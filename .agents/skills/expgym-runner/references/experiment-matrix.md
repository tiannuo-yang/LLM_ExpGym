# Experiment matrix and paper fidelity

Use this reference to distinguish the current ICLR 2026 paper experiments from convenient repository presets. Re-read the current paper source before asserting exact reproduction because later paper versions can change these values.

## ExpGym main ranking matrix

The current paper evaluates these six OpenRouter models with extended reasoning disabled:

- DeepSeek-V3.2
- GPT-5.2
- GPT-4.1
- Gemini-3-Flash
- Claude-Haiku-4.5
- Mistral-Large

Every environment uses the three regimes `cost_free`, `cost_moderate`, and `cost_tight`, with a common 30-agent-step limit.

| Scenario | Items | Repetitions | Temperature | Traces across 6 models and 3 regimes |
|---|---:|---:|---:|---:|
| Tuning | 9 HPOBench tasks | 3 | 0.7 | 486 |
| Restricted Search | 35 seed-1 three-hop whois + whatis questions | 1 | 0.0 | 630 |
| Evidence Audit | 13 ContractNLI documents, 3 hypothesis orderings | 3 | 0.0 | 702 |
| Total | | | | 1,818 |

This is 303 sequential ExpGym traces per model.

The nine tuning tasks are:

- ParamNet adult, higgs, and letter at `:steps` fidelity;
- NASBench-101 A, B, and C;
- NASBench-201 cifar10-valid, cifar100, and imagenet16-120.

`scripts/run_full.sh --part expgym` selects the correct item/repetition/regime count for one model, but the current runner defaults to 10 steps unless overridden inside the lower-level command. The paper states a 30-step common limit. Check resolved configuration before calling any run exact.

## PoolAct main fixed-parallelism table

The PoolAct main table is a smaller, separate matrix:

- models: DSV3.2, Haiku-4.5, Gemini-3;
- regimes: `cost_tight` and `cost_moderate` only;
- items: 18 whois questions, all 13 audit documents, and only NASBench-101:A;
- strategies: `naive`, `cached`, `poolact`;
- agents: 4;
- temperature: 0.7 throughout;
- aggregation: majority vote for Search, per-hypothesis vote for Audit, best-of-N for Tuning.

The local PhantomWiki loader stable-sorts by `(type, difficulty)`: indices `0:18` are the 18 type-11/12 whois questions; indices `18:35` are whatis. Reconfirm this after data or loader changes.

Per model, the main table contains:

```text
(18 Search + 13 Audit + 1 Tuning) × 2 regimes × 3 strategies
= 192 item/strategy runs
= 768 agent traces at N=4
```

Across the three paper models, it is 576 item/strategy runs and 2,304 agent traces.

## Why `run_full.sh --part poolact` is not the paper table

The current repository-full PoolAct preset is a deliberate superset for one model:

```text
(9 HPO + 35 Search + 13 Audit) × 3 regimes × 3 strategies × 4 agents
= 2,052 agent traces per model
```

It includes cost-free PoolAct, all 35 search questions, and all nine HPO tasks. Do not use that count to estimate the main PoolAct table or describe it as paper exact.

## Separate analyses

- Naive scaling figure: Haiku-4.5 only, N=1 through 8, Moderate and Tight. The paper averages offline over subsets of eight distinct seeded agents. Do not turn every subset into new LLM calls. Coordinated variants are reported at N=4 and N=8.
- Reasoning-lock ablation: separate from the main table; Haiku, N=8, Tight Search, with versus without the lock.
- Extended-reasoning analysis: separate from the main ExpGym ranking matrix.

Name these as separate experiments and do not silently add them to main-table cost estimates.

## Reproduction language

Use “paper-exact” only when model/provider identity, reasoning mode, items, regimes, repetitions, temperature, step/evaluation caps, seeds/orderings, strategy, agent count, data snapshot, and code/paper version all match.

If unavailable historical models are replaced by a Sub2API GPT model, call it a custom rerun on the paper matrix, not reproduction of the reported cross-model table.
