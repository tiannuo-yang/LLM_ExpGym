# 正式采用后的四层评分对照

全表 **4,698 个主实验位置**逐项并列：旧正式分数、此前诊断、完整既有轨迹重评分、最终正式运行采用。四层独立保存，未把诊断或离线评分冒充新的运行。

总采用 gate 已通过：97 个 HPO 新池、21 个 Search/Audit 新位置（78 成员）及独立 Whois 控制 1 项。主表有 **118** 个位置采用新的运行来源，其中 **109** 个位置至少一个数值指标相对既有轨迹重评分发生变化。Whois 仍在独立报告中，不加入 4,698 主表。

原诊断范围保持 **23 个成员、19 个分数变化池**；未诊断位置保持空值，不推断 MI、HPO 或未报告指标。完整三份诊断参考 CSV 与原 `DIAGNOSTIC_REFERENCE.json` 逐字节保留。当前全量重评分与最终运行层覆盖全部主表。

GLM Free N1 EA 百分比：旧正式 68.47662142 → 原诊断 83.86123680 → 既有轨迹重评分 86.42533937 → 正式采用 86.42533937。

- `score_layer_comparison.csv`：全部4,698项的四层数值、来源SHA与逐层差值。
- `audit_layer_group_means.csv`：108组Audit宏平均，明确各层分母和诊断覆盖。
- `CHECKS.json`：正式采用完整性、全部输入/输出SHA、算法和空值口径。

从公开仓库根目录复算：

```bash
python3 -B results/protocol-repair-20260918/score_layers/compare_score_layers.py \
  --main results/protocol-repair-20260918/rescore/main \
  --reference results/protocol-repair-20260918/score_layers \
  --output /tmp/score-layers-replay \
  --official results/protocol-repair-20260918/control_flow_adoption/new_official/slot_scalars.csv \
  --official-sources results/protocol-repair-20260918/control_flow_adoption/new_official/SOURCE_SELECTION.csv \
  --adoption results/protocol-repair-20260918/control_flow_adoption/new_official/SOURCE_SELECTION.csv \
  --adoption-layer-column selection
```

这一步重建四层对照和宏平均；底层终答解析、任务评分及采用关系由统一 `tools/verify_protocol_repair.py --full` 重新核验。它不重新调用模型或重放未公开的完整HTTP/图决策历史。
