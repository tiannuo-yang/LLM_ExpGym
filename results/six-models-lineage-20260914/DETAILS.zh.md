# 六模型详细报告

[主报告](README.zh.md) · [实验记录](EXPERIMENT_LOG.zh.md) · [数据来源](DATA_LINEAGE.zh.md) · [完整存档](ARCHIVE_INDEX.md)

## 设置与口径

Custom study：复用冻结分数，按用户要求限定六模型。原始分数、正常缺答、负值、失败与未完成全部保留在各自口径内。没有新增实验、重评分或重新选择成功任务。

ExpGym N1：Search 73 题（whois 39、whatis 34）R1；Audit 13 文档 × 3 固定顺序；HPO 9 任务 × 3 重复。PoolAct N4：whois 39 题、Audit 13 文档，均 R1；NAS101 A/B/C × 3 重复；Moderate/Tight × naive/cached/poolact。N4 的 Free 未计划。

Free 隐藏且不限制模拟反馈成本，但仍受步骤、上下文及输出上限约束。Moderate=10×、Tight=3× 基准成本；Search/Audit 基准 300 秒，HPO 使用冻结 oracle best_cost。真实推理时间不是模拟反馈成本。

先在 item 内平均重复/顺序，再对 item 等权平均；Audit 三顺序不是三次独立生成重复，N4 四名 agent 不是四次独立重复。沿用原 legacy HPO 最终配置选择规则，不改为 submitted-only。

F1/EA/LA 比例显示为 0–100；Gap/Gap0 为原 points。MV=原投票聚合，MI=池内个体分数均值，BoN=原最佳成员端点；端点之间不互换。`[known/expected]` 使用来源导出的分析单元，不是 API 请求数；Audit 的一些导出已折叠顺序，另一些保留 39 单元，两者都按原 item 权重读数。

完整均值缺失时写 unknown；已知子集均值单独列，不填完整端点。Gap0 仅对正常结束而缺有效 HPO 配置的成员赋 0；严格 Gap/Gap-MI 仍未知，失败、暂停、未启动不补零。

不同模型的 effort、native/text 协议、API/自托管部署和执行源码并不完全相同；9 月 12 日定向重跑同时涉及代码/提示与部署变动，不能把前后差异全部归因于一个 bug。具体身份、日期和整组替换记录见数据来源与实验日志。

Gemini 已完成 767/783，9 月 14 日 23:45 UTC 检查与 9 月 13 日快照一致。1 个 Search Moderate naive 池失败，15 个未完成项集中在 HPO 第三重复：N1 6 项、N4 9 项；不能假设缺失随机。

## ExpGym N1：完整预算

### Search — F1

| 模型 | Free | Moderate | Tight | Δ M−F | Δ T−M | Δ T−F |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | 63.59 [73/73] | 49.62 [73/73] | 15.76 [73/73] | -13.97 | -33.86 | -47.83 |
| GLM 5.3 | 65.11 [73/73] | 53.28 [73/73] | 19.23 [73/73] | -11.83 | -34.04 | -45.88 |
| Qwen 3.8 | 58.15 [73/73] | 50.98 [73/73] | 18.47 [73/73] | -7.17 | -32.51 | -39.68 |
| DeepSeek V4 Flash | 43.81 [73/73] | 42.11 [73/73] | 16.92 [73/73] | -1.70 | -25.19 | -26.89 |
| GPT-5.6-sol | 64.01 [73/73] | 53.06 [73/73] | 15.55 [73/73] | -10.95 | -37.51 | -48.46 |
| Gemini 3.8 Flash | 72.03 [73/73] | 55.02 [73/73] | 17.83 [73/73] | -17.01 | -37.19 | -54.20 |

### Audit — EvidenceAcc

| 模型 | Free | Moderate | Tight | Δ M−F | Δ T−M | Δ T−F |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | 89.44 [13/13] | 68.78 [13/13] | 51.58 [13/13] | -20.66 | -17.19 | -37.86 |
| GLM 5.3 | 68.48 [13/13] | 67.87 [13/13] | 50.23 [13/13] | -0.60 | -17.65 | -18.25 |
| Qwen 3.8 | 91.86 [13/13] | 74.96 [13/13] | 58.37 [13/13] | -16.89 | -16.59 | -33.48 |
| DeepSeek V4 Flash | 63.95 [13/13] | 58.67 [13/13] | 47.51 [13/13] | -5.28 | -11.16 | -16.44 |
| GPT-5.6-sol | 70.44 [13/13] | 65.91 [13/13] | 54.15 [13/13] | -4.52 | -11.76 | -16.29 |
| Gemini 3.8 Flash | 97.59 [39/39] | 82.81 [39/39] | 72.10 [39/39] | -14.78 | -10.71 | -25.49 |

### HPO — Gap0

| 模型 | Free | Moderate | Tight | Δ M−F | Δ T−M | Δ T−F |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | 98.51 [27/27] | 94.23 [27/27] | 89.68 [27/27] | -4.28 | -4.55 | -8.83 |
| GLM 5.3 | 97.91 [27/27] | 96.15 [27/27] | 86.07 [27/27] | -1.76 | -10.09 | -11.84 |
| Qwen 3.8 | 97.47 [27/27] | 95.13 [27/27] | 85.71 [27/27] | -2.33 | -9.42 | -11.76 |
| DeepSeek V4 Flash | 61.09 [27/27] | 74.02 [27/27] | 75.81 [27/27] | +12.93 | +1.79 | +14.72 |
| GPT-5.6-sol | 97.97 [27/27] | 96.61 [27/27] | 91.66 [27/27] | -1.36 | -4.95 | -6.31 |
| Gemini 3.8 Flash | unknown [25/27] | unknown [25/27] | unknown [25/27] | unknown | unknown | unknown |

## N4：全部预算与三种策略

### Search — F1-MV

| 模型 | 预算 | naive | cached | poolact | Δ cached−naive | Δ poolact−naive | Δ poolact−cached |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | Moderate | 64.59 [39/39] | 64.20 [39/39] | 66.74 [39/39] | -0.39 | +2.15 | +2.54 |
| Kimi K3 | Tight | 21.29 [39/39] | 18.72 [39/39] | 30.43 [39/39] | -2.56 | +9.15 | +11.71 |
| GLM 5.3 | Moderate | 62.03 [39/39] | 65.67 [39/39] | 65.74 [39/39] | +3.64 | +3.71 | +0.07 |
| GLM 5.3 | Tight | 20.86 [39/39] | 20.86 [39/39] | 30.01 [39/39] | +0.00 | +9.15 | +9.15 |
| Qwen 3.8 | Moderate | 61.21 [39/39] | 61.17 [39/39] | 63.48 [39/39] | -0.04 | +2.27 | +2.31 |
| Qwen 3.8 | Tight | 18.30 [39/39] | 23.31 [39/39] | 20.69 [39/39] | +5.02 | +2.39 | -2.63 |
| DeepSeek V4 Flash | Moderate | 60.27 [39/39] | 61.80 [39/39] | 61.33 [39/39] | +1.53 | +1.05 | -0.47 |
| DeepSeek V4 Flash | Tight | 2.56 [39/39] | 4.27 [39/39] | 7.44 [39/39] | +1.71 | +4.88 | +3.17 |
| GPT-5.6-sol | Moderate | 62.31 [39/39] | 63.78 [39/39] | 60.60 [39/39] | +1.47 | -1.71 | -3.17 |
| GPT-5.6-sol | Tight | 19.15 [39/39] | 20.28 [39/39] | 21.89 [39/39] | +1.13 | +2.74 | +1.61 |
| Gemini 3.8 Flash | Moderate | unknown [38/39] | 68.11 [39/39] | 68.04 [39/39] | unknown | unknown | -0.07 |
| Gemini 3.8 Flash | Tight | 20.43 [39/39] | 20.90 [39/39] | 33.40 [39/39] | +0.47 | +12.97 | +12.50 |

### Audit — EvidenceAcc-MV

