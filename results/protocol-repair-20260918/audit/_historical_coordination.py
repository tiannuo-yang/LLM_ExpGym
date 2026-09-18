"""Unchanged pure analysis functions from the frozen 297c3d0 report.

Historical parser acceptance is intentional; the driver substitutes the current
shared Audit parser for the adopted new-score pass. No local paths or API calls.
"""
import collections
import hashlib
import json
import re


def parse_answer(raw):
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def canonical_query(arg):
    """Audit semantic query identity (IDs as a set), not the cache's list key."""
    original = arg
    try:
        if isinstance(arg, str):
            arg = json.loads(arg)
        ids = arg.get('evidence_ids', [])
        if not isinstance(ids, list):
            raise ValueError('Non-list evidence IDs')
        return (str(arg['nda_id']).strip(), tuple(sorted(set(map(int, ids)))))
    except (ValueError, TypeError, KeyError, AttributeError):
        return ('__invalid_payload__', (hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest(),))


def extract(item, selected):
    cid, path, expected_sha = item
    raw = path.read_bytes()
    obj = json.loads(raw)
    config = obj.get('config', {})
    key = (config.get('model'), config.get('cost_regime'), obj.get('strategy'))
    if config.get('scenario') != 'evidence_audit' or selected.get(key) != cid:
        return None
    digest = hashlib.sha256(raw).hexdigest()
    assert not expected_sha or digest == expected_sha
    members = obj['agent_results']
    assert len(members) == 4
    row = dict(model=key[0], regime=key[1], strategy=key[2], cohort_id=cid,
               question_index=config.get('question_index'), data_source=config.get('data_source'),
               result_path=str(path), result_sha256=digest, bytes=len(raw), agents=len(members))
    agent_rows = []
    all_queries, all_visible_queries, agent_unique, own_correct_sets = [], [], [], []
    outcomes = collections.Counter()
    first_hypotheses = []
    for i, agent in enumerate(members):
        aid = agent.get('agent_id', i)
        records = agent.get('tool_records', [])
        messages = [m for m in agent.get('messages', []) if m.get('role') == 'tool'
                    and not m.get('content', '').startswith('Protocol error:')]
        assert len(messages) == len(records), (str(path), aid, len(messages), len(records))
        queries, visible_queries, own_correct, peer_correct = [], [], set(), set()
        peer_snapshot_count = 0
        budget_withheld = 0
        for (tool, arg, result), message in zip(records, messages):
            assert tool == 'human_feedback', (path, tool)
            query = canonical_query(arg)
            queries.append(query)
            content = message.get('content', '')
            visible = 'over-budget' not in content[:180] and 'result withheld' not in content[:180]
            if visible:
                visible_queries.append(query)
                if result == 'Evidence Correct':
                    own_correct.add(query)
                    outcomes['correct_visible'] += 1
                elif str(result).startswith('Evidence Incomplete'):
                    outcomes['incomplete_visible'] += 1
                elif result == 'Contain Irrelevant Evidences':
                    outcomes['irrelevant_visible'] += 1
                else:
                    outcomes['other_visible'] += 1
            else:
                budget_withheld += 1
            found_peer = False
            for line in content.splitlines():
                # Only actual injected completed-observation rows, not pending claims.
                match = re.search(r'nda:(nda-[\w-]+)\s+ev:(\[[^\]]*\])\s+\[(.*?)\]\s+\[agents ([\d, ]+)\]', line)
                if not match:
                    continue
                peers = set(map(int, re.findall(r'\d+', match.group(4)))) - {aid}
                if not peers:
                    continue
                found_peer = True
                if match.group(3) == 'Evidence Correct':
                    peer_correct.add((match.group(1), tuple(sorted(set(json.loads(match.group(2)))))))
            peer_snapshot_count += int(found_peer)
        all_queries.extend(queries)
        all_visible_queries.extend(visible_queries)
        agent_unique.append(set(queries))
        own_correct_sets.append(own_correct)
        if queries:
            first_hypotheses.append(queries[0][0])
        final = parse_answer(agent.get('answer'))
        final_queries = set()
        if isinstance(final, dict):
            for nda, value in final.items():
                if isinstance(value, dict) and 'evidence_ids' in value:
                    final_queries.add(canonical_query(dict(nda_id=nda, evidence_ids=value['evidence_ids'])))
        peer_only = peer_correct - set(visible_queries)
        peer_final = peer_only & final_queries
        arow = dict(model=key[0], regime=key[1], strategy=key[2],
                    question_index=row['question_index'], agent_id=aid,
                    feedback_attempts=len(queries), feedback_visible=len(visible_queries),
                    withheld=budget_withheld, unique_query_attempts=len(set(queries)),
                    unique_visible_queries=len(set(visible_queries)),
                    hypothesis_attempts=len({q[0] for q in queries if q[0] != '__invalid_payload__'}),
                    visible_hypotheses=len({q[0] for q in visible_queries if q[0] != '__invalid_payload__'}),
                    invalid_payload_attempts=sum(q[0] == '__invalid_payload__' for q in queries),
                    own_verified_correct_queries=len(own_correct),
                    peer_snapshot_count=peer_snapshot_count,
                    peer_verified_correct_queries=len(peer_correct),
                    peer_only_verified_correct_queries=len(peer_only),
                    final_matches_peer_only_verified=len(peer_final),
                    final_matches_peer_only_verified_nonempty=sum(bool(q[1]) for q in peer_final),
                    final_answer_parsed=int(isinstance(final, dict)),
                    final_answer_hypotheses=len(final_queries),
                    evidence_acc=agent.get('answer_metrics', {}).get('evidence_acc'),
                    label_acc=agent.get('answer_metrics', {}).get('label_acc'),
                    termination_reason=agent.get('termination_reason'),
                    result_path=str(path))
        agent_rows.append(arow)
    row.update(feedback_attempts=len(all_queries), feedback_visible=len(all_visible_queries),
               unique_query_attempts=len(set(all_queries)),
               unique_visible_queries=len(set(all_visible_queries)),
               hypothesis_attempts=len({q[0] for q in all_queries if q[0] != '__invalid_payload__'}),
               visible_hypotheses=len({q[0] for q in all_visible_queries if q[0] != '__invalid_payload__'}),
               first_choice_unique_hypotheses=len(set(first_hypotheses)),
               within_agent_repeated_attempts=sum(len(a) for a in agent_unique),
               cross_agent_overlap_queries=sum(map(len, agent_unique))-len(set(all_queries)),
               unique_verified_correct_queries=len(set().union(*own_correct_sets)),
               unique_verified_correct_nonempty=sum(bool(q[1]) for q in set().union(*own_correct_sets)))
    row['within_agent_repeated_attempts'] = len(all_queries)-row['within_agent_repeated_attempts']
    row['semantic_redundancy_fraction'] = 1-len(set(all_queries))/len(all_queries) if all_queries else 0
    row.update({k: outcomes.get(k, 0) for k in ['correct_visible', 'incomplete_visible', 'irrelevant_visible', 'other_visible']})
    for field in ['withheld', 'invalid_payload_attempts', 'peer_snapshot_count', 'peer_verified_correct_queries',
                  'peer_only_verified_correct_queries', 'final_matches_peer_only_verified',
                  'final_matches_peer_only_verified_nonempty', 'final_answer_parsed']:
        row[field] = sum(a[field] for a in agent_rows)
    row['agents_with_peer_snapshot'] = sum(a['peer_snapshot_count'] > 0 for a in agent_rows)
    row['agents_with_peer_only_nonempty_final_match'] = sum(a['final_matches_peer_only_verified_nonempty'] > 0 for a in agent_rows)
    shared = obj.get('shared_state') or {}
    row['cache_hits'] = shared.get('cache', {}).get('hits', 0)
    row['cache_size'] = shared.get('cache', {}).get('size', 0)
    row['graph_pending_claims'] = shared.get('graph', {}).get('pending_claims', 0)
    return row, agent_rows
