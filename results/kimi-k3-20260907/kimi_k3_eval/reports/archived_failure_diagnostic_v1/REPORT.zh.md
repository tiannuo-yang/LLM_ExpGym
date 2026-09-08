# 旧 full 的非零退出：补充只读诊断

结论：在 6 份完整非零 runner 日志及其全部 137 份保留 API dump 中，未发现第三个独立失败根因。9 个失败 agent/repeat 都属于已修复的两条路径：7 个 NAS101B 无效最终配置未被正确记零，2 个正文引用 Answer 导致最终答案截取错误。

本次只读旧证据并离线调用本地 evaluator；无新增 LLM 调用，不修改冻结源码、旧结果或 dump。当前验证源码指纹为 55637cee193071b35f06c3356e706d6f652de738a5340d2c4950d5966cf1a0a3。

## 六个任务逐项核对

| 系统 / task / regime | receipt 标签 | raw 数 | 实际日志中的失败项 | 根因及当前覆盖情况 |
|---|---|---:|---|---|
| PoolAct / ParamNet letter / Free | failed | 38 | naive agent 3 | 正文引用 Answer；新行首提取后精确重算 0.7092944375216987，通过 |
| ExpGym / NAS101B / Free | interrupted | 11 | repeats 0、1 | 未知 edge_9…edge_20；新输入分类均重算 0，通过 |
| PoolAct / NAS101B / Free | failed | 11 | naive agent 1 | 未知 edge_9…edge_20；新输入分类重算 0，通过 |
| PoolAct / NAS101B / Moderate | interrupted | 40 | poolact agents 1、2、3 | 未知 edge_9…edge_20；新输入分类均重算 0，通过 |
| ExpGym / NAS101B / Tight | failed | 9 | repeat 0 | 未知 edge_9…edge_20；新输入分类重算 0，通过 |
| PoolAct / NAS201 cifar100 / Moderate | interrupted | 28 | naive agent 2 | 正文引用 Answer；新行首提取后精确重算 0.7129666666666667，通过 |

三个 interrupted 是保留下来的 harness 状态标签，不能据此解释成纯外部信号中断：这三份日志实际都已报告 score-check 错误，且 returncode 为 1。本诊断不改写这些 receipt，只区分调度标签与程序错误证据。

## 复核边界

- 137/137 raw 均为 success，finish_reason 均为 stop；本范围无失败 HTTP、重试、未完成响应或 provider length 截断。请求历史中的工具异常只有已知 NAS101B 未知参数，无独立的数据读取或后端异常线索。
- 七个实际 NAS101B final 均提取自各自最后的原始响应。当前真实 NAS101B config space + score_result 离线重算均通过、结果为 0；用 guard 验证每个无效配置 backend 调用均为 0。它们是无效输入评分分类检查，不是把旧失败轨迹改成正式成绩。
- 两个 Answer 误提取案例均完成旧/新解析与评分的离线对照，保留 evaluator 原始非零分。只升级 InvalidConfiguration 而保留旧解析仍会失败，因为错误截取的大段文本通过旧子串匹配取得非零历史分，不能合法改写为零。
- ParamNet 日志中的 pandas 提示不是本次根因：固定 legacy evaluator 对该 agent 的三个实际合法配置均能正常重算，最终精确分数见独立报告。
- NAS101B Moderate 另有一条 13,453 字符响应触发原有 8,000 字符 loop 截断；它来自 poolact agent 0，日志失败列表是 agents 1、2、3。原始 dump 为 f72ec03d0ca54793998e231a31bbd7e8.json。这是已知输出/协议行为边界，不是这次新增的独立评分失败。

上述结论仅覆盖这些已发生失败的全部保留证据，不保证未来不同模型回答不会暴露新边界。新 full 仍应维持原有逐结果重评分及双审计，不可关闭失败检查。

## 查验入口

- [完整证据 JSON](evidence.json)：6 份完整 attempt 日志、逐 raw 路径/SHA256、所有 client session 末次内容、7 个 NAS101B 离线检查。
- [可复现只读检查脚本](check_evidence.py)：从原 manifest / 旧审计定位目标，核对 receipt 与日志 SHA，再扫描全部 raw。
- [ParamNet letter 独立旧/新复核](../paramnet_letter_free_agent3_review.zh.md)。
- [NAS201 cifar100 独立旧/新复核](../nas201_cifar100_moderate_agent2_review.zh.md)。
- [原归档失败审计](../archived_full_v1_audit_20260907_0936/execution_failures.json)。

复现扫描：

    LLM_ExpGym/.venv/bin/python -W ignore kimi_k3_eval/reports/archived_failure_diagnostic_v1/check_evidence.py
