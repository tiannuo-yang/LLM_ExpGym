# 四个机制样例：从总体统计回到可观察动作

这些短例仅将正文已有发现具体化，不承担估计普遍性或证明因果的作用。前三例从机制条件满足的候选中按明确规则选取，没有按最大得分提升挑选；第四例是固定的交付诊断配对，不声称为随机或中位样例。对应频率来自原有完整 CSV。下面只展示任务、工具动作/反馈和最终提交，不引用模型的私有推理内容。

前三例的精确原始路径、SHA-256、消息/工具位置、选择规则及逐项核验结果见 [case_index.json](case_index.json)；第四例见 [DeepSeek 核验记录](deepseek_delivery_checks.json)。原始轨迹仍位于既有存档位置，本目录不复制 raw dump。

<a id="search-query-diversity"></a>

## 1. 新查询，不一定获得新信息

Qwen 的一条 Free 搜索轨迹先后查询 `petroleum engineer`、`son of Adella Mcbroom`、`mother Adella Mcbroom` 和 `petroleum`，四个不同字符串均返回 Adella Mcbroom 的同一篇文章。整个运行发起 16 次查询、只覆盖 11 篇不同文章，自主提交后的 F1 为 1/3。例子具体呈现“动作新颖性不等于观测新颖性”；它呼应 Free 下 183/438 条轨迹出现文章重复、1,160 次重复返回中 1,144 次来自新查询字符串的总体统计。

重复文章免反馈费用，但仍占用决策步骤。该题 Tight 也得到 F1=1/3，因此此例不用于声称预算导致该题退化，也不暗示多查询一定无用。

- 科学标识：Qwen、`phantom_seed2`、题 31、Free；同时保留 Tight 配对作为解释边界。
- 选择：沿用 [既有代表索引](../search/representative_case_index.csv)，在 Qwen Free 自主结束且未满分的 19 个候选中，按不同文章数取上中位数（同数按 source/数值题号排序）。
- 统计来源：[逐轨迹指标](../search/trajectory_metrics.csv)、[Free/Tight 配对](../search/free_tight_paired.csv)。
- JSON 案例 ID：`search_action_novelty_not_observation_novelty`；包含全部 16 次工具的 query→文章映射及费用/可见性。

<a id="audit-evidence-completion"></a>

## 2. 标签正确，证据仍需补全

一个合同判断问“接收方是否可以从第三方获得类似信息”。Qwen 在 Free 下最初只引用具体的第三方来源例外子条款；收到 `Evidence Incomplete | missing: Carveout set` 后，补上说明“保密义务不适用于下列情形”的上位条款，随后获确认并提交完整证据。对应 Tight 运行仍给出正确的 Entailment 标签，却只提交原先的子条款，且未向工具查询该假设。例子把“正确标签之外，反馈还用于修订证据集合”具体化；相同严格配对模式共 253 个假设呈现，覆盖六模型、12/13 份文档，其中 245 个在 Free 下获得完整集合的正确确认。

| | Free 初始提案 | Free 反馈后最终提交 | Tight 最终提交 |
| --- | --- | --- | --- |
| 标签 | 工具仅核验所提证据，不核验标签 | Entailment | Entailment |
| 证据 | 具体例外子条款 `[51]` | 上位作用域句及子条款 `[47,51]` | 具体例外子条款 `[51]` |
| 对该证据的反馈 | 不完整，缺 `Carveout set` | `Evidence Correct` | 未请求 |

此处遗漏的是上位作用域句，已提交的子条款依然相关。因此它说明的是**标注证据集合的完整性**，不能夸大为“完全无证据”“事实依据错误”，也不能替代独立法律充分性判断。Free/Tight 是独立生成，不是同一轨迹的人为截断；不能证明额外一次反馈必然修复 Tight。

- 科学标识：Qwen、文档数组 index 10、顺序 1、`nda-13`。
- 选择：在 [配对模式表](../audit/paired_completion_patterns.csv) 的 Qwen 行中，限定金标准两片段、初始/ Tight 单片段的 53 个匹配，保留冻结 CSV 顺序，取第 27 行；不按得分差排序。
- 原始动作：Free `tool0022` 提交 `[51]`，`tool0023` 提交 `[47,51]`；两次结果均可见；Tight 对 `nda-13` 没有工具请求。
- JSON 案例 ID：`audit_correct_label_incomplete_evidence`；含原文两片段、标签和工具消息定位。

<a id="poolact-coverage-sharing"></a>

## 3. PoolAct：覆盖更多问题，并复用同伴核验

