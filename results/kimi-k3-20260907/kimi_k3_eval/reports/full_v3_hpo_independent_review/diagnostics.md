# full_v3 HPO 独立原始轨迹检查：零分、最终回答来源与 NAS101 提示

本检查直接读取 `runs/full_v3/manifest.json` 选中的原始 trace、PoolAct result、逐 agent 文件及执行回执；不调用正式汇总器、benchmark 评分器或 LLM API。冻结源码 SHA256 为 `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`。读取方法见 `diagnostics.py`，所有逐项路径和 SHA256、原始最终回答及最后模型回答见 `diagnostics.json`；完整 task × regime × system × strategy 分组见 `diagnostics.csv`。

## 完整性与真实零分

54/54 HPO 子进程回执均为 completed、returncode=0。读取到 81 ExpGym traces、81 PoolAct results 和 324 PoolAct agent 文件。所有逐轨迹/agent 评分通过标记为 true；每个独立 agent 文件与对应 result 内嵌记录一致；各 PoolAct tuning aggregate 都等于四个 individual_perfs 的最大值；源码指纹一致。此处是原始完整性检查，不替代主审计中的独立 benchmark 重算。

| 对象 | 数量 | 记录为精确 0 的数量 | 零分分布 |
|---|---:|---:|---|
| ExpGym traces | 81 | 7 | NAS101 B: 6；C: 1 |
| PoolAct aggregate results | 81 | 2 | NAS101 B / cost_free / naive 与 cached |
| PoolAct agents | 324 | 26 | NAS101 A: 2；B: 22；C: 2 |

agent 层共有 33 个零分（7+26），不能再把 2 个 aggregate 零分加进去当作独立轨迹。ParamNet 三个任务、NAS201 三个任务均没有原始零分。

NAS101 B 的完整零分计数如下。ExpGym 每格 3 repeats；每个 PoolAct strategy 每格 4 agents。

| Regime | ExpGym | naive agents | cached agents | poolact agents | 为零的 PoolAct aggregate |
|---|---:|---:|---:|---:|---|
| cost_free | 1/3 | 4/4 | 4/4 | 1/4 | naive、cached |
| cost_moderate | 2/3 | 2/4 | 3/4 | 1/4 | 无 |
| cost_tight | 3/3 | 3/4 | 3/4 | 1/4 | 无 |

其他零分是 NAS101 A / poolact strategy 的 free agent 0、moderate agent 3，以及 NAS101 C 的 free naive agent 0、moderate poolact agent 3、tight ExpGym rep 1。

## 最终回答来源：可证明的范围

ExpGym `outcome.answer_source` 明确记录：forced_model_answer 55、natural_model_answer 20、best_evaluated_fallback 6。六个明确 fallback 如下；完整原始路径/哈希见 JSON 中 `expgym_explicit_fallback_records`。

| Task | Regime | Rep | 记录性能 | 终止原因 |
|---|---|---:|---:|---|
| ParamNet adult | tight | 1 | 0.8422037010656462 | time_budget_exceeded |
| ParamNet letter | moderate | 2 | 0.4752600696879725 | missing_action |
| NAS101 B | free | 1 | 0 | missing_action |
| NAS101 B | moderate | 2 | 0 | missing_action |
| NAS101 B | tight | 2 | 0 | missing_action |
| NAS101 C | tight | 1 | 0 | missing_action |

四个零分 fallback 的可见已评估记录本身没有正分。不要将它们解释为缺失运行，也不要把最后模型建议配置的假想分数当成正式结果。

PoolAct 的 324 条 agent 记录均未提供 `answer_source`。按当前冻结解析器提取 `messages` 最后一个 assistant 的回答，与正式 `answer` 比较：257 条完全相同，67 条不同，没有仅文本格式不同但 JSON 等价的记录。不同的 67 条分布为 naive 8、cached 5、poolact 54；每条正式 answer 均能在本 agent 的最高分可见 eval_records 中找到。JSON 中 `poolact_answer_differences` 保存全部比较证据。

这 67 条只能表述为“正式 answer 与最后模型提取不同，且匹配最佳可见评估”。因为来源字段缺失，本检查不将它们作为已明确记录的 fallback 次数；其余 257 条相同也不能证明未经过 fallback。17/26 个零分 PoolAct agents 明确有 `answer_score_source=offline_final_answer`，这个字段表示离线补最终分数，不是 fallback 来源标签。

## 高风险及低分原始案例

以下路径相对于 `/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/full_v3/`。

1. `poolact/tuning/hpobench_nasbench101_B/cost_free/naive/agents/agent_1.json`：0 分、0 次工具调用、`answer_score_source=offline_final_answer`，最终回答与最后模型提取一致，但含 B 不存在的 `edge_9` 至 `edge_20` 共 12 个额外键。SHA256 `9fb8dd1ba34766059c664f37104a408c9b55db1a61e968f0184eacbe6d38792a`。这是已保留的明确非法配置零分，不是缺失补 0。

2. `poolact/tuning/hpobench_nasbench101_B/cost_free/naive/agents/agent_0.json`：0 分、0 次工具调用、离线最终评分；仅合法 B 参数，但九个 selector 全为 1。当前 B 解码器生成单条 `4→6`，没有输入节点 0 到输出节点 6 的路径。SHA256 `c7bc504646d93e096efa8af62e0a77f9e3223de61f8c9153098816cdbc52263c`。不能按错误提示将该零分解释为“九个参数为 1 导致边数超限”。

