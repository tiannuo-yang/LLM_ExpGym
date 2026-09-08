# full textual ReAct 协议诊断

完成时间：2026-09-07T11:52:28.704143+00:00。342 个 jobs、2355 条 agent traces。统计仅使用已完成结果。

版本2修正：旧字段cap_removed_textual_action_responses仅代表解析器候选，不能解释为可执行Action被截掉。此版重命名并加入工具名/JSON检查及原文证据；旧报告保留供追溯。

| 路径/场景 | traces | missing_action | forced final | 原始native响应 | trace native消息 |
|---|---:|---:|---:|---:|---:|
| expgym | 303 | 238 | 262 | 126 | 124 |
| expgym/tuning | 81 | 52 | 61 | 22 | 22 |
| expgym/restricted_search | 105 | 82 | 96 | 38 | 38 |
| expgym/evidence_audit | 117 | 104 | 105 | 66 | 64 |
| poolact | 2052 | 1591 | 1720 | 841 | 812 |
| poolact/tuning | 324 | 179 | 209 | 76 | 75 |
| poolact/restricted_search | 1260 | 993 | 1086 | 492 | 492 |
| poolact/evidence_audit | 468 | 419 | 425 | 273 | 245 |

原始 HTTP attempts=9068；state={'success': 9068}；finish_reason={'stop': 9064, 'length': 4}。thinking={'False': 9068}，reasoning_tokens={'0': 9068}；结构化 tool_calls 非空响应=0。

native标签共出现在 967 个响应 / 1028 个call开头；962/966 条含native标签trace在最后一个常规响应出现native标签后终止为missing_action，占全部missing_action的 962/1829。原始响应与保存trace在应用现有截断规则后完全一致：2355/2355。

常规响应超过8000字符：71；截断前存在、截断后消失的Action解析候选：22，其中仅通过预期工具名+JSON语法检查的候选：18。解析器会匹配长Thought中引用的Action:，因此这些计数不证明存在可执行动作，也不能据此归因于cap。即使工具名和JSON有效，仍未验证参数schema或实际执行。此cap是仓库既有行为，forced final不受该8000字符cap约束。

thinking参数与返回的reasoning字段需分开报告：170 个响应的reasoning_content非空，共 631606 字符，虽usage.reasoning_tokens的取值为 {'0': 9068}。因此只能确认请求了thinking=false及服务报告的token字段，不能据此证明模型完全没有产生reasoning channel。客户端仅保存content到多轮trace history，完整reasoning_content仍可在原始dump按request_id查验。

终止原因（原字段名是 termination_reason）：

```json
{
  "expgym": {
    "missing_action": 238,
    "natural_answer": 41,
    "time_budget_exceeded": 24
  },
  "poolact": {
    "missing_action": 1591,
    "natural_answer": 332,
    "time_budget_exceeded": 124,
    "unknown_tool": 5
  }
}
```

ExpGym answer_source：`{"forced_model_answer": 256, "natural_model_answer": 41, "best_evaluated_fallback": 6}`。PoolAct legacy agent结果未序列化termination_reason/answer_source；此处termination原因从保存的强制回答提示推导，不能将推导字段当原始字段。

promotion匹配使用保存的client_id与逐响应文本；原dumpcontext中的pilot路径和run_id作为证据保留，不影响full中的对应关系。promotion map及文件hash由独立dump审计确认。本脚本只应扫描目标stage的dump目录；若同时扫描pilot/full副本，重复request_id会拒绝。raw总体计数涵盖该目录全部attempt，trace分组仅统计保存client_id关联的attempt。

## 解释与论文语义

本次请求使用论文textual ReAct：Action: tool_name JSON。K3原生XTML工具通道 `<|open|>tools<|sep|><|open|>call tool=...` 不属于该语法。客户端未发送结构化tools，也未转换XTML；此类工具意图不会作为Action执行，随后按仓库协议强制最终回答。应同时报告协议遵循失败率、实际tool调用、强制回答率及得分，不能将其仅解释为任务知识能力不足，也不能用score复算通过替代交互协议成功。

