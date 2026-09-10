# Kimi-K3 与 GLM-5.3：固定 8 项恢复后的双模型报告

状态：作者冻结稿（以本目录INDEX为精确文件清单）；K3 最终 CPython 3.11 导出、新26有限科学检查与严格不变性独立复核已闭合，**成稿后的非作者 post-report 审阅仍 pending**。旧阶段报告、旧失败、全部费用与重放差异均保留。本报告不是ROOT最终科学接受、新实验授权或公开交付完成证明。

## 1. 结论与范围

在本研究指定的六个主比较上，两模型都观察到 ExpGym Free→Tight 的效用下降，以及 PoolAct 相对同 N4、同反馈预算 naive 的改善。恢复固定 8 项后，K3 九任务 HPO 主项从不完整变为可判定：Free−Tight 为 **8.829193 Gap points**，三个 seed blocks 的描述性 SD 约 **4.645597**；其余五主项不变。

这支持的是这两模型、这些任务、设置与预设指标下的**方向性观察**，不是所有指标退化、所有场景 PoolAct 稳定优胜、统计显著或普遍因果规律。完整负性能比较有 **49 行（K3 41、GLM 8）**；旧 31 行全部保留，补齐后新增的 18 行也全部在随附清单列出。尤其 K3 Moderate NAS 的 PoolAct best-of-4 可以下降，不能用主项的平均成员改善遮蔽。

这是 **Custom study**，不是论文逐项数字复现。Search/Audit 外层 R1，HPO/NAS 三个预声明 seed blocks；未证明 seed blocks 独立同分布。全部 CI/p 为 null，三 orders、四 agents、题目数不能冒充额外独立重复。研究设计已看过开发结果，不能包装成完全盲预注册。v5重启前已存在历史尝试，因此两模型最终manifest各453条Search logical标记为 **mixed_or_unknown**，330条Audit/HPO标记为 **previously_inspected**；不能沿用更早master的reserved/heldout时态。Search seed2/3是两个固定world，不是两次独立抽取的新语料；不证明训练未见。

| 有效统计范围 | Kimi-K3 composite | GLM-5.3 原正式轮 |
| --- | ---: | ---: |
| invocation / logical / agents | 705 / 783 / 1,881 | 705 / 783 / 1,881 |
| 选定完整 invocation / logical | 705 / 783 | 705 / 783 |
| 正常 model_no_answer agents | 0 / 1,881 | 59 / 1,881（3.136629%） |
| 保留的物理 invocation attempts | 713（旧705 + 新8） | 705 |
| 保留的旧 infrastructure failures | 8，未删除/改写 | 0 |

K3 是固定选择原 697 成功项 + 用户批准的新 8 项，不是一个新鲜的 705 项单轮，不按答案/成绩选择最好 attempt。新 8 使用原 task/预算/策略/seed/max_steps/profile，6 个 Pool 全 N4、2 个 Exp 单 agent，共26 owner；不挑池中成员，也不新增第九个样本。两个 ROOT 工程门阶段是原顺序首2、随后6，不据质量高低放行；W32 是原上限，并非恢复期实际并发32。新 deployment/allocation 独立记录，不伪装旧端点。

8 项全在第三 HPO seed block：Exp NAS101C Free/Moderate；Pool NAS101C Moderate naive/cached/poolact、C Tight poolact、A/B Moderate poolact。原失败及未知成本仍在旁账，未重新运行其余697成功项。Exp Audit 每 invocation 内含三个 orders，所以 invocation、logical 与 agent 不能混用分母。

## 2. 六个主比较与全部 outer 值

Exp effect=Free−Tight；Pool effect=PoolAct−naive（同N4、同预算）。Search/Audit 为0–1单位差，HPO为Gap points。表保留六位小数，原始浮点字符串、定义与分母见 [NUMERICAL_EXTRACT.json](NUMERICAL_EXTRACT.json)。R1 的 SD/CI 为 null，不能解释为零方差。

