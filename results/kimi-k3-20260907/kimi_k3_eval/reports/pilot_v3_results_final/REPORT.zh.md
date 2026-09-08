# Kimi-K3：ExpGym / PoolAct 实验结果

实验类型：Custom study；本地 Kimi-K3 + SGLang，按论文主设置新增模型，最终目标覆盖仓库全矩阵。

验收状态：**通过**。阶段：pilot。

| 验收项 | 计划 | 通过 |
|---|---:|---:|
| ExpGym traces | 42 | 42 |
| PoolAct results | 54 | 54 |
| PoolAct agent traces | 216 | 216 |
| 论文 PoolAct subset results | 18 | 18 |

缺失/失败状态：{'valid': 96}。缺失轨迹不补 0；有效模型零分保留。

## ExpGym 主表（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_free | single | audit | LA_pct | 90.196 | 3/3 |
| cost_free | single | audit | EA_pct | 37.255 | 3/3 |
| cost_moderate | single | audit | LA_pct | 94.118 | 3/3 |
| cost_moderate | single | audit | EA_pct | 39.216 | 3/3 |
| cost_tight | single | audit | LA_pct | 92.157 | 3/3 |
| cost_tight | single | audit | EA_pct | 35.294 | 3/3 |
| cost_free | single | whatis | F1_pct | 0.000 | 1/1 |
| cost_moderate | single | whatis | F1_pct | 0.000 | 1/1 |
| cost_tight | single | whatis | F1_pct | 0.000 | 1/1 |
| cost_free | single | whois | F1_pct | 96.296 | 1/1 |
| cost_moderate | single | whois | F1_pct | 78.261 | 1/1 |
| cost_tight | single | whois | F1_pct | 35.294 | 1/1 |
| cost_free | single | nasbench101 | Gap_pct | 94.774 | 3/3 |
| cost_moderate | single | nasbench101 | Gap_pct | 99.207 | 3/3 |
| cost_tight | single | nasbench101 | Gap_pct | 93.298 | 3/3 |
| cost_free | single | nasbench201 | Gap_pct | 88.208 | 3/3 |
| cost_moderate | single | nasbench201 | Gap_pct | 90.581 | 3/3 |
| cost_tight | single | nasbench201 | Gap_pct | 92.529 | 3/3 |
| cost_free | single | paramnet | Gap_pct | 89.630 | 3/3 |
| cost_moderate | single | paramnet | Gap_pct | 89.435 | 3/3 |
| cost_tight | single | paramnet | Gap_pct | 75.791 | 3/3 |

## PoolAct 论文子集（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_moderate | cached | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | naive | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | poolact | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | cached | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | naive | audit | EA_pct | 41.176 | 1/1 |
| cost_tight | poolact | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | cached | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | cached | whois | MI_F1_pct | 52.463 | 1/1 |
| cost_moderate | naive | whois | MV_F1_pct | 60.000 | 1/1 |
| cost_moderate | naive | whois | MI_F1_pct | 39.074 | 1/1 |
| cost_moderate | poolact | whois | MV_F1_pct | 44.444 | 1/1 |
| cost_moderate | poolact | whois | MI_F1_pct | 38.116 | 1/1 |
| cost_tight | cached | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | cached | whois | MI_F1_pct | 19.935 | 1/1 |
| cost_tight | naive | whois | MV_F1_pct | 44.444 | 1/1 |
| cost_tight | naive | whois | MI_F1_pct | 31.046 | 1/1 |
| cost_tight | poolact | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | poolact | whois | MI_F1_pct | 17.647 | 1/1 |
| cost_moderate | cached | nasbench101 | BoN_Gap_pct | 99.222 | 1/1 |
| cost_moderate | cached | nasbench101 | MI_Gap_pct | 95.159 | 1/1 |
| cost_moderate | naive | nasbench101 | BoN_Gap_pct | 99.568 | 1/1 |
| cost_moderate | naive | nasbench101 | MI_Gap_pct | 98.064 | 1/1 |
| cost_moderate | poolact | nasbench101 | BoN_Gap_pct | 98.500 | 1/1 |
| cost_moderate | poolact | nasbench101 | MI_Gap_pct | 72.684 | 1/1 |
| cost_tight | cached | nasbench101 | BoN_Gap_pct | 98.552 | 1/1 |
| cost_tight | cached | nasbench101 | MI_Gap_pct | 91.947 | 1/1 |
| cost_tight | naive | nasbench101 | BoN_Gap_pct | 99.260 | 1/1 |
| cost_tight | naive | nasbench101 | MI_Gap_pct | 92.448 | 1/1 |
| cost_tight | poolact | nasbench101 | BoN_Gap_pct | 98.761 | 1/1 |
| cost_tight | poolact | nasbench101 | MI_Gap_pct | 97.895 | 1/1 |

