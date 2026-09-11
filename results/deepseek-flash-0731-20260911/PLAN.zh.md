# DeepSeek Flash 独立全量研究：计划与执行记录

本研究沿用 Qwen / Kimi / GLM 的实际 **Custom study** 矩阵，不声称 paper-exact。
用户于 2026-09-11 授权增加四个节点，最大 thinking，完整 dump、分析与发布；不与 Qwen 的状态或资源混用。

## 当前状态

- 用户已于 2026-09-11 明确确认 `DeepSeek-V4-Flash-0731`，root 于 03:42 UTC 转达继续执行授权。四个独立 TP8 服务和真实 native / 六任务 smoke 已通过；正式783任务队列于04:39 UTC启动、06:48:03 UTC全部自然完成，0执行失败。四端无请求后06:50 UTC正常释放本研究GPU，进入CPU分析/交付；以下历史准备阶段的“待验证”仅描述当时时点。
- 源码工作树：`/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym-deepseek-flash-20260911`，分支 `study/deepseek-flash-20260911`，起点 `21b4de99b2a014874e3cec1595eaa40762b0c564`；冻结执行提交 `5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8` 已经 github-tn 发布。
- 研究根目录：`/lustrefs/users/chufan.shi/codex_space_tn/deepseek_flash_eval_20260911`。所有 formal / smoke / serving / runtime / cache / dump 均在本研究独立命名空间。
- Qwen 作业 `1204495`、节点 446–449、Qwen 源码/runtime/结果均不可修改；既有用户作业也不在范围内。
- 预留 HTTP 端口 32240–32243，分布式端口 52240–52243；最多新申请 `-A k2p` 的 4 节点 × 每节点 8 H200。
- 已核实当前 plain-TP16 配置不兼容：`o_groups=8` 而 SGLang 用 `o_groups // attn_tp_size`，TP16 会产生 0。选择四个单节点 TP8 副本（合计仍 4×8），不是泛称任何 TP16/DP 拓扑都不可能。root 已同意该显式拓扑；不引入额外 DP-attention/EP 推断。

## 阶段与验收

1. 身份与运行时：确认 checkpoint 修订；核对官方最大 thinking、编码器/tool/reasoning parser、H200 FP4 实现；独立 uv 固定版本。模型文件只读元数据及分片 stat，不扫描 156 GB 权重哈希。
2. 数据与矩阵：独立物理数据副本并对可信清单校验；独立 HPO 3.7 config/cache/socket；精确 783 execution jobs / 783 logical outcomes / 1881 agents，分析折叠到 705 单元。冻结源码、生成配置、数据、部署和全部路径。
3. Serving：使用已接受的四个单节点 TP8 副本，共 4 节点 × 8 H200；健康检查不替代真实验证。所有失败启动/尝试和资源时间保留。
4. 真实 smoke：native auto / named-tool / forced-final 及完整 assistant reasoning / tool history；同 Qwen 六个 task smoke（15 agents），验证真实评分、终态、隔离，不以得分好坏决定是否放行。
5. 正式全量：全局动态独立进程队列，无批次屏障；并发由 smoke 吞吐和长输出延迟确定一次。未答/length 正常保留 task-abstention-v1，HPO legacy，不因负向结果重抽样。
6. 数据交付：一次冻结分析输入、全档位/策略/重复表、完整 dump/聚合索引和全部尝试成本；成稿后一次独立数字/逻辑复核；单次显式清单 seal/scan/compress 和远端流验，github-tn 发布固定链接。
7. 释放：模型客户端自然 drain，确认不再需要 GPU 后仅释放本研究自己的 allocation；CPU 整理不空占 GPU。

## 固定科学设置

