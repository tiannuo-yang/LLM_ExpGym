#!/usr/bin/env bash
# Execute a repository Python entry point in the isolated legacy evaluator.
set -euo pipefail
RUNTIME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$RUNTIME_DIR/../../LLM_ExpGym" && pwd)"
export HPOBENCH_ROOT="$REPO_DIR/data/hpo_tuning/HPOBench"
export PYTHONNOUSERSITE=1
export PYTHONPATH="$REPO_DIR${PYTHONPATH:+:$PYTHONPATH}"
export XDG_DATA_HOME="$REPO_DIR/data/hpo_tuning/hpobench_data"
export XDG_CACHE_HOME="$REPO_DIR/data/hpo_tuning/hpobench_cache"
export XDG_CONFIG_HOME="$RUNTIME_DIR/hpobench_config"
export OMP_NUM_THREADS="${EXPGYM_HPO_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${EXPGYM_HPO_THREADS:-1}"
export MKL_NUM_THREADS="${EXPGYM_HPO_THREADS:-1}"
cd "$REPO_DIR"
exec "$RUNTIME_DIR/.venv-hpo/bin/python" "$@"
