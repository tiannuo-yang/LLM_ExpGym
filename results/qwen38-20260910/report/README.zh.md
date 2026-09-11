# qwen3.8-2.4t-a95b-fp8：ExpGym / PoolAct 全设置描述性报告

本报告只展示冻结分析结果，不新增实验、不重评分、不恢复 raw。属于固定已知任务的 Custom study，不自动等于 paper-exact reproduction。输入身份冻结与回顾性矩阵不构成预注册或显著性证据。

## 1. 主要发现与适用范围

主要展示端点（展示选择，不冒充事前注册）：ExpGym 的 F1 / EA / Gap，Free−Tight 为正向 3、零 0、负向 0、unknown 0；PoolAct 的 F1-MV / EA-MV / Gap-MI，两个预算下 poolact−naive 为正向 6、零 0、负向 0、unknown 0。所有端点和相邻档位/缓存对照见后文，包含负值和 unknown。

这里 ExpGym 的正差表示预算收紧后下降，PoolAct 的正差表示在该固定比较中改善。汇总改善不代表每个任务或每次重复都改善；本模型的方向也不能替代其他模型的证据。未完成或不可评分的完整端点不以已知子集均值代替。

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | evidence_acc | cost_free − cost_tight | +0.334842 | fraction | +33.4842 | 13/13 | 0 | 0.334842 |
| expgym | restricted_search | all/all | cost_free | f1 | cost_free − cost_tight | +0.396777 | fraction | +39.6777 | 73/73 | 0 | 0.396777 |
| expgym | tuning | all/all | cost_free | gap | cost_free − cost_tight | +11.7552 | Gap points | 不适用 | 27/27 | 0 | 11.7552 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mv | poolact − naive | +0.248869 | fraction | +24.8869 | 13/13 | 0 | 0.248869 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mv | poolact − naive | +0.0769231 | fraction | +7.69231 | 13/13 | 0 | 0.0769231 |
| poolact | restricted_search | all/all | cost_moderate | f1_mv | poolact − naive | +0.0227106 | fraction | +2.27106 | 39/39 | 0 | 0.0227106 |
| poolact | restricted_search | all/all | cost_tight | f1_mv | poolact − naive | +0.0239316 | fraction | +2.39316 | 39/39 | 0 | 0.0239316 |
| poolact | tuning | all/all | cost_moderate | gap_mi | poolact − naive | +1.94653 | Gap points | 不适用 | 9/9 | 0 | 1.94653 |
| poolact | tuning | all/all | cost_tight | gap_mi | poolact − naive | +5.64958 | Gap points | 不适用 | 9/9 | 0 | 5.64958 |


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

实际计划、身份记录与服务计划：[accounting](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/accounting.json) · [coverage](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_cache_salt/coverage.json) · [oracle](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/reference_oracle3.json) · [plan](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/formal_plan_cache_salt.json) · [run_inputs](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/study/RUN_INPUTS_launch02.json) · [serving_plan](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/serving/launch02/plan.json)

源码提交 `21b4de99b2a014874e3cec1595eaa40762b0c564`；源码树 SHA256 `58f8663d62864940cf16c9454d9c3d7230b77c2858748f5df491ce5d10a77251`。

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
| model | qwen3.8-2.4t-a95b-fp8 |
| checkpoint | /lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Qwen3.8-2.4T-A95B-FP8 |
| nodes × GPUs/node | 4 × 8 |
| replicas / TP / PP / EP | &#91;1,8,4,1&#93; |
| server context_length | 262144 |
| reasoning_parser | qwen3 |
| tool_call_parser | qwen3_coder |
| server_args | &#91;"--dist-timeout","1800","--linear-attn-prefill-backend","flashinfer","--linear-attn-decode-backend","flashinfer","--mamba-full-memory-ratio","0.95","--mamba-ssm-dtype","float32","--max-prefill-tokens","8192","--page-size","1"&#93; |
| weight_payload_hashes_verified（RUN_INPUTS 声明） | false |


以上是绑定的服务配置，不把其预启动 readiness 标志当作最终运行验收。权重内容 hash、实际服务版本/模板和数据验证范围以 RUN_INPUTS 的明确原件为准，不由本报告新增推断。

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
| expgym | top_k | 20 | 计划请求值；null 表示该参数未显式记录 |
| expgym | reasoning_effort | "xhigh" | 计划请求值；null 表示该参数未显式记录 |
| expgym | chat_template_kwargs | {"enable_thinking":true,"preserve_thinking":true} | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_tokens | 32768 | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_steps | 30 | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_evals | 30 | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_context_tokens | null | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_protocol_retries | 1 | 计划请求值；null 表示该参数未显式记录 |
| expgym | max_retries | 2 | 计划请求值；null 表示该参数未显式记录 |
| expgym | request_timeout | 3600.0 | 计划请求值；null 表示该参数未显式记录 |
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
| poolact | top_k | 20 | 计划请求值；null 表示该参数未显式记录 |
| poolact | reasoning_effort | "xhigh" | 计划请求值；null 表示该参数未显式记录 |
| poolact | chat_template_kwargs | {"enable_thinking":true,"preserve_thinking":true} | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_tokens | 32768 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_steps | 30 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_evals | 30 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_context_tokens | 131072 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_protocol_retries | 1 | 计划请求值；null 表示该参数未显式记录 |
| poolact | max_retries | 2 | 计划请求值；null 表示该参数未显式记录 |
| poolact | request_timeout | 3600.0 | 计划请求值；null 表示该参数未显式记录 |
| poolact | retry_base_seconds | 3.0 | 计划请求值；null 表示该参数未显式记录 |
| poolact | retry_max_seconds | 30.0 | 计划请求值；null 表示该参数未显式记录 |
| poolact | prompt_cache_scope | null | 计划请求值；null 表示该参数未显式记录 |
| poolact | prompt_cache_key_field | "cache_salt" | 计划请求值；null 表示该参数未显式记录 |


请求字段不等于服务端已验证的行为。上下文字段也不自动代表精确 tokenizer 计数；未显式给出的其他 runner 默认值，本报告不从旧报告反推，需沿固定源码/原件入口核查。预算秒数已经由上方冻结源码/绑定 oracle 表明确给出，不从结果均值倒推。

## 3. 预算收紧与 ExpGym 表现

绝对分数按 item 内先平均重复、再对 item 等权平均；Audit 先按文档折叠顺序一次。F1 / EA / LA 与 raw performance 为 0–1 分数；Gap 是效用型归一化分数（越高越好），每个 agent 先按冻结 oracle 截零后再算 MI，不能从汇总 raw performance 重新反推。

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | single | evidence_acc | fraction | 0.918552 | 13/13 | 0 | 13 | 0.918552 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | label_acc | fraction | 0.94721 | 13/13 | 0 | 13 | 0.94721 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | evidence_acc | fraction | 0.749623 | 13/13 | 0 | 13 | 0.749623 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | label_acc | fraction | 0.882353 | 13/13 | 0 | 13 | 0.882353 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | evidence_acc | fraction | 0.58371 | 13/13 | 0 | 13 | 0.58371 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | label_acc | fraction | 0.831071 | 13/13 | 0 | 13 | 0.831071 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | f1 | fraction | 0.581486 | 73/73 | 0 | 73 | 0.581486 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | f1 | fraction | 0.509827 | 73/73 | 0 | 73 | 0.509827 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | f1 | fraction | 0.184709 | 73/73 | 0 | 73 | 0.184709 | 1 / unknown |
| expgym | tuning | all/all | cost_free | single | gap | Gap points | 97.4652 | 27/27 | 0 | 9 | 97.4652 | 3 / 0.269885 |
| expgym | tuning | all/all | cost_free | single | raw_perf | fraction | 0.828712 | 27/27 | 0 | 9 | 0.828712 | 3 / 0.00148882 |
| expgym | tuning | all/all | cost_moderate | single | gap | Gap points | 95.1334 | 27/27 | 0 | 9 | 95.1334 | 3 / 2.07222 |
| expgym | tuning | all/all | cost_moderate | single | raw_perf | fraction | 0.825155 | 27/27 | 0 | 9 | 0.825155 | 3 / 0.00268025 |
| expgym | tuning | all/all | cost_tight | single | gap | Gap points | 85.71 | 27/27 | 0 | 9 | 85.71 | 3 / 0.643776 |
| expgym | tuning | all/all | cost_tight | single | raw_perf | fraction | 0.806783 | 27/27 | 0 | 9 | 0.806783 | 3 / 0.0066334 |


