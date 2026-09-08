# Kimi-K3：ExpGym / PoolAct 实验结果

实验类型：Custom study；本地 Kimi-K3 + SGLang，按论文主设置新增模型，最终目标覆盖仓库全矩阵。

验收状态：**通过**。阶段：full。

| 验收项 | 计划 | 通过 |
|---|---:|---:|
| ExpGym traces | 303 | 303 |
| PoolAct results | 513 | 513 |
| PoolAct agent traces | 2052 | 2052 |
| 论文 PoolAct subset results | 192 | 192 |

缺失/失败状态：{'valid': 816}。缺失轨迹不补 0；有效模型零分保留。

## ExpGym 主表（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_free | single | audit | LA_pct | 84.615 | 39/39 |
| cost_free | single | audit | EA_pct | 55.807 | 39/39 |
| cost_moderate | single | audit | LA_pct | 84.766 | 39/39 |
| cost_moderate | single | audit | EA_pct | 55.505 | 39/39 |
| cost_tight | single | audit | LA_pct | 83.409 | 39/39 |
| cost_tight | single | audit | EA_pct | 54.148 | 39/39 |
| cost_free | single | whatis | F1_pct | 10.588 | 17/17 |
| cost_moderate | single | whatis | F1_pct | 5.882 | 17/17 |
| cost_tight | single | whatis | F1_pct | 0.000 | 17/17 |
| cost_free | single | whois | F1_pct | 27.942 | 18/18 |
| cost_moderate | single | whois | F1_pct | 30.644 | 18/18 |
| cost_tight | single | whois | F1_pct | 11.220 | 18/18 |
| cost_free | single | nasbench101 | Gap_pct | 82.018 | 9/9 |
| cost_moderate | single | nasbench101 | Gap_pct | 76.898 | 9/9 |
| cost_tight | single | nasbench101 | Gap_pct | 51.220 | 9/9 |
| cost_free | single | nasbench201 | Gap_pct | 85.641 | 9/9 |
| cost_moderate | single | nasbench201 | Gap_pct | 88.028 | 9/9 |
| cost_tight | single | nasbench201 | Gap_pct | 85.455 | 9/9 |
| cost_free | single | paramnet | Gap_pct | 79.907 | 9/9 |
| cost_moderate | single | paramnet | Gap_pct | 71.455 | 9/9 |
| cost_tight | single | paramnet | Gap_pct | 75.170 | 9/9 |

