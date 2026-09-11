# Qwen3.8 isolated SGLang runtime build

Status: CPU readiness gates passed; runtime/lock/env frozen for the first GPU
loading smoke on 2026-09-10. This preparation did not allocate GPUs or launch a
model. GPU correctness, memory use, communication and throughput are unverified.

- Interpreter: CPython 3.12.13, existing standalone interpreter (read-only).
- SGLang: official PyPI 0.5.17; corresponding source tag
  `29481685462732237d80d86076d6563e1f658102`.
- Torch / torchaudio / torchvision: 2.11.0 / 2.11.0 / 0.26.0, official cu129 wheels.
- Cluster's previous H200 hardware receipt reports NVIDIA driver 570.133.20.
  CUDA 12 is deliberate; unmodified default cu13 dependencies are not appropriate
  for that driver without separately established forward compatibility.
- `pyproject.toml` overrides only CUDA dependency selection: cuda-python <13,
  FlashInfer cu12, CUTLASS without cu13 extras, Humming without cu13 extras,
  and official cu129 SGLang-kernel / DeepGEMM wheels. No SGLang sampler or model
  source changes; no old gumbel patch.
- Quack is explicitly pinned to 0.6.1, whose official dependency is CUTLASS
  4.6.0. The newer Quack 0.6.4 requires 4.6.2 and conflicts with SGLang's pin.
  Flash Attention 4.0.0b19 is an explicit required prerelease; unrelated
  prereleases are not enabled globally. The lock targets Linux x86_64 only.
- Official references:
  <https://docs.sglang.io/docs/get-started/install> (CUDA 12 alternative),
  <https://github.com/sgl-project/sglang/blob/29481685462732237d80d86076d6563e1f658102/docker/Dockerfile>,
  <https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8> (H200 TP8×PP4).

Build actions:

1. `uv lock --python /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/independent/python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12`
   resolved 212 packages, exit 0, tool `21a4e2`. This initial lock used uv's
   default shared download cache; subsequent installation uses the runtime-local
   cache. No old environment was modified.
2. Initial `uv sync --locked` installed 205 distributions, exit 0 (`abe225`).
   Dependency inspection caught the Quack/CUTLASS mismatch. After the explicit
   Quack/Flash Attention pins and prerelease-policy correction,
   `uv lock --upgrade --cache-dir ./uv-cache` resolved 206 packages (`f431eb`),
   and final `uv sync --locked --cache-dir ./uv-cache` completed (`75fa28`).
   These follow-up operations changed only this new environment.
3. Final lock SHA256:
   `ad2c27725f4734a8f9fb806c91befdf0233a9d5a95a846601cedd55517b3d8cc`.
   `versions.json` records all 205 installed distributions and CPU test results.
4. `uv pip check --python .venv/bin/python` reports only the deliberate upstream
   metadata mismatch: SGLang declares `cuda-python>=13.0`, while the approved
   CUDA 12 route installs 12.9.7 (`9ce597`). This is not reported as an entirely
   clean, unmodified dependency graph.

Acceptance gates completed:

- Torch 2.11.0+cu129 and SGLang 0.5.17 import successfully (`462400`).
- `sglang serve --help` exits 0 (`5299e4`), including TP/PP, multinode,
  FlashInfer linear attention, SSM, page size and both Qwen parser options.
  Optional diffusion support is not installed or required.
- Actual `ModelRegistry.resolve_model_cls(["Qwen3_5MoeForCausalLM"])` returns
  `sglang.srt.models.qwen3_5_text.Qwen3_5MoeForCausalLM`, not a Transformers
  fallback (`60d102`). Unrelated optional model imports warn about missing vLLM.
- `verify_cpu.py --checkpoint /lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Qwen3.8-2.4T-A95B-FP8`
  passes all nine checks (`a6ac78`): local config/tokenizer, supported reasoning
  efforts, rejection of `max` and disabled thinking, XML tool rendering,
  typed Qwen3-Coder tool parsing, and reasoning/final separation.
  Run with `CUDA_VISIBLE_DEVICES=''`; no CUDA context was initialized.
- `source runtime-env.sh` then `ldd` on the bundled SM90 common-ops library
  resolves every dependency (`a82471`), using this venv's Torch, CUDA 12.9,
  TVM and NCCL rather than old environments. NCCL `ncclGetVersion` returns
  22809 without initializing CUDA (`07dcb9`).
- One extra diagnostic explicitly loaded SM90 common-ops after importing
  SGLang, which had already registered its common ops; it aborted with a
  duplicate operator-registration error (`dc0ffd`). This was an invalid
  double-load diagnostic, not the normal import/CLI path. No kernel/source
  patch was applied and that diagnostic must not be used in the launcher.

First GPU smoke configuration / remaining checks:

- Source `runtime-env.sh` before running `.venv/bin/python` or `.venv/bin/sglang`.
  It does not select GPUs or hard-code network interfaces. The launcher may
  override compilation caches per rank/node; these are not model prompt caches.
- Planned allocation: four nodes × eight H200, one TP8 × PP4 replica, EP1,
  account `k2p`. Dual TP16 cannot fit the 2.496 TB FP8 checkpoint: even without
  MTP weights, 16 × 150121283584 device bytes is insufficient before buffers.
- Preserve official H200 TP8/PP4, FlashInfer linear prefill/decode, page size 64,
  max-prefill-tokens 8192, mamba-full-memory-ratio 0.95, dist-timeout 1800,
  qwen3 reasoning parser and qwen3_coder tool parser; no speculative decoding.
- Explicit departure from the latest cookbook: root selected
  `--mamba-ssm-dtype float32` for this version, matching the checkpoint config.
  The latest cookbook says bfloat16. Legacy SM90 prefill requires float32,
  but SGLang casts state on entry/write-back and this FlashInfer version also
  has a BF16 decode branch for K=V=128 with SM90-compatible FMA. Therefore we
  do **not** claim BF16 is categorically unsupported; it was not GPU-validated.
- Root's pilot limits: context 262144, mem-fraction-static 0.85,
  max-running-requests 64 and graph maximum batch 64. These are pilot limits,
  not a demonstrated peak-throughput or maximum-concurrency configuration.
  Do not change scientific max-output-token/budget settings to alter throughput.
- Metadata-only sampled FP8 evidence (`1d7203`): layer-0 expert gate/up weights
  are F8_E4M3 [2048,8192], BF16 weight_scale_inv [16,64]; down weight is
  [8192,2048], scale [64,16]. This agrees with 128×128 block quantization.
  SGLang fp8.py creates float32 scale parameters and its loaders copy/convert
  checkpoint scales; no re-quantization or checkpoint mutation is requested.
- This host's nvcc is 12.8.93, while isolated runtime libraries are cu129.
  No known hard blocker was established from this minor-version difference;
  first GPU kernel/JIT execution must validate it. Do not silently modify the
  system CUDA toolkit or driver.
- Read-only local networking: eth0 is up; mlx5_ib0..7 map to ib0..7, all up.
  This is not a cross-node NCCL test. Check allocated-node interfaces and
  communication during smoke; do not blindly copy cookbook interface names.

No checkpoint tensor payloads were read during CPU checks. An earlier bounded
metadata check verified all 213 shard headers/offsets against the index; this is
structural completeness, not a full payload checksum or successful model load.
