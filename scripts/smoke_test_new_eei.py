"""Smoke test: one tuning + one audit trace with DSV3 under EI (10x) mode.

Uses the new single-parameter EEI framework:
  - overhead_scale=1.0 (always real cost)
  - budget = base_cost × cost_multiplier
  - baseline = time_aware (shows cost + time_left)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from expgym.react_loop import run_react_loop, build_system_prompt
from expgym.llm_clients import build_openrouter_client
from expgym.task_tuning import SCENARIO as TUNING_SCENARIO
from expgym.task_evidence_audit import SCENARIO as AUDIT_SCENARIO
from demo_experiment import _call_scenario, _resolve_tools
import argparse

OUTPUT_DIR = "budget_sweep_results/smoke_new_eei"
os.makedirs(os.path.join(OUTPUT_DIR, "traces"), exist_ok=True)

COST_MULT = 10  # EI mode
TUNING_BASE_COST = 38.82  # paramnet:letter:steps mean_cost
AUDIT_BASE_COST = 300.0


def make_args(**overrides):
    defaults = dict(
        scenario="tuning",
        backend="openrouter",
        model="deepseek/deepseek-v3.2",
        api_key=None,
        system_prompt=None,
        temperature=0.0,
        seed=1206,
        base_url=None,
        probes=4,
        max_steps=30,
        time_budget=None,
        max_evals=999999,
        baseline="time_aware",
        question_index=0,
        tuning_task="hpobench:paramnet:letter:steps",
        list_tuning_tasks=False,
        openrouter_referer=None,
        openrouter_title=None,
        vllm_disable_thinking=False,
        data_source=None,
        cc_split="cc-large",
        hypothesis_order=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def run_trace(scenario_def, args, label):
    include_overhead = False  # time_aware uses include_cost, not include_overhead
    include_cost = True

    system_prompt = build_system_prompt()
    tools = _resolve_tools(scenario_def, args)
    context = _call_scenario(scenario_def["build_context"], include_overhead, args)
    instruction_notes = _call_scenario(
        scenario_def["build_instruction_notes"], include_overhead, args
    )

    llm = build_openrouter_client(
        model=args.model,
        system_prompt=system_prompt,
        temperature=args.temperature,
        seed=args.seed,
        max_tokens=4096,
    )

    answer_builder = scenario_def.get("build_answer_evaluator")
    answer_evaluator = None
    if answer_builder is not None:
        for kwargs in [
            {"cc_split": args.cc_split},
            {},
        ]:
            try:
                answer_evaluator = answer_builder(args.question_index, **kwargs)
                break
            except TypeError:
                continue

    result = run_react_loop(
        llm=llm,
        tools=tools,
        time_budget=args.time_budget,
        max_steps=args.max_steps,
        max_evals=args.max_evals,
        context=context,
        instruction_notes=instruction_notes or [],
        system_prompt=system_prompt,
        include_overhead_in_observation=include_overhead,
        include_cost_in_observation=include_cost,
        answer_evaluator=answer_evaluator,
        overhead_scale=1.0,  # Always real cost
    )

    # Save trace
    trace_path = os.path.join(OUTPUT_DIR, "traces", f"{label}.json")
    with open(trace_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved trace: {trace_path}")
    return result


def main():
    # --- Tuning: EI (10x), paramnet:letter:steps ---
    print("=" * 60)
    print("TUNING: paramnet:letter:steps, EI (10x), temp=0.7")
    print("=" * 60)
    tuning_budget = TUNING_BASE_COST * COST_MULT
    print(f"Budget: {TUNING_BASE_COST:.1f} × {COST_MULT} = {tuning_budget:.1f}s")

    tuning_args = make_args(
        scenario="tuning",
        tuning_task="hpobench:paramnet:letter:steps",
        temperature=0.7,
        time_budget=tuning_budget,
    )
    tuning_result = run_trace(TUNING_SCENARIO, tuning_args, "tuning_letter_ei10")

    perf = tuning_result.get("answer_perf")
    print(f"Perf: {perf}, Evals: {tuning_result['evaluations']}, "
          f"Overhead: {tuning_result['total_overhead']:.1f}s, "
          f"Aborted: {tuning_result['aborted']}")

    # --- Audit: EI (10x), doc 0 ---
    print("\n" + "=" * 60)
    print("AUDIT: cc-large doc 0, EI (10x), temp=0.0")
    print("=" * 60)
    audit_budget = AUDIT_BASE_COST * COST_MULT
    print(f"Budget: {AUDIT_BASE_COST:.1f} × {COST_MULT} = {audit_budget:.1f}s")

    audit_args = make_args(
        scenario="evidence_audit",
        temperature=0.0,
        time_budget=audit_budget,
        question_index=0,
        cc_split="cc-large",
    )
    audit_result = run_trace(AUDIT_SCENARIO, audit_args, "audit_doc0_ei10")

    perf = audit_result.get("answer_perf")
    metrics = audit_result.get("answer_metrics")
    print(f"Perf: {perf}, Metrics: {metrics}, Evals: {audit_result['evaluations']}, "
          f"Overhead: {audit_result['total_overhead']:.1f}s, "
          f"Aborted: {audit_result['aborted']}")


if __name__ == "__main__":
    main()
