# GLM 正式原始树：最小 delivery operator 绑定候选

[operator.py](operator.py) SHA
`2124e9929f29531d48960ece983eea10d493660244bfc1dc8938696ebfd79d3d`，21,547 B。
这是候选，不是实际交付 GO；尚未 import / 执行本 operator，未读正在运行的 GLM scanner 输出，未做真实 scan metadata gate / pack / restore。

## 唯一生产差异

以冻结 K3 delivery v2 SHA
`cc1b646b46d258d3071e9fe94bfe849683500beafeca68bca7fbbc56c14ccb14`
为基础。见 [PRODUCTION_DIFF.patch](PRODUCTION_DIFF.patch)。

纯 AST 只有 23 个常量差异、0 个结构或控制流差异；另有一处注释 33 → 36：

- 已由实际封存/组装确定的 36 batches / 70,520 files / 3,242,213,793 B。
- 三项 SCOPE 固定到新 GLM inventory / index / seal 和实际 SHA。
- 原 execution/score 两个 true：scan receipt 和 seal 均须满足，最终原样记录，不将其解释为全项目完成。
- schema / action / summary / 日志标签改为本 GLM 身份。
- 不改循环、异常处理、等待、caps、metadata 映射、完整 union、source/restore 检查。

`natural_wait` 与 `safe_invoke` 原始函数文字逐字相同；`identity` / `collect` 也逐字相同。`recheck` 仅注释数字变化，AST 完全相同。原单批 helper 不调用历史 preflight/main，只重绑定 ROOT / STOP / invoke 后使用 batch_run；旧历史总量不参与本次新执行。

## 验证与准确边界

[STATIC_REUSE_RECEIPT.json](STATIC_REUSE_RECEIPT.json) 保存完整差异、工具 refs、原 CPU 回执/log refs 与实际静态检查。

- 修正后的静态检查实际 exit 0 / `a2494e`；新旧 source、7 个原 helper/tool 和原 CPU source/log pins 全部匹配。
- 原 K3 v2 的 11 项合成测试曾分别在 Python 3.10 / 3.11 通过；本候选核了原回执与日志，但**没有重跑这些测试，也没有声称新的 GLM 真数据已通过**。
- 独立 peer `/root/glm_delivery_reuse/archive_contract` 只读核同一新 SHA，确认 23 常量 / 0 结构差异、关键等待函数字节相同、7 个原工具 pins 不变。
- 首次静态检查 `a5d09b` exit 1：诊断错误地要求包含已允许注释变化的 recheck 函数也逐字相同。原失败记录保留；生产源码不改，诊断改为核 recheck AST 完全相同，关键等待函数继续逐字核对。
- 未改源候选/实验原件，未读取原 payload/key，未生成正式 delivery GO 或扫描批准，未执行新 CLI、合成 pack/restore、Git、网络或模型调用。

旧 K3 CPU 只覆盖其原 false/false fixture；当前 true/true 的静态绑定已核，但不能冒称已有本新入口的实际 metadata gate。真实完整 scan refs 由 ROOT 在 scanner 退出后提供，再独立授权后续检查。保留这一边界，不伪造 PREPARED / SCAN_RECEIPT pin。

## 后续精确 GO 契约

[BINDINGS_PENDING.json](BINDINGS_PENDING.json) 记录已知固定原件 refs 和尚未取得的实际 scan refs。其中 null 不是 ref，也不是批准。

GO 顶层仍恰 20 字段，结构同原 v2，只替以下绑定：

- schema_version = `root-glm-original-delivery-go-v1`
- action = `pack_and_local_restore_exact_36_batches`
- driver_sha256 = 本新 SHA
- expected_totals = `{"batch_count":36,"file_count":70520,"original_bytes":3242213793}`
- inventory_ref / index_ref / seal_ref = 本源码 SCOPE，path/SHA 精确相等（可带 bytes）。
- scan_go_ref / prepared_ref / scan_receipt_ref = ROOT 提供的实际新扫描 refs，不复用 K3 或历史 refs。
- output_dir = ROOT 选定的不存在、父目录已存在的规范绝对路径，不与 input/tool/key 重叠。
- 其余保留 issuer=ROOT、approved=true、workspace、python=/usr/bin/python3、恰 3 条 secret_files、精确顺序的 5 个 tool_refs、max_parallel_batches=1、publication_authorized=false、network_authorized=false。

未来 CLI 保持：

```bash
/usr/bin/python3 -B publication/glm_formal_original_delivery_candidate_v1/operator.py \
  --go ABS_NEW_ROOT_GO --go-sha256 EXTERNAL_GO_SHA \
  --secret-file ABS_KEY_PATH_1 --secret-file ABS_KEY_PATH_2 --secret-file ABS_KEY_PATH_3
```

这只是接口说明，未执行。原 48 MiB compressed / 256 MiB expanded / 100 MiB original / 256 files-per-shard 与串行 pack → full local restore → 全 source/restore/COMPLETE 后验保持。pack 和 restore 用原 /usr/bin/python3 -B CLI；失败停止后续新批、保留真实退出和现场，不自动重试。闭合未知时 local_workers=null，不硬写 0。

actual GLM scanner session 由 ROOT 独占跟踪；本候选不读取其活跃 manifest，不把 scanner 启动当作扫描通过。等待 ROOT 的已闭合 refs 及独立下一步授权。当前候选停写。
