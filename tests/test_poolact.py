import json
import threading
import time
import unittest
from unittest.mock import patch

from expgym.poolact import (
    PoolActCoordinator,
    aggregate_results,
    run_agents_parallel,
)
from expgym.react_loop import LLMBackend, LLMOutput, run_react_loop


class SequenceLLM(LLMBackend):
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.inputs = []

    def generate(self, messages):
        self.inputs.append([dict(message) for message in messages])
        return LLMOutput(self.outputs.pop(0))


class CountingLock:
    def __init__(self):
        self._lock = threading.Lock()
        self.entries = 0

    def __enter__(self):
        self._lock.acquire()
        self.entries += 1
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._lock.release()


class PoolActClaimLifecycleTest(unittest.TestCase):
    def test_cache_and_claim_keys_canonicalize_json_object_order(self):
        coordinator = PoolActCoordinator(2)
        coordinator.cache.put(
            "lookup",
            '{"x":1,"y":2}',
            ("cached", 9.0),
            completion_time=0.0,
        )
        original_calls = 0

        def original(_payload):
            nonlocal original_calls
            original_calls += 1
            return ("fresh", 9.0)

        runtime = coordinator.bind_tools({"lookup": original}, agent_id=1)
        reordered = '{"y": 2, "x": 1}'
        runtime.pre_tool_hook("lookup", reordered)
        result = runtime.tools["lookup"](reordered)

        self.assertEqual(result, ("cached", 0.0))
        self.assertEqual(original_calls, 0)
        self.assertEqual(coordinator.cache.stats()["hits"], 1)
        self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)

    def test_cache_keeps_result_from_earliest_simulated_completion(self):
        coordinator = PoolActCoordinator(2)
        coordinator.cache.put("lookup", "{}", ("late", 5.0), completion_time=20.0)
        coordinator.cache.put("lookup", "{}", ("early", 5.0), completion_time=10.0)
        self.assertEqual(
            coordinator.cache.get("lookup", "{}", visible_before=10.0),
            ("early", 5.0),
        )

    def test_concurrent_cache_writes_keep_earliest_simulated_completion(self):
        coordinator = PoolActCoordinator(2)
        barrier = threading.Barrier(2, timeout=2.0)

        def put(result, completion_time):
            barrier.wait()
            coordinator.cache.put(
                "lookup",
                '{"x":1}',
                result,
                completion_time=completion_time,
            )

        late = threading.Thread(target=put, args=(("late", 5.0), 20.0))
        early = threading.Thread(target=put, args=(("early", 5.0), 10.0))
        late.start()
        early.start()
        late.join(timeout=2.0)
        early.join(timeout=2.0)

        self.assertFalse(late.is_alive())
        self.assertFalse(early.is_alive())
        self.assertEqual(
            coordinator.cache.get(
                "lookup", '{"x":1}', visible_before=10.0
            ),
            ("early", 5.0),
        )

    def test_cache_hit_completes_pre_tool_claim(self):
        coordinator = PoolActCoordinator(2)
        coordinator.cache.put("lookup", '{"x":1}', ("cached", 9.0))
        runtime = coordinator.bind_tools(
            {"lookup": lambda payload: ("fresh", 9.0)},
            agent_id=1,
        )

        runtime.pre_tool_hook("lookup", '{"x":1}')
        result = runtime.tools["lookup"]('{"x":1}')

        self.assertEqual(result, ("cached", 0.0))
        self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)

    def test_tool_exception_clears_pre_tool_claim(self):
        coordinator = PoolActCoordinator(2)

        def fail(_payload):
            raise RuntimeError("boom")

        runtime = coordinator.bind_tools({"lookup": fail}, agent_id=0)
        runtime.pre_tool_hook("lookup", "{}")
        with self.assertRaisesRegex(RuntimeError, "boom"):
            runtime.tools["lookup"]("{}")
        self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)

    def test_clock_is_advanced_once_by_react_loop(self):
        coordinator = PoolActCoordinator(1)
        runtime = coordinator.bind_tools(
            {"evaluate_config": lambda payload: (0.5, 10.0)},
            agent_id=0,
        )
        llm = SequenceLLM(
            [
                'Thought: test\nAction: evaluate_config {"x":1}',
                'Answer: {"x":1}',
            ]
        )
        result = run_react_loop(
            llm=llm,
            tools=runtime.tools,
            context="Tune x.",
            max_steps=2,
            time_budget=100.0,
            observation_augmenter=runtime.observation_augmenter,
            agent_clock=runtime.clock,
            pre_tool_hook=runtime.pre_tool_hook,
            llm_lock=runtime.reasoning_lock,
        )

        self.assertEqual(result["total_overhead"], 10.0)
        self.assertEqual(runtime.clock.now, 10.0)
        self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)


