"""Explicit Gemini generateContent transport with signed native history replay.

The runner's function-call aliases are an internal interface only. Original
model Parts, including opaque thoughtSignature values, remain authoritative on
the wire. No SDK automatically executes tools or advances the conversation.
"""
from __future__ import annotations

import copy
import hashlib
import http.client
import json
import math
import urllib.parse
import urllib.request
from typing import Dict, Sequence

from expgym.llm_clients import OpenAICompatibleLLM, PartialAPIResponseError


CONTENT_FIELD = "_gemini_content"
DEFAULT_OMITTED_PARAMETERS = ("prompt_cache_key",)
_PARAMETERS = {"temperature", "top_p", "top_k", "seed", "max_tokens", "prompt_cache_key"}


def _gemini_transport(request: urllib.request.Request, timeout: float) -> bytes:
    """Retain received stream bytes even when a subsequent socket read fails."""
    received = []
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            reader = getattr(response, "read1", None) or response.read
            while True:
                try:
                    chunk = reader(65536)
                except http.client.IncompleteRead as exc:
                    # HTTPResponse may deliver its final bytes only through
                    # IncompleteRead.partial rather than a successful read.
                    if exc.partial:
                        received.append(exc.partial)
                    raise
                if not chunk:
                    break
                received.append(chunk)
    except Exception as exc:
        if received:
            raise PartialAPIResponseError(
                "Gemini response interrupted after receiving bytes", b"".join(received),
            ) from exc
        raise
    return b"".join(received)


def _generate_content_url(base_url: str, model: str, stream: bool = True) -> str:
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Gemini requires an explicit model")
    model = model[7:] if model.startswith("models/") else model
    if not model or "/" in model or model != model.strip():
        raise ValueError("Gemini model must be one model identifier")
    parsed = urllib.parse.urlsplit(base_url.rstrip("/"))
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Gemini endpoint must be an HTTP(S) URL")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Gemini endpoint must not contain credentials, query, or fragment")
    action = "streamGenerateContent" if stream else "generateContent"
    suffix = "/models/" + urllib.parse.quote(model, safe="-._~") + ":" + action
    path = parsed.path.rstrip("/")
    if path.endswith((":generateContent", ":streamGenerateContent")):
        if not path.endswith(suffix):
            raise ValueError("Gemini endpoint model disagrees with configured model")
    elif ":" in path or path.endswith("/chat/completions"):
        raise ValueError("Gemini requires a native generateContent base URL")
    else:
        path = (path or "/v1beta") + suffix
    return urllib.parse.urlunsplit(parsed._replace(path=path, query="alt=sse" if stream else ""))


def _sse_events(raw: bytes):
    """Decode complete SSE events; EOF is legal without a [DONE] sentinel."""
    text = raw.decode("utf-8-sig")
    data, event_name = [], "message"
    for line in text.splitlines() + [""]:
        if not line:
            if data:
                body = "\n".join(data)
                yield event_name, body, None if body.strip() == "[DONE]" else json.loads(body)
            data, event_name = [], "message"
        elif not line.startswith(":"):
            name, separator, value = line.partition(":")
            if separator and value.startswith(" "):
                value = value[1:]
            if name == "data":
                data.append(value)
            elif name == "event":
                event_name = value


def _is_sse(raw: bytes) -> bool:
    value = raw.lstrip(b"\xef\xbb\xbf \r\n\t")
    return value.startswith((b"data:", b"event:", b":", b"id:", b"retry:"))