以下包含 Free−Moderate、Free−Tight、Moderate−Tight。差值保留原单位；fraction 的 0.02 在百分点列为 2，不是 0.02%。

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | evidence_acc | cost_free − cost_moderate | +0.168929 | fraction | +16.8929 | 13/13 | 0 | 0.168929 |
| expgym | evidence_audit | all/all | cost_free | evidence_acc | cost_free − cost_tight | +0.334842 | fraction | +33.4842 | 13/13 | 0 | 0.334842 |
| expgym | evidence_audit | all/all | cost_free | label_acc | cost_free − cost_moderate | +0.0648567 | fraction | +6.48567 | 13/13 | 0 | 0.0648567 |
| expgym | evidence_audit | all/all | cost_free | label_acc | cost_free − cost_tight | +0.116139 | fraction | +11.6139 | 13/13 | 0 | 0.116139 |
| expgym | evidence_audit | all/all | cost_moderate | evidence_acc | cost_moderate − cost_tight | +0.165913 | fraction | +16.5913 | 13/13 | 0 | 0.165913 |
| expgym | evidence_audit | all/all | cost_moderate | label_acc | cost_moderate − cost_tight | +0.0512821 | fraction | +5.12821 | 13/13 | 0 | 0.0512821 |
| expgym | restricted_search | all/all | cost_free | f1 | cost_free − cost_moderate | +0.0716589 | fraction | +7.16589 | 73/73 | 0 | 0.0716589 |
| expgym | restricted_search | all/all | cost_free | f1 | cost_free − cost_tight | +0.396777 | fraction | +39.6777 | 73/73 | 0 | 0.396777 |
| expgym | restricted_search | all/all | cost_moderate | f1 | cost_moderate − cost_tight | +0.325118 | fraction | +32.5118 | 73/73 | 0 | 0.325118 |
| expgym | tuning | all/all | cost_free | gap | cost_free − cost_moderate | +2.33184 | Gap points | 不适用 | 27/27 | 0 | 2.33184 |
| expgym | tuning | all/all | cost_free | gap | cost_free − cost_tight | +11.7552 | Gap points | 不适用 | 27/27 | 0 | 11.7552 |
| expgym | tuning | all/all | cost_free | raw_perf | cost_free − cost_moderate | +0.00355718 | fraction | +0.355718 | 27/27 | 0 | 0.00355718 |
| expgym | tuning | all/all | cost_free | raw_perf | cost_free − cost_tight | +0.021929 | fraction | +2.1929 | 27/27 | 0 | 0.021929 |
| expgym | tuning | all/all | cost_moderate | gap | cost_moderate − cost_tight | +9.42338 | Gap points | 不适用 | 27/27 | 0 | 9.42338 |
| expgym | tuning | all/all | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0183718 | fraction | +1.83718 | 27/27 | 0 | 0.0183718 |


## 4. 缓存、协调与 PoolAct 表现

两个实际预算档位均展示 naive / cached / poolact，保留 MI 与 MV/BoN 的区别。MI/MV/BoN 都是池级端点；任一必需 agent 不可评分时，完整池端点保持 unknown。

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| poolact | evidence_audit | all/all | cost_moderate | cached | evidence_acc_mi | fraction | 0.71267 | 13/13 | 0 | 13 | 0.71267 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | evidence_acc_mv | fraction | 0.746606 | 13/13 | 0 | 13 | 0.746606 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | label_acc_mi | fraction | 0.891403 | 13/13 | 0 | 13 | 0.891403 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | label_acc_mv | fraction | 0.891403 | 13/13 | 0 | 13 | 0.891403 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | evidence_acc_mi | fraction | 0.676471 | 13/13 | 0 | 13 | 0.676471 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | evidence_acc_mv | fraction | 0.687783 | 13/13 | 0 | 13 | 0.687783 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | label_acc_mi | fraction | 0.890271 | 13/13 | 0 | 13 | 0.890271 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | label_acc_mv | fraction | 0.900452 | 13/13 | 0 | 13 | 0.900452 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | evidence_acc_mi | fraction | 0.924208 | 13/13 | 0 | 13 | 0.924208 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | evidence_acc_mv | fraction | 0.936652 | 13/13 | 0 | 13 | 0.936652 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | label_acc_mi | fraction | 0.95362 | 13/13 | 0 | 13 | 0.95362 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | label_acc_mv | fraction | 0.959276 | 13/13 | 0 | 13 | 0.959276 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | evidence_acc_mi | fraction | 0.590498 | 13/13 | 0 | 13 | 0.590498 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | evidence_acc_mv | fraction | 0.60181 | 13/13 | 0 | 13 | 0.60181 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | label_acc_mi | fraction | 0.837104 | 13/13 | 0 | 13 | 0.837104 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | label_acc_mv | fraction | 0.837104 | 13/13 | 0 | 13 | 0.837104 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | evidence_acc_mi | fraction | 0.552036 | 13/13 | 0 | 13 | 0.552036 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | evidence_acc_mv | fraction | 0.561086 | 13/13 | 0 | 13 | 0.561086 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | label_acc_mi | fraction | 0.816742 | 13/13 | 0 | 13 | 0.816742 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | label_acc_mv | fraction | 0.832579 | 13/13 | 0 | 13 | 0.832579 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | evidence_acc_mi | fraction | 0.632353 | 13/13 | 0 | 13 | 0.632353 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | evidence_acc_mv | fraction | 0.638009 | 13/13 | 0 | 13 | 0.638009 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | label_acc_mi | fraction | 0.854072 | 13/13 | 0 | 13 | 0.854072 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | label_acc_mv | fraction | 0.855204 | 13/13 | 0 | 13 | 0.855204 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | f1_mi | fraction | 0.590689 | 39/39 | 0 | 39 | 0.590689 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | f1_mv | fraction | 0.611731 | 39/39 | 0 | 39 | 0.611731 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | f1_mi | fraction | 0.588896 | 39/39 | 0 | 39 | 0.588896 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | f1_mv | fraction | 0.612138 | 39/39 | 0 | 39 | 0.612138 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | f1_mi | fraction | 0.623277 | 39/39 | 0 | 39 | 0.623277 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | f1_mv | fraction | 0.634849 | 39/39 | 0 | 39 | 0.634849 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | f1_mi | fraction | 0.223102 | 39/39 | 0 | 39 | 0.223102 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | f1_mv | fraction | 0.233139 | 39/39 | 0 | 39 | 0.233139 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | f1_mi | fraction | 0.18552 | 39/39 | 0 | 39 | 0.18552 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | f1_mv | fraction | 0.182956 | 39/39 | 0 | 39 | 0.182956 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | f1_mi | fraction | 0.2269 | 39/39 | 0 | 39 | 0.2269 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | f1_mv | fraction | 0.206888 | 39/39 | 0 | 39 | 0.206888 | 1 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | gap_bon | Gap points | 99.0035 | 9/9 | 0 | 3 | 99.0035 | 3 / 0.59512 |
| poolact | tuning | all/all | cost_moderate | cached | gap_mi | Gap points | 97.7233 | 9/9 | 0 | 3 | 97.7233 | 3 / 0.787076 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_bon | fraction | 0.942916 | 9/9 | 0 | 3 | 0.942916 | 3 / 0.00166549 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_mi | fraction | 0.937188 | 9/9 | 0 | 3 | 0.937188 | 3 / 0.00156556 |
| poolact | tuning | all/all | cost_moderate | naive | gap_bon | Gap points | 98.7009 | 9/9 | 0 | 3 | 98.7009 | 3 / 0.268677 |
| poolact | tuning | all/all | cost_moderate | naive | gap_mi | Gap points | 96.923 | 9/9 | 0 | 3 | 96.923 | 3 / 0.717014 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_bon | fraction | 0.942059 | 9/9 | 0 | 3 | 0.942059 | 3 / 0.000950685 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_mi | fraction | 0.933885 | 9/9 | 0 | 3 | 0.933885 | 3 / 0.00442297 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_bon | Gap points | 99.1479 | 9/9 | 0 | 3 | 99.1479 | 3 / 0.267095 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_mi | Gap points | 98.8695 | 9/9 | 0 | 3 | 98.8695 | 3 / 0.264573 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_bon | fraction | 0.943754 | 9/9 | 0 | 3 | 0.943754 | 3 / 0.00106122 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_mi | fraction | 0.942661 | 9/9 | 0 | 3 | 0.942661 | 3 / 0.00103685 |
| poolact | tuning | all/all | cost_tight | cached | gap_bon | Gap points | 98.1504 | 9/9 | 0 | 3 | 98.1504 | 3 / 0.316521 |
| poolact | tuning | all/all | cost_tight | cached | gap_mi | Gap points | 90.7576 | 9/9 | 0 | 3 | 90.7576 | 3 / 4.33446 |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_bon | fraction | 0.937934 | 9/9 | 0 | 3 | 0.937934 | 3 / 0.00258256 |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_mi | fraction | 0.899698 | 9/9 | 0 | 3 | 0.899698 | 3 / 0.0275565 |
| poolact | tuning | all/all | cost_tight | naive | gap_bon | Gap points | 98.5243 | 9/9 | 0 | 3 | 98.5243 | 3 / 0.495823 |
| poolact | tuning | all/all | cost_tight | naive | gap_mi | Gap points | 90.6211 | 9/9 | 0 | 3 | 90.6211 | 3 / 3.79446 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_bon | fraction | 0.941273 | 9/9 | 0 | 3 | 0.941273 | 3 / 0.00229571 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_mi | fraction | 0.891752 | 9/9 | 0 | 3 | 0.891752 | 3 / 0.0391485 |
| poolact | tuning | all/all | cost_tight | poolact | gap_bon | Gap points | 98.2911 | 9/9 | 0 | 3 | 98.2911 | 3 / 0.166013 |
| poolact | tuning | all/all | cost_tight | poolact | gap_mi | Gap points | 96.2707 | 9/9 | 0 | 3 | 96.2707 | 3 / 0.86707 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_bon | fraction | 0.938869 | 9/9 | 0 | 3 | 0.938869 | 3 / 0.001521 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_mi | fraction | 0.930763 | 9/9 | 0 | 3 | 0.930763 | 3 / 0.00170524 |