| 模型 | 主比较 | baseline | target | effect | 描述性 outer SD |
| --- | --- | ---: | ---: | ---: | ---: |
| K3 | Exp whois / F1 | 0.658862 | 0.170136 | 0.488726 | null（R1） |
| K3 | Exp Audit / evidence_acc | 0.894419 | 0.515837 | 0.378582 | null（R1） |
| K3 | Exp 9 HPO / Gap | 98.512910 | 89.683717 | 8.829193 | 4.645597 |
| K3 | Pool whois Tight / F1-MV | 0.212871 | 0.304324 | 0.091453 | null（R1） |
| K3 | Pool Audit Moderate / evidence-MV | 0.737557 | 0.936652 | 0.199095 | null（R1） |
| K3 | Pool NAS101A Tight / Gap-MI | 93.427698 | 95.504557 | 2.076859 | 3.410222 |
| GLM | Exp whois / F1 | 0.682651 | 0.230575 | 0.452076 | null（R1） |
| GLM | Exp Audit / evidence_acc | 0.684766 | 0.502262 | 0.182504 | null（R1） |
| GLM | Exp 9 HPO / Gap | 97.911143 | 86.066889 | 11.844254 | 3.633329 |
| GLM | Pool whois Tight / F1-MV | 0.208597 | 0.300050 | 0.091453 | null（R1） |
| GLM | Pool Audit Moderate / evidence-MV | 0.809955 | 0.977376 | 0.167421 | null（R1） |
| GLM | Pool NAS101A Tight / Gap-MI | 88.907337 | 95.258942 | 6.351605 | 2.953989 |

主 E-S/P-S 各39 whois；E-A 为13文档内三个固定 orders 先平均；P-A 为13文档原 default order。E-H 为9任务×3 seed blocks，共27配对；P-H 为NAS101A×3，共3配对。这些配对是描述性分母，不是27或3个经验证的 IID 样本。

| R3 主项 | outer 0 | outer 1 | outer 2 |
| --- | ---: | ---: | ---: |
| K3 E-H | 3.8388051121411433 | 13.02838114996262 | 9.620393810656017 |
| K3 P-H | 0.11865431365261259 | 0.09729738452421088 | 6.014624865194335 |
| GLM E-H | 10.575221880614967 | 9.015643434548231 | 15.941896990979595 |
| GLM P-H | 9.55885053844601 | 5.75358396294348 | 3.7423813427032826 |

K3 P-H 的平均收益明显受第三 block 幅度影响，不能称幅度稳定。两模型 P-S 恰同均值0.09145299145299145：旧独立逐题检查发现39题中11题不同、28相同，6正5负变化在浮点精度内抵消；390对文件路径/SHA均不同。不是跨模型误绑，也不表示逐题输出或行为相同。[原专项](../glm_post_analysis_metric_review_v1/TIGHT_WHOIS_PAIR_CHECK.json)

## 3. 负例、unknown 与测量边界

[全部49负性能行](NEGATIVE_PERFORMANCE.md) 保留原精度、baseline/target、策略、分组与SD；包括Gap/raw及all/family的重复切片，不是49个独立反例或胜率统计。资源/协议负值另留在原514项完整表，不混称质量下降。

- **新补齐后 K3 Moderate NAS PoolAct Gap-BoN：总体98.986955→98.871046，effect −0.115908；NAS101B −0.161576、NAS101C −0.488325。** 相应总体 raw performance BoN effect −0.0003486982098332117。整体、家族和任务切片反复出现，不额外增加样本数。
- 原 **K3 NAS101A Tight PoolAct Gap-BoN98.691632 < naive98.807122，effect −0.115490、SD0.593511** 仍在。其 raw performance BoN effect −0.0008124046855502905。MI提高不保证BoN提高；不是只展示论文表中的有利指标。
- **GLM Exp Audit label_acc** Free0.692308→Tight0.736048，Free−Tight=−0.043741，与主 evidence_acc 下降不同。没有事后换主指标或把真实反向终点解释成汇总错误。
- Cached 不等于 PoolAct。新增K3 Moderate NAS cached总体Gap-MI −0.077726、Gap-BoN −0.147632；原Search/Audit/NAS cached负例均保留。GLM的8负性能行也不变。

| 完整514项比较分类 | 正 | 负 | 零 | unknown |
| --- | ---: | ---: | ---: | ---: |
| K3 | 190 | 239 | 57 | 28 |
| GLM | 286 | 190 | 10 | 28 |

每模型7,687指标格、5,393配对；两模型28个unknown比较及366个null cells均为Pool feedback_visible，仍不补零。所有性能终点现完整，不等于所有遥测字段完整。K3恢复使162个incomplete比较变为可计算，其余原负值/零值按完整表保留。

