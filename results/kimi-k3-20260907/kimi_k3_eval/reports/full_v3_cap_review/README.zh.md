# full_v3：8000 字符 cap 的 22 例逐项静态复核

结论：18 例为当前 `_extract_action` 可识别、工具名正确且参数静态检查通过的明确工具请求，其中 4 例行首、14 例行内；另 4 例仅为 Thought／协议引用，提取 payload 不是合法 JSON。不能只把 4 个行首请求当作全部有效语法：Action 解析器仍接受行内标签，与 Answer 的行首规则不同。

这是完成后对真实 dump 的只读文本／参数复核，不是新 fake 实验，也没有执行候选工具、模型调用、评分、取消 cap 或重跑。

## 证据范围与结论边界

- 仅使用 `dumps/full-full_v3-ad4275b6/`，按源报告的 `trace_rows.client_id` 与 `raw_success_request_ids` 唯一关联；没有混入 pilot/smoke 副本。
- 22 个原始成功响应和对应保存轨迹全部逐字核对：常规响应应用原来的 `strip → 前 8000 字符 → 截断标记` 后，与保存的 assistant 消息一致。每例下一条 user 提示均为 Missing Action 强制回答。
- 每例恰有一个 `Action:` literal，均完全位于 cap 之后；没有更早引用遮蔽更晚 ReAct Action。未截断的 22 个响应也均无 `_extract_answer` 匹配。
- 原报告的 71 个超长常规响应总数已与其 trace_rows 求和核对；本审查独立读取的是所选 22 个候选原文，不声称重新逐字审查其余 49 个超长响应。
- 18 个完整请求通过工具名、JSON 与参数静态检查，说明 cap 移除了当前解析器本可识别的这些请求文本。仍未验证执行、剩余预算、反馈内容、架构有效性或反事实最终得分，不能据此声称取消 cap 会提高成绩。
- 原有 8000 **字符** cap 保留，区别于 API 的 8192 **token** 生成上限；没有更改源码、数据、正式结果或原始 dump。

## 参数静态检查

- 15 个 `human_feedback` 请求均为对象，`nda_id` 为当前文档存在的假设 ID，`evidence_ids` 为整数列表且每个 segment ID 存在。仅检查 ID 与类型，不比较 gold evidence、标签或调用 human feedback。
- 1 个 `search` 请求含非空字符串 `query`；未查询 corpus 或缓存。
- 2 个 `evaluate_config` 请求均属于 NAS101 **B**，全部 14 个参数齐备、无额外字段，9 个 edge selector 在 0..20 内，5 个 op 在实际候选集合内。不是 A 的 21 个二元边参数；未执行 DAG、表查找、性能或成本评价。静态 schema 合法不意味着架构或得分良好。

## 逐例索引

完整 client ID、唯一 raw/trace 路径、原文件与内容 SHA256、字符位置、完整提取 payload、schema 结果和语境注释均在 [review.json](review.json)。下面的 index 与原报告 `cap_candidate_evidence` 的零起始顺序一致。

