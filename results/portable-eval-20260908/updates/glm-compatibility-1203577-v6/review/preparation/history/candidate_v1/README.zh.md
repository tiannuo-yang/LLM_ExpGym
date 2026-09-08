# GLM compatibility v6：仅本地发布准备

本候选不是发布 GO、正式矩阵结果或项目最终验收。ROOT 已确认 GLM development 的 15/15 个任务闭合，并接受 v5 实际协议审计；本轮只冻结目录项/大小/stat 身份，**不读取模型 raw 的内容、不解释成绩、不生成成绩表、不读取 key、不执行安全扫描、分片、恢复或 Git**。`SCOPE.json` 仍为 `approved=false`，绝不能当作可公开的安全扫描结果。

ROOT 选择保留完整原运行时验证清单 `validation_v6.json`（27,156,392 B），以便独立核验；它是元数据原件，不是 env 或权重 payload。本候选不能因大小删去失败、截断、零字节原件或诊断。

## 固定范围

所有路径相对 workspace `/lustrefs/users/chufan.shi/codex_space_tn`。以下缩写只用于阅读；机器清单逐文件保存完整相对路径。

- `OLD`：`portable_eval_20260908`
- `NEW`：`OLD/source_cohorts/v4/portable_eval_20260908`
- `OP`：`NEW/operations/development_runs/glm_compatibility_1203577_v6`
- `PHASE`：`OLD/serving/phase_candidates/gumbel_midpoint_v3`
- `RUN`：`PHASE/runs/1203577`
- `S`：`RUN/glm_compatibility`
- `STOP`：`RUN/operator_stop_glm_v1`

| 原件组 | 文件数 | 字节 |
|---|---:|---:|
| 完整 OP，包括 real_run、dry、失败候选、fresh_roles、原 timing review 与全部控制证据 | 1,011 | 127,233,746 |
| `OLD/review/development_protocol_v5` 当前完整封存源码、tests、修复历史、CPU、actual audit、supplement | 50 | 3,796,684 |
| `OLD/review/development_protocol_v5_peer` 当前三个文件 | 3 | 428,496 |
| `OLD/review/development_protocol_v4_preflight_failure_20260908` | 1 | 2,873 |
| STOP 全部固定原件，包括 immutable controller stop 前缀 | 26 | 41,701 |
| S 的 11 个固定 metadata/operator/diagnostic 子目录 | 183 | 1,171,271 |
| 96 个明确单文件：S 根部 80、PHASE 源码 12、seq2 命令 2、v5 ROOT acceptance 1、runtime manifest 1 | 96 | 34,194,817 |
| 合计 | **1,370** | **166,769,588** |

其中 OP/real_run 为 809 文件、123,055,838 B；这里只统计磁盘文件，不把文件数当调用/样本数。全范围包含 39 个零字节原件。完整名单及 inode/size/mtime 在 [SCOPE.json](checks/metadata_v3/SCOPE.json)。目录在以后 seal 前后必须仍是同一精确集合；任何新增、缺失、替换或 stat 改变均停下，不自动追加。metadata_v1/v2 保留开发历史，三版 SCOPE 字节一致；未来只使用 v3 的源码绑定 GO template。

11 个 S 子目录固定为 `metadata_v1`、`metadata_post_development_v1`、`operator_metadata_v1`、`operator_metadata_post_development_v1`、`memory_io_snapshot_v1`、`nonblocking_stack_snapshot_v1`、`progress_delta_snapshot_v1`、`readonly_prefetch_trial_v1`、`readonly_state_snapshot_v1`、`readonly_state_snapshot_v2`、`readonly_state_snapshot_v3`。未递归打包整个 RUN/PHASE/worktree。

ROOT 绑定的 `STOP/closed_originals.json` 包含 31 个终态日志/命令/exit 文件和 12 个来源文件；prepare 只读取这一个控制 JSON 取得绑定，其他模型/日志原件本轮仅 stat。它的 `controller_prefix_after` 指向仍会增长的 `RUN/events.jsonl`，**不能**按整文件发布；唯一纳入的是 ROOT 独立复制的 `STOP/controller_events_through_stop.jsonl`（1,940 B，SHA `c33c18f07f2e10fa5d9bd37d018c7c113692d12e05d4c960e0f043ea9da96357`）。其余 ROOT SHA 在清单中是外部验收输入，尚不冒称本轮对模型 raw 作过逐 SHA 复验。

## 明确排除与声明边界

- 不收 `S/private/`、`router_api_key`、其他凭据；不收 checkpoint 权重、env/venv/cache、数据集 payload、整个 runtime 或 dirty source tree。
- 不收 `RUN/events.jsonl`、K3 seq3 加载/后续运行目录、其他活动输出、旧 B/C 或 A21 的重打包副本。
- 9 个 GLM srun 子进程退出码均为 **137**，原因 `explicit_ROOT_operator_stop`。ROOT 记录 remaining_children=0、无 stop timeout；不能改成 exit 0、不能称全部优雅退出，也不能把它升级为设备内存/KV cache 的逐字节清空证明。Slurm allocation 的后续用途不在本 checkpoint。
- GLM development 闭合不等于 K3 已执行、不等于 M/R 正式矩阵完成或 formal reuse 被批准。M/R 冻结前不渲染/解读成绩方向；已有原结果/原 timing 文件仍完整保留。
- v4 preflight 失败、v5 修复原件及其审计归因不改写。source 身份来自原 plan/manifest/receipt，不按本机新 HEAD 重新贴标签或重打 dirty tree；未来 source commit 导航必须保留真实来源。
- 不沿用 B/C 单一 prose 例外。任何 GLM 命中原严格扫描规则都保留首次失败并报 ROOT，不能自行改原 JSON、增 allowlist 或静默遗漏。

