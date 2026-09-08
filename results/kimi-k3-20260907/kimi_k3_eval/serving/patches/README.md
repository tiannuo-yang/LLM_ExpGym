# SGLang PR #32477 backport for Kimi-K3

This is the unmodified upstream patch from [PR #32477](https://github.com/sgl-project/sglang/pull/32477), merged as `ee678910f7000aa43886f218de0e159bf418f1b5` on 2026-07-29. All three current image-source files match upstream base commit `84cdfde5b2cc383ea7008fe9fca519d4b1277329` byte for byte. The target copies match the merged commit byte for byte.

## Artifacts and integration

- `upstream_pr32477.patch`: exact upstream diff; two runtime files plus the upstream test file. The final PR does **not** modify `memory_pool.py`.
- `original/`: three original files only.
- `source/`: three complete patched files only; this directory is an overlay, not an importable SGLang checkout.
- `original.sha256`, `target.sha256`: checksums relative to a SGLang source root.
- `manifest.json`: full commit and digest provenance, verification state, scope, limitations.

From a full SGLang checkout, verify `sha256sum -c /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/patches/original.sha256` and `git apply --check /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/patches/upstream_pr32477.patch` before integration. After applying the changes, verify `sha256sum -c /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/patches/target.sha256`. Original and target overlay directories also pass the forward and reverse patch applicability checks, respectively.

The serving owner has built a distinct `0.5.16+pr32477` wheel from the two runtime changes. Keep that exact wheel and its dependency lock/manifest in the independent uv environment. Do not put this partial `source/python` directory on PYTHONPATH. For an installed wheel, the first two target hashes apply to matching `sglang/...` paths under site-packages. The test remains in this artifact directory.

## Meaning and compatibility

The upstream change adds `reserved_skip_index=0` to the Python/CUDA API and skips K/V copies into that slot. `reserved_skip_index=-1` restores the old ability to write row 0. The existing bounds assert remains intact, and the PDL secondary trigger remains outside the conditional.

Within the checked image source, paths below are relative to the SGLang root:

- `python/sglang/srt/mem_cache/allocator/token.py:43` allocates real slots from 1; `allocator/paged.py:278` allocates real pages from 1.
- `python/sglang/srt/model_executor/runner_utils/buffers.py:238` initializes graph-padding cache locations to 0.
- Production `memory_pool.py:51` imports `kernels/ops/kvcache/kvcache.py`; `memory_pool.py:156` calls its `store_cache`. The old `sglang/jit_kernel/` duplicates are not this production import path and are not part of the upstream patch.
- MHA writes reach `memory_pool.py:2384` and then the common implementation; the valid cache bound `size + page_size` is preserved.
- K3 chooses KDA/MLA by layer in `models/kimi_k3.py:1909` and `:1922`. Compressed MLA may instead reach `MLATokenToKVPool` indexed assignment (`memory_pool.py:3996`) or Triton writer (`:4045`); KDA recurrent-state writes are separate (`layers/attention/linear/kda_backend.py:447`).
- If `can_use_store_cache` fails to compile, the MHA fallback uses indexed assignment (`memory_pool.py:185`), which is also outside this patch.

Therefore the source change is a safe exact backport for the generic reserved-slot bug. Passing its regression test is not proof that every K3 KV writer or every source of NaNs is fixed.

## GPU acceptance and commands

Run these in the completed independent environment on a GPU already authorized by the serving owner. This subtask does not allocate GPUs or change jobs.

First confirm the installed wrapper has `reserved_skip_index` and its CUDA source has the target hash. Use a fresh, distinct `TVM_FFI_CACHE_DIR` for this patched build so the changed CUDA/Python argument signature cannot accidentally reuse an old JIT library.

Minimum upstream regression, expected **7 passed**:

```bash
python -m pytest -q -x -p no:cacheprovider \
  /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/patches/source/test/registered/kernels/ops/kvcache/test_store_cache.py \
  -k 'reserved_skip_index or zero_index_can_be_written_when_skip_disabled' \
  --junitxml=/ABSOLUTE_RUN_DIR/pr32477-minimum.xml
```

This injects NaNs into rows addressed to duplicate reserved indices, checks unchanged reserved contents and correct valid-slot writes, covers int32/int64 and split counts 1/2/4, and checks the opt-out.

Full upstream sweep, expected **340 passed** with full ranges forced:

```bash
SGLANG_JIT_KERNEL_RUN_FULL_TESTS=1 python -m pytest -q -x -p no:cacheprovider \
  /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/patches/source/test/registered/kernels/ops/kvcache/test_store_cache.py \
  --junitxml=/ABSOLUTE_RUN_DIR/pr32477-full.xml
```

The local full sweep passed all **340 tests in 144.85 seconds** on 2026-09-07,
using H200 GPU 0 of node 267 in owned bootstrap job `1203298` and the independent
uv environment with `sglang==0.5.16+pr32477`. The largest K+V cache pair used
roughly 4 GiB, within the existing allocation's free GPU memory. Raw output is
`../logs/padding-kernel-tests.log`; machine-readable records are
`../manifests/padding-tests.xml` and `../manifests/padding-tests-passed.json`.

After kernel tests, the serving owner should run the actual eight-node K3 endpoint through its multi-request and approximately 100k-context smoke/probe, preserve raw responses/logs, and check finite output and absence of PAD storms. This is a separate model-level gate because K3 also uses other writers.

## Verification status

- Current image source equals upstream base for all three files: passed.
- Complete target copies equal upstream merge file digests: passed.
- Forward patch applicability on current image source and original copies: passed.
- Reverse patch applicability on target copies: passed.
- Python wrapper/test syntax compilation and all original/target checksum files: passed.
- Local GPU regression: **340 passed, zero failures/errors**, 144.85 seconds;
  completed 2026-09-07 08:46:22 UTC.
- K3 long-context probe: **passed**, 100,174 prompt tokens, correct passcode
  retrieval, normal `stop`, no `[PAD]`, 33.622 seconds; completed 2026-09-07
  08:57:15 UTC on final job `1203299`. Full raw request and response are in
  `../runs/1203299/smoke/long_context_100000.json`.

An earlier collect-only attempt overlapped an incomplete uv installation and
collected no tests. The completed environment subsequently passed the full
340-test GPU sweep above; that completed run is the acceptance result.
