# ExpGym and PoolAct runbook

Run all commands from the `LLM_ExpGym` repository root. Inspect each script's `--help` because CLI options may evolve.

## Setup and no-cost validation

For initial setup only, run `bash scripts/setup.sh --with-data`. For an existing
study, locate and verify the recorded interpreter/dependency identity first;
set `EXPGYM_VENV` to that environment, not an assumed default `.venv`:

```bash
: "${EXPGYM_VENV:?Set the verified experiment environment first}"
test -x "$EXPGYM_VENV/bin/python" &&
  EXPGYM_VENV="$EXPGYM_VENV" bash scripts/check.sh &&
  "$EXPGYM_VENV/bin/python" scripts/download_data.py --check
```

Do not bypass this existence/identity guard for a frozen continuation:
`check.sh` automatically invokes setup if its selected Python is missing.

Use setup for an initial environment only; continue a frozen study without reinstalling its dependencies. `scripts/check.sh` compiles Python, syntax-checks shell, runs the unit/integration suite, then executes fake ExpGym and all three fake PoolAct strategies. HPO native skips are expected when legacy dependencies are absent; required ParamNet paths still need separate pinned-runtime validation. A passing fake check does not prove real provider compatibility.

Dataset setup can transiently use roughly 3.2 GiB and retains roughly 215 MiB of HPO data. Downloads are checksum-verified and atomically installed.

## Load local Sub2API without exposing secrets

Use a user-provided env file. If none is given, locate `.sub2api-client.env` in the adjacent Sub2API deployment. Source it; never display it:

```bash
set -a
source /path/to/sub2api/.sub2api-client.env
set +a
test -n "${SUB2API_API_KEY:-}" && test -n "${SUB2API_BASE_URL:-}"
```

Do not run `env`, `set`, `printenv`, shell tracing, or commands that print the key. Use the user's explicit model ID; the example names below are not a current availability guarantee. Provider access is account-specific. A real smoke for the intended model is needed before a large new run, not before documentation or offline artifact work.

## Small real validation

Start with small limits, but cover every relevant path. These examples make actual external calls:

```bash
bash scripts/eval_model.sh \
  --backend sub2api --model gpt-5.3-codex-spark \
  --scenario restricted_search --questions 0 \
  --budget cost_tight --max-steps 4 --max-evals 3 \
  --output-dir runs/real_smoke/expgym_search

bash scripts/eval_poolact.sh \
  --backend sub2api --model gpt-5.3-codex-spark \
  --scenario restricted_search --questions 0 \
  --budget cost_tight --strategies naive,cached,poolact --agents 2 \
  --max-steps 4 --max-evals 3 \
  --output-dir runs/real_smoke/poolact_search
```

Cover changed protocol/task/scoring paths with the smallest explicitly planned pilot. Include native tool delivery and forced final when those paths change, and a budget boundary when budget logic changes. Do not automatically multiply every smoke across all regimes and strategies when the same implementation is already covered by tests and an unchanged real smoke. Use a compact NASBench task when that is the relevant tuning path. Retain normal early answers instead of resampling until a desired path appears.

Small limits validate plumbing, not paper statistics. A zero F1 with valid `score_check` is a semantic failure by the sampled model, not a broken runner.

## Construct the ExpGym paper main matrix

For the exact OpenRouter model set, run Search and Audit natively, with the paper's 30-step limit and fixed temperatures:

```bash
.venv/bin/python scripts/run_paper_sweep.py \
  --backend openrouter \
  --models dsv32,gpt52,gpt41,gemini3flash,haiku45,mistral_large \
  --scenarios restricted_search,evidence_audit \
  --search-indices 0:35 --audit-indices 0:13 \
  --cost-regimes cost_free,cost_moderate,cost_tight \
  --search-reps 1 --audit-reps 3 \
  --temperature-eval 0.0 --max-steps 30 --max-evals 30 \
  --output-dir runs/paper_expgym --resume
```

Run the nine HPOBench tasks through the pinned Docker environment:

```bash
bash scripts/run_hpobench_docker.sh \
  --backend openrouter \
  --models dsv32,gpt52,gpt41,gemini3flash,haiku45,mistral_large \
  --scenarios tuning --tuning-tasks all-hpobench \
  --cost-regimes cost_free,cost_moderate,cost_tight \
  --tuning-reps 3 --temperature-tuning 0.7 \
  --max-steps 30 --max-evals 30 \
  --output-dir runs/paper_expgym --resume
```

Use `--dry-run` on `scripts/run_paper_sweep.py` first and require 1,818 planned traces across the combined matrix. The two execution commands divide this into 1,332 native Search/Audit traces and 486 Docker HPO traces. Build the Docker image once, then use `--no-build` when resuming.

Replacing the six paper models with one Sub2API GPT model produces 303 traces on the paper ExpGym item/regime matrix, but it is a custom rerun rather than the reported cross-model reproduction.

## Current repository-full run

Preview one model's superset without external calls:

```bash
bash scripts/run_full.sh \
  --backend sub2api --model gpt-5.3-codex-spark --dry-run
```

Run one or both parts with verified resume:

```bash
bash scripts/run_full.sh \
  --part expgym --backend sub2api --model gpt-5.3-codex-spark \
  --output-dir runs/full_gpt53_spark

bash scripts/run_full.sh \
  --part poolact --backend sub2api --model gpt-5.3-codex-spark \
  --agents 4 --output-dir runs/full_gpt53_spark --no-build
```

This PoolAct command is the repository superset, not the PoolAct paper main table. See `experiment-matrix.md`.

## Construct the PoolAct paper main-table subset

For each exact paper model/backend, run Search and Audit under both `cost_tight` and `cost_moderate`, with strategies `naive,cached,poolact`, four agents, temperature 0.7, and the paper's 30-step limit:

```bash
bash scripts/eval_poolact.sh \
  --backend BACKEND --model MODEL \
  --scenario restricted_search --questions 0:18 \
  --budget cost_tight --strategies naive,cached,poolact --agents 4 \
  --temperature 0.7 --max-steps 30 --max-evals 30 \
  --output-dir runs/paper_poolact/MODEL/cost_tight/search

bash scripts/eval_poolact.sh \
  --backend BACKEND --model MODEL \
  --scenario evidence_audit --questions 0:13 \
  --budget cost_tight --strategies naive,cached,poolact --agents 4 \
  --temperature 0.7 --max-steps 30 --max-evals 30 \
  --output-dir runs/paper_poolact/MODEL/cost_tight/audit
```

Repeat with `cost_moderate`. Use the HPO Docker wrapper for NASBench-101:A:

```bash
bash scripts/run_hpobench_docker.sh --poolact --no-build \
  --backend BACKEND --model MODEL \
  --scenario tuning --tuning-task hpobench:nasbench101:A \
  --cost-regime cost_tight --strategies naive,cached,poolact --agents 4 \
  --temperature 0.7 --max-steps 30 --max-evals 30 \
  --output-dir runs/paper_poolact/MODEL/cost_tight/tuning --resume
```

Build once without `--no-build`, then reuse the image. Repeat tuning for Moderate. Run each planned command with `--dry-run` at the lower runner level first and inspect resolved JSON.

Provider aliases are not necessarily the paper model IDs. Record the exact resolved model and whether extended reasoning is disabled.

## HPOBench and platform adaptation

Use:

```bash
bash scripts/run_hpobench_docker.sh [--no-build] [--poolact] <runner arguments>
```

The image is `linux/amd64` with Python 3.7 and legacy scikit-learn for ParamNet. On Apple Silicon it runs under emulation and is slower. Docker Desktop/Engine must be installed and running.

The adapters intentionally avoid obsolete heavyweight runtime dependencies:

- ParamNet downloads six exact blobs from a pinned HPOlib2 fork because the original automl URL is dead.
- NASBench-201 converts the official NATS topology archive instead of using the obsolete 16 GiB JSON/dependency path; maximum fidelity is 200.
- NASBench-101 converts the official TFRecord without TensorFlow; maximum fidelity is 108.

Do not add TensorFlow or official NASBench runtime imports back to the main environment. Old TensorFlow 1.15 on Apple Silicon can hang or crash under amd64/AVX assumptions. Invalid NASBench-101 DAGs can legitimately score zero.

For local Sub2API in Docker, use the wrapper so `127.0.0.1` or `localhost` is rewritten to `host.docker.internal` and only required credential variables enter the container.

## Validate persisted outputs

For sequential ExpGym, use the runner's terminal `score_check=ok`, then require `outcome.validation.passed == true` and method `repository_score_recompute` in trace v2. For PoolAct, programmatically scan every result instead of sampling one file. A safe read-only check is:

```bash
.venv/bin/python - <<'PY' runs/poolact
import json, math, pathlib, sys
root = pathlib.Path(sys.argv[1])
paths = sorted(root.rglob("result.json"))
assert paths, f"no result.json below {root}"
for path in paths:
    result = json.loads(path.read_text())
    agents = result.get("agent_results", [])
    assert agents and all(
        isinstance(a.get("score_check"), dict)
        and a["score_check"].get("ok") is True
        for a in agents
    ), path
    perf = result.get("aggregate", {}).get("answer_perf")
    assert isinstance(perf, (int, float)) and not isinstance(perf, bool) and math.isfinite(perf), path
    state = result.get("shared_state")
    if path.parent.name == "poolact":
        assert isinstance(state, dict), path
    if state is not None:
        assert isinstance(state, dict), path
        graph = state.get("graph")
        if graph is not None:
            assert isinstance(graph, dict), path
            assert type(graph.get("pending_claims")) is int and graph["pending_claims"] == 0, path
        if path.parent.name == "poolact":
            assert graph is not None, path
print(f"validated {len(paths)} PoolAct strategy results")
PY
```