## 现有入口与顺序

仅新增 [prepare.py](prepare.py) 与 metadata-only tests；原 `publication/validate_bundle_v2.py`、`publication/shard_delivery_candidate_v2/{common.py,pack.py,restore.py}` 均 SHA 固定且不改。默认压缩片 ≤48 MiB、展开 ≤256 MiB、单原件 ≤100 MiB、每片 ≤256 文件、索引 ≤8 MiB；超大原文件拒绝，不切割、截断或摘要代替。当前最大原件是上述 27 MB manifest，但**压缩大小、分片数和恢复成功尚未实测**。

已执行的 metadata-only 验证命令：

```bash
python3 -B -m unittest discover -s publication/glm_compatibility_1203577_v6_candidate -p test_prepare.py -v
python3 -B publication/glm_compatibility_1203577_v6_candidate/prepare.py verify --scope publication/glm_compatibility_1203577_v6_candidate/checks/metadata_v3/SCOPE.json --scope-sha256 ac5bb183bdf42d67fa26a84f21ce3d186f3d3dc412c9af31e0101e16285f2a4b
```

以下是**未来命令模板，当前不得执行**。ROOT 先审 source/scope，独立签新的 local-scan GO（不是 publication GO），把 template 的 false 改为明确授权并给外部 SHA。prepare 核 GO/自身源码/scope 后，才从固定 `S/private/router_api_key` 读入内存；不打印、不 hash、不复制 key。该 GO 由 ROOT 在独立路径签发，不能修改旧 template 冒充已经接受。

```bash
python3 -B publication/glm_compatibility_1203577_v6_candidate/prepare.py seal --scope publication/glm_compatibility_1203577_v6_candidate/checks/metadata_v3/SCOPE.json --scope-sha256 ac5bb183bdf42d67fa26a84f21ce3d186f3d3dc412c9af31e0101e16285f2a4b --root-scan-go ROOT_EXACT_NEW_SCAN_GO.json --root-scan-go-sha256 ROOT_EXTERNAL_GO_SHA --output-dir publication/glm_compatibility_1203577_v6_candidate/checks/seal_v1
python3 -B publication/shard_delivery_candidate_v2/pack.py --manifest publication/glm_compatibility_1203577_v6_candidate/checks/seal_v1/lock.json --manifest-sha256 ROOT_REVIEWED_LOCK_SHA --workspace /lustrefs/users/chufan.shi/codex_space_tn --output-dir publication/glm_compatibility_1203577_v6_candidate/checks/pack_v1 --secret-file portable_eval_20260908/serving/phase_candidates/gumbel_midpoint_v3/runs/1203577/glm_compatibility/private/router_api_key
python3 -B publication/shard_delivery_candidate_v2/restore.py --index publication/glm_compatibility_1203577_v6_candidate/checks/pack_v1/payload/INDEX.json --sha256 ROOT_REVIEWED_INDEX_SHA --output-dir publication/glm_compatibility_1203577_v6_candidate/checks/restore_v1
```

seal 先做已接受 common 的加严扫描，再由**原 v2 scanner**完整 seal。未来 pack 自己重新严格 scan 所有原件；恢复器先验 COMPLETE/INDEX/精确文件集合，再恢复全部相对路径、原字节与 SHA，拒绝已有目标、链接、重复/缺失、被篡改 header。还需逐片独立恢复，并把完整恢复的 1,370 条 bytes/SHA/path 再直接对原件校验；public restore 不需要真实 key，发布者审核会另用 ROOT 授权的内存 key 比较。

后续 public capsule 最小结构：中文导航 README、精确原件/来源索引、scan/lock/ROOT acceptance、完整 `pack_v1` wrapper（COMPLETE、INDEX、SOURCE_SCAN、分层 indexes、全部 shards）、可离线运行的上述冻结 scanner/common/restore 及来源 SHA。这些支持文件也必须逐文件扫描并纳入最终公开 manifest；本轮 scope 是原件集合，不是已生成的公开文件集合。不得只发布 CSV/摘要，不把当前 metadata snapshot 当最终 lock。当前不新增成绩 CSV。

## 未来 Git 追加边界（尚无授权）

只允许未来单独 GO 指定 `git@github-tn:tiannuo-yang/LLM_ExpGym.git` 的 `results/portable-eval-20260908` 分支，预期 parent `0220353cd0330c55494057a1f9d9782c229890f4`，追加 `results/portable-eval-20260908/updates/glm-compatibility-1203577-v6`。现在没有 Git/网络动作，也没有假定远端未变。

复用 B/C 的 append-only **流程**，不直接执行硬编码旧 B/C 58 文件的 publisher：ROOT 先接受最终 capsule 精确文件/字节/SHA，再另发 branch/path/parent 的 GO；fresh ls-remote/fetch 不符则停止；只暂存最终 manifest 的精确新增文件，旧 0220353 全树 path/mode/type/oid 保持不变。单次成功 commit/push 后 fresh bare 验新全部 blobs 与旧全树。不开 Release/API、tag、PR、force 或 main/source 写入；Git SSH 身份不推定 Release API 权限。