- ExpGym：Search 73 × Free/Moderate/Tight × R1；Audit 13 × 三档 × 3 个固定假设顺序；HPO 9 × 三档 × R3（种子块 2200/2204/2208）。
- PoolAct N4：whois Search 39、Audit 13（默认序、R1）、NAS101 A/B/C（R3）；Moderate/Tight × naive/cached/poolact。
- max_steps / max_evals = 30，max_output = 32768；Free 无反馈预算但非无限步骤；Moderate = 10 × c_base，Tight = 3 × c_base。
- T = 1，top_p = 0.95；最大 thinking 以本 checkpoint 的实际支持为准。DeepSeek README 推荐 high/max 输出 384K；本比较保留 32K 上限，必须报告为偏离其推荐且可能发生 length，不擅自扩大。
- Serving context 采用模型原生 1,048,576（root 明确同意），不同于 Qwen 原生 262,144；Pool 本地近似 131,072-token cap 不变，Exp 不新增历史裁剪。实际 KV 容量/并发需在授权 smoke 核实，不增加额外长输出压力实验。
- legacy tuning final policy；task-abstention-v1；strict N4 unknown 不用 known subset 冒充；paper-graph-lock-v3 保持池内 reasoning 锁。
- 初步预期使用 `cache_salt`，必须核对实际 SGLang backend 与编码器；默认禁用 speculative decoding，除非支持性/性能需要经过明确记录审查。

验收目标是完整、忠实、可追溯，不强制观察 ExpGym 退化或 PoolAct 改善。

## 2026-09-11 执行闭合与交付冻结

- 正式 controller 04:39:11 UTC → 06:48:03 UTC，自然 `drained`；783/783 execution、1881 agent slots、0 执行失败、0 未启动，32 workers 全程不变，无 STOP / 恢复 / 得分挑样。闭合 summary 记录 7731.582006718963 s；这是实际队列墙钟，不是 HTTP 时长之和。
- 闭合后四端非生成 `/metrics` 的 running / queue / grammar / decode-prealloc 均为0；仅正常释放本研究 `1204607`，未修改 Qwen 或既有用户作业。Slurm 最终记录结束06:50:36 UTC。第一次 `1204605` 的 CANCELLED 是此前为编译缓存隔离主动替换，第二次 CANCELLED 是正式完成后的正常释放；都不是按答案得分认定的运行失败。
- `study/allocation_final/ACCOUNTING.json` 绑定两个真实 deployment/plan，单次实际 sacct 查询：1204605 为1383 s ×32GPU=12.293333333333333 GPUh；1204607 为9649 s ×32GPU=85.7688888888889 GPUh；总98.06222222222223 GPUh。包含加载、smoke、正式和尾部空闲，不是 formal-only GPU 工作量；四副本不再乘四。后期最后3个请求只在副本3运行，不能声称尾段仍打满32GPU。
- 首次正式分析 `analysis/full_v1` 通过783→705/1881和全尝试完整性校验；发现报告层通用用量形状兼容遗漏：实际 SGLang 将 `reasoning_tokens` 放在 `response_json.usage` 顶层，而旧 helper 只读 `completion_tokens_details.reasoning_tokens`，14300次请求的reasoning子用量被错误显示unknown。输入/输出总token及科学分数不受此字段遗漏影响。
- 分析 helper 增加通用双位置读取，不按模型名分支；0合法、缺失保留unknown，两位置非null必须相等，严格非负整数且不超过completion，reasoning仍包含于output不能重复相加。23 fixtures通过（新增17个子案例）；新helper SHA `6f8b7e44c07d162296d904cf4dfed41fa906a3d199f26d14f9d3e45c38eb79cb`。旧helper由唯一精确逆patch重建，并与full_v1原SOURCE_INDEX的38251 B / SHA `85a705d92630bb0fdcb136e79ffdd460b1cee7704fb9fbbcc238fd6d70cfc3f4` 完全一致，保留为 `study/analyze_deepseek_pre_usage_fallback.py`，不称事前备份。
- 仅为上述明确字段变化进行一次受影响重算到 `analysis/full_v2`；旧原件/首次分析不删除，无模型请求或评分重算。最终推荐分析将明确为full_v2，并核对科学表与full_v1完全相同。首次分析未独立计时，不拿人工观察窗口冒充精确进程耗时。
- 报告 helper 仅增加 `ARCHIVE_INDEX.md/json` 两个精确同目录导航白名单，数据/context/旧报告仍固定40hex提交；4窄fixture通过。最终报告/索引与provider/data固定依赖采用少量本地分提交一次发布，不重封不变raw。
- `analysis/full_v2` 受影响重算完成，实际 `/usr/bin/time` 墙钟57.26 s、user9.21 s/system6.46 s、maxRSS202412 KiB，零模型调用/零评分重算。7张科学/终态/覆盖CSV及INPUTS.json与full_v1逐字节一致；14300条请求账本除reasoning子字段外所有字段逐行一致。最终input105359032、output23345301，其中reasoning18484906（包含于output），total128704333；14300次全部用量已知。该模型无关修补已同步Qwen交付负责人。
- 缺失最终配置是冻结端点的真实结果：Exp tuning70/81 agents可评分，Pool tuning135/216 agents可评分、10/54 pools全N4可评分。92个未知agent均execution_complete=true、normal_loop_return、model_no_answer、unscorable_missing_configuration；不认作执行失败、不用0或best-observed配置代填。现有CSV不能证明历史tool config不可评估，只证明缺少最终配置；legacy fallback与missing-final policy是独立约束。
- 封存时点：所有GPU和队列写者已结束；选择formal及smoke完成清单、native、两个真实serving目录、全量full_v2和显式必要provenance；full_v1仅保留首次INPUTS/COSTS/SOURCE_INDEX与精确原helper用于兼容修复追溯。原始文件不删除，后续成稿及一次独立review在CPU继续，不能以本记录代替尚未完成的公开验收。

