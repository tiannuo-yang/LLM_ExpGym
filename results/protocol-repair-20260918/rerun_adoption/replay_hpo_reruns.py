#!/usr/bin/env python3
"""Replay public HPO scoring inputs without APIs, raw dumps, or a Git checkout.

With --base-scalars, independently rebuild the 4698-row table from the frozen
existing-trace-rescored baseline and the 97 complete replacement pools. Pending
cohorts can export recomputed completed rows, but never a formal merged table.
With --base-sources, rebuild the matching source selection as well; its original
18 columns must match the frozen source inventory before any replacement.
Benchmark certificates attest original data-backed checks; they do not rerun
private benchmarks, models, graph sharing, or runtime decisions.
"""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys

CORE = ('slot_id', 'model', 'system', 'scenario', 'regime', 'strategy', 'item',
        'outer_repeat', 'order', 'seed', 'family')
CHANGED = ('execution_complete', 'score_complete', 'metrics_json',
           'provider_cohort', 'cohort_id')
METRICS = {'raw_perf_mi', 'raw_perf_bon', 'gap_mi', 'gap_bon', 'gap0_mi', 'gap0_bon'}
IDENTITY = ('model', 'item', 'regime', 'strategy', 'seed', 'outer_repeat')
ALIASES = {'gemini-3.8-flash-medium': 'gemini', 'gpt-5.6-sol': 'gpt',
           'glm-5.3': 'glm', 'kimi-k3': 'kimi',
           'qwen3.8-2.4t-a95b-fp8': 'qwen', 'deepseek-v4-flash-0731': 'deepseek'}
EXPECTED = {'gemini': 49, 'gpt': 9, 'glm': 10, 'kimi': 9, 'qwen': 19, 'deepseek': 1}
SOURCE_COLUMNS = ('slot_id', 'model', 'system', 'scenario', 'item', 'regime', 'strategy',
                  'seed', 'order', 'outer_repeat', 'execution_complete', 'score_complete',
                  'provider', 'cohort_id', 'selection', 'result_sha256',
                  'historical_trajectory', 'new_result_index')
# The frozen pre-repair source table, also identical to the first 18 columns of
# rescore/main/SOURCE_SELECTION.csv. This binds provenance when projecting it.
BASE_SOURCES_SHA256 = 'fb52849c2967ead9c5fd1a0e29e4177fe441203c899cb8a6fed58b4c7e7c7a9c'
PUBLIC_ENDPOINT_PROJECTION_PAYLOAD_SHA256 = 'd74c78e1d63e60f8fab8992199cb676cdd5babf81d260e7596c2c194e0737d58'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        columns, rows = reader.fieldnames, list(reader)
    require(columns and len(columns) == len(set(columns)), f'{path}: duplicate/missing columns')
    require(all(None not in row and all(v is not None for v in row.values()) for row in rows),
            f'{path}: malformed CSV row')
    return columns, rows


