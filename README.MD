# ExpGym

ExpGym evaluates a model in expensive-world tasks and writes score-checked
ReAct traces. Use it to see how a model spends tool calls, handles budget
pressure, and what score it gets at the end.

The user-facing interface is four scripts:

| Script | Use it for |
|---|---|
| `scripts/setup.sh` | One-time native Python setup |
| `scripts/eval_model.sh` | Default smoke, built-in tuning, restricted search, evidence audit |
| `scripts/eval_poolact.sh` | Parallel agents with a shared cache, graph, and reasoning lock |
| `scripts/run_hpobench_docker.sh` | HPOBench / NASBench tuning in Docker |

Everything else is a helper or advanced reproduction path.

## PoolAct Quick Start

These are the only commands most PoolAct readers need.

### 1. Install once

Python 3.9 or newer is required. The setup script creates `.venv` and installs
both the core and Search/audit dependencies. The eval scripts find this venv
automatically; there is no activation step.

```bash
git clone https://github.com/tiannuo-yang/LLM_ExpGym.git
cd LLM_ExpGym
bash scripts/setup.sh
```

### 2. Run the free check

This makes no API calls and needs no dataset:

```bash
bash scripts/eval_poolact.sh --backend fake
```

Success prints `POOLACT RESULT`; `summary.json` is written under the output
directory printed at startup.

### 3. Run PoolAct with a real model

Choose one API setup. OpenRouter can be passed inline:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_poolact.sh \
  --model openai/gpt-4.1-nano \
  --agents 4
```

For a local Sub2API deployment, source its client environment first:

```bash
set -a
source /path/to/sub2api/.sub2api-client.env
set +a

bash scripts/eval_poolact.sh \
  --backend sub2api \
  --model gpt-5.4 \
  --agents 4
```

The default runs PoolAct only on the built-in tuning task. It needs no external
dataset. To compare the three paper strategies on five Search questions, use
one command:

```bash
bash scripts/eval_poolact.sh --with-auto-data \
  --scenario restricted_search \
  --questions 0:5 \
  --agents 4 \
  --strategies naive,cached,poolact \
  --output-dir runs/poolact_search_5q
```

`0:5` means questions 0 through 4. The first run downloads only PhantomWiki;
later runs reuse it. A rerun resumes completed items automatically. The batch
summary is `runs/poolact_search_5q/summary.json`, with per-item traces under
`runs/poolact_search_5q/item_0/`, `item_1/`, and so on.

```bash
python -m json.tool runs/poolact_search_5q/summary.json
```

To run all 35 paper Search questions, change only the range:

```bash
bash scripts/eval_poolact.sh --with-auto-data \
  --scenario restricted_search \
  --questions 0:35 \
  --agents 4 \
  --strategies naive,cached,poolact \
  --output-dir runs/poolact_search_35q
```

Preview any command without model calls:

```bash
bash scripts/eval_poolact.sh \
  --scenario restricted_search \
  --questions 0:35 \
  --strategies naive,cached,poolact \
  --dry-run
```

## Single-Agent ExpGym Quick Start

Run one real end-to-end trace with no external dataset:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_model.sh
```

The default is deliberately small:

```text
model=openai/gpt-4.1-nano
scenario=tuning
task=neural_network_training
budget=cost_tight
```

Success ends with one line like this:

```text
EVALUATION RESULT | scenario=tuning | item=neural_network_training | model=openai/gpt-4.1-nano | cost_regime=cost_tight | answer_perf=... | score_check=ok | ... | trace=...
```

Summarize traces:

```bash
python scripts/summarize_traces.py runs/openai_gpt-4.1-nano
```

## Configure Once

Both runners read `.env`.

Either pass the key inline:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_model.sh
```

or create `.env`:

```bash
cp .env.example .env
# edit OPENROUTER_API_KEY or OPENROUTER_API_KEY_FILE
bash scripts/eval_model.sh
```

For a local or OpenAI-compatible server:

```bash
OPENROUTER_API_KEY=dummy bash scripts/eval_model.sh \
  --base-url http://localhost:8000/v1 \
  --model my-local-model
```

`--base-url` accepts either `http://localhost:8000/v1` or a full
`/chat/completions` endpoint.

### Local Sub2API

The repository has a native `sub2api` backend. Load the existing local client
configuration, then give the sweep a cache-key namespace:

```bash
set -a
source /path/to/sub2api/.sub2api-client.env
set +a

bash scripts/eval_model.sh \
  --backend sub2api \
  --prompt-cache-key expgym-tuning-v1
```

