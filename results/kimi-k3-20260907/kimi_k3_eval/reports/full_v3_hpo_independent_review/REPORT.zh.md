# full_v3：HPO 分区独立复核

这是已完成 HPO 分区的只读独立检查，不宣称整个 full_v3 矩阵已完成，不是新一轮模型运行。证据快照：2026-09-07T11:20:05.125842+00:00。首次生成时尚无正式 full_v3 summary；后续核对需另存报告，不能将本快照当成已完成的全量验收。

## 覆盖与方法

54/54 个 HPO 子进程回执 completed、returncode=0；9 个任务 × 3 种预算，ExpGym 每任务 3 repeats，共 81 条；PoolAct 每任务 3 strategies × 4 agents，共 81 个 result、324 个 agent 文件。所有独立 agent 文件与 result 内嵌记录一致，分数有限，源码／配置标识一致，已记录的评分复核标记均通过。本文直接解析原始文件及 oracle，未调用正式 summarizer、benchmark 评分器或 LLM；因此它独立验证聚合与记录一致性，不替代最终审计中的 benchmark 重算。

Gap = max(0, (raw − oracle.mean) / (oracle.best − oracle.mean) × 100)，不上限截断。ExpGym 逐 trace 算 Gap，再 3 repeats 求任务均值，再 3 tasks 等权求家族均值。PoolAct BoN 为 4 个 raw 中最大值对应的 Gap，MI 为 4 个逐 agent 已截零 Gap 的均值，再作 3 tasks 家族均值。不能先平均 raw 再截零。

## ExpGym：家族 Gap（%）

| 预算 | ParamNet | NAS201 | NAS101 |
|---|---:|---:|---:|
| free | 79.91 | 85.64 | 82.02 |
| moderate | 71.45 | 88.03 | 76.90 |
| tight | 75.17 | 85.45 | 51.22 |

## PoolAct：扩展 HPO 家族均值（%）

每个单元为 BoN / MI；这里包含全部 9 个 HPO 任务及 free，是扩展结果，不是论文 PoolAct 主表。每 task/strategy/regime 仅一组 N=4 agents，没有额外 outer repeats；差异为描述性结果，不声称统计显著。

| 预算 | 策略 | ParamNet BoN / MI | NAS201 BoN / MI | NAS101 BoN / MI |
|---|---|---:|---:|---:|
| free | naive | 95.15 / 87.94 | 91.55 / 80.71 | 65.72 / 55.88 |
| free | cached | 94.90 / 78.78 | 97.03 / 86.86 | 65.49 / 62.77 |
| free | poolact | 95.35 / 91.79 | 96.25 / 86.26 | 99.13 / 79.03 |
| moderate | naive | 94.57 / 88.73 | 94.50 / 79.31 | 97.97 / 78.21 |
| moderate | cached | 94.04 / 81.70 | 98.07 / 88.00 | 95.98 / 67.72 |
| moderate | poolact | 95.83 / 84.08 | 96.91 / 85.30 | 98.72 / 73.29 |
| tight | naive | 86.54 / 69.49 | 91.45 / 83.21 | 94.57 / 67.92 |
| tight | cached | 87.32 / 66.89 | 94.24 / 83.64 | 94.64 / 67.78 |
| tight | poolact | 95.72 / 90.87 | 92.52 / 81.85 | 97.93 / 89.22 |

论文 PoolAct 调参对应 NAS101 A、moderate/tight，不能用上述 A/B/C 均值替代：

| 预算 | 策略 | NAS101 A BoN | NAS101 A MI |
|---|---|---:|---:|
| moderate | naive | 99.57 | 98.06 |
| moderate | cached | 99.22 | 95.16 |
| moderate | poolact | 98.50 | 72.68 |
| tight | naive | 99.26 | 92.45 |
| tight | cached | 98.55 | 91.95 |
| tight | poolact | 98.76 | 97.90 |

## 值得解释的结果及证据边界

