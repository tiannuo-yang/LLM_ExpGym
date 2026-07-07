# ExpGym: Evaluating LLM Agents in Expensive Worlds

ExpGym evaluates LLM agents in tasks where each tool call represents an
expensive real-world action: training a model, searching a restricted corpus,
or asking a human auditor for feedback. ExpGym replaces the slow operation with
deterministic cached/surrogate feedback, so real LLM agents can be tested
end-to-end without waiting hours per tool call.

The repository currently covers three scenarios:

| Scenario | What the agent does | Data/deps needed for the default run |
|---|---|---|
| `tuning` | Tune a configuration and submit the best config | none for the built-in task |
| `restricted_search` | Search Phantom Wiki and answer a multi-hop question | auto-downloadable Phantom Wiki |
| `evidence_audit` | Audit ContractNLI labels/evidence with simulated human feedback | manually downloaded ContractNLI zip |

The runner always calls a real model by default. There is no fake-LLM smoke in
the main path.

## Quickstart

Clone, configure a key, and run one real end-to-end trace:

```bash
cp .env.example .env
# edit .env if your key file, server URL, model, or data root differs
bash scripts/run_paper_sweep.sh
```

Default run:

- model: `openai/gpt-4.1-nano`
- scenario: `tuning`
- tuning task: `neural_network_training`
- cost regime: `cost_tight`
- output: `budget_sweep_results/e2e/`

The wrapper creates/reuses `.venv-expgym`, installs light Python dependencies,
loads `.env`, calls OpenRouter, runs the ReAct loop, executes the ExpGym tool,
and writes a trace whose `score_check.ok` must be `true`.

## Configuration

Most users only need these `.env` entries:

```bash
# Direct key, or a file containing one key.
# OPENROUTER_API_KEY=sk-or-...
OPENROUTER_API_KEY_FILE=../openrouter.key

# Optional OpenAI-compatible endpoint override.
# OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Optional data locations. Defaults are inside ./data.
# EXPGYM_DATA_ROOT=/absolute/path/to/expgym-data
# PHANTOM_WIKI_ROOT=/absolute/path/to/expgym-data/phantom-wiki

EXPGYM_OPENROUTER_MODEL=openai/gpt-4.1-nano
```

`scripts/run_paper_sweep.sh` accepts wrapper options first, then passes all
remaining options to `scripts/run_paper_sweep.py`.

```bash
bash scripts/run_paper_sweep.sh --help
python scripts/run_paper_sweep.py --help
```

## Run Scenarios

All expansion is explicit. Select scenarios, models, questions, tasks, budgets,
and repetitions with CLI flags.

Built-in tuning smoke, no external datasets:

```bash
bash scripts/run_paper_sweep.sh \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks neural_network_training \
  --cost-regimes cost_tight
```

Restricted search, with auto-downloadable data:

```bash
bash scripts/run_paper_sweep.sh --with-auto-data \
  --models openai/gpt-4.1-nano \
  --scenarios restricted_search \
  --search-indices 0 \
  --cost-regimes cost_tight
```

Evidence audit, after accepting Stanford ContractNLI terms and downloading the
zip:

```bash
bash scripts/run_paper_sweep.sh \
  --contract-nli-archive /path/to/contract-nli.zip \
  --models openai/gpt-4.1-nano \
  --scenarios evidence_audit \
  --audit-indices 0 \
  --cc-split cc-small \
  --cost-regimes cost_tight
```

Common selectors:

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

## Data

Prepare and verify data independently:

```bash
python scripts/download_data.py --auto-only
python scripts/download_data.py --contract-nli-archive /path/to/contract-nli.zip
python scripts/download_data.py --check
```

| Dataset | Used by | How to prepare | Expected location |
|---|---|---|---|
| HPOBench source | `tuning` HPOBench tasks | auto via `--auto-only` | `data/hpo_tuning/HPOBench/` |
| HPOBench oracle | cost scaling | shipped | `data/hpo_tuning/oracle3.json` |
| Phantom Wiki | `restricted_search` | auto via `--auto-only` | `$PHANTOM_WIKI_ROOT/...` |
| ContractNLI segments | `evidence_audit` | manual zip, scripted extraction | `$EXPGYM_DATA_ROOT/contract-nli/test_segments.json` |
| ContractNLI hints | `evidence_audit` | shipped | `data/contract-nli/test_nda_span_dims.json` |

ContractNLI is not auto-downloaded because the Stanford page requires accepting
data-use terms. After you provide the zip, the script extracts the public
`contract-nli/test.json` split and normalizes it to ExpGym's
`test_segments.json` schema.

## HPOBench Dependencies

The default smoke and built-in tuning task do not need HPOBench Python deps.
Only `hpobench:*` tuning tasks need the legacy HPOBench/NASBench stack:

```bash
bash scripts/recreate_expgym_env.sh
```

This creates `expgym-hpobench` with HPOBench editable install,
`tensorflow==1.15`, `scikit-learn==0.23.2`, ConfigSpace, NASBench, and
NASBenchmarks. TensorFlow 1.15 does not have native macOS arm64 wheels, so the
script fails fast on Apple Silicon unless `EXPGYM_FORCE_HPOBENCH_INSTALL=1` is
set. For the full HPOBench/NASBench101 matrix, use Linux/x86_64.

Disk budget:

