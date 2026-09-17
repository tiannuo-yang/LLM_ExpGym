#!/usr/bin/env python3
"""Verify public numerical tables from the published saved scalar projection.

No private canonical/API dump or historical absolute path is required. This
checks aggregation and ranking, not the authenticity of the original model
responses or a re-execution of task scoring. Keep merge_main.py adjacent.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import merge_main as merger


def rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def same_serialized(actual, expected):
    return actual == ("" if expected is None else str(expected))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = args.report
    scalars = rows(root / "slot_scalars.csv")
    merger.require(len(scalars) == len({r["slot_id"] for r in scalars}) == 4698, "wrong/duplicate slot denominator")
    for row in scalars:
        row["metrics"] = json.loads(row["metrics_json"])
    groups = merger.group_slots(scalars)
    tables = {}
    checks = 0
    for filename in ("absolute_settings.csv", "by_repeat.csv", "main_expgym.csv", "main_poolact.csv"):
        tables[filename] = rows(root / filename)
        for line, record in enumerate(tables[filename], 1):
            calculated = merger.aggregate(record, merger.select_rows(record, groups))
            merger.require(all(merger.same(calculated[k], record[k]) for k in merger.NUMERICAL), f"aggregate mismatch: {filename}:{line}")
            checks += 1
    merger.require(checks == 7767, "unexpected aggregate row denominator")
    ranking = merger.ranks(tables["absolute_settings.csv"])
    supplied_rankings = rows(root / "dimension_rankings.csv")
    merger.require(len(ranking) == len(supplied_rankings) == 126, "wrong ranking denominator")
    for expected, supplied in zip(ranking, supplied_rankings):
        merger.require(all(same_serialized(supplied[k], v) for k, v in expected.items()), "ranking mismatch")
    primary = {tuple(r[k] for k in (*merger.CORE, "metric")): r for r in tables["absolute_settings.csv"] if r["slice_kind"] == "all"}
    merger.require(merger.findings(primary, ranking) == json.loads((root / "FINDINGS.json").read_text()), "findings mismatch")
    # Each wide comparison points to absolute CSV data-record numbers. Check
    # all supplied source fields and independent Decimal difference columns.
    from decimal import Decimal
    comparisons = rows(root / "COMPARISON.csv")
    absolute = tables["absolute_settings.csv"]
    covered = []
    pairs = (("moderate", "free"), ("tight", "free"), ("tight", "moderate"), ("cached", "naive"), ("poolact", "naive"), ("poolact", "cached"))
    for row in comparisons:
        for arm in ("free", "moderate", "tight", "naive", "cached", "poolact"):
            record = row[arm + "_absolute_record"]
            if record:
                original = absolute[int(record) - 1]
                covered.append(int(record))
                for field in ("model", "system", "scenario", "slice_kind", "slice", "metric", "unit", "N"):
                    merger.require(row[field] == original[field], "comparison identity mismatch")
                if original["system"] == "expgym":
                    merger.require(original["strategy"] == "single" and original["regime"] == "cost_" + arm and row["regime"] == "", "comparison budget arm mismatch")
                else:
                    merger.require(original["strategy"] == arm and original["regime"] == row["regime"], "comparison strategy arm mismatch")
                for field in ("full_mean", "expected_units", "known_units", "missing_units", "cohort_id"):
                    merger.require(row[arm + "_" + field] == original[field], "comparison source mismatch")
        for after, before in pairs:
            a, b = row[after + "_full_mean"], row[before + "_full_mean"]
            expected = str(Decimal(a) - Decimal(b)) if a and b else ""
            merger.require(row[after + "_minus_" + before] == expected, "comparison delta mismatch")
    merger.require(len(comparisons) == 1298 and sorted(covered) == list(range(1, len(absolute) + 1)), "comparison coverage mismatch")
    identity = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [root / name for name in (*tables, "slot_scalars.csv", "dimension_rankings.csv", "COMPARISON.csv", "FINDINGS.json")]}
    print(json.dumps({"status": "PASS", "slots": len(scalars), "aggregate_rows": checks, "ranking_rows": len(ranking), "comparison_rows": len(comparisons), "sha256": identity, "boundary": "Public saved scalars to aggregate/ranking/findings only; no raw response authentication or task rescoring."}, indent=2))


if __name__ == "__main__":
    main()
