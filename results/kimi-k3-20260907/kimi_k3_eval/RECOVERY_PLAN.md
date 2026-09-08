# 2026-09-07 全量早期评分/提示边界修复与重验

> 最终状态（2026-09-07 UTC）：恢复、正式评测与交付全部通过。342/342 jobs、0执行失败，303 ExpGym +513 PoolAct/2052agents双审计及独立复算PASS；生成64.65分钟，零调用resume 25.91秒、12,107个文件集合/字节不变。最终总览和CSV已生成；11:59:32 UTC确认本任务1203299已CANCELLED并退出队列，8节点/64 GPU完全释放，无关作业未动。

旧正式源码指纹：`85b569cf2505ff07e6fa7c289b3ea29ec8a35ab3a4b187e8862e7ee4afb9888a`，完整快照在 `provenance/evaluation_api_linkage/`。

## v3最终结果验收与交付（全部通过）

- 正式结果：[summary.json](reports/full_v3_results_final/summary.json)；[评分审计](reports/full_v3_audit_final/audit.json) 与 [dump审计](reports/full_v3_dumps_final/raw_dump_audit.json) 均complete=true，HPO/Search/Audit三个独立分区复算全部PASS。[最终总览](reports/final/OVERVIEW.zh.md)、[交付清单](reports/final/delivery.json) 和三张规整CSV已生成，`official_full_matrix_complete=true`；局限与结论见 [结果解读](reports/full_v3_interpretation.zh.md)。
- 正式生成10:46:07.804011–11:50:46.745903 UTC，用时3,878.9419秒/64.65分钟，342/342 jobs、0执行失败；原始进度与manifest冻结于 [full_v3_generation_completed/](reports/full_v3_generation_completed/)。
- 11:52:02.793–11:52:28.704 UTC的verified-resume用时25.91秒、0新调用；[comparison.json](reports/resume_full_v3.comparison.json) 证明3,039结果JSON +9,068 API JSON，共12,107文件集合与字节完全不变。当前 `runs/full_v3/progress.json` 是resume记录，不可误用为生成耗时。
- [最终项目用量](reports/project_usage_final/README.zh.md) 范围是v1/v2/v3各smoke/pilot/full九份manifest：17,046个raw位置、13,668唯一HTTP、3,378个推广副本不重计；input 29,662,818、output 3,973,226。归档失败任务及未选中响应全部纳入，但不含服务探针等非manifest流量，也不等于GPU-hours。
- 11:57:35 UTC root仅取消本任务精确Slurm作业1203299，记账End=11:57:36；11:59:32 UTC确认队列已无该作业且JobState=CANCELLED，8节点/64 GPU完全释放，无关jobs未动。最终以 [after_cleanup/slurm_receipt.json](serving/reports/final_accounting_20260907_after_cleanup/slurm_receipt.json) 与 [release_confirmation.json](serving/reports/final_accounting_20260907_after_cleanup/release_confirmation.json) 为凭据。
- 分配GPU-hours：服务202.6844444444、bootstrap 16.0177777778、总218.7022222222，含加载/验证/推理/空闲，非GPU利用率。服务地址现仅是已停止的历史配置；重跑需重新申请服务并使用独立新输出目录，不覆盖正式结果，现有结果的离线查验无需启动服务。

