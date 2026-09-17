# CSV 入口与比较口径

这组表固定于报告提交 `ad03e8c42ca501016176ee1bc407b38499178506`；不采用后续报告或运行状态。
原始表逐字节导出；新增宽表只对 `absolute_settings.csv` 的未舍入 `full_mean` 做透视与减法，未重评分。

## 先看哪张表

| 文件 | 每行代表什么 | 用途 |
| --- | --- | --- |
| [MAIN_COMPARISON.csv](MAIN_COMPARISON.csv) | 一个模型 × 主场景 × 主指标；N1 三预算或 N4 同预算三策略 | 最短比较入口，指标范围对应冻结 `main_expgym/main_poolact` |
| [COMPARISON.csv](COMPARISON.csv) | 一个模型 × 场景 × 切片 × 指标；N1 三预算或 N4 同预算三策略 | 全指标合并宽表，包含家族/具体任务与次指标 |
| [N1_BUDGET_COMPARISON.csv](N1_BUDGET_COMPARISON.csv) | 一个模型 × 场景 × 切片 × 指标 | Free / Moderate / Tight 及预算差 |
| [N4_STRATEGY_COMPARISON.csv](N4_STRATEGY_COMPARISON.csv) | 一个模型 × 场景 × 切片 × 指标 × 预算 | naive / cached / poolact 及策略差 |
| [absolute_settings.csv](../../six-models-lineage-20260914/absolute_settings.csv) | 一个模型—预算—策略—切片—指标设置 | 完整原均值、已知子集均值、分母、时间和来源 |
| [contrasts.csv](../../six-models-lineage-20260914/contrasts.csv) | 一个有方向的同指标比较 | 原报告逐比较差值、可比完整度 |
| [by_repeat.csv](../../six-models-lineage-20260914/by_repeat.csv) | 一个设置 × 已有重复/顺序标签 | 冻结重复层出口；不能把 R1 伪装成多次重复 |
| [main_expgym.csv](../../six-models-lineage-20260914/main_expgym.csv)、[main_poolact.csv](../../six-models-lineage-20260914/main_poolact.csv) | 主指标设置 | 原报告主表入口，保留显示值和完整状态 |
| [family_rankings.csv](../../six-models-lineage-20260914/family_rankings.csv)、[rank_transitions.csv](../../six-models-lineage-20260914/rank_transitions.csv) | 家族—预算排名或相同候选集的排名变化 | 必须保留可比模型集，不跨缺失集合比较冠军 |
| [SOURCE_SELECTION.csv](../../six-models-lineage-20260914/SOURCE_SELECTION.csv) | 被采用/替换的来源设置记录 | 解释哪些原运行由注册的重跑整组替换 |
| [DATA_LINEAGE.csv](../../six-models-lineage-20260914/DATA_LINEAGE.csv) | 一个模型—系统—场景—预算—策略主指标 | 运行来源、时间、原始 dump 入口与原提交 |
| [SCORE_COMPLETENESS.csv](../../six-models-lineage-20260914/SCORE_COMPLETENESS.csv) | 一个来源/设置的计划与评分计数 | 区分已执行、可评分、失败和未完成 |
| [EXPERIMENT_LOG.csv](../../six-models-lineage-20260914/EXPERIMENT_LOG.csv) | 一次实验/修补/恢复批次 | 历史日志含被排除的 Claude 批次，不进入六模型比较 |

## 新增宽表字段

- `comparison`：`N1_budget` 或 `N4_strategy`。N1 的 `regime` 留空，因为一行同时容纳三档；N4 的 `regime` 指明 Moderate/Tight。
- `slice_kind` / `slice`：`all`、家族或具体任务等原切片身份。不同层级重叠，不可把所有行再平均。
- `metric` / `unit` / `N` / `analysis_unit`：继承原指标、原单位、智能体数和聚合单位。不同指标不可合成总分。
- `{arm}_full_mean`：原 CSV 的完整均值字符串；未舍入、未缩放、未填补。`arm` 为 free/moderate/tight/naive/cached/poolact。
- `*_minus_*`：列名方向的差值，例如 `tight_minus_free`、`poolact_minus_cached`；用原均值十进制字符串相减，不用两位显示值。
- `unit=fraction` 时均值和差值仍是原 0–1 数值；乘 `report_scale=100` 才是报告 0–100 分数及百分点差。其他单位原样保留，`report_scale=1`。`report_score_unit` / `report_delta_unit` 仅说明转换后的单位，不表示数据已转换。
- `{arm}_absolute_record`：`absolute_settings.csv` 的一基数据记录号，不含表头；可定位完整时间、上游源行、重复分母、已知子集等字段。不是含表头的文本行号。
- `{arm}_cohort_id`：原运行/重跑身份；同一模型的 N1 与 N4 可能来自不同批次。来源不因新旧分数高低重新选择。
- `{arm}_expected_units` / `known_units` / `missing_units`：继承对应来源的计划、已知与缺失单位计数；单位可能是任务重复、文档顺序或整池，不能一概解释为独立任务数。应结合 `analysis_unit`、原聚合表的 `expected_items` 及重复字段使用；具体例子见下节。
- `complete`：该行三个有效实验臂的 `full_mean` 均存在。两臂可比时仍保留该对差值，即使第三臂不完整。

