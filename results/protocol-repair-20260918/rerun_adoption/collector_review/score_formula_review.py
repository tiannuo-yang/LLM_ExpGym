#!/usr/bin/env python3
"""Independent HPO formula/selection checks using public code and scoring inputs.

Use --repo, optional --runtime (defaults to --repo), --package and --output to
run outside the original workspace. Oracle references come from the public
package; raw traces, private benchmark tables and a Git checkout are unnecessary.
An adjacent collector source is optionally inspected for the historical None
representation fix; its absence does not prevent independent formula checks.
"""
from pathlib import Path
import argparse
import collections
import gzip
import hashlib
import importlib.util
import io
import json
import math
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2] if len(HERE.parents)>2 else HERE
WORKSPACE=ROOT.parent
ADOPTION=HERE.parent
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--repo',type=Path,default=WORKSPACE/'LLM_ExpGym-protocol-repair-20260918',
    help='Repository containing tools/rescore_hpo_protocol.py and expgym code')
cli.add_argument('--runtime',type=Path,help='Runtime code to inspect (default: --repo)')
cli.add_argument('--package',type=Path,default=ADOPTION/'progress/scoring_inputs.jsonl.gz',
    help='Public scoring_inputs.jsonl.gz snapshot')
cli.add_argument('--output',type=Path,default=HERE/'SCORE_FORMULA_REVIEW.json',
    help='Output JSON file; defaults to the adjacent review report')
args=cli.parse_args()
REPO=args.repo.resolve()
RUNTIME=(args.runtime or REPO).resolve()
sys.path.insert(0,str(RUNTIME))
from expgym.poolact import aggregate_results as core_aggregate
from expgym.missing_final import POLICY, finish_score, aggregate_terminal, terminal_publishable

HELPER=REPO/'tools/rescore_hpo_protocol.py'
spec=importlib.util.spec_from_file_location('_independent_formula_target',HELPER)
helper=importlib.util.module_from_spec(spec);sys.modules[spec.name]=helper;spec.loader.exec_module(helper)
sha=lambda b:hashlib.sha256(b).hexdigest()
def same(a,b):
    if a is None or b is None:return a is b
    return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9)

def independent_metrics(perfs,finals,reference):
    assert len(perfs)==len(finals)>0
    denom=reference['best_perf']-reference['mean_perf'];assert denom>0
    gaps=[None if p is None else max(0.,100*(p-reference['mean_perf'])/denom)for p in perfs]
    zeros=[0. if p is None and a is None else g for p,a,g in zip(perfs,finals,gaps)]
    if len(perfs)==1:return dict(raw_perf=perfs[0],gap=gaps[0],gap0=zeros[0])
    result={}
    for prefix,values in [('raw_perf',perfs),('gap',gaps),('gap0',zeros)]:
        result[prefix+'_mi']=sum(values)/len(values)if all(v is not None for v in values)else None
        result[prefix+'_bon']=max(values)if all(v is not None for v in values)else None
    return result

def terminal(answer,perf):
    result={'answer':answer,'answer_perf':perf,'answer_metrics':None,
        'missing_final_policy':POLICY,'terminal_origin':'normal_loop_return',
        'terminal_scenario':'tuning','scoring_input':answer,
        'score_status':'unscorable_missing_configuration'if answer is None else 'scored_final_answer'}
    check=({'ok':False,'reason':'unscorable_missing_configuration','score_complete':False,
            'policy_version':POLICY}if answer is None else {'ok':True})
    result['score_check']=finish_score(result,check)
    assert terminal_publishable(result)
    return result

