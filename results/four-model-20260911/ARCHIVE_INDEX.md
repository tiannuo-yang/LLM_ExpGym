# 四模型完整存档导航

本页集合 Kimi-K3、GLM-5.3、Qwen3.8 与 DeepSeek-V4-Flash-0731 的冻结原档、完整分析、原比较、成本与恢复入口；不新增实验，不重新封存，也不把规范化记录当作原始 dump。

机器可读导航见 [ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)，四模型主报告见 [README.zh.md](README.zh.md)。完整逐原件与逐分片身份沿固定子索引/manifest 获取，不在此复制数万行。

## 1. 模型级入口

| 模型 | 原完整报告 | 人读 / 机器索引 | raw collection / manifest |
| --- | --- | --- | --- |
| Kimi-K3 | [报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md) | [索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.md) / [JSON](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.json) | [原档入口](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/INDEX.kimi-k3-composite-v1.json) |
| GLM-5.3 | [报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md) | [索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.md) / [JSON](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.json) | [原档入口](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/INDEX.json) |
| Qwen3.8-2.4T-A95B-FP8 | [报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/README.zh.md) | [索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/ARCHIVE_INDEX.md) / [JSON](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/ARCHIVE_INDEX.json) | [原档入口](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/manifest.json) |
| DeepSeek-V4-Flash-0731 | [报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/README.zh.md) | [索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/ARCHIVE_INDEX.md) / [JSON](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/ARCHIVE_INDEX.json) | [原档入口](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/manifest.json) |

## 2. 封存载荷计数与边界

| 模型 | 旧 bundle | 新 single-manifest collection | tar | 原件 | 原字节 | 压缩字节 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kimi-K3 | 36 | 0 | 268 | 66,643 | 1,751,137,861 | 305,870,108 |
| GLM-5.3 | 37 | 0 | 288 | 71,634 | 3,467,116,893 | 772,603,212 |
| Qwen3.8-2.4T-A95B-FP8 | 0 | 1 | 24 | 31,386 | 1,437,241,763 | 235,083,685 |
| DeepSeek-V4-Flash-0731 | 0 | 1 | 22 | 26,444 | 1,384,642,088 | 237,500,959 |
| 合计（分格式） | 73 | 2 | 602 | 196,107 | 8,040,138,605 | 1,551,057,964 |

73 个旧 bundle 与 2 个新 single-manifest collection 是不同容器层级，不能合称 75 bundles。Kimi 36 包＝旧 34 包＋固定 8 项恢复 raw 1 包＋新 controls 1 包，旧包只计一次；有效合并不抹去旧失败尝试。

这些是各模型既有发布范围内的 tar 载荷相加：不跨模型内容去重；旧两模型为正式 collection（含 controls），新两模型还包括明确选入的 smoke、服务诊断、分析与运行身份原件。因此合计不是纯正式 dump 数、请求数或实验样本数。

原字节不含旧 tar 内嵌 member inventory 的额外开销，也不含外层附件及本次四模型报告；压缩字节只是 tar.gz 载荷，不是 Git clone 大小。完整存档还须保留子索引列出的外层 CSV/JSON/报告/代码/恢复说明，以及各固定报告提交和本次报告。外层与 tar 中同路径副本不再加入本表。

## 3. 每模型原件与完整分析导航

### Kimi-K3

正式 collection 的 raw 与 controls；Kimi composite 旧 34 包仅计一次，失败尝试保留；历史 smoke/DEV 不纳入该计数。

数据提交：`6119f9d136c9ed1f06a7bedd7371be0deb9b5d59`。原件映射：ARCHIVE_INDEX.json models['kimi-k3'].bundles[].shards[]: archive + member_inventory；完整原件在所指 inventory 中。

原档入口 SHA-256（继承子索引声明）：`a462bde564618f52b46b863095bfed5d2a97eb9c3ce4c730a34ac6fdad91a0f7`；12,428 B。

