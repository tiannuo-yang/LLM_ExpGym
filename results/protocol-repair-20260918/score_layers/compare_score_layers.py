#!/usr/bin/env python3
"""Portable score-layer join. No traces, benchmark data or model access needed."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def read_csv(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def indexed(path):
    table = read_csv(path)
    result = {row['slot_id']: row for row in table}
    if len(table) != len(result):
        raise ValueError('Duplicate slot_id in ' + path.name)
    return result


def write_csv(path, table):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)


def equivalent(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return abs(a - b) < 1e-12
    return a == b


def delta(after, before):
    if after is None or before is None:
        return None
    return {key: after[key] - before[key] for key in sorted(after.keys() & before.keys())
            if isinstance(after[key], (float, int)) and isinstance(before[key], (float, int))}


def json_cell(value):
    return '' if value is None else canonical(value)


def main(args):
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((args.reference / 'DIAGNOSTIC_REFERENCE.json').read_text())
    for name, info in metadata['reference_files'].items():
        assert sha(args.reference / name) == info['sha256'], name
    diagnostic = indexed(args.reference / 'prior_diagnostic_reference.csv')
    sources = indexed(args.main / 'SOURCE_SELECTION.csv')
    old = indexed(args.main / 'slot_scalars.legacy.csv')
    repaired = indexed(args.main / 'slot_scalars.csv')
    diffs = indexed(args.main / 'sample_diff.csv')
    assert len(sources) == 4698 and sources.keys() == old.keys() == repaired.keys() == diffs.keys()
    provided = [args.official is not None, args.official_sources is not None, args.adoption is not None]
    if any(provided) and not all(provided):
        raise ValueError('--official, --official-sources and --adoption must be supplied together')
    official = indexed(args.official) if args.official else None
    official_sources = indexed(args.official_sources) if args.official_sources else None
    adoption = indexed(args.adoption) if args.adoption else None
    if official is not None:
        assert official.keys() == official_sources.keys() == adoption.keys() == sources.keys()
    comparison, decoded = [], []
    for slot in sorted(sources):
        source, prior, new, diff = sources[slot], old[slot], repaired[slot], diffs[slot]
        identity = {key: source[key] for key in
                    ('slot_id', 'model', 'system', 'scenario', 'regime', 'strategy',
                     'item', 'seed', 'order', 'outer_repeat')}
        for row in (prior, new, diff):
            assert all(str(row[key]) == str(value) for key, value in identity.items())
        before = json.loads(prior['metrics_json'])
        after = json.loads(new['metrics_json'])
        assert equivalent(before, json.loads(diff['old_metrics_json']))
        assert equivalent(after, json.loads(diff['new_metrics_json']))
        assert source['result_sha256'] == diff['source_sha256']
        diagnosis = diagnostic.get(slot)
        previous_diagnostic = None
        diagnostic_status = 'not_evaluated'
        if diagnosis:
            assert diagnosis['source_sha256'] == source['result_sha256']
            assert all(diagnosis[key] == identity[key] for key in
                       ('model', 'system', 'scenario', 'regime', 'strategy', 'item', 'order'))
            mapping = json.loads(diagnosis['metric_mapping_json'])
            diagnostic_old = {mapping[key]: value for key, value in
                              json.loads(diagnosis['diagnostic_old_endpoint_metrics_json']).items()}
            previous_diagnostic = {mapping[key]: value for key, value in
                                   json.loads(diagnosis['prior_diagnostic_endpoint_metrics_json']).items()}
            assert all(equivalent(value, before[key]) for key, value in diagnostic_old.items() if key in before)
            assert set(previous_diagnostic) <= {'label_acc', 'evidence_acc', 'verification_eff',
                                                'label_acc_mv', 'evidence_acc_mv'}
            diagnostic_status = diagnosis['diagnostic_status']
        final, final_sha, final_layer = None, '', ''
        if official is not None:
            entry = official[slot]
            assert all(entry[key] == value for key, value in identity.items() if key in entry)
            final = json.loads(entry['metrics_json'])
            final_sha = official_sources[slot][args.official_source_sha_column]
            assert len(final_sha) == 64 and all(c in '0123456789abcdef' for c in final_sha)
            final_layer = adoption[slot][args.adoption_layer_column]
            assert final_layer, 'Empty adopted layer'
            assert 'pending' not in final_layer.lower(), 'Pending layer cannot be final official'
            assert adoption[slot].get('adoption_status', '').lower() not in (
                'pending', 'blocked', 'not_adopted'), 'Non-adopted slot in final manifest'
            stated_sha = adoption[slot].get(args.official_source_sha_column)
            if stated_sha:
                assert stated_sha == final_sha
        comparison.append({**identity, 'historical_source_sha256': source['result_sha256'],
            'old_official_metrics_json': canonical(before),
            'prior_diagnostic_status': diagnostic_status,
            'prior_diagnostic_metrics_json': json_cell(previous_diagnostic),
            'existing_trace_rescored_metrics_json': canonical(after),
            'existing_trace_score_change_reason': diff['change_reason'],
            'final_official_status': 'adopted_from_supplied_manifest' if final is not None else 'pending_uniform_rerun_adoption',
            'final_official_metrics_json': json_cell(final),
            'final_official_source_sha256': final_sha,
            'final_official_adopted_layer': final_layer,
            'final_source_differs_from_historical': '' if final is None else final_sha != source['result_sha256'],
            'delta_prior_diagnostic_minus_old_official_json': json_cell(delta(previous_diagnostic, before)),
            'delta_existing_trace_minus_old_official_json': json_cell(delta(after, before)),
            'delta_existing_trace_minus_prior_diagnostic_json': json_cell(delta(after, previous_diagnostic)),
            'delta_final_official_minus_existing_trace_json': json_cell(delta(final, after)),
        })
        decoded.append((identity, before, previous_diagnostic, after, final))
    groups = defaultdict(list)
    for item in decoded:
        identity = item[0]
        if identity['scenario'] == 'evidence_audit':
            groups[tuple(identity[key] for key in ('model', 'system', 'regime', 'strategy'))].append(item)
    summary = []
    for key, group in sorted(groups.items()):
        model, system, regime, strategy = key
        for metric in ('label_acc', 'evidence_acc'):
            slot_metric = metric if system == 'expgym' else metric + '_mv'
            record = dict(zip(('model', 'system', 'regime', 'strategy'), key))
            record.update(metric=slot_metric, slots=len(group), display_unit='percentage_points')
            for i, layer in enumerate(('old_official', 'prior_diagnostic', 'existing_trace_rescored', 'final_official'), 1):
                values = [item[i][slot_metric] for item in group
                          if item[i] is not None and isinstance(item[i].get(slot_metric), (int, float))]
                record[layer + '_count'] = len(values)
                record[layer + '_mean_percent'] = sum(values) / len(values) * 100 if values else ''
                record[layer + '_coverage'] = ('complete' if len(values) == len(group)
                                                else 'partial' if values else 'not_evaluated')
            summary.append(record)
    write_csv(output / 'score_layer_comparison.csv', comparison)
    write_csv(output / 'audit_layer_group_means.csv', summary)
    glm = next(row for row in summary if row['model'] == 'glm-5.3'
               and row['system'] == 'expgym' and row['regime'] == 'cost_free' and row['metric'] == 'evidence_acc')
    assert equivalent(glm['prior_diagnostic_mean_percent'], 83.86123680241326)
    assert equivalent(glm['existing_trace_rescored_mean_percent'], 86.42533936651583)
    status_counts = dict(Counter(row['prior_diagnostic_status'] for row in comparison))
    assert status_counts == {'not_evaluated': 3528, 'explicit_n1_diagnostic': 9,
                             'derived_unchanged_under_exhaustive_prior_policy': 693,
                             'explicit_pool_diagnostic': 468}
    inputs = {name: sha(args.main / name) for name in
              ('SOURCE_SELECTION.csv', 'slot_scalars.legacy.csv', 'slot_scalars.csv', 'sample_diff.csv')}
    inputs.update({name: sha(args.reference / name) for name in
                   ('DIAGNOSTIC_REFERENCE.json', 'prior_diagnostic_reference.csv')})
    if official is not None:
        inputs.update(official_scores=sha(args.official), official_sources=sha(args.official_sources),
                      official_adoption=sha(args.adoption))
    report = {'status': 'PASS', 'schema': 'expgym.score-layer-comparison.v1',
        'rows': len(comparison), 'diagnostic_status_counts': status_counts,
        'official_adoption_complete': official is not None,
        'final_official_status': 'supplied_manifest_joined' if official is not None else 'pending_uniform_rerun_adoption',
        'old_official_commit': '297c3d00a006f33fc5a8ca799ce91d327d92839e',
        'existing_trace_scoring_core_commit': '0e6c51b6d86f42437038518c2fc8adc510901c0b',
        'diagnostic_original_sha256': metadata['original_diagnostic']['sha256'],
        'glm_free_evidence_acc_means_percent': {layer: glm[layer + '_mean_percent'] for layer in
            ('old_official', 'prior_diagnostic', 'existing_trace_rescored', 'final_official')},
        'input_sha256': inputs, 'output_sha256': {name: sha(output / name) for name in
            ('score_layer_comparison.csv', 'audit_layer_group_means.csv')},
        'script_sha256': sha(Path(__file__)), 'model_calls': 0,
        'null_policy': 'Blank diagnostic JSON means not evaluated; null inside JSON is an explicitly reported unavailable metric. Blank final official JSON means adoption pending. Missing metrics are never filled with zero.',
        'delta_policy': 'Deltas are computed only for shared numeric keys; prior diagnostic never supplies MI, Search, HPO or unreported verification_eff.',
    }
    (output / 'CHECKS.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(canonical({key: report[key] for key in ('status', 'rows', 'diagnostic_status_counts',
        'official_adoption_complete', 'glm_free_evidence_acc_means_percent')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, required=True,
                        help='Frozen existing-trace rescore main directory containing four CSV inputs')
    parser.add_argument('--reference', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--official', type=Path, help='Future adopted 4698-row slot_scalars CSV')
    parser.add_argument('--official-sources', type=Path, help='Future 4698-row slot/source SHA index')
    parser.add_argument('--adoption', type=Path, help='Future 4698-row adopted-layer manifest CSV')
    parser.add_argument('--official-source-sha-column', default='result_sha256')
    parser.add_argument('--adoption-layer-column', default='adopted_layer')
    main(parser.parse_args())
