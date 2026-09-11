# 五模型 ExpGym / PoolAct：主问题与核心数据

**三个问题：反馈预算收紧是否降性能？PoolAct是否改善结果？最优模型是否依赖任务家族和部署反馈预算？**

本版只展示场景/家族级数据，不列具体 task、question 或 job ID。[完整详细报告](../README.zh.md)保留所有设置、逐任务、重复、成本及诊断；[原始 dump 与聚合完整索引](../ARCHIVE_INDEX.md)保留全部存档入口。本次没有重跑模型或修改历史评分。

## 先补齐数值口径：缺最终结果也计入比较

此前 GPT / DeepSeek 的 HPO/NAS `unknown`，确实来自**没有交付可评分的最终配置**，不是整轮实验没执行，也不是完全没有生成文本或推理。已交付配置的低分仍是真实得分，不能全部归因于未输出。

| 模型 | 单 agent 调优有效配置 | NAS池内有效成员 | 四成员全有效的池 |
| --- | --- | --- | --- |
| Kimi / GLM / Qwen（各模型） | 81/81 (100%) | 216/216 (100%) | 54/54 (100%) |
| GPT | 81/81 (100%) | 215/216 (99.5%) | 53/54 (98.1%) |
| DeepSeek | 70/81 (86.4%) | 135/216 (62.5%) | 10/54 (18.5%) |

GPT唯一缺失由本地上下文上限停止引起。DeepSeek的92个缺配置成员均记录为正常循环返回后的未交付，不是HTTP、工具或评分器异常；现有终态导出不足以把这92例进一步归为同一种停止原因。

Search/Audit的低分另作区分：GPT空回答为0/1584，并无缺答；DeepSeek为506/1584（31.9%）。这些空答已由原评估器按空预测计入现有分数，不是unknown，不再次补零或剔除；也不能据此把DeepSeek全部低分归因于缺答。[计数来源](NON_HPO_OUTPUTS.json)


为比较实际交付效果，本版新增 **Gap0（未交付计零效用）**：按原冻结legacy规则可评分的结果沿用原Gap；正常结束但无最终配置的agent效用取0；MI仍为四成员平均，BoN取已交付结果的最佳值（全空才为0）。不把一人缺失当作全池零分，也不把未开始或基础设施失败随意计零。这是用户本次要求下新增的**回顾性部署指标**，不是给不存在的配置跑出一个真实0分；原严格Gap的unknown及原排名均保留在详细版。

**下表Search F1 / Audit EA统一按0–100分展示；HPO/NAS用Gap0点，越高越好，100为参考值而非上限。** 先在每item内平均重复，再对item等权；不把不同指标相加为总分。

简要设置：ExpGym为Search73题、Audit13文档×3固定顺序、HPO/NAS9任务×3重复；四人池为Search39道whois、Audit13文档、NAS3任务×3重复。两系统的Search/HPO任务全集不同，不直接把两章的全体均值作N=1与N=4的效果比较。Free无有限反馈预算；Moderate为10×基准成本，Tight为3×，每名agent各有同档预算。Free还隐藏成本信息。GPT使用medium，其余模型使用各自最高thinking配置；API/自部署等差异见详细版，排名描述这些实际部署设置。

## 1. 预算收紧：哪些性能下降？

| 场景 / 主指标 | 模型 | Free | Moderate | Tight | Free−Tight ↓ |
| --- | --- | --- | --- | --- | --- |
| Search / F1 | Kimi | 63.59 | 49.62 | 15.76 | +47.83 |
| Search / F1 | GLM | 65.11 | 53.28 | 19.23 | +45.88 |
| Search / F1 | Qwen | 58.15 | 50.98 | 18.47 | +39.68 |
| Search / F1 | DeepSeek | 43.81 | 42.11 | 16.92 | +26.89 |
| Search / F1 | GPT (medium) | 64.01 | 53.06 | 15.55 | +48.46 |
| Audit / EA | Kimi | 89.44 | 68.78 | 51.58 | +37.86 |
| Audit / EA | GLM | 68.48 | 67.87 | 50.23 | +18.25 |
| Audit / EA | Qwen | 91.86 | 74.96 | 58.37 | +33.48 |
| Audit / EA | DeepSeek | 63.95 | 58.67 | 47.51 | +16.44 |
| Audit / EA | GPT (medium) | 70.44 | 65.91 | 54.15 | +16.29 |
| HPO/NAS / Gap0 | Kimi | 98.51 | 94.23 | 89.68 | +8.83 |
| HPO/NAS / Gap0 | GLM | 97.91 | 96.15 | 86.07 | +11.84 |
| HPO/NAS / Gap0 | Qwen | 97.47 | 95.13 | 85.71 | +11.76 |
| HPO/NAS / Gap0 | DeepSeek | 61.09 | 74.02 | 75.81 | -14.72 |
| HPO/NAS / Gap0 | GPT (medium) | 97.97 | 96.61 | 91.66 | +6.31 |


