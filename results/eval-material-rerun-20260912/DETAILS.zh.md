# 修复后定向重跑：完整设置与数据

[简明主报告](README.zh.md)

[详细报告](DETAILS.zh.md) · [逐池 CSV](pool_metrics.csv) · [全部设置 CSV](aggregate_metrics.csv) · [比较 CSV](contrasts.csv) · [原始 dump / 完整存档索引](ARCHIVE_INDEX.md) · [机器存档索引](ARCHIVE_INDEX.json)

本次是已见任务上的定向、探索性修复后复核：369 个计划 N4 池、9 个模型×场景×预算单元；终态计数 `{"completed": 369}`。旧反例与正对照在新模型调用前固定，选择已参考旧效果；不构成全矩阵或未见任务检验。

## 契约与来源

启动前范围见 [PLAN.zh.md](PLAN.zh.md)，动态执行规则见 [EXECUTION_CONTRACT.zh.md](EXECUTION_CONTRACT.zh.md)，实际重试/并发、服务拓扑、GPT恢复与context验证范围见 [EXECUTION_NOTES.zh.md](EXECUTION_NOTES.zh.md)。

每 item 内先折叠全部注册重复，再 item 等权；NAS 三个任务×R3 不是 36 个独立样本。Search/Audit R1 不计算重复 SD。不做显著性检验、不取配对交集。严格未知、零分、正常缺答、执行失败与未执行分别保存。评分为 legacy / task-abstention-v1；Gap=max(0,100×(agent_perf−oracle.mean_perf)/(oracle.best_perf−oracle.mean_perf))，逐成员变换后求 MI。本程序只读取已保存的标量与固定来源，不重新调用 scorer，也不代替原队列身份/评分校验或独立最终复核。

模型请求参数和源码分支见 [plan 设置投影](settings.json)，包括各自 source SHA；GPT native Responses 的实际 wire 参数省略规则不能从 nominal max_tokens 推断。执行恢复必须有显式映射，失败历史保留在完整尝试账本，不自动选最新成功文件。

NAS 仍沿用 legacy / task-abstention-v1，未升级 task-abstention-v5。提交 peer 配置但该配置不在自身 trace 时，原 legacy 评分可能回退自身 best，并不等同于重新评估所提交配置。本轮未改这个旧契约，也未事后把轨迹最优配置填给无回答成员。因此完整评分只能排除相应的缺答/未知问题，不能据此声称不存在其他评价局限；严格 Gap 与已授权 Gap0 敏感性都应在这一边界内解读。

主报告问1/问3直接读取同一冻结旧 cohort 的 [single 预算 CSV](historical_expgym_summary.csv) 和 [家族排名 CSV](historical_family_rankings.csv)，原值已是展示单位，不再次乘100或重算旧 raw。它们不是修复后数据；下列全部策略表才是本轮定向重跑，两个来源不拼成新的模型排行榜。

## 全部策略设置

