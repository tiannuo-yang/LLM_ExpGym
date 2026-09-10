# Self-serving: four nodes, two TP16 replicas per model

This is a **Static/fake validation**-tested deployment template. It has not had a
new GPU launch or real smoke. The default in
[`configs/serving/slurm_tp16.json`](../configs/serving/slurm_tp16.json) is one
exclusive `k2p` allocation per model: **4 nodes × 8 GPUs = 32 GPUs**, split into
two independent **2-node TP16** servers. Different models use separate exclusive
allocations, not overlapping node subsets. This changes total replica count from
the previous four-replica, 8-node/model study; it does **not** promise equal
throughput or that every GPU will remain fully occupied.

The deployment template is deliberately small: one planner/launcher, no automatic
checkpoint downloader, environment updater, model probe, router, retrying job
resubmitter or experimental scorer. Frozen historical deployments are unchanged.

## Prepare and inspect, without allocating GPUs

Prepare the model-compatible SGLang environment separately (for example with
`uv`), pin its package/source versions, and pass its absolute `sglang` executable.
Do not upgrade the runtime of an active study. Check the chosen runtime's own
`sglang serve --help` and model support before submission. The command shape and
core flags below come from the locally exercised SGLang launches, not a promise
that every SGLang version or checkpoint supports them.

```bash
python scripts/serve_slurm.py \
  --checkpoint /absolute/checkpoints/model-x \
  --sglang-bin /absolute/frozen-runtime/bin/sglang \
  --model model-x \
  --context-length 131072 --mem-fraction-static 0.84 --ep-size 1 \
  --output-dir /absolute/shared/serving/model-x-plan-v1 \
  --dry-run
```

The numeric model-capacity options above are **illustrations**, not model
recommendations. Context length, memory fraction and expert parallelism must be
chosen explicitly for the checkpoint/hardware. The script never guesses these
from a model name. Optional `--reasoning-parser`, `--tool-call-parser` and
`--trust-remote-code` must also be chosen explicitly. It imports neither SGLang
nor Torch, opens no checkpoint files, and calls no Slurm/model/HTTP commands in
the default planning path. Omit `--output-dir` to print JSON only. A supplied
output directory must be fresh; it receives `plan.json`, `serve.sbatch` and a
snapshot of the launcher.

`--server-args-json` accepts only the reviewed backend knobs
`--attention-backend`, `--moe-runner-backend`, `--sampling-backend`,
`--quantization`, `--random-seed`, `--enable-deterministic-inference`,
`--enable-symm-mem`, `--dist-timeout`, `--linear-attn-prefill-backend`,
`--linear-attn-decode-backend`, `--mamba-full-memory-ratio`,
`--mamba-ssm-dtype`, `--max-prefill-tokens` and `--page-size`. For example:

```text
--server-args-json '["--attention-backend", "fa3", "--random-seed", "42"]'
```

These are opt-in architecture/runtime choices, not common defaults. Unsupported
backend flags must be reviewed and added explicitly. Topology overrides, API
secrets and generation defaults cannot be smuggled through this field. An
explicit server initialization seed is shared by the two replicas; it is not a
proof of request-seed control or statistically independent repetitions. If a
study requires different initialization seeds per replica, that is a separate
configuration change to implement and validate before the study.

The additional pipeline/linear-attention knobs were reviewed against the
[SGLang Qwen3.8 cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8).
They are accepted as explicit values for any served model, not automatically
enabled by its name or by the pipeline profile. Acceptance by this planner is
not proof that the selected SGLang version/hardware supports a value.

If shared-library setup is required, pass `--runtime-env /absolute/runtime.sh`.
This script must contain only nonsecret runtime setup, not credential values.
It is sourced on each rank; rank-specific compilation/module cache locations are
then set under `/tmp/expgym_JOB_replicaR_rankK_*`. These are serving caches, not
PoolAct observations. Record and freeze the runtime setup/checkpoint identity
with the study; copying the launcher does not snapshot the external runtime.

For the cluster's Pyxis runtime, the previously exercised optional flags are
`--container-image /absolute/image.sqsh` and repeatable `--container-mount
SOURCE:DEST[:ro]`. Mount the checkpoint, runtime, runtime setup and any required
external interpreter/shared-library paths explicitly. Paths used inside the
container must exist there. No cluster-specific image path is hardcoded.

## Explicit submission and lifecycle

Only `--submit` invokes `sbatch`. Run the same reviewed arguments with a **new**
output directory, replacing `--dry-run` with:

```text
--submit --allow-private-unauthenticated
```

The second flag acknowledges that the direct HTTP endpoints have **no API
authentication** and must be restricted to a trusted private cluster network by
the operator. Do not expose them publicly. Use a separately reviewed
authenticated gateway when this network assumption is false; this launcher does
not install a gateway or handle secrets.

