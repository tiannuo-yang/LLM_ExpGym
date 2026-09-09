# Kimi-K3 v5：原运行的完整可恢复数据

这份交付保留原运行的 **697 项完成＋8 项节点故障失败**。数据包完整不等于实验矩阵完整：原 `execution_complete=false`、`score_complete=false` 不改写，也没有重抽成功结果。

先看[阶段结果与 CSV](README.zh.md)，数据归属沿用[ATTRIBUTION](ATTRIBUTION.md)。本页只说明原运行的数据交付；GLM、Kimi 故障项恢复与双模型最终验收另行报告。

## 范围与状态

| 归档范围 | 包数 | 原文件数 | 原始字节 |
| --- | ---: | ---: | ---: |
| Kimi 原正式运行，包括失败与 partial dump | 33 | 64,188 | 1,268,512,973 |
| 固定导出、审计、分析、封存与服务证据 | 1 | 917 | 253,018,660 |
| 合计 | 34 | 65,105 | 1,521,531,633 |

共 261 个压缩分片，压缩字节合计 275,003,805；含索引和五个恢复工具的 `payload/` 共 632 文件、342,275,930 B。另附 614 个外层执行／扫描／工程证据文件；它们和已有 37 个浏览文件不重复计入上述 65,105 原件。两个节点故障影响说明仍在浏览区，不伪装成917附属成员。

本次提交提供完整归档。本地逐批恢复、最终全部原件与恢复件的路径／大小／SHA 核对、34包组装及复制后检查均已通过。**从 GitHub 重新下载后的完整恢复与 AN2 异地分析重放尚待单独执行、公布回执**；不能由本地成功推断远端已验证。

不包含权重、虚拟环境、私钥、完整上游数据库或活动 GLM 数据。旧 DEV、作废运行与 smoke 见[此前32包归档](../../closed_history_v5_20260909/README.zh.md)。原文件中的用户目录和集群主机名是历史 provenance，不是公开 API。

## 下载和恢复

恢复工具只使用 Python 标准库；本轮验证环境为 Python 3.10/3.11。不需要 API key、GPU 或原集群目录。原件本身约1.52 GB，另需归档、Git对象和索引空间；请准备足够磁盘与文件数量配额。

```bash
git clone --filter=blob:none --no-checkout --single-branch \
  --branch results/portable-eval-20260908 \
  https://github.com/tiannuo-yang/LLM_ExpGym.git expgym-results
git -C expgym-results sparse-checkout set --no-cone \
  '/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/**'
git -C expgym-results checkout
cd expgym-results/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909
k3_restore_parent="$(mktemp -d)"
python3 payload/tools/publication/collection_restore_candidate_v2/restore_collection.py \
  --index payload/collection/INDEX.json \
  --sha256 a78227369423e71e8c4380e46416b8a4ed88464f3e8a502fe1747e7e703103f5 \
  --output-dir "$k3_restore_parent/restored"
```

输出目录必须尚不存在；失败产物保留，不应盲目删除或覆盖后重试。工具会解压、核原路径与SHA并做JSON安全检查，**不是重新评分**，也不承诺恢复原POSIX owner/mode/mtime。成功需实际exit0与`COLLECTION_COMPLETE.json`；只有下载或解压出部分文件不算完整恢复。

原件在 `<恢复根>/<bundle_id>/payload/<原workspace相对路径>`；`OWNERSHIP_INDEX.json` 提供完整成员归属。此布局保留原路径身份而不写入原集群绝对目录。分析输入里原有绝对`source_index`不能直接当成本地可用路径；异地映射和原分析器重放的验证将另行补充，不建议执行历史operator argv或跟读其中credential路径。

## 关键查验入口

- [完整合集索引](payload/collection/INDEX.json)、[归档逐文件清单](payload/RELEASE_FILES.json)、[实际组装回执](payload/ASSEMBLY_RECEIPT.json)。
- [ROOT 34包选择](evidence/workspace/publication/k3_formal_collection_assembly_v1/ROOT_SELECTION.json)、[组装实际退出与验证](evidence/workspace/publication/k3_formal_collection_assembly_v1/ROOT_COMPLETION.json)、[全部复制文件及成员核对](evidence/workspace/publication/k3_formal_collection_assembly_v1/ROOT_LOCAL_VERIFICATION.json)。
- [原33批最终回执](evidence/workspace/publication/k3_formal_original_local_delivery_v2/SUMMARY.json)、[ROOT 原件／恢复证据核对](evidence/workspace/publication/k3_formal_original_local_delivery_v2_operator/ROOT_LOCAL_PROOF.json)。33批各自的`pack.exit.json`、`restore.exit.json`、完整逐文件比较及日志原样保留。
- [917附属原件完整本地恢复证明](evidence/workspace/publication/k3_controls_local_delivery_v1/ROOT_LOCAL_PROOF.json)。
- [外层606原件候选清单与边界](evidence/workspace/publication/k3_formal_outer_evidence_candidate_v1/README.zh.md)。原`candidate/approved=false`只表示它形成时的状态，不篡改为实际发布证明；另8件是这份候选本身5件及最终ROOT组装证明3件。
- [本次新增／更新文件清单](FULL_DELIVERY_FILES.json)不包含其自身；原37浏览文件保持字节不变。

原始评分、反向结果、缺项与未知usage均保留。原配置为自部署模型、最大推理及自定义矩阵，不是论文主设置的精确复现。数据可恢复不证明所有外部训练数据／后端查表来源均已独立复现，也不证明PoolAct对所有模型或指标稳定改善。
