# 数据、定义与完整证据

[论文式正文](README.zh.md) · [英文摘要](ABSTRACT.en.md)

## A. 数据范围与评分版本

本页对应正式采用的新评分。评分与图修复核心代码为 `0e6c51b6d86f42437038518c2fc8adc510901c0b`；HPO 原生 API 执行快照为 `ffca5704580b75e254f6e52dd4fe9dff104b1be8`。Search/Audit 控制流对照的执行快照按模型记录：deepseek `885a5bd70dffe02b8dd610f1699e9f675da2b926`；glm `ffca5704580b75e254f6e52dd4fe9dff104b1be8`；qwen `ffca5704580b75e254f6e52dd4fe9dff104b1be8`。执行快照包含提供方兼容接入与环境绑定；其与统一评分核心分别留档，不把不同快照写成同一提交。 主实验 4,698 个固定槽位全量重新评分，旧运行原件保持不变。历史正式分数、2026-09-18 早期诊断与本次全量新评分各有独立身份；诊断中发现的 23 答案和 19 池不是本次重新评分的筛选范围。旧轨迹全量重评分有 57 个槽位的任一指标变化；41 个任务端点变化（Audit 的 LA 或 EA 任一项均计入）；按论文主指标——Search F1、Audit EA、HPO Gap0-MI/Gap0——计数则为 39 个。三者分母与事件定义不同，不能把 41 误称为论文主指标变化数。统一图版本及真实中间终答控制流的新运行是另一层替换，最终采用的来源和效果另见补跑对照。 Gemini 783 项包含历史 Sub2 与 OpenRouter，提供方差异不能被视作已隔离的因果变量。

正式主表已采用全部 97/97 个预注册 HPO 修复/提供方对照池，以及 21/21 个 Search/Audit 中间终答控制流对照槽位；逐运行来源、失败/正常无配置状态和选择规则单独留档。

| 材料 | 入口 |
| --- | --- |
| 全部采用槽位与原件 SHA | [SOURCE_SELECTION.csv](../protocol-repair-20260918/main/SOURCE_SELECTION.csv) |
| 旧轨迹重新评分的逐样本分数、原因 | [离线重评分对照](../protocol-repair-20260918/rescore/main/sample_diff.csv) |
| 旧历史→旧轨迹新评分→实际运行正式采用 | [4,698 行三层对照与采用原因](../protocol-repair-20260918/control_flow_adoption/new_official/sample_diff.csv) |
| 全部绝对值、重复层、宽比较 | [absolute](../protocol-repair-20260918/main/absolute_settings.csv)、[by_repeat](../protocol-repair-20260918/main/by_repeat.csv)、[COMPARISON](../protocol-repair-20260918/main/COMPARISON.csv) |
| 新旧聚合差与排名变化 | [聚合对照](../protocol-repair-20260918/main/all_aggregate_comparisons.csv)、[排名对照](../protocol-repair-20260918/main/ranking_changes.csv) |
| 旧/诊断/新身份与输入 | [评分身份](../protocol-repair-20260918/main/SCORE_VERSIONS.json)、[输入](../protocol-repair-20260918/main/INPUTS.json) |
| 结论与证据 | [conclusion_delta.csv](../protocol-repair-20260918/conclusion_delta.csv) |

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

[七维度完整排名](../protocol-repair-20260918/main/dimension_rankings.csv) · [选型表](../protocol-repair-20260918/display/dimension_selection.csv) · [九任务分数](../protocol-repair-20260918/display/hpo_task_scores.csv) · [regret](../protocol-repair-20260918/display/hpo_task_regret.csv)。

## C. 获取、停止与最终交付

行为分析完整覆盖 Search 1,314、Audit 702、HPO 486 条 N1，共 2,502 条。HPO 各预算 162 条、Free/Tight 162 对。尝试、实际可见结果、可见有效数值评估和隐藏越预算结果分列。不同查询不等于不同文章，HPO 配置按完整数值等价身份去重。停止类型来自真实日志，不用离线新解析重写动作历史。

