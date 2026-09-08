# Kimi-K3 / ExpGym / PoolAct：论文设定核对

核对日期：2026-09-07 UTC。任务分类为 **Custom study**：使用本地 Kimi-K3 权重与 SGLang，在论文设定的任务矩阵上新增模型结果，并扩展到当前仓库的完整 PoolAct 矩阵。Kimi-K3 与本地服务并非论文中的模型/提供商，因此不能称为原论文结果的 paper-exact reproduction。

> 当前协议身份：正式 `full_v3` 使用冻结的 `evaluation_recovery_v3` / `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`。这是保留论文任务矩阵及预算、经本地适配和三类最小边界修复的自定义评测，非原仓库逐字节复现。v1/v2结果、诊断和成本原位归档，不混入v3正式分数；下文注明版本的smoke/pilot统计均不能当作v3全量率。

## 版本与证据

- 代码初始版本：`LLM_ExpGym@703719150e8d44712ace50d6439686423dcd1328`。
- 论文版本：`expgym-paper@f763d3877f6970a918c0a163099c409ea067dda6`，以 `versions/iclr2026/main.tex` 为准。论文根 `README.md:5`、`versions/README.md:4,9` 明确当前工作版本为 ICLR 2026；NeurIPS 2026 是迁移前快照。
- 已读本仓库 `.agents/skills/expgym-runner/SKILL.md` 及两份 references，并核对两套 runner 的 `--help`。
- 当前正式源码与环境清单：[evaluation_recovery_v3/manifest.json](../provenance/evaluation_recovery_v3/manifest.json)，完整源码包及合并diff在同目录；当前正式矩阵见 [full_v3/manifest.json](../runs/full_v3/manifest.json)。初始commit不能代替该source hash。
- 除显式标为v3的证据外，此文件的源码行号针对上述初始版本。后续适配与边界修复以冻结源码包、合并diff、各阶段manifest及数据/环境清单为准，不能将初始行号直接套用于修改后的文件。

### v3已应用的最小边界修复

1. [Answer行首解析](../patches/answer_parser_fix.patch)：经既有Markdown/空白归一化后，仅行首 `Answer:` 作为答案标签；防止Thought里的内联协议引用误截答案。原多行答案提取方式保留。
2. [无效final配置评分](../patches/invalid_final_score_fix.patch)：显式验证配置的字段、形状、类型、范围与有限数值，只将明确的模型无效输入按既有离线final路径记为有效0分；数据缺失、工具内部异常等仍阻止验收。此修改也明确拒绝原实现会忽略的超长列表尾部，属于需披露的输入边界修正。
3. [canonical JSON精确关联](../patches/json_eval_exact_lookup_fix.patch)：具有canonical JSON的已评估记录只与完整规范化JSON答案精确匹配，不再向包含该JSON子串的长正文错误绑定分数；未匹配时沿用原有 `best_evaluated_fallback`，不改变标签选择、fallback实现或budget eligibility。非JSON历史标识符仍沿用原规则。

这些修复可影响最终答案、分数关联及落盘内容，不能声称与原版输出字节不变；任务数据、oracle、生成参数、textual ReAct动作协议、预算及NAS语义提示未因这三项修复调整。服务/客户端适配等其他差异以完整冻结diff为准，不能把它们隐去而声称“只改了三处”。每次改源前均先让在途旧runner完成并归档；v3重新执行统一source的smoke、pilot及正式矩阵，不择失败项重跑后混用旧分数。离线raw复放仅是诊断与回归证据，不替换任何正式模型结果。修复经过与旧版本归档入口见 [RECOVERY_PLAN.md](../RECOVERY_PLAN.md)。

## 主要矩阵与验收数量

| 路径 | 任务 | regime 数 | repeats / agents | item-strategy 数 | agent traces |
|---|---|---:|---:|---:|---:|
| ExpGym Tuning | 9 HPOBench tasks | 3 | 3 reps | — | 81 |
| ExpGym Search | seed-1，18 whois + 17 whatis | 3 | 1 rep | — | 105 |
| ExpGym Audit | 13 ContractNLI docs，17 hypotheses | 3 | 3 fixed orderings | — | 117 |
| ExpGym 合计 | 论文主表单模型矩阵 | 3 | — | — | **303** |
| PoolAct paper subset | 18 whois + 13 Audit + NASBench101:A | 2 | 3 strategies × 4 agents | **192** | **768** |
| PoolAct repository full | 35 Search + 13 Audit + 9 HPOBench | 3 | 3 strategies × 4 agents | **513** | **2,052** |

