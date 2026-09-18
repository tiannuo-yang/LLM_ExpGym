> 历史规划快照：本文件保留 parser 全量控制流审计前的 94 池方案，当前正式选择为97池，见本目录 README.zh.md。科学配置公开版已做字段白名单导出。

# HPO 采用版本、图碰撞与必要补跑矩阵

本目录是修复前采用样本的版本审计及执行计划，不是新实验结果。范围为主报告已经采用的 **486 个 N1 槽和 324 个 N4 槽**；N4 每槽 4 个成员，共 1,782 条成员轨迹。已逐份验证 810 个原件 SHA256、810 个执行 `source_tree_sha256` 与现存冻结源码完全一致，并实读校验 197 项去重后的任务配置、预算 oracle、数据表、解码器和表清单。所有检查通过，见 [CHECKS.json](CHECKS.json)。

## 逐槽记录与执行矩阵

- [hpo_all_slots.csv](hpo_all_slots.csv)：810 槽的模型、预算、策略、重复、源文件及 SHA、源码版本、运行协议、上下文上限、生成设置、任务与环境身份、碰撞证据、计划处理方式。
- [hpo_model_budget_strategy.csv](hpo_model_budget_strategy.csv)：每个模型 × 预算 × 策略的版本汇总；同组有多个源码版本时全部列出，不以单一标签掩盖混用。
- [module_hashes.csv](module_hashes.csv)：历史执行版本的关键模块 SHA256。完整源码树匹配后才记作 `verified_complete_tree`。
- [input_hashes.csv](input_hashes.csv)：任务输入元数据记录与当前本地源文件的实算 SHA256 对照。
- [hpo_rerun_slots.csv](hpo_rerun_slots.csv)：94 个明确需要新运行的 N4 槽；每槽原始配置见 [HPO_SCIENTIFIC_SETTINGS.json](HPO_SCIENTIFIC_SETTINGS.json)。该配置只用于重建旧设置，新的代码版本、图协议与实际 provider 必须另行记录。
- [archive audit_versions.py](tools/local_archives/audit_versions.py)：离线复算上述审计，无模型调用；依赖本地冻结 trajectory、历史源码及数据表。

`code_commit` 仅填原轨迹记录的 commit；历史 N4 多数只记录完整 source-tree hash，空 commit 不伪造为某次当前 Git HEAD。代码身份以完整 source-tree SHA 和模块 SHA 为准。路径列是本地来源定位，不代表必须公开原始大文件。

## 图碰撞的实际范围

N4 的三策略全部覆盖 NAS101 A/B/C、Moderate/Tight、每任务 3 次重复。下表每行的三个策略各有 9 槽；协议列反映 config 中记录的代码版本，但图只被 PoolAct 使用。`naive` 与 `cached` 不消费图路径。

| 模型 | 预算 | 历史协议 | PoolAct 前缀碰撞池 | 实际歧义路径池 | 同名自环池 |
|---|---|---|---:|---:|---:|
| DeepSeek | Moderate | v4 | 9 | 0 | 0 |
| DeepSeek | Tight | v4 | 8 | 0 | 0 |
| Gemini | Moderate | v3 | 9 | 9 | 9 |
| Gemini | Tight | v3 | 8 | 8 | 5 |
| GLM | Moderate | v3 | 9 | 9 | 9 |
| GLM | Tight | v4 | 9 | 0 | 0 |
| GPT | Moderate | v4 | 9 | 0 | 0 |
| GPT | Tight | v3 | 9 | 8 | 7 |
| Kimi | Moderate | v3 | 9 | 9 | 9 |
| Kimi | Tight | v4 | 9 | 0 | 0 |
| Qwen | Moderate | v3 | 9 | 9 | 9 |
| Qwen | Tight | v3 | 8 | 8 | 7 |

63 个 v3 池中，61 个有不同完整配置共享前 80 字符，60 个在保存的模型输入中实际呈现歧义路径，55 个呈现同名自环。44 个 v4 池也存在这种字符前缀重复，但 v4 使用完整配置 SHA256 身份，因此没有相应路径歧义；前缀重复本身不是 v4 缺陷。

碰撞影响模型可见共享图、路径和后续行动，不改变底层完整 key 的观测字典、评估值或缓存 key。不能事后改几条图文本，再把旧模型行动和分数宣称成修复后的运行。必要的新运行按**完整协议队列**选择，不只挑 60 个已观察到碰撞的池，更不按旧成绩选择。

## 最小充分干预：94 个新池，376 个成员