def _wire_data(raw: bytes) -> dict:
    if not _is_sse(raw):
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Gemini API response must be an object")
        return value
    result, parts, candidate_metadata = {}, [], {}
    saw_candidate, saw_finish = False, False
    for event_name, body, event in _sse_events(raw):
        if body.strip() == "[DONE]":
            continue
        if not isinstance(event, dict):
            raise ValueError("Gemini SSE data must be an object")
        if event_name == "error" or event.get("error"):
            result["error"] = copy.deepcopy(event.get("error", event))
        for name, value in event.items():
            if name != "candidates":
                if name in ("modelVersion", "responseId") and name in result and result[name] != value:
                    raise ValueError("Gemini SSE response identity changed within one generation")
                result[name] = copy.deepcopy(value)
        candidates = event.get("candidates", [])
        if not isinstance(candidates, list) or len(candidates) > 1:
            raise ValueError("Gemini SSE requires at most one candidate per event")
        for candidate in candidates:
            if not isinstance(candidate, dict) or candidate.get("index", 0) != 0:
                raise ValueError("Gemini SSE candidate must have index zero")
            saw_candidate = True
            for name, value in candidate.items():
                if name != "content" and (name != "finishReason" or value):
                    candidate_metadata[name] = copy.deepcopy(value)
            if candidate.get("finishReason"):
                saw_finish = True
            if "content" in candidate:
                content = candidate["content"]
                if not isinstance(content, dict) or content.get("role", "model") != "model":
                    raise ValueError("Gemini SSE candidate content must have model role")
                chunk_parts = content.get("parts", [])
                if not isinstance(chunk_parts, list):
                    raise ValueError("Gemini SSE candidate parts must be a list")
                # Parts are append-only in wire order. Never flatten or merge
                # opaque signatures, function calls, or signed text fragments.
                parts.extend(copy.deepcopy(chunk_parts))
    if not result.get("error") and not (isinstance(result.get("promptFeedback"), dict)
                                       and result["promptFeedback"].get("blockReason")):
        if not saw_candidate or not saw_finish:
            raise ValueError("Gemini SSE ended without a terminal candidate")
    result["candidates"] = [{**candidate_metadata, "content": {"role": "model", "parts": parts}}]
    return result


