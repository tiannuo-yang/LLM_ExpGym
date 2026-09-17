import copy
import json
import os
import tempfile
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest import mock

from expgym.llm_clients import APIClientError, APICompletionAbortedError
from expgym.native_anthropic_client import NativeAnthropicLLM


TOOLS = [{"type": "function", "function": {
    "name": "lookup", "description": "Read an item", "parameters": {
        "type": "object", "properties": {"item": {"type": "string"}},
        "required": ["item"],
    },
}}]


def response(content=None, stop="end_turn", usage=None):
    value = {"id": "msg_test", "type": "message", "role": "assistant",
             "model": "unfamiliar-provider-model", "content": content if content is not None else [
                 {"type": "text", "text": "Answer: done"}],
             "stop_reason": stop, "stop_sequence": None}
    if usage is not None:
        value["usage"] = usage
    return value


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item if isinstance(item, bytes) else json.dumps(item).encode()


class NativeAnthropicClientTest(unittest.TestCase):
    def client(self, transport, **kwargs):
        return NativeAnthropicLLM(api_key="private-test-credential", model="unfamiliar-provider-model",
                                  base_url="http://127.0.0.1:8080/v1", transport=transport,
                                  max_retries=0, **kwargs)

    def test_native_endpoint_default_effort_and_explicit_omissions(self):
        transport = Transport(response())
        client = self.client(transport, temperature=0.7, top_p=0.8, top_k=12,
                             seed=12, prompt_cache_key="pool-a")
        result = client.generate("question")
        self.assertEqual(result.text, "Answer: done")
        request = transport.requests[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8080/v1/messages")
        self.assertEqual(request.get_header("Anthropic-version"), "2023-06-01")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "unfamiliar-provider-model")
        self.assertEqual(payload["max_tokens"], 8192)
        self.assertNotIn("thinking", payload)
        self.assertNotIn("output_config", payload)
        for field in ("temperature", "top_p", "top_k", "seed", "prompt_cache_key"):
            self.assertNotIn(field, payload)
        self.assertEqual(client.parameter_compatibility["effort"], "high")
        self.assertEqual(client.parameter_compatibility["effort_source"], "provider_default")
        self.assertEqual(client.parameter_compatibility["omitted_parameters"]["temperature"], 0.7)

    def test_high_is_native_effort_not_legacy_thinking_budget(self):
        transport = Transport(response())
        client = self.client(transport, reasoning_effort="high", max_tokens=32768,
                             thinking={"type": "adaptive"})
        client.generate("question", tools=TOOLS)
        payload = json.loads(transport.requests[0].data)
        self.assertEqual(payload["output_config"], {"effort": "high"})
        self.assertEqual(payload["thinking"], {"type": "adaptive"})
        self.assertEqual(payload["max_tokens"], 32768)
        self.assertEqual(payload["tool_choice"], {"type": "auto", "disable_parallel_tool_use": True})
        self.assertEqual(payload["tools"][0]["input_schema"], TOOLS[0]["function"]["parameters"])
        self.assertNotIn("reasoning_effort", payload)

    def test_signature_only_redacted_tool_and_result_survive_full_roundtrip(self):
        blocks = [{"type": "thinking", "thinking": "", "signature": "opaque-signature"},
                  {"type": "redacted_thinking", "data": "opaque-redacted"},
                  {"type": "text", "text": "Looking up the item."},
                  {"type": "tool_use", "id": "toolu_real", "name": "lookup", "input": {"item": "A"}}]
        transport = Transport(response(blocks, "tool_use"), response())
        client = self.client(transport)
        initial = [{"role": "system", "content": "Task protocol"},
                   {"role": "user", "content": "question"}]
        original_initial = copy.deepcopy(initial)
        first = client.generate(initial, tools=TOOLS)
        self.assertEqual(first.finish_reason, "tool_calls")
        self.assertEqual(first.assistant_message["content"], blocks)
        self.assertEqual(first.tool_calls[0]["id"], "toolu_real")
        history = initial + [first.assistant_message,
                             {"role": "tool", "tool_call_id": "toolu_real", "content": "observed A"},
                             {"role": "user", "content": "Now answer."}]
        before = copy.deepcopy(history)
        client.generate(history, tools=TOOLS, tool_choice="none")
        sent = json.loads(transport.requests[1].data)
        self.assertEqual(sent["messages"][1], {"role": "assistant", "content": blocks})
        self.assertEqual(sent["messages"][2]["content"], [
            {"type": "tool_result", "tool_use_id": "toolu_real", "content": "observed A"},
            {"type": "text", "text": "Now answer."},
        ])
        self.assertEqual(sent["tool_choice"], {"type": "none"})
        self.assertEqual(sent["tools"], json.loads(transport.requests[0].data)["tools"])
        self.assertEqual(history, before)
        self.assertEqual(initial, original_initial)

    def test_tool_only_and_normal_empty_length_decisions_are_not_retried(self):
        cases = [
            (response([{"type": "tool_use", "id": "toolu_1", "name": "lookup", "input": {}}], "tool_use"), "tool_calls", 1),
            (response([], "max_tokens"), "length", 0),
            (response([], "end_turn"), "stop", 0),
            (response([{"type": "thinking", "thinking": "", "signature": "opaque"}], "max_tokens"), "length", 0),
            (response([{"type": "text", "text": ""}]), "stop", 0),
        ]
        for body, finish, count in cases:
            with self.subTest(body=body):
                transport = Transport(body)
                result = self.client(transport).generate("question", tools=TOOLS)
                self.assertEqual(result.finish_reason, finish)
                self.assertEqual(len(result.tool_calls), count)
                self.assertEqual(result.text, "")
                self.assertEqual(len(transport.requests), 1)

    def test_native_usage_is_raw_in_attempt_and_total_in_loop_counters(self):
        usage = {"input_tokens": 100, "output_tokens": 30,
                 "cache_read_input_tokens": 80, "cache_creation_input_tokens": 20,
                 "cache_creation": {"ephemeral_5m_input_tokens": 20, "ephemeral_1h_input_tokens": 0},
                 "output_tokens_details": {"thinking_tokens": 23}}
        transport = Transport(response(usage=usage))
        result = self.client(transport).generate("question")
        self.assertEqual(result.prompt_tokens, 200)
        self.assertEqual(result.completion_tokens, 30)
        self.assertEqual(result.cached_prompt_tokens, 80)
        self.assertEqual(result.cache_write_prompt_tokens, 20)
        self.assertEqual(result.attempt_usage[0]["usage"], usage)
        self.assertIsNone(result.attempt_usage[0]["http_status"])

    def test_missing_accounting_stays_unknown(self):
        for usage in (None, {}, {"input_tokens": 10, "output_tokens": 5},
                      {"input_tokens": 10, "cache_read_input_tokens": None, "cache_creation_input_tokens": 0}):
            with self.subTest(usage=usage):
                result = self.client(Transport(response(usage=usage))).generate("question")
                self.assertIsNone(result.prompt_tokens)

    def test_all_attempts_dump_native_payload_response_and_redact_credentials(self):
        error_usage = {"input_tokens": 4, "output_tokens": 2}
        error = urllib.error.HTTPError("http://local", 503, "Unavailable", {}, BytesIO(json.dumps({
            "error": "echo private-test-credential", "usage": error_usage,
        }).encode()))
        body = response([{"type": "text", "text": "private-test-credential"}])
        transport = Transport(error, body)
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
            client = NativeAnthropicLLM(api_key="private-test-credential", model="another-unfamiliar-model",
                                        base_url="http://local/v1", transport=transport,
                                        max_retries=1, retry_base_seconds=0, retry_max_seconds=0)
            result = client.generate("question", tools=TOOLS)
            dumps = [json.loads(path.read_text()) for path in Path(directory).rglob("*.json")]
            self.assertEqual(len(dumps), 2)
            self.assertEqual([a["state"] for a in result.attempt_usage], ["error", "success"])
            self.assertEqual(result.attempt_usage[0]["usage"], error_usage)
            for record in dumps:
                self.assertNotIn("private-test-credential", json.dumps(record))
                self.assertNotIn("temperature", record["request_payload"])
                self.assertIn("input_schema", record["request_payload"]["tools"][0])
                self.assertEqual(record["context"]["api_protocol"], "anthropic")
                self.assertEqual(record["endpoint"], "http://local/v1/messages")
            good = next(record for record in dumps if record["state"] == "success")
            self.assertEqual(good["response_json"]["type"], "message")
            self.assertIn("[REDACTED]", good["response_raw"])

    def test_malformed_abort_and_invalid_usage_preserve_one_attempt(self):
        cases = [
            b"bad JSON", response([{"type": "text", "text": 2}]),
            response([{"type": "thinking", "thinking": "missing signature"}]),
            response([], "tool_use"),
            response(usage={"input_tokens": 1, "cache_read_input_tokens": -1}),
            response(usage={"output_tokens_details": {"thinking_tokens": True}}),
        ]
        for body in cases:
            with self.subTest(body=body):
                transport = Transport(body)
                with self.assertRaises(APIClientError) as caught:
                    self.client(transport).generate("question")
                self.assertEqual(len(caught.exception.attempt_usage), 1)
                self.assertEqual(len(transport.requests), 1)
        transport = Transport(response(stop="abort", usage={"input_tokens": 2, "output_tokens": 1}))
        with self.assertRaises(APICompletionAbortedError) as caught:
            self.client(transport).generate("question")
        self.assertEqual(caught.exception.attempt_usage[0]["usage"]["output_tokens"], 1)

    def test_explicit_capability_can_allow_sampling_but_cannot_fake_seed(self):
        transport = Transport(response())
        client = self.client(transport, omitted_parameters=("seed", "prompt_cache_key"),
                             temperature=0.3, top_p=0.96, top_k=40)
        client.generate("question")
        sent = json.loads(transport.requests[0].data)
        self.assertEqual([sent[key] for key in ("temperature", "top_p", "top_k")], [0.3, 0.96, 40])
        with self.assertRaisesRegex(ValueError, "seed has no native"):
            self.client(Transport(), omitted_parameters=(), seed=1).generate("question")

    def test_refuses_unsupported_configuration_and_unsigned_reasoning(self):
        for kwargs in ({"api_protocol": "responses"}, {"reasoning": {"enabled": True}},
                       {"chat_template_kwargs": {"enable_thinking": True}},
                       {"omitted_parameters": "seed"}, {"omitted_parameters": ("max_tokens",)}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.client(Transport(), **kwargs)
        client = self.client(Transport())
        with self.assertRaisesRegex(ValueError, "unsigned"):
            client.generate([{"role": "assistant", "content": "", "reasoning_content": "old reasoning"}])
        with self.assertRaisesRegex(ValueError, "Mid-conversation"):
            client.generate([{"role": "user", "content": "q"}, {"role": "system", "content": "later"}])

    def test_native_tool_alias_cannot_change_original_blocks(self):
        native = {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t", "name": "lookup", "input": {"item": "original"}}],
            "tool_calls": [{"id": "t", "type": "function", "function": {
                "name": "lookup", "arguments": '{"item":"changed"}'}}]}
        with self.assertRaisesRegex(ValueError, "disagree"):
            self.client(Transport()).generate([native])


if __name__ == "__main__":
    unittest.main()
