"""Simple executable that wires the ExpGym components together."""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from typing import Dict, List, Optional, Tuple

from expgym.react_loop import FakeLLM, LLMBackend, build_system_prompt, run_react_loop
from expgym.task_tuning import SCENARIO as TUNING_SCENARIO
from expgym.task_restricted_search import SCENARIO as RESTRICTED_SEARCH_SCENARIO
from expgym.task_evidence_audit import SCENARIO as EVIDENCE_AUDIT_SCENARIO

Scenario = Dict[str, object]
_SCENARIOS: Dict[str, Scenario] = {
    "tuning": TUNING_SCENARIO,
    "restricted_search": RESTRICTED_SEARCH_SCENARIO,
    "evidence_audit": EVIDENCE_AUDIT_SCENARIO,
}

# ---------------------------------------------------------------------------
# Cost-regime presets (paper2 framing).
#
# A regime is a choice of budget multiplier beta and a cost-visibility flag.
# The wall-clock budget is B = beta * c_base, where c_base is the per-scenario
# base cost (oracle-best for tuning; ~300s for search and audit).
#
# Beta is continuous. The named presets below are the three points reported
# in the paper, but users may pass any positive --beta value to sweep along
# the cost axis.
# ---------------------------------------------------------------------------
COST_REGIMES: Dict[str, Dict[str, object]] = {
    "cost_free":     {"beta": math.inf, "show_cost": False},
    "cost_moderate": {"beta": 10.0,     "show_cost": True},
    "cost_tight":    {"beta": 3.0,      "show_cost": True},
    "custom":        {"beta": None,     "show_cost": None},  # use --beta / --baseline
}

# Default base cost for the built-in (non-HPOBench) tuning task. The 10-param
# demo overhead lives in [8, 140]s; ~100s is a representative midpoint.
_DEFAULT_TUNING_BUILTIN_C_BASE = 100.0
# Search and audit per-call overhead in this build is 300 +/- 20s.
_SEARCH_AUDIT_C_BASE = 300.0


def resolve_base_cost(scenario_name: str, args: argparse.Namespace) -> float:
    """Return the per-scenario base cost c_base used to scale beta.

    Tuning uses the oracle-best evaluation cost from
    ``data/hpo_tuning/oracle3.json`` (when available); search and audit use
    the per-call overhead of 300s.
    """
    if scenario_name == "tuning":
        task = getattr(args, "tuning_task", "neural_network_training")
        if task == "neural_network_training":
            return _DEFAULT_TUNING_BUILTIN_C_BASE
        oracle_path = os.path.join(
            os.path.dirname(__file__), "data", "hpo_tuning", "oracle3.json"
        )
        if os.path.exists(oracle_path):
            try:
                with open(oracle_path) as f:
                    oracle = json.load(f)
                entry = oracle.get("tasks", {}).get(task)
                if entry and "best_cost" in entry:
                    return float(entry["best_cost"])
            except (json.JSONDecodeError, OSError, KeyError, TypeError):
                pass
        return _DEFAULT_TUNING_BUILTIN_C_BASE
    if scenario_name in ("restricted_search", "evidence_audit"):
        return _SEARCH_AUDIT_C_BASE
    raise ValueError(f"Unknown scenario for base-cost lookup: {scenario_name}")


def resolve_cost_regime(
    args: argparse.Namespace, c_base: float
) -> Tuple[Optional[float], List[str]]:
    """Translate ``--cost-regime`` / ``--beta`` into (time_budget, baselines).

    Returns:
        time_budget: float seconds, or None for no ceiling.
        baselines: list of per-loop baselines to run (legacy ``--baseline`` mode
            names: "no_budget", "time_aware", "time_focus").
    """
    preset = COST_REGIMES[args.cost_regime]

    if args.cost_regime != "custom":
        beta = preset["beta"]
        show_cost = preset["show_cost"]
        time_budget = None if (beta is math.inf) else float(beta) * c_base
        baselines = ["time_aware"] if show_cost else ["no_budget"]
        return time_budget, baselines

    # Custom regime: respect explicit overrides.
    time_budget = args.time_budget
    if time_budget is None and args.beta is not None:
        time_budget = float(args.beta) * c_base
    baselines = (
        ["no_budget", "time_aware"] if args.baseline == "both" else [args.baseline]
    )
    return time_budget, baselines


