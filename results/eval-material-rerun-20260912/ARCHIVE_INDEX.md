# 完整存档索引

[主报告](README.zh.md) · [详细报告](DETAILS.zh.md) · [机器索引](ARCHIVE_INDEX.json) · [恢复与重建](REBUILD.zh.md)

369 个科学池、1,476 个 agent；四模型独立使用原 `expgym.delivery.v1` 格式。以下只索引已有冻结包，不重新封包。最终安全扫描/远端发布状态以获批交付记录及固定提交为准，本索引生成不构成成功声明。

| 模型 | 科学池 / 物理尝试 | 原件 / raw 数 | 原字节 | 分片 | 完整原件映射 |
|---|---:|---:|---:|---:|---|
| gpt | 27 / 28 | 1881 / 1415 | 277169618 | 5 | [manifest](bundles/gpt/payload/manifest.json) · [全部尝试](bundles/gpt/physical_attempts.jsonl) · [有效映射](bundles/gpt/effective_mapping.json) · [模型说明](bundles/gpt/MODEL_INDEX.json) |
| kimi | 27 / 27 | 1117 / 469 | 37833013 | 1 | [manifest](bundles/kimi/payload/manifest.json) · [全部尝试](bundles/kimi/queue/terminal_export/all_attempts_index.json) · [有效映射](bundles/kimi/queue/terminal_export/execution_index.json) · [模型说明](bundles/kimi/MODEL_INDEX.json) |
| deepseek | 249 / 249 | 17928 / 11952 | 812414348 | 13 | [manifest](bundles/deepseek/payload/manifest.json) · [全部尝试](bundles/deepseek/queue/terminal_export/all_attempts_index.json) · [有效映射](bundles/deepseek/queue/terminal_export/execution_index.json) · [模型说明](bundles/deepseek/MODEL_INDEX.json) |
| glm | 66 / 66 | 2828 / 1244 | 350815985 | 6 | [manifest](bundles/glm/payload/manifest.json) · [全部尝试](bundles/glm/queue/terminal_export/all_attempts_index.json) · [有效映射](bundles/glm/queue/terminal_export/execution_index.json) · [模型说明](bundles/glm/MODEL_INDEX.json) |

每份 manifest 的 `files` 给出 member→shard、SHA256、bytes；机器索引绑定 manifest、全部分片和模型外层附件的身份，不复制第二份 raw 清单。GPT 原失败 job 及 12 个 ConnectionRefused 请求与 recovery 全部保留，科学槽不增多；任何正常空答、失败或未知分数不静默删除。

包内 `pending` / `not pushed` 与生成器 `INPUTS.independent_final_review=false` 保留其生成时或职责范围状态，不替代最终固定发布提交和 [独立复核](INDEPENDENT_REVIEW.zh.md)。此解释不消除 GPT 本地 commit 的远端可达性限制：公开重建入口仍是已公开 `0d3c299f0352ddd53bc012c787d3da81db529d89` 加 [exact patch](bundles/gpt/source_delivery/source-0d3c299-to-7f0fe09.patch) / [来源说明](bundles/gpt/source_delivery/source-provenance.json)，不声称本地 ccaf/7f commit 本身可被远端 fetch。

## 主问题、详细数据及复核

[设置级汇总](aggregate_metrics.csv) · [策略比较](contrasts.csv) · [全部逐池分数](pool_metrics.csv) · [状态/分母](pool_status.csv) · [任务汇总](by_item.csv) · [重复汇总](by_outerseed.csv) · [配对原表](paired_rows.csv) · [修前/修后](historical_comparison.csv)

[资源表](resources_by_setting.csv) · [全部尝试与成本账本](ALL_ATTEMPTS_INDEX.json) · [输入身份](INPUTS.json) · [分析检查](CHECKS.json) · [配置](settings.json)

[独立复核](INDEPENDENT_REVIEW.zh.md)

主报告不展开 question/task ID，详细 CSV 保留逐项原始分数、真实负效应、零值和 unknown。资源表声明各自范围，不能把并发 pool wall 之和当总历时。

## 重建与来源边界

四个原 master plans、必要 GPT recovery plan、oracle、四份历史 CSV、冻结执行/资源输入位于研究根；[spec.json](spec.json) 和 [REBUILD.zh.md](REBUILD.zh.md) 给出选择性恢复到 `restored-study/<model>` 及原聚合器重放命令。生成器/测试/原归档读取器在 `rebuild/`。私有凭据控制原件不公开，原 request/reply 不作投影；模型安全 metadata 的转换/遗漏已明确列出。

[旧五模型正式 cohort](https://github.com/tiannuo-yang/LLM_ExpGym/tree/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911) 固定于 `6c63f1c03c88683fa55be5cafcbb8122ac8fadaa`：Free/Moderate/Tight 和 ranking reshuffle 引用该版本，不声称本轮按新代码重跑全部预算。

[旧诊断归档](https://github.com/tiannuo-yang/LLM_ExpGym/tree/d2cd3089d1d34a19e9c03dd5d38a7fd01be608cc/results/eval-integrity-diagnostics-20260912) 固定于 `d2cd3089d1d34a19e9c03dd5d38a7fd01be608cc`，709 原件只引用，不重封、不重复下载。共享文件完整路径和身份见机器索引；索引本身由最终 shared 清单与发布提交绑定。
