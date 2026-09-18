#!/usr/bin/env python3
"""Replay newly executed Search/Audit controls from minimal public inputs.

This scores new runtime results, not a hypothetical truncated historical trace.
No private trace, dataset download, Git history, or model call is required.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import math
import statistics
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from expgym import tool_protocol as protocol
from expgym import poolact, task_evidence_audit as audit, task_restricted_search as search

CORE_COMMIT = "0e6c51b6d86f42437038518c2fc8adc510901c0b"
CODE_FILES = ("expgym/tool_protocol.py", "expgym/poolact.py", "expgym/task_evidence_audit.py", "expgym/task_restricted_search.py")


def jdump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(jdump(value).encode()).hexdigest()


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if a is None or b is None:
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
    return a == b


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def score_slot(row):
    slot, gold = row["slot"], row["gold"]
    scenario = slot["scenario"]
    if scenario == "evidence_audit":
        audit._get_doc = lambda index: types.SimpleNamespace(annotations=gold["annotations"])
        audit._get_labels = lambda split: {k: v for k, v in gold["labels"].items() if not audit.CC_SPLITS.get(split) or k in audit.CC_SPLITS[split]}
        evaluator = audit.build_answer_evaluator(0, gold["cc_split"])
    elif scenario == "restricted_search":
        evaluator = lambda text, records=None: search._name_f1(text, gold["answers"])
    else:
        raise ValueError("Only Search/Audit control inputs are accepted")
    results, agents, overlays = [], [], []
    for a in row["agents"]:
        raw = a["terminal"]
        eligible = raw["api_state"] == "success" and raw["finish_reason"] != "length" and not raw["native_tool_calls_present"]
        answer = protocol.parse_final_answer(raw["content"], allow_unlabelled=a["allow_unlabelled"]) if eligible else None
        assert answer == a["saved_answer"], (slot["slot_id"], a["agent_id"], "saved answer differs from frozen runtime boundary")
        score = evaluator(answer or "", a.get("tool_records", []))
        metrics = score if isinstance(score, dict) else {"f1": score}
        perf = metrics["label_acc"] if scenario == "evidence_audit" else metrics["f1"]
        assert same(metrics, a["saved_metrics"]), (slot["slot_id"], a["agent_id"], "saved score mismatch")
        assert same(perf, a["saved_perf"])
        results.append({"answer": answer, "answer_perf": perf, "answer_metrics": score if isinstance(score, dict) else None})
        agents.append({**{k: slot[k] for k in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item", "seed")},
                       "agent_id": a["agent_id"], "result_sha256": row["source"]["result_sha256"],
                       "new_job_id": row["source"]["new_job_id"], "answer_sha256": digest(answer),
                       "answer_present": answer is not None, "legacy_metrics_json": jdump(a.get("legacy_metrics")),
                       "existing_trace_rescored_metrics_json": jdump(a.get("existing_trace_rescored_metrics")),
                       "new_runtime_metrics_json": jdump(metrics), "parser_sha256": row["source"]["parser_sha256"],
                       "source_layer": "new_runtime_control", "terminal_raw_sha256": raw["raw_dump_sha256"]})
        overlays.append({**{k: slot[k] for k in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item")},
                         "agent_id": a["agent_id"], "source_sha256": row["source"]["result_sha256"],
                         "new_answer": answer, "new_scoring_input": answer or "", "new_score_metrics": metrics,
                         "source_origin": "new_runtime_control", "answer_changed_reason": "fresh_run_under_fixed_terminal_protocol"})
    if slot["system"] == "expgym":
        assert len(results) == 1 and row["agents"][0]["agent_id"] == -1
        metrics = results[0]["answer_metrics"] if scenario == "evidence_audit" else {"f1": results[0]["answer_perf"]}
        if scenario == "evidence_audit":
            metrics = {k: metrics[k] for k in ("evidence_acc", "label_acc")}
    else:
        assert len(results) == 4 and [a["agent_id"] for a in row["agents"]] == [0, 1, 2, 3]
        aggregate = poolact.aggregate_results(scenario, results, answer_evaluator=evaluator)
        recorded = row["saved_aggregate"]
        assert aggregate["answer"] == recorded["answer"]
        assert same(aggregate["answer_perf"], recorded["answer_perf"])
        assert same(aggregate["answer_metrics"], recorded["answer_metrics"])
        if scenario == "evidence_audit":
            metrics = {**{f"{k}_mv": aggregate["answer_metrics"][k] for k in ("evidence_acc", "label_acc")},
                       **{f"{k}_mi": statistics.mean(a["answer_metrics"][k] for a in results) for k in ("evidence_acc", "label_acc")}}
        else:
            metrics = {"f1_mv": aggregate["answer_perf"], "f1_mi": statistics.mean(a["answer_perf"] for a in results)}
        overlays.append({"slot_id": slot["slot_id"], "agent_id": "aggregate", "scenario": scenario,
                         "new_answer": aggregate["answer"], "new_scoring_input": aggregate["answer"],
                         "new_score_metrics": aggregate["answer_metrics"] or {"f1": aggregate["answer_perf"]},
                         "source_sha256": row["source"]["result_sha256"], "source_origin": "new_runtime_control"})
    assert set(metrics) == set(json.loads(slot["metrics_json"]))
    updated = dict(slot, metrics_json=json.dumps(metrics, sort_keys=True), execution_complete="True", score_complete="True",
                   provider_cohort="preserved_historical_provider", cohort_id="terminal_protocol_control_20260918_" + row["model_alias"])
    comparison = {**{k: slot[k] for k in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item", "seed")},
                  "legacy_metrics_json": jdump(row["legacy_metrics"]), "existing_trace_rescored_metrics_json": slot["metrics_json"],
                  "new_runtime_metrics_json": jdump(metrics), "changed_from_legacy": not same(row["legacy_metrics"], metrics),
                  "changed_from_existing_trace_rescore": not same(json.loads(slot["metrics_json"]), metrics),
                  "selection_reason": "raw_API_verified_earlier_natural_stop", "source_layer": "new_runtime_control",
                  "old_result_sha256": row["source"]["old_result_sha256"], "result_sha256": row["source"]["result_sha256"],
                  "new_job_id": row["source"]["new_job_id"]}
    return updated, agents, comparison, overlays


def replay(rows, output):
    # Collector objects and gzip-loaded objects must yield identical column
    # order. The public package serializes all dictionaries canonically.
    rows = [json.loads(jdump(row)) for row in rows]
    code = {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in CODE_FILES}
    slots, members, changes, overlays = [], [], [], []
    for row in rows:
        assert row["source"]["parser_sha256"] == code["expgym/tool_protocol.py"]
        slot, agents, change, answers = score_slot(row)
        slots.append(slot); members.extend(agents); changes.append(change); overlays.extend(answers)
    assert len({r["slot_id"] for r in slots}) == len(slots)
    assert code == {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in CODE_FILES}
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "slot_scalars.csv", slots)
    write_csv(output / "agent_rows.csv", members)
    write_csv(output / "sample_diff.csv", changes)
    write_csv(output / "SOURCE_INVENTORY.csv", [r["source"] for r in rows])
    private = output / "private"; private.mkdir(exist_ok=True)
    (private / "answer_overlays.jsonl").write_text("".join(jdump(r) + "\n" for r in overlays))
    checks = {"status": "PASS", "scope": "completed_auxiliary_runtime_controls_only", "slots": len(slots), "members": len(members),
              "code_sha256": code, "core_repair_commit": CORE_COMMIT, "parser": protocol.ANSWER_PROTOCOL_VERSION,
              "all_saved_final_answers_reextracted": True, "all_saved_individual_and_pool_scores_recomputed": True,
              "model_calls": 0, "raw_traces_required_for_replay": False, "dataset_download_required_for_replay": False,
              "global_formal_adoption_claim": False}
    (output / "CHECKS.json").write_text(json.dumps(checks, indent=2) + "\n")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with gzip.open(args.inputs, "rt") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    print(json.dumps(replay(rows, args.output), indent=2))


if __name__ == "__main__":
    main()
