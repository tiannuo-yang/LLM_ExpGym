# HPO：resume 后最终独立核对 PASS

已从 resume 后相同原始结果重新计算，严格绑定最终 manifest `7016deb285696ff95c0aa970088c0580d0daf60cb0c6695ce8515e0fe85df854`，并与 [正式 summary](../full_v3_results_final/summary.json)（SHA256 `36e5badbd2b5e95a6042dead41703dc44146222260af05a29acc13e7ecf6e083`）核对通过。

比较覆盖 63 个家族值、189 个任务值、405 个 agent 的 raw／Gap／SHA、12 个论文 NAS101 A 值；最大数值差 1.4210854715202004e-14，低于 1e-10，文件 SHA 完全一致。

[最终独立证据](independent_post_resume_final.json) SHA256：`d0d92f9b0afec0815031b57b3b6d6527f62f13c8d2462f7b3e57986fe28d8958`。

旧 [independent.json](independent.json) 和 [首次 HPO 报告](REPORT.zh.md) 原字节保留。旧 manifest SHA256 为 `5b64a55da602c6442ae0fc83d737a3df6f23a7f8b39f60d66c190232ea95ec93`，与最终 manifest 不同是 resume 更新元数据的结果；没有绕过 SHA 绑定。重新逐路径比较确认旧／新 405 条 trace/agent、81 个 PoolAct result SHA 全部相同，189 个 task 和 63 个 family 指标也完全相同。因此首次表格及零分／提示诊断仍适用于同一批未变的原始结果；其中“等待 summary”的文字只表示首次快照时的历史状态，本文件记录后续完成的核对。

同期 Audit 独立 gold/raw 复算也通过，统一 [PASS 回执](../full_v3_audit_independent_review/PASS_FINAL.json)。没有新增 LLM 调用或修改正式产物。
