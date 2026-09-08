# verified-resume 后的 Search 独立复核

在正式 full_v3 的全矩阵 verified-resume 完成后，使用同一只读 [review_search.py](../full_v3_search_independent_review/review_search.py) 从原数据重新复算，绑定新的 manifest 字节 SHA，不放宽旧版比较条件，也不覆盖 [此前复核](../full_v3_search_independent_review/README.zh.md)。

新复核通过：105 ExpGym traces、315 PoolAct strategy results、1,260 agents；范围仍仅为 Search，不替代全矩阵或 API dump 审计。与旧复核的 1,785 个原文件路径/SHA、420 条逐题结果、1,365 条 agent/trace、54 格指标及 gold/source 引用全部完全一致，详见 [绑定核对](resume_rebinding_verification.json)。

新 manifest SHA：`7016deb285696ff95c0aa970088c0580d0daf60cb0c6695ce8515e0fe85df854`。

完整精度见 [review.json](review.json)、[汇总 CSV](aggregate_metrics.csv)、[逐题 CSV](questions.csv)、[逐 agent CSV](agents.csv)。同一数值的可读表与方法边界见此前复核 README。

## 与正式 summary 的最终对账：通过

2026-09-07 11:57 UTC，使用 [加强后的比较器](../full_v3_search_independent_review/compare_summary.py) 对 [正式 summary](../full_v3_results_final/summary.json) 完成只读严格比较，退出码 0。证据为 [comparison.json](comparison.json)，`complete=true`、`strict_identity_and_coverage_checked=true`。

- 420 个 Search artifact 与 1,365 条 agent/trace：分数、原文件 SHA、job/system/question/item/regime/strategy、agent ID/parent、论文子集身份全部匹配。
- 54 个分组 F1/MV/MI 指标格、951 个逐题指标格：数值、完整来源路径集合和有效样本数全部匹配。
- 重新检查全部 1,785 个原文件 SHA，与独立复核时相同。全程未调用 API、搜索工具或重跑模型。

正式 summary SHA：`36e5badbd2b5e95a6042dead41703dc44146222260af05a29acc13e7ecf6e083`。此处证明最终 summary 的 Search 分区与独立原数据复算一致；其他分区及 API 完整性依赖其对应审计，不由本报告外推。

本次执行命令如下；如需再次运行应更换输出文件名，现有证据不覆盖：

```bash
LLM_ExpGym/.venv/bin/python \
  kimi_k3_eval/reports/full_v3_search_independent_review/compare_summary.py \
  --review kimi_k3_eval/reports/full_v3_search_independent_review_post_resume/review.json \
  --summary kimi_k3_eval/reports/full_v3_results_final/summary.json \
  --output kimi_k3_eval/reports/full_v3_search_independent_review_post_resume/comparison.json
```
