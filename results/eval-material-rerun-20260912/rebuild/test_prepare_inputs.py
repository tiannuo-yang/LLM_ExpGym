"""Small metadata/relocation fixtures only; no real study outputs are read."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import aggregate_material as a
import prepare_inputs as p
import test_aggregate_material as fixtures


class PreparationInterfaceTests(unittest.TestCase):
    def test_missing_glm_blocks_without_opening_any_inputs(self):
        config = dict(schema="expgym.material-input-preparation.v1", selfhosted={
            "deepseek": {"terminal_export": {}, "resource_export": {}},
            "kimi": {"terminal_export": {}, "resource_export": {}},
            "glm": {"terminal_export": None, "resource_export": None}})
        with patch.object(Path, "read_bytes", side_effect=AssertionError("must not read")):
            with self.assertRaisesRegex(ValueError, "not all terminal exports"):
                p.prepare(config)

    def test_artifact_mapping_uses_manifest_identity_without_payload_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            prep = p.Preparation(dict(study_root=tmp))
            source = Path(tmp)/"deepseek/queue/runs/invocations/test/result/poolact/result.json"
            entry = dict(path=str(source), bytes=100, sha256="b"*64)
            with patch.object(Path, "read_bytes", side_effect=AssertionError("payload must not be read")):
                result = prep.artifact(entry)
            self.assertEqual(result["path"], "@study/deepseek/queue/runs/invocations/test/result/poolact/result.json")
            self.assertIn("queue/runs/invocations/test/result/poolact/result.json", prep.selections["deepseek"])
            self.assertEqual(result["sha256"], entry["sha256"])

    def test_stage_outputs_without_paths_resolve_next_to_export(self):
        entry = dict(path="/fixture/kimi/queue/terminal_export/EXPORT.json")
        stage = dict(output_identities={"execution_index.json": dict(bytes=4, sha256="a"*64)})
        expected = p.exported_file(entry, stage, "execution_index.json")
        self.assertEqual(expected["path"], "/fixture/kimi/queue/terminal_export/execution_index.json")
        self.assertEqual(expected["bytes"], 4)

    def test_preparation_rejects_raw_payload_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            prep = p.Preparation(dict(study_root=tmp))
            path = Path(tmp)/"gpt/api_dump/call.json"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "must not open"):
                prep.read(p.descriptor(path, b"{}"), "bad")

    def test_rebuild_is_identical_under_two_restoration_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root/"input"
            input_root.mkdir()
            spec_path = fixtures.EndToEndTests().fixture(input_root)
            index = json.loads((input_root/"executions.json").read_bytes())
            for row in index["jobs"]:
                for key in ("result", "summary", "verification_receipt"):
                    old = row[key]["path"]
                    for replica in ("restored_a", "restored_b"):
                        target = root/replica/"kimi"/old
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(input_root/old, target)
                    row[key]["path"] = "@study/kimi/"+old
            raw = a.jb(index)
            (input_root/"executions.json").write_bytes(raw)
            spec = json.loads(spec_path.read_bytes())
            spec["execution_index"].update(bytes=len(raw), sha256=a.sha(raw))
            spec_path.write_bytes(a.jb(spec))
            left = a.generate(spec_path, root/"restored_a")
            right = a.generate(spec_path, root/"restored_b")
            self.assertEqual(left, right)
            inventory = json.loads(left["INPUTS.json"])
            self.assertTrue(any(f["path"].startswith("@study/") for f in inventory["files"]))
            self.assertNotIn(str(root), left["INPUTS.json"].decode())

    def test_gpt_completion_adapter_does_not_need_scientific_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prep = p.Preparation(dict(study_root=str(root)))
            original_plan = root/"gpt/queue-plan.json"
            plan_ref = dict(path="plans/gpt.json", bytes=12, sha256="a"*64)
            prep.copies[str(original_plan.resolve())] = plan_ref
            rows = []
            for i in range(27):
                job = f"job_{i}"
                invocation = root/"gpt/study/invocations"/job
                receipt_path = root/"gpt/study/queue/jobs"/job/"completion.json"
                receipt_path.parent.mkdir(parents=True)
                receipt = dict(exit_code=0, job_id=job, artifacts={
                    "result/poolact/result.json": {"bytes": 10, "sha256": "b"*64},
                    "result/summary.json": {"bytes": 11, "sha256": "c"*64}})
                raw = a.jb(receipt)
                receipt_path.write_bytes(raw)
                rows.append(dict(scientific_slot_job_id=job, effective_physical_job_id=job,
                                 pool_terminal_status={"execution_complete": True}, receipt_artifact_inventory_verified=True,
                                 plan_path=str(original_plan), plan_sha256="a"*64,
                                 queue_receipt_path=str(receipt_path), queue_receipt_sha256=a.sha(raw),
                                 invocation_path=str(invocation), result_path=str(invocation/"result/poolact/result.json"),
                                 summary_path=str(invocation/"result/summary.json"), replacement_applied=False))
            source = root/"gpt/final_mapping.json"
            raw = a.jb(dict(schema="expgym.gpt-effective-delivery-mapping.v1", jobs=rows))
            source.write_bytes(raw)
            adapted, _ = p.adapt_gpt_mapping(prep, p.descriptor(source, raw))
            self.assertEqual(len(adapted), 27)
            self.assertEqual(adapted[0]["effective_plan"], plan_ref)
            self.assertFalse(Path(rows[0]["result_path"]).exists())
            self.assertEqual(adapted[0]["result"]["sha256"], "b"*64)

    def test_gpt_resource_adapter_keeps_superseded_attempts_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prep = p.Preparation(dict(study_root=str(root)))
            def write(name, raw):
                target = root/name
                target.write_bytes(raw)
                return p.descriptor(target, raw)
            tokens = {metric: dict(known_sum=10, unknown_attempts=0, total_if_fully_known=10)
                      for metric in ("input_tokens", "output_tokens", "reasoning_tokens")}
            usage = dict(by_physical_job={"effective": dict(physical_transport_attempts=2, states={"success": 2}, tokens=tokens)})
            attempts = [dict(physical_job_id=job, generation_id=generation) for job, generation in (
                ("effective", "generation-1"), ("effective", "generation-1"), ("superseded", "generation-0"))]
            metadata = dict(token_usage_summary=write("usage.json", a.jb(usage)),
                            physical_attempts=write("attempts.csv", a.csv_bytes(attempts)))
            mapping = dict(jobs=[dict(scientific_slot_job_id="logical", effective_physical_job_id="effective")])
            plan_rows = [dict(job_id="logical", model="gpt-5.6-sol", scenario="tuning", regime="cost_moderate", strategy="poolact")]
            rows, all_attempts = p.gpt_resources(prep, metadata, mapping, plan_rows)
            self.assertEqual(rows[0]["physical_attempts_complete_total"], 2)
            self.assertEqual(rows[0]["logical_generation_calls_complete_total"], 1)
            self.assertEqual(rows[0]["input_tokens_complete_total"], 10)
            self.assertIsNone(rows[0]["request_wall_seconds_complete_total"])
            self.assertIn("superseded", prep.files[all_attempts["physical_attempts"]["path"]].decode())


if __name__ == "__main__":
    unittest.main()
