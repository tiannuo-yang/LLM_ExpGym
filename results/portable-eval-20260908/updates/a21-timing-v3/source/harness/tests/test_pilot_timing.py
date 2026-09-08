"""Independent CPU-only harness checks; never contact model endpoints."""
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict
import copy
import hashlib
import importlib.util
from io import StringIO
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "pilot_timing.py"
SPEC = importlib.util.spec_from_file_location("portable_pilot_timing", SCRIPT)
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


class PilotTests(unittest.TestCase):
    def args(self, directory, *extra):
        return pilot.parse_args(["--output-dir", str(directory)] + list(extra))

    def test_matrix_is_exact_21_traces_in_two_stages(self):
        args = self.args("/tmp/pilot-unit-plan")
        jobs = pilot.build_jobs(args)
        self.assertEqual(len(jobs), 21)
        self.assertEqual(len({job["id"] for job in jobs}), 21)
        self.assertEqual([job["stage"] for job in jobs], [pilot.STAGES[0]] * 9 + [pilot.STAGES[1]] * 12)
        self.assertEqual({job["tuning_task"] for job in jobs[:9]}, set(pilot.TASKS))
        self.assertTrue(all(job["regime"] == "cost_moderate" for job in jobs[:9]))
        self.assertEqual({(job["scenario"], job["question_index"], job["regime"]) for job in jobs[9:]},
                         {(scenario, index, regime) for scenario, indices in (("restricted_search", (0, 18)), ("evidence_audit", (0, 2))) for index in indices for regime in pilot.REGIMES})
        self.assertEqual(sum(job["expected_traces"] for job in jobs), 21)

    def test_schedule_is_fixed_and_not_score_dependent(self):
        args = self.args("/tmp/pilot-unit-plan")
        jobs = pilot.build_jobs(args)
        self.assertEqual(jobs, pilot.build_jobs(args))
        ids = [job["id"] for job in jobs]
        self.assertNotEqual(ids, sorted(ids))
        changed = pilot.build_jobs(self.args("/tmp/pilot-unit-plan", "--schedule-seed", "15"))
        self.assertEqual(set(ids), {job["id"] for job in changed})
        self.assertNotEqual(ids, [job["id"] for job in changed])
        self.assertEqual([job["dispatch_index"] for job in jobs], list(range(21)))

    def test_runtime_split_and_resume_shim_preserve_interpreter(self):
        args = self.args("/tmp/pilot-unit-plan")
        jobs = pilot.build_jobs(args)
        self.assertEqual(sum(job["runtime"] == "legacy_paramnet" for job in jobs), 3)
        for job in jobs:
            expected = args.legacy_runtime_dir / ".venv-hpo/bin/python" if job["runtime"] == "legacy_paramnet" else args.python
            self.assertEqual(job["command"][0], str(expected))
            self.assertEqual(pilot.guard_command(job)[:2], job["command"][:2])
            self.assertEqual(pilot.guard_command(job)[2:4], [str(SCRIPT), "--_resume-guard"])
            self.assertEqual(pilot.guard_command(job)[4:-1], job["command"][2:])
            self.assertEqual(pilot.guard_command(job)[-1], "--resume")

    def test_every_command_has_frozen_profile(self):
        args = self.args("/tmp/pilot-unit-plan", "--backend", "openai", "--base-url", "http://example.invalid/v1")
        for job in pilot.build_jobs(args):
            command = job["command"]
            for flag, value in {"--max-steps": "30", "--max-evals": "30", "--max-tokens": "32768", "--reasoning-effort": "max", "--tool-protocol": "native", "--max-protocol-retries": "1", "--tuning-final-policy": "legacy", "--temperature-tuning": "1", "--temperature-eval": "1", "--audit-reps": "1", "--prompt-cache-scope": "disabled"}.items():
                self.assertEqual(command[command.index(flag) + 1], value)
            self.assertNotIn("--resume", command)
            self.assertNotIn("--shuffle", command)
            self.assertEqual(json.loads(command[command.index("--chat-template-kwargs") + 1]), {"thinking": True, "thinking_effort": "max"})
        self.assertFalse(args.execute)

    def test_real_requires_both_authority_flag_and_endpoint(self):
        for extra in (("--execute", "--backend", "openai"), ("--execute", "--backend", "openai", "--allow-real"), ("--execute", "--backend", "openai", "--base-url", "http://example.invalid/v1")):
            with self.subTest(extra=extra), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                self.args("/tmp/pilot-unit-plan", *extra)
        self.assertTrue(self.args("/tmp/pilot-unit-plan", "--execute", "--backend", "openai", "--allow-real", "--base-url", "http://example.invalid/v1").execute)

    def test_rejects_endpoints_with_secrets_and_fake_endpoint(self):
        for url in ("http://user:secret@example.invalid/v1", "http://example.invalid/v1?key=x", "http://example.invalid/#x", "file:///tmp/model"):
            with self.subTest(url=url), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                self.args("/tmp/pilot-unit-plan", "--backend", "openai", "--base-url", url)
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.args("/tmp/pilot-unit-plan", "--base-url", "http://example.invalid/v1")

    def test_worker_bound_and_repository_output_guard(self):
        for value in ("0", "5"):
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                self.args("/tmp/pilot-unit-plan", "--workers", value)
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.args(pilot.WORKSPACE / "LLM_ExpGym/never_create")

    def test_ambient_endpoints_and_hpo_overrides_are_removed(self):
        args = self.args("/tmp/pilot-unit-plan")
        legacy, native = (next(job for job in pilot.build_jobs(args) if job["runtime"] == runtime) for runtime in ("legacy_paramnet", "native"))
        bad = {name: "UNWANTED" for name in ("OPENAI_API_KEY", "SUB2API_API_KEY", "OPENAI_BASE_URL", "EXPGYM_BASE_URL", "PYTHONPATH", "HPOBENCH_ROOT", "XDG_DATA_HOME", "EXPGYM_HPO_THREADS")}
        with mock.patch.dict(os.environ, bad):
            env = pilot.child_environment(args, native)
            for name in bad:
                if name != "EXPGYM_HPO_THREADS":
                    self.assertNotIn(name, env)
            self.assertEqual(env["EXPGYM_HPO_THREADS"], "1")
            env = pilot.child_environment(args, legacy)
            self.assertEqual(env["HPOBENCH_ROOT"], str(args.repo_root / "data/hpo_tuning/HPOBench"))
            self.assertEqual(env["XDG_CONFIG_HOME"], str(args.legacy_runtime_dir / "hpobench_config"))
            self.assertEqual(env["OMP_NUM_THREADS"], "1")
            self.assertEqual(pilot.child_environment(args, native, "TEST_ONLY_SECRET")["OPENAI_API_KEY"], "TEST_ONLY_SECRET")

    def test_proxy_route_is_explicit_and_direct(self):
        args = self.args("/tmp/pilot-unit-plan")
        job = pilot.build_jobs(args)[0]
        names = ("HTTP_PROXY", "https_proxy", "ALL_PROXY", "HtTp_PrOxY", "NO_PROXY", "no_proxy")
        with mock.patch.dict(os.environ, {name: "http://proxy.invalid" for name in names}):
            env = pilot.child_environment(args, job)
        self.assertEqual(env["NO_PROXY"], "*")
        self.assertEqual(env["no_proxy"], "*")
        self.assertFalse(any(name.lower() in {"http_proxy", "https_proxy", "all_proxy"} for name in env))

    def fixture_receipt(self, directory):
        repo = directory / "repo"
        for name in ("demo_experiment.py", "expgym/module.py", "README.MD", "configs/hpobench_tasks.yaml", "configs/audit_hypothesis_orders.json", "requirements.txt", "requirements-data.txt"):
            path = repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n")
        files = {path.relative_to(repo).as_posix(): pilot.helpers().sha256(path) for path in repo.rglob("*") if path.is_file()}
        digest = hashlib.sha256()
        for path in pilot.source_paths(repo):
            digest.update(path.relative_to(repo).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
        receipt = directory / "acceptance.json"
        receipt.write_text(json.dumps({"files": files, "source_tree_sha256": digest.hexdigest()}))
        return repo, receipt

    def test_receipt_checks_config_files_outside_source_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, receipt = self.fixture_receipt(Path(temporary))
            self.assertEqual(len(pilot.verify_acceptance(repo, receipt)["verified_files"]), 7)
            (repo / "configs/hpobench_tasks.yaml").write_text("modified config\n")
            with self.assertRaisesRegex(RuntimeError, "file mismatch"):
                pilot.verify_acceptance(repo, receipt)

    def test_receipt_rejects_missing_source_inventory_and_arbitrary_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, receipt = self.fixture_receipt(Path(temporary))
            data = json.loads(receipt.read_text())
            data["source_tree_sha256"] = "0" * 64
            receipt.write_text(json.dumps(data))
            with self.assertRaisesRegex(RuntimeError, "source digest mismatch"):
                pilot.verify_acceptance(repo, receipt)
            (repo / "expgym/new_source.py").write_text("new code\n")
            with self.assertRaisesRegex(RuntimeError, "omits"):
                pilot.verify_acceptance(repo, receipt)

    def test_snapshot_covers_extra_json_and_byte_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "trace.json").write_text('{"value": 1}\n')
            before = pilot.snapshot(root)
            (root / "summary.json").write_text('{}\n')
            self.assertNotEqual(before, pilot.snapshot(root))
            (root / "trace.json").write_text('{"value": 2}\n')
            self.assertNotEqual(before["trace.json"]["sha256"], pilot.snapshot(root)["trace.json"]["sha256"])
            self.assertEqual(set(pilot.snapshot(root)), {"trace.json", "summary.json"})

    def test_guard_fails_closed_without_constructing_fake_model(self):
        # Isolated fixture repository, so the guard cannot mutate core modules
        # imported by other tests. No real client/endpoint is present.
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            (repo / "scripts").mkdir()
            (repo / "expgym").mkdir()
            (repo / "expgym/__init__.py").write_text("")
            (repo / "demo_experiment.py").write_text("class FakeLLM:\n    def generate(self): return 'unexpected'\ndef build_llm():\n    raise AssertionError('unguarded factory')\n")
            (repo / "expgym/llm_clients.py").write_text("class OpenAICompatibleLLM:\n    def generate(self): return 'unexpected'\n")
            runner = repo / "scripts/run_paper_sweep.py"
            runner.write_text("import demo_experiment\ndemo_experiment.build_llm()\n")
            completed = subprocess.run([sys.executable, str(SCRIPT), "--_resume-guard", str(runner), "--resume"], capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("PILOT_GUARD_MODEL_CALL_FORBIDDEN", completed.stderr)
            self.assertNotIn("unguarded factory", completed.stderr)

    def test_log_redacts_key_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.args(temporary)
            job = pilot.build_jobs(args)[0]
            command = [sys.executable, "-c", "import os; print(os.environ['OPENAI_API_KEY'])"]
            receipt, output = pilot.run_child(args, job, command, "unit.log", "TEST_ONLY_SECRET")
            self.assertEqual(receipt["exit_code"], 0)
            self.assertNotIn("TEST_ONLY_SECRET", output)
            self.assertIn("[REDACTED]", Path(receipt["log"]).read_text())
            with mock.patch.object(pilot.subprocess, "run") as child, self.assertRaises(FileExistsError):
                pilot.run_child(args, job, command, "unit.log", "TEST_ONLY_SECRET")
            child.assert_not_called()

    def dump_fixture(self, directory):
        args = self.args(directory, "--backend", "openai", "--base-url", "http://example.invalid/v1")
        job = pilot.build_jobs(args)[0]
        job["preflight"] = {"job": {"fixture": "same"}}
        trace_path = Path(job["output_dir"]) / "k3_cost_moderate/traces-v2/trace.json"
        trace_path.parent.mkdir(parents=True)
        message = {"role": "assistant", "content": "answer", "reasoning_content": "verbatim reasoning"}
        trace_path.write_text(json.dumps({"run": {"api_dump": {"client_id": "client"}}, "outcome": {"http_request_attempts": 1},
                                         "messages": [{"id": "m1", "role": "user", "content": "input"}], "tool_calls": [],
                                         "llm_calls": [{"id": "call", "input_message_ids": ["m1"], "forced": False, "output_message": message, "finish_reason": "stop", "attempt_usage": [{"request_id": "request", "generation_id": "generation", "attempt": 1, "state": "success", "http_status": None, "usage": {"completion_tokens": 3}}]}]}))
        dump_path = Path(job["dump_dir"]) / "request.json"
        dump_path.parent.mkdir(parents=True)
        record = {"schema_version": "expgym.api_attempt.v1", "request_id": "request", "client_id": "client", "state": "success", "finished_at_utc": "2026-09-08T00:00:00Z", "generation_id": "generation", "max_attempts": 3, "attempt": 1, "will_retry": False,
                  "endpoint": "http://example.invalid/v1/chat/completions", "run_id": "pilot-a21:" + args.output_dir.name, "context": {"job": job["preflight"]["job"]},
                  "request_payload": {"model": args.model, "messages": [{"role": "user", "content": "input"}], "temperature": 1, "top_p": 1, "max_tokens": 32768, "seed": args.seed, "reasoning_effort": "max", "chat_template_kwargs": {"thinking": True, "thinking_effort": "max"}, "tools": [{"type": "function", "function": {"name": "probe", "parameters": {"type": "object"}}}], "tool_choice": "auto", "parallel_tool_calls": False},
                  "response_json": {"choices": [{"message": message, "finish_reason": "stop"}], "usage": {"completion_tokens": 3}}}
        dump_path.write_text(json.dumps(record))
        return args, job, dump_path, record

    def test_dump_profile_checks_native_fields_and_endpoint_normalization(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, job, path, record = self.dump_fixture(temporary)
            self.assertTrue(pilot.dump_profile(args, job)["passed"])
            for key, value in (("top_p", .95), ("seed", 2), ("parallel_tool_calls", True), ("tool_choice", {"unexpected": True})):
                with self.subTest(key=key):
                    changed = copy.deepcopy(record)
                    changed["request_payload"][key] = value
                    path.write_text(json.dumps(changed))
                    self.assertFalse(pilot.dump_profile(args, job)["passed"])

    def test_dump_retry_chain_must_be_closed_and_contiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, job, path, record = self.dump_fixture(temporary)
            record["attempt"] = 2
            path.write_text(json.dumps(record))
            self.assertFalse(pilot.dump_profile(args, job)["passed"])
            record["attempt"] = 1
            record["will_retry"] = True
            path.write_text(json.dumps(record))
            self.assertFalse(pilot.dump_profile(args, job)["passed"])

    def test_malformed_response_usage_is_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, job, path, record = self.dump_fixture(temporary)
            record["response_json"] = {"choices": None}
            path.write_text(json.dumps(record))
            result = pilot.dump_profile(args, job)
            self.assertIsNone(result["attempts"][0]["usage"])
            self.assertEqual(result["attempts"][0]["finish_reasons"], [])

    def test_request_bijection_and_wire_history_are_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, job, path, record = self.dump_fixture(temporary)
            for field in ("generation_id", "request_id", "messages", "output_reasoning", "tool_choice"):
                with self.subTest(field=field):
                    changed = copy.deepcopy(record)
                    if field in {"generation_id", "request_id"}:
                        changed[field] = "other"
                    elif field == "messages":
                        changed["request_payload"]["messages"][0]["content"] = "different"
                    elif field == "output_reasoning":
                        changed["response_json"]["choices"][0]["message"]["reasoning_content"] = "different"
                    else:
                        changed["request_payload"]["tool_choice"] = "none"
                    path.write_text(json.dumps(changed))
                    self.assertFalse(pilot.dump_profile(args, job)["passed"])

    def test_wire_redaction_preserves_credential_safety(self):
        secret = "TEST_ONLY_SECRET"
        value = {"content": "echo " + secret, "api_key": "not the supplied key", "tools": [{"arguments": secret}]}
        client = pilot.repository_module(pilot.WORKSPACE / "LLM_ExpGym", "expgym.llm_clients").OpenAICompatibleLLM
        redacted = pilot.redact_wire(value, secret, client._is_secret_field)
        self.assertEqual(redacted, {"content": "echo [REDACTED]", "api_key": "[REDACTED]", "tools": [{"arguments": "[REDACTED]"}]})
        self.assertEqual(value["api_key"], "not the supplied key")

    def test_actual_client_trace_and_dump_contract_with_mock_transport(self):
        # Real runner/client serialization, but a data-free builtin task and
        # an in-process transport mock. No socket, model, GPU or dataset read.
        with tempfile.TemporaryDirectory() as temporary:
            args = self.args(temporary, "--backend", "openai", "--base-url", "http://example.invalid/v1")
            job = next(job for job in pilot.build_jobs(args) if job["runtime"] == "native" and job["stage"] == pilot.STAGES[0])
            command = job["command"][2:]
            command[command.index("--tuning-tasks") + 1] = "neural_network_training"
            clients = pilot.repository_module(args.repo_root, "expgym.llm_clients")
            response = {"choices": [{"message": {"role": "assistant", "content": '{"invalid_configuration": 1}', "reasoning_content": "mock reasoning"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
            env = pilot.child_environment(args, job, "TEST_ONLY_SECRET")
            with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(sys, "argv", command), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                scope = runpy.run_path(command[0], run_name="pilot_unit_runner")
                parsed = scope["parse_args"]()
                job["preflight"] = {"job": asdict(scope["_build_jobs"](parsed)[0])}
                transport = mock.Mock(return_value=json.dumps(response).encode())
                original_init = clients.OpenAICompatibleLLM.__init__

                def initialize(instance, *positional, **kwargs):
                    kwargs["transport"] = transport
                    original_init(instance, *positional, **kwargs)

                with mock.patch.object(clients.OpenAICompatibleLLM, "__init__", new=initialize):
                    self.assertEqual(scope["main"](), 0)
                    self.assertEqual(transport.call_count, 1)
            report = pilot.dump_profile(args, job, "TEST_ONLY_SECRET")
            self.assertTrue(report["passed"], report["errors"])
            self.assertEqual(len(report["attempts"]), 1)


if __name__ == "__main__":
    unittest.main()
