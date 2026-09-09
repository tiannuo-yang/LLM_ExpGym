# 闭合历史数据补充交付：v5 重跑之前与 smoke

本包不是新版正式实验结果，也不支持新版性能结论。它保留开发检查、已作废的旧两模型运行、新版 smoke 和对应控制资料；原失败、未开始项、缺答与原始 dump 没有改写或混入新版统计。

共 **47,529 个原文件、1,055,374,017 字节**，分为 32 个可独立校验的包；197 个 gzip 分片合计 204,621,699 字节。分类如下：

| 分类 | 包数 | 原文件数 | 用途 |
| --- | ---: | ---: | --- |
| history | 5 | 1,688 | DEV／协议与环境检查；名称含 formal 也不代表正式研究 |
| superseded | 23 | 43,279 | 旧 Kimi、GLM 运行，全部退出新版统计 |
| smoke | 2 | 2,116 | 新版实际 smoke，不计正式统计 |
| controls | 1 | 360 | 封存计划、环境与执行控制资料 |
| source | 1 | 86 | 实际冻结源码清单；不是整个开发工作区 |

精确归属与逐文件 SHA 在 [合集索引](payload/collection/INDEX.json) 及各包的 `payload/indexes/part-*.json` 中。旧 GitHub 交付仍保留在上级结果目录；本包是补充范围，不声称包含所有历史 Git 版本或仍在运行的新版正式实验。

## 一条命令完整恢复

需要 Python 3.10 或 3.11、完整下载本目录，以及一个尚不存在的输出目录；不需要模型、GPU、API key 或原集群路径。在本目录执行：

```bash
python3 -B payload/tools/publication/collection_restore_candidate_v2/restore_collection.py \
  --index payload/collection/INDEX.json \
  --sha256 ee080ed22ea8ccd2bf03bbb011369cc8329009c981f95c00f8d66aa4aa47d078 \
  --output-dir /ABS/FRESH_RESTORE_DIRECTORY
```

成功必须同时满足：命令退出码 0、有效 `COLLECTION_COMPLETE.json`、没有 `COLLECTION_INCOMPLETE.json`，以及全部原件字节／路径／SHA 校验通过。不能只看 COMPLETE 文件是否存在。失败保留现场，不自动重试、覆盖、接管或删除；另选全新目录才能再次恢复。

每个原件位于 `<输出目录>/<bundle_id>/payload/<原工作区相对路径>`。`OWNERSHIP_INDEX.json` 给出各包的恢复目录和复制的原成员索引，可按成员 `path` 查找文件。恢复不会写回原工作区，不保留原 POSIX 权限、所有者、时间戳，也不复制模型权重或虚拟环境。

公开恢复使用原路径、TAR/PAX、大小和 SHA 安全检查及文本规则；不会读取发布者私密 key，也不冒称重新执行了发布时的三份已知密钥值比较。原发布扫描证明随各包 `SOURCE_SCAN.json` 保留。固定限制为每分片压缩 48 MiB／展开 256 MiB、每原件 100 MiB、每分片 256 文件；没有为本次数据放宽。

## 已有验收与边界

全部 32 包已分别经过原打包器、独立恢复入口和逐原件核对；ROOT 又核对了全部原件与恢复件的完整集合及 SHA。装配只复制已验收包，不重写或重新压缩它们；[装配回执](payload/ASSEMBLY_RECEIPT.json) 和 [装配文件清单](payload/RELEASE_FILES.json) 绑定完整交付字节。恢复器的 10 项合成测试在 Python 3.10/3.11 通过，独立入口反例检查也通过。

这里尚不以本地检查冒充远端恢复。推送后的实际 GitHub 下载／完整恢复证据将单独记录；新版正式全量、分析和结果后独立逻辑审计另行交付。

[第三方归属与数据边界](ATTRIBUTION.md)。可用源码提交为 [8dfea729](https://github.com/tiannuo-yang/LLM_ExpGym/tree/8dfea72931d952ad90f1c722a83957ab23afc6bf)；其中实验源码仍为冻结 v5，新增归属说明没有改变实验实现。
