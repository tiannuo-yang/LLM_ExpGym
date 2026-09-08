# Kimi-K3：ExpGym / PoolAct 实验结果

实验类型：Custom study；本地 Kimi-K3 + SGLang，按论文主设置新增模型，最终目标覆盖仓库全矩阵。

验收状态：**未完成/未通过，以下仅报告已验证数据**。阶段：full。

| 验收项 | 计划 | 通过 |
|---|---:|---:|
| ExpGym traces | 303 | 0 |
| PoolAct results | 513 | 0 |
| PoolAct agent traces | 2052 | 0 |
| 论文 PoolAct subset results | 192 | 0 |

缺失/失败状态：{'missing': 816}。缺失轨迹不补 0；有效模型零分保留。

## ExpGym 主表（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_free | single | audit | LA_pct | — | 0/39 |
| cost_free | single | audit | EA_pct | — | 0/39 |
| cost_moderate | single | audit | LA_pct | — | 0/39 |
| cost_moderate | single | audit | EA_pct | — | 0/39 |
| cost_tight | single | audit | LA_pct | — | 0/39 |
| cost_tight | single | audit | EA_pct | — | 0/39 |
| cost_free | single | whatis | F1_pct | — | 0/17 |
| cost_moderate | single | whatis | F1_pct | — | 0/17 |
| cost_tight | single | whatis | F1_pct | — | 0/17 |
| cost_free | single | whois | F1_pct | — | 0/18 |
| cost_moderate | single | whois | F1_pct | — | 0/18 |
| cost_tight | single | whois | F1_pct | — | 0/18 |
| cost_free | single | nasbench101 | Gap_pct | — | 0/9 |
| cost_moderate | single | nasbench101 | Gap_pct | — | 0/9 |
| cost_tight | single | nasbench101 | Gap_pct | — | 0/9 |
| cost_free | single | nasbench201 | Gap_pct | — | 0/9 |
| cost_moderate | single | nasbench201 | Gap_pct | — | 0/9 |
| cost_tight | single | nasbench201 | Gap_pct | — | 0/9 |
| cost_free | single | paramnet | Gap_pct | — | 0/9 |
| cost_moderate | single | paramnet | Gap_pct | — | 0/9 |
| cost_tight | single | paramnet | Gap_pct | — | 0/9 |

## PoolAct 论文子集（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_moderate | cached | audit | LA_pct | — | 0/13 |
| cost_moderate | cached | audit | EA_pct | — | 0/13 |
| cost_moderate | naive | audit | LA_pct | — | 0/13 |
| cost_moderate | naive | audit | EA_pct | — | 0/13 |
| cost_moderate | poolact | audit | LA_pct | — | 0/13 |
| cost_moderate | poolact | audit | EA_pct | — | 0/13 |
| cost_tight | cached | audit | LA_pct | — | 0/13 |
| cost_tight | cached | audit | EA_pct | — | 0/13 |
| cost_tight | naive | audit | LA_pct | — | 0/13 |
| cost_tight | naive | audit | EA_pct | — | 0/13 |
| cost_tight | poolact | audit | LA_pct | — | 0/13 |
| cost_tight | poolact | audit | EA_pct | — | 0/13 |
| cost_moderate | cached | whois | MV_F1_pct | — | 0/18 |
| cost_moderate | cached | whois | MI_F1_pct | — | 0/18 |
| cost_moderate | naive | whois | MV_F1_pct | — | 0/18 |
| cost_moderate | naive | whois | MI_F1_pct | — | 0/18 |
| cost_moderate | poolact | whois | MV_F1_pct | — | 0/18 |
| cost_moderate | poolact | whois | MI_F1_pct | — | 0/18 |
| cost_tight | cached | whois | MV_F1_pct | — | 0/18 |
| cost_tight | cached | whois | MI_F1_pct | — | 0/18 |
| cost_tight | naive | whois | MV_F1_pct | — | 0/18 |
| cost_tight | naive | whois | MI_F1_pct | — | 0/18 |
| cost_tight | poolact | whois | MV_F1_pct | — | 0/18 |
| cost_tight | poolact | whois | MI_F1_pct | — | 0/18 |
| cost_moderate | cached | nasbench101 | BoN_Gap_pct | — | 0/1 |
| cost_moderate | cached | nasbench101 | MI_Gap_pct | — | 0/1 |
| cost_moderate | naive | nasbench101 | BoN_Gap_pct | — | 0/1 |
| cost_moderate | naive | nasbench101 | MI_Gap_pct | — | 0/1 |
| cost_moderate | poolact | nasbench101 | BoN_Gap_pct | — | 0/1 |
| cost_moderate | poolact | nasbench101 | MI_Gap_pct | — | 0/1 |
| cost_tight | cached | nasbench101 | BoN_Gap_pct | — | 0/1 |
| cost_tight | cached | nasbench101 | MI_Gap_pct | — | 0/1 |
| cost_tight | naive | nasbench101 | BoN_Gap_pct | — | 0/1 |
| cost_tight | naive | nasbench101 | MI_Gap_pct | — | 0/1 |
| cost_tight | poolact | nasbench101 | BoN_Gap_pct | — | 0/1 |
| cost_tight | poolact | nasbench101 | MI_Gap_pct | — | 0/1 |