HPO 严格有分数 475/486，包含 77 条历史回退；排除回退且终答为已评分 JSON 对象 396/486。可解析、任务有效、严格有分数、正常 Gap0 端点是不同口径，不能合并成一个“最终答案成功率”。

[Search 全部轨迹](../protocol-repair-20260918/search/trajectory_metrics.csv) · [预算行为](../protocol-repair-20260918/search/overall_regime.csv) · [438 配对](../protocol-repair-20260918/search/free_tight_paired.csv) · [代表案例](../protocol-repair-20260918/search/representative_case_index.csv)。

[HPO 全部事件与定义](../protocol-repair-20260918/hpo_behavior/README.zh.md) · [全部 486 轨迹](../protocol-repair-20260918/hpo_behavior/official_rescored486/trajectories.csv) · [预算汇总](../protocol-repair-20260918/hpo_behavior/official_rescored486/by_regime.csv) · [原始终止原因](../protocol-repair-20260918/hpo_behavior/official_rescored486/termination_reasons.csv)。

DeepSeek 分解固定每预算 27 槽位，条件严格 Gap 使用可评分重复等权。可评分比例乘该条件均值等于全部槽位 Gap0。共同可评分的 19 对不能替代含未交付项的完整端点。[交付分解](../protocol-repair-20260918/cases/deepseek_delivery.csv) · [27 配对](../protocol-repair-20260918/cases/deepseek_paired_delivery.csv) · [状态贡献](../protocol-repair-20260918/cases/deepseek_delivery_transitions.csv)。

## D. 答案、证据与配对案例

全部 702 N1 和 1,872 N4 成员的终答以统一接受规则处理，按既定包装、标签别名和证据 ID 类型规则归一化，不根据 gold 补造标签或证据。LA 与 EA 独立评分，联合正确率另列。缺失/多余证据按标准集合差计算，可能同时发生。总体及非空证据分层维持文档等权，合并条件分母另列，不混用宏均值和 pooled 比例。

“反馈补全”配对完整定义见正文，目前 272 呈现、264 次完整确认。历史固定案例保留为解释性样例，并重新核对新分数与候选规则；不是随机样本或最大增益选例。`verification_eff` 的分母为终答标签与证据均正确的假设，分子为其中曾向工具提交该正确证据集合的假设，包含预算隐藏返回；`visible_verification_eff` 使用相同分母，只计可见正确核验。

[Audit 方法/案例变化](../protocol-repair-20260918/audit/README.zh.md) · [假设级](../protocol-repair-20260918/audit/n1/hypothesis_metrics.csv) · [轨迹级](../protocol-repair-20260918/audit/n1/trace_metrics.csv) · [模型预算](../protocol-repair-20260918/audit/n1/model_budget_metrics.csv) · [条件分母](../protocol-repair-20260918/audit/n1/diagnostic_counts.csv) · [配对](../protocol-repair-20260918/audit/n1/paired_completion_patterns.csv)。

## E. POOLACT 与运行版本公平性

N4 三策略均为四智能体、匹配每成员反馈预算。Search 限 whois 39 题，Audit 13 文档，HPO NAS101 A/B/C 各三重复，仅 Moderate/Tight。主要端点分别为 F1-MV、EA-MV、Gap0-MI；BoN 是事后真实分最高的成员，不能当可部署选择器。

| 场景 | 预算 | naive | cached | POOLACT |
| --- | --- | --- | --- | --- |
| restricted_search | cost_moderate | 62.60 | 64.12 | 64.32 |
| restricted_search | cost_tight | 17.10 | 18.06 | 24.15 |
| evidence_audit | cost_moderate | 73.38 | 76.85 | 91.40 |
| evidence_audit | cost_tight | 59.80 | 62.22 | 69.53 |
| tuning | cost_moderate | 97.77 | 97.82 | 98.67 |
| tuning | cost_tight | 90.94 | 90.80 | 95.00 |

HPO 图路径原前缀标识会碰撞，原始观测/得分完整键与共享路径显示键需分开核验。已渲染进模型输入的路径不能靠离线改文件恢复为一次修复后的运行。代码版本、模型/预算/策略矩阵、实际受影响运行及统一修复版本的必要补跑选择均单独列出；禁止把修复前后的混合来源隐称相同协议。

