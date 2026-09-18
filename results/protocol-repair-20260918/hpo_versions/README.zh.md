# 公开 HPO 版本与公平性审计包

本包公布修复前已采用样本的版本身份、已证实问题、统一修复的等价证据及 **97 池**补跑选择。补跑的完成状态与新正式成绩由同次发布的实验结果表提供；本包不把计划槽算作完成。

冻结版本：[核心代码 0e6c51b](https://github.com/tiannuo-yang/LLM_ExpGym/commit/0e6c51b6d86f42437038518c2fc8adc510901c0b)、[实验运行包 ffca570](https://github.com/tiannuo-yang/LLM_ExpGym/commit/ffca5704580b75e254f6e52dd4fe9dff104b1be8)，运行 source-tree SHA256 为 `cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02`。完整版本与协议在 [CODE_FREEZE.json](CODE_FREEZE.json)，97 个旧槽到新 job 的固定映射在 [RERUN_BINDINGS.csv](RERUN_BINDINGS.csv)。核心源码和带 provider 适配器的运行包是两个明确版本，不以当前分支 HEAD 代替执行身份。

默认公开复算只需要 Python 标准库和本目录：

```bash
python3 tools/verify_public_tables.py
```

它验证表的覆盖、选择、哈希身份字段、科学设置、图碰撞统计、等价证据计数及包文件清单；**不声称仅凭 CSV 就重新读取了私有 trajectory、数据表或源快照**。[公开清单 ALLOWED.json](ALLOWED.json) 是本包文件的明确 allowlist 和 SHA256 清单；[SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json) 记录导出源及变换。历史数据集中的本地绝对路径仅是来源标识，不是 Git 可用资源，也不是下载链接。内部服务 URL 已替换为可比较的 SHA256 标识；API provider 和生成参数保留。

需要私有原件的审计脚本单列在 `tools/local_archives/`，必须显式提供原 workspace 和独立输出目录。它们需要本地完整 trajectory、旧源码快照、预算 oracle/benchmark 数据以及原路径定位条件；仓库普通 clone 不包含这些材料。例如：

```bash
python3 tools/local_archives/audit_versions.py --workspace /path/to/original/workspace --output /tmp/hpo-version-audit
python3 tools/local_archives/check_historical_v4_equivalence.py --workspace /path/to/original/workspace --output /tmp/hpo-v4-replay
```

本包不含 credential、原始 API 日志、完整 trace 或 serving 启动配置；`HPO_SCIENTIFIC_SETTINGS.json` 是324个历史N4配置的显式科学字段白名单，去除了 endpoint 值和 prompt-cache namespace 值，保留其行为语义。

## 采用版本、图碰撞与必要补跑矩阵

本目录是修复前采用样本的版本审计及执行计划，不是新实验结果。范围为主报告已经采用的 **486 个 N1 槽和 324 个 N4 槽**；N4 每槽 4 个成员，共 1,782 条成员轨迹。已逐份验证 810 个原件 SHA256、810 个执行 `source_tree_sha256` 与现存冻结源码完全一致，并实读校验 197 项去重后的任务配置、预算 oracle、数据表、解码器和表清单。所有检查通过，见 [CHECKS.json](CHECKS.json)。

## 逐槽记录与执行矩阵

- [hpo_all_slots.csv](hpo_all_slots.csv)：810 槽的模型、预算、策略、重复、源文件及 SHA、源码版本、运行协议、上下文上限、生成设置、任务与环境身份、碰撞证据、计划处理方式。
- [hpo_model_budget_strategy.csv](hpo_model_budget_strategy.csv)：每个模型 × 预算 × 策略的版本汇总；同组有多个源码版本时全部列出，不以单一标签掩盖混用。
- [module_hashes.csv](module_hashes.csv)：历史执行版本的关键模块 SHA256。完整源码树匹配后才记作 `verified_complete_tree`。
- [input_hashes.csv](input_hashes.csv)：任务输入元数据记录与当前本地源文件的实算 SHA256 对照。
- [hpo_rerun_slots.csv](hpo_rerun_slots.csv)：97 个明确需要新运行的 N4 槽；每槽原科学配置的白名单导出见 [HPO_SCIENTIFIC_SETTINGS.json](HPO_SCIENTIFIC_SETTINGS.json)。该配置只用于重建旧设置，新的代码版本、图协议与实际 provider 必须另行记录。
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

## 最小充分干预：97 个新池，388 个成员

统一修复只采用历史 v4 的完整 SHA256 identity 和可见快照唯一短 alias，不合并原子快照等其他行为改变。45 个既有 v4 PoolAct 池的两个历史源版本与目标修复版 `parallel_cache.py` **字节完全一致**，SHA256 为 `f7da6a20cdee00f47fc72632a4ba1bd86059c32c54f78a911d210bcd07ea41d7`。从这 45 池的 986 条评估记录按共同确定性顺序重放，双显示模式、4 个观察者及完成时间/预算边界产生 **9,568 个完整快照，全部逐字节一致**，包括节点显示、路径、claims 和可见性。证据：[HISTORICAL_V4_EQUIVALENCE.json](code_diff/HISTORICAL_V4_EQUIVALENCE.json)。这证明代码语义等价，不声称重建了历史真实线程交错。

| 模型 | 重跑 PoolAct | 追加 naive | 追加 cached | 新池合计 | 原因 |
|---|---:|---:|---:|---:|---|
| Gemini | 18 | 17 | 14 | 49 | v3 图修复；全部对照统一到当前 OpenRouter provider |
| Qwen | 18 | 0 | 1 | 19 | 两预算完整 v3 PoolAct 队列；一个 cached 槽的终答控制流不等价 |
| GLM | 10 | 0 | 0 | 10 | Moderate 完整 v3 PoolAct 队列；一个 Tight PoolAct 槽的终答控制流不等价 |
| Kimi | 9 | 0 | 0 | 9 | Moderate 完整 v3 PoolAct 队列 |
| GPT | 9 | 0 | 0 | 9 | Tight 完整 v3 PoolAct 队列 |
| DeepSeek | 1 | 0 | 0 | 1 | 图代码已等价；一个 Tight PoolAct 槽的终答控制流不等价 |
| **总计** | **65** | **17** | **15** | **97** | 按完整图协议与确定性控制流差异选择，不按成绩筛选 |

Gemini 已补齐的 9 个 N4 HPO 槽中，4 个为旧 v3 PoolAct，必须重跑；另有 **5 个** OpenRouter 基线可以有条件复用：Moderate cached B/C repeat 2、Moderate naive C repeat 2、Tight cached A/B repeat 2。Gemini 剩余 31 个 naive/cached 旧结果来自 Sub2，因此本轮即使它们不受图错误影响，也需随 provider 迁移补齐同期同 provider 对照。不能用新的 OpenRouter PoolAct 对比旧的 Sub2 基线后把差异归于算法。

余下 227 个 N4 原运行由 43 个 v4 PoolAct、179 个非 Gemini naive/cached、5 个 Gemini OpenRouter naive/cached 组成；在执行路径等价与终答控制流检查通过后，离线重评分复用。486 个 N1 不读共享图，图修复本身不要求重跑。所有旧终答仍进入全量正式重评分，不只处理先前发现的问题样本。

初版仅按图修复与 provider 匹配得到 94 池，保留于 [初版队列](hpo_rerun_slots.initial94.csv) 和 [初版说明](README.initial94.zh.md)。全量 **810 槽、1,782 成员、18,093 个 assistant turn** 的实际旧源码/新 parser 对照，额外发现 3 个原本拟复用槽会在中间 turn 提前认定终答，因此追加到 97 池：

| slot | 模型/预算/策略/任务/重复 | 成员与中间消息 | 旧/新接受终答 |
|---|---|---|---|
| `e70fbde891a064ec706ccf50` | DeepSeek / Tight / PoolAct / NAS101 B / 2 | agent 1，call 6，messages[12] | false → true |
| `bcb19e920f5a231e46770072` | GLM / Tight / PoolAct / NAS101 C / 0 | agent 2，call 7，messages[14] | false → true |
| `a0dae4e0f6c10847f6d8ea0b` | Qwen / Moderate / cached / NAS101 A / 1 | agent 3，call 11，messages[24] | false → true |

这三个原运行的最终分数恰好没有变化；它们被追加是因为动作序列不可视作新 runtime 的结果，不是因为成绩高低。完整旧/新 payload 见全量重评分输出的 `turn_parser_changes.csv`，逐槽本表也记录了中间 turn 定位。其余候选通过全量逐 turn 终止等价验证后，可以沿用原 provider/参数对照并离线重评分。另一个 GLM Tight cached C repeat 1 的终端 payload 表面提取变化不改变接受时刻，且 legacy 可见最优回退得到相同最终配置，因此无需因该表面变化重新运行。

最终冻结 parser `6b09495845fa6c1dc324a82ba471bcfba59265aaa4912ff0acf8307239e84bed` 已全量复查全部 1,782 成员、18,093 个 assistant turn，三个控制流槽集合不变；97 个新池的选择闭合。元数据对照见 [parser_control_flow.csv](parser_control_flow.csv) 与 [RESCORE_CHECKS.json](RESCORE_CHECKS.json)。不能事后把旧行动重命名为新协议行为。

## 复用条件与非图差异

1. 所有 810 槽任务配置 SHA 和 budget-oracle SHA 相同，`max_steps=max_evals=30`、`tool_protocol=native`、`tuning_final_policy=legacy`。全部 NAS101 的 NumPy 为 2.4.6、ConfigSpace 为 1.2.1；另有 162 个非 NAS101 N1 使用 Docker 的 NumPy 1.18.5、ConfigSpace 0.4.21。不能把不同任务环境概括为同一 NumPy 版本。
2. 保留每个模型及预算的原生成设置、seed 语义与 context cap。GPT Moderate 的三个策略原 cap 为 262144，其余 N4 为 131072；本轮不人为改成同一个数。GPT Moderate 保存完整历史的最大粗估为 109159 tokens，未发现 cap 绑定的证据，但这也不是统一 tokenizer 或计算量的证明。
3. GPT Responses 与 Gemini 原生/OpenRouter 历史客户端使用 `requires_immutable_history`，上下文超限不得套用可变 history 裁剪。统一运行包必须保留此适配。
4. Qwen/DeepSeek 历史客户端支持 `prompt_cache_key_field=cache_salt`，统一运行包须保留原 provider 缓存隔离字段。缓存 namespace 的具体随机值可以重建，隔离范围与语义不能静默改变。
5. GLM/Kimi 早期 `0671f352…` 版本在原生工具协议下，未带明确终答标签的普通文本直接作为终答；后续版本新增 `unlabelled_final_answer` 限制。正式新 parser 的终止等价检查须以各槽真实旧源码为基准，不能一律把修复前 main 的 parser 当成所有历史运行版本。
6. [PROVIDER_PARAMETER_SEMANTICS.json](PROVIDER_PARAMETER_SEMANTICS.json) 区分配置请求值和客户端实际发送：GPT Responses 配置虽记录 `max_tokens=32768`，实际请求省略该字段且 `max_output_tokens=null`，同样省略 temperature/top-p/top-k/seed；推理 effort medium 则发送。不能把配置列读成各 provider 实际输出限额相等。
7. 生成 effort 本来不同，GPT/Gemini medium、GLM/Kimi/DeepSeek max、Qwen xhigh，top-p/top-k 也按模型配置。修复的公平性主张是图/终答/评分核心统一、同模型同预算三策略 provider 与设置匹配，不是相同算力、tokenizer 或 provider 确定性。

旧原件及分数保持不变；新运行另建 cohort、记录修复源码和输入身份，正式采用关系按 slot 明示。本文只制定与验证复用条件，不把尚未执行的补跑计为完成。
