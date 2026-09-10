# v5 论文主张—实际设置对照预检

这是 **Custom study 的方法准备，不是结果报告或最终审计**。只读当前本地论文、已编译正式 plan、冻结 v5 源码及分析/导出代码；未读本轮或旧轮实际答案、分数、reasoning/raw 内容，未调用模型、scorer 或生产入口。最终完整输出及分析冻结后，仍须新的独立 post-analysis audit。

论文定位以 [paper README](/lustrefs/users/chufan.shi/codex_space_tn/expgym-paper/README.md:3) 为准：current 为 `versions/iclr2026/main.tex`，以下简写 **P**。下文源代码行号属于 `source_cohorts/v5/LLM_ExpGym`，不是 Sept7 的历史 text v3。实际计划、逐组全部 argv 控制项、来源文件 bytes/SHA 见 [EVIDENCE.json](EVIDENCE.json)；它只证明此预检所读输入，不证明实际运行完成。

## 1. 六个固定主对照：应检验什么、不能声称什么

分数均为 higher-is-better。ExpGym 主效应为 **Free − Tight**：正值表示退化，负值表示 Tight 更好；Pool 主效应为 **PoolAct − Naive**：正值表示改善，负值表示退步。此表只预先定义方向，不预填实际效应。F1/accuracy 差用原始 0–1 单位，乘 100 后才叫百分点；Gap 原本就是点数。论文相对增幅不是百分点，baseline 为零时相对增幅不可计算。

| 固定端点 | 论文实际依据（不扩大主张） | v5 指标、配对单位及参照 | 匹配/偏离与最终表述 |
| --- | --- | --- | --- |
| E-S：Exp Search 退化 | P:119、293、404–416：六模型在 Free/Tight 排名变化；whois 排名 τ_b=.20，**不是每个模型/题目都必降**。 | whois question macro-F1，固定同题同模型 Free vs Tight；39 whois，outer0。whatis、各题、成本列属预定次对照。 | 论文 seed1 的18 whois/17 whatis；本次 seed2/3 共73题（39/34），Search R1。只描述本固定题集的差，不复现六模型排名/τ_b。 |
| E-A：Exp Audit 退化 | P:493–500、875–888：论文六模型 EA 均下降；标签准确率不必下降（Mistral LA .754→.769，EA .555→.459）。 | 每 trace 的17假设 exact evidence-set accuracy；每文档三个固定 orders 等权均值后，13文档等权；同 doc 的 Free vs Tight，outer0。 | 保留13文档/3orders/3预算，不另乘R3。固定顺序不是随机独立重复；必须分别报 EA 与 LA，不能以标签保持证明证据保持。 |
| E-H：Exp HPO 退化 | P:272–294、412–416：PN/N201/N101 六模型平均损失17.4/10.7/4.7 Gap 点；路径可能非单调。 | 同 task、outer 的 Free vs Tight；逐有效 perf 做 Gap，再九task等权（每家族3task）；outer0/1/2。 | 九任务及三次生成重复相近；新的模型/采样/native协议、NAS提示和缺配置 unknown 使其非论文逐字节复现。HPO 总均值不是论文全部七维排名的替代。 |
| P-S：Pool Tight Search 改善 | P:600–603、644–647：Haiku locked MV .243→.370，约+52%；DSV/Gemini +37%/+35% 是 **prelock**。 | 同题、同模型、Tight、N4、outer0：PoolAct MV-F1 − Naive MV-F1；39 whois等权。 | 所有本次 poolact 使用 locked `paper-graph-lock-v3`；不能拿论文 prelock 行当同实现基线。MI、Cached 和 Moderate 另列；不是 Pool N4 与 Exp 单agent比较。 |
| P-A：Pool Moderate Audit 改善 | P:630–633、649–652：EA .633→.751、.629→.733、.588→.688，约+19%/+17%/+17%；Tight Audit 明列 flat。 | 同 doc、同模型、Moderate、N4、**default order**、outer0：voted EA 的 PoolAct−Naive；13文档等权。 | 沿用 Pool default order，不能把 Exp 三order均值并入 Pool。保留 voted LA、mean-individual、Tight 及 Cached 次对照；不能把 EA 增益改写为“各预算所有指标均改善”。 |
| P-H：Pool Tight NAS101:A 改善 | P:610–613、653：表格同时报 BoN/MI，但 Δ 是 MI Gap 点：DSV +27、Haiku +17、Gemini +39（后者 prelock）。 | 仅 NAS101:A，Tight，同模型同 outer 的完整N4池：逐agent Gap floor0后 MI，PoolAct−Naive；outer0/1/2。 | B/C、三task总值、BoN、raw perf、Moderate 是次对照，不能替换主终点。历史NAS主表具体seed目录数量正文未交代；本次明示R3，不冒称复原历史重复数。 |