| 完整分析文件 | 用途 |
| --- | --- |
| [EXPORT_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/EXPORT_INDEX.json) | 完整导出清单；哈希/大小权威来源 |
| [ALL_ATTEMPT_COST_LEDGER.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/ALL_ATTEMPT_COST_LEDGER.json) | K3 旧运行及固定8项恢复的全部尝试成本账本 |
| [COMPOSITE_PROVENANCE.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/COMPOSITE_PROVENANCE.json) | K3 697+8 有效合并与旧失败来源映射 |
| [OUTPUT_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/OUTPUT_INDEX.json) | 原分析十输出清单；字节重现基线 |
| [SUMMARY.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/SUMMARY.zh.md) | 原分析摘要（不是全矩阵宽表） |
| [effects.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/effects.csv) | 514 条基线/目标/效应比较，包括 cached 和 PoolAct |
| [input_pins.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/input_pins.json) | 固定分析输入身份绑定 |
| [known_subsets.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/known_subsets.csv) | 可观测子集汇总；不得冒充完整未知成本 |
| [logical_outcomes.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/logical_outcomes.csv) | 逻辑单元终态及缺失分类 |
| [manifest.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/manifest.json) | 实际实验矩阵、计划单元及输入选择 |
| [metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/metrics.csv) | 逐 item / strategy / regime / outerseed 的绝对指标长表 |
| [oracle.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/oracle.json) | 冻结HPO/NAS参考性能与成本 |
| [paired_rows.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/paired_rows.csv) | 比较的逐题配对明细 |
| [provenance.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/provenance.json) | 分析 provenance / 输入来源 |
| [raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/raw_terminals.csv) | agent终态、答案与评分投影；不是HTTP用量清单 |
| [records.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/records.json) | 规范化正式结果记录；不等于 HTTP raw dump |
| [results.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/results.json) | 全部聚合比较及分析结果；机器可读 |
| [source_index.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/source_index.json) | 原件来源路径、大小和哈希；原路径重放前需重定位 |

交付和最终恢复验收：

- [FULL_DELIVERY.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/FULL_DELIVERY.zh.md)
- [README.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/README.zh.md)
- [REPLAY_VERIFIED.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/replay_verified_v1/REPLAY_VERIFIED.zh.md)
- [FILE_MANIFEST.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/replay_verified_v1/FILE_MANIFEST.json)

历史独立复核：[已发布复核](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_post_report_review_fixed8_v2/REVIEW.zh.md)。

### GLM-5.3

正式 collection 的 raw 与 controls；历史 smoke/DEV 不纳入该计数。

数据提交：`6119f9d136c9ed1f06a7bedd7371be0deb9b5d59`。原件映射：ARCHIVE_INDEX.json models['glm-5.3'].bundles[].shards[]: archive + member_inventory；完整原件在所指 inventory 中。

原档入口 SHA-256（继承子索引声明）：`9d4433461c3cf0a3017220003c2d70b5085e715c5db82303449d57e48c8cca09`；8,340 B。

| 完整分析文件 | 用途 |
| --- | --- |
| [EXPORT_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/EXPORT_INDEX.json) | 完整导出清单；哈希/大小权威来源 |
| [EXPORT_EVIDENCE.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/EXPORT_EVIDENCE.json) | GLM 正式导出 provenance / HTTP 全部尝试证据 |
| [OUTPUT_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/OUTPUT_INDEX.json) | 原分析十输出清单；字节重现基线 |
| [SUMMARY.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/SUMMARY.zh.md) | 原分析摘要（不是全矩阵宽表） |
| [effects.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/effects.csv) | 514 条基线/目标/效应比较，包括 cached 和 PoolAct |
| [input_pins.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/input_pins.json) | 固定分析输入身份绑定 |
| [known_subsets.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/known_subsets.csv) | 可观测子集汇总；不得冒充完整未知成本 |
| [logical_outcomes.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/logical_outcomes.csv) | 逻辑单元终态及缺失分类 |
| [manifest.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/manifest.json) | 实际实验矩阵、计划单元及输入选择 |
| [metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/metrics.csv) | 逐 item / strategy / regime / outerseed 的绝对指标长表 |
| [oracle.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/oracle.json) | 冻结HPO/NAS参考性能与成本 |
| [paired_rows.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/paired_rows.csv) | 比较的逐题配对明细 |
| [provenance.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/provenance.json) | 分析 provenance / 输入来源 |
| [raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/raw_terminals.csv) | agent终态、答案与评分投影；不是HTTP用量清单 |
| [records.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/records.json) | 规范化正式结果记录；不等于 HTTP raw dump |
| [results.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/results.json) | 全部聚合比较及分析结果；机器可读 |
| [source_index.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/source_index.json) | 原件来源路径、大小和哈希；原路径重放前需重定位 |

交付和最终恢复验收：

