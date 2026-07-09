#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

USE_VENV=1
WITH_AUTO_DATA=0
CONTRACT_NLI_ARCHIVE="${CONTRACT_NLI_ARCHIVE:-}"
PYTHON_BIN="${PYTHON:-python3}"
VENV_DIR="${EXPGYM_VENV:-"$ROOT_DIR/.venv-expgym"}"
RUNNER_ARGS=()
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: bash scripts/run_paper_sweep.sh [wrapper options] [runner options]

Wrapper options:
  --with-auto-data              Install data deps and fetch Phantom Wiki, HPOBench source, and ContractNLI.
  --contract-nli-archive PATH   Optional offline ContractNLI zip override.
  --no-venv                     Use the active Python instead of .venv-expgym.
  --venv PATH                   Override the venv path.
  --python PATH                 Python executable used to create the venv.
  -h, --help                    Show this help.

Runner examples:
  bash scripts/run_paper_sweep.sh
  bash scripts/run_paper_sweep.sh --scenarios restricted_search --search-indices 0
  bash scripts/run_paper_sweep.sh --models openai/gpt-4.1-nano --cost-regimes cost_tight
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-auto-data)
      WITH_AUTO_DATA=1
      shift
      ;;
    --contract-nli-archive)
      CONTRACT_NLI_ARCHIVE="${2:?--contract-nli-archive requires a path}"
      shift 2
      ;;
    --no-venv)
      USE_VENV=0
      shift
      ;;
    --venv)
      VENV_DIR="${2:?--venv requires a path}"
      shift 2
      ;;
    --python)
      PYTHON_BIN="${2:?--python requires a path}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ "$1" == "--dry-run" ]]; then
        DRY_RUN=1
      fi
      RUNNER_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ "$USE_VENV" -eq 1 ]]; then
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  PY="$VENV_DIR/bin/python"
else
  PY="$PYTHON_BIN"
fi

echo "[run] python: $("$PY" -c 'import sys; print(sys.executable)')"
echo "[run] installing light Python dependencies"
"$PY" -m pip install --upgrade --disable-pip-version-check --quiet pip
"$PY" -m pip install --disable-pip-version-check --quiet -r requirements.txt

if [[ "$WITH_AUTO_DATA" -eq 1 && "$DRY_RUN" -eq 0 ]]; then
  echo "[run] preparing datasets"
  "$PY" -m pip install --disable-pip-version-check --quiet -r requirements-data.txt
  "$PY" scripts/download_data.py
elif [[ "$WITH_AUTO_DATA" -eq 1 ]]; then
  echo "[run] dry-run: skipping dataset preparation"
fi

if [[ -n "$CONTRACT_NLI_ARCHIVE" && "$DRY_RUN" -eq 0 ]]; then
  echo "[run] extracting ContractNLI test split"
  "$PY" scripts/download_data.py --contract-nli-archive "$CONTRACT_NLI_ARCHIVE"
elif [[ -n "$CONTRACT_NLI_ARCHIVE" ]]; then
  echo "[run] dry-run: skipping ContractNLI extraction"
fi

if [[ ${#RUNNER_ARGS[@]} -eq 0 ]]; then
  "$PY" scripts/run_paper_sweep.py
else
  "$PY" scripts/run_paper_sweep.py "${RUNNER_ARGS[@]}"
fi
