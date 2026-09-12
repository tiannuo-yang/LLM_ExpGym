# 修复后定向重跑：三问与核心数据

[详细报告](DETAILS.zh.md) · [逐池 CSV](pool_metrics.csv) · [全部设置 CSV](aggregate_metrics.csv) · [比较 CSV](contrasts.csv) · [原始 dump / 完整存档索引](ARCHIVE_INDEX.md) · [机器存档索引](ARCHIVE_INDEX.json)

本次是已见任务上的定向、探索性修复后复核：369 个计划 N4 池、9 个模型×场景×预算单元；终态计数 `{"completed": 369}`。旧反例与正对照在新模型调用前固定，选择已参考旧效果；不构成全矩阵或未见任务检验。

[实际执行设置与解释](EXECUTION_NOTES.zh.md)。

## 1. 预算收紧是否导致性能下降？

下表直接复用冻结旧五模型单体 cohort（`6c63f1c`），不是本轮修复后的新验证。Search F1 / Audit EA 为 0–100 分，调参为旧报告已授权的 Gap0 部署效用；F−T 为正表示下降。

| 模型 | Search F1：Free→Tight | F−T | Audit EA：Free→Tight | F−T | HPO/NAS Gap0：Free→Tight | F−T |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi | 63.59 → 15.76 | +47.83 | 89.44 → 51.58 | +37.86 | 98.51 → 89.68 | +8.83 |
| GLM | 65.11 → 19.23 | +45.88 | 68.48 → 50.23 | +18.25 | 97.91 → 86.07 | +11.84 |
| Qwen | 58.15 → 18.47 | +39.68 | 91.86 → 58.37 | +33.48 | 97.47 → 85.71 | +11.76 |
| DeepSeek | 43.81 → 16.92 | +26.89 | 63.95 → 47.51 | +16.44 | 61.09 → 75.81 | -14.72 |
| GPT (medium) | 64.01 → 15.55 | +48.46 | 70.44 → 54.15 | +16.29 | 97.97 → 91.66 | +6.31 |

冻结旧数据中，Search 有 5/5 个模型从 Free 到 Tight 下降，Audit 有 5/5 个模型从 Free 到 Tight 下降，HPO/NAS 有 4/5 个模型从 Free 到 Tight 下降。DeepSeek 的 HPO/NAS 反而改善 14.72 点，因此不能概括为所有模型和端点必然退化。

[旧完整预算报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911/main_findings_v2/README.zh.md) · [原封保留的 Free/Moderate/Tight CSV](historical_expgym_summary.csv)。本轮未重跑单体矩阵，旧源码/部署限制仍适用；新 N4 结果不混入此表。

## 2. 缓存与 PoolAct 的收益或损失有多大？

同预算、同 N4、同任务/重复范围比较；正差表示 target 较高。Search F1 / Audit EA 按 0–100 分展示；NAS 是逐成员计算的 Gap 点，100 不是上限。NAS 原严格端点只要缺一个必需成员就保留 unknown；不使用已知子集替代。

在全部 9 个登记主端点单元中，PoolAct 高于 naive 8/9，高于 cached 7/9（两项比较的未知单元分别为 0、0，仍计入总分母；并列分别为 0、0）。Tight 单元中 5/5 高于两臂，未知 0。这是登记设置上的描述性计数，不是显著性检验或模型总体的普遍结论。

| 模型 | 场景 | 预算 | 指标 | naive | cached | PoolAct | cached−naive | PoolAct−cached | PoolAct−naive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-flash-0731 | Audit | moderate | evidence_acc_mv | 69.68 | 72.40 | 94.57 | +2.71 | +22.17 | +24.89 |
| deepseek-v4-flash-0731 | Audit | tight | evidence_acc_mv | 61.99 | 61.99 | 71.49 | +0.00 | +9.50 | +9.50 |
| deepseek-v4-flash-0731 | Search whois | moderate | f1_mv | 60.27 | 61.80 | 61.33 | +1.53 | -0.47 | +1.05 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap_mi | 96.72 | 96.27 | 98.74 | -0.46 | +2.47 | +2.01 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap_mi | 83.20 | 82.98 | 95.29 | -0.22 | +12.31 | +12.09 |
| glm-5.3 | Audit | tight | evidence_acc_mv | 66.06 | 65.61 | 81.90 | -0.45 | +16.29 | +15.84 |
| glm-5.3 | NAS101 | tight | gap_mi | 85.93 | 86.57 | 94.33 | +0.64 | +7.76 | +8.40 |
| gpt-5.6-sol | NAS101 | moderate | gap_mi | 98.11 | 98.21 | 97.97 | +0.11 | -0.24 | -0.14 |
| kimi-k3 | NAS101 | tight | gap_mi | 93.65 | 92.95 | 95.52 | -0.70 | +2.57 | +1.87 |

