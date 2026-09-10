# 上一次正式运行：完整存档与结果索引

这是原始数据、逐题指标、全部聚合比较与恢复入口的统一导航；不是只列六个主比较。

所有原数据链接固定到 `6119f9d136c9ed1f06a7bedd7371be0deb9b5d59`；本页新增索引不改写该提交中的实验结果。机器可读的逐包/逐 tar 分片完整路径、大小、SHA-256 见 [ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)。

## 一次取回完整原档

```bash
git clone --single-branch --branch results/portable-eval-20260908 https://github.com/tiannuo-yang/LLM_ExpGym.git LLM_ExpGym-results
cd LLM_ExpGym-results
git checkout --detach 6119f9d136c9ed1f06a7bedd7371be0deb9b5d59
```

完整存档＝该固定提交的仓库文件（tar、外层CSV/JSON/报告/工具与重放说明）＋本次新增索引/完整报告。**仅下载556个tar不等于存齐全部外层报告与附件。** 上面checkout会回到旧数据提交；本新报告属于后续提交，需另保留当前报告目录，或保留最新完整clone并用旧提交校验原数据。已有clone可fetch，不必重复clone。数据读取不需要模型、GPU或API密钥；权重、虚拟环境及完整上游数据不在此归档中。

## 范围与去重

| 模型 | bundle 包数 | tar 分片 | 原文件 | 原字节 | 压缩字节 |
| --- | ---: | ---: | ---: | ---: | ---: |
| kimi-k3 | 36 | 268 | 66,643 | 1,751,137,861 | 305,870,108 |
| glm-5.3 | 37 | 288 | 71,634 | 3,467,116,893 | 772,603,212 |
| 合计 | 73 | 556 | 138,277 | 5,218,254,754 | 1,078,473,320 |

K3 的36包＝旧34包＋固定8项恢复 raw 1包＋新 controls 1包；**不再把旧34包作为第三份 collection 重复计数**。GLM为36个正式 raw 包＋1个 controls 包。不同模型自带的共享 controls 原件按各自归档计数，不跨模型物理去重；文件数不是模型调用数或独立实验样本数。历史 smoke/DEV 不混入正式分母。

## 先看哪份表

| 想查什么 | 文件 |
| --- | --- |
| 每个题目/任务、预算、策略、重复的绝对得分 | `metrics.csv`（含 Free/Moderate/Tight；PoolAct实际只跑Moderate/Tight） |
| 聚合基线、目标策略与差值 | `effects.csv` / `results.json`；每模型514比较，包含资源与缺失项，不是514个独立性能实验 |
| 每条比较的逐题配对 | `paired_rows.csv` |
| 具体跑了什么、结果和来源 | `manifest.json`、`records.json`、`source_index.json` |
| agent终态、答案与评分投影 / 逻辑单元缺失分类 | `raw_terminals.csv` / `logical_outcomes.csv`；不是HTTP请求或usage清单 |
| 完整请求/回复、HTTP失败、token与所有尝试 | 原始dump、K3 `ALL_ATTEMPT_COST_LEDGER.json`、GLM `EXPORT_EVIDENCE.json` |
| 全 raw 原始请求/回复/trace | 下方完整 collection → bundle INDEX → member inventory → tar；不是用规范化 records 替代原始 dump |

`effects.csv` 中 PoolAct 的 baseline=naive，target=该行 cached/poolact；ExpGym 比较为Free/Tight，不能因比较表的regime空白就认为Moderate没跑。`metrics.csv` 才是所有实际档位/策略绝对分数长表。Free下的PoolAct和未注册任务/档位组合未跑，不能补成0。

### kimi-k3：完整分析文件

字节重放解释器：**CPython 3.11.15**。

