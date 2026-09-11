# deepseek-v4-flash-0731 完整存档索引

deepseek-v4-flash-0731 · `deepseek-flash-0731-full-20260911`。本索引只整理明确清单，不新增模型调用、评分或内容扫描。

固定数据提交：`41ec233f849aff05d8d91443118b6b2392d1cc40`；仓库内根目录：`results/deepseek-flash-0731-20260911`。本索引/后续报告可属于更晚提交，不能据此宣称它们已包含于该数据提交。

## 入口与范围

- [全局 manifest](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/manifest.json)：唯一逐原件映射；`files[]` 给出原相对路径、所属 shard、原字节和 SHA-256。索引不再复制逐原件长清单。
- [外层附件 inventory](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/archive_attachments.json)：数据提交中明确选择的外层 CSV/JSON/代码等；只下载 tar 不足以取得这些文件。
- 既有 [Kimi-K3 / GLM-5.3 报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md) / [旧研究存档索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.md) 独立保留，不重复计入本次 DeepSeek Flash 大小或文件数。

| 范围 | 文件/分片数 | 字节（B） |
| --- | ---: | ---: |
| tar.gz 分片 | 22 | 237500959（压缩文件） |
| tar 原件 members | 26444 | 1384642088（原件，不含 tar/gzip 结构开销） |
| 外层附件 | 51 | 54262771 |
| 其中：与 member 身份一致的外层副本 | 49 | 50419066（已包含于上一行） |
| metadata controls（manifest + 附件 inventory） | 2 | 8319056 |
| 已列物理文件合计（分片 + 外层 + controls） | 75 | 300082786 |

members 与外层副本去重后为 26446 个逻辑原件路径、1388485793 B；只按显式 `member_path` 身份绑定去重，不把相同内容的不同实验文件合并。上述大小不是 Git clone 大小，也不自动包含本索引、后续报告、权重、完整环境或外部数据集。

## tar 内路径分类

以下为互斥的路径用途分类，不是运行/评分成功率。完整路径与 hash 仍以全局 manifest 为准。

| 用途 | members | 原字节（B） | 路径/口径 |
| --- | ---: | ---: | --- |
| 正式 API 请求/回复 | 14300 | 656934510 | formal/invocations/*/api_dump/；包含已保存的全部尝试，不按答案/得分筛选。 |
| 正式 ExpGym 轨迹 | 1251 | 296832358 | formal/invocations/* 下 traces-v2 或 traces；终态可能内嵌于轨迹。 |
| 正式 Pool 结果/agent 与终态证据 | 1830 | 224754187 | result.json、agents/agent_*.json 或 terminal_evidence；Pool 文件也可含完整轨迹。 |
| 正式 invocation 其他原件 | 4860 | 113081284 | 其余已选择的 worker、配置、运行日志等；分类不判断运行成功。 |
| 正式调度元数据 | 3919 | 17796955 | formal/queue/；保留所有所选 session、completion、日志和 controller.lock。 |
| 任务 smoke 调度元数据 | 34 | 105049 | task_smoke01/queue/，与正式队列分开。 |
| 任务 smoke 原件 | 109 | 5003792 | task_smoke01/ 的任务 dump/结果/诊断；不混入正式指标/HTTP 成本分母。 |
| 原生协议 smoke | 40 | 115399 | native_smoke01/；用于协议诊断，不是正式实验结果。 |
| 实际服务诊断子目录 | 22 | 19071221 | serving/*/；仅按 manifest 中实际列出的一级目录分组，目录数量不等于启动次数，不从命名推断最终状态。 |
| 分析与全设置比较 | 14 | 43181044 | 逐 execution/item 指标、聚合/重复/比较、SOURCE_INDEX、INPUTS 和全部尝试成本；raw_terminals.csv 是终态投影，不是 HTTP dump。 |
| 研究/运行身份 | 65 | 7766289 | study/、runtime/ 的明确选件与 PLAN.zh.md；不等于复制权重、环境或数据集。 |

## 明确列入的服务诊断目录

从 manifest 实际 serving 一级子目录分组列出，不要求 launch 数字命名；目录数量不等于启动次数，不把取消原因、模型请求数或最终成功状态从目录名推断出来。真实状态和分配成本见对应诊断/资源账本附件。

| 诊断目录 | members | 原字节（B） | 所属分片 |
| --- | ---: | ---: | --- |
| serving/launch01 | 11 | 493375 | part-000022.tar.gz |
| serving/launch02 | 11 | 18577846 | part-000022.tar.gz |

