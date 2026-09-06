#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "$ROOT_DIR/scripts/setup.sh" --with-data
bash "$ROOT_DIR/scripts/setup_vllm_env.sh" "$@"

echo "ExpGym and vLLM environments are installed. HPOBench uses Docker on demand."
