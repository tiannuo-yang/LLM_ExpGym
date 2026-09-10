# Kimi-K3 与 GLM-5.3：v5 双模型阶段科学报告

状态：作者稿，三路 GLM 独立分析已完成；本报告仍待非作者 post-report 审阅。**K3 尚有 8 项 NODE_FAIL，不能称整个项目完成。** 类型：Custom study，不是 paper-exact reproduction。报告只读取已封存导出、既有独立分析和调度元数据，不新读模型 raw、不重新评分、不调用模型/API、不补跑实验。

## 1. 目前可以得出的结论

在本次预先指定的设置和主指标上，两个模型均观察到 Search/Audit 的 ExpGym Free→Tight 性能下降，以及同 N4、同反馈预算下 PoolAct 相对 naive 的改善。GLM 六个主效应方向均符合预期；K3 五个可判定主项方向符合预期，九任务 HPO 总体主项因节点故障仍是 unknown。

这不是“所有指标下降、PoolAct 全面稳定更好”的结论。GLM Audit 的标签准确率反向变化；K3 NAS101A Tight 的平均成员分数改善，但 best-of-4 略降，主项幅度也受第三次重复影响。Search/Audit 只有外层 R1；HPO/NAS 只有 R3。所有 CI/p 均为 null，不将方向相符当统计显著、机制因果、稳定性证明或推广到任意模型的证据。

| 覆盖单位 | Kimi-K3 | GLM-5.3 |
| --- | ---: | ---: |
| 计划 / 已开始 invocation | 705 / 705 | 705 / 705 |
| 正常完成 / 基础设施失败 invocation | 697 / 8 | 705 / 0 |
| 计划 logical / 正常 terminal logical | 783 / 775 | 783 / 783 |
| 计划 agent / 已观测完整终态 agent | 1,881 / 1,855 | 1,881 / 1,881 |
| 正常模型缺答 agent | 0（1,855 个已观测终态内） | 59 / 1,881（约 3.14%） |

705 invocation 与 783 logical 的差别来自 Exp Audit：一个文档任务内包含三个固定 orders；N4 又产生四个 agent，不能混用分母。GLM 的 59 缺答属于执行正常终止但模型没有可用最终答案，不是 59 个 HTTP/环境失败。K3 未观测的 26 个 agent 保留缺失，不能算成无缺答或错误分数 0。

## 2. 六个预设主效应：保留原 baseline、target 和 R3 SD

Exp 的 baseline=Free、target=Tight，effect=Free−Tight，正值表示下降。Pool 的 baseline=naive、target=PoolAct，effect=PoolAct−naive，正值表示改善；不是把四个 agent 与一个 agent 相比。Search/Audit 为 0–1 单位差；Gap 为原 Gap points，分数越高越好。表中保留六位小数，完整浮点值、比较 ID、outer values 与原文件 SHA 见 [NUMERICAL_EXTRACT.json](NUMERICAL_EXTRACT.json)。

| 模型 | 预设主比较 | baseline | target | effect | outer sample SD |
| --- | --- | ---: | ---: | ---: | ---: |
| kimi-k3 | Exp whois / F1 | 0.658862 | 0.170136 | 0.488726 | null（R1） |
| kimi-k3 | Exp Audit / evidence_acc | 0.894419 | 0.515837 | 0.378582 | null（R1） |
| kimi-k3 | Exp 9 HPO / Gap | unknown | 89.683717 | unknown | unknown |
| kimi-k3 | Pool whois Tight / F1-MV | 0.212871 | 0.304324 | 0.091453 | null（R1） |
| kimi-k3 | Pool Audit Moderate / evidence-MV | 0.737557 | 0.936652 | 0.199095 | null（R1） |
| kimi-k3 | Pool NAS101A Tight / Gap-MI | 93.427698 | 95.504557 | 2.076859 | 3.410222 |
| glm-5.3 | Exp whois / F1 | 0.682651 | 0.230575 | 0.452076 | null（R1） |
| glm-5.3 | Exp Audit / evidence_acc | 0.684766 | 0.502262 | 0.182504 | null（R1） |
| glm-5.3 | Exp 9 HPO / Gap | 97.911143 | 86.066889 | 11.844254 | 3.633329 |
| glm-5.3 | Pool whois Tight / F1-MV | 0.208597 | 0.300050 | 0.091453 | null（R1） |
| glm-5.3 | Pool Audit Moderate / evidence-MV | 0.809955 | 0.977376 | 0.167421 | null（R1） |
| glm-5.3 | Pool NAS101A Tight / Gap-MI | 88.907337 | 95.258942 | 6.351605 | 2.953989 |

