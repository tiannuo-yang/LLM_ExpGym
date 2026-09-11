# DeepSeek Flash isolated serving runtime

This is an independent uv environment. Qwen's active runtime and all older
environments are read-only references, never modified by this build.

## Version and compatibility choices

- CPython 3.12.13 from the existing standalone interpreter, used read-only.
- Official SGLang 0.5.17, base source `29481685462732237d80d86076d6563e1f658102`.
- Torch 2.11.0 + cu129, torchaudio 2.11.0, torchvision 0.26.0. CUDA 12 is deliberate
  for the cluster's NVIDIA driver 570.133.20. Other exact dependencies are in
  `uv.lock`; selected CUDA-12 overrides follow the previously verified official
  SGLang CUDA-12 route, not a change to the system driver or toolkit.
- Quack 0.6.1 / CUTLASS 4.6.0, Flash Attention 4.0.0b19, FlashInfer cu12
  0.6.15.post1, SGLang-kernel 0.4.5+cu129, DeepGEMM 0.1.5.post1+cu129.
- `uv sync --locked --link-mode copy --cache-dir ./uv-cache` creates an independent
  environment from this study's cache. No Qwen environment or cache is used as
  an installation target. An initial offline lock against the ordinary shared
  uv download cache failed because a wheel was absent; the subsequent online
  lock used the new runtime-local cache and resolved 206 packages.

## Official DeepSeek-V4 effort compatibility backport

The downloaded checkpoint is `DeepSeek-V4-Flash-0731`. Its official encoder has
`low`, `high` and `max` effort profiles. The unmodified 0.5.17 encoder implements
the older preview mapping: its `max` renders the prompt that 0731 calls `high`.
An accepted request field alone therefore does not establish maximum thinking.