reference={'mean_perf':.2,'best_perf':.8}
metric_cases=[]
for name,perfs,finals in [
 ('all_numeric',[.2,.4,.6,.8],['{}']*4),
 ('all_none',[None]*4,[None]*4),
 ('partial_none',[None,.4,.6,.8],[None,'{}','{}','{}']),
 ('all_true_zero',[0.]*4,['{}']*4),
 ('partial_none_and_true_zero',[None,0.,.4,.8],[None,'{}','{}','{}']),
 ('clip_before_mean',[0.,.8],['{}']*2),
 ('above_oracle_best',[.9,.8],['{}']*2),
 ('unscorable_nonempty',[None,.8],['{}','{}']),
 ('n1_none',[None],[None]),('n1_true_zero',[0.],['{}']),
 ('n1_unscorable_nonempty',[None],['{}'])]:
    expected=independent_metrics(perfs,finals,reference)
    actual=helper.perfs_metrics(perfs,finals,'test',{'test':reference})
    assert expected.keys()==actual.keys()and all(same(v,actual[k])for k,v in expected.items())
    case={'name':name,'perfs':perfs,'finals':finals,'expected':expected,'actual':actual,'passed':True}
    # A nonempty but unscorable configuration is intentionally not a valid
    # task-abstention terminal and is held by the collector rather than zeroed.
    if len(perfs)>1 and all(p is not None or a is None for p,a in zip(perfs,finals)):
        terminals=[terminal(a,p)for a,p in zip(finals,perfs)]
        aggregate=aggregate_terminal('tuning',terminals,answer_evaluator=None,original_aggregate=core_aggregate)
        assert same(aggregate['answer_perf'],actual['raw_perf_bon'])
        assert same(aggregate['mean_individual_perf'],actual['raw_perf_mi'])
        case['runtime_aggregate']=aggregate
        case['collector_literal_answers_equal']=aggregate['individual_answers']==finals
        case['collector_normalized_answers_equal']=aggregate['individual_answers']==[a or ''for a in finals]
    metric_cases.append(case)

class NoModelEvaluator:
    def __init__(self,perf):self.perf=perf;self.calls=0
    def evaluate(self,item,answer):self.calls+=1;return self.perf,'test_offline_evaluation'

def record(raw,perf):
    try:key=json.dumps(json.loads(raw),sort_keys=True,separators=(',',':'))
    except ValueError:key=None
    return [raw,key,perf,1.]
a='{"x":1}';b='{"x":2}';c='{"x":3}'
selection_cases=[]
cases=[
 ('no_final_never_fallback',None,[record(a,.8)],(None,None,None,None,'no_accepted_final_configuration'),0),
 ('matching_real_zero_beats_fallback',a,[record(a,0.),record(b,.8)],(a,0.,'matching_tool_call','r0','visible_configuration_match'),0),
 ('matching_reverse_latest',a,[record(a,.2),record(a,.7)],(a,.7,'matching_tool_call','r1','visible_configuration_match'),0),
 ('fallback_best_visible',c,[record(a,.2),record(b,.8)],(b,.8,'best_evaluated_fallback','r1','legacy_best_visible_fallback'),0),
 ('fallback_tie_first_record',c,[record(a,.8),record(b,.8)],(a,.8,'best_evaluated_fallback','r0','legacy_best_visible_fallback'),0),
 ('only_none_records_not_offline',a,[record(a,None)],(a,None,None,None,'legacy_visible_records_without_numeric_score'),0),
 ('unmatched_all_zero_fallback',c,[record(a,0.),record(b,0.)],(a,0.,'best_evaluated_fallback','r0','legacy_best_visible_fallback'),0),
 ('no_visible_evaluations_offline_zero',c,[],(c,0.,'offline_final_answer','offline_submitted_configuration','test_offline_evaluation'),1),
]
for name,answer,records,expected,expected_calls in cases:
    evaluator=NoModelEvaluator(0.)
    actual=helper.select_answer(answer,records,['r'+str(i)for i in range(len(records))],'test',evaluator)
    assert actual==expected and evaluator.calls==expected_calls
    selection_cases.append(dict(name=name,actual=actual,passed=True,evaluator_calls=evaluator.calls))

