# Gemini 主报告更新审核（2026-09-18）

结论：本次将已发布的 16 项 Gemini 补齐结果合入原主报告路径，数值与文档独立核对通过。没有新增模型调用、重跑任务评分器或采用另行代码审查的诊断分数。

## 更新范围

- 当前主实验为 4,698/4,698 项执行完成、4,687 项严格评分完整，Gemini 为 783/783。保留全部 4,682 项历史采用结果，只补 N1 HPO 六项、N4 HPO 九项、N4 Search Moderate naive 一项。
- 正文、附件、英文摘要同步更新完整六模型排名、部署 regret、PoolAct 比较及宏均值；新表使用同一候选模型集合。
- N1 HPO 当前成绩覆盖 486 项；原行为分析仍明确采用冻结的 480 条轨迹。Search/Audit 历史行为表及所有旧 CSV 保持原字节。
- Gemini 的历史 Sub2 与新增 OpenRouter 来源分别标明，不解释为单一提供方的完整重跑。

## 已完成核验

| 项目 | 核验范围与结果 |
| --- | --- |
| 独立聚合 | 不导入原聚合器，从公开 4,698 项逐项标量重建 3,894 行绝对值，数值及缺失状态一致 |
| 原公开表回放 | 7,767 聚合行、126 排名、1,298 比较行通过 |
| 新派生 CSV | 七张表、244 行全部独立核对；八份生成的 CSV/检查文件可逐字节复算 |
| 正文显示 | 三份文档全部修改逐段核查，五张显示表的 205 个数值位置核对通过 |
| 文档身份 | 被复核的正文、附件、摘要和新 CSV 的 SHA256 已记录 |

[机器检查与文档身份](gemini-update-20260918/REVIEW_CHECKS.json) · [派生表输入与计算检查](gemini-update-20260918/CHECKS.json) · [复算脚本](gemini-update-20260918/recompute.py) · [补齐逐项来源](../gemini-openrouter-20260917/main/SOURCE_SELECTION.csv)。

本审核是“采用结果到报告”的数值审核，不等于底层评测协议没有问题。另行代码审查已发现答案提取及投票接受规则的问题；本次沿用历史评分，未混入诊断重评分，也未再次全读私有原始 API dump。历史行为分析继续沿用其原审核范围。

## 原版本留档

被更新的五份原文按原字节另存为 [README.ad03.zh.md](README.ad03.zh.md)、[APPENDIX.ad03.zh.md](APPENDIX.ad03.zh.md)、[ABSTRACT.ad03.en.md](ABSTRACT.ad03.en.md)、[MANIFEST.ad03.json](MANIFEST.ad03.json)、[REVIEW.ad03.zh.md](REVIEW.ad03.zh.md)。原 `review_checks.json` 仅对应历史版本。当前文件身份见 [MANIFEST.json](MANIFEST.json)，全仓身份及冻结归档映射由根目录轻量清单验证。

`ad03e8c` 的 GitHub 固定提交链接继续指向历史报告；更新版位于 main 的相同报告路径。
