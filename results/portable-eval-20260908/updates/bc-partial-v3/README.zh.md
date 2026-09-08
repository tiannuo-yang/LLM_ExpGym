# Kimi-K3 B/C v3：中断批次的完整原始证据

这是**已中断 pilot 的原件交付候选**，不是 78-pool 全矩阵结果、正式
K3/GLM 比较或全项目验收。ROOT 已有限接受 partial 与 transport 证据；
本候选仍待独立发布复核，未获 push GO。

## 先看什么

- [POOL_STATUS.csv](POOL_STATUS.csv)：原计划 78 个 pool 的逐项状态与隔离。
- [ATTEMPTS.csv](ATTEMPTS.csv)：全部 1,532 attempts 的关联、用量和 unknown。
- [FILES.csv](FILES.csv)：全部 2,348 原件的路径、bytes、SHA 与下载分片。
- [完整原件清单](provenance/full_original_inventory.json)、[分片索引](bundle/payload/INDEX.json)、[交付恢复回执](DELIVERY_ACCEPTANCE.json)。
- [SHA256SUMS](SHA256SUMS)：完整候选文件的 SHA，包括每个可独立下载的分片。
- [严格完整扫描的原始失败记录](provenance/initial_full_scan_failed/manifest.json)：保留而非改写历史。

| 范围 | 原计划 pool | 有执行证据 | 性能证据合格 |
|---|---:|---:|---:|
| B | 42 | 42 | 42 |
| C | 36 | 5 | 4 |
| 合计 | 78 | 47 | 46 |

原计划 312 agent traces，留存 188 个。31 个 pool 没有启动证据。
这些未启动行的语义零分数在 CSV 中标为 `not_applicable_no_execution`，不是 0。
一个 provider `abort` 导致整个 pool 隔离，不因原 local PASS 或 HTTP 200
而恢复资格。46 个合格 pool 中的 14 个原始语义零分保留；隔离池的另一个
原始零分也保留，但不混入合格语义零分。47 次 guarded skips 是原结果的
跳过复核，不是新实验；独立审计复用原 scorer，不是独立评分算法。
存储 graph/history 的检查不证明完整并发 graph/cache/clock 因果语义。

原 run 完整保留 **2,173 文件 / 99,498,860 bytes**：1,532 raw dump、
282 result JSON、344 个 logs 目录文件（含 47 个 execution.log）以及
15 个根文件。不存在正常结束 `execution.json`，没有补造。
支持证据和工具另计后，整集合为 **2,348 原件 / 120,489,460 bytes**。
2,347 原件进入 10 个无损分片，压缩档合计 21,400,125 bytes；另一个
21,217-byte 控制原件如下单独公开，最终合回仍是完整原 bytes/路径集合。

## Transport 与成本边界

全部 2,071 行 router 原快照保留。1,532 个 attempts 唯一关联：
1,531 个具有 request/response 双 SHA、HTTP 200 与 close 证据（含 abort），
1 个原始 502 只有 request 关联；该次原 attempt 2 的恢复也完整保留。
固定正负 1 秒只是关联假设，不是独立同步的精确服务时钟。

已知 input 为 14,686,457、output 1,829,866、provider total
16,516,323 tokens；reasoning 1,438,618 已包含在 output 中，不重复相加。
这些已知和包含 abort，但 502 的生成与费用未知，因此全 attempt 完整
usage/成本仍 unknown，不是 0。cache read/write 的 1,532 attempts 全部
未报告；CSV 明确写 unknown。SIGINT 后没有自然结束产生的最终全 harness
monotonic timing，不能用启动至停止的 wall 区间替代。

## 唯一固定控制原件例外

[原停机收据](control_originals/operator_single_pid_sigint_20260908T102501Z.json)
SHA：`15bbab050595d4c9137cd971f5201f42900d4da2856a0b822b65f9bb1b374de2`。
其顶层 `authorization` 是明确单 PID 的文字授权，不是凭据。
冻结扫描器仍如实报一个 `credential_metadata_field`，没有改规则、改原件、
改后缀或把整类字段设成免检。ROOT 仅人工准入这一个固定路径/固定 bytes。
它仍须通过已知秘密、高置信凭据模式、严格 JSON 和跨字段秘密检查。

因此“分片子集 strict PASS”与“所有原件 strict PASS”不同；后者为 false。
原 run 的 2,173 文件 = 2,172 个分片原件 + 1 个直接公开 control 原件。
工具 `assemble.py` 只认识这一固定文件，不接受泛化 allowlist。

## 下载、独立校验与完整恢复

本候选验收环境为 Python 3.10.12，使用已冻结 canonical-PAX 格式；
没有第三方依赖，不承诺任意第三方 TAR/profile 兼容。下载本目录完整内容后，可先运行
`sha256sum -c SHA256SUMS`。下面的输出目录必须不存在，父目录必须存在；
工具拒绝已有空目录、软链接、缺漏、重复和内容变更，不自动覆盖或接管。
恢复输出放在本目录之外，避免改变已下载候选的完整文件集合。

