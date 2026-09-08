#!/usr/bin/env python3
"""Meaningful offline checks: real fake-runner artifacts plus integrity tampering.

All mutation fixtures live in a fresh temporary directory. No real API is used.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

import audit_results as audit
import run_study as harness
import summarize_results as report


class ReportingChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        retained = os.getenv("KIMI_AUDIT_FIXTURE_DIR")
        cls.temporary = None if retained else tempfile.TemporaryDirectory(prefix="kimi_audit_fake_")
        cls.root = Path(retained) if retained else Path(cls.temporary.name)
        if retained:
            cls.root.mkdir(parents=True, exist_ok=False)
        args = harness.parse_args(["--stage", "smoke", "--base-url", "http://127.0.0.1:9/v1",
                                   "--output-dir", str(cls.root / "runs"),
                                   "--logs-dir", str(cls.root / "logs"),
                                   "--dumps-dir", str(cls.root / "dumps"), "--workers", "3"])
        manifest = harness.build_manifest(args)
        manifest["jobs"] = [job for job in manifest["jobs"] if job["cost_regime"] == "cost_tight"]
        for system in ("expgym", "poolact"):
            manifest["jobs"].append(harness.make_job(args, manifest["settings"], system, "tuning",
                                                    "hpobench:paramnet:adult:steps", "cost_tight"))
        manifest["settings"]["backend"] = "fake"
        manifest["study_type"] = "Static/fake validation"
        for job in manifest["jobs"]:
            command = job["command"]
            command[command.index("--backend") + 1] = "fake"
        manifest["counts"] = harness.count_jobs(manifest["jobs"])
        cls.manifest = manifest
        cls.manifest_path = cls.root / "manifest.json"
        audit.write_json(cls.manifest_path, manifest)
        status = harness.execute_study(args, manifest)
        if status:
            raise RuntimeError("fake runner fixture failed: " + str(cls.root))
        cls.clean = audit.run_audit(cls.manifest_path, Path(__file__).resolve().parents[1] / "data_runtime/.venv-hpo/bin/python")

    @classmethod
    def tearDownClass(cls):
        if cls.temporary:
            cls.temporary.cleanup()

    def test_complete_real_fake_runner_artifacts(self):
        self.assertTrue(self.clean["complete"], [(row["path"], row["issues"]) for row in self.clean["records"] if row["status"] != "valid"])
        self.assertEqual(self.clean["valid_counts"]["expgym_traces"], 4)
        self.assertEqual(self.clean["valid_counts"]["poolact_results"], 12)
        self.assertEqual(self.clean["valid_counts"]["poolact_agent_traces"], 24)

    def test_sequential_model_zero_score_stays_valid(self):
        rows = [row for row in self.clean["records"] if row["system"] == "expgym" and row["scenario"] == "restricted_search"]
        self.assertTrue(rows and rows[0]["status"] == "valid")
        self.assertEqual(rows[0]["answer_perf"], 0.0)

    def test_summary_not_a_trace(self):
        target = next(row for row in self.clean["records"] if row["system"] == "poolact")
        summary = audit.strict_json(target["summary_path"])
        schema = audit.strict_json(Path(self.manifest["repo_root"]) / "schemas/trace-v2.schema.json")
        with self.assertRaises(ValueError):
            audit.validate_json_schema(summary, schema)

    def mutate_and_audit(self, job, path, mutate):
        """Mutate only our generated temporary fake fixture, then restore it."""
        original = path.read_bytes()
        data = json.loads(original)
        mutate(data)
        try:
            with path.open("w") as handle:
                json.dump(data, handle, allow_nan=False)
            return audit.audit_job(job, self.manifest)
        finally:
            with path.open("wb") as handle:
                handle.write(original)

    def test_independent_sequential_score_recompute(self):
        job = next(job for job in self.manifest["jobs"] if job["system"] == "expgym" and job["scenario"] == "restricted_search")
        path = Path(job["expected_outputs"][0]["path"])
        def change(data):
            data["outcome"]["score"]["value"] = 0.812345
        rows = self.mutate_and_audit(job, path, change)
        self.assertEqual(rows[0]["status"], "invalid")
        self.assertIn("recomputation", str(rows[0]["issues"]))

    def test_per_agent_file_mismatch(self):
        job = next(job for job in self.manifest["jobs"] if job["system"] == "poolact")
        path = Path(job["expected_outputs"][0]["agent_paths"][0])
        rows = self.mutate_and_audit(job, path, lambda data: data.update(seed=-1))
        self.assertEqual(rows[0]["status"], "invalid")
        self.assertIn("differs from embedded", str(rows[0]["issues"]))

    def test_pending_claims_rejected_even_with_valid_scores(self):
        job = next(job for job in self.manifest["jobs"] if job["system"] == "poolact")
        output = next(out for out in job["expected_outputs"] if out["strategy"] == "poolact")
        def change(data):
            data["shared_state"]["graph"]["pending_claims"] = 1
        rows = self.mutate_and_audit(job, Path(output["path"]), change)
        row = next(row for row in rows if row["strategy"] == "poolact")
        self.assertEqual(row["status"], "invalid")
        self.assertIn("pending_claims", str(row["issues"]))

    def test_missing_agent_stays_missing(self):
        job = next(job for job in self.manifest["jobs"] if job["system"] == "poolact")
        path = Path(job["expected_outputs"][0]["agent_paths"][1])
        moved = path.with_suffix(".held")
        path.rename(moved)
        try:
            rows = audit.audit_job(job, self.manifest)
        finally:
            moved.rename(path)
        self.assertEqual(rows[0]["status"], "missing")

    def test_gap_clip_before_mean_and_no_upper_clip(self):
        oracle = {"task": {"mean_perf": 0.5, "best_perf": 1.0}}
        self.assertEqual(report.gap(0.0, "task", oracle), 0.0)
        self.assertEqual(report.gap(1.25, "task", oracle), 150.0)
        record = {"system": "poolact", "scenario": "tuning", "status": "valid", "tuning_task": "task",
                  "answer_perf": 1.0, "agent_records": [{"answer_perf": 0.0}, {"answer_perf": 1.0}]}
        self.assertEqual(report.metric_values(record, oracle)["MI_Gap_pct"], 50.0)

    def test_audit_nonzero_verification_from_v2_arguments(self):
        from expgym import task_evidence_audit as task
        job = next(job for job in self.manifest["jobs"] if job["system"] == "expgym" and job["scenario"] == "evidence_audit")
        trace = audit.strict_json(job["expected_outputs"][0]["path"])
        gold = task._get_doc(0).annotations
        labels = task._get_labels("cc-large")
        answer = {key: {"label": value["choice"], "evidence_ids": value.get("spans", [])}
                  for key, value in gold.items() if key in labels}
        hypothesis = next(iter(answer))
        trace["tool_calls"] = [
            {"name": "human_feedback", "arguments": {"nda_id": hypothesis, "evidence_ids": answer[hypothesis]["evidence_ids"]}},
            {"name": "human_feedback", "arguments": {"raw": "not valid JSON", "encoding": "text"}}]
        trace["outcome"]["answer_override"] = json.dumps(answer)
        result = audit.trace_to_result(trace)
        evaluator = task.build_answer_evaluator(row_index=0, cc_split="cc-large")
        metrics = evaluator(result["answer"], result["tool_records"])
        self.assertEqual(metrics["label_acc"], 1.0)
        self.assertEqual(metrics["evidence_acc"], 1.0)
        self.assertAlmostEqual(metrics["verification_eff"], 1 / len(answer))
        self.assertEqual(result["tool_records"][1][1], "not valid JSON")

    def test_report_indexes_all_expected_agents_and_metrics(self):
        summary = report.summarize(self.clean, Path(self.manifest["repo_root"]) / "data/hpo_tuning/oracle3.json")
        self.assertEqual(len(summary["agents"]), 28)
        self.assertTrue(summary["complete"])
        self.assertTrue(any(row["metric"] == "EA_pct" and row["value"] is not None for row in summary["aggregate_metrics"]))
        partial = copy.deepcopy(self.clean)
        partial["records"][0]["status"] = "missing"
        partial["complete"] = False
        draft = report.summarize(partial, Path(self.manifest["repo_root"]) / "data/hpo_tuning/oracle3.json")
        affected = [row for row in draft["aggregate_metrics"] if row["system"] == partial["records"][0]["system"]
                    and row["dimension"] == report.dimension(partial["records"][0])]
        self.assertTrue(affected and all(row["value"] is None for row in affected))

    def test_promoted_pilot_cost_not_replaced_by_resume_cost(self):
        pilot = {"started_at": "2026-09-07T01:00:00+00:00", "finished_at": "2026-09-07T02:00:00+00:00",
                 "wall_time_seconds": 3600, "pid": 10}
        full = {"started_at": "2026-09-07T03:00:00+00:00", "finished_at": "2026-09-07T03:00:05+00:00",
                "wall_time_seconds": 5, "pid": 11}
        data = {"receipts": [{"job_id": "same_job", "receipt": full}],
                "promotion": {"plan": {"jobs": [{"job_id": "same_job", "source_execution": pilot}]}}}
        resources = report.resource_summary(data, [])
        self.assertEqual(resources["sum_subprocess_attempt_wall_seconds"], 3605)
        self.assertEqual(resources["sum_promoted_pilot_subprocess_attempt_wall_seconds"], 3600)
        self.assertEqual(resources["sum_stage_subprocess_attempt_wall_seconds"], 5)
        self.assertEqual(resources["study_execution_span_seconds"], 7205)

    def test_missing_attempt_time_not_silently_omitted(self):
        data = {"receipts": [{"job_id": "x", "receipt": {"attempts": [
            {"started_at": "2026-09-07T01:00:00+00:00", "finished_at": None, "wall_time_seconds": None, "pid": 10},
            {"started_at": "2026-09-07T02:00:00+00:00", "finished_at": "2026-09-07T02:00:10+00:00", "wall_time_seconds": 10, "pid": 11}]}}]}
        resources = report.resource_summary(data, [])
        self.assertIsNone(resources["sum_subprocess_attempt_wall_seconds"])
        self.assertEqual(resources["known_subprocess_attempt_wall_seconds"], 10)
        self.assertEqual(resources["missing_subprocess_attempt_wall_count"], 1)
        self.assertIsNone(resources["study_execution_span_seconds"])

    def test_actual_model_must_match_manifest_label(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["settings"]["model"] = "a-different-model"
        for system in ("expgym", "poolact"):
            job = next(job for job in manifest["jobs"] if job["system"] == system and job["scenario"] == "restricted_search")
            rows = audit.audit_job(job, manifest)
            self.assertTrue(all(row["status"] == "invalid" for row in rows))
            self.assertTrue(all("model" in str(row["issues"]) for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
