import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts import run_poolact


REPO_ROOT = Path(__file__).resolve().parents[1]


class PoolActCliTest(unittest.TestCase):
    def test_resolved_config_records_generation_options(self):
        for options, expected in (
            ([], {"max_tokens": None, "chat_template_kwargs": None}),
            (
                ["--max-tokens", "4096", "--chat-template-kwargs", '{"enable_thinking":false}'],
                {"max_tokens": 4096, "chat_template_kwargs": {"enable_thinking": False}},
            ),
        ):
            with self.subTest(options=options), mock.patch.dict(os.environ, {}, clear=True):
                with mock.patch.object(sys, "argv", ["run_poolact.py", *options]):
                    args = run_poolact.parse_args()
                config = run_poolact._resolved_config(args, time_budget=300.0)
                self.assertEqual(config["max_tokens"], expected["max_tokens"])
                self.assertEqual(
                    config["chat_template_kwargs"], expected["chat_template_kwargs"]
                )

    def test_generation_options_change_resolved_resume_config(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(sys, "argv", ["run_poolact.py"]):
                args = run_poolact.parse_args()
        baseline = run_poolact._resolved_config(args, time_budget=300.0)
        for name, value in (
            ("max_tokens", 4096),
            ("chat_template_kwargs", {"enable_thinking": False}),
            ("reasoning_effort", "high"),
            ("tool_protocol", "text"),
            ("max_protocol_retries", 0),
            ("tuning_final_policy", "submitted"),
            ("repeats", 2),
        ):
            with self.subTest(option=name), mock.patch.object(args, name, value):
                changed = run_poolact._resolved_config(args, time_budget=300.0)
                self.assertNotEqual(baseline, changed)

    def test_question_selector_matches_eval_model_syntax(self):
        self.assertEqual(run_poolact._parse_indices("0"), [0])
        self.assertEqual(run_poolact._parse_indices("0,2,7"), [0, 2, 7])
        self.assertEqual(run_poolact._parse_indices("2:5"), [2, 3, 4])
        self.assertEqual(run_poolact._parse_indices(":3"), [0, 1, 2])
        self.assertEqual(run_poolact._parse_indices("0,2,2"), [0, 2])

    def test_question_selector_rejects_empty_or_negative_ranges(self):
        for value in ("", "3:3", "-1", "3:1", "1:2:3"):
            with self.subTest(value=value):
                with self.assertRaises(Exception):
                    run_poolact._parse_indices(value)

    def test_agent_prompt_cache_keys_are_distinct_and_bounded(self):
        keys = {
            run_poolact._agent_cache_key("poolact/reader/" + "x" * 100, "poolact", i)
            for i in range(4)
        }
        self.assertEqual(len(keys), 4)
        self.assertTrue(all(key is not None and len(key) <= 64 for key in keys))

    def test_strategy_parser_rejects_unknown_value(self):
        with self.assertRaisesRegex(Exception, "unknown strategies"):
            run_poolact._split_strategies("poolact,other")

    def test_strategy_parser_deduplicates_without_spending_twice(self):
        self.assertEqual(run_poolact._split_strategies("naive,poolact,naive"), ["naive", "poolact"])

    def test_repeats_have_disjoint_seeds_cache_keys_and_paths(self):
        with mock.patch.object(sys, "argv", [
            "run_poolact.py", "--agents", "4", "--repeats", "3",
            "--output-dir", "runs/example", "--prompt-cache-key", "portable",
        ]):
            args = run_poolact.parse_args()
        seeds, keys = set(), set()
        for repeat_index in range(3):
            repeated = run_poolact._repeat_namespace(args, repeat_index)
            self.assertEqual(repeated.agents, 4)
            self.assertEqual(repeated.seed, 1206 + 4 * repeat_index)
            self.assertEqual(repeated.output_dir, Path(f"runs/example/repeat_{repeat_index}"))
            config = run_poolact._resolved_config(repeated, None)
            self.assertEqual(config["base_seed"], 1206)
            self.assertEqual(config["repeat_index"], repeat_index)
            for agent_id in range(4):
                agent = run_poolact._agent_namespace(repeated, "poolact", agent_id, None)
                seeds.add(agent.seed)
                keys.add(agent.prompt_cache_key)
                self.assertEqual(agent._api_dump_context["repeat_index"], repeat_index)
        self.assertEqual(seeds, set(range(1206, 1218)))
        self.assertEqual(len(keys), 12)
        self.assertEqual(args.seed, 1206)
        self.assertEqual(args.output_dir, Path("runs/example"))

    def test_one_repeat_preserves_historical_output_path(self):
        args = argparse.Namespace(seed=1206, agents=4, repeats=1, output_dir=Path("runs/old"))
        repeated = run_poolact._repeat_namespace(args, 0)
        self.assertEqual(repeated.output_dir, args.output_dir)
        self.assertEqual(repeated.seed, args.seed)

    def test_repeat_dry_run_counts_independent_agent_pools(self):
        with mock.patch.object(sys, "argv", [
            "run_poolact.py", "--backend", "fake", "--scenario", "restricted_search",
            "--questions", "0:3", "--agents", "4", "--repeats", "2",
            "--strategies", "naive,cached,poolact", "--dry-run",
        ]), mock.patch.object(sys, "stdout", io.StringIO()) as output:
            self.assertEqual(run_poolact.main(), 0)
        plan = json.loads(output.getvalue())
        self.assertEqual(plan["item_strategy_runs"], 18)
        self.assertEqual(plan["agent_traces"], 72)
        self.assertEqual([item["seed"] for item in plan["items"]], [1206] * 3 + [1210] * 3)
        self.assertEqual({item["agents"] for item in plan["items"]}, {4})
        self.assertEqual(len({item["output_dir"] for item in plan["items"]}), 6)

    def test_shared_state_completion_rejects_pending_claims(self):
        for value in (None, {"cache": {}}, {"graph": {"pending_claims": 0}}):
            self.assertTrue(run_poolact._shared_state_is_complete(value))
        for value in ([], {"graph": None}, {"graph": {"pending_claims": 1}}, {"pending_claims": 1}):
            self.assertFalse(run_poolact._shared_state_is_complete(value))

    def test_resume_rejects_malformed_json_shapes_without_crashing(self):
        agent = {"agent_id": 0, "answer": "{}", "answer_perf": 1.0, "score_check": {"ok": True}}
        valid = {
            "config": {"scenario": "tuning", "evaluation_identity": {"sha256": "fixed"}}, "strategy": "naive", "agents": 1,
            "implementation_sha256": {"source_tree": "fixed"},
            "agent_results": [agent], "aggregate": {"answer_perf": 1.0},
        }
        malformed = [[], None, 42, "unexpected root"]
        malformed += [{**valid, "agent_results": [{**agent, "score_check": value}]} for value in ([], 42, "ok")]
        malformed += [{**valid, "aggregate": value} for value in ([], 42, "unexpected aggregate")]
        for document in malformed:
            with self.subTest(document=document):
                def read(path, **kwargs):
                    return json.dumps(document if path.name == "result.json" else agent)

                with mock.patch.object(Path, "read_text", autospec=True, side_effect=read):
                    loaded = run_poolact._load_resumable_result(
                        Path("run/naive/result.json"), item_output_dir=Path("run"),
                        strategy="naive", config=valid["config"],
                        implementation=valid["implementation_sha256"], agents=1,
                        answer_evaluator=None,
                        score_tools={"evaluate_config": lambda payload: (1.0, 0.0)},
                    )
                self.assertIsNone(loaded)

    def test_repeated_batches_write_independent_results_and_resume_without_calls(self):
        evaluator = lambda answer: {"Alex Example": 0.25, "Blair Example": 0.75}[answer]

        def fake_strategy(args, strategy, api_key, time_budget, mode):
            answer = "Alex Example" if args.repeat_index == 0 else "Blair Example"
            agents = [
                {
                    "agent_id": agent_id, "seed": args.seed + agent_id,
                    "repeat_index": args.repeat_index, "answer": answer,
                    "answer_perf": evaluator(answer), "score_check": {"ok": True},
                    "termination_reason": "answer", "answer_source": "model",
                    "answer_score_source": "answer_evaluator",
                    "tuning_final_policy": args.tuning_final_policy,
                }
                for agent_id in range(args.agents)
            ]
            return {
                "strategy": strategy, "agents": args.agents, "shared_state": None,
                "agent_results": agents,
                "aggregate": run_poolact.aggregate_results(
                    args.scenario, agents, answer_evaluator=evaluator,
                ),
            }

        with tempfile.TemporaryDirectory() as directory:
            command = [
                "run_poolact.py", "--backend", "fake", "--scenario", "restricted_search",
                "--questions", "0:2", "--agents", "2", "--repeats", "2",
                "--strategies", "naive,cached,poolact", "--output-dir", directory,
            ]
            with mock.patch.object(run_poolact, "_implementation_manifest", return_value={"source_tree": "fixed"}), \
                 mock.patch.object(run_poolact, "evaluation_identity", return_value={"files": {}, "dependencies": {}, "sha256": "fixed-inputs"}), \
                 mock.patch.object(run_poolact, "_resolve_answer_evaluator", return_value=evaluator), \
                 mock.patch.object(run_poolact, "_run_strategy", side_effect=fake_strategy) as run, \
                 mock.patch.object(sys, "stdout", io.StringIO()), \
                 mock.patch.dict(os.environ, {}, clear=True):
                with mock.patch.object(sys, "argv", command):
                    self.assertEqual(run_poolact.main(), 0)
                self.assertEqual(run.call_count, 12)
                initial = {path: path.read_bytes() for path in Path(directory).rglob("result.json")}
                self.assertEqual(len(initial), 12)
                with mock.patch.object(sys, "argv", [*command, "--resume"]):
                    self.assertEqual(run_poolact.main(), 0)
                self.assertEqual(run.call_count, 12, "verified repeats must not launch new pools")
                self.assertEqual(initial, {path: path.read_bytes() for path in initial})
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["agent_traces"], 24)
            self.assertEqual(summary["item_strategy_runs"], 12)
            self.assertEqual(set(summary["repeats"]), {"0", "1"})
            self.assertEqual(summary["strategy_metrics"]["poolact"]["completed_items"], 4)
            self.assertEqual(summary["strategy_metrics"]["poolact"]["mean_answer_perf"], 0.5)
            for repeat_index, seeds in ((0, [1206, 1207]), (1, [1208, 1209])):
                result = json.loads((Path(directory) / f"repeat_{repeat_index}/item_0/poolact/result.json").read_text())
                self.assertEqual([agent["seed"] for agent in result["agent_results"]], seeds)
                self.assertEqual(result["config"]["agent_seeds"], seeds)
                self.assertEqual(result["agents"], 2)
                for field in ("termination_reason", "answer_source", "answer_score_source"):
                    self.assertIn(field, result["agent_results"][0])

    def test_single_item_repeats_keep_pool_aggregation_separate(self):
        def fake_strategy(args, strategy, api_key, time_budget, mode):
            agents = [
                {
                    "agent_id": agent_id, "seed": args.seed + agent_id,
                    "answer": "{}", "answer_perf": 0.2 + 0.4 * args.repeat_index,
                    "score_check": {"ok": True},
                    "tuning_final_policy": args.tuning_final_policy,
                }
                for agent_id in range(args.agents)
            ]
            return {
                "strategy": strategy, "agents": args.agents, "shared_state": None,
                "agent_results": agents,
                "aggregate": run_poolact.aggregate_results("tuning", agents),
            }

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(sys, "argv", [
                "run_poolact.py", "--backend", "fake", "--agents", "2",
                "--repeats", "2", "--output-dir", directory,
            ]), mock.patch.object(run_poolact, "_run_strategy", side_effect=fake_strategy), \
                 mock.patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(run_poolact.main(), 0)
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["agent_traces"], 4)
            self.assertAlmostEqual(summary["strategy_metrics"]["poolact"]["mean_answer_perf"], 0.4)
            for repeat_index in range(2):
                self.assertTrue((Path(directory) / f"repeat_{repeat_index}/poolact/result.json").is_file())
                self.assertFalse((Path(directory) / f"repeat_{repeat_index}/item_0").exists())

    def test_strategy_preserves_loop_metadata_and_passes_protocol_options(self):
        with mock.patch.object(sys, "argv", [
            "run_poolact.py", "--backend", "fake", "--agents", "1",
            "--tool-protocol", "text", "--max-protocol-retries", "0",
            "--tuning-final-policy", "submitted",
        ]):
            args = run_poolact.parse_args()
        expected = {
            "answer": "{}", "answer_perf": 0.75,
            "termination_reason": "answer", "answer_source": "model",
            "answer_score_source": "offline_final_answer",
            "tuning_final_policy": "submitted", "protocol_repairs": 0,
        }
        with mock.patch.object(run_poolact, "run_react_loop", return_value=dict(expected)) as loop, \
             mock.patch.object(run_poolact, "_score_result", return_value={"ok": True}):
            result = run_poolact._run_strategy(args, "naive", None, None, "no_budget")
        agent = result["agent_results"][0]
        for key, value in expected.items():
            self.assertEqual(agent[key], value)
        self.assertEqual(loop.call_args.kwargs["tool_protocol"], "text")
        self.assertEqual(loop.call_args.kwargs["max_protocol_retries"], 0)
        self.assertEqual(loop.call_args.kwargs["tuning_final_policy"], "submitted")

    def test_dry_run_requires_no_api_key(self):
        environment = dict(os.environ)
        for name in (
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "SUB2API_API_KEY",
        ):
            environment.pop(name, None)
        process = subprocess.run(
            [
                sys.executable,
                "scripts/run_poolact.py",
                "--backend",
                "openrouter",
                "--api-key-file",
                "/definitely/missing/poolact.key",
                "--agents",
                "2",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
            env=environment,
        )
        config = json.loads(process.stdout)
        self.assertEqual(config["strategies"], ["poolact"])
        self.assertEqual(config["agents"], 2)

    def test_batch_dry_run_lists_every_question_without_loading_data(self):
        process = subprocess.run(
            [
                sys.executable,
                "scripts/run_poolact.py",
                "--backend",
                "fake",
                "--scenario",
                "restricted_search",
                "--questions",
                "0:3",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        preview = json.loads(process.stdout)
        self.assertTrue(preview["batch"])
        self.assertEqual(preview["question_indices"], [0, 1, 2])
        self.assertEqual(
            [item["question_index"] for item in preview["items"]],
            [0, 1, 2],
        )

    def test_batch_summary_averages_only_numeric_scores(self):
        items = {
            "0": {"poolact": {"answer_perf": 0.5}},
            "1": {"poolact": {"answer_perf": 1.0}},
            "2": {"poolact": {"answer_perf": None}},
        }
        metrics = run_poolact._batch_strategy_metrics(items, ["poolact"])
        self.assertEqual(metrics["poolact"]["completed_items"], 3)
        self.assertEqual(metrics["poolact"]["scored_items"], 2)
        self.assertEqual(metrics["poolact"]["mean_answer_perf"], 0.75)

    def test_fake_end_to_end_writes_reproducible_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_poolact.py",
                    "--backend",
                    "fake",
                    "--agents",
                    "2",
                    "--strategies",
                    "poolact",
                    "--max-steps",
                    "3",
                    "--output-dir",
                    directory,
                ],
                cwd=REPO_ROOT,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("POOLACT RESULT", process.stdout)
            result = json.loads(
                (Path(directory) / "poolact" / "result.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(result["agent_results"]), 2)
            self.assertEqual(result["shared_state"]["graph"]["pending_claims"], 0)
            self.assertEqual(
                set(result["implementation_sha256"]),
                {"source_tree"},
            )
            self.assertGreater(result["shared_state"]["graph"]["end_nodes"], 0)
            self.assertTrue(
                all(
                    agent["score_check"]["ok"]
                    for agent in result["agent_results"]
                )
            )
            result_path = Path(directory) / "poolact" / "result.json"
            loaded = run_poolact._load_resumable_result(
                result_path,
                item_output_dir=Path(directory),
                strategy="poolact",
                config=result["config"],
                implementation=result["implementation_sha256"],
                agents=2,
                answer_evaluator=None,
                score_tools=run_poolact._resolve_tools(
                    run_poolact._SCENARIOS["tuning"], argparse.Namespace(tuning_task="neural_network_training"),
                ),
            )
            self.assertIsNotNone(loaded)

            result["aggregate"]["answer_perf"] += 0.1
            result_path.write_text(json.dumps(result), encoding="utf-8")
            self.assertIsNone(
                run_poolact._load_resumable_result(
                    result_path,
                    item_output_dir=Path(directory),
                    strategy="poolact",
                    config=result["config"],
                    implementation=result["implementation_sha256"],
                    agents=2,
                    answer_evaluator=None,
                    score_tools=run_poolact._resolve_tools(
                        run_poolact._SCENARIOS["tuning"], argparse.Namespace(tuning_task="neural_network_training"),
                    ),
                )
            )

    def test_resume_independently_recomputes_each_saved_tuning_score(self):
        agent = {"agent_id": 0, "answer": "{}", "answer_perf": 0.9, "score_check": {"ok": True}}
        config = {"scenario": "tuning", "evaluation_identity": {"sha256": "fixed"}}
        implementation = {"source_tree": "fixed"}
        result = {
            "config": config, "implementation_sha256": implementation,
            "strategy": "naive", "agents": 1, "agent_results": [agent],
            "aggregate": run_poolact.aggregate_results("tuning", [agent]),
        }

        def read(path, **kwargs):
            return json.dumps(result if path.name == "result.json" else agent)

        for actual_score, expected_accepted in ((0.9, True), (0.1, False)):
            with self.subTest(actual_score=actual_score):
                scorer = mock.Mock(return_value=(actual_score, 1.0))
                with mock.patch.object(Path, "read_text", autospec=True, side_effect=read):
                    restored = run_poolact._load_resumable_result(
                        Path("run/naive/result.json"), item_output_dir=Path("run"),
                        strategy="naive", config=config, implementation=implementation,
                        agents=1, answer_evaluator=None, score_tools={"evaluate_config": scorer},
                    )
                self.assertEqual(restored is not None, expected_accepted)
                scorer.assert_called_once_with("{}")

    def test_resume_rejects_changed_input_fingerprint_before_scoring(self):
        config = {"scenario": "tuning", "evaluation_identity": {"sha256": "new"}}
        result = {"config": {**config, "evaluation_identity": {"sha256": "old"}}}
        scorer = mock.Mock()
        with mock.patch.object(Path, "read_text", return_value=json.dumps(result)):
            restored = run_poolact._load_resumable_result(
                Path("result.json"), item_output_dir=Path("run"), strategy="naive",
                config=config, implementation={}, agents=1, answer_evaluator=None,
                score_tools={"evaluate_config": scorer},
            )
        self.assertIsNone(restored)
        scorer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
