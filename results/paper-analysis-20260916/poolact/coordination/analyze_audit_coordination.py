#!/usr/bin/env python3
"""Read-only Audit trajectory census; never imports scoring/model code."""
import collections
import concurrent.futures
import csv
import hashlib
import json
import pathlib
import re
import subprocess

W = pathlib.Path('/lustrefs/users/chufan.shi/codex_space_tn')
R = W / 'publication/five_model_report_20260911/results/six-models-lineage-20260914'
OUT = pathlib.Path(__file__).resolve().parent


def load_json(path):
    return json.loads(path.read_text())


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidates():
    cohorts = {x['id']: x for x in load_json(R/'SOURCE_INDEX.json')['cohorts']}
    selected = {}
    for row in csv.DictReader((R/'DATA_LINEAGE.csv').open()):
        if row['system'] == 'poolact' and row['scenario'] == 'evidence_audit':
            key = (row['model'], row['regime'], row['strategy'])
            if key in selected:
                assert selected[key] == row['cohort_id']
            selected[key] = row['cohort_id']
    assert len(selected) == 36
    result = []
    for cid in sorted(set(selected.values()) - {'gemini_snapshot'}):
        for root in cohorts[cid]['local_raw_roots']:
            # rg inventory avoids reading agent companions or raw HTTP dumps.
            files = subprocess.check_output(['rg', '--files', root], text=True).splitlines()
            for name in files:
                p = pathlib.Path(name)
                if p.name != 'result.json' or p.parent.name not in {'naive', 'cached', 'poolact'}:
                    continue
                if '/portable_eval_' in name and '/poolact/evidence_audit/' not in name:
                    continue
                result.append((cid, p, None))
    for line in (W/'all_model_report_20260913/gemini_snapshot/data_v1/normalized.jsonl').open():
        row = json.loads(line)
        if row['system'] == 'poolact' and row['scenario'] == 'evidence_audit' and row['execution_complete']:
            result.append(('gemini_snapshot', pathlib.Path(row['planned_result']), row['result_sha256']))
    return selected, result


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


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    selected, files = candidates()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        values = [x for x in executor.map(lambda x: extract(x, selected), files) if x]
    values.sort(key=lambda x: (x[0]['model'], x[0]['regime'], x[0]['strategy'], x[0]['question_index']))
    rows = [x[0] for x in values]
    agents = [a for x in values for a in x[1]]
    keys = [(r['model'], r['regime'], r['strategy'], r['question_index']) for r in rows]
    assert len(set(keys)) == len(keys), 'Duplicate selected scientific pools'
    groups = collections.defaultdict(list)
    for row in rows:
        groups[(row['model'], row['regime'], row['strategy'])].append(row)
    assert len(rows) == 468 and len(groups) == 36
    assert all(len(g) == 13 for g in groups.values())
    aggregates = []
    numeric = [k for k,v in rows[0].items() if isinstance(v, (int,float)) and k not in {'question_index','bytes'}]
    for key,g in sorted(groups.items()):
        row = dict(model=key[0], regime=key[1], strategy=key[2], pools=len(g))
        row.update({f'mean_{k}':sum(x[k] for x in g)/len(g) for k in numeric})
        aggregates.append(row)
    write_csv(OUT/'audit_pools.csv', rows)
    write_csv(OUT/'audit_agents.csv', agents)
    write_csv(OUT/'audit_groups.csv', aggregates)
    manifest = dict(scope='All selected N4 Audit result.json trajectories; six-model frozen report selection',
                    pools=len(rows), agents=len(agents), groups=len(groups),
                    selection=[dict(path=str(R/n), sha256=hash_file(R/n)) for n in ['SOURCE_INDEX.json','DATA_LINEAGE.csv']],
                    sources=[{k:r[k] for k in ['model','regime','strategy','cohort_id','question_index','result_path','result_sha256','bytes']} for r in rows],
                    method='Native tool records aligned one-to-one with actual role=tool messages; withheld records excluded from visible metrics; semantic query identity uses nda_id plus set of int evidence IDs. No rescoring.',
                    limitations=['Semantic redundancy is not wasted paid cost: a cache hit is zero cost.',
                                 'Final agreement with a peer-verified observation does not prove copying or causal influence.',
                                 'Peer visibility measured from actual injected graph text, not final graph stats.',
                                 'Models and strategies are not independent repeated samples; descriptive census only.'])
    (OUT/'AUDIT_TRAJECTORY_MANIFEST.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(dict(pools=len(rows), agents=len(agents), groups=len(groups),
                          attempts=sum(r['feedback_attempts'] for r in rows),
                          visible=sum(r['feedback_visible'] for r in rows),
                          parsed_answers=sum(r['final_answer_parsed'] for r in rows))))


if __name__ == '__main__':
    main()
