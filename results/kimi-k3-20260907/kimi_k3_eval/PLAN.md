# Kimi-K3 × ExpGym / PoolAct 实验计划与验收

开始日期：2026-09-07 UTC。实验类型：**Custom study**（新增本地 Kimi-K3，沿用论文主实验设置，并覆盖 **Current repository full matrix** 的任务范围）。

> 最终状态（2026-09-07 UTC）：阶段0–7全部通过。正式full_v3完成342/342 jobs、0执行失败，303 ExpGym +513 PoolAct/2,052 agents全部双审计与三个分区独立复算通过，零调用resume通过；最终总览、CSV及交付清单已生成。11:59:32 UTC确认本任务作业1203299已退出队列且CANCELLED，8节点/64 GPU完全释放，无关作业未动。统一v3分数不混入v1/v2，历史ETA仅保留对照。

正式查验入口：[最终总览](reports/final/OVERVIEW.zh.md)、[交付清单](reports/final/delivery.json)、[结果解读](reports/full_v3_interpretation.zh.md)、[完整成绩](reports/full_v3_results_final/summary.json)、[评分审计](reports/full_v3_audit_final/audit.json)、[dump审计](reports/full_v3_dumps_final/raw_dump_audit.json)、[resume不变证明](reports/resume_full_v3.comparison.json)、[原始生成完成记录](reports/full_v3_generation_completed/progress.json)、[九manifest去重用量](reports/project_usage_final/README.zh.md)、[最终Slurm记账](serving/reports/final_accounting_20260907_after_cleanup/slurm_receipt.json)、[资源释放证明](serving/reports/final_accounting_20260907_after_cleanup/release_confirmation.json)。

当前入口：[恢复说明](RECOVERY_PLAN.md)、[评分修复离线证据](reports/nas101c_moderate_agent3_diagnostic/evidence.json)、[v3源码快照](provenance/evaluation_recovery_v3/manifest.json)、[v3静态/fake与数据验收](data_runtime/validation_v3/README.md)、[smoke_v3简报](reports/smoke_v3_delivery_final/OVERVIEW.zh.md)、[v3全量dry-run](runs/full_v3/manifest.dry-run.json)。v3完整检查250项，246通过、4项既有环境skip，legacy 16项通过。NASBench101提示保持原样，用户尚未回复提示修订选择；[提示候选补丁](patches/nas101_hints_fix.patch) 未应用。

预验收记录：[pilot_v3简报](reports/pilot_v3_delivery_final/OVERVIEW.zh.md)、[pilot评分审计](reports/pilot_v3_audit_final/audit.json)、[pilot dump审计](reports/pilot_v3_dumps_final/raw_dump_audit.json)、[pilot协议诊断](reports/pilot_v3_protocol_final.md)、[原ETA及外推假设](reports/pilot_v3_runtime_estimate/RUNTIME_ESTIMATE.md)、[推广映射](runs/full_v3/promotion_map.json)。正式全量协议统计见 [full_v3_protocol_final.md](reports/full_v3_protocol_final.md)，不使用smoke/pilot率代替。

当前源码指纹：`c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`（`evaluation_recovery_v3`）。v2查验记录继续保留：[pilot简报](reports/pilot_v2_delivery_final/OVERVIEW.zh.md)、[pilot评分审计](reports/pilot_v2_audit_final/audit.json)、[pilot原始dump审计](reports/pilot_v2_dumps_final/raw_dump_audit.json)、[已暂停适用的v2 ETA](reports/pilot_v2_runtime_estimate/RUNTIME_ESTIMATE.md)、[推广清单](runs/full_v2/promotion_map.json)、[full归档评分审计](reports/archived_full_v2_audit_20260907_1023/audit.json)、[full归档dump审计](reports/archived_full_v2_dumps_20260907_1023/raw_dump_audit.json)、[v1+v2全项目消耗](reports/archived_v1_v2_project_usage/project_usage_inventory.json)。

