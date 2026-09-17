#!/usr/bin/env python3
"""Join frozen scientific slots to copied trajectories and local raw archives.

Reads only metadata/manifests here; copied trajectory hashes are compared to
the original per-member archive identities. No scoring or model calls.
"""
from __future__ import annotations
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil

COMMIT = "ad03e8c42ca501016176ee1bc407b38499178506"


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def truth(value):
    return str(value).lower() in {"true", "1"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--delivery", type=Path, required=True)
    args = parser.parse_args()
    root, work = args.delivery, args.work
    original = read_csv(work / "selected_slots.csv")
    copied = {r["slot_id"]: r for r in read_csv(root / "index/selected_slots.csv")}
    assert len(copied) == len(original) == 4698
    critical = ["slot_id", "model", "system", "scenario", "regime", "strategy", "item", "outer_repeat", "order", "seed", "N", "cohort_id", "execution_complete", "score_complete", "status", "result_path", "result_sha256"]
    for row in original:
        prior = copied[row["slot_id"]]
        assert all(row[k] == prior[k] for k in critical), ("changed scientific or content binding", row["slot_id"])

    member_inputs = [root / "raw_archives/MEMBERS.csv", root / "raw_archives/gemini_snapshot/MEMBERS.csv"]
    by_cohort = defaultdict(list)
    member_count = 0
    for table in member_inputs:
        with table.open(newline="") as handle:
            for row in csv.DictReader(handle):
                cid = row.get("cohort_id") or row.get("source_id")
                assert cid
                row["cohort_id"] = cid
                row["member_table"] = table.relative_to(root).as_posix()
                by_cohort[cid].append(row)
                member_count += 1
    positions, exact = {}, defaultdict(list)
    for cid, rows in by_cohort.items():
        rows.sort(key=lambda x: x["original_path"])
        positions[cid] = [r["original_path"] for r in rows]
        for r in rows:
            exact[cid, r["original_path"]].append(r)

    final, bad, coverage, locations = [], [], Counter(), {}
    for row in original:
        prior = copied[row["slot_id"]]
        for key in ("trajectory_file", "trajectory_bytes", "trajectory_sha256", "embedded_agents", "trajectory_identity_check"):
            row[key] = prior[key]
        cid = row["cohort_id"]
        result = exact.get((cid, row["result_path"]), [])
        row.update(result_archive_file="", result_archive_member="", result_archive_logical_member="", result_member_table="", result_archive_identity="not_completed", dump_member_count=0, dump_bytes=0, dump_archives_json="[]", dump_member_table="", dump_scope="", dump_status="not_started_or_not_snapshot_bound")
        if truth(row["execution_complete"]):
            matches = [r for r in result if r["sha256"] == row["trajectory_sha256"] and int(r["bytes"]) == int(row["trajectory_bytes"])]
            if not matches:
                bad.append({"slot_id":row["slot_id"], "cohort_id":cid, "path":row["result_path"], "matching_paths":len(result)})
            else:
                assert len({(r["archive_file"], r["member_path"]) for r in matches}) == 1
                found = matches[0]
                row.update(result_archive_file=found["archive_file"], result_archive_member=found.get("tar_member_path", found["member_path"]), result_archive_logical_member=found["member_path"], result_member_table=found["member_table"], result_archive_identity="copied_canonical_bytes_match_archived_member_sha256")
                coverage[cid] += 1
        prefix = row["api_dump_root"].rstrip("/") + "/" if row["api_dump_root"] else ""
        dump_members = []
        if prefix:
            pos = bisect_left(positions.get(cid, []), prefix)
            group = by_cohort.get(cid, [])
            while pos < len(group) and group[pos]["original_path"].startswith(prefix):
                dump_members.append(group[pos])
                pos += 1
        if dump_members:
            tables = sorted({r["member_table"] for r in dump_members})
            row.update(dump_member_count=len(dump_members), dump_bytes=sum(int(r["bytes"]) for r in dump_members), dump_archives_json=json.dumps(sorted({r["archive_file"] for r in dump_members})), dump_member_table=";".join(tables), dump_scope="physical_invocation_may_cover_multiple_audit_orders", dump_status="archived")
            key = cid, row["api_dump_root"]
            locations[key] = {"cohort_id":cid, "original_api_dump_root":row["api_dump_root"], "dump_member_count":len(dump_members), "dump_bytes":row["dump_bytes"], "archive_files_json":row["dump_archives_json"], "member_table":row["dump_member_table"]}
        elif truth(row["execution_complete"]):
            bad.append({"slot_id":row["slot_id"], "cohort_id":cid, "missing_dump_root":row["api_dump_root"]})
        final.append(row)
    if bad:
        write_json(work / "join_gaps.json", bad)
        raise ValueError(f"archive joins need attention: {len(bad)}; see work/join_gaps.json")

    assert sum(coverage.values()) == 4682
    write_csv(root / "index/selected_slots.csv", final)
    write_csv(root / "index/DUMP_LOCATIONS.csv", [locations[k] for k in sorted(locations)])
    path_rows = [{k: row[k] for k in ("slot_id", "model", "system", "cohort_id", "result_path", "trajectory_file", "trajectory_sha256", "result_archive_file", "result_archive_member", "result_member_table", "api_dump_root", "dump_archives_json", "dump_member_table")} for row in final]
    write_csv(root / "index/ORIGINAL_TO_PORTABLE.csv", path_rows)
    # Keep case examples directly browsable without changing the frozen report.
    selected_by_path = {r["result_path"]: r for r in final if r["trajectory_file"]}
    case_rows = []
    case_root = root / "report/results/paper-analysis-20260916/cases"
    def cases_walk(value, pointer, case_file):
        if isinstance(value, dict):
            if value.get("path") in selected_by_path:
                selected = selected_by_path[value["path"]]
                if value.get("sha256"):
                    assert value["sha256"] == selected["trajectory_sha256"]
                case_rows.append(dict(case_file=case_file, json_pointer=pointer, slot_id=selected["slot_id"], model=selected["model"], regime=selected["regime"], strategy=selected["strategy"], original_path=value["path"], trajectory_file=selected["trajectory_file"], sha256=selected["trajectory_sha256"]))
            for key, child in value.items():
                cases_walk(child, pointer + "/" + key, case_file)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                cases_walk(child, pointer + "/" + str(i), case_file)
    for name, key in (("case_index.json", "cases"), ("deepseek_delivery_checks.json", "case")):
        cases_walk(json.loads((case_root / name).read_text())[key], "/" + key, name)
    assert len(case_rows) == 9
    write_csv(root / "index/CASE_TRAJECTORIES.csv", case_rows)
    audit_inputs = json.loads((root / "report/results/paper-analysis-20260916/audit/INPUTS.json").read_text())
    gold = next(x for x in audit_inputs["files"] if x["path"].endswith("/contract-nli/test_segments.json"))
    gold_bytes = Path(gold["path"]).read_bytes()
    assert len(gold_bytes) == gold["bytes"] and hashlib.sha256(gold_bytes).hexdigest() == gold["sha256"]
    gold_destination = root / "reference_data/contract-nli/test_segments.json"
    gold_destination.parent.mkdir(parents=True, exist_ok=True)
    if gold_destination.exists():
        assert gold_destination.read_bytes() == gold_bytes
    else:
        gold_destination.write_bytes(gold_bytes)
    write_json(root / "reference_data/INPUTS.json", dict(scope="Exact document/evidence reference read by frozen Audit and case analyses; not a full runtime or all benchmark training data export.", files=[dict(original_path=gold["path"], delivery_path=gold_destination.relative_to(root).as_posix(), bytes=gold["bytes"], sha256=gold["sha256"])]))
    for name in ("selected_slots_checks.json", "source_identity_checks.json", "superseded_slots.csv"):
        shutil.copyfile(work / name, root / "index" / name)
    receipt = json.loads((root / "index/TRAJECTORY_COPY.json").read_text())
    if "input_csv_sha256" in receipt:
        receipt["input_csv_sha256_observed_at_copy_end"] = receipt.pop("input_csv_sha256")
    receipt["final_source_metadata_sha256"] = hashlib.sha256((work / "selected_slots.csv").read_bytes()).hexdigest()
    receipt["metadata_refinement"] = "Final metadata adds separate metric source columns and corrects Kimi recovery dump namespace. Every scientific slot, canonical path and preexisting SHA was checked unchanged; no payload recopy or rescoring. All 4682 copied payload hashes now match archived member identities."
    write_json(root / "index/TRAJECTORY_COPY.json", receipt)
    summary = dict(status="PASS", report_commit=COMMIT, planned_slots=4698, completed_slots=4682, strict_score_complete=sum(truth(r["score_complete"]) for r in final), canonical_files_matched_to_archived_sha256=sum(coverage.values()), archived_results_by_cohort=dict(sorted(coverage.items())), archived_original_members=member_count, selected_distinct_dump_locations=len(locations), selected_distinct_dump_members=sum(r["dump_member_count"] for r in locations.values()), selected_distinct_dump_bytes=sum(r["dump_bytes"] for r in locations.values()), selected_slots_sha256=hashlib.sha256((root / "index/selected_slots.csv").read_bytes()).hexdigest(), incomplete_status_counts=dict(Counter(r["status"] for r in final if not truth(r["execution_complete"]))), new_model_calls=0, caveat="Archive stores preserve superseded and failed history as well as chosen runs. Dump roots shared by Audit orders are deduplicated for unique dump totals; do not sum per-slot dump counts.")
    write_json(root / "index/JOIN_CHECKS.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
