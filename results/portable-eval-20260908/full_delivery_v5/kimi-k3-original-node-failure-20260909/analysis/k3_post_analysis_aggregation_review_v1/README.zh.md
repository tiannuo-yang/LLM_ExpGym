# K3 冻结结果：独立汇总与配对审阅

本 reviewer 不是 exporter_candidate_v1 或 analysis_candidate_v2 的作者；任务授权前未读本次 K3 实际质量。只核当前 K3 node-failure export，未读 GLM、模型答案文本、HTTP raw、Search/Audit gold 或私钥，未调用模型/API、scorer、候选函数、原 CLI 或 Slurm。

结论：ROOT 批准的 review_v2.py 单次全量执行 exit 0，汇总与配对层 passed=true，0 个超出预先固定 rel/abs 1e-9 容差的差异。最大绝对浮点差为 7.275957614183426e-12。报告仅说明本层对账，不说明评分真值、投票算法、费用原始抽取、实验完整或确认性推断通过。

## 冻结与执行记录

- 原 export index：5934f9f6c4ccf8f9377ebfd51f874dc51936a22ee54f1992177eaf344ab68d33。
- results.json：1f5d641f1b4fb25a10d84698b2c3e0301aec6d073b4338544c8c5ff92a16885d。
- provenance.json：f4cd3d711c49c55bcf1b2ea8388527b52d1d4e62d1dbb03252e24e4fab6c18ec。
- v2 独立脚本：4cbcb3a63a98f7e100aaf9276d5f60733ee45e89e53a73ed3a69e13c0dc3e31c。
- actual_v2/REVIEW.json：88f7ea922c11c9f2346e8abeca5f94c2558d848fc5368bd00a7a69c512b249bb。
- actual_v2/EXECUTION_RECEIPT.json：8ebda44a4d525763b1f9f84e781fe3e8456e5ea0a5dce72adc863f9ea3c16c90。

12 个生成的审阅数据文件已逐一回读核字节数和 SHA；328 个实际读取输入在审阅后再次核 SHA，均未变。计划、execution、seal 和 source catalogue 均绑定 ROOT 提供的 SHA。实际原 export、计划与源码均未改。

## 全覆盖结果

| 层 | 独立核对规模 |
|---|---:|
| 原计划 invocation / logical / agent | 705 / 783 / 1881 |
| logical 正常 terminal / infrastructure_error | 775 / 8 |
| 展示单元 / 指标格 | 705 / 7687 |
| Exp Audit 文档预算单元 / 三 order 指标核对 | 39 / 416 |
| 固定 comparison / primary / secondary | 514 / 6 / 508 |
| ExpGym / PoolAct comparison | 158 / 356 |
| R1 / R3 comparison | 124 / 390 |
| paired cells | 5393 |
| 数值 / 结构断言 | 62880 / 150670 |

514 个 effect：正 116、负 166、零 42、unknown 190。5393 个 pair：正 1712、负 2003、零 1152、unknown 526。7687 个指标格中有 459 个 null。8 个基础设施错误对应 26 个未观测 agent 终态槽位，均未冒充模型缺答；本份报告的模型缺答计数为 0。

CSV/JSON 全行全字段镜像核对：metrics 7687、effects 514、paired_rows 5393、logical_outcomes 783、known_subsets 127；CSV 空数值与 JSON null 对应，不填零。

## 主比较的独立重算

| ID | baseline | target | effect | outer SD |
|---|---:|---:|---:|---:|
| E-S | 0.6588618353324236 | 0.17013574660633485 | 0.48872608872608875 | null |
| E-A | 0.894419306184012 | 0.5158371040723982 | 0.37858220211161386 | null |
| E-H | null | 89.68371695757193 | null | null |
| P-S | 0.21287078934137757 | 0.304323780794369 | 0.09145299145299145 | null |
| P-A | 0.7375565610859728 | 0.9366515837104072 | 0.1990950226244344 | null |
| P-H | 93.4276982130541 | 95.50455706751116 | 2.0768588544570528 | 3.410222118292855 |

E 的正值表示 utility-oriented Free−Tight 退化；P 的正值表示同预算 candidate−naive 改善。分数单位为 fraction，H 的单位为 Gap points。P-H 仅 NAS101 A / Tight / Gap-MI，不能扩张为全九任务优势。全部 CI/p 为 null。

E-H 三个 outer bundle 为 [3.8388051121411433, 13.02838114996262, null]；第三次 NAS101 C Free 缺失，完整 effect 和 SD 保持 null。P-H 的三个 bundle 为 [0.11865431365261259, 0.09729738452421088, 6.014624865194335]，样本 SD 的分母为 3−1。各 outer 内先固定 item 等权，再对完整 outer 等权；未把 item×outer、N4 agents 或 Audit 固定 orders 当独立重复。

## 审阅独立性和可复查证据

重算代码只用 stdlib；均值采用 Fraction 累加，SD 独立按有理数中心化平方和计算，没有调用候选的 mean/describe/project/gap/catalogue。514 目录从冻结 plan 的 item 元数据与固定 metric 规则重建，不以实际数值决定纳入项。

reported answer_perf/answer_metrics 与状态是本层输入；逐 agent Gap、MI/BoN、Audit 三 order 均值、记录中 telemetry 均值到全部展示指标均另算。312 个 Pool Search/Audit MV 从 SHA 绑定的原 result.aggregate 仅取数值，未重新投票或重新评分。原评分与投票真值另由独立 reviewer 核验；费用只核现有 records 到输出的算术，原 extraction、历史费用和 GPU 分配账单不在本层。

本份实际 Audit 的 117 条 order 全在，没有真实缺一 order 的案例。17 个独立手算例含缺一 order→null，并在 416 个实际指标向量上另列一次缺值后的独立期望；这是审阅器的 strict-null 对照，不冒充对生产转换器运行了 416 次缺值注入测试。真实缺失传播由当前 8 个 infrastructure_error→指标→pair→bundle 的完整对账覆盖。由于实际模型缺答为 0，不能从本数据声称实测覆盖了非零缺答分支。

可复查文件：actual_v2/audit_order_checks.json、cell_checks.json、pair_checks.json、effect_checks.json、recomputed_effects.json、known_subset_checks.json、pool_mv_source_projections.json、numeric_checks.json、structural_checks.json、inputs.json、synthetic_cases.json，以及执行收据。每项数值对照保存 reported/recomputed/delta/passed，null 和所有负值原样保留。

## 首次审阅器失败及限定修订

原 review.py 的 SHA ddce1adfdfd86a805685f5495996ced48dcd8c2bb8e2d19eda2991a8988bb056 保持不变。首次执行 exit 1，因为审阅器给计划中不存在的 PoolAct whatis 空题集虚构了 44 个比较，误得 558，随后在 secondary_0f4a4823d10a191d50fa 上 KeyError。没有生成伪通过收据，也没有修改原结果。

ROOT 随后明确授权另建 v2：只补空 subset 不登记、缺目录的明确诊断、一个空 slice 合成回归和独占 actual_v2 输出路径。原 16 个用例调用 AST 完全保留；新 17 例通过。558→514 是修复审阅器，不是删除实验。FIRST_ATTEMPT.json 和 REVISION_CHECK.json 保存经过与证据。

当前结果仍是缺 8 个单元的 K3 阶段审阅。它不能代替未来恢复、两模型最终输出冻结后的 fresh review，也不产生 confirmatory claim。
