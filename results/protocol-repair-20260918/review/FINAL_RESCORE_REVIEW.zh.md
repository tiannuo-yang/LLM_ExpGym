# 最终离线重评分独立核验

核验通过，针对冻结代码 `0e6c51b6d86f42437038518c2fc8adc510901c0b`。本轮只读正式重评分产物，没有修改生产 parser、轨迹或 CSV，没有调用模型。

- [AUDIT_WRAPPER_REJECTION_REVIEW.json](AUDIT_WRAPPER_REJECTION_REVIEW.json)：2,574 个 Audit 成员和 468 个聚合答案，旧 scorer 接受而新 wrapper 拒绝的条目为 **0**；成员 LA/EA 下降为 **0**。parser SHA 与正式 rescore CHECKS 一致。
- [FINAL_RESCORE_VERSION_COUNTS.json](FINAL_RESCORE_VERSION_COUNTS.json)：逐行核对 4,698 个旧/新主实验 slot 和 diff，全部一致。旧/新 score-complete 均为 4,687；11 个既有缺评分 slot 未被伪造补齐。
- 从正式压缩输入包重新提取全部 **2,574** 个 Audit 成员终答，结果与保存的正式输入全部一致；独立重算旧/新 LA、EA，也全部一致。参考标注只用于终答已确定后的指标校验，不用于选择、清洗或修改预测。
- 用独立投票实现重算全部 **468** 个 Audit 旧池与新池，全部与正式聚合答案一致。

Audit 成员共有 41 份 LA/EA 变化：15 份去掉标签的关闭 Markdown 标记，23 份从整段响应中提取唯一正式标签，3 份修复其他终答边界。所有变化都由正式通用规则产生，并非仅对历史发现的 23 例进行定向修改。

字段核查覆盖旧答案内 41,693 条和新评分输入内 42,390 条 hypothesis entry。合法 17 个 hypothesis ID 上，标签 alias 或 evidence key 的新旧解释差异均为 **0**。只有同一个 GPT Tight naive 成员在非法 key `nda- looks17` 中输出的乱码标签会被旧投票错误归一成 `Entailment`；新投票保留原标签。它使一个聚合答案的非法 key 内容变化，但不影响合法假设或 LA/EA。证据字段解释没有命中差异。这里不把缺失 label 从 `None` 显示为无效键 `""` 算作“被修正成正确标签”。

变化数采用不同分母和端点，必须区别书写：

| 计数 | 正式核验结果 | 定义 |
|---|---:|---|
| 主实验任何成绩列变化的 slot | 57 | 包含 MI 和 MV、LA 和 EA |
| 主实验任务输出端点变化的 slot | 41 | Audit 的 LA 或 EA；Search 的 F1；HPO 的主指标 |
| 论文主端点变化的 slot | 39 | Audit 仅以 EA 为主；另 2 个池只有 LA-MV 变化 |
| Audit 池 LA-MV 或 EA-MV 变化 | 23 | 其中 EA-MV 变化 21 池 |
| Audit 成员 LA/EA 变化 | 41 | N1 与 N4 成员合计，与 slot 计数不同 |
| HPO 离线重评分变化 | 0 / 810 slots | 不代表运行图修复无影响 |
| Whois sweep 分数变化 | 0 / 1,170 slots | 存在 2 份终答文本变化，F1 不变 |

完整生产解析/评分文件与固定 core commit 字节相符；各 rescore 脚本与 CHECKS 的 SHA 相符。新增重评分脚本尚不属于 core 修复提交，须随最终交付提交一起发布，不能宣称这些新增脚本已包含在 `0e6c51b` 中。

复算命令（workspace 根目录）：

```bash
python3 protocol_repair_20260918/review/audit_wrapper_rejections.py \
  --repo LLM_ExpGym-protocol-repair-20260918 \
  --rescore protocol_repair_20260918/analysis/rescore/search_audit \
  --output protocol_repair_20260918/review/AUDIT_WRAPPER_REJECTION_REVIEW.json

python3 protocol_repair_20260918/review/final_rescore_independent.py \
  --repo LLM_ExpGym-protocol-repair-20260918 \
  --rescore protocol_repair_20260918/analysis/rescore \
  --output protocol_repair_20260918/review/FINAL_RESCORE_VERSION_COUNTS.json
```

本检查证明已有轨迹的重评分、来源版本及聚合一致，不代替图信息共享或提前终止决策改变所需的新运行对照。
