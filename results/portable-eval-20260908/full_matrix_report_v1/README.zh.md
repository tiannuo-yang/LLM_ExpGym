# Kimi-K3 与 GLM-5.3：ExpGym / PoolAct 全设置实验报告

本报告回答两个问题：**反馈预算收紧时，单 agent 的任务表现如何变化？在相同预算档位、相同 N=4 条件下，缓存复用与 PoolAct 协调各带来多少收益？**

实验类型为 Custom study：沿用论文的任务/机制比较思路，具体运行矩阵与生成设置以下文冻结记录为准，不作为论文数值的逐项精确复现。

这里展示实际完成的全部设置，而不是只列六个主比较：ExpGym 的 **Free / Moderate / Tight**，以及多 agent 的 **naive / cached / poolact × Moderate / Tight**。所有结果来自已发布的固定数据提交 [`6119f9d`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59)，本次仅重新组织汇总与报告，没有新增模型调用。

**存档入口：** [原始 dump 与聚合比较完整索引](ARCHIVE_INDEX.md) · [机器可读索引（含逐包 SHA / 大小）](ARCHIVE_INDEX.json)。正文第 7 节提供同一索引的导航与存档方式。

## 1. 实验设置与覆盖

### 1.1 两模型采用相同实验矩阵

| 系统 | 任务 | 实际项目数 | 成本档位 | 方法 / agent 数 | 重复设置 |
| --- | --- | ---: | --- | --- | --- |
| ExpGym | Search | 73 题：39 whois + 34 whatis | Free / Moderate / Tight | single，N=1 | 每题每设置 1 次 |
| ExpGym | Evidence Audit | 13 文档 | Free / Moderate / Tight | single，N=1 | 每文档 3 个固定 hypothesis 顺序，先在文档内平均 |
| ExpGym | HPO / NAS | 9 任务 | Free / Moderate / Tight | single，N=1 | 3 个 seed blocks |
| 多 agent | Search | 39 道 whois | Moderate / Tight | naive / cached / poolact，均 N=4 | 每题每设置 1 个独立池 |
| 多 agent | Evidence Audit | 13 文档 | Moderate / Tight | naive / cached / poolact，均 N=4 | 默认 hypothesis 顺序，每设置 1 个独立池 |
| 多 agent | NAS | NASBench101 A / B / C | Moderate / Tight | naive / cached / poolact，均 N=4 | 每任务每设置 3 个独立池 |

9 个单 agent HPO / NAS 任务为：ParamNet adult、higgs、letter；NASBench101 A、B、C；NASBench201 cifar10-valid、cifar100、imagenet16-120。Search 使用 PhantomWiki seed2 / seed3 两个固定 world，所有选题身份可在存档的 `manifest.json` 中查到。

每模型共 **705 次 invocation、783 个 logical outcomes、1,881 个 agent traces**。其中 ExpGym 为 339 次 invocation / 417 个顺序或重复结果，多 agent 为 366 个池 / 1,464 个成员结果。Audit 的三个顺序同属一次 invocation，因此这些计数单位不同。K3 最终数据由原 697 个完成项和批准恢复的固定 8 项组成；两模型均使用全部规定的最终结果，不增加重抽样。

### 1.2 Free、Moderate、Tight 的具体含义

| 档位 | 模拟反馈预算 B | 是否向 agent 展示成本 / 剩余预算 |
| --- | --- | --- |
| Free (`cost_free`) | 无有限预算上限 | 否 |
| Moderate (`cost_moderate`) | 10 × c_base | 是 |
| Tight (`cost_tight`) | 3 × c_base | 是 |

Search / Audit 的 c_base=300 模拟秒，对应 Moderate 3000、Tight 900 模拟秒；HPO / NAS 使用冻结 oracle 的任务级 reference-best evaluation cost。Free 仍有相同的 30 步 / 30 次评估上限，不是无限生成。这里控制的是**工具反馈预算与成本可见性**，不是把 GPU 时间或 token 上限改成三档。多 agent 三种方法使用相同 N=4 和同一单 agent 预算规则，未运行多 agent Free。

### 1.3 方法与生成配置

| 方法 | 实验含义 |
| --- | --- |
| naive | 四个 agent 独立探索，不共享观察缓存与探索图；结束后按任务规则聚合。 |
| cached | 共享已完成且当前模拟时间可见的相同工具调用结果，避免重复支付该次反馈的模拟成本。 |
| poolact | 在 cached 基础上提供共享探索图和协调决策；决策/claim 使用 reasoning lock，工具执行仍可并行。 |

| 配置 | Kimi-K3 | GLM-5.3 |
| --- | --- | --- |
| 模型服务 | 自部署 checkpoint，SGLang / OpenAI-compatible native tools | 同左 |
| Temperature / top-p | 1.0 / 1.0 | 1.0 / 0.95 |
| 每次生成 max_tokens | 32768 | 32768 |
| reasoning_effort 请求值 | `max` | `max` |
| chat_template_kwargs 请求值 | `{"thinking":true,"thinking_effort":"max"}` | `{"clear_thinking":false,"reasoning_effort":"max"}` |
| max_steps / max_evals | 30 / 30 | 30 / 30 |
| 单模型部署（本轮历史实验） | 8 节点 × 8 GPU；4 个 TP16 / EP16 副本 | 8 节点 × 8 GPU；4 个 TP16 / EP1 副本 |
| 调度上限（本轮历史实验） | 32 个独立 invocation | 32 个独立 invocation |

