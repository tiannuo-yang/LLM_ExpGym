# 主实验补充版独立复核

结论：`analysis_tools/main-final-v2/` 的来源选择、保存分数抽取、聚合、比较、排名和动态结论核验通过。没有发现会改变当前数值结果的合并错误。

复核没有调用 `merge_main.py` 的聚合或排序实现来计算期望值。独立脚本 [check_independent.py](check_independent.py) 读取绑定原始 CSV、16 份新 canonical 和最终导出，得到以下结果；完整收据见 [CHECKS.json](CHECKS.json)。

- 9 份冻结输入的字节数和 SHA256 一致；新旧槽集合仍为 4,698。
- 原 4,682 槽的所有已有标量 CSV 字段逐项不变；新增只占原先没有 canonical 的 16 槽。
- 新 16 项全部严格评分完整；从 canonical 独立重算 74 个保存标量/Gap 字段一致。保存分数重算使用冻结 oracle，没有重新调用任务评分器。
- 7,767 聚合行、69,903 数值/分母字段独立核验通过；7,482 行所有原字段不变，285 行受缺项补齐影响。
- 126 个家族×模型×预算排名一致；没有把部分完整队列标记为六模型冠军。
- 38 个仅含新 OpenRouter 槽的聚合行标记为纯新 cohort，其余受影响混合行同时标记两来源。
- 1,298 行合并比较的 3,894 个绝对表引用、3,894 个差值位置均核验通过。见 [COMPARISON_CHECKS.json](COMPARISON_CHECKS.json)，其中同时绑定复核时最终目录各文件的 SHA256。
- 9 个内存反例检查通过：拒绝错误 provider、seed、预算 regime、损坏的 MI/BoN、重复池成员；未完成执行保留空值，正常 HPO 弃答仅 Gap0 为零，异常缺失不补零。见 [GUARDS.json](GUARDS.json)。反例没有修改原 canonical。
- 动态结论独立核验：Search/Audit 各 6/6 模型 Free→Tight 下降，HPO 为 5/6；36/36 策略组完整，PoolAct 在 31 组严格高于另两策略，Tight 为 17/18；7 个维度有 5 个 Free/Tight 第一名集合改变。见 [FINDINGS_CHECKS.json](FINDINGS_CHECKS.json)，包含 36 组逐组值、最新最终目录各文件 SHA256，以及与第一版 11 个非正文输出字节一致的证据。

复核中发现并由作者修正了两处问题：主整合文档原先引用 collector 不生成的 `main-results-for-report.json`，现已改为 `main-completed-result-paths.json`；纯新聚合行原先也被统一标成 mixed cohort，现已按所选槽的实际来源标记。这两处不影响分数，最终目录已包含修正。

`partial_actual/` 是发现 cohort 问题前的复核用临时输出，虽然该轮读取时 16 项已全部完成，但保留着旧 cohort 标注；它不是交付报告，不应发布或引用。`../main-final/` 是未加入动态结论的先行草稿；当前通过复核的报告为 `../main-final-v2/`。

本复核范围为报告整合，不替代独立运行证据审核：没有重跑任务评分器、检查全量请求的语义内容、重新验证 completion receipt 的所有 artifact 清单或识别 provider 模型权重。新旧 Gemini 提供方混合的限制已在最终报告正文说明；已完成 4,698 项不等于严格评分 4,698 项，最终严格评分数为 4,687。
