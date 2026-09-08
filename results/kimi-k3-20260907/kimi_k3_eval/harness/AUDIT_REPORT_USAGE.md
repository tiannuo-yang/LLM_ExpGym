# 结果审计与报告

在 workspace 根目录执行；所有输出目录必须是新路径，脚本不覆盖旧审计或原始结果。当前正式矩阵是 `full_v3`，`full` / `full_v2` 为不同源码版本的历史归档，不可代替当前成绩。审计是离线评分，不调用 LLM API。ParamNet 通过独立 Python 3.7 子进程评分，脚本自行配置固定 HPO 数据/缓存路径，无需 source 环境。

    LLM_ExpGym/.venv/bin/python kimi_k3_eval/harness/audit_results.py \
      --manifest kimi_k3_eval/runs/full_v3/manifest.json \
      --legacy-python kimi_k3_eval/data_runtime/.venv-hpo/bin/python \
      --output-dir kimi_k3_eval/reports/audit_full_YYYYMMDD

    LLM_ExpGym/.venv/bin/python kimi_k3_eval/harness/audit_dumps.py \
      --manifest kimi_k3_eval/runs/full_v3/manifest.json \
      --output-dir kimi_k3_eval/reports/dump_audit_full_YYYYMMDD

    LLM_ExpGym/.venv/bin/python kimi_k3_eval/harness/summarize_results.py \
      --audit kimi_k3_eval/reports/audit_full_YYYYMMDD/audit.json \
      --dump-audit kimi_k3_eval/reports/dump_audit_full_YYYYMMDD/raw_dump_audit.json \
      --output-dir kimi_k3_eval/reports/results_full_YYYYMMDD

评分审计不完整返回 2，dump 审计不完整返回 1；各自已验证完整返回 0。草稿汇总可显式加 --allow-partial；缺失/失败的正式表格单元格为 null，不补 0。有效模型零分与预算停止仍计入性能。完整真实 full 报告必须提供通过的 dump audit。最终审计应在全部任务完成及协调者的 verified-resume 验证结束后进行，以免执行凭据继续变化。

audit.json / artifact_index.csv 逐条列出状态、错误、原始路径、SHA256；missing.json 为缺文件，failed.json 为内容/配置/评分或执行证据失败，execution_failures.json 单独列非零退出的 subprocess。完整性要求包含：

- full 精确 303 ExpGym + 513 PoolAct results / 2052 agents；完整任务/重复/strategy 标识去重检查。
- 实际 source、配置、模型、种子、hypothesis 顺序、数据文件内容及生成选项符合冻结 manifest。
- v2 JSON schema 和跨记录引用检查；每个答案独立调用当前 repository evaluator 重算。
- PoolAct 所有 agent 文件与 embedded results 一致、aggregate 重算一致、summary 完整、shared_state.graph.pending_claims=0。
- subprocess 退出码和最后一次日志字节范围内的逐结果 score_check/verified-resume 标记。

报告输出 artifacts.csv、agents.csv、task_metrics.csv、aggregate_metrics.csv、summary.json、REPORT.zh.md。ExpGym Gap 每 trace 先裁剪，再按 task/repeat、family/task 分层求均值；PoolAct MI 每 agent 先裁剪。全量和论文 PoolAct 子集分别列出。汇总会再次校验结果、执行凭据、数据 provenance 与 API dump 是否在审计后变化。

若 full manifest 指向 promotion_map.json，报告计入保存的原 pilot execution receipts，并分别列出 pilot 与 full/resume 的耗时；不会把 resume 的几秒当成已复用轨迹的原始运行成本。并发总秒数与真实执行跨度、模拟反馈预算分别报告。缺失历史 attempt 时间时，完整总数为 null，并另外给已知总数与缺失计数。

无 API 的集成检查：

    LLM_ExpGym/.venv/bin/python kimi_k3_eval/harness/test_audit_reporting.py

检查覆盖真实 fake-runner 产生的 Search/Audit/NAS101/ParamNet 文件、非零 Audit verification_eff 重建、score 篡改、agent 文件缺失/不一致、pending claims、模型标签一致性、Gap 裁剪顺序、推广成本及未知历史 attempt。若需留存该 fake fixture，设置 KIMI_AUDIT_FIXTURE_DIR 为尚不存在的独立目录。

## 最终展示层

build_delivery.py 从已经通过的 summary / CSV / 双审计生成简洁中文 overview。JSON 和 CSV 逐字段对账，模型/stage/manifest 指纹必须一致，raw results 与 API dump 也复核 SHA。此步骤不调用 API，不启动/释放 Slurm 服务，不改变原结果。

    LLM_ExpGym/.venv/bin/python kimi_k3_eval/harness/build_delivery.py \
      --summary kimi_k3_eval/reports/results_full_YYYYMMDD/summary.json \
      --output-dir kimi_k3_eval/reports/delivery_full_YYYYMMDD \
      --runtime-estimate kimi_k3_eval/reports/runtime_YYYYMMDD/runtime_estimate.json \
      --protocol-diagnostics kimi_k3_eval/reports/protocol_YYYYMMDD/diagnostics.json \
      --service-receipt kimi_k3_eval/serving/runs/JOB/acceptance.json \
      --slurm-receipt kimi_k3_eval/serving/reports/JOB_final_receipt.json

后四项均可省略；未附证据的字段保持 null。Slurm receipt 支持 capture_slurm.py 的 allocations[] schema，按 service job_id 精确匹配；已确认 GPU 数与 elapsed_seconds 才计算 Allocated GPU-hours，并区分运行中已知快照与 final=true 最终成本、当前服务 allocation 与本项目全部 owned allocations。其他原始 JSON 可引用，但未知字段不猜值。raw_file/raw_sha256 也会复核。服务 ready 不代表作业已结束，step/extern 不重复计费。额外环境、模型、日志等文件可重复使用 --evidence NAME=PATH 附加 SHA 索引。

输出 OVERVIEW.zh.md、delivery.json、expgym_wide.csv（3 regime × 7 指标）、poolact_paper_wide.csv（2 regime × 3 strategy × 6 指标）、poolact_full_extension.csv。delivery.json 每个数值格都保留原聚合行、样本数和 trace 路径。smoke/pilot 始终显著标为非正式全量结果；缺维度不补零。length 截断次数及原始 dump 链接明确保留；请求 thinking=false 与实际 reasoning_content 字段分别展示，不将 parser 分段直接解释成模型行为。

展示边界检查不调用 API：

    LLM_ExpGym/.venv/bin/python kimi_k3_eval/harness/test_build_delivery.py
