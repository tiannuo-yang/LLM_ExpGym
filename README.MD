# ExpGym

ExpGym evaluates a model in expensive-world tasks. The model runs a ReAct loop,
decides when to call costly tools, and ExpGym saves a score-checked JSON trace.

## Run One Trace

```bash
git clone https://github.com/tiannuo-yang/LLM_ExpGym.git
cd LLM_ExpGym
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_model.sh
```

The default run uses `openai/gpt-4.1-nano`, `tuning`,
`neural_network_training`, and `cost_tight`. It needs no external dataset.

Success looks like:

```text
EVALUATION RESULT | scenario=tuning | item=neural_network_training | model=openai/gpt-4.1-nano | cost_regime=cost_tight | answer_perf=... | score_check=ok | ... | trace=...
```

Summarize traces:

```bash
python scripts/summarize_traces.py runs/openai_gpt-4.1-nano
```

## Evaluate Your Model

OpenRouter model:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_model.sh \
  --model mistralai/mistral-large
```

OpenAI-compatible local/server model:

```bash
OPENROUTER_API_KEY=dummy bash scripts/eval_model.sh \
  --base-url http://localhost:8000/v1 \
  --model my-local-model
```

Persistent config:

```bash
cp .env.example .env
# edit OPENROUTER_API_KEY or OPENROUTER_API_KEY_FILE, and optional EXPGYM_BASE_URL
bash scripts/eval_model.sh --model openai/gpt-4.1-nano
```

`--base-url` accepts either a base URL such as `http://localhost:8000/v1` or a
full `/chat/completions` endpoint.

## Choose A Scenario

| Goal | Command | Data |
|---|---|---|
| Fast zero-data smoke | `bash scripts/eval_model.sh --model <model>` | none |
| Restricted search | `bash scripts/eval_model.sh --model <model> --scenario restricted_search --questions 0:5 --with-auto-data` | auto |
| Evidence audit | `bash scripts/eval_model.sh --model <model> --scenario evidence_audit --questions 0:3 --contract-nli-archive /path/to/contract-nli.zip` | official ContractNLI zip |
| HPOBench tuning | `bash scripts/run_hpobench_docker.sh --models <model> --tuning-tasks hpobench:paramnet:adult:steps` | Docker |

Useful selectors:

```bash
--scenario tuning | restricted_search | evidence_audit
--model openai/gpt-4.1-nano,mistralai/mistral-large
--questions 0        # one question/doc
--questions 0:10     # range [0, 10)
--questions 0,2,7    # explicit set
--budget cost_tight | cost_moderate | cost_free
--reps 3
--max-steps 30
--max-evals 999999
--output-dir runs/my_eval
```

Preview planned jobs without model calls or result traces:

```bash
bash scripts/eval_model.sh --scenario restricted_search --questions 0:35 --dry-run
```

## Outputs

The exact trace path is printed in every `EVALUATION RESULT` line. By default,
traces live under:

```text
runs/<model>/<scenario>_<budget>/<model>_<budget>/traces/*.json
```

`answer_perf` is the primary score:

| Scenario | Primary score |
|---|---|
| `tuning` | final configuration performance |
| `restricted_search` | name-level F1 |
| `evidence_audit` | label accuracy |

`score_check=ok` means ExpGym recomputed the score from the saved answer/trace.

<details>
<summary>Data Setup</summary>

The default smoke has no data dependency.

Auto-downloadable data:

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

</details>

<details>
<summary>Full Runs</summary>

Run more questions for one model:

```bash
bash scripts/eval_model.sh --with-auto-data \
  --model openai/gpt-4.1-nano \
  --scenario restricted_search \
  --questions 0:35 \
  --budget cost_tight \
  --max-steps 30 \
  --max-evals 999999 \
  --output-dir runs/search_full
```

Run all three cost regimes for one search slice:

```bash
bash scripts/eval_model.sh --with-auto-data \
  --model openai/gpt-4.1-nano \
  --scenario restricted_search \
  --questions 0:35 \
  --budget cost_free,cost_moderate,cost_tight \
  --max-steps 30 \
  --max-evals 999999 \
  --output-dir runs/search_costs
```

For multiple scenarios in one command, use the lower-level batch runner:

```bash
bash scripts/run_paper_sweep.sh --with-auto-data --resume \
  --models openai/gpt-4.1-nano,mistralai/mistral-large \
  --scenarios tuning,restricted_search \
  --cost-regimes cost_tight \
  --tuning-tasks neural_network_training \
  --search-indices 0:35 \
  --max-steps 30 \
  --max-evals 999999 \
  --output-dir runs/batch_eval
```

</details>

<details>
<summary>HPOBench On macOS</summary>

HPOBench / NASBench uses TensorFlow 1.15, so macOS Apple Silicon should use
Docker:

```bash
bash scripts/run_hpobench_docker.sh --resume \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks hpobench:paramnet:adult:steps \
  --cost-regimes cost_tight \
  --output-dir runs/hpobench_smoke
```

For all paper HPOBench tasks:

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

Full NASBench201 runs need Docker Desktop memory at least 16GB; 24GB is safer.

</details>

<details>
<summary>Space</summary>

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
