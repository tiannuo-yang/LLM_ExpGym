"""Explicit Anthropic Messages transport with lossless assistant block replay.

The runner continues to exchange its common message/tool-call representation.
Only this wire boundary maps tools and tool results. Original native content
blocks (including opaque thinking signatures) and raw API responses are retained.
Retry policy, failure accounting and credential-safe dumps are inherited from
the common client; no model-name heuristics select capabilities.
"""
from __future__ import annotations

import copy
import json
import urllib.parse
import urllib.request
from typing import Dict, Optional, Sequence

from expgym.llm_clients import OpenAICompatibleLLM


DEFAULT_OMITTED_PARAMETERS = (
    "temperature", "top_p", "top_k", "seed", "prompt_cache_key",
)


def _messages_url(base_url: str) -> str:
    parsed = urllib.parse.urlsplit(base_url.rstrip("/"))
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        path = path[:-len("/chat/completions")] + "/messages"
    elif not path:
        path = "/v1/messages"
    elif not path.endswith("/messages"):
        path += "/messages"
    return urllib.parse.urlunsplit(parsed._replace(path=path))


class NativeAnthropicLLM(OpenAICompatibleLLM):
    """Messages API adapter; capabilities must be supplied explicitly.

    ``omitted_parameters`` describes the configured endpoint's unsupported
    controls. The default is suitable for a Messages endpoint whose sampling
    controls are fixed. Requested values remain in config and dump metadata,
    while the actual native payload omits those fields. An empty tuple permits
    temperature/top_p/top_k, but seed and prompt_cache_key have no native mapping.
    A routing key does not imply physical provider prompt-cache isolation.
    """

    api_protocol = "anthropic"
    requires_immutable_history = True

    def __init__(
        self, *, api_protocol: str = "anthropic",
        omitted_parameters: Sequence[str] = DEFAULT_OMITTED_PARAMETERS,
        thinking: Optional[Dict[str, object]] = None,
        anthropic_version: str = "2023-06-01",
        default_max_tokens: int = 8192,
        **kwargs,
    ) -> None:
        if api_protocol != "anthropic":
            raise ValueError("NativeAnthropicLLM requires api_protocol='anthropic'")
        if isinstance(omitted_parameters, str):
            raise ValueError("omitted_parameters must be a sequence of field names")
        self.omitted_parameters = tuple(omitted_parameters)
        allowed = set(DEFAULT_OMITTED_PARAMETERS) | {"max_tokens"}
        if any(name not in allowed for name in self.omitted_parameters):
            raise ValueError("unsupported omitted_parameters entry")
        if "max_tokens" in self.omitted_parameters:
            raise ValueError("Anthropic Messages requires max_tokens")
        if thinking is not None and not isinstance(thinking, dict):
            raise ValueError("thinking must be an explicit native configuration object")
        if (isinstance(default_max_tokens, bool)
                or not isinstance(default_max_tokens, int) or default_max_tokens < 1):
            raise ValueError("default_max_tokens must be a positive integer")
        if not isinstance(anthropic_version, str) or not anthropic_version.strip():
            raise ValueError("anthropic_version must be non-empty")
        # These controls cannot be translated faithfully by this adapter.
        for field in ("provider", "reasoning", "chat_template_kwargs", "nothink_prefix"):
            if kwargs.get(field):
                raise ValueError(field + " has no native Anthropic mapping")
        self.thinking = copy.deepcopy(thinking)
        self.anthropic_version = anthropic_version
        self.default_max_tokens = default_max_tokens
        endpoint = _messages_url(kwargs.pop("base_url", None) or "https://api.anthropic.com/v1")
        super().__init__(base_url=endpoint, **kwargs)
        # The parent accepts a complete /messages URL without changing it.
        self.config.base_url = endpoint
        self._dump_context.update({
            "api_protocol": self.api_protocol,
            "parameter_compatibility": self.parameter_compatibility,
        })

    @property
    def parameter_compatibility(self) -> Dict[str, object]:
        requested = {
            name: copy.deepcopy(getattr(self.config, name))
            for name in self.omitted_parameters
        }
        return {
            "api_protocol": self.api_protocol,
            "anthropic_version": self.anthropic_version,
            "requires_immutable_history": self.requires_immutable_history,
            "omitted_parameters": requested,
            "effort": self.config.reasoning_effort or "high",
            "effort_source": "explicit" if self.config.reasoning_effort else "provider_default",
            "thinking": copy.deepcopy(self.thinking) if self.thinking is not None else "provider_default",
            "max_tokens": self.config.max_tokens or self.default_max_tokens,
            "provider_cache_isolation": "not_guaranteed",
            "seed_semantics": "omitted; local task/pool seed does not seed provider generation",
        }

    @staticmethod
    def _blocks(content: object) -> list:
        if content is None:
            return []
        if isinstance(content, str):
            return [{"type": "text", "text": content}] if content else []
        if not isinstance(content, list):
            raise ValueError("Native message content must be text, blocks, or null")
        if any(not isinstance(block, dict) or not isinstance(block.get("type"), str)
               or not block["type"] for block in content):
            raise ValueError("Native content blocks require non-empty type strings")
        return copy.deepcopy(content)

    @classmethod
    def _native_messages(cls, messages: list) -> tuple:
        system = []
        native = []
        for message in messages:
            if not isinstance(message, dict):
                raise ValueError("Messages must be objects")
            role = message.get("role")
            if role in ("system", "developer"):
                if native:
                    raise ValueError("Mid-conversation system messages require a separately configured native capability")
                system.extend(cls._blocks(message.get("content")))
                continue
            if role == "tool":
                call_id = message.get("tool_call_id")
                if not isinstance(call_id, str) or not call_id:
                    raise ValueError("Tool result requires tool_call_id")
                content = message.get("content")
                if not isinstance(content, (str, list)):
                    raise ValueError("Tool result content must be text or native blocks")
                blocks = [{"type": "tool_result", "tool_use_id": call_id,
                           "content": copy.deepcopy(content)}]
                role = "user"
            elif role in ("user", "assistant"):
                blocks = cls._blocks(message.get("content"))
                if role == "assistant":
                    if message.get("reasoning_content") or message.get("reasoning"):
                        raise ValueError("Cannot replay unsigned Chat reasoning as native Anthropic thinking")
                    calls = cls._normalize_tool_calls(message.get("tool_calls"))
                    existing = {block.get("id"): block for block in blocks if block["type"] == "tool_use"}
                    for call in calls:
                        function = call["function"]
                        try:
                            arguments = json.loads(function["arguments"])
                        except (TypeError, ValueError) as exc:
                            raise ValueError("Historical native tool arguments must be JSON") from exc
                        if call["id"] in existing:
                            block = existing[call["id"]]
                            if block.get("name") != function["name"] or block.get("input") != arguments:
                                raise ValueError("Native tool block and internal tool-call alias disagree")
                        else:
                            blocks.append({"type": "tool_use", "id": call["id"],
                                           "name": function["name"], "input": arguments})
            else:
                raise ValueError("Unsupported native message role: " + str(role))
            # Tool results and any following runtime context form one user
            # message, preserving block order and the entire assistant block list.
            if native and native[-1]["role"] == role:
                native[-1]["content"].extend(blocks)
            else:
                native.append({"role": role, "content": blocks})
        return system, native

    def _native_payload(self, payload: Dict[str, object]) -> Dict[str, object]:
        system, messages = self._native_messages(payload["messages"])
        native = {
            "model": payload["model"], "messages": messages,
            "max_tokens": payload.get("max_tokens", self.default_max_tokens),
            "stream": False,
        }
        if system:
            native["system"] = system
        for name in ("temperature", "top_p", "top_k"):
            if name in payload and name not in self.omitted_parameters:
                native[name] = payload[name]
        for name in ("seed", "prompt_cache_key"):
            if name in payload and name not in self.omitted_parameters:
                raise ValueError(name + " has no native Anthropic mapping; explicitly omit it")
        if self.config.reasoning_effort is not None:
            native["output_config"] = {"effort": self.config.reasoning_effort}
        if self.thinking is not None:
            native["thinking"] = copy.deepcopy(self.thinking)
        if "tools" in payload:
            tools = []
            for tool in payload["tools"]:
                if not isinstance(tool, dict) or tool.get("type") != "function":
                    raise ValueError("Native adapter requires function tool definitions")
                function = tool.get("function")
                if not isinstance(function, dict) or not isinstance(function.get("name"), str):
                    raise ValueError("Function tool requires a name")
                converted = {"name": function["name"],
                             "input_schema": copy.deepcopy(function.get("parameters", {}))}
                for name in ("description", "strict"):
                    if name in function:
                        converted[name] = copy.deepcopy(function[name])
                tools.append(converted)
            native["tools"] = tools
        if "tool_choice" in payload:
            choice = payload["tool_choice"]
            if isinstance(choice, str) and choice in ("auto", "none", "required"):
                converted_choice = {"type": "any" if choice == "required" else choice}
            elif isinstance(choice, dict) and choice.get("type") == "function":
                function = choice.get("function") or {}
                name = function.get("name") or choice.get("name")
                if not isinstance(name, str) or not name:
                    raise ValueError("Named tool choice requires a name")
                converted_choice = {"type": "tool", "name": name}
            else:
                raise ValueError("Unsupported tool_choice for native Anthropic adapter")
            if converted_choice["type"] != "none":
                converted_choice["disable_parallel_tool_use"] = True
            native["tool_choice"] = converted_choice
        return native

    def _build_request(self, payload: Dict[str, object]) -> urllib.request.Request:
        return urllib.request.Request(
            self.config.base_url,
            data=json.dumps(self._native_payload(payload), ensure_ascii=False, allow_nan=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.config.api_key,
                     "Content-Type": "application/json",
                     "anthropic-version": self.anthropic_version,
                     **self.config.extra_headers},
            method="POST",
        )

    def _dump_attempt(self, metadata, payload, started, **kwargs) -> None:
        # Persist the actual native wire payload and original native response,
        # never the temporary common representation used by the retry engine.
        super()._dump_attempt(metadata, self._native_payload(payload), started, **kwargs)

    def _attempt_usage_record(self, metadata, state, raw=None, http_status=None):
        record = super()._attempt_usage_record(metadata, state, raw, http_status)
        record["api_protocol"] = self.api_protocol
        record["usage_semantics"] = "anthropic_input_excludes_cache_read_and_creation"
        return record

    @staticmethod
    def _validate_usage(usage: object) -> None:
        OpenAICompatibleLLM._validate_usage(usage)
        if usage is None:
            return
        counts = [(name, usage[name]) for name in (
            "cache_creation_input_tokens", "cache_read_input_tokens", "thinking_tokens",
        ) if name in usage]
        for section in ("cache_creation", "output_tokens_details"):
            details = usage.get(section)
            if details is not None:
                if not isinstance(details, dict):
                    raise ValueError("API usage " + section + " must be an object or null")
                counts.extend((section + "." + name, value) for name, value in details.items()
                              if name.endswith("tokens"))
        for name, value in counts:
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError("API usage " + name + " must be a non-negative integer or null")

    @classmethod
    def _decode_response(cls, raw: bytes) -> tuple:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            raise ValueError("API returned invalid JSON") from exc
        if not isinstance(data, dict) or data.get("type", "message") != "message":
            raise ValueError("API response is not a native Anthropic message")
        if data.get("role") != "assistant" or not isinstance(data.get("content"), list):
            raise ValueError("API response requires assistant role and native content blocks")
        content = cls._blocks(data["content"])
        text = []
        calls = []
        for block in content:
            if block["type"] == "text":
                if not isinstance(block.get("text"), str):
                    raise ValueError("API text block requires text")
                text.append(block["text"])
            elif block["type"] == "thinking":
                if not isinstance(block.get("thinking"), str) or not isinstance(block.get("signature"), str):
                    raise ValueError("API thinking block requires thinking text and signature")
            elif block["type"] == "redacted_thinking":
                if not isinstance(block.get("data"), str):
                    raise ValueError("API redacted_thinking block requires opaque data")
            elif block["type"] == "tool_use":
                if not isinstance(block.get("input"), dict):
                    raise ValueError("API tool_use block requires object input")
                calls.append({"id": block.get("id"), "type": "function", "function": {
                    "name": block.get("name"),
                    "arguments": json.dumps(block["input"], ensure_ascii=False, allow_nan=False),
                }})
        calls = cls._normalize_tool_calls(calls)
        stop = data.get("stop_reason")
        if stop is not None and not isinstance(stop, str):
            raise ValueError("API stop_reason must be a string or null")
        if stop == "tool_use" and not calls:
            raise ValueError("API tool_use stop missing tool calls")
        finish = {"tool_use": "tool_calls", "end_turn": "stop", "stop_sequence": "stop",
                  "max_tokens": "length"}.get(stop, stop)
        cls._validate_usage(data.get("usage"))
        assistant = {"role": "assistant", "content": content}
        if calls:
            # Alias is for the runner's pairing checks only. Native wire replay
            # uses the untouched content blocks, with no duplicate tool_use.
            assistant["tool_calls"] = copy.deepcopy(calls)
        normalized = copy.deepcopy(data)
        usage = data.get("usage")
        if isinstance(usage, dict):
            accounting = copy.deepcopy(usage)
            parts = [usage.get(name) for name in (
                "input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
            )]
            # Anthropic input_tokens excludes reads/writes. Missing pieces
            # remain unknown; zero is never invented for incomplete accounting.
            accounting["prompt_tokens"] = sum(parts) if all(isinstance(v, int) for v in parts) else None
            accounting["input_tokens"] = accounting["prompt_tokens"]
            accounting["prompt_tokens_details"] = {
                "cached_tokens": usage.get("cache_read_input_tokens"),
                "cache_write_tokens": usage.get("cache_creation_input_tokens"),
            }
            normalized["usage"] = accounting
        return normalized, "\n".join(text).strip(), calls, assistant, finish
