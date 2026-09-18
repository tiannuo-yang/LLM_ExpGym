#!/usr/bin/env python3
"""Rebuild the 582-row HPO runtime comparison from three scalar layers.

The runtime input must be completed_slot_scalars.csv produced by the public HPO
replay. All three scalar inputs are bound to the adoption manifest. The portable
historical inventory supplies the planned 97 slots, old hashes and reasons;
status and verified-source records supply the new invocation provenance.
The published comparison is read only for the final byte comparison, never as
a row, score, column-order or formatting template. No APIs or raw dumps are used.
"""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
from pathlib import Path

METRICS = ('raw_perf_mi', 'raw_perf_bon', 'gap_mi', 'gap_bon', 'gap0_mi', 'gap0_bon')
CORE = ('slot_id', 'model', 'system', 'scenario', 'regime', 'strategy', 'item',
        'outer_repeat', 'order', 'seed', 'family')
IDENTITY = ('model', 'item', 'regime', 'strategy', 'seed', 'outer_repeat')
PLAN_IDENTITY = ('slot_id', 'model', 'system', 'regime', 'strategy', 'item', 'seed', 'outer_repeat')
COLUMNS = ('slot_id', 'model', 'task', 'regime', 'strategy', 'seed', 'outer_repeat',
           'metric', 'state', 'historical_score', 'existing_trace_rescored',
           'new_runtime_score', 'extraction_delta', 'runtime_delta',
           'old_result_sha256', 'new_result_sha256', 'new_job_id', 'reason')
ALIASES = {'gemini-3.8-flash-medium': 'gemini', 'gpt-5.6-sol': 'gpt',
           'glm-5.3': 'glm', 'kimi-k3': 'kimi',
           'qwen3.8-2.4t-a95b-fp8': 'qwen', 'deepseek-v4-flash-0731': 'deepseek'}
EXPECTED = {'gemini': 49, 'gpt': 9, 'glm': 10, 'kimi': 9, 'qwen': 19, 'deepseek': 1}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path, label):
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        columns, rows = reader.fieldnames, list(reader)
    require(columns and len(columns) == len(set(columns)), label + ': missing/duplicate columns')
    require(all(None not in row and all(value is not None for value in row.values()) for row in rows),
            label + ': malformed row')
    require(all(row.get('slot_id') for row in rows), label + ': empty slot ID')
    by_id = {row['slot_id']: row for row in rows}
    require(len(by_id) == len(rows), label + ': duplicate slot ID')
    return columns, rows, by_id


def metric_values(row):
    values = json.loads(row['metrics_json'])
    require(set(values) == set(METRICS), row['slot_id'] + ': wrong HPO metric keys')
    require(all(value is None or (type(value) in (int, float) and math.isfinite(value))
                for value in values.values()), row['slot_id'] + ': nonfinite/non-numeric metric')
    return values


