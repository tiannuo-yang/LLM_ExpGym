# LLM ExpGym

**主报告：已补齐 Gemini 结果**

[完整主报告](results/paper-analysis-20260916/README.zh.md) · [数据与方法附件](results/paper-analysis-20260916/APPENDIX.zh.md) · [Gemini 补齐来源与数值表](results/gemini-openrouter-20260917/main/README.zh.md) · [六模型 Whois 预算报告](results/gemini-openrouter-20260917/whois/README.zh.md) · [接口与设置对应关系](results/gemini-openrouter-20260917/SETTINGS.zh.md)

2026-09-18 已将现有 Gemini 补齐结果合入主报告原路径，并同步更新排名、regret、附件与英文摘要。主实验保留原 4,682 个完成结果，只补 Gemini 的 16 个缺项，执行完成 4,698/4,698，严格评分完整 4,687；Gemini 为 783/783。此次文档更新没有新增模型调用。Whois sweep 的 Gemini β=1、5、15、20 各 39 题已完成，β10 复用原 39 份结果。新项使用 OpenRouter，历史 Gemini 使用 Sub2 API，报告中标明混合来源。

**冻结报告与原数据（`ad03e8c`）**

[冻结中文报告](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ad03e8c42ca501016176ee1bc407b38499178506/results/paper-analysis-20260916/README.zh.md) · [冻结附件](https://github.com/tiannuo-yang/LLM_ExpGym/blob/ad03e8c42ca501016176ee1bc407b38499178506/results/paper-analysis-20260916/APPENDIX.zh.md) · [冻结合并比较 CSV](results/paper-ad03e8c-delivery-20260916/csv/COMPARISON.csv) · [冻结 72 行主比较](results/paper-ad03e8c-delivery-20260916/csv/MAIN_COMPARISON.csv) · [冻结数据入口与来源索引](results/paper-ad03e8c-delivery-20260916/README.zh.md)

冻结版保留这份六模型报告所用的分析表、来源索引和工具。原报告五份被更新的文档另存同目录 `*.ad03.*`，原字节与 Git blob 身份仍受轻量清单校验；其余冻结分析数据保持原样。失败实验、被替换运行和中间结果的材料留在本地归档。原公开索引仍记录当时的缺失状态及 369 个整池替换；补齐后的采用关系见新版逐项来源表。原始 API dump 和完整 trajectory 未公开。

在仓库根目录运行 `python3 tools/verify_lightweight.py` 可校验轻量包所有文件身份及原冻结版的计数；文件身份及原文归档映射见 [LIGHTWEIGHT_MANIFEST.json](LIGHTWEIGHT_MANIFEST.json) 和 [SHA256SUMS](SHA256SUMS)。[来源说明](results/paper-ad03e8c-delivery-20260916/provenance/README.zh.md) 区分冻结文件、历史构建脚本与完整本地交付。新增实验数据保留在独立补充目录，主报告通过明确链接采用；冻结 CSV 不被覆盖。关于 `expected_units` 与 Audit 调用计数的两处说明见 [CSV 字典](results/paper-ad03e8c-delivery-20260916/csv/CSV_DICTIONARY.zh.md)。

获取轻量主分支时，请限定分支下载：

```bash
git clone --single-branch --branch main https://github.com/tiannuo-yang/LLM_ExpGym.git
```

2026-09-17 的轻量整理已将当时的旧分支完整留在本地 Git 归档。本次补充只更新 `main`；其他并行研究分支的内容不属于本轻量发布。

以下为仓库保留的运行与安装说明。根目录运行代码仍沿用冻结报告发布时的版本，其来源记录在轻量清单中；本次 OpenRouter 补跑使用独立运行时，版本与设置见补充实验目录。

One repository, two experiment paths:

- **ExpGym**: one ReAct agent on tuning, restricted search, and evidence audit.
- **PoolAct**: multiple ExpGym agents sharing completed observations and an
  exploration graph.

Both paths write strict JSON results by default, recompute the saved answer's
score, and resume only outputs that still match the current configuration and
source tree, selected data, and evaluator-dependency identities.

## Setup

Use Python 3.9+ for the main runner. The complete benchmark additionally needs
the pinned Python 3.7/scikit-learn stack for ParamNet: use the supplied Docker
wrapper or a separately verified equivalent legacy environment.

```bash
bash scripts/setup.sh --with-data
bash scripts/check.sh
```

The setup creates `.venv`; all shell entry points use it automatically. The
check command compiles the repository, runs the unit suite, and executes both
ExpGym and all three PoolAct strategies with the deterministic fake backend.
Setup verifies every source file before use. It converts NASBench101/201 to the
fixed fidelities used by the paper (108 and 200 epochs), checks their published
oracles, and never accepts interrupted downloads.
The first setup downloads about 3.2 GiB transiently and retains about 215 MiB
of HPO data; the first HPO run builds the Docker image.

Configure one real backend. For local Sub2API:

```bash
set -a
source /path/to/sub2api/.sub2api-client.env
set +a
```

Or export `OPENROUTER_API_KEY` / `OPENAI_API_KEY`. See `.env.example` for model,
URL, cache, retry, and external-data overrides. Secrets are never written to
result files.

## Small real runs

ExpGym, using the built-in tuning task:

```bash
bash scripts/eval_model.sh \
  --backend sub2api --model gpt-5.3-codex-spark \
  --max-steps 4 --max-evals 3 \
  --output-dir runs/expgym_smoke
```

PoolAct with two agents:

```bash
bash scripts/eval_poolact.sh \
  --backend sub2api --model gpt-5.3-codex-spark \
  --agents 2 --max-steps 4 --max-evals 3 \
  --output-dir runs/poolact_smoke
```

Use `--scenario restricted_search --questions 0:5` for five PhantomWiki
questions, or `--scenario evidence_audit --questions 0:3` for three ContractNLI
documents. Selectors are half-open: `0:5` means 0 through 4.

Each ExpGym job prints `score_check=ok` on success. Each PoolAct strategy writes
`result.json`, plus a validated trace for every agent. Batch runs also write
`summary.json`.

For OpenAI-compatible self-serving, use the lower-level runners with an explicit
`--base-url`, model and `--api-key-file`. `--tool-protocol auto` selects native
tools for compatible real clients; `text` retains the legacy protocol. Native
tool-only replies are valid, and delivered empty/length/protocol failures are
not free HTTP retries. Validate a real multi-turn tool interaction before a large
run; fake uses text and does not validate a provider's native template/parser.

Both runners expose `--max-tokens`, `--reasoning-effort`,
`--chat-template-kwargs`, `--top-p` and `--top-k`. Defaults retain legacy sampling
(`top_p=1`, top_k omitted); set model-specific choices explicitly and verify the
actual request. Record effective seed behavior rather than assuming a seed in
the request guarantees replay. See [portable-study.md](docs/portable-study.md).

## Full experiment

For a new concurrent self-served study, use the
[dynamic queue](docs/scheduling.md): freeze existing runner selectors with
`scripts/run_study_queue.py plan`, then execute the flat queue with `run`.
Independent invocations refill available slots across stage/repeat boundaries;
PoolAct agents still share only their own pool. The
[serving template](docs/serving.md) defaults to **4 nodes × 8 GPUs per model,
two TP16 replicas**, account `k2p`; planning does not submit GPU jobs.
The commands below retain the older sequential setup/Docker workflow.

Preview the entire one-model plan without API, data, or Docker calls:

```bash
bash scripts/run_full.sh \
  --backend sub2api --model gpt-5.3-codex-spark --dry-run
```

Run all ExpGym and PoolAct tasks, all three cost regimes, and all PoolAct
strategies:

```bash
bash scripts/run_full.sh \
  --backend sub2api --model gpt-5.3-codex-spark \
  --agents 4 \
  --output-dir runs/full_gpt-5.3-codex-spark
```

The ExpGym slice contains 303 traces per model: 9 HPOBench tasks × 3 repeats,
35 Search questions, and 13 Audit documents × 3 repeats, under each of the
three cost regimes. PoolAct covers the same items with `naive`, `cached`, and
`poolact`. `--repeats R` creates independent N-agent PoolAct pools; agents within
one coordinated pool are not independent repetitions. The one-model PoolAct
superset has 2,052 agent traces at N=4, R=1, not the smaller paper main table.

Runs are resumable by default. Re-running the same command skips only complete,
validated outputs; stale, corrupt, or source-mismatched artifacts are rerun.
Use `--part expgym` or `--part poolact` to run one half, and `--no-build` to
reuse an existing HPOBench image. The compact NAS tables avoid TensorFlow at
runtime and reduce NASBench201's old 16 GB loader to about 1.3 MB.

## Results

The primary `answer_perf` is tuning performance under the recorded final-answer
policy, name-level F1 for restricted search, and label accuracy for evidence audit.
Tuning defaults to historical `legacy`; `--tuning-final-policy submitted` is a
separately identified endpoint that scores the actually submitted configuration.
PoolAct aggregates tuning by best-of-N and classification tasks by normalized
voting.

```bash
.venv/bin/python scripts/summarize_traces.py runs/<experiment>
python -m json.tool runs/<poolact-batch>/summary.json
```

Advanced CLI options:

```bash
.venv/bin/python scripts/run_paper_sweep.py --help
.venv/bin/python scripts/run_poolact.py --help
```

See [docs/poolact.md](docs/poolact.md) for the PoolAct algorithm-to-code mapping,
concurrency contract, and output schema.

The [2026-09-10 bug-fix retrospective](docs/bug-fix-retrospective-20260910.md)
distinguishes generic correctness fixes, provider adapters and study settings.
The [follow-up plan](docs/maintenance-20260910.md) records acceptance and delivery;
published historical runs remain frozen under their original source identities.

For completed studies, use the [full-setting report workflow](docs/full-setting-report.md):
frozen inputs, complete regime/strategy tables, claim-focused analysis, an embedded
raw-dump/aggregate archive index, one post-draft independent check and authorized
delta-only publication. It includes the published Kimi-K3/GLM example without
making that study's model names, counts or repeats universal defaults.

For new deliveries, follow [efficient delivery](docs/efficient-delivery.md):
`scripts/package_run.py` automatically shards an explicit file inventory, combines
hashing/scanning/packing, and stream-verifies all contents without restoring the
full raw tree. Public clearance and scientific analysis remain separate checks.
