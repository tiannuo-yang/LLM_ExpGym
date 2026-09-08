# Audit 独立重算必须复刻的实际语义

本文件只记录冻结仓库现有规则，不调用正式 evaluator、aggregate 函数、汇总器或 LLM API。独立实现须与这些规则比较，不能用看起来更合理的清洗规则替代。主要依据为 `LLM_ExpGym/expgym/task_evidence_audit.py:311` 的 `build_answer_evaluator`，以及 `LLM_ExpGym/expgym/poolact.py:159`、`:179`、`:192`、`:204` 的聚合实现。

## 1. Gold 的选择和分母

- 数据文件 `data/contract-nli/test_segments.json` 中，row_index 指向 `documents` 原始数组位置，不是 doc_id，也不先排序。正式实现还接受 Python 式负下标，超范围抛 IndexError。
- 仅使用对应文档的 `annotation_sets[0]["annotations"]`，不合并其他 annotation_sets。
- `cc-large` 使用顶层 `labels` 的全部 hypothesis IDs；gold 是该文档 annotations 与这些 IDs 的交集。其他 split 有显式子集；未知 split 名在现实现中也因空列表而退回全部 labels。
- 分母为选出的 gold 数量，不是预测条目数量，也不是预测和 gold 的并集。当前目标 rows 0:13 均为 17，因此总共 221。
- gold `spans` 取 `set(int(s) for s in gold_entry.get("spans", []))`。这一转换不包异常；数据损坏不可静默当作空 gold。

## 2. 单 agent / ExpGym evaluator：答案解析

正式输入是 `prediction: str`。原逻辑依次执行：

```python
try:
    data = json.loads(prediction)
except json.JSONDecodeError:
    cleaned = prediction.strip().rstrip(";").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"label_acc": 0.0, "evidence_acc": 0.0,
                "verification_eff": None}
if not isinstance(data, dict):
    return {"label_acc": 0.0, "evidence_acc": 0.0,
            "verification_eff": None}
```

需要保留的边界：

- 只在首次 JSONDecodeError 后清洗；不是扫描任意正文中的 JSON，也不剥除 `Answer:` 前缀。从 trace/messages 提取最终答案属于上游另一个步骤。
- 清洗只移除最末尾连续分号及两端空白，随后处理开头为三个反引号的块。没有一般性 markdown 清洗，也没有先清洗反引号后再清洗内部尾部分号。围栏使用上述 split/rsplit 精确行为，不必要求 JSON 语言标记，也不验证围栏成对。
- Python 默认 `json.loads` 的重复 key 采用最后一个值；包括重复 hypothesis ID 和重复 `label` / `evidence_ids`。不能将重复 ID 当成多个 hypothesis，不能采用 first-wins，也不能在独立评分中额外拒绝重复 key。
- Python 默认内层 JSON 解析允许 NaN/Infinity；它们后续如何被处理取决于字段转换。不要把外层原始 artifact 的严格 JSON 审计规则套到答案字符串的内层解析。
- 顶层数组、字符串、数字、bool、null 即使 JSON 合法也返回三个空指标。直接向 evaluator 传 dict/None 不是这个“合法 JSON 顶层类型”分支：`json.loads` 会抛 TypeError，原代码不捕获这个 TypeError。独立实现若遇到这种异常类型，应显式记录边界，而非悄悄补零。

## 3. 单 agent evaluator：缺失、标签与证据

逐一遍历 gold hypothesis。预测没有该 key，或该 key 的值不是 dict，则整项跳过：LA 和 EA 都计错，但分母仍包含这一项。预测中额外/未知 hypothesis ID 完全不参与指标，也没有额外惩罚。

当 hypothesis 的预测值是 dict 时：

```python
pred_label = entry.get("label")
pred_evidence = entry.get("evidence_ids", [])
label_ok = pred_label == gold_choice
try:
    evidence_set = set(int(v) for v in pred_evidence)
except Exception:
    evidence_set = set()
evidence_ok = evidence_set == gold_spans
```

标签规则：只做精确相等，不 strip、不忽略大小写、不映射别名。`NotMentioned`、`Entailment`、`Contradiction` 才与当前 gold 的对应字符串相等；`neutral`、`not mentioned`、`entailed`、`E/N/C` 不会由单 agent evaluator 修复。

证据规则及不寻常后果：

