"""No-model regressions for full-configuration PoolAct graph identity.

These synthetic NAS-like payloads deliberately share the first 80 canonical
JSON characters. No evaluator, model, benchmark data, or saved run is used.
"""
import hashlib
import json
import unittest

from expgym.extras.parallel_cache import _parse_evaluate_config
from expgym.poolact import PoolActCoordinator, SharedExplorationGraph


def nas_payload(variant):
    config = {"edge_{}_{}".format(i, j): 1 if j == i + 1 else 0
              for i in range(6) for j in range(i + 1, 7)}
    config.update({"op_node_{}".format(i): "conv3x3-bn-relu"
                   for i in range(1, 6)})
    config["op_node_5"] = ("conv3x3-bn-relu", "conv1x1-bn-relu",
                           "maxpool3x3")[variant]
    return json.dumps(config, sort_keys=True, separators=(",", ":"))


class EvaluationGraphIdentityTest(unittest.TestCase):
    def setUp(self):
        self.payloads = [nas_payload(i) for i in range(3)]
        self.keys = self.payloads  # Already canonical, as required by the API.
        self.displays = [_parse_evaluate_config(p, "0.5")[1]
                         for p in self.payloads]
        self.assertGreater(len(self.keys[0]), 80)
        self.assertEqual(1, len({key[:80] for key in self.keys}))
        self.assertEqual(3, len(set(self.keys)))

    def record(self, graph, variant, agent_id=0, completion_time=0.0, perf=None):
        graph.record_evaluate_config(
            agent_id, self.keys[variant], self.displays[variant],
            perf if perf is not None else 0.1 * (variant + 1), 1.0,
            completion_time=completion_time,
        )

    def test_full_identity_is_stable_and_bounded_not_a_json_prefix(self):
        graph = SharedExplorationGraph()
        ids = [graph._eval_key(key) for key in self.keys]
        self.assertEqual(3, len(set(ids)))
        for key, node_id in zip(self.keys, ids):
            self.assertEqual("E:sha256:" + hashlib.sha256(key.encode("utf-8")).hexdigest(),
                             node_id)
            self.assertEqual(73, len(node_id))
            self.assertEqual(node_id, SharedExplorationGraph()._eval_key(key))
        long_key = json.dumps({"text": "configuration" * 1000})
        self.assertEqual(73, len(graph._eval_key(long_key)))

    def test_distinct_long_configs_do_not_create_false_self_loops(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        for i in range(3):
            self.record(graph, i)
        ids = [graph._eval_key(key) for key in self.keys]
        self.assertEqual(3, graph.stats()["eval_nodes"])
        self.assertEqual({(ids[0], ids[1]), (ids[1], ids[2])}, set(graph._edges))
        self.assertEqual(2, graph.stats()["edges"])
        self.assertTrue(all(src != dst for src, dst in graph._edges))

    def test_repeating_the_same_config_keeps_real_self_loop(self):
        graph = SharedExplorationGraph()
        self.record(graph, 0)
        self.record(graph, 0)
        node_id = graph._eval_key(self.keys[0])
        self.assertEqual(1, graph.stats()["eval_nodes"])
        self.assertEqual(2, graph.stats()["total_visits"])
        self.assertEqual({(node_id, node_id)}, set(graph._edges))
        self.assertEqual(1, graph._edges[(node_id, node_id)].count)

    def test_identical_transitions_merge_counts_not_distinct_nodes(self):
        graph = SharedExplorationGraph()
        for agent in (0, 1):
            self.record(graph, 0, agent_id=agent)
            self.record(graph, 1, agent_id=agent)
        ids = [graph._eval_key(key) for key in self.keys]
        self.assertEqual(2, graph.stats()["eval_nodes"])
        self.assertNotEqual(ids[0], ids[1])
        self.assertEqual({(ids[0], ids[1])}, set(graph._edges))
        edge = graph._edges[(ids[0], ids[1])]
        self.assertEqual(2, edge.count)
        self.assertEqual({0, 1}, edge.agents)

    def test_display_rows_bind_full_configs_to_the_path_ids(self):
        for diversity in (False, True):
            with self.subTest(diversity=diversity):
                graph = SharedExplorationGraph(diversity_mode=diversity)
                self.record(graph, 0)
                self.record(graph, 1)
                text = graph.format_for_injection()
                for key, display in zip(self.keys[:2], self.displays[:2]):
                    row = next(line for line in text.splitlines() if display in line)
                    self.assertIn(graph._eval_key(key), row)
                if diversity:
                    paths = text.split("== Exploration Paths ==", 1)[1].split(
                        "== Coverage Gap ==", 1)[0]
                    self.assertIn("{} --> {}".format(graph._eval_key(self.keys[0]),
                                                     graph._eval_key(self.keys[1])), paths)
                    self.assertNotIn("edge_", paths)

    def test_rebuilt_snapshot_preserves_ids_without_future_nodes_or_edges(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        self.record(graph, 2, agent_id=1, completion_time=30, perf=0.987654)
        self.record(graph, 0, completion_time=5)
        self.record(graph, 1, completion_time=10)
        self.record(graph, 0, completion_time=15, perf=0.876543)
        ids = [graph._eval_key(key) for key in self.keys]
        early = graph.format_for_injection(visible_before=10, agent_id=2)
        self.assertIn(ids[0], early)
        self.assertIn(ids[1], early)
        self.assertNotIn(ids[2], early)
        self.assertIn("{} --> {}".format(ids[0], ids[1]), early)
        self.assertNotIn("{} --> {}".format(ids[1], ids[0]), early)
        self.assertNotIn("0.987654", early)
        self.assertNotIn("0.876543", early)
        later = graph.format_for_injection(visible_before=20)
        self.assertIn("{} --> {}".format(ids[1], ids[0]), later)
        self.assertNotIn(ids[2], later)
        strict = graph.format_for_injection(visible_before=20, completion_before=10)
        self.assertIn(ids[0], strict)
        self.assertNotIn(ids[1], strict)
        self.assertNotIn("-->", strict)

    def test_end_nodes_still_hidden_from_time_gated_graph(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        self.record(graph, 0, completion_time=1)
        graph.record_end(0, "unpublished-final-answer")
        visible = graph.format_for_injection(visible_before=100)
        self.assertNotIn("END:", visible)
        self.assertNotIn("unpublished-final-answer", visible)


class EvaluationGraphCacheContractTest(unittest.TestCase):
    def test_full_payload_cache_and_claim_semantics_survive_graph_fix(self):
        calls = []

        def evaluate(payload):
            canonical = json.dumps(json.loads(payload), sort_keys=True,
                                   separators=(",", ":"))
            calls.append(canonical)
            return (0.8 if canonical == nas_payload(0) else 0.9, 3.0)

        coordinator = PoolActCoordinator(2)
        first = coordinator.bind_tools({"evaluate_config": evaluate}, 0, time_budget=100)
        second = coordinator.bind_tools({"evaluate_config": evaluate}, 1, time_budget=100)
        for variant, expected in ((0, 0.8), (1, 0.9)):
            payload = nas_payload(variant)
            first.pre_tool_hook("evaluate_config", payload)
            self.assertEqual((expected, 3.0), first.tools["evaluate_config"](payload))
            first.clock.advance(3.0)  # The ReAct loop owns advancement.
        second.clock.advance(10.0)
        reordered = json.dumps(dict(reversed(list(json.loads(nas_payload(0)).items()))), indent=2)
        second.pre_tool_hook("evaluate_config", reordered)
        self.assertTrue(coordinator.graph.has_pending_claim("evaluate_config", nas_payload(0), 1))
        self.assertEqual((0.8, 0.0), second.tools["evaluate_config"](reordered))
        self.assertEqual([nas_payload(0), nas_payload(1)], calls)
        self.assertEqual({"hits": 1, "misses": 2, "size": 2}, coordinator.cache.stats())
        self.assertEqual(0, coordinator.graph.stats()["pending_claims"])
        self.assertEqual(2, coordinator.graph.stats()["eval_nodes"])
        self.assertEqual(3, coordinator.graph.stats()["total_visits"])
        ids = [coordinator.graph._eval_key(nas_payload(i)) for i in (0, 1)]
        self.assertNotEqual(*ids)
        self.assertEqual({(ids[0], ids[1])}, set(coordinator.graph._edges))

    def test_future_result_is_still_a_paid_miss_then_earliest_completion_wins(self):
        coordinator = PoolActCoordinator(1)
        payload = nas_payload(0)
        coordinator.cache.put("evaluate_config", payload, (0.9, 2.0), completion_time=20)
        calls = []

        def evaluate(value):
            calls.append(value)
            return (0.4, 2.0)

        runtime = coordinator.bind_tools({"evaluate_config": evaluate}, 0, time_budget=100)
        self.assertEqual((0.4, 2.0), runtime.tools["evaluate_config"](payload))
        runtime.clock.advance(2)
        self.assertEqual((0.4, 0.0), runtime.tools["evaluate_config"](payload))
        self.assertEqual([payload], calls)
        self.assertEqual({"hits": 1, "misses": 1, "size": 1}, coordinator.cache.stats())
        text = coordinator.graph.format_for_injection(visible_before=2)
        self.assertIn("0.400000", text)
        self.assertNotIn("0.900000", text)

    def test_audit_feedback_rows_also_bind_distinct_full_payload_identities(self):
        coordinator = PoolActCoordinator(1)
        runtime = coordinator.bind_tools(
            {"human_feedback": lambda payload: ("Evidence Correct", 1.0)},
            0, time_budget=100,
        )
        keys = []
        for nda_id in (1, 2):
            payload = json.dumps({"evidence_ids": list(range(40)), "nda_id": nda_id},
                                 sort_keys=True, separators=(",", ":"))
            keys.append(payload)
            runtime.tools["human_feedback"](payload)
            runtime.clock.advance(1)
        self.assertEqual(keys[0][:80], keys[1][:80])
        ids = [coordinator.graph._eval_key(key) for key in keys]
        self.assertNotEqual(*ids)
        text = runtime.observation_augmenter("Feedback retained.")
        for nda_id, node_id in zip((1, 2), ids):
            row = next(line for line in text.splitlines() if "nda:{} ".format(nda_id) in line)
            self.assertIn(node_id, row)
            self.assertIn("Evidence Correct", row)
        self.assertIn("{} --> {}".format(*ids), text)
        self.assertIn("2 NDAs attempted so far.", text)


if __name__ == "__main__":
    unittest.main()
