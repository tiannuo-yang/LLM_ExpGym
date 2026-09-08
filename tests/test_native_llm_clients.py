"""Offline transport tests for portable Chat Completions native tools."""
import copy
import http.client
import json
import os
import tempfile
import unittest
import urllib.error
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest import mock

from expgym.llm_clients import APIClientError, OpenAICompatibleLLM


TOOLS = [{
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the local environment.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}]


def _call(arguments='{"query": "Ada"}', call_id="call_1"):
    return {
        "id": call_id, "type": "function",
        "function": {"name": "search", "arguments": arguments},
    }


def _response(message, finish_reason="tool_calls"):
    return {
        "choices": [{"message": message, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5},
    }


class _Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(json.loads(request.data.decode("utf-8")))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        if isinstance(response, bytes):
            return response
        return json.dumps(response, ensure_ascii=False).encode("utf-8")


class NativeLLMClientTest(unittest.TestCase):
    def _client(self, transport, **kwargs):
        return OpenAICompatibleLLM(
            api_key="native-client-test-credential", transport=transport,
            max_retries=kwargs.pop("max_retries", 0), retry_base_seconds=0,
            **kwargs,
        )

    def test_tool_only_response_is_success_without_empty_content_retry(self):
        for content in (None, "", "  ", []):
            with self.subTest(content=content):
                message = {
                    "role": "assistant", "content": content,
                    "reasoning_content": "Private reasoning retained for continuation.",
                    "tool_calls": [_call()],
                }
                transport = _Transport(_response(message))
                client = self._client(transport, max_retries=2)
                output = client.generate("Find Ada", tools=TOOLS)
                self.assertTrue(client.supports_native_tools)
                self.assertEqual(output.text, "")
                self.assertEqual(output.tool_calls, [_call()])
                self.assertEqual(output.assistant_message, message)
                self.assertEqual(output.finish_reason, "tool_calls")
                self.assertEqual(output.prompt_tokens, 12)
                self.assertEqual(output.completion_tokens, 5)
                self.assertEqual(output.request_attempts, 1)
                self.assertEqual(len(transport.requests), 1)

    def test_content_can_be_absent_for_valid_tool_call(self):
        message = {"tool_calls": [_call()]}
        transport = _Transport(_response(message))
        output = self._client(transport).generate("Find Ada", tools=TOOLS)
        self.assertEqual(output.text, "")
        self.assertEqual(output.assistant_message, {"role": "assistant", **message})

    def test_native_request_defaults_and_explicit_forced_final(self):
        for choice in (None, "none", "required", {"type": "function", "function": {"name": "search"}}):
            with self.subTest(choice=choice):
                transport = _Transport(_response({"content": "Answer: Ada"}, "stop"))
                definitions = copy.deepcopy(TOOLS)
                output = self._client(transport).generate(
                    "Find Ada", tools=definitions, tool_choice=choice,
                )
                payload = transport.requests[0]
                self.assertEqual(payload["tools"], TOOLS)
                self.assertEqual(payload["tool_choice"], "auto" if choice is None else choice)
                self.assertIs(payload["parallel_tool_calls"], False)
                self.assertEqual(definitions, TOOLS)
                self.assertEqual(output.text, "Answer: Ada")
                self.assertEqual(output.tool_calls, [])

    def test_unset_tools_preserves_legacy_payload(self):
        transport = _Transport(_response({"content": "Answer: Ada"}, "stop"))
        self._client(transport).generate("Find Ada")
        for key in ("tools", "tool_choice", "parallel_tool_calls"):
            self.assertNotIn(key, transport.requests[0])

    def test_explicit_none_without_tools_is_not_dropped(self):
        transport = _Transport(_response({"content": "Answer: Ada"}, "stop"))
        self._client(transport).generate("Find Ada", tool_choice="none")
        self.assertEqual(transport.requests[0]["tool_choice"], "none")
        self.assertNotIn("tools", transport.requests[0])

    def test_dict_arguments_are_normalized_separately_from_original_message(self):
        original = {
            "role": "assistant", "content": None,
            "reasoning_content": "Preserve me.",
            "tool_calls": [_call({"query": "中文", "nested": {"limit": 1}})],
            "provider_extension": {"opaque": [1, 2]},
        }
        transport = _Transport(_response(original))
        output = self._client(transport).generate("Find", tools=TOOLS)
        self.assertEqual(output.assistant_message, original)
        arguments = output.tool_calls[0]["function"]["arguments"]
        self.assertIsInstance(arguments, str)
        self.assertEqual(json.loads(arguments), original["tool_calls"][0]["function"]["arguments"])
        output.tool_calls[0]["function"]["name"] = "changed"
        self.assertEqual(output.assistant_message["tool_calls"][0]["function"]["name"], "search")
        output.assistant_message["provider_extension"]["opaque"].append(3)
        self.assertEqual(original["provider_extension"]["opaque"], [1, 2])

    def test_text_reasoning_tools_and_tool_role_history_survive_two_turns(self):
        first_message = {
            "role": "assistant", "content": " I will search. ",
            "reasoning_content": "Retain this reasoning verbatim.",
            "tool_calls": [_call(' { "query" : "Ada" } ')],
            "refusal": None,
        }
        transport = _Transport(
            _response(first_message),
            _response({"role": "assistant", "content": "Answer: Ada"}, "stop"),
        )
        client = self._client(transport)
        messages = [{"role": "user", "content": "Find Ada"}]
        first = client.generate(messages, tools=TOOLS)
        self.assertEqual(first.text, "I will search.")
        messages.extend([
            first.assistant_message,
            {"role": "tool", "tool_call_id": "call_1", "name": "search", "content": "Ada found."},
        ])
        before = copy.deepcopy(messages)
        second = client.generate(messages, tools=TOOLS, tool_choice="none")
        self.assertEqual(messages, before)
        self.assertEqual(transport.requests[1]["messages"], before)
        self.assertEqual(transport.requests[1]["messages"][1], first_message)
        self.assertEqual(second.assistant_message["role"], "assistant")
        self.assertEqual(second.finish_reason, "stop")

    def test_multiple_well_formed_calls_are_returned_not_silently_dropped(self):
        calls = [_call(call_id="first"), _call('{"query":"Grace"}', call_id="second")]
        transport = _Transport(_response({"content": None, "tool_calls": calls}))
        output = self._client(transport).generate("Find", tools=TOOLS)
        self.assertEqual(len(output.tool_calls), 2)
        self.assertEqual([item["id"] for item in output.tool_calls], ["first", "second"])

    def test_malformed_call_structure_is_terminal_not_resampled(self):
        malformed = [
            "not-a-list", {}, [None], [{}],
            [{"id": "a", "type": "custom", "function": {"name": "search", "arguments": "{}"}}],
            [{"type": "function", "function": {"name": "search", "arguments": "{}"}}],
            [_call(call_id=" ")], [_call(call_id=1)], [_call(), _call()],
            [{"id": "a", "type": "function", "function": None}],
            [{"id": "a", "type": "function", "function": {"arguments": "{}"}}],
            [{"id": "a", "type": "function", "function": {"name": " ", "arguments": "{}"}}],
            [{"id": "a", "type": "function", "function": {"name": "search"}}],
        ]
        malformed.append([_call({"query": float("nan")})])
        for calls in malformed:
            with self.subTest(calls=calls):
                transport = _Transport(_response({"content": "Some prose", "tool_calls": calls}))
                with self.assertRaisesRegex(RuntimeError, "API tool|API message tool_calls"):
                    self._client(transport, max_retries=3).generate("Find", tools=TOOLS)
                self.assertEqual(len(transport.requests), 1)

    def test_invalid_model_argument_strings_are_preserved_without_resampling(self):
        for arguments in ("", "not JSON", '{"query":', "[]", "null", "1", "true",
                          '{"query":NaN}', '{"query":Infinity}', '{"query":1e999}',
                          ' { "query" : "Ada" } '):
            with self.subTest(arguments=arguments):
                message = {"content": None, "tool_calls": [_call(arguments)]}
                transport = _Transport(_response(message, "length"))
                output = self._client(transport, max_retries=3).generate("Find", tools=TOOLS)
                self.assertEqual(output.tool_calls[0]["function"]["arguments"], arguments)
                self.assertEqual(output.assistant_message["tool_calls"], message["tool_calls"])
                self.assertEqual(output.finish_reason, "length")
                self.assertEqual(output.completion_tokens, 5)
                self.assertEqual(output.request_attempts, 1)
                self.assertEqual(len(transport.requests), 1)

    def test_structured_nonobject_arguments_are_not_repaired_to_valid_objects(self):
        for arguments in (None, [], [1, 2], 1, True):
            with self.subTest(arguments=arguments):
                transport = _Transport(_response({"content": None, "tool_calls": [_call(arguments)]}))
                output = self._client(transport, max_retries=3).generate("Find", tools=TOOLS)
                encoded = output.tool_calls[0]["function"]["arguments"]
                self.assertEqual(json.loads(encoded), arguments)
                self.assertEqual(output.request_attempts, 1)

    def test_reasoning_only_length_and_null_content_are_delivered_once(self):
        for calls in (None, []):
            for reason in ("stop", "length", "content_filter", None):
                with self.subTest(calls=calls, reason=reason):
                    message = {"content": None, "reasoning_content": "Unfinished thinking", "tool_calls": calls}
                    transport = _Transport(_response(message, reason))
                    output = self._client(transport, max_retries=3).generate("Find", tools=TOOLS)
                    self.assertEqual(output.text, "")
                    self.assertEqual(output.tool_calls, [])
                    self.assertEqual(output.assistant_message["reasoning_content"], "Unfinished thinking")
                    self.assertEqual(output.finish_reason, reason)
                    self.assertEqual(output.completion_tokens, 5)
                    self.assertEqual(len(transport.requests), 1)

    def test_missing_content_with_delivered_reasoning_is_not_resampled(self):
        transport = _Transport(_response({"reasoning_content": "Still thinking"}, "length"))
        output = self._client(transport, max_retries=2).generate("Find", tools=TOOLS)
        self.assertEqual(output.text, "")
        self.assertEqual(output.request_attempts, 1)
        self.assertEqual(output.finish_reason, "length")

    def test_tool_finish_reason_without_calls_is_rejected(self):
        transport = _Transport(_response({"content": "Some prose"}))
        with self.assertRaisesRegex(RuntimeError, "finish_reason missing tool calls"):
            self._client(transport).generate("Find", tools=TOOLS)

    def test_invalid_message_role_content_and_finish_reason_are_rejected(self):
        cases = [
            ({"role": "tool", "content": "bad", "tool_calls": [_call()]}, "stop"),
            ({"content": {"text": "bad"}, "tool_calls": [_call()]}, "tool_calls"),
            ({"content": [{"type": "text", "text": None}]}, "stop"),
            ({"content": [{"type": "text", "text": 123}]}, "stop"),
            ({"content": [{"type": "text", "text": {"text": "bad"}}]}, "stop"),
            ({"content": "fine"}, 123),
        ]
        for message, finish in cases:
            with self.subTest(message=message, finish=finish):
                transport = _Transport(_response(message, finish))
                with self.assertRaises(RuntimeError):
                    self._client(transport).generate("Find", tools=TOOLS)

    def test_content_list_and_length_finish_reason_survive_native_parsing(self):
        message = {
            "role": "assistant",
            "content": [{"type": "text", "text": " I will search. "}],
            "tool_calls": [_call()],
        }
        transport = _Transport(_response(message, "length"))
        output = self._client(transport).generate("Find", tools=TOOLS)
        self.assertEqual(output.text, "I will search.")
        self.assertEqual(output.assistant_message, message)
        self.assertEqual(output.finish_reason, "length")

    def test_invalid_usage_is_terminal_without_resampling(self):
        for usage in (["invalid"], {"prompt_tokens": "12"}, {"completion_tokens": -1},
                      {"completion_tokens": True}, {"prompt_tokens": float("nan")},
                      {"prompt_tokens_details": {"cached_tokens": "1"}}):
            with self.subTest(usage=usage):
                bad = _response({"content": None, "tool_calls": [_call()]})
                bad["usage"] = usage
                transport = _Transport(bad)
                with self.assertRaisesRegex(APIClientError, "API usage") as caught:
                    self._client(transport, max_retries=2).generate("Find", tools=TOOLS)
                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(len(caught.exception.attempt_usage), 1)
                self.assertIsNone(caught.exception.attempt_usage[0]["usage"])
                self.assertIn("usage_error", caught.exception.attempt_usage[0])
                json.dumps(caught.exception.attempt_usage, allow_nan=False)

    def test_invalid_model_arguments_dump_retains_response_and_does_not_retry(self):
        bad = _response({
            "role": "assistant", "content": None,
            "reasoning_content": "native-client-test-credential",
            "tool_calls": [_call("{")],
        })
        with tempfile.TemporaryDirectory() as directory:
            transport = _Transport(bad, _response({"content": "Must not replace the first decision"}, "stop"))
            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
                output = self._client(transport, max_retries=1).generate("Find", tools=TOOLS)
            paths = list(Path(directory).glob("*.json"))
            records = sorted((json.loads(path.read_text()) for path in paths), key=lambda r: r["attempt"])
            self.assertEqual(output.request_attempts, 1)
            self.assertEqual(len(transport.responses), 1)
            self.assertEqual([r["state"] for r in records], ["success"])
            self.assertFalse(records[0]["will_retry"])
            saved_message = records[0]["response_json"]["choices"][0]["message"]
            self.assertEqual(saved_message["tool_calls"][0]["function"]["arguments"], "{")
            self.assertEqual(saved_message["reasoning_content"], "[REDACTED]")
            self.assertEqual(output.assistant_message["reasoning_content"], "native-client-test-credential")
            self.assertEqual(output.completion_tokens, 5)
            self.assertEqual(output.attempt_usage[0]["usage"], bad["usage"])
            self.assertTrue(all(r["request_payload"]["tools"] == TOOLS for r in records))
            self.assertFalse(list(Path(directory).glob("*.tmp")))
            for path in paths:
                self.assertNotIn("native-client-test-credential", path.read_text())

    def test_service_retries_keep_each_usage_separate_from_delivered_usage(self):
        failed_usage = {"prompt_tokens": 7, "completion_tokens": 3}
        unavailable = urllib.error.HTTPError(
            "http://fake", 503, "Unavailable", Message(),
            BytesIO(json.dumps({"error": "overloaded", "usage": failed_usage}).encode()),
        )
        transport = _Transport(
            unavailable, urllib.error.URLError("connection lost"),
            _response({"content": None, "tool_calls": [_call("{")]}, "length"),
        )
        output = self._client(transport, max_retries=3).generate("Find", tools=TOOLS, tool_choice="none")
        self.assertEqual(output.request_attempts, 3)
        self.assertEqual(output.prompt_tokens, 12)  # Delivered response, not an all-attempt total.
        self.assertEqual(output.completion_tokens, 5)
        self.assertEqual([r["state"] for r in output.attempt_usage], ["error", "error", "success"])
        self.assertEqual(output.attempt_usage[0]["usage"], failed_usage)
        self.assertIsNone(output.attempt_usage[1]["usage"])  # Unknown, never fabricated as zero.
        self.assertEqual(output.attempt_usage[2]["usage"], {"prompt_tokens": 12, "completion_tokens": 5})
        self.assertEqual(len({r["generation_id"] for r in output.attempt_usage}), 1)
        self.assertEqual(len({r["request_id"] for r in output.attempt_usage}), 3)
        self.assertTrue(all(r["tool_choice"] == "none" and r["tools"] == TOOLS for r in transport.requests))

    def test_terminal_service_failure_exposes_known_attempt_usage(self):
        usage = {"prompt_tokens": 7, "completion_tokens": 3}
        unavailable = urllib.error.HTTPError(
            "http://fake", 503, "Unavailable", Message(),
            BytesIO(json.dumps({"usage": usage}).encode()),
        )
        with self.assertRaises(APIClientError) as caught:
            self._client(_Transport(unavailable)).generate("Find", tools=TOOLS)
        self.assertEqual(caught.exception.attempt_usage[0]["usage"], usage)

    def test_invalid_service_usage_is_unknown_not_a_numeric_total(self):
        unavailable = urllib.error.HTTPError(
            "http://fake", 503, "Unavailable", Message(),
            BytesIO(b'{"usage":{"completion_tokens":NaN}}'),
        )
        transport = _Transport(unavailable, _response({"content": "Answer: done"}, "stop"))
        output = self._client(transport, max_retries=1).generate("Find")
        self.assertIsNone(output.attempt_usage[0]["usage"])
        self.assertIn("usage_error", output.attempt_usage[0])
        self.assertEqual(output.attempt_usage[1]["usage"]["completion_tokens"], 5)
        self.assertIsNone(output.attempt_usage[1]["http_status"])
        json.dumps(output.attempt_usage, allow_nan=False)

    def test_terminal_bad_structure_does_not_retry_and_closes_dump(self):
        with tempfile.TemporaryDirectory() as directory:
            transport = _Transport(_response({"content": None, "tool_calls": [{}]}))
            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
                with self.assertRaises(APIClientError) as caught:
                    self._client(transport, max_retries=3).generate("Find", tools=TOOLS)
            records = [json.loads(path.read_text()) for path in Path(directory).glob("*.json")]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["state"], "malformed_response")
            self.assertFalse(records[0]["will_retry"])
            self.assertEqual(caught.exception.attempt_usage[0]["usage"], {"prompt_tokens": 12, "completion_tokens": 5})

    def test_unknown_transport_failure_keeps_previous_and_current_attempt_cost(self):
        for failure in (OSError("transport failed"), http.client.IncompleteRead(b"partial")):
            with self.subTest(failure=type(failure).__name__):
                unavailable = urllib.error.HTTPError(
                    "http://fake", 503, "Unavailable", Message(),
                    BytesIO(b'{"usage":{"prompt_tokens":7,"completion_tokens":3}}'),
                )
                transport = _Transport(unavailable, failure)
                with self.assertRaises(type(failure)) as caught:
                    self._client(transport, max_retries=3).generate("Find")
                ledger = caught.exception.attempt_usage
                self.assertEqual(len(ledger), 2)
                self.assertEqual(ledger[0]["usage"]["completion_tokens"], 3)
                self.assertIsNone(ledger[1]["usage"])
                self.assertEqual(len(transport.requests), 2)

    def test_unreadable_http_error_body_has_unknown_cost_and_no_resampling(self):
        class BrokenBody:
            def read(self):
                raise OSError("body unavailable")

            def close(self):
                pass

        failure = urllib.error.HTTPError("http://fake", 503, "Unavailable", Message(), BrokenBody())
        transport = _Transport(failure)
        with self.assertRaisesRegex(OSError, "body unavailable") as caught:
            self._client(transport, max_retries=3).generate("Find")
        self.assertEqual(len(caught.exception.attempt_usage), 1)
        self.assertEqual(caught.exception.attempt_usage[0]["http_status"], 503)
        self.assertIsNone(caught.exception.attempt_usage[0]["usage"])
        self.assertEqual(len(transport.requests), 1)

    def test_dump_failure_after_completion_keeps_delivered_usage_on_exception(self):
        client = self._client(_Transport(_response({"content": "Answer: done"}, "stop")))

        def dump(*args, **kwargs):
            if kwargs["state"] == "success":
                raise OSError("disk full")

        with mock.patch.object(client, "_dump_attempt", side_effect=dump):
            with self.assertRaisesRegex(OSError, "disk full") as caught:
                client.generate("Find")
        self.assertEqual(caught.exception.attempt_usage[0]["usage"], {"prompt_tokens": 12, "completion_tokens": 5})

    def test_deeply_nested_response_fails_once_and_leaves_terminal_dump(self):
        transport = _Transport(b"[" * 1500 + b"0" + b"]" * 1500)
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
                with self.assertRaises(APIClientError) as caught:
                    self._client(transport, max_retries=3).generate("Find")
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(len(caught.exception.attempt_usage), 1)
            records = [json.loads(path.read_text()) for path in Path(directory).glob("*.json")]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["state"], "malformed_response")
            self.assertFalse(records[0]["will_retry"])

    def test_null_primary_usage_fields_fall_back_to_reported_aliases(self):
        response = _response({"content": "Answer: done"}, "stop")
        response["usage"] = {"prompt_tokens": None, "input_tokens": 7, "completion_tokens": None, "output_tokens": 3}
        output = self._client(_Transport(response)).generate("Find")
        self.assertEqual(output.prompt_tokens, 7)
        self.assertEqual(output.completion_tokens, 3)
        self.assertEqual(output.attempt_usage[0]["usage"], response["usage"])


if __name__ == "__main__":
    unittest.main()
