"""No-model regressions for full-configuration PoolAct graph identity.

These synthetic NAS-like payloads deliberately share the first 80 canonical
JSON characters. No evaluator, model, benchmark data, or saved run is used.
"""
import hashlib
import json
import unittest
from unittest.mock import patch

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
                aliases = graph._eval_display_keys(graph._eval_nodes)
                text = graph.format_for_injection()
                for key, display in zip(self.keys[:2], self.displays[:2]):
                    row = next(line for line in text.splitlines() if display in line)
                    self.assertIn(aliases[graph._eval_key(key)], row)
                if diversity:
                    paths = text.split("== Exploration Paths ==", 1)[1].split(
                        "== Coverage Gap ==", 1)[0]
                    self.assertIn("{} --> {}".format(aliases[graph._eval_key(self.keys[0])],
                                                     aliases[graph._eval_key(self.keys[1])]), paths)
                    self.assertNotIn("edge_", paths)

    def test_rebuilt_snapshot_preserves_ids_without_future_nodes_or_edges(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        self.record(graph, 2, agent_id=1, completion_time=30, perf=0.987654)
        self.record(graph, 0, completion_time=5)
        self.record(graph, 1, completion_time=10)
        self.record(graph, 0, completion_time=15, perf=0.876543)
        aliases = graph._eval_display_keys(graph._eval_nodes)
        ids = [aliases[graph._eval_key(key)] for key in self.keys]
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
        aliases = coordinator.graph._eval_display_keys(coordinator.graph._eval_nodes)
        ids = [aliases[coordinator.graph._eval_key(key)] for key in keys]
        self.assertNotEqual(*ids)
        text = runtime.observation_augmenter("Feedback retained.")
        for nda_id, node_id in zip((1, 2), ids):
            row = next(line for line in text.splitlines() if "nda:{} ".format(nda_id) in line)
            self.assertIn(node_id, row)
            self.assertIn("Evidence Correct", row)
        self.assertIn("{} --> {}".format(*ids), text)
        self.assertIn("2 NDAs attempted so far.", text)


class CompactEvaluationDisplayTest(unittest.TestCase):
    def test_short_audit_graph_is_byte_equivalent_to_legacy_display(self):
        graph = SharedExplorationGraph(n_agents=2, diversity_mode=True)
        for nda_id in (1, 2):
            key = json.dumps({"evidence_ids": [1], "nda_id": nda_id},
                             sort_keys=True, separators=(",", ":"))
            graph.record_evaluate_config(0, key,
                                         "nda:{}  ev:[1]  [Evidence Correct]".format(nda_id),
                                         1.0, 1.0, completion_time=nda_id)
        expected = "\n".join([
            "[Parallel Exploration — Agent 1 of 2]",
            "You are one of 2 agents solving this task in parallel.",
            "Shared state below shows what other agents have explored and are exploring.",
            "Use this to plan your next action — prioritize paths not yet explored.",
            "", "== In Progress ==", "  None.", "", "== Already Explored ==",
            "  nda:1  ev:[1]  [Evidence Correct] [agents 0]",
            "  nda:2  ev:[1]  [Evidence Correct] [agents 0]",
            "", "== Exploration Paths ==",
            '  E:{"evidence_ids":[1],"nda_id":1} --> E:{"evidence_ids":[1],"nda_id":2} [agents 0]',
            "", "== Coverage Gap ==", "  2 NDAs attempted so far.",
        ])
        self.assertEqual(expected, graph.format_for_injection(visible_before=2, agent_id=1))

    def test_short_default_tuning_graph_is_byte_equivalent_to_legacy_display(self):
        graph = SharedExplorationGraph(n_agents=2)
        graph.record_evaluate_config(0, '{"x":1}', '{x:1}', 0.5, 2.0)
        expected = "\n".join([
            "[Shared Exploration Graph]", "You are one of 2 agents tuning in parallel.",
            "Use this to avoid redundant configs and learn from others' results.",
            "Cached evaluations cost 0s.", "", "=== Evaluated Configs ===",
            "  {x:1} -> perf=0.500000, cost=2s (1x by [0])",
            "", "=== Best So Far ===", "  perf=0.500000 {x:1} (by agent 0)",
        ])
        self.assertEqual(expected, graph.format_for_injection())

    def test_80_character_boundary_and_mixed_short_long_paths(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        keys = [json.dumps({"x": "a" * (length - 8)}, separators=(",", ":"))
                for length in (80, 81)]
        self.assertEqual([80, 81], list(map(len, keys)))
        for key in keys:
            graph.record_evaluate_config(0, key, key, 0.5, 1.0)
        aliases = graph._eval_display_keys(graph._eval_nodes)
        self.assertEqual("E:" + keys[0], aliases[graph._eval_key(keys[0])])
        long_alias = aliases[graph._eval_key(keys[1])]
        self.assertEqual("E:h:" + hashlib.sha256(keys[1].encode()).hexdigest()[:12], long_alias)
        text = graph.format_for_injection()
        self.assertIn("\n  {} -> 0.500000".format(keys[0]), text)
        self.assertIn("\n  {} {} -> 0.500000".format(long_alias, keys[1]), text)
        self.assertIn("E:{} --> {}".format(keys[0], long_alias), text)

    @staticmethod
    def colliding_digest(_graph, key):
        variant = [nas_payload(i) for i in range(3)].index(key)
        return "E:sha256:" + "0" * 12 + str(variant) + "0" * 51

    def test_colliding_prefixes_extend_all_aliases_independent_of_node_order(self):
        with patch.object(SharedExplorationGraph, "_eval_key", self.colliding_digest):
            maps = []
            for order in ((0, 1, 2), (2, 1, 0)):
                graph = SharedExplorationGraph(diversity_mode=True)
                for i in order:
                    graph.record_evaluate_config(0, nas_payload(i), "config {}".format(i), 0.5, 1.0)
                aliases = graph._eval_display_keys(graph._eval_nodes)
                self.assertEqual(3, len(set(aliases.values())))
                self.assertTrue(all(len(alias) == 17 for alias in aliases.values()))
                self.assertNotIn("E:h:" + "0" * 12, aliases.values())
                text = graph.format_for_injection()
                for i in order:
                    self.assertIn("{} config {}".format(aliases[graph._eval_key(nas_payload(i))], i), text)
                maps.append(aliases)
            self.assertEqual(*maps)

    def test_future_prefix_collision_does_not_change_past_visible_aliases(self):
        with patch.object(SharedExplorationGraph, "_eval_key", self.colliding_digest):
            graph = SharedExplorationGraph(diversity_mode=True)
            graph.record_evaluate_config(0, nas_payload(0), "visible config", 0.5, 1.0,
                                         completion_time=1)
            before = graph.format_for_injection(visible_before=1)
            graph.record_evaluate_config(0, nas_payload(1), "future config", 0.9, 1.0,
                                         completion_time=10)
            self.assertEqual(before, graph.format_for_injection(visible_before=1))
            self.assertEqual(before, graph.format_for_injection(visible_before=10, completion_before=10))
            after = graph.format_for_injection(visible_before=10)
            old_alias = "E:h:" + "0" * 12
            self.assertIn(old_alias + " visible config", before)
            self.assertNotIn(old_alias + " ", after)
            self.assertIn(old_alias + "0 visible config", after)
            self.assertIn(old_alias + "1 future config", after)

    def test_full_digest_collision_fails_before_graph_state_mutation(self):
        graph = SharedExplorationGraph()
        with patch.object(SharedExplorationGraph, "_eval_key", return_value="E:sha256:" + "0" * 64):
            graph.record_evaluate_config(0, nas_payload(0), "first", 0.5, 1.0)
            before = (graph.stats(), list(graph._observations), dict(graph._agent_last_node),
                      dict(graph._eval_key_payloads))
            with self.assertRaisesRegex(ValueError, "identity digest collision"):
                graph.record_evaluate_config(0, nas_payload(1), "second", 0.8, 1.0)
            after = (graph.stats(), list(graph._observations), dict(graph._agent_last_node),
                     dict(graph._eval_key_payloads))
            self.assertEqual(before, after)

    def test_short_and_long_display_namespace_collision_is_not_silent(self):
        # Normal canonical dict/list keys cannot start with 'h:'. Even direct
        # library misuse must not silently create a short/long alias collision.
        graph = SharedExplorationGraph()
        long_key = nas_payload(0)
        digest = hashlib.sha256(long_key.encode()).hexdigest()
        short_key = "h:" + digest[:12]
        for key in (short_key, long_key):
            graph.record_evaluate_config(0, key, key, 0.5, 1.0)
        aliases = graph._eval_display_keys(graph._eval_nodes)
        self.assertEqual("E:" + short_key, aliases[graph._eval_key(short_key)])
        self.assertEqual("E:h:" + digest[:13], aliases[graph._eval_key(long_key)])
        self.assertEqual(2, len(set(aliases.values())))

    def test_full_width_display_namespace_collision_fails_closed(self):
        graph = SharedExplorationGraph()
        long_key = nas_payload(0)
        digest = hashlib.sha256(long_key.encode()).hexdigest()
        for width in range(12, 65):
            key = "h:" + digest[:width]
            graph.record_evaluate_config(0, key, key, 0.5, 1.0)
        graph.record_evaluate_config(0, long_key, long_key, 0.5, 1.0)
        with self.assertRaisesRegex(ValueError, "distinct evaluation graph display IDs"):
            graph.format_for_injection()


if __name__ == "__main__":
    unittest.main()