Kimi 在同一份 Moderate 审计文档中，PoolAct 用 38 次可见反馈覆盖 16 个假设；naive 为 40 次/10 个，cached 为 46 次/12 个。投票 EA 分别为 100.00、82.35、88.24。其原始消息还记录了具体传播过程：agent 3 确认“依法披露前应通知披露方”的条款 `[21]` 正确，agent 0 看到了这一共享核验行、自己从未查询该假设，最终仍提交同一正确证据。这个例子具体说明覆盖分配与核验复用如何共同出现，而不是简单靠更多调用改善结果。

| 策略 | 可见反馈次数 | 获得反馈的不同假设 | 投票 EA（%） |
| --- | ---: | ---: | ---: |
| naive | 40 | 10 | 82.35 |
| cached | 46 | 12 | 88.24 |
| PoolAct | 38 | 16 | 100.00 |

可检查的共享行是 `nda:nda-8 ev:[21] [Evidence Correct] [agents 3]`。收到共享信息后最终一致，不能证明答案必然复制自同伴，也不能隔离图共享、共享观测和行动协调的独立因果贡献。

总体依据并不局限于此池：原有 468 个审计池统计中，PoolAct 在 12/12 个模型—预算组合的覆盖均值高于 cached；检测到“见过同伴正确核验、自己未核验、最终提交相同非空集合”的成员为 Moderate 253/312、Tight 153/312。这个检测不是对未检出者无受益的判断，也不是因果归因。

- 科学标识：Kimi、Moderate、四智能体、question index 3，原始文档 ID 5；数组位置是 `documents[3]`，不是 `documents[5]`。
- 选择：在 Moderate 池中限定 PoolAct 调用不多于 naive、覆盖优于两基线且出现同伴核验最终匹配，得到 39 个候选；按超过较好基线的覆盖数，再按模型/预算/字符串题号排序，取第 20 个，其覆盖优势为 4。不使用投票得分挑选。
- 三策略来源：[逐池指标及 raw 路径](../poolact/coordination/audit_pools.csv)；成员来源：[逐智能体指标](../poolact/coordination/audit_agents.csv)；总体来源：[组均值](../poolact/coordination/audit_groups.csv)。
- JSON 案例 ID：`poolact_coverage_and_verified_observation_reuse`；含三臂精确 SHA、原始聚合评分、生产者工具记录及接收者共享消息位置。

<a id="hpo-delivery"></a>

## 4. DeepSeek：发现好配置，不等于最终交付

在 NAS101 C、seed 2208 的固定配对中，Free 已获得 9 次有效可见评估，最好原始性能为 0.9412，却没有交付有效最终配置，因而 Gap0 为 0；Tight 只获得 3 次有效可见评估，最好原始性能为 0.8956，但交付了有效配置，Gap 为 91.16。Tight 最后一次越预算结果被扣留，随后强制最终回答成功提交了已评估配置，而非依赖回退评分。这个例子将“探索质量”和“可评分结果的交付”区分开来，不说明更少探索本身更好，也不主张这种反转普遍存在于其他模型。

对应全体 27 个 Free/Tight 配对，19 对两端均有严格分数，其均分为 85.76→78.94；另有 6 对由缺配置转为有分。这一交付状态变化是总体 Gap0 反向上升的重要组成，而不是把既有结果删去后强行恢复下降结论。有分子集是事后条件分析，不替代正式全体结果；空最终输出也不能唯一归因为模型、协议、serving 或上下文长度。

- [三预算交付率及分数分解](deepseek_delivery.csv)、[全部 27 个配对及 raw 路径](deepseek_paired_delivery.csv)、[两条原始轨迹 SHA 与核验边界](deepseek_delivery_checks.json)。
- 诊断例只使用原始 N1 数据，不混入后来的 N4 重跑；最好已观察性能不替代最终得分，原始性能与 Gap 也不混为同一量纲。

## 核验范围与复算

[analyze_cases.py](analyze_cases.py) 负责前三例：读取其七个原始轨迹/池文件、合同金标准和已有 CSV/索引，检查哈希、选择规则、动作可见性、最终提交、三臂指标及所引总体计数。[analyze_deepseek_delivery.py](analyze_deepseek_delivery.py) 独立负责第四例：核对既有 81 个任务—重复记录、27 个 Free/Tight 配对及两条诊断原始轨迹。两者均不调用模型、不重评分、不改 raw、不重新普查全部轨迹。

使用现有 Python 环境分别运行 `python -B analyze_cases.py --check` 和 `python -B analyze_deepseek_delivery.py --check`，可执行各自的只读、逐字节一致性检查；不加 `--check` 仅重新生成各自负责的 JSON/CSV。这不是新实验，也不是新的完整数据审计。原始证据保留在本地存档，发布本索引不代表将其原始全文一并公开。
