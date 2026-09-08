# Kimi-K3 × ExpGym / PoolAct：结果与原始证据

正式结果已完成：342/342 个运行任务，303 条 ExpGym traces、513 份 PoolAct results（2,052 条 agent traces），合计 2,355 条 agent traces。评分重算、原始 API dump 对齐、独立分区复核和无新增调用的 resume 检查均已通过。

这是 **Custom study**，不是论文数值的精确复现，也不是 K3 原生工具协议的最佳能力评测。论文设置、偏离和协议限制均在下方报告中保留。只有 `full_v3` 是正式全量成绩；v1/v2 和 fake 目录是历史验证/恢复证据，不计入正式成绩。v3 smoke/pilot 是阶段验证，其中 v3 pilot 的 36 个任务经原字节 promotion 后作为 `full_v3` 子集纳入，绝不重复计分。

## 先看这里

| 要查什么 | 入口 |
|---|---|
| 中文结果总览、主要表格、设置与限制 | [OVERVIEW.zh.md](kimi_k3_eval/reports/final/OVERVIEW.zh.md) |
| 对结果的解释 | [full_v3_interpretation.zh.md](kimi_k3_eval/reports/full_v3_interpretation.zh.md) |
| ExpGym 七维度汇总（3 行） | [expgym_wide.csv](kimi_k3_eval/reports/final/expgym_wide.csv) |
| PoolAct 论文子集（6 行） | [poolact_paper_wide.csv](kimi_k3_eval/reports/final/poolact_paper_wide.csv) |
| PoolAct 全量扩展（189 行） | [poolact_full_extension.csv](kimi_k3_eval/reports/final/poolact_full_extension.csv) |
| 逐结果、逐 agent、逐任务指标及评分口径 | [full_v3_results_final/](kimi_k3_eval/reports/full_v3_results_final/) |
| 每阶段验收标准与完成记录 | [PLAN.md](kimi_k3_eval/PLAN.md)、[RECOVERY_PLAN.md](kimi_k3_eval/RECOVERY_PLAN.md) |
| 论文设置对照 | [PAPER_ALIGNMENT.md](kimi_k3_eval/protocol/PAPER_ALIGNMENT.md) |

完整 PoolAct 扩展覆盖 3 个 regime × 3 种策略（naive/cached/poolact），每组 4 agents；论文子集单独列出 Moderate/Tight 下的 whois、Audit 和 NAS101:A，不把扩展矩阵冒充论文原表。

## 原始数据与审计

| 证据 | 入口 |
|---|---|
| 正式任务清单及结果文件 | [runs/full_v3/](kimi_k3_eval/runs/full_v3/) |
| 正式完整请求/响应 dump（9,068 份） | [dumps/full-full_v3-ad4275b6/](kimi_k3_eval/dumps/full-full_v3-ad4275b6/) |
| 评分与结构审计 | [audit.json](kimi_k3_eval/reports/full_v3_audit_final/audit.json) |
| 原始请求/响应与 trace 对齐审计 | [raw_dump_audit.json](kimi_k3_eval/reports/full_v3_dumps_final/raw_dump_audit.json) |
| 交付表格、来源与 SHA256 | [delivery.json](kimi_k3_eval/reports/final/delivery.json)、[file_integrity.json](kimi_k3_eval/reports/final/file_integrity.json) |
| 无改写、无新增调用的 resume 复核 | [resume_full_v3.comparison.json](kimi_k3_eval/reports/resume_full_v3.comparison.json) |
| HPO 独立复核 | [POST_RESUME_FINAL.zh.md](kimi_k3_eval/reports/full_v3_hpo_independent_review/POST_RESUME_FINAL.zh.md) |
| Search 独立复核 | [comparison.json](kimi_k3_eval/reports/full_v3_search_independent_review_post_resume/comparison.json) |
| Audit 独立复核 | [REPORT_FINAL.zh.md](kimi_k3_eval/reports/full_v3_audit_independent_review/REPORT_FINAL.zh.md) |
| 所有阶段 API 使用量及去重 | [project_usage_final/](kimi_k3_eval/reports/project_usage_final/) |
| 全部历史结果 / dumps / 日志 | [runs/](kimi_k3_eval/runs/)、[dumps/](kimi_k3_eval/dumps/)、[logs/](kimi_k3_eval/logs/) |

所有阶段共保留 17,046 个评测 API JSON 文件位置，其中 3,378 个是 v1/v2/v3 的 pilot→full 原字节推广副本，去重后 13,668 个请求。正式成绩只使用与 `full_v3` 对齐的 9,068 个请求。大 JSON 建议 clone 后查看，不依赖 GitHub 网页完整渲染。

## 耗时与服务

