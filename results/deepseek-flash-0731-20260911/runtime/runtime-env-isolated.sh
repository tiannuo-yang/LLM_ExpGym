#!/usr/bin/env bash
# Cache-isolation correction only; preserve the original package/encoder runtime.
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/runtime-env.sh"
export SGLANG_DG_CACHE_DIR="$DEEPSEEK_RUNTIME_ROOT/cache/deep_gemm"
export DG_JIT_CACHE_DIR="$SGLANG_DG_CACHE_DIR"
export TILELANG_CACHE_DIR="$DEEPSEEK_RUNTIME_ROOT/cache/tilelang"
export TILELANG_TMP_DIR="$DEEPSEEK_RUNTIME_ROOT/cache/tilelang/tmp"
export CUDA_CACHE_PATH="$DEEPSEEK_RUNTIME_ROOT/cache/cuda-driver"
# Launcher still owns per-allocation/per-replica TRITON, TVM and HF-module paths.
# Do not delete or copy another study's/user-level compilation caches.
