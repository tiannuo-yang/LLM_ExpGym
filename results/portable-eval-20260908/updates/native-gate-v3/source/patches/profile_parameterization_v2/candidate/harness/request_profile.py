"""Small external-harness request contract; no benchmark or server operations.

Explicit profiles change only request generation and declared external serving/
randomness expectations. They do not establish observed seed repeatability or
relax task, score, dump, resume or provider-protocol acceptance.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path


DEFAULT_PROFILE = {
    "schema_version": 1, "model": "kimi-k3", "temperature": 1.0,
    "top_p": 1.0, "top_k": None, "reasoning_effort": "max",
    "chat_template_kwargs": {"thinking": True, "thinking_effort": "max"},
    "server_context_tokens": 524288, "randomness_contract": "strict",
    "expected_metadata": {},
}
FIELDS = frozenset(DEFAULT_PROFILE)
_CREDENTIAL_KEYS = frozenset({
    "authorization", "proxy_authorization", "api_key", "apikey", "x_api_key",
    "access_token", "refresh_token", "password", "secret", "client_secret",
})


def _reject_credentials(value):
    """Match real_smoke.validate_config's recursive persisted-config boundary."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if (normalized_key in _CREDENTIAL_KEYS
                    or normalized_key.endswith(("_api_key", "_access_token", "_secret"))):
                # Neither user-supplied key text nor values enter diagnostics.
                raise ValueError("Credential keys are not allowed in request-profile objects")
            _reject_credentials(item)
    elif isinstance(value, list):
        for item in value:
            _reject_credentials(item)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate profile JSON field: " + key)
        result[key] = value
    return result


