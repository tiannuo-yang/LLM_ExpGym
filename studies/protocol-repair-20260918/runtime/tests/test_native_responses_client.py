import copy
import json
import os
import tempfile
import unittest
import urllib.error
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest import mock

from expgym.llm_clients import APIClientError, APICompletionAbortedError
from expgym.native_responses_client import NativeResponsesLLM, OUTPUT_ITEMS_FIELD


TOOLS = [{"type": "function", "function": {
    "name": "lookup", "description": "Look up a value.",
    "parameters": {"type": "object", "properties": {"key": {"type": "string"}},
                   "required": ["key"]},
}}]


def response(output=None, **kwargs):
    return {"id": "resp_fixture", "object": "response", "status": "completed",
            "model": "unfamiliar-native-model", "output": output or [], **kwargs}


def answer(text="Answer: 42", **kwargs):
    return response([{"type": "message", "role": "assistant", "id": "msg_1",
                      "status": "completed", "content": [
                          {"type": "output_text", "text": text, "annotations": []},
                      ]}], **kwargs)


class Transport:
    def __init__(self, *values):
        self.values = list(values)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        if isinstance(value, bytes):
            return value
        return json.dumps(value).encode("utf-8")

    @property
    def bodies(self):
        return [json.loads(request.data) for request in self.requests]


