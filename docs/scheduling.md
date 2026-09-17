# Dynamic study queue

`scripts/run_study_queue.py` is the production entry point for a new concurrent
study. It expands the existing ExpGym/PoolAct runner selectors into independent
invocations, then uses one bounded queue with `FIRST_COMPLETED` replenishment.
Stage labels describe the matrix; they are **not barriers**. An unfinished HPO
repeat does not prevent a later Search/Audit/strategy/repeat invocation starting
when a slot becomes free. A PoolAct pool remains one invocation; its agents and
reasoning lock are not split across processes or replicas.

This is a **Custom study** or **Static/fake validation**, depending on the matrix.
Concurrency does not make a matrix paper-exact or seed labels statistically
independent. Existing `run_full.sh` stays available as the older sequential
Docker/setup convenience wrapper; it does not silently switch scheduling policy.

## Freeze and run

Use the same runner options as an ordinary invocation. Matrix files contain an
ordered `stages` list; one stage may expand to many independently queued jobs:

```json
{
  "stages": [
    {
      "label": "expgym-tuning",
      "runner": "expgym",
      "args": ["--backend", "fake", "--models", "fake", "--scenarios", "tuning",
               "--tuning-reps", "3", "--cost-regimes", "cost_free,cost_moderate,cost_tight"]
    },
    {
      "label": "poolact-tuning",
      "runner": "poolact",
      "args": ["--backend", "fake", "--model", "fake", "--scenario", "tuning",
               "--strategies", "naive,cached,poolact", "--agents", "4", "--repeats", "3"]
    }
  ]
}
```

This data-free fake example expands to 18 invocations. Supply Search/Audit
selectors and the intended real backend/generation controls explicitly for a
registered real study. Use HPO/NAS R3 and Search/Audit R1 as appropriate to the
registration; ExpGym Audit `--audit-reps 3` represents its three specified
hypothesis orders, not three independent document samples. PoolAct Audit stays
one repeat unless separately planned. No question selection or repetition is
increased based on observed performance.

```bash
python scripts/run_study_queue.py plan \
  --matrix matrix.json --study-id study-unique-v1 \
  --output-root runs/study-unique-v1 --output queue-plan.json

# Copy the exact SHA256 printed by plan; no model call occurs during planning.
python scripts/run_study_queue.py run \
  --plan queue-plan.json --sha256 PLAN_SHA256 --workers 8

# Continue the same immutable plan/output: verify completed jobs, start unbegun jobs.
python scripts/run_study_queue.py run \
  --plan queue-plan.json --sha256 PLAN_SHA256 --workers 8 --resume
```

Planning freezes resolved defaults, actual job selectors, the source-tree hash,
interpreter path, namespace and output paths. `--api-key` literals are rejected;
credentials must come from the backend's environment or `--api-key-file`.
Endpoint URLs must not embed credentials or query strings. Runner `--resume`,
`--dry-run` and external terminal-evidence paths are queue-owned and rejected in
stage arguments. Stage `--output-dir` is replaced by the unique job directory;
the plan's `output_root` is authoritative. The plan is create-only and should be
retained with its independently recorded hash before model execution.

Each stage may supply `"python": "/absolute/verified/runtime/bin/python"`.
The executable path retains a virtualenv symlink identity; runtime version and
executable are recorded by each worker. The queue never installs a runtime or
builds Docker. ParamNet still requires the verified legacy environment: run the
queue in a compatible prebuilt environment or provide its accessible interpreter.
Do not run native ParamNet under an incompatible host Python. Data preparation
and exact-model native multi-turn smoke remain prerequisites, not queue features.

## Two TP16 replicas

The default serving configuration is
[`configs/serving/slurm_tp16.json`](../configs/serving/slurm_tp16.json): four
8-GPU nodes per model, two TP16 replicas. Its `dispatch.max_workers` defaults to
8 **independent invocations**, not 8 API requests or a guaranteed GPU saturation
setting. PoolAct naive/cached can issue up to N requests per active pool, whereas
PoolAct's reasoning lock serializes its own decision section. Tune the bound from
an authorized pilot's latency/throughput/memory measurements.

Supply the two ready, already smoke-tested endpoints when freezing the plan:

```bash
python scripts/run_study_queue.py plan \
  --matrix matrix.json --study-id real-study-v1 \
  --output-root runs/real-study-v1 --output queue-plan.json \
  --endpoint-file deployment.json
```

`deployment.json` supplies `endpoints: ["http://head0:31240/v1", ...]`. A stage
can override `endpoints` for its own model; never send one model's jobs to a
different model's replica. At each admission the least-loaded endpoint by active
invocation count is selected. The next job can fill a freed replica while a slow
job continues elsewhere. The chosen URL is persisted and remains fixed for all
turns, agents, tool calls and client transport retries of that invocation. Resume
verification uses that same URL as configuration identity, without calling it.
This is invocation balancing, not token-length-aware routing or automatic server
failover. The worker limit is global to one queue; run one queue per model when
each model should receive its own configured limit.

## Isolation and preserved algorithm

