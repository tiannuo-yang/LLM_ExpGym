#!/usr/bin/env bash
set -euo pipefail

./scripts/recreate_expgym_env.sh
./scripts/setup_vllm_env.sh

echo "Expgym and vLLM environments are installed."