Gap>100仍有K3 3格、GLM6格；原公式只下限clip0，reference-best不是本次独立证明的全库最优。逐格复核可证明固定oracle算术一致；本次新26的本地NAS表另经有限查询核对（见第7节），但未独立重查全部旧HPO/NAS任务、官方数据转换或证明模型字面最终选择。旧K3已观测271个终态HPO agent（Exp79+Pool192）中，61个为best_evaluated_fallback；6个forced_model_answer的评分来源为offline_final_answer；另204个为matching_tool_call（147 natural+57 forced）。这67项不是全部1,855旧agent的来源分类。新26中19 natural +1 forced为matching_tool_call，另6是best_evaluated_fallback：原本有答案、但未匹配时按既定legacy规则取最高已评估配置，**不是6个缺答，也不是26个都给出了严格有效的final配置**。PoolNAS报告MI/BoN，不是MV；fallback是否等价论文final-answer评测仍是设置边界，不把这6项称为新修好的干净复现。

Search/Audit格式边界完全不受8项HPO恢复影响：K3/GLM Search scorer-set 与 vote-key 不同的agent为62/25（各936），格式边界pool47/23（各234）、scorer-equivalent拆票pool6/7；Audit scorer接受而vote拒绝agent21/2（各312）、格式边界pool17/2（各78）。GLM专项确认7池17agent-pairs拆票、0合票。这是冻结parser/voter的描述，不是修复格式后的反事实成绩，也不能证明收益源于协调或仅源于格式。

## 4. GLM缺答、用量与长耗时

GLM有59正常model_no_answer（1,881 agents的3.136629%，46 logical）；本次逐IID核对也恰为46个不同invocation（41 Search、5 Audit），这是此次观测，不将两种单位一般等同。Search缺答agent54（Exp10、Pool44）、Audit5（Exp2、Pool3）、HPO0。独立原复核逐一确认59/59最后forced-final已发出并收到响应：tool_choice=none，max_tokens=completion_tokens=32768，finish_reason=length，原content长度0、decoder为空，reasoning非空白，原loop记录forced-final length rejection。不是只拿一例推广，不是parser丢掉非空正文，也不是这些调用没被发送；分类unknown0。

这支持“该次明确收尾到生成上限仍无可用正文”的近端机制，**不证明提高预算必然得到答案、正确答案或更优比较结果**；没有独立tokenizer重数。Search/Audit answer=None仍经原scoring_input=''语义复算（空gold可能为1，非统一补0）；N4保留空票，Audit aggregate保留原[] tool_records。HPO缺配置保留unknown，不伪装HTTP/环境/持久化失败；本次两模型完整有效HPO没有model_no_answer。

GLM从正式启动记录05:17:33.061708至ROOT核验execution完成18:42:11.600352，共 **48,278.538644秒（13:24:38.538644）**。这是两记录墙钟差，不冒称单GPU时间或本次直接读取了execution.elapsed字段。

已核GLM output61,759,454中reasoning59,754,394，占96.753436%；18,403 attempts平均output3,355.944900、reasoning3,246.992012。59个length末次调用共output1,933,312，占全output3.130390%。对比K3有效结果，GLM请求数约1.123倍、output约3.867倍、reasoning约4.336倍；这些是描述性工作量差，不是受控吞吐试验。**不能把13小时全归因于推理**：并发、排队、不同模型速度、工具/验证与长尾没有在这里因果分解，无低推理预算消融。

## 5. 成本：有效结果与保留失败分账

reasoning已包含在output内，禁止再相加。以下为已持久化响应的usage核验，不是收费账单、tokenizer真值或全部物理HTTP外部计量。

| 范围 | 请求 attempts | input已知小计 | output已知小计 | 其中reasoning | 每字段unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| K3原段全部 | 16,320 | 119,973,435 | 15,715,139 | 13,599,445 | 63 |
| K3恢复8增量 | 289 | 6,583,556 | 557,858 | 393,241 | 0 |
| K3两段全部 | 16,609 | 126,556,991 | 16,272,997 | 13,992,686 | 63 |
| K3有效783 logical | 16,387 | 124,643,382 | 15,971,159 | 13,781,826 | 0 |
| K3旧失败8的未选用尝试 | 222 | 1,913,609 | 301,838 | 210,860 | 63 |
| GLM全部=有效783 logical | 18,403 | 323,702,359 | 61,759,454 | 59,754,394 | 0 |

K3全尝试为16,546 success +63旧error；全尝试三个complete_total仍为null，不把known subtotal当最终精确总量。原失败消耗不因恢复而抹去；effective指标费用不是项目付出的总费用。ledger以(run_id,request_id)区分身份；source_ref是path+sha256两键，bytes在provenance/original seal按身份查，不伪造未持久化请求费用。