E-S/P-S 为 39 个 whois；E-A 为 13 文档、各三个固定 orders 先平均；P-A 为 13 文档的原 default order。E-H 为九任务、三个独立外层重复；P-H 为 NAS101A、三个外层重复。R3 SD 由三个 outer-bundle effects 计算，不能把题目×重复、四成员或三个 orders 充当额外独立 seed 样本。

K3 E-H 的 27 个计划任务配对中有 26 个完整，不能用 available-case 均值替代全端点；outer effects 为 [3.8388051121411433, 13.02838114996262, null]。K3 P-H 三次为 [0.11865431365261259, 0.09729738452421088, 6.014624865194335]，均值明显受第三次幅度影响。GLM E-H 三次为 [10.575221880614967, 9.015643434548231, 15.941896990979595]；GLM P-H 为 [9.55885053844601, 5.75358396294348, 3.7423813427032826]。

两模型 P-S 汇总均值同为 0.09145299145299145，已做独立逐题核对：39 题中 11 题增益不同、28 题相同；11 个变化中 6 正、5 负在浮点精度内抵消（原顺序直接求和差为 2.220446049250313e-16，不宣称任意加法下 bitwise 为零）。390 对原文件路径及 SHA 均不同，没有发现跨模型误绑定造成相同均值；不等于逐题输出相同，也不是两模型行为完全相同。[独立专项](../glm_post_analysis_metric_review_v1/TIGHT_WHOIS_PAIR_CHECK.json)

## 3. 必须同时报告的负面、unknown 与测量边界

- **K3 NAS101A Tight，PoolAct 的 Gap-BoN 98.691632 < naive 98.807122，差值 −0.115490，R3 SD 0.593511。** 相应 raw performance BoN 差值 −0.0008124046855502905。平均成员（MI）提高并不保证最好成员（BoN）提高；论文四-agent 表同时报告两者，不能只报 MI。
- **GLM Exp Audit label_acc 的 Free 0.692308 → Tight 0.736048，Free−Tight=−0.043741。** 主 evidence_acc 下降并不意味着标签准确率也下降。二者是不同测量终点，现有复核没有把它判成汇总错误；没有在本报告中事后换主指标或补造原因。
- Cached 不能等同于 PoolAct。K3 的 cached 在 Search、Audit 和 NAS 多个质量指标上为负；GLM 的 cached 在 Audit Moderate label-MI、NAS A/B Moderate BoN、NAS A Tight MI 为负。GLM 已观测 tuning 负值不是 PoolAct 负值。全部 23 个 K3 与 8 个 GLM 负性能比较（包括相同底层量的 Gap/raw 及 all/family 重复切片）列在 [NEGATIVE_PERFORMANCE.md](NEGATIVE_PERFORMANCE.md)，不是筛选胜率。
- 每模型完整目录都含 514 比较、7,687 指标格、5,393 配对。K3 比较正/负/零/unknown=116/166/42/190，GLM=286/190/10/28。负值中很多是资源/协议指标，不能全称性能下降。GLM 次要负值 190 中仅 8 为性能；182 为资源/协议。K3 有 50 个性能比较 unknown（包括主 E-H），原值全部保留；GLM 的 28 个 unknown 比较及 366 个 null cells 全为 Pool feedback_visible，并不因执行完成而补零。
- Gap 超过 100：K3 3 个，GLM 6 个（100.01772072491956–100.41349998628014）。原公式只下限 clip 到 0；固定 reference-best 不是本次独立证明的全局最优。保留原值；独立评分审阅只核 persisted backend performance 加固定 oracle 的算术，**没有独立重查 HPOBench/NAS 全库、配置有效性或证明模型字面最终选择**。
- K3 tuning 终点有 61 个 best_evaluated_fallback、6 个 offline_final_answer；保留的 legacy 选择语义意味着不能把所有分数都称为“模型最后提交配置的分数”。这与 model_no_answer 是不同问题。

