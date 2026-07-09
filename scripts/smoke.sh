#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${EXPGYM_SMOKE_VENV:-"$ROOT_DIR/.venv-smoke"}"
PYTHON_BIN="${PYTHON:-python3}"
OPENROUTER_MODEL="${EXPGYM_OPENROUTER_MODEL:-openai/gpt-4.1-nano}"
OPENROUTER_KEY_FILE="${OPENROUTER_API_KEY_FILE:-"$ROOT_DIR/../openrouter.key"}"
USE_VENV=1
WITH_AUTO_DATA=0

usage() {
  cat <<'EOF'
Usage: bash scripts/smoke.sh [--with-auto-data] [--no-venv] [--model MODEL] [--api-key-file PATH]

Runs the real OpenRouter ExpGym smoke:
  1. create/reuse .venv-smoke
  2. install Python dependencies
  3. run unit tests
  4. run a real OpenRouter ReAct tuning trace end to end

Options:
  --with-auto-data  Also install data dependencies and fetch external datasets:
                    Phantom Wiki, HPOBench source, and ContractNLI.
  --model MODEL     OpenRouter model for the real smoke
                    (default: EXPGYM_OPENROUTER_MODEL or openai/gpt-4.1-nano).
  --api-key-file PATH
                    File containing the OpenRouter API key when OPENROUTER_API_KEY
                    is not already set (default: ../openrouter.key).
  --no-venv         Use the active Python environment instead of .venv-smoke.
  -h, --help        Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-auto-data)
      WITH_AUTO_DATA=1
      shift
      ;;
    --no-venv)
      USE_VENV=0
      shift
      ;;
    --model)
      OPENROUTER_MODEL="${2:?--model requires a value}"
      shift 2
      ;;
    --api-key-file)
      OPENROUTER_KEY_FILE="${2:?--api-key-file requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

if [[ "$USE_VENV" -eq 1 ]]; then
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  PY="$VENV_DIR/bin/python"
else
  PY="$PYTHON_BIN"
fi

echo "[smoke] python: $("$PY" -c 'import sys; print(sys.executable)')"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  if [[ ! -f "$OPENROUTER_KEY_FILE" ]]; then
    echo "OPENROUTER_API_KEY is not set and key file was not found: $OPENROUTER_KEY_FILE" >&2
    echo "Set OPENROUTER_API_KEY or pass --api-key-file PATH." >&2
    exit 1
  fi
  OPENROUTER_API_KEY="$(tr -d '\n\r' < "$OPENROUTER_KEY_FILE")"
  export OPENROUTER_API_KEY
fi

if [[ "$WITH_AUTO_DATA" -eq 1 ]]; then
  "$PY" -m pip install -r requirements-data.txt
  "$PY" scripts/download_data.py
fi

echo "[smoke] running unit tests"
"$PY" -m unittest discover tests

echo "[smoke] running real OpenRouter tuning trace with $OPENROUTER_MODEL"
"$PY" scripts/openrouter_smoke.py --model "$OPENROUTER_MODEL"

echo "[smoke] OK"