| 文件 | 用途 | 字节 |
| --- | --- | ---: |
| [EXPORT_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/EXPORT_INDEX.json) | 完整导出清单；哈希/大小权威来源 | 1,991 |
| [ALL_ATTEMPT_COST_LEDGER.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/ALL_ATTEMPT_COST_LEDGER.json) | K3 旧运行及固定8项恢复的全部尝试成本账本 | 19,472,963 |
| [COMPOSITE_PROVENANCE.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/COMPOSITE_PROVENANCE.json) | K3 697+8 有效合并与旧失败来源映射 | 24,707,022 |
| [OUTPUT_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/OUTPUT_INDEX.json) | 原分析十输出清单；字节重现基线 | 1,097 |
| [SUMMARY.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/SUMMARY.zh.md) | 原分析摘要（不是全矩阵宽表） | 1,923 |
| [effects.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/effects.csv) | 514 条基线/目标/效应比较，包括 cached 和 PoolAct | 149,634 |
| [input_pins.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/input_pins.json) | 固定分析输入身份绑定 | 253 |
| [known_subsets.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/known_subsets.csv) | 可观测子集汇总；不得冒充完整未知成本 | 30,776 |
| [logical_outcomes.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/logical_outcomes.csv) | 逻辑单元终态及缺失分类 | 737,030 |
| [manifest.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/manifest.json) | 实际实验矩阵、计划单元及输入选择 | 2,363,699 |
| [metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/metrics.csv) | 逐 item / strategy / regime / outerseed 的绝对指标长表 | 1,434,509 |
| [oracle.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/oracle.json) | 冻结HPO/NAS参考性能与成本 | 28,814 |
| [paired_rows.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/paired_rows.csv) | 比较的逐题配对明细 | 553,781 |
| [provenance.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/provenance.json) | 分析 provenance / 输入来源 | 514,927 |
| [raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/raw_terminals.csv) | agent终态、答案与评分投影；不是HTTP用量清单 | 4,464,182 |
| [records.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/records.json) | 规范化正式结果记录；不等于 HTTP raw dump | 7,808,432 |
| [results.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/results.json) | 全部聚合比较及分析结果；机器可读 | 11,745,078 |
| [source_index.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/source_index.json) | 原件来源路径、大小和哈希；原路径重放前需重定位 | 1,069,770 |

### glm-5.3：完整分析文件

字节重放解释器：**CPython 3.10.12**。

| 文件 | 用途 | 字节 |
| --- | --- | ---: |
| [EXPORT_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/EXPORT_INDEX.json) | 完整导出清单；哈希/大小权威来源 | 1,821 |
| [EXPORT_EVIDENCE.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/EXPORT_EVIDENCE.json) | GLM 正式导出 provenance / HTTP 全部尝试证据 | 24,941,524 |
| [OUTPUT_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/OUTPUT_INDEX.json) | 原分析十输出清单；字节重现基线 | 1,097 |
| [SUMMARY.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/SUMMARY.zh.md) | 原分析摘要（不是全矩阵宽表） | 1,925 |
| [effects.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/effects.csv) | 514 条基线/目标/效应比较，包括 cached 和 PoolAct | 154,103 |
| [input_pins.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/input_pins.json) | 固定分析输入身份绑定 | 253 |
| [known_subsets.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/known_subsets.csv) | 可观测子集汇总；不得冒充完整未知成本 | 30,893 |
| [logical_outcomes.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/logical_outcomes.csv) | 逻辑单元终态及缺失分类 | 737,030 |
| [manifest.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/manifest.json) | 实际实验矩阵、计划单元及输入选择 | 2,363,699 |
| [metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/metrics.csv) | 逐 item / strategy / regime / outerseed 的绝对指标长表 | 1,440,254 |
| [oracle.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/oracle.json) | 冻结HPO/NAS参考性能与成本 | 28,814 |
| [paired_rows.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/paired_rows.csv) | 比较的逐题配对明细 | 568,654 |
| [provenance.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/provenance.json) | 分析 provenance / 输入来源 | 514,928 |
| [raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/raw_terminals.csv) | agent终态、答案与评分投影；不是HTTP用量清单 | 4,665,817 |
| [records.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/records.json) | 规范化正式结果记录；不等于 HTTP raw dump | 8,622,598 |
| [results.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/results.json) | 全部聚合比较及分析结果；机器可读 | 11,978,331 |
| [source_index.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/source_index.json) | 原件来源路径、大小和哈希；原路径重放前需重定位 | 1,069,482 |

