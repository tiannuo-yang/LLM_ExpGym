# K3：33 raw + 1 controls 的薄合集 assembler 候选

候选仅准备代码和小 synthetic；未读取当前 raw pack 输出、真实 INDEX/原件/key，未运行实际 assemble/pack/restore、Git、网络或模型。raw/controls 的最终 operator/ROOT proof 尚未成为本候选输入；真实 refs 由 ROOT 待两组闭合后填，不自动发现。旧 32 包合集不读、不复制、不重打包。

固定总量：34 包 / 65,105 原文件 / 1,521,531,633 B。其中 raw 为 33 个 `batch-000001`…`batch-000033`，前 32 批各 2,000 文件、末批 188 文件，总 64,188 / 1,268,512,973 B；controls 为单包 917 / 253,018,660 B。分类分别为 `original-node-failure`、`controls`。原 execution/score 两个 false 保留，交付成功不表示科学运行成功。

## 复用范围

`PRODUCTION_DIFF.patch` 与原 `collection_assembly_candidate_v1/assemble.py` 对比。只替换旧 30+2 selection、输入 roots/counts/proof 绑定及新 GO；原逐包 INDEX/COMPLETE、member pages、全原件 union、精确目录集合、原字节复制和后验、5 个工具拷贝、原 wrapper.preflight、RELEASE_FILES/ASSEMBLY_RECEIPT 布局保持。未修改 pack/restore/scanner 或 `whole-file-collection-v1` 协议。

输入包仍是 `BUNDLE/COMPLETE.json` + `BUNDLE/payload/{INDEX.json,SOURCE_SCAN.json,indexes/*,shards/*}`。外层 proof、README、许可证和发布回执不能塞进这些精确包根。输出仍是 `FRESH_OUTER/payload/collection/INDEX.json`、34 个完整包、5 个原工具，以及 RELEASE_FILES/ASSEMBLY_RECEIPT；外层 ROOT 材料独立留在 `FRESH_OUTER/`。保留原相对路径/bytes/SHA/空文件，不承诺 POSIX owner/mode/mtime。

## 外部 ROOT selection：先明确证明语义，不猜未来字段

selection JSON 恰字段：`schema='root-k3-collection-selection-v1'`、`issuer='ROOT'`、`original_execution_complete=false`、`original_score_complete=false`、固定 `bundle_count/file_count/original_bytes` 和 `bundles` 34 行。

每行恰：

| 字段 | 契约 |
| --- | --- |
| bundle_id / category | 上述固定 ID 与分类，不接受额外历史 scope |
| bundle_root | 显式绝对目录；raw 必须是 `publication/k3_formal_original_local_delivery_v2/batches/<id>/bundle`；controls 根由 ROOT 明确填入 |
| index_ref / complete_ref | 恰 `{path,bytes,sha256}`，路径必须分别为本 root 的 `payload/INDEX.json`、`COMPLETE.json` |
| file_count / original_bytes | 本包原件总量；与实际 member union 和原 INDEX 再核；各分类小计/全量总计固定 |
| operator_ref / local_proof_ref | 原 operator 执行回执与 ROOT 独立 local proof 的外部 `{path,bytes,sha256}`；可以多行共用同一完整证明原件，不递归其中路径 |
| local_verification | 恰 `pack_exit_code=0`、`restore_exit_code=0`、`complete_original_and_restored_path_bytes_sha_match=true`、`all_started_children_reaped=true` |

重要边界：`local_verification` 是 **ROOT 在签 selection 前逐条审核的规范化投影**，不是 assembler 从尚未冻结的不同原 receipt schema 自动推断。ROOT 必须确认引用的原 proof 确实证明同一包的 index/COMPLETE、全部原件与恢复件路径/bytes/SHA、真实 pack/restore exit 与进程闭合；不能仅据 summary.passed 或目录名填 true。本候选只机械验证投影的固定条件、所有原证明字节 pin、包身份与 member union；不声称已经自动解释任意 upstream proof schema。尚缺真实 proof 或 ROOT 未核对应关系时不得签 GO。这是一份显式选择输入，不新建 proof/授权登记系统。

所有 ref 为 canonical 无 symlink 的明确绝对路径，严格 JSON / SHA / bytes 核对，单 metadata ≤8 MiB；同一路径冲突 pin 拒绝。bundle roots 不能重复/互为祖先；原件完整相对路径跨包不重叠且无前缀冲突。ROOT 只给闭合文件，不能把 live run/monitor/未闭合来源混入 selection。

## 独立 ROOT GO 与命令

GO 恰 9 字段：`schema='root-k3-collection-assembly-go-v1'`、`issuer='ROOT'`、`approved=true`、`action='assemble_local_only'`、本冻结源码 `assembler_sha256`、selection 的外部 `selection_ref={path,bytes,sha256}`、新 `output_dir`、`publication_authorized=false`、`network_authorized=false`。

```text
/usr/bin/python3 -B /ABS/k3_formal_collection_assembly_candidate_v1/assemble.py
  --go /ABS/ROOT_ASSEMBLY_GO.json --go-sha256 EXTERNAL_GO_SHA
  --output-dir /ABS/FRESH_OUTER/payload
```

没有实际 GO 模板文件或自签 SHA。调用时 output 必须不存在，父目录存在，且与任何输入/工具不重叠。core=0；流式原字节复制，排他新写、fsync、源/副本 SHA 前后核对。原 48 MiB 压缩、256 MiB 展开、100 MiB 原件、256 文件/片、4096 片/包、8 MiB metadata 和 collection 256 MiB metadata 总限均不放宽。失败保留新输出，不 retry/resume/覆盖；assembler 并非事务。

证明原件只被引用核 pin，不自动复制到包精确树。最终公开 proof/attribution/navigation、已知值扫描证据、实际 Git push 与 fresh-remote 完整恢复仍由 ROOT 另行收集验收，不能仅以 assembler passed 取代。公开恢复使用原 collection wrapper；其 `remote_restore_performed=false` 不改写，真实远端来源由独立执行证明。

## CPU 测试

两个解释器各 5 项：34 行选择/分类/总量；缺批/重复/unknown closure/非 0；错 proof pin/错 raw root；两临时假包完整字节复制与拒已有输出；全局 member 路径重复在复制前拒绝。临时小 INDEX/COMPLETE 使用原 schema，archive 是明确的 opaque fixture bytes，**不是可恢复 TAR，也未创建/运行新 packer**。这些测试只验证选择、身份、复制接线，不冒充真实包 restore 验收或当前 34 包已经闭合。

首轮重复输出的拒绝实际上正确，但测试捕获了另一次动态加载的 DeliveryError 类对象，产生 1 个 harness error。只改为核类名与固定错误码；生产未因此修改。初始失败日志保留。当前 source/diff/CPU 封版后待 ROOT 主读；本作者非 fresh 科学结果 reviewer，旧 gold 暴露记录不变。
