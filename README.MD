# ExpGym: Evaluating LLM Agents in Expensive Worlds

ExpGym is for testing LLM agents on tasks where each tool call is slow,
minutes to hours per call. There are three scenarios: hyperparameter
tuning (using HPOBench surrogates), multi-hop search (Phantom Wiki
documents), and evidence audit (simulated human review). The slow tool
calls are replaced with pre-cached results, so a full run across six
models and three cost settings finishes overnight on one machine instead
of taking weeks.

The repo also includes PoolAct (`expgym.poolact`). When several agents
work on the same problem at the same time, they often repeat each other's
expensive tool calls. PoolAct lets them share what they have already
seen, through a shared cache, ledger, and graph, so one agent's work
helps the others.

## Install

Fastest real end-to-end path after cloning:

```bash
cp .env.example .env
# edit .env if your key file, server URL, or data root differs
bash scripts/run_paper_sweep.sh
```

This creates/reuses `.venv-expgym`, installs light dependencies, reads
`OPENROUTER_API_KEY` or `OPENROUTER_API_KEY_FILE`, and runs one real
OpenRouter-backed ExpGym trace. The default is intentionally small:

- scenario: `tuning`
- model: `openai/gpt-4.1-nano`
- task: `neural_network_training`
- cost regime: `cost_tight`

It does not require external datasets. To also install data dependencies and
fetch auto-downloadable data:

```bash
bash scripts/run_paper_sweep.sh --with-auto-data
```

If you have accepted Stanford's ContractNLI terms and downloaded their zip:

```bash
bash scripts/run_paper_sweep.sh --contract-nli-archive /path/to/contract-nli.zip
```

### Smoke coverage

The default run is a fast framework smoke, not a full paper reproduction. It
verifies the core ExpGym path used by the paper:

1. A real OpenRouter model is called.
2. The model enters the ReAct loop in `expgym/react_loop.py`.
3. The model emits `Action: evaluate_config {...}` for the built-in tuning
   world in `expgym/task_tuning.py`.
4. ExpGym executes the tool, returns `Observation: perf=..., cost=...`,
   asks for a final answer, and scores it as `answer_perf`.

It does not run the full model sweep, all cost regimes, HPOBench surrogate
tasks, Phantom Wiki search, ContractNLI audit, or PoolAct parallel-agent
experiments unless you request those selectors explicitly.

```bash
conda env create -f environment.yml && conda activate expgym
# or:
pip install -r requirements.txt
```

```bash
python -m unittest discover tests
# Ran 123 tests, OK (skipped=31; external-data tests skip cleanly)
```

## Run a scenario

The sweep runner is parameterized by scenario/model/question/task/budget
selectors. The shell wrapper handles env setup; all remaining flags are passed
to `scripts/run_paper_sweep.py`.

```bash
bash scripts/run_paper_sweep.sh \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks neural_network_training \
  --cost-regimes cost_tight

bash scripts/run_paper_sweep.sh --with-auto-data \
  --models openai/gpt-4.1-nano \
  --scenarios restricted_search \
  --search-indices 0 \
  --cost-regimes cost_tight

bash scripts/run_paper_sweep.sh \
  --contract-nli-archive /path/to/contract-nli.zip \
  --models openai/gpt-4.1-nano \
  --scenarios evidence_audit \
  --audit-indices 0 \
  --cc-split cc-small \
  --cost-regimes cost_tight
```

Useful selectors:

```bash
bash scripts/run_paper_sweep.sh --models openai/gpt-4.1-nano,mistralai/mistral-large
bash scripts/run_paper_sweep.sh --scenarios tuning,restricted_search
bash scripts/run_paper_sweep.sh --cost-regimes cost_free,cost_moderate,cost_tight
bash scripts/run_paper_sweep.sh --search-indices 0:10
bash scripts/run_paper_sweep.sh --audit-indices 0,1,2 --audit-reps 3
bash scripts/run_paper_sweep.sh --tuning-tasks hpobench:paramnet:adult:steps
bash scripts/run_paper_sweep.sh --model-alias fast=openai/gpt-4.1-nano --models fast
```

## Paper Reproduction

The main paper ranking matrix is not hidden behind a preset. Build it with
explicit selectors:

- 6 OpenRouter models: DeepSeek-V3.2, GPT-5.2, GPT-4.1,
  Gemini-3-Flash, Claude-Haiku-4.5, Mistral-Large.