cached−naive 描述共享缓存对照；poolact−cached 描述在该设置下进一步协调的差异；poolact−naive 是整体差异，不能据此分离所有机制或宣称相同 GPU 成本。

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mi | poolact − cached | +0.211538 | fraction | +21.1538 | 13/13 | 0 | 0.211538 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mv | poolact − cached | +0.190045 | fraction | +19.0045 | 13/13 | 0 | 0.190045 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mi | poolact − cached | +0.0622172 | fraction | +6.22172 | 13/13 | 0 | 0.0622172 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mv | poolact − cached | +0.0678733 | fraction | +6.78733 | 13/13 | 0 | 0.0678733 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mi | cached − naive | +0.0361991 | fraction | +3.61991 | 13/13 | 0 | 0.0361991 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mi | poolact − naive | +0.247738 | fraction | +24.7738 | 13/13 | 0 | 0.247738 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mv | cached − naive | +0.0588235 | fraction | +5.88235 | 13/13 | 0 | 0.0588235 |
| poolact | evidence_audit | all/all | cost_moderate | evidence_acc_mv | poolact − naive | +0.248869 | fraction | +24.8869 | 13/13 | 0 | 0.248869 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mi | cached − naive | +0.00113122 | fraction | +0.113122 | 13/13 | 0 | 0.00113122 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mi | poolact − naive | +0.0633484 | fraction | +6.33484 | 13/13 | 0 | 0.0633484 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mv | cached − naive | -0.00904977 | fraction | -0.904977 | 13/13 | 0 | -0.00904977 |
| poolact | evidence_audit | all/all | cost_moderate | label_acc_mv | poolact − naive | +0.0588235 | fraction | +5.88235 | 13/13 | 0 | 0.0588235 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mi | poolact − cached | +0.0418552 | fraction | +4.18552 | 13/13 | 0 | 0.0418552 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mv | poolact − cached | +0.0361991 | fraction | +3.61991 | 13/13 | 0 | 0.0361991 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mi | poolact − cached | +0.0169683 | fraction | +1.69683 | 13/13 | 0 | 0.0169683 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mv | poolact − cached | +0.0180995 | fraction | +1.80995 | 13/13 | 0 | 0.0180995 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mi | cached − naive | +0.0384615 | fraction | +3.84615 | 13/13 | 0 | 0.0384615 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mi | poolact − naive | +0.0803167 | fraction | +8.03167 | 13/13 | 0 | 0.0803167 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mv | cached − naive | +0.040724 | fraction | +4.0724 | 13/13 | 0 | 0.040724 |
| poolact | evidence_audit | all/all | cost_tight | evidence_acc_mv | poolact − naive | +0.0769231 | fraction | +7.69231 | 13/13 | 0 | 0.0769231 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mi | cached − naive | +0.020362 | fraction | +2.0362 | 13/13 | 0 | 0.020362 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mi | poolact − naive | +0.0373303 | fraction | +3.73303 | 13/13 | 0 | 0.0373303 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mv | cached − naive | +0.00452489 | fraction | +0.452489 | 13/13 | 0 | 0.00452489 |
| poolact | evidence_audit | all/all | cost_tight | label_acc_mv | poolact − naive | +0.0226244 | fraction | +2.26244 | 13/13 | 0 | 0.0226244 |
| poolact | restricted_search | all/all | cost_moderate | f1_mi | poolact − cached | +0.0325878 | fraction | +3.25878 | 39/39 | 0 | 0.0325878 |
| poolact | restricted_search | all/all | cost_moderate | f1_mv | poolact − cached | +0.0231176 | fraction | +2.31176 | 39/39 | 0 | 0.0231176 |
| poolact | restricted_search | all/all | cost_moderate | f1_mi | cached − naive | +0.0017932 | fraction | +0.17932 | 39/39 | 0 | 0.0017932 |
| poolact | restricted_search | all/all | cost_moderate | f1_mi | poolact − naive | +0.034381 | fraction | +3.4381 | 39/39 | 0 | 0.034381 |
| poolact | restricted_search | all/all | cost_moderate | f1_mv | cached − naive | -0.000407 | fraction | -0.0407 | 39/39 | 0 | -0.000407 |
| poolact | restricted_search | all/all | cost_moderate | f1_mv | poolact − naive | +0.0227106 | fraction | +2.27106 | 39/39 | 0 | 0.0227106 |
| poolact | restricted_search | all/all | cost_tight | f1_mi | poolact − cached | +0.00379751 | fraction | +0.379751 | 39/39 | 0 | 0.00379751 |
| poolact | restricted_search | all/all | cost_tight | f1_mv | poolact − cached | -0.0262515 | fraction | -2.62515 | 39/39 | 0 | -0.0262515 |
| poolact | restricted_search | all/all | cost_tight | f1_mi | cached − naive | +0.0375819 | fraction | +3.75819 | 39/39 | 0 | 0.0375819 |
| poolact | restricted_search | all/all | cost_tight | f1_mi | poolact − naive | +0.0413794 | fraction | +4.13794 | 39/39 | 0 | 0.0413794 |
| poolact | restricted_search | all/all | cost_tight | f1_mv | cached − naive | +0.0501832 | fraction | +5.01832 | 39/39 | 0 | 0.0501832 |
| poolact | restricted_search | all/all | cost_tight | f1_mv | poolact − naive | +0.0239316 | fraction | +2.39316 | 39/39 | 0 | 0.0239316 |
| poolact | tuning | all/all | cost_moderate | gap_bon | poolact − cached | +0.144411 | Gap points | 不适用 | 9/9 | 0 | 0.144411 |
| poolact | tuning | all/all | cost_moderate | gap_mi | poolact − cached | +1.14615 | Gap points | 不适用 | 9/9 | 0 | 1.14615 |
| poolact | tuning | all/all | cost_moderate | raw_perf_bon | poolact − cached | +0.000838368 | fraction | +0.0838368 | 9/9 | 0 | 0.000838368 |
| poolact | tuning | all/all | cost_moderate | raw_perf_mi | poolact − cached | +0.00547264 | fraction | +0.547264 | 9/9 | 0 | 0.00547264 |
| poolact | tuning | all/all | cost_moderate | gap_bon | cached − naive | +0.302657 | Gap points | 不适用 | 9/9 | 0 | 0.302657 |
| poolact | tuning | all/all | cost_moderate | gap_bon | poolact − naive | +0.447068 | Gap points | 不适用 | 9/9 | 0 | 0.447068 |
| poolact | tuning | all/all | cost_moderate | gap_mi | cached − naive | +0.800382 | Gap points | 不适用 | 9/9 | 0 | 0.800382 |
| poolact | tuning | all/all | cost_moderate | gap_mi | poolact − naive | +1.94653 | Gap points | 不适用 | 9/9 | 0 | 1.94653 |
| poolact | tuning | all/all | cost_moderate | raw_perf_bon | cached − naive | +0.000856927 | fraction | +0.0856927 | 9/9 | 0 | 0.000856927 |
| poolact | tuning | all/all | cost_moderate | raw_perf_bon | poolact − naive | +0.0016953 | fraction | +0.16953 | 9/9 | 0 | 0.0016953 |
| poolact | tuning | all/all | cost_moderate | raw_perf_mi | cached − naive | +0.00330344 | fraction | +0.330344 | 9/9 | 0 | 0.00330344 |
| poolact | tuning | all/all | cost_moderate | raw_perf_mi | poolact − naive | +0.00877608 | fraction | +0.877608 | 9/9 | 0 | 0.00877608 |
| poolact | tuning | all/all | cost_tight | gap_bon | poolact − cached | +0.140699 | Gap points | 不适用 | 9/9 | 0 | 0.140699 |
| poolact | tuning | all/all | cost_tight | gap_mi | poolact − cached | +5.51307 | Gap points | 不适用 | 9/9 | 0 | 5.51307 |
| poolact | tuning | all/all | cost_tight | raw_perf_bon | poolact − cached | +0.000934824 | fraction | +0.0934824 | 9/9 | 0 | 0.000934824 |
| poolact | tuning | all/all | cost_tight | raw_perf_mi | poolact − cached | +0.0310654 | fraction | +3.10654 | 9/9 | 0 | 0.0310654 |
| poolact | tuning | all/all | cost_tight | gap_bon | cached − naive | -0.373878 | Gap points | 不适用 | 9/9 | 0 | -0.373878 |
| poolact | tuning | all/all | cost_tight | gap_bon | poolact − naive | -0.233179 | Gap points | 不适用 | 9/9 | 0 | -0.233179 |
| poolact | tuning | all/all | cost_tight | gap_mi | cached − naive | +0.136512 | Gap points | 不适用 | 9/9 | 0 | 0.136512 |
| poolact | tuning | all/all | cost_tight | gap_mi | poolact − naive | +5.64958 | Gap points | 不适用 | 9/9 | 0 | 5.64958 |
| poolact | tuning | all/all | cost_tight | raw_perf_bon | cached − naive | -0.00333867 | fraction | -0.333867 | 9/9 | 0 | -0.00333867 |
| poolact | tuning | all/all | cost_tight | raw_perf_bon | poolact − naive | -0.00240385 | fraction | -0.240385 | 9/9 | 0 | -0.00240385 |
| poolact | tuning | all/all | cost_tight | raw_perf_mi | cached − naive | +0.00794605 | fraction | +0.794605 | 9/9 | 0 | 0.00794605 |
| poolact | tuning | all/all | cost_tight | raw_perf_mi | poolact − naive | +0.0390115 | fraction | +3.90115 | 9/9 | 0 | 0.0390115 |


