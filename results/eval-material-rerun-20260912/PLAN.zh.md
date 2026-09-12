# 重要影响设置的定向重跑：2026-09-12

登记时间：2026-09-12 04:48 UTC；在本研究首次模型调用之前固定选择。
研究 ID：`eval-material-rerun-20260912-v1`。类型：Custom study，已见任务上的探索性修复后复核，不是全矩阵或未见任务确认性实验。

## 1. 目的与固定范围

用户授权：只重跑对结论影响较大的设置，重点检查旧反例，不机械重跑全部受影响数据。选择依据包括旧效果方向和已知缺陷，因此明确是 outcome-informed 的定向研究；不是新随机抽样。范围在新模型调用前固定，所有格均保留 naive / cached / poolact，不能只更新 PoolAct 或重抽缺答成员。

| 模型 | 场景 | 预算 | 任务、重复与策略 | 池数 |
| --- | --- | --- | --- | ---: |
| DeepSeek V4 Flash 0731 | Audit | Moderate、Tight | 13 文档 × R1 × 3 策略 × 2 档 | 78 |
| DeepSeek V4 Flash 0731 | NAS101 | Moderate、Tight | A/B/C × R3 × 3 策略 × 2 档 | 54 |
| DeepSeek V4 Flash 0731 | Search whois | Moderate | 39 题 × R1 × 3 策略 | 117 |
| GPT-5.6-sol / medium | NAS101 | Moderate | A/B/C × R3 × 3 策略 | 27 |
| GLM-5.3 | NAS101 | Tight | A/B/C × R3 × 3 策略 | 27 |
| Kimi-K3 | NAS101 | Tight | A/B/C × R3 × 3 策略 | 27 |
| GLM-5.3 | Audit | Tight | 13 文档 × R1 × 3 策略 | 39 |
| 合计 | | | | **369** |

共 9 个模型×场景×预算单元、27 个策略 setting、123 组三策略匹配 block、369 个执行隔离池、1,476 个成员。每池 N=4，max_steps=30，max_evals=30。NAS outer seeds 为 2200/2204/2208；Search/Audit 池 R1、base seed 2200。种子标签不证明有效独立生成。

每成员最多 30 次普通模型决定及 1 次 forced final；协议修复占普通 step。因此正式任务最多 45,756 次逻辑模型调用，不含健康检查。物理 HTTP 尝试另按实际 transport retry 计；GPT 若继承 2 次 retry、其他模型为 0，上限为 52,452。不得将此上限或模拟反馈秒当作实际历时预测。

选择理由：DeepSeek Audit 两档是旧大幅负差；NAS 同时覆盖其 Moderate 负差和 Tight 正收益；Search Moderate 检查候选 serving 下的较小负差。GPT Moderate NAS 包含受单次本地 context stop 主导的旧负差。GLM/Kimi Tight NAS 保留原强/小正收益，GLM Tight Audit 提供通用 native 提示修复的跨模型正向历史对照。

不新增 DeepSeek Tight Search，不重新跑单体 ExpGym 或五模型排名矩阵，也不重跑 Qwen。未覆盖的旧格保留原数据与相应未复核标记，不自动外推为修复后普遍成立。预算退化、排名重排继续引用冻结旧报告；本研究主要更新同预算策略对照。

## 2. 源码、参数与隔离

自托管 runner 源码：`LLM_ExpGym-eval-docs-20260912`，Git `5bf5e5af817c2c6add48c7bae4eec4fe6e8110e9`，可执行代码同 `b3382b1c0b89ef1637e232f4b7eef68d55a54f12`。包含完整 graph identity / compact visible labels / native Audit 固定调用提示修复。沿用现有冻结数据、oracle、legacy 最终配置政策、task-abstention-v1、原采样与最高思考参数。

GPT 必须从实际 API 分支 `ccaf6adb8f7e82fa0f33d97c06cf5f7a33592122` 建独立 worktree，只移植上述对应修复，保留 Native Responses 的 opaque/encrypted 原生历史与实际 wire 参数省略规则。所有新 GPT 三策略统一将本地近似 context admission cap 131072 调为 262144。此值不是实际 tokenizer token 数，也不是声称代理服务已经保证 262144；源/config SHA、旧失败离线 admission 结果和网关验证另由执行计划记录。

首次实际 GPT 全池选择 NAS C / poolact / outer seed 2208，即旧失败设置的完整四人池。它是 27 个正式池之一：合法负分、缺答、正常耗尽均保留，不因不利结果另抽。若存在实质 provider/协议兼容故障，记录原尝试，先处理故障并另立恢复 cohort，不能偷偷覆盖或将失败改为成功。

