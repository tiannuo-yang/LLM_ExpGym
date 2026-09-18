import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from expgym.llm_clients import OpenAICompatibleLLM
from expgym.react_loop import FakeLLM
from expgym.task_tuning import build_fake_plan
from expgym.trace_v2 import build_trace_v2
from scripts import run_paper_sweep, run_poolact
from tests.test_run_paper_sweep import _args


class APIDumpProvenanceTest(unittest.TestCase):
    def test_client_identity_is_read_only_and_disabled_without_dumps(self):
        with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": ""}):
            self.assertIsNone(OpenAICompatibleLLM(api_key="fixture-credential").dump_metadata)
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory, "EXPGYM_RUN_ID": "fixture"}):
                client = OpenAICompatibleLLM(api_key="fixture-credential")
            metadata = client.dump_metadata
            self.assertEqual(metadata["run_id"], "fixture")
            self.assertEqual(metadata["schema_version"], "expgym.api_attempt.v1")
            self.assertNotIn("fixture-credential", json.dumps(metadata))
            metadata["client_id"] = "changed"
            self.assertNotEqual(client.dump_metadata["client_id"], "changed")
            with self.assertRaises(AttributeError):
                client.dump_metadata = {}

    def test_both_runners_persist_client_identity_only_when_enabled(self):
        def factory(**kwargs):
            fake = FakeLLM(plan=build_fake_plan(1))

            def transport(request, _timeout):
                text = fake.generate(json.loads(request.data)["messages"]).text
                return json.dumps({"choices": [{"message": {"content": text}}]}).encode("utf-8")

            return OpenAICompatibleLLM(transport=transport, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            for enabled in (False, True):
                with self.subTest(enabled=enabled):
                    environment = {"EXPGYM_API_DUMP_DIR": directory if enabled else "", "EXPGYM_RUN_ID": "fixture"}
                    with mock.patch.dict(os.environ, environment), mock.patch("expgym.llm_clients.OpenAICompatibleLLM", side_effect=factory):
                        args = _args(backend="openai", output_dir=Path(directory), max_steps=2, max_evals=2)
                        job = run_paper_sweep._build_jobs(args)[0]
                        result = run_paper_sweep._run_job(args, job, "fixture-credential")
                        trace = build_trace_v2(result, repo_root=run_paper_sweep.REPO_ROOT)
                        self.assertEqual("api_dump" in trace["run"], enabled)
                        self.assertNotIn("api_dump", trace["run"]["generation"])
                        with mock.patch.object(sys, "argv", ["run_poolact.py", "--backend", "openai", "--model", "fixture",
                                                             "--agents", "2", "--max-steps", "2", "--question-index", "0"]):
                            pool_args = run_poolact.parse_args()
                        result = run_poolact._run_strategy(pool_args, "naive", "fixture-credential", 300.0, "time_aware")
                        self.assertTrue(all(("api_dump" in agent) == enabled for agent in result["agent_results"]))
                        self.assertNotIn("api_dump", run_poolact._resolved_config(pool_args, 300.0))
                        if enabled:
                            identities = [trace["run"]["api_dump"]] + [agent["api_dump"] for agent in result["agent_results"]]
                            self.assertEqual(len({identity["client_id"] for identity in identities}), 3)
                            raw_clients = {json.loads(path.read_text())["client_id"] for path in Path(directory).glob("*.json")}
                            self.assertEqual({identity["client_id"] for identity in identities}, raw_clients)


if __name__ == "__main__":
    unittest.main()
