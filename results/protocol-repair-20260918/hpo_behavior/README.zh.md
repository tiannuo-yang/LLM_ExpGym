# HPO 单智能体行为：完整 486 条采用轨迹

本目录全量重新读取并校验采用清单中的 **486 条 HPO 单智能体原件**，包括新补齐的 6 条 Gemini。六个模型各 81 条，Free、Moderate、Tight 各 162 条。动作、工具反馈和停止事件来自实际已发生的轨迹；离线重评分不会被写成一次新的行动过程。

`observed_behavior486/` 使用既有采用分数，负责区分“样本补齐”与“评分规则修复”的影响。`official_rescored486/` 则逐条接入全量终答重新提取、重新评分的结果，评分版本为 `final-answer-boundary-v2/existing_trace_rescored`。**486 条均已重评分，最终答案和分数没有变化；所有行为汇总数值也保持一致。**这项结果不是仅检查过去发现的异常样本。

本目录的正式评分表示在已有单智能体轨迹上应用新规则；它不表示 HPO POOLACT 的图修复对照已运行。多智能体图修复的新运行属于另一项实验来源。

终答解析器已冻结为 SHA256 `6b09495845fa6c1dc324a82ba471bcfba59265aaa4912ff0acf8307239e84bed`；正式 HPO 逐成员评分输入 SHA256 为 `62226233999868aad4f90f0502cbb96dd6f189649a8d5bd52eac41799c9d2b3d`。这两个身份均绑定到正式行为输出的检查记录。

## 样本补齐的实际变化

| 指标 | Free：480 范围 → 486 范围 | Moderate：480 范围 → 486 范围 | Tight：480 范围 → 486 范围 |
|---|---:|---:|---:|
| 轨迹数 | 160 → 162 | 160 → 162 | 160 → 162 |
| 尝试评估总数 | 3970 → 4030 | 1724 → 1755 | 621 → 629 |
| 可见、数值有效评估总数 | 3938 → 3998 | 1683 → 1714 | 547 → 555 |
| 每轨迹可见评估均值 | 24.6125 → 24.6790 | 10.5188 → 10.5802 | 3.4188 → 3.4259 |
| 自然结束 | 48 → 48 | 126 → 128 | 87 → 89 |
| 达到预算 | 0 → 0 | 23 → 23 | 66 → 66 |
| 达到步数／评估上限 | 94 → 96 | 4 → 4 | 0 → 0 |
| 其他结束原因 | 18 → 18 | 7 → 7 | 7 → 7 |
| 可见有效反馈预算利用率均值 | 无预算分母 | 88.3239% → 88.3916% | 82.8335% → 82.9221% |
| 历史 `score_complete` | 153/160 → 155/162 | 158/160 → 160/162 | 158/160 → 160/162 |

Free–Tight 成对比较从 159 对补齐为 162 对。新增 6 条带来 99 次可见有效评估，均没有新增重复配置；新增清单和各条行为见 [added_gemini_six.csv](added_gemini_six.csv)。逐项新旧差值见 [old480_vs_observed486.csv](old480_vs_observed486.csv)，包括模型、任务家族、预算及其组合的统计。

移除这 6 条后，原 480 条的 **19,200 个轨迹字段**及 **5,290 个汇总／配对字段**与冻结行为表一致；不是只验证总行数。详见 [CHECKS.json](CHECKS.json)、[old480_reproduction.csv](old480_reproduction.csv)。

## 可评分口径

历史 `score_complete` 是原运行协议是否给出了分数，**包含 `best_evaluated_fallback`**。486 条中，475 条有历史完整分数（97.7366%），其中 77 条采用已观察最佳配置回退；其余 398 条为非回退评分（81.8930%），另外 11 条保留 `unscorable_missing_configuration`。因此 CSV 同时导出：

- `score_complete` / `score_complete_fraction`：沿用历史协议，包含回退。
- `nonfallback_terminal_scored` / 同名 `_fraction`：来源为 `matching_tool_call` 或 `offline_final_answer`，排除回退；其中 2 条自然语言终答被历史 scorer 赋 0 分，并非配置。
- `submitted_json_object_scored` / 同名 `_fraction`：上述非回退评分中终答实际为 JSON 对象的 396 条（81.4815%）。JSON 结构可解析仍不保证配置在任务语义上有效。
- `final_json_object`：包含回退的最终 JSON 对象数为 473；不把回退伪称为模型提交。
- `fallback_scored`：来源为 `best_evaluated_fallback`。
- `model_final_present`：历史来源标为自然或强制模型终答且有答复文本；不是配置语义有效性的替代指标。