- `evidence_ids` 缺失时默认空列表；`null`、单个数字、无法迭代或任何元素无法 `int()` 时，整个集合都变为空，而不是只丢掉坏元素。
- 不要求证据是 list。字符串 `"12"` 被逐字符转换为 `{1,2}`；dict 被迭代 key。因此不能额外增加 list 类型检查来“改善”独立评分。
- `int()` 原语义包括数字字符串、bool、浮点截断（如 `1.9 → 1`）；重复 ID 和顺序不影响集合。没有显式非负、越界、有效 span ID 或一基/零基修复。
- 例如 `[1,"oops"]` 整组退为空；如果 gold 空，则 EA 仍可计正确。gold 非空则计错。NaN/Infinity 转 int 引发的异常也在这一级被捕获为空。
- 缺失整个 hypothesis 与存在 `hypothesis: {}` 不等价：后者虽无正确 label，但默认空证据可在 gold 空时获得 EA。
- EA 只取 `evidence_ok`，与 `label_ok` 无关；不是联合正确率。LA 与 EA 分别对全部 gold hypothesis 求平均。

## 4. verification_eff 的重建

先从全部 tool_records 中建立提交索引；每条记录预期是三元组 `(tool_name, argument, ignored_result)`。只处理名称精确等于 `human_feedback` 的记录。

- 对 argument 执行 `json.loads`，只捕获 JSONDecodeError；参数不是合适的 JSON 字符串导致的 TypeError 并不会被捕获。结构错误的 tool_record 解包异常也不会被捕获。
- 若解析结果是非空 list，且第一个元素为 dict，只使用第一个元素；其余元素忽略。否则必须是 dict。
- `nda_id` 必须为 str，`evidence_ids` 必须为 list；这一处比最终预测的证据类型检查严格。
- 提交证据转 `set(int(v) for v in evidence_ids)`；任何转换异常使整次提交被忽略，**不是**保存为空提交。
- 同一个 nda_id 可有多次提交。最后答案的证据集合与其中任意一次提交相同即可。
- 完全忽略第三个工具返回值，也不核验返回是否成功、是否预算内展示、实际反馈文本或成本。若上游 tool_records 包含 withheld/错误返回的调用，符合上述输入条件的提交仍会参与 verification_eff；独立重算不能自行按 `visible_to_model` 过滤。

仅对 `label_ok and evidence_ok` 的 hypothesis 累计 fully_correct；其中有匹配提交的累计 verified_correct。`verification_eff = verified_correct / fully_correct`，分母为 0 时是 None。它不是已验证占全部 hypothesis 比例，也不是工具调用准确率。gold 分母为空时直接返回空指标。

ExpGym v2 没有旧式 tool_records，重建 argument 时应保留原语义：通常把结构化 arguments JSON 编码回字符串；仅 `{"raw": ..., "encoding": "text"}` 这种文本包装还原为 raw 字符串。`structured_result` / `withheld_result` 不影响此 evaluator 的提交匹配。

## 5. PoolAct aggregate：单独的答案解析规则

`individual_answers = [result.get("answer") or "" for result in results]`，保留原始 results 顺序。空/假值先变空字符串；不首先统一转 str。

每个 answer 是 str 时仅尝试一次 `json.loads`，捕获 JSONDecodeError 或 TypeError 后作为空 dict。若 answer 已为非空 dict，则直接使用；其他非 dict 解析结果一律为空 dict。

**这里不执行单 agent evaluator 的末尾分号/markdown 围栏清洗，也不执行 Answer 提取。** 因此单 agent 可能凭宽松清洗获得高分，但同一原始 answer 字符串在 aggregate 中可能完全没有票。独立聚合不能先调用/复用单 agent 的 cleaned prediction，否则与真实规则不同。

候选 hypothesis IDs 是所有成功解析 dict 的 key 的并集，并按 `sorted` 遍历；不预先限定 gold IDs。额外 IDs 可出现在 aggregate 输出中，但最终 evaluator 会忽略它们。对某个 hypothesis，仅保留该 key 的值为 dict 的 agent 条目；缺失或非 dict 条目不投票，也不补默认 NotMentioned。一个有效 agent 的单票也能决定该 hypothesis，没有法定票数要求。

## 6. PoolAct label canonicalization 与平票

对每个有效 entry 的 `entry.get("label")`：

```python
raw = re.sub(r"[^a-z]", "", str(value or "").lower())
mapping = {
    "entailment": "Entailment", "entailed": "Entailment",
    "contradiction": "Contradiction", "contradicted": "Contradiction",
    "notmentioned": "NotMentioned", "neutral": "NotMentioned",
}
label = mapping.get(raw, str(value or "").strip())
```

