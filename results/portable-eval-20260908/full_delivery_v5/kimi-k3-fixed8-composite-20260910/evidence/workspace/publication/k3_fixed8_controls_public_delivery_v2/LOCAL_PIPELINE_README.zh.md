# K3 fixed8 公开 controls：本地交付已通过

本轮严格封装 ROOT 授权的 466 个原件（195085429 B），生成 2 个 tar.gz 分片（24688100 B）。原 scanner、pack、restore 各执行一次，全部自然 exit 0；随后完整源/恢复字节核对通过。这是本地验收，不是 GitHub 发布或最终联合公开恢复验收。

| 阶段 | session / start → completion | exit |
| --- | --- | --- |
| 原 scanner | 77883 / bb0fe0 → f4c4aa | 0 |
| 原 pack | 27435 / cbeb74 → 3e53d4 | 0 |
| 原 restore | 59324 / 953e94 → dcf94a | 0 |
| 全 source/restore 字节核对 | 11435 / 276099 → 9b8dee | 0 |

前置门禁 cd53ed、扫描门禁 3f26c6、完整分片门禁 a7165d 均 exit 0。扫描具备全部 466 required stages、4 个已知密钥来源、0 findings / 0 advisories，lock 与批准 spec 语义完全一致；pack 全部分片 SHA/字节、INDEX/member union 和 COMPLETE 均已复核。

全量核对实际读取 951 个对象：466 源文件、466 恢复文件、2 个压缩分片、12 个 metadata、4 个原工具及 1 个冻结 helper。每个对象完整流式 SHA/字节及前后文件 stat 均通过；12 metadata 在末尾重新 hash。bundle 全树 7 文件/4 目录，restore 全树 467 文件/102 目录（含根）；前后路径集合、目录 stat 一致。源对象只按 inventory 的分散路径核对，不遍历整个 workspace，也不宣称源目录全集相等。sorted original-row digest 为 79358e5c20c6f9f726043f882d85bb466b89f987ce84bd8b87be18218f8c27be。

三条会加载密钥的真实 CLI 都显式以前缀 /usr/bin/prlimit --core=0:0 -- /usr/bin/python3 -B 启动；前置及全 byte 核验实际观察 RLIMIT_CORE=(0,0)、Python 3.10.12。CPU affinity 不作为 coredump 限制替代。四个路径仅在命令记录里用 GO 顺序占位；实际密钥内容只由原工具 RAM 读取，操作员未手动读取、stat、hash、打印密钥。没有新 driver、工具/规则修改、模型请求、Git 或网络发布。

## 有限公开子集说明

旧 467 个私有 controls 和首次失败扫描完整保留。本轮仅按 ROOT 新授权排除一件 1292 B 的 test_legacy_helpers_CPU.json：它是合成 CPU 测试收据，不是实验结果；原 scanner 拒绝原因是 credential_metadata_field，不能据此宣称已证明密钥泄漏。本操作员未读取或 stat 被排除原件，也未提供改写替代品。7 个旧同路径/SHA/字节 owner 只复用，不重打包；1072 新 raw 和旧 65105 成员均未重打包。

该公开遗漏不改变实验结果或科学分母，但部分留存证据仍指向被排除收据，因此不能宣称覆盖全部私有审计引用链。没有进一步排除或按成绩筛选。旧 raw 的 RLIMIT 历史限定记录原样保留，不被本轮追认覆盖。

## 查验入口

- [ROOT 公开 scope](ROOT_PUBLIC_SCOPE.json)、[inventory](inventory.json)、[批准 spec](ROOT_SCAN_SPEC.json)、[本轮 GO](ROOT_PIPELINE_GO.json)
- [真实 CLI/启动/全部 waits/自然退出与门禁](ACTUAL_CLI_RECORDS.json)
- [全字节比较](WHOLE_FILE_COMPARISON.json)、[操作员结论](LOCAL_OPERATOR.json)
- [扫描 manifest](scan_v1/manifest.json)、[扫描 lock](scan_v1/lock.json)
- [bundle INDEX](bundle_v1/payload/INDEX.json)、[bundle COMPLETE](bundle_v1/COMPLETE.json)、[恢复 COMPLETE](local_restore_v1/COMPLETE.json)

最终 outgoing 的原 scanner（4 known-value sources，tar 成员完整扫描）和全新 K3 union 的公开恢复仍待 ROOT 后续授权。本目录本轮操作员产物 STOP-WRITE。