每模型的新 config/plan/source/data 身份在放行队列前固定并记录 SHA。旧研究目录只读；本研究所有 dump、result、queue、provider 记录进入本目录下各模型命名空间。池间 task cache、进程与输出互不共享；同一池固定一个 ready 副本。

## 3. GPU 与队列

Slurm account `k2p`。每模型最多 4 节点、每节点 8 GPU。GLM/Kimi 各两个独立 TP16 副本；DeepSeek 沿用已验证的 4 个独立 TP8 / PP1 / EP1 副本，保留原冻结 SGLang runtime 与 0731 encoder，候选部署变量 `SGLANG_OPT_USE_MULTI_STREAM_OVERLAP=0`。不升级原 runtime，不重复全量权重哈希。

独立副本作业按正常 Slurm 调度；不抢占、取消其他研究作业。先 DeepSeek/GLM，Kimi 可在资源释放后接力。服务先冻结 deployment/launcher、足够申请时长、记录加载/ready/排空/释放时间及全 GPU allocation 成本。每个新副本通过实际 identity/health 和任务代表性的 native 协议检查后使用，不把 HTTP 200 当作语义正确证明。

统一动态队列，无重复批次屏障。自托管初始 workers=8/模型，GPT 先一个正式池，然后按实际稳定性启用并行；只按利用率/等待/资源调整并发，不改任务、输出长度、预算或依据分数决定重跑。所有并发调整与失败账本保留。

## 4. 分数与验收

主要策略端点：Search voted set F1；Audit voted exact evidence-set accuracy；NAS mean-individual Gap。同时保留 Search MI、Audit EA/LA 的 MI/MV、NAS raw accuracy / strict Gap / BoN / missing，以及已授权的 missing-config Gap=0 sensitivity。原 null/unknown 和真实零分不覆盖，不拿成功子集冒充完整端点。

先 item 内折叠 R3，再 item 等权汇总；NAS 每格只有 3 个任务簇，不把 36 成员当独立重复。报告 naive/cached/poolact 所有绝对分与 cached−naive、poolact−cached、poolact−naive；修前修后分别标 source/deployment cohort，差值不能唯一归因某个补丁。新研究不为报告润色另加显著性检验。

| 阶段 | 验收标准 |
| --- | --- |
| 冻结 | 精确 369 个槽位，三臂与重复完整、source/config/data 身份、输出命名空间及启动前 SHA 有据可查 |
| 执行 | 每个计划槽位有终态或明确未执行原因；原请求/回复、成员 trace、失败与花费完整；不按分数删换 |
| 工程 | 修复相关 CPU 测试通过；新服务的真实 native 内容、tool IDs/history 和 final 路径无已知传输损坏；异常按实际证据归因 |
| 分析 | 完整分母与缺答口径，未舍入值计算对照，三主问题范围清楚；正、零、负与未知全部展示 |
| 交付 | 主报告、详细报告、聚合/逐池 CSV、全部原始 dump 及完整索引；成稿后一次独立数字/逻辑复核；增量扫描和 github-tn 发布后核验 |

科学结果是否符合预期不是工程验收门槛。正常的 PoolAct 负差必须保留并解释，不能再把它当成必然存在 bug 的证据。新增实验/更改评分或提示需新登记，不能连续增加重复直到方向转正。

## 5. 输出与历史参照

本地新原始数据入口：本目录 `deepseek/`、`gpt/`、`glm/`、`kimi/`。最终报告与索引将放在 `report/`，包含既有五模型冻结报告和本轮修复后证据的双向链接，不覆盖历史归档。

旧完整矩阵：Git commit `6c63f1c03c88683fa55be5cafcbb8122ac8fadaa` 下 `results/five-model-ranking-20260911/`。上一轮有限 N2 smoke 与漏洞诊断：Git commit `d2cd3089d1d34a19e9c03dd5d38a7fd01be608cc` 下 `results/eval-integrity-diagnostics-20260912/`。该 smoke 不是本轮 N4/max_steps30 的正式替代。

GPT 本地 cap 的产品侧参考：2026-09-12 官方模型页列明 GPT-5.6-sol context 1,050,000 / max input 922,000 / max output 128,000（https://developers.openai.com/api/docs/models/gpt-5.6-sol）；这不替代实际 Sub2API 通路验证，不授权改变原 wire 参数或删除原生历史。
