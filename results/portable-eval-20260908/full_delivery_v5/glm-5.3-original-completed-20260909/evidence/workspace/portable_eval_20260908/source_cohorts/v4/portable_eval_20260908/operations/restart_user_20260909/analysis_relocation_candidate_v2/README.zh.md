# AN2 路径索引迁移候选 v2

v2只修复独立peer在实际使用前发现的工具合同缺口：POSIX `Path('//')`的anchor不是单根`/`，原v1未拒绝双根。现在`absolute()`显式要求anchor恰为`/`，并拒NUL与ASCII控制字符（0–31、127）。原v1源码、日志及peer反例保留，未证明当前ROOT的单根实际计划受此问题影响，**未改任何正式实验或真实索引**。原10项测试AST不改，追加1项边界回归；v2最终双Python日志单列，不覆盖v1失败/成功日志。

这是**原AN2/exporter作者**实现的离线路径适配器，不是fresh科学审阅者、恢复器、评分器或exporter。仅生成两件新文件：`source_index.relocated.json` 与 `MAPPING_EVIDENCE.json`；原manifest/records/oracle/input_pins/source_index、源原件、三份分析源码都不修改。没有模型、API、网络、key、Git或Slurm接口，也不会import/call AN2。

目前仅使用本目录的tiny synthetic restored-layout fixtures；**未读取任何真实K3/GLM payload、实际pack或远端恢复原件**。CPU通过不能称异地恢复或分析重放完成。真实路径与外部pins待ROOT验收实际远端restore后提供。

## 单一输入与调用

调用者提供一个UTF-8 JSON spec，并从独立可信渠道提供它的SHA；不能从任意新改spec自算SHA后冒原发布许可。此处没有新增GO/注册体系。

```bash
python3 -B /ABS/analysis_relocation_candidate_v2/relocate.py \
  --spec /ABS/externally_pinned_relocation_spec.json \
  --sha256 EXTERNALLY_VERIFIED_SPEC_SHA256 \
  --output-dir /ABS/a_fresh_derived_index_directory
```

API：`relocate(spec_path, spec_sha, output_dir)`。路径须绝对、规范、无symlink；输出父目录需已存在，输出目录不存在且与restore根/输入spec不重叠。失败不重试、不接管、不删partial输出。

spec恰好这些字段；下例只是形状，SHA占位符会拒绝，不是实际可执行输入：

```json
{
  "schema": "analysis-source-relocation-v1",
  "old_workspace": "/ABS/OLD_WORKSPACE",
  "restore_root": "/ABS/FRESH_RESTORE",
  "collection": {
    "index_sha256": "EXTERNAL_SHA_OF_COLLECTION_INDEX",
    "ownership_sha256": "EXTERNAL_SHA_OF_OWNERSHIP_INDEX",
    "complete_sha256": "EXTERNAL_SHA_OF_COLLECTION_COMPLETE"
  },
  "original_inputs": {
    "manifest": {"member": "FULL_WORKSPACE_RELATIVE/export/manifest.json", "sha256": "EXTERNAL_SHA"},
    "records": {"member": "FULL_WORKSPACE_RELATIVE/export/records.json", "sha256": "EXTERNAL_SHA"},
    "oracle": {"member": "FULL_WORKSPACE_RELATIVE/export/oracle.json", "sha256": "EXTERNAL_SHA"},
    "input_pins": {"member": "FULL_WORKSPACE_RELATIVE/export/input_pins.json", "sha256": "EXTERNAL_SHA"},
    "source_index": {"member": "FULL_WORKSPACE_RELATIVE/export/source_index.json", "sha256": "EXTERNAL_SHA"}
  }
}
```

五个member由原collection归属解析为 `restore_root/<bundle_id>/payload/<完整member>`；不另接收可能指向错文件的basename目录搜索。source_index每个旧绝对路径必须严格位于显式old_workspace之内，其relative_to(old_workspace)必须**原样**命中唯一member。若发布时namespace不是完整workspace-relative path，此版本直接拒绝，不能去前缀、模糊搜索或以相同SHA替代归属。

## 精确验证范围