## 固定输入与范围

- Repo: `../LLM_ExpGym`，初始核对时已存在且 clean；2026-09-07 核对 origin/main 为 `703719150e8d44712ace50d6439686423dcd1328`。当前适配后的源码以以上 `evaluation_recovery_v3` 指纹与快照为准。
- Paper: `../expgym-paper`，当前 ICLR 2026 工作版本，HEAD `f763d3877f6970a918c0a163099c409ea067dda6`；具体设置由 `protocol/PAPER_ALIGNMENT.md` 复核。
- 权重：`/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Kimi-K3/`；仅读取，记录模型配置、分片索引及文件完整性。
- 新建 uv 环境；SGLang 使用独立 Slurm 作业，账户 `k2p`，8 节点，每节点 8 GPU（64 GPU）。已有其他作业不属于本次实验。
- ExpGym：9 HPO 任务 × 3 repeats + 35 Search questions + 13 Audit documents × 3 hypothesis orderings，再 × 3 cost regimes = **303 traces**。
- PoolAct 全量：9 HPO + 35 Search + 13 Audit，再 × 3 regimes × 3 strategies (`naive,cached,poolact`) = **513 item/strategy results**，每组 N=4，共 **2,052 agent traces**。
- PoolAct 论文主表子集：NASBench101:A + 18 whois Search + 13 Audit，再 × Moderate/Tight × 3 strategies = **192 results / 768 agent traces**，从全量结果筛选，不重复调用。
- ExpGym tuning 温度 0.7，Search/Audit 温度 0.0；PoolAct 温度 0.7；max_steps=30、max_evals=30。记录 seed、hypothesis ordering、实际推理关闭方式、生成参数及任何偏离。
- 附录的其他原始模型 scaling、lock ablation 和 extended-reasoning 分析不属于本次 Kimi-K3 主实验全量范围；如论文对上述主实验有额外要求，以核对结果明确记录。

## 分阶段验收标准

| 阶段 | 交付与通过条件 | 状态 |
|---|---|---|
| 0 协议与计划 | 核对 skill、论文、repo；完整矩阵 dry-run 与预期数量相等；固定版本、种子和设置 | 通过；请求thinking=false，实际偶有reasoning，偏离见协议 |
| 1 环境与数据 | uv 环境可重建并保存依赖锁定；完整 `scripts/check.sh` 通过；数据校验通过；9 HPO 任务均可计算且 oracle 校验有效；记录 legacy ParamNet 运行方式 | v3通过：250项/246通过/4skip、legacy 16项；27 ExpGym fake +27 PoolAct/54agents、9HPO oracle/双环境等价、46份数据SHA256全部通过 |
| 2 八节点服务 | 新作业 -A k2p、8 节点；64 GPU/拓扑记录；所有 rank 正常加载；health/models/chat 成功；真实目标模型、非空输出和 usage 留存 | 通过：4副本及100k上下文验收通过；最终已正常收尾并释放8节点/64 GPU，部署与终态凭据保留 |
| 3 真实闭环 | ExpGym 三场景×三regime；PoolAct 三场景×论文两regime×三strategy，最小 N=2；schema/score recomputation通过、无pending claims；保存所有trace与请求响应 | smoke_v3通过：10:25:28–10:30:26 UTC，15/15 jobs、45traces双审计complete=true，146HTTP全部success/stop |
| 4 容量估计 | 代表性30步pilot，记录真实calls/tokens/秒、失败与retry，分别外推ExpGym及PoolAct，给范围及余量；全量并发由实测决定 | 通过：pilot_v3 36/36 jobs、258traces、12.64分钟，双审计complete；1.62–1.87小时含余量估计与最终64.65分钟实际时间均保留 |
| 5 全量执行 | 303 ExpGym、513 PoolAct result、2052 agents全部产出；可恢复；错误单独记录并修复/重跑；不得把未完成计作0分 | 通过：342/342 jobs、0执行失败；303/513/2052全部产出，论文子集192组覆盖；11:50:46 UTC生成结束，64.65分钟 |
| 6 结果审计 | 每个结果schema/config/source与计划一致，重算评分通过，PoolAct aggregate有限且pending_claims=0；验证恢复会跳过兼容结果；保存完整清单、校验和、耗时与usage | 通过：正式双审计complete=true、summary通过、三个分区独立复算PASS；resume 0新调用，12,107文件集合/字节不变 |
| 7 最终交付 | 主报告、CSV/JSON汇总、论文子集与全量表、逐项结果索引、原始API dump、运行日志、脚本、环境/模型/数据provenance齐全；准确列出偏离和失败 | 通过：final/总览、delivery.json与三张规整CSV已生成，official_full_matrix_complete=true；结果解读、终态及218.7022分配GPU-hours凭据齐全 |

