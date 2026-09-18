"""No-network Gemini wire, signed-history, accounting, and runner tests."""
import argparse
import copy
import http.client
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from expgym.llm_clients import APIClientError, APICompletionAbortedError, PartialAPIResponseError
from expgym.native_gemini_client import CONTENT_FIELD, NativeGeminiLLM, _gemini_transport
from expgym.react_loop import run_react_loop


TOOLS = [{"type": "function", "function": {
    "name": "lookup", "description": "Read an item", "parameters": {
        "type": "object", "properties": {"item": {"type": "string"}}, "required": ["item"],
    },
}}]
COMPLEX_PARAMETERS = {
    "type": "object",
    "properties": {
        "item": {"type": "string", "enum": ["Ada", "Grace"], "minLength": 3,
                 "maxLength": 8, "pattern": "^[A-Z][a-z]+$"},
        "settings": {
            "type": "object",
            "properties": {
                "depth": {"type": "integer", "enum": [1, 3, 5], "minimum": 1, "maximum": 5},
                "ratio": {"type": "number", "enum": [0.25, 0.5], "minimum": 0,
                          "exclusiveMaximum": 1, "multipleOf": 0.25},
                "enabled": {"type": "boolean", "enum": [False, True], "default": False},
                "limits": {"type": "array", "minItems": 1, "maxItems": 3, "uniqueItems": True,
                           "items": {"type": "object", "properties": {
                               "units": {"type": "integer", "minimum": 1}},
                               "required": ["units"], "additionalProperties": False}},
            },
            "required": ["depth", "ratio", "enabled"],
            "additionalProperties": False,
        },
        "extras": {"type": "object", "additionalProperties": {"type": "string", "minLength": 1}},
    },
    "required": ["item", "settings"],
    "additionalProperties": False,
}
USAGE = {"promptTokenCount": 11, "candidatesTokenCount": 3, "thoughtsTokenCount": 7,
         "totalTokenCount": 21, "cachedContentTokenCount": 2}


def response(parts=None, stop="STOP", usage=None):
    value = {"candidates": [{"content": {"role": "model", "parts": (
        [{"text": "Answer: done"}] if parts is None else parts)}, "finishReason": stop}],
        "modelVersion": "unfamiliar-upstream-model", "responseId": "response-1"}
    if usage is not None:
        value["usageMetadata"] = usage
    return value


def call(call_id="call-1"):
    value = {"name": "lookup", "args": {"item": "Ada"}}
    if call_id is not None:
        value["id"] = call_id
    return {"functionCall": value, "thoughtSignature": "opaque-tool-signature"}


def sse(*events):
    return (": heartbeat\n\n" + "".join("data: " + json.dumps(event) + "\n\n" for event in events)).encode()


class Transport:
    def __init__(self, *responses):
        self.responses, self.requests = list(responses), []

    def __call__(self, request, timeout):
        self.requests.append(request)
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value if isinstance(value, bytes) else json.dumps(value).encode()


