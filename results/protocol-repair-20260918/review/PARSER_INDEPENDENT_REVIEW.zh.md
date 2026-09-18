# 终答与 Audit 投票规则独立核验

本轮检查最终通过 **325 / 325** 项。详见 `PARSER_INDEPENDENT_CASES.json`；其中记录了 6 个受检实现文件的 SHA-256，及 23 个历史真实案例的来源 SHA-256。此检查没有模型调用，没有根据 benchmark 标准答案选择或改写任何终答内容。

覆盖范围：

- 终答标签：普通、粗体、下划线、冒号内外、空标签连续包装、含 `final answer:` 的说明前缀，以及 payload 自身的 Markdown 保持原样。
- 非指令性的 `Answer:` 前后提及不影响唯一正式标签；`**Answer: Ada**` 保留历史 payload `Ada**`；粗体后的 possessive 不会误打开引用区块。所有尾述原样保留，不根据分数清洗答案。
- 保守边界：拒绝引用、示例、未闭合 reasoning、已有提交后再提交、工具指令；带原始文本答案的 native 与 text 协议分别检查。
- Audit 接受规则：完整对象、分号、JSON 或无语言围栏、围栏后的正常说明及证据编号引用均接受；未闭合围栏、其他语言、第二对象或数组、第二围栏及追加协议指令均拒绝。
- 公共消费者一致性：以自造的单假设 fixture 同时验证真实 task evaluator、`aggregate_results` 及 aggregation diagnostics 的接受和拒绝行为。
- 字段一致性：20 种 label/evidence 变体分别核验 scorer、投票结果、聚合分数及 diagnostics。label 保留字符串字面值，投票不得把大小写、空白或别名自动改成正确标签；非字符串作为无效标签。evidence 保留历史单体评分的 iterable `int()` 集合语义，任一元素失败则整集合为空；bool、float、string、dict 等历史兼容行为没有被暗改。另验证错误别名取得多数时，仍作为错误标签评分。
- 通用 JSON parser 仍保持严格的 whole-document、有限数值契约；Audit payload 的历史 `json.loads` 非有限值与重复键行为保持不变。字段统一对齐历史单体评分语义，未根据标准答案修复内容。
- 23 个已确认历史实例全部核验源文件哈希、修复提取后的 payload 字面相等、JSON 字段和值不变。这里只把它们用作真实回归案例，不能替代本轮另外进行的全量重评分。

独立审阅过程中发现并反馈的两处边界遗漏均已修复：下划线标签被 `\b` 错拒，以及围栏后的独立多行数组未被识别为第二提交。扩展回归已纳入这两类。

复算命令（从 workspace 根目录运行）：

```bash
python3 protocol_repair_20260918/review/parser_independent_cases.py \
  --repo LLM_ExpGym-protocol-repair-20260918 \
  --audit-parser expgym.tool_protocol:parse_audit_answer \
  --output protocol_repair_20260918/review/PARSER_INDEPENDENT_CASES.json
```

另有 `audit_wrapper_rejections.py` 对当前全量重评分 overlay 做独立语法审阅，输出 `AUDIT_WRAPPER_REJECTION_REVIEW.json`。输入共 2,574 个 Audit 成员和 468 个聚合答案；检查历史可接受而新 parser 拒绝的所有类型，不以标准答案挑选规则。脚本会记录输入 SHA，并要求 parser 源码与全量重评分 CHECKS 中的源码版本一致；若版本尚未同步，明确标为 REVIEW，不可冒充最终复核。

最终全量重评分完成后已重新扫描并通过：old_answer 历史/当前均接受 2,925 条，new_scoring_input 历史/当前均接受 2,966 条；没有新增包装拒绝，成员分数中无 LA/EA 下降。`AUDIT_WRAPPER_REJECTION_REVIEW.json` 已为 PASS，输入与冻结代码 `0e6c51b6d86f42437038518c2fc8adc510901c0b` 的 SHA 一致。另由 `final_rescore_independent.py` 全量复算 2,574 份终答提取、旧/新 LA/EA 和 468 个池的旧/新投票，均无不一致；完整范围及计数区别见 `FINAL_RESCORE_REVIEW.zh.md`。

本脚本的真实来源路径取自历史诊断索引，需要本地留档存在；随仓库发布的独立语法回归测试应使用去除敏感信息后的固定 fixtures。当前 JSON 是本地独立核验证据，不应在不检查路径和内容的情况下直接公开。
