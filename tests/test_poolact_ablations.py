"""Behavioral checks for the two explicitly identified coordination ablations."""
import copy
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from expgym.poolact import PoolActCoordinator, poolact_protocol_for_strategy, run_agents_parallel
from expgym.react_loop import LLMOutput, run_react_loop
from scripts import run_poolact


def native_call():
    call = {"id": "fixture_call", "type": "function", "function": {
        "name": "search", "arguments": '{"query":"local"}'}}
    return LLMOutput(text="", tool_calls=[call], finish_reason="tool_calls",
                     assistant_message={"role": "assistant", "content": None,
                                        "tool_calls": [call]})


class NativeRecorder:
    supports_native_tools = True

    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.requests = []

    def generate(self, messages, **kwargs):
        self.requests.append((copy.deepcopy(messages), kwargs))
        return next(self.outputs)


def run_bound(runtime, llm, **options):
    return run_react_loop(
        llm, runtime.tools, context="Find the answer.",
        observation_augmenter=runtime.observation_augmenter,
        pre_tool_hook=runtime.pre_tool_hook, llm_lock=runtime.reasoning_lock,
        agent_clock=runtime.clock, **options,
    )


class CoordinationAblationTest(unittest.TestCase):
    def test_only_full_poolact_serializes_reasoning_tools_still_parallel(self):
        for strategy in ("poolact", "graph_no_lock", "peer_context"):
            with self.subTest(strategy=strategy):
                coordinator = PoolActCoordinator(2, strategy=strategy)
                reasoning_barrier = threading.Barrier(2, timeout=3)
                tool_barrier = threading.Barrier(2, timeout=3)
                counter_lock = threading.Lock()
                active = peak = 0

                class Backend:
                    def __init__(self):
                        self.calls = 0

                    def generate(self, messages):
                        nonlocal active, peak
                        self.calls += 1
                        if self.calls != 1:
                            return LLMOutput("Answer: done")
                        with counter_lock:
                            active += 1
                            peak = max(peak, active)
                        try:
                            if strategy == "poolact":
                                time.sleep(.02)
                            else:
                                reasoning_barrier.wait()
                            return LLMOutput('Action: search {"query":"same"}')
                        finally:
                            with counter_lock:
                                active -= 1

                def agent(agent_id):
                    def tool(payload):
                        tool_barrier.wait()
                        return "complete", 1.
                    runtime = coordinator.bind_tools({"search": tool}, agent_id, time_budget=10.)
                    try:
                        result = run_bound(runtime, Backend(), time_budget=10., max_steps=2)
                        self.assertEqual(runtime.clock.now, 1.)
                        return result
                    finally:
                        coordinator.complete_agent_claims(agent_id, completion_time=runtime.clock.now)

                results = run_agents_parallel(2, agent)
                self.assertEqual([r["answer"] for r in results], ["done", "done"])
                self.assertEqual(peak, 1 if strategy == "poolact" else 2)
                if coordinator.graph is not None:
                    self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)
                else:
                    self.assertEqual(coordinator.peer_context.stats()["total_entries"], 2)

    def test_graph_without_reasoning_lock_keeps_claims_and_cleans_exception(self):
        coordinator = PoolActCoordinator(2, strategy="graph_no_lock")
        def fail(_payload):
            raise RuntimeError("fixture tool failure")
        runtime = coordinator.bind_tools({"search": fail}, 0, time_budget=10.)
        self.assertIsNone(runtime.reasoning_lock)
        runtime.pre_tool_hook("search", '{"query":"pending"}')
        viewer = coordinator.bind_tools({}, 1, time_budget=10.)
        self.assertIn("pending", viewer.observation_augmenter("task"))
        with self.assertRaisesRegex(RuntimeError, "fixture tool failure"):
            runtime.tools["search"]('{"query":"pending"}')
        self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)

    def test_independent_pools_and_agent_clocks_have_no_shared_mutation(self):
        first = PoolActCoordinator(2, strategy="peer_context")
        second = PoolActCoordinator(2, strategy="peer_context")
        a = first.bind_tools({}, 0, time_budget=10.)
        b = first.bind_tools({}, 1, time_budget=10.)
        a.clock.advance(3.)
        first.peer_context.record(0, "search", "{}", "visible", completion_time=0.)
        self.assertEqual(b.clock.now, 0.)
        self.assertEqual(second.peer_context.stats()["total_entries"], 0)
        self.assertIsNot(first.cache, second.cache)

    def test_graph_no_lock_retains_full_long_payload_identity_and_cache_semantics(self):
        coordinator = PoolActCoordinator(2, strategy="graph_no_lock")
        payloads = [json.dumps({"a_long_prefix": "same" * 80, "z_variant": i},
                               sort_keys=True, separators=(",", ":")) for i in (0, 1)]
        self.assertEqual(payloads[0][:80], payloads[1][:80])
        calls = []
        def evaluate(payload):
            calls.append(payload)
            return float(json.loads(payload)["z_variant"]), 1.
        first = coordinator.bind_tools({"evaluate_config": evaluate}, 0, time_budget=10.)
        second = coordinator.bind_tools({"evaluate_config": evaluate}, 1, time_budget=10.)
        for payload in payloads:
            first.pre_tool_hook("evaluate_config", payload)
            first.tools["evaluate_config"](payload)
            first.clock.advance(1.)
        second.clock.advance(2.)
        self.assertEqual(second.tools["evaluate_config"](payloads[0]), (0., 0.))
        self.assertEqual(calls, payloads)
        self.assertEqual(coordinator.graph.stats()["eval_nodes"], 2)
        self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)
        self.assertTrue(all(a != b for a, b in coordinator.graph._edges))

    def test_forced_final_peer_context_filters_self_future_and_budget_boundary(self):
        coordinator = PoolActCoordinator(2, strategy="peer_context")
        peer = coordinator.peer_context
        peer.record(1, "search", "{}", "VISIBLE", completion_time=3.)
        peer.record(1, "search", "{}", "FUTURE", completion_time=8.)
        peer.record(1, "search", "{}", "BOUNDARY", completion_time=10.)
        peer.record(0, "search", "{}", "SELF", completion_time=1.)
        runtime = coordinator.bind_tools({}, 0, time_budget=10.)
        runtime.clock.advance(5.)
        llm = NativeRecorder([LLMOutput("Answer: done")])
        result = run_bound(runtime, llm, max_steps=0, time_budget=10.)
        prompt = json.dumps(llm.requests[0][0])
        self.assertIn("VISIBLE", prompt)
        for withheld in ("FUTURE", "BOUNDARY", "SELF"):
            self.assertNotIn(withheld, prompt)
        self.assertEqual(llm.requests[0][1]["tool_choice"], "none")
        self.assertEqual(result["context_preparations"][0]["latest_shared_snapshot_complete"], True)

    def test_native_wire_gets_all_long_peer_records_and_preserves_snapshot_history(self):
        coordinator = PoolActCoordinator(2, strategy="peer_context")
        def tool(_payload):
            for i in range(35):
                coordinator.peer_context.record(1, "search", json.dumps({"query": i}),
                                                "full-result-" + str(i) + "-" + "x" * 200,
                                                completion_time=1.)
            return "own result", 1.
        runtime = coordinator.bind_tools({"search": tool}, 0, time_budget=10.)
        llm = NativeRecorder([native_call(), native_call(), LLMOutput("Answer: done")])
        result = run_bound(runtime, llm, max_steps=2, time_budget=10., max_context_tokens=50000)
        self.assertEqual(len(llm.requests), 3)
        snapshot = llm.requests[1][0][-1]["content"]
        for i in range(35):
            self.assertIn("full-result-" + str(i) + "-" + "x" * 200, snapshot)
        self.assertIn(snapshot, [m.get("content") for m in llm.requests[2][0]])
        self.assertEqual(llm.requests[2][1]["tool_choice"], "none")
        self.assertTrue(all(event["admitted"] for event in result["context_preparations"]))
        self.assertFalse(any(event["history_modified"] for event in result["context_preparations"]))

    def test_latest_full_snapshot_is_rejected_instead_of_silently_truncated(self):
        coordinator = PoolActCoordinator(2, strategy="peer_context")
        def tool(_payload):
            for i in range(35):
                coordinator.peer_context.record(1, "search", str(i), "x" * 250, completion_time=1.)
            return "own result", 1.
        runtime = coordinator.bind_tools({"search": tool}, 0, time_budget=10.)
        llm = NativeRecorder([native_call()])
        result = run_bound(runtime, llm, max_steps=3, time_budget=10., max_context_tokens=1500)
        self.assertEqual(result["api_calls"], 1)
        self.assertIsNone(result["answer"])
        reasons = [event["reason"] for event in result["context_preparations"]]
        self.assertIn("latest_shared_snapshot_would_be_truncated", reasons)
        self.assertTrue(result["aborted"])
        self.assertGreater(result["context_preparations"][1]["latest_shared_snapshot_chars"], 600)