## 综合报告、成本与反例

- [REPORT.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/REPORT.zh.md)
- [PRIMARY_RESULTS.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/PRIMARY_RESULTS.csv)
- [NEGATIVE_PERFORMANCE.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/NEGATIVE_PERFORMANCE.csv)
- [COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/COSTS.json)
- [INPUT_REFS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/INPUT_REFS.json)
- [report INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/INDEX.json)
- [成稿后独立科学复核](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_post_report_review_fixed8_v2/REVIEW.zh.md)
- [最终科学验收（限定范围）](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/k3_recovery_root_v1/FINAL_SCIENTIFIC_ACCEPTANCE.json)

K3成本须同时保留旧失败运行与固定8项恢复；有效697+8结果不能覆盖旧失败尝试。未知usage保留unknown/null，不按0计；reasoning已包含于completion，不能重复相加。所有负向比较照存。

## 原始数据与恢复导航

### kimi-k3

[完整 collection INDEX](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/INDEX.kimi-k3-composite-v1.json)，12,428 B，SHA-256：`a462bde564618f52b46b863095bfed5d2a97eb9c3ce4c730a34ac6fdad91a0f7`。

- [FULL_DELIVERY.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/FULL_DELIVERY.zh.md)
- [README.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/README.zh.md)
- [REPLAY_VERIFIED.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/replay_verified_v1/REPLAY_VERIFIED.zh.md)
- [FILE_MANIFEST.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/replay_verified_v1/FILE_MANIFEST.json)

