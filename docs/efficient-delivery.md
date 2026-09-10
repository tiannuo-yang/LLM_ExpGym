# 高效、有限的实验交付流程

本次调整属于 **Static/fake validation**：只用合成小文件验证交付代码，不重跑模型，不重扫、不重打包、不删除 2026-09-08 两模型研究的历史数据。

## 复盘：慢在哪里，不能据此断言什么

Kimi 的公开数据恢复涉及 66,643 件原文件、1,751,137,861 字节，实际落地连同控制文件共 66,986 件；原始数据量只有约 1.75 GB。`CLI_EXIT.json` 中开始/结束被观察到的时间为 2026-09-10 01:37:59 / 07:39:42 UTC。**这是观察窗口，不是独立测得的六小时进程运行时间。** 共享存储上创建、打开、同步数万小文件，再读取恢复后的全部文件，存在明显可避免的元数据/I/O 工作；现有证据不能把全部时间都精确归因于 Lustre 或计算。

旧流程还把 seal、安全扫描、压缩、全恢复、恢复后全哈希及分析重放拆成多个往返，并积累多层人工证明文档。首次建立恢复能力有价值，但不应在同一份不变数据的每次报告/证明更新后重复执行。最终 `6119f9d136c9ed1f06a7bedd7371be0deb9b5d59` 的发布其实已正确改用增量检查：仅核对新增/修改的 35 个 Git blob，沿用 4,820 个未改变条目的既有身份，没有再次全恢复。

以上复盘依据现有 `CLI_EXIT.json`、`ROOT_POST_RESTORE_ACCEPTANCE.json`、`ROOT_FINAL_REMOTE_VERIFICATION.json`，未重新打开旧 raw。不根据这三个控制文件推断模型吞吐、精确磁盘耗时或新的科学结论。

## 今后的默认通路

| 阶段 | 保留 | 不再默认执行 |
| --- | --- | --- |
| 实验结束 | 完整性、缺失/失败分类、全部尝试成本；冻结显式原件清单 | 递归寻找“看起来像结果”的 JSON；按结果好坏挑选文件 |
| 分析 | 固定输入/解释器的一次分析；一次成稿后的独立逻辑复核 | 每个 receipt 再造一层 receipt 或反复复核未变的同一分析器 |
| Seal | 自动分片、原件哈希、安全扫描和压缩共用同一次源内容读取 | 先全哈希，再单独全扫描，再全量重读打包 |
| 发布验收 | 从远端取得可信 manifest/归档，一次流式验证压缩包及全部成员 | 完整解出数万文件后再全量哈希；为只改说明的提交再次 clone/extract |
| 重现分析 | 流校验时只写出分析实际读取的输入，然后重放一次 | 为几个分析输入默认恢复全部 raw；在不同 Python 版本间无目的重试 |
| 后续修订 | 只发布新增/修改的文件；未改归档沿用已核对的 Git blob/SHA | 因为新增一个说明文件，就重封/重扫全部旧归档 |

全量提取不是禁用：新恢复器首次用小 fixture 做端到端恢复；归档格式改变、故障调查或用户明确要完整原始目录时再执行大规模恢复。一次可信的完整流校验已经检查所有原件内容，不需要为了“多一层放心”重新生成 6 万个文件。只有发生输入/实现/解释器变化，才重做受影响的分析或校验。

`summarize_traces.py` 是人工快速查看工具，不是全研究的科学验收器；它会递归读指定目录内 JSON，因此不要对整棵 raw/receipt 树调用。`analyze_portable_study.py` 已采用显式注册文件清单；继续使用该设计，不另造按目录猜测结果的分析入口。分析恢复清单须覆盖程序实际读取的全部引用，包括必要的 source-index 原件；不能未经验证地假设“只需五个汇总 JSON”。记录解释器/统计库版本，避免本轮遇到的 Python 3.10/3.11 次级标准差末位差异被误判成实验变化。

## 实现：一个 CLI、一个全局 manifest

入口为 `scripts/package_run.py`，核心为 `expgym/delivery.py`。输入是一份显式 JSON 字符串数组，例如：

```json
["analysis/records.json", "analysis/source_index.json", "raw/invocation-0001/call-0001.json"]
```

清单必须由已确定的运行/分析索引生成，不依赖输出成绩。默认按 **64 MiB 原件目标大小或 2,000 件文件**自动分片；原件不拆开、不改相对路径。整个研究仍只有一个 `manifest.json`，记录每个归档和原件的大小、SHA-256、所属分片及扫描状态，不需要为几十个分片建立手工审批链。因而可处理本轮 1.75 GB/3.47 GB 级别研究，不受单归档上限限制；本轮历史大包没有用新工具重跑。

本地小 fixture/内部校验，明确不能当发布通过：

```bash
python scripts/package_run.py seal \
  --root /absolute/run-root --files files.json \
  --output-dir /absolute/fresh-sealed --local-only

python scripts/package_run.py verify \
  --manifest /absolute/fresh-sealed/manifest.json \
  --archive-dir /absolute/fresh-sealed
```

