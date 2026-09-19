# POOLACT 回退交付（2026-09-19）

[当前主报告](../paper-analysis-20260916/README.zh.md) · [完整比较 CSV](main/COMPARISON.csv) · [逐样本回退对照](selection/sample_rollback.csv)

本版恢复全部 **2,196 个 N4 槽位**的修复前结果与来源，覆盖 naive、cached、POOLACT 三种策略和已补齐的 Gemini。**2,502 个 N1 槽位**保留 `7776f70` 的分数与来源，包括单体终答修复、两个 Audit 实际控制流补跑、Gemini 补齐和 486 条 HPO 行为。独立 Whois N1 sweep 也保持不变。

这次是完整范围的版本回退；未调用模型，未按分数挑选槽位或拼接池成员。旧运行仍保持真实的执行版本，不标为由当前代码重新生成。此前诊断和修复候选独立留作历史材料，当前 N4 采用既有运行结果。

相对上一正式版 `7776f70`，共有 **148** 个槽位的任一指标改变，其中 **126** 个论文主指标改变；**116** 个来源恢复为旧原件。所有变化均属于 N4，N1 逐字段不变。恢复的运行来源包括 97 个 HPO 池和 19 个 Search/Audit N4 槽位。

POOLACT 高于两基线的组合数恢复为 **31/36**，Tight 为 **17/18**。[相对回退前 7776f70 的结论对照](rollback_conclusion_delta.csv)与[相对 297c3d0 的结论对照](conclusion_delta.csv)分别列出，避免混淆比较基准。

| 内容 | 入口 |
| --- | --- |
| 4,698 个标量、原件 SHA、逐槽恢复原因 | [selection](selection/ROLLBACK_MANIFEST.json)、[来源](main/SOURCE_SELECTION.csv) |
| 7,767 行聚合、126 行排名、1,298 行比较 | [main](main/CHECKS.json)、[排名](main/dimension_rankings.csv)、[比较](main/COMPARISON.csv) |
| N1 主成绩与 regret | [展示表](display/n1_main.csv)、[逐任务 regret](display/hpo_task_regret.csv) |
| N4 三策略全部指标和主增益 | [全部指标](poolact/poolact_all_metrics.csv)、[主增益](poolact/poolact_primary.csv) |
| Audit：N1 当前、N4 历史的行为与证据 | [方法与重放](audit/README.zh.md) |
| 保留的 486 条 HPO 行为导出 | [行为 CSV](../protocol-repair-20260918/hpo_behavior/README.zh.md) |
| 保留的 Whois sweep | [预算表与图](../protocol-repair-20260918/whois/README.zh.md) |
| 当前代码回退清单 | [源码恢复与N1保留](review/CODE_SOURCE_MANIFEST.json)；固定代码提交 `ba4b39ed46b445288c2ba04f65dade33621c64a5` |
| 本次公开构建核验 | [CHECKS](CHECKS.json)、[独立采用规则](selection/ROLLBACK_MANIFEST.json) |

公开重建只需 Python 标准库，在仓库根目录执行：

```bash
python3 results/poolact-rollback-20260919/tools/rebuild_rollback.py --repo . --output /tmp/poolact-rollback-rebuilt
```

输出包括选择、主表、展示、Search、POOLACT、案例、Audit 的全量重建及 `docs/` 三份报告。四份分数/来源输入均固定 SHA256；N1/N4 按 system 字段确定性选择。Audit 从对应版本的公开假设/成员叶表重建 31 张 CSV，并与主表检查来源和 LA/EA。此命令复算选择及聚合，不重新调用模型或重新执行已撤回的 N4 评分器。

[7776f70 完整历史交付](https://github.com/tiannuo-yang/LLM_ExpGym/tree/7776f700902db194c69124b1a5f59d985379cfb3/results/protocol-repair-20260918)保留旧分、诊断、修复评分、修复补跑、行为、代码与复算材料；仓库中的 `results/protocol-repair-20260918/` 保持原字节。本包独立采用清单明确 `total_main_runtime_adoption=false`，不会把修复版的 97 池完成闸门冒充本次采用依据。
