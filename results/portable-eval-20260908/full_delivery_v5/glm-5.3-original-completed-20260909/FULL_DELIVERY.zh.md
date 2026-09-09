# GLM-5.3：完整实验归档与恢复

本地归档、完整恢复和 37 包组装及独立全量校验已通过。**远端发布、fresh GitHub 副本恢复及原 AN2 异地重放均待验证**，本页不宣称完整交付已完成。科学结果与限制沿用 [原结果入口](RESULTS.zh.md)，原 35 份浏览材料不改写。

| 归档范围 | 包数 | 原文件数 | 原字节数 |
| --- | ---: | ---: | ---: |
| GLM 正式运行全部原件 | 36 | 70,520 | 3,242,213,793 |
| 公开 controls 子集 | 1 | 1,114 | 224,903,100 |
| 合计 | 37 | 71,634 | 3,467,116,893 |

本地组装得到 288 个 tar 分片，压缩字节共 772,603,212；release payload 693 文件，加两份回执共 695 文件、846,529,622 B。这些交付文件数不等于包内原文件数，也不重复计入既有 35 份网页。

固定入口：[collection INDEX](payload/collection/INDEX.json)、[release 清单](payload/RELEASE_FILES.json)、[组装回执](payload/ASSEMBLY_RECEIPT.json)。当前 INDEX 为 8,340 B，其外部 SHA-256 为：

```text
9d4433461c3cf0a3017220003c2d70b5085e715c5db82303449d57e48c8cca09
```

上述链接是发布布局；本页编写时尚未验证远端对应文件。

## 从完整下载副本恢复

进入本页所在目录，保留 `payload/` 内工具与包的相对布局。以下命令离线执行，不传 secret；`restored-glm-v5-fresh` 必须尚不存在，失败输出保留，不覆盖重试。

```bash
python3 -B payload/tools/publication/collection_restore_candidate_v2/restore_collection.py \
  --index payload/collection/INDEX.json \
  --sha256 9d4433461c3cf0a3017220003c2d70b5085e715c5db82303449d57e48c8cca09 \
  --output-dir restored-glm-v5-fresh
```

恢复成功须实际 exit 0、stdout 和 `COLLECTION_COMPLETE.json` 均为 `complete:true`、完成记录 `input_sha256` 匹配上述 SHA、无 `COLLECTION_INCOMPLETE.json`，并核对 37 包、71,634 文件、3,467,116,893 B 及其索引绑定。原件位于 `<恢复根>/<bundle_id>/payload/<原 workspace 相对路径>`；用 `OWNERSHIP_INDEX.json` 和各 member index 查归属。工具验证路径/字节/SHA及公共安全规则，不重做发布者的私密 known-value 扫描，不保证原 owner/mode/mtime。

原 `source_index.json` 含原机器绝对路径，不能直接异地使用。须先验收完整恢复，再通过原 relocator 派生新 plain 路径索引，保留原输入及 pins、相对代码布局，运行原 AN2 并比较全部输出。字节恢复不等于分析重放。runtime/profile 证据不等于完整可运行 backend；此归档不自包含模型权重、虚拟环境或完整上游数据仓库。

## 公开范围限制

全部实验原件保留，没有按成绩筛选。公开 controls 比原 1,115 件 seal 仅排除 `seal_operator_glm_formal_v1/invocation.json`：一份 4,783 B 非实验操作回执；不改写该原件，原 seal 与失败扫描保留。153 份 shared 原件仍物理携带；部分审计引用指向这份未公开回执，因此公开内部证明链不是完全闭合。

原 dump 可能包含任务、工具回复及模型输出，[数据归属与许可边界](../../ATTRIBUTION.md)仍适用。旧 DEV、作废运行与 smoke 不混入本次正式归档；K3 原节点失败交付保持独立，其 8 项缺失不因 GLM 归档完成而被补齐。

本页状态仅到独立本地全量核验通过；远端提交/副本核验、公开恢复与 AN2 重放的最终证明均为 pending，须由后续实际回执确认。