def encode_csv(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical-scalars', type=Path, required=True)
    parser.add_argument('--rescored-scalars', type=Path, required=True)
    parser.add_argument('--runtime-scalars', type=Path, required=True)
    parser.add_argument('--adoption', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.adoption
    paths = dict(historical_scalars=args.historical_scalars, rescored_scalars=args.rescored_scalars,
                 runtime_scalars=args.runtime_scalars, manifest=root / 'FAIRNESS_MANIFEST.json',
                 portable_plan=root / 'historical_hpo_versions_input.csv',
                 portable_plan_checks=root / 'HISTORICAL_CODE_INPUT_CHECKS.json',
                 status=root / 'progress/slot_status.csv',
                 verified_sources=root / 'progress/verified_sources.csv',
                 builder=Path(__file__))
    published = root / 'NEW_RUNTIME_COMPARISON.csv'
    destination = args.output / 'NEW_RUNTIME_COMPARISON.csv'
    checks_path = args.output / 'RUNTIME_COMPARISON_CHECKS.json'
    protected = {path.resolve() for path in list(paths.values()) + [published]}
    require(destination.resolve() not in protected and checks_path.resolve() not in protected,
            'Refusing to overwrite a source artifact')
    input_hashes = {name: sha(path) for name, path in paths.items()}
    manifest = json.loads(paths['manifest'].read_text())
    plan_checks = json.loads(paths['portable_plan_checks'].read_text())
    require(manifest['adoption_scope'] == 'hpo97_stage_only' and
            manifest['global_formal_adoption_claim'] is False, 'Expected an HPO-stage manifest')
    require(type(manifest['adoption_ready']) is bool and manifest['pre_registered_pools'] == 97 and
            manifest['pre_registered_members'] == 388 and manifest['expected_model_counts'] == EXPECTED,
            'Wrong HPO cohort gate metadata')
    for name, field in (('historical_scalars', 'historical_scalars_sha256'),
                        ('rescored_scalars', 'existing_trace_rescored_scalars_sha256'),
                        ('runtime_scalars', 'completed_slot_scalars_sha256')):
        require(input_hashes[name] == manifest[field], name + ': manifest SHA256 mismatch')
    require(plan_checks['status'] == 'PASS' and plan_checks['slots'] == 810 and
            input_hashes['portable_plan'] == plan_checks['portable_input_sha256'],
            'Portable historical inventory SHA256/count check failed')
    historical_columns, historical_rows, historical = read(args.historical_scalars, 'historical scalars')
    rescored_columns, rescored_rows, rescored = read(args.rescored_scalars, 'rescored scalars')
    runtime_columns, runtime_rows, runtime = read(args.runtime_scalars, 'runtime scalars')
    require(historical_columns == rescored_columns == runtime_columns and
            len(historical) == len(rescored) == 4698 and set(historical) == set(rescored),
            'Scalar schema or 4698-slot baseline membership mismatch')
    _, plan_rows, plan_all = read(paths['portable_plan'], 'portable historical inventory')
    require(len(plan_all) == 810, 'Expected all 810 HPO inventory slots')
    planned = {row['slot_id']: row for row in plan_rows if row['planned_action'] == 'rerun'}
    require(len(planned) == 97 and dict(Counter(ALIASES[row['model']] for row in planned.values())) == EXPECTED,
            'Wrong 97-slot replacement inventory')
    _, status_rows, statuses = read(paths['status'], 'status inventory')
    require(len(statuses) == 97 and set(statuses) == set(planned), 'Status/planned slot membership differs')
    require([row['slot_id'] for row in status_rows] == sorted(statuses), 'Status rows must be sorted by slot ID')
    require(dict(Counter(row['state'] for row in status_rows)) == manifest['status_counts'],
            'Status counters differ from manifest')
    complete = {sid for sid, row in statuses.items() if row['state'] == 'verified_complete'}
    _, _, verified_sources = read(paths['verified_sources'], 'verified sources')
    require(set(runtime) == set(verified_sources) == complete, 'Runtime/source/complete-status membership differs')
    require(len(complete) == manifest['verified_complete_pools'] and
            4 * len(complete) == manifest['verified_complete_members'], 'Complete cohort count mismatch')
    require(dict(Counter(ALIASES[planned[sid]['model']] for sid in complete)) == manifest['verified_model_counts'],
            'Complete model counts differ from manifest')
    if manifest['adoption_ready']:
        require(len(complete) == 97 and manifest['status'] == 'PASS' and not manifest['errors'],
                'Full actual-cohort adoption gate failed')
    comparison = []
    for status in status_rows:
        sid = status['slot_id']
        plan, old, new = planned[sid], historical[sid], rescored[sid]
        require(plan['system'] == 'poolact' and old['scenario'] == new['scenario'] == 'tuning',
                sid + ': not an HPO pool')
        require(all(plan[key] == old[key] == new[key] for key in PLAN_IDENTITY),
                sid + ': historical/diagnostic/planned identity mismatch')
        require(all(old[key] == new[key] for key in CORE), sid + ': baseline identity changed')
        require(all(status[key] == plan[key] for key in IDENTITY), sid + ': status/planned identity mismatch')
        require(status['rerun_reason'] == plan['planned_reason'], sid + ': replacement reason mismatch')
        current = {}
        if sid in complete:
            row, source = runtime[sid], verified_sources[sid]
            require(all(row[key] == new[key] for key in CORE), sid + ': runtime identity mismatch')
            require(row['execution_complete'] == status['execution_complete'] == 'True' and
                    row['score_complete'] == status['score_complete'] and not status['error'],
                    sid + ': execution/score status mismatch')
            require(source['old_result_sha256'] == plan['trajectory_sha256'] and
                    source['model'] == plan['model'] and source['cohort_id'] == row['cohort_id'] and
                    source['members'] == '4' and source['result_sha256'] == status['result_sha256'] and
                    source['new_job_id'] == status['new_job_id'] and
                    source['completion_sha256'] == status['completion_sha256'] and
                    source['rerun_reason'] == plan['planned_reason'], sid + ': invocation/source binding mismatch')
            for key in ('runtime_source_tree_sha256', 'runtime_core_commit', 'runtime_snapshot_commit',
                        'parser_sha256', 'graph_sha256'):
                require(source[key] == manifest[key], sid + ': source ' + key + ' mismatch')
            current = metric_values(row)
        before, diagnostic = metric_values(old), metric_values(new)
        for metric in METRICS:
            first, second, third = before[metric], diagnostic[metric], current.get(metric)
            comparison.append(dict(
                slot_id=sid, model=plan['model'], task=plan['item'], regime=plan['regime'],
                strategy=plan['strategy'], seed=plan['seed'], outer_repeat=plan['outer_repeat'],
                metric=metric, state=status['state'], historical_score=first,
                existing_trace_rescored=second, new_runtime_score=third,
                extraction_delta=second - first if second is not None and first is not None else None,
                runtime_delta=third - second if third is not None and second is not None else None,
                old_result_sha256=plan['trajectory_sha256'], new_result_sha256=status['result_sha256'],
                new_job_id=status['new_job_id'], reason=plan['planned_reason']))
    require(len(comparison) == 582, 'Expected all 97 x 6 comparison rows')
    rebuilt = encode_csv(comparison)
    # The reference supplies no inputs to reconstruction; compare only after all
    # 582 rows and their CSV bytes have been independently computed.
    reference = published.read_bytes()
    published_sha = hashlib.sha256(reference).hexdigest()
    require(rebuilt == reference, 'Recomputed comparison differs byte-for-byte from published CSV')
    require(all(sha(paths[name]) == value for name, value in input_hashes.items()) and
            sha(published) == published_sha, 'Inputs changed during reconstruction; retry on a fixed snapshot')
    args.output.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.csv.tmp')
    temporary.write_bytes(rebuilt)
    temporary.replace(destination)
    checks = dict(
        schema='expgym.hpo-runtime-comparison-replay.v1', status='PASS', rows=582, columns=len(COLUMNS),
        planned_pools=97, complete_pools=len(complete), complete_members=4 * len(complete),
        pending_or_failed_pools=97 - len(complete), pending_or_failed_metric_rows=6 * (97 - len(complete)),
        pending_or_failed_new_scores_and_deltas_empty=True,
        completed_null_metric_values=sum(row['new_runtime_score'] is None for row in comparison
                                         if row['state'] == 'verified_complete'),
        all_bytes_identical=True, rebuilt_comparison_sha256=sha(destination),
        published_comparison_sha256=published_sha, input_sha256=input_hashes,
        source_plan_sha256=manifest['source_plan_sha256'],
        captured_full_historical_plan_sha256=plan_checks['source_planning_sha256'],
        adoption_scope='hpo97_stage_only', hpo_stage_adoption_ready=manifest['adoption_ready'],
        global_formal_adoption_claim=False, model_calls=0,
        scope='Recompute all historical/diagnostic/runtime score values and both deltas, preserving None as empty CSV cells and every planned slot regardless of improvement.',
        provenance_notes=[
            'Historical and existing-trace-rescored scalar bytes are separately bound by the adoption manifest; runtime scalar bytes must match its completed-pool table and are intended to come from replay_hpo_reruns.py.',
            'The portable 810-slot inventory is hash-bound by HISTORICAL_CODE_INPUT_CHECKS.json. Its 97 rerun rows supply old trajectory hashes and reasons, and match the complete status inventory.',
            'New result/job/receipt identifiers are cross-checked against verified_sources.csv. Original raw receipts, historical source-tree verification and the private plan hash remain collector/capture attestations.',
            'This arithmetic/CSV replay does not rerun models or benchmarks and does not establish global formal adoption.'])
    checks_path.write_text(json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
