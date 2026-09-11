"""Small CPU-only regressions for the fixed third-model matrix; no model calls."""
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import build_matrix as builder


STUDY = Path(__file__).resolve().parent
SOURCE = STUDY.parents[1] / "LLM_ExpGym-qwen38-20260910"
MAIN = STUDY / "python_main"
HPO = STUDY / "python_hpo"
DATA = STUDY.parent / "data"


def replace_arg(stage, flag, value):
    index = stage["args"].index(flag)
    stage["args"][index + 1] = value


class MatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = builder.load_manifest(builder.MANIFEST)
        cls.matrix = builder.build_stages(cls.manifest, SOURCE, MAIN, HPO)

    def validate(self, matrix, **kwargs):
        return builder.expand_and_validate(matrix, self.manifest, SOURCE,
                                           python=MAIN, python_hpo=HPO, **kwargs)

    def test_exact_coverage_and_runtime_seed_mapping(self):
        coverage = self.validate(self.matrix)
        self.assertEqual((coverage["stages"], coverage["queue_jobs"], coverage["agent_traces"]),
                         (33, 783, 1881))
        self.assertEqual(coverage["jobs_by_python"], {str(MAIN): 756, str(HPO): 27})
        self.assertEqual(coverage["canonical_identity_sha256"],
                         "469ac7b34ab802d7b60747275a9f8a1853706275a489b75c5336ffff1d21b13e")
        hpo_units = [row for row in coverage["stage_units"] if row["scenarios"] == ["tuning"]]
        self.assertEqual({tuple(row["scientific_outerreps"]) for row in hpo_units}, {(0,), (1,), (2,)})
        for unit in hpo_units:
            outer = unit["scientific_outerreps"][0]
            self.assertTrue(all(seeds[0] == 2200 + 4 * outer for seeds in unit["agent_seed_blocks"]))

    def test_actual_queue_expansion_in_memory_only(self):
        self.validate(self.matrix)
        queue = importlib.import_module("scripts.run_study_queue")
        matrix = builder.build_stages(self.manifest, SOURCE, MAIN, HPO,
                                      endpoints=["http://127.0.0.1:9/v1"])
        # No filesystem write, endpoint request, wrapper process, or final plan.
        plan = queue.make_plan(matrix, study_id="offline-unit-test-only",
                               output_root=Path("/not-created/offline-matrix-test"),
                               default_python=str(MAIN))
        self.assertEqual(len(plan["jobs"]), 783)
        self.assertEqual(len({job["job_id"] for job in plan["jobs"]}), 783)
        self.assertEqual(len({job["args"]["output_dir"] for job in plan["jobs"]}), 783)
        self.assertEqual(len({job["args"]["prompt_cache_key"] for job in plan["jobs"]}), 783)

    def test_seed_and_audit_order_changes_rejected_without_count_change(self):
        matrix = copy.deepcopy(self.matrix)
        stage = next(stage for stage in matrix["stages"]
                     if stage["runner"] == "expgym" and "--tuning-tasks" in stage["args"]
                     and stage["args"][stage["args"].index("--seed") + 1] == "2204")
        replace_arg(stage, "--seed", "2201")
        with self.assertRaisesRegex(ValueError, "identity"):
            self.validate(matrix)
        matrix = copy.deepcopy(self.matrix)
        stage = next(stage for stage in matrix["stages"] if "--audit-orders" in stage["args"])
        with tempfile.TemporaryDirectory(prefix="qwen38-matrix-orders-test-") as directory:
            orders = json.loads((SOURCE / "configs/audit_hypothesis_orders.json").read_text())
            orders["orders"][0], orders["orders"][1] = orders["orders"][1], orders["orders"][0]
            changed_orders = Path(directory) / "orders.json"
            changed_orders.write_text(json.dumps(orders))
            replace_arg(stage, "--audit-orders", str(changed_orders))
            with self.assertRaisesRegex(ValueError, "identity"):
                self.validate(matrix)

    def test_missing_or_duplicate_stage_rejected(self):
        matrix = copy.deepcopy(self.matrix)
        matrix["stages"].pop()
        with self.assertRaisesRegex(ValueError, "identity"):
            self.validate(matrix)
        matrix = copy.deepcopy(self.matrix)
        duplicate = copy.deepcopy(matrix["stages"][0])
        duplicate["label"] += "-extra"
        matrix["stages"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "identity"):
            self.validate(matrix)

    def test_model_runtime_and_profile_changes_rejected(self):
        changes = [("expgym", "--model-alias", builder.MODEL + "=wrong-model"),
                   ("poolact", "--model", "wrong-model"),
                   ("expgym", "--max-tokens", "16384"),
                   ("expgym", "--reasoning-effort", "high"),
                   ("poolact", "--top-k", "10"),
                   ("poolact", "--probes", "3"),
                   ("poolact", "--max-context-tokens", "262144"),
                   ("expgym", "--trace-format", "v1")]
        changes.append(("poolact", "--prompt-cache-key-field", "prompt_cache_key"))
        for runner, flag, value in changes:
            with self.subTest(flag=flag, runner=runner):
                matrix = copy.deepcopy(self.matrix)
                stage = next(stage for stage in matrix["stages"] if stage["runner"] == runner)
                replace_arg(stage, flag, value)
                with self.assertRaises(ValueError):
                    self.validate(matrix)
        matrix = copy.deepcopy(self.matrix)
        stage = next(stage for stage in matrix["stages"] if stage["python"] == str(HPO))
        stage["python"] = str(MAIN)
        with self.assertRaisesRegex(ValueError, "runtime"):
            self.validate(matrix)

    def test_admitted_deployment_and_auth_path_without_reading_credentials(self):
        endpoints = ["http://127.0.0.1:9/v1", "http://127.0.0.1:10/v1"]
        auth_file = Path("/nonexistent-key-not-to-be-read/matrix-test-placeholder")
        with self.assertRaisesRegex(ValueError, "no-auth"):
            builder.build_stages(self.manifest, SOURCE, MAIN, HPO,
                                 endpoints=endpoints, auth_file=auth_file)
        matrix = builder.build_stages(self.manifest, SOURCE, MAIN, HPO,
                                      endpoints=endpoints)
        self.validate(matrix, endpoints=endpoints)
        for target in ("endpoint", "base-url", "auth-file"):
            with self.subTest(target=target):
                changed = copy.deepcopy(matrix)
                if target == "endpoint":
                    changed["stages"][0]["endpoints"] = ["http://127.0.0.1:11/v1"]
                elif target == "auth-file":
                    changed["stages"][0]["args"] += ["--api-key-file", str(auth_file)]
                else:
                    replace_arg(changed["stages"][0], "--base-url", "http://127.0.0.1:11/v1")
                with self.assertRaises(ValueError):
                    self.validate(changed, endpoints=endpoints)
        for value in ("http://user:secret@localhost/v1", "http://localhost/v1?key=secret",
                      "http://localhost/v1#secret", "file:///tmp/api"):
            with self.assertRaises(ValueError):
                builder.endpoints_from_values([value])

    def test_pinned_manifest_and_input_mapping(self):
        with tempfile.TemporaryDirectory(prefix="qwen38-matrix-test-") as directory:
            altered = Path(directory) / "manifest.json"
            altered.write_bytes(builder.MANIFEST.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                builder.load_manifest(altered)
        inputs = builder.expected_inputs(self.manifest, SOURCE, DATA)
        self.assertEqual(len(inputs["required_unchanged_inputs"]), 21)
        self.assertFalse(inputs["large_data_bytes_verified_here"])
        self.assertEqual(set(inputs["historical_runtime_references"]),
                         {"paramnet.runtime_config", "paramnet.wrapper"})

    def test_offline_draft_writes_only_three_assets_and_queue_rejects_it(self):
        with tempfile.TemporaryDirectory(prefix="qwen38-matrix-draft-test-") as directory:
            command = [sys.executable, "-B", str(STUDY / "build_matrix.py"),
                       "--source-repo", str(SOURCE), "--data-root", str(DATA),
                       "--python", str(MAIN), "--python-hpo", str(HPO),
                       "--draft", "--output-dir", directory]
            completed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual({path.name for path in Path(directory).iterdir()},
                             {"matrix.json", "coverage.json", "runtime_environment.json"})
            coverage = json.loads((Path(directory) / "coverage.json").read_text())
            self.assertTrue(coverage["deployment_pending"])
            self.assertFalse(coverage["credentials_read"])
            self.assertEqual(coverage["new_model_calls"], 0)
            queue = importlib.import_module("scripts.run_study_queue")
            with self.assertRaisesRegex(ValueError, "unknown stage fields"):
                queue.make_plan(json.loads((Path(directory) / "matrix.json").read_text()),
                                study_id="offline-draft-test", output_root=Path(directory) / "not-created",
                                default_python=str(MAIN))
            again = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("output exists", again.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
