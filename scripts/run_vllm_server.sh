#!/usr/bin/env bash
set -euo pipefail

LOG_FILE=${LOG_FILE:-/tmp/vllm_server.log}
PID_FILE=${PID_FILE:-/tmp/vllm_server.pid}
GPU_UTIL=${GPU_UTIL:-0.95}
MAX_BATCHED_TOKENS=${MAX_BATCHED_TOKENS:-20480}

if [[ "${1:-}" == "--stop" ]]; then
  if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID"
      echo "Stopped vLLM server (PID $PID)."
    else
      echo "PID file found but process not running. Removing stale PID file."
    fi
    rm -f "$PID_FILE"
  else
    echo "No PID file found. Nothing to stop."
  fi
  exit 0
fi

ENV_NAME=${1:-vllm}
MODEL=${2:-Qwen/Qwen3-32B}
PORT=${3:-8000}

if [[ -f "$PID_FILE" ]]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "vLLM server already running (PID $PID)."
    echo "Log: $LOG_FILE"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

ENV_PYTHON="${EXPGYM_CONDA_PREFIX:-/path/to/conda/envs}/${ENV_NAME}/bin/python"
if [[ ! -x "$ENV_PYTHON" ]]; then
  echo "Python not found at $ENV_PYTHON"
  exit 1
fi

nohup "$ENV_PYTHON" -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" \
  --dtype bfloat16 \
  --gpu-memory-utilization "$GPU_UTIL" \
  --max-num-batched-tokens "$MAX_BATCHED_TOKENS" \
  --port "$PORT" \
  > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"
echo "Started vLLM server (PID $PID)."
echo "Log: $LOG_FILE"