| bundle（点开原清单） | 原件类别/来源段 | 原文件 | 原字节 | tar分片 | 压缩字节 |
| --- | --- | ---: | ---: | ---: | ---: |
| [batch-000001](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000001/payload/INDEX.json) | raw / original-formal | 2,000 | 90,608,432 | 8 | 18,906,727 |
| [batch-000002](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000002/payload/INDEX.json) | raw / original-formal | 2,000 | 71,350,444 | 8 | 13,620,210 |
| [batch-000003](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000003/payload/INDEX.json) | raw / original-formal | 2,000 | 81,198,547 | 8 | 16,447,121 |
| [batch-000004](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000004/payload/INDEX.json) | raw / original-formal | 2,000 | 78,144,239 | 8 | 15,468,215 |
| [batch-000005](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000005/payload/INDEX.json) | raw / original-formal | 2,000 | 85,326,157 | 8 | 16,925,650 |
| [batch-000006](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000006/payload/INDEX.json) | raw / original-formal | 2,000 | 83,944,421 | 8 | 16,757,332 |
| [batch-000007](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000007/payload/INDEX.json) | raw / original-formal | 2,000 | 79,393,644 | 8 | 16,008,781 |
| [batch-000008](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000008/payload/INDEX.json) | raw / original-formal | 2,000 | 74,725,428 | 8 | 14,052,348 |
| [batch-000009](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000009/payload/INDEX.json) | raw / original-formal | 2,000 | 138,151,362 | 8 | 28,203,199 |
| [batch-000010](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000010/payload/INDEX.json) | raw / original-formal | 2,000 | 154,392,707 | 8 | 29,391,173 |
| [batch-000011](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000011/payload/INDEX.json) | raw / original-formal | 2,000 | 21,804,557 | 8 | 3,915,528 |
| [batch-000012](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000012/payload/INDEX.json) | raw / original-formal | 2,000 | 2,644,524 | 8 | 530,672 |
| [batch-000013](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000013/payload/INDEX.json) | raw / original-formal | 2,000 | 2,633,919 | 8 | 532,075 |
| [batch-000014](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000014/payload/INDEX.json) | raw / original-formal | 2,000 | 2,622,687 | 8 | 535,755 |
| [batch-000015](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000015/payload/INDEX.json) | raw / original-formal | 2,000 | 2,649,256 | 8 | 538,080 |
| [batch-000016](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000016/payload/INDEX.json) | raw / original-formal | 2,000 | 2,666,037 | 8 | 538,674 |
| [batch-000017](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000017/payload/INDEX.json) | raw / original-formal | 2,000 | 2,657,699 | 8 | 535,565 |
| [batch-000018](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000018/payload/INDEX.json) | raw / original-formal | 2,000 | 2,672,063 | 8 | 535,201 |
| [batch-000019](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000019/payload/INDEX.json) | raw / original-formal | 2,000 | 2,639,255 | 8 | 541,020 |
| [batch-000020](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000020/payload/INDEX.json) | raw / original-formal | 2,000 | 2,707,699 | 8 | 546,134 |
| [batch-000021](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000021/payload/INDEX.json) | raw / original-formal | 2,000 | 2,586,265 | 8 | 523,286 |
| [batch-000022](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000022/payload/INDEX.json) | raw / original-formal | 2,000 | 2,590,054 | 8 | 538,113 |
| [batch-000023](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000023/payload/INDEX.json) | raw / original-formal | 2,000 | 2,730,922 | 8 | 542,820 |
| [batch-000024](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000024/payload/INDEX.json) | raw / original-formal | 2,000 | 2,576,876 | 8 | 533,963 |
| [batch-000025](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000025/payload/INDEX.json) | raw / original-formal | 2,000 | 2,672,216 | 8 | 538,437 |
| [batch-000026](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000026/payload/INDEX.json) | raw / original-formal | 2,000 | 2,653,442 | 8 | 536,209 |
| [batch-000027](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000027/payload/INDEX.json) | raw / original-formal | 2,000 | 2,654,802 | 8 | 540,101 |
| [batch-000028](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000028/payload/INDEX.json) | raw / original-formal | 2,000 | 2,648,797 | 8 | 533,690 |
| [batch-000029](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000029/payload/INDEX.json) | raw / original-formal | 2,000 | 2,645,724 | 8 | 544,118 |
| [batch-000030](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000030/payload/INDEX.json) | raw / original-formal | 2,000 | 2,645,468 | 8 | 535,813 |
| [batch-000031](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000031/payload/INDEX.json) | raw / original-formal | 2,000 | 49,983,724 | 8 | 10,431,221 |
| [batch-000032](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000032/payload/INDEX.json) | raw / original-formal | 2,000 | 191,169,663 | 8 | 34,867,755 |
| [batch-000033](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/batch-000033/payload/INDEX.json) | raw / original-formal | 188 | 18,021,943 | 1 | 3,439,920 |
| [controls](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/collection/controls/payload/INDEX.json) | controls / original-formal | 917 | 253,018,660 | 4 | 26,368,899 |
| [recovery-raw-000001](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/payload/collection/recovery-raw-000001/payload/INDEX.json) | raw / fixed8-recovery | 1,072 | 34,520,799 | 5 | 6,178,203 |
| [recovery-controls-000001](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/payload/collection/recovery-controls-000001/payload/INDEX.json) | controls / fixed8-recovery | 466 | 195,085,429 | 2 | 24,688,100 |

### glm-5.3

[完整 collection INDEX](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/INDEX.json)，8,340 B，SHA-256：`9d4433461c3cf0a3017220003c2d70b5085e715c5db82303449d57e48c8cca09`。

- [FULL_DELIVERY.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/FULL_DELIVERY.zh.md)
- [RESULTS.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/RESULTS.zh.md)
- [REPLAY_VERIFIED.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/replay_verified_v2/REPLAY_VERIFIED.zh.md)
- [FILE_MANIFEST.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/replay_verified_v2/FILE_MANIFEST.json)

