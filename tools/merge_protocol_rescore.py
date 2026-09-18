#!/usr/bin/env python3
"""Join exhaustive component rescoring by immutable registered slot identity.

This is an adoption-neutral join: all outputs retain the
``existing_trace_rescored`` layer. Runtime graph repairs require fresh controls.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def read(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write(path, rows, fields=None):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fields or list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def same(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(same(left[k], right[k]) for k in left)
    if left is None or right is None:
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(left - right) < 1e-10
    return left == right


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def yes(value):
    return str(value).lower() == "true"


def main():
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=repo / "results/gemini-openrouter-20260917/main")
    parser.add_argument("--search-audit", type=Path, required=True)
    parser.add_argument("--hpo", type=Path, required=True)
    parser.add_argument("--sweep", type=Path, help="Optional 1170-row sweep for overlap verification and unique-source inventory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original = read(args.baseline / "slot_scalars.csv")
    selection = read(args.baseline / "SOURCE_SELECTION.csv")
    baseline = {r["slot_id"]: r for r in original}
    sources = {r["slot_id"]: r for r in selection}
    new_rows = {r["slot_id"]: r for r in read(args.search_audit / "slot_scalars.csv")}
    diffs = {r["slot_id"]: r for r in read(args.search_audit / "sample_diff.csv")}
    for row in read(args.hpo / "slot_metrics.csv"):
        slot_id = row["slot_id"]
        assert slot_id not in new_rows
        old = baseline[slot_id]
        assert same(json.loads(old["metrics_json"]), json.loads(row["old_metrics_json"]))
        assert row["source_sha256"] == sources[slot_id]["result_sha256"]
        new_rows[slot_id] = dict(old, metrics_json=json.dumps(json.loads(row["new_metrics_json"]), sort_keys=True), score_complete=row["new_score_complete"])
        diffs[slot_id] = {**{k: old[k] for k in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item", "outer_repeat", "order", "seed")},
                          "source_sha256": row["source_sha256"], "old_metrics_json": row["old_metrics_json"], "new_metrics_json": row["new_metrics_json"],
                          "score_changed": row["score_changed"], "aggregate_answer_changed": "False", "aggregate_parsed_content_changed": "False", "endpoint_score_changed": row["score_changed"], "change_reason": row["reason"], "score_layer": "existing_trace_rescored"}
    assert len(original) == len(new_rows) == len(diffs) == 4698
    assert set(baseline) == set(new_rows) == set(diffs) == set(sources)
    ordered_new, ordered_diff = [], []
    for old in original:
        slot_id = old["slot_id"]
        new = new_rows[slot_id]
        assert set(old) == set(new)
        assert all(old[k] == new[k] for k in old if k not in ("metrics_json", "score_complete"))
        assert same(json.loads(old["metrics_json"]), json.loads(diffs[slot_id]["old_metrics_json"]))
        assert same(json.loads(new["metrics_json"]), json.loads(diffs[slot_id]["new_metrics_json"]))
        assert yes(diffs[slot_id]["score_changed"]) == (not same(json.loads(old["metrics_json"]), json.loads(new["metrics_json"])))
        assert diffs[slot_id]["source_sha256"] == sources[slot_id]["result_sha256"]
        ordered_new.append(new)
        ordered_diff.append(diffs[slot_id])
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "slot_scalars.legacy.csv").write_bytes((args.baseline / "slot_scalars.csv").read_bytes())
    write(args.output / "slot_scalars.csv", ordered_new, list(original[0]))
    write(args.output / "sample_diff.csv", ordered_diff, list(ordered_diff[0]))
    write(args.output / "affected_scores.csv", [r for r in ordered_diff if yes(r["score_changed"])], list(ordered_diff[0]))
    write(args.output / "SOURCE_SELECTION.csv", [dict(r, scoring_layer="existing_trace_rescored", scoring_component="hpo" if r["scenario"] == "tuning" else "search_audit", scoring_protocol="final-answer-boundary-v2") for r in selection])
    checks = {"status": "PASS", "score_layer": "existing_trace_rescored", "adoption_neutral": True,
              "registered_slots": len(original), "all_original_sources_preserved": True,
              "all_slots_rescored": True, "registered_members": 11286,
              "slots_by_system_scenario": dict(Counter(r["system"] + "/" + r["scenario"] for r in original)),
              "old_score_complete": sum(yes(r["score_complete"]) for r in original),
              "new_score_complete": sum(yes(r["score_complete"]) for r in ordered_new),
              "score_changed_slots": sum(yes(r["score_changed"]) for r in ordered_diff),
              "score_changed_by_system_scenario": dict(Counter(r["system"] + "/" + r["scenario"] for r in ordered_diff if yes(r["score_changed"]))),
              "component_checks": {"search_audit": json.loads((args.search_audit / "CHECKS.json").read_text()), "hpo": json.loads((args.hpo / "CHECKS.json").read_text())},
              "input_sha256": {"baseline_slot_scalars": sha(args.baseline / "slot_scalars.csv"), "baseline_sources": sha(args.baseline / "SOURCE_SELECTION.csv"),
                               "search_audit_scalars": sha(args.search_audit / "slot_scalars.csv"), "hpo_slot_metrics": sha(args.hpo / "slot_metrics.csv")},
              "model_calls": 0, "runtime_graph_corrected_by_rescoring": False}
    checks["merge_script_sha256"] = sha(Path(__file__))
    if args.sweep:
        sweep = read(args.sweep / "SOURCE_SELECTION.csv")
        sweep_scores = {r["slot_id"]: r for r in read(args.sweep / "agent_rows.csv")}
        unique = [{"unique_slot_id": r["slot_id"], "cohort": "main", "model": r["model"], "system": r["system"], "scenario": r["scenario"], "regime_or_beta": r["regime"], "strategy": r["strategy"], "item": r["item"], "source_sha256": r["result_sha256"], "members": 1 if r["system"] == "expgym" else 4} for r in selection]
        overlap = 0
        for row in sweep:
            main_id = row["main_overlap_slot_id"]
            if main_id:
                assert row["source_sha256"] == sources[main_id]["result_sha256"]
                overlap += 1
            else:
                unique.append({"unique_slot_id": row["slot_id"], "cohort": "sweep_additional", "model": row["model_id"], "system": row["system"], "scenario": row["scenario"], "regime_or_beta": "beta=" + row["beta"], "strategy": row["strategy"], "item": row["item"], "source_sha256": row["source_sha256"], "members": 1})
        assert len(sweep) == 1170 and overlap == 234 and len(unique) == 5634
        assert len({r["unique_slot_id"] for r in unique}) == len(unique)
        assert sum(r["members"] for r in unique) == 12222
        write(args.output / "UNIQUE_SOURCE_SELECTION.csv", unique)
        checks["main_and_sweep"] = {"main_slots": 4698, "sweep_slots": 1170, "main_overlap": overlap, "additional_slots": 936, "unique_slots": len(unique), "unique_members": 12222, "overlap_source_hashes_matched": overlap, "score_join_check": json.loads((args.sweep / "BETA10_MAIN_JOIN_CHECK.json").read_text()), "sweep_checks": json.loads((args.sweep / "CHECKS.json").read_text())}
    (args.output / "CHECKS.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in checks.items() if k != "component_checks"}, indent=2))


if __name__ == "__main__":
    main()
