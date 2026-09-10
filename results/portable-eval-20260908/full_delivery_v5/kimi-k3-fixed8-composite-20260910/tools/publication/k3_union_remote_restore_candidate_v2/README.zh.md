# K3 固定 697 + 8 union：公共恢复后逐文件 verifier 候选

本候选仅做 CPU 准备。没有运行真实 restore/post-verifier，没有读取实际 tar、实验 original/restored payload、raw、答案或 key；没有 Git、模型、评分、网络或 Slurm 操作。原 GLM/K3 工具和原 697 + 8 数据均不修改。

**v2 范围决策：新 controls 466 件 / 195,085,429 B。** ROOT 已将唯一被旧 scanner 拦截的 1,292 B `test_legacy_helpers_CPU.json` 排除出公开子集：它是 synthetic-only / 82 tests / exit 0 的非实验 CPU 收据，不是实验原件。原 467 件 private scope、首次 scan exit 1（99445 → 213ae2）、原规则和 v1 source/tests/CPU 均保留。ROOT 新 scope 为 `P/k3_fixed8_controls_public_delivery_v2/ROOT_PUBLIC_SCOPE.json`，SHA `c5a927e2996da3e2ee1b37c151253e16bdc1484ebe76402f9cc8d145e15be8e6`，本作者只读核该 scope metadata 的全文/原 pin（8ccda3），未读实际被拒文件。没有删源文件或绕过 scanner。ROOT 后续通知公开 466 件原 scan 已 PASS（77883 / bb0fe0 → f4c4aa exit 0，gate 3f26c6 exit 0，4 sources / 0 findings / 0 advisory），据此确认此 scope；本作者未重跑或独立读取该 scan payload。pack、whole INDEX 外部 pin、公开和恢复仍 pending；scope/scan 通过不是实际交付完成。部分保留证明仍引用这一私有 CPU 收据，因此不能宣称全部 private proof 引用自包含；实验原件和统计分母不减少。

## 最小复用与固定范围

基线为 `P/glm_full_remote_restore_candidate_v1/verify_restored_files.py`，209 行 / 12,412 B，SHA-256 `40e7b3af4e1d4b1e573e60ee192de19f6db9bd223515b32acbe0c8e345bc7d2b`。这里 `P=/lustrefs/users/chufan.shi/codex_space_tn/publication`。

新文件只更换固定总量、bundle ID/count/category 映射、collection 相对定位和相应分类门。原 `need/encoded/signature/path_safe/digest/load/relative/tree` 八函数、完整 per-bundle/member 校验循环逐字及 AST 均一致，CLI AST 不变；精确差异见 `PRODUCTION_DIFF.patch`。不新增 scope 参数、driver、恢复实现或 fallback 路径。

本目录 diff 是 v1 → v2 的两行常量变化；完整 GLM → union 接线差异保留于相邻 v1 的 `PRODUCTION_DIFF.patch`，其 SHA `0494d2a2f08e62b0a235fe292dcbf72e9bcbf7d839f013d4aa7b7bf3d6916f0d`。两层 diff 和直接相对原 GLM 的 AST/逐字校验共同说明复用边界。

| 分组 | IDs / category | 包数 | 原件数 | 原件字节 |
| --- | --- | ---: | ---: | ---: |
| 旧失败轮完整 run | batch-000001…batch-000033 / original-node-failure | 33 | 64,188 | 1,268,512,973 |
| 旧 controls | controls / controls | 1 | 917 | 253,018,660 |
| 新固定 8 完整 run | recovery-raw-000001 / recovery-raw | 1 | 1,072 | 34,520,799 |
| 新 final controls | recovery-controls-000001 / recovery-controls | 1 | 466 | 195,085,429 |
| union | 上述 exact IDs，无其他项 | 36 | 66,643 | 1,751,137,861 |

前 32 个旧 run 包各 2,000 件，末包 188 件。两段 run 包合计 65,260 / 1,303,033,772 B。此处“raw 包”含 run 全部原件，不是 HTTP 请求数。生产内核验 exact IDs、每个 run 包件数/category、两类 controls 各自件数/字节/category、run 总字节及 whole 总量；逐包具体字节/SHA 来自 ROOT 事先接受并外部 pin 的完整 union INDEX，后续原 member loop 再核所有成员及逐包总量。不是仅凭这几个总量接受任意另一套 collection。

本组数依据 ROOT 对原 467 私有源集合的独立核验及随后明确的单件非实验收据公开排除决定。selection mapping 的 7 个 oldreuse 已由旧包携带，不重复加入；selection 自身 11 个 sidecars、此 verifier、以后 publication/restore/replay proofs 都是 outer，不加进本 controls。后续若 scope 改变，本版本保留并另建候选，不原地悄改常量。此公开 scope 已由 ROOT 以单次新 scan 确认；新 bundle INDEX、whole INDEX 外部 pin 仍须 ROOT 验收，CPU 通过不是已公开或已完整恢复。v1 的历史 INDEX 为 `d5b880a00a67b800202c7b7f9b196f2d6bb43155519ee00a74b8c0bce16838cf`；v2 相比 v1 生产仅改两个 literal rows（controls C/B 和 whole C/B），测试仅改对应四个固定数字，原 21 测试逻辑不变。

