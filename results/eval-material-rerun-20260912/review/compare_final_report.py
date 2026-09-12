#!/usr/bin/env python3
"""Compare the frozen report to this review's SHA-bound scalar cache only.
No report/scorer imports, original result rereads, raw opens, or model calls.
"""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import statistics
import subprocess

S=Path('/lustrefs/users/chufan.shi/codex_space_tn/eval_material_rerun_20260912')
R=S/'report/full_report_v1'
I=S/'review/final_material_review/final'
P=Path('/lustrefs/users/chufan.shi/codex_space_tn/publication/five_model_report_20260911')
C='6c63f1c03c88683fa55be5cafcbb8122ac8fadaa'
MODEL={'deepseek':'deepseek-v4-flash-0731','glm':'glm-5.3','gpt':'gpt-5.6-sol','kimi':'kimi-k3'}
RMODEL={v:k for k,v in MODEL.items()}
METRIC={'raw_perf_mi':'raw_mi','raw_perf_bon':'raw_bon'}
identities={}
counts=defaultdict(int)


def data(p,sha=None):
    p=Path(p)
    b=p.read_bytes()
    h=hashlib.sha256(b).hexdigest()
    if sha:
        assert h==sha,(str(p),'SHA mismatch')
    key=str(p.relative_to(S)) if p.is_relative_to(S) else str(p)
    identities[key]={'bytes':len(b),'sha256':h}
    return b


def csvread(p):
    return list(csv.DictReader(io.StringIO(data(p).decode())))


def num(v):
    return None if v is None or v=='' else float(v)


def eq(a,b):
    a,b=num(a),num(b)
    if a is None or b is None:
        assert a is None and b is None,(a,b)
    else:
        assert math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-10),(a,b)
    counts['numeric_equalities']+=1


def avg(vals):
    return statistics.mean(vals) if vals and all(v is not None for v in vals) else None


def item_of(x):
    return x['item'].replace('audit:','cc-large:')


def old_csv(rel):
    b=subprocess.check_output(['git','-C',str(P),'show',C+':results/five-model-ranking-20260911/'+rel])
    identities['git:'+C+':'+rel]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    return b,list(csv.DictReader(io.StringIO(b.decode())))


