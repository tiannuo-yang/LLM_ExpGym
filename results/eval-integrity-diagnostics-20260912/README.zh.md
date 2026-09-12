# ExpGym / PoolAct：五模型结论的诊断复盘

状态：**本轮 GPU 修复验证完成，主比较 12/12 池完整评分；另保留 1 个被替代的已完成池和 2 个未启动槽。** 本轮不是完整矩阵重跑；旧样本与分数保持不变，未启动项不记为 0。

[详细报告](DETAILS.zh.md)保留设置、协议和影响范围。[原五模型主报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911/main_findings_v2/README.zh.md)与[原详细报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911/README.zh.md)保持不变。

通用源码修复、报告规范和 runner 技能已推送至 [fix/eval-integrity-20260912](https://github.com/tiannuo-yang/LLM_ExpGym/commit/5bf5e5af817c2c6add48c7bae4eec4fe6e8110e9)。实际任务固定运行 `b3382b1`，之后仅更新文档和技能。

本轮区分三个层次：框架能否正确执行、模型输出是否稳定、PoolAct 是否提高分数。**前两层通过不保证第三层；实际增益必须由同设置对照给出。**

## 1. 预算收紧是否降低表现？

旧正式矩阵中，五模型 Search F1 与 Audit EA 均从 Free 到 Tight 下降。主报告记录的下降幅度分别为 **26.89–48.46 分**和 **16.29–37.86 分**（0–100 显示）。调优并非统一方向：四模型 Gap0 下降，DeepSeek 的回顾性 Gap0 从 **61.09 升至 75.81**，不能写成所有端点必然退化。

已确认的图路径 ID 碰撞属于多 agent PoolAct 共享图；**单体 ExpGym 不使用该图，因此上述预算趋势不直接受此缺陷影响。** 这不证明其他协议或 serving 影响为零，尤其 DeepSeek 的数值仍描述其冻结部署下的实际交付表现，不能直接当成纯模型能力。

本轮 smoke 仅使用 Tight、两个固定诊断任务、N=2、一次池运行及短决策上限，**没有新增 Free/Moderate/Tight 对照，不能重新验证完整预算退化曲线**。

## 2. 缓存与 PoolAct 能改善多少？

通用图身份修复涉及旧 **90 个 NAS PoolAct 池中的 80 个碰撞池**；另 **130 个 Audit 池均无此碰撞**。它影响协作输入，不直接合并成绩，因此不能只重算旧输出来得到修后的 NAS 收益。native Audit 的固定参数提示冲突也已通用修复，没有按模型改答案或评分。[修复与影响范围](DETAILS.zh.md#3-原五模型中的确认问题与影响)

DeepSeek 基线并发回放曾再现乱码/循环；关闭多流重叠后的前后 **16 次保序回放均连贯**。候选实际六池 **47 次回复中 46 条连贯、1 条语义循环、0 条明显碎词乱码**，12 个成员均完整评分。这支持当前候选部署的有限验证，不证明根因已唯一定位或所有请求永不异常；完整分类见[详细报告](DETAILS.zh.md#4-首请求回放保序输入与真实协议)。

新 GLM Audit PoolAct 的 8 次回复均交付有效工具调用或最终答案，没有乱码、空答或输出触顶，但其中 **7 条存在持续语义重复**。因此工程执行通过，不等于推理效率或所有生成行为都已理想；这一现象也不能直接定性为框架或 serving bug。

下表使用同 cohort 的三策略实际结果，**均按0–100显示，差值为百分点**。GLM NAS 使用原部署；GLM Audit 因原作业时限不足，另起同参数三策略完整cohort，不跨服务拼接。DeepSeek 六池均使用关闭多流重叠的同一候选部署。

| 模型 / 场景 | 本轮主指标 | naive | cached | PoolAct | PoolAct−naive | PoolAct−cached |
| --- | --- | --- | --- | --- | --- | --- |
| GLM / NAS | raw accuracy MI | 84.59 | 84.59 | 84.59 | 0.00 | 0.00 |
| GLM / NAS | raw accuracy BoN | 84.59 | 84.59 | 84.59 | 0.00 | 0.00 |
| GLM / Audit | EA-MI | 38.24 | 35.29 | 47.06 | +8.82 | +11.76 |
| GLM / Audit | EA-MV | 41.18 | 35.29 | 52.94 | +11.76 | +17.65 |
| DeepSeek / NAS | raw accuracy MI | 84.59 | 84.59 | 86.21 | +1.62 | +1.62 |
| DeepSeek / NAS | raw accuracy BoN | 84.59 | 84.59 | 87.82 | +3.24 | +3.24 |
| DeepSeek / Audit | EA-MI | 38.24 | 38.24 | 32.35 | −5.88 | −5.88 |
| DeepSeek / Audit | EA-MV | 35.29 | 41.18 | 35.29 | 0.00 | −5.88 |

数值来源为[三策略比较 CSV](comparisons.csv)。缺失保持 unknown，正、零、负差和全部已发生费用均保留。新任务/样本量与旧全矩阵不同，不能把新旧聚合差直接当成修复效果量。

实际数值支持“修后 DeepSeek 在该 NAS smoke 上获益，GLM Audit 的主要 EA 指标优于 naive 和 cached”，**不支持“所有模型、每个任务都稳定提升”**：GLM NAS 持平，DeepSeek Audit仍有小样本负差；GLM Audit 的次要 LA 指标相对 naive 下降、相对 cached 持平，详表保留。cached 有一次输出长度耗尽，之后在原预算内恢复，未删除失败回复。此处每个策略只有一个两成员池，不能把负差唯一归因为bug，也不能把正差外推成总体优势。

## 3. 最优模型会随家族和部署预算变化吗？

旧正式报告按固定五模型候选集、各家族自身指标排序，不把不同指标加成总榜。Free→Tight 有 **2/6 家族冠军换位**，且不存在跨家族的单一赢家：

| 任务家族 | Free 冠军 | Tight 冠军 |
| --- | --- | --- |
| Search whatis | GPT | DeepSeek |
| Search whois | GLM | GLM |
| Audit | Qwen | Qwen |
| ParamNet | GPT | GPT |
| NAS101 | GLM | GPT |
| NAS201 | Kimi | Kimi |

这些排名来自 ExpGym 单体，**不直接使用存在碰撞的 PoolAct 图**。它们支持“选型要看任务、反馈预算与实际部署条件”的描述，但不证明纯模型能力、同实际成本下的优势或小分差显著。

本轮只有 GLM 与 DeepSeek 的有限 Tight smoke，既没有五模型全矩阵，也没有完整预算档位；**不能用它宣布家族/预算排名已复现或改写旧冠军**。新数值只回答对应诊断设置下的策略表现与输出完整性。

## 数据与存档入口

实际执行共 13 池、26 个完整评分成员、101 次任务请求；另有 40 次诊断回放，不计入任务成绩。原始输入、回复、失败、验证和费用均按各自范围留存。

- [原始 dump 完整机器索引](INDEX.json) · [人读存档索引](ARCHIVE_INDEX.md)。
- [逐池 CSV](per_pool.csv) · [逐成员 CSV](per_agent.csv) · [聚合比较 CSV](comparisons.csv)。
- [全部物理请求](physical_attempts.csv) · [完整/已知子集费用](costs.csv)。Task smoke 与 API replay 分列，未知费用不补零。
- [原件到公开分片的路径/SHA映射](RAW_INDEX.json) · [修复、回放与完整输出检查证据](ARCHIVE_INDEX.md#other-evidence)。
- [旧五模型原始 dump 与完整存档索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911/ARCHIVE_INDEX.md)。旧正式样本、失败与分数全部保留。

最终独立数值/逻辑复核已通过，未发现阻断发布的问题；包括76个报告数值单元与122项CSV一致性检查。[复核记录](ARCHIVE_INDEX.md#other-evidence)位于归档 `originals/reporting/FINAL_REVIEW.zh.md`，明确列出检查版本、范围和允许的发布状态更新。此验收不等于所有模型/场景均改善。