## 分片下载

| 分片 | members | 原字节（B） | 压缩字节（B） | SHA-256（继承） |
| --- | ---: | ---: | ---: | --- |
| [part-000001.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000001.tar.gz) | 416 | 67082787 | 9293683 | `5850b58d42b03afa2d352b053fcc6286acb7413b8149086cf8c6cef66b95c614` |
| [part-000002.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000002.tar.gz) | 1061 | 67102857 | 11592489 | `2816b2474eecd800417799a1f16a8f438ab37076ddea8735aeef9caba97b8c72` |
| [part-000003.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000003.tar.gz) | 1335 | 67092185 | 11363343 | `a6a78bc5c13b2f89bcfdf91079b4218f74bc0290d48fcfb41408a29e85f97e39` |
| [part-000004.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000004.tar.gz) | 973 | 67027306 | 12164707 | `238769541e37cc3d206d66a02a40102f35a5a76cdabb5db2a0f655a59ddd5762` |
| [part-000005.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000005.tar.gz) | 1147 | 66098455 | 12610616 | `7195bd4fefd4c53f3246c4a16b5c3b23e11f66992724fdb0bf5b5a7eda80bfaa` |
| [part-000006.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000006.tar.gz) | 1115 | 67072298 | 11544305 | `0bb68e1b5aeac16c7b7e0bdde3388581b0cf1380b75a671a0c8e59f0454dca9c` |
| [part-000007.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000007.tar.gz) | 895 | 67088183 | 12466404 | `6ef17b4f88b8915869f62d40a8e24d071b0fa0d60811569415afe8f2971110fa` |
| [part-000008.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000008.tar.gz) | 1302 | 67061386 | 12054864 | `134405ff4026cc0cfb27a20dff201eae5ee3a7b27004f3dbf3dc581e28d5d045` |
| [part-000009.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000009.tar.gz) | 987 | 67103547 | 11254548 | `10c8ea69af07e7f838e595f83f18e045f97c4cc9c9db84ffad67c6929b94156e` |
| [part-000010.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000010.tar.gz) | 992 | 67090512 | 11117685 | `efb49158a7c374cfbc837df2bbed2549d4db4f7244778bafdf7f5aa68134186e` |
| [part-000011.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000011.tar.gz) | 1638 | 67051918 | 11138452 | `868d46b7e5ceccd4d69a577b6ba0d8bfa7785fe6fb6cdf93d1036ee75c758200` |
| [part-000012.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000012.tar.gz) | 1027 | 67012723 | 11877561 | `a5be2e0846a99fd6c269ab80b8695f41d8317f702a27f85d89bb223d715ec0db` |
| [part-000013.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000013.tar.gz) | 1291 | 67107671 | 10742014 | `9cd3a76388ad711a1cc85d9abb472a3e406b787a6e117edbc16ca367f2043a3b` |
| [part-000014.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000014.tar.gz) | 1152 | 67090037 | 12035724 | `fe8f474230b18e7d1f38f42f4cca7988689fca0b17c6cfffef7ade54e74f8392` |
| [part-000015.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000015.tar.gz) | 1152 | 67106801 | 10907142 | `1e54c6c49ecf99ea634b0c7ff00b8ee3fb38fbf5e81aa81a13900d2b32adf500` |
| [part-000016.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000016.tar.gz) | 1028 | 67091497 | 11945428 | `ecd90f5e55b2dc46005c5941f9d5bbbc722a7984722d6af90fe8143dfb221bfe` |
| [part-000017.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000017.tar.gz) | 920 | 67071373 | 11155538 | `05ccffda2f957668e2e5b014884f3743b7f5b0dc533ffdf4e15d6a286c3d57fe` |
| [part-000018.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000018.tar.gz) | 1574 | 67106724 | 11947527 | `0174a174317de188a99806eb6be63273772b03c4cbeba8248e88f517b62f1284` |
| [part-000019.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000019.tar.gz) | 1425 | 67094108 | 12285560 | `ab371781997692ab121d9c221ae3755aa07e36675a4fa43f298aa180a2fa0ca8` |
| [part-000020.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000020.tar.gz) | 1644 | 67108477 | 11848396 | `f6ecbd176dc99d964d467c18f0466ad9124619dd93dfc2df95e03853e05c0c10` |
| [part-000021.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000021.tar.gz) | 2000 | 5139268 | 1657671 | `088c51db33fb9c9c36da73840c1cf6617fc08a73c888c9f12a1f181f4bbfebd7` |
| [part-000022.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/part-000022.tar.gz) | 1370 | 38841975 | 4497302 | `df6c19cc9a089ce5010561d79424756a94433b30877aa750d7e405bf24263194` |