论文并未承诺 PoolAct 一定胜过 Cached：DSV Moderate Search 的 MV 为 Cached .810、PoolAct .781，而 MI 为 .760、.788；Moderate tuning 部分退步（P:626、635–638、665）。因此“无提升、反向、混合、端点未知”都是必须保留的合法最终结论。

主次目录由 [converter.py:179](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/design/formal_export_candidate/converter.py:179) 固定为每模型 **6主+508次=514**，其中 Exp 158、Pool 356；不能按效果改名、删负值或把不完整端点排除后宣称完整。历史NAS重复数量不确定的直接依据是 [paper checker:583](/lustrefs/users/chufan.shi/codex_space_tn/expgym-paper/scripts/verify_paper_claims.py:583) 对多个 `nb101a_s*` 目录求均值；其缺失过滤也不等同本次 nullable 规则。

## 2. v5 实际设置，不沿用旧全 R3 模板

以下计数由两份完整正式 plan 的 `matrix.logical_rows` 和 `jobs` 独立分组，**每模型相同**：

| 场景 | 固定范围 | invocations | logical | agent traces |
| --- | --- | ---: | ---: | ---: |
| Exp Search | 73题 × Free/Moderate/Tight × R1 | 219 | 219 | 219 |
| Exp Audit | 13doc × 3预算 × 3固定orders × R1；每inv执行3orders | 39 | 117 | 117 |
| Exp HPO | 9task × 3预算 × R3 | 81 | 81 | 81 |
| Pool Search | 39whois × Moderate/Tight × naive/cached/poolact × R1 × N4 | 234 | 234 | 936 |
| Pool Audit | 13doc × 2预算 × 3策略 × default order × R1 × N4 | 78 | 78 | 312 |
| Pool NAS101 | A/B/C × 2预算 × 3策略 × R3 × N4 | 54 | 54 | 216 |
| 合计 | 每模型 | **705** | **783** | **1881** |

两模型合计1410 invocations、1566 logical、3762 agent traces；这些是计划量，不是实际完成量。Audit doc内归并后每模型705展示单元、7687 metric cells。九 HPO 精确名单为 ParamNet `adult:steps/higgs:steps/letter:steps`；NAS101 `A/B/C`；NAS201 `cifar10-valid/cifar100/imagenet16-120`，均以 `hpobench:` 前缀存储。范围、repeat与seed算法见 [planner.py:162](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/planner_candidate_v1/planner.py:162)、[planner.py:254](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/planner_candidate_v1/planner.py:254)。

