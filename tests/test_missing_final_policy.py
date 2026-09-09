"""Synthetic-only production-entry policy checks. No actual data/model calls."""
from contextlib import contextmanager, ExitStack, redirect_stdout, redirect_stderr
import argparse
import copy
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
OVERLAY = HERE
BASE = HERE
sys.path.insert(0, str(BASE))
import expgym
from expgym.react_loop import LLMOutput, run_react_loop


@contextmanager
def loaded():
    names = ("demo_experiment", "scripts", "scripts.run_paper_sweep", "scripts.run_poolact",
             "expgym.terminal_evidence", "expgym.missing_final", "expgym.trace_v2")
    saved = {name: sys.modules.get(name) for name in names}
    old_path, old_package = list(sys.path), list(expgym.__path__)
    try:
        sys.path[:] = [str(OVERLAY), str(BASE)] + old_path
        expgym.__path__[:] = [str(OVERLAY / "expgym"), str(BASE / "expgym")]
        for name in names:
            sys.modules.pop(name, None)
        demo = importlib.import_module("demo_experiment")
        sweep = importlib.import_module("scripts.run_paper_sweep")
        pool = importlib.import_module("scripts.run_poolact")
        helper = importlib.import_module("expgym.missing_final")
        trace = importlib.import_module("expgym.trace_v2")
        for module in (demo, sweep, pool, helper, trace):
            assert str(Path(module.__file__)).startswith(str(OVERLAY) + os.sep)
        yield demo, sweep, pool, helper, trace
    finally:
        sys.path[:] = old_path
        expgym.__path__[:] = old_package
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class Native:
    supports_native_tools = True

    def __init__(self, agent_id=0, mode="length"):
        self.agent_id, self.mode, self.requests = agent_id, mode, []

    def generate(self, messages, **options):
        self.requests.append((copy.deepcopy(messages), copy.deepcopy(options)))
        if self.mode == "api_error":
            from expgym.llm_clients import APIClientError
            raise APIClientError("SYNTHETIC transport error", [])
        if len(self.requests) == 1:
            assert options["tool_choice"] == "auto"
            call = {"id": "synthetic_%d" % self.agent_id, "type": "function", "function": {
                "name": "search", "arguments": json.dumps({"query": "MOCK PERSON"})}}
            return LLMOutput("", tool_calls=[call], assistant_message={"role": "assistant", "content": None,
                "tool_calls": [call]}, finish_reason="tool_calls", request_attempts=1)
        assert len(self.requests) == 2 and options["tool_choice"] == "none", "No additional model decision authorized"
        missing = self.mode in {"length", "empty_stop"}
        text = "" if missing else "Answer: MOCK PERSON"
        return LLMOutput(text, assistant_message={"role": "assistant", "content": None if missing else text},
            finish_reason="length" if self.mode == "length" else "stop", request_attempts=1,
            attempt_usage=[{"attempt": 1, "state": "success", "http_status": None, "usage": None}])


def original_search_evaluator(gold):
    import expgym.task_restricted_search as search
    with mock.patch.object(search, "_load_qa", return_value=[{"answer": gold}]):
        return search.build_answer_evaluator(0, "phantom_seed3")


def loop_result(evaluator=None, mode="length", capture=False):
    return run_react_loop(llm=Native(mode=mode), tools={"search": lambda _: ("SYNTHETIC observation", 1.0)},
        context="SYNTHETIC", system_prompt="SYNTHETIC", time_budget=1.0, max_steps=30, max_evals=30,
        answer_evaluator=evaluator, capture_trace_v2=capture, tool_protocol="native")


def bind_score(helper, sweep, result, scenario, evaluator=None):
    helper.mark_loop_return(result, scenario, helper.POLICY)
    result["score_check"] = sweep._score_result(result, {}, evaluator)
    return result