| Run target | Practical free space |
|---|---:|
| Default `tuning` smoke | `0.5 GB` |
| `restricted_search` + `evidence_audit` data | `1 GB` |
| ParamNet-only HPOBench tasks | `5-8 GB` |
| Full paper HPOBench/NASBench tuning matrix | `20-30 GB` |

The HPOBench source clone is small, but the benchmark data is not. HPOBench
downloads data lazily into its configured data directory, usually
`~/.local/share/hpobench`. The main large files are:

| Component | Compressed/download size | Notes |
|---|---:|---|
| NASBench101 `nasbench_full.tfrecord` | `2.1 GB` | kept on disk |
| NASBench201 `nasbench_201_data_v1.3.zip` | `1.5 GB` | read into memory, then extracted |
| ParamNet/SVM `surrogates.tar.gz` | `0.5 GB` | kept and extracted |

Leave extra headroom for extracted files, conda packages, pip caches, and trace
outputs. If disk is tight, run only `neural_network_training`,
`restricted_search`, or `evidence_audit`, or select one HPOBench family instead
of `--tuning-tasks all-hpobench`.

Run HPOBench tasks from that env:

```bash
conda run -n expgym-hpobench python scripts/run_paper_sweep.py \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks hpobench:paramnet:adult:steps \
  --cost-regimes cost_tight
```

## Paper Reproduction

The paper matrix is built from explicit selectors, not from a hidden preset:

- 6 model aliases: `dsv32,gpt52,gpt41,gemini3flash,haiku45,mistral_large`
- 3 cost regimes: `cost_free,cost_moderate,cost_tight`
- 9 HPOBench tuning tasks x 3 reps: `--tuning-tasks all-hpobench --tuning-reps 3`
- 35 Phantom Wiki questions: `--search-indices 0:35`
- 13 ContractNLI documents x 3 hypothesis orders: `--audit-indices 0:13 --audit-reps 3`

Dry-run the exact 1,818-trace matrix:

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
  --max-evals 999999 \
  --output-dir budget_sweep_results/paper
```

Run it with resumable writes:

```bash
bash scripts/run_paper_sweep.sh --resume \
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
  --max-evals 999999 \
  --output-dir budget_sweep_results/paper
```

If a model alias no longer maps to an available OpenRouter model, override it:

```bash
bash scripts/run_paper_sweep.sh \
  --model-alias gpt52=openai/gpt-5.2 \
  --models gpt52 \
  --scenarios tuning
```

## Outputs And Scoring

Each trace is a JSON file under:

```text
<output-dir>/<model_alias>_<cost_regime>/traces/*.json
```

Important fields:

| Field | Meaning |
|---|---|
| `job` | scenario, model, question/task index, seed, repetition |
| `cost_regime_resolved` | resolved budget mode, `c_base`, and time budget |
| `steps` | prompts, actions, observations, and final answer text |
| `tool_records` | tool calls used for score recomputation |
| `answer_perf` | primary scalar score |
| `answer_metrics` | structured metrics when the scenario has more than one |
| `score_check` | recomputed score; runs fail if `ok` is false |

Scenario scores:

| Scenario | Primary score |
|---|---|
| `tuning` | performance of the final submitted configuration |
| `restricted_search` | name-level F1 against Phantom Wiki gold answers |
| `evidence_audit` | label accuracy, plus evidence accuracy and verification efficiency |

Cost regimes:

| Regime | Budget | Cost visibility |
|---|---|---|
| `cost_free` | no ceiling | hidden |
| `cost_moderate` | `10 * c_base` | shown |
| `cost_tight` | `3 * c_base` | shown |

## Sanity Checks

```bash
python -m unittest discover tests
python scripts/run_paper_sweep.py --dry-run
python scripts/download_data.py --check
```

The default dry-run should report one job. The explicit paper command above
should report 1,818 jobs: 486 tuning, 630 restricted search, and 702 evidence
audit.

## PoolAct

The repo also includes PoolAct (`expgym.poolact`) for parallel agents sharing
expensive observations through a shared cache, ledger, and graph. Use
`wrap_tools_with_poolact` for the main PoolAct behavior; `wrap_tools_with_cache`
and `wrap_tools_with_polact` are ablations.

```python
from expgym.poolact import (
    SharedObservationCache,
    SharedExplorationLedger,
    make_ledger_augmenter,
    wrap_tools_with_poolact,
)
from expgym.react_loop import run_react_loop
from expgym.task_restricted_search import SCENARIO as SEARCH

cache = SharedObservationCache()
ledger = SharedExplorationLedger()
augmenter = make_ledger_augmenter(ledger)

def run_one(agent_id, llm):
    tools = wrap_tools_with_poolact(
        SEARCH["tools"](data_source="phantom_seed1"),
        cache=cache,
        ledger=ledger,
        agent_id=agent_id,
    )
    return run_react_loop(
        llm=llm,
        tools=tools,
        time_budget=900,
        observation_augmenter=augmenter,
    )
```

## Extending

A scenario is a Python module exporting a `SCENARIO` dict. The core ReAct loop
has no scenario-specific code.

```python
SCENARIO = {
    "name": "my_world",
    "tools": {"my_tool": my_tool},   # or build_tools(): callable
    "build_context": ...,            # (include_overhead, **kw) -> str
    "build_instruction_notes": ...,  # (include_overhead) -> List[str]
    "build_fake_plan": ...,          # (probes, **kw) -> [(tool, payload)]
}
```

Register the module in `demo_experiment.py` (`_SCENARIOS`) and add a branch in
`resolve_base_cost()` if the cost-regime machinery should derive a budget for
it.
