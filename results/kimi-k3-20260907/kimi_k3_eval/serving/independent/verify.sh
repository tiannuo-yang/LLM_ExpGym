#!/usr/bin/env bash
set -euo pipefail
BASE=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/independent
source "$BASE/runtime.sh"
"$BASE/.venv/bin/python" "$BASE/validate_independent.py" > "$BASE/logs/validation.log" 2>&1
"$BASE/.venv/bin/sglang" serve --help > "$BASE/manifests/sglang-serve-help.txt" 2> "$BASE/logs/serve-help-stderr.log"
/lustrefs/users/chufan.shi/.local/bin/uv pip freeze --python "$BASE/.venv/bin/python" > "$BASE/manifests/uv-freeze.txt"
