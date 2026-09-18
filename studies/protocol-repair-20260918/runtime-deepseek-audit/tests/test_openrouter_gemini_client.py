"""No-network parity, signed-history, and terminal-failure checks."""
import copy
import http.client
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import demo_experiment
from expgym.llm_clients import APICompletionAbortedError, PartialAPIResponseError
from expgym.openrouter_gemini_client import MODEL, PROVIDER, OpenRouterGeminiLLM
from expgym.react_loop import run_react_loop
from tests.test_native_gemini_client import COMPLEX_PARAMETERS


TOOLS = [{"type": "function", "function": {
    "name": "evaluate_config", "description": "Evaluate", "parameters": COMPLEX_PARAMETERS,
}}]


def response(message=None, finish="stop", native="STOP"):
    return {"model": MODEL, "provider": "Google AI Studio", "id": "generation-1",
            "choices": [{"finish_reason": finish, "native_finish_reason": native,
                         "message": message or {"role": "assistant", "content": "Answer: done"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18,
                      "completion_tokens_details": {"reasoning_tokens": 5}}}


def signed_call(arguments='{"x":1}'):
    return {"role": "assistant", "content": None,
            "reasoning_details": [{"type": "reasoning.encrypted", "data": "opaque-signature",
                                   "id": "call-1", "format": "google-gemini-v1", "index": 0}],
            "tool_calls": [{"id": "call-1", "type": "function",
                            "function": {"name": "evaluate_config", "arguments": arguments},
                            "extra_content": {"google": {"thought_signature": "opaque-extra"}}}]}


class Transport:
    def __init__(self, *responses):
        self.responses, self.requests = list(responses), []

    def __call__(self, request, timeout):
        self.requests.append(request)
        return json.dumps(self.responses.pop(0)).encode()


class OpenRouterGeminiTest(unittest.TestCase):
    def client(self, transport=None, **kwargs):
        if transport is not None:
            kwargs["transport"] = transport
        return OpenRouterGeminiLLM(api_key="private-test-key", model=MODEL,
                                   temperature=1.0, top_p=1.0, seed=2200,
                                   max_tokens=32768, reasoning_effort="medium", **kwargs)

    def test_wire_settings_exact_schema_and_secret_free_actual_dump(self):
        transport = Transport(response())
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"EXPGYM_API_DUMP_DIR": directory}
        ):
            client = self.client(transport, prompt_cache_key="task-key")
            client.generate([{"role": "system", "content": "Exact 中文\n"},
                             {"role": "user", "content": "Task"}], tools=TOOLS, tool_choice="none")
            payload = json.loads(transport.requests[0].data)
            self.assertEqual(payload["tools"], TOOLS)
            self.assertEqual(payload["messages"][0]["content"], "Exact 中文\n")
            self.assertEqual(payload["reasoning"], {"effort": "medium", "exclude": False})
            self.assertEqual(payload["provider"], PROVIDER)
            self.assertEqual((payload["temperature"], payload["top_p"], payload["seed"],
                              payload["max_tokens"]), (1.0, 1.0, 2200, 32768))
            self.assertEqual(payload["transforms"], [])
            self.assertFalse(payload["stream"])
            self.assertEqual(payload["tool_choice"], "none")
            for name in ("reasoning_effort", "prompt_cache_key", "parallel_tool_calls", "top_k"):
                self.assertNotIn(name, payload)
            dump = json.loads(next(Path(directory).glob("*.json")).read_text())
            self.assertEqual(dump["request_payload"], payload)
            self.assertTrue(dump["context"]["parameter_compatibility"]["requires_immutable_history"])
            self.assertNotIn("private-test-key", json.dumps(dump))

    def test_runner_replays_complete_signed_message_without_mutation(self):
        message = signed_call()
        before = copy.deepcopy(message)
        transport = Transport(response(message, "tool_calls"),
                              response({"role": "assistant", "content": 'Answer: {"x":1}'}))
        result = run_react_loop(self.client(transport),
                                {"evaluate_config": lambda _: (.4, 2.)},
                                context="Tune x.", max_steps=3, capture_trace_v2=True)
        second = json.loads(transport.requests[1].data)
        self.assertEqual(second["messages"][-2], before)
        self.assertEqual(second["messages"][-1]["tool_call_id"], "call-1")
        self.assertEqual(message, before)
        self.assertEqual(result["answer_perf"], .4)
        self.assertEqual(result["_trace_v2_capture"]["llm_calls"][0]["output_message"], before)

    def test_reasoning_only_is_delivered_exactly_and_length_remains_length(self):
        message = {"role": "assistant", "reasoning_details": signed_call()["reasoning_details"]}
        transport = Transport(response(message), response(signed_call(), "length", "MAX_TOKENS"),
                              response(signed_call(), "stop", "MAX_TOKENS"))
        client = self.client(transport)
        first = client.generate("Task")
        self.assertEqual(first.assistant_message, message)
        self.assertEqual(first.text, "")
        self.assertEqual(first.request_attempts, 1)
        self.assertEqual(client.generate("Task").finish_reason, "length")
        self.assertEqual(client.generate("Task").finish_reason, "length")

    def test_error_or_blocked_partial_decision_never_retries_or_executes(self):
        failures = [response(signed_call(), reason) for reason in (
            "abort", "content_filter", "error", "unexpected", None)]
        failures += [response(signed_call(), "tool_calls", "SAFETY"),
                     {"error": {"code": 503, "message": "provider error"}}]
        error_choice = response(signed_call(), "tool_calls")
        error_choice["choices"][0]["error"] = {"message": "interrupted"}
        failures.append(error_choice)
        for failure in failures:
            with self.subTest(failure=failure):
                transport = Transport(failure)
                seen = []
                with self.assertRaises(APICompletionAbortedError):
                    run_react_loop(self.client(transport, max_retries=3),
                                   {"evaluate_config": lambda p: seen.append(p)}, max_steps=3)
                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(seen, [])

    def test_invalid_arguments_consume_step_and_force_final_disables_tools(self):
        transport = Transport(response(signed_call("{"), "tool_calls"), response())
        result = run_react_loop(self.client(transport),
                                {"evaluate_config": lambda _: self.fail("invalid tool executed")},
                                max_steps=1, max_protocol_retries=1)
        self.assertEqual(result["agent_steps"], 1)
        self.assertEqual(result["evaluations"], 0)
        self.assertEqual(json.loads(transport.requests[-1].data)["tool_choice"], "none")

    def test_signed_history_over_cap_stops_without_trimming_or_sending(self):
        transport = Transport(response(signed_call(), "tool_calls"))
        result = run_react_loop(self.client(transport),
                                {"evaluate_config": lambda _: ("observation-" * 5000, .4, 2.)},
                                context="Tune x.", max_steps=3, max_context_tokens=1500)
        self.assertEqual(len(transport.requests), 1)
        self.assertTrue(result["aborted"])

    def test_partial_response_bytes_preserved_without_retry(self):
        first = b'{"choices": ['
        http_response = mock.MagicMock()
        http_response.__enter__.return_value = http_response
        http_response.read1.side_effect = [first, http.client.IncompleteRead(b'{', 20)]
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"EXPGYM_API_DUMP_DIR": directory}
        ), mock.patch("expgym.native_gemini_client.urllib.request.urlopen", return_value=http_response) as opened:
            with self.assertRaises(PartialAPIResponseError) as caught:
                self.client(max_retries=3).generate("Task")
            opened.assert_called_once()
            self.assertEqual(caught.exception.partial_response, first + b'{')
            saved = json.loads(next(Path(directory).glob("*.json")).read_text())
            self.assertEqual(saved["response_raw"], (first + b'{').decode())
            self.assertTrue(saved["response_partial"])

    def test_factory_uses_adapter_only_for_exact_openrouter_model(self):
        with mock.patch("sys.argv", ["demo_experiment", "--model", MODEL, "--api-key", "private-test-key",
                                     "--reasoning-effort", "medium", "--max-tokens", "32768"]):
            args = demo_experiment.parse_args()
        client = demo_experiment.build_llm("openrouter", [], args)
        self.assertIsInstance(client, OpenRouterGeminiLLM)
        self.assertEqual(client.config.reasoning, {"effort": "medium", "exclude": False})


if __name__ == "__main__":
    unittest.main()
