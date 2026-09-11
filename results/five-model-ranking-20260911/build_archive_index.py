#!/usr/bin/env python3
"""Frozen metadata-only navigation; never opens payloads, tars, or credentials.

This adapter is specific to five-model-ranking-20260911. Local input relocation
flags do not change the original artifact locations recorded in the output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


WORKSPACE = Path('/lustrefs/users/chufan.shi/codex_space_tn')
API_ROOT = WORKSPACE / 'LLM_ExpGym_api_studies_20260910'
API_DELIVERY = API_ROOT / 'deliveries/api_studies_20260910'
FOUR_ROOT = WORKSPACE / 'publication/four_model_report_20260911/results/four-model-20260911'
FOUR_COMMIT = 'a79cbc100804a1bc8d374e084a4b9999e3697a91'
FOUR_URL = f'https://github.com/tiannuo-yang/LLM_ExpGym/blob/{FOUR_COMMIT}/results/four-model-20260911'
PINS = {
    'four_index': (71685, '1fafeba1a75537b4ad9507d94016ceb5c65d82584c557b38a92983a1670db7ca'),
    'api_index': (12051169, '536c732b683c845a3fb378d01c092c872f9a0015a8a265e9b876eb683b53c483'),
    'api_outer': (47368, 'c1998a5e45d2dcf6729e0381c2e37025b950b457a65876400322314d0e83f8e7'),
    'api_verification': (682, '898eac23839a1c9b615f0441728ac2f75aeb45b1d3a7d0af5ec66ff876113597'),
    'api_spec': (4902, '8e386b3b8e9f926d251292fcdf716049efbb46e02ecbde77805cf9114dcbcc31'),
}
API_INPUT_NAMES = {
    'api_index': 'ARCHIVE_INDEX.json', 'api_outer': 'OUTER_FILES.json',
    'api_verification': 'STREAM_VERIFICATION.json', 'api_spec': 'archive-spec.json',
}
OLD_MODELS = {'kimi-k3', 'glm-5.3', 'qwen3.8-2.4t-a95b-fp8', 'deepseek-v4-flash-0731'}
PACKAGES = ('gpt', 'claude', 'common')
STUDIES = {
    'gpt': 'gpt56sol_medium_refmatrix_20260910_v1',
    'claude': 'claude_fable5_high_poolact_refmatrix_20260910_v1',
}
SCOPES = {
    'gpt': 'GPT 正式矩阵的原件、队列、分析及设置；合报第五模型，缺失端点依正文保留 unknown。',
    'claude': 'Claude 未完成正式 PoolAct 研究；保留失败/未启动账本，仅登记存档，不进入五模型正式排名。',
    'common': '共享源码、控制器、总报告及 GPT/Claude smoke；单列一次，不是额外正式模型或重复。',
}
COUNT_KEYS = ('original_files', 'original_bytes', 'tar_shards', 'compressed_bytes')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_bound(path, identity):
    raw = Path(path).read_bytes()
    require((len(raw), hashlib.sha256(raw).hexdigest()) == identity, 'input_identity_mismatch')
    return json.loads(raw)


def valid_path(value):
    p = PurePosixPath(value)
    require(bool(value) and not p.is_absolute() and all(x not in ('', '.', '..') for x in value.split('/')), 'invalid_member_path')
    require('\\' not in value and all(ord(x) >= 32 for x in value), 'invalid_member_path')


def valid_identity(value):
    require(type(value['bytes']) is int and value['bytes'] >= 0, 'invalid_bytes')
    require(bool(re.fullmatch('[0-9a-f]{64}', value['sha256'])), 'invalid_sha256')


def fixed_url(value):
    require(bool(re.match(r'https://github\.com/tiannuo-yang/LLM_ExpGym/blob/[0-9a-f]{40}/', value)), 'nonimmutable_url')


def validate_metadata(four, api, outer, verification, spec):
    require(four['schema'] == 'four-model.archive-navigation.v1', 'unexpected_four_schema')
    names = [x['model'] for x in four['models']]
    require(len(names) == 4 and set(names) == OLD_MODELS, 'old_model_set_or_duplicate')
    for key in COUNT_KEYS:
        require(sum(x['counts'][key] for x in four['models']) == four['tar_payload_totals'][key], 'old_count_mismatch')
    for model in four['models']:
        for value in model['navigation'].values():
            fixed_url(value)
        fixed_url(model['raw_entry']['url'])
    require(api['schema'] == 'expgym.api-full-archive-index.v1', 'unexpected_api_schema')
    require(api['publication'] == 'local-only; no public clearance or upload', 'api_publication_status_changed')
    package_rows = {x['id']: x for x in api['packages']}
    require(len(api['packages']) == 3 and set(package_rows) == set(PACKAGES), 'package_set_or_duplicate')
    files, archives = {}, {}
    for package in api['packages']:
        require(package['public_scan_passed'] is False, 'api_public_scan_status_changed')
        valid_identity(package['manifest'])
        valid_path(package['manifest']['path'])
        require(package['manifest']['path'] == package['id'] + '/manifest.json', 'manifest_package_mismatch')
        for archive in package['archives']:
            valid_identity(archive)
            valid_path(archive['path'])
            require(archive['path'].startswith(package['id'] + '/'), 'archive_package_mismatch')
            require(archive['path'] not in archives, 'duplicate_archive_path')
            archives[archive['path']] = archive
        require(sum(x['bytes'] for x in package['archives']) == package['compressed_bytes'], 'compressed_count_mismatch')
    for item in api['files']:
        valid_identity(item)
        valid_path(item['path'])
        require(item['path'] not in files, 'duplicate_member_path')
        require(item['package'] in package_rows and item['archive'] in archives, 'unknown_member_mapping')
        require(item['archive'].startswith(item['package'] + '/'), 'member_package_mismatch')
        files[item['path']] = item
    for name, package in package_rows.items():
        selected = [x for x in files.values() if x['package'] == name]
        require(len(selected) == package['file_count'], 'member_count_mismatch')
        require(sum(x['bytes'] for x in selected) == package['original_bytes'], 'member_bytes_mismatch')
    outer_files = {x['path']: x for x in outer['files']}
    require(len(outer_files) == len(outer['files']), 'duplicate_outer_path')
    require(outer['self_excluded'] == 'OUTER_FILES.json', 'unexpected_self_exclusion')
    for x in outer['files']:
        valid_identity(x)
        valid_path(x['path'])
    for x in list(archives.values()) + [p['manifest'] for p in api['packages']]:
        require(x['path'] in outer_files and all(outer_files[x['path']][k] == x[k] for k in ('bytes', 'sha256')), 'outer_identity_mismatch')
    for item in api['browse_copies']:
        source = files.get(item['source_member'])
        require(source is not None and all(source[k] == item[k] for k in ('bytes', 'sha256')), 'browse_source_mismatch')
        require(item['path'] in outer_files and all(outer_files[item['path']][k] == item[k] for k in ('bytes', 'sha256')), 'browse_outer_mismatch')
    verified = {x['package']: x['verification'] for x in verification}
    require(len(verification) == 3 and set(verified) == set(PACKAGES), 'verification_package_mismatch')
    for name, value in verified.items():
        package = package_rows[name]
        require(value['passed'] is True and value['public_scan_declaration'] is False and value['restored_files'] == 0, 'verification_scope_changed')
        require((value['files'], value['original_bytes'], value['archives']) == (package['file_count'], package['original_bytes'], len(package['archives'])), 'verification_count_mismatch')
    require(spec['schema'] == 'expgym.api-archive-spec.v1', 'unexpected_spec_schema')
    require({x['id'] for x in spec['packages']} == set(PACKAGES), 'spec_packages_mismatch')
    for external in api['external_immutable_inputs']:
        require(external['payload_archived'] is False, 'external_scope_changed')
    return files, outer_files


def local_ref(entry, root=API_DELIVERY):
    return {
        'local_path': str(root / entry['path']), 'bytes': entry['bytes'], 'sha256': entry['sha256'],
        'evidence_basis': 'inherited_from_sha_bound_metadata_not_payload_read', 'public_url': None,
    }


def member_ref(entry):
    return {**local_ref(entry, API_ROOT), 'source_member': entry['path'],
            'package': entry['package'], 'archive_local_path': str(API_DELIVERY / entry['archive'])}


def build_index(four, api, outer, verification, spec):
    files, outer_files = validate_metadata(four, api, outer, verification, spec)
    inputs = [{
        'id': 'four_index', 'original_location': FOUR_URL + '/ARCHIVE_INDEX.json',
        'bytes': PINS['four_index'][0], 'sha256': PINS['four_index'][1],
        'evidence_basis': 'this_generator_read_and_sha256_checked',
    }]
    for name, filename in API_INPUT_NAMES.items():
        inputs.append({'id': name, 'original_location': str(API_DELIVERY / filename),
                       'bytes': PINS[name][0], 'sha256': PINS[name][1],
                       'evidence_basis': 'this_generator_read_and_sha256_checked'})
    old_models = [{k: m[k] for k in ('model', 'label', 'data_commit', 'counts', 'navigation', 'raw_entry', 'raw_mapping')}
                  for m in four['models']]
    collections = []
    for name in PACKAGES:
        p = next(x for x in api['packages'] if x['id'] == name)
        row = {
            'id': name, 'scope': SCOPES[name], 'publication': 'local_only_no_public_clearance',
            'counts': {'original_files': p['file_count'], 'original_bytes': p['original_bytes'],
                       'tar_shards': len(p['archives']), 'compressed_bytes': p['compressed_bytes']},
            'manifest': local_ref(p['manifest']),
            'archives': [local_ref(x) for x in p['archives']],
            'existing_stream_verification': next(x['verification'] for x in verification if x['package'] == name),
        }
        if name in STUDIES:
            study = STUDIES[name]
            prefix = f'studies/{study}/analysis_v1/'
            row['study_id'] = study
            row['study_local_root'] = str(API_ROOT / 'studies' / study)
            row['analysis_files'] = [member_ref(x) for path, x in sorted(files.items()) if path.startswith(prefix)]
            controller = spec['authoritative_model_controller_results'][study]
            row['authoritative_controller'] = member_ref(files[controller])
            row['invocation_members'] = {
                'prefix': f'studies/{study}/invocations/',
                'files': sum(1 for x in files if x.startswith(f'studies/{study}/invocations/')),
                'bytes': sum(v['bytes'] for x, v in files.items() if x.startswith(f'studies/{study}/invocations/')),
            }
        else:
            prefix = 'studies/api_20260910/full_report_v1/'
            row['report_and_resource_files'] = [member_ref(x) for path, x in sorted(files.items()) if path.startswith(prefix)]
            row['shared_only_count_once'] = True
        collections.append(row)
    controls = [local_ref(outer_files[name]) for name in (
        'ARCHIVE_INDEX.md', 'ARCHIVE_INDEX.json', 'MEMBERS.csv', 'BROWSE_FILES.json',
        'STREAM_VERIFICATION.json', 'archive-spec.json', 'prepared-catalog.json')]
    controls.append({'local_path': str(API_DELIVERY / 'OUTER_FILES.json'),
                     'bytes': PINS['api_outer'][0], 'sha256': PINS['api_outer'][1],
                     'evidence_basis': 'this_generator_read_and_sha256_checked', 'public_url': None})
    external = [{k: v for k, v in x.items() if k != 'files'} for x in api['external_immutable_inputs']]
    return {
        'schema': 'five-model.archive-navigation.v1', 'study': 'five-model-ranking-20260911',
        'inputs_read_this_generation': inputs,
        'report_input_snapshots': {'index': 'INPUTS.json', 'report': 'README.zh.md',
                                 'scope': 'Only explicitly listed, separately scanned report inputs are published here; API raw archives remain local.'},
        'published_four_model_parent': {
            'commit': FOUR_COMMIT, 'archive_index_md': FOUR_URL + '/ARCHIVE_INDEX.md',
            'archive_index_json': FOUR_URL + '/ARCHIVE_INDEX.json', 'report': FOUR_URL + '/README.zh.md',
            'models': old_models, 'tar_payload_totals': four['tar_payload_totals'],
            'complete_navigation': 'Parent models entries retain all analysis/cost/review/restore identities, member/shard inventories and format-specific limits.',
            'evidence_basis': 'inherited_from_bound_published_parent_not_new_remote_or_tar_verification',
        },
        'api_local_delivery': {
            'original_repo_root': str(API_ROOT), 'delivery_root': str(API_DELIVERY),
            'publication': api['publication'], 'public_raw_url': None,
            'collections': collections, 'controls': controls,
            'tar_payload_totals': {key: sum(x['counts'][key] for x in collections) for key in COUNT_KEYS},
            'browse_copies': {'count': len(api['browse_copies']), 'scope': 'Byte-identical duplicate declarations, not additional results; member/browse identity metadata matched this generation.'},
            'outer_inventory_scope': {'listed_files_excluding_self': len(outer['files']),
                                      'listed_bytes_excluding_self': sum(x['bytes'] for x in outer['files']),
                                      'already_includes_tars_and_browse_do_not_add_to_tar_totals': True},
            'external_immutable_inputs': external,
            'restore': {
                'tool': str(API_ROOT / 'scripts/package_run.py'),
                'protocol': 'expgym.delivery.v1; select original repo-relative source_member paths; restore into a fresh directory only.',
                'example_verify': f'python {API_ROOT}/scripts/package_run.py verify --manifest {API_DELIVERY}/gpt/manifest.json --archive-dir {API_DELIVERY}/gpt',
                'selection_flags': '--select <explicit-source-member-paths.json> --restore-dir <fresh-directory>',
                'limits': [
                    'Existing local manifests have no public clearance; do not add --require-public-scan or claim remote availability.',
                    'Verification streams all selected package archives, but restores only requested members. Index generation does neither.',
                    'browse/ is a partial duplicate tree; original relative links can require selective restoration in the original repository layout.',
                    'No arbitrary-root analysis replay was verified here; preserve original metadata paths and provide external datasets/runtime.',
                    'Current package_run.py is not the legacy Kimi/GLM archive reader; follow their fixed child-index restoration tools.',
                ],
            },
        },
        'counting_scope': {
            'archive_files_are_not_experiment_samples': True,
            'public_and_local_totals_kept_separate': True,
            'common_counted_once_and_not_ranked': True,
            'claude_partial_not_in_five_model_ranking': True,
            'old_kimi_composite_reused_once': True,
            'no_content_dedup_across_studies': True,
            'tar_totals_exclude_outer_attachments_current_report_and_external_payloads': True,
        },
        'evidence': {
            'input_metadata_files_read_and_sha256_checked': len(inputs),
            'payload_or_tar_files_read': 0, 'files_restored': 0, 'model_calls': 0,
            'new_secret_scan_by_generator': False, 'new_remote_content_verification': False,
            'independent_scientific_review_by_generator': False,
            'checks': 'Bound input identities; old-model set and totals; API unique member/shard mappings, package totals, manifest/shard outer identities, browse identities, existing stream-verification scope.',
        },
    }


def md_link(label, location):
    return f'[{label}](<{location}>)'


def render(index):
    old = index['published_four_model_parent']
    api = index['api_local_delivery']
    lines = [
        '# 五模型报告：原始 dump、聚合与恢复索引', '',
        '本索引连接既有 Kimi / GLM / Qwen / DeepSeek 的公开存档与 GPT API 的本地完整封存。Claude 部分研究和共享 common 包单列，不进入五模型正式排名。原件数是文件数，不是实验样本数。', '',
        '**公开范围不同：** 四模型原始包沿既有固定提交访问；GPT / Claude / common 的原始包只有本地完整性封存，未获公共扫描通过，也没有确认的公开 raw 链接。本次公开的报告及评分/配置快照另见 [正文](README.zh.md) 与 [INPUTS.json](INPUTS.json)，不能据此声称 API raw 已公开。', '',
        '机器索引：[ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)。生成器：[build_archive_index.py](build_archive_index.py)；窄测试：[test_archive_index.py](test_archive_index.py)。', '',
        '## 1. 已公开四模型：保留完整固定子索引', '',
        f"{md_link('四模型完整人读索引', old['archive_index_md'])} · {md_link('完整机器索引', old['archive_index_json'])} · {md_link('原四模型报告', old['report'])}", '',
        '子索引保留 raw → collection/bundle → member inventory → shard、全部分析/成本账本、恢复工具及复核入口；这里不重新复制几十万条原件映射。Kimi composite 的旧包只计一次；旧 bundle 与新 single-manifest collection 不是同一单位。', '',
        '| 模型 | 原件数 | 原件 bytes | tar 分片 | 压缩 bytes | raw / 完整子索引 |',
        '|---|---:|---:|---:|---:|---|',
    ]
    for m in old['models']:
        c = m['counts']
        links = md_link('raw 入口', m['raw_entry']['url']) + ' / ' + md_link('全部导航', m['navigation']['archive_index_md'])
        lines.append(f"| {m['label']} | {c['original_files']} | {c['original_bytes']} | {c['tar_shards']} | {c['compressed_bytes']} | {links} |")
    c = old['tar_payload_totals']
    lines += [f"| 既有四模型 tar 合计 | {c['original_files']} | {c['original_bytes']} | {c['tar_shards']} | {c['compressed_bytes']} | 不含外层附件 / 本报告 |", '',
              '上述大小、member/shard 身份及旧内容验证是固定子索引的继承声明；本次只读取并核验父索引 JSON 的 SHA，不重新下载或打开旧 tar。旧格式使用其匹配的恢复器；Qwen/DeepSeek 的任意目录 raw→分析重放限制仍按各自子索引，不由本 wrapper 解除。', '',
              '## 2. API 本地三包：GPT、Claude、common 分列', '',
              f"本地 delivery：`{api['delivery_root']}`。包内原件保留原仓库相对路径；全路径/大小/SHA/所属 tar 见下方控制索引。", '',
              '| 包 | 范围 | 原件数 | 原件 bytes | 分片数 | 压缩 bytes | manifest（本地） |',
              '|---|---|---:|---:|---:|---:|---|']
    for p in api['collections']:
        c = p['counts']
        lines.append(f"| {p['id']} | {p['scope']} | {c['original_files']} | {c['original_bytes']} | {c['tar_shards']} | {c['compressed_bytes']} | {md_link('manifest', p['manifest']['local_path'])} |")
    c = api['tar_payload_totals']
    lines += [f"| API 三包 tar 合计 | 非五模型正式样本数 | {c['original_files']} | {c['original_bytes']} | {c['tar_shards']} | {c['compressed_bytes']} | common 只计一次 |", '',
              'GPT 包含正式矩阵；Claude 包保留未完成计划、失败和已保存结果；common 包含共享控制器、源码与报告，以及双方 smoke，不作为额外正式重复。原件同时包含队列、metadata、分析和轨迹，不能全部称为 HTTP 请求。', '',
              f"browse/ 的 {api['browse_copies']['count']} 份副本是重复物理文件，不是新结果。OUTER_FILES 的 {api['outer_inventory_scope']['listed_files_excluding_self']} 件 / {api['outer_inventory_scope']['listed_bytes_excluding_self']} bytes 已包含所有 tar、browse 与控制件（仅清单自身除外），不能再次加到 tar 总量上。", '',
              '### 2.1 完整 member、shard 与控制索引', '',
              '| 入口（均本地） | bytes | SHA256 |', '|---|---:|---|']
    for ref in api['controls']:
        lines.append(f"| {md_link(Path(ref['local_path']).name, ref['local_path'])} | {ref['bytes']} | `{ref['sha256']}` |")
    lines += ['', 'MEMBERS.csv / ARCHIVE_INDEX.json 保存逐原件与分片映射；各 manifest 同时列出所属包的全部原件及归档。prepared-catalog 是首次封存选择记录，本次生成器不读取或复制该大文件。所有 41 个 API shard 的本地路径、压缩大小和继承 SHA 也保存在本索引 JSON 的 `api_local_delivery.collections[].archives[]`。', '',
              '### 2.2 GPT / Claude 全量分析、成本与终态入口', '',
              '以下链接定位原仓库本地文件，不代表 GitHub 已公开；机器索引同时给出该文件所属 tar，完整恢复不依赖当前 raw 目录一直存在。`raw_terminals.csv` 是终态投影，不是 HTTP dump；`all_attempt_costs.csv` 包含全部已保存请求尝试，不能因未知用量而当作完整已知成本。', '']
    for p in api['collections']:
        if p['id'] == 'common':
            continue
        lines += [f"#### {p['id']}：`{p['study_id']}`", '',
                  f"{md_link('原 study 根目录', p['study_local_root'])}；{md_link('权威控制器终态', p['authoritative_controller']['local_path'])}。", '',
                  '| 文件 | bytes | SHA256 |', '|---|---:|---|']
        for f in p['analysis_files']:
            lines.append(f"| {md_link(Path(f['local_path']).name, f['local_path'])} | {f['bytes']} | `{f['sha256']}` |")
        lines += ['']
    common = next(p for p in api['collections'] if p['id'] == 'common')
    lines += ['### 2.3 common：原总报告、资源与独立复核', '', '| 文件 | bytes | SHA256 |', '|---|---:|---|']
    for f in common['report_and_resource_files']:
        label = f['source_member'].split('/full_report_v1/', 1)[1]
        lines.append(f"| {md_link(label, f['local_path'])} | {f['bytes']} | `{f['sha256']}` |")
    lines += ['', '这里的独立复核属于原 API 报告。五模型新稿复核由主报告另行记录，本索引生成器不冒称完成科学复核。', '',
              '## 3. 按需恢复与公开边界', '',
              '优先使用冻结聚合 CSV，无须为了更新报告恢复 raw。本地完整性校验命令示例（本次未执行）：', '',
              '```bash', api['restore']['example_verify'], '```', '',
              '若确需少量文件，追加 `--select <显式原仓库相对路径数组.json> --restore-dir <尚不存在的新目录>`。校验仍流式读取该包全部分片，只落地所选原件；恢复多个包时保留原仓库相对布局，避免覆盖已有目录。API 本地 manifest 未获 public scan，不能添加 `--require-public-scan` 伪装公开验证通过。', '',
              'browse/ 只含选定副本，不是完整恢复树：原报告中的相对链接可能需要按原仓库布局选择性恢复。数据 payload、Python 环境及权重不在这些结果包内；没有在此验证任意路径下分析重放。', '']
    for ext in api['external_immutable_inputs']:
        lines += [f"外部数据清单 `{ext['inventory']}`：{ext['file_count']} 件 / {ext['bytes']} bytes，清单继承 SHA `{ext['inventory_sha256']}`；payload_archived=false。"]
    lines += ['', 'API public_scan=false 不能通过改 manifest 字段升级。将来若发布 raw，需执行真实首次公开安全流程；本次只由主作者扫描确切报告/输入快照增量，安全扫描结果不由本生成器产生。', '',
              '## 4. 输入身份、生成与有限检查', '',
              f"生成器实际读取 {len(index['inputs_read_this_generation'])} 份 JSON metadata，均绑定 bytes/SHA；未读 tar/member payload，未解包、重新评分、调用模型或读取凭据。子文件/分片身份仍为继承声明。", '',
              '| 显式输入 | bytes | SHA256 |', '|---|---:|---|']
    for x in index['inputs_read_this_generation']:
        lines.append(f"| {md_link(x['id'], x['original_location'])} | {x['bytes']} | `{x['sha256']}` |")
    lines += ['', '原记录 CPython 3.11.15 下，从本目录执行：', '',
              '```bash', 'python -B -m unittest test_archive_index.py -v', 'python -B build_archive_index.py --check', '```', '',
              '`--four-index` / `--api-dir` 可重定位同字节的 metadata 输入；输出中的原始来源路径保持不变。`--output-dir` 指定输出目录；`--check` 只比较现有输出字节，不创建或修改文件。fixtures 检查假数据的身份、计数、重复映射与公开边界，不是原始 payload 安全扫描或科学独立复核。', '']
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--four-index', type=Path, default=FOUR_ROOT / 'ARCHIVE_INDEX.json')
    parser.add_argument('--api-dir', type=Path, default=API_DELIVERY)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    four = read_bound(args.four_index, PINS['four_index'])
    data = {name: read_bound(args.api_dir / filename, PINS[name]) for name, filename in API_INPUT_NAMES.items()}
    index = build_index(four, data['api_index'], data['api_outer'], data['api_verification'], data['api_spec'])
    outputs = {'ARCHIVE_INDEX.json': json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
               'ARCHIVE_INDEX.md': render(index)}
    if args.check:
        for name, value in outputs.items():
            require((args.output_dir / name).read_bytes() == value.encode(), 'generated_output_mismatch')
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, value in outputs.items():
            (args.output_dir / name).write_bytes(value.encode())
    print(json.dumps({'check': args.check, 'outputs': list(outputs), 'inputs': len(PINS),
                      'api_tar_totals': index['api_local_delivery']['tar_payload_totals'],
                      'payload_files_read': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
