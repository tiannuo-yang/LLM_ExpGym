# K3 最终联合归档与恢复

2026-09-10 后续验收：K3 公开数据已完整恢复并通过全量文件检查，原分析的 10/10 输出逐字节重现。[最终恢复／重放凭据](replay_verified_v1/REPLAY_VERIFIED.zh.md)。以下原文末尾的“发布候选”或“尚待追加”描述 1694aa2 发布时状态，历史报告与收据不倒填修改。

本归档按完整 workspace-relative 原路径保存文件字节，不重序列化原始实验数据。旧 34 包保持不变，增加固定 8 项恢复 raw 一包和公开 controls 一包；联合索引只对旧包位置加目录前缀。

| 范围 | 原始文件 | 原始字节 |
| --- | ---: | ---: |
| 旧正式运行及 controls | 65,105 | 1,521,531,633 |
| 固定8项恢复 raw | 1,072 | 34,520,799 |
| 新公开 controls | 466 | 195,085,429 |
| 联合归档 | **66,643** | **1,751,137,861** |

36 包含 268 个分片，压缩总计 305,870,108 B。新增只有 7 个分片（30,866,303 B），没有重复打包旧数据。恢复还会生成/复制索引及完成回执，预计物理文件总数 66,986；这不同于原始文件分母。

本地凭据：[联合索引、全部分片SHA及路径前置核验](evidence/root/ROOT_UNION_PREFLIGHT.json)；[466份新controls源/恢复字节及复制核验](evidence/root/ROOT_CONTROLS_LOCAL_ACCEPTANCE.json)。

附属证据与工具导航：[精确外层映射及复用工具说明](evidence/outer-selection/README.zh.md)；[恢复后逐文件检查器](tools/publication/k3_union_remote_restore_candidate_v2/README.zh.md)及[独立工程复核](tools/publication/k3_union_remote_restore_peer_v2/REVIEW.zh.md)。

## 获取与完整恢复

[联合 INDEX](../INDEX.kimi-k3-composite-v1.json) SHA256：

```text
a462bde564618f52b46b863095bfed5d2a97eb9c3ce4c730a34ac6fdad91a0f7
```

下载整个 results 分支，或完整保留 full_delivery_v5 下联合索引引用的两个 K3 目录；不能只下载新目录。恢复程序复用原公开工具，逐包读取旧包和新包，拒绝重复路径、额外文件、不匹配哈希或不完整分片。下面命令从仓库根执行，输出目录必须不存在：

```bash
git clone --branch results/portable-eval-20260908 --single-branch \
  https://github.com/tiannuo-yang/LLM_ExpGym.git
cd LLM_ExpGym
python3 -B results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909/payload/tools/publication/collection_restore_candidate_v2/restore_collection.py \
  --index results/portable-eval-20260908/full_delivery_v5/INDEX.kimi-k3-composite-v1.json \
  --sha256 a462bde564618f52b46b863095bfed5d2a97eb9c3ce4c730a34ac6fdad91a0f7 \
  --output-dir /absolute/new/k3-restored
```

工具成功退出后，根 COLLECTION_COMPLETE.json 绑定联合索引；OWNERSHIP_INDEX.json 指向每包恢复位置及复制的 member indexes。原件在对应 bundle_id/payload/<workspace-relative-path>。恢复完整字节/路径，不恢复 POSIX 所有者、mtime 或原始模式。

公开恢复不需要模型、GPU、API 密钥或原私有服务器。原恢复工具回执的 publication_performed、remote_restore_performed 固定为 false；是否实际从 GitHub 下载，由后续独立远端凭据证明，不能改写工具原回执。

## 数据与分析

- [新 raw 包](payload/collection/recovery-raw-000001/payload/INDEX.json)与[新 controls 包](payload/collection/recovery-controls-000001/payload/INDEX.json)。
- [原 K3 失败运行完整归档](../kimi-k3-original-node-failure-20260909/FULL_DELIVERY.zh.md)保留失败8项，不被恢复后的成功结果覆盖。
- [最终结果与全部反例](README.zh.md)、[最终18文件导出索引](analysis/actual_k3_fixed8_composite_export_v2_py311_final/EXPORT_INDEX.json)。
- K3 最终十个分析输出使用 **CPython 3.11.15**；GLM 字节基线使用 **CPython 3.10.12**。同一数学结果的样本标准差在两个 Python 版本间存在末位差异；原失败重放和最终正确运行均保留，不把跨版本差异改写成一致。
- 原 AN2 分析和原 relocator 只重定位公开恢复数据路径，不调用模型或重评分。最终 K3 的五个输入来自 recovery-controls-000001 下 actual_k3_fixed8_composite_export_v2_py311_final；原分析代码来自旧 controls 包。最终 OUTPUT_INDEX SHA256 为 9e9d1c767b09f916e21b273a0c8cd985a8db2b3a0a9f6a0dc64f3604c403b147。
- [GLM 已完成的 GitHub 下载、完整恢复及十输出精确重放证明](../glm-5.3-original-completed-20260909/replay_verified_v2/REPLAY_VERIFIED.zh.md)。

## 公开范围限定

467份私有新controls中，唯一未公开的是1,292 B的合成CPU测试回执 test_legacy_helpers_CPU.json。原扫描器因凭据命名的元数据字段拒绝它；这是保守规则命中，不证明已泄漏真实密钥。原文件和失败扫描留存，不改写、不按实验成绩删选，所有实验原件、模型缺答、基础设施失败及科学分母不变。公开附属证据的私有引用链并非完全自包含。

外层另有一份10,383 B清单复核回执 FINAL474_READBACK.json 被整批发布扫描以同一保守规则拒绝，已从待公开副本移至私有可恢复位置，原源文件保留。它不是归档成员或实验结果：上述66,643/466计数和联合SHA不变。冻结outer候选仍记55件，实际公开其54件；[明确缺项说明](evidence/root/ROOT_PUBLIC_OUTER_OMISSION.json)及[首次整批失败扫描](evidence/publication-scan-failed-v1/manifest.json)保留，不改写历史候选或声称全部私有引用可下载。

新raw的早期本地封装没有记录显式 RLIMIT_CORE=0:0，不能追认为符合当时完整执行门禁；原限定说明和成功字节核验均保留。发布前整批新增文件与7个tar完整成员须再经过原扫描器、四个已知密钥来源和显式 core=0:0 检查。

冻结历史报告/收据中的绝对路径及pending状态不回填修改。外层导航提供最终状态；深层历史README相对链接可能指向当时本地布局，查验应优先使用本页联合索引及完整workspace-relative原件路径。

本文件生成时：本地原件/恢复字节与联合归档前置核验已进行；全新 GitHub K3 联合恢复及最终十输出重放的实际凭据尚待追加，不能把本地通过当作远端通过。
