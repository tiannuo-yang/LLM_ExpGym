#!/usr/bin/env python3
"""Run a parameterized ExpGym reproduction sweep.

By default this runs one low-friction real E2E trace:
one cheap OpenRouter model, the built-in tuning scenario, one cost regime.
Expand the matrix explicitly with --models, --scenarios, --cost-regimes,
--tuning-tasks, --search-indices, --audit-indices, and the rep counts.

The paper's main ranking matrix is expressible with explicit selector values:
6 models x 3 cost regimes x (9 HPOBench tasks x 3 reps + 35 search questions
+ 13 audit docs x 3 reps) = 1,818 traces.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
import random
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demo_experiment import (  # noqa: E402
    COST_REGIMES,
    _SCENARIOS,
    _call_scenario,
    _resolve_system_prompt,
    _resolve_tools,
    build_llm,
    resolve_base_cost,
    resolve_cost_regime,
)
from expgym.react_loop import build_system_prompt, run_react_loop  # noqa: E402

PAPER_MODELS: Dict[str, str] = {
    "dsv32": "deepseek/deepseek-v3.2",
    "gpt52": "openai/gpt-5.2",
    "gpt41": "openai/gpt-4.1",
    "gemini3flash": "google/gemini-3-flash",
    "haiku45": "anthropic/claude-haiku-4.5",
    "mistral_large": "mistralai/mistral-large",
}

PAPER_TUNING_TASKS = [
    "hpobench:paramnet:adult:steps",
    "hpobench:paramnet:higgs:steps",
    "hpobench:paramnet:letter:steps",
    "hpobench:nasbench101:A",
    "hpobench:nasbench101:B",
    "hpobench:nasbench101:C",
    "hpobench:nasbench201:cifar10-valid",
    "hpobench:nasbench201:cifar100",
    "hpobench:nasbench201:imagenet16-120",
]

PAPER_COST_REGIMES = ["cost_free", "cost_moderate", "cost_tight"]
SCENARIOS = ["tuning", "restricted_search", "evidence_audit"]
DEFAULT_MODEL = os.environ.get("EXPGYM_OPENROUTER_MODEL", "openai/gpt-4.1-nano")
DEFAULT_SCENARIOS = os.environ.get("EXPGYM_SCENARIOS", "tuning")
DEFAULT_COST_REGIMES = os.environ.get("EXPGYM_COST_REGIMES", "cost_tight")
DEFAULT_TUNING_TASKS = os.environ.get("EXPGYM_TUNING_TASKS", "neural_network_training")
DEFAULT_SEARCH_INDICES = os.environ.get("EXPGYM_SEARCH_INDICES", "0")
DEFAULT_AUDIT_INDICES = os.environ.get("EXPGYM_AUDIT_INDICES", "0")
REGIME_DIR = {
    "cost_free": "cost_free",
    "cost_moderate": "cost_moderate",
    "cost_tight": "cost_tight",
}


@dataclass(frozen=True)
class Job:
    scenario: str
    model_alias: str
    model_id: str
    cost_regime: str
    rep: int
    seed: int
    tuning_task: str = "neural_network_training"
    question_index: int = 0
    data_source: Optional[str] = None
    cc_split: str = "cc-large"
    hypothesis_order: Optional[List[str]] = None


def _default_key_file() -> Path:
    return Path(
        os.environ.get("OPENROUTER_API_KEY_FILE", REPO_ROOT.parent / "openrouter.key")
    )


def _load_api_key(path: Optional[Path]) -> Optional[str]:
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        return env_key.strip()
    if path is not None and path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return None


def _split_csv(value: str) -> List[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_indices(value: str) -> List[int]:
    value = value.strip()
    if ":" in value:
        start_s, end_s = value.split(":", 1)
        start = int(start_s or 0)
        end = int(end_s)
        return list(range(start, end))
    return [int(part) for part in _split_csv(value)]


def _sanitize(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return clean.strip("_") or "x"


def _parse_models(raw_models: str, overrides: Sequence[str]) -> List[Tuple[str, str]]:
    mapping = dict(PAPER_MODELS)
    for override in overrides:
        if "=" not in override:
            raise ValueError("--model-alias must be NAME=OPENROUTER_ID")
        name, model_id = override.split("=", 1)
        mapping[name.strip()] = model_id.strip()

    result = []
    for raw in _split_csv(raw_models):
        if raw in mapping:
            result.append((raw, mapping[raw]))
        else:
            result.append((_sanitize(raw), raw))
    return result


def _load_audit_orders(path: Path, reps: int) -> List[Optional[List[str]]]:
    if not path.exists():
        return [None for _ in range(reps)]
    data = json.loads(path.read_text(encoding="utf-8"))
    orders = data.get("orders", [])
    result: List[Optional[List[str]]] = []
    for rep in range(reps):
        result.append(orders[rep % len(orders)] if orders else None)
    return result


def _build_jobs(args: argparse.Namespace) -> List[Job]:
    models = _parse_models(args.models, args.model_alias)
    scenarios = _split_csv(args.scenarios)
    cost_regimes = _split_csv(args.cost_regimes)
    tuning_tasks = (
        PAPER_TUNING_TASKS
        if args.tuning_tasks == "all-hpobench"
        else _split_csv(args.tuning_tasks)
    )
    search_indices = _parse_indices(args.search_indices)
    audit_indices = _parse_indices(args.audit_indices)
    audit_orders = _load_audit_orders(args.audit_orders, args.audit_reps)

    for scenario in scenarios:
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario {scenario!r}; choose from {SCENARIOS}")
    for regime in cost_regimes:
        if regime not in COST_REGIMES:
            raise ValueError(f"Unknown cost regime {regime!r}; choose from {list(COST_REGIMES)}")

    jobs: List[Job] = []
    for model_alias, model_id in models:
        for cost_regime in cost_regimes:
            if "tuning" in scenarios:
                for task in tuning_tasks:
                    for rep in range(args.tuning_reps):
                        jobs.append(
                            Job(
                                scenario="tuning",
                                model_alias=model_alias,
                                model_id=model_id,
                                cost_regime=cost_regime,
                                rep=rep,
                                seed=args.seed + rep,
                                tuning_task=task,
                            )
                        )
            if "restricted_search" in scenarios:
                for idx in search_indices:
                    for rep in range(args.search_reps):
                        jobs.append(
                            Job(
                                scenario="restricted_search",
                                model_alias=model_alias,
                                model_id=model_id,
                                cost_regime=cost_regime,
                                rep=rep,
                                seed=args.seed + rep,
                                question_index=idx,
                                data_source=args.search_data_source,
                            )
                        )
            if "evidence_audit" in scenarios:
                for idx in audit_indices:
                    for rep in range(args.audit_reps):
                        jobs.append(
                            Job(
                                scenario="evidence_audit",
                                model_alias=model_alias,
                                model_id=model_id,
                                cost_regime=cost_regime,
                                rep=rep,
                                seed=args.seed + rep,
                                question_index=idx,
                                cc_split=args.cc_split,
                                hypothesis_order=audit_orders[rep],
                            )
                        )
    if args.shuffle:
        random.Random(args.seed).shuffle(jobs)
    if args.limit is not None:
        jobs = jobs[: args.limit]
    return jobs


def _trace_path(output_dir: Path, job: Job) -> Path:
    base = output_dir / f"{job.model_alias}_{REGIME_DIR[job.cost_regime]}" / "traces"
    if job.scenario == "tuning":
        name = f"tuning_{_sanitize(job.tuning_task)}_r{job.rep}_s{job.seed}.json"
    elif job.scenario == "restricted_search":
        source = _sanitize(job.data_source or "phantom_seed1")
        name = f"restricted_search_{source}_{job.question_index}_r{job.rep}_s{job.seed}.json"
    else:
        name = (
            f"evidence_audit_{_sanitize(job.cc_split)}_{job.question_index}"
            f"_r{job.rep}_s{job.seed}.json"
        )
    return base / name


def _namespace_for_job(args: argparse.Namespace, job: Job, api_key: str) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.scenario = job.scenario
    ns.backend = "openrouter"
    ns.model = job.model_id
    ns.api_key = api_key
    ns.system_prompt = None
    ns.temperature = (
        args.temperature_tuning
        if job.scenario == "tuning"
        else args.temperature_eval
    )
    ns.seed = job.seed
    ns.base_url = args.base_url
    ns.probes = 4
    ns.max_steps = args.max_steps
    ns.time_budget = None
    ns.max_evals = args.max_evals
    ns.cost_regime = job.cost_regime
    ns.beta = None
    ns.baseline = "both"
    ns.question_index = job.question_index
    ns.tuning_task = job.tuning_task
    ns.list_tuning_tasks = False
    ns.openrouter_referer = args.openrouter_referer
    ns.openrouter_title = args.openrouter_title
    ns.vllm_disable_thinking = False
    ns.data_source = job.data_source
    ns.cc_split = job.cc_split
    ns.hypothesis_order = job.hypothesis_order
    return ns


def _answer_evaluator_for(scenario: Dict[str, object], ns: argparse.Namespace):
    builder = scenario.get("build_answer_evaluator")
    if builder is None:
        return None
    candidates = [
        {
            "data_source": getattr(ns, "data_source", None),
            "cc_split": getattr(ns, "cc_split", None),
        },
        {"data_source": getattr(ns, "data_source", None)},
        {"cc_split": getattr(ns, "cc_split", None)},
        {},
    ]
    for kwargs in candidates:
        clean = {k: v for k, v in kwargs.items() if v is not None}
        try:
            return builder(ns.question_index, **clean)
        except TypeError:
            continue
    return builder(ns.question_index)


def _run_job(args: argparse.Namespace, job: Job, api_key: str) -> Dict[str, Any]:
    ns = _namespace_for_job(args, job, api_key)
    random.seed(ns.seed)
    scenario = _SCENARIOS[job.scenario]
    c_base = resolve_base_cost(job.scenario, ns)
    time_budget, baselines = resolve_cost_regime(ns, c_base)
    if len(baselines) != 1:
        raise RuntimeError(f"Expected one baseline for {job.cost_regime}, got {baselines}")
    mode = baselines[0]
    include_overhead = mode == "time_focus"
    include_cost = mode == "time_aware"
    system_prompt = _resolve_system_prompt(scenario, include_overhead, ns)
    tools = _resolve_tools(scenario, ns)
    llm = build_llm(ns.backend, [], ns, system_prompt=system_prompt)
    context = _call_scenario(scenario["build_context"], include_overhead, ns)
    instruction_notes = _call_scenario(
        scenario["build_instruction_notes"], include_overhead, ns
    )
    answer_evaluator = _answer_evaluator_for(scenario, ns)
    result = run_react_loop(
        llm=llm,
        tools=tools,
        time_budget=time_budget,
        max_steps=ns.max_steps,
        max_evals=ns.max_evals,
        context=context,
        instruction_notes=instruction_notes or [],
        system_prompt=system_prompt or build_system_prompt(),
        include_overhead_in_observation=include_overhead,
        include_cost_in_observation=include_cost,
        answer_evaluator=answer_evaluator,
    )
    result["job"] = asdict(job)
    result["cost_regime_resolved"] = {
        "mode": mode,
        "c_base": c_base,
        "time_budget": time_budget,
    }
    result["score_check"] = _score_check(result, tools, answer_evaluator)
    return result


def _parse_tool_perf(tool_result: Any) -> Optional[float]:
    if isinstance(tool_result, tuple) and len(tool_result) == 2:
        first, _second = tool_result
        return float(first) if isinstance(first, (int, float)) else None
    if isinstance(tool_result, tuple) and len(tool_result) == 3:
        _output, perf, _overhead = tool_result
        return float(perf) if perf is not None else None
    return None


def _is_zero_score_tool_result(tool_result: Any) -> bool:
    if not isinstance(tool_result, tuple) or len(tool_result) not in {2, 3}:
        return False
    output = tool_result[0]
    if not isinstance(output, str):
        return False
    text = output.lower()
    zero_markers = [
        "invalid",
        "degenerate",
        "out of range",
        "missing",
        "tool error",
    ]
    return any(marker in text for marker in zero_markers)


def _score_check(
    result: Dict[str, Any],
    tools: Dict[str, Callable[[str], Any]],
    answer_evaluator: Optional[Callable[..., Any]],
) -> Dict[str, Any]:
    answer = result.get("answer")
    if not answer:
        return {"ok": False, "reason": "missing answer"}
    if answer_evaluator is not None:
        try:
            recomputed = answer_evaluator(answer, result.get("tool_records", []))
        except TypeError:
            recomputed = answer_evaluator(answer)
        if isinstance(recomputed, dict):
            metrics = result.get("answer_metrics") or {}
            ok = _metrics_close(metrics, recomputed)
            primary = recomputed.get("label_acc")
            if primary is not None:
                ok = ok and _float_close(result.get("answer_perf"), primary)
            return {
                "ok": ok,
                "recomputed_metrics": recomputed,
                "reported_metrics": metrics,
                "reported_perf": result.get("answer_perf"),
            }
        ok = _float_close(result.get("answer_perf"), recomputed)
        return {
            "ok": ok,
            "recomputed_perf": recomputed,
            "reported_perf": result.get("answer_perf"),
        }

    if not tools:
        return {"ok": False, "reason": "no tools available for score recompute"}
    tool = next(iter(tools.values()))
    try:
        tool_result = tool(answer)
        recomputed = _parse_tool_perf(tool_result)
    except Exception as exc:
        return {"ok": False, "reason": f"tool recompute failed: {exc}"}
    if (
        recomputed is None
        and _float_close(result.get("answer_perf"), 0.0)
        and _is_zero_score_tool_result(tool_result)
    ):
        recomputed = 0.0
    if recomputed is None or result.get("answer_perf") is None:
        return {
            "ok": False,
            "reason": "missing numeric score",
            "recomputed_perf": recomputed,
            "reported_perf": result.get("answer_perf"),
        }
    ok = _float_close(result.get("answer_perf"), recomputed)
    return {
        "ok": ok,
        "recomputed_perf": recomputed,
        "reported_perf": result.get("answer_perf"),
    }


def _float_close(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return actual == expected
    try:
        return math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9)
    except (TypeError, ValueError):
        return False


def _metrics_close(actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
    if set(actual) != set(expected):
        return False
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
            if not _float_close(actual_value, expected_value):
                return False
        elif actual_value != expected_value:
            return False
    return True


def _preflight(args: argparse.Namespace, jobs: Sequence[Job]) -> None:
    if args.dry_run or args.skip_preflight:
        return
    errors: List[str] = []
    if any(j.scenario == "tuning" and j.tuning_task.startswith("hpobench:") for j in jobs):
        hpobench_setup = REPO_ROOT / "data" / "hpo_tuning" / "HPOBench" / "setup.py"
        if not hpobench_setup.exists():
            errors.append(
                "HPOBench source is missing. Run: python scripts/download_data.py --auto-only"
            )
        try:
            import ConfigSpace  # noqa: F401
        except Exception:
            errors.append(
                "HPOBench Python deps are missing. Run: bash scripts/recreate_expgym_env.sh"
            )
        if any(j.tuning_task.startswith("hpobench:nasbench101:") for j in jobs):
            try:
                import nasbench  # noqa: F401
                import tabular_benchmarks  # noqa: F401
            except Exception:
                errors.append(
                    "NASBench101 deps are missing. Run: bash scripts/recreate_expgym_env.sh"
                )
    if any(j.scenario == "restricted_search" for j in jobs):
        from expgym.task_restricted_search import CORPUS_DIR, QA_DIR

        if not Path(QA_DIR).is_dir() or not Path(CORPUS_DIR).is_dir():
            errors.append(
                "Phantom Wiki is missing. Run: python scripts/download_data.py --auto-only"
            )
        try:
            import pyarrow  # noqa: F401
        except Exception:
            errors.append(
                "pyarrow is missing for Phantom Wiki parquet files. "
                "Run: python -m pip install -r requirements-data.txt"
            )
    if any(j.scenario == "evidence_audit" for j in jobs):
        from expgym.task_evidence_audit import EVIDENCE_PATH, HINTS_PATH
        from scripts.download_data import CONTRACT_NLI_PAGE

        if not Path(EVIDENCE_PATH).is_file() or not Path(HINTS_PATH).is_file():
            errors.append(
                "ContractNLI segments are missing. ExpGym does not mirror this archive; "
                f"download it from the official page after reviewing the terms: {CONTRACT_NLI_PAGE}\n"
                "  Then set CONTRACT_NLI_ARCHIVE=/path/to/contract-nli.zip in .env, or run:\n"
                "  python scripts/download_data.py --contract-nli-archive /path/to/contract-nli.zip"
            )
    if errors:
        raise SystemExit("Preflight failed:\n- " + "\n- ".join(errors))


def _print_dry_run(jobs: Sequence[Job], args: argparse.Namespace) -> None:
    counts: Dict[str, int] = {}
    for job in jobs:
        counts[job.scenario] = counts.get(job.scenario, 0) + 1
    print("ExpGym sweep dry-run")
    print(f"output_dir: {args.output_dir}")
    print(f"jobs: {len(jobs)}")
    for scenario in SCENARIOS:
        print(f"- {scenario}: {counts.get(scenario, 0)}")
    print()
    print("First jobs:")
    for job in jobs[: min(10, len(jobs))]:
        print(json.dumps(asdict(job), sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.environ.get("EXPGYM_OUTPUT_DIR", "budget_sweep_results/e2e")),
    )
    parser.add_argument(
        "--models",
        default=os.environ.get("EXPGYM_MODELS", DEFAULT_MODEL),
        help=(
            "Comma-separated aliases or OpenRouter IDs. Default: "
            f"{DEFAULT_MODEL}. Paper aliases: {','.join(PAPER_MODELS.keys())}."
        ),
    )
    parser.add_argument(
        "--model-alias",
        action="append",
        default=[],
        help="Override/add model alias as NAME=OPENROUTER_MODEL_ID.",
    )
    parser.add_argument("--scenarios", default=DEFAULT_SCENARIOS)
    parser.add_argument("--cost-regimes", default=DEFAULT_COST_REGIMES)
    parser.add_argument(
        "--tuning-tasks",
        default=DEFAULT_TUNING_TASKS,
        help=(
            "Comma-separated tuning tasks. Default: neural_network_training. "
            "Use all-hpobench for the 9 HPOBench tasks from the paper."
        ),
    )
    parser.add_argument("--search-indices", default=DEFAULT_SEARCH_INDICES)
    parser.add_argument("--search-data-source", default="phantom_seed1")
    parser.add_argument("--audit-indices", default=DEFAULT_AUDIT_INDICES)
    parser.add_argument("--cc-split", default="cc-large")
    parser.add_argument(
        "--audit-orders",
        type=Path,
        default=REPO_ROOT / "configs" / "audit_hypothesis_orders.json",
    )
    parser.add_argument("--tuning-reps", type=int, default=1)
    parser.add_argument("--search-reps", type=int, default=1)
    parser.add_argument("--audit-reps", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1206)
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--max-evals", type=int, default=30)
    parser.add_argument("--temperature-tuning", type=float, default=0.7)
    parser.add_argument("--temperature-eval", type=float, default=0.0)
    parser.add_argument("--api-key-file", type=Path, default=_default_key_file())
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENROUTER_BASE_URL") or os.environ.get("EXPGYM_BASE_URL"),
    )
    parser.add_argument("--openrouter-referer", default=None)
    parser.add_argument("--openrouter-title", default="ExpGym sweep")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--shuffle", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    jobs = _build_jobs(args)
    if args.dry_run:
        _print_dry_run(jobs, args)
        return 0
    api_key = _load_api_key(args.api_key_file)
    if not api_key:
        raise SystemExit(
            "OPENROUTER_API_KEY is not set and no key file was found. "
            "Set OPENROUTER_API_KEY or pass --api-key-file PATH."
        )
    _preflight(args, jobs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    failures: List[Tuple[Job, str]] = []
    for idx, job in enumerate(jobs, start=1):
        path = _trace_path(args.output_dir, job)
        if args.resume and path.exists():
            print(f"[{idx}/{len(jobs)}] skip existing {path}")
            continue
        print(f"[{idx}/{len(jobs)}] run {job.scenario} {job.model_alias} {job.cost_regime}")
        start = time.time()
        try:
            result = _run_job(args, job, api_key)
            result["wall_time_seconds"] = time.time() - start
            if not result["score_check"].get("ok"):
                raise RuntimeError(f"score check failed: {result['score_check']}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
            print(f"  wrote {path} score_check=ok")
        except Exception as exc:
            failures.append((job, str(exc)))
            print(f"  ERROR: {exc}", file=sys.stderr)
            if not args.resume:
                break
    if failures:
        print("Failures:")
        for job, error in failures:
            print(json.dumps(asdict(job), sort_keys=True), error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
