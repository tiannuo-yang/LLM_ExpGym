# 双模型阶段报告补充说明 v1

本附件只修正 [原阶段报告](../dual_model_analysis_v1/REPORT.zh.md) 的证据强度与修复范围说明，处理 [独立成稿后审阅](../dual_model_post_report_review_v1/REVIEW.zh.md) 的 F1/F2。原报告目录六个文件全部保留不改；原分数、代码、实验设置、缺答规则与统计分母均未改变，无新模型调用、重新评分或补跑。应将本附件与原报告合读；数值以原冻结导出为准。

## F1：R3 是预定 seed-block，不是已证明 iid

原报告第 40 行“三个独立外层重复”应读作：

> E-H 为九任务、三个预定外层 seed-block 重复；P-H 为 NAS101A、同样三个外层重复。服务端 seed 生效及统计独立性未在本研究中独立证明；SD 只描述三个 outer-bundle effects 的样本离散程度，不是 CI。

不同请求 seed 标签、不同副本初始化 seed 或相关 deterministic 设置，不自动证明三个外层样本独立同分布。原计划明确 seed_control 未经 planner 验证，不能从 R3 标签推导出服务端采样已受控。这里更正的是措辞与证据强度，**不修改原 R3 sample SD 或任何主效应数值**。

Search/Audit 仍为外层 R1；Exp Audit 的三个固定 orders、N4 成员、题目×重复均不能扩作额外独立样本。所有原 CI/p 仍为 null，不增加显著性、稳定性或普适性结论。具体原计划/部署核验见独立审阅 F1。

## F2：真实通用图隔离修复，不只 serving 适配

原报告 §5 应补充下面两项模型无关、上游已有的漏洞与修复。它们不是仅某个模型的 template/transport 适配问题，也不是已证明由某次整理代码新引入。[既有三版本代码审阅](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/review/REVIEW.zh.md:45) 保留了上游与 v3 的代码对照及确定性反例。

| 问题 | 旧逻辑边界 | 冻结 v5 的修复 |
| --- | --- | --- |
| 共享图混入未来事件 | 用节点最早完成时间过滤，却把后续 performance、visitor、edge 合并进节点/图；早期视图可能看见后续事件。 | 保存不可变的完成事件；按完成时间不晚于观察者时钟、且严格小于反馈预算上界的事件重放视图，不直接暴露未来合并状态。 |
| 已扣留反馈又进入 forced-final | wrapper 先发布结果；loop 在累计模拟 cost≥budget 时扣留该次反馈；之后图注入可能再次显示同一结果。 | 仅 completion_time<budget 时发布新的 cache/graph 结果，图注入同时接收观察者时钟与严格预算上界，防止这一被扣留结果经图回流。 |

精确实现入口：[不可变完成事件](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/extras/parallel_cache.py:879)、[按时钟/预算重放](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/extras/parallel_cache.py:1086)、[严格预算发布](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/extras/parallel_cache.py:1788)、[注入绑定时钟及预算](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/extras/parallel_cache.py:1951)。[原 loop](/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v5/LLM_ExpGym/expgym/react_loop.py:438) 仍保留达到/超过预算时扣留反馈的政策；不是提高或放松反馈预算。独立审阅 F2 另核了生产 runner 的 budget 接线及相关反例测试源码，本附件没有重新执行测试或实验。

必须保留的边界：

- **旧 cache 对未来完成结果的时间门控本来正确。** 问题是共享图的事件快照和预算扣留后的可见性回流，不能泛称“旧缓存全部错误”。
- 图修复恢复可见性隔离，可能减少 PoolAct 旧有的不当信息优势；**不保证提高 PoolAct 分数**，也不能拿当前正方向作补丁有效性的因果证明。
- 旧真实轨迹中实际发生多少次泄漏、模型利用多少次、每个补丁对成绩的反事实贡献，均未量化。既有 synthetic 反例证明逻辑路径，不等于真实成绩影响估计。
- 通用图修复与 K3 特定 template/transport 适配须分开披露。当前 Search/Audit 的历史 scorer/parser 与 vote 接受边界仍保留，原报告的格式差异、拆票、负面与 unknown 不变；不能描述成“所有解析已统一修好”。
- 本补充不把图漏洞指认为本轮 GLM 59 个缺答的原因。那些终态已有逐条独立近端核验：forced-final 已发送，返回 length，32768 completion tokens 后正文仍空；原说明与限制不变。

## 可选补充：GLM 提示审计的有限统计

[ROOT 已产审计统计核验](../glm_formal_postseal_go_v1/ROOT_PROMPT_OUTPUTS_VERIFIED.json) 确认：指定审计字段覆盖 18,403 次请求；HPOBench 字面标记为 0，source-controlled/mixed marker 命中为 0；126 次命中均在 model-generated history（oracle102、nasbench101 11、contractnli13）。历史中重复出现的名称观察次数不等于独立泄漏事件，字面零命中也不证明任务不可识别。

该 ROOT 核验检查已有审计输出的统计、provenance 和字节绑定，**不是 fresh 逐一原 request-payload 来源审阅**。它未遍历全部显式 assistant reasoning 字段、其他未审请求字段/JSON keys 或服务端渲染模板，不排除间接 benchmark 识别、同义表达或预训练污染；不得升级原报告的 fresh-full-prompt-review 状态。

## 不变的阶段状态

仍是 K3 697 正常完成 + 8 NODE_FAIL、GLM 705 完成的阶段报告，不是最终项目完成。固定八项恢复待用户授权新 64 GPU；本附件不启动恢复、不覆盖失败、不重抽缺答、不改变任何结论端点。原报告十二行主数值、31 个负性能比较、50 个性能 unknown 及成本口径均保持。

作者只负责本说明修订和 exact refs 固定；本附件仍交原独立非作者审阅者核验，不自行作最终科学验收。所有依赖为有限明列文件，见 [INPUT_REFS.json](INPUT_REFS.json)，不递归重建 raw 证据链。

