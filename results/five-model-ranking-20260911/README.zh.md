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

| 切片 | 指标 | 预算 | 策略 | items | Kimi-K3 | GLM-5.3 | Qwen3.8 | DeepSeek-0731 | GPT-5.6-sol (medium) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | f1 | free | single | 73 | 0.635911 | 0.651102 | 0.581486 | 0.438134 | 0.640114 |
| all | f1 | moderate | single | 73 | 0.496169 | 0.532761 | 0.509827 | 0.421117 | 0.530600 |
| all | f1 | tight | single | 73 | 0.157561 | 0.192341 | 0.184709 | 0.169184 | 0.155486 |
| whois | f1 | free | single | 39 | 0.658862 | 0.682651 | 0.641102 | 0.498341 | 0.627828 |
| whois | f1 | moderate | single | 39 | 0.573004 | 0.642842 | 0.611283 | 0.497486 | 0.597486 |
| whois | f1 | tight | single | 39 | 0.170136 | 0.230575 | 0.225691 | 0.177828 | 0.170136 |
| whatis | f1 | free | single | 34 | 0.609584 | 0.614914 | 0.513103 | 0.369073 | 0.654206 |
| whatis | f1 | moderate | single | 34 | 0.408034 | 0.406491 | 0.393451 | 0.333516 | 0.453877 |
| whatis | f1 | tight | single | 34 | 0.143137 | 0.148485 | 0.137701 | 0.159269 | 0.138681 |
| all | evidence_acc | free | single | 13 | 0.894419 | 0.684766 | 0.918552 | 0.639517 | 0.704374 |
| all | evidence_acc | moderate | single | 13 | 0.687783 | 0.678733 | 0.749623 | 0.586727 | 0.659125 |
| all | evidence_acc | tight | single | 13 | 0.515837 | 0.502262 | 0.583710 | 0.475113 | 0.541478 |
| all | label_acc | free | single | 13 | 0.926094 | 0.692308 | 0.947210 | 0.668175 | 0.859729 |
| all | label_acc | moderate | single | 13 | 0.853695 | 0.760181 | 0.882353 | 0.755656 | 0.879336 |
| all | label_acc | tight | single | 13 | 0.794872 | 0.736048 | 0.831071 | 0.702866 | 0.787330 |


Moderate 列说明下降发生在哪一段；whois 与 whatis 的拆分保留其不同任务结构。Audit EA 与 LA 分别展示：GLM、DeepSeek 的 LA 在受限档位高于各自 Free，GPT 的 LA 也并非从 Free 经 Moderate 单调下降，因此结论针对证据集合端点，不泛指所有 Audit 指标同步退化。

### 2.2 HPO：全体、三个家族及九个任务

| 切片 | 指标 | 预算 | 策略 | items | Kimi-K3 | GLM-5.3 | Qwen3.8 | DeepSeek-0731 | GPT-5.6-sol (medium) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | gap | free | single | 9 | 98.512910 | 97.911143 | 97.465205 | unknown (20/27) | 97.973235 |
| all | gap | moderate | single | 9 | 94.230104 | 96.154560 | 95.133369 | unknown (25/27) | 96.611095 |
| all | gap | tight | single | 9 | 89.683717 | 86.066889 | 85.709990 | unknown (25/27) | 91.660929 |
| all | raw_perf | free | single | 9 | 0.830424 | 0.829110 | 0.828712 | unknown (20/27) | 0.829635 |
| all | raw_perf | moderate | single | 9 | 0.819970 | 0.824766 | 0.825155 | unknown (25/27) | 0.827481 |
| all | raw_perf | tight | single | 9 | 0.814494 | 0.801956 | 0.806783 | unknown (25/27) | 0.820595 |
| family=paramnet | gap | free | single | 3 | 97.075883 | 96.038788 | 95.282291 | unknown (5/9) | 97.312330 |
| family=paramnet | gap | moderate | single | 3 | 87.756501 | 94.240269 | 94.952694 | unknown (8/9) | 95.271826 |
| family=paramnet | gap | tight | single | 3 | 79.422483 | 79.401892 | 77.865845 | unknown (7/9) | 85.694084 |
| family=paramnet | raw_perf | free | single | 3 | 0.843288 | 0.839029 | 0.839365 | unknown (5/9) | 0.843427 |
| family=paramnet | raw_perf | moderate | single | 3 | 0.818739 | 0.835086 | 0.841848 | unknown (8/9) | 0.840618 |
| family=paramnet | raw_perf | tight | single | 3 | 0.823773 | 0.815296 | 0.817976 | unknown (7/9) | 0.831702 |
| family=nasbench101 | gap | free | single | 3 | 98.692013 | 99.057476 | 98.661766 | unknown (7/9) | 98.377842 |
| family=nasbench101 | gap | moderate | single | 3 | 97.857181 | 97.736559 | 96.510997 | 71.877135 | 98.324002 |
| family=nasbench101 | gap | tight | single | 3 | 94.968099 | 90.761443 | 93.815152 | 86.864351 | 97.030843 |
| family=nasbench101 | raw_perf | free | single | 3 | 0.941770 | 0.943450 | 0.942100 | unknown (7/9) | 0.941206 |
| family=nasbench101 | raw_perf | moderate | single | 3 | 0.937407 | 0.936239 | 0.933920 | 0.711108 | 0.939885 |
| family=nasbench101 | raw_perf | tight | single | 3 | 0.918447 | 0.898441 | 0.914118 | 0.883410 | 0.933223 |
| family=nasbench201 | gap | free | single | 3 | 99.770835 | 98.637164 | 98.451560 | unknown (8/9) | 98.229532 |
| family=nasbench201 | gap | moderate | single | 3 | 97.076629 | 96.486852 | 93.936417 | unknown (8/9) | 96.237458 |
| family=nasbench201 | gap | tight | single | 3 | 94.660569 | 88.037331 | 85.448973 | 76.621201 | 92.257861 |
| family=nasbench201 | raw_perf | free | single | 3 | 0.706212 | 0.704850 | 0.704670 | unknown (8/9) | 0.704273 |
| family=nasbench201 | raw_perf | moderate | single | 3 | 0.703764 | 0.702974 | 0.699696 | unknown (8/9) | 0.701938 |
| family=nasbench201 | raw_perf | tight | single | 3 | 0.701261 | 0.692131 | 0.688255 | 0.679044 | 0.696862 |
| task=hpobench:nasbench101:A | gap | free | single | 1 | 99.258011 | 99.579172 | 99.580753 | unknown (2/3) | 99.436785 |
| task=hpobench:nasbench101:A | gap | moderate | single | 1 | 98.079371 | 99.003299 | 98.190116 | 64.140107 | 98.878317 |
| task=hpobench:nasbench101:A | gap | tight | single | 1 | 90.517091 | 85.756650 | 89.675431 | 90.121573 | 96.614377 |
| task=hpobench:nasbench101:A | raw_perf | free | single | 1 | 0.940861 | 0.943120 | 0.943131 | unknown (2/3) | 0.942118 |
| task=hpobench:nasbench101:A | raw_perf | moderate | single | 1 | 0.932570 | 0.939069 | 0.933349 | 0.612947 | 0.938190 |
| task=hpobench:nasbench101:A | raw_perf | tight | single | 1 | 0.879374 | 0.845887 | 0.873453 | 0.876591 | 0.922265 |
| task=hpobench:nasbench101:B | gap | free | single | 1 | 97.454035 | 97.969343 | 97.113406 | 86.802912 | 96.362283 |
| task=hpobench:nasbench101:B | gap | moderate | single | 1 | 96.585000 | 97.467138 | 92.650329 | 57.666268 | 97.095939 |
| task=hpobench:nasbench101:B | gap | tight | single | 1 | 95.759638 | 89.995192 | 93.270448 | 85.178388 | 95.462681 |
| task=hpobench:nasbench101:B | raw_perf | free | single | 1 | 0.942463 | 0.943777 | 0.941595 | 0.915320 | 0.939681 |
| task=hpobench:nasbench101:B | raw_perf | moderate | single | 1 | 0.940249 | 0.942497 | 0.930222 | 0.609698 | 0.941551 |
| task=hpobench:nasbench101:B | raw_perf | tight | single | 1 | 0.938145 | 0.923455 | 0.931802 | 0.911180 | 0.937389 |
| task=hpobench:nasbench101:C | gap | free | single | 1 | 99.363994 | 99.623912 | 99.291139 | unknown (2/3) | 99.334460 |
| task=hpobench:nasbench101:C | gap | moderate | single | 1 | 98.907173 | 96.739239 | 98.692546 | 93.825030 | 98.997748 |
| task=hpobench:nasbench101:C | gap | tight | single | 1 | 98.627567 | 96.532487 | 98.499576 | 85.293093 | 99.015472 |
| task=hpobench:nasbench101:C | raw_perf | free | single | 1 | 0.941985 | 0.943454 | 0.941573 | unknown (2/3) | 0.941818 |
| task=hpobench:nasbench101:C | raw_perf | moderate | single | 1 | 0.939403 | 0.927150 | 0.938190 | 0.910679 | 0.939915 |
| task=hpobench:nasbench101:C | raw_perf | tight | single | 1 | 0.937823 | 0.925982 | 0.937099 | 0.862458 | 0.940015 |
| task=hpobench:nasbench201:cifar10-valid | gap | free | single | 1 | 100.000000 | 99.391401 | 99.302065 | unknown (2/3) | 99.776661 |
| task=hpobench:nasbench201:cifar10-valid | gap | moderate | single | 1 | 93.657170 | 93.880509 | 93.216075 | 86.130643 | 98.855387 |
| task=hpobench:nasbench201:cifar10-valid | gap | tight | single | 1 | 90.206581 | 93.657170 | 96.460076 | 82.311545 | 97.654940 |
| task=hpobench:nasbench201:cifar10-valid | raw_perf | free | single | 1 | 0.916067 | 0.915582 | 0.915511 | unknown (2/3) | 0.915889 |
| task=hpobench:nasbench201:cifar10-valid | raw_perf | moderate | single | 1 | 0.911018 | 0.911196 | 0.910667 | 0.905027 | 0.915156 |
| task=hpobench:nasbench201:cifar10-valid | raw_perf | tight | single | 1 | 0.908271 | 0.911018 | 0.913249 | 0.901987 | 0.914200 |
| task=hpobench:nasbench201:cifar100 | gap | free | single | 1 | 100.000000 | 99.171863 | 97.652095 | 94.248544 | 98.307325 |
| task=hpobench:nasbench201:cifar100 | gap | moderate | single | 1 | 100.000000 | 99.171863 | 100.000000 | 87.914661 | 94.248544 |
| task=hpobench:nasbench201:cifar100 | gap | tight | single | 1 | 97.479188 | 90.981498 | 90.080558 | 90.990598 | 95.267789 |
| task=hpobench:nasbench201:cifar100 | raw_perf | free | single | 1 | 0.735033 | 0.734022 | 0.732167 | 0.728011 | 0.732967 |
| task=hpobench:nasbench201:cifar100 | raw_perf | moderate | single | 1 | 0.735033 | 0.734022 | 0.735033 | 0.720278 | 0.728011 |
| task=hpobench:nasbench201:cifar100 | raw_perf | tight | single | 1 | 0.731956 | 0.724022 | 0.722922 | 0.724033 | 0.729256 |
| task=hpobench:nasbench201:imagenet16-120 | gap | free | single | 1 | 99.312504 | 97.348228 | 98.400519 | 89.841892 | 96.604610 |
| task=hpobench:nasbench201:imagenet16-120 | gap | moderate | single | 1 | 97.572717 | 96.408183 | 88.593174 | unknown (2/3) | 95.608442 |
| task=hpobench:nasbench201:imagenet16-120 | gap | tight | single | 1 | 96.295938 | 79.473326 | 69.806286 | 56.561461 | 83.850853 |
| task=hpobench:nasbench201:imagenet16-120 | raw_perf | free | single | 1 | 0.467537 | 0.464944 | 0.466333 | 0.455037 | 0.463963 |
| task=hpobench:nasbench201:imagenet16-120 | raw_perf | moderate | single | 1 | 0.465241 | 0.463704 | 0.453389 | unknown (2/3) | 0.462648 |
| task=hpobench:nasbench201:imagenet16-120 | raw_perf | tight | single | 1 | 0.463556 | 0.441352 | 0.428593 | 0.411111 | 0.447130 |
| task=hpobench:paramnet:adult:steps | gap | free | single | 1 | 97.856995 | 95.601586 | 94.590022 | unknown (2/3) | 97.939423 |
| task=hpobench:paramnet:adult:steps | gap | moderate | single | 1 | 87.329255 | 95.414265 | 91.982442 | 87.366726 | 90.925923 |
| task=hpobench:paramnet:adult:steps | gap | tight | single | 1 | 77.355993 | 72.013444 | 76.921396 | unknown (2/3) | 72.013444 |
| task=hpobench:paramnet:adult:steps | raw_perf | free | single | 1 | 0.852849 | 0.851920 | 0.851503 | unknown (2/3) | 0.852883 |
| task=hpobench:paramnet:adult:steps | raw_perf | moderate | single | 1 | 0.848512 | 0.851843 | 0.850429 | 0.848528 | 0.849994 |
| task=hpobench:paramnet:adult:steps | raw_perf | tight | single | 1 | 0.844404 | 0.842204 | 0.844225 | unknown (2/3) | 0.842204 |
| task=hpobench:paramnet:higgs:steps | gap | free | single | 1 | 94.148953 | 95.829008 | 93.995253 | unknown (2/3) | 94.813201 |
| task=hpobench:paramnet:higgs:steps | gap | moderate | single | 1 | 89.082285 | 92.269269 | 93.989956 | 92.657927 | 97.146907 |
| task=hpobench:paramnet:higgs:steps | gap | tight | single | 1 | 66.679766 | 78.314729 | 65.533231 | unknown (2/3) | 89.704134 |
| task=hpobench:paramnet:higgs:steps | raw_perf | free | single | 1 | 0.715973 | 0.717435 | 0.715839 | unknown (2/3) | 0.716551 |
| task=hpobench:paramnet:higgs:steps | raw_perf | moderate | single | 1 | 0.711564 | 0.714337 | 0.715835 | 0.714676 | 0.718582 |
| task=hpobench:paramnet:higgs:steps | raw_perf | tight | single | 1 | 0.692066 | 0.702193 | 0.691069 | unknown (2/3) | 0.712105 |
| task=hpobench:paramnet:letter:steps | gap | free | single | 1 | 99.221702 | 96.685771 | 97.261597 | unknown (1/3) | 99.184367 |
| task=hpobench:paramnet:letter:steps | gap | moderate | single | 1 | 86.857961 | 95.037272 | 98.885684 | unknown (2/3) | 97.742648 |
| task=hpobench:paramnet:letter:steps | gap | tight | single | 1 | 94.231691 | 87.877503 | 91.142909 | 82.366233 | 95.364674 |
| task=hpobench:paramnet:letter:steps | raw_perf | free | single | 1 | 0.961043 | 0.947731 | 0.950754 | unknown (1/3) | 0.960847 |
| task=hpobench:paramnet:letter:steps | raw_perf | moderate | single | 1 | 0.896141 | 0.939077 | 0.959279 | unknown (2/3) | 0.953279 |
| task=hpobench:paramnet:letter:steps | raw_perf | tight | single | 1 | 0.934848 | 0.901493 | 0.918634 | 0.872561 | 0.940796 |


