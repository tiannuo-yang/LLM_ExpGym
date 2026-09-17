#!/usr/bin/env python3
"""Independent saved-scalar/aggregation checks, without importing the merger."""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CORE = ('model', 'system', 'scenario', 'regime', 'strategy')
GEM = 'gemini-3.8-flash-medium'

def rows(path):
    return list(csv.DictReader(path.open()))

def close(a, b):
    a = None if a in ('', None) else float(a)
    b = None if b in ('', None) else float(b)
    return a is b if a is None or b is None else math.isclose(a, b, abs_tol=1e-9, rel_tol=1e-11)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('report', type=Path)
    args = ap.parse_args()
    bindings = json.loads((ROOT / 'BASELINE_BINDINGS.json').read_text())
    for key, spec in bindings['inputs'].items():
        raw = Path(spec['path']).read_bytes()
        assert len(raw) == spec['bytes'] and hashlib.sha256(raw).hexdigest() == spec['sha256'], key
    old = {r['slot_id']: r for r in rows(Path(bindings['inputs']['old_scalars']['path']))}
    new = {r['slot_id']: r for r in rows(args.report / 'slot_scalars.csv')}
    slots = {r['slot_id']: r for r in rows(Path(bindings['inputs']['selected_slots']['path']))}
    assert len(old) == len(new) == len(slots) == 4698
    assert set(old) == set(new) == set(slots)
    inputs = json.loads((args.report / 'INPUTS.json').read_text())
    added = {r['slot_id'] for r in inputs['new_results']}
    assert added == {k for k,v in slots.items() if not v['trajectory_file']}
    assert len(added) == 16
    preserved = 0
    for sid, row in old.items():
        if sid not in added:
            assert all(new[sid][k] == v for k,v in row.items()), sid
            preserved += 1
    assert preserved == 4682
    oracle = json.loads(Path(bindings['inputs']['oracle']['path']).read_text())['tasks']
    scalar_checks = 0
    for source in inputs['new_results']:
        raw = Path(source['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source['sha256']
        obj = json.loads(raw)
        slot = slots[source['slot_id']]
        actual = json.loads(new[source['slot_id']]['metrics_json'])
        assert new[source['slot_id']]['provider_cohort'] == 'openrouter'
        def gap(p):
            ref = oracle[slot['item']]
            return max(0, 100 * (p - ref['mean_perf']) / (ref['best_perf'] - ref['mean_perf']))
        if slot['system'] == 'expgym':
            assert obj['run']['backend']['name'] == 'openrouter'
            assert obj['run']['model']['id'] == 'google/gemini-3.8-flash'
            p = obj['outcome']['score']['value']
            expected = dict(raw_perf=p, gap=gap(p), gap0=gap(p))
            assert obj['outcome']['terminal_status']['score_complete'] is True
        else:
            assert obj['config']['backend'] == 'openrouter'
            assert obj['config']['model'] == 'google/gemini-3.8-flash'
            ps = [a['answer_perf'] for a in obj['agent_results']]
            assert len(ps) == 4 and all(p is not None for p in ps)
            assert all(a['terminal_status']['score_complete'] is True for a in obj['agent_results'])
            assert close(mean(ps), obj['aggregate']['mean_individual_perf'])
            if slot['scenario'] == 'restricted_search':
                assert obj['aggregate']['answer_perf'] == 1.0 and ps == [1.0] * 4
                expected = dict(f1_mi=mean(ps), f1_mv=1.0)
            else:
                assert close(max(ps), obj['aggregate']['answer_perf'])
                gs = list(map(gap, ps))
                expected = dict(raw_perf_mi=mean(ps), raw_perf_bon=max(ps), gap_mi=mean(gs), gap_bon=max(gs), gap0_mi=mean(gs), gap0_bon=max(gs))
        assert set(actual) == set(expected)
        for k,v in expected.items():
            assert close(v, actual[k]), (source['slot_id'], k, v, actual[k])
            scalar_checks += 1

    groups = defaultdict(list)
    for s in new.values():
        s['metrics'] = json.loads(s['metrics_json'])
        groups[tuple(s[k] for k in CORE)].append(s)
    untouched = changed = numeric_checks = 0
    pure_new_aggregate_rows = 0
    for filename in ('absolute_settings.csv','by_repeat.csv','main_expgym.csv','main_poolact.csv'):
        orig = rows(Path(bindings['inputs'][filename]['path']))
        updated = rows(args.report / filename)
        assert len(orig) == len(updated)
        for oldrow, row in zip(orig, updated):
            selected = list(groups[tuple(row[k] for k in CORE)])
            if row['slice_kind'] == 'family':
                selected = [s for s in selected if s['family'] == row['slice']]
            elif row['slice_kind'] == 'task':
                selected = [s for s in selected if s['item'] == row['slice']]
            else:
                assert row['slice_kind'] == 'all'
            if filename == 'by_repeat.csv':
                rep = row['repeat']
                if rep.startswith('seed_'):
                    selected = [s for s in selected if int(s['seed']) == int(rep[5:])]
                elif rep.startswith('R'):
                    selected = [s for s in selected if int(s['outer_repeat']) + 1 == int(rep[1:])]
                elif int(rep) >= 2200:
                    selected = [s for s in selected if int(s['seed']) == int(rep)]
                else:
                    selected = [s for s in selected if int(s['outer_repeat']) == int(rep)]
            assert selected
            if not any(s['slot_id'] in added for s in selected):
                assert row == oldrow
                untouched += 1
            else:
                changed += 1
                assert row['model'] == GEM
                assert set(json.loads(row['source_row'])) == {s['slot_id'] for s in selected}
                only_new = all(s['slot_id'] in added for s in selected)
                pure_new_aggregate_rows += only_new
                expected_cohort = 'gemini_openrouter_missing_main_20260917' if only_new else 'gemini_snapshot+gemini_openrouter_missing_main_20260917'
                assert set(row['cohort_id'].split('+')) == set(expected_cohort.split('+')), (filename, row['slice'], row['cohort_id'], expected_cohort)
            by_item = defaultdict(list)
            for s in selected:
                by_item[s['item']].append(s['metrics'].get(row['metric']))
            if row['system'] == 'expgym' and row['scenario'] == 'evidence_audit' and row['model'] != GEM:
                assert all(len(vs) == 3 for vs in by_item.values())
                by_item = {k:[mean(vs) if all(v is not None for v in vs) else None] for k,vs in by_item.items()}
            flat = [v for vs in by_item.values() for v in vs]
            item_means = [mean(v for v in vs if v is not None) for vs in by_item.values() if any(v is not None for v in vs)]
            known_mean = mean(item_means) if item_means else None
            fields = dict(expected_units=len(flat), known_units=sum(v is not None for v in flat), missing_units=sum(v is None for v in flat), expected_items=len(by_item), complete_items=sum(all(v is not None for v in vs) for vs in by_item.values()), repeats_min=min(map(len,by_item.values())), repeats_max=max(map(len,by_item.values())), known_subset_mean=known_mean, full_mean=known_mean if all(v is not None for v in flat) else None)
            for k,v in fields.items():
                assert close(v, row[k]), (filename, k, row, v)
                numeric_checks += 1
    rankrows = rows(args.report / 'dimension_rankings.csv')
    assert len(rankrows) == 126
    rankgroups = defaultdict(list)
    for r in rankrows:
        rankgroups[(r['dimension'],r['regime'])].append(r)
    for rs in rankgroups.values():
        assert len(rs) == 6
        vals = [float(r['full_mean']) for r in rs if r['full_mean'] != '']
        for r in rs:
            value = None if not r['full_mean'] else float(r['full_mean'])
            expected = None if value is None else 1 + sum(v > value and abs(v-value) > 1e-9 for v in vals)
            assert close(expected, r['rank_among_complete'])
            assert (r['overall_winner'] == 'True') == (len(vals) == 6 and expected == 1)
    result = dict(status='PASS', report=str(args.report.resolve()), binding_hashes_verified=len(bindings['inputs']), preserved_old_slots=preserved, new_slots=len(added), new_scalar_fields=scalar_checks, aggregate_rows=untouched+changed, unchanged_aggregate_rows=untouched, changed_aggregate_rows=changed, aggregate_numeric_fields=numeric_checks, pure_openrouter_aggregate_rows=pure_new_aggregate_rows, ranking_rows=len(rankrows), boundary='Saved scores only; no independent task scorer execution, model requests, or receipt inventory audit.')
    (HERE/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
