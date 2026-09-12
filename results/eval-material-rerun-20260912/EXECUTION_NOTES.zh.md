# 本轮实际设置与登记计划的解释

本文补充实际执行事实，不修改启动前冻结的 [PLAN.zh.md](PLAN.zh.md) 或 [动态执行契约](EXECUTION_CONTRACT.zh.md)。最终分数见 [主报告](README.zh.md) / [详细报告](DETAILS.zh.md)，原件与全部尝试见 [完整索引](ARCHIVE_INDEX.md)。本轮仅复核登记的 369 个 N4 池，不是重新运行全部五模型单体矩阵。

## 重要的计划假设与实际差异

- **HTTP 重试：实际四个模型均为 `max_retries=2`。** 原 PLAN 中的 52,452 物理尝试上限以“自托管 retry=0”为条件，不是实际配置。本轮每成员最多 30 个普通决定加 1 个 forced final，1,476 成员对应最多 45,756 个逻辑决定；按每决定最多三次传输，正式有效槽位的物理尝试理论界为 137,268。启动/健康检查和明确登记的原 GPT 失败尝试另计。实际请求和 token 用量读资源账本，不用该理论界估计耗时。
- **GPU 启动不是模型间串行接力。** 三个自托管模型曾同时运行，峰值 12 节点/96 张 H200。每模型最多四节点：GLM/Kimi 各两个 TP16；DeepSeek 沿用已验证的四个 TP8/PP1/EP1。完成后按模型分别释放，不能把正常释放造成的 Slurm `CANCELLED` 当作实验失败。
- **并发只调整调度，不调整科学设置。** 自托管初始各 8 个独立池；DeepSeek 于 06:00:47 UTC 调为 16，GLM 于 06:56:11 UTC 调为 12，均在资源观察后维持；Kimi 保持 8。GPT 固定首池后，剩余原槽位使用并发 2。PoolAct 同池的模型决定仍按原锁串行，不能将 active pools×4 当作恒定并行请求数。
- **GPT 有一次显式基础设施恢复。** 原首池因本研究节点缺少 loopback tunnel，产生 12 次 ConnectionRefused；保留原件，建立本研究独立转发后，以新物理任务恢复同一科学槽位。最终 27 科学槽对应 28 个物理池尝试；并未添加第 370 个槽，也没有按成绩重抽。失败请求未报告的 usage 保持 unknown，不填零。

实际 endpoint、节点、启动/释放时间、运行时和模型参数由各 [模型索引](ARCHIVE_INDEX.json) 链接的 serving metadata 与原 bound plans 给出。模拟反馈秒、重叠请求 wall 之和、allocation GPU-hours 是不同量；allocation 包含加载、JIT、空闲和排空时间。

## 修复、源码和模型适配的边界

自托管 runner 使用 Git `5bf5e5af817c2c6add48c7bae4eec4fe6e8110e9`，可执行代码与 `b3382b1c0b89ef1637e232f4b7eef68d55a54f12` 相同；source-tree SHA 为 `e96575475b66e9e25b59115301dee10d04850a1f14f9d6b4d499f0651da47a78`。通用修复包括：

1. 用完整配置身份区分 graph 节点，修复旧 `config_key[:80]` 的碰撞；模型可见图使用短别名，内部身份不截断。不是针对某个模型的分数分支。
2. native Audit 提示只描述当前任务的合法调用，移除固定示例调用和与 native 接口冲突的文本格式指令；legacy 文本接口不随之改写。这属于接口兼容修复。

DeepSeek 另使用已验证的部署候选 `SGLANG_OPT_USE_MULTI_STREAM_OVERLAP=0`，保留原固定 runtime 与 0731 encoder。它是 serving 层的针对性兼容设置，不是 PoolAct 算法里针对 DeepSeek 的特殊待遇。旧新之间同时存在源码、提示和部署变化；不能把性能差全部归因于其中一个补丁，也不声称已唯一定位某个 kernel 的原因。

GPT 使用实际旧 API 分支 `ccaf6adb8f7e82fa0f33d97c06cf5f7a33592122` 的独立派生版本 `7f0fe09584a57266832efa38662df7fe599f2431`，source-tree SHA 为 `88289be4903cbf1c993e1710bfe51f75aa5c4e2321069e99c652518e2f456d5b`。两者之间仅移植相应通用修复及测试，保留 native Responses 的 opaque/encrypted history 和原 wire 省略规则。

这两个 GPT 本地 commit 不冒充已经独立公开的源码版本。可公开重建入口是 [GPT 包的来源补丁](bundles/gpt/source_delivery/source-0d3c299-to-7f0fe09.patch) 与 [来源说明](bundles/gpt/source_delivery/source-provenance.json)：从已公开 `0d3c299f0352ddd53bc012c787d3da81db529d89` 应用 exact patch。补丁也包含旧 API 分支原已有的兼容代码；不能将全部补丁文件都算成本轮新修复。

## GPT context 设置不是实际 wire 容量承诺

所有新 GPT 三策略统一使用本地近似 admission cap **262144**，旧值为 131072；effort 仍为 medium。原生历史不裁剪。实际 wire 的 `max_output_tokens`/`max_tokens`、temperature、top_p、top_k、seed、prompt_cache_key 仍按原 API 分支省略；计划中的 nominal max_tokens 不代表发送给 provider 的输出上限。

离线检查表明，旧被本地拒绝的请求可通过新的 admission 阈值；本轮 GPT 108/108 成员均评分完整。但未重新扫描全部 raw 以统计本地 heuristic 峰值，首个恢复池也未实际越过旧的 131072 阈值。因此不将本轮称作网关真实 262144 容量压力测试；provider input token 数也不能替代本地 heuristic 数。

## 保留的评分约定与解释限制

本轮保持 legacy / task-abstention-v1，以维持与旧对照的契约一致；未升级 task-abstention-v5。正常 NAS 无最终配置在严格端点保持 unknown，另列事先授权的 Gap0 部署效用敏感性；基础设施失败不赋零。Search/Audit 沿用其原评分器对空预测的处理，不将所有空答一概设为零。

另一个保留的 legacy 行为是：提交的 peer 配置不在自身 trace 时，NAS 评分可能回退自身 best。它不等同于重新评估所提交配置。本轮没有改变这个旧约定，也没有事后为缺答者填入轨迹最优答案；详细结果应在此评分边界下解读。完整评分只能排除相应的缺答/未知问题，不能据此断言不存在任何其他评价局限。

本轮实际启动池检查和既有公开 GPU/CPU 验证提供工程证据；例如一个真实 DeepSeek NAS 池的 29 个不同可见配置，在旧截断规则下只剩 4 个标签，新标识保留 29 个。它是同一轨迹上的结构反事实，不是旧轨迹重评分或单补丁性能因果实验。内容检查是有界检查，不冒充审核了全部生成文字。

最终独立复核从固定来源核对身份、分母、保存标量和聚合；不重新调用评分器，也不按新结果挑样本。所有正、零、负与 unknown 均保留。Free→Tight 退化与 ranking reshuffle 仍明确引用冻结旧五模型 cohort，本轮不能更新单体模型排行榜。
