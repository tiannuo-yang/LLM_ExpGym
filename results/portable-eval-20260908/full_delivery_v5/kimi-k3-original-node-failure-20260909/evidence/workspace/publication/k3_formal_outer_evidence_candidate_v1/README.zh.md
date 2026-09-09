# K3 完整交付：606 件外层证据候选清单

`FILES.candidate.json` 是本轮精确 source→target 清单，**candidate=true、approved=false**。606 件原件共 **263,946,656 B**，目标为 K3 原节点故障 leaf 下的 `evidence/workspace/<原 workspace-relative path>`。只完成元数据／脚本／日志原件哈希，没有复制、内容扫描、pack/restore、Git、模型操作或远端验收；没有读取任何 raw、archive、restored payload、key 或活动 GLM。

入口：`FILES.candidate.json` 290,311 B，SHA `168a8eeee8d07cab00b88fa77640d0439b166b47c37cd0aa6c89113ca79cdf32`；`HASH_RECEIPT.json` SHA `15ef6dbef38b96aa4ca722f345deb06216b1ebcb5fdada930aff8e38e91697e0`。全部 canonical regular 原件两遍完整 SHA/bytes 与前后 stat 相同；606 个目标字符串排序、唯一、无前缀冲突。32 个在指令／既有冻结证据中给出的外部 SHA 另外核对，其余行明确标为本次完整观察哈希，不假称所有 606 件都已有独立外部 pin。

| 分组 | 件数 | bytes |
| --- | ---: | ---: |
| raw 每批完整外层 proof/log（含全部 66 child exits） | 363 | 21,284,943 |
| raw PREFLIGHT/STARTED/SUMMARY | 3 | 197,741 |
| 原 33 批 scan 全输出 | 167 | 166,053,143 |
| raw scan GO＋ROOT COMPLETION | 2 | 4,126 |
| raw 原 scope candidates | 36 | 72,092,098 |
| raw operator 4 件 ROOT 文件 | 4 | 89,636 |
| raw pack GO | 1 | 3,659 |
| controls scan 元数据 | 5 | 2,385,079 |
| controls seal 三输出＋GO＋ROOT completion | 5 | 907,548 |
| controls 两 candidate | 2 | 743,670 |
| controls 五 proof/GO/restore COMPLETE | 5 | 9,670 |
| 冻结实用代码／说明／owner CPU receipts | 11 | 117,569 |
| 真实 assembly selection＋GO | 2 | 57,774 |

`prepare_metadata.py` 只枚举指令给定的路径与 33 个明确 batch ID；不递归扫描目录，不解析或跟读原 JSON 的 refs。每个输入小于 100 MiB，没有放宽既有 cap。目标排序首次拒绝暴露的是本脚本将 Path 分段排序当作完整目标字符串排序（例如 `restore/COMPLETE.json` 与 `restore.exit.json`）的问题；只增加 `rows.sort(key=lambda row: row['target_path'])`。没有改变任何 scope、pin、原件或限制。首次失败、有限诊断与最终真实运行记录在 `EXECUTION_RECEIPT.json`，没有把失败隐去。

## 明确选中的路径边界

raw operator 根的四件恰为 `ROOT_START_ACCEPTANCE.json`、`ROOT_COMPLETION.json`、`ROOT_LOCAL_PROOF.json`、`ROOT_METADATA_CHECK.executed_inline.py`；最后一件只按字节读取，没有执行。每批保留 RESULT、WHOLE_FILE_COMPARISON、restore/COMPLETE，以及 pack/restore 各 started/exit/stdout/stderr（空文件也保留）；不复制 bundle 或 restore/payload。Controls 的 pack/restore 事实来自原 OPERATOR_COMPLETION 投影，没有创造独立原 stdout 日志。

三个初始简称的精确位置经 ROOT 更正为：`OP/ROOT_K3_CONTROLS_HASH_GO_20260909.json`、`OP/k3_delivery_controls_sealed_v1_operator/ROOT_COMPLETION.json` 和 `P/k3_formal_collection_assembly_v1/ROOT_GO.json`。仅按这些更正继续，没有范围发现式扩展。

## 不在本候选内的外部引用

- 完整 assembly `payload`、其中的 collection、34 包的 INDEX/COMPLETE/SOURCE_SCAN/member pages/archives、五恢复工具、RELEASE_FILES 和 ASSEMBLY_RECEIPT：由 ROOT 原 assembler 精确集合另纳入；本轮从未打开它们。ROOT 后来报告 assembly 已完成，但这不改变本候选范围或构成本轮核验。
- 刚生成的实际 assembly／ROOT 后验三件证明：ROOT 最后精确追加，不从已知 refs 自动扩张606范围。最终 outgoing 总数与 SHA 必须重新针对实际组合计算，不能沿用606声称全leaf完整。
- 已在917 controls中的完整导出17件、AN2/exporter、评分／汇总／用量／提示词／格式审计及原 run seal 等，不再次复制到本 outer 清单。原 raw 64,188件也不在此清单；它们由34包恢复。之前发布的37浏览／导航原件不改；两个 impact 附属原件仍在这37中，不因此变成917的成员。
- 33批 scope inventory 的 authority、原 source acceptance、runtime/profile、论文 metric catalogue/planner、具体 seal part 等 refs，本程序没有递归验证其公开闭包；已有917或旧32包的原件应经它们的 OWNERSHIP/member index 定位。没有确认成员归属的具体外部 ref 不能因旧包存在就声称可离线复跑。
- 工程 CPU_RECEIPT 可能引用本轮未选的 tests、CPU logs、AST/peer/root acceptance；11实用代码件不是完整工程验收附件全集。原 bytes/ref 保留，缺项若需要公开由 ROOT 后续明确决定，不自动纳入。
- GO/started 中的服务／credential 路径只是原元数据字节；**路径指向的 key、环境私密内容、解释器/venv、权重、缓存、数据库及活动 monitor 全部不在 scope**。不要按原 argv 或 refs 盲目执行、复制或跟读。

这些边界不妨碍使用独立 payload 的公开 restore CLI，但“所有外部执行依赖完全自包含”与“AN2 异地 replay 已验证”不能由本清单推论。新 outer 文本仍须经过 ROOT 后续内容／许可与已知值审查，本次哈希不继承或代替 scan pass。

原 execution/score false 与8项 infra 保持；本地交付成功、科学完成、完整公开、远端恢复、异地分析分别记录。本作者既有 gold 暴露记录不变，不承担 fresh 科学主结论审阅。
