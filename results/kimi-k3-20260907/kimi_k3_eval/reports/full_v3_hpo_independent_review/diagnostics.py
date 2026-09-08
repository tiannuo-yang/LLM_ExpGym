#!/usr/bin/env python3
"""Read manifest-selected raw HPO artifacts; no evaluator, summarizer, or API."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('/lustrefs/users/chufan.shi/codex_space_tn')
REPO = ROOT / 'LLM_ExpGym'
MANIFEST = ROOT / 'kimi_k3_eval/runs/full_v3/manifest.json'
sys.path.insert(0, str(REPO))
from expgym.react_loop import _extract_answer
from expgym.trace_v2 import materialize_message, source_tree_sha256


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parsed(value):
    try:
        result = json.loads(value)
        return result if isinstance(result, (dict, list)) else None
    except (ValueError, TypeError):
        return None


def compare(left, right):
    if left == right:
        return 'exact_same'
    left_json, right_json = parsed(left), parsed(right)
    if left_json is not None and right_json is not None and left_json == right_json:
        return 'json_equivalent_text_differs'
    return 'different'


def shape(task, answer):
    data = parsed(answer)
    if not isinstance(data, dict):
        return {'is_json_object': False}
    result = {'is_json_object': True}
    if 'nasbench101:' in task:
        variant = task.rsplit(':', 1)[-1]
        expected = {'op_node_%d' % i for i in range(5)}
        expected.update('edge_%d' % i for i in range(9 if variant == 'B' else 21))
        if variant == 'C':
            expected.add('num_edges')
        edges = [value for key, value in data.items() if key.startswith('edge_')]
        result.update(unknown_keys=sorted(set(data) - expected),
                      missing_keys=sorted(expected - set(data)),
                      edge_values_all_binary=bool(edges) and all(value in (0, 1) for value in edges),
                      distinct_edge_values=len({str(value) for value in edges}),
                      num_edges=data.get('num_edges'))
    return result


def base(job, path, kind, strategy, agent=None, rep=None):
    return {'task': job['tuning_task'], 'regime': job['cost_regime'],
            'system': job['system'], 'kind': kind, 'strategy': strategy,
            'agent_id': agent, 'rep': rep, 'path': str(path), 'sha256': sha(path)}


def last_model(messages):
    texts = [message.get('content', '') for message in messages if message.get('role') == 'assistant']
    text = texts[-1] if texts else ''
    return text, (_extract_answer(text) or text)


def main():
    manifest = read(MANIFEST)
    assert source_tree_sha256(REPO) == manifest['source_tree_sha256']
    rows, job_receipts, issues = [], [], []
    for job in manifest['jobs']:
        if job['scenario'] != 'tuning':
            continue
        status = read(job['status_path'])
        job_receipts.append({'job_id': job['id'], 'path': job['status_path'],
                             'sha256': sha(job['status_path']), 'status': status['status'],
                             'returncode': status['returncode']})
        if status['status'] != 'completed' or status['returncode'] != 0:
            issues.append('non-complete job receipt: ' + job['id'])
        for output in job['expected_outputs']:
            path = Path(output['path'])
            data = read(path)
            if job['system'] == 'expgym':
                row = base(job, path, 'expgym_trace', 'single', rep=output['rep'])
                outcome = data['outcome']
                final_id = outcome.get('answer_message_id')
                content = materialize_message(data, final_id)['content'] if final_id else ''
                model_answer = _extract_answer(content) or content
                answer = outcome.get('answer_override', model_answer)
                tools = data['tool_calls']
                row.update(score=outcome['score']['value'], score_marker_passed=outcome['validation']['passed'],
                           answer_source=outcome['answer_source'], answer=answer,
                           model_final_text=content, model_final_extracted=model_answer,
                           answer_vs_model=compare(answer, model_answer),
                           termination_reason=outcome['termination_reason'],
                           tool_calls=len(tools), zero_visible_evaluations=sum(t.get('performance') == 0 and t['visible_to_model'] for t in tools),
                           unscored_tool_calls=sum(t.get('performance') is None for t in tools),
                           tool_error_observations=[{'id': t['id'], 'text': t.get('observation', t.get('withheld_result'))}
                               for t in tools if any(marker in str(t.get('observation', t.get('withheld_result', '')))
                               for marker in ('Invalid config:', 'Invalid JSON payload:', 'Tool error:'))],
                           source_hash=data['provenance']['repository']['source_tree_sha256'])
                row['answer_shape'] = shape(job['tuning_task'], answer)
                rows.append(row)
            else:
                row = base(job, path, 'poolact_result', output['strategy'])
                aggregate = data['aggregate']
                row.update(score=aggregate['answer_perf'], answer=aggregate['answer'],
                           aggregate_method=aggregate['method'], individual_perfs=aggregate['individual_perfs'],
                           zero_agents=sum(value == 0 for value in aggregate['individual_perfs']),
                           source_hash=data['implementation_sha256']['source_tree'])
                if aggregate['answer_perf'] != max(aggregate['individual_perfs']):
                    issues.append('aggregate is not max: ' + str(path))
                rows.append(row)
                by_id = {agent['agent_id']: agent for agent in data['agent_results']}
                for agent_path in output['agent_paths']:
                    agent = read(agent_path)
                    assert agent == by_id[agent['agent_id']], agent_path
                    item = base(job, agent_path, 'poolact_agent', output['strategy'], agent=agent['agent_id'])
                    content, model_answer = last_model(agent['messages'])
                    evaluations = agent['eval_records']
                    numeric = [evaluation[2] for evaluation in evaluations if isinstance(evaluation[2], (int, float))]
                    maximum = max(numeric) if numeric else None
                    matched_evaluations = [evaluation for evaluation in evaluations
                                          if compare(agent['answer'], evaluation[0]) != 'different']
                    item.update(score=agent['answer_perf'], score_marker_passed=agent['score_check']['ok'],
                                answer_source=agent.get('answer_source'), answer_score_source=agent.get('answer_score_source'),
                                answer=agent['answer'], model_final_text=content,
                                model_final_extracted=model_answer, answer_vs_model=compare(agent['answer'], model_answer),
                                best_visible_evaluation_perf=maximum,
                                answer_matches_best_visible_evaluation=any(evaluation[2] == maximum for evaluation in matched_evaluations),
                                api_calls=agent['api_calls'], tool_calls=agent['evaluations'],
                                zero_visible_evaluations=sum(evaluation[2] == 0 for evaluation in evaluations),
                                visible_evaluation_records=len(evaluations),
                                tool_error_observations=[{'index': index, 'text': record[2]}
                                    for index, record in enumerate(agent['tool_records'])
                                    if any(marker in str(record[2]) for marker in ('Invalid config:', 'Invalid JSON payload:', 'Tool error:'))],
                                source_hash=data['implementation_sha256']['source_tree'])
                    item['answer_shape'] = shape(job['tuning_task'], agent['answer'])
                    rows.append(item)
    grouped = collections.defaultdict(list)
    for row in rows:
        if row['source_hash'] != manifest['source_tree_sha256']:
            issues.append('source differs: ' + row['path'])
        if row.get('score_marker_passed') is False:
            issues.append('score marker false: ' + row['path'])
        grouped[(row['task'], row['regime'], row['system'], row['kind'], row['strategy'])].append(row)
    groups = []
    for key, values in sorted(grouped.items()):
        group = dict(zip(('task', 'regime', 'system', 'kind', 'strategy'), key))
        group.update(count=len(values), zero_count=sum(row['score'] == 0 for row in values),
                     minimum=min(row['score'] for row in values),
                     answer_sources=dict(collections.Counter(row.get('answer_source', 'not_applicable') for row in values)),
                     answers_different_from_last_model=sum(row.get('answer_vs_model') == 'different' for row in values),
                     zero_paths=[row['path'] for row in values if row['score'] == 0])
        groups.append(group)
    totals = {}
    for kind in ('expgym_trace', 'poolact_result', 'poolact_agent'):
        selected = [row for row in rows if row['kind'] == kind]
        totals[kind] = {'count': len(selected), 'zero_count': sum(row['score'] == 0 for row in selected),
                        'answer_sources': dict(collections.Counter(str(row.get('answer_source', 'not_applicable')) for row in selected)),
                        'answer_vs_model': dict(collections.Counter(str(row.get('answer_vs_model', 'not_applicable')) for row in selected))}
    report = {'manifest_path': str(MANIFEST), 'manifest_sha256': sha(MANIFEST),
              'source_tree_sha256': manifest['source_tree_sha256'], 'review_script_sha256': sha(__file__),
              'counts': totals, 'job_receipts': job_receipts, 'issues': issues, 'groups': groups,
              'rows': rows, 'zero_records': [row for row in rows if row['score'] == 0],
              'expgym_explicit_fallback_records': [row for row in rows if row.get('answer_source') == 'best_evaluated_fallback'],
              'poolact_answer_differences': [row for row in rows if row['kind'] == 'poolact_agent' and row['answer_vs_model'] == 'different'],
              'limitations': ['No benchmark score recomputation: raw numeric outcomes and repository validation markers are inspected directly.',
                              'PoolAct answer_source is absent: answer differences are observations, not assertions that fallback occurred.',
                              'Same final model extraction cannot prove fallback did not occur.',
                              'PoolAct visible eval_records exclude withheld results; tool error strings do not classify all zero causes.',
                              'This diagnostic does not establish a causal effect of NAS101 prompt mismatch on scores.']}
    prefix = Path(__file__).with_suffix('')
    with prefix.with_suffix('.json').open('x') as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, allow_nan=False)
    fields = ('task', 'regime', 'system', 'kind', 'strategy', 'count', 'zero_count', 'minimum', 'answer_sources', 'answers_different_from_last_model', 'zero_paths')
    with prefix.with_suffix('.csv').open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for group in groups:
            writer.writerow({key: json.dumps(value) if isinstance(value, (list, dict)) else value for key, value in group.items()})
    print(json.dumps({'counts': totals, 'jobs': len(job_receipts), 'issues': issues,
                      'zero_cases': [{'task': r['task'], 'regime': r['regime'], 'kind': r['kind'], 'strategy': r['strategy'],
                                      'agent': r.get('agent_id'), 'rep': r.get('rep'), 'answer_shape': r.get('answer_shape'), 'path': r['path']}
                                     for r in report['zero_records']],
                      'explicit_fallbacks': [{'path': r['path'], 'score': r['score']} for r in report['expgym_explicit_fallback_records']],
                      'poolact_differences': [{'path': r['path'], 'score': r['score'], 'best_match': r['answer_matches_best_visible_evaluation']} for r in report['poolact_answer_differences']]}, indent=2))


if __name__ == '__main__':
    main()