`SUB2API_BASE_URL`, `SUB2API_API_KEY`, and `SUB2API_MODEL` are read directly
from that environment file. By default, the supplied value is a namespace: the
sweep deterministically derives a separate key for each logical job from its
model, scenario, cost regime, item, repetition, seed, and loop settings. The
derived key is at most 64 characters and is reused unchanged for every turn and
retry in that job. Different jobs therefore cannot accidentally share a cache
routing bucket. Trace v2 stores the effective key, namespace, scope, and
derivation version alongside per-call cache usage. For the `sub2api` backend,
omitting `--prompt-cache-key` automatically uses the namespace `expgym` so a
paper sweep cannot silently lose per-job key isolation.

Use `--prompt-cache-scope literal` only when an exact key is needed for a
targeted compatibility test, or `--prompt-cache-scope disabled` to omit the
field explicitly. A stable key helps routing but a cache hit still requires an
identical, sufficiently long prompt prefix.

### Trace format

New runs default to the normalized, versioned `expgym.trace` v2 format and are
written under `traces-v2/`. Each message body is stored once; LLM and tool calls
reference message IDs. Per-call usage, cache reporting, retry count, termination
reason, effective model settings, dataset revision, and source provenance are
preserved. The contract is documented in
`schemas/trace-v2.schema.json` and every artifact is validated before an atomic
write.

Use `--trace-format v1` only for legacy consumers. Existing v1 files remain
readable by `scripts/summarize_traces.py`; v1 and v2 paths do not collide.

## Runner 1: Eval Model

Use `scripts/eval_model.sh` for the built-in smoke, restricted search, and
evidence audit. There is no required manual dataset step. When a scenario needs
data, add `--with-auto-data`; the runner downloads what is missing.

```bash
bash scripts/eval_model.sh \
  --model <model-or-comma-list> \
  --scenario <tuning|restricted_search|evidence_audit> \
  --budget <cost_tight|cost_moderate|cost_free> \
  [--task <tuning-task> | --questions <index-or-range>] \
  --output-dir runs/<name>
```

Common flags:

| Flag | Meaning | Examples |
|---|---|---|
| `--backend` | API backend | `openrouter`, `openai`, `sub2api` |
| `--model` | Model ID or comma-separated model IDs | `openai/gpt-4.1-nano`, `mistralai/mistral-large` |
| `--base-url` | OpenAI-compatible server | `http://localhost:8000/v1` |
| `--prompt-cache-key` | Namespace used to derive one stable key per job | `expgym-paper-v1` |
| `--prompt-cache-scope` | `job` (derived), `literal` (exact), or `disabled` | `job` |
| `--trace-format` | Trace artifact format | `v2` (default), `v1` (legacy) |
| `--scenario` | Task family | `tuning`, `restricted_search`, `evidence_audit` |
| `--task` | Tuning task name | `neural_network_training` |
| `--questions` | Search/audit item selector | `0`, `0:10`, `0,2,7` |
| `--budget` | Cost regime | `cost_tight`, `cost_moderate`, `cost_free` |
| `--with-auto-data` | Download missing datasets before running | search/audit |
| `--dry-run` | Print planned jobs only | no model calls, no traces |

Examples:

```bash
# Search slice.
bash scripts/eval_model.sh --with-auto-data \
  --model openai/gpt-4.1-nano \
  --scenario restricted_search \
  --questions 0:5 \
  --budget cost_tight

# Evidence-audit slice. ContractNLI downloads automatically.
bash scripts/eval_model.sh --with-auto-data \
  --model openai/gpt-4.1-nano \
  --scenario evidence_audit \
  --questions 0:3 \
  --budget cost_tight

# Compare two models on the same slice.
bash scripts/eval_model.sh --with-auto-data \
  --model openai/gpt-4.1-nano,mistralai/mistral-large \
  --scenario restricted_search \
  --questions 0:5 \
  --budget cost_tight \
  --output-dir runs/search_compare

# Preview before spending API calls.
bash scripts/eval_model.sh --with-auto-data \
  --scenario restricted_search \
  --questions 0:35 \
  --budget cost_free,cost_moderate,cost_tight \
  --dry-run
```

## Runner 2: PoolAct

PoolAct runs several agents on the same item. They share completed tool
observations and a compact exploration graph, while LLM decisions are
serialized so each agent sees earlier agents' completed work and current
`In Progress` claims. Tool calls execute in parallel.