建议完整交付采用 **303 ExpGym traces + 513 PoolAct item-strategy results / 2,052 agent traces**，然后按明确过滤条件从 PoolAct 全量结果导出 192-result 论文主表子集。这样共 2,355 agent traces，论文子集无需再调用模型。

192/768 是当前公开 runner 能明确表达的单 outer-repeat 主表矩阵。历史 NASBench101:A 的 outer-repeat 数量不可从公开材料精确恢复：论文核查脚本 `expgym-paper/scripts/verify_paper_claims.py:583-619` 对多个 `...nb101a_s*` 目录求均值，但正文未给具体种子/数量，原目录未随当前论文仓库提供。不要将 768 描述为已证实的历史真实总 trace 数。此次明确使用一个 N=4 pool、base seed 1206，另保留该偏差。

九个 HPOBench tasks 必须是：

```text
hpobench:paramnet:adult:steps
hpobench:paramnet:higgs:steps
hpobench:paramnet:letter:steps
hpobench:nasbench101:A
hpobench:nasbench101:B
hpobench:nasbench101:C
hpobench:nasbench201:cifar10-valid
hpobench:nasbench201:cifar100
hpobench:nasbench201:imagenet16-120
```

来源：`LLM_ExpGym/scripts/run_paper_sweep.py:61-71`；论文 `main.tex:227-232,318-323,582-589`。

## 固定参数

| 参数 | ExpGym | PoolAct |
|---|---|---|
| 模型 | 本地 Kimi-K3，记录 resolved served model ID 和 checkpoint fingerprint | 同左 |
| horizon / evaluation cap | 显式 `--max-steps 30 --max-evals 30` | 同左，每 agent 独立 |
| temperature | Tuning 0.7；Search/Audit 0.0 | 所有场景 0.7 |
| regimes | `cost_free,cost_moderate,cost_tight` | full 三种；paper subset 仅 moderate/tight |
| beta | free = infinity，moderate = 10，tight = 3 | 每 agent 同一 ceiling；总容量随 agents 增加 |
| seed | Tuning/Audit 1206,1207,1208；Search 1206 | base 1206，agents 为 1206,1207,1208,1209 |
| Audit order | 显式 `configs/audit_hypothesis_orders.json` 的三个固定排列 | 当前 runner 使用原数据的 hypothesis 顺序 |
| Search snapshot | `phantom_seed1`；loader 排序后 0:35 | full 0:35；paper 0:18 |
| Audit snapshot | `cc-large`，0:13，17 hypotheses | 同左 |
| strategies | 单 ReAct | `naive,cached,poolact` |
| reasoning | 主结果尽可能关闭 extended reasoning，保留普通 ReAct Thought | 同左；需服务端/请求级实证 |

`top_p=1.0` 是当前客户端默认值，论文正文未明确说明。当前 runner 无统一输出 token cap，若为了 Kimi/SGLang 运行设置 cap，须记录为新的实现参数，确保 smoke 中无截断。temperature=0 不保证分布式推理跨硬件字节级确定性。

### 本次真实服务验证后的固定选择

请求固定 `chat_template_kwargs={"thinking":false}`、`max_tokens=8192`。短探针可跳过reasoning；**136次HTTP、其中6次 `reasoning_content` 非空，是已归档v1 smoke的历史诊断**，不是当前v3全量调用数或reasoning率，见 [v1 smoke诊断](../reports/smoke_protocol_diagnostic.md)。provider当时 `usage.reasoning_tokens` 均报0，因此只能称“请求非thinking模式”，不能称严格关闭扩展思考；实际reasoning文本与reported token计数分开统计。v3正式结果必须从对应full manifest/dump独立统计，不复用任何smoke/pilot比例。K3文档推荐always-thinking模式，此设置亦偏离其推荐用法。原仓库只把assistant content放入下一轮ReAct历史，原始reasoning仍完整保存在API dump。此项限制须随正式结果披露。

