# Kimi-K3 v5 阶段性结果：缺8项，非最终验收

时间：2026-09-09 15:15 UTC。只分析本次用户修订后的 Kimi-K3 正式执行；GLM仍在运行，不能声称已跨模型复现。

## 结论与未完成项

已完成的 Search/Audit 在预定主对照上同时出现 ExpGym Free→Tight 明显下降、同N4/同预算 PoolAct 相对 Naive 改善。独立评分/投票复算及完整汇总对账未发现超预定容差的差异。HPO/NAS不能概括成全面稳定改善：完整九任务R3主终点因节点故障缺项仍为unknown；NAS101A平均成员表现改善，但best-of-4略降，重复间差异也不小。

K3服务于14:25:32被Slurm记为NODE_FAIL，失败节点instance-003。ROOT与agents没有取消本次运行；controller于14:27:39自然返回exit2。705项均已开始，697项completed_scored、8项infrastructure_or_integrity_failure。原execution_complete/score_complete=false不改写。原件全部封存，补跑这8项的新服务恢复仍待用户确认，不能把本报告当全项目完成。

## 六个预定主终点

分数为0–1；HPO为Gap points。Exp的效应是Free−Tight，Pool的效应是同N4、同预算PoolAct−Naive，不是4个agent对1个agent。

|主终点|baseline|target|效应|范围与完整性|
|---|---:|---:|---:|---|
|Exp Search whois F1|Free 0.658862|Tight 0.170136|下降0.488726|39题，R1，完整|
|Exp Audit evidence accuracy|Free 0.894419|Tight 0.515837|下降0.378582|13文档，各3固定order先平均，完整|
|Exp HPO Gap|unknown|Tight 89.683717|unknown|9任务×R3，26/27配对有效，完整端点不补值|
|Pool Search voted F1|Naive 0.212871|PoolAct 0.304324|+0.091453|Tight、N4、39题，完整|
|Pool Audit voted evidence accuracy|Naive 0.737557|PoolAct 0.936652|+0.199095|Moderate、N4、13文档、default order，完整|
|Pool NAS101A Gap-MI|Naive 93.427698|PoolAct 95.504557|+2.076859|Tight、N4、R3，完整；描述SD3.410222|

所有CI和p值均为null。Search/Audit的R1不制造seed方差；Audit固定orders、Pool成员都不是额外独立重复。HPO的R3只作描述统计，不以3次观察证明普遍或显著效果。完整514对照中还包括成本指标及重复切片，其正负总数不能当独立“胜率”。

## 不应省略的反向结果和异常

1. NAS101A Tight的PoolAct Gap-MI三次差值为0.118654、0.097297、6.014625，均值明显受第三次影响；不能仅据正均值称幅度稳定。该条件Gap-BoN为98.691632，对照Naive98.807122，差值-0.115490。NAS101B Tight的Gap-MI差值+1.371242、描述SD0.372539是已完成的次要结果，不提升为事后主终点。其余缺项条件明确保留unknown。
2. 原评分器与投票器仍有格式接受边界不一致。Search的62/936个答案出现scorer-set与vote-key差异，涉及47/234池的格式边界，其中6池出现拆票。Audit的21/312个fenced JSON答案被个体评分parser接受、被JSON-only投票拒绝，涉及17/78池。当前独立复算验证的是冻结实现被忠实执行，不证明这套规则最合理。已做共现诊断，没有采用另一套投票重写主分数，也不能把全部MV收益归因于协调或格式。
3. 3个HPO Gap超过100，不是浮点尾差：NAS101C约100.177214、100.106328，ParamNet adult约100.292241。当前公式只下限clip到0；reported perf超过固定表中的reference best时可>100。保留原值，不将参考best描述成独立证明的全局最优。本次审阅未重新查后端全库。
4. HPO persisted endpoints中有61个best_evaluated_fallback和6个offline_final_answer来源。不能把全部终态都说成模型字面最后提交；这是保留的历史最终答案选择语义，须与“模型明确缺答”分开。
5. Cached并非处处改善：本次已完成的Search/Audit成本条件/质量指标中存在相对Naive的负值。不能将PoolAct的改善概括成任意共享缓存都有收益。

## 提示词：查到了什么、没有证明什么

对封存的16,320份请求逐一检查指定request_payload字段，包括16,257 success和63 error。705 invocation、783 logical、1,881 owner均有可审请求；0不可审、0未映射、0身份/参数/结构问题。

已审system、任务模板、tool schema及配置/混合来源层没有目标名称命中，HPOBench字面标记为0。313次名称观察全部位于模型生成后回传的历史：NASBench101 204、NASBench106、oracle2、ContractNLI1；这是重复历史中的观察次数，不等于313次独立泄漏。名称可能被模型从任务结构推知，不能反推是源模板泄漏。

