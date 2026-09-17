# Gemini OpenRouter 主实验补充报告

冻结来源：`ad03e8c42ca501016176ee1bc407b38499178506`。此目录是独立补充版，未修改冻结报告。执行完成 **4698/4698**；严格评分完整 **4687**；Gemini **783/783**。

本版保留原 4682 份采用结果（其中 Gemini 767 份），只补原先注册但没有采用完成结果的 16 项。新项使用 OpenRouter；原 Gemini 项使用 Sub2 API。星号 Gemini* 表示混合提供方的数据组合，不是全套 OpenRouter 重跑。协议、思考与采样参数尽量对应，但提供方切换的影响不能从这批数据单独识别。

F1 / EA 显示 0–100；Gap0 使用原 points。完整均值缺失仍为 unknown；不把部分成功均值用作完整结果。HPO 先在任务内平均 3 重复，再对任务等权；Gap0 仅将正常结束的无配置结果计零，失败或未执行不计零。

## N1：Free / Moderate / Tight

| 模型 | Search F1 | Audit EA | HPO Gap0 |
| --- | --- | --- | --- |
| Kimi | 63.59 / 49.62 / 15.76 | 89.44 / 68.78 / 51.58 | 98.51 / 94.23 / 89.68 |
| GLM | 65.11 / 53.28 / 19.23 | 68.48 / 67.87 / 50.23 | 97.91 / 96.15 / 86.07 |
| Qwen | 58.15 / 50.98 / 18.47 | 91.86 / 74.96 / 58.37 | 97.47 / 95.13 / 85.71 |
| DeepSeek | 43.81 / 42.11 / 16.92 | 63.95 / 58.67 / 47.51 | 61.09 / 74.02 / 75.81 |
| GPT | 64.01 / 53.06 / 15.55 | 70.44 / 65.91 / 54.15 | 97.97 / 96.61 / 91.66 |
| Gemini* | 72.03 / 55.02 / 17.83 | 97.59 / 82.81 / 72.10 | 98.16 / 97.27 / 93.86 |

## N4：naive / cached / PoolAct

Search 为 whois 39 题；Audit 13 文档；HPO 为 NAS101 A/B/C × 3 重复。

| 模型 | 预算 | Search F1-MV | Audit EA-MV | HPO Gap0-MI |
| --- | --- | --- | --- | --- |
| Kimi | moderate | 64.59 / 64.20 / 66.74 | 73.76 / 76.47 / 93.67 | 98.04 / 97.96 / 98.56 |
| Kimi | tight | 21.29 / 18.72 / 30.43 | 55.20 / 54.75 / 62.90 | 93.65 / 92.95 / 95.52 |
| GLM | moderate | 62.03 / 65.67 / 65.74 | 81.00 / 84.62 / 97.74 | 97.87 / 98.06 / 98.97 |
| GLM | tight | 20.86 / 20.86 / 30.01 | 66.06 / 65.61 / 81.90 | 85.93 / 86.57 / 94.33 |
| Qwen | moderate | 61.21 / 61.17 / 63.48 | 68.78 / 74.66 / 93.67 | 96.92 / 97.72 / 98.87 |
| Qwen | tight | 18.30 / 23.31 / 20.69 | 56.11 / 60.18 / 63.80 | 90.62 / 90.76 / 96.27 |
| DeepSeek | moderate | 60.27 / 61.80 / 61.33 | 69.68 / 72.40 / 94.57 | 96.72 / 96.27 / 98.74 |
| DeepSeek | tight | 2.56 / 4.27 / 7.44 | 61.99 / 61.99 / 71.49 | 83.20 / 82.98 / 95.29 |
| GPT | moderate | 62.31 / 63.78 / 60.60 | 64.71 / 65.16 / 67.42 | 98.11 / 98.21 / 97.97 |
| GPT | tight | 19.15 / 20.28 / 21.89 | 51.58 / 58.82 / 62.44 | 96.64 / 96.05 / 97.27 |
| Gemini* | moderate | 65.20 / 68.11 / 68.04 | 80.54 / 87.33 / 97.74 | 98.82 / 98.82 / 98.84 |
| Gemini* | tight | 20.43 / 20.90 / 33.40 | 68.78 / 71.49 / 73.76 | 95.93 / 96.05 / 97.57 |

## 家族与预算排名

[dimension_rankings.csv](dimension_rankings.csv)含 7 维 × 6 模型 × 3 预算，缺失保留；只有六模型完整时标记全体冠军，并列保持。

[完整聚合](absolute_settings.csv) · [逐重复](by_repeat.csv) · [合并比较](COMPARISON.csv) · [逐字段变化](CHANGES.csv) · [4698 项来源](SOURCE_SELECTION.csv) · [逐项分数](slot_scalars.csv) · [输入哈希](INPUTS.json) · [检查结果](CHECKS.json)

原有 Search / Audit N1 分数不变。本次补齐会改变 Gemini HPO 完整均值、相关家族与模型排名、N4 Search Moderate naive 及部分 NAS 端点。不得将旧报告中的“未齐”、冠军数、三策略完整组数或宏均值描述直接复制为本版结论。

## 本版重新计算的结论

N1 Free→Tight：Search 6/6、Audit 6/6、HPO 5/6 个完整模型下降。

PoolAct 三策略比较完整 36/36 组，其中 31 组严格高于 naive 与 cached；Tight 为 17/18。这是当前任务与设置下的方向计数。

以下 7 个维度在 Free/Tight 均具六模型完整结果，其中 5 个第一名集合改变。Audit LA 与 EA 是同一 Audit 场景的两个指标，不能当作两个独立任务。

| 维度 | Free 第一名 | Moderate 第一名 | Tight 第一名 |
| --- | --- | --- | --- |
| Search whois | Gemini* | GLM | GLM |
| Search whatis | Gemini* | Gemini* | DeepSeek |
| Audit EA | Gemini* | Gemini* | Gemini* |
| Audit LA | Gemini* | Gemini* | Gemini* |
| ParamNet | GPT | GPT | Gemini* |
| NAS101 | Gemini* | Gemini* | GPT |
| NAS201 | Kimi | Gemini* | Gemini* |

汇总数字见 [FINDINGS.json](FINDINGS.json)。不跨场景合成总分，不据此作显著性或单一提供方效应的因果判断。
