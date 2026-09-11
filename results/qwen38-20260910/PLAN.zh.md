# Qwen3.8：同矩阵 ExpGym / PoolAct 完整实验

状态：离线准备、4节点TP8×PP4服务、原生协议及6项任务smoke均已通过；已启动正式783项动态队列。目标是按前两模型的实际 Custom study 设置完成第三模型，不要求得分满足预期方向；保留所有有效结果、失败、未知用量及原始 dump。

## 固定范围

- Checkpoint：`/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Qwen3.8-2.4T-A95B-FP8`。213 个分片元数据齐全，权重数据 2,496,066,252,544 B；此阶段未逐字节扫描 TB 权重。
- 实验基于维护后源码 `0d3c299f0352ddd53bc012c787d3da81db529d89` 的独立工作树，必要实现修订将在正式执行前固定。K3/GLM 历史源码及结果保持不变；新修订与旧运行差异在报告中说明。
- ExpGym：73 道 Search（seed2 36 + seed3 37），三预算，R1；13 Audit 文档，三预算、三个固定顺序；9 HPO/NAS 任务，三预算、R3。
- PoolAct：39 道 whois（seed2 20 + seed3 19），13 Audit 默认顺序，均 R1；NAS101 A/B/C，R3。全部 N4、naive/cached/poolact × Moderate/Tight。
- 保留30步骤/评估、每次生成32768输出上限、legacy评分端点和相同题目/种子标签。思考及采样参数按千问真实支持显式记录，不复制无效的模型专属参数。
- 算力保持4节点×8 H200，Slurm账户k2p。单TP16显存不足，采用官方H200配方单TP8×PP4副本；不增加到8节点。实际容量、吞吐仍须加载和smoke验证。

## 当前执行记录

