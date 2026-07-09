# ExpGym

ExpGym evaluates a model in expensive-world tasks and writes score-checked
ReAct traces. Use it when you want to see how a model spends tool calls, handles
budget pressure, and what score it gets at the end.

Most users only need one runner:

```bash
bash scripts/eval_model.sh [flags]
```

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

## Data Before You Run

Data setup is scenario-specific. Check this table before launching anything
beyond the default smoke:

| Run target | What to prepare first | Runner flag |
|---|---|---|
| Default smoke / built-in `tuning` | Nothing. It runs immediately. | none |
| `restricted_search` | Nothing manual. Add `--with-auto-data` on the first run; it downloads Phantom Wiki data under `data/`. | `--with-auto-data` |
| `evidence_audit` | Download the official ContractNLI zip yourself, then pass the local path. | `--contract-nli-archive /path/to/contract-nli.zip` |
| HPOBench / NASBench tuning | Docker is recommended for the old TensorFlow 1.15 stack. Native Linux x86_64 can also use the conda setup below; macOS/Windows should use Docker. | use `scripts/run_hpobench_docker.sh` or native Linux conda |

Useful data commands:

```bash
# Optional: prefetch all auto-downloadable data instead of using --with-auto-data.
python scripts/download_data.py --auto-only

# ContractNLI is manual; print the official link/instructions.
python scripts/download_data.py --print-manual-links
```

You do not need data for `--dry-run`; it only prints planned jobs.

## The One Command

Use the same command shape for smoke, slices, sweeps, and model comparisons:

```bash
bash scripts/eval_model.sh \
  --model <model-or-comma-list> \
  --scenario <tuning|restricted_search|evidence_audit> \
  --budget <cost_tight|cost_moderate|cost_free> \
  [--task <tuning-task> | --questions <index-or-range>] \
  --output-dir runs/<name>
```

Only a few flags change between runs:

| Flag | Meaning | Examples |
|---|---|---|
| `--model` | Model ID or comma-separated model IDs | `openai/gpt-4.1-nano`, `mistralai/mistral-large` |
| `--base-url` | OpenAI-compatible server | `http://localhost:8000/v1` |
| `--scenario` | Expensive-world task family | `tuning`, `restricted_search`, `evidence_audit` |
| `--task` | Tuning task name | `neural_network_training` |
| `--questions` | Search/audit item selector | `0`, `0:10`, `0,2,7` |
| `--budget` | Cost regime | `cost_tight`, `cost_moderate`, `cost_free` |
| `--reps` | Repeat each selected item | `3` |
| `--max-steps` | ReAct step limit | `30` |
| `--max-evals` | Tool-call limit | `999999` |
| `--dry-run` | Print planned jobs only | no model calls, no traces |

## Common Runs

| What you want | Data first | Flags to add |
|---|---|---|
| Fast smoke | none | none |
| Different OpenRouter model | none if using default `tuning` | `--model mistralai/mistral-large` |
| Local/server model | none if using default `tuning` | `--base-url http://localhost:8000/v1 --model my-local-model` |
| Search slice | auto via runner | `--scenario restricted_search --questions 0:5 --with-auto-data` |
| Evidence-audit slice | ContractNLI zip | `--scenario evidence_audit --questions 0:3 --contract-nli-archive /path/to/contract-nli.zip` |
| More budget regimes | same as selected scenario | `--budget cost_free,cost_moderate,cost_tight` |
| More items | same as selected scenario | `--questions 0:35 --max-steps 30 --max-evals 999999` |
| Preview a run | none | `--dry-run` |

Examples:

```bash
# One OpenRouter model on five restricted-search questions.
bash scripts/eval_model.sh --with-auto-data \
  --model openai/gpt-4.1-nano \
  --scenario restricted_search \
  --questions 0:5 \
  --budget cost_tight

# Compare two models on the same slice.
bash scripts/eval_model.sh --with-auto-data \
  --model openai/gpt-4.1-nano,mistralai/mistral-large \
  --scenario restricted_search \
  --questions 0:5 \
  --budget cost_tight \
  --output-dir runs/search_compare

# Preview the full restricted-search slice before spending API calls.
bash scripts/eval_model.sh --with-auto-data \
  --scenario restricted_search \
  --questions 0:35 \
  --budget cost_free,cost_moderate,cost_tight \
  --dry-run
```

## Scenarios

| Scenario | What it tests | Main selector | Data |
|---|---|---|---|
| `tuning` | choosing configurations under evaluation cost | `--task` | default task needs none |
| `restricted_search` | retrieving/combining evidence under search cost | `--questions` | auto via `--with-auto-data` |
| `evidence_audit` | auditing claims against contracts | `--questions` | official ContractNLI zip |

The default `tuning` task is intentionally tiny. HPOBench/NASBench tuning uses
an old TensorFlow 1.15 stack, so Docker is the recommended path. Native Linux
x86_64 can also run it without Docker using the conda setup below.

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

Evidence audit also writes additional metrics:

| Metric | Meaning |
|---|---|
| `answer_metrics.label_acc` | fraction of hypotheses with the correct NLI label |
| `answer_metrics.evidence_acc` | fraction of hypotheses with exact-match evidence IDs |
| `answer_metrics.verification_eff` | among fully-correct hypotheses, fraction verified via `human_feedback` |

`score_check=ok` means ExpGym recomputed the score from the saved answer/trace.

<details>
<summary>Data Notes</summary>

Auto-downloadable data can be prepared explicitly:

```bash
python scripts/download_data.py --auto-only
```

ContractNLI is manual. ExpGym does not mirror or auto-download the archive.

```bash
python scripts/download_data.py --print-manual-links
python scripts/download_data.py --contract-nli-archive /path/to/contract-nli.zip
```

You can also put this in `.env`:

```bash
CONTRACT_NLI_ARCHIVE=/absolute/path/to/contract-nli.zip
```

The runner also accepts the path directly:

```bash
bash scripts/eval_model.sh \
  --scenario evidence_audit \
  --questions 0:3 \
  --contract-nli-archive /path/to/contract-nli.zip
```

</details>

<details>
<summary>HPOBench / NASBench</summary>

Docker is the recommended cross-platform path because it pins the old
TensorFlow 1.15 stack. Use Docker Engine on Linux, Docker Desktop on macOS, or
Docker Desktop with WSL2 on Windows. Run the same command from a bash shell; on
Windows, use the WSL2 shell inside the cloned repo.

```bash
bash scripts/run_hpobench_docker.sh --resume \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks hpobench:paramnet:adult:steps \
  --cost-regimes cost_tight \
  --output-dir runs/hpobench_smoke
```

All paper HPOBench tasks:

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

Full NASBench201 runs need at least 16GB Docker memory; 24GB is safer.

On native Linux x86_64, Docker is optional. You can use conda instead:

```bash
python scripts/download_data.py --auto-only
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
