import json
import os
import tempfile
import unittest
import urllib.error
from dataclasses import asdict
from email.message import Message
from io import BytesIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

from expgym.llm_clients import (
    DEFAULT_GEMINI_URL,
    DEFAULT_OPENROUTER_URL,
    DEFAULT_SUB2API_URL,
    DEFAULT_VLLM_URL,
    OpenAICompatibleLLM,
    build_gemini_client,
    build_openrouter_client,
    build_sub2api_client,
    build_vllm_client,
)


class _CaptureTransport:
    def __init__(self, payload: dict):
        self.payload = payload
        self.request = None
        self.timeout = None

    def __call__(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return json.dumps(self.payload).encode("utf-8")


class _SequenceTransport:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = 0

    def __call__(self, _request, _timeout):
        payload = self.payloads[self.calls]
        self.calls += 1
        return json.dumps(payload).encode("utf-8")


class OpenAICompatibleLLMTest(unittest.TestCase):
    def test_generate_parses_choice_and_builds_request(self) -> None:
        payload = {
            "choices": [{"message": {"content": "Answer"}}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 25,
                "prompt_tokens_details": {
                    "cached_tokens": 80,
                    "cache_write_tokens": 20,
                },
            },
        }
        transport = _CaptureTransport(payload)
        llm = OpenAICompatibleLLM(
            api_key="test",
            model="gpt-test",
            seed=1206,
            prompt_cache_key="expgym-task-abc-v1",
            transport=transport,
        )
        output = llm.generate("Hi")
        self.assertEqual(output.text, "Answer")
        self.assertEqual(output.prompt_tokens, 100)
        self.assertEqual(output.completion_tokens, 25)
        self.assertEqual(output.cached_prompt_tokens, 80)
        self.assertEqual(output.cache_write_prompt_tokens, 20)
        self.assertEqual(output.request_attempts, 1)
        self.assertEqual(transport.request.get_full_url(), llm.config.base_url)
        body = json.loads(transport.request.data.decode("utf-8"))
        self.assertEqual(body["model"], "gpt-test")
        self.assertEqual(body["messages"][-1]["content"], "Hi")
        self.assertEqual(body["temperature"], 0.0)
        self.assertEqual(body["top_p"], 1.0)
        self.assertEqual(body["seed"], 1206)
        self.assertEqual(body["prompt_cache_key"], "expgym-task-abc-v1")

    def test_prompt_cache_key_is_omitted_when_unset(self) -> None:
        transport = _CaptureTransport({"choices": [{"message": {"content": "Ok"}}]})
        llm = OpenAICompatibleLLM(api_key="k", transport=transport)
        llm.generate("Hi")
        body = json.loads(transport.request.data.decode("utf-8"))
        self.assertNotIn("prompt_cache_key", body)

    def test_reasoning_effort_is_optional_top_level_and_recorded_in_config(self) -> None:
        for effort in (None, "none", "low", "high", "provider-specific-effort"):
            with self.subTest(effort=effort):
                transport = _CaptureTransport({"choices": [{"message": {"content": "Ok"}}]})
                llm = OpenAICompatibleLLM(
                    api_key="k", transport=transport, reasoning_effort=effort,
                    chat_template_kwargs={"some_template_flag": True},
                )
                llm.generate("Hi")
                body = json.loads(transport.request.data.decode("utf-8"))
                self.assertEqual(asdict(llm.config)["reasoning_effort"], effort)
                if effort is None:
                    self.assertNotIn("reasoning_effort", body)
                else:
                    self.assertEqual(body["reasoning_effort"], effort)
                self.assertEqual(body["chat_template_kwargs"], {"some_template_flag": True})

    def test_invalid_reasoning_effort_is_rejected_before_transport(self) -> None:
        for effort in ("", "  ", 1, False, {"effort": "high"}):
            with self.subTest(effort=effort):
                with self.assertRaisesRegex(ValueError, "reasoning_effort"):
                    OpenAICompatibleLLM(api_key="k", reasoning_effort=effort)

    def test_conflicting_explicit_reasoning_controls_are_rejected(self) -> None:
        for effort, enabled in (("high", False), ("low", False), ("none", True)):
            with self.subTest(effort=effort, enabled=enabled):
                with self.assertRaisesRegex(ValueError, "conflicts with explicit reasoning.enabled"):
                    OpenAICompatibleLLM(
                        api_key="k", reasoning_effort=effort, reasoning={"enabled": enabled},
                    )

    def test_explicit_disabled_reasoning_controls_are_compatible(self) -> None:
        transport = _CaptureTransport({"choices": [{"message": {"content": "Ok"}}]})
        llm = OpenAICompatibleLLM(
            api_key="k", transport=transport, reasoning_effort="none", reasoning={"enabled": False},
        )
        llm.generate("Hi")
        payload = json.loads(transport.request.data.decode("utf-8"))
        self.assertEqual(payload["reasoning_effort"], "none")
        self.assertEqual(payload["reasoning"], {"enabled": False})

    def test_missing_api_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            OpenAICompatibleLLM(api_key="")

    def test_custom_base_url(self) -> None:
        url = "https://example.com/chat"
        payload = {
            "choices": [{"message": {"content": "Ok"}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
        transport = _CaptureTransport(payload)
        llm = OpenAICompatibleLLM(api_key="k", base_url=url, transport=transport)
        result = llm.generate("Prompt")
        self.assertEqual(result.prompt_tokens, 0)
        self.assertEqual(transport.request.get_full_url(), url)

    def test_base_url_accepts_openai_compatible_base(self) -> None:
        cases = {
            "http://localhost:8000": "http://localhost:8000/v1/chat/completions",
            "http://localhost:8000/v1": "http://localhost:8000/v1/chat/completions",
            "https://openrouter.ai/api/v1": "https://openrouter.ai/api/v1/chat/completions",
            "https://example.com/v1/chat/completions": "https://example.com/v1/chat/completions",
        }
        for given, expected in cases.items():
            with self.subTest(given=given):
                llm = OpenAICompatibleLLM(api_key="k", base_url=given)
                self.assertEqual(llm.config.base_url, expected)

    def test_max_retries_zero_fails_after_one_attempt(self) -> None:
        calls = 0

        def unavailable(_request, _timeout):
            nonlocal calls
            calls += 1
            raise urllib.error.HTTPError(
                "http://fake",
                503,
                "Unavailable",
                Message(),
                BytesIO(b'{"error":"down"}'),
            )

        llm = OpenAICompatibleLLM(
            api_key="k",
            transport=unavailable,
            max_retries=0,
        )
        with self.assertRaisesRegex(RuntimeError, "API error"):
            llm.generate("test")
        self.assertEqual(calls, 1)

    def test_retry_after_is_bounded(self) -> None:
        headers = Message()
        headers["Retry-After"] = "999"
        llm = OpenAICompatibleLLM(
            api_key="k",
            retry_max_seconds=7,
        )
        self.assertEqual(llm._retry_delay(0, headers), 7)

    def test_empty_delivered_response_is_not_resampled(self) -> None:
        transport = _SequenceTransport(
            [
                {"choices": [{"message": {"content": None}}]},
                {"choices": [{"message": {"content": "Recovered"}}]},
            ]
        )
        llm = OpenAICompatibleLLM(
            api_key="k",
            transport=transport,
            max_retries=1,
            retry_base_seconds=0,
        )

        output = llm.generate("test")

        self.assertEqual(output.text, "")
        self.assertEqual(output.request_attempts, 1)
        self.assertEqual(transport.calls, 1)
        self.assertIsNone(output.assistant_message["content"])

    def test_missing_message_fails_without_resampling(self) -> None:
        transport = _CaptureTransport(
            {"choices": [{}]}
        )
        llm = OpenAICompatibleLLM(
            api_key="k",
            transport=transport,
            max_retries=3,
        )
        with self.assertRaisesRegex(RuntimeError, "missing message content"):
            llm.generate("test")


class APIAttemptDumpTest(unittest.TestCase):
    def _records(self, directory):
        return [json.loads(path.read_text(encoding="utf-8")) for path in Path(directory).glob("*.json")]

    def test_dump_preserves_raw_reasoning_usage_and_pending_request(self):
        response = {
            "id": "chatcmpl-test",
            "choices": [{"message": {"role": "assistant", "content": " Answer ", "reasoning_content": "reasoning 中文"}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 19, "completion_tokens_details": {"reasoning_tokens": 16}},
        }
        raw = json.dumps(response, ensure_ascii=False).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            def transport(_request, _timeout):
                pending = self._records(directory)
                self.assertEqual(len(pending), 1)
                self.assertEqual(pending[0]["state"], "in_progress")
                return raw

            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory, "EXPGYM_RUN_ID": "pilot-search-0"}):
                llm = OpenAICompatibleLLM(
                    api_key="credential-never-persist", transport=transport,
                    max_tokens=8192, chat_template_kwargs={"thinking": True},
                    reasoning_effort="high",
                    dump_context={"strategy": "poolact", "agent_id": 2},
                )
                output = llm.generate("Prompt")
            self.assertEqual(output.text, "Answer")
            self.assertEqual(output.completion_tokens, 19)
            records = self._records(directory)
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["state"], "success")
            self.assertEqual(record["response_json"], response)
            self.assertEqual(record["response_raw"], raw.decode("utf-8"))
            self.assertEqual(record["run_id"], "pilot-search-0")
            self.assertEqual(record["context"]["agent_id"], 2)
            self.assertEqual(record["request_payload"]["max_tokens"], 8192)
            self.assertEqual(record["request_payload"]["chat_template_kwargs"], {"thinking": True})
            self.assertEqual(record["request_payload"]["reasoning_effort"], "high")
            self.assertEqual(record["pid"], os.getpid())
            self.assertIsInstance(record["thread_id"], int)
            self.assertGreaterEqual(record["wall_time_seconds"], 0)
            self.assertTrue(record["started_at_utc"])
            self.assertTrue(record["finished_at_utc"])
            self.assertFalse(record["will_retry"])
            self.assertIsNone(record["error"])
            self.assertFalse(list(Path(directory).glob("*.tmp")))

    def test_every_retry_keeps_response_and_generation_identity(self):
        responses = [
            urllib.error.HTTPError("http://fake", 503, "Unavailable", Message(), BytesIO(b'{"error":"down"}')),
            urllib.error.URLError("connection lost"),
            b'{"choices":[{"message":{"content":null,"reasoning_content":"truncated"}}]}',
            b'{"choices":[{"message":{"content":"Recovered"}}]}',
        ]
        with tempfile.TemporaryDirectory() as directory:
            def transport(_request, _timeout):
                response = responses.pop(0)
                if isinstance(response, Exception):
                    raise response
                return response

            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
                llm = OpenAICompatibleLLM(
                    api_key="credential-never-persist", transport=transport,
                    max_retries=3, retry_base_seconds=0,
                )
                output = llm.generate("Prompt")
            records = sorted(self._records(directory), key=lambda record: record["attempt"])
            # HTTP/connection failures retry, but the delivered reasoning-only
            # completion must consume a loop decision instead of being replaced.
            self.assertEqual(output.text, "")
            self.assertEqual(output.request_attempts, 3)
            self.assertEqual(len(records), 3)
            self.assertEqual(len({record["generation_id"] for record in records}), 1)
            self.assertEqual(len({record["request_id"] for record in records}), 3)
            self.assertEqual([record["attempt"] for record in records], [1, 2, 3])
            self.assertTrue(all(record["will_retry"] for record in records[:-1]))
            self.assertEqual(records[0]["http_status"], 503)
            self.assertEqual(records[0]["response_json"], {"error": "down"})
            self.assertEqual(records[1]["error"]["type"], "URLError")
            self.assertEqual(records[2]["state"], "success")
            self.assertEqual(records[2]["response_json"]["choices"][0]["message"]["reasoning_content"], "truncated")
            self.assertFalse(records[2]["will_retry"])
            self.assertEqual(len(responses), 1)
            self.assertEqual(len(output.attempt_usage), 3)
            self.assertTrue(all(record["usage"] is None for record in output.attempt_usage))

    def test_terminal_invalid_response_is_dumped_before_raise(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
                llm = OpenAICompatibleLLM(
                    api_key="credential-never-persist", transport=lambda request, timeout: b'bad json \xff',
                    max_retries=0,
                )
                with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
                    llm.generate("Prompt")
            record = self._records(directory)[0]
            self.assertEqual(record["state"], "malformed_response")
            self.assertEqual(record["response_raw"], 'bad json \\xff')
            self.assertFalse(record["will_retry"])

    def test_dump_redacts_credentials_and_never_serializes_headers_or_url_secrets(self):
        api_key = "credential-never-persist"
        header_key = "extra-header-credential"
        response = {
            "choices": [{"message": {"content": "safe " + api_key + " " + header_key}}],
            "api_key": "echoed-provider-secret",
            "details": {"access_token": "provider-token-secret"},
        }
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
                llm = OpenAICompatibleLLM(
                    api_key=api_key, extra_headers={"X-Api-Key": header_key},
                    base_url="http://username:url-password@fake/v1/chat/completions?key=query-secret",
                    transport=_CaptureTransport(response),
                )
                output = llm.generate("Prompt")
            self.assertIn(api_key, output.text)  # Redaction only affects the audit dump.
            paths = list(Path(directory).glob("*.json"))
            saved = paths[0].read_text(encoding="utf-8")
            for secret in (api_key, header_key, "echoed-provider-secret", "provider-token-secret", "url-password", "query-secret"):
                self.assertNotIn(secret, saved)
            self.assertNotIn("Authorization", saved)
            self.assertNotIn("X-Api-Key", saved)
            self.assertEqual(json.loads(saved)["endpoint"], "http://fake/v1/chat/completions")

    def test_concurrent_clients_produce_unique_complete_files(self):
        transport = _CaptureTransport({"choices": [{"message": {"content": "Answer"}}]})
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": directory}):
                clients = [OpenAICompatibleLLM(api_key="credential-never-persist", transport=transport) for _ in range(2)]
                with ThreadPoolExecutor(max_workers=4) as executor:
                    outputs = list(executor.map(lambda index: clients[index % 2].generate("Prompt"), range(8)))
            records = self._records(directory)
            self.assertEqual(len(outputs), 8)
            self.assertEqual(len(records), 8)
            self.assertEqual(len({record["request_id"] for record in records}), 8)
            self.assertEqual(len({record["client_id"] for record in records}), 2)
            self.assertTrue(all(record["state"] == "success" for record in records))
            self.assertFalse(list(Path(directory).glob("*.tmp")))

    def test_requested_dump_failure_prevents_undocumented_api_call(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid_directory = Path(directory) / "a-file"
            invalid_directory.touch()
            transport = mock.Mock()
            with mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": str(invalid_directory)}):
                llm = OpenAICompatibleLLM(api_key="credential-never-persist", transport=transport)
                with self.assertRaises(OSError):
                    llm.generate("Prompt")
            transport.assert_not_called()


class GeminiHelperTest(unittest.TestCase):
    def test_build_gemini_client_uses_default_url(self) -> None:
        transport = _CaptureTransport({"choices": [{"message": {"content": "Gem"}}]})
        llm = build_gemini_client(api_key="gkey", transport=transport)
        llm.generate("hi")
        self.assertEqual(llm.config.base_url, DEFAULT_GEMINI_URL)
        self.assertEqual(transport.request.get_full_url(), DEFAULT_GEMINI_URL)

    def test_missing_api_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_gemini_client(api_key="")


class OpenRouterHelperTest(unittest.TestCase):
    def test_explicit_reasoning_effort_does_not_inherit_disable_reasoning_default(self) -> None:
        transport = _CaptureTransport({"choices": [{"message": {"content": "OpenRouter"}}]})
        llm = build_openrouter_client(
            api_key="orkey", reasoning_effort="high", transport=transport,
        )
        llm.generate("Hi")
        payload = json.loads(transport.request.data.decode("utf-8"))
        self.assertEqual(payload["reasoning_effort"], "high")
        self.assertNotIn("reasoning", payload)

    def test_reasoning_effort_does_not_overwrite_explicit_provider_reasoning(self) -> None:
        transport = _CaptureTransport({"choices": [{"message": {"content": "OpenRouter"}}]})
        llm = build_openrouter_client(
            api_key="orkey", reasoning_effort="high", reasoning={"enabled": True},
            transport=transport,
        )
        llm.generate("Hi")
        payload = json.loads(transport.request.data.decode("utf-8"))
        self.assertEqual(payload["reasoning_effort"], "high")
        self.assertEqual(payload["reasoning"], {"enabled": True})

    def test_build_openrouter_client_sets_headers(self) -> None:
        payload = {
            "choices": [{"message": {"content": "OpenRouter"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2},
        }
        transport = _CaptureTransport(payload)
        llm = build_openrouter_client(
            api_key="orkey",
            referer="https://example.com",
            title="ExpGym",
            transport=transport,
        )
        llm.generate("hi")
        headers = {k.lower(): v for k, v in transport.request.header_items()}
        self.assertEqual(transport.request.get_full_url(), DEFAULT_OPENROUTER_URL)
        self.assertEqual(headers.get("http-referer"), "https://example.com")
        self.assertEqual(headers.get("x-title"), "ExpGym")

    def test_missing_api_key_raises(self) -> None:
        import os
        from unittest import mock

        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            with self.assertRaises(ValueError):
                build_openrouter_client(api_key="")


class VLLMHelperTest(unittest.TestCase):
    def test_build_vllm_client_uses_default_url(self) -> None:
        payload = {
            "choices": [{"message": {"content": "vLLM"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2},
        }
        transport = _CaptureTransport(payload)
        llm = build_vllm_client(
            api_key="vkey",
            chat_template_kwargs={"enable_thinking": False},
            transport=transport,
        )
        llm.generate("hi")
        self.assertEqual(llm.config.base_url, DEFAULT_VLLM_URL)
        self.assertEqual(transport.request.get_full_url(), DEFAULT_VLLM_URL)
        body = json.loads(transport.request.data.decode("utf-8"))
        self.assertEqual(body.get("chat_template_kwargs"), {"enable_thinking": False})


class Sub2APIHelperTest(unittest.TestCase):
    def test_build_sub2api_client_uses_env_and_default_url(self) -> None:
        import os
        from unittest import mock

        transport = _CaptureTransport({"choices": [{"message": {"content": "Sub2"}}]})
        with mock.patch.dict(
            os.environ,
            {"SUB2API_API_KEY": "sub2-key", "SUB2API_BASE_URL": ""},
            clear=False,
        ):
            llm = build_sub2api_client(
                model="gpt-5.4",
                prompt_cache_key="expgym-sub2-v1",
                transport=transport,
            )
        llm.generate("hi")
        self.assertEqual(llm.config.base_url, DEFAULT_SUB2API_URL)
        body = json.loads(transport.request.data.decode("utf-8"))
        self.assertEqual(body["prompt_cache_key"], "expgym-sub2-v1")

    def test_missing_api_key_raises(self) -> None:
        import os
        from unittest import mock

        with mock.patch.dict(os.environ, {"SUB2API_API_KEY": ""}, clear=False):
            with self.assertRaises(ValueError):
                build_sub2api_client(api_key="")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
