# Kimi-K3：ExpGym / PoolAct 实验结果

实验类型：Custom study；本地 Kimi-K3 + SGLang，按论文主设置新增模型，最终目标覆盖仓库全矩阵。

验收状态：**通过**。阶段：smoke。

| 验收项 | 计划 | 通过 |
|---|---:|---:|
| ExpGym traces | 9 | 9 |
| PoolAct results | 18 | 18 |
| PoolAct agent traces | 36 | 36 |
| 论文 PoolAct subset results | 18 | 18 |

缺失/失败状态：{'valid': 27}。缺失轨迹不补 0；有效模型零分保留。

## ExpGym 主表（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_free | single | audit | LA_pct | 94.118 | 1/1 |
| cost_free | single | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | single | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | single | audit | EA_pct | 41.176 | 1/1 |
| cost_tight | single | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | single | audit | EA_pct | 35.294 | 1/1 |
| cost_free | single | whois | F1_pct | 35.294 | 1/1 |
| cost_moderate | single | whois | F1_pct | 0.000 | 1/1 |
| cost_tight | single | whois | F1_pct | 35.294 | 1/1 |
| cost_free | single | nasbench101 | Gap_pct | 96.782 | 1/1 |
| cost_moderate | single | nasbench101 | Gap_pct | 96.322 | 1/1 |
| cost_tight | single | nasbench101 | Gap_pct | 98.344 | 1/1 |

## PoolAct 论文子集（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_moderate | cached | audit | LA_pct | 88.235 | 1/1 |
| cost_moderate | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | naive | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | poolact | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | cached | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | naive | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | poolact | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | cached | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | cached | whois | MI_F1_pct | 0.000 | 1/1 |
| cost_moderate | naive | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | naive | whois | MI_F1_pct | 17.647 | 1/1 |
| cost_moderate | poolact | whois | MV_F1_pct | 44.444 | 1/1 |
| cost_moderate | poolact | whois | MI_F1_pct | 39.869 | 1/1 |
| cost_tight | cached | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | cached | whois | MI_F1_pct | 17.647 | 1/1 |
| cost_tight | naive | whois | MV_F1_pct | 44.444 | 1/1 |
| cost_tight | naive | whois | MI_F1_pct | 22.222 | 1/1 |
| cost_tight | poolact | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | poolact | whois | MI_F1_pct | 0.000 | 1/1 |
| cost_moderate | cached | nasbench101 | BoN_Gap_pct | 98.880 | 1/1 |
| cost_moderate | cached | nasbench101 | MI_Gap_pct | 96.958 | 1/1 |
| cost_moderate | naive | nasbench101 | BoN_Gap_pct | 98.799 | 1/1 |
| cost_moderate | naive | nasbench101 | MI_Gap_pct | 98.756 | 1/1 |
| cost_moderate | poolact | nasbench101 | BoN_Gap_pct | 95.624 | 1/1 |
| cost_moderate | poolact | nasbench101 | MI_Gap_pct | 90.690 | 1/1 |
| cost_tight | cached | nasbench101 | BoN_Gap_pct | 98.344 | 1/1 |
| cost_tight | cached | nasbench101 | MI_Gap_pct | 92.050 | 1/1 |
| cost_tight | naive | nasbench101 | BoN_Gap_pct | 85.757 | 1/1 |
| cost_tight | naive | nasbench101 | MI_Gap_pct | 85.757 | 1/1 |
| cost_tight | poolact | nasbench101 | BoN_Gap_pct | 93.621 | 1/1 |
| cost_tight | poolact | nasbench101 | MI_Gap_pct | 89.689 | 1/1 |