| bundle（点开原清单） | 原件类别/来源段 | 原文件 | 原字节 | tar分片 | 压缩字节 |
| --- | --- | ---: | ---: | ---: | ---: |
| [batch-000001](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000001/payload/INDEX.json) | raw / original-formal | 2,000 | 227,736,423 | 8 | 52,350,557 |
| [batch-000002](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000002/payload/INDEX.json) | raw / original-formal | 2,000 | 153,182,206 | 8 | 33,728,329 |
| [batch-000003](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000003/payload/INDEX.json) | raw / original-formal | 2,000 | 235,064,253 | 8 | 56,153,743 |
| [batch-000004](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000004/payload/INDEX.json) | raw / original-formal | 2,000 | 206,156,663 | 8 | 48,781,531 |
| [batch-000005](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000005/payload/INDEX.json) | raw / original-formal | 2,000 | 203,939,267 | 8 | 47,745,250 |
| [batch-000006](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000006/payload/INDEX.json) | raw / original-formal | 2,000 | 151,279,366 | 8 | 33,480,606 |
| [batch-000007](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000007/payload/INDEX.json) | raw / original-formal | 2,000 | 170,978,671 | 8 | 40,059,888 |
| [batch-000008](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000008/payload/INDEX.json) | raw / original-formal | 2,000 | 230,900,200 | 8 | 54,803,338 |
| [batch-000009](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000009/payload/INDEX.json) | raw / original-formal | 2,000 | 190,913,250 | 8 | 44,482,497 |
| [batch-000010](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000010/payload/INDEX.json) | raw / original-formal | 2,000 | 354,671,476 | 8 | 81,091,795 |
| [batch-000011](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000011/payload/INDEX.json) | raw / original-formal | 2,000 | 382,543,839 | 8 | 88,454,419 |
| [batch-000012](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000012/payload/INDEX.json) | raw / original-formal | 2,000 | 45,434,594 | 8 | 9,374,405 |
| [batch-000013](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000013/payload/INDEX.json) | raw / original-formal | 2,000 | 2,703,757 | 8 | 536,257 |
| [batch-000014](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000014/payload/INDEX.json) | raw / original-formal | 2,000 | 2,654,370 | 8 | 533,322 |
| [batch-000015](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000015/payload/INDEX.json) | raw / original-formal | 2,000 | 2,717,576 | 8 | 536,993 |
| [batch-000016](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000016/payload/INDEX.json) | raw / original-formal | 2,000 | 2,619,533 | 8 | 537,716 |
| [batch-000017](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000017/payload/INDEX.json) | raw / original-formal | 2,000 | 2,687,992 | 8 | 541,651 |
| [batch-000018](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000018/payload/INDEX.json) | raw / original-formal | 2,000 | 2,633,691 | 8 | 533,034 |
| [batch-000019](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000019/payload/INDEX.json) | raw / original-formal | 2,000 | 2,702,590 | 8 | 530,159 |
| [batch-000020](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000020/payload/INDEX.json) | raw / original-formal | 2,000 | 2,712,874 | 8 | 541,854 |
| [batch-000021](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000021/payload/INDEX.json) | raw / original-formal | 2,000 | 2,640,315 | 8 | 538,922 |
| [batch-000022](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000022/payload/INDEX.json) | raw / original-formal | 2,000 | 2,780,613 | 8 | 548,017 |
| [batch-000023](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000023/payload/INDEX.json) | raw / original-formal | 2,000 | 2,574,699 | 8 | 518,117 |
| [batch-000024](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000024/payload/INDEX.json) | raw / original-formal | 2,000 | 2,695,038 | 8 | 536,234 |
| [batch-000025](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000025/payload/INDEX.json) | raw / original-formal | 2,000 | 2,646,737 | 8 | 537,980 |
| [batch-000026](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000026/payload/INDEX.json) | raw / original-formal | 2,000 | 2,623,149 | 8 | 538,183 |
| [batch-000027](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000027/payload/INDEX.json) | raw / original-formal | 2,000 | 2,669,048 | 8 | 539,239 |
| [batch-000028](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000028/payload/INDEX.json) | raw / original-formal | 2,000 | 2,706,791 | 8 | 539,264 |
| [batch-000029](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000029/payload/INDEX.json) | raw / original-formal | 2,000 | 2,695,475 | 8 | 526,497 |
| [batch-000030](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000030/payload/INDEX.json) | raw / original-formal | 2,000 | 2,680,738 | 8 | 537,630 |
| [batch-000031](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000031/payload/INDEX.json) | raw / original-formal | 2,000 | 2,676,437 | 8 | 533,256 |
| [batch-000032](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000032/payload/INDEX.json) | raw / original-formal | 2,000 | 2,654,229 | 8 | 539,895 |
| [batch-000033](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000033/payload/INDEX.json) | raw / original-formal | 2,000 | 2,656,468 | 8 | 541,191 |
| [batch-000034](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000034/payload/INDEX.json) | raw / original-formal | 2,000 | 54,379,815 | 8 | 13,138,681 |
| [batch-000035](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000035/payload/INDEX.json) | raw / original-formal | 2,000 | 458,118,616 | 8 | 103,720,750 |
| [batch-000036](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/batch-000036/payload/INDEX.json) | raw / original-formal | 520 | 120,783,034 | 3 | 28,318,123 |
| [controls](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/controls/payload/INDEX.json) | controls / original-formal | 1,114 | 224,903,100 | 5 | 25,653,889 |

