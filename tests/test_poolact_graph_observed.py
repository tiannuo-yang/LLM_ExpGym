"""Regression from the saved Gemini NAS101 A Moderate graph message.

Only an already visible graph is reconstructed here. This is not a replay of
the model's actions and cannot estimate the effect of the repair on its score.
"""
import hashlib
import json
from pathlib import Path
import unittest

from expgym.extras.parallel_cache import SharedExplorationGraph


class ObservedGraphCollisionTest(unittest.TestCase):
    def test_observed_path_selects_the_actual_full_configuration(self):
        fixture = json.loads((Path(__file__).parent / "fixtures" /
                              "poolact_gemini_graph_collision.json").read_text())
        graph = SharedExplorationGraph(n_agents=4, diversity_mode=True)
        for event in fixture["events"]:
            graph.record_evaluate_config(
                event["agent_id"], event["config_key"], event["config_display"],
                event["perf"], event["cost"],
            )
        for pending in fixture["pending"]:
            graph.record_claim("evaluate_config", pending["payload"],
                               pending["agent_id"])
        message = graph.format_for_injection(visible_before=1, agent_id=0)
        keys = fixture["ambiguous_keys"]
        self.assertNotEqual(*keys)
        self.assertEqual(keys[0][:80], keys[1][:80])
        aliases = ["E:h:" + hashlib.sha256(k.encode()).hexdigest()[:12]
                   for k in keys]
        self.assertNotEqual(*aliases)
        for key, alias in zip(keys, aliases):
            event = next(e for e in fixture["events"] if e["config_key"] == key)
            self.assertIn(alias + " " + event["config_display"], message)
        paths = message.split("== Exploration Paths ==\n", 1)[1].split(
            "\n\n== Coverage Gap ==", 1)[0]
        # Agent 0 actually reached the edge_15=1 configuration. The other
        # ambiguous legacy target was evaluated by agent 2, not this path.
        self.assertEqual(1, json.loads(keys[1])["edge_15"])
        self.assertIn(" --> " + aliases[1] + " [agents 0]", paths)
        self.assertNotIn(aliases[0], paths)
        self.assertNotIn('E:{"edge_', paths)
        self.assertEqual(1, len(paths.splitlines()))
        self.assertEqual(5, graph.stats()["eval_nodes"])
        self.assertEqual(3, graph.stats()["pending_claims"])
        # Labels change; the visible feedback, agent attribution, pending
        # display and coverage summary do not.
        old = fixture["historical_graph"]
        for section in ("== In Progress ==", "== Coverage Gap =="):
            old_part = old.split(section, 1)[1].split("\n\n==", 1)[0]
            new_part = message.split(section, 1)[1].split("\n\n==", 1)[0]
            self.assertEqual(old_part, new_part)
        for event in fixture["events"]:
            old_row = next(line.strip() for line in old.splitlines()
                           if event["config_display"] + " -> " in line)
            new_row = next(line.strip() for line in message.splitlines()
                           if event["config_display"] + " -> " in line)
            self.assertEqual(old_row, new_row.split(" ", 1)[1])


if __name__ == "__main__":
    unittest.main()
