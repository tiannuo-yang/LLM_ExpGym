"""No-network sampling controls across clients, runners, identities and wrappers."""
import argparse
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

import demo_experiment
from expgym.llm_clients import OpenAICompatibleLLM
from scripts import run_paper_sweep, run_poolact
from tests.test_run_paper_sweep import _args

ROOT = Path(__file__).resolve().parents[1]


class GenerationSamplingTest(unittest.TestCase):
    PARSERS = (demo_experiment, run_paper_sweep, run_poolact)

    def parse(self, module, options):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(sys, "argv", [module.__name__] + options):
                return module.parse_args()

    def test_legacy_defaults_and_older_programmatic_namespaces(self):
        for module in self.PARSERS:
            with self.subTest(cli=module.__name__):
                args = self.parse(module, [])
                self.assertEqual(args.top_p, 1.0)
                self.assertIsNone(args.top_k)
        options = demo_experiment._generation_options(argparse.Namespace())
        self.assertEqual(options["top_p"], 1.0)
        self.assertIsNone(options["top_k"])

    def test_all_cli_accept_explicit_sampling_in_both_forms(self):
        for module in self.PARSERS:
            for options in (["--top-p", "0.95", "--top-k", "-1"],
                            ["--top-p=0.95", "--top-k=40"]):
                with self.subTest(cli=module.__name__, options=options):
                    args = self.parse(module, options)
                    self.assertEqual(args.top_p, 0.95)
                    self.assertEqual(args.top_k, -1 if options[0] == "--top-p" else 40)

    def test_all_cli_reject_invalid_sampling_before_execution(self):
        invalid = {
            "--top-p": ("0", "-1", "1.01", "NaN", "Infinity", "-Infinity", "1e309", "true", "null"),
            "--top-k": ("0", "-2", "1.0", "2.5", "NaN", "Infinity", "true", "null"),
        }
        for module in self.PARSERS:
            for option, values in invalid.items():
                for value in values:
                    with self.subTest(cli=module.__name__, option=option, value=value):
                        with mock.patch.object(sys, "stderr", io.StringIO()):
                            with self.assertRaises(SystemExit) as raised:
                                self.parse(module, [option + "=" + value])
                        self.assertEqual(raised.exception.code, 2)

    def test_client_rejects_invalid_programmatic_values(self):
        invalid = {
            "top_p": (True, False, 0, -1, 1.01, float("nan"), float("inf"), -float("inf"), "0.95", None, 10 ** 500),
            "top_k": (True, False, 0, -2, 1.0, 2.5, float("nan"), float("inf"), "40"),
        }
        for name, values in invalid.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    transport = mock.Mock()
                    with self.assertRaisesRegex(ValueError, name):
                        OpenAICompatibleLLM(api_key="test-placeholder", transport=transport, **{name: value})
                    transport.assert_not_called()

    def test_default_and_explicit_values_reach_wire_unchanged(self):
        for top_p, top_k in ((1.0, None), (0.95, -1), (0.25, 40), (1e-9, 1)):
            with self.subTest(top_p=top_p, top_k=top_k):
                requests = []

                def transport(request, timeout):
                    requests.append(json.loads(request.data))
                    return json.dumps({"choices": [{"message": {"content": "Answer: done"}}]}).encode()

                client = OpenAICompatibleLLM(
                    api_key="test-placeholder", transport=transport, top_p=top_p, top_k=top_k,
                )
                client.generate("one")
                client.generate("two", tools=[{"type": "function", "function": {
                    "name": "probe", "parameters": {"type": "object", "properties": {}},
                }}], tool_choice="auto")
                self.assertEqual(client.config.top_p, top_p)
                self.assertEqual(client.config.top_k, top_k)
                for payload in requests:
                    self.assertEqual(payload["top_p"], top_p)
                    if top_k is None:
                        self.assertNotIn("top_k", payload)
                    else:
                        self.assertEqual(payload["top_k"], top_k)

    def test_shared_demo_options_reach_all_five_real_factories(self):
        original_client = OpenAICompatibleLLM
        for backend in ("openai", "gemini", "openrouter", "sub2api", "vllm"):
            with self.subTest(backend=backend):
                args = self.parse(demo_experiment, [
                    "--api-key", "test-placeholder", "--model", "model-under-test",
                    "--top-p", "0.95", "--top-k", "40",
                ])
                requests = []

                def transport(request, timeout):
                    requests.append(json.loads(request.data))
                    return b'{"choices":[{"message":{"content":"Answer: done"}}]}'

                def factory(**kwargs):
                    return original_client(transport=transport, **kwargs)

                with mock.patch("expgym.llm_clients.OpenAICompatibleLLM", side_effect=factory):
                    client = demo_experiment.build_llm(backend, [], args)
                client.generate("test")
                self.assertEqual(requests[0]["top_p"], 0.95)
                self.assertEqual(requests[0]["top_k"], 40)

    def test_sweep_namespace_resume_and_cache_identity(self):
        base = _args(top_p=1.0, top_k=None, prompt_cache_key="sampling-test")
        job = run_paper_sweep._build_jobs(base)[0]
        identity = {"sha256": "synthetic-offline-identity"}
        base_key = run_paper_sweep._resume_key(base, job, evaluation=identity)
        base_cache = run_paper_sweep._prompt_cache_config(base, job)
        for changes in ({"top_p": 0.95}, {"top_k": -1}, {"top_k": 40}):
            args = copy.copy(base)
            vars(args).update(changes)
            ns = run_paper_sweep._namespace_for_job(args, job, None)
            self.assertEqual(ns.top_p, args.top_p)
            self.assertEqual(ns.top_k, args.top_k)
            self.assertNotEqual(base_key, run_paper_sweep._resume_key(args, job, evaluation=identity))
            self.assertNotEqual(base_cache, run_paper_sweep._prompt_cache_config(args, job))
        explicit_default = copy.copy(base)
        explicit_default.top_p = 1.0
        self.assertEqual(base_key, run_paper_sweep._resume_key(explicit_default, job, evaluation=identity))
        base.prompt_cache_scope = "disabled"
        changed = copy.copy(base)
        changed.top_p = 0.95
        self.assertNotEqual(
            run_paper_sweep._resume_key(base, job, evaluation=identity),
            run_paper_sweep._resume_key(changed, job, evaluation=identity),
        )

    def test_poolact_configuration_and_agent_namespace_include_sampling(self):
        args = self.parse(run_poolact, ["--top-p", "0.95", "--top-k", "-1"])
        config = run_poolact._resolved_config(args, 300.0)
        self.assertEqual(config["top_p"], 0.95)
        self.assertEqual(config["top_k"], -1)
        agent = run_poolact._agent_namespace(args, "naive", 0, "test-placeholder")
        self.assertEqual(agent.top_p, 0.95)
        self.assertEqual(agent.top_k, -1)
        changed = copy.copy(args)
        changed.top_p = 1.0
        self.assertNotEqual(config, run_poolact._resolved_config(changed, 300.0))

    def test_v1_records_readable_requested_sampling(self):
        args = _args(backend="fake", models="fake", trace_format="v1",
                     max_steps=2, max_evals=1, top_p=0.95, top_k=40)
        job = run_paper_sweep._build_jobs(args)[0]
        result = run_paper_sweep._run_job(args, job, None)
        self.assertEqual(result["generation_options"]["top_p"], 0.95)
        self.assertEqual(result["generation_options"]["top_k"], 40)
        self.assertTrue(result["score_check"]["ok"])

    def test_full_wrapper_dry_run_preserves_sampling(self):
        environment = {"PATH": os.environ.get("PATH", os.defpath),
                       "EXPGYM_VENV": str(Path(sys.executable).parent.parent)}
        for flags in (["--top-p", "0.95", "--top-k", "-1"],
                      ["--top-p=0.95", "--top-k=40"]):
            with self.subTest(flags=flags):
                completed = subprocess.run(
                    ["bash", "scripts/run_full.sh", "--backend", "fake", "--model", "fake",
                     "--dry-run"] + flags, cwd=ROOT, env=environment,
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn('"top_p": 0.95', completed.stdout)
                self.assertIn('"top_k": ' + ("-1" if "-1" in flags else "40"), completed.stdout)


if __name__ == "__main__":
    unittest.main()
