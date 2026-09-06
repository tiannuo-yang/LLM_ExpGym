#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${EXPGYM_HPOBENCH_ENV:-expgym-hpobench}"
PYTHON_VERSION="${EXPGYM_HPOBENCH_PYTHON:-3.7}"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is required but not found in PATH." >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" && "${EXPGYM_FORCE_HPOBENCH_INSTALL:-0}" != "1" ]]; then
  cat >&2 <<'EOF'
ParamNet needs a legacy Python 3.7/scikit-learn stack, which is not reliably
available as native macOS arm64 packages. Use the supported Docker runner.

Set EXPGYM_FORCE_HPOBENCH_INSTALL=1 only if you know your Python/package
indexes provide compatible Python 3.7 and scikit-learn wheels.
EOF
  exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"

conda env remove -n "$ENV_NAME" -y >/dev/null 2>&1 || true
conda create -n "$ENV_NAME" -y python="$PYTHON_VERSION" pip

ENV_PREFIX="$(conda env list | awk -v env="$ENV_NAME" '$1==env{print $2}')"
if [[ -z "$ENV_PREFIX" ]]; then
  echo "Failed to locate conda env prefix for $ENV_NAME" >&2
  exit 1
fi

export PYTHONNOUSERSITE=1
"$ENV_PREFIX/bin/python" -m pip install -U "pip<23" setuptools wheel
"$ENV_PREFIX/bin/python" -m pip install \
  "numpy==1.18.5" \
  "scipy==1.4.1" \
  "pyyaml>=6.0,<7" \
  "ConfigSpace==0.4.21" \
  "importlib-metadata>=4,<7" \
  "tqdm" \
  "scikit-learn==0.23.2"

# Install HPOBench from the local checkout.
"$ENV_PREFIX/bin/python" -m pip install -e "$ROOT_DIR/data/hpo_tuning/HPOBench"

# Optional: print env python for verification.
"$ENV_PREFIX/bin/python" - <<'PY'
import sys
print('expgym-hpobench python:', sys.executable)
import ConfigSpace  # noqa: F401
import hpobench  # noqa: F401
print('HPOBench imports OK')
PY
