"""No-network boundary tests for pilot accounting and incomplete coverage."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import estimate_runtime as estimate


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class PilotAccountingTests(unittest.TestCase):
    def test_all_job_states_count_and_in_progress_latency_is_excluded(self):
        with tempfile.TemporaryDirectory(prefix="kimi-eta-usage-") as directory:
            root = Path(directory)
            jobs = []
            cases = [("completed", "success", None, 10.0, 100, 10),
                     ("running", "in_progress", None, 0.001, 0, 0),
                     ("failed", "error", {"message": "failed"}, 4.0, 20, 2),
                     ("pending", "success", None, 6.0, 30, 3)]
            for index, (job_state, state, error, elapsed, prompt, completion) in enumerate(cases):
                dump = root / job_state
                jobs.append({"dump_dir": str(dump)})
                write_json(dump / "attempt.json", {
                    "schema_version": "expgym.api_attempt.v1", "request_id": str(index),
                    "state": state, "error": error, "wall_time_seconds": elapsed,
                    "response_json": {"usage": {"prompt_tokens": prompt, "completion_tokens": completion},
                                      "choices": [{"finish_reason": "length" if index == 3 else "stop"}]},
                })
            write_json(root / "completed" / "unrelated.json", {"schema_version": "other"})
            usage, latencies = estimate.collect_api_usage(jobs)
            self.assertEqual(usage, {"attempts": 4, "successful_attempts": 2, "failed_attempts": 1,
                                     "in_progress_attempts": 1, "prompt_tokens": 150,
                                     "completion_tokens": 15, "truncated_completions": 1})
            self.assertEqual(sorted(latencies), [4.0, 6.0, 10.0])
            self.assertEqual(estimate.collect_api_usage([])[1], [])

    def test_incomplete_strata_keep_eta_unset_but_count_unfinished_usage(self):
        with tempfile.TemporaryDirectory(prefix="kimi-eta-incomplete-") as directory:
            root = Path(directory)
            jobs = [{"id": "done", "system": "expgym", "scenario": "restricted_search",
                     "question_index": 0, "cost_regime": "cost_free", "status_path": str(root / "done.json"),
                     "dump_dir": str(root / "done-dumps")},
                    {"id": "pending", "system": "expgym", "scenario": "evidence_audit",
                     "question_index": 0, "cost_regime": "cost_free", "status_path": str(root / "absent.json"),
                     "dump_dir": str(root / "pending-dumps")}]
            write_json(root / "done.json", {"attempts": [{"status": "completed", "wall_time_seconds": 10.0,
                       "started_at": "2026-09-07T09:00:00+00:00", "finished_at": "2026-09-07T09:00:10+00:00"}]})
            for index, job in enumerate(jobs):
                write_json(Path(job["dump_dir"]) / "attempt.json", {
                    "schema_version": "expgym.api_attempt.v1", "state": "success", "wall_time_seconds": 1,
                    "response_json": {"usage": {"prompt_tokens": 10 + index, "completion_tokens": 2}},
                })
            manifest = {"settings": {}, "source_tree_sha256": "test-source", "workers": 2, "jobs": jobs}
            pilot, full, output = root / "pilot.json", root / "full.json", root / "estimate"
            write_json(pilot, manifest)
            write_json(full, manifest)
            arguments = ["estimate_runtime.py", "--pilot-manifest", str(pilot), "--full-manifest", str(full),
                         "--output-dir", str(output), "--assume-pilot-reused"]
            with patch.object(sys, "argv", arguments), contextlib.redirect_stdout(io.StringIO()):
                estimate.main()
            result = json.loads((output / "runtime_estimate.json").read_text())
            self.assertEqual(result["pilot_completed_jobs"], 1)
            self.assertEqual(result["usage"]["attempts"], 2)
            self.assertEqual(result["usage"]["prompt_tokens"], 21)
            self.assertEqual(result["missing_strata"], ["expgym/audit/cost_free"])
            self.assertIsNone(result["remaining_wall_time_seconds_point"])
            self.assertIsNone(result["remaining_wall_time_hours_range"])


if __name__ == "__main__":
    unittest.main()
