"""No-network regression checks for the historical runner's explicit budgets."""
import copy
from dataclasses import replace
from pathlib import Path
import unittest
from unittest import mock

from expgym.react_loop import LLMOutput, run_react_loop
from scripts import run_paper_sweep as runner


def args_for(regime="custom", beta=10):
    argv = ["--backend", "fake", "--models", "fake", "--scenarios", "restricted_search",
            "--search-data-source", "phantom_seed2", "--search-indices", "0",
            "--seed", "2200", "--cost-regimes", regime, "--tool-protocol", "native"]
    if beta is not None:
        argv += ["--beta", str(beta)]
    return runner.parse_args(argv)


class CustomBetaTest(unittest.TestCase):
    def test_invalid_budget_rejected_before_jobs(self):
        for regimes, beta in [(["custom"], None), (["custom"], 0), (["custom"], -1),
                              (["custom"], float("nan")), (["custom"], float("inf")),
                              (["custom"], True), (["cost_moderate"], 10),
                              (["custom", "cost_moderate"], 10)]:
            with self.subTest(regimes=regimes, beta=beta), self.assertRaises(ValueError):
                runner._validate_custom_beta(regimes, beta)

    def test_requested_search_budgets_and_visible_cost_mode(self):
        for beta, seconds in [(1, 300), (5, 1500), (15, 4500), (20, 6000)]:
            with self.subTest(beta=beta):
                args = args_for(beta=beta)
                job, = runner._build_jobs(args)
                namespace = runner._namespace_for_job(args, job, None)
                self.assertEqual(namespace.beta, beta)
                self.assertEqual(namespace.baseline, "time_aware")
                self.assertEqual(runner._job_budget(job), {
                    "mode": "time_aware", "c_base": 300, "beta": beta, "time_budget": seconds})

    def test_named_presets_remain_unchanged_and_beta10_matches_moderate(self):
        for regime, seconds, mode in [("cost_free", None, "no_budget"),
                                     ("cost_moderate", 3000, "time_aware"),
                                     ("cost_tight", 900, "time_aware")]:
            args = args_for(regime=regime, beta=None)
            job, = runner._build_jobs(args)
            namespace = runner._namespace_for_job(args, job, None)
            self.assertIsNone(namespace.beta)
            self.assertEqual(namespace.baseline, "both")
            self.assertEqual(runner._job_budget(job)["time_budget"], seconds)
            self.assertEqual(runner._job_budget(job)["mode"], mode)
        moderate, = runner._build_jobs(args_for("cost_moderate", None))
        custom, = runner._build_jobs(args_for(beta=10))
        self.assertEqual(runner._job_budget(moderate), runner._job_budget(custom))

    def test_budgets_separate_trace_cache_and_resume_identity(self):
        args = args_for(beta=1)
        args.prompt_cache_key = "budget-regression"
        job, = runner._build_jobs(args)
        other = replace(job, beta=5.0)
        self.assertNotEqual(runner._trace_path(Path("out"), job), runner._trace_path(Path("out"), other))
        self.assertNotEqual(runner._prompt_cache_config(args, job)["key"],
                            runner._prompt_cache_config(args, other)["key"])
        with mock.patch.object(runner, "source_tree_sha256", return_value="fixed-source"):
            self.assertNotEqual(runner._resume_key(args, job, evaluation={}),
                                runner._resume_key(args, other, evaluation={}))
        nearby = replace(job, beta=1.0000000000000002)
        self.assertNotEqual(runner._trace_path(Path("out"), job), runner._trace_path(Path("out"), nearby))

    def test_selected_job_cannot_silently_use_different_beta(self):
        args = args_for(beta=1)
        args.dry_run = True
        job, = runner._build_jobs(args)
        with self.assertRaisesRegex(SystemExit, "selected job beta"):
            runner.main(args, selected_job=replace(job, beta=5.0))

    def test_native_budget_boundary_hides_result_at_or_over_budget(self):
        for cost, visible in [(299.0, True), (300.0, False), (301.0, False)]:
            call = {"id": "fixture_call", "type": "function", "function": {
                "name": "search", "arguments": '{"query":"A"}'}}

            class Replay:
                supports_native_tools = True

                def __init__(self):
                    self.requests = []
                    self.outputs = iter([LLMOutput("", tool_calls=[call], finish_reason="tool_calls"),
                                         LLMOutput("Answer: A", finish_reason="stop")])

                def generate(self, messages, **kwargs):
                    self.requests.append(copy.deepcopy(messages))
                    return next(self.outputs)

            def search(_):
                return "ARTICLE_SENTINEL", cost

            search.__expgym_tool_schema__ = {"name": "search", "description": "Fixture search",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                               "required": ["query"], "additionalProperties": False}}
            replay = Replay()
            job, = runner._build_jobs(args_for(beta=1))
            result = run_react_loop(llm=replay, tools={"search": search},
                time_budget=runner._job_budget(job)["time_budget"], max_steps=30, max_evals=30,
                context="Fixture question", include_cost_in_observation=True,
                tool_protocol="native", capture_trace_v2=True)
            second_tools = [m["content"] for m in replay.requests[1] if m["role"] == "tool"]
            self.assertEqual(any("ARTICLE_SENTINEL" in text for text in second_tools), visible)
            self.assertEqual(result["aborted"], not visible)
            if visible:
                self.assertIn("cost=299s [time_left=1s]", second_tools[0])
            else:
                self.assertIn("result withheld", second_tools[0])


if __name__ == "__main__":
    unittest.main()
