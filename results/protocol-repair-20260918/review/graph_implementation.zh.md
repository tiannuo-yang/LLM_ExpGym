# HPO PoolAct 图身份正式修复

本轮将主代码的图实现统一为 `paper-graph-lock-v4`：`expgym/extras/parallel_cache.py` 与已经用于部分历史实验的 v4 实现逐字相同。源码 SHA-256 为 `f7da6a20cdee00f47fc72632a4ba1bd86059c32c54f78a911d210bcd07ea41d7`。协议常量由负责整合 PoolAct 与终答协议的代码修改统一记录；终答提取另行版本化，不能把新的终答规则误称为历史图协议。

## 改了什么

- `_eval_key` 使用完整规范化配置的完整 SHA-256；不同长配置不再因为前 80 个字符相同而共用路径节点。遇到完整摘要碰撞时，在修改任何图状态之前报错。
- 长配置显示为 `E:h:<摘要前缀>`，前缀从 12 位起，遇到冲突时对整个冲突组同时延长。节点观察行和路径端点使用同一映射；短配置沿用原 JSON 显示名。稳定的是完整内部身份，显示别名保证在当前可见快照内唯一。
- 显示名只根据已通过时间与严格预算过滤的节点生成；隐藏的未来结果不会使过去的别名改变。
- 没有修改缓存 key、claim key、工具结果、费用、时钟推进、预算边界或物理调度。58 个其他函数相对原主线的 AST 完全相同。

本轮**没有**合入 observation 与 pending claim 的原子快照修改。两次锁读取之间的竞争仍是已披露的独立问题；若后续修改，需要新图协议及相应运行对照，不能声称 v4 已修复。此次选择与历史 v4 保持同一运行协议，避免同时引入另一项信息共享改变。

## 实际记录回归

新增 `tests/fixtures/poolact_gemini_graph_collision.json` 来自真实采用的 Gemini OpenRouter、NAS101 A、Moderate、第三重复，slot `e10db734b2d3d4788dc8c5eb`、agent 0、message 5。源结果 SHA-256 为 `ecb56ee8107ac21106da1449d3e8e75e6ff0a4a3698bfadceca9a68691e35922`；fixture 记录源消息哈希，只含该次可见图需要的配置/性能与 pending 信息。

该快照的两份配置仅在 `edge_15` 不同，旧显示共用同一路径端点；修复后分别显示 `E:h:963d973a97b5` 与 `E:h:89032d4ba830`。保存的 agent 0 路径正确指向后者，即实际评估的 `edge_15=1` 配置。5 个可见节点、3 个 pending claim、观察性能、成员归属、Coverage Gap 文本保持一致。

- [修复前显示](graph_observed_before.txt)
- [修复后显示](graph_observed_after.txt)
- [来源与检查结果](graph_implementation_checks.json)

这些文本是已有可见观察的**展示重建**，不是模型反事实运行，也不是正式新分数。模型当时已经看过的错误路径可能改变后续决策；离线重新绘图无法消除该影响，必须采用统一版本补跑必要对照。历史全量版本归属与受影响样本清单由本轮来源分析单独导出。

## 验证

```bash
python3 -m unittest discover -s tests -p 'test_poolact_graph*.py' -v
```

19 项图专项通过，其中 18 项完整图身份回归来自历史 v4，另新增 1 项真实保存提示回归。覆盖长配置碰撞、真实自环保留、转移计数、80/81 字符边界、人工摘要前缀/完整碰撞、隐藏未来别名、严格预算与零费用缓存。[图专项测试日志](graph_identity_tests.log)。在正式终答协议冻结后再次运行全部 PoolAct 测试，84/84 通过，见 [完整测试日志](graph_poolact_tests.log)；对应核心修复提交 `0e6c51b6d86f42437038518c2fc8adc510901c0b`

独立复核还使用 163 种配置、1,000 条事件及 14 个时间/预算快照，分别从每成员完整配置序列推导路径和计数，全部相同；12 次追加隐藏未来节点不改变过去图文本，旧/新 wrapper 的工具调用、缓存、费用、时钟与 claims 一致。见 [独立复核](graph_identity_independent.zh.md) 与其可复算脚本。

以上检查不调用模型或评估器，没有修改原始 trajectory、旧分数或已采用结果。补跑采用范围与正式新成绩由整合报告给出。
