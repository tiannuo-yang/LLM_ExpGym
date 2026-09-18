#!/usr/bin/env python3
"""Offline JSON-lines ParamNet evaluator for the existing Python 3.7 stack.

This process isolates the legacy sklearn 0.23.2 / NumPy 1.18.5 dependencies
needed by the original ParamNet pickles from NAS evaluators using NumPy 2.4.6.
It calls the repository's build_tools unchanged, and never calls an LLM.

Each stdin line is {"item": "hpobench:paramnet:adult:steps", "answer": "..."}.
Each stdout line is {"performance": number, "evaluation_reason": string}.
Only InvalidConfigurationError maps to the historical invalid-config zero;
all dependency, data, input-protocol, and unexpected evaluator errors fail
the process instead of silently turning unavailable scores into zero.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--data-root", type=Path, required=True,
                   help="Directory containing HPOBench/ and hpobench_data/")
    p.add_argument("--state-root", type=Path, required=True,
                   help="Invocation-specific directory for HPOBench config/cache")
    args = p.parse_args()
    repo = args.repo.resolve()
    data = args.data_root.resolve()
    state = args.state_root.resolve()
    source, tables = data / "HPOBench", data / "hpobench_data"
    if not (repo / "expgym/task_tuning.py").is_file():
        p.error("--repo must contain expgym/task_tuning.py")
    if not (source / "hpobench").is_dir() or not tables.is_dir():
        p.error("--data-root must contain existing HPOBench and hpobench_data")
    # HPOBench otherwise attempts to download missing surrogates. Require
    # every local file before import so this worker remains strictly offline.
    for dataset in ("adult", "higgs", "letter"):
        for prefix in ("rf_surrogate_paramnet_", "rf_cost_surrogate_paramnet_"):
            surrogate = tables / "Surrogates" / (prefix + dataset + ".pkl")
            if not surrogate.is_file():
                p.error("Missing local ParamNet surrogate: " + str(surrogate))
    config_dir, cache_dir, socket_dir = (state / n for n in ("config", "cache", "sockets"))
    for directory in (config_dir, cache_dir, socket_dir):
        directory.mkdir(parents=True, exist_ok=True)
    config = {
        "version": "0.0.10", "verbosity": 0,
        "cache_dir": str(cache_dir), "data_dir": str(tables),
        "socket_dir": str(socket_dir),
        "container_dir": str(cache_dir / ("hpobench-" + str(os.getuid()))),
        "container_source": "oras://gitlab.tf.uni-freiburg.de:5050/muelleph/hpobench-registry",
        "pyro_connect_max_wait": 400,
    }
    body = json.dumps(config, indent=2, sort_keys=True) + "\n"
    config_path = config_dir / ".hpobenchrc"
    if config_path.exists():
        if json.loads(config_path.read_text()) != config:
            raise RuntimeError("Existing worker HPOBench configuration differs")
    else:
        config_path.write_text(body)
    os.environ.update({
        "HPOBENCH_ROOT": str(source),
        "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "XDG_CONFIG_HOME": str(config_dir), "XDG_CACHE_HOME": str(cache_dir),
        "XDG_DATA_HOME": str(tables), "TMPDIR": str(socket_dir),
        "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    })
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo))
    # HPOBench prints an optional-pandas notice during import. Keep stdout
    # exclusively machine-readable while retaining that notice on stderr.
    with contextlib.redirect_stdout(sys.stderr):
        from expgym.errors import InvalidConfigurationError
        from expgym.react_loop import _parse_tool_return
        from expgym.task_tuning import build_tools
        import numpy
        import sklearn
        if numpy.__version__ != "1.18.5" or sklearn.__version__ != "0.23.2":
            raise RuntimeError("ParamNet worker requires NumPy 1.18.5 and sklearn 0.23.2")
    tools = {}
    for line in sys.stdin:
        request = json.loads(line)
        item, answer = request["item"], request["answer"]
        if item not in {
            "hpobench:paramnet:adult:steps", "hpobench:paramnet:higgs:steps",
            "hpobench:paramnet:letter:steps",
        } or not isinstance(answer, str):
            raise ValueError("Worker accepts only the three paper ParamNet tasks and string answers")
        with contextlib.redirect_stdout(sys.stderr):
            if item not in tools:
                tools[item] = build_tools(tuning_task=item)["evaluate_config"]
            try:
                performance, _, _ = _parse_tool_return(tools[item](answer))
                if not isinstance(performance, (int, float)) or not math.isfinite(performance):
                    raise ValueError("Benchmark returned a nonfinite or nonnumeric performance")
                result = {"performance": performance, "evaluation_reason": "benchmark_evaluation"}
            except InvalidConfigurationError:
                result = {"performance": 0.0, "evaluation_reason": "invalid_configuration_zero"}
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