def validate_profile(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError("Profile must contain exactly: " + ", ".join(sorted(FIELDS)))
    profile = copy.deepcopy(value)
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1:
        raise ValueError("Unsupported request-profile schema_version")
    if not isinstance(profile["model"], str) or not profile["model"].strip() or profile["model"] != profile["model"].strip():
        raise ValueError("model must be a nonempty string without surrounding whitespace")
    for name in ("temperature", "top_p"):
        number = profile[name]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ValueError(name + " must be finite numeric, not bool")
        profile[name] = float(number)
    if profile["temperature"] < 0 or not 0 < profile["top_p"] <= 1:
        raise ValueError("temperature must be nonnegative and top_p must lie in (0, 1]")
    top_k = profile["top_k"]
    if top_k is not None and (type(top_k) is not int or (top_k != -1 and top_k < 1)):
        raise ValueError("top_k must be null (omitted), -1, or a positive integer")
    effort = profile["reasoning_effort"]
    if effort is not None and (not isinstance(effort, str) or not effort.strip() or effort != effort.strip()):
        raise ValueError("reasoning_effort must be null or a nonempty string")
    for name in ("chat_template_kwargs", "expected_metadata"):
        if not isinstance(profile[name], dict):
            raise ValueError(name + " must be a JSON object")
        _reject_credentials(profile[name])
    if type(profile["server_context_tokens"]) is not int or profile["server_context_tokens"] <= 0:
        raise ValueError("server_context_tokens must be a positive integer")
    if profile["randomness_contract"] not in ("strict", "seed_labels_only"):
        raise ValueError("randomness_contract must be strict or seed_labels_only")
    # No nonfinite values or opaque Python objects hidden in nested expectations.
    try:
        json.dumps(profile, allow_nan=False)
    except (TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise ValueError("Request profile must be finite JSON") from exc
    return profile


def load_profile(path):
    raw = Path(path).read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
        profile = validate_profile(value)
    except (UnicodeError, ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise ValueError("Invalid request profile: " + str(exc)) from exc
    return profile, hashlib.sha256(raw).hexdigest()


def add_arguments(parser, *, server_context_already_present=False):
    parser.add_argument("--request-profile", type=Path,
                        help="Complete generation/declared-serving JSON; unknown or conflicting fields are rejected.")
    parser.add_argument("--model-alias", help="Output naming only; does not select benchmark items.")
    if not server_context_already_present:
        parser.add_argument("--server-context-tokens", type=int, default=None)


def resolve(args, parser):
    path = args.request_profile
    if path is not None:
        path = path.expanduser().resolve()
        try:
            profile, raw_sha = load_profile(path)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        for option, field in (("model", "model"), ("server_context_tokens", "server_context_tokens")):
            if getattr(args, option, None) is not None and getattr(args, option) != profile[field]:
                parser.error("--" + option.replace("_", "-") + " conflicts with --request-profile")
        source = {"path": str(path), "file_sha256": raw_sha}
    else:
        profile = copy.deepcopy(DEFAULT_PROFILE)
        if args.model is not None:
            profile["model"] = args.model
        if args.server_context_tokens is not None:
            profile["server_context_tokens"] = args.server_context_tokens
        try:
            profile = validate_profile(profile)
        except ValueError as exc:
            parser.error(str(exc))
        source = {"path": None, "file_sha256": None}
    alias = args.model_alias
    if alias is not None and (not alias or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in alias)):
        parser.error("--model-alias must contain only ASCII letters, digits, underscore or hyphen")
    args.request_profile = path
    args.model, args.server_context_tokens = profile["model"], profile["server_context_tokens"]
    args._request_profile = {"profile": profile, "sha256": digest(profile), "source": source}
    return args


def profile(args):
    return copy.deepcopy(args._request_profile["profile"])


def identity(args):
    return copy.deepcopy(args._request_profile)


def unchanged(args):
    if args.request_profile is None:
        return True
    try:
        current, raw_sha = load_profile(args.request_profile)
    except (OSError, ValueError):
        return False
    return current == args._request_profile["profile"] and raw_sha == args._request_profile["source"]["file_sha256"]


def model_alias(args, legacy_default):
    return args.model_alias or ("evaluation-model" if args.request_profile is not None else legacy_default)


def numeric_argument(value):
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def generation_arguments(args):
    """Preserve old K3 argv exactly; explicit profiles transmit P and optional K."""
    selected = profile(args)
    result = ["--max-tokens", "32768"]
    if selected["reasoning_effort"] is not None:
        result += ["--reasoning-effort", selected["reasoning_effort"]]
    result += ["--chat-template-kwargs", json.dumps(selected["chat_template_kwargs"], sort_keys=True)]
    if args.request_profile is not None:
        result += ["--top-p", numeric_argument(selected["top_p"])]
        if selected["top_k"] is not None:
            result += ["--top-k", str(selected["top_k"])]
    return result


def wire_errors(payload, args, *, seed):
    """Exact generation field/omission checks, independent of model names."""
    selected = profile(args)
    errors = []
    expected = {"model": selected["model"], "temperature": selected["temperature"],
                "top_p": selected["top_p"], "seed": seed, "max_tokens": 32768}
    for key, value in expected.items():
        if payload.get(key) != value or isinstance(payload.get(key), bool):
            errors.append("generation field differs: " + key)
    for key in ("top_k", "reasoning_effort"):
        value = selected[key]
        if (value is None and key in payload) or (value is not None and payload.get(key) != value) or (key == "top_k" and value is not None and type(payload.get(key)) is not int):
            errors.append("generation value/omission differs: " + key)
    kwargs = selected["chat_template_kwargs"]
    try:
        same_kwargs = isinstance(payload.get("chat_template_kwargs"), dict) and digest(payload["chat_template_kwargs"]) == digest(kwargs)
    except (TypeError, ValueError, RecursionError, OverflowError):
        same_kwargs = False
    if (kwargs and not same_kwargs) or (not kwargs and "chat_template_kwargs" in payload):
        errors.append("chat_template_kwargs differ")
    # This fixed experiment profile does not route through provider-specific
    # sampling dictionaries, min_p overrides, or alternate reasoning objects.
    for key in ("min_p", "reasoning", "provider"):
        if key in payload:
            errors.append("unexpected request generation override: " + key)
    return errors
