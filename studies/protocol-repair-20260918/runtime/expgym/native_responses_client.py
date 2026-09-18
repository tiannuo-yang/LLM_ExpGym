"""Explicit Responses transport with lossless native output-item replay.

The common runner sees assistant messages and function-call aliases. The wire
boundary retains every native output item, including opaque encrypted reasoning,
and sends those items back unchanged with their matching function-call results.
Transport retries, all-attempt accounting and credential-safe dumps are inherited
from the common client. Capabilities are configured, never guessed from model IDs.
"""
from __future__ import annotations

import copy
import json
import urllib.parse
import urllib.request
from typing import Dict, Sequence

from expgym.llm_clients import OpenAICompatibleLLM


DEFAULT_OMITTED_PARAMETERS = (
    "temperature", "top_p", "top_k", "seed", "max_tokens", "prompt_cache_key",
)
OUTPUT_ITEMS_FIELD = "_responses_output"


def _responses_url(base_url: str) -> str:
    parsed = urllib.parse.urlsplit(base_url.rstrip("/"))
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        path = path[:-len("/chat/completions")] + "/responses"
    elif not path:
        path = "/v1/responses"
    elif not path.endswith("/responses"):
        path += "/responses"
    return urllib.parse.urlunsplit(parsed._replace(path=path))