## PoolAct 全量扩展（%）

| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |
|---|---|---|---|---:|---:|
| cost_free | cached | audit | LA_pct | — | 0/13 |
| cost_free | cached | audit | EA_pct | — | 0/13 |
| cost_free | naive | audit | LA_pct | — | 0/13 |
| cost_free | naive | audit | EA_pct | — | 0/13 |
| cost_free | poolact | audit | LA_pct | — | 0/13 |
| cost_free | poolact | audit | EA_pct | — | 0/13 |
| cost_moderate | cached | audit | LA_pct | — | 0/13 |
| cost_moderate | cached | audit | EA_pct | — | 0/13 |
| cost_moderate | naive | audit | LA_pct | — | 0/13 |
| cost_moderate | naive | audit | EA_pct | — | 0/13 |
| cost_moderate | poolact | audit | LA_pct | — | 0/13 |
| cost_moderate | poolact | audit | EA_pct | — | 0/13 |
| cost_tight | cached | audit | LA_pct | — | 0/13 |
| cost_tight | cached | audit | EA_pct | — | 0/13 |
| cost_tight | naive | audit | LA_pct | — | 0/13 |
| cost_tight | naive | audit | EA_pct | — | 0/13 |
| cost_tight | poolact | audit | LA_pct | — | 0/13 |
| cost_tight | poolact | audit | EA_pct | — | 0/13 |
| cost_free | cached | whatis | MV_F1_pct | — | 0/17 |
| cost_free | cached | whatis | MI_F1_pct | — | 0/17 |
| cost_free | naive | whatis | MV_F1_pct | — | 0/17 |
| cost_free | naive | whatis | MI_F1_pct | — | 0/17 |
| cost_free | poolact | whatis | MV_F1_pct | — | 0/17 |
| cost_free | poolact | whatis | MI_F1_pct | — | 0/17 |
| cost_moderate | cached | whatis | MV_F1_pct | — | 0/17 |
| cost_moderate | cached | whatis | MI_F1_pct | — | 0/17 |
| cost_moderate | naive | whatis | MV_F1_pct | — | 0/17 |
| cost_moderate | naive | whatis | MI_F1_pct | — | 0/17 |
| cost_moderate | poolact | whatis | MV_F1_pct | — | 0/17 |
| cost_moderate | poolact | whatis | MI_F1_pct | — | 0/17 |
| cost_tight | cached | whatis | MV_F1_pct | — | 0/17 |
| cost_tight | cached | whatis | MI_F1_pct | — | 0/17 |
| cost_tight | naive | whatis | MV_F1_pct | — | 0/17 |
| cost_tight | naive | whatis | MI_F1_pct | — | 0/17 |
| cost_tight | poolact | whatis | MV_F1_pct | — | 0/17 |
| cost_tight | poolact | whatis | MI_F1_pct | — | 0/17 |
| cost_free | cached | whois | MV_F1_pct | — | 0/18 |
| cost_free | cached | whois | MI_F1_pct | — | 0/18 |
| cost_free | naive | whois | MV_F1_pct | — | 0/18 |
| cost_free | naive | whois | MI_F1_pct | — | 0/18 |
| cost_free | poolact | whois | MV_F1_pct | — | 0/18 |
| cost_free | poolact | whois | MI_F1_pct | — | 0/18 |
| cost_moderate | cached | whois | MV_F1_pct | — | 0/18 |
| cost_moderate | cached | whois | MI_F1_pct | — | 0/18 |
| cost_moderate | naive | whois | MV_F1_pct | — | 0/18 |
| cost_moderate | naive | whois | MI_F1_pct | — | 0/18 |
| cost_moderate | poolact | whois | MV_F1_pct | — | 0/18 |
| cost_moderate | poolact | whois | MI_F1_pct | — | 0/18 |
| cost_tight | cached | whois | MV_F1_pct | — | 0/18 |
| cost_tight | cached | whois | MI_F1_pct | — | 0/18 |
| cost_tight | naive | whois | MV_F1_pct | — | 0/18 |
| cost_tight | naive | whois | MI_F1_pct | — | 0/18 |
| cost_tight | poolact | whois | MV_F1_pct | — | 0/18 |
| cost_tight | poolact | whois | MI_F1_pct | — | 0/18 |
| cost_free | cached | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_free | cached | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_free | naive | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_free | naive | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_free | poolact | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_free | poolact | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_moderate | cached | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_moderate | cached | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_moderate | naive | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_moderate | naive | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_moderate | poolact | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_moderate | poolact | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_tight | cached | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_tight | cached | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_tight | naive | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_tight | naive | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_tight | poolact | nasbench101 | BoN_Gap_pct | — | 0/3 |
| cost_tight | poolact | nasbench101 | MI_Gap_pct | — | 0/3 |
| cost_free | cached | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_free | cached | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_free | naive | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_free | naive | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_free | poolact | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_free | poolact | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_moderate | cached | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_moderate | cached | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_moderate | naive | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_moderate | naive | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_moderate | poolact | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_moderate | poolact | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_tight | cached | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_tight | cached | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_tight | naive | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_tight | naive | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_tight | poolact | nasbench201 | BoN_Gap_pct | — | 0/3 |
| cost_tight | poolact | nasbench201 | MI_Gap_pct | — | 0/3 |
| cost_free | cached | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_free | cached | paramnet | MI_Gap_pct | — | 0/3 |
| cost_free | naive | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_free | naive | paramnet | MI_Gap_pct | — | 0/3 |
| cost_free | poolact | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_free | poolact | paramnet | MI_Gap_pct | — | 0/3 |
| cost_moderate | cached | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_moderate | cached | paramnet | MI_Gap_pct | — | 0/3 |
| cost_moderate | naive | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_moderate | naive | paramnet | MI_Gap_pct | — | 0/3 |
| cost_moderate | poolact | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_moderate | poolact | paramnet | MI_Gap_pct | — | 0/3 |
| cost_tight | cached | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_tight | cached | paramnet | MI_Gap_pct | — | 0/3 |
| cost_tight | naive | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_tight | naive | paramnet | MI_Gap_pct | — | 0/3 |
| cost_tight | poolact | paramnet | BoN_Gap_pct | — | 0/3 |
| cost_tight | poolact | paramnet | MI_Gap_pct | — | 0/3 |

