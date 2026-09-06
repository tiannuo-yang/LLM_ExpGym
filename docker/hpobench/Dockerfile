FROM python:3.7-bullseye

ARG HPOBENCH_GIT_REF=47bf141f79e6bdfb26d1f1218b5d5aac09d7d2ce

ENV DEBIAN_FRONTEND=noninteractive \
    HPOBENCH_ROOT=/opt/HPOBench \
    PYTHONNOUSERSITE=1 \
    PIP_NO_CACHE_DIR=1 \
    XDG_CACHE_HOME=/workspace/LLM_ExpGym/data/hpo_tuning/hpobench_cache \
    XDG_DATA_HOME=/workspace/LLM_ExpGym/data/hpo_tuning/hpobench_data

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
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
        "importlib-metadata>=4,<7" \
        "scikit-learn==0.23.2"

RUN git init "$HPOBENCH_ROOT" \
    && git -C "$HPOBENCH_ROOT" remote add origin https://github.com/automl/HPOBench.git \
    && git -C "$HPOBENCH_ROOT" fetch --depth 1 origin "$HPOBENCH_GIT_REF" \
    && git -C "$HPOBENCH_ROOT" checkout --detach FETCH_HEAD \
    && python -m pip install -e "$HPOBENCH_ROOT"

WORKDIR /workspace/LLM_ExpGym

CMD ["python", "scripts/run_paper_sweep.py", "--help"]
