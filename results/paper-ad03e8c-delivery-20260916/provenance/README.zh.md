# 来源身份与轻量布局

本次发布以 `ad03e8c42ca501016176ee1bc407b38499178506` 为报告版本。仓库中的 [paper-analysis-20260916](../../paper-analysis-20260916/README.zh.md) 70 件文件和 [six-models-lineage-20260914](../../six-models-lineage-20260914/README.zh.md) 32 件文件保留该提交原字节。四张合并比较 CSV 继承上次交付的数值，此次没有重跑或重评分。

## 当前位置与历史身份

| 记录 | 含义 |
| --- | --- |
| [ORIGINAL_EXPORTS.json](ORIGINAL_EXPORTS.json) | 原交付的 102 件源文件清单，保留源提交、路径、Git blob、大小和 SHA256；`destinations` 是原交付路径 |
| [PATH_MAP.json](PATH_MAP.json) | 被合并副本的原交付路径 → 当前仓库唯一文件路径；`repository_path` 从仓库根目录解析 |
| [ORIGINAL_GENERATED.json](ORIGINAL_GENERATED.json) | 原交付 CSV 清单的原字节，路径按原布局解释 |
| [当前 GENERATED.json](../csv/GENERATED.json) | 本版 CSV 位置、行数与 SHA256；路径基准见该文件的 `path_base` |
| [LIGHTWEIGHT_MANIFEST.json](../../../LIGHTWEIGHT_MANIFEST.json)、[SHA256SUMS](../../../SHA256SUMS) | 当前轻量发布的文件身份，从仓库根目录使用 |

原交付的 `report/`、`csv/paper/` 和重复 lineage CSV 已去重。现在浏览报告及表格请使用当前仓库的 canonical 路径，即 `results/paper-analysis-20260916/` 与 `results/six-models-lineage-20260914/`。冻结报告中的旧 GitHub 提交链接、绝对路径和输入哈希仍记录当时来源；它们不是要求重新引入旧实验目录的依赖清单，也不作为本版浏览入口。

完整本地交付仍位于 `/lustrefs/users/chufan.shi/codex_space_tn/deliveries/paper-ad03e8c-20260916/`。其原 `FILE_MANIFEST.json`、`SHA256SUMS`、归档、trajectory 与参考材料保持原样。公开版根目录的新清单描述轻量发布，不能替代完整本地交付的校验清单。

## 历史脚本与复核记录

`assembly/` 是上次完整交付的构建脚本原件，保留其来源价值。部分脚本使用旧工作区绝对路径、原 `report/` 布局、旧实验元数据或本地原始文件；重新运行可能重新生成旧副本。它们应结合完整历史归档使用，不是轻量包的安装或日常验证步骤。

报告中的 trajectory 分析脚本同样保留当时输入配置。`six-models-lineage-20260914/build_report.py` 及其历史测试需要旧 `all-models-latest-20260913` 输入；这批材料已本地留档。仅凭公开分析 CSV 可以核对已发布统计，不能声称恢复原始请求或重跑全部分析。

`REVIEW.zh.md`、`review_checks.json`、`COMPARISON_CHECKS.json` 和各分析模块检查文件保留的是原审核范围。它们中的历史文件数、路径和哈希按当时布局解释。当前包使用仓库根目录的 `python3 tools/verify_lightweight.py` 验证；运行代码的常规单元测试位于 `tests/`，历史 `results/` 测试不应混入无需归档输入的测试发现范围。

`index/selected_slots.csv` 与 `index/superseded_slots.csv` 继续保留完整采用关系和 369 个池的替换证据。失败或未完成槽位的状态属于报告分母说明；保留索引不意味着公开其原始运行材料。普通 `find_record.py` 查询只读取公开的逐项索引，原件恢复仍需完整本地交付。

运行代码沿用报告发布所携的版本，具体代码来源由根目录轻量清单记录。本次 Git 整理不构成后续运行修补的合并或有效性声明。

## 两处已澄清的口径

上轮审核发现 `expected_units` 可能是任务重复、文档顺序或池单位，不能一概解释为独立任务数；N1 Audit 的行为字段 `tool_calls` 只计有效假设查询，排除了保存在原件中的 10 次无效参数尝试。这两处解释已补充到 [CSV 字典](../csv/CSV_DICTIONARY.zh.md)，冻结报告和数值保持原样。
