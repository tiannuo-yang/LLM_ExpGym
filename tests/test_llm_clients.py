import json
import unittest
import urllib.error
from email.message import Message
from io import BytesIO

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

    def test_retries_empty_success_response(self) -> None:
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

        self.assertEqual(output.text, "Recovered")
        self.assertEqual(output.request_attempts, 2)
        self.assertEqual(transport.calls, 2)

    def test_empty_response_fails_after_retry_limit(self) -> None:
        transport = _CaptureTransport(
            {"choices": [{"message": {"content": None}}]}
        )
        llm = OpenAICompatibleLLM(
            api_key="k",
            transport=transport,
            max_retries=0,
        )
        with self.assertRaisesRegex(RuntimeError, "missing message content"):
            llm.generate("test")


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
