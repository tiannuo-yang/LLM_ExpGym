# 双模型冻结报告后的独立逻辑审阅

被审对象：`dual_model_analysis_v1`，INDEX SHA `3ff8e6d4b664fe2f5862ca6236d56077bdacef1668f692be09ecc29d43cf92c6`；REPORT SHA `2cb93a26292607c7707bad1e12b4b26dd3064c77e25fe68688370864af7ff70e`。先核 exact 6 文件，再实际审阅；没有改原报告、分析或实验。

结论：**未发现实质数值错误、负面或 unknown 遗漏；发现两处应在新修订附件中更正的报告问题。** 当前不无条件签署报告接受，也不称项目完成。两项均不要求修改原分数、parser、正式设置或重跑模型。原 v1 保留作为历史冻结记录。

审阅者不是报告作者、runner 或 exporter 作者；是此前独立 usage checker 和格式诊断器作者。本次 usage 证据不替代 metric/vote/aggregation 的独立证据。另一位非报告作者仅承担精确 effects/表格算术子审；主审另外直接重数固定 CSV、plan/execution、设置和关键图逻辑。

## 必须勘误

### F1：第 40 行把预定 R3 称为“独立”超出了证据

原文：“E-H 为九任务、三个独立外层重复”。数值与 R3 sample SD 本身正确，但“独立”是额外的统计/执行性质，不能由不同 seed 标签推出。

两个原 plan 均为 base_seed=2200，outer blocks 使用 2200–2203、2204–2207、2208–2211；每条 logical row 明写 `seed_control=not_verified_by_planner`。固定 `planner.py:254–255,294,316–317` 仅生成 seed 标签。K3 deployment 为 `seed_control_candidate`，GLM 为 `seed_labels_only`；后者明确不同 replica initialization seeds 不证明 iid。请求指定 seed、甚至确定性设置，也不自动证明外层统计独立。

建议新附件将该句限定为：“E-H 为九任务、三个预定外层 seed-block 重复；P-H 为 NAS101A、同样三个外层重复。服务端 seed 生效及统计独立性未在本研究中独立证明；SD 只描述三个 outer-bundle effects 的样本离散程度，不是 CI。”保留原第 9、40、86 行的 R1/R3、orders 不当 iid 和描述性限制，不增加显著性/稳定性措辞。

影响：措辞/证据强度问题，不改变六个主项或 SD。已证实的 sampler/profile 元数据不能被重写为全模型可复现性或 iid 证明。

### F2：第 82 行及 §5 对通用仓库修复交代不完整

§5 主要概述自 serving 协议、持久化、usage 与缺答，遗漏用户重点追问的两个真实、模型无关的上游图/预算隔离漏洞。这不是新的已观察分数污染结论，也不能据遗漏否定当前数值，但完整阶段解释应补足“到底修了什么”。

已有冻结三版本审阅 `portable_eval_20260908/review/REVIEW.zh.md:45–71`（SHA `30aaa8825a5b6d7d61c5e68b2f576b5b5ed29c23ca7e6036e541a64e2dc148b3`）记录：

- 旧共享图按节点最早时间过滤，却合并后续 performance/visitor/edge，较早视图可能看到未来事件。
- 旧 wrapper 先发布结果，loop 随后在 cost≥budget 时扣留反馈，forced-final 的 graph 注入又可能把该反馈显示出来。

本次直接核冻结 v5 实现，而非只相信旧审阅的“已修”摘要：

- `parallel_cache.py:879–885,1086–1104` 保存不可变完成事件，按 `completion_time≤viewer_time` 且 `completion_time<budget` 重放视图；不把未来聚合节点/边直接泄漏进早期视图。
- `parallel_cache.py:1788–1794` 仅在严格小于预算时发布新 cache/graph 结果；`1951–1959` 给 graph 注入同时传观察者时钟和严格预算上界。
- `poolact.py:68–109` 将同一 budget 传入 wrapper/augmenter；`run_poolact.py:472–488,520–537` 接入正式策略与 loop；`react_loop.py:438–470` 保留达到/超过预算时的扣留政策。
- `tests/test_poolact_visibility.py:13–58,109–151,153–185` 有对应未来节点/边、预算边界、forced-final 和观察者预算反例。这里只读测试源码，未再次运行测试、loop、scorer 或模型。

建议新附件增加上述两项及边界：旧缓存的未来完成时间门控本来已正确（旧审阅第 148 行），不能称整个 cache 都有漏洞；图修复恢复的是可见性隔离，可能减少 PoolAct 旧有的不当信息优势，**不保证提高 PoolAct 分数**。没有量化旧真实轨迹泄漏发生率、利用次数或各补丁的反事实贡献。K3 特定 template/transport 适配应与通用漏洞区分。当前 Search/Audit scorer 与 vote 的历史接受边界有意保留，不得把本次描述写成“所有解析已统一修好”。

