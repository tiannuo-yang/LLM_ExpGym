# Kimi-K3 × GLM-5.3：固定8项恢复后的最终结果

2026-09-10 后续验收：K3 公开数据已完整恢复并通过全量文件检查，原分析的 10/10 输出逐字节重现。[最终恢复／重放凭据](replay_verified_v1/REPLAY_VERIFIED.zh.md)。以下原文末尾的“发布候选”或“尚待追加”描述 1694aa2 发布时状态，历史报告与收据不倒填修改。

两模型的正式有效结果均为 **705 invocation / 783 logical / 1,881 agents**。K3 使用原697项＋用户批准的固定8项恢复，保留原8项基础设施失败与全部成本；GLM 使用原正式705项，不因正常缺答重抽。

六个主比较方向均符合预设，但这是两个模型及本研究设置下的描述性观察，不是所有场景稳定提高、统计显著或论文数字精确复现。完整报告保留 **49行负性能比较（K3 41、GLM 8）**，相关切片不算独立样本。

## 主结果

Exp effect=Free−Tight；Pool effect=PoolAct−同N4、同反馈预算naive。Search/Audit为0–1单位差，HPO为Gap points；不是相对百分比。

| 比较 | Kimi-K3 | GLM-5.3 |
| --- | ---: | ---: |
| Exp whois F1 | +0.488726 | +0.452076 |
| Exp Audit evidence accuracy | +0.378582 | +0.182504 |
| Exp 9-task HPO Gap | +8.829193 | +11.844254 |
| Pool whois Tight F1-MV | +0.091453 | +0.091453 |
| Pool Audit Moderate evidence-MV | +0.199095 | +0.167421 |
| Pool NAS101A Tight Gap-MI | +2.076859 | +6.351605 |

原值、baseline/target、三个HPO seed-block值及描述性SD见[主结果CSV](analysis/dual_model_analysis_fixed8_v2/PRIMARY_RESULTS.csv)和[完整报告](analysis/dual_model_analysis_fixed8_v2/REPORT.zh.md)。Search/Audit外层R1，HPO/NAS三个预声明seed blocks；未证明IID，CI/p均null。K3 NAS-A MI增益约0.119、0.097、6.015，不能称幅度稳定。

## 必须一起看的边界

- **PoolAct不是总赢：** K3 Moderate NAS的总体Gap-BoN下降约0.115908，NAS101B/C分别下降约0.161576/0.488325；原NAS101A Tight BoN负例仍在。[全部负性能CSV](analysis/dual_model_analysis_fixed8_v2/NEGATIVE_PERFORMANCE.csv)
- GLM Audit label accuracy在Tight反而更高，与主evidence accuracy不同。Cached不是PoolAct，另列反例。
- GLM正常缺答59/1881（46 logical）：逐一核实已发送明确forced-final，生成达到32768上限而正文为空、reasoning非空；不是解析器丢了非空正文。全部保留，不据此停止正式实验。
- K3全部16,609个持久化请求包含旧63个error/用量未知，完整费用总量仍null；有效结果费用不能冒充项目总成本。[费用原件](analysis/dual_model_analysis_fixed8_v2/COSTS.json)
- 新26个NAS结果与固定本地表全部数值一致，但6个采用冻结的legacy best-evaluated fallback；不能说26个都提交了严格有效的最终配置，也未证明官方数据转换或无训练污染。
- 提示身份审计的新289请求中60次marker均来自模型生成历史，source-bound/candidate/mixed为0；不是“全部prompt零命中”，也不是语义匿名或预训练污染检测。
- 自部署8×8 GPU/model、最大推理、温度1、扩展题集，和论文的模型/推理/温度/任务设置不同。没有旧/新代码平行消融，不能把观察到的收益因果归于补丁。

## 复核与数据查验

- [完整联合归档与恢复命令](FULL_DELIVERY.zh.md)：旧34包＋新2包，66,643个原件。
- [本研究修补源码的固定提交](https://github.com/tiannuo-yang/LLM_ExpGym/tree/8dfea72931d952ad90f1c722a83957ab23afc6bf)位于独立代码分支；不要把本results分支仓库根的上游代码当作实际实验源码。冻结86文件身份见报告中的source acceptance。
- [新26有限科学核验及289请求用量核验](analysis/k3_fixed8_science_review_v1/REVIEW.zh.md)。
- [合成结果严格不变量复核](analysis/k3_composite_invariance_actual_v2/REVIEW.zh.md)：341个不受恢复影响的效应全字段、775条旧记录及7,588个旧指标格精确保留；旧23个K3负性能比较未消失。
- [成稿后的独立复核](analysis/dual_model_post_report_review_fixed8_v2/REVIEW.zh.md)已完成，未发现阻断问题；[ROOT有限科学验收](analysis/k3_recovery_root_v1/FINAL_SCIENTIFIC_ACCEPTANCE.json)已签署。不是全源码无漏洞的证明。
- [最终K3导出索引](analysis/actual_k3_fixed8_composite_export_v2_py311_final/EXPORT_INDEX.json)和[全部514效应CSV](analysis/actual_k3_fixed8_composite_export_v2_py311_final/effects.csv)。
- [GLM完整原始归档](../glm-5.3-original-completed-20260909/FULL_DELIVERY.zh.md)与[已完成的公共恢复/十输出字节重放凭据](../glm-5.3-original-completed-20260909/replay_verified_v2/REPLAY_VERIFIED.zh.md)。
- 旧失败、Python3.10的K3严格SD差异、GLM首次3.11重放差异均保留。最终分析字节基线分别为 **K3 CPython3.11.15 / GLM CPython3.10.12**；不改模型推理环境。
- K3包内controls只排除一份1,292 B的非实验CPU测试回执：原扫描器因其凭据命名字段拒绝公开，私有原件、身份及失败记录保留；不据此声称实际密钥泄漏。全部实验原件和分母不变，但公开附属引用链并非每个私有回执都可下载。
- 上述1,292 B是包内controls的唯一缺项；外层发布另省略10,383 B的非实验清单复核回执，同样因凭据命名字段被拦截。原件及失败扫描保留，联合归档字节和所有成绩不变，详见[公开范围限定](FULL_DELIVERY.zh.md#公开范围限定)。

本入口当前为发布候选：K3联合公开恢复/重放的实际证明需在完成后追加。冻结报告中的pending记录保留其当时状态，应合读后续独立复核与ROOT验收，不倒填历史通过。部分历史附件保留本机绝对路径，它们是原件身份而非在线URL；可按完整workspace-relative路径在恢复合集的ownership/member indexes中查找，未归档的外部依赖不宣称可恢复。
