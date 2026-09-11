# 独立成稿复核

结论：通过本次限定范围的复核；无未解决阻断。复核于 2026-09-11 UTC 完成，最终正文窄修后的输入身份见 REVIEW.json。该结论不是新增实验、原始评分复验或全部归档内容验真。

发现并修正一处措辞：原摘要泛称 Audit 随预算收紧退化，现限定为 Search F1 与 Audit evidence accuracy，并显式保留 Audit label accuracy 的反向结果：Free 0.668175 → Moderate 0.755656 / Tight 0.702866。作者确认正文冻结后，已用原 CSV 对这两处文字与三个值作窄复查。

独立核查结果：

- 从 8519 行 metrics_execution 重建 7687 行分析指标；783 唯一执行、1881 agent、705 分析单元吻合。Exp Audit 每文档三个 order 只平均一次：117 执行 → 39 跨档位单位。Search R1、HPO R3 与 2200/2204/2208 标签、Pool N4 共 366 池符合计划矩阵。
- 逐项重建全部 1245 行 absolute、2857 行 by_outerseed、1227 行 contrasts 的数值、完整/known 分母、item 权重及描述性 SD。配对使用完整 item×outerrep 范围；方向和百分点换算正确。正文及附件的 1245 个设置、1227 个对照、594 个 tuning 重复展示齐全，所有受核数值一致。
- 从 agent 最终性能 CSV 与固定 oracle 独立核 HPO：逐 agent 截零后再取 MI，Gap 越高越好。92 个未知 agent = Exp 11 + Pool 81，均为缺失最终配置且执行完成。54 个 HPO 池中 44 个不完整，其完整 MI/BoN 均保持 unknown；10 个完整。未把 known 子集或零分填为完整均值。此检查不判定历史工具调用是否存在可评估配置。
- 独立汇总 14300 个唯一请求，均首尝试 success；input 105359032 + output 23345301 = 128704333。reasoning 18484906 已包含于 output；138 次 length。逐 execution token 合计一致。两个唯一 Slurm allocation：1383 秒与 9649 秒，各 32 GPU，合计 98.062222 GPU·h，没有再次乘四副本。
- 独立读取成本 helper 的三个纯函数并作 13 个合成用量案例：支持嵌套/顶层 reasoning、合法 0、一致双字段，拒绝冲突/非法值/超过 output。没有运行作者完整 analyze 或 fixtures。另独立逐字节确认 full_v1 与 full_v2 的七张科学/终态/覆盖 CSV 及 INPUTS 不变。
- 17 个 report_inputs 数据/上下文交付副本的大小与 SHA 相符。相对链接 9 处、5 个目标存在；本地 data/provider Git pins 下 97 处引用、76 个唯一路径可解析。22 shards / 26444 files / 1384642088 raw bytes / 237500959 compressed bytes 的索引与 manifest 元数据一致；manifest SHA256 为 b9166ac1d1395d39e072ab5f928fac26ab8a42c08beeb23e3e45cb426a4c8a58。

正文诚实保留 Exp Search/EA 退化、Pool Tight Search 改善而 Moderate Search/Audit 负向、HPO 完整端点 unknown。文中明确 Custom study、无显著性/普适性证明；最高 effort 的四副本 16 请求证据归属运行方，两个 roles 共用一份复合记录。服务 context 1048576、每请求 output 32768、Pool 局部 131072 与厂商 384K 推荐区分清楚；混合量化及 NCCL fallback 已披露。

限制：本次独立算术从交付 CSV 开始，没有复核原始答案评分、扫描 raw、解压或哈希归档 payload，也没有 API/GPU 调用或重跑 native/encoder。存档核查仅覆盖元数据，远端 HTTP/运输验真由发布流程另做；未独立核验上游 SGLang/DeepGEMM Git 对象。任意新根恢复仅可查看，分析器的绝对路径、锁和解释器不会自动迁移。后续仅增加指向本复核的导航链接，不属于所列正文精确字节快照。

保留独立脚本 check_csv.py（只读，输出 JSON）；用 Python 3.11+ 执行 `python3 check_csv.py <交付结果目录>`。本次实际使用 Python 3.12.13。机器可读检查范围、计数、发现和全部输入 pins 见 REVIEW.json。
