#!/usr/bin/env python3
"""Replay every published aggregate from a complete, versioned scalar cohort.

The immutable baseline supplies row definitions only. All 7,767 aggregate rows,
126 ranks and 1,298 comparisons are recomputed, including unchanged endpoints.
No original trace, historical report, or historical score is overwritten.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from decimal import Decimal
from pathlib import Path

TABLES = ('absolute_settings.csv', 'by_repeat.csv', 'main_expgym.csv', 'main_poolact.csv')
ARMS = ('free', 'moderate', 'tight', 'naive', 'cached', 'poolact')
PAIRS = (('moderate', 'free'), ('tight', 'free'), ('tight', 'moderate'), ('cached', 'naive'), ('poolact', 'naive'), ('poolact', 'cached'))


def rows(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, data, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fields or list(data[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(data)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + '\n')


def identity(path):
    data = path.read_bytes()
    return {'name': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def comparison_rows(template, absolute):
    result = []
    for old in template:
        row = dict(old)
        present = []
        for arm in ARMS:
            index = row[arm + '_absolute_record']
            if not index:
                continue
            original = absolute[int(index) - 1]
            for field in ('model', 'system', 'scenario', 'slice_kind', 'slice', 'metric', 'unit', 'N'):
                assert row[field] == original[field], (field, index)
            for field in ('full_mean', 'expected_units', 'known_units', 'missing_units', 'cohort_id'):
                row[arm + '_' + field] = original[field]
            present.append(original['full_mean'] != '')
        row['complete'] = str(all(present)).lower()
        for after, before in PAIRS:
            a, b = row[after + '_full_mean'], row[before + '_full_mean']
            row[after + '_minus_' + before] = str(Decimal(a) - Decimal(b)) if a and b else ''
        result.append(row)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True, help='Checkout containing the preserved Gemini public aggregation code')
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--scalars', type=Path, required=True)
    ap.add_argument('--selection', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--score-identity', required=True)
    ap.add_argument('--code-commit', required=True)
    ap.add_argument('--adoption-state', choices=('candidate', 'official'), default='candidate')
    ap.add_argument('--fairness-manifest', type=Path)
    args = ap.parse_args()
    assert not args.output.exists(), 'Use a new output directory to retain previous scoring versions'
    merger_path = args.repo / 'results/gemini-openrouter-20260917/tools/merge_main.py'
    merger = load_module(merger_path, 'preserved_aggregation')
    old = rows(args.baseline / 'slot_scalars.csv')
    new = rows(args.scalars)
    selection = rows(args.selection)
    old_ids, new_ids = [r['slot_id'] for r in old], [r['slot_id'] for r in new]
    assert len(old) == len(new) == len(set(new_ids)) == 4698
    assert set(old_ids) == set(new_ids) == {r['slot_id'] for r in selection}
    index = {r['slot_id']: r for r in new}
    new = [index[s] for s in old_ids]
    for before, after in zip(old, new):
        for key in (*merger.CORE, 'slot_id', 'item', 'outer_repeat', 'order', 'seed', 'family'):
            assert before[key] == after[key], (key, before['slot_id'])
        before['metrics'] = json.loads(before['metrics_json'])
        after['metrics'] = json.loads(after['metrics_json'])
    old_groups, new_groups = merger.group_slots(old), merger.group_slots(new)
    if args.adoption_state == 'official':
        assert args.fairness_manifest, 'Official adoption requires an explicit HPO fairness decision'
        fairness = json.loads(args.fairness_manifest.read_text())
        assert fairness.get('status') == 'PASS' and fairness.get('adoption_ready') is True
    else:
        fairness = json.loads(args.fairness_manifest.read_text()) if args.fairness_manifest else None
    args.output.mkdir(parents=True)
    historical = args.output / 'historical'
    historical.mkdir()
    changed = []
    all_comparisons = []
    outputs = {}
    checked = 0
    for filename in TABLES:
        template = rows(args.baseline / filename)
        write_csv(historical / filename, template)
        updated = []
        for record, prior in enumerate(template, 1):
            replay = merger.aggregate(prior, merger.select_rows(prior, old_groups))
            assert all(merger.same(prior[k], replay[k]) for k in merger.NUMERICAL), (filename, record)
            checked += 1
            selected = merger.select_rows(prior, new_groups)
            computed = merger.aggregate(prior, selected)
            current = dict(prior)
            current.update({k: '' if v is None else str(v) for k, v in computed.items()})
            current.update(cohort_id='+'.join(sorted({r['cohort_id'] for r in selected})),
                           source_input='slot_scalars.csv',
                           source_row=json.dumps(sorted(r['slot_id'] for r in selected)),
                           latest_selection=args.score_identity)
            if 'display_value' in current:
                current['display_value'] = merger.display(current)
                current['status'] = 'known' if current['full_mean'] != '' else 'unknown'
            updated.append(current)
            for field in merger.NUMERICAL:
                change = not merger.same(prior[field], current[field])
                item = dict(table=filename, record=record, **{k: prior[k] for k in (*merger.CORE, 'slice_kind', 'slice', 'metric')}, field=field,
                            historical=prior[field], new=current[field], changed=change,
                            delta=(float(current[field]) - float(prior[field])) if current[field] != '' and prior[field] != '' else '',
                            historical_identity='published-297c3d0-historical-scoring', new_identity=args.score_identity)
                if field == 'full_mean':
                    all_comparisons.append(item)
                if change:
                    changed.append(item)
        outputs[filename] = updated
        write_csv(args.output / filename, updated)
    assert checked == 7767
    scalar_fields = [k for k in new[0] if k != 'metrics']
    write_csv(args.output / 'slot_scalars.csv', [{k: r[k] for k in scalar_fields} for r in new], scalar_fields)
    write_csv(args.output / 'SOURCE_SELECTION.csv', selection)
    write_csv(historical / 'slot_scalars.csv', [{k: v for k, v in r.items() if k != 'metrics'} for r in old])
    write_csv(args.output / 'all_aggregate_comparisons.csv', all_comparisons)
    write_csv(args.output / 'changed_aggregate_fields.csv', changed, list(all_comparisons[0]))
    ranks = merger.ranks(outputs['absolute_settings.csv'])
    write_csv(args.output / 'dimension_rankings.csv', ranks)
    old_ranks = rows(args.baseline / 'dimension_rankings.csv')
    write_csv(historical / 'dimension_rankings.csv', old_ranks)
    rank_diffs = []
    for before, after in zip(old_ranks, ranks):
        assert all(before[k] == after[k] for k in ('dimension', 'model', 'regime', 'metric'))
        rank_diffs.append({**{k: after[k] for k in ('dimension', 'model', 'regime', 'metric')},
                           'old_score': before['full_mean'], 'new_score': after['full_mean'],
                           'old_rank': before['rank_among_complete'], 'new_rank': after['rank_among_complete'],
                           'rank_changed': str(before['rank_among_complete']) != str(after['rank_among_complete']),
                           'score_changed': not merger.same(before['full_mean'], after['full_mean'])})
    write_csv(args.output / 'ranking_changes.csv', rank_diffs)
    comparisons = comparison_rows(rows(args.baseline / 'COMPARISON.csv'), outputs['absolute_settings.csv'])
    write_csv(args.output / 'COMPARISON.csv', comparisons)
    primary = {tuple(r[k] for k in (*merger.CORE, 'metric')): r for r in outputs['absolute_settings.csv'] if r['slice_kind'] == 'all'}
    findings = merger.findings(primary, ranks)
    write_json(args.output / 'FINDINGS.json', findings)
    old_findings = json.loads((args.baseline / 'FINDINGS.json').read_text())
    write_json(historical / 'FINDINGS.json', old_findings)
    conclusions = []
    for scene in findings['n1_budget']:
        for field in ('declined', 'unchanged', 'improved'):
            a, b = old_findings['n1_budget'][scene][field], findings['n1_budget'][scene][field]
            conclusions.append(dict(conclusion=f'N1 {scene} Free-to-Tight {field} models', historical=a, new=b, changed=a != b))
    for budget in ('all', 'tight'):
        a, b = old_findings['poolact'][budget]['poolact_above_both'], findings['poolact'][budget]['poolact_above_both']
        conclusions.append(dict(conclusion=f'POOLACT {budget} above both baselines', historical=a, new=b, changed=a != b))
    for before, after in zip(old_findings['dimension_leader_changes'], findings['dimension_leader_changes']):
        for budget in merger.REGIMES:
            a, b = ';'.join(before['winners'][budget]), ';'.join(after['winners'][budget])
            conclusions.append(dict(conclusion=f'{after["dimension"]} {budget} highest mean', historical=a, new=b, changed=a != b))
    write_csv(args.output / 'conclusion_changes.csv', conclusions)
    versions = dict(historical={'identity': 'published-297c3d0-historical-scoring', 'commit': '297c3d00a006f33fc5a8ca799ce91d327d92839e', 'preserved': True},
                    diagnostic={'identity': 'review-20260918-diagnostic-only', 'adopted': False, 'scope': 'Earlier exploratory parser/vote diagnostics, not the new full-cohort rescore'},
                    new={'identity': args.score_identity, 'code_commit': args.code_commit, 'adoption_state': args.adoption_state, 'full_cohort_recomputed': True},
                    hpo_fairness=fairness,
                    known_remaining_limits=['Audit fixed native example remains unchanged.', 'Historical provider and thinking/output resource settings differ across models.', 'Historical scheduling and shared-cache availability remain observed execution conditions.', 'Audit verification_eff retains historical submitted-evidence semantics; visible-only efficiency must use a separate name.', 'Recomputed scores do not retroactively change actions or shared prompts; affected HPO runtime comparisons require the separately registered uniform-version controls.'])
    write_json(args.output / 'SCORE_VERSIONS.json', versions)
    inputs = [('new_scalars',args.scalars), ('new_selection',args.selection), ('preserved_aggregation_core',merger_path), *[('historical/'+f,args.baseline/f) for f in (*TABLES, 'slot_scalars.csv', 'dimension_rankings.csv', 'COMPARISON.csv', 'FINDINGS.json')]]
    write_json(args.output / 'INPUTS.json', {'inputs': [dict(role=role,**identity(p)) for role,p in inputs], 'score_identity': args.score_identity, 'scoring_code_commit': args.code_commit, 'analysis_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    checks = dict(status='PASS', adoption_state=args.adoption_state, slots=len(new), execution_complete=sum(merger.yes(r['execution_complete']) for r in new),
                  score_complete=sum(merger.yes(r['score_complete']) for r in new), baseline_aggregate_rows_verified=checked,
                  new_aggregate_rows_recomputed=checked, ranking_rows=len(ranks), comparison_rows=len(comparisons),
                  changed_numeric_fields=len(changed), changed_ranks=sum(r['rank_changed'] for r in rank_diffs),
                  all_scalar_slots_recomputed_source_claim='See upstream rescoring CHECKS.json; this layer independently verifies aggregation only',
                  no_model_calls=True, no_original_files_overwritten=True)
    write_json(args.output / 'CHECKS.json', checks)
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
