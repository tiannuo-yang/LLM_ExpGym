# Kimi-K3、GLM-5.3、Qwen3.8 与 DeepSeek-V4-Flash-0731：ExpGym / PoolAct 全设置实验报告

本报告回答两个问题：**反馈预算收紧时，单 agent 的任务表现如何变化？在相同预算档位、相同 N=4 条件下，缓存复用与 PoolAct 协调各带来多少收益？**

实验类型为 Custom study：沿用论文的任务与机制比较思路，以实际冻结矩阵、生成设置和评分契约为准，不作为论文数值的逐项精确复现。本报告按照原 [Kimi-K3 / GLM-5.3 全设置报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md) 的八章结构，加入已经完成的 Qwen3.8 与 DeepSeek 结果；**仅合并、组织冻结导出，不新增模型调用、不重评分，不修改历史结果。**

这里展示 ExpGym 的 **Free / Moderate / Tight**，以及多 agent 的 **naive / cached / poolact × Moderate / Tight**。四模型在 Search 和 Audit 证据指标上都观察到 Free→Tight 退化；PoolAct 的收益则有明确适用范围：Kimi、GLM、Qwen 的六组主要展示端点均优于 naive，DeepSeek 只在 Tight Search 观察到相应改善，其余结果不支持普适优势。

**存档入口：** [原始 dump 与聚合比较完整索引](ARCHIVE_INDEX.md) · [机器可读索引](ARCHIVE_INDEX.json)。正文第 7 节给出四模型原报告、原件与成本的固定入口。

## 1. 实验设置与覆盖

### 1.1 四模型采用相同的科学矩阵

| 系统 | 任务 | 实际项目数 | 成本档位 | 方法 / agent 数 | 重复设置 |
| --- | --- | ---: | --- | --- | --- |
| ExpGym | Search | 73 题：39 whois + 34 whatis | Free / Moderate / Tight | single，N=1 | 每题每设置 1 次 |
| ExpGym | Evidence Audit | 13 文档，17 hypotheses | Free / Moderate / Tight | single，N=1 | 每文档 3 个固定 hypothesis 顺序，文档内平均一次 |
| ExpGym | HPO / NAS | 9 任务 | Free / Moderate / Tight | single，N=1 | 每任务每设置 3 个 seed blocks |
| 多 agent | Search | 39 道 whois | Moderate / Tight | naive / cached / poolact，均 N=4 | 每题每设置 1 个独立池 |
| 多 agent | Evidence Audit | 13 文档 | Moderate / Tight | naive / cached / poolact，均 N=4 | 默认 hypothesis 顺序，每文档每设置 1 个独立池 |
| 多 agent | NAS | NASBench101 A / B / C | Moderate / Tight | naive / cached / poolact，均 N=4 | 每任务每设置 3 个独立池 |

9 个单 agent HPO / NAS 任务为 ParamNet adult、higgs、letter，NASBench101 A、B、C，以及 NASBench201 cifar10-valid、cifar100、imagenet16-120。Search 使用 PhantomWiki seed2 / seed3 两个固定 world；相同问题共享 world，不等于相同数量的独立语料。单 agent Search 的 73 题与 Pool 的 39 题、单 agent tuning 的 9 任务与 Pool 的 3 任务不是同一全集，不能直接拿两个系统的 `all` 计算胜负。

每模型对应 **783 个顺序/重复/池级逻辑结果、1,881 个 agent 结果，以及折叠 Audit 顺序后的 705 个分析单元**。物理执行方式不同：Kimi / GLM 的 Audit 三顺序同属一次 invocation，因此每模型为 705 次 invocation；Qwen / DeepSeek 将三顺序拆为三个进程，因此每模型为 783 个执行槽位。不能把这个进程数差异当成增加了实验样本。Kimi 最终结果由原 697 个完成 invocation 与批准恢复的固定 8 项组成，失败尝试及其成本仍保留；其余三模型不以质量表现为理由增加重抽样。