- 3 cost regimes: `cost_free`, `cost_moderate`, `cost_tight`.
- 9 HPOBench tuning tasks x 3 reps (`--tuning-tasks all-hpobench`).
- 35 Phantom Wiki restricted-search questions.
- 13 ContractNLI audit documents x 3 randomized hypothesis orders.

That is `486 + 630 + 702 = 1,818` traces. Dry-run the exact matrix:

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

Run the same matrix with resumable writes:

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

Every trace is saved under `--output-dir` with `job`,
`cost_regime_resolved`, and `score_check` metadata. `score_check` recomputes
the score from the scenario evaluator or tool and fails the run if the reported
score disagrees.

| Scenario | Module | EEI source | Per-call cost (surrogate wallclock) |
|---|---|---|---|
| Hyperparameter tuning | `expgym/task_tuning.py` | HPOBench surrogate eval (`--list-tuning-tasks` for the menu) | 8–50,000 s |
| Restricted search | `expgym/task_restricted_search.py` | Phantom Wiki document fetch | 300 ± 20 s |
| Evidence audit | `expgym/task_evidence_audit.py` | Simulated human verification | 300 ± 20 s |

The paper evaluates six frontier LLMs (DeepSeek-V3.2, GPT-5.2, GPT-4.1,
Gemini-3-Flash, Claude-Haiku-4.5, Mistral-Large) through OpenRouter, with
extended reasoning disabled. The code is model-agnostic: pass any model
identifier with `--backend openrouter --model <name>` and your own key.
The OpenRouter client disables extended reasoning by default
(`reasoning: {enabled: false}`); for the reasoning-enabled ablation,
construct the client with `disable_thinking=False`.

<!-- ### How the simulated human reviewer works (audit scenario)

The audit scenario does not call a second LLM for verification. Instead,
the `human_feedback` tool returns one of three deterministic responses
based on the agent's proposed evidence IDs and the ground-truth
annotations:

- **`Evidence Correct`** — the proposed evidence set exactly matches the
  ground-truth set, or both are empty for a `NotMentioned` hypothesis.
- **`Evidence Incomplete | missing: <hint>`** — the proposed set is a
  proper subset of ground truth; the hint lists semantic dimensions of
  the missing pieces (e.g. "termination clause").
- **`Contain Irrelevant Evidences`** — the proposed set contains IDs not
  in ground truth.

The full ruleset is in `expgym/task_evidence_audit.py:human_feedback`. -->

## Cost regimes

Cost is a continuous axis: `budget = β · c_base`, where `c_base` is the
per-call base cost (oracle-best evaluation cost for tuning, ~300 s for
search and audit). The paper reports three points, exposed as named
presets; `--beta` picks any other point.

| Preset | β | Cost shown | What it tests |
|---|---|---|---|
| `cost_free` | no budget | hidden | classical leaderboard |
| `cost_moderate` | 10 | shown | 10× the oracle-best cost |
| `cost_tight` | 3 | shown | ~3 affordable queries per session |

```bash
python demo_experiment.py --cost-regime cost_tight
python demo_experiment.py --cost-regime custom --beta 5 --baseline time_aware
```

The CLI prints the resolved `(preset, β, c_base, time_budget)` at run
start whenever a preset or `--beta` is set.

## PoolAct (parallel agents)

When tool calls dominate wallclock, running N agents in parallel only
helps if they share what they learn. PoolAct is that sharing layer: a
thread-safe observation cache, an exploration ledger, and an exploration
graph, all read by every agent.

Use **`wrap_tools_with_poolact`** — that is the configuration reported
as `poolact` in the paper. The other two wrappers in `expgym.poolact`
are ablations: `wrap_tools_with_cache` is cache-only (zero-cost dedup,
no ledger), and `wrap_tools_with_polact` is the v2 graph variant that
supports time-gated visibility via `AgentClock`.

```python
from expgym.poolact import (
    SharedObservationCache, SharedExplorationLedger,
    wrap_tools_with_poolact, make_ledger_augmenter,
)
from expgym.react_loop import run_react_loop
from expgym.task_restricted_search import SCENARIO as SEARCH

cache, ledger = SharedObservationCache(), SharedExplorationLedger()
augmenter = make_ledger_augmenter(ledger)

def run_one(agent_id, llm):
    tools = wrap_tools_with_poolact(
        SEARCH["tools"](data_source="phantom_seed1"),
        cache=cache, ledger=ledger, agent_id=agent_id,
    )
    return run_react_loop(
        llm=llm, tools=tools,
        time_budget=900,
        observation_augmenter=augmenter,
    )
```

