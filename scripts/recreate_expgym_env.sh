#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="expgym"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is required but not found in PATH." >&2
  exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"

conda env remove -n "$ENV_NAME" -y >/dev/null 2>&1 || true
conda env create -f "$ROOT_DIR/environment.yml"

ENV_PREFIX="$(conda env list | awk -v env="$ENV_NAME" '$1==env{print $2}')"
if [[ -z "$ENV_PREFIX" ]]; then
  echo "Failed to locate conda env prefix for $ENV_NAME" >&2
  exit 1
fi

export PYTHONNOUSERSITE=1
"$ENV_PREFIX/bin/python" -m pip install -U "pip<23" setuptools wheel

# Install HPOBench from the local checkout.
"$ENV_PREFIX/bin/python" -m pip install -e "$ROOT_DIR/data/hpo_tuning/HPOBench"

# NASBench-101 dependencies (needed for hpobench:nasbench101:* tasks).
"$ENV_PREFIX/bin/python" -m pip install "protobuf<4" "tensorflow==1.15.0"
"$ENV_PREFIX/bin/python" -m pip install git+https://github.com/automl/nas_benchmarks.git@master
"$ENV_PREFIX/bin/python" -m pip install git+https://github.com/google-research/nasbench.git@master

# Pin sklearn to keep HPOBench surrogate pickles loadable.
"$ENV_PREFIX/bin/python" -m pip install "scikit-learn==0.23.2"

# Optional: print env python for verification.
"$ENV_PREFIX/bin/python" -c "import sys; print('expgym python:', sys.executable)"
