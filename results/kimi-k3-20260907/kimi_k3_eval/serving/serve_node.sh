#!/usr/bin/env bash
set -euo pipefail
BASE=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving
source "$BASE/independent/runtime.sh"
K3_PAIR=$1
K3_RANK=$2
K3_HEAD_IP=$3
export TRITON_CACHE_DIR="/tmp/k3_expgym_triton_${SLURM_JOB_ID}_${K3_PAIR}_${K3_RANK}"
export HF_MODULES_CACHE="/tmp/k3_expgym_hf_modules_${SLURM_JOB_ID}_${K3_PAIR}_${K3_RANK}"
export OMP_NUM_THREADS=8
export PYTHONUNBUFFERED=1
exec "$BASE/independent/.venv/bin/sglang" serve \
  --model-path /models/kimi-k3 --served-model-name kimi-k3 --trust-remote-code \
  --tp-size 16 --ep-size 16 --nnodes 2 --node-rank "$K3_RANK" \
  --dist-init-addr "$K3_HEAD_IP:$((50140 + K3_PAIR))" \
  --moe-runner-backend marlin --decode-attention-backend flashmla \
  --enable-symm-mem --tool-call-parser kimi_k3 --reasoning-parser kimi_k3 \
  --context-length 524288 --mem-fraction-static 0.84 \
  --cuda-graph-max-bs-decode 128 --max-running-requests 128 \
  --enable-metrics --host 0.0.0.0 --port 30140
