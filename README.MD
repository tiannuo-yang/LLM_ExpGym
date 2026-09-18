# LLM ExpGym

**正式主报告：协议修复、全量重评分与必要运行对照已采用**

[完整主报告](results/paper-analysis-20260916/README.zh.md) · [数据与方法附件](results/paper-analysis-20260916/APPENDIX.zh.md) · [新版交付与全部 CSV](results/protocol-repair-20260918/README.zh.md) · [新旧评分层](results/protocol-repair-20260918/score_layers/README.zh.md) · [HPO 486 条行为表](results/protocol-repair-20260918/hpo_behavior/README.zh.md) · [Whois 预算分析](results/protocol-repair-20260918/whois/README.zh.md)

2026-09-18 更新终答提取和投票规则，对全部相关 N1/N4 与 sweep 重新评分，并采用 97 个 HPO 池、21 个 Search/Audit 主实验槽和独立 1 个 sweep 槽的必要补对照。主实验 4,698 个结果全部采用，严格评分完整 4,687 个；正常无答案继续使用原有全分母规则，不将基础设施失败补零。 排名、regret、证据质量、配对案例和 POOLACT 增益同步重算；评分层与实际运行来源清楚区分。

历史报告和数据保持原字节：[修复前 297c3d0 报告](results/paper-analysis-20260916/README.pre-repair-297c3d0.zh.md) · [ad03 冻结报告](results/paper-analysis-20260916/README.ad03.zh.md) · [ad03 数据入口](results/paper-ad03e8c-delivery-20260916/README.zh.md) · [此前 Gemini 补齐](results/gemini-openrouter-20260917/README.zh.md)。原始 API dump、完整 trajectory、失败或被替换尝试继续本地留档；公开包保留最小复算输入、来源和代码身份。

`python3 tools/verify_lightweight.py` 校验所有公开文件及旧冻结版身份；`python3 tools/verify_protocol_repair.py --full` 重新执行新版评分与分析回放。见 [复算说明](tools/VERIFY_PROTOCOL_REPAIR.zh.md)、[LIGHTWEIGHT_MANIFEST.json](LIGHTWEIGHT_MANIFEST.json) 和 [SHA256SUMS](SHA256SUMS)。

```bash
git clone --single-branch --branch main --depth 1 https://github.com/tiannuo-yang/LLM_ExpGym.git
```

根目录包含正式 parser、投票与图身份修复；本次真实补跑所用原生客户端及冻结运行源码保存在 [studies/protocol-repair-20260918](studies/protocol-repair-20260918/README.zh.md)，版本不能与历史冻结结果混用。以下保留运行与安装说明。

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
