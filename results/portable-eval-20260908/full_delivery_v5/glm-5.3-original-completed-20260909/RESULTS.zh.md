# Kimi-K3 × GLM-5.3：ExpGym / PoolAct 阶段结果

**GLM：705/705 项完成，科学分析及成稿后复核完成。K3：697 项正常完成、8 项 NODE_FAIL 尚未恢复。** 这是 v5 自 serving 的 Custom study，不是整个项目已完成；本入口冻结时，GLM 完整远程归档交付仍待核验，不能用分析完成代替文件交付完成。

总体观察：在预设主指标上，两模型均出现 Search/Audit 的 ExpGym 预算收紧退化，以及同 N4、同反馈预算下 PoolAct 相对 naive 的改善。但有反向结果、缺失与测量边界，不能概括为“全面、稳定、普适提升”。

## 六个预设主对照

Exp 效应=Free−Tight（正值表示退化）；Pool 效应=PoolAct−naive（正值表示改善）。F1/accuracy 为 0–1 单位差，Gap 为原 points；不是相对百分比。

| 主对照 | Kimi-K3 effect | GLM-5.3 effect |
| --- | ---: | ---: |
| Exp whois F1 | +0.488726 | +0.452076 |
| Exp Audit evidence_acc | +0.378582 | +0.182504 |
| Exp 九任务 HPO Gap | unknown | +11.844254 |
| Pool whois Tight F1-MV | +0.091453 | +0.091453 |
| Pool Audit Moderate evidence-MV | +0.199095 | +0.167421 |
| Pool NAS101A Tight Gap-MI | +2.076859 | +6.351605 |

原 baseline/target、完整精度与逐外层效应见 [数值抽取](analysis/dual_model_analysis_v1/NUMERICAL_EXTRACT.json)。R3 sample SD：K3 NAS-A MI=3.410222；GLM HPO=3.633329、NAS-A MI=2.953989；K3 HPO 全端点 SD=unknown。它们只是三个预定 seed-block 的描述离散程度，非 CI，seed 生效及 iid 未独立证明。Search/Audit 外层 R1，CI/p 全为 null；固定 orders 和 N4 成员不是额外独立重复。

两模型 whois 主增益均值相同，但 39 题中 11 题增益不同、浮点精度内互抵；独立检查未发现跨模型错绑，不是逐题结果相同。

## 不能省略的反例和 unknown

- **K3 NAS101A Tight 的 Gap-BoN：naive 98.807122 → PoolAct 98.691632，差 −0.115490。** MI 提高不保证最好成员提高；MI 三次增益约 0.119、0.097、6.015，也不能称幅度稳定。
- **GLM Exp Audit label_acc：Free 0.692308 → Tight 0.736048，Free−Tight=−0.043741。** 标签准确率没有跟主 evidence_acc 一样下降。
- Cached 不是 PoolAct：两模型均有 cached 负面；GLM NAS-A Tight cached Gap-MI=−0.974949，不能归咎于 PoolAct。
- K3 HPO 27 个计划配对只有 26 个完整，全主端点保留 unknown；GLM 28 个 unknown 比较是 Pool feedback_visible，不因执行完成补零。K3 8 项基础设施缺失不删样、不记模型零分。
- [全部 31 个负性能比较](analysis/dual_model_analysis_v1/NEGATIVE_PERFORMANCE.md)（K3 23、GLM 8）及 50 个 K3 性能 unknown 保留；相关 Gap/raw、all/family 切片不是独立胜率。

历史 scorer 与 vote 接受格式仍有差别；Gap 可超过 100，HPO legacy fallback 也不都等于模型字面最终提交。已完成的有限独立复算不等于 HPOBench 后端全库真值、所有 parser 或全部实验逻辑均获证明。[完整报告](analysis/dual_model_analysis_v1/REPORT.zh.md)

## GLM 59 个正常缺答：原因与保留方式

59/1881 个 agent（Search54、Audit5、HPO0）缺答，涉及46个 logical。逐条独立复核均确认：forced-final 已发送并收到响应，tool_choice=none、max_tokens=32768；返回 finish_reason=length、completion_tokens=32768，原 content 是空字符串而 reasoning 非空。不是这批 final 根本未发或 parser 丢掉非空正文；**增加预算是否改善尚未证明**。

原 answer=None 保留；Search/Audit 使用原空预测评分规则，非一律给0；N4 空票保留，未重抽。HPO 无配置时仍应为 unknown；HTTP/环境异常不能冒充模型缺答。[缺答说明与证据入口](analysis/dual_model_analysis_v1/REPORT.zh.md#4-glm-59-个缺答逐一核实的近端原因)

## 设置与审计边界

每模型 8×8 GPU、四个双节点副本，Pool N4；30 steps/evaluations，单次32k输出、max reasoning、温度1。Exp Search73题/Pool whois39题；HPO/NAS R3，Search/Audit R1，Exp Audit 内含三个固定 orders。模型、服务、推理、温度和题集均与论文主表存在明确差异，**不是 paper-exact，也不足以证明任意模型或统计显著的稳定改善**。

通用图修复将不可变完成事件按观察者时钟及严格预算隔离，阻止已扣留反馈经图回流 final；旧 cache 时间门控本来正确。修复不保证 PoolAct 分数上升，旧真实轨迹受影响数量及补丁因果贡献未量化。详见 [必须合读的勘误附件](analysis/dual_model_analysis_addendum_v1/README.zh.md)。

GLM 指定提示字段审计覆盖18,403次请求，HPOBench字面命中0，126次标记均来自 model-generated history。ROOT复核的是已产统计/provenance/字节，不是 fresh 原请求全遍历；未覆盖所有 reasoning、字段或服务端模板，不排除间接任务识别与训练污染。

## 查验与归档入口

- GLM 原冻结导出：[effects.csv](analysis/actual_formal_export_glm_completed_v2/effects.csv)、[EXPORT_INDEX.json](analysis/actual_formal_export_glm_completed_v2/EXPORT_INDEX.json)、[原件引用索引](analysis/actual_formal_export_glm_completed_v2/source_index.json)。
- K3 原 NODE_FAIL 版本：[effects.csv](../kimi-k3-original-node-failure-20260909/analysis/actual_formal_export_k3_node_failure_v2/effects.csv)、[EXPORT_INDEX.json](../kimi-k3-original-node-failure-20260909/analysis/actual_formal_export_k3_node_failure_v2/EXPORT_INDEX.json)、source_index 原件保存在 controls 恢复包，获取方式见[已公开交付说明](../kimi-k3-original-node-failure-20260909/FULL_DELIVERY.zh.md)。
- [报告成稿后的独立审阅](analysis/dual_model_post_report_review_v1/REVIEW.zh.md)提出两项说明修订；[附件独立复核](analysis/dual_model_addendum_review_v1/REVIEW.zh.md)已关闭 F1/F2。原稿“待审”是当时冻结记录，应结合附件及后续复核阅读。
- 原件路径/SHA索引不等于所有 raw dump 已在线交付；完整文件与归档状态须按实际发布清单查验。本入口不启动实验、不改分数、不把 K3 固定8项未恢复说成完成。