全部预定义 family / tuning task 的绝对值及对应差值见 [TABLES.md](TABLES.md)，R3 明细见 [REPEATS.md](REPEATS.md)。不按结果方向删减家族或任务。

## 5. 资源与时间

### 5.1 实际分配成本与正式队列墙钟

以下来自操作方采集并冻结的 Slurm/正式队列账本；本生成器检查身份和算术，未现场查询 Slurm。范围是账本明确列出的顶层 serving jobs，不重复计算 .batch/.extern 等 step。

| Slurm job | 角色 | 状态 | 实际 start UTC | 实际 end UTC | 终态 Slurm elapsed 秒 | 分配 nodes | 分配 GPU 总数 | allocation GPU-hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1204491 | startup_attempt | FAILED | 2026-09-10T22:45:39Z | 2026-09-10T23:25:06Z | 2367 | 4 | 32 | 21.04 |
| 1204495 | formal_serving | CANCELLED | 2026-09-10T23:27:01Z | 2026-09-11T13:25:27Z | 50306 | 4 | 32 | 447.164 |


完整分配成本 = 468.204 GPU-hours；仅已知终态子集合计 = 468.204 GPU-hours（known/expected jobs：2/2）。计算为每个 job 的实际分配 GPU 总数 × Slurm elapsed 秒 ÷ 3600，再按唯一 job 相加。

allocation GPU-hours 是资源保留量，不是有效 GPU compute、实测利用率或 formal-only 消耗；冷加载、失败启动、smoke、等待和空闲均可能包含其中，不按最终有效答案扣除。运行中或 END 未知时，最终 elapsed/GPU-hours 显示 unknown，原账本的中途 elapsed 不当作终态，也不外推到 now。

| 正式 queue session | 状态 | workers（并行 invocation 上限） | start UTC | end UTC | session 墙钟秒（单调 elapsed） |
| --- | --- | --- | --- | --- | --- |
| 1789084311493837147-2799794 | stopped | 16 | 2026-09-10T23:51:51.514375Z | 2026-09-11T02:08:28.109206Z | 8196.59 |
| 1789092647915522583-2932149 | completed | 6 | 2026-09-11T02:10:47.918747Z | 2026-09-11T13:24:48.441054Z | 40440.5 |


正式 queue session 墙钟与 serving allocation 计时范围不同，不与 HTTP 请求时长相加；多个 session 的墙钟也不简单相加冒充整体实验历时。Slurm 秒级字段允许 1 秒误差；队列单调 elapsed 对事件 UTC 起止允许 2 秒误差，不要求纳秒级相等。

### 5.2 HTTP 尝试成本与分析单元资源

