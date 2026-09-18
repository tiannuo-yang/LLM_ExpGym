# Whois：正式运行控制后的六模型预算分析

本版保留原 1,170 个实验位置，对所有旧终答先重新评分，再无条件采用预注册的一个新 GLM β=20 运行。其余 1,169 个位置继续采用既有轨迹重评分结果。历史结果、旧轨迹修复评分、新运行正式采用三个层次分别保留。

新运行位置为 `whois:glm:beta20:phantom_seed2:5:R1`。该题旧/修复分数为 1.000000，新运行 F1 为 1.000000。全表有 0 个 F1、0 个排名位置相对历史变化。

| 模型 | β1 | β5 | β10 | β15 | β20 |
| --- | ---: | ---: | ---: | ---: | ---: |
| gpt | 6.84 | 36.87 | 59.75 | 63.17 | 63.27 |
| kimi | 6.84 | 32.19 | 57.30 | 65.20 | 64.35 |
| glm | 7.69 | 36.25 | 64.28 | 65.79 | 69.03 |
| qwen | 7.26 | 37.78 | 61.13 | 61.21 | 61.49 |
| deepseek | 5.56 | 33.99 | 49.75 | 62.11 | 61.21 |
| gemini | 8.72 | 40.09 | 62.77 | 67.09 | 72.43 |

数值为 F1×100，每点39题。β=10的234位置复用主实验，不能再算独立样本；其余936位置为独立预算实验。Gemini β=10来自历史Sub2，其他β来自OpenRouter，保留提供方/批次差异。

旧轨迹全量终答修复原本导致2个提取文本变化、0个F1变化；本页的新运行变化应与该旧轨迹诊断分开解释。除GLM β=20及涉及它的排名/预算差值外，其余29个模型×预算设置的成绩和成本完全保留。

成本也替换成此次真实新运行：移除旧任务 21 条attempt，采用新任务 21 条attempt。所有重试和未知usage保持原义；详见 `runtime_behavior_changes.csv` 和 `inputs/agents.csv`、`inputs/attempts.csv`。

复算：`tools/build_whois_control_flow_overlay.py --base-whois WHOIS_EXISTING_TRACE --existing-sweep RESCORE_SWEEP --new-inputs CONTROL_SWEEP/scoring_inputs.jsonl.gz --output NEW_DIR --plots`。该入口真实调用解析器及任务评分器，无需私有原件、Parquet、Git或网络；绘图另需matplotlib。