正式全量生成阶段：2026-09-07 10:46:07–11:50:46 UTC，实测 **64 分 39 秒**；v3 pilot 为 12 分 38 秒，v3 smoke 为 4 分 57 秒。总览中的 4,899.92 秒是选中结果包含复用 pilot 的执行时间跨度，不是单独 full 阶段计时；并发 subprocess 累计时长也不能当作墙钟。

服务按 `-A k2p` 使用 8 节点、64 张 H200，以 4 个双节点 TP16/EP16 副本提供本地 SGLang API。独立 uv 环境、依赖版本、补丁、启动与验收证据见 [serving/README.md](kimi_k3_eval/serving/README.md) 和 [independent/](kimi_k3_eval/serving/independent/)。服务已在评测结束后释放；Slurm 最终 `CANCELLED` 是主动释放，并非正式评测失败。

服务分配 202.68 GPU-hours；含环境准备的本项目已确认分配合计 **218.70 GPU-hours**。这些数值含加载、验证和空闲，并非有效 GPU 利用量。详见 [最终 Slurm 记录](kimi_k3_eval/serving/reports/final_accounting_20260907_after_cleanup/slurm_receipt.json) 和 [释放确认](kimi_k3_eval/serving/reports/final_accounting_20260907_after_cleanup/release_confirmation.json)。

## 可复现范围与已知限制

- 评测代码基线：`703719150e8d44712ace50d6439686423dcd1328`；论文源码版本：`f763d3877f6970a918c0a163099c409ea067dda6`。
- 正式源码 fingerprint：`c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`。本分支根目录代码仍是基线；实际评测使用的 58 个源码文件快照在 [LLM_ExpGym/](LLM_ExpGym/)，原 tar、差异补丁和锁定依赖在 [evaluation_recovery_v3/](kimi_k3_eval/provenance/evaluation_recovery_v3/)。不要误用分支根目录代码解释 v3 结果。
- 请求 `thinking=false`，`max_tokens=8192`，最大 30 steps/evals，沿用文本 ReAct；未把 K3 原生 XTML 工具标记转换为框架工具调用。共 1,829/2,355 条 traces 出现 missing_action（PoolAct 部分为有来源的推断），因此框架跑通与模型语义表现必须区分。
- 观察到 170 份非空 `reasoning_content` 和 4 份 `finish_reason=length`，均保留原文；不能从请求开关或 reasoning token counter=0 推断响应没有 reasoning 文本。
- 原始 8,000 字符解析上限和 NAS101 B/C 提示/编码差异保留且单独审计；未应用候选修正后重跑，不作其分数因果影响的结论。见 [协议诊断](kimi_k3_eval/reports/full_v3_protocol_final.md)、[逐例 cap 复核](kimi_k3_eval/reports/full_v3_cap_review/review.json) 和 [NAS101 状态](kimi_k3_eval/protocol/nas101_hints_status_evaluation_recovery_v3.json)。
- 未上传权重、下载的数据集、虚拟环境、wheel/cache、集群镜像或凭据。数据与 checkpoint 的位置/检查范围见 [dataset_manifest.json](kimi_k3_eval/data_runtime/dataset_manifest.json) 和 [checkpoint.json](kimi_k3_eval/provenance/initial/checkpoint.json)。Checkpoint 检查覆盖索引、头部、offset 和文件大小，并非所有权重 payload 的完整 SHA256。

## 本地查验与路径映射

```bash
git clone --branch results/kimi-k3-20260907 --single-branch https://github.com/tiannuo-yang/LLM_ExpGym.git
cd LLM_ExpGym/results/kimi-k3-20260907
python3 verify_publication.py
```

验证脚本仅用 Python 标准库，不启动模型或评测。它逐文件核对本次发布的原始证据 SHA256/字节数、正式交付文件哈希、总览相对链接和发布附加文件清单。

原始 JSON/CSV/日志里的绝对路径参与审计，发布时**没有改写原始文件**。将前缀 `/lustrefs/users/chufan.shi/codex_space_tn/` 映射到本 README 所在目录，即可定位已打包的 `kimi_k3_eval/…` 与 `LLM_ExpGym/…`；权重、下载数据和环境仍是外部依赖，不能只做路径替换后就假定可执行。部分历史 Markdown 绝对路径链接保留原样，请使用本页导航或该映射查找。

[PUBLICATION_MANIFEST.json](PUBLICATION_MANIFEST.json) 列出每个原始文件的源路径、发布路径、字节数与 SHA256，以及明确排除的外部材料。[publication_checks/](publication_checks/) 保存发布前凭据扫描和独立链接/哈希检查；扫描通过表示指定规则未留下未解决命中，不是对任意形式秘密的绝对保证。[PUBLICATION_CHECKSUMS.json](PUBLICATION_CHECKSUMS.json) 覆盖所有发布文件（清单自身除外）；Git commit 标识绑定包含该清单的完整版本。
