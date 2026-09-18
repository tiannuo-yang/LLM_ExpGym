#!/usr/bin/env python3
"""Inspect every Audit overlay for newly rejected historical wrappers.

No benchmark reference labels, tool feedback, or model calls are used. The old
wrapper reader is independently copied from the frozen scorer's 12-line policy.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def old_accepts(text):
    try:
        parsed = json.loads(text)
    except (ValueError, RecursionError, OverflowError, TypeError):
        try:
            cleaned = text.strip().rstrip(';').strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
            parsed = json.loads(cleaned)
        except (ValueError, RecursionError, OverflowError, TypeError, AttributeError):
            return False
    return isinstance(parsed, dict)


def run(repo, source):
    sys.path.insert(0, str(repo))
    parser = importlib.import_module('expgym.tool_protocol').parse_audit_answer
    paths = {'answer_overlays': source / 'private/answer_overlays.jsonl',
             'agent_rows': source / 'agent_rows.csv', 'rescore_checks': source / 'CHECKS.json',
             'parser_source': repo / 'expgym/tool_protocol.py'}
    input_hashes = {key: sha(path) for key, path in paths.items()}
    rows = {(r['slot_id'], r['agent_id']): r for r in csv.DictReader(paths['agent_rows'].open())}
    counts, newly_rejected, decreases = Counter(), [], []
    for line in paths['answer_overlays'].open():
        overlay = json.loads(line)
        if overlay['scenario'] != 'evidence_audit':
            continue
        identity = {k: overlay.get(k) for k in ('slot_id', 'agent_id', 'model', 'system', 'regime', 'strategy')}
        counts['aggregate' if overlay['agent_id'] == 'aggregate' else 'member'] += 1
        for field in ('old_answer', 'new_scoring_input'):
            text = overlay[field]
            historic = old_accepts(text)
            try:
                parser(text)
                now, error = True, None
            except (ValueError, TypeError, RecursionError, OverflowError) as exc:
                now, error = False, str(exc)
            counts[f'{field}/old_accepted'] += int(historic)
            counts[f'{field}/current_accepted'] += int(now)
            if historic and not now:
                newly_rejected.append(identity | {'field': field, 'error': error,
                    'head': text[:200], 'tail': text[-1200:]})
        row = rows.get((overlay['slot_id'], str(overlay['agent_id'])))
        if row is not None:
            old, new = json.loads(row['old_metrics_json']), json.loads(row['new_metrics_json'])
            if any((old.get(k) or 0) > (new.get(k) or 0) for k in ('label_acc', 'evidence_acc')):
                decreases.append(identity | {'old_metrics': old, 'new_metrics': new,
                    'change_reason': row['change_reason']})
    rescoring = json.loads(paths['rescore_checks'].read_text())
    matching_version = (input_hashes['parser_source'] ==
                        rescoring['code_sha256']['expgym/tool_protocol.py'])
    stable_inputs = {key: sha(path) for key, path in paths.items()} == input_hashes
    return {'status': 'PASS' if matching_version and stable_inputs and not newly_rejected else 'REVIEW',
            'counts': dict(counts), 'newly_rejected_count': len(newly_rejected),
            'newly_rejected': newly_rejected, 'individual_LA_EA_decrease_count': len(decreases),
            'individual_LA_EA_decreases': decreases, 'input_sha256': input_hashes,
            'parser_matches_rescore_version': matching_version, 'stable_inputs': stable_inputs,
            'benchmark_gold_labels_used': False, 'model_calls': 0,
            'policy': 'Inspect syntactic acceptance independently; do not choose parser behavior by scores.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--rescore', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = run(args.repo.resolve(), args.rescore.resolve())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'counts', 'newly_rejected_count',
                     'individual_LA_EA_decrease_count', 'parser_matches_rescore_version')}))