| index | request_id / 原始 dump | 场景 | 标签位置 | 分类 | 参数静态检查 |
| --- | --- | --- | --- | --- | --- |
| 0 | [`d9fb6af772f640d5a4fd0289f01f9aa9`](../../dumps/full-full_v3-ad4275b6/expgym__evidence_audit__2__cost_moderate/d9fb6af772f640d5a4fd0289f01f9aa9.json) | evidence_audit | 行内 @8701 | 引用误候选 | JSON 不合法，未进入 schema 检查 |
| 1 | [`e51ec3db69c64e098ef3388c928ef227`](../../dumps/full-full_v3-ad4275b6/expgym__evidence_audit__7__cost_tight/e51ec3db69c64e098ef3388c928ef227.json) | evidence_audit | 行内 @8543 | 明确工具请求 | 通过；未执行 |
| 2 | [`ff5904821dd34269839d33090cf1b02e`](../../dumps/full-full_v3-ad4275b6/expgym__evidence_audit__9__cost_moderate/ff5904821dd34269839d33090cf1b02e.json) | evidence_audit | 行首 @8691 | 明确工具请求 | 通过；未执行 |
| 3 | [`4b00b0cbd3b8464693d05d7bf6fcb1dd`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__10__cost_free/4b00b0cbd3b8464693d05d7bf6fcb1dd.json) | evidence_audit | 行内 @8863 | 明确工具请求 | 通过；未执行 |
| 4 | [`54991b53c67b477495c626fc7b5480f3`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__11__cost_free/54991b53c67b477495c626fc7b5480f3.json) | evidence_audit | 行首 @8553 | 明确工具请求 | 通过；未执行 |
| 5 | [`4c27190a50db413aae0154aed3491deb`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__11__cost_moderate/4c27190a50db413aae0154aed3491deb.json) | evidence_audit | 行内 @12385 | 明确工具请求 | 通过；未执行 |
| 6 | [`df90cf6686354f3c8cba680a121f09c7`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__11__cost_moderate/df90cf6686354f3c8cba680a121f09c7.json) | evidence_audit | 行内 @28766 | 引用误候选 | JSON 不合法，未进入 schema 检查 |
| 7 | [`1fc7a45bdabd4443abeabd8449325053`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__12__cost_tight/1fc7a45bdabd4443abeabd8449325053.json) | evidence_audit | 行内 @8706 | 明确工具请求 | 通过；未执行 |
| 8 | [`32b82d5801c24feb83f054d2de0a47e2`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__3__cost_tight/32b82d5801c24feb83f054d2de0a47e2.json) | evidence_audit | 行内 @9006 | 明确工具请求 | 通过；未执行 |
| 9 | [`2206e9965d414c97aa5ab37a73a8c1c4`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__4__cost_tight/2206e9965d414c97aa5ab37a73a8c1c4.json) | evidence_audit | 行内 @8770 | 明确工具请求 | 通过；未执行 |
| 10 | [`d493b99b0683464b980c6ad42c5224dc`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__4__cost_tight/d493b99b0683464b980c6ad42c5224dc.json) | evidence_audit | 行内 @13049 | 明确工具请求 | 通过；未执行 |
| 11 | [`e2db5e604a974b82a0604a7778c8e7d4`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__5__cost_free/e2db5e604a974b82a0604a7778c8e7d4.json) | evidence_audit | 行内 @12464 | 明确工具请求 | 通过；未执行 |
| 12 | [`25b63a923ad94c4a8560b8f65732d78f`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__5__cost_moderate/25b63a923ad94c4a8560b8f65732d78f.json) | evidence_audit | 行内 @10298 | 明确工具请求 | 通过；未执行 |
| 13 | [`ed50b2af9f724b06a43b2dce7cd1dbf6`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__6__cost_free/ed50b2af9f724b06a43b2dce7cd1dbf6.json) | evidence_audit | 行内 @8840 | 明确工具请求 | 通过；未执行 |
| 14 | [`616687ae12db4f89b90f92b1c6035a08`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__7__cost_moderate/616687ae12db4f89b90f92b1c6035a08.json) | evidence_audit | 行内 @9519 | 明确工具请求 | 通过；未执行 |
| 15 | [`a663c51a07fc400890a41967cbab22e3`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__8__cost_tight/a663c51a07fc400890a41967cbab22e3.json) | evidence_audit | 行内 @12341 | 引用误候选 | JSON 不合法，未进入 schema 检查 |
| 16 | [`16515705ed994909831f9193591eab25`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__9__cost_moderate/16515705ed994909831f9193591eab25.json) | evidence_audit | 行内 @9890 | 明确工具请求 | 通过；未执行 |
| 17 | [`78b199fdc0374b8487d137da8c67fa35`](../../dumps/full-full_v3-ad4275b6/poolact__evidence_audit__9__cost_moderate/78b199fdc0374b8487d137da8c67fa35.json) | evidence_audit | 行内 @9532 | 明确工具请求 | 通过；未执行 |
| 18 | [`a876441349284408926545d6fb106203`](../../dumps/full-full_v3-ad4275b6/poolact__restricted_search__11__cost_free/a876441349284408926545d6fb106203.json) | restricted_search | 行首 @12030 | 明确工具请求 | 通过；未执行 |
| 19 | [`acdf7057d7484dfeb18a336e1ca8fb3b`](../../dumps/full-full_v3-ad4275b6/poolact__restricted_search__11__cost_free/acdf7057d7484dfeb18a336e1ca8fb3b.json) | restricted_search | 行内 @15489 | 引用误候选 | JSON 不合法，未进入 schema 检查 |
| 20 | [`a7bec99c747442818a82fd2358805a53`](../../dumps/full-full_v3-ad4275b6/poolact__tuning__hpobench_nasbench101_B__cost_moderate/a7bec99c747442818a82fd2358805a53.json) | tuning | 行内 @9938 | 明确工具请求 | 通过；未执行 |
| 21 | [`6fdfd2bb62934f69b7e87a6e85997970`](../../dumps/full-full_v3-ad4275b6/poolact__tuning__hpobench_nasbench101_B__cost_tight/6fdfd2bb62934f69b7e87a6e85997970.json) | tuning | 行首 @9799 | 明确工具请求 | 通过；未执行 |

4 个引用误候选是 indices 0、6、15、19。indices 6、15 在后文另有 K3 native 工具格式文本，但不是第二个 `Action:`，不把它算作当前 ReAct parser 支持的请求。index 19 的模型自述“forced answer/tool_choice=none”不是实际请求设置；该响应对应常规回合，引用用于讨论不应调用工具。

## 复查与文件

`review.py` 仅导入文本解析函数，读取既有 report/dump/trace 和参数定义；不导入或调用任何场景工具/evaluator。输出到 stdout，不改已生成 JSON。复查命令（从 `kimi_k3_eval/`，不要把 stdout 重定向覆盖正式证据）：

```sh
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 ../LLM_ExpGym/.venv/bin/python reports/full_v3_cap_review/review.py
```

独立语境审查见 [interpretation_even.json](interpretation_even.json) 与 [interpretation_odd.json](interpretation_odd.json)。源报告 SHA256 和解析器／schema 源文件 SHA256 记录于 [review.json](review.json)。