固定服务源码的只读诊断进一步确认：`thinking=false` 关闭的是reasoning计数门控，故reported 0不证明实际token为0；parser即使只见think-close、没有think-open，也可能划分reasoning_content。现有HTTP dump是服务解析后的完整API响应，不含原始生成token序列，无法区分模型生成think-open与孤立close误分。此处“reasoning文本”均指服务器返回的字段，而非对内部过程的推断。证据、源码哈希及离线复现见 [REASONING_MODE_DIAGNOSTIC.md](../serving/REASONING_MODE_DIAGNOSTIC.md)。本实验未开启grammar或自定义logit硬约束。

保持所有策略统一的原始textual `Action: tool_name JSON` 协议，不将K3 native XTML工具标签自动转译。**30/45 traces触发missing_action、20个原始native响应随后触发该原因，同样仅属于已归档v1 smoke**；其4-step/N=2设置与正式30-step/N=4不同，不能当作v3全量失败率。当前v3 smoke与pilot诊断也必须按各自manifest单独解释，例如 [v3 pilot协议诊断](../reports/pilot_v3_protocol_final.md) 只覆盖该pilot的258traces。协议遵循失败不等同于runner/评分损坏或单纯知识能力低；最终v3 full的missing_action、forced final、native与reasoning统计须待全量对应审计报告。若后续测试native适配，必须独立矩阵与dump，不能混入当前主表。

代码证据：`run_paper_sweep.py:276-284,319-359,900-912`；`run_poolact.py:148-166,497-503`；`demo_experiment.py:34-45,87-94`；`expgym/task_restricted_search.py:120-140`；`expgym/task_evidence_audit.py:139-146`。实际只读构建任务已确认 303 jobs，分场景 81/105/117、三个 Audit order 各17项、上述 seed 集。

数据下载完成后须通过 loader 验证实际 0:18 为 whois、18:35 为 whatis；仅验证文件数不足。须保存每题/文档的 index→ID/type/difficulty 映射及数据 hash，避免后续排序变化使索引失去含义。

## 预算、墙钟与生成调用

Search/Audit 的 base cost = 300 simulated seconds，每个新反馈约280–320；moderate ceiling=3000、tight ceiling=900。Tuning base cost 必须来自 `data/hpo_tuning/oracle3.json` 的该 task `best_cost`。`demo_experiment.py:48-73` 在 oracle 缺失/异常时会静默降级为100，故验收必须确认9项 oracle 均命中，不能只看进程成功。

达到或超过 ceiling 时，尝试的 tool 调用及费用仍进入记录，但 observation 被扣留，随后强制提交答案；论文 `main.tex:205-208` 与 `expgym/react_loop.py:372-380` 一致。Free 的反馈费用不显示给模型。`max-steps=30` 仍可能另触发一次强制最终回答，因此每 agent 成功的逻辑生成调用上界为31，重试 HTTP 尝试不包括在内。

模拟费用不应作为 Slurm 墙钟估算：论文 `main.tex:218-219` 明确环境即时返回，`main.tex:745-747` 的3.9分钟至76.4小时是旧模型的估算反馈+模型时间，不是此任务实际运行时长。

完整主任务最多约73,005次逻辑生成调用（2,355×31）；仅论文子集主任务最多33,201次（(303+768)×31）。这是 horizon 上界，不能作为实际调用预测。实际 ETA 应按 scenario×regime×strategy 的 pilot 测得 wall time、token usage、重试数量和并发吞吐外推，并附30%–50%波动余量。应报告服务冷启动/权重载入、pilot、正式推理、聚合分别耗时；8-node 单模型分片不等于8个独立副本，吞吐不能机械乘8。PoolAct 的同一 pool 内 LLM 决策有串行锁；独立 item 可以并发以提高服务利用率。

## 可执行的矩阵命令

