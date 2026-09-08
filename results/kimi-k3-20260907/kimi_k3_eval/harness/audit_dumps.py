#!/usr/bin/env python3
"""Audit raw API attempts against the final manifest-selected agent traces.

No provider calls or repository mutations occur. A completed trace must match one
whole client session; earlier sessions remain separately accounted for. Token
totals include only reported usage, including usage on unsuccessful attempts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlsplit, urlunsplit


SCHEMA = "expgym.api_attempt.v1"
STATES = {"in_progress", "success", "error", "malformed_response"}
_COMPACT_RECORD = object()


def strict_json(path):
    def reject(_value):
        raise ValueError("non-finite JSON")
    value = json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject)
    json.dumps(value, allow_nan=False)
    return value


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name, dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, str(path))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def require(condition, label):
    if not condition:
        raise ValueError(label)


def number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def token(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def timestamp(value):
    require(isinstance(value, str), "missing UTC timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timestamp lacks timezone")
    require(parsed.utcoffset().total_seconds() == 0, "timestamp is not UTC")
    return parsed.timestamp()


def messages_projection(messages):
    require(isinstance(messages, list), "messages is not a list")
    require(all(isinstance(message, dict) and "role" in message and "content" in message for message in messages), "malformed message record")
    return [{"role": message["role"], "content": message["content"]} for message in messages]


def visible_content(response):
    require(isinstance(response, dict), "response is not an object")
    choices = response.get("choices")
    require(isinstance(choices, list) and choices and isinstance(choices[0], dict), "response choices missing or malformed")
    message = choices[0].get("message")
    require(isinstance(message, dict), "response message missing")
    content = message.get("content")
    if isinstance(content, list):
        content = "\n".join(str(part.get("text", "")) for part in content
                            if isinstance(part, dict) and part.get("type") == "text")
    require(isinstance(content, str) and content.strip(), "success has no visible content")
    return content.strip()


def reasoning_usage(record):
    """Keep provider token accounting separate from returned reasoning text.

    Prefer completion details, then output details, then the SGLang top-level
    field. A zero is a reported value. Conflicting fields are retained for an
    explicit warning; neither text length nor an alternative field is added to
    completion tokens.
    """
    if record.get("_compact_record") is _COMPACT_RECORD:
        return record["_reasoning_usage"]
    response = record.get("response_json") or {}
    values = response.get("usage") if isinstance(response, dict) else None
    values = values if isinstance(values, dict) else {}
    fields = {}
    for name in ("completion_tokens_details", "output_tokens_details"):
        details = values.get(name)
        if isinstance(details, dict) and details.get("reasoning_tokens") is not None:
            fields[name + ".reasoning_tokens"] = details["reasoning_tokens"]
    if values.get("reasoning_tokens") is not None:
        fields["reasoning_tokens"] = values["reasoning_tokens"]
    selected_source = next(iter(fields), None)
    selected = fields.get(selected_source)
    return {
        "value": selected,
        "selected_source": selected_source,
        "reported_fields": fields,
        "conflict": any(value != selected for value in fields.values()),
    }


def usage(record):
    if record.get("_compact_record") is _COMPACT_RECORD:
        return record["_usage"]
    response = record.get("response_json") or {}
    values = response.get("usage") if isinstance(response, dict) else None
    values = values if isinstance(values, dict) else {}
    prompt_details = values.get("prompt_tokens_details") or values.get("input_tokens_details") or {}
    return {
        "input_tokens": values.get("prompt_tokens", values.get("input_tokens")),
        "output_tokens": values.get("completion_tokens", values.get("output_tokens")),
        "cached_input_tokens": prompt_details.get("cached_tokens") if isinstance(prompt_details, dict) else None,
        "cache_write_input_tokens": prompt_details.get("cache_write_tokens") if isinstance(prompt_details, dict) else None,
        "reasoning_tokens": reasoning_usage(record)["value"],
    }


def compact_attempt(record):
    """Retain accounting only between jobs, not every cumulative prompt in RAM."""
    compact = {key: record.get(key) for key in ("request_id", "generation_id", "client_id", "state", "will_retry", "retry_delay_seconds", "wall_time_seconds", "context", "started_at_utc", "finished_at_utc")}
    compact["state"] = record.get("state") if isinstance(record.get("state"), str) else "invalid"
    compact["context"] = record.get("context") if isinstance(record.get("context"), dict) else {}
    compact["_usage"] = usage(record)
    compact["_reasoning_usage"] = reasoning_usage(record)
    compact["_compact_record"] = _COMPACT_RECORD
    response = record.get("response_json") or {}
    choices = response.get("choices") if isinstance(response, dict) else None
    compact.update(_has_choice=False, _finish_reason=None, _reasoning_chars=None, _visible_chars=None)
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        compact["_has_choice"] = True
        compact["_finish_reason"] = choices[0].get("finish_reason")
        message = choices[0].get("message") or {}
        if isinstance(message, dict) and isinstance(message.get("reasoning_content"), str):
            compact["_reasoning_chars"] = len(message["reasoning_content"])
        try:
            compact["_visible_chars"] = len(visible_content(response))
        except (ValueError, KeyError, TypeError):
            pass
    return compact


def audit_attempt(record):
    require(isinstance(record, dict) and record.get("schema_version") == SCHEMA, "unknown attempt schema")
    require(not any(key.startswith("_") for key in record), "raw attempt contains reserved internal fields")
    for field in ("request_id", "generation_id", "client_id"):
        require(isinstance(record.get(field), str) and record[field], "missing " + field)
    require(isinstance(record.get("run_id"), str) and record["run_id"], "run_id missing")
    for field in ("attempt", "max_attempts", "pid", "thread_id"):
        require(token(record.get(field)) and record[field] >= 1, "invalid " + field)
    require(record["attempt"] <= record["max_attempts"], "attempt exceeds maximum")
    require(isinstance(record.get("context"), dict), "context missing")
    require(isinstance(record.get("request_payload"), dict), "request payload missing")
    require(isinstance(record["request_payload"].get("model"), str), "request model missing")
    messages_projection(record["request_payload"].get("messages"))
    require("response_raw" in record and "response_json" in record, "response fields missing")
    require(record.get("state") in STATES, "unknown attempt state")
    require(number(record.get("wall_time_seconds")) and record["wall_time_seconds"] >= 0, "invalid wall duration")
    started = timestamp(record.get("started_at_utc"))
    require(record["state"] != "in_progress", "unfinished in_progress request")
    require(timestamp(record.get("finished_at_utc")) >= started, "finish precedes start")
    require(isinstance(record.get("will_retry"), bool), "retry disposition missing")
    if record["will_retry"]:
        require(number(record.get("retry_delay_seconds")) and record["retry_delay_seconds"] >= 0, "retry delay missing")
        require(record["attempt"] < record["max_attempts"], "retry after configured maximum")
    else:
        require(record.get("retry_delay_seconds") is None, "unexpected retry delay")
    raw = record["response_raw"]
    parsed = record["response_json"]
    if raw is not None:
        require(isinstance(raw, str), "raw response is not text")
        try:
            from_raw = json.loads(raw)
        except ValueError:
            require(parsed is None, "invalid raw JSON has a parsed response")
        else:
            require(from_raw == parsed, "raw and parsed responses differ")
    else:
        require(parsed is None, "parsed response has no raw response")
    if record["state"] == "success":
        visible_content(parsed)
        require(raw is not None and record.get("error") is None and not record["will_retry"], "invalid success disposition")
    else:
        require(isinstance(record.get("error"), dict) and record["error"].get("type")
                and isinstance(record["error"].get("message"), str), "failure lacks error record")
        if record["state"] == "malformed_response":
            require(raw is not None, "malformed response body missing")
        if record["error"]["type"] == "HTTPError":
            require(token(record.get("http_status")) and 400 <= record["http_status"] < 600 and raw is not None, "HTTP failure status/body missing")
    for field, value in usage(record).items():
        require(value is None or token(value), "invalid reported " + field)
    for field, value in reasoning_usage(record)["reported_fields"].items():
        require(token(value), "invalid reported " + field)


def audit_generations(records):
    groups = defaultdict(list)
    for record in records:
        groups[(record["client_id"], record["generation_id"])].append(record)
    problems = []
    for (_client, generation), attempts in groups.items():
        attempts.sort(key=lambda record: record["attempt"])
        try:
            require([record["attempt"] for record in attempts] == list(range(1, len(attempts) + 1)), "attempt sequence has gaps or duplicates")
            first = attempts[0]
            for index, record in enumerate(attempts):
                for field in ("request_payload", "context", "run_id", "pid", "max_attempts", "endpoint"):
                    require(record.get(field) == first.get(field), "retry changes " + field)
                if index < len(attempts) - 1:
                    require(record["state"] != "success" and record["will_retry"], "retry follows terminal attempt")
                    require(timestamp(record["finished_at_utc"]) <= timestamp(attempts[index + 1]["started_at_utc"]), "retry timestamps overlap")
                else:
                    require(not record["will_retry"], "announced retry has no recorded attempt")
        except (ValueError, TypeError, KeyError) as error:
            problems.append({"generation_id": generation, "issue": str(error) if isinstance(error, ValueError) else "malformed retry metadata"})
    return groups, problems


def percentile(values, fraction):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def totals(records):
    result = {
        "http_attempts": len(records),
        "successful_logical_calls": sum(record.get("state") == "success" for record in records),
        "failed_http_attempts": sum(record.get("state") in {"error", "malformed_response"} for record in records),
        "in_progress_http_attempts": sum(record.get("state") == "in_progress" for record in records),
        "announced_retries": sum(record.get("will_retry") is True for record in records),
        "retry_delay_seconds_sum": sum(record["retry_delay_seconds"] for record in records if number(record.get("retry_delay_seconds"))),
        "unique_generations": len({(record.get("client_id"), record.get("generation_id")) for record in records}),
        "unique_client_sessions": len({record.get("client_id") for record in records}),
    }
    all_usage = [usage(record) for record in records]
    for field in ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_input_tokens", "reasoning_tokens"):
        reported = [entry[field] for entry in all_usage if token(entry[field])]
        result[field] = sum(reported)
        result[field + "_reported_attempts"] = len(reported)
    reasoning = [reasoning_usage(record) for record in records]
    result["reasoning_tokens_selected_sources"] = dict(Counter(
        entry["selected_source"] for entry in reasoning if entry["selected_source"] is not None))
    result["reasoning_tokens_top_level_reported_attempts"] = sum(
        token(entry["reported_fields"].get("reasoning_tokens")) for entry in reasoning)
    result["reasoning_tokens_nested_reported_attempts"] = sum(
        any(name != "reasoning_tokens" and token(value) for name, value in entry["reported_fields"].items())
        for entry in reasoning)
    result["reasoning_tokens_conflicting_attempts"] = sum(entry["conflict"] for entry in reasoning)
    result["usage_unreported_http_attempts"] = sum(
        entry["input_tokens"] is None or entry["output_tokens"] is None for entry in all_usage)
    result["cached_input_fraction_when_fully_reported"] = (
        result["cached_input_tokens"] / result["input_tokens"]
        if result["input_tokens"] > 0 and result["input_tokens_reported_attempts"] == result["cached_input_tokens_reported_attempts"] == len(records)
        else None
    )
    walls = [record["wall_time_seconds"] for record in records if number(record.get("wall_time_seconds"))]
    result.update(request_wall_seconds_sum=sum(walls), request_latency_seconds_p50=percentile(walls, .5),
                  request_latency_seconds_p95=percentile(walls, .95), request_latency_seconds_max=max(walls) if walls else None)
    finish_reasons, reasoning_lengths, visible_lengths = Counter(), [], []
    for record in records:
        if record.get("_compact_record") is _COMPACT_RECORD:
            if record["_has_choice"]:
                reason = record["_finish_reason"]
                finish_reasons[str(reason) if reason is not None else "unreported"] += 1
            if record["_reasoning_chars"] is not None:
                reasoning_lengths.append(record["_reasoning_chars"])
            if record["_visible_chars"] is not None:
                visible_lengths.append(record["_visible_chars"])
            continue
        response = record.get("response_json") or {}
        choices = response.get("choices") if isinstance(response, dict) else None
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            continue
        reason = choices[0].get("finish_reason")
        finish_reasons[str(reason) if reason is not None else "unreported"] += 1
        message = choices[0].get("message") or {}
        if isinstance(message, dict) and isinstance(message.get("reasoning_content"), str):
            reasoning_lengths.append(len(message["reasoning_content"]))
        try:
            visible_lengths.append(len(visible_content(response)))
        except (ValueError, TypeError, KeyError):
            pass
    result["finish_reasons"] = dict(finish_reasons)
    result["finish_reason_length_attempts"] = finish_reasons.get("length", 0)
    for label, lengths in (("reasoning_content_chars", reasoning_lengths), ("visible_content_chars", visible_lengths)):
        result.update({label + "_sum": sum(lengths), label + "_p50": percentile(lengths, .5),
                       label + "_p95": percentile(lengths, .95), label + "_max": max(lengths) if lengths else None,
                       label + "_reported_attempts": len(lengths)})
        result["nonempty_" + label[:-6] + "_attempts"] = sum(length > 0 for length in lengths)
        result["nonempty_" + label + "_sum"] = sum(length for length in lengths if length > 0)
    warning_counts = Counter(warning["type"] for record in records for warning in reasoning_warnings(record))
    result["nonempty_reasoning_content_with_zero_reported_tokens_attempts"] = warning_counts.get("reasoning_text_with_zero_reported_tokens", 0)
    result["reasoning_warning_counts"] = dict(warning_counts)
    return result


def reasoning_warnings(record):
    warnings = []
    accounting = reasoning_usage(record)
    if accounting["conflict"]:
        warnings.append({
            "type": "reasoning_token_sources_conflict",
            "selected_source": accounting["selected_source"],
            "reported_fields": {name: value if token(value) else "invalid"
                                for name, value in accounting["reported_fields"].items()},
        })
    compact = record if record.get("_compact_record") is _COMPACT_RECORD else compact_attempt(record)
    if (compact["_reasoning_chars"] or 0) > 0 and accounting["value"] == 0:
        warnings.append({
            "type": "reasoning_text_with_zero_reported_tokens",
            "reasoning_content_chars": compact["_reasoning_chars"],
            "selected_source": accounting["selected_source"],
            "reported_reasoning_tokens": 0,
        })
    return warnings


def load_repository_helpers(repo_root):
    # Reuse the frozen repository's formatting/trimming helpers, never its score
    # adapters or benchmark runtimes. This is read-only and imports no GPU stack.
    spec = importlib.util.spec_from_file_location("dump_audit_react", Path(repo_root) / "expgym/react_loop.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def materialize(trace, message_id):
    message = next(message for message in trace["messages"] if message["id"] == message_id)
    if "content" in message:
        content = message["content"]
    else:
        tool_id = message["content_ref"]["tool_call_id"]
        content = next(tool["observation"] for tool in trace["tool_calls"] if tool["id"] == tool_id)
    return {"role": str(message["role"]), "content": str(content)}


def logical_context_matches(record, job, output, agent_id=None):
    context = record.get("context") or {}
    if not isinstance(context, dict):
        return False
    identity = context.get("job") if job["system"] == "expgym" else context
    if not isinstance(identity, dict) or context.get("runner") != job["system"]:
        return False
    path_field = "trace_path" if job["system"] == "expgym" else "output_dir"
    if not isinstance(context.get(path_field), str) or not context[path_field]:
        return False
    for field in ("scenario", "cost_regime"):
        if identity.get(field) != job[field]:
            return False
    if job["scenario"] == "tuning":
        if identity.get("tuning_task") != job["tuning_task"]:
            return False
    elif identity.get("question_index") != job["question_index"]:
        return False
    if job["system"] == "expgym":
        return (identity.get("seed") == output["seed"] and identity.get("rep") == output["rep"]
                and identity.get("hypothesis_order") == output.get("hypothesis_order"))
    return (identity.get("seed") == output["agent_seeds"][agent_id]
            and identity.get("agent_id") == agent_id and identity.get("strategy") == output["strategy"])


def expected_parameters(record, job, manifest, seed):
    payload, settings = record["request_payload"], manifest["settings"]
    for field, expected in (("model", settings["model"]), ("seed", seed), ("temperature", job["temperature"])):
        require(payload.get(field) == expected, "request differs from planned " + field)
    require(payload.get("max_tokens") == settings.get("max_tokens"), "request differs from planned max_tokens")
    require((payload.get("chat_template_kwargs") or {}) == (settings.get("chat_template_kwargs") or {}), "request differs from planned chat_template_kwargs")
    require(payload.get("top_p") == settings.get("top_p", 1.0), "request differs from planned top_p")
    if settings.get("prompt_cache") == "disabled":
        require(payload.get("prompt_cache_key") is None, "disabled prompt-cache routing was sent")
    parsed = urlsplit(settings["base_url"].rstrip("/"))
    path = parsed.path.rstrip("/")
    if not path:
        path = "/v1/chat/completions"
    elif path.endswith(("/v1", "/api/v1", "/openai")):
        path += "/chat/completions"
    endpoint = urlunsplit((parsed.scheme, parsed.netloc.rsplit("@", 1)[-1], path, "", ""))
    require(record.get("endpoint") == endpoint, "request endpoint differs from planned backend")


def match_session(records, trace, job, output, manifest, helpers, agent_id=None):
    require(records, "empty client session")
    require(isinstance(trace, dict), "trace is not an object")
    require(all(logical_context_matches(record, job, output, agent_id) for record in records), "client session crosses logical identities")
    for record in records:
        for field in ("context", "run_id", "pid", "thread_id", "endpoint", "max_attempts"):
            require(record.get(field) == records[0].get(field), "client session changes " + field)
    successes = sorted((record for record in records if record["state"] == "success"),
                       key=lambda record: (record["started_at_utc"], record["generation_id"]))
    generations = {record["generation_id"] for record in records}
    require(len(successes) == len(generations), "client session contains an unsuccessful generation")
    previous_finish = None
    for success in successes:
        started = min(timestamp(record["started_at_utc"]) for record in records if record["generation_id"] == success["generation_id"])
        require(previous_finish is None or previous_finish <= started, "client generation timestamps overlap")
        previous_finish = timestamp(success["finished_at_utc"])
    if job["system"] == "expgym":
        calls = trace["llm_calls"]
        require(len(successes) == len(calls), "logical call count differs")
        for record, call in zip(successes, calls):
            expected_parameters(record, job, manifest, output["seed"])
            inputs = [materialize(trace, message_id) for message_id in call["input_message_ids"]]
            require(messages_projection(record["request_payload"]["messages"]) == inputs, "trace request messages differ")
            visible = visible_content(record["response_json"])
            expected = call.get("raw_output")
            if expected is None:
                expected = materialize(trace, call["output_message_id"])["content"]
            require(visible == expected, "trace response content differs")
            stored = visible
            if not call.get("forced"):
                if len(stored) > 8000:
                    stored = stored[:8000] + "\n[... output truncated due to excessive length ...]"
                if helpers._extract_action(stored):
                    stored = helpers._truncate_after_action(stored)
            require(stored == materialize(trace, call["output_message_id"])["content"], "trace stored response differs from decoded output")
            require(record["attempt"] == call["request_attempts"], "trace request_attempts differs")
            actual, saved = usage(record), call["usage"]
            require(isinstance(saved, dict), "trace usage is not an object")
            for field in ("input_tokens", "output_tokens"):
                require(actual[field] == saved.get(field), "trace " + field + " differs")
            cache = saved.get("cache") or {}
            require(isinstance(cache, dict), "trace cache is not an object")
            require(actual["cached_input_tokens"] == cache.get("read_tokens"), "trace cached tokens differ")
            require(actual["cache_write_input_tokens"] == cache.get("write_tokens"), "trace cache write tokens differ")
            require(cache.get("reported") == (actual["cached_input_tokens"] is not None or actual["cache_write_input_tokens"] is not None), "trace cache reporting flag differs")
        created = (trace.get("provenance") or {}).get("created_at")
        if created:
            require(max(timestamp(record["finished_at_utc"]) for record in records) <= timestamp(created), "session ends after trace creation")
    else:
        require(trace.get("agent_id") == agent_id and trace.get("seed") == output["agent_seeds"][agent_id], "agent trace identity differs")
        require(len(successes) == trace["api_calls"], "logical call count differs")
        messages = trace["messages"]
        messages_projection(messages)
        assistant_indices = [index for index, message in enumerate(messages) if message.get("role") == "assistant"]
        require(len(assistant_indices) == len(successes), "agent history/call count differs")
        limit = manifest["settings"].get("max_context_tokens")
        for index, (record, position) in enumerate(zip(successes, assistant_indices)):
            expected_parameters(record, job, manifest, output["agent_seeds"][agent_id])
            inputs = messages[:position]
            if limit is not None:
                inputs = helpers._trim_messages(inputs, limit)
            require(messages_projection(record["request_payload"]["messages"]) == messages_projection(inputs), "agent request messages differ")
            visible = visible_content(record["response_json"])
            forced = index == len(successes) - 1 and trace.get("aborted") is True
            if not forced:
                if len(visible) > 8000:
                    visible = visible[:8000] + "\n[... output truncated due to excessive length ...]"
                if helpers._extract_action(visible):
                    visible = helpers._truncate_after_action(visible)
            require(visible == messages[position]["content"], "agent response content differs")
        for dump_field, trace_field in (("input_tokens", "prompt_tokens"), ("output_tokens", "completion_tokens"),
                                        ("cached_input_tokens", "cached_prompt_tokens")):
            total = sum(usage(record)[dump_field] or 0 for record in successes)
            require(total == trace.get(trace_field), "agent " + trace_field + " differs")
        require((usage(successes[0])["input_tokens"] or 0) == trace.get("instruction_tokens"), "agent instruction_tokens differs")
    return successes


def explicit_fake(job, manifest):
    command = job.get("command") or []
    if "--backend" in command:
        index = command.index("--backend")
        return index + 1 < len(command) and command[index + 1] == "fake"
    return job.get("backend", manifest.get("settings", {}).get("backend")) == "fake"


def validate_promotion(path, manifest):
    if path is None:
        return None, [], {}
    mapping, issues, translated = strict_json(path), [], {}
    source_namespace = None
    try:
        require(mapping.get("operation") == "audited_pilot_to_full", "unknown promotion operation")
        require(mapping.get("status") == "copied_pending_full_runner_resume", "promotion copy has not completed")
        source_path, target_path = Path(mapping["source_manifest"]), Path(mapping["target_manifest"])
        for label, candidate in (("source_manifest", source_path), ("target_manifest", target_path)):
            if candidate.exists():
                require(sha256(candidate) == mapping[label + "_sha256"], "promotion " + label + " hash differs")
        source_manifest = strict_json(source_path)
        source_namespace = source_manifest.get("run_namespace")
        source_audit_path = Path(mapping["source_audit"])
        require(sha256(source_audit_path) == mapping["source_audit_sha256"], "promotion source audit hash differs")
        source_audit = strict_json(source_audit_path)
        require(source_audit.get("complete") is True and source_audit.get("manifest_sha256") == mapping["source_manifest_sha256"], "promotion source audit incomplete or for another manifest")
        planned = strict_json(target_path)
        require(source_manifest["settings"] == manifest["settings"], "promotion source settings differ")
        require(planned["settings"] == manifest["settings"], "promotion target settings differ")
        require(planned["source_tree_sha256"] == manifest["source_tree_sha256"], "promotion target source fingerprint differs")
        current_jobs = {job["id"]: job for job in manifest["jobs"]}
        source_jobs = {job["id"]: job for job in source_manifest["jobs"]}
        promotion_jobs = {}
        for job in mapping["jobs"]:
            require(job["job_id"] in current_jobs, "promotion contains an unselected job")
            require(job["job_id"] not in promotion_jobs, "duplicate promotion job")
            promotion_jobs[job["job_id"]] = job
            require(job["job_id"] in source_jobs, "promotion job absent from source manifest")
            require(Path(job["source_output_dir"]).resolve() == Path(source_jobs[job["job_id"]]["output_dir"]).resolve(), "promotion source output differs")
            require(Path(job["source_dump_dir"]).resolve() == Path(source_jobs[job["job_id"]]["dump_dir"]).resolve(), "promotion source dump directory differs")
            require(Path(job["target_output_dir"]).resolve() == Path(current_jobs[job["job_id"]]["output_dir"]).resolve(), "promotion target output differs")
            require(Path(job["target_dump_dir"]).resolve() == Path(current_jobs[job["job_id"]]["dump_dir"]).resolve(), "promotion target dump directory differs")
        for entry in mapping["files"]:
            target = Path(entry["target"])
            require(entry["job_id"] in promotion_jobs, "promoted file lacks a mapped job")
            job = promotion_jobs[entry["job_id"]]
            require(entry["kind"] in {"result", "agent", "summary", "api_dump", "source_status", "source_stdout"}, "unknown promoted file kind")
            if entry["kind"] in {"source_status", "source_stdout"}:
                status = entry["kind"] == "source_status"
                source_field = "source_status_path" if status else "source_stdout_log"
                target_field = "preserved_status_path" if status else "preserved_stdout_log"
                original_field = "status_path" if status else "stdout_log"
                require(Path(entry["source"]).resolve() == Path(job[source_field]).resolve() == Path(source_jobs[entry["job_id"]][original_field]).resolve(), "promoted execution source path differs")
                require(target.resolve() == Path(job[target_field]).resolve(), "promoted execution target path differs")
                require(entry["sha256"] == job["source_status_sha256" if status else "source_stdout_sha256"], "promoted execution checksum differs")
            else:
                location = "dump_dir" if entry["kind"] == "api_dump" else "output_dir"
                relative = target.resolve().relative_to(Path(job["target_" + location]).resolve())
                expected_source = Path(job["source_" + location]).resolve() / relative
                require(Path(entry["source"]).resolve() == expected_source, "promoted source and target relative paths differ")
            require(target.is_file() and sha256(target) == entry["sha256"], "promoted target file missing or changed")
            source = Path(entry["source"])
            if source.exists():
                require(sha256(source) == entry["sha256"], "promotion source file changed")
            target_key = str(target.resolve())
            require(target_key not in translated or translated[target_key] == str(source.resolve()), "conflicting promotion file mappings")
            translated[target_key] = str(source.resolve())
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        issues.append(str(error) if isinstance(error, ValueError) else "promotion map unreadable or malformed")
    return {"path": str(Path(path).resolve()), "sha256": sha256(path), "source_run_namespace": source_namespace}, issues, translated


def validate_session_location(session, trace_path, job, promoted_paths, seen):
    context = session[0]["context"]
    if job["system"] == "expgym":
        source = Path(context["trace_path"]).resolve()
        if source == trace_path.resolve():
            return None
    else:
        root = Path(context["output_dir"]).resolve()
        if root == Path(job["output_dir"]).resolve():
            return None
        source = root / trace_path.resolve().relative_to(Path(job["output_dir"]).resolve())
    mapped = promoted_paths.get(str(trace_path.resolve()))
    require(mapped is not None and Path(mapped).resolve() == source, "foreign artifact context requires a verified promotion source mapping")
    require(all(seen[record["request_id"]][2] in promoted_paths for record in session), "promoted raw attempt lacks a promotion file mapping")
    return mapped


def allowed_run_id(record, job, manifest, promotion):
    if manifest.get("run_namespace"):
        namespaces = {manifest["run_namespace"]}
        if promotion and promotion.get("source_run_namespace"):
            namespaces.add(promotion["source_run_namespace"])
        require(record["run_id"] in {"kimi-k3/" + namespace + "/" + job["id"] for namespace in namespaces}, "client run_id differs from manifest or promoted source")


def validate_job_assignment(record, job, manifest, promotion, promoted_paths, seen):
    for output in job["expected_outputs"]:
        artifacts = [(Path(output["path"]), None)] if job["system"] == "expgym" else [
            (Path(path), agent) for agent, path in enumerate(output["agent_paths"])]
        for trace_path, agent_id in artifacts:
            if logical_context_matches(record, job, output, agent_id):
                allowed_run_id(record, job, manifest, promotion)
                validate_session_location([record], trace_path, job, promoted_paths, seen)
                return
    raise ValueError("raw attempt does not belong to any planned logical agent in this job")


def run_audit(manifest_path, promotion_map=None):
    manifest_path = Path(manifest_path).resolve()
    manifest = strict_json(manifest_path)
    helpers = load_repository_helpers(manifest["repo_root"])
    promotion, issues, promoted_paths = validate_promotion(promotion_map or manifest.get("promotion_map"), manifest)
    records, files, all_attempts, unassigned_attempts, seen, selected_ids = [], [], [], [], {}, set()
    for job in manifest["jobs"]:
        if explicit_fake(job, manifest):
            records.append({"job_id": job["id"], "status": "skipped_fake", "reason": "explicit fake backend requires no HTTP dump"})
            continue
        attempts = []
        directory = Path(job["dump_dir"])
        for path in sorted(directory.rglob("*.json")):
            file_record = {"path": str(path.resolve()), "job_id": job["id"]}
            files.append(file_record)
            try:
                file_record.update(sha256=sha256(path), size_bytes=path.stat().st_size)
                record = strict_json(path)
                require(isinstance(record, dict), "attempt is not an object")
                request_id = record["request_id"]
                require(isinstance(request_id, str) and request_id, "invalid request_id")
                for field in ("client_id", "generation_id"):
                    require(isinstance(record.get(field), str) and record[field], "invalid " + field)
                file_record.update(request_id=request_id, client_id=record["client_id"], generation_id=record["generation_id"], state=record["state"])
                if request_id in seen:
                    require(seen[request_id][0] == file_record["sha256"], "duplicate request_id has different bytes")
                    require(seen[request_id][1] == job["id"], "request_id appears in different logical jobs")
                    file_record["duplicate_of"] = seen[request_id][2]
                    continue
                seen[request_id] = (file_record["sha256"], job["id"], str(path.resolve()))
                compact = compact_attempt(record)
                compact["job_id"] = job["id"]
                try:
                    validate_job_assignment(record, job, manifest, promotion, promoted_paths, seen)
                except (ValueError, KeyError, TypeError, IndexError, AttributeError):
                    unassigned_attempts.append(compact)
                    raise
                all_attempts.append(compact)
                audit_attempt(record)
                attempts.append(record)
            except (ValueError, OSError, KeyError, TypeError, IndexError, AttributeError) as error:
                file_record["issue"] = str(error) if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError) else "unreadable or malformed attempt"
                issues.append({"path": str(path.resolve()), "issue": file_record["issue"]})
        _groups, retry_issues = audit_generations(attempts)
        issues.extend({"job_id": job["id"], **issue} for issue in retry_issues)
        for temporary in directory.rglob("*.tmp"):
            issues.append({"path": str(temporary.resolve()), "issue": "unfinalized temporary dump file"})
        sessions = defaultdict(list)
        for attempt in attempts:
            sessions[attempt["client_id"]].append(attempt)
        for output in job["expected_outputs"]:
            outputs = [(Path(output["path"]), None)] if job["system"] == "expgym" else [
                (Path(path), agent) for agent, path in enumerate(output["agent_paths"])]
            for trace_path, agent_id in outputs:
                row = {"job_id": job["id"], "system": job["system"], "trace_path": str(trace_path.resolve()),
                       "agent_id": agent_id, "strategy": output.get("strategy"), "rep": output.get("rep"), "status": "invalid"}
                records.append(row)
                try:
                    trace = strict_json(trace_path)
                    row["trace_sha256"] = sha256(trace_path)
                    require(isinstance(trace, dict), "trace is not an object")
                    dump_identity = (trace.get("run") or {}).get("api_dump") if job["system"] == "expgym" else trace.get("api_dump")
                    if dump_identity is not None:
                        require(isinstance(dump_identity, dict) and dump_identity.get("schema_version") == SCHEMA
                                and isinstance(dump_identity.get("client_id"), str) and dump_identity["client_id"], "invalid persisted API dump identity")
                        row["persisted_api_dump"] = dump_identity
                    candidates, rejected = [], []
                    for client_id, session in sessions.items():
                        if dump_identity is not None and client_id != dump_identity["client_id"]:
                            continue
                        if not logical_context_matches(session[0], job, output, agent_id):
                            continue
                        try:
                            if dump_identity is not None:
                                require(all(record.get("run_id") == dump_identity.get("run_id") for record in session), "persisted run_id differs from raw client session")
                            allowed_run_id(session[0], job, manifest, promotion)
                            successes = match_session(session, trace, job, output, manifest, helpers, agent_id)
                            mapped = validate_session_location(session, trace_path, job, promoted_paths, seen)
                            candidates.append((max(record["finished_at_utc"] for record in session), client_id, session, successes, mapped))
                        except (ValueError, KeyError, TypeError, IndexError, AttributeError, StopIteration) as error:
                            rejected.append({"client_id": client_id, "reason": str(error) if isinstance(error, ValueError) else "malformed trace/session"})
                    row["rejected_sessions"] = rejected
                    row["matching_client_ids"] = [candidate[1] for candidate in candidates]
                    row["matching_session_count"] = len(candidates)
                    require(candidates, "no complete client session matches final trace content, requests, and usage")
                    require(len(candidates) == 1, "ambiguous client attribution: multiple complete sessions exactly match this trace")
                    _finished, client_id, session, successes, mapped = candidates[0]
                    require(not any(record["request_id"] in selected_ids for record in session), "client session matches more than one trace")
                    row.update(status="valid", client_id=client_id, matching_session_count=len(candidates),
                               selection_method="persisted_client_id_with_full_validation" if dump_identity is not None else "unique_complete_matching_client_session",
                               selected_totals=totals(session), selected_success_totals=totals(successes),
                               request_ids=[record["request_id"] for record in session],
                               checks={"logical_identity": True, "request_messages": True, "visible_content": True,
                                       "logical_call_count": True, "input_output_usage": True, "cached_input_usage": True,
                                       "per_call_usage_and_retry_count": job["system"] == "expgym"})
                    row.update(started_at_utc=min(record["started_at_utc"] for record in session),
                               finished_at_utc=max(record["finished_at_utc"] for record in session),
                               pid=session[0]["pid"], run_id=session[0].get("run_id"))
                    row["calls"] = []
                    for call_index, success in enumerate(successes):
                        call_attempts = sorted((record for record in session if record["generation_id"] == success["generation_id"]), key=lambda record: record["attempt"])
                        row["calls"].append({
                            "logical_call_index": call_index,
                            "llm_call_id": trace["llm_calls"][call_index]["id"] if job["system"] == "expgym" else None,
                            "generation_id": success["generation_id"], "successful_request_id": success["request_id"],
                            "request_ids": [record["request_id"] for record in call_attempts],
                            "request_attempts": len(call_attempts), "successful_usage": usage(success),
                        })
                    if mapped is not None:
                        row["promoted_from_trace_path"] = mapped
                    selected_ids.update(record["request_id"] for record in session)
                except (ValueError, OSError, KeyError, TypeError, IndexError, AttributeError, StopIteration) as error:
                    row["status"] = "invalid"
                    row["issue"] = str(error) if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError) else "trace unreadable or malformed"
    selected = [record for record in all_attempts if record["request_id"] in selected_ids]
    historical = [record for record in all_attempts if record["request_id"] not in selected_ids]
    historical_sessions = defaultdict(list)
    for record in historical:
        historical_sessions[record["client_id"]].append(record)
    for file_record in files:
        file_record["classification"] = "invalid" if "issue" in file_record else "selected" if file_record.get("request_id") in selected_ids else "historical"
    status_counts = dict(Counter(row["status"] for row in records))
    return {
        "schema_version": "kimi_k3.raw_dump_audit.v1", "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(manifest_path), "manifest_sha256": sha256(manifest_path),
        "auditor_sha256": sha256(__file__), "promotion_map": promotion,
        "complete": bool(records) and not issues and all(row["status"] in {"valid", "skipped_fake"} for row in records),
        "statuses": status_counts, "totals": totals(all_attempts), "selected_totals": totals(selected),
        "selected_success_totals": totals([record for record in selected if record["state"] == "success"]),
        "historical_totals": totals(historical), "unique_dump_files": len(seen),
        "unassigned_totals": totals(unassigned_attempts),
        "dump_files_enumerated": len(files), "invalid_dump_files": sum("issue" in entry for entry in files),
        "duplicate_dump_files": sum("duplicate_of" in entry for entry in files),
        "records": records, "issues": issues, "files": files,
        "warnings": [{"request_id": record["request_id"], "client_id": record["client_id"],
                      "job_id": record["job_id"], **warning}
                     for record in all_attempts for warning in reasoning_warnings(record)],
        "historical_sessions": [{"client_id": client_id, "job_id": session[0]["job_id"], "context": {key: value for key, value in session[0]["context"].items()
                                                                       if key in {"runner", "strategy", "agent_id", "seed", "scenario", "question_index"}},
                                 "totals": totals(session), "started_at_utc": min((record["started_at_utc"] for record in session if isinstance(record["started_at_utc"], str)), default=None),
                                 "finished_at_utc": max((record["finished_at_utc"] for record in session if isinstance(record["finished_at_utc"], str)), default=None),
                                 "terminal_states": dict(Counter(record["state"] for record in session if not record["will_retry"]))}
                                for client_id, session in sorted(historical_sessions.items())],
        "accounting_notes": [
            "All totals deduplicate request_id. selected_totals includes retries belonging to matched final client sessions.",
            "selected_success_totals is comparable with trace logical-call token counters; historical sessions are excluded from it.",
            "Token sums include only provider-reported usage. Failed requests without usage may still have consumed compute.",
            "Reasoning text is retained in original dump files; reports contain only lengths and reported reasoning tokens.",
            "Reasoning token fields prefer completion_tokens_details, output_tokens_details, then usage.reasoning_tokens; conflicting provider fields generate warnings.",
            "Nonempty reasoning_content is counted independently. A reported reasoning token count of zero does not establish that no reasoning text was generated.",
            "PoolAct saves aggregate usage but no per-call retry count; per-call attempt counts come from the raw dump.",
            "If multiple complete client sessions match a final trace, attribution is ambiguous and acceptance fails instead of choosing arbitrary retry costs.",
        ],
    }


def run_usage_self_tests():
    """Small in-memory fixtures; no repository, output files, or APIs required."""
    def fixture(extra_usage, reasoning_content=None):
        response = {
            "choices": [{"message": {"content": "Answer", "reasoning_content": reasoning_content}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 9,
                      "prompt_tokens_details": {"cached_tokens": 3}, **extra_usage},
        }
        return {
            "schema_version": SCHEMA, "request_id": "request", "generation_id": "generation",
            "client_id": "client", "run_id": "fixture", "attempt": 1, "max_attempts": 1,
            "pid": 1, "thread_id": 1, "context": {}, "state": "success", "wall_time_seconds": .1,
            "request_payload": {"model": "fixture", "messages": [{"role": "user", "content": "Prompt"}]},
            "started_at_utc": "2026-09-07T00:00:00+00:00", "finished_at_utc": "2026-09-07T00:00:01+00:00",
            "will_retry": False, "retry_delay_seconds": None, "error": None,
            "response_json": response, "response_raw": json.dumps(response),
        }

    cases = [
        ({}, None, None, False),
        ({"reasoning_tokens": 0}, 0, "reasoning_tokens", False),
        ({"reasoning_tokens": 7}, 7, "reasoning_tokens", False),
        ({"completion_tokens_details": {"reasoning_tokens": 5}}, 5, "completion_tokens_details.reasoning_tokens", False),
        ({"output_tokens_details": {"reasoning_tokens": 4}}, 4, "output_tokens_details.reasoning_tokens", False),
        ({"completion_tokens_details": {"reasoning_tokens": None}, "reasoning_tokens": 2}, 2, "reasoning_tokens", False),
        ({"completion_tokens_details": {"other": 1}, "output_tokens_details": {"reasoning_tokens": 4}}, 4, "output_tokens_details.reasoning_tokens", False),
        ({"completion_tokens_details": {"reasoning_tokens": 5}, "reasoning_tokens": 5}, 5, "completion_tokens_details.reasoning_tokens", False),
        ({"completion_tokens_details": {"reasoning_tokens": 5}, "reasoning_tokens": 0}, 5, "completion_tokens_details.reasoning_tokens", True),
        ({"completion_tokens_details": {"reasoning_tokens": 5}, "output_tokens_details": {"reasoning_tokens": 3}, "reasoning_tokens": 1}, 5, "completion_tokens_details.reasoning_tokens", True),
    ]
    checks = 0
    for extra, expected, source, conflict in cases:
        record = fixture(extra)
        audit_attempt(record)
        normalized = usage(record)
        require(normalized["reasoning_tokens"] == expected, "self-test reasoning normalization")
        require((normalized["input_tokens"], normalized["output_tokens"], normalized["cached_input_tokens"]) == (11, 9, 3), "self-test changed trace usage semantics")
        require(reasoning_usage(record)["selected_source"] == source and reasoning_usage(record)["conflict"] == conflict, "self-test source selection")
        require(totals([record]) == totals([compact_attempt(record)]), "self-test compact accounting mismatch")
        require(any(warning["type"] == "reasoning_token_sources_conflict" for warning in reasoning_warnings(record)) == conflict, "self-test conflict warning")
        checks += 1
    for invalid in (-1, True, 1.5, "7"):
        record = fixture({"completion_tokens_details": {"reasoning_tokens": 3}, "reasoning_tokens": invalid})
        try:
            audit_attempt(record)
        except ValueError:
            pass
        else:
            raise AssertionError("self-test accepted invalid secondary reasoning field")
        checks += 1
    records = [fixture({"reasoning_tokens": 0}, text) for text in (None, "", "think")]
    report = totals(records)
    require(report["reasoning_tokens_reported_attempts"] == 3 and report["reasoning_tokens"] == 0, "self-test lost reported zero")
    require(report["reasoning_content_chars_reported_attempts"] == 2 and report["nonempty_reasoning_content_attempts"] == 1
            and report["reasoning_content_chars_sum"] == 5, "self-test confused text presence with nonempty text")
    require(report["nonempty_reasoning_content_with_zero_reported_tokens_attempts"] == 1
            and report["reasoning_tokens_conflicting_attempts"] == 0, "self-test conflated text observation with source conflict")
    require(totals(records) == totals([compact_attempt(record) for record in records]), "self-test compact text accounting mismatch")
    return checks + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--promotion-map", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--self-test", action="store_true", help="run in-memory reasoning usage boundary fixtures")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"reasoning_usage_self_tests": "passed", "cases": run_usage_self_tests()}))
        return 0
    if args.manifest is None:
        parser.error("--manifest is required unless --self-test is used")
    result = run_audit(args.manifest, args.promotion_map)
    output_dir = args.output_dir or args.manifest.resolve().parent / "raw_dump_audit"
    destination = output_dir / "raw_dump_audit.json"
    write_json(destination, result)
    print(json.dumps({"complete": result["complete"], "statuses": result["statuses"],
                      "http_attempts": result["totals"]["http_attempts"], "report": str(destination)}, ensure_ascii=False))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
