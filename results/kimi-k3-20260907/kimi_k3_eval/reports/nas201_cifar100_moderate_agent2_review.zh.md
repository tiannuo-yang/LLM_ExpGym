# 旧 full：NAS201 cifar100 / Moderate / naive agent 2 失败复核

复核日期：2026-09-07 UTC。本报告为已留存 API content 的离线诊断，没有调用模型 API，没有更改实验源码、原始 dump 或旧结果。

## 结论

此项 `score check failed for agents: [2]` 由旧 `_extract_answer` 将 Thought 内引用的 `Answer:` 误识别为正式答案引起。当前冻结源码 `55637cee193071b35f06c3356e706d6f652de738a5340d2c4950d5966cf1a0a3` 的 Answer 行首匹配修复已覆盖：用该 agent 的全部 8 条真实响应离线重放，7 次本地 NAS201 评估后正常回答，重评分通过，分数为 `0.7129666666666667`。

该验证不生成可晋升的正式 agent trace，也不把旧失败任务标为完成。原 runner 在保存 PoolAct result / agent 文件之前因 score check 失败退出；旧结果应继续保留为执行失败证据。

## 原始证据

以下链接相对本报告目录。哈希为复核时 SHA256。

| 证据 | SHA256 |
|---|---|
| [触发 final 的原始请求与响应](../dumps/full/poolact__tuning__hpobench_nasbench201_cifar100__cost_moderate/0d249bc07ba841fc93efbfd135d0cdf3.json) | `2f2179bb86c38bb999ed03f634171b1c8f77ed23876d7c7a088954326d18b578` |
| [runner stdout / exception](../logs/full/poolact__tuning__hpobench_nasbench201_cifar100__cost_moderate/stdout.log) | `7ebb27c84f8dd617ab0e60e99dd0ecb739b91fe023583a57c00c3ecac42992f3` |
| [harness status](../logs/full/poolact__tuning__hpobench_nasbench201_cifar100__cost_moderate/status.json) | `4f11bf3286af48d3eb501ff049073c8e7c4fa9061e14f20b274f4e17f579f843` |
| [旧冻结源码包](../provenance/evaluation_api_linkage/evaluation-source.tar.gz) | `3a8e28a3e08a44b377d761207059689bac1f5297b6a330261a94fdd6742e1e33` |
| [新冻结源码包](../provenance/evaluation_recovery_v2/evaluation-source.tar.gz) | `39e0ac906f391565ff77c6040010f21815b3050bc932a88aac5857847e7e2c71` |

旧源码树：`85b569cf2505ff07e6fa7c289b3ea29ec8a35ab3a4b187e8862e7ee4afb9888a`。新源码树：`55637cee193071b35f06c3356e706d6f652de738a5340d2c4950d5966cf1a0a3`，离线复核时再次读取当前树指纹，匹配新冻结版本。

原始身份为 `strategy=naive`, `agent_id=2`, `seed=1208`, `client_id=2d2ba42f70d1407db9a35c8bd210f950`。该 job 共留存 28 个请求；本次仅重放此 agent 的 8 个请求，按 `started_at_utc` 排序如下：

```text
3fa8a39c9ea843db973cbdfe497a183c
bc8fa7c26a0d4e4ebbe6469337dcbc8e
4a66b11cafdb4c4187f9abc26990e130
5dd8a540ed524a57bce99679798fc008
a2673c3e1bd04b6faac392d25d879518
2ac72f534fab4f899c2c6ddbc6f1a52f
1c3664c1f07a4acf8ffa65b571ffde76
0d249bc07ba841fc93efbfd135d0cdf3
```

8 个响应均为 `finish_reason=stop`。最后一次请求时间为 `2026-09-07T09:25:58.860228+00:00`。harness status 在本次复核时记录 `status=interrupted`, `returncode=1`；stdout 中明确保留的是 runner 的 score-check 异常，不能仅从顶层状态名将其原因解释为用户中断。

