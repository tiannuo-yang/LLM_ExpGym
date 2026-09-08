# Kimi-K3：ExpGym / PoolAct 全量结果

模型：kimi-k3；实验类型：Custom study。本阶段结果和原始 API dump 均通过对应审计。

## 覆盖与核心结果

| 项目 | 本阶段通过/计划 | 正式全量目标 |
|---|---|---|
| ExpGym traces | 303/303 | 303 |
| PoolAct results | 513/513 | 513 |
| PoolAct agent traces | 2052/2052 | 2052 |
| 全部 agent traces | 2355/2355 | 2355 |
| 论文 PoolAct 子集 results | 192/192 | 192 |
| 论文 PoolAct 子集 agents | 768/768 | 768 |

### ExpGym：七维度宽表

数值单位为 %，所有指标均为越高越好；Gap 是相对随机均值的改进比例，不是剩余误差。Gap 每 trace 先归一化并裁剪至不低于 0，再按 repeats/task 与 tasks/family 求均值，可以超过 100。

| Regime | ParamNet Gap | NAS201 Gap | NAS101 Gap | whois F1 | whatis F1 | Audit LA | Audit EA |
|---|---|---|---|---|---|---|---|
| Free | 79.91 | 85.64 | 82.02 | 27.94 | 10.59 | 84.62 | 55.81 |
| Moderate | 71.45 | 88.03 | 76.90 | 30.64 | 5.88 | 84.77 | 55.51 |
| Tight | 75.17 | 85.45 | 51.22 | 11.22 | 0.00 | 83.41 | 54.15 |

### PoolAct：论文子集

Moderate/Tight；正式子集为 18 whois + 13 Audit + NAS101:A。MV 是多数票、MI 是 agent 均值、BoN 是 best-of-N；Tuning MI 逐 agent 先算 clipped Gap。

| Regime | Strategy | whois MV | whois MI | Audit LA | Audit EA | NAS101A BoN | NAS101A MI |
|---|---|---|---|---|---|---|---|
| Moderate | naive | 31.26 | 25.53 | 83.26 | 52.49 | 99.57 | 98.06 |
| Moderate | cached | 28.16 | 31.68 | 83.71 | 53.39 | 99.22 | 95.16 |
| Moderate | poolact | 29.88 | 29.04 | 82.81 | 52.49 | 98.50 | 72.68 |
| Tight | naive | 25.45 | 17.11 | 84.16 | 54.30 | 99.26 | 92.45 |
| Tight | cached | 17.04 | 13.92 | 85.07 | 55.20 | 98.55 | 91.95 |
| Tight | poolact | 22.59 | 19.84 | 82.81 | 53.85 | 98.76 | 97.90 |

全量扩展（含 cost_free、whatis 和其余 HPO tasks）独立导出：[PoolAct full extension CSV](<poolact_full_extension.csv>)。

Free→Tight 变化（百分点）：ParamNet Gap -4.74；NAS201 Gap -0.19；NAS101 Gap -30.80；whois F1 -16.72；whatis F1 -10.59；Audit LA -1.21；Audit EA -1.66。

Moderate 下 PoolAct−naive（百分点）：whois MV -1.38；Audit LA -0.45；NAS101A BoN -1.07。

Tight 下 PoolAct−naive（百分点）：whois MV -2.86；Audit LA -1.36；NAS101A BoN -0.50。

## 耗时、调用与运行证据

| 指标 | 值 |
|---|---|
| 真实执行跨度（秒） | 4899.92 |
| 全部 subprocess 尝试累计（秒，含并发重叠） | 66248.90 |
| 其中复用 pilot 的原始尝试（秒） | 8593.16 |
| 历史尝试缺失耗时条数 | 0 |
| 模拟反馈预算合计（秒，非实际墙钟） | 16257831.53 |
| 当前结果逻辑成功调用 | 9068 |
| 当前结果 HTTP 尝试（含重试） | 9068 |
| 当前结果失败 HTTP 尝试 | 0 |
| 当前结果 input tokens（含重试） | 17977502 |
| 当前结果 output tokens（含重试） | 2434522 |
| 历史未选中 HTTP 尝试 | 0 |
| finish_reason=length 次数 | 4 |

并发累计秒数不可当作端到端墙钟；复用 pilot 的原始执行成本单列。reasoning tokens 若被提供，已包含在 output tokens 中，不再加一次。未知时间或未完整报告的 token 总量保留 null（表中 —）。

