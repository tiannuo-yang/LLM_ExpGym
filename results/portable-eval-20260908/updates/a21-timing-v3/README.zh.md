# Kimi-K3：A21 单代理计时试验与完整原始数据

2026-09-08 UTC，Custom study / development timing pilot。这是已完成的计时与实现验收阶段，不是正式性能矩阵，也不能据此认定 ExpGym 退化、PoolAct 提升或跨模型结论。A21 不进入后续正式效应分析。

固定范围：9 个 HPO 任务，加 Restricted Search 和 Evidence Audit 的 12 条轨迹，共 21 个单代理任务；预算、顺序和请求配置见[冻结授权](receipts/a21_authorization_v3.json)及[完整运行目录](evidence/pilot/k3_a21_1203474_v3/)。所有原始尝试、合法提前结束和零分均保留。

| 项目 | 核对结果 |
| --- | --- |
| 轨迹 / 原始 HTTP 请求 | 21 / 248，全部保留 |
| 原 evaluator 独立重评分 | 21 条全部一致；其中 1 条合法零分 |
| 禁止生成的恢复检查 | 21 次 verified skip，受保护原件不变 |
| 实际任务提示、schema、有序历史、raw 账目 | 全部通过 |
| 请求失败 / HTTP 重试 / length / 协议修复 | 0 / 0 / 0 / 0 |
| HPO 阶段 wall time | 1,034.336 秒，17.24 分钟 |
| Search + Audit 阶段 wall time | 817.891 秒，13.63 分钟 |
| 两阶段 harness wall time 之和 | 1,852.227 秒，30.87 分钟 |
| 启动至 execution 完成 | 1,871.403 秒，31.19 分钟，含启动间隔 |
| input / output / total tokens | 1,625,495 / 160,442 / 1,785,937 |

119,939 reasoning tokens 已包含在 output，不能重复累加。prefix-cache 用量未报告，不能补零或判断没有命中。14 条自然结束、5 条预算结束、2 条步数结束；241 次 auto 与 7 次 forced-none 请求，不要求每个 agent 都经历 forced-none。

## 为什么仍要半小时

权重冷加载已经在本轮开始前完成。[HPO 耗时分解](receipts/validation/a21_A1_time_decomposition_20260908T0547Z.json)显示，各 child 重叠耗时之和约 2,574.3 秒，其中 HTTP 区间之和约 2,551.6 秒（99.1%）；这些重叠区间不能再当作整体 wall time 相加。此观察支持本轮主要在等待模型请求，不能分离精确的 prefill、decode 和网络耗时。

资源为 8 节点 × 每节点 8 张 H200，总计 64 GPU，组织为 4 个双节点 TP16 副本，不是单个 TP64 副本。A21 实际完成请求区间峰值并发为 4，每副本最多 1；它不是饱和吞吐测试。输出峰值 7,093 tokens，单请求最长约 240.93 秒。[配置复核](receipts/a21_serving_config_recheck_v3/README.zh.md)未发现已核对范围内的配置不一致，但未证明配置最优，也不能据此给出整个后续项目的可靠 ETA。启动时的 GPU UUID 证据不冒充本次实时物理扫描。

## 查验入口

- [完整 A21 运行产物](evidence/pilot/k3_a21_1203474_v3/)：21 trace、248 raw dump、全部日志、计划、命令、状态与 lock。
- [独立评分与提示审计](receipts/validation/a21_v3_independent.json)、[独立 raw 审计](receipts/validation/a21_v3_raw_independent.json)、[ROOT 验收](receipts/validation/a21_root_acceptance_20260908T0558Z.json)和 [ROOT wire 用量复核](receipts/validation/a21_root_wire_usage_recheck_20260908T0557Z.json)。
- [router 双 SHA 对账](receipts/a21_router_rawjoin_v3/final_20260908T0555Z/receipt.json)、[用量与时间](receipts/a21_router_rawjoin_v3/final_20260908T0555Z/usage_runtime_receipt.json)、[服务排空](receipts/a21_router_rawjoin_v3/root_drain_20260908T0555Z.json)。router 快照还保留 291 条旧窗外记录；本轮只对齐并计入 248 次 A21 请求。
- [实际 harness](source/harness/pilot_timing.py)、[审计器原件](source/review/audit_a21_v3.py)、[单行 schema 修正版](source/review/audit_a21_v3_score_schema_fix.py)、[修复与回归记录](receipts/validation/a21_independent_auditor_score_schema_repair.json)。
- [本次逐文件清单](MANIFEST.json)、[安全扫描清单](receipts/publication/a21_v3_locked.manifest.json)、[先前验收的精确 v3 源码包](../../source/accepted-source-v3.tar.gz)及[前一阶段](../native-gate-v3/README.zh.md)。源码指纹为 `d1606db7d6036c8975ce9d3e556daf7fa2ce4604879f2b3878435b0f96aebb78`；本次不重新打包活动工作树。

## 失败记录与边界

首次全量审计在开始重评分前，因审计器取不存在的 `answer_perf` 字段而报错。保留原审计器；只新增一行派生修正，从原 scorer 的实际结构取零分计数。没有修改 evaluator、原始实验结果或重新调用模型。准备收据 v1/v2 中 5 条历史代码哈希与最终冻结版本不同；旧版本未重建，历史收据不能充当当前代码哈希凭据。当前原件、派生修正版及修复记录均在本清单内。

原先发布的 704 个文件保持不变。本次 420 个原始证据文件仅构成追加检查点，不包括活动 B/C、正式矩阵、第二模型或最终复审。全部实验与分析之后仍须进行一次独立端到端逻辑复查，即使方向符合预期也不能跳过。

库根目录仍为原上游快照；运行修正版须使用已验收源码包及其对应环境和数据，不要把本结果分支根目录当作修正版 checkout。原始收据内保留工作区绝对路径，公开浏览请使用本页相对链接。数据归属及许可证遵循[原 ATTRIBUTION](../../ATTRIBUTION.md)；未发布密钥、模型权重、环境或独立数据文件。已知密钥与模式检查不能证明不存在所有未知秘密或许可问题。
