# 存档元数据投影说明

这组文件用于查找本地存档中的原件及其存储位置。原件和压缩分片保持本地私有（`local-only`）；公开元数据 CSV 不代表 payload 可以下载，也不代表原件、分片或候选附件已通过发布安全扫描。发布扫描由最终发布流程另行执行。

## MEMBERS.csv

每行代表一个实际存储位置，共 **41,929 行数据**，覆盖 **41,920 个不同的原件路径**。6 个原件有多个存储位置，产生的 9 条额外存储记录全部保留；它们不是新增实验。

| 字段 | 含义 |
|---|---|
| `path` | 相对 study 根目录的原件路径，同时是 tar 内的 member path。生成器必须验证两者严格相等，否则拒绝输出。 |
| `bytes` | 原件的字节数，继承冻结清单。 |
| `sha256` | 原件内容的 SHA256，继承冻结清单。 |
| `shard_id` | 连接 `SHARDS.csv` 的紧凑键，无独立身份含义。 |

相同 `path` 可以有多行，分别保留对应分片中的存储位置；不能仅按 `path` 去重后解释为完整存储清单。

## SHARDS.csv

共 **92 行数据**，压缩分片总计 **1,356,265,462 B**。

| 字段 | 含义 |
|---|---|
| `shard_id` | 本投影内唯一的连接键，与 `MEMBERS.csv.shard_id` 对应。 |
| `path` | 相对 study 根目录的本地归档分片位置，例如 `archives/original917-v1/payload/part-000001.tar.gz`。不是下载链接。 |
| `bytes` | 压缩分片文件的字节数，继承冻结清单。 |
| `sha256` | 压缩分片文件内容的 SHA256，继承冻结清单。 |

## 身份与来源

`ARCHIVE_INDEX.json` 分开记录两类身份：`source_inputs` 指向原冻结清单的路径、大小和 SHA；`projection_files` 记录本次投影文件自身的大小和 SHA。投影 CSV 的 SHA 只能标识该 CSV，不能冒充原件或分片的内容身份。

**25 项外部来源**仅概述数量与类别，不复制 host/user 绝对路径、完整 endpoint 或私有配置的实际值。目录路径均按声明的相对根解析，不依赖公开仓库所在位置。

## 连接与恢复定位

按 `shard_id` 连接两张表，即可从原件路径定位所有本地分片。例如将 CSV 导入同名表后：

```sql
SELECT m.path AS member_path,
       m.bytes AS member_bytes,
       m.sha256 AS member_sha256,
       s.path AS shard_path,
       s.bytes AS shard_bytes,
       s.sha256 AS shard_sha256
FROM MEMBERS AS m
JOIN SHARDS AS s ON m.shard_id = s.shard_id
WHERE m.path = 'relative/path/to/file.json';
```

返回多行时，每行是一个保留的存储位置。恢复还需要本地 payload 分片，以及与之匹配的原生 `expgym.delivery.v1` manifest 和恢复器；公开投影本身不能替代这些文件。以 study 根目录解析 `shard_path`，由匹配的 manifest／恢复器在一次流校验中核对分片和原件的大小、SHA，并只恢复所需 `member_path`，保留原字节。

## 实验范围

| 范围 | 物理 jobs | Agent trajectories |
|---|---:|---:|
| 正式实验：原 917 条与新增 Max 417 条 | 1,334 | 3,146 |
| 技术验证：pilot 19 条与 patch 2 条 | 21 | 63 |

两类范围分别记录。CSV 行数、重复存储位置、分析行和外层附件都不能用于推导实验数。本投影不重新计算成本，也不认证科学报告结论。