## 精确触发链

最后响应的 Thought 包含引用：`The instruction says "Answer format: Answer: {...}" when confident.`；后面另起一行给出了合法 `Answer: {...}`。

旧 `_extract_answer` 使用 `if "Answer:" in clean`，因此先匹配 Thought 中的引用，得到以下非 JSON 答案，而非后面的独立 Answer 行：

```text
{...}" when confident. Given the constraint, I should provide my best answer now based on the evaluations so far. The best configuration found was perf=0.712967 with: 1<-0: nor_conv_3x3, 2<-0: nor_conv_3x3, 2<-1: nor_conv_1x1, 3<-0: nor_conv_1x1, 3<-1: nor_conv_3x3, 3<-2: nor_conv_3x3.
Answer: {"1<-0": "nor_conv_3x3", "2<-0": "nor_conv_3x3", "2<-1": "nor_conv_1x1", "3<-0": "nor_conv_1x1", "3<-1": "nor_conv_3x3", "3<-2": "nor_conv_3x3"}
```

`_lookup_answer_metrics` 在答案不是合法 JSON 时允许对已评估配置做原始字符串子串匹配。错误答案仍包含实际配置的完整 JSON，因此循环给它赋了已有分数 `0.7129666666666667`，也没有触发 best-evaluated fallback。严格 JSON 重评分随后返回 invalid JSON、无 numeric perf，旧 score check 报错。

新 `_extract_answer` 使用 `clean.startswith("Answer:")`，跳过 Thought 中的引用并提取独立 Answer 行，得到完整合法配置：

```json
{"1<-0":"nor_conv_3x3","2<-0":"nor_conv_3x3","2<-1":"nor_conv_1x1","3<-0":"nor_conv_1x1","3<-1":"nor_conv_3x3","3<-2":"nor_conv_3x3"}
```

## 离线复放方法与结果

在评测 uv 环境 `LLM_ExpGym/.venv/bin/python` 中设置 `PYTHONDONTWRITEBYTECODE=1`。旧循环和旧评分函数从旧冻结源码包读入内存，新循环和评分来自上述新冻结源码树。两组均使用本地 NAS201 cifar100 evaluator；LLM 替身仅依次返回原始 dump 的 `response_json.choices[0].message.content`，用尽即报错，没有网络回退。

使用 `oracle3.json` 的精确 Moderate 预算 `18639.38294943741 × 10 = 186393.8294943741`，`max_steps=30`, `max_evals=30`。旧、新循环发给替身的 8 组 messages 均与原 dump 的 `request_payload.messages` 完全相等，消息失配次数均为 0。

| 比较 | reported perf | recomputed perf | score check |
|---|---:|---:|---|
| 旧解析 + 旧评分 | 0.7129666666666667 | null | false；`missing numeric score` |
| 旧解析 + 新 InvalidConfiguration 评分 | 0.7129666666666667 | 0.0 | false；非零旧报告分数不被静默改写 |
| 新行首 Answer 解析 + 新评分 | 0.7129666666666667 | 0.7129666666666667 | true |

旧、新循环均消费 8 条响应、执行 7 次评估、`aborted=false`、`termination=Natural answer`、`answer_source=natural_model_answer`。评估分数依次为：

```json
[0.6900666666666668, 0.7090666666666667, 0.7040333333333335, 0.7087999999999999, 0.7087000000000001, 0.7129666666666667, 0.7101333333333333]
```

最终剩余模拟预算为 `51635.69541130739`；本例没有预算超限、horizon 或 provider length 截断。模型在 Thought 中声称“system says I must not call tools”不能当作实际系统限制，原最后请求末尾仅是正常 Observation。

此 dump 中未发现独立于已修复 Answer 行首解析的另一项未覆盖根因。只修 InvalidConfiguration 分类不能修好本例；现有行首解析与新评分组合则通过上述完整重放。
