#!/usr/bin/env python3
"""Check frozen old-analysis parity and byte-exact public CSV replay."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile


def rows(path):
    return list(csv.DictReader(path.open()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--report', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    frozen = args.repo / 'results/paper-analysis-20260916'
    checks, mismatches = [], []
    tables = [
        ('audit/trace_metrics.csv', 'old/n1/trace_metrics.csv', ('model','budget','doc_index','order')),
        ('audit/hypothesis_metrics.csv', 'old/n1/hypothesis_metrics.csv', ('model','budget','doc_index','order','hypothesis')),
        ('audit/document_metrics.csv', 'old/n1/document_metrics.csv', ('model','budget','doc_index')),
        ('audit/model_budget_metrics.csv', 'old/n1/model_budget_metrics.csv', ('model','budget')),
        ('audit/budget_metrics.csv', 'old/n1/budget_metrics.csv', ('budget',)),
        ('audit/diagnostic_counts.csv', 'old/n1/diagnostic_counts.csv', ('budget','model','gold_subset')),
        ('audit/paired_completion_patterns.csv', 'old/n1/paired_completion_patterns.csv', ('model','doc_index','order','hypothesis')),
        ('poolact/coordination/audit_pools.csv', 'old/coordination/audit_pools.csv', ('model','regime','strategy','question_index')),
        ('poolact/coordination/audit_agents.csv', 'old/coordination/audit_agents.csv', ('model','regime','strategy','question_index','agent_id')),
        ('poolact/coordination/audit_groups.csv', 'old/coordination/audit_groups.csv', ('model','regime','strategy'))]
    for original, current, keys in tables:
        before = {tuple(r[k] for k in keys): r for r in rows(frozen / original)}
        after = {tuple(r[k] for k in keys): r for r in rows(args.report / current)}
        assert before.keys() == after.keys(), original
        count = 0
        for key, old in before.items():
            for name, old_value in old.items():
                if name in {'trace_path', 'free_trace', 'tight_trace', 'result_path'}:
                    continue
                count += 1
                new_value = after[key].get(name)
                if old_value == new_value:
                    continue
                try:
                    equal = math.isclose(float(old_value), float(new_value), abs_tol=1e-12)
                except (ValueError, TypeError):
                    equal = False
                if not equal:
                    mismatches.append([original, key, name, old_value, new_value])
        checks.append(dict(table=original, rows=len(before), cells_compared=count,
                           frozen_sha256=hashlib.sha256((frozen/original).read_bytes()).hexdigest()))
    result = dict(status='PASS' if not mismatches else 'FAIL', checks=checks,
                  total_cells_compared=sum(c['cells_compared'] for c in checks), mismatches=mismatches)
    (args.report/'OLD_BASELINE_CHECK.json').write_text(json.dumps(result, indent=2)+'\n')
    assert not mismatches, mismatches[:5]
    with tempfile.TemporaryDirectory(prefix='audit-public-replay-') as tmp:
        dest = Path(tmp)
        subprocess.run([sys.executable, str(args.report/'recompute_audit.py'),
                        '--replay-public', str(args.report), '--output', str(dest)],
                       check=True, stdout=subprocess.DEVNULL)
        files, different = [], []
        for file in sorted(args.report.rglob('*.csv')):
            relative = file.relative_to(args.report)
            replayed = dest/relative
            if not replayed.exists() or file.read_bytes() != replayed.read_bytes():
                different.append(str(relative))
            else:
                files.append(dict(path=str(relative), sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    replay = dict(status='PASS' if not different else 'FAIL', files=files, mismatches=different)
    (args.report/'PUBLIC_REPLAY_CHECK.json').write_text(json.dumps(replay, indent=2)+'\n')
    assert not different, different
    print(json.dumps(dict(status='PASS', old_cells=result['total_cells_compared'], replayed_csvs=len(files))))


if __name__ == '__main__':
    main()
