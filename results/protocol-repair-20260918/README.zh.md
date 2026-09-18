# 协议修复、全量评分与行为分析交付

[完整主报告](../paper-analysis-20260916/README.zh.md) · [附件](../paper-analysis-20260916/APPENDIX.zh.md) · [主比较 CSV](main/COMPARISON.csv) · [主要结论的新旧对照](conclusion_delta.csv)

主实验 4,698 个结果全部采用，严格评分完整 4,687 个；正常无答案继续使用原有全分母规则，不将基础设施失败补零。 所有相关旧结果均重新提取终答、评分及聚合：主实验 4,698 个结果、11,286 个成员；Whois sweep 1,170 个结果，其中 234 个 β10 结果复用主实验，去重为 5,634 个结果、12,222 个成员。结果数量与评分完整数量的含义分别保留。

## 评分层及受影响样本

- [所有样本的评分层对照](score_layers/README.zh.md)：旧正式评分、之前 23 个成员／19 个池的诊断、全量旧轨迹重评分，以及正式新采用结果。未做过诊断的样本留空，不虚构诊断分数。
- [全量旧轨迹新旧差异](rescore/main/sample_diff.csv)：57 个样本有任意指标变化；41 个有任务端点变化；39 个有论文主指标变化。这些计数仅属于旧轨迹重评分层。
- [HPO 97 池新旧运行对照](rerun_adoption/NEW_RUNTIME_COMPARISON.csv)：保留旧分数、旧轨迹重评分及新运行分数、来源和替换原因。
- [全部 4,698 项正式新旧评分与原因](control_flow_adoption/new_official/sample_diff.csv)、[最终采用清单](control_flow_adoption/FAIRNESS_MANIFEST.json)与[全部逐样本来源](main/SOURCE_SELECTION.csv)：正式采用 97 个 HPO 整池补跑、21 个 Search/Audit 完整运行槽，以及独立的 1 个 GLM β20 sweep 控制。全部按版本或解析控制流差异选入，不按得分挑选尝试，不拼接池成员。

## 代码版本与公平对照

[HPO 每模型、预算、策略版本核查](hpo_versions/README.zh.md)覆盖全部 486 N1 与 324 N4 原结果。63 个旧图协议 POOLACT 池全部补跑，31 个 Gemini 基线匹配 OpenRouter，另 3 个 HPO 池因中途终答接受时刻改变而补跑。Search/Audit 全量中间响应资格核查另识别 21 个主实验槽；[证据与选择理由](review/search_audit_control_flow/README.zh.md)同时列出独立 sweep 控制。

终答／投票和图修复核心固定于 `0e6c51b6d86f42437038518c2fc8adc510901c0b`；通用原生运行源码固定于 `ffca5704580b75e254f6e52dd4fe9dff104b1be8`。DeepSeek Audit 为保留其历史提示，只恢复旧 `_build_context`，独立源码固定于 `885a5bd70dffe02b8dd610f1699e9f675da2b926`；parser、运行循环和图实现与通用修复版保持相同。见[运行源码说明](../../studies/protocol-repair-20260918/README.zh.md)及[DeepSeek 提示保留说明](../../studies/protocol-repair-20260918/DEEPSEEK_AUDIT_RUNTIME.zh.md)。

新旧运行差值包含重新采样的影响；Gemini 对照还涉及预先声明的 provider 迁移，不能将差值单独归因为图修复。相同反馈预算也不等于相同 token、计算量或实际费用。已有轨迹重评分保留原行动；只有列明的真实补跑才使用新的运行轨迹。图状态的两次锁读取竞争与 Audit 历史固定调用示例不属于此次修复。

[实际运行与费用账本](operations/README.zh.md)公开 119 个运行槽、467 个成员及全部 3,776 次 HTTP 尝试；包括原客户端恢复的两次传输错误。GPU allocation 时间含加载与等待，和 provider 实报费用分别列出。

## 行为、证据与案例表

- [HPO 486 条行为统计](hpo_behavior/README.zh.md)：每预算 162 条；评估次数、停止原因、预算利用率、最终可评分性及历史 480→486 对照均已导出。
- [Audit 正式采用行为与证据](audit/README.zh.md)：全部 702 N1、468 池及 1,872 成员，采用补跑后的实际行动重新分析。
- [Search 行为与配对表](search/) · [POOLACT 增益](poolact/) · [配对案例](cases/) · [排名与 regret](display/)。
- [Whois 正式预算分析](whois/README.zh.md)：β1、5、10、15、20 完整曲线及实际成本；β10 复用关系保持可核验。

旧轨迹重评分的 Audit、Whois 分析分别保存在 [audit_existing_trace/](audit_existing_trace/README.zh.md) 与 [whois_existing_trace/](whois_existing_trace/README.zh.md)。修复前主报告保存在 [README.pre-repair-297c3d0.zh.md](../paper-analysis-20260916/README.pre-repair-297c3d0.zh.md)；更早 ad03 文档、CSV 和归档索引保持原字节。中间发布 `2a78fc8` 的五份原文另存为 `*.interim-2a78fc8.*`；阅读其当时关联的数据，应使用[该固定提交的报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/2a78fc8ef0d0882d0e94080f0bbfec1fc789946a/results/paper-analysis-20260916/README.zh.md)。

## 公开复算

在仓库根目录运行：

```bash
python3 tools/verify_lightweight.py
python3 tools/verify_protocol_repair.py --full
```

[复算说明](../../tools/VERIFY_PROTOCOL_REPAIR.zh.md)明确依赖、输出目录和检查范围；[完整公开回放收据](review/FULL_PUBLIC_VERIFICATION.json)记录本次验收。公开包自带按哈希固定的历史 scorer，浅克隆或不含 `.git` 的源码副本也可以重算。它重新执行终答 parser、任务 scorer、投票及采用合并，再重建主表和行为分析；不是只核对已经保存的最终分数。

HPO 的轻量评分包使用已实际查表核验的性能证书；再次独立查询完整 benchmark 需要另行准备冻结数据与相应依赖。原始请求、完整 trajectory 和所有尝试继续本地留档，公开最小评分输入及来源哈希不冒充原件全量语义审核。
