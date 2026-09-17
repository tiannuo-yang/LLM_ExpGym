#!/usr/bin/env python3
"""Package the exact frozen Gemini snapshot without examining later outcomes."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from datetime import datetime, timezone

W = Path('/lustrefs/users/chufan.shi/codex_space_tn')
P = W / 'publication/five_model_report_20260911'
SNAP = W / 'all_model_report_20260913/gemini_snapshot/data_v1'
OUT = W / 'deliveries/paper-ad03e8c-20260916/raw_archives/gemini_snapshot'
OLD = W / 'gemini38_eval_20260911/formal_segment_delivery_v1/gemini_formal_segment_v3'
WORK = W / 'ad03_delivery_20260916/work'
sys.path.insert(0, str(P))
from expgym.delivery import seal, verify


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def copy_checked(src, dst, expected=None):
    h = hashlib.sha256()
    size = 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open('rb') as inp, dst.open('xb') as out:
        while chunk := inp.read(1 << 20):
            h.update(chunk)
            size += len(chunk)
            out.write(chunk)
    identity = {'bytes': size, 'sha256': h.hexdigest()}
    if expected:
        assert all(identity[k] == expected[k] for k in identity), f'copy identity: {src.name}'
    return identity


def main():
    assert not OUT.exists(), 'Fresh destination required'
    OUT.mkdir(parents=True, mode=0o700)
    rows = [json.loads(x) for x in (SNAP / 'normalized.jsonl').read_text().splitlines()]
    inputs = read(SNAP / 'INPUTS.json')
    source = read(SNAP / 'SOURCE_INDEX.json')
    source_by_path = {x['path']: x for x in source['files']}
    assert len(rows) == 783
    assert sum(x['execution_complete'] for x in rows) == 767
    completed = [x for x in rows if x['source_id'] == 'recovery_v1' and x['execution_complete']]
    assert len(completed) == 691
    recovery = Path(completed[0]['source_root'])
    original = Path(next(x for x in rows if x['source_id'] == 'original_v3')['source_root'])
    members = []
    archive_sets = []
    t0 = time.monotonic()
    old_manifest = read(OLD / 'manifest.json')
    for name in ['manifest.json', *[x['path'] for x in old_manifest['archives']]]:
        expected = next((x for x in old_manifest['archives'] if x['path'] == name), None)
        copy_checked(OLD / name, OUT / 'original_v3' / name, expected)
    for f in old_manifest['files']:
        members.append(dict(source_id='gemini_snapshot',
            archive_file=f'raw_archives/gemini_snapshot/original_v3/{f["archive"]}',
            member_path=f['path'], bytes=f['bytes'], sha256=f['sha256'],
            original_path=str(original / f['path'])))
    archive_sets.append(dict(kind='original_v3', original_root=str(original),
        manifest='original_v3/manifest.json', files=len(old_manifest['files']),
        archives=len(old_manifest['archives']),
        original_bytes=sum(x['bytes'] for x in old_manifest['files']),
        compressed_bytes=sum(x['bytes'] for x in old_manifest['archives']),
        verification='Existing manifest member identities reused; each compressed archive copied and SHA256 verified in this delivery. No new member stream verification or restoration.',
        public_scan_passed=old_manifest['security']['public_scan_passed'],
        selected_completed=76, selected_failed=1,
        elapsed_seconds=round(time.monotonic()-t0,3)))
    expected = {}
    selections = []
    for row in completed:
        receipt_path = Path(row['receipt'])
        receipt_raw = receipt_path.read_bytes()
        assert hashlib.sha256(receipt_raw).hexdigest() == row['receipt_sha256']
        receipt = json.loads(receipt_raw)
        assert receipt['job_id'] == row['source_job_id']
        assert receipt['exit_code'] == 0
        inv = recovery / 'invocations' / row['source_job_id']
        artifact_paths = []
        for member, identity in receipt['artifacts'].items():
            relative = str((inv / member).relative_to(recovery))
            assert '..' not in Path(relative).parts
            assert relative not in expected
            expected[relative] = {'bytes': identity['bytes'], 'sha256': identity['sha256'],
                                  'binding': 'frozen_completion_receipt'}
            artifact_paths.append(relative)
        receipt_relative = str(receipt_path.relative_to(recovery))
        expected[receipt_relative] = {'bytes': len(receipt_raw), 'sha256': row['receipt_sha256'],
                                      'binding': 'frozen_snapshot_source_index'}
        started = receipt_path.parent / 'started.json'
        if started.is_file():
            # Immutable completed-job control; identity is newly recorded by seal.
            expected[str(started.relative_to(recovery))] = {'binding': 'completed_job_control'}
        result_relative = str(Path(row['planned_result']).relative_to(recovery))
        assert result_relative in expected
        assert expected[result_relative]['sha256'] == row['result_sha256']
        selections.append({k: row[k] for k in ['logical_id', 'source_job_id', 'source_id',
            'started_at', 'ended_at', 'execution_complete', 'score_complete', 'queue_status',
            'system', 'scenario', 'budget', 'strategy', 'N', 'item', 'repeat']})
        selections[-1].update(receipt_member=receipt_relative, result_member=result_relative,
                              artifacts=len(artifact_paths),
                              api_dumps=sum('/api_dump/' in x for x in artifact_paths))
    plan = source_by_path[str(recovery / 'queue-plan.json')]
    expected['queue-plan.json'] = {'bytes': plan['bytes'], 'sha256': plan['sha256'],
                                  'binding': 'frozen_snapshot_source_index'}
    write(WORK / 'gemini_recovery_files.json', sorted(expected))
    write(OUT / 'RECOVERY_SELECTION.json', {'schema': 'expgym.delivery.frozen-selection.v1',
        'cutoff_utc': inputs['cutoff_utc'], 'source_root': str(recovery),
        'selected_completed': selections,
        'excluded_incomplete': [{k: r[k] for k in ['logical_id','source_job_id','queue_status',
             'started_at','ended_at','execution_complete','score_complete']}
             for r in rows if r['source_id'] == 'recovery_v1' and not r['execution_complete']],
        'file_bindings': expected})
    print(json.dumps({'phase': 'seal_recovery', 'files': len(expected),
                      'receipt_bound_bytes': sum(v.get('bytes',0) for v in expected.values())}), flush=True)
    t0 = time.monotonic()
    manifest = seal(recovery, sorted(expected), OUT / 'recovery_v1', None)
    seal_seconds = time.monotonic()-t0
    for file in manifest['files']:
        binding = expected[file['path']]
        for key in ('bytes','sha256'):
            if key in binding:
                assert binding[key] == file[key], f'Frozen receipt mismatch: {file["path"]}'
        members.append(dict(source_id='gemini_snapshot',
            archive_file=f'raw_archives/gemini_snapshot/recovery_v1/{file["archive"]}',
            member_path=file['path'], bytes=file['bytes'], sha256=file['sha256'],
            original_path=str(recovery / file['path'])))
    print(json.dumps({'phase': 'verify_recovery', 'archives': len(manifest['archives']),
                      'seal_seconds': round(seal_seconds,3)}), flush=True)
    t0 = time.monotonic()
    verification = verify(OUT / 'recovery_v1', manifest)
    verify_seconds = time.monotonic()-t0
    archive_sets.append(dict(kind='recovery_v1', original_root=str(recovery),
        manifest='recovery_v1/manifest.json', files=len(manifest['files']),
        archives=len(manifest['archives']), original_bytes=sum(x['bytes'] for x in manifest['files']),
        compressed_bytes=sum(x['bytes'] for x in manifest['archives']),
        verification=verification, seal_seconds=round(seal_seconds,3),
        verify_seconds=round(verify_seconds,3), public_scan_passed=False,
        selected_completed=691, selected_failed=0))
    controls = []
    control_paths = [SNAP / x for x in ['SOURCE_INDEX.json','INPUTS.json','normalized.jsonl',
        'SHA256.json','VALIDATION.json']]
    control_paths += [Path(x['snapshot_path']) for x in inputs['captures']]
    capture_map = {x['snapshot_path']: x for x in inputs['captures']}
    for path in control_paths:
        relative = path.relative_to(SNAP)
        identity = copy_checked(path, OUT / 'snapshot_controls' / relative,
                                capture_map.get(str(path)))
        controls.append({'path': str(Path('snapshot_controls') / relative),
             'original_path': str(path), **identity,
             'captured_source_path': capture_map.get(str(path),{}).get('source_path')})
    with (OUT / 'MEMBERS.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['source_id','archive_file','member_path',
                                                    'bytes','sha256','original_path'])
        writer.writeheader()
        writer.writerows(sorted(members,key=lambda x:(x['archive_file'],x['member_path'])))
    index = {'schema': 'expgym.delivery.gemini-frozen-snapshot.v1',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'report_commit': 'ad03e8c42ca501016176ee1bc407b38499178506',
        'snapshot_cutoff_utc': inputs['cutoff_utc'],
        'capture_finished_utc': inputs['capture_finished_utc'],
        'scope': 'Exact selected completed sources behind frozen report; no later-run results admitted.',
        'expected_jobs': 783, 'completed_jobs': 767, 'score_complete_jobs': 767,
        'failed_jobs': 1, 'started_incomplete_jobs': 1, 'unstarted_jobs': 14,
        'archive_sets': archive_sets, 'snapshot_controls': controls,
        'member_index': 'MEMBERS.csv', 'selection': 'RECOVERY_SELECTION.json',
        'local_only': True, 'public_upload_authorized': False,
        'paused_snapshot_slot': {k: next(r for r in rows if r['queue_status'] == 'incomplete_started')[k]
            for k in ['logical_id','source_job_id','system','scenario','budget','strategy','N','item','repeat','started_at','queue_status']},
        'boundary': 'The paused recovery invocation had no frozen attempt-body inventory in this snapshot. Its later mutable API dumps and later failure receipt are deliberately excluded. Its original frozen status and start event remain in snapshot_controls. No unknown endpoint is filled.',
        'counts': {'archives': sum(x['archives'] for x in archive_sets),
             'members': len(members), 'original_bytes': sum(x['bytes'] for x in members),
             'compressed_bytes': sum(x['compressed_bytes'] for x in archive_sets)}}
    write(OUT / 'INDEX.json', index)
    (OUT / 'README.zh.md').write_text('''# Gemini：ad03e8c 报告对应原始材料\n\n此处固定到 2026-09-13 05:27:39.527814740 UTC 的报告快照，不引入后续结果。783 个计划槽位中，767 个完成并评分；1 个原始失败池保留，1 个已启动但未完成，14 个未启动。未知结果不补零。\n\n- `original_v3/`：复用原始已关闭运行的完整 3 个分片，含 76 个完成项和 1 个失败项；保留其他被恢复槽位在原段留下的历史证据。原始成员哈希沿用旧 manifest；本次复制时核对所有压缩文件 SHA256，未重新全量解包。\n- `recovery_v1/`：仅封存本快照选中的 691 个完成项。每个 completion receipt 声明的全部 API 请求/回复、agent trajectory、终态/评分证据和 worker 文件均在内；另含 completion/started 控制及固定 queue plan。其中 22,446 件有冻结 receipt 或 SOURCE_INDEX 的历史哈希绑定；691 份 `started.json` 完成任务控制文件另按本次封存记录身份。全部 23,137 件均完成一次成员流式验证，未全量恢复。\n- `snapshot_controls/`：精确复制原快照的 SOURCE_INDEX、normalized、INPUTS 和 captured_metadata；后者是当时 controller、queue timeline、quota 与 oracle 的字节，不使用后来改变的在线控制文件。\n- `MEMBERS.csv`：每个 archive/member → 原始绝对路径、大小、SHA256，便于与合并 CSV 联接。\n- `RECOVERY_SELECTION.json`：选中的逻辑槽位、源 job、运行时间、结果/receipt 路径及全部文件绑定依据。\n- `INDEX.json`：总计、每组验证范围、来源根目录及时间。\n\n恢复 archive member 的原始路径：相应 manifest 的 `path` 加到该组 `original_root`；不要把 absolute source path 当作交付依赖。所有原件已在本目录的分片中。使用交付附带的 `package_run.py verify --manifest ... --archive-dir ...` 可验证；加 `--select` 和新建 `--restore-dir` 可按清单恢复所需原件。\n\n边界：尚未完成的 recovery job 在原快照中没有逐 API payload 的冻结清单；其后续 dump 和后续失败结果没有被反写进此快照。快照中的状态、开始事件和未知端点完整保留。此包为私有本地交付，未做公开凭据扫描，不可直接上传 GitHub。\n''')
    print(json.dumps({'phase': 'complete', **index['counts'], 'root': str(OUT)}), flush=True)


if __name__ == '__main__':
    main()
