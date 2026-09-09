"""Explicit post-loop task-abstention policy; never retries a model decision.

Only a normally returned LoopResult may enter this policy. The raw terminal
snapshot is already owned by TerminalEvidence. HTTP/tool/scorer/persistence
exceptions are not handled here and remain infrastructure/integrity failures.
"""
from __future__ import annotations

import copy
import json
import math

POLICY = "task-abstention-v1"
SCHEMA = "expgym.execution-terminal.v1"
SCENARIOS = {"tuning", "restricted_search", "evidence_audit"}


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def mark_loop_return(result, scenario, policy="error"):
    if policy == "error":
        return
    if policy != POLICY or scenario not in SCENARIOS:
        raise ValueError("Unknown missing-final policy or scenario")
    # Called only after evidence.loop returns; no exception-to-answer coercion.
    if type(result) is not dict or "answer" not in result or not (result["answer"] is None or type(result["answer"]) is str):
        raise ValueError("Malformed returned loop answer")
    if (type(result.get("api_calls")) is not int or result["api_calls"] < 0
            or type(result.get("aborted")) is not bool or type(result.get("termination_reason")) is not str
            or type(result.get("tool_records")) is not list or type(result.get("eval_records")) is not list
            or not finite(result.get("total_overhead")) or result["total_overhead"] < 0):
        raise ValueError("Malformed returned loop evidence")
    result.update(missing_final_policy=POLICY, terminal_origin="normal_loop_return", terminal_scenario=scenario)


def _normal_terminal(result):
    if (result.get("missing_final_policy") != POLICY or result.get("terminal_origin") != "normal_loop_return"
            or result.get("terminal_scenario") not in SCENARIOS or "answer" not in result):
        raise ValueError("Explicit normally-returned terminal policy required")


def is_policy_missing(result):
    return result.get("missing_final_policy") == POLICY and result.get("answer") is None


def score_missing(result, evaluator, *, commit, float_close, metrics_close):
    """The independent check reuses the original evaluator, not a zero rule."""
    _normal_terminal(result)
    if result["answer"] is not None:
        raise ValueError("Missing-final scorer requires the original None answer")
    scenario = result["terminal_scenario"]
    if scenario == "tuning":
        # No configuration exists. Never call a tuning tool or best-observed
        # fallback and never invent performance/Gap for the missing endpoint.
        if evaluator is not None or result.get("answer_perf") is not None or result.get("answer_metrics") is not None:
            raise ValueError("Missing configuration cannot carry a task score")
        if commit:
            result.update(scoring_input=None, score_status="unscorable_missing_configuration")
        return {"ok": False, "reason": "unscorable_missing_configuration", "score_complete": False,
                "policy_version": POLICY, "scoring_input": None, "reported_perf": None}
    if evaluator is None:
        raise ValueError("Search/Audit abstention requires the original evaluator")
    from expgym.react_loop import _finalize_answer, _unpack_perf
    raw, overhead = _finalize_answer("", result.get("eval_records", []), evaluator,
                                     result.get("tool_records", []), result["total_overhead"])
    performance, metrics = _unpack_perf(raw)
    if not finite(performance):
        raise ValueError("Empty prediction evaluator did not produce a finite score")
    if commit:
        result.update(scoring_input="", score_status="scored_empty_prediction", answer_perf=performance,
                      answer_metrics=copy.deepcopy(metrics), answer_overhead=overhead,
                      answer_score_source="offline_empty_prediction")
    ok = (result.get("scoring_input") == "" and result.get("score_status") == "scored_empty_prediction"
          and result.get("answer_score_source") == "offline_empty_prediction"
          and float_close(result.get("answer_perf"), performance)
          and float_close(result.get("answer_overhead"), overhead))
    if metrics is None:
        ok = ok and result.get("answer_metrics") is None
    else:
        ok = ok and isinstance(result.get("answer_metrics"), dict) and metrics_close(result["answer_metrics"], metrics)
    return {"ok": bool(ok), "score_complete": bool(ok), "policy_version": POLICY, "scoring_input": "",
            "recomputed_perf": performance, "recomputed_metrics": metrics,
            "reported_perf": result.get("answer_perf"), "reported_metrics": result.get("answer_metrics")}