## PoolAct 全量扩展（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_free | cached | audit | LA_pct | 94.118 | 1/1 |
| cost_free | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_free | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_free | naive | audit | EA_pct | 35.294 | 1/1 |
| cost_free | poolact | audit | LA_pct | 88.235 | 1/1 |
| cost_free | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | cached | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | naive | audit | EA_pct | 35.294 | 1/1 |
| cost_moderate | poolact | audit | LA_pct | 94.118 | 1/1 |
| cost_moderate | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | cached | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | cached | audit | EA_pct | 35.294 | 1/1 |
| cost_tight | naive | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | naive | audit | EA_pct | 41.176 | 1/1 |
| cost_tight | poolact | audit | LA_pct | 94.118 | 1/1 |
| cost_tight | poolact | audit | EA_pct | 35.294 | 1/1 |
| cost_free | cached | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_free | cached | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_free | naive | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_free | naive | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_free | poolact | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_free | poolact | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_moderate | cached | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | cached | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_moderate | naive | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | naive | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_moderate | poolact | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | poolact | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_tight | cached | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | cached | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_tight | naive | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | naive | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_tight | poolact | whatis | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | poolact | whatis | MI_F1_pct | 0.000 | 1/1 |
| cost_free | cached | whois | MV_F1_pct | 13.333 | 1/1 |
| cost_free | cached | whois | MI_F1_pct | 62.899 | 1/1 |
| cost_free | naive | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_free | naive | whois | MI_F1_pct | 53.731 | 1/1 |
| cost_free | poolact | whois | MV_F1_pct | 66.667 | 1/1 |
| cost_free | poolact | whois | MI_F1_pct | 42.157 | 1/1 |
| cost_moderate | cached | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_moderate | cached | whois | MI_F1_pct | 52.463 | 1/1 |
| cost_moderate | naive | whois | MV_F1_pct | 60.000 | 1/1 |
| cost_moderate | naive | whois | MI_F1_pct | 39.074 | 1/1 |
| cost_moderate | poolact | whois | MV_F1_pct | 44.444 | 1/1 |
| cost_moderate | poolact | whois | MI_F1_pct | 38.116 | 1/1 |
| cost_tight | cached | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | cached | whois | MI_F1_pct | 19.935 | 1/1 |
| cost_tight | naive | whois | MV_F1_pct | 44.444 | 1/1 |
| cost_tight | naive | whois | MI_F1_pct | 31.046 | 1/1 |
| cost_tight | poolact | whois | MV_F1_pct | 0.000 | 1/1 |
| cost_tight | poolact | whois | MI_F1_pct | 17.647 | 1/1 |
| cost_free | cached | nasbench101 | BoN_Gap_pct | 97.347 | 1/1 |
| cost_free | cached | nasbench101 | MI_Gap_pct | 93.625 | 1/1 |
| cost_free | naive | nasbench101 | BoN_Gap_pct | 98.927 | 1/1 |
| cost_free | naive | nasbench101 | MI_Gap_pct | 94.834 | 1/1 |
| cost_free | poolact | nasbench101 | BoN_Gap_pct | 99.497 | 1/1 |
| cost_free | poolact | nasbench101 | MI_Gap_pct | 73.936 | 1/1 |
| cost_moderate | cached | nasbench101 | BoN_Gap_pct | 99.222 | 1/1 |
| cost_moderate | cached | nasbench101 | MI_Gap_pct | 95.159 | 1/1 |
| cost_moderate | naive | nasbench101 | BoN_Gap_pct | 99.568 | 1/1 |
| cost_moderate | naive | nasbench101 | MI_Gap_pct | 98.064 | 1/1 |
| cost_moderate | poolact | nasbench101 | BoN_Gap_pct | 98.500 | 1/1 |
| cost_moderate | poolact | nasbench101 | MI_Gap_pct | 72.684 | 1/1 |
| cost_tight | cached | nasbench101 | BoN_Gap_pct | 98.552 | 1/1 |
| cost_tight | cached | nasbench101 | MI_Gap_pct | 91.947 | 1/1 |
| cost_tight | naive | nasbench101 | BoN_Gap_pct | 99.260 | 1/1 |
| cost_tight | naive | nasbench101 | MI_Gap_pct | 92.448 | 1/1 |
| cost_tight | poolact | nasbench101 | BoN_Gap_pct | 98.761 | 1/1 |
| cost_tight | poolact | nasbench101 | MI_Gap_pct | 97.895 | 1/1 |
| cost_free | cached | nasbench201 | BoN_Gap_pct | 94.791 | 1/1 |
| cost_free | cached | nasbench201 | MI_Gap_pct | 88.174 | 1/1 |
| cost_free | naive | nasbench201 | BoN_Gap_pct | 92.998 | 1/1 |
| cost_free | naive | nasbench201 | MI_Gap_pct | 85.758 | 1/1 |
| cost_free | poolact | nasbench201 | BoN_Gap_pct | 99.330 | 1/1 |
| cost_free | poolact | nasbench201 | MI_Gap_pct | 98.911 | 1/1 |
| cost_moderate | cached | nasbench201 | BoN_Gap_pct | 97.906 | 1/1 |
| cost_moderate | cached | nasbench201 | MI_Gap_pct | 89.619 | 1/1 |
| cost_moderate | naive | nasbench201 | BoN_Gap_pct | 87.203 | 1/1 |
| cost_moderate | naive | nasbench201 | MI_Gap_pct | 80.080 | 1/1 |
| cost_moderate | poolact | nasbench201 | BoN_Gap_pct | 100.000 | 1/1 |
| cost_moderate | poolact | nasbench201 | MI_Gap_pct | 87.563 | 1/1 |
| cost_tight | cached | nasbench201 | BoN_Gap_pct | 99.079 | 1/1 |
| cost_tight | cached | nasbench201 | MI_Gap_pct | 88.823 | 1/1 |
| cost_tight | naive | nasbench201 | BoN_Gap_pct | 99.330 | 1/1 |
| cost_tight | naive | nasbench201 | MI_Gap_pct | 93.752 | 1/1 |
| cost_tight | poolact | nasbench201 | BoN_Gap_pct | 99.330 | 1/1 |
| cost_tight | poolact | nasbench201 | MI_Gap_pct | 79.975 | 1/1 |
| cost_free | cached | paramnet | BoN_Gap_pct | 97.999 | 1/1 |
| cost_free | cached | paramnet | MI_Gap_pct | 91.992 | 1/1 |
| cost_free | naive | paramnet | BoN_Gap_pct | 100.292 | 1/1 |
| cost_free | naive | paramnet | MI_Gap_pct | 91.441 | 1/1 |
| cost_free | poolact | paramnet | BoN_Gap_pct | 93.899 | 1/1 |
| cost_free | poolact | paramnet | MI_Gap_pct | 92.226 | 1/1 |
| cost_moderate | cached | paramnet | BoN_Gap_pct | 88.738 | 1/1 |
| cost_moderate | cached | paramnet | MI_Gap_pct | 79.673 | 1/1 |
| cost_moderate | naive | paramnet | BoN_Gap_pct | 90.694 | 1/1 |
| cost_moderate | naive | paramnet | MI_Gap_pct | 87.153 | 1/1 |
| cost_moderate | poolact | paramnet | BoN_Gap_pct | 93.234 | 1/1 |
| cost_moderate | poolact | paramnet | MI_Gap_pct | 82.034 | 1/1 |
| cost_tight | cached | paramnet | BoN_Gap_pct | 81.275 | 1/1 |
| cost_tight | cached | paramnet | MI_Gap_pct | 74.329 | 1/1 |
| cost_tight | naive | paramnet | BoN_Gap_pct | 72.013 | 1/1 |
| cost_tight | naive | paramnet | MI_Gap_pct | 72.013 | 1/1 |
| cost_tight | poolact | paramnet | BoN_Gap_pct | 95.909 | 1/1 |
| cost_tight | poolact | paramnet | MI_Gap_pct | 89.935 | 1/1 |

