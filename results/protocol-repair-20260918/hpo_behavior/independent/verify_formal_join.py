#!/usr/bin/env python3
"""Independently verify formal score attachment against previously checked rows."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
B=OUT.parent
OBSERVED=B/'observed_behavior486'
FORMAL=B/'official_rescored486'
SCORING=B.parent/'rescore/hpo/agent_rows.csv'
EXPECTED_SCORING_SHA='62226233999868aad4f90f0502cbb96dd6f189649a8d5bd52eac41799c9d2b3d'
checks=Counter()
errors=[]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return list(csv.DictReader(p.open()))
def number(s):return None if s=='' else float(s)
def boolean(s):
    assert s in ('True','False'),s
    return s=='True'
def object_text(s):
    try:return isinstance(json.loads(s),dict)
    except (ValueError,TypeError):return False
def stringify(v):return '' if v is None else str(v)
def eq(a,b):
    if a==b:return True
    if a=='' or b=='':return False
    try:return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12)
    except (ValueError,TypeError):return False
def check(kind,key,field,a,b):
    checks[kind]+=1
    if not eq(a,stringify(b)):errors.append(dict(kind=kind,key=key,field=field,actual=a,expected=b))


def main():
    assert sha(SCORING)==EXPECTED_SCORING_SHA
    old={r['slot_id']:r for r in read(OBSERVED/'trajectories.csv')}
    new={r['slot_id']:r for r in read(FORMAL/'trajectories.csv')}
    independent={r['slot_id']:r for r in read(OUT/'independent_trajectories486.csv')}
    all_scores=read(SCORING)
    selected=[r for r in all_scores if r['slot_id'] in old]
    scores={r['slot_id']:r for r in selected}
    assert len(old)==len(new)==len(selected)==len(scores)==486
    assert set(old)==set(new)==set(scores)==set(independent)
    metadata=json.loads((OUT/'PUBLICATION_CHECKS.json').read_text())
    for p in metadata['source_files']:
        assert sha(OBSERVED/p['path'])==p['sha256'],p
    previous_check=json.loads((FORMAL/'CHECKS.json').read_text())
    assert previous_check['inputs']['formal_agent_rows_sha256']==sha(SCORING)
    assert previous_check['inputs']['observed_trajectories_sha256']==sha(OBSERVED/'trajectories.csv')
    assert previous_check['script_sha256']==sha(B/'attach_rescored.py')
    mutable={'answer_source','answer_score_source','score_cost_basis','score_status','score_complete',
        'final_performance','final_below_observed_best','final_above_observed_best','nonfallback_terminal_scored',
        'submitted_json_object_scored','final_json_object','fallback_scored','scoring_version'}
    comparison={r['slot_id']:r for r in read(FORMAL/'old_new_final_comparison.csv')}
    assert set(comparison)==set(old)
    score_changes=answer_changes=0
    for slot,prior in old.items():
        current=new[slot];s=scores[slot]
        assert s['system']=='expgym' and s['strategy']=='single'
        assert s['source_sha256']==prior['trace_sha256']==current['trace_sha256']==independent[slot]['trace_sha256']
        for key in ('model','regime','seed','outer_repeat'):
            check('identity',slot,key,s[key],prior[key])
        check('identity',slot,'task',s['item'],prior['task'])
        check('old_score_join',slot,'old_perf',s['old_perf'],prior['final_performance'])
        check('old_score_join',slot,'old_score_complete',s['old_score_complete'],prior['score_complete'])
        for field in set(prior)-mutable:
            check('unchanged_observed_fields',slot,field,current[field],prior[field])
        complete=boolean(s['new_score_complete']);source=s['new_answer_score_source'];actual=s['new_answer'];extracted=s['new_extracted_answer']
        nonfallback=complete and source in ('matching_tool_call','offline_final_answer')
        final=number(s['new_perf']);best=number(prior['best_observed_performance'])
        expected={'final_performance':final,'score_complete':complete,'answer_score_source':source,
            'score_cost_basis':{'matching_tool_call':'matching_tool_call','best_evaluated_fallback':'matching_tool_call',
                'offline_final_answer':'offline_final_answer','':'unscored_terminal'}[source],
            'score_status':s['new_score_status'],
            'nonfallback_terminal_scored':nonfallback,'submitted_json_object_scored':nonfallback and object_text(actual),
            'final_json_object':object_text(actual),'fallback_scored':source=='best_evaluated_fallback',
            'rescored_extracted_final_present':bool(extracted),'rescored_model_final_json_object':object_text(extracted),
            'scoring_version':'final-answer-boundary-v2/existing_trace_rescored',
            'answer_source':'best_evaluated_fallback' if source=='best_evaluated_fallback' else
                'offline_reextracted_model_answer' if prior['answer_source']=='best_evaluated_fallback' and extracted else prior['answer_source'],
            'final_below_observed_best':final<best-1e-6 if final is not None and best is not None else None,
            'final_above_observed_best':final>best+1e-6 if final is not None and best is not None else None}
        assert set(current)-set(prior)=={'rescored_extracted_final_present','rescored_model_final_json_object'}
        for field,v in expected.items():check('new_score_columns',slot,field,current[field],v)
        score_changed=not eq(prior['final_performance'],s['new_perf'])
        answer_changed=s['old_answer']!=actual
        score_changes+=score_changed;answer_changes+=answer_changed
        expected_comp={k:prior[k] for k in ('slot_id','model','task','regime','seed')}
        expected_comp.update(old_score=number(prior['final_performance']),new_score=final,
            delta=final-number(prior['final_performance']) if final is not None and prior['final_performance'] else None,
            old_score_complete=boolean(prior['score_complete']),new_score_complete=complete,
            old_answer_score_source=prior['answer_score_source'],new_answer_score_source=source,
            old_submitted_json_object_scored=boolean(prior['submitted_json_object_scored']),new_submitted_json_object_scored=expected['submitted_json_object_scored'],
            old_final_json_object=boolean(prior['final_json_object']),new_final_json_object=object_text(actual),
            old_answer=s['old_answer'],new_extracted_answer=extracted,new_scoring_answer=actual,
            score_changed=score_changed,answer_changed=answer_changed,reason=s['reason'],source_sha256=s['source_sha256'])
        assert set(comparison[slot])==set(expected_comp)
        for field,v in expected_comp.items():check('old_new_comparison',slot,field,comparison[slot][field],v)
    identical=[]
    for p in sorted(OBSERVED.glob('*.csv')):
        if p.name=='trajectories.csv':continue
        if p.read_bytes()!=(FORMAL/p.name).read_bytes():errors.append(dict(kind='observed_table_changed',file=p.name))
        else:identical.append(p.name)
    groups={'by_regime.csv':('regime',),'by_model_regime.csv':('model','regime'),
        'by_family_regime.csv':('family','regime'),'by_model_family_regime.csv':('model','family','regime'),
        'matched_free_tight_by_regime.csv':('regime',),'matched_free_tight_by_model.csv':('model','regime')}
    lookup={}
    for name,keys in groups.items():
        for r in read(OBSERVED/name):
            group=tuple((k,r[k]) for k in keys)
            for metric,value in r.items():
                if metric not in keys:lookup[(name,group,metric)]=value
    for r in read(FORMAL/'historical486_vs_formal486.csv'):
        name=r['table'];group=json.loads(r['group']);key=(name,tuple((k,group[k]) for k in groups[name]),r['metric'])
        expected=lookup.pop(key)
        check('aggregate_comparison',str(key),'old',r['old'],expected)
        check('aggregate_comparison',str(key),'new',r['new'],expected)
        check('aggregate_comparison',str(key),'changed',r['changed'],False)
        if r['delta']!='':check('aggregate_comparison',str(key),'delta',r['delta'],0)
    assert not lookup
    report=dict(status='PASS' if not errors else 'FAIL',schema='expgym.hpo-independent-formal-join.v1',
        unique_original_sources_reused=486,source_sha256_matches=486,formal_score_rows=486,
        unchanged_event_tables=['evaluation_events.csv','delivered_events.csv'],identical_nontrajectory_csvs=identical,
        old_score_complete=sum(boolean(r['score_complete']) for r in old.values()),
        new_score_complete=sum(boolean(r['score_complete']) for r in new.values()),
        score_changed=score_changes,scoring_answer_changed=answer_changes,
        checks_by_type=dict(checks),total_field_checks=sum(checks.values()),errors=errors,
        input_sha256={'agent_rows':sha(SCORING),'previous_independent_checks':sha(OUT/'PUBLICATION_CHECKS.json'),
            'observed_trajectories':sha(OBSERVED/'trajectories.csv')},
        output_sha256={p.name:sha(p) for p in sorted(FORMAL.glob('*.csv'))},
        verifier_sha256=sha(Path(__file__)),
        limitation='Verifies every join and table against prior independently checked observations and full scorer output. Does not claim independent re-execution of the scorer; original traces were read and hashed in the prior 486-trace audit.',
        final_presence_definition='model_final_present preserves historical provenance. rescored_extracted_final_present is bool(new_extracted_answer), not new_final_present which can include a legacy fallback configuration.')
    (OUT/'FORMAL_JOIN_CHECKS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','total_field_checks','old_score_complete','new_score_complete','score_changed','scoring_answer_changed','errors')},indent=2))
    assert not errors


if __name__=='__main__':main()
