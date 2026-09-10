# K3 fixed8：最终 controls 集合候选

最终有限 membership 已闭合；随本目录最终 INDEX 生效 STOP-WRITE。这仍是 candidate=true、approved=false，不是发布 inventory 或 scan/pack/Git 授权。独立 post-report review 与 ROOT 最终科学验收已各自作为原始闭合文件纳入；最终公共 restore verifier、Git/restore/AN2 后续证明按 ROOT 决定放在 outer 范围，不递归并入此清单。

## 最终精确清单

CANDIDATE_MAPPING.json：474 条唯一完整路径，467 条新增 controls / 195,086,721 B，7 条精确旧 owner 复用 / 8,580,841 B；总计 203,667,562 B。SHA c2a02c1311ddf4e7dc8cd5e02b39d4bfc199666ed5043657590ed9849a940bb9（433,878 B）。

相对下方467准备快照，只增加报告后独立复核6件 / 71,126 B，以及 ROOT 最终科学接受1件 / 5,493 B；原467 entry对象全部保留。ROOT有界闭合快照从48增至49件，新增的正是最终科学接受。原v2的375条仍完整对象不变，总增量99条，不按结果质量筛选。

- post-report INDEX：eb54798d1d8c01ae1e675ed3b141d74ba8ac8e9930eb355110d435f9fde68a48 / 1,449 B。
- ROOT FINAL_SCIENTIFIC_ACCEPTANCE：e04109b93ae6d283fe3016c3d6968fec6141dbd03b4be67a9ad6cc4e92608bd2 / 5,493 B。

这两项是有限科学与成稿后复核接受，保留49项负性能、旧63未知费用、GLM原start本次未独立复读、非盲/非IID/无显著性等限制；都没有宣称新K3公开交付完成。原报告和各历史INDEX中的pending状态不倒写；后续真实门用单独文件并列。

## 已闭合的准备快照

PREPARATION_MAPPING.json：467 条完整 workspace-relative 路径，460 条新增 controls / 195,010,102 B，7 条旧 owner 复用 / 8,580,841 B。该快照文件 SHA 为 0f4207d53f38481a625d48795b0bf8f555c28a29628128162194f0bd1762072c（426,372 B）。

从冻结 v2 的 375 条完整 entry 对象逐项原样保留，再增加 92 条：

| 增量组 | 文件数 |
|---|---:|
| 最终 Python 3.11 composite export | 18 |
| 固定8科学审阅 | 12 |
| 最终严格不变量审阅 | 5 |
| Python 3.10 严格失败证据 | 3 |
| 原预定严格不变量 BASELINE | 3 |
| 原 v2 选择与 peer 历史记录 | 14 |
| 冻结双模型报告（含4历史件） | 14 |
| ROOT 当前48件中尚未纳入的闭合记录 | 4 |
| ROOT 精确授权 raw 本地 pipeline controls | 19 |

全部旧375条、新92条与原65105 ownership 已交叉核实。7条复用必须完整 path、bytes、SHA 同时相等；同path内容冲突拒绝。不同path即使字节相同仍各自保留。原 v2 exact14、原所有实验结果、失败记录均不修改。

## 最终产物和历史失败严格分开

原 Python 3.10 export exact18/75,085,889 B 仍保留，明确标记 historical_strict_failure，不充作最终科学依据。新的 Python 3.11 export exact18/75,085,881 B 单独保留，EXPORT_INDEX SHA fc68a5a057c45056924b17b91f054311d6cd43dc8174da85892265f8d7758f86。

严格审查文件保留原 BASELINE 以及首次未通过、最终通过三个阶段，不能用 process exit 0 代替 strict gate。科学审阅和不变量审阅是各作者独立的已有证明，本选择仅核文件身份，不重算指标、不重新评分，也不将其冒充最终报告完成后的审查。