## 外层附件

这些链接只指向所给固定数据提交；生成器不访问 GitHub 来确认远端对象。`member_path` 表示 tar 中保留的同一原件副本，其大小/hash 已在两份 metadata 间比对。

| 文件 | 用途 | 字节（B） | tar member 副本 |
| --- | --- | ---: | --- |
| [PLAN.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/PLAN.zh.md) | 冻结研究/运行依据：PLAN.zh.md | 19199 | PLAN.zh.md |
| [analysis/full_v1/COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v1/COSTS.json) | 首次分析成本/身份（顶层reasoning漏读；推荐full_v2） | 1615 | analysis/full_v1/COSTS.json |
| [analysis/full_v1/INPUTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v1/INPUTS.json) | 首次分析成本/身份（顶层reasoning漏读；推荐full_v2） | 1021 | analysis/full_v1/INPUTS.json |
| [analysis/full_v1/SOURCE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v1/SOURCE_INDEX.json) | 首次分析成本/身份（顶层reasoning漏读；推荐full_v2） | 11265096 | analysis/full_v1/SOURCE_INDEX.json |
| [analysis/full_v2/COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/COSTS.json) | 正式分析：COSTS.json | 1645 | analysis/full_v2/COSTS.json |
| [analysis/full_v2/INPUTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/INPUTS.json) | 正式分析：INPUTS.json | 1021 | analysis/full_v2/INPUTS.json |
| [analysis/full_v2/SOURCE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/SOURCE_INDEX.json) | 正式分析：SOURCE_INDEX.json | 11265096 | analysis/full_v2/SOURCE_INDEX.json |
| [analysis/full_v2/absolute_settings.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/absolute_settings.csv) | 正式分析：absolute_settings.csv | 334497 | analysis/full_v2/absolute_settings.csv |
| [analysis/full_v2/all_attempt_costs.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/all_attempt_costs.csv) | 正式分析：all_attempt_costs.csv | 10574398 | analysis/full_v2/all_attempt_costs.csv |
| [analysis/full_v2/by_outerseed.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/by_outerseed.csv) | 正式分析：by_outerseed.csv | 717165 | analysis/full_v2/by_outerseed.csv |
| [analysis/full_v2/contrasts.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/contrasts.csv) | 正式分析：contrasts.csv | 394843 | analysis/full_v2/contrasts.csv |
| [analysis/full_v2/metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/metrics.csv) | 正式分析：metrics.csv | 3697141 | analysis/full_v2/metrics.csv |
| [analysis/full_v2/metrics_execution.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/metrics_execution.csv) | 正式分析：metrics_execution.csv | 2501197 | analysis/full_v2/metrics_execution.csv |
| [analysis/full_v2/normalized.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/normalized.csv) | 正式分析：normalized.csv | 333234 | analysis/full_v2/normalized.csv |
| [analysis/full_v2/raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/raw_terminals.csv) | 正式分析：raw_terminals.csv | 2093075 | analysis/full_v2/raw_terminals.csv |
| [runtime/BUILD.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/runtime/BUILD.md) | 冻结研究/运行依据：runtime/BUILD.md | 9855 | runtime/BUILD.md |
| [runtime/pyproject.toml](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/runtime/pyproject.toml) | 冻结研究/运行依据：runtime/pyproject.toml | 1209 | runtime/pyproject.toml |
| [runtime/runtime-env-isolated.sh](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/runtime/runtime-env-isolated.sh) | 冻结研究/运行依据：runtime/runtime-env-isolated.sh | 646 | runtime/runtime-env-isolated.sh |
| [runtime/runtime-env.sh](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/runtime/runtime-env.sh) | 冻结研究/运行依据：runtime/runtime-env.sh | 1524 | runtime/runtime-env.sh |
| [runtime/sglang-dsv4-official-0592695.patch](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/runtime/sglang-dsv4-official-0592695.patch) | 冻结研究/运行依据：runtime/sglang-dsv4-official-0592695.patch | 12839 | runtime/sglang-dsv4-official-0592695.patch |
| [runtime/uv.lock](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/runtime/uv.lock) | 冻结研究/运行依据：runtime/uv.lock | 204656 | runtime/uv.lock |
| [runtime/versions.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/runtime/versions.json) | 冻结研究/运行依据：runtime/versions.json | 19141 | runtime/versions.json |
| [serving/launch01/deployment.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/serving/launch01/deployment.json) | 冻结研究/运行依据：serving/launch01/deployment.json | 9400 | serving/launch01/deployment.json |
| [serving/launch01/plan.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/serving/launch01/plan.json) | 冻结研究/运行依据：serving/launch01/plan.json | 1631 | serving/launch01/plan.json |
| [serving/launch02/deployment.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/serving/launch02/deployment.json) | 冻结研究/运行依据：serving/launch02/deployment.json | 9436 | serving/launch02/deployment.json |
| [serving/launch02/plan.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/serving/launch02/plan.json) | 冻结研究/运行依据：serving/launch02/plan.json | 1640 | serving/launch02/plan.json |
| [study/allocation_final/ACCOUNTING.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/allocation_final/ACCOUNTING.json) | 冻结研究/运行依据：study/allocation_final/ACCOUNTING.json | 7497 | study/allocation_final/ACCOUNTING.json |
| [study/allocation_final/ACCOUNTING.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/allocation_final/ACCOUNTING.md) | 冻结研究/运行依据：study/allocation_final/ACCOUNTING.md | 1553 | study/allocation_final/ACCOUNTING.md |
| [study/analyze_deepseek.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/analyze_deepseek.py) | 冻结研究/运行依据：study/analyze_deepseek.py | 38569 | study/analyze_deepseek.py |
| [study/analyze_deepseek_metrics.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/analyze_deepseek_metrics.py) | 冻结研究/运行依据：study/analyze_deepseek_metrics.py | 15299 | study/analyze_deepseek_metrics.py |
| [study/analyze_deepseek_pre_usage_fallback.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/analyze_deepseek_pre_usage_fallback.py) | 冻结研究/运行依据：study/analyze_deepseek_pre_usage_fallback.py | 38251 | study/analyze_deepseek_pre_usage_fallback.py |
| [study/archive_files.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/archive_files.json) | 冻结研究/运行依据：study/archive_files.json | 3841019 | 无 |
| [study/build_archive_index.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/build_archive_index.py) | 冻结研究/运行依据：study/build_archive_index.py | 30035 | study/build_archive_index.py |
| [study/build_archive_list.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/build_archive_list.py) | 冻结研究/运行依据：study/build_archive_list.py | 17271 | study/build_archive_list.py |
| [study/build_report.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/build_report.py) | 冻结研究/运行依据：study/build_report.py | 54308 | study/build_report.py |
| [study/collect_allocation.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/collect_allocation.py) | 冻结研究/运行依据：study/collect_allocation.py | 16512 | study/collect_allocation.py |
| [study/data_inventory.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/data_inventory.json) | 冻结研究/运行依据：study/data_inventory.json | 53930 | study/data_inventory.json |
| [study/explicit_attachments.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/explicit_attachments.json) | 冻结研究/运行依据：study/explicit_attachments.json | 2686 | 无 |
| [study/formal_v1/RUN_INPUTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/RUN_INPUTS.json) | 冻结研究/运行依据：study/formal_v1/RUN_INPUTS.json | 17924 | study/formal_v1/RUN_INPUTS.json |
| [study/formal_v1/analysis_states.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/analysis_states.json) | 冻结研究/运行依据：study/formal_v1/analysis_states.json | 392 | study/formal_v1/analysis_states.json |
| [study/formal_v1/coverage.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/coverage.json) | 冻结研究/运行依据：study/formal_v1/coverage.json | 25832 | study/formal_v1/coverage.json |
| [study/formal_v1/matrix.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/matrix.json) | 冻结研究/运行依据：study/formal_v1/matrix.json | 60857 | study/formal_v1/matrix.json |
| [study/formal_v1/queue_plan.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/queue_plan.json) | 冻结研究/运行依据：study/formal_v1/queue_plan.json | 4018131 | study/formal_v1/queue_plan.json |
| [study/formal_v1/runtime_environment.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/runtime_environment.json) | 冻结研究/运行依据：study/formal_v1/runtime_environment.json | 1479 | study/formal_v1/runtime_environment.json |
| [study/model_profile.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/model_profile.json) | 冻结研究/运行依据：study/model_profile.json | 162 | study/model_profile.json |
| [study/native_contract_replay.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/native_contract_replay.json) | 冻结研究/运行依据：study/native_contract_replay.json | 55184 | study/native_contract_replay.json |
| [study/provenance/oracle3.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/provenance/oracle3.json) | 冻结研究/运行依据：study/provenance/oracle3.json | 28814 | study/provenance/oracle3.json |
| [study/provenance/reference_manifest.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/provenance/reference_manifest.json) | 冻结研究/运行依据：study/provenance/reference_manifest.json | 2363699 | study/provenance/reference_manifest.json |
| [study/replay_native_contract.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/replay_native_contract.py) | 冻结研究/运行依据：study/replay_native_contract.py | 29439 | study/replay_native_contract.py |
| [study/test_analyze_deepseek.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/test_analyze_deepseek.py) | 冻结研究/运行依据：study/test_analyze_deepseek.py | 31670 | study/test_analyze_deepseek.py |
| [study/test_build_report.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/test_build_report.py) | 冻结研究/运行依据：study/test_build_report.py | 40038 | study/test_build_report.py |