HPO 总体下降不代表每项任务、每个 block 都下降，也不说明同一个模型在三个家族中均最优。DeepSeek Exp tuning 为70/81可评分，Free20/27、Moderate与Tight各25/27；完整九任务均值保持 unknown，不拿不同可评分子集均值之差补成总体趋势。第4章排名仅使用相应范围内三档完整的固定候选集，并明确排除的缺失模型。

### 2.3 HPO：三个 seed blocks

| 模型 | 预算 | 策略 | 指标 | 2200 | 2204 | 2208 | 三块均值 | 描述 SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi-K3 | free | single | gap | 98.323337 | 98.022659 | 99.192735 | 98.512910 | 0.607637 |
| Kimi-K3 | free | single | raw_perf | 0.830364 | 0.830405 | 0.830501 | 0.830424 | 0.000070 |
| Kimi-K3 | moderate | single | gap | 91.888380 | 96.720920 | 94.081011 | 94.230104 | 2.419717 |
| Kimi-K3 | moderate | single | raw_perf | 0.809523 | 0.829398 | 0.820988 | 0.819970 | 0.009977 |
| Kimi-K3 | tight | single | gap | 94.484532 | 84.994278 | 89.572341 | 89.683717 | 4.746108 |
| Kimi-K3 | tight | single | raw_perf | 0.815959 | 0.810399 | 0.817122 | 0.814494 | 0.003593 |
| GLM-5.3 | free | single | gap | 97.433902 | 97.962348 | 98.337178 | 97.911143 | 0.453810 |
| GLM-5.3 | free | single | raw_perf | 0.825708 | 0.830673 | 0.830947 | 0.829110 | 0.002949 |
| GLM-5.3 | moderate | single | gap | 94.984465 | 98.060230 | 95.418984 | 96.154560 | 1.664598 |
| GLM-5.3 | moderate | single | raw_perf | 0.823852 | 0.825649 | 0.824797 | 0.824766 | 0.000899 |
| GLM-5.3 | tight | single | gap | 86.858680 | 88.946705 | 82.395281 | 86.066889 | 3.346713 |
| GLM-5.3 | tight | single | raw_perf | 0.801129 | 0.807389 | 0.797350 | 0.801956 | 0.005070 |
| Qwen3.8 | free | single | gap | 97.218451 | 97.423743 | 97.753422 | 97.465205 | 0.269885 |
| Qwen3.8 | free | single | raw_perf | 0.829311 | 0.827017 | 0.829808 | 0.828712 | 0.001489 |
| Qwen3.8 | moderate | single | gap | 96.950300 | 95.573292 | 92.876516 | 95.133369 | 2.072216 |
| Qwen3.8 | moderate | single | raw_perf | 0.827805 | 0.825213 | 0.822446 | 0.825155 | 0.002680 |
| Qwen3.8 | tight | single | gap | 86.407961 | 85.139476 | 85.582533 | 85.709990 | 0.643776 |
| Qwen3.8 | tight | single | raw_perf | 0.813929 | 0.800823 | 0.805597 | 0.806783 | 0.006633 |
| DeepSeek-0731 | free | single | gap | unknown (8/9) | unknown (7/9) | unknown (5/9) | unknown (20/27) | unknown |
| DeepSeek-0731 | free | single | raw_perf | unknown (8/9) | unknown (7/9) | unknown (5/9) | unknown (20/27) | unknown |
| DeepSeek-0731 | moderate | single | gap | 82.417808 | unknown (8/9) | unknown (8/9) | unknown (25/27) | unknown |
| DeepSeek-0731 | moderate | single | raw_perf | 0.713211 | unknown (8/9) | unknown (8/9) | unknown (25/27) | unknown |
| DeepSeek-0731 | tight | single | gap | 84.428658 | 82.732146 | unknown (7/9) | unknown (25/27) | unknown |
| DeepSeek-0731 | tight | single | raw_perf | 0.798632 | 0.799665 | unknown (7/9) | unknown (25/27) | unknown |
| GPT-5.6-sol (medium) | free | single | gap | 98.220952 | 97.928277 | 97.770475 | 97.973235 | 0.228579 |
| GPT-5.6-sol (medium) | free | single | raw_perf | 0.829992 | 0.829713 | 0.829200 | 0.829635 | 0.000402 |
| GPT-5.6-sol (medium) | moderate | single | gap | 97.392597 | 95.988893 | 96.451795 | 96.611095 | 0.715282 |
| GPT-5.6-sol (medium) | moderate | single | raw_perf | 0.828783 | 0.826499 | 0.827159 | 0.827481 | 0.001175 |
| GPT-5.6-sol (medium) | tight | single | gap | 90.833567 | 92.132295 | 92.016927 | 91.660929 | 0.718835 |
| GPT-5.6-sol (medium) | tight | single | raw_perf | 0.818542 | 0.822705 | 0.820538 | 0.820595 | 0.002082 |


三个 blocks 的 SD 描述固定任务上的重复层变化，不是标准误或模型独立生成证明。完整任务、raw/Gap与unknown见 [REPEATS.md](REPEATS.md) 及 [by_outerseed.csv](by_outerseed.csv)。

## 3. 主问题二：缓存复用与 PoolAct 协调改善了什么？

以下对照固定同一模型、相同档位与N=4。cached−naive 是观察复用的描述性差异，poolact−cached 是进一步协调的差异，poolact−naive 为整体方法对照。相同反馈预算不等于相同 token 或实际推理时长，三组对照同时展示。

Kimi、GLM、Qwen 的 Search F1-MV、Audit EA-MV、NAS Gap-MI 在两档共六组主要展示端点上均有正的 poolact−naive；GPT 为四组正向、Moderate Search一组负向、Moderate NAS一组unknown；DeepSeek只有Tight Search主端点正向、Moderate Search与两档Audit负向、NAS完整对照unknown。改善的稳定范围需要从完整设置中读出，不能仅数有利切片。

| 模型 | 预算 | 指标 | cached − naive | poolact − cached | poolact − naive |
| --- | --- | --- | --- | --- | --- |
| Kimi-K3 | moderate | f1_mv | -0.003885 | +0.025375 | +0.021490 |
| Kimi-K3 | moderate | evidence_acc_mv | +0.027149 | +0.171946 | +0.199095 |
| Kimi-K3 | moderate | label_acc_mv | +0.013575 | +0.036199 | +0.049774 |
| Kimi-K3 | moderate | gap_mi | -0.077726 | +0.595188 | +0.517462 |
| Kimi-K3 | moderate | gap_bon | -0.147632 | +0.031723 | -0.115908 |
| Kimi-K3 | tight | f1_mv | -0.025641 | +0.117094 | +0.091453 |
| Kimi-K3 | tight | evidence_acc_mv | -0.004525 | +0.081448 | +0.076923 |
| Kimi-K3 | tight | label_acc_mv | -0.004525 | +0.036199 | +0.031674 |
| Kimi-K3 | tight | gap_mi | -0.146798 | +1.940211 | +1.793413 |
| Kimi-K3 | tight | gap_bon | +0.373105 | -0.001140 | +0.371965 |
| GLM-5.3 | moderate | f1_mv | +0.036447 | +0.000694 | +0.037141 |
| GLM-5.3 | moderate | evidence_acc_mv | +0.036199 | +0.131222 | +0.167421 |
| GLM-5.3 | moderate | label_acc_mv | +0.009050 | +0.045249 | +0.054299 |
| GLM-5.3 | moderate | gap_mi | +0.188003 | +0.904495 | +1.092498 |
| GLM-5.3 | moderate | gap_bon | +0.108255 | +0.264798 | +0.373053 |
| GLM-5.3 | tight | f1_mv | +0.000000 | +0.091453 | +0.091453 |
| GLM-5.3 | tight | evidence_acc_mv | +0.013575 | +0.090498 | +0.104072 |
| GLM-5.3 | tight | label_acc_mv | +0.022624 | +0.013575 | +0.036199 |
| GLM-5.3 | tight | gap_mi | +2.222250 | +9.994021 | +12.216271 |
| GLM-5.3 | tight | gap_bon | +0.739115 | +3.914245 | +4.653360 |
| Qwen3.8 | moderate | f1_mv | -0.000407 | +0.023118 | +0.022711 |
| Qwen3.8 | moderate | evidence_acc_mv | +0.058824 | +0.190045 | +0.248869 |
| Qwen3.8 | moderate | label_acc_mv | -0.009050 | +0.067873 | +0.058824 |
| Qwen3.8 | moderate | gap_mi | +0.800382 | +1.146151 | +1.946533 |
| Qwen3.8 | moderate | gap_bon | +0.302657 | +0.144411 | +0.447068 |
| Qwen3.8 | tight | f1_mv | +0.050183 | -0.026252 | +0.023932 |
| Qwen3.8 | tight | evidence_acc_mv | +0.040724 | +0.036199 | +0.076923 |
| Qwen3.8 | tight | label_acc_mv | +0.004525 | +0.018100 | +0.022624 |
| Qwen3.8 | tight | gap_mi | +0.136512 | +5.513071 | +5.649583 |
| Qwen3.8 | tight | gap_bon | -0.373878 | +0.140699 | -0.233179 |
| DeepSeek-0731 | moderate | f1_mv | +0.038462 | -0.051282 | -0.012821 |
| DeepSeek-0731 | moderate | evidence_acc_mv | -0.004525 | -0.253394 | -0.257919 |
| DeepSeek-0731 | moderate | label_acc_mv | -0.049774 | -0.289593 | -0.339367 |
| DeepSeek-0731 | moderate | gap_mi | unknown (1/9) | unknown (0/9) | unknown (0/9) |
| DeepSeek-0731 | moderate | gap_bon | unknown (1/9) | unknown (0/9) | unknown (0/9) |
| DeepSeek-0731 | tight | f1_mv | +0.017094 | +0.031674 | +0.048768 |
| DeepSeek-0731 | tight | evidence_acc_mv | -0.126697 | -0.303167 | -0.429864 |
| DeepSeek-0731 | tight | label_acc_mv | -0.190045 | -0.371041 | -0.561086 |
| DeepSeek-0731 | tight | gap_mi | unknown (0/9) | unknown (0/9) | unknown (1/9) |
| DeepSeek-0731 | tight | gap_bon | unknown (0/9) | unknown (0/9) | unknown (1/9) |
| GPT-5.6-sol (medium) | moderate | f1_mv | +0.014652 | -0.031746 | -0.017094 |
| GPT-5.6-sol (medium) | moderate | evidence_acc_mv | +0.004525 | +0.022624 | +0.027149 |
| GPT-5.6-sol (medium) | moderate | label_acc_mv | +0.036199 | -0.009050 | +0.027149 |
| GPT-5.6-sol (medium) | moderate | gap_mi | +0.068257 | unknown (8/9) | unknown (8/9) |
| GPT-5.6-sol (medium) | moderate | gap_bon | +0.095875 | unknown (8/9) | unknown (8/9) |
| GPT-5.6-sol (medium) | tight | f1_mv | +0.011255 | +0.016095 | +0.027350 |
| GPT-5.6-sol (medium) | tight | evidence_acc_mv | +0.072398 | +0.036199 | +0.108597 |
| GPT-5.6-sol (medium) | tight | label_acc_mv | +0.045249 | +0.022624 | +0.067873 |
| GPT-5.6-sol (medium) | tight | gap_mi | -0.591553 | +1.221249 | +0.629696 |
| GPT-5.6-sol (medium) | tight | gap_bon | +0.103880 | -0.217912 | -0.114031 |


### 3.1 Search：Tight 改善跨五模型出现

