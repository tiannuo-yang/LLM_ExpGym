"""JSON answer matching without changing observation, cost or fallback rules."""
import json
import unittest

from expgym.react_loop import (
    LLMOutput, _canonicalize_payload, _lookup_answer_metrics, run_react_loop,
)
from scripts.run_paper_sweep import _score_result


class RecordedReplies:
    def __init__(self, replies):
        self.replies = iter(replies)

    def generate(self, messages):
        return LLMOutput(text=next(self.replies))


class JsonAnswerLookupTest(unittest.TestCase):
    def test_json_objects_and_arrays_require_complete_canonical_match(self):
        for raw, equivalent in [('{"x": 1, "y": 2}', '{ "y":2,"x":1 }'),
                                ('[1, 2]', '[ 1,2 ]')]:
            with self.subTest(raw=raw):
                records = [(raw, _canonicalize_payload(raw), 0.0, 7.0)]
                self.assertEqual(_lookup_answer_metrics(equivalent, records), (0.0, 7.0))
                for invalid in ["selected " + raw, raw + "\nExplanation", raw + "\nAnswer: " + raw]:
                    self.assertEqual(_lookup_answer_metrics(invalid, records), (None, None))
                records.append((equivalent, _canonicalize_payload(equivalent), 0.7, 0.0))
                self.assertEqual(_lookup_answer_metrics(raw, records), (0.7, 0.0))

    def test_non_json_identifiers_keep_historical_matching(self):
        records = [("cfg_1", None, 0.4, 3.0)]
        self.assertEqual(_lookup_answer_metrics("I choose cfg_1", records), (0.4, 3.0))
        self.assertEqual(_lookup_answer_metrics('{"id":"cfg_1"}', records), (None, None))
        self.assertEqual(_lookup_answer_metrics("anything", []), (None, None))

    def test_known_zero_unseen_and_multiple_answers_keep_existing_fallback(self):
        configs = ['{"x": 1}', '{"x": 2}', '{"x": 3}']
        scores = {1: 0.9, 2: 0.4, 3: 0.0}

        def tool(payload):
            perf = scores[json.loads(payload)["x"]]
            if perf == 0:
                return "perf=0.000000 (invalid or degenerate configuration)", 0.0, 1.0
            return perf, 1.0

        cases = [
            ("Answer: " + configs[1], configs[1], 0.4, "natural_model_answer"),
            ("Answer: " + configs[2], configs[2], 0.0, "natural_model_answer"),
            ('Answer: {"x": 99}', configs[0], 0.9, "best_evaluated_fallback"),
            ("Answer: I should continue exploring.\n\nAnswer: " + configs[1], configs[0], 0.9, "best_evaluated_fallback"),
            ("Answer: " + configs[1] + "\nAnswer: " + configs[2], configs[0], 0.9, "best_evaluated_fallback"),
        ]
        for final, expected_answer, expected_perf, source in cases:
            with self.subTest(final=final):
                replies = ["Action: evaluate_config " + config for config in configs] + [final]
                result = run_react_loop(llm=RecordedReplies(replies), tools={"evaluate_config": tool}, max_steps=5, capture_trace_v2=True)
                self.assertEqual(result["answer"], expected_answer)
                self.assertEqual(result["answer_perf"], expected_perf)
                self.assertEqual(result["_trace_v2_capture"]["answer_source"], source)
                self.assertEqual(result["evaluations"], 3)
                self.assertEqual(result["api_calls"], 4)
                self.assertEqual(result["total_overhead"], 3.0)
                self.assertEqual([record[0] for record in result["eval_records"]], configs)
                self.assertTrue(_score_result(result, {"evaluate_config": tool}, None)["ok"])

    def test_fallback_excludes_withheld_best_and_preserves_visible_zero(self):
        for visible_perf in (0.4, 0.0):
            with self.subTest(visible_perf=visible_perf):
                def tool(payload):
                    return (visible_perf, 1.0) if json.loads(payload)["x"] == 1 else (0.99, 10.0)

                replies = ['Action: evaluate_config {"x": 1}',
                           'Action: evaluate_config {"x": 2}',
                           'Answer: deliberating\nAnswer: {"x": 2}']
                result = run_react_loop(llm=RecordedReplies(replies), tools={"evaluate_config": tool}, time_budget=5.0, max_steps=4, capture_trace_v2=True)
                self.assertEqual(result["answer"], '{"x": 1}')
                self.assertEqual(result["answer_perf"], visible_perf)
                self.assertEqual(len(result["eval_records"]), 1)
                self.assertEqual(result["evaluations"], 2)
                self.assertEqual(result["api_calls"], 3)
                self.assertEqual(result["total_overhead"], 11.0)
                self.assertFalse(result["_trace_v2_capture"]["tool_calls"][1]["visible_to_model"])
                self.assertNotIn("perf=0.990000", "\n".join(message["content"] for message in result["messages"]))

    def test_no_visible_evaluations_keep_existing_offline_score_boundary(self):
        cases = [
            ("invalid_config", None, 'Answer: {"x": 1}', 0.0),
            ("valid", 1.0, 'Answer: {"x": 1}', 0.99),
            ("valid", 1.0, 'Answer: deliberating\nAnswer: {"x": 1}', 0.0),
        ]
        for mode, budget, final, expected in cases:
            with self.subTest(mode=mode, final=final):
                def tool(payload):
                    try:
                        json.loads(payload)
                    except json.JSONDecodeError:
                        return "Invalid JSON payload: rejected", 0.0
                    if mode == "invalid_config":
                        return "Invalid config: missing parameter", 0.0
                    return 0.99, 10.0

                replies = ['Action: evaluate_config {"x": 1}', final]
                result = run_react_loop(llm=RecordedReplies(replies), tools={"evaluate_config": tool}, time_budget=budget, max_steps=3, capture_trace_v2=True)
                self.assertEqual(result["eval_records"], [])
                self.assertIsNone(result["answer_perf"])
                self.assertNotEqual(result["_trace_v2_capture"]["answer_source"], "best_evaluated_fallback")
                messages_before = list(result["messages"])
                self.assertTrue(_score_result(result, {"evaluate_config": tool}, None)["ok"])
                self.assertEqual(result["answer_perf"], expected)
                self.assertEqual(result["answer_score_source"], "offline_final_answer")
                self.assertEqual(result["messages"], messages_before)
                self.assertEqual(result["evaluations"], 1)
                self.assertEqual(result["api_calls"], 2)


if __name__ == "__main__":
    unittest.main()