## PoolAct 论文子集（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_moderate | cached | audit | LA_pct | 83.710 | 13/13 |
| cost_moderate | cached | audit | EA_pct | 53.394 | 13/13 |
| cost_moderate | naive | audit | LA_pct | 83.258 | 13/13 |
| cost_moderate | naive | audit | EA_pct | 52.489 | 13/13 |
| cost_moderate | poolact | audit | LA_pct | 82.805 | 13/13 |
| cost_moderate | poolact | audit | EA_pct | 52.489 | 13/13 |
| cost_tight | cached | audit | LA_pct | 85.068 | 13/13 |
| cost_tight | cached | audit | EA_pct | 55.204 | 13/13 |
| cost_tight | naive | audit | LA_pct | 84.163 | 13/13 |
| cost_tight | naive | audit | EA_pct | 54.299 | 13/13 |
| cost_tight | poolact | audit | LA_pct | 82.805 | 13/13 |
| cost_tight | poolact | audit | EA_pct | 53.846 | 13/13 |
| cost_moderate | cached | whois | MV_F1_pct | 28.164 | 18/18 |
| cost_moderate | cached | whois | MI_F1_pct | 31.676 | 18/18 |
| cost_moderate | naive | whois | MV_F1_pct | 31.259 | 18/18 |
| cost_moderate | naive | whois | MI_F1_pct | 25.528 | 18/18 |
| cost_moderate | poolact | whois | MV_F1_pct | 29.877 | 18/18 |
| cost_moderate | poolact | whois | MI_F1_pct | 29.042 | 18/18 |
| cost_tight | cached | whois | MV_F1_pct | 17.037 | 18/18 |
| cost_tight | cached | whois | MI_F1_pct | 13.922 | 18/18 |
| cost_tight | naive | whois | MV_F1_pct | 25.454 | 18/18 |
| cost_tight | naive | whois | MI_F1_pct | 17.111 | 18/18 |
| cost_tight | poolact | whois | MV_F1_pct | 22.593 | 18/18 |
| cost_tight | poolact | whois | MI_F1_pct | 19.840 | 18/18 |
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
| cost_free | cached | audit | LA_pct | 82.805 | 13/13 |
| cost_free | cached | audit | EA_pct | 52.941 | 13/13 |
| cost_free | naive | audit | LA_pct | 83.710 | 13/13 |
| cost_free | naive | audit | EA_pct | 52.036 | 13/13 |
| cost_free | poolact | audit | LA_pct | 83.710 | 13/13 |
| cost_free | poolact | audit | EA_pct | 53.846 | 13/13 |
| cost_moderate | cached | audit | LA_pct | 83.710 | 13/13 |
| cost_moderate | cached | audit | EA_pct | 53.394 | 13/13 |
| cost_moderate | naive | audit | LA_pct | 83.258 | 13/13 |
| cost_moderate | naive | audit | EA_pct | 52.489 | 13/13 |
| cost_moderate | poolact | audit | LA_pct | 82.805 | 13/13 |
| cost_moderate | poolact | audit | EA_pct | 52.489 | 13/13 |
| cost_tight | cached | audit | LA_pct | 85.068 | 13/13 |
| cost_tight | cached | audit | EA_pct | 55.204 | 13/13 |
| cost_tight | naive | audit | LA_pct | 84.163 | 13/13 |
| cost_tight | naive | audit | EA_pct | 54.299 | 13/13 |
| cost_tight | poolact | audit | LA_pct | 82.805 | 13/13 |
| cost_tight | poolact | audit | EA_pct | 53.846 | 13/13 |
| cost_free | cached | whatis | MV_F1_pct | 8.824 | 17/17 |
| cost_free | cached | whatis | MI_F1_pct | 4.412 | 17/17 |
| cost_free | naive | whatis | MV_F1_pct | 0.000 | 17/17 |
| cost_free | naive | whatis | MI_F1_pct | 0.908 | 17/17 |
| cost_free | poolact | whatis | MV_F1_pct | 5.882 | 17/17 |
| cost_free | poolact | whatis | MI_F1_pct | 4.585 | 17/17 |
| cost_moderate | cached | whatis | MV_F1_pct | 0.000 | 17/17 |
| cost_moderate | cached | whatis | MI_F1_pct | 2.941 | 17/17 |
| cost_moderate | naive | whatis | MV_F1_pct | 0.000 | 17/17 |
| cost_moderate | naive | whatis | MI_F1_pct | 2.206 | 17/17 |
| cost_moderate | poolact | whatis | MV_F1_pct | 0.000 | 17/17 |
| cost_moderate | poolact | whatis | MI_F1_pct | 1.471 | 17/17 |
| cost_tight | cached | whatis | MV_F1_pct | 0.000 | 17/17 |
| cost_tight | cached | whatis | MI_F1_pct | 0.735 | 17/17 |
| cost_tight | naive | whatis | MV_F1_pct | 2.941 | 17/17 |
| cost_tight | naive | whatis | MI_F1_pct | 1.471 | 17/17 |
| cost_tight | poolact | whatis | MV_F1_pct | 2.941 | 17/17 |
| cost_tight | poolact | whatis | MI_F1_pct | 3.114 | 17/17 |
| cost_free | cached | whois | MV_F1_pct | 32.000 | 18/18 |
| cost_free | cached | whois | MI_F1_pct | 30.930 | 18/18 |
| cost_free | naive | whois | MV_F1_pct | 33.704 | 18/18 |
| cost_free | naive | whois | MI_F1_pct | 24.801 | 18/18 |
| cost_free | poolact | whois | MV_F1_pct | 36.790 | 18/18 |
| cost_free | poolact | whois | MI_F1_pct | 31.644 | 18/18 |
| cost_moderate | cached | whois | MV_F1_pct | 28.164 | 18/18 |
| cost_moderate | cached | whois | MI_F1_pct | 31.676 | 18/18 |
| cost_moderate | naive | whois | MV_F1_pct | 31.259 | 18/18 |
| cost_moderate | naive | whois | MI_F1_pct | 25.528 | 18/18 |
| cost_moderate | poolact | whois | MV_F1_pct | 29.877 | 18/18 |
| cost_moderate | poolact | whois | MI_F1_pct | 29.042 | 18/18 |
| cost_tight | cached | whois | MV_F1_pct | 17.037 | 18/18 |
| cost_tight | cached | whois | MI_F1_pct | 13.922 | 18/18 |
| cost_tight | naive | whois | MV_F1_pct | 25.454 | 18/18 |
| cost_tight | naive | whois | MI_F1_pct | 17.111 | 18/18 |
| cost_tight | poolact | whois | MV_F1_pct | 22.593 | 18/18 |
| cost_tight | poolact | whois | MI_F1_pct | 19.840 | 18/18 |
| cost_free | cached | nasbench101 | BoN_Gap_pct | 65.489 | 3/3 |
| cost_free | cached | nasbench101 | MI_Gap_pct | 62.770 | 3/3 |
| cost_free | naive | nasbench101 | BoN_Gap_pct | 65.724 | 3/3 |
| cost_free | naive | nasbench101 | MI_Gap_pct | 55.882 | 3/3 |
| cost_free | poolact | nasbench101 | BoN_Gap_pct | 99.130 | 3/3 |
| cost_free | poolact | nasbench101 | MI_Gap_pct | 79.026 | 3/3 |
| cost_moderate | cached | nasbench101 | BoN_Gap_pct | 95.977 | 3/3 |
| cost_moderate | cached | nasbench101 | MI_Gap_pct | 67.720 | 3/3 |
| cost_moderate | naive | nasbench101 | BoN_Gap_pct | 97.966 | 3/3 |
| cost_moderate | naive | nasbench101 | MI_Gap_pct | 78.209 | 3/3 |
| cost_moderate | poolact | nasbench101 | BoN_Gap_pct | 98.715 | 3/3 |
| cost_moderate | poolact | nasbench101 | MI_Gap_pct | 73.289 | 3/3 |
| cost_tight | cached | nasbench101 | BoN_Gap_pct | 94.641 | 3/3 |
| cost_tight | cached | nasbench101 | MI_Gap_pct | 67.776 | 3/3 |
| cost_tight | naive | nasbench101 | BoN_Gap_pct | 94.565 | 3/3 |
| cost_tight | naive | nasbench101 | MI_Gap_pct | 67.921 | 3/3 |
| cost_tight | poolact | nasbench101 | BoN_Gap_pct | 97.929 | 3/3 |
| cost_tight | poolact | nasbench101 | MI_Gap_pct | 89.221 | 3/3 |
| cost_free | cached | nasbench201 | BoN_Gap_pct | 97.029 | 3/3 |
| cost_free | cached | nasbench201 | MI_Gap_pct | 86.858 | 3/3 |
| cost_free | naive | nasbench201 | BoN_Gap_pct | 91.550 | 3/3 |
| cost_free | naive | nasbench201 | MI_Gap_pct | 80.708 | 3/3 |
| cost_free | poolact | nasbench201 | BoN_Gap_pct | 96.255 | 3/3 |
| cost_free | poolact | nasbench201 | MI_Gap_pct | 86.260 | 3/3 |
| cost_moderate | cached | nasbench201 | BoN_Gap_pct | 98.067 | 3/3 |
| cost_moderate | cached | nasbench201 | MI_Gap_pct | 87.998 | 3/3 |
| cost_moderate | naive | nasbench201 | BoN_Gap_pct | 94.500 | 3/3 |
| cost_moderate | naive | nasbench201 | MI_Gap_pct | 79.308 | 3/3 |
| cost_moderate | poolact | nasbench201 | BoN_Gap_pct | 96.908 | 3/3 |
| cost_moderate | poolact | nasbench201 | MI_Gap_pct | 85.300 | 3/3 |
| cost_tight | cached | nasbench201 | BoN_Gap_pct | 94.235 | 3/3 |
| cost_tight | cached | nasbench201 | MI_Gap_pct | 83.638 | 3/3 |
| cost_tight | naive | nasbench201 | BoN_Gap_pct | 91.453 | 3/3 |
| cost_tight | naive | nasbench201 | MI_Gap_pct | 83.206 | 3/3 |
| cost_tight | poolact | nasbench201 | BoN_Gap_pct | 92.518 | 3/3 |
| cost_tight | poolact | nasbench201 | MI_Gap_pct | 81.847 | 3/3 |
| cost_free | cached | paramnet | BoN_Gap_pct | 94.898 | 3/3 |
| cost_free | cached | paramnet | MI_Gap_pct | 78.777 | 3/3 |
| cost_free | naive | paramnet | BoN_Gap_pct | 95.146 | 3/3 |
| cost_free | naive | paramnet | MI_Gap_pct | 87.943 | 3/3 |
| cost_free | poolact | paramnet | BoN_Gap_pct | 95.353 | 3/3 |
| cost_free | poolact | paramnet | MI_Gap_pct | 91.793 | 3/3 |
| cost_moderate | cached | paramnet | BoN_Gap_pct | 94.040 | 3/3 |
| cost_moderate | cached | paramnet | MI_Gap_pct | 81.699 | 3/3 |
| cost_moderate | naive | paramnet | BoN_Gap_pct | 94.567 | 3/3 |
| cost_moderate | naive | paramnet | MI_Gap_pct | 88.729 | 3/3 |
| cost_moderate | poolact | paramnet | BoN_Gap_pct | 95.828 | 3/3 |
| cost_moderate | poolact | paramnet | MI_Gap_pct | 84.080 | 3/3 |
| cost_tight | cached | paramnet | BoN_Gap_pct | 87.319 | 3/3 |
| cost_tight | cached | paramnet | MI_Gap_pct | 66.885 | 3/3 |
| cost_tight | naive | paramnet | BoN_Gap_pct | 86.535 | 3/3 |
| cost_tight | naive | paramnet | MI_Gap_pct | 69.495 | 3/3 |
| cost_tight | poolact | paramnet | BoN_Gap_pct | 95.721 | 3/3 |
| cost_tight | poolact | paramnet | MI_Gap_pct | 90.873 | 3/3 |