原评分/投票存在格式接受边界，忠实复算不等于规则已最合理：

| N4 格式诊断 | K3 | GLM |
| --- | ---: | ---: |
| Search scorer-set 与 vote-key 不同的 agent / 936 | 62 | 25 |
| Search 格式边界 pool / 234 | 47 | 23 |
| Search scorer-equivalent 拆票 pool / 234 | 6 | 7 |
| Audit scorer 接受、vote 拒绝的 agent / 312 | 21 | 2 |
| Audit 格式边界 pool / 78 | 17 | 2 |

这些是冻结 parser/voter 的描述诊断，不是用统一新 parser 重写后的反事实成绩。GLM 独立 metric 核对确认 7 池、17 个 agent-pairs 的拆票、0 合票；格式共现不能直接证明 PoolAct 收益来自协调或只是格式。原始分数、票和分母未改变。

## 4. GLM 59 个缺答：逐一核实的近端原因

独立重数为 Search 54（Exp 10 + Pool 44）、Audit 5（Exp 2 + Pool 3）、HPO 0；分布于 46 个 logical。59/59 均绑定到唯一原 agent、终态账本、最终 raw 和 wire 记录，结果全部相同：

1. 最后 forced-final 请求确实发出并收到响应，tool_choice=none；不是 final 根本没发送。
2. 请求 max_tokens=32768，原 usage 的 completion_tokens=32768，finish_reason=length。
3. 原 content 是长度 0 的字符串，decoder 提取文本为空；reasoning_content 非空白；没有把 reasoning 当作答案。
4. 原 loop 记录 forced-final length rejection。未发现这些终态是 parser 丢掉非空正文、length 非空拒绝或 context-cap 阻止 final 发送；分类 unknown 为 0。

因此，本批缺答可归为“明确收尾调用在该次生成上限处返回 length，仍无可用正文”，而不是基础设施补零或只凭首个案例推全体。该结论没有独立用 tokenizer 重数 tokens，也不证明增加预算一定能回答正确或改变比较结论。[缺答独立复核](../glm_missing_cause_post_analysis_review_v1/REVIEW.zh.md)

v5 原缺答政策保持：answer=None；Search/Audit 用独立 scoring_input='' 调原评价语义（空 gold Search 可能为 1，非统一给零）；N4 保留空票；Audit aggregate 仍用原 [] tool_records。HPO/NAS 无配置时 unknown，部分池完整 MI/BoN unknown、已知子集仅描述。HTTP、环境、scorer、持久化或完整性异常不伪装成模型缺答。实际 GLM 这次 HPO 缺答为 0。

## 5. v5 设置、HPOBench 提示审计与论文差异

这是用户批准的新 v5 重跑 cohort；此前两模型旧轮次退役、不混入本报告。通用补丁保留正常模型终态并分类，修复自 serving 的协议/持久化/usage 兼容，不通过改答案、筛样或挑重抽来保证预期方向。

