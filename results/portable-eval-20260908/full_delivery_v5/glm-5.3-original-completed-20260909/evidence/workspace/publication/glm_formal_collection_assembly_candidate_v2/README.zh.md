# GLM collection v2：完整实验原始数据 + 公开 controls 子集

本候选保留全部 70,520 份 GLM 实验原始文件，配以 1,114 份公开 controls。它不是完整内部审计链的公开副本：原 controls 1,115 份中，一份 4,783 B 非实验操作 receipt 不公开，原件仍完整保存在原私有 seal 中，原失败扫描也保持失败原记录。

ROOT 已独立审阅并确认这一精确排除，不修改 scanner、不替换或删改 receipt 内容，也不新增免检规则。入口为：

```text
portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/glm_public_controls_subset_v1/
ROOT_SCOPE_DECISION.json
  SHA256 90df6e9b1301211278c290676c7ee387398c487a527c2df6851a5a0146f473c3
inventory.json
  SHA256 3c321f8bbecba16cb3570bd6be04ccdc3956fdf857ed8dbb669becdd9a66726a
```

唯一未公开项为原 OP 下 `seal_operator_glm_formal_v1/invocation.json`。ROOT 决策说明：冻结 scanner 对 credential-named 元数据字段保守拒绝；独立比对确认该字段是固定操作授权描述，而非实际 credential。这里仅读决策和核其 pins，不读取该 receipt 正文、不重复判定或扫描。

| 交付范围 | 包数 | 原文件数 | 原字节数 |
| --- | ---: | ---: | ---: |
| 完整 GLM 实验 raw | 36 | 70,520 | 3,242,213,793 |
| 公开 controls 子集 | 1 | 1,114 | 224,903,100 |
| 合计 | 37 | 71,634 | 3,467,116,893 |

ROOT 的精确减集核验保留全部 153 shared 原件、17 个正式导出文件及 source_index 的 2,247 引用；被排除项不在这些分析引用内。这是上游范围证据，不代表本候选已经执行离线 AN2 完整性或异地复跑验收；这些仍须另验。原审计文件中的引用不重写，公开审计引用因此不能宣称完全闭合。

## 唯一生产差异与 CPU 检查

相对冻结 v1，`assemble.py` 只改变两行常量：controls totals 与全体 totals。所有函数 AST、36 批/末批 520、raw root、GLM schema、严格 `is True` 身份、`original-completed` 分类、5 个工具 pins、原协议及 caps 均不改。`PRODUCTION_DIFF.patch` 给出完整 2 行差异。

原 6 项 synthetic 完整沿用，仅将一个预期总量 tuple 更新；两个解释器各 6/6 PASS。仍覆盖缺批/重复/错 pin/错根、局部 proof 失败、全局原件冲突、两份 opaque 假包的完整字节复制/拒绝已有输出、以及 true 与整数 1/false 的严格区分。假 archive 不是实际 TAR，不冒充真实恢复。真实 exit/log/pins 见 `CPU_RECEIPT.json`。

v1 的全部 9 文件保持原 SHA，不覆盖、不回写。v2 停写后等待 ROOT review；本阶段没有读活动 raw 包/真实包 INDEX/原实验 payload/key，没有 actual assemble/pack/restore、模型、评分、网络、Git 或内容扫描操作。

## 实际组装仍需独立授权

沿用原 CLI：

```text
/usr/bin/python3 -B /ABS/glm_formal_collection_assembly_candidate_v2/assemble.py
  --go /ABS/ROOT_GO.json --go-sha256 EXTERNAL_GO_SHA
  --output-dir /ABS/FRESH_OUTER/payload
```

只有 36 raw 与新公开 controls 包全部闭合并获得 ROOT 完整本地 pack/restore proof 接受后，ROOT 才能签 37 行精确 selection 与独立 GO，绑定本 v2 源码 SHA。各原件路径/bytes/SHA 与完整包目录集合仍按原算法核验；任何再次改变 scope 必须新 revision/review，不能放宽常量。`full_project_complete`、publication、remote restore 标志仍为 false；实际发布和公共恢复不由本候选自证。