| State | Isolation / evidence |
|---|---|
| Python globals and `random.seed` | One OS subprocess per ExpGym job / PoolAct pool; no thread changes to parent `os.environ` or cwd. ExpGym's process-global seeding cannot reseed another invocation. |
| Coordinator, graph, observation cache | `run_poolact._run_strategy` creates fresh objects for each strategy invocation; no cross-item/strategy/repeat sharing. |
| Agent clocks and pending claims | Separate runtime/clock per agent; the pool's existing reasoning lock, tool concurrency, completion-time visibility and cleanup are unchanged. |
| Repeat identity | Original `repeats`, `base_seed`, `repeat_index` and `seed + repeat_index*N + agent_id` are retained. A pool is never enlarged to N×R. |
| Outputs and API dumps | SHA256-derived job ID owns one directory, result tree, raw dump tree, run ID and worker receipt. Separate strategies cannot race on `summary.json`. |
| Prompt-cache routing | Study/job namespace plus full PoolAct invocation identity and per-agent derivation. Previous PoolAct keys omitted model/item/seed; that generic routing collision is fixed. |
| Task loaders / evaluator state | Separate process per invocation; within a pool, immutable loader caches and existing locked HPO operations remain unchanged. Selected data/dependency fingerprints are checked by original runners. |

Prompt-cache keys are advisory provider routing fields. A provider may ignore
them; this does **not** prove physical KV-cache separation, independent random
sampling, or absence of training contamination. The earlier key collision is
not evidence that historical observation caches or answers were contaminated.
Fake has no server/cache payload and explicitly disables ExpGym's effective API
cache field while retaining unique queue identity.

Use `--prompt-cache-key-field cache_salt` explicitly for compatible SGLang
servers. The default `prompt_cache_key` preserves the original API payload;
the client sends only the selected field, and only when a namespace is enabled.
This option changes neither the existing namespace derivation nor task caches,
prompts, seeds or scoring. It is recorded in client configuration, traces and
resume/queue identities, so changing it requires a new accepted plan. No model
name inference or automatic fallback is used. In SGLang 0.5.17, `cache_salt`
feeds the prefix-cache `extra_key`; `prompt_cache_key` is not a recognized chat
request field. Check the actual provider version and execution path before
claiming prefix-cache separation; a field alone does not prove physical GPU
memory isolation or sampling independence.
For SGLang 0.5.17 this isolation claim is limited to the verified Python radix /
Unified paths: the experimental C++ radix wrapper drops `extra_key`. Exclude
`SGLANG_EXPERIMENTAL_CPP_RADIX_TREE=1` and record the actual cache backend.

## Completion, errors, and resume

Every session writes `events.jsonl` with queue/start/end timestamps, job IDs,
chosen endpoints, active counts and a final drain event; `summary.json` records
the maximum active workers, wall duration, all finished reports, stop reasons and
unstarted IDs. Start events mean local admission, not the first HTTP token.
Worker stdout/stderr and per-job PID/runtime/configuration receipts are retained.
Artifacts are inventoried once at completion and rechecked when explicitly
resuming, not repeatedly during monitoring.

Exit 0 alone is insufficient: the worker invokes the original runner's exact
resume validator, including configuration, source/data/dependency identity,
per-agent outputs, scoring and PoolAct summary consistency. Only then does the
controller save a completion receipt covering the full owned output tree.
Normal task abstentions, length-limited delivered decisions, zero/negative scores
and valid wrong answers remain completed data under the selected missing-final
policy; the scheduler never tests score sign or visible answer length.

A nonzero exit, transport error escaping the registered client retry policy,
artifact mismatch or stale identity stops **new admissions**. All already-started
subprocesses drain naturally. No failed attempt is automatically rerun; incomplete
started jobs require explicit recovery planning/new identity, preserving their
old outputs and raw attempts. An external `--stop-file` or admission
`--max-wall-seconds` also stops new work and drains; it is not a hard kill timeout.
Ctrl-C during waiting follows stop-new/drain; child process sessions are separate.
A machine crash/SIGKILL cannot guarantee draining, so a begun-but-incomplete
receipt blocks implicit resampling after restart. Provider-side quiescence is
not claimed by local process completion.

Resume requires the exact frozen queue definition. For **already completed jobs**,
it checks complete artifact hashes and launches **verification-only** subprocesses
using the original validators. Those checks may load/recompute selected evaluator
data, but make no HTTP/model calls. **Never-started jobs still run for the first
time and can make model calls.** Started-but-incomplete jobs require explicit
recovery; invalid existing results cannot fall through to model generation.
`run --resume` is therefore a continuation command, not an integrity-only command
for a partially completed plan. This version has no top-level verify-only mode;
do not use resume for a no-model-call audit unless every planned job is already
complete and the complete scope has first been checked.
Changing concurrency alone is allowed; changing source, matrix, paths, endpoints,
or generation protocol requires a new study identity. Keep inputs immutable;
the checks are not an atomic adversarial filesystem snapshot. One advisory
controller lock prevents two cooperating queues from owning the same state.

## Static/fake acceptance

```bash
python -B -m unittest tests.test_study_queue tests.test_poolact_cache_namespace
```

Tests use subprocess fakes and the actual runners' built-in fake tuning task;
they cover a later stage starting before a slow earlier job ends, concurrency
bounds, no duplicate/lost IDs, endpoint replenishment, failure/drain, missing
answers as data, exact resume/tamper rejection, independent process/dump/cache
namespaces and two repeats of all three PoolAct strategies. These tests make no
API calls, allocate no GPUs and do not validate real-provider throughput.