公开 seal 必须加载实际四个已知密钥来源，路径用实际记录替换下例占位符；不得把密钥内容放进命令行。工具内也显式设定 `RLIMIT_CORE=(0,0)`，不是把 `taskset` 当成禁用 core dump：

```bash
/usr/bin/prlimit --core=0:0 -- python -B scripts/package_run.py seal \
  --root /absolute/run-root --files files.json \
  --output-dir /absolute/fresh-public-sealed \
  --scanner tools/publication/validate_bundle_v2.py \
  --secret-file /actual/private/source-1 \
  --secret-file /actual/private/source-2 \
  --secret-file /actual/private/source-3 \
  --secret-file /actual/private/source-4
```

`tools/publication/validate_bundle_v2.py` 原字节来自本轮已使用的同名发布扫描器，SHA-256 固定为 `aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116`。本工具直接复用其 `load_secrets`、`scan_bytes` 和路径/大小策略，不改变 credential 字段规则、不允许把自述 `authorization` 字段的误报直接忽略。密钥值只在内存里匹配，不写到 manifest、诊断、日志，也不输出被拒内容的哈希。

原策略每原件/每压缩包 **100 MiB**、每包展开 **512 MiB** 的硬上限保留；64 MiB/2,000 文件目标为默认安全余量。大于目标但未超单文件上限的原件独占一片；如果它实际压缩后仍超 100 MiB，seal 明确失败，而不是改写原件或放松限制。公开扫描保留完整 JSON 语义检查，因此单件内容会在原 100 MiB 上限内暂存，内存有界但不是常数 1 MiB；非公开 seal 和 verify 的 payload 读取为小块流式，清单元数据内存为 O(文件数)。

远端验收和按需恢复可以在**同一次**流式读取中完成：

```bash
python scripts/package_run.py verify \
  --manifest /downloaded/release/manifest.json \
  --archive-dir /downloaded/release --require-public-scan \
  --select analysis-input-paths.json --restore-dir /absolute/fresh-analysis-inputs
```

不需要重现分析时省略 `--select` / `--restore-dir`，默认产生零个恢复后的 payload 文件。即使只恢复一件输入，仍会验证所有分片、所有未提取成员的哈希和路径集合，检查 gzip CRC/footer、tar 结束后的隐藏成员/非零垃圾。新恢复目录必须不存在；失败可能留下不完整的私有目录，只有 CLI exit 0 表示本次验收完成，不能把“目录存在”当成功。

## 安全与证据边界

- 原件封存前必须停止写入；工具拒绝普通并发修改、路径穿越、重复路径、跨分片 file/directory 前缀冲突、symlink 和特殊文件。末尾只检查源元数据，没有第二次全量内容读取；这不是抵抗同权限恶意写者的原子文件系统快照。
- 失败 seal 保留私有输出目录（0700）和可能的部分归档（0600），不生成成功 manifest，不自动删除历史数据、不自动发布。先检查退出状态；不能把部分归档或整个工作目录直接 `git add`。仅发布 manifest 明确列出的成功归档和另行选定的报告/代码文件。
- `--require-public-scan` 检查**可信 manifest 的原扫描声明**，不是重新读取密钥，也不是独立签名认证。先用已核对的发布提交/内容哈希确认 manifest 来源和身份；不信任第三方手改的 `public_scan_passed: true`。若发布清单另含说明、代码、图片或日志，它们也须走相同原策略的扫描，不能只扫描 raw 后自动放行所有新文件。
- 只改报告/校验说明时，利用已验证的 Git 对象身份保留旧归档，只扫描/核对新增和修改内容。数据变更则对受影响的封存单元重新 seal/分析；不要声称对尚未核对的远端新对象已经验收。完全新增研究统一一次 seal，不把每个分片变成单独人工流程。
- raw、缺失答案、错误响应、节点失败尝试、未知 token 成本以及所有负向比较都保留。成稿后的独立科学复核保留一次；交付加速不能删掉反例、改评分端点、把“跑完”冒充“结论显著”，也不增加模型调用。

## 小样本验收与性能边界

`python -B -m unittest discover -s tests -p test_delivery.py -v` 覆盖多分片完整性、选择性恢复、跨片路径冲突、非选中成员损坏、CRC/footer/隐藏尾随 archive、源修改、秘密路径、原扫描策略、core 限制及 CLI。测试只用临时合成数据/假密钥。

当前版本 512 件合成 JSON、4,208,530 字节、4 个分片（测试设 `shard_files=128`）、共 2,425,701 压缩字节的 `/tmp` 示范：seal 0.208 秒，默认流校验 0.074 秒，只恢复 8 件输入的完整流校验 0.072 秒。**这不是历史 Lustre 全量流程的速度承诺**；实际收益的确定部分是默认不再创建数万恢复文件、不再重复全量恢复后哈希，而非一个未经测量的加速倍数。未来真实运行分别记录 seal、传输、verify、分析的单调时钟耗时，首次慢步骤就定位，不用人工观察窗口替代进程计时。
