# K3 节点故障：8项影响索引

仅据三个外部SHA固定的元数据原件核对。**705个计划invocation均恰有一条report：697 completed_scored，8 infrastructure_or_integrity_failure；8项ID及顺序与ROOT事件完全相符。** 这里核的是分类/计划覆盖，不是评分正确性或原件完整性。

ROOT元数据记录 Slurm 1203653 于2026-09-09 14:25:32 UTC为NODE_FAIL，失败节点azure-uk-hpc-H200-instance-003；底层原因仍unknown。本轮未查询Slurm或读取节点/模型日志，不能独立归因每个失败的网络细节。

## 全部受影响项

均为第三次预定重复，即zero-based outerrep=2；下表数字只是sampling seed labels，不证明逐token可复现。N表示每项计划agent槽位，不表示已经落盘或确实丢失的agent数量。

| # / invocation ID前缀 | 系统 | task | cost regime | strategy | outerrep | seed labels | N |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 / `2db6e0051763` | ExpGym | NAS101 C | moderate | single | 2 | 2208 | 1 |
| 2 / `2128eec1bc88` | ExpGym | NAS101 C | free | single | 2 | 2208 | 1 |
| 3 / `dbf6b81b2b56` | PoolAct | NAS101 C | moderate | cached | 2 | 2208, 2209, 2210, 2211 | 4 |
| 4 / `8d34d8906662` | PoolAct | NAS101 C | moderate | naive | 2 | 2208, 2209, 2210, 2211 | 4 |
| 5 / `17e194780d35` | PoolAct | NAS101 C | tight | poolact | 2 | 2208, 2209, 2210, 2211 | 4 |
| 6 / `1926939d7c70` | PoolAct | NAS101 C | moderate | poolact | 2 | 2208, 2209, 2210, 2211 | 4 |
| 7 / `70994c0fc3e6` | PoolAct | NAS101 B | moderate | poolact | 2 | 2208, 2209, 2210, 2211 | 4 |
| 8 / `f41fd4716d94` | PoolAct | NAS101 A | moderate | poolact | 2 | 2208, 2209, 2210, 2211 | 4 |

完整ID、logical ID、固定selector argv、同条件三个repeat分类、输入路径/SHA见 [8项元数据](FAILED_INVOCATIONS.metadata.json)。逐项核对了plan实际command与selection_argv：Exp使用plural `--tuning-tasks/--cost-regimes`，Pool使用singular `--tuning-task/--cost-regime`；没有为修复重新拼runner。

## 缺失范围与未受此事件影响的覆盖

- 8项=2个Exp单agent任务+6个N4池，共8 logical、26个计划agent槽位。**不据此断言26个agent都没有结果或所有partial原件可复用**：本轮不打开原agent文件。
- 前两重复块的分类为outer0：615/615 completed_scored，outer1：45/45；outer2：37/45 completed_scored、8项失败。上述8个固定task/预算/strategy条件都只有前两次完成状态，第三次缺完整执行证据，不能当R3完整或用前两次平均冒充三次。
- Search：Exp 219/219、Pool 234/234 invocation均为completed_scored；Audit：Exp 39/39（计划含117个fixed-order logical）、Pool 78/78（default order）同样全部为该状态。合计570 invocation无本次失败项；**这仅是状态覆盖，不是效果、无缺答或fresh质量验收**。
- tuning：Exp 79/81、Pool 48/54为completed_scored。整体原execution_complete和score_complete仍false；不把705 reported误写为全量成功。

选择依据只有`reports[].decision.classification`中的**全部**infrastructure_or_integrity_failure，未依据答案、分数、比较方向或可恢复程度筛选。分类原文仍包含“or integrity”，而不是用本索引重分类它们。

## 原件与授权边界

只打开ROOT_TERMINAL、固定plan、固定execution三个文件；JSON解码后execution仅投影`reports[].invocation_id/decision`并计数，未访问`report`内部内容。未跟随其中其他refs，未读raw、质量、源日志、数据库或key；无模型、API、评分器、Git、Slurm或生产CLI执行。

所有8个失败及其partial原件原位保留，无覆盖、删样本、补零、隐式重试或费用清空。此索引**不表示旧执行可直接resume**，不创建新allocation/runner/GO，不授权合并新旧结果。记录时用户是否允许新8×8部署及补这8项仍待决定；后续许可必须另行明确，不能由本报告推断。

三输入SHA在读取及交付前保持一致。初次纯元数据计数把decision dict直接传给Counter而退出1；随后改取classification并完成断言，未读取报告payload。该失误在元数据中保留，不隐去或冒称首命令通过。

