# K3 composite：浏览版 exact-copy 候选

状态：`STOP_WRITE_METADATA_CANDIDATE_PENDING_ROOT_COPY_GO`，`approved=false`。只创建本候选映射和说明；未复制文件、未操作 Git/网络、未扫描/打包/恢复、未读 key 或原始 raw/压缩包内容。ROOT 的新导航 README 不在本 copy set，不能覆盖。

目标 leaf：`results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910`。全部源以 OP 相对路径镜像到 `analysis/`，**不改源报告任何字节**；特别是 `source_acceptance_v5_final.json` 位于 `analysis/` 根，而不是额外组目录。

## 精确范围

**75 件 / 77,044,594 B**，最大单文件24,707,022 B。每件 exact source/target/bytes/SHA 都在 `MAPPING.candidate.json`。

| 组 | 件数 | bytes |
| --- | ---: | ---: |
| 最终 CPython3.11 export | 18 | 75085881 |
| fixed8 最终报告原组 | 14 | 294735 |
| 新26科学/289usage复核 | 12 | 565372 |
| composite严格不变量 | 5 | 43734 |
| 旧双模型报告完整组（历史） | 6 | 134879 |
| 旧成稿后复核完整组（历史） | 5 | 50889 |
| 新成稿后独立复核完整组 | 6 | 71126 |
| 有限链接补充8件＋ROOT最终科学接受1件 | 9 | 797978 |

最终 export18 的大 JSON 全部保留，不抽取摘要代替。原 raw dump 仍由归档提供，浏览映射不展开它们。新 post-report 以 `eb54798d…` INDEX STOP-WRITE exact6 为准，不沿用此前约5件的估计；ROOT有限科学接受为 `e04109b9…` /5493B，单独映射到 `analysis/k3_recovery_root_v1/FINAL_SCIENTIFIC_ACCEPTANCE.json`。这些新接受不用于倒填冻结报告里的历史 pending、失败或作者阶段状态。

元数据实际核验：`59ab48`（base54）、`269c57`（ROOT批准的历史14）、`8d7f75`（链接）、`85f809`（post-report6）、`9988cf`（ROOT接受1），均真实 exit0。按每组 INDEX 完整列出的文件核实际 SHA/bytes/稳定stat和exact文件集合；没有沿 INPUT_REFS/source_index 递归读取任何引用。

## 链接边界

有限审计的9件 Markdown：最终 REPORT、NEGATIVE_PERFORMANCE、PREPARATION，最终export SUMMARY，新科学 REVIEW、strict REVIEW，addendum README、setting-preflight README，以及新 post-report REVIEW。

- 主 REPORT 的13次相对链接/11个唯一目标全部闭合。
- 既定 secondary 文档的7次相对链接及新 post-report 的4次相对链接全部闭合；合计24次。
- ROOT批准补齐旧报告exact6、旧独立复核exact5，以及 ROOT_PROMPT_OUTPUTS_VERIFIED、addendum INPUT_REFS、claim EVIDENCE；仅镜像这些有限原件，不继续展开它们内部的新链接或 JSON refs。
- 在上述9件文档中发现的30条 `/lustrefs/...:行号` 本地绝对链接全部保留原文；它们**不是 GitHub 在线URL**。这不是对全部75件文件所有潜在链接的递归穷举。导航应说明按原 WS member 身份查全量归档归属，或另从已公开旧浏览 leaf 阅读历史链；本候选不猜测 archive owner，也不伪造替代URL。

## 目标保护及 GLM 链接

初次只读目标文件名检查为现有13件 `payload/collection/recovery-raw-000001/...` 加 ROOT README，共14件；未读这13件原件/压缩包内容。本75目标全部位于 `analysis/`，不存在旧目标或路径前缀冲突。ROOT真正copy前仍须重新核target fresh、输入pins与exact范围；原README由ROOT独占维护。

ROOT README 的 `../glm-5.3-original-completed-20260909/replay_verified_v2/REPLAY_VERIFIED.zh.md` 已与GLM精确48copy映射核对，路径正确；不应改成GLM leaf根目录。所用FILE_MANIFEST为 `322f2bd17397a04e3af51319787af940c7eecba2f7c663860d8f90db96e654d6` /23461B，命中行SHA `fab99395c878a58608189fdff5cde9cae824f166ddf108adee4da1aff44cee02` /2979B。没有重读48个GLM文件；仅核原映射、copy收据和两个明确路径的存在性。

本目录不是公开发布或fresh whole union restore/AN2 replay通过证明。后续copy、完整四key原publisher扫描、Git发布及fresh公开恢复仍由ROOT另行授权。