class PoolActReasoningSemanticsTest(unittest.TestCase):
    def test_regular_reasoning_is_locked(self):
        lock = CountingLock()
        llm = SequenceLLM(["Answer: done"])

        result = run_react_loop(
            llm=llm,
            tools={},
            context="Task",
            max_steps=1,
            llm_lock=lock,
        )

        self.assertEqual(result["answer"], "done")
        self.assertEqual(lock.entries, 1)

    def test_initial_reasoning_call_sees_existing_pending_claim(self):
        coordinator = PoolActCoordinator(2)
        coordinator.graph.record_claim(
            "search", '{"query":"alice"}', 0, start_time=0.0
        )
        runtime = coordinator.bind_tools({}, agent_id=1)
        llm = SequenceLLM(["Answer: done"])

        run_react_loop(
            llm=llm,
            tools=runtime.tools,
            context="Find the answer.",
            max_steps=1,
            observation_augmenter=runtime.observation_augmenter,
            agent_clock=runtime.clock,
            pre_tool_hook=runtime.pre_tool_hook,
            llm_lock=runtime.reasoning_lock,
        )

        first_prompt = "\n".join(message["content"] for message in llm.inputs[0])
        self.assertIn("== In Progress ==", first_prompt)
        self.assertIn('search "alice"', first_prompt)
        self.assertIn("== Already Explored ==", first_prompt)
        self.assertIn("== Exploration Paths ==", first_prompt)
        self.assertIn("== Coverage Gap ==", first_prompt)

    def test_forced_answer_is_also_reasoning_locked(self):
        lock = CountingLock()
        llm = SequenceLLM(["Answer: done"])
        result = run_react_loop(
            llm=llm,
            tools={},
            context="Task",
            max_steps=0,
            llm_lock=lock,
        )

        self.assertEqual(result["answer"], "done")
        self.assertEqual(lock.entries, 1)

    def test_tool_calls_execute_in_parallel_after_reasoning_unlocks(self):
        coordinator = PoolActCoordinator(2)
        barrier = threading.Barrier(2, timeout=2.0)
        counter_lock = threading.Lock()
        active = 0
        max_active = 0
        reasoning_active = 0
        max_reasoning_active = 0

        class SlowSequenceLLM(SequenceLLM):
            def generate(self, messages):
                nonlocal reasoning_active, max_reasoning_active
                with counter_lock:
                    reasoning_active += 1
                    max_reasoning_active = max(
                        max_reasoning_active, reasoning_active
                    )
                try:
                    time.sleep(0.02)
                    return super().generate(messages)
                finally:
                    with counter_lock:
                        reasoning_active -= 1

        def run_agent(agent_id):
            nonlocal active, max_active

            def tool(_payload):
                nonlocal active, max_active
                with counter_lock:
                    active += 1
                    max_active = max(max_active, active)
                barrier.wait()
                with counter_lock:
                    active -= 1
                return ("ok", 10.0)

            runtime = coordinator.bind_tools({"lookup": tool}, agent_id)
            llm = SlowSequenceLLM(
                [
                    'Thought: look\nAction: lookup {"x":1}',
                    "Answer: done",
                ]
            )
            return run_react_loop(
                llm=llm,
                tools=runtime.tools,
                context="Task",
                max_steps=2,
                observation_augmenter=runtime.observation_augmenter,
                agent_clock=runtime.clock,
                pre_tool_hook=runtime.pre_tool_hook,
                llm_lock=runtime.reasoning_lock,
            )

        results = run_agents_parallel(2, run_agent)
        self.assertEqual(max_reasoning_active, 1)
        self.assertEqual(max_active, 2)
        self.assertEqual([result["answer"] for result in results], ["done", "done"])
        self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)


