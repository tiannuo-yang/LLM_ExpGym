# 正式终答与投票协议修复

本次修复不读取参考答案、不选择得分更高的候选，也不改变模型已经输出的实体、标签或证据 ID。源码已冻结；版本及逐文件 SHA-256 见 [PARSER_CODE_FREEZE.json](PARSER_CODE_FREEZE.json)。旧成绩和旧轨迹保持原件，正式重评分由全量回放产生，不能把此前 23 答案、19 个池的诊断子集当作正式处理范围。

## 接口与版本

| 接口/协议 | 正式版本或用途 |
|---|---|
| `tool_protocol.parse_final_answer(text, *, allow_unlabelled=True)` | 所有任务共享的文本终答边界；返回提取后的 payload 或 `None` |
| `ANSWER_PROTOCOL_VERSION` | `final-answer-boundary-v2` |
| `parse_audit_answer(payload)` | Audit 个体评分、池投票、诊断共用 JSON 包装解析，非法输入抛出 `ValueError` |
| `AUDIT_ANSWER_PROTOCOL_VERSION` | `audit-json-wrapper-v2` |
| `audit_label_key` / `audit_evidence_key` | 个体评分、池投票、诊断共用字段解释 |
| `AUDIT_FIELD_PROTOCOL_VERSION` | `audit-literal-label-legacy-evidence-v2` |
| `parse_search_answer(payload)` | Search 个体 F1 与投票共用原有名字集合解析 |
| `SEARCH_ANSWER_PROTOCOL_VERSION` | `search-name-set-v2` |
| `POOLACT_PROTOCOL_VERSION` | `paper-graph-lock-v4`，图修复单独核查，不能混同答案协议 |

`react_loop` 的 native 自然结束和 forced-final 允许裸文本，旧 text transport 的自然结束仍要求显式终答或完整结构化答案。两条运行入口与离线回放使用同一 `parse_final_answer`。调用者必须先拒绝 provider-native `tool_calls` 和 `finish_reason=length`；函数自身另外拒绝真实文本 `Action:` 指令。`LoopResult`、trace-v2 outcome 和池 aggregate 记录终答协议版本。

## 终答边界的允许与拒绝集

- 行首 `Answer:` / `Final Answer:` 及其列表、标题、加粗包装可作为正式标签。`**Answer:**`、`**Answer**:`、`__Answer:__` 等只去掉属于标签的闭合标记，不吞掉 payload 自身开头的 `**` 或 `_`。
- `Here is my final answer:` 之类前导说明、普通句子中的 `the answer:` 不是另一次提交，先按指令边界过滤，再计数。连续的空标签（如 `Final answer:` 后立即换行 `**Answer:**`）属于包装；不能把有实际内容的第一份答案当成空标签。
- `**Answer: Ada Lovelace**` 这种整个提交加粗的格式保持旧行提取器的 payload `Ada Lovelace**`。后续解释文字完整保留，交给原任务解析规则；不截取出一个“看起来正确”的名字。
- 引号、代码示例、Markdown 引用、显式 `think/analysis/reasoning` 区域不能提交答案。粗体名字后面的所有格，例如 `**Bettye Gendron**'s`，与普通名字所有格一样处理，不能误作开引号而吞掉后面的真实答案。
- 两个**非空**正式 `Answer:` 指令、先提交裸 JSON 后又提交带标签答案、真实工具动作与答案混杂，均拒绝。不会根据最后出现、投票结果或参考答案选择一个。即使 Search 两处列出了相同名字，只要是两份非空提交，也沿用这一统一拒绝规则，不额外执行任务语义消歧。
- 原通用 `parse_json_answer` 仍要求完整有限 JSON；不能从任意推理正文挖出 JSON 对象。它的严格契约没有因 Audit 对尾述的兼容而放宽。

行标签后的 payload 保持字面内容；历史 `structured_final_answer` 对完整 JSON 的等价序列化继续保留，以兼容原本已接受的裸 fenced JSON。任何清理都不重写 JSON 字段、实体名单或证据集合的原始预测内容。

## 单体评分与投票如何保持一致

