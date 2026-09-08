---
name: expgym-runner
description: Run, reproduce, validate, debug, or adapt the ExpGym and PoolAct research codebase. Use for dataset setup, paper versus custom experiment matrices, fake and real-model evaluation (including OpenAI-compatible self-serving), HPOBench runtimes, verified resume, trace integrity, resource estimates, and portable model/task/PoolAct adaptations.
---

# ExpGym Runner

Treat ExpGym and PoolAct as one evaluation system with two runners. Establish the requested scope before running anything expensive, then verify both execution and result integrity.

## Locate and inspect the project

1. Prefer the current directory when it contains `scripts/run_paper_sweep.py`, `scripts/run_poolact.py`, and `expgym/`.
2. Otherwise honor `EXPGYM_REPO`, then search the current workspace for `LLM_ExpGym`.
3. Work from the repository root. Read `README.MD`, `docs/poolact.md`, runner `--help`, and `git status --short` before modifying or launching a large run.
4. If paper fidelity matters, locate the paper source and confirm which version is current. In this project it may be a sibling `paper/` repository; do not infer historical settings solely from current script defaults.

Preserve unrelated user changes. Generated datasets and run outputs are local artifacts and should not be committed unless explicitly requested.

## Classify the requested run

Use exactly one of these labels in the work log or response:

- **Static/fake validation**: free, deterministic code-path testing. It is necessary but does not validate a real provider.
- **Real smoke validation**: a tiny paid/API-backed run that proves transport, response parsing, scenario execution, scoring, and persistence.
- **Current repository full matrix**: the deliberate superset produced by `scripts/run_full.sh` for one model.
- **Paper-exact reproduction**: the precise paper version's models, scenarios, regimes, repeats, agent count, temperature, and step limit.
- **Custom study**: any deliberate deviation; list the deviations.

Never call `run_full.sh` “paper exact” without comparing it to the current paper. Read [references/experiment-matrix.md](references/experiment-matrix.md) for the known ICLR 2026 distinction and trace counts.

## Execute the validation ladder

1. Run the no-model-call preflight. Use setup only for an initial environment; do not reinstall or upgrade a frozen runtime during an active study. For a continuation, set `EXPGYM_VENV` to the recorded environment, verify its interpreter/dependency identity against the run manifest, and stop if it is missing or incompatible. `check.sh` otherwise auto-installs a missing default environment:

   ```bash
   # Initial setup only, not a frozen continuation:
   # bash scripts/setup.sh --with-data
   # export EXPGYM_VENV="$PWD/.venv"
   : "${EXPGYM_VENV:?Set the verified experiment environment first}"
   test -x "$EXPGYM_VENV/bin/python" &&
     EXPGYM_VENV="$EXPGYM_VENV" bash scripts/check.sh &&
     "$EXPGYM_VENV/bin/python" scripts/download_data.py --check
   ```

2. Resolve the intended command with `--dry-run`. Report models, scenarios, item ranges, regimes, repetitions, strategies, agents, maximum steps/evaluations, and the resulting job or agent-trace count before a large external run.
3. When the user asks for real verification, use a real backend. Do not stop after fake runs. Start with one item per relevant scenario/regime and the smallest useful agent count; use the exact target model in at least one preflight because provider access differs by model.
4. Inspect outputs using the integrity rules below. A process exit code alone is insufficient.
5. Launch the requested matrix with `--resume` and a stable output directory. Re-running the same command should skip only verified compatible results.
6. Summarize evidence: commands, actual matrix, result paths, validation status, failures/retries, and explicit deviations from the paper.

Use [references/runbook.md](references/runbook.md) for commands, Sub2API handling, Docker/HPOBench, validation queries, and troubleshooting.

## Judge results correctly

For ExpGym, require:

- process exit status 0;
- a schema-valid trace;
- `outcome.validation.passed == true` with repository score recomputation in trace v2, plus the runner's `score_check=ok` message;
- configuration and source fingerprints matching the current run.

For PoolAct, require for every selected item and strategy:

- `result.json` and all expected per-agent JSON files;
- every `agent_results[].score_check.ok == true`;
- finite aggregate performance;
- zero integer pending claims in the actual shared-state schema (`shared_state.graph.pending_claims` for current PoolAct); cached-only state need not contain a graph;
- current configuration, implementation, selected-data and evaluator-dependency identities;
- a valid item/batch `summary.json`.

A score of zero can be a valid but wrong model answer. Distinguish **runner/integrity success** from **semantic task performance**. Search F1 of zero, a valid NASBench configuration scoring poorly, or a budget stop is not automatically a software failure.

## Handle real APIs safely

