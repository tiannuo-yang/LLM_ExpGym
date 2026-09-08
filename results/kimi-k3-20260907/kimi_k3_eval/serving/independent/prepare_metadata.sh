#!/usr/bin/env bash
set -euo pipefail
BASE=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/independent
IMAGE=/lustrefs/users/chufan.shi/codex_space/Tau_vision/.images/sglang_k3_cu12.sqsh
mkdir -p "$BASE/logs" "$BASE/manifests" "$BASE/wheels"
unsquashfs -processors 8 -no-progress -no-xattrs -dest "$BASE/image_metadata" "$IMAGE" 'usr/local/lib/python3.12/dist-packages/*.dist-info'
export UV_PYTHON_INSTALL_DIR="$BASE/python"
uv python install 3.12
PYTHON=$(uv python find 3.12 --python-preference only-managed --managed-python)
uv venv --python "$PYTHON" "$BASE/.venv"
