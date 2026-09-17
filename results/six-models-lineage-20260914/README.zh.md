# 六模型综合报告

范围：Kimi、GLM、Qwen、DeepSeek、GPT、Gemini；按用户要求排除 Claude。本次只更新报告，没有新增实验或重评分。

沿用 2026-09-13 冻结分数；Gemini 于 2026-09-14 23:45 UTC 复查，完成项未变化。合计执行完成 **4,682/4,698**，严格评分完整 **4,671**。

[每次实验记录](EXPERIMENT_LOG.zh.md) · [最终数据来自哪里](DATA_LINEAGE.zh.md) · [原始 dump / CSV 存档](ARCHIVE_INDEX.md) · [完整设置与详细数据](DETAILS.zh.md) · [独立复核](INDEPENDENT_REVIEW.zh.md)

## 三个结论

1. **预算收紧，表现下降。** Free→Tight：Search 6/6、Audit 6/6 个模型下降；HPO 4/5 个完整模型下降，Gemini 全场景 HPO 未齐。
2. **PoolAct 通常改善同预算表现。** 33/36 组三策略数据完整，其中 29 组高于 naive 和 cached；Tight 为 16/17。这是方向计数，不是每个模型、每个任务都改善。
3. **最佳模型随任务和部署预算变化。** 六模型在 Free/Tight 都完整的 4 个任务家族中，3 个更换第一名，见下表。模型选择需要结合 task family 和 budget。

这些是当前部署设置下的描述性结果，不是显著性或单一算法的因果结论。排除 Claude 是用户指定的回顾性范围调整，不构成稳健性检验；未删除其历史记录。

## 数据范围

| 模型 | effort | 执行完成/计划 | 严格评分完整 |
| --- | --- | --- | --- |
| Kimi K3 | max | 783/783 | 783 |
| GLM 5.3 | max | 783/783 | 783 |
| Qwen 3.8 | xhigh | 783/783 | 783 |
| DeepSeek V4 Flash | max | 783/783 | 772 |
| GPT-5.6-sol | medium | 783/783 | 783 |
| Gemini 3.8 Flash | medium | 767/783 | 767 |

每模型计划：ExpGym N1 417 项（Free/Moderate/Tight）+ N4 366 池（Moderate/Tight × naive/cached/poolact）。DeepSeek 有 11 项严格评分缺失；Gemini 保留 1 个 Search 池失败和 15 个 HPO 未完成项，不能视为全量。

## 1. ExpGym：Free → Moderate → Tight

F1、EvidenceAcc 显示为 0–100；Gap0 保持原 points。不同场景不合成总分。

| 模型 | Search F1：F / M / T | Audit EA：F / M / T | HPO Gap0：F / M / T |
| --- | --- | --- | --- |
| Kimi K3 | 63.59 / 49.62 / 15.76 | 89.44 / 68.78 / 51.58 | 98.51 / 94.23 / 89.68 |
| GLM 5.3 | 65.11 / 53.28 / 19.23 | 68.48 / 67.87 / 50.23 | 97.91 / 96.15 / 86.07 |
| Qwen 3.8 | 58.15 / 50.98 / 18.47 | 91.86 / 74.96 / 58.37 | 97.47 / 95.13 / 85.71 |
| DeepSeek V4 Flash | 43.81 / 42.11 / 16.92 | 63.95 / 58.67 / 47.51 | 61.09 / 74.02 / 75.81 |
| GPT-5.6-sol | 64.01 / 53.06 / 15.55 | 70.44 / 65.91 / 54.15 | 97.97 / 96.61 / 91.66 |
| Gemini 3.8 Flash | 72.03 / 55.02 / 17.83 | 97.59 / 82.81 / 72.10 | unknown [25/27] / unknown [25/27] / unknown [25/27] |

## 2. N4：naive / cached / PoolAct

每格依次为 naive / cached / poolact；Search 为 whois 子集的 F1-MV，Audit 为 EA-MV，HPO 为 Gap0-MI。N4 Search 与 N1 的 73 题全集不同，不直接互减。