四模型的数据、任务身份和来源见 [输入清单](INPUTS.json) 及各原报告索引。此次核对已有元数据清单：Qwen 与 DeepSeek 的 249 个数据文件路径、大小和 SHA 声明相同；旧 Kimi manifest 的 19 项数据载荷/清单 SHA 与大小也能在新模型数据清单中对应。HPO oracle、任务配置与 Audit 顺序配置的冻结身份一致。这是已发布清单的比对，**不是本次重新读取数据 payload 或 raw 的完整性验证**。

### 1.2 Free、Moderate、Tight 的具体含义

| 档位 | 模拟反馈预算 B | 是否向 agent 展示成本 / 剩余预算 |
| --- | --- | --- |
| Free (`cost_free`) | 无有限预算上限 | 否 |
| Moderate (`cost_moderate`) | 10 × c_base | 是 |
| Tight (`cost_tight`) | 3 × c_base | 是 |

Search / Audit 的 c_base=300 模拟秒，对应 Moderate 3000、Tight 900 模拟秒；HPO / NAS 使用同一冻结 oracle 的任务级 reference-best evaluation cost。Free 仍受 30 步 / 30 次评估及单次输出上限约束，不是无限生成。这里改变的是**工具反馈预算与成本可见性**，不是把 GPU 时间或 token 上限设为三档；Free 与受限档位的差异不能仅归因于预算数值，而忽略成本可见性。

多 agent 三种方法均为 N=4，每个 agent 各有同一 B，不是整个池只共享一个 B。未运行多 agent Free，也未运行 Pool whatis、ParamNet 或 NASBench201；这些组合是未计划，不是零分或缺失实验。

### 1.3 方法、生成配置与服务实现

| 方法 | 实验含义 |
| --- | --- |
| naive | 四个 agent 独立探索，不共享观察缓存和探索图；结束后按原任务规则聚合。 |
| cached | 共享已经完成、当前模拟时间可见的相同工具调用结果，避免重复支付该次反馈的模拟成本。 |
| poolact | 在 cached 基础上提供共享探索图与协调决策；决策与动作 claim 使用 reasoning lock，工具执行在锁外。 |

池内成员不是四次独立重复。PoolAct 的共享图注入、一次 LLM 决策和动作登记受同一推理锁保护，因而池内模型推理并发与 naive / cached 不同；全局队列并行的是独立 pool，不能以 `workers × N` 直接计算 PoolAct 的同时推理数。

| 配置 | Kimi-K3 | GLM-5.3 | Qwen3.8-2.4T-A95B-FP8 | DeepSeek-V4-Flash-0731 |
| --- | --- | --- | --- | --- |
| 模型服务 | 自部署，SGLang / OpenAI-compatible native tools | 同左 | 同左 | 同左 |
| Temperature / top-p | 1.0 / 1.0 | 1.0 / 0.95 | 1.0 / 0.95 | 1.0 / 0.95 |
| top-k 请求 | 未显式发送 | 未显式发送 | 20 | 未显式发送 |
| 单次 max_tokens | 32768 | 32768 | 32768 | 32768 |
| reasoning_effort 请求 | `max` | `max` | `xhigh` | `max` |
| chat_template_kwargs 请求 | `{"thinking":true,"thinking_effort":"max"}` | `{"clear_thinking":false,"reasoning_effort":"max"}` | `{"enable_thinking":true,"preserve_thinking":true}` | `{"thinking":true}` |
| max_steps / max_evals | 30 / 30 | 30 / 30 | 30 / 30 | 30 / 30 |
| 服务端 context | 524288 | 262144 | 262144 | 1048576 |
| Pool 本地输入 cap | 131072 近似 tokens | 同左 | 同左 | 同左 |
| HTTP timeout | 3600 s | 3600 s | 3600 s | 7200 s |
| 本轮资源与拓扑 | 8 节点 × 8 GPU；4 个 TP16 / EP16 副本 | 8 节点 × 8 GPU；4 个 TP16 / EP1 副本 | 4 节点 × 8 GPU；1 个 TP8 × PP4 / EP1 副本 | 4 节点 × 8 GPU；4 个 TP8 / PP1 / EP1 副本 |
| 实际正式队列 workers 上限 | 32 | 32 | 首 session 16；自然 drain 后以 6 续接 | 全程 32 |