- 2026-09-10：独立源码冻结为 `f2d14aefed33ba1ff9e225a8df0803a421bec9a5`；增加显式TP8×PP4配置并重新校验保存的启动计划，未改科学评分端点。原schema1启动输出保持兼容。
- 一次完整无模型检查：684 tests，33个显式环境/依赖skip；ExpGym fake及naive/cached/poolact fake均通过（执行工具记录`09d400`）。真实ParamNet路径另由固定Python3.7验证，不能由skip证明。
- 新数据物理副本249文件、240,303,980 B，已按来源清单逐件核对SHA；旧数据/旧环境/旧结果未改。全部9个HPO/NAS任务的实际CPU评分、fidelity、预算与冻结oracle匹配；73题Search及13文档Audit加载正确。
- 独立uv运行时SGLang0.5.17、Torch2.11.0+cu129：原生模型registry、CLI、模板及parser的CPU检查通过，GPU加载另验。显式SSM状态采用checkpoint的float32；不盲从新版配方的bfloat16，也不据legacy分支断言bf16必不支持。其它拓扑/后端见 `serving/launch01/plan.json`，锁文件与版本见 `runtime/`。
- 新GPU allocation `1204491` 于2026-09-10 22:45:39 UTC启动，节点446–449，4×8、account k2p，单TP8×PP4/EP1；server context262144、memory fraction0.85、MRR64。跨节点实查每节点8张H200、143771 MiB/卡、驱动570.133.20（工具记录`146c51`）；已有用户Slurm作业不动。正式Pool局部context上限仍131072近似tokens，正式输出/步骤上限未变。
- `study/formal_v1/` 已按实际deployment地址生成33 stages/783逻辑项/1881 agents的配置；不是服务ready或已执行声明。在任何模型调用前已固定 `study/formal_plan.json`（SHA `a9857207e5dc8f30bc582108e086ed423ef3001b83da710e965c0e1759741720`）和 `study/RUN_INPUTS.json` 的源码、数据清单、wrapper、runtime及checkpoint元数据身份；执行仍须先通过真实smoke。单独准备6个有界task-smoke（15 agents），仅smoke为3步/2评估，其余provider设置不变，不纳入正式分母。
- 22:48:46 UTC，32/32 workers完成分布式初始化（约5.4秒）；22:48:54全部进入weight load。加载期实测每GPU约75–76GiB已分配，但分片遍历100%不等于张量传输/预热完成。
- 正式调用前的服务接口审查发现：SGLang0.5.17使用 `cache_salt` → `extra_key`，不会消费OpenAI的 `prompt_cache_key`。已在 `21b4de99b2a014874e3cec1595eaa40762b0c564` 增加显式、模型无关的请求字段适配；OpenAI默认payload逐字节相同，namespace/任务cache/评分不改。完整回归691 tests（33 skips）+fake均通过，另有Python3.7客户端与CLI检查；native模拟多轮/强制最终/盐字段检查通过，尚不代表真实smoke。
- 当前接受矩阵：`study/formal_cache_salt/`；正式计划：`study/formal_plan_cache_salt.json`，SHA `f6958c036bd3ba3dbda5de44d2810ca3cfbd0d6ae0f90d0253a2161b20a5d3fd`；输入身份：`study/RUN_INPUTS_cache_salt.json`。f2版本旧计划仅未执行初稿，不能用于运行。GPU服务不用重启。缓存隔离声明限Python Unified/Radix路径；四节点实际sglang进程均未设实验C++ radix flag（`ff18e3`），仍待实际缓存backend初始化日志核对。
- 当前task-smoke计划：`study/task_smoke_plan_cache_salt.json`，SHA `87a3fc604520df855abaa167802feb2e42add1eb7e3ee431b22da17120b3fb7e`。6jobs/15agents，原生工具smoke仍先行。所有旧plan均未执行，正式dump计数仍0。
- 加载诊断：mmap分片遍历完成后才实际加载tensor，故42秒的100%进度不是服务就绪。22:57附近node446的8个scheduler在62.8秒采样中合计`read_bytes`增加18.07GiB，且全体持续major faults，不能据此宣称挂死；共享RSS不能按8倍当独立内存。单分片53（8,591,113,328 B）普通顺序读→`/dev/null`实测4.79秒，仅测速，不是正式推理吞吐。
- 23:18 UTC启动一次有界PP本地page-cache warming（`study/warm_pp_pages.py`，日志`serving/launch01/warm-rank*.log`）：每节点单reader、16MiB buffered read，只读本PP约616–624GB集合；不改权重、不重启服务、不增加GPU。四节点host可用约1.85TB、真实job/服务cgroup上限1.950TB且当前已用207–247GB，已核对全部有限祖先。执行器按节点/rank映射验证，保留384GiB余量、900秒内部/960秒外部上限，服务健康即停。此操作只改变初始OS页缓存，不计入科学实验。
- 四个warming reader全部正常完成并退出（`e3a1db`），PP0/1/2/3依次读取622,264,968,272 / 616,220,394,336 / 616,220,394,336 / 623,434,800,936 B，耗时232.489 / 251.929 / 248.785 / 249.742秒。23:23:06开始出现实际`Load weight end`，仍须等32 workers及服务预热全部就绪，不将warming吞吐当模型吞吐。
- launch01失败：32/32 workers加载完成，KV/SSM缓存分配、FlashInfer GDN、CUDA graph约43秒均通过，但23:25:05 Unified MambaComponent因`page_size=64`且未启用extra-buffer触发断言；作业1204491于23:25:06 FAILED，历时39分27秒，完整日志保留，模型实验调用仍0。静态核查根因是0.5.17的Mamba参数规范化架构集合遗漏`Qwen3_5MoeForCausalLM`文本wrapper，不能误写为PP禁止extra-buffer。选择既有no-extra-buffer实现兼容的`page_size=1`，不改模型代码、不强开未规范化的extra-buffer。
- launch02替代启动：1204495，约23:27 UTC，仍原节点446–449，单TP8×PP4/EP1、4×8 H200。只改`--page-size 64→1`；原作业已退出，无新增并行GPU占用。正式/任务smoke计划的源码、参数、endpoint地址均未变，继续使用原cache_salt计划；另绑定新launch的输入身份，不把旧1204491写成正式服务来源。
- launch02已通过：32 workers全部加载、KV/SSM分配和CUDA graph成功；实际初始化为Python `UnifiedRadixCache hybrid_ssm=True`。23:35:08内部`/generate`预热200并报ready，ROOT于23:35:48实查`/health`200。第二次权重加载日志约144–240秒（各worker不同）；预读后OS页缓存保留，不再用初次冷加载推算服务吞吐。当前正式输入身份为`study/RUN_INPUTS_launch02.json`（绑定原正式计划、源码21b4de9及新launch02）；启动`native_smoke01`的两预设case，正式逻辑结果仍0。
- 原生smoke通过：23:36:06–23:37:23，auto及named-tool均完成native工具→forced-final，4/4物理尝试均首次成功，总76.916秒；首请求71.177秒，其余1.141/1.702/2.771秒。ROOT按实际四份dump检查原assistant全文、reasoning、tool_calls、tool返回、schema及cache_salt在wire中保留（`dd3d5b`）；这不是服务端模板不作任何变换的声明，render差异另核。nonce两次正确仅作描述，不作性能挑选。
- 启动接受的task_smoke_plan_cache_salt，workers=6、6 jobs/15 agents、仅smoke为3 steps/2 evals，不纳入正式分母。不增加smoke重采样；正式783项仍未启动。
- 原生render核对通过：同版本ChatCompletionRequest与本地tokenizer/template纯CPU重现四次输入359/193/360/190 tokens。forced-final在服务端移除273 tokens工具定义/调用说明，但system/user、原assistant reasoning、XML调用及工具结果实际仍保留；反事实保留定义时两个final分别466/463 tokens。不混淆HTTP wire与模板行为。
- 实际提示词有界检查：6个smoke job首请求的system/user/tools无显式benchmark/dataset名称或任务ID泄漏；当时41请求中40条去重tool-role消息亦未见上述标识。必要NAS搜索空间仍可被熟悉benchmark的模型推断来源，不能声称不可识别；该检查不覆盖尚未执行的NAS201或当时尚未产生的PoolAct后续tool消息。检查来源为新study路径及当前smoke plan，不重扫旧结果。
- task-smoke前5项（Search、Audit、ParamNet、NAS naive/cached）完成且worker评分/恢复完整性检查通过；PoolAct仍正常运行。32卡单次利用率快照约51%–93%（`b03629`），不是长期利用率或有效计算占比证明。正式队列预定workers=16，N4 Pool最多64个并行agent请求匹配服务MRR64，统一动态补位，不改题目/种子/预算/生成上限；实际吞吐及剩余时间以正式运行测量更新。
- 报告准备：`study/analyze_qwen.py`及metrics helper为此783执行/1881agents→705分析单元结构适配；`study/build_report.py`从显式SHA-bound聚合、计划、RUN_INPUTS、serving plan和oracle生成三份Markdown，全预算/策略/任务/R3均覆盖。报告fixture 24项通过，未读取正式结果或生成真实结论；实际成稿后仍须一次独立数字/逻辑复核。
- task_smoke01全部6/6通过，15 agents，历时645.293秒，无stop reason；session=`1789083576696821255-2789200`。PoolAct尾部较慢不仅是生成长度，还因既有`paper-graph-lock-v3`在单pool内串行保护graph injection→LLM decision→pending claim，工具在锁外；不能把整段耗时说成一条超长推理，也不为速度改算法。16全局workers对于naive/cached最多64个agent请求，对于全部PoolAct决策阶段最多约16个请求（不同pool并行）。
- 正式队列启动：原plan SHA `f6958c036bd3ba3dbda5de44d2810ca3cfbd0d6ae0f90d0253a2161b20a5d3fd`，output=`formal`，workers16，stop-file=`formal/STOP_ADMISSION`（未创建；只作必要时停止新准入并自然drain的入口），无额外wall deadline。启动前服务metrics running=0/queue=0，累计generation_tokens83006仅作启动前观测，不混入正式token账本。预计运行约6–12小时只是按smoke与目标并发的粗预留，实际以各场景正式吞吐更新。
- 2026-09-11 00:05 UTC附近，正式首批Free Audit已陆续结束：19/783通过、0失败、16 active；这是运行/评分完整性状态，不是性能方向结论。服务未见新增异常。源码增量的14个Git blobs及2个commit（322,184 B）按固定发布扫描器和四个已知密钥来源检查通过（`c10342`）；通过github-tn推送 `study/qwen38-20260910`，远端确认为`21b4de99b2a014874e3cec1595eaa40762b0c564`（`4db90e`）。未推送任何活动结果或修改正式源码。
- 运行期并行完成交付准备：`study/build_archive_list.py`从已关闭queue及completion inventories生成既有packager的单一文件数组，补session logs/report和显式smoke/两次serving附件，不读取活动formal payload，20项合成测试通过（`7a5ee5`）。`study/build_report.py`增加可选SHA绑定的Slurm/queue accounting输入，30项合成测试及精度容差窄核通过；分别展示HTTP尝试成本、正式queue墙钟、GPU总数×Slurm elapsed的资源保留量，不冒充有效计算或formal-only GPU用量。无END时终态成本unknown；真实账本须在客户端drain和服务释放后采集。这两项均未触碰冻结执行源码/模型设置。
- 约00:30 UTC容量评估：一个Free Audit物理请求`f0433e1fb2684880955cc823fa040d65`首次成功、输出32768（全reasoning）、1290.039秒、finish=`length`，随后正常继续；截断不是infra failure，不重抽样。当前全局吞吐观测约300–510 tokens/s，但不能把PP当前microbatch running gauge当全部请求，也不能把吞吐再乘PP4。16个Pool invocations按首批顺序最多49请求，动态最坏64；这与3600秒非stream socket timeout的组合存在可避免的超时风险，大batch吞吐可能增长，不能宣称必定超时。
- 已决定一次性容量切换（此条记录时尚未实施）：当前Exp维持workers16；接近Pool边界、尚有一小段Exp未准入时提前设置`formal/STOP_ADMISSION`，已开始任务自然drain，不取消。旧session主动停止可能`passed=false`/CLI1，必须区分未跑完整计划与failed experiment。保存并移走STOP原路径后，同一plan及源码`--resume --workers6`，只复核已完成、执行从未开始项；剩余Exp尾项与全部Pool共用动态队列，不设置每stage屏障。N4/提示词/预算/输出/token timeout/评分全不变；记录实际两个session、workers和STOP时已开始Pool数，不声称观察首Pool再STOP能保证只启动一个。报告accounting表已补每session的workers，2项针对性测试通过（`bd1c00`）。
- 正式首个场景完成：截至2026-09-11约01:14 UTC（队列elapsed4949.79秒），Audit三档各39/39、合计117/117执行完成；Search当时Free56、Moderate35、Tight36，总体244/783，0 failed、16 active。计数来自计划身份与session事件关联（`65270b`），不是得分/答案完整率；尚未进行正式聚合分析。用户另授权DeepSeek独立4节点研究，由独立子代理负责，此处源码/环境/数据/dump及1204495资源保持不变。
- 并发切换已开始：2026-09-11 01:54:35 UTC，ROOT创建原controller指定的`formal/STOP_ADMISSION`。controller在elapsed7364.036秒读取并记录`stop_new`；实际388个Exp jobs已启动、372完成、16 active、0 failed，Pool已启动0（`9ca35e`）。比操作前快照多准入1个Exp，按实际事件记录，不删除它。尚有29个Exp及366个Pool从未开始；当前仅自然drain，未取消任务、未停止GPU、未修改模型/预算/计划。标记文件保留操作原因及16→6意图，旧session结束后更名归档并继续同plan resume。

