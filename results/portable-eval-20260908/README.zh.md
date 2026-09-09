# ExpGym / PoolAct 可迁移性修补：阶段性检查点

2026-09-09 新增：[Kimi-K3 v5 阶段结果与 CSV](full_delivery_v5/kimi-k3-original-node-failure-20260909/README.zh.md)。K3 已闭合为 697 项完成、8 项节点故障；报告及分析后独立复核可直接查看。完整 dump 发布与远端恢复仍在进行，GLM 尚未闭合；这不是双模型最终验收。

2026-09-09 追加：[旧运行与 v5 smoke 完整归档](closed_history_v5_20260909/README.zh.md)已发布，并通过[GitHub 重新下载与全原件恢复验收](updates/closed-history-v5-remote-verification/README.zh.md)。这不是新版正式性能结论；双模型正式全量与分析另行交付。以下保留原初始检查点说明。

封存范围：2026-09-08 04:48 UTC 之前已完成的证据。分类：**Custom study / Real smoke validation**，不是论文性能复现完成，也不是正式多模型结果。

本目录发布完整历史失败和成本，不以得分或预期方向选择样本。当前主库修补的精确源码在 `source/` 压缩包中；本分支仓库根仍是上游 main，不要把根目录代码误当成 v3 实验源码。

## 结论与证据

| 检查 | 实际观察 | 可查验入口 |
| --- | --- | --- |
| K3 原生协议，56 次请求 | 全部交付、0 传输重试；严格验收失败：裸 `none` 的 nonce 为 3/4，相同 seed 请求输出不一致 | [原始报告](evidence/protocol/k3_smoke_1203474_v2/report.json) |
| 追加边界诊断，8 次请求 | `auto` 与 `none` 加实际 final 指令各 4/4 精确 nonce；不覆盖先前失败，不构成唯一原因证明 | [追加报告](evidence/nonce-boundary/k3_nonce_boundary_1203474_v2/report.json) |
| 原 v2 三场景验证，45 条 agent trace | 228 次请求全部交付；45 条评分、18 个 PoolAct 聚合和 27 次禁止模型调用的恢复检查通过，保留 2 个零分 | [完整运行](evidence/scenario/k3_smoke_1203474_v2/)、[独立评分审计](receipts/scenario_smoke_v2_independent.json) |
| 同一批 v2 的提示兼容性 | **失败**：228/228 实际请求仍包含任务侧文本 Action 指令，与 native 系统指令冲突；有 1 次文本 Action 响应及正常步骤内修复，无 HTTP 重试 | [独立完整 raw 审计](receipts/scenario_smoke_v2_raw_independent.json)、[逐请求 router 对账](receipts/scenario_router_rawjoin_v2/final_20260908T0423Z/receipt.json) |
| v3 源码修补 | 仅对实际 native 协议调整可信任务调用指令，默认 text 字节兼容，任务数据、评分、预算和 Answer 格式不改；567 tests /5 skips，Python 3.7 专项 48 项通过 | [验收清单](receipts/static_acceptance_v3.json)、[精确源码](source/accepted-source-v3.tar.gz)、[本次增量补丁](source/patches/native_task_context_v3.final.patch) |

原 45 条验证耗时 **41.49 分钟**，输入 **1,246,357**、输出 **280,495** tokens；其中 reasoning **228,650** 已含于输出，不重复相加。每个请求/响应均和 router 双 SHA 唯一匹配；HTTP 200 来自 router，不能把 client dump 中的 null 状态字段当成已记录 200。[用量与计时回执](receipts/scenario_router_rawjoin_v2/final_20260908T0423Z/usage_runtime_receipt.json)

提示冲突属于此次从文本工具协议迁移至 native 协议时的集成遗漏；它不是“上游文本提示本来就错误”的证据。已证实冲突存在，但不能证明它是某次模型行为的唯一原因。此前 fake 的 auto 模式实际走 text，所以 fake 成功漏掉了这个真实路径问题。

K3 使用自部署权重、T=1 / top-p=1、thinking max，seed 仅作试次标签。上述配置、短 horizon 和 smoke 范围均不等于论文设定；不能从这些结果宣称 ExpGym 已普遍退化、PoolAct 已稳定提升或已推广到其他模型。

## 完整性与后续

- [逐文件 MANIFEST](MANIFEST.json) 列出 **534 个原始封存文件 /15,739,752 字节**的相对来源、发布路径和 SHA256；两份原安全清单另留在 [publication receipts](receipts/publication/)。导航及归属说明不计入这 534 文件。
- 原始 56、8、228 次请求、未满足验收的结果、协议错误、零分和用量全部保留；原文件未改写。绝对路径、研究用户名、集群主机名是历史 provenance，不是可公开访问的 API 服务。
- 不包含 API key、权重、虚拟环境、cache 或整套原始数据；任务文本及模型输出保留在请求 dump 中，参见 [数据归属说明](ATTRIBUTION.md)。
- 新 v3 21 条提示/路径验证、A21 计时、B/C 四代理 pilot、正式矩阵和其他模型 **不在本检查点中**。后续结果应追加为独立有身份的批次，不覆盖此次失败证据。
- 旧已发布实验仍在独立 [`results/kimi-k3-20260907`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/results/kimi-k3-20260907) 分支，与本研究分开。
