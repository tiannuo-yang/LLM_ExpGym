# LLM ExpGym

**最终报告与轻量数据发布（固定于 `ad03e8c`）**

[中文报告](results/paper-analysis-20260916/README.zh.md) · [数据与方法附件](results/paper-analysis-20260916/APPENDIX.zh.md) · [完整合并比较 CSV](results/paper-ad03e8c-delivery-20260916/csv/COMPARISON.csv) · [72 行主比较](results/paper-ad03e8c-delivery-20260916/csv/MAIN_COMPARISON.csv) · [数据入口与来源索引](results/paper-ad03e8c-delivery-20260916/README.zh.md)

本版本仅保留这份六模型报告所用的冻结分析表、来源索引、工具及仓库运行代码。报告与分析数据按指定提交保留，重复副本合并到唯一文件；失败实验、被替换运行和中间结果的材料留在本地归档。公开索引仍记录缺失状态及 369 个整池替换，便于解释最终采用关系。原始 API dump 和完整 trajectory 未公开。

在仓库根目录运行 `python3 tools/verify_lightweight.py` 可校验轻量包；文件身份见 [LIGHTWEIGHT_MANIFEST.json](LIGHTWEIGHT_MANIFEST.json) 和 [SHA256SUMS](SHA256SUMS)。[来源说明](results/paper-ad03e8c-delivery-20260916/provenance/README.zh.md) 区分当前文件、历史构建脚本与完整本地交付。本次整理没有重跑实验或重评分；关于 `expected_units` 与 Audit 调用计数的两处说明已补充到 [CSV 字典](results/paper-ad03e8c-delivery-20260916/csv/CSV_DICTIONARY.zh.md)，冻结报告及数值保持原样。

获取轻量主分支时，请限定分支下载：

```bash
git clone --single-branch --branch main https://github.com/tiannuo-yang/LLM_ExpGym.git
```

其他保留分支可能仍引用旧实验历史；下载所有分支不属于轻量主分支的体积范围。

本研究分支已从先前验证的 `5bf4ff7` 执行版本集成运行修补，并增加 GLM scaling、Low thinking 与 PoolAct 消融支持；研究范围见 [GLM follow-ups](docs/glm-followups-study.md)。冻结报告及其数据保持原字节，代码变更不代表重跑或替换历史结果。当前文件身份记录于轻量清单，运行版本另由每次研究的源码身份绑定。以下为运行与安装说明。

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
