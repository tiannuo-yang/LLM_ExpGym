# 数据、定义与完整证据

[论文式正文](README.zh.md) · [英文摘要](ABSTRACT.en.md)

## A. 数据范围与可追溯入口

本报告在[六模型归档报告的固定版本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/4b9f565e34e03c382cf71ffd7dd86d015593bc4f/results/six-models-lineage-20260914/README.zh.md)及原有轨迹行为分析上，合入已完成的 [16 项 Gemini OpenRouter 补齐结果](../gemini-openrouter-20260917/main/README.zh.md)。2026-09-18 本次报告更新未再调用模型，沿用原答案提取与评分实现。另行代码审查已发现答案提取及投票接受规则的问题；本页尚未采用诊断重评分，相关结果仍按历史协议解释。Claude 不参加此次比较。模型简称分别指该报告中的 Kimi K3 max、GLM 5.3 max、Qwen 3.8 xhigh、DeepSeek V4 Flash 0731 max、GPT-5.6-sol medium、Gemini 3.8 Flash medium；结论适用于这些实际模型—生成设置，而非脱离设置的模型名称。

| 材料 | 入口 |
| --- | --- |
| 原始 dump、存档包、恢复与聚合 CSV 的完整索引 | [固定归档入口](https://github.com/tiannuo-yang/LLM_ExpGym/blob/4b9f565e34e03c382cf71ffd7dd86d015593bc4f/results/six-models-lineage-20260914/ARCHIVE_INDEX.md) |
| 每个采用结果的来源（含补齐） | [4,698 项来源选择](../gemini-openrouter-20260917/main/SOURCE_SELECTION.csv)、[补齐设置与提供方](../gemini-openrouter-20260917/SETTINGS.zh.md)；历史[来源映射](../six-models-lineage-20260914/DATA_LINEAGE.zh.md) |
| 补齐后完整分数，包括 Moderate、cached 与次指标 | [全部绝对值](../gemini-openrouter-20260917/main/absolute_settings.csv)、[重复层](../gemini-openrouter-20260917/main/by_repeat.csv)、[合并比较](../gemini-openrouter-20260917/main/COMPARISON.csv)、[逐项分数](../gemini-openrouter-20260917/main/slot_scalars.csv) |
| 本报告的新增聚合与原件定位 | 下列 B–F 各模块 CSV、输入清单与 SHA256 |
| 正文四个短案例及新增交付分解 | [案例索引与选择规则](cases/CASE_INDEX.zh.md)、[三场景动作证据](cases/case_index.json)、[DeepSeek 分解与原件核验](cases/deepseek_delivery_checks.json) |

当前采用结果合计 4,698/4,698 项执行完成，严格评分完整 4,687。DeepSeek 的 11 项正常缺配置属于 N1 调优；Gap0 与严格 Gap 分开。Gemini 已完成 783/783：在历史采用的 767 项上，补齐 N1 HPO 六项、N4 HPO 九项以及 N4 Search Moderate naive 一项。新增池采用完整新执行，不拼接旧失败池成员；原有 4,682 项采用结果保持不变。Gemini* 表示历史 Sub2 与新增 OpenRouter 混合提供方，不能解释为单一网关重跑结果。失败/未完成实验没有补零；来源不按新分数重新挑选。

原件链接沿用已归档身份；部分 API 原始 dump 仍为本地可访问材料，并不因本报告引用而变成公开数据。本次实际读取的 canonical trace 或 pool result 另有逐文件哈希。输入核对不声称重新验证全部 HTTP dump 或全部压缩包。

## B. EXPGYM 与选型 regret

### B.1 评价单位

N1：Search 73 题（whois 39、whatis 34），每题每预算一次；Audit 13 文档、每文档三个固定顺序；调优九任务、每任务三次重复。三档预算为 Free/Moderate/Tight。Free 不限制反馈成本；Moderate 与 Tight 分别为基准成本的 10 倍和 3 倍，Search/Audit 基准为 300 秒，调优使用各自冻结参考成本。这里是反馈成本模型的单位，不是实际运行时长。最大交互步数/评估次数为 30。

质量均值先平均任务内重复，再等权平均任务。Audit 的顺序、同一文档的假设以及池内成员均不能作为独立任务重复。模型宏均值仅是本研究固定候选集合的等权描述；不跨不同评分指标合成总分。

Gap 越高越好；Gap0 只把正常未交付有效配置的终态定义为零效用，失败或未完成项不适用该定义。Gemini 已由实际完成结果补齐。调优沿用历史最终配置规则，可能采用最佳已评估配置回退，不能把得分直接当作严格的原样最终提交质量。N4 完整调优组的严格 Gap 与 Gap0 相等。

### B.2 排名与 regret

以 Free/Tight 两端都有完整任务均值的相同模型集作比较；不允许 Free 用六模型、Tight 换成五模型。Free 并列保留为集合，regret 报告其范围；并列判断容差见脚本。最高观察均分不自动意味着显著冠军。

正文七维度为两个 Search 家族、两个 Audit 指标、三个调优家族。当前七个维度均具备六模型完整比较，其中五个换领先者；两个 Audit 指标仍属同一场景，不能当作两个独立任务。历史五模型敏感性分析保留为原冻结快照材料，不与当前六模型结论混用。

| 九个调优任务 | 可比模型数 | Free 领先者 | Tight 领先者 | regret，Gap points |
| --- | ---: | --- | --- | ---: |
| NAS101 A | 6 | Gemini* | GPT | 2.32 |
| NAS101 B | 6 | Gemini* | Gemini* | 0.00 |
| NAS101 C | 6 | Gemini* | GPT | 0.32 |
| NAS201 CIFAR10 | 6 | Kimi / Gemini* | GPT | 1.99–7.45 |
| NAS201 CIFAR100 | 6 | Kimi / Gemini* | Gemini* | 0.00–1.10 |
| NAS201 ImageNet16-120 | 6 | Kimi | Kimi | 0.00 |
| ParamNet Adult | 6 | GPT | Gemini* | 15.22 |
| ParamNet Higgs | 6 | Gemini* | Gemini* | 0.00 |
| ParamNet Letter | 6 | Kimi | GPT | 1.13 |

九任务均采用同一六模型候选集合，任务内三重复的 Gap0 先平均；DeepSeek 正常无配置项保留为零。当前最大 regret 为 Adult 的 15.22，且 Free 无并列；NAS201 CIFAR10 的 1.99–7.45 区间仍由 Free 并列选择决定。regret 是同一批观测均分上的回顾性选型比较，没有独立训练/选型/部署数据划分。

当前补齐版：[预算完整比较](../gemini-openrouter-20260917/main/COMPARISON.csv) · [七维度所有模型与预算排名](../gemini-openrouter-20260917/main/dimension_rankings.csv) · [选型与 regret](gemini-update-20260918/dimension_selection.csv) · [逐任务分数](gemini-update-20260918/hpo_task_scores.csv) · [九任务 regret 及并列](gemini-update-20260918/hpo_task_regret.csv) · [输入身份与检查](gemini-update-20260918/CHECKS.json) · [生成器](gemini-update-20260918/recompute.py)。原 `rank/` 保留原冻结快照，不用于当前补齐版的数值结论。

## C. Trajectory：获取与停止

原行为分析实际读取 N1 Search 1,314 条、Audit 702 条、HPO 480 条，共 2,496 条完成轨迹。Search/Audit 输入未变，仍为全量；HPO 行为表保留原冻结快照的 480 条，不含本次合入的六条新 N1 轨迹。当前 HPO 主分数、排名与 regret 使用全部 486 条完成结果。行为分析包括正常结束但无可评分配置的 HPO 轨迹；不把“有轨迹”误当成“有严格分数”。

- **尝试**：已经执行的工具调用；**可见反馈**：明确向模型提供的结果。达到或超过预算边界的结果未提供，不能计为已获取信息。
- **不同观测**：Search 按返回文章身份计数，HPO 按完整配置身份计数；不同查询字符串不自动代表新文章。配置中的数值等价整数/浮点数视为相同。
- **自主提交**：日志中的自然回答路径，不推断自信、完成证明或继续反馈的主观价值。预算边界、步数/评估上限和其他协议终态分开保留。
- 行为数量的合并描述不用于统计显著性；原 HPO 行为样本中另有 159 对相同模型—任务—重复的 Free/Tight 配对，该冻结分析未填补当时缺失的轨迹。

Search 的全部十八个模型—预算分数与冻结报告一致；并在每模型的 Free 不完美自主结束、Tight 不完美预算结束两类中，按不同文章数量中位数确定十二条代表轨迹进行结构核查。该案例选择只用于解释，不用于估计总体比例；总体比例来自全量轨迹。

[Search 分析](search/OBSERVATIONS.zh.md) · [模型×预算](search/by_model_regime.csv) · [所有轨迹](search/trajectory_metrics.csv) · [Free/Tight 配对](search/free_tight_paired.csv) · [代表轨迹索引](search/representative_case_index.csv) · [输入 SHA](search/INPUTS.json) · [检查](search/CHECKS.json) · [脚本](search/analyze_search.py)

[HPO 分析](hpo/INSIGHTS.md) · [模型×预算](hpo/by_model_regime.csv) · [任务家族](hpo/by_model_family_regime.csv) · [全部轨迹](hpo/trajectories.csv) · [可见评估序列](hpo/delivered_events.csv) · [配对](hpo/free_tight_pairs.csv) · [输入 SHA](hpo/INPUT_INVENTORY.json) · [脚本](hpo/analyze_hpo.py)

正文新增的 DeepSeek 分解以九任务各三次重复、每预算 27 个固定槽位为分母。可评分比例乘以可评分重复的等权 Gap 均值，恰好等于这 27 项的 Gap0；这里的条件均值不是“各任务已知子集均值再等权”的旧列，两种权重不能混用。可评分不等于正确或高分，真正零分仍保留。Free/Tight 的 27 对中，19 对两端均可评分，6 对从无分到有分，1 对从有分到无分，1 对两端无分；对整体 Gap0 变化的贡献分别为 −4.80、+20.26、−0.75、0.00，合计 +14.72。完整配对的均值只作诊断，不代替包含未交付项的完整端点。

DeepSeek 示例为 NAS101 C、seed 2208：Free 已获得较好观测，但最终未给出配置；Tight 观测较差，却完成交付。它是为解释这一分解选择的具体案例，不是随机抽样，不能证明预算本身改善了停止策略，也不能确定空答案的底层原因。原始 N1 来源及评分保持不变，未把后续 N4 修补反写为该轨迹的运行条件。

[三预算交付分解](cases/deepseek_delivery.csv) · [27 对状态及贡献](cases/deepseek_paired_delivery.csv) · [定义、原件 SHA 与检查](cases/deepseek_delivery_checks.json) · [复算脚本](cases/analyze_deepseek_delivery.py)

## D. Trajectory：答案与证据

审计使用已存最终答案、与运行身份匹配的标准证据以及实际可见的反馈。全部 702 条轨迹的 LA/EA 与原存分数一致。新增的联合正确率要求标签与证据同时正确；遗漏和多余证据按标准片段集合之差计算，二者可同时发生，不能相加成总错误率。这是集合充分性指标，不是人工评价解释是否有说服力。

总体和标准证据非空分层均保持文档等权，三个顺序先在文档内平均。正文条件比例 257/1,818、986/1,850 为标准证据非空且标签正确的呈现次数合并计数；它不是文档宏平均条件比例。后者遇到零个正确标签时未定义，分别有 Free/Moderate/Tight 23/14/17 个呈现无分母；机器表保留两种定义，不混用。

“反馈补全”模式要求同一模型、文档、顺序、假设同时满足：Free 首次可见提案缺证据且收到不完整提示，最后标签/证据均正确；Tight 标签正确但提交与 Free 首次提案完全相同的部分集合，且没有获得对该假设的可见工具反馈。253 个呈现折叠顺序后为 160 个模型—文档—假设组合，覆盖 58/78 个模型—文档组合。这不是额外反馈的随机干预实验。

历史 N1 提示的固定调用示例与首个查询一致的比例为 Free 220/234、Moderate 226/234、Tight 227/234。它可能影响反馈分配，因此不从这些轨迹推断模型固有的假设优先级，也不主张提示无关性。相关评分分解是所记录协议下的观察结果。

[Audit 完整分析](audit/README.zh.md) · [全部模型与预算](audit/model_budget_metrics.csv) · [文档级](audit/document_metrics.csv) · [轨迹级](audit/trace_metrics.csv) · [假设级](audit/hypothesis_metrics.csv) · [条件分母](audit/diagnostic_counts.csv) · [补全模式配对](audit/paired_completion_patterns.csv) · [输入 SHA](audit/INPUTS.json) · [脚本](audit/analyze_audit.py)

## E. POOLACT 的比较与行为证据

N4 的三个策略都使用四名智能体、相同单智能体反馈预算。Search 为 whois 39 题，每设置一次；Audit 为 13 文档，每设置一次；NAS101 A/B/C 各三次重复。只计划 Moderate/Tight，没有 Free 池实验。主要端点分别为 Search 多数投票 F1、Audit 投票 EA、调优个体均值 MI；调优 BoN 为事后最高分，不是实际可部署的选择规则。

| 场景 | 预算 | 三策略完整模型数 | naive | cached | POOLACT |
| --- | --- | ---: | ---: | ---: | ---: |
| Search F1-MV | Moderate | 6 | 62.60 | 64.12 | 64.32 |
| Search F1-MV | Tight | 6 | 17.10 | 18.06 | 23.98 |
| Audit EA-MV | Moderate | 6 | 73.08 | 76.77 | 90.80 |
| Audit EA-MV | Tight | 6 | 59.95 | 62.14 | 69.38 |
| NAS101 Gap-MI | Moderate | 6 | 97.75 | 97.84 | 98.66 |
| NAS101 Gap-MI | Tight | 6 | 91.00 | 90.89 | 96.04 |

当前全部行均为同一六模型的完整宏均值，不与历史五模型宏均值混用，也不据此主张预算交互效应的统计显著性。正差/负差全部保留；相对提升先逐模型用各自基线计算，零基线不定义，再取中位数。正文 43.4% 是六个 Tight Search 相对 naive 增幅的中位数，不是宏均值之比（后者为 40.2%），也不是最大增幅。

审计协调分析读取当前选定来源的全部 468 池、1,872 个成员。依据实际消息辨认模型可见工具回复；计数包括缓存命中和三条可见工具错误回复，错误回复不解释为有效核验。覆盖按池去重合法假设 ID，一条无法解析的请求不增加覆盖。图内共享内容不再计作新工具回复，因而不能把“可见回复数”理解为新付费获取数。两档预算下各模型都使用同样的十三文档权重。轨迹指标解释的是观察到的覆盖和复用行为，不单独识别缓存、图或串行决策部分的因果贡献。

当前补齐版：[主要端点及两基线差值](gemini-update-20260918/poolact_primary.csv) · [全部端点](../gemini-openrouter-20260917/main/absolute_settings.csv) · [场景宏均值](gemini-update-20260918/poolact_scenario_summary.csv) · [BoN−MI](gemini-update-20260918/nas_best_minus_mean.csv) · [输入身份](gemini-update-20260918/CHECKS.json) · [生成器](gemini-update-20260918/recompute.py)。原 `poolact/` 顶层分数表保留历史冻结快照；下列审计协调分析的原件未变。

[审计每池轨迹指标](poolact/coordination/audit_pools.csv) · [成员指标](poolact/coordination/audit_agents.csv) · [模型—预算—策略汇总](poolact/coordination/audit_groups.csv) · [原件 SHA 清单](poolact/coordination/AUDIT_TRAJECTORY_MANIFEST.json) · [提取器](poolact/coordination/analyze_audit_coordination.py)

## F. 解释范围与复算

本文不报告 p 值或统计显著性。模型、题库和文档均为固定已观察集合；共享语料、同文档假设、固定顺序和池内成员不提供相互独立的总体抽样。定向重跑曾参考旧结果，且不同来源的协议并非完全一致；本报告复用固定的最终来源，不将前后改进归因于单一修补，也不将当前观察提升为一般模型定律。

早期写作示例中的“全部七维度更换冠军”“最大 regret 33.9”“Search 最大提升 52%”，既不由原冻结快照、也不由本次补齐结果支持。本报告及当前英文摘要据实际可比集合、并列规则和指定基线表述；不通过更换任务、模型集合或分母去追求示例数字。

各模块提供分析脚本和实读输入清单。轨迹复算需要访问清单中的原始本地文件；只有公开 CSV 时可以复算展示表，不能声称已重建原始轨迹。未更改模型、环境或官方评分程序。

正文案例只引用任务、工具动作/反馈及最终提交，不引用私有推理。Search、Audit 与 PoolAct 示例均从满足相应行为条件的候选中按明确的中位数规则选择，并非随机样本，也不是按最大成绩提升选取；一般性描述仍由完整轨迹统计承担。[案例索引](cases/CASE_INDEX.zh.md) 保留精确题目/文档位置、选择规则、原件 SHA 和解释限制。两个案例脚本的 `--check` 仅做只读复算与输出一致性检查，不重跑模型或重新评分。

当前更新检查见 [REVIEW.zh.md](REVIEW.zh.md) 与[派生数据检查](gemini-update-20260918/CHECKS.json)；本报告发布文件身份见 [MANIFEST.json](MANIFEST.json)。[ad03 原文与附件](README.ad03.zh.md)及其原始审核留档，原有审核结论不代替本次更新核查。
