#!/usr/bin/env python3
"""Rebuild final main adoption from separately re-scored HPO/aux components.

This is a source-assignment check, not an additional scorer invocation. Run the
HPO and auxiliary scoring-input replayers first. No private paths or Git needed.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if a is None or b is None:
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
    return a == b


def merge(stage, selected, replacements, new_sources):
    assert len(stage) == len(selected) == 4698
    before = {r["slot_id"]: r for r in stage}
    assert len(before) == 4698 and set(before) == {r["slot_id"] for r in selected}
    assert len(replacements) == len(new_sources) == 21 and set(replacements) == set(new_sources)
    for sid, row in replacements.items():
        assert before[sid]["scenario"] != "tuning", "Auxiliary controls cannot overwrite HPO stage"
        assert set(before[sid]) == set(row)
        for key in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item", "outer_repeat", "order", "seed", "family"):
            assert row[key] == before[sid][key], (sid, key)
    merged = [replacements.get(r["slot_id"], r) for r in stage]
    assert sum(r["slot_id"] not in replacements and r == stage[i] for i, r in enumerate(merged)) == 4677
    sources = [dict(r) for r in selected]
    for row in sources:
        sid = row["slot_id"]
        if sid in replacements:
            source, scalar = new_sources[sid], replacements[sid]
            assert row["result_sha256"] == source["old_result_sha256"]
            assert source["members"] in ("1", "4", 1, 4)
            assert int(source["members"]) == (1 if row["system"] == "expgym" else 4)
            row.update(old_result_sha256=row["result_sha256"], old_historical_trajectory=row.get("historical_trajectory", ""), old_new_result_index=row.get("new_result_index", ""),
                       result_sha256=source["result_sha256"], cohort_id=scalar["cohort_id"], provider=scalar["provider_cohort"],
                       selection="new_runtime_terminal_protocol_control", historical_trajectory="", new_result_index="",
                       new_result_path=source["result_path"], new_job_id=source["new_job_id"], runtime_source_tree_sha256=source["runtime_source_tree_sha256"],
                       runtime_core_commit=source["runtime_core_commit"], runtime_snapshot_commit=source["runtime_snapshot_commit"], execution_complete=scalar["execution_complete"], score_complete=scalar["score_complete"])
    return merged, sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hpo-stage", type=Path, required=True)
    parser.add_argument("--hpo-manifest", type=Path, required=True)
    parser.add_argument("--aux-dir", type=Path, required=True)
    parser.add_argument("--total-manifest", type=Path, required=True)
    parser.add_argument("--base-legacy-scalars", type=Path, required=True)
    parser.add_argument("--base-rescored-scalars", type=Path, required=True)
    parser.add_argument("--base-sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    hpo, total = [json.loads(p.read_text()) for p in (args.hpo_manifest, args.total_manifest)]
    assert hpo["status"] == "PASS" and hpo["adoption_ready"] is True and hpo["verified_complete_pools"] == 97
    assert total["status"] == "PASS" and total["adoption_ready"] is True and total["total_main_runtime_adoption"] is True
    assert total["main_slots"] == 4698 and total["hpo_verified_pools"] == 97 and total["auxiliary_verified_main_slots"] == 21 and total["auxiliary_verified_members"] == 78
    assert total["hpo_stage_manifest_sha256"] == sha(args.hpo_manifest)
    gate = total["sweep_control_gate"]
    if gate["required"]:
        assert gate["status"] == "PASS" and gate["verified_slots"] == gate["registered_slots"] == total["sweep_additional_slots"]
    assert sha(args.hpo_stage / "slot_scalars.csv") == hpo["official_slot_scalars_sha256"]
    assert sha(args.hpo_stage / "SOURCE_SELECTION.csv") == hpo["official_source_selection_sha256"]
    stage, selection = [read_csv(args.hpo_stage / f) for f in ("slot_scalars.csv", "SOURCE_SELECTION.csv")]
    replacements = {r["slot_id"]: r for r in read_csv(args.aux_dir / "slot_scalars.csv")}
    sources = {r["slot_id"]: r for r in read_csv(args.aux_dir / "SOURCE_INVENTORY.csv")}
    merged, selected = merge(stage, selection, replacements, sources)
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "slot_scalars.csv", merged, list(stage[0]))
    write_csv(args.output / "SOURCE_SELECTION.csv", selected)
    baseline_paths = {"legacy_scalars": args.base_legacy_scalars, "rescored_scalars": args.base_rescored_scalars, "source_selection": args.base_sources}
    for name, path in baseline_paths.items():
        assert sha(path) == total["base_input_sha256"][name], (name, "baseline input changed")
    legacy, rescored, original = [{r["slot_id"]: r for r in read_csv(path)} for path in baseline_paths.values()]
    selected_by = {r["slot_id"]: r for r in selected}
    assert len(legacy) == len(rescored) == len(original) == 4698
    assert set(legacy) == set(rescored) == set(original) == set(selected_by)
    diffs = []
    for row in merged:
        sid = row["slot_id"]; adopted = selected_by[sid]
        before, middle, after = [json.loads(r["metrics_json"]) for r in (legacy[sid], rescored[sid], row)]
        diffs.append({**{k: row[k] for k in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item", "outer_repeat", "order", "seed")},
                      "legacy_metrics_json": canonical(before), "existing_trace_rescored_metrics_json": canonical(middle),
                      "new_official_metrics_json": canonical(after), "changed_from_legacy": not same(before, after),
                      "changed_from_existing_trace_rescore": not same(middle, after),
                      "legacy_source_sha256": original[sid]["result_sha256"], "adopted_source_sha256": adopted["result_sha256"],
                      "source_changed": original[sid]["result_sha256"] != adopted["result_sha256"],
                      "adoption_reason": "terminal_protocol_runtime_control" if sid in replacements else "hpo_graph_runtime_control" if adopted.get("new_result_path") else "retained_existing_trace_rescore"})
    write_csv(args.output / "sample_diff.csv", diffs)
    write_csv(args.output / "auxiliary_slot_diff.csv", read_csv(args.aux_dir / "sample_diff.csv"))
    hashes = {f: sha(args.output / f) for f in ("slot_scalars.csv", "SOURCE_SELECTION.csv", "sample_diff.csv", "auxiliary_slot_diff.csv")}
    assert hashes["slot_scalars.csv"] == total["official_slot_scalars_sha256"]
    assert hashes["SOURCE_SELECTION.csv"] == total["official_source_selection_sha256"]
    assert hashes["sample_diff.csv"] == total["official_sample_diff_sha256"]
    assert hashes["auxiliary_slot_diff.csv"] == sha(args.aux_dir / "sample_diff.csv")
    checks = {"status": "PASS", "scope": "source-assignment rebuild after separate scorer replays", "main_slots": 4698,
              "hpo_stage_pools": 97, "auxiliary_whole_slots": 21, "auxiliary_members": 78,
              "preserved_hpo_stage_slots": 4677, "output_sha256": hashes, "network_calls": 0}
    (args.output / "CHECKS.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
