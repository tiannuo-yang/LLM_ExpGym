#!/usr/bin/env python3
"""Join all 486 formal HPO N1 rescores onto observed actions; never rerun agents."""
import argparse
import csv
import json
import shutil
from pathlib import Path
import build_behavior as behavior


def boolean(v):
    if isinstance(v,bool): return v
    if v in ('True','true','1',1): return True
    if v in ('False','false','0',0,'',None): return False
    raise ValueError(v)


def number(v):
    return None if v in ('',None) else float(v)


def json_object(v):
    try:return isinstance(json.loads(v or ''),dict)
    except (ValueError,TypeError):return False


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--observed',type=Path,required=True)
    p.add_argument('--agent-rows',type=Path,required=True)
    p.add_argument('--rescore-checks',type=Path,help='Defaults to CHECKS.json beside agent rows; binds the answer parser identity')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--scoring-version',required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    upstream=json.loads((a.rescore_checks or a.agent_rows.with_name('CHECKS.json')).read_text())
    assert upstream['status']=='PASS' and upstream['n1']==486
    old=behavior.typed_csv(a.observed/'trajectories.csv')
    wanted={r['slot_id'] for r in old}
    candidates=[r for r in behavior.read_csv(a.agent_rows) if r['slot_id'] in wanted]
    assert len(candidates)==486 and len({r['slot_id'] for r in candidates})==486
    scores={r['slot_id']:r for r in candidates}
    rows=[]; changes=[]
    mutable={'answer_source','answer_score_source','score_cost_basis','score_status','score_complete',
             'final_performance','final_below_observed_best','final_above_observed_best',
             'nonfallback_terminal_scored','submitted_json_object_scored','final_json_object','fallback_scored','scoring_version'}
    action_checks=0
    for prior in old:
        r=dict(prior);s=scores[r['slot_id']]
        assert s['source_sha256']==prior['trace_sha256'],r['slot_id']
        assert behavior.same_value(s['old_perf'],prior['final_performance']),(r['slot_id'],'old perf')
        assert boolean(s['old_score_complete'])==prior['score_complete']
        final=number(s['new_perf']);complete=boolean(s['new_score_complete'])
        source=s['new_answer_score_source'] or None
        actual=s['new_answer'];extracted=s['new_extracted_answer']
        nonfallback=complete and source in ('matching_tool_call','offline_final_answer')
        is_json=json_object(actual)
        cost_basis=('matching_tool_call' if source in ('matching_tool_call','best_evaluated_fallback') else
                    'offline_final_answer' if source=='offline_final_answer' else 'unscored_terminal')
        r.update(final_performance=final,score_complete=complete,answer_score_source=source,
                 score_cost_basis=cost_basis,score_status=s.get('new_score_status') or ('scored_final_answer' if complete else 'unscorable_missing_configuration'),
                 nonfallback_terminal_scored=nonfallback,
                 submitted_json_object_scored=nonfallback and is_json,final_json_object=is_json,
                 fallback_scored=source=='best_evaluated_fallback',scoring_version=a.scoring_version)
        r['rescored_extracted_final_present']=bool(extracted)
        r['rescored_model_final_json_object']=json_object(extracted)
        if r['fallback_scored']:r['answer_source']='best_evaluated_fallback'
        elif prior['answer_source']=='best_evaluated_fallback' and extracted:r['answer_source']='offline_reextracted_model_answer'
        best=r['best_observed_performance']
        r['final_below_observed_best']=(final<best-1e-6) if final is not None and best is not None else None
        r['final_above_observed_best']=(final>best+1e-6) if final is not None and best is not None else None
        for field in set(prior)-mutable:
            assert r[field]==prior[field],(r['slot_id'],field)
            action_checks+=1
        rows.append(r)
        changes.append(dict(slot_id=r['slot_id'],model=r['model'],task=r['task'],regime=r['regime'],seed=r['seed'],
            old_score=prior['final_performance'],new_score=final,
            delta=final-prior['final_performance'] if final is not None and prior['final_performance'] is not None else None,
            old_score_complete=prior['score_complete'],new_score_complete=complete,
            old_answer_score_source=prior['answer_score_source'],new_answer_score_source=source,
            old_submitted_json_object_scored=prior['submitted_json_object_scored'],new_submitted_json_object_scored=r['submitted_json_object_scored'],
            old_final_json_object=prior['final_json_object'],new_final_json_object=is_json,
            old_answer=s['old_answer'],new_extracted_answer=extracted,new_scoring_answer=actual,
            score_changed=not behavior.same_value(prior['final_performance'],final),
            answer_changed=s['old_answer']!=actual,reason=s.get('reason',''),source_sha256=r['trace_sha256']))
    behavior.write_csv(a.output/'trajectories.csv',rows)
    for filename in ('evaluation_events.csv','delivered_events.csv'):
        shutil.copyfile(a.observed/filename,a.output/filename)
    tables=behavior.build_tables(rows);tables['termination_reasons.csv']=behavior.termination_table(rows)
    for name,rs in tables.items():behavior.write_csv(a.output/name,rs)
    behavior.write_csv(a.output/'old_new_final_comparison.csv',changes)
    old_tables=behavior.build_tables(old);diff=[]
    groups=list(behavior.GROUPS.items())+[
        ('matched_free_tight_by_regime.csv',('regime',)),('matched_free_tight_by_model.csv',('model','regime'))]
    for name,keys in groups:
        diff.extend(behavior.compare_tables(old_tables[name],tables[name],keys,name))
    behavior.write_csv(a.output/'historical486_vs_formal486.csv',diff)
    behavior.write_json(a.output/'CHECKS.json',dict(status='PASS',schema='expgym.hpo-formal-score-behavior-join.v1',
        scoring_version=a.scoring_version,traces=len(rows),matched_source_sha256=486,all_n1_rescored=True,
        answer_parser_sha256=upstream['parser_sha256'],rescore_baseline_commit=upstream['baseline_commit'],
        unchanged_observed_action_fields=action_checks,score_changed=sum(r['score_changed'] for r in changes),
        scoring_answer_changed=sum(r['answer_changed'] for r in changes),
        old_score_complete=sum(r['score_complete'] for r in old),new_score_complete=sum(r['score_complete'] for r in rows),
        inputs={'observed_trajectories_sha256':behavior.sha(a.observed/'trajectories.csv'),'formal_agent_rows_sha256':behavior.sha(a.agent_rows)},
        script_sha256=behavior.sha(Path(__file__)),
        limits='Observed actions and stopping causes are identical. Only final extraction/scoring attributes are joined from full formal rescoring; no counterfactual model decisions are simulated.'))
    print(json.dumps({'status':'PASS','traces':486,'score_changed':sum(r['score_changed'] for r in changes)},indent=2))


if __name__=='__main__':main()