Use the exact upstream fix
[`059269594c5f245f77dad711631843c299d7713f`](https://github.com/sgl-project/sglang/commit/059269594c5f245f77dad711631843c299d7713f)
(PR #33140). `sglang-dsv4-official-0592695.patch` contains its three functional
runtime files and no invented model-name branch: `chat_encoding.py`,
`encoding_dsv4.py`, and `serving_chat.py`, 13 original upstream hunks. The remaining
upstream changes are documentation, an environment-variable help comment and tests.
The runtime detects the checkpoint encoder's official profile using a bounded
AST inspection; it does not execute arbitrary checkpoint Python to select it.
All original files and original/patched hashes are retained before application.

SGLang 0.5.18 already contains the fix but also upgrades the GPU stack to Torch
2.13 / FlashInfer 0.6.17 / kernel 0.4.6.post1. Backporting the exact compatible
three-file upstream change avoids that unrelated hardware dependency change.
Do not replace the whole module with the checkpoint's standalone encoder:
SGLang's stricter dict/JSON tool-argument normalization and task helper are needed.
No sampler, attention, MoE kernel or model tensor loading logic is patched.

Requests explicitly use `reasoning_effort=max`, `chat_template_kwargs={"thinking":true}`,
T=1 and top_p=0.95; top_k is not sent. The actual encoded highest-effort prefix
must match the checkpoint's official `Beyond maximum` prefix in CPU checks and
native continuation replay. The study retains max_output=32768 for the shared
comparison budget; this is below the vendor's **384K** recommendation for high/max.

## Serving candidate and gates

Four exclusive H200 nodes, each running an independent TP8 / PP1 / EP1 server.
The default plain TP16 path is incompatible with this checkpoint's eight output
groups (`o_groups // attn_tp_size` would be zero); this is not a claim that every
possible DP/TP16 topology is impossible. No unnecessary DP/CP or pipeline mode is used.

The checkpoint uses FP4 experts alongside other tensor types. On H200, select
Marlin W4A16 MoE, dsv4 attention, page size 256, chunked prefill 4096, native context
1048576, static memory fraction .85, max_running_requests=64 and CUDA graph batch
ceiling=64. No speculative decoding: the target loader skips `mtp*` draft tensors.
No Qwen GDN/SSM settings or page-size=1 are inherited.
The native context differs from Qwen's 262144; the parent coordinator approved
preserving this model's native capacity rather than imposing a lower server cap.
ExpGym gains no new history pruning; PoolAct retains its existing approximate
131072-token local history limit. Actual KV capacity still requires GPU startup
and the authorized native/task smoke, not only theoretical memory estimates.

Parsers are exactly `deepseek-v4` (reasoning) and `deepseekv4` (tools). The dsv4
path retains tool definitions and full reasoning/tool history even on
`tool_choice=none`; this differs from the Qwen template and must be verified
on actual saved requests. `cache_salt` feeds `extra_key` in the Python Unified
FULL+SWA cache; the experimental C++ cache is excluded. These observations are
static source evidence until actual startup and native smoke complete.

`verify_cpu.py` is a non-GPU/non-API acceptance tool. Its output will bind the
actual package/model/encoding files and distinguish static checks from live
serving, JIT, sampling and scored-task smoke. Neither a successful import nor a
deployment JSON is a readiness claim.

Official references:

- [Model release and recommended settings](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731)
- [SGLang DeepSeek-V4 cookbook](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4)
- [CUDA-12 SGLang installation route](https://docs.sglang.io/docs/get-started/install)

## Completed CPU acceptance, 2026-09-11

- uv lock resolved 206 packages; sync installed 205 distributions in **10m35s**
  after **1m27s** package preparation. Tool `20009a` exited 0. The long install
  phase was observed copying Torch/TileLang header trees on Lustre, not model
  loading or GPU work.
- Exact upstream three-file backport applied via `apply_patch`; baseline files
  are retained under `upstream-original/`. Patched hashes match the independent
  exact-hunk reconstruction and are enforced by `verify_cpu.py`.
- Actual isolated-runtime CPU acceptance passed (tool `7bf65d`): **9/9 actual
  serving renderer** conversations / effort levels match the checkpoint's
  official encoder character-for-character and token-for-token; highest prefix,
  native model registry, typed DSML, reasoning/final separation and five cache
  salt checks passed. **0 API requests / no CUDA context / no weight loading**.
  The single `versions.json` records package and encoding/model identities.
- Six verifier helper fixtures passed; native-smoke client mock passed with two
  synthetic requests. `sglang serve --help` includes the chosen parsers, Marlin,
  page size and chunked-prefill flags. CPU no-CUDA warnings and optional unrelated
  model imports requiring vLLM are not GPU smoke results.
- `uv pip check` reports exactly the known deliberate metadata mismatch:
  SGLang requires cuda-python>=13.0 but the CUDA-12 route uses 12.9.7. This is not
  described as an unmodified or completely clean dependency graph.

| Runtime module | Original SHA256 | Patched SHA256 |
| --- | --- | --- |
| chat_encoding.py | 00fa7e93b0b6ad1f22c49b64326e0354dc39506a417e5d5fe672d341f35bf95d | 4cc93655ba72dabc45b40a23a107c76c2208cb7c5c612193f6832388fe2c624c |
| encoding_dsv4.py | 012e4dc254c4046f600674eaa799d59dffe5e4a46450da7b4629cf16706fc6c3 | 764dcfb28a57c3196975475747cb525ccacb4110556e3d9d35f038d6283ca527 |
| serving_chat.py | 0eea8dc3911bf3f1a51f8ebf5acaff2823b14325bb67fca32f7dacc174b7488a | c6b6d725b96e6a9fd924a39bf7702af0fbe1c657aa0678c0a48841e73b018603 |

Patch SHA256: `3ed229fbf6181aaeff82e1fb725901f60757482d35119f1a1a8f26d5e204899b`.
uv lock SHA256: `6a9df510ee8c578d5e3f8911a39e185c4ccfad07d58f2c7fe6252986fe73c859`.
Runtime environment SHA256: `561c407e172cce80bb78b75401834eb0fa516173d2787035f5bb4d4b97bf4afc`.

The user confirmed DeepSeek-V4-Flash-0731 on 2026-09-11. The first independent
GPU allocation is Slurm 1204605, started 03:46:08 UTC on nodes 222–225,
four single-node TP8 replicas. CPU identities above are unchanged. Actual
startup, native/task smoke, and any subsequent attempts are recorded in
`../PLAN.zh.md` and `../serving/`; the CPU checks alone are not serving acceptance.

Actual allocated-node JIT compiler is `/usr/local/cuda/bin/nvcc`, **12.8.93**,
distinct from Torch/cu129 runtime libraries. DeepGEMM emits its 12.9
best-performance recommendation. The installed binary's allowed branch and
[fixed release README](https://github.com/sgl-project/DeepGEMM/blob/fa3a5ca07d768dd0f9089f70a445208b166c48d1/README.md)
allow NVCC >=12.3 on SM90; this warning alone is not an incompatibility or
evidence of a quantified slowdown. The compiler was not replaced mid-startup.

Before any native/formal inference, startup 1204605 was deliberately stopped to
correct compilation-cache isolation. `runtime-env-isolated.sh` sources the
unchanged base above, then explicitly sets SGLANG_DG_CACHE_DIR / DG_JIT_CACHE_DIR,
TILELANG_CACHE_DIR / TILELANG_TMP_DIR, and CUDA_CACHE_PATH under this runtime's
cache directory. These libraries do not all honor XDG_CACHE_HOME. No shared
cache was deleted or copied. This changes cache location, not kernels, weights,
sampling, encoder or scoring; the original startup remains in the resource ledger.

Observed startup limitations: the optional custom all-reduce JIT fails at the
C++/TVM-FFI tuple `get` call, so both starts use the supported NCCL 2.28.9
fallback (including explicitly enabled PyNccl during CUDA graph capture), not
omitted reductions. This can affect throughput and floating-point reduction
order; no bitwise equivalence to the custom kernel is claimed. Separately, the
generic "FP8 KV scale 1.0" warning does not describe DSV4's actual packed cache:
its dedicated kernels calculate/store per-64-value UE8M0 scales and read them
back. The official auto-selected FP8 dtype is retained; this is not a claim
that FP8 and BF16 produce identical results. Real native/task gates remain required.