## 输出布局

所有本次实验管理文件存于本目录；代码仓库保留独立。

- `serving/`：uv 环境/依赖、Slurm 启动脚本、job metadata、各 rank logs、API probe。
- `data_runtime/`：数据校验日志、HPO 环境、下载/版本 provenance。
- `protocol/`：论文对照、固定矩阵与配置。
- `harness/`：运行/恢复/审计/汇总脚本。
- `runs/smoke_v2/`、`runs/pilot_v2/`：v2已验收记录；`runs/full_v2/`：v2最终排空状态、已产出结果及推广映射。所有v2结果/dump/归档审计/成本原位保留，不计入v3成绩。
- `runs/smoke_v3/`、`runs/pilot_v3/`：已验收真实闭环与代表性pilot；`runs/full_v3/`：正式全量结果及原字节推广映射。此目录当前progress属于完成后的零调用resume；原始生成progress/manifest另冻结在 `reports/full_v3_generation_completed/`。
- `runs/smoke/`, `runs/pilot/`, `runs/full/`：历史归档，原始轨迹与执行记录原位保留，不计入新版验收。
- `dumps/`：逐次模型请求/响应/usage/耗时和失败记录；不保存Authorization等凭据。
- `logs/`：安装、检查、runner及编排日志。
- `reports/`：运行状态、时间预估、逐项CSV、聚合表、最终报告、校验和。

## 实际耗时与历史时间估计

实际正式生成为10:46:07.804011–11:50:46.745903 UTC，3,878.9419秒，即64.65分钟；见 [原始生成progress](reports/full_v3_generation_completed/progress.json)。后续11:52:02.793–11:52:28.704 UTC为独立的零调用resume验收，25.91秒，不是模型生成耗时。原 `runs/full_v3/progress.json` 已记录这次resume，故时间报告必须使用正确阶段的冻结凭据。

启动前ETA基于完整且双审计通过的 `pilot_v3`：10:30:48.692–10:43:27.128 UTC，36/36 jobs、258traces、12.64分钟；1,193HTTP全部success/stop，2,889,395 input +317,983 output tokens。复用36jobs后剩余306jobs/2,097traces，分层外推点估计约1.25小时，加30–50%工程余量为1.62–1.87小时，非统计置信区间；当时预计约12:25–12:40 UTC运行结束后再审计。最终11:50:46 UTC提前完成，详见 [原ETA报告](reports/pilot_v3_runtime_estimate/RUNTIME_ESTIMATE.md)。所有历史估计均不再作为待完成承诺。

九份v1/v2/v3 smoke/pilot/full manifest的最终去重用量为13,668唯一HTTP请求、17,046个位置、3,378个相同字节推广副本不重计；input 29,662,818、output 3,973,226 tokens。包含归档失败和未选中响应消耗，不含service probes或其他非manifest流量；不等于正式full单阶段用量、服务所有流量或GPU-hours。范围与证据见 [project_usage_final/README.zh.md](reports/project_usage_final/README.zh.md)。