def status_for(result, check):
    _normal_terminal(result)
    if not {"scoring_input", "score_status", "answer_perf", "answer_metrics"}.issubset(result):
        raise ValueError("Explicit policy score fields required")
    missing = result["answer"] is None
    if not missing and (type(result["answer"]) is not str or result.get("scoring_input") != result["answer"]
                        or result.get("score_status") != "scored_final_answer"):
        raise ValueError("Final answer and independent scoring input differ")
    scored = type(check) is dict and check.get("ok") is True and finite(result.get("answer_perf"))
    unknown = (missing and result["terminal_scenario"] == "tuning" and type(check) is dict
               and check.get("ok") is False and check.get("reason") == "unscorable_missing_configuration"
               and check.get("score_complete") is False and check.get("policy_version") == POLICY
               and result.get("score_status") == "unscorable_missing_configuration"
               and result.get("scoring_input") is None and result.get("answer_perf") is None
               and result.get("answer_metrics") is None)
    complete = bool(scored or unknown)
    return {"schema_version": SCHEMA, "policy_version": POLICY, "execution_complete": complete,
            "score_complete": bool(scored), "terminal_classification": (
                "model_no_answer" if complete and missing else "completed_scored" if complete else "integrity_failure"),
            "model_no_answer_count": int(missing), "expected_model_terminals": 1, "reported_model_terminals": 1}


def finish_score(result, check):
    if result.get("missing_final_policy") == POLICY:
        if result.get("answer") is not None:
            result.update(scoring_input=copy.deepcopy(result["answer"]), score_status="scored_final_answer")
        result["terminal_status"] = status_for(result, check)
    return check


def terminal_publishable(result, recomputed_check=None):
    """Execution completion is not finite-score completion or raw-file proof.

    Offline consumers MUST pass an independently recomputed check. The source
    runner may omit it only immediately after its own score-check call.
    """
    check = result.get("score_check") if recomputed_check is None else recomputed_check
    if result.get("missing_final_policy", "error") == "error":
        return type(check) is dict and check.get("ok") is True
    try:
        expected = status_for(result, check)
        return expected["execution_complete"] and canonical(result.get("terminal_status")) == canonical(expected)
    except (ValueError, TypeError, KeyError):
        return False


def aggregate_terminal(scenario, results, *, answer_evaluator, original_aggregate):
    active = [result.get("missing_final_policy", "error") for result in results]
    if POLICY not in active:
        return original_aggregate(scenario, results, answer_evaluator=answer_evaluator)
    if not results or any(policy != POLICY for policy in active) or any(
            result.get("terminal_scenario") != scenario or not terminal_publishable(result) for result in results):
        raise ValueError("Complete policy-consistent terminals required for the entire pool")
    known = [result for result in results if result["terminal_status"]["score_complete"]]
    if scenario == "tuning" and len(known) != len(results):
        aggregate = {"method": "best_of_n", "answer": None, "answer_perf": None, "answer_metrics": None,
                     "individual_answers": [result.get("answer") or "" for result in results],
                     "individual_perfs": [result.get("answer_perf") for result in results],
                     "diagnostics": {"full_pool_endpoint": "unknown_missing_configuration"}}
    else:
        # Keep ALL N answer slots and original tie/parse rules. Original Audit
        # aggregate evaluator uses [] records, never concatenated agent tools.
        aggregate = original_aggregate(scenario, results, answer_evaluator=answer_evaluator)
        if not finite(aggregate.get("answer_perf")):
            raise ValueError("Complete pool aggregate must have a finite score")
    missing = sum(result["answer"] is None for result in results)
    aggregate["mean_individual_perf"] = (sum(result["answer_perf"] for result in known) / len(results)
                                           if len(known) == len(results) else None)
    aggregate["known_subset_descriptive"] = {
        "n_known": len(known), "n_total": len(results), "not_full_pool_endpoint": len(known) != len(results),
        "mean_perf": sum(result["answer_perf"] for result in known) / len(known) if known else None,
        "best_perf": max(result["answer_perf"] for result in known) if known else None}
    aggregate["terminal_status"] = {"schema_version": SCHEMA, "policy_version": POLICY,
        "execution_complete": True, "score_complete": finite(aggregate.get("answer_perf")),
        "terminal_classification": "model_no_answer" if missing else "completed_scored",
        "model_no_answer_count": missing, "expected_model_terminals": len(results), "reported_model_terminals": len(results)}
    return aggregate


def aggregate_publishable(aggregate):
    status = aggregate.get("terminal_status")
    if status is None:
        return finite(aggregate.get("answer_perf"))
    return (type(status) is dict and status.get("schema_version") == SCHEMA and status.get("policy_version") == POLICY
            and status.get("execution_complete") is True and type(status.get("score_complete")) is bool
            and (finite(aggregate.get("answer_perf")) if status["score_complete"] else
                 aggregate.get("answer_perf") is None and aggregate.get("diagnostics", {}).get("full_pool_endpoint") == "unknown_missing_configuration"))
