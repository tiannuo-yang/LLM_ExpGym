# GLM collection selection：独立有限静态审查

审查者：`/root/runner_integration`。日期：2026-09-09 UTC。结论：在本次代码与闭合元数据范围内，未确认阻止 ROOT 另行采纳 selection 的关键逻辑漏洞。本记录不是 assembly、archive、恢复或发布验收，也不签发执行 GO。

## 范围与输入身份

以下路径相对于 `/lustrefs/users/chufan.shi/codex_space_tn/publication/`；SHA-256 是本次实际读取身份。

| 文件 | SHA-256 |
| --- | --- |
| `glm_full_collection_selection_candidate_v1/verify_selection.py` | `8c126bd89f744ec6c4c48bfd51301711b018025a55d2717f0ca3711cd73688ae` |
| `glm_full_collection_selection_candidate_v1/README.plan.md` | `d03e614b2dca0439d4fb3c1151a39aa3f5bfbf31554f7a3a63a8a1130448df75` |
| `glm_full_collection_selection_candidate_v1/README.result.md` | `b6f664d2ea4a007a24d709792832dda3a6332cd6d53e7c2e586a5254e47f97c7` |
| `glm_full_collection_selection_candidate_v1/CLOSED_METADATA_REVIEW.json` | `1d2c1eb31c6507991705e97a24c39250b2436c1232e4aefa15936288c8f77b08` |
| `glm_full_collection_selection_candidate_v1/SELECTION_CANDIDATE.json` | `fcbf3570d94d72340165ca08f6c67f9f58b94b4835126dbd32ecabccd8a4e12a` |
| `glm_full_collection_selection_candidate_v1/CLI_RECEIPT.json` | `6ab9fca2b71bfa39b3bc021512b63b633c200d400ec32b8074088e15ac4ece4c` |
| `glm_full_collection_selection_candidate_v1/ACTUAL.stdout.json` | `ec55ef6741dd47d68d1454792c9d9ada12949d8d291204fceb3df7d2c4e849db` |
| `glm_formal_collection_assembly_candidate_v2/assemble.py` | `5255f2f390632bd9686ce379f0868fac8ddddc0e8c2304000ee017f236d6f9f6` |

已全文阅读 verifier 与两份说明，并对照 assembler 的直接 selection 契约；没有执行 verifier、assembler、publisher 或任何测试套件。

## 有限结论与代码定位

- `verify_selection.py:122,135,152` 将实际读取限制到指定元数据，拒 symlink、特殊文件及被禁止的 payload/archive 路径；哈希读取核对前后 stat。声明的 archive SHA 不被冒充为本次重新读取 archive 的 SHA。
- `:235` 的 wait 验证核实际 PID、精确整数 exit 0、reaped、wait 返回及无 poll/异常替代；`:285` 起核定 36 组 pack/restore 的 72 个子进程记录，不以单一父进程 exit 0 替代。
- `:189` 核 37 个 bundle INDEX、288 个 member-index pages 的引用、逐 shard 限额和完整成员并集；`:298` 起核 36 个原 whole-file comparisons、批次结果与原 inventory 全局并集；controls 另核 1,114 个文件并与 raw 去重。最终是 37 bundles、71,634 files、3,467,116,893 bytes，非历史 1,115-controls 版本。
- `:399` 固定第一遍元数据 ledger 后进行第二遍 SHA/stat 核验，不在迭代中悄然扩展输入。原实际 verifier 收据记录 594 项、两遍一致；其中包含 72 child-exit、36 comparisons、37 bundle INDEX、288 member pages，而不是“37 member pages”。
- `assemble.py:43` 所需 inner selection 为精确八字段、37 个精确十字段 bundle rows，verification 为精确四字段。候选 `proposed_selection` 与之相符；外层 `approved=false` / `actual_assembly_authorized=false` envelope 不能直接作为已批准 selection，仍需 ROOT 单独采纳及新 GO。

## 本审查实际做过的独立核对

只读标准库检查 `e5505b` 实际 exit 0：核 CLI 所列四份元数据原件 bytes/SHA；stdout 与 envelope/review 对象精确相等；canonical envelope/selection SHA、原 operator 结束引用、source identity 相互绑定；37 行顺序/字段/类型/数量/bytes 合计正确；594 分组计数及报告的双遍 digest 相同。随后 `5a95ff` 再核四份核心文件 SHA 未变。

原 verifier 的实际一次 session 65434、exit 0 及 reaped 来自上述 CLI 原收据；本审查没有重复启动该程序。原 guard 首次失败、修正后的 guard 通过及保存文件 reverse-diff 首次诊断失败均保留，未将它们改写为首次全成功。

## 明确边界

本审查没有独立重读全部 594 个输入，也没有读取 tar、实验 original/restored payload、答案或 key 内容。594 项双遍结果属于原 verifier 的实际执行证据；本审查独立核的是代码逻辑及输出间绑定。日志引用仅按原契约核形状，SOURCE_SCAN 为已存在的 pinned 元数据，不是新扫描；此前全量 original/restored 字节相等仍依赖原闭合 operator 与 ROOT 证据。本记录不推导新 archive 字节验证、完整秘密扫描、远端存在性、实际恢复或最终公开交付通过。

ROOT 另告其独立核对 `027da7` 已通过；这是 ROOT 的并行事实，不计作本审查重复执行。后续实际采纳/assembly 权限与结果由 ROOT 独立记录。本审查到此停止。
