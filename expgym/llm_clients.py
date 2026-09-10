"""LLM backend implementations that assume OpenAI-compatible APIs.

All real backends share the same message schema. Use ``base_url`` to target vendors
such as Gemini that offer OpenAI-compatible endpoints.
"""
from __future__ import annotations

import copy
import http.client
import json
import logging
import math
import os
import socket
import ssl
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

from expgym.react_loop import LLMBackend, LLMOutput

logger = logging.getLogger("expgym")

Transport = Callable[[urllib.request.Request, float], bytes]
DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEFAULT_VLLM_URL = "http://localhost:8000/v1/chat/completions"
DEFAULT_SUB2API_URL = "http://127.0.0.1:8080/v1/chat/completions"
DEFAULT_RETRY_HTTP_STATUSES = (429, 500, 502, 503, 504)


class APIClientError(RuntimeError):
    """Terminal transport/protocol failure with all known attempt usage.

    Missing usage is unknown, not zero. Raw response evidence remains in the
    optional attempt dump; this metadata also survives when generation fails.
    """

    def __init__(self, message: str, attempt_usage: List[Dict[str, object]]) -> None:
        super().__init__(message)
        self.attempt_usage = copy.deepcopy(attempt_usage)


class APICompletionAbortedError(APIClientError):
    """Provider explicitly aborted a completion; terminal, never resampled.

    Partial text/tool calls are evidence, not a delivered agent decision. The
    original response stays in the attempt dump and usage stays on the error.
    """

    finish_reason = "abort"


def _normalize_chat_completions_url(base_url: str) -> str:
    """Accept either an OpenAI-compatible base URL or the full chat endpoint."""
    parsed = urllib.parse.urlparse(base_url.rstrip("/"))
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        return urllib.parse.urlunparse(parsed)
    if path in ("", "/"):
        path = "/v1/chat/completions"
    elif path.endswith("/v1") or path.endswith("/api/v1") or path.endswith("/openai"):
        path = f"{path}/chat/completions"
    else:
        return base_url
    return urllib.parse.urlunparse(parsed._replace(path=path))


def _default_transport(request: urllib.request.Request, timeout: float) -> bytes:
    """Direct HTTPS transport (no tunnel)."""
    with urllib.request.urlopen(request, timeout=timeout) as response:  # type: ignore[no-untyped-call]
        return response.read()


def build_tunnel_transport(
    tunnel_port: int = 8443,
    remote_host: str = "openrouter.ai",
) -> Transport:
    """Build a transport that routes HTTPS through a local SSH tunnel.

    Expects ``scripts/tunnel_keepalive.sh`` to be running, forwarding
    ``localhost:<tunnel_port>`` to ``<remote_host>:443`` via a login node.

    The transport creates a raw TCP socket to localhost, wraps it with TLS
    using the correct SNI hostname, and sends the HTTP request manually.
    This avoids the SNI mismatch that urllib would cause.
    """
    try:
        import certifi
        _ca_file = certifi.where()
    except ImportError:
        _ca_file = None

    def _tunnel_transport(request: urllib.request.Request, timeout: float) -> bytes:
        ctx = ssl.create_default_context(cafile=_ca_file)
        sock = socket.create_connection(("localhost", tunnel_port), timeout=timeout)
        try:
            ssock = ctx.wrap_socket(sock, server_hostname=remote_host)
        except Exception:
            sock.close()
            raise

        parsed = urllib.parse.urlparse(request.full_url)
        path = parsed.path
        if parsed.query:
            path += "?" + parsed.query

        conn = http.client.HTTPSConnection("localhost", tunnel_port)
        conn.sock = ssock

        headers = dict(request.headers)
        headers["Host"] = remote_host

        try:
            conn.request(request.get_method(), path, body=request.data, headers=headers)
            resp = conn.getresponse()
            body = resp.read()
            if resp.status >= 400:
                import io
                raise urllib.error.HTTPError(
                    request.full_url, resp.status, resp.reason,
                    resp.msg, io.BytesIO(body),
                )
            return body
        finally:
            conn.close()

    return _tunnel_transport


