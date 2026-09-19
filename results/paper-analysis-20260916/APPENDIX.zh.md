# 数据、定义与完整证据

[论文式正文](README.zh.md) · [英文摘要](ABSTRACT.en.md)

## A. 数据范围与评分版本

本页对应单智能体保留 7776f70、多智能体恢复修复前结果的正式采用版本。当前仓库代码回退版本为 `ba4b39ed46b445288c2ba04f65dade33621c64a5`，该提交不代表重新执行旧轨迹。N1 保留 7776f70 的评分与实际运行来源。N4 恢复修复前的解析、投票、图代码及完整三策略成绩；历史执行版本仍以逐槽来源记录为准。当前入口的代码回退清单与验证见新交付，不把旧运行标为以本次回退提交重新执行。 主实验 4,698 个固定槽位全部重新聚合，其中 N1 保留 7776f70 修复评分，N4 完整恢复 297c3d0 历史评分。历史分数、早期诊断、已撤回采用的修复分数与本次回退选择分别留存；本次没有重新评分旧 N4 来替代其历史成绩。当前 N1 保持 7776f70 的全部 2,502 个槽位；N4 的全部 2,196 个槽位恢复到含 Gemini 补齐的 297c3d0 分数与来源。7776f70 的全量旧轨迹重评分诊断曾记录 57 个任一指标变化、41 个任务端点变化和 39 个论文主指标变化；这些是保留的历史诊断计数，不是本版 N4 采用新评分的计数。本次回退相对于 7776f70 的逐样本变化另列。 Gemini 783 项包含历史 Sub2 与 OpenRouter，提供方差异不能被视作已隔离的因果变量。

本版完整恢复全部 2,196 个 N4 槽位的修复前分数和原件来源，涵盖 naive、cached、POOLACT 三种策略。97 个 HPO 池和 19 个 Search/Audit N4 修复补跑不再作为主表来源，全部保留在 7776f70 历史包中。2,502 个 N1 槽位保持 7776f70，其中包括两个 Audit 实际控制流补跑、Gemini 补齐、486 条 HPO 行为和已修复的单体终答评分。本次没有调用模型或按成绩挑选样本。

| 材料 | 入口 |
| --- | --- |
| 全部采用槽位与原件 SHA | [SOURCE_SELECTION.csv](../poolact-rollback-20260919/main/SOURCE_SELECTION.csv) |
| 旧轨迹重新评分的逐样本分数、原因 | [离线重评分对照](../protocol-repair-20260918/rescore/main/sample_diff.csv) |
| 回退前→当前采用来源、分数及原因 | [4,698 行回退对照](../poolact-rollback-20260919/selection/sample_rollback.csv) |
| 全部绝对值、重复层、宽比较 | [absolute](../poolact-rollback-20260919/main/absolute_settings.csv)、[by_repeat](../poolact-rollback-20260919/main/by_repeat.csv)、[COMPARISON](../poolact-rollback-20260919/main/COMPARISON.csv) |
| 新旧聚合差与排名变化 | [聚合对照](../poolact-rollback-20260919/main/all_aggregate_comparisons.csv)、[排名对照](../poolact-rollback-20260919/main/ranking_changes.csv) |
| 旧/诊断/新身份与输入 | [评分身份](../poolact-rollback-20260919/main/SCORE_VERSIONS.json)、[输入](../poolact-rollback-20260919/main/INPUTS.json) |
| 结论与证据 | [conclusion_delta.csv](../poolact-rollback-20260919/conclusion_delta.csv) |

## B. EXPGYM、排名与 regret

N1 Search 为 73 题（whois 39、whatis 34），每题每预算一次；Audit 为 13 文档、三种固定假设顺序；HPO 为九任务各三重复。均值先平均任务内重复，再对任务等权。`expected_units` 是对应表的评分单元，未必等于任务数，例如 HPO 27 是九任务乘三重复。Audit 的顺序和假设不作为独立任务。

Free 不限制反馈成本，但有步数上限。Moderate/Tight 使用基准成本的 10/3 倍；Search/Audit 基准为 300 秒，HPO 使用冻结任务参考成本。预算单位是模拟反馈成本，不是墙钟时间。达到或超过预算边界的结果计费但未向模型提供，不能计作已获取信息。

Gap/Gap0 越高越好；Gap0 只对已完成、正常无配置的终态使用零效用，不把失败或未完成补零。历史最佳已评估配置回退仍单独标注。新终答接受规则不修补答案内容、不查询 gold 选择最有利候选，也不改变历史工具行动。

排名使用相同六模型集合，Free 并列全部保留，绝对容差 1e-9。regret 是同任务 Tight 最优分减去 Free 选中模型的 Tight 分；并列保留区间，无独立选型/部署留出集。