## 耗时与费用口径

| 项目 | 秒/次/token |
|---|---:|
| valid_agent_rows | 258 |
| sum_agent_wall_seconds | 18812.369 |
| sum_simulated_feedback_cost_seconds | 2529975.628 |
| sum_logical_api_calls | 1193 |
| sum_trace_input_tokens | 2889395 |
| sum_trace_output_tokens | 317983 |
| sum_subprocess_attempt_wall_seconds | 8593.164 |
| known_subprocess_attempt_wall_seconds | 8593.164 |
| missing_subprocess_attempt_wall_count | 0 |
| sum_stage_subprocess_attempt_wall_seconds | 8593.164 |
| known_stage_subprocess_attempt_wall_seconds | 8593.164 |
| missing_stage_attempt_wall_count | 0 |
| sum_promoted_pilot_subprocess_attempt_wall_seconds | — |
| known_promoted_pilot_subprocess_attempt_wall_seconds | — |
| missing_promoted_pilot_attempt_wall_count | 0 |
| study_execution_span_seconds | 758.372 |
| known_execution_span_seconds | 758.372 |
| missing_attempt_start_or_end_count | 0 |

模拟反馈费用只表示 benchmark 预算；并发 agent/subprocess 墙钟求和会重复计时。真实执行跨度为最早开始至最晚结束，包含排队/重试/空档；完整 HTTP 尝试与 usage 以原始 API dump 为准。

