"""Synthetic bytes only: explicit provider abort is not an agent decision."""
import copy
import json
import os
import tempfile
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest import mock

from expgym.llm_clients import APIClientError, OpenAICompatibleLLM
from expgym.react_loop import run_react_loop


USAGE = {"prompt_tokens": 2901, "completion_tokens": 908,
         "total_tokens": 3809, "reasoning_tokens": 754}
CALL = {"id": "abort-call-1", "type": "function",
        "function": {"name": "evaluate_config", "arguments": '{"x":1}'}}
TOOLS = [{"type": "function", "function": {"name": "evaluate_config",
    "parameters": {"type": "object", "properties": {"x": {"type": "integer"}}}}}]


def response(reason="abort", content='Answer: {"x":1}', calls=None, usage=USAGE):
    message = {"role": "assistant", "content": content, "reasoning_content": "retained partial reasoning"}
    if calls is not None:
        message["tool_calls"] = copy.deepcopy(calls)
    return {"choices": [{"message": message, "finish_reason": reason}], "usage": copy.deepcopy(usage)}


class Transport:
    def __init__(self, *values):
        self.values = list(values)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(json.loads(request.data.decode("utf-8")))
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return json.dumps(value, ensure_ascii=False).encode("utf-8")


def client(transport):
    return OpenAICompatibleLLM(api_key="synthetic-abort-test-credential", transport=transport,
        max_retries=3, retry_base_seconds=0, retry_max_seconds=0)


def unavailable(usage=None):
    body = {"error": {"message": "synthetic temporary unavailable"}, "usage": usage}
    return urllib.error.HTTPError("http://synthetic.invalid/v1/chat/completions", 503, "unavailable", {},
                                  BytesIO(json.dumps(body).encode("utf-8")))