空值有两种原因：不适用的臂（N1 无三种池策略；N4 无 Free 池），或已计划但缺少完整分数。
前者没有 `absolute_record`，后者有来源记录与缺失分母。只在两端完整时计算差值。
正常结束但未交付配置的零效用只属于原定义的 Gap0；严格 Gap 仍缺失。失败/未完成均不补零。

## 计数口径补充

上轮审核确认聚合数值正确，但原字段说明过于概括。以下为 `slice_kind=all` 的例子，读取其他切片时应以其原记录为准：

| 设置 | `expected_units` | 原聚合表的 `expected_items` |
| --- | --- | --- |
| 六模型 N1 HPO | 27 次任务重复 | 9 个任务 |
| 六模型 N4 NAS | 9 个池/重复 | 3 个任务 |
| 五个非 Gemini 模型 N1 Audit | 13 个已折叠顺序的文档 | 13 个文档 |
| Gemini N1 Audit | 39 个文档—顺序单位 | 13 个文档 |
| 六模型 N4 Audit | 13 个池/文档 | 13 个文档 |

这些计数保留了来源数据的表示方式，不改变报告对任务/文档及其内部重复的聚合规则。不同表示不能混加为样本量，也不能把池内成员当成独立任务。`{arm}_absolute_record` 可定位原 `absolute_settings.csv` 的完整计数字段。

N1 Audit 的 [trace_metrics.csv](../../paper-analysis-20260916/audit/trace_metrics.csv) 中，`tool_calls` 实际统计**有效假设查询**；[原分析脚本](../../paper-analysis-20260916/audit/analyze_audit.py) 跳过了假设 ID 无效的尝试。行为表合计 8,134 次，完整 trajectory 的工具尝试合计 8,144 次。差异为 8 条轨迹中的 10 次无效参数尝试（DeepSeek 8 次、GLM 2 次），均为零反馈费用，原件完整保留。

因此，不能把这里的 `tool_calls` 当成全部工具尝试，也不能把有效假设查询数直接当成实际可见反馈数。该说明针对 N1 Audit 行为表；不改 LA、EA、联合正确率或 PoolAct 指标。上述两处为口径说明修正，冻结报告、CSV 字段与数值保持原样，没有重新评分。

## 论文派生表与 trajectory

分析 CSV 现在直接保留在相邻的 `results/paper-analysis-20260916/`，原 `csv/paper/` 副本已合并：

- [rank/](../../paper-analysis-20260916/rank/)：预算效应、七维度分数/候选集合、任务级 regret。
- [search/](../../paper-analysis-20260916/search/)：一行一条 N1 Search trajectory、模型/家族汇总、Free/Tight 配对与代表例。
- [hpo/](../../paper-analysis-20260916/hpo/)：一行一条 HPO trajectory、逐可见配置评估事件、配对和聚合。
- [audit/](../../paper-analysis-20260916/audit/)：轨迹、文档、假设呈现、证据补全配对；假设呈现不是独立文档。
- [poolact/](../../paper-analysis-20260916/poolact/)：主要/全部指标与场景宏均值；`coordination/` 分别是审计池、池内成员、模型—预算—策略汇总。
- [cases/](../../paper-analysis-20260916/cases/)：DeepSeek 交付分解与成对明细，以及四个案例的选择规则和原件索引。

这些文件是已冻结的派生表。完整 trajectory 与原始 dump 仅保留在完整本地交付中，公开表格中的原件路径不表示该 payload 已公开。

原报告及方法附件保留原文。报告侧源文件、Git blob 和 SHA256 见 [ORIGINAL_EXPORTS.json](../provenance/ORIGINAL_EXPORTS.json)；旧路径到当前唯一文件的对应关系见 [PATH_MAP.json](../provenance/PATH_MAP.json)。新增宽表的原算术检查见 [COMPARISON_CHECKS.json](COMPARISON_CHECKS.json)，当前 CSV 位置、身份与行数见 [GENERATED.json](GENERATED.json)。后者的 `csv_files[].path` 和 `source` 从交付目录解析，`source_export_index` 从本 `csv/` 目录解析。

原 CSV 中绝对路径和历史链接继续保留来源身份；完整本地交付中的 raw/trajectory 新位置以包级索引为准。历史脚本和复核记录的适用范围见 [来源说明](../provenance/README.zh.md)。
