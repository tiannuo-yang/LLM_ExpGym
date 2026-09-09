# Kimi-K3 v5：节点故障原始 cohort 的阶段报告

本次入口仅提供**已闭合的阶段报告与 31 件便捷原件**，供网页查看结论、CSV、故障归属及独立审查证据。这不是完整数据交付完成或全项目验收声明。

完整 34 包目前仍在本地打包／恢复核验收尾中，**本叶目录尚未发布全量 raw payload；远端完整恢复与 AN2 异地描述性分析 replay 均未完成**。后续将在同一叶目录追加完整数据、可执行恢复命令和独立验证证明。GLM 此时仍未闭合；本页只解释已封存的 K3 节点故障 cohort，不得据此宣称双模型结论。

## 先读结论与限制

阅读 [15:15 阶段报告](analysis/k3_interim_analysis_v1/README.zh.md) 后务必同时阅读 [15:30 补记](analysis/k3_interim_analysis_v1/ADDENDUM_1530.zh.md)。原件保留当时状态和措辞，不回写历史；补记纠正“NASBench 106 次”的排版歧义，补充独立用量及论文设置复核。

以下直接摘取已冻结报告的六个预定主对照，未重新计算指标。Exp 效应为 Free−Tight（正值表示退化）；Pool 效应为同 N4、同模拟反馈预算 PoolAct−Naive（正值表示改善）。Search/Audit 分数为 0–1，HPO 为 Gap points。

| 预定主对照 | baseline → target | 效应 | 限度 |
| --- | --- | ---: | --- |
| Exp Search whois F1 | 0.658862 → 0.170136 | 下降 0.488726 | 39 题，R1 |
| Exp Audit evidence accuracy | 0.894419 → 0.515837 | 下降 0.378582 | 13 文档，三个固定 order 先在文档内平均 |
| Exp HPO Gap | unknown → 89.683717 | unknown | 九任务×R3，完整端点缺项，不以 26/27 子集补值 |
| Pool Search voted F1 | 0.212871 → 0.304324 | +0.091453 | Tight，N4，39 题 |
| Pool Audit voted evidence accuracy | 0.737557 → 0.936652 | +0.199095 | Moderate，N4，default order |
| Pool NAS101A Gap-MI | 93.427698 → 95.504557 | +2.076859 | Tight，N4，R3；描述 SD 3.410222 |

Search/Audit 已完成主对照支持本次设置下的 ExpGym 下降及 PoolAct 改善；不能写成 HPO 全面稳定改善或跨模型复现。NAS101A 三次 Gap-MI 差值为 0.118654、0.097297、6.014625，均值受第三次影响；同条件 Gap-BoN **反向 −0.115490**。所有 CI/p 均 null，R1 不造 seed 方差，固定 orders/N4 成员不冒充额外随机重复。GLM 此时仍未闭合，不据本页得出双模型结论。

705 invocation 中 697 completed_scored、8 infrastructure_or_integrity_failure，原 execution/score_complete 均 false。见 [全部八项影响](analysis/k3_node_failure_impact_v1/README.zh.md) 与 [八项元数据](analysis/k3_node_failure_impact_v1/FAILED_INVOCATIONS.metadata.json)。失败/partial dump 已全部包含在原 run 的 64,188 文件中，不是被删除的实验样本；本页不授权补跑、resume 或合并新旧数据。

这是一项启用 max reasoning、扩展任务/重复设置的 **custom study**，不是论文主实验逐项精确复现；论文还包含 Think 消融，不能概括为整篇论文关闭推理。模拟反馈预算匹配不表示真实 token、GPU 或时间相等。[论文设置补核](analysis/k3_interim_report_review_v1/PAPER_SETTING_ADDENDUM.json) 保留边界。

## 直接查看表格和独立复查

