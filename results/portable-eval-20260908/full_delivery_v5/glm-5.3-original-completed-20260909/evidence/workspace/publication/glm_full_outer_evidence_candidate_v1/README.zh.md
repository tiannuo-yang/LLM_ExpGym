# GLM 外层证据：最小绑定 CPU 候选

本目录当前只完成源代码绑定与合成 CPU 测试。不是实际元数据组装、秘密扫描、发布或恢复验收；真实 FILES.candidate.json / HASH_RECEIPT.json 尚未生成。CPU_PENDING.md 保留首次准备时的历史状态，不回写。

## 冻结复用

prepare_metadata.py：15,763 B，SHA-256 `fab571b5252374afc2b247bf8db408a4a1fb778d47bbb884d7ae6223e60bd163`。

直接复用 K3 原 preparer `cd6e38d33b0230a394a06f6b99df34b9176a0e11ffe6553039ddc21025f9e72e`，完整差异见 PRODUCTION_DIFF.patch。add / need / fingerprint / hashed / write_new 五个函数源码逐字相同；main AST 结构不变，恰 6 个常量差异：两处精确总数 606→668、两个 schema、两个原状态 false→true。外围只改固定路径、批次枚举、明确证据清单和真实 SHA 绑定。无新 operator、进程或扫描框架。

保留 O_NOFOLLOW、规范真实路径、regular/<100 MiB、两遍完整 SHA 和 dev/ino/size/mtime/ctime/mode 稳定检查、外部 SHA pins、唯一排序无前缀冲突、O_EXCL 拒绝覆盖。PINS 有 54 个已知外部 SHA；其它选中元数据未来由本次实际 main 完整观察 SHA，不伪称预先已有独立 pins。CPU 步骤未核全部 668 真实输入。

## 精确范围

| 组 | 文件数 |
| --- | ---: |
| 36 批 raw proof/log，含 72 child exits | 396 |
| raw scan 每批五件＋两件总元数据 | 182 |
| raw scope 36 候选＋inventory/index/receipt | 39 |
| raw run metadata / scan controls / retained failure | 3 / 3 / 1 |
| raw ROOT proofs / delivery GO | 2 / 1 |
| controls scan / public scope / byte verification / local proofs | 4 / 2 / 4 / 5 |
| 冻结 driver/helpers/assembler 代码说明 | 12 |
| selection evidence / independent peer | 8 / 1 |
| 正式 assembly selection/GO/operator/localproof/verifier | 5 |
| 合计 | 668 |

全部目标为 `evidence/workspace/<workspace-relative source path>`，位于 GLM leaf `results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909`。不存在递归发现或 refs 自动跟随。

Controls 只保留原决定的 1,114 原件公开子集；外层选中其决定/inventory、已完成 byte verifier 四件、ROOT local proof/operator、scan acceptance/spec/manifest/lock，以及 ROOT 后续明确批准的原 pack GO / restore GO / restore COMPLETE。不读或公开私有 1,115 seal 或唯一被排除的 invocation.json；原失败扫描和私有证据不改，公开引用链不宣称完全闭合。

GLM README 的真实源文件名为 README.zh.md；controls 恢复完成路径为 restore/COMPLETE.json。原 driver 历史 pending README 保留，CPU_ADDENDUM.zh.md 一并附上，不能拿历史 pending 文字覆盖后续实际证明。

本选定集合保留 ACTUAL_METADATA_GATE.json 的真实失败与后续 v2 / ROOT 接受；selection 首次 guard 失败及后续读取诊断记录亦随原 receipts/README 保留。未重试或改写原历史失败。

## 闭合输入与不重复内容

ROOT 已报告 raw 原 operator 13206 / 895e99 实际自然 exit 0，以及 37 包 assembly 82096 / fd6c28 和 ROOT full-copy/member 后验 69405 / ea568f 均 exit 0；固定原 ROOT proofs 被纳入且 SHA 已外部提供。本 CPU 阶段不重跑这些工作、不重新检查实验字节。

原实验完成状态 true / true，来自最终封存及 ROOT 正式 selection，不能解读为完整项目已完成。Raw 70,520 / 3,242,213,793 B；controls 1,114 / 224,903,100 B；合计 71,634 / 3,467,116,893 B。Collection 已有 288 tar，tar 内每份 FILES.json 属归档元数据、不是新增实验原件；将来的 publisher 展开成员数预期是 71,634 + 288 = 71,922，仍须真实扫描证明。

这里不读/复制 assembled payload、不重复加入其 ASSEMBLY_RECEIPT / RELEASE_FILES / indexes / tar 或五个恢复工具；它们按 assembler 精确 payload 整体发布。也不加入 restored 实验原件、旧 35 项 browser 报告或新导航；这些由 ROOT 在最终 outgoing 明确组合。原 35 项须保持原 bytes/SHA，不由此候选证明已公开。

## 合成验收与下一步

同一 9 项 tests 各运行一次：Python 3.10.12 exit 0 / 308ad9，Python 3.11.15 exit 0 / ef3649。涵盖精确清单、双遍完整读取、拒绝覆盖、重复/缺失路径、范围外 pin、错误 SHA、symlink、第二遍内容变更及仅 stat 变更。每次先将 W/OUT/LEAF/groups/PINS 重绑定到测试私有 TemporaryDirectory，才调用 main；只创建和清理自有 tiny synthetic JSON，未运行 pack/restore/scanner/subprocess。测试为新候选新增，不冒称 K3 原套件或真实证据已读。

STATIC_REUSE_RECEIPT.json / CPU_RECEIPT.json 记录实际 CLI、身份和日志；原工具未改。diff 命令 exit 1 仅表示确有预期差异，不是执行失败。没有新的测试失败或重试。

经 ROOT 主读源代码/完整差异/CPU 后，须另给一次真实 metadata GO；届时唯一命令为：

```bash
/usr/bin/prlimit --core=0:0 -- /usr/bin/python3 -B /lustrefs/users/chufan.shi/codex_space_tn/publication/glm_full_outer_evidence_candidate_v1/prepare_metadata.py
```

本文件不授权执行该命令。未来仍无 key 读取/新扫描/pack/restore/Git；只允许所枚举的闭合元数据。真正 outgoing privacy scan（包含 ROOT 指定的第四份新 known-value）、公开远端恢复和离线分析重放均独立后续步骤；不能将原三-key scan 当作这些新步骤已完成。