以下是初始公开 CLI 可接受的命令模板。先设置 `KIMI_EVAL_PY` 为 uv 评测环境的 Python 绝对路径、`KIMI_EVAL_BASE_URL` 为已验证的 SGLang chat-completions endpoint、`KIMI_EVAL_MODEL` 为实际 served model ID、`KIMI_EVAL_OUTPUT` 为本次独立输出目录，并从环境安全加载服务要求的 `OPENAI_API_KEY`。无认证本地服务可使用明确的非秘密 placeholder，但不能因此覆盖已有外部 API 配置。

在 `LLM_ExpGym` 根目录运行。下方 openai backend 本身不关闭 thinking，正式运行前须完成下节说明的兼容性验收；如果统一添加了 `sglang` backend/flags，保存实际最终命令并替换这里的 transport 部分。

```bash
"$KIMI_EVAL_PY" scripts/run_paper_sweep.py \
  --backend openai --models "$KIMI_EVAL_MODEL" --base-url "$KIMI_EVAL_BASE_URL" \
  --scenarios tuning,restricted_search,evidence_audit \
  --tuning-tasks all-hpobench --search-indices 0:35 --audit-indices 0:13 \
  --search-data-source phantom_seed1 --cc-split cc-large \
  --audit-orders configs/audit_hypothesis_orders.json \
  --cost-regimes cost_free,cost_moderate,cost_tight \
  --tuning-reps 3 --search-reps 1 --audit-reps 3 --seed 1206 \
  --temperature-tuning 0.7 --temperature-eval 0.0 \
  --max-steps 30 --max-evals 30 --trace-format v2 \
  --output-dir "$KIMI_EVAL_OUTPUT/expgym" --resume --dry-run
```

该 dry-run 已使用系统 Python3 只读核验为303 jobs。正式运行移除 `--dry-run`。如果 ParamNet 必须使用独立的兼容环境，将场景拆成 Search/Audit（222 traces）与 Tuning（81 traces），输出目录保持一致；仍须由最终 validator 对整张303-row manifest验收。不要将内置 `neural_network_training` smoke 当成9项HPOBench正式结果。

PoolAct full 可按下列循环展开；正式运行前先统一加 `--dry-run` 检查每条下层命令：

```bash
for regime in cost_free cost_moderate cost_tight; do
  common=(--backend openai --model "$KIMI_EVAL_MODEL" --base-url "$KIMI_EVAL_BASE_URL"
          --cost-regime "$regime" --strategies naive,cached,poolact --agents 4
          --seed 1206 --temperature 0.7 --max-steps 30 --max-evals 30 --resume)
  "$KIMI_EVAL_PY" scripts/run_poolact.py "${common[@]}" \
    --scenario restricted_search --data-source phantom_seed1 --questions 0:35 \
    --output-dir "$KIMI_EVAL_OUTPUT/poolact/$regime/search"
  "$KIMI_EVAL_PY" scripts/run_poolact.py "${common[@]}" \
    --scenario evidence_audit --cc-split cc-large --questions 0:13 \
    --output-dir "$KIMI_EVAL_OUTPUT/poolact/$regime/audit"
  for task in hpobench:paramnet:adult:steps hpobench:paramnet:higgs:steps \
              hpobench:paramnet:letter:steps hpobench:nasbench101:A \
              hpobench:nasbench101:B hpobench:nasbench101:C \
              hpobench:nasbench201:cifar10-valid hpobench:nasbench201:cifar100 \
              hpobench:nasbench201:imagenet16-120; do
    "$KIMI_EVAL_PY" scripts/run_poolact.py "${common[@]}" \
      --scenario tuning --tuning-task "$task" \
      --output-dir "$KIMI_EVAL_OUTPUT/poolact/$regime/${task//:/_}"
  done
done
```

原 `run_full.sh` 无法透传30-step参数，且依赖Docker，不能未经修改作为此次严格协议入口：`scripts/run_full.sh:51-63,132-158,170-201` 均未设置 horizon。两个Python runner默认都是10 steps。

## 已发现的实现/历史差异