| 模型 | 场景 | 预算 | 策略 | 指标 | 完整均值 | 已知/预期池 | 完整 items | R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-flash-0731 | Audit | moderate | cached | evidence_acc_mi | 71.27 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | cached | evidence_acc_mv | 72.40 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | cached | label_acc_mi | 89.48 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | cached | label_acc_mv | 93.21 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | naive | evidence_acc_mi | 66.74 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | naive | evidence_acc_mv | 69.68 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | naive | label_acc_mi | 85.97 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | naive | label_acc_mv | 91.86 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | poolact | evidence_acc_mi | 94.68 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | poolact | evidence_acc_mv | 94.57 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | poolact | label_acc_mi | 96.15 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | moderate | poolact | label_acc_mv | 96.38 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | cached | evidence_acc_mi | 58.94 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | cached | evidence_acc_mv | 61.99 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | cached | label_acc_mi | 84.62 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | cached | label_acc_mv | 89.59 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | naive | evidence_acc_mi | 60.97 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | naive | evidence_acc_mv | 61.99 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | naive | label_acc_mi | 86.88 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | naive | label_acc_mv | 89.14 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | poolact | evidence_acc_mi | 70.59 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | poolact | evidence_acc_mv | 71.49 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | poolact | label_acc_mi | 90.72 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Audit | tight | poolact | label_acc_mv | 92.76 | 13/13 | 13/13 | 1 |
| deepseek-v4-flash-0731 | Search whois | moderate | cached | f1_mi | 60.88 | 39/39 | 39/39 | 1 |
| deepseek-v4-flash-0731 | Search whois | moderate | cached | f1_mv | 61.80 | 39/39 | 39/39 | 1 |
| deepseek-v4-flash-0731 | Search whois | moderate | naive | f1_mi | 58.36 | 39/39 | 39/39 | 1 |
| deepseek-v4-flash-0731 | Search whois | moderate | naive | f1_mv | 60.27 | 39/39 | 39/39 | 1 |
| deepseek-v4-flash-0731 | Search whois | moderate | poolact | f1_mi | 60.02 | 39/39 | 39/39 | 1 |
| deepseek-v4-flash-0731 | Search whois | moderate | poolact | f1_mv | 61.33 | 39/39 | 39/39 | 1 |
| deepseek-v4-flash-0731 | NAS101 | moderate | cached | gap0_bon | 98.80 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | cached | gap0_mi | 96.27 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | cached | gap_bon | 98.80 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | cached | gap_mi | 96.27 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | cached | raw_perf_bon | 94.23 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | cached | raw_perf_mi | 93.12 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | naive | gap0_bon | 98.70 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | naive | gap0_mi | 96.72 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | naive | gap_bon | 98.70 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | naive | gap_mi | 96.72 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | naive | raw_perf_bon | 94.21 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | naive | raw_perf_mi | 93.35 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | poolact | gap0_bon | 99.00 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | poolact | gap0_mi | 98.74 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | poolact | gap_bon | 99.00 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | poolact | gap_mi | 98.74 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | poolact | raw_perf_bon | 94.27 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | moderate | poolact | raw_perf_mi | 94.16 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | cached | gap0_bon | 95.21 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | cached | gap0_mi | 82.98 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | cached | gap_bon | 95.21 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | cached | gap_mi | 82.98 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | cached | raw_perf_bon | 91.86 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | cached | raw_perf_mi | 84.91 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | naive | gap0_bon | 94.88 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | naive | gap0_mi | 83.20 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | naive | gap_bon | 94.88 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | naive | gap_mi | 83.20 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | naive | raw_perf_bon | 91.78 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | naive | raw_perf_mi | 84.98 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | poolact | gap0_bon | 98.28 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | poolact | gap0_mi | 95.29 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | poolact | gap_bon | 98.28 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | poolact | gap_mi | 95.29 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | poolact | raw_perf_bon | 93.85 | 9/9 | 3/3 | 3 |
| deepseek-v4-flash-0731 | NAS101 | tight | poolact | raw_perf_mi | 92.42 | 9/9 | 3/3 | 3 |
| glm-5.3 | Audit | tight | cached | evidence_acc_mi | 62.90 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | cached | evidence_acc_mv | 65.61 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | cached | label_acc_mi | 86.65 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | cached | label_acc_mv | 89.14 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | naive | evidence_acc_mi | 63.46 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | naive | evidence_acc_mv | 66.06 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | naive | label_acc_mi | 86.65 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | naive | label_acc_mv | 90.50 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | poolact | evidence_acc_mi | 75.79 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | poolact | evidence_acc_mv | 81.90 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | poolact | label_acc_mi | 85.07 | 13/13 | 13/13 | 1 |
| glm-5.3 | Audit | tight | poolact | label_acc_mv | 92.31 | 13/13 | 13/13 | 1 |
| glm-5.3 | NAS101 | tight | cached | gap0_bon | 94.87 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | cached | gap0_mi | 86.57 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | cached | gap_bon | 94.87 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | cached | gap_mi | 86.57 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | cached | raw_perf_bon | 91.79 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | cached | raw_perf_mi | 88.41 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | naive | gap0_bon | 93.13 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | naive | gap0_mi | 85.93 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | naive | gap_bon | 93.13 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | naive | gap_mi | 85.93 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | naive | raw_perf_bon | 90.67 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | naive | raw_perf_mi | 88.42 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | poolact | gap0_bon | 98.37 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | poolact | gap0_mi | 94.33 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | poolact | gap_bon | 98.37 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | poolact | gap_mi | 94.33 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | poolact | raw_perf_bon | 93.87 | 9/9 | 3/3 | 3 |
| glm-5.3 | NAS101 | tight | poolact | raw_perf_mi | 92.19 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | cached | gap0_bon | 99.01 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | cached | gap0_mi | 98.21 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | cached | gap_bon | 99.01 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | cached | gap_mi | 98.21 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | cached | raw_perf_bon | 94.31 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | cached | raw_perf_mi | 93.96 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | naive | gap0_bon | 98.74 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | naive | gap0_mi | 98.11 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | naive | gap_bon | 98.74 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | naive | gap_mi | 98.11 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | naive | raw_perf_bon | 94.21 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | naive | raw_perf_mi | 93.92 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | poolact | gap0_bon | 99.19 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | poolact | gap0_mi | 97.97 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | poolact | gap_bon | 99.19 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | poolact | gap_mi | 97.97 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | poolact | raw_perf_bon | 94.37 | 9/9 | 3/3 | 3 |
| gpt-5.6-sol | NAS101 | moderate | poolact | raw_perf_mi | 93.87 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | cached | gap0_bon | 97.48 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | cached | gap0_mi | 92.95 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | cached | gap_bon | 97.48 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | cached | gap_mi | 92.95 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | cached | raw_perf_bon | 93.72 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | cached | raw_perf_mi | 91.44 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | naive | gap0_bon | 96.16 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | naive | gap0_mi | 93.65 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | naive | gap_bon | 96.16 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | naive | gap_mi | 93.65 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | naive | raw_perf_bon | 92.68 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | naive | raw_perf_mi | 91.38 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | poolact | gap0_bon | 98.20 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | poolact | gap0_mi | 95.52 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | poolact | gap_bon | 98.20 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | poolact | gap_mi | 95.52 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | poolact | raw_perf_bon | 93.96 | 9/9 | 3/3 | 3 |
| kimi-k3 | NAS101 | tight | poolact | raw_perf_mi | 92.69 | 9/9 | 3/3 | 3 |

