#!/usr/bin/env python3
"""Only in-memory fixtures; does not read full_v3 results or call official code."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compute

GOLD = {"a": {"choice": "Entailment", "spans": [1, 2]},
        "b": {"choice": "NotMentioned", "spans": []}}
CORRECT = {"a": {"label": "Entailment", "evidence_ids": [1, 2]},
           "b": {"label": "NotMentioned", "evidence_ids": []}}


class ScoreTests(unittest.TestCase):
    def score(self, prediction, tools=()):
        return compute.score_answer(json.dumps(prediction), GOLD, tools)

    def test_evidence_is_independent_of_label(self):
        prediction = copy.deepcopy(CORRECT)
        prediction["a"]["label"] = prediction["b"]["label"] = "wrong"
        score = self.score(prediction)
        self.assertEqual((score["label_acc"], score["evidence_acc"], score["fully_correct"]), (0, 1, 0))
        self.assertIsNone(score["verification_eff"])

    def test_missing_hypothesis_not_empty_entry(self):
        self.assertEqual(self.score({})["evidence_acc"], 0)
        self.assertEqual(self.score({"a": {}, "b": {}})["evidence_acc"], .5)

    def test_label_aliases_not_normalized_by_score(self):
        prediction = copy.deepcopy(CORRECT)
        prediction["a"]["label"], prediction["b"]["label"] = "entailed", "neutral"
        self.assertEqual(self.score(prediction)["label_acc"], 0)

    def test_cleanup_fence_and_semicolon(self):
        text = "```json\n" + json.dumps(CORRECT) + "\n```;"
        score = compute.score_answer(text, GOLD)
        self.assertEqual((score["label_acc"], score["evidence_acc"], score["parse_mode"]), (1, 1, "cleanup_json"))

    def test_invalid_and_nonobject(self):
        for text in ("broken", "[]", "null", '"text"'):
            score = compute.score_answer(text, GOLD)
            self.assertEqual((score["label_acc"], score["evidence_acc"]), (0, 0))

    def test_invalid_prediction_exits_before_bad_tool_argument(self):
        for answer in ("not json", "[]"):
            score = compute.score_answer(answer, GOLD, [("human_feedback", {}, None)])
            self.assertEqual((score["label_acc"], score["evidence_acc"], score["verification_eff"]), (0, 0, None))

    def test_inner_nonfinite_preserves_score_and_serializes_diagnostics(self):
        score = compute.score_answer('{"b":{"label":"NotMentioned","evidence_ids":[NaN,Infinity]}}', GOLD)
        self.assertEqual((score["label_acc"], score["evidence_acc"]), (.5, .5))
        self.assertEqual(score["hypotheses"][1]["predicted_evidence_raw"],
                         [{"$python_json_nonfinite": "nan"}, {"$python_json_nonfinite": "inf"}])
        json.dumps(score, allow_nan=False)

    def test_inner_duplicate_keys_last_wins(self):
        score = compute.score_answer('{"b":{"label":"wrong"},"b":{"label":"NotMentioned"}}', GOLD)
        self.assertEqual((score["label_acc"], score["evidence_acc"]), (.5, .5))

    def test_whole_evidence_conversion_failure(self):
        prediction = {"b": {"label": "wrong", "evidence_ids": [1, "bad"]}}
        score = self.score(prediction)
        self.assertEqual(score["evidence_acc"], .5)
        self.assertTrue(score["hypotheses"][1]["evidence_conversion_failed"])

    def test_numeric_strings_duplicates_bool_and_float_follow_int(self):
        for values in (["1", 2, 2], [True, 2.9], "12", {"1": "ignored", "2": None}):
            prediction = copy.deepcopy(CORRECT)
            prediction["a"]["evidence_ids"] = values
            self.assertEqual(self.score(prediction)["evidence_acc"], 1)

    def test_feedback_result_ignored_first_list_payload_only(self):
        tools = [("human_feedback", json.dumps([{"nda_id": "a", "evidence_ids": [2, 1]},
                                                 {"nda_id": "b", "evidence_ids": []}]), "withheld_or_bad_result")]
        score = self.score(CORRECT, tools)
        self.assertEqual(score["verification_eff"], .5)

    def test_bad_tool_payloads_not_verified(self):
        tools = [("other", '{"nda_id":"a","evidence_ids":[1,2]}', None),
                 ("human_feedback", "bad", None),
                 ("human_feedback", '{"nda_id":"a","evidence_ids":"12"}', None),
                 ("human_feedback", '{"nda_id":"b","evidence_ids":["bad"]}', None)]
        self.assertEqual(self.score(CORRECT, tools)["verification_eff"], 0)


class VotingTests(unittest.TestCase):
    def vote(self, entries):
        return compute.vote_answers([json.dumps({"a": entry}) for entry in entries])

    def test_label_tie_first_agent(self):
        entries = [{"label": label, "evidence_ids": [index]} for index, label in enumerate(
            ("Contradiction", "Entailment", "Entailment", "Contradiction"))]
        answer, diagnostics = self.vote(entries)
        self.assertEqual(json.loads(answer)["a"], {"label": "Contradiction", "evidence_ids": [0]})
        self.assertTrue(diagnostics[0]["label_tie"])
        self.assertTrue(diagnostics[0]["evidence_tie"])
        self.assertEqual(diagnostics[0]["winning_label_agent_indices"], [0, 3])

    def test_evidence_votes_only_winning_label_and_as_whole_set(self):
        entries = [{"label": "Entailment", "evidence_ids": [1]}, {"label": "Contradiction", "evidence_ids": [9]},
                   {"label": "Entailment", "evidence_ids": [2]}, {"label": "Entailment", "evidence_ids": [1, 2]}]
        answer, diagnostics = self.vote(entries)
        self.assertEqual(json.loads(answer)["a"]["evidence_ids"], [1])
        self.assertEqual(diagnostics[0]["winning_label_agent_indices"], [0, 2, 3])

    def test_aliases_only_for_vote_and_set_normalization(self):
        entries = [{"label": "entailed", "evidence_ids": ["2", 1, 1]}, {"label": "Entailment", "evidence_ids": [1, 2]},
                   {"label": "NEUTRAL", "evidence_ids": []}, {"label": "Not Mentioned", "evidence_ids": []}]
        answer, _ = self.vote(entries)
        self.assertEqual(json.loads(answer)["a"], {"label": "Entailment", "evidence_ids": [1, 2]})

    def test_fenced_answer_abstains_in_vote(self):
        text = "```json\n" + json.dumps(CORRECT) + "\n```"
        self.assertEqual(compute.score_answer(text, GOLD)["label_acc"], 1)
        answer, diagnostics = compute.vote_answers([text, "bad", "[]", "null"])
        self.assertEqual((answer, diagnostics), ("{}", []))

    def test_missing_entry_abstains(self):
        answer, diagnostics = compute.vote_answers(['{}', '{"a":null}', '{"a":{}}', '{"a":{"label":"Entailment"}}'])
        self.assertEqual(json.loads(answer)["a"]["label"], "")
        self.assertEqual(diagnostics[0]["voting_agent_indices"], [2, 3])

    def test_vote_conversion_is_per_element(self):
        self.assertEqual(compute.canonical_vote_evidence([2, "bad", 2]), (2, "bad"))
        self.assertEqual(compute.canonical_vote_evidence("12"), ())
        self.assertEqual(compute.canonical_vote_evidence([2, 10]), (10, 2))
        with self.assertRaises(OverflowError):
            compute.canonical_vote_evidence([float("inf")])

    def test_aggregate_feedback_is_not_union_of_agent_feedback(self):
        answer, _ = compute.vote_answers([json.dumps(CORRECT)] * 4)
        self.assertEqual(compute.score_answer(answer, GOLD, [])["verification_eff"], 0)


class TraceAndCoverageTests(unittest.TestCase):
    def trace(self, content):
        return {"outcome": {"answer_message_id": "m1"}, "messages": [{"id": "m1", "role": "assistant", "content": content}], "tool_calls": []}

    def test_first_line_start_answer_not_embedded_quote(self):
        content = 'Thought: user said Answer: fake\n- Answer: {"b":{}}\nAnswer: later'
        self.assertEqual(compute.extract_final(self.trace(content))[0], '{"b":{}}\nAnswer: later')

    def test_override_has_priority(self):
        trace = self.trace("Answer: wrong")
        trace["outcome"]["answer_override"] = "actual"
        self.assertEqual(compute.extract_final(trace), ("actual", "outcome.answer_override"))

    def test_empty_answer_uses_whole_content(self):
        self.assertEqual(compute.extract_final(self.trace("Answer:"))[0], "Answer:")

    def test_raw_text_tool_wrapper(self):
        trace = {"tool_calls": [{"name": "human_feedback", "arguments": {"raw": '{"nda_id":"b","evidence_ids":[]}', "encoding": "text"}}]}
        tools = compute.trace_tools(trace)
        self.assertEqual(tools[0][1], '{"nda_id":"b","evidence_ids":[]}')
        self.assertEqual(compute.score_answer(json.dumps(CORRECT), GOLD, tools)["verification_eff"], .5)

    def test_missing_partition_not_zero_filled(self):
        manifest = {"jobs": [], "source_tree_sha256": compute.EXPECTED_SOURCE_TREE}
        with patch.object(compute, "read", return_value=manifest), patch.object(compute, "ref", return_value={"path": "synthetic", "sha256": "synthetic"}):
            report = compute.run("synthetic")
        self.assertFalse(report["complete"])
        self.assertIsNone(report["metrics"])
        self.assertTrue(report["readiness"]["issues"])
        self.assertNotIn("traces", report)

    def test_doc_then_rep_equal_weight(self):
        traces, results = [], []
        for regime in compute.REGIMES:
            for index in range(13):
                for rep in range(3):
                    traces.append({"system": "expgym", "item_index": index, "regime": regime, "strategy": None,
                                   "path": str((regime, index, rep)), "label_acc": index / 12, "evidence_acc": rep / 2})
                for strategy in compute.STRATEGIES:
                    results.append({"system": "poolact", "item_index": index, "regime": regime, "strategy": strategy,
                                    "path": str((regime, index, strategy)), "label_acc": index / 12, "evidence_acc": .25,
                                    "mean_individual_label_acc": .5, "mean_individual_evidence_acc": .75})
        metrics = compute.build_metrics(traces, results)
        self.assertEqual((len(metrics["document_metrics"]), len(metrics["aggregate_metrics"])), (546, 42))
        for row in metrics["aggregate_metrics"]:
            expected = 50 if row["system"] == "expgym" or row["metric"] in ("LA_pct", "MI_LA_pct") else {"EA_pct": 25, "MI_EA_pct": 75}[row["metric"]]
            self.assertAlmostEqual(row["value"], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
