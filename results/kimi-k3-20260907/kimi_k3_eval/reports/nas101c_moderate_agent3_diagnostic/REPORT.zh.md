# full_v2：NAS101C Moderate / naive agent 3 评分失败

结论：这是 JSON 评分关联的独立边界，并非 benchmark 数值不稳定、API 失败或未知参数。末次响应包含两个真正的行首 Answer，当前提取器选择第一个解释性文本；旧子串查找却给整段非 JSON 文本绑定了其中嵌入配置的非零分，导致严格 JSON 重评分不一致。

当前冻结源码为 55637cee193071b35f06c3356e706d6f652de738a5340d2c4950d5966cf1a0a3。此次仅离线复放，没有调用 LLM API，没有修改仓库或正式实验结果。

## 精确复放

client_id：28ad2bfa6e37435da3638778796e5fde。共 6 条成功响应；每次离线 run_react_loop 发出的 messages 均与其原始 request_payload.messages 逐字段完全相同，5 次真实本地 evaluator 调用如下。

| Evaluation | 性能 | 模拟 cost 秒 |
|---|---:|---:|
| 1 | 0.9366319378217062 | 3457.2479248046875 |
| 2 | 0.8919604818026224 | 5816.525146484375 |
| 3 | 0.845886747042338 | 13875.8564453125 |
| 4 | 0.9294871687889099 | 14599.13818359375 |
| 5 | 0.9388020833333334 | 3023.324951171875 |

总模拟 cost 为 40772.09265136719 秒，预算为 112038.63037109375 秒；不是预算耗尽故障。

末次 raw 为 fbe2ec8734c94fb8b64905add2ff63d1.json，SHA256：6c08b93e50e2e4cf7397203e3920e9c3d1be1eed78b6adfe270e4afe57b18291。第 15 行的 Answer 后是 “I should continue exploring...” 等解释，第 25 行才是完整最终 JSON。当前提取产生 1750 字符非 JSON answer；它包含第 5 次 Action 的原文，因此 _lookup_answer_metrics 的子串分支关联到第 5 次分数，导致已有最佳配置 fallback 被跳过。

| 离线分支 | runtime answer_perf | 独立 recomputed_perf | score_check |
|---|---:|---:|---|
| 冻结当前代码 | 0.9388020833333334 | 0 | false |
| 仅进程内替换 JSON canonical-only 查找 | 0.9388020833333334 | 0.9388020833333334 | true |

候选分支没有改 Answer 标签选择。非 JSON answer 不再冒领 JSON 配置分数，因此进入既有 best-evaluated fallback，最终 answer 等于第 5 次已评估的 460 字符 JSON。两分支全部 6 次请求、5 次 eval_records、tool_records 及模拟开销完全一致；未新增模型调用。

## 最小建议与兼容性

只收紧 _lookup_answer_metrics：canonical JSON eval record 必须与完整 final JSON canonical 相等；只有非 JSON 旧工具参数可继续使用子串匹配。非 JSON final 引用一段 JSON 不应直接取得其分数。

该 helper 只在自然终止/强制 finalization 时被调用，不影响 Action 解析、工具执行、预算或 Observation。有效 JSON 保留原等价匹配；cfg_custom 等非 JSON 工具 ID 保留原子串行为。不建议为此全局改成“最后一个 Answer 胜出”，它额外定义了多标签优先级，且不能统一修复 markdown/正文包裹 JSON 的评分关联问题。

候选单行规则及回归补丁由 data_runtime 独立准备；本任务没有应用源码补丁。建议验收至少覆盖完整/重排/多行 JSON、非 JSON 包裹 JSON→fallback、多个 Answer、非 JSON 工具 ID、零分和 over-budget fallback、外部 Search/Audit scorer。

## PoolAct END 与后续 prompt 的精确影响

scripts/run_poolact.py 第 439 行确实把最终 answer 交给 coordinator.graph.record_end，因此持久化 END 节点/边及最终汇总可能变化，不能称为所有模式下都仅影响展示。

但本项目当前 locked PoolAct wiring 为每个 agent 始终传入 AgentClock；make_graph_augmenter 使用该 clock.now 作为 visible_before。parallel_cache.py 第 956–983 行在此模式下会隐藏 END 节点，并过滤所有含 END 的边。因此在当前绑定下，final answer 的改变不会通过 END 改变其他 agent 收到的共享图 prompt。

本报告动态构造相同五条评估、不同 final answer 的两份图，结果为：当前带 clock 的注入文本逐字相同；不传 clock 的视图不同。这个结论只适用于当前时间过滤模式，不应推广到无 clock 的其他 PoolAct 配置；不同运行时调度也仍可能影响并发事件顺序。

## 查验

- [完整离线证据](evidence.json)：逐请求路径/SHA、精确 request 对账、原/候选 final 与五条 eval_records、带/不带 clock 的图文本。
- [只读复放脚本](replay.py)：候选函数只在一个独立 Python 进程中临时替换，退出即恢复，不修改任何源码文件。
- [原始末次 dump](../../dumps/full-full_v2-e0565217/poolact__tuning__hpobench_nasbench101_C__cost_moderate/fbe2ec8734c94fb8b64905add2ff63d1.json)。
- [原始失败日志](../../logs/full-full_v2-e0565217/poolact__tuning__hpobench_nasbench101_C__cost_moderate/stdout.log)。

复现：

    LLM_ExpGym/.venv/bin/python -W ignore kimi_k3_eval/reports/nas101c_moderate_agent3_diagnostic/replay.py

以上是故障诊断与候选规则验证，不是修改后的正式实验成绩，也不改变旧 trace/source 指纹。若采用修复，仍须按根任务的统一版本与审计约定处理。
