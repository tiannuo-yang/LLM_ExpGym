# 诊断复盘与 matched-strategy smoke：详细报告

状态：GPU 与 matched-strategy 验证均已完成，12/12 primary 池、24/24 primary 成员完整评分。另保留旧GLM Audit已完成池及两个未启动controls，实际共13池、26成员。本文不是完整矩阵重跑或 paper-exact reproduction，不覆盖旧正式结果。[主报告](README.zh.md)围绕预算退化、PoolAct 收益和 ranking reshuffle 三个问题。

## 1. 研究身份与当前范围

本次有四类证据，不能混为同一研究样本：

| 范围 | 已有/计划单位 | 用途与边界 |
| --- | --- | --- |
| 原五模型正式结果 | 已冻结的原矩阵 | 保留旧评分、预算与排名；诊断不自动改写其端点 |
| 冻结原件审查 | 90 NAS + 130 Audit PoolAct 池 | 定位图身份问题及发生范围，不构造修后分数 |
| 新首请求 GPU 回放 | baseline v2 c1/c4各8；candidate前后各8；另留v1的8次 | 协议、生成保真与 runtime 诊断；40次回放不计任务成绩 |
| 新 matched-strategy smoke | primary 12池/24成员；另留旧GLM Audit三槽，其中1池完成、2池未启动 | 每模型 NAS/Audit × naive/cached/poolact；实际13执行池/26成员，不丢旧费用 |

新 task smoke 的修复源码提交：`b3382b1c0b89ef1637e232f4b7eef68d55a54f12`；runtime source tree SHA：`e96575475b66e9e25b59115301dee10d04850a1f14f9d6b4d499f0651da47a78`。图协议为 `paper-graph-lock-v4`。Audit native prompt 修改改变源码/提示身份，不另造模型专属评分规则。

