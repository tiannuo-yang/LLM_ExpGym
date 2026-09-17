# 原始 dump 与分析索引

[主报告](README.zh.md) · [最终数据构成](DATA_LINEAGE.zh.md) · [机器索引](ARCHIVE_INDEX.json)

本轮只生成六模型报告与实验沿革，没有重新打包或上传原始数据。公开链接固定到既有 commit；标注“本地”的路径不是 GitHub 下载地址。

| 数据来源 | raw / member / shard 入口 |
|---|---|
| `kimi_original` | [固定索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/INDEX.kimi-k3-composite-v1.json) |
| `glm_original` | [固定索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/INDEX.json) |
| `qwen_original` | [固定索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/manifest.json) |
| `deepseek_original` | [固定索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/manifest.json) |
| `gpt_original` | [本地 GPT 原始归档](/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/gpt/manifest.json)；恢复器与逐原件映射见机器索引 |
| `kimi_rerun_20260912` | [固定索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/b9483acbac11c0d3787618d8bdf1fc95c09ddcab/results/eval-material-rerun-20260912/bundles/kimi/MODEL_INDEX.json) |
| `glm_rerun_20260912` | [固定索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/b9483acbac11c0d3787618d8bdf1fc95c09ddcab/results/eval-material-rerun-20260912/bundles/glm/MODEL_INDEX.json) |
| `deepseek_rerun_20260912` | [固定索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/b9483acbac11c0d3787618d8bdf1fc95c09ddcab/results/eval-material-rerun-20260912/bundles/deepseek/MODEL_INDEX.json) |
| `gpt_rerun_20260912` | [固定索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/b9483acbac11c0d3787618d8bdf1fc95c09ddcab/results/eval-material-rerun-20260912/bundles/gpt/MODEL_INDEX.json) |
| `gemini_snapshot` | [本地 Gemini 完整来源](/lustrefs/users/chufan.shi/codex_space_tn/all_model_report_20260913/gemini_snapshot/data_v1/SOURCE_INDEX.json)；含原始与恢复 job 的实际路径 |

Gemini 当前完整 raw 仍在各 study 的 `invocations/<job>/api_dump/` 与 `result/`；已关闭归档仅覆盖原始中断段，不能把 recovery 快照说成完整封存。GPT 原始 raw 同样未公开；公开的 GPT 定向重跑包不等于全部原始 GPT raw 已公开。

## 本报告附件

- [全设置绝对值](absolute_settings.csv)、[全部比较](contrasts.csv)、[逐重复](by_repeat.csv)。
- [详细设置与结果](DETAILS.zh.md)、[家族排名](family_rankings.csv)、[排名变化](rank_transitions.csv)。
- [逐设置来源](DATA_LINEAGE.csv)、[采用/替换记录](SOURCE_SELECTION.csv)、[严格评分完整度](SCORE_COMPLETENESS.csv)。
- [历史批次日志](EXPERIMENT_LOG.zh.md)、[逐批次机器日志](EXPERIMENT_LOG.csv)。
- [资源口径与既有账本引用](resources.csv)：继承的设置均值、整池总量及不同来源账本不可直接相加；Gemini 尚无当前完整全尝试成本导出，未知不补零。

`ARCHIVE_INDEX.json` 保留原归档身份、member/shard 映射和恢复入口；本次没有重读 tar 或做新远端核验。重复引用旧归档不代表新数据。
