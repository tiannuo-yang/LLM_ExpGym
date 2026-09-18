"""Explicit native wire selection must survive runner and resume boundaries."""
import argparse
from pathlib import Path
import sys
import tempfile
import unittest

from demo_experiment import build_llm
from scripts import run_paper_sweep as sweep, run_poolact as pool
from scripts.run_study_queue import make_plan


class NativeRunnerOptionsTest(unittest.TestCase):
    def test_both_runners_select_native_client_and_keep_nominal_controls(self):
        for protocol in ("responses", "anthropic"):
            with self.subTest(protocol=protocol):
                args = sweep.parse_args([
                    "--backend", "sub2api", "--models", "unfamiliar-model",
                    "--api-protocol", protocol, "--max-tokens", "32768",
                    "--reasoning-effort", "high", "--prompt-cache-scope", "disabled",
                    "--base-url", "http://localhost:8080/v1",
                ])
                job = sweep._build_jobs(args)[0]
                ns = sweep._namespace_for_job(args, job, "test-only-key")
                client = build_llm("sub2api", [], ns)
                self.assertEqual(client.api_protocol, protocol)
                self.assertEqual(client.config.max_tokens, 32768)
                self.assertIn("seed", client.parameter_compatibility["omitted_parameters"])
                p_args = pool.parse_args([
                    "--backend", "sub2api", "--model", "unfamiliar-model",
                    "--api-protocol", protocol, "--base-url", "http://localhost:8080/v1",
                ])
                p_ns = pool._agent_namespace(p_args, "poolact", 0, "test-only-key")
                self.assertEqual(build_llm("sub2api", [], p_ns).api_protocol, protocol)
                self.assertEqual(pool._resolved_config(p_args, 1)["api_protocol"], protocol)

    def test_protocol_changes_expgym_resume_identity(self):
        args = sweep.parse_args(["--backend", "sub2api", "--models", "unfamiliar-model"])
        job = sweep._build_jobs(args)[0]
        one = sweep._resume_key(args, job, evaluation={"sha256": "frozen-test"})
        args.api_protocol = "responses"
        two = sweep._resume_key(args, job, evaluation={"sha256": "frozen-test"})
        self.assertNotEqual(one, two)

    def test_queue_preserves_explicit_disabled_prompt_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = make_plan({"stages": [{"label": "one", "runner": "expgym", "args": [
                "--backend", "sub2api", "--models", "unfamiliar-model",
                "--api-protocol", "responses", "--prompt-cache-scope", "disabled",
                "--base-url", "http://localhost:8080/v1",
            ]}]}, study_id="test", output_root=Path(tmp), default_python=sys.executable)
            self.assertEqual(plan["jobs"][0]["args"]["prompt_cache_scope"], "disabled")


if __name__ == "__main__":
    unittest.main()