class AblationRunnerIdentityTest(unittest.TestCase):
    def test_strategy_protocol_bound_in_config_dumps_cache_namespaces(self):
        strategies = "naive,cached,peer_context,graph_no_lock,poolact"
        args = run_poolact.parse_args(["--strategies", strategies, "--prompt-cache-key", "fixture"])
        config = run_poolact._resolved_config(args, 900.)
        self.assertEqual(set(config["strategy_protocols"]), set(strategies.split(",")))
        keys = []
        for strategy in args.strategies:
            namespace = run_poolact._agent_namespace(args, strategy, 0, None)
            self.assertEqual(namespace._api_dump_context["strategy_protocol"], poolact_protocol_for_strategy(strategy))
            keys.append(namespace.prompt_cache_key)
        self.assertEqual(len(set(keys)), 5)
        before = run_poolact._agent_namespace(args, "peer_context", 0, None).prompt_cache_key
        with mock.patch("expgym.poolact.PEER_CONTEXT_PROTOCOL_VERSION", "fixture-different-protocol"):
            after = run_poolact._agent_namespace(args, "peer_context", 0, None).prompt_cache_key
            self.assertNotEqual(before, after)
            self.assertNotEqual(config, run_poolact._resolved_config(args, 900.))

    def test_runner_routes_new_hooks_and_records_actual_protocol(self):
        for strategy in ("graph_no_lock", "peer_context"):
            with self.subTest(strategy=strategy), tempfile.TemporaryDirectory() as directory:
                args = run_poolact.parse_args(["--strategies", strategy, "--agents", "1",
                                                "--output-dir", directory])
                expected = {"answer": "{}", "answer_perf": .5}
                with mock.patch.object(run_poolact, "run_react_loop", return_value=expected.copy()) as loop, \
                     mock.patch.object(run_poolact, "_score_result", return_value={"ok": True}):
                    result = run_poolact._run_strategy(args, strategy, None, 900., "time_aware")
                self.assertIsNone(loop.call_args.kwargs["llm_lock"])
                self.assertEqual(result["strategy_protocol"], poolact_protocol_for_strategy(strategy))
                self.assertEqual(result["agent_results"][0]["strategy_protocol"], result["strategy_protocol"])
                self.assertEqual(loop.call_args.kwargs["pre_tool_hook"] is None, strategy == "peer_context")
                self.assertEqual("peer_context" in result["shared_state"], strategy == "peer_context")

    def test_resume_rejects_wrong_strategy_protocol_before_score_or_model_calls(self):
        args = run_poolact.parse_args(["--strategies", "peer_context", "--agents", "1"])
        args._evaluation_identity = {"sha256": "fixture"}
        config = run_poolact._resolved_config(args, 900.)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps({"config": config, "strategy": "peer_context", "agents": 1,
                                        "implementation_sha256": {"source_tree": "fixture"},
                                        "strategy_protocol": "paper-graph-lock-v4"}))
            with mock.patch.object(run_poolact, "_score_check", side_effect=AssertionError("unexpected scoring")):
                result = run_poolact._load_resumable_result(
                    path, item_output_dir=Path(directory), strategy="peer_context", config=config,
                    implementation={"source_tree": "fixture"}, agents=1, answer_evaluator=None)
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
