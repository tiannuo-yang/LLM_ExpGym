# 最终九份 manifest 调用用量：独立只读复核

独立直接读取原始 JSON 字节，未导入或调用 `inventory_project_attempts.py`、`audit_dumps.py`，未调用 API 或修改实验数据。`verify_raw_attempts.py` 与 `independent_project_usage.json` 留存完整方法及逐来源统计；`compare_reports.py` 将独立统计与正式账单逐项比较，结果留存于 `comparison.json`。

与正式账单的 **339 项机器对比全部通过**，覆盖总表及九份来源的 manifest 哈希、文件数、请求数、调用状态、缺失目录、token 完整性和 reasoning 观察值。

## 结论

17,046 个文件位置去重为 **13,668 次请求**，3,378 个推广副本不重复计费。所有请求均为 `success`、`attempt=1`，无在途请求、重试或 usage 对象缺失。

| 来源 | 原始文件位置 / 独立请求 | 缺失 dump 目录 |
|---|---:|---:|
| smoke | 136 | 0 |
| pilot | 1,092 | 0 |
| full | 1,985 | 278 |
| smoke_v2 | 138 | 0 |
| pilot_v2 | 1,093 | 0 |
| full_v2 | 2,195 | 278 |
| smoke_v3 | 146 | 0 |
| pilot_v3 | 1,193 | 0 |
| full_v3 | 9,068 | 0 |

三代 pilot/full 分别共享 1,092 / 1,093 / 1,193 个请求，且每个副本的原始字节 SHA256 相同。每代独立请求为 2,121 / 2,333 / 9,214，跨代请求 ID 交集均为 0。无临时文件；扫描前后文件 stat 与目录列表保持不变。

输入 **29,662,818 tokens**，输出 **3,973,226 tokens**，合计 **33,636,044 tokens**；每条均报告完整，且 provider total 等于 prompt + completion。缓存读写未报告：known sum 为 0，完整总额为 null。

顶层 `reasoning_tokens` 在全部 13,668 条响应中报告为 0，但 **294 条响应存在非空 reasoning 文本，共 960,140 字符**。两者单独报告，不将 provider 的 0 解释为没有 reasoning 文本。嵌套 reasoning 字段均未报告，来源冲突为 0。每条响应恰有一个 choice。

## 范围与限制

仅包含上述九份 manifest 的 `jobs[].dump_dir` 下留存的直接 `*.json` 文件，包括旧版本后来被废弃、未选中或任务失败时已经发生的调用。**不包含服务探测、健康检查、长上下文预热或其他 scope 外调用，因此不是完整 serving 生命周期账单。** 旧 full 的缺失目录不代表完整矩阵已运行，也不能证明目录外没有发生过调用。

本复核验证已留存调用的去重与用量，不验证 benchmark 结果。请求耗时相加存在并发重叠，不代表墙钟时长或 GPU-hours。

## 复跑

脚本采用标准库，输入只读；输出使用排他创建，须指定新的输出文件，避免覆盖本次证据：

```bash
python3 kimi_k3_eval/reports/project_usage_final_independent_review/verify_raw_attempts.py \
  --output /absolute/path/to/new_independent_report.json
python3 kimi_k3_eval/reports/project_usage_final_independent_review/compare_reports.py \
  --output /absolute/path/to/new_comparison.json
```

独立 JSON SHA256：`c90463d7c1dfe5736475c5e083bda86b35c68196e08c9591ceb659b7bc60fcb8`。

原始扫描脚本 SHA256：`480ce332e95862ee4605c8c52fc1158a285c6f0c0afa18476b76ff13bb93d709`。
