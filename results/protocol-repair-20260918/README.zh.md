# 主报告阶段数据：既有轨迹全量重评分

[当前主报告](../paper-analysis-20260916/README.zh.md)已更新已完成的终答/投票重评分与 486 条 HPO 行为分析。当前评分身份为 `existing-trace-rescore-v1`，评分代码提交 `0e6c51b6d86f42437038518c2fc8adc510901c0b`。

本阶段使用原 4,698 个主实验槽位的完整重评分，不混入仍在执行或验收的 HPO 补跑。`main/SCORE_VERSIONS.json` 的 `candidate` 表示尚未完成整个统一运行版本的最终封版，并不表示报告仍使用旧解析分数。97 个注册 HPO N4 补跑池验收后，才会替换对应旧运行。

| 材料 | 入口 |
| --- | --- |
| 完整主成绩 | [COMPARISON.csv](main/COMPARISON.csv)、[逐槽标量](main/slot_scalars.csv) |
| 旧/新/诊断身份 | [SCORE_VERSIONS.json](main/SCORE_VERSIONS.json) |
| 原件与来源 SHA | [SOURCE_SELECTION.csv](main/SOURCE_SELECTION.csv)、[输入身份](main/INPUTS.json) |
| 全量新旧分数与变化原因 | [sample_diff.csv](rescore/main/sample_diff.csv) |
| HPO 486 行为及原始终止原因 | [行为说明](hpo_behavior/README.zh.md) |
| Audit 证据、配对和投票 | [Audit 说明](audit/README.zh.md) |
| 结论变化 | [conclusion_delta.csv](conclusion_delta.csv) |
| 本次报告核对 | [REVIEW.zh.md](../paper-analysis-20260916/REVIEW.zh.md) |

本轮必要 HPO 对照为 97 个四成员池：63 个旧图版本池、31 个 Gemini 同提供方基线和 3 个终答控制流改变的池。按模型为 Gemini 49、GPT 9、GLM 10、Kimi 9、Qwen 19、DeepSeek 1。486 条 HPO 单智能体不受共享图碰撞影响；其行为统计和成绩无需等待这些多智能体对照即可更新。

`main/historical/` 与主报告的 `*.pre-repair-297c3d0.*` 保留更新前结果；旧数据文件未反写。`SOURCE_RENDER_CHECKS.json` 只校验原生成稿的输入，当前编辑稿的检查另见主报告 `interim-update-20260918/CHECKS.json`。本次发布包含阶段报告及其已完成的重评分和行为数据，不代表 HPO 统一运行版本的最终公平对照已验收。
