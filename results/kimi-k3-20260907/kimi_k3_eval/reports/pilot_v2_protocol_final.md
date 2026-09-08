# pilot textual ReAct 协议诊断

完成时间：2026-09-07T09:59:51.441265+00:00。36 个 jobs、258 条 agent traces。统计仅使用已完成结果。

版本2修正：旧字段cap_removed_textual_action_responses仅代表解析器候选，不能解释为可执行Action被截掉。此版重命名并加入工具名/JSON检查及原文证据；旧报告保留供追溯。

| 路径/场景 | traces | missing_action | forced final | 原始native响应 | trace native消息 |
|---|---:|---:|---:|---:|---:|
| expgym | 42 | 24 | 28 | 14 | 14 |
| expgym/tuning | 27 | 13 | 16 | 8 | 8 |
| expgym/restricted_search | 6 | 4 | 5 | 1 | 1 |
| expgym/evidence_audit | 9 | 7 | 7 | 5 | 5 |
| poolact | 216 | 135 | 159 | 65 | 64 |
| poolact/tuning | 108 | 54 | 69 | 20 | 20 |
| poolact/restricted_search | 72 | 49 | 58 | 23 | 23 |
| poolact/evidence_audit | 36 | 32 | 32 | 22 | 21 |

原始 HTTP attempts=1093；state={'success': 1093}；finish_reason={'stop': 1093}。thinking={'False': 1093}，reasoning_tokens={'0': 1093}；结构化 tool_calls 非空响应=0。

native标签共出现在 79 个响应 / 82 个call开头；79/79 条含native标签trace在最后一个常规响应出现native标签后终止为missing_action，占全部missing_action的 79/159。原始响应与保存trace在应用现有截断规则后完全一致：258/258。

常规响应超过8000字符：5；截断前存在、截断后消失的Action解析候选：1，其中仅通过预期工具名+JSON语法检查的候选：1。解析器会匹配长Thought中引用的Action:，因此这些计数不证明存在可执行动作，也不能据此归因于cap。即使工具名和JSON有效，仍未验证参数schema或实际执行。此cap是仓库既有行为，forced final不受该8000字符cap约束。

thinking参数与返回的reasoning字段需分开报告：29 个响应的reasoning_content非空，共 88811 字符，虽usage.reasoning_tokens的取值为 {'0': 1093}。因此只能确认请求了thinking=false及服务报告的token字段，不能据此证明模型完全没有产生reasoning channel。客户端仅保存content到多轮trace history，完整reasoning_content仍可在原始dump按request_id查验。

终止原因（原字段名是 termination_reason）：

```json
{
  "expgym": {
    "missing_action": 24,
    "natural_answer": 14,
    "time_budget_exceeded": 4
  },
  "poolact": {
    "missing_action": 135,
    "natural_answer": 57,
    "time_budget_exceeded": 24
  }
}
```

ExpGym answer_source：`{"forced_model_answer": 26, "natural_model_answer": 12, "best_evaluated_fallback": 4}`。PoolAct legacy agent结果未序列化termination_reason/answer_source；此处termination原因从保存的强制回答提示推导，不能将推导字段当原始字段。

promotion匹配使用保存的client_id与逐响应文本；原dumpcontext中的pilot路径和run_id作为证据保留，不影响full中的对应关系。promotion map及文件hash由独立dump审计确认。本脚本只应扫描目标stage的dump目录；若同时扫描pilot/full副本，重复request_id会拒绝。raw总体计数涵盖该目录全部attempt，trace分组仅统计保存client_id关联的attempt。

## 解释与论文语义

本次请求使用论文textual ReAct：Action: tool_name JSON。K3原生XTML工具通道 `<|open|>tools<|sep|><|open|>call tool=...` 不属于该语法。客户端未发送结构化tools，也未转换XTML；此类工具意图不会作为Action执行，随后按仓库协议强制最终回答。应同时报告协议遵循失败率、实际tool调用、强制回答率及得分，不能将其仅解释为任务知识能力不足，也不能用score复算通过替代交互协议成功。

missing_action与有效最终得分可同时成立：强制回答后原中断标记仍保留；Tuning还可能使用best_evaluated_fallback。HTTP成功、结果完整性、动作格式遵循和语义正确率是不同维度。

在严格主实验中保留统一textual ReAct语义并披露这些失败。若另做K3 native适配，需将其列为独立协议敏感性实验，并对ExpGym及PoolAct各策略应用相同适配，重新保留manifest和dump；不要把适配后的结果混入原配置。smoke的4-step/3-evaluation/N=2不能用于推断论文30-step/N=4失败率。

代码依据：LLM_ExpGym/expgym/react_loop.py:304（8000字符cap）、:312（Action/Answer解析）、:332（missing_action）、:453（forced final）、:519（tuning fallback）、:737（字面Action）；expgym/llm_clients.py:358（仅content）、:405（无tools）；expgym/trace_v2.py:202（原因映射）。原始标签证据及request/client/trace对应关系见同名JSON。


### 截断候选逐例

request_id `2f4a0779895044d1b4b88a125fd3d6ad`；原始 8148 字符，finish_reason=stop，首个Action: offset=8063。提取工具 `human_feedback`；payload JSON有效=True。

```text
 few key ones using human_feedback. I'll verify nda-16, nda-7, nda-20, and maybe nda-2.

Let me start with verifying evidence IDs for some hypotheses.Action: human_feedback {"nda_id": "nda-16", "evidence_ids": [60, 84, 85, 86, 87, 88]}
```

提取payload：

```text
{"nda_id": "nda-16", "evidence_ids": [60, 84, 85, 86, 87, 88]}
```

这里只记录静态解析候选，不认为未截断时工具即可成功执行。