| 模型 | 预算 | naive | cached | poolact | Δ cached−naive | Δ poolact−naive | Δ poolact−cached |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | Moderate | 73.76 [13/13] | 76.47 [13/13] | 93.67 [13/13] | +2.71 | +19.91 | +17.19 |
| Kimi K3 | Tight | 55.20 [13/13] | 54.75 [13/13] | 62.90 [13/13] | -0.45 | +7.69 | +8.14 |
| GLM 5.3 | Moderate | 81.00 [13/13] | 84.62 [13/13] | 97.74 [13/13] | +3.62 | +16.74 | +13.12 |
| GLM 5.3 | Tight | 66.06 [13/13] | 65.61 [13/13] | 81.90 [13/13] | -0.45 | +15.84 | +16.29 |
| Qwen 3.8 | Moderate | 68.78 [13/13] | 74.66 [13/13] | 93.67 [13/13] | +5.88 | +24.89 | +19.00 |
| Qwen 3.8 | Tight | 56.11 [13/13] | 60.18 [13/13] | 63.80 [13/13] | +4.07 | +7.69 | +3.62 |
| DeepSeek V4 Flash | Moderate | 69.68 [13/13] | 72.40 [13/13] | 94.57 [13/13] | +2.71 | +24.89 | +22.17 |
| DeepSeek V4 Flash | Tight | 61.99 [13/13] | 61.99 [13/13] | 71.49 [13/13] | +0.00 | +9.50 | +9.50 |
| GPT-5.6-sol | Moderate | 64.71 [13/13] | 65.16 [13/13] | 67.42 [13/13] | +0.45 | +2.71 | +2.26 |
| GPT-5.6-sol | Tight | 51.58 [13/13] | 58.82 [13/13] | 62.44 [13/13] | +7.24 | +10.86 | +3.62 |
| Gemini 3.8 Flash | Moderate | 80.54 [13/13] | 87.33 [13/13] | 97.74 [13/13] | +6.79 | +17.19 | +10.41 |
| Gemini 3.8 Flash | Tight | 68.78 [13/13] | 71.49 [13/13] | 73.76 [13/13] | +2.71 | +4.98 | +2.26 |

### HPO — Gap0-MI

| 模型 | 预算 | naive | cached | poolact | Δ cached−naive | Δ poolact−naive | Δ poolact−cached |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | Moderate | 98.04 [9/9] | 97.96 [9/9] | 98.56 [9/9] | -0.08 | +0.52 | +0.60 |
| Kimi K3 | Tight | 93.65 [9/9] | 92.95 [9/9] | 95.52 [9/9] | -0.70 | +1.87 | +2.57 |
| GLM 5.3 | Moderate | 97.87 [9/9] | 98.06 [9/9] | 98.97 [9/9] | +0.19 | +1.09 | +0.90 |
| GLM 5.3 | Tight | 85.93 [9/9] | 86.57 [9/9] | 94.33 [9/9] | +0.64 | +8.40 | +7.76 |
| Qwen 3.8 | Moderate | 96.92 [9/9] | 97.72 [9/9] | 98.87 [9/9] | +0.80 | +1.95 | +1.15 |
| Qwen 3.8 | Tight | 90.62 [9/9] | 90.76 [9/9] | 96.27 [9/9] | +0.14 | +5.65 | +5.51 |
| DeepSeek V4 Flash | Moderate | 96.72 [9/9] | 96.27 [9/9] | 98.74 [9/9] | -0.46 | +2.01 | +2.47 |
| DeepSeek V4 Flash | Tight | 83.20 [9/9] | 82.98 [9/9] | 95.29 [9/9] | -0.22 | +12.09 | +12.31 |
| GPT-5.6-sol | Moderate | 98.11 [9/9] | 98.21 [9/9] | 97.97 [9/9] | +0.11 | -0.14 | -0.24 |
| GPT-5.6-sol | Tight | 96.64 [9/9] | 96.05 [9/9] | 97.27 [9/9] | -0.59 | +0.63 | +1.22 |
| Gemini 3.8 Flash | Moderate | unknown [8/9] | unknown [7/9] | unknown [6/9] | unknown | unknown | unknown |
| Gemini 3.8 Flash | Tight | 95.93 [9/9] | unknown [7/9] | unknown [8/9] | unknown | unknown | unknown |

## HPO：严格 Gap 与 Gap0 分开

未知旁括号内为已知子集均值，只供核查，不进入完整组比较。

### N1 严格 Gap

| 模型 | 预算 | single |
| --- | --- | --- |
| Kimi K3 | Free | 98.51 [27/27] |
| Kimi K3 | Moderate | 94.23 [27/27] |
| Kimi K3 | Tight | 89.68 [27/27] |
| GLM 5.3 | Free | 97.91 [27/27] |
| GLM 5.3 | Moderate | 96.15 [27/27] |
| GLM 5.3 | Tight | 86.07 [27/27] |
| Qwen 3.8 | Free | 97.47 [27/27] |
| Qwen 3.8 | Moderate | 95.13 [27/27] |
| Qwen 3.8 | Tight | 85.71 [27/27] |
| DeepSeek V4 Flash | Free | unknown [20/27]（已知子集 81.72） |
| DeepSeek V4 Flash | Moderate | unknown [25/27]（已知子集 79.38） |
| DeepSeek V4 Flash | Tight | unknown [25/27]（已知子集 81.89） |
| GPT-5.6-sol | Free | 97.97 [27/27] |
| GPT-5.6-sol | Moderate | 96.61 [27/27] |
| GPT-5.6-sol | Tight | 91.66 [27/27] |
| Gemini 3.8 Flash | Free | unknown [25/27]（已知子集 98.16） |
| Gemini 3.8 Flash | Moderate | unknown [25/27]（已知子集 97.33） |
| Gemini 3.8 Flash | Tight | unknown [25/27]（已知子集 93.81） |

### N4 严格 Gap-MI

| 模型 | 预算 | naive | cached | poolact |
| --- | --- | --- | --- | --- |
| Kimi K3 | Moderate | 98.04 [9/9] | 97.96 [9/9] | 98.56 [9/9] |
| Kimi K3 | Tight | 93.65 [9/9] | 92.95 [9/9] | 95.52 [9/9] |
| GLM 5.3 | Moderate | 97.87 [9/9] | 98.06 [9/9] | 98.97 [9/9] |
| GLM 5.3 | Tight | 85.93 [9/9] | 86.57 [9/9] | 94.33 [9/9] |
| Qwen 3.8 | Moderate | 96.92 [9/9] | 97.72 [9/9] | 98.87 [9/9] |
| Qwen 3.8 | Tight | 90.62 [9/9] | 90.76 [9/9] | 96.27 [9/9] |
| DeepSeek V4 Flash | Moderate | 96.72 [9/9] | 96.27 [9/9] | 98.74 [9/9] |
| DeepSeek V4 Flash | Tight | 83.20 [9/9] | 82.98 [9/9] | 95.29 [9/9] |
| GPT-5.6-sol | Moderate | 98.11 [9/9] | 98.21 [9/9] | 97.97 [9/9] |
| GPT-5.6-sol | Tight | 96.64 [9/9] | 96.05 [9/9] | 97.27 [9/9] |
| Gemini 3.8 Flash | Moderate | unknown [8/9]（已知子集 98.80） | unknown [7/9]（已知子集 98.81） | unknown [6/9]（已知子集 98.75） |
| Gemini 3.8 Flash | Tight | 95.93 [9/9] | unknown [7/9]（已知子集 96.33） | unknown [8/9]（已知子集 97.90） |

## 家族分数与排名

只比较 N1；每行同时给六模型分数，unknown 保留。全候选未齐时不宣布全体最佳。

### whois

| 预算 | Kimi K3 | GLM 5.3 | Qwen 3.8 | DeepSeek V4 Flash | GPT-5.6-sol | Gemini 3.8 Flash | 已知最高及资格 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Free | 65.89 | 68.27 | 64.11 | 49.83 | 62.78 | 73.86 | Gemini 3.8 Flash 73.86 |
| Moderate | 57.30 | 64.28 | 61.13 | 49.75 | 59.75 | 62.77 | GLM 5.3 64.28 |
| Tight | 17.01 | 23.06 | 22.57 | 17.78 | 17.01 | 20.43 | GLM 5.3 23.06 |

### whatis

| 预算 | Kimi K3 | GLM 5.3 | Qwen 3.8 | DeepSeek V4 Flash | GPT-5.6-sol | Gemini 3.8 Flash | 已知最高及资格 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Free | 60.96 | 61.49 | 51.31 | 36.91 | 65.42 | 69.93 | Gemini 3.8 Flash 69.93 |
| Moderate | 40.80 | 40.65 | 39.35 | 33.35 | 45.39 | 46.13 | Gemini 3.8 Flash 46.13 |
| Tight | 14.31 | 14.85 | 13.77 | 15.93 | 13.87 | 14.85 | DeepSeek V4 Flash 15.93 |

### evidence_audit

| 预算 | Kimi K3 | GLM 5.3 | Qwen 3.8 | DeepSeek V4 Flash | GPT-5.6-sol | Gemini 3.8 Flash | 已知最高及资格 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Free | 89.44 | 68.48 | 91.86 | 63.95 | 70.44 | 97.59 | Gemini 3.8 Flash 97.59 |
| Moderate | 68.78 | 67.87 | 74.96 | 58.67 | 65.91 | 82.81 | Gemini 3.8 Flash 82.81 |
| Tight | 51.58 | 50.23 | 58.37 | 47.51 | 54.15 | 72.10 | Gemini 3.8 Flash 72.10 |

### paramnet

