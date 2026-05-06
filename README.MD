# ExpGym: Evaluating LLM Agents in Expensive Worlds

ExpGym is for testing LLM agents on tasks where each tool call is slow,
seconds to minutes per call. There are three scenarios: hyperparameter
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

## Quick check: do the paper's numbers come from the shipped data?

The full experiment in the paper is about a day of LLM API calls. A
reviewer cannot redo that, so the actual outputs from that experiment
are saved and shipped with this repo as a small file of traces. A short
script then reads those traces and recomputes the metrics, so you can
verify that the numbers in the paper really come from the data we
provide. It is a pipeline check, not a rerun of the LLM experiments.

From the repo root:

```bash
python reproduce.py
```

The script reads `data/repro/v17_search_whois_traces.json`, recomputes
the 18 search-F1 numbers in the *whois* column of Table 2, and prints
each one next to the value reported in the paper. If everything matches
you will see:

```
ALL 18 CELLS MATCH the paper to within 0.0005
```

It finishes in a few seconds. No LLM calls, no API key, no internet
needed.

## Install

```bash
conda env create -f environment.yml && conda activate expgym
# or:
pip install -r requirements.txt
```

```bash
python -m unittest discover tests
# Ran 129 tests, OK (skipped=31; external-data tests skip cleanly)
```

## Run a scenario

One trace, FakeLLM, no API key:

```bash
python demo_experiment.py --baseline both --max-evals 6
```

The full menu:

```bash
python demo_experiment.py --backend openai --model gpt-4o-mini
python demo_experiment.py --scenario tuning --tuning-task hpobench:svm_surrogate
python demo_experiment.py --scenario restricted_search --question-index 5
python demo_experiment.py --scenario evidence_audit --max-steps 20
```

| Scenario | Module | EEI source | Per-call cost (surrogate wallclock) |
|---|---|---|---|
| Hyperparameter tuning | `expgym/task_tuning.py` | HPOBench surrogate eval (`--list-tuning-tasks` for the menu) | 8–50,000 s |
| Restricted search | `expgym/task_restricted_search.py` | Phantom Wiki document fetch | 300 ± 20 s |
| Evidence audit | `expgym/task_evidence_audit.py` | Simulated human verification | 300 ± 20 s |

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

Only needed beyond `reproduce.py`. Phantom Wiki and HPOBench
auto-download; ContractNLI is manual.

```bash
python scripts/download_data.py            # fetches Phantom Wiki + HPOBench
python scripts/download_data.py --check    # layout-only, no network
```

| Dataset | Used by | Source | Lands at |
|---|---|---|---|
| HPOBench code | tuning | `git clone` (auto) | `data/hpo_tuning/HPOBench/` |
| Phantom Wiki | search | HuggingFace (auto) | `$PHANTOM_WIKI_ROOT/...` |
| ContractNLI | audit | manual (see below) | `$EXPGYM_DATA_ROOT/contract-nli/` |
| HPOBench oracle, repro fixture | tuning, β presets, `reproduce.py` | shipped | `data/hpo_tuning/oracle3.json`, `data/repro/...` |

**HPOBench Python deps** (run after the HPOBench source clone — this is
the biggest reproducibility hazard if you skip it):

```bash
bash scripts/recreate_expgym_env.sh
# installs HPOBench (editable) + tensorflow==1.15, protobuf<4,
# scikit-learn==0.23.2, automl/nas_benchmarks, google-research/nasbench
```

**ContractNLI** (manual): Stanford's release page requires accepting
data-use terms that cannot be auto-clicked. Download from
[stanfordnlp/contract-nli](https://stanfordnlp.github.io/contract-nli/),
extract, then copy `test_segments.json` and `test_nda_span_dims.json`
into `$EXPGYM_DATA_ROOT/contract-nli/`.

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
| `EXPGYM_DATA_ROOT` | parent of `contract-nli/` |
| `PHANTOM_WIKI_ROOT` | Phantom Wiki cache directory |