- 所有非 ASCII 小写字母字符被移除后再查上述六个别名；因此空白、下划线、连字符和标点可被容忍。
- 没有 E/N/C 或 yes/no 等额外映射。未识别值保留 `str(value or "").strip()`；不是丢票，也不是强制 NotMentioned。
- 缺失 label、None、False、0 等假值变为空字符串。这种空字符串仍参与投票。`if not labels` 仅表示无有效 entry，不表示标签字符串为空就忽略。
- 原码没有要求 label 类型必须为 str，先执行上述 `str(...)` 处理；独立实现不能悄悄跳过非字符串 label。
- `Counter(labels).most_common(1)[0][0]` 决定 winning_label。平票取最早出现的候选标签，即 results 原始顺序中首个贡献该标签的 agent；不按标签字典序、不根据 agent 性能、不优先有效标签或非空标签。
- 原 runner 的 `run_agents_parallel` 按 agent_id 0..N-1 返回结果，所以正常工件表现为较早 agent 优先。独立重算应保留 result 内 `agent_results` 原始顺序；不要使用完成时间或随机 dict 顺序。

## 7. PoolAct evidence canonicalization 与二级投票

**仅在 winning_label 的 entries 里面**对完整证据集合投票；不是所有 agent 一起投，不是对每个 span 逐位投，也不是先做 `(label,evidence)` 联合票。

```python
if not isinstance(value, list):
    canonical = ()
else:
    normalized = set()
    for item in value:
        try:
            normalized.add(int(item))
        except (TypeError, ValueError):
            normalized.add(str(item))
    canonical = tuple(sorted(normalized,
                     key=lambda item: (str(type(item)), str(item))))
```

- 缺失/非 list 证据在投票时直接是空 tuple；这与单 agent evaluator 对字符串/dict 的迭代规则不同。
- 单个坏元素被转成字符串保留，而不是使整组为空；同组其他可转换整数保留。OverflowError 没有被这一级捕获，例如 `int(float('inf'))` 可使 aggregate 失败，不能额外改成空证据。
- 去重后按 `(类型字符串, 值字符串)` 排序；整数 `[2,10]` 的 canonical 次序为 `(10,2)`，不是数值升序。虽然 EA 集合比较不受顺序影响，精确 aggregate.answer 比较需要复刻。
- evidence 使用 `Counter(evidence).most_common(1)[0][0]`，平票同样取 winning_label 子序列中最早出现的整组集合。
- `NotMentioned` 不会强制清空证据；它可以赢得非空甚至含非法字符串的证据集合。
- voted entry 为 `{"label": winning_label, "evidence_ids": list(winning_evidence)}`。若最终列表含无法转 int 的字符串，后续正式 evaluator 会按第 3 节将整组 evidence 当作空集，可能在空 gold 上获得 EA。

## 8. PoolAct 最终 aggregate 输出与评分

- `answer = json.dumps(voted, sort_keys=True)`，使用默认空格分隔和 ensure_ascii=True。精确比较字符串时不要另改 separators/Unicode 转义；语义比较可独立注明。
- `method` 为 `per_hypothesis_majority_vote`。`individual_answers` 和 `individual_perfs` 保持输入顺序；individual_perfs 是输入 agent 的原始 answer_perf，不参与投票加权。
- 调用 evaluator 时传 `answer, []`，**不汇总 agent 的 tool_records**。因此 aggregate verification_eff 在存在 fully_correct 时恒为 0.0，完全正确项为 0 时为 None；不能把 agent 的验证情况混入 aggregate VE。
- evaluator 返回 metrics dict 时，aggregate answer_perf 取 `label_acc` 的 float；EA 单独保留在 answer_metrics 内。
- `_evaluate_aggregate` 对 evaluator(answer, []) 的 TypeError 会尝试 evaluator(answer)。当前目标 evaluator 需要第二参数，异常数据不要通过独立实现额外吞掉，标为运行/兼容性问题即可。

## 9. 已完成原始样本的 shape 确认（非全量完成声明）

检查时已存在 50 个 full_v3 Audit PoolAct result，全部 agent_results 按 agent_id 升序；200 个 agent.answer 全为字符串、均能直接 JSON 解析为 dict，3400 个 hypothesis entry 全为 dict、evidence_ids 全为 list。标签为标准三种：NotMentioned 1213、Entailment 1776、Contradiction 411。这只是动态运行中的一次原始 shape 快照，不能用来推断尚未完成结果的类型或最终总体分布。

代表文件：`/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/full_v3/poolact/evidence_audit/0/cost_free/naive/agents/agent_0.json`；SHA256 `f57d00bdb795f64a9ab1799012f2236491e7f445c49f62f96e7efeb7febf53b8`。

独立实现的关键防偏差原则：原始 outer artifact 校验可以严格；评分和投票必须分别忠实复刻各自不同的内层解析与规范化。对于看起来怪异的空证据得分、label 别名修复、平票优先等，不在复核阶段悄悄修正协议。