- NAS101 家族 ExpGym 从 free 82.02 到 tight 51.22，伴随 B 的任务 Gap 从 52.56 降至 0、C 从 98.72 降至 60.36；A 在 tight 仍为 93.30。B 的 9 条 ExpGym 中 6 个真实零分，tight 为 3/3。
- B/C 的 90/90 个初始原始请求仍使用 A 式“二元邻接矩阵”提示，而 B 实际为 9 个 edge selector、C 实际为 21 个 priority 加 num_edges。B 的 28/45 个 agent 层真实零分中，8 个带未知额外键；其余 20 个键合法配置按当前解码均无输入输出路径。此现象与误用二元编码相容，但没有改提示对照，不能归因为唯一原因，也不能改分。C 的二元 priority 本身合法，不能称为非法配置。详见 [diagnostics.md](diagnostics.md)；[提示状态证据](../../protocol/nas101_hints_status_evaluation_recovery_v3.json) 明确候选提示修复未应用。
- PoolAct 策略在 tight ParamNet 的 MI 为 90.87，naive/cached 为 69.49/66.89；但不是全域领先：NAS201 三档 BoN 都由 cached 高于 poolact。NAS101 free 的家族 BoN 差异也受 B naive/cached 两组全零强烈影响，不宜推广为 NAS101 A 论文主结果。
- NAS101 A moderate 中 poolact BoN 98.50、MI 72.68；4 agents 中有 1 个真实零分，说明 BoN 可以掩盖组内失败。naive 同格 BoN 99.57、MI 98.06，无原始零分。
- ParamNet letter moderate 任务均值仅 31.39；3 次 raw 为 0.4752601 / 0.8643826 / 0.4752601，Gap 为 6.68 / 80.81 / 6.68。两个低分运行拉低均值，其中 rep 2 明确 fallback 到默认配置；不能把家族分数非单调直接归因于预算单一因素。
- 共 33 个原始零分 agent 记录：ExpGym 7，PoolAct 26；81 个 PoolAct aggregate 中的 2 个零分已包含在这些 agent 中，不应重复计数。另有 2 个 raw 非零但低于 oracle.mean，故 Gap=0；缺失不填零，模型语义零分不当作基础设施失败。
- ExpGym 明确记录 6 个 best_evaluated_fallback（其中 4 个零分）；PoolAct 未记录 answer_source。67 个 PoolAct 正式答案不同于最后模型提取但都匹配最佳可见评估，只报告这一可观察事实，不将 67 推断为确定 fallback 次数。完整逐条证据在诊断 JSON。
- ParamNet adult/free/naive/agent0 的 raw=0.8538518543、Gap=100.2922407，略高于 oracle.best=0.8537314791。oracle 的 sampled reference 并非数学上界，按论文公式保留 >100，不应截成 100。

本文不估算 GPU 时、真实墙钟或 token 用量；这些须由最终 dump audit、执行／promotion receipts 和 Slurm accounting 提供。上述 budget 是模拟任务成本，不等于真实墙钟。

## 数据与复算

- [独立完整 JSON](independent.json)：405 个 agent 层路径／SHA256／raw／Gap，81 个 PoolAct result，189 个 task 指标、63 个家族指标、54 个执行回执引用。
- [ExpGym 宽表 CSV](expgym_family_wide.csv)、[PoolAct 扩展宽表 CSV](poolact_family_wide.csv)、[论文 NAS101 A CSV](paper_poolact_nas101a.csv)、[逐任务指标 CSV](task_metrics.csv)。
- [诊断说明](diagnostics.md)、[逐 trace 诊断 JSON](diagnostics.json)、[零分分组 CSV](diagnostics.csv)。
- [纯 stdlib 独立计算脚本](compute.py)、[原始 manifest](../../runs/full_v3/manifest.json)。

冻结 source SHA256：`c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`。manifest SHA256：`5b64a55da602c6442ae0fc83d737a3df6f23a7f8b39f60d66c190232ea95ec93`。oracle SHA256：`f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e`。完整 oracle 路径及各任务 mean/best 见独立 JSON。

复算命令（stdout 输出 JSON，不覆盖旧快照）：

```bash
python3 kimi_k3_eval/reports/full_v3_hpo_independent_review/compute.py
# 正式 summary 生成后：另存 stdout 为新的证据，不覆盖 independent.json。
python3 kimi_k3_eval/reports/full_v3_hpo_independent_review/compute.py --summary /absolute/path/to/full_v3/summary.json
```

带 --summary 时会要求正式 summary 完整且绑定同一 manifest，并比较 63 个家族单元、189 个任务单元、405 个 agent 原始分数／Gap／SHA，以及论文子集 12 个 NAS101 A 指标。初始本文不宣称这些待运行核对已经通过。

[test_comparison.py](test_comparison.py) 的 9 项临时 synthetic-fixture 检查已通过：一致数据通过；分别篡改完成标志、manifest、家族值、任务值、agent raw、agent Gap、agent SHA、论文子集值均被拒绝。这是比较器测试，不是正式 summary 核对，也没有新增模型结果。
