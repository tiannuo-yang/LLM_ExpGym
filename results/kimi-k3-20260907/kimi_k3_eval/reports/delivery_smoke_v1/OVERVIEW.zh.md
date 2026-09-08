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
| Free | — | — | 96.56 | 35.29 | — | 94.12 | 35.29 |
| Moderate | — | — | 84.07 | 35.29 | — | 88.24 | 35.29 |
| Tight | — | — | 97.64 | 0.00 | — | 88.24 | 35.29 |

### PoolAct：论文子集（SMOKE 所选小样本）

Moderate/Tight；正式子集为 18 whois + 13 Audit + NAS101:A。MV 是多数票、MI 是 agent 均值、BoN 是 best-of-N；Tuning MI 逐 agent 先算 clipped Gap。

| Regime | Strategy | whois MV | whois MI | Audit LA | Audit EA | NAS101A BoN | NAS101A MI |
|---|---|---|---|---|---|---|---|
| Moderate | naive | 35.29 | 35.29 | 94.12 | 35.29 | 97.52 | 96.76 |
| Moderate | cached | 35.29 | 35.29 | 94.12 | 35.29 | 95.11 | 90.43 |
| Moderate | poolact | 35.29 | 35.29 | 88.24 | 35.29 | 99.02 | 98.53 |
| Tight | naive | 35.29 | 35.29 | 94.12 | 35.29 | 96.69 | 96.66 |
| Tight | cached | 0.00 | 0.00 | 88.24 | 35.29 | 98.55 | 98.51 |
| Tight | poolact | 0.00 | 17.65 | 94.12 | 35.29 | 98.80 | 92.28 |

上表空白表示本阶段未覆盖；非空格也只来自本阶段所选 task。每格的样本数和原始路径保存在 delivery.json 的 tables.cells。

全量扩展（含 cost_free、whatis 和其余 HPO tasks）独立导出：[PoolAct full extension CSV](<poolact_full_extension.csv>)。

## 耗时、调用与运行证据

| 指标 | 值 |
|---|---|
| 真实执行跨度（秒） | 315.22 |
| 全部 subprocess 尝试累计（秒，含并发重叠） | 1390.59 |
| 其中复用 pilot 的原始尝试（秒） | — |
| 历史尝试缺失耗时条数 | 0 |
| 模拟反馈预算合计（秒，非实际墙钟） | 101244.73 |
| 当前结果逻辑成功调用 | 136 |
| 当前结果 HTTP 尝试（含重试） | 136 |
| 当前结果失败 HTTP 尝试 | 0 |
| 当前结果 input tokens（含重试） | 308698 |
| 当前结果 output tokens（含重试） | 57243 |
| 历史未选中 HTTP 尝试 | 0 |
| finish_reason=length 次数 | 0 |

并发累计秒数不可当作端到端墙钟；复用 pilot 的原始执行成本单列。reasoning tokens 若被提供，已包含在 output tokens 中，不再加一次。未知时间或未完整报告的 token 总量保留 null（表中 —）。

| Slurm job | Account | Nodes | GPUs | Replicas | 每副本并行 | 最终状态 |
|---|---|---|---|---|---|---|
| 1203299 | k2p | 8 | 64 | 4 | {"nodes": 2, "tp": 16, "ep": 16} | — |

Slurm 最终状态只取已提供的 final receipt；服务 ready 或部署文件不等于作业已结束。

Runtime estimate：未附证据（null）。

## 设置、偏离与协议诊断

请求参数：chat_template_kwargs={"thinking": false}；max_tokens=8192；max_steps/max_evals=4/3；PoolAct agents=2；协议=paper-graph-lock-v2。

实际选中响应中 6/136 条含非空 reasoning_content，共 21707 字符。thinking=false 表示请求设定；reasoning_content 也可能来自服务 parser 对标记的分段，不能仅据此判断模型中途开启思考，或凭 token counter 为 0 声称没有该文本字段。

Kimi-K3 与本地 SGLang 是论文外的新模型/提供商；8192 token cap 是新增实现参数。当前 paper-graph-lock-v2 使用修正后的 locked 实现，论文历史表含 locked/prelock 两类；历史 tuning outer-repeat 数量未公开。Audit EA 为证据集合精确匹配，不要求 label 同时正确。

| 系统 | aborted=true | 总 agents | 记录到的终止原因 | 终止原因未记录 |
|---|---|---|---|---|
| expgym | 9 | 9 | {"missing_action": 7, "max_evaluations_reached": 2} | 0 |
| poolact | 35 | 36 | {} | 36 |

aborted 可由预算、horizon 或指令解析触发，随后仍可能强制回答并通过重评分；这里展示协议行为，不把有效语义零分标成软件失败。

独立 protocol diagnostics：未附证据（null）；上表仅从已审计 traces 直接计数。

## 查验入口

- [manifest](<../../runs/smoke/manifest.json>)
- [summary](<../smoke_results_20260907_0905/summary.json>)
- [audit](<../smoke_audit_20260907_0905/audit.json>)
- [dump_audit](<../smoke_dumps_20260907_0905/raw_dump_audit.json>)
- [artifacts_csv](<../smoke_results_20260907_0905/artifacts.csv>)
- [agents_csv](<../smoke_results_20260907_0905/agents.csv>)
- [dataset_manifest](<../../data_runtime/dataset_manifest.json>)
- [oracle](<../../../LLM_ExpGym/data/hpo_tuning/oracle3.json>)
- [paper_alignment](<../../protocol/PAPER_ALIGNMENT.md>)
- [service_receipt](<../../serving/runs/1203299/acceptance.json>)
- [slurm_receipt](<../../serving/runs/1203299/deployment.json>)

完整文件路径、SHA256、输入 CSV/JSON 一致性和逐格来源见 [delivery.json](<delivery.json>)；原始数据及 dump 保留在索引指向的位置。
