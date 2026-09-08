#!/usr/bin/env bash
set -euo pipefail
BASE=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving
source "$BASE/independent/runtime.sh"
exec "$BASE/independent/.venv/bin/python" "$BASE/router.py" --deployment "$1"