3. `expgym/tuning/hpobench_nasbench101_C/cost_tight/Kimi-K3_cost_tight/traces-v2/tuning_hpobench_nasbench101_C_r1_s1207.json`：明确 best_evaluated_fallback，1 次工具调用、唯一可见评估为 0。正式 answer 的 21 个 priority 全为 0.5、num_edges=4；当前冻结 NumPy/解码器选出 `3→6,4→5,4→6,5→6`，没有 `0→6` 路径。最后模型实际提出了另一份二元优先级配置，该配置不是正式计分答案。SHA256 `54f7f18fe343a2e1498fee9cd8ae2b39984c98485f76d65f75e790451dbeaf40`。

4. `poolact/tuning/hpobench_nasbench101_C/cost_free/naive/agents/agent_0.json`：0 分、0 次工具调用、离线最终评分。最终 answer 与最后模型提取一致；num_edges=4，当前解码出的边为 `0→1,2→5,4→5,5→6`，没有完整输入输出路径。SHA256 `34dfd9d47630e06e75a27f2538136809d4ef034be2b77fd99305a27f3de346d6`。

5. `poolact/tuning/hpobench_nasbench101_C/cost_moderate/poolact/agents/agent_3.json`：0 分、1 条零分可见 eval record；正式 answer 与最后模型提取不同，正式 answer 匹配该可见记录。未记录 answer_source，不据此补写 fallback 标签。SHA256 `649681beff277a9d2b5e253a8905c15d34466438bdb102de7c2d6953fb9cac1a`。

6. `expgym/tuning/hpobench_paramnet_letter_steps/cost_moderate/Kimi-K3_cost_moderate/traces-v2/tuning_hpobench_paramnet_letter_steps_r2_s1208.json`：明确 fallback 至默认配置，性能仅 0.4752600696879725；终止原因 missing_action。最后模型提出另一份未成为正式计分答案的配置。SHA256 `b1d2b1323947b80a9f8d4d99e60b111314e2de989d433c8bc00d875915323ae5`。

NAS101 B 的 28/45 条 agent 层零分记录，正式配置的 edge 值全部仅有 0/1；其中 8 条带额外键（ExpGym 1、PoolAct 7），在正式工具路径中会先被参数检查拒绝。其余 20 条键合法的 B 零分配置经纯拓扑解码都只有 `4→6` 或 `4→6,5→6`，均不连接输入。其他 5 个 A/C 零分的合法配置也均无输入输出路径。这个补充只调用纯矩阵解码函数，没有调用 benchmark 或替换任何正式分数；对含额外键的 8 条不能绕过验证器后用拓扑替代其正式非法输入原因。

## NAS101 B/C 实际提示仍为 A 式

独立逐 raw 初始请求检查覆盖 90/90 个 B/C run 起始消息：ExpGym B/C 各 9；PoolAct B/C 在 naive/cached/poolact 各 12。全部仍含 `The edge_* parameters form the upper-triangular adjacency matrix (0 or 1) of the DAG.`、`Do NOT set all edges to 1` 和 `set unused edges to 0`。B 同一提示的参数表却给出 9 个取值 0..20 的槽，C 给出 21 个浮点 priority 和 num_edges。

原始请求代表路径相对于 `kimi_k3_eval/dumps/full-full_v3-ad4275b6/`：

| 请求 | 路径 | SHA256 |
|---|---|---|
| ExpGym B/free/rep0 | `expgym__tuning__hpobench_nasbench101_B__cost_free/d70a7de076f0464e9e37135649ddb929.json` | `92b99927fb94c7393181f400479d87b374c057c5794968459a5c79eab94ae0a0` |
| ExpGym C/free/rep0 | `expgym__tuning__hpobench_nasbench101_C__cost_free/aba28e93954446e98340292ff236353c.json` | `41086cd588333e412f1fa6826713da59a43932f2b9314a05f6e93a73afbc3105` |
| PoolAct B/free/poolact/agent0 | `poolact__tuning__hpobench_nasbench101_B__cost_free/e5d8abf2a2844b79b186ce507aeecb33.json` | `e8d87793650310e8558f1b7846b6ad4dcdeed240b3655a636c531afc18a86894` |
| PoolAct C/free/poolact/agent0 | `poolact__tuning__hpobench_nasbench101_C__cost_free/a5b31a7128fb41eda36a4f5acaacc837.json` | `f6ed9dc75c34ccd9f4f4ffd32d35c7b6eb1ad2f501c69ca44db153c13a239769` |

根源在 `expgym/task_tuning.py` 的 `_task_hints`：按 nasbench101 前缀为三个变体返回统一文本。`compact_nasbench101.py` 实际对 B 将参数值作为边编号 selector，重复合并，0 也是有效编号；例如 0→边5→6、1→边4→6、5→边0→6、20→边0→1。C 按 priority 排序取前 num_edges 条边，不是按数值为 1 的位置直接决定邻接矩阵。相同优先级使用 NumPy quicksort 的次序，不能假定稳定的编号优先约定。合法 B/C 的编码均至多选 9 条边，因此通用提示的“全部设 1 超过 9 条边”对它们不成立。

实际提示存在语义缺陷，且 B 的零分输出模式与误用二元邻接编码相容；没有做改提示的对照实验，不能断言这就是所有零分的唯一原因，也不能据此改分。C 的 44/45 份正式最终配置仅用 0/1 priority（另 1 份为全部 0.5）；二元 priority 本身合法，不能一概称为非法配置。

## 边界

本诊断保留全部零分、不修改冻结源码、提示、运行结果或原始 dump。没有根据 API 外部知识估计未评估配置性能；没有把最后模型建议强行替换为正式答案；没有将缺失 PoolAct 来源字段补成确定结论。PoolAct 四 agent 共享资源与各策略中终止/fallback 的因果效应需结合完整轨迹与协议说明另行分析。
