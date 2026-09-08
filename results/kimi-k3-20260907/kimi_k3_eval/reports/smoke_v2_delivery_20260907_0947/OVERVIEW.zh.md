# SMOKE 验证报告：非正式全量结果

> 本报告只验证 SMOKE 所选子集；不代表 303 ExpGym + 513 PoolAct 的正式矩阵完成，也不表示论文设定的统计结果。

模型：kimi-k3；实验类型：Custom study。本阶段结果和原始 API dump 均通过对应审计。

## 覆盖与核心结果

| 项目 | 本阶段通过/计划 | 正式全量目标 |
|---|---|---|
| ExpGym traces | 9/9 | 303 |
| PoolAct results | 18/18 | 513 |
| PoolAct agent traces | 36/36 | 2052 |
| 全部 agent traces | 45/45 | 2355 |
| 论文 PoolAct 子集 results | 18/18 | 192 |
| 论文 PoolAct 子集 agents | 36/36 | 768 |

### ExpGym：七维度宽表（SMOKE 所选小样本）

数值单位为 %；Gap 每 trace 先归一化并裁剪至不低于 0，再按 repeats/task 与 tasks/family 求均值，可以超过 100。

| Regime | ParamNet Gap | NAS201 Gap | NAS101 Gap | whois F1 | whatis F1 | Audit LA | Audit EA |
|---|---|---|---|---|---|---|---|
| Free | — | — | 96.78 | 35.29 | — | 94.12 | 35.29 |
| Moderate | — | — | 96.32 | 0.00 | — | 94.12 | 41.18 |
| Tight | — | — | 98.34 | 35.29 | — | 94.12 | 35.29 |

### PoolAct：论文子集（SMOKE 所选小样本）

Moderate/Tight；正式子集为 18 whois + 13 Audit + NAS101:A。MV 是多数票、MI 是 agent 均值、BoN 是 best-of-N；Tuning MI 逐 agent 先算 clipped Gap。

| Regime | Strategy | whois MV | whois MI | Audit LA | Audit EA | NAS101A BoN | NAS101A MI |
|---|---|---|---|---|---|---|---|
| Moderate | naive | 0.00 | 17.65 | 94.12 | 35.29 | 98.80 | 98.76 |
| Moderate | cached | 0.00 | 0.00 | 88.24 | 35.29 | 98.88 | 96.96 |
| Moderate | poolact | 44.44 | 39.87 | 94.12 | 35.29 | 95.62 | 90.69 |
| Tight | naive | 44.44 | 22.22 | 94.12 | 35.29 | 85.76 | 85.76 |
| Tight | cached | 0.00 | 17.65 | 94.12 | 35.29 | 98.34 | 92.05 |
| Tight | poolact | 0.00 | 0.00 | 94.12 | 35.29 | 93.62 | 89.69 |

上表空白表示本阶段未覆盖；非空格也只来自本阶段所选 task。每格的样本数和原始路径保存在 delivery.json 的 tables.cells。

SMOKE 本阶段已覆盖的 PoolAct 扩展（尚非全量）独立导出：[PoolAct full extension CSV](<poolact_full_extension.csv>)。

## 耗时、调用与运行证据

| 指标 | 值 |
|---|---|
| 真实执行跨度（秒） | 301.30 |
| 全部 subprocess 尝试累计（秒，含并发重叠） | 1347.65 |
| 其中复用 pilot 的原始尝试（秒） | — |
| 历史尝试缺失耗时条数 | 0 |
| 模拟反馈预算合计（秒，非实际墙钟） | 155925.56 |
| 当前结果逻辑成功调用 | 138 |
| 当前结果 HTTP 尝试（含重试） | 138 |
| 当前结果失败 HTTP 尝试 | 0 |
| 当前结果 input tokens（含重试） | 327825 |
| 当前结果 output tokens（含重试） | 58135 |
| 历史未选中 HTTP 尝试 | 0 |
| finish_reason=length 次数 | 0 |

并发累计秒数不可当作端到端墙钟；复用 pilot 的原始执行成本单列。reasoning tokens 若被提供，已包含在 output tokens 中，不再加一次。未知时间或未完整报告的 token 总量保留 null（表中 —）。

