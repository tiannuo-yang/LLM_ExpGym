# GLM 完整研究：同版 Low/Max、Audit scaling 与 PoolAct 消融

> 图件修订版：四张图已重绘，并补充已有数据的 N=1 点；原实验分数、210设置总表及存档保持不变。新增点的口径、英文图注、逐点数据和复现入口见[论文图件说明](FIGURES.zh.md)。原55项复核对应初版成稿，本次图形另作有限复核；原件与公开修订身份见[来源说明](PROVENANCE.md)。

1,334个新正式作业、3,146条agent轨迹均执行与评分完整；技术验证21作业／63agents另列。新增同版Max417已完成，成为Low417的主要对照；用户指定9/18重评分的历史Max417只作次级参考。原始分数、缺答零分、失败尝试和负结果均保留。本研究只有一个模型，不能回答跨模型排名。

[详细报告](DETAILS.zh.md) · [210设置总表](metrics/unified_settings.csv) · [417项同版配对](metrics/same_version_pairs.csv) · [12对具体轨迹](TRAJECTORIES.zh.md) · [原917 dump索引](archive/MEMBERS.csv) · [新增Max dump索引](archive/MEMBERS.csv) · [完整分包与恢复入口](ARCHIVES.zh.md)

## 1. Low 与同版本 Max：更多 thinking 是否值得

同题、同预算、同source88、同终答提取/评分契约。Low仍开启thinking；唯一计划模型参数改动是top-level与chat template两层effort的low→max。两组依次运行，保留部署时段和争用差异，不把配对描述成随机化纯因果实验。

| 指标 | 预算 | Low | 同版本 Max | Low − Max |
| --- | --- | --- | --- | --- |
| Search F1 % | Free | 49.414 | 60.631 | -11.217 |
| Search F1 % | Moderate | 41.318 | 55.658 | -14.341 |
| Search F1 % | Tight | 13.930 | 18.106 | -4.176 |
| Audit EA % | Free | 90.799 | 94.721 | -3.922 |
| Audit EA % | Moderate | 66.063 | 81.750 | -15.686 |
| Audit EA % | Tight | 58.824 | 57.919 | +0.905 |
| HPO Gap | Free | 95.621 | 98.700 | -3.079 |
| HPO Gap | Moderate | 93.970 | 96.295 | -2.325 |
| HPO Gap | Tight | 86.119 | 83.601 | +2.517 |

Search是Whois39题与Whatis34题合并、逐题等权。Audit每预算13文档×3固定order；HPO每预算9任务×R3、先任务内均值再任务等权。F1/EA差值用百分点，Gap与差值用points，均越高越好；不跨量纲合成总分。

Max在Search三个预算、Audit与HPO的Free/Moderate上更高；Tight下Low的Audit EA高0.905个百分点、HPO Gap高2.517点。Audit标签LA另计：Free/Moderate/Tight的Low/Max分别为95.324/94.570、84.465/90.347、86.124/77.979%，不能用EA代替LA。

Low全尝试用量15,070,708 tokens，Max105,299,537 tokens，Max约为Low的6.99倍。Max最终缺答7条、Low0条，缺答零分没有剔除。固定轨迹对照显示更多推理并不总带来更多有效评估：Audit Free样本得到相同分数但Max少用5次核验；ParamNet Tight样本Low用更多便宜的可见试验得到更好的配置。它们是预选案例，不能解释全部417对的差异。

![同版 Low/Max](figures/thinking_same_version.svg)

## 2. Audit scaling：增加agent及协调的收益

GLM Max，13文档；N≥2为EA-MV %，N1个体均分单独注明。每agent预算固定，N增加时整池潜在预算也增加；这不是等整池预算对照。naive只实跑N8，N2/4/6/8分别枚举28/70/28/1子集，先各子集投票再平均，原agent ID顺序处理legacy平局；组合不能当独立重复。

| 预算 | 方法 | N1（个体均分） | N2 | N4 | N6 | N8 |
| --- | --- | --- | --- | --- | --- | --- |
| Moderate | naive | 77.602 | 82.579 | 84.286 | 84.454 | 84.163 |
| Moderate | cached | 未运行 | 86.878 | 90.045 | 92.308 | 91.855 |
| Moderate | poolact | 未运行 | 92.760 | 97.738 | 100.000 | 100.000 |
| Tight | naive | 59.106 | 63.203 | 63.129 | 62.815 | 63.348 |
| Tight | cached | 未运行 | 61.991 | 66.968 | 66.063 | 66.063 |
| Tight | poolact | 未运行 | 64.253 | 80.995 | 87.330 | 92.308 |

