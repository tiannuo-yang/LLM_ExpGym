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

    def test_schema1_rendered_defaults_are_byte_compatible(self):
        # Captured before adding pipeline support: no pp_size=1 metadata/flag
        # or other silent default change. Launcher-source hashes must change.
        layout = serving.node_layout(self.plan, ["n0", "n1", "n2", "n3"])
        commands = [serving.server_command(self.plan, replica, rank, replica["nodes"][0])
                    for replica in layout for rank in range(2)]
        values = {
            "config": serving.DEFAULT_CONFIG.read_bytes(),
            "plan": json.dumps(self.plan, indent=2, sort_keys=True, allow_nan=False).encode(),
            "layout": json.dumps(layout, indent=2, sort_keys=True, allow_nan=False).encode(),
            "commands": json.dumps(commands, indent=2, sort_keys=True, allow_nan=False).encode(),
            "batch": serving.batch_script(self.plan, Path("/shared/plan"),
                                          Path("/shared/plan/serve_slurm.py"), "/controller/bin/python").encode(),
        }
        expected = {
            "config": "f6eccb4db5fe81572487bad118664348a42b17271b0d8ff68435e5613018f875",
            "plan": "2c3a9aadf09d2050803780e63b452e9c0a6cb39a9ef96ea9f985b15386f11352",
            "layout": "e37db42299908f92473927cd4e5295e55d1db432bb920d4fc6605704b2e77d6e",
            "commands": "53a35118f93f43a045183a4a315d0169ca00503ab7934df2a943569ec454332c",
            "batch": "a377a768a153d92073bb41a89812a0edeaf441c9ba394357caca8e3ba5c09ff8",
        }
        self.assertEqual({key: hashlib.sha256(value).hexdigest() for key, value in values.items()}, expected)

    def pipeline_config(self):
        return json.loads((serving.DEFAULT_CONFIG.parent / "slurm_tp8_pp4.json").read_text())

    def four_replica_config(self):
        return json.loads((serving.DEFAULT_CONFIG.parent / "slurm_tp8_four_replicas.json").read_text())

    def test_schema2_rendered_defaults_are_byte_compatible(self):
        # Captured before adding four single-node replicas. Existing profile
        # outputs are frozen, apart from the separately recorded launcher hash.
        config = self.pipeline_config()
        plan = serving.build_plan(config, **self.arguments)
        layout = serving.node_layout(plan, ["n0", "n1", "n2", "n3"])
        commands = [serving.server_command(plan, replica, rank, replica["nodes"][0])
                    for replica in layout for rank in range(4)]
        values = {
            "config": (serving.DEFAULT_CONFIG.parent / "slurm_tp8_pp4.json").read_bytes(),
            "plan": json.dumps(plan, indent=2, sort_keys=True, allow_nan=False).encode(),
            "layout": json.dumps(layout, indent=2, sort_keys=True, allow_nan=False).encode(),
            "commands": json.dumps(commands, indent=2, sort_keys=True, allow_nan=False).encode(),
            "batch": serving.batch_script(plan, Path("/shared/plan"),
                                          Path("/shared/plan/serve_slurm.py"), "/controller/bin/python").encode(),
        }
        expected = {
            "config": "b1acd7bd766d60c800db5bdb5c7fa6ff0af3970f88959dab2fab05ae569d5eee",
            "plan": "80ac948ecf1e2ee49c7a6bd8e2ff1a86a9c6fed60e026e15d47f2dc952816653",
            "layout": "b6d0072232777cb605f14ddfe15dcfa82961dab909535c15a41a99a5eeb1984e",
            "commands": "ee6dea2c60afd5f0b07343a3e1568b3a5e8eb6691945990d7edb999da5b5c78a",
            "batch": "a377a768a153d92073bb41a89812a0edeaf441c9ba394357caca8e3ba5c09ff8",
        }
        self.assertEqual({key: hashlib.sha256(value).hexdigest() for key, value in values.items()}, expected)

    def test_four_tp8_replicas_have_independent_single_node_endpoints(self):
        for ep_size in (1, 2, 4, 8):
            with self.subTest(ep_size=ep_size):
                plan = serving.build_plan(self.four_replica_config(), **dict(self.arguments, model="model-spruce", ep_size=ep_size))
                layout = serving.node_layout(plan, ["n0", "n1", "n2", "n3"])
                self.assertEqual(plan["schema_version"], 3)
                self.assertEqual(layout, [{"replica": index, "nodes": ["n" + str(index)],
                                           "tp_size": 8, "pp_size": 1, "http_port": 32240 + index,
                                           "dist_port": 52240 + index,
                                           "base_url": "http://n%d:%d/v1" % (index, 32240 + index)}
                                          for index in range(4)])
                for index, replica in enumerate(layout):
                    command = serving.server_command(plan, replica, 0, "10.0.0." + str(index + 1))
                    for flag, value in (("--tp-size", "8"), ("--pp-size", "1"), ("--nnodes", "1"),
                                        ("--node-rank", "0"), ("--dist-init-addr", "10.0.0.%d:%d" % (index + 1, 52240 + index)),
                                        ("--port", str(32240 + index)), ("--ep-size", str(ep_size)),
                                        ("--served-model-name", "model-spruce")):
                        self.assertEqual(command.count(flag), 1)
                        self.assertEqual(command[command.index(flag) + 1], value)
                    self.assertNotIn("--temperature", command)
                    self.assertNotIn("--max-tokens", command)
                self.assertEqual(plan["server_args"], [])
                self.assertFalse(plan["real_smoke_passed"])

    def test_four_replica_invalid_topology_ep_and_rank_fail_closed(self):
        invalid = []
        config = self.four_replica_config()
        del config["topology"]["pp_size"]
        invalid.append(config)
        config = self.four_replica_config()
        config["topology"].update(replicas=2, nodes_per_replica=2, pp_size=2)
        invalid.append(config)
        for section, field, value in (("topology", "pp_size", True), ("topology", "pp_size", 0),
                                      ("topology", "pp_size", 2), ("topology", "tp_size", 16),
                                      ("topology", "nodes_per_replica", 2), ("topology", "replicas", 2),
                                      ("slurm", "nodes", 8), ("slurm", "gpus_per_node", 4)):
            config = self.four_replica_config()
            config[section][field] = value
            invalid.append(config)
        for config in invalid:
            with self.subTest(config=config), self.assertRaises(ValueError):
                serving.validate_config(config)
        # A numerically consistent but unreviewed profile, or a profile relabelled
        # as another schema, must not bypass the explicit shape allowlist.
        for profile in (self.config, self.pipeline_config(), self.four_replica_config()):
            for schema in (1, 2, 3, 99):
                if schema == profile["schema_version"]:
                    continue
                config = copy.deepcopy(profile)
                config["schema_version"] = schema
                with self.subTest(profile=profile["schema_version"], schema=schema), self.assertRaises(ValueError):
                    serving.validate_config(config)
        for ep_size in (True, 0, 3, 16, 32):
            with self.subTest(ep_size=ep_size), self.assertRaises(ValueError):
                serving.build_plan(self.four_replica_config(), **dict(self.arguments, ep_size=ep_size))
        plan = serving.build_plan(self.four_replica_config(), **self.arguments)
        replica = serving.node_layout(plan, ["n0", "n1", "n2", "n3"])[0]
        for rank in (-1, 1, 4, True, "0"):
            with self.subTest(rank=rank), self.assertRaises(ValueError):
                serving.server_command(plan, replica, rank, "10.0.0.1")
        for index in (-1, 4, True, "0"):
            with self.subTest(replica=index), self.assertRaises(ValueError):
                serving.server_command(plan, dict(replica, replica=index), 0, "10.0.0.1")

    def test_four_replica_port_ranges_and_configurable_bases(self):
        config = self.four_replica_config()
        config["topology"].update(http_port_base=65532, dist_port_base=1024)
        plan = serving.build_plan(config, **self.arguments)
        layout = serving.node_layout(plan, ["n0", "n1", "n2", "n3"])
        self.assertEqual([item["http_port"] for item in layout], [65532, 65533, 65534, 65535])
        self.assertEqual([item["dist_port"] for item in layout], [1024, 1025, 1026, 1027])
        for http_port, dist_port in ((1023, 52240), (32240, 65533), (65533, 52240),
                                    (32240, 32240), (32240, 32243), (32240, 32237)):
            config = self.four_replica_config()
            config["topology"].update(http_port_base=http_port, dist_port_base=dist_port)
            with self.subTest(http_port=http_port, dist_port=dist_port), self.assertRaises(ValueError):
                serving.validate_config(config)

    def test_pipeline_is_one_four_node_replica_with_one_endpoint(self):
        for ep_size in (1, 2, 4, 8):
            with self.subTest(ep_size=ep_size):
                plan = serving.build_plan(self.pipeline_config(), **dict(self.arguments, model="model-cedar", ep_size=ep_size))
                layout = serving.node_layout(plan, ["n0", "n1", "n2", "n3"])
                self.assertEqual(plan["schema_version"], 2)
                self.assertEqual(layout, [{"replica": 0, "nodes": ["n0", "n1", "n2", "n3"],
                                          "tp_size": 8, "pp_size": 4, "http_port": 31240,
                                          "dist_port": 51240, "base_url": "http://n0:31240/v1"}])
                commands = [serving.server_command(plan, layout[0], rank, "10.0.0.1") for rank in range(4)]
                for rank, command in enumerate(commands):
                    for flag, value in (("--tp-size", "8"), ("--pp-size", "4"), ("--nnodes", "4"),
                                        ("--node-rank", str(rank)), ("--dist-init-addr", "10.0.0.1:51240"),
                                        ("--port", "31240"), ("--ep-size", str(ep_size)), ("--served-model-name", "model-cedar")):
                        self.assertEqual(command.count(flag), 1)
                        self.assertEqual(command[command.index(flag) + 1], value)
                    self.assertNotIn("--temperature", command)
                    self.assertNotIn("--max-tokens", command)
                self.assertEqual(plan["server_args"], [])
                self.assertFalse(plan["real_smoke_passed"])

    def test_pipeline_invalid_topology_schema_ep_and_rank_fail_closed(self):
        invalid = []
        config = self.pipeline_config()
        del config["topology"]["pp_size"]
        invalid.append(config)
        config = copy.deepcopy(self.config)
        config["topology"]["pp_size"] = 1
        invalid.append(config)
        for section, field, value in (("topology", "pp_size", True), ("topology", "pp_size", 0),
                                      ("topology", "pp_size", 2), ("topology", "tp_size", 16),
                                      ("topology", "nodes_per_replica", 2), ("topology", "replicas", 2),
                                      ("slurm", "nodes", 8), ("slurm", "gpus_per_node", 4)):
            config = self.pipeline_config()
            config[section][field] = value
            invalid.append(config)
        for config in invalid:
            with self.subTest(config=config), self.assertRaises(ValueError):
                serving.validate_config(config)
        for ep_size in (True, 0, 3, 16, 32):
            with self.subTest(ep_size=ep_size), self.assertRaises(ValueError):
                serving.build_plan(self.pipeline_config(), **dict(self.arguments, ep_size=ep_size))
        plan = serving.build_plan(self.pipeline_config(), **self.arguments)
        replica = serving.node_layout(plan, ["n0", "n1", "n2", "n3"])[0]
        for rank in (-1, 4, True, "0"):
            with self.subTest(rank=rank), self.assertRaises(ValueError):
                serving.server_command(plan, replica, rank, "10.0.0.1")
        for index in (-1, 1, True, "0"):
            with self.subTest(replica=index), self.assertRaises(ValueError):
                serving.server_command(plan, dict(replica, replica=index), 0, "10.0.0.1")

    def test_pipeline_ports_use_actual_replica_count(self):
        config = self.pipeline_config()
        config["topology"].update(http_port_base=65535, dist_port_base=1024)
        plan = serving.build_plan(config, **self.arguments)
        layout = serving.node_layout(plan, ["n0", "n1", "n2", "n3"])
        self.assertEqual(layout[0]["base_url"], "http://n0:65535/v1")
        for http_port, dist_port in ((1023, 51240), (31240, 65536), (31240, 31240)):
            config = self.pipeline_config()
            config["topology"].update(http_port_base=http_port, dist_port_base=dist_port)
            with self.subTest(http_port=http_port, dist_port=dist_port), self.assertRaises(ValueError):
                serving.validate_config(config)

    def test_reviewed_pipeline_backend_values_are_explicit_only(self):
        extra = ["--dist-timeout", "1800", "--linear-attn-prefill-backend", "flashinfer",
                 "--linear-attn-decode-backend", "flashinfer", "--mamba-full-memory-ratio", "0.95",
                 "--mamba-ssm-dtype", "bfloat16", "--max-prefill-tokens", "8192", "--page-size", "64"]
        plan = serving.build_plan(self.pipeline_config(), **dict(self.arguments, server_args=extra))
        replica = serving.node_layout(plan, ["n0", "n1", "n2", "n3"])[0]
        for rank in range(4):
            command = serving.server_command(plan, replica, rank, "10.0.0.1")
            self.assertEqual(command[-len(extra):], extra)
        default = serving.server_command(self.plan, serving.node_layout(self.plan, ["n0", "n1", "n2", "n3"])[0], 0, "10.0.0.1")
        for flag in extra[::2]:
            self.assertNotIn(flag, default)
            for malformed in ([flag], [flag, "--pp-size"], [flag, "x", flag, "y"]):
                with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                    serving.backend_args(malformed)

    def test_pipeline_and_security_overrides_cannot_enter_server_args(self):
        for config in (self.pipeline_config(), self.four_replica_config()):
            for flag in ("--pp", "--pp-size", "--pipeline-parallel-size", "--tp", "--tp-size", "--ep-size",
                         "--nnodes", "--node-rank", "--dist-init-addr", "--host", "--port", "--api-key",
                         "--admin-api-key", "--config", "--config-file", "--model-path", "--max-running-requests"):
                for values in ([flag, "placeholder"], [flag + "=placeholder"]):
                    with self.subTest(schema=config["schema_version"], values=values), self.assertRaises(ValueError):
                        serving.build_plan(config, **dict(self.arguments, server_args=values))
            for value in ({}, "", 0, False):
                with self.subTest(schema=config["schema_version"], value=value), self.assertRaises(ValueError):
                    serving.build_plan(config, **dict(self.arguments, server_args=value))

    def test_pipeline_dry_run_never_executes_subprocess(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()), \
             patch.object(serving.subprocess, "run") as run, patch.object(serving.subprocess, "Popen") as popen, \
             patch.object(serving.subprocess, "check_output") as check:
            config_path = serving.DEFAULT_CONFIG.parent / "slurm_tp8_pp4.json"
            directory = Path(temporary) / "pipeline"
            self.assertEqual(serving.main(self.cli() + ["--config", str(config_path), "--dry-run", "--output-dir", str(directory)]), 0)
            plan = json.loads((directory / "plan.json").read_text())
            self.assertEqual(plan["config"], self.pipeline_config())
            self.assertEqual(plan["schema_version"], 2)
            self.assertFalse((directory / "submission.json").exists())
            self.assertIn("#SBATCH --nodes=4\n", (directory / "serve.sbatch").read_text())
            self.assertIn("#SBATCH --gres=gpu:8\n", (directory / "serve.sbatch").read_text())
            with self.assertRaises(FileExistsError):
                serving.main(self.cli() + ["--config", str(config_path), "--output-dir", str(directory)])
            run.assert_not_called()
            popen.assert_not_called()
            check.assert_not_called()

    def test_four_replica_dry_run_never_executes_subprocess(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()), \
             patch.object(serving.subprocess, "run") as run, patch.object(serving.subprocess, "Popen") as popen, \
             patch.object(serving.subprocess, "check_output") as check:
            config_path = serving.DEFAULT_CONFIG.parent / "slurm_tp8_four_replicas.json"
            directory = Path(temporary) / "four-replicas"
            self.assertEqual(serving.main(self.cli() + ["--config", str(config_path), "--dry-run", "--output-dir", str(directory)]), 0)
            plan = json.loads((directory / "plan.json").read_text())
            self.assertEqual(plan["config"], self.four_replica_config())
            self.assertEqual(plan["schema_version"], 3)
            serving.validate_plan(plan)
            self.assertFalse((directory / "submission.json").exists())
            self.assertIn("#SBATCH --nodes=4\n", (directory / "serve.sbatch").read_text())
            self.assertIn("#SBATCH --gres=gpu:8\n", (directory / "serve.sbatch").read_text())
            with self.assertRaises(FileExistsError):
                serving.main(self.cli() + ["--config", str(config_path), "--output-dir", str(directory)])
            run.assert_not_called()
            popen.assert_not_called()
            check.assert_not_called()

    def test_saved_plan_revalidates_before_any_slurm_or_rank_command(self):
        plans = [self.plan, serving.build_plan(self.pipeline_config(), **self.arguments),
                 serving.build_plan(self.four_replica_config(), **self.arguments)]
        for original in plans:
            cases = [("server_args", ["--pp-size", "4"]), ("server_args", ["--api-key", "placeholder"]),
                     ("server_args", {}), ("context_length", True), ("ep_size", 32), ("schema_version", 99),
                     ("real_smoke_passed", True), ("trust_remote_code", "yes"), ("api_key", "placeholder")]
            for field, value in cases:
                with self.subTest(schema=original["schema_version"], field=field, value=value), tempfile.TemporaryDirectory() as temporary:
                    plan = copy.deepcopy(original)
                    plan[field] = value
                    plan["launcher_sha256"] = hashlib.sha256(Path(serving.__file__).read_bytes()).hexdigest()
                    path = Path(temporary) / "plan.json"
                    serving.write_json(path, plan)
                    with patch.dict(serving.os.environ, {"SLURM_JOB_ID": "12345", "SLURM_JOB_ACCOUNT": "k2p", "SLURM_JOB_NODELIST": "n[0-3]"}), \
                         patch.object(serving.subprocess, "check_output") as check, \
                         patch.object(serving.subprocess, "Popen") as popen, \
                         patch.object(serving.subprocess, "run") as run, self.assertRaises(ValueError):
                        serving.run_allocation(path)
                    check.assert_not_called()
                    popen.assert_not_called()
                    run.assert_not_called()
                    self.assertFalse((path.parent / "deployment.json").exists())

    def test_four_replica_saved_config_tamper_is_rejected_before_allocation(self):
        mutations = [
            ("topology", {"http_port_base": 65533}),
            ("topology", {"dist_port_base": 32243}),
            ("topology", {"replicas": 2, "nodes_per_replica": 2, "pp_size": 2}),
            ("slurm", {"account": "other"}),
            ("slurm", {"nodes": 8}),
        ]
        for section, fields in mutations:
            with self.subTest(section=section, fields=fields), tempfile.TemporaryDirectory() as temporary:
                plan = serving.build_plan(self.four_replica_config(), **self.arguments)
                plan["config"][section].update(fields)
                plan["launcher_sha256"] = hashlib.sha256(Path(serving.__file__).read_bytes()).hexdigest()
                path = Path(temporary) / "plan.json"
                serving.write_json(path, plan)
                with patch.dict(serving.os.environ, {"SLURM_JOB_ID": "67890", "SLURM_JOB_ACCOUNT": "k2p", "SLURM_JOB_NODELIST": "n[0-3]"}), \
                     patch.object(serving.subprocess, "check_output") as check, \
                     patch.object(serving.subprocess, "Popen") as popen, \
                     patch.object(serving.subprocess, "run") as run, self.assertRaises(ValueError):
                    serving.run_allocation(path)
                check.assert_not_called()
                popen.assert_not_called()
                run.assert_not_called()
                self.assertFalse((path.parent / "deployment.json").exists())

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

    def test_pipeline_rank_failure_cleans_owned_four_ranks_on_one_endpoint(self):
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
        children = [Process(failed=index == 2) for index in range(4)]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.json"
            plan = serving.build_plan(self.pipeline_config(), **dict(self.arguments, model="model-cedar"))
            serving.write_json(path, dict(plan, launcher_sha256=hashlib.sha256(Path(serving.__file__).read_bytes()).hexdigest()))
            with patch.dict(serving.os.environ, {"SLURM_JOB_ID": "12345", "SLURM_JOB_ACCOUNT": "k2p", "SLURM_JOB_NODELIST": "n[0-3]"}), \
                 patch.object(serving.subprocess, "check_output", return_value="n0\nn1\nn2\nn3\n"), \
                 patch.object(serving.socket, "gethostbyname", return_value="10.0.0.1") as dns, \
                 patch.object(serving.subprocess, "Popen", side_effect=children) as popen, \
                 patch.object(serving.subprocess, "run") as run:
                self.assertEqual(serving.run_allocation(path), 1)
            run.assert_not_called()
            dns.assert_called_once_with("n0")
            self.assertEqual(popen.call_count, 4)
            self.assertTrue(all(children[index].terminated for index in (0, 1, 3)))
            self.assertFalse(children[2].terminated)
            deployment = json.loads((path.parent / "deployment.json").read_text())
            self.assertEqual(deployment["schema_version"], 2)
            self.assertEqual(deployment["endpoints"], ["http://n0:31240/v1"])
            self.assertEqual([(record["replica"], record["rank"], record["node"]) for record in deployment["rank_commands"]],
                             [(0, rank, "n" + str(rank)) for rank in range(4)])
            cache_dirs = set()
            for rank, call in enumerate(popen.call_args_list):
                command = call.args[0]
                for flag, value in (("--pp-size", "4"), ("--nnodes", "4"), ("--node-rank", str(rank)),
                                    ("--dist-init-addr", "10.0.0.1:51240")):
                    self.assertEqual(command[command.index(flag) + 1], value)
                self.assertIn("--nodelist=n" + str(rank), command)
                self.assertIn("--gres=gpu:8", command)
                cache_dirs.add(call.kwargs["env"]["TRITON_CACHE_DIR"])
            self.assertEqual(len(cache_dirs), 4)
            self.assertFalse(deployment["real_smoke_passed"])
            exit_receipt = json.loads((path.parent / "launcher_exit.json").read_text())
            self.assertEqual(exit_receipt["rank_exit_codes"], [-15, -15, 2, -15])
            self.assertFalse(exit_receipt["server_request_drain_verified"])

    def test_four_replica_failure_cleans_owned_ranks_and_keeps_namespaces_separate(self):
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
        children = [Process(failed=index == 1) for index in range(4)]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.json"
            plan = serving.build_plan(self.four_replica_config(), **dict(self.arguments, model="model-spruce"))
            serving.write_json(path, dict(plan, launcher_sha256=hashlib.sha256(Path(serving.__file__).read_bytes()).hexdigest()))
            with patch.dict(serving.os.environ, {"SLURM_JOB_ID": "67890", "SLURM_JOB_ACCOUNT": "k2p", "SLURM_JOB_NODELIST": "n[0-3]"}), \
                 patch.object(serving.subprocess, "check_output", return_value="n0\nn1\nn2\nn3\n"), \
                 patch.object(serving.socket, "gethostbyname", side_effect=["10.0.0." + str(i + 1) for i in range(4)]) as dns, \
                 patch.object(serving.subprocess, "Popen", side_effect=children) as popen, \
                 patch.object(serving.subprocess, "run") as run:
                self.assertEqual(serving.run_allocation(path), 1)
            run.assert_not_called()
            self.assertEqual([call.args[0] for call in dns.call_args_list], ["n0", "n1", "n2", "n3"])
            self.assertEqual(popen.call_count, 4)
            self.assertTrue(all(children[index].terminated for index in (0, 2, 3)))
            self.assertFalse(children[1].terminated)
            deployment = json.loads((path.parent / "deployment.json").read_text())
            self.assertEqual(deployment["schema_version"], 3)
            self.assertEqual(deployment["endpoints"], ["http://n%d:%d/v1" % (index, 32240 + index) for index in range(4)])
            self.assertEqual([(record["replica"], record["rank"], record["node"]) for record in deployment["rank_commands"]],
                             [(index, 0, "n" + str(index)) for index in range(4)])
            for index, call in enumerate(popen.call_args_list):
                command = call.args[0]
                for flag, value in (("--tp-size", "8"), ("--pp-size", "1"), ("--nnodes", "1"), ("--node-rank", "0"),
                                    ("--dist-init-addr", "10.0.0.%d:%d" % (index + 1, 52240 + index)),
                                    ("--port", str(32240 + index)), ("--ep-size", "1")):
                    self.assertEqual(command[command.index(flag) + 1], value)
                self.assertIn("--nodelist=n" + str(index), command)
                self.assertIn("--gres=gpu:8", command)
                tag = "expgym_67890_replica%d_rank0" % index
                self.assertIn(tag, command)
                self.assertEqual(call.kwargs["env"]["TRITON_CACHE_DIR"], "/tmp/" + tag + "_triton")
                self.assertEqual(call.kwargs["env"]["HF_MODULES_CACHE"], "/tmp/" + tag + "_hf")
                self.assertEqual(call.kwargs["env"]["TVM_FFI_CACHE_DIR"], "/tmp/" + tag + "_tvm")
                self.assertTrue((path.parent / ("replica%d-rank0.log" % index)).is_file())
            self.assertFalse(deployment["real_smoke_passed"])
            exit_receipt = json.loads((path.parent / "launcher_exit.json").read_text())
            self.assertEqual(exit_receipt["rank_exit_codes"], [-15, 2, -15, -15])
            self.assertFalse(exit_receipt["server_request_drain_verified"])


if __name__ == "__main__":
    unittest.main()