The batch requests `--account=k2p --nodes=4 --gres=gpu:8 --exclusive` and one
32-CPU task per node, using the configurable `higherprio` partition and a
three-day limit by default. It does not select busy nodes or cancel other jobs.
The allocation controller requires four distinct nodes and the correct account.
Nodes 0/1 form replica 0; nodes 2/3 form replica 1. Each rank uses all eight GPUs
on its node, `--tp-size 16 --nnodes 2 --node-rank 0/1`, and a replica-specific
distributed rendezvous endpoint. HTTP ports are 31240/31241; distributed ports
are 51240/51241. Port ranges are configurable and overlapping ranges are rejected.

`deployment.json` records the allocated nodes, two `/v1` endpoints, exact rank
commands and plan hash. **Its existence means launching, not ready.** No health
or model request is made automatically. Keep the actual checkpoint/runtime
identity, hardware inventory and authorized smoke evidence with the experiment.
A rank exiting ends this serving allocation and stops only its other owned
ranks; there is no silent retry. `launcher_exit.json` explicitly does not claim
that server requests drained. Before a planned `scancel JOB_ID`, stop new
experiment dispatch and verify in-flight clients have completed. A forced stop
is infrastructure failure evidence, not a reason to silently replace results.

## Explicit single-replica TP8 × PP4 profile

Keep the default schema-1 config unchanged for two TP16 replicas. To explicitly
use the same **4 nodes × 8 GPUs** as one tensor/pipeline-parallel server, add:

```text
--config configs/serving/slurm_tp8_pp4.json
```

This schema-2 profile records `replicas=1`, `nodes_per_replica=4`, `tp_size=8`
and `pp_size=4`. Validation requires **TP × PP = GPUs per replica**, the replica
node total to match the allocation, and EP to divide the actual TP (so EP16 is
invalid here). Schema 1 accepts only the existing two-TP16 layout; schema 2 adds
only this reviewed single-TP8×PP4 layout, not arbitrary untested shapes. Neither
configuration is selected from a model name.

All four allocated nodes belong to replica 0, with node ranks 0/1/2/3,
`--tp-size 8 --pp-size 4 --nnodes 4`, and one shared head-node rendezvous.
`deployment.json` contains **one** HTTP endpoint on node 0; other ranks are not
independent replicas. Port validation uses the configured replica count. No
topology override, including `--pp-size`, can enter through extra server args.
Saved plans are revalidated before allocation commands execute, so editing their
fields cannot bypass the same argument checks. The launcher still cleans up
only its owned rank processes and never submits or retries by default.

Existing schema-1 plan/layout/rank commands/batch text remain unchanged (the
launcher source/hash necessarily changes). Pipeline loading, backend support,
capacity and throughput require a model/runtime-specific authorized smoke; this
generic profile is CPU/mock-tested, not a memory-fit or performance guarantee.

## Connect the dynamic experiment queue

After an authorized native multi-turn/tool/forced-final smoke through **every**
replica (two by default, one in the explicit pipeline profile), supply
`deployment.json` to the queue planner:

```bash
python scripts/run_study_queue.py plan \
  --matrix /absolute/study/matrix.json --study-id study-v1 \
  --output-root /absolute/shared/runs/study-v1 \
  --output /absolute/study/queue-plan.json \
  --endpoint-file /absolute/shared/serving/model-x-run-v1/deployment.json

python scripts/run_study_queue.py run \
  --plan /absolute/study/queue-plan.json --sha256 RECORDED_PLAN_SHA256 --resume
```

The queue's configured default is **8 concurrent invocations**, not eight agents
or eight model requests. A PoolAct invocation contains its own N-agent pool.
Completed slots are refilled across the whole queue, rather than waiting for a
whole repeat/scenario batch. The next invocation goes to the endpoint with the
fewest active invocations and stays on that endpoint for its whole conversation
or PoolAct pool; the actual endpoint is recorded. Multi-model stages can provide
their own `endpoints` lists. The queue does not implement HTTP-level failover or
switch a live conversation between replicas. Endpoint assignment balances active
invocation counts, not measured tokens/second or GPU utilization.

Keep per-request `max_tokens`, temperature, top-p/top-k, thinking settings,
protocol, horizon, scenario budget and scoring policy in the **experiment**
configuration unchanged when changing serving topology. Start at the default
8-invocation limit, measure each replica's active requests, GPU memory/utilization,
queue delay, prompt/output/reasoning token lengths and errors, then choose a
recorded concurrency limit. The per-server settings of 64 running requests and
CUDA graph batch size 64 preserve the previously exercised launch options; they
are ceilings, not evidence that 64 simultaneous requests fit every checkpoint.
Do not reduce reasoning/output lengths or select shorter/easier tasks merely to
make utilization or elapsed time look better.

## CPU acceptance

```bash
python -m unittest discover -s tests -p test_serving_plan.py -v
```

Tests cover 4×8 / 2×TP16 byte-compatible defaults and explicit 1×TP8×PP4 rank
mapping, single/shared versus distinct endpoints, no default
submission, fresh output protection, explicit submission acknowledgement,
backend/topology override and saved-plan tamper rejection, preserved generation settings and owned
rank cleanup on failure. Slurm and processes are mocked. New hardware/runtime
loading, throughput, native parsing and task results remain **unverified** until
an explicitly authorized real smoke and subsequent study.