missing_action与有效最终得分可同时成立：强制回答后原中断标记仍保留；Tuning还可能使用best_evaluated_fallback。HTTP成功、结果完整性、动作格式遵循和语义正确率是不同维度。

在严格主实验中保留统一textual ReAct语义并披露这些失败。若另做K3 native适配，需将其列为独立协议敏感性实验，并对ExpGym及PoolAct各策略应用相同适配，重新保留manifest和dump；不要把适配后的结果混入原配置。smoke的4-step/3-evaluation/N=2不能用于推断论文30-step/N=4失败率。

代码依据：LLM_ExpGym/expgym/react_loop.py:304（8000字符cap）、:312（Action/Answer解析）、:332（missing_action）、:453（forced final）、:519（tuning fallback）、:737（字面Action）；expgym/llm_clients.py:358（仅content）、:405（无tools）；expgym/trace_v2.py:202（原因映射）。原始标签证据及request/client/trace对应关系见同名JSON。


### 截断候选逐例

request_id `d9fb6af772f640d5a4fd0289f01f9aa9`；原始 10329 字符，finish_reason=stop，首个Action: offset=8701。提取工具 `human_feedback`；payload JSON有效=False。

```text
A document "nda-11"?? The example in the prompt used nda_id "nda-11". The nda_id parameter — is it the hypothesis ID or the document ID? The example: Action: human_feedback {"nda_id": "nda-11", "evidence_ids": [3, 7]}. And hypotheses are named nda-10, nda-4, etc. So "nda-11" in the example is a hypothesis ID (No reverse engineering). So I passed nda-16 = "Return of confidential information". Evidence [11]. Feedback: Contains Irrelevant Evidences.

Hmm interesting — the example used evidence [3,7] for nda-11 (no reverse engineering) which is clearly wrong/NotMentioned, just an example.

So for nda-16, gold evidence doesn't include [11]?? That'
```

提取payload：

```text
{"nda_id": "nda-11", "evidence_ids": [3, 7]}. And hypotheses are named nda-10, nda-4, etc. So "nda-11" in the example is a hypothesis ID (No reverse engineering). So I passed nda-16 = "Return of confidential information". Evidence [11]. Feedback: Contains Irrelevant Evidences.
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `e51ec3db69c64e098ef3388c928ef227`；原始 8608 字符，finish_reason=stop，首个Action: offset=8543。提取工具 `human_feedback`；payload JSON有效=True。

```text
d, evidence_ids}. Let me verify nda-16 with [26], nda-17 with [25], nda-1 with [23], nda-18 with [27], nda-15 with [26].