1. **thinking 不统一**：ExpGym CLI 的 backend choices 没有 vllm/sglang（`run_paper_sweep.py:859`），且 `ns.vllm_disable_thinking=False`（:463）。OpenAI路径仅传温度/seed等，不传 `reasoning` 或 `chat_template_kwargs`（`demo_experiment.py:117-129`）；OpenRouter builder默认发送 `reasoning.enabled=false`（`expgym/llm_clients.py:390-420`）。PoolAct虽支持 `--backend vllm --vllm-disable-thinking`，不能用这一点推定另一条路径已关闭thinking。需在共同客户端和两runner显式记录可验证的Kimi生成模式，或者服务端固定模板并把模板hash及resolved参数加入provenance。
2. **历史 PoolAct 混有两种协议**：论文主表P上标L/U区分locked与prelock（`main.tex:585,589,601-613`）。当前 `paper-graph-lock-v2` 是修正后的locked实现；不能把Kimi新结果称为对历史U行严格复现。当前协议还修正首轮图注入、pending claim清理、强制回答加锁、最早虚拟完成缓存及语义投票（`docs/poolact.md` Historical CARC runs）。
3. **Audit顺序不等于seed**：ExpGym使用3个JSON排列；缺失orders文件会静默返回None（`run_paper_sweep.py:276-284`），必须验证存在/hash/三个不同完整排列。PoolAct每agent虽有独立seed，但 `hypothesis_order=None`，不会随机排列hypotheses（`run_poolact.py:155-163`）。
4. **历史Tuning outer repeats未恢复**：见上文192矩阵限定。新实验若增加多个outer pools，应明确列为custom repeat extension，每个outer seed下仍用4个agents，不能混成一个更大的pool。
5. **summary不是完整论文表**：`scripts/summarize_traces.py:30-36,151-154` 递归收集所有JSON且不先过滤trace schema。将整个结果root传入会误读summary/manifest/result。正式聚合需从计划manifest选有效trace，单独解析PoolAct result。
6. **真实结果与完整性不同**：零分、低Gap、预算中止、horizon强制回答均可为有效模型结果；传输失败、失配source/config hash、score recompute失败、缺失agent文件应列作执行失败并重跑，不能补0伪装完成。
7. **解析前8000字符上限可移除完整Action**：原仓库 `expgym/react_loop.py:304-310` 在常规响应解析前按Python字符截断；这不是本次API的8192 token生成上限。已归档 `evaluation_recovery_v2` 的smoke确认一例：Audit/Moderate/cached agent1的10,318字符响应，在字符10,253处生成完整 `Action: human_feedback` JSON；API为`stop`且仅2,174 completion tokens。截断后实际出现`missing_action`、0次工具执行和强制最终回答。完整响应可由解析器识别，因此这一例可以归因于解析前截断；不能推断其未截断后的最终表现，也不能计作v3全量事件。另须区分v1旧pilot只在长Thought中引用`Action:`、payload并非JSON的静态候选，后者没有证明合法动作丢失。证据与逐项边界见 [smoke_v2截断复核](../reports/smoke_v2_cap_review_20260907_0944.md)。当前v3保留原有8000字符上限，未因该截断事件修改提示或截断协议；在报告中将经复核的截断事件、普通协议遵循失败及API生成长度截断分别披露。v3另有上节明确列出的边界修复，不应把“保留此上限”理解为整个源码未改。
8. **NAS101 B/C原提示与实际编码不一致，主矩阵保留原提示**：v3 `expgym/task_tuning.py:302-317` 对A/B/C使用同一套A型二进制邻接边提示。实际 `compact_nasbench101.py:56-82,199-212` 中，B是9个 `edge_0…edge_8` categorical selectors，值0…20，按反向列序bit-ID选择边、重复ID合并，并不是21个行序二进制边；C是21个[0,1]优先级加 `num_edges`（0…9），按行序位置选择top-k，并不是直接把0/1解释为关闭/开启。该矛盾是静态输入协议限制，不能只据此断言某条C轨迹失败或估计因果影响。当前明确保留原论文/仓库NAS提示，[提示修订候选](../patches/nas101_hints_fix.patch) **未应用**，不给主矩阵额外编码提示。冻结绑定证据 [nas101_hints_status_evaluation_recovery_v3.json](nas101_hints_status_evaluation_recovery_v3.json) 记录 `retained_original_paper_hints=true`、`candidate_patch_applied=false`、同一v3 source hash，以及提示/编码/候选文件的SHA256；B/C结果须随此限制解读。若未来应用修订，需独立协议/源码身份与结果，不回写当前主表。

