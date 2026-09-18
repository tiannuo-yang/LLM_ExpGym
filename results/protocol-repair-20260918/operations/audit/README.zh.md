# 独立账本核验凭据

本投影只公开计数、数值汇总、状态及来源 SHA。内部完整审查读取了私有原始请求与 completion receipts；这些原件不在公开包中。

当前凭据覆盖 HPO 97/97、辅助 22/22 个已固定完成槽。请求 SHA、receipt、真实 queue wall、token 与费用均逐条复核。未完成槽不计入固定原件审查。

`INDEPENDENT_REVIEW.json` 的 snapshot SHA 与 `REEXPORT_REVIEW.json` 的 before SHA 相接；after SHA 应对应本包 main/aux 子 manifest。完整最终包要求全部 119 槽完成且独立审查覆盖齐全。

公开包中的离线 verifier 复算公开 CSV/JSON 及哈希闭包；它不能替代持有私有原件时的全文/API 语义审查。原审查脚本身份和原 receipt SHA 保存在投影及顶层 ALLOWLIST 中。