| 预算 | Kimi K3 | GLM 5.3 | Qwen 3.8 | DeepSeek V4 Flash | GPT-5.6-sol | Gemini 3.8 Flash | 已知最高及资格 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Free | 97.08 | 96.04 | 95.28 | 41.56 | 97.31 | unknown | 未齐；已知最高 GPT-5.6-sol 97.31 |
| Moderate | 87.76 | 94.24 | 94.95 | 70.84 | 95.27 | 93.95 | GPT-5.6-sol 95.27 |
| Tight | 79.42 | 79.40 | 77.87 | 63.94 | 85.69 | unknown | 未齐；已知最高 GPT-5.6-sol 85.69 |

### nasbench101

| 预算 | Kimi K3 | GLM 5.3 | Qwen 3.8 | DeepSeek V4 Flash | GPT-5.6-sol | Gemini 3.8 Flash | 已知最高及资格 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Free | 98.69 | 99.06 | 98.66 | 60.10 | 98.38 | 99.33 | Gemini 3.8 Flash 99.33 |
| Moderate | 97.86 | 97.74 | 96.51 | 71.88 | 98.32 | unknown | 未齐；已知最高 GPT-5.6-sol 98.32 |
| Tight | 94.97 | 90.76 | 93.82 | 86.86 | 97.03 | unknown | 未齐；已知最高 GPT-5.6-sol 97.03 |

### nasbench201

| 预算 | Kimi K3 | GLM 5.3 | Qwen 3.8 | DeepSeek V4 Flash | GPT-5.6-sol | Gemini 3.8 Flash | 已知最高及资格 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Free | 99.77 | 98.64 | 98.45 | 81.62 | 98.23 | 99.15 | Kimi K3 99.77 |
| Moderate | 97.08 | 96.49 | 93.94 | 79.34 | 96.24 | 99.12 | Gemini 3.8 Flash 99.12 |
| Tight | 94.66 | 88.04 | 85.45 | 76.62 | 92.26 | 94.87 | Gemini 3.8 Flash 94.87 |

完整排名：[family_rankings.csv](family_rankings.csv)；同一全预算已知候选集上的重排：[rank_transitions.csv](rank_transitions.csv)。后者显式记录缺失候选，不能用子集排名宣称六模型冠军。

## 全场景所有端点

以下不只列主指标；逐任务/家族、全设置和次指标全量行见 [absolute_settings.csv](absolute_settings.csv)。已知子集与完整均值分列。