## 主表、额外分析与交付指标

ExpGym应导出每个regime的7个维度：ParamNet/NASBench201/NASBench101 Gap，whois/whatis F1，Audit LA/EA。Gap严格按 `max(0, (perf-mean_perf)/(best_perf-mean_perf)*100)`，使用本地 `oracle3.json` 中该task的参考值；有效结果允许超过100，无有效perf记0。先每task平均3rep，再平均每family3task。Search按question macro F1；Audit每trace先17假设均值，再对13docs×3order均值。来源：论文 `main.tex:272-294`。不要将原始HPOBench `answer_perf` 直接放入Gap列。

PoolAct主表每regime/strategy输出 Search MV F1 / mean-individual F1、Audit voted LA / exact evidence-set EA、Tuning best-of-N Gap / mean-individual Gap。Tuning MI须先逐agent计算并裁剪Gap再平均，不能把平均raw perf后统一裁剪。PoolAct聚合方法应调用原 `expgym.poolact.aggregate_results`，保留其语义集合majority vote及tie规则（:204-282），禁止事后选择最好Search答案。论文核心子集过滤为moderate/tight、whois0:18、Audit0:13、NASBench101:A；full表保留其余所有任务。

主dump可直接派生：每task/per-regime得分、bootstrap区间（以独立item为unit，Audit以doc为cluster）、agent MI、tool/evaluation次数、abort原因、模拟费用、actual wall time、token usage、重试、unique action与duplicate/cache统计、Audit verification效率、Search证据支持诊断。不需为这些重复调用模型。单模型不能重现原文六模型的Kendall排名统计；可列原论文已发表分数作静态参照并注明新模型/提供商/协议差异。

下列论文分析是额外有调用成本的矩阵，应单独列项目与预计时间，不混入303+2,052主矩阵：

- **Naive N=1…8 scaling**：论文只针对Haiku、18 whois+13 Audit+NASBench101:A、moderate/tight。每item保留8个不同seed的naive agent，再离线枚举各N子集；所有N共有255个非空子集，不应为每子集调用LLM。Kimi仿照此设计是新研究。完整另跑N=8的3策略需64 items×3×8=1,536 agent traces；N=4协调结果可复用主矩阵，不能通过裁剪N=8 coordinated traces伪造N=4。理论可复用同配置naive的前4个独立seed，但现有runner不支持追加4agent后合并为原生N=8结果，需专门manifest与验证。
- **Reasoning-lock ablation**：论文Haiku N=8 Tight whois18题，locked/unlocked比较（`main.tex:666`）。Kimi需显式实现/记录unlocked图共享变体，现有公开CLI没有该策略；若已有N=8 locked，新增unlocked为18×8=144 agent traces。
- **Extended reasoning ablation**：论文DSV3.2/Gemini，whois18题×3regimes×Think/Standard=每模型108traces（`main.tex:931`）。Kimi在具备可验证的双模式时，可复用主ExpGym中54条Standard whois，另跑54条Think。不存在可用的non-thinking模式时，必须报告该事实，不制造两种名称相同的配置。

以上额外实验不应成为验证两runner是否跑通的前置条件。主任务完成后可按用户“全部结果”的最终scope扩展；是否执行以及实际counts须由任务manifest明确，不能遗漏已承诺项目后称全部完成。

交付至少包括：完整计划manifest、resolved配置/命令、版本和数据/model fingerprint、uv lock/environment export、Slurm job/node/GPU记录、服务启动日志、真实smoke dump、完整ExpGym traces、每PoolAct result及所有agent JSON、失败重试清单、完整性validator结果、逐item/agent表、论文格式汇总表及full扩展表、ETA与actual对照、简明中文总结。完成标准是计划manifest覆盖100%、所有必需score校验通过、pending_claims=0、每项文件齐全且可resume、再从原dump独立重算报告数值相同。
