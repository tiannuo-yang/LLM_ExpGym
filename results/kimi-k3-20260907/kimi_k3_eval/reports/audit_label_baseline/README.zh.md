# Audit 标签分布与固定空证据基线

> 这是离线常量参考，不是 Kimi-K3 测量，不替代正式 ExpGym/PoolAct 矩阵。没有 LLM 或 human_feedback 调用，未修改源码、模型结果或原始数据。

固定规则：对每个文档的全部 17 个 hypothesis，始终提交 label="NotMentioned"、evidence_ids=[]。标签拼写严格使用仓库定义，类别不根据 gold 选择；直接调用当前 build_answer_evaluator(row_index, "cc-large")，tool_records=[]。

13 个文档 × 17 个假设共 221 项：Entailment=101（45.701357%）、NotMentioned=101（45.701357%）、Contradiction=19（8.597285%）。NotMentioned 与 Entailment 并列，不能称前者是压倒性的唯一多数类。

常量基线 LA=EA=101/221=45.7013574661%。每文档同为 17 项，因此文档等权均值和 221 项 micro 均值相同。无反馈调用，verification_eff 均为 0；这里分母非空，不是缺失值。基线不依赖 cost regime 或 hypothesis 顺序，只列一次，不扩充成模型运行次数。

| row_index | doc_id | Entailment | Contradiction | NotMentioned | 固定基线 LA=EA（%） |
|---|---|---|---|---|---|
| 0 | 1 | 11 | 2 | 4 | 23.529412 |
| 1 | 2 | 11 | 3 | 3 | 17.647059 |
| 2 | 4 | 4 | 2 | 11 | 64.705882 |
| 3 | 5 | 4 | 1 | 12 | 70.588235 |
| 4 | 6 | 10 | 1 | 6 | 35.294118 |
| 5 | 8 | 3 | 1 | 13 | 76.470588 |
| 6 | 11 | 8 | 2 | 7 | 41.176471 |
| 7 | 18 | 3 | 2 | 12 | 70.588235 |
| 8 | 21 | 11 | 1 | 5 | 29.411765 |
| 9 | 22 | 11 | 1 | 5 | 29.411765 |
| 10 | 23 | 9 | 2 | 6 | 35.294118 |
| 11 | 24 | 9 | 1 | 7 | 41.176471 |
| 12 | 25 | 7 | 0 | 10 | 58.823529 |

文档身份与每条 gold label、spans、JSON pointer 均在 [baseline.json](baseline.json) 的 documents 中；同文件 per_hypothesis 另列 17 个假设各自跨 13 文档的标签分布。

## EA 为什么不联合 label

当前 evaluator 分别累加 label_ok 与 evidence_ok。LA 检查 label 精确相等；EA 仅检查预测证据集合与 gold spans 集合精确相等，并不乘以 label 是否正确。只有 verification_eff 的分母才要求 label 与 evidence 同时正确。参见 [评分实现](../../../LLM_ExpGym/expgym/task_evidence_audit.py)。

选中的 221 项中，恰好只有 NotMentioned 的 101 项拥有空 gold spans，其他 120 项证据均非空。因此全空证据的 EA 也是 101/221，与本次固定标签基线 LA 数值相同；这不是 EA 定义成联合正确率。保持所有条目的 evidence_ids=[]、仅改变其 label 时，EA 仍不变。

这项参考说明空证据本身可得到 45.70% EA，也提醒 Contradiction 样本较少；但它本身不能解释约 94% 的模型 LA。正式结果的优势、分项错误及显著性仍须使用同一 13 文档的真实结果单独分析，不能从 smoke/pilot 小样本直接推断全量表现。

## 指纹与复现

- 数据：[test_segments.json](../../../LLM_ExpGym/data/contract-nli/test_segments.json)，SHA256：a81e3ecfc1d423f11289a1711ccd4d5cf3167f4d75576f5180bcc0b4c928fd23。
- 当前 source_tree_sha256：c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e。
- evaluator SHA256：c034571d6a09ffedd522426550c2aab37b97616342b5ce3646cc81ec8ebfe5fb。
- 选择依据：[dataset_manifest.json](../../data_runtime/dataset_manifest.json) 的 audit.items 与 [论文对齐说明](../../protocol/PAPER_ALIGNMENT.md) 中 cc-large rows 0:13；逐文档 doc_id/17 项及数据 SHA 已断言核对。
- [compute.py](compute.py) 可重复离线计算；[baseline.json](baseline.json) 保存数据、源码、脚本、选择依据的完整绝对路径与 SHA256。smoke_v3 manifest 仅用于核对当前源码指纹，未读取其中任何模型分数。

    LLM_ExpGym/.venv/bin/python kimi_k3_eval/reports/audit_label_baseline/compute.py
