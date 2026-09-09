# K3 v2 usage 独立核验结果

本项一次实际执行通过：session `83570`，真实 exit 0，完成 chunk `5f4d77`。核验器不导入或调用 exporter / AN2 函数；16 个手算合成测试先通过，并在实际读取前完成独立静态复核。

## 覆盖和对账

封存清单中的全部 **16,320 个 raw** 都核对了原路径、bytes、SHA、文件名与内部 request ID、唯一 logical/seed/agent 或 order 归属；没有重复、遗漏或 generation attempt 缺口。

全部 **783 个 logical records** 的三个 usage sidecar（每项 attempts / known_sum / unknown_attempts / complete_total）与 record 的 input/output/reasoning 端点均一致。记录状态为 775 terminal、8 infrastructure_error，不因失败删除费用观察。

16,257 success 请求均有合法 flat reasoning 值；63 error 请求三个字段均 unknown。未出现 flat/nested 合法值冲突或单请求 reasoning 超过 completion。未发现 nested 的实际样本，不把 synthetic 兼容测试误称为 nested 的实际覆盖。

## 两种分母不能混为总账

下表都是对应范围的 **已知部分之和**，不是全运行完整 token 总量。

| 范围 | 输入 P | 输出 C（含 R） | reasoning R |
| --- | ---: | ---: | ---: |
| 全 16,320 attempts 的已知部分 | 119,973,435 | 15,715,139 | 13,599,445 |
| 775/783 个字段完整 records 的已知子集 | 118,059,826 | 15,413,301 | 13,388,585 |
| 8 个 infra records 的已知部分 | 1,913,609 | 301,838 | 210,860 |

8 个 infra records 包含 222 次请求，其中 159 次有已知 usage，63 次 unknown。因此“完整 record 字段子集”比全 attempts 已知部分少，并不表示这些失败 records 没有产生 token。

全 attempts 的 P/C/R 各有 63 unknown，三个 `complete_total` 均为 **null**。按 AN2 同定义独立推导的 record 字段总账，每字段 `n_known=775 / n_expected=783`，全量 `total` 也均为 **null**。该子集从独立原请求核验结果推导，不从 AN2 results 或 observer 总数反填。

Reasoning 已包含在 completion/output 中，**不能把 C 与 R 相加**。本项未估算缺失 usage，也未验证供应商真实收费、GPU 费用或服务端 tokenization。

## 可查验产物与限制

`actual_v1/attempts.jsonl` 保存 16,320 条数值/身份/原件 ref；`logical_usage.json` 保存 783 条逐记录对账；`SUMMARY.json` 保存状态分账及明确边界；`INDEX.json` 绑定另外三个文件的 SHA/bytes。四文件 exact 集合、输出 SHA/bytes、行数均已在进程真实结束后核对。

只读取一次选定原件，读取前后与最后 stat 稳定；没有重复遍历原 raw、修改原件、重导出或运行模型/scorer。原 raw JSON 容器整体读取/反序列化不可避免，但没有语义检查或输出响应正文、reasoning body、答案、gold、私钥。记录中的使用量仍是服务端报告数字，不是对实际 tokenizer 的独立计数。

本项只证明**已封存请求集合**中的 usage 复算与新 records 相符，不独立证明不存在未 dump 的 HTTP。也未重核 agent ledger 另存 token 字段、性能指标、HPO 后端真值、模型质量或最终双模型结论。
