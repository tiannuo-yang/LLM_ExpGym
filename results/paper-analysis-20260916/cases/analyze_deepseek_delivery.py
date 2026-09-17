#!/usr/bin/env python3
"""Explain DeepSeek N1 tuning Gap0 using frozen scores, without rescoring.

Run with Python 3.10+: python -B analyze_deepseek_delivery.py [--check]
Only the three declared companion artifacts are written. Canonical traces are
read only for the two NAS101-C examples; private model reasoning is not emitted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean


OUT = Path(__file__).resolve().parent
REPORT = OUT.parent
FROZEN = REPORT.parent / "six-models-lineage-20260914"
MODEL = "deepseek-v4-flash-0731"
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
SEED_BY_REPEAT = {0: 2200, 1: 2204, 2: 2208}
CASE_TASK = "hpobench:nasbench101:C"
CASE_SEED = 2208
TOL = 1e-9


def close(a, b):
    assert math.isclose(a, b, rel_tol=0, abs_tol=TOL), (a, b)


def number(s):
    return float(s) if s != "" else None


def file_info(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data)}


def read_rows(path):
    with path.open(newline="") as handle:
        return [dict(row, _record=i) for i, row in enumerate(csv.DictReader(handle), 1)]


def csv_text(rows):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_case(row, strict_gap):
    path = Path(row["trace_path"])
    info = file_info(path)
    assert info["sha256"] == row["trace_sha256"], path
    trace = json.loads(path.read_text())
    assert trace["task"]["item"]["id"] == CASE_TASK
    assert trace["run"]["seed"] == CASE_SEED
    assert trace["task"]["budget"]["regime"] == row["regime"]
    assert trace["outcome"]["terminal_status"]["execution_complete"] is True
    calls = trace["tool_calls"]
    assert all(c["name"] == "evaluate_config" for c in calls)
    visible = [c for c in calls if c["visible_to_model"]
               and isinstance(c.get("performance"), (int, float))
               and math.isfinite(c["performance"])]
    performances = [c["performance"] for c in visible]
    outcome = trace["outcome"]
    scored = outcome["terminal_status"]["score_complete"]
    assert scored == (strict_gap is not None)
    assert len(calls) == int(row["attempted_evaluations"])
    assert len(visible) == int(row["delivered_evaluations"])
    assert outcome["termination_reason"] == row["termination"]
    assert sum(not c["visible_to_model"] for c in calls) == int(row["withheld_evaluations"])
    close(max(performances), float(row["best_observed_performance"]))
    assert performances.index(max(performances)) + 1 == int(row["first_best_observation_index"])
    final = outcome["score"]["value"]
    assert (final is None) == (row["final_performance"] == "")
    if final is not None:
        close(final, float(row["final_performance"]))
    failures = outcome.get("protocol_failures", [])
    info.update({
        "task": CASE_TASK, "seed": CASE_SEED, "regime": row["regime"],
        "trajectory_csv_data_record": row["_record"],
        "attempted_evaluations": len(calls),
        "delivered_evaluations": len(visible),
        "visible_error_results": sum(c["visible_to_model"] and c not in visible for c in calls),
        "withheld_evaluations": sum(not c["visible_to_model"] for c in calls),
        "delivered_performances_in_order": performances,
        "best_observed_performance": max(performances),
        "first_best_observation_index": performances.index(max(performances)) + 1,
        "termination": outcome["termination_reason"],
        "answer_present": outcome["answer"] is not None,
        "score_complete": scored, "final_performance": final,
        "answer_score_source": outcome.get("answer_score_source"),
        "strict_gap": strict_gap, "gap0": strict_gap if strict_gap is not None else 0.0,
        "protocol_failures": [{"agent_step": f["agent_step"], "forced": f["forced"],
                               "reason": f["reason"], "finish_reason": f.get("finish_reason")}
                              for f in failures],
        "last_two_calls": [{"forced": c["forced"], "finish_reason": c.get("finish_reason")}
                           for c in trace["llm_calls"][-2:]],
    })
    return info


def build():
    paths = {
        "trajectories": REPORT / "hpo/trajectories.csv",
        "repeat_scores": FROZEN / "by_repeat.csv",
        "absolute_scores": FROZEN / "absolute_settings.csv",
        "task_scores": REPORT / "rank/hpo_task_scores.csv",
    }
    source = {name: read_rows(path) for name, path in paths.items()}
    trajectories = [r for r in source["trajectories"] if r["model"] == MODEL]
    tr = {(r["task"], int(r["seed"]), r["regime"]): r for r in trajectories}
    assert len(trajectories) == len(tr) == 81
    repeats = [r for r in source["repeat_scores"] if r["model"] == MODEL
               and r["system"] == "expgym" and r["scenario"] == "tuning"
               and r["slice_kind"] == "task" and r["metric"] == "gap"]
    sr = {(r["slice"], SEED_BY_REPEAT[int(r["repeat"])], r["regime"]): r for r in repeats}
    assert len(repeats) == len(sr) == 81 and set(sr) == set(tr)
    for key, row in sr.items():
        assert row["expected_units"] == "1" and row["analysis_unit"] == "single_trace"
        scored = number(row["full_mean"]) is not None
        assert scored == (row["known_units"] == "1")
        assert scored == (tr[key]["score_complete"] == "True")
        if not scored:
            assert tr[key]["score_status"] == "unscorable_missing_configuration"
            assert tr[key]["score_cost_basis"] == "unscored_terminal"
    absolute = {(r["slice_kind"], r["slice"], r["regime"]): r
                for r in source["absolute_scores"] if r["model"] == MODEL
                and r["system"] == "expgym" and r["scenario"] == "tuning"
                and r["metric"] == "gap0"}
    tasks = sorted({key[0] for key in sr})
    assert len(tasks) == 9
    delivery = []
    family_summaries = []
    for regime in REGIMES:
        rows = [r for r in repeats if r["regime"] == regime]
        assert len(rows) == 27
        known = [number(r["full_mean"]) for r in rows if r["full_mean"] != ""]
        rate = len(known) / len(rows)
        conditional = mean(known)
        gap0 = sum(known) / len(rows)
        close(rate * conditional, gap0)
        frozen = absolute["all", "all", regime]
        close(gap0, float(frozen["full_mean"]))
        selected = [r for r in trajectories if r["regime"] == regime]
        delivery.append({
            "model": MODEL, "regime": regime, "expected_task_repeats": len(rows),
            "score_complete_task_repeats": len(known), "normal_missing_configuration": len(rows)-len(known),
            "score_complete_rate": rate, "conditional_strict_gap_repeat_equal": conditional,
            "gap0_all_task_repeats": gap0, "rate_times_conditional_gap": rate * conditional,
            "frozen_gap0": float(frozen["full_mean"]),
            "frozen_absolute_data_record": frozen["_record"],
            "mean_delivered_evaluations": mean(int(r["delivered_evaluations"]) for r in selected),
            "termination_counts": compact(dict(Counter(r["termination"] for r in selected))),
        })
        for family in ("nasbench101", "nasbench201", "paramnet"):
            family_rows = [r for r in rows if r["slice"].split(":")[1] == family]
            assert len(family_rows) == 9
            family_known = [number(r["full_mean"]) for r in family_rows if r["full_mean"] != ""]
            family_gap0 = sum(family_known) / 9
            close(family_gap0, float(absolute["family", family, regime]["full_mean"]))
            family_summaries.append({"family": family, "regime": regime, "expected": 9,
                                     "scored": len(family_known), "gap0": family_gap0,
                                     "conditional_strict_gap_repeat_equal": mean(family_known)})
    task_checks = 0
    for row in source["task_scores"]:
        if row["model"] != MODEL:
            continue
        vals = [number(sr[row["task"], seed, row["regime"]]["full_mean"])
                for seed in SEED_BY_REPEAT.values()]
        close(sum(v if v is not None else 0.0 for v in vals) / 3, float(row["gap0"]))
        task_checks += 1
    assert task_checks == 27

    pairs = []
    for task in tasks:
        for repeat, seed in SEED_BY_REPEAT.items():
            free, tight = [sr[task, seed, regime] for regime in (REGIMES[0], REGIMES[2])]
            ftr, ttr = [tr[task, seed, regime] for regime in (REGIMES[0], REGIMES[2])]
            fs, ts = number(free["full_mean"]), number(tight["full_mean"])
            f0, t0 = fs if fs is not None else 0.0, ts if ts is not None else 0.0
            transition = ("scored" if fs is not None else "missing") + "_to_" + ("scored" if ts is not None else "missing")
            pairs.append({
                "model": MODEL, "task": task, "family": task.split(":")[1], "repeat": repeat, "seed": seed,
                "transition": transition, "free_score_complete": fs is not None,
                "tight_score_complete": ts is not None, "free_strict_gap": fs, "tight_strict_gap": ts,
                "free_gap0": f0, "tight_gap0": t0, "tight_minus_free_gap0": t0-f0,
                "free_delivered_evaluations": int(ftr["delivered_evaluations"]),
                "tight_delivered_evaluations": int(ttr["delivered_evaluations"]),
                "free_best_observed_performance": number(ftr["best_observed_performance"]),
                "tight_best_observed_performance": number(ttr["best_observed_performance"]),
                "free_termination": ftr["termination"], "tight_termination": ttr["termination"],
                "free_repeat_csv_data_record": free["_record"], "tight_repeat_csv_data_record": tight["_record"],
                "free_trace_path": ftr["trace_path"], "tight_trace_path": ttr["trace_path"],
                "free_trace_sha256": ftr["trace_sha256"], "tight_trace_sha256": ttr["trace_sha256"],
            })
    assert len(pairs) == 27
    zero_case = next(r for r in pairs if r["task"] == "hpobench:nasbench101:A" and r["seed"] == 2204)
    assert zero_case["free_strict_gap"] == 0.0 and zero_case["free_score_complete"] is True
    assert zero_case["transition"] == "scored_to_scored"
    groups = []
    for transition in ("scored_to_scored", "missing_to_scored", "scored_to_missing", "missing_to_missing"):
        rows = [r for r in pairs if r["transition"] == transition]
        groups.append({
            "transition": transition, "pairs": len(rows),
            "free_gap0_mean_in_group": mean(r["free_gap0"] for r in rows),
            "tight_gap0_mean_in_group": mean(r["tight_gap0"] for r in rows),
            "contribution_to_all_27_delta": sum(r["tight_minus_free_gap0"] for r in rows) / 27,
            "tight_better": sum(r["tight_minus_free_gap0"] > TOL for r in rows),
            "tight_worse": sum(r["tight_minus_free_gap0"] < -TOL for r in rows),
            "ties": sum(abs(r["tight_minus_free_gap0"]) <= TOL for r in rows),
        })
    delta = delivery[2]["gap0_all_task_repeats"] - delivery[0]["gap0_all_task_repeats"]
    close(sum(r["contribution_to_all_27_delta"] for r in groups), delta)
    assert [r["pairs"] for r in groups] == [19, 6, 1, 1]
    assert [groups[0][k] for k in ("tight_better", "tight_worse", "ties")] == [4, 12, 3]
    assert [r["score_complete_task_repeats"] for r in delivery] == [20, 25, 25]

    cases = [canonical_case(tr[CASE_TASK, CASE_SEED, regime],
                            number(sr[CASE_TASK, CASE_SEED, regime]["full_mean"]))
             for regime in (REGIMES[0], REGIMES[2])]
    fc, tc = cases
    assert (fc["delivered_evaluations"], tc["delivered_evaluations"]) == (9, 3)
    assert (fc["first_best_observation_index"], tc["first_best_observation_index"]) == (3, 3)
    assert (fc["attempted_evaluations"], tc["attempted_evaluations"]) == (10, 5)
    assert fc["termination"] == "empty_model_response" and fc["answer_present"] is False
    assert fc["last_two_calls"] == [{"forced": False, "finish_reason": "stop"},
                                     {"forced": True, "finish_reason": "stop"}]
    assert {f["reason"] for f in fc["protocol_failures"]} >= {
        "LLM returned empty response", "Forced final returned empty response"}
    assert tc["termination"] == "time_budget_exceeded" and tc["answer_present"] is True
    assert tc["withheld_evaluations"] == 1 and tc["answer_score_source"] == "matching_tool_call"
    assert tc["last_two_calls"][-1] == {"forced": True, "finish_reason": "stop"}
    close(fc["best_observed_performance"], 0.9412393172581991)
    close(tc["best_observed_performance"], 0.8955996036529541)
    close(tc["final_performance"], tc["best_observed_performance"])
    close(tc["gap0"], 91.15695048809212)

    free_missing = [r for r in pairs if not r["free_score_complete"]]
    recovered = [r for r in pairs if r["transition"] == "missing_to_scored"]
    better_observed_free = [r for r in recovered
                            if r["free_best_observed_performance"] is not None
                            and r["tight_best_observed_performance"] is not None
                            and r["free_best_observed_performance"] > r["tight_best_observed_performance"] + TOL]
    assert len(free_missing) == 7 and all(r["free_delivered_evaluations"] > 0 for r in free_missing)
    assert len(better_observed_free) == 4
    others = [r for r in source["trajectories"] if r["model"] != MODEL]
    assert len(others) == 399 and all(r["score_complete"] == "True" for r in others)
    checks = {
        "schema": "paper-analysis.deepseek-delivery.v1", "status": "PASS",
        "inputs": {name: file_info(path) for name, path in paths.items()},
        "definitions": {
            "analysis_unit": "one original selected N1 tuning task-repeat; nine tasks times three repeats per regime",
            "seed_by_repeat": SEED_BY_REPEAT,
            "source_record_index": "one-based CSV data record, excluding the header; not a physical line index",
            "score_complete": "frozen strict Gap is present, including genuinely scored zero; not necessarily natural submission or submitted-only scoring",
            "conditional_strict_gap_repeat_equal": "arithmetic mean of strict Gap over scored task-repeats; differs from task-equal known-subset summaries when scored repeat counts differ",
            "gap0": "existing convention: retain frozen strict Gap where available; zero only the selected normal missing-configuration outcomes; never zero failures or unexecuted items",
            "identity": "Gap0 = scored_task_repeats / 27 * mean(strict Gap | scored task-repeat)",
            "paired_contribution": "sum(Tight Gap0 - Free Gap0) within transition group divided by all 27 pairs",
            "observed_performance": "finite performance visible to the agent; not normalized Gap; hidden over-budget results excluded",
        },
        "validation": {"matched_repeat_and_trajectory_records": 81, "task_gap0_checks": task_checks,
                       "family_gap0_checks": len(family_summaries), "overall_gap0_checks": 3,
                       "matched_free_tight_pairs": len(pairs), "canonical_case_hashes_verified": 2,
                       "scored_zero_kept_in_scored_denominator": True,
                       "new_model_calls": 0, "rescored_outcomes": 0},
        "overall_tight_minus_free_gap0": delta,
        "paired_decomposition": groups,
        "family_summary": family_summaries,
        "case": cases,
        "supporting_counts": {
            "free_missing_configurations": len(free_missing),
            "free_missing_with_visible_performance": sum(r["free_delivered_evaluations"] > 0 for r in free_missing),
            "free_missing_visible_evaluations_min": min(r["free_delivered_evaluations"] for r in free_missing),
            "free_missing_visible_evaluations_max": max(r["free_delivered_evaluations"] for r in free_missing),
            "free_missing_termination_counts": dict(sorted(Counter(r["free_termination"] for r in free_missing).items())),
            "free_missing_tight_scored_pairs": len(recovered),
            "those_pairs_with_better_free_best_observed_performance": len(better_observed_free),
            "other_models_completed_hpo_trajectories": len(others),
            "other_models_score_complete_hpo_trajectories": sum(r["score_complete"] == "True" for r in others),
        },
        "interpretation_boundaries": [
            "The decomposition is descriptive accounting, not a causal effect of earlier stopping or shorter histories.",
            "The both-scored subset is selected after observing outcomes; it explains the aggregate reversal but must not replace the official all-item result.",
            "Observed best performance in an unscored trace is diagnostic only; it is never substituted for the final score.",
            "Gap uses the inherited final-scoring policy, including legacy fallback where present; score completeness is not proof of a correctly submitted configuration.",
            "A scored zero is different from missing configuration and remains in the scored denominator.",
            "The selected DeepSeek N1 cohort is the original cohort, not the later targeted N4 rerun.",
            "Empty final output is established; these records do not establish a unique model, protocol, serving, or context-length cause.",
            "The missing-configuration reversal is concentrated in DeepSeek here, not demonstrated as a universal cross-model effect.",
        ],
    }
    return {"deepseek_delivery.csv": csv_text(delivery),
            "deepseek_paired_delivery.csv": csv_text(pairs),
            "deepseek_delivery_checks.json": json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True) + "\n"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare generated bytes without writing")
    args = parser.parse_args()
    artifacts = build()
    for filename, content in artifacts.items():
        path = OUT / filename
        expected = content.encode("utf-8")
        if args.check:
            assert path.read_bytes() == expected, f"stale artifact: {path}"
        else:
            path.write_bytes(expected)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write",
                      "artifacts": list(artifacts), "paired_units": 27,
                      "canonical_traces_checked": 2, "new_model_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
