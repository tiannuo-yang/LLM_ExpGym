#!/usr/bin/env bash
# Source before the launcher. Does not select GPUs, allocate nodes, or launch.
QWEN_RUNTIME_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
QWEN_RUNTIME_VENV="$QWEN_RUNTIME_ROOT/.venv"
QWEN_RUNTIME_SITE="$QWEN_RUNTIME_VENV/lib/python3.12/site-packages"
QWEN_RUNTIME_LIBS="$QWEN_RUNTIME_SITE/torch/lib:$QWEN_RUNTIME_SITE/tvm_ffi/lib"
for qwen_vendor_lib in "$QWEN_RUNTIME_SITE"/nvidia/*/lib; do
    if [[ -d "$qwen_vendor_lib" ]]; then
        QWEN_RUNTIME_LIBS="$qwen_vendor_lib:$QWEN_RUNTIME_LIBS"
    fi
done
export LD_LIBRARY_PATH="$QWEN_RUNTIME_LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBRARY_PATH="$QWEN_RUNTIME_SITE/nvidia/nccl/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
export PATH="$QWEN_RUNTIME_VENV/bin:$PATH"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export HF_HOME="$QWEN_RUNTIME_ROOT/hf-cache"
export HF_MODULES_CACHE="$QWEN_RUNTIME_ROOT/hf-cache/modules"
export XDG_CACHE_HOME="$QWEN_RUNTIME_ROOT/cache"
export TRITON_CACHE_DIR="$QWEN_RUNTIME_ROOT/cache/triton"
export FLASHINFER_WORKSPACE_BASE="$QWEN_RUNTIME_ROOT/cache/flashinfer"
unset PYTHONPATH
# No NCCL interface/HCA is hard-coded: validate interfaces on allocated nodes.
# CUDA_VISIBLE_DEVICES remains Slurm-owned. No inherited credentials are read.
