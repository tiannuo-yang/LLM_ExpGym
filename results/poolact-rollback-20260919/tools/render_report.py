#!/usr/bin/env python3
"""Render the full paper narrative from explicit scoring/behavior versions.

Preserves the scientific structure of the prior paper, with full replacements
of affected paragraphs and tables. Requires all updated behavior tables.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from statistics import mean, median

MODELS=['kimi-k3','glm-5.3','qwen3.8-2.4t-a95b-fp8','deepseek-v4-flash-0731','gpt-5.6-sol','gemini-3.8-flash-medium']
NAMES=dict(zip(MODELS,['Kimi','GLM','Qwen','DeepSeek','GPT','Gemini*']))
BUDGETS=['cost_free','cost_moderate','cost_tight']
STRATEGIES=['naive','cached','poolact']

def read(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))

def table(head, body):
    return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |',*['| '+' | '.join(map(str,r))+' |' for r in body]])

def f(value, digits=2):
    return f'{float(value):.{digits}f}'

def names(value):
    return ' / '.join(NAMES.get(m,m) for m in value.split(';'))

def replace_paragraph(text, start, replacement):
    pattern=re.escape(start)+r'[^\n]*(?:\n(?!\n)[^\n]*)*'
    text,n=re.subn(pattern,lambda m:replacement,text,count=1)
    assert n==1,start
    return text

def replace_table(text, first_header, replacement):
    pattern=re.escape(first_header)+r'[^\n]*\n(?:\|[^\n]*\n?)+'
    text,n=re.subn(pattern,lambda m:replacement+'\n',text,count=1)
    assert n==1,first_header
    return text

def replace_section(text, heading, next_heading, replacement):
    start=text.index(heading);end=text.index(next_heading,start)
    return text[:start]+replacement.rstrip()+'\n\n'+text[end:]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--main',type=Path,required=True)
    ap.add_argument('--display',type=Path,required=True)
    ap.add_argument('--secondary',type=Path,required=True)
    ap.add_argument('--audit',type=Path,required=True)
    ap.add_argument('--hpo',type=Path,required=True,help='Official 486 behavior directory')
    ap.add_argument('--existing-rescore',type=Path,help='Frozen existing-trace rescore layer, separate from new runtime adoption')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--public-prefix',default='../poolact-rollback-20260919')
    args=ap.parse_args()
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    prior=args.repo/'results/paper-analysis-20260916'
    prefix=args.public_prefix.rstrip('/')
    template=prior/'README.pre-repair-297c3d0.zh.md'
    if not template.exists():
        template=prior/'README.zh.md'
    doc=template.read_text()
    version=json.loads((args.main/'SCORE_VERSIONS.json').read_text())
    existing_rescore=args.existing_rescore or args.repo/'results/protocol-repair-20260918/rescore/main'
    legacy_diffs=read(existing_rescore/'sample_diff.csv')
    assert len(legacy_diffs)==4698
    legacy_any=sum(r['score_changed']=='True' for r in legacy_diffs)
    legacy_endpoint=sum(r['endpoint_score_changed']=='True' for r in legacy_diffs)
    legacy_primary=0
    for row in legacy_diffs:
        before,after=json.loads(row['old_metrics_json']),json.loads(row['new_metrics_json'])
        key=({'restricted_search':'f1','evidence_audit':'evidence_acc','tuning':'gap0'} if row['system']=='expgym' else {'restricted_search':'f1_mv','evidence_audit':'evidence_acc_mv','tuning':'gap0_mi'})[row['scenario']]
        a,b=before.get(key),after.get(key)
        legacy_primary+=((a is None)!=(b is None)) or (a is not None and b is not None and not math.isclose(a,b,rel_tol=0,abs_tol=1e-12))
    fairness=version.get('runtime_fairness') or version.get('hpo_fairness') or {}
    runtime_commit='N4 historical execution versions retained'
    auxiliary_runtime_commits={}
    core_commit=version['new']['code_commit']
    checks=json.loads((args.main/'CHECKS.json').read_text())
    findings=json.loads((args.main/'FINDINGS.json').read_text())
    dcheck=json.loads((args.display/'CHECKS.json').read_text())
    n1=read(args.display/'n1_main.csv');ni={(r['model'],r['regime']):r for r in n1}
    dims=read(args.display/'dimension_selection.csv')
    regrets=read(args.display/'hpo_task_regret.csv')
    task_scores=read(args.display/'hpo_task_scores.csv')
    p1=read(args.secondary/'poolact/poolact_primary.csv');pi={(r['model'],r['scenario'],r['regime']):r for r in p1}
    pa=read(args.secondary/'poolact/poolact_all_metrics.csv')
    ps=read(args.secondary/'poolact/poolact_scenario_summary.csv');psi={(r['scenario'],r['regime']):r for r in ps}
    bon=read(args.display/'nas_best_minus_mean.csv');bi={(r['regime'],r['strategy']):r for r in bon}
    sb=read(args.secondary/'search/overall_regime.csv');sbi={r['regime']:r for r in sb}
    sm=read(args.secondary/'search/by_model_regime.csv');smi={(r['model'],r['regime']):r for r in sm}
    search_pairs=read(args.secondary/'search/paired_direction_summary.csv');sp=next(r for r in search_pairs if r['model']=='ALL')
    hpo=read(args.hpo/'by_regime.csv');hi={r['regime']:r for r in hpo}
    ab=read(args.audit/'n1/budget_metrics.csv');ai={r['budget']:r for r in ab}
    ah=read(args.audit/'n1/hypothesis_metrics.csv')
    ac=read(args.audit/'n1/diagnostic_counts.csv')
    patterns=read(args.audit/'n1/paired_completion_patterns.csv')
    coords=read(args.audit/'coordination/audit_groups.csv')
    coord_pools=read(args.audit/'coordination/audit_pools.csv')
    audit_check=json.loads((args.audit/'CHECKS.json').read_text())
    case_population=audit_check.get('case_population',[])
    current_case_population=next((r for r in reversed(case_population) if r.get('score_version')!='old'),{})
    deep=read(args.secondary/'cases/deepseek_delivery.csv');di={r['regime']:r for r in deep}
    transitions=read(args.secondary/'cases/deepseek_delivery_transitions.csv');both=next(r for r in transitions if r['transition']=='scored_to_scored')
    allslots={r['slot_id']:r for r in read(args.main/'slot_scalars.csv')}
    allsources={r['slot_id']:r for r in read(args.main/'SOURCE_SELECTION.csv')}
    matched_audit=0
    for row in read(args.audit/'n1/trace_metrics.csv'):
        metrics=json.loads(allslots[row['slot_id']]['metrics_json'])
        assert row['source_sha256']==allsources[row['slot_id']]['result_sha256']
        for field in ['label_acc','evidence_acc']:
            assert abs(float(row[field])-metrics[field])<1e-12,(row['slot_id'],field,'Audit evidence/main scoring versions differ')
        matched_audit+=1
    for row in coord_pools:
        metrics=json.loads(allslots[row['slot_id']]['metrics_json'])
        assert row['source_sha256']==allsources[row['slot_id']]['result_sha256']
        for field in ['label_acc','evidence_acc']:
            assert abs(float(row[field])-metrics[field+'_mv'])<1e-12,(row['slot_id'],field,'Audit pool/main scoring versions differ')
        matched_audit+=1
    assert matched_audit==1170
    hpo_traces=read(args.hpo/'trajectories.csv')
    assert len(hpo_traces)==486
    for row in hpo_traces:
        metrics=json.loads(allslots[row['slot_id']]['metrics_json'])
        assert row['trace_sha256']==allsources[row['slot_id']]['result_sha256']
        perf=None if row['final_performance']=='' else float(row['final_performance'])
        assert (perf is None and metrics['raw_perf'] is None) or (perf is not None and metrics['raw_perf'] is not None and abs(perf-metrics['raw_perf'])<1e-12),(row['slot_id'],'HPO behavior/main scoring versions differ')
    strict=checks['score_complete'];leaders=dcheck['dimension_leader_changes']
    win=findings['poolact']['all']['poolact_above_both'];twin=findings['poolact']['tight']['poolact_above_both']
    tight_search=[r for r in p1 if r['scenario']=='restricted_search' and r['regime']=='cost_tight']
    search_med=median(float(r['delta_vs_naive']) for r in tight_search)
    search_rel=median(float(r['relative_percent_vs_naive']) for r in tight_search)
    audit_both=sum(float(r['delta_vs_stronger_baseline'])>0 for r in p1 if r['scenario']=='evidence_audit')
    adopted=version['new']['adoption_state']=='official'
    state='单智能体保留 7776f70、多智能体恢复修复前结果的正式采用版本'
    sweep_note='独立 Whois N1 sweep 保留 7776f70 的采用来源、分数和实际 token/墙钟统计；本次 N4 回退不改变它。'
    adoption_note='本版完整恢复全部 2,196 个 N4 槽位的修复前分数和原件来源，涵盖 naive、cached、POOLACT 三种策略。97 个 HPO 池和 19 个 Search/Audit N4 修复补跑不再作为主表来源，全部保留在 7776f70 历史包中。2,502 个 N1 槽位保持 7776f70，其中包括两个 Audit 实际控制流补跑、Gemini 补齐、486 条 HPO 行为和已修复的单体终答评分。本次没有调用模型或按成绩挑选样本。'
    note=f"**2026-09-19 POOLACT 回退：**本页使用{state}。本次仅改变 N4 正式采用来源与相关代码，重新聚合全部 4,698 个主实验槽；N1 分数和来源逐项保持。本版恢复 N4 既有方案，保留单体修复；此前诊断和修复候选留作历史材料。[采用规则与逐样本对照]({prefix}/selection/sample_rollback.csv) · [独立回退核验]({prefix}/selection/ROLLBACK_MANIFEST.json) · [评分版本]({prefix}/main/SCORE_VERSIONS.json) · [结论对照]({prefix}/conclusion_delta.csv) · [回退前 7776f70 报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/7776f700902db194c69124b1a5f59d985379cfb3/results/paper-analysis-20260916/README.zh.md)。"
    doc=replace_paragraph(doc,'**2026-09-18 更新：**',note)
    doc=doc.replace(note,note+'\n\n'+adoption_note,1)
    doc=replace_paragraph(doc,'这是已观察任务与模型设置上的描述性分析。',f'这是已观察任务与模型设置上的描述性分析。“最佳”指最高观察均分，不意味着统计上显著优于其他模型。现有注册主实验覆盖 4,698/4,698 项，其中 Gemini 783/783；本评分版本严格评分完整 {strict:,} 项。正常无配置、零分与失败/未完成保持分开。完整分数、轨迹证据与来源见[数据附件](APPENDIX.zh.md)，不将不同任务指标合成为一个总榜。')
    abstract=f'LLM 智能体的表现不仅取决于如何推理，也取决于能够获取哪些外部反馈。我们基于 EXPGYM 的六模型结果，研究反馈预算如何改变任务表现、模型排序与部署选型。预算从 Free 收紧到 Tight 时，多跳搜索 F1 与证据集合准确率分别有 {findings["n1_budget"]["restricted_search"]["declined"]}/6、{findings["n1_budget"]["evidence_audit"]["declined"]}/6 个模型下降；七个评价维度中，{leaders} 个更换了最高均分模型。Free 下的领先不保证 Tight 下的最佳选择，排序变化也不必然意味着大的部署损失。我们在完整 486 条调优轨迹、1,314 条搜索轨迹和 702 条审计轨迹上分析获取、停止与最终提交，并以四智能体比较 POOLACT、独立运行与共享缓存。Tight Search 相对独立运行的模型间 F1 增益中位数为 {search_med:.2f} 个百分点；审计 {audit_both}/12 个模型—预算组合高于两种基线。本文保留单智能体的修复评分；四智能体的分数、投票结果和运行来源已恢复为修复前版本。'
    doc=replace_paragraph(doc,'LLM 智能体的表现不仅取决于如何推理，',abstract)
    budget_effects=read(args.display/'budget_effects.csv')
    mono={metric:sum(r['monotonic_decline']=='True' for r in budget_effects if r['metric']==metric) for metric in ['search_f1','audit_ea']}
    doc=replace_paragraph(doc,'搜索与审计呈现一致的预算效应：',f'搜索与审计呈现明显的预算效应：Search 有 {mono["search_f1"]}/6 个模型、Audit EA 有 {mono["audit_ea"]}/6 个模型在 Free→Moderate→Tight 两阶段均下降。')
    doc=replace_table(doc,'| 模型 | Search F1：',table(['模型','Search F1：Free / Moderate / Tight','Audit EA：Free / Moderate / Tight','HPO Gap0：Free / Moderate / Tight'],[[NAMES[m],*[' / '.join(f(ni[m,b][metric]) for b in BUDGETS) for metric in ['search_f1','audit_ea','hpo_gap0']]] for m in MODELS]))
    macro=lambda metric,b:mean(float(ni[m,b][metric]) for m in MODELS)
    doc=replace_paragraph(doc,'F1、EA 以 0–100 表示，',f'F1、EA 以 0–100 表示，差值为百分点；Gap0 使用原分数单位。六模型等权的 Search F1 从 {macro("search_f1",BUDGETS[0]):.2f} 降至 {macro("search_f1",BUDGETS[2]):.2f}，Audit EA 从 {macro("audit_ea",BUDGETS[0]):.2f} 降至 {macro("audit_ea",BUDGETS[2]):.2f}。Moderate Search 为 {macro("search_f1",BUDGETS[1]):.2f}，预算退化的幅度并非线性。压缩到很少的反馈机会时，多跳获取尤其脆弱；这是观察关联，不能把预算当作唯一因果解释。')
    doc=replace_paragraph(doc,'逐题配对也呈现相同方向：',f'逐题配对得到 {sp["n_pairs"]} 对模型—搜索题的 Free/Tight 比较：{sp["tight_lower"]} 对下降、{sp["tied"]} 对相同、{sp["tight_higher"]} 对上升。配对数用于描述已观察任务，不作为独立语料或显著性样本量。')
    doc=replace_paragraph(doc,'调优的响应更不均匀：',f'调优的响应更不均匀：Free→Tight 有 {findings["n1_budget"]["tuning"]["declined"]}/6 个模型下降、{findings["n1_budget"]["tuning"]["improved"]}/6 个提高。最终配置是否可评分也影响 Gap0，§3.2 将交付率与条件配置质量分开。现有观察不支持“每种模型、每类任务必然随预算单调退化”的普遍定律。')
    db=[]
    for r in dims:
        score=' / '.join(f(v) for v in r['free_leader_tight'].split(';'))
        regret=f(r['regret_min']) if math.isclose(float(r['regret_min']),float(r['regret_max']),abs_tol=1e-9) else f(r['regret_min'])+'–'+f(r['regret_max'])
        db.append([r['dimension'],6,names(r['free_leaders'])+' '+f(r['free_best']),score,names(r['tight_leaders'])+' '+f(r['tight_best']),regret])
    doc=replace_table(doc,'| 评价维度 | 可比模型数 |',table(['评价维度','可比模型数','Free 最高均分','该模型的 Tight 分数','Tight 最高均分','Free 选型的 Tight 损失'],db))
    doc=replace_paragraph(doc,'六模型在两端都完整的七个维度中，',f'六模型在两端都完整的七个维度中，{leaders} 个更换了第一名集合。Tight 领先者随评价维度变化，具体集合和并列保留在上表。模型选择需要结合任务与可获得的反馈，不能仅依赖 Free 表现。')
    maxreg=max(regrets,key=lambda r:float(r['regret_max']))
    doc=replace_paragraph(doc,'九个调优任务中，',f'九个调优任务中，{dcheck["task_positive_regret_optimistic_tie"]} 个任务即使采用最有利的 Free 并列选择也有正 regret，{dcheck["task_positive_regret_pessimistic_tie"]} 个在至少一种 Free 并列选择下有正 regret。最大的观察上界出现在 {maxreg["task"]}，为 {float(maxreg["regret_max"]):.2f} Gap points；其 Free 领先者为 {names(maxreg["free_leaders"])}，Tight 领先者为 {names(maxreg["tight_leaders"])}。逐任务表保留完整候选集合与并列区间。')
    dimi={r['dimension']:r for r in dims}
    doc=replace_paragraph(doc,'排名与损失幅度需要同时报告。',f'排名与损失幅度需要同时报告。NAS201、NAS101、ParamNet 三家族的 Free 选型 regret 上界分别为 {f(dimi["NAS201"]["regret_max"])}、{f(dimi["NAS101"]["regret_max"])}、{f(dimi["ParamNet"]["regret_max"])}。这有助于区分近似并列和有实质幅度的部署差异。regret 是同一批观测均分的回顾性比较，不是独立留出集上的选型泛化保证。[逐任务分数]({prefix}/display/hpo_task_scores.csv) · [并列与 regret]({prefix}/display/hpo_task_regret.csv)。')
    doc=replace_paragraph(doc,'本章从结构化 trajectory 出发，',f'本章全量覆盖 1,314 条 Search、702 条 Audit 和 486 条 HPO 单智能体轨迹。HPO 每预算由 160 条补至 162 条。动作和终止原因来自最终采用的实际运行；有真实控制流补跑时，行为表也切换到相应新原件。仅做离线评分的旧轨迹不虚构不同动作。最终答案的成功率、证据质量、配对和案例均按本评分版本重新计算。')
    doc=replace_paragraph(doc,'Free 下 336 次自主提交中，',f'Free 下 {sbi["cost_free"]["natural_stop"]} 次自主提交中，有 {sbi["cost_free"]["natural_stop_imperfect"]} 次 F1 未满分，其中 {sbi["cost_free"]["natural_stop_zero"]} 次为零分。即使没有反馈预算强制终止，模型仍可能在答案不完整或错误时提交；这一成功分类已经按新评分全量重算。Tight 的主要终止来源是预算先结束获取，两种终止不能合并解释。')
    doc=replace_paragraph(doc,'模型也没有统一的停止风格：',f'模型也没有统一的停止风格：GPT 在 Free 下 {smi["gpt-5.6-sol","cost_free"]["natural_stop"]}/73 次自主提交，平均获取 {f(smi["gpt-5.6-sol","cost_free"]["mean_unique_articles"])} 篇不同文章，F1 为 {float(smi["gpt-5.6-sol","cost_free"]["mean_score"])*100:.2f}；Gemini 为 {smi["gemini-3.8-flash-medium","cost_free"]["natural_stop"]}/73 次、{f(smi["gemini-3.8-flash-medium","cost_free"]["mean_unique_articles"])} 篇及 {float(smi["gemini-3.8-flash-medium","cost_free"]["mean_score"])*100:.2f}。这些是获取与停止风格的描述，不证明延长任一模型的轨迹都会带来同等收益。')
    doc=replace_paragraph(doc,'任务之间也不同。',f'任务之间也不同。全部 486 条已完成调优轨迹中，Free 的 162 条有 {hi["cost_free"]["cap_n"]} 条触及步数/评估上限，自主回答 {hi["cost_free"]["natural_n"]} 条；Moderate 自主回答为 {hi["cost_moderate"]["natural_n"]}/162，Tight 为 {hi["cost_tight"]["natural_n"]}/162。自然结束的调优轨迹在 Moderate/Tight 平均已使用 {float(hi["cost_moderate"]["natural_stop_budget_fraction_mean"])*100:.1f}%/{float(hi["cost_tight"]["natural_stop_budget_fraction_mean"])*100:.1f}% 的可见有效反馈预算。全部轨迹相应均值为 {float(hi["cost_moderate"]["delivered_budget_fraction_mean"])*100:.2f}%/{float(hi["cost_tight"]["delivered_budget_fraction_mean"])*100:.2f}%。预算利用率先按轨迹计算，再等权平均；Free 没有此分母。')
    totaldel=sum(int(r['delivered_total']) for r in hpo);repeated=sum(int(r['repeated_delivered_total']) for r in hpo)
    free=hi['cost_free']; late=int(free['observed_best_reached_by_first5_denom'])-int(free['observed_best_reached_by_first5_n'])
    doc=replace_paragraph(doc,'这一调优轨迹样本还反驳了',f'这批完整调优轨迹中，{totaldel:,} 次可见有效配置评估只有 {repeated} 次重复。Free 的 {free["observed_best_reached_by_first5_denom"]} 条有可见有效性能的轨迹中，{late} 条的最佳已观察配置在第五次评估之后才首次出现；在全部 {free["observed_best_reached_by_first5_denom"]} 条有可见性能的 Free 轨迹中，第五次之后的原始性能增益中位数为 {float(free["best_performance_gain_after_first5_median"])*100:.2f} 个百分点。发现得晚不等于改善很大；观察序列也不能直接证明增加预算的因果收益。最终评分同时可能采用历史最佳已评估配置回退，因此不能将有分数等同于模型自主提交了有效配置。[完整评估事件与行为表](../protocol-repair-20260918/hpo_behavior/README.zh.md)。')
    deliverytable=table(['DeepSeek 调优：九任务 × 三重复','Free','Moderate','Tight'],[['可评分最终结果',*[di[b]['score_complete_task_repeats']+'/27' for b in BUDGETS]],['可评分重复的平均 Gap',*[f(di[b]['conditional_strict_gap_repeat_equal']) for b in BUDGETS]],['全部 27 个槽位的 Gap0',*[f(di[b]['gap0_all_task_repeats']) for b in BUDGETS]]])
    doc=replace_table(doc,'| DeepSeek 调优：',deliverytable)
    doc=replace_paragraph(doc,'这里 `Gap0 =',f'这里 `Gap0 = 可评分比例 × 可评分重复的平均 Gap`。条件均值的样本组成随预算变化，不能作为独立能力比较。两端均可评分的 {both["pairs"]} 对中，平均 Gap 从 {f(both["free_gap0_mean_in_group"])} 变为 {f(both["tight_gap0_mean_in_group"])}。因此应将最终交付率和已可评分配置的质量分开报告。[三预算分解]({prefix}/cases/deepseek_delivery.csv) · [全部配对与贡献]({prefix}/cases/deepseek_delivery_transitions.csv)。')
    abody=table(['六模型等权均值','Free','Moderate','Tight'],[[label,*[f(float(ai[b][field])*100) for b in BUDGETS]] for label,field in [('标签准确率 LA','label_acc'),('证据集合准确率 EA','evidence_acc'),('标签与证据同时正确','joint_acc')]])
    subset={(r['budget'],r['gold_subset']):r for r in ac if r['model']=='ALL'}
    af,at=ai['cost_free'],ai['cost_tight']; cf,ct=subset['cost_free','nonempty'],subset['cost_tight','nonempty']
    confirmed=sum(int(r['free_exact_feedback_seen']) for r in patterns)
    pattern_doc=len({r['doc_index'] for r in patterns});pattern_models=len({r['model'] for r in patterns})
    qwen_case_text=('Qwen 文档 10、顺序 1、nda-13 的固定案例仍满足完整配对条件：Free 先引用第三方来源子条款，再在不完整反馈后补充上位例外条款；Tight 只提交部分证据。' if current_case_population.get('qwen_frozen_case_still_qualifies') else 'Qwen 文档 10、顺序 1、nda-13 的历史固定案例已按当前采用轨迹重新核对；其新旧答案和筛选状态见案例核验，不能继续把历史案例自动算作当前合格配对。')
    sec=f'''### 3.3 标签仍然正确时，证据可能已经退化

全部 702 条审计轨迹重新提取终答后，逐假设重算标签正确、证据集合精确及两者联合正确。EA 不要求标签正确，不能直接当作联合正确率。

{abody}

Free→Tight 的 LA 下降 {(float(af['label_acc'])-float(at['label_acc']))*100:.2f} 个百分点，EA 下降 {(float(af['evidence_acc'])-float(at['evidence_acc']))*100:.2f}，联合正确率下降 {(float(af['joint_acc'])-float(at['joint_acc']))*100:.2f}。终答修复及必要控制运行改变了旧稿的具体差距，应使用这里的完整新结果，不再引用旧诊断或旧解析下的数字。

仅看标准证据非空的假设并维持文档等权，LA 从 {float(af['nonempty_label_correct'])*100:.2f}% 到 {float(at['nonempty_label_correct'])*100:.2f}%，EA 从 {float(af['nonempty_evidence_exact'])*100:.2f}% 到 {float(at['nonempty_evidence_exact'])*100:.2f}%，联合正确率从 {float(af['nonempty_joint_correct'])*100:.2f}% 到 {float(at['nonempty_joint_correct'])*100:.2f}%。另按标签正确的假设呈现次数合并计数，证据不完全正确的比例为 Free {cf['label_correct_wrong_evidence']}/{cf['label_correct']}（{int(cf['label_correct_wrong_evidence'])/int(cf['label_correct'])*100:.1f}%）、Tight {ct['label_correct_wrong_evidence']}/{ct['label_correct']}（{int(ct['label_correct_wrong_evidence'])/int(ct['label_correct'])*100:.1f}%）。该合并条件比例不同于文档宏均值，不把重复顺序当独立任务。

需要非空证据的假设中，至少漏掉一个标准片段的比例从 {float(af['nonempty_missing_any'])*100:.2f}% 变为 {float(at['nonempty_missing_any'])*100:.2f}%；加入多余片段从 {float(af['nonempty_extra_any'])*100:.2f}% 变为 {float(at['nonempty_extra_any'])*100:.2f}%。两类错误可以同时出现，不能相加为总错误率。

严格“反馈补全”配对要求：Free 首次可见提案缺证据并收到不完整反馈，最后标签与证据均正确；Tight 标签正确，却提交与 Free 首次提案相同的部分集合，且未获得该假设的可见反馈。全量新评分下匹配到 {len(patterns)} 个假设呈现，覆盖 {pattern_models} 个模型、{pattern_doc}/13 份文档；其中 {confirmed} 个在 Free 下实际获得完整集合的正确确认。这些独立生成的 Free/Tight 配对不是同一随机轨迹的截断实验，不能推断额外一次反馈一定修复 Tight 错误。

{qwen_case_text} 案例的新旧终答、筛选条件与总体匹配数均重新核对，不能仅因旧稿已经选中就跳过复核。[配对与案例核验]({prefix}/audit/README.zh.md)。

审计反馈验证所提交证据集合，不直接提供正确标签。历史单智能体提示包含固定示例，可能影响查询对象；本次未改提示或调度。`verification_eff` 保留历史定义：在终答标签与证据均正确的假设中，曾向工具提交该正确证据集合的比例，包含返回因预算被隐藏的尝试。`visible_verification_eff` 使用相同分母，只计模型实际收到的正确核验，不混改旧字段含义。'''
    doc=replace_section(doc,'### 3.3 标签仍然正确时，','### 3.4 可检验的后续问题',sec)
    pt=table(['模型','预算','Search F1-MV：Δnaive / Δcached','Audit EA-MV：Δnaive / Δcached','NAS Gap0-MI：Δnaive / Δcached'],[[NAMES[m],b.removeprefix('cost_').title(),*[' / '.join(f'{float(pi[m,s,b]["delta_vs_"+base]):+.2f}' for base in ['naive','cached']) for s in ['restricted_search','evidence_audit','tuning']]] for m in MODELS for b in BUDGETS[1:]])
    doc=replace_table(doc,'| 模型 | 预算 | Search F1-MV：',pt)
    doc=replace_paragraph(doc,'在 36 个三策略均完整的组合中，',f'在 {findings["poolact"]["all"]["complete"]} 个三策略均完整的组合中，POOLACT 在 {win} 个高于两种基线；Tight 为 {twin}/{findings["poolact"]["tight"]["complete"]}。正差、负差均保留；HPO 恢复为历史运行版本，须与[回退范围和来源版本]({prefix}/README.zh.md)一起解释。')
    st,sm=psi['restricted_search','cost_tight'],psi['restricted_search','cost_moderate']
    doc=replace_paragraph(doc,'**搜索的收益主要出现在更紧的预算下。**',f'**搜索的收益随预算变化。** Tight 六模型 F1-MV 均值依次为 naive {f(st["naive_model_macro"])}、cached {f(st["cached_model_macro"])}、POOLACT {f(st["poolact_model_macro"])}；对 naive 的提升中位数为 {search_med:.2f} 个百分点、相对提升中位数为 {search_rel:.1f}%，{st["positive_vs_naive"]}/6 个模型为正。Moderate 均值从 naive {f(sm["naive_model_macro"])} 变为 POOLACT {f(sm["poolact_model_macro"])}，差值 {float(sm["mean_delta_vs_naive"]):+.2f} 个百分点。这是同一六模型的描述性比较，不作为预算交互效应的显著性检验。')
    am,atp=psi['evidence_audit','cost_moderate'],psi['evidence_audit','cost_tight']
    la_gain=lambda b:mean(float(r['delta_vs_naive']) for r in pa if r['scenario']=='evidence_audit' and r['regime']==b and r['metric']=='label_acc_mv')
    doc=replace_paragraph(doc,'**审计的收益最一致，而且主要体现为证据质量。**',f'**审计的证据收益保持广泛，但幅度需要更新。** {audit_both}/12 个模型—预算组合高于两种基线。Moderate EA-MV 对 naive/cached 的模型平均增益为 {f(am["mean_delta_vs_naive"])}/{f(am["mean_delta_vs_cached"])} 个百分点；Tight 为 {f(atp["mean_delta_vs_naive"])}/{f(atp["mean_delta_vs_cached"])}。LA-MV 对 naive 的对应增益为 {la_gain("cost_moderate"):.2f}/{la_gain("cost_tight"):.2f}。本段使用恢复后的历史 N4 成绩，三个策略同时恢复，不按分数选择版本。')
    ht=psi['tuning','cost_tight']
    doc=replace_paragraph(doc,'**调优的收益在 Tight 下更大。**',f'**调优使用恢复后的历史三策略结果。** 当前采用表的 Tight Gap0-MI 均值为 naive {f(ht["naive_model_macro"])}、cached {f(ht["cached_model_macro"])}、POOLACT {f(ht["poolact_model_macro"])}，高于两基线的模型数为 {ht["positive_vs_stronger_baseline"]}/6。{adoption_note} 本版不采用修复图版本的实际对照；历史运行、离线重评分与补跑三层仍单独留存。[全部端点与增益]({prefix}/poolact/poolact_all_metrics.csv)。')
    # N4 acquisition and vote EA both use the restored historical layer.
    coord_macro=lambda b,s,k:mean(float(r[k]) for r in coords if r['regime']==b and r['strategy']==s)
    cb=[]
    for b,label in [('cost_moderate','Moderate'),('cost_tight','Tight')]:
        cb.extend([[label+'：每池可见工具反馈数',*[f(coord_macro(b,s,'mean_feedback_visible')) for s in STRATEGIES]],
                   [label+'：获得反馈的不同假设数',*[f(coord_macro(b,s,'mean_visible_hypotheses')) for s in STRATEGIES]],
                   [label+'：最终投票 EA（%）',*[f(psi['evidence_audit',b][s+'_model_macro']) for s in STRATEGIES]]])
    doc=replace_table(doc,'| 六模型审计池均值 |',table(['六模型审计池均值','naive','cached','POOLACT'],cb))
    coord_lookup={(r['model'],r['regime'],r['strategy']):r for r in coords}
    coverage_wins={base:sum(float(coord_lookup[m,b,'poolact']['mean_visible_hypotheses'])>float(coord_lookup[m,b,base]['mean_visible_hypotheses']) for m in MODELS for b in BUDGETS[1:]) for base in ['naive','cached']}
    doc=replace_paragraph(doc,'Moderate 下，POOLACT 在较少的直接反馈调用下',f'将每池可见调用与假设覆盖分开后，POOLACT 的覆盖在 {coverage_wins["cached"]}/12 个模型—预算组高于 cached，在 {coverage_wins["naive"]}/12 组高于 naive。表中调用数来自最终采用成员实际看到的工具回复，图内共享内容不重复记作新工具获取，也不等同于计算或金钱开销。覆盖与分数的共同变化可以支持获取分配的描述，仍不能独立识别哪一种共享机制造成了改进。')
    if not (coord_macro('cost_moderate','poolact','mean_feedback_visible')<coord_macro('cost_moderate','naive','mean_feedback_visible') and coord_macro('cost_moderate','poolact','mean_visible_hypotheses')>coord_macro('cost_moderate','naive','mean_visible_hypotheses')):
        doc=doc.replace('### 4.2 更广的验证覆盖，而不是简单增加调用','### 4.2 验证覆盖、调用与共享的关系')
    # Explicitly avoid silently inheriting the old fixed example score triplet.
    case_scalars=read(args.main/'slot_scalars.csv')
    kc={r['strategy']:json.loads(r['metrics_json'])['evidence_acc_mv']*100 for r in case_scalars if r['system']=='poolact' and r['scenario']=='evidence_audit' and r['model']=='kimi-k3' and r['regime']=='cost_moderate' and r['item'].endswith(':3')}
    assert set(kc)==set(STRATEGIES)
    kp={r['strategy']:r for r in coord_pools if r['model']=='kimi-k3' and r['regime']=='cost_moderate' and r['question_index']=='3'}
    assert set(kp)==set(STRATEGIES)
    call_text='、'.join(kp[s]['feedback_visible'] for s in STRATEGIES)
    cover_text='、'.join(kp[s]['visible_hypotheses'] for s in STRATEGIES)
    sharing_text=('该固定案例在新版本仍满足共享证据筛选条件：一名成员实际验证了证据，另一名未直接查询该假设的成员收到共享验证消息并提交相同证据。' if current_case_population.get('kimi_frozen_case_still_qualifies') else '该固定案例是否仍满足共享证据机制筛选条件已单独核验；不把旧运行中的共享消息自动归给新采用轨迹。')
    doc=replace_paragraph(doc,'Kimi 的一个 Moderate 审计池展示了',f'Kimi 的 Moderate 审计文档 3 保留作固定对照：naive、cached、POOLACT 分别用 {call_text} 次可见反馈覆盖 {cover_text} 个假设，本版采用的历史投票 EA 依次为 {kc["naive"]:.2f}%、{kc["cached"]:.2f}%、{kc["poolact"]:.2f}%。{sharing_text} 该案例不证明共享消息是唯一答案来源。[池级案例复核]({prefix}/audit/README.zh.md)。')
    bvals={s:bi['cost_tight',s] for s in STRATEGIES}
    bon_gain=float(bvals['poolact']['gap0_bon'])-float(bvals['naive']['gap0_bon'])
    mi_gain=float(bvals['poolact']['gap0_mi'])-float(bvals['naive']['gap0_mi'])
    spread_conclusion=('本版个体平均分的改善大于最佳成员端点的改善，与收益更广泛分布的解释相容；不意味着每个池、每个成员都改善。' if mi_gain>0 and mi_gain>bon_gain else '本版不支持沿用“个体平均分改善大于最佳成员端点”的旧概括，应按这两个端点分别解释。')
    doc=replace_paragraph(doc,'调优的两个端点提供了一个补充视角：',f'调优的两个端点提供了一个补充视角：当前采用表中 Tight 的 POOLACT−naive 个体均分差为 {mi_gain:.2f} points，事后四成员最高分差为 {bon_gain:.2f}。BoN−MI 差距在 naive、cached、POOLACT 中依次为 {f(bvals["naive"]["bon_minus_mi"])}/{f(bvals["cached"]["bon_minus_mi"])} / {f(bvals["poolact"]["bon_minus_mi"])}。{spread_conclusion}')
    if not (mi_gain>0 and mi_gain>bon_gain):
        doc=doc.replace('### 4.3 协调不只是制造一条更幸运的轨迹','### 4.3 区分个体均值与最佳成员')
    # All live references move to new versioned tables; preserved sources stay explicit.
    links={'../gemini-openrouter-20260917/main/':prefix+'/main/','gemini-update-20260918/':prefix+'/display/','cases/CASE_INDEX.zh.md':prefix+'/cases/CASE_INDEX.zh.md','cases/deepseek_delivery.csv':prefix+'/cases/deepseek_delivery.csv'}
    for a,b in links.items():
        doc=doc.replace(']('+a,']('+b)
    # Add score-vs-submission distinction explicitly, avoiding the old fallback conflation.
    scorecount=sum(int(r['score_complete_n']) for r in hpo)
    fallback=sum(int(r['fallback_scored_n']) for r in hpo)
    parsed=sum(int(r['submitted_json_object_scored_n']) for r in hpo)
    insert=f'全部 486 条 HPO 中，按现行协议可评分（含回退）{scorecount}/486；其中 {fallback} 条包含最佳已观察配置回退。排除回退后，终答为 JSON 对象且已评分为 {parsed}/486（{parsed/486*100:.2f}%）。JSON 可解析不保证任务语义有效，也不能把回退算作模型提交。新 CSV 同时提供尝试数、可见有效评估数、全部原始终止原因、预算利用率与这几种最终交付口径。'
    insert+='\n\n'+table(['完整 HPO 行为（每预算 162 条）','Free','Moderate','Tight'],[
        ['评估尝试总数',*[hi[b]['attempted_evaluations_total'] for b in BUDGETS]],
        ['可见有效评估均值',*[f(hi[b]['delivered_evaluations_mean']) for b in BUDGETS]],
        ['预算终止 / 上限终止',*[hi[b]['budget_n']+' / '+hi[b]['cap_n'] for b in BUDGETS]],
        ['严格有分数（含回退）',*[hi[b]['score_complete_n']+'/162' for b in BUDGETS]],
        ['已提交 JSON 对象且评分（排除回退）',*[hi[b]['submitted_json_object_scored_n']+'/162' for b in BUDGETS]]])
    doc=doc.replace('获取与最终交付还需要进一步区分。',insert+'\n\n获取与最终交付还需要进一步区分。',1)
    # Old selected examples are retained as fixed illustrations, their new scores must be checked.
    qcase=[r for r in read(args.secondary/'search/trajectory_metrics.csv') if r['model']=='qwen3.8-2.4t-a95b-fp8' and r['source']=='phantom_seed2' and r['question_id']=='31']
    qvals={r['regime']:float(r['score']) for r in qcase}
    assert len(qvals)==3
    doc=replace_paragraph(doc,'一个具体例子是 Qwen 的一条 Free 搜索轨迹：',f'一个固定保留的例子是 Qwen 的 phantom_seed2 第 31 题 Free 轨迹：前四次不同查询连续返回同一人物文章，全程 16 次可见反馈仅覆盖 11 篇不同文章。新评分 Free F1={qvals["cost_free"]:.4f}、Tight F1={qvals["cost_tight"]:.4f}。这说明查询多样性不等于信息增量；案例不替代全量获取统计，也不用于证明预算导致退化。[重算后的代表案例索引]({prefix}/search/representative_case_index.csv)。')
    limitations='本次保留的解释限制包括：Audit 固定首步示例未改；不同模型思考强度、输出上限、提供方和实际计算资源并不完全相同；等反馈预算不等于等 token、等金钱或等墙钟时间。N4 恢复的历史结果包含原来的图路径、解析、投票和提供方差异。此前的诊断、修复候选和实际对照完整留档；本版 N4 使用既有运行，其执行版本与提供方差异按来源表记录。'
    count_note=f'当前 N1 保持 7776f70 的全部 2,502 个槽位；N4 的全部 2,196 个槽位恢复到含 Gemini 补齐的 297c3d0 分数与来源。7776f70 的全量旧轨迹重评分诊断曾记录 {legacy_any} 个任一指标变化、{legacy_endpoint} 个任务端点变化和 {legacy_primary} 个论文主指标变化；这些是保留的历史诊断计数，不是本版 N4 采用新评分的计数。本次回退相对于 7776f70 的逐样本变化另列。'
    code_note=f'当前仓库代码回退版本为 `{core_commit}`，该提交不代表重新执行旧轨迹。N1 保留 7776f70 的评分与实际运行来源。N4 恢复修复前的解析、投票、图代码及完整三策略成绩；历史执行版本仍以逐槽来源记录为准。当前入口的代码回退清单与验证见新交付，不把旧运行标为以本次回退提交重新执行。'
    doc+='\n## 6. 评分版本、结论变化与复算\n\n'+count_note+'\n\n'+code_note+'\n\n'+limitations+f'\n\n[相对原 297c3d0 的结论对照]({prefix}/conclusion_delta.csv)与[相对回退前 7776f70 的逐样本变化]({prefix}/selection/sample_rollback.csv)分别留存。当前采用由独立回退选择清单验证，不复用 97 池修复补跑完成闸门。公开脚本可从两个冻结版本完整重建选择、聚合、行为连接和报告。\n'
    # Every highlighted interpretation has a named old/new comparison and evidence.
    delta=[]
    def add(name,old,new,evidence,unit=''):
        try: unchanged=math.isclose(float(old),float(new),rel_tol=0,abs_tol=1e-9)
        except (ValueError,TypeError):unchanged=old==new
        delta.append(dict(conclusion=name,historical=old,new=new,unit=unit,status='保持' if unchanged else '修改',evidence=evidence,old_identity='published-297c3d0-historical-scoring',new_identity=version['new']['identity']))
    for r in read(args.main/'conclusion_changes.csv'):
        add(r['conclusion'],r['historical'],r['new'],'main/FINDINGS.json')
    add('Existing-trace rescore: slots with any metric change',0,legacy_any,'../protocol-repair-20260918/rescore/main/sample_diff.csv','slots; any MI/MV or endpoint metric')
    add('Existing-trace rescore: task endpoints changed',0,legacy_endpoint,'../protocol-repair-20260918/rescore/main/sample_diff.csv','slots; Audit LA or EA')
    add('Existing-trace rescore: paper-primary endpoints changed',0,legacy_primary,'../protocol-repair-20260918/rescore/main/sample_diff.csv','slots; Audit EA only')
    old_display=prior/'gemini-update-20260918'
    olddims={r['dimension']:r for r in read(old_display/'dimension_selection.csv')}
    old_leader_changes=sum(r['leader_set_changed']=='True' for r in olddims.values())
    add('Dimension Free-to-Tight leader-set changes',old_leader_changes,leaders,'display/dimension_selection.csv','dimensions')
    for row in dims:
        for field in ['regret_min','regret_max']:
            add(row['dimension']+' selection '+field,olddims[row['dimension']][field],row[field],'display/dimension_selection.csv','reported points')
    oldregret={r['task']:r for r in read(old_display/'hpo_task_regret.csv')}
    add('HPO maximum task-level regret',max(float(r['regret_max']) for r in oldregret.values()),float(maxreg['regret_max']),'display/hpo_task_regret.csv','Gap points')
    for row in regrets:
        for field in ['regret_min','regret_max']:
            add(row['task']+' '+field,oldregret[row['task']][field],row[field],'display/hpo_task_regret.csv','Gap points')
    oldprimary={(r['model'],r['scenario'],r['regime']):r for r in read(old_display/'poolact_primary.csv')}
    for row in p1:
        key=row['model'],row['scenario'],row['regime']
        for base in ['naive','cached']:
            add('POOLACT '+':'.join(key)+' gain over '+base,oldprimary[key]['poolact_minus_'+base],row['delta_vs_'+base],'poolact/poolact_primary.csv','pp or Gap points')
    oldmacro={(r['scenario'],r['regime']):r for r in read(old_display/'poolact_scenario_summary.csv')}
    for row in ps:
        key=row['scenario'],row['regime']
        for base in ['naive','cached']:
            add('POOLACT model-macro '+':'.join(key)+' gain over '+base,oldmacro[key]['poolact_minus_'+base],row['mean_delta_vs_'+base],'poolact/poolact_scenario_summary.csv','pp or Gap points')
        oldwins=sum(float(r['poolact_minus_naive'])>0 and float(r['poolact_minus_cached'])>0 for r in oldprimary.values() if (r['scenario'],r['regime'])==key)
        add('POOLACT '+':'.join(key)+' models above both',oldwins,row['positive_vs_stronger_baseline'],'poolact/poolact_scenario_summary.csv','models')
    oldbon={r['strategy']:r for r in read(old_display/'nas_best_minus_mean.csv') if r['regime']=='cost_tight'}
    old_mi_gain=float(oldbon['poolact']['gap_mi'])-float(oldbon['naive']['gap_mi'])
    old_bon_gain=float(oldbon['poolact']['gap_bon'])-float(oldbon['naive']['gap_bon'])
    add('HPO Tight MI improvement exceeds BoN improvement',old_mi_gain>old_bon_gain and old_mi_gain>0,mi_gain>bon_gain and mi_gain>0,'display/nas_best_minus_mean.csv','boolean')
    add('HPO Tight BoN model-macro PoolAct minus naive',old_bon_gain,bon_gain,'display/nas_best_minus_mean.csv','Gap0 points')
    oldab={r['budget']:r for r in read(prior/'audit/budget_metrics.csv')}
    for b in BUDGETS:
        for metric in ['label_acc','evidence_acc','joint_acc','nonempty_label_correct','nonempty_evidence_exact','nonempty_joint_correct','nonempty_missing_any','nonempty_extra_any']:
            add('Audit '+b+' '+metric,float(oldab[b][metric])*100,float(ai[b][metric])*100,'audit/n1/budget_metrics.csv','0-100')
    oldpatterns=read(prior/'audit/paired_completion_patterns.csv')
    add('Audit paired completion patterns',len(oldpatterns),len(patterns),'audit/n1/paired_completion_patterns.csv','presentations')
    add('Audit paired confirmed complete evidence',sum(int(r['free_exact_feedback_seen']) for r in oldpatterns),confirmed,'audit/n1/paired_completion_patterns.csv','presentations')
    add('HPO behavioral trajectories',480,sum(int(r['n']) for r in hpo),'../protocol-repair-20260918/hpo_behavior/official_rescored486/by_regime.csv','trajectories')
    oldh={r['regime']:r for r in read(prior/'hpo/by_regime.csv')}
    for b in BUDGETS:
        for field in ['n','delivered_total','natural_n','budget_n','cap_n','delivered_evaluations_mean','delivered_budget_fraction_mean','score_complete_n']:
            add('HPO '+b+' '+field,oldh[b][field],hi[b][field],'../protocol-repair-20260918/hpo_behavior/official_rescored486/by_regime.csv')
    oldsp=next(r for r in read(prior/'search/paired_direction_summary.csv') if r['model']=='ALL')
    for field in ['tight_lower','tied','tight_higher']:
        add('Search paired '+field,oldsp[field],sp[field],'search/paired_direction_summary.csv')
    for b in BUDGETS:
        oldrow=next(r for r in read(prior/'search/overall_regime.csv') if r['regime']==b)
        for field in ['natural_stop_imperfect','natural_stop_zero']:
            add('Search '+b+' '+field,oldrow[field],sbi[b][field],'search/overall_regime.csv')
    with (args.output/'conclusion_delta.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,list(delta[0]),lineterminator='\n');writer.writeheader();writer.writerows(delta)
    delta_lookup={r['conclusion']:r for r in delta}
    summary_specs=[
        ('Search Free→Tight 下降模型数（/6）',['N1 restricted_search Free-to-Tight declined models'],0),
        ('Audit EA Free→Tight 下降模型数（/6）',['N1 evidence_audit Free-to-Tight declined models'],0),
        ('Free/Tight 领先集合变化（/7）',['Dimension Free-to-Tight leader-set changes'],0),
        ('HPO 最大逐任务 regret（Gap points）',['HPO maximum task-level regret'],2),
        ('POOLACT 高于两基线：全部 / Tight',['POOLACT all above both baselines','POOLACT tight above both baselines'],0),
        ('HPO Tight POOLACT−naive 均值增益',['POOLACT model-macro tuning:cost_tight gain over naive'],2),
        ('Audit 非空证据 LA：Free / Tight（%）',['Audit cost_free nonempty_label_correct','Audit cost_tight nonempty_label_correct'],2),
        ('Audit 补全配对 / 实际确认完整证据',['Audit paired completion patterns','Audit paired confirmed complete evidence'],0),
        ('HPO 行为轨迹数',['HPO behavioral trajectories'],0),
    ]
    summary_rows=[]
    for label,keys,digits in summary_specs:
        chosen=[delta_lookup[key] for key in keys]
        summary_rows.append([label,' / '.join(f(r['historical'],digits) for r in chosen),' / '.join(f(r['new'],digits) for r in chosen),'保持' if all(r['status']=='保持' for r in chosen) else '修改'])
    doc+='\n主要结论与支撑数值按最终采用结果逐项比较；“保持”只针对该行的定义与数值，不代表所有单样本、所有排名都未变化。\n\n'+table(['项目','原 297c3d0 报告','本版','结论处理'],summary_rows)+'\n\nAudit 非空证据标签准确率应报告上述实际差距，不再沿用“基本不变”的旧概括；同时保留其与证据集合准确率的不同变化幅度。HPO 的行为分母、最终可评分比例与真实提交配置分列，论文表格应使用本版全部行为 CSV。具体模型排名、每个预算的正负增益和固定案例资格见完整结论对照。\n'
    previous_findings=json.loads((args.repo/'results/protocol-repair-20260918/main/FINDINGS.json').read_text())
    prior_primary=read(args.repo/'results/protocol-repair-20260918/poolact/poolact_primary.csv')
    previous_hpo_tight=sum(float(r['delta_vs_stronger_baseline'])>0 for r in prior_primary if r['scenario']=='tuning' and r['regime']=='cost_tight')
    current_hpo_tight=sum(float(r['delta_vs_stronger_baseline'])>0 for r in p1 if r['scenario']=='tuning' and r['regime']=='cost_tight')
    doc+='\n本次回退相对上一正式版 7776f70 的主要变化如下；N1 主成绩、排名和 regret 逐项保持。\n\n'+table(['POOLACT 高于两基线','回退前 7776f70','当前恢复版'],[
        ['全部模型—场景—预算（/36）',previous_findings['poolact']['all']['poolact_above_both'],win],
        ['Tight（/18）',previous_findings['poolact']['tight']['poolact_above_both'],twin],
        ['HPO Tight（/6）',previous_hpo_tight,current_hpo_tight]])+'\n'
    (args.output/'README.zh.md').write_text(doc)
    # Companion appendix is a complete current methods/data guide, not an erratum.
    appendix=f'''# 数据、定义与完整证据

[论文式正文](README.zh.md) · [英文摘要](ABSTRACT.en.md)

## A. 数据范围与评分版本

本页对应{state}。{code_note} 主实验 4,698 个固定槽位全部重新聚合，其中 N1 保留 7776f70 修复评分，N4 完整恢复 297c3d0 历史评分。历史分数、早期诊断、已撤回采用的修复分数与本次回退选择分别留存；本次没有重新评分旧 N4 来替代其历史成绩。{count_note} Gemini 783 项包含历史 Sub2 与 OpenRouter，提供方差异不能被视作已隔离的因果变量。

{adoption_note}

| 材料 | 入口 |
| --- | --- |
| 全部采用槽位与原件 SHA | [SOURCE_SELECTION.csv]({prefix}/main/SOURCE_SELECTION.csv) |
| 旧轨迹重新评分的逐样本分数、原因 | [离线重评分对照](../protocol-repair-20260918/rescore/main/sample_diff.csv) |
| 回退前→当前采用来源、分数及原因 | [4,698 行回退对照]({prefix}/selection/sample_rollback.csv) |
| 全部绝对值、重复层、宽比较 | [absolute]({prefix}/main/absolute_settings.csv)、[by_repeat]({prefix}/main/by_repeat.csv)、[COMPARISON]({prefix}/main/COMPARISON.csv) |
| 新旧聚合差与排名变化 | [聚合对照]({prefix}/main/all_aggregate_comparisons.csv)、[排名对照]({prefix}/main/ranking_changes.csv) |
| 旧/诊断/新身份与输入 | [评分身份]({prefix}/main/SCORE_VERSIONS.json)、[输入]({prefix}/main/INPUTS.json) |
| 结论与证据 | [conclusion_delta.csv]({prefix}/conclusion_delta.csv) |

## B. EXPGYM、排名与 regret

N1 Search 为 73 题（whois 39、whatis 34），每题每预算一次；Audit 为 13 文档、三种固定假设顺序；HPO 为九任务各三重复。均值先平均任务内重复，再对任务等权。`expected_units` 是对应表的评分单元，未必等于任务数，例如 HPO 27 是九任务乘三重复。Audit 的顺序和假设不作为独立任务。

Free 不限制反馈成本，但有步数上限。Moderate/Tight 使用基准成本的 10/3 倍；Search/Audit 基准为 300 秒，HPO 使用冻结任务参考成本。预算单位是模拟反馈成本，不是墙钟时间。达到或超过预算边界的结果计费但未向模型提供，不能计作已获取信息。

Gap/Gap0 越高越好；Gap0 只对已完成、正常无配置的终态使用零效用，不把失败或未完成补零。历史最佳已评估配置回退仍单独标注。新终答接受规则不修补答案内容、不查询 gold 选择最有利候选，也不改变历史工具行动。

排名使用相同六模型集合，Free 并列全部保留，绝对容差 1e-9。regret 是同任务 Tight 最优分减去 Free 选中模型的 Tight 分；并列保留区间，无独立选型/部署留出集。

{table(['HPO 任务','Free 领先者','Tight 领先者','regret 最小 / 最大'],[[r['task'],names(r['free_leaders']),names(r['tight_leaders']),f(r['regret_min'])+' / '+f(r['regret_max'])] for r in regrets])}

[七维度完整排名]({prefix}/main/dimension_rankings.csv) · [选型表]({prefix}/display/dimension_selection.csv) · [九任务分数]({prefix}/display/hpo_task_scores.csv) · [regret]({prefix}/display/hpo_task_regret.csv)。

## C. 获取、停止与最终交付

行为分析完整覆盖 Search 1,314、Audit 702、HPO 486 条 N1，共 2,502 条。HPO 各预算 162 条、Free/Tight 162 对。尝试、实际可见结果、可见有效数值评估和隐藏越预算结果分列。不同查询不等于不同文章，HPO 配置按完整数值等价身份去重。停止类型来自真实日志，不用离线新解析重写动作历史。

HPO 严格有分数 {scorecount}/486，包含 {fallback} 条历史回退；排除回退且终答为已评分 JSON 对象 {parsed}/486。可解析、任务有效、严格有分数、正常 Gap0 端点是不同口径，不能合并成一个“最终答案成功率”。

[Search 全部轨迹]({prefix}/search/trajectory_metrics.csv) · [预算行为]({prefix}/search/overall_regime.csv) · [438 配对]({prefix}/search/free_tight_paired.csv) · [代表案例]({prefix}/search/representative_case_index.csv)。

[HPO 全部事件与定义](../protocol-repair-20260918/hpo_behavior/README.zh.md) · [全部 486 轨迹](../protocol-repair-20260918/hpo_behavior/official_rescored486/trajectories.csv) · [预算汇总](../protocol-repair-20260918/hpo_behavior/official_rescored486/by_regime.csv) · [原始终止原因](../protocol-repair-20260918/hpo_behavior/official_rescored486/termination_reasons.csv)。

DeepSeek 分解固定每预算 27 槽位，条件严格 Gap 使用可评分重复等权。可评分比例乘该条件均值等于全部槽位 Gap0。共同可评分的 {both['pairs']} 对不能替代含未交付项的完整端点。[交付分解]({prefix}/cases/deepseek_delivery.csv) · [27 配对]({prefix}/cases/deepseek_paired_delivery.csv) · [状态贡献]({prefix}/cases/deepseek_delivery_transitions.csv)。

## D. 答案、证据与配对案例

702 条 N1 保留修复后的终答接受与评分；1,872 个 N4 成员及 468 个池恢复历史解析、投票和评分。两层分别标注，不将其描述为统一的新接受规则，也不根据 gold 补造标签或证据。LA 与 EA 独立评分，联合正确率另列。缺失/多余证据按标准集合差计算，可能同时发生。总体及非空证据分层维持文档等权，合并条件分母另列，不混用宏均值和 pooled 比例。

“反馈补全”配对完整定义见正文，目前 {len(patterns)} 呈现、{confirmed} 次完整确认。历史固定案例保留为解释性样例，并重新核对新分数与候选规则；不是随机样本或最大增益选例。`verification_eff` 的分母为终答标签与证据均正确的假设，分子为其中曾向工具提交该正确证据集合的假设，包含预算隐藏返回；`visible_verification_eff` 使用相同分母，只计可见正确核验。

[Audit 方法/案例变化]({prefix}/audit/README.zh.md) · [假设级]({prefix}/audit/n1/hypothesis_metrics.csv) · [轨迹级]({prefix}/audit/n1/trace_metrics.csv) · [模型预算]({prefix}/audit/n1/model_budget_metrics.csv) · [条件分母]({prefix}/audit/n1/diagnostic_counts.csv) · [配对]({prefix}/audit/n1/paired_completion_patterns.csv)。

## E. POOLACT 与运行版本公平性

N4 三策略均为四智能体、匹配每成员反馈预算。Search 限 whois 39 题，Audit 13 文档，HPO NAS101 A/B/C 各三重复，仅 Moderate/Tight。主要端点分别为 F1-MV、EA-MV、Gap0-MI；BoN 是事后真实分最高的成员，不能当可部署选择器。

{table(['场景','预算','naive','cached','POOLACT'],[[r['scenario'],r['regime'],*[f(r[s+'_model_macro']) for s in STRATEGIES]] for r in ps])}

本版恢复全部历史 N4 来源，因此原图路径前缀标识、解析/投票规则、提供方和版本差异也随之保留。此前图审计、碰撞证据和 97 池修复补跑完整保存在 7776f70 历史交付中，不作为本版的正式 N4 来源。本版沿用既有三策略运行，执行版本按历史来源记录。

[历史 HPO 逐运行版本（810 项）](../protocol-repair-20260918/hpo_versions/hpo_all_slots.csv)与[历史模型—预算—策略版本矩阵（54 组）](../protocol-repair-20260918/hpo_versions/hpo_model_budget_strategy.csv)记录实际执行身份；当前全部 HPO 的来源哈希与该历史集合一致。旧 HPO 记录中 492 项未写 Git 提交号，保留空值并使用已核验源码树 SHA，不补造提交号。

[全部指标与两基线差]({prefix}/poolact/poolact_all_metrics.csv) · [主增益]({prefix}/poolact/poolact_primary.csv) · [宏均值]({prefix}/poolact/poolact_scenario_summary.csv) · [MI/BoN]({prefix}/display/nas_best_minus_mean.csv) · [Audit 池]({prefix}/audit/coordination/audit_pools.csv) · [Audit 成员]({prefix}/audit/coordination/audit_agents.csv)。

## F. 解释边界与复算

{limitations}

不报告 p 值，不将固定模型、重复顺序、共享题库或池成员当总体独立抽样。图/缓存/行动协调的各自因果贡献仍未由独立消融完全识别。

主聚合脚本从完整新版 slot scalars 重算 7,767 聚合行、126 排名和 1,298 宽比较，再生成展示、regret、配对及全部 POOLACT 指标。本次公开回退重建器从两个固定版本逐行选择：N1 采用 7776f70，N4 采用含 Gemini 补齐的 297c3d0；重新计算所有聚合、报告和对应 Audit 行为表。它不将撤回的 N4 新评分再次套用。7776f70 的最小评分包和完整重放器仍作为历史材料保留，其中 HPO 使用已核验性能证书，不默认读取完整 benchmark。上述公开重放不重新调用模型，也不等同于从完整原件重建最小包、逐次 HTTP 审查或再次验证全 turn 控制流。最后几项及可选完整 benchmark 复核仍需冻结本地归档与对应环境。

Whois 预算 sweep 单列 [完整预算分析与图](../protocol-repair-20260918/whois/README.zh.md)，不额外累加到上述 4,698 主实验分母。其 1,170 个预算—模型—题目结果全量重评分，其中 beta=10 的 234 项已属于主实验，来源与新评分逐项连接；其余 936 项为主分母之外的独立预算设置。旧轨迹离线重评分层的两处终答文本变化均未改变分数。{sweep_note}

[重建主分析]({prefix}/tools/rebuild_analysis.py) · [重建展示]({prefix}/tools/recompute_display.py) · [重建 Search/POOLACT/交付]({prefix}/tools/rebuild_secondary.py) · [生成本报告]({prefix}/tools/render_report.py) · [审阅记录](REVIEW.zh.md)。
'''
    (args.output/'APPENDIX.zh.md').write_text(appendix)
    en=f'''# Abstract

Large language model agents depend on external feedback to test hypotheses, retrieve information, and verify conclusions. EXPGYM studies how feedback budgets alter observed performance, model selection, and coordination across tuning, multi-hop search, and evidence audit. Under the retained single-agent scoring and restored historical four-agent results, tightening feedback from Free to Tight reduces search F1 for {findings['n1_budget']['restricted_search']['declined']} of six models and exact evidence-set accuracy for {findings['n1_budget']['evidence_audit']['declined']} of six. The highest observed model changes in {leaders} of seven evaluation dimensions. Free-based model selection can incur nontrivial Tight regret, reaching {float(maxreg['regret_max']):.2f} Gap points on {maxreg['task']}. Complete behavioral analysis covers 486 tuning, 1,314 search, and 702 audit trajectories and distinguishes attempted calls, visible feedback, stopping, submitted configurations, and fallback scores. For hypotheses requiring nonempty evidence, label accuracy changes from {float(af['nonempty_label_correct'])*100:.2f}% to {float(at['nonempty_label_correct'])*100:.2f}%, while exact evidence-set accuracy changes from {float(af['nonempty_evidence_exact'])*100:.2f}% to {float(at['nonempty_evidence_exact'])*100:.2f}%. With four agents and matched per-agent feedback budgets, POOLACT's median Tight-search gain over independent rollouts is {search_med:.2f} F1 percentage points; audit evidence accuracy exceeds both independent and cache-sharing baselines in {audit_both} of twelve model-budget settings. Audit trajectories associate these gains with broader verification coverage. These results are descriptive, preserve negative comparisons, and do not establish universal model superiority or isolate individual coordination mechanisms.

All 4,698 registered main-experiment slots are reaggregated. The 2,502 single-agent slots retain the 7776f70 scores and sources; all 2,196 four-agent slots restore the pre-repair scores and sources, including Gemini backfills and all three strategies. The withdrawn four-agent rescoring and runtime controls remain archived. The retained four-agent results follow the historical protocol; diagnostics and repaired candidates remain archived. Gemini combines historical Sub2 and OpenRouter backfills. Model/provider differences, thinking/output settings, physical scheduling, and the fixed Audit prompt example remain interpretation limits; matched feedback budgets do not imply matched computational expenditure.

[中文论文式报告](README.zh.md) · [Data, definitions, and scope](APPENDIX.zh.md)
'''
    (args.output/'ABSTRACT.en.md').write_text(en)
    manifest=dict(status='PASS',adoption_state=version['new']['adoption_state'],score_identity=version['new']['identity'],core_code_commit=core_commit,runtime_snapshot_commit=runtime_commit,auxiliary_runtime_snapshot_commits=auxiliary_runtime_commits,hpo_behavior_rows=sum(int(r['n']) for r in hpo),conclusion_rows=len(delta),changed_conclusions=sum(r['status']=='修改' for r in delta),existing_trace_change_counts=dict(any_metric_slots=legacy_any,task_endpoint_slots=legacy_endpoint,paper_primary_slots=legacy_primary),sources={role:hashlib.sha256(p.read_bytes()).hexdigest() for role,p in [('main/slot_scalars.csv',args.main/'slot_scalars.csv'),('display/n1_main.csv',args.display/'n1_main.csv'),('audit/n1/budget_metrics.csv',args.audit/'n1/budget_metrics.csv'),('../protocol-repair-20260918/hpo_behavior/official_rescored486/by_regime.csv',args.hpo/'by_regime.csv'),('template/README.pre-repair-297c3d0.zh.md',template),('../protocol-repair-20260918/rescore/main/sample_diff.csv',existing_rescore/'sample_diff.csv')]})
    (args.output/'RENDER_CHECKS.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(manifest,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
