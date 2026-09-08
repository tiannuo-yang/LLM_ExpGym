#!/usr/bin/env python3
"""Presentation-boundary checks; all input is synthetic or already recorded."""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

import build_delivery as delivery
from audit_results import write_csv


class DeliveryChecks(unittest.TestCase):
    def synthetic_summary(self):
        rows = []
        for regime in delivery.REGIMES:
            for number, (_, dimension, metric) in enumerate(delivery.EXP_COLUMNS):
                rows.append({"subset": "full", "system": "expgym", "cost_regime": regime, "strategy": None,
                             "dimension": dimension, "metric": metric, "value": number + 0.25, "complete": True})
        for regime in delivery.REGIMES[1:]:
            for strategy in delivery.STRATEGIES:
                for number, (_, dimension, metric) in enumerate(delivery.POOL_COLUMNS):
                    rows.append({"subset": "paper_poolact", "system": "poolact", "cost_regime": regime, "strategy": strategy,
                                 "dimension": dimension, "metric": metric, "value": number + 0.75, "complete": True})
        return {"stage": "full", "aggregate_metrics": rows,
                "task_metrics": [{"subset": "paper_poolact", "scenario": "tuning", "item_id": "hpobench:nasbench101:A"}]}

    def test_full_wide_shape_and_missing_primary_metric_rejected(self):
        summary = self.synthetic_summary()
        tables = delivery.wide_tables(summary)
        self.assertEqual((len(tables["expgym"]), len(tables["expgym"][0])), (3, 8))
        self.assertEqual((len(tables["poolact_paper"]), len(tables["poolact_paper"][0])), (6, 8))
        self.assertEqual(tables["expgym"][0]["ParamNet Gap"], 0.25)
        self.assertEqual(tables["poolact_paper"][0]["NAS101A MI"], 5.75)
        summary["aggregate_metrics"].pop()
        with self.assertRaisesRegex(ValueError, "missing primary"):
            delivery.wide_tables(summary)

    def test_smoke_missing_cell_remains_null(self):
        summary = self.synthetic_summary()
        summary["stage"] = "smoke"
        summary["aggregate_metrics"].pop(0)
        self.assertIsNone(delivery.wide_tables(summary)["expgym"][0]["ParamNet Gap"])

    def test_duplicate_metric_rejected(self):
        summary = self.synthetic_summary()
        summary["aggregate_metrics"].append(copy.deepcopy(summary["aggregate_metrics"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            delivery.wide_tables(summary)

    def test_csv_semantic_json_key_order_but_score_tamper_rejected(self):
        rows = [{"score": 1.5, "metadata": {"b": 2, "a": 1}}]
        with tempfile.TemporaryDirectory(prefix="delivery_csv_") as directory:
            path = Path(directory) / "data.csv"
            write_csv(path, rows)
            reordered = [{"metadata": {"a": 1, "b": 2}, "score": 1.5}]
            delivery.verify_csv(path, reordered)
            with self.assertRaisesRegex(ValueError, "differs from summary"):
                delivery.verify_csv(path, [{"score": 2.5, "metadata": {"b": 2, "a": 1}}])

    def test_unreported_tokens_and_unknown_slurm_are_null(self):
        group = {"http_attempts": 10, "reasoning_tokens": 0, "reasoning_tokens_reported_attempts": 0}
        self.assertIsNone(delivery.usage_view(group)["reasoning_tokens_total"])
        self.assertIsNone(delivery.service_view(None, None)["allocated_gpu_hours"])
        service = {"data": {"gpu_count": 64}, "reference": {}}
        slurm = {"data": {"elapsed_seconds": 3600}, "reference": {}}
        self.assertIsNone(delivery.service_view(service, slurm)["allocated_gpu_hours"])
        self.assertEqual(delivery.service_view(service, slurm)["known_allocated_gpu_hours"], 64)
        slurm["data"]["final"] = True
        self.assertEqual(delivery.service_view(service, slurm)["allocated_gpu_hours"], 64)
        self.assertIsNone(delivery.service_view(service, {"data": {"jobs": []}, "reference": {}})["allocated_gpu_hours"])

    def test_slurm_allocations_snapshot_and_final_are_distinct(self):
        service = {"data": {"job_id": "2", "gpu_count": 64}, "reference": {}}
        slurm = {"reference": {}, "data": {"final": False, "known_allocated_gpu_hours": 96,
                 "allocations": [{"JobIDRaw": "1", "State": "CANCELLED", "gpu_count": 64,
                                  "elapsed_seconds": 1800, "final": True},
                                 {"JobIDRaw": "2", "State": "RUNNING", "gpu_count": 64,
                                  "elapsed_seconds": 3600, "final": False}]}}
        view = delivery.service_view(service, slurm)
        self.assertEqual(view["slurm_observed_state"], "RUNNING")
        self.assertIsNone(view["slurm_final_state"])
        self.assertEqual(view["known_allocated_gpu_hours"], 64)
        self.assertEqual(view["owned_allocations_known_allocated_gpu_hours"], 96)
        self.assertIsNone(view["owned_allocations_final_allocated_gpu_hours"])
        slurm["data"]["final"] = True
        slurm["data"]["allocations"][1].update(final=True, State="COMPLETED")
        view = delivery.service_view(service, slurm)
        self.assertEqual(view["allocated_gpu_hours"], 64)
        self.assertEqual(view["owned_allocations_final_allocated_gpu_hours"], 96)
        service["data"]["gpu_count"] = 32
        with self.assertRaisesRegex(ValueError, "GPU count differs"):
            delivery.service_view(service, slurm)
        service["data"]["job_id"] = "3"
        with self.assertRaisesRegex(ValueError, "does not contain"):
            delivery.service_view(service, slurm)

    def test_dump_trace_versions_bind_current_scores_to_usage(self):
        audit = {"complete": True, "backend": "openai", "records": [
            {"system": "expgym", "path": "/tmp/exp.json", "sha256": "exp"},
            {"system": "poolact", "agent_records": [{"path": "/tmp/agent.json", "sha256": "agent"}]}]}
        dump = {"complete": True, "records": [
            {"status": "valid", "trace_path": "/tmp/exp.json", "trace_sha256": "exp"},
            {"status": "valid", "trace_path": "/tmp/agent.json", "trace_sha256": "agent"}]}
        delivery.verify_dump_trace_links(audit, dump)
        dump["records"][1]["trace_sha256"] = "old-agent"
        with self.assertRaisesRegex(ValueError, "differ from current result"):
            delivery.verify_dump_trace_links(audit, dump)
        dump["records"].append(copy.deepcopy(dump["records"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate dump"):
            delivery.verify_dump_trace_links(audit, dump)

    def protocol_fixture(self):
        manifest = {"stage": "smoke", "settings": {"max_tokens": 8192}, "source_tree_sha256": "source",
                    "counts": {"total_agent_traces": 1}}
        row = {"path": "/tmp/trace.json", "client_id": "client", "runner": "poolact", "reason": "missing_action",
               "reason_source": "inferred_from_saved_forced_prompt; field_not_serialized",
               "raw_success_request_ids": ["request"], "forced_final_calls": 1, "raw_native_responses": 1,
               "raw_native_calls": 1, "trace_native_messages": 1, "native_before_missing_action": True,
               "normal_responses_over_8000_chars": 1, "cap_removed_action_parser_candidates": 1,
               "cap_removed_known_tool_json_candidates": 1}
        fields = ("forced_final_calls", "raw_native_responses", "raw_native_calls", "trace_native_messages",
                  "native_before_missing_action", "normal_responses_over_8000_chars",
                  "cap_removed_action_parser_candidates", "cap_removed_known_tool_json_candidates")
        group = {field: int(row[field]) for field in fields}
        group.update(traces=1, termination_reasons={"missing_action": 1})
        empty = {field: 0 for field in fields}
        empty.update(traces=0, termination_reasons={})
        data = dict(manifest, expected_counts=manifest["counts"], schema_version=2, trace_rows=[row],
                    groups={"all": group, "poolact": group, "expgym": empty})
        attachment = {"reference": {"path": "/tmp/diagnostic.json"}, "data": data}
        dump = {"records": [{"status": "valid", "client_id": "client", "system": "poolact", "trace_path": "/tmp/trace.json",
                             "calls": [{"successful_request_id": "request"}]}]}
        return manifest, attachment, dump

    def test_schema2_diagnostics_are_session_bound_and_separate_from_raw_fields(self):
        manifest, attachment, dump = self.protocol_fixture()
        view = delivery.protocol_view(attachment, manifest, dump)
        self.assertEqual(view["groups"]["all"]["missing_action"], 1)
        self.assertIn("inferred_from_saved_forced_prompt; field_not_serialized",
                      view["groups"]["poolact"]["termination_reason_sources"])
        for key in ("stage", "source_tree_sha256", "settings", "expected_counts"):
            changed = copy.deepcopy(attachment)
            changed["data"][key] = "different"
            with self.assertRaisesRegex(ValueError, "differs from manifest"):
                delivery.protocol_view(changed, manifest, dump)
        for key, value in (("client_id", "another-client"), ("raw_success_request_ids", ["another-request"])):
            changed = copy.deepcopy(attachment)
            changed["data"]["trace_rows"][0][key] = value
            with self.assertRaisesRegex(ValueError, "differ from audited traces"):
                delivery.protocol_view(changed, manifest, dump)
        changed = copy.deepcopy(attachment)
        changed["data"]["groups"]["all"]["cap_removed_known_tool_json_candidates"] = 2
        with self.assertRaisesRegex(ValueError, "group count differs"):
            delivery.protocol_view(changed, manifest, dump)

    def test_absent_or_legacy_protocol_inferences_remain_null(self):
        manifest, attachment, dump = self.protocol_fixture()
        self.assertIsNone(delivery.protocol_view(None, manifest, dump))
        attachment["data"]["schema_version"] = 1
        self.assertIsNone(delivery.protocol_view(attachment, manifest, dump))

    def test_nas101_disclosure_requires_explicit_matching_source_and_file_hashes(self):
        self.assertIsNone(delivery.nas101_hints_view({}, {"source_tree_sha256": "source"}))
        with tempfile.TemporaryDirectory(prefix="delivery_nas101_") as directory:
            root = Path(directory)
            files = []
            for role in ("prompt", "encoding", "candidate_patch"):
                path = root / (role + ".json")
                delivery.write_json(path, {"fixture": role})
                files.append(dict(delivery.reference(path), role=role))
            evidence = root / "evidence.json"
            data = {"schema_version": 1, "source_tree_sha256": "source", "retained_original_paper_hints": True,
                    "candidate_patch_applied": False, "files": files}
            delivery.write_json(evidence, data)
            refs = {"nas101_hints_status": delivery.reference(evidence)}
            view = delivery.nas101_hints_view(refs, {"source_tree_sha256": "source"})
            self.assertFalse(view["candidate_patch_applied"])
            with self.assertRaisesRegex(ValueError, "different source"):
                delivery.nas101_hints_view(refs, {"source_tree_sha256": "future-source"})
            (root / "prompt.json").write_text('{"fixture": "changed"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed after validation"):
                delivery.nas101_hints_view(refs, {"source_tree_sha256": "source"})

    def test_overview_labels_inferences_candidates_and_unreported_raw_fields(self):
        manifest, attachment, dump = self.protocol_fixture()
        example = {"official_full_matrix_complete": False, "stage": "smoke", "backend": "fake", "model_id": "fixture",
                   "study_type": "fixture", "observed_reasoning": None, "coverage": [], "tables": delivery.wide_tables(self.synthetic_summary()),
                   "usage": {"selected_totals": None, "selected_success_totals": None, "historical_totals": None},
                   "execution_resources": {}, "service": delivery.service_view(None, None), "runtime_estimate": None,
                   "request_policy": {key: None for key in ("chat_template_kwargs", "max_tokens", "max_steps", "max_evals", "poolact_agents", "poolact_protocol")},
                   "diagnostics": delivery.diagnostics_from_summary({"agents": [{"system": "poolact", "aborted": True}]}),
                   "protocol_inferences": delivery.protocol_view(attachment, manifest, dump), "protocol_diagnostics": attachment,
                   "nas101_hints_status": {"reference": {"path": "/tmp/hints.json"}}, "references": {}}
        text = delivery.overview(example, Path("/tmp/delivery"))
        self.assertIn("独立诊断观察与推断（不补写原字段）", text)
        self.assertIn("已知工具名 + 合法 JSON 候选", text)
        self.assertIn("不证明参数 schema 合法、工具可执行", text)
        self.assertIn("未记录显示 null", text)
        self.assertIn("候选修正 patch 未应用", text)
        self.assertNotIn("| {} |", text)
        example["protocol_inferences"] = None
        example["nas101_hints_status"] = None
        text = delivery.overview(example, Path("/tmp/delivery"))
        self.assertIn("schema2 分组诊断推断：未附适用证据（null）", text)
        self.assertIn("NAS101 B/C 提示/编码差异状态：未附", text)
        self.assertNotIn("不是整个开发/恢复过程的总消耗", text)
        example["references"]["project_usage_inventory"] = {"path": "/tmp/project_usage.json"}
        text = delivery.overview(example, Path("/tmp/delivery"))
        self.assertIn("不是整个开发/恢复过程的总消耗", text)
        self.assertIn("[项目 API 消耗清单](<../project_usage.json>)", text)
        self.assertIn("服务验收探针和后台 health 请求不属于评测 dump 清单", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
