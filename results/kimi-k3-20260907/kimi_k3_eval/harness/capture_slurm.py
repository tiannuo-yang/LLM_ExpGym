#!/usr/bin/env python3
"""Capture accounting for the two exact Slurm allocations owned by this study."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    command = ['sacct', '-j', '1203298,1203299',
               '--format=JobIDRaw,JobName,Account,State,Start,End,ElapsedRaw,AllocNodes,AllocTRES,ExitCode',
               '--parsable2']
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    raw = result.stdout
    (args.output_dir / 'sacct.psv').write_text(raw)
    records = list(csv.DictReader(io.StringIO(raw), delimiter='|'))
    allocations = []
    for record in records:
        if record['JobIDRaw'] not in {'1203298', '1203299'}:
            continue
        tres = dict(part.split('=', 1) for part in record['AllocTRES'].split(',') if '=' in part)
        gpu_count = int(tres['gres/gpu']) if 'gres/gpu' in tres else None
        elapsed = int(record['ElapsedRaw']) if record['ElapsedRaw'].isdigit() else None
        allocations.append({
            **record, 'gpu_count': gpu_count, 'elapsed_seconds': elapsed,
            'allocated_gpu_hours': gpu_count * elapsed / 3600 if gpu_count is not None and elapsed is not None else None,
            'final': record['End'] not in {'Unknown', 'N/A', ''} and record['State'] != 'RUNNING',
        })
    final = len(allocations) == 2 and all(row['final'] for row in allocations)
    data = {
        'schema_version': 1, 'captured_at': datetime.now(timezone.utc).isoformat(),
        'command': command, 'owned_allocation_ids': ['1203298', '1203299'],
        'raw_file': str((args.output_dir / 'sacct.psv').resolve()),
        'raw_sha256': hashlib.sha256(raw.encode()).hexdigest(),
        'allocations': allocations, 'final': final,
        'known_allocated_gpu_hours': sum(row['allocated_gpu_hours'] or 0 for row in allocations),
        'accounting_note': 'Allocated GPU-hours include environment bootstrap, loading, validation, evaluation, and idle time; not GPU utilization or token billing. Step rows are not summed because they overlap allocations.',
    }
    (args.output_dir / 'slurm_receipt.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'output_dir': str(args.output_dir), 'final': final,
                      'known_allocated_gpu_hours': data['known_allocated_gpu_hours']}))


if __name__ == '__main__':
    main()
