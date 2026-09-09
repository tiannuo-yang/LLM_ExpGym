# K3 阶段性报告：结果后独立事实与逻辑复核

被审对象为 ../k3_interim_analysis_v1/README.zh.md，2026-09-09 15:15 UTC 版本，SHA fb44f0aac721f970c89b620752dca9c457b6af266c92ed75024ccdfa4e6d17ab。本 reviewer 不是该阶段报告的作者，也不是 exporter/analysis 候选的作者；此前独立完成本份 K3 冻结输出的汇总层对账。

结论：在以下已绑定、限定读取的证据范围内，未发现实质数字或逻辑错误。报告保留缺 8 项、R1/R3 的分母、次要负值、费用 unknown、提示词审计盲区及单模型/描述性限制，没有将五个已知正效应提升为稳定、通用、因果或跨模型结论。存在一处不影响数值的文字歧义，以及原论文具体设置未在本次范围内独立重核的限制，见末段。

## 实际核对

| 报告内容 | 对照证据与结论 |
|---|---|
| 六个预定主终点 | v2 results 的六条 role=primary 与此前 actual_v2 独立重算逐一一致；报告的六位小数均正确。E-A 是 evidence_acc，P-A 是 evidence_acc_mv，均非 label_acc。 |
| E-H 缺失与 R3 | 固定 9 tasks × 3 = 27 pairs，26 个已知、1 个未知；第三 outer 的 NAS101 C Free 缺失。完整 baseline/effect/SD 为 null，Tight 单侧完整均值 89.68371695757193 可单独保留。没有把 26 个已知 pair 当完整端点。 |
| R1、三 order、N4 | Search/Audit R1 的 SD 为 null；所有 CI/p 均 null。Exp Audit 每文档的三个固定 order 先等权合并；Pool default order 与 N4 agents 均未被报告当随机重复。 |
| NAS A 与次要 B | A Tight Gap-MI=+2.0768588544570528，outer SD=3.410222118292855；三次差值 0.11865431365261259、0.09729738452421088、6.014624865194335。A 同条件 Gap-BoN=-0.11549001032652484。B Tight Gap-MI=+1.3712415962610531、SD=0.37253868386232764，role=secondary。报告均保留且未升主。 |
| 反向与缓存结果 | 全目录包含负值/零/unknown；cached 的 Search/Audit 质量确有多个负值，如 f1_mv=-0.02564102564102564、evidence_acc_mi=-0.031674208144796386。报告未写“缓存处处有效”。 |
| Gap>100 | 与 known_subsets 及 metric review 计数一致：NAS C 100.17721427983435、100.10632786483673；ParamNet adult 100.2922407081013。只下限 clip 的解释正确，没有宣称 reference best 是已证明的全局最优。 |
| persisted endpoints | metric review 的 tuning 来源计数为 best_evaluated_fallback 61、offline_final_answer 6，另有 matching_tool_call 204。报告正确区分 persisted endpoint、模型字面最后提交及模型缺答，并声明未重证后端/最终选择。 |
| 格式诊断 | group_counts 支持 Search 62/936 scorer-set/vote-key差异、47/234边界池、6拆票池；Audit 21/312接受边界、17/78池。报告把这些作为冻结规则的格式诊断，不拿共现作因果归因，也未替换主分数。 |
| prompt覆盖与归因 | SHA绑定的705份job审计元数据含16320 attempts，success16257/error63；0未映射、0不可审、0请求问题。313 hits=nasbench101 204+nasbench 106+oracle 2+contractnli 1，全部 origin=model_generated_history。只跟随审计元数据 refs，没有跟随 raw_ref 或读提示/答案文本。 |
| prompt限制 | 所有 attempt 元数据的 response_and_reasoning_fields_examined=false；receipt 明示未观察服务端tokenizer/template渲染及physical-wire一一映射。报告没有把零模板命中说成隐含识别/训练污染已排除，也没有把313次重复历史观察说成313次独立泄漏。 |
| v1→v2 | 7687 rows、514 effects、5393 paired_rows、comparison catalogue、logical states及known_subsets全对象相等；1881终态仅对数值/状态等非答案字段做相等核对。原完整答案内容相等沿ROOT既有比较，本次不重新展开。records移除reasoning_tokens及telemetry_sidecar.attempt_usage.reasoning_tokens后完全相等。 |
| 费用完整性 | 从v2已有attempt_usage元数据求和：input119973435/output15715139/reasoning13599445；每项16320attempts、63unknown、complete_total=null。raw_request_ids数量与去重后同为16320。与报告精确一致，不能与仅775完成logical的known subtotal混淆。reasoning作为output子集不另相加；非计费/GPU利用率声明正确。 |
| 费用审阅时间点 | “独立全raw费用核验仍在进行”按报告15:15 UTC写定时点理解。没有使用之后的审阅状态倒推该时间记录错误。 |
| 节点故障与封存 | ROOT_TERMINAL记录NODE_FAIL 14:25:32、instance-003、caller signal0、Slurm cancel0；execution finished_at=14:27:39.330705，ROOT实际session exit2。705 reported/697 completed_scored/8 infrastructure_or_integrity_failure与影响索引一致；8项均第三轮NAS。封存64188files/11560dirs/1268512973bytes吻合。 |
| 运行设置 | 两份正式plan只有元数据读取：并发上限32、阶段615/45/45、max_steps=max_evals30、max_tokens32768、max reasoning；K3 temperature1/top_p1，GLM temperature1/top_p.95，正式请求top_k=null。部署各64GPU/8节点/4双节点副本，K3 TP16/EP16、GLM TP16/EP1吻合；未读GLM质量。 |
| 任务与可比范围 | 固定plan支持Exp Search73题、Pool仅whois39；Exp HPO9任务、Pool仅NAS A/B/C；混合R与N4明确。报告将工具模拟预算与真实token/算力分开，没有把同反馈预算写成等真实计算量，且明确是扩展custom study、不是跨模型复现或论文全部claim的确认。 |

