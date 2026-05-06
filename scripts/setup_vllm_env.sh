#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=${1:-vllm}
PYTHON_VERSION=${2:-3.10}

conda env create -n "$ENV_NAME" python="$PYTHON_VERSION" -y || true
conda run -n "$ENV_NAME" python -m pip install --upgrade pip
conda run -n "$ENV_NAME" python -m pip install vllm

echo "vLLM env '$ENV_NAME' is ready."
