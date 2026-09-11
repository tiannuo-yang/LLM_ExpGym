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

{{NON_HPO}}

为比较实际交付效果，本版新增 **Gap0（未交付计零效用）**：按原冻结legacy规则可评分的结果沿用原Gap；正常结束但无最终配置的agent效用取0；MI仍为四成员平均，BoN取已交付结果的最佳值（全空才为0）。不把一人缺失当作全池零分，也不把未开始或基础设施失败随意计零。这是用户本次要求下新增的**回顾性部署指标**，不是给不存在的配置跑出一个真实0分；原严格Gap的unknown及原排名均保留在详细版。

**下表Search F1 / Audit EA统一按0–100分展示；HPO/NAS用Gap0点，越高越好，100为参考值而非上限。** 先在每item内平均重复，再对item等权；不把不同指标相加为总分。

简要设置：ExpGym为Search73题、Audit13文档×3固定顺序、HPO/NAS9任务×3重复；四人池为Search39道whois、Audit13文档、NAS3任务×3重复。两系统的Search/HPO任务全集不同，不直接把两章的全体均值作N=1与N=4的效果比较。Free无有限反馈预算；Moderate为10×基准成本，Tight为3×，每名agent各有同档预算。Free还隐藏成本信息。GPT使用medium，其余模型使用各自最高thinking配置；API/自部署等差异见详细版，排名描述这些实际部署设置。

## 1. 预算收紧：哪些性能下降？

{{EXPGYM}}

**共同方向明确，但不是所有端点都同向：** 五模型Search F1与Audit EA均从Free到Tight下降；Kimi、GLM、Qwen、GPT的HPO/NAS Gap0也下降。DeepSeek调优Gap0则从61.09升至75.81，同时有效配置率由20/27升至25/27；计入未交付损失后，它不支持“HPO预算收紧必然退化”。Audit标签准确率等次指标也不能由EA趋势代替，完整结果留在详细版。

## 2. 缓存与PoolAct：收益有多大？

以下在同一预算、相同四人池N=4内比较。Search/Audit用投票结果MV；NAS用成员平均Gap0-MI。正差表示PoolAct更好，负差完整保留。

### Moderate

{{POOL_MODERATE}}

### Tight

{{POOL_TIGHT}}

**PoolAct的收益取决于场景和预算，不能概括为处处最优。** Tight Search在五模型上都优于naive；计入缺输出的损失后，Tight NAS的Gap0-MI也在五模型上高于naive。Audit则为四模型改善、DeepSeek两档下降（Moderate−25.79、Tight−42.99分，相对naive）。缓存本身的作用可由cached列直接区分，PoolAct相对cached不保证更好。

缺输出不是略去后就不影响结论：GPT Moderate NAS现在可给出95.58的Gap0-MI，低于naive98.21（−2.63点）；DeepSeek Moderate NAS为23.53，与naive23.43接近，且低于cached39.31；Tight NAS则从naive28.68升至PoolAct47.91。它们是计入全部计划成员的交付比较，不能用只看有结果的子集均值替代。

## 3. Ranking reshuffle：部署时该选哪个模型？

六个家族分别排序，不混合不同指标。本表对所有家族都使用固定的五模型候选集；HPO家族改用明确标注的Gap0，因此DeepSeek也有可比较数值。冠军括号内为该家族得分。

{{FAMILY_WINNERS}}

**最优模型同时依赖任务和部署反馈预算。** whois偏向GLM，Audit偏向Qwen，ParamNet偏向GPT，NAS201偏向Kimi；不存在跨家族的单一赢家。Free→Tight时，whatis冠军由GPT变为DeepSeek，NAS101由GLM变为GPT：六家族中两家族换位，其他四家族冠军不变。Gap0补入后这两处换位仍成立；这不是“所有任务都换位”，也不代表小分差具有统计显著性。

部署选型应看目标任务、目标反馈预算，以及是否能交付有效结果，而不只看Free下的能力排序。资源、生成配置与有限样本仍会影响这些观察，不能据此宣称纯模型能力或同实际成本下的普遍优越。

## 查验与详细版本

- [完整详细报告](../README.zh.md)：原严格评分、完整setting、全部任务/重复、次指标和成本，不改写原结果。
- [Gap0详细补充](GAP0_DETAILS.zh.md)：新增指标的设置级数值、有效率、条件均值、BoN与原严格端点并列。
- [核心ExpGym数据](main_expgym.csv) · [核心PoolAct数据](main_poolact.csv) · [五模型家族排名全分数](main_family_rankings.csv)。
- [原始dump与聚合完整索引](../ARCHIVE_INDEX.md) · [新增数值来源](GAP0_INPUTS.json) · [本版复核与发布验收](VALIDATION.json)。GPT raw仍为本地存档，确切路径已列入索引。

原生成环境CPython3.11.15。`python3 -B gap0.py --check`与`python3 -B build_summary.py --check`核对本版冻结输入派生；不调用模型、scorer或恢复raw。公开派生输入的来源身份、投影字段和适用边界分别在清单和详细补充中保留。