[HPO 逐运行代码版本（810 项）](../protocol-repair-20260918/rerun_adoption/adopted_hpo_code_versions.csv)与[模型—预算—策略版本矩阵（54 组）](../protocol-repair-20260918/rerun_adoption/adopted_hpo_model_budget_strategy.csv)分别记录实际执行版本和当前离线评分版本，[版本核验](../protocol-repair-20260918/rerun_adoption/ADOPTED_CODE_VERSION_CHECKS.json)绑定采用来源。旧 HPO 记录中 492 项未写 Git 提交号；这些空值保留，以完整源码树的已核验 SHA 标识执行版本，不补造提交号。旧源码对应八份完整源码树。最终采用的 97 项 HPO 新运行替换与其余 713 项历史执行分别列出。

[全部指标与两基线差](../protocol-repair-20260918/poolact/poolact_all_metrics.csv) · [主增益](../protocol-repair-20260918/poolact/poolact_primary.csv) · [宏均值](../protocol-repair-20260918/poolact/poolact_scenario_summary.csv) · [MI/BoN](../protocol-repair-20260918/display/nas_best_minus_mean.csv) · [Audit 池](../protocol-repair-20260918/audit/coordination/audit_pools.csv) · [Audit 成员](../protocol-repair-20260918/audit/coordination/audit_agents.csv)。

## F. 解释边界与复算

本次保留的解释限制包括：Audit 固定首步示例未改；不同模型思考强度、输出上限、提供方和实际计算资源并不完全相同；等反馈预算不等于等 token、等金钱或等墙钟时间。真实调度会影响共享缓存可用时刻，未证明与提供方时延无关。NAS101 A/B/C 不是三个独立数据集，数值库版本影响并列处理的复现。早期筛选过的运行版本与统一修复补跑分别标注；补跑也包含新采样和并发时序差异，不能把其差值全部归因于修复本身或模型能力。

不报告 p 值，不将固定模型、重复顺序、共享题库或池成员当总体独立抽样。图/缓存/行动协调的各自因果贡献仍未由独立消融完全识别。

主聚合脚本从完整新版 slot scalars 重算 7,767 聚合行、126 排名和 1,298 宽比较，再生成展示、regret、配对及全部 POOLACT 指标。公开最小评分包支持 Search/Audit/Whois 的终答重新提取、任务评分及池投票，也支持 HPO 的重新提取、可见评估匹配、回退和池聚合；HPO 数值性能使用配置 SHA 绑定的已核验 benchmark 证书，默认回放不重新读取完整 benchmark。公开逐事件/假设叶表支持行为汇总与评分连接重建。统一核验器的完整模式另验证实际补跑的最小包、全量采用来源和三份报告。上述公开重放不重新调用模型，也不等同于从完整原件重建最小包、逐次 HTTP 审查或再次验证全 turn 控制流。最后几项及可选完整 benchmark 复核仍需冻结本地归档与对应环境。

Whois 预算 sweep 单列 [完整预算分析与图](../protocol-repair-20260918/whois/README.zh.md)，不额外累加到上述 4,698 主实验分母。其 1,170 个预算—模型—题目结果全量重评分，其中 beta=10 的 234 项已属于主实验，来源与新评分逐项连接；其余 936 项为主分母之外的独立预算设置。旧轨迹离线重评分层的两处终答文本变化均未改变分数。独立报告还采用 1 条必要的实际控制流补跑；该层的新分数和实际 token、墙钟成本按独立报告及其来源解释，不混称为离线评分变化。

[重建主分析](../protocol-repair-20260918/tools/rebuild_analysis.py) · [重建展示](../protocol-repair-20260918/tools/recompute_display.py) · [重建 Search/POOLACT/交付](../protocol-repair-20260918/tools/rebuild_secondary.py) · [生成本报告](../protocol-repair-20260918/tools/render_report.py) · [审阅记录](REVIEW.zh.md)。
