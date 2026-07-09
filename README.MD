# ExpGym

ExpGym evaluates a model in expensive-world tasks and writes score-checked
ReAct traces. Use it to see how a model spends tool calls, handles budget
pressure, and what score it gets at the end.

The user-facing interface is two scripts:

| Script | Use it for |
|---|---|
| `scripts/eval_model.sh` | Default smoke, built-in tuning, restricted search, evidence audit |
| `scripts/run_hpobench_docker.sh` | HPOBench / NASBench tuning in Docker |

Everything else is a helper or advanced reproduction path.

## Quick Start

Run one real end-to-end trace with no external dataset:

```bash
git clone https://github.com/tiannuo-yang/LLM_ExpGym.git
cd LLM_ExpGym
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
| `--model` | Model ID or comma-separated model IDs | `openai/gpt-4.1-nano`, `mistralai/mistral-large` |
| `--base-url` | OpenAI-compatible server | `http://localhost:8000/v1` |
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

## Runner 2: Docker HPOBench

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