- 每模型 8 节点×8 GPU=64 GPU，四个两节点服务副本；K3 TP16/EP16，GLM TP16/EP1；正式 independent invocation 并发上限 32，阶段 615→45→45，不表示始终有 32 个并发 HTTP 请求或 GPU 始终满载。
- Exp HPO 九任务（ParamNet adult/higgs/letter、NAS101 A/B/C、NAS201 三数据集），Pool HPO 仅 NAS101 A/B/C。HPO/NAS 外层 R3；Search 外层 R1；Exp Audit 外层 R1、内含三固定 orders；Pool Audit default order、R1。Pool 三策略 naive/cached/poolact，N4。HPOBench 使用本地 Python 环境而非 Docker 入口；ParamNet 为冻结的 .venv-hpo 解释器，其余使用主 .venv，不能将环境启动成功当后端评分真值的独立证明。
- Exp Search 扩到 73 题（whois39、whatis34），Pool Search whois39；Exp 三预算，Pool Moderate/Tight。max_steps/max_evals=30，单次 max_tokens=32768，max reasoning。K3 temperature=1/top_p=1；GLM temperature=1/top_p=.95；top_k 未显式设置。申请 seed 不是已证明的服务端确定性保证。
- Moderate=10×c_base、Tight=3×c_base 是模拟工具反馈预算，不是实际 GPU 或 LLM token 上限。同反馈预算、同 N4 不意味着同实际总 tokens/墙钟。
- Pool 的本地 context cap=131072，采用 chars/3 估计而不是 tokenizer 真值；Exp 对应本地 cap=None。Pool 在保护历史无法容纳时存在“不发送 forced final”的策略截断分支；本次 GLM 59 缺答逐条均不是该分支。此设置不对称仍须披露，不能据这些 59 例宣布所有上下文边界不存在。

v5 提示词通用化去掉源模板中不必要的 benchmark 品牌提示，但保留实际搜索空间、工具契约、数据与反馈。K3 全 16,320 次已封请求的指定 payload 字段审计无不可审/身份参数结构问题；已审源模板层无目标名称，HPOBench 字面标记为 0。313 次名称观察全部来自模型生成后回传的历史，且是历史重复计数，不是 313 次独立泄漏。GLM 同类 payload 审计覆盖 18,403 次，0 不可审、0 参数/结构问题、126 次 marker hits；命中不自动等于源模板泄漏。

**提示审计边界：**不是模型训练污染测试；不遍历全部显式 reasoning，不实测服务器 tokenizer/chat-template 渲染，不排除同义表达或模型由搜索空间、反馈/预算推认任务。HPOBench 原后端查表正确性也不由提示词扫描证明。GLM receipt 的 fresh independent prompt-review 仍标 still_required；本报告不把 metric/usage 审阅冒充该项独立全请求提示来源审阅。

论文 ICLR2026 主 ExpGym 表是六个 OpenRouter 模型、关闭 extended reasoning；HPO 温度 .7、Search/Audit 0，Search35题。四-agent 表是另三个模型、温度 .7、whois18题、NAS101A；同时有独立 Think vs Standard 消融，所以不能说整篇论文都关闭推理。当前自 serving 两新模型、最大推理、温度1、更广题集/Pool NAS 集是明确偏离，不能称逐项复现论文数字，也不足以检验论文六模型 leaderboard 重排。此报告主 P-H 事前选 MI，但仍报告论文同时展示的 BoN 负面结果。[本地论文与设置核对](../k3_interim_report_review_v1/PAPER_SETTING_ADDENDUM.json)

## 6. 成本：真实 usage 元数据与 allocation 代理分开

下表来自两路独立 usage 审阅的全 attempt 已知小计；reasoning 已包含在 output 内，不能再相加：

| 模型 | attempts | input tokens | output tokens | 其中 reasoning tokens | 每字段 unknown attempts |
| --- | ---: | ---: | ---: | ---: | ---: |
| K3 | 16,320 | 119,973,435 | 15,715,139 | 13,599,445 | 63 |
| GLM | 18,403 | 323,702,359 | 61,759,454 | 59,754,394 | 0 |

K3 63 个 error 用量 unknown，故三个 complete_total 均为 null；不能把已知小计称最终精确总量。K3 775/783 完整 record 的字段子集另为 input118,059,826、output15,413,301、reasoning13,388,585，不与全 attempt 小计混用。GLM 783/783 完整，两种口径同值。usage 是原响应数值归属核验，不是实际收费账单、吞吐 benchmark 或全部物理 HTTP 的外部计量。

