# 最终实验项目 API 用量账单

范围为 v1、v2、v3 各 smoke/pilot/full 共九份 manifest 指定的 job dump 目录。包含已归档失败运行、未选中会话和已知 NAS101C 未落盘失败的全部 6 次调用；**不含 service probes、后台健康检查或其他非 manifest API 流量**，不是服务端所有请求的总账。机器可读范围与报告 SHA 见 [scope.json](scope.json)。

| 项目 | 值 |
|---|---:|
| 原始 dump 文件位置 | 17,046 |
| request_id 去重后 HTTP 调用 | 13,668 |
| 去除的相同字节副本 | 3,378 |
| v1 / v2 / v3 pilot→full 副本 | 1,092 / 1,093 / 1,193 |
| 输入 tokens（全部有报告） | 29,662,818 |
| 输出 tokens（全部有报告） | 3,973,226 |
| 在途 / HTTP 错误 / 宣告重试 | 0 / 0 / 0 |
| finish_reason=length | 5 |
| reasoning_content 非空响应 | 294 |
| reasoning_content 字符总量 | 960,140 |

13,668 次 HTTP 均成功，不表示其所在实验均通过评分校验。reasoning token counter 均为服务报告的 0，不能据此否认已保留的非空 reasoning 文本。缓存读/写 tokens 均未报告，known_sum=0、complete_total=null，不宣称缓存真实用量为零。

请求墙钟累计 150,180.634 秒包含并发重叠，不等于项目端到端耗时或 GPU-hours。此账单保留所有实验阶段成本，不能把正式 full_v3 分数对应的调用数直接当作项目全部消耗。

查验入口：[完整 JSON](project_usage_inventory.json)、[每个唯一请求与全部副本位置 CSV](unique_raw_requests.csv)。每份输入 manifest、每个 raw 文件位置均留有 SHA。旧 v1、v1+v2 账单保持不变。

独立审查未使用本账单的 inventory/audit helper，而是重新读取全部原始字节，计数、三代推广副本、终态和 tokens 均一致：[独立 JSON](../project_usage_final_independent_review/independent_project_usage.json)、[独立检算脚本](../project_usage_final_independent_review/verify_raw_attempts.py)。另核对 provider total_tokens=33,636,044，等于上述输入与输出之和。

[独立账单对比证据](../project_usage_final_independent_review/comparison.json) 的 339 项检查全部通过，涵盖九份 manifest SHA、阶段计数/缺失目录、状态、用量与 reasoning 观察。独立说明见[审查报告](../project_usage_final_independent_review/README.zh.md)。