I'll start with a few calls.Action: human_feedback {"nda_id": "nda-16", "evidence_ids": [26]}
```

提取payload：

```text
{"nda_id": "nda-16", "evidence_ids": [26]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `ff5904821dd34269839d33090cf1b02e`；原始 8761 字符，finish_reason=stop，首个Action: offset=8691。提取工具 `human_feedback`；payload JSON有效=True。

```text
 nda-8, nda-20, nda-10, nda-11, nda-18 (the NotMentioned ones I could verify by submitting empty? Probably not useful). Let me focus on nda-7 first.

Action: human_feedback {"nda_id": "nda-7", "evidence_ids": [8, 9, 17]}
```

提取payload：

```text
{"nda_id": "nda-7", "evidence_ids": [8, 9, 17]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `4b00b0cbd3b8464693d05d7bf6fcb1dd`；原始 8932 字符，finish_reason=stop，首个Action: offset=8863。提取工具 `human_feedback`；payload JSON有效=True。

```text


Let me verify a few with human feedback. I should verify the trickier ones: nda-16, nda-17, nda-13, nda-10.

Let me start with human feedback calls.Action: human_feedback {"nda_id": "nda-16", "evidence_ids": [81, 82]}
```

提取payload：

```text
{"nda_id": "nda-16", "evidence_ids": [81, 82]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `54991b53c67b477495c626fc7b5480f3`；原始 8621 字符，finish_reason=stop，首个Action: offset=8553。提取工具 `human_feedback`；payload JSON有效=True。

```text
 Agent 2 is verifying nda-16 with [55, 56, 57, 58]. Let me verify a different one — perhaps nda-7 (sharing with third-parties) since it's ambiguous.

Action: human_feedback {"nda_id": "nda-7", "evidence_ids": [17, 30]}
```

提取payload：

```text
{"nda_id": "nda-7", "evidence_ids": [17, 30]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `4c27190a50db413aae0154aed3491deb`；原始 12470 字符，finish_reason=stop，首个Action: offset=12385。提取工具 `human_feedback`；payload JSON有效=True。

```text
7 (third parties with consent), nda-20 (retention), nda-1 (explicit identification), nda-17 (permissible copy).

Let me call human_feedback for these.Action: human_feedback {"nda_id": "nda-16", "evidence_ids": [53, 54, 55, 56, 57, 58]}
```

提取payload：

```text
{"nda_id": "nda-16", "evidence_ids": [53, 54, 55, 56, 57, 58]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `df90cf6686354f3c8cba680a121f09c7`；原始 29814 字符，finish_reason=stop，首个Action: offset=28766。提取工具 `human_feedback`；payload JSON有效=False。

```text
segment_ids]}}. The example shows {"nda_id": "nda-11", "evidence_ids": [3, 7]} — interesting, nda-11 there is the document id? Wait, the example says Action: human_feedback {"nda_id": "nda-11", "evidence_ids": [3, 7]}. And the document is nda-11. Hmm, but the hypotheses are also labeled nda-XX. The example uses nda-11 which is both the doc id and a hypothesis id. Confusing. I think "nda_id" in the tool refers to the hypothesis id (like nda-7). Let me use hypothesis ids.

Let me start verifying. I'll call human_feedback for nda-7 first with [17, 30].

Actually, let me batch my thinking and be strategic. I have 17 hypotheses; I'm confident abou
```

提取payload：

```text
{"nda_id": "nda-11", "evidence_ids": [3, 7]}. And the document is nda-11. Hmm, but the hypotheses are also labeled nda-XX. The example uses nda-11 which is both the doc id and a hypothesis id. Confusing. I think "nda_id" in the tool refers to the hypothesis id (like nda-7). Let me use hypothesis ids.
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `1fc7a45bdabd4443abeabd8449325053`；原始 8775 字符，finish_reason=stop，首个Action: offset=8706。提取工具 `human_feedback`；payload JSON有效=True。

```text
estroy exists. But strictly, the trigger differs. Let me use human feedback to check.

Let me start with human feedback for nda-16 with evidence [39].Action: human_feedback {"nda_id": "nda-16", "evidence_ids": [39, 40]}
```

提取payload：

```text
{"nda_id": "nda-16", "evidence_ids": [39, 40]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `32b82d5801c24feb83f054d2de0a47e2`；原始 9071 字符，finish_reason=stop，首个Action: offset=9006。提取工具 `human_feedback`；payload JSON有效=True。

```text
ing) with segment 16
- nda-18 (no solicitation) with segment 13
- nda-7 with segment 3
- nda-5 with segment 6

Let me start with a few feedback calls.Action: human_feedback {"nda_id": "nda-15", "evidence_ids": [16]}
```

提取payload：

```text
{"nda_id": "nda-15", "evidence_ids": [16]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `2206e9965d414c97aa5ab37a73a8c1c4`；原始 8834 字符，finish_reason=stop，首个Action: offset=8770。提取工具 `human_feedback`；payload JSON有效=True。

```text
 evidence for a hypothesis - it takes nda_id and evidence_ids. Let me call it for the uncertain ones.

First turn: human_feedback for nda-1 with [12].Action: human_feedback {"nda_id": "nda-1", "evidence_ids": [12]}
```

提取payload：

```text
{"nda_id": "nda-1", "evidence_ids": [12]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `d493b99b0683464b980c6ad42c5224dc`；原始 13118 字符，finish_reason=stop，首个Action: offset=13049。提取工具 `human_feedback`；payload JSON有效=True。

```text
a-3 ([12]), nda-5 ([24]), nda-7 ([25]).

The tool signature: human_feedback {"nda_id": "...", "evidence_ids": [...]}. Let me call it for nda-15 first.Action: human_feedback {"nda_id": "nda-15", "evidence_ids": [29, 35]}
```

提取payload：

```text
{"nda_id": "nda-15", "evidence_ids": [29, 35]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `e2db5e604a974b82a0604a7778c8e7d4`；原始 12528 字符，finish_reason=stop，首个Action: offset=12464。提取工具 `human_feedback`；payload JSON有效=True。

```text
ice on compelled disclosure) with evidence [11], and nda-1 with [7]. I can only call one action per turn. Let me prioritize the most uncertain: nda-8.Action: human_feedback {"nda_id": "nda-8", "evidence_ids": [11]}
```

提取payload：

```text
{"nda_id": "nda-8", "evidence_ids": [11]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `25b63a923ad94c4a8560b8f65732d78f`；原始 10361 字符，finish_reason=stop，首个Action: offset=10298。提取工具 `human_feedback`；payload JSON有效=True。

```text
by verifying nda-3 and nda-1 with evidence [7].

Let me call human_feedback for a batch of these. I'll make multiple calls across turns. Let me start.Action: human_feedback {"nda_id": "nda-3", "evidence_ids": [7]}
```

提取payload：

```text
{"nda_id": "nda-3", "evidence_ids": [7]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `ed50b2af9f724b06a43b2dce7cd1dbf6`；原始 8905 字符，finish_reason=stop，首个Action: offset=8840。提取工具 `human_feedback`；payload JSON有效=True。

```text
ion vs NotMentioned), nda-19, nda-8, nda-1, nda-2.

Let me start with the most uncertain ones. I'll call human_feedback for nda-20 with evidence [48].Action: human_feedback {"nda_id": "nda-20", "evidence_ids": [48]}
```

提取payload：

```text
{"nda_id": "nda-20", "evidence_ids": [48]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `616687ae12db4f89b90f92b1c6035a08`；原始 9584 字符，finish_reason=stop，首个Action: offset=9519。提取工具 `human_feedback`；payload JSON有效=True。

```text
ed
- nda-13: NotMentioned
- nda-5: NotMentioned
- nda-4: Entailment [25]

Let me use human_feedback on the uncertain ones. I'll do them one at a time.Action: human_feedback {"nda_id": "nda-17", "evidence_ids": [34]}
```

提取payload：

```text
{"nda_id": "nda-17", "evidence_ids": [34]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `a663c51a07fc400890a41967cbab22e3`；原始 13405 字符，finish_reason=stop，首个Action: offset=12341。提取工具 `human_feedback`；payload JSON有效=False。

```text
nes. The tool input takes nda_id and evidence_ids. Let me verify the tricky ones: nda-17, nda-16, nda-3, nda-10, nda-1.

Actually, the example shows: Action: human_feedback {"nda_id": "nda-11", "evidence_ids": [3, 7]}. So I can call it to verify evidence for a hypothesis. Let me start with nda-17.

Let me plan my labels:
- nda-11: NotMentioned, []
- nda-16: Entailment, [42]
- nda-15: Entailment, [49]
- nda-10: Entailment, [21, 34] (maybe [22] too)
- nda-2: Contradiction, [23]
- nda-1: NotMentioned, []
- nda-19: Entailment, [62]
- nda-12: Entailment, [28]
- nda-20: Entailment, [43, 44, 45]
- nda-3: Entailment, [19, 23] (or just [23])
- nda-18:
```

提取payload：

```text
{"nda_id": "nda-11", "evidence_ids": [3, 7]}. So I can call it to verify evidence for a hypothesis. Let me start with nda-17.
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `16515705ed994909831f9193591eab25`；原始 9954 字符，finish_reason=stop，首个Action: offset=9890。提取工具 `human_feedback`；payload JSON有效=True。

```text
) with evidence [17], [8], [9].
And nda-20 with no evidence (NotMentioned).
And nda-8 with no evidence or [40].

Let me call human_feedback for these.Action: human_feedback {"nda_id": "nda-7", "evidence_ids": [17]}
```

提取payload：

```text
{"nda_id": "nda-7", "evidence_ids": [17]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `78b199fdc0374b8487d137da8c67fa35`；原始 9597 字符，finish_reason=stop，首个Action: offset=9532。提取工具 `human_feedback`；payload JSON有效=True。

```text
feedback multiple times. Let me verify the tricky ones: nda-16, nda-7, nda-8.

Let me make my first human_feedback call for nda-16 with evidence [33].Action: human_feedback {"nda_id": "nda-16", "evidence_ids": [33]}
```

提取payload：

```text
{"nda_id": "nda-16", "evidence_ids": [33]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `a876441349284408926545d6fb106203`；原始 12080 字符，finish_reason=stop，首个Action: offset=12030。提取工具 `search`；payload JSON有效=True。

```text
ching "glass blower" with different phrasings to find other glass blowers: "glass blowing", "glassblower", "blows glass".

Let me try "glassblower".

Action: search {"query": "glassblower occupation"}
```

提取payload：

```text
{"query": "glassblower occupation"}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `acdf7057d7484dfeb18a336e1ca8fb3b`；原始 37186 字符，finish_reason=length，首个Action: offset=15489。提取工具 `search`；payload JSON有效=False。

```text
 format but the tool_choice=none means the harness will handle it? The instruction is explicit: "You MUST NOT call any tools in the next message." So Action: search would violate this. The only compliant output is "Answer: ...".

Given that, I'll provide the answer that the glass blower is Chad Huss and... no, the answer should be names of the sibling(s).

Let me make an educated guess: The question generator likely created a family where Chad Huss has children. The names in this wiki universe... I can't guess specific names.

Alternatively, maybe the answer is "Jocelyn Soliz, Leticia Landeros" under a misreading where "son" = Chad himself? L
```

提取payload：

```text
would violate this. The only compliant output is "Answer: ...".
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `a7bec99c747442818a82fd2358805a53`；原始 10244 字符，finish_reason=stop，首个Action: offset=9938。提取工具 `evaluate_config`；payload JSON有效=True。

```text
3x3.

Probe 1 with this candidate directly — if score is decent, selector interpretation confirmed and we can refine. This wastes no turn on defaults.Action: evaluate_config {"edge_0": 1, "edge_1": 2, "edge_2": 7, "edge_3": 8, "edge_4": 12, "edge_5": 16, "edge_6": 18, "edge_7": 19, "edge_8": 20, "op_node_0": "conv3x3-bn-relu", "op_node_1": "conv3x3-bn-relu", "op_node_2": "conv3x3-bn-relu", "op_node_3": "conv3x3-bn-relu", "op_node_4": "conv3x3-bn-relu"}
```

提取payload：

```text
{"edge_0": 1, "edge_1": 2, "edge_2": 7, "edge_3": 8, "edge_4": 12, "edge_5": 16, "edge_6": 18, "edge_7": 19, "edge_8": 20, "op_node_0": "conv3x3-bn-relu", "op_node_1": "conv3x3-bn-relu", "op_node_2": "conv3x3-bn-relu", "op_node_3": "conv3x3-bn-relu", "op_node_4": "conv3x3-bn-relu"}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。

### 截断候选逐例

request_id `6fdfd2bb62934f69b7e87a6e85997970`；原始 10075 字符，finish_reason=stop，首个Action: offset=9799。提取工具 `evaluate_config`；payload JSON有效=True。

```text
mit...

Better: let me test with all edges = 1 but all ops = maxpool3x3 to rule out op-related invalidity. This is the single most informative test.

Action: evaluate_config {"edge_0": 1, "edge_1": 1, "edge_2": 1, "edge_3": 1, "edge_4": 1, "edge_5": 1, "edge_6": 1, "edge_7": 1, "edge_8": 1, "op_node_0": "maxpool3x3", "op_node_1": "maxpool3x3", "op_node_2": "maxpool3x3", "op_node_3": "maxpool3x3", "op_node_4": "maxpool3x3"}
```

提取payload：

```text
{"edge_0": 1, "edge_1": 1, "edge_2": 1, "edge_3": 1, "edge_4": 1, "edge_5": 1, "edge_6": 1, "edge_7": 1, "edge_8": 1, "op_node_0": "maxpool3x3", "op_node_1": "maxpool3x3", "op_node_2": "maxpool3x3", "op_node_3": "maxpool3x3", "op_node_4": "maxpool3x3"}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。