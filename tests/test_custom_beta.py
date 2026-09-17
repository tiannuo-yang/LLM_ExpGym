"""Custom budgets bind execution, trace, cache, and frozen queue identities."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from expgym.react_loop import LLMOutput
from expgym.terminal_evidence import TerminalEvidence
from expgym.trace_v2 import build_trace_v2, validate_trace_v2
from scripts import run_paper_sweep as sweep, run_poolact as pool, run_study_queue as queue


class LookupLLM:
    def __init__(self):
        self.inputs = []

    def generate(self, messages):
        self.inputs.append(copy.deepcopy(messages))
        return LLMOutput('Action: lookup {"name":"Alex"}' if len(self.inputs) == 1
                         else 'Answer: Alex')


@contextlib.contextmanager
def fake_search(module):
    """Use the real ReAct/cache/clock/scorer with a deterministic 300s tool."""
    with contextlib.ExitStack() as stack:
        for name, value in {
            "_resolve_tools": {"lookup": lambda payload: ("KNOWN_PERSON", 300.0)},
            "_resolve_context": "Find Alex.",
            "_resolve_system_prompt": "Find a name using tools.",
            "_resolve_answer_evaluator": lambda answer: float(answer == "Alex"),
            "_call_scenario": [],
            "evaluation_identity": {"sha256": "fixed-inputs", "files": {}, "dependencies": {}},
        }.items():
            stack.enter_context(mock.patch.object(module, name, return_value=value))
        stack.enter_context(mock.patch.object(module, "bind_evaluation_identity"))
        clients = []

        def build(*args, **kwargs):
            client = LookupLLM()
            client.dump_context = args[2]._api_dump_context
            clients.append(client)
            return client

        stack.enter_context(mock.patch.object(module, "build_llm", side_effect=build))
        yield clients


class CustomBetaTests(unittest.TestCase):
    def sweep_args(self, beta, *extra):
        return sweep.parse_args(["--backend", "fake", "--models", "fake",
                                 "--scenarios", "restricted_search", "--cost-regimes", "custom",
                                 "--beta", str(beta), "--tool-protocol", "text",
                                 "--prompt-cache-scope", "disabled", *extra])

    def pool_args(self, beta, *extra):
        return pool.parse_args(["--backend", "fake", "--model", "fake",
                                "--scenario", "restricted_search", "--cost-regime", "custom",
                                "--beta", str(beta), "--agents", "1", "--tool-protocol", "text", *extra])

    def test_cli_rejects_missing_invalid_or_ambiguous_beta(self):
        for module, option in ((sweep, "--cost-regimes"), (pool, "--cost-regime")):
            cases = [[option, "custom"], ["--beta", "5"]]
            cases += [[option, "custom", "--beta=" + value]
                      for value in ("0", "-1", "nan", "inf", "-inf")]
            if module is sweep:
                cases.append([option, "custom,cost_tight", "--beta", "5"])
            for command in cases:
                with self.subTest(module=module.__name__, command=command), \
                     contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    module.parse_args(command)

    def test_resolved_budget_rejects_overflow_and_hidden_time_override(self):
        for args in (self.pool_args(1e308), self.pool_args(5)):
            if args.beta == 5:
                args.time_budget = 12.0
            with self.assertRaises(ValueError):
                sweep._resolved_budget(args)

    def test_presets_keep_historical_budgets_and_cost_visibility(self):
        for regime, beta, budget, mode in (("cost_free", None, None, "no_budget"),
                                           ("cost_moderate", 10.0, 3000.0, "time_aware"),
                                           ("cost_tight", 3.0, 900.0, "time_aware")):
            args = pool.parse_args(["--scenario", "restricted_search", "--cost-regime", regime])
            self.assertEqual(sweep._resolved_budget(args),
                             {"beta": beta, "time_budget": budget, "c_base": 300.0, "mode": mode})

    def test_budget_changes_paths_resume_and_cache_identities(self):
        paths, resumes, keys, pool_keys, configs = set(), set(), set(), set(), set()
        with mock.patch.object(sweep, "source_tree_sha256", return_value="fixed-source"):
            for beta in (1, 5, 15, 20, 1.00000001):
                args = self.sweep_args(beta, "--prompt-cache-scope", "job", "--prompt-cache-key", "study")
                job = sweep._build_jobs(args)[0]
                paths.add(sweep._trace_path(Path("same-output"), job))
                resumes.add(sweep._resume_key(args, job, evaluation={"sha256": "fixed-inputs"}))
                keys.add(sweep._prompt_cache_config(args, job)["key"])
                pool_args = self.pool_args(beta, "--prompt-cache-key", "study")
                pool_keys.add(pool._pool_cache_namespace(pool_args))
                configs.add(json.dumps(pool._resolved_config(pool_args, 300.0 * beta), sort_keys=True))
        for values in (paths, resumes, keys, pool_keys, configs):
            self.assertEqual(len(values), 5)

    def test_sweep_real_loop_trace_and_dump_context_resolve_all_four_budgets(self):
        with fake_search(sweep) as clients, \
             mock.patch.object(sweep, "source_tree_sha256", return_value="fixed-source"):
            for beta in (1, 5, 15, 20):
                args = self.sweep_args(beta)
                job = sweep._build_jobs(args)[0]
                evidence = TerminalEvidence(None, owner={}, source_root=sweep.REPO_ROOT)
                result = sweep._run_job_with_evidence(args, job, None, evidence)
                self.assertTrue(result["score_check"]["ok"])
                self.assertEqual(result["total_overhead"], 300.0)
                self.assertEqual(result["cost_regime_resolved"]["time_budget"], beta * 300.0)
                self.assertEqual(clients[-1].dump_context["cost_regime_resolved"], result["cost_regime_resolved"])
                self.assertEqual("KNOWN_PERSON" in str(clients[-1].inputs[-1]), beta > 1)
                trace = build_trace_v2(result, repo_root=sweep.REPO_ROOT)
                self.assertEqual(trace["task"]["budget"]["limit_seconds"], beta * 300.0)
                self.assertEqual(trace["task"]["budget"]["beta"], beta)
                trace["task"]["budget"]["beta"] = 0.0
                with self.assertRaisesRegex(ValueError, "exclusive minimum"):
                    validate_trace_v2(trace)

    def test_pool_real_runtime_clock_cache_and_graph_obey_same_budget(self):
        with tempfile.TemporaryDirectory() as directory, fake_search(pool) as clients:
            for beta in (1, 5, 15, 20):
                for strategy in ("naive", "cached", "poolact"):
                    with self.subTest(beta=beta, strategy=strategy):
                        args = self.pool_args(beta, "--output-dir", directory)
                        with mock.patch.object(pool, "run_react_loop", wraps=pool.run_react_loop) as loop:
                            result = pool._run_strategy(args, strategy, None, beta * 300.0, "time_aware")
                        self.assertEqual(loop.call_args.kwargs["time_budget"], beta * 300.0)
                        if strategy != "naive":
                            self.assertEqual(loop.call_args.kwargs["agent_clock"].now, 300.0)
                            self.assertEqual(result["shared_state"]["cache"]["size"], int(beta > 1))
                        if strategy == "poolact":
                            self.assertEqual(result["shared_state"]["graph"]["pending_claims"], 0)
                        agent = result["agent_results"][0]
                        self.assertEqual(agent["cost_regime_resolved"]["time_budget"], beta * 300.0)
                        self.assertEqual(clients[-1].dump_context["cost_regime_resolved"], agent["cost_regime_resolved"])
                        self.assertEqual("KNOWN_PERSON" in str(clients[-1].inputs[-1]), beta > 1)

    def matrix(self, betas=(1, 5, 15, 20)):
        return {"stages": [
            {"label": f"{runner}-{beta}", "runner": runner, "args":
             (["--backend", "fake", "--models", "fake", "--scenarios", "restricted_search", "--cost-regimes", "custom"]
              if runner == "expgym" else
              ["--backend", "fake", "--model", "fake", "--scenario", "restricted_search", "--cost-regime", "custom",
               "--strategies", "naive", "--agents", "1"])
             + ["--beta", str(beta), "--tool-protocol", "text"]}
            for runner in ("expgym", "poolact") for beta in betas]}

    def test_queue_freezes_effective_budget_and_distinct_outputs_and_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            matrix = self.matrix()
            kwargs = dict(study_id="budget-grid", output_root=Path(directory), default_python=sys.executable)
            plan = queue.make_plan(matrix, **kwargs)
            self.assertEqual(len(plan["jobs"]), 8)
            for field in ("output_dir", "prompt_cache_key"):
                self.assertEqual(len({job["args"][field] for job in plan["jobs"]}), 8)
            for job in plan["jobs"]:
                self.assertEqual(job["identity"]["budget"]["time_budget"], 300.0 * job["args"]["beta"])
            matrix["stages"].append({**matrix["stages"][0], "label": "duplicate"})
            with self.assertRaisesRegex(ValueError, "duplicate logical"):
                queue.make_plan(matrix, **kwargs)

    def test_custom_pool_queue_verifies_saved_result_and_rejects_changed_beta(self):
        with tempfile.TemporaryDirectory() as directory, fake_search(pool), \
             mock.patch.object(pool, "_implementation_manifest", return_value={"source_tree": "fixed"}), \
             contextlib.redirect_stdout(io.StringIO()):
            plan = queue.make_plan(self.matrix((1,)), study_id="budget-grid",
                                   output_root=Path(directory), default_python=sys.executable)
            job = next(job for job in plan["jobs"] if job["runner"] == "poolact")
            args = queue.namespace(job["args"])
            self.assertEqual(pool.main(args, selected_repeat=0), 0)
            queue.verify_result(job, args)
            args.beta = 5.0
            with self.assertRaisesRegex(ValueError, "exact identity/score"):
                queue.verify_result(job, args)

    def test_pool_records_native_parameter_omissions_without_dump(self):
        client = LookupLLM()
        client.api_protocol = "responses"
        client.parameter_compatibility = {"omitted": ["max_tokens", "seed"]}
        with tempfile.TemporaryDirectory() as directory, fake_search(pool), \
             mock.patch.object(pool, "build_llm", return_value=client):
            args = self.pool_args(5, "--output-dir", directory)
            agent = pool._run_strategy(args, "naive", None, 1500.0, "time_aware")["agent_results"][0]
            self.assertEqual(agent["api_protocol"], "responses")
            self.assertEqual(agent["parameter_compatibility"], client.parameter_compatibility)
            self.assertIsNot(agent["parameter_compatibility"], client.parameter_compatibility)


if __name__ == "__main__":
    unittest.main()