| 切片 | 指标 | 预算 | 策略 | items | Kimi-K3 | GLM-5.3 | Qwen3.8 | DeepSeek-0731 | GPT-5.6-sol (medium) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | f1_mi | moderate | naive | 39 | 0.623870 | 0.599406 | 0.588896 | 0.090769 | 0.613970 |
| all | f1_mi | moderate | cached | 39 | 0.632024 | 0.620111 | 0.590689 | 0.169872 | 0.626424 |
| all | f1_mi | moderate | poolact | 39 | 0.640914 | 0.659089 | 0.623277 | 0.079060 | 0.577492 |
| all | f1_mi | tight | naive | 39 | 0.201002 | 0.203255 | 0.185520 | 0.025641 | 0.195777 |
| all | f1_mi | tight | cached | 39 | 0.192511 | 0.203255 | 0.223102 | 0.047009 | 0.192547 |
| all | f1_mi | tight | poolact | 39 | 0.272395 | 0.247425 | 0.226900 | 0.054927 | 0.238499 |
| all | f1_mv | moderate | naive | 39 | 0.645919 | 0.620278 | 0.612138 | 0.132479 | 0.623127 |
| all | f1_mv | moderate | cached | 39 | 0.642034 | 0.656725 | 0.611731 | 0.170940 | 0.637779 |
| all | f1_mv | moderate | poolact | 39 | 0.667409 | 0.657419 | 0.634849 | 0.119658 | 0.606033 |
| all | f1_mv | tight | naive | 39 | 0.212871 | 0.208597 | 0.182956 | 0.025641 | 0.191503 |
| all | f1_mv | tight | cached | 39 | 0.187230 | 0.208597 | 0.233139 | 0.042735 | 0.202759 |
| all | f1_mv | tight | poolact | 39 | 0.304324 | 0.300050 | 0.206888 | 0.074409 | 0.218854 |


Tight Search 的投票F1在五模型上均高于各自naive，是PoolAct结果中最一致的跨模型方向。但Qwen的Tight投票结果仍低于cached；GPT与DeepSeek的Moderate投票结果均低于naive和cached。因而“相对naive改善”与“协调优于仅缓存”是不同主张，二者必须分别核对。

### 3.2 Audit：证据与标签，成员平均与投票分别报告

| 切片 | 指标 | 预算 | 策略 | items | Kimi-K3 | GLM-5.3 | Qwen3.8 | DeepSeek-0731 | GPT-5.6-sol (medium) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | evidence_acc_mi | moderate | naive | 13 | 0.702489 | 0.654977 | 0.676471 | 0.322398 | 0.636878 |
| all | evidence_acc_mi | moderate | cached | 13 | 0.670814 | 0.668552 | 0.712670 | 0.364253 | 0.569005 |
| all | evidence_acc_mi | moderate | poolact | 13 | 0.908371 | 0.802036 | 0.924208 | 0.109729 | 0.593891 |
| all | evidence_acc_mi | tight | naive | 13 | 0.545249 | 0.549774 | 0.552036 | 0.185520 | 0.497738 |
| all | evidence_acc_mi | tight | cached | 13 | 0.542986 | 0.585973 | 0.590498 | 0.128959 | 0.523756 |
| all | evidence_acc_mi | tight | poolact | 13 | 0.602941 | 0.607466 | 0.632353 | 0.016968 | 0.591629 |
| all | evidence_acc_mv | moderate | naive | 13 | 0.737557 | 0.809955 | 0.687783 | 0.592760 | 0.647059 |
| all | evidence_acc_mv | moderate | cached | 13 | 0.764706 | 0.846154 | 0.746606 | 0.588235 | 0.651584 |
| all | evidence_acc_mv | moderate | poolact | 13 | 0.936652 | 0.977376 | 0.936652 | 0.334842 | 0.674208 |
| all | evidence_acc_mv | tight | naive | 13 | 0.552036 | 0.588235 | 0.561086 | 0.497738 | 0.515837 |
| all | evidence_acc_mv | tight | cached | 13 | 0.547511 | 0.601810 | 0.601810 | 0.371041 | 0.588235 |
| all | evidence_acc_mv | tight | poolact | 13 | 0.628959 | 0.692308 | 0.638009 | 0.067873 | 0.624434 |
| all | label_acc_mi | moderate | naive | 13 | 0.894796 | 0.757919 | 0.890271 | 0.400452 | 0.843891 |
| all | label_acc_mi | moderate | cached | 13 | 0.840498 | 0.753394 | 0.891403 | 0.447964 | 0.786199 |
| all | label_acc_mi | moderate | poolact | 13 | 0.928733 | 0.808824 | 0.953620 | 0.149321 | 0.781674 |
| all | label_acc_mi | tight | naive | 13 | 0.822398 | 0.792986 | 0.816742 | 0.236425 | 0.772624 |
| all | label_acc_mi | tight | cached | 13 | 0.811086 | 0.869910 | 0.837104 | 0.171946 | 0.756787 |
| all | label_acc_mi | tight | poolact | 13 | 0.846154 | 0.798643 | 0.854072 | 0.032805 | 0.828054 |
| all | label_acc_mv | moderate | naive | 13 | 0.923077 | 0.927602 | 0.900452 | 0.787330 | 0.841629 |
| all | label_acc_mv | moderate | cached | 13 | 0.936652 | 0.936652 | 0.891403 | 0.737557 | 0.877828 |
| all | label_acc_mv | moderate | poolact | 13 | 0.972851 | 0.981900 | 0.959276 | 0.447964 | 0.868778 |
| all | label_acc_mv | tight | naive | 13 | 0.841629 | 0.868778 | 0.832579 | 0.692308 | 0.791855 |
| all | label_acc_mv | tight | cached | 13 | 0.837104 | 0.891403 | 0.837104 | 0.502262 | 0.837104 |
| all | label_acc_mv | tight | poolact | 13 | 0.873303 | 0.904977 | 0.855204 | 0.131222 | 0.859729 |


Kimi、GLM、Qwen、GPT在两档Audit的EA-MV均有poolact−naive改善，DeepSeek则在两档EA-MV和LA-MV均更低。GPT Moderate中投票EA改善也不能替代成员平均EA的变化；表中MI/MV和EA/LA始终保留，避免把不同端点合并成一个笼统“更好”。

### 3.3 NAS：MI 与 best-of-4 不互换