class ProviderAbortTests(unittest.TestCase):
    def test_abort_text_native_and_forced_none_are_terminal_without_resampling(self):
        for options, calls, content in (({}, None, 'Answer: {"x":1}'),
                ({"tools": TOOLS}, [CALL], None),
                ({"tools": TOOLS, "tool_choice": "none"}, None, 'Answer: {"x":1}')):
            with self.subTest(options=options):
                transport = Transport(response(calls=calls, content=content), response("stop"))
                with mock.patch("time.sleep") as sleep, self.assertRaises(APIClientError) as raised:
                    client(transport).generate("test", **options)
                self.assertEqual(type(raised.exception).__name__, "APICompletionAbortedError")
                self.assertEqual(raised.exception.finish_reason, "abort")
                self.assertEqual(len(transport.requests), 1)
                sleep.assert_not_called()
                attempts = raised.exception.attempt_usage
                self.assertEqual(len(attempts), 1)
                self.assertEqual(attempts[0]["state"], "error")
                self.assertEqual(attempts[0]["usage"], USAGE)
                self.assertIsNone(attempts[0]["http_status"])

    def test_abort_raw_full_message_reasoning_usage_and_finish_preserved(self):
        original = response(content=None, calls=[CALL])
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ,
                {"EXPGYM_API_DUMP_DIR": directory, "EXPGYM_RUN_ID": "synthetic-abort-dump"}):
            transport = Transport(original)
            with self.assertRaises(APIClientError):
                client(transport).generate("test", tools=TOOLS)
            paths = list(Path(directory).glob("*.json"))
            self.assertEqual(len(paths), 1)
            dump = json.loads(paths[0].read_text(encoding="utf-8"))
            self.assertEqual(dump["state"], "error")
            self.assertEqual(dump["response_json"], original)
            self.assertEqual(json.loads(dump["response_raw"]), original)
            self.assertEqual(dump["error"]["type"], "APICompletionAbortedError")
            self.assertFalse(dump["will_retry"])
            self.assertIsNone(dump["retry_delay_seconds"])
            self.assertIsNotNone(dump["finished_at_utc"])
            self.assertIsNone(dump["http_status"])
            self.assertNotIn("synthetic-abort-test-credential", paths[0].read_text(encoding="utf-8"))

    def test_retryable_503_then_abort_keeps_both_attempts(self):
        prior = {"prompt_tokens": 2, "completion_tokens": 3}
        transport = Transport(unavailable(prior), response(), response("stop"))
        with mock.patch("time.sleep") as sleep, self.assertRaises(APIClientError) as raised:
            client(transport).generate("test")
        self.assertEqual(len(transport.requests), 2)
        sleep.assert_called_once_with(0)
        attempts = raised.exception.attempt_usage
        self.assertEqual([a["state"] for a in attempts], ["error", "error"])
        self.assertEqual([a["attempt"] for a in attempts], [1, 2])
        self.assertEqual([a["usage"] for a in attempts], [prior, USAGE])
        self.assertEqual(attempts[0]["generation_id"], attempts[1]["generation_id"])
        self.assertNotEqual(attempts[0]["request_id"], attempts[1]["request_id"])

    def test_original_503_retry_still_reaches_normal_stop(self):
        transport = Transport(unavailable(), response("stop"))
        with mock.patch("time.sleep") as sleep:
            result = client(transport).generate("test")
        self.assertEqual(result.finish_reason, "stop")
        self.assertEqual(result.request_attempts, 2)
        self.assertEqual([a["state"] for a in result.attempt_usage], ["error", "success"])
        self.assertIsNone(result.attempt_usage[0]["usage"])
        sleep.assert_called_once_with(0)

    def test_normal_refusal_length_and_unknown_finish_are_not_reclassified(self):
        for reason in ("stop", "length", "content_filter", None, "provider_future_reason"):
            with self.subTest(reason=reason):
                value = response(reason, content="I cannot answer that request.")
                value["choices"][0]["message"]["refusal"] = "provider refusal"
                transport = Transport(value)
                with mock.patch("time.sleep") as sleep:
                    result = client(transport).generate("test")
                self.assertEqual(result.finish_reason, reason)
                self.assertEqual(result.assistant_message, value["choices"][0]["message"])
                self.assertEqual(result.attempt_usage[0]["state"], "success")
                sleep.assert_not_called()
        result = client(Transport(response("tool_calls", content=None, calls=[CALL]))).generate("test", tools=TOOLS)
        self.assertEqual(result.tool_calls, [CALL])

    def test_empty_reasoning_only_and_unknown_usage_remain_delivered(self):
        for reason in ("stop", "length", None):
            with self.subTest(reason=reason):
                result = client(Transport(response(reason, content=None, usage=None))).generate("test")
                self.assertEqual(result.text, "")
                self.assertIsNone(result.attempt_usage[0]["usage"])
        with self.assertRaises(APIClientError) as raised:
            client(Transport(response(usage=None))).generate("test")
        self.assertIsNone(raised.exception.attempt_usage[0]["usage"])

    def test_abort_dump_failure_preserves_original_error_and_attempt_usage(self):
        transport = Transport(response())
        llm = client(transport)
        def writer(metadata, payload, started, **kwargs):
            if kwargs["state"] == "error":
                raise OSError("synthetic terminal dump failure")
        with mock.patch.object(llm, "_dump_attempt", side_effect=writer), self.assertRaises(OSError) as raised:
            llm.generate("test")
        self.assertEqual(raised.exception.attempt_usage[0]["usage"], USAGE)
        self.assertEqual(raised.exception.attempt_usage[0]["state"], "error")
        self.assertEqual(len(transport.requests), 1)

    def test_malformed_abort_still_fails_without_weakening_existing_decoder(self):
        value = response(calls=[{"type": "function", "id": "", "function": {}}])
        transport = Transport(value, response("stop"))
        with self.assertRaises(APIClientError) as raised:
            client(transport).generate("test")
        self.assertEqual(raised.exception.attempt_usage[0]["state"], "malformed_response")
        self.assertEqual(raised.exception.attempt_usage[0]["usage"], USAGE)
        self.assertEqual(len(transport.requests), 1)

    def test_abort_cannot_execute_tool_score_repair_or_forced_final(self):
        for protocol, calls, content in (("native", [CALL], None), ("native", None, 'Answer: {"x":1}'),
                                        ("text", None, 'Action: evaluate_config({"x":1})'),
                                        ("text", None, 'Answer: {"x":1}')):
            for steps in (0, 3):
                with self.subTest(protocol=protocol, steps=steps, calls=calls):
                    transport = Transport(response(calls=calls, content=content), response("stop"))
                    tool, scorer = mock.Mock(return_value=(0.9, 1.0)), mock.Mock(return_value=0.9)
                    with self.assertRaises(APIClientError):
                        run_react_loop(client(transport), {"evaluate_config": tool}, context="synthetic task",
                            max_steps=steps, max_protocol_retries=3, tool_protocol=protocol, answer_evaluator=scorer)
                    self.assertEqual(len(transport.requests), 1)
                    tool.assert_not_called()
                    scorer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
