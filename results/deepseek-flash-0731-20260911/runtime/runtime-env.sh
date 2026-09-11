#!/usr/bin/env bash
# Source before the launcher. Does not select GPUs, allocate nodes, or launch.
DEEPSEEK_RUNTIME_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEEPSEEK_RUNTIME_VENV="$DEEPSEEK_RUNTIME_ROOT/.venv"
DEEPSEEK_RUNTIME_SITE="$DEEPSEEK_RUNTIME_VENV/lib/python3.12/site-packages"
DEEPSEEK_RUNTIME_LIBS="$DEEPSEEK_RUNTIME_SITE/torch/lib:$DEEPSEEK_RUNTIME_SITE/tvm_ffi/lib"
for deepseek_vendor_lib in "$DEEPSEEK_RUNTIME_SITE"/nvidia/*/lib; do
    if [[ -d "$deepseek_vendor_lib" ]]; then
        DEEPSEEK_RUNTIME_LIBS="$deepseek_vendor_lib:$DEEPSEEK_RUNTIME_LIBS"
    fi
done
export LD_LIBRARY_PATH="$DEEPSEEK_RUNTIME_LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBRARY_PATH="$DEEPSEEK_RUNTIME_SITE/nvidia/nccl/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
export PATH="$DEEPSEEK_RUNTIME_VENV/bin:$PATH"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export HF_HOME="$DEEPSEEK_RUNTIME_ROOT/hf-cache"
export HF_MODULES_CACHE="$DEEPSEEK_RUNTIME_ROOT/hf-cache/modules"
export XDG_CACHE_HOME="$DEEPSEEK_RUNTIME_ROOT/cache"
export TRITON_CACHE_DIR="$DEEPSEEK_RUNTIME_ROOT/cache/triton"
export FLASHINFER_WORKSPACE_BASE="$DEEPSEEK_RUNTIME_ROOT/cache/flashinfer"
unset SGLANG_EXPERIMENTAL_CPP_RADIX_TREE SGLANG_DEFAULT_THINKING SGLANG_DSV4_REASONING_EFFORT
unset PYTHONPATH
# No NCCL interface/HCA is hard-coded: validate interfaces on allocated nodes.
# CUDA_VISIBLE_DEVICES remains Slurm-owned. No inherited credentials are read.