独立评分审阅的1855完整个体、360完整N4、1455性能格、39三order组、13402核对及0超容差差异均与其固定SUMMARY一致。本复核引用该已完成审阅，不重新执行评分/投票，也不提升其“reported HPO performance + frozen oracle arithmetic”证据等级。

## 非实质文字提醒与核对限制

1. 被审报告第38行“NASBench106”实指 marker_class=nasbench 的106次命中；建议下一版本写“NASBench 106次”，避免被读成名为NASBench106的benchmark。这不是数字错误，不需要改已冻结版本来使本审阅通过。
2. 第49行“论文原模型/低温/关闭推理配置”中的原论文具体设置，未由本次允许的原plan/deployment/profile及现有review refs独立给出原文出处；本轮未联网或扩大读论文。当前custom study不能声称逐项精确复现、不能推广到所有模型的保守限制本身成立。本项是本次独立核对范围的限制，未发现相反事实。
3. 本次不重读模型答案/gold/HTTP raw、不读取当前GLM质量、不查私钥、不调用模型/网络/scorer/Slurm，不运行先前聚合脚本，不实现新分析器。只写本fresh审阅目录与此前ROOT明确要求的operator小补记；被审报告和原数据未改。

可复查 refs 与投影核对结果分别见 refs.json 和 checks.json。prompt的705份job元数据由receipt.parts逐一SHA/字节核准；该清单原样保存在被引用receipt中，无须复制提示词或答案。

先前汇总审阅真实工具退出的补记位于 ../k3_post_analysis_aggregation_review_v1/OPERATOR_COMPLETION.json：exec_command chunk e1528f，session92586，write_stdin完成chunk bc1d32，actual exit0；与语义passed分列，绑定原REVIEW88f7...与EXECUTION_RECEIPT8ebd...，没有重跑或改旧收据。

本结果仅是已封 K3 阶段报告之后的一次逻辑复核，不能代替补齐8项、新恢复数据、GLM完成结果及最终联合报告冻结后的复核。
