# GLM compatibility development：封存原件与恢复索引

这是 GLM 首轮 compatibility development 的 checkpoint，不是正式 M/R 矩阵、K3 结果、模型优劣结论或项目最终验收。原件全部保留，可下载核验；本页不展示答案、评分值或效果方向。

| 留存内容 | 数量 |
|---|---:|
| 原始文件 | 1370 |
| 原始字节 | 166769588 |
| 零字节原件 | 39 |
| 独立 gzip 分片 | 6 |
| gzip 合计字节 | 36041706 |

导航：[逐原件 TSV](ORIGINALS.tsv)、[公开文件清单](MANIFEST.json)、[校验和](SHA256SUMS)、[原 seal lock](evidence/seal/lock.json)、[bundle INDEX](bundle/payload/INDEX.json)、[ROOT 恢复验收](controls/ROOT_RESTORE_ACCEPTANCE.json)、[七次离线恢复记录](operators/restore/RECEIPT.json)。所有失败、length、截断及空文件均保留，不用摘要替代 raw。

15 jobs、51 task traces、12 nonce slots；475 task raw + 12 nonce raw = 487 原始请求。原协议补充记录 21 次循环内修复：9 次 provider length + 12 次多 native tool calls；9 已包含在 21 内。这不是 HTTP 重试，487 请求均 attempt 1；审计通过不等于零协议失误。v4 preflight、v5 初始 fixture 失败及早期监控归因修正保留在原件中。

reported usage 不是价格或全项目 GPU/启动成本；reasoning 已包含在 completion，不能再次加总；cache usage 为 unknown/null，不是 0。rendered_task_context 仅是 source→client 请求重建，不是 server tokenizer 实际渲染，也不是全并发/cache/clock 因果重放、strict repeatability 或 router 双哈希 join。独立重跑原 repository scorer 不等于新设计的独立评分算法。

GLM 九个 srun 原退出码均为 **137 / explicit_ROOT_operator_stop**；ROOT 记录 children=0、无 stop timeout，不能改称 exit 0、全部优雅退出、provider drain 或设备/KV 内存逐字节清空。该 checkpoint 不证明后续 K3 或 formal 实验完成。

## 源码身份不能混同

[来源身份索引](SOURCE_IDENTITY.json) 分开记录：历史 source-only Git commit `7a3d3ac9058e6dbccc2b3ea75ed61d1c1dc6c106` 与实际 study 源树指纹 `b280a0f640ffab8aa90bc74df4c9ecf3189b375cdd674094a005b3569bb4b608`。它们不是同一种标识；原 plan 还有各 harness/runtime/auditor 的逐文件绑定。见 [Git source 发布原收据](provenance/source_commit_7a3d_publication_receipt.json) 与 [study static acceptance](provenance/study_static_acceptance_v4.json)。未将当前 dirty worktree/新 HEAD 冒充实际运行版本，也不声称完整环境/数据集已自包含。

## 不用私有 key 的离线恢复

保留下载目录布局，在 capsule 根目录运行以下命令。已验证 Python 3.10.12；输出目录必须不存在。

```bash
python3 -B tools/shard_delivery_candidate_v2/restore.py --index bundle/payload/INDEX.json --sha256 0044ee0569058c371afe7fa6774f0a0313d1ef04b96186c520eb9b27c621bf18 --output-dir restored-new
```

也可只下载任一分片及 [恢复器](tools/shard_delivery_candidate_v2/restore.py)、[common](tools/shard_delivery_candidate_v2/common.py)、[原扫描器](tools/validate_bundle_v2.py)，保持它们的相对布局；该片的独立 SHA 见 TSV/INDEX：

```bash
python3 -B tools/shard_delivery_candidate_v2/restore.py --archive bundle/payload/shards/part-000001.tar.gz --sha256 a50a996ba1aabe34ee19c5a91cd372c83b12adc83678c01e871c6d19c3a77efd --output-dir restored-part-000001-new
```

无需 secret-file、网络、GPU 或原实验环境。完整恢复及六个单片恢复均已各一次成功；full 与六片不重叠合集逐文件对原件及 lock 的 bytes/SHA/paths 严等。仅承诺原字节与相对路径，不承诺恢复 POSIX ownership/mode/mtime。原 lock SHA 为 `1b64e8f9cc2ca1ea30b47a7cec0b58cccc30e730494a70ca93bc73d623feec26`。

`review/`、`operators/` 和各 ROOT GO 是历史控制/审计原件，可能保留实验室绝对路径与当时的未发布状态，不是用户离线执行入口。公开路径只使用上述 tools 布局；Git 发布状态由后续外部发布收据记录，不能把本地扫描/恢复 GO 当作 Git 授权。