**共同方向明确，但不是所有端点都同向：** 五模型Search F1与Audit EA均从Free到Tight下降；Kimi、GLM、Qwen、GPT的HPO/NAS Gap0也下降。DeepSeek调优Gap0则从61.09升至75.81，同时有效配置率由20/27升至25/27；计入未交付损失后，它不支持“HPO预算收紧必然退化”。Audit标签准确率等次指标也不能由EA趋势代替，完整结果留在详细版。

## 2. 缓存与PoolAct：收益有多大？

以下在同一预算、相同四人池N=4内比较。Search/Audit用投票结果MV；NAS用成员平均Gap0-MI。正差表示PoolAct更好，负差完整保留。

### Moderate

| 场景 / 主指标 | 模型 | naive | cached | PoolAct | PoolAct−naive | PoolAct−cached |
| --- | --- | --- | --- | --- | --- | --- |
| Search / F1-MV | Kimi | 64.59 | 64.20 | 66.74 | +2.15 | +2.54 |
| Search / F1-MV | GLM | 62.03 | 65.67 | 65.74 | +3.71 | +0.07 |
| Search / F1-MV | Qwen | 61.21 | 61.17 | 63.48 | +2.27 | +2.31 |
| Search / F1-MV | DeepSeek | 13.25 | 17.09 | 11.97 | -1.28 | -5.13 |
| Search / F1-MV | GPT (medium) | 62.31 | 63.78 | 60.60 | -1.71 | -3.17 |
| Audit / EA-MV | Kimi | 73.76 | 76.47 | 93.67 | +19.91 | +17.19 |
| Audit / EA-MV | GLM | 81.00 | 84.62 | 97.74 | +16.74 | +13.12 |
| Audit / EA-MV | Qwen | 68.78 | 74.66 | 93.67 | +24.89 | +19.00 |
| Audit / EA-MV | DeepSeek | 59.28 | 58.82 | 33.48 | -25.79 | -25.34 |
| Audit / EA-MV | GPT (medium) | 64.71 | 65.16 | 67.42 | +2.71 | +2.26 |
| NAS / Gap0-MI | Kimi | 98.04 | 97.96 | 98.56 | +0.52 | +0.60 |
| NAS / Gap0-MI | GLM | 97.87 | 98.06 | 98.97 | +1.09 | +0.90 |
| NAS / Gap0-MI | Qwen | 96.92 | 97.72 | 98.87 | +1.95 | +1.15 |
| NAS / Gap0-MI | DeepSeek | 23.43 | 39.31 | 23.53 | +0.11 | -15.78 |
| NAS / Gap0-MI | GPT (medium) | 98.21 | 98.28 | 95.58 | -2.63 | -2.70 |


### Tight

| 场景 / 主指标 | 模型 | naive | cached | PoolAct | PoolAct−naive | PoolAct−cached |
| --- | --- | --- | --- | --- | --- | --- |
| Search / F1-MV | Kimi | 21.29 | 18.72 | 30.43 | +9.15 | +11.71 |
| Search / F1-MV | GLM | 20.86 | 20.86 | 30.01 | +9.15 | +9.15 |
| Search / F1-MV | Qwen | 18.30 | 23.31 | 20.69 | +2.39 | -2.63 |
| Search / F1-MV | DeepSeek | 2.56 | 4.27 | 7.44 | +4.88 | +3.17 |
| Search / F1-MV | GPT (medium) | 19.15 | 20.28 | 21.89 | +2.74 | +1.61 |
| Audit / EA-MV | Kimi | 55.20 | 54.75 | 62.90 | +7.69 | +8.14 |
| Audit / EA-MV | GLM | 58.82 | 60.18 | 69.23 | +10.41 | +9.05 |
| Audit / EA-MV | Qwen | 56.11 | 60.18 | 63.80 | +7.69 | +3.62 |
| Audit / EA-MV | DeepSeek | 49.77 | 37.10 | 6.79 | -42.99 | -30.32 |
| Audit / EA-MV | GPT (medium) | 51.58 | 58.82 | 62.44 | +10.86 | +3.62 |
| NAS / Gap0-MI | Kimi | 94.26 | 94.11 | 96.05 | +1.79 | +1.94 |
| NAS / Gap0-MI | GLM | 83.96 | 86.18 | 96.18 | +12.22 | +9.99 |
| NAS / Gap0-MI | Qwen | 90.62 | 90.76 | 96.27 | +5.65 | +5.51 |
| NAS / Gap0-MI | DeepSeek | 28.68 | 23.06 | 47.91 | +19.24 | +24.85 |
| NAS / Gap0-MI | GPT (medium) | 96.64 | 96.05 | 97.27 | +0.63 | +1.22 |