## 2026-09-11 CPU 准备里程碑

- 数据：249 files / 240,303,980 B 独立物理副本，对可信清单逐文件一次 SHA 校验通过；文件 0444、目录 0555。新索引 SHA `9517d543a2504ac162a3e5e5875e9507da469db4e9becf9a7c054adec4639ed6`。9 wrapper fixtures、73 Search / 13 Audit / 9 HPO/NAS 的真实离线检查通过。
- 矩阵：12 helper fixtures 与实际 profile `--check-only` 通过；33 stages、783 jobs、1881 agents、705 analysis units；canonical identity SHA `469ac7b34ab802d7b60747275a9f8a1853706275a489b75c5336ffff1d21b13e` 与 Qwen 相同。
- Serving launcher：显式 schema3 四单节点 TP8 profile；默认 schema1 两 TP16 与 schema2 TP8×PP4 字节兼容。25 focused tests 通过；完整无成本测试 698 tests、33 skips，Exp fake 与三策略 Pool fake 全通过（tool `ef42ce`）。随后新增显式 `--chunked-prefill-size` allowlist 以固定 4096，此最终 revision 完整 698 tests + fake 也通过（21.576 s，tool `9efb2e`）。HPO skips 由前述真实 CPU checks 单独覆盖。两次源码提交分别 `8fc18878d03dea8d08f8ed89d9bb66433862b30c` 与 `5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8`，无评分/任务改动，尚未 push。
- 离线分析器：22 fixtures 通过，783→705 折叠与 strict unknown / all-attempt 成本语义不变；尚无正式结果，也未运行正式分析。
- Runtime：独立 uv 已完成 SGLang 0.5.17 / Torch 2.11 cu129 基础环境，安装205 distributions（10m35s）及准备1m27s。首次 offline lock 因共享 cache 缺 wheel 退出，随后新 study 独立 cache 在线 lock/sync；不修改旧环境。
- 最大 thinking 的关键兼容性问题：stock 0.5.17 的 `max` 仍是 preview 的 Absolute maximum 文案，等于 0731 的 high。官方修复 `059269594c5f245f77dad711631843c299d7713f` 增加基于 checkpoint encoder 的 preview/official profile。正在采用有固定来源的官方修复；真实最高档必须以实际渲染 prefix 验证，不看字段名猜测。不能直接整份替换 checkpoint encoder，因为 SGLang 的 dict tool-argument normalization 和 task helper 需保留。
- 权重结构检查：48 shards / 72,317 tensors，声明张量 166,878,536,440 B、物理分片 166,886,535,336 B；仅读取 7,998,896 B safetensors headers，索引全部匹配/offset合法，未读或哈希权重 payload。4,705 个 `mtp*` 张量在无 speculative 的目标加载路径中跳过；这不是一次真实 GPU 加载通过。
- 最高 thinking 官方三文件 backport 已应用且精确 SHA 匹配；实际新环境 CPU renderer 9/9 对照官方0731字符串/token IDs通过，最高 prefix、registry/typed tools/reasoning/cache_salt 通过（tool `7bf65d`）。单份 `runtime/versions.json` 记录实际身份。6 verifier fixtures、2次mock native client也通过。零 API 请求、未初始化 CUDA、未加载权重；GPU/JIT/真实native仍待授权确认后执行。
- 报告/归档生成器适配完成：57 fixtures 通过，原生1M context 的4项窄回归通过；尚未生成真实报告或归档。成稿后的独立复核仍未进行，不能以作者 fixtures 冒充。
- 资源报告适配边界已核对：未继承 Qwen 强制 failed startup 的可选 accounting 适配器；真实 allocation 账本单独记录，四副本仍只对应一个四节点 Slurm job，不能虚构失败启动或把 replica 数当 job 数。资源配置表读取实际 topology，已增加“无 accounting/无 startup 仍可生成、4/8/1/1 展示、无账本为 unknown”窄回归；三个相关 report tests 通过。后续若加入账本，只可用真实 expected job ID 集合、去重及绑定；当前尚无 GPU job。