- [FULL_DELIVERY.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/FULL_DELIVERY.zh.md)
- [RESULTS.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/RESULTS.zh.md)
- [REPLAY_VERIFIED.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/replay_verified_v2/REPLAY_VERIFIED.zh.md)
- [FILE_MANIFEST.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/replay_verified_v2/FILE_MANIFEST.json)

历史独立复核：[已发布复核](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_post_report_review_fixed8_v2/REVIEW.zh.md)。

### Qwen3.8-2.4T-A95B-FP8

全封存选件：正式 dump/trace/queue，加明确选入的 smoke、服务诊断、analysis、study/runtime 原件；不等同纯正式请求集合。

数据提交：`03dd6ef0ed9a63cb673a7b4e62a5a19026015225`。原件映射：manifest files[].{path,archive,bytes,sha256}；子索引 archives[] 提供每个分片固定链接与 SHA。

原档入口 SHA-256（继承子索引声明）：`f3971da5944ac9b0eb8e81f7a2325af2c113cacb4dcc553928b05a05231099d7`；9,818,983 B。

| 完整分析文件 | 用途 |
| --- | --- |
| [analysis/full_v1/COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/COSTS.json) | 冻结聚合输出 |
| [analysis/full_v1/INPUTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/INPUTS.json) | 冻结聚合输出 |
| [analysis/full_v1/SOURCE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/SOURCE_INDEX.json) | 冻结聚合输出 |
| [analysis/full_v1/absolute_settings.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/absolute_settings.csv) | 冻结聚合输出 |
| [analysis/full_v1/all_attempt_costs.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/all_attempt_costs.csv) | 冻结聚合输出 |
| [analysis/full_v1/by_outerseed.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/by_outerseed.csv) | 冻结聚合输出 |
| [analysis/full_v1/contrasts.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/contrasts.csv) | 冻结聚合输出 |
| [analysis/full_v1/metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/metrics.csv) | 冻结聚合输出 |
| [analysis/full_v1/metrics_execution.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/metrics_execution.csv) | 冻结聚合输出 |
| [analysis/full_v1/normalized.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/normalized.csv) | 冻结聚合输出 |
| [analysis/full_v1/raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/raw_terminals.csv) | 冻结聚合输出 |

运行矩阵、身份与 Slurm 成本上下文：

- [study/RUN_INPUTS_launch02.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/RUN_INPUTS_launch02.json)
- [study/accounting.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/accounting.json)
- [study/formal_analysis_states.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_analysis_states.json)
- [study/formal_cache_salt/coverage.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_cache_salt/coverage.json)
- [study/formal_cache_salt/matrix.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_cache_salt/matrix.json)

全部外层附件由 [附件清单](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/archive_attachments.json) 和子索引列举：62 件 / 48,229,548 B；其中 61 件 / 43,702,154 B 有 tar member 身份副本，其余须另存。当前报告/复核等后续附件不自动算入历史清单。

复核导航边界：固定报告提交未提供独立 review 原件链接；不据报告流程说明宣称已提供复核原件。 [固定报告说明](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/README.zh.md)。

### DeepSeek-V4-Flash-0731

全封存选件：正式 dump/trace/queue，加明确选入的 smoke、服务诊断、analysis、study/runtime 原件；不等同纯正式请求集合。

数据提交：`41ec233f849aff05d8d91443118b6b2392d1cc40`。原件映射：manifest files[].{path,archive,bytes,sha256}；子索引 archives[] 提供每个分片固定链接与 SHA。

原档入口 SHA-256（继承子索引声明）：`b9166ac1d1395d39e072ab5f928fac26ab8a42c08beeb23e3e45cb426a4c8a58`；8,302,237 B。

| 完整分析文件 | 用途 |
| --- | --- |
| [analysis/full_v2/COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/COSTS.json) | 正式分析：COSTS.json |
| [analysis/full_v2/INPUTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/INPUTS.json) | 正式分析：INPUTS.json |
| [analysis/full_v2/SOURCE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/SOURCE_INDEX.json) | 正式分析：SOURCE_INDEX.json |
| [analysis/full_v2/absolute_settings.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/absolute_settings.csv) | 正式分析：absolute_settings.csv |
| [analysis/full_v2/all_attempt_costs.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/all_attempt_costs.csv) | 正式分析：all_attempt_costs.csv |
| [analysis/full_v2/by_outerseed.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/by_outerseed.csv) | 正式分析：by_outerseed.csv |
| [analysis/full_v2/contrasts.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/contrasts.csv) | 正式分析：contrasts.csv |
| [analysis/full_v2/metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/metrics.csv) | 正式分析：metrics.csv |
| [analysis/full_v2/metrics_execution.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/metrics_execution.csv) | 正式分析：metrics_execution.csv |
| [analysis/full_v2/normalized.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/normalized.csv) | 正式分析：normalized.csv |
| [analysis/full_v2/raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/raw_terminals.csv) | 正式分析：raw_terminals.csv |