| Slurm job | Account | Nodes | GPUs | Replicas | 每副本并行 | 采集时状态 | 最终状态 |
|---|---|---|---|---|---|---|---|
| 1203299 | — | 8 | 64 | 4 | {"nodes": 2, "tp": 16, "ep": 16} | — | — |

| Allocated GPU-hours 范围 | 采集时已知值 | 最终值 |
|---|---|---|
| 服务 allocation | — | — |
| 本项目全部 owned allocations | — | — |

Slurm 最终状态和最终总量只取明确 final=true 的 receipt；服务 ready 或部署文件不等于作业已结束。运行中快照不是最终成本。Allocated GPU-hours 为已确认分配 GPU 数 × allocation 墙钟，包含加载、验证及空闲，不代表 GPU 利用率，也不重复累加 step/extern。

Runtime estimate：未附证据（null）。

## 设置、偏离与协议诊断

请求参数：chat_template_kwargs={"thinking": false}；max_tokens=8192；max_steps/max_evals=4/3；PoolAct agents=2；协议=paper-graph-lock-v2。

原始选中请求里 138/138 条匹配上述 thinking/token cap，138 条保留 request payload。

实际选中响应中 7/138 条含非空 reasoning_content，共 18671 字符。thinking=false 表示请求设定；reasoning_content 也可能来自服务 parser 对标记的分段，不能仅据此判断模型中途开启思考，或凭 token counter 为 0 声称没有该文本字段。

Provider reasoning token counter：0（138/138 次有报告，嵌套/顶层来源冲突 0 次）；非空 reasoning 文本且报告 0 token 的响应 7 次。字段来源冲突与文本/计数观察警告均保留在 delivery.json 的 dump_warnings。

服务验收另有明确偏差：本次 thinking=false 请求不同于 K3 推荐的 always-thinking 用法；服务原生默认未被修改。

Kimi-K3 与本地 SGLang 是论文外的新模型/提供商；max_tokens=8192 是本次记录的实现参数。当前协议记录为 paper-graph-lock-v2；paper-graph-lock-v2 为修正后的 locked 实现，论文历史表含 locked/prelock 两类。历史 tuning outer-repeat 数量未公开。Audit EA 为证据集合精确匹配，不要求 label 同时正确。

| 系统 | aborted=true | 总 agents | 记录到的终止原因 | 终止原因未记录 |
|---|---|---|---|---|
| expgym | 9 | 9 | {"missing_action": 6, "max_evaluations_reached": 3} | 0 |
| poolact | 34 | 36 | {} | 36 |

aborted 可由预算、horizon 或指令解析触发，随后仍可能强制回答并通过重评分；这里展示协议行为，不把有效语义零分标成软件失败。

补充诊断：[protocol diagnostics](<../smoke_v2_protocol_20260907_0944.json>)。

## 查验入口

- [manifest](<../../runs/smoke_v2/manifest.json>)
- [summary](<../smoke_v2_results_20260907_0945/summary.json>)
- [audit](<../smoke_v2_audit_20260907_0944/audit.json>)
- [dump_audit](<../smoke_v2_dumps_20260907_0944/raw_dump_audit.json>)
- [artifacts_csv](<../smoke_v2_results_20260907_0945/artifacts.csv>)
- [agents_csv](<../smoke_v2_results_20260907_0945/agents.csv>)
- [dataset_manifest](<../../data_runtime/dataset_manifest.json>)
- [oracle](<../../../LLM_ExpGym/data/hpo_tuning/oracle3.json>)
- [paper_alignment](<../../protocol/PAPER_ALIGNMENT.md>)
- [service_receipt](<../../serving/runs/1203299/acceptance.json>)
- [task_metrics_csv](<../smoke_v2_results_20260907_0945/task_metrics.csv>)
- [aggregate_metrics_csv](<../smoke_v2_results_20260907_0945/aggregate_metrics.csv>)
- [audit_orders](<../../../LLM_ExpGym/configs/audit_hypothesis_orders.json>)
- [protocol_diagnostics](<../smoke_v2_protocol_20260907_0944.json>)
- [reasoning_diagnostic](<../../serving/REASONING_MODE_DIAGNOSTIC.json>)

完整文件路径、SHA256、输入 CSV/JSON 一致性和逐格来源见 [delivery.json](<delivery.json>)；原始数据及 dump 保留在索引指向的位置。
