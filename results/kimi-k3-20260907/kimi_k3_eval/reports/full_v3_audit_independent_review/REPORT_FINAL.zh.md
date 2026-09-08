# full_v3 Audit 最终独立复算：PASS

已在 resume 与正式双审计完成后，于 2026-09-07T11:57:07.386610+00:00 从当前 gold／raw final 独立复算，全部文件身份、LA／EA／verification_eff 及 PoolAct 重新投票结果一致；与正式 summary 的严格比较通过，无缺失、无不一致。这是离线检查，没有新增 API 调用，也没有修改冻结源码、数据或运行结果。

## 复核覆盖与证据

Audit 覆盖 78/78 jobs、117 ExpGym traces（13 docs × 3 regimes × 3 orders）、117 PoolAct results／468 agents（13 docs × 3 regimes × 3 strategies × N=4）。以每条最终答案对 17 个 gold hypotheses 计分，再按 doc／order 等权聚合；未从 summary 或已存的 aggregate 分数取数计算。

与最终 summary 比较 42 个宏指标、546 个 doc 指标、585 个 trace/agent 的 LA／EA／SHA、117 个 aggregate 记录、24 个论文预算子集指标（含描述性 MI）。其中 PoolAct 的 voted answer 先由 4 agents 独立重建，并与原始 aggregate.answer 逐字核对。最大数值差 1.4210854715202004e-14，仅浮点求均值顺序造成的舍入，低于 1e-10；文件 SHA 必须完全相同。

同期 HPO 独立复算亦通过：63 家族值、189 任务值、405 agent 记录、12 个论文 NAS101 A 值。相对旧 HPO 快照，405 个原始 trace/agent 和 81 个 result 的路径／SHA 以及全部任务／家族数值完全不变；manifest 随 resume 合法更新，已重新绑定新 SHA，没有放松一致性检查，也没有覆盖旧快照。

- [机器可查 PASS 回执](PASS_FINAL.json)
- [Audit 完整独立证据（逐 hypothesis／投票／路径／SHA）](independent_post_resume_final.json)
- [正式 summary](../full_v3_results_final/summary.json)、[正式结果审计](../full_v3_audit_final/audit.json)、[原始 dump 审计](../full_v3_dumps_final/raw_dump_audit.json)
- [HPO 最终比较说明](../full_v3_hpo_independent_review/POST_RESUME_FINAL.zh.md)

## ExpGym：全部 Audit 文档

| 预算 | LA (%) | EA (%) |
|---|---:|---:|
| free | 84.62 | 55.81 |
| moderate | 84.77 | 55.51 |
| tight | 83.41 | 54.15 |

## PoolAct：论文预算子集

各单元先逐文档投票再等权平均 13 docs，不是单 agent 平均。每格仅一组 N=4，未将 agents 当成额外独立 repetitions。

| 预算 | 策略 | 投票 LA (%) | 投票 EA (%) |
|---|---|---:|---:|
| moderate | naive | 83.26 | 52.49 |
| moderate | cached | 83.71 | 53.39 |
| moderate | poolact | 82.81 | 52.49 |
| tight | naive | 84.16 | 54.30 |
| tight | cached | 85.07 | 55.20 |
| tight | poolact | 82.81 | 53.85 |

free 为扩展矩阵，不是论文 PoolAct 主表：

| 策略 | 投票 LA (%) | 投票 EA (%) |
|---|---:|---:|
| naive | 83.71 | 52.04 |
| cached | 82.81 | 52.94 |
| poolact | 83.71 | 53.85 |

[ExpGym 宽表 CSV](expgym_final_wide.csv)、[PoolAct 全三预算宽表 CSV（含描述性 MI）](poolact_final_wide.csv)、[546 个 doc 指标 CSV](document_metrics_final.csv)、[585 个 trace/agent 指标 CSV](trace_metrics_final.csv)。完整精度在 CSV／JSON，展示表保留两位小数。

## 主要观察与不能混淆的含义

1. 全量 LA 为约 83%–85%，不是 smoke 单文档常见的约 94%。ExpGym moderate 的 LA 84.77 略高于 free 84.62，tight 为 83.41；EA 为 54.15–55.81。固定预算间小差异仅作描述，不声称单调关系或统计显著。
2. PoolAct 的 cached 在 moderate/tight 的投票 LA／EA 均为三策略最高；poolact 策略并非在 Audit 全部领先。tight 的 cached 为 85.07/55.20，poolact 为 82.81/53.85。未做额外策略重复或显著性检验。
3. LA 高于 EA 并不矛盾：正确选择标签不代表证据集合精确匹配。ExpGym 共 1989 个 hypothesis 实例中，608 个标签对但证据错；PoolAct 投票同样 1989 个实例中为 627 个。无需将这种任务错误记作执行失败。
4. EA 本身不要求标签正确。原始 ExpGym row 1/free/rep 0 的 nda-7，gold 为 Contradiction／[23]，模型为 Entailment／[23]：LA 错但 EA 对。所有 ExpGym 中共有 29 个此类实例，PoolAct 投票中为 27 个。若把 EA 乘上 label correctness，会错误降低正式指标。[原始示例](/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/full_v3/expgym/evidence_audit/1/cost_free/Kimi-K3_cost_free/traces-v2/evidence_audit_cc-large_1_r0_s1206.json)
5. 117 个 PoolAct result 共 1989 个 hypothesis 投票中，有 59 次标签平票、94 次证据平票。两级均按原 agent 顺序取首次出现者；证据只在获胜标签内部投整组集合，不按 span 逐项投。完整序列已留证据，未用 gold 打破平票。
6. 585 条 trace/agent 中，117 条 ExpGym 及 467 条 PoolAct final 可直接 JSON 解析；另 1 条 PoolAct final 是无效 JSON，按原 evaluator 真正得到 LA=EA=0，并非缺失填零。它是 row 7/free/naive/agent 0，原始评分与独立评分一致：[原始记录](/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/full_v3/poolact/evidence_audit/7/cost_free/naive/agents/agent_0.json)。投票时该答案不提供有效条目。

## 固定离线基线：不是 Kimi-K3 测量

对这 13 docs × 17 hypotheses，gold 标签分布为 NotMentioned 101、Entailment 101、Contradiction 19。事先固定“每项回答 NotMentioned，evidence_ids=[]”的常量策略，LA=101/221=45.701357%，EA 同为 45.701357%。

这里 LA=EA 仅因为该固定策略及本数据中空 gold 证据恰好对应 NotMentioned，不意味着通用 EA 是联合标签指标。NotMentioned 与 Entailment 数量相同；不能用“绝大多数都是 NotMentioned”解释约 84% LA，更不能将这 45.7% 作为 Kimi-K3 的测量。该策略不读文档、不调用模型／反馈，不计入正式矩阵，也不替代正式结果。[基线说明与逐 doc 数据](../audit_label_baseline/README.zh.md)

## 精确绑定

- Final manifest SHA256：`7016deb285696ff95c0aa970088c0580d0daf60cb0c6695ce8515e0fe85df854`
- Final summary SHA256：`36e5badbd2b5e95a6042dead41703dc44146222260af05a29acc13e7ecf6e083`
- Gold SHA256：`a81e3ecfc1d423f11289a1711ccd4d5cf3167f4d75576f5180bcc0b4c928fd23`
- Frozen source SHA256：`c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`

[复算方法／命令](USAGE.zh.md)、[冻结解析与投票细则](SEMANTICS.zh.md)。本报告不推算 token、GPU 时或真实墙钟，这些由正式 dump 与执行／Slurm 回执报告；Audit 模拟预算不是实际运行秒数。