Audit 的同一 `parse_audit_answer` 同时服务于 `task_evidence_audit.build_answer_evaluator`、`poolact.aggregate_results` 和 `aggregation_diagnostics`。允许裸 JSON 对象、尾分号、完整的 JSON/无语言 fence。保留原 scorer 对 closing fence 后说明文字的接受，但明确拒绝第二个 fence、另一个 JSON 对象/独立数组或新的协议指令。未闭合 fence、非 JSON 语言 fence、前导引用/说明中嵌入 JSON 不接受。普通说明中的 evidence 引用 `[45]` 或非指令 `the answer:` 提及不会自行构成第二份提交。

包装一致还不足以保证字段一致，因此一并修正两处字段差异：

1. 标签采用字符串字面值，停止把 `entailed`、`neutral`、大小写或标点变体转成正确的标准标签。非字符串值只能成为无效标签键，不能变成合法标签。原个体标签准确率的严格定义保留。
2. 证据集合完整沿用原个体指标的 `set(int(v) for v in value)` 语义：可转换的迭代值按原规则解释；任一转换异常导致整个集合为空。投票不再使用自己的“仅接受 list、保留坏项字符串”分支。原 EA 与 LA 独立、原整数转换语义均保留，未借本次修复重新定义指标。

初次全量字段核查的 1,872 个 Audit 成员没有真实 17 个假设上的标签 alias 命中，也没有 evidence coercion 差异；两个异常标签位于非法 hypothesis key。正式回放仍重新处理全部成员和池，不据此跳过。精确记录由 rescore 的 `audit_field_semantics.json` 给出。

Search 保留原个体名字提取规则（JSON 数组、逗号/分号/换行、列表符号，以及文本片段 1–5 词限制），将投票键改为同一函数返回的名字集合。投票不再额外接收个体 scorer 已滤掉的长解释文本，也不擅自改写 JSON 数组元素里的编号。票数、首成员 tie-break、空键计票和返回原获胜成员答案的规则不变。

HPO 的真实评估、可见性、预算及“已接受但不可评分的单份配置”触发的 legacy visible-best fallback 不变。被新协议拒绝的多份非空答案不能通过该 fallback 自动变成一份有效提交；新运行需要请求重新回答，旧轨迹没有该反事实响应时必须如实标记。

## 验证和回放边界

- 最终 [parser_full_check_final.log](parser_full_check_final.log)：`scripts/check.sh` 通过，712 项单元/集成测试、33 项因缺本地可选数据跳过；compile、shell 检查及 ExpGym、naive/cached/poolact fake 端到端均通过。
- 新 `tests/test_answer_protocol_v2.py` 覆盖实际标签错误、整个提交加粗、所有格、引用/动作/多答负例、尾述包装、Search 个体与投票集合一致、Audit 包装与字段消费者一致，以及自然/forced-final 运行入口。
- 独立核验脚本 [parser_independent_cases.py](parser_independent_cases.py) 与 [PARSER_INDEPENDENT_CASES.json](PARSER_INDEPENDENT_CASES.json) 覆盖 23 个已发现案例的来源哈希、payload 字面不变和 JSON 内容不变，并以人工构造的单假设 fixture 测消费者一致性，不读取 benchmark gold 选择规则。
- [audit_wrapper_rejections.py](audit_wrapper_rejections.py) 全读 Audit 重评分输入，检查原 scorer 能解析而新 wrapper 拒绝的条目；该检查的输入 SHA 与正式全量回放 SHA 必须一致，草稿检查不能冒充冻结版检查。

正式全量回放须扫描全部相关 N1、N4 成员、所有池和 sweep；其中所有非终止 assistant turn 也须检查新旧终答识别差异。对已有终答的重评分是 **existing-trace rescoring**，不是新协议的反事实运行。若新 parser 会使历史中间响应提前结束，或者图修复改变信息共享，应单独标出并由统一版本对照补跑处理，不能把离线评分冒充重跑轨迹。

本实现阶段未调用任何模型 API，未改历史轨迹或旧评分，未提交或推送仓库。代码冻结后的正式补跑、重新聚合、报告采用和发布由主任务统一完成。
