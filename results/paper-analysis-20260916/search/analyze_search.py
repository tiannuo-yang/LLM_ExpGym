#!/usr/bin/env python3
"""Read canonical selected N1 Search traces; no model calls or scoring mutations."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

W = Path('/lustrefs/users/chufan.shi/codex_space_tn')
OUT = Path(__file__).resolve().parent
INDEX = W / 'publication/five_model_report_20260911/results/six-models-lineage-20260914/SOURCE_INDEX.json'
INPUTS = {}

def read(path):
    path = Path(path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    INPUTS[str(path)] = {'path': str(path), 'bytes': len(raw), 'sha256': digest}
    return json.loads(raw)

def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def selected_paths():
    index = read(INDEX)
    result = []
    for cohort in index['cohorts']:
        cid, model = cohort['id'], cohort['model']
        if '_rerun_' in cid:
            continue  # Current material reruns replace N4 only, never N1.
        if cid == 'gemini_snapshot':
            frozen = read(cohort['full_source_index_path'])
            for item in frozen['files']:
                if item['role'] == 'receipt_bound_terminal_scalar_source' and '/traces-v2/restricted_search_' in item['path']:
                    result.append((model, cid, Path(item['path']), item['sha256']))
            continue
        for raw_root in cohort['local_raw_roots']:
            root = Path(raw_root)
            if cid in ('kimi_original', 'glm_original'):
                paths = root.glob('results/*/*/outer_*/expgym/restricted_search/*/*/single/*/traces-v2/restricted_search_*.json')
                result.extend((model, cid, path, None) for path in paths)
            else:
                queue = read(root / 'queue/definition.json')
                for job in queue['jobs']:
                    identity = job['identity']
                    selection = identity['selection']
                    if identity['runner'] == 'expgym' and selection['scenario'] == 'restricted_search':
                        paths = list(Path(job['output']).glob('result/*/traces-v2/restricted_search_*.json'))
                        assert len(paths) == 1, (job['id'], len(paths))
                        result.append((model, cid, paths[0], None))
    return sorted(result, key=lambda item: (item[0], str(item[2])))

def extract(model, cid, path, expected):
    trace = read(path)
    assert expected is None or INPUTS[str(path)]['sha256'] == expected, path
    task, outcome = trace['task'], trace['outcome']
    assert task['scenario'] == 'restricted_search'
    assert outcome['terminal_status']['execution_complete'] and outcome['terminal_status']['score_complete'], path
    tools = trace['tool_calls']
    calls = trace['llm_calls']
    assert all(tool['name'] == 'search' for tool in tools)
    visible = [tool for tool in tools if tool['visible_to_model']]
    articles = []
    seen_articles, seen_queries = set(), set()
    repeat_new_query = repeat_same_query = 0
    for tool in visible:
        result = str(tool.get('tool_result', ''))
        match = re.search(r'^Article: ([^\n]+)', result)
        if match:
            article = match.group(1).strip()
            query = str(tool.get('arguments', {}).get('query', '')).strip().lower()
            if article in seen_articles:
                if query in seen_queries:
                    repeat_same_query += 1
                else:
                    repeat_new_query += 1
            articles.append(article)
            seen_articles.add(article)
            seen_queries.add(query)
    question = next(message['content'].split('Question: ', 1)[1] for message in trace['messages']
                    if message.get('role') == 'user' and 'Question: ' in message.get('content', ''))
    family = 'whois' if question.startswith('Who ') else 'whatis'
    overhead = outcome['answer_overhead']
    limit = task['budget']['limit_seconds']
    row = {
        'model': model, 'cohort': cid, 'regime': task['budget']['regime'],
        'family': family, 'source': task['item']['source'], 'question_id': task['item']['id'],
        'score': outcome['score']['value'], 'termination_reason': outcome['termination_reason'],
        'answer_source': outcome['answer_source'], 'agent_steps': outcome.get('agent_steps'),
        'llm_calls': len(calls), 'forced_calls': sum(bool(call['forced']) for call in calls),
        'attempted_feedback': len(tools), 'visible_feedback': len(visible),
        'visible_article_calls': len(articles), 'unique_visible_articles': len(set(articles)),
        'repeat_article_deliveries': len(articles) - len(set(articles)),
        'repeat_article_via_new_query': repeat_new_query,
        'repeat_article_via_same_query': repeat_same_query,
        'paid_feedback_calls': sum(tool['simulated_cost_seconds'] > 0 for tool in tools),
        'zero_cost_calls': sum(tool['simulated_cost_seconds'] == 0 for tool in tools),
        'withheld_feedback': sum(not tool['visible_to_model'] for tool in tools),
        'withheld_charge_seconds': sum(tool['simulated_cost_seconds'] for tool in tools if not tool['visible_to_model']),
        'feedback_charge_seconds': sum(tool['simulated_cost_seconds'] for tool in tools),
        'total_cost_seconds': overhead, 'budget_seconds': limit,
        'budget_utilization': overhead / limit if limit else None,
        'protocol_failures': len(outcome.get('protocol_failures', [])),
        'trace_path': str(path), 'trace_sha256': INPUTS[str(path)]['sha256'],
    }
    return row, articles

def summary(rows, group_keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in group_keys)].append(row)
    result = []
    for keys, subset in sorted(groups.items()):
        natural = [r for r in subset if r['termination_reason'] == 'natural_answer']
        budget = [r for r in subset if r['termination_reason'] == 'time_budget_exceeded']
        cap = [r for r in subset if r['termination_reason'] in ('max_evaluations_reached', 'max_steps_reached')]
        other = [r for r in subset if r not in natural and r not in budget and r not in cap]
        row = dict(zip(group_keys, keys))
        row.update(n=len(subset), mean_score=mean(r['score'] for r in subset),
                   mean_attempted_feedback=mean(r['attempted_feedback'] for r in subset),
                   mean_visible_feedback=mean(r['visible_feedback'] for r in subset),
                   mean_unique_articles=mean(r['unique_visible_articles'] for r in subset),
                   natural_stop=len(natural), budget_forced_stop=len(budget),
                   horizon_forced_stop=len(cap), other_stop=len(other),
                   natural_stop_mean_score=mean(r['score'] for r in natural) if natural else None,
                   budget_stop_mean_score=mean(r['score'] for r in budget) if budget else None,
                   horizon_stop_mean_score=mean(r['score'] for r in cap) if cap else None,
                   natural_stop_imperfect=sum(r['score'] < 1-1e-9 for r in natural),
                   natural_stop_zero=sum(r['score'] == 0 for r in natural),
                   natural_stop_mean_utilization=mean(r['budget_utilization'] for r in natural if r['budget_utilization'] is not None)
                       if any(r['budget_utilization'] is not None for r in natural) else None,
                   total_attempted=sum(r['attempted_feedback'] for r in subset),
                   total_delivered=sum(r['visible_feedback'] for r in subset),
                   total_withheld=sum(r['withheld_feedback'] for r in subset),
                   total_article_deliveries=sum(r['visible_article_calls'] for r in subset),
                   trajectories_with_repeat_articles=sum(r['repeat_article_deliveries'] > 0 for r in subset),
                   total_repeat_article_deliveries=sum(r['repeat_article_deliveries'] for r in subset),
                   total_repeat_article_via_new_query=sum(r['repeat_article_via_new_query'] for r in subset),
                   total_repeat_article_via_same_query=sum(r['repeat_article_via_same_query'] for r in subset))
        result.append(row)
    return result

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, article_map = [], {}
    for model, cid, path, expected in selected_paths():
        row, articles = extract(model, cid, path, expected)
        key = tuple(row[k] for k in ('model', 'source', 'question_id', 'regime'))
        assert key not in article_map, key
        rows.append(row)
        article_map[key] = articles
    counts = Counter((r['model'], r['regime']) for r in rows)
    assert len(counts) == 18 and set(counts.values()) == {73}, counts
    family_counts = Counter((r['model'], r['regime'], r['family']) for r in rows)
    assert set(family_counts.values()) == {39, 34}, family_counts
    assert len(rows) == 1314
    report_path = INDEX.parent / 'main_expgym.csv'
    report_bytes = report_path.read_bytes()
    INPUTS[str(report_path)] = {'path': str(report_path), 'bytes': len(report_bytes), 'sha256': hashlib.sha256(report_bytes).hexdigest()}
    expected = {(r['model'], r['regime']): float(r['full_mean']) for r in csv.DictReader(report_bytes.decode().splitlines()) if r['scenario'] == 'restricted_search'}
    actual = {(r['model'], r['regime']): r['mean_score'] for r in summary(rows, ['model', 'regime'])}
    assert len(expected) == 18 and expected.keys() == actual.keys()
    assert all(abs(expected[key] - value) < 1e-12 for key, value in actual.items())
    assert all(r['withheld_feedback'] == int(r['termination_reason'] == 'time_budget_exceeded') for r in rows)
    assert all(r['forced_calls'] == 1 for r in rows if r['termination_reason'] == 'time_budget_exceeded')
    assert all(r['forced_calls'] == 0 for r in rows if r['termination_reason'] == 'natural_answer')
    write_csv('trajectory_metrics.csv', rows)
    write_csv('by_model_regime.csv', summary(rows, ['model', 'regime']))
    write_csv('by_family_regime.csv', summary(rows, ['family', 'regime']))
    write_csv('by_model_family_regime.csv', summary(rows, ['model', 'family', 'regime']))
    write_csv('overall_regime.csv', summary(rows, ['regime']))
    by_key = {(r['model'], r['source'], r['question_id'], r['regime']): r for r in rows}
    paired = []
    for key, free in by_key.items():
        if key[-1] != 'cost_free':
            continue
        tightkey = (*key[:-1], 'cost_tight')
        tight = by_key[tightkey]
        fa, ta = article_map[key], article_map[tightkey]
        prefix = 0
        for left, right in zip(fa, ta):
            if left != right:
                break
            prefix += 1
        paired.append({
            'model': key[0], 'source': key[1], 'question_id': key[2], 'family': free['family'],
            'free_score': free['score'], 'tight_score': tight['score'], 'score_change': tight['score'] - free['score'],
            'free_visible': free['visible_feedback'], 'tight_visible': tight['visible_feedback'],
            'free_unique_articles': free['unique_visible_articles'], 'tight_unique_articles': tight['unique_visible_articles'],
            'shared_articles': len(set(fa)&set(ta)), 'common_article_prefix': prefix,
            'same_first_article': bool(fa and ta and fa[0] == ta[0]),
            'tight_is_free_prefix': ta == fa[:len(ta)],
            'tight_term': tight['termination_reason'], 'free_term': free['termination_reason'],
            'tight_trace_path': tight['trace_path'], 'free_trace_path': free['trace_path'],
        })
    write_csv('free_tight_paired.csv', paired)
    paired_summary = []
    for model in ['ALL'] + sorted({r['model'] for r in paired}):
        selected = paired if model == 'ALL' else [r for r in paired if r['model'] == model]
        paired_summary.append({
            'model': model, 'n_pairs': len(selected),
            'tight_lower': sum(r['score_change'] < -1e-12 for r in selected),
            'tied': sum(abs(r['score_change']) <= 1e-12 for r in selected),
            'tight_higher': sum(r['score_change'] > 1e-12 for r in selected),
            'same_first_article': sum(r['same_first_article'] for r in selected),
            'tight_exact_free_prefix': sum(r['tight_is_free_prefix'] for r in selected),
        })
    write_csv('paired_direction_summary.csv', paired_summary)
    cases = []
    for model in sorted({r['model'] for r in rows}):
        for regime, term in [('cost_tight', 'time_budget_exceeded'), ('cost_free', 'natural_answer')]:
            candidates = [r for r in rows if r['model'] == model and r['regime'] == regime and r['termination_reason'] == term and r['score'] < 1]
            candidates.sort(key=lambda r: (r['unique_visible_articles'], r['source'], r['question_id']))
            selected = candidates[len(candidates) // 2]
            case = {k: selected[k] for k in ('model', 'regime', 'source', 'question_id', 'score', 'unique_visible_articles', 'attempted_feedback', 'termination_reason', 'trace_path', 'trace_sha256')}
            case['selection'] = 'upper median distinct visible articles among imperfect answers in model/regime/terminal stratum; source/qid tiebreak'
            case['candidate_count'] = len(candidates)
            cases.append(case)
    write_csv('representative_case_index.csv', cases)
    (OUT / 'INPUTS.json').write_text(json.dumps({'schema': 'paper.search_trajectory_inputs.v1', 'files': list(INPUTS.values())}, indent=2)+'\n')
    (OUT / 'CHECKS.json').write_text(json.dumps({'n_traces': len(rows), 'n_models': 6, 'n_per_model_regime': 73, 'n_paired_questions': len(paired), 'gemini_frozen_hashes_checked': True, 'frozen_main_report_18_search_means_match_tolerance': 1e-12, 'withheld_results_exactly_one_per_budget_terminal': True, 'all_budget_terminals_have_one_forced_final': True, 'all_natural_terminals_have_no_forced_final': True, 'termination_counts': dict(Counter(r['termination_reason'] for r in rows))},indent=2)+'\n')
    print(json.dumps({'n_traces': len(rows), 'n_paired': len(paired), 'summary': summary(rows, ['regime'])}, indent=2))

if __name__ == '__main__':
    main()
