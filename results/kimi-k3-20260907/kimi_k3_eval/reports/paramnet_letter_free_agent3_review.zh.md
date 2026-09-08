# 旧 full：PoolAct ParamNet letter / cost_free / naive / agent 3

结论：该失败属于已修复的 `Answer:` 行首解析问题，没有发现第三个根因。冻结新源码 `55637cee193071b35f06c3356e706d6f652de738a5340d2c4950d5966cf1a0a3` 已覆盖该实际回答。

## 原始证据

所有路径均相对于 `/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/`。

| 原始文件 | SHA256 |
|---|---|
| `dumps/full/poolact__tuning__hpobench_paramnet_letter_steps__cost_free/072a9e5619574f9e8c873270cc889cb9.json` | `5861d1be340dfe26ecd49532f26ed55f67a8f23f8c68614149df535237db0651` |
| `logs/full/poolact__tuning__hpobench_paramnet_letter_steps__cost_free/stdout.log` | `28cd8a23823ea1d3581803f608082ade9d30310d452037c64c8f6fbf3ecb9510` |
| `logs/full/poolact__tuning__hpobench_paramnet_letter_steps__cost_free/status.json` | `6da2aac661d5664e43cc751546c6ad6b7b02edf90568101b9f045dd5c5cb9c2d` |

日志报告 `RuntimeError: score check failed for agents: [3]`。agent 3 / seed 1209 共 4 次成功 API 返回，时间依次为 09:20:24、09:20:32、09:20:41、09:20:50 UTC。

末次回答先在正文中引用规则 `The rule says "When confident in your final answer, reply with ONLY: Answer: <your answer>".`，随后才输出真正的行首 `Answer:` 和完整 JSON。最终配置为：

```json
{"average_units_per_layer_log2":8.0,"batch_size_log2":5.5,"dropout_0":0.25,"dropout_1":0.25,"final_lr_fraction_log2":-2.0,"initial_lr_log10":-4.0,"num_layers":5,"shape_parameter_1":0.5}
```

## 失败机制

旧 `_extract_answer` 接受任意位置的 `Answer:`，因此返回从引用里的 `<your answer>` 开始的一大段正文。该正文包含最终 JSON，`_lookup_answer_metrics` 的子串匹配分支又把第 3 次工具性能关联给它。由于已有非空性能，最佳已评估配置 fallback 不会发生。独立评分将整段正文作为 JSON 解析失败，于是非零已有性能不能通过评分检查。

新解析器仅接受经既有标签规范化后位于行首的 `Answer:`，提取完整 JSON，独立重算与第 3 次工具性能完全相同。

## 离线复核

使用 `data_runtime/run_hpo.sh -` 的 Python 3.7 / 固定 HPO 数据和 ConfigSpace 环境，fidelity 为 `{"step":50}`。旧解析器与旧评分函数从 `provenance/evaluation_api_linkage/evaluation-source.tar.gz` 读取 AST 后仅在内存中加载；新函数来自当前冻结仓库。工具执行使用当前固定 ParamNet evaluator，三个合法输入不涉及本轮非法输入协议调整。未调用 LLM API，未修改仓库、原始 dump 或正式结果。

| 离线重算对象 | 性能 | 模拟原始 cost 秒 |
|---|---:|---:|
| 第 1 次默认配置 | 0.4752600696879725 | 25.136411786079403 |
| 第 2 次 units=7 / layers=4 | 0.6843509736285119 | 40.91113908290863 |
| 第 3 次 units=8 / layers=5 | 0.7092944375216987 | 126.11017372608187 |

| 实际最终回答处理方式 | `score_check.ok` | `reported_perf` | `recomputed_perf` | 原因 |
|---|---|---:|---:|---|
| 冻结旧解析器 + 冻结旧评分函数 | false | 0.7092944375216987 | null | missing numeric score；提取文本不是 JSON |
| 冻结新解析器 + 冻结新评分函数 | true | 0.7092944375216987 | 0.7092944375216987 | 正确提取已评估的最终 JSON |

这是故障解释及离线回放证据，不是新增模型运行结果，也没有把该旧失败任务标成正式通过。
