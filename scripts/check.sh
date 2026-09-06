#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${EXPGYM_VENV:-$ROOT_DIR/.venv}"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  EXPGYM_VENV="$VENV_DIR" bash scripts/setup.sh
fi
PY="$VENV_DIR/bin/python"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/expgym-check.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "[check] compile"
"$PY" -m compileall -q expgym scripts demo_experiment.py

echo "[check] shell syntax"
for script in scripts/*.sh; do
  bash -n "$script"
done

echo "[check] unit/integration tests"
"$PY" -m unittest discover -s tests

echo "[check] ExpGym fake end to end"
"$PY" scripts/run_paper_sweep.py \
  --backend fake --models fake --scenarios tuning \
  --tuning-tasks neural_network_training --cost-regimes cost_tight \
  --max-steps 5 --max-evals 4 --output-dir "$TMP_DIR/expgym"

echo "[check] PoolAct fake end to end"
"$PY" scripts/run_poolact.py \
  --backend fake --model fake --scenario tuning \
  --agents 2 --strategies naive,cached,poolact \
  --max-steps 5 --max-evals 4 --output-dir "$TMP_DIR/poolact"

echo "[check] OK"
