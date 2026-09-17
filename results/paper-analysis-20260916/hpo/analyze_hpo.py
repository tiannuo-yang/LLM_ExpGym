#!/usr/bin/env python3
"""Read all selected N1 tuning traces; descriptive statistics, no rescoring."""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path('/lustrefs/users/chufan.shi/codex_space_tn')
REPORT = ROOT / 'publication/five_model_report_20260911/results/six-models-lineage-20260914'
OUT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def canonical(value):
    # Match numerical equivalence, e.g. integer 6 versus 6.0.
    if isinstance(value, dict):
        return tuple(sorted((k, canonical(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(canonical(v) for v in value)
    return value


def inputs():
    manifests = [REPORT / 'SOURCE_INDEX.json']
    paths = []
    for cohort in load(manifests[0])['cohorts']:
        if not cohort['id'].endswith('_original'):
            continue
        model = cohort['model']
        for raw in cohort['local_raw_roots']:
            root = Path(raw)
            if model in ('kimi-k3', 'glm-5.3'):
                # One fixed result nesting, never traverse the API dump trees.
                for path in sorted(root.glob('results/*/*/outer_*/expgym/tuning/*/*/single/*/traces-v2/*.json')):
                    paths.append((model, cohort['id'], path, None))
            else:
                definition = root / 'queue/definition.json'
                manifests.append(definition)
                for job in load(definition)['jobs']:
                    identity = job['identity']
                    if identity['runner'] != 'expgym' or identity['selection']['scenario'] != 'tuning':
                        continue
                    traces = sorted(Path(job['output']).glob('result/*/traces-v2/tuning_*.json'))
                    assert len(traces) == 1, (model, job['id'], traces)
                    paths.append((model, cohort['id'], traces[0], None))
    gem_manifest = ROOT / 'all_model_report_20260913/gemini_snapshot/data_v1/SOURCE_INDEX.json'
    manifests.append(gem_manifest)
    for item in load(gem_manifest)['files']:
        path = Path(item['path'])
        if item['role'] == 'receipt_bound_terminal_scalar_source' and '/traces-v2/tuning_' in str(path):
            paths.append(('gemini-3.8-flash-medium', 'gemini_snapshot', path, item['sha256']))
    return paths, manifests


def extract(model, cohort, path, expected):
    data = path.read_bytes()
    sha = digest(data)
    assert expected is None or sha == expected, path
    trace = json.loads(data)
    task, outcome = trace['task'], trace['outcome']
    assert task['scenario'] == 'tuning'
    assert outcome['terminal_status']['execution_complete'], path
    calls = trace['tool_calls']
    assert all(t['name'] == 'evaluate_config' for t in calls), path
    delivered = [t for t in calls if t['visible_to_model'] and isinstance(t.get('performance'), (int, float)) and math.isfinite(t['performance'])]
    unique = {canonical(t['arguments']) for t in delivered}
    perfs = [t['performance'] for t in delivered]
    best = max(perfs) if perfs else None
    first_best = perfs.index(best) + 1 if perfs else None
    record = []
    running = -float('inf')
    for idx, p in enumerate(perfs, 1):
        if p > running + 1e-12:
            record.append(idx)
            running = p
    budget = task['budget']['limit_seconds']
    visible_cost = sum(t['simulated_cost_seconds'] for t in delivered)
    final = outcome['score']['value']
    reason = outcome['termination_reason']
    reason_class = ('budget' if reason == 'time_budget_exceeded' else
                    'cap' if reason in ('max_steps_reached', 'max_evaluations_reached') else
                    'natural' if reason == 'natural_answer' else 'other')
    task_id = task['item']['id']
    row = dict(model=model, cohort=cohort, task=task_id, family=task_id.split(':')[1],
               regime=task['budget']['regime'], seed=trace['run']['seed'], rep=task['rep'],
               termination=reason, termination_class=reason_class,
               answer_source=outcome['answer_source'], score_cost_basis=outcome['score_cost_basis'],
               answer_score_source=outcome.get('answer_score_source'),
               score_status=outcome.get('score_status'), score_complete=outcome['terminal_status']['score_complete'],
               max_steps=task['limits']['max_steps'], max_evaluations=task['limits']['max_evaluations'],
               agent_steps=outcome.get('agent_steps'), attempted_evaluations=len(calls),
               delivered_evaluations=len(delivered), unique_delivered_configs=len(unique),
               repeated_delivered_evaluations=len(delivered)-len(unique),
               withheld_evaluations=sum(not t['visible_to_model'] for t in calls),
               visible_error_results=sum(t['visible_to_model'] and t not in delivered for t in calls),
               limit_seconds=budget, delivered_cost_seconds=visible_cost,
               delivered_budget_fraction=visible_cost/budget if budget else None,
               best_observed_performance=best, first_best_observation_index=first_best,
               first_best_fraction=first_best/len(delivered) if first_best else None,
               observations_after_first_best=len(delivered)-first_best if first_best else None,
               strict_record_improvements=max(0,len(record)-1),
               best_performance_gain_after_first3=(best-max(perfs[:3])) if perfs else None,
               best_performance_gain_after_first5=(best-max(perfs[:5])) if perfs else None,
               observed_best_reached_by_first3=(first_best <= 3) if first_best else None,
               observed_best_reached_by_first5=(first_best <= 5) if first_best else None,
               observed_best_reached_in_first_half=(first_best <= math.ceil(len(delivered)/2)) if first_best else None,
               final_performance=final,
               final_below_observed_best=(final < best-1e-6) if best is not None and final is not None else None,
               final_above_observed_best=(final > best+1e-6) if best is not None and final is not None else None,
               trace_path=str(path), trace_sha256=sha)
    events = [dict(model=model, task=task_id, regime=row['regime'], seed=row['seed'],
                   delivered_index=i, performance=p, is_new_record=(i in record),
                   best_so_far=max(perfs[:i])) for i,p in enumerate(perfs,1)]
    return row, events, dict(path=str(path), sha256=sha, bytes=len(data), model=model, cohort=cohort)


def summarize(rows, fields):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in fields)].append(row)
    result = []
    for key, rs in sorted(groups.items()):
        item = dict(zip(fields,key))
        item['n'] = len(rs)
        item['score_complete_n'] = sum(r['score_complete'] for r in rs)
        item['delivered_total'] = sum(r['delivered_evaluations'] for r in rs)
        item['repeated_delivered_total'] = sum(r['repeated_delivered_evaluations'] for r in rs)
        natural_budget_fractions = [r['delivered_budget_fraction'] for r in rs if r['termination_class'] == 'natural' and r['delivered_budget_fraction'] is not None]
        item['natural_stop_budget_fraction_mean'] = mean(natural_budget_fractions) if natural_budget_fractions else None
        item['natural_stop_budget_fraction_median'] = median(natural_budget_fractions) if natural_budget_fractions else None
        for reason in ('natural', 'budget', 'cap', 'other'):
            item[reason+'_n'] = sum(r['termination_class'] == reason for r in rs)
        for field in ('delivered_evaluations', 'unique_delivered_configs',
                      'repeated_delivered_evaluations', 'withheld_evaluations',
                      'delivered_budget_fraction', 'first_best_fraction',
                      'observations_after_first_best', 'strict_record_improvements',
                      'best_performance_gain_after_first3', 'best_performance_gain_after_first5'):
            vals = [r[field] for r in rs if r[field] is not None]
            item[field+'_mean'] = mean(vals) if vals else None
            item[field+'_median'] = median(vals) if vals else None
        for field in ('final_below_observed_best', 'final_above_observed_best',
                      'observed_best_reached_by_first3', 'observed_best_reached_by_first5',
                      'observed_best_reached_in_first_half'):
            vals = [r[field] for r in rs if r[field] is not None]
            item[field+'_n'] = sum(vals)
            item[field+'_denom'] = len(vals)
        item['score_source_counts'] = json.dumps(dict(sorted(Counter(r['answer_score_source'] or 'missing' for r in rs).items())))
        result.append(item)
    return result


def write_csv(name, rows):
    with (OUT/name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    paths, manifests = inputs()
    selected, events, inventory = {}, {}, {}
    for args in paths:
        row, ev, inv = extract(*args)
        key = (row['model'], row['task'], row['regime'], row['seed'], row['rep'])
        assert key not in selected, ('duplicate selected scientific slot', key)
        selected[key], events[key], inventory[key] = row, ev, inv
    rows = [selected[k] for k in sorted(selected)]
    counts = Counter(r['model'] for r in rows)
    assert sorted(counts.values()) == [75,81,81,81,81,81], counts
    assert len(rows) == 480
    write_csv('trajectories.csv', rows)
    write_csv('delivered_events.csv', [event for k in sorted(events) for event in events[k]])
    write_csv('by_model_regime.csv', summarize(rows, ('model','regime')))
    write_csv('by_family_regime.csv', summarize(rows, ('family','regime')))
    write_csv('by_regime.csv', summarize(rows, ('regime',)))
    write_csv('by_model_family_regime.csv', summarize(rows, ('model','family','regime')))
    # Compare budgets within the same task and seed; missing Gemini slots are not imputed.
    paired = defaultdict(dict)
    for r in rows:
        paired[(r['model'],r['task'],r['seed'],r['rep'])][r['regime']] = r
    pairs = []
    for key, regimes in sorted(paired.items()):
        if not all(k in regimes for k in ('cost_free','cost_tight')):
            continue
        free, tight = regimes['cost_free'], regimes['cost_tight']
        pairs.append(dict(model=key[0], task=key[1], seed=key[2], rep=key[3],
                          free_delivered=free['delivered_evaluations'], tight_delivered=tight['delivered_evaluations'],
                          free_stopping=free['termination_class'], tight_stopping=tight['termination_class'],
                          free_first_best=free['first_best_observation_index'], tight_first_best=tight['first_best_observation_index'],
                          free_final=free['final_performance'], tight_final=tight['final_performance']))
    write_csv('free_tight_pairs.csv',pairs)
    matched_rows = [r for r in rows if r['regime'] in ('cost_free','cost_tight') and all(k in paired[(r['model'],r['task'],r['seed'],r['rep'])] for k in ('cost_free','cost_tight'))]
    write_csv('matched_free_tight_by_regime.csv', summarize(matched_rows, ('regime',)))
    write_csv('matched_free_tight_by_model.csv', summarize(matched_rows, ('model','regime')))
    summary = dict(schema='paper.hpo-trajectory-analysis.v1', traces=len(rows), counts=dict(counts),
                   missing='Six unfinished Gemini N1 slots excluded, no substitution or scoring.',
                   scope='All available completed N1 tuning trajectories selected by six-model report; original cohorts only.',
                   limits='Descriptive observed trajectories, not a counterfactual replay or causal intervention. Free removes the feedback-budget constraint and cost visibility, retains 30 steps/evaluations, and still records feedback costs. Hidden over-budget performance never enters observed-quality metrics.',
                   script_sha256=digest(Path(__file__).read_bytes()),
                   input_manifests=[dict(path=str(p),sha256=digest(p.read_bytes())) for p in manifests],
                   traces_inventory=[inventory[k] for k in sorted(inventory)])
    (OUT/'INPUT_INVENTORY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'traces':len(rows),'per_model':dict(counts),'pairs':len(pairs)},indent=2))


if __name__ == '__main__':
    main()