**PoolAct的收益取决于场景和预算，不能概括为处处最优。** Tight Search在五模型上都优于naive；计入缺输出的损失后，Tight NAS的Gap0-MI也在五模型上高于naive。Audit则为四模型改善、DeepSeek两档下降（Moderate−25.79、Tight−42.99分，相对naive）。缓存本身的作用可由cached列直接区分，PoolAct相对cached不保证更好。

缺输出不是略去后就不影响结论：GPT Moderate NAS现在可给出95.58的Gap0-MI，低于naive98.21（−2.63点）；DeepSeek Moderate NAS为23.53，与naive23.43接近，且低于cached39.31；Tight NAS则从naive28.68升至PoolAct47.91。它们是计入全部计划成员的交付比较，不能用只看有结果的子集均值替代。

## 3. Ranking reshuffle：部署时该选哪个模型？

六个家族分别排序，不混合不同指标。本表对所有家族都使用固定的五模型候选集；HPO家族改用明确标注的Gap0，因此DeepSeek也有可比较数值。冠军括号内为该家族得分。

| 任务家族 | Free 最优 | Moderate 最优 | Tight 最优 | Free→Tight换位 |
| --- | --- | --- | --- | --- |
| Search whois | GLM (68.27) | GLM (64.28) | GLM (23.06) | 否 |
| Search whatis | GPT (medium) (65.42) | GPT (medium) (45.39) | DeepSeek (15.93) | 是 |
| Audit | Qwen (91.86) | Qwen (74.96) | Qwen (58.37) | 否 |
| ParamNet / Gap0 | GPT (medium) (97.31) | GPT (medium) (95.27) | GPT (medium) (85.69) | 否 |
| NAS101 / Gap0 | GLM (99.06) | GPT (medium) (98.32) | GPT (medium) (97.03) | 是 |
| NAS201 / Gap0 | Kimi (99.77) | Kimi (97.08) | Kimi (94.66) | 否 |


**最优模型同时依赖任务和部署反馈预算。** whois偏向GLM，Audit偏向Qwen，ParamNet偏向GPT，NAS201偏向Kimi；不存在跨家族的单一赢家。Free→Tight时，whatis冠军由GPT变为DeepSeek，NAS101由GLM变为GPT：六家族中两家族换位，其他四家族冠军不变。Gap0补入后这两处换位仍成立；这不是“所有任务都换位”，也不代表小分差具有统计显著性。

部署选型应看目标任务、目标反馈预算，以及是否能交付有效结果，而不只看Free下的能力排序。资源、生成配置与有限样本仍会影响这些观察，不能据此宣称纯模型能力或同实际成本下的普遍优越。

## 查验与详细版本

- [完整详细报告](../README.zh.md)：原严格评分、完整setting、全部任务/重复、次指标和成本，不改写原结果。
- [Gap0详细补充](GAP0_DETAILS.zh.md)：新增指标的设置级数值、有效率、条件均值、BoN与原严格端点并列。
- [核心ExpGym数据](main_expgym.csv) · [核心PoolAct数据](main_poolact.csv) · [五模型家族排名全分数](main_family_rankings.csv)。
- [原始dump与聚合完整索引](../ARCHIVE_INDEX.md) · [新增数值来源](GAP0_INPUTS.json) · [本版复核与发布验收](VALIDATION.json)。GPT raw仍为本地存档，确切路径已列入索引。

原生成环境CPython3.11.15。`python3 -B gap0.py --check`与`python3 -B build_summary.py --check`核对本版冻结输入派生；不调用模型、scorer或恢复raw。公开派生输入的来源身份、投影字段和适用边界分别在清单和详细补充中保留。