## 核对通过的主要内容

| 内容 | 实际核查及边界 |
| --- | --- |
| 主效应和单位 | 两模型共 12 主表行逐字段对原 effects/抽取一致；Exp=Free−Tight、Pool=candidate−naive；Search/Audit 为 0–1 差值，不混相对百分比；Gap 为原 points。 |
| 全部反例与不确定项 | 31 负性能项、50 性能 unknown 与原 CSV 集合一致；K3 Gap-BoN −0.115490、GLM Audit label 反向均保留；重复 Gap/raw/all/family 切片没有被当独立胜率。 |
| R 与 SD | 独立重算 578 个完整 R3 sample SD，218 个完整性能方向；共 1028 比较的 CI/p 均 null。除 F1 单句外，报告没有把三个 orders、N4 或题目×重复当 iid 扩样。 |
| 全计划分母 | 从原 execution/plan 和新引用的六份精确 CSV 重数：每模型 705 invocation、783 logical、1881 slots；K3 697/8、775 terminal、26 未观测 slots；GLM 705/0、783 terminal。 |
| K3 未完成 | 原八项确实全在第三 NAS 外层；E-H 27 个配对只有 26 完整，主 baseline/effect/SD 保持 unknown，不使用 available-case 补齐。 |
| GLM 缺答 | 59 个缺答分布于 46 logical：Search 54=Exp10+Pool44，Audit5=Exp2+Pool3，HPO0。未删或伪装 infra；近端 length/空正文解释准确引用另一个独立逐59条审阅，本次不重新读其 raw。 |
| 大表与 null | 两模型各 7687 metric cells、5393 pair rows；GLM366 null cells 全是 Pool feedback_visible，28 unknown effects 同属该指标；不因执行完成补零。 |
| 相同 Search 主效应 | 39 对数值中 11 不同、28 相同，6 正/5 负。CSV 顺序累加尾差 −2.22e−16，引用的原 question 数字顺序为 +2.22e−16；原报告明确指定后者并否认任意顺序 bitwise 为零，故不是报告错误。跨模型原件是否误绑定的更强事实沿用已固定专项证据，不以相同均值推断相同输出。 |
| 原终点语义 | 报告披露 legacy fallback/离线 final、Gap>100 和 persisted backend 真值边界，未把 scorer 忠实复算等同于后端全库或字面最终配置已证明正确。 |
| 设置与论文 | 固定 plan/profile/deployment 支持 8×8、四双节点副本、K3 TP16/EP16、GLM TP16/EP1、R1/R3、73/39题、请求温度/top_p/max reasoning 与 Pool/Exp context cap 不对称；本地论文正文支持主表/四-agent 温度、题数与独立 Think 消融区别。Custom study 限制正确。 |
| usage 与费用 | 报告正确引用两路独立 usage；K3 known sums 不冒充 complete totals，GLM complete totals 与783完整子集同值；reasoning 不再相加。两顶层 allocation 的 GPUh 算术正确，明确不是 formal-only、有效计算或收费，未把更多 tokens 当协调因果证据。 |
| prompt 与因果 | 指定 payload 字段有限审计、未重渲染 server template、未排除任务推认/训练污染；没有把 format 共现、更多 tokens 或方向为正当成机制、稳定性或任意模型普适证明。 |

## 可选的新事实补充，不是原稿错误

ROOT 后补的 `ROOT_PROMPT_OUTPUTS_VERIFIED.json`（SHA `ac2589dcb33060aa9c87272095981e13e0f459803d2212f24030d77fd7c9c7e1`）可在新附件说明：GLM 已审字段 HPOBench 字面标记为 0，126 次命中均为 model-generated history。ROOT 此次核的是已产审计统计/provenance/字节，并未重新逐一阅读原 request payload。不得升级为 fresh 全请求独立来源审阅，也不得宣称所有 model-visible reasoning 已审。原报告第 90–92 行保守保留 18403/126 和未完成独立来源审阅，本身不错误。

## 本次范围与交付

77 个精确引用见 INPUT_REFS.json，含六份报告文件、50 个声明依赖及必要 source/plan/profile/结果元数据；没有递归跟随原 raw 引用。CHECKS.json 保存独立重数和子审算术结果，EXECUTION.json 分列真实工具 exit。原件、报告、评分器和正式运行全部未改；未读取密钥或模型 raw，未调用 scorer、backend、模型、API、Slurm 或 Git。

本次完成的是成稿后独立逻辑审阅，发现的两项仍须新修订附件处理并另行冻结。它不补齐 K3 八项，也不代替未来恢复数据的再导出/复核，不签署整个项目已完成。
