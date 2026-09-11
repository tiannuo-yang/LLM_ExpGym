# Qwen 完整存档索引

qwen3.8-2.4t-a95b-fp8 · `qwen38-formal-20260910`。本索引只整理明确清单，不新增模型调用、评分或内容扫描。

固定数据提交：`03dd6ef0ed9a63cb673a7b4e62a5a19026015225`；仓库内根目录：`results/qwen38-20260910`。本索引/后续报告可属于更晚提交，不能据此宣称它们已包含于该数据提交。

## 入口与范围

- [全局 manifest](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/manifest.json)：唯一逐原件映射；`files[]` 给出原相对路径、所属 shard、原字节和 SHA-256。索引不再复制逐原件长清单。
- [外层附件 inventory](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/archive_attachments.json)：数据提交中明确选择的外层 CSV/JSON/代码等；只下载 tar 不足以取得这些文件。
- 既有 [Kimi-K3 / GLM-5.3 报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md) / [旧研究存档索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.md) 独立保留，不重复计入本次 Qwen 大小或文件数。

| 范围 | 文件/分片数 | 字节（B） |
| --- | ---: | ---: |
| tar.gz 分片 | 24 | 235083685（压缩文件） |
| tar 原件 members | 31386 | 1437241763（原件，不含 tar/gzip 结构开销） |
| 外层附件 | 62 | 48229548 |
| 其中：与 member 身份一致的外层副本 | 61 | 43702154（已包含于上一行） |
| metadata controls（manifest + 附件 inventory） | 2 | 9837968 |
| 已列物理文件合计（分片 + 外层 + controls） | 88 | 293151201 |

members 与外层副本去重后为 31387 个逻辑原件路径、1441769157 B；只按显式 `member_path` 身份绑定去重，不把相同内容的不同实验文件合并。上述大小不是 Git clone 大小，也不自动包含本索引、后续报告、权重、完整环境或外部数据集。

## tar 内路径分类

以下为互斥的路径用途分类，不是运行/评分成功率。完整路径与 hash 仍以全局 manifest 为准。

