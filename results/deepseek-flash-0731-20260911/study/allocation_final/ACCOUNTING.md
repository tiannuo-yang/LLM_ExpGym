# 实际 Slurm allocation 账本


| job_id | state | start_utc | end_utc | observed_elapsed_seconds | final_elapsed_seconds | allocated_nodes | allocated_gpus | model_replicas | allocation_gpu_hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1204605 | CANCELLED | 2026-09-11T03:46:08Z | 2026-09-11T04:09:11Z | 1383 | 1383 | 4 | 32 | 4 | 12.293333333333333 |
| 1204607 | CANCELLED | 2026-09-11T04:09:47Z | 2026-09-11T06:50:36Z | 9649 | 9649 | 4 | 32 | 4 | 85.7688888888889 |

采集状态：passed；完整 allocation GPU-hours：98.06222222222223；known/expected allocations：2/2；仅已知子集合计：98.06222222222223。

只按唯一顶层 Slurm job 的实际 AllocTRES GPU 总数 × 终态 ElapsedRaw 秒 ÷ 3600 计算。四个模型副本不是四个 allocation，不额外乘副本数。
RUNNING 或缺少实际起止/elapsed/GPU 字段时，最终成本保持 unknown；observed elapsed 仅保留查询时观测，不外推当前时间。时间戳区间不替换 Slurm ElapsedRaw。
deployment 含原始 plan SHA；仅有 submission 的早期失败记录采用操作员显式 plan 关联，不声称 sbatch stdout 自身证明了实际使用的 plan。查询或解析失败会保留全部原始输出、成本置 unknown，并非有效的完整账本。
包括加载、smoke、正式运行、等待与失败启动所属分配时间；不是 formal-only 成本、有效计算量或 GPU 利用率。原始查询命令、全部 sacct 行、被排除的 step/重复行及绑定见 [ACCOUNTING.json](ACCOUNTING.json)。