外层附件 SHA-256 见机器索引 `outer_attachments` 与原 inventory；它们是继承声明，不是本次对附件内容的重新哈希。

## 实际检查范围

本生成器仅实读并 SHA-256 校验两份输入 metadata；没有打开 tar/member 或外层附件 payload，没有重新读密钥、扫描、评分，也没有查询 Git/Slurm。运行是否完成、终态是否可评分及远端是否存在均不由本索引推断。

| 本次实读输入 | 字节（B） | SHA-256 |
| --- | ---: | --- |
| manifest | 8302237 | `b9166ac1d1395d39e072ab5f928fac26ab8a42c08beeb23e3e45cb426a4c8a58` |
| 外层 inventory | 16819 | `fb9e289f04b015c871589eab2d9a794f76b5c1eebfbc75872b356f76307e2324` |

manifest 原有声明为 `public_scan_passed=true`，scanner SHA 为 `aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116`，已知密钥来源数 4，advisory 数 0。这里只继承该声明；它不是新扫描或独立签名，也不自动放行外层/后续报告文件。

## 验证、选择性恢复与分析重放

使用冻结源码 `5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8` 中的 [scripts/package_run.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8/scripts/package_run.py) 与 [expgym/delivery.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8/expgym/delivery.py)；先核对下载提交/manifest 身份，再调用对应版本。

