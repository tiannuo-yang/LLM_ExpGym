#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=${1:-vllm}
PYTHON_VERSION=${2:-3.10}

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is required but not found in PATH." >&2
  exit 1
fi

if ! conda env list | awk 'NF >= 1 {print $1}' | grep -Fxq "$ENV_NAME"; then
  conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
fi
conda run -n "$ENV_NAME" python -m pip install --upgrade pip
conda run -n "$ENV_NAME" python -m pip install vllm

echo "vLLM env '$ENV_NAME' is ready."