```sh
python3 -B tools/restore.py --index bundle/payload/INDEX.json \
  --sha256 f756064abe54adc4a0fc21d10e9e0ef6d76ac863c3eae325dc58fb5913c413b0 \
  --output-dir ../bc-shards-restored

python3 -B tools/assemble.py --index bundle/payload/INDEX.json \
  --index-sha256 f756064abe54adc4a0fc21d10e9e0ef6d76ac863c3eae325dc58fb5913c413b0 \
  --restored ../bc-shards-restored \
  --control control_originals/operator_single_pid_sigint_20260908T102501Z.json \
  --output-dir ../bc-complete-originals
```

最终原件位于 `../bc-complete-originals/payload/`，其下保留 workspace
相对路径，例如 `portable_eval_20260908/pilot_runs/k3_bc312_1203474_v3/`。
已有 restored wrapper 的 COMPLETE/payload 不会被补写；assembly 产生新的
独占 wrapper，全部 payload 校验/fsync 后才写新的 COMPLETE。
模式、时间戳和 ownership 不作为可恢复保证；原内容 bytes 与路径完整保留。

每片也能独立恢复，不需要其他分片或完整 INDEX：从 INDEX/SHA256SUMS 获取
该片 SHA，调用 `tools/restore.py --archive <part.tar.gz> --sha256 <该片SHA>
--output-dir <全新目录>`。保留 `tools/common.py`、`tools/restore.py` 和
上一级 `validate_bundle_v2.py` 的目录结构。单片内部含该片完整原路径/SHA
清单，不是摘要替代。单片恢复成功不能冒充整包完成。

默认限制不变：48 MiB 压缩/片、256 MiB 展开/片、100 MiB 原件、
256 原件/片、8 MiB 元数据、最多 4,096 片。过大原件拒绝，不 chunk。
下载者不需要服务密钥；本地准备与验收另用已授权固定 key 在内存 exact scan，
没有把 key 或 secret-only fingerprint 放入本包。扫描不能证明所有未知秘密
不存在；人工公开内容复核和可信外部 SHA 仍重要。

如需 CPU 复跑本包的合回边界测试，可运行 `python3 -B tools/test_assemble.py`；
它只使用本包固定 control 原件、合成数据与合成 marker，不读取真实服务 key。
[完整新增 diff](review/assemble.added.diff) 和 [28-test 日志](review/assembly_tests.log)
便于审查这一固定例外；被冻结 v2 的 pack/restore/common/scanner 原字节不变。
最后的 CSV 缺省字段开发失败及其修复归因也保留在
[开发记录](review/local_workflow/DEVELOPMENT.md)、
[失败版脚本原件](review/development_csv_failure_v1/build_candidate.failed_original.py) 和
[5 个 metadata tests](review/metadata_tests.log)；收尾没有改已完成恢复 payload。

## 来源及审计导航

source-v3 tree SHA 不变：
`d1606db7d6036c8975ce9d3e556daf7fa2ce4604879f2b3878435b0f96aebb78`。
沿用既有 [accepted-source-v3.tar.gz](../../source/accepted-source-v3.tar.gz)，
SHA `97ecfe148a2c47e811dbf15e0b820f28979972c1ad7a5939cc065b1f4ee0e15b`。
它未重复打包；新 source branch 不给这些历史 v3 结果换标签。
既有 1,127 个公开结果文件保持不变。

完整恢复后主要入口（前缀均为 `portable_eval_20260908/validation/`）：

- `bc_partial_independent_20260908T1046Z/README.zh.md` 与 receipt
  `c53de465cdbff775f772d3c3d9a1cf5011976e2a06fb63a140f85489e43f3e4f`。
- `bc_partial_transport_20260908T1055Z/README.zh.md` 与 receipt
  `9de144fe7d2ac535663bbfba7a8c7225826c7c55977f80bf169d6f89a3dbc0f0`。
- ROOT 独立 transport receipt
  `bc_partial_transport_root_20260908T1100Z/receipt.json`，SHA
  `406c98a07a3ac8c397aa76f392070586c160688715a556471ee83a46450b7625`。
- ROOT drain `bc_partial_root_drain_20260908T1045Z.json`，SHA
  `52455499cbeb6237dd7aad70332731bb85ae834fba3539ea87aea7ed3aeb4e9b`。
- ROOT 有限接受 `bc_partial_root_acceptance_20260908T1112Z.json`，SHA
  `83572c23398112b37593b496960723aad0f56fb2f2c3ff0a41fbfc3aaeafae56`，
  明确 publication_authorized=false。

全部失败/unknown、原 manifest/commands/started、人工中断/单 PID stop/drain、
独立审计 stdout/stderr、完整 namespace inventory/raw audit、准备/复核收据和
绑定 source/helpers 一并保留。权重、私钥文件、runtime/environment 二进制、
独立 dataset payload 文件、live router 日志及当前 dirty source tree 不进入包；
已在 raw 请求/响应中的上下文和工具观测原 bytes 不裁剪。