该词法审计不遍历显式assistant reasoning字段，不实测服务端tokenizer渲染，不覆盖所有同义词。必要搜索空间、反馈与oracle-derived预算本身也可能帮助识别任务，因此不能声称排除了隐含benchmark识别或训练污染。

## 本轮设置与论文可比性

- 每模型8节点×8GPU；4个两节点副本。K3每副本TP16/EP16，GLM TP16/EP1；各模型正式调用并发上限32，阶段615→45→45。
- HPO/NAS R3；Search R1；Exp Audit保留三个固定顺序、外层R1；Pool Audit原default order、外层R1。Pool统一N4。
- Exp Search73题（whois39、whatis34）；Pool Search仅whois39。Exp HPO9任务；Pool只NAS101 A/B/C。没有按已见成绩选题。
- 每次实验max_steps/max_evals=30，单次输出max_tokens=32768，max reasoning。K3 temperature=1/top_p=1；GLM temperature=1/top_p=.95，top_k均未显式设置。正常模型缺答继续执行，不因此重抽。
- Free/Moderate/Tight是工具反馈的模拟成本条件，Moderate=10×c_base、Tight=3×c_base；不是实际GPU/LLM token预算。Pool与Naive反馈预算匹配不代表真实token/时间等算力。
- 这是扩展任务且启用max reasoning的custom study，不是论文原模型/低温/关闭推理配置的逐项精确复现；可支持本注册设置下的描述结论，不等于论文全部claim或所有模型的通用结论。

## 原始数据、费用与复查链

完整原run双遍封存：64,188文件、11,560目录、1,268,512,973 bytes。8个失败及63个error请求均保留，Search/Audit全部570 invocation不受此次节点故障影响。失败8项全在第三轮NAS：Exp NAS101C Free/Moderate；Pool NAS101C Moderate三策略、C Tight PoolAct、A/B Moderate PoolAct。

原v1导出漏读SGLang flat usage.reasoning_tokens；后验新建v2仅修费用字段兼容及同request上限检查，不改运行/评分/原件。v1原17文件保留。ROOT完整比较确认v1/v2的7,687指标格、514效应、5,393配对、1,881原终态完全相同；records仅两个reasoning字段改变。

v2全部attempt已知input119,973,435、output15,715,139、reasoning13,599,445；各有63个error用量unknown，完整total仍null。Reasoning是output子集，不能相加；这里不是实际收费账单或GPU利用率。独立全raw费用核验仍在进行，不能将observer进度值冒充该独立验收。

独立评分/投票审阅覆盖1,855完整个体、360完整N4、1,455性能格、39三order组，13,402核对无超1e-9容差差异；独立汇总审阅覆盖全部514对照、5,393配对与CSV镜像，0超容差差异。HPO后端查表、有效配置与字面最终回答选择未由这两层重证。后续恢复数据、GLM结果及最终联合报告还需各自闭合、复核与发布。

## 查验入口

- [v2完整结果](../actual_formal_export_k3_node_failure_v2/results.json)，SHA445bbde84fe9f2c2027f6eb27409c0cb98d24f1a6d6a59023df9bda87a366900。
- [v2导出索引](../actual_formal_export_k3_node_failure_v2/EXPORT_INDEX.json)，SHAababd4141ab276e32dfa9ec07b39c6b68a571850b6469f3657033f65bd882ba7。
- [原始run封存索引](../sealed_restart_runs_v1/kimi-k3-formal-node-failure-20260909/inventory.json)，SHAb98bbd8d06627b7fb757fb0beac661d40d98d1d94da5098b0fbf1c5d6ab97c66。
- [提示词审计](../actual_formal_prompt_audit_k3_node_failure_v2/RECEIPT.json)，SHA5ec775944fa7d4ecdaa52a4f0a030afc1b036c689260eb72a5aa24c5f0e39845。
- [独立评分与投票审阅](../k3_post_analysis_metric_review_v1/actual_v1/SUMMARY.json)，SHA38f5466ee05b24a1d93280acbef45a87d3139319e64c30c5366cc7a322d2d9df。
- [独立汇总审阅](../k3_post_analysis_aggregation_review_v1/actual_v2/REVIEW.json)，SHA88f7ea922c11c9f2346e8abeca5f94c2558d848fc5368bd00a7a69c512b249bb。
- [格式诊断](../actual_format_diagnostics_k3_node_failure_v1/INDEX.json)，SHAeb995749fbd2a9f5251b81c2a6d97a48d232dccd2e3e68aefcc81d6531528b6b。
- [8项故障影响](../k3_node_failure_impact_v1/README.zh.md)。本报告原run数据发布清单正在准备；未声称这份正式结果已在GitHub完整交付。