class PolicyTests(unittest.TestCase):
    def test_original_search_empty_prediction_nonempty_and_empty_gold(self):
        with loaded() as (_, sweep, _, helper, _):
            for gold, expected in ((["MOCK PERSON"], 0.0), ([], 1.0)):
                evaluator = original_search_evaluator(gold)
                result = bind_score(helper, sweep, loop_result(evaluator), "restricted_search", evaluator)
                self.assertIsNone(result["answer"])
                self.assertEqual(result["scoring_input"], "")
                self.assertEqual(result["answer_perf"], expected)
                self.assertTrue(helper.terminal_publishable(result, sweep._score_check(result, {}, evaluator)))

    def test_original_audit_empty_prediction_retains_nullable_efficiency(self):
        import expgym.task_evidence_audit as audit
        with loaded() as (_, sweep, _, helper, _), mock.patch.object(audit, "_get_doc", return_value=argparse.Namespace(
                annotations={"NDA-1": {"choice": "Entailment", "spans": [1]}})), mock.patch.object(audit, "_get_labels", return_value=["NDA-1"]):
            evaluator = audit.build_answer_evaluator(0)
            result = bind_score(helper, sweep, loop_result(evaluator), "evidence_audit", evaluator)
            self.assertEqual(result["answer_metrics"], {"label_acc": 0.0, "evidence_acc": 0.0, "verification_eff": None})
            self.assertTrue(result["score_check"]["ok"])

    def test_tuning_missing_is_unknown_without_tools_or_fallback(self):
        with loaded() as (_, sweep, _, helper, _):
            result = loop_result()
            result["eval_records"] = [("{\"x\":1}", "{\"x\":1}", .95, 1.0)]
            helper.mark_loop_return(result, "tuning", helper.POLICY)
            tool = mock.Mock(side_effect=AssertionError("No missing-config evaluation"))
            result["score_check"] = sweep._score_result(result, {"tool": tool}, None)
            self.assertIsNone(result["answer"])
            self.assertIsNone(result["answer_perf"])
            self.assertFalse(result["score_check"]["ok"])
            self.assertTrue(helper.terminal_publishable(result, sweep._score_check(result, {"tool": tool}, None)))
            tool.assert_not_called()

    def test_legacy_missing_still_fails(self):
        with loaded() as (_, sweep, _, helper, _):
            result = loop_result()
            result["score_check"] = sweep._score_result(result, {}, None)
            self.assertFalse(helper.terminal_publishable(result))
            self.assertNotIn("terminal_status", result)

    def test_missing_without_normal_return_marker_fails(self):
        with loaded() as (_, sweep, _, helper, _):
            result = loop_result()
            result["missing_final_policy"] = helper.POLICY
            with self.assertRaises(ValueError):
                sweep._score_result(result, {}, None)

    def test_scorer_exception_and_nonfinite_are_not_model_abstention(self):
        with loaded() as (_, sweep, _, helper, _):
            for evaluator in (mock.Mock(side_effect=RuntimeError("SYNTHETIC scorer error")), lambda _: float("nan"), lambda _: True):
                result = loop_result()
                helper.mark_loop_return(result, "restricted_search", helper.POLICY)
                with self.assertRaises((ValueError, TypeError, RuntimeError)):
                    sweep._score_result(result, {}, evaluator)
                self.assertNotIn("terminal_status", result)

    def test_terminal_status_tampering_and_bool_counts_fail(self):
        with loaded() as (_, sweep, _, helper, _):
            result = bind_score(helper, sweep, loop_result(), "tuning")
            for field, value in (("score_complete", True), ("expected_model_terminals", True), ("model_no_answer_count", 0)):
                changed = copy.deepcopy(result)
                changed["terminal_status"][field] = value
                self.assertFalse(helper.terminal_publishable(changed, sweep._score_check(changed, {}, None)))

    def test_search_n4_empty_slots_and_original_tie(self):
        with loaded() as (_, sweep, pool, helper, _):
            evaluator = original_search_evaluator(["MOCK PERSON"])
            for modes, expected in ((["length"] * 4, ""), (["length", "length", "stop", "stop"], "MOCK PERSON")):
                results = [bind_score(helper, sweep, loop_result(evaluator, mode), "restricted_search", evaluator) for mode in modes]
                aggregate = pool.aggregate_results("restricted_search", results, answer_evaluator=evaluator)
                self.assertEqual(len(aggregate["individual_answers"]), 4)
                self.assertEqual(aggregate["answer"], expected)

    def test_audit_aggregate_keeps_original_empty_tool_records(self):
        with loaded() as (_, sweep, pool, helper, _):
            records = []
            def evaluator(answer, tools):
                records.append(copy.deepcopy(tools))
                return {"label_acc": 0.0, "evidence_acc": 0.0, "verification_eff": None}
            results = [bind_score(helper, sweep, loop_result(evaluator), "evidence_audit", evaluator) for _ in range(4)]
            records[:] = []
            aggregate = pool.aggregate_results("evidence_audit", results, answer_evaluator=evaluator)
            self.assertEqual(records, [[]])
            self.assertEqual(aggregate["answer"], "{}")
            self.assertEqual(len(aggregate["individual_answers"]), 4)

    def test_tuning_partial_and_all_unknown_full_pool_endpoints_unknown(self):
        with loaded() as (_, sweep, pool, helper, _):
            unknown = bind_score(helper, sweep, loop_result(), "tuning")
            known = copy.deepcopy(unknown)
            known.update(answer="{\"x\":1}", answer_perf=.95, scoring_input="{\"x\":1}", score_status="scored_final_answer")
            known["score_check"] = {"ok": True}
            helper.finish_score(known, known["score_check"])
            for n_known in (0, 3):
                values = [copy.deepcopy(known) for _ in range(n_known)] + [copy.deepcopy(unknown) for _ in range(4 - n_known)]
                aggregate = pool.aggregate_results("tuning", values)
                self.assertIsNone(aggregate["answer_perf"])
                self.assertIsNone(aggregate["mean_individual_perf"])
                self.assertEqual(aggregate["known_subset_descriptive"]["n_known"], n_known)
                self.assertTrue(aggregate["terminal_status"]["execution_complete"])
                self.assertFalse(aggregate["terminal_status"]["score_complete"])

    def test_unknown_batch_mean_is_not_complete_case_mean(self):
        with loaded() as (_, _, pool, _, _):
            items = {"0": {"naive": {"answer_perf": .8}}, "1": {"naive": {"answer_perf": None}}}
            for item in items.values():
                item["naive"]["terminal_status"] = {"policy_version": "task-abstention-v1"}
            values = pool._batch_strategy_metrics(items, ["naive"])["naive"]
            self.assertIsNone(values["mean_answer_perf"])
            self.assertEqual(values["known_subset_mean_answer_perf_descriptive"], .8)
            self.assertEqual((values["completed_items"], values["scored_items"], values["unscored_items"]), (2, 1, 1))


    def test_legacy_batch_mean_keeps_original_numeric_only_semantics(self):
        with loaded() as (_, _, pool, _, _):
            for status in (None, {"policy_version": "error"}):
                items = {str(i): {"naive": {"answer_perf": score}} for i, score in enumerate((.5, 1.0, None, True, float("nan")))}
                if status is not None:
                    for item in items.values():
                        item["naive"]["terminal_status"] = status
                metrics = pool._batch_strategy_metrics(items, ["naive"])["naive"]
                self.assertEqual(metrics["mean_answer_perf"], .75)
                self.assertEqual((metrics["completed_items"], metrics["scored_items"]), (5, 2))

    def test_new_policy_all_finite_and_empty_batch_metrics(self):
        with loaded() as (_, _, pool, _, _):
            items = {str(i): {"naive": {"answer_perf": score, "terminal_status": {"policy_version": "task-abstention-v1"}}}
                     for i, score in enumerate((.5, 1.0))}
            self.assertEqual(pool._batch_strategy_metrics(items, ["naive"])["naive"]["mean_answer_perf"], .75)
            self.assertIsNone(pool._batch_strategy_metrics({}, ["naive"])["naive"]["mean_answer_perf"])

    def test_mixed_policy_batch_metrics_rejected(self):
        with loaded() as (_, _, pool, _, _):
            for old_status in (None, {"policy_version": "error"}):
                items = {"0": {"naive": {"answer_perf": .5, "terminal_status": {"policy_version": "task-abstention-v1"}}},
                         "1": {"naive": {"answer_perf": 1.0}}}
                if old_status is not None:
                    items["1"]["naive"]["terminal_status"] = old_status
                with self.assertRaisesRegex(ValueError, "Mixed missing-final policies"):
                    pool._batch_strategy_metrics(items, ["naive"])

    def test_unknown_or_malformed_batch_policy_rejected(self):
        with loaded() as (_, _, pool, _, _):
            for status in (None, [], {"policy_version": "future-policy"}, {"policy_version": True}):
                with self.assertRaises(ValueError):
                    pool._batch_strategy_metrics({"0": {"naive": {"answer_perf": .5, "terminal_status": status}}}, ["naive"])

    def test_independent_agent_guard_is_readonly_and_tuning_unknown_has_no_tool_call(self):
        with loaded() as (_, sweep, _, helper, _):
            result = bind_score(helper, sweep, loop_result(), "tuning")
            before = copy.deepcopy(result)
            tool = mock.Mock(side_effect=AssertionError("No missing-config tool"))
            check = sweep.validate_terminal_result(result, {"evaluate": tool}, None, scenario="tuning")
            self.assertTrue(check["execution_complete"])
            self.assertFalse(check["score_complete"])
            self.assertEqual(result, before)
            tool.assert_not_called()
            self.assertFalse(sweep.validate_terminal_result(result, {}, None, scenario="restricted_search")["execution_complete"])

    def test_independent_pool_guard_recomputes_and_rejects_changed_aggregate(self):
        with loaded() as (_, sweep, pool, helper, _):
            agents = [bind_score(helper, sweep, loop_result(), "tuning") for _ in range(4)]
            for i, agent in enumerate(agents):
                agent["agent_id"] = i
            aggregate = pool.aggregate_results("tuning", agents)
            result = {"agent_results": agents, "aggregate": aggregate, "terminal_status": aggregate["terminal_status"], "shared_state": None}
            before = copy.deepcopy(result)
            checked = pool.validate_terminal_pool(result, {}, None, scenario="tuning", expected_agents=4)
            self.assertTrue(checked["execution_complete"])
            self.assertFalse(checked["score_complete"])
            self.assertEqual(result, before)
            result["aggregate"]["answer_perf"] = .99
            self.assertFalse(pool.validate_terminal_pool(result, {}, None, scenario="tuning", expected_agents=4)["execution_complete"])

    def test_trace_v21_roundtrip_missing_search_and_tuning(self):
        with loaded() as (_, sweep, _, helper, trace):
            for scenario, evaluator in (("tuning", None), ("restricted_search", original_search_evaluator(["MOCK PERSON"]))):
                result = bind_score(helper, sweep, loop_result(evaluator, capture=True), scenario, evaluator)
                result.update(job={"scenario": scenario, "cost_regime": "cost_tight"}, wall_time_seconds=.1,
                              _trace_v2_runtime={"run": {}, "limits": {}})
                with mock.patch.object(trace, "_task_metadata", return_value={"scenario": scenario}), mock.patch.object(trace, "_git_provenance", return_value={}), mock.patch.object(trace, "_environment_provenance", return_value={}):
                    saved = trace.build_trace_v2(result, repo_root=BASE)
                self.assertEqual(saved["schema"]["version"], "2.1.0")
                restored = trace.result_for_score_check(saved)
                self.assertIsNone(restored["answer"])
                self.assertTrue(helper.terminal_publishable(restored, sweep._score_check(restored, {}, evaluator)))
                old = copy.deepcopy(saved)
                old["schema"]["version"] = "2.0.0"
                with self.assertRaises(ValueError):
                    trace.validate_trace_v2(old)

    def pool_run(self, strategy="naive", scenario="restricted_search", modes=None, fail=None, resume=False, corrupt_resume=False):
        modes = modes or ["length"] * 4
        with loaded() as (_, sweep, pool, helper, _), tempfile.TemporaryDirectory(prefix="synthetic_restart_pool_") as temp:
            output = Path(temp) / "results"
            clients = []
            evaluator = None if scenario == "tuning" else original_search_evaluator(["MOCK PERSON"])
            def build(_backend, _plan, ns, **_kw):
                client = Native(ns.seed - 2200, modes[ns.seed - 2200])
                clients.append(client)
                return client
            def tools(_scenario, ns):
                def search(_argument):
                    if fail == "environment" and ns.seed == 2200:
                        raise FileNotFoundError("SYNTHETIC data error")
                    return "SYNTHETIC observation", 1.0
                return {"search": search}
            argv = ["run_poolact.py", "--backend", "openai", "--model", "SYNTHETIC", "--scenario", scenario,
                "--agents", "4", "--seed", "2200", "--question-index", "0", "--strategies", strategy,
                "--tool-protocol", "native", "--output-dir", str(output), "--missing-final-policy", helper.POLICY]
            with mock.patch.object(sys, "argv", argv):
                args = pool.parse_args()
            with ExitStack() as stack:
                blocked = mock.Mock(side_effect=AssertionError("No network or model process"))
                for target in ("socket.socket.connect", "socket.create_connection", "urllib.request.urlopen", "subprocess.Popen"):
                    stack.enter_context(mock.patch(target, blocked))
                patches = {"build_llm": build, "_resolve_tools": tools, "_resolve_context": lambda *_: "SYNTHETIC task",
                    "_resolve_system_prompt": lambda *_: "SYNTHETIC system", "_resolve_answer_evaluator": lambda *_: evaluator,
                    "_call_scenario": lambda *_: [], "evaluation_identity": lambda *_: {"files": {}, "dependencies": {}, "sha256": "SYNTHETIC"}}
                if fail == "scorer":
                    patches["_score_result"] = mock.Mock(side_effect=RuntimeError("SYNTHETIC scorer failure"))
                if fail == "write":
                    patches["_atomic_json"] = mock.Mock(side_effect=OSError("SYNTHETIC disk failure"))
                for key, value in patches.items():
                    stack.enter_context(mock.patch.object(pool, key, value))
                error = None
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    try:
                        pool._run_items(args, [0], None, 1.0, "time_aware", {"source_tree": "SYNTHETIC"})
                    except Exception as exc:
                        error = exc
                    if resume and error is None:
                        before = {str(p): p.read_bytes() for p in output.rglob("*.json") if p.is_file()}
                        count = len(clients)
                        args.resume = True
                        if corrupt_resume:
                            (output / strategy / "result.json").write_text("{}")
                            with self.assertRaisesRegex(RuntimeError, "refusing model resampling"):
                                pool._run_items(args, [0], None, 1.0, "time_aware", {"source_tree": "SYNTHETIC"})
                            self.assertEqual(count, len(clients))
                            return None, None, [], sum(len(c.requests) for c in clients)
                        pool._run_items(args, [0], None, 1.0, "time_aware", {"source_tree": "SYNTHETIC"})
                        self.assertEqual(count, len(clients))
                        self.assertEqual(before, {str(p): p.read_bytes() for p in output.rglob("*.json") if p.is_file()})
                blocked.assert_not_called()
            artifacts = [json.loads(p.read_text()) for p in output.rglob("*.json") if p.is_file()]
            result_path = output / strategy / "result.json"
            result = json.loads(result_path.read_text()) if result_path.exists() else None
            return error, result, artifacts, sum(len(c.requests) for c in clients)

    def test_all_three_pool_strategies_publish_complete_missing_terminals(self):
        for strategy in ("naive", "cached", "poolact"):
            error, result, artifacts, calls = self.pool_run(strategy=strategy, modes=["length", "empty_stop", "stop", "stop"])
            self.assertIsNone(error)
            self.assertEqual(calls, 8)
            self.assertEqual(len(result["agent_results"]), 4)
            self.assertEqual(result["terminal_status"]["model_no_answer_count"], 2)
            self.assertTrue(result["terminal_status"]["score_complete"])
            raw_loops = [v for v in artifacts if v.get("event") == "loop_terminal"]
            self.assertEqual(len(raw_loops), 4)
            self.assertIsNone(raw_loops[0]["payload"]["loop_result"].get("terminal_status"))

    def test_search_and_tuning_unknown_resume_do_not_resample(self):
        for scenario in ("restricted_search", "tuning"):
            error, result, _, calls = self.pool_run(scenario=scenario, resume=True)
            self.assertIsNone(error)
            self.assertEqual(calls, 8)
            self.assertEqual(result["terminal_status"]["score_complete"], scenario == "restricted_search")

    def test_pool_infra_scorer_and_write_failures_still_fail(self):
        for failure in ("environment", "scorer", "write"):
            error, result, artifacts, _ = self.pool_run(fail=failure)
            self.assertIsNotNone(error)
            self.assertIsNone(result)
            self.assertTrue(any(v.get("event") == "exception" for v in artifacts))

    def test_pool_http_exception_is_not_missing_final(self):
        error, result, artifacts, _ = self.pool_run(modes=["api_error", "length", "length", "length"])
        self.assertIsNotNone(error)
        self.assertIsNone(result)
        self.assertEqual(sum(v.get("event") == "loop_terminal" for v in artifacts), 3)

    def test_policy_flag_does_not_enter_generation_or_loop_options(self):
        with loaded() as (demo, _, pool, helper, _):
            with mock.patch.object(sys, "argv", ["run_poolact.py"]):
                args = pool.parse_args()
            before = (demo._generation_options(args), demo._loop_options(args))
            args.missing_final_policy = helper.POLICY
            self.assertEqual(before, (demo._generation_options(args), demo._loop_options(args)))

    def sweep_run(self, scenario, trace_format="v2", fail=None, resume=False, corrupt_resume=False):
        with loaded() as (_, sweep, _, helper, trace), tempfile.TemporaryDirectory(prefix="synthetic_restart_sweep_") as temp:
            output = Path(temp) / "results"
            evaluator = None if scenario == "tuning" else original_search_evaluator(["MOCK PERSON"])
            clients = []
            def build(*_args, **_kwargs):
                client = Native(mode="api_error" if fail == "api" else "length")
                clients.append(client)
                return client
            argv = ["run_paper_sweep.py", "--backend", "openai", "--models", "SYNTHETIC", "--scenarios", scenario,
                "--cost-regimes", "cost_tight", "--tuning-tasks", "neural_network_training", "--tuning-reps", "1",
                "--search-indices", "0", "--search-reps", "1", "--tool-protocol", "native", "--trace-format", trace_format,
                "--output-dir", str(output), "--missing-final-policy", helper.POLICY]
            if resume:
                argv.append("--resume")
            with ExitStack() as stack:
                blocked = mock.Mock(side_effect=AssertionError("No external call"))
                for target in ("socket.socket.connect", "socket.create_connection", "urllib.request.urlopen", "subprocess.Popen"):
                    stack.enter_context(mock.patch(target, blocked))
                patches = {"build_llm": build, "_resolve_tools": lambda *_: {"search": lambda _: ("SYNTHETIC observation", 1.0)},
                    "_resolve_context": lambda *_: "SYNTHETIC task", "_resolve_system_prompt": lambda *_: "SYNTHETIC system",
                    "_resolve_answer_evaluator": lambda *_: evaluator, "_call_scenario": lambda *_: [],
                    "evaluation_identity": lambda *_: {"files": {}, "dependencies": {}, "sha256": "SYNTHETIC"},
                    "_preflight": lambda *_: None, "_load_api_key": lambda *_: "SYNTHETIC-NO-REAL-KEY",
                    "resolve_base_cost": lambda *_: 1.0 / 3.0, "source_tree_sha256": lambda *_: "SYNTHETIC"}
                if fail == "write":
                    patches["write_trace_v2"] = mock.Mock(side_effect=OSError("SYNTHETIC disk failure"))
                for key, value in patches.items():
                    stack.enter_context(mock.patch.object(sweep, key, value))
                for key, value in {"_task_metadata": lambda job, *_: {"scenario": job["scenario"]},
                                   "_git_provenance": lambda *_: {}, "_environment_provenance": lambda: {}}.items():
                    stack.enter_context(mock.patch.object(trace, key, value))
                stack.enter_context(mock.patch.object(sys, "argv", argv))
                captured_error = io.StringIO()
                with redirect_stdout(io.StringIO()), redirect_stderr(captured_error):
                    exit_code = sweep.main()
                    if resume and exit_code == 0:
                        before = {str(p): p.read_bytes() for p in output.rglob("*.json") if p.is_file()}
                        count = len(clients)
                        if corrupt_resume:
                            originals = [p for p in output.rglob("*.json") if p.is_file() and "_terminal_evidence" not in p.parts]
                            self.assertEqual(len(originals), 1)
                            originals[0].write_text("{}")
                            with self.assertRaisesRegex(RuntimeError, "refusing model resampling"):
                                sweep.main()
                            self.assertEqual(len(clients), count)
                            return 0, [], sum(len(c.requests) for c in clients)
                        self.assertEqual(sweep.main(), 0)
                        self.assertEqual(len(clients), count)
                        self.assertEqual(before, {str(p): p.read_bytes() for p in output.rglob("*.json") if p.is_file()})
                if fail is None:
                    self.assertEqual(exit_code, 0, (scenario, trace_format, captured_error.getvalue()))
                blocked.assert_not_called()
            artifacts = [json.loads(p.read_text()) for p in output.rglob("*.json") if p.is_file()]
            return exit_code, artifacts, sum(len(client.requests) for client in clients)

    def test_sweep_v1_v21_search_and_unknown_tuning_persist_and_resume(self):
        for scenario in ("restricted_search", "tuning"):
            for trace_format in ("v1", "v2"):
                code, artifacts, calls = self.sweep_run(scenario, trace_format, resume=True)
                self.assertEqual(code, 0)
                self.assertEqual(calls, 2)
                terminal = [v for v in artifacts if v.get("event") == "loop_terminal"]
                self.assertEqual(len(terminal), 1)
                self.assertIsNone(terminal[0]["payload"]["loop_result"]["answer"])

    def test_sweep_http_and_trace_write_failures_still_exit_nonzero(self):
        for failure in ("api", "write"):
            code, artifacts, _ = self.sweep_run("restricted_search", fail=failure)
            self.assertEqual(code, 1)
            self.assertTrue(any(v.get("event") == "exception" for v in artifacts))

    def test_new_policy_corrupt_pool_resume_fails_without_resampling(self):
        self.pool_run(scenario="tuning", resume=True, corrupt_resume=True)

    def test_new_policy_corrupt_sweep_resume_fails_without_resampling(self):
        self.sweep_run("tuning", resume=True, corrupt_resume=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
