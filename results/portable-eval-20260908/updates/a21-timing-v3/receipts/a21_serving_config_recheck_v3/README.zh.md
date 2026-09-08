# A21 后服务配置只读复核

结论：**检查范围内未发现明显配置错配；尚未证明性能最优。** 新[回执](receipt.json) SHA256：`7596db3124f53ec3b5fc2e05e7f880df225c0f8759d5ded599607a2e0643e8c1`。本次仅读取既有文件、Slurm 状态和一次带认证的 router `/health`，未生成、修改服务、创建 Slurm step 或分配 GPU。

## 64 张 GPU 实际如何使用

Slurm job `1203474` 的 8 个节点、8 个模型 step 仍在运行，每个模型 step 对应 1 个节点/8 张 GPU。router 的 overlap step 复用已有节点，不是额外分配 GPU。

实际布局为 **4 个副本 × 每副本 2 节点/16 GPU，TP16 / EP16 / PP1**。一个请求由一个 16-GPU 副本处理，不会同时利用全部 64 张卡；其余副本提供请求并发能力。

8 份节点启动日志的实际 `ServerArgs` 一致：FA3 attention、Marlin MoE、PyTorch sampler、`enable_deterministic_inference=true`、seed 42、CUDA graph 启用、DP1、K3 reasoning/tool parser。各副本首节点日志覆盖 TP0–7，第二节点覆盖 TP8–15；4 份冻结服务源 SHA 与 deployment 相同。8 份启动硬件验收实际记录 **64 个不同 H200 UUID**、每卡 143771 MiB；物理设备与 CUDA 可见设备集合当时相同。

这些证据的路径、SHA、日志行号、启动命令及当前 Slurm step 明细均写入回执。06:04:20 UTC router 为 4/4 healthy、inflight 全 0、无 cleanup quarantine。当前模型 worker 的 PID/命令行未直接取得：登录节点 `scontrol listpids` 未查到节点任务，SSH host-key 校验拒绝连接；未绕过校验或新增 srun。当前运行状态依据控制器的现有 step 和 router metadata，64 UUID 属于启动时硬件实测，不伪称刚刚重测。

## A21 实测负载与等待

21 条 trace、248 请求、1852.227 秒（30.87 分钟）。输出 160442 token，其中 provider 报告 reasoning 119939 token，约占 74.76%；reasoning 已包含在输出中，不能重复计数。

| 副本 | 请求数 | 输出 token | HTTP 平均秒 | HTTP 累计秒 | 输出/HTTP 累计秒 |
|---|---:|---:|---:|---:|---:|
| 0 | 55 | 37073 | 22.21 | 1221.40 | 30.35 token/s |
| 1 | 98 | 45382 | 14.92 | 1462.10 | 31.04 token/s |
| 2 | 66 | 41329 | 20.49 | 1352.41 | 30.56 token/s |
| 3 | 29 | 36658 | 41.07 | 1191.03 | 30.78 token/s |

请求数不是等量工作：副本 3 请求更少但每条输出更多，因此不能仅凭其平均 HTTP 更长就判定副本故障。四者输出/HTTP 累计时长相近；这是端到端速率，**不是纯解码速度**。跨副本 HTTP 累计时长互相重叠，也不是总运行时间。

该阶段 router 完整区间峰值仅 **总共 4 条、每副本 1 条**。四个副本分别留有 927 / 1134 / 1033 / 916 条解码日志样本，样本的 running 全是 1、queue 最大 0；日志解码吞吐中位数分别为 31.51 / 32.99 / 31.28 / 31.42 token/s。这是低 batch 工作负载，尚未检验多请求合批与饱和吞吐。日志中存在 cached-token prefill，不应把成功 dump 的 `prompt_tokens_details=null` 当成无缓存证据；分块 prefill 可产生多个样本，样本数不是独立请求数。

实际请求输出上限均为 32768，最大已报告输入/输出为 26862 / 7093，未报告 `finish_reason=length`。[既有容量回执](../capacity_snapshot_v2/capacity_receipt.json)仍有效且未改动：声明 context 524288，但每副本共享 token 容量 268448、有效 running-request cap 为 47，不应把声明 context 或配置的 64 个请求槽当作本次实际并发。

## 不能据此保证的事项

- 没有逐请求 TTFT 或纯解码计时。HTTP 包含队列、分词、prefill、decode、网络等，扣除本地工具/脚本耗时后仍不能称为 pure decode。
- 周期解码/prefill日志没有逐请求唯一关联，无法精确拆分通信、kernel、prefill 等开销；没有受控比较其他 attention、量化、并行布局或 sampler 的性能。
- 长 reasoning 是实际输出负载，不是关闭思考模式的反事实测试；不能直接按 reasoning 比例承诺提速幅度。
- 当前已经 drain，空闲 GPU utilization 无法证明运行期间 GPU 利用率。此次没有采集 GPU utilization/功耗/时钟曲线。
- 先前严格重复性测试失败仍保留；deterministic/PyTorch 参数正确不等于真实逐字一致。A21 属于 `seed_labels_only` 的计时试验，不是正式效果结论。

## B 阶段可用的只读监控预案（未启动）

由 root 单独授权 B 后，将监控时间严格限定在 B 的真实请求窗口，继续使用既有 router receipt 与 rank 日志记录并发、队列、prefill 和 decode 样本；不额外发送性能 probe。若需 GPU 曲线，先取得可信的节点访问方式，再由 root 授权通过既有访问通道只读采集每 GPU 的 UUID、utilization、显存、功耗、时钟及 owned worker PID，按 UTC 与请求窗口对齐。不要绕过 SSH host-key 检查，不自动提交新的 Slurm step，不在 drain 后的数据上推断活跃利用率。
