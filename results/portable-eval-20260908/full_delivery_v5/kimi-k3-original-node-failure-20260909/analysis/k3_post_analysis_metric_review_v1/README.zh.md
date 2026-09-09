# K3 冻结输出后的独立指标审阅

范围仅为自然闭合的本次 K3 v5：705 invocation 中 697 terminal、8 infrastructure_error；783 planned logical、1881 planned agents。不是最终双模型验收。

审阅者没有编写 runner/exporter/主汇总器，没有提前读取当前质量结果。此前做过冻结解析/投票及诊断候选的静态与合成审阅、发布工具审阅，因此对规则不是全盲，但对本次实际结果没有预先选择。独立重写的公式/投票函数不 import 原 scorer、投票器、Gap 或 converter。人工期望的 12 个合成用例先执行；实际读取时禁 socket 与子进程调用。

固定输入为 ROOT 指定的 plan/execution/seal/source acceptance 与 EXPORT_INDEX；全 17 个输出绑定、86 个源码和封存索引逐项 SHA。只从 records 的明确路径读取原结果/agent 文件，并同时核原封存索引。每个 planned 单元保留，包括错误；partial artifact 仅哈希，不把残余 agent 当完整 N4。

Search 仅读 plan 固定的 seed2/3 小 QA parquet 的 answer/type/difficulty 列，按原稳定排序规则定位已选 73 题；不读取 corpus。Audit 读取固定单一 JSON 容器，但只从已选 13 文档的 annotation_sets[0] 提取 gold；不输出 gold/答案正文。HPO 只用已持久化 reported perf 和原定 oracle 的 mean/best 做下限 clip、MI/BoN/unknown 复核；未做后端查表、有效配置复核或 oracle 真值验证。

原件不变。结果输出每条数值 reported/独立期望/delta/是否在预定 rel=abs=1e-9 内，字符串只比较类型/长度/SHA。覆盖全部完整个体、全部完整 N4 及 39 个三 order 文档组、所有性能 metric cells 与独立已知子集。主效应/配对另由 `/root/runner_integration/formal_scope_readonly/display_m1_readonly/main_analyzer_readonly` 独立审阅（paper_matrix 作者已撤回），费用另由费用 reviewer 审阅。N4 与固定 orders 不作为独立统计重复。

验证对象是 persisted final answer，不冒称与模型字面最后输出相同。Search/Audit 解析差异、标签规范化与投票是现行端点的规则；本脚本不改规则、不进行替代政策重评分。实际差异会保留全部对账及首个反例位置，并通知 ROOT；不修改得分、重跑模型或挑选有利样本。

脚本实际执行前固定代码 SHA；首次实际执行输出使用 `actual_v1`，若失败保留其工具记录，任何后续脚本修正须说明原因。代码、合成测试与实际结果不混为一份通过声明。

实际已一次执行完成：exit 0，13,402 项对账零超容差差异；完整 1,855/1,881 个体、360/366 个 N4、全部 1,455 性能 cells。8 个缺失 invocation（Exp HPO 2、Pool HPO 6）保留 error/unknown。46 项非零浮点差最大绝对值 1.1102230246251565e-16、最大相对值 1.9428902930940237e-16；3 条真实 Gap>100 与这类浮点等价分开披露。完整过程、分母、解释边界及 SHA 见 `EXECUTION.json`、`FINDINGS.zh.md` 与 `actual_v1/INDEX.json`。不因此声称已核 HPO 后端真值、字面模型终答选择或最终双模型结论。