| 模型 | 系统 | 场景 | 预算 | 策略 | 指标 | 完整均值 [known/expected] | 已知子集均值 | 来源 cohort |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek V4 Flash | expgym | Audit | Free | single | evidence_acc | 63.95 [13/13] | 63.95 | deepseek_original |
| DeepSeek V4 Flash | expgym | Audit | Free | single | label_acc | 66.82 [13/13] | 66.82 | deepseek_original |
| DeepSeek V4 Flash | expgym | Audit | Moderate | single | evidence_acc | 58.67 [13/13] | 58.67 | deepseek_original |
| DeepSeek V4 Flash | expgym | Audit | Moderate | single | label_acc | 75.57 [13/13] | 75.57 | deepseek_original |
| DeepSeek V4 Flash | expgym | Audit | Tight | single | evidence_acc | 47.51 [13/13] | 47.51 | deepseek_original |
| DeepSeek V4 Flash | expgym | Audit | Tight | single | label_acc | 70.29 [13/13] | 70.29 | deepseek_original |
| DeepSeek V4 Flash | expgym | Search | Free | single | f1 | 43.81 [73/73] | 43.81 | deepseek_original |
| DeepSeek V4 Flash | expgym | Search | Moderate | single | f1 | 42.11 [73/73] | 42.11 | deepseek_original |
| DeepSeek V4 Flash | expgym | Search | Tight | single | f1 | 16.92 [73/73] | 16.92 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Free | single | gap | unknown [20/27] | 81.72 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Free | single | gap0 | 61.09 [27/27] | 61.09 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Free | single | raw_perf | unknown [20/27] | 0.76 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Moderate | single | gap | unknown [25/27] | 79.38 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Moderate | single | gap0 | 74.02 [27/27] | 74.02 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Moderate | single | raw_perf | unknown [25/27] | 0.72 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Tight | single | gap | unknown [25/27] | 81.89 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Tight | single | gap0 | 75.81 [27/27] | 75.81 | deepseek_original |
| DeepSeek V4 Flash | expgym | HPO | Tight | single | raw_perf | unknown [25/27] | 0.79 | deepseek_original |
| DeepSeek V4 Flash | poolact | Audit | Moderate | cached | evidence_acc_mi | 71.27 [13/13] | 71.27 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | cached | evidence_acc_mv | 72.40 [13/13] | 72.40 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | cached | label_acc_mi | 89.48 [13/13] | 89.48 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | cached | label_acc_mv | 93.21 [13/13] | 93.21 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | naive | evidence_acc_mi | 66.74 [13/13] | 66.74 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | naive | evidence_acc_mv | 69.68 [13/13] | 69.68 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | naive | label_acc_mi | 85.97 [13/13] | 85.97 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | naive | label_acc_mv | 91.86 [13/13] | 91.86 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | poolact | evidence_acc_mi | 94.68 [13/13] | 94.68 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | poolact | evidence_acc_mv | 94.57 [13/13] | 94.57 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | poolact | label_acc_mi | 96.15 [13/13] | 96.15 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Moderate | poolact | label_acc_mv | 96.38 [13/13] | 96.38 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | cached | evidence_acc_mi | 58.94 [13/13] | 58.94 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | cached | evidence_acc_mv | 61.99 [13/13] | 61.99 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | cached | label_acc_mi | 84.62 [13/13] | 84.62 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | cached | label_acc_mv | 89.59 [13/13] | 89.59 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | naive | evidence_acc_mi | 60.97 [13/13] | 60.97 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | naive | evidence_acc_mv | 61.99 [13/13] | 61.99 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | naive | label_acc_mi | 86.88 [13/13] | 86.88 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | naive | label_acc_mv | 89.14 [13/13] | 89.14 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | poolact | evidence_acc_mi | 70.59 [13/13] | 70.59 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | poolact | evidence_acc_mv | 71.49 [13/13] | 71.49 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | poolact | label_acc_mi | 90.72 [13/13] | 90.72 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Audit | Tight | poolact | label_acc_mv | 92.76 [13/13] | 92.76 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Search | Moderate | cached | f1_mi | 60.88 [39/39] | 60.88 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Search | Moderate | cached | f1_mv | 61.80 [39/39] | 61.80 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Search | Moderate | naive | f1_mi | 58.36 [39/39] | 58.36 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Search | Moderate | naive | f1_mv | 60.27 [39/39] | 60.27 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Search | Moderate | poolact | f1_mi | 60.02 [39/39] | 60.02 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Search | Moderate | poolact | f1_mv | 61.33 [39/39] | 61.33 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | Search | Tight | cached | f1_mi | 4.70 [39/39] | 4.70 | deepseek_original |
| DeepSeek V4 Flash | poolact | Search | Tight | cached | f1_mv | 4.27 [39/39] | 4.27 | deepseek_original |
| DeepSeek V4 Flash | poolact | Search | Tight | naive | f1_mi | 2.56 [39/39] | 2.56 | deepseek_original |
| DeepSeek V4 Flash | poolact | Search | Tight | naive | f1_mv | 2.56 [39/39] | 2.56 | deepseek_original |
| DeepSeek V4 Flash | poolact | Search | Tight | poolact | f1_mi | 5.49 [39/39] | 5.49 | deepseek_original |
| DeepSeek V4 Flash | poolact | Search | Tight | poolact | f1_mv | 7.44 [39/39] | 7.44 | deepseek_original |
| DeepSeek V4 Flash | poolact | HPO | Moderate | cached | gap0_bon | 98.80 [9/9] | 98.80 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | cached | gap0_mi | 96.27 [9/9] | 96.27 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | cached | gap_bon | 98.80 [9/9] | 98.80 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | cached | gap_mi | 96.27 [9/9] | 96.27 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | cached | raw_perf_bon | 0.94 [9/9] | 0.94 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | cached | raw_perf_mi | 0.93 [9/9] | 0.93 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | naive | gap0_bon | 98.70 [9/9] | 98.70 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | naive | gap0_mi | 96.72 [9/9] | 96.72 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | naive | gap_bon | 98.70 [9/9] | 98.70 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | naive | gap_mi | 96.72 [9/9] | 96.72 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | naive | raw_perf_bon | 0.94 [9/9] | 0.94 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | naive | raw_perf_mi | 0.93 [9/9] | 0.93 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | poolact | gap0_bon | 99.00 [9/9] | 99.00 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | poolact | gap0_mi | 98.74 [9/9] | 98.74 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | poolact | gap_bon | 99.00 [9/9] | 99.00 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | poolact | gap_mi | 98.74 [9/9] | 98.74 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Moderate | poolact | raw_perf_mi | 0.94 [9/9] | 0.94 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | cached | gap0_bon | 95.21 [9/9] | 95.21 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | cached | gap0_mi | 82.98 [9/9] | 82.98 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | cached | gap_bon | 95.21 [9/9] | 95.21 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | cached | gap_mi | 82.98 [9/9] | 82.98 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | cached | raw_perf_bon | 0.92 [9/9] | 0.92 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | cached | raw_perf_mi | 0.85 [9/9] | 0.85 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | naive | gap0_bon | 94.88 [9/9] | 94.88 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | naive | gap0_mi | 83.20 [9/9] | 83.20 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | naive | gap_bon | 94.88 [9/9] | 94.88 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | naive | gap_mi | 83.20 [9/9] | 83.20 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | naive | raw_perf_bon | 0.92 [9/9] | 0.92 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | naive | raw_perf_mi | 0.85 [9/9] | 0.85 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | poolact | gap0_bon | 98.28 [9/9] | 98.28 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | poolact | gap0_mi | 95.29 [9/9] | 95.29 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | poolact | gap_bon | 98.28 [9/9] | 98.28 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | poolact | gap_mi | 95.29 [9/9] | 95.29 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | deepseek_rerun_20260912 |
| DeepSeek V4 Flash | poolact | HPO | Tight | poolact | raw_perf_mi | 0.92 [9/9] | 0.92 | deepseek_rerun_20260912 |
| Gemini 3.8 Flash | expgym | Audit | Free | single | evidence_acc | 97.59 [39/39] | 97.59 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | Audit | Free | single | label_acc | 97.29 [39/39] | 97.29 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | Audit | Moderate | single | evidence_acc | 82.81 [39/39] | 82.81 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | Audit | Moderate | single | label_acc | 92.31 [39/39] | 92.31 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | Audit | Tight | single | evidence_acc | 72.10 [39/39] | 72.10 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | Audit | Tight | single | label_acc | 88.24 [39/39] | 88.24 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | Search | Free | single | f1 | 72.03 [73/73] | 72.03 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | Search | Moderate | single | f1 | 55.02 [73/73] | 55.02 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | Search | Tight | single | f1 | 17.83 [73/73] | 17.83 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Free | single | gap | unknown [25/27] | 98.16 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Free | single | gap0 | unknown [25/27] | 98.16 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Free | single | raw_perf | unknown [25/27] | 0.83 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Moderate | single | gap | unknown [25/27] | 97.33 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Moderate | single | gap0 | unknown [25/27] | 97.33 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Moderate | single | raw_perf | unknown [25/27] | 0.83 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Tight | single | gap | unknown [25/27] | 93.81 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Tight | single | gap0 | unknown [25/27] | 93.81 | gemini_snapshot |
| Gemini 3.8 Flash | expgym | HPO | Tight | single | raw_perf | unknown [25/27] | 0.82 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | cached | evidence_acc_mi | 84.16 [13/13] | 84.16 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | cached | evidence_acc_mv | 87.33 [13/13] | 87.33 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | cached | label_acc_mi | 92.42 [13/13] | 92.42 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | cached | label_acc_mv | 94.12 [13/13] | 94.12 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | naive | evidence_acc_mi | 80.09 [13/13] | 80.09 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | naive | evidence_acc_mv | 80.54 [13/13] | 80.54 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | naive | label_acc_mi | 90.61 [13/13] | 90.61 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | naive | label_acc_mv | 91.40 [13/13] | 91.40 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | poolact | evidence_acc_mi | 97.17 [13/13] | 97.17 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | poolact | evidence_acc_mv | 97.74 [13/13] | 97.74 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | poolact | label_acc_mi | 96.04 [13/13] | 96.04 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Moderate | poolact | label_acc_mv | 96.38 [13/13] | 96.38 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | cached | evidence_acc_mi | 69.57 [13/13] | 69.57 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | cached | evidence_acc_mv | 71.49 [13/13] | 71.49 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | cached | label_acc_mi | 87.10 [13/13] | 87.10 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | cached | label_acc_mv | 88.24 [13/13] | 88.24 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | naive | evidence_acc_mi | 69.34 [13/13] | 69.34 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | naive | evidence_acc_mv | 68.78 [13/13] | 68.78 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | naive | label_acc_mi | 87.44 [13/13] | 87.44 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | naive | label_acc_mv | 88.24 [13/13] | 88.24 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | poolact | evidence_acc_mi | 73.30 [13/13] | 73.30 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | poolact | evidence_acc_mv | 73.76 [13/13] | 73.76 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | poolact | label_acc_mi | 87.78 [13/13] | 87.78 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Audit | Tight | poolact | label_acc_mv | 87.78 [13/13] | 87.78 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Moderate | cached | f1_mi | 67.62 [39/39] | 67.62 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Moderate | cached | f1_mv | 68.11 [39/39] | 68.11 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Moderate | naive | f1_mi | unknown [38/39] | 63.42 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Moderate | naive | f1_mv | unknown [38/39] | 64.29 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Moderate | poolact | f1_mi | 68.36 [39/39] | 68.36 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Moderate | poolact | f1_mv | 68.04 [39/39] | 68.04 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Tight | cached | f1_mi | 20.44 [39/39] | 20.44 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Tight | cached | f1_mv | 20.90 [39/39] | 20.90 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Tight | naive | f1_mi | 21.07 [39/39] | 21.07 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Tight | naive | f1_mv | 20.43 [39/39] | 20.43 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Tight | poolact | f1_mi | 30.23 [39/39] | 30.23 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | Search | Tight | poolact | f1_mv | 33.40 [39/39] | 33.40 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | cached | gap0_bon | unknown [7/9] | 99.23 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | cached | gap0_mi | unknown [7/9] | 98.81 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | cached | gap_bon | unknown [7/9] | 99.23 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | cached | gap_mi | unknown [7/9] | 98.81 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | cached | raw_perf_bon | unknown [7/9] | 0.94 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | cached | raw_perf_mi | unknown [7/9] | 0.94 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | naive | gap0_bon | unknown [8/9] | 99.50 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | naive | gap0_mi | unknown [8/9] | 98.80 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | naive | gap_bon | unknown [8/9] | 99.50 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | naive | gap_mi | unknown [8/9] | 98.80 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | naive | raw_perf_bon | unknown [8/9] | 0.95 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | naive | raw_perf_mi | unknown [8/9] | 0.94 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | poolact | gap0_bon | unknown [6/9] | 99.12 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | poolact | gap0_mi | unknown [6/9] | 98.75 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | poolact | gap_bon | unknown [6/9] | 99.12 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | poolact | gap_mi | unknown [6/9] | 98.75 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | poolact | raw_perf_bon | unknown [6/9] | 0.94 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Moderate | poolact | raw_perf_mi | unknown [6/9] | 0.94 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | cached | gap0_bon | unknown [7/9] | 98.07 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | cached | gap0_mi | unknown [7/9] | 96.33 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | cached | gap_bon | unknown [7/9] | 98.07 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | cached | gap_mi | unknown [7/9] | 96.33 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | cached | raw_perf_bon | unknown [7/9] | 0.94 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | cached | raw_perf_mi | unknown [7/9] | 0.93 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | naive | gap0_bon | 98.88 [9/9] | 98.88 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | naive | gap0_mi | 95.93 [9/9] | 95.93 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | naive | gap_bon | 98.88 [9/9] | 98.88 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | naive | gap_mi | 95.93 [9/9] | 95.93 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | naive | raw_perf_bon | 0.94 [9/9] | 0.94 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | naive | raw_perf_mi | 0.92 [9/9] | 0.92 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | poolact | gap0_bon | unknown [8/9] | 98.67 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | poolact | gap0_mi | unknown [8/9] | 97.90 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | poolact | gap_bon | unknown [8/9] | 98.67 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | poolact | gap_mi | unknown [8/9] | 97.90 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | poolact | raw_perf_bon | unknown [8/9] | 0.94 | gemini_snapshot |
| Gemini 3.8 Flash | poolact | HPO | Tight | poolact | raw_perf_mi | unknown [8/9] | 0.94 | gemini_snapshot |
| GLM 5.3 | expgym | Audit | Free | single | evidence_acc | 68.48 [13/13] | 68.48 | glm_original |
| GLM 5.3 | expgym | Audit | Free | single | label_acc | 69.23 [13/13] | 69.23 | glm_original |
| GLM 5.3 | expgym | Audit | Moderate | single | evidence_acc | 67.87 [13/13] | 67.87 | glm_original |
| GLM 5.3 | expgym | Audit | Moderate | single | label_acc | 76.02 [13/13] | 76.02 | glm_original |
| GLM 5.3 | expgym | Audit | Tight | single | evidence_acc | 50.23 [13/13] | 50.23 | glm_original |
| GLM 5.3 | expgym | Audit | Tight | single | label_acc | 73.60 [13/13] | 73.60 | glm_original |
| GLM 5.3 | expgym | Search | Free | single | f1 | 65.11 [73/73] | 65.11 | glm_original |
| GLM 5.3 | expgym | Search | Moderate | single | f1 | 53.28 [73/73] | 53.28 | glm_original |
| GLM 5.3 | expgym | Search | Tight | single | f1 | 19.23 [73/73] | 19.23 | glm_original |
| GLM 5.3 | expgym | HPO | Free | single | gap | 97.91 [27/27] | 97.91 | glm_original |
| GLM 5.3 | expgym | HPO | Free | single | gap0 | 97.91 [27/27] | 97.91 | glm_original |
| GLM 5.3 | expgym | HPO | Free | single | raw_perf | 0.83 [27/27] | 0.83 | glm_original |
| GLM 5.3 | expgym | HPO | Moderate | single | gap | 96.15 [27/27] | 96.15 | glm_original |
| GLM 5.3 | expgym | HPO | Moderate | single | gap0 | 96.15 [27/27] | 96.15 | glm_original |
| GLM 5.3 | expgym | HPO | Moderate | single | raw_perf | 0.82 [27/27] | 0.82 | glm_original |
| GLM 5.3 | expgym | HPO | Tight | single | gap | 86.07 [27/27] | 86.07 | glm_original |
| GLM 5.3 | expgym | HPO | Tight | single | gap0 | 86.07 [27/27] | 86.07 | glm_original |
| GLM 5.3 | expgym | HPO | Tight | single | raw_perf | 0.80 [27/27] | 0.80 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | cached | evidence_acc_mi | 66.86 [13/13] | 66.86 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | cached | evidence_acc_mv | 84.62 [13/13] | 84.62 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | cached | label_acc_mi | 75.34 [13/13] | 75.34 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | cached | label_acc_mv | 93.67 [13/13] | 93.67 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | naive | evidence_acc_mi | 65.50 [13/13] | 65.50 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | naive | evidence_acc_mv | 81.00 [13/13] | 81.00 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | naive | label_acc_mi | 75.79 [13/13] | 75.79 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | naive | label_acc_mv | 92.76 [13/13] | 92.76 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | poolact | evidence_acc_mi | 80.20 [13/13] | 80.20 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | poolact | evidence_acc_mv | 97.74 [13/13] | 97.74 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | poolact | label_acc_mi | 80.88 [13/13] | 80.88 | glm_original |
| GLM 5.3 | poolact | Audit | Moderate | poolact | label_acc_mv | 98.19 [13/13] | 98.19 | glm_original |
| GLM 5.3 | poolact | Audit | Tight | cached | evidence_acc_mi | 62.90 [13/13] | 62.90 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | cached | evidence_acc_mv | 65.61 [13/13] | 65.61 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | cached | label_acc_mi | 86.65 [13/13] | 86.65 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | cached | label_acc_mv | 89.14 [13/13] | 89.14 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | naive | evidence_acc_mi | 63.46 [13/13] | 63.46 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | naive | evidence_acc_mv | 66.06 [13/13] | 66.06 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | naive | label_acc_mi | 86.65 [13/13] | 86.65 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | naive | label_acc_mv | 90.50 [13/13] | 90.50 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | poolact | evidence_acc_mi | 75.79 [13/13] | 75.79 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | poolact | evidence_acc_mv | 81.90 [13/13] | 81.90 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | poolact | label_acc_mi | 85.07 [13/13] | 85.07 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Audit | Tight | poolact | label_acc_mv | 92.31 [13/13] | 92.31 | glm_rerun_20260912 |
| GLM 5.3 | poolact | Search | Moderate | cached | f1_mi | 62.01 [39/39] | 62.01 | glm_original |
| GLM 5.3 | poolact | Search | Moderate | cached | f1_mv | 65.67 [39/39] | 65.67 | glm_original |
| GLM 5.3 | poolact | Search | Moderate | naive | f1_mi | 59.94 [39/39] | 59.94 | glm_original |
| GLM 5.3 | poolact | Search | Moderate | naive | f1_mv | 62.03 [39/39] | 62.03 | glm_original |
| GLM 5.3 | poolact | Search | Moderate | poolact | f1_mi | 65.91 [39/39] | 65.91 | glm_original |
| GLM 5.3 | poolact | Search | Moderate | poolact | f1_mv | 65.74 [39/39] | 65.74 | glm_original |
| GLM 5.3 | poolact | Search | Tight | cached | f1_mi | 20.33 [39/39] | 20.33 | glm_original |
| GLM 5.3 | poolact | Search | Tight | cached | f1_mv | 20.86 [39/39] | 20.86 | glm_original |
| GLM 5.3 | poolact | Search | Tight | naive | f1_mi | 20.33 [39/39] | 20.33 | glm_original |
| GLM 5.3 | poolact | Search | Tight | naive | f1_mv | 20.86 [39/39] | 20.86 | glm_original |
| GLM 5.3 | poolact | Search | Tight | poolact | f1_mi | 24.74 [39/39] | 24.74 | glm_original |
| GLM 5.3 | poolact | Search | Tight | poolact | f1_mv | 30.01 [39/39] | 30.01 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | cached | gap0_bon | 99.12 [9/9] | 99.12 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | cached | gap0_mi | 98.06 [9/9] | 98.06 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | cached | gap_bon | 99.12 [9/9] | 99.12 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | cached | gap_mi | 98.06 [9/9] | 98.06 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | cached | raw_perf_bon | 0.94 [9/9] | 0.94 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | cached | raw_perf_mi | 0.94 [9/9] | 0.94 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | naive | gap0_bon | 99.01 [9/9] | 99.01 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | naive | gap0_mi | 97.87 [9/9] | 97.87 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | naive | gap_bon | 99.01 [9/9] | 99.01 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | naive | gap_mi | 97.87 [9/9] | 97.87 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | naive | raw_perf_bon | 0.94 [9/9] | 0.94 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | naive | raw_perf_mi | 0.94 [9/9] | 0.94 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | poolact | gap0_bon | 99.38 [9/9] | 99.38 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | poolact | gap0_mi | 98.97 [9/9] | 98.97 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | poolact | gap_bon | 99.38 [9/9] | 99.38 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | poolact | gap_mi | 98.97 [9/9] | 98.97 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | glm_original |
| GLM 5.3 | poolact | HPO | Moderate | poolact | raw_perf_mi | 0.94 [9/9] | 0.94 | glm_original |
| GLM 5.3 | poolact | HPO | Tight | cached | gap0_bon | 94.87 [9/9] | 94.87 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | cached | gap0_mi | 86.57 [9/9] | 86.57 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | cached | gap_bon | 94.87 [9/9] | 94.87 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | cached | gap_mi | 86.57 [9/9] | 86.57 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | cached | raw_perf_bon | 0.92 [9/9] | 0.92 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | cached | raw_perf_mi | 0.88 [9/9] | 0.88 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | naive | gap0_bon | 93.13 [9/9] | 93.13 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | naive | gap0_mi | 85.93 [9/9] | 85.93 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | naive | gap_bon | 93.13 [9/9] | 93.13 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | naive | gap_mi | 85.93 [9/9] | 85.93 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | naive | raw_perf_bon | 0.91 [9/9] | 0.91 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | naive | raw_perf_mi | 0.88 [9/9] | 0.88 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | poolact | gap0_bon | 98.37 [9/9] | 98.37 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | poolact | gap0_mi | 94.33 [9/9] | 94.33 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | poolact | gap_bon | 98.37 [9/9] | 98.37 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | poolact | gap_mi | 94.33 [9/9] | 94.33 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | glm_rerun_20260912 |
| GLM 5.3 | poolact | HPO | Tight | poolact | raw_perf_mi | 0.92 [9/9] | 0.92 | glm_rerun_20260912 |
| GPT-5.6-sol | expgym | Audit | Free | single | evidence_acc | 70.44 [13/13] | 70.44 | gpt_original |
| GPT-5.6-sol | expgym | Audit | Free | single | label_acc | 85.97 [13/13] | 85.97 | gpt_original |
| GPT-5.6-sol | expgym | Audit | Moderate | single | evidence_acc | 65.91 [13/13] | 65.91 | gpt_original |
| GPT-5.6-sol | expgym | Audit | Moderate | single | label_acc | 87.93 [13/13] | 87.93 | gpt_original |
| GPT-5.6-sol | expgym | Audit | Tight | single | evidence_acc | 54.15 [13/13] | 54.15 | gpt_original |
| GPT-5.6-sol | expgym | Audit | Tight | single | label_acc | 78.73 [13/13] | 78.73 | gpt_original |
| GPT-5.6-sol | expgym | Search | Free | single | f1 | 64.01 [73/73] | 64.01 | gpt_original |
| GPT-5.6-sol | expgym | Search | Moderate | single | f1 | 53.06 [73/73] | 53.06 | gpt_original |
| GPT-5.6-sol | expgym | Search | Tight | single | f1 | 15.55 [73/73] | 15.55 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Free | single | gap | 97.97 [27/27] | 97.97 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Free | single | gap0 | 97.97 [27/27] | 97.97 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Free | single | raw_perf | 0.83 [27/27] | 0.83 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Moderate | single | gap | 96.61 [27/27] | 96.61 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Moderate | single | gap0 | 96.61 [27/27] | 96.61 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Moderate | single | raw_perf | 0.83 [27/27] | 0.83 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Tight | single | gap | 91.66 [27/27] | 91.66 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Tight | single | gap0 | 91.66 [27/27] | 91.66 | gpt_original |
| GPT-5.6-sol | expgym | HPO | Tight | single | raw_perf | 0.82 [27/27] | 0.82 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | cached | evidence_acc_mi | 56.90 [13/13] | 56.90 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | cached | evidence_acc_mv | 65.16 [13/13] | 65.16 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | cached | label_acc_mi | 78.62 [13/13] | 78.62 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | cached | label_acc_mv | 87.78 [13/13] | 87.78 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | naive | evidence_acc_mi | 63.69 [13/13] | 63.69 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | naive | evidence_acc_mv | 64.71 [13/13] | 64.71 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | naive | label_acc_mi | 84.39 [13/13] | 84.39 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | naive | label_acc_mv | 84.16 [13/13] | 84.16 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | poolact | evidence_acc_mi | 59.39 [13/13] | 59.39 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | poolact | evidence_acc_mv | 67.42 [13/13] | 67.42 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | poolact | label_acc_mi | 78.17 [13/13] | 78.17 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Moderate | poolact | label_acc_mv | 86.88 [13/13] | 86.88 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | cached | evidence_acc_mi | 52.38 [13/13] | 52.38 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | cached | evidence_acc_mv | 58.82 [13/13] | 58.82 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | cached | label_acc_mi | 75.68 [13/13] | 75.68 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | cached | label_acc_mv | 83.71 [13/13] | 83.71 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | naive | evidence_acc_mi | 49.77 [13/13] | 49.77 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | naive | evidence_acc_mv | 51.58 [13/13] | 51.58 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | naive | label_acc_mi | 77.26 [13/13] | 77.26 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | naive | label_acc_mv | 79.19 [13/13] | 79.19 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | poolact | evidence_acc_mi | 59.16 [13/13] | 59.16 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | poolact | evidence_acc_mv | 62.44 [13/13] | 62.44 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | poolact | label_acc_mi | 82.81 [13/13] | 82.81 | gpt_original |
| GPT-5.6-sol | poolact | Audit | Tight | poolact | label_acc_mv | 85.97 [13/13] | 85.97 | gpt_original |
| GPT-5.6-sol | poolact | Search | Moderate | cached | f1_mi | 62.64 [39/39] | 62.64 | gpt_original |
| GPT-5.6-sol | poolact | Search | Moderate | cached | f1_mv | 63.78 [39/39] | 63.78 | gpt_original |
| GPT-5.6-sol | poolact | Search | Moderate | naive | f1_mi | 61.40 [39/39] | 61.40 | gpt_original |
| GPT-5.6-sol | poolact | Search | Moderate | naive | f1_mv | 62.31 [39/39] | 62.31 | gpt_original |
| GPT-5.6-sol | poolact | Search | Moderate | poolact | f1_mi | 57.75 [39/39] | 57.75 | gpt_original |
| GPT-5.6-sol | poolact | Search | Moderate | poolact | f1_mv | 60.60 [39/39] | 60.60 | gpt_original |
| GPT-5.6-sol | poolact | Search | Tight | cached | f1_mi | 19.25 [39/39] | 19.25 | gpt_original |
| GPT-5.6-sol | poolact | Search | Tight | cached | f1_mv | 20.28 [39/39] | 20.28 | gpt_original |
| GPT-5.6-sol | poolact | Search | Tight | naive | f1_mi | 19.58 [39/39] | 19.58 | gpt_original |
| GPT-5.6-sol | poolact | Search | Tight | naive | f1_mv | 19.15 [39/39] | 19.15 | gpt_original |
| GPT-5.6-sol | poolact | Search | Tight | poolact | f1_mi | 23.85 [39/39] | 23.85 | gpt_original |
| GPT-5.6-sol | poolact | Search | Tight | poolact | f1_mv | 21.89 [39/39] | 21.89 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Moderate | cached | gap0_bon | 99.01 [9/9] | 99.01 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | cached | gap0_mi | 98.21 [9/9] | 98.21 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | cached | gap_bon | 99.01 [9/9] | 99.01 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | cached | gap_mi | 98.21 [9/9] | 98.21 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | cached | raw_perf_bon | 0.94 [9/9] | 0.94 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | cached | raw_perf_mi | 0.94 [9/9] | 0.94 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | naive | gap0_bon | 98.74 [9/9] | 98.74 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | naive | gap0_mi | 98.11 [9/9] | 98.11 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | naive | gap_bon | 98.74 [9/9] | 98.74 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | naive | gap_mi | 98.11 [9/9] | 98.11 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | naive | raw_perf_bon | 0.94 [9/9] | 0.94 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | naive | raw_perf_mi | 0.94 [9/9] | 0.94 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | poolact | gap0_bon | 99.19 [9/9] | 99.19 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | poolact | gap0_mi | 97.97 [9/9] | 97.97 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | poolact | gap_bon | 99.19 [9/9] | 99.19 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | poolact | gap_mi | 97.97 [9/9] | 97.97 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Moderate | poolact | raw_perf_mi | 0.94 [9/9] | 0.94 | gpt_rerun_20260912 |
| GPT-5.6-sol | poolact | HPO | Tight | cached | gap0_bon | 98.30 [9/9] | 98.30 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | cached | gap0_mi | 96.05 [9/9] | 96.05 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | cached | gap_bon | 98.30 [9/9] | 98.30 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | cached | gap_mi | 96.05 [9/9] | 96.05 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | cached | raw_perf_bon | 0.94 [9/9] | 0.94 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | cached | raw_perf_mi | 0.93 [9/9] | 0.93 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | naive | gap0_bon | 98.20 [9/9] | 98.20 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | naive | gap0_mi | 96.64 [9/9] | 96.64 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | naive | gap_bon | 98.20 [9/9] | 98.20 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | naive | gap_mi | 96.64 [9/9] | 96.64 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | naive | raw_perf_bon | 0.94 [9/9] | 0.94 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | naive | raw_perf_mi | 0.93 [9/9] | 0.93 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | poolact | gap0_bon | 98.08 [9/9] | 98.08 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | poolact | gap0_mi | 97.27 [9/9] | 97.27 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | poolact | gap_bon | 98.08 [9/9] | 98.08 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | poolact | gap_mi | 97.27 [9/9] | 97.27 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | gpt_original |
| GPT-5.6-sol | poolact | HPO | Tight | poolact | raw_perf_mi | 0.94 [9/9] | 0.94 | gpt_original |
| Kimi K3 | expgym | Audit | Free | single | evidence_acc | 89.44 [13/13] | 89.44 | kimi_original |
| Kimi K3 | expgym | Audit | Free | single | label_acc | 92.61 [13/13] | 92.61 | kimi_original |
| Kimi K3 | expgym | Audit | Moderate | single | evidence_acc | 68.78 [13/13] | 68.78 | kimi_original |
| Kimi K3 | expgym | Audit | Moderate | single | label_acc | 85.37 [13/13] | 85.37 | kimi_original |
| Kimi K3 | expgym | Audit | Tight | single | evidence_acc | 51.58 [13/13] | 51.58 | kimi_original |
| Kimi K3 | expgym | Audit | Tight | single | label_acc | 79.49 [13/13] | 79.49 | kimi_original |
| Kimi K3 | expgym | Search | Free | single | f1 | 63.59 [73/73] | 63.59 | kimi_original |
| Kimi K3 | expgym | Search | Moderate | single | f1 | 49.62 [73/73] | 49.62 | kimi_original |
| Kimi K3 | expgym | Search | Tight | single | f1 | 15.76 [73/73] | 15.76 | kimi_original |
| Kimi K3 | expgym | HPO | Free | single | gap | 98.51 [27/27] | 98.51 | kimi_original |
| Kimi K3 | expgym | HPO | Free | single | gap0 | 98.51 [27/27] | 98.51 | kimi_original |
| Kimi K3 | expgym | HPO | Free | single | raw_perf | 0.83 [27/27] | 0.83 | kimi_original |
| Kimi K3 | expgym | HPO | Moderate | single | gap | 94.23 [27/27] | 94.23 | kimi_original |
| Kimi K3 | expgym | HPO | Moderate | single | gap0 | 94.23 [27/27] | 94.23 | kimi_original |
| Kimi K3 | expgym | HPO | Moderate | single | raw_perf | 0.82 [27/27] | 0.82 | kimi_original |
| Kimi K3 | expgym | HPO | Tight | single | gap | 89.68 [27/27] | 89.68 | kimi_original |
| Kimi K3 | expgym | HPO | Tight | single | gap0 | 89.68 [27/27] | 89.68 | kimi_original |
| Kimi K3 | expgym | HPO | Tight | single | raw_perf | 0.81 [27/27] | 0.81 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | cached | evidence_acc_mi | 67.08 [13/13] | 67.08 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | cached | evidence_acc_mv | 76.47 [13/13] | 76.47 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | cached | label_acc_mi | 84.05 [13/13] | 84.05 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | cached | label_acc_mv | 93.67 [13/13] | 93.67 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | naive | evidence_acc_mi | 70.25 [13/13] | 70.25 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | naive | evidence_acc_mv | 73.76 [13/13] | 73.76 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | naive | label_acc_mi | 89.48 [13/13] | 89.48 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | naive | label_acc_mv | 92.31 [13/13] | 92.31 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | poolact | evidence_acc_mi | 90.84 [13/13] | 90.84 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | poolact | evidence_acc_mv | 93.67 [13/13] | 93.67 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | poolact | label_acc_mi | 92.87 [13/13] | 92.87 | kimi_original |
| Kimi K3 | poolact | Audit | Moderate | poolact | label_acc_mv | 97.29 [13/13] | 97.29 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | cached | evidence_acc_mi | 54.30 [13/13] | 54.30 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | cached | evidence_acc_mv | 54.75 [13/13] | 54.75 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | cached | label_acc_mi | 81.11 [13/13] | 81.11 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | cached | label_acc_mv | 83.71 [13/13] | 83.71 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | naive | evidence_acc_mi | 54.52 [13/13] | 54.52 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | naive | evidence_acc_mv | 55.20 [13/13] | 55.20 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | naive | label_acc_mi | 82.24 [13/13] | 82.24 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | naive | label_acc_mv | 84.16 [13/13] | 84.16 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | poolact | evidence_acc_mi | 60.29 [13/13] | 60.29 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | poolact | evidence_acc_mv | 62.90 [13/13] | 62.90 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | poolact | label_acc_mi | 84.62 [13/13] | 84.62 | kimi_original |
| Kimi K3 | poolact | Audit | Tight | poolact | label_acc_mv | 87.33 [13/13] | 87.33 | kimi_original |
| Kimi K3 | poolact | Search | Moderate | cached | f1_mi | 63.20 [39/39] | 63.20 | kimi_original |
| Kimi K3 | poolact | Search | Moderate | cached | f1_mv | 64.20 [39/39] | 64.20 | kimi_original |
| Kimi K3 | poolact | Search | Moderate | naive | f1_mi | 62.39 [39/39] | 62.39 | kimi_original |
| Kimi K3 | poolact | Search | Moderate | naive | f1_mv | 64.59 [39/39] | 64.59 | kimi_original |
| Kimi K3 | poolact | Search | Moderate | poolact | f1_mi | 64.09 [39/39] | 64.09 | kimi_original |
| Kimi K3 | poolact | Search | Moderate | poolact | f1_mv | 66.74 [39/39] | 66.74 | kimi_original |
| Kimi K3 | poolact | Search | Tight | cached | f1_mi | 19.25 [39/39] | 19.25 | kimi_original |
| Kimi K3 | poolact | Search | Tight | cached | f1_mv | 18.72 [39/39] | 18.72 | kimi_original |
| Kimi K3 | poolact | Search | Tight | naive | f1_mi | 20.10 [39/39] | 20.10 | kimi_original |
| Kimi K3 | poolact | Search | Tight | naive | f1_mv | 21.29 [39/39] | 21.29 | kimi_original |
| Kimi K3 | poolact | Search | Tight | poolact | f1_mi | 27.24 [39/39] | 27.24 | kimi_original |
| Kimi K3 | poolact | Search | Tight | poolact | f1_mv | 30.43 [39/39] | 30.43 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | cached | gap0_bon | 98.84 [9/9] | 98.84 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | cached | gap0_mi | 97.96 [9/9] | 97.96 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | cached | gap_bon | 98.84 [9/9] | 98.84 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | cached | gap_mi | 97.96 [9/9] | 97.96 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | cached | raw_perf_bon | 0.94 [9/9] | 0.94 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | cached | raw_perf_mi | 0.94 [9/9] | 0.94 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | naive | gap0_bon | 98.99 [9/9] | 98.99 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | naive | gap0_mi | 98.04 [9/9] | 98.04 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | naive | gap_bon | 98.99 [9/9] | 98.99 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | naive | gap_mi | 98.04 [9/9] | 98.04 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | naive | raw_perf_bon | 0.94 [9/9] | 0.94 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | naive | raw_perf_mi | 0.94 [9/9] | 0.94 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | poolact | gap0_bon | 98.87 [9/9] | 98.87 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | poolact | gap0_mi | 98.56 [9/9] | 98.56 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | poolact | gap_bon | 98.87 [9/9] | 98.87 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | poolact | gap_mi | 98.56 [9/9] | 98.56 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | kimi_original |
| Kimi K3 | poolact | HPO | Moderate | poolact | raw_perf_mi | 0.94 [9/9] | 0.94 | kimi_original |
| Kimi K3 | poolact | HPO | Tight | cached | gap0_bon | 97.48 [9/9] | 97.48 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | cached | gap0_mi | 92.95 [9/9] | 92.95 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | cached | gap_bon | 97.48 [9/9] | 97.48 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | cached | gap_mi | 92.95 [9/9] | 92.95 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | cached | raw_perf_bon | 0.94 [9/9] | 0.94 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | cached | raw_perf_mi | 0.91 [9/9] | 0.91 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | naive | gap0_bon | 96.16 [9/9] | 96.16 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | naive | gap0_mi | 93.65 [9/9] | 93.65 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | naive | gap_bon | 96.16 [9/9] | 96.16 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | naive | gap_mi | 93.65 [9/9] | 93.65 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | naive | raw_perf_bon | 0.93 [9/9] | 0.93 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | naive | raw_perf_mi | 0.91 [9/9] | 0.91 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | poolact | gap0_bon | 98.20 [9/9] | 98.20 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | poolact | gap0_mi | 95.52 [9/9] | 95.52 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | poolact | gap_bon | 98.20 [9/9] | 98.20 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | poolact | gap_mi | 95.52 [9/9] | 95.52 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | kimi_rerun_20260912 |
| Kimi K3 | poolact | HPO | Tight | poolact | raw_perf_mi | 0.93 [9/9] | 0.93 | kimi_rerun_20260912 |
| Qwen 3.8 | expgym | Audit | Free | single | evidence_acc | 91.86 [13/13] | 91.86 | qwen_original |
| Qwen 3.8 | expgym | Audit | Free | single | label_acc | 94.72 [13/13] | 94.72 | qwen_original |
| Qwen 3.8 | expgym | Audit | Moderate | single | evidence_acc | 74.96 [13/13] | 74.96 | qwen_original |
| Qwen 3.8 | expgym | Audit | Moderate | single | label_acc | 88.24 [13/13] | 88.24 | qwen_original |
| Qwen 3.8 | expgym | Audit | Tight | single | evidence_acc | 58.37 [13/13] | 58.37 | qwen_original |
| Qwen 3.8 | expgym | Audit | Tight | single | label_acc | 83.11 [13/13] | 83.11 | qwen_original |
| Qwen 3.8 | expgym | Search | Free | single | f1 | 58.15 [73/73] | 58.15 | qwen_original |
| Qwen 3.8 | expgym | Search | Moderate | single | f1 | 50.98 [73/73] | 50.98 | qwen_original |
| Qwen 3.8 | expgym | Search | Tight | single | f1 | 18.47 [73/73] | 18.47 | qwen_original |
| Qwen 3.8 | expgym | HPO | Free | single | gap | 97.47 [27/27] | 97.47 | qwen_original |
| Qwen 3.8 | expgym | HPO | Free | single | gap0 | 97.47 [27/27] | 97.47 | qwen_original |
| Qwen 3.8 | expgym | HPO | Free | single | raw_perf | 0.83 [27/27] | 0.83 | qwen_original |
| Qwen 3.8 | expgym | HPO | Moderate | single | gap | 95.13 [27/27] | 95.13 | qwen_original |
| Qwen 3.8 | expgym | HPO | Moderate | single | gap0 | 95.13 [27/27] | 95.13 | qwen_original |
| Qwen 3.8 | expgym | HPO | Moderate | single | raw_perf | 0.83 [27/27] | 0.83 | qwen_original |
| Qwen 3.8 | expgym | HPO | Tight | single | gap | 85.71 [27/27] | 85.71 | qwen_original |
| Qwen 3.8 | expgym | HPO | Tight | single | gap0 | 85.71 [27/27] | 85.71 | qwen_original |
| Qwen 3.8 | expgym | HPO | Tight | single | raw_perf | 0.81 [27/27] | 0.81 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | cached | evidence_acc_mi | 71.27 [13/13] | 71.27 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | cached | evidence_acc_mv | 74.66 [13/13] | 74.66 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | cached | label_acc_mi | 89.14 [13/13] | 89.14 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | cached | label_acc_mv | 89.14 [13/13] | 89.14 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | naive | evidence_acc_mi | 67.65 [13/13] | 67.65 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | naive | evidence_acc_mv | 68.78 [13/13] | 68.78 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | naive | label_acc_mi | 89.03 [13/13] | 89.03 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | naive | label_acc_mv | 90.05 [13/13] | 90.05 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | poolact | evidence_acc_mi | 92.42 [13/13] | 92.42 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | poolact | evidence_acc_mv | 93.67 [13/13] | 93.67 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | poolact | label_acc_mi | 95.36 [13/13] | 95.36 | qwen_original |
| Qwen 3.8 | poolact | Audit | Moderate | poolact | label_acc_mv | 95.93 [13/13] | 95.93 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | cached | evidence_acc_mi | 59.05 [13/13] | 59.05 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | cached | evidence_acc_mv | 60.18 [13/13] | 60.18 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | cached | label_acc_mi | 83.71 [13/13] | 83.71 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | cached | label_acc_mv | 83.71 [13/13] | 83.71 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | naive | evidence_acc_mi | 55.20 [13/13] | 55.20 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | naive | evidence_acc_mv | 56.11 [13/13] | 56.11 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | naive | label_acc_mi | 81.67 [13/13] | 81.67 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | naive | label_acc_mv | 83.26 [13/13] | 83.26 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | poolact | evidence_acc_mi | 63.24 [13/13] | 63.24 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | poolact | evidence_acc_mv | 63.80 [13/13] | 63.80 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | poolact | label_acc_mi | 85.41 [13/13] | 85.41 | qwen_original |
| Qwen 3.8 | poolact | Audit | Tight | poolact | label_acc_mv | 85.52 [13/13] | 85.52 | qwen_original |
| Qwen 3.8 | poolact | Search | Moderate | cached | f1_mi | 59.07 [39/39] | 59.07 | qwen_original |
| Qwen 3.8 | poolact | Search | Moderate | cached | f1_mv | 61.17 [39/39] | 61.17 | qwen_original |
| Qwen 3.8 | poolact | Search | Moderate | naive | f1_mi | 58.89 [39/39] | 58.89 | qwen_original |
| Qwen 3.8 | poolact | Search | Moderate | naive | f1_mv | 61.21 [39/39] | 61.21 | qwen_original |
| Qwen 3.8 | poolact | Search | Moderate | poolact | f1_mi | 62.33 [39/39] | 62.33 | qwen_original |
| Qwen 3.8 | poolact | Search | Moderate | poolact | f1_mv | 63.48 [39/39] | 63.48 | qwen_original |
| Qwen 3.8 | poolact | Search | Tight | cached | f1_mi | 22.31 [39/39] | 22.31 | qwen_original |
| Qwen 3.8 | poolact | Search | Tight | cached | f1_mv | 23.31 [39/39] | 23.31 | qwen_original |
| Qwen 3.8 | poolact | Search | Tight | naive | f1_mi | 18.55 [39/39] | 18.55 | qwen_original |
| Qwen 3.8 | poolact | Search | Tight | naive | f1_mv | 18.30 [39/39] | 18.30 | qwen_original |
| Qwen 3.8 | poolact | Search | Tight | poolact | f1_mi | 22.69 [39/39] | 22.69 | qwen_original |
| Qwen 3.8 | poolact | Search | Tight | poolact | f1_mv | 20.69 [39/39] | 20.69 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | cached | gap0_bon | 99.00 [9/9] | 99.00 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | cached | gap0_mi | 97.72 [9/9] | 97.72 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | cached | gap_bon | 99.00 [9/9] | 99.00 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | cached | gap_mi | 97.72 [9/9] | 97.72 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | cached | raw_perf_bon | 0.94 [9/9] | 0.94 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | cached | raw_perf_mi | 0.94 [9/9] | 0.94 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | naive | gap0_bon | 98.70 [9/9] | 98.70 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | naive | gap0_mi | 96.92 [9/9] | 96.92 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | naive | gap_bon | 98.70 [9/9] | 98.70 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | naive | gap_mi | 96.92 [9/9] | 96.92 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | naive | raw_perf_bon | 0.94 [9/9] | 0.94 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | naive | raw_perf_mi | 0.93 [9/9] | 0.93 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | poolact | gap0_bon | 99.15 [9/9] | 99.15 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | poolact | gap0_mi | 98.87 [9/9] | 98.87 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | poolact | gap_bon | 99.15 [9/9] | 99.15 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | poolact | gap_mi | 98.87 [9/9] | 98.87 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | qwen_original |
| Qwen 3.8 | poolact | HPO | Moderate | poolact | raw_perf_mi | 0.94 [9/9] | 0.94 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | cached | gap0_bon | 98.15 [9/9] | 98.15 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | cached | gap0_mi | 90.76 [9/9] | 90.76 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | cached | gap_bon | 98.15 [9/9] | 98.15 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | cached | gap_mi | 90.76 [9/9] | 90.76 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | cached | raw_perf_bon | 0.94 [9/9] | 0.94 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | cached | raw_perf_mi | 0.90 [9/9] | 0.90 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | naive | gap0_bon | 98.52 [9/9] | 98.52 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | naive | gap0_mi | 90.62 [9/9] | 90.62 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | naive | gap_bon | 98.52 [9/9] | 98.52 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | naive | gap_mi | 90.62 [9/9] | 90.62 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | naive | raw_perf_bon | 0.94 [9/9] | 0.94 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | naive | raw_perf_mi | 0.89 [9/9] | 0.89 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | poolact | gap0_bon | 98.29 [9/9] | 98.29 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | poolact | gap0_mi | 96.27 [9/9] | 96.27 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | poolact | gap_bon | 98.29 [9/9] | 98.29 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | poolact | gap_mi | 96.27 [9/9] | 96.27 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | poolact | raw_perf_bon | 0.94 [9/9] | 0.94 | qwen_original |
| Qwen 3.8 | poolact | HPO | Tight | poolact | raw_perf_mi | 0.93 [9/9] | 0.93 | qwen_original |

