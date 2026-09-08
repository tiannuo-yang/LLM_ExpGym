#!/usr/bin/env bash
set -euo pipefail
BASE=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving
source "$BASE/independent/runtime.sh"
export CUDA_VISIBLE_DEVICES=0
export SGLANG_JIT_KERNEL_RUN_FULL_TESTS=1
export TRITON_CACHE_DIR="/tmp/k3_padding_verify_${SLURM_JOB_ID}"
"$BASE/independent/.venv/bin/python" -m pytest \
  "$BASE/patches/source/test/registered/kernels/ops/kvcache/test_store_cache.py" \
  -q -x --junitxml="$BASE/manifests/padding-tests.xml"
"$BASE/independent/.venv/bin/python" "$BASE/record_padding_pass.py"
