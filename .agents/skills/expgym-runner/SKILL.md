---
name: expgym-runner
description: Run, debug, validate, or adapt ExpGym and PoolAct experiments, including OpenAI-compatible self-serving, native tool protocols, HPOBench runtimes, repeat isolation, and reproducible result delivery.
---

# ExpGym Runner

Treat ExpGym and PoolAct as one system with two runners. Preserve the user's experiment settings and distinguish framework correctness from model performance.

## Pick the relevant path

Locate the requested repository (honor `EXPGYM_REPO`) and inspect `git status --short` before edits. Preserve unrelated changes and frozen run artifacts. For initial orientation, read `README.MD` and `docs/poolact.md`; inspect the relevant runner's `--help` before changing its invocation, not before every metadata-only check.

Label work as **Static/fake validation**, **Real smoke validation**, **Current repository full matrix**, **Paper-exact reproduction**, or **Custom study**.

- For paper claims or matrix design, read [experiment-matrix.md](references/experiment-matrix.md) and confirm the actual paper version. `run_full.sh` is a superset, not automatically paper-exact.
- For setup, provider transport, HPO runtimes, CLI examples or failure diagnosis, read the relevant sections of [runbook.md](references/runbook.md).
- For scientific endpoints, study registration and descriptive analysis, read `docs/portable-study.md`. It does not implement confirmatory inference.
- For normal missing answers versus execution failures, read `docs/task-abstention-v5.md`; for explicit provider aborts, read `docs/provider-abort-v4.md`.
- For analysis packaging, Git publication or restoration, read `docs/efficient-delivery.md`. Use explicit input inventories and `scripts/package_run.py`; stream-verify archives and restore only needed inputs. Local-only sealing is not public clearance. Reuse unchanged archive identities and scan the actual publication delta.

A status question needs current process/artifact evidence and an answer, not a restart of the entire validation ladder.

## Make compatibility fixes portable

Branch on explicit capabilities, protocol or observed response shape, not model-name guesses. Keep necessary model/provider adapters explicit and recorded: template/parser, thinking and sampling settings are configuration, not permission to alter scoring or resample failures. Test fixes with unfamiliar model IDs and native/text/tool-only/reasoning-only/malformed envelopes as applicable.

- Preserve complete native assistant messages, tool calls, reasoning, tool-result IDs, finish reasons and every attempt's usage. Empty `content` with tool calls can be valid.
- Normal native decisions send real tool schemas and `tool_choice=auto`; forced final uses `none` while retaining schemas/history. Fake text runs cannot verify this native transport path.
- Inspect task-owned system **and user** instructions. Change incompatible protocol examples at their source; do not scrub question/document text or model history globally.
- Do not recover rejected reasoning, quoted examples or partial tool messages through a catch-all final-answer fallback.
- Delivered empty/length/malformed decisions are not free HTTP retries. Keep normal step-bounded protocol repair separate from configured transient transport retries. Explicit aborts remain failures.
- Record effective request parameters and observed seed behavior. A seed flag is not proof of independent or repeatable generation.

Load credentials without printing them; never serialize real keys into traces, plans, logs or Git.

## Preserve task and PoolAct semantics

Keep historical `legacy` tuning final selection and Audit scoring/voting unless the user requests a separately identified endpoint. `submitted` and `task-abstention-v1` are explicit study policies; do not enable them silently for one model.

For PoolAct, retain one fresh coordinator/cache/graph per independent pool and one runtime/clock per agent. Agent states within a pool may be shared according to the algorithm, but independent repetitions must not share mutable state. Bind the same budget and overhead scale in the runtime and ReAct loop.

Only completed, time-visible observations are cache hits. Withheld budget feedback must not leak through graph views, cached observations or forced-final prompts. Preserve the reasoning/claim critical section while environment tools run concurrently; close pending claims on completion and exceptions. Record the actual `POOLACT_PROTOCOL_VERSION`, not a guessed historical label.

## Verify the right outcome

Separate `execution_complete`, `score_complete` and task performance.

- Sequential scored results need matching source/config/data/evaluator identities, a valid trace and repository score validation.
- PoolAct needs all expected agent files, validated individual and aggregate results, matching identities, a consistent summary and zero pending claims.
- Under explicit `task-abstention-v1`, a normal missing Search/Audit answer preserves raw null and scores the empty prediction through the original evaluator. A missing HPO configuration is unscorable; full-pool MI/BoN stays unknown if a required agent is missing. Do not require finite performance for a legitimately recorded unscorable endpoint.
- Transport, tool, scorer and persistence exceptions remain failures, not abstentions or successful zero scores.
- Valid wrong answers, zero scores, normal missing answers and negative effects remain in the planned accounting. Do not retry or exclude them to improve results.

Use identity-checked resume. An integrity-only check must forbid model calls rather than silently rerun a stale result. A hash-bound receipt is evidence for its stated scope, not independent proof of scientific truth.

## Validate proportionately and stop

During development, run focused tests for changed behavior. Run the full no-cost suite and fake runner integration once per coherent code revision before delivery; reuse its result for unchanged code. Documentation-only changes need link/schema review, not a new model run.

Use the recorded interpreter for an existing study; never reinstall a frozen environment to make a check pass. `scripts/check.sh` bootstraps a missing environment, so verify `EXPGYM_VENV/bin/python` exists before invoking it. ParamNet requires the verified legacy environment; fake or skipped tests do not establish that real path.

New or changed model-facing/execution paths require an authorized representative real smoke before a full experiment. If this task is code-only or no GPU/API run is requested, finish the static/fake work and state that real smoke remains unperformed; do not acquire resources automatically.

Keep one plan, one execution record and one report per meaningful revision. Reuse immutable input inventories and completed checks; do not recursively create reviews of reviews, re-extract every raw file for metadata-only work, or repeat full scans for unchanged report text. Retain necessary safety scans, score-integrity checks, failed-attempt costs and the user's requested independent post-report review.

Report the actual scope, changed behavior, tests, source/result locations, remaining limitations and whether code was pushed or merged. Finite tests do not prove “no bugs,” and desired performance trends are not an acceptance criterion for a bug fix.