| 切片 | 指标 | 预算 | 策略 | items | Kimi-K3 | GLM-5.3 | Qwen3.8 | DeepSeek-0731 | GPT-5.6-sol (medium) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | gap_mi | moderate | naive | 3 | 98.038866 | 97.873330 | 96.922951 | unknown (1/9) | 98.211271 |
| all | gap_mi | moderate | cached | 3 | 97.961140 | 98.061333 | 97.723333 | unknown (3/9) | 98.279528 |
| all | gap_mi | moderate | poolact | 3 | 98.556328 | 98.965828 | 98.869484 | unknown (1/9) | unknown (8/9) |
| all | gap_mi | tight | naive | 3 | 94.258262 | 83.960328 | 90.621090 | unknown (2/9) | 96.641015 |
| all | gap_mi | tight | cached | 3 | 94.111464 | 86.182578 | 90.757603 | unknown (1/9) | 96.049462 |
| all | gap_mi | tight | poolact | 3 | 96.051676 | 96.176599 | 96.270673 | unknown (2/9) | 97.270712 |
| all | gap_bon | moderate | naive | 3 | 98.986955 | 99.007686 | 98.700872 | unknown (1/9) | 98.703210 |
| all | gap_bon | moderate | cached | 3 | 98.839323 | 99.115941 | 99.003529 | unknown (3/9) | 98.799085 |
| all | gap_bon | moderate | poolact | 3 | 98.871046 | 99.380739 | 99.147940 | unknown (1/9) | unknown (8/9) |
| all | gap_bon | tight | naive | 3 | 97.993150 | 93.809666 | 98.524288 | unknown (2/9) | 98.196592 |
| all | gap_bon | tight | cached | 3 | 98.366255 | 94.548781 | 98.150410 | unknown (1/9) | 98.300473 |
| all | gap_bon | tight | poolact | 3 | 98.365115 | 98.463026 | 98.291108 | unknown (2/9) | 98.082561 |
| all | raw_perf_mi | moderate | naive | 3 | 0.938288 | 0.937173 | 0.933885 | unknown (1/9) | 0.939797 |
| all | raw_perf_mi | moderate | cached | 3 | 0.937575 | 0.938197 | 0.937188 | unknown (3/9) | 0.940138 |
| all | raw_perf_mi | moderate | poolact | 3 | 0.941256 | 0.942421 | 0.942661 | unknown (1/9) | unknown (8/9) |
| all | raw_perf_mi | tight | naive | 3 | 0.919430 | 0.880532 | 0.891752 | unknown (2/9) | 0.931537 |
| all | raw_perf_mi | tight | cached | 3 | 0.916669 | 0.888600 | 0.899698 | unknown (1/9) | 0.932405 |
| all | raw_perf_mi | tight | poolact | 3 | 0.929105 | 0.928628 | 0.930763 | unknown (2/9) | 0.935207 |
| all | raw_perf_bon | moderate | naive | 3 | 0.943153 | 0.942712 | 0.942059 | unknown (1/9) | 0.942089 |
| all | raw_perf_bon | moderate | cached | 3 | 0.942315 | 0.943324 | 0.942916 | unknown (3/9) | 0.942467 |
| all | raw_perf_bon | moderate | poolact | 3 | 0.942805 | 0.944478 | 0.943754 | unknown (1/9) | unknown (8/9) |
| all | raw_perf_bon | tight | naive | 3 | 0.938976 | 0.920903 | 0.941273 | unknown (2/9) | 0.940141 |
| all | raw_perf_bon | tight | cached | 3 | 0.940167 | 0.923040 | 0.937934 | unknown (1/9) | 0.940479 |
| all | raw_perf_bon | tight | poolact | 3 | 0.939919 | 0.941020 | 0.938869 | unknown (2/9) | 0.939629 |
| task=hpobench:nasbench101:A | gap_mi | moderate | naive | 1 | 98.287414 | 97.771660 | 97.396710 | unknown (1/3) | 98.881085 |
| task=hpobench:nasbench101:A | gap_mi | moderate | cached | 1 | 97.813188 | 97.880822 | 98.339226 | unknown (2/3) | 98.922218 |
| task=hpobench:nasbench101:A | gap_mi | moderate | poolact | 1 | 99.263154 | 98.993806 | 99.282534 | unknown (1/3) | 98.567044 |
| task=hpobench:nasbench101:A | gap_mi | tight | naive | 1 | 93.427698 | 88.907337 | 85.565821 | unknown (1/3) | 97.165728 |
| task=hpobench:nasbench101:A | gap_mi | tight | cached | 1 | 91.237326 | 87.932388 | 86.153354 | unknown (1/3) | 97.922747 |
| task=hpobench:nasbench101:A | gap_mi | tight | poolact | 1 | 95.504557 | 95.258942 | 96.669354 | unknown (1/3) | 97.871330 |
| task=hpobench:nasbench101:A | gap_bon | moderate | naive | 1 | 99.319713 | 99.215297 | 99.267504 | unknown (1/3) | 99.224789 |
| task=hpobench:nasbench101:A | gap_bon | moderate | cached | 1 | 99.134610 | 99.049178 | 99.356101 | unknown (2/3) | 99.281743 |
| task=hpobench:nasbench101:A | gap_bon | moderate | poolact | 1 | 99.621889 | 99.520635 | 99.433620 | unknown (1/3) | 99.178907 |
| task=hpobench:nasbench101:A | gap_bon | tight | naive | 1 | 98.807122 | 94.397901 | 99.216879 | unknown (1/3) | 99.310220 |
| task=hpobench:nasbench101:A | gap_bon | tight | cached | 1 | 98.864077 | 94.459601 | 97.753465 | unknown (1/3) | 99.131447 |
| task=hpobench:nasbench101:A | gap_bon | tight | poolact | 1 | 98.691632 | 99.224789 | 98.281876 | unknown (1/3) | 99.107715 |
| task=hpobench:nasbench101:A | raw_perf_mi | moderate | naive | 1 | 0.934033 | 0.930405 | 0.927768 | unknown (1/3) | 0.938209 |
| task=hpobench:nasbench101:A | raw_perf_mi | moderate | cached | 1 | 0.930697 | 0.931173 | 0.934398 | unknown (2/3) | 0.938499 |
| task=hpobench:nasbench101:A | raw_perf_mi | moderate | poolact | 1 | 0.940897 | 0.939002 | 0.941033 | unknown (1/3) | 0.936000 |
| task=hpobench:nasbench101:A | raw_perf_mi | tight | naive | 1 | 0.899848 | 0.868050 | 0.824324 | unknown (1/3) | 0.926143 |
| task=hpobench:nasbench101:A | raw_perf_mi | tight | cached | 1 | 0.884440 | 0.861192 | 0.848677 | unknown (1/3) | 0.931468 |
| task=hpobench:nasbench101:A | raw_perf_mi | tight | poolact | 1 | 0.914458 | 0.912730 | 0.922651 | unknown (1/3) | 0.931106 |
| task=hpobench:nasbench101:A | raw_perf_bon | moderate | naive | 1 | 0.941295 | 0.940560 | 0.940928 | unknown (1/3) | 0.940627 |
| task=hpobench:nasbench101:A | raw_perf_bon | moderate | cached | 1 | 0.939993 | 0.939392 | 0.941551 | unknown (2/3) | 0.941028 |
| task=hpobench:nasbench101:A | raw_perf_bon | moderate | poolact | 1 | 0.943421 | 0.942708 | 0.942096 | unknown (1/3) | 0.940304 |
| task=hpobench:nasbench101:A | raw_perf_bon | tight | naive | 1 | 0.937689 | 0.906673 | 0.940572 | unknown (1/3) | 0.941228 |
| task=hpobench:nasbench101:A | raw_perf_bon | tight | cached | 1 | 0.938090 | 0.907107 | 0.930277 | unknown (1/3) | 0.939971 |
| task=hpobench:nasbench101:A | raw_perf_bon | tight | poolact | 1 | 0.936877 | 0.940627 | 0.933994 | unknown (1/3) | 0.939804 |
| task=hpobench:nasbench101:B | gap_mi | moderate | naive | 1 | 96.818635 | 96.762956 | 94.581638 | unknown (0/3) | 96.566441 |
| task=hpobench:nasbench101:B | gap_mi | moderate | cached | 1 | 96.872130 | 96.848113 | 96.181054 | unknown (0/3) | 96.628671 |
| task=hpobench:nasbench101:B | gap_mi | moderate | poolact | 1 | 97.211667 | 98.202974 | 97.573035 | unknown (0/3) | 97.868900 |
| task=hpobench:nasbench101:B | gap_mi | tight | naive | 1 | 92.227822 | 71.553333 | 89.094498 | unknown (1/3) | 95.208303 |
| task=hpobench:nasbench101:B | gap_mi | tight | cached | 1 | 93.119782 | 75.460710 | 88.936192 | unknown (0/3) | 91.474515 |
| task=hpobench:nasbench101:B | gap_mi | tight | poolact | 1 | 93.599063 | 94.632951 | 93.711513 | unknown (1/3) | 95.414644 |
| task=hpobench:nasbench101:B | gap_bon | moderate | naive | 1 | 97.755357 | 98.248830 | 97.226954 | unknown (0/3) | 97.192013 |
| task=hpobench:nasbench101:B | gap_bon | moderate | cached | 1 | 97.676749 | 98.174594 | 98.091617 | unknown (0/3) | 97.375427 |
| task=hpobench:nasbench101:B | gap_bon | moderate | poolact | 1 | 97.593781 | 98.716097 | 98.104715 | unknown (0/3) | 98.104718 |
| task=hpobench:nasbench101:B | gap_bon | tight | naive | 1 | 96.135197 | 88.785528 | 96.999865 | unknown (1/3) | 96.344816 |
| task=hpobench:nasbench101:B | gap_bon | tight | cached | 1 | 97.047906 | 90.785619 | 97.532642 | unknown (0/3) | 96.506398 |
| task=hpobench:nasbench101:B | gap_bon | tight | poolact | 1 | 97.205119 | 96.912531 | 97.633082 | unknown (1/3) | 96.126465 |
| task=hpobench:nasbench101:B | raw_perf_mi | moderate | naive | 1 | 0.940844 | 0.940702 | 0.935143 | unknown (0/3) | 0.940202 |
| task=hpobench:nasbench101:B | raw_perf_mi | moderate | cached | 1 | 0.940981 | 0.940919 | 0.939219 | unknown (0/3) | 0.940360 |
| task=hpobench:nasbench101:B | raw_perf_mi | moderate | poolact | 1 | 0.941846 | 0.944372 | 0.942767 | unknown (0/3) | 0.943521 |
| task=hpobench:nasbench101:B | raw_perf_mi | tight | naive | 1 | 0.929145 | 0.876458 | 0.921160 | unknown (1/3) | 0.936740 |
| task=hpobench:nasbench101:B | raw_perf_mi | tight | cached | 1 | 0.931418 | 0.886415 | 0.920757 | unknown (0/3) | 0.927225 |
| task=hpobench:nasbench101:B | raw_perf_mi | tight | poolact | 1 | 0.932639 | 0.935274 | 0.932926 | unknown (1/3) | 0.937266 |
| task=hpobench:nasbench101:B | raw_perf_bon | moderate | naive | 1 | 0.943231 | 0.944489 | 0.941885 | unknown (0/3) | 0.941796 |
| task=hpobench:nasbench101:B | raw_perf_bon | moderate | cached | 1 | 0.943031 | 0.944300 | 0.944088 | unknown (0/3) | 0.942263 |
| task=hpobench:nasbench101:B | raw_perf_bon | moderate | poolact | 1 | 0.942820 | 0.945680 | 0.944122 | unknown (0/3) | 0.944122 |
| task=hpobench:nasbench101:B | raw_perf_bon | tight | naive | 1 | 0.939103 | 0.920373 | 0.941306 | unknown (1/3) | 0.939637 |
| task=hpobench:nasbench101:B | raw_perf_bon | tight | cached | 1 | 0.941429 | 0.925470 | 0.942664 | unknown (0/3) | 0.940049 |
| task=hpobench:nasbench101:B | raw_perf_bon | tight | poolact | 1 | 0.941829 | 0.941084 | 0.942920 | unknown (1/3) | 0.939080 |
| task=hpobench:nasbench101:C | gap_mi | moderate | naive | 1 | 99.010548 | 99.085373 | 98.790506 | unknown (0/3) | 99.186287 |
| task=hpobench:nasbench101:C | gap_mi | moderate | cached | 1 | 99.198101 | 99.455064 | 98.649719 | unknown (1/3) | 99.287694 |
| task=hpobench:nasbench101:C | gap_mi | moderate | poolact | 1 | 99.194164 | 99.700703 | 99.752884 | unknown (0/3) | unknown (2/3) |
| task=hpobench:nasbench101:C | gap_mi | tight | naive | 1 | 97.119267 | 91.420315 | 97.202952 | unknown (0/3) | 97.549015 |
| task=hpobench:nasbench101:C | gap_mi | tight | cached | 1 | 97.977285 | 95.154636 | 97.183262 | unknown (0/3) | 98.751125 |
| task=hpobench:nasbench101:C | gap_mi | tight | poolact | 1 | 99.051407 | 98.637904 | 98.431153 | unknown (0/3) | 98.526160 |
| task=hpobench:nasbench101:C | gap_bon | moderate | naive | 1 | 99.885793 | 99.558932 | 99.608158 | unknown (0/3) | 99.692829 |
| task=hpobench:nasbench101:C | gap_bon | moderate | cached | 1 | 99.706609 | 100.124052 | 99.562870 | unknown (1/3) | 99.740087 |
| task=hpobench:nasbench101:C | gap_bon | moderate | poolact | 1 | 99.397468 | 99.905485 | 99.905485 | unknown (0/3) | unknown (2/3) |
| task=hpobench:nasbench101:C | gap_bon | tight | naive | 1 | 99.037133 | 98.245569 | 99.356119 | unknown (0/3) | 98.934741 |
| task=hpobench:nasbench101:C | gap_bon | tight | cached | 1 | 99.186781 | 98.401123 | 99.165121 | unknown (0/3) | 99.263573 |
| task=hpobench:nasbench101:C | gap_bon | tight | poolact | 1 | 99.198595 | 99.251758 | 98.958368 | unknown (0/3) | 99.013503 |
| task=hpobench:nasbench101:C | raw_perf_mi | moderate | naive | 1 | 0.939987 | 0.940410 | 0.938744 | unknown (0/3) | 0.940981 |
| task=hpobench:nasbench101:C | raw_perf_mi | moderate | cached | 1 | 0.941047 | 0.942500 | 0.937948 | unknown (1/3) | 0.941554 |
| task=hpobench:nasbench101:C | raw_perf_mi | moderate | poolact | 1 | 0.941025 | 0.943888 | 0.944183 | unknown (0/3) | unknown (2/3) |
| task=hpobench:nasbench101:C | raw_perf_mi | tight | naive | 1 | 0.929298 | 0.897088 | 0.929771 | unknown (0/3) | 0.931727 |
| task=hpobench:nasbench101:C | raw_perf_mi | tight | cached | 1 | 0.934147 | 0.918194 | 0.929660 | unknown (0/3) | 0.938521 |
| task=hpobench:nasbench101:C | raw_perf_mi | tight | poolact | 1 | 0.940218 | 0.937881 | 0.936713 | unknown (0/3) | 0.937250 |
| task=hpobench:nasbench101:C | raw_perf_bon | moderate | naive | 1 | 0.944934 | 0.943087 | 0.943365 | unknown (0/3) | 0.943843 |
| task=hpobench:nasbench101:C | raw_perf_bon | moderate | cached | 1 | 0.943921 | 0.946281 | 0.943109 | unknown (1/3) | 0.944111 |
| task=hpobench:nasbench101:C | raw_perf_bon | moderate | poolact | 1 | 0.942174 | 0.945045 | 0.945045 | unknown (0/3) | unknown (2/3) |
| task=hpobench:nasbench101:C | raw_perf_bon | tight | naive | 1 | 0.940138 | 0.935664 | 0.941940 | unknown (0/3) | 0.939559 |
| task=hpobench:nasbench101:C | raw_perf_bon | tight | cached | 1 | 0.940983 | 0.936543 | 0.940861 | unknown (0/3) | 0.941417 |
| task=hpobench:nasbench101:C | raw_perf_bon | tight | poolact | 1 | 0.941050 | 0.941351 | 0.939692 | unknown (0/3) | 0.940004 |


Kimi、GLM、Qwen的两个预算档位Gap-MI均优于naive。GPT Tight也有MI改善，但其BoN不随MI同向改善；成员整体水平与最佳候选质量不是同一个端点。

GPT Moderate poolact的一个NAS池中，一成员在本地近似context cap处停止、缺最终配置，因此该设置完整MI/BoN与涉及它的完整对照均为unknown，只有8/9完整池；不能用已知8池的正差代替9池完整结果。DeepSeek为135/216 tuning agents可评分，仅10/54严格N4池完整，六个预算×策略设置的完整MI/BoN均值均为unknown。缺失保留原分母，不因报告需要而恢复、重采样或从历史best-observed补最终答案。

