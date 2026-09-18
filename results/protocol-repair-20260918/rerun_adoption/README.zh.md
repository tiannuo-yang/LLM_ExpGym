# HPO 补跑采用与旧—新对照

本公开副本对48个槽位的私有提供方端点做了发布投影：两份来源CSV的`provider_base_url`以及最小评分包的`config.base_url`改为稳定的`endpoint_sha256:`标识，共144个字段；49个官方OpenRouter端点保留。其余配置、终答、评分和来源值逐项不变。原始端点及完整原件保留在冻结本地存档。

[PUBLIC_ENDPOINT_PROJECTION.json](PUBLIC_ENDPOINT_PROJECTION.json)分别绑定原始与公开文件SHA、实际运行配置SHA与公开投影配置SHA；原`FAIRNESS_MANIFEST.json`、runtime／result／config身份及科学CSV保持原字节。公开replayer固定投影凭证的payload摘要，再核验每个槽位，不能用公开配置的SHA冒充实际执行配置的SHA。[ORIGINAL_PUBLIC_REPLAY_CHECKS.json](ORIGINAL_PUBLIC_REPLAY_CHECKS.json)保留投影前的科学回放记录；当前`PUBLIC_REPLAY_CHECKS.json`明确记录两套身份。

`collector_review/`中的历史原件审查与67项边界测试仍绑定投影前包和原replayer版本，其hash没有被替换成新文件hash。它们作为原始科学审查证据保留；发布投影另外经过仅字段差异核验及新的公开回放。公开读者可验证投影后的字节、凭证与分数，无法由opaque端点摘要还原私有端点；原件到投影仅字段变化的证明来自读取本地冻结原件的采集检查。

本目录只采集事先冻结的 **97 个 HPO N4 池、388 个成员**。预定模型数量为 Gemini 49、GPT 9、GLM 10、Kimi 9、Qwen 19、DeepSeek 1；每次采纳一个完整四成员池。数量和槽位来自 `planning/hpo_versions/hpo_rerun_slots.csv` 与 `operations/queues-v2/*/BINDINGS.json`，不会根据补跑分数选择样本或重新抽样。

**是否完成 HPO 97 池采用阶段，以 [FAIRNESS_MANIFEST.json](FAIRNESS_MANIFEST.json) 为准。**只有 `status: PASS` 且 `adoption_ready: true`，全部 97 池才已通过完成性、来源、配置、数据、终答、评分与图检查。运行尚未完成时，只输出进度和已完成样本。

这是 `hpo97_stage_only`，**不是整份主实验的最终封版门禁**。Search／Audit 另有21个运行时终答接受变化的完整槽位对照；下游 `control_flow_adoption` 阶段必须同时确认本阶段97池和额外21槽均完成，再生成最终正式4,698行采用表。本目录的4,698行表是先应用HPO替换的中间采用层，不能提前当作全任务控制对照已经全部完成。

## 采集与校验

[collect_hpo_reruns.py](collect_hpo_reruns.py) 不调用模型，按以下条件验收每池：

1. 冻结的旧 slot 对应唯一新 job，队列 plan、matrix、旧采用来源和运行源码 SHA 全部匹配；固定四成员，seed 顺序一致，不从不同尝试拼池。
2. generation、任务、预算、工具协议、上限与旧配置一致；实际新 backend、模型、endpoint、缓存配置与冻结的新 plan 一致。Gemini provider 迁移属于预先声明的干预，并有相应基线补跑。
3. 任务配置、预算 oracle、NAS 表、解码器、表清单及关键依赖 SHA，与历史输入逐项核对并实读验证；NumPy 排序语义保持一致。
4. 已有 `completion.json` 且执行成功；对全部 invocation 文件逐项重新计算 SHA，并用正式运行器再次进行只读 exact identity／终端／评分校验。
5. 重新提取四成员最后模型回复，按冻结正式 parser 与 HPO `legacy` 规则从可见评估选择最终配置，并独立查表核对最终性能。重新计算全部六项 `raw_perf_mi/bon`、`gap_mi/bon`、`gap0_mi/bon`，核对保存的完整池聚合。
6. [verify_graph.py](verify_graph.py) 检查实际保存的图快照及路径端点；不同完整配置不能共享显示身份。naive/cached 标为不适用，真实同配置自环允许。图验收的范围、反例和测试见 [GRAPH_ACCEPTANCE.zh.md](GRAPH_ACCEPTANCE.zh.md)。

`None` 的含义按原任务协议保留：正常没有最终配置时，严格性能／Gap 保持空；Gap0 使用既有正常无答案处理。待完成、基础设施失败、来源不匹配均不补零，也不伪造成功。严格 `score_complete: false` 本身不是要求重跑的理由。

## 输出

