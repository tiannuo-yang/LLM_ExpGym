# Explicit PoolAct coordination ablations

This is a custom-study execution interface. Select arms with
`scripts/run_poolact.py --strategies naive,cached,peer_context,graph_no_lock,poolact`.
The default remains `poolact`; the existing three arms retain their execution,
scoring, cache, and graph semantics. No model-name special cases are used.

| Strategy | Shared observation cache | Injected coordination context | Reasoning/claim lock | Protocol identity |
|---|---|---|---|---|
| `naive` | No | None | No | `independent-agents-v1` |
| `cached` | Yes | None | No | `shared-observation-cache-v1` |
| `peer_context` | Yes | Full completed observations from other agents | No | `full-peer-context-v1` |
| `graph_no_lock` | Yes | Existing v4 graph, paths, coverage, pending claims | No | `paper-graph-no-lock-v1` |
| `poolact` | Yes | Same v4 graph, paths, coverage, pending claims | Yes | `paper-graph-lock-v4` |

Each invocation creates fresh mutable state for its pool. Each agent has its
own runtime and simulated clock. All arms keep the same step, evaluation,
budget, native-tool, final-answer, and scoring policies supplied by the runner.
Internal cache/graph/peer-store data locks remain enabled in every shared arm.
Concurrent cache misses can still execute duplicate tools; none of the caches
claims to reserve a key or wait for another agent's result.

## Graph without the reasoning lock

`graph_no_lock` uses the same graph wrapper, graph injection, claim hook, and
claim cleanup as full PoolAct. It omits only the lock spanning snapshot
injection, model decision, and claim registration. Environment tools continue
to run concurrently in both variants. Tool exceptions close their claims;
the runner's `finally` also closes any outstanding claims for an exiting
agent. A completed pool requires zero pending claims.

Full PoolAct still serializes that decision section, including forced-final
calls. No-lock arms allow overlapping model calls, so graph snapshots can
become stale before the chosen action is registered. This is the intended
mechanism difference, not an unsafe concurrent write to the graph.

## Full peer context

`peer_context` uses a new `SharedPeerContext`, not the legacy truncated ledger.
Every successfully completed tool call, including cache hits, adds an
immutable record. Records carry agent ID, exact tool name and payload string,
full tool-return string, cache-hit flag, completion time, and insertion
sequence. The full tuple is retained, including result/performance/cost fields;
cache-hit records contain the zero cost actually returned to that agent.
Records are not deduplicated, summarized, or limited to 30 entries/80 characters.
Snapshots preserve physical publication order after applying visibility.

A receiving agent sees only other agents' physically completed observations
whose simulated completion satisfies both `completion_time <= receiver_clock`
and `completion_time < time_budget` when a finite budget exists. Thus future
observations and feedback at the strict budget boundary stay hidden. The
wrapper predicts completion time; only the ReAct loop advances its clock,
exactly once. The same execution-contract checks reject mixed clocks,
overhead scales, or budgets before model/tool execution.

Peer snapshots contain no private reasoning, agent final answers, or pending
actions without results. Failed or malformed tool results are not published.
The full graph arm additionally provides pending claims and its existing
path/coverage representations: `peer_context` to `graph_no_lock` therefore
compares this entire representation/information bundle, not graph formatting
alone. It is not a factorial estimate of an isolated graph effect.

## Context capacity and actual requests

All arms retain the existing history policy: a new shared snapshot is appended
to the latest environment message, prior snapshots remain in history, and the
normal context preparation may shorten observations and remove old complete
decision groups. The native tool call/result pairing is retained. Backends
requiring immutable signed history keep their existing admission-only policy.

For `peer_context`, the latest appended snapshot is an additional completeness
requirement. If the normal preparation would truncate or drop that snapshot,
the request is **not sent**. This guard also covers forced final. It does not
replace old snapshots or grant this arm a different history-retention policy.
Earlier snapshots remain subject to the same historical trimming rules as in
the graph arms. A capacity stop and any missing answer remain in the recorded
outcome; do not silently shorten, resample, or enlarge the cap for this arm.

Every returned trajectory now has `context_preparations`: source/prepared
message and serialized-character counts, changed-history and dropped-message
counts, latest protected snapshot length/SHA, its completeness, admission, and
the reason for a blocked request. These are preparation events, not extra API
attempts. Actual admitted requests are still preserved in API dumps. The
context token estimate remains the repository's character heuristic, not a
guarantee from the checkpoint tokenizer.

## Identity, resume, and analysis

`config.strategy_protocols` binds each selected arm to its actual protocol.
Each pool result, agent result, and API dump context also has
`strategy_protocol`. The existing `config.poolact_protocol` identifies the
full-graph implementation lineage; it is not a claim that all arms use its
reasoning lock. Source identity, strategy, actual protocol, generation,
task/data identity, budget, agent count, and repeat/seed namespace are bound in
the existing config/resume/cache derivation. Resume checks the pool and agent
strategy protocols as well as the full expected config, source identity,
artifacts, scoring, and claim closure. Provider prompt-cache keys remain
routing requests, not proof of physical KV isolation.

The five-arm plot should retain negative/zero differences and each task's
own metric orientation. A sequence of adjacent differences describes effects
conditional on the preceding arm; it does not establish independent additive
contributions. Full PoolAct having the highest bar is a hypothesis, not a
validation condition. Native multi-turn, scoring, and representative actual
peer/graph contexts require a separately recorded real pilot before a study.

The focused no-cost coverage is in
[`test_poolact_ablations.py`](../tests/test_poolact_ablations.py),
[`test_peer_context.py`](../tests/test_peer_context.py), and existing
PoolAct visibility, graph identity, execution-contract, native ReAct, and
runner tests.