| HPO 任务 | Free 领先者 | Tight 领先者 | regret 最小 / 最大 |
| --- | --- | --- | --- |
| hpobench:nasbench101:A | Gemini* | GPT | 2.32 / 2.32 |
| hpobench:nasbench101:B | Gemini* | Gemini* | 0.00 / 0.00 |
| hpobench:nasbench101:C | Gemini* | GPT | 0.32 / 0.32 |
| hpobench:nasbench201:cifar10-valid | Kimi / Gemini* | GPT | 1.99 / 7.45 |
| hpobench:nasbench201:cifar100 | Kimi / Gemini* | Gemini* | 0.00 / 1.10 |
| hpobench:nasbench201:imagenet16-120 | Kimi | Kimi | 0.00 / 0.00 |
| hpobench:paramnet:adult:steps | GPT | Gemini* | 15.22 / 15.22 |
| hpobench:paramnet:higgs:steps | Gemini* | Gemini* | 0.00 / 0.00 |
| hpobench:paramnet:letter:steps | Kimi | GPT | 1.13 / 1.13 |

[七维度完整排名](../poolact-rollback-20260919/main/dimension_rankings.csv) · [选型表](../poolact-rollback-20260919/display/dimension_selection.csv) · [九任务分数](../poolact-rollback-20260919/display/hpo_task_scores.csv) · [regret](../poolact-rollback-20260919/display/hpo_task_regret.csv)。

## C. 获取、停止与最终交付

行为分析完整覆盖 Search 1,314、Audit 702、HPO 486 条 N1，共 2,502 条。HPO 各预算 162 条、Free/Tight 162 对。尝试、实际可见结果、可见有效数值评估和隐藏越预算结果分列。不同查询不等于不同文章，HPO 配置按完整数值等价身份去重。停止类型来自真实日志，不用离线新解析重写动作历史。

HPO 严格有分数 475/486，包含 77 条历史回退；排除回退且终答为已评分 JSON 对象 396/486。可解析、任务有效、严格有分数、正常 Gap0 端点是不同口径，不能合并成一个“最终答案成功率”。

[Search 全部轨迹](../poolact-rollback-20260919/search/trajectory_metrics.csv) · [预算行为](../poolact-rollback-20260919/search/overall_regime.csv) · [438 配对](../poolact-rollback-20260919/search/free_tight_paired.csv) · [代表案例](../poolact-rollback-20260919/search/representative_case_index.csv)。

[HPO 全部事件与定义](../protocol-repair-20260918/hpo_behavior/README.zh.md) · [全部 486 轨迹](../protocol-repair-20260918/hpo_behavior/official_rescored486/trajectories.csv) · [预算汇总](../protocol-repair-20260918/hpo_behavior/official_rescored486/by_regime.csv) · [原始终止原因](../protocol-repair-20260918/hpo_behavior/official_rescored486/termination_reasons.csv)。

DeepSeek 分解固定每预算 27 槽位，条件严格 Gap 使用可评分重复等权。可评分比例乘该条件均值等于全部槽位 Gap0。共同可评分的 19 对不能替代含未交付项的完整端点。[交付分解](../poolact-rollback-20260919/cases/deepseek_delivery.csv) · [27 配对](../poolact-rollback-20260919/cases/deepseek_paired_delivery.csv) · [状态贡献](../poolact-rollback-20260919/cases/deepseek_delivery_transitions.csv)。

## D. 答案、证据与配对案例

702 条 N1 保留修复后的终答接受与评分；1,872 个 N4 成员及 468 个池恢复历史解析、投票和评分。两层分别标注，不将其描述为统一的新接受规则，也不根据 gold 补造标签或证据。LA 与 EA 独立评分，联合正确率另列。缺失/多余证据按标准集合差计算，可能同时发生。总体及非空证据分层维持文档等权，合并条件分母另列，不混用宏均值和 pooled 比例。

“反馈补全”配对完整定义见正文，目前 272 呈现、264 次完整确认。历史固定案例保留为解释性样例，并重新核对新分数与候选规则；不是随机样本或最大增益选例。`verification_eff` 的分母为终答标签与证据均正确的假设，分子为其中曾向工具提交该正确证据集合的假设，包含预算隐藏返回；`visible_verification_eff` 使用相同分母，只计可见正确核验。

[Audit 方法/案例变化](../poolact-rollback-20260919/audit/README.zh.md) · [假设级](../poolact-rollback-20260919/audit/n1/hypothesis_metrics.csv) · [轨迹级](../poolact-rollback-20260919/audit/n1/trace_metrics.csv) · [模型预算](../poolact-rollback-20260919/audit/n1/model_budget_metrics.csv) · [条件分母](../poolact-rollback-20260919/audit/n1/diagnostic_counts.csv) · [配对](../poolact-rollback-20260919/audit/n1/paired_completion_patterns.csv)。