class NativeResponsesLLM(OpenAICompatibleLLM):
    """Native Responses adapter with an explicit endpoint capability profile.

    The default omissions describe an endpoint with fixed sampling controls and
    no accepted output-token limit. Requested values stay in config and audit
    metadata; the actual request omits them. An empty omission list permits
    temperature/top_p/max_tokens, but seed and top_k have no Responses mapping.
    ``max_tokens`` maps to ``max_output_tokens`` only when explicitly supported.
    """

    api_protocol = "responses"
    requires_immutable_history = True

    def __init__(
        self, *, api_protocol: str = "responses",
        omitted_parameters: Sequence[str] = DEFAULT_OMITTED_PARAMETERS,
        store: bool = False,
        include: Sequence[str] = ("reasoning.encrypted_content",),
        **kwargs,
    ) -> None:
        if api_protocol != "responses":
            raise ValueError("NativeResponsesLLM requires api_protocol='responses'")
        if isinstance(omitted_parameters, str):
            raise ValueError("omitted_parameters must be a sequence of field names")
        self.omitted_parameters = tuple(omitted_parameters)
        allowed = set(DEFAULT_OMITTED_PARAMETERS)
        if any(name not in allowed for name in self.omitted_parameters):
            raise ValueError("unsupported omitted_parameters entry")
        if not isinstance(store, bool):
            raise ValueError("store must be a boolean")
        if isinstance(include, str) or any(not isinstance(value, str) or not value for value in include):
            raise ValueError("include must be a sequence of non-empty strings")
        self.store = store
        self.include = tuple(include)
        if not store and "reasoning.encrypted_content" not in self.include:
            raise ValueError("Stateless native history requires reasoning.encrypted_content")
        for field in ("provider", "chat_template_kwargs", "nothink_prefix"):
            if kwargs.get(field):
                raise ValueError(field + " has no native Responses mapping")
        reasoning = kwargs.get("reasoning")
        if reasoning is not None:
            if not isinstance(reasoning, dict) or any(name not in ("effort", "summary") for name in reasoning):
                raise ValueError("reasoning must be a native Responses effort/summary object")
            if (kwargs.get("reasoning_effort") is not None and reasoning.get("effort") is not None
                    and kwargs["reasoning_effort"] != reasoning["effort"]):
                raise ValueError("reasoning_effort conflicts with native reasoning.effort")
        endpoint = _responses_url(kwargs.pop("base_url", None) or "https://api.openai.com/v1")
        super().__init__(base_url=endpoint, **kwargs)
        self.config.base_url = endpoint
        self._dump_context.update({
            "api_protocol": self.api_protocol,
            "parameter_compatibility": self.parameter_compatibility,
        })

    @property
    def parameter_compatibility(self) -> Dict[str, object]:
        requested = {name: copy.deepcopy(getattr(self.config, name)) for name in self.omitted_parameters}
        native_reasoning = copy.deepcopy(self.config.reasoning or {})
        if self.config.reasoning_effort is not None:
            native_reasoning["effort"] = self.config.reasoning_effort
        return {
            "api_protocol": self.api_protocol,
            "omitted_parameters": requested,
            "reasoning": native_reasoning or "provider_default",
            "max_output_tokens": None if "max_tokens" in self.omitted_parameters else self.config.max_tokens,
            "output_token_limit_enforced_by_client": False,
            "store": self.store,
            "include": list(self.include),
            "provider_cache_isolation": "not_guaranteed",
            "seed_semantics": "omitted; local task/pool seed does not seed provider generation",
        }

    @staticmethod
    def _items(value: object) -> list:
        if not isinstance(value, list):
            raise ValueError("Native Responses output must be a list")
        if any(not isinstance(item, dict) or not isinstance(item.get("type"), str)
               or not item["type"] for item in value):
            raise ValueError("Native Responses items require non-empty type strings")
        return copy.deepcopy(value)

    @classmethod
    def _calls(cls, items: list) -> list:
        return cls._normalize_tool_calls([
            {"id": item.get("call_id"), "type": "function", "function": {
                "name": item.get("name"), "arguments": item["arguments"],
            }} for item in items if item["type"] == "function_call" and "arguments" in item
        ])

    @classmethod
    def _native_messages(cls, messages: list) -> list:
        native = []
        for message in messages:
            if not isinstance(message, dict):
                raise ValueError("Messages must be objects")
            role = message.get("role")
            if role == "assistant" and OUTPUT_ITEMS_FIELD in message:
                items = cls._items(message[OUTPUT_ITEMS_FIELD])
                native_calls = cls._calls(items)
                aliases = cls._normalize_tool_calls(message.get("tool_calls"))
                if aliases != native_calls:
                    raise ValueError("Native output items and internal tool-call aliases disagree")
                native.extend(items)
                continue
            if role == "tool":
                call_id = message.get("tool_call_id")
                if not isinstance(call_id, str) or not call_id:
                    raise ValueError("Tool result requires tool_call_id")
                content = message.get("content")
                if not isinstance(content, (str, list)):
                    raise ValueError("Tool result content must be text or native blocks")
                native.append({"type": "function_call_output", "call_id": call_id,
                               "output": copy.deepcopy(content)})
                continue
            if role not in ("system", "developer", "user", "assistant"):
                raise ValueError("Unsupported native message role: " + str(role))
            if message.get("reasoning_content") or message.get("reasoning"):
                raise ValueError("Cannot replay Chat reasoning without original native Responses items")
            content = message.get("content")
            if content is not None and not isinstance(content, (str, list)):
                raise ValueError("Message content must be text, blocks, or null")
            if content is not None:
                if isinstance(content, list):
                    content = copy.deepcopy(content)
                    for block in content:
                        if not isinstance(block, dict) or not isinstance(block.get("type"), str):
                            raise ValueError("Message blocks require a type string")
                        if block["type"] == "text":
                            block["type"] = "output_text" if role == "assistant" else "input_text"
                native.append({"role": role, "content": content})
            calls = cls._normalize_tool_calls(message.get("tool_calls"))
            if calls and role != "assistant":
                raise ValueError("Only assistant messages can carry function calls")
            for call in calls:
                native.append({"type": "function_call", "call_id": call["id"],
                               "name": call["function"]["name"],
                               "arguments": call["function"]["arguments"]})
        return native

    def _native_payload(self, payload: Dict[str, object]) -> Dict[str, object]:
        native = {
            "model": payload["model"], "input": self._native_messages(payload["messages"]),
            "stream": False, "store": self.store, "include": list(self.include),
        }
        for name in ("temperature", "top_p", "prompt_cache_key"):
            if name in payload and name not in self.omitted_parameters:
                native[name] = copy.deepcopy(payload[name])
        if "max_tokens" in payload and "max_tokens" not in self.omitted_parameters:
            native["max_output_tokens"] = payload["max_tokens"]
        for name in ("seed", "top_k"):
            if name in payload and name not in self.omitted_parameters:
                raise ValueError(name + " has no native Responses mapping; explicitly omit it")
        reasoning = copy.deepcopy(payload.get("reasoning") or {})
        if self.config.reasoning_effort is not None:
            reasoning["effort"] = self.config.reasoning_effort
        if reasoning:
            native["reasoning"] = reasoning
        if "tools" in payload:
            tools = []
            for tool in payload["tools"]:
                if not isinstance(tool, dict) or tool.get("type") != "function":
                    raise ValueError("Native adapter requires function tool definitions")
                function = tool.get("function")
                if not isinstance(function, dict) or not isinstance(function.get("name"), str) or not function["name"]:
                    raise ValueError("Function tool requires a name")
                # Preserve the complete supplied schema, including strict and
                # optional future function fields, while flattening its wrapper.
                converted = copy.deepcopy(function)
                converted["type"] = "function"
                tools.append(converted)
            native["tools"] = tools
            native["parallel_tool_calls"] = False
        if "tool_choice" in payload:
            choice = payload["tool_choice"]
            if isinstance(choice, str) and choice in ("auto", "none", "required"):
                native["tool_choice"] = choice
            elif isinstance(choice, dict) and choice.get("type") == "function":
                function = choice.get("function") or {}
                name = function.get("name") or choice.get("name")
                if not isinstance(name, str) or not name:
                    raise ValueError("Named tool choice requires a name")
                native["tool_choice"] = {"type": "function", "name": name}
            else:
                raise ValueError("Unsupported tool_choice for native Responses adapter")
        return native

    def _build_request(self, payload: Dict[str, object]) -> urllib.request.Request:
        return urllib.request.Request(
            self.config.base_url,
            data=json.dumps(self._native_payload(payload), ensure_ascii=False, allow_nan=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.config.api_key,
                     "Content-Type": "application/json", **self.config.extra_headers},
            method="POST",
        )

    def _dump_attempt(self, metadata, payload, started, **kwargs) -> None:
        super()._dump_attempt(metadata, self._native_payload(payload), started, **kwargs)

    @classmethod
    def _decode_response(cls, raw: bytes) -> tuple:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            raise ValueError("API returned invalid JSON") from exc
        if not isinstance(data, dict) or data.get("object", "response") != "response":
            raise ValueError("API response is not a native Responses object")
        status = data.get("status")
        if status not in ("completed", "incomplete", "failed", "cancelled"):
            raise ValueError("API response has no terminal Responses status")
        cls._validate_usage(data.get("usage"))
        if status in ("failed", "cancelled") or data.get("error"):
            # No partially emitted tool is a delivered decision on an explicit
            # provider failure, even if the partial output is malformed.
            return data, "", [], {"role": "assistant", "content": None,
                                  OUTPUT_ITEMS_FIELD: copy.deepcopy(data.get("output"))}, "abort"
        items = cls._items(data.get("output"))
        text = []
        for item in items:
            if item["type"] == "function_call" and "arguments" not in item:
                raise ValueError("Native function call missing arguments")
            if item["type"] == "message":
                if item.get("role") != "assistant" or not isinstance(item.get("content"), list):
                    raise ValueError("Native output message requires assistant role and content blocks")
                for block in item["content"]:
                    if not isinstance(block, dict) or not isinstance(block.get("type"), str) or not block["type"]:
                        raise ValueError("Native output blocks require a type string")
                    if block["type"] == "output_text":
                        if not isinstance(block.get("text"), str):
                            raise ValueError("Native output_text block requires text")
                        text.append(block["text"])
        calls = cls._calls(items)
        visible = "\n".join(text).strip()
        assistant = {"role": "assistant", "content": visible or None,
                     OUTPUT_ITEMS_FIELD: items, "_responses_status": status}
        if data.get("incomplete_details") is not None:
            assistant["_responses_incomplete_details"] = copy.deepcopy(data["incomplete_details"])
        if calls:
            assistant["tool_calls"] = copy.deepcopy(calls)
        if status == "incomplete":
            details = data.get("incomplete_details")
            if not isinstance(details, dict) or not isinstance(details.get("reason"), str):
                raise ValueError("Incomplete Responses output requires a reason")
            finish = "length" if details["reason"] == "max_output_tokens" else details["reason"]
        else:
            finish = "tool_calls" if calls else "stop"
        return data, visible, calls, assistant, finish
