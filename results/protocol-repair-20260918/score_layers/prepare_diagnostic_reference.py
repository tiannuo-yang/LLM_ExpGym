#!/usr/bin/env python3
"""Export numeric prior diagnostics without raw answers or private path fields."""
import argparse
from collections import Counter
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


def write_csv(path, rows, columns):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def close(left, right):
    return left == right or (isinstance(left, (int, float)) and isinstance(right, (int, float))
                             and abs(left - right) < 1e-12)


def prepare(diagnostic, scanner, n1_index, main, output):
    original = json.loads(diagnostic.read_text())
    selected = read_csv(main / 'SOURCE_SELECTION.csv')
    previous = {r['slot_id']: r for r in read_csv(main / 'slot_scalars.legacy.csv')}
    by_sha = {r['result_sha256']: r for r in selected}
    assert len(selected) == len(by_sha) == len(previous) == 4698
    original_n1 = read_csv(n1_index)
    n1_sources = {r['result_sha256'] for r in selected
                  if r['system'] == 'expgym' and r['scenario'] == 'evidence_audit'}
    assert len(original_n1) == len(n1_sources) == 702
    assert {r['trace_sha256'] for r in original_n1} == n1_sources
    assert original['summary']['scanned_agents'] == {'n1': 702, 'n4': 1872}
    assert len(original['hits']) == 23 and len(original['pool_diagnostics']) == 468

    def identity(source, expected_system, expected_model, expected_regime, doc_index,
                 strategy=None, order=None):
        row = by_sha[source]
        assert row['system'] == expected_system and row['scenario'] == 'evidence_audit'
        assert row['model'] == expected_model and row['regime'] == expected_regime
        assert row['item'] == 'cc-large:' + str(doc_index)
        if strategy is not None:
            assert row['strategy'] == strategy
        if order is not None:
            assert row['order'] == str(order)
        return {key: row[key] for key in
                ('slot_id', 'model', 'system', 'scenario', 'regime', 'strategy', 'item', 'order')}

    hits = []
    n1_hits = {}
    for hit in original['hits']:
        is_n1 = hit['system'] == 'n1'
        ident = identity(hit['sha256'], 'expgym' if is_n1 else 'poolact', hit['model'],
                         hit['regime'], hit['doc_index'], hit.get('strategy'), hit.get('order'))
        hits.append({**ident, 'source_sha256': hit['sha256'],
                     'diagnostic_agent_index': hit['agent_index'], 'mechanism': hit['mechanism'],
                     'old_metrics_json': canonical(hit['old_metrics']),
                     'prior_diagnostic_metrics_json': canonical(hit['new_metrics']),
                     'strict_structured_suffix': hit['strict_structured_suffix']})
        if is_n1:
            assert hit['sha256'] not in n1_hits
            n1_hits[hit['sha256']] = hit
    assert len(n1_hits) == 9
    reference, public_n1 = [], []
    for row in original_n1:
        ident = identity(row['trace_sha256'], 'expgym', row['model'], row['budget'],
                         row['doc_index'], order=row['order'])
        old = {'label_acc': float(row['label_acc']), 'evidence_acc': float(row['evidence_acc'])}
        baseline = json.loads(previous[ident['slot_id']]['metrics_json'])
        assert all(close(value, baseline[key]) for key, value in old.items())
        hit = n1_hits.get(row['trace_sha256'])
        if hit:
            assert all(close(value, hit['old_metrics'][key]) for key, value in old.items())
            old, new = hit['old_metrics'], hit['new_metrics']
            status = 'explicit_n1_diagnostic'
            reason = hit['mechanism']
        else:
            new = old.copy()
            status = 'derived_unchanged_under_exhaustive_prior_policy'
            reason = 'not_in_the_9_n1_hits_of_the_complete_702_source_scan'
        reference.append({**ident, 'source_sha256': row['trace_sha256'], 'diagnostic_status': status,
                          'diagnostic_old_endpoint_metrics_json': canonical(old),
                          'prior_diagnostic_endpoint_metrics_json': canonical(new),
                          'metric_mapping_json': canonical({key: key for key in new}),
                          'change_reason': reason})
        public_n1.append({**ident, 'source_sha256': row['trace_sha256'], 'label_acc': row['label_acc'],
                          'evidence_acc': row['evidence_acc'], 'explicit_diagnostic_hit': bool(hit)})
    for pool in original['pool_diagnostics']:
        ident = identity(pool['sha256'], 'poolact', pool['model'], pool['regime'],
                         pool['doc_index'], pool['strategy'])
        mapping = {'label_acc': 'label_acc_mv', 'evidence_acc': 'evidence_acc_mv',
                   'verification_eff': 'verification_eff'}
        baseline = json.loads(previous[ident['slot_id']]['metrics_json'])
        assert all(close(pool['old_metrics'][key], baseline[mapping[key]])
                   for key in ('label_acc', 'evidence_acc'))
        reference.append({**ident, 'source_sha256': pool['sha256'],
                          'diagnostic_status': 'explicit_pool_diagnostic',
                          'diagnostic_old_endpoint_metrics_json': canonical(pool['old_metrics']),
                          'prior_diagnostic_endpoint_metrics_json': canonical(pool['combined_diagnostic_metrics']),
                          'metric_mapping_json': canonical(mapping),
                          'change_reason': 'prior_bold_label_subset_and_historical_task_wrapper_vote_policy'})
    assert len(reference) == len({r['slot_id'] for r in reference}) == 1170
    output.mkdir(parents=True, exist_ok=True)
    filenames = ('prior_diagnostic_reference.csv', 'prior_diagnostic_agent_hits.csv',
                 'prior_diagnostic_n1_scan_index.csv')
    for filename, table in zip(filenames, (reference, hits, public_n1)):
        table.sort(key=lambda row: (row['slot_id'], str(row.get('diagnostic_agent_index', ''))))
        write_csv(output / filename, table, list(table[0]))
    metadata = {
        'schema': 'expgym.prior-diagnostic-reference.v1',
        'original_diagnostic': {'basename': diagnostic.name, 'sha256': sha(diagnostic),
                                'bytes': diagnostic.stat().st_size, 'raw_file_public': False},
        'original_scanner': {'basename': scanner.name, 'sha256': sha(scanner)},
        'original_n1_source_index': {'basename': n1_index.name, 'sha256': sha(n1_index), 'rows': 702},
        'alignment_inputs': {name: sha(main / name) for name in
                             ('SOURCE_SELECTION.csv', 'slot_scalars.legacy.csv')},
        'policy': 'Only unique unquoted line-start bold Answer recovery; suffix unchanged; historical Audit task wrapper acceptance used for vote. This is the prior diagnostic, not the repaired general protocol.',
        'counts': {'original_hit_members': 23, 'explicit_n1_hit_members': 9,
                   'explicit_n4_hit_members': 14, 'explicit_pool_diagnostics': 468,
                   'prior_pool_answer_changes': original['summary']['combined_pool_answer_changes'],
                   'prior_pool_EA_changes': original['summary']['combined_pool_EA_changes'],
                   'prior_pool_LA_changes': original['summary']['combined_pool_LA_changes'],
                   'prior_pool_LA_or_EA_changes': original['summary']['combined_pool_either_metric_changes'],
                   'original_candidate_checks': len(original['candidate_checks']),
                   'full_n1_source_scan': 702, 'derived_unchanged_n1': 693,
                   'diagnostic_reference_slots': 1170},
        'n1_derivation': 'All 702 original source hashes exactly equal the 702 adopted Audit N1 hashes; the original exhaustive scanner modifies only its 9 listed N1 hits. Therefore LA and EA of the other 693 remain their recorded historical values under that narrow diagnostic policy. No verification_eff is invented for those 693 rows.',
        'endpoint_limit': 'Only original LA/EA/verification_eff are represented. Pool label_acc/evidence_acc map to *_mv; no diagnostic MI, HPO or Search scores are constructed.',
        'reference_files': {name: {'sha256': sha(output / name), 'rows': len(table)}
                            for name, table in zip(filenames, (reference, hits, public_n1))},
        'privacy': 'No trajectory paths, answer text, prompts, tool contents or credential values are exported.',
        'status': 'PASS', 'model_calls': 0,
    }
    (output / 'DIAGNOSTIC_REFERENCE.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    print(canonical({'status': 'PASS', 'counts': metadata['counts'], 'source_sha_unique': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--diagnostic', type=Path, required=True)
    parser.add_argument('--scanner', type=Path, required=True)
    parser.add_argument('--n1-index', type=Path, required=True)
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.diagnostic, args.scanner, args.n1_index, args.main, args.output)
