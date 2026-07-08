# ExpGym

ExpGym runs LLM agents in the three expensive-world tasks from the paper:

| Scenario | Paper task |
|---|---|
| `tuning` | 9 HPOBench / NASBench tuning tasks |
| `restricted_search` | 35 Phantom Wiki multi-hop questions |
| `evidence_audit` | 13 ContractNLI audit documents |

For the smoke run, you only need an OpenRouter API key.

## Smoke: Three Lines

Run one end-to-end evaluation with no external datasets:

```bash
git clone https://github.com/tiannuo-yang/LLM_ExpGym.git
cd LLM_ExpGym
OPENROUTER_API_KEY=sk-or-... bash scripts/run_paper_sweep.sh
```

Successful output ends with a score line:

```text
EVALUATION RESULT | scenario=tuning | item=neural_network_training | model=openai/gpt-4.1-nano | cost_regime=cost_tight | answer_perf=... | score_check=ok | ... | trace=...
```

The smoke creates `.venv-expgym`, installs light dependencies, runs an
OpenRouter ReAct trace, writes a JSON trace, and prints the primary score.

For persistent config:

```bash
cp .env.example .env
# edit OPENROUTER_API_KEY or OPENROUTER_API_KEY_FILE
bash scripts/run_paper_sweep.sh
```

## Full Paper Reproduction

Full reproduction is 1,818 model traces:

- 6 models
- 3 cost regimes
- 9 HPOBench tasks x 3 reps
- 35 Phantom Wiki questions
- 13 ContractNLI docs x 3 hypothesis orders

First prepare data:

```bash
# Auto-downloadable data: Phantom Wiki + HPOBench source.
bash scripts/run_paper_sweep.sh --with-auto-data --dry-run

# ContractNLI is manual: print official link/instructions.
python scripts/download_data.py --print-manual-links
```

Download ContractNLI from the official page, then put this in `.env`:

```bash
CONTRACT_NLI_ARCHIVE=/absolute/path/to/contract-nli.zip
```

For HPOBench on macOS Apple Silicon, install/start Docker Desktop and set
Docker memory to at least 16GB, 24GB recommended.

Then run the full paper matrix in two parts.

Native tasks:

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

HPOBench / NASBench tuning:

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

<details>
<summary>Linux x86_64 native HPOBench instead of Docker</summary>

```bash
bash scripts/recreate_expgym_env.sh
conda run -n expgym-hpobench python scripts/run_paper_sweep.py --resume \
  --models dsv32,gpt52,gpt41,gemini3flash,haiku45,mistral_large \
  --scenarios tuning \
  --cost-regimes cost_free,cost_moderate,cost_tight \
  --tuning-tasks all-hpobench \
  --tuning-reps 3 \
  --max-steps 30 \
  --max-evals 999999 \
  --output-dir budget_sweep_results/paper
```

</details>

`--dry-run` means: print the jobs that would run, without calling models or
writing result traces.

<details>
<summary>Dry-run the exact full matrix</summary>

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
<summary>If a paper model alias is unavailable</summary>

Override it:

```bash
bash scripts/run_paper_sweep.sh \
  --model-alias gpt52=openai/gpt-5.2 \
  --models gpt52 \
  --scenarios tuning
```

</details>

<details>
<summary>macOS Docker details</summary>

Docker is only needed for HPOBench / NASBench on macOS Apple Silicon. The
runner builds a Linux x86_64 image with TensorFlow 1.15 and HPOBench installed.
Full NASBench201 runs need Docker Desktop memory at least 16GB; 24GB is safer.

</details>

<details>
<summary>Validated short paper check</summary>

This is not the full paper table. It is the smallest check that touches every
paper task family once with one OpenRouter model under `cost_tight`.

Native tasks:

```bash
bash scripts/run_paper_sweep.sh --with-auto-data --resume \
  --models openai/gpt-4.1-nano \
  --scenarios restricted_search,evidence_audit \
  --cost-regimes cost_tight \
  --search-data-source phantom_seed1 \
  --search-indices 0:35 \
  --cc-split cc-large \
  --audit-indices 0:13 \
  --max-steps 30 \
  --output-dir budget_sweep_results/task_e2e_tight_native
```

HPOBench tasks:

```bash
bash scripts/run_hpobench_docker.sh --resume \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks all-hpobench \
  --cost-regimes cost_tight \
  --tuning-reps 1 \
  --max-steps 30 \
  --output-dir budget_sweep_results/task_e2e_tight_hpobench
```

We have run this check successfully: 57/57 traces, no missing scores,
`score_check=ok`.

</details>

## Data And Space

| Item | Preparation | Notes |
|---|---|---|
| Smoke | none | no external datasets |
| Phantom Wiki | auto via `--with-auto-data` | paper subset is `phantom_seed1`, indices `0:35` |
| ContractNLI | manual official zip | ExpGym does not mirror or auto-download it |
| HPOBench | auto source + Docker/native deps | full NASBench needs Docker memory >=16GB on macOS |

Disk:

| Run target | Practical free space |
|---|---:|
| Smoke | 0.5GB |
| Search + audit data | 1GB |
| ParamNet-only HPOBench | 5-8GB |
| Full HPOBench / NASBench | 20-30GB |

## Outputs

Traces are written under:

```text
<output-dir>/<model_alias>_<cost_regime>/traces/*.json
```

Each successful job prints:

```text
EVALUATION RESULT | ... | answer_perf=... | score_check=ok | trace=...
```

Primary scores:

| Scenario | `answer_perf` |
|---|---|
| `tuning` | final configuration performance |
| `restricted_search` | name-level F1 |
| `evidence_audit` | label accuracy |

`score_check=ok` means the saved answer was recomputed from the trace.

<details>
<summary>Common options</summary>

```bash
bash scripts/run_paper_sweep.sh --models openai/gpt-4.1-nano,mistralai/mistral-large
bash scripts/run_paper_sweep.sh --model-alias fast=openai/gpt-4.1-nano --models fast
bash scripts/run_paper_sweep.sh --scenarios tuning,restricted_search
bash scripts/run_paper_sweep.sh --cost-regimes cost_free,cost_moderate,cost_tight
bash scripts/run_paper_sweep.sh --search-indices 0:10
bash scripts/run_paper_sweep.sh --audit-indices 0,1,2 --audit-reps 3
bash scripts/run_paper_sweep.sh --tuning-tasks hpobench:paramnet:adult:steps
bash scripts/run_paper_sweep.sh --resume --output-dir budget_sweep_results/my_run
```

</details>

<details>
<summary>Developer checks</summary>

```bash
python -m unittest discover tests
python scripts/download_data.py --check
python scripts/run_paper_sweep.py --dry-run
```

</details>