## 精确路径与原 34 包身份

未来 `--release-root` 是 fresh clone 内共同祖先的绝对 canonical 路径：

`<fresh repo>/results/portable-eval-20260908/full_delivery_v5`

只读取其 `INDEX.kimi-k3-composite-v1.json`，不回退至旧 `payload/collection/INDEX.json` 或根 `INDEX.json`。

旧 34 行在新 union 中只给 `index` 加精确前缀：

`kimi-k3-original-node-failure-20260909/payload/collection/`

旧 original INDEX、archives 不改；bundle_id/category/sha256/file_count/original_bytes 必须与旧 34 行逐字段相同。此构建身份由 ROOT/union assembler 在 pin 新 collection 前核验；verifier 不重新发现或猜测旧 collection。原旧 INDEX 身份为 `a78227369423e71e8c4380e46416b8a4ed88464f3e8a502fe1747e7e703103f5`。新两个 row.index 的最终相对路径由已接受的 union 提供，不在本候选虚构实际 leaf 名。原 member loop 从 `COLLECTION.parent / row.index` 解析各自 bundle；复用公开 restore 的相同相对寻址。

恢复后原件仍是 `<restored>/<bundle_id>/payload/<workspace-relative-original>`。全局 owner 唯一、无父子路径碰撞；旧错误原件/费用旁账和新 8 原件都保留，不能用“有效 705”名义删旧失败。

## 复用校验边界

原 NoFollow、regular-file、100 MiB 原件上限、8 MiB metadata 上限、读前/打开/读后/路径 stat 稳定、duplicate JSON key 与 nonfinite 拒绝均保留。ns/inode 始终 Python int，本候选不经过 JavaScript 序列化。

原入口继续要求全绝对 canonical 路径，外部显式 SHA/commit，真正 CLI_EXIT 的 `actual_exit_code` 是 int 0（False 不等于准入 0），且绑定相同 collection SHA/commit。ROOT remote proof 只验其 pinned JSON 字节；Git/fresh-clone 语义由 ROOT 在实际 GO 前独立核验，不把任意 JSON 当作已重新验证 Git。输出 receipt 必须 fresh、输入树外，`xb` 写入；失败不产生成功结论，不重试/修原件。

原循环逐一核 original INDEX/member pages 与 copied metadata、全部 restored bytes/SHA、bundle COMPLETE、全局 OWNERSHIP_INDEX、collection COMPLETE、无 INCOMPLETE、精确全部输出文件集合，并最后重 hash 全部 metadata。实验文件只流式 hash、不解析答案；该工具不校验科学评分/费用解释/模型表现，也不替代别的 scanner、restore 或原 AN2 replay。原 collection COMPLETE 内 `remote_restore_performed=false` 等字段按原 schema 精确核验而非改写。

## CPU 与实际使用前件

合成 suite 保留原 14 个测试语义，新增 7 个 union 边界：只选新 union、缺失不 fallback、错误 union SHA 不用旧默认替代、新 raw 分类/计数、新 controls 分类/总量、缺新 controls、旧/新 original owner 碰撞。fake 36 包各一件一字节，仅测试进程 mock 四个数值集合，category maps 不 mock；不把 fake 36 件称为真实 66,643 件验收。两 Python 真实单次 suite exits 与所有 pins 见 CPU 收据。

CLI 不新增参数；实际待 ROOT 提供的绑定为：

- release root、restored root、全新输出 receipt 的 canonical 绝对路径；
- 接受的新 union INDEX SHA、fresh public commit；
- ROOT remote proof 的精确路径/SHA；
- 原 restore 自然退出的 CLI_EXIT 路径/SHA（实际 exit 0、无 INCOMPLETE、完整 COMPLETE）；
- 新候选完整主读/独立 peer 接受及唯一实际执行 GO。

参数顺序：

```text
/usr/bin/python3 -B <outer verifier 的绝对路径>
  --release-root <fresh repo 下 full_delivery_v5 的绝对路径>
  --restored-root <闭合 restored 根的绝对路径>
  --root-remote-proof <ROOT 原件绝对路径>
  --root-remote-proof-sha256 <ROOT 提供 SHA>
  --cli-exit <真实 restore 退出收据绝对路径>
  --cli-exit-sha256 <ROOT 提供 SHA>
  --collection-sha256 <最终 union INDEX SHA>
  --remote-commit <实际 fresh public commit>
  --output-receipt <输入树外且不存在的绝对路径>
```

这不是可执行的实际授权命令。运行时 core 0；owner 自然等唯一真实 exit，再独立读取 receipt 核结果，失败保留且不自动 retry。完整 post-restore 通过后也仍要独立完成 composite 两段 source ownership 重定位与 K3 原 AN2（明确 CPython 3.11.15）的十输出 byte/SHA 对比；本 verifier 不调用它们。外部 backend/runtime 不因此变成可独立重新推理的完整环境。
