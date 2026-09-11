# 五模型报告：原始 dump、聚合与恢复索引

本索引连接既有 Kimi / GLM / Qwen / DeepSeek 的公开存档与 GPT API 的本地完整封存。Claude 部分研究和共享 common 包单列，不进入五模型正式排名。原件数是文件数，不是实验样本数。

**公开范围不同：** 四模型原始包沿既有固定提交访问；GPT / Claude / common 的原始包只有本地完整性封存，未获公共扫描通过，也没有确认的公开 raw 链接。本次公开的报告及评分/配置快照另见 [正文](README.zh.md) 与 [INPUTS.json](INPUTS.json)，不能据此声称 API raw 已公开。

机器索引：[ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)。生成器：[build_archive_index.py](build_archive_index.py)；窄测试：[test_archive_index.py](test_archive_index.py)。

## 1. 已公开四模型：保留完整固定子索引

[四模型完整人读索引](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/a79cbc100804a1bc8d374e084a4b9999e3697a91/results/four-model-20260911/ARCHIVE_INDEX.md>) · [完整机器索引](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/a79cbc100804a1bc8d374e084a4b9999e3697a91/results/four-model-20260911/ARCHIVE_INDEX.json>) · [原四模型报告](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/a79cbc100804a1bc8d374e084a4b9999e3697a91/results/four-model-20260911/README.zh.md>)

子索引保留 raw → collection/bundle → member inventory → shard、全部分析/成本账本、恢复工具及复核入口；这里不重新复制几十万条原件映射。Kimi composite 的旧包只计一次；旧 bundle 与新 single-manifest collection 不是同一单位。

| 模型 | 原件数 | 原件 bytes | tar 分片 | 压缩 bytes | raw / 完整子索引 |
|---|---:|---:|---:|---:|---|
| Kimi-K3 | 66643 | 1751137861 | 268 | 305870108 | [raw 入口](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/INDEX.kimi-k3-composite-v1.json>) / [全部导航](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.md>) |
| GLM-5.3 | 71634 | 3467116893 | 288 | 772603212 | [raw 入口](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/INDEX.json>) / [全部导航](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.md>) |
| Qwen3.8-2.4T-A95B-FP8 | 31386 | 1437241763 | 24 | 235083685 | [raw 入口](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/sealed/manifest.json>) / [全部导航](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/ARCHIVE_INDEX.md>) |
| DeepSeek-V4-Flash-0731 | 26444 | 1384642088 | 22 | 237500959 | [raw 入口](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/sealed/manifest.json>) / [全部导航](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/ARCHIVE_INDEX.md>) |
| 既有四模型 tar 合计 | 196107 | 8040138605 | 602 | 1551057964 | 不含外层附件 / 本报告 |

上述大小、member/shard 身份及旧内容验证是固定子索引的继承声明；本次只读取并核验父索引 JSON 的 SHA，不重新下载或打开旧 tar。旧格式使用其匹配的恢复器；Qwen/DeepSeek 的任意目录 raw→分析重放限制仍按各自子索引，不由本 wrapper 解除。

## 2. API 本地三包：GPT、Claude、common 分列

本地 delivery：`/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910`。包内原件保留原仓库相对路径；全路径/大小/SHA/所属 tar 见下方控制索引。

| 包 | 范围 | 原件数 | 原件 bytes | 分片数 | 压缩 bytes | manifest（本地） |
|---|---|---:|---:|---:|---:|---|
| gpt | GPT 正式矩阵的原件、队列、分析及设置；合报第五模型，缺失端点依正文保留 unknown。 | 25818 | 2286906515 | 37 | 620463814 | [manifest](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/gpt/manifest.json>) |
| claude | Claude 未完成正式 PoolAct 研究；保留失败/未启动账本，仅登记存档，不进入五模型正式排名。 | 4886 | 128592791 | 3 | 21416999 | [manifest](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/claude/manifest.json>) |
| common | 共享源码、控制器、总报告及 GPT/Claude smoke；单列一次，不是额外正式模型或重复。 | 518 | 19850010 | 1 | 4143200 | [manifest](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/common/manifest.json>) |
| API 三包 tar 合计 | 非五模型正式样本数 | 31222 | 2435349316 | 41 | 646024013 | common 只计一次 |

GPT 包含正式矩阵；Claude 包保留未完成计划、失败和已保存结果；common 包含共享控制器、源码与报告，以及双方 smoke，不作为额外正式重复。原件同时包含队列、metadata、分析和轨迹，不能全部称为 HTTP 请求。

