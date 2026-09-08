# R10：native 任务提示集成遗漏

记录时间：2026-09-08 04:23 UTC。这是实现诊断，不是性能效应估计。

## 已证实的事实

冻结主代码 v2（源码指纹 `972aa9db9c2d640634d392c3e48882d893a42704a73ece371b860dd7517a37b9`）只把系统提示转换为 native 协议，原样传入任务的用户 context。三个任务仍含可信代码生成的文本调用示例：

| v2 位置 | 用户提示片段 |
| --- | --- |
| `expgym/task_restricted_search.py:360` | `Action format:` 与 `Action: search ...` |
| `expgym/task_tuning.py:844`、`:857` | builtin 与 HPO 都使用 `Action format: Action: evaluate_config ...` |
| `expgym/task_evidence_audit.py:269` | `Action: human_feedback ...` |

`expgym/react_loop.py:194` 附近仅转换 `sys_text`，随后直接附加 `context.strip()`。三个任务的 `build_instruction_notes` 均为空；题目正文不是这个问题的来源。

真实反例为 [PoolAct Search Moderate 首轮 raw](../scenario_runs/k3_smoke_1203474_v2/dumps/poolact__restricted_search__cost_moderate/6d502b1c7288456b974b625ee837b50a.json)：

- request ID：`6d502b1c7288456b974b625ee837b50a`；client ID：`7e9604ef2d88407d843c7b234e59b86d`。
- 文件 SHA256：`186b455fb82c72b3e4ef88abaa0355442900373f2c2ef9f8f5f9c9d4a1dca025`。
- 实际请求发送 search function schema、`tool_choice=auto`、`parallel_tool_calls=false`；系统要求原生函数调用，用户 context 同时给出文本 Action 示例。
- 模型返回 content 为 `Action: search {"query": "husband of Jeanette Byrd"}`，没有 native tool call。完整 reasoning 与响应保留。
- 这是首试成功交付；正常 agent horizon 内记录一次协议修复，未触发 HTTP 重试或免费重抽。不能把它记为服务传输失败。

## 归因边界

这是新增 native 集成中的跨任务遗漏，不是“上游文本协议示例本身错误”。上游 HEAD `703719150e8d44712ace50d6439686423dcd1328` 的循环原本使用文本协议；把这些文本说明与新增 native 系统提示组合后才产生矛盾。因此用户关于“整理/集成过程中引入问题”的怀疑有具体依据。

结构性提示矛盾已由实际 wire 与独立源码检查共同证实。尚不能证明它是这一次模型文本响应的唯一原因，更不能据此解释全部旧结果或预告 PoolAct 必然提升。旧实验的文本协议/模型模板问题、共享状态问题等仍按原 [三版本复审](REVIEW.zh.md) 分别归因。

前序 fake 的 auto backend 解析为 text；原 native 测试主要覆盖系统与合成 context，未覆盖真实任务 user context。这是验收覆盖缺口。45 条 v2 场景的留存、重评分或传输通过，不意味着提示兼容性通过。

## 修补范围与验收

隔离候选见 [native_task_context_v3](../patches/native_task_context_v3/)。只修改代码生成的调用说明，不修改题目/文档、答案格式、数据、预算、指标或评分。

1. 共用能力驱动的协议 resolver；demo、sweep、PoolAct 与循环使用相同解析规则，不按模型名分支。
2. 三个任务 builder 接收已解析的 text/native；默认 text 输出必须与冻结 v2 逐字节兼容，覆盖 builtin 与全部九个 HPO 提示分支。单测使用小型内存配置空间，不等于实际完整 HPO 数据集运行。
3. 保留数据中的字面 `Action`、`Thought`，不正则清洗任意 context。公共直接库调用者须自行用共享 resolver 构造匹配的任务 context。
4. 模拟传输使用真实客户端、真实任务 builder，检查三个生产入口、三种 PoolAct 策略、完整 system/user、assistant reasoning、schema、tool ID 及续轮。
5. 保持执行合同先于 backend capability 属性读取。候选曾短暂提前 resolver；全套回归测试与独立检查发现后已要求恢复该顺序，不将失败候选当作最终验收。
6. 完整静态检查与 Python 3.7 定向检查后建立新源码验收；原 45 条完成并独立审计前，不修改其冻结主源码。
7. v3 另跑小规模真实提示路径 gate。v2 A21 dry-run 不执行，需新 v3 dry-run 与明确放行记录。

当前状态以 [STATUS](../STATUS.zh.md) 为准；此诊断保留发现时证据，不覆盖原始运行报告。
