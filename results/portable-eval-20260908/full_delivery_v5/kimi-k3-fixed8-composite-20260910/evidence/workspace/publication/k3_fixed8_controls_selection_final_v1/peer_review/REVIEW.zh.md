# 最终 K3 controls 候选：独立 metadata 复核

结论：PASS_BOUNDED_METADATA_SELECTION_REVIEW。针对冻结 474 项候选，未发现阻断性的路径归属、增量遗漏或索引绑定问题。该结论不是 ROOT 发布授权、全项目完成、公共恢复或 AN2 回放通过，也不是重新计算科学结论。

## 精确对象与实际检查

候选 CANDIDATE_MAPPING.json：433,878 B，SHA c2a02c1311ddf4e7dc8cd5e02b39d4bfc199666ed5043657590ed9849a940bb9。准备快照 PREPARATION_MAPPING.json：426,372 B，SHA 0f4207d53f38481a625d48795b0bf8f555c28a29628128162194f0bd1762072c。

- 474 项 = 467 项新增 / 195,086,721 B + 7 项旧 owner 精确复用 / 8,580,841 B。
- 冻结 v2 的 375 个 entry 对象和本轮准备的 467 个 entry 对象均逐字面保留；375 到最终新增 99 项。
- 准备到最终只新增 post-report 6 件 / 71,126 B 和 ROOT 最终科学接受 1 件 / 5,493 B，共 7 件 / 76,619 B。ROOT 闭合列举由 48 变为 49，唯一新增为 FINAL_SCIENTIFIC_ACCEPTANCE.json。
- 从固定旧 collection、34 个 bundle INDEX、261 个 member page 共 296 份 metadata 重建 65,105 个唯一 owner / 1,521,531,633 B。完整 path、bytes、SHA 和丰富 owner 的 bundle/page 引用逐项核对。
- old + controls 的 65,572 个路径无重复归属或文件/目录前缀冲突；18 组不同路径但相同内容的文件全部保留，不按 SHA 合并。

准备检查实际 68080b exit 0（2.054106 s）；最终检查实际 4922f4 exit 0（2.099563 s）。最终检查实际读取的 308 个唯一 metadata refs 均在末尾再次按 SHA/bytes/stat 核验。该集合是两个候选 mapping、继承 v2 mapping、旧 296 份 metadata、8 个组 INDEX 和 ROOT 科学接受 metadata；不是对 474 个所选原件正文的全字节独立复核。

作者声称实际核验 770 refs / 225,070,219 B，本 peer 核对其计数及字节算术，未替代作者读取全部原件。作者实际回执由其 CHECKS 保存，本 peer 不引用尚未冻结的 CHECKS/顶层 INDEX，避免闭环。

## 分组与历史材料

按每个冻结 INDEX 的自身加 children，核对精确路径集合和每条 bytes/SHA：v2 历史选择 14、最终 py311 export 18、科学审阅 12、最终严格不变量 5、py310 失败 3、原严格 BASELINE 3、最终报告 14、报告后复核 6。另核 raw 本地 controls 明确 19 条、ROOT 当前明确 49 条；本 peer 没有枚举 ROOT 实际目录。

旧 py310 export 18 项继续标记为历史失败材料，不作为最终科学 export；最终 py311 18 项另列。不同路径即使内容相同也各自保留。此处仅验证角色和身份，不重新验证浮点原因或数值不变量。

最终报告 9 个有效 children 与 4 个历史 children 精确、不相交地覆盖 13 个 children；历史件完整保留：

- AUTHOR_CHECK_FIRST_ERROR.txt
- AUTHOR_NUMERICAL_CHECK.py
- NUMERICAL_EXTRACT.py310_candidate.json
- PREPARATION.zh.md

这里的 PREPARATION.zh.md 是冻结报告已选历史件，不能按名字误排除。旧 INDEX 的 pending 字段保持原貌，后续真实门另用新冻结文件绑定，不回写历史状态。

## 科学门仅核 metadata 交叉绑定

post-report INDEX eb54798d1d8c01ae1e675ed3b141d74ba8ac8e9930eb355110d435f9fde68a48 / 1,449 B 精确绑定报告 INDEX aa2f55e3b42d179e505603ce2f4870c56582e5ec7152ad901f355729b43ff854，声明 bounded pass / blocking 0。

ROOT FINAL_SCIENTIFIC_ACCEPTANCE.json e04109b93ae6d283fe3016c3d6968fec6141dbd03b4be67a9ad6cc4e92608bd2 / 5,493 B 的 issuer/accepted 与 5 个 refs 已核对：报告、报告后复核、科学审阅、最终严格不变量及最终 py311 export。它明确是 custom study 的有界描述性接受，不是普遍优越、paper-exact 复现或已验证显著性。本 peer 阅读这些接受声明但没有独立重算或背书其中全部科学数字。

公开 union、fresh whole restore、public AN2 replay、full project complete 均仍 false；后续四来源扫描显式 core=0 要求保留。原报告仍有历史 pending 并不覆盖新 ROOT 接受，科学接受也不覆盖交付门。

## 严格范围与保留失败

未读取实际新 RUN 的 1,072 个成员名称或正文；66,644 仅为已独立核出的 65,572 加声明的 1,072 的算术检查，同时验证 controls/old 路径与声明 RUN 根前缀隔离。完整 new RUN namespace 验证由作者负责，不能把本 peer 算术称为 whole union ownership 证明。

实际读取了所选 INDEX 和 ROOT acceptance 这些 metadata/control 成员；“未读 member body”专指未打开组内科学/运行/raw payload 正文，绝非“未读任何所选文件”。未读取 17 个科学 export 子文件、raw bundle13、raw/restore payload、answers、密钥、权重、活动 PLAN；未运行模型、API、Slurm、网络、Git、scan、seal、pack、restore 或 AN2。

815b7b exit 0 的 5 个全假规则例验证：同 path SHA 冲突拒绝、同 path bytes 冲突拒绝、闭合组缺项拒绝、额外项拒绝、不同 path 同内容不合并；另有 exact reuse、unknown bytes 不可 reuse 和集合顺序无关的正对照。这是独立规则演示，不是对生产 packaging driver 的测试。

首个 post-report 索引调用使用不存在的 python，502c76 exit 127，在读文件前失败；定位 /usr/bin/python3 后 e0e2af exit 0。原失败保存在 FOCUSED_RECEIPT.json，候选未因该错误更改。README 与 PREPARATION_CHECKS 全文读回 6075fb exit 0，内容与上述范围一致。

## 封存边界

本 peer 只写本目录的证据文件。474 mapping 不含本目录或作者当前目录的自身 sidecars；这些由 ROOT 后续明确 outer 纳入，避免自引用 SHA。最终 delta/bundle/composite 数仍 null。本目录 INDEX 仅绑定已冻结输入和自身 children，不绑定作者未来 CHECKS/INDEX；作者可单向引用本 peer INDEX。