| 用途 | members | 原字节（B） | 路径/口径 |
| --- | ---: | ---: | --- |
| 正式 API 请求/回复 | 18121 | 697504802 | formal/invocations/*/api_dump/；包含已保存的全部尝试，不按答案/得分筛选。 |
| 正式 ExpGym 轨迹 | 1251 | 232997352 | formal/invocations/* 下 traces-v2 或 traces；终态可能内嵌于轨迹。 |
| 正式 Pool 结果/agent 与终态证据 | 1830 | 211885585 | result.json、agents/agent_*.json 或 terminal_evidence；Pool 文件也可含完整轨迹。 |
| 正式 invocation 其他原件 | 4860 | 104356342 | 其余已选择的 worker、配置、运行日志等；分类不判断运行成功。 |
| 正式调度元数据 | 5085 | 20092442 | formal/queue/；保留所有所选 session、completion、日志和 controller.lock。 |
| 任务 smoke 调度元数据 | 34 | 104162 | task_smoke01/queue/，与正式队列分开。 |
| 任务 smoke 原件 | 112 | 3423618 | task_smoke01/ 的任务 dump/结果/诊断；不混入正式指标/HTTP 成本分母。 |
| 原生协议 smoke | 10 | 30835 | native_smoke01/；用于协议诊断，不是正式实验结果。 |
| 服务 launch01 诊断 | 15 | 352017 | serving/launch01/；保留所选原件，不从目录名推断最终状态。 |
| 服务 launch02 诊断 | 11 | 122805017 | serving/launch02/；保留所选原件，不从目录名推断最终状态。 |
| 分析与全设置比较 | 11 | 36723785 | 逐 execution/item 指标、聚合/重复/比较、SOURCE_INDEX、INPUTS 和全部尝试成本；raw_terminals.csv 是终态投影，不是 HTTP dump。 |
| 研究/运行身份 | 46 | 6965806 | study/、runtime/ 的明确选件与 PLAN.zh.md；不等于复制权重、环境或数据集。 |

## 分片下载

| 分片 | members | 原字节（B） | 压缩字节（B） | SHA-256（继承） |
| --- | ---: | ---: | ---: | --- |
| [part-000001.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000001.tar.gz) | 641 | 67108271 | 9380207 | `6cf5de038cc806e964b5f621cc67366c6f0a42b1ef271a824d70703e3424bdb0` |
| [part-000002.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000002.tar.gz) | 1203 | 67099363 | 12016568 | `764cbb142ed25e9d45e18ae44e99d6448ddb2270e12108daee80cfb77c376933` |
| [part-000003.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000003.tar.gz) | 1375 | 67105964 | 12640561 | `30e8bb14312ec7b87d6f5e042b3e29c83f832026cb08493f0dc0bbfa07ead79e` |
| [part-000004.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000004.tar.gz) | 1566 | 67097879 | 11050546 | `9e9d3793aa0904ecb7a83def4445bb7009f2b6650d0cc24e6cc5d751e2aea520` |
| [part-000005.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000005.tar.gz) | 1582 | 67090338 | 11659607 | `cce4714e1d757a0dfceef4acd140516a8b3dc999e9358d8e4a5fffd8233babbb` |
| [part-000006.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000006.tar.gz) | 1354 | 67065105 | 11775200 | `e84e7dcccb76a70592f262c53b1880cf0bb7f456cae198eba5431bfab571fca1` |
| [part-000007.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000007.tar.gz) | 1392 | 67053618 | 11994661 | `9f4472ef1d18091cf7d1577808999c0e8ca686eb455d560f552d870181e188d5` |
| [part-000008.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000008.tar.gz) | 1557 | 67059055 | 10711872 | `82bf2cfef9af58d5f06579c8c0b679b14b7c36984499947e15fb83cca8662ba9` |
| [part-000009.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000009.tar.gz) | 1621 | 65894392 | 11450435 | `47efb164e4359998d71f79b4926e86aa543fcd12433a98054c82328122a33675` |
| [part-000010.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000010.tar.gz) | 1300 | 67079607 | 12607733 | `2ddfd2a4eb7117163cdaa9a09388757503c90fcb5141fa4fba4ad963052f58ad` |
| [part-000011.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000011.tar.gz) | 1409 | 67086717 | 12054290 | `c8be6b1136faae4fb7a58ce0ba1e603574489d407f6ef1b70b3989fa5167a250` |
| [part-000012.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000012.tar.gz) | 1373 | 66148811 | 12136806 | `ab734f65e5d0716a7a52c23f175370baf43d7b29c7afe5770611ee6125f57db0` |
| [part-000013.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000013.tar.gz) | 1598 | 67100107 | 11896172 | `03e4262b0132003709de5fbc8b415798c3ffb000e48fe759345acd04fdd2d859` |
| [part-000014.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000014.tar.gz) | 1320 | 67093128 | 11269545 | `9450b9b5af60f6922a7eba1dc4d4ac8b5591364e4f431db4dfd4caa483289d0c` |
| [part-000015.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000015.tar.gz) | 1059 | 66976310 | 10771283 | `73600a816003b6c0471f6874506dbe1d231128d0892753615d5abe1608de1e62` |
| [part-000016.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000016.tar.gz) | 1370 | 65968977 | 11592552 | `f057be2cff8bd8b9feb5de21628eb0df81506d4a66513b7d634cc41199b220bd` |
| [part-000017.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000017.tar.gz) | 1290 | 67107513 | 11470754 | `e05d0554265e3b8e6352938bd534924d6b1ed8f8fbe8a83085da21a51fa15d2a` |
| [part-000018.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000018.tar.gz) | 1238 | 67052523 | 13080687 | `8003f834dfd793dc6b57bbcd18d3a24cdf93e6f3147c4d98f7122fbeb902dd23` |
| [part-000019.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000019.tar.gz) | 1509 | 67064070 | 10520610 | `b3ae48faa5c16080a81015ed1f2da1b263529008c2951125f7858b036a96b5c6` |
| [part-000020.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000020.tar.gz) | 2000 | 21008099 | 4051043 | `962526aa506125dcfc5d3af0fc7dff25e189b475b302e9f8bd2bc1522b66eb48` |
| [part-000021.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000021.tar.gz) | 2000 | 5339364 | 1634361 | `413843997c56080c724cc3244dfcb4d4b3dc3410f802d0ceac6e9cb8dc8dc7bb` |
| [part-000022.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000022.tar.gz) | 1437 | 38661967 | 3724917 | `6d41a20502a8d488dafe45100f5081f74bddedbfeab3659020d543a3cbc801b2` |
| [part-000023.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000023.tar.gz) | 2 | 60476033 | 3020146 | `202fba8f13add7343672b9698350b7c3261121f69d7ec6efe0e3b59e3ad4ce37` |
| [part-000024.tar.gz](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/part-000024.tar.gz) | 190 | 40504552 | 2573129 | `9764941e08b004231df39537a86733d18c62a7df92122c8187d928314a1857e4` |

## 外层附件

这些链接只指向所给固定数据提交；生成器不访问 GitHub 来确认远端对象。`member_path` 表示 tar 中保留的同一原件副本，其大小/hash 已在两份 metadata 间比对。

| 文件 | 用途 | 字节（B） | tar member 副本 |
| --- | --- | ---: | --- |
| [PLAN.zh.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/PLAN.zh.md) | 冻结运行身份或交付工具 | 22895 | PLAN.zh.md |
| [analysis/full_v1/COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/COSTS.json) | 冻结聚合输出 | 1641 | analysis/full_v1/COSTS.json |
| [analysis/full_v1/INPUTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/INPUTS.json) | 冻结聚合输出 | 1013 | analysis/full_v1/INPUTS.json |
| [analysis/full_v1/SOURCE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/SOURCE_INDEX.json) | 冻结聚合输出 | 12853098 | analysis/full_v1/SOURCE_INDEX.json |
| [analysis/full_v1/absolute_settings.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/absolute_settings.csv) | 冻结聚合输出 | 338728 | analysis/full_v1/absolute_settings.csv |
| [analysis/full_v1/all_attempt_costs.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/all_attempt_costs.csv) | 冻结聚合输出 | 14132013 | analysis/full_v1/all_attempt_costs.csv |
| [analysis/full_v1/by_outerseed.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/by_outerseed.csv) | 冻结聚合输出 | 728488 | analysis/full_v1/by_outerseed.csv |
| [analysis/full_v1/contrasts.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/contrasts.csv) | 冻结聚合输出 | 409667 | analysis/full_v1/contrasts.csv |
| [analysis/full_v1/metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/metrics.csv) | 冻结聚合输出 | 3694208 | analysis/full_v1/metrics.csv |
| [analysis/full_v1/metrics_execution.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/metrics_execution.csv) | 冻结聚合输出 | 2490316 | analysis/full_v1/metrics_execution.csv |
| [analysis/full_v1/normalized.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/normalized.csv) | 冻结聚合输出 | 319923 | analysis/full_v1/normalized.csv |
| [analysis/full_v1/raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/raw_terminals.csv) | 冻结聚合输出 | 1754690 | analysis/full_v1/raw_terminals.csv |
| [runtime/BUILD.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/runtime/BUILD.md) | 冻结运行身份或交付工具 | 7114 | runtime/BUILD.md |
| [runtime/pyproject.toml](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/runtime/pyproject.toml) | 冻结运行身份或交付工具 | 1201 | runtime/pyproject.toml |
| [runtime/runtime-env.sh](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/runtime/runtime-env.sh) | 冻结运行身份或交付工具 | 1342 | runtime/runtime-env.sh |
| [runtime/uv.lock](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/runtime/uv.lock) | 冻结运行身份或交付工具 | 204648 | runtime/uv.lock |
| [runtime/verify_cpu.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/runtime/verify_cpu.py) | 冻结运行身份或交付工具 | 4695 | runtime/verify_cpu.py |
| [runtime/versions.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/runtime/versions.json) | 冻结运行身份或交付工具 | 7213 | runtime/versions.json |
| [serving/launch01/plan.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/serving/launch01/plan.json) | 冻结运行身份或交付工具 | 1717 | serving/launch01/plan.json |
| [serving/launch02/deployment.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/serving/launch02/deployment.json) | 冻结运行身份或交付工具 | 8991 | serving/launch02/deployment.json |
| [serving/launch02/launcher_exit.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/serving/launch02/launcher_exit.json) | 冻结运行身份或交付工具 | 139 | serving/launch02/launcher_exit.json |
| [serving/launch02/plan.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/serving/launch02/plan.json) | 冻结运行身份或交付工具 | 1716 | serving/launch02/plan.json |
| [study/CPU_RUNTIME.md](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/CPU_RUNTIME.md) | 冻结运行身份或交付工具 | 6443 | study/CPU_RUNTIME.md |
| [study/RUN_INPUTS_launch02.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/RUN_INPUTS_launch02.json) | 冻结运行身份或交付工具 | 33532 | study/RUN_INPUTS_launch02.json |
| [study/accounting.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/accounting.json) | 冻结运行身份或交付工具 | 1402 | study/accounting.json |
| [study/admission_transition01.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/admission_transition01.json) | 冻结运行身份或交付工具 | 1346 | study/admission_transition01.json |
| [study/analyze_qwen.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/analyze_qwen.py) | 冻结运行身份或交付工具 | 38526 | study/analyze_qwen.py |
| [study/analyze_qwen_metrics.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/analyze_qwen_metrics.py) | 冻结运行身份或交付工具 | 15296 | study/analyze_qwen_metrics.py |
| [study/archive_files.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/archive_files.json) | 明确选件清单；其原件内容已由 sealed manifest 逐一固定 | 4527394 | 无 |
| [study/build_archive_index.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/build_archive_index.py) | 冻结运行身份或交付工具 | 28558 | study/build_archive_index.py |
| [study/build_archive_list.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/build_archive_list.py) | 冻结运行身份或交付工具 | 16336 | study/build_archive_list.py |
| [study/build_matrix.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/build_matrix.py) | 冻结运行身份或交付工具 | 23484 | study/build_matrix.py |
| [study/build_report.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/build_report.py) | 冻结运行身份或交付工具 | 53408 | study/build_report.py |
| [study/cpu_runtime.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/cpu_runtime.py) | 冻结运行身份或交付工具 | 7041 | study/cpu_runtime.py |
| [study/data_inventory.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/data_inventory.json) | 冻结运行身份或交付工具 | 53922 | study/data_inventory.json |
| [study/explicit_attachments.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/explicit_attachments.json) | 冻结运行身份或交付工具 | 1413 | study/explicit_attachments.json |
| [study/formal_analysis_states.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_analysis_states.json) | 冻结运行身份或交付工具 | 415 | study/formal_analysis_states.json |
| [study/formal_cache_salt/coverage.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_cache_salt/coverage.json) | 冻结运行身份或交付工具 | 24867 | study/formal_cache_salt/coverage.json |
| [study/formal_cache_salt/matrix.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_cache_salt/matrix.json) | 冻结运行身份或交付工具 | 56805 | study/formal_cache_salt/matrix.json |
| [study/formal_cache_salt/runtime_environment.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_cache_salt/runtime_environment.json) | 冻结运行身份或交付工具 | 1431 | study/formal_cache_salt/runtime_environment.json |
| [study/formal_plan_cache_salt.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_plan_cache_salt.json) | 冻结运行身份或交付工具 | 3770744 | study/formal_plan_cache_salt.json |
| [study/freeze_inputs.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/freeze_inputs.py) | 冻结运行身份或交付工具 | 4952 | study/freeze_inputs.py |
| [study/native_smoke.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/native_smoke.py) | 冻结运行身份或交付工具 | 7977 | study/native_smoke.py |
| [study/prepare_data.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/prepare_data.py) | 冻结运行身份或交付工具 | 5516 | study/prepare_data.py |
| [study/prepare_task_smoke.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/prepare_task_smoke.py) | 冻结运行身份或交付工具 | 3037 | study/prepare_task_smoke.py |
| [study/probe_cpu_loaders.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/probe_cpu_loaders.py) | 冻结运行身份或交付工具 | 5440 | study/probe_cpu_loaders.py |
| [study/python_hpo](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/python_hpo) | 冻结运行身份或交付工具 | 240 | study/python_hpo |
| [study/python_main](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/python_main) | 冻结运行身份或交付工具 | 235 | study/python_main |
| [study/reference_matrix_manifest.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/reference_matrix_manifest.json) | 冻结运行身份或交付工具 | 2363699 | study/reference_matrix_manifest.json |
| [study/reference_oracle3.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/reference_oracle3.json) | 冻结运行身份或交付工具 | 28814 | study/reference_oracle3.json |
| [study/task_smoke_analysis_states.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/task_smoke_analysis_states.json) | 冻结运行身份或交付工具 | 382 | study/task_smoke_analysis_states.json |
| [study/task_smoke_matrix_cache_salt.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/task_smoke_matrix_cache_salt.json) | 冻结运行身份或交付工具 | 7071 | study/task_smoke_matrix_cache_salt.json |
| [study/task_smoke_plan_cache_salt.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/task_smoke_plan_cache_salt.json) | 冻结运行身份或交付工具 | 28837 | study/task_smoke_plan_cache_salt.json |
| [study/test_analyze_qwen.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/test_analyze_qwen.py) | 冻结运行身份或交付工具 | 28542 | study/test_analyze_qwen.py |
| [study/test_build_archive_index.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/test_build_archive_index.py) | 冻结运行身份或交付工具 | 14655 | study/test_build_archive_index.py |
| [study/test_build_archive_list.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/test_build_archive_list.py) | 冻结运行身份或交付工具 | 14453 | study/test_build_archive_list.py |
| [study/test_build_matrix.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/test_build_matrix.py) | 冻结运行身份或交付工具 | 9690 | study/test_build_matrix.py |
| [study/test_build_report.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/test_build_report.py) | 冻结运行身份或交付工具 | 40703 | study/test_build_report.py |
| [study/test_cpu_runtime.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/test_cpu_runtime.py) | 冻结运行身份或交付工具 | 6932 | study/test_cpu_runtime.py |
| [study/validation/cpu_hpo.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/validation/cpu_hpo.json) | 冻结运行身份或交付工具 | 1798 | study/validation/cpu_hpo.json |
| [study/validation/cpu_main.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/validation/cpu_main.json) | 冻结运行身份或交付工具 | 3924 | study/validation/cpu_main.json |
| [study/warm_pp_pages.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/warm_pp_pages.py) | 冻结运行身份或交付工具 | 4832 | study/warm_pp_pages.py |

外层附件 SHA-256 见机器索引 `outer_attachments` 与原 inventory；它们是继承声明，不是本次对附件内容的重新哈希。

## 实际检查范围

本生成器仅实读并 SHA-256 校验两份输入 metadata；没有打开 tar/member 或外层附件 payload，没有重新读密钥、扫描、评分，也没有查询 Git/Slurm。运行是否完成、终态是否可评分及远端是否存在均不由本索引推断。

| 本次实读输入 | 字节（B） | SHA-256 |
| --- | ---: | --- |
| manifest | 9818983 | `f3971da5944ac9b0eb8e81f7a2325af2c113cacb4dcc553928b05a05231099d7` |
| 外层 inventory | 18985 | `b498ec30406223d8983289f8e1f8c72b5602d5750d0279161afdf4f8b3d3977a` |

manifest 原有声明为 `public_scan_passed=true`，scanner SHA 为 `aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116`，已知密钥来源数 4，advisory 数 0。这里只继承该声明；它不是新扫描或独立签名，也不自动放行外层/后续报告文件。

最终索引生成器见 [同一报告提交的 build_archive_index.py](../study/build_archive_index.py)。数据提交和 tar 内工具是封存时的历史版本；成稿复核后的文案修订版本随本报告提交，不应混淆。此修订没有改动原件、分析值或 archive identity。

## 验证、选择性恢复与分析重放

使用冻结源码 `21b4de99b2a014874e3cec1595eaa40762b0c564` 中的 [scripts/package_run.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/21b4de99b2a014874e3cec1595eaa40762b0c564/scripts/package_run.py) 与 [expgym/delivery.py](https://github.com/tiannuo-yang/LLM_ExpGym/blob/21b4de99b2a014874e3cec1595eaa40762b0c564/expgym/delivery.py)；先核对下载提交/manifest 身份，再调用对应版本。

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

`--select` / `--restore-dir` 只决定写出哪些文件，仍校验全部分片与全部未选中成员。恢复目录必须事先不存在；失败可能留下不完整私有目录。只有 CLI exit 0 表示该次完整性验证完成，目录存在不等于成功；完整性不等于重新评分或科学真实性证明。外层附件作为独立文件分发；有 member_path 身份绑定的副本也存在于 tar 中，无副本的附件须另取并按其继承 pin 校验。

`--require-public-scan` 只检查可信 manifest 的原扫描声明，不重新读取密钥或扫描内容。未核对 manifest 的来源时，一个手写 true 不构成可信证据。

当前 `analyze_qwen.py` 内部绑定绝对 state/artifact/authorization 路径，没有 `--relocate` 或 `--path-map`。任意新根可用于查看/验证 raw 与 CSV，不自动支持原样 raw→analysis 重放。原重放需要冻结的绝对布局、脚本/Python 身份和全部实际读取依赖（包括 controller.lock、session 元数据及所选授权记录），以及新的输出目录；不能假定只恢复几份 CSV 足够。需要逐字节重放时还应保留记录中的实际输入/脚本路径和解释器版本。

不推荐用 symlink 绕过布局：分析器拒绝 symlink 父目录。修改绑定路径会形成新的 input identity，不能宣称已经通过原身份的重放；本索引未尝试这种迁移。原始源码/数据/权重的身份记录不代表其实体已收入当前 tar。