## 全部方向对照

| 模型 | 场景 | 预算 | 指标 | target−baseline | 差值 | 已知/预期配对池 |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-flash-0731 | Audit | moderate | evidence_acc_mi | cached_minus_naive | +4.52 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | evidence_acc_mv | cached_minus_naive | +2.71 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | label_acc_mi | cached_minus_naive | +3.51 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | label_acc_mv | cached_minus_naive | +1.36 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | evidence_acc_mi | poolact_minus_cached | +23.42 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | evidence_acc_mv | poolact_minus_cached | +22.17 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | label_acc_mi | poolact_minus_cached | +6.67 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | label_acc_mv | poolact_minus_cached | +3.17 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | evidence_acc_mi | poolact_minus_naive | +27.94 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | evidence_acc_mv | poolact_minus_naive | +24.89 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | label_acc_mi | poolact_minus_naive | +10.18 | 13/13 |
| deepseek-v4-flash-0731 | Audit | moderate | label_acc_mv | poolact_minus_naive | +4.52 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | evidence_acc_mi | cached_minus_naive | -2.04 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | evidence_acc_mv | cached_minus_naive | +0.00 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | label_acc_mi | cached_minus_naive | -2.26 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | label_acc_mv | cached_minus_naive | +0.45 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | evidence_acc_mi | poolact_minus_cached | +11.65 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | evidence_acc_mv | poolact_minus_cached | +9.50 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | label_acc_mi | poolact_minus_cached | +6.11 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | label_acc_mv | poolact_minus_cached | +3.17 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | evidence_acc_mi | poolact_minus_naive | +9.62 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | evidence_acc_mv | poolact_minus_naive | +9.50 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | label_acc_mi | poolact_minus_naive | +3.85 | 13/13 |
| deepseek-v4-flash-0731 | Audit | tight | label_acc_mv | poolact_minus_naive | +3.62 | 13/13 |
| deepseek-v4-flash-0731 | Search whois | moderate | f1_mi | cached_minus_naive | +2.52 | 39/39 |
| deepseek-v4-flash-0731 | Search whois | moderate | f1_mv | cached_minus_naive | +1.53 | 39/39 |
| deepseek-v4-flash-0731 | Search whois | moderate | f1_mi | poolact_minus_cached | -0.87 | 39/39 |
| deepseek-v4-flash-0731 | Search whois | moderate | f1_mv | poolact_minus_cached | -0.47 | 39/39 |
| deepseek-v4-flash-0731 | Search whois | moderate | f1_mi | poolact_minus_naive | +1.66 | 39/39 |
| deepseek-v4-flash-0731 | Search whois | moderate | f1_mv | poolact_minus_naive | +1.05 | 39/39 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap0_bon | cached_minus_naive | +0.10 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap0_mi | cached_minus_naive | -0.46 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap_bon | cached_minus_naive | +0.10 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap_mi | cached_minus_naive | -0.46 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | raw_perf_bon | cached_minus_naive | +0.02 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | raw_perf_mi | cached_minus_naive | -0.23 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap0_bon | poolact_minus_cached | +0.19 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap0_mi | poolact_minus_cached | +2.47 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap_bon | poolact_minus_cached | +0.19 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap_mi | poolact_minus_cached | +2.47 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | raw_perf_bon | poolact_minus_cached | +0.05 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | raw_perf_mi | poolact_minus_cached | +1.04 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap0_bon | poolact_minus_naive | +0.30 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap0_mi | poolact_minus_naive | +2.01 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap_bon | poolact_minus_naive | +0.30 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap_mi | poolact_minus_naive | +2.01 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | raw_perf_bon | poolact_minus_naive | +0.07 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | moderate | raw_perf_mi | poolact_minus_naive | +0.81 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap0_bon | cached_minus_naive | +0.34 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap0_mi | cached_minus_naive | -0.22 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap_bon | cached_minus_naive | +0.34 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap_mi | cached_minus_naive | -0.22 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | raw_perf_bon | cached_minus_naive | +0.07 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | raw_perf_mi | cached_minus_naive | -0.07 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap0_bon | poolact_minus_cached | +3.07 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap0_mi | poolact_minus_cached | +12.31 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap_bon | poolact_minus_cached | +3.07 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap_mi | poolact_minus_cached | +12.31 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | raw_perf_bon | poolact_minus_cached | +2.00 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | raw_perf_mi | poolact_minus_cached | +7.51 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap0_bon | poolact_minus_naive | +3.41 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap0_mi | poolact_minus_naive | +12.09 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap_bon | poolact_minus_naive | +3.41 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap_mi | poolact_minus_naive | +12.09 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | raw_perf_bon | poolact_minus_naive | +2.07 | 9/9 |
| deepseek-v4-flash-0731 | NAS101 | tight | raw_perf_mi | poolact_minus_naive | +7.44 | 9/9 |
| glm-5.3 | Audit | tight | evidence_acc_mi | cached_minus_naive | -0.57 | 13/13 |
| glm-5.3 | Audit | tight | evidence_acc_mv | cached_minus_naive | -0.45 | 13/13 |
| glm-5.3 | Audit | tight | label_acc_mi | cached_minus_naive | -0.00 | 13/13 |
| glm-5.3 | Audit | tight | label_acc_mv | cached_minus_naive | -1.36 | 13/13 |
| glm-5.3 | Audit | tight | evidence_acc_mi | poolact_minus_cached | +12.90 | 13/13 |
| glm-5.3 | Audit | tight | evidence_acc_mv | poolact_minus_cached | +16.29 | 13/13 |
| glm-5.3 | Audit | tight | label_acc_mi | poolact_minus_cached | -1.58 | 13/13 |
| glm-5.3 | Audit | tight | label_acc_mv | poolact_minus_cached | +3.17 | 13/13 |
| glm-5.3 | Audit | tight | evidence_acc_mi | poolact_minus_naive | +12.33 | 13/13 |
| glm-5.3 | Audit | tight | evidence_acc_mv | poolact_minus_naive | +15.84 | 13/13 |
| glm-5.3 | Audit | tight | label_acc_mi | poolact_minus_naive | -1.58 | 13/13 |
| glm-5.3 | Audit | tight | label_acc_mv | poolact_minus_naive | +1.81 | 13/13 |
| glm-5.3 | NAS101 | tight | gap0_bon | cached_minus_naive | +1.74 | 9/9 |
| glm-5.3 | NAS101 | tight | gap0_mi | cached_minus_naive | +0.64 | 9/9 |
| glm-5.3 | NAS101 | tight | gap_bon | cached_minus_naive | +1.74 | 9/9 |
| glm-5.3 | NAS101 | tight | gap_mi | cached_minus_naive | +0.64 | 9/9 |
| glm-5.3 | NAS101 | tight | raw_perf_bon | cached_minus_naive | +1.12 | 9/9 |
| glm-5.3 | NAS101 | tight | raw_perf_mi | cached_minus_naive | -0.01 | 9/9 |
| glm-5.3 | NAS101 | tight | gap0_bon | poolact_minus_cached | +3.50 | 9/9 |
| glm-5.3 | NAS101 | tight | gap0_mi | poolact_minus_cached | +7.76 | 9/9 |
| glm-5.3 | NAS101 | tight | gap_bon | poolact_minus_cached | +3.50 | 9/9 |
| glm-5.3 | NAS101 | tight | gap_mi | poolact_minus_cached | +7.76 | 9/9 |
| glm-5.3 | NAS101 | tight | raw_perf_bon | poolact_minus_cached | +2.07 | 9/9 |
| glm-5.3 | NAS101 | tight | raw_perf_mi | poolact_minus_cached | +3.78 | 9/9 |
| glm-5.3 | NAS101 | tight | gap0_bon | poolact_minus_naive | +5.23 | 9/9 |
| glm-5.3 | NAS101 | tight | gap0_mi | poolact_minus_naive | +8.40 | 9/9 |
| glm-5.3 | NAS101 | tight | gap_bon | poolact_minus_naive | +5.23 | 9/9 |
| glm-5.3 | NAS101 | tight | gap_mi | poolact_minus_naive | +8.40 | 9/9 |
| glm-5.3 | NAS101 | tight | raw_perf_bon | poolact_minus_naive | +3.19 | 9/9 |
| glm-5.3 | NAS101 | tight | raw_perf_mi | poolact_minus_naive | +3.77 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap0_bon | cached_minus_naive | +0.27 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap0_mi | cached_minus_naive | +0.11 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap_bon | cached_minus_naive | +0.27 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap_mi | cached_minus_naive | +0.11 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | raw_perf_bon | cached_minus_naive | +0.10 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | raw_perf_mi | cached_minus_naive | +0.04 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap0_bon | poolact_minus_cached | +0.18 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap0_mi | poolact_minus_cached | -0.24 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap_bon | poolact_minus_cached | +0.18 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap_mi | poolact_minus_cached | -0.24 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | raw_perf_bon | poolact_minus_cached | +0.05 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | raw_perf_mi | poolact_minus_cached | -0.09 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap0_bon | poolact_minus_naive | +0.45 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap0_mi | poolact_minus_naive | -0.14 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap_bon | poolact_minus_naive | +0.45 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | gap_mi | poolact_minus_naive | -0.14 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | raw_perf_bon | poolact_minus_naive | +0.16 | 9/9 |
| gpt-5.6-sol | NAS101 | moderate | raw_perf_mi | poolact_minus_naive | -0.05 | 9/9 |
| kimi-k3 | NAS101 | tight | gap0_bon | cached_minus_naive | +1.32 | 9/9 |
| kimi-k3 | NAS101 | tight | gap0_mi | cached_minus_naive | -0.70 | 9/9 |
| kimi-k3 | NAS101 | tight | gap_bon | cached_minus_naive | +1.32 | 9/9 |
| kimi-k3 | NAS101 | tight | gap_mi | cached_minus_naive | -0.70 | 9/9 |
| kimi-k3 | NAS101 | tight | raw_perf_bon | cached_minus_naive | +1.04 | 9/9 |
| kimi-k3 | NAS101 | tight | raw_perf_mi | cached_minus_naive | +0.06 | 9/9 |
| kimi-k3 | NAS101 | tight | gap0_bon | poolact_minus_cached | +0.72 | 9/9 |
| kimi-k3 | NAS101 | tight | gap0_mi | poolact_minus_cached | +2.57 | 9/9 |
| kimi-k3 | NAS101 | tight | gap_bon | poolact_minus_cached | +0.72 | 9/9 |
| kimi-k3 | NAS101 | tight | gap_mi | poolact_minus_cached | +2.57 | 9/9 |
| kimi-k3 | NAS101 | tight | raw_perf_bon | poolact_minus_cached | +0.25 | 9/9 |
| kimi-k3 | NAS101 | tight | raw_perf_mi | poolact_minus_cached | +1.25 | 9/9 |
| kimi-k3 | NAS101 | tight | gap0_bon | poolact_minus_naive | +2.04 | 9/9 |
| kimi-k3 | NAS101 | tight | gap0_mi | poolact_minus_naive | +1.87 | 9/9 |
| kimi-k3 | NAS101 | tight | gap_bon | poolact_minus_naive | +2.04 | 9/9 |
| kimi-k3 | NAS101 | tight | gap_mi | poolact_minus_naive | +1.87 | 9/9 |
| kimi-k3 | NAS101 | tight | raw_perf_bon | poolact_minus_naive | +1.28 | 9/9 |
| kimi-k3 | NAS101 | tight | raw_perf_mi | poolact_minus_naive | +1.31 | 9/9 |

逐 task/question 不挤入主报告；[逐池原分](pool_metrics.csv)、[逐 task 汇总](by_item.csv)、[逐 seed block](by_outerseed.csv)、[三策略配对](paired_rows.csv)保留完整细节。[修前修后对照](historical_comparison.csv)使用未舍入值，历史文件不重写。

## 资源与原始数据

[设置级资源](resources_by_setting.csv)是资源 exporter 已记录的范围，不代表所有失败尝试。[全部尝试账本](ALL_ATTEMPTS_INDEX.json)另计冷启动、验证、失败、未完成及获准恢复；并发 pool wall 之和不能推导总历时。reasoning 若包含在 output 不再次相加；模拟反馈秒不是实际 GPU 秒，allocation GPU-hours 可含空闲。

[详细报告](DETAILS.zh.md) · [逐池 CSV](pool_metrics.csv) · [全部设置 CSV](aggregate_metrics.csv) · [比较 CSV](contrasts.csv) · [原始 dump / 完整存档索引](ARCHIVE_INDEX.md) · [机器存档索引](ARCHIVE_INDEX.json)