| 模型 | 预算 | 策略 | 指标 | 2200 | 2204 | 2208 | 三块均值 | 描述 SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi-K3 | moderate | naive | gap_mi | 98.159365 | 97.682031 | 98.275201 | 98.038866 | 0.314409 |
| Kimi-K3 | moderate | naive | gap_bon | 98.929687 | 99.008280 | 99.022896 | 98.986955 | 0.050130 |
| Kimi-K3 | moderate | naive | raw_perf_mi | 0.938966 | 0.935486 | 0.940413 | 0.938288 | 0.002533 |
| Kimi-K3 | moderate | naive | raw_perf_bon | 0.942786 | 0.943176 | 0.943498 | 0.943153 | 0.000357 |
| Kimi-K3 | moderate | cached | gap_mi | 98.189185 | 97.876493 | 97.817742 | 97.961140 | 0.199665 |
| Kimi-K3 | moderate | cached | gap_bon | 98.999939 | 98.619248 | 98.898781 | 98.839323 | 0.197187 |
| Kimi-K3 | moderate | cached | raw_perf_mi | 0.938785 | 0.937405 | 0.936535 | 0.937575 | 0.001135 |
| Kimi-K3 | moderate | cached | raw_perf_bon | 0.943476 | 0.941161 | 0.942308 | 0.942315 | 0.001157 |
| Kimi-K3 | moderate | poolact | gap_mi | 98.742041 | 98.409035 | 98.517909 | 98.556328 | 0.169795 |
| Kimi-K3 | moderate | poolact | gap_bon | 99.203580 | 98.778343 | 98.631216 | 98.871046 | 0.297230 |
| Kimi-K3 | moderate | poolact | raw_perf_mi | 0.942160 | 0.940647 | 0.940961 | 0.941256 | 0.000799 |
| Kimi-K3 | moderate | poolact | raw_perf_bon | 0.944278 | 0.942586 | 0.941551 | 0.942805 | 0.001376 |
| Kimi-K3 | tight | naive | gap_mi | 95.204981 | 95.935980 | 91.633827 | 94.258262 | 2.302029 |
| Kimi-K3 | tight | naive | gap_bon | 98.382865 | 97.934448 | 97.662139 | 97.993150 | 0.363931 |
| Kimi-K3 | tight | naive | raw_perf_mi | 0.925186 | 0.926566 | 0.906539 | 0.919430 | 0.011185 |
| Kimi-K3 | tight | naive | raw_perf_bon | 0.940505 | 0.939336 | 0.937088 | 0.938976 | 0.001736 |
| Kimi-K3 | tight | cached | gap_mi | 94.012988 | 95.230677 | 93.090729 | 94.111464 | 1.073367 |
| Kimi-K3 | tight | cached | gap_bon | 98.556372 | 98.499508 | 98.042884 | 98.366255 | 0.281487 |
| Kimi-K3 | tight | cached | raw_perf_mi | 0.916386 | 0.920061 | 0.913559 | 0.916669 | 0.003260 |
| Kimi-K3 | tight | cached | raw_perf_bon | 0.940994 | 0.940527 | 0.938980 | 0.940167 | 0.001054 |
| Kimi-K3 | tight | poolact | gap_mi | 96.017289 | 96.675142 | 95.462595 | 96.051676 | 0.607004 |
| Kimi-K3 | tight | poolact | gap_bon | 98.509911 | 98.153972 | 98.431462 | 98.365115 | 0.187015 |
| Kimi-K3 | tight | poolact | raw_perf_mi | 0.927968 | 0.929596 | 0.929751 | 0.929105 | 0.000988 |
| Kimi-K3 | tight | poolact | raw_perf_bon | 0.940316 | 0.939080 | 0.940360 | 0.939919 | 0.000726 |
| GLM-5.3 | moderate | naive | gap_mi | 98.284886 | 97.116195 | 98.218909 | 97.873330 | 0.656527 |
| GLM-5.3 | moderate | naive | gap_bon | 98.659706 | 99.337451 | 99.025902 | 99.007686 | 0.339239 |
| GLM-5.3 | moderate | naive | raw_perf_mi | 0.940023 | 0.932492 | 0.939002 | 0.937173 | 0.004086 |
| GLM-5.3 | moderate | naive | raw_perf_bon | 0.941607 | 0.943699 | 0.942831 | 0.942712 | 0.001051 |
| GLM-5.3 | moderate | cached | gap_mi | 98.313975 | 98.089126 | 97.780897 | 98.061333 | 0.267624 |
| GLM-5.3 | moderate | cached | gap_bon | 99.041402 | 99.010835 | 99.295587 | 99.115941 | 0.156326 |
| GLM-5.3 | moderate | cached | raw_perf_mi | 0.940533 | 0.939539 | 0.934520 | 0.938197 | 0.003223 |
| GLM-5.3 | moderate | cached | raw_perf_bon | 0.943376 | 0.943298 | 0.943298 | 0.943324 | 0.000045 |
| GLM-5.3 | moderate | poolact | gap_mi | 98.943264 | 98.786747 | 99.167472 | 98.965828 | 0.191363 |
| GLM-5.3 | moderate | poolact | gap_bon | 99.303895 | 99.400526 | 99.437796 | 99.380739 | 0.069109 |
| GLM-5.3 | moderate | poolact | raw_perf_mi | 0.941963 | 0.941317 | 0.943983 | 0.942421 | 0.001391 |
| GLM-5.3 | moderate | poolact | raw_perf_bon | 0.943610 | 0.944912 | 0.944912 | 0.944478 | 0.000752 |
| GLM-5.3 | tight | naive | gap_mi | 87.086990 | 81.378917 | 83.415077 | 83.960328 | 2.892836 |
| GLM-5.3 | tight | naive | gap_bon | 93.425246 | 91.065575 | 96.938176 | 93.809666 | 2.955113 |
| GLM-5.3 | tight | naive | raw_perf_mi | 0.885976 | 0.873734 | 0.881886 | 0.880532 | 0.006232 |
| GLM-5.3 | tight | naive | raw_perf_bon | 0.907741 | 0.920339 | 0.934629 | 0.920903 | 0.013453 |
| GLM-5.3 | tight | cached | gap_mi | 87.586956 | 86.326175 | 84.634604 | 86.182578 | 1.481405 |
| GLM-5.3 | tight | cached | gap_bon | 97.310553 | 98.131415 | 88.204374 | 94.548781 | 5.509725 |
| GLM-5.3 | tight | cached | raw_perf_mi | 0.889559 | 0.891373 | 0.884869 | 0.888600 | 0.003357 |
| GLM-5.3 | tight | cached | raw_perf_bon | 0.935063 | 0.939804 | 0.894253 | 0.923040 | 0.025043 |
| GLM-5.3 | tight | poolact | gap_mi | 96.015442 | 95.255042 | 97.259313 | 96.176599 | 1.011807 |
| GLM-5.3 | tight | poolact | gap_bon | 98.309475 | 98.353883 | 98.725721 | 98.463026 | 0.228581 |
| GLM-5.3 | tight | poolact | raw_perf_mi | 0.927111 | 0.925873 | 0.932901 | 0.928628 | 0.003752 |
| GLM-5.3 | tight | poolact | raw_perf_bon | 0.940093 | 0.940416 | 0.942553 | 0.941020 | 0.001337 |
| Qwen3.8 | moderate | naive | gap_mi | 97.263539 | 97.406194 | 96.099122 | 96.922951 | 0.717014 |
| Qwen3.8 | moderate | naive | gap_bon | 98.896086 | 98.812086 | 98.394444 | 98.700872 | 0.268677 |
| Qwen3.8 | moderate | naive | raw_perf_mi | 0.934860 | 0.937739 | 0.929056 | 0.933885 | 0.004423 |
| Qwen3.8 | moderate | naive | raw_perf_bon | 0.942408 | 0.942786 | 0.940983 | 0.942059 | 0.000951 |
| Qwen3.8 | moderate | cached | gap_mi | 96.827323 | 98.303108 | 98.039568 | 97.723333 | 0.787076 |
| Qwen3.8 | moderate | cached | gap_bon | 98.316408 | 99.338952 | 99.355229 | 99.003529 | 0.595120 |
| Qwen3.8 | moderate | cached | raw_perf_mi | 0.935475 | 0.938543 | 0.937547 | 0.937188 | 0.001566 |
| Qwen3.8 | moderate | cached | raw_perf_bon | 0.940994 | 0.943810 | 0.943944 | 0.942916 | 0.001665 |
| Qwen3.8 | moderate | poolact | gap_mi | 98.570337 | 98.965374 | 99.072741 | 98.869484 | 0.264573 |
| Qwen3.8 | moderate | poolact | gap_bon | 98.902879 | 99.108303 | 99.432638 | 99.147940 | 0.267095 |
| Qwen3.8 | moderate | poolact | raw_perf_mi | 0.941643 | 0.942625 | 0.943716 | 0.942661 | 0.001037 |
| Qwen3.8 | moderate | poolact | raw_perf_bon | 0.942998 | 0.943298 | 0.944967 | 0.943754 | 0.001061 |
| Qwen3.8 | tight | naive | gap_mi | 93.249957 | 86.271082 | 92.342232 | 90.621090 | 3.794459 |
| Qwen3.8 | tight | naive | gap_bon | 98.690903 | 97.966618 | 98.915342 | 98.524288 | 0.495823 |
| Qwen3.8 | tight | naive | raw_perf_mi | 0.918625 | 0.846835 | 0.909795 | 0.891752 | 0.039148 |
| Qwen3.8 | tight | naive | raw_perf_bon | 0.941707 | 0.938791 | 0.943320 | 0.941273 | 0.002296 |
| Qwen3.8 | tight | cached | gap_mi | 92.510783 | 85.821170 | 93.940855 | 90.757603 | 4.334461 |
| Qwen3.8 | tight | cached | gap_bon | 98.180871 | 97.819759 | 98.450598 | 98.150410 | 0.316521 |
| Qwen3.8 | tight | cached | raw_perf_mi | 0.913028 | 0.868011 | 0.918055 | 0.899698 | 0.027556 |
| Qwen3.8 | tight | cached | raw_perf_bon | 0.937589 | 0.935541 | 0.940672 | 0.937934 | 0.002583 |
| Qwen3.8 | tight | poolact | gap_mi | 96.648598 | 95.278785 | 96.884637 | 96.270673 | 0.867070 |
| Qwen3.8 | tight | poolact | gap_bon | 98.111913 | 98.321740 | 98.439672 | 98.291108 | 0.166013 |
| Qwen3.8 | tight | poolact | raw_perf_mi | 0.932701 | 0.929490 | 0.930099 | 0.930763 | 0.001705 |
| Qwen3.8 | tight | poolact | raw_perf_bon | 0.937166 | 0.939347 | 0.940093 | 0.938869 | 0.001521 |
| DeepSeek-0731 | moderate | naive | gap_mi | unknown (1/3) | unknown (0/3) | unknown (0/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | moderate | naive | gap_bon | unknown (1/3) | unknown (0/3) | unknown (0/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | moderate | naive | raw_perf_mi | unknown (1/3) | unknown (0/3) | unknown (0/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | moderate | naive | raw_perf_bon | unknown (1/3) | unknown (0/3) | unknown (0/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | moderate | cached | gap_mi | unknown (1/3) | unknown (1/3) | unknown (1/3) | unknown (3/9) | unknown |
| DeepSeek-0731 | moderate | cached | gap_bon | unknown (1/3) | unknown (1/3) | unknown (1/3) | unknown (3/9) | unknown |
| DeepSeek-0731 | moderate | cached | raw_perf_mi | unknown (1/3) | unknown (1/3) | unknown (1/3) | unknown (3/9) | unknown |
| DeepSeek-0731 | moderate | cached | raw_perf_bon | unknown (1/3) | unknown (1/3) | unknown (1/3) | unknown (3/9) | unknown |
| DeepSeek-0731 | moderate | poolact | gap_mi | unknown (0/3) | unknown (1/3) | unknown (0/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | moderate | poolact | gap_bon | unknown (0/3) | unknown (1/3) | unknown (0/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | moderate | poolact | raw_perf_mi | unknown (0/3) | unknown (1/3) | unknown (0/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | moderate | poolact | raw_perf_bon | unknown (0/3) | unknown (1/3) | unknown (0/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | tight | naive | gap_mi | unknown (0/3) | unknown (2/3) | unknown (0/3) | unknown (2/9) | unknown |
| DeepSeek-0731 | tight | naive | gap_bon | unknown (0/3) | unknown (2/3) | unknown (0/3) | unknown (2/9) | unknown |
| DeepSeek-0731 | tight | naive | raw_perf_mi | unknown (0/3) | unknown (2/3) | unknown (0/3) | unknown (2/9) | unknown |
| DeepSeek-0731 | tight | naive | raw_perf_bon | unknown (0/3) | unknown (2/3) | unknown (0/3) | unknown (2/9) | unknown |
| DeepSeek-0731 | tight | cached | gap_mi | unknown (0/3) | unknown (0/3) | unknown (1/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | tight | cached | gap_bon | unknown (0/3) | unknown (0/3) | unknown (1/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | tight | cached | raw_perf_mi | unknown (0/3) | unknown (0/3) | unknown (1/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | tight | cached | raw_perf_bon | unknown (0/3) | unknown (0/3) | unknown (1/3) | unknown (1/9) | unknown |
| DeepSeek-0731 | tight | poolact | gap_mi | unknown (1/3) | unknown (1/3) | unknown (0/3) | unknown (2/9) | unknown |
| DeepSeek-0731 | tight | poolact | gap_bon | unknown (1/3) | unknown (1/3) | unknown (0/3) | unknown (2/9) | unknown |
| DeepSeek-0731 | tight | poolact | raw_perf_mi | unknown (1/3) | unknown (1/3) | unknown (0/3) | unknown (2/9) | unknown |
| DeepSeek-0731 | tight | poolact | raw_perf_bon | unknown (1/3) | unknown (1/3) | unknown (0/3) | unknown (2/9) | unknown |
| GPT-5.6-sol (medium) | moderate | naive | gap_mi | 98.108029 | 98.523865 | 98.001919 | 98.211271 | 0.275864 |
| GPT-5.6-sol (medium) | moderate | naive | gap_bon | 98.617411 | 99.072453 | 98.419767 | 98.703210 | 0.334695 |
| GPT-5.6-sol (medium) | moderate | naive | raw_perf_mi | 0.939292 | 0.941114 | 0.938986 | 0.939797 | 0.001151 |
| GPT-5.6-sol (medium) | moderate | naive | raw_perf_bon | 0.941339 | 0.943810 | 0.941117 | 0.942089 | 0.001495 |
| GPT-5.6-sol (medium) | moderate | cached | gap_mi | 98.165924 | 98.307406 | 98.365254 | 98.279528 | 0.102548 |
| GPT-5.6-sol (medium) | moderate | cached | gap_bon | 98.609833 | 98.831032 | 98.956391 | 98.799085 | 0.175473 |
| GPT-5.6-sol (medium) | moderate | cached | raw_perf_mi | 0.939584 | 0.940449 | 0.940380 | 0.940138 | 0.000481 |
| GPT-5.6-sol (medium) | moderate | cached | raw_perf_bon | 0.941462 | 0.943320 | 0.942619 | 0.942467 | 0.000939 |
| GPT-5.6-sol (medium) | moderate | poolact | gap_mi | 98.436691 | 98.328463 | unknown (2/3) | unknown (8/9) | unknown |
| GPT-5.6-sol (medium) | moderate | poolact | gap_bon | 98.950926 | 98.667483 | unknown (2/3) | unknown (8/9) | unknown |
| GPT-5.6-sol (medium) | moderate | poolact | raw_perf_mi | 0.938991 | 0.940138 | unknown (2/3) | unknown (8/9) | unknown |
| GPT-5.6-sol (medium) | moderate | poolact | raw_perf_bon | 0.942163 | 0.941740 | unknown (2/3) | unknown (8/9) | unknown |
| GPT-5.6-sol (medium) | tight | naive | gap_mi | 96.421315 | 96.317920 | 97.183811 | 96.641015 | 0.472909 |
| GPT-5.6-sol (medium) | tight | naive | gap_bon | 98.188349 | 98.398921 | 98.002508 | 98.196592 | 0.198335 |
| GPT-5.6-sol (medium) | tight | naive | raw_perf_mi | 0.929523 | 0.929415 | 0.935672 | 0.931537 | 0.003582 |
| GPT-5.6-sol (medium) | tight | naive | raw_perf_bon | 0.940371 | 0.940627 | 0.939425 | 0.940141 | 0.000633 |
| GPT-5.6-sol (medium) | tight | cached | gap_mi | 94.034024 | 96.351635 | 97.762727 | 96.049462 | 1.882628 |
| GPT-5.6-sol (medium) | tight | cached | gap_bon | 98.006313 | 98.025482 | 98.869622 | 98.300473 | 0.492991 |
| GPT-5.6-sol (medium) | tight | cached | raw_perf_mi | 0.926374 | 0.932336 | 0.938504 | 0.932405 | 0.006066 |
| GPT-5.6-sol (medium) | tight | cached | raw_perf_bon | 0.939281 | 0.939503 | 0.942653 | 0.940479 | 0.001886 |
| GPT-5.6-sol (medium) | tight | poolact | gap_mi | 97.574040 | 97.369761 | 96.868333 | 97.270712 | 0.363131 |
| GPT-5.6-sol (medium) | tight | poolact | gap_bon | 98.356693 | 98.195024 | 97.695967 | 98.082561 | 0.344421 |
| GPT-5.6-sol (medium) | tight | poolact | raw_perf_mi | 0.937550 | 0.934960 | 0.933112 | 0.935207 | 0.002229 |
| GPT-5.6-sol (medium) | tight | poolact | raw_perf_bon | 0.941506 | 0.939470 | 0.937912 | 0.939629 | 0.001803 |


NAS101 A/B/C的逐任务与三个blocks均保留，完整结果见 [TABLES.md](TABLES.md) 与 [REPEATS.md](REPEATS.md)。

## 4. 主问题三：任务家族与部署预算改变时，模型排名如何重排？

**本次候选模型中，不存在跨任务家族和反馈预算的单一赢家。** 在同一任务端点内，Free最优者不一定在Tight仍最优；另一方面，部分家族的领先者保持不变。这里的排名重排指实际部署的反馈受限程度改变后，已观察到的质量顺序发生变化，而不是根据不同指标拼一个跨模型总榜。

### 4.1 六个预设任务家族主端点

排名使用六个不重复的ExpGym端点：whois F1、whatis F1、Audit EA、ParamNet Gap、NAS101 Gap、NAS201 Gap。它们不再额外加入Search all或HPO all计数，也不混入PoolAct不同N/策略。每个家族先确定Free / Moderate / Tight三档都具有完整分母的模型，形成**跨三档固定候选集**，然后按原单位、越高越好排列；绝对差不超过`1e-12`的值按并列处理。unknown不补零，不以单档可评分者变动制造排名变化。

排名仅使用同一端点、同一预算的原指标，先在每个端点固定 F/M/T 三档均完整的候选集，不按每档已知结果动态增减模型。原计划五模型的所有原值、分母及排除原因保留在 [RANKINGS.csv](RANKINGS.csv)。HPO 缺失模型不补零、不用已知子集均值参与完整端点排名；排除后第一仅是该固定候选集内的观察第一。并列按未舍入分数与本组最高分 anchor 的绝对差 ≤1e-12，不使用相邻分数传递链；这是浮点等分规则，不是统计等价。名次采用 competition rank（1、2、2、4）。runner-up margin 为第一与第二个候选的分数差；并列第一记 0，不用它声称显著性。

| 端点 | 三档固定完整候选 | Free 观察第一 | Moderate 观察第一 | Tight 观察第一 | Free→Tight |
| --- | --- | --- | --- | --- | --- |
| Search whois / F1 | Kimi / GLM / Qwen / DeepSeek / GPT | GLM 0.682651 | GLM 0.642842 | GLM 0.230575 | 不变 |
| Search whatis / F1 | Kimi / GLM / Qwen / DeepSeek / GPT | GPT 0.654206 | GPT 0.453877 | DeepSeek 0.159269 | 换位 |
| Audit / EA | Kimi / GLM / Qwen / DeepSeek / GPT | Qwen 0.918552 | Qwen 0.749623 | Qwen 0.583710 | 不变 |
| ParamNet / Gap | Kimi / GLM / Qwen / GPT | GPT 97.312330 | GPT 95.271826 | GPT 85.694084 | 不变 |
| NAS101 / Gap | Kimi / GLM / Qwen / GPT | GLM 99.057476 | GPT 98.324002 | GPT 97.030843 | 换位 |
| NAS201 / Gap | Kimi / GLM / Qwen / GPT | Kimi 99.770835 | Kimi 97.076629 | Kimi 94.660569 | 不变 |

| 端点 | Free 完整排序 | Moderate 完整排序 | Tight 完整排序 |
| --- | --- | --- | --- |
| Search whois / F1 | GLM > Kimi > Qwen > GPT > DeepSeek | GLM > Qwen > GPT > Kimi > DeepSeek | GLM > Qwen > DeepSeek > GPT = Kimi |
| Search whatis / F1 | GPT > GLM > Kimi > Qwen > DeepSeek | GPT > Kimi > GLM > Qwen > DeepSeek | DeepSeek > GLM > Kimi > GPT > Qwen |
| Audit / EA | Qwen > Kimi > GPT > GLM > DeepSeek | Qwen > Kimi > GLM > GPT > DeepSeek | Qwen > GPT > Kimi > GLM > DeepSeek |
| ParamNet / Gap | GPT > Kimi > GLM > Qwen | GPT > Qwen > GLM > Kimi | GPT > Kimi > GLM > Qwen |
| NAS101 / Gap | GLM > Kimi > Qwen > GPT | GPT > Kimi > GLM > Qwen | GPT > Kimi > Qwen > GLM |
| NAS201 / Gap | Kimi > GLM > Qwen > GPT | Kimi > GLM > GPT > Qwen | Kimi > GPT > GLM > Qwen |

Free→Tight的六个家族中，两处冠军发生变化：**whatis由GPT变为DeepSeek，NAS101由GLM变为GPT**。whois仍为GLM、Audit仍为Qwen、ParamNet仍为GPT、NAS201仍为Kimi。这里三个HPO家族因DeepSeek完整结果缺失，候选集只有Kimi、GLM、Qwen、GPT；所谓NAS101换位是这四个完整候选内的换位，不能写成已确认五模型冠军。

任务家族之间也存在明显区别：whois领先者不能自动代表whatis，Audit的领先者也不代表ParamNet或NAS。模型选择因此应同时指定“做哪类任务”和“允许多少反馈”，不能只看Free下的一列绝对分数。

### 4.2 九个 HPO / NAS 任务的预算排名变化

| 端点 | 三档固定完整候选 | Free 观察第一 | Moderate 观察第一 | Tight 观察第一 | Free→Tight |
| --- | --- | --- | --- | --- | --- |
| NAS101 A | Kimi / GLM / Qwen / GPT | Qwen 99.580753 | GLM 99.003299 | GPT 96.614377 | 换位 |
| NAS101 B | Kimi / GLM / Qwen / DeepSeek / GPT | GLM 97.969343 | GLM 97.467138 | Kimi 95.759638 | 换位 |
| NAS101 C | Kimi / GLM / Qwen / GPT | GLM 99.623912 | GPT 98.997748 | GPT 99.015472 | 换位 |
| NAS201 cifar10-valid | Kimi / GLM / Qwen / GPT | Kimi 100.000000 | GPT 98.855387 | GPT 97.654940 | 换位 |
| NAS201 cifar100 | Kimi / GLM / Qwen / DeepSeek / GPT | Kimi 100.000000 | Kimi 100.000000; Qwen 100.000000 | Kimi 97.479188 | 不变 |
| NAS201 imagenet16-120 | Kimi / GLM / Qwen / GPT | Kimi 99.312504 | Kimi 97.572717 | Kimi 96.295938 | 不变 |
| ParamNet adult | Kimi / GLM / Qwen / GPT | GPT 97.939423 | GLM 95.414265 | Kimi 77.355993 | 换位 |
| ParamNet higgs | Kimi / GLM / Qwen / GPT | GLM 95.829008 | GPT 97.146907 | GPT 89.704134 | 换位 |
| ParamNet letter | Kimi / GLM / Qwen / GPT | Kimi 99.221702 | Qwen 98.885684 | GPT 95.364674 | 换位 |

九 task 保持既有 item 内三次重复平均；原 Gap 不重新评分、不截断到 100。

在每任务固定、三档完整的候选集内，九个HPO任务有七个发生Free→Tight冠军换位。这是逐任务候选范围内的描述，不是九个任务都具备五模型完整证据。若严格要求五模型在三档全部完整，只剩两个任务，其中一个换位。两种口径同时列明，避免把缺失的DeepSeek当成落后，或把四模型比较扩写为完整五模型排行榜。

### 4.3 重排统计与部署含义

六类家族主端点的固定完整候选排名中，Free→Tight 冠军集合换位 **2/6**（计划 6 个端点）；严格五模型全三档完整的家族子集为 **1/3**。九个 HPO task 的对应计数为 **7/9**（计划 9 个），严格五模型子集为 **1/2**。分子比较 Free 与 Tight 的冠军集合，不把 Moderate 暂时并列混入；Search/HPO all 与 Audit LA 只作次级展示，不再加入这些分母。

在五模型全完整的家族中，Free；Moderate；Tight 都不存在跨家族共同第一名。这里考察部署反馈预算程度（deployment budget degree）下的相对表现：整体排序和局部冠军是否随任务、预算变化，而不是构造跨指标总榜。观察换位不意味着每个家族都会换位，也不是不同 effort、API/自部署设置已受控的纯模型因果排名。

完整名次、候选集、并列与各预算转移见 [RANKINGS.md](RANKINGS.md)、[RANKINGS.csv](RANKINGS.csv) 和 [RANK_TRANSITIONS.csv](RANK_TRANSITIONS.csv)。冠军不变也不意味着所有名次不变；反过来，小幅分数差导致的换位也不等于统计显著胜出。本次不新增p值、不凭名次数选择任务，也不将API medium、自部署最高effort及不同量化/拓扑条件视为已严格控制的纯模型能力实验。

部署上的直接含义是：应在实际任务家族与目标反馈预算下选型，并同时核对质量、缓存/协调策略和资源账本。下面将资源分为已有自部署分析单元均值与GPT全部尝试总账，避免把不同导出单位混成一个效率排名。

### 4.4 自部署四模型：分析单元资源与分配成本

以下资源均值沿用四模型冻结导出，按item内重复平均、再对item等权；不是整项研究总账。Pool的tokens、反馈次数及模拟反馈成本为四agents合计；Exp Audit资源为三个orders的均值。旧Kimi/GLM有整个pool子进程wall，新Qwen/DeepSeek原exporter没有该字段，保持unknown，不能用agent时长sum/max补齐。

受限档位的budget_utilization为反馈成本/B，Pool为四成员反馈成本合计/(4B)。最后一次已发起工具调用可能越过剩余预算，所以该值允许大于1；Free没有有限分母，标为“不适用”。模拟反馈秒不是GPU秒。

| 模型 | 系统/场景 | 预算 | 策略 | input_tokens | output_tokens | feedback_cost_seconds | wall_time_seconds | feedback_attempts | duplicate_action_attempts | feedback_visible | budget_utilization | protocol_failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi-K3 | expgym/restricted_search | free | single | 99545.136986 | 9387.739726 | 3631.827073 | 664.067277 | 14.054795 | 0.013699 | 14.054795 | 不适用 | 0.000000 |
| Kimi-K3 | expgym/restricted_search | moderate | single | 43586.767123 | 7193.082192 | 2525.175439 | 523.515513 | 9.958904 | 0.000000 | 9.767123 | 0.841725 | 0.000000 |
| Kimi-K3 | expgym/restricted_search | tight | single | 6940.410959 | 2861.712329 | 1012.913496 | 203.157551 | 3.753425 | 0.000000 | 2.958904 | 1.125459 | 0.000000 |
| Kimi-K3 | expgym/evidence_audit | free | single | 366956.589744 | 16024.974359 | 8327.956221 | 1086.338041 | 27.717949 | 0.128205 | 27.717949 | 不适用 | 0.000000 |
| Kimi-K3 | expgym/evidence_audit | moderate | single | 104462.025641 | 14751.871795 | 2844.170369 | 1017.687354 | 9.435897 | 0.000000 | 9.230769 | 0.948057 | 0.000000 |
| Kimi-K3 | expgym/evidence_audit | tight | single | 22878.307692 | 8032.512821 | 850.588274 | 571.388226 | 2.820513 | 0.000000 | 2.384615 | 0.945098 | 0.000000 |
| Kimi-K3 | expgym/tuning | free | single | 230295.592593 | 14047.407407 | 252387.797068 | 825.945845 | 23.666667 | 0.185185 | 23.666667 | 不适用 | 0.000000 |
| Kimi-K3 | expgym/tuning | moderate | single | 57097.444444 | 8961.444444 | 96667.251220 | 493.495243 | 8.111111 | 0.000000 | 7.962963 | 0.871193 | 0.000000 |
| Kimi-K3 | expgym/tuning | tight | single | 21049.037037 | 6563.111111 | 36051.521950 | 382.524720 | 3.814815 | 0.000000 | 3.370370 | 1.232265 | 0.000000 |
| Kimi-K3 | poolact/restricted_search | moderate | naive | 171855.666667 | 24429.564103 | 9643.410741 | 670.684804 | 39.384615 | 21.794872 | unknown (0/39) | 0.803618 | 0.000000 |
| Kimi-K3 | poolact/restricted_search | moderate | cached | 193728.256410 | 25506.128205 | 8963.780838 | 636.872697 | 41.051282 | 22.743590 | unknown (0/39) | 0.746982 | 0.001508 |
| Kimi-K3 | poolact/restricted_search | moderate | poolact | 469631.333333 | 39232.923077 | 7673.324528 | 2785.353798 | 40.666667 | 20.564103 | unknown (0/39) | 0.639444 | 0.000000 |
| Kimi-K3 | poolact/restricted_search | tight | naive | 30428.615385 | 12059.948718 | 4109.480041 | 384.863589 | 15.461538 | 9.487179 | unknown (0/39) | 1.141522 | 0.000000 |
| Kimi-K3 | poolact/restricted_search | tight | cached | 35100.794872 | 13563.769231 | 4007.590673 | 468.324156 | 16.256410 | 9.461538 | unknown (0/39) | 1.113220 | 0.000000 |
| Kimi-K3 | poolact/restricted_search | tight | poolact | 73846.153846 | 17289.384615 | 3886.969286 | 1169.436990 | 17.461538 | 6.102564 | unknown (0/39) | 1.079714 | 0.000000 |
| Kimi-K3 | poolact/evidence_audit | moderate | naive | 435431.692308 | 59997.076923 | 11537.166336 | 1771.345564 | 38.307692 | 17.538462 | unknown (0/13) | 0.961431 | 0.000000 |
| Kimi-K3 | poolact/evidence_audit | moderate | cached | 506641.076923 | 59882.538462 | 10966.121039 | 1551.636591 | 43.846154 | 21.615385 | unknown (0/13) | 0.913843 | 0.000000 |
| Kimi-K3 | poolact/evidence_audit | moderate | poolact | 670641.692308 | 76833.461538 | 11228.417970 | 5380.948324 | 37.615385 | 10.384615 | unknown (0/13) | 0.935701 | 0.000000 |
| Kimi-K3 | poolact/evidence_audit | tight | naive | 94498.384615 | 36806.846154 | 3153.365251 | 1039.522642 | 10.461538 | 4.846154 | unknown (0/13) | 0.875935 | 0.000000 |
| Kimi-K3 | poolact/evidence_audit | tight | cached | 104495.000000 | 40671.076923 | 3219.343615 | 1207.165748 | 10.769231 | 5.076923 | unknown (0/13) | 0.894262 | 0.000000 |
| Kimi-K3 | poolact/evidence_audit | tight | poolact | 123983.153846 | 47385.307692 | 3507.503484 | 3396.817980 | 11.615385 | 2.615385 | unknown (0/13) | 0.974307 | 0.000000 |
| Kimi-K3 | poolact/tuning | moderate | naive | 519038.333333 | 67688.333333 | 322161.705777 | 1608.792329 | 39.222222 | 0.222222 | unknown (0/9) | 0.913028 | 0.000000 |
| Kimi-K3 | poolact/tuning | moderate | cached | 512309.777778 | 63995.888889 | 309297.951823 | 1398.424206 | 38.444444 | 0.777778 | unknown (0/9) | 0.888557 | 0.000000 |
| Kimi-K3 | poolact/tuning | moderate | poolact | 1118384.333333 | 88541.222222 | 268570.794532 | 5582.461858 | 32.888889 | 2.555556 | unknown (0/9) | 0.786614 | 0.000000 |
| Kimi-K3 | poolact/tuning | tight | naive | 113636.888889 | 34181.000000 | 109658.326131 | 800.030740 | 12.666667 | 0.111111 | unknown (0/9) | 1.107222 | 0.000000 |
| Kimi-K3 | poolact/tuning | tight | cached | 113071.888889 | 35135.888889 | 114140.534058 | 867.783888 | 12.666667 | 0.444444 | unknown (0/9) | 1.144623 | 0.000000 |
| Kimi-K3 | poolact/tuning | tight | poolact | 169065.666667 | 33587.333333 | 105743.352919 | 1758.332952 | 12.222222 | 0.555556 | unknown (0/9) | 1.033461 | 0.000000 |
| GLM-5.3 | expgym/restricted_search | free | single | 169909.917808 | 19600.808219 | 4126.073236 | 494.852681 | 16.863014 | 0.041096 | 16.863014 | 不适用 | 0.034175 |
| GLM-5.3 | expgym/restricted_search | moderate | single | 67510.958904 | 19054.767123 | 2558.468748 | 481.319470 | 10.287671 | 0.000000 | 10.054795 | 0.852823 | 0.058324 |
| GLM-5.3 | expgym/restricted_search | tight | single | 14507.273973 | 9697.479452 | 1056.824892 | 244.842457 | 4.054795 | 0.000000 | 3.164384 | 1.174250 | 0.067482 |
| GLM-5.3 | expgym/evidence_audit | free | single | 899925.666667 | 49681.974359 | 7895.183171 | 1256.699367 | 26.307692 | 0.025641 | 26.307692 | 不适用 | 0.015424 |
| GLM-5.3 | expgym/evidence_audit | moderate | single | 468084.230769 | 84948.794872 | 2935.049756 | 2134.877804 | 9.794872 | 0.000000 | 9.512821 | 0.978350 | 0.017677 |
| GLM-5.3 | expgym/evidence_audit | tight | single | 110772.923077 | 49455.769231 | 907.450009 | 1261.353119 | 3.025641 | 0.000000 | 2.564103 | 1.008278 | 0.055983 |
| GLM-5.3 | expgym/tuning | free | single | 274232.037037 | 14701.185185 | 346971.654252 | 374.648285 | 29.407407 | 0.111111 | 29.407407 | 不适用 | 0.014419 |
| GLM-5.3 | expgym/tuning | moderate | single | 184063.444444 | 27606.629630 | 113814.763947 | 620.089671 | 10.629630 | 0.000000 | 10.444444 | 0.968884 | 0.054599 |
| GLM-5.3 | expgym/tuning | tight | single | 37732.703704 | 16316.370370 | 37035.891735 | 403.254350 | 3.666667 | 0.000000 | 3.185185 | 1.113898 | 0.101587 |
| GLM-5.3 | poolact/restricted_search | moderate | naive | 302391.282051 | 82204.641026 | 10017.152159 | 889.069421 | 41.025641 | 24.692308 | unknown (0/39) | 0.834763 | 0.054349 |
| GLM-5.3 | poolact/restricted_search | moderate | cached | 355575.743590 | 83759.102564 | 9200.367612 | 840.881999 | 44.512821 | 26.102564 | unknown (0/39) | 0.766697 | 0.043353 |
| GLM-5.3 | poolact/restricted_search | moderate | poolact | 1062983.717949 | 135370.948718 | 8433.958196 | 3376.654692 | 47.153846 | 24.923077 | unknown (0/39) | 0.702830 | 0.012362 |
| GLM-5.3 | poolact/restricted_search | tight | naive | 45893.282051 | 43355.051282 | 4168.844006 | 531.803013 | 16.230769 | 9.666667 | unknown (0/39) | 1.158012 | 0.088134 |
| GLM-5.3 | poolact/restricted_search | tight | cached | 69631.128205 | 46091.564103 | 4144.983991 | 566.510133 | 17.615385 | 10.435897 | unknown (0/39) | 1.151384 | 0.077924 |
| GLM-5.3 | poolact/restricted_search | tight | poolact | 240859.076923 | 88946.358974 | 4024.406994 | 2257.047684 | 20.410256 | 7.461538 | unknown (0/39) | 1.117891 | 0.031344 |
| GLM-5.3 | poolact/evidence_audit | moderate | naive | 1798701.769231 | 322716.615385 | 11668.482933 | 2641.934361 | 38.846154 | 20.307692 | unknown (0/13) | 0.972374 | 0.018194 |
| GLM-5.3 | poolact/evidence_audit | moderate | cached | 2465750.923077 | 352803.461538 | 10778.941689 | 2982.409317 | 47.076923 | 25.307692 | unknown (0/13) | 0.898245 | 0.021547 |
| GLM-5.3 | poolact/evidence_audit | moderate | poolact | 1828379.923077 | 287668.000000 | 11390.704547 | 7175.411588 | 38.384615 | 10.461538 | unknown (0/13) | 0.949225 | 0.005367 |
| GLM-5.3 | poolact/evidence_audit | tight | naive | 456518.538462 | 207078.538462 | 3584.775565 | 1825.328098 | 11.923077 | 5.692308 | unknown (0/13) | 0.995771 | 0.052790 |
| GLM-5.3 | poolact/evidence_audit | tight | cached | 490287.307692 | 211146.230769 | 3570.146708 | 1663.473940 | 12.384615 | 6.153846 | unknown (0/13) | 0.991707 | 0.063340 |
| GLM-5.3 | poolact/evidence_audit | tight | poolact | 422295.153846 | 231944.307692 | 3559.264010 | 5667.666078 | 11.846154 | 3.538462 | unknown (0/13) | 0.988684 | 0.070792 |
| GLM-5.3 | poolact/tuning | moderate | naive | 988802.111111 | 197910.666667 | 338082.847551 | 1745.712838 | 38.666667 | 3.000000 | unknown (0/9) | 0.950887 | 0.068127 |
| GLM-5.3 | poolact/tuning | moderate | cached | 1071169.666667 | 215092.777778 | 327973.409776 | 1772.964828 | 39.444444 | 3.444444 | unknown (0/9) | 0.946202 | 0.066177 |
| GLM-5.3 | poolact/tuning | moderate | poolact | 3115054.777778 | 322813.888889 | 318969.753086 | 7034.944031 | 43.666667 | 1.555556 | unknown (0/9) | 0.919878 | 0.015097 |
| GLM-5.3 | poolact/tuning | tight | naive | 369815.333333 | 133198.555556 | 113389.873281 | 1299.392815 | 13.888889 | 2.111111 | unknown (0/9) | 1.171354 | 0.151512 |
| GLM-5.3 | poolact/tuning | tight | cached | 244441.444444 | 87543.111111 | 117391.549025 | 965.025405 | 13.666667 | 3.000000 | unknown (0/9) | 1.181798 | 0.106991 |
| GLM-5.3 | poolact/tuning | tight | poolact | 457954.555556 | 130600.000000 | 107524.511929 | 2708.759140 | 15.555556 | 0.888889 | unknown (0/9) | 1.074063 | 0.060739 |
| Qwen3.8 | expgym/restricted_search | free | single | 83932.780822 | 6003.315068 | 3497.117931 | 258.115580 | 14.643836 | 0.041096 | 14.643836 | 不适用 | 0.033667 |
| Qwen3.8 | expgym/restricted_search | moderate | single | 53450.150685 | 5958.506849 | 2476.096656 | 246.691747 | 10.767123 | 0.054795 | 10.465753 | 0.825366 | 0.045585 |
| Qwen3.8 | expgym/restricted_search | tight | single | 9639.465753 | 2305.890411 | 986.534212 | 86.664292 | 4.013699 | 0.013699 | 3.356164 | 1.096149 | 0.055055 |
| Qwen3.8 | expgym/evidence_audit | free | single | 307147.282051 | 13626.307692 | 8356.558677 | 562.460795 | 27.820513 | 0.025641 | 27.820513 | 不适用 | 0.018590 |
| Qwen3.8 | expgym/evidence_audit | moderate | single | 95237.230769 | 12671.256410 | 2942.532437 | 464.679027 | 9.769231 | 0.000000 | 9.358974 | 0.980844 | 0.004274 |
| Qwen3.8 | expgym/evidence_audit | tight | single | 29621.743590 | 10947.256410 | 915.954274 | 410.386282 | 3.051282 | 0.000000 | 2.435897 | 1.017727 | 0.008547 |
| Qwen3.8 | expgym/tuning | free | single | 267768.259259 | 13746.296296 | 312526.104967 | 503.442693 | 29.074074 | 0.185185 | 29.074074 | 不适用 | 0.008894 |
| Qwen3.8 | expgym/tuning | moderate | single | 64952.777778 | 7655.888889 | 112729.789523 | 286.809788 | 9.666667 | 0.037037 | 9.592593 | 0.929251 | 0.023952 |
| Qwen3.8 | expgym/tuning | tight | single | 23737.111111 | 6487.814815 | 38539.219282 | 227.093650 | 3.814815 | 0.000000 | 3.222222 | 1.108715 | 0.018871 |
| Qwen3.8 | poolact/restricted_search | moderate | naive | 230991.769231 | 25173.179487 | 9834.076814 | unknown (0/39) | 45.179487 | 24.512821 | unknown (0/39) | 0.819506 | 0.048776 |
| Qwen3.8 | poolact/restricted_search | moderate | cached | 250738.025641 | 23713.897436 | 9106.026165 | unknown (0/39) | 47.461538 | 25.717949 | unknown (0/39) | 0.758836 | 0.043727 |
| Qwen3.8 | poolact/restricted_search | moderate | poolact | 548091.333333 | 35190.794872 | 7867.017264 | unknown (0/39) | 44.487179 | 21.230769 | unknown (0/39) | 0.655585 | 0.009733 |
| Qwen3.8 | poolact/restricted_search | tight | naive | 34095.179487 | 7174.333333 | 3966.822959 | unknown (0/39) | 16.512821 | 9.743590 | unknown (0/39) | 1.101895 | 0.052547 |
| Qwen3.8 | poolact/restricted_search | tight | cached | 35458.282051 | 6880.897436 | 3905.680213 | unknown (0/39) | 16.410256 | 9.461538 | unknown (0/39) | 1.084911 | 0.067137 |
| Qwen3.8 | poolact/restricted_search | tight | poolact | 60483.846154 | 14122.641026 | 3915.714097 | unknown (0/39) | 16.538462 | 4.717949 | unknown (0/39) | 1.087698 | 0.016294 |
| Qwen3.8 | poolact/evidence_audit | moderate | naive | 367328.307692 | 44462.923077 | 11892.643388 | unknown (0/13) | 39.461538 | 19.230769 | unknown (0/13) | 0.991054 | 0.008589 |
| Qwen3.8 | poolact/evidence_audit | moderate | cached | 432017.769231 | 45707.307692 | 11904.439203 | unknown (0/13) | 44.384615 | 22.846154 | unknown (0/13) | 0.992037 | 0.004586 |
| Qwen3.8 | poolact/evidence_audit | moderate | poolact | 607184.846154 | 60782.153846 | 11360.052137 | unknown (0/13) | 37.769231 | 8.923077 | unknown (0/13) | 0.946671 | 0.012737 |
| Qwen3.8 | poolact/evidence_audit | tight | naive | 109687.000000 | 43988.384615 | 3572.513785 | unknown (0/13) | 11.846154 | 6.307692 | unknown (0/13) | 0.992365 | 0.000000 |
| Qwen3.8 | poolact/evidence_audit | tight | cached | 115658.846154 | 47583.000000 | 3529.017576 | unknown (0/13) | 11.846154 | 5.923077 | unknown (0/13) | 0.980283 | 0.008573 |
| Qwen3.8 | poolact/evidence_audit | tight | poolact | 121894.000000 | 45493.923077 | 3611.961734 | unknown (0/13) | 12.000000 | 3.230769 | unknown (0/13) | 1.003323 | 0.008856 |
| Qwen3.8 | poolact/tuning | moderate | naive | 635250.222222 | 57983.111111 | 336390.507575 | unknown (0/9) | 46.888889 | 0.666667 | unknown (0/9) | 0.950695 | 0.019584 |
| Qwen3.8 | poolact/tuning | moderate | cached | 669797.777778 | 61250.888889 | 344911.559275 | unknown (0/9) | 46.666667 | 0.333333 | unknown (0/9) | 0.979511 | 0.027357 |
| Qwen3.8 | poolact/tuning | moderate | poolact | 2087892.555556 | 120289.888889 | 283669.345161 | unknown (0/9) | 39.666667 | 1.888889 | unknown (0/9) | 0.816040 | 0.014731 |
| Qwen3.8 | poolact/tuning | tight | naive | 129447.666667 | 32709.666667 | 113055.235318 | unknown (0/9) | 12.111111 | 0.222222 | unknown (0/9) | 1.093464 | 0.095879 |
| Qwen3.8 | poolact/tuning | tight | cached | 141519.000000 | 37746.000000 | 112835.088630 | unknown (0/9) | 13.333333 | 0.222222 | unknown (0/9) | 1.111161 | 0.057537 |
| Qwen3.8 | poolact/tuning | tight | poolact | 293542.888889 | 54818.222222 | 104479.993761 | unknown (0/9) | 14.444444 | 0.222222 | unknown (0/9) | 1.027782 | 0.028719 |
| DeepSeek-0731 | expgym/restricted_search | free | single | 131940.369863 | 11589.178082 | 3387.712077 | 134.496908 | 17.547945 | 0.027397 | 17.547945 | 不适用 | 0.063256 |
| DeepSeek-0731 | expgym/restricted_search | moderate | single | 68977.479452 | 11360.534247 | 2568.349812 | 127.875105 | 12.794521 | 0.041096 | 12.273973 | 0.856117 | 0.076490 |
| DeepSeek-0731 | expgym/restricted_search | tight | single | 12432.958904 | 8252.520548 | 1064.204590 | 89.370928 | 4.643836 | 0.013699 | 3.739726 | 1.182450 | 0.121330 |
| DeepSeek-0731 | expgym/evidence_audit | free | single | 366150.871795 | 21262.435897 | 6914.979495 | 241.673945 | 23.128205 | 0.128205 | 23.128205 | 不适用 | 0.109717 |
| DeepSeek-0731 | expgym/evidence_audit | moderate | single | 137147.051282 | 17861.641026 | 2904.364756 | 192.190897 | 9.743590 | 0.000000 | 9.179487 | 0.968122 | 0.096219 |
| DeepSeek-0731 | expgym/evidence_audit | tight | single | 44672.102564 | 16333.564103 | 886.331050 | 175.489407 | 3.000000 | 0.000000 | 2.333333 | 0.984812 | 0.179548 |
| DeepSeek-0731 | expgym/tuning | free | single | 148796.740741 | 12851.222222 | 216689.802123 | 152.040070 | 16.407407 | 0.037037 | 16.407407 | 不适用 | 0.159228 |
| DeepSeek-0731 | expgym/tuning | moderate | single | 74453.037037 | 9823.407407 | 109647.200313 | 118.364281 | 9.740741 | 0.037037 | 9.370370 | 0.805942 | 0.127625 |
| DeepSeek-0731 | expgym/tuning | tight | single | 24947.666667 | 6140.740741 | 34420.824366 | 72.669557 | 4.074074 | 0.000000 | 3.629630 | 0.939236 | 0.239390 |
| DeepSeek-0731 | poolact/restricted_search | moderate | naive | 186091.435897 | 35565.974359 | 4945.457496 | unknown (0/39) | 24.923077 | 11.948718 | unknown (0/39) | 0.412121 | 0.308474 |
| DeepSeek-0731 | poolact/restricted_search | moderate | cached | 169259.128205 | 31060.666667 | 4688.736843 | unknown (0/39) | 25.076923 | 13.307692 | unknown (1/39) | 0.390728 | 0.323588 |
| DeepSeek-0731 | poolact/restricted_search | moderate | poolact | 126466.384615 | 32022.794872 | 2443.333261 | unknown (0/39) | 10.923077 | 4.461538 | unknown (0/39) | 0.203611 | 0.417162 |
| DeepSeek-0731 | poolact/restricted_search | tight | naive | 66929.128205 | 26095.974359 | 2333.695477 | unknown (0/39) | 11.538462 | 5.948718 | unknown (0/39) | 0.648249 | 0.370000 |
| DeepSeek-0731 | poolact/restricted_search | tight | cached | 54360.435897 | 26575.743590 | 2935.111190 | unknown (0/39) | 13.435897 | 7.435897 | unknown (2/39) | 0.815309 | 0.309256 |
| DeepSeek-0731 | poolact/restricted_search | tight | poolact | 80792.692308 | 33809.615385 | 2267.306043 | unknown (0/39) | 9.717949 | 4.846154 | unknown (0/39) | 0.629807 | 0.402962 |
| DeepSeek-0731 | poolact/evidence_audit | moderate | naive | 376721.692308 | 109929.461538 | 5595.334333 | unknown (0/13) | 18.846154 | 4.615385 | unknown (1/13) | 0.466278 | 0.353350 |
| DeepSeek-0731 | poolact/evidence_audit | moderate | cached | 473478.461538 | 82999.076923 | 7514.718550 | unknown (0/13) | 32.153846 | 9.846154 | unknown (1/13) | 0.626227 | 0.235076 |
| DeepSeek-0731 | poolact/evidence_audit | moderate | poolact | 302074.461538 | 84832.384615 | 2959.628886 | unknown (0/13) | 10.461538 | 1.615385 | unknown (2/13) | 0.246636 | 0.447477 |
| DeepSeek-0731 | poolact/evidence_audit | tight | naive | 249212.230769 | 104833.769231 | 2059.258741 | unknown (0/13) | 7.000000 | 2.538462 | unknown (1/13) | 0.572016 | 0.459612 |
| DeepSeek-0731 | poolact/evidence_audit | tight | cached | 194020.846154 | 82773.846154 | 1913.588035 | unknown (0/13) | 7.000000 | 2.153846 | unknown (1/13) | 0.531552 | 0.453801 |
| DeepSeek-0731 | poolact/evidence_audit | tight | poolact | 132750.769231 | 61874.000000 | 624.278457 | unknown (0/13) | 2.230769 | 0.692308 | unknown (2/13) | 0.173411 | 0.631380 |
| DeepSeek-0731 | poolact/tuning | moderate | naive | 269754.333333 | 72492.444444 | 66391.563171 | unknown (0/9) | 9.888889 | 0.666667 | unknown (1/9) | 0.188325 | 0.505538 |
| DeepSeek-0731 | poolact/tuning | moderate | cached | 278340.000000 | 77948.222222 | 94525.820157 | unknown (0/9) | 15.222222 | 1.666667 | unknown (3/9) | 0.336466 | 0.453267 |
| DeepSeek-0731 | poolact/tuning | moderate | poolact | 212592.333333 | 55006.666667 | 31728.029487 | unknown (0/9) | 5.111111 | 0.444444 | unknown (3/9) | 0.120280 | 0.586604 |
| DeepSeek-0731 | poolact/tuning | tight | naive | 229168.444444 | 72176.222222 | 46493.551731 | unknown (0/9) | 9.000000 | 2.222222 | unknown (1/9) | 0.492657 | 0.461251 |
| DeepSeek-0731 | poolact/tuning | tight | cached | 168160.333333 | 82649.222222 | 40665.060096 | unknown (0/9) | 6.666667 | 0.777778 | unknown (0/9) | 0.389056 | 0.470592 |
| DeepSeek-0731 | poolact/tuning | tight | poolact | 238965.888889 | 89996.333333 | 46509.283440 | unknown (0/9) | 6.777778 | 0.222222 | unknown (0/9) | 0.463469 | 0.465028 |


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

| 系统/场景 | 预算 | 策略 | 完成/计划 jobs | 全部 HTTP 尝试 | Input | Output | 模拟反馈秒合计 | 反馈尝试合计 | HTTP wall 秒合计（非历时） |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym/evidence_audit | free | single | 39/39 | 371 | 3285134 | 75439 | 99946.07177583501 | 332.0 | 2454.4249144550413 |
| expgym/evidence_audit | moderate | single | 39/39 | 262 | 2205144 | 79576 | 67093.41248040088 | 223.0 | 2344.896582468413 |
| expgym/evidence_audit | tight | single | 39/39 | 121 | 952864 | 65628 | 24675.410883892328 | 82.0 | 1726.1632637307048 |
| expgym/restricted_search | free | single | 73/73 | 904 | unknown；已知小计 5974680，未知尝试 1 | unknown；已知小计 76347，未知尝试 1 | 209049.00610168464 | 830.0 | 3733.349753221497 |
| expgym/restricted_search | moderate | single | 73/73 | 795 | 5117411 | 82445 | 170310.6373281777 | 722.0 | 3633.0573739716783 |
| expgym/restricted_search | tight | single | 73/73 | 383 | unknown；已知小计 2054198，未知尝试 1 | unknown；已知小计 35141，未知尝试 1 | 74246.56800188124 | 309.0 | 1613.954133898951 |
| expgym/tuning | free | single | 27/27 | 615 | unknown；已知小计 5095906，未知尝试 2 | unknown；已知小计 137952，未知尝试 2 | 5330582.137336936 | 586.0 | 4062.9821226922795 |
| expgym/tuning | moderate | single | 27/27 | 393 | 3124812 | 100124 | 3041573.2809130303 | 366.0 | 2958.6997842555866 |
| expgym/tuning | tight | single | 27/27 | 131 | 860621 | 47320 | 928698.3452399311 | 104.0 | 1327.3997807074338 |
| poolact/evidence_audit | moderate | cached | 13/13 | 310 | unknown；已知小计 2671645，未知尝试 1 | unknown；已知小计 108551，未知尝试 1 | 68460.04925244488 | 257.0 | 3203.8589063063264 |
| poolact/evidence_audit | moderate | naive | 13/13 | 391 | 3470015 | 130760 | 101924.39742436633 | 339.0 | 3836.1849236581475 |
| poolact/evidence_audit | moderate | poolact | 13/13 | 268 | 2707449 | 105678 | 64905.160214910284 | 216.0 | 2898.841161912307 |
| poolact/evidence_audit | tight | cached | 13/13 | 157 | unknown；已知小计 1221918，未知尝试 1 | unknown；已知小计 97082，未知尝试 1 | 29842.286407994106 | 104.0 | 2564.687980336137 |
| poolact/evidence_audit | tight | naive | 13/13 | 157 | 1237969 | 102436 | 31715.507345600054 | 105.0 | 2639.6175384605303 |
| poolact/evidence_audit | tight | poolact | 13/13 | 158 | 1260327 | 85984 | 31982.840207917616 | 106.0 | 2278.803262363188 |
| poolact/restricted_search | moderate | cached | 39/39 | 1690 | 10789611 | 167099 | 330736.7709207535 | 1534.0 | 7349.023319288157 |
| poolact/restricted_search | moderate | naive | 39/39 | 1644 | unknown；已知小计 10364037，未知尝试 1 | unknown；已知小计 163540，未知尝试 1 | 344116.82166794315 | 1487.0 | 7386.410864525475 |
| poolact/restricted_search | moderate | poolact | 39/39 | 1539 | 15436045 | 180817 | 268216.4057530649 | 1383.0 | 7496.8977288091555 |
| poolact/restricted_search | tight | cached | 39/39 | 855 | unknown；已知小计 4621210，未知尝试 1 | unknown；已知小计 84039，未知尝试 1 | 159272.25420684554 | 698.0 | 3990.015110853128 |
| poolact/restricted_search | tight | naive | 39/39 | 854 | unknown；已知小计 4598259，未知尝试 4 | unknown；已知小计 87107，未知尝试 4 | 158676.30626311526 | 694.0 | 4109.166595076211 |
| poolact/restricted_search | tight | poolact | 39/39 | 758 | 4682378 | 94073 | 142596.0547803063 | 602.0 | 3779.210785424337 |
| poolact/tuning | moderate | cached | 9/9 | 531 | unknown；已知小计 5417437，未知尝试 1 | unknown；已知小计 204696，未知尝试 1 | 2971709.8481445312 | 494.0 | 5174.5787232341245 |
| poolact/tuning | moderate | naive | 9/9 | 507 | 5098806 | 200164 | 2969344.0255737305 | 471.0 | 5217.966708665714 |
| poolact/tuning | moderate | poolact | 9/9 | 390 | 13724143 | 184948 | 2433914.348754883 | 355.0 | 4706.417301430367 |
| poolact/tuning | tight | cached | 9/9 | 178 | 1424817 | 88697 | 921115.6451416016 | 142.0 | 2273.5147542450577 |
| poolact/tuning | tight | naive | 9/9 | 170 | 1355593 | 89042 | 926999.3751220703 | 134.0 | 2360.358655168675 |
| poolact/tuning | tight | poolact | 9/9 | 150 | 1726362 | 73203 | 769471.1740722656 | 114.0 | 1886.0745772467926 |


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