- 并发切换完成：首session于2026-09-11 02:08:28 UTC自然drain，388/388已启动项均execute成功、0失败、395项从未开始；elapsed8196.595秒。CLI1和summary passed=false仅对应主动停止完整计划的新准入，不代表任何实验失败。STOP标记已更名保存为`study/admission_transition01.json`，原路径不存在；同一plan/source/runtime以workers6、`--resume`续接，session=`1789092647915522583-2932149`、PID2932149。已有388项仅进行identity/inventory/评分恢复校验，不调用模型、不重抽样；之后29个Exp尾项和366个N4 Pool统一动态补位。跨session的verify_resume事件不得重复计入实验分母。

- 2026-09-11 03:43–03:44 UTC只读复核：ExpGym 417/417已全部完成，Pool 29/366完成，合计446/783唯一项、0执行失败、6 active；第二session的388个verify_resume不重复计入。GPU作业1204495正常，后续仅Qwen交付代理管理此研究。已完成Pool当时仍只有Audit Moderate样本，PoolAct单pool均值30.21分钟，而naive/cached约7–8分钟；其串行推理锁及未完成长尾均影响估时，不能按已完成短项把剩余全部任务线性外推。其余设置/源码/runtime保持冻结。
- 报告链接准备：仅study/build_report.py新增两份索引的精确同目录文件名白名单，4项针对性fixture通过；固定数据提交A之后，索引和报告一并在提交B解析相对索引，避免同提交SHA自引用循环。输入与旧报告链接仍须固定40位commit，禁止路径穿越/移动分支；这不改运行源码或科学端点。索引生成器由独立子代理用合成数据准备，实际成稿仍统一一次独立数字/逻辑复核。
- `study/build_archive_index.py`已完成13项合成fixture（`819709`），只读两份metadata并继承原件pins/扫描声明，支持实际delivery.v1、分片/成员/外层副本去重及明确恢复边界。正式与smoke的analysis-states文件只列接受plan SHA和实际session身份，不表示活动queue已关闭。为使分析实际依赖均可归档，另将原参考矩阵manifest与oracle按原字节复制到`study/reference_matrix_manifest.json`和`study/reference_oracle3.json`，SHA分别仍为`cdb8fe32b0904f49e8dd3f083e40378c18213fdb6c0004bd1d49c9beff6302d3`、`f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e`；不是复制/扫描旧raw，不改变科学矩阵。真实分析仍等本轮全部输入关闭后执行一次。
- 2026-09-11约07:00 UTC，DeepSeek交付发现SGLang实际将reasoning token置于usage顶层，而研究分析器先前只读completion_tokens_details中的嵌套字段。Qwen闭合native smoke两件也确认顶层28/31 tokens；在首次正式分析前复用模型无关双形状适配：0合法、缺失不补0、两形状非null冲突报错、严格非负整数且不超过output，reasoning不再次计入total。8项projection fixture与上述两件smoke提取核对通过（`883958`），未扫描正式raw或调用模型；仅study分析器改变，不动冻结执行源码/runtime/评分/并发。分析器新SHA为`d1759ccbc49a449fd651d8c5cff9fed343453086fe23cb45c88579404984187d`。
- 08:16 UTC阶段描述更正：07:10的一条进度消息曾按总数误推Search已在Moderate/Tight之间推进；实际按plan job_id关联events，当前601/783由ExpGym417、Audit Pool78、Search Moderate seed2 60与seed3 46组成，Search Tight尚未开始。总完成数、0失败和任何运行参数/结果均不变。后续阶段分解只按接受计划逐job身份关联事件，不按预想顺序推断；当时服务持续decode约309tokens/s、queue0，最长整pool在途45.3分钟。先前剩余6–10小时只是含尚未观测Tight/NAS与长尾风险的低置信排期，不是完成时点保证。
- 约08:36 UTC，按原job身份确认首次NAS Pool准入：`job_3a0d0fc67f01f4f72d12447c327aced0f1ecb7873ecaa5b03a9687b1e8fcc144`，tuning / Moderate / naive。此刻607/783完成、0失败、6 active，Moderate Search尾项与NAS已并行；Search Tight尚未开始。实际flat plan在Moderate Search之后先安排Moderate NAS，再继续后续阶段，不存在等Search尾项全收齐才准入的屏障。

