# ad03e8c 最终报告：轻量数据入口

本目录对应指定的 `ad03e8c42ca501016176ee1bc407b38499178506` 报告。正文、分析附件和来源选择固定于该版本；此次只整理发布布局，没有重跑实验或重评分。

2026-09-18 主分支的[主报告原路径](../paper-analysis-20260916/README.zh.md)已合入 Gemini 的 16 个补齐结果。**本目录仍是 ad03 冻结数据**；当前完整的 4,698 项数据与采用关系见[Gemini 补齐数据入口](../gemini-openrouter-20260917/main/README.zh.md)。原报告五份被更新文档的原字节另存同目录 `*.ad03.*`，冻结清单保留原提交身份。

## 报告、CSV 与来源

| 需要什么 | 当前入口 | 内容 |
| --- | --- | --- |
| 冻结报告 | [中文正文](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ad03e8c42ca501016176ee1bc407b38499178506/results/paper-analysis-20260916/README.zh.md)、[数据与方法附件](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ad03e8c42ca501016176ee1bc407b38499178506/results/paper-analysis-20260916/APPENDIX.zh.md) | 指定版本原文，全部 70 件原文件字节保留，更新文档以 `.ad03` 文件归档 |
| 简明比较 | [MAIN_COMPARISON.csv](csv/MAIN_COMPARISON.csv) | 72 行主比较：N1 三预算、N4 同预算三策略 |
| 完整比较 | [COMPARISON.csv](csv/COMPARISON.csv) | 1,298 行，保留任务/家族、次指标、差值与缺失 |
| 分开查看实验臂 | [N1_BUDGET_COMPARISON.csv](csv/N1_BUDGET_COMPARISON.csv)、[N4_STRATEGY_COMPARISON.csv](csv/N4_STRATEGY_COMPARISON.csv) | 单智能体预算比较与四智能体策略比较 |
| 冻结原始聚合表 | [absolute_settings.csv](../six-models-lineage-20260914/absolute_settings.csv)、[by_repeat.csv](../six-models-lineage-20260914/by_repeat.csv)、[contrasts.csv](../six-models-lineage-20260914/contrasts.csv) | 完整设置、重复层结果及原报告差值 |
| 冻结行为分析与案例 | [冻结分析附件](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ad03e8c42ca501016176ee1bc407b38499178506/results/paper-analysis-20260916/APPENDIX.zh.md)、[案例索引](../paper-analysis-20260916/cases/CASE_INDEX.zh.md) | ad03 排名、Search/HPO/Audit trajectory 指标、PoolAct 协调行为和案例数据 |
| 每项采用来源 | [selected_slots.csv](index/selected_slots.csv)、[SOURCE_SELECTION.csv](../six-models-lineage-20260914/SOURCE_SELECTION.csv) | 4,698 个计划槽位及最终采用关系；结果身份与本地原件位置 |
| 重跑替换 | [superseded_slots.csv](index/superseded_slots.csv)、[实验日志](../six-models-lineage-20260914/EXPERIMENT_LOG.zh.md) | 解释 369 个旧池为何被替换；旧池不重复计分 |
| 字段口径与文件身份 | [CSV 字典](csv/CSV_DICTIONARY.zh.md)、[CSV 清单](csv/GENERATED.json)、[来源与迁移说明](provenance/README.zh.md) | 单位、差值方向、缺失口径、SHA256 与新旧路径映射 |

报告和 lineage 表各保留一份，原交付的 `report/`、`csv/paper/` 及重复聚合 CSV 已合并到上表的路径。原路径到当前仓库路径见 [PATH_MAP.json](provenance/PATH_MAP.json)。本目录应随整个仓库使用，单独复制它不包含相邻的报告和 lineage 文件。

## 数据范围

六模型为 Kimi、GLM、Qwen、DeepSeek、GPT、Gemini，Claude 不进入比较。冻结范围为 **4,698 项计划、4,682 项完成、4,671 项严格评分完整**。

- 完成本地结果含 2,496 份 N1 trajectory 和 2,186 份 N4 整池结果，共 11,240 条智能体轨迹。池内四名成员不作为四次独立重复。
- 重跑沿用原报告规定的九组整组三策略替换，共 369 个 N4 池；所有 N1 保留原来源。被替换索引是来源证据，不是额外采用的数据。
- DeepSeek 的 11 项正常结束但未交付有效配置，严格 Gap 缺失；Gap0 沿用原报告的零效用端点定义。
- Gemini 保持原报告快照，767 项完成，其余 16 项失败或未完成，不混入后续结果，也不补零。

上轮审核确认数值与来源链一致，并发现两处说明需要澄清：`expected_units` 不总等于任务数；N1 Audit 行为表的 `tool_calls` 排除了 10 次无效参数尝试。具体例子和计数见 [CSV 字典](csv/CSV_DICTIONARY.zh.md)。本次补充说明不改冻结报告、评分或 CSV 数值。

## 查询与本地原件

从仓库根目录查询公开元数据，只需 Python 标准库：

```bash
python3 results/paper-ad03e8c-delivery-20260916/tools/find_record.py \
  --model deepseek-v4-flash-0731 --system expgym \
  --scenario restricted_search --regime cost_tight --limit 1
```

输出中的 `trajectory_file`、归档成员表和 dump 位置指向完整本地交付，不代表这些原件已包含在 GitHub 中。正文案例的原件关联见 [CASE_TRAJECTORIES.csv](index/CASE_TRAJECTORIES.csv)；原绝对路径到完整交付路径的映射见 [ORIGINAL_TO_PORTABLE.csv](index/ORIGINAL_TO_PORTABLE.csv)。

完整本地交付约 4.9 GB，原目录保持原样：

`/lustrefs/users/chufan.shi/codex_space_tn/deliveries/paper-ad03e8c-20260916/`

其中保留原始归档分片、全部采用 trajectory、参考材料及原完整校验清单。失败实验、被替换运行和中间材料保留在本地历史归档；GitHub 只保留最终报告所需的分析数据和追溯元数据。[raw_archives 说明](raw_archives/README.zh.md)、历史恢复工具和清单描述的是这份完整本地交付。

`--dump-members` 需要完整交付的成员表，`--restore-dumps` 还需要真实归档分片。应进入上述完整目录运行恢复命令，例如：

```bash
python3 tools/find_record.py --slot 1a636084208d057bacd3c04b \
  --dump-members --limit 5
```

公开版没有这些 payload，不能仅凭公开 CSV 重建每步实际请求内容。

## 轻量包校验

在仓库根目录运行：

```bash
python3 tools/verify_lightweight.py
```

当前发布的文件身份见根目录 [LIGHTWEIGHT_MANIFEST.json](../../LIGHTWEIGHT_MANIFEST.json) 与 [SHA256SUMS](../../SHA256SUMS)。原 102 件报告/lineage 文件的提交、Git blob 与 SHA256 保留在 [ORIGINAL_EXPORTS.json](provenance/ORIGINAL_EXPORTS.json)。

[REVIEW.zh.md](REVIEW.zh.md)、`review_checks.json`、各模块检查记录和 `provenance/assembly/` 保留历史身份与复核范围；它们不是此次轻量发布的新验收记录。历史分析脚本可能依赖旧工作区、旧布局或本地原件。具体适用范围见 [来源说明](provenance/README.zh.md)。