# Snapshot once: collector may publish newer progress concurrently.
package_path=args.package;raw=package_path.read_bytes()
packages=[json.loads(line)for line in gzip.decompress(raw).decode().splitlines()]
real_checks=[];member_count=0;none_count=0;zero_count=0
for pool in packages:
    perfs=[];finals=[];members=[]
    certs={}
    for member in pool['agents']:
        cert=member['benchmark_certificate']
        if cert:
            key=(cert['item'],sha(cert['answer'].encode()))
            offline=member['answer_score_source']=='offline_final_answer'
            if offline:
                assert member['reason'] in {'benchmark_evaluation','invalid_configuration_zero'}
            # The certificate replays a previously checked benchmark result;
            # preserve its original evaluation label for an offline endpoint.
            # Do not overwrite that label with a visible-match agent sharing
            # the same answer. This does not independently rerun the benchmark.
            if key not in certs or offline:
                certs[key]={**cert,'evaluation_reason':member['reason'] if offline else 'saved_certificate'}
    evaluator=helper.Evaluator(certificates=certs)
    for member in pool['agents']:
        actual=helper.select_answer(member['extracted_answer'],member['eval_records'],member['record_ids'],pool['item'],evaluator)
        expected=(member['final_answer'],member['performance'],member['answer_score_source'],member['selected_record'],member['reason'])
        assert actual==expected
        # Independent branch selection does not call helper matching/fallback.
        answer=member['extracted_answer'];records=member['eval_records']
        if answer is None: expected_perf=None;selected=None
        else:
            try:canonical=json.dumps(json.loads(answer),sort_keys=True,separators=(',',':'))
            except (ValueError,TypeError):canonical=None
            matches=[i for i,r in enumerate(records)if r[1]is not None and canonical==r[1]]
            if matches and records[matches[-1]][2]is not None:selected=matches[-1];expected_perf=records[selected][2]
            else:
                scored=[i for i,r in enumerate(records)if type(r[2])in(int,float)and math.isfinite(r[2])]
                if scored:selected=max(scored,key=lambda i:records[i][2]);expected_perf=records[selected][2]
                elif not records:selected=None;expected_perf=member['benchmark_certificate']['performance']
                else:selected=None;expected_perf=None
        assert same(expected_perf,member['performance'])
        if selected is not None:assert member['selected_record']==member['record_ids'][selected]
        perfs.append(member['performance']);finals.append(member['final_answer']);member_count+=1
        none_count+=member['performance']is None;zero_count+=member['performance']==0
        members.append({'agent_id':member['agent_id'],'performance':member['performance'],'selected_record':member['selected_record'],'passed':True})
    expected=independent_metrics(perfs,finals,pool['oracle_reference'])
    assert expected.keys()==pool['metrics'].keys()and all(same(v,pool['metrics'][k])for k,v in expected.items())
    runtime=aggregate_terminal('tuning',[terminal(a,p)for a,p in zip(finals,perfs)],answer_evaluator=None,original_aggregate=core_aggregate)
    assert same(runtime['answer_perf'],expected['raw_perf_bon'])and same(runtime['mean_individual_perf'],expected['raw_perf_mi'])
    real_checks.append(dict(slot_id=pool['slot_id'],result_sha256=pool['result_sha256'],metrics=expected,members=members,passed=True))

collector_path=ADOPTION/'collect_hpo_reruns.py'
collector=collector_path.read_text() if collector_path.is_file() else ''
problem="assert agg['individual_answers']==finals"
fixed="assert agg['individual_answers']==[v or '' for v in finals]" in collector
fixed = fixed and all(c.get('collector_normalized_answers_equal', True) for c in metric_cases)
issue={
 'code':'collector_none_answer_slot_representation_mismatch',
 'severity':'acceptance_false_rejection',
 'collector_vulnerable_exact_expression_present':problem in collector,
 'status':'FIX_VERIFIED' if fixed else ('OPEN' if collector_path.is_file() else 'NOT_CHECKED_COLLECTOR_SOURCE_UNAVAILABLE'),
 'normalized_comparison_present_and_passes_all_policy_valid_cases':fixed,
 'finding':'Runtime intentionally serializes None member answers as empty strings in aggregate.individual_answers, but collector compares directly to finals retaining None. A normal missing-final completed pool therefore fails this expression even though strict endpoints and Gap0 are correct.',
 'affected_synthetic_cases':[c['name']for c in metric_cases if c.get('collector_literal_answers_equal')is False],
 'current_completed_packages_with_missing_scores':none_count,
 'proposed_scope':'Normalize only the comparison representation to [a or "" for a in finals]; retain None in per-member final/strict score exports and existing Gap0 rule.'}
