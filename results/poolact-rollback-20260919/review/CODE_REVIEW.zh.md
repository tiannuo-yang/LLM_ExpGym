# POOLACT 代码回退核查

当前回退基准为 `297c3d00a006f33fc5a8ca799ce91d327d92839e`，保留单智能体采用的新版终答提取与评分。

- `expgym/poolact.py`、`expgym/extras/parallel_cache.py`、`expgym/extras/aggregation_diagnostics.py` 三份运行源码逐字节恢复基准版本。
- `expgym/poolact_legacy_tool_protocol.py` 是基准 `tool_protocol.py` 的完整逐字节副本。它包括旧 Action 识别和终答提取，防止仅恢复投票却继续使用新控制流。
- `expgym/poolact_legacy.py` 保留旧 native/forced-final fallback 顺序；Audit evaluator 是旧函数，仅将两处数据查询限定为当前 task 模块的查询函数，归一后 AST 完全相同。
- 共享 `react_loop.run_react_loop` 增加按调用选择的 `answer_protocol`；默认继续 `final-answer-boundary-v2`。N4 runner 的 naive、cached、poolact 三策略明确传入 `poolact-answer-297c3d0`，并在配置与缓存命名空间中记录；成员评分、聚合评分、恢复验证均使用 N4 旧 Audit builder。
- 使用库接口手动组装 pool 时，应显式传 `answer_protocol="poolact-answer-297c3d0"` 并选择 legacy Audit evaluator。共享 loop 的默认行为属于 N1，不能仅凭绑定共享图推断调用者意图。
- 未修改 provider、prompt、预算、缓存命中规则及冻结的修复实验 runtime；也未运行模型。

[CODE_SOURCE_MANIFEST.json](CODE_SOURCE_MANIFEST.json) 给出逐文件哈希、旧源码相等性及 N1 未改的五份入口/任务源码。[N4_RUNTIME_DIFFERENTIAL.json](N4_RUNTIME_DIFFERENTIAL.json) 比较旧基准 loop 与当前 legacy 分支的 72 个组合（18 种响应 × native/text × 自然/forced horizon），除真实耗时和新增版本元数据外，所有结果字段一致。

[CODE_TESTS.json](CODE_TESTS.json) 与 [日志](CODE_TEST_SUITE.log)记录完整离线测试：702 项，33 项由于环境/可选数据条件跳过，其余通过；包括新增的 10 项 N1/N4 并发隔离及所有池策略传参检查。根目录不再运行两份仅针对 v4 的图测试，它们在原冻结 runtime 中完整保留。单智能体 v2 parser/scorer 测试仍运行。

先前已采用的修复实验及其复算入口属于固定 `7776f700902db194c69124b1a5f59d985379cfb3`；不能在当前回退源码上把它们重新标称为同一评分版本。
