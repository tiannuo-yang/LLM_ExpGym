"""Frozen Gemini study transport through OpenRouter Chat Completions.

Only transport representation changes. Complete provider messages, encrypted
reasoning details, and tool-call extensions remain authoritative history.
"""
from __future__ import annotations

import copy
import json
import os

from expgym.llm_clients import DEFAULT_OPENROUTER_URL, OpenAICompatibleLLM
from expgym.native_gemini_client import _gemini_transport


MODEL = "google/gemini-3.8-flash"
PROVIDER = {
    "only": ["google-ai-studio"],
    "ignore": ["google-ai-studio/flex", "google-ai-studio/priority"],
    "allow_fallbacks": False,
    "require_parameters": True,
}


class OpenRouterGeminiLLM(OpenAICompatibleLLM):
    api_protocol = "openrouter_gemini_chat"
    requires_immutable_history = True

    def __init__(self, *, api_key=None, base_url=None, referer=None, title=None, **kwargs):
        if kwargs.get("model", MODEL) != MODEL:
            raise ValueError("This frozen adapter requires " + MODEL)
        kwargs["model"] = MODEL
        effort = kwargs.get("reasoning_effort") or "medium"
        if effort not in ("minimal", "low", "medium", "high"):
            raise ValueError("Gemini thinking level must be minimal, low, medium, or high")
        kwargs["reasoning_effort"] = effort
        reasoning = {"effort": effort, "exclude": False}
        for name, expected in (("reasoning", reasoning), ("provider", PROVIDER)):
            supplied = kwargs.pop(name, None)
            if supplied is not None and supplied != expected:
                raise ValueError(name + " disagrees with the frozen OpenRouter mapping")
            kwargs[name] = copy.deepcopy(expected)
        if kwargs.get("top_k") is not None:
            raise ValueError("Original Gemini study omitted top_k; this endpoint does not advertise it")
        if kwargs.get("chat_template_kwargs") or kwargs.get("nothink_prefix"):
            raise ValueError("Gemini study must not alter prompt or thinking through chat templates")
        headers = dict(kwargs.pop("extra_headers", {}) or {})
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
        kwargs.setdefault("transport", _gemini_transport)
        super().__init__(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
            base_url=base_url or DEFAULT_OPENROUTER_URL,
            extra_headers=headers,
            **kwargs,
        )
        self._dump_context.update({"api_protocol": self.api_protocol,
                                   "parameter_compatibility": self.parameter_compatibility})

    @property
    def parameter_compatibility(self):
        return {
            "api_protocol": self.api_protocol,
            "upstream_transport": "OpenRouter Chat Completions to Google AI Studio",
            "thinking_level": self.config.reasoning_effort,
            "effort_mapping": "reasoning.effort maps to Gemini thinkingLevel",
            "reasoning_max_tokens": "not set; original used level, not a reasoning token budget",
            "max_output_tokens": self.config.max_tokens,
            "requires_immutable_history": True,
            "history": "complete assistant message including reasoning_details and tool-call extensions unchanged",
            "omitted_parameters": {"prompt_cache_key": self.config.prompt_cache_key},
            "seed_semantics": "sent as seed; provider determinism unverified",
            "parallel_tool_calls": "omitted as in native Gemini; one-call rule enforced by runner",
            "tool_schema_preservation": "deepcopy_unchanged",
            "provider_routing": copy.deepcopy(PROVIDER),
            "provider_cache_isolation": "not_guaranteed",
            "prompt_transforms": [],
            "stream": False,
            "usage_semantics": "provider-reported OpenRouter usage; completion includes reasoning",
            "attempt_scope": "client-to-OpenRouter; intermediary retries are not individually observable",
        }

    @staticmethod
    def _wire_payload(payload):
        wire = copy.deepcopy(payload)
        # The level is represented once, through OpenRouter's unified field.
        wire.pop("reasoning_effort", None)
        wire.pop("prompt_cache_key", None)
        wire.pop("parallel_tool_calls", None)
        wire["transforms"] = []
        wire["stream"] = False
        return wire

    def _build_request(self, payload):
        return super()._build_request(self._wire_payload(payload))

    def _dump_attempt(self, metadata, payload, started, **kwargs):
        return super()._dump_attempt(metadata, self._wire_payload(payload), started, **kwargs)

    @classmethod
    def _decode_response(cls, raw):
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("OpenRouter response must be an object")
        choices = data.get("choices")
        if data.get("error"):
            return data, "", [], {"role": "assistant", "content": None}, "abort"
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise ValueError("OpenRouter requires exactly one response choice")
        choice = choices[0]
        finish = choice.get("finish_reason")
        native_finish = choice.get("native_finish_reason")
        if choice.get("error") or finish not in ("stop", "tool_calls", "length") or (
            native_finish is not None and native_finish not in ("STOP", "MAX_TOKENS")
        ):
            # Failed/blocked partial generations are evidence, never decisions.
            return data, "", [], copy.deepcopy(choice.get("message") or {
                "role": "assistant", "content": None}), "abort"
        message = choice.get("message")
        decode_data = data
        if isinstance(message, dict) and "reasoning_details" in message:
            details = message["reasoning_details"]
            if details is not None and (not isinstance(details, list) or any(
                not isinstance(item, dict) for item in details
            )):
                raise ValueError("OpenRouter reasoning_details must be a list of objects or null")
            # A delivered reasoning-only completion must consume a runner step.
            # Add a decoder-only null content field, then restore original bytes
            # at the message level for all future replay and trace capture.
            if not any(key in message for key in (
                "content", "tool_calls", "reasoning_content", "reasoning", "refusal",
            )):
                decode_data = copy.deepcopy(data)
                decode_data["choices"][0]["message"]["content"] = None
        _, text, calls, assistant, finish = super()._decode_response(
            json.dumps(decode_data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        )
        if decode_data is not data:
            assistant = copy.deepcopy(message)
            assistant.setdefault("role", "assistant")
        if native_finish == "MAX_TOKENS":
            finish = "length"
        return data, text, calls, assistant, finish


def build_openrouter_gemini_client(**kwargs):
    return OpenRouterGeminiLLM(**kwargs)
