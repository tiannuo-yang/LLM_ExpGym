"""Read fixed owned Slurm allocations and export a credential-free GPU ledger.

Elapsed allocation time includes deployment, model loading, generation and any
validation/acceptance wait. It is not model-only compute or billable USD.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import os
import pwd
from pathlib import Path
import re
import subprocess
import tempfile

OUT = Path(__file__).resolve().parent / 'resource_usage'
OWNED = {'1213909': ('glm', 16), '1213910': ('kimi', 16),
         '1213911': ('qwen', 32), '1214130': ('deepseek', 8)}
SUBMISSION_DATE = '2026-09-18'
FIELDS = ('JobIDRaw', 'JobName', 'User', 'State', 'AllocTRES', 'ReqTRES', 'Start', 'End', 'ElapsedRaw', 'Submit', 'Suspended', 'Restarts')
TERMINAL = {'COMPLETED', 'CANCELLED', 'FAILED', 'TIMEOUT', 'NODE_FAIL', 'OUT_OF_MEMORY',
            'BOOT_FAIL', 'DEADLINE', 'PREEMPTED', 'REVOKED'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def gpu_count(tres):
    values = dict(item.split('=', 1) for item in tres.split(',') if '=' in item)
    # Some clusters report both gres/gpu and typed gres/gpu:a100. The generic
    # total takes precedence, so typed entries must never be added to it.
    if 'gres/gpu' in values:
        value = values['gres/gpu']
        return int(value) if re.fullmatch(r'\d+', value) else None
    typed = [value for key, value in values.items() if key.startswith('gres/gpu:')]
    if not typed or any(not re.fullmatch(r'\d+', value) for value in typed):
        return None
    return sum(map(int, typed))


def timestamp(value):
    if value in ('', 'Unknown', 'None', 'N/A'):
        return None
    return dt.datetime.fromisoformat(value).replace(tzinfo=dt.timezone.utc).isoformat()


def project(raw, observed_at, expected_user):
    records = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        values = line.split('|')
        assert len(values) == len(FIELDS), 'Unexpected accounting schema; no output replaced'
        row = dict(zip(FIELDS, values))
        job = row['JobIDRaw']
        assert job in OWNED and job not in records, 'Unexpected or duplicate accounting allocation'
        model, expected_gpus = OWNED[job]
        assert row['JobName'] == 'protocol-hpo-' + model, 'Job name does not match fixed ownership allowlist'
        assert row['User'] == expected_user, 'Job owner does not match current user'
        # CANCELLED may include an actor ID; only the non-identifying state is public.
        state = row['State'].split(' ', 1)[0].rstrip('+')
        start, end = timestamp(row['Start']), timestamp(row['End'])
        submitted = timestamp(row['Submit'])
        assert submitted is not None and submitted.startswith(SUBMISSION_DATE + 'T'), 'Job submission date differs; possible reused job ID'
        allocated, requested = gpu_count(row['AllocTRES']), gpu_count(row['ReqTRES'])
        if allocated is not None:
            assert allocated == expected_gpus, 'Allocated GPU count differs from registered owned job'
        if requested is not None:
            assert requested == expected_gpus, 'Requested GPU count differs from registered owned job'
        # PENDING jobs may have a forecast Start and ElapsedRaw=0. These are not
        # observations of consumed allocation time, and are kept unknown.
        if state == 'PENDING' or start is None:
            elapsed = None
            allocated = None
            start = None
        else:
            assert re.fullmatch(r'\d+', row['ElapsedRaw']), 'Invalid accounting elapsed value'
            elapsed = int(row['ElapsedRaw'])
        restarts = int(row['Restarts']) if re.fullmatch(r'\d+', row['Restarts']) else None
        suspended = row['Suspended']
        assert not suspended or re.fullmatch(r'[0-9:-]+', suspended), 'Unexpected suspension time format'
        suspension_zero = bool(suspended) and not any(char in '123456789' for char in suspended)
        history_review = restarts != 0 or not suspension_zero
        complete = state in TERMINAL and end is not None and elapsed is not None and allocated is not None and not history_review
        records[job] = {'model': model, 'job_id': job, 'job_name': row['JobName'],
            'ownership_verified': True, 'accounting_record_present': True, 'state': state,
            'gpu_count': allocated, 'requested_gpu_count': requested,
            'submitted_at_utc': submitted, 'start_at_utc': start, 'end_at_utc': end,
            'observed_at_utc': observed_at, 'elapsed_allocation_seconds': elapsed,
            'suspended_time_sacct': row['Suspended'] or None, 'restart_count': restarts,
            'allocation_history_review_required': history_review,
            'gpu_allocation_hours': allocated * elapsed / 3600 if allocated is not None and elapsed is not None else None,
            'allocation_final': complete, 'reported_cost_usd': None,
            'measurement_status': ('accounting_history_review_required' if history_review else
                                   'final' if complete else 'pending_or_unknown' if elapsed is None else 'provisional_allocation')}
    for job, (model, _) in OWNED.items():
        if job not in records:
            records[job] = {'model': model, 'job_id': job, 'job_name': 'protocol-hpo-' + model,
                'ownership_verified': False, 'accounting_record_present': False, 'state': 'UNKNOWN',
                'gpu_count': None, 'requested_gpu_count': None, 'submitted_at_utc': None,
                'start_at_utc': None, 'end_at_utc': None, 'observed_at_utc': observed_at,
                'elapsed_allocation_seconds': None, 'gpu_allocation_hours': None,
                'suspended_time_sacct': None, 'restart_count': None,
                'allocation_history_review_required': True,
                'allocation_final': False, 'reported_cost_usd': None,
                'measurement_status': 'accounting_record_missing'}
    return [records[job] for job in OWNED]


def atomic_write(name, raw):
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=OUT, prefix='.resource-export-', delete=False) as stream:
        stream.write(raw)
        path = Path(stream.name)
    path.replace(OUT / name)


def main():
    formats = {'JobName': 'JobName%64', 'State': 'State%40', 'AllocTRES': 'AllocTRES%300', 'ReqTRES': 'ReqTRES%300'}
    command = ['sacct', '--jobs', ','.join(OWNED), '--parsable2', '--noheader', '--allocations',
               '--starttime', SUBMISSION_DATE + 'T00:00:00',
               '--format', ','.join(formats.get(field, field) for field in FIELDS)]
    env = dict(os.environ, TZ='UTC', LC_ALL='C', SLURM_TIME_FORMAT='%Y-%m-%dT%H:%M:%S')
    result = subprocess.run(command, text=True, capture_output=True, env=env, timeout=30)
    if result.returncode:
        # Raw stderr can disclose cluster information. Keep the last good files.
        raise RuntimeError('sacct read failed; previous resource export retained (return code %s)' % result.returncode)
    observed_at = dt.datetime.now(dt.timezone.utc).isoformat()
    rows = project(result.stdout, observed_at, pwd.getpwuid(os.geteuid()).pw_name)
    known = [row['gpu_allocation_hours'] for row in rows if row['gpu_allocation_hours'] is not None]
    summary = {'schema': 'expgym.owned-gpu-allocation-ledger.v1', 'observed_at_utc': observed_at,
        'jobs': rows, 'expected_jobs': 4, 'verified_accounting_jobs': sum(r['ownership_verified'] for r in rows),
        'all_allocations_final': all(row['allocation_final'] for row in rows),
        'known_gpu_allocation_hours': sum(known) if known else None,
        'gpu_allocation_hours_complete': len(known) == len(rows) and not any(row['allocation_history_review_required'] for row in rows), 'reported_cost_usd': None,
        'accounting_source': 'Read-only sacct allocation records; UTC timezone requested',
        'raw_accounting_stdout_sha256': digest(result.stdout.encode()),
        'scope': 'Only the four fixed owned model-serving allocations; HPO and auxiliary controls may share their allocations.',
        'time_interpretation': 'Total allocated elapsed time includes deployment, model loading, request processing, idle time and validation/acceptance waiting. It is not model-only compute.',
        'cost_policy': 'No GPU-hour to USD conversion. Dollar cost is unknown and remains null.',
        'unknown_policy': 'Pending/missing start, missing accounting record, missing end, and unknown GPU count remain null rather than zero.',
        'restart_policy': 'Nonzero/unknown restarts or suspension time require review of allocation history before treating the total as final; this exporter does not infer omitted attempts.',
        'public_projection': 'No username, account, nodes, endpoints, absolute paths, credentials, prompts or response content.'}
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    atomic_write('resource_usage.csv', buffer.getvalue().encode())
    atomic_write('RESOURCE_USAGE.json', (json.dumps(summary, indent=2, sort_keys=True) + '\n').encode())
    readme = '''# 模型服务 GPU 分配账本

`resource_usage.csv` 和 `RESOURCE_USAGE.json` 来自固定的 4 个本轮 owned Slurm allocation，只读 `sacct`，每次刷新都核对作业名及当前用户归属。公开投影不含用户名、账号、节点、endpoint、绝对路径或凭证。

GPU hours = 实际分配 GPU 数 × sacct ElapsedRaw 秒数 / 3600。分配时长包括部署、模型加载、生成、空闲和等待验收，不能当作纯模型计算时长。HPO 与追加控制共享服务时，不重复累计这份 allocation。RUNNING 的数值是截至导出时的暂定值；作业结束后重新运行 exporter 可得到最终数值。

PENDING、未知 start/end、缺失 accounting/GPU 数保留 null（CSV 空字段），不填 0。`requested_gpu_count` 只是申请数，不代替实际分配数。美元成本始终 null，没有 GPU 到美元的换算。

在本目录父级运行 `python3 export_resource_usage.py` 可重复刷新。脚本只读取固定作业，不启动、取消或修改服务；读取或身份核验失败时保留上次成功导出。`MANIFEST.json` 固定本轮 CSV/JSON/说明及 exporter SHA。
'''
    atomic_write('README.zh.md', readme.encode())
    files = {name: {'bytes': (OUT / name).stat().st_size, 'sha256': digest((OUT / name).read_bytes())}
             for name in ('resource_usage.csv', 'RESOURCE_USAGE.json', 'README.zh.md')}
    manifest = {'schema': 'expgym.resource-usage-manifest.v1', 'observed_at_utc': observed_at,
                'exporter_sha256': digest(Path(__file__).read_bytes()), 'files': files,
                'all_allocations_final': summary['all_allocations_final'],
                'source_stdout_sha256': summary['raw_accounting_stdout_sha256']}
    atomic_write('MANIFEST.json', (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({'observed_at_utc': observed_at, 'verified_jobs': summary['verified_accounting_jobs'],
        'all_allocations_final': summary['all_allocations_final'],
        'known_gpu_allocation_hours': summary['known_gpu_allocation_hours'],
        'reported_cost_usd': None, 'manifest_sha256': digest((OUT / 'MANIFEST.json').read_bytes())}))


if __name__ == '__main__':
    main()
