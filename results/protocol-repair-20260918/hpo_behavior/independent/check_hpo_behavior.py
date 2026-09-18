#!/usr/bin/env python3
"""Independent canonical-trace census; does not import publication analysis code."""
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[4]
REPO = ROOT / 'LLM_ExpGym-protocol-repair-20260918'
OUT = Path(__file__).resolve().parent
SOURCE = REPO / 'results/gemini-openrouter-20260917/main'
FROZEN = ROOT / 'deliveries/paper-ad03e8c-20260916'


def finite(v):
    return type(v) in (int, float) and math.isfinite(v)


def normalized(v):
    if isinstance(v, dict):
        return tuple((k, normalized(x)) for k, x in sorted(v.items()))
    if isinstance(v, list):
        return tuple(map(normalized, v))
    return v


def consume(pair):
    selected, path = pair
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == selected['result_sha256'], path
    trace = json.loads(raw)
    task, result = trace['task'], trace['outcome']
    assert task['scenario'] == 'tuning'
    assert task['item']['id'] == selected['item']
    assert task['budget']['regime'] == selected['regime']
    assert str(trace['run']['seed']) == selected['seed']
    assert result['terminal_status']['execution_complete'] is True
    attempts = trace['tool_calls']
    assert {x['name'] for x in attempts} <= {'evaluate_config'}
    delivered = [x for x in attempts if x['visible_to_model'] and finite(x['performance'])]
    vals = [x['performance'] for x in delivered]
    configs = {normalized(x['arguments']) for x in delivered}
    best = max(vals) if vals else None
    first_best = vals.index(best) + 1 if vals else None
    record_idxs = []
    current = float('-inf')
    for i, v in enumerate(vals, 1):
        if v > current + 1e-12:
            record_idxs.append(i)
            current = v
    termination = result['termination_reason']
    term_class = {'time_budget_exceeded': 'budget', 'max_steps_reached': 'cap',
                  'max_evaluations_reached': 'cap', 'natural_answer': 'natural'}.get(termination, 'other')
    limit = task['budget']['limit_seconds']
    visible_cost = sum(x['simulated_cost_seconds'] for x in delivered)
    all_cost = sum(x['simulated_cost_seconds'] for x in attempts)
    final = result['score'].get('value')
    answer = result.get('answer')
    try:
        decoded = json.loads(answer)
        answer_json_object = isinstance(decoded, dict)
    except (TypeError, ValueError):
        answer_json_object = False
    source = result.get('answer_score_source')
    row = dict(model=selected['model'], cohort=selected['cohort_id'],
        task=selected['item'], family=selected['item'].split(':')[1],
        regime=selected['regime'], seed=trace['run']['seed'], rep=task['rep'],
        termination=termination, termination_class=term_class,
        answer_source=result.get('answer_source'), score_cost_basis=result.get('score_cost_basis'),
        answer_score_source=source, score_status=result.get('score_status'),
        score_complete=result['terminal_status']['score_complete'],
        max_steps=task['limits']['max_steps'], max_evaluations=task['limits']['max_evaluations'],
        agent_steps=result.get('agent_steps'), attempted_evaluations=len(attempts),
        delivered_evaluations=len(delivered), unique_delivered_configs=len(configs),
        repeated_delivered_evaluations=len(delivered)-len(configs),
        withheld_evaluations=sum(x['visible_to_model'] is False for x in attempts),
        visible_error_results=sum(x['visible_to_model'] and not finite(x['performance']) for x in attempts),
        limit_seconds=limit, delivered_cost_seconds=visible_cost,
        delivered_budget_fraction=visible_cost / limit if limit else None,
        best_observed_performance=best, first_best_observation_index=first_best,
        first_best_fraction=first_best / len(vals) if vals else None,
        observations_after_first_best=len(vals)-first_best if vals else None,
        strict_record_improvements=max(len(record_idxs)-1, 0),
        best_performance_gain_after_first3=best-max(vals[:3]) if vals else None,
        best_performance_gain_after_first5=best-max(vals[:5]) if vals else None,
        observed_best_reached_by_first3=first_best <= 3 if vals else None,
        observed_best_reached_by_first5=first_best <= 5 if vals else None,
        observed_best_reached_in_first_half=first_best <= math.ceil(len(vals)/2) if vals else None,
        final_performance=final,
        final_below_observed_best=final < best-1e-6 if best is not None and final is not None else None,
        final_above_observed_best=final > best+1e-6 if best is not None and final is not None else None,
        trace_path=str(path), trace_sha256=digest,
        slot_id=selected['slot_id'], is_new=not bool(selected['historical_trajectory']),
        all_attempt_cost_seconds=all_cost,
        all_attempt_budget_fraction=all_cost/limit if limit else None,
        validation_passed=result.get('validation', {}).get('passed') is True,
        numeric_final_score=finite(final), answer_present=isinstance(answer,str) and bool(answer.strip()),
        answer_json_object=answer_json_object,
        legacy_best_evaluated_fallback=source == 'best_evaluated_fallback',
        offline_final_answer=source == 'offline_final_answer',
        score_zero=final == 0, source_score_complete=selected['score_complete'] == 'True',
        result_validation_method=result.get('validation', {}).get('method'))
    row.update(visible_results=sum(x['visible_to_model'] for x in attempts),
        all_attempted_cost_seconds=all_cost,
        all_visible_cost_seconds=sum(x['simulated_cost_seconds'] for x in attempts if x['visible_to_model']),
        model_final_present=result.get('answer_source') in {'natural_model_answer','forced_model_answer'} and bool(answer),
        submitted_configuration_scored=bool(row['score_complete'] and source in {'matching_tool_call','offline_final_answer'}),
        nonfallback_terminal_scored=bool(row['score_complete'] and source in {'matching_tool_call','offline_final_answer'}),
        submitted_json_object_scored=bool(row['score_complete'] and source in {'matching_tool_call','offline_final_answer'} and answer_json_object),
        final_json_object=answer_json_object,
        fallback_scored=bool(row['score_complete'] and source == 'best_evaluated_fallback'))
    assert row['score_complete'] == row['source_score_complete']
    return row


