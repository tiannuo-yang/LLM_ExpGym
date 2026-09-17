#!/usr/bin/env python3
"""Verify three bounded, selected cases. No model calls, rescoring, or raw writes."""
import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
P = OUT.parent
W = Path('/lustrefs/users/chufan.shi/codex_space_tn')
INPUTS = {}


def read(path, expected=None):
    path = Path(path)
    raw = path.read_bytes()
    meta = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    assert expected is None or meta['sha256'] == expected, str(path)
    INPUTS[str(path)] = meta
    return raw


def rows(relative):
    return list(csv.DictReader(read(P / relative).decode().splitlines()))


def raw_json(path, expected=None):
    return json.loads(read(path, expected))


def source(path):
    return INPUTS[str(path)]


def obj(value):
    return json.loads(value) if isinstance(value, str) else value


def single(items):
    items = list(items)
    assert len(items) == 1, len(items)
    return items[0]


def search_case():
    inventory = rows('search/representative_case_index.csv')
    row = single(r for r in inventory if r['model'] == 'qwen3.8-2.4t-a95b-fp8'
                 and r['regime'] == 'cost_free')
    assert (row['source'], row['question_id'], row['candidate_count']) == ('phantom_seed2', '31', '19')
    metrics = rows('search/trajectory_metrics.csv')
    candidates = [r for r in metrics if r['model'] == row['model'] and r['regime'] == 'cost_free'
                  and r['termination_reason'] == 'natural_answer' and float(r['score']) < 1-1e-9]
    candidates.sort(key=lambda r: (int(r['unique_visible_articles']), r['source'], int(r['question_id'])))
    assert len(candidates) == 19 and candidates[len(candidates)//2]['trace_path'] == row['trace_path']
    trace = raw_json(row['trace_path'], row['trace_sha256'])
    events = []
    for call in trace['tool_calls']:
        article = re.search(r'^Article: ([^\n]+)', call['tool_result'])
        events.append(dict(tool_id=call['id'], request_message_id=call['request_message_id'],
                           result_message_id=call['result_message_id'],
                           query=call['arguments']['query'], article=article.group(1) if article else None,
                           visible=call['visible_to_model'], feedback_charge=call['simulated_cost_seconds']))
    assert len(events) == 16 and len({e['article'] for e in events if e['article']}) == 11
    assert len({e['query'] for e in events[:4]}) == 4
    assert {e['article'] for e in events[:4]} == {'Adella Mcbroom'}
    assert all(e['feedback_charge'] == 0 for e in events[1:4])
    assert trace['outcome']['termination_reason'] == 'natural_answer'
    assert abs(trace['outcome']['score']['value'] - 1/3) < 1e-12
    pair = single(r for r in rows('search/free_tight_paired.csv') if r['model'] == row['model']
                  and r['source'] == row['source'] and r['question_id'] == row['question_id'])
    tight_meta = single(r for r in metrics if r['trace_path'] == pair['tight_trace_path'])
    tight = raw_json(pair['tight_trace_path'], tight_meta['trace_sha256'])
    assert abs(tight['outcome']['score']['value'] - 1/3) < 1e-12
    free = [r for r in metrics if r['regime'] == 'cost_free']
    population = dict(free_trajectories=len(free), trajectories_with_repeated_articles=sum(int(r['repeat_article_deliveries']) > 0 for r in free),
                      repeated_article_deliveries=sum(int(r['repeat_article_deliveries']) for r in free),
                      repeated_articles_via_new_query=sum(int(r['repeat_article_via_new_query']) for r in free))
    assert tuple(population.values()) == (438, 183, 1160, 1144)
    return dict(id='search_action_novelty_not_observation_novelty', model=row['model'], source=row['source'], question_id=31,
                selection=dict(rule=row['selection'], candidates=len(candidates), selected_zero_based_index=len(candidates)//2,
                               preexisting_representative_index='search/representative_case_index.csv', selected_by_score_gain=False),
                source_files=[source(row['trace_path']), source(pair['tight_trace_path'])],
                question=next(m['content'].split('Question: ', 1)[1] for m in trace['messages']
                              if m.get('role') == 'user' and 'Question: ' in m.get('content', '')),
                action_sequence=events,
                free_outcome=dict(answer=trace['outcome']['answer'], f1=trace['outcome']['score']['value'],
                                  termination_reason=trace['outcome']['termination_reason'], attempts=16, unique_articles=11),
                tight_outcome=dict(answer=tight['outcome']['answer'], f1=tight['outcome']['score']['value'],
                                   termination_reason=tight['outcome']['termination_reason'], unique_articles=int(tight_meta['unique_visible_articles'])),
                population=population,
                supports='Different action strings need not yield new observations; action novelty overstates information acquisition.',
                limitations=['Same-score Free/Tight pair: not an illustration of budget-caused degradation.',
                             'Repeated articles are free of feedback charge but still consume decision steps.',
                             'A selected imperfect trajectory illustrates the mechanism, not its prevalence or a model-intrinsic defect.'])


def audit_case(gold):
    patterns = rows('audit/paired_completion_patterns.csv')
    candidates = [r for r in patterns if r['model'] == 'qwen3.8-2.4t-a95b-fp8'
                  and len(json.loads(r['gold_evidence_ids'])) == 2
                  and len(json.loads(r['free_first_partial_and_tight_final_ids'])) == 1]
    row = candidates[len(candidates)//2]
    assert len(candidates) == 53
    assert (row['doc_index'], row['order'], row['hypothesis']) == ('10', '1', 'nda-13')
    manifest = raw_json(P / 'audit/INPUTS.json')
    expected = {r['path']: r['sha256'] for r in manifest['trace_files']}
    free = raw_json(row['free_trace'], expected[row['free_trace']])
    tight = raw_json(row['tight_trace'], expected[row['tight_trace']])
    selected = [c for c in free['tool_calls'] if obj(c['arguments']).get('nda_id') == 'nda-13']
    assert [obj(c['arguments'])['evidence_ids'] for c in selected] == [[51], [47, 51]]
    assert all(c['visible_to_model'] for c in selected)
    assert selected[0]['tool_result'] == 'Evidence Incomplete | missing: Carveout set'
    assert selected[1]['tool_result'] == 'Evidence Correct'
    assert not any(obj(c['arguments']).get('nda_id') == 'nda-13' for c in tight['tool_calls'])
    outcomes = {}
    for regime, trace in [('free', free), ('tight', tight)]:
        outcomes[regime] = dict(final=obj(trace['outcome']['scoring_input'])['nda-13'],
                               termination_reason=trace['outcome']['termination_reason'])
    assert outcomes['free']['final'] == dict(label='Entailment', evidence_ids=[47, 51])
    assert outcomes['tight']['final'] == dict(label='Entailment', evidence_ids=[51])
    document = gold['documents'][10]
    assert document['annotation_sets'][0]['annotations']['nda-13'] == dict(choice='Entailment', spans=[47, 51])
    population = dict(matched_hypothesis_presentations=len(patterns), models=len({r['model'] for r in patterns}),
                      documents=len({r['doc_index'] for r in patterns}),
                      free_exact_confirmation=sum(int(r['free_exact_feedback_seen']) for r in patterns))
    assert tuple(population.values()) == (253, 6, 12, 245)
    return dict(id='audit_correct_label_incomplete_evidence', model=row['model'], doc_index=10, doc_id=document['id'], order=1,
                hypothesis_id='nda-13', hypothesis=gold['labels']['nda-13']['hypothesis'],
                selection=dict(rule='Qwen matched patterns with two gold spans and one partial span; retain frozen CSV row order, take upper middle row.',
                               candidates=53, selected_zero_based_index=26, selected_by_score_gain=False),
                source_files=[source(row['free_trace']), source(row['tight_trace'])],
                gold_evidence=[document['segments'][i] for i in [47, 51]],
                free_actions=[{k: c[k] for k in ['id', 'request_message_id', 'result_message_id', 'arguments', 'tool_result', 'visible_to_model']} for c in selected],
                tight_target_attempts=0, outcomes=outcomes, population=population,
                supports='Feedback completes the annotated evidence set behind an already-correct label.',
                limitations=['The omitted span is an enclosing exception/scope clause; the submitted subclause is relevant, not evidence-free.',
                             'Evidence completeness is exact annotated-set completeness, not a separate legal sufficiency assessment.',
                             'Independent Free/Tight generations are not a causal truncation experiment.',
                             'Case selection is from a mechanism-positive subset; population counts, not this case, establish its observed spread.'])


def query(arg):
    arg = obj(arg)
    return arg['nda_id'], tuple(sorted(set(arg['evidence_ids'])))


def pool_case(gold):
    pool_rows = rows('poolact/coordination/audit_pools.csv')
    groups = defaultdict(dict)
    for row in pool_rows:
        groups[row['model'], row['regime'], row['question_index']][row['strategy']] = row
    candidates = []
    for key, arms in groups.items():
        if key[1] != 'cost_moderate':
            continue
        n, c, p = (arms[s] for s in ['naive', 'cached', 'poolact'])
        coverage_gain = int(p['visible_hypotheses']) - max(int(n['visible_hypotheses']), int(c['visible_hypotheses']))
        if int(p['feedback_visible']) <= int(n['feedback_visible']) and coverage_gain > 0 and int(p['final_matches_peer_only_verified_nonempty']) > 0:
            candidates.append((coverage_gain, key, arms))
    candidates.sort(key=lambda x: (x[0], x[1]))
    gain, key, arms = candidates[len(candidates)//2]
    assert len(candidates) == 39 and gain == 4 and key == ('kimi-k3', 'cost_moderate', '3')
    loaded, summary = {}, []
    for strategy in ['naive', 'cached', 'poolact']:
        row = arms[strategy]
        loaded[strategy] = raw_json(row['result_path'], row['result_sha256'])
        actual = loaded[strategy]
        visible, hypotheses = 0, set()
        for agent in actual['agent_results']:
            messages = [m for m in agent['messages'] if m['role'] == 'tool' and not m.get('content', '').startswith('Protocol error:')]
            assert len(messages) == len(agent['tool_records'])
            for record, message in zip(agent['tool_records'], messages):
                if 'over-budget' not in message['content'][:180] and 'result withheld' not in message['content'][:180]:
                    visible += 1
                    hypotheses.add(query(record[1])[0])
        assert visible == int(row['feedback_visible']) and len(hypotheses) == int(row['visible_hypotheses'])
        summary.append(dict(strategy=strategy, visible_feedback=visible, covered_hypotheses=len(hypotheses),
                            evidence_accuracy_mv=actual['aggregate']['answer_metrics']['evidence_acc'], source=source(row['result_path'])))
    assert [s['visible_feedback'] for s in summary] == [40, 46, 38]
    assert [s['covered_hypotheses'] for s in summary] == [10, 12, 16]
    assert all(abs(s['evidence_accuracy_mv']-v) < 1e-12 for s, v in zip(summary, [14/17, 15/17, 1]))
    members = {a['agent_id']: a for a in loaded['poolact']['agent_results']}
    producer, consumer = members[3], members[0]
    target = ('nda-8', (21,))
    producer_record_index = single(i for i, r in enumerate(producer['tool_records']) if query(r[1]) == target and r[2] == 'Evidence Correct')
    producer_tool_messages = [m for m in producer['messages'] if m['role'] == 'tool' and not m.get('content', '').startswith('Protocol error:')]
    assert 'over-budget' not in producer_tool_messages[producer_record_index]['content'][:180]
    assert 'result withheld' not in producer_tool_messages[producer_record_index]['content'][:180]
    assert not any(query(r[1])[0] == 'nda-8' for r in consumer['tool_records'])
    shared_rows = []
    for i, message in enumerate(consumer['messages']):
        if message['role'] != 'tool':
            continue
        for line in message['content'].splitlines():
            if re.fullmatch(r'\s*nda:nda-8\s+ev:\[21\]\s+\[Evidence Correct\]\s+\[agents 3\]\s*', line):
                shared_rows.append(dict(message_index_zero_based=i, line=line.strip()))
    assert shared_rows and obj(consumer['answer'])['nda-8'] == dict(label='Entailment', evidence_ids=[21])
    document = gold['documents'][3]
    assert document['id'] == 5
    assert document['annotation_sets'][0]['annotations']['nda-8'] == dict(choice='Entailment', spans=[21])
    group_rows = rows('poolact/coordination/audit_groups.csv')
    groupmap = {(r['model'], r['regime'], r['strategy']): r for r in group_rows}
    wins = sum(float(r['mean_visible_hypotheses']) > float(groupmap[m, b, 'cached']['mean_visible_hypotheses'])
               for (m, b, s), r in groupmap.items() if s == 'poolact')
    agent_rows = rows('poolact/coordination/audit_agents.csv')
    reuse = {}
    for regime in ['cost_moderate', 'cost_tight']:
        selected = [r for r in agent_rows if r['regime'] == regime and r['strategy'] == 'poolact']
        reuse[regime] = dict(agents=len(selected), detected_peer_only_nonempty_final_match=sum(int(r['final_matches_peer_only_verified_nonempty']) > 0 for r in selected))
    assert len(pool_rows) == 468 and wins == 12
    assert [(r['agents'], r['detected_peer_only_nonempty_final_match']) for r in reuse.values()] == [(312, 253), (312, 153)]
    return dict(id='poolact_coverage_and_verified_observation_reuse', model='kimi-k3', regime='cost_moderate', question_index=3, doc_id=5,
                selection=dict(rule='Among Moderate pools: PoolAct visible feedback <= naive, coverage > both baselines, peer-only nonempty final match > 0; sort coverage margin then model/regime/string item key; take upper middle.',
                               candidates=39, selected_zero_based_index=19, selected_coverage_margin=4, selected_by_score_gain=False),
                arm_comparison=summary,
                transmission=dict(hypothesis_id='nda-8', hypothesis=gold['labels']['nda-8']['hypothesis'],
                                  gold_evidence=document['segments'][21], producer_agent_id=3,
                                  producer_tool_record_index_zero_based=producer_record_index,
                                  producer_record=producer['tool_records'][producer_record_index],
                                  consumer_agent_id=0, consumer_shared_rows=shared_rows,
                                  consumer_target_attempts=0, consumer_final=obj(consumer['answer'])['nda-8']),
                population=dict(audit_pools=len(pool_rows), model_budget_groups_with_coverage_above_cached=wins,
                                compared_model_budget_groups=12, peer_only_final_match_agents=reuse),
                limitations=['Matched three-strategy scientific item, not an isolated causal ablation of shared-graph versus other coordination components.',
                             'A final match after exposure does not prove copying; independent derivation remains possible.',
                             'Tool feedback counts are observed information, not GPU time or monetary cost.',
                             'Mechanism-positive median selection is illustrative, not a random sample or a claim that all pools improve.',
                             'question_index 3 is gold documents[3], whose document ID is 5; not documents[5].'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Check byte-identical JSON without writing.')
    args = parser.parse_args()
    gold_path = W / 'LLM_ExpGym/data/contract-nli/test_segments.json'
    gold = raw_json(gold_path, 'a81e3ecfc1d423f11289a1711ccd4d5cf3167f4d75576f5180bcc0b4c928fd23')
    cases = [search_case(), audit_case(gold), pool_case(gold)]
    payload = dict(schema='expgym.paper-cases.v1', scope='Three bounded cases from current selected sources; existing derived CSV population counts; no new inference or rescoring.',
                   selection_notice='Mechanism-positive, reproducible illustrative cases; neither random nor maximum-gain selection. Frequency statements come from full existing population summaries.',
                   raw_evidence_policy='Only task text, tool arguments/results, final submitted answers, and score fields. No private reasoning excerpts.',
                   checks='PASS: source hashes, deterministic selection, original actions, visible results, final answers, three-arm metrics, and cited CSV counts.',
                   cases=cases, inputs=list(INPUTS.values()))
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    destination = OUT / 'case_index.json'
    if args.check:
        assert destination.read_text() == rendered, 'case_index.json differs; do not overwrite during check'
    else:
        destination.write_text(rendered)
    print(json.dumps(dict(status='PASS', cases=len(cases), source_files=len(INPUTS), mode='check' if args.check else 'generate')))


if __name__ == '__main__':
    main()