运行矩阵、身份与 Slurm 成本上下文：

- [study/formal_v1/coverage.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/coverage.json)
- [study/formal_v1/matrix.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/matrix.json)

全部外层附件由 [附件清单](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/archive_attachments.json) 和子索引列举：51 件 / 54,262,771 B；其中 49 件 / 50,419,066 B 有 tar member 身份副本，其余须另存。当前报告/复核等后续附件不自动算入历史清单。

历史独立复核：[已发布复核](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/review/REVIEW.md)。

### 旧两模型共享成本与原报告比较

- [REPORT.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/REPORT.zh.md)
- [PRIMARY_RESULTS.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/PRIMARY_RESULTS.csv)
- [NEGATIVE_PERFORMANCE.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/NEGATIVE_PERFORMANCE.csv)
- [COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/COSTS.json)
- [INPUT_REFS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/INPUT_REFS.json)
- [report INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/INDEX.json)
- [成稿后独立科学复核](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_post_report_review_fixed8_v2/REVIEW.zh.md)
- [最终科学验收（限定范围）](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/k3_recovery_root_v1/FINAL_SCIENTIFIC_ACCEPTANCE.json)

旧 `effects.csv` / `results.json` 保留原比较定义；新 `contrasts.csv`、`absolute_settings.csv`、`by_outerseed.csv` 保留新分析定义。`raw_terminals.csv` 是终态/评分投影，不是 HTTP dump。Kimi 成本保留旧失败及恢复；reasoning 已包含于 output，不能再加一次；未知值不补 0。

## 4. 恢复与重放：按归档格式选择

### Kimi / GLM 旧格式

从 source_index 查来源相对路径，再沿 collection → bundle INDEX → member inventory → tar 找原件。旧恢复器还原为 `<恢复根>/<bundle_id>/payload/<workspace-relative-path>`，原 tar member 为 `data/<path>`。需要原 AN2 分析时使用匹配 relocator 和已记录 Python；不要直接执行 source_index 中原机器绝对路径。旧恢复/重放最终状态看各模型 REPLAY_VERIFIED，而非较早说明里的 pending。

Kimi-K3 分析解释器：CPython 3.11.15；匹配工具：

- [restore_collection.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/tools/publication/collection_restore_candidate_v2/restore_collection.py)
- [restore.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/tools/publication/shard_delivery_candidate_v2/restore.py)
- [common.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/tools/publication/shard_delivery_candidate_v2/common.py)
- [pack.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/tools/publication/shard_delivery_candidate_v2/pack.py)
- [validate_bundle_v2.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/tools/publication/validate_bundle_v2.py)
- [relocate.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/relocate.py)

GLM-5.3 分析解释器：CPython 3.10.12；匹配工具：

- [restore_collection.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/tools/publication/collection_restore_candidate_v2/restore_collection.py)
- [restore.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/tools/publication/shard_delivery_candidate_v2/restore.py)
- [common.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/tools/publication/shard_delivery_candidate_v2/common.py)
- [pack.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/tools/publication/shard_delivery_candidate_v2/pack.py)
- [validate_bundle_v2.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/tools/publication/validate_bundle_v2.py)
- [relocate.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/relocate.py)

旧格式不能交给新的 package_run.py 直接恢复。公共 controls 已排除有记录的非实验回执，私有审计引用链并非全部自包含；详见旧子索引。模型权重、环境实体、完整上游数据与私密凭据不在原档内。

### Qwen / DeepSeek 单 manifest 格式

- Qwen3.8-2.4T-A95B-FP8：[package_run.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/21b4de99b2a014874e3cec1595eaa40762b0c564/scripts/package_run.py) / [delivery.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/21b4de99b2a014874e3cec1595eaa40762b0c564/expgym/delivery.py)，版本 `21b4de99b2a014874e3cec1595eaa40762b0c564`。
- DeepSeek-V4-Flash-0731：[package_run.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8/scripts/package_run.py) / [delivery.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8/expgym/delivery.py)，版本 `5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8`。