def dumpcsv(name, rows):
    with (OUT/name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def group_stats(rows):
    ans = []
    for regime in ('cost_free', 'cost_moderate', 'cost_tight'):
        rs = [r for r in rows if r['regime'] == regime]
        item = dict(regime=regime, n=len(rs))
        for field in ('attempted_evaluations', 'delivered_evaluations', 'withheld_evaluations',
                      'visible_error_results', 'repeated_delivered_evaluations'):
            item[field+'_total'] = sum(r[field] for r in rs)
            item[field+'_mean'] = mean(r[field] for r in rs)
            item[field+'_median'] = median(r[field] for r in rs)
        for field in ('delivered_budget_fraction','all_attempt_budget_fraction'):
            nums = [r[field] for r in rs if r[field] is not None]
            item[field+'_mean'] = mean(nums) if nums else None
            item[field+'_median'] = median(nums) if nums else None
        for field in ('score_complete','numeric_final_score','answer_present','answer_json_object',
                      'validation_passed','legacy_best_evaluated_fallback','offline_final_answer','score_zero'):
            item[field+'_n'] = sum(r[field] for r in rs)
        item['termination_classes'] = dict(Counter(r['termination_class'] for r in rs))
        item['termination_reasons'] = dict(Counter(r['termination'] for r in rs))
        item['score_sources'] = dict(Counter(r['answer_score_source'] for r in rs))
        ans.append(item)
    return ans


def main():
    selected = list(csv.DictReader((SOURCE/'SOURCE_SELECTION.csv').open()))
    selected = [s for s in selected if s['system']=='expgym' and s['scenario']=='tuning']
    inputs = json.loads((SOURCE/'INPUTS.json').read_text())
    new = {d['slot_id']:d for d in inputs['new_results']}
    jobs = [(s, FROZEN/s['historical_trajectory'] if s['historical_trajectory'] else Path(new[s['slot_id']]['path'])) for s in selected]
    with ThreadPoolExecutor(max_workers=12) as executor:
        rows = sorted(executor.map(consume,jobs), key=lambda r:(r['model'],r['task'],r['regime'],r['seed'],r['rep']))
    assert len(rows)==486
    assert set(Counter(r['regime'] for r in rows).values())=={162}
    assert set(Counter(r['model'] for r in rows).values())=={81}
    assert sum(r['is_new'] for r in rows)==6
    assert all(r['score_complete'] == (r['numeric_final_score'] and r['validation_passed']) for r in rows)
    previous = list(csv.DictReader((REPO/'results/paper-analysis-20260916/hpo/trajectories.csv').open()))
    lookup = {r['trace_sha256']:r for r in rows if not r['is_new']}
    diffs = []
    assert len(previous)==len(lookup)==480
    checked = 0
    for old in previous:
        actual = lookup[old['trace_sha256']]
        for field, expected in old.items():
            if field in {'trace_path','cohort'}:
                continue
            value = actual[field]
            if value is None:
                ok = expected == ''
            elif type(value) in (float,int):
                ok = math.isclose(value,float(expected),rel_tol=1e-12,abs_tol=1e-12)
            else:
                ok = str(value) == expected
            checked += 1
            if not ok:
                diffs.append(dict(slot_id=actual['slot_id'], field=field, old=expected, actual=value))
    assert not diffs, diffs[:10]
    dumpcsv('independent_trajectories486.csv',rows)
    dumpcsv('independent_added6.csv',[r for r in rows if r['is_new']])
    summary = dict(schema='expgym.hpo-behavior-independent-check.v1', status='PASS',
        canonical_traces=486, old_traces=480, new_traces=6,
        hashes_checked=486, old_fields_compared=checked, old_field_mismatches=diffs,
        counts_by_model=dict(Counter(r['model'] for r in rows)),
        old480=group_stats([r for r in rows if not r['is_new']]),new486=group_stats(rows),
        new6=group_stats([r for r in rows if r['is_new']]),
        zero_score_samples=[r for r in rows if r['score_zero']],
        scoreability_explanation='Score completeness is checked against explicit finite saved scalar and repository recompute validation for every trace. It is score availability, not a guarantee the model explicitly submitted that configuration: legacy best_evaluated_fallback is reported separately. No absent scalar is replaced by zero in this census. Scorer code explicitly treats a missing tuning configuration as unscorable.',
        budget_explanation='Delivered utilization counts only numeric feedback actually visible to the agent. Attempted utilization includes over-budget withheld cost and may exceed one. Free has no budget denominator and is null, not zero.',
        source_manifests=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (SOURCE/'SOURCE_SELECTION.csv',SOURCE/'INPUTS.json')],
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/'CHECKS.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('status','canonical_traces','old_fields_compared','new486')},indent=2))


if __name__=='__main__':
    main()
