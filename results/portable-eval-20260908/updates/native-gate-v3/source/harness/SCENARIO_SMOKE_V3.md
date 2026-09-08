# K3 v3 native-context integration gate

This is a **Real smoke validation** plan, not paper reproduction or a performance
study. The preceding v2 run keeps all 45 traces and costs; its artifact acceptance
does not override its failed native task-context compatibility gate. No outcomes
are replaced. A fake execution below is **Static/fake validation** only.

## Fixed scope

| Runner | Tasks | Regime | Strategies / agents | Traces | Verified resume skips |
|---|---|---|---|---:|---:|
| ExpGym | NASBench-101:A, Search seed-1 item 0, Audit item 0 | Moderate | sequential | 3 | 3 |
| PoolAct | same three task selectors | Moderate | naive, cached, poolact; 2 agents each | 18 | 9 |
| Total | 6 child jobs | | | 21 | 12 |

This six-job gate is separate from the A21 HPO pilot, which has different jobs,
task coverage, and authorization.

The limits are 3 ordinary agent steps, 2 tool evaluations, 1 bounded protocol
repair, and up to 4 logical generations including a forced final. There are 4
child workers and a conservative simultaneous-generation bound of 7. The model
profile is K3-only: temperature 1, top-p 1, no top-k override, 32,768 output tokens,
reasoning max, K3 thinking enabled. Seeds 1206/1207 are **labels only**, not proven
deterministic or independently controlled sampling. PoolAct's input estimate cap
is 131,072; ExpGym has no runner input trim. Recorded server and effective
admission limits remain separate quantities.

## Acceptance fixed before the first v3 model request

1. Artifact integrity: exact plan/source/data/dependency identities, all 21 scored
   traces, valid strategy summaries and no pending claims, full request dumps,
   and 12 guarded resume skips. Offline scoring remains enabled during resume;
   model construction/generation is blocked. Original result/trace/dump bytes,
   size, and mtime must remain unchanged. Summaries must retain bytes and semantic
   contents; their mtime may legitimately change.
2. Trusted instructions: exact system and actual task-builder context, exact
   native schemas, and the fixed PoolAct graph renderer's instruction grammar.
   Task/model/tool data is not globally filtered for words such as `Action:`.
   Graph checks do not reconstruct historical concurrent graph state.
3. Native paths: each client must show normal `auto`; every coordinated client
   must show graph context. Native continuation and forced `none` are checked
   by the union of clients within each of 12 runner/scenario/strategy cells.
   No branch evidence is borrowed between cells. Full ordered assistant/tool
   history and request profile are integrity requirements, not optional coverage.

A legal early answer can leave a path unobserved. It is retained, remaining fixed
jobs continue, and the gap is reported without replacement calls. A semantic zero
is not infrastructure failure. An integrity failure stops new dispatch and drains
already-started jobs. Real promotion requires all three gates; fake text execution
can pass artifact checks but cannot pass native prompt/path promotion.

## Execution control

`scenario_smoke_v3.py` imports only hash-pinned helpers from the preceding harness
and shared request-profile module; it neither calls the old coordinator's main nor
changes frozen repository source. Supply `--static-acceptance` explicitly.
`--request-profile` accepts only the presently validated K3 profile.

First generate a fresh dry plan. Real execution additionally requires the bound
endpoint, private key file, a serving-evidence sidecar, and a post-plan authorization
that hashes the exact manifest, commands, source, helpers, profile, and counts.
The authorization is deliberately not inside the manifest identity, avoiding a
circular hash. An existing started/completed attempt is never automatically replayed.

Serving evidence demonstrates observed successful transport and configured
admission. It does not assert saturated throughput, a queueing guarantee, strict
seed control, or prompt compatibility. All proxy variables are removed before
child execution and `NO_PROXY=no_proxy=*` is set; credentials are read privately,
never embedded in command arguments or receipts.