This is only a structural spot-check, not independent re-scoring. Also require the expected per-agent files, `summary.json`, configuration/source/data/dependency hashes, and the planned count. Run the identical command with `--resume` and a no-model-call guard when auditing a supposedly complete run: compatible results should skip after re-scoring, without changing trace or dump bytes. Changed source/configuration/data/schema/scores intentionally invalidate resume; do not silently spend more model calls during an integrity-only audit. Historical readable traces that lack exact scoring inputs cannot be promoted to re-score-verified results.

## Native tools and self-serving acceptance

Inspect the intended model's real template/parser, not only an HTTP health response. A small multi-turn native smoke should obtain information through a tool and demonstrate that the next request preserves the provider's assistant/tool history. Send real schemas for normal `auto` decisions; forced final uses `none` with schemas retained. `--tool-protocol auto` selects native for compatible real clients, while the repository fake backend resolves to text.

Check the complete request from each changed task/runner path, not just its system prompt or a synthetic nonce context. Task-owned Action examples in user messages must agree with the resolved protocol; questions, document segments, and other data may legitimately contain those same words and must not be globally stripped. Distinguish artifact integrity, prompt compatibility, observed native path coverage, and task score in the smoke report. A normal early answer can leave a path unobserved; retain it without automatically resampling for coverage.

The official demo, sweep, and PoolAct runners share protocol-aware task-context construction. Direct library callers should call `resolve_tool_protocol(llm, requested)` from `expgym.tool_protocol`, pass that resolved value to the selected task's `build_context(..., tool_protocol=protocol)`, and use it for `run_react_loop(..., tool_protocol=protocol)`. Builders default to historical text output; the loop does not rewrite arbitrary caller-supplied context, and custom hooks without a protocol argument remain caller-owned.

Use `EXPGYM_API_DUMP_DIR` and a distinct run ID/output directory. Count every transport attempt, record whether token usage is known, and retain delivered malformed decisions and length stops. Do not require nonempty visible `content` for a successful API delivery: a tool-only response is legitimate.

Capture actual device inventory, environment/package and checkpoint identities, effective generation settings, and seed-control observations. Keep model semantics unchanged when selecting attention backends. Seed values without effective sampling control are run labels, not proven repeatability; a separately registered stochastic study remains possible. Never substitute a desired performance trend for implementation acceptance.

## Common failures

| Symptom | Interpretation and action |
|---|---|
| Fake checks pass, real calls fail | Backend/model/auth/response compatibility remains untested. Run exact-model real smoke. |
| HTTP 200 but assistant content is null/empty | Inspect native tool calls, reasoning and finish reason. Tool-only delivery can be valid. A delivered empty/length/model-protocol failure is retained, not freely HTTP-resampled; ambiguous malformed envelopes fail explicitly. |
| 429/5xx/timeout | Retry is expected within configured bounds; reduce concurrency only if the provider is saturated. |
| `upstream_400_codex_plan_gated_model` | Subscription lacks that exact model. Test an available model or change account; endpoint health is not enough. |
| Search score is zero | Inspect trace and `score_check`; the model may simply be wrong. |
| NASBench-101 score is zero | The proposed DAG/config may be invalid. Confirm evaluator integrity before diagnosing infrastructure. |
| ParamNet import/version failure | Use the pinned legacy runtime (Docker wrapper when available, or an independently validated equivalent); do not substitute incompatible host dependencies. |
| Docker cannot reach local Sub2API | Use the wrapper and `host.docker.internal`; confirm daemon and local service are running. |
| Resume reruns an existing path | Source/config/schema/score fingerprint changed or output is incomplete; inspect manifest rather than forcing a skip. |
| Short visible trace consumes surprising quota | Count hidden reasoning/completion tokens and retried attempts from provider usage; pilot-measure instead of estimating from printed text. |
| `pending_claims` is nonzero | PoolAct result is incomplete/invalid; inspect exception cleanup and claim lifecycle. |

## Cost and capacity estimation

Before a large run:

1. Compute planned sequential traces and PoolAct agent traces from the resolved matrix.
2. Execute representative real pilots for each model, scenario, regime, and strategy class that materially changes behavior.
3. Read charged usage/call counts from Sub2API or provider records, including retries and hidden reasoning tokens.
4. Use median and high-percentile charged usage, not only the shortest trace.
5. Multiply by the exact matrix and add a retry/variance margin. Keep separate estimates for ExpGym, PoolAct main table, and repository PoolAct superset.

For self-serving, additionally measure loading/compilation, tokens and wall time by task/regime/strategy, effective concurrency and allocated GPU-hours. Simulated feedback seconds are not GPU wall time. Do not extrapolate from earlier runs that ended prematurely because of protocol bugs. Independent outer pools are repetitions; agents inside one coordinated pool and Audit hypothesis orders are not independent task samples.

Subscription units are provider policy, not an intrinsic trace property. Do not convert traces to subscriptions without observed account-specific depletion data.