- [progress/slot_status.csv](progress/slot_status.csv)：全部97池当前状态，包含 pending、验证失败及成功记录。
- [progress/completed_slot_scalars.csv](progress/completed_slot_scalars.csv)：仅已完成并全部通过的池。
- [progress/member_scores.csv](progress/member_scores.csv)：完整四成员的终答、重新提取文本、性能、评分来源、可见记录及原件 SHA。
- [progress/verified_sources.csv](progress/verified_sources.csv)：旧来源 SHA、新来源 SHA、job、代码／parser／graph、generation 配置摘要、数据身份和完整成员数。
- [NEW_RUNTIME_COMPARISON.csv](NEW_RUNTIME_COMPARISON.csv)：97池 × 6指标，共582行，分别保留历史采用分数、旧轨迹重评分、实际新运行分数及两段差值。pending 的新值保持空，并同时提供状态；不能把空值解释为零分。
- `progress/scoring_inputs.jsonl.gz`：公开最小评分包，保存终端公开文本、可见评估记录、已核验数据性能证书和来源身份，不含 API key 或原始请求归档。
- `new_official/slot_scalars.csv`：仅全部97池通过后生成的 **HPO阶段4,698行表**；严格替换原4,698槽中的97槽，其余4,601条已重评分记录保持不变，再交下游额外21槽采用阶段。
- `new_official/SOURCE_SELECTION.csv`：完整4,698采用来源；新运行与旧轨迹来源明确分开，保留旧 SHA。
- `new_official/hpo_rerun_slot_scalars.csv` 与 `SOURCE_INVENTORY.csv`：97个实际替换记录及逐项来源。
- `adopted_hpo_code_versions.csv`：全部810个HPO槽位的新旧采用代码、结果SHA、实际运行parser、图模块及替换／复用原因。486条N1保留原运行，324个N4池中替换97池、复用227池。
- `adopted_hpo_model_budget_strategy.csv`：按模型、N1／N4、预算、策略汇总54组版本。一个组存在多个版本时列出全部版本，不用单个标签遮盖差异。
- `historical_hpo_versions_input.csv` 与 `HISTORICAL_CODE_INPUT_CHECKS.json`：去掉本地路径的810条历史版本输入及校验；8份历史完整源码树重新核验后记录parser、react loop、graph和POOLACT模块SHA。

代码表将 `adopted_run_parser_sha256`（实际产生轨迹的执行代码）和 `scoring_parser_sha256`（正式离线重评分代码）分开。复用旧轨迹不表示模型执行过新parser；旧记录没有Git提交号时保留空值，并使用已核验的完整源码树SHA定位代码。图模块存在也不表示N1或naive／cached实际消费了共享图。

本目录只替换指定 HPO N4 池。486条 HPO N1 行为没有补跑，也不会用离线重评分伪造行动变化。

## 复算

在完整本地存档上，所有路径显式传入；运行时数据目录及冻结队列仍需可访问：

```bash
/path/to/evaluation-python -B collect_hpo_reruns.py \
  --repair-root /path/to/protocol_repair_20260918 \
  --repo /path/to/LLM_ExpGym \
  --output /tmp/hpo-rerun-adoption
```

发布前添加 `--require-complete`；若不足97池或任一验证失败，命令以非零状态结束，manifest 不会标记正式可采用。

仅用公开最小评分包，可再次重新提取终答、选择可见配置并计算全部池指标：

```bash
python3 -B replay_hpo_reruns.py \
  --repo /path/to/LLM_ExpGym \
  --adoption /path/to/rerun_adoption \
  --base-scalars /path/to/rescore/main/slot_scalars.csv \
  --base-sources /path/to/rescore/main/SOURCE_SELECTION.csv \
  --rebuild-output /tmp/hpo-adoption-rebuilt \
  --output /tmp/hpo-rerun-replay.json
```

公开回放验证评分数据与规则；查表性能使用采集时已经实际核验的证书。它不冒充再次读取私有原始请求，也不重新模拟共享图或模型决策。完整采集模式另行验证这些原件及源代码身份。

传入两个base表时，回放将使用实际重新算出的97池分数替换旧轨迹重评分层，重建4,698行成绩及来源选择表，并逐字段检查其余4,601槽保持一致。只有97池完整门禁通过时才导出完整采用表；pending时仅导出实际已完成的重算池表。base必须是旧轨迹的全量重评分层，不能用最早历史旧分数代替。

三层分数及差值对照另可从上述真正重算的池表复建，不读取原比较表作为输出模板：

```bash
python3 -B rebuild_runtime_comparison.py \
  --historical-scalars /path/to/gemini-openrouter-20260917/main/slot_scalars.csv \
  --rescored-scalars /path/to/rescore/main/slot_scalars.csv \
  --runtime-scalars /tmp/hpo-adoption-rebuilt/completed_slot_scalars.csv \
  --adoption /path/to/rerun_adoption \
  --output /tmp/hpo-comparison-rebuilt
```

该步骤重算582行的三层指标和两段差值，并与公开CSV逐字节核对；结果记录在`RUNTIME_COMPARISON_CHECKS.json`。来源、队列收据、原件turn数量和图快照验收等字段属于完整本地采集的证据记录；公开回放重新计算评分与采用表，不声称重新执行了模型行动或读取全部私有原件。

在97池全部通过后，仅用公开文件即可重建810槽版本表和54组汇总：

```bash
python3 -B build_adopted_versions.py \
  --historical-input /path/to/rerun_adoption/historical_hpo_versions_input.csv \
  --adoption /path/to/rerun_adoption \
  --output /tmp/hpo-code-versions
```

`formal_scoring_helper_sha256`记录本次离线采集所用helper文件。公开版本为无`.git`环境增加历史parser capsule加载与SHA检查，helper SHA因此由`a8e3c2c63c57a7a43e3f7887446d8006d0c60aa7b3d029774028ec25a72342e8`变为`5534e0df2d131e6131af1c82800bc4ee2b7fc4be96472bb72b356a46a33405a9`；正式新parser和评分函数保持不变，模型运行的冻结源码树仍为`cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02`，没有因此改动运行时输入或重新生成轨迹。