### 2026-09-11 正式闭合与资源回收

- 按 plan job_id 关联 events，Search Tight 首次准入为 10:32:03 UTC；NAS Moderate 全部 27 项于 12:04:05 闭合；NAS Tight 首次准入为 12:09:25。后续阶段与上阶段尾项并行，不是批次屏障。
- 13:24:48 UTC 正式队列自然 drained：783/783、passed=true、0 execution failures、unstarted=0、active=0。第一 session 的 388 个真实执行由第二 session verify_resume 复用，正式分母仍为 783，而非两个 session finished 相加。错误答案、长度停止和负结果不重跑。
- 原 controller PID2932149 和正式客户端已退出。13:25:07 与 13:25:18 两次 GET /metrics 累计 generation 均为 14,735,511，queue/running/throughput 均为 0；最后 POST 于 13:24:46 完成，期间没有新 decode。此静稳判断结合客户端退出与累计量/日志，不将单次 PP microbatch gauge=0 冒充全服务静稳；queue 原始 provider_quiescence_proven=false 字段原样保留。
- 13:25:27 UTC 仅取消已完成实验的本研究 serving allocation 1204495，不触碰其他作业。Slurm CANCELLED 是完成后的资源回收，不是实验失败。最终 accounting 保存启动失败 1204491（2367秒、32GPU）与正式 serving 1204495（50306秒、32GPU），以及 workers16/6 的两个 queue session；allocation GPU-hours 包含加载/smoke/空闲，不代表有效计算。
- 接下来只做一次正式 CPU 分析、一次原件 seal、完整报告/索引、一次非作者成稿复核及精确远端验证；不重启模型，不改变冻结设置，不扫旧模型 raw。
- 随后 squeue 已无 1204495，最后 COMPLETING 节点清理结束，全部资源释放。唯一 `analysis/full_v1` 正式分析以 Python 3.10.12 完成，墙钟315.42秒，生成11份输出；783 execution slots、1881 agents、705 analysis units，模型调用与重新评分均为0。正式18121个物理HTTP尝试的usage全部已知：input140855799、output14652505、reasoning12785832（已包含output内），不得把HTTP墙钟合计当作并发实验历时。后续只复用这些输出。