browse/ 的 101 份副本是重复物理文件，不是新结果。OUTER_FILES 的 152 件 / 835018357 bytes 已包含所有 tar、browse 与控制件（仅清单自身除外），不能再次加到 tar 总量上。

### 2.1 完整 member、shard 与控制索引

| 入口（均本地） | bytes | SHA256 |
|---|---:|---|
| [ARCHIVE_INDEX.md](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/ARCHIVE_INDEX.md>) | 4704 | `98fffebefdfe34fa1d1fc5850cd44d3e8a726c52fb196dd2c761b7c036d1d35a` |
| [ARCHIVE_INDEX.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/ARCHIVE_INDEX.json>) | 12051169 | `536c732b683c845a3fb378d01c092c872f9a0015a8a265e9b876eb683b53c483` |
| [MEMBERS.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/MEMBERS.csv>) | 8729123 | `5770fa1b2f97ac8c60cb9f6ffb6f4509f61a8f5332b56d09fbf77c512a4abaac` |
| [BROWSE_FILES.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/BROWSE_FILES.json>) | 37694 | `b4879356e3ca5af8ebf3759a5f811fd06215fbb85d10731869a450e7b310a500` |
| [STREAM_VERIFICATION.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/STREAM_VERIFICATION.json>) | 682 | `898eac23839a1c9b615f0441728ac2f75aeb45b1d3a7d0af5ec66ff876113597` |
| [archive-spec.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/archive-spec.json>) | 4902 | `8e386b3b8e9f926d251292fcdf716049efbb46e02ecbde77805cf9114dcbcc31` |
| [prepared-catalog.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/prepared-catalog.json>) | 18700925 | `144c0463e8df3f4a026a30b35d561ecf1540ea2250d8c74c984945a05ab7c7d3` |
| [OUTER_FILES.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/OUTER_FILES.json>) | 47368 | `c1998a5e45d2dcf6729e0381c2e37025b950b457a65876400322314d0e83f8e7` |

MEMBERS.csv / ARCHIVE_INDEX.json 保存逐原件与分片映射；各 manifest 同时列出所属包的全部原件及归档。prepared-catalog 是首次封存选择记录，本次生成器不读取或复制该大文件。所有 41 个 API shard 的本地路径、压缩大小和继承 SHA 也保存在本索引 JSON 的 `api_local_delivery.collections[].archives[]`。

### 2.2 GPT / Claude 全量分析、成本与终态入口

以下链接定位原仓库本地文件，不代表 GitHub 已公开；机器索引同时给出该文件所属 tar，完整恢复不依赖当前 raw 目录一直存在。`raw_terminals.csv` 是终态投影，不是 HTTP dump；`all_attempt_costs.csv` 包含全部已保存请求尝试，不能因未知用量而当作完整已知成本。

#### gpt：`gpt56sol_medium_refmatrix_20260910_v1`

[原 study 根目录](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1>)；[权威控制器终态](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/formal_controller_v1/gpt_waves/result.json>)。

| 文件 | bytes | SHA256 |
|---|---:|---|
| [INPUTS.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/INPUTS.json>) | 12322571 | `9a18b84fc7ed8a10ee5f19236d8499928eac536d0ceb6ec8dcaf36d521ec1112` |
| [README.zh.md](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/README.zh.md>) | 21576 | `135716a83d6193ca7ff5423e3e2dae856b28f4f2daa9604c25ada4a6622daa1f` |
| [VALIDATION.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/VALIDATION.json>) | 1967 | `83b2f8b03775b863ca829c85fc16d2d60666bd29cfaaa7d01be08e337159e687` |
| [absolute_settings.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/absolute_settings.csv>) | 32132 | `82c767b9ef91ab96666f55291afd268f4b9c8726dcf14d9d3388c11b08932be4` |
| [all_attempt_costs.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/all_attempt_costs.csv>) | 83559048 | `79810edff5b2c3687a0d8be27ca38f258ca69f9849c227198c502d56fbce36be` |
| [analyze_api_studies.py](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/analyze_api_studies.py>) | 63758 | `160a769e0ebf49ecd24c3f6fffeb3d0906593afcee9855d59a0968baa9ac8948` |
| [by_repeat.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/by_repeat.csv>) | 62985 | `e9d651a389bd49c4d045acc5c3bebf959725b648ea98bcad3ce56a5bcc38ad88` |
| [contrasts.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/contrasts.csv>) | 53076 | `0cc21c70930486556cc9aef2382332830a45db0ec7757dcff6b623dc88454088` |
| [metrics.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/metrics.csv>) | 719236 | `5d63a301b4fa50204a6fca669f41b4c25b31a282326dfd1723a9036ac070e8b0` |
| [normalized.jsonl](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/normalized.jsonl>) | 4315786 | `503705e0d3d00e9df7d86e99050bbb6783fbd4f99a12e80f26e0d414fe739cd1` |
| [raw_terminals.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/raw_terminals.csv>) | 2649368 | `6ace55412638db2686de5abb6fd9f8551de0d57b97f8aeb53a05f4f082204558` |
| [source_index.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/source_index.json>) | 16419526 | `caf92d448bacee3e29d0dc581cf92585c46fa3ac6155aeb52e3be26b9f691d9a` |