def build_llm(
    backend: str,
    plan: List[tuple[str, str]],
    args: argparse.Namespace,
    *,
    system_prompt: str | None = None,
) -> LLMBackend:
    if backend == "fake":
        final_answer = plan[-1][1] if plan else None
        return FakeLLM(plan=plan, final_answer=final_answer)
    if backend == "openai":
        from expgym.llm_clients import OpenAICompatibleLLM

        return OpenAICompatibleLLM(
            api_key=args.api_key,
            model=args.model or "gpt-4o-mini",
            system_prompt=system_prompt,
            temperature=getattr(args, "temperature", 0.0),
            seed=args.seed,
            base_url=args.base_url,
        )
    if backend == "gemini":
        from expgym.llm_clients import build_gemini_client

        return build_gemini_client(
            api_key=args.api_key,
            model=args.model or "gemini-2.5-flash",
            system_prompt=system_prompt,
            temperature=getattr(args, "temperature", 0.0),
            seed=args.seed,
            base_url=args.base_url,
        )
    if backend == "openrouter":
        from expgym.llm_clients import build_openrouter_client

        return build_openrouter_client(
            api_key=args.api_key,
            model=args.model or "deepseek/deepseek-v3.2",
            system_prompt=system_prompt,
            temperature=getattr(args, "temperature", 0.0),
            seed=args.seed,
            base_url=args.base_url,
            referer=args.openrouter_referer,
            title=args.openrouter_title,
        )
    if backend == "vllm":
        from expgym.llm_clients import build_vllm_client

        chat_kwargs = None
        if args.vllm_disable_thinking:
            chat_kwargs = {"enable_thinking": False}
        return build_vllm_client(
            api_key=args.api_key,
            model=args.model or "local-model",
            system_prompt=system_prompt,
            temperature=getattr(args, "temperature", 0.0),
            seed=args.seed,
            base_url=args.base_url,
            chat_template_kwargs=chat_kwargs,
        )
    raise ValueError(f"Unknown backend: {backend}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ExpGym demo experiment.")
    parser.add_argument(
        "--scenario",
        choices=sorted(_SCENARIOS.keys()),
        default="tuning",
        help="Scenario configuration to run.",
    )
    parser.add_argument(
        "--backend",
        choices=["fake", "openai", "gemini", "openrouter", "vllm"],
        default="fake",
        help="LLM backend to use for the ReAct loop.",
    )
    parser.add_argument("--model", default=None, help="Model identifier for API backends.")
    parser.add_argument("--api-key", default=None, help="Optional API key override.")
    parser.add_argument("--system-prompt", default=None, help="Optional system prompt.")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for API backends.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1206,
        help="Global seed for deterministic sampling.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override the OpenAI-compatible endpoint (e.g., Gemini OpenAI URL).",
    )
    parser.add_argument(
        "--probes",
        type=int,
        default=4,
        help="Number of seeded configs the fake LLM probes before answering.",
    )
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument(
        "--time-budget",
        type=float,
        default=None,
        help="Optional ceiling on cumulative overhead (seconds).",
    )
    parser.add_argument(
        "--max-evals",
        type=int,
        default=30,
        help="Maximum tool evaluations permitted in the loop.",
    )
    parser.add_argument(
        "--cost-regime",
        choices=sorted(COST_REGIMES.keys()),
        default="custom",
        help=(
            "Named cost regime from the paper (paper2 framing). "
            "'cost_free' (beta=inf, cost hidden), 'cost_moderate' (beta=10), "
            "'cost_tight' (beta=3), or 'custom' to use --beta / --time-budget / "
            "--baseline directly. Setting any preset overrides --baseline."
        ),
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=None,
        help=(
            "Continuous budget multiplier: time_budget = beta * c_base. "
            "Only used when --cost-regime is 'custom' and --time-budget is unset. "
            "c_base is the oracle-best eval cost for tuning, 300s for search/audit."
        ),
    )
    parser.add_argument(
        "--baseline",
        choices=["no_budget", "time_aware", "time_focus", "both"],
        default="both",
        help=(
            "Prompt/observation configuration (legacy). Used only when "
            "--cost-regime is 'custom'."
        ),
    )
    parser.add_argument(
        "--question-index",
        type=int,
        default=0,
        help="Row index into the HotpotQA test set (restricted_search only).",
    )
    parser.add_argument(
        "--tuning-task",
        default="neural_network_training",
        help="Tuning subtask name (e.g., neural_network_training or hpobench:svm_surrogate).",
    )
    parser.add_argument(
        "--list-tuning-tasks",
        action="store_true",
        help="List available tuning subtasks and exit.",
    )
    parser.add_argument(
        "--openrouter-referer",
        default=None,
        help="HTTP-Referer header required by OpenRouter (recommended).",
    )
    parser.add_argument(
        "--openrouter-title",
        default=None,
        help="X-Title header sent to OpenRouter (optional).",
    )
    parser.add_argument(
        "--vllm-disable-thinking",
        action="store_true",
        help="Send chat_template_kwargs={\"enable_thinking\": false} to vLLM.",
    )
    parser.add_argument(
        "--data-source",
        default=None,
        help="Filter restricted_search questions by data source (e.g., musique, hotpotqa).",
    )
    parser.add_argument(
        "--cc-split",
        default="cc-large",
        choices=["cc-small", "cc-medium", "cc-large"],
        help="Evidence audit hypothesis subset size.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    if args.list_tuning_tasks:
        from expgym.task_tuning import list_hpobench_tasks

        tasks = ["neural_network_training"]
        tasks.extend(list_hpobench_tasks())
        print("Available tuning tasks:")
        for name in tasks:
            print(f"- {name}")
        return
    scenario = _SCENARIOS[args.scenario]
    fake_plan = _call_scenario(scenario["build_fake_plan"], args.probes, args)

    c_base = resolve_base_cost(args.scenario, args)
    time_budget, baselines = resolve_cost_regime(args, c_base)
    _print_regime_banner(args, c_base, time_budget)

    for mode in baselines:
        tools = _resolve_tools(scenario, args)
        include_overhead = mode == "time_focus"
        include_cost = mode == "time_aware"
        system_prompt = _resolve_system_prompt(scenario, include_overhead, args)
        llm = build_llm(
            args.backend, fake_plan, args, system_prompt=system_prompt
        )
        context = _call_scenario(scenario["build_context"], include_overhead, args)
        instruction_notes = _call_scenario(
            scenario["build_instruction_notes"], include_overhead, args
        )
        answer_builder = scenario.get("build_answer_evaluator")
        answer_evaluator = (
            answer_builder(args.question_index) if answer_builder is not None else None
        )
        result = run_react_loop(
            llm=llm,
            tools=tools,
            time_budget=time_budget,
            max_steps=args.max_steps,
            max_evals=args.max_evals,
            context=context,
            instruction_notes=instruction_notes,
            system_prompt=system_prompt,
            include_overhead_in_observation=include_overhead,
            include_cost_in_observation=include_cost,
            answer_evaluator=answer_evaluator,
        )

        _print_result(mode, result)
        _print_metrics(result)
        print("")


def _print_regime_banner(
    args: argparse.Namespace, c_base: float, time_budget: Optional[float]
) -> None:
    if args.cost_regime != "custom":
        beta = COST_REGIMES[args.cost_regime]["beta"]
        beta_str = "inf" if beta is math.inf else f"{beta:g}"
        budget_str = "no ceiling" if time_budget is None else f"{time_budget:.0f}s"
        print(
            f"[cost-regime] preset={args.cost_regime} beta={beta_str} "
            f"c_base={c_base:.1f}s -> time_budget={budget_str}"
        )
    elif args.beta is not None and args.time_budget is None:
        budget_str = "no ceiling" if time_budget is None else f"{time_budget:.0f}s"
        print(
            f"[cost-regime] preset=custom beta={args.beta:g} "
            f"c_base={c_base:.1f}s -> time_budget={budget_str}"
        )


def _print_result(mode: str, result: dict) -> None:
    print(f"=== ReAct Result ({mode}) ===")
    print(f"aborted: {result['aborted']}")
    print(f"answer: {result['answer']}")
    if result.get("answer_perf") is not None:
        print(
            f"answer_perf: {result['answer_perf']:.6f} | "
            f"answer_overhead: {result['answer_overhead']:.2f}"
        )
    print(
        f"api_calls: {result['api_calls']} | evaluations: {result['evaluations']} | "
        f"total_overhead: {result['total_overhead']:.3f}"
    )
    printed_prompt = False
    for line in result["steps"]:
        if line.startswith("Prompt:"):
            if printed_prompt:
                continue
            printed_prompt = True
        print(line)


def _print_metrics(result: dict) -> None:
    total_time = result["llm_time"] + result["eval_time"]
    token_sum = result["prompt_tokens"] + result["completion_tokens"]
    print(
        "-- Metrics: total_time={:.3f}s (LLM {:.3f}s + eval {:.3f}s), tokens={}, "
        "prompt_tokens={}, completion_tokens={}, instruction_tokens={}, api_calls={}, evals={}".format(
            total_time,
            result["llm_time"],
            result["eval_time"],
            token_sum,
            result["prompt_tokens"],
            result["completion_tokens"],
            result["instruction_tokens"],
            result["api_calls"],
            result["evaluations"],
        )
    )


def _call_scenario(fn, primary_arg, args):
    """Call a scenario hook, introspecting its signature to pass only accepted kwargs."""
    if fn is None:
        return None
    import inspect
    try:
        sig = inspect.signature(fn)
        params = sig.parameters
    except (ValueError, TypeError):
        params = {}

    kwargs = {}
    # Map attribute names to their arg values
    candidates = {
        "row_index": getattr(args, "question_index", 0),
        "tuning_task": getattr(args, "tuning_task", "neural_network_training"),
        "seed": getattr(args, "seed", 1206),
        "data_source": getattr(args, "data_source", None),
        "cc_split": getattr(args, "cc_split", None),
        "hypothesis_order": getattr(args, "hypothesis_order", None),
    }
    for name, value in candidates.items():
        if name in params:
            kwargs[name] = value
    # Also accept **kwargs catch-all
    has_var_keyword = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
    )
    if has_var_keyword:
        kwargs = {k: v for k, v in candidates.items() if v is not None}

    return fn(primary_arg, **kwargs)


def _resolve_tools(scenario: Scenario, args: argparse.Namespace) -> dict:
    import inspect
    tools_spec = scenario["tools"]
    if callable(tools_spec):
        sig = inspect.signature(tools_spec)
        params = sig.parameters
        candidates = {
            "row_index": getattr(args, "question_index", 0),
            "tuning_task": getattr(args, "tuning_task", None),
            "data_source": getattr(args, "data_source", None),
            "cc_split": getattr(args, "cc_split", None),
        }
        kwargs = {
            name: value
            for name, value in candidates.items()
            if name in params
        }
        return tools_spec(**kwargs)
    return tools_spec


def _resolve_system_prompt(
    scenario: Scenario, include_overhead: bool, args: argparse.Namespace
) -> str | None:
    if args.system_prompt:
        return args.system_prompt
    return build_system_prompt()


if __name__ == "__main__":
    main()