## 耗时与费用口径

| 项目 | 秒/次/token |
|---|---:|
| valid_agent_rows | 2355 |
| sum_agent_wall_seconds | 144199.836 |
| sum_simulated_feedback_cost_seconds | 16257831.533 |
| sum_logical_api_calls | 9068 |
| sum_trace_input_tokens | 17977502 |
| sum_trace_output_tokens | 2434522 |
| sum_subprocess_attempt_wall_seconds | 66248.899 |
| known_subprocess_attempt_wall_seconds | 66248.899 |
| missing_subprocess_attempt_wall_count | 0 |
| sum_stage_subprocess_attempt_wall_seconds | 57655.735 |
| known_stage_subprocess_attempt_wall_seconds | 57655.735 |
| missing_stage_attempt_wall_count | 0 |
| sum_promoted_pilot_subprocess_attempt_wall_seconds | 8593.164 |
| known_promoted_pilot_subprocess_attempt_wall_seconds | 8593.164 |
| missing_promoted_pilot_attempt_wall_count | 0 |
| study_execution_span_seconds | 4899.925 |
| known_execution_span_seconds | 4899.925 |
| missing_attempt_start_or_end_count | 0 |

模拟反馈费用只表示 benchmark 预算；并发 agent/subprocess 墙钟求和会重复计时。真实执行跨度为最早开始至最晚结束，包含排队/重试/空档；完整 HTTP 尝试与 usage 以原始 API dump 为准。

