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
HPOBench/NASBench101 needs the legacy TensorFlow 1.15 stack, which has no
native macOS arm64 wheels. Use the default smoke/search/audit runs on this
machine, or build the full HPOBench environment on Linux/x86_64.

Set EXPGYM_FORCE_HPOBENCH_INSTALL=1 only if you know your Python/package
indexes provide compatible TensorFlow 1.15 wheels.
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
  "tqdm" \
  "protobuf<4" \
  "tensorflow==1.15.0" \
  "scikit-learn==0.23.2"

# Install HPOBench from the local checkout.
"$ENV_PREFIX/bin/python" -m pip install -e "$ROOT_DIR/data/hpo_tuning/HPOBench"

# NASBench-101 dependencies (needed for hpobench:nasbench101:* tasks).
"$ENV_PREFIX/bin/python" -m pip install git+https://github.com/automl/nas_benchmarks.git@master
"$ENV_PREFIX/bin/python" -m pip install git+https://github.com/google-research/nasbench.git@master

# Optional: print env python for verification.
"$ENV_PREFIX/bin/python" - <<'PY'
import sys
print('expgym-hpobench python:', sys.executable)
import ConfigSpace  # noqa: F401
import hpobench  # noqa: F401
import nasbench  # noqa: F401
import tabular_benchmarks  # noqa: F401
print('HPOBench/NASBench imports OK')
PY