- Load credentials from environment files without printing them. Never echo, serialize, commit, or paste API keys.
- For local Sub2API, require `SUB2API_API_KEY` and `SUB2API_BASE_URL`; `SUB2API_MODEL` is optional. Use the model ID requested by the user and preflight it explicitly.
- Empty/null `content` can be a valid native tool response. Preserve complete `assistant_message`, `tool_calls`, `reasoning_content`, finish reason, and paired tool-result IDs. Never flatten native calls into guessed text actions.
- A delivered reasoning-only/empty response, invalid model arguments, or `finish_reason=length` is not a transport retry. Record the decision once; any protocol repair consumes the normal agent-step horizon. Retry only the client's configured transient HTTP/transport failures, and retain every attempt's usage/dump, including unknown usage. An ambiguous malformed HTTP-200 envelope fails explicitly rather than being resampled for a better answer.
- For native models, inspect the effective rendered prompt and complete a real multi-turn tool smoke. Normal decisions send actual schemas with `tool_choice=auto`; forced final uses `none` while retaining schemas/history. A nominally healthy endpoint or fake text plan does not verify this path.
- Inspect the actual task's complete system and user messages, including task-builder instructions and PoolAct additions. A native system prompt can still conflict with text Action examples in the task context. Test changed production entrypoints with a native-capable mock transport; fake `auto` resolves to text and cannot cover that integration. Change only source-owned protocol instructions, preserving dataset text and explicit text-mode behavior.
- Do not estimate subscription or token consumption from visible trace length alone. Provider-side reasoning tokens and retried attempts may dominate. Measure a representative real pilot from Sub2API usage, then extrapolate from observed calls and charged usage with a safety margin.
- A model can be account- or plan-gated even when the endpoint works for another model. Report the provider error after secret redaction.
- When Sub2API runs inside Docker, use the repository wrapper; it rewrites localhost to `host.docker.internal`.

## Preserve ExpGym and PoolAct semantics when adapting

When adding or changing a model/backend:

1. Extend the existing client factory and CLI/environment resolution instead of bypassing `expgym/llm_clients.py`.
2. Normalize message/content and usage fields, bounded retries, timeout behavior, reasoning controls, and secret redaction.
3. Add fake/unit coverage and one authorized real smoke for the exact provider/model.

When adding or changing a scenario/task:

1. Follow the scenario interface registered through `_SCENARIOS`: context, system prompt/instruction notes, tools, fake plan, answer evaluator, and base cost.
2. Update selectors and validation consistently in `demo_experiment.py`, both runners, trace v2, summarization, and PoolAct aggregation/coverage logic.
3. Make environment feedback deterministic or snapshot-pinned. Record hashes and test score recomputation.
4. Add fake tests, data integrity tests, sequential real smoke, and PoolAct real smoke when PoolAct supports the scenario.

When changing PoolAct:

- Preserve one runtime and simulated clock per agent. Bind the same `time_budget` and `overhead_scale` to the coordinator runtime and the ReAct loop.
- Cache only completed observations at zero simulated cost; in-flight work is not a completed cache hit. Graph/cache views must respect the viewer's simulated time and strict feedback budget; withheld scores must not reappear through shared state or forced-final prompts.
- Keep the exploration graph and serialized LLM decision/pending-claim step while allowing environment tools to execute concurrently.
- Close pending claims on success and exception, and force final-answer locking when the protocol requires it.
- Record `POOLACT_PROTOCOL_VERSION` from the code (currently `paper-graph-lock-v3`); do not conflate this with trace schema v2 or byte-for-byte historical CARC output.

Preserve the default `legacy` tuning final policy and historical Audit scoring/voting unless the user deliberately requests a separately identified endpoint change. `submitted` is an explicit study option, not an unlabelled compatibility fix. For study design and data/dependency limits, read `docs/portable-study.md`.

For self-serving, record actual hardware, checkpoint/runtime identity, generation settings and measured seed behavior. A request seed is not proof it controls sampling; exact output repeatability is not required to conduct an explicitly stochastic study. Do not alter a model's computation merely to satisfy a seed flag. Confirm the actual HTTP payload: runner CLI and server defaults can differ.

After any adaptation, run the complete no-cost check and an authorized real smoke through every changed path.

## Communicate scope without ambiguity

Always state:

- whether the run is fake, real smoke, repository-full, paper-exact, or custom;
- the exact scenario/regime/model subset actually verified;
- whether HPOBench ran natively or in Docker;
- whether validation proves infrastructure only or includes meaningful statistical reproduction;
- what remains unrun.

Do not claim “no bugs” from a finite test suite. Say which checks and real paths passed and identify residual provider stochasticity, quota, platform, or unexecuted-matrix risk.