- 所有实际 argv：native、30 steps、30 evaluations、单请求输出上限32768、最多一次协议 repair；HTTP重试上限2另计，交付的模型格式/length失败不是免费重抽。每模型workers32指独立invocations，不是独立统计样本量，也不保证固定HTTP并发。
- K3：temperature=1、top_p=1、top_k未传，reasoning_effort=max，chat_template_kwargs={thinking:true, thinking_effort:max}。GLM：temperature=1、top_p=.95、top_k未传，reasoning_effort=max，chat_template_kwargs={clear_thinking:false, reasoning_effort:max}。这是 **requested max-reasoning profile**；不凭字段名推定实际用了相同推理token或达到某种“最大能力”。论文主表六模型 extended reasoning disabled，Exp Search/Audit温度0、Tuning/Pool温度.7（P:318–323、584），均不同。
- 两profile均声明 `seed_labels_only`。base_seed=2200，调度seed=20260909；HPO outer标签2200/2204/2208，Pool各outer四成员为该标签至+3；Exp Audit三个order标签2200/2201/2202。题目配对是相同任务条件，不是已证实 common-RNG 配对；不能从标签断言独立同分布或位级复现。
- 实际上下文不是所有框架同限：Exp sweep未传客户端 max_context_tokens，loop默认None；Pool三策略都传131072，使用 JSON字符数/3近似并按组裁剪历史（非真实tokenizer证明）。K3/GLM profile的server_context_tokens分别524288/262144，是另一层配置；本预检没有读取新的server_info，不能凭profile代替实际server limit验收，最终须引用独立当前metadata/启动参数证据。依据 [sweep:638](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/scripts/run_paper_sweep.py:638)、[Pool:520](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/scripts/run_poolact.py:520)、[loop:73](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/react_loop.py:73)。native schema/客户端history正确，不等于已经观察到服务端最终tokenizer渲染。
- 预算与成本可见性对应论文：Free无反馈上限且隐藏成本；Moderate=10×base，Tight=3×base。Search/Audit base=300模拟秒，预算3000/900，新付费反馈约280–320；Search回取本trace已见文章、合格共享缓存命中可为0，不能把请求数直接乘300当实耗。HPO base来自该task冻结oracle.best_cost，不能统一写900/3000。loop与cached wrapper/coordinator overhead_scale=1，不按模型或场景另缩放。达到或超过预算的反馈须隐藏，成本仍留账。依据 [demo:38](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/demo_experiment.py:38)、[Pool:472](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/scripts/run_poolact.py:472)。最终需核9task确实命中oracle，不能接受 `resolve_base_cost` 缺失时默认100作为等价证明。
- Search seed2/3 是两个固定world，不是抽样来的两次独立新corpus；该轮重启时部分范围已有历史尝试，因此新manifest记 `mixed_or_unknown`，Audit/HPO记 `previously_inspected`。不得沿用旧master“未运行/heldout”时态，旧结果和成本保留但不混作本轮重复。

旧 [MASTER_PROTOCOL:9](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/parallel_full_20260908/MASTER_PROTOCOL.zh.md:9) 和 [METHODS.template:9](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/parallel_full_20260908/report_methods_disclosure_candidate_v1/METHODS.template.zh.md:9) 的全R3/1845/5049/source82、旧预算时间与旧资格事件只作历史，不能原样填本轮报告。v5当前source tree为 `0671f352f8980b7360baae6f8e6c98b7336ef50823b0d27ab8e090e5d0a42fdc`，source acceptance明确86files。旧K3条件资格与GLM严格资格属于各自历史证据，v5实际smoke/完整性状态须另列实际收据；此预检不提升或重新颁发资格。

## 3. 最少必要的可比性/评分披露

1. **同环境反馈预算不是同总资源。** 正确对照是同模型/任务/outer/regime的 naive N4、cached N4、poolact N4，各agent同30步/反馈上限。PoolAct新增graph上下文和action-selection lock本身会改变LLM输入和墙钟；即使token上限相同也不代表实际token相同。不能把Pool N4对Exp单agent的差归为协调增益。反馈模拟秒、实际prompt/output（含reasoning）、请求/repair/retry、episode wall、调度跨度、排队/加载/资格/收尾、Slurm GPU-h和旧作废成本必须分列。论文91–100%“EEI时间”是字符/token速率假设下的估算（P:740–747），不是本次GPU或实测wall占比；重复query率也不自动等于重复付费率。

2. **Tuning legacy不是“原始提交配置统一打分”。** 有预算内记录且最终提交未精确匹配时，loop会回退为最高已评估配置并替换终态answer（[loop:523](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/react_loop.py:523)、[lookup:634](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/react_loop.py:634)）；没有eval_records且有实际最终配置时，原CLI存在offline_final_answer补评分路径（[sweep:817](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/scripts/run_paper_sweep.py:817)）。这是离线评分而非新模型反馈/免费工具观察，但相对于P:232–233的简述须披露。BoN通过评估分数选择最好成员，含评估器选择权，不等于无oracle可部署投票。`raw_terminals.raw_answer`来自原持久化终态，不保证是模型最初逐字提交；应与answer_source/answer_score_source及原HTTP/loop终态证据一起解释，不能拿fallback成功直接声称提交正确。

