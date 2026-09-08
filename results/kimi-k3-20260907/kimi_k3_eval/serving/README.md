# Kimi-K3 evaluation serving

Final status: the evaluation and all acceptance checks completed, and owned job
`1203299` was intentionally cancelled at 2026-09-07 11:57:35 UTC to release the
eight nodes. Its accounting End is 11:57:36; queue absence and `CANCELLED` state
were confirmed at 11:59:32 after asynchronous cleanup. This is normal
post-evaluation release, not a benchmark failure. The recorded API endpoint is
therefore historical, not a currently running service. Final accounting is
202.6844 allocated GPU-hours for this service and 218.7022 including bootstrap
job `1203298`; see [accounting](reports/final_accounting_20260907_after_cleanup/slurm_receipt.json)
and [release confirmation](reports/final_accounting_20260907_after_cleanup/release_confirmation.json).
No unrelated job was cancelled, and all weights, results, dumps and scripts remain.

Serving acceptance passed on 2026-09-07: all four replicas answered normally,
all seven short API probes completed, the 100,174-token retrieval probe passed
in 33.622 seconds, and all 340 padding regression tests passed. See
`ACCEPTANCE.json` and `runs/1203299/smoke/` for the structured summary and raw data.

This directory owns only the new ExpGym/PoolAct serving deployment. Existing
Tau_vision jobs and files are never modified.

The deployment uses eight Slurm nodes (`-A k2p`, `higherprio`, eight H200 GPUs per
node), organized as four independent two-node TP16/EP16 replicas. K3 has 96
attention and KDA heads, so plain TP64 is not a valid eight-node configuration.

The final independent `uv` environment is `independent/.venv` with Python
3.12.13 and **no inherited system or user Python packages**. Its 311 packages
reproduce the verified CUDA 12.9 stack: 304 version-pinned public distributions
and seven image-specific distributions repacked into auditable wheels. The
SGLang wheel was then updated to `0.5.16+pr32477` using the exact upstream
reserved-KV-padding repair. All 340 upstream CUDA regression tests passed.

The immutable image
`/lustrefs/users/chufan.shi/codex_space/Tau_vision/.images/sglang_k3_cu12.sqsh`
provides the OS and CUDA 12.9 toolchain/runtime. Python packages all come from the
new uv environment. This preserves compatibility with the cluster's r570
driver while avoiding CUDA 13 wheels. Source, package versions, launch settings,
logs, job IDs, and smoke responses are retained here for audit.

Deployment records:

- Bootstrap job: `1203298`, started 2026-09-07 08:32 UTC on nodes 267–274.
- Bootstrap job used a uv overlay for initial compatibility checks and was
  cancelled before any formal evaluation to release all eight nodes.
- Final job: `1203299`, started 2026-09-07 08:47:36 UTC on nodes 267–274.
- Final router: `http://azure-uk-hpc-H200-instance-267:30141/v1`.
- `deployment.json` always identifies the current owned job and endpoints;
  `runs/<job-id>/deployment.json` preserves each deployment independently.
- `runs/<job-id>/replica<i>-rank<j>.log` preserves each distributed server log.
- `smoke.py` saves exact API requests and responses, response headers, elapsed
  time, finish reason, and presence of content/reasoning for all four replicas.

The checkpoint README states that K3 always thinks and requires preserved
`reasoning_content` and `tool_calls` in multi-turn history. The tokenizer has a
low-level `thinking=False` argument, but this is not the documented trained
usage. Smoke tests compare the default behavior with `thinking=False` and
`enable_thinking=False`; the latter is not the K3 tokenizer parameter.
The server's native request default remains thinking enabled;
`reasoning_effort` supports `low`, `high`, and `max` (default `max`). The actual
ExpGym/PoolAct benchmark requests explicitly send
`chat_template_kwargs={"thinking": false}` to follow the paper's non-thinking
setting. This per-request benchmark choice differs from K3's recommended
always-thinking trained usage and is a documented experimental deviation.
It does not change the server's native default.

The single arithmetic `thinking=False` probe returned normal content without
a reasoning field, whereas `enable_thinking=False` left reasoning enabled.
This is not a hard non-thinking guarantee: in the completed benchmark smoke,
6/136 requests with `thinking=false` returned nonempty server-parsed
`reasoning_content` (21,707 characters). All reported zero reasoning tokens,
but that counter is disabled by the request flag and does not measure those
parsed fields. Saved HTTP JSON cannot distinguish explicit think-open emission
from orphan think-close parser misclassification. No grammar or custom logit
constraint was applied. See the [offline diagnostic](REASONING_MODE_DIAGNOSTIC.md)
and [hashed JSON evidence](REASONING_MODE_DIAGNOSTIC.json).
The native `low` replica probes took about 1.54 seconds each; these arithmetic
probes are functional checks, not estimates of benchmark throughput.

Reproducibility and validation:

- `independent/README.md` describes environment reconstruction and initial
  isolation/import verification.
- `build_patched_sglang.py` deterministically builds the final SGLang wheel from
  the baseline wheel plus audited upstream files; the output hash is
  `f5a0269e1362391f0852d27e67bc7b3acd04282336b6de7050a73c62e2187708`.
- `manifests/padding-tests-passed.json` and `padding-tests.xml` record the
  340-pass GPU regression gate; `logs/padding-kernel-tests.log` is the raw log.
- `patches/README.md` documents the repair and its limits: compressed MLA/KDA
  paths are not covered by this generic store-cache fix.
- `long_context_probe.py` verifies an actual prompt of at least 90,000 tokens,
  retrieval of a passcode at the beginning, normal completion, and absence of
  `[PAD]` corruption, saving the complete request and response.
- The [v3 output sanity snapshot](reports/v3_output_sanity_snapshot/README.md)
  checks 1,339 completed smoke/pilot response choices for the exact configured
  `[PAD]` token, separate media padding placeholder, and empty content. It
  retains response-level IDs/context/hashes and a read-only scanner to repeat
  on full_v3 after completion. No marker matches does not rule out all cache
  or other output errors.

Submit only after environment and kernel gates exist:

```bash
sbatch kimi_k3_eval/serving/serve_8nodes.sbatch
python3 kimi_k3_eval/serving/smoke.py
python3 kimi_k3_eval/serving/long_context_probe.py
```

Do not submit a second eight-node deployment while an owned one remains active.
The batch script's cleanup trap terminates only its own launched processes.

The live router health-checks all replicas at a five-second interval after each
round completes. In this SGLang version, `/health` generates a special one-token
request while a replica is idle; when the replica is busy that request is
ignored, and health requests do not contribute to request metrics. This fixed
background configuration is retained across pilot and full evaluation. The
router is supervised by the batch job, so replacing it independently would
terminate the deployment; no router restart is performed during evaluation.

Cache accounting has two distinct layers. The study's
`prompt_cache=disabled` / `--prompt-cache-scope disabled` disables the
runner's explicit prompt-cache key, not the serving engine's automatic prefix
cache. All four retained rank-0 startup argument records show
`disable_radix_cache=False` and `enable_hierarchical_cache=False`; these
settings are unchanged across smoke, pilot, and full. The API does not report
cached-input usage for these runs, so cache-hit rates and complete cache-token
totals remain unknown rather than zero. Logical prompt-token counts are not
measurements of uncached prefill work.
