import argparse
import json
import os
import statistics
import traceback
import gc
from multiprocessing import Pool
from typing import Dict, Any, List, Tuple

from expgym.task_tuning import list_hpobench_tasks, _load_hpobench, _hpobench_evaluate

DEFAULT_SEED = 1206
DEFAULT_SAMPLES = 1000
DEFAULT_WORKERS = 4
OUTPUT_PATH = os.path.join("data", "hpo_tuning", "oracle3.json")
NASBENCH101_FILE = os.path.join(
    os.path.expanduser("~/.local/share/hpobench"),
    "nasbench_101",
    "nasbench_full.tfrecord",
)


def _summarize_task(task_name: str, samples: int, seed: int) -> Dict[str, Any]:
    task = _load_hpobench(task_name)
    task.config_space.seed(seed)

    perfs: List[float] = []
    costs: List[float] = []
    best_perf = None
    best_cost = None
    best_config = None

    invalid_perf_count = 0
    for _ in range(samples):
        config = dict(task.config_space.sample_configuration())
        perf, cost = _hpobench_evaluate(task, config)
        if not isinstance(perf, (int, float)):
            invalid_perf_count += 1
            perf = 0.0
        else:
            perf = float(perf)
        try:
            cost = float(cost)
        except (TypeError, ValueError):
            cost = 0.0
        perfs.append(perf)
        costs.append(cost)
        if best_perf is None or perf > best_perf:
            best_perf = perf
            best_cost = cost
            best_config = config

    rounded = [round(p, 6) for p in perfs]
    unique_perf_count = len(set(rounded))

    return {
        "task": task_name,
        "seed": seed,
        "samples": samples,
        "fidelity": task.fidelity,
        "best_perf": best_perf,
        "best_cost": best_cost,
        "best_config": best_config,
        "mean_perf": statistics.mean(perfs),
        "median_perf": statistics.median(perfs),
        "min_perf": min(perfs),
        "max_perf": max(perfs),
        "unique_perf_count": unique_perf_count,
        "unique_perf_ratio": unique_perf_count / max(1, samples),
        "mean_cost": statistics.mean(costs),
        "median_cost": statistics.median(costs),
        "invalid_perf_count": invalid_perf_count,
    }


def _summarize_task_for_pool(args: Tuple[str, int, int]) -> Tuple[str, Dict[str, Any]]:
    task_name, samples, seed = args
    return task_name, _summarize_task(task_name, samples, seed)


def _is_nas_task(task_name: str) -> bool:
    return task_name.startswith("hpobench:nasbench")


def _sanitize_numeric_fields(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize legacy string-encoded numerics loaded from older oracle files."""
    numeric_keys = (
        "best_perf",
        "best_cost",
        "mean_perf",
        "median_perf",
        "min_perf",
        "max_perf",
        "unique_perf_ratio",
        "mean_cost",
        "median_cost",
    )
    for key in numeric_keys:
        value = entry.get(key)
        if isinstance(value, str):
            try:
                entry[key] = float(value)
            except ValueError:
                pass
    unique_count = entry.get("unique_perf_count")
    if isinstance(unique_count, str):
        try:
            entry["unique_perf_count"] = int(float(unique_count))
        except ValueError:
            pass
    invalid_count = entry.get("invalid_perf_count")
    if isinstance(invalid_count, str):
        try:
            entry["invalid_perf_count"] = int(float(invalid_count))
        except ValueError:
            pass
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute HPOBench oracle summaries.")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--output", default=OUTPUT_PATH)
    parser.add_argument("--log", default="/tmp/hpobench_oracle.log")
    parser.add_argument(
        "--tasks",
        nargs="*",
        default=None,
        help="Optional list of task names to run (space-separated).",
    )
    args = parser.parse_args()

    tasks = list_hpobench_tasks()
    if not os.path.exists(NASBENCH101_FILE):
        tasks = [t for t in tasks if not t.startswith("hpobench:nasbench101:")]
    if args.tasks:
        selected = set(args.tasks)
        tasks = [t for t in tasks if t in selected]
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as handle:
            results: Dict[str, Any] = json.load(handle)
        results.setdefault("tasks", {})
        results.setdefault("errors", {})
        for task_name in list(results["tasks"].keys()):
            results["tasks"][task_name] = _sanitize_numeric_fields(
                results["tasks"][task_name]
            )
        results["seed"] = args.seed
        results["samples"] = args.samples
    else:
        results = {
            "seed": args.seed,
            "samples": args.samples,
            "tasks": {},
            "errors": {},
        }

    def _log(msg: str) -> None:
        with open(args.log, "a", encoding="utf-8") as handle:
            handle.write(msg + "\n")

    def _write_results() -> None:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(results, handle, indent=2, sort_keys=True)

    pending = [t for t in tasks if t not in results["tasks"]]
    light_tasks = [t for t in pending if not _is_nas_task(t)]
    nas_tasks = [t for t in pending if _is_nas_task(t)]

    for task_name in light_tasks:
        _log(f"[start] {task_name}")
    if args.workers <= 1:
        for task_name in light_tasks:
            try:
                results["tasks"][task_name] = _summarize_task(
                    task_name, args.samples, args.seed
                )
                results["errors"].pop(task_name, None)
                _log(f"[done] {task_name}")
            except Exception as exc:  # pragma: no cover - diagnostic path
                results["errors"][task_name] = str(exc)
                _log(f"[error] {task_name}: {exc}")
                _log(traceback.format_exc())
            finally:
                _write_results()
                gc.collect()
    elif light_tasks:
        work_items = [(task_name, args.samples, args.seed) for task_name in light_tasks]
        with Pool(processes=args.workers) as pool:
            for task_name, summary in pool.imap_unordered(_summarize_task_for_pool, work_items):
                results["tasks"][task_name] = summary
                results["errors"].pop(task_name, None)
                _log(f"[done] {task_name}")
                _write_results()

    # NAS tasks are memory-heavy; run sequentially to avoid worker OOM kills.
    for task_name in nas_tasks:
        _log(f"[start] {task_name}")
        try:
            results["tasks"][task_name] = _summarize_task(
                task_name, args.samples, args.seed
            )
            results["errors"].pop(task_name, None)
            _log(f"[done] {task_name}")
        except Exception as exc:  # pragma: no cover - diagnostic path
            results["errors"][task_name] = str(exc)
            _log(f"[error] {task_name}: {exc}")
            _log(traceback.format_exc())
        finally:
            _write_results()
            gc.collect()

    _write_results()
    print(f"Wrote {args.output} with {len(tasks)} tasks")


if __name__ == "__main__":
    main()