#### claude：`claude_fable5_high_poolact_refmatrix_20260910_v1`

[原 study 根目录](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1>)；[权威控制器终态](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/claude_continuation_20260911T0020_v1/claude_waves/result.json>)。

| 文件 | bytes | SHA256 |
|---|---:|---|
| [INPUTS.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/INPUTS.json>) | 2210095 | `e04ead2efa0f72b7568a8ed0abbb5553747e4d7eee3e918ed2e44885cfd8a435` |
| [README.zh.md](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/README.zh.md>) | 18758 | `e2fa6784d1503f8df3f8f12199020df375c7c5c249ad738aa296d17e744b0d80` |
| [VALIDATION.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/VALIDATION.json>) | 2020 | `2455db2d9328c94a9bbb5a1b57839ceee4816ef38d9ee9742178a10c905c9d83` |
| [absolute_settings.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/absolute_settings.csv>) | 20209 | `76291bc09c5759b7b5673195af60b0e3094e9357deaa6f1ba240adc278c4d9c5` |
| [all_attempt_costs.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/all_attempt_costs.csv>) | 4387740 | `7708814cb34cf018be94e6da40abca0f4936e88b43f71482b85d5c2922e94756` |
| [analyze_api_studies.py](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/analyze_api_studies.py>) | 63758 | `160a769e0ebf49ecd24c3f6fffeb3d0906593afcee9855d59a0968baa9ac8948` |
| [by_repeat.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/by_repeat.csv>) | 36524 | `9d5cf0dd716fc4c8551de651d0ce4ac739f812d5b1d47673bfa68f2c62503b37` |
| [contrasts.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/contrasts.csv>) | 29801 | `18849c1da0e83fd6082a8021502152172dd6899b31167861d84560b77d0d7ca5` |
| [metrics.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/metrics.csv>) | 410787 | `33eeb025cbd31a91cf619722f805cd8363201fa1472e9e75a0895e98a641727e` |
| [normalized.jsonl](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/normalized.jsonl>) | 1000922 | `31c0a3c956c5851922666cb4b10cd4dcbb475933884846e5d2d2a8ee6d2cbc9c` |
| [raw_terminals.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/raw_terminals.csv>) | 1008217 | `e745031d66bdbfa6d7af07b9387ec5a87d6a903705da334f6518452d822b188f` |
| [source_index.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/claude_fable5_high_poolact_refmatrix_20260910_v1/analysis_v1/source_index.json>) | 3081246 | `9b211b1f45e5f8e498f648de5277d96933709369e8fe81613364d0a7676ac8d2` |

### 2.3 common：原总报告、资源与独立复核

| 文件 | bytes | SHA256 |
|---|---:|---|
| [INDEPENDENT_REVIEW.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/INDEPENDENT_REVIEW.json>) | 14634 | `6b59b2cfd607abc8bbde7bf80e13bef5a4660ba7877dd2fc8963f13d15e621eb` |
| [INDEPENDENT_REVIEW.zh.md](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/INDEPENDENT_REVIEW.zh.md>) | 4566 | `66db3d038282f44070bb04beea14ce8dfeb5bc930ee8814eabc01c1033488436` |
| [INPUTS.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/INPUTS.json>) | 8124 | `66bebba0c5f31bd2a4f40d68ff4f86f9f3aeea2a3dc3bbea28254d801c3a5d4c` |
| [README.zh.md](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/README.zh.md>) | 33051 | `53fc04d18664019d4e4c0051d90d3419e0e903f76722f5e6b77380d4a0aeb2e8` |
| [VALIDATION.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/VALIDATION.json>) | 6497 | `b04c00500c3632ad6c309a30a593c4d89653423720388650e63fda6bb6fb0539` |
| [build_full_report.py](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/build_full_report.py>) | 41489 | `861a59f7c68ca6d05908a5ef39e1d1d8b33691c7c7c3d8f5a12201088967cd18` |
| [cross_model/INPUTS.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/cross_model/INPUTS.json>) | 801 | `49af20614960f82a5e21aa1e65951caf434dee2e027f5026c58792dfaa2527d4` |
| [cross_model/README.zh.md](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/cross_model/README.zh.md>) | 2605 | `05ebd36bcdaec03e48a562ecf344c90be0a110990e81cb7d00400d218c17b2a1` |
| [cross_model/analyze_api_studies.py](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/cross_model/analyze_api_studies.py>) | 63758 | `160a769e0ebf49ecd24c3f6fffeb3d0906593afcee9855d59a0968baa9ac8948` |
| [cross_model/cross_model_poolact.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/cross_model/cross_model_poolact.csv>) | 23888 | `6bba56d71937395185c4229fff58a19a3d8083da5e7b249ce629621bdcab4b8d` |
| [execution_timeline.json](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/execution_timeline.json>) | 6497 | `cb2c0e8f877ee5d835d6186bfc36440ff3dc82d16a96755d53244d0ea2f0c5d4` |
| [resources_by_setting.csv](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/resources_by_setting.csv>) | 19036 | `254ef1cdddbca8e7d2d4807257b198d413ce7e5c57ff474b9552d283f59ad811` |