- 当前源码 `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`，冻结快照 [evaluation_recovery_v3/manifest.json](provenance/evaluation_recovery_v3/manifest.json)。canonical JSON精确匹配补丁已在v2排空且归档审计完成后应用；250项检查246通过/4既有环境skip，legacy 16项通过。
- [validation_v3/README.md](data_runtime/validation_v3/README.md) 的静态/fake验收已完成：27 ExpGym fake traces、27 PoolAct fake results/54agents，9HPO oracle/6NAS双环境等价、46份数据SHA256均通过；所有结果匹配冻结v3，fake不计作真实模型成绩。
- `smoke_v3` 10:25:28.732722–10:30:26.192139 UTC完成15/15 jobs、45traces；[评分审计](reports/smoke_v3_audit_final/audit.json) 与 [dump审计](reports/smoke_v3_dumps_final/raw_dump_audit.json) 均complete=true。146HTTP全部success/stop，369,468 input +58,960 output tokens；4个响应含解析出的reasoning。验收简报见 [OVERVIEW.zh.md](reports/smoke_v3_delivery_final/OVERVIEW.zh.md)，不能以smoke代替全量成绩或宣称严格无思考。
- `pilot_v3` 于10:30:48.692280–10:43:27.127730 UTC完成36/36 jobs、258traces，用时12.64分钟；[评分审计](reports/pilot_v3_audit_final/audit.json) 与 [dump审计](reports/pilot_v3_dumps_final/raw_dump_audit.json) 均complete=true。1,193HTTP全部success/stop，2,889,395 input +317,983 output tokens，21个响应含parsed reasoning/共43,810字符；[pilot简报](reports/pilot_v3_delivery_final/OVERVIEW.zh.md) 不替代全量成绩。
- [pilot协议诊断](reports/pilot_v3_protocol_final.md) 为169/258 missing_action、201强制final、67个原始响应含native标签；65条trace在最后常规响应含native后终止于missing_action。8000字符cap移除Action候选为0；这些协议兼容表现与文件完整性验收分开披露，不能宣称严格无思考或全部交互成功。
- [启动前ETA历史记录](reports/pilot_v3_runtime_estimate/RUNTIME_ESTIMATE.md)：当时复用36个pilot jobs后剩余306jobs/2,097traces，点估计约1.25小时，含30–50%工程余量为1.62–1.87小时，非统计置信区间、不含最终离线审计。实际正式生成64.65分钟、11:50:46 UTC完成，早于当时12:25–12:40 UTC窗口；估计仅保留对照，不再作完成承诺。
- 10:45:49 UTC完成1,595份原字节文件推广，330份结果/agent/summary JSON +1,193份dump +72份执行凭据，见 [promotion_map.json](runs/full_v3/promotion_map.json)。推广不等于全量完成；full resume验证兼容结果后跳过，不重复调用这些v3 pilot条目。
- `full_v3` 于10:46:07.804011 UTC正式启动，workers=16，编排器PID1434566由root管理；11:50:46.745903 UTC完成303 ExpGym +513 PoolAct/2052agents，共342jobs/2355traces。原始生成状态见 [冻结progress](reports/full_v3_generation_completed/progress.json)，不要与后续resume进度混用。
- v1/v2所有已验收smoke/pilot结果、full部分结果、dump、执行凭据和成本原位保留，不复用于v3正式分数、不只择失败重跑。此前12:00–12:20 UTC ETA窗口不再承诺。

## v2评分问题与恢复处置（排空/归档/修复已完成）

- 根因：同一原始响应含多个行首 `Answer:`，当前first-answer解析结果包含后续正文及JSON；`_lookup_answer_metrics` 的substring匹配把已评估配置的0.9388020833333334绑定给整段非法答案，独立重算却为0。这不是新数据缺失或服务错误。
- 修复方案（现已应用于v3）：仅改为canonical JSON精确匹配；未匹配时回退仓库原有 `best_evaluated_fallback`，不改Answer选择规则、模型输出、NAS提示、工具预算或生成参数。
- 应用前[离线证据](reports/nas101c_moderate_agent3_diagnostic/evidence.json)：精确复放同6份raw，所有请求消息一致；修前/修后同为6calls、5evaluations，修后score_check=true，reported/recomputed均0.9388020833333334。该复放只在单个离线进程内替换lookup，当时未改源码、不新增API、不充当正式成绩。
- 10:09 UTC对已精确核对的full_v2编排器PID1396766发送SIGUSR1，仅停止新任务派发；在途任务保留完整请求并自然完成。此处的SIGUSR1排空与下方v1历史SIGSTOP处置不同，不应混用。
- 排空期间遵守不改源码门禁：在途runner保存时仍计算指纹，保持 `evaluation_recovery_v2` / `55637cee193071b35f06c3356e706d6f652de738a5340d2c4950d5966cf1a0a3` 不变。10:23:20.674650 UTC完全drained、退出75，最终45completed/1failed/296pending/0running，之后才归档审计和应用v3补丁。
- [v2归档评分审计](reports/archived_full_v2_audit_20260907_1023/audit.json)：69 ExpGym traces +66 PoolAct results/264agents有效，639missing、42unverified_execution，complete=false；归档成功不等于全量实验完成。[v2 dump审计](reports/archived_full_v2_dumps_20260907_1023/raw_dump_audit.json)：2,195 HTTP、无在途。全部原始结果、失败记录和执行凭据保留，缺失不补0。
- [v1+v2全项目消耗清单](reports/archived_v1_v2_project_usage/project_usage_inventory.json)：6,639个raw文件位置去重后4,454个唯一请求（2,185个重复位置），input 11,315,848、output 1,479,744，包含失败任务和未选中响应的实际消耗；推广副本不重复计数。该账单不是成绩验收。
- 全部验收已完成：v2排空与归档审计 → 应用最小评分匹配修复并冻结统一v3 → v3静态/fake及真实smoke双审计 → v3 pilot双审计与ETA → 原字节推广 → v3 full双审计/独立复算 → 零调用resume → 最终交付与服务资源释放。全部v3正式矩阵统一source，不混入v1/v2已完成成绩；所有旧记录仍原位保留。

