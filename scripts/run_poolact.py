#!/usr/bin/env python3
"""Run one ExpGym item with naive, cached, or PoolAct parallel agents."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional

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
from expgym.extras.parallel_cache import (  # noqa: E402
    AgentClock,
    SharedObservationCache,
    wrap_tools_with_cache,
)
from expgym.poolact import (  # noqa: E402
    POOLACT_PROTOCOL_VERSION,
    PoolActCoordinator,
    aggregate_results,
    run_agents_parallel,
)
from expgym.react_loop import build_system_prompt, run_react_loop  # noqa: E402
from scripts.run_paper_sweep import _score_check  # noqa: E402


STRATEGIES = ("naive", "cached", "poolact")


def _split_strategies(value: str) -> List[str]:
    strategies = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [item for item in strategies if item not in STRATEGIES]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown strategies {unknown}; choose from {STRATEGIES}"
        )
    if not strategies:
        raise argparse.ArgumentTypeError("at least one strategy is required")
    return strategies


def _parse_indices(value: str) -> List[int]:
    """Parse ``0``, ``0,2,7``, or the half-open range ``0:5``."""
    raw = value.strip()
    if not raw:
        raise argparse.ArgumentTypeError("--questions must not be empty")
    try:
        if ":" in raw:
            if raw.count(":") != 1:
                raise ValueError
            start_text, end_text = raw.split(":", 1)
            start = int(start_text or 0)
            end = int(end_text)
            indices = list(range(start, end))
        else:
            indices = [int(part.strip()) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--questions must be an index, comma list, or half-open range such as 0:5"
        ) from exc
    if not indices:
        raise argparse.ArgumentTypeError("--questions selected no items")
    if any(index < 0 for index in indices):
        raise argparse.ArgumentTypeError("question indices must be non-negative")
    # Keep the first occurrence so accidental duplicates do not spend twice.
    return list(dict.fromkeys(indices))


def _default_model() -> str:
    return (
        os.environ.get("SUB2API_MODEL")
        or os.environ.get("EXPGYM_MODEL")
        or os.environ.get("EXPGYM_OPENROUTER_MODEL")
        or "openai/gpt-4.1-nano"
    )


def _load_api_key(args: argparse.Namespace) -> Optional[str]:
    if args.api_key:
        return args.api_key.strip()
    if args.backend == "sub2api":
        env_names = ("SUB2API_API_KEY", "OPENROUTER_API_KEY")
    elif args.backend == "openai":
        env_names = ("OPENAI_API_KEY", "OPENROUTER_API_KEY")
    elif args.backend == "gemini":
        env_names = ("GEMINI_API_KEY", "OPENROUTER_API_KEY")
    else:
        env_names = ("OPENROUTER_API_KEY",)
    for name in env_names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    if args.api_key_file and args.api_key_file.is_file():
        return args.api_key_file.read_text(encoding="utf-8").strip()
    return None


def _agent_cache_key(base: Optional[str], strategy: str, agent_id: int) -> Optional[str]:
    if not base:
        return None
    digest = hashlib.sha256(
        f"{base}\0{strategy}\0{agent_id}".encode("utf-8")
    ).hexdigest()[:24]
    prefix = "".join(
        character if character.isalnum() or character in "_.-" else "-"
        for character in base
    ).strip("._-") or "expgym"
    suffix = f"-{strategy}-a{agent_id}-{digest}"
    return prefix[: 64 - len(suffix)] + suffix


def _answer_evaluator_for(
    scenario: Dict[str, object], args: argparse.Namespace
) -> Optional[Callable]:
    builder = scenario.get("build_answer_evaluator")
    if builder is None:
        return None
    candidates = [
        {"data_source": args.data_source, "cc_split": args.cc_split},
        {"data_source": args.data_source},
        {"cc_split": args.cc_split},
        {},
    ]
    for candidate in candidates:
        kwargs = {key: value for key, value in candidate.items() if value is not None}
        try:
            return builder(args.question_index, **kwargs)
        except TypeError:
            continue
    return builder(args.question_index)


def _agent_namespace(
    args: argparse.Namespace,
    strategy: str,
    agent_id: int,
    api_key: Optional[str],
) -> argparse.Namespace:
    namespace = argparse.Namespace(**vars(args))
    namespace.seed = args.seed + agent_id
    namespace.api_key = api_key
    namespace.prompt_cache_key = _agent_cache_key(
        args.prompt_cache_key,
        strategy,
        agent_id,
    )
    namespace.system_prompt = None
    namespace.hypothesis_order = None
    namespace.openrouter_referer = args.openrouter_referer
    namespace.openrouter_title = args.openrouter_title
    namespace.vllm_disable_thinking = args.vllm_disable_thinking
    namespace.list_tuning_tasks = False
    namespace.probes = args.probes
    namespace.time_budget = None
    namespace.beta = None
    namespace.baseline = "time_aware"
    return namespace


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(value, handle, indent=2, ensure_ascii=False, default=str)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _implementation_manifest() -> Dict[str, str]:
    files = {
        "runner": REPO_ROOT / "scripts" / "run_poolact.py",
        "api": REPO_ROOT / "expgym" / "poolact.py",
        "shared_state": REPO_ROOT / "expgym" / "extras" / "parallel_cache.py",
        "react_loop": REPO_ROOT / "expgym" / "react_loop.py",
    }
    return {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in files.items()
    }


def _resolved_config(
    args: argparse.Namespace,
    time_budget: Optional[float],
) -> Dict[str, Any]:
    return {
        "poolact_protocol": POOLACT_PROTOCOL_VERSION,
        "backend": args.backend,
        "model": args.model,
        "scenario": args.scenario,
        "tuning_task": args.tuning_task,
        "question_index": args.question_index,
        "data_source": args.data_source,
        "cc_split": args.cc_split,
        "cost_regime": args.cost_regime,
        "time_budget": time_budget,
        "strategies": args.strategies,
        "agents": args.agents,
        "seed": args.seed,
        "temperature": args.temperature,
        "max_steps": args.max_steps,
        "max_evals": args.max_evals,
        "max_context_tokens": args.max_context_tokens,
    }


def _batch_strategy_metrics(
    items: Dict[str, Dict[str, Dict[str, Any]]],
    strategies: List[str],
) -> Dict[str, Dict[str, Any]]:
    metrics: Dict[str, Dict[str, Any]] = {}
    for strategy in strategies:
        scores = [
            item[strategy].get("answer_perf")
            for item in items.values()
            if strategy in item
        ]
        numeric_scores = [
            float(score) for score in scores if isinstance(score, (int, float))
        ]
        metrics[strategy] = {
            "completed_items": len(scores),
            "scored_items": len(numeric_scores),
            "mean_answer_perf": (
                sum(numeric_scores) / len(numeric_scores) if numeric_scores else None
            ),
        }
    return metrics


def _run_strategy(
    args: argparse.Namespace,
    strategy: str,
    api_key: Optional[str],
    time_budget: Optional[float],
    mode: str,
) -> Dict[str, Any]:
    scenario = _SCENARIOS[args.scenario]
    cache = SharedObservationCache() if strategy == "cached" else None
    coordinator = (
        PoolActCoordinator(args.agents) if strategy == "poolact" else None
    )

    def run_agent(agent_id: int) -> Dict[str, Any]:
        namespace = _agent_namespace(args, strategy, agent_id, api_key)
        tools = _resolve_tools(scenario, namespace)
        direct_tools = tools
        clock = None
        augmenter = None
        pre_tool_hook = None
        reasoning_lock = None
        if strategy == "cached":
            clock = AgentClock()
            tools = wrap_tools_with_cache(
                tools,
                cache,
                clock=clock,
                overhead_scale=1.0,
            )
        elif strategy == "poolact":
            runtime = coordinator.bind_tools(tools, agent_id)
            tools = runtime.tools
            clock = runtime.clock
            augmenter = runtime.observation_augmenter
            pre_tool_hook = runtime.pre_tool_hook
            reasoning_lock = runtime.reasoning_lock

        include_overhead = mode == "time_focus"
        include_cost = mode == "time_aware"
        system_prompt = _resolve_system_prompt(
            scenario,
            include_overhead,
            namespace,
        ) or build_system_prompt()
        context = _call_scenario(
            scenario["build_context"],
            include_overhead,
            namespace,
        )
        instruction_notes = _call_scenario(
            scenario["build_instruction_notes"],
            include_overhead,
            namespace,
        )
        fake_plan = _call_scenario(
            scenario["build_fake_plan"],
            args.probes,
            namespace,
        )
        llm = build_llm(
            args.backend,
            fake_plan,
            namespace,
            system_prompt=system_prompt,
        )
        answer_evaluator = _answer_evaluator_for(scenario, namespace)
        started = time.perf_counter()
        result = run_react_loop(
            llm=llm,
            tools=tools,
            time_budget=time_budget,
            max_steps=args.max_steps,
            max_evals=args.max_evals,
            max_context_tokens=args.max_context_tokens,
            context=context,
            instruction_notes=instruction_notes or [],
            system_prompt=system_prompt,
            include_overhead_in_observation=include_overhead,
            include_cost_in_observation=include_cost,
            answer_evaluator=answer_evaluator,
            observation_augmenter=augmenter,
            agent_clock=clock,
            pre_tool_hook=pre_tool_hook,
            llm_lock=reasoning_lock,
            capture_trace_v2=False,
        )
        result["wall_time_seconds"] = time.perf_counter() - started
        result["agent_id"] = agent_id
        result["seed"] = namespace.seed
        result["strategy"] = strategy
        result["score_check"] = _score_check(
            result,
            direct_tools,
            answer_evaluator,
        )
        return result

    agent_results = run_agents_parallel(args.agents, run_agent)
    aggregate_evaluator = _answer_evaluator_for(scenario, args)
    aggregate = aggregate_results(
        args.scenario,
        agent_results,
        answer_evaluator=aggregate_evaluator,
    )
    state: Optional[Dict[str, Any]] = None
    if cache is not None:
        state = {"cache": cache.stats()}
    if coordinator is not None:
        state = coordinator.stats()
    return {
        "strategy": strategy,
        "agents": args.agents,
        "aggregate": aggregate,
        "shared_state": state,
        "agent_results": agent_results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=["fake", "openai", "gemini", "openrouter", "sub2api", "vllm"],
        default=os.environ.get("EXPGYM_BACKEND", "fake"),
    )
    parser.add_argument("--model", default=_default_model())
    parser.add_argument("--api-key", default=None)
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=Path(os.environ.get("OPENROUTER_API_KEY_FILE", "../openrouter.key")),
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("EXPGYM_BASE_URL") or os.environ.get("SUB2API_BASE_URL"),
    )
    parser.add_argument("--prompt-cache-key", default=os.environ.get("EXPGYM_PROMPT_CACHE_KEY"))
    parser.add_argument("--openrouter-referer", default=None)
    parser.add_argument("--openrouter-title", default="ExpGym PoolAct")
    parser.add_argument("--vllm-disable-thinking", action="store_true")

    parser.add_argument("--scenario", choices=sorted(_SCENARIOS), default="tuning")
    parser.add_argument("--tuning-task", "--task", default="neural_network_training")
    question_selector = parser.add_mutually_exclusive_group()
    question_selector.add_argument("--question-index", type=int, default=None)
    question_selector.add_argument(
        "--questions",
        type=_parse_indices,
        default=None,
        metavar="INDICES",
        help="Batch selector: 0, 0,2,7, or half-open range 0:5",
    )
    parser.add_argument("--data-source", default="phantom_seed1")
    parser.add_argument("--cc-split", choices=["cc-small", "cc-medium", "cc-large"], default="cc-large")
    parser.add_argument(
        "--cost-regime",
        choices=["cost_tight", "cost_moderate", "cost_free"],
        default="cost_tight",
    )

    parser.add_argument("--strategies", type=_split_strategies, default=["poolact"])
    parser.add_argument("--agents", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1206)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--max-evals", type=int, default=30)
    parser.add_argument("--max-context-tokens", type=int, default=None)
    parser.add_argument("--probes", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/poolact"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.agents < 1:
        raise SystemExit("--agents must be at least 1")
    if args.question_index is not None and args.question_index < 0:
        raise SystemExit("--question-index must be non-negative")
    if args.questions is not None and args.scenario == "tuning":
        raise SystemExit("--questions is only valid for restricted_search or evidence_audit")
    question_indices = (
        args.questions
        if args.questions is not None
        else [args.question_index if args.question_index is not None else 0]
    )
    api_key = _load_api_key(args)
    if not args.dry_run and args.backend not in {"fake", "vllm"} and not api_key:
        raise SystemExit(
            f"No API key configured for backend={args.backend}. "
            "Set OPENROUTER_API_KEY/SUB2API_API_KEY or pass --api-key."
        )

    c_base = resolve_base_cost(args.scenario, args)
    time_budget, baselines = resolve_cost_regime(args, c_base)
    if len(baselines) != 1:
        raise SystemExit("PoolAct requires one named --cost-regime")
    mode = baselines[0]
    if args.dry_run:
        configs = []
        for question_index in question_indices:
            item_args = argparse.Namespace(**vars(args))
            item_args.question_index = question_index
            item_args.questions = None
            configs.append(_resolved_config(item_args, time_budget))
        preview: object = configs[0] if args.questions is None else {
            "batch": True,
            "question_indices": question_indices,
            "items": configs,
        }
        print(json.dumps(preview, indent=2, sort_keys=True))
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    implementation = _implementation_manifest()
    batch_items: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for question_index in question_indices:
        item_args = argparse.Namespace(**vars(args))
        item_args.question_index = question_index
        item_args.questions = None
        config = _resolved_config(item_args, time_budget)
        item_output_dir = (
            args.output_dir / f"item_{question_index}"
            if args.questions is not None
            else args.output_dir
        )
        completed: Dict[str, Any] = {}
        for strategy in args.strategies:
            result_path = item_output_dir / strategy / "result.json"
            if args.resume and result_path.is_file():
                existing = json.loads(result_path.read_text(encoding="utf-8"))
                agent_files_complete = all(
                    (
                        item_output_dir
                        / strategy
                        / "agents"
                        / f"agent_{agent_id}.json"
                    ).is_file()
                    for agent_id in range(args.agents)
                )
                if (
                    existing.get("config") == config
                    and existing.get("implementation_sha256") == implementation
                    and agent_files_complete
                ):
                    completed[strategy] = existing
                    print(f"[resume] item={question_index} strategy={strategy}: {result_path}")
                    continue
                print(
                    f"[resume] item={question_index} strategy={strategy}: "
                    "run snapshot changed or incomplete; rerunning"
                )
            print(
                f"[run] item={question_index} strategy={strategy} "
                f"agents={args.agents} scenario={args.scenario}"
            )
            result = _run_strategy(
                item_args,
                strategy,
                api_key,
                time_budget,
                mode,
            )
            result["config"] = config
            result["implementation_sha256"] = implementation
            # The strategy-level result is the completion marker.  Write all
            # per-agent traces first so --resume cannot accept a partial run.
            for agent in result["agent_results"]:
                _atomic_json(
                    item_output_dir
                    / strategy
                    / "agents"
                    / f"agent_{agent['agent_id']}.json",
                    agent,
                )
            _atomic_json(result_path, result)
            completed[strategy] = result
            aggregate = result["aggregate"]
            print(
                "POOLACT RESULT | "
                f"item={question_index} | strategy={strategy} | agents={args.agents} | "
                f"scenario={args.scenario} | answer_perf={aggregate.get('answer_perf')} | "
                f"output={result_path}"
            )

        item_summary = {
            "config": config,
            "implementation_sha256": implementation,
            "strategies": {
                strategy: result.get("aggregate")
                for strategy, result in completed.items()
            },
        }
        _atomic_json(item_output_dir / "summary.json", item_summary)
        batch_items[str(question_index)] = item_summary["strategies"]

    if args.questions is not None:
        batch_config = _resolved_config(
            argparse.Namespace(**{**vars(args), "question_index": None}),
            time_budget,
        )
        batch_config.pop("question_index")
        batch_config["question_indices"] = question_indices
        _atomic_json(
            args.output_dir / "summary.json",
            {
                "config": batch_config,
                "implementation_sha256": implementation,
                "items": batch_items,
                "strategy_metrics": _batch_strategy_metrics(
                    batch_items,
                    args.strategies,
                ),
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