3. **缺答新口径与论文有实质偏差。** v5只把正常loop返回的None按 `task-abstention-v1` 处理：Search/Audit保留answer=None，以原evaluator对空预测的分数作projection，不硬写所有空预测=0；HPO缺配置保持null，不触发工具/最佳已评估fallback。任何N4缺配置使完整MI/BoN unknown，known-subset只描述；基础设施/完整性失败单列，计划分母不删除。论文P:287写无有效performance记0，839写failed repetitions记Gap0，本次不采用笼统填0。**这两句没有细分missing final、forced-length、invalid evaluation、无eval_records或基础设施异常；不能说论文明确规定所有None=0。** P:232–233又有匹配/fallback条件，因此“无已见评估但提交了实际配置”与“根本没有提交配置”须区分，不能凭文字重建缺失的历史原件行为。依据 [missing_final:52](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/missing_final.py:52)、[missing_final:138](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/missing_final.py:138)。必须区分execution_complete、score_complete、raw None、投影评分与未读到答案，null不等于差、零或失败重抽许可。

4. **指标并非全语义统一。** Search F1解析的非JSON分支有1–5词过滤（JSON数组分支没有），但Pool投票key没有同一过滤；投票按规范化答案集合频数，平局偏非空、再最早agent，并非逐实体多数投票或oracle选最佳（[Search:162](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/task_restricted_search.py:162)、[Pool:141](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/poolact.py:141)、[Pool:279](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/poolact.py:279)）。Audit原单agent LA标签精确比较、EA与LA独立且保留int-coercion；Pool投票另有label/evidence规范化，aggregate evaluator使用空tool_records，不可把aggregate verification_eff解释为四agent真实获得的证据覆盖（[Audit:399](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/task_evidence_audit.py:399)、[Pool:169](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/poolact.py:169)）。EA不是“标签和证据联合正确率”；MV不是MI。v5 NAS B/C提示已经按真实编码修正（[task_tuning:307](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/task_tuning.py:307)），Sept7“未修提示”的旧披露不适用；同名任务仍可能由参数结构辨识，不宣称完全盲化。

5. **固定语料、描述性重复与验证界限。** Gap逐agent `max(0,100*(perf−mean)/(best−mean))`后聚合，无100上限；oracle是固定参考统计量，必须绑定task/数据/版本，不能拿raw perf当Gap或先均值再clip。Exp Audit缺任何order则doc端点unknown；HPO/NAS每outer先固定题集均值，再对3个完整bundle给描述SD。Search/Audit R1的SD/CI为null，R3也不提供CI/p值或确认性结论；订单、四agent、同world题目不能膨胀独立N。依据 [AN2:262](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_candidate_v2/analysis.py:262)。原CLI禁LLM独立重执行证明同源重算一致，不等于独立算法实现正确；exporter/AN2仅提取与运算，最终fresh审计仍要看原件来源、隐藏反馈、费用和解释。

## 4. 本矩阵未检验的论文结论

不检验六论文模型的七维全leader变更、平均Kendall τ_b=.39或33.9点部署regret的数值复现；不检验N=1…8 scaling、locked vs prelock/N8消融、Think vs Standard消融、论文三模型全部主表，或原论文91–100%估算时间。即使固定6主方向均符合预期，也只能说“本次两模型、各自profile、固定语料、已披露评分/缺答口径下观察到这些差值”。若不符合，照报原值、负/零/unknown与coverage，不更换端点或解释为工程必坏。

“经完整来源证明的正常模型缺答另派生Gap0惩罚”在概念上可以作为将来明确授权的探索性敏感性假设，但**本阶段未启用、未实现、未注册新端点**，不把它称为paper-exact或追加到514主次对照。它也不能为infra/unstarted/任意unknown填0，不能替换完整N4 unknown主规则或按哪个方向更好选用。若以后确有必要，须透明单列假设、缺失范围与完整池重算规则；answer=None却有已见评估的情况尤其不能冒称已还原论文fallback。当前报告先如实列模型缺答率、score coverage、unknown和已知子集的条件性范围。

本技能要求区分 custom、工程与语义验收，因此本稿保留上述偏差及未检验项；未按旧技能“全部finite”示例把获准缺配置unknown误记为零。`EVIDENCE.json`不含实际效果，未新建正式接受/注册/GO。本稿不修改任何旧模板、冻结源码、原件或既定统计方案。