oracle={}
for pool in packages:
    reference=pool['oracle_reference']
    assert pool['item'] not in oracle or oracle[pool['item']]==reference
    oracle[pool['item']]=reference
assert all(v['best_perf']>v['mean_perf']for v in oracle.values())
source_paths=[Path(__file__),HELPER,RUNTIME/'expgym/poolact.py',RUNTIME/'expgym/missing_final.py',
    RUNTIME/'scripts/run_poolact.py',RUNTIME/'scripts/run_paper_sweep.py',RUNTIME/'expgym/react_loop.py']
if collector_path.is_file():source_paths.append(collector_path)
assert all(p.is_file() for p in source_paths),'Public code source is missing'
path=args.output
assert path.resolve() not in {p.resolve() for p in source_paths+[package_path]},'Refusing to overwrite an input'
output={'schema':'expgym.hpo-score-formula-independent-review.v1',
 'formula_status':'PASS','collector_boundary_status':'PASS_FIX_VERIFIED'if fixed else ('ISSUE_FOUND'if problem in collector else ('RECHECK_EXPRESSION_CHANGED'if collector_path.is_file()else 'NOT_CHECKED_COLLECTOR_SOURCE_UNAVAILABLE')),
 'scope':'Read-only existing package replay and synthetic local formula checks; evaluator stubs/certificates only; no model or benchmark reruns and no collector modification.',
 'summary':{'metric_cases':len(metric_cases),'selection_cases':len(selection_cases),'completed_pools':len(packages),'completed_members':member_count,'completed_missing_scores':none_count,'completed_true_zeros':zero_count,'oracle_tasks_with_positive_denominator':len(oracle)},
 'oracle_reference_scope':'Unique task references in this exact public scoring package; not an independent read of private oracle tables.',
 'formulas':{'Gap':'max(0,100*(perf-oracle.mean_perf)/(oracle.best_perf-oracle.mean_perf)); no upper clamp',
  'MI':'mean over all members; None if any member is None; Gap MI averages individually floored gaps',
  'BoN':'max over all members only when all member scores are present; otherwise None',
  'Gap0':'normal missing answer AND None performance becomes zero; nonempty unscorable answer stays None; applies to gap only, not raw performance',
  'zero':'A finite numeric zero is scored, matches visible evaluations, contributes to means and can be selected as best; it is never treated as None',
  'runtime_layer':'Runner uses missing_final.aggregate_terminal around core poolact.aggregate_results; core alone has known-subset max semantics for partial None and is not the formal endpoint'},
 'boundary_requirements':['Scoring helper assumes a nonempty pool, aligned perfs/finals lengths and finite numeric scores; collector validates four members and benchmark finiteness first.','Gap0 helper lacks terminal provenance fields, so execution-complete normal-abstention gates must precede it.','Raw API, source identity and benchmark certificate provenance are outside this formula-only replay.'],
 'issues':[issue], 'metric_cases':metric_cases,'selection_cases':selection_cases,'real_package_checks':real_checks,
 'sources':[{'path':str(p),'sha256':sha(p.read_bytes())}for p in source_paths],
 'package_snapshot':{'path':str(package_path),'sha256':sha(raw),'bytes':len(raw)}}
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'formula_status':output['formula_status'],'collector_boundary_status':output['collector_boundary_status'],'summary':output['summary'],'report_sha256':sha(path.read_bytes())},indent=2))
