#!/usr/bin/env python3
"""Synthetic comparator fixtures, never official results; no model/evaluator calls."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class ComparisonChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        snapshot = HERE / "independent_post_resume_final.json"
        if not snapshot.exists():
            snapshot = HERE / "independent.json"
        raw = json.loads(snapshot.read_text())
        cls.summary = {"complete": True, "manifest_sha256": raw["manifest"]["sha256"],
                       "aggregate_metrics": [], "task_metrics": [], "agents": []}
        for row in raw["family_metrics"]:
            cls.summary["aggregate_metrics"].append({"complete": True, "subset": "full", "system": row["system"],
                "dimension": row["family"], "cost_regime": row["regime"], "strategy": row["strategy"],
                "metric": row["metric"], "value": row["value"]})
        for row in raw["task_metrics"]:
            cls.summary["task_metrics"].append({"complete": True, "subset": "full", "system": row["system"],
                "item_id": row["task"], "cost_regime": row["regime"], "strategy": row["strategy"],
                "metric": row["metric"], "value": row["value"]})
            if row["system"] == "poolact" and row["task"] == "hpobench:nasbench101:A" and row["regime"] != "cost_free":
                cls.summary["aggregate_metrics"].append({"complete": True, "subset": "paper_poolact", "system": "poolact",
                    "dimension": "nasbench101", "cost_regime": row["regime"], "strategy": row["strategy"],
                    "metric": row["metric"], "value": row["value"]})
        for row in raw["traces"]:
            cls.summary["agents"].append({"path": row["path"], "sha256": row["sha256"], "status": "valid",
                "answer_perf": row["raw_performance"], "Gap_pct": row["gap_pct"]})

    def run_comparison(self, change=None):
        fixture = copy.deepcopy(self.summary)
        if change:
            change(fixture)
        with tempfile.TemporaryDirectory(prefix="hpo-comparison-synthetic-") as directory:
            path = Path(directory) / "synthetic_summary.json"
            path.write_text(json.dumps(fixture))
            return subprocess.run([sys.executable, str(HERE / "compute.py"), "--summary", str(path)],
                                  capture_output=True, text=True, check=False)

    def test_matching_synthetic_cells(self):
        result = self.run_comparison()
        self.assertEqual(result.returncode, 0, result.stderr)
        comparison = json.loads(result.stdout)["summary_comparison"]
        self.assertEqual([comparison[key] for key in ("family_cells_checked", "task_cells_checked",
                          "agent_records_checked", "paper_nas101a_cells_checked")], [63, 189, 405, 12])

    def test_reject_incomplete(self):
        self.assertNotEqual(self.run_comparison(lambda s: s.update(complete=False)).returncode, 0)

    def test_reject_manifest_mismatch(self):
        self.assertNotEqual(self.run_comparison(lambda s: s.update(manifest_sha256="0" * 64)).returncode, 0)

    def test_reject_family_difference(self):
        self.assertNotEqual(self.run_comparison(lambda s: s["aggregate_metrics"][0].update(value=-1)).returncode, 0)

    def test_reject_task_difference(self):
        self.assertNotEqual(self.run_comparison(lambda s: s["task_metrics"][0].update(value=-1)).returncode, 0)

    def test_reject_agent_raw_difference(self):
        self.assertNotEqual(self.run_comparison(lambda s: s["agents"][0].update(answer_perf=-1)).returncode, 0)

    def test_reject_agent_gap_difference(self):
        self.assertNotEqual(self.run_comparison(lambda s: s["agents"][0].update(Gap_pct=-1)).returncode, 0)

    def test_reject_agent_sha_difference(self):
        self.assertNotEqual(self.run_comparison(lambda s: s["agents"][0].update(sha256="0" * 64)).returncode, 0)

    def test_reject_paper_subset_difference(self):
        self.assertNotEqual(self.run_comparison(lambda s: s["aggregate_metrics"][-1].update(value=-1)).returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
