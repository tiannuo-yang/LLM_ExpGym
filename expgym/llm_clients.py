"""LLM backend implementations that assume OpenAI-compatible APIs.

All real backends share the same message schema. Use ``base_url`` to target vendors
such as Gemini that offer OpenAI-compatible endpoints.
"""
from __future__ import annotations

import http.client
import json
import logging
import os
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Union

logger = logging.getLogger("expgym")

from expgym.react_loop import LLMBackend, LLMOutput

Transport = Callable[[urllib.request.Request, float], bytes]
DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEFAULT_VLLM_URL = "http://localhost:8000/v1/chat/completions"
DEFAULT_SUB2API_URL = "http://127.0.0.1:8080/v1/chat/completions"


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


class OpenAICompatibleLLM(LLMBackend):
    """LLMBackend that speaks the OpenAI Chat Completions protocol.

    Accepts either a messages list (multi-turn) or a plain string (legacy).
    """

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
    ) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("An API key is required for OpenAICompatibleLLM")
        self.config = OpenAIConfig(
            api_key=key,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
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
        )
        self._transport = transport

    def generate(self, messages: Union[str, List[Dict[str, str]]]) -> LLMOutput:
        if isinstance(messages, str):
            # Legacy: wrap plain string into messages list
            msgs: List[Dict[str, str]] = []
            if self.config.system_prompt:
                msgs.append({"role": "system", "content": self.config.system_prompt})
            msgs.append({"role": "user", "content": messages})
        else:
            msgs = list(messages)

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
        if self.config.chat_template_kwargs:
            payload["chat_template_kwargs"] = self.config.chat_template_kwargs
        if self.config.prompt_cache_key is not None:
            payload["prompt_cache_key"] = self.config.prompt_cache_key
        request = urllib.request.Request(
            self.config.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                **self.config.extra_headers,
            },
            method="POST",
        )
        max_retries = 10
        for attempt in range(max_retries + 1):
            try:
                raw = self._transport(request, self.config.timeout)
                break
            except urllib.error.HTTPError as exc:
                code = exc.code
                body = exc.read().decode("utf-8", "ignore")
                if code in (429, 500, 502, 503) and attempt < max_retries:
                    wait = min(2 ** attempt * 3, 120)
                    logger.warning("HTTP %d, retry %d/%d in %ds", code, attempt + 1, max_retries, wait)
                    import time as _time
                    _time.sleep(wait)
                    # rebuild request (body consumed)
                    request = urllib.request.Request(
                        self.config.base_url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={
                            "Authorization": f"Bearer {self.config.api_key}",
                            "Content-Type": "application/json",
                            **self.config.extra_headers,
                        },
                        method="POST",
                    )
                    continue
                raise RuntimeError(f"API error: {body}") from exc
            except urllib.error.URLError as exc:
                if attempt < max_retries:
                    wait = min(2 ** attempt * 3, 120)
                    logger.warning("URLError, retry %d/%d in %ds: %s", attempt + 1, max_retries, wait, exc)
                    import time as _time
                    _time.sleep(wait)
                    continue
                raise RuntimeError(f"API connection failed: {exc}") from exc

        data = json.loads(raw.decode("utf-8"))
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("API returned no choices")
        message = choices[0].get("message")
        if not message or "content" not in message:
            raise RuntimeError("API choice missing message content")
        usage = data.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
        completion_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
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
            text=str(message["content"]).strip(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_prompt_tokens=cached_prompt_tokens,
            cache_write_prompt_tokens=cache_write_prompt_tokens,
            request_attempts=attempt + 1,
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
    # Disable thinking by default for deterministic output
    reasoning = kwargs.pop("reasoning", None)
    if reasoning is None and disable_thinking:
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
