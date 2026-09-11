# deepseek-v4-flash-0731：ExpGym / PoolAct 全设置描述性报告

本报告只展示冻结分析结果，不新增实验、不重评分、不恢复 raw。属于固定已知任务的 Custom study，不自动等于 paper-exact reproduction。输入身份冻结与回顾性矩阵不构成预注册或显著性证据。

## 1. 主要发现与适用范围

本次数据支持两个明确但不同的结论：ExpGym 的 Search F1 与 Audit evidence accuracy 在预算收紧时退化；PoolAct 的收益具有场景依赖，并未稳定优于 naive/cached。Search F1 从 Free 的 0.438134 降至 Tight 的 0.169184（下降 26.895 个百分点），Audit evidence accuracy 从 0.639517 降至 0.475113（下降 16.440 个百分点）。Pool 的 Tight Search F1-MV 为 naive 0.025641、cached 0.042735、poolact 0.074409；但 Moderate Search 的 PoolAct 较 naive 低 1.282 个百分点，Audit 的 Moderate/Tight EA-MV 较 naive 分别低 25.792/42.986 个百分点。HPO/NAS 的完整分母端点存在真实缺失最终配置，不能用已知子集替代总体结论。以下完整列出全部设置、端点和负向比较；这些是本固定样本的描述性差异，不是显著性或跨模型普适性证明。

上述退化结论限定在明确端点，不覆盖所有Audit指标：label accuracy从Free的0.668175升至Moderate的0.755656、Tight的0.702866；对应绝对值和全部方向均保留在下文。证据准确率与标签准确率不能混作同一指标。

主要展示端点（展示选择，不冒充事前注册）：ExpGym 的 F1 / EA / Gap，Free−Tight 为正向 2、零 0、负向 0、unknown 1；PoolAct 的 F1-MV / EA-MV / Gap-MI，两个预算下 poolact−naive 为正向 1、零 0、负向 3、unknown 2。所有端点和相邻档位/缓存对照见后文，包含负值和 unknown。

这里 ExpGym 的正差表示预算收紧后下降，PoolAct 的正差表示在该固定比较中改善。汇总改善不代表每个任务或每次重复都改善；本模型的方向也不能替代其他模型的证据。未完成或不可评分的完整端点不以已知子集均值代替。

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | evidence_acc | cost_free − cost_tight | +0.164404 | fraction | +16.4404 | 13/13 | 0 | 0.164404 |
| expgym | restricted_search | all/all | cost_free | f1 | cost_free − cost_tight | +0.26895 | fraction | +26.895 | 73/73 | 0 | 0.26895 |
| expgym | tuning | all/all | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 19/27 | 8 | 7.46699 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mv | poolact − naive | -0.257919 | fraction | -25.7919 | 13/13 | 0 | -0.257919 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mv | poolact − naive | -0.429864 | fraction | -42.9864 | 13/13 | 0 | -0.429864 |
| poolact | restricted_search | all/all | cost_moderate | f1_mv | poolact − naive | -0.0128205 | fraction | -1.28205 | 39/39 | 0 | -0.0128205 |
| poolact | restricted_search | all/all | cost_tight | f1_mv | poolact − naive | +0.0487682 | fraction | +4.87682 | 39/39 | 0 | 0.0487682 |
| poolact | tuning | all/all | cost_moderate | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 40.5782 |


## 2. 实际设置、覆盖和分析单元

固定分母为 **783 个执行槽位、1881 个 agent 槽位、705 个分析单元**；已完成执行 783 / 783。执行完成不等于分数完整，质量表另列 known/expected/missing。

| 系统 | 场景 | item 数 | 档位 | 策略 | N | outerrep 标签 | 执行槽 | 分析单元 | agent 槽 | 执行完成 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | 13 | &#91;"cost_free","cost_moderate","cost_tight"&#93; | &#91;"single"&#93; | &#91;1&#93; | &#91;0&#93; | 117 | 39 | 117 | 117 |
| expgym | restricted_search | 73 | &#91;"cost_free","cost_moderate","cost_tight"&#93; | &#91;"single"&#93; | &#91;1&#93; | &#91;0&#93; | 219 | 219 | 219 | 219 |
| expgym | tuning | 9 | &#91;"cost_free","cost_moderate","cost_tight"&#93; | &#91;"single"&#93; | &#91;1&#93; | &#91;0,1,2&#93; | 81 | 81 | 81 | 81 |
| poolact | evidence_audit | 13 | &#91;"cost_moderate","cost_tight"&#93; | &#91;"cached","naive","poolact"&#93; | &#91;4&#93; | &#91;0&#93; | 78 | 78 | 312 | 78 |
| poolact | restricted_search | 39 | &#91;"cost_moderate","cost_tight"&#93; | &#91;"cached","naive","poolact"&#93; | &#91;4&#93; | &#91;0&#93; | 234 | 234 | 936 | 234 |
| poolact | tuning | 3 | &#91;"cost_moderate","cost_tight"&#93; | &#91;"cached","naive","poolact"&#93; | &#91;4&#93; | &#91;0,1,2&#93; | 54 | 54 | 216 | 54 |


ExpGym Audit 每文档的三种固定顺序拆成三个进程，报告中只平均一次；不是三组独立文档。Search 与 Pool Audit 为 R1；tuning 的 outerrep 0/1/2 对应三个 R1 stage 的 seed block 2200/2204/2208。种子只是请求标签，不证明独立或可重复生成。N=4 的池是一个分析结果，不是四次独立重复。

冻结源码的 PoolAct 协议为 paper-graph-lock-v3：同 pool 的共享图注入、一次 LLM 决策与待执行动作登记由同一推理锁串行保护，工具执行在锁外。因此 PoolAct 内部的 LLM 并发与 naive/cached 不同；全局动态队列并行的是独立 pool，不能把队列 workers×N 直接当成 PoolAct 同时推理数。

两个系统的 all 不是同一任务全集：表中 Search 的 item 范围分别呈现，tuning 亦分别呈现；本报告不从两套 all 直接计算跨系统胜负，也不把旧双模型结果合并成相同样本。