本轮 NAS 的 540 个计划成员全部可评分，各 setting 的原严格 Gap-MI/BoN 与已授权 Gap=0 敏感性数值相同，因此不重复展示同值表；完整两种口径仍保留在[聚合 CSV](aggregate_metrics.csv)和详细版。


### 旧反例与正对照的变化

以下按同一端点比较修前/后；NAS 此小节特指旧主报告使用的 Gap0-MI 敏感性，不能替代上方原严格端点。‘旧负差’指历史 PoolAct 低于 naive 或 cached 中至少一个；所有登记单元均进入计数，不按本轮表现选样。

旧负差共 5 个单元：高于两臂 3 个，低于至少一臂 2 个。 旧非负对照共 4 个单元：高于两臂 4 个。 残余负差单元（DeepSeek / Search whois / moderate；GPT (medium) / NAS101 / moderate）的三臂均无缺最终回答，故这些负差不能归因于本轮缺答；这不排除 legacy 等其他评价边界。

| 模型 | 场景 | 预算 | 指标 | 旧 P−naive | 新 P−naive | 旧 P−cached | 新 P−cached |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-flash-0731 | Audit | moderate | evidence_acc_mv | -25.79 | +24.89 | -25.34 | +22.17 |
| deepseek-v4-flash-0731 | Audit | tight | evidence_acc_mv | -42.99 | +9.50 | -30.32 | +9.50 |
| deepseek-v4-flash-0731 | Search whois | moderate | f1_mv | -1.28 | +1.05 | -5.13 | -0.47 |
| deepseek-v4-flash-0731 | NAS101 | moderate | gap0_mi | +0.11 | +2.01 | -15.78 | +2.47 |
| deepseek-v4-flash-0731 | NAS101 | tight | gap0_mi | +19.24 | +12.09 | +24.85 | +12.31 |
| glm-5.3 | Audit | tight | evidence_acc_mv | +10.41 | +15.84 | +9.05 | +16.29 |
| glm-5.3 | NAS101 | tight | gap0_mi | +12.22 | +8.40 | +9.99 | +7.76 |
| gpt-5.6-sol | NAS101 | moderate | gap0_mi | -2.63 | -0.14 | -2.70 | -0.24 |
| kimi-k3 | NAS101 | tight | gap0_mi | +1.79 | +1.87 | +1.94 | +2.57 |

全部正、零、负与未知均保留；来源变化包含源码、提示和部署候选，修前修后差不能唯一归因于某一个补丁。[历史/本轮逐 setting 比较](historical_comparison.csv)分开保留两个 cohort。[资源表](resources_by_setting.csv)和[全部尝试账本](ALL_ATTEMPTS_INDEX.json)包含其声明范围；同反馈预算不等于同 token、GPU 或真实时间。

## 3. 最优模型是否随任务和预算重排？

下表同样直接引用冻结旧单体 cohort（`6c63f1c`）：每家族都使用当时相同的五模型候选集，并列最优全部保留；不混合不同指标为总榜，不加入本轮 PoolAct 新分数。

| 任务家族 / 指标 | Free 最优（分数） | Tight 最优（分数） | 最优集合改变 |
| --- | --- | --- | --- |
| Search whois / F1 | GLM (68.27) | GLM (23.06) | 否 |
| Search whatis / F1 | GPT (medium) (65.42) | DeepSeek (15.93) | 是 |
| Audit / EA | Qwen (91.86) | Qwen (58.37) | 否 |
| ParamNet / Gap0 | GPT (medium) (97.31) | GPT (medium) (85.69) | 否 |
| NAS101 / Gap0 | GLM (99.06) | GPT (medium) (97.03) | 是 |
| NAS201 / Gap0 | Kimi (99.77) | Kimi (94.66) | 否 |

旧 cohort 的 6 个家族中，2 个在 Free→Tight 时发生最优模型集合变化。Free 和 Tight 两档都不存在横跨所有家族的同一最优模型，选型依赖目标任务及反馈预算。

[旧家族排名完整报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911/main_findings_v2/README.zh.md) · [原封保留的五模型×六家族×三预算 CSV](historical_family_rankings.csv)。这描述当时任务与部署条件的依赖性，不意味着小差值具有显著性；本轮定向 N4 矩阵不能更新这一单体排名。

## 查验入口

[详细报告](DETAILS.zh.md) · [逐池 CSV](pool_metrics.csv) · [全部设置 CSV](aggregate_metrics.csv) · [比较 CSV](contrasts.csv) · [原始 dump / 完整存档索引](ARCHIVE_INDEX.md) · [机器存档索引](ARCHIVE_INDEX.json)

[输入身份](INPUTS.json) · [逐池执行/缺答分母](pool_status.csv) · [逐重复 CSV](by_outerseed.csv)。
