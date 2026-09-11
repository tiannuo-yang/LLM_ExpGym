# 五模型 ExpGym / PoolAct 全设置报告：预算退化、协调改善与模型排名重排

本报告围绕三个主问题展开：**反馈预算收紧是否导致性能下降？共享缓存和 PoolAct 协调能改善多少？不同任务家族与预算强度下，最优模型是否仍然相同？**

模型为 Kimi-K3、GLM-5.3、Qwen3.8-2.4T-A95B-FP8、DeepSeek-V4-Flash-0731，以及通过原生 Responses API 运行的 gpt-5.6-sol（下文简称 GPT）。采用原 [Kimi / GLM 八章全设置报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md) 的设置、全表和存档结构，在 [四模型合报](https://github.com/tiannuo-yang/LLM_ExpGym/blob/a79cbc100804a1bc8d374e084a4b9999e3697a91/results/four-model-20260911/README.zh.md) 基础上加入冻结 GPT 数据和明确的排名比较。

研究类型仍为 Custom study，不是论文数值逐项精确复现。**本次只合并已有导出和生成描述性比较，不新增模型调用、不重评分、不改变历史结果。** 全文保留 ExpGym Free / Moderate / Tight，以及 N=4 的 naive / cached / poolact × Moderate / Tight；排名不是用一张跨任务总分表替代这些完整设置。

主要观察是：五模型 Search 与 Audit 证据指标均出现 Free→Tight 退化；PoolAct 在 Tight Search 的改善跨五模型成立，但其他场景有正向、负向和未知结果；最优模型随任务家族而异，部分家族及多数所列 HPO 任务在 Free→Tight 时换位。具体候选范围和完整分母紧邻相应表格说明。

**统一存档入口：** [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md) · [ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)。GPT 原始数据当前为本地冻结存档，不将本次报告发布误写成其全部 raw 已获公开发布验收。

## 1. 实验设置与覆盖

### 1.1 五模型共用的科学矩阵

| 系统 | 任务 | 实际项目数 | 预算档位 | 方法 / agent 数 | 重复设置 |
| --- | --- | ---: | --- | --- | --- |
| ExpGym | Search | 73 题：39 whois + 34 whatis | Free / Moderate / Tight | single，N=1 | 每题每设置 1 次 |
| ExpGym | Evidence Audit | 13 文档，17 hypotheses | Free / Moderate / Tight | single，N=1 | 每文档 3 个固定顺序，文档内平均一次 |
| ExpGym | HPO / NAS | 9 任务 | Free / Moderate / Tight | single，N=1 | 每任务每设置 3 个 seed blocks |
| 多 agent | Search | 39 道 whois | Moderate / Tight | naive / cached / poolact，均 N=4 | 每题每设置 1 个独立池 |
| 多 agent | Evidence Audit | 13 文档 | Moderate / Tight | naive / cached / poolact，均 N=4 | 默认 hypothesis 顺序，每文档每设置 1 个独立池 |
| 多 agent | NAS | NASBench101 A / B / C | Moderate / Tight | naive / cached / poolact，均 N=4 | 每任务每设置 3 个独立池 |

9 个单 agent tuning 任务为 ParamNet adult、higgs、letter，NASBench101 A、B、C，以及 NASBench201 cifar10-valid、cifar100、imagenet16-120。Search 使用 PhantomWiki seed2 / seed3 两个固定 world。Pool 不包含 whatis、ParamNet、NASBench201，也未计划 Free，因此两个系统的 `all` 不能直接当作相同任务全集。

每个完整矩阵对应 783 个顺序/重复/池级逻辑结果、1881 个 agent 结果，以及将 Audit 三顺序折叠后的 705 个分析单元。Kimi / GLM 将 Audit 三顺序放在同一进程，每模型实际为 705 次 invocation；Qwen / DeepSeek / GPT 将其拆为三个进程，每模型为 783 个执行槽位。此差异改变物理进程数，不增加独立任务或科学样本。

| 模型 | 计划逻辑结果 | 当前执行完成 | 评分完整性的关键范围 |
| --- | ---: | ---: | --- |
| Kimi-K3 | 783 | 全部 | 最终有效结果使用原完成项及批准恢复的固定 8 项；失败尝试另存 |
| GLM-5.3 | 783 | 全部 | 全部规定最终结果保留 |
| Qwen3.8 | 783 | 783 | 全部规定最终结果保留 |
| DeepSeek-V4-Flash-0731 | 783 | 783 | HPO 缺最终配置使部分完整评分端点 unknown，见第 2、3 章 |
| GPT | 783 | 783 | 782 个执行槽评分完整；1 个 Moderate NAS pool 缺一成员配置 |

Claude-fable-5 只作完整性登记，不进入本报告模型排名：原计划仅含 366 个 Pool 槽位，完成 108、评分完整 104、失败 8、未开始 250。不能将这个不完整 Pool 子集当作第六个完整模型，也不把未运行结果补零参与排名。

### 1.2 预算与重复

| 档位 | 模拟反馈预算 B | 向 agent 展示成本 / 剩余预算 |
| --- | --- | --- |
| Free (`cost_free`) | 无有限预算上限 | 否 |
| Moderate (`cost_moderate`) | 10 × c_base | 是 |
| Tight (`cost_tight`) | 3 × c_base | 是 |

Search / Audit 的 c_base=300 模拟秒，对应 Moderate 3000、Tight 900 模拟秒；HPO / NAS 使用冻结 oracle 的任务级 reference-best evaluation cost。Free 仍受步骤/评估次数及实际 provider 限制，不等于无限推理。这里改变的是反馈预算与成本可见性，不是直接限制成三档 GPU 时间；Free 与受限档位差异不能仅归因于预算数值而忽略成本信息。

N=4 时每个 agent 各有同一 B，不是整个池只有一个 B。HPO blocks 为 2200 / 2204 / 2208，池内四成员使用 block 至 block+3；Search / Audit 使用首个 block，ExpGym Audit 三顺序标签为 2200 / 2201 / 2202。标签只是本地重复与工具随机性标识，尤其 GPT 未将 seed 发给 provider；三个 blocks 不证明三次独立模型采样，四成员也不构成四次独立重复。

### 1.3 方法与实际 provider 配置

| 方法 | 含义 |
| --- | --- |
| naive | 四成员独立探索，不共享观察缓存和探索图，结束后按任务规则聚合。 |
| cached | 复用已完成且当前模拟时间可见的相同工具观察，避免重复支付相应模拟反馈成本。 |
| poolact | 在 cached 基础上增加共享探索图和协调；一次推理决策及 claim 受 reasoning lock 保护，环境工具执行在锁外。 |

各独立池的任务状态、缓存与图分开；池内共享按算法定义进行。PoolAct 串行保护池内决策，naive / cached 的推理并发不同；队列 workers 是独立 invocation 上限，不能简单乘 N 当作 PoolAct 同时推理数。算法观察缓存与 provider prompt/KV cache 是两种机制，后者的命中不会自动证明前者的作用。

| 配置 | Kimi-K3 | GLM-5.3 | Qwen3.8 | DeepSeek-V4-Flash-0731 | GPT |
| --- | --- | --- | --- | --- | --- |
| 服务 / 协议 | 自部署 SGLang，native chat tools | 同左 | 同左 | 同左 | 网关接入原生 Responses，`gpt-5.6-sol` |
| Temperature / top-p 请求 | 1.0 / 1.0 | 1.0 / 0.95 | 1.0 / 0.95 | 1.0 / 0.95 | 均未发送 |
| top-k 请求 | 未发送 | 未发送 | 20 | 未发送 | 未发送 |
| 单次输出上限 | max_tokens=32768 | 同左 | 同左 | 同左 | max_tokens / Responses max_output_tokens 均未发送；nominal 32768 不代表生效 |
| reasoning effort 请求 | `max` | `max` | `xhigh` | `max` | `medium` |
| template / reasoning 配置 | `thinking:true, thinking_effort:max` | `clear_thinking:false, reasoning_effort:max` | `enable_thinking:true,preserve_thinking:true` | `thinking:true` | `reasoning:{effort:medium}`，`parallel_tool_calls:false` |
| max_steps / max_evals | 30 / 30 | 同左 | 同左 | 同左 | 同左 |
| 服务端 context | 524288 | 262144 | 262144 | 1048576 | 不由本地 nominal 配置推断 |
| Pool 本地 cap | 131072 近似 tokens | 同左 | 同左 | 同左 | 131072，包含保留的 opaque 原生历史近似计数 |
| provider 缓存字段 | `prompt_cache_key` | 同左 | `cache_salt` | `cache_salt` | `prompt_cache_key` 未发送；上游隔离不获保证 |
| 部署 | 8×8 GPU；4 个 TP16 / EP16 副本 | 8×8 GPU；4 个 TP16 / EP1 副本 | 4×8 GPU；1 个 TP8×PP4 / EP1 副本 | 4×8 GPU；4 个 TP8 / PP1 / EP1 副本 | 外部 API，无本地 GPU 分配 |
| 正式队列 workers | 32 | 32 | 首 session16，后6 | 全程32 | 6 |

GPT 实际 adapter 记录未发送 `max_tokens, max_output_tokens, prompt_cache_key, seed, temperature, top_k, top_p`。这些 nominal 字段不能反写成有效 API 设置；其 medium 也不应改称最高 thinking。Responses 保留原生工具与 opaque 历史，本地 context 估计不等于 provider tokenizer 对完整请求的计数；超过限制后停止，而不截断原生历史。请求 dump 反映客户端与网关之间的正文，不等于网关内部改写后的全部上游报文。

四个自部署模型的最高 effort 标签也不等价于相同计算量。Qwen 模板不支持 `max`，使用最高档 `xhigh`；DeepSeek 使用精确官方0731 encoder backport，`max` 对应实际最高档，但32768输出仍低于其厂商384K长输出建议。Qwen / DeepSeek 均以独立 uv 运行时采用 CPython3.12.13、SGLang0.5.17、Torch2.11.0+cu129，具体精度与内核不同。forced-final wire 保留历史不意味着模板完全相同：Qwen会移除工具定义/说明而保留历史，DeepSeek encoder 仍保留定义及历史。

执行源码为 Kimi / GLM [`8dfea72`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/8dfea72931d952ad90f1c722a83957ab23afc6bf)、Qwen [`21b4de9`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/21b4de99b2a014874e3cec1595eaa40762b0c564)、DeepSeek [`5aabf7f`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8)；GPT 本地冻结源码提交 `ccaf6adb8f7e82fa0f33d97c06cf5f7a33592122`、source tree SHA `c6c60cbc358820ce26b04bfade1bfe9be6597c9c3c1e7546bbd14a67fba2fa3c`。GPT配置见 [queue config](inputs/gpt_queue_config.json)、[矩阵核对](inputs/gpt_matrix_validation.json)、[API请求范围](inputs/api_request_scope.json)；原件身份和完整路径见 [INPUTS.json](INPUTS.json) 与 [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md)。

### 1.4 指标与汇总单位

Search 使用集合 F1；Audit EA 是精确证据集合准确率，LA 是标签准确率。F1 / EA / LA 为 fraction，0.01 差值等于1个百分点。HPO Gap 是冻结 oracle 归一化效用、越高越好，逐 agent 截零后再算 MI；100 是参考水平，允许大于100，不作上截断。raw performance 与 Gap 均保留，不从汇总 raw 反推 Gap。

MI 为成员平均，MV 为原投票规则结果，BoN 为四成员最佳得分。先在同一 item 内平均重复，再对 item 等权；Audit 三顺序只折叠一次。GPT 原 API 导出中 Audit 的 39/39 表示13文档×3顺序，不是39个文档；合报同时保留原分母与统一分析单位的含义。质量表的 `unknown (k/n)` 表示 k 个已知、n 个计划分析单元，不是HTTP请求数或池成员数。

冻结 `legacy` final selection 与 `task-abstention-v1` 不在合报阶段更改。正常 Search / Audit null 回答保存原件并由原 evaluator 评分空预测；HPO 无最终配置为不可评分，完整 N4 若少一个必需成员，其 MI / BoN 都保持 unknown。完整均值、配对差与排名不以 known 子集替代，unknown 不补零。正文与附件保留原主要展示端点及次要指标，不新增显著性检验。

## 2. 主问题一：反馈预算收紧，ExpGym 是否退化？

五模型的 Search F1 与 Audit EA 均观察到 Free→Tight 下降；Kimi、GLM、Qwen、GPT 的九任务 HPO 总体 Gap 也下降。GPT 加入后，预算退化不再只出现在这四个自部署实例中；但实际 API 和采样配置不同，仍应读作列明设置下的描述性共同方向。

### 2.1 Search / Audit

{{EXP_SEARCH_AUDIT}}

Moderate 列说明下降发生在哪一段；whois 与 whatis 的拆分保留其不同任务结构。Audit EA 与 LA 分别展示：GLM、DeepSeek 的 LA 在受限档位高于各自 Free，GPT 的 LA 也并非从 Free 经 Moderate 单调下降，因此结论针对证据集合端点，不泛指所有 Audit 指标同步退化。

### 2.2 HPO：全体、三个家族及九个任务

{{EXP_HPO}}

HPO 总体下降不代表每项任务、每个 block 都下降，也不说明同一个模型在三个家族中均最优。DeepSeek Exp tuning 为70/81可评分，Free20/27、Moderate与Tight各25/27；完整九任务均值保持 unknown，不拿不同可评分子集均值之差补成总体趋势。第4章排名仅使用相应范围内三档完整的固定候选集，并明确排除的缺失模型。

### 2.3 HPO：三个 seed blocks

{{EXP_REPEATS}}

三个 blocks 的 SD 描述固定任务上的重复层变化，不是标准误或模型独立生成证明。完整任务、raw/Gap与unknown见 [REPEATS.md](REPEATS.md) 及 [by_outerseed.csv](by_outerseed.csv)。

## 3. 主问题二：缓存复用与 PoolAct 协调改善了什么？

以下对照固定同一模型、相同档位与N=4。cached−naive 是观察复用的描述性差异，poolact−cached 是进一步协调的差异，poolact−naive 为整体方法对照。相同反馈预算不等于相同 token 或实际推理时长，三组对照同时展示。

Kimi、GLM、Qwen 的 Search F1-MV、Audit EA-MV、NAS Gap-MI 在两档共六组主要展示端点上均有正的 poolact−naive；GPT 为四组正向、Moderate Search一组负向、Moderate NAS一组unknown；DeepSeek只有Tight Search主端点正向、Moderate Search与两档Audit负向、NAS完整对照unknown。改善的稳定范围需要从完整设置中读出，不能仅数有利切片。

{{POOL_CONTRASTS}}

### 3.1 Search：Tight 改善跨五模型出现

{{POOL_SEARCH}}

Tight Search 的投票F1在五模型上均高于各自naive，是PoolAct结果中最一致的跨模型方向。但Qwen的Tight投票结果仍低于cached；GPT与DeepSeek的Moderate投票结果均低于naive和cached。因而“相对naive改善”与“协调优于仅缓存”是不同主张，二者必须分别核对。

### 3.2 Audit：证据与标签，成员平均与投票分别报告

{{POOL_AUDIT}}

Kimi、GLM、Qwen、GPT在两档Audit的EA-MV均有poolact−naive改善，DeepSeek则在两档EA-MV和LA-MV均更低。GPT Moderate中投票EA改善也不能替代成员平均EA的变化；表中MI/MV和EA/LA始终保留，避免把不同端点合并成一个笼统“更好”。

### 3.3 NAS：MI 与 best-of-4 不互换

{{POOL_NAS}}

Kimi、GLM、Qwen的两个预算档位Gap-MI均优于naive。GPT Tight也有MI改善，但其BoN不随MI同向改善；成员整体水平与最佳候选质量不是同一个端点。

GPT Moderate poolact的一个NAS池中，一成员在本地近似context cap处停止、缺最终配置，因此该设置完整MI/BoN与涉及它的完整对照均为unknown，只有8/9完整池；不能用已知8池的正差代替9池完整结果。DeepSeek为135/216 tuning agents可评分，仅10/54严格N4池完整，六个预算×策略设置的完整MI/BoN均值均为unknown。缺失保留原分母，不因报告需要而恢复、重采样或从历史best-observed补最终答案。

{{POOL_REPEATS}}

NAS101 A/B/C的逐任务与三个blocks均保留，完整结果见 [TABLES.md](TABLES.md) 与 [REPEATS.md](REPEATS.md)。

## 4. 主问题三：任务家族与部署预算改变时，模型排名如何重排？

**本次候选模型中，不存在跨任务家族和反馈预算的单一赢家。** 在同一任务端点内，Free最优者不一定在Tight仍最优；另一方面，部分家族的领先者保持不变。这里的排名重排指实际部署的反馈受限程度改变后，已观察到的质量顺序发生变化，而不是根据不同指标拼一个跨模型总榜。

### 4.1 六个预设任务家族主端点

排名使用六个不重复的ExpGym端点：whois F1、whatis F1、Audit EA、ParamNet Gap、NAS101 Gap、NAS201 Gap。它们不再额外加入Search all或HPO all计数，也不混入PoolAct不同N/策略。每个家族先确定Free / Moderate / Tight三档都具有完整分母的模型，形成**跨三档固定候选集**，然后按原单位、越高越好排列；绝对差不超过`1e-12`的值按并列处理。unknown不补零，不以单档可评分者变动制造排名变化。

{{RANK_FAMILY}}

Free→Tight的六个家族中，两处冠军发生变化：**whatis由GPT变为DeepSeek，NAS101由GLM变为GPT**。whois仍为GLM、Audit仍为Qwen、ParamNet仍为GPT、NAS201仍为Kimi。这里三个HPO家族因DeepSeek完整结果缺失，候选集只有Kimi、GLM、Qwen、GPT；所谓NAS101换位是这四个完整候选内的换位，不能写成已确认五模型冠军。

任务家族之间也存在明显区别：whois领先者不能自动代表whatis，Audit的领先者也不代表ParamNet或NAS。模型选择因此应同时指定“做哪类任务”和“允许多少反馈”，不能只看Free下的一列绝对分数。

### 4.2 九个 HPO / NAS 任务的预算排名变化

{{RANK_TASK}}

在每任务固定、三档完整的候选集内，九个HPO任务有七个发生Free→Tight冠军换位。这是逐任务候选范围内的描述，不是九个任务都具备五模型完整证据。若严格要求五模型在三档全部完整，只剩两个任务，其中一个换位。两种口径同时列明，避免把缺失的DeepSeek当成落后，或把四模型比较扩写为完整五模型排行榜。

### 4.3 重排统计与部署含义

{{RANK_SUMMARY}}

完整名次、候选集、并列与各预算转移见 [RANKINGS.md](RANKINGS.md)、[RANKINGS.csv](RANKINGS.csv) 和 [RANK_TRANSITIONS.csv](RANK_TRANSITIONS.csv)。冠军不变也不意味着所有名次不变；反过来，小幅分数差导致的换位也不等于统计显著胜出。本次不新增p值、不凭名次数选择任务，也不将API medium、自部署最高effort及不同量化/拓扑条件视为已严格控制的纯模型能力实验。

部署上的直接含义是：应在实际任务家族与目标反馈预算下选型，并同时核对质量、缓存/协调策略和资源账本。下面将资源分为已有自部署分析单元均值与GPT全部尝试总账，避免把不同导出单位混成一个效率排名。

### 4.4 自部署四模型：分析单元资源与分配成本

以下资源均值沿用四模型冻结导出，按item内重复平均、再对item等权；不是整项研究总账。Pool的tokens、反馈次数及模拟反馈成本为四agents合计；Exp Audit资源为三个orders的均值。旧Kimi/GLM有整个pool子进程wall，新Qwen/DeepSeek原exporter没有该字段，保持unknown，不能用agent时长sum/max补齐。

受限档位的budget_utilization为反馈成本/B，Pool为四成员反馈成本合计/(4B)。最后一次已发起工具调用可能越过剩余预算，所以该值允许大于1；Free没有有限分母，标为“不适用”。模拟反馈秒不是GPU秒。

{{RESOURCES}}

| 模型 | 正式有效结果请求数 | Input tokens | Output tokens | 其中reasoning | 实际allocation GPU-hours |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kimi-K3 | 16,387 | 124,643,382 | 15,971,159 | 13,781,826 | 1259.235556 |
| GLM-5.3 | 18,403 | 323,702,359 | 61,759,454 | 59,754,394 | 1342.648889 |
| Qwen3.8 | 18,121 | 140,855,799 | 14,652,505 | 12,785,832 | 468.204444 |
| DeepSeek-V4-Flash-0731 | 14,300 | 105,359,032 | 23,345,301 | 18,484,906 | 98.062222 |

reasoning已包含在output，不能重复相加。Kimi完整尝试的已知input/output小计为126,556,991 /16,272,997，另63次用量未知；上表有效结果不能冒充其完整尝试成本。其余三模型的相应完整尝试与有效结果总计相同。DeepSeek推荐成本源为full_v2，其中双形状reasoning字段修复不改变科学评分。

GPU-hours按实际顶层allocation的GPU数×elapsed÷3600计算，包含加载、失败启动、smoke、等待与空闲，不是formal-only有效计算量。Kimi账本含固定8项恢复；Qwen含失败启动21.04GPUh；DeepSeek含编译缓存隔离前启动12.293333GPUh。不同模型、副本数、并发、精度和输出长度共同影响资源，不能据该表推断纯模型效率或同算力下质量排名。

固定来源：[旧两模型总账](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/COSTS.json)；[Qwen HTTP成本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/analysis/full_v1/COSTS.json)与[分配账本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/study/accounting.json)；[DeepSeek HTTP成本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/analysis/full_v2/COSTS.json)与[分配账本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/study/allocation_final/ACCOUNTING.json)。

### 4.5 GPT：逐 setting 的全部 API 尝试总账

GPT原资源表按唯一物理request、job与agent槽位计入全部尝试，不通过MI/MV/Gap多行重复计费。下表是**setting总量**而非上节item等权均值，不与旧四模型均值混排；agent wall之和不是pool wall，也不是实验总历时。

{{GPT_RESOURCES}}

GPT共14,682次物理尝试，含13次失败及其重试；最终783执行槽全部完成，不意味着每次HTTP尝试都成功。13个失败尝试没有usage，所以完整token总量为unknown。已知小计为input120,478,791、output2,947,888、reasoning1,870,955、cache-read74,817,408；reasoning已含在output，Responses cached input已含在input，二者均不可再次相加。已知input+output小计123,426,679，不是无缺失的完整总量。

GPT的API请求观察跨度为2026-09-10 22:33:08.898804至2026-09-11 01:36:25.038024 UTC，含暂停和等待，只是首末记录跨度。网关并发上限运行中由8调整为24、worker数仍6，此变化保留在原元数据中，不反写成初始条件。没有本地GPU分配，也不据token虚构美元成本或拿“无本地GPU”当作零计算成本。27个正式setting的原资源总表见 [api_resources.csv](inputs/api_resources.csv)，全部尝试账本的原位置见 [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md)。

## 5. 围绕三个主张的归纳

1. **预算收紧导致的性能退化具有跨模型共同方向。** 五模型Search F1和Audit EA均在Free→Tight下降；Kimi、GLM、Qwen、GPT的HPO总体Gap也下降。完整Moderate列与任务拆分说明退化发生在哪一段、哪些端点更敏感，DeepSeek HPO完整未知和LA不同向均保留在相应表旁。
2. **PoolAct能够改善受限反馈下的质量，但收益取决于任务、模型与对照。** 五模型Tight Search F1-MV均优于naive；Kimi、GLM、Qwen的六组主要端点全部正向，GPT和DeepSeek则有场景限制与unknown。cached对照、MI/MV/BoN和资源账本一起说明改善来自什么设置，不能把质量提升扩大成所有模型、所有任务、相同实际成本下均更优。
3. **任务家族与预算强度会重排模型选择。** 六个预设家族在跨三档完整的固定候选集内，有两处Free→Tight冠军换位；九个HPO任务有七处换位，严格五模型完整的两个任务中有一处换位。whois、Audit、ParamNet、NAS201等家族的领先模型本就不同，因此选型应依据目标任务和部署反馈预算，而非用Free下总榜固定一个“最好模型”。

## 6. 表格文件与生成方法

[absolute_settings.csv](absolute_settings.csv) 保留五模型所有实际设置的绝对指标；[contrasts.csv](contrasts.csv) 保留预算/策略对照及known/expected；[by_outerseed.csv](by_outerseed.csv) 保留重复层。完整可读表在 [TABLES.md](TABLES.md) 和 [REPEATS.md](REPEATS.md)。新增 [RANKINGS.csv](RANKINGS.csv)、[RANK_TRANSITIONS.csv](RANK_TRANSITIONS.csv)、[RANKINGS.md](RANKINGS.md) 只从这些冻结分数派生，不产生新模型结果。

输入身份、原路径和快照见 [INPUTS.json](INPUTS.json)，生成器与适量fixture分别为 [build_report.py](build_report.py)、[test_report.py](test_report.py)。旧模型与API导出schema显式适配，保留分数方向、完整与已知子集、Audit顺序折叠以及资源单位；不以已舍入正文值算新差值，不将API的39个Audit顺序结果当39个独立文档，不从不完整NAS子集生成冠军。

13 份输入中，12 份是同字节冻结副本；`api_request_scope.json` 是公开派生副本，仅将两个描述性的 Authorization 模板值改为标准脱敏标记。清单分别保存原件与公开副本的大小、SHA及精确转换规则，原实验元数据不修改；评分输入均未改写。

下载本报告目录后，可以仅用Python标准库离线检查或重新生成表格，不必恢复raw。原生成环境为 CPython 3.11.15；其他版本可能产生浮点末位或输出字节差异，精确 `--check` 应使用原版本：

```bash
python3 -B -m unittest test_report test_rankings test_archive_index
python3 -B build_report.py --check
```

去掉`--check`即从冻结快照及[正文模板](REPORT_TEMPLATE.zh.md)重新生成；[rankings.py](rankings.py)与[report_tables.py](report_tables.py)分别负责排名和展示。索引复建另需原索引的五份固定metadata，命令见[存档索引](ARCHIVE_INDEX.md)。本报告快照重建不等于上游原实验重放。

旧四模型来源为固定`a79cbc1`合报的 [prior_absolute.csv](inputs/prior_absolute.csv)、[prior_blocks.csv](inputs/prior_blocks.csv)、[prior_contrasts.csv](inputs/prior_contrasts.csv)。GPT原绝对聚合表只覆盖family层；本次所需task表从 [gpt_metrics.csv](inputs/gpt_metrics.csv) 中已经保存的质量指标按item/repeat聚合，**不调用scorer**，并与原 [absolute](inputs/gpt_absolute.csv)、[repeats](inputs/gpt_repeats.csv)、[contrasts](inputs/gpt_contrasts.csv) 保持明确对应。

排名规则固定六家族、九HPO任务、完整候选集与`1e-12`并列容差；不添加相互重叠的all作为额外家族，不依据胜负挑模型或删任务。完整排序是本次描述性派生，不替代原研究比较定义，也不声称获得确认性统计证据。

本次使用的GPT小型分析/配置来源通过明确清单快照到`inputs/`，其角色、大小、SHA和公开状态由清单标明；另保留原 [GPT有限验证记录](inputs/gpt_validation.json) 与 [API成稿复核记录](inputs/api_review.json) 的来源身份，它们不代替本轮五模型报告复核。原始大账本及上游完整INPUTS只登记位置，不重复复制；raw、凭据、provider headers和运行目录不随意加入。生成器只处理本次列明输入，不触发模型、工具环境、scorer或全量archive恢复。

## 7. 原始 dump、聚合比较与恢复：完整存档索引

统一入口为 [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md) 与 [ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)，汇集五模型报告输入、原指标与成本、原件清单/归档以及各自恢复边界。旧四模型继续使用已经发布的固定数据与报告身份，不重封、不复制已有大归档。

| 范围 | 报告与索引入口 | 当前存档状态 |
| --- | --- | --- |
| 已发布四模型合报 | [报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/a79cbc100804a1bc8d374e084a4b9999e3697a91/results/four-model-20260911/README.zh.md) · [完整索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/a79cbc100804a1bc8d374e084a4b9999e3697a91/results/four-model-20260911/ARCHIVE_INDEX.md) · [JSON](https://github.com/tiannuo-yang/LLM_ExpGym/blob/a79cbc100804a1bc8d374e084a4b9999e3697a91/results/four-model-20260911/ARCHIVE_INDEX.json) | 各原件保持原固定提交；索引逐模型链接，不重复累计Kimi composite引用 |
| GPT冻结分析与API资源总表 | 本次[输入清单](INPUTS.json)、[统一索引](ARCHIVE_INDEX.md)及`inputs/`明确快照 | 分析/配置来源可由本次报告清单追溯；raw仍为本地冻结归档 |
| GPT / Claude原API研究 | 本地原全报告及原交付索引，确切路径见下文与统一索引 | 不将原本地封存或既有有限扫描等同于完整公开发布验收；Claude不入本报告排名 |

GPT原分析根为 `/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/`；API总报告与资源表根为 `/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_api_studies_20260910/studies/api_20260910/full_report_v1/`。其中`source_index.json`映射原结果、receipt和失败证据，`all_attempt_costs.csv`保留全部尝试，`resources_by_setting.csv`保留API setting资源总账。它们不是HTTP原始回复的替代物。本地归档位置及公开状态由本次统一索引登记，不为GPT raw提供尚不存在的GitHub下载链接。

存档应包含原件清单、分片、外层分析/成本附件、配置与本次合报，只有tar或只有报告均不足。使用对应历史格式的恢复工具；Qwen / DeepSeek原分析器绑定绝对原件/状态路径，换目录下载可读raw/CSV，不自动提供任意路径下的逐字节分析重放。复用旧哈希声明和Git身份不意味着本次重新读取全部tar成员，更不等于重新评分。

## 8. 验收记录

本次按`expgym-runner`报告流程固定输入、生成全设置表与排名、完成正文和统一索引，再执行一次成稿独立数字/逻辑复核及确切增量发布检查。验收针对完整、忠实、可追溯，而不是要求所有模型的结果同向。

检查范围包括五模型实际矩阵与单位映射、GPT省略参数及不完整NAS端点、完整/known分母、六家族和九任务固定候选排名、并列与预算转移、原资源口径、公开与本地存档边界，以及本次新增文件的扫描/远端身份。实际执行、修正与通过情况见 [REVIEW.md](REVIEW.md) 和 [VALIDATION.json](VALIDATION.json)，不把旧报告的review或计划中的检查称作本轮已经通过。

本轮不申请GPU、不新增API请求、不重跑scorer，不恢复或重打包全部旧raw。发布沿用用户指定github-tn身份，仅处理明确列出的新增/修改字节；报告发布不自动宣布GPT全部原始归档已公开。完成有限验收后停止，不为同一冻结数据继续建立重复审计链。
