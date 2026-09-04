#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${EXPGYM_VENV:-$ROOT_DIR/.venv}"
BOOTSTRAP_PYTHON="${PYTHON:-python3}"
DOWNLOAD_DATA=0

usage() {
  cat <<'EOF'
Usage: bash scripts/setup.sh [--with-data]

Create/reuse .venv and install everything needed for native ExpGym and
PoolAct tuning, restricted-search, and evidence-audit runs.

Options:
  --with-data  Also download all external datasets now. Without this flag,
               pass --with-auto-data to an eval command when data is needed.
  -h, --help   Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-data) DOWNLOAD_DATA=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if ! command -v "$BOOTSTRAP_PYTHON" >/dev/null 2>&1; then
  echo "Python was not found: $BOOTSTRAP_PYTHON" >&2
  echo "Install Python 3.9+ and rerun this command." >&2
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "[setup] creating $VENV_DIR"
  "$BOOTSTRAP_PYTHON" -m venv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python"
"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit("ExpGym requires Python 3.9 or newer.")
print(f"[setup] python={sys.executable} version={sys.version.split()[0]}")
PY

echo "[setup] installing Python dependencies"
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r "$ROOT_DIR/requirements.txt" -r "$ROOT_DIR/requirements-data.txt"

if [[ "$DOWNLOAD_DATA" -eq 1 ]]; then
  echo "[setup] downloading external datasets"
  "$PYTHON_BIN" "$ROOT_DIR/scripts/download_data.py"
fi

cat <<EOF

[setup] ready

No activation step is required; eval_model.sh and eval_poolact.sh automatically
use $VENV_DIR.

No-cost check:
  bash scripts/eval_poolact.sh --backend fake

Real PoolAct run after configuring .env:
  bash scripts/eval_poolact.sh
EOF