| 顶层Slurm allocation | Start UTC | End UTC | 秒 | GPU | GPUh proxy |
| --- | --- | --- | ---: | ---: | ---: |
| K3原1203653 NODE_FAIL | 09-08 21:52:41 | 09-09 14:25:32 | 59,571 | 64 | 1,059.040000 |
| GLM1203652 COMPLETED | 09-08 21:52:40 | 09-09 18:51:24 | 75,524 | 64 | 1,342.648889 |
| K3恢复1203933 COMPLETED | 09-09 21:02:03 | 09-10 00:09:44 | 11,261 | 64 | 200.195556 |

这三allocation合计 **2,601.884444 GPUh proxy**（elapsed×64/3600），包括加载、开发/smoke、idle、验收和任务，不是formal-only、有效利用率或收费，也不是整个项目所有历史allocation账本。服务steps不重复累计；完成后释放步骤的原137退出不倒置为模型任务失败。

## 6. 设置、修正与提示身份审计

原正式W32 independent invocation，上限不是恒定HTTP并发或GPU满载；每模型8节点×8GPU、四个两节点副本，K3 TP16/EP16，GLM TP16/EP1。原阶段615→45→45；恢复固定8采用首2/后6工程门。Exp HPO九任务（ParamNet adult/higgs/letter、NAS101A/B/C、NAS201三数据集），Pool HPO仅NAS101A/B/C。Exp Search73题（whois39、whatis34），Pool whois39；Exp三预算，Pool Moderate/Tight，三策略naive/cached/poolact。恢复沿用同一冻结v5科学源码/配置/测试86文件，source_tree SHA 0671f352f8980b7360baae6f8e6c98b7336ef50823b0d27ab8e090e5d0a42fdc；新增恢复适配器独立记身份，不把它混作原源码字节未变的证明。[原source acceptance](../source_acceptance_v5_final.json)

max_steps/max_evals=30、每调用max_tokens32768、请求最大推理profile；两模型temperature1，K3 top_p1、GLM .95，top_k未显式设置。base_seed2200，HPO outer标签2200/2204/2208，Pool四成员为该标签至+3；两profile均为seed_labels_only，申请seed不等于服务端确定性、共同随机数配对或相同实际推理量的保证。Moderate=10×c_base、Tight=3×c_base是模拟反馈成本，不是实际LLM/GPU上限，同N4/反馈预算也不等于同tokens/wall。原HTTP timeout3600，失败按原策略分类；没有为成绩更改预算。

Pool本地context cap131072用chars/3近似，Exp本地cap=None；它不是独立tokenizer长度证明。保护历史无法容纳时Pool可以不发送forced final，但GLM上述59例逐一排除此分支，不外推全部调用。HPOBench使用本地Python而非Docker；ParamNet冻结.venv-hpo、其余主.venv；环境运行通过不代表后台真值独立审定。

修正不应仅描述为serving适配：原共享图按min-completion过滤仍可能带入后来的performance/visitor/edge状态；修正为按观察时点重放不可变完成事件。原withheld反馈可能在超预算后经共享图/forced final暴露；现以严格完成时间及观察时钟/预算边界控制发布。原cache future-completion gate本身未被证明全错。另有协议、持久化、usage兼容与正常缺答分类修正；这些可消除不当优势，不保证PoolAct更高。**没有旧/新源并行消融，不可将收益因果归于补丁，更不可把全部旧程序称为错误。** 原格式/投票接受边界和负例照留。[原勘误及独立附件](../dual_model_analysis_addendum_v1/README.zh.md)

提示词通用化去掉源模板中不必要的品牌提示，保留真实空间、工具契约与反馈。原K3已审16,320请求，313 marker observations来自模型生成后回传的历史；GLM18,403请求有126历史marker（oracle102/nasbench10111/contractnli13），来源/混合0。**新K3恢复审计是289请求、8 invocation、26owner完整覆盖，60 marker observations出现在51请求，全部历史（nasbench41/nasbench10119）；source-bound/candidate/mixed均0。不是“所有prompt零命中”。** 重复历史观察不是独立泄漏事件。

提示审计没有遍历全部reasoning、实测服务器tokenizer/chat-template、排除同义表达或由搜索空间识别任务，更不是预训练污染测试。新289原auditor结果经ROOT输出对账，不夸称ROOT另跑逐请求审计；GLM已有ROOT输出核对也不自动改其旧fresh-independent-review字段。

