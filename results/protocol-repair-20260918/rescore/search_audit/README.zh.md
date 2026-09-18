# Search / Audit 全量终答重评分

本目录是 `existing_trace_rescored`：对保存的终端输出使用新协议重提取、重新评分、重新投票；未改变任何运行时工具动作，也不声称重建修复后的行动轨迹。正式采用层及 HPO 新对照来源由发布清单单独指定。

- 源基线：`297c3d00a006f33fc5a8ca799ce91d327d92839e`，补全 Gemini 后的主实验。
- 正式实现：`0e6c51b6d86f42437038518c2fc8adc510901c0b` 的版本化终答/投票规则；最终发布提交还包含本目录及离线工具。
- `CHECKS.json` 锁定每个实际调用实现的 SHA；运行开始/结束代码 SHA 必须相同。

## 覆盖与结果

全读并校验 3,888 个采用结果：N1 Search 1,314、Audit 702；N4 Search 1,404、Audit 468。全部 9,504 个成员重新提取/评分，全部 1,872 个池重新投票。重新运行历史评分器后逐成员/逐池旧分均与保存结果一致。

答案文本变化与成绩变化分别统计：77 个成员答案文本变化，其中 67 个任务解析内容变化、10 个仅格式变化；45 个成员分数变化。56 个池的投票输出字符串变化，其中 50 个解析内容变化、6 个仅序列化变化。57 个结果至少一个 MI/MV 指标变化；其中 41 个单体或池端点成绩变化：Audit N1 16、Audit N4 23、Search N1 1、Search N4 1。完整表也保留所有未变化的样本。

旧诊断中的 23 个答案/19 个池是此前特定故障规则的范围，并非本次全量评分筛选条件。这里全部终答均执行同一正式协议。Kimi 一份 Search 同时给出两个非空 Answer 指令，正式通用规则拒绝；即使人能认为两次内容相同，也不使用任务答案或 gold 来选择其中一次，原因字段为 `two_nonempty_final_directives`。

## 可公开复算

`scoring_inputs.jsonl.gz` 是由原件派生的最小评分输入，包含终端原文、历史答案与分数、原件 SHA、任务身份、仅评分需要的冻结 gold 名称/标签/证据 ID，以及 Audit 历史工具提交记录；不包含完整合同、检索语料、完整轨迹、HTTP 请求头或推理签名。拒绝/截断输出只保留资格与摘要校验信息，不将其当成终答。

从仓库根目录运行（需 Git 历史中的基线提交；不需要私有原件或完整数据集）：

```bash
python tools/rescore_protocol.py --inputs PATH/scoring_inputs.jsonl.gz --output /tmp/search-audit-replay
```

脚本直接调用生产 `parse_final_answer`、任务评分器和 `aggregate_results`；同时从固定历史 Git 提交加载旧实现，重算并验证旧分。`LIGHTWEIGHT_REPLAY_CHECKS.json` 记录七张 CSV 的逐字节复算结果。表的再汇总与 parser/scorer 回放是不同检查，本目录提供后者。

若持有完整本地留档，可从原件重新构建输入包：

```bash
python tools/rescore_protocol.py --source results/gemini-openrouter-20260917/main --delivery PATH/paper-ad03e8c-20260916 --terminal-evidence PATH/n4_missing_terminals.json --output /tmp/search-audit-full
```

## 文件与口径

- `slot_scalars.csv`：与旧主表同 schema 的 3,888 个新标量；`SOURCE_SELECTION.csv` 锁定原件，不改历史源。
- `agent_rows.csv`：全部 9,504 个成员的旧/新指标、文本与解析内容变化、终答定位与原因。
- `sample_diff.csv`：全部结果旧/新指标；`affected_samples.csv` 可筛受影响结果。
- `pool_decomposition.csv`：按“只改终答提取 → 再改 payload 接受 → 再改投票规则”的固定顺序分解池变化；属于顺序敏感的诊断分解，最终分数以全部修复共同生效为准。
- `runtime_counterfactual.csv`：中间输出的文本解析差异筛选，不是重新运行结果；原 API 资格及后续动作核查在相邻终端证据目录，可能影响提前停答的情形需与离线终答评分分开解释。

`source_sha256` 是原文件字节 SHA-256。答案文本的 `*_sha256` 使用 `SHA256(canonical JSON(value))`，JSON 为 UTF-8、非 ASCII 转义关闭、键排序、无额外空白；这使空答案与 `null` 可区分。`answer_changed` 是原始终答字符串比较；`parsed_content_changed` 使用任务接受的名字集合/Audit 对象，排除空白/JSON 键顺序差异。

Audit 主 LA/EA 定义保持不变。`verification_eff` 保留历史“提交过的反馈尝试”语义；N1 同时导出 `visible_verification_eff` 以排除未收到结果的尝试，两者不混用。N4 旧导出没有逐工具可见标志，因此该辅助字段为空，不伪造已收到反馈。

全部 N4 旧空终答 236 个均查到实际 API 终端：185 stop（其中 46 非空）、51 length。46 个非空完整终答统一经过新 parser 后仍无有效终答，没有恢复分数；其余拒绝有原始证据，并非因为字段缺失而补零。N1 原终答由 `answer_message_id` 精确关联 `llm_calls.output_message_id`，只有资格完整的 final-only 输出可重提取。