实际计划、身份记录与服务计划：[coverage](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/coverage.json) · [oracle](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/provenance/oracle3.json) · [plan](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/queue_plan.json) · [provider_contract](https://github.com/tiannuo-yang/LLM_ExpGym/blob/629c85f02497403295747c8b0e76ad279162f417/results/deepseek-flash-0731-20260911/study/provider_contract.json) · [run_inputs](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/formal_v1/RUN_INPUTS.json) · [serving_plan](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/serving/launch02/plan.json)

源码提交 `5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8`；源码树 SHA256 `b040dd01fa8faec8e7ef0dbab349463a16f739daa4df9c42969001173580abac`。

### 2.1 模拟反馈预算与成本可见性

按已审阅冻结源码 demo_experiment.py:38–108 的具名档位：Free 无模拟反馈预算上限且成本隐藏；Moderate = 10×c_base、Tight = 3×c_base，二者成本可见。Search/Audit 的 c_base 固定为 300 模拟秒；全部九个 tuning 任务采用绑定 oracle3.json 的 best_cost。这里不使用缺失任务的 100 秒 fallback。

| 任务/场景 | 适用系统 | c_base（模拟秒） | Free（仅 ExpGym） | Moderate 每 agent（模拟秒；成本可见） | Tight 每 agent（模拟秒；成本可见） |
| --- | --- | --- | --- | --- | --- |
| restricted_search | expgym / poolact | 300 | 无上限；成本隐藏 | 3000 | 900 |
| evidence_audit | expgym / poolact | 300 | 无上限；成本隐藏 | 3000 | 900 |
| hpobench:nasbench101:A | expgym / poolact | 4944.15 | 无上限；成本隐藏 | 49441.5 | 14832.5 |
| hpobench:nasbench101:B | expgym / poolact | 10302.6 | 无上限；成本隐藏 | 103026 | 30907.7 |
| hpobench:nasbench101:C | expgym / poolact | 11203.9 | 无上限；成本隐藏 | 112039 | 33611.6 |
| hpobench:nasbench201:cifar10-valid | expgym | 11310 | 无上限；成本隐藏 | 113100 | 33930.1 |
| hpobench:nasbench201:cifar100 | expgym | 18639.4 | 无上限；成本隐藏 | 186394 | 55918.1 |
| hpobench:nasbench201:imagenet16-120 | expgym | 50264.2 | 无上限；成本隐藏 | 502642 | 150793 |
| hpobench:paramnet:adult:steps | expgym | 28.5389 | 无上限；成本隐藏 | 285.389 | 85.6167 |
| hpobench:paramnet:higgs:steps | expgym | 234.357 | 无上限；成本隐藏 | 2343.57 | 703.071 |
| hpobench:paramnet:letter:steps | expgym | 98.2705 | 无上限；成本隐藏 | 982.705 | 294.811 |


以上是模拟反馈预算，不是推理墙钟或 GPU 时间。PoolAct 只运行 Moderate/Tight，N=4 的每个 agent 各有同一 B；不能称整个池共用一个 B，N×B 是池级名义预算口径而非实际开销测量。Free 仍有步骤、评估次数和输出等限制，不表示无限推理。此预算解释只接受已审阅源码提交且拒绝 custom、beta/time_budget 或成本可见性覆盖；切换源码需重新核对契约。

### 2.2 服务与请求配置

| 服务计划字段 | 冻结值 |
| --- | --- |
| model | deepseek-v4-flash-0731 |
| checkpoint | /lustrefs/users/runner/chufan.shi/tau_vision/ckpts/DeepSeek-V4-Flash-0731 |
| nodes × GPUs/node | 4 × 8 |
| replicas / TP / PP / EP | &#91;4,8,1,1&#93; |
| server context_length | 1.04858e+06 |
| reasoning_parser | deepseek-v4 |
| tool_call_parser | deepseekv4 |
| server_args | &#91;"--moe-runner-backend","marlin","--attention-backend","dsv4","--page-size","256","--chunked-prefill-size","4096","--dist-timeout","1800"&#93; |
| weight_payload_hashes_verified（RUN_INPUTS 声明） | false |


以上是绑定的服务配置：4 节点 × 每节点 8 GPU，共四个独立的单节点 TP8 副本，不是跨四节点的一份模型。量化与协议检查范围见以下冻结 provider_contract；本报告不把配置值或 HTTP health 自动提升为真实 native 验收。

| Provider 契约字段 | 冻结记录 |
| --- | --- |
| expert weight format / backend / arithmetic | &#91;"FP4 experts (mixed checkpoint)","Marlin","W4A16 MoE"&#93; |
| checkpoint 同时包含的 dense 权重格式 | FP8 |
| vendor high/max recommended output | 384K |
| 实际每请求输出上限 | 32768 |
| forced-final tool_choice | none |
| speculative decoding / MTP used | &#91;false,false&#93; |
| assistant_reasoning_history_retained | {"evidence":&#91;"native_wire","cpu_encoder_replay"&#93;,"observed":true} |
| rendered_tool_definitions_retained | {"evidence":&#91;"cpu_encoder_replay"&#93;,"observed":true} |
| tool_history_retained | {"evidence":&#91;"native_wire","cpu_encoder_replay"&#93;,"observed":true} |
| wire_tools_retained | {"evidence":&#91;"native_wire"&#93;,"observed":true} |
| 运行方 native 验收记录状态 | passed |
| 运行方记录的实际检查范围 | 4 replicas × 2 native cases (auto/named-tool) × 2 requests = 16 delivered requests/16 attempts，其中8次tool_choice=none continuation。核对已保存native request payload及精确assistant/tool history，并以冻结实际encoder做CPU重放：工具定义、已有非空reasoning和tool content保留，prompt token counts相符；replay新增API=0、CUDA=false。两个evidence role指向同一复合检查记录，不是两份独立证据；非网络抓包，server未dump token IDs；非独立科学验证，未外推正式矩阵或长上下文。 |


FP4 仅描述 experts；该混合 checkpoint 同时包含 FP8 dense 等格式，W4A16 指 Marlin 的 MoE 执行路径，不是全模型统一 4-bit 算术。本次不开 speculative decoding，也不使用 MTP。

最大 thinking 使用 reasoning_effort=max 与 thinking=true；每请求输出最多 32768 token。厂商 checkpoint README 对 high/max 推荐最大输出长度为 384K token，本 Custom study 沿用跨模型比较的 32768 上限，未采用厂商该推荐长输出设置；因此不是厂商性能的完全复现。冻结 server context_length=1048576 也不是最大输出长度，两者不可互换；该服务值直接读取实际 serving plan，不沿用其他模型的上限。

上表逐项记录 dsv4 forced-final（tool_choice=none）是否保留 wire tools、渲染后工具定义、assistant reasoning 与 tool 历史。每项观察值都绑定其实际 wire dump / CPU 实际 encoder 重放的证据；没有验证的属性保持 null。本报告只转述运行方冻结验证状态和具体范围，不将自身离线生成视为新增 native 实测。证据入口：[cpu_encoder_replay](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/native_contract_replay.json) · [native_wire](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/native_contract_replay.json)

| 系统 | 参数 | 冻结计划值集合 | 口径 |
| --- | --- | --- | --- |
| expgym | backend | "openai" | 计划请求值；null 表示该参数未显式记录 |
| expgym | tool_protocol | "native" | 计划请求值；null 表示该参数未显式记录 |
| expgym | missing_final_policy | "task-abstention-v1" | 计划请求值；null 表示该参数未显式记录 |
| expgym | tuning_final_policy | "legacy" | 计划请求值；null 表示该参数未显式记录 |
| expgym | temperature | null | 计划请求值；null 表示该参数未显式记录 |
| expgym | temperature_eval | 1.0 | 计划请求值；null 表示该参数未显式记录 |
| expgym | temperature_tuning | 1.0 | 计划请求值；null 表示该参数未显式记录 |
| expgym | top_p | 0.95 | 计划请求值；null 表示该参数未显式记录 |
| expgym | top_k | null | 计划请求值；null 表示该参数未显式记录 |
| expgym | reasoning_effort | "max" | 计划请求值；null 表示该参数未显式记录 |
| expgym | chat_template_kwargs | {"thinking":true} | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_tokens | 32768 | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_steps | 30 | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_evals | 30 | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_context_tokens | null | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_protocol_retries | 1 | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_retries | 2 | 计划请求值；null 表示该参数未显式记录 |
| expgym | request_timeout | 7200.0 | 计划请求值；null 表示该参数未显式记录 |
| expgym | retry_base_seconds | 3.0 | 计划请求值；null 表示该参数未显式记录 |
| expgym | retry_max_seconds | 30.0 | 计划请求值；null 表示该参数未显式记录 |
| expgym | prompt_cache_scope | "job" | 计划请求值；null 表示该参数未显式记录 |
| expgym | prompt_cache_key_field | "cache_salt" | 计划请求值；null 表示该参数未显式记录 |
| poolact | backend | "openai" | 计划请求值；null 表示该参数未显式记录 |
| poolact | tool_protocol | "native" | 计划请求值；null 表示该参数未显式记录 |
| poolact | missing_final_policy | "task-abstention-v1" | 计划请求值；null 表示该参数未显式记录 |
| poolact | tuning_final_policy | "legacy" | 计划请求值；null 表示该参数未显式记录 |
| poolact | temperature | 1.0 | 计划请求值；null 表示该参数未显式记录 |
| poolact | temperature_eval | null | 计划请求值；null 表示该参数未显式记录 |
| poolact | temperature_tuning | null | 计划请求值；null 表示该参数未显式记录 |
| poolact | top_p | 0.95 | 计划请求值；null 表示该参数未显式记录 |
| poolact | top_k | null | 计划请求值；null 表示该参数未显式记录 |
| poolact | reasoning_effort | "max" | 计划请求值；null 表示该参数未显式记录 |
| poolact | chat_template_kwargs | {"thinking":true} | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_tokens | 32768 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_steps | 30 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_evals | 30 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_context_tokens | 131072 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_protocol_retries | 1 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_retries | 2 | 计划请求值；null 表示该参数未显式记录 |
| poolact | request_timeout | 7200.0 | 计划请求值；null 表示该参数未显式记录 |
| poolact | retry_base_seconds | 3.0 | 计划请求值；null 表示该参数未显式记录 |
| poolact | retry_max_seconds | 30.0 | 计划请求值；null 表示该参数未显式记录 |
| poolact | prompt_cache_scope | null | 计划请求值；null 表示该参数未显式记录 |
| poolact | prompt_cache_key_field | "cache_salt" | 计划请求值；null 表示该参数未显式记录 |


请求字段不等于服务端已验证的行为。上下文字段也不自动代表精确 tokenizer 计数；未显式给出的其他 runner 默认值，本报告不从旧报告反推，需沿固定源码/原件入口核查。预算秒数已经由上方冻结源码/绑定 oracle 表明确给出，不从结果均值倒推。

## 3. 预算收紧与 ExpGym 表现

绝对分数按 item 内先平均重复、再对 item 等权平均；Audit 先按文档折叠顺序一次。F1 / EA / LA 与 raw performance 为 0–1 分数；Gap 是效用型归一化分数（越高越好），每个 agent 先按冻结 oracle 截零后再算 MI，不能从汇总 raw performance 重新反推。

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | single | evidence_acc | fraction | 0.639517 | 13/13 | 0 | 13 | 0.639517 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | label_acc | fraction | 0.668175 | 13/13 | 0 | 13 | 0.668175 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | evidence_acc | fraction | 0.586727 | 13/13 | 0 | 13 | 0.586727 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | label_acc | fraction | 0.755656 | 13/13 | 0 | 13 | 0.755656 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | evidence_acc | fraction | 0.475113 | 13/13 | 0 | 13 | 0.475113 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | label_acc | fraction | 0.702866 | 13/13 | 0 | 13 | 0.702866 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | f1 | fraction | 0.438134 | 73/73 | 0 | 73 | 0.438134 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | f1 | fraction | 0.421117 | 73/73 | 0 | 73 | 0.421117 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | f1 | fraction | 0.169184 | 73/73 | 0 | 73 | 0.169184 | 1 / unknown |
| expgym | tuning | all/all | cost_free | single | gap | Gap points | unknown | 20/27 | 7 | 9 | 81.7185 | 3 / unknown |
| expgym | tuning | all/all | cost_free | single | raw_perf | fraction | unknown | 20/27 | 7 | 9 | 0.758444 | 3 / unknown |
| expgym | tuning | all/all | cost_moderate | single | gap | Gap points | unknown | 25/27 | 2 | 9 | 79.3797 | 3 / unknown |
| expgym | tuning | all/all | cost_moderate | single | raw_perf | fraction | unknown | 25/27 | 2 | 9 | 0.72011 | 3 / unknown |
| expgym | tuning | all/all | cost_tight | single | gap | Gap points | unknown | 25/27 | 2 | 9 | 81.8907 | 3 / unknown |
| expgym | tuning | all/all | cost_tight | single | raw_perf | fraction | unknown | 25/27 | 2 | 9 | 0.790709 | 3 / unknown |


以下包含 Free−Moderate、Free−Tight、Moderate−Tight。差值保留原单位；fraction 的 0.02 在百分点列为 2，不是 0.02%。

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | evidence_acc | cost_free − cost_moderate | +0.0527903 | fraction | +5.27903 | 13/13 | 0 | 0.0527903 |
| expgym | evidence_audit | all/all | cost_free | evidence_acc | cost_free − cost_tight | +0.164404 | fraction | +16.4404 | 13/13 | 0 | 0.164404 |
| expgym | evidence_audit | all/all | cost_free | label_acc | cost_free − cost_moderate | -0.0874811 | fraction | -8.74811 | 13/13 | 0 | -0.0874811 |
| expgym | evidence_audit | all/all | cost_free | label_acc | cost_free − cost_tight | -0.0346908 | fraction | -3.46908 | 13/13 | 0 | -0.0346908 |
| expgym | evidence_audit | all/all | cost_moderate | evidence_acc | cost_moderate − cost_tight | +0.111614 | fraction | +11.1614 | 13/13 | 0 | 0.111614 |
| expgym | evidence_audit | all/all | cost_moderate | label_acc | cost_moderate − cost_tight | +0.0527903 | fraction | +5.27903 | 13/13 | 0 | 0.0527903 |
| expgym | restricted_search | all/all | cost_free | f1 | cost_free − cost_moderate | +0.0170172 | fraction | +1.70172 | 73/73 | 0 | 0.0170172 |
| expgym | restricted_search | all/all | cost_free | f1 | cost_free − cost_tight | +0.26895 | fraction | +26.895 | 73/73 | 0 | 0.26895 |
| expgym | restricted_search | all/all | cost_moderate | f1 | cost_moderate − cost_tight | +0.251933 | fraction | +25.1933 | 73/73 | 0 | 0.251933 |
| expgym | tuning | all/all | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 19/27 | 8 | 2.95881 |
| expgym | tuning | all/all | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 19/27 | 8 | 7.46699 |
| expgym | tuning | all/all | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 19/27 | 8 | 0.0256491 |
| expgym | tuning | all/all | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 19/27 | 8 | -0.0131797 |
| expgym | tuning | all/all | cost_moderate | gap | cost_moderate − cost_tight | unknown | Gap points | 不适用 | 23/27 | 4 | -1.68244 |
| expgym | tuning | all/all | cost_moderate | raw_perf | cost_moderate − cost_tight | unknown | fraction | unknown | 23/27 | 4 | -0.0677845 |


## 4. 缓存、协调与 PoolAct 表现

两个实际预算档位均展示 naive / cached / poolact，保留 MI 与 MV/BoN 的区别。MI/MV/BoN 都是池级端点；任一必需 agent 不可评分时，完整池端点保持 unknown。

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| poolact | evidence_audit | all/all | cost_moderate | cached | evidence_acc_mi | fraction | 0.364253 | 13/13 | 0 | 13 | 0.364253 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | evidence_acc_mv | fraction | 0.588235 | 13/13 | 0 | 13 | 0.588235 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | label_acc_mi | fraction | 0.447964 | 13/13 | 0 | 13 | 0.447964 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | label_acc_mv | fraction | 0.737557 | 13/13 | 0 | 13 | 0.737557 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | evidence_acc_mi | fraction | 0.322398 | 13/13 | 0 | 13 | 0.322398 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | evidence_acc_mv | fraction | 0.59276 | 13/13 | 0 | 13 | 0.59276 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | label_acc_mi | fraction | 0.400452 | 13/13 | 0 | 13 | 0.400452 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | label_acc_mv | fraction | 0.78733 | 13/13 | 0 | 13 | 0.78733 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | evidence_acc_mi | fraction | 0.109729 | 13/13 | 0 | 13 | 0.109729 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | evidence_acc_mv | fraction | 0.334842 | 13/13 | 0 | 13 | 0.334842 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | label_acc_mi | fraction | 0.149321 | 13/13 | 0 | 13 | 0.149321 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | label_acc_mv | fraction | 0.447964 | 13/13 | 0 | 13 | 0.447964 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | evidence_acc_mi | fraction | 0.128959 | 13/13 | 0 | 13 | 0.128959 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | evidence_acc_mv | fraction | 0.371041 | 13/13 | 0 | 13 | 0.371041 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | label_acc_mi | fraction | 0.171946 | 13/13 | 0 | 13 | 0.171946 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | label_acc_mv | fraction | 0.502262 | 13/13 | 0 | 13 | 0.502262 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | evidence_acc_mi | fraction | 0.18552 | 13/13 | 0 | 13 | 0.18552 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | evidence_acc_mv | fraction | 0.497738 | 13/13 | 0 | 13 | 0.497738 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | label_acc_mi | fraction | 0.236425 | 13/13 | 0 | 13 | 0.236425 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | label_acc_mv | fraction | 0.692308 | 13/13 | 0 | 13 | 0.692308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | evidence_acc_mi | fraction | 0.0169683 | 13/13 | 0 | 13 | 0.0169683 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | evidence_acc_mv | fraction | 0.0678733 | 13/13 | 0 | 13 | 0.0678733 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | label_acc_mi | fraction | 0.0328054 | 13/13 | 0 | 13 | 0.0328054 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | label_acc_mv | fraction | 0.131222 | 13/13 | 0 | 13 | 0.131222 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | f1_mi | fraction | 0.169872 | 39/39 | 0 | 39 | 0.169872 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | f1_mv | fraction | 0.17094 | 39/39 | 0 | 39 | 0.17094 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | f1_mi | fraction | 0.0907692 | 39/39 | 0 | 39 | 0.0907692 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | f1_mv | fraction | 0.132479 | 39/39 | 0 | 39 | 0.132479 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | f1_mi | fraction | 0.0790598 | 39/39 | 0 | 39 | 0.0790598 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | f1_mv | fraction | 0.119658 | 39/39 | 0 | 39 | 0.119658 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | f1_mi | fraction | 0.0470085 | 39/39 | 0 | 39 | 0.0470085 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | f1_mv | fraction | 0.042735 | 39/39 | 0 | 39 | 0.042735 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | f1_mi | fraction | 0.025641 | 39/39 | 0 | 39 | 0.025641 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | f1_mv | fraction | 0.025641 | 39/39 | 0 | 39 | 0.025641 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | f1_mi | fraction | 0.0549271 | 39/39 | 0 | 39 | 0.0549271 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | f1_mv | fraction | 0.0744093 | 39/39 | 0 | 39 | 0.0744093 | 1 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | gap_bon | Gap points | unknown | 3/9 | 6 | 3 | 98.7191 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | gap_mi | Gap points | unknown | 3/9 | 6 | 3 | 90.8581 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_bon | fraction | unknown | 3/9 | 6 | 3 | 0.937191 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_mi | fraction | unknown | 3/9 | 6 | 3 | 0.867371 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | gap_bon | Gap points | unknown | 1/9 | 8 | 3 | 10.8189 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | gap_mi | Gap points | unknown | 1/9 | 8 | 3 | 2.70472 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_bon | fraction | unknown | 1/9 | 8 | 3 | 0.318743 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_mi | fraction | unknown | 1/9 | 8 | 3 | 0.0796858 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | gap_bon | Gap points | unknown | 1/9 | 8 | 3 | 97.8974 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | gap_mi | Gap points | unknown | 1/9 | 8 | 3 | 72.4394 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_bon | fraction | unknown | 1/9 | 8 | 3 | 0.93129 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_mi | fraction | unknown | 1/9 | 8 | 3 | 0.691548 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | gap_bon | Gap points | unknown | 1/9 | 8 | 3 | 85.7566 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | gap_mi | Gap points | unknown | 1/9 | 8 | 3 | 21.4392 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_bon | fraction | unknown | 1/9 | 8 | 3 | 0.845887 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_mi | fraction | unknown | 1/9 | 8 | 3 | 0.211472 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | gap_bon | Gap points | unknown | 2/9 | 7 | 3 | 86.5374 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | gap_mi | Gap points | unknown | 2/9 | 7 | 3 | 46.8368 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_bon | fraction | unknown | 2/9 | 7 | 3 | 0.88126 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_mi | fraction | unknown | 2/9 | 7 | 3 | 0.617626 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | gap_bon | Gap points | unknown | 2/9 | 7 | 3 | 85.1915 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | gap_mi | Gap points | unknown | 2/9 | 7 | 3 | 71.4656 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_bon | fraction | unknown | 2/9 | 7 | 3 | 0.88146 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_mi | fraction | unknown | 2/9 | 7 | 3 | 0.801737 | 3 / unknown |


cached−naive 描述共享缓存对照；poolact−cached 描述在该设置下进一步协调的差异；poolact−naive 是整体差异，不能据此分离所有机制或宣称相同 GPU 成本。

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mi | poolact − cached | -0.254525 | fraction | -25.4525 | 13/13 | 0 | -0.254525 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mv | poolact − cached | -0.253394 | fraction | -25.3394 | 13/13 | 0 | -0.253394 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mi | poolact − cached | -0.298643 | fraction | -29.8643 | 13/13 | 0 | -0.298643 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mv | poolact − cached | -0.289593 | fraction | -28.9593 | 13/13 | 0 | -0.289593 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mi | cached − naive | +0.0418552 | fraction | +4.18552 | 13/13 | 0 | 0.0418552 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mi | poolact − naive | -0.21267 | fraction | -21.267 | 13/13 | 0 | -0.21267 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mv | cached − naive | -0.00452489 | fraction | -0.452489 | 13/13 | 0 | -0.00452489 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mv | poolact − naive | -0.257919 | fraction | -25.7919 | 13/13 | 0 | -0.257919 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mi | cached − naive | +0.0475113 | fraction | +4.75113 | 13/13 | 0 | 0.0475113 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mi | poolact − naive | -0.251131 | fraction | -25.1131 | 13/13 | 0 | -0.251131 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mv | cached − naive | -0.0497738 | fraction | -4.97738 | 13/13 | 0 | -0.0497738 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mv | poolact − naive | -0.339367 | fraction | -33.9367 | 13/13 | 0 | -0.339367 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mi | poolact − cached | -0.111991 | fraction | -11.1991 | 13/13 | 0 | -0.111991 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mv | poolact − cached | -0.303167 | fraction | -30.3167 | 13/13 | 0 | -0.303167 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mi | poolact − cached | -0.13914 | fraction | -13.914 | 13/13 | 0 | -0.13914 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mv | poolact − cached | -0.371041 | fraction | -37.1041 | 13/13 | 0 | -0.371041 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mi | cached − naive | -0.0565611 | fraction | -5.65611 | 13/13 | 0 | -0.0565611 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mi | poolact − naive | -0.168552 | fraction | -16.8552 | 13/13 | 0 | -0.168552 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mv | cached − naive | -0.126697 | fraction | -12.6697 | 13/13 | 0 | -0.126697 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mv | poolact − naive | -0.429864 | fraction | -42.9864 | 13/13 | 0 | -0.429864 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mi | cached − naive | -0.0644796 | fraction | -6.44796 | 13/13 | 0 | -0.0644796 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mi | poolact − naive | -0.20362 | fraction | -20.362 | 13/13 | 0 | -0.20362 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mv | cached − naive | -0.190045 | fraction | -19.0045 | 13/13 | 0 | -0.190045 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mv | poolact − naive | -0.561086 | fraction | -56.1086 | 13/13 | 0 | -0.561086 |
| poolact | restricted_search | all/all | cost_moderate | f1_mi | poolact − cached | -0.090812 | fraction | -9.0812 | 39/39 | 0 | -0.090812 |
| poolact | restricted_search | all/all | cost_moderate | f1_mv | poolact − cached | -0.0512821 | fraction | -5.12821 | 39/39 | 0 | -0.0512821 |
| poolact | restricted_search | all/all | cost_moderate | f1_mi | cached − naive | +0.0791026 | fraction | +7.91026 | 39/39 | 0 | 0.0791026 |
| poolact | restricted_search | all/all | cost_moderate | f1_mi | poolact − naive | -0.0117094 | fraction | -1.17094 | 39/39 | 0 | -0.0117094 |
| poolact | restricted_search | all/all | cost_moderate | f1_mv | cached − naive | +0.0384615 | fraction | +3.84615 | 39/39 | 0 | 0.0384615 |
| poolact | restricted_search | all/all | cost_moderate | f1_mv | poolact − naive | -0.0128205 | fraction | -1.28205 | 39/39 | 0 | -0.0128205 |
| poolact | restricted_search | all/all | cost_tight | f1_mi | poolact − cached | +0.00791855 | fraction | +0.791855 | 39/39 | 0 | 0.00791855 |
| poolact | restricted_search | all/all | cost_tight | f1_mv | poolact − cached | +0.0316742 | fraction | +3.16742 | 39/39 | 0 | 0.0316742 |
| poolact | restricted_search | all/all | cost_tight | f1_mi | cached − naive | +0.0213675 | fraction | +2.13675 | 39/39 | 0 | 0.0213675 |
| poolact | restricted_search | all/all | cost_tight | f1_mi | poolact − naive | +0.0292861 | fraction | +2.92861 | 39/39 | 0 | 0.0292861 |
| poolact | restricted_search | all/all | cost_tight | f1_mv | cached − naive | +0.017094 | fraction | +1.7094 | 39/39 | 0 | 0.017094 |
| poolact | restricted_search | all/all | cost_tight | f1_mv | poolact − naive | +0.0487682 | fraction | +4.87682 | 39/39 | 0 | 0.0487682 |
| poolact | tuning | all/all | cost_moderate | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | gap_bon | cached − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 86.509 |
| poolact | tuning | all/all | cost_moderate | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | gap_mi | cached − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 68.7819 |
| poolact | tuning | all/all | cost_moderate | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | raw_perf_bon | cached − naive | unknown | fraction | unknown | 1/9 | 8 | 0.60854 |
| poolact | tuning | all/all | cost_moderate | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | raw_perf_mi | cached − naive | unknown | fraction | unknown | 1/9 | 8 | 0.60516 |
| poolact | tuning | all/all | cost_moderate | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | gap_bon | cached − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 1.61846 |
| poolact | tuning | all/all | cost_tight | gap_mi | cached − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 40.5782 |
| poolact | tuning | all/all | cost_tight | raw_perf_bon | cached − naive | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 1/9 | 8 | 0.0113849 |
| poolact | tuning | all/all | cost_tight | raw_perf_mi | cached − naive | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 1/9 | 8 | 0.346104 |


全部预定义 family / tuning task 的绝对值及对应差值见 [TABLES.md](TABLES.md)，R3 明细见 [REPEATS.md](REPEATS.md)。不按结果方向删减家族或任务。

## 5. 资源与时间

### 5.1 实际分配成本与正式队列墙钟

正式783项执行于2026-09-11 04:39:11–06:48:03 UTC自然完成，闭合队列墙钟 **7731.582 s（约2小时9分）**，0执行失败、0未启动，32workers全程保持，无恢复或质量重抽样。四端非生成metrics确认无running/queue后，仅释放本研究1204607；Qwen和既有用户作业未修改。完整依据见[执行记录](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/PLAN.zh.md)和[实际Slurm账本](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/study/allocation_final/ACCOUNTING.md)。

| Slurm allocation | 实际区间 UTC | 32 GPU分配秒数 | GPU-hours | 结束原因 |
| --- | --- | ---: | ---: | --- |
| 1204605 | 03:46:08–04:09:11 | 1383 | 12.293333 | 在study-client请求前，为编译缓存隔离主动替换；原日志保留 |
| 1204607 | 04:09:47–06:50:36 | 9649 | 85.768889 | 正式全量完成后的正常释放 |
| 合计 | 两次非重叠实际分配 | 11032 | 98.062222 | 两个真实allocation，四副本不重复乘四 |

GPU-hours 包含加载、smoke、正式运行和尾部空闲，不是formal-only计算量。两个Slurm终态均为CANCELLED，但原因不同，不能自动视为实验失败。动态队列按活跃invocation数补位，不按剩余token工时预测；末尾请求集中在一个副本，不能声称所有32GPU全程饱和。HTTP/agent时长之和不等于该墙钟；未记录连续GPU利用率，不能推断有效算力占比。

### 5.2 HTTP 尝试成本与分析单元资源

下表为完整 HTTP 尝试账本的独立总计：all_physical_attempts 包含保留的失败/恢复前尝试，effective_slots 只属于最终授权槽位。reasoning 已包含在 output，不能再加一次。unknown 表示必要用量缺失，旁列仅是已知尝试子集。

| 范围 | 指标 | 单位 | 完整总计 | 已知子集合计 | known/expected 尝试 |
| --- | --- | --- | --- | --- | --- |
| all_physical_attempts | input_tokens | tokens | 1.05359e+08 | 1.05359e+08 | 14300/14300 |
| all_physical_attempts | output_tokens | tokens | 2.33453e+07 | 2.33453e+07 | 14300/14300 |
| all_physical_attempts | reasoning_tokens_included_in_output | tokens | 1.84849e+07 | 1.84849e+07 | 14300/14300 |
| all_physical_attempts | request_wall_seconds | seconds | 274929 | 274929 | 14300/14300 |
| all_physical_attempts | total_tokens | tokens | 1.28704e+08 | 1.28704e+08 | 14300/14300 |
| effective_slots | input_tokens | tokens | 1.05359e+08 | 1.05359e+08 | 14300/14300 |
| effective_slots | output_tokens | tokens | 2.33453e+07 | 2.33453e+07 | 14300/14300 |
| effective_slots | reasoning_tokens_included_in_output | tokens | 1.84849e+07 | 1.84849e+07 | 14300/14300 |
| effective_slots | request_wall_seconds | seconds | 274929 | 274929 | 14300/14300 |
| effective_slots | total_tokens | tokens | 1.28704e+08 | 1.28704e+08 | 14300/14300 |


每分析单元资源均值如下；完整 family/task 资源表在 TABLES.md。Pool 的 token、反馈和模拟成本按池内 N 个 agent 合计；Exp Audit 资源按三个顺序均值展示，物理尝试成本则仍逐执行计入上表。

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | single | duplicate_action_attempts | count | 0.128205 | 13/13 | 0 | 13 | 0.128205 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_attempts | count | 23.1282 | 13/13 | 0 | 13 | 23.1282 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_cost_seconds | seconds | 6914.98 | 13/13 | 0 | 13 | 6914.98 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_visible | count | 23.1282 | 13/13 | 0 | 13 | 23.1282 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | input_tokens | tokens | 366151 | 13/13 | 0 | 13 | 366151 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | output_tokens | tokens | 21262.4 | 13/13 | 0 | 13 | 21262.4 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | protocol_failure_rate | fraction | 0.109717 | 13/13 | 0 | 13 | 0.109717 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | wall_time_seconds | seconds | 241.674 | 13/13 | 0 | 13 | 241.674 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | budget_utilization | fraction | 0.968122 | 13/13 | 0 | 13 | 0.968122 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_attempts | count | 9.74359 | 13/13 | 0 | 13 | 9.74359 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 2904.36 | 13/13 | 0 | 13 | 2904.36 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_visible | count | 9.17949 | 13/13 | 0 | 13 | 9.17949 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | input_tokens | tokens | 137147 | 13/13 | 0 | 13 | 137147 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | output_tokens | tokens | 17861.6 | 13/13 | 0 | 13 | 17861.6 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.096219 | 13/13 | 0 | 13 | 0.096219 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | wall_time_seconds | seconds | 192.191 | 13/13 | 0 | 13 | 192.191 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | budget_utilization | fraction | 0.984812 | 13/13 | 0 | 13 | 0.984812 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_attempts | count | 3 | 13/13 | 0 | 13 | 3 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_cost_seconds | seconds | 886.331 | 13/13 | 0 | 13 | 886.331 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_visible | count | 2.33333 | 13/13 | 0 | 13 | 2.33333 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | input_tokens | tokens | 44672.1 | 13/13 | 0 | 13 | 44672.1 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | output_tokens | tokens | 16333.6 | 13/13 | 0 | 13 | 16333.6 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.179548 | 13/13 | 0 | 13 | 0.179548 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | wall_time_seconds | seconds | 175.489 | 13/13 | 0 | 13 | 175.489 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | duplicate_action_attempts | count | 0.0273973 | 73/73 | 0 | 73 | 0.0273973 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_attempts | count | 17.5479 | 73/73 | 0 | 73 | 17.5479 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_cost_seconds | seconds | 3387.71 | 73/73 | 0 | 73 | 3387.71 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_visible | count | 17.5479 | 73/73 | 0 | 73 | 17.5479 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | input_tokens | tokens | 131940 | 73/73 | 0 | 73 | 131940 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | output_tokens | tokens | 11589.2 | 73/73 | 0 | 73 | 11589.2 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | protocol_failure_rate | fraction | 0.0632559 | 73/73 | 0 | 73 | 0.0632559 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | wall_time_seconds | seconds | 134.497 | 73/73 | 0 | 73 | 134.497 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | budget_utilization | fraction | 0.856117 | 73/73 | 0 | 73 | 0.856117 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | duplicate_action_attempts | count | 0.0410959 | 73/73 | 0 | 73 | 0.0410959 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_attempts | count | 12.7945 | 73/73 | 0 | 73 | 12.7945 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 2568.35 | 73/73 | 0 | 73 | 2568.35 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_visible | count | 12.274 | 73/73 | 0 | 73 | 12.274 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | input_tokens | tokens | 68977.5 | 73/73 | 0 | 73 | 68977.5 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | output_tokens | tokens | 11360.5 | 73/73 | 0 | 73 | 11360.5 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.0764896 | 73/73 | 0 | 73 | 0.0764896 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | wall_time_seconds | seconds | 127.875 | 73/73 | 0 | 73 | 127.875 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | budget_utilization | fraction | 1.18245 | 73/73 | 0 | 73 | 1.18245 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | duplicate_action_attempts | count | 0.0136986 | 73/73 | 0 | 73 | 0.0136986 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_attempts | count | 4.64384 | 73/73 | 0 | 73 | 4.64384 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_cost_seconds | seconds | 1064.2 | 73/73 | 0 | 73 | 1064.2 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_visible | count | 3.73973 | 73/73 | 0 | 73 | 3.73973 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | input_tokens | tokens | 12433 | 73/73 | 0 | 73 | 12433 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | output_tokens | tokens | 8252.52 | 73/73 | 0 | 73 | 8252.52 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.12133 | 73/73 | 0 | 73 | 0.12133 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | wall_time_seconds | seconds | 89.3709 | 73/73 | 0 | 73 | 89.3709 | 1 / unknown |
| expgym | tuning | all/all | cost_free | single | duplicate_action_attempts | count | 0.037037 | 27/27 | 0 | 9 | 0.037037 | 3 / 0.06415 |
| expgym | tuning | all/all | cost_free | single | feedback_attempts | count | 16.4074 | 27/27 | 0 | 9 | 16.4074 | 3 / 5.1787 |
| expgym | tuning | all/all | cost_free | single | feedback_cost_seconds | seconds | 216690 | 27/27 | 0 | 9 | 216690 | 3 / 61675.2 |
| expgym | tuning | all/all | cost_free | single | feedback_visible | count | 16.4074 | 27/27 | 0 | 9 | 16.4074 | 3 / 5.1787 |
| expgym | tuning | all/all | cost_free | single | input_tokens | tokens | 148797 | 27/27 | 0 | 9 | 148797 | 3 / 64728.1 |
| expgym | tuning | all/all | cost_free | single | output_tokens | tokens | 12851.2 | 27/27 | 0 | 9 | 12851.2 | 3 / 6707.51 |
| expgym | tuning | all/all | cost_free | single | protocol_failure_rate | fraction | 0.159228 | 27/27 | 0 | 9 | 0.159228 | 3 / 0.0741547 |
| expgym | tuning | all/all | cost_free | single | wall_time_seconds | seconds | 152.04 | 27/27 | 0 | 9 | 152.04 | 3 / 80.6081 |
| expgym | tuning | all/all | cost_moderate | single | budget_utilization | fraction | 0.805942 | 27/27 | 0 | 9 | 0.805942 | 3 / 0.162412 |
| expgym | tuning | all/all | cost_moderate | single | duplicate_action_attempts | count | 0.037037 | 27/27 | 0 | 9 | 0.037037 | 3 / 0.06415 |
| expgym | tuning | all/all | cost_moderate | single | feedback_attempts | count | 9.74074 | 27/27 | 0 | 9 | 9.74074 | 3 / 2.42501 |
| expgym | tuning | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 109647 | 27/27 | 0 | 9 | 109647 | 3 / 2020.72 |
| expgym | tuning | all/all | cost_moderate | single | feedback_visible | count | 9.37037 | 27/27 | 0 | 9 | 9.37037 | 3 / 2.48535 |
| expgym | tuning | all/all | cost_moderate | single | input_tokens | tokens | 74453 | 27/27 | 0 | 9 | 74453 | 3 / 22573.9 |
| expgym | tuning | all/all | cost_moderate | single | output_tokens | tokens | 9823.41 | 27/27 | 0 | 9 | 9823.41 | 3 / 2586.18 |
| expgym | tuning | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.127625 | 27/27 | 0 | 9 | 0.127625 | 3 / 0.0552428 |
| expgym | tuning | all/all | cost_moderate | single | wall_time_seconds | seconds | 118.364 | 27/27 | 0 | 9 | 118.364 | 3 / 30.6877 |
| expgym | tuning | all/all | cost_tight | single | budget_utilization | fraction | 0.939236 | 27/27 | 0 | 9 | 0.939236 | 3 / 0.126418 |
| expgym | tuning | all/all | cost_tight | single | duplicate_action_attempts | count | 0 | 27/27 | 0 | 9 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_tight | single | feedback_attempts | count | 4.07407 | 27/27 | 0 | 9 | 4.07407 | 3 / 0.42066 |
| expgym | tuning | all/all | cost_tight | single | feedback_cost_seconds | seconds | 34420.8 | 27/27 | 0 | 9 | 34420.8 | 3 / 2127.6 |
| expgym | tuning | all/all | cost_tight | single | feedback_visible | count | 3.62963 | 27/27 | 0 | 9 | 3.62963 | 3 / 0.42066 |
| expgym | tuning | all/all | cost_tight | single | input_tokens | tokens | 24947.7 | 27/27 | 0 | 9 | 24947.7 | 3 / 33.143 |
| expgym | tuning | all/all | cost_tight | single | output_tokens | tokens | 6140.74 | 27/27 | 0 | 9 | 6140.74 | 3 / 1014.88 |
| expgym | tuning | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.23939 | 27/27 | 0 | 9 | 0.23939 | 3 / 0.0872608 |
| expgym | tuning | all/all | cost_tight | single | wall_time_seconds | seconds | 72.6696 | 27/27 | 0 | 9 | 72.6696 | 3 / 13.3471 |
| poolact | evidence_audit | all/all | cost_moderate | cached | budget_utilization | fraction | 0.626227 | 13/13 | 0 | 13 | 0.626227 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | duplicate_action_attempts | count | 9.84615 | 13/13 | 0 | 13 | 9.84615 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_attempts | count | 32.1538 | 13/13 | 0 | 13 | 32.1538 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 7514.72 | 13/13 | 0 | 13 | 7514.72 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | input_tokens | tokens | 473478 | 13/13 | 0 | 13 | 473478 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | output_tokens | tokens | 82999.1 | 13/13 | 0 | 13 | 82999.1 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.235076 | 13/13 | 0 | 13 | 0.235076 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | budget_utilization | fraction | 0.466278 | 13/13 | 0 | 13 | 0.466278 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | duplicate_action_attempts | count | 4.61538 | 13/13 | 0 | 13 | 4.61538 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_attempts | count | 18.8462 | 13/13 | 0 | 13 | 18.8462 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 5595.33 | 13/13 | 0 | 13 | 5595.33 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | input_tokens | tokens | 376722 | 13/13 | 0 | 13 | 376722 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | output_tokens | tokens | 109929 | 13/13 | 0 | 13 | 109929 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.35335 | 13/13 | 0 | 13 | 0.35335 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.246636 | 13/13 | 0 | 13 | 0.246636 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 1.61538 | 13/13 | 0 | 13 | 1.61538 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_attempts | count | 10.4615 | 13/13 | 0 | 13 | 10.4615 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 2959.63 | 13/13 | 0 | 13 | 2959.63 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 2/13 | 11 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | input_tokens | tokens | 302074 | 13/13 | 0 | 13 | 302074 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | output_tokens | tokens | 84832.4 | 13/13 | 0 | 13 | 84832.4 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.447477 | 13/13 | 0 | 13 | 0.447477 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | budget_utilization | fraction | 0.531552 | 13/13 | 0 | 13 | 0.531552 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | duplicate_action_attempts | count | 2.15385 | 13/13 | 0 | 13 | 2.15385 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_attempts | count | 7 | 13/13 | 0 | 13 | 7 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 1913.59 | 13/13 | 0 | 13 | 1913.59 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | input_tokens | tokens | 194021 | 13/13 | 0 | 13 | 194021 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | output_tokens | tokens | 82773.8 | 13/13 | 0 | 13 | 82773.8 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.453801 | 13/13 | 0 | 13 | 0.453801 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | budget_utilization | fraction | 0.572016 | 13/13 | 0 | 13 | 0.572016 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | duplicate_action_attempts | count | 2.53846 | 13/13 | 0 | 13 | 2.53846 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_attempts | count | 7 | 13/13 | 0 | 13 | 7 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 2059.26 | 13/13 | 0 | 13 | 2059.26 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | input_tokens | tokens | 249212 | 13/13 | 0 | 13 | 249212 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | output_tokens | tokens | 104834 | 13/13 | 0 | 13 | 104834 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.459612 | 13/13 | 0 | 13 | 0.459612 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | budget_utilization | fraction | 0.173411 | 13/13 | 0 | 13 | 0.173411 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | duplicate_action_attempts | count | 0.692308 | 13/13 | 0 | 13 | 0.692308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_attempts | count | 2.23077 | 13/13 | 0 | 13 | 2.23077 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 624.278 | 13/13 | 0 | 13 | 624.278 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_visible | count | unknown | 2/13 | 11 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | input_tokens | tokens | 132751 | 13/13 | 0 | 13 | 132751 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | output_tokens | tokens | 61874 | 13/13 | 0 | 13 | 61874 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.63138 | 13/13 | 0 | 13 | 0.63138 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | budget_utilization | fraction | 0.390728 | 39/39 | 0 | 39 | 0.390728 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | duplicate_action_attempts | count | 13.3077 | 39/39 | 0 | 39 | 13.3077 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_attempts | count | 25.0769 | 39/39 | 0 | 39 | 25.0769 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 4688.74 | 39/39 | 0 | 39 | 4688.74 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_visible | count | unknown | 1/39 | 38 | 39 | 0 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | input_tokens | tokens | 169259 | 39/39 | 0 | 39 | 169259 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | output_tokens | tokens | 31060.7 | 39/39 | 0 | 39 | 31060.7 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.323588 | 39/39 | 0 | 39 | 0.323588 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | budget_utilization | fraction | 0.412121 | 39/39 | 0 | 39 | 0.412121 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | duplicate_action_attempts | count | 11.9487 | 39/39 | 0 | 39 | 11.9487 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_attempts | count | 24.9231 | 39/39 | 0 | 39 | 24.9231 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 4945.46 | 39/39 | 0 | 39 | 4945.46 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | input_tokens | tokens | 186091 | 39/39 | 0 | 39 | 186091 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | output_tokens | tokens | 35566 | 39/39 | 0 | 39 | 35566 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.308474 | 39/39 | 0 | 39 | 0.308474 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.203611 | 39/39 | 0 | 39 | 0.203611 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 4.46154 | 39/39 | 0 | 39 | 4.46154 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_attempts | count | 10.9231 | 39/39 | 0 | 39 | 10.9231 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 2443.33 | 39/39 | 0 | 39 | 2443.33 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | input_tokens | tokens | 126466 | 39/39 | 0 | 39 | 126466 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | output_tokens | tokens | 32022.8 | 39/39 | 0 | 39 | 32022.8 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.417162 | 39/39 | 0 | 39 | 0.417162 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | budget_utilization | fraction | 0.815309 | 39/39 | 0 | 39 | 0.815309 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | duplicate_action_attempts | count | 7.4359 | 39/39 | 0 | 39 | 7.4359 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_attempts | count | 13.4359 | 39/39 | 0 | 39 | 13.4359 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 2935.11 | 39/39 | 0 | 39 | 2935.11 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_visible | count | unknown | 2/39 | 37 | 39 | 0 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | input_tokens | tokens | 54360.4 | 39/39 | 0 | 39 | 54360.4 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | output_tokens | tokens | 26575.7 | 39/39 | 0 | 39 | 26575.7 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.309256 | 39/39 | 0 | 39 | 0.309256 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | budget_utilization | fraction | 0.648249 | 39/39 | 0 | 39 | 0.648249 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | duplicate_action_attempts | count | 5.94872 | 39/39 | 0 | 39 | 5.94872 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_attempts | count | 11.5385 | 39/39 | 0 | 39 | 11.5385 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 2333.7 | 39/39 | 0 | 39 | 2333.7 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | input_tokens | tokens | 66929.1 | 39/39 | 0 | 39 | 66929.1 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | output_tokens | tokens | 26096 | 39/39 | 0 | 39 | 26096 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.37 | 39/39 | 0 | 39 | 0.37 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | budget_utilization | fraction | 0.629807 | 39/39 | 0 | 39 | 0.629807 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | duplicate_action_attempts | count | 4.84615 | 39/39 | 0 | 39 | 4.84615 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_attempts | count | 9.71795 | 39/39 | 0 | 39 | 9.71795 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 2267.31 | 39/39 | 0 | 39 | 2267.31 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | input_tokens | tokens | 80792.7 | 39/39 | 0 | 39 | 80792.7 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | output_tokens | tokens | 33809.6 | 39/39 | 0 | 39 | 33809.6 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.402962 | 39/39 | 0 | 39 | 0.402962 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | budget_utilization | fraction | 0.336466 | 9/9 | 0 | 3 | 0.336466 | 3 / 0.0775656 |
| poolact | tuning | all/all | cost_moderate | cached | duplicate_action_attempts | count | 1.66667 | 9/9 | 0 | 3 | 1.66667 | 3 / 1.1547 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_attempts | count | 15.2222 | 9/9 | 0 | 3 | 15.2222 | 3 / 8.28206 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 94525.8 | 9/9 | 0 | 3 | 94525.8 | 3 / 35612.9 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_visible | count | unknown | 3/9 | 6 | 3 | 0 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | input_tokens | tokens | 278340 | 9/9 | 0 | 3 | 278340 | 3 / 168429 |
| poolact | tuning | all/all | cost_moderate | cached | output_tokens | tokens | 77948.2 | 9/9 | 0 | 3 | 77948.2 | 3 / 40631.6 |
| poolact | tuning | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.453267 | 9/9 | 0 | 3 | 0.453267 | 3 / 0.120559 |
| poolact | tuning | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | budget_utilization | fraction | 0.188325 | 9/9 | 0 | 3 | 0.188325 | 3 / 0.117837 |
| poolact | tuning | all/all | cost_moderate | naive | duplicate_action_attempts | count | 0.666667 | 9/9 | 0 | 3 | 0.666667 | 3 / 0.881917 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_attempts | count | 9.88889 | 9/9 | 0 | 3 | 9.88889 | 3 / 8.77074 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 66391.6 | 9/9 | 0 | 3 | 66391.6 | 3 / 59036.9 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_visible | count | unknown | 1/9 | 8 | 3 | 0 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | input_tokens | tokens | 269754 | 9/9 | 0 | 3 | 269754 | 3 / 161062 |
| poolact | tuning | all/all | cost_moderate | naive | output_tokens | tokens | 72492.4 | 9/9 | 0 | 3 | 72492.4 | 3 / 31099 |
| poolact | tuning | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.505538 | 9/9 | 0 | 3 | 0.505538 | 3 / 0.0894579 |
| poolact | tuning | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.12028 | 9/9 | 0 | 3 | 0.12028 | 3 / 0.103462 |
| poolact | tuning | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 0.444444 | 9/9 | 0 | 3 | 0.444444 | 3 / 0.19245 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_attempts | count | 5.11111 | 9/9 | 0 | 3 | 5.11111 | 3 / 3.16813 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 31728 | 9/9 | 0 | 3 | 31728 | 3 / 32867.9 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 3/9 | 6 | 3 | 0 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | input_tokens | tokens | 212592 | 9/9 | 0 | 3 | 212592 | 3 / 111745 |
| poolact | tuning | all/all | cost_moderate | poolact | output_tokens | tokens | 55006.7 | 9/9 | 0 | 3 | 55006.7 | 3 / 30640.3 |
| poolact | tuning | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.586604 | 9/9 | 0 | 3 | 0.586604 | 3 / 0.202288 |
| poolact | tuning | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | budget_utilization | fraction | 0.389056 | 9/9 | 0 | 3 | 0.389056 | 3 / 0.0466743 |
| poolact | tuning | all/all | cost_tight | cached | duplicate_action_attempts | count | 0.777778 | 9/9 | 0 | 3 | 0.777778 | 3 / 0.83887 |
| poolact | tuning | all/all | cost_tight | cached | feedback_attempts | count | 6.66667 | 9/9 | 0 | 3 | 6.66667 | 3 / 2.96273 |
| poolact | tuning | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 40665.1 | 9/9 | 0 | 3 | 40665.1 | 3 / 11356 |
| poolact | tuning | all/all | cost_tight | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | input_tokens | tokens | 168160 | 9/9 | 0 | 3 | 168160 | 3 / 78093.8 |
| poolact | tuning | all/all | cost_tight | cached | output_tokens | tokens | 82649.2 | 9/9 | 0 | 3 | 82649.2 | 3 / 29886.3 |
| poolact | tuning | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.470592 | 9/9 | 0 | 3 | 0.470592 | 3 / 0.0554102 |
| poolact | tuning | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | budget_utilization | fraction | 0.492657 | 9/9 | 0 | 3 | 0.492657 | 3 / 0.253608 |
| poolact | tuning | all/all | cost_tight | naive | duplicate_action_attempts | count | 2.22222 | 9/9 | 0 | 3 | 2.22222 | 3 / 2.00924 |
| poolact | tuning | all/all | cost_tight | naive | feedback_attempts | count | 9 | 9/9 | 0 | 3 | 9 | 3 / 8.14453 |
| poolact | tuning | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 46493.6 | 9/9 | 0 | 3 | 46493.6 | 3 / 21986.9 |
| poolact | tuning | all/all | cost_tight | naive | feedback_visible | count | unknown | 1/9 | 8 | 3 | 0 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | input_tokens | tokens | 229168 | 9/9 | 0 | 3 | 229168 | 3 / 220874 |
| poolact | tuning | all/all | cost_tight | naive | output_tokens | tokens | 72176.2 | 9/9 | 0 | 3 | 72176.2 | 3 / 37207.1 |
| poolact | tuning | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.461251 | 9/9 | 0 | 3 | 0.461251 | 3 / 0.189539 |
| poolact | tuning | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | budget_utilization | fraction | 0.463469 | 9/9 | 0 | 3 | 0.463469 | 3 / 0.220204 |
| poolact | tuning | all/all | cost_tight | poolact | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.19245 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_attempts | count | 6.77778 | 9/9 | 0 | 3 | 6.77778 | 3 / 3.42107 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 46509.3 | 9/9 | 0 | 3 | 46509.3 | 3 / 25388.9 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | input_tokens | tokens | 238966 | 9/9 | 0 | 3 | 238966 | 3 / 130182 |
| poolact | tuning | all/all | cost_tight | poolact | output_tokens | tokens | 89996.3 | 9/9 | 0 | 3 | 89996.3 | 3 / 31485.4 |
| poolact | tuning | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.465028 | 9/9 | 0 | 3 | 0.465028 | 3 / 0.126787 |
| poolact | tuning | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |


feedback_cost_seconds 是模拟反馈秒，不是 GPU 推理时长；预算利用率也不是 GPU 利用率。Pool 整个子进程 wall 未被该 exporter 记录，因此保持 unknown，不能以 agent wall 求和/最大值冒充。HTTP request wall 合计不是并发实验总历时；真实分配账本与正式 queue wall 单独记录，此处没有 formal-only GPU 利用量，故不据此推算有效算力或速度优越性。

## 6. 主张、缺失与限制

本次14300次正式HTTP请求全部首尝试success：10801次tool_calls、3361次stop、138次length（约0.965%请求）。总output23345301 token中含reasoning18484906（约79.180%）；reasoning不另加一次，length计数是请求数而非agent/任务数。

Exp tuning为70/81 agents可评分，11个缺失最终配置；Pool tuning为135/216 agents可评分，54个pool中只有10个全N4端点已知。全部92个未知agent均为正常loop返回、model_no_answer、unscorable_missing_configuration，不是执行失败。此处只能判定没有最终配置，不能声称没有历史可评估的tool配置；冻结missing-final策略不允许用best-observed替换这类缺失。

运行时使用SGLang0.5.17加精确官方0731 effort编码器backport，最高effort经过四副本16次真实native请求的保存记录和CPU实际encoder重放验证。CUDA-12依赖override、实际NVCC12.8.93、可选custom-all-reduce编译失败后的标准NCCL fallback以及DSV4专用FP8 KV路径均如实记录在[冻结运行时说明](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/runtime/BUILD.md)。这些兼容与部署差异不构成性能差异的单一因果解释。本研究保持32K输出和Pool局部131072上限，不等于厂商384K推荐长输出配置。

推荐分析为full_v2。首次full_v1成本适配器漏读usage顶层reasoning_tokens，已用模型无关双形状读取修复并保留旧成本/身份及精确原helper；23个fixtures通过，受影响重算57.26 s。7张科学/终态/覆盖CSV及INPUTS与full_v1逐字节一致，14300条成本行除reasoning子字段外全部相同，无模型重跑或评分重算。

当前表格能回答本模型、这些固定任务与设置下的方向和幅度；不能证明模型总体普适、未见任务泛化或统计显著性。负向结果保留，unknown 不补零。task-abstention-v1 下正常 Search/Audit 空回答可有合法零分；HPO 缺配置不可评分，不把二者当作同一种故障。

完整均值只在全部计划端点已知时给出；已知子集仅作诊断。配对差值使用完整计划 item×outerrep 范围，不静默取交集。R3 的 SD 是三个 block 的描述性变化，不是标准误、置信区间或独立生成证据；R1 不提供重复 SD。

## 7. 完整原件、聚合和存档入口

[成稿后独立数字/逻辑复核](review/REVIEW.md) · [机器可读复核记录](review/REVIEW.json) · [独立CSV核查脚本](review/check_csv.py)

[原始 dump 存档索引](ARCHIVE_INDEX.md) · [机器可读存档索引](ARCHIVE_INDEX.json) · [旧双模型完整报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md)

存档索引应定位 collection/bundle → member inventory → tar 分片及匹配恢复工具。这里引用其固定版本，不重新扫描 tar、不声称已恢复或验证全部内容，也不把新 collection 引用的旧包再计作一份新物理副本。旧双模型报告仅供独立比较入口，不与本模型 all 直接合并。

- [COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/COSTS.json)
- [INPUTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/INPUTS.json)
- [SOURCE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/SOURCE_INDEX.json)
- [absolute_settings.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/absolute_settings.csv)
- [all_attempt_costs.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/all_attempt_costs.csv)
- [by_outerseed.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/by_outerseed.csv)
- [contrasts.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/contrasts.csv)
- [metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/metrics.csv)
- [metrics_execution.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/metrics_execution.csv)
- [normalized.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/normalized.csv)
- [raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/41ec233f849aff05d8d91443118b6b2392d1cc40/results/deepseek-flash-0731-20260911/analysis/full_v2/raw_terminals.csv)

metrics_execution 是执行层；metrics 是 Audit 已折叠一次的分析层；normalized 是唯一有效槽位映射；raw_terminals 是终态投影，不是 HTTP 回复。all_attempt_costs 与原始请求/回复的完整映射入口分别是成本表和 SOURCE_INDEX/存档索引。

| 显式输入 | 字节 | SHA256 | 本次使用范围 |
| --- | --- | --- | --- |
| COSTS.json | 1645 | 1cde2fc4f5b11b71fb224798eab9d06931ef6e759e51e454c21198f5a82686da | 本次读取并校验 SHA |
| INPUTS.json | 1021 | 2e6d279d27610390d4fa70ce8e3ce61e754970825ffa2d488d2d2624e1b19cad | 本次读取并校验 SHA |
| SOURCE_INDEX.json | 1.12651e+07 | a6cf9cb14443a4a0efd4cd6dcc7085c89284f7da76d5253e7b85b04ac471c959 | 仅继承冻结 pin、核大小并提供链接 |
| absolute_settings.csv | 334497 | edd58cbbd400fa021a8f131b12a089dc710547dd70e38c0e78fed42be169e7d3 | 本次读取并校验 SHA |
| all_attempt_costs.csv | 1.05744e+07 | ecbc032e4a91d95a284ef8d040574cdd6fcfd919c18c2c9648ef777b5019139a | 仅继承冻结 pin、核大小并提供链接 |
| by_outerseed.csv | 717165 | 0996872cf4a4f3d340aeeea4b68b9d0558dd0dee7f60fb03bc9c2036e1fa9a48 | 本次读取并校验 SHA |
| contrasts.csv | 394843 | 93273291093c37ffae708af3266475313365ba9d5cfa8325fb807d854aa3d0b0 | 本次读取并校验 SHA |
| metrics.csv | 3.69714e+06 | f61975bf146d499d2691ae02dbb129850f2da6107ce63121f060fe1c8d3196c0 | 仅继承冻结 pin、核大小并提供链接 |
| metrics_execution.csv | 2.5012e+06 | 64fe8f174f1d8c37e97e32819b4e0b339959bc9b370ce2c358b7fba3b0b6bd77 | 仅继承冻结 pin、核大小并提供链接 |
| normalized.csv | 333234 | a5c05a9f3dcc9eb615c04848c0829a91623c37fa2f664024d2dcd283f4f601a1 | 本次读取并校验 SHA |
| raw_terminals.csv | 2.09308e+06 | 85bf5569adb4484975a6706dad48246ac7bf009b9289ff78e84be21855242834 | 仅继承冻结 pin、核大小并提供链接 |
| coverage | 25832 | 5c764f672dddd73ee8d8ff9f229ed902191116a2ebf74a0c714067bef0373122 | 本次读取并校验 SHA |
| oracle | 28814 | f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e | 本次读取并校验 SHA |
| plan | 4.01813e+06 | 69048ff627626da685ca34157d4954e8d8413cd83c3fe995c811a93778b09c5b | 本次读取并校验 SHA |
| provider_contract | 3611 | 95a16593c66ad33c0695118b59097fe738700aaf9cf417c98e340eded71743a8 | 本次读取并校验 SHA |
| run_inputs | 17924 | 57bbe761f556a31643d9f9402cf5747b6fd4d06fc05355fde4510d8ef7f86107 | 本次读取并校验 SHA |
| serving_plan | 1640 | 54cd209e728d39153bc3d354e88068284ccf166d06d84dac099aa5245389380e | 本次读取并校验 SHA |


## 8. 生成与有限验收

报告输入描述 SHA256：`71b89def1c412b336238c2aa446f0f3ea79e29d9a0e9abbbcc9af2a464206aa8`；生成器 SHA256：`2fd30e4a36fc3b7234829dfb0b1e75ec998f9d98837a9667ec1dd50f7db481b2`。没有模型调用、重评分、raw 恢复或归档内容扫描。

生成器检查 schema、固定输入 SHA、覆盖/分母、对照方向与均值差（1e-10 浮点容差）及固定提交链接格式；显示保留六位有效数字，真实 CSV 值不改写。`--check` 只比较这三份 Markdown 的精确字节，不写文件。链接实际可达性与一次成稿后的独立数值/逻辑复核仍由发布流程完成；本生成器不把自身检查称为独立复核。