最终Slurm分配用量：服务202.6844444444 GPU-hours、bootstrap 16.0177777778 GPU-hours，合计218.7022222222 GPU-hours。包含环境bootstrap、权重加载、验证、推理和空闲，不是GPU实际利用率；step/extern行不重复累加。最终凭据采用 [after_cleanup/slurm_receipt.json](serving/reports/final_accounting_20260907_after_cleanup/slurm_receipt.json) 与 [release_confirmation.json](serving/reports/final_accounting_20260907_after_cleanup/release_confirmation.json)，不使用清理过程中的中间receipt替代终态。

保留v2外推与成本记录：`pilot_v2` 36/36 jobs、258traces，09:45:07.883–09:59:51.441 UTC，用时14.73分钟；1,093 HTTP全部success/stop，2,780,036 input +330,107 output tokens。当时按复用36jobs后剩余306jobs/2,097traces分层外推，加30–50%工程余量为1.97–2.28小时，非统计置信区间；该估计没有包含本次恢复及统一v3重跑。详见 [v2 ETA历史报告](reports/pilot_v2_runtime_estimate/RUNTIME_ESTIMATE.md)。下方v1操作记录中的12.77分钟pilot及1.68–1.94小时外推同样仅为历史数据。

最初只估计环境/数据/服务预热为约0.5–2小时（依赖兼容、模型加载、队列等待会影响）。全量共有2,355 agent traces，最多70,650常规agent steps，包含强制final-answer后至多73,005逻辑生成调用；retry HTTP尝试另外记录。这不是实测API调用数。全量时间必须由完成的代表性pilot和实际服务吞吐估计，不能用模拟工具time_cost代替wall time；运行过程中按完成率修正。

## v3当前验收记录

- v2所有在途任务完全退出并完成归档审计后，已应用canonical JSON精确匹配修复，未匹配沿用原有 `best_evaluated_fallback`；NAS提示、Answer选择规则、生成参数和预算未改。
- 当前冻结 `evaluation_recovery_v3`，source `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`。250项检查246通过/4既有环境skip，legacy 16项通过；完整快照见 [manifest.json](provenance/evaluation_recovery_v3/manifest.json)。
- v3静态/fake验收已完成：[validation_v3/README.md](data_runtime/validation_v3/README.md) 包含27 ExpGym fake traces、27 PoolAct fake results/54agents，9个协调graph pending_claims均为0；9HPO oracle、6NAS双环境等价与46份数据SHA256全部通过。fake结果仅验收基础设施，不计入Kimi-K3成绩。
- `smoke_v3` 10:25:28.732722–10:30:26.192139 UTC完成15/15 jobs、45traces；[评分审计](reports/smoke_v3_audit_final/audit.json) 与 [dump审计](reports/smoke_v3_dumps_final/raw_dump_audit.json) 均complete=true。146HTTP全部success/stop，369,468 input +58,960 output tokens；4个响应含解析出的reasoning，不宣称严格无思考。见 [smoke简报](reports/smoke_v3_delivery_final/OVERVIEW.zh.md)。
- `pilot_v3` 于10:30:48.692280–10:43:27.127730 UTC完成36/36 jobs、42 ExpGym +54 PoolAct results/216agents，共258traces，用时12.64分钟。分数与dump双审计complete=true；1,193HTTP全部success/stop，2,889,395 input +317,983 output tokens，21个响应含parsed reasoning/共43,810字符。
- [pilot_v3协议诊断](reports/pilot_v3_protocol_final.md)：169/258 traces为missing_action、201强制final，67个原始响应含K3 native标签；65条trace在最后常规响应含native后终止于missing_action。原始响应与保存trace按原截断规则258/258一致，8000字符cap移除Action候选为0。协议遵循和分数/文件完整性是独立维度，不能把pilot率直接当作全量统计。
- 10:45:49 UTC，v3 pilot的1,595份文件按原字节推广：330份结果/agent/summary JSON、1,193份raw dump、72份执行凭据；[promotion_map.json](runs/full_v3/promotion_map.json) 保存来源与校验和。copy完成不代表全量完成，full resume仍逐项验证兼容性。
- `full_v3` 于10:46:07.804011 UTC正式启动，workers=16，编排器PID1434566由root管理；11:50:46.745903 UTC完成342/342 jobs、0执行失败，即303 ExpGym +513 PoolAct/2052agents全部产出。原启动估计12:25–12:40 UTC作为历史对照保留。所有正式结果保持source `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`，不将v1/v2通过记录复用作v3正式分数。
- 正式[评分审计](reports/full_v3_audit_final/audit.json)、[dump审计](reports/full_v3_dumps_final/raw_dump_audit.json) 均complete=true，[summary.json](reports/full_v3_results_final/summary.json) 通过；HPO、Search、Audit三个独立分区复算全部PASS。正式协议诊断另见 [full_v3_protocol_final.md](reports/full_v3_protocol_final.md)，不混入旧smoke/pilot统计。
- 11:52:02.793–11:52:28.704 UTC完成verified-resume，25.91秒、0新增调用；[比对证明](reports/resume_full_v3.comparison.json) 确认3,039结果JSON +9,068 API JSON，共12,107文件集合与字节不变。原生成progress已单独冻结，resume元数据不代表原推理耗时。
- 11:57:35 UTC仅对本任务精确Slurm作业1203299提交scancel正常收尾，记账End为11:57:36；11:59:32 UTC确认squeue已无该作业且scontrol为CANCELLED，8节点/64 GPU完全释放，无关jobs未动。服务202.6844444444 +bootstrap 16.0177777778 =218.7022222222分配GPU-hours。
- 最终总览、delivery.json与三张规整CSV已生成，`official_full_matrix_complete=true`，阶段7通过。服务端点现为已停止的历史信息；复现须独立重新申请服务，并使用新输出目录，不能覆盖此次已验收结果。读取/审计现有结果无需重新启动模型服务。

