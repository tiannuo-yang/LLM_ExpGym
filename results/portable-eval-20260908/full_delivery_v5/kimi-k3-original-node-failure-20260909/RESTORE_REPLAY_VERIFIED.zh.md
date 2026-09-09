# K3：公共恢复与分析复跑验证补充

这份补充记录完整交付后的恢复验证。既有阶段报告及 FULL_GUIDE 的历史待办表述保留原字节；以下后续证据不改写实验记录，也不表示补齐了 8 个 NODE_FAIL 调用。

## 已实际完成

公开源提交为 `ac9a621c98ade026d3562a3c1b50206de16e4a89`。[远端核验](evidence/workspace/publication/k3_full_publication_v1/ROOT_REMOTE_VERIFICATION.json)确认 fresh clone 的 1,286 个 Git 文件及工作树字节、模式一致。

原公共恢复 CLI 单次运行，session `79432`，实际退出码 `0`；使用 collection SHA `a78227369423e71e8c4380e46416b8a4ed88464f3e8a502fe1747e7e703103f5`，未传私密 secret-file。[实际退出记录](evidence/workspace/publication/k3_full_remote_restore_v1/CLI_EXIT.json)、[操作总回执](evidence/workspace/publication/k3_full_remote_restore_v1/OPERATOR_COMPLETION.json)和[完成标记](evidence/workspace/publication/k3_full_remote_restore_v1/restored/COLLECTION_COMPLETE.json)保留原件。

ROOT 随后单次独立核验全部 34 包的 65,105 份原件，共 1,521,531,633 B：原相对路径、字节数、SHA 全部一致。见[完整逐件核验摘要](evidence/workspace/publication/k3_full_remote_restore_v1/POST_RESTORE_VERIFICATION.json)及[接受回执](evidence/workspace/publication/k3_full_remote_restore_v1/ROOT_POST_RESTORE_ACCEPTANCE.json)。此处不承诺 POSIX 权限、mtime 等原文件系统属性复原。

公开恢复会解压、读字节并执行 JSON 结构及安全校验；这不是实验评分或答案质量分析，也不是再次执行私密 known-value 扫描。原 wrapper 的 `remote_restore_performed=false` 等字段未回写；实际远端来源由上述独立操作证据证明。

## 描述性分析已从恢复原件复跑

原 relocator v2 单次退出 `0`（session `66253`），仅生成本次恢复位置的路径映射；原 AN2 单次退出 `0`（session `15525`）。ROOT 比较全部 10 份输出，均与已恢复原分析输出逐字节一致，见[完整 10 项比较索引](evidence/workspace/publication/k3_public_analysis_replay_v1/ROOT_REPLAY_VERIFICATION.json)。没有调用模型、评分后端或重新抽样；这证明分析可复跑，不是一次新的独立科学结论审阅。

网页可直接查看原 [SUMMARY](analysis/actual_formal_export_k3_node_failure_v2/SUMMARY.zh.md)、[effects.csv](analysis/actual_formal_export_k3_node_failure_v2/effects.csv)、[known_subsets.csv](analysis/actual_formal_export_k3_node_failure_v2/known_subsets.csv)、[logical_outcomes.csv](analysis/actual_formal_export_k3_node_failure_v2/logical_outcomes.csv)、[metrics.csv](analysis/actual_formal_export_k3_node_failure_v2/metrics.csv)、[paired_rows.csv](analysis/actual_formal_export_k3_node_failure_v2/paired_rows.csv)与 [results.json](analysis/actual_formal_export_k3_node_failure_v2/results.json)。其余 `provenance.json`、`raw_terminals.csv`、`OUTPUT_INDEX.json` 不重复镜像；10 份原输出均在 controls 包中，原相对位置是：

```text
portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/
operations/restart_user_20260909/actual_formal_export_k3_node_failure_v2/
```

按 collection 的 OWNERSHIP 映射定位这些原件；上面的换行仅为排版。

## 在另一台机器复用

先完成公共恢复与完整原件校验，再依[原 relocator 使用说明](evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/README.zh.md)和[源码](evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/relocate.py)为自己的恢复目录生成新 spec 与 source_index。原 manifest、records、oracle、input_pins、source_index 及被引用原件的字节和 pins 保持不变；只有派生路径映射改变。

本次[原 spec](evidence/workspace/publication/k3_public_analysis_replay_v1/ROOT_RELOCATION_SPEC.json)、[映射证据](evidence/workspace/publication/k3_public_analysis_replay_v1/relocated/MAPPING_EVIDENCE.json)、[派生 source_index](evidence/workspace/publication/k3_public_analysis_replay_v1/relocated/source_index.relocated.json)含执行现场绝对路径，不能直接当作任意机器上的可运行配置。[迁移接受回执](evidence/workspace/publication/k3_public_analysis_replay_v1/ROOT_RELOCATION_ACCEPTANCE.json)与[AN2 实际命令记录](evidence/workspace/publication/k3_public_analysis_replay_v1/ROOT_AN2_REPLAY_GO.json)提供本次实例。

本次 controls 包已包含 AN2、converter、planner 三份代码，并保留所需相对目录布局，无需为这次 K3 复跑另取旧 32 包。按原说明保持这些相对目录；不要改解析器、指标规则或原输入来追求一致输出。全部原始失败/unknown 和 `false` 状态仍保留；8 个 NODE_FAIL 未由此次恢复或复跑补齐。