class NativeGeminiClientTest(unittest.TestCase):
    def client(self, transport, **kwargs):
        kwargs.setdefault("max_retries", 0)
        return NativeGeminiLLM(api_key="private-gemini-test-key", model="unfamiliar-model",
                               base_url="http://127.0.0.1:8080/antigravity/v1beta",
                               transport=transport, **kwargs)

    def test_native_url_parameters_omissions_and_headers(self):
        transport = Transport(response(usage=USAGE))
        client = self.client(transport, temperature=0.7, top_p=0.8, top_k=12, seed=77,
                             reasoning_effort="medium", max_tokens=16384, prompt_cache_key="pool-a")
        output = client.generate("question", tools=TOOLS)
        request = transport.requests[0]
        self.assertEqual(request.full_url,
                         "http://127.0.0.1:8080/antigravity/v1beta/models/unfamiliar-model:streamGenerateContent?alt=sse")
        self.assertEqual(request.get_header("X-goog-api-key"), "private-gemini-test-key")
        payload = json.loads(request.data)
        self.assertEqual(payload["generationConfig"], {"temperature": 0.7, "topP": 0.8,
                         "topK": 12, "seed": 77, "maxOutputTokens": 16384,
                         "thinkingConfig": {"thinkingLevel": "medium"}})
        self.assertNotIn("model", payload)
        self.assertNotIn("prompt_cache_key", payload)
        self.assertNotIn("parallel_tool_calls", payload)
        self.assertEqual(payload["toolConfig"]["functionCallingConfig"]["mode"], "AUTO")
        self.assertEqual(output.prompt_tokens, 11)
        self.assertEqual(output.completion_tokens, 10)
        self.assertEqual(output.cached_prompt_tokens, 2)
        self.assertEqual(output.attempt_usage[0]["provider_usage"], USAGE)
        self.assertIsNone(output.attempt_usage[0]["http_status"])
        self.assertIn("unverified", client.parameter_compatibility["seed_semantics"])
        self.assertEqual(client.parameter_compatibility["omitted_parameters"], {"prompt_cache_key": "pool-a"})
        self.assertEqual(client.parameter_compatibility["tool_schema_format"], "parametersJsonSchema")
        self.assertEqual(client.parameter_compatibility["tool_schema_preservation"], "deepcopy_unchanged")
        self.assertIs(client.parameter_compatibility["tool_schema_coercion"], False)

    def test_explicit_seed_omission_and_unsupported_controls(self):
        transport = Transport(response())
        client = self.client(transport, seed=22, omitted_parameters=("seed", "prompt_cache_key"))
        client.generate("question")
        self.assertNotIn("seed", json.loads(transport.requests[0].data)["generationConfig"])
        self.assertEqual(client.parameter_compatibility["omitted_parameters"]["seed"], 22)
        for kwargs in ({"reasoning_effort": "automatic"}, {"top_k": -1},
                       {"chat_template_kwargs": {"enable_thinking": True}},
                       {"omitted_parameters": "seed"}, {"seed": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.client(Transport(), **kwargs)

    def test_signed_parts_and_function_response_survive_two_turns(self):
        original = [{"thought": True, "text": "private thought", "thoughtSignature": "opaque-thought"},
                    {"text": "Checking", "thoughtSignature": "opaque-text"}, call()]
        transport = Transport(response(original), response())
        client = self.client(transport)
        messages = [{"role": "system", "content": "Use tools"}, {"role": "user", "content": "Find Ada"}]
        first = client.generate(messages, tools=TOOLS)
        self.assertEqual(first.text, "Checking")
        self.assertEqual(first.finish_reason, "tool_calls")
        self.assertEqual(first.assistant_message[CONTENT_FIELD]["parts"], original)
        messages.extend([first.assistant_message,
                         {"role": "tool", "tool_call_id": "call-1", "content": "Observation: London"}])
        frozen = copy.deepcopy(messages)
        client.generate(messages, tools=TOOLS, tool_choice="none")
        wire = json.loads(transport.requests[1].data)
        self.assertEqual(messages, frozen)
        self.assertEqual(wire["contents"][1], {"role": "model", "parts": original})
        self.assertEqual(wire["contents"][2]["parts"], [{"functionResponse": {
            "name": "lookup", "id": "call-1", "response": {"result": "Observation: London"}}}])
        self.assertEqual(wire["toolConfig"]["functionCallingConfig"], {"mode": "NONE"})
        self.assertEqual(wire["tools"][0]["functionDeclarations"], [{
            "name": "lookup", "description": "Read an item",
            "parametersJsonSchema": TOOLS[0]["function"]["parameters"],
        }])

    def test_json_schema_is_deepcopied_without_type_or_constraint_coercion(self):
        tools = copy.deepcopy(TOOLS)
        tools[0]["function"]["parameters"] = copy.deepcopy(COMPLEX_PARAMETERS)
        payload = {"messages": [{"role": "user", "content": "Find Ada"}],
                   "tools": tools, "tool_choice": "auto"}
        frozen = copy.deepcopy(payload)
        client = self.client(Transport())
        native = client._native_payload(payload)
        declaration = native["tools"][0]["functionDeclarations"][0]
        self.assertNotIn("parameters", declaration)
        schema = declaration["parametersJsonSchema"]
        self.assertEqual(schema, COMPLEX_PARAMETERS)
        self.assertIsNot(schema, tools[0]["function"]["parameters"])
        properties = schema["properties"]["settings"]["properties"]
        original = tools[0]["function"]["parameters"]["properties"]["settings"]["properties"]
        self.assertIsNot(properties, original)
        self.assertIsNot(properties["depth"]["enum"], original["depth"]["enum"])
        self.assertEqual([type(value) for value in properties["depth"]["enum"]], [int, int, int])
        self.assertEqual([type(value) for value in properties["ratio"]["enum"]], [float, float])
        self.assertEqual([type(value) for value in properties["enabled"]["enum"]], [bool, bool])
        self.assertEqual(payload, frozen)
        properties["depth"]["enum"].append(7)
        properties["limits"]["items"]["additionalProperties"] = True
        schema["required"].append("extras")
        self.assertEqual(payload, frozen, "Mutating the wire copy must not alter caller-owned tools")

    def test_complex_json_schema_survives_signed_turns_and_forced_final_for_unfamiliar_model(self):
        tools = copy.deepcopy(TOOLS)
        tools[0]["function"]["parameters"] = copy.deepcopy(COMPLEX_PARAMETERS)
        signed_turns = [
            [{"thought": True, "text": "First lookup", "thoughtSignature": "opaque-first-thought"}, call("call-1")],
            [{"text": "Verify result", "thoughtSignature": "opaque-second-text"}, call("call-2")],
        ]
        transport = Transport(response(signed_turns[0]), response(signed_turns[1]), response())
        client = self.client(transport)
        messages = [{"role": "system", "content": "Use tools"},
                    {"role": "user", "content": "Find Ada"}]
        frozen_tools = copy.deepcopy(tools)
        for index in range(2):
            frozen_history = copy.deepcopy(messages)
            output = client.generate(messages, tools=tools)
            self.assertEqual(messages, frozen_history)
            self.assertEqual(tools, frozen_tools)
            messages.extend([output.assistant_message, {
                "role": "tool", "tool_call_id": "call-" + str(index + 1),
                "content": "Observation " + str(index + 1),
            }])
        frozen_history = copy.deepcopy(messages)
        client.generate(messages, tools=tools, tool_choice="none")
        self.assertEqual(messages, frozen_history)
        self.assertEqual(tools, frozen_tools)
        wires = [json.loads(request.data) for request in transport.requests]
        expected_declaration = {"name": "lookup", "description": "Read an item",
                                "parametersJsonSchema": COMPLEX_PARAMETERS}
        for index, (request, wire) in enumerate(zip(transport.requests, wires)):
            with self.subTest(turn=index):
                self.assertIn("/models/unfamiliar-model:", request.full_url)
                self.assertEqual(wire["tools"][0]["functionDeclarations"], [expected_declaration])
                self.assertNotIn("parameters", wire["tools"][0]["functionDeclarations"][0])
        self.assertEqual([wire["toolConfig"]["functionCallingConfig"]["mode"] for wire in wires],
                         ["AUTO", "AUTO", "NONE"])
        final_contents = wires[-1]["contents"]
        self.assertEqual(final_contents[1], {"role": "model", "parts": signed_turns[0]})
        self.assertEqual(final_contents[3], {"role": "model", "parts": signed_turns[1]})
        for index, content_index in enumerate((2, 4), start=1):
            self.assertEqual(final_contents[content_index]["parts"], [{"functionResponse": {
                "name": "lookup", "id": "call-" + str(index),
                "response": {"result": "Observation " + str(index)},
            }}])

    def test_idless_calls_use_internal_alias_without_mutating_native_calls(self):
        transport = Transport(response([call(None)]), response())
        client = self.client(transport)
        first = client.generate("Find", tools=TOOLS)
        alias = first.tool_calls[0]["id"]
        self.assertTrue(alias.startswith("gemini_"))
        client.generate([{"role": "user", "content": "Find"}, first.assistant_message,
                         {"role": "tool", "tool_call_id": alias, "content": "result"}], tools=TOOLS)
        wire = json.loads(transport.requests[1].data)
        self.assertNotIn("id", wire["contents"][1]["parts"][0]["functionCall"])
        self.assertNotIn("id", wire["contents"][2]["parts"][0]["functionResponse"])

    def test_alias_tampering_and_unmatched_results_rejected_before_network(self):
        transport = Transport(response([call()]))
        client = self.client(transport)
        first = client.generate("Find", tools=TOOLS)
        first.assistant_message["tool_calls"][0]["function"]["arguments"] = '{"item":"changed"}'
        with self.assertRaisesRegex(ValueError, "aliases disagree"):
            client.generate([first.assistant_message], tools=TOOLS)
        with self.assertRaisesRegex(ValueError, "no matching"):
            client.generate([{"role": "tool", "tool_call_id": "wrong", "content": "result"}])
        self.assertEqual(len(transport.requests), 1)

    def test_empty_reasoning_only_and_length_are_delivered_without_resampling(self):
        for parts, stop in (([], "STOP"), ([{"thought": True, "text": "thought", "thoughtSignature": "sig"}], "STOP"),
                            ([{"text": "partial"}, call()], "MAX_TOKENS")):
            with self.subTest(parts=parts):
                transport = Transport(response(parts, stop, USAGE))
                output = self.client(transport, max_retries=3).generate("Find", tools=TOOLS)
                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(output.request_attempts, 1)
                self.assertEqual(output.finish_reason, "length" if stop == "MAX_TOKENS" else "stop")
                self.assertEqual(output.text, "partial" if stop == "MAX_TOKENS" else "")

    def test_empty_parts_preserved_in_trace_and_omitted_from_repair_wire(self):
        transport = Transport(response([]), response())
        client = self.client(transport)
        first = client.generate("Find")
        history = [{"role": "user", "content": "Find"}, first.assistant_message,
                   {"role": "user", "content": "Protocol error: please answer"}]
        client.generate(history)
        self.assertEqual(first.assistant_message[CONTENT_FIELD]["parts"], [])
        wire = json.loads(transport.requests[1].data)
        self.assertTrue(all(content["parts"] for content in wire["contents"]))
        self.assertEqual(len(wire["contents"]), 2)

    def test_empty_unsigned_text_is_omitted_but_empty_signed_part_is_preserved(self):
        for parts, expected_count in (([{"text": ""}], 2),
                                      ([{"text": "", "thoughtSignature": "opaque"}], 3)):
            with self.subTest(parts=parts):
                transport = Transport(response(parts), response())
                client = self.client(transport)
                first = client.generate("Find")
                client.generate([{"role": "user", "content": "Find"}, first.assistant_message,
                                 {"role": "user", "content": "Please answer"}])
                self.assertEqual(len(json.loads(transport.requests[1].data)["contents"]), expected_count)
                self.assertEqual(first.assistant_message[CONTENT_FIELD]["parts"], parts)

    def test_explicit_stops_and_prompt_blocks_are_terminal_with_usage(self):
        cases = [response([call()], stop=reason, usage=USAGE)
                 for reason in ("SAFETY", "MALFORMED_FUNCTION_CALL", "OTHER")]
        cases.append({"promptFeedback": {"blockReason": "SAFETY"}, "usageMetadata": USAGE})
        for value in cases:
            with self.subTest(value=value):
                transport = Transport(value)
                with self.assertRaises(APICompletionAbortedError) as caught:
                    self.client(transport, max_retries=3).generate("Find", tools=TOOLS)
                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(caught.exception.attempt_usage[0]["provider_usage"], USAGE)

    def test_malformed_accounting_and_response_never_retry(self):
        for value in (response(usage={"promptTokenCount": True}), response(usage={"thoughtsTokenCount": -1}),
                      response(usage={"totalTokenCount": 1, "promptTokenCount": 2}),
                      {"candidates": []}, b"not JSON"):
            with self.subTest(value=value):
                transport = Transport(value)
                with self.assertRaises(APIClientError):
                    self.client(transport, max_retries=3).generate("Find")
                self.assertEqual(len(transport.requests), 1)

    def test_usage_unknowns_and_total_derived_completion(self):
        transport = Transport(response(usage={"promptTokenCount": 5, "candidatesTokenCount": 2}),
                              response(usage={"promptTokenCount": 5, "totalTokenCount": 9}))
        client = self.client(transport)
        first = client.generate("Find")
        self.assertIsNone(first.completion_tokens)
        self.assertIsNone(first.cached_prompt_tokens)
        second = client.generate("Find")
        self.assertEqual(second.completion_tokens, 4)
        self.assertIsNone(second.attempt_usage[0]["usage"]["completion_tokens_details"]["reasoning_tokens"])

    def test_every_transport_attempt_and_native_dump_are_secret_safe(self):
        error_body = {"error": {"message": "private-gemini-test-key", "x-goog-api-key": "other-key"},
                      "usageMetadata": USAGE}
        error = urllib.error.HTTPError("http://localhost", 503, "Unavailable", {},
                                       io.BytesIO(json.dumps(error_body).encode()))
        transport = Transport(error, response([{"text": "Answer: private-gemini-test-key"}], usage=USAGE))
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
            client = self.client(transport, max_retries=1, retry_base_seconds=0)
            output = client.generate("Find", tools=TOOLS)
            self.assertEqual([entry["state"] for entry in output.attempt_usage], ["error", "success"])
            self.assertEqual(output.attempt_usage[0]["http_status"], 503)
            files = list(Path(directory).glob("*.json"))
            self.assertEqual(len(files), 2)
            for path in files:
                text = path.read_text()
                self.assertNotIn("private-gemini-test-key", text)
                self.assertNotIn("other-key", text)
                data = json.loads(text)
                self.assertIn("contents", data["request_payload"])
                self.assertNotIn("messages", data["request_payload"])
                self.assertNotIn("headers", data)
                compatibility = data["context"]["parameter_compatibility"]
                self.assertEqual(compatibility["tool_schema_format"], "parametersJsonSchema")
                self.assertEqual(compatibility["tool_schema_preservation"], "deepcopy_unchanged")
                self.assertIs(compatibility["tool_schema_coercion"], False)
                declaration = data["request_payload"]["tools"][0]["functionDeclarations"][0]
                self.assertNotIn("parameters", declaration)
                self.assertEqual(declaration["parametersJsonSchema"], TOOLS[0]["function"]["parameters"])

    def test_runner_executes_tool_and_forces_final_with_complete_history(self):
        transport = Transport(response([call()], usage=USAGE), response(usage=USAGE))
        client = self.client(transport)
        executed = []
        def lookup(argument):
            executed.append(argument)
            return "London", 1.0
        result = run_react_loop(client, {"lookup": lookup}, context="Find Ada",
                                max_steps=1, max_evals=1, tool_protocol="native",
                                answer_evaluator=lambda _: 1.0)
        self.assertEqual(len(executed), 1)
        self.assertEqual(result["answer"], "done")
        wire = json.loads(transport.requests[1].data)
        self.assertEqual(wire["toolConfig"]["functionCallingConfig"]["mode"], "NONE")
        self.assertTrue(any("functionResponse" in part for content in wire["contents"] for part in content["parts"]))

    def test_shared_cli_factory_selects_native_gemini(self):
        import demo_experiment
        parser = argparse.ArgumentParser()
        demo_experiment._add_generation_arguments(parser)
        args = parser.parse_args(["--api-protocol", "gemini", "--reasoning-effort", "medium"])
        args.api_key, args.model, args.seed = "test-key", "unfamiliar-model", 3
        args.base_url = "http://127.0.0.1:8080/antigravity/v1beta"
        client = demo_experiment.build_llm("sub2api", [], args)
        self.assertIsInstance(client, NativeGeminiLLM)
        self.assertEqual(client.config.reasoning_effort, "medium")

    def test_sse_keeps_early_function_call_when_terminal_event_has_empty_text(self):
        tool = response([call()])
        tool["candidates"][0].pop("finishReason")
        empty_terminal = response([{"text": ""}])
        wire_bytes = sse(tool, empty_terminal, {"usageMetadata": USAGE})
        transport = Transport(wire_bytes, response())
        client = self.client(transport)
        first = client.generate("Find", tools=TOOLS)
        self.assertEqual(first.tool_calls[0]["id"], "call-1")
        self.assertEqual(first.assistant_message[CONTENT_FIELD]["parts"], [call(), {"text": ""}])
        self.assertEqual(first.completion_tokens, 10)
        self.assertEqual(first.attempt_usage[0]["provider_usage"], USAGE)
        client.generate([{"role": "user", "content": "Find"}, first.assistant_message,
                         {"role": "tool", "tool_call_id": "call-1", "content": "value"}], tools=TOOLS)
        second_wire = json.loads(transport.requests[1].data)
        self.assertEqual(second_wire["contents"][1]["parts"][0], call())

    def test_sse_text_fragments_concatenate_and_cumulative_usage_is_not_summed(self):
        first = response([{"thought": True, "text": "reason"}, {"text": "Ans"}], usage={"promptTokenCount": 11})
        first["candidates"][0].pop("finishReason")
        second = response([{"text": "wer: done", "thoughtSignature": "signed-text"}], usage=USAGE)
        output = self.client(Transport(sse(first, second) + b"data: [DONE]\n\n")).generate("Find")
        self.assertEqual(output.text, "Answer: done")
        self.assertEqual(output.prompt_tokens, 11)
        self.assertEqual(output.completion_tokens, 10)
        self.assertEqual(output.assistant_message[CONTENT_FIELD]["parts"][2]["thoughtSignature"], "signed-text")

    def test_sse_error_after_partial_call_is_terminal_not_a_tool_decision(self):
        partial = response([call()], usage=USAGE)
        partial["candidates"][0].pop("finishReason")
        raw = sse(partial) + b'event: error\ndata: {"error":{"message":"upstream disconnected"}}\n\n'
        transport = Transport(raw)
        with self.assertRaises(APICompletionAbortedError) as caught:
            self.client(transport, max_retries=3).generate("Find", tools=TOOLS)
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(caught.exception.attempt_usage[0]["provider_usage"], USAGE)

    def test_truncated_sse_retains_known_usage_and_is_not_retried(self):
        partial = response([{"text": "part"}], usage=USAGE)
        partial["candidates"][0].pop("finishReason")
        for raw in (sse(partial), sse(partial) + b'data: {bad json}\n\n'):
            with self.subTest(raw=raw):
                transport = Transport(raw)
                with self.assertRaises(APIClientError) as caught:
                    self.client(transport, max_retries=3).generate("Find")
                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(caught.exception.attempt_usage[0]["provider_usage"], USAGE)

    def test_sse_dump_preserves_raw_events_and_redacts_echoed_header_fields(self):
        normal = sse(response(usage=USAGE))
        secret = sse({"error": {"message": "private-gemini-test-key", "x-goog-api-key": "other-key"},
                      "usageMetadata": USAGE})
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
            client = self.client(Transport(normal, secret))
            client.generate("Find")
            first = next(Path(directory).glob("*.json"))
            self.assertEqual(json.loads(first.read_text())["response_raw"], normal.decode())
            with self.assertRaises(APICompletionAbortedError):
                client.generate("Find")
            for path in Path(directory).glob("*.json"):
                text = path.read_text()
                self.assertNotIn("private-gemini-test-key", text)
                self.assertNotIn("other-key", text)

    def test_quota_hook_only_exposes_complete_decision_free_error(self):
        client = self.client(Transport())
        quota = {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED",
                           "message": "Quota exhausted", "details": [{"retryDelay": "60s"}]}}
        found = client._quota_error_response(sse(quota))
        self.assertEqual(found[0], 429)
        self.assertEqual(json.loads(found[1]), quota)
        self.assertIsNone(client._quota_error_response(sse(response([call()]), quota)))
        self.assertIsNone(client._quota_error_response(sse(response([]), quota)))
        self.assertIsNone(client._quota_error_response(sse({"usageMetadata": {"thoughtsTokenCount": 1}}, quota)))
        self.assertIsNone(client._quota_error_response(sse({"error": {"code": 400, "message": "blocked"}})))
        self.assertIsNone(client._quota_error_response(sse(quota) + b"data: {incomplete"))

    def test_plain_json_quota_hook_preserves_decision_and_error_guards(self):
        client = self.client(Transport())
        for code, status in ((429, "RESOURCE_EXHAUSTED"), (503, "UNAVAILABLE")):
            quota = {"error": {"code": code, "status": status, "message": "Quota exhausted"}}
            found = client._quota_error_response(json.dumps(quota).encode())
            self.assertEqual(found[0], code)
            self.assertEqual(json.loads(found[1]), quota)
            with_candidates = {**quota, "candidates": response([call()])["candidates"]}
            with_tokens = {**quota, "usageMetadata": {"candidatesTokenCount": 1}}
            self.assertIsNone(client._quota_error_response(json.dumps(with_candidates).encode()))
            self.assertIsNone(client._quota_error_response(json.dumps(with_tokens).encode()))
        self.assertIsNone(client._quota_error_response(b'{"error":{"code":400,"message":"blocked"}}'))
        self.assertIsNone(client._quota_error_response(b'{"error":'))

    def test_default_transport_partial_sse_is_saved_with_usage_and_never_retried(self):
        partial = response([call()], usage=USAGE)
        partial["candidates"][0].pop("finishReason")
        first_chunk = sse(partial)
        tails = [(TimeoutError("private-gemini-test-key"), b""),
                 (http.client.IncompleteRead(b"data: {", 20), b"data: {")]
        for error, tail in tails:
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as directory:
                http_response = mock.MagicMock()
                http_response.__enter__.return_value = http_response
                http_response.read1.side_effect = [first_chunk, error]
                with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}), mock.patch(
                        "expgym.native_gemini_client.urllib.request.urlopen", return_value=http_response) as opened:
                    client = NativeGeminiLLM(api_key="private-gemini-test-key", model="unfamiliar-model",
                                             base_url="http://localhost/v1beta", max_retries=3,
                                             retry_base_seconds=0)
                    self.assertIs(client._transport, _gemini_transport)
                    with self.assertRaises(PartialAPIResponseError) as caught:
                        client.generate("Find", tools=TOOLS)
                opened.assert_called_once()
                self.assertEqual(http_response.read1.call_count, 2)
                self.assertEqual(caught.exception.partial_response, first_chunk + tail)
                attempt = caught.exception.attempt_usage[0]
                self.assertEqual(attempt["provider_usage"], USAGE)
                self.assertTrue(attempt["response_partial"])
                self.assertTrue(attempt["usage_partial"])
                saved = json.loads(next(Path(directory).glob("*.json")).read_text())
                self.assertEqual(saved["response_raw"], (first_chunk + tail).decode())
                self.assertTrue(saved["response_partial"])
                self.assertEqual(saved["state"], "error")
                self.assertNotIn("private-gemini-test-key", json.dumps(saved))

    def test_incremental_transport_keeps_first_read_incomplete_partial_and_read_fallback(self):
        request = mock.Mock()
        http_response = mock.MagicMock()
        http_response.__enter__.return_value = http_response
        http_response.read1 = None
        http_response.read.side_effect = http.client.IncompleteRead(b"data: {", 8)
        with mock.patch("expgym.native_gemini_client.urllib.request.urlopen", return_value=http_response):
            with self.assertRaises(PartialAPIResponseError) as caught:
                _gemini_transport(request, 1)
        self.assertEqual(caught.exception.partial_response, b"data: {")
        http_response.read.assert_called_once_with(65536)

    def test_default_transport_no_bytes_timeout_keeps_bounded_retry(self):
        failed = mock.MagicMock()
        failed.__enter__.return_value = failed
        failed.read1.side_effect = TimeoutError("connection timed out")
        succeeded = mock.MagicMock()
        succeeded.__enter__.return_value = succeeded
        succeeded.read1.side_effect = [sse(response(usage=USAGE)), b""]
        with mock.patch("expgym.native_gemini_client.urllib.request.urlopen",
                        side_effect=[failed, succeeded]) as opened:
            client = NativeGeminiLLM(api_key="test-key", model="unfamiliar-model",
                                     base_url="http://localhost/v1beta", max_retries=1,
                                     retry_base_seconds=0)
            result = client.generate("Find")
        self.assertEqual(opened.call_count, 2)
        self.assertEqual(result.request_attempts, 2)
        self.assertEqual(result.text, "Answer: done")


if __name__ == "__main__":
    unittest.main()