新增 Gemini 6 条中，NAS-B Moderate、NAS-C Moderate、NAS-C Tight 直接匹配已评估配置；Adult Free、Letter Free、Adult Tight 使用历史回退。它们有分数不代表模型都提交了可直接解析、可直接评分的最终配置。正式重评分保留这些原协议的回退规则；本次终答边界修复没有改变这 486 条的分数或这些比例。

正式逐条新旧对照见 [official_rescored486/old_new_final_comparison.csv](official_rescored486/old_new_final_comparison.csv)，全量 486 行保留旧答案、新提取文本、新计分答案、旧／新分数、可评分标志、评分来源与原因；不只导出发生变化的行。汇总对照见 [official_rescored486/historical486_vs_formal486.csv](official_rescored486/historical486_vs_formal486.csv)。[合并检查](official_rescored486/CHECKS.json) 核验 486 个原件 SHA、21,384 个未变的行为字段及重评分输入表 SHA。

`model_final_present` 保留原运行来源口径。正式 CSV 另有 `rescored_extracted_final_present` 和 `rescored_model_final_json_object`，表示离线重新提取的模型终答；不会把实际用于计分的回退配置冒充为模型提交。重评分输入的 `new_final_present` 包含回退，不能拿来替代前述模型终答指标。

## 文件及定义

`observed_behavior486/` 中保留旧分析表的文件名和原列，并添加覆盖范围、版本与分母列：

- `trajectories.csv`：486 条逐轨迹行为、历史最终分数、停止原因、原件 SHA、代码提交／源码树哈希。
- `evaluation_events.csv`：全部 6,414 次记录在轨迹中的 `evaluate_config` 尝试，含可见性、有效性、成本、配置摘要；不是 HTTP 请求数，也不包含未成为工具记录的协议错误。
- `delivered_events.csv`：6,267 次模型实际可见且性能数值有效的反馈，含最佳值出现步骤和纪录改善。
- `by_regime.csv`、`by_model_regime.csv`、`by_family_regime.csv`、`by_model_family_regime.csv`：预算、模型、任务家族汇总。
- `free_tight_pairs.csv`、`matched_free_tight_by_regime.csv`、`matched_free_tight_by_model.csv`：完整 162 对预算比较。
- `termination_reasons.csv`：保留原始终止原因，不把 `other` 合并后当作一种实际原因。

`delivered_budget_fraction` 是可见有效反馈成本除以该轨迹预算，先逐轨迹计算再平均；Free 没有预算分母，保持空值。`all_attempted_cost_seconds` 包括越预算后未交付的工具尝试，不能当成模型实际获得的反馈。最佳性能、最佳出现步骤、后续改善均仅使用可见有效反馈。配置去重沿用旧分析的数值等价规则（例如 `6` 与 `6.0` 等价）。

[SOURCE_SELECTION.csv](SOURCE_SELECTION.csv) 固定全量 486 个采用 slot、相对来源位置、原件 SHA256、字节数、代码提交及源码树哈希。只有新增 6 条来源为 `new_missing_slot`；其它 480 条逐字节保持原来源。

## 复算

从完整本地存档重读全部原件，三个路径均为显式参数，不依赖作者的绝对目录：

```bash
python3 build_behavior.py \
  --repo /path/to/LLM_ExpGym \
  --workspace-root /path/to/archive-parent \
  --frozen-delivery /path/to/paper-ad03e8c-20260916 \
  --output /tmp/hpo-behavior
```

`--workspace-root` 下须包含 `gemini_openrouter_20260917/` 存档；`--frozen-delivery` 下须有 `trajectories/`。全部原件都核验 SHA256 后才提取。

仅用公开 CSV 可重放行为汇总并核对全部评估事件：

```bash
python3 verify_public_behavior.py \
  --behavior observed_behavior486 \
  --output /tmp/hpo-public-replay.json
```

[PUBLIC_REPLAY_CHECKS.json](PUBLIC_REPLAY_CHECKS.json) 记录 486 条的 6,146 个事件级复算字段及 8 张逐字节一致的汇总表。公开 CSV 重放不冒充对私有完整轨迹的再次读取；原件读取证据单独记录于 `CHECKS.json`。

将完整新评分结果按 slot 和 SHA 合并，随后对正式行为表重放：

```bash
python3 attach_rescored.py \
  --observed observed_behavior486 \
  --agent-rows ../rescore/hpo/agent_rows.csv \
  --output /tmp/hpo-formal-behavior \
  --scoring-version final-answer-boundary-v2/existing_trace_rescored
python3 verify_public_behavior.py \
  --behavior official_rescored486 \
  --output /tmp/hpo-formal-public-replay.json
```

独立实现另外逐项复核了 198,217 个字段，覆盖全部原件、事件、汇总及配对；证据见 [independent/README.zh.md](independent/README.zh.md) 与 [independent/PUBLICATION_CHECKS.json](independent/PUBLICATION_CHECKS.json)。