HPO seed-block 标签为 2200 / 2204 / 2208，池内四成员依次使用 block 标签至 +3；Search / Audit 使用首个 block，ExpGym Audit 三个顺序的标签为 2200 / 2201 / 2202。top-k 未显式设置；原生工具协议最多一次协议 repair，HTTP 重试上限 2。Pool 本地输入 context cap 为 131072 个近似 token（序列化消息字符数 ÷3，并计入工具 schema 的同口径估计；非精确 tokenizer 计数）；ExpGym 本地 cap 未另设，实际服务上下文和其他参数按冻结 profile。请求参数、选择器和原方法对照可查[设置明细](../full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/claim_setting_preflight_v1/EVIDENCE.json)。实际实验源码为 [`8dfea72`](https://github.com/tiannuo-yang/LLM_ExpGym/tree/8dfea72931d952ad90f1c722a83957ab23afc6bf)。后来改为每模型四节点双 TP16 的配置**不属于本报告这次 run**。

### 1.4 指标与汇总口径

- Search：集合 F1；Audit：EA 为精确证据集合准确率，LA 为标签准确率。表中 F1 / EA / LA 都是 0–1 的绝对分数，差值 0.01 相当于 1 个百分点。
- HPO / NAS：Gap 是冻结 oracle 归一化后的效用，**越高越好**；raw performance 是原任务分数，不把 Gap 当作越低越好的 regret。采用本轮冻结的 `legacy` final policy。
- MI 为四个成员分数的平均，MV 为原投票规则的聚合得分，BoN 为四成员最佳分数。NAS 同时展示 MI 与 BoN，Search / Audit 同时给出 MI 与投票结果。
- 先平均同一 item 的重复，再对 item 等权平均；ExpGym Audit 已先将三个固定顺序在文档内平均。HPO 的分任务表覆盖全部三个 blocks，逐 block 结果另列。单 agent 9 个 HPO 任务与多 agent 3 个 NAS 任务不直接混为相同任务全集。

这是在本轮两模型和既定任务上的描述性结果，不新增显著性检验；各表保留实际的正、零和负差值。完整逐题、逐文档、逐池指标及原比较定义均在第 7 节索引中。

## 2. 主问题一：反馈预算收紧，ExpGym 是否退化？

两模型在 Search、Audit 的证据指标和九任务 HPO 总体上，都呈现 **Free > Moderate > Tight** 的均值次序。Search 的影响尤其大：whois F1 从 Free 到 Tight 分别下降约 48.87 / 45.21 个百分点；whatis 也有同方向下降。HPO 九任务平均 Gap 分别下降 8.83 / 11.84 points。

Moderate 的完整列很重要：它说明性能不是只在两个端点间不同。例如 K3 Audit EA 为 0.8944 → 0.6878 → 0.5158；GLM 为 0.6848 → 0.6787 → 0.5023，后者主要损失集中在 Tight。具体任务的变化幅度不同，以下全表用于观察这一结构。

### 2.1 Search / Audit

| 场景 | 切片 | 预算 | 指标 | items / R1 | Kimi-K3 | GLM-5.3 |
| --- | --- | --- | --- | --- | --- | --- |
| restricted_search | all | Free | f1 | 73 | 0.635911 | 0.651102 |
| restricted_search | all | Moderate | f1 | 73 | 0.496169 | 0.532761 |
| restricted_search | all | Tight | f1 | 73 | 0.157561 | 0.192341 |
| restricted_search | whois | Free | f1 | 39 | 0.658862 | 0.682651 |
| restricted_search | whois | Moderate | f1 | 39 | 0.573004 | 0.642842 |
| restricted_search | whois | Tight | f1 | 39 | 0.170136 | 0.230575 |
| restricted_search | whatis | Free | f1 | 34 | 0.609584 | 0.614914 |
| restricted_search | whatis | Moderate | f1 | 34 | 0.408034 | 0.406491 |
| restricted_search | whatis | Tight | f1 | 34 | 0.143137 | 0.148485 |
| evidence_audit | all | Free | evidence_acc | 13 | 0.894419 | 0.684766 |
| evidence_audit | all | Free | label_acc | 13 | 0.926094 | 0.692308 |
| evidence_audit | all | Moderate | evidence_acc | 13 | 0.687783 | 0.678733 |
| evidence_audit | all | Moderate | label_acc | 13 | 0.853695 | 0.760181 |
| evidence_audit | all | Tight | evidence_acc | 13 | 0.515837 | 0.502262 |
| evidence_audit | all | Tight | label_acc | 13 | 0.794872 | 0.736048 |

表内 Audit 的 R1 指一个已平均三个顺序的文档级分析单元，不是只运行了一个顺序。

### 2.2 HPO：全体、任务家族及九个任务

| 切片 | 预算 | items（每项 R=3） | K3 Gap | K3 raw | GLM Gap | GLM raw |
| --- | --- | --- | --- | --- | --- | --- |
| all | Free | 9 | 98.512910 | 0.830424 | 97.911143 | 0.829110 |
| all | Moderate | 9 | 94.230104 | 0.819970 | 96.154560 | 0.824766 |
| all | Tight | 9 | 89.683717 | 0.814494 | 86.066889 | 0.801956 |
| family=nasbench101 | Free | 3 | 98.692013 | 0.941770 | 99.057476 | 0.943450 |
| family=nasbench101 | Moderate | 3 | 97.857181 | 0.937407 | 97.736559 | 0.936239 |
| family=nasbench101 | Tight | 3 | 94.968099 | 0.918447 | 90.761443 | 0.898441 |
| family=nasbench201 | Free | 3 | 99.770835 | 0.706212 | 98.637164 | 0.704850 |
| family=nasbench201 | Moderate | 3 | 97.076629 | 0.703764 | 96.486852 | 0.702974 |
| family=nasbench201 | Tight | 3 | 94.660569 | 0.701261 | 88.037331 | 0.692131 |
| family=paramnet | Free | 3 | 97.075883 | 0.843288 | 96.038788 | 0.839029 |
| family=paramnet | Moderate | 3 | 87.756501 | 0.818739 | 94.240269 | 0.835086 |
| family=paramnet | Tight | 3 | 79.422483 | 0.823773 | 79.401892 | 0.815296 |
| task=hpobench:nasbench101:A | Free | 1 | 99.258011 | 0.940861 | 99.579172 | 0.943120 |
| task=hpobench:nasbench101:A | Moderate | 1 | 98.079371 | 0.932570 | 99.003299 | 0.939069 |
| task=hpobench:nasbench101:A | Tight | 1 | 90.517091 | 0.879374 | 85.756650 | 0.845887 |
| task=hpobench:nasbench101:B | Free | 1 | 97.454035 | 0.942463 | 97.969343 | 0.943777 |
| task=hpobench:nasbench101:B | Moderate | 1 | 96.585000 | 0.940249 | 97.467138 | 0.942497 |
| task=hpobench:nasbench101:B | Tight | 1 | 95.759638 | 0.938145 | 89.995192 | 0.923455 |
| task=hpobench:nasbench101:C | Free | 1 | 99.363994 | 0.941985 | 99.623912 | 0.943454 |
| task=hpobench:nasbench101:C | Moderate | 1 | 98.907173 | 0.939403 | 96.739239 | 0.927150 |
| task=hpobench:nasbench101:C | Tight | 1 | 98.627567 | 0.937823 | 96.532487 | 0.925982 |
| task=hpobench:nasbench201:cifar10-valid | Free | 1 | 100.000000 | 0.916067 | 99.391401 | 0.915582 |
| task=hpobench:nasbench201:cifar10-valid | Moderate | 1 | 93.657170 | 0.911018 | 93.880509 | 0.911196 |
| task=hpobench:nasbench201:cifar10-valid | Tight | 1 | 90.206581 | 0.908271 | 93.657170 | 0.911018 |
| task=hpobench:nasbench201:cifar100 | Free | 1 | 100.000000 | 0.735033 | 99.171863 | 0.734022 |
| task=hpobench:nasbench201:cifar100 | Moderate | 1 | 100.000000 | 0.735033 | 99.171863 | 0.734022 |
| task=hpobench:nasbench201:cifar100 | Tight | 1 | 97.479188 | 0.731956 | 90.981498 | 0.724022 |
| task=hpobench:nasbench201:imagenet16-120 | Free | 1 | 99.312504 | 0.467537 | 97.348228 | 0.464944 |
| task=hpobench:nasbench201:imagenet16-120 | Moderate | 1 | 97.572717 | 0.465241 | 96.408183 | 0.463704 |
| task=hpobench:nasbench201:imagenet16-120 | Tight | 1 | 96.295938 | 0.463556 | 79.473326 | 0.441352 |
| task=hpobench:paramnet:adult:steps | Free | 1 | 97.856995 | 0.852849 | 95.601586 | 0.851920 |
| task=hpobench:paramnet:adult:steps | Moderate | 1 | 87.329255 | 0.848512 | 95.414265 | 0.851843 |
| task=hpobench:paramnet:adult:steps | Tight | 1 | 77.355993 | 0.844404 | 72.013444 | 0.842204 |
| task=hpobench:paramnet:higgs:steps | Free | 1 | 94.148953 | 0.715973 | 95.829008 | 0.717435 |
| task=hpobench:paramnet:higgs:steps | Moderate | 1 | 89.082285 | 0.711564 | 92.269269 | 0.714337 |
| task=hpobench:paramnet:higgs:steps | Tight | 1 | 66.679766 | 0.692066 | 78.314729 | 0.702193 |
| task=hpobench:paramnet:letter:steps | Free | 1 | 99.221702 | 0.961043 | 96.685771 | 0.947731 |
| task=hpobench:paramnet:letter:steps | Moderate | 1 | 86.857961 | 0.896141 | 95.037272 | 0.939077 |
| task=hpobench:paramnet:letter:steps | Tight | 1 | 94.231691 | 0.934848 | 87.877503 | 0.901493 |

raw 列保留原任务分值供查验；跨任务结论以归一化 Gap 为主。

### 2.3 HPO：三个 seed blocks

outer0 / 1 / 2 对应标签 2200 / 2204 / 2208；每格是九任务等权均值。SD 是三个 block 均值的样本描述标准差，不是置信区间，也不代表已验证的独立随机重复。

| 模型 | 系统 | 预算 | 策略 | 指标 | outer0 | outer1 | outer2 | 描述 SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | expgym | Free | single | gap | 98.323337 | 98.022659 | 99.192735 | 0.607637 |
| kimi-k3 | expgym | Moderate | single | gap | 91.888380 | 96.720920 | 94.081011 | 2.419717 |
| kimi-k3 | expgym | Tight | single | gap | 94.484532 | 84.994278 | 89.572341 | 4.746108 |
| glm-5.3 | expgym | Free | single | gap | 97.433902 | 97.962348 | 98.337178 | 0.453810 |
| glm-5.3 | expgym | Moderate | single | gap | 94.984465 | 98.060230 | 95.418984 | 1.664598 |
| glm-5.3 | expgym | Tight | single | gap | 86.858680 | 88.946705 | 82.395281 | 3.346713 |

## 3. 主问题二：缓存复用与协调，分别改善了什么？

这里比较相同预算档位下的三个 N=4 方法。**cached−naive** 衡量仅加入观察复用时的描述性差异；**poolact−cached** 展示进一步加入图/协调后的差异；**poolact−naive** 对应完整机制的总体比较。它们都是本轮观察到的策略差异，不把两个独立 run 的均值之差解释为已经隔离所有因素的因果估计。

各场景总体比较如下；Search / Audit 差值单位为绝对分数，NAS 为 Gap points。所有差值使用未四舍五入的均值计算。

| 模型 | 预算 | 指标 | cached − naive | poolact − cached | poolact − naive |
| --- | --- | --- | ---: | ---: | ---: |
| kimi-k3 | Moderate | Search F1-MV | -0.003885 | +0.025375 | +0.021490 |
| kimi-k3 | Moderate | Audit EA-MV | +0.027149 | +0.171946 | +0.199095 |
| kimi-k3 | Moderate | Audit LA-MV | +0.013575 | +0.036199 | +0.049774 |
| kimi-k3 | Moderate | NAS Gap-MI | -0.077726 | +0.595188 | +0.517462 |
| kimi-k3 | Moderate | NAS Gap-BoN | -0.147632 | +0.031723 | -0.115908 |
| kimi-k3 | Tight | Search F1-MV | -0.025641 | +0.117094 | +0.091453 |
| kimi-k3 | Tight | Audit EA-MV | -0.004525 | +0.081448 | +0.076923 |
| kimi-k3 | Tight | Audit LA-MV | -0.004525 | +0.036199 | +0.031674 |
| kimi-k3 | Tight | NAS Gap-MI | -0.146798 | +1.940211 | +1.793413 |
| kimi-k3 | Tight | NAS Gap-BoN | +0.373105 | -0.001140 | +0.371965 |
| glm-5.3 | Moderate | Search F1-MV | +0.036447 | +0.000694 | +0.037141 |
| glm-5.3 | Moderate | Audit EA-MV | +0.036199 | +0.131222 | +0.167421 |
| glm-5.3 | Moderate | Audit LA-MV | +0.009050 | +0.045249 | +0.054299 |
| glm-5.3 | Moderate | NAS Gap-MI | +0.188003 | +0.904495 | +1.092498 |
| glm-5.3 | Moderate | NAS Gap-BoN | +0.108255 | +0.264798 | +0.373053 |
| glm-5.3 | Tight | Search F1-MV | +0.000000 | +0.091453 | +0.091453 |
| glm-5.3 | Tight | Audit EA-MV | +0.013575 | +0.090498 | +0.104072 |
| glm-5.3 | Tight | Audit LA-MV | +0.022624 | +0.013575 | +0.036199 |
| glm-5.3 | Tight | NAS Gap-MI | +2.222250 | +9.994021 | +12.216271 |
| glm-5.3 | Tight | NAS Gap-BoN | +0.739115 | +3.914245 | +4.653360 |

### 3.1 Search：Tight 下 PoolAct 的提升最清楚

whois Tight 的投票 F1，K3 从 naive 0.2129 提升至 poolact 0.3043，GLM 从 0.2086 提升至 0.3001，两者均提高约 9.15 个百分点。Moderate 下基线已有约 0.62–0.65，提升幅度较小。cached 的表现依模型与预算而变：仅有缓存复用并不等价于完整协调的收益。

每格为 39 道 whois 的等权均值。无 Pool whatis 设置。

| 模型 | 预算 | 策略 | F1 MI | F1 MV |
| --- | --- | --- | --- | --- |
| kimi-k3 | Moderate | naive | 0.623870 | 0.645919 |
| kimi-k3 | Moderate | cached | 0.632024 | 0.642034 |
| kimi-k3 | Moderate | poolact | 0.640914 | 0.667409 |
| kimi-k3 | Tight | naive | 0.201002 | 0.212871 |
| kimi-k3 | Tight | cached | 0.192511 | 0.187230 |
| kimi-k3 | Tight | poolact | 0.272395 | 0.304324 |
| glm-5.3 | Moderate | naive | 0.599406 | 0.620278 |
| glm-5.3 | Moderate | cached | 0.620111 | 0.656725 |
| glm-5.3 | Moderate | poolact | 0.659089 | 0.657419 |
| glm-5.3 | Tight | naive | 0.203255 | 0.208597 |
| glm-5.3 | Tight | cached | 0.203255 | 0.208597 |
| glm-5.3 | Tight | poolact | 0.247425 | 0.300050 |

### 3.2 Audit：证据收集能力的增益大于标签指标的增益

Moderate 的投票 EA，K3 为 naive 0.7376 → poolact 0.9367，GLM 为 0.8100 → 0.9774；Tight 下也同方向提升。EA 与 LA 一起报告，可区分“判断标签正确”与“找齐对应证据”的能力。成员均值与投票值同时列出，用于观察改善是否仅存在于最终投票这一层。

每格为 13 个文档默认顺序的等权均值。

| 模型 | 预算 | 策略 | EA MI | EA MV | LA MI | LA MV |
| --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | Moderate | naive | 0.702489 | 0.737557 | 0.894796 | 0.923077 |
| kimi-k3 | Moderate | cached | 0.670814 | 0.764706 | 0.840498 | 0.936652 |
| kimi-k3 | Moderate | poolact | 0.908371 | 0.936652 | 0.928733 | 0.972851 |
| kimi-k3 | Tight | naive | 0.545249 | 0.552036 | 0.822398 | 0.841629 |
| kimi-k3 | Tight | cached | 0.542986 | 0.547511 | 0.811086 | 0.837104 |
| kimi-k3 | Tight | poolact | 0.602941 | 0.628959 | 0.846154 | 0.873303 |
| glm-5.3 | Moderate | naive | 0.654977 | 0.809955 | 0.757919 | 0.927602 |
| glm-5.3 | Moderate | cached | 0.668552 | 0.846154 | 0.753394 | 0.936652 |
| glm-5.3 | Moderate | poolact | 0.802036 | 0.977376 | 0.808824 | 0.981900 |
| glm-5.3 | Tight | naive | 0.549774 | 0.588235 | 0.792986 | 0.868778 |
| glm-5.3 | Tight | cached | 0.585973 | 0.601810 | 0.869910 | 0.891403 |
| glm-5.3 | Tight | poolact | 0.607466 | 0.692308 | 0.798643 | 0.904977 |

### 3.3 NAS：成员平均效用与 best-of-4 分开看

在完整 NAS101 A/B/C 上，Tight 的 Gap-MI 从 naive 到 poolact，K3 为 94.2583 → 96.0517，GLM 为 83.9603 → 96.1766。GLM 的成员平均表现改善更大。BoN 回答的是另一问题：只取四个成员中的最好配置，是否仍有增益？其起点通常更高，所以 MI 的改善不必等量反映在 BoN 上。下面同时列出总体、A/B/C 和三个 blocks，避免用单个任务代替全部 NAS 设置。

all 即 NAS101 三任务等权；不含 ParamNet/NAS201。BoN 与 MI 均原样保留，不能只看最高值。

| 模型 | 切片 | 预算 | 策略 | Gap MI | Gap BoN | raw MI | raw BoN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | all | Moderate | naive | 98.038866 | 98.986955 | 0.938288 | 0.943153 |
| kimi-k3 | all | Moderate | cached | 97.961140 | 98.839323 | 0.937575 | 0.942315 |
| kimi-k3 | all | Moderate | poolact | 98.556328 | 98.871046 | 0.941256 | 0.942805 |
| kimi-k3 | all | Tight | naive | 94.258262 | 97.993150 | 0.919430 | 0.938976 |
| kimi-k3 | all | Tight | cached | 94.111464 | 98.366255 | 0.916669 | 0.940167 |
| kimi-k3 | all | Tight | poolact | 96.051676 | 98.365115 | 0.929105 | 0.939919 |
| kimi-k3 | task=hpobench:nasbench101:A | Moderate | naive | 98.287414 | 99.319713 | 0.934033 | 0.941295 |
| kimi-k3 | task=hpobench:nasbench101:A | Moderate | cached | 97.813188 | 99.134610 | 0.930697 | 0.939993 |
| kimi-k3 | task=hpobench:nasbench101:A | Moderate | poolact | 99.263154 | 99.621889 | 0.940897 | 0.943421 |
| kimi-k3 | task=hpobench:nasbench101:A | Tight | naive | 93.427698 | 98.807122 | 0.899848 | 0.937689 |
| kimi-k3 | task=hpobench:nasbench101:A | Tight | cached | 91.237326 | 98.864077 | 0.884440 | 0.938090 |
| kimi-k3 | task=hpobench:nasbench101:A | Tight | poolact | 95.504557 | 98.691632 | 0.914458 | 0.936877 |
| kimi-k3 | task=hpobench:nasbench101:B | Moderate | naive | 96.818635 | 97.755357 | 0.940844 | 0.943231 |
| kimi-k3 | task=hpobench:nasbench101:B | Moderate | cached | 96.872130 | 97.676749 | 0.940981 | 0.943031 |
| kimi-k3 | task=hpobench:nasbench101:B | Moderate | poolact | 97.211667 | 97.593781 | 0.941846 | 0.942820 |
| kimi-k3 | task=hpobench:nasbench101:B | Tight | naive | 92.227822 | 96.135197 | 0.929145 | 0.939103 |
| kimi-k3 | task=hpobench:nasbench101:B | Tight | cached | 93.119782 | 97.047906 | 0.931418 | 0.941429 |
| kimi-k3 | task=hpobench:nasbench101:B | Tight | poolact | 93.599063 | 97.205119 | 0.932639 | 0.941829 |
| kimi-k3 | task=hpobench:nasbench101:C | Moderate | naive | 99.010548 | 99.885793 | 0.939987 | 0.944934 |
| kimi-k3 | task=hpobench:nasbench101:C | Moderate | cached | 99.198101 | 99.706609 | 0.941047 | 0.943921 |
| kimi-k3 | task=hpobench:nasbench101:C | Moderate | poolact | 99.194164 | 99.397468 | 0.941025 | 0.942174 |
| kimi-k3 | task=hpobench:nasbench101:C | Tight | naive | 97.119267 | 99.037133 | 0.929298 | 0.940138 |
| kimi-k3 | task=hpobench:nasbench101:C | Tight | cached | 97.977285 | 99.186781 | 0.934147 | 0.940983 |
| kimi-k3 | task=hpobench:nasbench101:C | Tight | poolact | 99.051407 | 99.198595 | 0.940218 | 0.941050 |
| glm-5.3 | all | Moderate | naive | 97.873330 | 99.007686 | 0.937173 | 0.942712 |
| glm-5.3 | all | Moderate | cached | 98.061333 | 99.115941 | 0.938197 | 0.943324 |
| glm-5.3 | all | Moderate | poolact | 98.965828 | 99.380739 | 0.942421 | 0.944478 |
| glm-5.3 | all | Tight | naive | 83.960328 | 93.809666 | 0.880532 | 0.920903 |
| glm-5.3 | all | Tight | cached | 86.182578 | 94.548781 | 0.888600 | 0.923040 |
| glm-5.3 | all | Tight | poolact | 96.176599 | 98.463026 | 0.928628 | 0.941020 |
| glm-5.3 | task=hpobench:nasbench101:A | Moderate | naive | 97.771660 | 99.215297 | 0.930405 | 0.940560 |
| glm-5.3 | task=hpobench:nasbench101:A | Moderate | cached | 97.880822 | 99.049178 | 0.931173 | 0.939392 |
| glm-5.3 | task=hpobench:nasbench101:A | Moderate | poolact | 98.993806 | 99.520635 | 0.939002 | 0.942708 |
| glm-5.3 | task=hpobench:nasbench101:A | Tight | naive | 88.907337 | 94.397901 | 0.868050 | 0.906673 |
| glm-5.3 | task=hpobench:nasbench101:A | Tight | cached | 87.932388 | 94.459601 | 0.861192 | 0.907107 |
| glm-5.3 | task=hpobench:nasbench101:A | Tight | poolact | 95.258942 | 99.224789 | 0.912730 | 0.940627 |
| glm-5.3 | task=hpobench:nasbench101:B | Moderate | naive | 96.762956 | 98.248830 | 0.940702 | 0.944489 |
| glm-5.3 | task=hpobench:nasbench101:B | Moderate | cached | 96.848113 | 98.174594 | 0.940919 | 0.944300 |
| glm-5.3 | task=hpobench:nasbench101:B | Moderate | poolact | 98.202974 | 98.716097 | 0.944372 | 0.945680 |
| glm-5.3 | task=hpobench:nasbench101:B | Tight | naive | 71.553333 | 88.785528 | 0.876458 | 0.920373 |
| glm-5.3 | task=hpobench:nasbench101:B | Tight | cached | 75.460710 | 90.785619 | 0.886415 | 0.925470 |
| glm-5.3 | task=hpobench:nasbench101:B | Tight | poolact | 94.632951 | 96.912531 | 0.935274 | 0.941084 |
| glm-5.3 | task=hpobench:nasbench101:C | Moderate | naive | 99.085373 | 99.558932 | 0.940410 | 0.943087 |
| glm-5.3 | task=hpobench:nasbench101:C | Moderate | cached | 99.455064 | 100.124052 | 0.942500 | 0.946281 |
| glm-5.3 | task=hpobench:nasbench101:C | Moderate | poolact | 99.700703 | 99.905485 | 0.943888 | 0.945045 |
| glm-5.3 | task=hpobench:nasbench101:C | Tight | naive | 91.420315 | 98.245569 | 0.897088 | 0.935664 |
| glm-5.3 | task=hpobench:nasbench101:C | Tight | cached | 95.154636 | 98.401123 | 0.918194 | 0.936543 |
| glm-5.3 | task=hpobench:nasbench101:C | Tight | poolact | 98.637904 | 99.251758 | 0.937881 | 0.941351 |

三个 seed blocks 的 NAS101 A/B/C 等权结果如下；SD 口径同第 2.3 节。逐 task × block 明细见 [by_outerseed.csv](by_outerseed.csv)。

| 模型 | 系统 | 预算 | 策略 | 指标 | outer0 | outer1 | outer2 | 描述 SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | poolact | Moderate | naive | gap_mi | 98.159365 | 97.682031 | 98.275201 | 0.314409 |
| kimi-k3 | poolact | Moderate | naive | gap_bon | 98.929687 | 99.008280 | 99.022896 | 0.050130 |
| kimi-k3 | poolact | Moderate | cached | gap_mi | 98.189185 | 97.876493 | 97.817742 | 0.199665 |
| kimi-k3 | poolact | Moderate | cached | gap_bon | 98.999939 | 98.619248 | 98.898781 | 0.197187 |
| kimi-k3 | poolact | Moderate | poolact | gap_mi | 98.742041 | 98.409035 | 98.517909 | 0.169795 |
| kimi-k3 | poolact | Moderate | poolact | gap_bon | 99.203580 | 98.778343 | 98.631216 | 0.297230 |
| kimi-k3 | poolact | Tight | naive | gap_mi | 95.204981 | 95.935980 | 91.633827 | 2.302029 |
| kimi-k3 | poolact | Tight | naive | gap_bon | 98.382865 | 97.934448 | 97.662139 | 0.363931 |
| kimi-k3 | poolact | Tight | cached | gap_mi | 94.012988 | 95.230677 | 93.090729 | 1.073367 |
| kimi-k3 | poolact | Tight | cached | gap_bon | 98.556372 | 98.499508 | 98.042884 | 0.281487 |
| kimi-k3 | poolact | Tight | poolact | gap_mi | 96.017289 | 96.675142 | 95.462595 | 0.607004 |
| kimi-k3 | poolact | Tight | poolact | gap_bon | 98.509911 | 98.153972 | 98.431462 | 0.187015 |
| glm-5.3 | poolact | Moderate | naive | gap_mi | 98.284886 | 97.116195 | 98.218909 | 0.656527 |
| glm-5.3 | poolact | Moderate | naive | gap_bon | 98.659706 | 99.337451 | 99.025902 | 0.339239 |
| glm-5.3 | poolact | Moderate | cached | gap_mi | 98.313975 | 98.089126 | 97.780897 | 0.267624 |
| glm-5.3 | poolact | Moderate | cached | gap_bon | 99.041402 | 99.010835 | 99.295587 | 0.156326 |
| glm-5.3 | poolact | Moderate | poolact | gap_mi | 98.943264 | 98.786747 | 99.167472 | 0.191363 |
| glm-5.3 | poolact | Moderate | poolact | gap_bon | 99.303895 | 99.400526 | 99.437796 | 0.069109 |
| glm-5.3 | poolact | Tight | naive | gap_mi | 87.086990 | 81.378917 | 83.415077 | 2.892836 |
| glm-5.3 | poolact | Tight | naive | gap_bon | 93.425246 | 91.065575 | 96.938176 | 2.955113 |
| glm-5.3 | poolact | Tight | cached | gap_mi | 87.586956 | 86.326175 | 84.634604 | 1.481405 |
| glm-5.3 | poolact | Tight | cached | gap_bon | 97.310553 | 98.131415 | 88.204374 | 5.509725 |
| glm-5.3 | poolact | Tight | poolact | gap_mi | 96.015442 | 95.255042 | 97.259313 | 1.011807 |
| glm-5.3 | poolact | Tight | poolact | gap_bon | 98.309475 | 98.353883 | 98.725721 | 0.228581 |

## 4. 运行资源与反馈使用

性能表之外，资源表报告各档位/方法的平均反馈尝试、模拟反馈成本、token 与实际记录时长。单 agent 和四 agent 池的开销单位不同；三种 N=4 方法之间可以在同一表内比较，但不能仅因反馈预算相同就认为实际 token 开销相同。ExpGym Audit 的资源单元是三个顺序的均值，项目真实总消耗用下方独立成本账本，不从这些均值表简单相加。

从同 N=4 的实际记录看，PoolAct 的质量提升伴随额外协调开销。例如 Search Tight，K3 每池平均 output 从 naive 约 12,060 增至 17,289 tokens，GLM 从 43,355 增至 88,946；两者的池级记录墙钟也更长。因而本轮支持的是**受限反馈下的质量改善**，而不是“同样的实际推理时间或 token 总量下必然更省”。反馈复用降低模拟反馈消耗，与图上下文、额外推理和串行决策增加模型侧开销，可以同时发生。

以下均取同一分析单元的冻结遥测，再按 item/repeat 等权；不是整项 study 总账。Input/Output 为 token；reasoning 已包含于 Output，不能再相加。反馈秒是模拟工具反馈成本，不是 GPU 秒。Exp Audit 列为每文档三个 orders 的均值，不是三 orders 合计。

Pool input/output tokens、feedback成本/次数为四 agents 合计；Pool wall 是整个 pool 子进程实际 source_capture.elapsed_seconds，不是 agent wall 的 sum/max。Exp wall 为单 agent 实测（Audit再平均三个orders）。不能相加推导整个并行 study 实际耗时或 GPU-hour；总账另见主报告。每个 Pool 的 feedback_visible 原导出缺失，在 CSV 保留 unknown，未补零；本表展示可用的反馈尝试数。

Free 的反馈预算为无限且不展示成本，不意味着实际反馈成本为零。budget_utilization 保留在 CSV，有限预算下 Pool 为四 agents 总反馈成本/(4×单 agent 预算)；允许最后一次工具越界带来大于1的值。

| 模型 | 系统 | 场景 | 预算 | 策略 | Input tokens | Output tokens | 反馈秒 | 冻结 wall 秒 | 反馈尝试数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | expgym | restricted_search | Free | single | 99545.136986 | 9387.739726 | 3631.827073 | 664.067277 | 14.054795 |
| kimi-k3 | expgym | restricted_search | Moderate | single | 43586.767123 | 7193.082192 | 2525.175439 | 523.515513 | 9.958904 |
| kimi-k3 | expgym | restricted_search | Tight | single | 6940.410959 | 2861.712329 | 1012.913496 | 203.157551 | 3.753425 |
| kimi-k3 | expgym | evidence_audit | Free | single | 366956.589744 | 16024.974359 | 8327.956221 | 1086.338041 | 27.717949 |
| kimi-k3 | expgym | evidence_audit | Moderate | single | 104462.025641 | 14751.871795 | 2844.170369 | 1017.687354 | 9.435897 |
| kimi-k3 | expgym | evidence_audit | Tight | single | 22878.307692 | 8032.512821 | 850.588274 | 571.388226 | 2.820513 |
| kimi-k3 | expgym | tuning | Free | single | 230295.592593 | 14047.407407 | 252387.797068 | 825.945845 | 23.666667 |
| kimi-k3 | expgym | tuning | Moderate | single | 57097.444444 | 8961.444444 | 96667.251220 | 493.495243 | 8.111111 |
| kimi-k3 | expgym | tuning | Tight | single | 21049.037037 | 6563.111111 | 36051.521950 | 382.524720 | 3.814815 |
| kimi-k3 | poolact | restricted_search | Moderate | naive | 171855.666667 | 24429.564103 | 9643.410741 | 670.684804 | 39.384615 |
| kimi-k3 | poolact | restricted_search | Moderate | cached | 193728.256410 | 25506.128205 | 8963.780838 | 636.872697 | 41.051282 |
| kimi-k3 | poolact | restricted_search | Moderate | poolact | 469631.333333 | 39232.923077 | 7673.324528 | 2785.353798 | 40.666667 |
| kimi-k3 | poolact | restricted_search | Tight | naive | 30428.615385 | 12059.948718 | 4109.480041 | 384.863589 | 15.461538 |
| kimi-k3 | poolact | restricted_search | Tight | cached | 35100.794872 | 13563.769231 | 4007.590673 | 468.324156 | 16.256410 |
| kimi-k3 | poolact | restricted_search | Tight | poolact | 73846.153846 | 17289.384615 | 3886.969286 | 1169.436990 | 17.461538 |
| kimi-k3 | poolact | evidence_audit | Moderate | naive | 435431.692308 | 59997.076923 | 11537.166336 | 1771.345564 | 38.307692 |
| kimi-k3 | poolact | evidence_audit | Moderate | cached | 506641.076923 | 59882.538462 | 10966.121039 | 1551.636591 | 43.846154 |
| kimi-k3 | poolact | evidence_audit | Moderate | poolact | 670641.692308 | 76833.461538 | 11228.417970 | 5380.948324 | 37.615385 |
| kimi-k3 | poolact | evidence_audit | Tight | naive | 94498.384615 | 36806.846154 | 3153.365251 | 1039.522642 | 10.461538 |
| kimi-k3 | poolact | evidence_audit | Tight | cached | 104495.000000 | 40671.076923 | 3219.343615 | 1207.165748 | 10.769231 |
| kimi-k3 | poolact | evidence_audit | Tight | poolact | 123983.153846 | 47385.307692 | 3507.503484 | 3396.817980 | 11.615385 |
| kimi-k3 | poolact | tuning | Moderate | naive | 519038.333333 | 67688.333333 | 322161.705777 | 1608.792329 | 39.222222 |
| kimi-k3 | poolact | tuning | Moderate | cached | 512309.777778 | 63995.888889 | 309297.951823 | 1398.424206 | 38.444444 |
| kimi-k3 | poolact | tuning | Moderate | poolact | 1118384.333333 | 88541.222222 | 268570.794532 | 5582.461858 | 32.888889 |
| kimi-k3 | poolact | tuning | Tight | naive | 113636.888889 | 34181.000000 | 109658.326131 | 800.030740 | 12.666667 |
| kimi-k3 | poolact | tuning | Tight | cached | 113071.888889 | 35135.888889 | 114140.534058 | 867.783888 | 12.666667 |
| kimi-k3 | poolact | tuning | Tight | poolact | 169065.666667 | 33587.333333 | 105743.352919 | 1758.332952 | 12.222222 |
| glm-5.3 | expgym | restricted_search | Free | single | 169909.917808 | 19600.808219 | 4126.073236 | 494.852681 | 16.863014 |
| glm-5.3 | expgym | restricted_search | Moderate | single | 67510.958904 | 19054.767123 | 2558.468748 | 481.319470 | 10.287671 |
| glm-5.3 | expgym | restricted_search | Tight | single | 14507.273973 | 9697.479452 | 1056.824892 | 244.842457 | 4.054795 |
| glm-5.3 | expgym | evidence_audit | Free | single | 899925.666667 | 49681.974359 | 7895.183171 | 1256.699367 | 26.307692 |
| glm-5.3 | expgym | evidence_audit | Moderate | single | 468084.230769 | 84948.794872 | 2935.049756 | 2134.877804 | 9.794872 |
| glm-5.3 | expgym | evidence_audit | Tight | single | 110772.923077 | 49455.769231 | 907.450009 | 1261.353119 | 3.025641 |
| glm-5.3 | expgym | tuning | Free | single | 274232.037037 | 14701.185185 | 346971.654252 | 374.648285 | 29.407407 |
| glm-5.3 | expgym | tuning | Moderate | single | 184063.444444 | 27606.629630 | 113814.763947 | 620.089671 | 10.629630 |
| glm-5.3 | expgym | tuning | Tight | single | 37732.703704 | 16316.370370 | 37035.891735 | 403.254350 | 3.666667 |
| glm-5.3 | poolact | restricted_search | Moderate | naive | 302391.282051 | 82204.641026 | 10017.152159 | 889.069421 | 41.025641 |
| glm-5.3 | poolact | restricted_search | Moderate | cached | 355575.743590 | 83759.102564 | 9200.367612 | 840.881999 | 44.512821 |
| glm-5.3 | poolact | restricted_search | Moderate | poolact | 1062983.717949 | 135370.948718 | 8433.958196 | 3376.654692 | 47.153846 |
| glm-5.3 | poolact | restricted_search | Tight | naive | 45893.282051 | 43355.051282 | 4168.844006 | 531.803013 | 16.230769 |
| glm-5.3 | poolact | restricted_search | Tight | cached | 69631.128205 | 46091.564103 | 4144.983991 | 566.510133 | 17.615385 |
| glm-5.3 | poolact | restricted_search | Tight | poolact | 240859.076923 | 88946.358974 | 4024.406994 | 2257.047684 | 20.410256 |
| glm-5.3 | poolact | evidence_audit | Moderate | naive | 1798701.769231 | 322716.615385 | 11668.482933 | 2641.934361 | 38.846154 |
| glm-5.3 | poolact | evidence_audit | Moderate | cached | 2465750.923077 | 352803.461538 | 10778.941689 | 2982.409317 | 47.076923 |
| glm-5.3 | poolact | evidence_audit | Moderate | poolact | 1828379.923077 | 287668.000000 | 11390.704547 | 7175.411588 | 38.384615 |
| glm-5.3 | poolact | evidence_audit | Tight | naive | 456518.538462 | 207078.538462 | 3584.775565 | 1825.328098 | 11.923077 |
| glm-5.3 | poolact | evidence_audit | Tight | cached | 490287.307692 | 211146.230769 | 3570.146708 | 1663.473940 | 12.384615 |
| glm-5.3 | poolact | evidence_audit | Tight | poolact | 422295.153846 | 231944.307692 | 3559.264010 | 5667.666078 | 11.846154 |
| glm-5.3 | poolact | tuning | Moderate | naive | 988802.111111 | 197910.666667 | 338082.847551 | 1745.712838 | 38.666667 |
| glm-5.3 | poolact | tuning | Moderate | cached | 1071169.666667 | 215092.777778 | 327973.409776 | 1772.964828 | 39.444444 |
| glm-5.3 | poolact | tuning | Moderate | poolact | 3115054.777778 | 322813.888889 | 318969.753086 | 7034.944031 | 43.666667 |
| glm-5.3 | poolact | tuning | Tight | naive | 369815.333333 | 133198.555556 | 113389.873281 | 1299.392815 | 13.888889 |
| glm-5.3 | poolact | tuning | Tight | cached | 244441.444444 | 87543.111111 | 117391.549025 | 965.025405 | 13.666667 |
| glm-5.3 | poolact | tuning | Tight | poolact | 457954.555556 | 130600.000000 | 107524.511929 | 2708.759140 | 15.555556 |

### 4.1 本轮有效结果的总体模型用量

| 模型 | 有效 invocation / logical / agents | 已持久化请求数 | Input tokens | Output tokens | 其中 reasoning tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| Kimi-K3 | 705 / 783 / 1881 | 16,387 | 124,643,382 | 15,971,159 | 13,781,826 |
| GLM-5.3 | 705 / 783 / 1881 | 18,403 | 323,702,359 | 61,759,454 | 59,754,394 |

reasoning 已包含在 output 中，不重复相加。GLM 的生成总量明显更大，因此“题数相同”不代表推理工作量相同。完整尝试成本也已存档：K3 包含原失败尝试的已知 input/output 小计为 126,556,991 / 16,272,997，另有 63 次用量未知；GLM 完整尝试与有效结果相同。三次相关 Slurm allocation 合计 2601.88 GPU-hours（含加载、验证、空闲及执行），它不是 formal-only 的有效 GPU 利用量。详细账本在第 7 节。

## 5. 围绕主张的归纳

1. **ExpGym 的核心现象在两模型上成立：** 固定步骤上限下，反馈预算从 Free 经 Moderate 收紧到 Tight，Search、证据检索和 HPO 总体质量下降。三档完整结果说明了退化发生在哪一段，而不只是给出一个 Free−Tight 差值。
2. **并行池中的共享与协调具有实用收益：** 相比同 N=4 的 naive，PoolAct 提高两模型 Search / Audit 的投票质量，以及 NAS 的成员平均效用。Search 和 NAS 的改善在 Tight 更突出，Audit 在两个档位均改善。全表同时保留 BoN，以区分改善成员整体水平和改善最终最佳候选。
3. **只加入缓存并不能替代协调：** cached 是必要的中间对照，其结果表明收益依任务和预算而异；从 cached 到 poolact 的完整列，才显示图/协调机制在本轮设置下增加了多少结果质量。

结论对应这两模型、上述固定任务和本轮生成设置。本文围绕全部设置给出可读汇总，不替换原六主比较的定义，也不把未运行的方法/档位补成结果。

## 6. 表格文件与生成方法

[全部绝对聚合指标](aggregate_metrics.csv) 包含系统、模型、场景、任务分组、档位、策略、指标、均值和分母；[逐 seed-block 表](by_outerseed.csv) 保留重复层的数值。[独立表格附件](TABLES.md) 与本文表格同源。原 `metrics.csv` 则保留逐 item 指标，原 `effects.csv` 保留全部 514 项比较 / 模型。

本次输入固定清单见 [INPUTS.json](INPUTS.json)，生成器为 [aggregate_settings.py](aggregate_settings.py)；汇总核对结果见 [aggregate_checks.json](aggregate_checks.json)。生成器只读取固定 Git 提交中的分析产物，不调用模型、scorer 或工具环境，不修改旧文件。原始分数、策略和分母保持不变；缺失值不当作零，不从汇总中悄悄剔除。

## 7. 原始 dump、聚合比较与恢复：完整存档索引

**完整索引附件是本报告的一部分：** [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md) 列出全部 73 个 bundle、分析文件及恢复说明；[ARCHIVE_INDEX.json](ARCHIVE_INDEX.json) 列出全部 556 个 tar 分片及相应 member 清单的固定 Git 路径、大小、已有 SHA-256。下表是常用直接入口。

| 模型 | 全部原始 dump / 恢复入口 | 逐 item 绝对指标 | 全部聚合比较 | 配对明细 / 来源 |
| --- | --- | --- | --- | --- |
| Kimi-K3 | [完整 collection](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/INDEX.kimi-k3-composite-v1.json) · [恢复说明](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/FULL_DELIVERY.zh.md) | [metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/metrics.csv) | [effects.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/effects.csv) · [results.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/results.json) | [paired_rows.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/paired_rows.csv) · [source_index.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/source_index.json) |
| GLM-5.3 | [完整 collection](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/payload/collection/INDEX.json) · [恢复说明](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/FULL_DELIVERY.zh.md) | [metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/metrics.csv) | [effects.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/effects.csv) · [results.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/results.json) | [paired_rows.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/paired_rows.csv) · [source_index.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/source_index.json) |

| 模型 | bundle | tar 分片 | 原文件数 | 原字节 | 压缩字节 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kimi-K3 | 36 | 268 | 66,643 | 1,751,137,861 | 305,870,108 |
| GLM-5.3 | 37 | 288 | 71,634 | 3,467,116,893 | 772,603,212 |
| 合计 | 73 | 556 | 138,277 | 5,218,254,754 | 1,078,473,320 |

压缩载荷约 **1.078 GB**，原件约 **5.218 GB**（十进制，外层 CSV / JSON / 报告另计）。K3 的 36 包已包含旧 34 包和固定 8 项恢复 / 新 controls 两包，不重复把旧包再加一次。原文件数包含归档 controls，不是独立试验数。

原全部比较入口每模型有 **514 行**，含质量、资源和缺失项；ExpGym 原比较表是 Free→Tight，Moderate 的绝对值在 metrics 及本报告全表中。PoolAct 原比较表以 naive 为 baseline，包含 cached 和 poolact，不能把它误读为只跑了 baseline。

[双模型总成本账本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/dual_model_analysis_fixed8_v2/COSTS.json) · [K3 全部尝试账本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/ALL_ATTEMPT_COST_LEDGER.json) · [GLM 导出 / 全部尝试证据](https://github.com/tiannuo-yang/LLM_ExpGym/blob/6119f9d136c9ed1f06a7bedd7371be0deb9b5d59/results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2/EXPORT_EVIDENCE.json)。完整请求/回复在原始 dump 中；规范化 records 和 agent 终态投影不是 HTTP 原始记录的替代物。

存档建议：保留 results 分支的完整 clone 和本报告目录，并记录本次报告提交；以原数据提交 `6119f9d136c9ed1f06a7bedd7371be0deb9b5d59` 固定原档身份。只下载 tar 会漏掉外层分析表和恢复工具；具体取回、定位单条原件和解释器要求见完整索引。此次只核对既有清单与 Git 元数据，不把索引汇总说成重新解压、重跑或重算所有原始评分。

## 8. 验收记录

本报告已完成一次成稿后独立核对；审阅者未导入作者聚合器，而是从冻结输入另行计算。

| 验收项 | 结果 |
| --- | --- |
| 实际矩阵及完整覆盖 | 两模型各 705 invocation / 783 logical / 1,881 agents；全部规定档位、策略、任务与重复均纳入。 |
| 汇总可复算 | 5 个生成文件逐字节一致；原 1,028 项比较的 baseline / target 与新均值对齐。 |
| 独立数字核对 | 2,270 行聚合、5,494 行 block 结果、正文 900 个数值格通过；含 20 行 × 3 策略差值及全部资源表。 |
| 逻辑与设置说明 | 结论对应完整表格；已澄清 Pool context cap 为近似 token，而非字符上限。成本与时长使用各自原始单位。 |
| 存档索引 | 73 bundle / 556 tar；1,322 个引用文件的 Git 路径/声明大小和相关小索引校验通过，无 K3 旧包重复计数。 |
| 链接与变更范围 | 原数据链接固定提交，未修改原结果；本次仅新增报告、索引、聚合附件及入口导航。 |

机器可读核对记录见 [VALIDATION.json](VALIDATION.json)，执行计划见 [PLAN.zh.md](PLAN.zh.md)。本次遵循仓库 `expgym-runner` 的冻结输入与适量验收流程：**0 模型调用、0 GPU 分配、0 scorer 重跑、0 tar 解压或重打包**。