以上调用统计仅覆盖本阶段 manifest，不是整个开发/恢复过程的总消耗。跨阶段已留存评测请求及其去重范围见 [项目 API 消耗清单](<../project_usage_final/project_usage_inventory.json>)；其他版本、smoke 与失败任务不混入本表成绩。服务验收探针和后台 health 请求不属于评测 dump 清单；Slurm 分配时长仍包含服务占用时间。

已观察到 provider 标记的 length 截断，这是输出 token cap 的实现边界及协议诊断信息；保留原始回答和评分。示例：[dump 1](<../../dumps/full-full_v3-ad4275b6/poolact__restricted_search__11__cost_free/acdf7057d7484dfeb18a336e1ca8fb3b.json>)、[dump 2](<../../dumps/full-full_v3-ad4275b6/poolact__restricted_search__26__cost_free/8a9c4a68363941dbbf2989c0801a164e.json>)、[dump 3](<../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__8__cost_tight/a458d7a79cfa41b8afe514078fd493bc.json>)；全部路径见 delivery.json 的 observed_reasoning.length_responses。

| Slurm job | Account | Nodes | GPUs | Replicas | 每副本并行 | 采集时状态 | 最终状态 |
|---|---|---|---|---|---|---|---|
| 1203299 | k2p | 8 | 64 | 4 | {"nodes": 2, "tp": 16, "ep": 16} | CANCELLED by 1071 | CANCELLED by 1071 |

| Allocated GPU-hours 范围 | 采集时已知值 | 最终值 |
|---|---|---|
| 服务 allocation | 202.68 | 202.68 |
| 本项目全部 owned allocations | 218.70 | 218.70 |

Slurm 最终状态和最终总量只取明确 final=true 的 receipt；服务 ready 或部署文件不等于作业已结束。运行中快照不是最终成本。Allocated GPU-hours 为已确认分配 GPU 数 × allocation 墙钟，包含加载、验证及空闲，不代表 GPU 利用率，也不重复累加 step/extern。

Pilot 外推证据：[runtime estimate](<../pilot_v3_runtime_estimate/runtime_estimate.json>)；原预测剩余小时范围 [1.6201506947946998, 1.8694046478400381]，这是当时预测，不替代上述实测耗时。

## 设置、偏离与协议诊断

请求参数：chat_template_kwargs={"thinking": false}；max_tokens=8192；max_steps/max_evals=30/30；PoolAct agents=4；协议=paper-graph-lock-v2。

原始选中请求里 9068/9068 条匹配上述 thinking/token cap，9068 条保留 request payload。

实际选中响应中 170/9068 条含非空 reasoning_content，共 631606 字符。thinking=false 表示请求设定；reasoning_content 也可能来自服务 parser 对标记的分段，不能仅据此判断模型中途开启思考，或凭 token counter 为 0 声称没有该文本字段。

Provider reasoning token counter：0（9068/9068 次有报告，嵌套/顶层来源冲突 0 次）；非空 reasoning 文本且报告 0 token 的响应 170 次。字段来源冲突与文本/计数观察警告均保留在 delivery.json 的 dump_warnings。

服务验收另有明确偏差：本次 thinking=false 请求不同于 K3 推荐的 always-thinking 用法；服务原生默认未被修改。

Kimi-K3 与本地 SGLang 是论文外的新模型/提供商；max_tokens=8192 是本次记录的实现参数。当前协议记录为 paper-graph-lock-v2；paper-graph-lock-v2 为修正后的 locked 实现，论文历史表含 locked/prelock 两类。历史 tuning outer-repeat 数量未公开。Audit EA 为证据集合精确匹配，不要求 label 同时正确。

NAS101 B/C 提示与编码差异（仅适用于证据绑定的本次 source）：B/C 原提示沿用 A 型二进制边描述，但实际 B 为反序 column bit-ID 编码，C 为 top-k 边优先值编码。本次保留原 paper/repo 提示，候选修正 patch 未应用；这限制 B/C 结果的解释，不代表已测得该差异对分数的因果影响。证据：[NAS101 hints status](<../../protocol/nas101_hints_status_evaluation_recovery_v3.json>)。

| 系统 | aborted=true | 总 agents | 原字段记录到的终止原因 | 终止原因未记录 |
|---|---|---|---|---|
| expgym | 262 | 303 | {"missing_action": 238, "time_budget_exceeded": 24, "natural_answer": 41} | 0 |
| poolact | 1720 | 2052 | — | 2052 |

上表仅统计序列化原字段；未记录显示 null（—），不代表终止次数为零。aborted 可由预算、horizon 或指令解析触发，随后仍可能强制回答并通过重评分；不把有效语义零分标成软件失败。

### 独立诊断观察与推断（不补写原字段）

