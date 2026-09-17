#!/usr/bin/env python3
"""Read-only, bounded N1 Audit trajectory analysis of selected six-model cohort."""
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path('/lustrefs/users/chufan.shi/codex_space_tn')
OUT = Path(__file__).resolve().parent
REPORT = ROOT / 'publication/five_model_report_20260911/results/six-models-lineage-20260914'
SOURCE = REPORT / 'SOURCE_INDEX.json'
GOLD = ROOT / 'LLM_ExpGym/data/contract-nli/test_segments.json'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def write_csv(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


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


def inventory():
    cohorts = json.loads(SOURCE.read_text())['cohorts']
    files = []
    manifest_inputs = [SOURCE, GOLD]
    for cohort in cohorts:
        cid = cohort['id']
        if cid.endswith('_original') and cid not in ('gpt_original',):
            for raw in cohort['local_raw_roots']:
                root = Path(raw)
                if cid in ('kimi_original', 'glm_original'):
                    paths = root.glob('results/*/*/outer_*/expgym/evidence_audit/*/*/single/*/traces-v2/evidence_audit*.json')
                else:
                    paths = root.glob('invocations/*/result/*/traces-v2/evidence_audit*.json')
                files.extend((cohort['model'], cid, p) for p in paths)
        elif cid in ('gpt_original', 'gemini_snapshot'):
            norm = (Path(cohort['local_raw_roots'][0]) / 'analysis_v1/normalized.jsonl') if cid == 'gpt_original' else (Path(cohort['local_analysis_root']) / 'normalized.jsonl')
            manifest_inputs.append(norm)
            for line in norm.read_text().splitlines():
                r = json.loads(line)
                if r['scenario'] == 'evidence_audit' and r['N'] == 1 and r.get('execution_complete', True):
                    p = Path(r.get('planned_result') or r.get('result_path') or r.get('result'))
                    if not p.is_absolute():
                        assert cid == 'gpt_original'
                        p = Path(cohort['local_raw_roots'][0]) / p
                    files.append((cohort['model'], cid, p))
    return sorted(files), manifest_inputs


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


def main():
    paths, manifests = inventory()
    assert len(paths) == 702, Counter(p[0] for p in paths)
    raw_gold = GOLD.read_bytes(); gold_sha = SHA(raw_gold)
    gold_docs = json.loads(raw_gold)['documents']
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda item: analyze(item, gold_docs, gold_sha), paths))
    traces = [r[0] for r in results]
    hypotheses = [h for r in results for h in r[1]]
    keyset = [(r['model'],r['budget'],r['doc_index'],r['order']) for r in traces]
    assert len(set(keyset)) == len(traces)
    assert all(n == 117 for n in Counter(r['model'] for r in traces).values())
    assert all(n == 3 for n in Counter((r['model'],r['budget'],r['doc_index']) for r in traces).values())
    metric_names = [k for k,v in traces[0].items() if isinstance(v,(int,float)) and k not in ('doc_index','doc_id','order','trace_bytes','hypothesis_count')]
    docs = aggregate(traces, ['model','budget','doc_index'], metric_names)
    models = aggregate(docs, ['model','budget'], metric_names)
    budgets = aggregate(models, ['budget'], metric_names)
    write_csv('trace_metrics.csv',traces)
    write_csv('hypothesis_metrics.csv',hypotheses)
    write_csv('document_metrics.csv',docs)
    write_csv('model_budget_metrics.csv',models)
    write_csv('budget_metrics.csv',budgets)
    # Additional count-based diagnostics have explicit denominators, not IID SEs.
    counts = []
    for budget in ['cost_free','cost_moderate','cost_tight']:
        group = [r for r in hypotheses if r['budget']==budget]
        for model in ['ALL'] + sorted(set(r['model'] for r in group)):
            sub = group if model=='ALL' else [r for r in group if r['model']==model]
            for gold_subset in ['all','nonempty','empty']:
                s = sub if gold_subset=='all' else [r for r in sub if bool(r['gold_nonempty']) == (gold_subset=='nonempty')]
                row = dict(budget=budget,model=model,gold_subset=gold_subset,n_hypothesis_presentations=len(s))
                for key in ['label_correct','evidence_exact','joint_correct','label_correct_wrong_evidence','missing_any','extra_any','queried','ever_exact_proposal','wrong_first_final_exact','exact_seen_final_wrong','revised_after_wrong']:
                    row[key]=sum(r[key] for r in s)
                row['queried_first_wrong']=sum(r['first_proposal_exact']==0 for r in s)
                row['queried_first_correct']=sum(r['first_proposal_exact']==1 for r in s)
                counts.append(row)
    write_csv('diagnostic_counts.csv',counts)
    paired = {(r['model'],r['budget'],r['doc_index'],r['order'],r['hypothesis']):r for r in hypotheses}
    patterns = []
    for free in hypotheses:
        if free['budget'] != 'cost_free' or not free['joint_correct'] or free['first_visible_feedback_status'] != 'Evidence Incomplete':
            continue
        tight = paired[(free['model'],'cost_tight',free['doc_index'],free['order'],free['hypothesis'])]
        if not tight['label_correct'] or not tight['missing_any'] or tight['extra_any'] or tight['queried']:
            continue
        if free['first_visible_evidence_ids'] != tight['submitted_evidence_ids']:
            continue
        patterns.append(dict(model=free['model'],doc_index=free['doc_index'],order=free['order'],hypothesis=free['hypothesis'],gold_evidence_ids=free['gold_evidence_ids'],free_first_partial_and_tight_final_ids=tight['submitted_evidence_ids'],free_feedback_calls=free['visible_feedback_calls'],free_exact_feedback_seen=free['ever_exact_proposal'],free_trace=free['trace_path'],tight_trace=tight['trace_path']))
    write_csv('paired_completion_patterns.csv',patterns)
    inventory_out = {'scope':'702 N1 Audit traces; six models, 13 documents, three fixed orders, three budgets; no N4 or API payload reads', 'aggregation':'hypotheses within trace; three fixed orders within document; documents within model; equal model macro average. Conditional rates are first computed per document/order, then macro averaged; diagnostic_counts exposes pooled descriptive alternatives.', 'feedback_semantics':'hypothesis-level queried/ever_exact_proposal/revised_after_wrong use only visible_to_model feedback. trace tool_calls/distinct_hypotheses/repeat_calls are executed requests; visible_* variants exclude withheld over-budget results.', 'files':[dict(path=str(p),sha256=SHA(p.read_bytes()),bytes=p.stat().st_size) for p in manifests], 'trace_files':[dict(path=t['trace_path'],sha256=t['trace_sha256'],bytes=t['trace_bytes']) for t in traces], 'checks':{'trace_count':len(traces),'hypothesis_presentations':len(hypotheses),'models':dict(Counter(r['model'] for r in traces)),'all_702_stored_label_and_evidence_scores_match':True,'gold_sha256':gold_sha,'all_traces_gold_sha_matches':True},'limitations':['Observed actions and final answers, not privileged mental-state inference.','Order presentations are not independent tasks.','Legacy fixed native example may confound acquisition target selection; first_fixed_example is retained.','Evidence exact set correctness is independent of label; exploratory joint and precision/recall do not replace stored score.','Gold-empty and nonempty evidence are reported separately.']}
    (OUT/'INPUTS.json').write_text(json.dumps(inventory_out,indent=2)+'\n')
    print(json.dumps({'checks':inventory_out['checks'],'macro_budget_metrics':budgets},indent=2))


if __name__ == '__main__':
    main()
