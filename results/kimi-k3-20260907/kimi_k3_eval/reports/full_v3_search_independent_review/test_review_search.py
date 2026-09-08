"""No-API tests for metric/tie boundaries and the future summary interface."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import review_search as review
import compare_summary


class ReviewChecks(unittest.TestCase):
    def test_metric_and_tie_boundaries(self):
        self.assertEqual(review.self_test(), {"passed": True, "cases": 12})

    def test_future_summary_interface_and_tamper_rejection(self):
        # This synthetic summary is built from the independent review solely to
        # exercise comparison wiring. It is NOT a check of an official summary.
        source = Path(__file__).with_name("review.json")
        data = json.loads(source.read_text(encoding="utf-8"))
        summary = {"complete": True, "stage": "full", "manifest_sha256": data["manifest"]["sha256"],
                   "model_id": data["model_id"], "artifacts": [], "agents": [], "aggregate_metrics": [], "task_metrics": []}
        for key, rows in (("artifacts", data["questions"]), ("agents", data["agents"])):
            summary[key] = [dict(row, scenario="restricted_search", status="valid", answer_perf=row["recomputed_answer_perf"],
                                 parent_status="valid", paper_subset=row["system"] == "poolact" and row["question_index"] < 18
                                 and row["cost_regime"] != "cost_free") for row in rows]
        summary["aggregate_metrics"] = [dict(row, scenario="restricted_search", complete=True,
                                             model_id=data["model_id"],
                                             expected_tasks=row["questions"], numeric_tasks=row["questions"],
                                             expected_results=row["questions"], valid_results=row["questions"],
                                             paths=[item["path"] for item in data["questions"] if item["system"] == row["system"]
                                                    and item["dimension"] == row["dimension"] and item["cost_regime"] == row["cost_regime"]
                                                    and item["strategy"] == row["strategy"]])
                                        for row in data["aggregate_metrics"]]
        for row in data["questions"]:
            for subset in ["full"] + (["paper_poolact"] if row["system"] == "poolact" and row["dimension"] == "whois"
                                      and row["cost_regime"] != "cost_free" else []):
                for metric, value in row["metrics"].items():
                    summary["task_metrics"].append(dict(row, subset=subset, metric=metric, value=value, scenario="restricted_search",
                                                         complete=True, paths=[row["path"]], expected_results=1, valid_results=1, numeric_results=1))
        with tempfile.TemporaryDirectory(prefix="search-summary-comparison-") as directory:
            path = Path(directory) / "synthetic.json"
            review.write_json(path, summary)
            result = compare_summary.compare(source, path)
            self.assertEqual(result["matched_counts"], {"artifacts": 420, "agents": 1365,
                                                       "aggregate_metric_cells": 54, "question_metric_cells": 951})
            for number, field in enumerate(("manifest_sha256", "agents", "aggregate_metrics", "task_metrics")):
                changed = copy.deepcopy(summary)
                if field == "manifest_sha256":
                    changed[field] = "wrong"
                elif field == "agents":
                    changed[field][0]["answer_perf"] += .1
                else:
                    changed[field][0]["value"] += .1
                bad = Path(directory) / ("tampered_%d.json" % number)
                review.write_json(bad, changed)
                with self.assertRaises(ValueError):
                    compare_summary.compare(source, bad)
            mutations = [
                ("agents", "agent_id", 99), ("agents", "question_index", 999),
                ("agents", "item_id", "999"), ("agents", "cost_regime", "wrong"),
                ("agents", "strategy", "wrong"), ("agents", "system", "wrong"),
                ("agents", "parent_result_path", "wrong"), ("task_metrics", "expected_results", 999),
                ("task_metrics", "numeric_results", 0), ("aggregate_metrics", "valid_results", 0),
                ("aggregate_metrics", "paths", ["wrong"])]
            for number, (kind, field, value) in enumerate(mutations):
                changed = copy.deepcopy(summary)
                row = next(item for item in changed[kind] if item["system"] == "poolact")
                row[field] = value
                bad = Path(directory) / ("mapping_%d.json" % number)
                review.write_json(bad, changed)
                with self.assertRaises(ValueError):
                    compare_summary.compare(source, bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
