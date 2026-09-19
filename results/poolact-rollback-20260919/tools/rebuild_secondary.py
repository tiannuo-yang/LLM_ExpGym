#!/usr/bin/env python3
"""Update all Search score-conditioned behavior and all POOLACT contrasts.

Unchanged acquisition fields are replayed from the hash-bound published behavior
projection. Every Search score and every score-conditioned stratum/pair/case is
recomputed from the new full scalar cohort, not from the identified-error list.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from statistics import mean, median


def rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, list(data[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(data)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--source', type=Path, required=True, help='New main aggregates with full scalars and selection')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    paper = args.repo / 'results/paper-analysis-20260916'
    mod_path = paper / 'search/analyze_search.py'
    spec = importlib.util.spec_from_file_location('frozen_search_behavior', mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    scalars = rows(args.source / 'slot_scalars.csv')
    selected = {r['slot_id']: r for r in rows(args.source / 'SOURCE_SELECTION.csv')}
    search = [r for r in scalars if r['system'] == 'expgym' and r['scenario'] == 'restricted_search']
    scalar_index = {(r['model'], r['regime'], r['item']): r for r in search}
    assert len(search) == len(scalar_index) == 1314
    originals = rows(paper / 'search/trajectory_metrics.csv')
    strings = {'model','cohort','regime','family','source','termination_reason','answer_source','trace_path','trace_sha256'}
    updated, changes = [], []
    for original in originals:
        row = {k: (v if k in strings else float(v) if '.' in v or 'e' in v.lower() else int(v)) if v else None for k, v in original.items()}
        key = row['model'], row['regime'], f'{row["source"]}:{row["question_id"]}'
        scalar = scalar_index[key]
        old_score = row['score']
        row['score'] = json.loads(scalar['metrics_json'])['f1']
        assert row['score'] is not None
        source = selected[scalar['slot_id']]
        assert source['result_sha256'] == row['trace_sha256']
        row['slot_id'] = scalar['slot_id']
        row.pop('trace_path')
        row['old_score'] = old_score
        row['score_changed'] = abs(row['score'] - old_score) > 1e-12
        updated.append(row)
        changes.append(dict(slot_id=row['slot_id'], model=row['model'], regime=row['regime'], source=row['source'], question_id=row['question_id'], old_score=old_score, new_score=row['score'], delta=row['score']-old_score, changed=row['score_changed']))
    index = {(r['model'], r['source'], str(r['question_id']), r['regime']):r for r in updated}
    write(args.output / 'search/trajectory_metrics.csv', updated)
    write(args.output / 'search/score_comparison.csv', changes)
    for name, keys in [('by_model_regime', ['model','regime']), ('by_family_regime',['family','regime']), ('by_model_family_regime',['model','family','regime']), ('overall_regime',['regime'])]:
        write(args.output / f'search/{name}.csv', mod.summary(updated,keys))
    paired = rows(paper / 'search/free_tight_paired.csv')
    for pair in paired:
        free = index[pair['model'], pair['source'], pair['question_id'], 'cost_free']
        tight = index[pair['model'], pair['source'], pair['question_id'], 'cost_tight']
        pair.update(free_score=free['score'], tight_score=tight['score'], score_change=tight['score'] - free['score'], free_slot_id=free['slot_id'], tight_slot_id=tight['slot_id'])
        pair.pop('free_trace_path')
        pair.pop('tight_trace_path')
    assert len(paired) == 438
    write(args.output / 'search/free_tight_paired.csv', paired)
    pair_summary = []
    for model in ['ALL'] + sorted({r['model'] for r in paired}):
        group = [r for r in paired if model == 'ALL' or r['model'] == model]
        pair_summary.append(dict(model=model, n_pairs=len(group), tight_lower=sum(r['score_change'] < -1e-12 for r in group), tied=sum(abs(r['score_change']) <= 1e-12 for r in group), tight_higher=sum(r['score_change'] > 1e-12 for r in group), same_first_article=sum(r['same_first_article']=='True' for r in group), tight_exact_free_prefix=sum(r['tight_is_free_prefix']=='True' for r in group)))
    write(args.output / 'search/paired_direction_summary.csv', pair_summary)
    cases = []
    for model in sorted({r['model'] for r in updated}):
        for regime, term in [('cost_tight','time_budget_exceeded'),('cost_free','natural_answer')]:
            candidates = [r for r in updated if r['model']==model and r['regime']==regime and r['termination_reason']==term and r['score']<1]
            candidates.sort(key=lambda r:(r['unique_visible_articles'],r['source'],r['question_id']))
            if not candidates:
                continue
            chosen = candidates[len(candidates)//2]
            case = {k:chosen[k] for k in ('slot_id','model','regime','source','question_id','score','unique_visible_articles','attempted_feedback','termination_reason','trace_sha256')}
            case.update(selection='Upper median distinct visible articles among imperfect answers in model/regime/terminal stratum; source/qid tiebreak',candidate_count=len(candidates))
            cases.append(case)
    write(args.output / 'search/representative_case_index.csv',cases)
    absolute = rows(args.source / 'absolute_settings.csv')
    main_search={(r['model'],r['regime']):float(r['full_mean']) for r in absolute if r['system']=='expgym' and r['scenario']=='restricted_search' and r['slice_kind']=='all' and r['metric']=='f1'}
    for row in mod.summary(updated,['model','regime']):
        assert abs(row['mean_score']-main_search[row['model'],row['regime']])<1e-12
    groups=defaultdict(dict)
    for row in absolute:
        if row['system']=='poolact' and row['slice_kind']=='all':
            groups[tuple(row[k] for k in ('model','scenario','regime','metric'))][row['strategy']]=row
    pool_rows=[]
    for key, arms in sorted(groups.items()):
        assert set(arms)=={'naive','cached','poolact'}
        scale=100 if arms['poolact']['unit']=='fraction' else 1
        values={s:float(r['full_mean'])*scale if r['full_mean']!='' else None for s,r in arms.items()}
        complete=all(v is not None for v in values.values())
        result=dict(zip(('model','scenario','regime','metric'),key))
        result.update(reported_unit='0-100' if scale==100 else arms['poolact']['unit'],complete_three_strategy=complete,**values)
        for baseline in ('naive','cached'):
            a,b=values['poolact'],values[baseline]
            result['delta_vs_'+baseline]=a-b if a is not None and b is not None else None
            result['relative_percent_vs_'+baseline]=(a/b-1)*100 if a is not None and b not in (None,0) else None
        result['delta_vs_stronger_baseline']=values['poolact']-max(values['naive'],values['cached']) if complete else None
        pool_rows.append(result)
    assert len(pool_rows)==144
    write(args.output/'poolact/poolact_all_metrics.csv',pool_rows)
    primary_metrics={'restricted_search':'f1_mv','evidence_audit':'evidence_acc_mv','tuning':'gap0_mi'}
    primary=[r for r in pool_rows if r['metric']==primary_metrics[r['scenario']]]
    write(args.output/'poolact/poolact_primary.csv',primary)
    summaries=[]
    for scenario,metric in primary_metrics.items():
        for regime in ('cost_moderate','cost_tight'):
            group=[r for r in primary if r['scenario']==scenario and r['regime']==regime and r['complete_three_strategy']]
            row=dict(scenario=scenario,regime=regime,metric=metric,matched_models=len(group))
            row.update({s+'_model_macro':mean(r[s] for r in group) for s in ('naive','cached','poolact')})
            for base in ('naive','cached','stronger_baseline'):
                deltas=[r['delta_vs_'+base] for r in group]
                row.update({f'{stat}_delta_vs_{base}':fn(deltas) for stat,fn in [('mean',mean),('median',median),('min',min),('max',max)]})
                row['positive_vs_'+base]=sum(v>0 for v in deltas)
            summaries.append(row)
    write(args.output/'poolact/poolact_scenario_summary.csv',summaries)
    deep = [r for r in scalars if r['system']=='expgym' and r['scenario']=='tuning' and r['model']=='deepseek-v4-flash-0731']
    assert len(deep)==81
    delivery=[]
    for regime in ('cost_free','cost_moderate','cost_tight'):
        chosen=[r for r in deep if r['regime']==regime]
        metrics=[json.loads(r['metrics_json']) for r in chosen]
        known=[m['gap'] for m in metrics if m['gap'] is not None]
        assert len(chosen)==27
        complete_rate=len(known)/27
        conditional=mean(known) if known else None
        gap0=mean(m['gap0'] for m in metrics)
        assert conditional is None or abs(complete_rate*conditional-gap0)<1e-9
        delivery.append(dict(model='deepseek-v4-flash-0731',regime=regime,expected_task_repeats=27,score_complete_task_repeats=len(known),normal_missing_configuration=27-len(known),score_complete_rate=complete_rate,conditional_strict_gap_repeat_equal=conditional,gap0_all_task_repeats=gap0))
    write(args.output/'cases/deepseek_delivery.csv',delivery)
    deep_index={(r['item'],r['outer_repeat'],r['regime']):r for r in deep}
    deep_pairs=[]
    for free in deep:
        if free['regime']!='cost_free':
            continue
        tight=deep_index[free['item'],free['outer_repeat'],'cost_tight']
        f,t=[json.loads(r['metrics_json']) for r in (free,tight)]
        transition=('scored' if f['gap'] is not None else 'missing')+'_to_'+('scored' if t['gap'] is not None else 'missing')
        deep_pairs.append(dict(model=free['model'],task=free['item'],repeat=free['outer_repeat'],seed=free['seed'],transition=transition,free_slot_id=free['slot_id'],tight_slot_id=tight['slot_id'],free_score_complete=f['gap'] is not None,tight_score_complete=t['gap'] is not None,free_strict_gap=f['gap'],tight_strict_gap=t['gap'],free_gap0=f['gap0'],tight_gap0=t['gap0'],tight_minus_free_gap0=t['gap0']-f['gap0']))
    write(args.output/'cases/deepseek_paired_delivery.csv',deep_pairs)
    deep_transitions=[]
    for transition in ('scored_to_scored','missing_to_scored','scored_to_missing','missing_to_missing'):
        chosen=[r for r in deep_pairs if r['transition']==transition]
        deep_transitions.append(dict(transition=transition,pairs=len(chosen),free_gap0_mean_in_group=mean(r['free_gap0'] for r in chosen) if chosen else None,tight_gap0_mean_in_group=mean(r['tight_gap0'] for r in chosen) if chosen else None,contribution_to_all_27_delta=sum(r['tight_minus_free_gap0'] for r in chosen)/27))
    write(args.output/'cases/deepseek_delivery_transitions.csv',deep_transitions)
    assert abs(sum(r['contribution_to_all_27_delta'] for r in deep_transitions)-(delivery[2]['gap0_all_task_repeats']-delivery[0]['gap0_all_task_repeats']))<1e-9
    case=next(r for r in deep_pairs if r['task']=='hpobench:nasbench101:C' and r['seed']=='2208')
    qwen_free=index['qwen3.8-2.4t-a95b-fp8','phantom_seed2','31','cost_free']
    qwen_tight=index['qwen3.8-2.4t-a95b-fp8','phantom_seed2','31','cost_tight']
    case_rows=[]
    for label,slot_id,score in [('search_qwen_free',qwen_free['slot_id'],qwen_free['score']),('search_qwen_tight',qwen_tight['slot_id'],qwen_tight['score']),('hpo_deepseek_free',case['free_slot_id'],case['free_gap0']),('hpo_deepseek_tight',case['tight_slot_id'],case['tight_gap0'])]:
        case_rows.append(dict(case=label,slot_id=slot_id,new_score=score,source_sha256=selected[slot_id]['result_sha256'],selection='Retain the pre-repair illustrative case; recompute its current endpoint, do not reselect for a larger score difference'))
    write(args.output/'cases/fixed_case_scores.csv',case_rows)
    (args.output/'cases/CASE_INDEX.zh.md').write_text(f'''# 固定案例与新评分

原稿案例作为固定解释性样例保留；新主分数与全部代表候选另行重算，不以最大分差重新选例。[四个单体端点与来源 SHA](fixed_case_scores.csv)。

## Search query diversity

Qwen，phantom_seed2 第 31 题。Free 的前四个不同查询返回同一文章，16 次可见反馈覆盖 11 篇不同文章。新评分 Free F1={qwen_free['score']:.12g}，Tight F1={qwen_tight['score']:.12g}。该例解释动作字符串不同不等于观测不同；不是额外预算必然提升的因果证据。[全量候选规则与新代表索引](../search/representative_case_index.csv)。

## HPO delivery

DeepSeek，NAS101 C，seed 2208。保留同一 Free/Tight 槽位，新 Gap0 为 {case['free_gap0']:.12g} / {case['tight_gap0']:.12g}，严格分数状态为 {case['free_score_complete']} / {case['tight_score_complete']}。原可见评估与停止事件保存在完整 486 行为导出中，获取和交付不能混为一谈。[27 对交付变化](deepseek_paired_delivery.csv)。

## Audit evidence completion and PoolAct coverage sharing

Qwen 文档 10、顺序 1、nda-13 和 Kimi Moderate 审计文档 3 的完整新旧证据、投票、候选 membership 与总体配对数由 [Audit 全量重算](../audit/README.zh.md)核验。原始动作历史与可见共享消息不因离线新评分而改写。
''')
    checks=dict(status='PASS',search_all_1314_scores_replaced=True,search_scores_changed=sum(r['changed'] for r in changes),search_paired_questions=len(paired),search_source_hashes_bound=True,search_18_means_match_new_main=True,poolact_all_metric_rows=len(pool_rows),poolact_primary_rows=len(primary),source_sha256={str(p.relative_to(paper)):sha(p) for p in (paper/'search/trajectory_metrics.csv',paper/'search/free_tight_paired.csv',mod_path)},scope='Existing Search acquisition projections are unchanged; all final-score-conditioned outputs are rebuilt from the new score version. POOLACT contrasts use every current setting mean.')
    (args.output/'CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks,indent=2))


if __name__=='__main__':
    main()
