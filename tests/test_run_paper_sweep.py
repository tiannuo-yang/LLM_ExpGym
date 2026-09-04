import argparse
from dataclasses import replace
import re
import unittest
from pathlib import Path

from scripts import run_paper_sweep


def _args(**overrides):
    defaults = dict(
        output_dir=Path("budget_sweep_results/e2e"),
        models="openai/gpt-4.1-nano",
        model_alias=[],
        scenarios="tuning",
        cost_regimes="cost_tight",
        tuning_tasks="neural_network_training",
        search_indices="0",
        search_data_source="phantom_seed1",
        audit_indices="0",
        cc_split="cc-large",
        audit_orders=Path("configs/audit_hypothesis_orders.json"),
        tuning_reps=1,
        search_reps=1,
        audit_reps=1,
        seed=1206,
        max_steps=10,
        max_evals=30,
        temperature_tuning=0.7,
        temperature_eval=0.0,
        api_key_file=Path("../openrouter.key"),
        backend="openrouter",
        base_url=None,
        prompt_cache_key=None,
        prompt_cache_scope="job",
        trace_format="v2",
        openrouter_referer=None,
        openrouter_title="ExpGym sweep",
        dry_run=True,
        resume=False,
        skip_preflight=False,
        limit=None,
        shuffle=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class PaperSweepMatrixTest(unittest.TestCase):
    def test_default_matrix_is_one_low_friction_smoke_job(self):
        jobs = run_paper_sweep._build_jobs(_args())
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job.model_id, "openai/gpt-4.1-nano")
        self.assertEqual(job.scenario, "tuning")
        self.assertEqual(job.cost_regime, "cost_tight")
        self.assertEqual(job.tuning_task, "neural_network_training")

    def test_explicit_paper_matrix_matches_trace_count(self):
        jobs = run_paper_sweep._build_jobs(
            _args(
                models=",".join(run_paper_sweep.PAPER_MODELS.keys()),
                scenarios=",".join(run_paper_sweep.SCENARIOS),
                cost_regimes=",".join(run_paper_sweep.PAPER_COST_REGIMES),
                tuning_tasks="all-hpobench",
                search_indices="0:35",
                audit_indices="0:13",
                tuning_reps=3,
                audit_reps=3,
                max_steps=30,
                max_evals=999999,
            )
        )
        self.assertEqual(len(jobs), 1818)
        counts = {}
        for job in jobs:
            counts[job.scenario] = counts.get(job.scenario, 0) + 1
        self.assertEqual(counts["tuning"], 486)
        self.assertEqual(counts["restricted_search"], 630)
        self.assertEqual(counts["evidence_audit"], 702)

    def test_small_selector_builds_one_job(self):
        jobs = run_paper_sweep._build_jobs(
            _args(
                models="openai/gpt-4.1-nano",
                scenarios="tuning",
                tuning_tasks="neural_network_training",
                cost_regimes="cost_tight",
                tuning_reps=1,
                limit=1,
            )
        )
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job.model_id, "openai/gpt-4.1-nano")
        self.assertEqual(job.model_alias, "openai_gpt-4.1-nano")
        self.assertEqual(job.scenario, "tuning")
        self.assertEqual(job.tuning_task, "neural_network_training")

    def test_prompt_cache_key_is_stable_and_isolated_per_job(self):
        args = _args(prompt_cache_key="paper-v1", backend="sub2api")
        job = run_paper_sweep._build_jobs(args)[0]
        first = run_paper_sweep._prompt_cache_config(args, job)
        second = run_paper_sweep._prompt_cache_config(args, job)
        self.assertEqual(first, second)
        self.assertEqual(first["scope"], "job")
        self.assertEqual(first["namespace"], "paper-v1")
        self.assertEqual(first["derivation"], "expgym.job.v1")
        self.assertEqual(first["source"], "explicit")
        self.assertLessEqual(len(first["key"]), 64)
        self.assertRegex(first["key"], r"^[A-Za-z0-9_.-]+$")

        variants = [
            replace(job, cost_regime="cost_moderate"),
            replace(job, rep=1, seed=1207),
            replace(job, model_id="gpt-other"),
            replace(job, scenario="restricted_search", question_index=1),
        ]
        keys = {first["key"]}
        keys.update(
            run_paper_sweep._prompt_cache_config(args, variant)["key"]
            for variant in variants
        )
        self.assertEqual(len(keys), 1 + len(variants))

    def test_long_prompt_cache_namespace_still_produces_bounded_key(self):
        args = _args(prompt_cache_key="paper/实验/" + "x" * 200)
        job = run_paper_sweep._build_jobs(args)[0]
        config = run_paper_sweep._prompt_cache_config(args, job)
        self.assertLessEqual(len(config["key"]), 64)
        self.assertIsNotNone(re.fullmatch(r"[A-Za-z0-9_.-]+", config["key"]))

        other_args = _args(prompt_cache_key="paper/实验/" + "x" * 199 + "y")
        other = run_paper_sweep._prompt_cache_config(other_args, job)
        self.assertNotEqual(config["key"], other["key"])

    def test_literal_prompt_cache_key_preserves_exact_value(self):
        args = _args(
            prompt_cache_key="exact-task-v1",
            prompt_cache_scope="literal",
        )
        job = run_paper_sweep._build_jobs(args)[0]
        config = run_paper_sweep._prompt_cache_config(args, job)
        self.assertEqual(
            config,
            {"key": "exact-task-v1", "scope": "literal"},
        )

    def test_literal_prompt_cache_key_rejects_api_limit_violation(self):
        args = _args(prompt_cache_key="x" * 65, prompt_cache_scope="literal")
        job = run_paper_sweep._build_jobs(args)[0]
        with self.assertRaisesRegex(ValueError, "64-character"):
            run_paper_sweep._prompt_cache_config(args, job)

    def test_unset_prompt_cache_key_remains_disabled(self):
        args = _args(prompt_cache_key=None)
        job = run_paper_sweep._build_jobs(args)[0]
        self.assertEqual(
            run_paper_sweep._prompt_cache_config(args, job),
            {"key": None, "scope": "disabled"},
        )

    def test_sub2api_defaults_to_derived_job_key(self):
        args = _args(prompt_cache_key=None, backend="sub2api")
        job = run_paper_sweep._build_jobs(args)[0]
        config = run_paper_sweep._prompt_cache_config(args, job)
        self.assertEqual(config["scope"], "job")
        self.assertEqual(config["namespace"], "expgym")
        self.assertEqual(config["source"], "sub2api_default")
        self.assertLessEqual(len(config["key"]), 64)

    def test_prompt_cache_can_be_explicitly_disabled_for_sub2api(self):
        args = _args(
            prompt_cache_key="ignored",
            prompt_cache_scope="disabled",
            backend="sub2api",
        )
        job = run_paper_sweep._build_jobs(args)[0]
        self.assertEqual(
            run_paper_sweep._prompt_cache_config(args, job),
            {"key": None, "scope": "disabled"},
        )

    def test_namespace_for_job_passes_effective_derived_key_to_client(self):
        args = _args(prompt_cache_key="paper-v1", backend="sub2api")
        job = run_paper_sweep._build_jobs(args)[0]
        namespace = run_paper_sweep._namespace_for_job(args, job, "secret")
        self.assertEqual(namespace.prompt_cache_key, namespace.prompt_cache["key"])
        self.assertEqual(namespace.prompt_cache["scope"], "job")

    def test_one_model_paper_slice_has_one_unique_key_per_job(self):
        args = _args(
            prompt_cache_key="paper-v1",
            backend="sub2api",
            models="gpt-5.4",
            scenarios=",".join(run_paper_sweep.SCENARIOS),
            cost_regimes=",".join(run_paper_sweep.PAPER_COST_REGIMES),
            tuning_tasks="all-hpobench",
            search_indices="0:35",
            audit_indices="0:13",
            tuning_reps=3,
            audit_reps=3,
            max_steps=30,
            max_evals=999999,
        )
        jobs = run_paper_sweep._build_jobs(args)
        keys = [
            run_paper_sweep._prompt_cache_config(args, job)["key"]
            for job in jobs
        ]
        self.assertEqual(len(jobs), 303)
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(len(key) <= 64 for key in keys))

    def test_trace_path_is_stable(self):
        jobs = run_paper_sweep._build_jobs(
            _args(
                models="dsv32",
                scenarios="restricted_search",
                cost_regimes="cost_moderate",
                search_indices="2",
            )
        )
        path = run_paper_sweep._trace_path(Path("out"), jobs[0])
        self.assertEqual(
            str(path),
            "out/dsv32_cost_moderate/traces/"
            "restricted_search_phantom_seed1_2_r0_s1206.json",
        )

    def test_v2_trace_path_does_not_collide_with_legacy_trace(self):
        job = run_paper_sweep._build_jobs(_args())[0]
        path = run_paper_sweep._trace_path(Path("out"), job, "v2")
        self.assertEqual(
            str(path),
            "out/openai_gpt-4.1-nano_cost_tight/traces-v2/"
            "tuning_neural_network_training_r0_s1206.json",
        )

    def test_result_summary_shows_score_and_trace(self):
        result = {
            "job": {
                "scenario": "tuning",
                "tuning_task": "neural_network_training",
                "model_id": "openai/gpt-4.1-nano",
                "cost_regime": "cost_tight",
            },
            "answer_perf": 0.812345678,
            "score_check": {"ok": True},
            "evaluations": 2,
            "api_calls": 3,
            "cached_prompt_tokens": 120,
            "aborted": False,
        }
        summary = run_paper_sweep._format_result_summary(
            result, Path("budget_sweep_results/e2e/trace.json")
        )
        self.assertIn("EVALUATION RESULT", summary)
        self.assertIn("answer_perf=0.812346", summary)
        self.assertIn("score_check=ok", summary)
        self.assertIn("cached_prompt_tokens=120", summary)
        self.assertIn("trace=budget_sweep_results/e2e/trace.json", summary)

    def test_score_check_rejects_missing_numeric_tool_score(self):
        result = {"answer": "{}", "answer_perf": None}
        check = run_paper_sweep._score_check(
            result,
            {"evaluate_config": lambda _payload: (None, 1.0)},
            None,
        )
        self.assertFalse(check["ok"])
        self.assertEqual(check["reason"], "missing numeric score")

    def test_score_check_accepts_invalid_config_as_zero(self):
        result = {"answer": "{}", "answer_perf": 0.0}
        check = run_paper_sweep._score_check(
            result,
            {
                "evaluate_config": lambda _payload: (
                    "perf=0.000000 (invalid or degenerate configuration)",
                    0.0,
                )
            },
            None,
        )
        self.assertTrue(check["ok"])
        self.assertEqual(check["recomputed_perf"], 0.0)


if __name__ == "__main__":
    unittest.main()