以下仅使用与已审计 client_id/成功 request_id 对齐的 schema2 诊断。ExpGym 的 trace_v2_outcome 来源为原字段；PoolAct 的 inferred_from_saved_forced_prompt 来源是保存的强制回答提示与 aborted 标记推断，不能当作已序列化的 termination_reason。

| 范围 | agents | missing_action（含推断） | forced-final 调用 | 原始 native 响应 | native 后 missing_action traces |
|---|---|---|---|---|---|
| all | 2355 | 1829 | 1982 | 967 | 962 |
| expgym | 303 | 238 | 262 | 126 | 126 |
| poolact | 2052 | 1591 | 1720 | 841 | 836 |

native 是响应中的 K3 XTML 工具标记观察；与 missing_action 的先后共现不单独证明因果，也不等于工具实际执行或语义评分失败。

| 范围 | 常规响应 >8000 字符 | cap 后丢失 Action 解析候选 | 其中已知工具名 + 合法 JSON 候选 |
|---|---|---|---|
| all | 71 | 22 | 18 |
| expgym | 9 | 3 | 2 |
| poolact | 62 | 19 | 16 |

8000 字符 cap 是常规响应解析前的字符上限，独立于 API 的 max_tokens；forced-final 不受此字符 cap 约束。解析候选可能只是 Thought 中引用的 Action:。已知工具名 + 合法 JSON 仅为静态检查，不证明参数 schema 合法、工具可执行或截断导致最终得分变化；额外逐例复核的结论应查其独立证据。

补充诊断：[protocol diagnostics](<../full_v3_protocol_final.json>)。

## 查验入口

- [manifest](<../../runs/full_v3/manifest.json>)
- [summary](<../full_v3_results_final/summary.json>)
- [audit](<../full_v3_audit_final/audit.json>)
- [dump_audit](<../full_v3_dumps_final/raw_dump_audit.json>)
- [artifacts_csv](<../full_v3_results_final/artifacts.csv>)
- [agents_csv](<../full_v3_results_final/agents.csv>)
- [dataset_manifest](<../../data_runtime/dataset_manifest.json>)
- [oracle](<../../../LLM_ExpGym/data/hpo_tuning/oracle3.json>)
- [paper_alignment](<../../protocol/PAPER_ALIGNMENT.md>)
- [service_receipt](<../../serving/ACCEPTANCE.json>)
- [slurm_receipt](<../../serving/reports/final_accounting_20260907_after_cleanup/slurm_receipt.json>)
- [task_metrics_csv](<../full_v3_results_final/task_metrics.csv>)
- [aggregate_metrics_csv](<../full_v3_results_final/aggregate_metrics.csv>)
- [audit_orders](<../../../LLM_ExpGym/configs/audit_hypothesis_orders.json>)
- [runtime_estimate](<../pilot_v3_runtime_estimate/runtime_estimate.json>)
- [protocol_diagnostics](<../full_v3_protocol_final.json>)
- [slurm_receipt_raw](<../../serving/reports/final_accounting_20260907_after_cleanup/sacct.psv>)
- [nas101_hints_status](<../../protocol/nas101_hints_status_evaluation_recovery_v3.json>)
- [interpretation](<../full_v3_interpretation.zh.md>)
- [generation_run_progress](<../full_v3_generation_completed/progress.json>)
- [verified_resume](<../resume_full_v3.comparison.json>)
- [source_provenance](<../../provenance/evaluation_recovery_v3/manifest.json>)
- [static_validation](<../../data_runtime/validation_v3/artifact_integrity.json>)
- [checkpoint_integrity](<../../provenance/initial/checkpoint.json>)
- [reasoning_diagnostic](<../../serving/REASONING_MODE_DIAGNOSTIC.json>)
- [output_sanity](<../../serving/reports/full_v3_output_sanity_final/summary.json>)
- [cap_review](<../full_v3_cap_review/review.json>)
- [audit_label_baseline](<../audit_label_baseline/baseline.json>)
- [hpo_independent](<../full_v3_hpo_independent_review/independent_post_resume_final.json>)
- [search_independent](<../full_v3_search_independent_review_post_resume/comparison.json>)
- [audit_independent](<../full_v3_audit_independent_review/independent_post_resume_final.json>)
- [project_usage_inventory](<../project_usage_final/project_usage_inventory.json>)
- [project_usage_independent](<../project_usage_final_independent_review/comparison.json>)
- [release_confirmation](<../../serving/reports/final_accounting_20260907_after_cleanup/release_confirmation.json>)

完整文件路径、SHA256、输入 CSV/JSON 一致性和逐格来源见 [delivery.json](<delivery.json>)；原始数据及 dump 保留在索引指向的位置。