@dataclass
class OpenAIConfig:
    api_key: str
    model: str
    system_prompt: Optional[str]
    temperature: float
    top_p: float
    seed: Optional[int]
    chat_template_kwargs: Dict[str, object]
    timeout: float
    base_url: str
    extra_headers: Dict[str, str]
    top_k: Optional[int] = None
    provider: Optional[Dict[str, object]] = None
    reasoning: Optional[Dict[str, object]] = None
    max_tokens: Optional[int] = None
    nothink_prefix: bool = False
    prompt_cache_key: Optional[str] = None
    max_retries: int = 10
    retry_base_seconds: float = 3.0
    retry_max_seconds: float = 120.0
    retry_http_statuses: Tuple[int, ...] = DEFAULT_RETRY_HTTP_STATUSES
    reasoning_effort: Optional[str] = None
    prompt_cache_key_field: str = "prompt_cache_key"


class OpenAICompatibleLLM(LLMBackend):
    """LLMBackend that speaks the OpenAI Chat Completions protocol.

    Accepts either a messages list (multi-turn) or a plain string (legacy).
    """

    supports_native_tools = True

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        top_p: float = 1.0,
        seed: Optional[int] = None,
        chat_template_kwargs: Optional[Dict[str, object]] = None,
        system_prompt: Optional[str] = None,
        timeout: float = 600.0,
        base_url: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        transport: Transport = _default_transport,
        top_k: Optional[int] = None,
        provider: Optional[Dict[str, object]] = None,
        reasoning: Optional[Dict[str, object]] = None,
        max_tokens: Optional[int] = None,
        nothink_prefix: bool = False,
        prompt_cache_key: Optional[str] = None,
        max_retries: int = 10,
        retry_base_seconds: float = 3.0,
        retry_max_seconds: float = 120.0,
        retry_http_statuses: Tuple[int, ...] = DEFAULT_RETRY_HTTP_STATUSES,
        dump_context: Optional[Dict[str, object]] = None,
        reasoning_effort: Optional[str] = None,
        prompt_cache_key_field: str = "prompt_cache_key",
    ) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("An API key is required for OpenAICompatibleLLM")
        if prompt_cache_key_field not in ("prompt_cache_key", "cache_salt"):
            raise ValueError("prompt_cache_key_field must be prompt_cache_key or cache_salt")
        if (isinstance(top_p, bool) or not isinstance(top_p, (int, float))
                or not 0.0 < top_p <= 1.0 or not math.isfinite(top_p)):
            raise ValueError("top_p must be a finite number in (0, 1]")
        if top_k is not None and (
            isinstance(top_k, bool) or not isinstance(top_k, int)
            or (top_k != -1 and top_k < 1)
        ):
            raise ValueError("top_k must be None, -1 (disable), or a positive integer")
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if retry_base_seconds < 0 or retry_max_seconds < 0:
            raise ValueError("retry delays must be non-negative")
        if max_tokens is not None and (
            isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1
        ):
            raise ValueError("max_tokens must be a positive integer")
        if chat_template_kwargs is not None and not isinstance(chat_template_kwargs, dict):
            raise ValueError("chat_template_kwargs must be a JSON object")
        if reasoning_effort is not None and (
            not isinstance(reasoning_effort, str) or not reasoning_effort.strip()
        ):
            raise ValueError("reasoning_effort must be a non-empty string")
        if reasoning_effort is not None and isinstance(reasoning, dict):
            enabled = reasoning.get("enabled")
            if ((enabled is False and reasoning_effort != "none")
                    or (enabled is True and reasoning_effort == "none")):
                raise ValueError("reasoning_effort conflicts with explicit reasoning.enabled")
        self.config = OpenAIConfig(
            api_key=key,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=float(top_p),
            seed=seed,
            chat_template_kwargs=chat_template_kwargs or {},
            timeout=timeout,
            base_url=_normalize_chat_completions_url(base_url or DEFAULT_OPENAI_URL),
            extra_headers=extra_headers or {},
            top_k=top_k,
            provider=provider,
            reasoning=reasoning,
            max_tokens=max_tokens,
            nothink_prefix=nothink_prefix,
            prompt_cache_key=(
                prompt_cache_key.strip() if prompt_cache_key and prompt_cache_key.strip() else None
            ),
            max_retries=max_retries,
            retry_base_seconds=retry_base_seconds,
            retry_max_seconds=retry_max_seconds,
            retry_http_statuses=tuple(retry_http_statuses),
            reasoning_effort=reasoning_effort,
            prompt_cache_key_field=prompt_cache_key_field,
        )
        self._transport = transport
        dump_directory = os.getenv("EXPGYM_API_DUMP_DIR")
        self._dump_directory = Path(dump_directory) if dump_directory else None
        self._dump_run_id = os.getenv("EXPGYM_RUN_ID")
        self._dump_context = dict(dump_context or {})
        self._dump_client_id = uuid.uuid4().hex

    @property
    def dump_metadata(self) -> Optional[Dict[str, object]]:
        """Public audit identity, independent of generation and resume settings."""
        if self._dump_directory is None:
            return None
        return {
            "schema_version": "expgym.api_attempt.v1",
            "client_id": self._dump_client_id,
            "run_id": self._dump_run_id,
        }

    @staticmethod
    def _is_secret_field(name: str) -> bool:
        normalized = name.lower().replace("-", "_")
        return normalized in {
            "authorization", "proxy_authorization", "api_key", "apikey", "x_api_key",
            "access_token", "refresh_token", "password", "secret", "client_secret",
        } or normalized.endswith(("_api_key", "_access_token", "_secret"))

    def _redact_dump_value(self, value: object) -> object:
        """Exclude credential fields and any echoed configured credentials."""
        if isinstance(value, dict):
            return {
                key: "[REDACTED]" if self._is_secret_field(str(key)) else self._redact_dump_value(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self._redact_dump_value(item) for item in value]
        if isinstance(value, str):
            secrets = [self.config.api_key]
            secrets.extend(
                header_value for name, header_value in self.config.extra_headers.items()
                if self._is_secret_field(name)
            )
            for secret in sorted(set(secrets), key=len, reverse=True):
                if secret:
                    value = value.replace(secret, "[REDACTED]")
            return value
        return value

    def _dump_attempt(
        self,
        metadata: Dict[str, object],
        payload: Dict[str, object],
        started: float,
        *,
        state: str,
        raw: Optional[bytes] = None,
        error: Optional[Exception] = None,
        http_status: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ) -> None:
        """Atomically record each HTTP attempt, including failed and pending ones.

        Dump failures propagate so an explicitly audited run cannot silently lose
        requests. Transport headers are never serialized. Non-JSON response bytes
        are decoded with backslash escapes so malformed responses remain inspectable.
        """
        if self._dump_directory is None:
            return
        parsed_url = urllib.parse.urlsplit(self.config.base_url)
        endpoint = urllib.parse.urlunsplit((
            parsed_url.scheme, parsed_url.netloc.rsplit("@", 1)[-1], parsed_url.path, "", "",
        ))
        response_text = raw.decode("utf-8", "backslashreplace") if raw is not None else None
        response_json = None
        if raw is not None:
            try:
                response_json = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError, RecursionError):
                pass
        safe_response = self._redact_dump_value(response_json)
        if safe_response != response_json:
            # A provider may echo a credential in its error body. Keep a redacted
            # equivalent instead of persisting that credential in the raw string.
            response_text = json.dumps(safe_response, ensure_ascii=False)
        record = {
            "schema_version": "expgym.api_attempt.v1",
            **metadata,
            "run_id": self._dump_run_id,
            "client_id": self._dump_client_id,
            "context": self._dump_context,
            "pid": os.getpid(),
            "thread_id": threading.get_ident(),
            "thread_name": threading.current_thread().name,
            "state": state,
            "finished_at_utc": None if state == "in_progress" else datetime.now(timezone.utc).isoformat(),
            "wall_time_seconds": time.monotonic() - started,
            "endpoint": endpoint,
            "request_payload": payload,
            "response_raw": response_text,
            "response_json": safe_response,
            "http_status": http_status,
            "error": {"type": type(error).__name__, "message": str(error)} if error else None,
            "will_retry": retry_delay is not None,
            "retry_delay_seconds": retry_delay,
        }
        self._dump_directory.mkdir(parents=True, exist_ok=True)
        destination = self._dump_directory / (str(metadata["request_id"]) + ".json")
        handle = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(self._dump_directory),
            prefix=".api-attempt-", suffix=".tmp", delete=False,
        )
        temporary = Path(handle.name)
        try:
            with handle:
                json.dump(self._redact_dump_value(record), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(temporary), str(destination))
        except BaseException:
            if temporary.exists():
                temporary.unlink()
            raise

    def _build_request(self, payload: Dict[str, object]) -> urllib.request.Request:
        return urllib.request.Request(
            self.config.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                **self.config.extra_headers,
            },
            method="POST",
        )

    def _retry_delay(self, attempt: int, headers: Optional[Message] = None) -> float:
        """Return a bounded exponential delay, honoring numeric Retry-After."""
        if headers is not None:
            retry_after = headers.get("Retry-After")
            if retry_after:
                try:
                    return max(
                        0.0,
                        min(float(retry_after), self.config.retry_max_seconds),
                    )
                except ValueError:
                    pass
        exponential = self.config.retry_base_seconds * (2 ** attempt)
        return min(exponential, self.config.retry_max_seconds)

    @staticmethod
    def _normalize_tool_calls(value: object) -> List[Dict[str, object]]:
        """Validate transport shape, not the model's argument content.

        Argument strings are preserved verbatim, even when they are invalid
        JSON or violate the tool schema. Such a delivered action must consume
        an agent step in the loop, never trigger hidden HTTP resampling here.
        Structured provider arguments are serialized without changing values;
        the original assistant message is separately retained for history.
        """
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("API message tool_calls must be a list")
        normalized = []
        seen_ids = set()
        for call in value:
            if not isinstance(call, dict) or call.get("type") != "function":
                raise ValueError("API tool call must have type function")
            call_id = call.get("id")
            if not isinstance(call_id, str) or not call_id.strip() or call_id in seen_ids:
                raise ValueError("API tool calls require non-empty unique ids")
            seen_ids.add(call_id)
            function = call.get("function")
            if not isinstance(function, dict):
                raise ValueError("API tool call missing function")
            name = function.get("name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("API tool call missing function name")
            if "arguments" not in function:
                raise ValueError("API tool call missing function arguments")
            arguments = function["arguments"]
            if isinstance(arguments, str):
                encoded = arguments
            else:
                try:
                    encoded = json.dumps(arguments, ensure_ascii=False, allow_nan=False)
                except (ValueError, TypeError, OverflowError) as exc:
                    raise ValueError("API tool call arguments have a non-JSON representation") from exc
            item = copy.deepcopy(call)
            item["function"]["arguments"] = encoded
            normalized.append(item)
        return normalized

    @staticmethod
    def _validate_usage(usage: object) -> None:
        """Fail explicitly on unusable accounting, never resample a completion."""
        if usage is None:
            return
        if not isinstance(usage, dict):
            raise ValueError("API usage must be an object or null")
        numeric_keys = (
            "prompt_tokens", "input_tokens", "completion_tokens", "output_tokens",
            "total_tokens", "reasoning_tokens",
        )
        counts = [(key, usage[key]) for key in numeric_keys if key in usage]
        for details_key in ("prompt_tokens_details", "input_tokens_details",
                            "completion_tokens_details", "output_tokens_details"):
            details = usage.get(details_key)
            if details is None:
                continue
            if not isinstance(details, dict):
                raise ValueError("API usage token details must be an object or null")
            counts.extend(
                (details_key + "." + key, details[key])
                for key in ("cached_tokens", "cache_write_tokens", "reasoning_tokens")
                if key in details
            )
        for key, value in counts:
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError("API usage " + key + " must be a non-negative integer or null")

    def _attempt_usage_record(
        self, metadata: Dict[str, object], state: str,
        raw: Optional[bytes] = None, http_status: Optional[int] = None,
    ) -> Dict[str, object]:
        usage = None
        usage_error = None
        if raw is not None:
            try:
                data = json.loads(raw.decode("utf-8"))
                if isinstance(data, dict) and data.get("usage") is not None:
                    try:
                        self._validate_usage(data["usage"])
                        json.dumps(data["usage"], allow_nan=False)
                    except (ValueError, TypeError, RecursionError) as exc:
                        usage_error = str(exc)
                    else:
                        usage = self._redact_dump_value(copy.deepcopy(data["usage"]))
            except (UnicodeDecodeError, ValueError, RecursionError):
                pass
        record = {
            "attempt": metadata["attempt"],
            "request_id": metadata["request_id"],
            "generation_id": metadata["generation_id"],
            "state": state,
            "http_status": http_status,
            "usage": usage,
        }
        if usage_error is not None:
            # Invalid provider accounting is not usable as a token total. The
            # original bytes remain in the attempt dump, without invented zeros.
            record["usage_error"] = usage_error
        return record

    @classmethod
    def _decode_response(
        cls, raw: bytes,
    ) -> Tuple[Dict[str, object], str, List[Dict[str, object]], Dict[str, object], Optional[str]]:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise ValueError("API returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("API response is not an object")
        choices = data.get("choices") or []
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ValueError("API returned no choices")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise ValueError("API choice missing message content")
        if not any(key in message for key in (
            "content", "tool_calls", "reasoning_content", "reasoning", "refusal",
        )):
            raise ValueError("API choice missing assistant response fields")
        if message.get("role", "assistant") != "assistant":
            raise ValueError("API choice message role must be assistant")
        tool_calls = cls._normalize_tool_calls(message.get("tool_calls"))
        content = message.get("content")
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            text_parts = []
            for part in content:
                if (not isinstance(part, dict) or not isinstance(part.get("type"), str)
                        or not part["type"].strip()):
                    raise ValueError("API content parts must be objects with non-empty type strings")
                if part["type"] == "text":
                    part_text = part.get("text")
                    if not isinstance(part_text, str):
                        raise ValueError("API text content parts must contain strings")
                    text_parts.append(part_text)
            text = "\n".join(text_parts).strip()
        elif content is None:
            text = ""
        else:
            raise ValueError("API message content must be text, a content list, or null")
        # An empty visible completion, reasoning-only output, or length stop
        # is still a delivered model decision. The loop handles its protocol
        # outcome after charging this step; it is not an HTTP retry condition.
        finish_reason = choices[0].get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            raise ValueError("API choice finish_reason must be a string or null")
        if finish_reason == "tool_calls" and not tool_calls:
            raise ValueError("API tool_calls finish_reason missing tool calls")
        cls._validate_usage(data.get("usage"))
        # Keep the complete provider message for the next conversation turn,
        # including reasoning fields and the original (unnormalized) tool calls.
        assistant_message = copy.deepcopy(message)
        assistant_message.setdefault("role", "assistant")
        return data, text, tool_calls, assistant_message, finish_reason

    def generate(
        self,
        messages: Union[str, List[Dict[str, object]]],
        *,
        tools: Optional[List[Dict[str, object]]] = None,
        tool_choice: Optional[Union[str, Dict[str, object]]] = None,
    ) -> LLMOutput:
        """Return one delivered decision, retrying only transport failures.

        Every terminal exception retains known attempt usage, including a dump
        failure after a completion arrived. Original exception types are kept
        for callers that distinguish filesystem failures from API failures.
        """
        attempt_usage: List[Dict[str, object]] = []
        try:
            return self._generate(
                messages, tools=tools, tool_choice=tool_choice, attempt_usage=attempt_usage,
            )
        except Exception as exc:
            exc.attempt_usage = copy.deepcopy(attempt_usage)
            raise

    def _generate(
        self,
        messages: Union[str, List[Dict[str, object]]],
        *,
        tools: Optional[List[Dict[str, object]]],
        tool_choice: Optional[Union[str, Dict[str, object]]],
        attempt_usage: List[Dict[str, object]],
    ) -> LLMOutput:
        """Generate text and/or native calls without flattening chat history.

        Supplying tool definitions enables native auto selection; a final-answer
        request passes the same definitions with ``tool_choice="none"``. Omitting
        both arguments retains the legacy text-only request shape.
        """
        if tools is not None and not isinstance(tools, list):
            raise ValueError("tools must be a list of OpenAI tool definitions")
        if tool_choice is not None and not isinstance(tool_choice, (str, dict)):
            raise ValueError("tool_choice must be a string or an OpenAI choice object")
        if isinstance(messages, str):
            # Legacy: wrap plain string into messages list
            msgs: List[Dict[str, object]] = []
            if self.config.system_prompt:
                msgs.append({"role": "system", "content": self.config.system_prompt})
            msgs.append({"role": "user", "content": messages})
        else:
            # Assistant reasoning/tool calls and tool-role/tool_call_id entries
            # must survive intact. A private copy also protects callers from
            # provider-specific prompt adjustments and subsequent mutation.
            msgs = copy.deepcopy(messages)

        # Prepend /nothink to system message for Qwen3 thinking suppression
        if (self.config.nothink_prefix
                and "qwen" in self.config.model.lower()
                and msgs and msgs[0]["role"] == "system"):
            content = msgs[0]["content"]
            if not content.startswith("/nothink"):
                msgs[0] = {**msgs[0], "content": "/nothink\n" + content}

        payload: Dict[str, object] = {
            "model": self.config.model,
            "messages": msgs,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        if self.config.seed is not None:
            payload["seed"] = self.config.seed
        if self.config.max_tokens is not None:
            payload["max_tokens"] = self.config.max_tokens
        if self.config.top_k is not None:
            payload["top_k"] = self.config.top_k
        if self.config.provider is not None:
            payload["provider"] = self.config.provider
        if self.config.reasoning is not None:
            payload["reasoning"] = self.config.reasoning
        if self.config.reasoning_effort is not None:
            payload["reasoning_effort"] = self.config.reasoning_effort
        if self.config.chat_template_kwargs:
            payload["chat_template_kwargs"] = self.config.chat_template_kwargs
        if self.config.prompt_cache_key is not None:
            payload[self.config.prompt_cache_key_field] = self.config.prompt_cache_key
        if tools is not None:
            payload["tools"] = copy.deepcopy(tools)
            payload["tool_choice"] = copy.deepcopy(tool_choice) if tool_choice is not None else "auto"
            payload["parallel_tool_calls"] = False
        elif tool_choice is not None:
            payload["tool_choice"] = copy.deepcopy(tool_choice)
        generation_id = uuid.uuid4().hex
        for attempt in range(self.config.max_retries + 1):
            request = self._build_request(payload)
            started = time.monotonic()
            metadata = {
                "generation_id": generation_id,
                "request_id": uuid.uuid4().hex,
                "attempt": attempt + 1,
                "max_attempts": self.config.max_retries + 1,
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            self._dump_attempt(metadata, payload, started, state="in_progress")
            try:
                raw = self._transport(request, self.config.timeout)
            except urllib.error.HTTPError as exc:
                code = exc.code
                try:
                    raw_error = exc.read()
                except Exception as read_error:
                    attempt_usage.append(self._attempt_usage_record(metadata, "error", http_status=code))
                    self._dump_attempt(metadata, payload, started, state="error", error=read_error, http_status=code)
                    raise
                body = raw_error.decode("utf-8", "ignore")
                attempt_usage.append(self._attempt_usage_record(metadata, "error", raw_error, code))
                will_retry = code in self.config.retry_http_statuses and attempt < self.config.max_retries
                wait = self._retry_delay(attempt, exc.headers) if will_retry else None
                self._dump_attempt(
                    metadata, payload, started, state="error", raw=raw_error,
                    error=exc, http_status=code, retry_delay=wait,
                )
                if (
                    code in self.config.retry_http_statuses
                    and attempt < self.config.max_retries
                ):
                    wait = self._retry_delay(attempt, exc.headers)
                    logger.warning(
                        "HTTP %d, retry %d/%d in %.1fs",
                        code,
                        attempt + 1,
                        self.config.max_retries,
                        wait,
                    )
                    import time as _time
                    _time.sleep(wait)
                    continue
                raise APIClientError(
                    "API error: " + str(self._redact_dump_value(body)), attempt_usage,
                ) from exc
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                attempt_usage.append(self._attempt_usage_record(metadata, "error"))
                wait = self._retry_delay(attempt) if attempt < self.config.max_retries else None
                self._dump_attempt(
                    metadata, payload, started, state="error", error=exc, retry_delay=wait,
                )
                if attempt < self.config.max_retries:
                    wait = self._retry_delay(attempt)
                    logger.warning(
                        "URLError, retry %d/%d in %.1fs: %s",
                        attempt + 1,
                        self.config.max_retries,
                        wait,
                        self._redact_dump_value(str(exc)),
                    )
                    import time as _time
                    _time.sleep(wait)
                    continue
                raise APIClientError(
                    "API connection failed: " + str(self._redact_dump_value(str(exc))), attempt_usage,
                ) from exc
            except Exception as exc:
                attempt_usage.append(self._attempt_usage_record(metadata, "error"))
                self._dump_attempt(metadata, payload, started, state="error", error=exc)
                raise
            try:
                data, text, tool_calls, assistant_message, finish_reason = self._decode_response(raw)
            except Exception as exc:
                attempt_usage.append(self._attempt_usage_record(metadata, "malformed_response", raw))
                self._dump_attempt(
                    metadata, payload, started, state="malformed_response", raw=raw,
                    error=exc,
                )
                # A decoded HTTP success with an uncertain structure is an
                # explicit invalid run, not a chance to sample another answer.
                raise APIClientError(str(exc), attempt_usage) from exc
            if finish_reason == "abort":
                # An explicit provider abort is not a completed model decision,
                # even when partial content or tool calls look valid. Preserve
                # this physical attempt, but do not retry, score, or execute it.
                attempt_usage.append(self._attempt_usage_record(metadata, "error", raw))
                error = APICompletionAbortedError(
                    "API generation aborted (finish_reason=abort)", attempt_usage,
                )
                self._dump_attempt(metadata, payload, started, state="error", raw=raw, error=error)
                raise error
            # Transport returns bytes only: an exact success status is not
            # available through this interface, so do not fabricate HTTP 200.
            attempt_usage.append(self._attempt_usage_record(metadata, "success", raw))
            self._dump_attempt(metadata, payload, started, state="success", raw=raw)
            break

        usage = data.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens")
        if prompt_tokens is None:
            prompt_tokens = usage.get("input_tokens")
        completion_tokens = usage.get("completion_tokens")
        if completion_tokens is None:
            completion_tokens = usage.get("output_tokens")
        prompt_token_details = (
            usage.get("prompt_tokens_details")
            or usage.get("input_tokens_details")
            or {}
        )
        cached_prompt_tokens = (
            prompt_token_details.get("cached_tokens")
            if isinstance(prompt_token_details, dict)
            else None
        )
        cache_write_prompt_tokens = (
            prompt_token_details.get("cache_write_tokens")
            if isinstance(prompt_token_details, dict)
            else None
        )
        return LLMOutput(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_prompt_tokens=cached_prompt_tokens,
            cache_write_prompt_tokens=cache_write_prompt_tokens,
            request_attempts=attempt + 1,
            tool_calls=tool_calls,
            assistant_message=assistant_message,
            finish_reason=finish_reason,
            # Scalar counters above describe the delivered response only.
            # Account for all attempts separately; usage=None is unknown cost.
            attempt_usage=attempt_usage,
        )


def build_gemini_client(**kwargs) -> OpenAICompatibleLLM:
    """Helper that instantiates the OpenAI client for Gemini endpoints."""
    api_key = kwargs.pop("api_key", None) or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for the Gemini backend")
    base_url = kwargs.pop("base_url", None) or DEFAULT_GEMINI_URL
    return OpenAICompatibleLLM(
        api_key=api_key,
        base_url=base_url,
        **kwargs,
    )


DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_openrouter_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    referer: Optional[str] = None,
    title: Optional[str] = None,
    require_parameters: bool = False,
    disable_thinking: bool = True,
    **kwargs,
) -> OpenAICompatibleLLM:
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY is required for the OpenRouter backend")
    headers: Dict[str, str] = {}
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title
    # Build provider preferences for deterministic routing
    provider = kwargs.pop("provider", None)
    if provider is None and require_parameters:
        provider = {"require_parameters": True}
    # Retain the legacy default only when no explicit effort was requested.
    reasoning = kwargs.pop("reasoning", None)
    if reasoning is None and disable_thinking and kwargs.get("reasoning_effort") is None:
        reasoning = {"enabled": False}
    return OpenAICompatibleLLM(
        api_key=key,
        base_url=base_url or DEFAULT_OPENROUTER_URL,
        extra_headers=headers,
        provider=provider,
        reasoning=reasoning,
        **kwargs,
    )


def build_vllm_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    chat_template_kwargs: Optional[Dict[str, object]] = None,
    **kwargs,
) -> OpenAICompatibleLLM:
    key = api_key or os.getenv("VLLM_API_KEY") or "EMPTY"
    return OpenAICompatibleLLM(
        api_key=key,
        base_url=base_url or DEFAULT_VLLM_URL,
        chat_template_kwargs=chat_template_kwargs,
        **kwargs,
    )


def build_sub2api_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs,
) -> OpenAICompatibleLLM:
    """Build a client for a local or remote Sub2API deployment."""
    key = api_key or os.getenv("SUB2API_API_KEY")
    if not key:
        raise ValueError("SUB2API_API_KEY is required for the Sub2API backend")
    endpoint = base_url or os.getenv("SUB2API_BASE_URL") or DEFAULT_SUB2API_URL
    return OpenAICompatibleLLM(
        api_key=key,
        base_url=endpoint,
        **kwargs,
    )
