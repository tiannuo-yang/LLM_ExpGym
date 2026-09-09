# 冻结 K3 v5：独立评分与投票复核结果

**现行规则的逐项核验通过：13,402 项对账，0 个超出预定容差的反例。** 一次实际执行 exit 0；并非只复查几个正向结果。此结论限已封存 K3，尚非双模型最终验收，也不是断言所有研究假设成立。

独立代码未 import 原 scorer、Pool 投票函数、Gap/汇总器；Search 按预测集合与固定 gold 直接算 F1，Audit 按固定 gold 分母独立计算 LA/EA，投票另按输入 agent 顺序独立计票与选代表。HPO 仅核原 reported performance 与固定 oracle 常量的算术，不冒称独立后端性能验证。

## 实际覆盖与失败分母

|任务|Exp 完整个体/计划|Pool 完整个体/计划|完整 N4 池/计划|
|---|---:|---:|---:|
|Search|219/219|936/936|234/234|
|Audit|117/117|312/312|78/78|
|HPO/NAS|79/81|192/216|48/54|

总计 783 planned logical、1,881 planned agents；实际核验 775 完整 logical、1,855 个完整个体和 360/366 个完整 N4。剩余 8 个 invocation 全为 HPO 基础设施失败：Exp 2、Pool 6，对应 26 个 planned agents，继续保留 unknown/error，未换成缺答或零分。本次完整个体中没有 None 缺答，因此缺答路径的实际发生证明不来自这份 K3 cohort；其公式分支有合成检查。

全部 1,455 性能 metric cells 均对照 `results.rows` 与 derived body；Exp Audit 39 个 doc×budget 组各自严格合并 3 个固定 order，缺分则完整端点 null，没有将 orders/N4 当独立样本。每个完整 HPO 单元的 known subset n、mean/max perf、mean/max clipped Gap 都核对；没有用可用子集填满完整 N4。

46 项比较有非零浮点差，最大绝对差 `1.1102230246251565e-16`、最大相对差 `1.9428902930940237e-16`（相对差定义为绝对差除以两侧绝对值的最大值），均远小于事前固定 rel=abs=`1e-9`。每项原值、独立值、delta、pointer 均保存在 `actual_v1/checks.json`，没有只保存一个总 PASS。这些浮点等价差异不包括下述三个实际超过 100 的 Gap；后者是当前公式的真实取值。

## 实际出现、但不是算术复现错误的解释边界

1. **Search 的 scorer-set / vote-key 差异确实发生。** 234 个完整 Search 池中 6 个存在同 scorer 集合拆成不同 vote key 的 agent 对，共 13 对；0 个出现同 vote key 对应不同 scorer 集合。6 个池分布为 naive 2、cached 3、poolact 1。它们的原 winner 与原 F1 均符合冻结规则。发生拆票不能直接证明换一个政策会改变赢家/分数；本次没有执行替代政策重评分。
2. **Gap 超过 100 不是浮点尾差。** 三个值为 `100.17721427983435`、`100.10632786483673`、`100.2922407081013`。前两条属于 NAS101 C（cached/Moderate/R0 agent3；naive/Moderate/R1 agent2），后一条属于 ParamNet adult steps（Exp/Free/R2）。reported perf 确实略高于固定 oracle 的 best_perf，且该文件 best_perf 与 max_perf 一致。下限 clip、不设上限的现行公式计算正确，应保留；固定 oracle best 不能因此声称是已证明的全局最优。未查后端/配置空间/随机性的更深原因。
3. **HPO 端点不是全部字面模型提交。** 271 个完整 HPO 个体的持久化 provenance 中有 61 个 `best_evaluated_fallback`，另有 6 个 `offline_final_answer`；其余 204 个为 `matching_tool_call`。这不是本次新增数据改写，但方法解释必须披露。此审未逐条回溯模型原始 HTTP 最后一条字面答案及上游选择逻辑。

Search 拆票的 logical IDs（完整定位见 `actual_v1/pools.json`）：

- `87905dd83425b383260f29de2fb83a90ea1da3f6208068cb215d3a7d1295fec5`：seed2/q13，cached/Moderate。
- `08b034a6fd5ec5d3f4c787e1ae80c7e13493d60bcf72554255c6d49ea7715640`：seed2/q13，cached/Tight。
- `fe351dc013257918ec84003d996c6c791280e106d343e5d1ec14e5531d2f593f`：seed2/q13，poolact/Tight。
- `558b37fdb2ec1f97bde2d1fcdf49756abbb2a87a9cc0a242eb8cd2c033d05628`：seed2/q15，naive/Tight。
- `0bd9f2470bf4cbfe236b906819f39b8381de49c8cdafddfa843bf1515883486f`：seed2/q15，cached/Tight。
- `e55aa6288a77df6b85938af0192846cbb44888172586aa36ceac473ed9c4376a`：seed2/q17，naive/Moderate。

## 证据与边界

先执行 12 个人工期望合成用例并通过；ROOT 全文有限代码审查后，只更正一处 reviewer 角色说明，固定新代码 SHA，再执行一次实际比较。未自动重试、未改任何原 source/result/export。2,359 个明确输入逐项前后 SHA 相同；输出 8 个文件的字节/SHA/精确文件集另核通过。

`actual_v1/INDEX.json` SHA：`8047a5b32217910e159bbfd6fc51fa56771b38a8f388520ea22bcc73cb6b9d30`。

实际过程与工具 exit/chunk 见 `EXECUTION.json`。主效应/配对的独立审阅者是 `/root/runner_integration/formal_scope_readonly/display_m1_readonly/main_analyzer_readonly`；早期 paper_matrix 的角色说明已被撤回，执行后的 SUMMARY 与最终 README 均已纠正。费用、reasoning、GPU 账单另审，本文件不冒领通过。

gold 仅来自固定两份 QA 容器与 ContractNLI 的已选 13 个文档；没有读 corpus 或全 HPO 数据库。没有输出 gold/answer 正文，没有调用模型、API、后端、原 scorer 或原 CLI。实际规则一致不能证明 parser 理想、策略因果收益、训练集不泄漏、预算公平、oracle 全局最优或两模型普遍结论。
