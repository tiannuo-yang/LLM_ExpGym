"""Real fake-backend worker -> custom trace export -> queue verification."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from expgym.trace_v2 import validate_trace_v2
from scripts import run_paper_sweep as sweep
from scripts import run_study_queue as queue


class CustomBetaExportTest(unittest.TestCase):
    def test_complete_fake_workers_export_all_betas_and_verify_in_new_process(self):
        with tempfile.TemporaryDirectory(prefix="gemini-beta-export-") as directory:
            root = Path(directory)
            stages = [{"label": "beta" + str(beta), "runner": "expgym", "args": [
                "--backend", "fake", "--models", "fake", "--scenarios", "restricted_search",
                "--search-data-source", "phantom_seed2", "--search-indices", "2",
                "--seed", "2200", "--cost-regimes", "custom", "--beta", str(beta),
                "--tool-protocol", "auto", "--max-steps", "3", "--max-evals", "3",
                "--missing-final-policy", "task-abstention-v1", "--trace-format", "v2",
            ]} for beta in (1, 5, 15, 20)]
            plan = queue.make_plan({"stages": stages}, study_id="fake-custom-export",
                                   output_root=root / "outputs", default_python=sys.executable)
            plan_path = root / "plan.json"
            raw = json.dumps(plan, sort_keys=True).encode()
            plan_path.write_bytes(raw)
            checksum = hashlib.sha256(raw).hexdigest()
            for row in plan["jobs"]:
                command = [sys.executable, "-B", str(Path(queue.__file__)), "worker",
                           "--plan", str(plan_path), "--sha256", checksum,
                           "--job-id", row["job_id"]]
                with self.subTest(beta=row["selection"]["beta"]):
                    run = subprocess.run(command, cwd=queue.REPO_ROOT, capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    verify = subprocess.run(command + ["--verify-only"], cwd=queue.REPO_ROOT,
                                            capture_output=True, text=True)
                    self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
                    job = sweep.Job(**row["selection"])
                    trace_path = sweep._trace_path(Path(row["args"]["output_dir"]), job, "v2")
                    trace = json.loads(trace_path.read_text())
                    validate_trace_v2(trace)
                    self.assertEqual(trace["task"]["budget"]["regime"], "custom")
                    self.assertEqual(trace["task"]["budget"]["beta"], job.beta)
                    self.assertEqual(trace["task"]["budget"]["limit_seconds"], 300 * job.beta)
                    self.assertEqual(trace["task"]["budget"]["mode"], "time_aware")
                    invalid = copy.deepcopy(trace)
                    invalid["task"]["budget"]["beta"] = 0
                    with self.assertRaises(ValueError):
                        validate_trace_v2(invalid)


if __name__ == "__main__":
    unittest.main()
