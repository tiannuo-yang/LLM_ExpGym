#!/usr/bin/env python3
"""Recompute all report display, regret, and POOLACT tables from versioned scalars.

No expected score/direction is hard coded. This does not execute task scoring.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

MODELS = ['kimi-k3','glm-5.3','qwen3.8-2.4t-a95b-fp8','deepseek-v4-flash-0731','gpt-5.6-sol','gemini-3.8-flash-medium']
NAMES = dict(zip(MODELS, ['Kimi','GLM','Qwen','DeepSeek','GPT','Gemini*']))
BUDGETS = ['cost_free','cost_moderate','cost_tight']
STRATEGIES = ['naive','cached','poolact']

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args = ap.parse_args()
    def read(name):
        with (args.source/name).open(newline='') as f:
            return list(csv.DictReader(f))
    absolute=read('absolute_settings.csv'); ranks=read('dimension_rankings.csv'); slots=read('slot_scalars.csv')
    lookup={tuple(r[k] for k in ['system','scenario','slice_kind','slice','regime','strategy','metric','model']):r for r in absolute}
    assert len(lookup)==len(absolute)
    def score(system,scene,kind,slice_,regime,strategy,metric,model):
        r=lookup[(system,scene,kind,slice_,regime,strategy,metric,model)]
        assert r['full_mean'] != '' and int(r['missing_units'])==0
        return float(r['full_mean'])*(100 if r['unit']=='fraction' else 1)
    def winners(values):
        return [m for m in MODELS if math.isclose(values[m],max(values.values()),rel_tol=0,abs_tol=1e-9)]
    def write(name,rows):
        with (args.output/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    args.output.mkdir(parents=True,exist_ok=True)
    dimension_rows=[]
    for dim in dict.fromkeys(r['dimension'] for r in ranks):
        values={b:{r['model']:float(r['full_mean'])*(100 if r['metric'] in ['f1','evidence_acc','label_acc'] else 1) for r in ranks if r['dimension']==dim and r['regime']==b} for b in BUDGETS}
        assert all(set(v)==set(MODELS) for v in values.values())
        free,tight=values['cost_free'],values['cost_tight'];fw,tw=winners(free),winners(tight)
        regrets={m:max(tight.values())-tight[m] for m in fw}
        dimension_rows.append(dict(dimension=dim,n_models=6,free_leaders=';'.join(fw),free_best=max(free.values()),free_leader_tight=';'.join(str(tight[m]) for m in fw),moderate_leaders=';'.join(winners(values['cost_moderate'])),tight_leaders=';'.join(tw),tight_best=max(tight.values()),leader_set_changed=set(fw)!=set(tw),regret_min=min(regrets.values()),regret_max=max(regrets.values())))
    task_rows=[];task_scores=[]
    tuning=[r for r in slots if r['system']=='expgym' and r['scenario']=='tuning']
    assert len(tuning)==486 and all(r['execution_complete']=='True' for r in tuning)
    missing_strict = sum(r['score_complete']=='False' for r in tuning)
    for task in sorted(set(r['item'] for r in tuning)):
        values={}
        for b in BUDGETS:
            values[b]={}
            for m in MODELS:
                chosen=[r for r in tuning if r['item']==task and r['regime']==b and r['model']==m]
                assert len(chosen)==3 and len({r['outer_repeat'] for r in chosen})==3
                scores=[json.loads(r['metrics_json'])['gap0'] for r in chosen]
                assert all(x is not None for x in scores)
                values[b][m]=statistics.mean(scores)
                task_scores.append(dict(task=task,model=m,regime=b,gap0=values[b][m],repeats=3,slot_ids=';'.join(r['slot_id'] for r in chosen)))
        free,tight=values['cost_free'],values['cost_tight'];fw,tw=winners(free),winners(tight)
        regrets={m:max(tight.values())-tight[m] for m in fw}
        task_rows.append(dict(task=task,n_models=6,free_leaders=';'.join(fw),free_best=max(free.values()),tight_leaders=';'.join(tw),tight_best=max(tight.values()),free_tied=len(fw)>1,regret_by_free_leader=json.dumps(regrets,sort_keys=True),regret_min=min(regrets.values()),regret_max=max(regrets.values())))
    n1_rows=[]
    for m in MODELS:
        for b in BUDGETS:
            n1_rows.append(dict(model=m,regime=b,search_f1=score('expgym','restricted_search','all','all',b,'single','f1',m),audit_ea=score('expgym','evidence_audit','all','all',b,'single','evidence_acc',m),audit_la=score('expgym','evidence_audit','all','all',b,'single','label_acc',m),hpo_gap0=score('expgym','tuning','all','all',b,'single','gap0',m)))
    primary_rows=[];pool_summaries=[];bon_rows=[]
    for scene,metric in [('restricted_search','f1_mv'),('evidence_audit','evidence_acc_mv'),('tuning','gap0_mi')]:
        for b in BUDGETS[1:]:
            vals={s:{m:score('poolact',scene,'all','all',b,s,metric,m) for m in MODELS} for s in STRATEGIES}
            for m in MODELS:
                row=dict(scenario=scene,regime=b,model=m,metric=metric,**{s:vals[s][m] for s in STRATEGIES})
                row.update(poolact_minus_naive=row['poolact']-row['naive'],poolact_minus_cached=row['poolact']-row['cached'])
                primary_rows.append(row)
            macro={s:statistics.mean(vals[s].values()) for s in STRATEGIES}
            pool_summaries.append(dict(scenario=scene,regime=b,n_models=6,metric=metric,**macro,poolact_minus_naive=macro['poolact']-macro['naive'],poolact_minus_cached=macro['poolact']-macro['cached']))
    for b in BUDGETS[1:]:
        for s in STRATEGIES:
            mi=statistics.mean(score('poolact','tuning','all','all',b,s,'gap0_mi',m) for m in MODELS)
            bon=statistics.mean(score('poolact','tuning','all','all',b,s,'gap0_bon',m) for m in MODELS)
            strict_mi=[lookup[('poolact','tuning','all','all',b,s,'gap_mi',m)]['full_mean'] for m in MODELS]
            strict_bon=[lookup[('poolact','tuning','all','all',b,s,'gap_bon',m)]['full_mean'] for m in MODELS]
            strict_mi_mean=statistics.mean(float(v) for v in strict_mi) if all(v!='' for v in strict_mi) else None
            strict_bon_mean=statistics.mean(float(v) for v in strict_bon) if all(v!='' for v in strict_bon) else None
            bon_rows.append(dict(regime=b,strategy=s,n_models=6,gap0_mi=mi,gap0_bon=bon,bon_minus_mi=bon-mi,strict_gap_mi_macro=strict_mi_mean,strict_gap_bon_macro=strict_bon_mean,strict_equals_gap0=strict_mi_mean is not None and strict_bon_mean is not None and math.isclose(strict_mi_mean,mi,rel_tol=0,abs_tol=1e-9) and math.isclose(strict_bon_mean,bon,rel_tol=0,abs_tol=1e-9)))
    budget_rows=[]
    for metric in ['search_f1','audit_ea','audit_la','hpo_gap0']:
        for m in MODELS:
            vals={r['regime']:r[metric] for r in n1_rows if r['model']==m}
            f,md,t=(vals[b] for b in BUDGETS)
            budget_rows.append(dict(model=m,metric=metric,free=f,moderate=md,tight=t,moderate_minus_free=md-f,tight_minus_moderate=t-md,tight_minus_free=t-f,monotonic_decline=f>md>t))
    for name,rows in [('budget_effects.csv',budget_rows),('dimension_selection.csv',dimension_rows),('hpo_task_regret.csv',task_rows),('hpo_task_scores.csv',task_scores),('n1_main.csv',n1_rows),('poolact_primary.csv',primary_rows),('poolact_scenario_summary.csv',pool_summaries),('nas_best_minus_mean.csv',bon_rows)]:
        write(name,rows)
    findings=json.loads((args.source/'FINDINGS.json').read_text())
    count=sum(r['poolact_minus_naive']>0 and r['poolact_minus_cached']>0 for r in primary_rows)
    tight_count=sum(r['regime']=='cost_tight' and r['poolact_minus_naive']>0 and r['poolact_minus_cached']>0 for r in primary_rows)
    assert count==findings['poolact']['all']['poolact_above_both']
    assert tight_count==findings['poolact']['tight']['poolact_above_both']
    leader_changes = sum(r['leader_set_changed'] for r in dimension_rows)
    summary=dict(status='PASS',source='supplied_versioned_public_tables',sources={n:dict(sha256=hashlib.sha256((args.source/n).read_bytes()).hexdigest(),bytes=(args.source/n).stat().st_size) for n in ['absolute_settings.csv','dimension_rankings.csv','slot_scalars.csv','FINDINGS.json']},scoring='Scores supplied by the explicit scoring cohort; see source SCORE_VERSIONS.json; no model calls in this script',n1_hpo_slots=486,n1_hpo_missing_strict_score=missing_strict,dimension_leader_changes=leader_changes,dimension_count=7,task_positive_regret_optimistic_tie=sum(r['regret_min']>1e-9 for r in task_rows),task_positive_regret_pessimistic_tie=sum(r['regret_max']>1e-9 for r in task_rows),poolact_above_both=count,poolact_tight_above_both=tight_count,n1_hpo_model_macro={b:statistics.mean(r['hpo_gap0'] for r in n1_rows if r['regime']==b) for b in BUDGETS},tie_absolute_tolerance=1e-9)
    (args.output/'CHECKS.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
