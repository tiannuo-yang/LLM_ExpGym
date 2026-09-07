# ExpGym and PoolAct runbook

Run all commands from the `LLM_ExpGym` repository root. Inspect each script's `--help` because CLI options may evolve.

## Setup and no-cost validation

```bash
bash scripts/setup.sh --with-data
bash scripts/check.sh
.venv/bin/python scripts/download_data.py --check
```

`scripts/check.sh` compiles Python, syntax-checks shell, runs the unit/integration suite, then executes fake ExpGym and all three fake PoolAct strategies. HPO native skips are expected when legacy dependencies are absent. A passing fake check does not prove real provider compatibility.

Dataset setup can transiently use roughly 3.2 GiB and retains roughly 215 MiB of HPO data. Downloads are checksum-verified and atomically installed.

## Load local Sub2API without exposing secrets

Use a user-provided env file. If none is given, locate `.sub2api-client.env` in the adjacent Sub2API deployment. Source it; never display it:

```bash
set -a
source /path/to/sub2api/.sub2api-client.env
set +a
test -n "${SUB2API_API_KEY:-}" && test -n "${SUB2API_BASE_URL:-}"
```

Do not run `env`, `set`, `printenv`, shell tracing, or commands that print the key. A locally tested stable model is `gpt-5.3-codex-spark`, but availability is account-specific. Exact-model preflight is mandatory; `gpt-5.4` has returned `upstream_400_codex_plan_gated_model` on one local subscription.

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

For a complete path smoke, repeat the sequential command for `tuning`, `restricted_search`, and `evidence_audit` under all three regimes. Repeat PoolAct for all three scenarios under Tight and Moderate, the regimes used by the main PoolAct table. Use a compact NASBench task for the tuning smoke.

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
    assert isinstance(perf, (int, float)) and math.isfinite(perf), path
    state = result.get("shared_state")
    if state is not None:
        assert state.get("pending_claims", 0) == 0, path
print(f"validated {len(paths)} PoolAct strategy results")
PY
```

Also require the expected per-agent files, `summary.json`, configuration/source hashes, and the planned count. Run the identical command again with `--resume`; compatible complete results should skip. If changed source, configuration, schema, or scores cause reruns, that is intentional.

## Common failures

| Symptom | Interpretation and action |
|---|---|
| Fake checks pass, real calls fail | Backend/model/auth/response compatibility remains untested. Run exact-model real smoke. |
| HTTP 200 but assistant content is null/empty | Transient malformed success; rely on bounded retry and inspect attempts. Do not write an empty trace as success. |
| 429/5xx/timeout | Retry is expected within configured bounds; reduce concurrency only if the provider is saturated. |
| `upstream_400_codex_plan_gated_model` | Subscription lacks that exact model. Test an available model or change account; endpoint health is not enough. |
| Search score is zero | Inspect trace and `score_check`; the model may simply be wrong. |
| NASBench-101 score is zero | The proposed DAG/config may be invalid. Confirm evaluator integrity before diagnosing infrastructure. |
| ParamNet import/version failure | Use the pinned Docker wrapper, not the host Python environment. |
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

Subscription units are provider policy, not an intrinsic trace property. Do not convert traces to subscriptions without observed account-specific depletion data.
