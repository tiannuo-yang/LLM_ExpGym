# 最终独立复核

结论：已完成同一次独立复核，未发现改变本报告主要结论的聚合、分母或来源串用错误。此结论限于本次登记的修复复验，不是宣称框架或模型的所有行为都已无误。

[主报告](README.zh.md) · [详细报告](DETAILS.zh.md) · [完整归档索引](ARCHIVE_INDEX.md) · [机器检查](review/final/REPORT_COMPARISON.json) · [独立旧新比较](review/final/contrasts.csv)

## 核到了什么

- 全部 369 个科学池、1476 个成员执行及评分完整；9 个模型×场景×预算单元、27 个策略设置，所有登记槽位均保留。
- 独立代码不调用正式报告生成器的计算函数，也不调用评分器或模型。按 SHA 绑定的计划、索引、result/summary 和完成回执核身份、终态及保存标量；前三模型 303 池形成标量缓存后，GLM 阶段仅追加其 66 池，没有再读取前三模型 result。
- 对成稿核对 1512 行逐池指标、132 行聚合、132 行方向对照、1512 行配对、312 行按 seed 汇总、972 行按 item 汇总、132 行旧新指标比较，共 8195 次数值一致性检查，全部通过。Search 用 F1-MV，Audit 主端点用 Evidence-Accuracy-MV，不把 Label Accuracy 当作 Evidence Accuracy。
- NAS 对每成员先计算下限截为 0、无 100 上限的 Gap，再按 N4 求 MI；ABC 各自折叠 R3 后 item 等权。不删除未知成员、不取已知交集。540 个 NAS 成员均可评分，故新 strict 与 Gap0 同值。
- 旧对照不是只按 setting 名称匹配：全部消费行都核对 N、expected outcomes/items 和重复数；NAS Gap0 补绑定 strict 的 36 成员/9 池。WHOIS 为 39 题、Audit 为 13 文档、NAS 为 ABC×R3。旧 GPT 缺失的 repeat-match 标志通过同一 commit 的逐池 CSV 核对实际三个 seed；旧 legacy 表的空标志没有伪装成 True。GLM 旧 Audit 只有 all 行而无重复 family 行，明确按其 Audit13/R1 元数据绑定。

成员评分完整不等于所有回答非空：GLM Audit PoolAct 有 1 个空回答，原评分器已评分且保留在 N4 分母；没有补造答案，也没有当成 unknown 排除。独立 CSV 的 `normal_model_missing` 专指未评分的正常无配置，因此该列为 0 与这一已评分空答不矛盾。

## 结论是否忠于数据

是。登记主端点中，PoolAct 高于 naive 8/9，高于 cached 7/9，同时高于两者 7/9；Tight 的 5 个主端点单元均高于两者。它不等同于所有次级指标都改善：例如 GLM Audit 的 Label-Accuracy-MI 仍有负差，详细表予以保留。

DeepSeek Audit 和 NAS 的主要旧反例消失；仍需保留 DeepSeek WHOIS Moderate 相对 cached 的 −0.474 分，以及 GPT NAS Moderate 相对 naive/cached 的 −0.139/−0.244 Gap 点。这两类残余反例的三臂没有缺最终回答，不能归咎于本轮空答。没有为追求正差选择 seed、删除数据或追加抽样。

主报告的三个问题边界正确：预算退化与家族排名仍使用冻结旧五模型单体 cohort，原 CSV 字节与指定 commit 一致；六家族中 2 个 Free→Tight 最优集合改变，两档均不存在跨所有家族的唯一最优模型。本次仅重跑四模型的定向 N4 队列，不能更新旧单体排行榜，也不是 Qwen 的新复验。修复前后包含源码、提示和 DeepSeek 部署设置等共同变化，不能归为单补丁性能因果，更未进行显著性或未见任务检验。

## 实际设置、资源与交付边界

[实际执行说明](EXECUTION_NOTES.zh.md)已与冻结计划和来源 metadata 核对：四模型实际 HTTP retry=2；GPT 为统一的本地近似 cap262144、medium，保留原 opaque history 与 wire 参数省略；首个恢复池未越过旧 cap，不能冒充 provider 容量压力测试。通用 graph/Audit 修复与 DeepSeek serving 兼容设置区分清楚。保留 legacy peer 配置可能回退自身 best 的评分边界，未升级评分约定或替无回答成员填配置。

资源小表按池到 setting 的加总通过。GPT 的 27 科学槽对应 28 个物理池尝试，1403 次成功请求与原 12 次 ConnectionRefused 分账保留；失败 usage 是 unknown，不能填 0。请求耗时之和有并发重叠，不等于总历时；reasoning/output 和 cached/input 子集不重复相加。三模型 top-level allocation 按 GPU 数×Start/End 时长复算共 **328.5311 GPU-hours**（DeepSeek 78.9889、Kimi 73.48、GLM 176.0622），包含启动/JIT/空闲/排空，不是纯推理时间。正常释放的 Slurm CANCELLED 不代表实验被中断，也不把 cancellation End 冒充精确物理 GPU 空闲时刻。

发布布局将报告与共享输入平铺到同一研究根，因此全部尝试索引内 `attempts/`、`resource_exports/`、`accounting/` 的相对路径有明确解析基准；完整原件由四个模型包及归档索引查验。原件内 pending/not-pushed、生成器 `independent_final_review=false` 等是生成时及生产者自身范围的快照，不改写成发布后状态；本独立说明与最终发布/远端验证记录分别提供后续证据。

本 reviewer 没有打开 API raw 或独立 agents 文件、恢复压缩包、重评分、重做全库源码或模型回复语义审核。原件保密扫描、封包与远端哈希验证由交付流程另行记录，不冒充本次独立数值检查已完成那些步骤。独立算术的 4 个边界 fixture 通过；这些不替代项目自身既有测试。