Implementation: `expgym/extras/parallel_cache.py`.

## Datasets

Phantom Wiki and HPOBench source auto-download; ContractNLI requires the user
to accept Stanford's terms and provide the downloaded zip path.

```bash
python scripts/download_data.py --auto-only # fetch Phantom Wiki + HPOBench
python scripts/download_data.py --contract-nli-archive /path/to/contract-nli.zip
python scripts/download_data.py --check     # layout-only, no network
python scripts/download_data.py             # full readiness check; reports ContractNLI manual step if missing
```

| Dataset | Used by | Source | Lands at |
|---|---|---|---|
| HPOBench code | tuning | `git clone` (auto) | `data/hpo_tuning/HPOBench/` |
| HPOBench oracle | tuning, β presets | shipped | `data/hpo_tuning/oracle3.json` |
| Phantom Wiki | search | HuggingFace (auto) | `$PHANTOM_WIKI_ROOT/...` |
| ContractNLI segments | audit | manual (see below) | `$EXPGYM_DATA_ROOT/contract-nli/test_segments.json` |
| ContractNLI hints | audit | shipped | `data/contract-nli/test_nda_span_dims.json` |

**HPOBench Python deps** (needed only for `hpobench:*` tuning tasks):

```bash
bash scripts/recreate_expgym_env.sh
# creates conda env expgym-hpobench with HPOBench (editable),
# tensorflow==1.15, scikit-learn==0.23.2, NASBench deps, and ConfigSpace.
```

The default smoke does not need these dependencies. The full HPOBench/NASBench
stack includes TensorFlow 1.15 and is intended for Linux/x86_64-style legacy
Python environments; Apple Silicon/macOS cannot run the NASBench101 dependency
stack natively.

Run HPOBench sweeps from that env:

```bash
conda run -n expgym-hpobench python scripts/run_paper_sweep.py \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks hpobench:paramnet:adult:steps \
  --cost-regimes cost_tight
```

**ContractNLI** (manual terms, scripted extraction): the audit scenario reads two files. The
hints file `test_nda_span_dims.json` (which drives the `human_feedback`
"Evidence Incomplete | missing: ..." messages) ships with this repo at
`data/contract-nli/test_nda_span_dims.json`. The document segments
`test_segments.json` come from Stanford and require manual download
because their release page asks you to accept data-use terms that cannot
be auto-clicked. Steps:

1. Open [stanfordnlp/contract-nli](https://stanfordnlp.github.io/contract-nli/)
   and download the dataset archive.
2. Run `python scripts/download_data.py --contract-nli-archive /path/to/contract-nli.zip`.
3. The script extracts `contract-nli/test.json` as
   `$EXPGYM_DATA_ROOT/contract-nli/test_segments.json`.

## Extending

A scenario is a Python module exporting a `SCENARIO` dict. The core
ReAct loop has no scenario-specific code, so adding one requires no
changes to `react_loop.py` or the budget machinery.

```python
SCENARIO = {
    "name": "my_world",
    "tools": {"my_tool": my_tool},   # or build_tools(): callable
    "build_context": ...,             # (include_overhead, **kw) -> str
    "build_instruction_notes": ...,   # (include_overhead) -> List[str]
    "build_fake_plan": ...,           # (probes, **kw) -> [(tool, payload)]
}
```

Register the module in `demo_experiment.py:17` (`_SCENARIOS` dict), and
add a branch in `resolve_base_cost()` if `--cost-regime` / `--beta`
should compute a budget for it.

## Environment variables

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `VLLM_API_KEY` | LLM backends |
| `OPENROUTER_API_KEY_FILE` | one-line OpenRouter key file, default `../openrouter.key` |
| `OPENROUTER_BASE_URL`, `EXPGYM_BASE_URL` | OpenRouter/OpenAI-compatible server override |
| `EXPGYM_OPENROUTER_MODEL` | default smoke model |
| `EXPGYM_DATA_ROOT` | parent of `contract-nli/` |
| `PHANTOM_WIKI_ROOT` | Phantom Wiki cache directory |