默认验证全部 shard 和全部 member，恢复 **0 个文件**：

```bash
python -B /absolute/frozen-source/scripts/package_run.py verify \
  --manifest /downloaded/release/sealed/manifest.json \
  --archive-dir /downloaded/release/sealed --require-public-scan
```

如果只需部分原件，以原 member 相对路径写非空 JSON 字符串数组作为选择清单；增加：

```bash
  --select /absolute/selected-member-paths.json \
  --restore-dir /absolute/fresh-selected-inputs
```

`--select` / `--restore-dir` 只决定写出哪些文件，仍校验全部分片与全部未选中成员。恢复目录必须事先不存在；失败可能留下不完整私有目录。只有 CLI exit 0 表示该次完整性验证完成，目录存在不等于成功；完整性不等于重新评分或科学真实性证明。外层附件不是 tar member，须另取并按其继承 pin 校验。

`--require-public-scan` 只检查可信 manifest 的原扫描声明，不重新读取密钥或扫描内容。未核对 manifest 的来源时，一个手写 true 不构成可信证据。

当前 `analyze_deepseek.py` 内部绑定绝对 state/artifact/authorization 路径，没有 `--relocate` 或 `--path-map`。任意新根可用于查看/验证 raw 与 CSV，不自动支持原样 raw→analysis 重放。原重放需要冻结的绝对布局、脚本/Python 身份和全部实际读取依赖（包括 controller.lock、session 元数据及所选授权记录），以及新的输出目录；不能假定只恢复几份 CSV 足够。需要逐字节重放时还应保留记录中的实际输入/脚本路径和解释器版本。

不推荐用 symlink 绕过布局：分析器拒绝 symlink 父目录。修改绑定路径会形成新的 input identity，不能宣称已经通过原身份的重放；本索引未尝试这种迁移。原始源码/数据/权重的身份记录不代表其实体已收入当前 tar。