下表为正式计划范围内完整 HTTP 尝试账本的独立总计：all_physical_attempts 包含保留的失败/恢复前尝试，effective_slots 只属于最终授权槽位。native/task smoke 的诊断请求另见原件索引，不纳入此表或正式性能分母；上节 serving allocation 则包含这些准备阶段。reasoning 已包含在 output，不能再加一次。unknown 表示必要用量缺失，旁列仅是已知尝试子集。

| 范围 | 指标 | 单位 | 完整总计 | 已知子集合计 | known/expected 尝试 |
| --- | --- | --- | --- | --- | --- |
| all_physical_attempts | input_tokens | tokens | 1.40856e+08 | 1.40856e+08 | 18121/18121 |
| all_physical_attempts | output_tokens | tokens | 1.46525e+07 | 1.46525e+07 | 18121/18121 |
| all_physical_attempts | reasoning_tokens_included_in_output | tokens | 1.27858e+07 | 1.27858e+07 | 18121/18121 |
| all_physical_attempts | request_wall_seconds | seconds | 482219 | 482219 | 18121/18121 |
| all_physical_attempts | total_tokens | tokens | 1.55508e+08 | 1.55508e+08 | 18121/18121 |
| effective_slots | input_tokens | tokens | 1.40856e+08 | 1.40856e+08 | 18121/18121 |
| effective_slots | output_tokens | tokens | 1.46525e+07 | 1.46525e+07 | 18121/18121 |
| effective_slots | reasoning_tokens_included_in_output | tokens | 1.27858e+07 | 1.27858e+07 | 18121/18121 |
| effective_slots | request_wall_seconds | seconds | 482219 | 482219 | 18121/18121 |
| effective_slots | total_tokens | tokens | 1.55508e+08 | 1.55508e+08 | 18121/18121 |