def main():
    check=json.loads(data(I/'CHECKS.json'))
    scalar_spec=check['scalar_cache_identity']
    rows=json.loads(data(scalar_spec['path'],scalar_spec['sha256']))
    assert len(rows)==369 and sum(x['valid_agents'] for x in rows)==1476
    assert sum(x['empty_scored_agents'] for x in rows)==1
    pool={r['logical_job_id']:r for r in rows}
    assert len(pool)==369
    report_bound={
        'CHECKS.json':'5024162e0c25ca3321b685d1530e503ef25e80ef75d2ea7fe75e733b2685c0ee',
        'INPUTS.json':'c42ba4ed1edcbc9426bbddfb6878ab9e01e1f0100149ae1cb9acb0c1e93163c3',
        'README.zh.md':'c9d314a10a2cca69cd3377a0a0e8c6bff4dd961331f7a6d6e22a24956a845513',
        'DETAILS.zh.md':'6897ef03499ff2f890c146c124bc11716291d63b59e24020b4c74ff9433503c5'}
    for f,h in report_bound.items():
        data(R/f,h)
    statuses=csvread(R/'pool_status.csv')
    assert len(statuses)==369 and {x['job_id'] for x in statuses}==set(pool)
    for st in statuses:
        r=pool[st['job_id']]
        assert st['execution_status']=='completed' and st['N']==st['expected_agents']==st['scored_agents']=='4'
        assert st['model']==MODEL[r['model']] and st['item']==item_of(r)
        assert st['scenario']==r['scenario'] and st['regime']==r['regime'] and st['strategy']==r['strategy']
        assert int(st['seed'])==r['seed'] and int(st['missing_configuration_agents'])==0
    assert sum(int(x['missing_answer_agents']) for x in statuses)==1
    metrics=csvread(R/'pool_metrics.csv')
    assert len(metrics)==1512
    seen=set()
    metricset={
        'restricted_search':{'f1_mi','f1_mv'},
        'evidence_audit':{'evidence_acc_mi','evidence_acc_mv','label_acc_mi','label_acc_mv'},
        'tuning':{'gap_mi','gap_bon','gap0_mi','gap0_bon','raw_perf_mi','raw_perf_bon'}}
    for m in metrics:
        r=pool[m['job_id']]
        key=(m['job_id'],m['metric'])
        assert key not in seen and m['metric'] in metricset[r['scenario']]
        seen.add(key)
        eq(m['value'],r[METRIC.get(m['metric'],m['metric'])])
        assert m['N']=='4' and m['execution_status']=='completed'
    assert seen=={(jid,met) for jid,r in pool.items() for met in metricset[r['scenario']]}
    counts['pool_scalar_rows']=len(metrics)
    goldgroups=defaultdict(list)
    for r in rows:
        for metric in metricset[r['scenario']]:
            goldgroups[(MODEL[r['model']],r['scenario'],r['regime'],r['strategy'],metric)].append(r)
    aggregates=csvread(R/'aggregate_metrics.csv')
    assert len(aggregates)==len(goldgroups)==132
    def gold_values(group,metric):
        return [r[METRIC.get(metric,metric)] for r in group]
    def mean_items(group,metric):
        items=defaultdict(list)
        for r in group:
            items[item_of(r)].append(r[METRIC.get(metric,metric)])
        return avg([avg(v) for v in items.values()])
    mean_index={}
    for a in aggregates:
        k=tuple(a[x] for x in ('model','scenario','regime','strategy','metric'))
        g=goldgroups[k]
        want=mean_items(g,a['metric'])
        eq(a['full_mean'],want)
        eq(a['known_subset_item_weighted_mean'],want)
        assert int(a['expected_pools'])==int(a['known_pools'])==len(g) and int(a['missing_pools'])==0
        assert int(a['expected_items'])==int(a['complete_items'])==len({r['item'] for r in g})
        assert int(a['repeats_per_item'])==(3 if a['scenario']=='tuning' else 1)
        mean_index[k]=want
    counts['aggregate_rows']=len(aggregates)
    effects=csvread(R/'contrasts.csv')
    assert len(effects)==132
    for a in effects:
        k=tuple(a[x] for x in ('model','scenario','regime'))
        t=mean_index[k+(a['target'],a['metric'])]
        b=mean_index[k+(a['baseline'],a['metric'])]
        assert a['strategy']==a['target']+'_minus_'+a['baseline'] and a['effect_definition']=='target_minus_baseline'
        eq(a['full_mean'],None if t is None or b is None else t-b)
        assert int(a['expected_pools'])==int(a['known_pools']) and int(a['missing_pools'])==0
    counts['contrast_rows']=len(effects)
    paired=csvread(R/'paired_rows.csv')
    assert len(paired)==1512
    for a in paired:
        b,t=pool[a['baseline_job_id']],pool[a['target_job_id']]
        assert all(b[k]==t[k] for k in ('model','scenario','regime','item','seed'))
        assert b['strategy']==a['baseline'] and t['strategy']==a['target']
        key=METRIC.get(a['metric'],a['metric'])
        eq(a['baseline_value'],b[key]); eq(a['target_value'],t[key]); eq(a['value'],t[key]-b[key])
    counts['paired_rows']=len(paired)
    for fname,split in [('by_outerseed.csv','seed'),('by_item.csv','item')]:
        subset_rows=csvread(R/fname)
        for a in subset_rows:
            k=tuple(a[x] for x in ('model','scenario','regime','strategy','metric'))
            g=[r for r in goldgroups[k] if str(r['seed'] if split=='seed' else item_of(r))==a[split]]
            assert g
            eq(a['full_mean'],mean_items(g,a['metric']))
        counts[fname+'_rows']=len(subset_rows)
    _,old=old_csv('absolute_settings.csv')
    _,old0=old_csv('main_findings_v2/gap0_settings.csv')
    historical=csvread(R/'historical_comparison.csv')
    assert len(historical)==132
    for h in historical:
        key=tuple(h[k] for k in ('model','scenario','regime','strategy','metric'))
        use0=h['metric'].startswith('gap0_')
        source=old0 if use0 else old
        rr=[r for r in source if all(r[k]==h[k] for k in ('model','scenario','regime','strategy','metric'))
            and r['system']=='poolact' and r['slice_kind']=='all' and r['slice']=='all']
        assert len(rr)==1
        o=rr[0]
        members=goldgroups[key]
        if use0:
            assert int(o['planned_agents'])==36 and int(o['planned_pools'])==9
            strict_metric=h['metric'].replace('gap0_','gap_')
            strict=[r for r in old if all(r[k]==h[k] for k in ('model','scenario','regime','strategy')) and r['metric']==strict_metric
                    and r['system']=='poolact' and r['slice_kind']=='all' and r['slice']=='all']
            assert len(strict)==1
            strict=strict[0]
            assert int(o['valid_pools'])==int(strict['known_outcomes'])
            eq(o['strict_value'],strict['full_mean'])
        else:
            strict=o
        assert int(strict['N'])==4 and int(strict['expected_outcomes'])==len(members)
        assert int(strict['expected_items'])==len({r['item'] for r in members})
        repeats=3 if h['scenario']=='tuning' else 1
        assert all(int(strict[x])==repeats for x in ('min_repeats_per_item','max_repeats_per_item','repeat_blocks'))
        eq(h['historical_value'],o['value'] if use0 else o['full_mean'])
        eq(h['rerun_value'],mean_index[key])
        before=num(h['historical_value']); after=mean_index[key]
        eq(h['rerun_minus_historical'],None if before is None or after is None else after-before)
        assert h['not_single_patch_causal_effect']=='True'
    counts['historical_rows_all_metrics_bound']=len(historical)
    for rel,dest in [('main_findings_v2/main_expgym.csv','historical_expgym_summary.csv'),('main_findings_v2/main_family_rankings.csv','historical_family_rankings.csv')]:
        original,_=old_csv(rel)
        assert data(R/dest)==original
    families=csvread(R/'historical_family_rankings.csv')
    assert len(families)==90
    fg=defaultdict(list)
    for r in families: fg[(r['family'],r['regime'])].append(r)
    winners={}
    for k,g in fg.items():
        assert len(g)==5 and len({r['model'] for r in g})==5
        best=max(float(r['value']) for r in g)
        win={r['model'] for r in g if math.isclose(float(r['value']),best,rel_tol=0,abs_tol=1e-9)}
        assert {r['model'] for r in g if r['winner']=='True'}==win
        winners[k]=win
    fams={r['family'] for r in families}
    reshuffles=sum(winners[(f,'cost_free')]!=winners[(f,'cost_tight')] for f in fams)
    assert len(fams)==6 and reshuffles==2
    assert not set.intersection(*(winners[(f,'cost_free')] for f in fams))
    assert not set.intersection(*(winners[(f,'cost_tight')] for f in fams))
    budget=csvread(R/'historical_expgym_summary.csv')
    assert len(budget)==15
    declines=defaultdict(int)
    for r in budget:
        eq(float(r['free'])-float(r['tight']),r['free_minus_tight'])
        declines[r['scenario']]+=float(r['free_minus_tight'])>0
    assert sorted(declines.values())==[4,5,5]
    primary=[a for a in effects if a['metric']==({'tuning':'gap_mi','restricted_search':'f1_mv','evidence_audit':'evidence_acc_mv'}[a['scenario']])]
    assert sum(float(a['full_mean'])>0 for a in primary if a['strategy']=='poolact_minus_naive')==8
    assert sum(float(a['full_mean'])>0 for a in primary if a['strategy']=='poolact_minus_cached')==7
    assert len([a for a in primary if a['regime']=='cost_tight' and a['target']=='poolact'])==10
    assert all(float(a['full_mean'])>0 for a in primary if a['regime']=='cost_tight' and a['target']=='poolact')
    resources=csvread(R/'resources_by_setting.csv')
    assert len(resources)==27
    resource_gold=json.loads(data(I/'RESOURCE_CHECKS.json'))
    for model,ident in MODEL.items():
        rs=[r for r in resources if r['model']==ident]
        assert sum(int(r['planned_pools']) for r in rs)==len([r for r in rows if r['model']==model])
        if model=='gpt':
            mapping={'physical_attempts_known_subtotal':'formal_successful_requests','input_tokens_known_subtotal':'known_input_tokens',
                     'output_tokens_known_subtotal':'known_output_tokens','reasoning_tokens_known_subtotal':'known_reasoning_tokens_subset_output'}
            assert all(r['request_wall_seconds_complete_total']==r['pool_wall_seconds_complete_total']=='' for r in rs)
        else:
            mapping={k:k for k in ('physical_attempts_known_subtotal','input_tokens_known_subtotal','output_tokens_known_subtotal','reasoning_tokens_known_subtotal','request_wall_seconds_known_subtotal','pool_wall_seconds_known_subtotal')}
        for k,g in mapping.items(): eq(sum(float(r[k]) for r in rs),resource_gold[model][g])
    config=json.loads(data(S/'report/preparation_config.json'))
    gpu_hours={}
    for model,spec in config['public_accounting'].items():
        m=json.loads(data(spec['path'],spec['sha256']))
        assert m['accounting']['final'] and m['release']['normal_release_after_complete_and_observed_idle']
        assert not m['release']['task_interrupted_by_release'] and not m['release']['provider_quiescence_proven']
        expected=0
        for replica in m['replicas']:
            start=datetime.fromisoformat(replica['start_utc'].replace('Z','+00:00'))
            end=datetime.fromisoformat(replica['slurm_end_utc'].replace('Z','+00:00'))
            seconds=(end-start).total_seconds()
            expected+=seconds*m['serving']['tp_size']/3600
        eq(expected,m['accounting']['gpu_hours_total'])
        gpu_hours[model]=expected
    eq(sum(gpu_hours.values()),328.5311111111111)
    data(S/'EXECUTION_NOTES.zh.md','3432da6055fdfb3bc330fc8225781c3ce30b66fb3c60528b73a6e69ecf40a856')
    outcome={'schema':'expgym.independent-final-report-review.v1','passed':True,
        'scope':'Saved scalar aggregation, report CSV and prose/source-contract review; no raw/scorer/model calls',
        'pools':369,'agents':1476,'scored_agents':1476,'cells':9,'strategy_settings':27,
        'empty_scored_members':1,'unscored_members':0,'nas_members':540,
        'primary_pool_above_naive':8,'primary_pool_above_cached':7,'primary_cells':9,
        'tight_primary_pool_above_both':5,'old_family_winner_reshuffles':2,'old_families':6,
        'checks':dict(counts),'allocation_gpu_hours':gpu_hours,'allocation_gpu_hours_total':sum(gpu_hours.values()),
        'source_notes_consistent':True,'report_prose_checked_by_reviewer':True,
        'public_layout_contract':'Report and 35 shared inputs flattened to study root; attempts/resource_exports/accounting resolve relative to the root ALL_ATTEMPTS_INDEX.json',
        'archive_path_resolution_issue_resolved_by_flattened_layout':True,
        'archive_remote_verification_not_performed_by_this_reviewer':True,
        'identities':identities}
    (I/'REPORT_COMPARISON.json').write_text(json.dumps(outcome,indent=2)+'\n')
    print(json.dumps({k:v for k,v in outcome.items() if k!='identities'},indent=2))


if __name__=='__main__': main()