## 怎么找到某个原件并重现

1. 在该模型 `source_index.json` 查原来源路径；去掉原 workspace 根后得到 workspace-relative 路径。
2. 从 collection 找 bundle INDEX，再查其 `indexes/part-*.json`（本索引JSON逐片列出链接）。member行的 `path`、`bytes`、`sha256` 就是完整原件身份，对应同片tar里的 `data/<path>`。
3. 用已发布恢复器保留相对布局恢复：输出为 `<新恢复根>/<bundle_id>/payload/<workspace-relative-path>`。原 OWNERSHIP_INDEX 和复制的member indexes可查归属；不直接运行 `source_index` 内的旧机器绝对路径。
4. 先按原 relocator 重定位来源索引，再以对应Python运行原AN2；分析代码的包内位置见JSON的 `analysis_code_inside_archives`。不重跑模型，不重新评分，不覆盖旧输出。

原恢复/重定位程序入口（整库clone会保留依赖的相对布局）：

- kimi-k3 [restore_collection.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/tools/publication/collection_restore_candidate_v2/restore_collection.py)
- glm-5.3 [restore_collection.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/tools/publication/collection_restore_candidate_v2/restore_collection.py)
- shared [relocate.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/relocate.py)

完整恢复会写出数万小文件；只需查看指标时直接下载上述CSV/JSON即可，不必先恢复raw。原工具与已发布分片是一套旧格式，不能把新的打包CLI直接当作旧collection恢复器。

## 证据与公开范围

本新索引只读固定Git树、collection/bundle/member/导出索引及小型说明。所有引用路径在同一提交存在、Git blob大小与既有清单一致；collection及member索引哈希和原件计数/字节和进行了元数据级自检。**556个tar的SHA来自原封存清单，本步骤没有重读或重新哈希tar/raw，也没有重新恢复或运行模型。**原件内容恢复/AN2十输出重现的验收证据见各模型最终 replay addendum，不能把导航生成误称为新一次全量内容验证。

GLM旧 `FULL_DELIVERY.zh.md` 和部分冻结导出/报告里的pending是当时状态，最终状态以各自 `REPLAY_VERIFIED.zh.md` 为准。公共controls有已记录的非实验回执未公开（GLM4,783 B；K3新controls1,292 B，外层另10,383 B），不是原实验成绩删选；私有引用链并非完全自包含。保留所有实验dump与科学分母不意味着可以下载密钥、权重或每一份私有审计文件。

复建本索引（只处理小元数据）：`python build_archive_index.py --repo /path/to/LLM_ExpGym-results --check`。没有递归复制审计链，也不把本索引自身纳入它所验证的旧提交。
