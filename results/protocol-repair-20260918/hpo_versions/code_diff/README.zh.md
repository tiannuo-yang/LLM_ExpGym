> 公开版：以下本地路径是历史来源标识。原件重放脚本需要 local archives；默认仅核公开表请运行上一级 `tools/verify_public_tables.py`。45池图等价不排除parser控制流问题：另有其中2池因parser中间终止改变已纳入97池新队列。

# HPO 历史运行代码与统一修复版本等价核查

本检查只读源代码与已采用记录，未执行模型调用、修改仓库或改写轨迹。主报告基线为 `297c3d00a006f33fc5a8ca799ce91d327d92839e`。

## 可以保留历史 v4 图实现

统一修复工作树 `LLM_ExpGym-protocol-repair-20260918/expgym/extras/parallel_cache.py` 与两个实际历史 v4 运行源 **逐字节相同**：

| 运行源 | source_tree SHA256 | Git HEAD |
|---|---|---|
| eval-docs；DeepSeek 两预算、GLM/Kimi Tight | `e96575475b66e9e25b59115301dee10d04850a1f14f9d6b4d499f0651da47a78` | `5bf5e5af817c2c6add48c7bae4eec4fe6e8110e9` |
| GPT material rerun；GPT Moderate | `88289be4903cbf1c993e1710bfe51f75aa5c4e2321069e99c652518e2f456d5b` | `7f0fe09584a57266832efa38662df7fe599f2431` |

上述 graph 文件共同 SHA256 为 `f7da6a20cdee00f47fc72632a4ba1bd86059c32c54f78a911d210bcd07ea41d7`，包括完整配置 SHA256 身份、可见快照内唯一短别名、节点文字、路径文字、可见性过滤、claims 与原锁行为；不是仅 `_eval_key` 相同。

[完整重放检查](HISTORICAL_V4_EQUIVALENCE.json) 对 45 个历史 v4 池逐份核对原件 SHA256，将 986 条已有评估记录按同一固定顺序输入三份实现。在两种图显示模式、4 个观察 agent、全部完成时间及预算边界，共 **9,568 份完整提示快照逐字节一致**。脚本为 [archive check_historical_v4_equivalence.py](../tools/local_archives/check_historical_v4_equivalence.py)。该重放证明实现等价，没有声称恢复真实线程交错或每次真实 API 输入。

因此，**仅修复图身份时，45 个历史 v4 PoolAct 池无需因图问题重跑**。如果额外修 observations/claims 两次加锁的原子性，或修改图文案、图截断、锁时序，则不再能引用本等价证明。本次已明确不并入该额外改动。

## v3 → v4 具体改变及重跑边界

[AST_RUNTIME_DIFF.json](AST_RUNTIME_DIFF.json) 和对应 `.diff` 给出逐函数差异。`poolact.py` 只更改协议版本常量，没有函数差异。`parallel_cache.py` 更改仅位于 `SharedExplorationGraph` 的构造、评估身份/显示 ID、记录评估和图格式化方法；cache 查询、计费、claim 规范化、锁调度没有随 v4 改变。

- v3 使用配置规范 JSON 前 80 字符作为边端点；v4 使用完整配置 SHA256，渲染为短且唯一的快照局部别名。
- 配置节点字典、工具结果 cache 和 claims 原本就使用完整配置；不存在可通过改最终分数解决的缓存串值问题。
- naive/cached 不调用共享图，可以在其他有效设置相同、正式终答解析后仍可接受的条件下复用既有记录。
- v3 PoolAct 的历史模型已看过不同图提示，不能离线改图后当作新运行。应按预先固定的模型×预算×任务×重复单元统一补跑，而不是只重跑观察到碰撞且得分低的记录。已确认的旧 v3 池为 63 个；61 个有前缀碰撞，60 个保存提示有歧义路径。未观察到歧义路径的 3 个也仍属于旧协议单元。

## 图以外的真实运行差异

下表依据完整运行源，而非主分支当前代码推测。逐文件 SHA 在 [runtime_source_hashes.csv](runtime_source_hashes.csv)，额外适配器与入口 SHA 在 [extra_runtime_source_hashes.csv](extra_runtime_source_hashes.csv)。

| source_tree 前缀与来源 | HPO 有效差异 | 复用/新执行要求 |
|---|---|---|
| `0671f352`，早期 GLM/Kimi v5 | native 最终非工具响应的最后 fallback 为裸 `text`；main 改为拒绝仅 reasoning/protocol 示例。客户端旧版略宽松接受 content parts。provider prompt cache namespace 派生也较旧。 | 全量重新提取终答；检查历史第一次终答是否仍可接受。若新规则会触发继续交互/重试，离线重评分不能恢复反事实行动，应另标运行时差异。正常可接受终态可复用。 |
| `c6c60cbc`，GPT 旧 API 源；`88289be4`，GPT v4 | Responses 原生适配器及 `requires_immutable_history`：完整历史超过 cap 就拒绝入场，不裁切带签名历史。main 原版缺少这一适配。 | 保留实际 Responses 适配、完整历史入场规则与原 slot cap；GPT Moderate 为 262144，Tight 为 131072。不能把 main 的 chat 客户端当作原 GPT 协议。 |
| `58f8663d` Qwen、`b040dd01` DeepSeek 早期、`e9657547` v4 | 允许 provider prompt cache 字段名 `cache_salt`，其他共享 HPO loop、任务/解码器与 main 相同。v4 源的 Audit prompt 改动对 HPO 无效。 | 保留每模型实际 `prompt_cache_key_field`、thinking、采样、请求上限等设置；routing namespace 不是反馈 cache。 |
| `8a589861` 旧 Gemini Sub2 | 原生 Gemini 客户端、不可裁剪 signed history、quota transport/部分响应终态处理。 | provider 改为 OpenRouter 后不能把旧 Sub2 baseline 默认为同批 provider 对照。 |
| `ec52a337` 新 Gemini OpenRouter | 在旧 Gemini 有效源上增加专用 OpenRouter 客户端；sweep runner 增加自定义 beta；graph 仍 v3。 | 保留固定 Google AI Studio provider、medium reasoning、提示/预算/数据；旧 OpenRouter naive/cached 若其他参数一致可复用，PoolAct 必须修图重跑。 |

`task_tuning.py`、`compact_nasbench101.py`、`compact_nasbench201.py` 在所核的旧/新运行源中相同；`tool_protocol.py` 除 `0671f352` 缺失更严格 unlabelled fallback 外，历史来源均相同。新正式提取规则另属评分协议变更，不能仅看文件 SHA 不同就要求重跑所有基线，也不能在历史终态会被拒收时宣称整个交互完全等价。

三类新增适配器在主报告旧 main 缺失：`native_responses_client.py`、`native_gemini_client.py`、`openrouter_gemini_client.py`；新统一执行树须明确采用并记录这些代码，不能静默回退为 chat API。历史 GPT 与 Gemini 基线的 Responses 适配器本身 SHA 相同，均为 `45a592ada5863ef1f281c5b462616991fac7d683ec7971fe4760f398f3233265`。

## 复算

```bash
python3 tools/local_archives/check_historical_v4_equivalence.py --workspace /path/to/original/workspace --output /tmp/hpo-v4-replay
```

路径是本地归档定位；公开交付应同时保留 source_tree 身份、对应 Git 提交/源码快照索引及源文件 SHA，避免把当前 Git HEAD 误当历史实际执行源。逐模型、预算、策略、slot 的最终矩阵由上一级 HPO 版本审计产物提供。