## v1已确认问题（历史记录）

1. Letter/Free/naive agent3：Thought引用 `Answer: <your answer>` 被当作答案起点，真正行首JSON在后面。runtime子串匹配得到0.7092944375216987，但完整污染字符串不能JSON重算；纯行首答案重算分数完全一致。
2. NAS101-B/Free/naive agent1：提交了A型edge_0…edge_20；B实际只接受9个edge-slot，值是0…20的类别。未知参数异常使整个PoolAct strategy未保存，而不是把无效模型答案明确评分为0。
3. NAS101 A/B/C共享A型二进制edge提示。B实际是9个categorical edge IDs；C是21个连续优先级加num_edges。原测试却明确固定公共提示以沿用paper constraint。提示修订会改变实验输入，因此已询问用户；**若无补充，主表保留原提示并披露矛盾**，修订版仅作为未应用候选 `patches/nas101_hints_fix.patch` 留存，不混入正式分数。

## 旧版处置记录（已完成，保留操作时序）

以下暂停、排空与恢复步骤为旧版本历史记录，不是当前待执行指令；PID1327749对应的旧编排器已退出。当前新版状态见上方banner与下方验收记录。

- SGLang作业1203299保持不变；权重/服务/生成参数未调整。
- 2026-09-07约09:25 UTC，对已精确验证的full编排器PID **1327749** 发送SIGSTOP，仅暂停派发线程。已启动的16个runner子进程继续完成，保留完整API响应；未杀死在途请求。
- 不可在这些子进程完成前修改LLM_ExpGym源码：原runner在保存时计算source hash。
- 09:36 UTC全部直接子进程已为Z、原始dump无in_progress，按TERM→CONT顺序使编排器正常写盘退出130。最终旧进度：40completed、3failed、3interrupted、296未派发；这里部分interrupted为已退出非零runner在stop标志下的状态分类，实际退出码/错误日志仍保留。每任务wall time包含编排器暂停后的收割等待，旧API独立wall time与Slurm真实allocation仍可精确核查。
- 补丁先保存在 `patches/`，使用独立临时copy测试。待PID1327749的全部直接子进程为Z/已退出，再对该PID先发送SIGTERM（排队）、随后SIGCONT，使原handler设置stop，收割已结束子进程并完整写入status，不再派发新任务。不得SIGCONT后直接让旧全量继续。
- 旧 `runs/full`, `dumps/full`, `logs/full`、pilot、smoke及既有审计均保留，不覆盖，不重写原sourcehash；旧full不计作正式完成。
- 选择统一新版本重新执行正式矩阵，不按失败结果挑选重试、不混合旧/新协议分数。新目录建议 `runs/smoke_v2`, `runs/pilot_v2`, `runs/full_v2`，通过harness `--output-dir`设定，关联logs/dumps使用独立namespace。
- 应用最小补丁，完整tests/数据校验/9HPO非法输入边界，保存新source快照。再做新真实smoke和代表性pilot/ETA，审计后只推广新pilot到新full。
- 最终记录旧实验消耗与修复/重验开销；此前1.68–1.94小时ETA仅适用于旧pilot外推，不能当新的完成承诺。

## v2已应用与冻结（历史快照，现已归档）

只应用 `answer_parser_fix.patch` 和 `invalid_final_score_fix.patch`；未应用NAS提示补丁。新源码指纹：`55637cee193071b35f06c3356e706d6f652de738a5340d2c4950d5966cf1a0a3`，快照 `provenance/evaluation_recovery_v2/`。

`scripts/check.sh` 跑245项，241通过/4既有环境skip，两个fake闭环均通过；legacy新增11项边界通过；完整数据check通过。日志见 `data_runtime/logs/full_check_recovery_v2.log`、`legacy_invalid_final_v2.log`、`data_check_recovery_v2.log`。