## 2026-09-11 GPU 执行授权

03:42 UTC 收到 root 转达的用户明确型号确认及继续执行授权。冻结候选源码和 runtime 身份未变化；复用已通过的 CPU / fixture 验收，不重复全套测试。开始申请独立四节点，实际 Slurm ID、节点、启动/请求结果在下方追加。

- 首次真实 serving：Slurm `1204605`，`higherprio` / `k2p`，节点 `azure-uk-hpc-H200-instance-[222-225]`。部署目录 `serving/launch01/`；32 张 NVIDIA H200 均实际可见，143,771 MiB/card，driver 570.133.20。四副本同一次 Slurm allocation。尚未判定加载或真实请求通过。
- 对应部署的完整矩阵已生成到 `study/formal_v1/`，33 stages / 783 jobs / 1881 agents；正式队列未冻结、未启动。六任务 smoke 队列 `study/smoke_v1/queue_plan.json` SHA `67d974caccb4647241a1f1cdf26abfdb80d15f5500fe01ef6dd6cdfc63e40245`，仅 3 steps / 2 evals，6 jobs / 15 agents，不作为正式分数。
- 首次启动完成真实权重加载（约 20.46 GB/card），进入 MHC/DeepGEMM 预编译后发现编译缓存隔离遗漏：DeepGEMM / TileLang / CUDA driver 的默认缓存不遵循 XDG。它们是代码编译缓存，不是 prompt/KV/agent 观察状态；本次仍为 0 模型请求。为落实独立缓存约束，主动取消仅本研究 `1204605`，保留全部启动日志及真实资源成本，不删除/修改共享缓存，也不修改 Qwen。
- 新增 `runtime/runtime-env-isolated.sh` 只显式设置上述编译缓存到本研究 runtime/cache，source 原 `runtime-env.sh`；原 package / encoder / CPU acceptance 身份均保留。其 SHA `5b52270bc12986f1ebdeb067598c0844db4fde37df0c44e58031e045d0863edf`，bash 语法和显式路径检查通过。
- 第二次 serving：Slurm `1204607`，04:09:47 UTC 启动，仍是节点 222–225；旧 job 于 04:09:11 UTC 终止（主动取消，23m03s）。`serving/launch02/plan.json` SHA `54cd209e728d39153bc3d354e88068284ccf166d06d84dac099aa5245389380e`，deployment SHA `41972b57b531cfe659ba417ca138d2029293efc0744016646ea2794a8b5a3c93`。节点/端口完全相同，未执行的 matrix 与 smoke queue endpoint 字节一致，直接复用；正式 RUN_INPUTS 将绑定新的部署与独立环境，不复制相同计划。

## 2026-09-11 真实验收与正式启动