## 查验路径与指标

逐项索引见 artifacts.csv，逐 agent 原始指标见 agents.csv，逐任务分数见 task_metrics.csv，汇总见 aggregate_metrics.csv / summary.json。每条记录保留原始路径与 SHA256；各输出为新目录，原始结果不覆盖。

Gap 按每条有效性能计算 max(0,(perf−mean)/(best−mean)×100)，先均值各 task 的 repeats、后均值各 family 的 tasks；可以超过 100。PoolAct MI 先分别计算每 agent 的 clipped Gap。Audit EA 是证据集合精确匹配，独立于 label 是否正确。

Kimi-K3/本地提供商是新增设置；PoolAct 使用当前 corrected locked 协议，历史论文含 locked/prelock 混合行，不能声称字节级或原模型复现。论文 tuning outer repeat 历史设定未公开；正式 full 阶段为一个 N=4 pool，smoke 为 N=2。非 full 阶段表格仅表示本阶段选定子集。设置与偏离详见 protocol/PAPER_ALIGNMENT.md。

归一化 oracle：/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/data/hpo_tuning/oracle3.json，SHA256 f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e。
Manifest：/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/pilot_v3/manifest.json，SHA256 6a04e41ff3b15cd5fc7358faabac9edec72a3a018ef8cb44750ede6b86148d60。

原始 API dump 完整性：通过。当前结果对应调用与历史重跑调用分开保留；详见 summary.json 的 dump_audit 字段。