报告自身冻结 INDEX 的4件历史材料继续完整保存：AUTHOR_CHECK_FIRST_ERROR.txt、AUTHOR_NUMERICAL_CHECK.py、NUMERICAL_EXTRACT.py310_candidate.json、PREPARATION.zh.md。该报告的原 pending 声明不改写；后续审查与 ROOT 接受将单独并列。

## raw 交付范围和执行限制保留

新 RUN 的 1,072 文件 / 34,520,799 B 及其 raw bundle13 由另一交付范围所有，controls 不重复、不读取正文。本次只读取 accepted seal 的 namespace metadata 来排除重叠。

raw 本地交付只纳 ROOT 明确的19个非payload路径：14个顶层控制文件、scan manifest/lock、restore COMPLETE，以及两个 batches candidate metadata。没有递归 local_restore/payload 或 bundle 目录。

ROOT_EXECUTION_QUALIFICATION 明确保留原 operator 用 CPU affinity 代替显式 RLIMIT_CORE wrapper 的未满足义务：full GO compliance=false；ROOT_LOCAL_BYTE_ACCEPTANCE 的 byte restoration=true 是不同结论。不能声称这次本地 pipeline 满足全部原 GO 或已通过公开交付；完整 outgoing 在 Git stage/push 前仍需另行显式 core=0 的原四来源扫描。

## 实际检查边界

准备核验 session59363：7b8340 启动、6df328 自然 exit0。共763个唯一已明确非secret metadata/control/source/export refs / 224,993,600 B，每次 SHA/bytes/stat 核验，最后对同一已准入集合全部重 hash。原公开296份 metadata 重建65105个唯一 owner；controls、旧owner及新 RUN 路径联合无前缀冲突。

17个最终 export 子文件仅流式读字节核 SHA，不解析回答或科学值。确实重新读取7个旧 owner 所有的控制/代码/execution原件，因此不能声称“没有读任何旧 member 字节”。未读取原 raw、tar、new RUN1072、local_restore payload、密钥或权重；未运行模型、scorer、Slurm、网络、scan、seal、pack、restore 或 Git。

仅按冻结 INDEX 列出的有限文件/有限父目录核 exact pathset；ROOTDIR 仅当时48个已获授权的 closed regular files。没有递归 WS/OP/serving，也没有无界追踪 input refs。mutable OP/PLAN、private/credential、venv/checkpoints、.pkl/归档 payload 排除。

本目录及独立 peer 自身的 sidecars 由 ROOT 最终明确 outer 纳入，不能让 mapping 自引用自身 SHA。当前总 delta/bundle/最终联合数保持未定，不声称包含离线重 serve 所需权重、数据后端或完整环境。

## 最终只读核验与剩余交付门

最终构建 session50336：1cbfc7 启动、722e73 自然 exit0。770个唯一已准入 refs / 225,070,219 B 全SHA/bytes/stat核验、末尾再次重hash；最终474文件全部实际字节核对。cd9243另核落盘mapping的SHA与字节。PREPARATION467与原v2的375对象全保留，18组不同路径同内容继续保留。

独立 peer 从旧296 metadata重新重建完整65105 ownership，独立核375→467→474、分组、历史角色、旧owner与不重复/缺项拒绝；只读metadata，未代替作者对474控制原件的全字节核验，也未读取新RUN成员namespace。具体边界和真实工具回执见 peer_review/INDEX.json 与 CHECKS.json。

报告后复核与 ROOT 科学门现在已纳入，不再等待这些文件；仍须 ROOT 明确最终 controls inventory，另行 scan/pack/联合公开恢复与AN2回放。本474清单不含本目录及peer自身sidecars，不能把474直接当最终delta数。原raw1072、raw bundle13与后续outer verifier/发布证明各自归属明确，不能重复。

PREPARATION_MAPPING.json / PREPARATION_CHECKS.json 永久保留其当时pending状态；最终使用CANDIDATE_MAPPING.json与本目录INDEX，不回写历史。
