# 最终结果由哪些数据组成

[主报告](README.zh.md) · [实验沿革](EXPERIMENT_LOG.zh.md) · [逐设置来源 CSV](DATA_LINEAGE.csv) · [原始数据索引](ARCHIVE_INDEX.md)

最终使用六模型；Claude 仅保留在历史日志，不参加分数、排名或方向统计。Gemini 的 9 月 13 日快照经 9 月 14 日 23:45 UTC 核验，767 个完成项均未变化。

## 一眼看清最终构成

| 模型 | 原正式数据仍采用 | 9/12 重跑替换 | 最终完成 / 计划 |
|---|---:|---:|---:|
| Kimi K3 | 756 | 27 | 783 / 783 |
| GLM 5.3 | 717 | 66 | 783 / 783 |
| Qwen 3.8 | 783 | 0 | 783 / 783 |
| DeepSeek V4 Flash 0731 | 534 | 249 | 783 / 783 |
| GPT-5.6-sol Medium | 756 | 27 | 783 / 783 |
| Gemini 3.8 Flash Medium | 原始 76 + 恢复 691 | 0 | 767 / 783 |

计数是逻辑执行项（N1 单次运行或 N4 整池），不是独立样本数。Kimi/GLM 的原始 Audit 将三个顺序合在一次进程里，因此原 705 次物理 invocation 对应 783 个逻辑项；这里统一按逻辑项计。重跑是替换，不额外增加最终样本量。

## 哪些范围被重跑替换

下表均为 **N4 × naive/cached/poolact 三策略完整替换**；同一组的新结果无论升降均采用，其余范围仍用原结果。所有 N1 结果都没有参与 9/12 的定向重跑。

| 模型 | 场景 | 预算 | 替换池数 |
|---|---|---|---:|
| Kimi K3 | NAS101 | Tight | 27 |
| GLM 5.3 | Audit | Tight | 39 |
| GLM 5.3 | NAS101 | Tight | 27 |
| DeepSeek V4 Flash 0731 | Audit | Moderate | 39 |
| DeepSeek V4 Flash 0731 | Audit | Tight | 39 |
| DeepSeek V4 Flash 0731 | Search whois | Moderate | 117 |
| DeepSeek V4 Flash 0731 | NAS101 | Moderate | 27 |
| DeepSeek V4 Flash 0731 | NAS101 | Tight | 27 |
| GPT-5.6-sol Medium | NAS101 | Moderate | 27 |

选择这 9 组时参考过旧结果，因此是定向、探索性重跑，不是盲选实验。旧新之间含代码、提示及部署变化，不能把差值全部归因于某一个补丁。旧分数和失败记录没有删除。

## 来源与日期

以下均为 2026 年 UTC，显示到分钟；原始时间戳和计时依据见 CSV / JSON。

| 来源 ID | 实际运行 UTC | 代码版本 |
|---|---|---|
| `kimi_original` | 09-09 05:32 — 09-10 00:04 | `8dfea72931d9` |
| `glm_original` | 09-09 05:17 — 09-09 18:42 | `8dfea72931d9` |
| `qwen_original` | 09-10 23:51 — 09-11 13:24 | `21b4de99b2a0` |
| `deepseek_original` | 09-11 04:39 — 09-11 06:48 | `5aabf7f6b568` |
| `gpt_original` | 09-10 22:33 — 09-11 01:36 | `ccaf6adb8f7e` |
| `kimi_rerun_20260912` | 09-12 05:23 — 09-12 07:10 | `5bf5e5af817c` |
| `glm_rerun_20260912` | 09-12 05:42 — 09-12 10:20 | `5bf5e5af817c` |
| `deepseek_rerun_20260912` | 09-12 05:24 — 09-12 07:17 | `5bf5e5af817c` |
| `gpt_rerun_20260912` | 09-12 04:59 — 09-12 06:37 | `7f0fe09584a5` |
| `gemini_snapshot` | 09/11 起；最后完成 09/12 12:39；研究未关闭 | `de96fb644623` |

上表不同来源的时间依据可能是队列首/末事件或 API 请求观察窗，不能相减后混充纯 GPU 计算时长。完整时间依据、源码指纹、请求配置及原始目录保留在 [SOURCE_INDEX.json](SOURCE_INDEX.json)。

## 如何追到原件

1. 在 `absolute_settings.csv` 找到设置及 `cohort_id`。
2. 在 `DATA_LINEAGE.csv` / `SOURCE_SELECTION.csv` 查采用或被替换的来源；`source_row` 为去掉表头后的第几条数据记录，从 1 开始。
3. 从 `ARCHIVE_INDEX.md` 进入该来源的 member/shard 清单；Gemini 通过来源索引和固定槽位映射找到原始/恢复的具体 job、completion、trace 与 API dump。

失败、未启动及暂停项仍是 unknown；DeepSeek 的 11 个严格评分不完整项保留原严格缺失和单列 Gap0，不借用旧成功值。Gemini 未完成的 15 项不补零，也未用完成子集假冒完整 HPO 场景。
