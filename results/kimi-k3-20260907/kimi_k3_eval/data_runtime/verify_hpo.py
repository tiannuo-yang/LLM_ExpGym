"""Replay repository oracle configurations without searching or model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=["all", "nas", "paramnet"], default="all")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2] / "LLM_ExpGym"
    sys.path.insert(0, str(repo))
    from expgym.task_tuning import list_hpobench_tasks, _load_hpobench, _hpobench_evaluate
    from demo_experiment import resolve_base_cost, resolve_cost_regime
    import ConfigSpace
    import numpy

    oracle_path = repo / "data/hpo_tuning/oracle3.json"
    oracle_bytes = oracle_path.read_bytes()
    oracle = json.loads(oracle_bytes.decode("utf-8"))["tasks"]
    report = {
        "classification": "Static/fake validation",
        "python": sys.executable,
        "python_version": platform.python_version(),
        "numpy": numpy.__version__,
        "configspace": version("ConfigSpace"),
        "oracle_sha256": hashlib.sha256(oracle_bytes).hexdigest(),
        "family": args.family,
        "tasks": [],
    }
    for name in list_hpobench_tasks():
        if args.family == "nas" and ":nasbench" not in name:
            continue
        if args.family == "paramnet" and ":paramnet:" not in name:
            continue
        started = time.monotonic()
        task = _load_hpobench(name)
        expected = oracle[name]
        assert "best_cost" in expected, name
        c_base = resolve_base_cost("tuning", argparse.Namespace(tuning_task=name))
        assert c_base == float(expected["best_cost"]), (name, c_base)
        regimes = {}
        for regime, beta in [("cost_free", None), ("cost_moderate", 10), ("cost_tight", 3)]:
            budget, baselines = resolve_cost_regime(argparse.Namespace(cost_regime=regime), c_base)
            assert budget == (None if beta is None else beta * c_base)
            assert baselines == (["no_budget"] if beta is None else ["time_aware"])
            regimes[regime] = {"beta": beta, "budget_seconds": budget, "baselines": baselines}
        config_space = []
        for hyperparameter in task.config_space.get_hyperparameters():
            record = {"name": hyperparameter.name, "class": type(hyperparameter).__name__}
            for key in ["lower", "upper", "default_value", "log", "choices", "weights"]:
                if hasattr(hyperparameter, key):
                    value = getattr(hyperparameter, key)
                    record[key] = list(value) if isinstance(value, tuple) else value
            config_space.append(record)
        config_space.sort(key=lambda item: item["name"])
        config = expected["best_config"]
        perf, cost = _hpobench_evaluate(task, config)
        perf_again, cost_again = _hpobench_evaluate(task, config)
        result = {
            "task": name,
            "fidelity": task.fidelity,
            "config": config,
            "config_space": config_space,
            "c_base_seconds": c_base,
            "cost_regimes": regimes,
            "perf": perf,
            "cost": cost,
            "oracle_perf": float(expected["best_perf"]),
            "oracle_cost": float(expected["best_cost"]),
            "finite": math.isfinite(perf) and math.isfinite(cost) and 0 <= perf <= 1 and cost >= 0,
            "fidelity_match": task.fidelity == expected["fidelity"],
            "perf_match": math.isclose(perf, float(expected["best_perf"]), rel_tol=1e-10, abs_tol=1e-10),
            "cost_match": math.isclose(cost, float(expected["best_cost"]), rel_tol=1e-8, abs_tol=1e-6),
            "deterministic": (perf, cost) == (perf_again, cost_again),
            "elapsed_seconds": time.monotonic() - started,
        }
        result["passed"] = all(result[key] for key in ["finite", "fidelity_match", "perf_match", "cost_match", "deterministic"])
        report["tasks"].append(result)
        print(json.dumps(result, sort_keys=True), flush=True)
    report["passed"] = bool(report["tasks"]) and all(item["passed"] for item in report["tasks"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