| 模型 | 预算 | Search F1-MV | Audit EA-MV | HPO Gap0-MI |
| --- | --- | --- | --- | --- |
| Kimi K3 | Moderate | 64.59 / 64.20 / 66.74 | 73.76 / 76.47 / 93.67 | 98.04 / 97.96 / 98.56 |
| Kimi K3 | Tight | 21.29 / 18.72 / 30.43 | 55.20 / 54.75 / 62.90 | 93.65 / 92.95 / 95.52 |
| GLM 5.3 | Moderate | 62.03 / 65.67 / 65.74 | 81.00 / 84.62 / 97.74 | 97.87 / 98.06 / 98.97 |
| GLM 5.3 | Tight | 20.86 / 20.86 / 30.01 | 66.06 / 65.61 / 81.90 | 85.93 / 86.57 / 94.33 |
| Qwen 3.8 | Moderate | 61.21 / 61.17 / 63.48 | 68.78 / 74.66 / 93.67 | 96.92 / 97.72 / 98.87 |
| Qwen 3.8 | Tight | 18.30 / 23.31 / 20.69 | 56.11 / 60.18 / 63.80 | 90.62 / 90.76 / 96.27 |
| DeepSeek V4 Flash | Moderate | 60.27 / 61.80 / 61.33 | 69.68 / 72.40 / 94.57 | 96.72 / 96.27 / 98.74 |
| DeepSeek V4 Flash | Tight | 2.56 / 4.27 / 7.44 | 61.99 / 61.99 / 71.49 | 83.20 / 82.98 / 95.29 |
| GPT-5.6-sol | Moderate | 62.31 / 63.78 / 60.60 | 64.71 / 65.16 / 67.42 | 98.11 / 98.21 / 97.97 |
| GPT-5.6-sol | Tight | 19.15 / 20.28 / 21.89 | 51.58 / 58.82 / 62.44 | 96.64 / 96.05 / 97.27 |
| Gemini 3.8 Flash | Moderate | unknown [38/39] / 68.11 / 68.04 | 80.54 / 87.33 / 97.74 | unknown [8/9] / unknown [7/9] / unknown [6/9] |
| Gemini 3.8 Flash | Tight | 20.43 / 20.90 / 33.40 | 68.78 / 71.49 / 73.76 | 95.93 / unknown [7/9] / unknown [8/9] |

## 3. 任务家族与预算的排名重排

| 任务家族 | Free 最高 | Moderate 最高 | Tight 最高 |
| --- | --- | --- | --- |
| whois | Gemini 3.8 Flash 73.86 | GLM 5.3 64.28 | GLM 5.3 23.06 |
| whatis | Gemini 3.8 Flash 69.93 | Gemini 3.8 Flash 46.13 | DeepSeek V4 Flash 15.93 |
| evidence_audit | Gemini 3.8 Flash 97.59 | Gemini 3.8 Flash 82.81 | Gemini 3.8 Flash 72.10 |
| paramnet | 未齐；已知最高 GPT-5.6-sol 97.31 | GPT-5.6-sol 95.27 | 未齐；已知最高 GPT-5.6-sol 85.69 |
| nasbench101 | Gemini 3.8 Flash 99.33 | 未齐；已知最高 GPT-5.6-sol 98.32 | 未齐；已知最高 GPT-5.6-sol 97.03 |
| nasbench201 | Kimi K3 99.77 | Gemini 3.8 Flash 99.12 | Gemini 3.8 Flash 94.87 |

“未齐；已知最高”不代表六模型冠军。排名只使用 N1，同一端点、同一家族；并列保留。

unknown 不补零、不用成功子集冒充全量。Gap0 仅把正常结束但无有效 HPO 配置记 0；严格 Gap 仍缺失，失败/未完成不适用。所有负差保留在详细表和 CSV。

[详细报告](DETAILS.zh.md)含完整预算、策略、严格 Gap / Gap0、全部次指标和重复层入口。[实验记录](EXPERIMENT_LOG.zh.md)说明何时发现问题、哪些组重跑及最终采用哪份数据。
