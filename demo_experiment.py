"""Simple executable that wires the ExpGym components together."""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from expgym.react_loop import FakeLLM, LLMBackend, build_system_prompt, run_react_loop
from expgym.task_tuning import SCENARIO as TUNING_SCENARIO
from expgym.task_restricted_search import SCENARIO as RESTRICTED_SEARCH_SCENARIO
from expgym.task_evidence_audit import SCENARIO as EVIDENCE_AUDIT_SCENARIO
from expgym.tool_protocol import resolve_tool_protocol
from expgym.terminal_evidence import TerminalEvidence
from expgym.missing_final import mark_loop_return, terminal_publishable

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
        time_budget = None if math.isinf(float(beta)) else float(beta) * c_base
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
    prompt_cache_key = getattr(args, "prompt_cache_key", None)
    prompt_cache_key_field = getattr(args, "prompt_cache_key_field", "prompt_cache_key")
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
            prompt_cache_key=prompt_cache_key,
            prompt_cache_key_field=prompt_cache_key_field,
            **_generation_options(args, backend=backend),
            **_transport_options(args),
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
            prompt_cache_key=prompt_cache_key,
            prompt_cache_key_field=prompt_cache_key_field,
            **_generation_options(args, backend=backend),
            **_transport_options(args),
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
            prompt_cache_key=prompt_cache_key,
            prompt_cache_key_field=prompt_cache_key_field,
            **_generation_options(args, backend=backend),
            **_transport_options(args),
        )
    if backend == "vllm":
        from expgym.llm_clients import build_vllm_client

        return build_vllm_client(
            api_key=args.api_key,
            model=args.model or "local-model",
            system_prompt=system_prompt,
            temperature=getattr(args, "temperature", 0.0),
            seed=args.seed,
            base_url=args.base_url,
            prompt_cache_key=prompt_cache_key,
            prompt_cache_key_field=prompt_cache_key_field,
            **_generation_options(args, backend=backend),
            **_transport_options(args),
        )
    if backend == "sub2api":
        from expgym.llm_clients import build_sub2api_client

        return build_sub2api_client(
            api_key=args.api_key,
            model=args.model or os.getenv("SUB2API_MODEL", "gpt-5.4"),
            system_prompt=system_prompt,
            temperature=getattr(args, "temperature", 0.0),
            seed=args.seed,
            base_url=args.base_url,
            prompt_cache_key=prompt_cache_key,
            prompt_cache_key_field=prompt_cache_key_field,
            **_generation_options(args, backend=backend),
            **_transport_options(args),
        )
    raise ValueError(f"Unknown backend: {backend}")


def _generation_options(
    args: argparse.Namespace, backend: Optional[str] = None,
) -> Dict[str, object]:
    """Preserve legacy sampling defaults; pass optional generation controls."""
    chat_kwargs = getattr(args, "chat_template_kwargs", None)
    if (backend or getattr(args, "backend", "vllm")) == "vllm" and getattr(
        args, "vllm_disable_thinking", False
    ):
        chat_kwargs = dict(chat_kwargs or {})
        if chat_kwargs.get("enable_thinking") not in (None, False):
            raise ValueError("--vllm-disable-thinking conflicts with chat_template_kwargs.enable_thinking")
        chat_kwargs["enable_thinking"] = False
    return {
        "max_tokens": getattr(args, "max_tokens", None),
        "top_p": getattr(args, "top_p", 1.0),
        "top_k": getattr(args, "top_k", None),
        "chat_template_kwargs": chat_kwargs,
        "reasoning_effort": getattr(args, "reasoning_effort", None),
    }


def _loop_options(args: argparse.Namespace) -> Dict[str, object]:
    """Shared, fingerprintable protocol choices for both experiment runners."""
    return {
        "tool_protocol": getattr(args, "tool_protocol", "auto"),
        "max_protocol_retries": getattr(args, "max_protocol_retries", 1),
        "tuning_final_policy": getattr(args, "tuning_final_policy", "legacy"),
    }