N1复用naive N8池中的个体评分均值 EA_MI：每文档8个agent先平均，再13文档等权；N≥2仍为原EA-MV，未重新投票或增加实验。独立ExpGym Max N1为Moderate **81.750%**、Tight **57.919%**，在图中用空心菱形标出；它采用3种order且context/cache设置不同，不作为三条曲线的共同起点。Cached/PoolAct的N1保持未运行。详见[定义与图注](FIGURES.zh.md#n1-的定义与可比性)。

PoolAct在本组已实测N2/4/6/8的EA-MV均高于两个基线，Tight随N从64.253%升至92.308%。次指标保留反例：Tight N2的PoolAct LA-MV为82.805%，低于naive87.492%和cached88.235%。Moderate N6/N8的PoolAct EA-MV为100%，LA-MV为98.190%。完整LA、MI和分母见详表。

![Audit scaling](figures/audit_scaling_EA_MV.svg)

图中naive N1为MI、N≥2为MV，ExpGym N1为独立参考；每agent预算固定，整池预算随N增长。纵轴范围50–104%，完整[英文图注与导出说明](FIGURES.zh.md)。

## 3. Tight N4 消融：哪些组合带来增益或退步

五方法都是本轮Max。Whois39题、Audit13文档、NAS101三任务×R3；Audit的39个baseline位置复用本轮scaling，naive N4使用N8的70子集均值；Whois/NAS101的naive直接实跑N4。

| 指标 | naive | cached | peer_context | graph_no_lock | poolact |
| --- | --- | --- | --- | --- | --- |
| Whois F1-MV % | 19.578 | 18.762 | 23.741 | 20.738 | 31.165 |
| Audit EA-MV % | 63.129 | 66.968 | 71.493 | 76.471 | 80.995 |
| NAS101 Gap-MI | 84.811 | 85.263 | 87.550 | 87.683 | 96.044 |

本次三个主指标都是完整PoolAct最高；这不表示每一步都有正贡献。Whois的cache步骤−0.816个百分点、peer→graph步骤−3.004个百分点；最后加入外层reasoning/claim临界区时三个任务均上升。peer→graph是graph、path、coverage、pending整个机制替换，不是只改变显示格式；graph_no_lock仍保留内部数据结构锁。

| 场景 | 相邻比较 | Δ target − baseline |
| --- | --- | --- |
| restricted_search | naive → cached | -0.816 |
| restricted_search | cached → peer_context | +4.979 |
| restricted_search | peer_context → graph_no_lock | -3.004 |
| restricted_search | graph_no_lock → poolact | +10.427 |
| evidence_audit | naive → cached | +3.840 |
| evidence_audit | cached → peer_context | +4.525 |
| evidence_audit | peer_context → graph_no_lock | +4.977 |
| evidence_audit | graph_no_lock → poolact | +4.525 |
| tuning | naive → cached | +0.452 |
| tuning | cached → peer_context | +2.287 |
| tuning | peer_context → graph_no_lock | +0.133 |
| tuning | graph_no_lock → poolact | +8.361 |

![Tight N4消融](figures/tight_N4_ablation.svg)

## 数据版本、成本与可复核范围

正式source为`88e27ad5963625ccbd3f9269dce0f95412b8d786`，原917与新增Max分别独立导出一次，未重评分。历史参考采用发布快照`2a78fc8…`，历史模型实际执行为`8dfea729…`，重新提取/评分为`0e6c51b…`；这些身份不能互换，历史比较跨执行与评分版本。上游candidate字段保留，用户已指定作为参照。[历史次级表及解释](DETAILS.zh.md#历史次级参照)。

全部正式26,226次attempt共684,463,294 tokens；技术验证280次／7,893,738 tokens独立列出。reasoning已包含在output，缓存token全部unknown。64张H200已于2026-09-18 09:57:17 UTC释放，四个allocation合计1932.996 GPU-hours，包含启动、pilot、空闲、正式实验和收尾，不能称为纯计算或只归到正式实验。

有限fidelity样本共32槽／40agents，完整external轨迹与长reasoning阅读范围分别记录。保守parser的非空intro、Markdown suffix、普通词脱敏碰撞、history trim及cache producer未知等边界仍保留；通过检查不等于所有输出正确或系统完全无bug。最终报告的独立复核和发布扫描由独立receipt记录，原件与旧报告不被覆盖。