| 对象 | 本工具实际核什么 | 不由本工具重新证明什么 |
| --- | --- | --- |
| collection/ownership/collection COMPLETE | 三件原bytes对外部pins；schema、bundle顺序/ID、计数、completion中的index/ownership SHA；拒绝INCOMPLETE | 外部pin可信性、此前restore是否真正由指定程序执行 |
| 每bundle copied INDEX、每个member page、bundle COMPLETE | 原SHA/bytes、全member path/类型/范围、全局去重/前缀冲突、bundle归属、总数/bytes；按原common.py的canonical-row编码复核COMPLETE inventory hash | 不读TAR、SOURCE_SCAN或重跑restore/scanner；不对全payload做第二次完整byte扫描 |
| 原五份分析输入 | 必须是显式member且SHA/bytes匹配；input_pins三SHA与manifest/records/oracle原bytes一致；records的manifest/source tree及manifest的oracle SHA对应 | 不验证全部科学矩阵或oracle正确性；不重新打分 |
| records.source_sha256并集 | 冲突SHA拒绝；原source_index key集合必须恰等该并集；旧路径不能越界/重复别名 | 不从manifest补结果、不删unknown/error、不另选样本 |
| 每个被引用的恢复source | 按精确old-relative-member→bundle→实际path流式读取**完整原bytes**，核SHA与member声明bytes | 不读取未引用的历史raw、其他模型文件、全DB；不把同内容不同path视作同一来源 |

因此，必须先由ROOT/调用者完成并接受**实际公共restore的全量完整性检查**。这里明确依赖此前的全payload验收；`all_collection_payload_bytes_rechecked=false`不是缺失文件被修好。合成测试特意删除一个未被分析引用的payload而迁移仍能成功，以锁定此有限边界，不能拿本工具代替restore的exact-tree或secret检查。

完整member metadata均核对，但新证据只展开分析所需key→旧路径→member→bundle→新路径及SHA/bytes，不复制全项目路径表；完整项目raw/失败成本仍由原bundle交付。原件在读取时核inode/size/mtime/ctime，结束复核已读路径stat；这是稳定性guard，不是抗恶意并发的原子快照，不保证捕获change-and-revert或验证后的修改。

限制：512 bundles、4096 shards/bundle、256 files/shard；collection/ownership/COMPLETE/每member page默认8MiB；五输入与被引用whole-file source单件≤100MiB；保留的元数据读取累计≤256MiB；单件派生输出≤100MiB。仅支持已完成whole-file collection，不支持large-file pieces重组或自动扩限。元数据字节上限不是Python DOM/RSS上限；没有额外扫描全部包。多文件写入不是原子事务，异常可能留下partial新目录；必须两输出齐全并核派生索引SHA，不能只见目录就称成功。CLI失败只打印固定规则，不打印异常/内容。

## AN2 三源码相对闭包：另一步，不自动执行

原布局与SHA仍是：

| 相对 `ANALYSIS_ROOT` 的文件 | SHA256 |
| --- | --- |
| operations/restart_user_20260909/analysis_candidate_v2/analysis.py | 5df8525973261d61b5c3c373945129db22979131e6ce3b586c8913efeed256bf |
| design/formal_export_candidate/converter.py | 0261660a38d80c9135efc498f11580ef3fea26de00e6061824e9c9380662547f |
| design/formal_matrix_candidate/planner.py | 13914a8341765d0c0ed75812d9b79d2281478b7fc82accef64deaa70a5ead68a |

若三者恰在同bundle保留上述共同根，可直接指向该恢复根。若分散在不同bundle，后续可按OWNERSHIP完整member逐一定位这三件，在**另一个全新**ANALYSIS_ROOT按表中相对布局复制原bytes并核原SHA；不得扁平化、替换planner为7f4ff5或覆盖原恢复目录。这里只给建议，本工具不复制源码、不创建此代码目录，也不核当前实际代码交付闭包。

迁移后由用户另行执行原AN2 CLI，沿[既有说明](../analysis_relocation_notes_v1/README.zh.md)传原manifest/records/oracle/input_pins和新source-index，输出另一个fresh目录。此举只重放已报告分数的描述性分析，非重新评分。还须比较AN2新输出与原发布分析的全部表/JSON；本工具不自动比较，也不将fresh_post_analysis_audit升级。

## 本次CPU回执

`test_relocate.py`仅构造自有小fixture，不运行真正restore或AN2。原10项涵盖正常CLI、不同bundle同basename/同bytes仍正确归属、外部pin拒绝、key缺失/额外/冲突、旧root越界/不存在/别名、ownership错配、跨bundle重复/前缀、选中source变字节/symlink、输入pin/INCOMPLETE拒绝，以及有限读取范围/已有输出拒绝。fixture里的COMPLETE是合成测试结构，不是真实准入证据。

首轮双Python各9通过1fixture构造错误：同一测试先造重复成员，再复用目录造前缀文件，碰到先前目录而未到生产拒绝分支。现把第二反例换成该测试自己的新目录；原失败日志保留。上述首轮构造失败及其日志属于已保留v1历史。v2最终11项测试日志、exact生产diff及旧新版pins见CPU_RECEIPT.json。作者候选验收不等于ROOT/peer接受，实际迁移仍未执行。
