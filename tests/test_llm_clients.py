import json
import unittest

from expgym.llm_clients import (
    DEFAULT_GEMINI_URL,
    DEFAULT_OPENROUTER_URL,
    DEFAULT_VLLM_URL,
    OpenAICompatibleLLM,
    build_gemini_client,
    build_openrouter_client,
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


class OpenAICompatibleLLMTest(unittest.TestCase):
    def test_generate_parses_choice_and_builds_request(self) -> None:
        payload = {
            "choices": [{"message": {"content": "Answer"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 25},
        }
        transport = _CaptureTransport(payload)
        llm = OpenAICompatibleLLM(
            api_key="test",
            model="gpt-test",
            seed=1206,
            transport=transport,
        )
        output = llm.generate("Hi")
        self.assertEqual(output.text, "Answer")
        self.assertEqual(output.prompt_tokens, 100)
        self.assertEqual(output.completion_tokens, 25)
        self.assertEqual(transport.request.get_full_url(), llm.config.base_url)
        body = json.loads(transport.request.data.decode("utf-8"))
        self.assertEqual(body["model"], "gpt-test")
        self.assertEqual(body["messages"][-1]["content"], "Hi")
        self.assertEqual(body["temperature"], 0.0)
        self.assertEqual(body["top_p"], 1.0)
        self.assertEqual(body["seed"], 1206)

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
