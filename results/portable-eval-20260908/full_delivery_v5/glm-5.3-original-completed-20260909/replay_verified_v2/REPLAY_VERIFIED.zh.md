# GLM 公共恢复与 AN2 重放：已验收

已从公开提交 `09ced6f12c5de3a19b01b2f0fc606b7fccd4e8f9` 的 fresh clone 实际恢复 **37 个包、71,634 个原文件、3,467,116,893 字节**，并独立逐路径、大小和 SHA-256 核验通过。恢复目录另含工具生成的记录，物理文件数为 71,999，不应混作原文件数。[恢复验收](evidence/glm_full_remote_restore_v1/ROOT_POST_RESTORE_ACCEPTANCE.json) · [完整核验收据](evidence/glm_full_remote_restore_v1/POST_RESTORE_VERIFICATION.json)

随后复用已验证的 2,247 项来源路径重定位，执行未修改的 AN2 分析：**10 个输出、20,093,032 字节，全部与公开恢复的原输出逐字节及 SHA-256 相同**。本次使用绝对路径 `/usr/bin/python3`，实测 **CPython 3.10.12**；`statistics.py` SHA-256 为 `88678d0406c9b3a1acff23d36eb35db88a2c6ca379c3a665226cea8d56c223ca`。完整命令和运行时记录见[执行收据](evidence/glm_public_analysis_replay_py310_v1/OPERATOR_EXIT.json)，逐文件比对见[字节核验](evidence/glm_public_analysis_replay_py310_v1/OPERATOR_BYTE_VERIFICATION.json)，最终见[ROOT 验收](evidence/glm_public_analysis_replay_py310_v1/ROOT_ACCEPTANCE.json)。历史运行只记录了裸 `python3`，其当时解析到的解释器身份未记录；不能反推历史版本就是 3.10。

首次使用 **Python 3.11.15** 的 AN2 进程虽正常退出，但字节验收失败：仅 **7/10** 文件相同。差异为 34 个 secondary `outerrep_descriptive_sd` 数值各差 1 ULP，影响 `effects.csv`、`results.json` 及其 `OUTPUT_INDEX.json`；主效应和所有均值不变。同输入的两版本标准差诊断分别复现了原值和首次重放值。首次输出、失败和诊断均保留：[首次比对](evidence/glm_public_analysis_replay_v1/OPERATOR_BYTE_COMPARISON.json) · [首次执行与失败记录](evidence/glm_public_analysis_replay_v1/OPERATOR_AN2_EXIT.json)。另一次 JS 大整数元数据序列化失真也未掩盖：[当时文件](evidence/glm_public_analysis_replay_v1/OPERATOR_PREFLIGHT.json)与[精确原始 stdout](evidence/glm_public_analysis_replay_v1/OPERATOR_PREFLIGHT.original_stdout.json)同时保留。

这证明的是**公共文件恢复与固定输入的原分析重放**，不是新模型/backend/scorer 运行，也不是跨 Python 版本必然字节相同、独立科学验证或“没有逻辑漏洞”的保证。原 pending 标记、[旧交付说明](../FULL_DELIVERY.zh.md)、其绑定 inventory 和已发布包均未改写；本页是后续证据增量。[路径重定位说明](../RELOCATION_TOOL.zh.md)

[增量文件清单](FILE_MANIFEST.json)按不同源路径保留两次重放的全部原件，不按相同内容去重；不再次复制 71,634 个恢复文件。另附[冻结的恢复后核验程序](tools/verify_restored_files.py)及[旧 controls 元数据覆盖检查](COLLECTION_COVERAGE.json)。本增量整理阶段未重新执行恢复、分析、模型或扫描。