源码与技能来源：实际 task smoke 固定运行 `b3382b1c0b89ef1637e232f4b7eef68d55a54f12`。后续报告/serving 文档与 runner 技能已推送到 `fix/eval-integrity-20260912`，提交 [5bf5e5af817c2c6add48c7bae4eec4fe6e8110e9](https://github.com/tiannuo-yang/LLM_ExpGym/commit/5bf5e5af817c2c6add48c7bae4eec4fe6e8110e9)；相对实际任务源码仅为 docs-only 差异，不是重跑、运行源码变更或新的任务验收。

具体输入清单由[reporting/spec.json](ARCHIVE_INDEX.md#other-evidence)选定，被读取文件的 SHA/大小、已有 validation 和原 dump inventory 见[INDEX.json](INDEX.json)。计划、实际启动/结束、评分完整性分别留存。

## 2. 新 task smoke 设置

| 项目 | 本轮冻结设置 |
| --- | --- |
| 任务 | NASBench101-A；Audit cc-large 第 0 文档；均为已检查的固定诊断任务 |
| 模型 / 部署 cohort | GLM NAS：1205018；GLM新Audit三策略：1205034；DeepSeek全部六池：multistream-off 1205022 |
| 策略 / 样本单位 | naive、cached、poolact；N=2，每任务/策略一个完整池，R1 |
| 预算 | Tight；NAS 14832.456298828125 模拟反馈秒/成员，Audit 900 秒/成员 |
| 决策上限 | max_steps=4，max_evals=3；每成员最多四次普通决定及一次 forced final |
| 输出 / 上下文 | max_tokens=32768；max_context_tokens=131072 |
| 采样 | 各模型原配置：temperature=1.0，top_p=0.95，reasoning_effort=max；其余字段按原模型冻结配置继承 |
| 工具 / 缺答 | native；max_protocol_retries=1；transport max_retries=0；legacy tuning final；task-abstention-v1 |
| seed | base 2200，两成员请求 seed 2200/2201；不是独立或确定生成的证明 |
| 隔离 | 独立进程、coordinator/cache、run ID、输出目录和 cache salt；同一比较必须绑定同一部署 |

DeepSeek 候选只关闭多 stream 重叠并显式保持 baseline 有效 server seed；其他实际 flags、runtime/权重和部署身份见原部署文件。前后16个同输入回放均连贯；实际六池47条中46连贯、1语义重复、0明显碎词乱码。证据支持保留候选，不证明某个kernel的严格因果根因或全部请求永不退化。

GLM原allocation启动约59分钟，无法延长两小时时限。原NAS三策略及Audit PoolAct共四池29请求完成后排空；旧Audit两个controls未启动，均保留为 `not_started_infra_budget`。在原Audit成绩产生前已决定新四小时allocation，仅重建Audit PoolAct→naive→cached三池；旧Audit三槽标 `superseded_for_matched`，不能同新controls拼分。全部GLM最多70调用，增加的一池来自时限而非按分数补抽。DeepSeek六池均来自同streamoff cohort；旧Deep baseline PoolAct执行数为0。

计划入口：[GLM PoolAct 计划，仅选择 GLM 条目](ARCHIVE_INDEX.md#other-evidence) · [GLM 补充策略计划，仅选择 GLM 条目](ARCHIVE_INDEX.md#other-evidence) · [DeepSeek 候选 PoolAct](ARCHIVE_INDEX.md#other-evidence) · [DeepSeek 候选补充策略](ARCHIVE_INDEX.md#other-evidence)。

新GLM Audit：[PoolAct计划](ARCHIVE_INDEX.md#other-evidence) · [同部署controls](ARCHIVE_INDEX.md#other-evidence) · [部署差异/时限计划](ARCHIVE_INDEX.md#other-evidence)。

## 3. 原五模型中的确认问题与影响

### 3.1 共享图路径身份碰撞

历史实现用完整 canonical configuration 存储节点/缓存，但路径端点仅使用其前 80 字符；不同长配置可能共享路径 ID。修复后完整身份使用稳定、唯一的完整键/hash，显示采用可核对的别名，不以截断显示值充当身份。此规则不按模型分支。

已明确读取全部 220 个目标原 result，NAS 的保存 eval_records 重建配置数逐池等于 graph.eval_nodes；未把超预算、不进入共享图的评价加入计数。

| 模型 | NAS 碰撞池 | Moderate / Tight | 完整配置 → 前缀 ID（各池求和） |
| --- | ---: | --- | --- |
| Kimi | 17/18 | 9/9；8/9 | 356 → 172 |
| GLM | 18/18 | 9/9；9/9 | 490 → 265 |
| Qwen | 17/18 | 9/9；8/9 | 440 → 236 |
| DeepSeek | 10/18 | 3/9；7/9 | 78 → 43 |
| GPT | 18/18 | 9/9；9/9 | 423 → 158 |

合计 80/90 NAS 池。Audit 的 130 池均无该碰撞，各模型最长 feedback key 为 54/56/54/54/57 字符，均不到 80。全部 220 池 pending claims 为 0。完整配置数是逐池求和，不是跨池去重。[原文件路径、SHA 与算法](ARCHIVE_INDEX.md#other-evidence) · [复现脚本](ARCHIVE_INDEX.md#other-evidence)

它影响 NAS 的协调信息与轨迹解释，但不是已有 scalar score 直接算错；不能从碰撞频率估算效果量。单体 ExpGym 预算与家族排名不使用此图，因此不直接受该缺陷影响。

### 3.2 GPT 本地上下文终止

全 1881 成员只有 1 次 context stop（0.0532%）；按 783 个 execution 为 0.1277%。这属于 Moderate NAS PoolAct 设置的 1/36 成员、1/9 池：全局少见，却可能主导该格小幅差值。

原 Gap0-MI 为 PoolAct 95.579679、naive 98.211271（−2.631592）。若缺失成员交付 Gap=`G`，该设置均值增加 `G/36`。使用原 trace 已见的最后/最佳配置作假设，分别得到 +0.123542/+0.136997 的相对 naive 差值。这些只是敏感度，既非真实最终配置，也不是数学最大影响，不能补入正式评分。本轮没有改变上下文策略。

### 3.3 DeepSeek 输出异常与 Audit native prompt

DeepSeek Tight Audit 的 naive/cached/PoolAct 均有 22/52 个空答，但非空中直接 JSON 字典数分别为 15/11/2；对应原 EA-MI 为 18.55/12.90/1.70 分，EA-MV 为 49.77/37.10/6.79 分。空答率相同仍有明显差距，不能把负效应全部归为空答。

“非空”不等于任务合法答案；另一方面，其他模型的直接 JSON 解析失败可能只是评分器允许的围栏/分号，不能一概称为乱码。原 individual evaluator 与 strict voter 的语法接受差异应另列，不因本次报告擅自统一评分政策。

另确认 native Audit 用户任务提示把固定 `nda-11 / [3,7]` 参数写成没有示例标签的调用命令，可能与 PoolAct 的已在进行动作提示冲突。通用修复删除固定可执行参数，改成依据当前文档选择验证项；legacy text、数据、tool schema、答案和评分未变。该修复不能自动解释或消除服务端多调用、循环退化及乱码。

来源分开：图截断见初始公开版本 `aa135b1`（2026-05-05）；命令式native提示由我们的移植提交 `18fa994`（2026-09-08）引入，不应归给原论文或某一模型。诊断v1的字段排序错误同样是我们本次harness的错误，保留原数据及成本并由v2纠正。

以上数值与边界来源于[冻结影响说明](ARCHIVE_INDEX.md#other-evidence)，不是本报告新增评分或重读全量 raw 的结果。

## 4. 首请求回放：保序输入与真实协议

v1 诊断 helper 错误使用 `sort_keys=True`，改变工具 schema 的嵌套字段顺序和模型实际渲染提示。它的 8 次调用、费用和原始输出全部保留，**不能称为历史原始输入精确回放**。

v2 使用冻结客户端的 `json.dumps(payload).encode("utf-8")` 序列化，保留每层插入顺序与默认分隔符，不新增 nonce；原 messages、tools、tool_choice、sampling、seed 和 cache_salt 保持原样。canonical JSON 等价仅证明语义键值相同，不能替代真实 wire bytes、渲染 text/token 身份。

baseline v2 c1/c4 共 16 次实际 wire 已逐字节匹配各自冻结请求，并与既有 renderer CPU 审计的 SHA 链相符；实际 prompt token 计数也一致，计数只作辅助，不独自证明输入一致。[v2 输入身份](ARCHIVE_INDEX.md#other-evidence) · [完整协议复核](ARCHIVE_INDEX.md#other-evidence)

| 同输入条件 | 请求 | 连贯 | 严重循环退化 | 明显乱码 | 原 runner 接受首决策 | 多调用拒绝 | 空回复拒绝 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| c1 | 8 | 8 | 0 | 0 | 5 | 3 | 0 |
| c4 | 8 | 2 | 4 | 2 | 6 | 1 | 1 |
| multistream-off c4初始 | 8 | 8 | 0 | 0 | 6 | 2 | 0 |
| multistream-off c4六池后 | 8 | 8 | 0 | 0 | 7 | 1 | 0 |

标签来自完整输出阅读。runner 接受性由冻结 decoder 和 CPU 单步、惰性工具回放判断，不调用 gold 或任务 scorer。可读但多工具的输出会被原单调用规则拒绝；已有工具调用也不排除 reasoning 中途乱码。`parallel_tool_calls=false` 是请求约束，不是 backend 已落实约束的证明。

四条目的性选取的首请求各重复两次，不是总体发生率估计。c1/c4 未随机化、交错或充分重复，请求 seed 不保证采样完全确定；不能据此唯一归因于并发、schema 顺序或具体 kernel。

候选前后两组已完成8/8，各自wire/token全部匹配：[初组分类](ARCHIVE_INDEX.md#other-evidence) · [后组分类](ARCHIVE_INDEX.md#other-evidence)。前后检查均在运行前预留，没有对坏结果补抽；其中真实六池的47条也全读，语义循环例在cached最终回复中，答案依然有效。文本循环与碎词乱码分开，不用HTTP成功或分数代替判断。

## 5. 新 smoke 数值与验收口径

12个primary槽与3个superseded槽的终态/计划状态冻结后统一导出；保留未启动和旧费用，不按答案好坏选择文件。真实结果见[逐池](per_pool.csv)、[逐成员](per_agent.csv)和[三策略比较](comparisons.csv)。

已完成数值（fraction）：

| 模型/端点 | naive | cached | PoolAct |
| --- | ---: | ---: | ---: |
| GLM NAS MI/BoN | .845886747/.845886747 | .845886747/.845886747 | .845886747/.845886747 |
| DeepSeek NAS MI/BoN | .845886747/.845886747 | .845886747/.845886747 | .862062633/.878238519 |
| DeepSeek Audit EA-MI/MV | .382352941/.352941176 | .382352941/.411764706 | .323529412/.352941176 |
| DeepSeek Audit LA-MI/MV | .941176471/.941176471 | .882352941/.941176471 | .911764706/.882352941 |
| 新GLM Audit EA-MI/MV | .382352941/.411764706 | .352941176/.352941176 | .470588235/.529411765 |
| 新GLM Audit LA-MI/MV | .911764706/.941176471 | .882352941/.882352941 | .882352941/.882352941 |

旧GLM Audit单独留存：EA-MI/MV=.470588235/.411764706，LA-MI/MV=.941176471/.941176471，不是新matched结果。DeepSeek六池共47次调用、12成员完整评分，5次多调用整批拒绝；旧GLM四池共29次调用、8成员完整评分，4次多调用拒绝，后续均按原预算完成。五个实际完成的PoolAct池均pending=0；naive/cached不使用claims，pending应为N/A而非伪填0。

新GLM Audit三池25次请求、6/6有效最终答案；cached有一次 `finish_reason=length`，回复被按原协议拒绝，之后在原步数预算内恢复，没有HTTP重试或删掉失败回复。PoolAct相对naive/cached：EA-MI为+8.82/+11.76pp，EA-MV为+11.76/+17.65pp；LA-MI为−2.94/0pp，LA-MV为−5.88/0pp。主EA指标获益不等于所有指标改善。

检查范围不能混用：旧GLM29次通过原件/配置、协议、评分、图一致性验证，但没有逐份通读全部reasoning/content，不能标为“29次生成全文保真通过”。新GLM Audit启动前预定的PoolAct全文检查现已完成：8/8原件各读一次，覆盖438,696个reasoning字符和4,911个content字符；1条正常推进、7条持续可读语义重复、0条明显乱码。6条单工具调用、2条可见最终答案，均无多调用、空答和length；执行者独立验证2/2最终答案有效、协议错误0、5 canonical nodes、7 snapshots、pending=0。循环都有逐条依据与当前回复内的字符定位，不是按输出长度自动标记，也不能直接归因为serving损坏。naive/cached没有做相同全文检查，不能外推标签或估计PoolAct相对这些对照的循环增幅。[完整复核](ARCHIVE_INDEX.md#other-evidence)，归档前缀 `originals/glm_fidelity_review/`。

该新PoolAct池实际02:45:14→03:15:54，wall约1840.16秒；8次HTTP wall合计1839.94秒，最长412.10秒，prompt162,298/output114,588 tokens，其中reasoning112,902。请求wall之和接近整个池的wall，但不能据此推定不同策略具有相同物理并发模式或相同实际成本。反馈预算与决策上限按同一冻结设置比较，真实耗时另报。

新GLM Audit成本（UTC；reasoning已包含于output；HTTP累计可能包含并发）：

| 策略 | 请求 | 起止 | 池wall秒 | HTTP累计秒 | input tokens | output tokens | 其中reasoning |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| PoolAct | 8 | 02:45:14–03:15:54 | 1840.16 | 1839.94 | 162298 | 114588 | 112902 |
| naive | 8 | 03:17:22–03:31:26 | 844.36 | 1604.08 | 160960 | 94959 | 93554 |
| cached | 9 | 03:31:55–03:45:37 | 822.54 | 1305.78 | 207465 | 78156 | 76750 |

合计25次、input530723/output287703（其中reasoning283206）。这三池并非相同真实耗时/算力成本的实验，不能把得分比较写成吞吐或性价比优势。

针对重复现象所做的窄范围只读配置核对没有发现明显不兼容：实际GLM模板把max写成模型可见的 `Reasoning Effort: Max`，但不会额外增加32768硬上限；`clear_thinking=false` 是模板默认且按预期保留历史reasoning。SGLang补出的 `enable_thinking=true` 不是此模板的独立开关，模板本身使用思考前缀。此核对只覆盖配置到源码的作用链，不等于逐请求渲染对照，也不证明长重复由模型、提示或kernel中的哪一层引起。没有因此改动正在运行的对照；源位置与模板SHA见归档 `originals/serving/glm-continuation/SETTINGS-READONLY.zh.md`。

NAS GPU path覆盖不能夸大：GLM Pool只有1 canonical节点；DeepSeek Pool为2节点，但旧80字符ID也不同，因此实际GPU没有触发旧碰撞，且没有可见E→E多步边。完整身份碰撞路径由CPU回归覆盖，GPU验证真实节点/显示/清理/结算链路。

DeepSeek NAS两次 `legacy` fallback保留。其中Pool成员实际选择当时可见的同伴好配置，却因自身history无匹配被legacy替换；保持该次选择的静态敏感度使MI增加1.61759个raw-accuracy百分点，BoN不变。这符合明确政策而不是意外scalar bug；`submitted`还包含离线评估未知提交，不是只读取共享cache。没有实现新政策或补写原成绩。[实际例子、7个CPU控制与边界](ARCHIVE_INDEX.md#other-evidence)

| 场景 | 必须报告的指标 | 未交付/缺失处理 |
| --- | --- | --- |
| NAS | 保存 raw accuracy 的 MI、BoN | 必要成员缺配置则完整 MI/BoN unknown；不自动追加 Gap0 |
| Audit | EA-MI、EA-MV、LA-MI、LA-MV | 用原评分结果；EA 不从 `answer_perf` 的 LA 代替 |
| 对照 | cached−naive、PoolAct−cached、PoolAct−naive | 所需端点未知则差值未知，保留正、零、负 |

三个层次分别验收：

1. **执行完整性**：冻结 source/config/result、成员原件、已有 validation/score_check 与全部请求可追溯。
2. **工具与输出保真**：真实任务中的工具调用、ID、history、forced final 及完整输出没有已知传递损坏；HTTP/JSON 成功或评分通过不能代替这一层。
3. **科学表现**：固定任务/预算/策略上的实际得分和差值。技术通过不保证改善，合法错误或零分也不自动证明 serving 故障。

现有 validation 被引用而非在导出时再次调用 scorer。主/详细报告填入实际数据后的独立最终数值/逻辑复核已通过：76个报告数值单元、122项CSV一致性检查，以及费用、协议、旧排名和结论边界均无阻断问题。[完整复核记录](ARCHIVE_INDEX.md#other-evidence)位于归档 `originals/reporting/FINAL_REVIEW.zh.md`，保存检查版本SHA并明确允许这处非数值状态更新；不从工程检查推断普遍性能提升。

## 6. 资源与完整索引

Task smoke 与 API replay 分别统计所有物理尝试，包括v1与模型协议失败。实际共101次任务请求及40次回放；任务请求包括旧GLM29、新GLM25、DeepSeek47。Deep baseline 1205016为8.34 allocated GPU-hours；candidate 1205022为6.15778；旧GLM 1205018为27.27111；新GLM1205034为6437秒×16GPU=28.60889；合计70.37778 GPU-hours。均按allocation一次计，包含启动/等待，不叠加job steps，也不是纯推理利用率。四个作业均由ROOT在全部已派发请求完成/flush后主动释放，不是取消未结束样本。新GLM最后任务03:45:37完成，最终control四路200后，ROOT于03:46:31释放。reasoning包含于output，cached input包含于input，不重复相加；模拟反馈秒、请求wall之和、实验历时和GPU-hours不互换。

物理 `transport_failure/http_failure/malformed_response` 等失败与模型协议违规分别计数。HTTP 成功但模型一次生成多调用，不改记 transport failure。未识别或未结束 state、缺 usage、SUMMARY 不完整时保留未知费用与失败总数，已知子计数另列。每 agent 保存原 api_calls、answer_source、protocol_failures，不据此自动判定“已修复”。

实际141次物理请求均成功返回，没有transport/HTTP失败；任务执行中的10次协议违规为9次多调用、1次length。141次均保存input/output/reasoning用量，但cached-input用量全部未知，不能补零。

| 范围 | input tokens | output tokens | 其中reasoning | HTTP累计秒 |
| --- | ---: | ---: | ---: | ---: |
| 全部task（含旧Audit） | 1145618 | 504817 | 465296 | 7792.49 |
| 全部replay（含v1） | 73874 | 169547 | 162568 | 1917.97 |
| 合计 | 1219492 | 674364 | 627864 | 9710.46 |

12个primary池的93次请求为input1011567/output415214；不把旧Audit的8次调用隐去。20条成本账中18条实际请求账完整，旧2个未启动槽保留unknown。因此INDEX中计划槽口径的 `all_physical_attempt_ledgers_complete=false` 不表示已发生调用缺账。七项导出共277892字节；INDEX固定171个实读输入身份，SHA为 `d0445e686b9894c821840ffce47568da440c65574ced2d9d5433ebe612244368`。

完整数据入口：

- [原始 dump 机器清单](INDEX.json) · [完整人读存档索引](ARCHIVE_INDEX.md)。
- [逐池 CSV](per_pool.csv) · [逐成员 CSV](per_agent.csv) · [三策略绝对值与差值](comparisons.csv)。
- [全部物理尝试](physical_attempts.csv) · [费用与未知分母](costs.csv)。
- 已有原始回放：[v1](ARCHIVE_INDEX.md#other-evidence) · [v2 c1](ARCHIVE_INDEX.md#other-evidence) · [v2 c4](ARCHIVE_INDEX.md#other-evidence)；[逐回复分类 CSV](ARCHIVE_INDEX.md#other-evidence)。
- 代码与输入：[导出器](ARCHIVE_INDEX.md#other-evidence) · [精确选择 spec](ARCHIVE_INDEX.md#other-evidence) · [接口/复现说明](ARCHIVE_INDEX.md#other-evidence)。
- [旧五模型详细报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911/README.zh.md) · [旧原始 dump 与聚合完整索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911/ARCHIVE_INDEX.md)。

### 归档内的原文件定位

诊断证据、计划和脚本统一从[其他证据](ARCHIVE_INDEX.md#other-evidence)进入，不要求另行公开一份诊断目录树。诊断根目录内的原件使用 `originals/<诊断根相对路径>`，例如 `originals/graph_collision_census.json`、`originals/v2_contract_review/classification.csv`、`originals/graph_smoke/` 和 `originals/reporting/spec.json`。诊断根以外的引用输入使用 `references/<workspace相对路径>`。

[RAW_INDEX.json](RAW_INDEX.json)将原绝对/相对路径映射到 `public_member`、archive、bytes 和 SHA；按该映射查找 `payload/manifest.json` 与对应分片中的精确 member。回放文件 `response.body.bin` 在归档中改名为 `response.raw.json`，字节不变，不能只依旧文件名猜位置。[INDEX.json](INDEX.json)与[完整存档索引](ARCHIVE_INDEX.md)提供整体入口。

原件/输入身份、已有验证声明与本次新实读核对范围必须分别标注。此次报告不重封旧归档、不替换旧评分，也不将小规模诊断添加到原正式矩阵。