统一修复只采用历史 v4 的完整 SHA256 identity 和可见快照唯一短 alias，不合并原子快照等其他行为改变。45 个既有 v4 PoolAct 池的两个历史源版本与目标修复版 `parallel_cache.py` **字节完全一致**，SHA256 为 `f7da6a20cdee00f47fc72632a4ba1bd86059c32c54f78a911d210bcd07ea41d7`。从这 45 池的 986 条评估记录按共同确定性顺序重放，双显示模式、4 个观察者及完成时间/预算边界产生 **9,568 个完整快照，全部逐字节一致**，包括节点显示、路径、claims 和可见性。证据：[HISTORICAL_V4_EQUIVALENCE.json](code_diff/HISTORICAL_V4_EQUIVALENCE.json)。这证明代码语义等价，不声称重建了历史真实线程交错。

| 模型 | 重跑 PoolAct | 追加 naive | 追加 cached | 新池合计 | 原因 |
|---|---:|---:|---:|---:|---|
| Gemini | 18 | 17 | 14 | 49 | v3 图修复；全部对照统一到当前 OpenRouter provider |
| Qwen | 18 | 0 | 0 | 18 | 两预算完整 v3 PoolAct 队列 |
| GLM | 9 | 0 | 0 | 9 | Moderate 完整 v3 PoolAct 队列 |
| Kimi | 9 | 0 | 0 | 9 | Moderate 完整 v3 PoolAct 队列 |
| GPT | 9 | 0 | 0 | 9 | Tight 完整 v3 PoolAct 队列 |
| DeepSeek | 0 | 0 | 0 | 0 | 两预算已采用 v4，图代码及显示等价 |
| **总计** | **63** | **17** | **14** | **94** | 不按观察到的碰撞或成绩筛选 |

Gemini 已补齐的 9 个 N4 HPO 槽中，4 个为旧 v3 PoolAct，必须重跑；另有 **5 个** OpenRouter 基线可以有条件复用：Moderate cached B/C repeat 2、Moderate naive C repeat 2、Tight cached A/B repeat 2。Gemini 剩余 31 个 naive/cached 旧结果来自 Sub2，因此本轮即使它们不受图错误影响，也需随 provider 迁移补齐同期同 provider 对照。不能用新的 OpenRouter PoolAct 对比旧的 Sub2 基线后把差异归于算法。

余下 230 个 N4 原运行由 45 个 v4 PoolAct、180 个非 Gemini naive/cached、5 个 Gemini OpenRouter naive/cached 组成；在执行路径等价与终答控制流检查通过后，离线重评分复用。486 个 N1 不读共享图，图修复本身不要求重跑。所有旧终答仍进入全量正式重评分，不只处理先前发现的问题样本。

**94 是图修复与 provider 匹配已明确需要的新运行数，不是无条件的总上限。** 新终答解析器还需逐 assistant turn 检查是否改变终止判定；若旧程序已经错误早停、或新规则会在更早时刻停止，仅改终端分数不能重建缺失行动，需单独标记并扩展必要对照。不得把这种样本描述为新 runtime 的等价复用。终端 payload 改变但认定终答的时刻不变，可以离线修正。

## 复用条件与非图差异

1. 所有 810 槽任务配置 SHA 和 budget-oracle SHA 相同，`max_steps=max_evals=30`、`tool_protocol=native`、`tuning_final_policy=legacy`。全部 NAS101 的 NumPy 为 2.4.6、ConfigSpace 为 1.2.1；另有 162 个非 NAS101 N1 使用 Docker 的 NumPy 1.18.5、ConfigSpace 0.4.21。不能把不同任务环境概括为同一 NumPy 版本。
2. 保留每个模型及预算的原生成设置、seed 语义与 context cap。GPT Moderate 的三个策略原 cap 为 262144，其余 N4 为 131072；本轮不人为改成同一个数。GPT Moderate 保存完整历史的最大粗估为 109159 tokens，未发现 cap 绑定的证据，但这也不是统一 tokenizer 或计算量的证明。
3. GPT Responses 与 Gemini 原生/OpenRouter 历史客户端使用 `requires_immutable_history`，上下文超限不得套用可变 history 裁剪。统一运行包必须保留此适配。
4. Qwen/DeepSeek 历史客户端支持 `prompt_cache_key_field=cache_salt`，统一运行包须保留原 provider 缓存隔离字段。缓存 namespace 的具体随机值可以重建，隔离范围与语义不能静默改变。
5. GLM/Kimi 早期 `0671f352…` 版本在原生工具协议下，未带明确终答标签的普通文本直接作为终答；后续版本新增 `unlabelled_final_answer` 限制。正式新 parser 的终止等价检查须以各槽真实旧源码为基准，不能一律把修复前 main 的 parser 当成所有历史运行版本。
6. 生成 effort 本来不同，GPT/Gemini medium、GLM/Kimi/DeepSeek max、Qwen xhigh，top-p/top-k 也按模型配置。修复的公平性主张是图/终答/评分核心统一、同模型同预算三策略 provider 与设置匹配，不是相同算力、tokenizer 或 provider 确定性。

旧原件及分数保持不变；新运行另建 cohort、记录修复源码和输入身份，正式采用关系按 slot 明示。本文只制定与验证复用条件，不把尚未执行的补跑计为完成。
