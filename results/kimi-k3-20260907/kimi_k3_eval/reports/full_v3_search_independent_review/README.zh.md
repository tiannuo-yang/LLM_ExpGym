# full_v3 Search 分区独立复核

Custom study，仅复核 Kimi-K3 本轮 Search 分区；**不代表 full 矩阵、原始 API dump 或模型协议行为已经全部验收**。最终总 summary 尚未提供，对比状态为待完成。

已检查全部 210 个完成的 Search jobs：105 条 ExpGym traces、315 个 PoolAct strategy results、1,260 份 PoolAct agent 文件，以及 105 个 PoolAct item summaries。35 题按固定 QA parquet 的原筛选/稳定排序复查为 18 whois 与 17 whatis，三种 regime 与三种策略无遗漏。

所有逐 agent 分数、原保存 score_check、独立 agent 与 embedded 副本、策略 aggregate 原始答案/分数/个体数组均一致。ExpGym schema/validation、任务与源码标识通过；PoolAct 图 pending_claims 均为零。已保存原文件 SHA，未改任何源码、数据或正式产物。

## 独立性边界

直接读取 manifest 指定原文件及固定 QA parquet gold，没有从 audit_results 或 summarize_results 取数。复用仓库 `_extract_answer`、`_name_f1`、name extraction、vote-key normalization 与 schema validator，因此不是完全独立重写 scorer。另以集合公式 `2|P∩G|/(|P|+|G|)` 核对 F1；空集合行为按原实现。

MV 在本脚本独立实现：对完整规范化答案集合取众数；票数并列时非空集合优先，再选 agent ID 顺序中首个。用首个获胜 agent 的原始 answer 复算 F1，不把规范化 key 重新拼接后评分，也不是逐实体投票或 best-of-N。独立 vote 同时与原 aggregate_results 对照。315 个策略结果中 145 个有最高票平局。

MI 为每题四个 agent 的复算 F1 均值，再对 whois 18 题或 whatis 17 题等权宏平均。论文 Search 主表只含 Moderate/Tight 的 whois；下表其余部分属于仓库扩展。论文规定宏平均与 MV/MI，具体 tie/文本规范化细节来自当前仓库而非论文额外承诺。

## ExpGym F1（%）

| Regime | whois（18 题） | whatis（17 题） |
|---|---:|---:|
| Free | 27.942 | 10.588 |
| Moderate | 30.644 | 5.882 |
| Tight | 11.220 | 0.000 |

## PoolAct（%，MV / MI）

| Regime | Strategy | whois MV | whois MI | whatis MV | whatis MI |
|---|---|---:|---:|---:|---:|
| Free | naive | 33.704 | 24.801 | 0.000 | 0.908 |
| Free | cached | 32.000 | 30.930 | 8.824 | 4.412 |
| Free | poolact | 36.790 | 31.644 | 5.882 | 4.585 |
| Moderate | naive | 31.259 | 25.528 | 0.000 | 2.206 |
| Moderate | cached | 28.164 | 31.676 | 0.000 | 2.941 |
| Moderate | poolact | 29.877 | 29.042 | 0.000 | 1.471 |
| Tight | naive | 25.454 | 17.111 | 2.941 | 1.471 |
| Tight | cached | 17.037 | 13.922 | 0.000 | 0.735 |
| Tight | poolact | 22.593 | 19.840 | 2.941 | 3.114 |

完整精度、逐题和逐 agent 证据见 [review.json](review.json)、[aggregate_metrics.csv](aggregate_metrics.csv)、[questions.csv](questions.csv)、[agents.csv](agents.csv)。源代码、QA parquet、manifest 与每个原文件 SHA 均在 review.json；progress 为运行中观测快照，不是 full 完成凭证。

## 后续与正式 summary 对比

以下命令只读并产生新的比较文件，不会调用 API。它要求最终 summary 为 passed/full 且 manifest SHA、模型身份相同；重新确认原文件 SHA，再逐条比对 420 个 artifact、1,365 条 agent/trace、54 个分组指标格和 951 个逐题指标格（含论文子集的重复视图）。

```bash
LLM_ExpGym/.venv/bin/python \
  kimi_k3_eval/reports/full_v3_search_independent_review/compare_summary.py \
  --review kimi_k3_eval/reports/full_v3_search_independent_review/review.json \
  --summary /absolute/path/to/final/summary.json \
  --output kimi_k3_eval/reports/full_v3_search_independent_review/final_summary_comparison.json
```

请使用上述加强后的 compare_summary.py 入口；review_search.py 与原 review.json 保持生成时哈希不变。除分数外，对比还严格核验每行 system/question/item/regime/strategy/job、agent_id/parent_result_path、分组完整来源集合及逐题/分组有效样本数。

边界测试包含原始获胜文本与 vote key 的差异、空集合、六词过滤、平票处理，以及合成 summary 的来源/逐 agent/分组/逐题分数和身份、样本数篡改拒绝。合成 summary 仅用于接口测试，不等于已经与正式 summary 对比。
