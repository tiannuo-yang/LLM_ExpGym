#!/usr/bin/env python3
"""Independent negative tests for collector bindings and normal missing finals.

Synthetic RuntimeChecks tests bypass the queue's disk comparison only, because
their result dictionaries intentionally differ from immutable real files. The
separate replay/ run exercises the actual end-to-end disk/receipt verifier.
"""
import copy
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=BASE.parents[1]
WORKSPACE=ROOT.parent
REPO=WORKSPACE/'LLM_ExpGym-protocol-repair-20260918'
sys.path.insert(0,str(BASE))
import collect_hpo_reruns as collector


def read(p):return list(csv.DictReader(p.open()))
def load(p):return json.loads(p.read_text())
def hash_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tests=[]


def exercise(name,func,rejected):
    error=None
    try:func()
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    tests.append(dict(name=name,expected_rejected=rejected,rejected=error is not None,
        passed=(error is not None)==rejected,error=error))


def main():
    selected={r['slot_id']:r for r in read(ROOT/'planning/hpo_versions/hpo_rerun_slots.csv')}
    old_configs=load(ROOT/'planning/hpo_versions/hpo_n4_original_configs.json')
    frozen=load(ROOT/'runtime_build/RUNTIME_SOURCE_MANIFEST.json')
    bindings=[]
    for alias in collector.EXPECTED:
        p=ROOT/'operations/queues-v2'/alias
        binding=load(p/'BINDINGS.json');plan=load(p/'queue-plan.json')
        jobs={j['job_id']:j for j in plan['jobs']}
        for b in binding['jobs']:
            j=jobs[b['new_job_id']];r=selected[b['old_slot_id']];old=old_configs[r['slot_id']]
            collector.assert_identity(b,j,r,old,frozen['source_tree_sha256'])
            bindings.append((alias,b,j,r,old))
    assert len(bindings)==97
    _,b,j,r,old=bindings[0]
    exercise('correct_frozen_binding',lambda:collector.assert_identity(b,j,r,old,frozen['source_tree_sha256']),False)
    bad=copy.deepcopy(b);bad['old_slot_id']='wrong-slot'
    exercise('wrong_binding_slot',lambda:collector.assert_identity(bad,j,r,old,frozen['source_tree_sha256']),True)
    for field,value in [('model','WRONG-MODEL'),('backend','fake'),('base_url','https://example.invalid'),('api_protocol','responses'),('temperature',0.123)]:
        mutated=copy.deepcopy(j);mutated['args'][field]=value
        exercise('job_args_identity_drift_'+field,lambda mutated=mutated:collector.assert_identity(b,mutated,r,old,frozen['source_tree_sha256']),True)
    # Validate actual completed-pool shape and source before synthetic tests.
    available=[]
    for alias,b,j,r,old in bindings:
        output=Path(b['output_dir'])/r['strategy']/'result.json'
        if output.exists() and r['strategy']=='cached':available.append((alias,b,j,r,old,output))
    assert available
    alias,b,j,r,old,path=available[0]
    original=load(path)
    os.environ.update(HPOBENCH_ROOT=str(ROOT/'runtime/data/hpo_tuning/HPOBench'),
        XDG_DATA_HOME=str(ROOT/'runtime/data/hpo_tuning/hpobench_data'),PYTHONDONTWRITEBYTECODE='1')
    checker=collector.RuntimeChecks(ROOT/'runtime',REPO,HERE)
    real_queue=checker.queue
    checker.queue=SimpleNamespace(verify_result=lambda *args:None,namespace=lambda value:value)
    def verify(result):return checker.verify(b,j,result,old,path,{})
    exercise('real_complete_pool_in_memory',lambda:verify(original),False)
    bad=copy.deepcopy(original);bad['agent_results'].pop()
    exercise('missing_member',lambda:verify(bad),True)
    bad=copy.deepcopy(original);bad['agent_results'][1]['agent_id']=0
    exercise('duplicate_member_id',lambda:verify(bad),True)
    bad=copy.deepcopy(original);bad['agent_results'][1]['seed']+=100
    exercise('wrong_member_seed',lambda:verify(bad),True)
    bad=copy.deepcopy(original);bad['agent_results'][1]['api_dump']['run_id']='another-job'
    exercise('foreign_invocation_member',lambda:verify(bad),True)
    bad=copy.deepcopy(original);bad['agent_results'][1]['api_dump']['client_id']=bad['agent_results'][0]['api_dump']['client_id']
    exercise('duplicate_member_client_identity',lambda:verify(bad),True)
    bad=copy.deepcopy(original);bad['implementation_sha256']['source_tree']='wrong-tree'
    exercise('wrong_runtime_tree',lambda:verify(bad),True)
    bad=copy.deepcopy(original);bad['config']['evaluation_identity']['files']['table']['sha256']='0'*64
    exercise('wrong_benchmark_bytes',lambda:verify(bad),True)
    bad=copy.deepcopy(original)
    assistant_messages=[m for m in bad['agent_results'][0]['messages'] if m['role']=='assistant']
    assert len(assistant_messages)>1
    assistant_messages[0]['content']='Answer: '+bad['agent_results'][0]['eval_records'][0][0]
    assistant_messages[0].pop('tool_calls',None)
    exercise('missed_earlier_accepted_final',lambda:verify(bad),True)
    def terminal_text(agent,text):
        msg=next(m for m in reversed(agent['messages']) if m['role']=='assistant')
        msg['content']=text;msg.pop('tool_calls',None)
    def refresh_aggregate(result):
        perfs=[a['answer_perf'] for a in result['agent_results']]
        finals=[a['answer'] for a in result['agent_results']]
        metrics=checker.helper.perfs_metrics(perfs,finals,result['config']['tuning_task'],checker.oracle)
        result['aggregate'].update(individual_answers=[a or '' for a in finals],individual_perfs=perfs,
            mean_individual_perf=metrics['raw_perf_mi'],answer_perf=metrics['raw_perf_bon'])
        result['terminal_status']['score_complete']=all(p is not None for p in perfs)
        return metrics
    for missing in (1,4):
        bad=copy.deepcopy(original)
        for a in bad['agent_results'][:missing]:
            terminal_text(a,'')
            a.update(answer=None,answer_perf=None,answer_score_source=None)
            a['terminal_status'].update(score_complete=False,terminal_classification='model_no_answer')
        metrics=refresh_aggregate(bad)
        assert metrics['raw_perf_mi'] is None and metrics['raw_perf_bon'] is None
        assert metrics['gap0_mi'] is not None
        if missing==4:assert metrics['gap0_mi']==metrics['gap0_bon']==0
        exercise('normal_missing_final_'+str(missing)+'_members',lambda bad=bad:verify(bad),False)
    # An actual visible, worse configuration remains admissible. This tests
    # absence of gain-based selection, not a claim that this synthetic answer
    # was ever produced by a model.
    lower=copy.deepcopy(original);changed=False
    for a in lower['agent_results']:
        records=[e for e in a['eval_records'] if e[2] is not None and a['answer_perf'] is not None and e[2]<a['answer_perf']-1e-6]
        if records:
            chosen=min(records,key=lambda e:e[2]);terminal_text(a,'Answer: '+chosen[0]);a.update(answer=chosen[0],answer_perf=chosen[2],answer_score_source='matching_tool_call');changed=True;break
    assert changed,'Choose a real fixture with a suboptimal observed configuration'
    before=original['aggregate']['mean_individual_perf'];after=refresh_aggregate(lower)['raw_perf_mi']
    assert after<before
    exercise('legitimate_lower_scoring_configuration_not_filtered',lambda:verify(lower),False)
    # Exercise real disk/receipt guards on an isolated copy, never on the run.
    plan=load(ROOT/'operations/queues-v2'/alias/'queue-plan.json')
    receipt=load(Path(plan['output_root'])/'queue/jobs'/j['job_id']/'completion.json')
    original_invocation=Path(b['output_dir']).parent
    original_inventory=collector.inventory(original_invocation)
    with tempfile.TemporaryDirectory(prefix='collector-negative-',dir=HERE) as temporary:
        cloned=Path(temporary)/'invocation'
        shutil.copytree(original_invocation,cloned)
        def check_receipt():assert receipt['artifacts']==collector.inventory(cloned)
        exercise('copied_complete_invocation_receipt_matches',check_receipt,False)
        (cloned/'result'/r['strategy']/'agents/agent_0.json').unlink()
        exercise('receipt_with_missing_member_artifact',check_receipt,True)
        args=copy.deepcopy(j['args']);args['output_dir']=str(cloned/'result')
        exercise('runtime_disk_verifier_missing_member_artifact',lambda:real_queue.verify_result(j,real_queue.namespace(args)),True)
    assert collector.inventory(original_invocation)==original_inventory
    report=dict(schema='expgym.hpo-collector-boundary-review.v1',status='PASS' if all(t['passed'] for t in tests) else 'FAIL',
        frozen_bindings_checked=97,tests=tests,passed=sum(t['passed'] for t in tests),total=len(tests),
        source_hashes={'collector':hash_file(BASE/'collect_hpo_reruns.py'),'test_script':hash_file(Path(__file__)),
            'real_fixture':hash_file(path)},
        real_fixture=str(path),synthetic_decline={'old_mi':before,'synthetic_mi':after},
        scope='No files in running invocations altered. Pure binding negatives plus synthetic in-memory RuntimeChecks negatives; queue disk/receipt comparison bypassed only for synthetic objects. Complete real disk/receipt verifier is exercised separately by collector_review/replay.')
    (HERE/'BOUNDARY_TESTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','passed','total','tests')},ensure_ascii=False,indent=2))
    assert report['status']=='PASS'


if __name__=='__main__':main()