每分析单元资源均值如下；完整 family/task 资源表在 TABLES.md。Pool 的 token、反馈和模拟成本按池内 N 个 agent 合计；Exp Audit 资源按三个顺序均值展示，物理尝试成本则仍逐执行计入上表。

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | single | duplicate_action_attempts | count | 0.025641 | 13/13 | 0 | 13 | 0.025641 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_attempts | count | 27.8205 | 13/13 | 0 | 13 | 27.8205 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_cost_seconds | seconds | 8356.56 | 13/13 | 0 | 13 | 8356.56 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_visible | count | 27.8205 | 13/13 | 0 | 13 | 27.8205 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | input_tokens | tokens | 307147 | 13/13 | 0 | 13 | 307147 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | output_tokens | tokens | 13626.3 | 13/13 | 0 | 13 | 13626.3 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | protocol_failure_rate | fraction | 0.01859 | 13/13 | 0 | 13 | 0.01859 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | wall_time_seconds | seconds | 562.461 | 13/13 | 0 | 13 | 562.461 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | budget_utilization | fraction | 0.980844 | 13/13 | 0 | 13 | 0.980844 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_attempts | count | 9.76923 | 13/13 | 0 | 13 | 9.76923 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 2942.53 | 13/13 | 0 | 13 | 2942.53 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_visible | count | 9.35897 | 13/13 | 0 | 13 | 9.35897 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | input_tokens | tokens | 95237.2 | 13/13 | 0 | 13 | 95237.2 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | output_tokens | tokens | 12671.3 | 13/13 | 0 | 13 | 12671.3 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.0042735 | 13/13 | 0 | 13 | 0.0042735 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | wall_time_seconds | seconds | 464.679 | 13/13 | 0 | 13 | 464.679 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | budget_utilization | fraction | 1.01773 | 13/13 | 0 | 13 | 1.01773 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_attempts | count | 3.05128 | 13/13 | 0 | 13 | 3.05128 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_cost_seconds | seconds | 915.954 | 13/13 | 0 | 13 | 915.954 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_visible | count | 2.4359 | 13/13 | 0 | 13 | 2.4359 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | input_tokens | tokens | 29621.7 | 13/13 | 0 | 13 | 29621.7 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | output_tokens | tokens | 10947.3 | 13/13 | 0 | 13 | 10947.3 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.00854701 | 13/13 | 0 | 13 | 0.00854701 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | wall_time_seconds | seconds | 410.386 | 13/13 | 0 | 13 | 410.386 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | duplicate_action_attempts | count | 0.0410959 | 73/73 | 0 | 73 | 0.0410959 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_attempts | count | 14.6438 | 73/73 | 0 | 73 | 14.6438 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_cost_seconds | seconds | 3497.12 | 73/73 | 0 | 73 | 3497.12 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_visible | count | 14.6438 | 73/73 | 0 | 73 | 14.6438 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | input_tokens | tokens | 83932.8 | 73/73 | 0 | 73 | 83932.8 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | output_tokens | tokens | 6003.32 | 73/73 | 0 | 73 | 6003.32 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | protocol_failure_rate | fraction | 0.0336668 | 73/73 | 0 | 73 | 0.0336668 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | wall_time_seconds | seconds | 258.116 | 73/73 | 0 | 73 | 258.116 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | budget_utilization | fraction | 0.825366 | 73/73 | 0 | 73 | 0.825366 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | duplicate_action_attempts | count | 0.0547945 | 73/73 | 0 | 73 | 0.0547945 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_attempts | count | 10.7671 | 73/73 | 0 | 73 | 10.7671 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 2476.1 | 73/73 | 0 | 73 | 2476.1 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_visible | count | 10.4658 | 73/73 | 0 | 73 | 10.4658 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | input_tokens | tokens | 53450.2 | 73/73 | 0 | 73 | 53450.2 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | output_tokens | tokens | 5958.51 | 73/73 | 0 | 73 | 5958.51 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.0455848 | 73/73 | 0 | 73 | 0.0455848 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | wall_time_seconds | seconds | 246.692 | 73/73 | 0 | 73 | 246.692 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | budget_utilization | fraction | 1.09615 | 73/73 | 0 | 73 | 1.09615 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | duplicate_action_attempts | count | 0.0136986 | 73/73 | 0 | 73 | 0.0136986 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_attempts | count | 4.0137 | 73/73 | 0 | 73 | 4.0137 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_cost_seconds | seconds | 986.534 | 73/73 | 0 | 73 | 986.534 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_visible | count | 3.35616 | 73/73 | 0 | 73 | 3.35616 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | input_tokens | tokens | 9639.47 | 73/73 | 0 | 73 | 9639.47 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | output_tokens | tokens | 2305.89 | 73/73 | 0 | 73 | 2305.89 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.0550554 | 73/73 | 0 | 73 | 0.0550554 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | wall_time_seconds | seconds | 86.6643 | 73/73 | 0 | 73 | 86.6643 | 1 / unknown |
| expgym | tuning | all/all | cost_free | single | duplicate_action_attempts | count | 0.185185 | 27/27 | 0 | 9 | 0.185185 | 3 / 0.1283 |
| expgym | tuning | all/all | cost_free | single | feedback_attempts | count | 29.0741 | 27/27 | 0 | 9 | 29.0741 | 3 / 0.739814 |
| expgym | tuning | all/all | cost_free | single | feedback_cost_seconds | seconds | 312526 | 27/27 | 0 | 9 | 312526 | 3 / 4786.27 |
| expgym | tuning | all/all | cost_free | single | feedback_visible | count | 29.0741 | 27/27 | 0 | 9 | 29.0741 | 3 / 0.739814 |
| expgym | tuning | all/all | cost_free | single | input_tokens | tokens | 267768 | 27/27 | 0 | 9 | 267768 | 3 / 10232.3 |
| expgym | tuning | all/all | cost_free | single | output_tokens | tokens | 13746.3 | 27/27 | 0 | 9 | 13746.3 | 3 / 2582.25 |
| expgym | tuning | all/all | cost_free | single | protocol_failure_rate | fraction | 0.0088942 | 27/27 | 0 | 9 | 0.0088942 | 3 / 0.00635119 |
| expgym | tuning | all/all | cost_free | single | wall_time_seconds | seconds | 503.443 | 27/27 | 0 | 9 | 503.443 | 3 / 93.3476 |
| expgym | tuning | all/all | cost_moderate | single | budget_utilization | fraction | 0.929251 | 27/27 | 0 | 9 | 0.929251 | 3 / 0.0167424 |
| expgym | tuning | all/all | cost_moderate | single | duplicate_action_attempts | count | 0.037037 | 27/27 | 0 | 9 | 0.037037 | 3 / 0.06415 |
| expgym | tuning | all/all | cost_moderate | single | feedback_attempts | count | 9.66667 | 27/27 | 0 | 9 | 9.66667 | 3 / 0.509175 |
| expgym | tuning | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 112730 | 27/27 | 0 | 9 | 112730 | 3 / 1640.56 |
| expgym | tuning | all/all | cost_moderate | single | feedback_visible | count | 9.59259 | 27/27 | 0 | 9 | 9.59259 | 3 / 0.525091 |
| expgym | tuning | all/all | cost_moderate | single | input_tokens | tokens | 64952.8 | 27/27 | 0 | 9 | 64952.8 | 3 / 7593.76 |
| expgym | tuning | all/all | cost_moderate | single | output_tokens | tokens | 7655.89 | 27/27 | 0 | 9 | 7655.89 | 3 / 1092.65 |
| expgym | tuning | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.023952 | 27/27 | 0 | 9 | 0.023952 | 3 / 0.00408001 |
| expgym | tuning | all/all | cost_moderate | single | wall_time_seconds | seconds | 286.81 | 27/27 | 0 | 9 | 286.81 | 3 / 41.9926 |
| expgym | tuning | all/all | cost_tight | single | budget_utilization | fraction | 1.10872 | 27/27 | 0 | 9 | 1.10872 | 3 / 0.0439762 |
| expgym | tuning | all/all | cost_tight | single | duplicate_action_attempts | count | 0 | 27/27 | 0 | 9 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_tight | single | feedback_attempts | count | 3.81481 | 27/27 | 0 | 9 | 3.81481 | 3 / 0.669746 |
| expgym | tuning | all/all | cost_tight | single | feedback_cost_seconds | seconds | 38539.2 | 27/27 | 0 | 9 | 38539.2 | 3 / 3325.8 |
| expgym | tuning | all/all | cost_tight | single | feedback_visible | count | 3.22222 | 27/27 | 0 | 9 | 3.22222 | 3 / 0.7698 |
| expgym | tuning | all/all | cost_tight | single | input_tokens | tokens | 23737.1 | 27/27 | 0 | 9 | 23737.1 | 3 / 4180.96 |
| expgym | tuning | all/all | cost_tight | single | output_tokens | tokens | 6487.81 | 27/27 | 0 | 9 | 6487.81 | 3 / 695.72 |
| expgym | tuning | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.0188713 | 27/27 | 0 | 9 | 0.0188713 | 3 / 0.0190501 |
| expgym | tuning | all/all | cost_tight | single | wall_time_seconds | seconds | 227.094 | 27/27 | 0 | 9 | 227.094 | 3 / 38.7972 |
| poolact | evidence_audit | all/all | cost_moderate | cached | budget_utilization | fraction | 0.992037 | 13/13 | 0 | 13 | 0.992037 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | duplicate_action_attempts | count | 22.8462 | 13/13 | 0 | 13 | 22.8462 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_attempts | count | 44.3846 | 13/13 | 0 | 13 | 44.3846 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 11904.4 | 13/13 | 0 | 13 | 11904.4 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | input_tokens | tokens | 432018 | 13/13 | 0 | 13 | 432018 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | output_tokens | tokens | 45707.3 | 13/13 | 0 | 13 | 45707.3 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.00458645 | 13/13 | 0 | 13 | 0.00458645 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | budget_utilization | fraction | 0.991054 | 13/13 | 0 | 13 | 0.991054 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | duplicate_action_attempts | count | 19.2308 | 13/13 | 0 | 13 | 19.2308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_attempts | count | 39.4615 | 13/13 | 0 | 13 | 39.4615 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 11892.6 | 13/13 | 0 | 13 | 11892.6 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | input_tokens | tokens | 367328 | 13/13 | 0 | 13 | 367328 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | output_tokens | tokens | 44462.9 | 13/13 | 0 | 13 | 44462.9 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.00858935 | 13/13 | 0 | 13 | 0.00858935 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.946671 | 13/13 | 0 | 13 | 0.946671 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 8.92308 | 13/13 | 0 | 13 | 8.92308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_attempts | count | 37.7692 | 13/13 | 0 | 13 | 37.7692 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 11360.1 | 13/13 | 0 | 13 | 11360.1 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | input_tokens | tokens | 607185 | 13/13 | 0 | 13 | 607185 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | output_tokens | tokens | 60782.2 | 13/13 | 0 | 13 | 60782.2 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.0127373 | 13/13 | 0 | 13 | 0.0127373 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | budget_utilization | fraction | 0.980283 | 13/13 | 0 | 13 | 0.980283 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | duplicate_action_attempts | count | 5.92308 | 13/13 | 0 | 13 | 5.92308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_attempts | count | 11.8462 | 13/13 | 0 | 13 | 11.8462 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 3529.02 | 13/13 | 0 | 13 | 3529.02 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | input_tokens | tokens | 115659 | 13/13 | 0 | 13 | 115659 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | output_tokens | tokens | 47583 | 13/13 | 0 | 13 | 47583 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.00857347 | 13/13 | 0 | 13 | 0.00857347 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | budget_utilization | fraction | 0.992365 | 13/13 | 0 | 13 | 0.992365 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | duplicate_action_attempts | count | 6.30769 | 13/13 | 0 | 13 | 6.30769 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_attempts | count | 11.8462 | 13/13 | 0 | 13 | 11.8462 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 3572.51 | 13/13 | 0 | 13 | 3572.51 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | input_tokens | tokens | 109687 | 13/13 | 0 | 13 | 109687 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | output_tokens | tokens | 43988.4 | 13/13 | 0 | 13 | 43988.4 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | budget_utilization | fraction | 1.00332 | 13/13 | 0 | 13 | 1.00332 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | duplicate_action_attempts | count | 3.23077 | 13/13 | 0 | 13 | 3.23077 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_attempts | count | 12 | 13/13 | 0 | 13 | 12 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 3611.96 | 13/13 | 0 | 13 | 3611.96 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | input_tokens | tokens | 121894 | 13/13 | 0 | 13 | 121894 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | output_tokens | tokens | 45493.9 | 13/13 | 0 | 13 | 45493.9 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.00885628 | 13/13 | 0 | 13 | 0.00885628 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | budget_utilization | fraction | 0.758836 | 39/39 | 0 | 39 | 0.758836 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | duplicate_action_attempts | count | 25.7179 | 39/39 | 0 | 39 | 25.7179 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_attempts | count | 47.4615 | 39/39 | 0 | 39 | 47.4615 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 9106.03 | 39/39 | 0 | 39 | 9106.03 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | input_tokens | tokens | 250738 | 39/39 | 0 | 39 | 250738 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | output_tokens | tokens | 23713.9 | 39/39 | 0 | 39 | 23713.9 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.0437267 | 39/39 | 0 | 39 | 0.0437267 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | budget_utilization | fraction | 0.819506 | 39/39 | 0 | 39 | 0.819506 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | duplicate_action_attempts | count | 24.5128 | 39/39 | 0 | 39 | 24.5128 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_attempts | count | 45.1795 | 39/39 | 0 | 39 | 45.1795 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 9834.08 | 39/39 | 0 | 39 | 9834.08 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | input_tokens | tokens | 230992 | 39/39 | 0 | 39 | 230992 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | output_tokens | tokens | 25173.2 | 39/39 | 0 | 39 | 25173.2 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.0487763 | 39/39 | 0 | 39 | 0.0487763 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.655585 | 39/39 | 0 | 39 | 0.655585 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 21.2308 | 39/39 | 0 | 39 | 21.2308 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_attempts | count | 44.4872 | 39/39 | 0 | 39 | 44.4872 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 7867.02 | 39/39 | 0 | 39 | 7867.02 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | input_tokens | tokens | 548091 | 39/39 | 0 | 39 | 548091 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | output_tokens | tokens | 35190.8 | 39/39 | 0 | 39 | 35190.8 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.00973334 | 39/39 | 0 | 39 | 0.00973334 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | budget_utilization | fraction | 1.08491 | 39/39 | 0 | 39 | 1.08491 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | duplicate_action_attempts | count | 9.46154 | 39/39 | 0 | 39 | 9.46154 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_attempts | count | 16.4103 | 39/39 | 0 | 39 | 16.4103 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 3905.68 | 39/39 | 0 | 39 | 3905.68 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | input_tokens | tokens | 35458.3 | 39/39 | 0 | 39 | 35458.3 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | output_tokens | tokens | 6880.9 | 39/39 | 0 | 39 | 6880.9 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.0671366 | 39/39 | 0 | 39 | 0.0671366 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | budget_utilization | fraction | 1.1019 | 39/39 | 0 | 39 | 1.1019 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | duplicate_action_attempts | count | 9.74359 | 39/39 | 0 | 39 | 9.74359 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_attempts | count | 16.5128 | 39/39 | 0 | 39 | 16.5128 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 3966.82 | 39/39 | 0 | 39 | 3966.82 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | input_tokens | tokens | 34095.2 | 39/39 | 0 | 39 | 34095.2 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | output_tokens | tokens | 7174.33 | 39/39 | 0 | 39 | 7174.33 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.0525472 | 39/39 | 0 | 39 | 0.0525472 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | budget_utilization | fraction | 1.0877 | 39/39 | 0 | 39 | 1.0877 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | duplicate_action_attempts | count | 4.71795 | 39/39 | 0 | 39 | 4.71795 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_attempts | count | 16.5385 | 39/39 | 0 | 39 | 16.5385 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 3915.71 | 39/39 | 0 | 39 | 3915.71 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | input_tokens | tokens | 60483.8 | 39/39 | 0 | 39 | 60483.8 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | output_tokens | tokens | 14122.6 | 39/39 | 0 | 39 | 14122.6 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.0162939 | 39/39 | 0 | 39 | 0.0162939 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | budget_utilization | fraction | 0.979511 | 9/9 | 0 | 3 | 0.979511 | 3 / 0.0242982 |
| poolact | tuning | all/all | cost_moderate | cached | duplicate_action_attempts | count | 0.333333 | 9/9 | 0 | 3 | 0.333333 | 3 / 0 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_attempts | count | 46.6667 | 9/9 | 0 | 3 | 46.6667 | 3 / 3.1798 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 344912 | 9/9 | 0 | 3 | 344912 | 3 / 5388.06 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | input_tokens | tokens | 669798 | 9/9 | 0 | 3 | 669798 | 3 / 32659.4 |
| poolact | tuning | all/all | cost_moderate | cached | output_tokens | tokens | 61250.9 | 9/9 | 0 | 3 | 61250.9 | 3 / 5192.04 |
| poolact | tuning | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.0273574 | 9/9 | 0 | 3 | 0.0273574 | 3 / 0.0089794 |
| poolact | tuning | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | budget_utilization | fraction | 0.950695 | 9/9 | 0 | 3 | 0.950695 | 3 / 0.0141404 |
| poolact | tuning | all/all | cost_moderate | naive | duplicate_action_attempts | count | 0.666667 | 9/9 | 0 | 3 | 0.666667 | 3 / 0.333333 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_attempts | count | 46.8889 | 9/9 | 0 | 3 | 46.8889 | 3 / 5.67972 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 336391 | 9/9 | 0 | 3 | 336391 | 3 / 4830.55 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | input_tokens | tokens | 635250 | 9/9 | 0 | 3 | 635250 | 3 / 104855 |
| poolact | tuning | all/all | cost_moderate | naive | output_tokens | tokens | 57983.1 | 9/9 | 0 | 3 | 57983.1 | 3 / 5929.93 |
| poolact | tuning | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.0195836 | 9/9 | 0 | 3 | 0.0195836 | 3 / 0.0119131 |
| poolact | tuning | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.81604 | 9/9 | 0 | 3 | 0.81604 | 3 / 0.0336904 |
| poolact | tuning | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 1.88889 | 9/9 | 0 | 3 | 1.88889 | 3 / 0.3849 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_attempts | count | 39.6667 | 9/9 | 0 | 3 | 39.6667 | 3 / 4.91031 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 283669 | 9/9 | 0 | 3 | 283669 | 3 / 15602.3 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | input_tokens | tokens | 2.08789e+06 | 9/9 | 0 | 3 | 2.08789e+06 | 3 / 570805 |
| poolact | tuning | all/all | cost_moderate | poolact | output_tokens | tokens | 120290 | 9/9 | 0 | 3 | 120290 | 3 / 15752.3 |
| poolact | tuning | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.0147306 | 9/9 | 0 | 3 | 0.0147306 | 3 / 0.00912009 |
| poolact | tuning | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | budget_utilization | fraction | 1.11116 | 9/9 | 0 | 3 | 1.11116 | 3 / 0.040331 |
| poolact | tuning | all/all | cost_tight | cached | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | all/all | cost_tight | cached | feedback_attempts | count | 13.3333 | 9/9 | 0 | 3 | 13.3333 | 3 / 0.333333 |
| poolact | tuning | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 112835 | 9/9 | 0 | 3 | 112835 | 3 / 1857.69 |
| poolact | tuning | all/all | cost_tight | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | input_tokens | tokens | 141519 | 9/9 | 0 | 3 | 141519 | 3 / 13866.4 |
| poolact | tuning | all/all | cost_tight | cached | output_tokens | tokens | 37746 | 9/9 | 0 | 3 | 37746 | 3 / 8818.97 |
| poolact | tuning | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.0575375 | 9/9 | 0 | 3 | 0.0575375 | 3 / 0.0304565 |
| poolact | tuning | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | budget_utilization | fraction | 1.09346 | 9/9 | 0 | 3 | 1.09346 | 3 / 0.106143 |
| poolact | tuning | all/all | cost_tight | naive | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | all/all | cost_tight | naive | feedback_attempts | count | 12.1111 | 9/9 | 0 | 3 | 12.1111 | 3 / 1.64429 |
| poolact | tuning | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 113055 | 9/9 | 0 | 3 | 113055 | 3 / 7134.14 |
| poolact | tuning | all/all | cost_tight | naive | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | input_tokens | tokens | 129448 | 9/9 | 0 | 3 | 129448 | 3 / 11351.1 |
| poolact | tuning | all/all | cost_tight | naive | output_tokens | tokens | 32709.7 | 9/9 | 0 | 3 | 32709.7 | 3 / 5087.63 |
| poolact | tuning | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.0958787 | 9/9 | 0 | 3 | 0.0958787 | 3 / 0.0253025 |
| poolact | tuning | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | budget_utilization | fraction | 1.02778 | 9/9 | 0 | 3 | 1.02778 | 3 / 0.0341902 |
| poolact | tuning | all/all | cost_tight | poolact | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_attempts | count | 14.4444 | 9/9 | 0 | 3 | 14.4444 | 3 / 1.34715 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 104480 | 9/9 | 0 | 3 | 104480 | 3 / 4712.86 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | input_tokens | tokens | 293543 | 9/9 | 0 | 3 | 293543 | 3 / 73250.2 |
| poolact | tuning | all/all | cost_tight | poolact | output_tokens | tokens | 54818.2 | 9/9 | 0 | 3 | 54818.2 | 3 / 2782.29 |
| poolact | tuning | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.028719 | 9/9 | 0 | 3 | 0.028719 | 3 / 0.0146298 |
| poolact | tuning | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |


