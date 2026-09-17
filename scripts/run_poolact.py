#!/usr/bin/env python3
"""Run one ExpGym item with naive, cached, or PoolAct parallel agents."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
    _SCENARIOS,
    _add_generation_arguments,
    _generation_options,
    _loop_options,
    _call_scenario,
    _resolve_context,
    _resolve_answer_evaluator,
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
    aggregate_results as _original_aggregate_results,
    run_agents_parallel,
)
from expgym.react_loop import build_system_prompt, run_react_loop  # noqa: E402
from scripts.run_paper_sweep import _score_check, _score_result  # noqa: E402
from expgym.evaluation_identity import bind_evaluation_identity, evaluation_identity  # noqa: E402
from expgym.trace_v2 import source_tree_sha256  # noqa: E402
from expgym.terminal_evidence import TerminalEvidence  # noqa: E402
from expgym.missing_final import (  # noqa: E402
    mark_loop_return, terminal_publishable, aggregate_terminal, aggregate_publishable, canonical as _terminal_canonical,
)


STRATEGIES = ("naive", "cached", "poolact")


def aggregate_results(scenario, results, *, answer_evaluator=None):
    return aggregate_terminal(scenario, results, answer_evaluator=answer_evaluator,
                              original_aggregate=_original_aggregate_results)


def validate_terminal_pool(result, tools, answer_evaluator, *, scenario, expected_agents):
    """Independent per-agent score and whole-pool aggregation recheck only."""
    from scripts.run_paper_sweep import validate_terminal_result
    agents = result.get("agent_results") if type(result) is dict else None
    if (type(expected_agents) is not int or expected_agents < 1 or type(agents) is not list
            or len(agents) != expected_agents or any(type(v) is not dict or type(v.get("agent_id")) is not int for v in agents)
            or [v["agent_id"] for v in agents] != list(range(expected_agents))):
        return {"schema_version": "expgym.independent-pool-terminal-check.v1", "execution_complete": False,
                "score_complete": False, "terminal_classification": "integrity_failure", "reason": "incomplete_expected_agents"}
    checks = [validate_terminal_result(agent, tools, answer_evaluator, scenario=scenario) for agent in agents]
    if not all(check["execution_complete"] for check in checks):
        return {"schema_version": "expgym.independent-pool-terminal-check.v1", "execution_complete": False,
                "score_complete": False, "terminal_classification": "integrity_failure", "agent_checks": checks}
    aggregate = aggregate_results(scenario, agents, answer_evaluator=answer_evaluator)
    complete = (_terminal_canonical(aggregate) == _terminal_canonical(result.get("aggregate"))
                and _terminal_canonical(result.get("terminal_status")) == _terminal_canonical(aggregate.get("terminal_status"))
                and _shared_state_is_complete(result.get("shared_state")))
    return {"schema_version": "expgym.independent-pool-terminal-check.v1", "execution_complete": bool(complete),
            "score_complete": bool(complete and aggregate["terminal_status"]["score_complete"]),
            "terminal_classification": aggregate["terminal_status"]["terminal_classification"] if complete else "integrity_failure",
            "agent_checks": checks, "recomputed_aggregate": aggregate, "raw_and_artifact_integrity_checked": False}


def _split_strategies(value: str) -> List[str]:
    strategies = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [item for item in strategies if item not in STRATEGIES]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown strategies {unknown}; choose from {STRATEGIES}"
        )
    if not strategies:
        raise argparse.ArgumentTypeError("at least one strategy is required")
    return list(dict.fromkeys(strategies))


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
    return os.environ.get("EXPGYM_MODEL", "")


def _backend_model(backend: str) -> str:
    return {
        "sub2api": os.environ.get("SUB2API_MODEL", "gpt-5.4"),
        "openai": os.environ.get("EXPGYM_OPENAI_MODEL", "gpt-4o-mini"),
        "gemini": os.environ.get("EXPGYM_GEMINI_MODEL", "gemini-2.5-flash"),
        "vllm": os.environ.get("EXPGYM_VLLM_MODEL", "local-model"),
        "fake": "fake",
    }.get(
        backend,
        os.environ.get("EXPGYM_OPENROUTER_MODEL", "openai/gpt-4.1-nano"),
    )


def _backend_base_url(backend: str) -> Optional[str]:
    if os.environ.get("EXPGYM_BASE_URL"):
        return os.environ["EXPGYM_BASE_URL"]
    return {
        "sub2api": os.environ.get("SUB2API_BASE_URL"),
        "openrouter": os.environ.get("OPENROUTER_BASE_URL"),
        "openai": os.environ.get("OPENAI_BASE_URL"),
        "gemini": os.environ.get("GEMINI_BASE_URL"),
        "vllm": os.environ.get("VLLM_BASE_URL"),
    }.get(backend)


def _load_api_key(args: argparse.Namespace) -> Optional[str]:
    if args.api_key:
        return args.api_key.strip()
    env_name = {
        "sub2api": "SUB2API_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }.get(args.backend)
    value = os.environ.get(env_name, "") if env_name else ""
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


def _pool_cache_namespace(args: argparse.Namespace) -> Optional[str]:
    """Bind an optional routing namespace to one independent pool invocation.

    These are provider prompt-cache routing keys, not the observation cache.
    A provider may ignore them; this does not promise physical KV-cache isolation.
    Keep the identity allowlisted so credentials and arbitrary Namespace fields
    never enter the serialized input, and keep output paths out for relocation.
    """
    base = getattr(args, "prompt_cache_key", None)
    if not base:
        return None
    evaluation = getattr(args, "_evaluation_identity", None)
    identity = {
        "derivation": "expgym.pool-invocation.v1",
        "namespace": base,
        "backend": args.backend,
        "model": args.model,
        "task": {
            "scenario": args.scenario,
            "tuning_task": args.tuning_task,
            "question_index": args.question_index,
            "data_source": args.data_source,
            "cc_split": args.cc_split,
            "cost_regime": args.cost_regime,
            "evaluation_sha256": evaluation.get("sha256") if isinstance(evaluation, dict) else None,
        },
        "pool": {
            "agents": args.agents,
            "seed": args.seed,
            "base_seed": getattr(args, "base_seed", args.seed),
            "repeat_index": getattr(args, "repeat_index", 0),
        },
        "generation": {
            "temperature": args.temperature,
            "max_steps": args.max_steps,
            "max_evaluations": args.max_evals,
            "max_context_tokens": args.max_context_tokens,
            "probes": args.probes,
            **_generation_options(args),
        },
        "protocol": {
            "poolact": POOLACT_PROTOCOL_VERSION,
            "missing_final_policy": getattr(args, "missing_final_policy", "error"),
            **_loop_options(args),
        },
    }
    canonical = json.dumps(
        identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "pool-" + hashlib.sha256(canonical).hexdigest()


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
        _pool_cache_namespace(args),
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
    namespace._api_dump_context = {
        "runner": "poolact",
        "scenario": args.scenario,
        "tuning_task": args.tuning_task,
        "question_index": args.question_index,
        "cost_regime": args.cost_regime,
        "strategy": strategy,
        "agent_id": agent_id,
        "seed": namespace.seed,
        "repeat_index": getattr(args, "repeat_index", 0),
        "repeats": getattr(args, "repeats", 1),
        "output_dir": str(args.output_dir),
    }
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
            json.dump(
                value,
                handle,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _implementation_manifest() -> Dict[str, str]:
    return {"source_tree": source_tree_sha256(REPO_ROOT)}


def _resolved_config(
    args: argparse.Namespace,
    time_budget: Optional[float],
) -> Dict[str, Any]:
    return {
        "poolact_protocol": POOLACT_PROTOCOL_VERSION,
        "missing_final_policy": getattr(args, "missing_final_policy", "error"),
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
        "base_seed": getattr(args, "base_seed", args.seed),
        "repeat_index": getattr(args, "repeat_index", 0),
        "repeats": getattr(args, "repeats", 1),
        "agent_seeds": [args.seed + agent_id for agent_id in range(args.agents)],
        "seed_semantics": "requested_per_agent_seed; provider determinism requires separate verification",
        "temperature": args.temperature,
        **_generation_options(args),
        **_loop_options(args),
        "max_steps": args.max_steps,
        "max_evals": args.max_evals,
        "max_context_tokens": args.max_context_tokens,
        "probes": args.probes,
        "base_url": args.base_url,
        "prompt_cache_key": args.prompt_cache_key,
        "vllm_disable_thinking": args.vllm_disable_thinking,
        "request_timeout": args.request_timeout,
        "max_retries": args.max_retries,
        "retry_base_seconds": args.retry_base_seconds,
        "retry_max_seconds": args.retry_max_seconds,
        "evaluation_identity": getattr(args, "_evaluation_identity", None),
    }


def _repeat_namespace(args: argparse.Namespace, repeat_index: int) -> argparse.Namespace:
    """Create one independent pool repetition without changing the pool size."""
    namespace = argparse.Namespace(**vars(args))
    namespace.base_seed = args.seed
    namespace.repeat_index = repeat_index
    namespace.seed = args.seed + repeat_index * args.agents
    if args.repeats > 1:
        namespace.output_dir = args.output_dir / f"repeat_{repeat_index}"
    return namespace


def _batch_strategy_metrics(
    items: Dict[str, Dict[str, Dict[str, Any]]],
    strategies: List[str],
) -> Dict[str, Dict[str, Any]]:
    metrics: Dict[str, Dict[str, Any]] = {}
    for strategy in strategies:
        aggregates = [item[strategy] for item in items.values() if strategy in item]
        policies = set()
        for aggregate in aggregates:
            status = aggregate.get("terminal_status", {})
            if not isinstance(status, dict):
                raise ValueError("Invalid aggregate terminal_status in batch metrics")
            policy = status.get("policy_version")
            if policy not in (None, "error", "task-abstention-v1"):
                raise ValueError("Unknown missing-final policy in batch metrics")
            policies.add("error" if policy is None else policy)
        if len(policies) > 1:
            raise ValueError("Mixed missing-final policies in batch metrics")
        strict_complete = policies == {"task-abstention-v1"}
        scores = [aggregate.get("answer_perf") for aggregate in aggregates]
        numeric_scores = [float(score) for score in scores if _is_finite_number(score)]
        metrics[strategy] = {
            "completed_items": len(scores),
            "scored_items": len(numeric_scores),
            "mean_answer_perf": (
                sum(numeric_scores) / len(numeric_scores)
                if numeric_scores and (not strict_complete or len(numeric_scores) == len(scores)) else None
            ),
            "known_subset_mean_answer_perf_descriptive": (sum(numeric_scores) / len(numeric_scores) if numeric_scores else None),
            "unscored_items": len(scores) - len(numeric_scores),
        }
    return metrics


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _shared_state_is_complete(state: Any) -> bool:
    if state is None:
        return True
    if not isinstance(state, dict):
        return False
    graph = state.get("graph", {})
    return (
        isinstance(graph, dict)
        and graph.get("pending_claims", 0) == 0
        and state.get("pending_claims", 0) == 0
        and type(graph.get("pending_claims", 0)) is int
        and type(state.get("pending_claims", 0)) is int
    )


def _load_resumable_result(
    result_path: Path,
    *,
    item_output_dir: Path,
    strategy: str,
    config: Dict[str, Any],
    implementation: Dict[str, str],
    agents: int,
    answer_evaluator: Optional[Callable[..., Any]],
    score_tools: Optional[Dict[str, Callable[..., Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Load a verified PoolAct completion marker, or return ``None``."""
    try:
        existing = json.loads(result_path.read_text(encoding="utf-8"))
        if not isinstance(existing, dict):
            return None
        if existing.get("config") != config:
            return None
        if not isinstance(config.get("evaluation_identity"), dict):
            return None
        if existing.get("implementation_sha256") != implementation:
            return None
        if existing.get("strategy") != strategy or existing.get("agents") != agents:
            return None
        if not _shared_state_is_complete(existing.get("shared_state")):
            return None
        embedded_agents = existing.get("agent_results")
        if not isinstance(embedded_agents, list) or len(embedded_agents) != agents:
            return None
        if not all(isinstance(agent, dict) for agent in embedded_agents):
            return None
        if any(type(agent.get("agent_id")) is not int for agent in embedded_agents) or [agent["agent_id"] for agent in embedded_agents] != list(range(agents)):
            return None
        by_id = {agent.get("agent_id"): agent for agent in embedded_agents}
        if set(by_id) != set(range(agents)):
            return None
        for agent_id in range(agents):
            agent = by_id[agent_id]
            score_check = agent.get("score_check")
            if not isinstance(score_check, dict) or not terminal_publishable(agent):
                return None
            if agent.get("missing_final_policy", "error") != config.get("missing_final_policy", "error"):
                return None
            if "tuning_final_policy" in config and agent.get("tuning_final_policy") != config["tuning_final_policy"]:
                return None
            agent_path = (
                item_output_dir / strategy / "agents" / f"agent_{agent_id}.json"
            )
            if json.loads(agent_path.read_text(encoding="utf-8")) != agent:
                return None
            if not terminal_publishable(agent, _score_check(agent, score_tools or {}, answer_evaluator)):
                return None
        aggregate = existing.get("aggregate")
        if not isinstance(aggregate, dict) or not aggregate_publishable(aggregate):
            return None
        recomputed_aggregate = aggregate_results(
            str(config["scenario"]),
            embedded_agents,
            answer_evaluator=answer_evaluator,
        )
        if _terminal_canonical(aggregate) != _terminal_canonical(recomputed_aggregate):
            return None
        if _terminal_canonical(existing.get("terminal_status")) != _terminal_canonical(aggregate.get("terminal_status")):
            return None
        return existing
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _terminal_evidence_root(args: argparse.Namespace) -> Path:
    explicit = getattr(args, "terminal_evidence_dir", None)
    if explicit is None:
        return args.output_dir / "_terminal_evidence"
    question = getattr(args, "question_index", None)
    return (Path(explicit) / ("repeat_%d" % getattr(args, "repeat_index", 0))
            / ("item_%s" % (question if question is not None else "batch")))


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
    runtimes: Dict[int, Any] = {}

    def execute_agent(agent_id: int, evidence: TerminalEvidence) -> Dict[str, Any]:
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
                time_budget=time_budget,
            )
        elif strategy == "poolact":
            runtime = coordinator.bind_tools(tools, agent_id, time_budget=time_budget)
            runtimes[agent_id] = runtime
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
        instruction_notes = _call_scenario(
            scenario["build_instruction_notes"],
            include_overhead,
            namespace,
        )
        fake_plan = (
            _call_scenario(
                scenario["build_fake_plan"],
                args.probes,
                namespace,
            )
            if args.backend == "fake"
            else []
        )
        llm = build_llm(
            args.backend,
            fake_plan,
            namespace,
            system_prompt=system_prompt,
        )
        context = _resolve_context(scenario, include_overhead, namespace, llm)
        answer_evaluator = _resolve_answer_evaluator(scenario, namespace)
        started = time.perf_counter()
        result = evidence.loop(
            run_react_loop,
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
            **_loop_options(namespace),
        )
        result["wall_time_seconds"] = time.perf_counter() - started
        dump_metadata = getattr(llm, "dump_metadata", None)
        if dump_metadata is not None:
            result["api_dump"] = dict(dump_metadata)
        result["agent_id"] = agent_id
        result["seed"] = namespace.seed
        result["repeat_index"] = getattr(args, "repeat_index", 0)
        result["strategy"] = strategy
        mark_loop_return(result, args.scenario, getattr(args, "missing_final_policy", "error"))
        result["score_check"] = evidence.score(
            _score_result,
            result,
            direct_tools,
            answer_evaluator,
        )
        if coordinator is not None and result.get("answer"):
            coordinator.graph.record_end(agent_id, str(result["answer"]))
        return result

    def run_agent(agent_id: int) -> Dict[str, Any]:
        evidence = TerminalEvidence(
            _terminal_evidence_root(args) / strategy / ("agent_%d" % agent_id),
            owner={"runner": "poolact", "scope": "agent", "strategy": strategy,
                   "agent_id": agent_id, "seed": args.seed + agent_id,
                   "question_index": args.question_index,
                   "repeat_index": getattr(args, "repeat_index", 0)},
            source_root=REPO_ROOT,
        )
        # Scope exit flushes only AFTER original graph/claim cleanup.
        with evidence:
            try:
                return execute_agent(agent_id, evidence)
            finally:
                runtime = runtimes.get(agent_id)
                if runtime is not None:
                    coordinator.graph.complete_agent_claims(
                        agent_id, completion_time=runtime.clock.now,
                    )

    agent_results = run_agents_parallel(args.agents, run_agent)
    failed_agents = [
        result["agent_id"]
        for result in agent_results
        if not terminal_publishable(result)
    ]
    if failed_agents:
        raise RuntimeError(f"score check failed for agents: {failed_agents}")
    aggregate_evaluator = _resolve_answer_evaluator(scenario, args)
    aggregate = aggregate_results(
        args.scenario,
        agent_results,
        answer_evaluator=aggregate_evaluator,
    )
    if not aggregate_publishable(aggregate):
        raise RuntimeError("aggregate answer could not be scored")
    state: Optional[Dict[str, Any]] = None
    if cache is not None:
        state = {"cache": cache.stats()}
    if coordinator is not None:
        state = coordinator.stats()
    if not _shared_state_is_complete(state):
        raise RuntimeError("shared state contains unfinished pending claims")
    response = {
        "strategy": strategy,
        "agents": args.agents,
        "aggregate": aggregate,
        "shared_state": state,
        "agent_results": agent_results,
    }
    if "terminal_status" in aggregate:
        response["terminal_status"] = dict(aggregate["terminal_status"])
    return response


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    _add_generation_arguments(parser)
    parser.add_argument("--terminal-evidence-dir", type=Path, default=None,
                        help="Optional separate evidence root; default: output-dir/_terminal_evidence.")
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
        default=None,
    )
    parser.add_argument(
        "--base-url",
        default=None,
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
    parser.add_argument(
        "--repeats", type=int, default=1,
        help="Independent N-agent pools, with seeds base_seed + repeat_index * N + agent_id.",
    )
    parser.add_argument("--seed", type=int, default=1206)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--max-evals", type=int, default=30)
    parser.add_argument("--max-context-tokens", type=int, default=None)
    parser.add_argument("--request-timeout", type=float, default=600.0)
    parser.add_argument("--max-retries", type=int, default=10)
    parser.add_argument("--retry-base-seconds", type=float, default=3.0)
    parser.add_argument("--retry-max-seconds", type=float, default=120.0)
    parser.add_argument("--probes", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/poolact"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(args=None, *, selected_repeat=None) -> int:
    """Run the CLI matrix, or one independent repeat selected by the queue."""
    args = parse_args() if args is None else args
    if not args.model:
        args.model = _backend_model(args.backend)
    if args.base_url is None:
        args.base_url = _backend_base_url(args.backend)
    if args.api_key_file is None and args.backend == "openrouter":
        args.api_key_file = Path(
            os.environ.get("OPENROUTER_API_KEY_FILE", "../openrouter.key")
        )
    if args.agents < 1:
        raise SystemExit("--agents must be at least 1")
    if args.repeats < 1:
        raise SystemExit("--repeats must be at least 1")
    if selected_repeat is not None and (type(selected_repeat) is not int
                                       or not 0 <= selected_repeat < args.repeats):
        raise SystemExit("selected_repeat must identify an existing repeat")
    if args.max_steps < 1:
        raise SystemExit("--max-steps must be at least 1")
    if args.max_evals < 1:
        raise SystemExit("--max-evals must be at least 1")
    if args.max_context_tokens is not None and args.max_context_tokens < 1:
        raise SystemExit("--max-context-tokens must be positive")
    if args.request_timeout <= 0:
        raise SystemExit("--request-timeout must be positive")
    if args.max_retries < 0:
        raise SystemExit("--max-retries must be non-negative")
    if args.retry_base_seconds < 0 or args.retry_max_seconds < 0:
        raise SystemExit("retry delays must be non-negative")
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
            "Set the matching backend API key or pass --api-key."
        )

    c_base = resolve_base_cost(args.scenario, args)
    time_budget, baselines = resolve_cost_regime(args, c_base)
    if len(baselines) != 1:
        raise SystemExit("PoolAct requires one named --cost-regime")
    mode = baselines[0]
    if args.dry_run:
        configs = []
        for repeat_index in range(args.repeats):
            for question_index in question_indices:
                item_args = _repeat_namespace(args, repeat_index)
                item_args.question_index = question_index
                item_args.questions = None
                config = _resolved_config(item_args, time_budget)
                config["output_dir"] = str(
                    item_args.output_dir / f"item_{question_index}"
                    if args.questions is not None else item_args.output_dir
                )
                configs.append(config)
        preview: object = configs[0] if args.questions is None and args.repeats == 1 else {
            "batch": True,
            "question_indices": question_indices,
            "repeats": args.repeats,
            "item_strategy_runs": len(configs) * len(args.strategies),
            "agent_traces": len(configs) * len(args.strategies) * args.agents,
            "items": configs,
        }
        print(json.dumps(preview, indent=2, sort_keys=True))
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    implementation = _implementation_manifest()
    repetitions: Dict[str, Dict[str, Any]] = {}
    observations: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for repeat_index in (range(args.repeats) if selected_repeat is None else [selected_repeat]):
        repeat_args = _repeat_namespace(args, repeat_index)
        summary = _run_items(
            repeat_args, question_indices, api_key, time_budget, mode, implementation,
        )
        repetitions[str(repeat_index)] = summary
        if args.questions is None:
            observations[f"repeat_{repeat_index}/item_{question_indices[0]}"] = summary["strategies"]
        else:
            observations.update({
                f"repeat_{repeat_index}/item_{item}": strategies
                for item, strategies in summary["items"].items()
            })
    if args.repeats > 1 and selected_repeat is None:
        with TerminalEvidence(
            _terminal_evidence_root(args) / "repeat_summary",
            owner={"runner": "poolact", "scope": "repeat_summary", "seed": args.seed},
            source_root=REPO_ROOT, stage="runner_finalize",
        ):
            _atomic_json(args.output_dir / "summary.json", {
                "config": {
                    **_resolved_config(args, time_budget),
                    "question_indices": question_indices,
                },
                "implementation_sha256": implementation,
                "repeats": repetitions,
                "strategy_metrics": _batch_strategy_metrics(observations, args.strategies),
                "aggregation_unit": "item_by_independent_pool_repeat; agents are never pooled across repeats",
                "item_strategy_runs": len(observations) * len(args.strategies),
                "agent_traces": len(observations) * len(args.strategies) * args.agents,
            })
    return 0


def _run_items(
    args: argparse.Namespace,
    question_indices: List[int],
    api_key: Optional[str],
    time_budget: Optional[float],
    mode: str,
    implementation: Dict[str, str],
) -> Dict[str, Any]:
    with TerminalEvidence(
        _terminal_evidence_root(args) / "invocation",
        owner={"runner": "poolact", "scope": "invocation", "question_indices": list(question_indices),
               "strategies": list(args.strategies), "seed": args.seed},
        source_root=REPO_ROOT, stage="run_items",
    ):
        return _run_items_with_evidence(args, question_indices, api_key, time_budget, mode, implementation)


def _run_items_with_evidence(
    args: argparse.Namespace,
    question_indices: List[int],
    api_key: Optional[str],
    time_budget: Optional[float],
    mode: str,
    implementation: Dict[str, str],
) -> Dict[str, Any]:
    """Run the original single-repeat item batch; every call owns fresh pools."""
    batch_items: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for question_index in question_indices:
        item_args = argparse.Namespace(**vars(args))
        item_args.question_index = question_index
        item_args.questions = None
        item_args._evaluation_identity = evaluation_identity(item_args, REPO_ROOT)
        bind_evaluation_identity(item_args._evaluation_identity)
        config = _resolved_config(item_args, time_budget)
        resume_answer_evaluator = (
            _resolve_answer_evaluator(_SCENARIOS[args.scenario], item_args)
            if args.resume
            else None
        )
        resume_tools = _resolve_tools(_SCENARIOS[args.scenario], item_args) if args.resume else None
        item_output_dir = (
            args.output_dir / f"item_{question_index}"
            if args.questions is not None
            else args.output_dir
        )
        item_args.output_dir = item_output_dir
        completed: Dict[str, Any] = {}
        for strategy in args.strategies:
            result_path = item_output_dir / strategy / "result.json"
            if args.resume and result_path.exists():
                existing = _load_resumable_result(
                    result_path,
                    item_output_dir=item_output_dir,
                    strategy=strategy,
                    config=config,
                    implementation=implementation,
                    agents=args.agents,
                    answer_evaluator=resume_answer_evaluator,
                    score_tools=resume_tools,
                )
                if existing is not None:
                    completed[strategy] = existing
                    print(f"[resume] item={question_index} strategy={strategy}: {result_path}")
                    continue
                if getattr(args, "missing_final_policy", "error") == "task-abstention-v1":
                    raise RuntimeError("Existing terminal artifact failed exact resume validation; refusing model resampling")
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
            if evaluation_identity(item_args, REPO_ROOT) != item_args._evaluation_identity:
                raise RuntimeError("Evaluation inputs/dependencies changed during the pool; refusing to publish a score")
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
        batch_summary = {
            "config": batch_config,
            "implementation_sha256": implementation,
            "items": batch_items,
            "strategy_metrics": _batch_strategy_metrics(batch_items, args.strategies),
        }
        _atomic_json(args.output_dir / "summary.json", batch_summary)
        return batch_summary
    return item_summary


if __name__ == "__main__":
    raise SystemExit(main())
