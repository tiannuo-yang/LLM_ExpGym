"""Create a closed, safe operations delivery; reject incomplete final releases."""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import tempfile

OPS = Path(__file__).resolve().parent
DEST = OPS / 'public_delivery'
LEDGER_FILES = ('MANIFEST.json', 'request_attempt_ledger.csv', 'service_versions.json',
                'USAGE_SUMMARY.json', 'request_profiles.json')
RESOURCE_FILES = ('resource_usage.csv', 'RESOURCE_USAGE.json', 'README.zh.md', 'CHECKS.json', 'MANIFEST.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def csvread(path):
    return list(csv.DictReader(path.open()))


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def safe_content(name, raw):
    """Check actual content, including nested JSON values and source scripts."""
    text = raw.decode('utf-8')
    path_pattern = '/' + '(?:lustrefs|home|root|mnt|tmp)' + '/'
    network_pattern = r'(?:https?[:][/][/]|azure[-]uk[-]|[0-9]{1,3}(?:[.][0-9]{1,3}){3}:[0-9]+)'
    secret_pattern = r'(?:sk[-]or[-][A-Za-z0-9_-]{12,}|sk[-][A-Za-z0-9_-]{24,}|Bearer[ ]+[A-Za-z0-9._-]{12,}|BEGIN[ ](?:RSA[ ])?PRIVATE[ ]KEY)'
    for pattern in (path_pattern, network_pattern, secret_pattern):
        if re.search(pattern, text):
            raise ValueError('Unsafe content rejected in ' + name)
    if name.endswith(('.json', '.csv')):
        value = json.loads(text) if name.endswith('.json') else list(csv.DictReader(io.StringIO(text)))
        def walk(item):
            if isinstance(item, dict):
                for key, child in item.items():
                    if key.lower() in {'api_key', 'authorization', 'access_token', 'password', 'private_key'} and child:
                        raise ValueError('Sensitive nonempty field rejected in ' + name)
                    walk(child)
            elif isinstance(item, list):
                for child in item:
                    walk(child)
            elif isinstance(item, str) and re.match(r'^(?:[/]|[A-Za-z]:[\\/]|~[/\\])', item):
                raise ValueError('Absolute path value rejected in ' + name)
        walk(value)


def review_projection(value):
    fields = ('snapshot_manifest_sha256', 'snapshot_checked_at', 'exporter_sha256', 'slots',
              'completed_slots_fully_audited', 'public_attempt_rows', 'completed_attempt_rows_fully_audited',
              'raw_sha_and_receipt_checks', 'numeric_usage_checks', 'effective_setting_checks',
              'per_slot_cost_sum_checks', 'real_queue_wall_time_checks', 'profiles_verified',
              'attempt_seed_checks', 'completed_attempts_without_usage', 'usage_numeric_path_presence',
              'usage_numeric_path_nonzero', 'completed_raw_numeric_usage_sums', 'privacy_scan_hits', 'pending_attempt_policy')
    assert value['passed'] and value.get('issues') == [], 'Independent audit has unresolved findings'
    return {'schema': 'expgym.public-independent-ledger-receipt.v1', 'passed': True,
            'reviewed_at_utc': value['reviewed_at_utc'], 'model_calls': value['model_calls'],
            'review_script_sha256': value['review_script_sha256'], 'issues': [],
            'ledgers': {alias: {key: value['ledgers'][alias][key] for key in fields}
                        for alias in ('hpo', 'aux')},
            'projection': 'Whitelisted counts, numeric usage aggregates and hashes only; no private raw paths or bodies.'}


def reexport_projection(value):
    fields = ('passed', 'sealed_slots_byte_value_equal', 'sealed_attempt_rows_byte_value_equal', 'profiles_equal',
              'before_manifest_sha256', 'after_manifest_sha256', 'exporter_sha256', 'manifest_all_files_verified', 'note')
    assert value['passed'] and value.get('model_calls') == 0
    return {'schema': 'expgym.public-reexport-receipt.v1', 'passed': True, 'model_calls': 0,
            'checker_sha256': value['checker_sha256'],
            'results': {alias: {key: value['results'][alias][key] for key in fields} for alias in ('hpo', 'aux')}}


def verify_source_manifest(directory):
    manifest = read(directory / 'MANIFEST.json')
    for name, expected in manifest['files'].items():
        path = directory / name
        assert path.parent == directory and path.is_file(), 'Unexpected source manifest path'
        assert sha(path) == expected['sha256'] and path.stat().st_size == expected['bytes'], 'Source export is changing or inconsistent'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-partial', action='store_true', help='Build an explicitly incomplete preview; never a final release')
    args = parser.parse_args()
    sources = {'hpo': OPS / 'public_ledger', 'aux': OPS / 'aux-controls/public_ledger'}
    for directory in [*sources.values(), OPS / 'resource_usage']:
        verify_source_manifest(directory)
    review_source = OPS / 'ledger_review/CHECKS.json'
    repeat_source = OPS / 'ledger_review/REEXPORT_CHECKS.json'
    review = review_projection(read(review_source))
    repeat = reexport_projection(read(repeat_source))
    slots = {'hpo': csvread(sources['hpo'] / 'pool_run_ledger.csv'),
             'aux': csvread(sources['aux'] / 'slot_run_ledger.csv')}
    summaries = {alias: read(path / 'USAGE_SUMMARY.json') for alias, path in sources.items()}
    for alias, filename in [('hpo', 'export_public_ledger.py'), ('aux', 'export_aux_public_ledger.py')]:
        manifest = read(sources[alias] / 'MANIFEST.json')
        assert manifest['exporter_sha256'] == sha(OPS / filename), 'Exporter changed after last ledger refresh'
        if alias == 'aux':
            assert manifest['common_exporter_sha256'] == sha(OPS / 'export_public_ledger.py')
    attempts = {alias: csvread(path / 'request_attempt_ledger.csv') for alias, path in sources.items()}
    all_attempts = [row for rows in attempts.values() for row in rows]
    recovered_errors = []
    for row in all_attempts:
        if row['state'] in ('success', 'in_progress'):
            continue
        later = [item for item in all_attempts if item['job_id'] == row['job_id']
                 and item['generation_id'] == row['generation_id'] and item['state'] == 'success'
                 and int(item['attempt']) > int(row['attempt'])]
        if row['will_retry'] == 'True' and later and int(row['attempt']) < int(row['max_attempts']):
            recovered_errors.append({'model': row['model'], 'job_id': row['job_id'],
                'generation_id': row['generation_id'], 'error_attempt': int(row['attempt']),
                'successful_retry_attempt': min(int(item['attempt']) for item in later),
                'max_attempts': int(row['max_attempts'])})
    resource = read(OPS / 'resource_usage/RESOURCE_USAGE.json')
    resource_manifest = read(OPS / 'resource_usage/MANIFEST.json')
    resource_checks = read(OPS / 'resource_usage/CHECKS.json')
    assert resource_checks['passed'] and resource_checks['exporter_sha256'] == resource_manifest['exporter_sha256']
    assert resource_manifest['exporter_sha256'] == sha(OPS / 'export_resource_usage.py')
    assert len(slots['hpo']) == 97 and len(slots['aux']) == 22
    members = sum(int(row['agents']) for rows in slots.values() for row in rows)
    assert members == 467
    gates = {}
    for alias in ('hpo', 'aux'):
        expected = len(slots[alias])
        sealed = sum(row['status'] == 'validated_complete' for row in slots[alias])
        gates[alias + '_all_slots_complete'] = summaries[alias]['all_complete'] and sealed == expected
        gates[alias + '_independent_audit_full_coverage'] = review['ledgers'][alias]['completed_slots_fully_audited'] == expected
        gates[alias + '_review_chain_matches_current_export'] = (
            review['ledgers'][alias]['snapshot_manifest_sha256'] == repeat['results'][alias]['before_manifest_sha256']
            and repeat['results'][alias]['after_manifest_sha256'] == sha(sources[alias] / 'MANIFEST.json')
            and review['ledgers'][alias]['exporter_sha256'] == read(sources[alias] / 'MANIFEST.json')['exporter_sha256']
            and repeat['results'][alias]['sealed_slots_byte_value_equal'] == review['ledgers'][alias]['completed_slots_fully_audited'])
    gates['gpu_allocation_accounting_final'] = resource['all_allocations_final']
    gates['gpu_accounting_complete'] = resource['gpu_allocation_hours_complete'] and resource['verified_accounting_jobs'] == 4
    ready = all(gates.values())
    if not ready and not args.allow_partial:
        raise SystemExit('Refusing final delivery; unmet gates: ' + ', '.join(key for key, passed in gates.items() if not passed))
    complete = ready and not args.allow_partial
    model_costs = {}
    for summary in summaries.values():
        for alias, value in summary['models'].items():
            model_costs.setdefault(alias, [])
            if value['reported_cost_usd'] is not None:
                model_costs[alias].append(value['reported_cost_usd'])
    status = {'schema': 'expgym.public-ops-delivery-status.v1', 'complete': complete,
        'status': 'final' if complete else 'partial_preview_not_final',
        'built_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'registered_slots': 119, 'registered_agent_members': members, 'hpo_slots': 97, 'aux_slots': 22,
        'validated_slots': sum(row['status'] == 'validated_complete' for rows in slots.values() for row in rows),
        'attempt_records': sum(len(rows) for rows in attempts.values()),
        'http_error_attempts': sum(row['state'] not in ('success', 'in_progress') for rows in attempts.values() for row in rows),
        'http_error_retries_recovered': len(recovered_errors), 'http_retry_recovery': recovered_errors,
        'readiness_gates': gates, 'model_calls_by_packager': 0,
        'scope': 'Operations usage/provenance only; no scores, ranking or result adoption is defined by this package.',
        'reported_cost_usd_by_model': {alias: sum(values) if values else None for alias, values in model_costs.items()},
        'resource_all_final': resource['all_allocations_final']}
    if DEST.exists():
        assert (DEST / 'MANIFEST.json').is_file(), 'Refusing to replace an unrecognized output directory'
        assert read(DEST / 'MANIFEST.json').get('schema') == 'expgym.public-ops-delivery-manifest.v1'
        old_paths = {str(path.relative_to(DEST)) for path in DEST.rglob('*') if path.is_file()}
        assert old_paths == set(read(DEST / 'MANIFEST.json')['files']) | {'MANIFEST.json'}, 'Unexpected files in existing generated delivery'
    with tempfile.TemporaryDirectory(prefix='.ops-delivery-', dir=OPS) as temp:
        stage = Path(temp) / 'package'
        stage.mkdir()
        entries = []
        def add(source, destination, value=None):
            raw = source.read_bytes() if value is None else value
            safe_content(destination, raw)
            output = stage / destination
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(raw)
            entries.append({'source': 'operations/' + str(source.relative_to(OPS)), 'destination': destination,
                'mode': 'byte_copy' if value is None else 'safe_projection_or_generated',
                'source_sha256': sha(source), 'source_bytes': source.stat().st_size,
                'destination_sha256': sha(output), 'destination_bytes': len(raw)})
        for alias, destination, name in [('hpo', 'main', 'pool_run_ledger.csv'), ('aux', 'aux', 'slot_run_ledger.csv')]:
            for filename in LEDGER_FILES + (name,):
                add(sources[alias] / filename, destination + '/' + filename)
        for filename in RESOURCE_FILES:
            add(OPS / 'resource_usage' / filename, 'resource_usage/' + filename)
        add(review_source, 'audit/INDEPENDENT_REVIEW.json', encoded(review))
        add(repeat_source, 'audit/REEXPORT_REVIEW.json', encoded(repeat))
        audit_readme = f'''# 独立账本核验凭据

本投影只公开计数、数值汇总、状态及来源 SHA。内部完整审查读取了私有原始请求与 completion receipts；这些原件不在公开包中。

当前凭据覆盖 HPO {review['ledgers']['hpo']['completed_slots_fully_audited']}/97、辅助 {review['ledgers']['aux']['completed_slots_fully_audited']}/22 个已固定完成槽。请求 SHA、receipt、真实 queue wall、token 与费用均逐条复核。未完成槽不计入固定原件审查。

`INDEPENDENT_REVIEW.json` 的 snapshot SHA 与 `REEXPORT_REVIEW.json` 的 before SHA 相接；after SHA 应对应本包 main/aux 子 manifest。完整最终包要求全部 119 槽完成且独立审查覆盖齐全。

公开包中的离线 verifier 复算公开 CSV/JSON 及哈希闭包；它不能替代持有私有原件时的全文/API 语义审查。原审查脚本身份和原 receipt SHA 保存在投影及顶层 ALLOWLIST 中。
'''
        add(Path(__file__), 'audit/README.zh.md', audit_readme.encode())
        for filename in ('export_public_ledger.py', 'export_aux_public_ledger.py', 'export_resource_usage.py', 'build_public_ops_delivery.py'):
            add(OPS / filename, 'source_scripts/' + filename)
        add(OPS / 'verify_public_ledgers.py', 'tools/verify_public_ledgers.py')
        add(Path(__file__), 'DELIVERY_STATUS.json', encoded(status))
        report = f'''# 公开运营与资源账本

状态：**{'FINAL — 已完成' if complete else 'PARTIAL — 仅预览，不可当作最终交付'}**。登记 **97 个 HPO 槽 + 22 个辅助控制槽 = 119 槽、467 个智能体成员**；本次快照已有 **{status['validated_slots']} 槽**通过生产完成校验。辅助控制含主实验 21 槽与独立 GLM β20 sweep 1 槽，不能把后者并入主 β10。

账本只描述实际运行的请求、用量、费用、设置、版本与资源，不定义正式采用分数、排名或评分修正。历史分数和新正式分数由实验分析交付管理。

## 内容与复算

- `main/`：HPO 97 槽的 6 个公开账本文件。
- `aux/`：辅助 22 槽的 6 个公开账本文件。
- `resource_usage/`：4 个固定服务 allocation 的 5 个资源文件。
- `audit/`：独立原件审查和重复导出凭据的安全投影。
- `ALLOWLIST.json`：每个 payload 的来源相对位置、原件/投影 SHA、字节数及转换方式。
- `MANIFEST.json`：封闭文件清单；包含 ALLOWLIST，只有 manifest 自身不自哈希。

在任意 Python 3 环境，从本包目录运行：

```bash
python3 tools/verify_public_ledgers.py --root .
```

它只读取包内 CSV/JSON，复算槽数与成员数、attempt/profile 关联、逐槽和逐模型用量/费用/错误次数，并验证所有文件 SHA；无需网络、GPU 或私有原件。用 `--require-complete` 可拒绝 partial 包。

当前导出的 HTTP error attempts 为 **{status['http_error_attempts']}**，来自全部尝试记录动态统计；其中 **{status['http_error_retries_recovered']}** 条按原 will_retry/max_attempts 标记重试，且同一 generation 随后成功。重试身份和费用字段全部保留，不等于 whole-slot 重跑。生产层允许的 HTTP 传输重试和 whole-slot 重新采样须分开解释。

USD 仅汇总 provider 实际报告的 usage.cost，未知费用保持 null，不填 0。GPU hours 是分配数乘 scheduler 记账时长，包含部署、加载、生成、空闲和等待验收，不是纯模型计算，也不换算美元。资源是否最终结束见 DELIVERY_STATUS 的独立 gate。

`source_scripts/` 保留实际 exporter/packager 源码便于审计。运行这些原导出器需要原项目完整本地 archive、队列与（资源查询时）Slurm 布局；公开包不包含这些材料，也不能单靠该目录重读私有 API 原件。资源目录原 README 中的刷新命令同样属于原运行环境；公开独立复算入口只有上述 verifier。

未发布原 plans、BINDINGS、API dumps、prompt、答案、工具内容、endpoint、凭证或绝对本地路径。`--allow-partial` 构建始终标记 complete=false；最终构建要求生产完成、独审覆盖、receipt 链和资源记账全部通过。
'''
        add(Path(__file__), 'README.zh.md', report.encode())
        allowlist = {'schema': 'expgym.public-ops-allowlist.v1', 'payload_file_count': len(entries),
                     'closed_file_count': len(entries) + 2, 'entries': sorted(entries, key=lambda item: item['destination'])}
        (stage / 'ALLOWLIST.json').write_bytes(encoded(allowlist))
        files = {str(path.relative_to(stage)): {'bytes': path.stat().st_size, 'sha256': sha(path)}
                 for path in sorted(stage.rglob('*')) if path.is_file()}
        manifest = {'schema': 'expgym.public-ops-delivery-manifest.v1', 'complete': complete,
                    'closed_file_count': len(files) + 1, 'files': files,
                    'allowlist_sha256': sha(stage / 'ALLOWLIST.json'),
                    'packager_sha256': sha(Path(__file__)), 'readiness_gates': gates}
        (stage / 'MANIFEST.json').write_bytes(encoded(manifest))
        module_spec = importlib.util.spec_from_file_location('public_ledger_verify', OPS / 'verify_public_ledgers.py')
        verifier = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(verifier)
        verified = verifier.verify(stage, require_complete=complete)
        assert verified['passed']
        if DEST.exists():
            shutil.rmtree(DEST)
        shutil.copytree(stage, DEST)
    print(json.dumps({'complete': complete, 'files': manifest['closed_file_count'],
                      'validated_slots': status['validated_slots'], 'manifest_sha256': sha(DEST / 'MANIFEST.json'),
                      'offline_verified': True, 'output': 'operations/public_delivery'}))


if __name__ == '__main__':
    main()