feedback_cost_seconds 是模拟反馈秒，不是 GPU 推理时长；预算利用率也不是 GPU 利用率。Pool 整个子进程 wall 未被该 exporter 记录，因此保持 unknown，不能以 agent wall 求和/最大值冒充。HTTP request wall 合计不是并发实验总历时；可选 accounting 的正式 queue wall 和 allocation GPU-hours 另列，仍没有 formal-only GPU 利用量，故不据此推算有效算力或速度优越性。

## 6. 主张、缺失与限制

当前表格能回答本模型、这些固定任务与设置下的方向和幅度；不能证明模型总体普适、未见任务泛化或统计显著性。负向结果保留，unknown 不补零。task-abstention-v1 下正常 Search/Audit 空回答可有合法零分；HPO 缺配置不可评分，不把二者当作同一种故障。

完整均值只在全部计划端点已知时给出；已知子集仅作诊断。配对差值使用完整计划 item×outerrep 范围，不静默取交集。R3 的 SD 是三个 block 的描述性变化，不是标准误、置信区间或独立生成证据；R1 不提供重复 SD。

## 7. 完整原件、聚合和存档入口

[原始 dump 存档索引](ARCHIVE_INDEX.md) · [机器可读存档索引](ARCHIVE_INDEX.json) · [旧双模型完整报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91/results/portable-eval-20260908/full_matrix_report_v1/README.zh.md)

