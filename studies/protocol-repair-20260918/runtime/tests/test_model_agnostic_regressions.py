"""Fictional model IDs, real client/loop, synthetic transport; no APIs or data.

These metamorphic checks verify identifier-independent mechanics, not that an
unobserved provider implements the Chat Completions contract or performs well.
"""
import copy
import json
import os
import unittest
from unittest import mock

from expgym.llm_clients import APIClientError, APICompletionAbortedError, OpenAICompatibleLLM
from expgym.missing_final import POLICY, mark_loop_return, score_missing
from expgym.react_loop import run_react_loop
from expgym.tool_protocol import extract_text_answer, structured_final_answer


MODELS = ("unseen-lab/Orchid-17", "other-provider/quartz-opaque", "local-without-model-family")
USAGE = {"prompt_tokens": 17, "completion_tokens": 9,
         "completion_tokens_details": {"reasoning_tokens": 6}}


def reply(message, finish="stop", usage=USAGE):
    return {"choices": [{"message": copy.deepcopy(message), "finish_reason": finish}],
            "usage": copy.deepcopy(usage)}


class Wire:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(json.loads(request.data.decode("utf-8")))
        if not self.responses:
            raise AssertionError("Unexpected additional generation or transport retry")
        return json.dumps(self.responses.pop(0), ensure_ascii=False).encode("utf-8")


class ModelAgnosticRegressionTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": ""})
        patcher.start()
        self.addCleanup(patcher.stop)

    def client(self, model, wire):
        return OpenAICompatibleLLM(api_key="synthetic-offline-credential", model=model,
            base_url="http://offline.invalid/v1", transport=wire,
            max_retries=3, retry_base_seconds=0, retry_max_seconds=0)

    def test_native_tool_history_and_result_are_independent_of_model_identifier(self):
        baseline = None
        for model in MODELS:
            for content, arguments in ((None, '{"query":"Ada"}'),
                                       ([], {"query": "Ada"})):
                with self.subTest(model=model, content=content, arguments=arguments):
                    first = {"role": "assistant", "content": content,
                        "reasoning_content": "Opaque reasoning: keep verbatim.",
                        "provider_extension": {"unrecognized": "preserve"},
                        "tool_calls": [{"id": "opaque-id", "type": "function", "function": {
                            "name": "search", "arguments": arguments}}]}
                    wire = Wire(reply(first, "tool_calls"), reply({"content": "Ada"}))
                    seen = []
                    result = run_react_loop(self.client(model, wire),
                        {"search": lambda p: seen.append(json.loads(p)) or ("Ada found", 2.)},
                        context="Find the requested person.", max_steps=2,
                        answer_evaluator=lambda answer: float(answer == "Ada"))
                    self.assertEqual(seen, [{"query": "Ada"}])
                    self.assertEqual(wire.requests[1]["messages"][-2], first)
                    self.assertEqual(wire.requests[1]["messages"][-1]["tool_call_id"], "opaque-id")
                    for request in wire.requests:
                        self.assertEqual(request["model"], model)
                        self.assertEqual(request["tool_choice"], "auto")
                        self.assertFalse(request["parallel_tool_calls"])
                    outcome = tuple(result[key] for key in
                        ("answer", "answer_perf", "evaluations", "agent_steps", "api_calls", "total_overhead"))
                    if baseline is None:
                        baseline = outcome
                    self.assertEqual(outcome, baseline)
                    self.assertEqual(outcome, ("Ada", 1., 1, 2, 2, 2.))

    def test_explicit_text_mode_and_content_parts_remain_supported(self):
        for model in MODELS:
            wire = Wire(reply({"content": [{"type": "text", "text": 'Action: search {"query":"Ada"}'}]}),
                        reply({"content": [{"type": "text", "text": "Answer: Ada"}],
                               "reasoning": "Provider-specific reasoning kept separate."}))
            result = run_react_loop(self.client(model, wire), {"search": lambda _: ("Ada", 1.)},
                                    tool_protocol="text", max_steps=2)
            self.assertEqual(result["answer"], "Ada")
            self.assertEqual(result["tool_protocol"], "text")
            for request in wire.requests:
                self.assertEqual(request["model"], model)
                self.assertNotIn("tools", request)
                self.assertNotIn("tool_choice", request)

    def test_length_reasoning_only_is_not_hidden_http_retry_or_invented_answer(self):
        for model in MODELS:
            for field in ("reasoning_content", "reasoning"):
                with self.subTest(model=model, field=field):
                    completion = reply({"content": None, field: "Unfinished reasoning."}, "length", usage=None)
                    wire = Wire(completion, completion)
                    evaluator = mock.Mock(return_value=0.)
                    result = run_react_loop(self.client(model, wire), {}, max_steps=1,
                                            answer_evaluator=evaluator)
                    self.assertEqual(len(wire.requests), 2)  # one step + recorded forced final
                    self.assertEqual([r["tool_choice"] for r in wire.requests], ["auto", "none"])
                    self.assertEqual((result["agent_steps"], result["api_calls"],
                                      result["http_request_attempts"]), (1, 2, 2))
                    self.assertIsNone(result["answer"])
                    evaluator.assert_not_called()
                    self.assertTrue(all(call["attempts"][0]["usage"] is None
                                        for call in result["usage_attempts"]))
                    mark_loop_return(result, "restricted_search", POLICY)
                    check = score_missing(result, evaluator, commit=True,
                                          float_close=lambda a, b: a == b,
                                          metrics_close=lambda a, b: a == b)
                    self.assertTrue(check["ok"])
                    evaluator.assert_called_once_with("", [])
                    self.assertIsNone(result["answer"])
                    self.assertEqual(result["scoring_input"], "")
                    self.assertEqual(len(wire.requests), 2)

    def test_rejected_reasoning_and_examples_cannot_reenter_as_raw_final(self):
        rejected = ('<think>Answer: {"x":9}</think>', '<think>Answer: {"x":9}',
                    '<analysis>Do not submit this draft.</analysis>',
                    'Thought: Example:\nAnswer: {"x":9}', '> Answer: {"x":9}',
                    '```text\nAnswer: {"x":9}\n```', '"Answer: Ada"')
        for model in MODELS:
            for text in rejected:
                self.assertIsNone(extract_text_answer(text))
                self.assertIsNone(structured_final_answer(text))
                for protocol, steps in (("native", 1), ("native", 0), ("text", 0)):
                    with self.subTest(model=model, text=text, protocol=protocol, steps=steps):
                        completion = reply({"content": text})
                        wire = Wire(*([completion] * (steps + 1)))
                        evaluator = mock.Mock(return_value=1.)
                        result = run_react_loop(self.client(model, wire), {}, max_steps=steps,
                                                tool_protocol=protocol, answer_evaluator=evaluator)
                        self.assertIsNone(result["answer"])
                        self.assertIsNone(result["answer_perf"])
                        evaluator.assert_not_called()
                        self.assertEqual(result["api_calls"], steps + 1)
                        self.assertEqual(len(wire.requests), steps + 1)
                        self.assertTrue(result["protocol_failures"][-1]["forced"])

    def test_plain_and_explicit_finals_keep_their_existing_payloads(self):
        cases = (("Ada Lovelace", "Ada Lovelace"), ('"Ada Lovelace"', '"Ada Lovelace"'),
                 ('{"text":"Action: literal </think>"}', '{"text": "Action: literal </think>"}'),
                 ('<think>draft</think>\nAnswer: Ada', "Ada"),
                 ("Answer: literal Action: text", "literal Action: text"))
        for model in MODELS:
            for text, expected in cases:
                for protocol, steps in (("native", 1), ("native", 0), ("text", 0)):
                    with self.subTest(model=model, text=text, protocol=protocol, steps=steps):
                        wire = Wire(reply({"content": text}))
                        result = run_react_loop(self.client(model, wire), {}, max_steps=steps,
                                                tool_protocol=protocol)
                        self.assertEqual(result["answer"], expected)
                        self.assertEqual(len(wire.requests), 1)

    def test_malformed_content_parts_are_errors_not_scored_empty_predictions(self):
        for model in MODELS:
            for content in ([42], [None], [{}], [{"type": None}], [{"type": " "}],
                            [{"type": "text"}], [{"type": "text", "text": 42}]):
                with self.subTest(model=model, content=content):
                    wire = Wire(reply({"content": content}), reply({"content": "Answer: rescue"}))
                    with self.assertRaises(APIClientError) as caught:
                        self.client(model, wire).generate("Task")
                    self.assertEqual(len(wire.requests), 1)
                    self.assertEqual(caught.exception.attempt_usage[0]["state"], "malformed_response")
                    self.assertEqual(caught.exception.attempt_usage[0]["usage"], USAGE)

    def test_well_formed_unknown_content_extensions_are_preserved_not_reinterpreted(self):
        for model in MODELS:
            for content in ([], [{"type": "text", "text": ""}],
                            [{"type": "future-provider-part", "opaque": {"x": 1}}]):
                wire = Wire(reply({"content": content}))
                result = self.client(model, wire).generate("Task")
                self.assertEqual(result.text, "")
                self.assertEqual(result.assistant_message["content"], content)
                self.assertEqual(len(wire.requests), 1)

    def test_explicit_provider_abort_never_executes_scores_or_resamples(self):
        for model in MODELS:
            wire = Wire(reply({"content": "Answer: partial"}, "abort"),
                        reply({"content": "Answer: rescue"}))
            evaluator = mock.Mock(return_value=1.)
            with self.assertRaises(APICompletionAbortedError):
                run_react_loop(self.client(model, wire), {}, max_steps=1,
                               answer_evaluator=evaluator, max_protocol_retries=1)
            evaluator.assert_not_called()
            self.assertEqual(len(wire.requests), 1)


if __name__ == "__main__":
    unittest.main()