## E. POOLACT 与运行版本公平性

N4 三策略均为四智能体、匹配每成员反馈预算。Search 限 whois 39 题，Audit 13 文档，HPO NAS101 A/B/C 各三重复，仅 Moderate/Tight。主要端点分别为 F1-MV、EA-MV、Gap0-MI；BoN 是事后真实分最高的成员，不能当可部署选择器。

| 场景 | 预算 | naive | cached | POOLACT |
| --- | --- | --- | --- | --- |
| restricted_search | cost_moderate | 62.60 | 64.12 | 64.32 |
| restricted_search | cost_tight | 17.10 | 18.06 | 23.98 |
| evidence_audit | cost_moderate | 73.08 | 76.77 | 90.80 |
| evidence_audit | cost_tight | 59.95 | 62.14 | 69.38 |
| tuning | cost_moderate | 97.75 | 97.84 | 98.66 |
| tuning | cost_tight | 91.00 | 90.89 | 96.04 |

本版恢复全部历史 N4 来源，因此原图路径前缀标识、解析/投票规则、提供方和版本差异也随之保留。此前图审计、碰撞证据和 97 池修复补跑完整保存在 7776f70 历史交付中，不作为本版的正式 N4 来源。本版沿用既有三策略运行，执行版本按历史来源记录。

[历史 HPO 逐运行版本（810 项）](../protocol-repair-20260918/hpo_versions/hpo_all_slots.csv)与[历史模型—预算—策略版本矩阵（54 组）](../protocol-repair-20260918/hpo_versions/hpo_model_budget_strategy.csv)记录实际执行身份；当前全部 HPO 的来源哈希与该历史集合一致。旧 HPO 记录中 492 项未写 Git 提交号，保留空值并使用已核验源码树 SHA，不补造提交号。

[全部指标与两基线差](../poolact-rollback-20260919/poolact/poolact_all_metrics.csv) · [主增益](../poolact-rollback-20260919/poolact/poolact_primary.csv) · [宏均值](../poolact-rollback-20260919/poolact/poolact_scenario_summary.csv) · [MI/BoN](../poolact-rollback-20260919/display/nas_best_minus_mean.csv) · [Audit 池](../poolact-rollback-20260919/audit/coordination/audit_pools.csv) · [Audit 成员](../poolact-rollback-20260919/audit/coordination/audit_agents.csv)。

## F. 解释边界与复算

本次保留的解释限制包括：Audit 固定首步示例未改；不同模型思考强度、输出上限、提供方和实际计算资源并不完全相同；等反馈预算不等于等 token、等金钱或等墙钟时间。N4 恢复的历史结果包含原来的图路径、解析、投票和提供方差异。此前的诊断、修复候选和实际对照完整留档；本版 N4 使用既有运行，其执行版本与提供方差异按来源表记录。

不报告 p 值，不将固定模型、重复顺序、共享题库或池成员当总体独立抽样。图/缓存/行动协调的各自因果贡献仍未由独立消融完全识别。

主聚合脚本从完整新版 slot scalars 重算 7,767 聚合行、126 排名和 1,298 宽比较，再生成展示、regret、配对及全部 POOLACT 指标。本次公开回退重建器从两个固定版本逐行选择：N1 采用 7776f70，N4 采用含 Gemini 补齐的 297c3d0；重新计算所有聚合、报告和对应 Audit 行为表。它不将撤回的 N4 新评分再次套用。7776f70 的最小评分包和完整重放器仍作为历史材料保留，其中 HPO 使用已核验性能证书，不默认读取完整 benchmark。上述公开重放不重新调用模型，也不等同于从完整原件重建最小包、逐次 HTTP 审查或再次验证全 turn 控制流。最后几项及可选完整 benchmark 复核仍需冻结本地归档与对应环境。

Whois 预算 sweep 单列 [完整预算分析与图](../protocol-repair-20260918/whois/README.zh.md)，不额外累加到上述 4,698 主实验分母。其 1,170 个预算—模型—题目结果全量重评分，其中 beta=10 的 234 项已属于主实验，来源与新评分逐项连接；其余 936 项为主分母之外的独立预算设置。旧轨迹离线重评分层的两处终答文本变化均未改变分数。独立 Whois N1 sweep 保留 7776f70 的采用来源、分数和实际 token/墙钟统计；本次 N4 回退不改变它。

[重建主分析](../poolact-rollback-20260919/tools/rebuild_analysis.py) · [重建展示](../poolact-rollback-20260919/tools/recompute_display.py) · [重建 Search/POOLACT/交付](../poolact-rollback-20260919/tools/rebuild_secondary.py) · [生成本报告](../poolact-rollback-20260919/tools/render_report.py) · [审阅记录](REVIEW.zh.md)。