- 四个 HTTP 服务于 04:24:11–12 UTC 就绪，真实权重加载与 CUDA graph 完成。无致命启动错误/OOM；可选 custom all-reduce JIT 失败后使用标准 NCCL 2.28.9 fallback、NVCC 12.8.93 建议升级 warning 等实际运行时限制已写入冻结的 `runtime/BUILD.md`，不能表述为零 warning 或未经修改官方环境。
- 原生 smoke 四副本全部通过，16/16 delivered requests、16 attempts，覆盖 auto / named-tool / forced-none，保留完整 native assistant reasoning 和 tool history。原始记录在 `native_smoke01/replica0..3/`。
- 保存 wire 的离线真实 renderer 重放通过：4 副本 / 16 requests / 53 input identities，实际 prompt token IDs 与0731官方编码器一致且 server prompt token counts 对齐；最高 `max` prefix 已实际验证。`study/native_contract_replay.json` SHA `fd10fd0caadbc877d0d6ff74247c0049e11f489c1180ed39b60e1e9bb52621a9`；此重放为零 API 请求、CUDA 未初始化。
- 六任务 smoke 全通过（6 jobs / 15 agents，397.311 s，无失败或 stop reason），会话 `task_smoke01/queue/sessions/1789100867084806815-3040396`，summary SHA `8f4e8685e14d0d98b9d75f6a18ad93e8249ce8dc6bbb2c1f75cbefabbde79f33`。包含真实 Search / Audit / ParamNet 与 NAS101 三策略；不把 smoke 分数纳入正式研究。
- 正式输入冻结：源码 `5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8`（干净树）；`study/formal_v1/queue_plan.json` SHA `69048ff627626da685ca34157d4954e8d8413cd83c3fe995c811a93778b09c5b`；`RUN_INPUTS.json` SHA `57bbe761f556a31643d9f9402cf5747b6fd4d06fc05355fde4510d8ef7f86107`。绑定 launch02 与实际独立 cache 环境，无科学配置变更。
- 正式队列于约 04:39 UTC 启动，32 workers、全局动态补位，无批次/重复屏障。会话 `formal/queue/sessions/1789101551771860378-3049313`，controller PID 3049313（工具 session 75953）；独立 STOP admission 路径 `formal/STOP_ADMISSION`。
- 并发依据：四副本通常各8个 invocation，naive/cached N4 时名义上各32个请求，低于每 server `max_running_requests=64`；实际 full KV pool 13,400,832 tokens，并非仅使用静态估算。真实 smoke 每个请求约110 token/s，三并发单副本约327 token/s。HTTP timeout7200 s 为长 reasoning 留余量；这些是 smoke 的短期证据，不是全量 ETA 或硬性无溢出保证，重试残留可超出名义请求数。保持 PoolAct 池内锁、30 steps 与32768输出预算不变。
- 正式最先完成的三个 invocation 有限只读抽查：46 个实际 wire 请求均为目标0731 / max / thinking=true /32768，43 次跨轮前缀精确保留完整 provider assistant reasoning / tool calls，46 条 trace output_message 均与原始 provider 对象一致；2 次 forced-none 仍保留 schemas/全历史并 stop。这不是全量质量审计。`job_558edd0804937867611048e97f0c0b4d32c50796a9a8a4f767524097bbfeecc9/api_dump/6a56eb9014bc45148bf573e58befeeb2.json` 和 `job_29f2aae074929bcbf44cc70b2c978eb179a3e445d316e28716b2d205aee6f844/api_dump/55c1e471b5974e69917afb2bf40dadd3.json`（均位于 `formal/invocations/`）各第二次请求在 `parallel_tool_calls=false` 下仍返回6/15个调用；下一轮所有对应 tool_call_id 均逐项回复，无丢调用。该 provider hint 并非模型遵循保证，不据此重跑或筛选样本。
- 源码发布提前完成：04:44 UTC 通过 `github-tn` 推送独立分支 `study/deepseek-flash-20260911`，远端 ref 实际为冻结执行提交 `5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8`（工具 `d6524f`）。推送前使用固定 `validate_bundle_v2.py` 策略对相对已公开父提交的两次新增 commit 全部7个独特 Git blobs 做安全扫描，四个已知 secret 来源仅在RAM检查，0 finding，耗时0.207 s（工具 `2564f1`）。只包含通用四副本profile、显式chunked-prefill参数及对应文档/测试；无任务、提示词、评分或agent算法变更。正式raw仍在产生，尚未封存/发布，不把本次源码push称作实验完成。
- 05:32 UTC 单次调度元数据快照：ExpGym 417/417 全部通过执行完整性校验（Audit117、Search219、HPO/NAS81）；Pool Audit61/78完成、17活跃，Pool Search7/234完成、15活跃，Pool NAS0/54。总计485/783完成、32活跃、无执行失败。Pool与Exp尾项自然交错，没有阶段屏障；全程维持32workers，无恢复/质量重抽样或配置改动。此“通过”不代表答案全对；科学结果尚未汇总。