- [导出简表](analysis/actual_formal_export_k3_node_failure_v2/SUMMARY.zh.md)、[六主＋全部预定对照 CSV](analysis/actual_formal_export_k3_node_failure_v2/effects.csv)、[指标格 CSV](analysis/actual_formal_export_k3_node_failure_v2/metrics.csv)、[配对 CSV](analysis/actual_formal_export_k3_node_failure_v2/paired_rows.csv)。负值、零和 unknown 均保留，不能把 514 条含成本/切片的比较计作独立胜率。
- [logical 状态 CSV](analysis/actual_formal_export_k3_node_failure_v2/logical_outcomes.csv)、[已知子集 CSV](analysis/actual_formal_export_k3_node_failure_v2/known_subsets.csv)、[完整描述结果 JSON](analysis/actual_formal_export_k3_node_failure_v2/results.json)、[原导出索引](analysis/actual_formal_export_k3_node_failure_v2/EXPORT_INDEX.json)。大 JSON 可下载查验，不依赖 GitHub 是否提供页面内预览。
- 独立[评分/投票发现](analysis/k3_post_analysis_metric_review_v1/FINDINGS.zh.md)、[范围说明](analysis/k3_post_analysis_metric_review_v1/README.zh.md)、[摘要](analysis/k3_post_analysis_metric_review_v1/actual_v1/SUMMARY.json)：验证冻结规则的忠实执行，不证明 parser 理想、HPO 后端真值或模型字面最终提交选择正确。
- 独立[汇总与配对审阅](analysis/k3_post_analysis_aggregation_review_v1/README.zh.md)、[摘要](analysis/k3_post_analysis_aggregation_review_v1/actual_v2/REVIEW.json)；其原始审阅针对旧导出，后续 v1→v2 性能数据相等的限定核对见[阶段报告复核](analysis/k3_interim_report_review_v1/README.zh.md)。不能改写旧文件使其看似直接使用新费用版本。
- 独立[用量发现](analysis/k3_post_analysis_usage_review_v1/FINDINGS.zh.md)、[范围](analysis/k3_post_analysis_usage_review_v1/README.zh.md)、[摘要](analysis/k3_post_analysis_usage_review_v1/actual_v1/SUMMARY.json)：16,320 attempts 的已知 input/output/reasoning 为 119,973,435 / 15,715,139 / 13,599,445，各有 63 unknown，完整总量仍 null。Reasoning 已包含于 output，不能再相加；不是收费或 GPU 账单。
- [格式诊断摘要](analysis/actual_format_diagnostics_k3_node_failure_v1/group_counts.json)、[索引](analysis/actual_format_diagnostics_k3_node_failure_v1/INDEX.json)：存在 scorer/vote 接受边界差异，但未替换冻结主分数，也不以共现诊断宣称协调收益的因果来源。
- [提示词审计收据](analysis/actual_formal_prompt_audit_k3_node_failure_v2/RECEIPT.json)：指定 request payload 范围逐条审阅，模板/tool 层无目标字面 marker 命中；模型生成历史中的 313 次观察不是 313 次独立泄漏。该审计不遍历显式 assistant reasoning、不实测服务器 tokenizer 渲染、不穷尽同义词，不能排除隐含 benchmark 识别或训练污染。

## 镜像、附属原件与完整包的关系

`analysis/` 中 29 件是已封存 **917 controls 清单内原件**的便捷字节镜像：保留相对 OP 子路径、原 bytes/SHA，不改 Markdown/CSV/JSON，不增加原始样本。`BROWSER_FILES.candidate.json` 列出原 workspace 路径→此叶目录相对目标路径及每件 pin。未镜像的大型 records、原响应、oracle、逐请求审计和完整证明数据将由后续完整交付提供；本次浏览原件不代替完整 dump，也不能用于宣称全量 raw 已上传。

另两件 `k3_node_failure_impact_v1/*` 是 ROOT 明确追加的独立闭合附属原件，**不在原 917 controls/34 包内，也不继承其扫描通过**。此前阶段报告链接到了它们，而 917 清单没有收录；这个导航缺口被保留记录，没有静默修改已封包。两件与全部 outer 发布材料的发布扫描／核验证据须另列，不能挪用原 917 件的扫描证明。它们仅是八项故障索引，八项实际失败 dump 本来已在原 run 中。

待完整交付的 34 包固定原件总数为 **65,105 / 1,521,531,633 B**：33 raw 包 64,188 文件＋1 controls 包 917 文件。不要把浏览副本重复加进原始样本数，也不要把附属索引当新实验。原[run 封存索引](analysis/sealed_restart_runs_v1/kimi-k3-formal-node-failure-20260909/inventory.json)保留原文件路径与失败身份。

原 Markdown 的直接相对链接尽量闭合；原 JSON refs 和文中绝对路径不改写。它们可能指向未做网页镜像的大文件，不能直接当异地本地路径使用；后续完整恢复成功后，可用 OWNERSHIP_INDEX 和 member indexes 定位同一 workspace-relative 原件。`LINK_CHECKS.candidate.json` 列出直接链接检查及有意不展开的引用边界。

## 完整恢复与异地重分析：尚待完成

当前不提供占位恢复命令，也不把本地检查当远端验收。完整包收尾、上传及 fresh remote clone 核验后，本页将补充 collection 索引、可信 SHA256、实际可运行的恢复命令和完整逐文件对账证明；AN2 异地重分析还需明确依赖布局与派生 source_index，不能承诺原绝对路径可直接复用。

公开恢复无需私密 key，会解压、读字节并做 JSON 安全校验，不等于实验评分／内容分析；恢复范围为原路径、bytes 与 SHA，不承诺原 POSIX mode、owner 或 mtime。既有 wrapper 的 `remote_restore_performed=false` 原件字段不会回写；将来的真实远端恢复事实由独立 operator 证据另行记录。

源码使用、数据归属与许可说明见 [ATTRIBUTION.md](ATTRIBUTION.md) 及其中链接的既有研究说明。这里没有给第三方数据或原仓库重新授予许可证，也不能因没有整库文件就忽略 raw prompt/tool reply 中的数据派生内容。
