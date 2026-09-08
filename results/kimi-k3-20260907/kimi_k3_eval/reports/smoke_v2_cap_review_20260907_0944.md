# smoke_v2：8000字符截断导致一次 missing_action

只读复核确认：PoolAct / Evidence Audit 文档0 / Moderate / `cached` / agent1 的首轮原始响应含有当前解析器可识别的完整工具请求，但它位于8000字符之后，被仓库已有截断移除。随后实际保存的终止原因为 `Missing Action directive`，工具执行数为0，并触发一次强制最终回答。这里可以确认解析失败的直接原因，不能推断未截断后的最终得分会提高。

| 证据 | 值 |
|---|---|
| request_id | `2468d42804ca41ad9dccfda96aca46d7` |
| client_id | `dd9959a328634ad38ab0bcbb6cb60ca5` |
| 原始content长度 | 10,318个Python字符 |
| 唯一`Action:`的位置 | 从0计数的字符10,253 |
| API停止原因/输出量 | `stop`，2,174 completion tokens |
| 请求生成上限 | `max_tokens=8192`，本响应未达到 |
| 保存的首轮assistant消息 | 原始前8000字符加51字符截断标记，合计8051字符 |

原始末尾为：

```text
Let me call human_feedback for nda-1 first.Action: human_feedback {"nda_id": "nda-11", "evidence_ids": [53]}
```

尽管`Action:`与前一句直接相连，仓库 `_extract_action` 支持行内标签，未截断原文的返回值是工具名 `human_feedback` 和完整JSON `{"nda_id": "nda-11", "evidence_ids": [53]}`；工具名正确、参数类型符合接口，`nda-11`与segment53也存在于该请求上下文。前8000字符既无可解析Action，也无Answer；首轮保存文本与按原截断规则计算的文本完全一致。这里没有K3 native工具标签。诊断未执行工具或新增API调用，也未评价这条证据建议的语义正确性。

[原始API dump](../dumps/smoke-smoke_v2-21fa0add/poolact__evidence_audit__0__cost_moderate/2468d42804ca41ad9dccfda96aca46d7.json) 与 [agent轨迹](../runs/smoke_v2/poolact/evidence_audit/0/cost_moderate/cached/agents/agent_1.json) 记录随后调用 `6e632772b7c64dc3b536b1de19ea40c4` 的强制回答提示。最终LA=0.8823529411764706、EA=0.4117647058823529，评分复算通过；这些分数不能抹去上述交互中断。

这是 [react_loop.py:304](../../LLM_ExpGym/expgym/react_loop.py:304) 在解析前实施的**8000字符**上限，区别于API的**8192 token**生成上限。解析顺序见同文件:312–334，工具接口见 [task_evidence_audit.py:200](../../LLM_ExpGym/expgym/task_evidence_audit.py:200)。该行为来自原仓库，此次只记录局限，不修改协议或源码。

旧pilot的 `01f94c6127bd4d70b0eae41de72c471b` 是另一种情况：长Thought引用 `Action: evaluate_config in final? ...`，提取payload不是合法JSON，因此没有证据证明当时存在可执行Action被截掉；见 [旧pilot诊断v2](pilot_protocol_diagnostic_v2.md)。不能把所有静态解析候选统一当作已确认的截断因果。

校验和：原始dump SHA256 `27bf5d1c715d9c9b247ca719ff23ef47952e15c4014040299f48537fe958439a`；agent JSON SHA256 `34f5c64ec127f83aa60b0a3fbe56fb54ceb943abdd0d420155c4e6f202160251`。总体频次仍以 [smoke_v2协议诊断](smoke_v2_protocol_20260907_0944.json) 为准；该小规模smoke不能代替正式矩阵的发生率。
