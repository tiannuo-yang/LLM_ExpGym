# K3 公开数据恢复与分析重放验收

2026-09-10：对 GitHub 数据提交 `1694aa2a1a79a651629055b45fdd02e20aacdc95` 的完整恢复及原 AN2 分析重放已通过。此页记录离线交付验收，不是新增模型实验。

## 已通过的实际检查

- 全新 GitHub clone：4,822 个 Git 文件、2,345,347,523 B，Git blob 与工作文件字节/模式核验通过；不是本地恢复目录复用。[远端身份与完整 Git 树凭据](evidence/k3_composite_full_remote_restore_v1/ROOT_REMOTE_VERIFICATION.json)
- 原恢复程序一次正常退出：36 包、66,643 件原文件、1,751,137,861 B。随后原全量检查器再次逐文件核对路径、大小、SHA；实际恢复树为 66,986 件（包括索引和回执），无缺失、多件或 INCOMPLETE。[全量校验](evidence/k3_composite_full_remote_restore_v1/POST_RESTORE_VERIFICATION.json)、[ROOT 接受](evidence/k3_composite_full_remote_restore_v1/ROOT_POST_RESTORE_ACCEPTANCE.json)
- 原路径迁移器一次正常退出：2,247 个来源，2,215 来自原轮、32 来自固定恢复；准确对应原 697＋恢复 8 项和 783 logical。没有换样本、再生成答案或重新评分。[映射核查](evidence/k3_composite_public_analysis_replay_v1/RELOCATION_CHECK.json)
- 原 AN2 使用明确的 **CPython 3.11.15** 一次运行，全部 **10/10 输出、19,632,937 B** 与恢复出的最终 K3 Py311 基线逐字节相同，包含 OUTPUT_INDEX 自身；不是只比较均值或使用浮点容差。[实际执行](evidence/k3_composite_public_analysis_replay_v1/AN2_EXECUTION.json)、[完整对照](evidence/k3_composite_public_analysis_replay_v1/REPLAY_COMPARISON.json)、[ROOT 接受](evidence/k3_composite_public_analysis_replay_v1/ROOT_REPLAY_ACCEPTANCE.json)
- [此前发布文本的有限独立复核](evidence/k3_final_public_release_review_v1/RELEASE_REVIEW.zh.md)单独保留。它是对 1694aa2 版本导航与科学解释的复核，不冒充本次恢复/重放检查。

最终十输出见[实际输出索引](evidence/k3_composite_public_analysis_replay_v1/replayed_an2/OUTPUT_INDEX.json)，SHA `9e9d1c767b09f916e21b273a0c8cd985a8db2b3a0a9f6a0dc64f3604c403b147`。[有限交付清单](FILE_MANIFEST.json)记录本增量各原件来源、公开路径与哈希；清单自身不包含自己的哈希，避免自引用。

## 查验与结论边界

[联合归档与原恢复命令](../FULL_DELIVERY.zh.md)、[最终报告与全部反例](../README.zh.md)、[GLM 已通过的恢复/重放](../../glm-5.3-original-completed-20260909/replay_verified_v2/REPLAY_VERIFIED.zh.md)。本次没有新模型调用、GPU 申请、评分修改或重新打包旧归档。

两模型六个主比较方向一致，但仍保留全部 49 行负性能比较、GLM 正常缺答、旧 K3 基础设施失败与未知费用；不能据字节重放推导普适、稳定、统计显著或 paper-exact 结论。本研究仍为 Custom study；报告成稿后的独立逻辑复核已另行完成。

K3 内层 1,292 B 和外层 10,383 B 两份非实验回执的公开省略及原失败不变，详见[公开范围限定](../FULL_DELIVERY.zh.md#公开范围限定)。不是所有私有附属引用都可公开下载；所有实验原件和科学分母不受这两项影响。GLM 自身的历史范围限定见其独立交付页。

原工具中 `publication_performed=false`、`remote_restore_performed=false` 和旧报告 pending 字段保留历史原值；真正远端身份与后续完成状态由外层凭据证明。恢复不保证 POSIX 模式/所有者/mtime，逐文件检查也不是对抗并发篡改的原子快照。收据中的绝对路径是本次执行身份，不是网络地址；换机器重放应依照 ownership/member indexes 和原迁移 spec 绑定新恢复根，仍需相同的分析 Python 版本，不能直接运行历史绝对路径。

本页验证的数据身份是 **1694aa2**。承载这些新凭据的后续 Git 提交与数据提交不同；新提交不修改联合索引、归档或冻结分析结果。本清单不递归收录证明自身未来 Git 发布的收据，发布后取回核验另外留存。
