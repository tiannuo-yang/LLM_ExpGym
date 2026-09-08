# 正式 v3 结果解读

本页解读已通过双审计及三个分区独立复算的 [正式汇总](full_v3_results_final/REPORT.zh.md)。完整宽表和逐格来源见 [最终总览](final/OVERVIEW.zh.md)，逐任务与逐 agent 数值见 [task_metrics.csv](full_v3_results_final/task_metrics.csv) 和 [agents.csv](full_v3_results_final/agents.csv)。这是 **Custom study**：本地 Kimi-K3 在仓库原始文本 ReAct 协议下的结果，不是原论文逐字节复现，也不代表 K3 原生工具调用／推荐思考模式下的最佳能力。

## 主要观察

1. **预算收紧对 Search 和 NAS101 的影响较明显，但并非所有维度单调下降。** ExpGym whois F1 在 Free/Moderate/Tight 为 27.94/30.64/11.22%，whatis 为 10.59/5.88/0.00%；NAS101 家族 Gap 为 82.02/76.90/51.22%。NAS201 则为 85.64/88.03/85.45%。这些是本次固定样本的描述性结果，不是因果效应或统计显著性结论。Gap 是相对 oracle 随机均值的改进比例，越高越好，不是剩余误差。
2. **PoolAct 没有在论文子集上普遍胜过 naive。** Moderate/Tight 的 whois 多数票 F1：poolact 为 29.88/22.59%，naive 为 31.26/25.45%；Audit LA：poolact 为 82.81/82.81%，naive 为 83.26/84.16%；NAS101:A BoN Gap：poolact 为 98.50/98.76%，naive 为 99.57/99.26%。扩展矩阵也有不同表现：Free whois 的 poolact 多数票为 36.79%，高于 naive 的 33.70%；Tight ParamNet BoN 为 95.72%，高于 naive 的 86.54%。不能把 NAS101 家族均值和论文仅 NAS101:A 的单任务表混为一谈，也不能由这些单次 N=4 pool 宣称普遍排名。
3. **Audit 标签与证据定位表现不同。** ExpGym Free/Moderate/Tight 的 LA 为 84.62/84.77/83.41%，EA 为 55.81/55.51/54.15%。EA 按证据集合精确匹配独立计算，不要求标签同时正确；它不是“标签且证据均正确率”。独立的“全部 NotMentioned＋空证据”基线 LA=EA=45.70%，只是 [离线基线](audit_label_baseline/README.zh.md)，不是新增 K3 实验；不能用它解释为本次约84%的 LA 仅来自全负类预测。
4. **协议兼容是解释成绩的重要限制。** 2,355 条轨迹中，1,829 条（77.66%）终止于 missing_action，1,982 次触发强制 final。PoolAct 的终止原因来自保存的强制回答提示推断，未补写原结果字段；ExpGym 为序列化原字段。967 个原始响应含 K3 native 工具标签，962 条轨迹在最后常规响应出现 native 标签后终止于 missing_action；这种先后共现不是单独的因果证明。未把 native 标签自动转成文本 Action，也未事后改写模型回答。详见 [全量协议诊断](full_v3_protocol_final.md)。

## 需要与分数一起保留的边界

- 请求固定 `thinking=false`、`max_tokens=8192`；9,068 次正式请求中有170个响应包含服务解析的 `reasoning_content`，共631,606字符。provider reasoning token counter 均为0，但该计数受请求参数门控，不能据此宣称严格无思考；HTTP JSON 不能区分实际 think-open 与孤立 close 被 parser 分段。客户端下一轮只保留 content，另与 K3 文档的推荐多轮用法不同。见 [服务诊断](../serving/REASONING_MODE_DIAGNOSTIC.md)。
- API `finish_reason=length` 有4次；仓库原有的常规响应 **8000字符** cap 是另一个限制，不能与8192 token cap混淆。71个常规响应超过字符上限；对22个 Action 解析候选逐例复核，18个明确工具请求可被当前 parser 识别且通过静态参数检查（4行首、14行内），另4个是引用误候选。18个请求文本在截断后丢失，不代表工具原本一定执行成功、预算足够或最终得分会提升。原 cap 未改，见 [逐例证据](full_v3_cap_review/README.zh.md)。
- NAS101 B/C 保留原 paper/repo 的 A 式提示，未应用候选提示补丁；实际 B 是9个 categorical selectors，C 是21个优先级的 top-k 编码。B 的45个 agent层结果中有28个真实零分，但不能把这些零分全部因果归于提示差异。全 HPO 的33个 raw 零分与另外2个因低于 oracle mean 而 Gap 截为0的结果分开记录，见 [HPO 独立复核](full_v3_hpo_independent_review/REPORT.zh.md)。
- runner 的 `prompt_cache=disabled` 仅关闭显式 cache key；服务自动 radix/prefix cache 仍启用且配置未变。API 未报告缓存 token，因此缓存命中率未知，不是0；输入 token 数也不是未缓存 prefill 计算量。
- 论文主设置和仓库完整主矩阵均已覆盖；历史 PoolAct outer-repeat 数量、locked/prelock 协议及 K3 新提供商差异见 [论文对齐说明](../protocol/PAPER_ALIGNMENT.md)。额外 N=8 scaling、lock ablation、原生思考模式实验不属于本次承诺的主矩阵。

## 时间、消耗与恢复

| 阶段 | UTC 区间 | 实测墙钟 |
|---|---|---:|
| v3 smoke | 10:25:28–10:30:26 | 4.96分钟 |
| v3 pilot | 10:30:48–10:43:27 | 12.64分钟 |
| 正式 full 主运行 | 10:46:07–11:50:46 | 64.65分钟 |
| 全342任务 verified-resume | 11:52:02–11:52:28 | 25.91秒 |

[原始主运行快照](full_v3_generation_completed/progress.json) 与 [恢复验证](resume_full_v3.comparison.json) 分别留存。pilot中36个兼容任务原字节推广，计入正式结果和原始成本；恢复验证没有新增评测请求，3,039份结果JSON和9,068份dump的集合与字节全部不变。主运行前外推点估计74.78分钟，含30–50%工程余量为97.21–112.16分钟，实际64.65分钟；该余量从来不是统计置信区间，且未包含最终审计整理。

正式结果共9,068次成功HTTP请求，输入17,977,502、输出2,434,522 tokens，无重试。另有两轮评分边界修复和统一重跑：旧 v1/v2 数据及失败证据保留，不混入正式v3分数。覆盖九份阶段manifest的 [项目消耗账单](project_usage_final/README.zh.md) 为13,668次独立评测请求，输入29,662,818、输出3,973,226 tokens；3,378个推广副本不重复计数。账单含失败任务与未被正式结果选中的评测消耗，但不含服务验收探针、后台health请求或其他manifest之外流量。

Slurm GPU-hours 按整个 allocation 的分配GPU数与记账墙钟计算，包含加载、验证、调试和空闲，不能由上述 token 或模拟工具费用换算。最终记账与资源释放状态见 [最终总览](final/OVERVIEW.zh.md)。