| 原 Slurm allocation | Start UTC | End UTC | ElapsedRaw s | allocated GPUs | GPUh proxy |
| --- | --- | --- | ---: | ---: | ---: |
| K3 job1203653 / NODE_FAIL | 09-08 21:52:41 | 09-09 14:25:32 | 59,571 | 64 | 1,059.040000 |
| GLM job1203652 / COMPLETED | 09-08 21:52:40 | 09-09 18:51:24 | 75,524 | 64 | 1,342.648889 |

GPUh=原顶层 allocation ElapsedRaw×64/3600，合计 2,401.688889 GPUh。**这两整个 allocation 含加载、开发/smoke、idle、正式任务，不是 formal-only GPUh、有效计算量、平均利用率或实际收费；不是全项目所有历史 allocation 账本。** 不再把 .batch/.extern/服务 steps 重复累加。GLM 完成后停止服务的 CANCELLED steps 不意味着正式任务被取消；K3 顶层状态确为 NODE_FAIL。[GLM 原调度快照](../glm_formal_service_release_v1/operator_finish_v1/final_scheduler_snapshot.json)

## 7. 复核边界、剩余验收与查验入口

独立 metric/vote：K3 13,402 检查、0 超容差差异；GLM 13,560 检查、0 超容差差异（58 项约 1e-16 的非零浮点差保留）。独立 aggregation 全部两模型各 514 effects/5,393 pairs 对账；GLM 64,103 数值+149,607结构断言通过。独立 usage 分别完整核16,320/18,403 attempts。缺答机制另有逐59条独立验证。这些是有限范围内未发现逻辑反例，不是“仓库所有逻辑无漏洞”。

K3 8 项均在第三 NAS 外层重复：Exp NAS101C Free/Moderate；Pool NAS101C Moderate 三策略、C Tight PoolAct、A/B Moderate PoolAct。全部原失败、费用与缺失保留；Search/Audit 570 invocation 不受该故障影响。新 64 GPU 恢复这固定 8 项仍待用户批准，不在本报告中启动、替换或把原失败改写成通过。补齐后必须新导出/复核全端点，再判断 K3 E-H；本报告不提前替它下结论。

本报告仍需**非作者**在成稿之后重查数值、引用、反例、分母和结论强度；底层已经核过不替代报告终稿审阅。报告作者参与 missing-final/缺答审计实现，主动披露，不自行签署最终科学验收。结果发布也必须有 GitHub-tn 对应 commit/文件清单后才能称已推送；此稿不声称发布已完成。

- [K3 冻结 v2 导出索引](../actual_formal_export_k3_node_failure_v2/EXPORT_INDEX.json)；[GLM 冻结 v2 导出索引](../actual_formal_export_glm_completed_v2/EXPORT_INDEX.json)。
- [K3 独立评分](../k3_post_analysis_metric_review_v1/actual_v1/SUMMARY.json)、[汇总](../k3_post_analysis_aggregation_review_v1/actual_v2/REVIEW.json)、[usage](../k3_post_analysis_usage_review_v1/actual_v1/SUMMARY.json)、[旧阶段报告的独立审阅](../k3_interim_report_review_v1/README.zh.md)。
- [GLM 独立评分/巧合专项](../glm_post_analysis_metric_review_v1/FINDINGS.zh.md)、[汇总](../glm_post_analysis_aggregation_review_v1/ACTUAL_REVIEW.zh.md)、[usage](../glm_post_analysis_usage_review_v1_operator/FINDINGS.zh.md)、[缺答](../glm_missing_cause_post_analysis_review_v1/REVIEW.zh.md)。
- [完整精确数值抽取](NUMERICAL_EXTRACT.json)、[全部负性能项](NEGATIVE_PERFORMANCE.md)、[本报告依赖的文件 pins](INPUT_REFS.json)。完整正/零/资源负/unknown 仍在两冻结 effects.csv，没有改原端点或分析分母。
