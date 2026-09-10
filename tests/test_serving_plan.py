"""No GPU/Slurm/model calls: topology, argument safety and lifecycle contracts."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import serve_slurm as serving


class ServingPlanTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(serving.DEFAULT_CONFIG.read_text())
        self.arguments = dict(checkpoint="/models/model-x", sglang_bin="/runtime/bin/sglang", model="model-x",
                              context_length=131072, mem_fraction_static=0.84, ep_size=1)
        self.plan = serving.build_plan(self.config, **self.arguments)

    def cli(self):
        return ["--checkpoint", "/models/model-x", "--sglang-bin", "/runtime/bin/sglang", "--model", "model-x",
                "--context-length", "131072", "--mem-fraction-static", "0.84", "--ep-size", "1"]

    def test_default_is_four_nodes_two_tp16_and_eight_invocation_slots(self):
        self.assertEqual(self.config["slurm"]["nodes"], 4)
        self.assertEqual(self.config["slurm"]["gpus_per_node"], 8)
        self.assertEqual(self.config["dispatch"]["max_workers"], 8)
        layout = serving.node_layout(self.plan, ["n0", "n1", "n2", "n3"])
        self.assertEqual([r["nodes"] for r in layout], [["n0", "n1"], ["n2", "n3"]])
        self.assertEqual([r["tp_size"] for r in layout], [16, 16])
        self.assertEqual([r["base_url"] for r in layout], ["http://n0:31240/v1", "http://n2:31241/v1"])
        addresses = set()
        for replica in layout:
            for rank in (0, 1):
                command = serving.server_command(self.plan, replica, rank, replica["nodes"][0])
                self.assertEqual(command[:2], ["/runtime/bin/sglang", "serve"])
                self.assertEqual(command[command.index("--tp-size") + 1], "16")
                self.assertEqual(command[command.index("--nnodes") + 1], "2")
                self.assertEqual(command[command.index("--node-rank") + 1], str(rank))
                addresses.add(command[command.index("--dist-init-addr") + 1])
        self.assertEqual(addresses, {"n0:51240", "n2:51241"})

    def test_no_generation_rewrite_or_architecture_guess(self):
        command = serving.server_command(self.plan, serving.node_layout(self.plan, ["n0", "n1", "n2", "n3"])[0], 0, "10.0.0.1")
        for absent in ("--max-tokens", "--temperature", "--top-p", "--random-seed", "--reasoning-parser", "--trust-remote-code"):
            self.assertNotIn(absent, command)
        self.assertFalse(self.plan["real_smoke_passed"])

    def test_explicit_model_parser_backend_options_preserved(self):
        kwargs = dict(self.arguments, reasoning_parser="custom_parser", tool_call_parser="custom_tools", trust_remote_code=True,
                      server_args=["--attention-backend", "fa3", "--random-seed", "42", "--enable-symm-mem"])
        plan = serving.build_plan(self.config, **kwargs)
        command = serving.server_command(plan, serving.node_layout(plan, ["n0", "n1", "n2", "n3"])[1], 1, "10.0.0.3")
        self.assertIn("custom_parser", command)
        self.assertIn("custom_tools", command)
        self.assertIn("--trust-remote-code", command)
        self.assertEqual(command[-5:], kwargs["server_args"])

    def test_invalid_nodes_and_topology_fail_closed(self):
        for nodes in (["n0", "n1", "n2"], ["n0", "n1", "n2", "n0"], ["n0", "n1", "n2", "n3\nbad"]):
            with self.subTest(nodes=nodes), self.assertRaises(ValueError):
                serving.node_layout(self.plan, nodes)
        for section, field, value in (("slurm", "nodes", 8), ("slurm", "gpus_per_node", True),
                                      ("topology", "replicas", 4), ("topology", "tp_size", 8),
                                      ("topology", "dist_port_base", 31241), ("topology", "http_port_base", 65535),
                                      ("slurm", "account", "other"), ("slurm", "partition", "p\n#SBATCH --nodes=8"),
                                      ("dispatch", "max_workers", False)):
            config = copy.deepcopy(self.config)
            config[section][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                serving.validate_config(config)

    def test_rejects_backend_override_secret_and_invalid_values(self):
        for values in (["--tp-size", "8"], ["--tp=8"], ["--port", "1"], ["--api-key", "not-a-key"],
                       ["--temperature", "0"], ["--random-seed"], ["--random-seed", "1", "--random-seed", "2"]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                serving.backend_args(values)
        for key, value in (("checkpoint", "relative"), ("sglang_bin", None), ("ep_size", 3),
                           ("context_length", True), ("mem_fraction_static", float("nan"))):
            with self.subTest(key=key), self.assertRaises(ValueError):
                serving.build_plan(self.config, **dict(self.arguments, **{key: value}))

    def test_default_and_write_only_never_execute_subprocess(self):
        with patch.object(serving.subprocess, "run") as run, patch.object(serving.subprocess, "Popen") as popen, \
             patch.object(serving.subprocess, "check_output") as check:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(serving.main(self.cli()), 0)
                with tempfile.TemporaryDirectory() as temporary:
                    directory = Path(temporary) / "prepared"
                    self.assertEqual(serving.main(self.cli() + ["--dry-run", "--output-dir", str(directory)]), 0)
                    self.assertEqual(set(p.name for p in directory.iterdir()), {"plan.json", "serve.sbatch", "serve_slurm.py"})
                    script = (directory / "serve.sbatch").read_text()
                    self.assertIn("#SBATCH --account=k2p\n", script)
                    self.assertIn("#SBATCH --nodes=4\n", script)
                    self.assertIn("#SBATCH --exclusive\n", script)
                    with self.assertRaises(FileExistsError):
                        serving.main(self.cli() + ["--output-dir", str(directory)])
            run.assert_not_called()
            popen.assert_not_called()
            check.assert_not_called()

    def test_submit_requires_explicit_private_scope_and_records_actual_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "submitted"
            for extra in (["--submit"], ["--submit", "--output-dir", str(directory)], ["--submit", "--dry-run"]):
                with self.assertRaises(ValueError):
                    serving.main(self.cli() + extra)
            with patch.object(serving.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()):
                run.return_value = serving.subprocess.CompletedProcess([], 0, "12345\n", "")
                self.assertEqual(serving.main(self.cli() + ["--submit", "--allow-private-unauthenticated", "--output-dir", str(directory)]), 0)
                self.assertEqual(run.call_args.args[0], ["sbatch", "--parsable", str(directory / "serve.sbatch")])
                self.assertEqual(json.loads((directory / "submission.json").read_text())["stdout"], "12345\n")

    def test_allocation_fails_without_slurm_before_starting_rank(self):
        with tempfile.TemporaryDirectory() as temporary:
            plan = dict(self.plan, launcher_sha256=hashlib.sha256(Path(serving.__file__).read_bytes()).hexdigest())
            path = Path(temporary) / "plan.json"
            serving.write_json(path, plan)
            with patch.dict(serving.os.environ, {}, clear=True), patch.object(serving.subprocess, "Popen") as popen, \
                 self.assertRaises(ValueError):
                serving.run_allocation(path)
            popen.assert_not_called()

    def test_rank_exit_stops_other_owned_ranks_and_preserves_no_drain_claim(self):
        class Process:
            def __init__(self, failed=False):
                self.returncode = 2 if failed else None
                self.terminated = False
            def poll(self):
                return self.returncode
            def terminate(self):
                self.terminated = True
                self.returncode = -15
            def wait(self, timeout):
                return self.returncode
        children = [Process(failed=index == 0) for index in range(4)]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.json"
            serving.write_json(path, dict(self.plan, launcher_sha256=hashlib.sha256(Path(serving.__file__).read_bytes()).hexdigest()))
            with patch.dict(serving.os.environ, {"SLURM_JOB_ID": "12345", "SLURM_JOB_ACCOUNT": "k2p", "SLURM_JOB_NODELIST": "n[0-3]"}), \
                 patch.object(serving.subprocess, "check_output", return_value="n0\nn1\nn2\nn3\n"), \
                 patch.object(serving.socket, "gethostbyname", side_effect=["10.0.0.1", "10.0.0.3"]), \
                 patch.object(serving.subprocess, "Popen", side_effect=children) as popen:
                self.assertEqual(serving.run_allocation(path), 1)
            self.assertEqual(popen.call_count, 4)
            self.assertTrue(all(child.terminated for child in children[1:]))
            deployment = json.loads((path.parent / "deployment.json").read_text())
            self.assertEqual(len(deployment["endpoints"]), 2)
            self.assertFalse(deployment["real_smoke_passed"])
            exit_receipt = json.loads((path.parent / "launcher_exit.json").read_text())
            self.assertFalse(exit_receipt["server_request_drain_verified"])
            self.assertEqual(exit_receipt["rank_exit_codes"], [2, -15, -15, -15])


if __name__ == "__main__":
    unittest.main()
