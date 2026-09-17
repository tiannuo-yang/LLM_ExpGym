"""Full peer observations retain tool transport and obey cached EEI semantics."""
import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

from expgym.execution_contract import UNBOUND
from expgym.extras.parallel_cache import (
    AgentClock,
    SharedObservationCache,
    SharedPeerContext,
    make_peer_context_augmenter,
    wrap_tools_with_cache,
    wrap_tools_with_peer_context,
)
from expgym.react_loop import LLMOutput, run_react_loop


def injection_records(text):
    """Decode the JSON payload between the explicit observation markers."""
    if not text:
        return []
    begin = "[BEGIN FULL PEER OBSERVATIONS]\n"
    end = "\n[END FULL PEER OBSERVATIONS]"
    assert text.startswith(begin) and text.endswith(end)
    body = text[len(begin):-len(end)]
    return json.loads(body[body.index("["):])


class SharedPeerContextTest(unittest.TestCase):
    def test_preserves_all_records_and_complete_action_and_result_strings(self):
        peers = SharedPeerContext()
        expected = []
        for index in range(47):
            payload = json.dumps({"index": index, "text": "payload-" * 30})
            result = ("result-" * 60 + str(index), {"score": index / 100}, 12.5)
            peers.record(index % 3, "evaluate_config", payload, result,
                         cache_hit=index % 4 == 0, completion_time=index)
            expected.append((payload, str(result)))
        records = injection_records(peers.format_for_injection(agent_id=99))
        self.assertEqual(47, len(records))
        for index, (record, (payload, result)) in enumerate(zip(records, expected)):
            self.assertEqual(index, record["sequence"])
            self.assertEqual({"tool": "evaluate_config", "payload": payload},
                             record["action"])
            self.assertEqual(result, record["result"])
            self.assertEqual(index % 4 == 0, record["cache_hit"])
        self.assertEqual({"total_entries": 47, "unique_entries": 35,
                          "cached_entries": 12, "agents": 3}, peers.stats())

    def test_frozen_snapshot_cannot_change_with_original_mutable_values(self):
        peers = SharedPeerContext()
        payload, output = {"query": ["first"]}, {"items": ["original"]}
        result = (output, 2.0)
        expected_payload, expected_result = str(payload), str(result)
        entry = peers.record(0, "lookup", payload, result)
        snapshot = peers.snapshot(agent_id=1)
        payload["query"].append("later")
        output["items"].append("mutation")
        peers.record(0, "lookup", "next", ("next", 1.0))
        self.assertIsInstance(snapshot, tuple)
        self.assertEqual(1, len(snapshot))
        self.assertEqual(expected_payload, snapshot[0].payload)
        self.assertEqual(expected_result, snapshot[0].result)
        with self.assertRaises(FrozenInstanceError):
            entry.result = "changed"

    def test_excludes_self_future_and_strict_budget_boundary_in_insertion_order(self):
        peers = SharedPeerContext()
        peers.record(1, "lookup", "self", ("own", 0), completion_time=0)
        peers.record(2, "lookup", "late-first", ("visible", 0), completion_time=4)
        peers.record(2, "lookup", "early-second", ("visible", 0), completion_time=2)
        peers.record(3, "lookup", "at-budget", ("hidden", 0), completion_time=5)
        peers.record(3, "lookup", "future", ("hidden", 0), completion_time=6)
        entries = peers.snapshot(agent_id=1, visible_before=5, completion_before=5)
        self.assertEqual(["late-first", "early-second"], [e.payload for e in entries])
        entries = peers.snapshot(agent_id=1, visible_before=4)
        self.assertEqual([1, 2], [e.sequence for e in entries])
        self.assertEqual(4, len(peers.snapshot(agent_id=1)))
        self.assertEqual("", peers.format_for_injection(agent_id=1, visible_before=0))

    def test_invalid_times_never_publish_or_disable_visibility(self):
        peers = SharedPeerContext()
        for invalid in (-1, float("nan"), float("inf"), True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    peers.record(0, "lookup", "{}", ("ok", 1), completion_time=invalid)
                for parameter in ("visible_before", "completion_before"):
                    with self.assertRaises(ValueError):
                        peers.snapshot(agent_id=1, **{parameter: invalid})
        self.assertEqual(0, peers.stats()["total_entries"])

    def test_concurrent_publications_produce_complete_immutable_prefixes(self):
        peers = SharedPeerContext()
        barrier = threading.Barrier(5, timeout=5)
        done = threading.Event()

        def write(agent_id):
            barrier.wait()
            for index in range(40):
                peers.record(agent_id, "lookup", str(index), ({"item": index}, 1))

        def read():
            barrier.wait()
            count = 0
            while True:
                snapshot = peers.snapshot(agent_id=99)
                self.assertEqual(list(range(len(snapshot))), [e.sequence for e in snapshot])
                self.assertTrue(all(e.result.endswith(", 1)") for e in snapshot))
                count += 1
                if done.is_set():
                    return count

        with ThreadPoolExecutor(max_workers=5) as executor:
            writers = [executor.submit(write, agent) for agent in range(4)]
            reader = executor.submit(read)
            try:
                for writer in writers:
                    writer.result(timeout=5)
            finally:
                done.set()
            self.assertGreater(reader.result(timeout=5), 0)
        entries = peers.snapshot(agent_id=99)
        self.assertEqual(160, len(entries))
        self.assertEqual(160, len({(e.agent_id, e.payload) for e in entries}))


class PeerWrapperTest(unittest.TestCase):
    def test_cached_cost_and_visibility_match_cached_strategy(self):
        for result in (("full output" * 40, 3.0), ("full output" * 40, .75, 3.0)):
            with self.subTest(tuple_size=len(result)):
                outcomes = []
                for kind in ("cached", "peer"):
                    cache, peers, clock, calls = (SharedObservationCache(),
                                                  SharedPeerContext(), AgentClock(), [])

                    def tool(payload):
                        calls.append(payload)
                        return result

                    kwargs = dict(clock=clock, overhead_scale=2, time_budget=20)
                    if kind == "peer":
                        wrapped = wrap_tools_with_peer_context(
                            {"lookup": tool}, cache, peers, 0, **kwargs)
                    else:
                        wrapped = wrap_tools_with_cache({"lookup": tool}, cache, **kwargs)
                    first = wrapped["lookup"]('{"a":1,"b":2}')
                    self.assertEqual(0, clock.now)
                    self.assertIsNone(cache.get("lookup", '{"a":1,"b":2}', visible_before=5))
                    clock.advance(6)
                    second = wrapped["lookup"]('{"b":2,"a":1}')
                    outcomes.append((first, second, len(calls), cache.stats(), clock.now))
                    if kind == "peer":
                        observed = peers.snapshot(agent_id=1)
                        self.assertEqual([False, True], [e.cache_hit for e in observed])
                        self.assertEqual([6, 6], [e.completion_time for e in observed])
                        self.assertEqual([str(first), str(second)], [e.result for e in observed])
                        self.assertEqual(result[:-1] + (0.0,), second)
                self.assertEqual(outcomes[0], outcomes[1])

    def test_pending_tool_is_absent_until_physical_completion(self):
        cache, peers = SharedObservationCache(), SharedPeerContext()
        entered, finish = threading.Event(), threading.Event()

        def tool(payload):
            entered.set()
            if not finish.wait(timeout=5):
                raise TimeoutError("test did not release the pending tool")
            return "complete", 2.0

        wrapped = wrap_tools_with_peer_context({"lookup": tool}, cache, peers, 0)
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(wrapped["lookup"], "{}")
            try:
                self.assertTrue(entered.wait(timeout=5))
                self.assertEqual((), peers.snapshot(agent_id=1))
                self.assertEqual(0, cache.stats()["size"])
            finally:
                finish.set()
            self.assertEqual(("complete", 2.0), pending.result(timeout=5))
        self.assertEqual(1, len(peers.snapshot(agent_id=1)))

    def test_at_and_after_budget_result_returns_for_accounting_but_is_not_published(self):
        for raw_cost in (5.0, 6.0):
            with self.subTest(raw_cost=raw_cost):
                cache, peers, clock = SharedObservationCache(), SharedPeerContext(), AgentClock()
                wrapped = wrap_tools_with_peer_context(
                    {"lookup": lambda _: ("withheld", raw_cost)}, cache, peers, 0,
                    clock=clock, overhead_scale=2, time_budget=10)
                self.assertEqual(("withheld", raw_cost), wrapped["lookup"]("{}"))
                self.assertEqual(0, cache.stats()["size"])
                self.assertEqual(0, peers.stats()["total_entries"])
                self.assertEqual(0, clock.now)

    def test_cache_hit_at_viewer_budget_does_not_publish_new_observation(self):
        cache, peers, clock = SharedObservationCache(), SharedPeerContext(), AgentClock()
        cache.put("lookup", "{}", ("known", 3), completion_time=3)
        wrapped = wrap_tools_with_peer_context(
            {"lookup": lambda _: self.fail("cache hit must not execute tool")},
            cache, peers, 0, clock=clock, time_budget=10)
        clock.advance(10)
        self.assertEqual(("known", 0.0), wrapped["lookup"]("{}"))
        self.assertEqual(0, peers.stats()["total_entries"])

    def test_invalid_cost_shape_and_exception_publish_nothing(self):
        invalid_results = [
            ("bad", -1), ("bad", float("nan")), ("bad", float("inf")),
            ("bad", True), ("bad", "1"), ("bad", None), ("bad", .5, -1),
            "bare output", None, ("short",), ("too", "many", "items", 1),
        ]
        for result in invalid_results:
            with self.subTest(result=result):
                cache, peers = SharedObservationCache(), SharedPeerContext()
                wrapped = wrap_tools_with_peer_context(
                    {"lookup": lambda _: result}, cache, peers, 0)
                with self.assertRaises((TypeError, ValueError)):
                    wrapped["lookup"]("{}")
                self.assertEqual(0, cache.stats()["size"])
                self.assertEqual(0, peers.stats()["total_entries"])
        cache, peers = SharedObservationCache(), SharedPeerContext()

        def fail(payload):
            raise RuntimeError("failed tool")

        wrapped = wrap_tools_with_peer_context({"lookup": fail}, cache, peers, 0)
        with self.assertRaisesRegex(RuntimeError, "failed tool"):
            wrapped["lookup"]("{}")
        self.assertEqual(0, cache.stats()["size"])
        self.assertEqual(0, peers.stats()["total_entries"])

    def test_invalid_cached_cost_is_not_hidden_by_zeroing(self):
        cache, peers = SharedObservationCache(), SharedPeerContext()
        cache.put("lookup", "{}", ("bad", float("nan")))
        wrapped = wrap_tools_with_peer_context(
            {"lookup": lambda _: self.fail("invalid cache must not fall through")},
            cache, peers, 0)
        with self.assertRaises(ValueError):
            wrapped["lookup"]("{}")
        self.assertEqual(0, peers.stats()["total_entries"])

    def test_malformed_performance_or_cost_cannot_publish_on_miss_or_hit(self):
        malformed = [
            (True, 1), (float("nan"), 1), (float("inf"), 1),
            ("output", True, 1), ("output", float("nan"), 1),
            ("output", "score", 1), ("output", .5, "1"),
        ]
        for result in malformed:
            for cache_hit in (False, True):
                with self.subTest(result=result, cache_hit=cache_hit):
                    cache, peers, calls = SharedObservationCache(), SharedPeerContext(), []
                    if cache_hit:
                        cache.put("lookup", "{}", result)

                    def tool(payload):
                        calls.append(payload)
                        return result

                    wrapped = wrap_tools_with_peer_context({"lookup": tool}, cache, peers, 0)
                    with self.assertRaises((TypeError, ValueError)):
                        wrapped["lookup"]("{}")
                    self.assertEqual(0, peers.stats()["total_entries"])
                    self.assertEqual(1 if cache_hit else 0, cache.stats()["size"])
                    self.assertEqual([] if cache_hit else ["{}"], calls)

    def test_scaled_completion_overflow_does_not_publish(self):
        cache, peers, clock = SharedObservationCache(), SharedPeerContext(), AgentClock()
        wrapped = wrap_tools_with_peer_context(
            {"lookup": lambda _: ("bad", 1e308)}, cache, peers, 0,
            clock=clock, overhead_scale=2)
        with self.assertRaises(ValueError):
            wrapped["lookup"]("{}")
        self.assertEqual(0, cache.stats()["size"])
        self.assertEqual(0, peers.stats()["total_entries"])

    def test_zero_scale_publishes_without_charging_or_advancing(self):
        cache, peers, clock = SharedObservationCache(), SharedPeerContext(), AgentClock()
        wrapped = wrap_tools_with_peer_context(
            {"lookup": lambda _: ("free", 100)}, cache, peers, 0,
            clock=clock, overhead_scale=0, time_budget=10)
        self.assertEqual(("free", 100), wrapped["lookup"]("{}"))
        self.assertEqual(0, peers.snapshot(agent_id=1)[0].completion_time)
        self.assertEqual(0, clock.now)


class PeerAugmenterContractTest(unittest.TestCase):
    def test_latest_snapshot_preserves_own_observation_and_updates_without_accumulating(self):
        peers, clock = SharedPeerContext(), AgentClock()
        augmenter = make_peer_context_augmenter(peers, agent_id=0, clock=clock, time_budget=10)
        self.assertTrue(augmenter.requires_complete_context)
        self.assertEqual("", augmenter.last_snapshot)
        self.assertEqual("own first", augmenter("own first"))
        peers.record(0, "lookup", "self", ("private", 0))
        peers.record(1, "lookup", "peer", ("visible", 2), completion_time=2)
        peers.record(1, "lookup", "at-boundary", ("hidden", 10), completion_time=10)
        self.assertEqual("own second", augmenter("own second"))
        self.assertEqual("", augmenter.last_snapshot)
        clock.advance(2)
        rendered = augmenter("own third")
        self.assertEqual("own third\n\n" + augmenter.last_snapshot, rendered)
        self.assertEqual(["peer"], [r["action"]["payload"]
                                    for r in injection_records(augmenter.last_snapshot)])
        clock.advance(8)
        again = augmenter("own fourth")
        self.assertEqual(1, again.count("[BEGIN FULL PEER OBSERVATIONS]"))
        self.assertNotIn("at-boundary", again)
        self.assertNotIn("own third", again)

    def test_invalid_policy_parameters_fail_during_construction(self):
        for invalid in (-1, float("nan"), float("inf"), True):
            for parameter in ("overhead_scale", "time_budget"):
                with self.subTest(parameter=parameter, invalid=invalid):
                    with self.assertRaises(ValueError):
                        wrap_tools_with_peer_context(
                            {}, SharedObservationCache(), SharedPeerContext(), 0,
                            clock=AgentClock(), **{parameter: invalid})
            with self.assertRaises(ValueError):
                make_peer_context_augmenter(SharedPeerContext(), agent_id=0,
                                            clock=AgentClock(), time_budget=invalid)
        with self.assertRaisesRegex(ValueError, "AgentClock"):
            wrap_tools_with_peer_context({}, SharedObservationCache(), SharedPeerContext(),
                                         0, time_budget=10)
        with self.assertRaisesRegex(ValueError, "AgentClock"):
            make_peer_context_augmenter(SharedPeerContext(), agent_id=0, time_budget=10)

    def test_conflicting_nested_wrapper_does_not_bind_new_clock(self):
        first, second = AgentClock(), AgentClock()
        inner = wrap_tools_with_cache({"lookup": lambda _: ("ok", 1)},
                                      SharedObservationCache(), clock=first, time_budget=10)
        with self.assertRaisesRegex(ValueError, "agent_clock identity"):
            wrap_tools_with_peer_context(inner, SharedObservationCache(), SharedPeerContext(),
                                         0, clock=second, time_budget=10)
        self.assertFalse(hasattr(second, "__expgym_execution_contract__"))

    def test_augmenter_binds_budget_and_wrapper_can_supply_scale(self):
        clock, peers = AgentClock(), SharedPeerContext()
        augmenter = make_peer_context_augmenter(peers, agent_id=0, clock=clock, time_budget=10)
        self.assertIs(clock.__expgym_execution_contract__.overhead_scale, UNBOUND)
        wrapped = wrap_tools_with_peer_context(
            {"lookup": lambda _: ("ok", 5)}, SharedObservationCache(), peers, 0,
            clock=clock, time_budget=10, overhead_scale=0)
        self.assertEqual(("ok", 5), wrapped["lookup"]("{}"))
        self.assertEqual("own", augmenter("own"))
        with self.assertRaisesRegex(ValueError, "time_budget mismatch"):
            make_peer_context_augmenter(peers, agent_id=0, clock=clock, time_budget=11)

    def test_loop_contract_mismatch_rejected_before_model_or_tool(self):
        class Replay:
            def __init__(self):
                self.calls = 0

            def generate(self, messages):
                self.calls += 1
                return LLMOutput("Answer: done")

        clock, peers, tool_calls = AgentClock(), SharedPeerContext(), []

        def tool(payload):
            tool_calls.append(payload)
            return "ok", 1

        wrapped = wrap_tools_with_peer_context(
            {"lookup": tool}, SharedObservationCache(), peers, 0,
            clock=clock, time_budget=10, overhead_scale=2)
        augmenter = make_peer_context_augmenter(peers, agent_id=0, clock=clock, time_budget=10)
        for changes in ({"time_budget": 11}, {"overhead_scale": 1},
                        {"agent_clock": AgentClock()}):
            with self.subTest(changes=changes):
                kwargs = dict(agent_clock=clock, time_budget=10, overhead_scale=2,
                              observation_augmenter=augmenter)
                kwargs.update(changes)
                llm = Replay()
                with self.assertRaisesRegex(ValueError, "Execution contract"):
                    run_react_loop(llm, wrapped, max_steps=1, **kwargs)
                self.assertEqual(0, llm.calls)
                self.assertEqual([], tool_calls)


if __name__ == "__main__":
    unittest.main()