先核对固定数据提交与 manifest 身份，再用对应源码运行：

```bash
python -B /absolute/frozen-source/scripts/package_run.py verify \
  --manifest /downloaded/release/sealed/manifest.json \
  --archive-dir /downloaded/release/sealed --require-public-scan
```

默认校验全部 shard 与 member，恢复 0 件。需部分原件时加 `--select <非空 JSON 路径数组>` 与 `--restore-dir <事先不存在的新目录>`；仍校验全部未提取成员。只有 CLI exit 0 表示该次完整性验证结束，目录存在不是成功，完整性也不是重新评分或科学真实性证明。`--require-public-scan` 只检查可信 manifest 中的历史扫描声明，不重新读取密钥扫描。

两份新模型 analyzer 都没有任意 root 的 `--relocate` / `--path-map` 能力。新根可浏览/验证 raw 和 CSV，但原样 raw→analysis 重放要求冻结的绝对 state/artifact/authorization 布局、controller.lock 与 session 等所有真实依赖、冻结脚本/Python 身份，以及新的输出目录。更改路径会改变输入身份；不能用 symlink 绕过，也不能承诺只恢复几份 CSV 就可原身份重放。

## 5. 本次实读证据与继承身份

本生成器实读并核对下列 6 份输入（JSON 用于元数据聚合，Markdown 固定恢复说明来源）。所有被链接的 collection、manifest、member、tar、分析及工具 SHA/大小均继承这些已发布索引；本步骤未打开它们。计数自检只核对既有元数据求和和物理 tar 路径唯一性，不是新内容验证、恢复、模型执行或科学复核。

| 本次实读输入 | 字节 | SHA-256 |
| --- | ---: | --- |
| [legacy/ARCHIVE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.json) | 1,412,583 | `1372ef13e22ccf6d7cbfa9726abee5d03878ab3a6b12045d7f5fc286b374d136` |
| [legacy/ARCHIVE_INDEX.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.md) | 45,486 | `fefd11aa95692549fdb684f93cb889239168144b8993338021a824b5b8099c59` |
| [qwen/ARCHIVE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/ARCHIVE_INDEX.json) | 48,505 | `9201a74f45fff5709f954ef369c00caa1f9977a4bd09af5f55ea6952f6aef7e4` |
| [qwen/ARCHIVE_INDEX.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/ARCHIVE_INDEX.md) | 30,008 | `10f91f477eb3be146ac1fbb95c9047f45784d2d212429fab2ec2dcf5e4d31e39` |
| [deepseek/ARCHIVE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/ARCHIVE_INDEX.json) | 44,492 | `431496f24b7cb8f602adb4d5792dc4ef98ebbaeb79e73c1b6a099bf9723c154f` |
| [deepseek/ARCHIVE_INDEX.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/ARCHIVE_INDEX.md) | 29,178 | `b5607cd125ee5382aa54303647fe63aef399ecc0ae4707affaf94de0ab2f44d7` |

生成器为 [build_archive_index.py](build_archive_index.py)，窄契约测试为 [test_archive_index.py](test_archive_index.py)。完整性通过固定子索引导航提供，未把数万 member 复制进本索引。这里的元数据自检不替代四模型正文成稿后的一次独立数字/逻辑复核，也不替代新发布文件的安全扫描。

复建只需将上述六份固定输入下载为文件；输入路径可变化，但内容 SHA 和固定来源不能变化：

```bash
python -B build_archive_index.py \
  --legacy-index /inputs/legacy/ARCHIVE_INDEX.json --legacy-guide /inputs/legacy/ARCHIVE_INDEX.md \
  --qwen-index /inputs/qwen/ARCHIVE_INDEX.json --qwen-guide /inputs/qwen/ARCHIVE_INDEX.md \
  --deepseek-index /inputs/deepseek/ARCHIVE_INDEX.json --deepseek-guide /inputs/deepseek/ARCHIVE_INDEX.md \
  --output-dir /path/to/four-model-report --check
```

`--check` 仅读取既有两份输出并逐字节比较，不写文件；省略时生成这两份索引，不更改实验数据或其他报告。脚本不联网、不扫描/解压 tar、不调用模型。
