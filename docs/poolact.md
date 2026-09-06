# PoolAct implementation and reproduction

PoolAct coordinates parallel ExpGym agents through observation pooling. The
public implementation follows Algorithm 1 in the paper and has three shared
objects:

1. `SharedObservationCache`: completed identical actions can be reused at zero
   simulated cost.
2. `SharedExplorationGraph`: records completed actions, exploration paths,
   coverage gaps, and actions currently `In Progress`.
3. A reasoning lock: graph injection, one LLM decision, and recording that
   decision's pending claim are one serialized critical section.

The serialized result identifies this contract as
`paper-graph-lock-v2` (`expgym.poolact.POOLACT_PROTOCOL_VERSION`).

After the claim is recorded, the lock is released and the tool executes in
parallel with other agents' tools.

## Run it

One-time setup (Python 3.9+):

```bash
bash scripts/setup.sh
```

The eval scripts automatically use the resulting `.venv`; activation is not
required.

No-cost functional smoke:

```bash
bash scripts/eval_poolact.sh --backend fake --agents 2
```

Real model:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_poolact.sh \
  --model openai/gpt-4.1-nano \
  --agents 4
```

Local Sub2API:

```bash
set -a
source /path/to/sub2api/.sub2api-client.env
set +a

bash scripts/eval_poolact.sh \
  --backend sub2api \
  --model gpt-5.4 \
  --agents 4
```

Strategy comparison:

```bash
bash scripts/eval_poolact.sh \
  --agents 4 \
  --strategies naive,cached,poolact \
  --output-dir runs/poolact_comparison
```

Five Search questions in one resumable command:

```bash
bash scripts/eval_poolact.sh --with-auto-data \
  --scenario restricted_search \
  --questions 0:5 \
  --agents 4 \
  --strategies naive,cached,poolact \
  --output-dir runs/poolact_search_5q
```

The range is half-open, so `0:5` selects 0 through 4. Batch results are stored
under `item_0/`, `item_1/`, and so on. The top-level `summary.json` reports the
mean `answer_perf` for every strategy. Use `--dry-run` to preview without model
calls.

The Python runner exposes all advanced flags:

```bash
.venv/bin/python scripts/run_poolact.py --help
```

## Paper-to-code mapping

| Paper operation | Code |
|---|---|
| Launch N parallel threads | `expgym.poolact.run_agents_parallel` |
| Shared cache C | `SharedObservationCache` |
| Shared graph G | `SharedExplorationGraph` |
| Acquire reasoning lock | `run_react_loop(..., llm_lock=...)` |
| Inject G before reasoning | `make_graph_augmenter` |
| Record pending claim before unlock | `make_pre_tool_hook` |
| Execute tools in parallel | tool call outside the locked ReAct section |
| Return cached observation at zero cost | `wrap_tools_with_poolact` |
| Mark claim completed and update G | PoolAct tool wrapper |
| Best-of-N / majority / per-hypothesis vote | `aggregate_results` |

The graph text uses the same four concepts described in the paper:
`In Progress`, `Already Explored`, `Exploration Paths`, and `Coverage Gap`.

## Library API

```python
from expgym.poolact import PoolActCoordinator
from expgym.react_loop import run_react_loop

coordinator = PoolActCoordinator(n_agents=4)
runtime = coordinator.bind_tools(my_tools, agent_id=0)

result = run_react_loop(
    llm=my_llm,
    tools=runtime.tools,
    context=my_context,
    observation_augmenter=runtime.observation_augmenter,
    agent_clock=runtime.clock,
    pre_tool_hook=runtime.pre_tool_hook,
    llm_lock=runtime.reasoning_lock,
)
```

Create one runtime per agent from the same coordinator. Do not share a runtime
or `AgentClock` between agents.

## Concurrency semantics

PoolAct deliberately does not block an action merely because another agent is
currently executing the same action. The pending action is visible in the
graph, and the next LLM may choose another path. If it chooses the duplicate
anyway, both tools may execute. This is the paper's soft-coordination design.

Only completed observations are cache hits. A hit returns the original tool
result with its simulated overhead changed to zero. Virtual completion times
ensure an agent cannot observe a result from the future of the simulated
parallel timeline.

The ReAct loop, not the wrapper, advances each agent's virtual clock. Wrappers
only calculate the future completion timestamp used by the shared cache and
graph. This keeps every paid interaction counted exactly once.

## Outputs and provenance

For a single item, each strategy writes:

```text
<output>/
├── summary.json
└── poolact/
    ├── result.json
    └── agents/
        ├── agent_0.json
        └── ...
```

`result.json` contains individual answers, aggregate answer and score, cache
and graph statistics, the complete resolved configuration, and a fingerprint
of the repository source tree. Files are written atomically; `--resume` skips a
result only after validating the configuration, source fingerprint, aggregate
score, every agent trace, and the separate per-agent files.

With `--questions`, the same tree appears under `<output>/item_N/` for each
selected item, and `<output>/summary.json` contains the per-item results and
cross-item mean scores.

## Compatibility

Early internal experiments used two confusing names:

- `wrap_tools_with_poolact` for a flat ledger prototype.
- `wrap_tools_with_polact` for the graph implementation.

The public API now uses `wrap_tools_with_poolact` for the paper's graph-based
implementation. `wrap_tools_with_polact` remains an alias, and the flat ledger
is available explicitly as `wrap_tools_with_ledger`.

### Historical CARC runs

This is the corrected, paper-conformant reference implementation, not a
bit-for-bit copy of the historical CARC working tree. During migration we fixed
five behaviors that can change rerun trajectories:

- the graph is now injected before the first LLM decision as well as later
  decisions;
- cache hits and tool exceptions close their pending claims;
- forced final-answer calls also use the reasoning lock;
- concurrent cache writes retain the result with the earliest simulated
  completion time;
- semantic search answers with different name ordering share one majority-vote
  bucket.

The historical artifacts remain evidence for the reported runs, but fresh
experiments should record the new implementation hashes and should not be
expected to reproduce stochastic API outputs byte-for-byte.
