#!/usr/bin/env bash
set -euo pipefail
BASE=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving
UV=/lustrefs/users/chufan.shi/.local/bin/uv
export UV_CACHE_DIR="$BASE/.uv-cache"
export SGLANG_BUILD_RUST_EXTS=none
export SETUPTOOLS_SCM_PRETEND_VERSION=0.5.16+k3.expgym
mkdir -p "$BASE/logs" "$BASE/manifests"
"$UV" venv --python /usr/bin/python3.12 --system-site-packages "$BASE/.venv"
"$UV" pip install --python "$BASE/.venv/bin/python" --no-deps --no-build-isolation --editable "$BASE/image_source/sgl-workspace/sglang/python"
"$UV" pip freeze --python "$BASE/.venv/bin/python" > "$BASE/manifests/uv-freeze.txt"
"$BASE/.venv/bin/python" "$BASE/inspect_environment.py"
"$BASE/.venv/bin/sglang" serve --help > "$BASE/manifests/sglang-serve-help.txt"
