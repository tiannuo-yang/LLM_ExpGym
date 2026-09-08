# full_v3 Audit 独立复算器

状态：工具已准备，当前尚未执行全量 Audit 数值复算；等待主运行所有 Audit 完成及最终 summary。此目录不代表正式矩阵已验收。

使用纯 Python 标准库，从冻结 gold 数据和原始最终答案独立计算；不 import／调用仓库 evaluator、PoolAct aggregator 或正式 summarizer，不调用模型／human_feedback，不改源码、数据或结果文件。遵循 expgym-runner skill 的完整性与“语义零分不等于执行失败”规则。当前研究为新增 Kimi-K3 的 Current repository full matrix 自定义模型复跑，不称为原论文模型的 paper-exact 复现。

## 准备条件与输出

严格要求 78 个 Audit 子进程完成、13 documents × 3 regimes：ExpGym 每文档 3 hypothesis orders，共 117 traces；PoolAct 每文档 naive/cached/poolact，各 N=4，共 117 results／468 agents。检查所有路径、回执和项目 manifest 槽位。未齐全时输出 `complete=false`、`metrics=null`、具体缺失／pending 列表并以 2 退出；不会用 0 代替缺失。

只检查就绪状态，不读取原始最终答案评分：

```bash
python3 kimi_k3_eval/reports/full_v3_audit_independent_review/compute.py --ready-only
```

完整后实际复算（默认 JSON 写到 stdout；可用 --output 排他创建新的生成证据文件，已有路径直接拒绝）：

```bash
python3 kimi_k3_eval/reports/full_v3_audit_independent_review/compute.py
python3 kimi_k3_eval/reports/full_v3_audit_independent_review/compute.py --summary /absolute/path/to/full_v3/summary.json
python3 kimi_k3_eval/reports/full_v3_audit_independent_review/compute.py --output kimi_k3_eval/reports/full_v3_audit_independent_review/independent.json
```

输出保留 gold 路径、SHA256、各 doc 的 JSON pointer／17 个 gold hypotheses、原始 artifact 路径／SHA、最终 answer 定位与哈希、逐 hypothesis 正误、实际投票序列／平票、每文档和宏平均。所有记录重新检查已保存 LA／EA／verification_eff，PoolAct 从 4 个 agent final 重新投票并逐字核对 aggregate answer；不会从原始 aggregate 分数字段取数计算指标。

`--summary` 在上述原始复算完成后才读取正式汇总，比较：42 个全量宏指标、546 个 doc 指标、585 个 agent/Exp trace 的 LA／EA／SHA、117 个 PoolAct aggregate 记录，以及 24 个 moderate/tight 论文子集指标。585 = 117 ExpGym + 468 PoolAct agents；各 PoolAct aggregate 不是额外 agent。

## 计分与聚合

LA 为标签字符串的准确率，单 agent 不替换同义词或大小写。EA 为 evidence ID 集合完全相同的比例，独立于标签正确性；只有 verification_eff 的分母要求标签和证据同时正确。缺失整个 hypothesis 得 0，不等同于有空 dict 但省略 evidence_ids（后者默认空集合）。这些是冻结实现语义，不在本工具中“改正”。

ExpGym 先平均每 doc 的 3 orders，再等权平均 13 docs。PoolAct 先对每 hypothesis 的标签做相对多数投票，再仅在获胜标签的 agents 中投完整证据集合；两级平票均按原始 agent 顺序首次出现者胜出，不使用 gold 打破平票。每个 doc 的投票 LA／EA 等权宏平均；同时单独汇总 MI_LA／MI_EA 作为描述性指标，不把它们替换论文投票指标。因为每 doc 恰有 17 hypotheses、每组恰有相同 repeats/agents，本矩阵等权宏平均与相应微平均数值相同，但代码仍明确按 doc／rep 层次聚合。

详细的 JSON 清理、别名、证据转换和工具记录规则见 [SEMANTICS.zh.md](SEMANTICS.zh.md)。其中单 agent evaluator 与 PoolAct 投票解析不完全一致；复算器按原规则分别实现。内层 JSON 的 NaN/Inf 不被擅自改成不同评分语义，只在诊断字段以显式 `$python_json_nonfinite` 标记编码，确保报告 JSON 合法；精确原文仍由原始文件路径／哈希定位。

## 验证与边界

[test_compute.py](test_compute.py) 的 25 个纯内存测试已通过，覆盖独立 EA、缺失与空条目、内层重复键、fence／分号、非有限值、工具 wrapper、首个行首 Answer、两级平票、整组证据投票、缺失不填 0 和 doc／rep 等权。没有读取模型全分区来生成测试预期，也没有任何新增 API 调用。

[test_summary_comparison.py](test_summary_comparison.py) 的 24 项纯内存检查也已通过：五类正确比较计数，并验证单值、SHA、manifest、完成标志、重复／缺失、指标身份和非有限值篡改均被拒绝。合计 49 tests 通过；这些测试不是实际 full_v3 summary 交叉核对。

脚本显式绑定 full_v3 source SHA256 `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`。其他源码版本的 manifest 会被拒绝，必须先重新审核计分／投票语义。

此工具专门独立验证 Audit 数值和原始记录一致性，不代替最终 schema／source/config 全审计、raw HTTP dump 对账、成本统计或 Slurm 回执。对缺失、异常或数值不一致一律保留 incomplete，不凭常量 baseline 补数。