## 重复、资源和来源

[by_repeat.csv](by_repeat.csv)保留原重复层/顺序标签与分母；R1 不制造 SD。[contrasts.csv](contrasts.csv)保留家族/任务/所有端点的预算差、cached−naive、poolact−naive、poolact−cached，均先用未舍入值计算。

[resources.csv](resources.csv)保留六模型的原资源账本口径；[inherited_resources.csv](inherited_resources.csv)保留未被整组替换设置的原资源出口。reference-only 与不完整总量不冒充完整成本；Gemini 尚无关闭运行的全尝试成本总账，不记为零。并发 wall 不能相加作总历时，allocation GPU-hours 不能当作正式实验利用量。

[SOURCE_SELECTION.csv](SOURCE_SELECTION.csv)列出保留/替换理由、源行号和 cohort；[SCORE_COMPLETENESS.csv](SCORE_COMPLETENESS.csv)记录逻辑计划项和严格评分完整数。按 9 月 12 日已注册的完整三策略组替换，不在新旧结果间择优；其他设置继承旧正式数据。

[EXPERIMENT_LOG.zh.md](EXPERIMENT_LOG.zh.md)回答每次跑了什么、发现什么问题、是否重跑；[DATA_LINEAGE.zh.md](DATA_LINEAGE.zh.md)回答最终每部分从哪里来；[ARCHIVE_INDEX.md](ARCHIVE_INDEX.md)定位原始 dump、归档和 CSV。

## 可重建性

在本目录执行 `python build_report.py --check` 和 `python -m unittest test_build_report.py`；仅标准库，记录环境为 CPython 3.11.15。默认读取相邻的冻结 `../all-models-latest-20260913/`，也可用 `--input-dir` 指定同一组输入。`--check` 逐字节核对本生成器拥有的输出，不写文件；不读取原始请求、不重新评分。

[REPORT_INPUTS.json](REPORT_INPUTS.json)记录实际输入和 SHA256；[REPORT_CHECKS.json](REPORT_CHECKS.json)记录六模型分母、缺失、胜负和排名重算。源码固定输入的 `render_report.py` 仅用于数字助手；旧报告文字与七模型计数未复用。独立复核与来源/存档文件由本次报告工作流另行检查，不由本生成器覆盖。