这里的独立复核属于原 API 报告。五模型新稿复核由主报告另行记录，本索引生成器不冒称完成科学复核。

## 3. 按需恢复与公开边界

优先使用冻结聚合 CSV，无须为了更新报告恢复 raw。本地完整性校验命令示例（本次未执行）：

```bash
python /lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/scripts/package_run.py verify --manifest /lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/gpt/manifest.json --archive-dir /lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/gpt
```

若确需少量文件，追加 `--select <显式原仓库相对路径数组.json> --restore-dir <尚不存在的新目录>`。校验仍流式读取该包全部分片，只落地所选原件；恢复多个包时保留原仓库相对布局，避免覆盖已有目录。API 本地 manifest 未获 public scan，不能添加 `--require-public-scan` 伪装公开验证通过。

browse/ 只含选定副本，不是完整恢复树：原报告中的相对链接可能需要按原仓库布局选择性恢复。数据 payload、Python 环境及权重不在这些结果包内；没有在此验证任意路径下分析重放。

外部数据清单 `studies/api_20260910/common/data_inventory.json`：249 件 / 240303980 bytes，清单继承 SHA `0dcd364d3642ddd76dff4e492855fc8a60059a2cda6f243ec65fe742290b64b7`；payload_archived=false。

API public_scan=false 不能通过改 manifest 字段升级。将来若发布 raw，需执行真实首次公开安全流程；本次只由主作者扫描确切报告/输入快照增量，安全扫描结果不由本生成器产生。

## 4. 输入身份、生成与有限检查

生成器实际读取 5 份 JSON metadata，均绑定 bytes/SHA；未读 tar/member payload，未解包、重新评分、调用模型或读取凭据。子文件/分片身份仍为继承声明。

| 显式输入 | bytes | SHA256 |
|---|---:|---|
| [four_index](<https://github.com/tiannuo-yang/LLM_ExpGym/blob/a79cbc100804a1bc8d374e084a4b9999e3697a91/results/four-model-20260911/ARCHIVE_INDEX.json>) | 71685 | `1fafeba1a75537b4ad9507d94016ceb5c65d82584c557b38a92983a1670db7ca` |
| [api_index](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/ARCHIVE_INDEX.json>) | 12051169 | `536c732b683c845a3fb378d01c092c872f9a0015a8a265e9b876eb683b53c483` |
| [api_outer](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/OUTER_FILES.json>) | 47368 | `c1998a5e45d2dcf6729e0381c2e37025b950b457a65876400322314d0e83f8e7` |
| [api_verification](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/STREAM_VERIFICATION.json>) | 682 | `898eac23839a1c9b615f0441728ac2f75aeb45b1d3a7d0af5ec66ff876113597` |
| [api_spec](</lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/deliveries/api_studies_20260910/archive-spec.json>) | 4902 | `8e386b3b8e9f926d251292fcdf716049efbb46e02ecbde77805cf9114dcbcc31` |

原记录 CPython 3.11.15 下，从本目录执行：

```bash
python -B -m unittest test_archive_index.py -v
python -B build_archive_index.py --check
```

`--four-index` / `--api-dir` 可重定位同字节的 metadata 输入；输出中的原始来源路径保持不变。`--output-dir` 指定输出目录；`--check` 只比较现有输出字节，不创建或修改文件。fixtures 检查假数据的身份、计数、重复映射与公开边界，不是原始 payload 安全扫描或科学独立复核。