class NativeGeminiLLM(OpenAICompatibleLLM):
    """Gemini transport; omission capabilities are explicit, never model guesses."""

    api_protocol = "gemini"
    requires_immutable_history = True

    def __init__(self, *, api_protocol: str = "gemini", stream: bool = True,
                 omitted_parameters: Sequence[str] = DEFAULT_OMITTED_PARAMETERS,
                 **kwargs) -> None:
        if api_protocol != "gemini":
            raise ValueError("NativeGeminiLLM requires api_protocol='gemini'")
        if not isinstance(stream, bool):
            raise ValueError("Gemini stream must be boolean")
        self.stream = stream
        if isinstance(omitted_parameters, str):
            raise ValueError("omitted_parameters must be a sequence of field names")
        self.omitted_parameters = tuple(omitted_parameters)
        if any(name not in _PARAMETERS for name in self.omitted_parameters):
            raise ValueError("Unsupported Gemini omitted_parameters entry")
        for field in ("provider", "reasoning", "chat_template_kwargs", "nothink_prefix"):
            if kwargs.get(field):
                raise ValueError(field + " has no native Gemini mapping")
        effort = kwargs.get("reasoning_effort")
        if effort is not None and effort not in ("minimal", "low", "medium", "high"):
            raise ValueError("Gemini thinkingLevel must be minimal, low, medium, or high")
        for field in ("temperature", "top_p"):
            value = kwargs.get(field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                      or not math.isfinite(value) or value < 0):
                raise ValueError(field + " must be a finite non-negative number")
        seed = kwargs.get("seed")
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            raise ValueError("Gemini seed must be an integer")
        if kwargs.get("top_k") == -1 and "top_k" not in self.omitted_parameters:
            raise ValueError("Gemini topK=-1 has no native mapping; explicitly omit top_k")
        endpoint = _generate_content_url(
            kwargs.pop("base_url", None) or "https://generativelanguage.googleapis.com/v1beta",
            kwargs.get("model"),
            stream,
        )
        kwargs.setdefault("transport", _gemini_transport)
        super().__init__(base_url=endpoint, **kwargs)
        self.config.base_url = endpoint
        self._dump_context.update({"api_protocol": self.api_protocol,
                                   "parameter_compatibility": self.parameter_compatibility})

    @property
    def parameter_compatibility(self) -> Dict[str, object]:
        return {
            "api_protocol": self.api_protocol,
            "stream": self.stream,
            "response_assembly": "all SSE Parts in wire order; final cumulative usage" if self.stream else "JSON",
            "requires_immutable_history": True,
            "omitted_parameters": {name: copy.deepcopy(getattr(self.config, name))
                                   for name in self.omitted_parameters},
            "thinking_level": self.config.reasoning_effort or "provider_default",
            "effort_source": "explicit" if self.config.reasoning_effort else "provider_default",
            "max_output_tokens": (None if "max_tokens" in self.omitted_parameters
                                  else self.config.max_tokens),
            "seed_semantics": ("omitted; local task/pool seed does not seed provider generation"
                               if "seed" in self.omitted_parameters else
                               "sent as generationConfig.seed; provider determinism unverified"),
            "parallel_tool_calls": "no native switch; one-call rule enforced by runner",
            "tool_schema_format": "parametersJsonSchema",
            "tool_schema_preservation": "deepcopy_unchanged",
            "tool_schema_coercion": False,
            "provider_cache_isolation": "not_guaranteed",
            "empty_model_content_replay": "zero parts or only empty unsigned text omitted; original retained in trace",
            "usage_semantics": "prompt includes cache; completion includes candidates and thoughts",
            "attempt_scope": "client-to-endpoint; intermediary retries are not individually observable",
        }

    @staticmethod
    def _content(value: object) -> dict:
        if not isinstance(value, dict) or value.get("role", "model") != "model":
            raise ValueError("Gemini model content requires model role")
        parts = value.get("parts", [])
        if not isinstance(parts, list) or any(not isinstance(part, dict) for part in parts):
            raise ValueError("Gemini model parts must be a list of objects")
        for part in parts:
            if "text" in part and not isinstance(part["text"], str):
                raise ValueError("Gemini text must be a string")
            if "thought" in part and not isinstance(part["thought"], bool):
                raise ValueError("Gemini thought flag must be boolean")
            if "thoughtSignature" in part and not isinstance(part["thoughtSignature"], str):
                raise ValueError("Gemini thoughtSignature must be an opaque string")
        json.dumps(value, allow_nan=False)
        return copy.deepcopy(value)

    @classmethod
    def _calls(cls, content: dict) -> list:
        calls = []
        digest = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False,
                                           allow_nan=False).encode("utf-8")).hexdigest()[:24]
        for index, part in enumerate(content.get("parts", [])):
            if "functionCall" not in part:
                continue
            call = part["functionCall"]
            if not isinstance(call, dict) or not isinstance(call.get("args", {}), dict):
                raise ValueError("Gemini functionCall requires object args")
            call_id = call.get("id")
            if call_id is None:
                call_id = "gemini_" + digest + "_" + str(index)
            calls.append({"id": call_id, "type": "function", "function": {
                "name": call.get("name"),
                "arguments": json.dumps(call.get("args", {}), ensure_ascii=False, allow_nan=False),
            }})
        return cls._normalize_tool_calls(calls)

    @classmethod
    def _native_messages(cls, messages: list) -> tuple:
        system, native, pending = [], [], {}
        for message in messages:
            if not isinstance(message, dict):
                raise ValueError("Messages must be objects")
            role = message.get("role")
            if role in ("system", "developer"):
                if native:
                    raise ValueError("Mid-conversation system messages have no Gemini mapping")
                if not isinstance(message.get("content"), str):
                    raise ValueError("Gemini system instructions must be text")
                system.append({"text": message["content"]})
                continue
            if role == "assistant" and CONTENT_FIELD in message:
                if pending:
                    raise ValueError("Gemini history is missing function results")
                content = cls._content(message[CONTENT_FIELD])
                calls = cls._calls(content)
                if calls != cls._normalize_tool_calls(message.get("tool_calls")):
                    raise ValueError("Gemini native function calls and internal aliases disagree")
                original_calls = [part["functionCall"] for part in content.get("parts", [])
                                  if "functionCall" in part]
                pending = {alias["id"]: original for alias, original in zip(calls, original_calls)}
                # An empty delivered decision still occupies a runner step and
                # remains in trace. Gemini rejects zero-Part wire messages.
                if any(part != {"text": ""} for part in content.get("parts", [])):
                    native.append(content)
                continue
            if role == "tool":
                call_id = message.get("tool_call_id")
                if not isinstance(call_id, str) or call_id not in pending:
                    raise ValueError("Gemini tool result has no matching pending function call")
                call = pending.pop(call_id)
                if message.get("name", call["name"]) != call["name"]:
                    raise ValueError("Gemini tool result function name disagrees with its call")
                if not isinstance(message.get("content"), str):
                    raise ValueError("Gemini runner tool result must be text")
                result = {"name": call["name"], "response": {"result": message["content"]}}
                if "id" in call:
                    result["id"] = call["id"]
                native.append({"role": "user", "parts": [{"functionResponse": result}]})
                continue
            if role not in ("user", "assistant"):
                raise ValueError("Unsupported Gemini message role: " + str(role))
            if pending:
                raise ValueError("Gemini history is missing function results")
            if message.get("tool_calls") or message.get("reasoning") or message.get("reasoning_content"):
                raise ValueError("Cannot replay signed Gemini history from Chat aliases alone")
            value = message.get("content")
            if not isinstance(value, str):
                raise ValueError("Plain Gemini history requires text")
            if value:
                native.append({"role": "model" if role == "assistant" else "user",
                               "parts": [{"text": value}]})
        if pending:
            raise ValueError("Gemini request is missing pending function results")
        return system, native

    def _native_payload(self, payload: Dict[str, object]) -> Dict[str, object]:
        system, contents = self._native_messages(payload["messages"])
        native = {"contents": contents}
        if system:
            native["systemInstruction"] = {"parts": system}
        generation = {}
        for source, target in (("temperature", "temperature"), ("top_p", "topP"),
                               ("top_k", "topK"), ("seed", "seed"),
                               ("max_tokens", "maxOutputTokens")):
            if source in payload and source not in self.omitted_parameters:
                generation[target] = payload[source]
        if payload.get("prompt_cache_key") is not None and "prompt_cache_key" not in self.omitted_parameters:
            raise ValueError("prompt_cache_key has no native Gemini mapping; explicitly omit it")
        if self.config.reasoning_effort is not None:
            generation["thinkingConfig"] = {"thinkingLevel": self.config.reasoning_effort}
        if generation:
            native["generationConfig"] = generation
        if "tools" in payload:
            declarations = []
            for tool in payload["tools"]:
                if not isinstance(tool, dict) or tool.get("type") != "function":
                    raise ValueError("Gemini adapter requires function tools")
                function = tool.get("function")
                if not isinstance(function, dict) or not isinstance(function.get("name"), str):
                    raise ValueError("Gemini function requires a name")
                if set(function) - {"name", "description", "parameters"}:
                    raise ValueError("Gemini function contains unsupported schema fields")
                declaration = copy.deepcopy(function)
                if "parameters" in declaration:
                    declaration["parametersJsonSchema"] = declaration.pop("parameters")
                declarations.append(declaration)
            native["tools"] = [{"functionDeclarations": declarations}]
        if "tool_choice" in payload:
            choice = payload["tool_choice"]
            if isinstance(choice, str) and choice in ("auto", "none", "required"):
                config = {"mode": {"auto": "AUTO", "none": "NONE", "required": "ANY"}[choice]}
            elif isinstance(choice, dict) and choice.get("type") == "function":
                name = (choice.get("function") or {}).get("name") or choice.get("name")
                if not isinstance(name, str) or not name:
                    raise ValueError("Named Gemini tool choice requires a name")
                config = {"mode": "ANY", "allowedFunctionNames": [name]}
            else:
                raise ValueError("Unsupported Gemini tool_choice")
            native["toolConfig"] = {"functionCallingConfig": config}
        return native

    def _build_request(self, payload: Dict[str, object]) -> urllib.request.Request:
        return urllib.request.Request(
            self.config.base_url,
            data=json.dumps(self._native_payload(payload), ensure_ascii=False, allow_nan=False).encode("utf-8"),
            headers={"x-goog-api-key": self.config.api_key, "Content-Type": "application/json",
                     **self.config.extra_headers}, method="POST",
        )

    def _dump_attempt(self, metadata, payload, started, **kwargs) -> None:
        raw = kwargs.get("raw")
        if raw is not None and _is_sse(raw):
            try:
                events = list(_sse_events(raw))
                if any(self._redact_dump_value(value) != value for _, _, value in events):
                    # Keep original SSE bytes unless a credential field was
                    # echoed. In that case store a redacted SSE equivalent.
                    kwargs["raw"] = "".join(
                        "event: " + name + "\ndata: " + (body if value is None else json.dumps(
                            self._redact_dump_value(value), ensure_ascii=False)) + "\n\n"
                        for name, body, value in events
                    ).encode("utf-8")
            except (UnicodeDecodeError, ValueError, TypeError, RecursionError):
                pass  # Base dump still removes all configured secret strings.
        super()._dump_attempt(metadata, self._native_payload(payload), started, **kwargs)

    def _quota_error_response(self, raw: bytes):
        """Expose an unambiguous, decision-free SSE/JSON error to the gate.

        The gate separately decides whether the error is actually quota related.
        Once any candidate or generated-token usage has arrived, it is never a
        quota retry opportunity: the original abort/partial-response path wins.
        """
        errors = []
        try:
            events = _sse_events(raw) if _is_sse(raw) else [
                ("message", "", json.loads(raw.decode("utf-8")))]
            for name, body, value in events:
                if body.strip() == "[DONE]":
                    continue
                if not isinstance(value, dict):
                    return None
                if value.get("candidates") or value.get("promptFeedback"):
                    return None
                usage = value.get("usageMetadata")
                if isinstance(usage, dict) and any(usage.get(field) not in (None, 0)
                                                  for field in ("candidatesTokenCount", "thoughtsTokenCount")):
                    return None
                if name == "error" or value.get("error"):
                    error = value.get("error", value)
                    if not isinstance(error, dict):
                        return None
                    code = error.get("code")
                    if not isinstance(code, int) or isinstance(code, bool):
                        code = {"RESOURCE_EXHAUSTED": 429, "UNAVAILABLE": 503}.get(error.get("status"))
                    if code not in (429, 503):
                        return None
                    envelope = value if "error" in value else {"error": error}
                    errors.append((code, json.dumps(envelope, ensure_ascii=False, allow_nan=False).encode("utf-8")))
        except (UnicodeDecodeError, ValueError, TypeError, RecursionError):
            return None
        return errors[0] if len(errors) == 1 else None

    @staticmethod
    def _usage(usage: object) -> object:
        if usage is None:
            return None
        if not isinstance(usage, dict):
            raise ValueError("Gemini usageMetadata must be an object or null")
        for name in ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount",
                     "totalTokenCount", "cachedContentTokenCount", "toolUsePromptTokenCount"):
            value = usage.get(name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError("Gemini usage " + name + " must be a non-negative integer or null")
        json.dumps(usage, allow_nan=False)
        prompt, candidates, thoughts, total = (usage.get(name) for name in (
            "promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount", "totalTokenCount"))
        completion = candidates + thoughts if candidates is not None and thoughts is not None else None
        if completion is None and total is not None and prompt is not None:
            if total < prompt:
                raise ValueError("Gemini totalTokenCount is smaller than promptTokenCount")
            completion = total - prompt
        return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": total,
                "prompt_tokens_details": {"cached_tokens": usage.get("cachedContentTokenCount")},
                "completion_tokens_details": {"reasoning_tokens": thoughts},
                "candidate_tokens": candidates}

    def _attempt_usage_record(self, metadata, state, raw=None, http_status=None):
        record = super()._attempt_usage_record(metadata, state, None, http_status)
        record.update(api_protocol=self.api_protocol,
                      usage_semantics="prompt includes cache; completion includes candidates and thoughts")
        if raw is not None:
            try:
                values = (event for _, _, event in _sse_events(raw)) if _is_sse(raw) else [
                    json.loads(raw.decode("utf-8"))]
                for data in values:
                    if isinstance(data, dict) and data.get("usageMetadata") is not None:
                        record["usage"] = self._redact_dump_value(self._usage(data["usageMetadata"]))
                        record["provider_usage"] = self._redact_dump_value(copy.deepcopy(data["usageMetadata"]))
            except (UnicodeDecodeError, ValueError, TypeError, RecursionError) as exc:
                record["usage_error"] = str(self._redact_dump_value(str(exc)))
                if record["usage"] is not None:
                    record["usage_partial"] = True
        return record

    @classmethod
    def _decode_response(cls, raw: bytes) -> tuple:
        try:
            data = _wire_data(raw)
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            raise ValueError("Gemini API returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Gemini API response must be an object")
        normalized = copy.deepcopy(data)
        normalized["usage"] = cls._usage(data.get("usageMetadata"))
        candidates = data.get("candidates")
        if data.get("error") or (isinstance(data.get("promptFeedback"), dict)
                                 and data["promptFeedback"].get("blockReason")):
            return normalized, "", [], {"role": "assistant", "content": None}, "abort"
        if not isinstance(candidates, list) or len(candidates) != 1 or not isinstance(candidates[0], dict):
            raise ValueError("Gemini API requires exactly one response candidate")
        candidate = candidates[0]
        stop = candidate.get("finishReason")
        if stop is not None and not isinstance(stop, str):
            raise ValueError("Gemini finishReason must be a string or null")
        content = cls._content(candidate.get("content", {"role": "model", "parts": []}))
        visible = "".join(part["text"] for part in content.get("parts", [])
                            if "text" in part and not part.get("thought", False)).strip()
        calls = cls._calls(content)
        assistant = {"role": "assistant", "content": visible or None,
                     CONTENT_FIELD: content, "_gemini_finish_reason": stop,
                     "_gemini_model_version": data.get("modelVersion"),
                     "_gemini_response_id": data.get("responseId")}
        if calls:
            assistant["tool_calls"] = copy.deepcopy(calls)
        if stop in (None, "STOP"):
            finish = "tool_calls" if calls else "stop"
        elif stop == "MAX_TOKENS":
            finish = "length"
        else:
            # Explicit blocked/invalid/tool/other provider stops are preserved
            # as failures. Partial text and calls are never executed or scored.
            finish = "abort"
        return normalized, visible, calls, assistant, finish
