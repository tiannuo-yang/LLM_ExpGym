import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import run_poolact


REPO_ROOT = Path(__file__).resolve().parents[1]


class PoolActCliTest(unittest.TestCase):
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
                )
            )


if __name__ == "__main__":
    unittest.main()