## v2验收与恢复记录（完整保留，不计入v3成绩）

- v2当时仅应用答案解析与非法最终配置评分边界修复，冻结快照见 `provenance/evaluation_recovery_v2/`；NAS提示候选未应用，协议/生成参数保持现有设置。
- 完整 `scripts/check.sh`：245项检查，241通过/4skip；日志 `data_runtime/logs/full_check_recovery_v2.log`。新版9HPO验收详见 `data_runtime/validation_v2/README.md`，包括27 ExpGym traces、27 PoolAct results/54 agents、oracle、预算与双环境等价；9个带graph结果的实际 `shared_state.graph.pending_claims` 均为0。
- 09:44 UTC：`smoke_v2` 15/15 jobs、45traces完成，分数与原始dump双审计complete=true，138HTTP全部success/stop；见 [新版smoke简报](reports/smoke_v2_delivery_20260907_0947/OVERVIEW.zh.md)。
- 09:45:07.883–09:59:51.441 UTC：`pilot_v2` 36/36 jobs、42 ExpGym +54 PoolAct results/216agents，共258traces完成；双审计complete=true。1,093HTTP全部success/stop，2,780,036 input +330,107 output tokens，用时14.73分钟。分数仅为代表性pilot，不能替代全量成绩。
- 10:01:51 UTC：新pilot的1,495份文件原字节推广完成：330份结果/agent/summary JSON、1,093份raw dump、72份执行凭据；[promotion_map.json](runs/full_v2/promotion_map.json) 留存来源、目标及校验和。copy完成不等于全量完成，full resume继续验证兼容性。
- 10:01:55.946849 UTC（约10:02）：`full_v2` 正式启动，workers=16，由root管理执行session69464；目标342jobs/2,355traces。当时估计12:00–12:20 UTC运行结束；该窗口因下述恢复暂停适用，不作为当前承诺。
- 10:08:47 UTC：NAS101C/Moderate/naive agent3出现评分不一致。同一响应多个行首Answer使首个答案含后续正文/JSON，substring lookup错误绑定0.9388020833333334，而独立重算为0。10:09向精确PID1396766发送SIGUSR1，仅停止新派发并等待在途任务自然完成；最终排空状态见 [progress.json](runs/full_v2/progress.json)。
- 应用前修复候选仅在离线进程内复放：将lookup改为canonical JSON精确匹配，未匹配沿用原有 `best_evaluated_fallback`。6份raw请求消息全部精确匹配，修前/修后均6calls、5evaluations；修后score_check=true，reported/recomputed均0.9388020833333334。见 [evidence.json](reports/nas101c_moderate_agent3_diagnostic/evidence.json)；该复放没有新增模型调用，也未替换正式成绩或修改源码。
- 下一阶段门禁：所有在途任务完成 → v2输出/dump/执行凭据与成本归档审计 → 应用最小评分匹配修复、完整测试/数据验收并冻结统一v3 → v3 smoke双审计 → v3 pilot双审计与新ETA → v3 full。NAS提示、生成参数、预算保持原样；不混合旧分数，不只择失败重跑。
- 10:23:20.674650 UTC：v2 full完全drained、退出75，最终45completed/1failed/296pending/0running。归档评分审计有效69 ExpGym traces +66 PoolAct results/264agents，另639missing、42unverified_execution，complete=false；这准确记录未完成全量，而非将归档当实验通过。dump审计共2,195HTTP、无在途。
- v1+v2全项目[去重消耗清单](reports/archived_v1_v2_project_usage/project_usage_inventory.json)：6,639个raw位置、4,454个唯一请求、2,185个重复位置；input 11,315,848、output 1,479,744。失败任务、未选中响应及所有已发生请求消耗均纳入，推广副本不重复计数；不把此清单当成绩验收。

