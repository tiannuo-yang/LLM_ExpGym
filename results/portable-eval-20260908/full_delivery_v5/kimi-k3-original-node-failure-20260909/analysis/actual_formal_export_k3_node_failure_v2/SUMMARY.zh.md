# 新方案描述性结果

研究：restart-20260909-v5-kimi-k3-formal；计划单元 783，全部已列出；实际执行完成：False。
共 514 个预定对照，负值、零值及 unknown 均保留。原始缺答 0 条。

Search/Audit R1：SD、CI 均为 null。HPO/NAS R3：仅 outerrep 描述性 SD，全部 CI/p 值为 null。
Audit 三个固定 orders 先在文档内等权平均，缺一则完整端点 unknown；orders 和 N4 agents 均不是额外独立重复。
ExpGym 展示 Free→Tight 的效用退化；PoolAct/cached 分别对比同预算 naive N4。反馈预算匹配不代表真实 token、wall 或 GPU 成本相等。
HPO Gap 每 agent 先 clip，再计算 MI/BoN；缺配置时完整 N4 端点 unknown，可用子集仅另列描述。固定九任务/三家族均衡，任务等权等价家族等权。
reasoning tokens 已包含于 output，禁止相加。费用表是逐 invocation 遥测（Audit 三 orders 分别计费）；实际小时、排队、加载、GPU-h 需独立 allocation 账单。

本适配器仅读取已报告分数，不执行 scorer、投票或模型。原件哈希不是独立评分真相；独立评分/实际完整性以及最终 fresh post-analysis review 均尚未由本候选证明。

|模型|主对照|效应|描述 SD|状态|
|---|---|---:|---:|---|
|kimi-k3|kimi-k3__E-S|0.488726|unknown|descriptive_complete|
|kimi-k3|kimi-k3__E-A|0.378582|unknown|descriptive_complete|
|kimi-k3|kimi-k3__E-H|unknown|unknown|unknown_incomplete_endpoint|
|kimi-k3|kimi-k3__P-S|0.091453|unknown|descriptive_complete|
|kimi-k3|kimi-k3__P-A|0.199095|unknown|descriptive_complete|
|kimi-k3|kimi-k3__P-H|2.07686|3.41022|descriptive_complete|

完整文件：metrics.csv（十列，空 value 表示 null）、effects.csv、paired_rows.csv、logical_outcomes.csv、raw_terminals.csv、known_subsets.csv、results.json、provenance.json。后续 fresh audit 必须另附，不得由 CPU PASS 替代。
