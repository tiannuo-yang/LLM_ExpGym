# 终答控制流补跑与最终采用层

本目录将两类必要的新运行对照合并到原有 4,698 个主实验槽：HPO 的 97 个完整池，以及 Search/Audit 的 21 个完整运行槽（2 条单智能体、19 个四智能体池，共 78 个成员）。另有一个独立的 GLM Whois β=20 单智能体对照，不与主实验重复。补跑集合按原始 API 资格与修复前后控制流差异预先确定，采用所有预注册结果，不按分数挑选，不拼接不同运行的成员。

只有 `FAIRNESS_MANIFEST.json` 同时满足 `status=PASS`、`adoption_ready=true` 与 `total_main_runtime_adoption=true`，并核齐 HPO 97、主实验辅助 21/78 和独立 sweep 1，`new_official/` 才是正式总采用层。单个子集验收通过不等于总交付完成。

- `aux_rescore/scoring_inputs.jsonl.gz`：新运行的最小评分输入，包含终答正文、终端资格、任务 gold 与 Audit 可见工具记录及来源 SHA；不含完整轨迹、请求头、API key 或推理签名。
- `aux_rescore/{slot_scalars,agent_rows,sample_diff,SOURCE_INVENTORY}.csv`：逐槽、逐成员、三层分数差异和新运行来源。
- `new_official/slot_scalars.csv`：最终全部 4,698 槽；`SOURCE_SELECTION.csv` 给出每槽唯一采用来源。
- `new_official/sample_diff.csv`：全部 4,698 槽的旧评分、已有轨迹重新评分、正式采用评分，以及来源是否被新运行替换。
- `new_official/auxiliary_slot_diff.csv`：21 个 Search/Audit 辅助对照子集。
- `SWEEP_CONTROL_GATE.json` 与 `sweep_rescore/`：独立 β=20 对照及完整 Whois sweep 采用层。
- `MODEL_ACCEPTANCE/`：用于按模型释放计算资源的已完成子集证书，明确不代表总采用层通过。
- `VALIDATOR_REVISION_NOTES.json`：采集器对旧/新记录格式和已批准执行快照的校验修正记录；原件、运行时与分数未因此修改。

旧结果和“已有轨迹重新评分”分别保留在原始交付与 `../rescore/`，本目录不会覆盖它们。已有轨迹重评分仅修复终答解释与投票；改变实际停答或图共享的情况，采用这里的真实新运行作为正式对照。

## 离线复算

在仓库根目录执行，不需要 Git 历史、私有原件或模型 API：

```bash
python tools/replay_control_flow_results.py \
  --inputs results/protocol-repair-20260918/control_flow_adoption/aux_rescore/scoring_inputs.jsonl.gz \
  --output /tmp/expgym-aux-replay
```

该命令真正重新提取终答、重算全部成员分数及投票，再生成四张 CSV。先用 `replay_hpo_reruns.py` 将 HPO 最小输入和已重评分主表重建成 HPO-stage，再将它与以上新的辅助结果合并：

```bash
python tools/rebuild_control_flow_adoption.py \
  --hpo-stage /tmp/expgym-hpo-replay \
  --hpo-manifest results/protocol-repair-20260918/rerun_adoption/FAIRNESS_MANIFEST.json \
  --aux-dir /tmp/expgym-aux-replay \
  --total-manifest results/protocol-repair-20260918/control_flow_adoption/FAIRNESS_MANIFEST.json \
  --base-legacy-scalars results/protocol-repair-20260918/rescore/main/slot_scalars.legacy.csv \
  --base-rescored-scalars /tmp/expgym-rescore-main/slot_scalars.csv \
  --base-sources /tmp/expgym-rescore-main/SOURCE_SELECTION.csv \
  --output /tmp/expgym-main-adoption
```

合并器严格验证 97/21/78 与 sweep 门禁，并逐字节校验最终主表、来源表和两张分数对照表。它是来源选择复算；真正评分由此前两个回放器执行。完整统一核验入口另见交付根目录说明。

静态系统消息、任务提示词、预算、随机种子、generation 参数及数据身份均与对应历史实验核对。PoolAct 在其他成员开始后可能已出现动态 claim，因此新旧共享状态后缀不要求相同；所有新运行初始完整消息仍逐字对应其原始 API 请求。DeepSeek 使用保留其历史任务提示词的独立执行快照，最终清单分别记录各模型的完整源码树、代码提交和解析器 SHA。

新运行与旧运行的分数差包含重新采样与并发顺序差异，不能将整段差值解释为某一代码修复的独立因果效应。选择标准是预注册的控制流或共享状态缺陷，分数升降均采用。