## 操作记录（历史归档，非当前状态）

以下按原实验过程保留。旧源码冻结、smoke/pilot通过、推广及ETA记录不代表当前新版已完成；当前状态以上方banner、新版验收记录和对应progress为准。

- 已完整阅读仓库 `.agents/skills/expgym-runner/SKILL.md`、experiment-matrix/runbook references、README和PoolAct文档。
- 已核对远端 main 与本地一致，无需重复clone或覆盖既有目录。
- 分工并行：SGLang 8节点部署、论文协议核对、数据/HPO兼容环境，主agent负责整体验收与评测集成。
- 模型96分片、497,220个tensor的index/header/offset/file-size全部检查通过，1,560,936,091,448字节；未全量hash权重payload，后续以完整SGLang加载另验。
- 已通过适配后的完整 `scripts/check.sh`：229 tests，4 skips（2026-09-07 08:36 UTC）；日志 `data_runtime/logs/full_check_after_adaptation.log`。ParamNet legacy独立验证弥补主Python缺失旧栈。
- 客户端新增可追溯原始请求/响应dump及显式max-tokens/chat-template-kwargs，均纳入配置指纹；针对性66项测试在Python3.11/3.7双环境通过。
- 无成本边界测试发现并修正FakeLLM忽略forced final-answer的问题；仅修改假模型回应，不改变真实后端、预算与计分语义。
- Serving bootstrap job `1203298` 已申请8节点267–274，总64 H200，以4组TP16/EP16副本服务（96 heads不可直接TP64）。完整独立uv环境完成后只释放/重建本任务作业并固定版本；正式结果以最终部署manifest为准。
- 新实验的目标是沿用论文non-extended-reasoning设置；K3 README声明always-thinking，但低层tokenizer有thinking参数。须真实验证后固定生成模式并记录偏离，不能根据参数存在就宣称成功关闭。
- 数据环境最终验收通过：46文件SHA256及完整内容校验；9HPO oracle/预算匹配；6NAS跨环境等价。`data_runtime/fake_hpo_acceptance.json` 记录27 ExpGym、27 PoolAct results/54 agents通过；再次resume的54个结果跳过，108个持久化文件字节不变。
- 评测源码当前冻结：`bee7c08e226a2b23dcfc7aa625c4faaa98ebfa925e8c2cbc30a1e84aebe7e4b8`。最终完整check为230tests、4skips，通过；主/legacy各11HPO tests通过。源码bundle与原diff见 `provenance/evaluation_frozen/`。服务探针若揭示必须的真实后端适配，需更新冻结记录并重验。
- 全量342条子命令已逐条通过仓库原生dry-run；pilot36jobs与full配置/seed/repeats完全一致，验收通过后复用42 ExpGym+54 PoolAct results/216agents，避免额外258条agent轨迹。
- 正式服务作业为 `1203299`，2026-09-07 08:47:36 UTC启动，8节点267–274/64 H200；bootstrap `1203298`已完全释放。新Python环境311包均独立安装、无system/user-site继承，SGLang版本 `0.5.16+pr32477`；上游KV padding修复的340项GPU回归全部通过。服务配置、wheel/hash和冷启动日志见 `serving/`。
- 09:02 UTC 更新：最终评测源码为 `85b569cf2505ff07e6fa7c289b3ea29ec8a35ab3a4b187e8862e7ee4afb9888a`；增加只用于审计的 trace→API client_id 显式关联，完整检查232 tests/4 skips通过。快照见 `provenance/evaluation_api_linkage/`，替代上面的历史冻结记录。
- 服务四副本真实探针均通过；100,174 input tokens 长上下文提取成功，33.622秒，无PAD异常。`chat_template_kwargs={"thinking":false}` 在短探针中无reasoning输出，`enable_thinking=false`对该模型无效。正式请求沿用该关闭参数，但完整smoke另有6/136响应带reasoning_content，不能宣称严格无思考；明确偏离K3文档推荐always-thinking模式和论文统一无扩展思考设定。max_tokens=8192为本次显式输出上限。
- 真实smoke的低分、missing_action或预算停止按原协议保留；仅schema、配置、重算、传输等完整性错误阻止进入下一阶段，不通过改写模型输出提高成绩。
- 真实smoke全部通过：`reports/smoke_audit_20260907_0905/audit.json` 与 `reports/smoke_dumps_20260907_0905/raw_dump_audit.json` 均 complete=true；136 HTTP attempts全部success/stop，无截断。代表性pilot现已启动，所有配置与正式full一致，验收后可复用。
- 完整smoke协议诊断：45traces中30 missing_action、44强制final；20个原始响应含K3 native XTML工具标签，均导致missing_action；45/45 raw→trace按原截断规则一致。6响应有reasoning_content，而provider reasoning_tokens均报0。以上作为模型/协议兼容表现独立披露，不是文件完整性失败；见 `reports/smoke_protocol_diagnostic.md`。不得用smoke的4step/N2失败率代替正式30step/N4统计。
- 真实pilot 09:04:15–09:17:01 UTC 全部36jobs完成：42 ExpGym+54 PoolAct results/216agents，共258traces；两独立审计complete=true，见 `reports/pilot_audit_20260907_0917/` 与 `reports/pilot_dumps_20260907_0917/`。1092 HTTP全部success、1091 stop/1 length，2,317,921 input +307,030 output tokens；1个length为首轮长Thought达到8192上限，保留该有效边界结果。
- ETA按36个system/family/regime分层实测：pilot12.77分钟、有效并发10.81；复用36jobs后剩余306jobs/2097traces，点估计约1.30小时，加30–50%余量为1.68–1.94小时，未含最终离线审计/进一步队列延迟，详见 `reports/runtime_estimate_20260907_0917/`。全量保持workers=16；余量是工程预算范围，不是统计置信区间。
- pilot→full推广先dry-run校验330个required JSON、1092原始API dump及原始执行凭据，保存哈希后才按原字节复制。下一步full --resume逐项再次验证；推广后的 `runs/full/manifest.dry-run.json` 不再改写。