The [PoolAct Quick Start](#poolact-quick-start) above is the recommended entry
point. The cheapest functional smoke needs no key or data:

```bash
bash scripts/eval_poolact.sh --backend fake --agents 2
```

Run a real four-agent PoolAct smoke with the same `.env` conventions as
`eval_model.sh`:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_poolact.sh --agents 4
```

Compare all three strategies on the same item:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_poolact.sh \
  --agents 4 \
  --strategies naive,cached,poolact \
  --output-dir runs/poolact_comparison
```

For one Search question, add `--with-auto-data` on the first run:

```bash
bash scripts/eval_poolact.sh --with-auto-data \
  --scenario restricted_search \
  --question-index 0 \
  --agents 4
```

For several Search questions or audit documents, `--questions` accepts the
same syntax as `eval_model.sh`:

```bash
# One item, a comma list, or a half-open range.
--questions 0
--questions 0,2,7
--questions 0:5
```

Common flags:

| Flag | Meaning | Default |
|---|---|---|
| `--backend` | `openrouter`, `openai`, `sub2api`, `vllm`, or `fake` | auto-detected |
| `--model` | Model ID exposed by the selected backend | `openai/gpt-4.1-nano` |
| `--scenario` | `tuning`, `restricted_search`, or `evidence_audit` | `tuning` |
| `--question-index` | Run one Search/audit item | `0` |
| `--questions` | Run an item list/range | unset |
| `--agents` | Parallel agent count | `2` |
| `--strategies` | Any ordered subset of `naive,cached,poolact` | `poolact` |
| `--budget` | `cost_tight`, `cost_moderate`, or `cost_free` | `cost_tight` |
| `--with-auto-data` | Fetch only the dataset needed by the scenario | off |
| `--output-dir` | Result directory | generated from model/scenario/item |
| `--dry-run` | Resolve and print the run without calling a model | off |

The aggregation method follows the paper:

| Scenario | Aggregation |
|---|---|
| `tuning` | best-of-N |
| `restricted_search` | majority vote over normalized answer sets |
| `evidence_audit` | per-hypothesis label and evidence vote |

For a single item, each strategy writes `result.json`, one JSON trace per agent
under `agents/`, and a top-level `summary.json`. A `--questions` batch creates
one `item_N/` directory per item and a top-level `summary.json` containing each
answer plus mean `answer_perf` for every strategy. Results include SHA-256
hashes for the runner, public API, shared-state implementation, and ReAct loop
so a run can be tied to the exact PoolAct source snapshot.

### PoolAct troubleshooting

| Message or symptom | Fix |
|---|---|
| `No API key configured` | Use `--backend fake`, set a key in `.env`, or source the Sub2API client env. |
| `No module named pyarrow` | Run `bash scripts/setup.sh` and retry. |
| PhantomWiki is missing | Add `--with-auto-data` once. |
| A rerun prints `[resume]` | The exact result already exists; choose another `--output-dir` to rerun it. |
| PoolAct has higher wall time | Expected: reasoning calls are serialized; expensive tool calls remain parallel. |

The library entry point is `expgym.poolact.PoolActCoordinator`. The canonical
`wrap_tools_with_poolact` API is the paper implementation: shared cache,
`SharedExplorationGraph`, pending claims, and serialized reasoning. The old
misspelled `wrap_tools_with_polact` name remains only as a compatibility alias.
See [`docs/poolact.md`](docs/poolact.md) for the paper-to-code mapping and
library example.

For HPOBench/NASBench PoolAct, use the same Docker image with `--poolact`:

```bash
bash scripts/run_hpobench_docker.sh --poolact \
  --backend openrouter \
  --model openai/gpt-4.1-nano \
  --scenario tuning \
  --tuning-task hpobench:paramnet:adult:steps \
  --agents 4 \
  --strategies naive,cached,poolact \
  --output-dir runs/hpobench_poolact
```

Full NASBench201 PoolAct runs still need at least 16GB Docker memory; 24GB is
safer. PoolAct does not single-flight an action another agent is currently
executing: the graph exposes it as `In Progress`, and the model decides whether
to avoid it. This matches the paper's “no hard blocking” design.

## Runner 3: Docker HPOBench

Use `scripts/run_hpobench_docker.sh` for HPOBench / NASBench. This is separate
because those tasks need the old TensorFlow 1.15 stack. Docker keeps the command
the same across Linux, macOS, and Windows with WSL2.

```bash
bash scripts/run_hpobench_docker.sh --resume \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks hpobench:paramnet:adult:steps \
  --cost-regimes cost_tight \
  --output-dir runs/hpobench_smoke
```

Full NASBench201 runs need at least 16GB Docker memory; 24GB is safer.

## Outputs

Each successful job prints the primary score and trace path:

```text
EVALUATION RESULT | ... | answer_perf=... | score_check=ok | trace=...
```

By default traces are under:

```text
runs/<model>/<scenario>_<budget>/<model>_<budget>/traces/*.json
```

Primary scores:

| Scenario | `answer_perf` means |
|---|---|
| `tuning` | final configuration performance |
| `restricted_search` | name-level F1 |
| `evidence_audit` | label accuracy (`answer_metrics.label_acc`) |

Evidence audit also writes:

| Metric | Meaning |
|---|---|
| `answer_metrics.label_acc` | fraction of hypotheses with the correct NLI label |
| `answer_metrics.evidence_acc` | fraction of hypotheses with exact-match evidence IDs |
| `answer_metrics.verification_eff` | among fully-correct hypotheses, fraction verified via `human_feedback` |

`score_check=ok` means ExpGym recomputed the score from the saved answer/trace.

<details>
<summary>Advanced: Data Utility</summary>

`scripts/download_data.py` is the implementation behind `--with-auto-data`.
Most users do not need to call it directly.

Use it manually only when you want to prefetch data without starting a model
run, verify a cache in CI, print data source URLs, or use an offline ContractNLI
zip:

```bash
python scripts/download_data.py
python scripts/download_data.py --check
python scripts/download_data.py --print-data-links
```

ContractNLI is downloaded from the official GitHub-hosted zip:

```bash
https://github.com/stanfordnlp/contract-nli/blob/gh-pages/resources/contract-nli.zip
```

Offline override:

```bash
CONTRACT_NLI_ARCHIVE=/absolute/path/to/contract-nli.zip
```

</details>

<details>
<summary>Advanced: More HPOBench Options</summary>

All paper HPOBench tasks in Docker:

```bash
bash scripts/run_hpobench_docker.sh --resume \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks all-hpobench \
  --cost-regimes cost_tight \
  --tuning-reps 1 \
  --max-steps 30 \
  --max-evals 999999 \
  --output-dir runs/hpobench_all
```

On native Linux x86_64, Docker is optional. You can use conda instead:

```bash
python scripts/download_data.py
bash scripts/recreate_expgym_env.sh
conda run -n expgym-hpobench python scripts/run_paper_sweep.py --resume \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks hpobench:paramnet:adult:steps \
  --cost-regimes cost_tight \
  --output-dir runs/hpobench_native
```

</details>

<details>
<summary>Disk Space</summary>

| Run target | Practical free space |
|---|---:|
| Default smoke | 0.5GB |
| Search + audit data | 1GB |
| ParamNet-only HPOBench | 5-8GB |
| Full HPOBench / NASBench | 20-30GB |

</details>

<details>
<summary>Paper Reproduction</summary>

The paper matrix is 1,818 traces:

- 6 models
- 3 cost regimes
- 9 HPOBench tasks x 3 reps
- 35 Phantom Wiki questions
- 13 ContractNLI docs x 3 hypothesis orders

Native search + audit:

```bash
bash scripts/run_paper_sweep.sh --with-auto-data --resume \
  --models dsv32,gpt52,gpt41,gemini3flash,haiku45,mistral_large \
  --scenarios restricted_search,evidence_audit \
  --cost-regimes cost_free,cost_moderate,cost_tight \
  --search-data-source phantom_seed1 \
  --search-indices 0:35 \
  --cc-split cc-large \
  --audit-indices 0:13 \
  --search-reps 1 \
  --audit-reps 3 \
  --max-steps 30 \
  --max-evals 999999 \
  --output-dir budget_sweep_results/paper
```

HPOBench / NASBench:

```bash
bash scripts/run_hpobench_docker.sh --resume \
  --models dsv32,gpt52,gpt41,gemini3flash,haiku45,mistral_large \
  --scenarios tuning \
  --cost-regimes cost_free,cost_moderate,cost_tight \
  --tuning-tasks all-hpobench \
  --tuning-reps 3 \
  --max-steps 30 \
  --max-evals 999999 \
  --output-dir budget_sweep_results/paper
```

Dry-run the full matrix:

```bash
bash scripts/run_paper_sweep.sh --dry-run \
  --models dsv32,gpt52,gpt41,gemini3flash,haiku45,mistral_large \
  --scenarios tuning,restricted_search,evidence_audit \
  --cost-regimes cost_free,cost_moderate,cost_tight \
  --tuning-tasks all-hpobench \
  --search-indices 0:35 \
  --audit-indices 0:13 \
  --tuning-reps 3 \
  --search-reps 1 \
  --audit-reps 3 \
  --max-steps 30 \
  --max-evals 999999
```

Expected dry-run count: `1818` jobs.

</details>

<details>
<summary>Developer Checks</summary>

```bash
python -m unittest discover tests
python scripts/download_data.py --check
python scripts/run_paper_sweep.py --dry-run
```

</details>