## 步骤及验收

1. 环境与部署：确认checkpoint/模型架构，使用独立uv运行环境、固定兼容SGLang版本，离线验证启动配置和数据环境。验收：模型支持、显存预算、CLI及各节点rank映射成立，旧环境不改。
2. 原生协议与任务smoke：申请上述资源，确认实际加载/健康、native多轮工具及forced-final，覆盖必要Search/Audit/tuning评分路径，保留所有尝试。验收：真实请求/响应与任务协议一致、score验证通过；不以非零分或特定输出内容判断管道成功。
3. 冻结正式矩阵与并发：核对逐项选择器、R/order/seed和数据身份，先测并发/吞吐再确定全局动态队列上限。验收：逻辑结果数783、agent traces1881；调度拆分后的进程/invocation数另按实际记录，不照搬旧705进程计数。
4. 全量执行：无批次屏障，独立状态/输出/dump/cache namespace；正常长度停止、错误答案和负分差不重抽样。验收：每个计划项有可核查终态、评分与来源；基础设施失败保留原件，恢复须显式规划。
5. 全设置汇总、报告和索引：固定输入生成所有档位/策略、逐任务和重复层表，单列模拟反馈与实际token/墙钟/Slurm成本，报告中放完整原数据索引。验收：分母/权重/缺失与所有原比较一致，不删反例。
6. 成稿后独立复核与发布：一次数字/逻辑/口径核对，确切增量安全扫描，通过github-tn发布并核对远端。验收：用户能从报告链接定位原dump、聚合比较及恢复入口；不重复全量解包或递归审计链。全部客户端收尾后释放仅本任务申请的GPU。

完成每步更新此状态与用户进度。加载、smoke和正式吞吐实测后再给剩余时间估计，不沿用K3/GLM的吞吐作保证。