def _add_generation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--prompt-cache-key-field", choices=["prompt_cache_key", "cache_salt"],
        default="prompt_cache_key",
        help="Explicit provider field for the existing prompt-cache namespace; cache_salt for compatible SGLang servers. Never inferred from model name.",
    )
    parser.add_argument("--missing-final-policy", choices=["error", "task-abstention-v1"], default="error",
                        help="Explicit post-loop missing-answer policy; does not change model requests or budgets.")
    def positive_integer(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be a positive integer") from exc
        if parsed < 1:
            raise argparse.ArgumentTypeError("must be a positive integer")
        return parsed

    def non_negative_integer(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
        if parsed < 0:
            raise argparse.ArgumentTypeError("must be a non-negative integer")
        return parsed

    def nucleus_probability(value: str) -> float:
        try:
            parsed = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be a finite number in (0, 1]") from exc
        if not math.isfinite(parsed) or not 0.0 < parsed <= 1.0:
            raise argparse.ArgumentTypeError("must be a finite number in (0, 1]")
        return parsed

    def top_k_count(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be -1 (disable) or a positive integer") from exc
        if parsed != -1 and parsed < 1:
            raise argparse.ArgumentTypeError("must be -1 (disable) or a positive integer")
        return parsed

    def json_object(value: str) -> Dict[str, object]:
        def reject_constant(constant: str) -> None:
            raise ValueError("non-finite JSON constant: " + constant)

        try:
            parsed = json.loads(value, parse_constant=reject_constant)
            json.dumps(parsed, allow_nan=False)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be a JSON object: " + str(exc)) from exc
        if not isinstance(parsed, dict):
            raise argparse.ArgumentTypeError("must be a JSON object")
        return parsed

    parser.add_argument(
        "--top-p", type=nucleus_probability, default=1.0,
        help="Nucleus probability in (0, 1]; default 1.0 preserves the legacy client payload.",
    )
    parser.add_argument(
        "--top-k", type=top_k_count, default=None,
        help="Optional provider top-k: -1 disables filtering, positive integers cap it; omitted by default.",
    )
    parser.add_argument(
        "--max-tokens", type=positive_integer, default=None,
        help="Per-request completion token cap; omitted by default (provider default).",
    )
    parser.add_argument(
        "--chat-template-kwargs", type=json_object, default=None, metavar="JSON",
        help="Optional JSON object passed to the provider chat template, e.g. thinking controls.",
    )
    parser.add_argument(
        "--reasoning-effort", default=None,
        help="Optional provider reasoning effort; omitted to preserve provider defaults.",
    )
    parser.add_argument(
        "--tool-protocol", choices=["auto", "native", "text"], default="auto",
        help="Tool protocol: auto selects native tools on capable clients, otherwise text ReAct.",
    )
    parser.add_argument(
        "--max-protocol-retries", type=non_negative_integer, default=1,
        help="Bounded malformed-decision repairs; each repair consumes a normal agent step.",
    )
    parser.add_argument(
        "--tuning-final-policy", choices=["submitted", "legacy"], default="legacy",
        help="Score the submitted tuning answer offline, or retain historical best-observed fallback.",
    )


def _transport_options(args: argparse.Namespace) -> Dict[str, object]:
    """Resolve shared HTTP timeout/retry settings for every real backend."""
    return {
        "timeout": getattr(args, "request_timeout", 600.0),
        "max_retries": getattr(args, "max_retries", 10),
        "retry_base_seconds": getattr(args, "retry_base_seconds", 3.0),
        "retry_max_seconds": getattr(args, "retry_max_seconds", 120.0),
        "dump_context": getattr(args, "_api_dump_context", None),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ExpGym demo experiment.")
    _add_generation_arguments(parser)
    parser.add_argument(
        "--scenario",
        choices=sorted(_SCENARIOS.keys()),
        default="tuning",
        help="Scenario configuration to run.",
    )
    parser.add_argument(
        "--backend",
        choices=["fake", "openai", "gemini", "openrouter", "sub2api", "vllm"],
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
        help="Requested model/environment seed; provider sampling determinism must be verified separately.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("EXPGYM_BASE_URL"),
        help="Override the OpenAI-compatible endpoint (e.g., Gemini OpenAI URL).",
    )
    parser.add_argument(
        "--prompt-cache-key",
        default=os.getenv("EXPGYM_PROMPT_CACHE_KEY"),
        help=(
            "Stable prompt cache routing key reused for every turn and retry in "
            "this run."
        ),
    )
    parser.add_argument(
        "--probes",
        type=int,
        default=4,
        help="Number of seeded configs the fake LLM probes before answering.",
    )
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--request-timeout", type=float, default=600.0)
    parser.add_argument("--max-retries", type=int, default=10)
    parser.add_argument("--retry-base-seconds", type=float, default=3.0)
    parser.add_argument("--retry-max-seconds", type=float, default=120.0)
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
    parser.add_argument("--terminal-evidence-dir", type=Path, default=None,
                        help="Opt-in local terminal evidence; not a result completion marker.")
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
        with TerminalEvidence(
            args.terminal_evidence_dir / mode if args.terminal_evidence_dir is not None else None,
            owner={"runner": "demo", "scope": "baseline", "mode": mode,
                   "scenario": args.scenario, "seed": args.seed},
            source_root=Path(__file__).resolve().parent, stage="demo_run",
        ) as evidence:
            tools = _resolve_tools(scenario, args)
            include_overhead = mode == "time_focus"
            include_cost = mode == "time_aware"
            system_prompt = _resolve_system_prompt(scenario, include_overhead, args)
            llm = build_llm(
                args.backend, fake_plan, args, system_prompt=system_prompt
            )
            context = _resolve_context(scenario, include_overhead, args, llm)
            instruction_notes = _call_scenario(
                scenario["build_instruction_notes"], include_overhead, args
            )
            answer_evaluator = _resolve_answer_evaluator(scenario, args)
            result = evidence.loop(
                run_react_loop,
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
                **_loop_options(args),
            )
            # Import lazily: the sweep imports this module's scenario/client helpers.
            from scripts.run_paper_sweep import _score_result

            mark_loop_return(result, args.scenario, args.missing_final_policy)
            result["score_check"] = evidence.score(_score_result, result, tools, answer_evaluator)
            if not terminal_publishable(result):
                raise RuntimeError(f"score check failed: {result['score_check']}")

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


def _call_scenario(fn, primary_arg, args, *, tool_protocol=None):
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
    if tool_protocol is not None:
        candidates["tool_protocol"] = tool_protocol
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


def _resolve_context(scenario: Scenario, include_overhead: bool, args: argparse.Namespace, llm: LLMBackend) -> str:
    """Render source-owned task instructions for the loop's resolved protocol.

    Dataset text and caller-supplied context are never rewritten here.
    """
    protocol = resolve_tool_protocol(llm, getattr(args, "tool_protocol", "auto"))
    return _call_scenario(
        scenario["build_context"], include_overhead, args, tool_protocol=protocol,
    )


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


def _resolve_answer_evaluator(
    scenario: Scenario,
    args: argparse.Namespace,
):
    """Build a scenario evaluator without masking TypeErrors from its body."""
    import inspect

    builder = scenario.get("build_answer_evaluator")
    if builder is None:
        return None
    signature = inspect.signature(builder)
    candidates = {
        "data_source": getattr(args, "data_source", None),
        "cc_split": getattr(args, "cc_split", None),
    }
    kwargs = {
        name: value
        for name, value in candidates.items()
        if name in signature.parameters and value is not None
    }
    return builder(getattr(args, "question_index", 0), **kwargs)


def _resolve_system_prompt(
    scenario: Scenario, include_overhead: bool, args: argparse.Namespace
) -> str | None:
    if args.system_prompt:
        return args.system_prompt
    return build_system_prompt()


if __name__ == "__main__":
    main()