v2 smoke和pilot已验收记录保留；`runs/full_v2/` 启动后因新增评分问题停止新派发，10:23:20已完全排空并归档，原规划见 [manifest.dry-run.json](runs/full_v2/manifest.dry-run.json)，342jobs/2355traces，workers16。v2 dump namespace由manifest明确指定，例如full为 `dumps/full-full_v2-e0565217/`，不要误扫旧 `dumps/full/`；这些记录不混入v3正式成绩。

09:44 UTC 新smoke全部15jobs/45traces完成，301.37秒；分数与原始dump双审计complete=true，138次HTTP全部success/stop，327,825 input +58,135 output tokens。审计见 [评分审计](reports/smoke_v2_audit_20260907_0944/audit.json)、[dump审计](reports/smoke_v2_dumps_20260907_0944/raw_dump_audit.json)，简报见 [smoke_v2 OVERVIEW](reports/smoke_v2_delivery_20260907_0947/OVERVIEW.zh.md)。新9HPO fake与跨环境oracle完整验收见 [validation_v2/README.md](data_runtime/validation_v2/README.md)。

旧6个非零任务、137份raw的完整离线复查未发现第三类根因：7个NAS101B无效final均由新输入验证零分规则覆盖，另2个final由Answer行首解析修复恢复原分数。证据见 `reports/archived_failure_diagnostic_v1/REPORT.zh.md`。新smoke另观察到原仓库8000字符cap移除1个合法Action候选，导致missing_action；这是保留的原协议限制，不改变冻结源码，见 `reports/smoke_v2_cap_review_20260907_0944.md`。

## v2 pilot验收、推广与全量执行记录（保留成本）

- `pilot_v2` 固定30步/N=4、workers16，于09:45:07.883–09:59:51.441 UTC完成，用时14.73分钟；36/36 jobs、42 ExpGym traces +54 PoolAct results/216agents，共258traces。
- 分数与原始dump双审计complete=true：[pilot_v2_audit_final/audit.json](reports/pilot_v2_audit_final/audit.json)、[pilot_v2_dumps_final/raw_dump_audit.json](reports/pilot_v2_dumps_final/raw_dump_audit.json)。1,093HTTP全部success/stop，2,780,036 input +330,107 output tokens；[pilot简报](reports/pilot_v2_delivery_final/OVERVIEW.zh.md) 仅代表pilot，不是正式全量成绩。
- [v2 ETA历史报告](reports/pilot_v2_runtime_estimate/RUNTIME_ESTIMATE.md) 当时按已验收pilot分层外推；复用36jobs后剩余306jobs/2,097traces，包含30–50%工程余量约1.97–2.28小时。这不是统计置信区间，也不含最终离线审计、本次恢复或统一v3重跑时间；目前暂停适用，旧1.68–1.94小时外推也仅历史留存。
- 10:01:51 UTC推广完成：1,495个原字节文件，包括330份结果/agent/summary JSON、1,093份原始API dump和72份执行凭据；来源及校验和见 [promotion_map.json](runs/full_v2/promotion_map.json)。推广清单的copy状态不代表正式全量已完成；新full使用resume逐项验证后跳过兼容结果。
- `full_v2` 于10:01:55.946849 UTC（约10:02）启动，workers=16，由root管理执行session69464，10:23:20完全排空退出75。原目标303 ExpGym traces +513 PoolAct results/2,052 agents，共342jobs/2,355traces；当时12:00–12:20 UTC运行结束的估计因10:08:47新增评分问题及统一v3重跑计划暂停适用。最终状态见 [full_v2/progress.json](runs/full_v2/progress.json)，全部已产出记录与消耗保留。

## 新版验收原则

- Answer仅接受规范化后的行首标签，保留正常Markdown和多行答案。
- 仅明确模型输入验证失败记为有效0分；数据、运行环境、工具内部错误仍失败，不得把`(None, cost)`或缺数据默认为0。
- 保持textual ReAct，不自动转译K3 native tags，不调整reasoning、采样、预算或token上限。
- 默认主表不改B/C提示；若用户明确选择修订，则使用已核对实际编码、无最优配置/答案的补丁，并记录为额外paper-prompt偏离。
- 正式目标仍为303 ExpGym +513 PoolAct/2052 agents；缺失不补0，实际模型无效配置可以有已验证0分。
