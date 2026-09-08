# Kimi-K3：修正任务提示后的真实兼容性验收

2026-09-08 UTC。分类：**Real smoke validation / Custom study**。
这是已完成的小规模验收，不是正式性能矩阵；尚不能据此认定 ExpGym 退化、PoolAct 提升或跨模型泛化。

固定范围：三个场景各一个 Moderate 单代理任务，加同一场景的 naive/cached/poolact、每池两个 agents；共 21 条轨迹、9 个池结果。每 agent 最多 3 个普通步骤、2 次工具评估。K3 使用 native 工具、T=1、top-p=1、max output=32768、thinking/max；请求 seed 仅为标签，不承诺确定性。

| 检查 | 结果 |
| --- | --- |
| 独立原 evaluator 重评分 | 21 条轨迹、9 个池结果全部一致 |
| 只读恢复 | 12 次 verified skip，受保护结果/raw 字节与 mtime 不变 |
| 实际任务提示、schema、完整历史 | 全部通过，12 个预定格内调用路径覆盖完整 |
| 原始请求/响应与服务日志 | 63/63 双 SHA 唯一匹配，HTTP 200 且连接关闭完成 |
| 协议错误 / 协议修复 / HTTP 重试 / length | 0 / 0 / 0 / 0 |
| 有效零分 | 7 个，全部保留 |
| 实际 wall time | 1681.441 秒，28.02 分钟 |
| input / output / total tokens | 301,867 / 125,228 / 427,095 |

111,048 reasoning tokens 已含在 output，不重复累加。prefix-cache 用量未报告，不能补零或断言未命中。观测到的完成请求峰值并发为 6；单请求最长 473.37 秒。上述是实际工作流耗时，不是饱和 serving 吞吐，也不能直接外推正式矩阵 ETA。

## 查验入口

- [完整原始运行目录](evidence/scenario/k3_native_context_1203474_v3/)：计划、日志、21 条轨迹、9 个池结果及全部 63 次 dump。
- [独立重评分及 prompt/history 终审](receipts/scenario_smoke_v3_independent.json)与 [raw/attempt 终审](receipts/scenario_smoke_v3_raw_independent.json)。审计复用冻结原 evaluator，不是另写一套评分定义。
- [router 双 SHA 对账](receipts/scenario_router_rawjoin_v3/final_20260908T0517Z/receipt.json)、[全部用量](receipts/scenario_router_rawjoin_v3/final_20260908T0517Z/usage_runtime_receipt.json)、[服务排空观察](receipts/root_drain_20260908T0517Z.json)。路由快照还含旧运行的 228 条窗外记录，未计入本轮 63 次用量。
- [提示集成遗漏的归因报告](review/NATIVE_CONTEXT_INTEGRATION.zh.md)、[实际 harness](source/harness/scenario_smoke_v3.py)及 [测试](source/harness/tests/test_scenario_smoke_v3.py)。原始报告保留原工作区路径；浏览本次产物可用本页相对链接。
- [本增量逐文件清单](MANIFEST.json)与[先前检查点的 v3 源码包](../../source/accepted-source-v3.tar.gz)。源码指纹为 `d1606db7d6036c8975ce9d3e556daf7fa2ce4604879f2b3878435b0f96aebb78`。

## 能说明什么，不能说明什么

上一轮的系统提示要求 native 调用，但任务 user context 仍要求文本 Action；这是本地适配的集成遗漏，不应一概归因于模型或上游。本轮只改源码自有协议指令，保留任务数据、预算、Answer 格式、默认 text 行为和 legacy 评分。完整原始提示现在通过检查，但有限 smoke 不能证明不存在其他 bug，也不能给出该遗漏对旧分数的反事实影响量。

原 56-call strict gate、8-call 诊断和 45-trace 旧场景记录仍在[先前检查点](../../README.zh.md)，没有覆盖其失败状态。原 540 个已发布文件保持逐字节不变。本增量不包含正在运行的 A21 计时、未执行的 B/C、正式矩阵或第二模型结果。库根目录仍为原上游快照；运行本轮版本须使用精确源码包和对应环境/数据身份，不要把分支根目录误认为修正版 checkout。

数据归属及许可证继续遵循[原检查点 ATTRIBUTION](../../ATTRIBUTION.md)；未发布模型权重、API key、环境或缓存。
