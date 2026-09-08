# Kimi-K3 在 ExpGym / PoolAct 的实验

> 最终状态（2026-09-07 UTC）：全部验收完成。正式矩阵342/342 jobs、0执行失败，303 ExpGym traces +513 PoolAct results/2,052 agents全部通过双审计与独立复算，零调用resume通过，最终报告已生成。本任务8节点/64 GPU已释放，历史服务端点已停止，无关作业未改动。

这是 **Custom study**：沿用论文主设定并覆盖仓库完整矩阵，统一冻结源码 `evaluation_recovery_v3` / `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`，不是原版逐字节复现。PoolAct论文主表192组结果从513组全量结果筛选，不额外调用模型。

## 查验入口

| 内容 | 位置 |
|---|---|
| 最终总览与交付清单 | [OVERVIEW.zh.md](reports/final/OVERVIEW.zh.md)、[delivery.json](reports/final/delivery.json) |
| 交付文件、34份引用及57个链接的最终完整性核对 | [file_integrity.json](reports/final/file_integrity.json) |
| 规整主表CSV | [ExpGym](reports/final/expgym_wide.csv)、[PoolAct论文子集](reports/final/poolact_paper_wide.csv)、[PoolAct全量扩展](reports/final/poolact_full_extension.csv) |
| 结果解读与局限 | [full_v3_interpretation.zh.md](reports/full_v3_interpretation.zh.md) |
| 完整成绩与机器可读汇总 | [REPORT.zh.md](reports/full_v3_results_final/REPORT.zh.md)、[summary.json](reports/full_v3_results_final/summary.json) |
| 论文子集/全量聚合、逐任务、逐agent、文件索引 | [aggregate_metrics.csv](reports/full_v3_results_final/aggregate_metrics.csv)、[task_metrics.csv](reports/full_v3_results_final/task_metrics.csv)、[agents.csv](reports/full_v3_results_final/agents.csv)、[artifacts.csv](reports/full_v3_results_final/artifacts.csv) |
| 正式分数与原始请求双审计 | [评分审计](reports/full_v3_audit_final/audit.json)、[dump审计](reports/full_v3_dumps_final/raw_dump_audit.json) |
| 三个分区独立核对 | [HPO](reports/full_v3_hpo_independent_review/POST_RESUME_FINAL.zh.md)、[Search](reports/full_v3_search_independent_review_post_resume/README.zh.md)、[Audit](reports/full_v3_audit_independent_review/REPORT_FINAL.zh.md) |
| 零调用resume及原字节不变证明 | [resume_full_v3.comparison.json](reports/resume_full_v3.comparison.json) |
| 原始生成耗时与正式清单 | [生成完成progress](reports/full_v3_generation_completed/progress.json)、[manifest.json](reports/full_v3_generation_completed/manifest.json) |
| 正式协议诊断与论文对照 | [full_v3_protocol_final.md](reports/full_v3_protocol_final.md)、[PAPER_ALIGNMENT.md](protocol/PAPER_ALIGNMENT.md) |
| 冻结源码、合并diff、环境 | [evaluation_recovery_v3/](provenance/evaluation_recovery_v3/)、[静态/fake及数据验收](data_runtime/validation_v3/README.md) |
| 8节点SGLang部署、uv环境及历史运行日志 | [serving/](serving/) |
| 最终GPU记账与资源释放证明 | [slurm_receipt.json](serving/reports/final_accounting_20260907_after_cleanup/slurm_receipt.json)、[release_confirmation.json](serving/reports/final_accounting_20260907_after_cleanup/release_confirmation.json) |
| 九份实验manifest范围的去重用量 | [用量说明](reports/project_usage_final/README.zh.md)、[完整JSON](reports/project_usage_final/project_usage_inventory.json)、[逐请求CSV](reports/project_usage_final/unique_raw_requests.csv) |
| 每阶段验收、历史ETA、修复及归档 | [PLAN.md](PLAN.md)、[RECOVERY_PLAN.md](RECOVERY_PLAN.md) |

原始请求/响应及usage保存在 `dumps/`，正式轨迹在 `runs/full_v3/`，由manifest、审计索引及request/client ID关联；不含Authorization。v1/v2的全部结果、失败记录与消耗原位保留，不计入正式分数。

## 如何解读

采用原始textual ReAct `Action: tool_name JSON`，未将K3 native工具标签转译；结果衡量该协议下表现，不代表K3最佳native工具能力。NAS101 B/C保留原仓库提示及其编码矛盾，[提示候选未应用](protocol/nas101_hints_status_evaluation_recovery_v3.json)。请求`thinking=false`不能证明无reasoning；字段与计数限制见[服务诊断](serving/REASONING_MODE_DIAGNOSTIC.md)。实际低分、missing_action与强制回答均保留，不能用完整性通过代替能力结论。

## 耗时与复查

正式生成：10:46:07.804–11:50:46.746 UTC，**64.65分钟**；另一次11:52:02.793–11:52:28.704 UTC的resume用时25.91秒、0新增调用，12,107个文件（3,039结果JSON +9,068 API JSON）的集合与字节全部不变。当前 `runs/full_v3/progress.json` 属于resume，不能据此把模型生成耗时写成25.91秒。

九份v1/v2/v3 smoke/pilot/full manifest合计13,668唯一HTTP调用，17,046个dump位置；3,378个推广副本不重计。输入29,662,818、输出3,973,226 tokens，包含失败/未选中实验消耗，不含服务探针等非manifest流量；不等于正式full独立用量或GPU-hours。

Slurm最终分配用量为**218.70 GPU-hours**：正式服务202.6844、bootstrap 16.0178，含加载、验证、推理及空闲，并非GPU利用率。11:57:35 UTC主动取消本任务作业1203299，记账结束11:57:36，11:59:32确认队列中已无该作业。服务地址仅作历史证据；重新运行需重新申请资源、启动服务并使用独立新输出目录，不覆盖已验收结果。

从上级工作区执行只读复查：

```bash
jq '{complete, valid_counts}' kimi_k3_eval/reports/full_v3_results_final/summary.json
jq '{passed, difference_counts, before_totals, after_totals}' kimi_k3_eval/reports/resume_full_v3.comparison.json
LLM_ExpGym/.venv/bin/python kimi_k3_eval/harness/run_study.py --help
```
