# v2 HPO 最终回答子串匹配：离线影响范围快照

本次为 Custom study 的只读诊断，不是新模型实验或新评分。推荐查验 [snapshot2/evidence.json](snapshot2/evidence.json) 和 [逐文件索引](snapshot2/scanned_results.csv)；snapshot1 保留作为早期扫描证据。

## 已落盘结果的结论

扫描 smoke_v2 15 个、pilot_v2 135 个、full_v2 317 个已保存 HPO trace/agent 文件，共 467 个位置。按 system/client_id 去重并要求副本字节一致后为 332 条独立结果，135 个位置为 pilot→full 副本。full 在扫描时仍处于 drain，未落盘路径和当时完整 progress 均保留，不能称全矩阵扫描完成。

332 条结果全部保留了通过的 score_check/validation；其中“实际持久化最终 answer 不是 json.loads 合法 JSON，但 answer_perf 为数字”的记录为 **0**。进一步要求某个 canonical JSON eval record 的 raw argument 命中最终 answer 子串，候选仍为 **0**。在这些已保存 answer/eval_records 上，旧 lookup 与拟议 canonical-only 修复的结果变化为 **0**。

因此，不能用本次快照声称已经发现其他通过结果受此修复影响。独立只读复核 smoke/pilot 150 个产物也得到零候选。此结论仅适用于当前已保存结果，不涵盖未落盘失败、剩余任务或未来输出；统一新源码正式矩阵是源码一致性要求，不是这次零候选扫描证明了所有旧分数错误。

## 单列的未落盘失败

NAS101:C / Moderate / naive / agent 3，client_id `28ad2bfa6e37435da3638778796e5fde`，原失败诊断为 [独立离线重放证据](../nas101c_moderate_agent3_diagnostic/evidence.json)。本扫描没有再次运行模型、环境或重评分，只独立检查该已存重放结果中的原 final、5 条 eval_records 和对应 lookup 分支。

原 final 非合法 JSON，含第 5 条 canonical eval record 的完整 raw argument；旧 lookup 返回 0.9388020833333334，但原离线重放 score_check 为 false、recomputed_perf 为 0。跳过该子串关联后进入已有 best_evaluated_fallback，候选重放记录的 reported/recomputed 均为 0.9388020833333334。完整原 final、eval_records、raw 路径/SHA 和两种原存 score_check 已收录在 snapshot2 的 separate_unsaved_failure_evidence，未算作通过结果。

## 边界及证据强度

ExpGym 原 eval_records 未重复序列化，故从 visible_to_model=true 且 performance 为数字的 evaluate_config tool_calls 按序恢复：raw argument 取 request_message_id 的原 assistant 文本，经现有 _extract_action 提取并与已存 arguments 核对；排除 withheld/超预算调用。PoolAct 直接读取原 eval_records。

另有三个无 API 的合成边界检查（当前 Python 与 Python 3.7 均通过）。合成例展示：若非 JSON final 子串命中零分记录，而 malformed-final 的重评分亦为 0，则当前可能通过；修复后已有 fallback 可以选择另一条更高分记录。它仅证明机制上存在影响有效零分的可能，不是本次模型的观测结果。

所有扫描原文件保持不变。脚本只做 JSON/字符串比对，没有发 API，也没有运行任何 objective evaluator。

## SHA256

- scan.py：`850f9437ba0c5870cfcfa6e87a4ae96419eaff03352653715930c4b5788fa54f`
- snapshot2/evidence.json：`2cb01dd3e6e65be4601f5e17cc2b8c855cf9297604f544b97ffff8c73ed5ca61`
- snapshot2/scanned_results.csv：`b80ff9b459015b2e55bde1cf5223edae3cc1f6956f4d80dd0d6a85dd4087074e`