## PoolAct 全量扩展（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_moderate | cached | audit | LA_pct | 88.235 | 1/1 |
| cost_moderate | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | naive | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | poolact | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | cached | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | naive | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | poolact | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | cached | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | cached | whois | MI_F1_pct | 0.000 | 1/1 |
| cost_moderate | naive | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | naive | whois | MI_F1_pct | 17.647 | 1/1 |
| cost_moderate | poolact | whois | MV_F1_pct | 44.444 | 1/1 |
| cost_moderate | poolact | whois | MI_F1_pct | 39.869 | 1/1 |
| cost_tight | cached | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | cached | whois | MI_F1_pct | 17.647 | 1/1 |
| cost_tight | naive | whois | MV_F1_pct | 44.444 | 1/1 |
| cost_tight | naive | whois | MI_F1_pct | 22.222 | 1/1 |
| cost_tight | poolact | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | poolact | whois | MI_F1_pct | 0.000 | 1/1 |
| cost_moderate | cached | nasbench101 | BoN_Gap_pct | 98.880 | 1/1 |
| cost_moderate | cached | nasbench101 | MI_Gap_pct | 96.958 | 1/1 |
| cost_moderate | naive | nasbench101 | BoN_Gap_pct | 98.799 | 1/1 |
| cost_moderate | naive | nasbench101 | MI_Gap_pct | 98.756 | 1/1 |
| cost_moderate | poolact | nasbench101 | BoN_Gap_pct | 95.624 | 1/1 |
| cost_moderate | poolact | nasbench101 | MI_Gap_pct | 90.690 | 1/1 |
| cost_tight | cached | nasbench101 | BoN_Gap_pct | 98.344 | 1/1 |
| cost_tight | cached | nasbench101 | MI_Gap_pct | 92.050 | 1/1 |
| cost_tight | naive | nasbench101 | BoN_Gap_pct | 85.757 | 1/1 |
| cost_tight | naive | nasbench101 | MI_Gap_pct | 85.757 | 1/1 |
| cost_tight | poolact | nasbench101 | BoN_Gap_pct | 93.621 | 1/1 |
| cost_tight | poolact | nasbench101 | MI_Gap_pct | 89.689 | 1/1 |

## 耗时与费用口径

| 项目 | 秒/次/token |
|---|---:|
| valid_agent_rows | 45 |
| sum_agent_wall_seconds | 1973.778 |
| sum_simulated_feedback_cost_seconds | 155925.562 |
| sum_logical_api_calls | 138 |
| sum_trace_input_tokens | 327825 |
| sum_trace_output_tokens | 58135 |
| sum_subprocess_attempt_wall_seconds | 1347.647 |
| known_subprocess_attempt_wall_seconds | 1347.647 |
| missing_subprocess_attempt_wall_count | 0 |
| sum_stage_subprocess_attempt_wall_seconds | 1347.647 |
| known_stage_subprocess_attempt_wall_seconds | 1347.647 |
| missing_stage_attempt_wall_count | 0 |
| sum_promoted_pilot_subprocess_attempt_wall_seconds | — |
| known_promoted_pilot_subprocess_attempt_wall_seconds | — |
| missing_promoted_pilot_attempt_wall_count | 0 |
| study_execution_span_seconds | 301.305 |
| known_execution_span_seconds | 301.305 |
| missing_attempt_start_or_end_count | 0 |

模拟反馈费用只表示 benchmark 预算；并发 agent/subprocess 墙钟求和会重复计时。真实执行跨度为最早开始至最晚结束，包含排队/重试/空档；完整 HTTP 尝试与 usage 以原始 API dump 为准。

## 查验路径与指标

逐项索引见 artifacts.csv，逐 agent 原始指标见 agents.csv，逐任务分数见 task_metrics.csv，汇总见 aggregate_metrics.csv / summary.json。每条记录保留原始路径与 SHA256；各输出为新目录，原始结果不覆盖。

Gap 按每条有效性能计算 max(0,(perf−mean)/(best−mean)×100)，先均值各 task 的 repeats、后均值各 family 的 tasks；可以超过 100。PoolAct MI 先分别计算每 agent 的 clipped Gap。Audit EA 是证据集合精确匹配，独立于 label 是否正确。

Kimi-K3/本地提供商是新增设置；PoolAct 使用当前 corrected locked 协议，历史论文含 locked/prelock 混合行，不能声称字节级或原模型复现。论文 tuning outer repeat 历史设定未公开；正式 full 阶段为一个 N=4 pool，smoke 为 N=2。非 full 阶段表格仅表示本阶段选定子集。设置与偏离详见 protocol/PAPER_ALIGNMENT.md。

归一化 oracle：/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/data/hpo_tuning/oracle3.json，SHA256 f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e。
Manifest：/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/smoke_v2/manifest.json，SHA256 4a4eadd9985e97ae5a1fbd11922d2d6d06ca77d4d8cf12c077501bee5f190426。

原始 API dump 完整性：通过。当前结果对应调用与历史重跑调用分开保留；详见 summary.json 的 dump_audit 字段。