## 查验路径与指标

逐项索引见 artifacts.csv，逐 agent 原始指标见 agents.csv，逐任务分数见 task_metrics.csv，汇总见 aggregate_metrics.csv / summary.json。每条记录保留原始路径与 SHA256；各输出为新目录，原始结果不覆盖。

Gap 按每条有效性能计算 max(0,(perf−mean)/(best−mean)×100)，先均值各 task 的 repeats、后均值各 family 的 tasks；可以超过 100。PoolAct MI 先分别计算每 agent 的 clipped Gap。Audit EA 是证据集合精确匹配，独立于 label 是否正确。

Kimi-K3/本地提供商是新增设置；PoolAct 使用当前 corrected locked 协议，历史论文含 locked/prelock 混合行，不能声称字节级或原模型复现。论文 tuning outer repeat 历史设定未公开；正式 full 阶段为一个 N=4 pool，smoke 为 N=2。非 full 阶段表格仅表示本阶段选定子集。设置与偏离详见 protocol/PAPER_ALIGNMENT.md。

归一化 oracle：/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/data/hpo_tuning/oracle3.json，SHA256 f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e。
Manifest：/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/full_v3/manifest.json，SHA256 7016deb285696ff95c0aa970088c0580d0daf60cb0c6695ce8515e0fe85df854。

原始 API dump 完整性：通过。当前结果对应调用与历史重跑调用分开保留；详见 summary.json 的 dump_audit 字段。
