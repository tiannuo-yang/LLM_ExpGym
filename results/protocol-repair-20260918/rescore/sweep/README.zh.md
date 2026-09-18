# Whois budget sweep：终答协议修复后的全量重评分

范围为六模型 × 五个 β（1、5、10、15、20）× 39 道 Whois 问题，共 1,170 个已采用单智能体结果。本交付从每份原始轨迹重新选取记录的终答并评分；没有只修改先前发现的个案，没有调用模型或搜索工具。

其中 β=10 的 234 个位置与主实验 N=1 Moderate 完全重叠。`main_overlap_slot_id` 给出主实验身份；合并样本数时只把其余 936 个位置作为新增独立结果。Gemini β=10 沿用历史 Sub2API 结果，其余四个 β 使用已完成的 OpenRouter 结果，本次没有改变提供方或重新采样。

正式全量复算结果：**2 个终答提取文本发生变化，0 个 F1 分数变化**。30 个模型/预算均值、30 个名次和 24 个预算差值均保持不变；不存在由此次评分修复导致的 sweep 结论反转。两个变化分别为 Kimi β=10、`phantom_seed3:7`（从整个原始响应恢复显式 `Answer` 后缀，F1 仍为 0）和 GLM β=20、`phantom_seed2:1`（移除泄漏进答案的标签闭合 `**`，F1 仍为 1）。

另外，GLM β=20、`phantom_seed2:5` 有一次非最终响应在新规则下可提前作为终答。历史运行随后只多进行了一次模型重答，没有新增工具调用，重答名单与提前可接受的名单一致，F1 均为 1。本交付保留真实发生的调用和成本，没有把这次历史重答从行为统计中删除。

## 分数版本和终答选择

`old_score` 保留原采用分数，先用原 Search name-level F1 scorer 全量回算核对，再用修复后的统一终答提取器计算 `new_score`。新分数版本为 `formal_protocol_repair_v1`，不是前轮抽查的诊断分数；旧原件和既有报告均没有被覆写。

终答只取 `outcome.answer_message_id` 对应的最后一条 assistant 消息，使用 `llm_calls.output_message_id` 核对输出及 `finish_reason`。长度截断或仍有工具调用的响应不作为有效终答。原来没有终答的样本，仅当该响应有 `forced=true` 的明确终答证据时重新解析；没有向前搜寻替代答案或补写答案内容。Search 的 gold、规范化和 F1 公式保持不变。

另扫描非最终的、无工具调用且未截断的 assistant 响应，判断修复后的解析器是否会提前接受终答。这种运行路径差异单独记录在 `runtime_counterfactual.csv`；它们不会代替实际轨迹中记录的终答，也不会伪造重新运行的行为或成本。

## 产物

- `SOURCE_SELECTION.csv`：全部 1,170 个来源、原件 SHA256、运行代码版本、QA 文件身份及主实验重叠身份。
- `agent_rows.csv`、`slot_metrics.csv`：全部新旧分数、答案哈希、终答选择信息、变化原因及版本标记。
- `affected_samples.csv`：答案提取或分数发生变化的全部样本。答案文字变化不必然改变 F1。
- `aggregate_metrics.csv`：30 个模型/β 设置的新旧均值；每个均值的分母仍为 39。
- `budget_differences.csv`：24 个相对 β=20 的配对均值差及其变化。
- `rankings.csv`：30 个新旧名次，使用并列竞争排名，数值相差不超过 1e-12 视作并列。
- `scoring_inputs.jsonl.gz`：可公开的最小真实评分输入，包含原始终答文本、旧答案、gold 名单、来源哈希与终答资格信息。为核验提前终止差异，仅额外保留相关非工具、未截断的响应文本。没有完整轨迹、工具返回、HTTP 请求、认证信息或推理签名。
- `CHECKS.json`：全量原件/旧分数核验、数据和代码哈希；评分开始和结束的代码哈希必须一致。
- `PUBLIC_REPLAY_CHECK.json`：从 CSV 复算汇总、差值和排名的结果。
- `SCORE_REPLAY_CHECK.json`：从最小输入逐条调用正式解析器和 Search scorer 回算全部 1,170 个旧/新分数的结果。
- `BETA10_MAIN_JOIN.csv`、`BETA10_MAIN_JOIN_CHECK.json`：234 个 β=10 重叠样本与正式主实验逐条对照；原件 SHA、旧 F1、新 F1 以及主表采用 F1 均一致。`check_beta10_main.py` 可重新执行该核验。

## 复算

在仓库根目录执行，下方 `BUNDLE` 是本目录。此路径不需要私有原始轨迹、Parquet 文件、pyarrow 或网络访问：

```bash
python3 tools/rescore_whois_protocol.py --output BUNDLE --check-public
python3 tools/rescore_whois_protocol.py \
  --output BUNDLE --inputs BUNDLE/scoring_inputs.jsonl.gz
python3 BUNDLE/check_beta10_main.py \
  --sweep BUNDLE --main MAIN_SEARCH_AUDIT_BUNDLE
```

若持有完整本地留档，可重新从全部原始轨迹与校验后的 QA Parquet 生成一个新输出目录：

```bash
python3 tools/rescore_whois_protocol.py \
  --workspace /path/to/archive-workspace \
  --report results/gemini-openrouter-20260917 \
  --output /path/to/new-empty-output
```

这一路径需要 pyarrow。已有 CSV 目录不能被覆盖；任何原件哈希、旧分数或数据身份不符都会失败。公开回放同时检查所运行的解析器、评分器及脚本 SHA256 与本交付记录完全一致。