HPO seed blocks 为 2200 / 2204 / 2208；池内四成员使用 block 至 block+3。Search / Audit 使用首个 block，ExpGym Audit 三顺序为 2200 / 2201 / 2202。标签相同不证明采样逐 token 可重复，也不证明不同标签构成独立生成重复。原生工具协议最多一次 protocol repair，HTTP 重试上限 2；Pool 本地 context 是序列化字符及工具 schema 的近似 token 估计，不是服务端精确 tokenizer 计数。ExpGym 未另设本地 context cap。

实际实验源码为 Kimi / GLM [`8dfea72`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/8dfea72931d952ad90f1c722a83957ab23afc6bf)、Qwen [`21b4de9`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/21b4de99b2a014874e3cec1595eaa40762b0c564)、DeepSeek [`5aabf7f`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8)。科学矩阵和评分端点相同，不代表全部执行源码、采样器、模板和部署条件相同。

Qwen 与 DeepSeek 均使用独立 uv 运行时：CPython 3.12.13、SGLang 0.5.17、Torch 2.11.0+cu129。Qwen 未修改 SGLang sampler/model 源码，采用 FP8 checkpoint、float32 SSM 与最终 page-size=1；模板不支持 `max`，使用其最高档 `xhigh`。DeepSeek 在同一 SGLang 基线上应用精确官方 [`0592695` effort 编码修复](https://github.com/sgl-project/sglang/commit/059269594c5f245f77dad711631843c299d7713f)，使0731的 `max` 真正对应最高档，而非旧 encoder 的 high 映射；FP4 experts / FP8 dense、Marlin W4A16 与 dsv4 attention 保持显式配置。最高 effort **不等于等量推理**，DeepSeek 的 32768 输出上限也不等于厂商推荐的 384K 长输出配置。

两个后续模型显式使用 SGLang 消费的 `cache_salt`；旧客户端字段为 `prompt_cache_key`，不能将后续验证过的行为反写为旧服务已验证。这里的推理前缀缓存与 PoolAct 共享工具观察缓存是不同机制。forced-final 的 HTTP schema/history 保留也不代表模型模板相同：Qwen 模板会移除工具定义/说明、保留历史；DeepSeek encoder 仍保留工具定义及 reasoning/tool history。新两模型均完成对应原生工具验证，但这不消除模型间的模板与部署差异。

可查原始固定设置：[Kimi / GLM 设置证据](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/claim_setting_preflight_v1/EVIDENCE.json)；[Qwen 输入身份](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/study/RUN_INPUTS_launch02.json)、[服务计划](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/serving/launch02/plan.json)；[DeepSeek 输入身份](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/study/formal_v1/RUN_INPUTS.json)、[服务计划](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/serving/launch02/plan.json)、[provider 契约](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/study/provider_contract.json)。预启动计划内的 readiness 标志不替代原研究完成后的验收记录。

### 1.4 指标、完整分母与汇总口径

- Search：集合 F1；Audit：EA 为精确证据集合准确率，LA 为标签准确率。F1 / EA / LA 为 0–1 分数；差值 0.01 是 1 个百分点。
- HPO / NAS：Gap 是冻结 oracle 归一化后的效用，越高越好；raw performance 是原任务分数。采用冻结 `legacy` final policy，不把 Gap 当作越低越好的 regret，也不从汇总 raw 分数反推 Gap。成员先按 oracle 计算并截零，再算 MI；只设下界，不截到 100，超过参考最优时可以大于 100。
- MI 为成员分数均值，MV 为原投票规则的结果，BoN 为四成员最佳分数。MI 与 MV / BoN 均为池级端点，不是四份独立样本。
- 先在 item 内平均重复，再对 item 等权平均；ExpGym Audit 三顺序已经在文档内折叠一次，不再重复计权。三个 blocks 的 SD 是描述性变动，不是标准误或独立生成的证明；R1 不伪造重复 SD。
- `task-abstention-v1` 下，正常 Search / Audit 空回答通过原 evaluator 得到空预测分数，原 null 仍保留；HPO 缺最终配置不可评分。完整均值或配对差只在计划分母全部已知时给出；unknown 不补零，known 子集另列，不能悄悄取交集或替换完整端点。

本次不新增显著性检验或跨模型平均总分。文中“主要展示端点”指 ExpGym 的 F1 / EA / Gap，以及 Pool 的 F1-MV / EA-MV / Gap-MI；这是沿用报告结构的展示选择，不将回顾性矩阵包装成事前预注册。

## 2. 主问题一：反馈预算收紧，ExpGym 是否退化？

**Search 的预算退化在四模型上最一致，Audit 的证据指标也有相同总体方向。** Free / Moderate / Tight 完整列用于区分退化发生在哪一段，而不只是给出 Free−Tight 一次差值。Kimi、GLM、Qwen 的九任务 HPO 总体也观察到 Free→Tight Gap 下降；DeepSeek 的 HPO 完整端点不可评分，不能用于补成“四模型 HPO 结论一致”。

### 2.1 Search / Audit

{{EXP_SEARCH_AUDIT}}

Audit 的分析 R1 是已经平均三个固定顺序的文档级单元，并非只运行一个顺序。Search 表列出 whois / whatis；原逐题导出保留两个 world 的题目身份，不按结果方向挑选题目。本次不另算按 world 汇总。

EA 与 LA 需分开解释：GLM、DeepSeek 的 Audit 标签准确率在 Moderate / Tight 均高于各自 Free，但精确证据集合准确率从 Free 到 Tight 下降。因此本轮稳定观察到的是**证据收集端点退化**，不能扩大为“Audit 的所有能力或所有指标同时退化”。

### 2.2 HPO：全体、任务家族及九个任务

{{EXP_HPO}}

此处完整呈现 ParamNet、NASBench101、NASBench201 及九个任务，不能用表现较好的 NAS 子集替代单 agent HPO 的 `all`。总体均值的下降也不代表每项任务、每次重复都下降。

DeepSeek Exp tuning 共 70/81 个 agent 可评分：Free 为 20/27，Moderate / Tight 各为 25/27。因此三档九任务 `all` 的完整 Gap / raw 均值保持 unknown；已知子集的均值只用于展示已观察到的范围，不能拿不同可评分子集之差判定总体退化或改善。缺少的是最终配置，不是已证明此前没有任何可评分工具观察；不在报告阶段用历史 best-observed 替换冻结 missing-final 策略。

### 2.3 HPO：三个 seed blocks

{{EXP_REPEATS}}

同一 block 标签跨任务形成一个描述性重复层；三个 blocks 不是九个全新任务，更不因为池中有四个成员就变成十二次独立重复。完整结果、unknown 与逐任务对应关系见 [REPEATS.md](REPEATS.md) 和 [by_outerseed.csv](by_outerseed.csv)。

## 3. 主问题二：缓存复用与协调，分别改善了什么？

这里比较同一模型、相同预算档位与 N=4 的三个方法。**cached−naive** 表示加入观察复用后的描述性差异；**poolact−cached** 表示进一步加入探索图/协调后的差异；**poolact−naive** 是整体策略比较。相同模拟反馈预算不等于相同 token、推理时间或 GPU 成本，两个独立 run 的差值也不是已隔离全部因素的因果估计。

Kimi、GLM、Qwen 的 Search F1-MV、Audit EA-MV、NAS Gap-MI，在 Moderate / Tight 两档共六组主要展示端点上均有正的 poolact−naive 差值。这个跨三个模型的共同方向值得保留，但 DeepSeek 的结果说明它**不是四模型上的普适优势**：仅 Tight Search 主端点改善，Moderate Search 与两档 Audit 方向相反，NAS 完整比较未知。

{{POOL_CONTRASTS}}

### 3.1 Search：Tight 下出现四模型共同的 PoolAct−naive 改善

{{POOL_SEARCH}}

四模型的 Tight Search 投票 F1 均高于各自 naive。这是本次 PoolAct 结果中跨模型最一致的方向，但并不等价于 PoolAct 总是最优：Qwen Tight Search 的 F1-MV 仍低于 cached；DeepSeek Moderate Search 的 F1-MV 则低于 naive 和 cached。缓存与协调的差异必须保留三个方法才能看清，不能只展示一个 baseline。

MI 与 MV 分别反映成员平均表现和最终投票质量，两者可不沿同一方向变化。不能在某个对照不利时把主要展示端点从 MV 换成 MI，或事后改成挑选最优成员答案。

### 3.2 Audit：证据集合与标签投票分别报告

{{POOL_AUDIT}}

Kimi、GLM、Qwen 在两档 Audit 的 EA-MV 均有 poolact−naive 改善；DeepSeek 的 EA-MV 与 LA-MV 在两档都更低。故报告支持“协调收益依赖模型与任务交互”，而不是“同一图共享机制对所有模型都稳定有利”。EA、LA 的 MI 与 MV 同时保留，也不把标签正确误写成证据完整。

### 3.3 NAS：成员平均效用与 best-of-4 分开看

{{POOL_NAS}}

Kimi、GLM、Qwen 在两个预算档位的 Gap-MI 均优于 naive，但 MI 提升不自动意味着 BoN 也提高；best-of-4 已接近参考水平时，成员整体质量与最佳候选质量的变化可不同。逐任务表覆盖 NAS101 A/B/C，不按某项正负缩小 `all`。

DeepSeek Pool tuning 为 135/216 个 agent 可评分，而严格完整 N4 池只有 10/54 个。每个预算×策略应有 9 个池；Moderate 的 naive / cached / poolact 完整池数分别为 1/3/1，Tight 为 2/1/2。六个设置的完整 MI / BoN 均值均为 unknown，不能以可评分成员或完整池子集代表全体。其 poolact−naive 在 Moderate 仅 0/9、Tight 仅 1/9 配对端点已知；即使已知子集有正差，也不能用来证明 NAS 整体改善。正常缺最终配置与执行失败是不同事件，不能为补齐质量分母而重抽样。

{{POOL_REPEATS}}

以上三个 seed blocks 的变动仅用于描述固定任务的重复层结果；完整 MI、BoN、raw 与全部负值、unknown 见 [TABLES.md](TABLES.md) 和 [REPEATS.md](REPEATS.md)。

## 4. 运行资源与反馈使用

**受限反馈下质量改善，不等于相同实际推理开销下更省。** 观察复用可以减少重复模拟反馈，而图上下文、协调推理和池内串行决策可能增加或改变模型侧开销。只有保留质量、反馈、token 与实际时长的不同口径，才能判断具体设置的取舍。

下表取已有分析单元遥测，先 item 内平均重复、再 item 等权，不是整项研究的总账。Input / Output 是 token；reasoning 已包含在 Output，不能再次相加。反馈秒为模拟工具成本，不是 GPU 秒。Exp Audit 的遥测为每文档三个 orders 的均值，不是三次合计。

Pool token、反馈次数与模拟成本是四 agents 合计；旧 Kimi / GLM 的 pool wall 来自整个子进程 source_capture.elapsed_seconds。Qwen / DeepSeek 的原 exporter 未记录整个 pool wall，因此保留 unknown，**不使用 agent wall 的 sum / max 补齐**。这项导出差异不能解读为运行没有耗时，也不能据不一致的 wall 字段作跨模型速度排名。Free 无有限预算，budget_utilization 标为“不适用”；这不同于已计划但遥测缺失的 unknown。

受限档位的 `budget_utilization` 为反馈成本 / B；Pool 为四成员反馈成本合计 / (4B)。环境在动作之间检查预算，最后一次已发起工具调用可以越过余额，因此该值允许大于 1，不在报告中截为 1。

{{RESOURCES}}

### 4.1 有效结果与完整尝试的总体模型用量

| 模型 | 有效分析单元 / 逻辑结果 / agent 结果 | 正式持久化请求数 | Input tokens | Output tokens | 其中 reasoning tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| Kimi-K3 | 705 / 783 / 1881 | 16,387 | 124,643,382 | 15,971,159 | 13,781,826 |
| GLM-5.3 | 705 / 783 / 1881 | 18,403 | 323,702,359 | 61,759,454 | 59,754,394 |
| Qwen3.8 | 705 / 783 / 1881 | 18,121 | 140,855,799 | 14,652,505 | 12,785,832 |
| DeepSeek-V4-Flash-0731 | 705 / 783 / 1881 | 14,300 | 105,359,032 | 23,345,301 | 18,484,906 |

上表 Kimi 是最终有效结果用量；包含原失败尝试的**已知** input / output 小计为 126,556,991 / 16,272,997，另有 63 次用量未知，不能把该小计写成完整已知总量。GLM 的完整尝试与有效结果相同；Qwen / DeepSeek 的 `all_physical_attempts` 与 `effective_slots` 总计相同。正式 HTTP 总账不把 native / task smoke 加入正式质量分母。

Qwen / DeepSeek 的 reasoning 读取同时支持 usage 顶层与嵌套形状，不按 reasoning 文本估算，也不重复加入 output。DeepSeek 的推荐成本源为 `full_v2`；修复只补齐漏读的 reasoning 用量，原科学结果未被重新评分。各模型 tokenizer、推理设置、任务进程结构与服务拓扑不同，以上 token 数不是直接可比的有效计算量。

### 4.2 实际 Slurm 分配成本与队列历时

| 模型 | 本次冻结总账内 Slurm allocation | allocation GPU-hours | 口径 |
| --- | --- | ---: | --- |
| Kimi-K3 | 1203653、1203933 | 1259.235556 | 原服务及固定 8 项恢复服务；包含加载、验证、等待和空闲 |
| GLM-5.3 | 1203652 | 1342.648889 | 一次完整服务分配；包含准备与非正式执行时间 |
| Qwen3.8 | 1204491、1204495 | 468.204444 | 包含失败启动 21.04 GPU-hours 及最终服务分配 |
| DeepSeek-V4-Flash-0731 | 1204605、1204607 | 98.062222 | 包含编译缓存隔离前的启动与最终服务分配 |

每项以顶层 job 的实际分配 GPU 数 × Slurm elapsed 秒 ÷3600 计算，不再乘副本数或重复加入 batch/extern steps。这是**资源保留量**，不是实测有效 GPU compute、formal-only 用量或完整项目历史总成本；不同服务拓扑、并发、精度、模型规模、加载和空闲都影响它，不能据此宣称模型本身速度或成本效率的因果排名。

Qwen 正式队列从 2026-09-10 23:51:51 UTC 到 2026-09-11 13:24:48 UTC，两 session 的 elapsed 分别为 8196.595 s 与 40440.522 s，中间有已记录的停止准入、自然 drain 与同计划续接；已有完成项只作身份校验，不重算得分或重跑模型。DeepSeek 全部正式执行在 2026-09-11 04:39:11–06:48:03 UTC 自然完成，队列 elapsed 为 7731.582 s，正式 workers 全程为 32。两者 HTTP request wall 合计分别为 482219.492 s 与 274929.122 s，不能相加或与 queue wall 混用来推导实验历时。四副本动态补位也不证明所有 GPU 全程饱和。

固定账本：[Kimi / GLM 总成本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/COSTS.json)；[Qwen HTTP 成本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/analysis/full_v1/COSTS.json)、[Slurm/queue 账本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/study/accounting.json)；[DeepSeek HTTP 成本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/analysis/full_v2/COSTS.json)、[Slurm 账本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/study/allocation_final/ACCOUNTING.json)。

## 5. 围绕主张的归纳

1. **反馈预算收紧带来的退化具有跨模型共同方向。** 四模型 Search F1 与 Audit EA 在 Free→Tight 均下降；Moderate 列说明损失发生在哪一段。Kimi、GLM、Qwen 的 HPO 总体 Gap 也下降；DeepSeek 因完整配置分母缺失，不能给出同等级的 HPO 结论。Audit LA 与 EA 的方向并不总相同，不把证据端点退化扩大到所有能力。
2. **PoolAct 的收益能跨部分模型出现，但有清晰边界。** Kimi、GLM、Qwen 的六组主要展示端点均优于 naive；四模型 Tight Search F1-MV 共同改善。DeepSeek Moderate Search、Audit 的负向结果以及 HPO unknown 同样构成结论的一部分，排除了本轮“所有模型、所有场景稳定改善”的概括。
3. **cached 是必要中间对照，协调不总比缓存更好。** Qwen Tight Search 投票质量低于 cached，说明 poolact−naive 为正仍不能证明协调部分优于仅缓存。NAS 同时保留 MI 与 BoN，区分成员平均质量和最佳候选质量。
4. **这里比较的是固定设置下的质量与资源取舍，不是等实际成本下的普适优势。** N=4 和每 agent 同反馈预算没有控制 token、推理锁、服务并发或 GPU 分配成本。四模型的源码/provider、采样设置、上下文与拓扑不同，合报是同任务上的并列描述，不是纯模型能力排行榜、跨模型总体推断或统计显著性证据。

这些结论对应四个已经运行的 checkpoint、所列固定任务及冻结生成设置。结果相符与不相符都保留；报告整理不能将完整性验收改成“必须得到预期性能趋势”。

## 6. 表格文件与生成方法

[全部绝对聚合指标](absolute_settings.csv) 保留各模型、系统、场景、任务层次、档位、策略、指标与分母；[全部对照差值](contrasts.csv) 保留比较方向、完整端点及 known 子集；[逐 seed-block 表](by_outerseed.csv) 保留重复层结果。[TABLES.md](TABLES.md) 与 [REPEATS.md](REPEATS.md) 提供完整可读附件，正文按原八章结构组织主要表格，而不是另选一套有利数字。

输入固定清单见 [INPUTS.json](INPUTS.json)，本次生成器见 [build_report.py](build_report.py)，针对报告适配与聚合契约的测试见 [test_report.py](test_report.py)。`inputs/` 内是按清单固定 Git commit 取得的原样小型 CSV/JSON 快照；下载本报告目录后可离线运行以下命令，不依赖原始 dump 或旧绝对路径：

```bash
python3 -B -m unittest -v test_report test_archive_index
python3 -B build_report.py --check
```

去掉 `--check` 可从快照与 [正文模板](REPORT_TEMPLATE.zh.md) 重新生成表格和正文。索引的独立复建入口与六个固定外部索引输入见 [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md)。本次仅读取列明的冻结导出并统一展示，不调用模型、scorer 或工具环境，不修改旧 metrics、原始终态、请求/回复、归档或旧分析器。原报告中的展示舍入不作为计算新差值的输入；先使用冻结未舍入值，再格式化。旧模型对照是完整冻结均值的描述性差，新模型直接保留原生配对导出的结果；有缺失时不对不同 known 子集的均值做差。

旧模型与新模型导出 schema 不同，适配时明确映射模型、分析单元、档位、指标、完整与缺失分母；已折叠的 Audit orders 不再折叠第二次。保留旧 CSV 的真实资源单位，并使新模型原本缺少的 Pool wall 继续为 unknown。原 `raw_terminals` 仅为终态投影，不替代 HTTP 原始 dump；本次 CSV 也不是重新签发的逐题评分证据。

此次输入身份和哈希的读取范围、继承的旧检查声明以及实际生成核对范围，以 [INPUTS.json](INPUTS.json)、[REVIEW.md](REVIEW.md) 与 [VALIDATION.json](VALIDATION.json) 为准，不把本次元数据比对写成又做了一次全量 raw/归档验证。

## 7. 原始 dump、聚合比较与恢复：完整存档索引

**统一入口：** [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md) · [ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)。这里汇集既有原件、逐文件 member inventory、归档分片、分析 CSV、全部尝试成本与恢复说明，原件留在各自固定发布提交，不复制或重打包已有大文件。

| 模型 | 完整原报告 | 原始 dump 与聚合完整索引 |
| --- | --- | --- |
| Kimi-K3 / GLM-5.3 | [双模型全设置报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md) | [双模型完整索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.md) · [JSON](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/ARCHIVE_INDEX.json) |
| Qwen3.8 | [全设置报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/README.zh.md) | [完整索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/ARCHIVE_INDEX.md) · [JSON](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ff8c572b6a00c33964a00a8fb991fd79dcf900e4/results/qwen38-20260910/report/ARCHIVE_INDEX.json) |
| DeepSeek-V4-Flash-0731 | [全设置报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/README.zh.md) | [完整索引](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/ARCHIVE_INDEX.md) · [JSON](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8c79111de3398d12fb36ba349d8f4266f2330200/results/deepseek-flash-0731-20260911/report/ARCHIVE_INDEX.json) |

Kimi / GLM 的原始数据固定于 `6119f9d136c9ed1f06a7bedd7371be0deb9b5d59`；Qwen 与 DeepSeek 的推荐分析分别为 `analysis/full_v1` 与 `analysis/full_v2`。统一索引明确区分原 collection、逐原件清单、tar 分片、外层 CSV/JSON/报告及本次合报附件；不把 Kimi composite 引用的原包再作为一份新物理副本累计。

存档时应同时保留索引引用的原件清单、分片、外层分析/成本附件和本报告，只有 tar 不足以保存完整研究。按对应历史格式的恢复说明和工具操作；原归档校验通过仅说明内容完整性，不等于重新评分或科学结论被独立证明。Qwen / DeepSeek 的原分析器绑定绝对原件/状态路径，换一个目录下载可以阅读 raw 和 CSV，但不自动得到任意路径重定位后的逐字节重放能力；不要把继承的 hash 声明写成本次重新恢复或重评分。

## 8. 验收记录

本次按仓库 `expgym-runner` 的“冻结输入→全设置汇总→主问题报告→完整索引→一次成稿独立复核→确切增量发布”流程完成报告层工作。验收目标是完整、忠实、可追溯，不是使四模型必须支持相同方向。

验收记录分别覆盖：冻结输入身份与实际矩阵、schema/分母及 unknown 处理、未舍入值生成表格与差值、源文件与本地链接范围、独立成稿数字/逻辑复核，以及本次发布增量扫描和远端提交身份。实际执行的检查、通过与未通过项、修正范围见 [REVIEW.md](REVIEW.md) 和 [VALIDATION.json](VALIDATION.json)；本节不以计划中的检查冒充已通过。

本次报告任务不申请 GPU、不新增模型调用、不重新评分，不恢复、扫描或重打包全部历史 raw/tar。对旧归档复用已有不可变身份；仅本次新增/修改的发布字节进入增量检查。一次有限复核不能证明没有任何逻辑漏洞，原研究已有的性能负向结果、不可评分端点和复现边界均随本报告保留。
