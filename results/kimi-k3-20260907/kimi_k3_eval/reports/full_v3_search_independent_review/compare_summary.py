#!/usr/bin/env python3
"""Strict provenance/coverage comparison layered over immutable Search review."""
import argparse
from pathlib import Path

import review_search as base


def compare(review_path, summary_path):
    result = base.comparison(review_path, summary_path)
    reviewed, _ = base.read(review_path)
    summary, _ = base.read(summary_path)
    require = base.require
    fields = ("system", "question_index", "item_id", "cost_regime", "strategy", "job_id")
    for kind, rows in (("artifacts", reviewed["questions"]), ("agents", reviewed["agents"])):
        expected = {row["path"]: row for row in rows}
        for row in summary[kind]:
            if row["scenario"] != "restricted_search":
                continue
            other = expected[row["path"]]
            for field in fields:
                require(row.get(field) == other.get(field), "summary %s %s mapping differs" % (kind, field))
            paper_subset = other["system"] == "poolact" and other["question_index"] < 18 and other["cost_regime"] != "cost_free"
            require(row.get("paper_subset") is paper_subset, "summary paper-subset membership differs")
            if kind == "agents":
                for field in ("agent_id", "parent_result_path"):
                    require(row.get(field) == other.get(field), "summary agent %s mapping differs" % field)
                if other["system"] == "poolact":
                    require(row.get("parent_status") == "valid", "summary agent parent status differs")
            else:
                require(row.get("dimension") == other["dimension"], "summary artifact dimension differs")
    def identity(row):
        return (row["subset"], row["system"], row["dimension"], row["cost_regime"], row["strategy"])
    grouped_paths = {}
    for row in reviewed["questions"]:
        subsets = ["full"] + (["paper_poolact"] if row["system"] == "poolact" and row["dimension"] == "whois"
                              and row["cost_regime"] != "cost_free" else [])
        for subset in subsets:
            key = (subset, row["system"], row["dimension"], row["cost_regime"], row["strategy"])
            grouped_paths.setdefault(key, set()).add(row["path"])
    for row in summary["aggregate_metrics"]:
        if row["scenario"] == "restricted_search":
            paths = grouped_paths[identity(row)]
            require(row.get("model_id") == reviewed["model_id"], "summary aggregate model identity differs")
            require(row.get("expected_results") == row.get("valid_results") == len(paths), "summary aggregate result counts differ")
            require(isinstance(row.get("paths"), list) and len(row["paths"]) == len(paths) and set(row["paths"]) == paths,
                    "summary aggregate source paths differ")
    for row in summary["task_metrics"]:
        if row["scenario"] == "restricted_search":
            require(row.get("expected_results") == row.get("valid_results") == row.get("numeric_results") == 1,
                    "summary question result counts differ")
    result["comparison_script"] = base.reference(__file__)
    result["metric_comparison_script"] = base.reference(base.__file__)
    result["strict_identity_and_coverage_checked"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.review, args.summary)
    base.write_json(args.output, result)
    import json
    print(json.dumps(result))


if __name__ == "__main__":
    main()
