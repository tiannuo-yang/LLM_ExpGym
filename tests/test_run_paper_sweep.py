import argparse
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
        base_url=None,
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