论文ICLR2026主ExpGym表为六个OpenRouter模型、extended reasoning关闭，HPO温度.7、Search/Audit0、Search35题；四-agent表为另三个模型、温度.7、whois18、NAS101A，同时另有Think vs Standard消融。当前两自部署新模型、最大推理、温度1、扩展任务与恢复composite不能逐项复现论文数字，也不能检验其六模型leaderboard重排。主P-H选MI不取消论文同时展示的BoN反例。论文无有效performance记0的文字并未细分各种缺答/基础设施情形；当前HPO缺配置unknown、infra另列的政策不能称为论文所有失败置0的精确复原。依据为本地论文main.tex:272–294、318–324、582–585及[已核设置补充](../k3_interim_report_review_v1/PAPER_SETTING_ADDENDUM.json)、[本轮设置预检](../claim_setting_preflight_v1/README.zh.md)。

## 7. 数值、独立复核与公开重放状态

最终K3输入是 [CPython 3.11 最终导出](../actual_k3_fixed8_composite_export_v2_py311_final/EXPORT_INDEX.json)，EXPORT_INDEX SHA fc68a5a057c45056924b17b91f054311d6cd43dc8174da85892265f8d7758f86。作者已严格核341个不受任务影响的comparison全字段不变，五主项精确不变；合计352整行一致，另11是受影响范围内仍unknown的遥测比较。固定8影响的173比较范围未按结果改动，162个原incomplete变完整。原697来源的775 logical行及7,588个非fixed8 metric rows逐字段一致，不据此冒称重新审过所有原raw。

新独立复核实际完成：232项26-agent算术检查；新8的28个Gap/raw-performance MI/BoN或单agent指标格与独立算术差0；local NAS table lookup对26项/21种architecture均精确匹配已pin的108-epoch本地表，未训练模型或重跑backend评测。**这只证明所查本地表一致；复用冻结configuration_hash并不独立证明图规范化，也不证明官方TFRecord转换正确、整个NAS库正确或训练未污染。** 另逐289请求核恢复usage与账本一致、unknown0；全部两段旧63unknown/totalnull仍保留。独立final检查还确认341全字段、775记录、7,588格、旧23K3负例和五主不变，162变化均在173允许范围，CI/p均null；原3.10严格SD失败另存。两份已冻结原审查为[新26科学/289usage](../k3_fixed8_science_review_v1/REVIEW.zh.md)（INDEX 306cad8bbee247e631743f1cd60b88a140e3d2670a95153e5876896681832f87）及[最终composite严格不变量](../k3_composite_invariance_actual_v2/REVIEW.zh.md)（INDEX 834a3d59fde699d437533fc790675da097bf1990930f5bd5c10aec1bc57f34d3）；全部精确refs列于INPUT_REFS。这些是数据输出后、成稿前的独立有限审查，不冒称成稿后审阅。

历史3.10 composite曾有18个不受恢复影响的次要SD与原K3差1ULP；相同outer值/均值/效应不变，但严格全字段一致性未过。ROOT选择另目录、原AN2/merge代码、K3 CPython3.11.15保持旧K3数值基线；旧3.10导出及失败保留，不覆盖、不调指标或实验。GLM则按明确CPython3.10.12公共原件基线重放。两种解释器仅是分析标准库SD字节兼容配置，不是模型推理runtime变更。**GLM原历史导出仅记裸python3，没有已记录的精确版本证据；本次K3显式3.11由同18 triples精确匹配证据选择，不凭匹配反推K3历史解释器身份。**

GLM已由fresh GitHub commit09ced6f12c5de3a19b01b2f0fc606b7fccd4e8f9完整恢复37bundles、71,634原件，原AN2十输出逐byte/SHA一致，ROOT另件接受；最初3.11的34个次要SD1ULP差异亦保留。公开重放复算既有分数不等于重新运行scorer、NAS后台或模型，完整backend/runtime仍非自包含。**新K3 composite联合公开包、fresh GitHub恢复/AN2重放仍pending**；原K3失败轮已公开不能替代新8与composite交付。

旧独立metric/vote K3 13,402检查、GLM13,560检查均无超容差差异，GLM58项约1e-16差异原样保留；旧汇总两模型各514effects/5,393pairs，usage分别16,320/18,403attempts，GLM59缺答另逐项核实。这些旧审查不能替代新26科学检查或本终稿审阅，更不能升级为所有逻辑无漏洞。报告作者参与恢复runner和原运行操作，最终必须由非作者复核，不自行签ROOT科学接受。

完整精度、负值、unknown与引用见 [NUMERICAL_EXTRACT.json](NUMERICAL_EXTRACT.json)、[NEGATIVE_PERFORMANCE.md](NEGATIVE_PERFORMANCE.md)、[INPUT_REFS.json](INPUT_REFS.json)。准备稿及首次作者metadata键名错误保留为历史，不是科学输入或最终通过证据。