class NativeResponsesLLMTest(unittest.TestCase):
    def test_explicit_parameters_wire_payload_and_native_usage(self):
        usage = {"input_tokens": 40, "output_tokens": 17, "total_tokens": 57,
                 "input_tokens_details": {"cached_tokens": 12, "cache_write_tokens": 3},
                 "output_tokens_details": {"reasoning_tokens": 10}}
        transport = Transport(answer(usage=usage))
        client = NativeResponsesLLM(api_key="fixture-secret", model="unfamiliar-model",
                                    base_url="http://localhost:8080/v1/chat/completions",
                                    transport=transport, temperature=0.7, top_p=0.95,
                                    top_k=20, seed=2200, max_tokens=32768,
                                    reasoning_effort="medium", prompt_cache_key="local-scope")
        result = client.generate("Hello", tools=TOOLS)
        body = transport.bodies[0]
        self.assertEqual(transport.requests[0].full_url, "http://localhost:8080/v1/responses")
        self.assertEqual(body["input"], [{"role": "user", "content": "Hello"}])
        self.assertEqual(body["reasoning"], {"effort": "medium"})
        self.assertEqual(body["include"], ["reasoning.encrypted_content"])
        self.assertFalse(body["store"])
        self.assertFalse(body["stream"])
        self.assertFalse(body["parallel_tool_calls"])
        self.assertEqual(body["tool_choice"], "auto")
        self.assertEqual(body["tools"][0], {"type": "function", **TOOLS[0]["function"]})
        for field in ("temperature", "top_p", "seed", "top_k", "max_tokens", "max_output_tokens", "messages", "prompt_cache_key"):
            self.assertNotIn(field, body)
        self.assertEqual(client.parameter_compatibility["omitted_parameters"]["max_tokens"], 32768)
        self.assertEqual(client.parameter_compatibility["omitted_parameters"]["prompt_cache_key"], "local-scope")
        self.assertTrue(client.requires_immutable_history)
        self.assertEqual((result.prompt_tokens, result.completion_tokens), (40, 17))
        self.assertEqual((result.cached_prompt_tokens, result.cache_write_prompt_tokens), (12, 3))
        self.assertEqual(result.attempt_usage[0]["usage"], usage)

    def test_multiturn_preserves_complete_items_and_call_ids(self):
        original_items = [
            {"type": "reasoning", "id": "rs_1", "summary": [],
             "encrypted_content": "opaque-encrypted-reasoning", "future_field": {"x": [1, 2]}},
            {"type": "message", "role": "assistant", "id": "msg_comment", "phase": "commentary",
             "content": [{"type": "output_text", "text": "Looking up", "annotations": []}]},
            {"type": "function_call", "id": "fc_distinct_item_id", "call_id": "call_1",
             "name": "lookup", "arguments": '{ "key": "x" }', "status": "completed"},
        ]
        transport = Transport(response(original_items), answer())
        client = NativeResponsesLLM(api_key="fixture-secret", transport=transport)
        first = client.generate([{"role": "system", "content": "Instructions"},
                                 {"role": "user", "content": "Question"}], tools=TOOLS)
        self.assertEqual(first.assistant_message[OUTPUT_ITEMS_FIELD], original_items)
        self.assertEqual(first.tool_calls[0]["id"], "call_1")
        self.assertEqual(first.tool_calls[0]["function"]["arguments"], '{ "key": "x" }')
        messages = [{"role": "system", "content": "Instructions"},
                    {"role": "user", "content": "Question"}, first.assistant_message,
                    {"role": "tool", "tool_call_id": "call_1", "name": "lookup", "content": "42"},
                    {"role": "user", "content": "Finish now"}]
        frozen = copy.deepcopy(messages)
        second = client.generate(messages, tools=TOOLS, tool_choice="none")
        self.assertEqual(messages, frozen)
        body = transport.bodies[1]
        self.assertEqual(body["input"][2:5], original_items)
        self.assertEqual(body["input"][5], {"type": "function_call_output", "call_id": "call_1", "output": "42"})
        self.assertEqual(body["input"][6], {"role": "user", "content": "Finish now"})
        self.assertEqual(body["tool_choice"], "none")
        self.assertEqual(body["tools"], transport.bodies[0]["tools"])
        self.assertEqual(second.text, "Answer: 42")

    def test_reasoning_only_empty_and_length_are_delivered_without_retry(self):
        items = [{"type": "reasoning", "id": "rs_1", "encrypted_content": "opaque", "summary": []}]
        for payload, expected in ((response(items), "stop"), (response(), "stop"),
                                  (response(items, status="incomplete", incomplete_details={"reason": "max_output_tokens"}), "length")):
            with self.subTest(expected=expected, output=payload["output"]):
                transport = Transport(payload)
                result = NativeResponsesLLM(api_key="fixture-secret", transport=transport).generate("Hi")
                self.assertEqual(result.text, "")
                self.assertEqual(result.finish_reason, expected)
                self.assertEqual(result.request_attempts, 1)
                self.assertEqual(result.assistant_message[OUTPUT_ITEMS_FIELD], payload["output"])

    def test_invalid_json_function_arguments_are_delivered_verbatim(self):
        item = {"type": "function_call", "call_id": "call_1", "name": "lookup", "arguments": "{broken"}
        transport = Transport(response([item]))
        output = NativeResponsesLLM(api_key="fixture-secret", transport=transport).generate("Hi", tools=TOOLS)
        self.assertEqual(output.tool_calls[0]["function"]["arguments"], "{broken")
        self.assertEqual(output.finish_reason, "tool_calls")
        self.assertEqual(output.request_attempts, 1)

    def test_provider_failed_or_cancelled_is_never_resampled(self):
        for status in ("failed", "cancelled"):
            usage = {"input_tokens": 5, "output_tokens": 3}
            transport = Transport(response(status=status, usage=usage,
                                           error={"code": "provider_abort", "message": "stopped"}))
            with self.assertRaises(APICompletionAbortedError) as raised:
                NativeResponsesLLM(api_key="fixture-secret", transport=transport).generate("Hi")
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(raised.exception.attempt_usage[0]["usage"], usage)
            self.assertEqual(raised.exception.attempt_usage[0]["state"], "error")

    def test_missing_usage_remains_unknown(self):
        transport = Transport(answer())
        output = NativeResponsesLLM(api_key="fixture-secret", transport=transport).generate("Hi")
        self.assertIsNone(output.prompt_tokens)
        self.assertIsNone(output.completion_tokens)
        self.assertIsNone(output.attempt_usage[0]["usage"])

    def test_malformed_terminal_response_and_usage_are_not_retried(self):
        payloads = [b"broken", {"object": "response", "status": "in_progress"},
                    response([{"type": "function_call", "call_id": "call_1", "name": "lookup"}]),
                    answer(usage={"input_tokens": -1}),
                    response(status="incomplete", incomplete_details={})]
        for payload in payloads:
            with self.subTest(payload=payload):
                transport = Transport(payload)
                with self.assertRaises(APIClientError) as raised:
                    NativeResponsesLLM(api_key="fixture-secret", transport=transport).generate("Hi")
                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(raised.exception.attempt_usage[0]["state"], "malformed_response")

    def test_transport_retry_dumps_actual_wire_and_all_usage_without_credentials(self):
        key = "fixture-secret-not-for-dump"
        failed_usage = {"input_tokens": 9, "output_tokens": 1}
        error_payload = {"error": {"message": "echo " + key, "api_key": key}, "usage": failed_usage}
        failure = urllib.error.HTTPError("http://test/v1/responses", 429, "limited", Message(),
                                         BytesIO(json.dumps(error_payload).encode()))
        transport = Transport(failure, answer(usage={"input_tokens": 11, "output_tokens": 2}))
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
            client = NativeResponsesLLM(api_key=key, transport=transport, seed=2200,
                                       max_retries=1, retry_base_seconds=0)
            output = client.generate("Hi", tools=TOOLS)
            records = [json.loads(path.read_text()) for path in Path(directory).glob("*.json")]
            serialized = json.dumps(records)
            self.assertNotIn(key, serialized)
            self.assertEqual(len(records), 2)
            self.assertEqual(output.request_attempts, 2)
            self.assertEqual(output.attempt_usage[0]["usage"], failed_usage)
            self.assertEqual(output.attempt_usage[1]["usage"], {"input_tokens": 11, "output_tokens": 2})
            self.assertEqual(transport.bodies[0], transport.bodies[1])
            for record in records:
                self.assertEqual(record["request_payload"], transport.bodies[0])
                self.assertEqual(record["context"]["parameter_compatibility"]["omitted_parameters"]["seed"], 2200)
                self.assertIsNotNone(record["response_raw"])
            failed = next(record for record in records if record["state"] == "error")
            self.assertEqual(failed["http_status"], 429)
            self.assertEqual(failed["response_json"]["error"]["api_key"], "[REDACTED]")

    def test_supported_output_limit_is_explicitly_mapped(self):
        transport = Transport(answer())
        client = NativeResponsesLLM(api_key="fixture-secret", transport=transport,
                                    omitted_parameters=("seed", "top_k"), max_tokens=123,
                                    temperature=0.5, top_p=0.8)
        client.generate("Hi")
        self.assertEqual(transport.bodies[0]["max_output_tokens"], 123)
        self.assertEqual(transport.bodies[0]["temperature"], 0.5)
        self.assertEqual(transport.bodies[0]["top_p"], 0.8)

    def test_incompatible_configuration_or_unsigned_reasoning_fails_before_network(self):
        for kwargs in ({"api_protocol": "chat"}, {"omitted_parameters": "seed"},
                       {"omitted_parameters": ("unrecognized",)}, {"store": "false"},
                       {"include": ()}, {"provider": {"order": ["x"]}},
                       {"reasoning": {"enabled": True}},
                       {"reasoning": {"effort": "low"}, "reasoning_effort": "high"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                NativeResponsesLLM(api_key="fixture-secret", **kwargs)
        transport = Transport(answer())
        client = NativeResponsesLLM(api_key="fixture-secret", transport=transport,
                                    omitted_parameters=(), seed=1)
        with self.assertRaisesRegex(ValueError, "seed has no native"):
            client.generate("Hi")
        self.assertFalse(transport.requests)
        client = NativeResponsesLLM(api_key="fixture-secret", transport=transport)
        with self.assertRaisesRegex(ValueError, "Cannot replay Chat reasoning"):
            client.generate([{"role": "assistant", "content": "Hi", "reasoning_content": "unsigned"}])
        self.assertFalse(transport.requests)

    def test_native_history_alias_mismatch_is_rejected(self):
        transport = Transport(answer())
        client = NativeResponsesLLM(api_key="fixture-secret", transport=transport)
        message = {"role": "assistant", "content": None, OUTPUT_ITEMS_FIELD: [
            {"type": "function_call", "call_id": "call_1", "name": "lookup", "arguments": "{}"},
        ]}
        with self.assertRaisesRegex(ValueError, "aliases disagree"):
            client.generate([message])
        self.assertFalse(transport.requests)


if __name__ == "__main__":
    unittest.main()
