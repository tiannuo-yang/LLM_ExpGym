"""Unchanged pure analysis functions from the frozen 297c3d0 report.

Historical parser acceptance is intentional; the driver substitutes the current
shared Audit parser for the adopted new-score pass. No local paths or API calls.
"""
import hashlib
import json
import statistics
from collections import Counter, defaultdict
SHA = lambda b: hashlib.sha256(b).hexdigest()


def parse_answer(answer):
    if not isinstance(answer, str):
        return {}
    try:
        obj = json.loads(answer)
    except (ValueError, RecursionError, OverflowError):
        clean = answer.strip().rstrip(';').strip()
        if clean.startswith('```'):
            clean = clean.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
        try:
            obj = json.loads(clean)
        except (ValueError, RecursionError, OverflowError):
            return {}
    return obj if isinstance(obj, dict) else {}


def ids(value):
    try:
        return set(int(v) for v in value)
    except Exception:
        return set()


def analyze(item, gold_docs, gold_sha):
    model, cohort, path = item
    raw = path.read_bytes()
    t = json.loads(raw)
    assert t['task']['scenario'] == 'evidence_audit'
    recorded_gold_sha = t['task']['dataset']['revision'].get('test_segments_sha256') or t['run']['evaluation_identity']['files']['evidence']['sha256']
    assert recorded_gold_sha == gold_sha
    doc_index = int(t['task']['item']['id'])
    gold = gold_docs[doc_index]['annotation_sets'][0]['annotations']
    hypotheses = t['task']['hypothesis_order']
    assert len(hypotheses) == 17 and set(hypotheses) == set(gold)
    outcome = t['outcome']
    pred = parse_answer(outcome.get('scoring_input', outcome.get('answer', '')))
    by_nda = defaultdict(list)
    tool_rows = []
    for call_i, call in enumerate(t['tool_calls']):
        if call['name'] != 'human_feedback':
            continue
        arg = call.get('arguments') or {}
        if isinstance(arg, str):
            arg = json.loads(arg)
        if isinstance(arg, list):
            arg = arg[0]
        nda = arg.get('nda_id')
        if nda not in gold:
            continue
        proposal = ids(arg.get('evidence_ids', []))
        gs = ids(gold[nda].get('spans', []))
        status = (call.get('tool_result') or call.get('observation') or '').removeprefix('Observation: ').split(' | ')[0]
        rec = {'call_i': call_i, 'nda': nda, 'proposal': proposal, 'exact': proposal == gs, 'visible': call.get('visible_to_model', True), 'status': status}
        by_nda[nda].append(rec)
        tool_rows.append(rec)
    common = dict(model=model, budget=t['task']['budget']['regime'], doc_index=doc_index, doc_id=gold_docs[doc_index]['id'], order=t['task']['rep'], source_cohort=cohort, trace_path=str(path))
    hrows = []
    for pos, nda in enumerate(hypotheses):
        ge = gold[nda]
        gs = ids(ge.get('spans', []))
        submitted = pred.get(nda)
        valid = isinstance(submitted, dict)
        submitted = submitted if valid else {}
        ps = ids(submitted.get('evidence_ids', []))
        label_ok = valid and submitted.get('label') == ge['choice']
        evidence_ok = valid and ps == gs
        attempted_calls = by_nda.get(nda, [])
        calls = [c for c in attempted_calls if c['visible']]
        row = dict(common, hypothesis=nda, position=pos, gold_label=ge['choice'], gold_nonempty=int(bool(gs)), gold_size=len(gs), submitted_size=len(ps), valid_hypothesis_submission=int(valid), label_correct=int(label_ok), evidence_exact=int(evidence_ok), joint_correct=int(label_ok and evidence_ok), label_correct_wrong_evidence=int(label_ok and not evidence_ok), missing_count=len(gs-ps), extra_count=len(ps-gs), overlap_count=len(gs & ps), missing_any=int(bool(gs-ps)), extra_any=int(bool(ps-gs)), evidence_precision=(len(gs&ps)/len(ps) if ps else (1.0 if not gs else 0.0)), evidence_recall=(len(gs&ps)/len(gs) if gs else 1.0), feedback_calls=len(attempted_calls), visible_feedback_calls=len(calls), queried=int(bool(calls)), ever_exact_proposal=int(any(c['exact'] for c in calls)), submitted_exactly_verified=int(any(c['proposal']==ps for c in calls)), first_proposal_exact=(int(calls[0]['exact']) if calls else ''), wrong_first_final_exact=int(bool(calls) and not calls[0]['exact'] and evidence_ok), exact_seen_final_wrong=int(any(c['exact'] for c in calls) and not evidence_ok), revised_after_wrong=int(bool(calls) and not calls[0]['exact'] and any(c['proposal'] != calls[0]['proposal'] for c in calls[1:])), final_changed_from_first=int(bool(calls) and ps != calls[0]['proposal']))
        row.update(gold_evidence_ids=json.dumps(sorted(gs)), submitted_evidence_ids=json.dumps(sorted(ps)), first_visible_evidence_ids=json.dumps(sorted(calls[0]['proposal'])) if calls else '', first_visible_feedback_status=calls[0]['status'] if calls else '')
        hrows.append(row)
    n = len(hrows)
    counts = Counter(c['status'] for c in tool_rows)
    total_cost = t.get('timing', {}).get('tool_simulated_cost_seconds')
    limit = t['task']['budget']['limit_seconds']
    trace = dict(common, trace_sha256=SHA(raw), trace_bytes=len(raw), hypothesis_count=n, label_acc=sum(r['label_correct'] for r in hrows)/n, evidence_acc=sum(r['evidence_exact'] for r in hrows)/n, joint_acc=sum(r['joint_correct'] for r in hrows)/n, label_correct_wrong_evidence_rate=sum(r['label_correct_wrong_evidence'] for r in hrows)/n, correct_label_wrong_evidence_conditional=(sum(r['label_correct_wrong_evidence'] for r in hrows)/sum(r['label_correct'] for r in hrows) if sum(r['label_correct'] for r in hrows) else ''), tool_calls=len(tool_rows), visible_tool_calls=sum(c['visible'] for c in tool_rows), distinct_hypotheses=len(by_nda), repeat_calls=len(tool_rows)-len(by_nda), gold_nonempty_query_calls=sum(bool(ids(gold[c['nda']].get('spans', []))) for c in tool_rows), gold_empty_query_calls=sum(not bool(ids(gold[c['nda']].get('spans', []))) for c in tool_rows), feedback_correct=counts['Evidence Correct'], feedback_incomplete=counts['Evidence Incomplete'], feedback_irrelevant=counts['Contain Irrelevant Evidences'], first_fixed_example=int(bool(tool_rows) and tool_rows[0]['nda']=='nda-11' and tool_rows[0]['proposal']=={3,7}), last_feedback_not_exact=int(bool(tool_rows) and not tool_rows[-1]['exact']), termination_reason=outcome.get('termination_reason'), answer_source=outcome.get('answer_source'), agent_steps=outcome.get('agent_steps'), simulated_feedback_cost=total_cost, budget_limit=limit, budget_fraction=(total_cost/limit if limit else ''), residual_less_than_min_call=(int(limit-total_cost < 280) if limit else ''), residual_at_least_max_call=(int(limit-total_cost >= 320) if limit else ''), zero_feedback=int(not tool_rows))
    visible_rows = [c for c in tool_rows if c['visible']]
    visible_nda = set(c['nda'] for c in visible_rows)
    trace.update(visible_distinct_hypotheses=len(visible_nda), visible_repeat_calls=len(visible_rows)-len(visible_nda), visible_feedback_correct=sum(c['status']=='Evidence Correct' for c in visible_rows), visible_feedback_incomplete=sum(c['status']=='Evidence Incomplete' for c in visible_rows), visible_feedback_irrelevant=sum(c['status']=='Contain Irrelevant Evidences' for c in visible_rows), visible_last_feedback_not_exact=int(bool(visible_rows) and not visible_rows[-1]['exact']), hidden_result_count=len(tool_rows)-len(visible_rows), natural_answer=int(outcome.get('termination_reason')=='natural_answer'), time_budget_exceeded=int(outcome.get('termination_reason')=='time_budget_exceeded'), max_steps_reached=int(outcome.get('termination_reason')=='max_steps_reached'), visible_nonempty_query_calls=sum(bool(ids(gold[c['nda']].get('spans', []))) for c in visible_rows))
    metrics = outcome['score']['metrics']
    assert abs(trace['label_acc'] - metrics['label_acc']) < 1e-10, (path, trace['label_acc'], metrics)
    assert abs(trace['evidence_acc'] - metrics['evidence_acc']) < 1e-10, (path, trace['evidence_acc'], metrics)
    for subset_name, subset in [('nonempty', [r for r in hrows if r['gold_nonempty']]), ('empty', [r for r in hrows if not r['gold_nonempty']])]:
        trace[subset_name+'_n'] = len(subset)
        for key in ['label_correct','evidence_exact','joint_correct','label_correct_wrong_evidence','missing_any','extra_any','evidence_precision','evidence_recall','queried']:
            trace[subset_name+'_'+key] = statistics.mean(r[key] for r in subset) if subset else ''
        lc = sum(r['label_correct'] for r in subset)
        trace[subset_name+'_correct_label_wrong_evidence_conditional'] = sum(r['label_correct_wrong_evidence'] for r in subset)/lc if lc else ''
    return trace, hrows


def aggregate(rows, groupkeys, metrics):
    buckets = defaultdict(list)
    for row in rows:
        buckets[tuple(row[k] for k in groupkeys)].append(row)
    out = []
    for key, group in sorted(buckets.items()):
        r = dict(zip(groupkeys, key)); r['n_rows'] = len(group)
        for name in metrics:
            vals = [x[name] for x in group if isinstance(x.get(name), (int,float))]
            r[name] = statistics.mean(vals) if vals else ''
        out.append(r)
    return out
