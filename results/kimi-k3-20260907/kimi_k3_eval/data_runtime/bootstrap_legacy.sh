#!/usr/bin/env bash
# Docker-equivalent evaluator versions without changing Docker or system Python.
set -euo pipefail
RUNTIME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$RUNTIME_DIR/../../LLM_ExpGym" && pwd)"
mkdir -p "$RUNTIME_DIR/bootstrap" "$RUNTIME_DIR/logs"
if [[ ! -x "$RUNTIME_DIR/bootstrap/bin/micromamba" ]]; then
  curl -fL --retry 3 https://micro.mamba.pm/api/micromamba/linux-64/latest \
    -o "$RUNTIME_DIR/bootstrap/micromamba.tar.bz2"
  tar -xjf "$RUNTIME_DIR/bootstrap/micromamba.tar.bz2" \
    -C "$RUNTIME_DIR/bootstrap" bin/micromamba
fi
if [[ ! -x "$RUNTIME_DIR/bootstrap/py37/bin/python" ]]; then
  MAMBA_ROOT_PREFIX="$RUNTIME_DIR/bootstrap/mamba_root" \
    "$RUNTIME_DIR/bootstrap/bin/micromamba" create -y \
    -p "$RUNTIME_DIR/bootstrap/py37" -c conda-forge --override-channels \
    python=3.7.12 pip
fi
if [[ ! -x "$RUNTIME_DIR/.venv-hpo/bin/python" ]]; then
  uv venv --python "$RUNTIME_DIR/bootstrap/py37/bin/python" \
    "$RUNTIME_DIR/.venv-hpo"
fi
if [[ -f "$RUNTIME_DIR/requirements-hpo.lock" ]]; then
  uv pip install --python "$RUNTIME_DIR/.venv-hpo/bin/python" \
    --require-hashes -r "$RUNTIME_DIR/requirements-hpo.lock"
else
  uv pip install --python "$RUNTIME_DIR/.venv-hpo/bin/python" \
    -r "$RUNTIME_DIR/requirements-hpo.in"
fi
# HPOBench's pinned checkout is installed from verified download_data.py output.
uv pip install --python "$RUNTIME_DIR/.venv-hpo/bin/python" \
  --no-build-isolation -e "$REPO_DIR/data/hpo_tuning/HPOBench"
uv pip freeze --python "$RUNTIME_DIR/.venv-hpo/bin/python" \
  > "$RUNTIME_DIR/requirements-hpo.freeze.txt"