存档索引应定位 collection/bundle → member inventory → tar 分片及匹配恢复工具。这里引用其固定版本，不重新扫描 tar、不声称已恢复或验证全部内容，也不把新 collection 引用的旧包再计作一份新物理副本。旧双模型报告仅供独立比较入口，不与本模型 all 直接合并。

- [COSTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/COSTS.json)
- [INPUTS.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/INPUTS.json)
- [SOURCE_INDEX.json](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/SOURCE_INDEX.json)
- [absolute_settings.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/absolute_settings.csv)
- [all_attempt_costs.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/all_attempt_costs.csv)
- [by_outerseed.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/by_outerseed.csv)
- [contrasts.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/contrasts.csv)
- [metrics.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/metrics.csv)
- [metrics_execution.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/metrics_execution.csv)
- [normalized.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/normalized.csv)
- [raw_terminals.csv](https://github.com/tiannuo-yang/LLM_ExpGym/blob/03dd6ef0ed9a63cb673a7b4e62a5a19026015225/results/qwen38-20260910/analysis/full_v1/raw_terminals.csv)

metrics_execution 是执行层；metrics 是 Audit 已折叠一次的分析层；normalized 是唯一有效槽位映射；raw_terminals 是终态投影，不是 HTTP 回复。all_attempt_costs 与原始请求/回复的完整映射入口分别是成本表和 SOURCE_INDEX/存档索引。

| 显式输入 | 字节 | SHA256 | 本次使用范围 |
| --- | --- | --- | --- |
| COSTS.json | 1641 | 1412dc9aef9a0632438199c31a68e09ce6d727fc07d802b1d3486a27c1ac6556 | 本次读取并校验 SHA |
| INPUTS.json | 1013 | a0f6ce918ac24d0c0f085499558b06f978693130b1aa96eb53be2f621520ffd7 | 本次读取并校验 SHA |
| SOURCE_INDEX.json | 1.28531e+07 | b3fac08779fc6d007fa3a1752db05c00559af5d5208131b748c131f7fd123884 | 仅继承冻结 pin、核大小并提供链接 |
| absolute_settings.csv | 338728 | fce30264431844fca613ee83aacf8a63f03892e224a52d0242294684df6a3547 | 本次读取并校验 SHA |
| all_attempt_costs.csv | 1.4132e+07 | cbd6e56a8e8e6c81b1eb4a9d43f8f6ccfeaaf5e53020ce46d55ae8586ee228a7 | 仅继承冻结 pin、核大小并提供链接 |
| by_outerseed.csv | 728488 | 3bdc8e05b3fdea3336be065babd03b2f4998098cf919ed63bd73c0970e19884a | 本次读取并校验 SHA |
| contrasts.csv | 409667 | 8de1afce1ecfa4c5d64b525ad4549620d8cf9d1e7a74c7cdaa373bb672efbcff | 本次读取并校验 SHA |
| metrics.csv | 3.69421e+06 | 412287f1e9fa108dcfd52be9a382e293009c4a1c2d93bd7094ef5331d277ac23 | 仅继承冻结 pin、核大小并提供链接 |
| metrics_execution.csv | 2.49032e+06 | f126039a7e155ad8843affe4c0ac40851e476c0c57d147d6085fccc3a0de0c23 | 仅继承冻结 pin、核大小并提供链接 |
| normalized.csv | 319923 | 0ec8b19d050582c5dba442189fa5282a821efb2ee4789ce8b4ff3df0d8e2b0e5 | 本次读取并校验 SHA |
| raw_terminals.csv | 1.75469e+06 | a62a4f1e76f56494939d9cfc9414c04c0e5eff244a5f06065b51f8991f421164 | 仅继承冻结 pin、核大小并提供链接 |
| accounting | 1402 | d4f798b5fcedae7e5c75c3daa018c3d08a0d90d85453fdded9f9a5414d4a82e9 | 本次读取并校验 SHA |
| coverage | 24867 | c3d2441bcd2719b43eb550ff9ae2f2956b603d2f15850423b2ee43f1d74abd5a | 本次读取并校验 SHA |
| oracle | 28814 | f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e | 本次读取并校验 SHA |
| plan | 3.77074e+06 | f6958c036bd3ba3dbda5de44d2810ca3cfbd0d6ae0f90d0253a2161b20a5d3fd | 本次读取并校验 SHA |
| run_inputs | 33532 | 6b1c51051a2176dcd2990306e1fc39676efa3564eeb85abde2773a6d94da69d8 | 本次读取并校验 SHA |
| serving_plan | 1716 | eb48590874a743c4ade35873c5f27494c4238d983973e6cc4fb2801f033475dc | 本次读取并校验 SHA |


## 8. 生成与有限验收

本稿最终生成器见 [同一报告提交的 build_report.py](../study/build_report.py)，输入描述见 [report_inputs.json](../study/report_inputs.json)。数据提交和 tar 内保留的是封存时的历史工具版本；成稿复核后的文案修订工具随本报告提交，不能将历史版本当作本稿实际生成器。分析数据与原始封包未改变。

报告输入描述 SHA256：`2d4b83c0933bfe2406ef27d7f42cfbb5a622b4e0aa948cfab07c159e3a72b9c9`；生成器 SHA256：`e083d04d620ba56aae75f5e9533f40b4d877f86e4fd6a1823905234096ccac9f`。没有模型调用、重评分、raw 恢复或归档内容扫描。

生成器检查 schema、固定输入 SHA、覆盖/分母、对照方向与均值差（1e-10 浮点容差）及固定提交链接格式；仅允许两份存档索引用精确同目录文件名，随本报告固定提交解析。显示保留六位有效数字，真实 CSV 值不改写。`--check` 只比较这三份 Markdown 的精确字节，不写文件。链接实际可达性、索引内容与一次成稿后的独立数值/逻辑复核仍由发布流程完成；本生成器不把自身检查称为独立复核。