class PoolActAggregationTest(unittest.TestCase):
    def test_search_vote_is_invariant_to_name_order(self):
        results = [
            {"answer": "Alice Smith, Bob Jones", "answer_perf": 1.0},
            {"answer": "Bob Jones, Alice Smith", "answer_perf": 1.0},
            {"answer": "Carol Doe", "answer_perf": 0.0},
        ]
        aggregate = aggregate_results(
            "restricted_search",
            results,
            answer_evaluator=lambda answer: 1.0 if "Alice" in answer else 0.0,
        )
        self.assertEqual(aggregate["answer"], "Alice Smith, Bob Jones")
        self.assertEqual(aggregate["answer_perf"], 1.0)

    def test_search_vote_normalizes_name_order_case_and_space(self):
        results = [
            {"answer": "  Alice   Smith, BOB Jones  ", "answer_perf": 1.0},
            {"answer": "bob jones, alice smith", "answer_perf": 1.0},
            {"answer": "Carol Doe", "answer_perf": 0.0},
        ]
        aggregate = aggregate_results(
            "restricted_search",
            results,
            answer_evaluator=lambda answer: 1.0 if "Alice" in answer else 0.0,
        )
        self.assertEqual(aggregate["answer"], "  Alice   Smith, BOB Jones  ")
        self.assertEqual(aggregate["answer_perf"], 1.0)

    def test_search_vote_prefers_nonempty_answer_on_tie(self):
        results = [
            {"answer": "", "answer_perf": 0.0},
            {"answer": "Alice Smith", "answer_perf": 1.0},
        ]
        aggregate = aggregate_results(
            "restricted_search",
            results,
            answer_evaluator=lambda answer: float(bool(answer)),
        )
        self.assertEqual(aggregate["answer"], "Alice Smith")

    def test_audit_votes_per_hypothesis(self):
        results = [
            {
                "answer": json.dumps(
                    {"nda1": {"label": "E", "evidence_ids": [1]}}
                )
            },
            {
                "answer": json.dumps(
                    {"nda1": {"label": "E", "evidence_ids": [1]}}
                )
            },
            {
                "answer": json.dumps(
                    {"nda1": {"label": "N", "evidence_ids": [2]}}
                )
            },
        ]
        aggregate = aggregate_results("evidence_audit", results)
        self.assertEqual(
            json.loads(aggregate["answer"]),
            {"nda1": {"label": "E", "evidence_ids": [1]}},
        )

    def test_audit_vote_normalizes_labels_and_evidence_ids(self):
        results = [
            {
                "answer": json.dumps(
                    {
                        "nda1": {
                            "label": "not_mentioned",
                            "evidence_ids": ["2", 2, 1],
                        }
                    }
                )
            },
            {
                "answer": json.dumps(
                    {"nda1": {"label": "NotMentioned", "evidence_ids": [1, 2]}}
                )
            },
        ]
        aggregate = aggregate_results("evidence_audit", results)
        self.assertEqual(
            json.loads(aggregate["answer"]),
            {"nda1": {"label": "NotMentioned", "evidence_ids": [1, 2]}},
        )

    def test_parallel_runner_preserves_agent_order(self):
        results = run_agents_parallel(
            4,
            lambda agent_id: {"agent_id": agent_id},
        )
        self.assertEqual([result["agent_id"] for result in results], [0, 1, 2, 3])


class PoolActPublicApiTest(unittest.TestCase):
    def test_polact_name_is_only_a_delegating_compatibility_alias(self):
        import expgym.poolact as public_api
        from expgym.extras import parallel_cache as implementation

        self.assertIs(
            public_api.wrap_tools_with_poolact,
            implementation.wrap_tools_with_poolact,
        )
        self.assertIn(
            "Compatibility alias",
            public_api.wrap_tools_with_polact.__doc__ or "",
        )
        delegated = {"lookup": object()}
        tools = {}
        cache = object()
        graph = object()
        with patch.object(
            implementation,
            "wrap_tools_with_poolact",
            return_value=delegated,
        ) as primary:
            result = public_api.wrap_tools_with_polact(
                tools, cache, graph, 3
            )

        self.assertIs(result, delegated)
        primary.assert_called_once_with(
            tools, cache, graph, 3,
            clock=None,
            overhead_scale=1.0,
        )


if __name__ == "__main__":
    unittest.main()
