# 闭合历史归档：GitHub fresh clone 完整恢复证明

历史归档提交 [`c4aca97c`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/c4aca97c2ef7ce6826b58de10755a9a8c4a237f6/results/portable-eval-20260908/closed_history_v5_20260909) 已推送并从 GitHub 重新克隆；506 个交付文件的完整路径、工作副本 bytes/SHA、Git blob 与模式均已核对。随后，公开恢复 CLI 对该 fresh clone 中的 32 个包实际执行成功，并由独立后验检查核对 **47,529 个原件、1,055,374,017 B** 的全部相对路径、bytes、SHA 和恢复输出精确集合。

这是历史 DEV、已作废运行、新版 smoke、封存控制资料与源码的归档证明，**不是 v5 正式实验结果或性能结论**。归档范围与公开恢复命令见[原归档说明](../../closed_history_v5_20260909/README.zh.md)。本页补充其发布后证据，不改写归档内当时的本地状态收据。

## 核验链

| 环节 | 原件证据 | 实际结果 |
| --- | --- | --- |
| 推送及 fresh clone | [ROOT_DELIVERY_EXECUTION](closed_history_publication_stage_v1/ROOT_DELIVERY_EXECUTION.json) | 非强制推送与 fresh clone 均 exit 0；commit `c4aca97c2ef7ce6826b58de10755a9a8c4a237f6` |
| 506 交付文件／Git blob | [ROOT_REMOTE_VERIFICATION](closed_history_publication_stage_v1/ROOT_REMOTE_VERIFICATION.json) | 完整集合匹配、原有已跟踪文件未变 |
| 公共 CLI 恢复 | [CLI_EXIT](closed_history_remote_restore_v1/CLI_EXIT.json) | session 93752，exit 0，completion chunk `7221f0` |
| 独立全原件恢复核验 | [POST_RESTORE_VERIFICATION](closed_history_remote_restore_v1/POST_RESTORE_VERIFICATION.json) | session 47356，exit 0，completion chunk `74347e`；32 包／47,529 原件全 SHA 匹配，无 INCOMPLETE |
| 远端来源与全过程汇总 | [OPERATOR_COMPLETION](closed_history_remote_restore_v1/OPERATOR_COMPLETION.json) | 绑定 remote commit、全部操作收据、日志、脚本及 COMPLETE |

源合集 INDEX SHA 为 `ee080ed22ea8ccd2bf03bbb011369cc8329009c981f95c00f8d66aa4aa47d078`；恢复后的 [COLLECTION_COMPLETE](closed_history_remote_restore_v1/restored/COLLECTION_COMPLETE.json) SHA 为 `8a20a437645b1b14bdacf97aaf9fff868cac06b9d8f4247ac3b16abf1787f03d`。恢复输出包含原件和索引／完成元数据时共 47,793 个文件，不应把这个数当作实验原件数。

## 字段解释与边界

“远端恢复”在这里指：ROOT 从 GitHub fresh clone 取得归档与冻结工具，然后在本地对该克隆运行公开恢复命令；不是在 GitHub 服务器执行程序。公开恢复不读取发布者私密 key，known-secret source 数为 0。原打包时的三值检查是另一个已绑定的生产端证据，不能冒称这次公开恢复重新比对了私密值。

通用 wrapper 的 `COLLECTION_COMPLETE.json` 原本写 `remote_restore_performed=false`，因为 wrapper 不负责验证输入的网络来源。该原件字节保持不变；新增独立 operator 收据绑定 fresh clone／commit 与实际恢复过程，不能靠改写原 false 字段制造远端证明。同理，早期 ROOT_REMOTE_VERIFICATION 仅证明 506 文件身份、当时尚未解压，其原 false 字段也保持。

公开恢复会解压、读取成员字节并执行 JSON/JSONL（含 response_raw）的结构／安全校验；没有进行实验评分或质量内容分析，而独立 post verifier 只核 bytes／path／SHA。原 operator 的 `restored_experimental_payload_parsed_or_analyzed=false` 不能被解释成整个恢复子进程完全未解析 JSON；原件不回写，精确边界见新增 [RESTORE_SCOPE_CLARIFICATION](closed_history_publication_stage_v1/RESTORE_SCOPE_CLARIFICATION.json)。

恢复承诺原相对路径／bytes／SHA，不承诺 POSIX 权限、所有者或时间戳恢复。这里所附三个 `.py` 是当时操作／审查脚本原件，含当时集群路径，作为可查验证据而非通用入口；要重新恢复请使用原归档说明中的公开 CLI。

本更新只包含小型元数据、四份 stdout/stderr 日志与三份脚本，没有重复存放压缩包或实验 payload。两份 stderr 原件为空；stdout／退出状态和工具会话对应关系保留在 operator 收据。本候选整理只复制已冻结原件并扫描这些小文本，未再次解压或扫描恢复 payload、读取私密 key、调用模型／评分／API。新版正式全量、分析和最终独立逻辑审计仍是另行交付的任务。
