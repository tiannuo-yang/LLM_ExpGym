# Whois 独立运行控制

仅包含预注册 GLM β20、phantom_seed2:5、seed2200 的首次完整新运行。无条件采用其分数与实际成本，不按高分筛选。其与主实验 β10 不重复。

`scoring_inputs.jsonl.gz` 可用 `tools/replay_control_flow_results.py` 真正重提取终答并重评分；其中只保留终答、任务 gold、终端资格、哈希和成本标量。实际成本由新 trajectory 和全部 API attempt 核验后导出，不含 HTTP 内容或 reasoning。

`actual_agents.csv`、`actual_attempts.csv` 包含全部实际重试、工具次数、时长与未知 usage；`COLLECTION_CHECKS.json`、`COST_CHECKS.json` 记录来源验证。