## 耗时与费用口径

| 项目 | 秒/次/token |
|---|---:|
| valid_agent_rows | 0 |
| sum_agent_wall_seconds | — |
| sum_simulated_feedback_cost_seconds | — |
| sum_logical_api_calls | — |
| sum_trace_input_tokens | — |
| sum_trace_output_tokens | — |
| sum_subprocess_attempt_wall_seconds | — |
| study_execution_span_seconds | — |

模拟反馈费用只表示 benchmark 预算；并发 agent/subprocess 墙钟求和会重复计时。真实执行跨度为最早开始至最晚结束，包含排队/重试/空档；完整 HTTP 尝试与 usage 以原始 API dump 为准。

## 查验路径与指标

逐项索引见 artifacts.csv，逐 agent 原始指标见 agents.csv，逐任务分数见 task_metrics.csv，汇总见 aggregate_metrics.csv / summary.json。每条记录保留原始路径与 SHA256；各输出为新目录，原始结果不覆盖。

Gap 按每条有效性能计算 max(0,(perf−mean)/(best−mean)×100)，先均值各 task 的 repeats、后均值各 family 的 tasks；可以超过 100。PoolAct MI 先分别计算每 agent 的 clipped Gap。Audit EA 是证据集合精确匹配，独立于 label 是否正确。

Kimi-K3/本地提供商是新增设置；PoolAct 使用当前 corrected locked 协议，历史论文含 locked/prelock 混合行，不能声称字节级或原模型复现。论文 tuning outer repeat 历史设定未公开；正式 full 阶段为一个 N=4 pool，smoke 为 N=2。非 full 阶段表格仅表示本阶段选定子集。设置与偏离详见 protocol/PAPER_ALIGNMENT.md。

归一化 oracle：/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/data/hpo_tuning/oracle3.json，SHA256 f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e。
Manifest：/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/full/manifest.dry-run.json，SHA256 bb7feac51f342837fca545c4adf0dc1cef80449b120e9101898eb7b7e7032b4d。