def indexed(rows, label):
    require(all(row.get('slot_id') for row in rows), f'{label}: empty slot ID')
    result = {row['slot_id']: row for row in rows}
    require(len(result) == len(rows), f'{label}: duplicate slot ID')
    return result


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def csv_digest(columns, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return hashlib.sha256(stream.getvalue().encode()).hexdigest()


def load_module(path):
    spec = importlib.util.spec_from_file_location('_public_hpo_rerun_scoring', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def finite_or_none(value):
    return value is None or (type(value) in (int, float) and math.isfinite(value))


def check_metrics(actual, expected, scoring, label):
    require(set(actual) == set(expected) == METRICS, f'{label}: six metric keys')
    for key in METRICS:
        require(finite_or_none(actual[key]) and finite_or_none(expected[key]),
                f'{label}.{key}: nonfinite/non-numeric metric')
        require(scoring.close(actual[key], expected[key]), f'{label}.{key}: metric mismatch')


def check_row(actual, expected, scoring, label, exact_metrics=False):
    require(actual.keys() == expected.keys(), f'{label}: column mismatch')
    for key in actual:
        if key == 'metrics_json' and not exact_metrics:
            check_metrics(json.loads(actual[key]), json.loads(expected[key]), scoring, label)
        else:
            require(actual[key] == expected[key], f'{label}.{key}: value mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--adoption', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-scalars', type=Path,
                        help='Frozen existing-trace-rescored 4698 rows, bound by manifest SHA256')
    parser.add_argument('--base-sources', type=Path,
                        help='Optional frozen source selection (18 original columns, or rescore superset)')
    parser.add_argument('--rebuild-output', type=Path,
                        help='Export scorer-produced completed rows and, only if ready, all 4698 rows')
    args = parser.parse_args()
    require(args.rebuild_output is None or args.base_scalars is not None,
            '--rebuild-output requires --base-scalars')
    require(args.base_sources is None or args.base_scalars is not None,
            '--base-sources requires --base-scalars')
    root = args.adoption
    manifest_path = root / 'FAIRNESS_MANIFEST.json'
    package_path = root / 'progress/scoring_inputs.jsonl.gz'
    completed_path = root / 'progress/completed_slot_scalars.csv'
    status_path = root / 'progress/slot_status.csv'
    official_path = root / 'new_official/slot_scalars.csv'
    official_sources_path = root / 'new_official/SOURCE_SELECTION.csv'
    verified_sources_path = root / 'progress/verified_sources.csv'
    projection_path = root / 'PUBLIC_ENDPOINT_PROJECTION.json'
    projection = None
    helper = args.repo / 'tools/rescore_hpo_protocol.py'
    protocol = args.repo / 'expgym/tool_protocol.py'
    sources = [manifest_path, package_path, completed_path, status_path, helper, protocol, Path(__file__)]
    if projection_path.exists():
        sources.extend([projection_path, root / 'ORIGINAL_PUBLIC_REPLAY_CHECKS.json',
                        verified_sources_path, root / 'new_official/SOURCE_INVENTORY.csv',
                        root / 'project_public_endpoints.py'])
    if args.base_scalars is not None:
        sources.append(args.base_scalars)
    if args.base_sources is not None:
        sources.extend([args.base_sources, verified_sources_path])
    protected = {path.resolve() for path in sources + [official_path, official_sources_path,
                                                     verified_sources_path]}
    output_paths = [args.output]
    if args.rebuild_output is not None:
        output_paths += [args.rebuild_output / 'completed_slot_scalars.csv',
                         args.rebuild_output / 'slot_scalars.csv',
                         args.rebuild_output / 'SOURCE_SELECTION.csv']
    require(len({p.resolve() for p in output_paths}) == len(output_paths), 'Output paths overlap')
    require(all(path.resolve() not in protected for path in output_paths),
            'Refusing to overwrite a source artifact')
    input_hashes = {path: sha(path) for path in sources}
    manifest = json.loads(manifest_path.read_text())
    require(manifest['adoption_scope'] == 'hpo97_stage_only' and
            manifest['global_formal_adoption_claim'] is False, 'HPO-only adoption scope required')
    require(type(manifest['adoption_ready']) is bool, 'adoption_ready must be a boolean')
    require(manifest['pre_registered_pools'] == 97 and manifest['pre_registered_members'] == 388,
            'Wrong pre-registered cohort size')
    require(manifest['expected_model_counts'] == EXPECTED, 'Wrong pre-registered model counts')
    if projection_path.exists():
        projection = json.loads(projection_path.read_text())
        require(projection.get('schema') == 'expgym.hpo-public-endpoint-projection.v1' and
                projection.get('status') == 'PASS' and projection.get('slots') == 97,
                'Invalid endpoint projection receipt')
        projection_payload = {k:v for k,v in projection.items()
                              if k not in {'public_replay_script_sha256', 'projection_payload_sha256'}}
        payload_sha = hashlib.sha256(json.dumps(projection_payload, ensure_ascii=False, sort_keys=True,
            allow_nan=False, separators=(',', ':')).encode()).hexdigest()
        require(payload_sha == projection['projection_payload_sha256'] ==
                PUBLIC_ENDPOINT_PROJECTION_PAYLOAD_SHA256,
                'Trusted endpoint projection payload SHA256 mismatch')
        require(projection['original_scientific_manifest_sha256'] == input_hashes[manifest_path],
                'Projection original scientific manifest mismatch')
        require(projection['public_replay_script_sha256'] == sha(Path(__file__)) and
                projection['projection_tool_sha256'] == sha(root / 'project_public_endpoints.py'),
                'Projection publication code identity mismatch')
        receipt_path = root / 'ORIGINAL_PUBLIC_REPLAY_CHECKS.json'
        require(projection['original_public_replay_receipt_sha256'] == input_hashes[receipt_path],
                'Original replay receipt SHA256 mismatch')
        original_receipt = json.loads(receipt_path.read_text())
        require(original_receipt['status'] == 'PASS' and original_receipt['adoption_ready'] is True and
                original_receipt['source_manifest_sha256'] == input_hashes[manifest_path] and
                original_receipt['input_package_sha256'] == manifest['public_scoring_inputs_sha256'] and
                original_receipt['replay_script_sha256'] == projection['original_replay_script_sha256'],
                'Original replay receipt scientific identity mismatch')
        projected_files = {row['path']: row for row in projection['files']}
        required_projected = {'progress/scoring_inputs.jsonl.gz', 'progress/verified_sources.csv',
                              'new_official/SOURCE_INVENTORY.csv'}
        require(len(projection['files']) == 3 and set(projected_files) == required_projected,
                'Projection must enumerate exactly three endpoint-bearing artifacts')
        for relative, record in projected_files.items():
            expected_original = (manifest['public_scoring_inputs_sha256'] if relative.endswith('.gz')
                                 else original_receipt['verified_sources_sha256'])
            require(record['original_sha256'] == expected_original and
                    record['public_sha256'] == input_hashes[root / relative],
                    'Projection original/public artifact SHA256 mismatch: ' + relative)
        require(projected_files['progress/verified_sources.csv']['public_sha256'] ==
                projected_files['new_official/SOURCE_INVENTORY.csv']['public_sha256'],
                'Projected source inventories must remain byte-identical')
        expected_unchanged = {'FAIRNESS_MANIFEST.json', 'progress/slot_status.csv',
            'progress/completed_slot_scalars.csv', 'progress/member_scores.csv',
            'new_official/slot_scalars.csv', 'new_official/SOURCE_SELECTION.csv',
            'new_official/hpo_rerun_slot_scalars.csv', 'NEW_RUNTIME_COMPARISON.csv',
            'adopted_hpo_code_versions.csv', 'adopted_hpo_model_budget_strategy.csv'}
        require(set(projection['unchanged_scientific_artifacts']) == expected_unchanged,
                'Projection unchanged-scientific-artifact scope mismatch')
        for relative, expected in projection['unchanged_scientific_artifacts'].items():
            require(sha(root / relative) == expected, 'Projection changed scientific artifact: ' + relative)
        require(projection['all_non_endpoint_values_identical'] is True and
                projection['original_private_files_unchanged'] is True and projection['model_calls'] == 0,
                'Projection scope claims missing')
    for path, key in ((package_path, 'public_scoring_inputs_sha256'),
                      (completed_path, 'completed_slot_scalars_sha256'),
                      (helper, 'formal_scoring_helper_sha256'), (protocol, 'parser_sha256')):
        expected = (projected_files['progress/scoring_inputs.jsonl.gz']['public_sha256']
                    if projection is not None and path == package_path else manifest[key])
        require(input_hashes[path] == expected, f'{path.name}: manifest/projection SHA256 mismatch')
    scoring = load_module(helper)
    with gzip.open(package_path, 'rt') as stream:
        packages = [json.loads(line) for line in stream]
    package_by = indexed(packages, 'scoring package')
    if projection is not None:
        slot_projection = indexed(projection['slot_bindings'], 'endpoint projection slots')
        require(set(slot_projection) == set(package_by) and len(slot_projection) == 97,
                'Projection slot membership mismatch')
        _, projected_source_rows = read(verified_sources_path)
        projected_source_by = indexed(projected_source_rows, 'projected verified sources')
        require(set(projected_source_by) == set(package_by), 'Projected source membership mismatch')
        for sid, pool in package_by.items():
            record = slot_projection[sid]; config = pool['config']; source = projected_source_by[sid]
            canonical = lambda value: hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                allow_nan=False, separators=(',', ':')).encode()).hexdigest()
            require(record['public_config_sha256'] == canonical(config) and
                    record['original_config_sha256'] == source['config_sha256'] and
                    record['config_without_endpoint_sha256'] == canonical({k:v for k,v in config.items() if k!='base_url'}) and
                    record['source_without_endpoint_sha256'] == canonical({k:v for k,v in source.items() if k!='provider_base_url'}),
                    sid + ': original/public configuration projection mismatch')
            require(record['original_result_sha256'] == pool['result_sha256'] == source['result_sha256'] and
                    record['new_job_id'] == pool['new_job_id'] == source['new_job_id'],
                    sid + ': projected runtime identity mismatch')
            value = str(config.get('base_url') or '')
            require(source['provider_base_url'] == value, sid + ': projected endpoint/source mismatch')
            require(type(record['endpoint_redacted']) is bool, sid + ': invalid redaction flag')
            if record['endpoint_redacted']:
                require(value == 'endpoint_sha256:' + record['original_endpoint_sha256'],
                        sid + ': opaque endpoint identity mismatch')
            else:
                require(hashlib.sha256(value.encode()).hexdigest() == record['original_endpoint_sha256'] and
                        record['original_config_sha256'] == record['public_config_sha256'],
                        sid + ': preserved public endpoint identity mismatch')
        redacted = sum(row['endpoint_redacted'] for row in slot_projection.values())
        require(redacted == projection['redacted_slots'] and 97-redacted == projection['preserved_public_or_empty_slots'] and
                projection['fields_changed'] == redacted*3 and
                all(row['endpoint_fields_changed'] == redacted for row in projected_files.values()),
                'Projection redaction counters mismatch')
    columns, saved_rows = read(completed_path)
    require(set(columns) == set(CORE + CHANGED), 'Unexpected scalar schema')
    saved = indexed(saved_rows, 'completed scalars')
    _, status_rows = read(status_path)
    statuses = indexed(status_rows, 'slot status')
    require(len(statuses) == 97, 'Slot status must enumerate all 97 planned pools')
    require(dict(Counter(ALIASES[row['model']] for row in status_rows)) == EXPECTED,
            'Planned status model counts mismatch')
    require(dict(Counter(row['state'] for row in status_rows)) == manifest['status_counts'],
            'Status counters do not match the 97-row inventory')
    verified = {sid for sid, row in statuses.items() if row['state'] == 'verified_complete'}
    require(set(saved) == set(package_by) == verified, 'Completed status/package/scalar membership differs')
    require(len(packages) == manifest['verified_complete_pools'], 'Complete pool count mismatch')
    require(dict(Counter(ALIASES[statuses[sid]['model']] for sid in verified)) ==
            manifest['verified_model_counts'], 'Complete model counts mismatch')
    base_rows, base = None, None
    if args.base_scalars is not None:
        require(input_hashes[args.base_scalars] == manifest['existing_trace_rescored_scalars_sha256'],
                'Wrong baseline: expected frozen existing-trace-rescored scalars')
        base_columns, base_rows = read(args.base_scalars)
        base = indexed(base_rows, 'baseline scalars')
        require(base_columns == columns and len(base) == 4698, 'Baseline schema/count mismatch')
        require(set(statuses) <= set(base), 'Planned pools missing from baseline')
        for sid, status in statuses.items():
            require(base[sid]['system'] == 'poolact' and base[sid]['scenario'] == 'tuning',
                    f'{sid}: replacement is not an HPO pool')
            require(all(base[sid][key] == status[key] for key in IDENTITY),
                    f'{sid}: planned identity differs from baseline')
    base_sources, new_sources = None, None
    if args.base_sources is not None:
        source_columns, source_rows = read(args.base_sources)
        require(source_columns[:18] == list(SOURCE_COLUMNS), 'Source baseline column order mismatch')
        base_sources = [{key: row[key] for key in SOURCE_COLUMNS} for row in source_rows]
        base_source_by = indexed(base_sources, 'baseline sources')
        require(len(base_source_by) == 4698 and
                csv_digest(SOURCE_COLUMNS, base_sources) == BASE_SOURCES_SHA256,
                'Wrong source baseline: projected 18-column SHA256 mismatch')
        require([row['slot_id'] for row in base_sources] == [row['slot_id'] for row in base_rows],
                'Source baseline order/membership differs from scalar baseline')
        for sid, source in base_source_by.items():
            require(all(source[key] == base[sid][key] for key in CORE if key != 'family'),
                    f'{sid}: source/scalar baseline identity mismatch')
        _, source_rows = read(verified_sources_path)
        new_sources = indexed(source_rows, 'verified sources')
        require(set(new_sources) == verified, 'Verified source/package membership differs')
        for sid, source in new_sources.items():
            pool, status = package_by[sid], statuses[sid]
            require(source['old_result_sha256'] == base_source_by[sid]['result_sha256'] and
                    source['model'] == pool['model'] and source['members'] == '4' and
                    source['result_sha256'] == pool['result_sha256'] and
                    source['new_job_id'] == pool['new_job_id'] and
                    source['completion_sha256'] == status['completion_sha256'],
                    f'{sid}: verified source binding mismatch')
            config = pool['config']
            config_sha = hashlib.sha256(json.dumps(config, ensure_ascii=False, sort_keys=True,
                                                   allow_nan=False, separators=(',', ':')).encode()).hexdigest()
            expected_config_sha = (slot_projection[sid]['public_config_sha256'] if projection is not None
                                   else source['config_sha256'])
            require(expected_config_sha == config_sha and
                    source['result_bytes'] == str(pool['result_bytes']) and
                    source['graph_check_status'] == pool['graph_check']['status'] and
                    source['poolact_protocol'] == config['poolact_protocol'] and
                    source['source_kind'] == 'new_runtime_complete_pool' and
                    source['rerun_reason'] == status['rerun_reason'],
                    f'{sid}: verified source configuration/result metadata mismatch')
            for source_key, config_key in (('provider_model', 'model'), ('provider_backend', 'backend'),
                                           ('provider_base_url', 'base_url')):
                require(source[source_key] == str(config.get(config_key) or ''),
                        f'{sid}: verified source {source_key} mismatch')
            for key in ('runtime_source_tree_sha256', 'runtime_core_commit', 'runtime_snapshot_commit',
                        'parser_sha256', 'graph_sha256'):
                require(source[key] == manifest[key], f'{sid}: verified source {key} mismatch')
    certificates = {}
    for pool in packages:
        for member in pool['agents']:
            cert = member['benchmark_certificate']
            if cert is not None:
                require(cert['item'] == pool['item'] and isinstance(cert['answer'], str) and
                        cert['performance'] is not None and finite_or_none(cert['performance']),
                        f"{pool['slot_id']}: invalid benchmark certificate")
                key = cert['item'], hashlib.sha256(cert['answer'].encode()).hexdigest()
                value = {'answer': cert['answer'], 'performance': cert['performance'],
                         'evaluation_reason': 'recorded_data_backed_benchmark_certificate'}
                require(key not in certificates or certificates[key] == value,
                        'Conflicting benchmark certificates')
                certificates[key] = value
    evaluator = scoring.Evaluator(certificates=certificates)
    recomputed = {}
    members = 0
    for pool in packages:
        sid = pool['slot_id']
        status, scalar, config = statuses[sid], saved[sid], pool['config']
        require(all(str(pool[key]) == scalar[key] == status[key] for key in IDENTITY),
                f'{sid}: package/scalar/status identity mismatch')
        require(pool['source_tree_sha256'] == manifest['runtime_source_tree_sha256'] and
                pool['new_job_id'] == status['new_job_id'] and
                pool['result_sha256'] == status['result_sha256'], f'{sid}: source binding mismatch')
        require(pool['execution_complete'] is True and status['execution_complete'] == 'True' and
                not status['error'], f'{sid}: execution is not verified complete')
        require(type(pool['seed']) is int and config['seed'] == pool['seed'] and
                config['scenario'] == 'tuning' and config['tuning_task'] == pool['item'] and
                config['cost_regime'] == pool['regime'] and config['strategies'] == [pool['strategy']],
                f'{sid}: config identity mismatch')
        require(len(pool['agents']) == 4 and [m['agent_id'] for m in pool['agents']] == [0, 1, 2, 3],
                f'{sid}: expected a complete four-member pool')
        require([m['seed'] for m in pool['agents']] == config['agent_seeds'] ==
                list(range(pool['seed'], pool['seed'] + 4)), f'{sid}: member seed mismatch')
        perfs, finals = [], []
        for member in pool['agents']:
            label = f"{sid}/agent{member['agent_id']}"
            extracted = scoring.parse_turn(member['terminal_turn'], config['tool_protocol'],
                                            scoring.tool_protocol.parse_final_answer)
            require(extracted == member['extracted_answer'], label + ': extracted answer mismatch')
            require(len(member['eval_records']) == len(member['record_ids']), label + ': record ID mismatch')
            answer, perf, source, record, _ = scoring.select_answer(
                extracted, member['eval_records'], member['record_ids'], pool['item'], evaluator)
            require(finite_or_none(perf) and finite_or_none(member['performance']),
                    label + ': nonfinite/non-numeric performance')
            require(answer == member['final_answer'] and scoring.close(perf, member['performance']),
                    label + ': selected answer/performance mismatch')
            require(source == member['answer_score_source'] and record == member['selected_record'],
                    label + ': selection provenance mismatch')
            if perf is not None:
                measured, _ = evaluator.evaluate(pool['item'], answer)
                require(finite_or_none(measured) and scoring.close(measured, perf),
                        label + ': benchmark certificate mismatch')
            perfs.append(perf)
            finals.append(answer)
            members += 1
        metrics = scoring.perfs_metrics(perfs, finals, pool['item'], {pool['item']: pool['oracle_reference']})
        check_metrics(metrics, pool['metrics'], scoring, sid + '/package')
        check_metrics(metrics, json.loads(scalar['metrics_json']), scoring, sid + '/scalar')
        complete = all(perf is not None for perf in perfs)
        require(pool['score_complete'] is complete and status['score_complete'] == str(complete),
                f'{sid}: score completeness mismatch (normal None is permitted)')
        row = dict(base[sid] if base is not None else scalar)
        alias = ALIASES[pool['model']]
        row.update(metrics_json=json.dumps(metrics, ensure_ascii=False, sort_keys=True,
                                          allow_nan=False, separators=(',', ':')),
                   execution_complete='True', score_complete=str(complete),
                   provider_cohort='openrouter_google_ai_studio' if alias == 'gemini' else 'preserved_historical_provider',
                   cohort_id='hpo_protocol_repair_20260918_' + alias + '_v2')
        check_row(row, scalar, scoring, sid + '/completed-row')
        if new_sources is not None:
            require(new_sources[sid]['cohort_id'] == row['cohort_id'], f'{sid}: source cohort mismatch')
        recomputed[sid] = row
    require(members == 4 * len(recomputed) == manifest['verified_complete_members'],
            'Complete member count mismatch')
    merged = None
    merged_sources, adopted_source_columns = None, None
    official_fields_checked = 0
    if manifest['adoption_ready']:
        require(len(recomputed) == 97 and members == 388 and set(recomputed) == set(statuses) and
                manifest['status'] == 'PASS' and not manifest['errors'] and
                manifest['verified_model_counts'] == EXPECTED, 'Full 97-pool / 388-member gate failed')
        require(manifest['adopted_main_slots'] == 4698 and manifest['replaced_slots'] == 97 and
                manifest['unchanged_rescored_slots'] == 4601, 'Wrong official replacement counts')
        input_hashes[official_path] = sha(official_path)
        require(input_hashes[official_path] == manifest['official_slot_scalars_sha256'],
                'Official scalar SHA256 mismatch')
        official_columns, official_rows = read(official_path)
        official = indexed(official_rows, 'official scalars')
        require(official_columns == columns and len(official) == 4698,
                'Official scalar schema/count mismatch')
        for sid, row in recomputed.items():
            require(sid in official, f'{sid}: missing official replacement')
            check_row(row, official[sid], scoring, sid + '/official-replacement')
        official_fields_checked = len(recomputed) * len(columns)
        if base is not None:
            require([row['slot_id'] for row in official_rows] == [row['slot_id'] for row in base_rows],
                    'Official row order/membership differs from baseline')
            merged = [recomputed.get(row['slot_id'], row) for row in base_rows]
            for row in merged:
                sid = row['slot_id']
                check_row(row, official[sid], scoring, sid + '/official', exact_metrics=sid not in recomputed)
            require(sum(row['slot_id'] not in recomputed for row in merged) == 4601,
                    'Expected 4601 untouched baseline rows')
            official_fields_checked = len(merged) * len(columns)
        if base_sources is not None:
            merged_sources = []
            for source in base_sources:
                row = dict(source)
                sid = row['slot_id']
                if sid in recomputed:
                    replacement, provenance = recomputed[sid], new_sources[sid]
                    row.update(old_result_sha256=row['result_sha256'],
                               result_sha256=provenance['result_sha256'],
                               cohort_id=replacement['cohort_id'], selection='new_runtime_protocol_repair',
                               provider=replacement['provider_cohort'],
                               execution_complete=replacement['execution_complete'],
                               score_complete=replacement['score_complete'],
                               historical_trajectory='', new_result_index='',
                               old_historical_trajectory=row['historical_trajectory'],
                               old_new_result_index=row['new_result_index'],
                               new_result_path=provenance['result_path'], new_job_id=provenance['new_job_id'],
                               runtime_source_tree_sha256=manifest['runtime_source_tree_sha256'],
                               runtime_core_commit=manifest['runtime_core_commit'])
                    row['runtime_snapshot_commit'] = manifest['runtime_snapshot_commit']
                merged_sources.append(row)
            adopted_source_columns = list(dict.fromkeys(key for row in merged_sources for key in row))
            input_hashes[official_sources_path] = sha(official_sources_path)
            require(input_hashes[official_sources_path] == manifest['official_source_selection_sha256'],
                    'Official source selection SHA256 mismatch')
            official_source_columns, official_source_rows = read(official_sources_path)
            indexed(official_source_rows, 'official sources')
            require(official_source_columns == adopted_source_columns and len(official_source_rows) == 4698,
                    'Official source selection schema/count mismatch')
            for rebuilt, saved_source in zip(merged_sources, official_source_rows):
                require({key: rebuilt.get(key, '') for key in adopted_source_columns} == saved_source,
                        f"{rebuilt['slot_id']}: official source selection differs")
            require(csv_digest(adopted_source_columns, merged_sources) ==
                    manifest['official_source_selection_sha256'], 'Rebuilt source selection SHA256 mismatch')
    # A concurrent collector refresh must not create an apparently coherent replay.
    require(all(sha(path) == value for path, value in input_hashes.items()),
            'Source artifacts changed during replay; retry on a fixed snapshot')
    exported = {}
    invalidated = []
    if args.rebuild_output is not None:
        destination = args.rebuild_output
        formal = destination / 'slot_scalars.csv'
        for path, fresh in ((formal, merged), (destination / 'SOURCE_SELECTION.csv', merged_sources)):
            if fresh is None and path.exists():
                archived = destination / 'invalidated' / (path.stem + '.' + sha(path) + '.csv')
                archived.parent.mkdir(parents=True, exist_ok=True)
                path.replace(archived)
                invalidated.append(str(archived))
        completed = destination / 'completed_slot_scalars.csv'
        write_csv(completed, columns, [recomputed[row['slot_id']] for row in saved_rows])
        exported['completed_slot_scalars'] = {'path': str(completed), 'sha256': sha(completed),
                                             'rows': len(recomputed)}
        if merged is not None:
            write_csv(formal, columns, merged)
            exported['slot_scalars'] = {'path': str(formal), 'sha256': sha(formal), 'rows': len(merged)}
        if merged_sources is not None:
            selected = destination / 'SOURCE_SELECTION.csv'
            write_csv(selected, adopted_source_columns, merged_sources)
            exported['source_selection'] = {'path': str(selected), 'sha256': sha(selected), 'rows': len(merged_sources)}
    result = dict(
        status='PASS', adoption_ready=manifest['adoption_ready'], adoption_scope=manifest['adoption_scope'],
        global_formal_adoption_claim=False, completed_pools=len(recomputed), completed_members=members,
        planned_pools_checked=len(statuses), parser_sha256=manifest['parser_sha256'],
        formal_scoring_helper_sha256=manifest['formal_scoring_helper_sha256'],
        replay_script_sha256=sha(Path(__file__)), input_package_sha256=input_hashes[package_path],
        source_manifest_sha256=input_hashes[manifest_path], slot_status_sha256=input_hashes[status_path],
        source_plan_sha256=manifest['source_plan_sha256'],
        base_scalars_sha256=input_hashes.get(args.base_scalars), certificate_count=len(certificates),
        base_sources_sha256=input_hashes.get(args.base_sources),
        projected_base_sources_sha256=BASE_SOURCES_SHA256 if base_sources is not None else None,
        verified_sources_sha256=input_hashes.get(verified_sources_path),
        certificate_uses=evaluator.certificate_uses, model_calls=0,
        completed_row_fields_checked=len(recomputed) * len(columns),
        official_row_fields_checked=official_fields_checked, all_official_rows_checked=merged is not None,
        untouched_rows_checked=4601 if merged is not None else 0,
        official_source_row_fields_checked=4698 * len(adopted_source_columns) if merged_sources is not None else 0,
        rebuilt_outputs=exported, prior_rebuilt_official_archived=invalidated,
        scope='Re-extract completed terminal texts, select visible evaluations, and recompute six MI/BoN/Gap0 metrics. With the bound baseline and full gate, rebuild all 4698 rows and compare every official field, preserving all 4601 untouched rows exactly.',
        limitations=[
            'Benchmark performance is replayed from bound data-backed certificates, not rerun against private tables.',
            'The public 97-row status inventory is checked for identities and counts. The private source-plan hash, raw receipts, full messages, graph/source checks and first-attempt selection remain collector attestations.',
            'HPO readiness does not establish global formal adoption; auxiliary control-flow experiments remain a separate gate.'])
    result['endpoint_projection'] = (dict(status='VERIFIED',
        projection_receipt_sha256=input_hashes[projection_path],
        original_scientific_manifest_sha256=input_hashes[manifest_path],
        original_input_package_sha256=manifest['public_scoring_inputs_sha256'],
        public_input_package_sha256=input_hashes[package_path],
        original_verified_sources_sha256=original_receipt['verified_sources_sha256'],
        public_verified_sources_sha256=input_hashes[verified_sources_path],
        original_replay_script_sha256=projection['original_replay_script_sha256'],
        redacted_slots=projection['redacted_slots'],
        original_config_hashes_preserved=True,
        scope='Only endpoint fields are publication-projected. Original run/config/result/gate identities remain original; public replay validates the receipt and projected copies.')
        if projection is not None else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
