#!/usr/bin/env bash
# Source before running the independent environment, especially outside image.
K3_INDEPENDENT=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/independent
K3_SITE="$K3_INDEPENDENT/.venv/lib/python3.12/site-packages"
K3_LIBRARY_PATH="$K3_SITE/torch/lib:$K3_SITE/tvm_ffi/lib"
for K3_VENDOR_LIB in "$K3_SITE"/nvidia/*/lib; do
  if [ -d "$K3_VENDOR_LIB" ]; then
    K3_LIBRARY_PATH="$K3_VENDOR_LIB:$K3_LIBRARY_PATH"
  fi
done
export LD_LIBRARY_PATH="$K3_LIBRARY_PATH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBRARY_PATH="$K3_SITE/nvidia/nccl/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
export PYTHONNOUSERSITE=1
export PATH="$K3_INDEPENDENT/.venv/bin:$PATH"
unset PYTHONPATH
