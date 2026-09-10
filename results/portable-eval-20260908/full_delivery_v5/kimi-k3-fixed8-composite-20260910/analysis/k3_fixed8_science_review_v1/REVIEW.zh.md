# K3 固定恢复8项：独立有限科学核验

结论：固定新8 invocation / 26 agent / 38结果文件通过本次**来源、原评分算术及固定本地NAS101表一致性核验**；289次请求的用量也经另一非exporter/merge作者独立核验。
这不是新实验、重新选样、替代评分或最终报告后的独立审稿。旧8失败原件和全部费用保留，不与新Pool成员拼接。

## 核验了什么

实际159a8a exit0：按已接受seal/plan的原38个确切路径和SHA读取，无递归发现结果；固定8全部NAS101 A/B/C outerrep2。
232项检查覆盖26 agent的终态/原final配置与末次匹配工具评分、完整N4的原文件和embedded结果一致、6份summary与aggregate一致、BoN选择及已登记Gap算术。源/结果/控制refs在ARITHMETIC.json，末尾复核不变。
全部26原配置均为JSON dict，且原终态有可评分结果；并未把不存在的答案补为空字符串后评分。

分数单位和方向：原perf为0–1的validation performance；固定oracle转换为
`Gap = max(0, 100 × (perf − mean_perf) / (best_perf − mean_perf))`，越高越好。
这是归一化Gap百分数，不是直接把raw accuracy写成百分数；仅下限截0，不截到100。
NAS Pool使用全N4的MI（分别对四个已截下限的Gap取平均）和BoN（最大perf/Gap），**不是MV**。
原aggregate为BoN，最大perf同分时保留原agent顺序中最早者；没有按新旧attempt再挑最优。
新8共28个登记性能metric cells与最终Python3.11 composite逐项对账，全部delta=0；详见另目录 `../k3_composite_invariance_actual_v2/CHECKS.json`。

## 必须保留的legacy边界

26个agent的来源为19个natural_model_answer+1个forced_model_answer（均matching_tool_call），以及6个best_evaluated_fallback。
这6个不是缺答，也不是26个全都做了strict final-answer独立新评分：在冻结的legacy tuning规则下，已有答案未匹配评分且已有评估记录时，最终采用已评估配置中最高perf。
本次逐项核原eval_records和fallback选择；没有修改该版本化规则，也不能据此将任何改善归因为信息共享。
所有26值有原匹配工具评分，本地表核查另提供其数值一致性证据。

## 本地NAS101表核验

ROOT精确GO为 `../k3_recovery_root_v1/NAS26_TABLE_VALIDATION_GO.json`，SHA `9bfdab7affb5db7914b890bfd7cb4175b29111f4645ad0e4a9d0b5790b2e85cb`。
唯一实际session12288→f0c589 exit0：只执行已pin compact_nasbench101.configuration_hash处理26个原dict配置，查一次SHA固定的423624条maxfidelity表，独立用原1−validation_error/clamp公式对账。
26/26查得到（21个不同architecture hash），26/26 reported_perf逐float精确相同、delta=0；无容差放宽。
数据只经一次拒绝全部GLOBAL/find_class和persistent对象构造的restricted Unpickler反序列化；先有3个纯合成拒绝测试fe8418 exit0。
0 benchmark实例、0 objective/evaluate/原scorer调用、0 ConfigSpace调用、0新模型/训练/网络；core限制0、字节码关闭。实际源函数调用和表读取并未冒称为“纯metadata”。
原表路径/SHA、每配置hash、26原结果ref及逐项值见NAS26_TABLE_CHECK.json。
限制：复用了冻结的configuration_hash，不是独立证明该图规范化算法；只证明已pin**本地**表一致，不证明官方TFRecord转换完整/正确、数据来源真实性或无训练污染，也没有重新训练架构。

## 289次请求用量

独立作者 `/root/paper_matrix/finalizer_contract_review/profile_contract/historical_poolact_evidence` 的代码已由主审全文读完；其39合成检查及唯一actual 8c1fcd exit0证明全289原raw path/size/SHA/sealed-stat和run/request/IID绑定。
原raw JSON仅解释身份/state和response_json.usage数字；不解释回答/推理正文。289全部success，同新run_id，run_id+request_id唯一，8 IID；flat reasoning字段289个均合法，逐次reasoning≤completion。
input=6,583,556，output=557,858，reasoning=393,241；三字段unknown均0，known_sum=complete_total。reasoning已含在output，不能再次相加。
usage_peer下代码、实际attempts、summary、STARTED及RUN_EVIDENCE保留；主审又把全部289逐request值/状态/path/SHA与最终ledger对账，精确相同，而非只比较三个总数。
旧16320成本的保留由独立composite不变量审查处理；两段合计的63旧unknown未补0，完整总量仍null。本核验不是供应商账单或GPU费用验证。

## 失败记录与作者独立性

本审阅者不是runner/exporter/merge或最终报告作者，但曾编写sealer及format/usage审查；没有用自己的sealer结果替代来源和科学检查。
准备脚本78ad85 exit1是本审阅者将summary_artifact相对路径误当绝对路径；只改新review helper的RUN拼接后通过。a0e3a2 exit0输出被工具截断，159a8a只读复核并完整保存；没有改变原件、容差或任何分数。
主审对usage_peer的主读/receipt核验分别fc6e9a、4cffdd及4baccd，未再次运行其actual入口或重读289 raw。
这不是用户要求的“最终报告分析之后再独立复核”；报告冻结后仍须另做。STOP-WRITE随INDEX生效。
