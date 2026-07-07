FROM python:3.7-bullseye

ENV DEBIAN_FRONTEND=noninteractive \
    HPOBENCH_ROOT=/opt/HPOBench \
    PYTHONNOUSERSITE=1 \
    PIP_NO_CACHE_DIR=1 \
    XDG_CACHE_HOME=/workspace/LLM_ExpGym/data/hpo_tuning/hpobench_cache \
    XDG_DATA_HOME=/workspace/LLM_ExpGym/data/hpo_tuning/hpobench_data

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install -U "pip<23" setuptools wheel

RUN python -m pip install \
        "numpy==1.18.5" \
        "scipy==1.4.1" \
        "pyyaml==6.0.1" \
        "ConfigSpace==0.4.21" \
        "Pyro4==4.80" \
        "oslo.concurrency>=4.2.0" \
        "requests" \
        "tqdm" \
        "protobuf<4" \
        "tensorflow==1.15.0" \
        "scikit-learn==0.23.2"

RUN git clone --depth 1 https://github.com/automl/HPOBench.git "$HPOBENCH_ROOT" \
    && python -m pip install -e "$HPOBENCH_ROOT" \
    && python -m pip install git+https://github.com/automl/nas_benchmarks.git@master \
    && python -m pip install git+https://github.com/google-research/nasbench.git@master

WORKDIR /workspace/LLM_ExpGym

CMD ["python", "scripts/run_paper_sweep.py", "--help"]
