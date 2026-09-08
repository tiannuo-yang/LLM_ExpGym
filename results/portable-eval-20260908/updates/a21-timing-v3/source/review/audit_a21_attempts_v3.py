#!/usr/bin/env python3
"""A21 21-job/21-trace post-drain attempt/usage audit; no model/evaluator/network calls.

Derived from audit_scenario_attempts_20260908.py; the original is unmodified.

Prints analysis without writing receipts or modifying inputs. The caller must
also establish that the runner has drained. Scores never select audit rows.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path


def strict_json(text):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate JSON key")
            value[key] = item
        return value

    def reject(_value):
        raise ValueError("Non-finite JSON constant")

    return json.loads(text, object_pairs_hook=unique, parse_constant=reject)


def materialize(trace, identifier):
    message = copy.deepcopy(next(m for m in trace["messages"] if m["id"] == identifier))
    message.pop("id")
    message.pop("request_only", None)
    reference = message.pop("content_ref", None)
    if reference is not None:
        if reference["kind"] != "tool_observation":
            raise ValueError("Unknown content reference")
        tool = next(t for t in trace["tool_calls"] if t["id"] == reference["tool_call_id"])
        message["content"] = tool["observation"]
    return message


def usage_values(usage):
    usage = usage or {}
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}

    def first(primary, fallback):
        return primary if primary is not None else fallback

    return {
        "input_tokens": first(usage.get("prompt_tokens"), usage.get("input_tokens")),
        "output_tokens": first(usage.get("completion_tokens"), usage.get("output_tokens")),
        "provider_total_tokens": usage.get("total_tokens"),
        "reasoning_tokens": first(usage.get("reasoning_tokens"),
                                  first(completion_details.get("reasoning_tokens"), output_details.get("reasoning_tokens"))),
        "cache_read_tokens": details.get("cached_tokens"),
        "cache_write_tokens": details.get("cache_write_tokens"),
    }


def total_usage(records):
    values = [usage_values(record) for record in records]
    return {field: {
        "known_sum": sum(row[field] for row in values if row[field] is not None),
        "known_count": sum(row[field] is not None for row in values),
        "unknown_count": sum(row[field] is None for row in values),
    } for field in usage_values({})}


def provider_usage(raw):
    response = raw.get("response_json")
    return response.get("usage") if isinstance(response, dict) else None


def strict_dump_inventory(run_dir):
    """No symlink anywhere in/above dumps; every JSON must be in one flat job dir."""
    dump_root = Path(run_dir).absolute() / "dumps"
    for path in list(dump_root.parents) + [dump_root]:
        if path.is_symlink():
            raise ValueError("Dump ancestor is a symlink")
    if not dump_root.is_dir():
        raise ValueError("Missing dump directory")
    for directory, directories, files in os.walk(dump_root, followlinks=False):
        for name in directories + files:
            if (Path(directory) / name).is_symlink():
                raise ValueError("Dump descendant is a symlink")
    recursive = sorted(dump_root.rglob("*.json"))
    flat = sorted(dump_root.glob("*/*.json"))
    if recursive != flat or any(not path.is_file() for path in recursive):
        raise ValueError("Dump JSON inventory contains a root orphan, deep file or non-file")
    return flat


def ordered_native_history(messages, delivered_assistants, previous_prefix):
    """A21 ExpGym has no context trim: retain every prior delivery and feedback."""
    if [message for message in messages if message.get("role") == "assistant"] != delivered_assistants:
        return False
    if messages[:len(previous_prefix)] != previous_prefix:
        return False
    pending = []
    for message in messages:
        role = message.get("role")
        if role == "assistant":
            if pending:
                return False
            pending.extend(call.get("id") for call in message.get("tool_calls") or [])
        elif role == "tool":
            identifier = message.get("tool_call_id")
            if identifier not in pending:
                return False
            pending.remove(identifier)
        elif pending:
            return False
    return not pending


def audit(run_dir, authorization):
    root = Path(run_dir).resolve()
    if not (root / "execution.json").is_file():
        raise ValueError("No final execution.json; do not audit a still-running collection")
    errors, files, warnings = [], {}, []

    def require(condition, label):
        if not condition:
            errors.append(label)

    def read(path):
        path = Path(path).resolve()
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
                str(path) + ": changed while reading")
        record = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                  "bytes": len(raw), "mtime_ns": after.st_mtime_ns}
        if str(path) in files:
            require(files[str(path)] == record, str(path) + ": changed between reads")
        files[str(path)] = record
        return strict_json(raw)

    authorization = read(authorization)
    manifest = read(root / "manifest.json")
    execution = read(root / "execution.json")
    identity = manifest["identity"]
    settings, jobs = identity["settings"], identity["jobs"]
    require(authorization.get("authorized") is True, "Missing authorization")
    require(authorization["source_tree_sha256"] == identity["static_acceptance"]["source_tree_sha256"], "Authorized main source differs")
    require(authorization["harness_sha256"] in identity["harness_files"].values(), "Authorized harness differs")
    require(authorization["manifest_sha256"] == files[str(root / "manifest.json")]["sha256"], "Authorized manifest bytes differ")
    require(execution.get("executed") is True, "Receipt does not record execution")
    require(execution.get("unstarted") == [] and execution.get("passed") is True and all(row.get("passed") is True for row in execution["results"]), "Not every planned job completed")
    require(len(jobs) == 21 and sum(j["expected_traces"] for j in jobs) == 21, "Authorized 21-job/21-trace matrix differs")
    require(Path(authorization["output_dir"]).resolve() == root, "Authorized run directory differs")
    require(authorization["counts"] == {"child_jobs": 21, "agent_traces": 21, "guarded_resume_skips": 21, "A1_hpo": 9, "A2_search_audit": 12, "legacy_paramnet_python37": 3, "native_python311": 18}, "Authorized scope differs")
    commands = read(root / "commands.json")
    require(authorization["commands_sha256"] == files[str(root / "commands.json")]["sha256"], "Authorized commands differ")
    expected_ids = {job["id"] for job in jobs}
    require(len(expected_ids) == 21 and set(commands) == expected_ids and all(job["system"] == "expgym" for job in jobs), "Fixed A21 selection differs")
    require({row["job_id"] for row in execution["results"]} == expected_ids and len(execution["results"]) == 21, "Execution job set differs")
    expected_run = "pilot-a21:" + root.name
    dump_paths = strict_dump_inventory(run_dir)
    raw_by_client, raw_by_request = defaultdict(list), {}
    states, http_statuses = Counter(), Counter()
    success_http_status_unknown = 0
    client_request_configs = {}
    for path in dump_paths:
        raw = read(path)
        label = str(path.relative_to(root))
        require(raw.get("schema_version") == "expgym.api_attempt.v1", label + ": dump schema differs")
        request_id = raw.get("request_id")
        require(path.stem == request_id and request_id not in raw_by_request, label + ": duplicate/misnamed request ID")
        require(raw.get("run_id") == expected_run, label + ": run ID differs")
        require(isinstance(raw.get("client_id"), str) and bool(raw["client_id"]), label + ": missing client ID")
        require(isinstance(raw.get("generation_id"), str) and bool(raw["generation_id"]), label + ": missing generation ID")
        require(type(raw.get("attempt")) is int and 1 <= raw["attempt"] <= 3, label + ": attempt index outside bound")
        require(raw.get("max_attempts") == settings["http_max_retries"] + 1, label + ": max attempts differs")
        states[raw.get("state")] += 1
        http_statuses[str(raw["http_status"]) if raw.get("http_status") is not None else "unknown"] += 1
        require(raw.get("state") in {"success", "error", "malformed_response"}, label + ": unfinished/unknown attempt")
        require(isinstance(raw.get("finished_at_utc"), str), label + ": missing finish timestamp")
        if raw.get("finished_at_utc"):
            require(datetime.fromisoformat(raw["finished_at_utc"]) >= datetime.fromisoformat(raw["started_at_utc"]), label + ": timestamps reversed")
        if raw.get("response_json") is not None:
            require(isinstance(raw.get("response_raw"), str) and strict_json(raw["response_raw"]) == raw["response_json"], label + ": raw/parsed response differ")
        if raw["state"] == "success":
            require(raw.get("error") is None and raw.get("will_retry") is False, label + ": success marked retry/error")
            success_http_status_unknown += raw.get("http_status") is None
        payload = raw["request_payload"]
        reported_usage = provider_usage(raw)
        if isinstance(reported_usage, dict):
            reasoning_sources = {"reasoning_tokens": reported_usage.get("reasoning_tokens")}
            for details_key in ("completion_tokens_details", "output_tokens_details"):
                details = reported_usage.get(details_key)
                if isinstance(details, dict):
                    reasoning_sources[details_key + ".reasoning_tokens"] = details.get("reasoning_tokens")
            reasoning_sources = {key: value for key, value in reasoning_sources.items() if value is not None}
            if len(set(reasoning_sources.values())) > 1:
                warnings.append({"kind": "conflicting_provider_reasoning_counts", "request_id": request_id,
                                 "sources": reasoning_sources, "aggregation_policy": "top_level_then_completion_details_then_output_details"})
        fixed_config = {key: value for key, value in payload.items() if key not in {"messages", "tool_choice"}}
        if raw["client_id"] in client_request_configs:
            require(client_request_configs[raw["client_id"]] == fixed_config, label + ": client schema/generation configuration changed")
        client_request_configs[raw["client_id"]] = fixed_config
        require(raw["endpoint"] == settings["base_url"].rstrip("/") + "/chat/completions", label + ": endpoint differs")
        for field in ("model", "temperature", "max_tokens", "reasoning_effort", "chat_template_kwargs"):
            require(payload.get(field) == settings[field], label + ": generation setting differs: " + field)
        require(payload.get("top_p") == 1.0 and "top_k" not in payload, label + ": effective legacy sampling differs")
        require(payload.get("parallel_tool_calls") is False and bool(payload.get("tools")), label + ": native schema/parallel policy differs")
        require(payload.get("tool_choice") in ("auto", "none"), label + ": unexpected tool choice")
        require(not any(key.lower().replace("-", "_") in {"authorization", "api_key", "headers", "extra_headers"}
                        for key in set(raw) | set(payload)), label + ": unexpected credential/header field")
        raw_by_request[request_id] = (path, raw)
        raw_by_client[raw["client_id"]].append((path, raw))

    used_clients, used_requests, used_generations = set(), set(), set()
    trace_rows, all_attempt_usage, all_success_usage = [], [], []
    for job in jobs:
        directory = Path(job["output_dir"]).resolve()
        require(root in directory.parents, job["id"] + ": artifact root outside run")
        paths = (sorted(directory.glob("*/traces-v2/*.json")) if job["system"] == "expgym"
                 else sorted(directory.glob("*/agents/agent_*.json")))
        require(len(paths) == job["expected_traces"], job["id"] + ": expected trace count differs")
        for path in paths:
            trace = read(path)
            label = str(path.relative_to(root))
            v2 = job["system"] == "expgym"
            metadata = trace["run"]["api_dump"] if v2 else trace["api_dump"]
            client_id = metadata["client_id"]
            require(client_id not in used_clients and metadata["run_id"] == expected_run,
                    label + ": duplicate client/cross-run identity")
            used_clients.add(client_id)
            expected_count = trace["outcome"]["http_request_attempts"] if v2 else trace["http_request_attempts"]
            require(len(raw_by_client[client_id]) == expected_count, label + ": raw/trace attempt counts differ")
            if v2:
                calls = [{"index": index, "attempts": call["attempt_usage"], "v2": call}
                         for index, call in enumerate(trace["llm_calls"], 1)]
            else:
                calls = [{"index": item["llm_call_index"], "attempts": item["attempts"]} for item in trace["usage_attempts"]]
                require(len(calls) == trace["api_calls"], label + ": generation count differs")
                assistant_positions = [index for index, m in enumerate(trace["messages"]) if m.get("role") == "assistant"]
                require(len(assistant_positions) == len(calls), label + ": assistant delivery count differs")
            require([c["index"] for c in calls] == list(range(1, len(calls) + 1)), label + ": noncontiguous call indices")
            require(len(calls) <= 31 and expected_count <= 93, label + ": fixed 30-step generation/attempt bound exceeded")
            trace_attempts, successes, finishes = [], [], Counter()
            delivered_assistants, previous_prefix = [], []
            reasoning_nonempty, max_input_estimate = 0, 0
            for call in calls:
                attempts = call["attempts"]
                call_label = label + ": call " + str(call["index"])
                require(bool(attempts), call_label + ": empty attempt list")
                require([a["attempt"] for a in attempts] == list(range(1, len(attempts) + 1)), call_label + ": noncontiguous attempts")
                generations = {a["generation_id"] for a in attempts}
                require(len(generations) == 1 and not (generations & used_generations), call_label + ": generation collision")
                used_generations.update(generations)
                original_request = None
                for number, attempt in enumerate(attempts):
                    request_id = attempt["request_id"]
                    require(request_id not in used_requests, call_label + ": attempt reused")
                    used_requests.add(request_id)
                    raw_path, raw = raw_by_request[request_id]
                    require(raw_path.parent.name == job["id"] and raw["client_id"] == client_id, call_label + ": attempt job/client differs")
                    for field in ("request_id", "generation_id", "attempt", "state", "http_status"):
                        require(raw.get(field) == attempt.get(field), call_label + ": attempt metadata differs: " + field)
                    require(provider_usage(raw) == attempt.get("usage"), call_label + ": provider usage not preserved exactly")
                    for field, value in usage_values(attempt.get("usage")).items():
                        require(value is None or (type(value) is int and value >= 0), call_label + ": invalid usage: " + field)
                    values = usage_values(attempt.get("usage"))
                    if all(values[f] is not None for f in ("input_tokens", "output_tokens", "provider_total_tokens")):
                        require(values["input_tokens"] + values["output_tokens"] == values["provider_total_tokens"], call_label + ": provider token total differs")
                    trace_attempts.append(attempt.get("usage"))
                    payload = raw["request_payload"]
                    if original_request is None:
                        original_request = payload
                    require(payload == original_request, call_label + ": retry request changed")
                    if number < len(attempts) - 1:
                        require(raw["state"] == "error" and raw["will_retry"] is True, call_label + ": delivered/malformed decision resampled")
                    else:
                        require(raw["state"] == "success" and raw["will_retry"] is False, call_label + ": missing final delivery")
                response = raw["response_json"]
                input_estimate = sum(len(json.dumps(m, ensure_ascii=False, allow_nan=False)) for m in payload["messages"]) // 3
                input_estimate += len(json.dumps(payload["tools"], ensure_ascii=False, allow_nan=False)) // 3
                max_input_estimate = max(max_input_estimate, input_estimate)
                message = copy.deepcopy(response["choices"][0]["message"])
                message.setdefault("role", "assistant")
                require(ordered_native_history(payload["messages"], delivered_assistants, previous_prefix),
                        call_label + ": complete ordered native history/preserved tool feedback differs")
                delivered_assistants.append(copy.deepcopy(message))
                previous_prefix = copy.deepcopy(payload["messages"]) + [copy.deepcopy(message)]
                finish = response["choices"][0].get("finish_reason")
                finishes[finish] += 1
                reasoning_nonempty += bool(message.get("reasoning_content"))
                successes.append(attempts[-1].get("usage"))
                seed = trace["run"]["seed"] if v2 else trace["seed"]
                require(payload.get("seed") == seed, call_label + ": requested seed differs")
                if v2:
                    saved = call["v2"]
                    require(saved["request_attempts"] == len(attempts), call_label + ": v2 attempt count differs")
                    require(saved.get("output_message") == message, call_label + ": complete assistant output differs")
                    require(materialize(trace, saved["output_message_id"]) == message, call_label + ": stored assistant differs")
                    require([materialize(trace, identifier) for identifier in saved["input_message_ids"]] == payload["messages"], call_label + ": actual wire input differs")
                    require(saved.get("finish_reason") == finish, call_label + ": finish reason differs")
                    require(payload["tool_choice"] == ("none" if saved["forced"] else "auto"), call_label + ": forced tool choice differs")
                    values = usage_values(successes[-1])
                    expected_usage = {"input_tokens": values["input_tokens"], "output_tokens": values["output_tokens"],
                                      "cache": {"reported": values["cache_read_tokens"] is not None or values["cache_write_tokens"] is not None,
                                                "read_tokens": values["cache_read_tokens"], "write_tokens": values["cache_write_tokens"]}}
                    require(saved["usage"] == expected_usage, call_label + ": v2 normalized usage differs")
                else:
                    position = assistant_positions[call["index"] - 1]
                    require(trace["messages"][position] == message, call_label + ": complete assistant output differs")
                    require(trace["messages"][:position] == payload["messages"], call_label + ": full wire input differs (inspect trim/augmentation)")
            delivered = total_usage(successes)
            if not v2:
                for legacy, metric in (("prompt_tokens", "input_tokens"), ("completion_tokens", "output_tokens"),
                                       ("cached_prompt_tokens", "cache_read_tokens")):
                    require(trace[legacy] == delivered[metric]["known_sum"], label + ": legacy delivered counter differs: " + legacy)
            require(len(trace_attempts) == expected_count, label + ": flattened attempt count differs")
            all_attempt_usage.extend(trace_attempts)
            all_success_usage.extend(successes)
            trace_rows.append({"path": str(path), "job_id": job["id"], "client_id": client_id,
                               "generations": len(calls), "attempts": len(trace_attempts), "finish_reasons": dict(finishes),
                               "reasoning_content_nonempty": reasoning_nonempty,
                               "max_runner_estimated_input_tokens_including_schema": max_input_estimate,
                               "protocol_failure_count": len((trace["outcome"] if v2 else trace).get("protocol_failures", [])),
                               "all_attempt_usage": total_usage(trace_attempts), "delivered_usage": delivered})

    require(used_clients == set(raw_by_client), "Raw clients do not exactly match persisted traces; preserve orphan/error evidence")
    require(used_requests == set(raw_by_request), "Raw attempts do not exactly match persisted ledgers")
    require(len(trace_rows) == 21, "Final persisted trace count differs from 21")
    require(strict_dump_inventory(run_dir) == dump_paths, "Dump inventory changed during audit")
    for record in list(files.values()):
        path = Path(record["path"])
        current = path.stat()
        require(current.st_mtime_ns == record["mtime_ns"] and current.st_size == record["bytes"]
                and hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], str(path) + ": changed during audit")
    return {"audit_kind": "post-drain independent read-only attempt and usage analysis",
            "run_directory": str(root), "manifest_sha256": files[str(root / "manifest.json")]["sha256"],
            "execution_sha256": files[str(root / "execution.json")]["sha256"],
            "passed": not errors, "errors": errors, "warnings": warnings, "scores_selected_or_recomputed": False,
            "model_or_network_calls": 0, "trace_count": len(trace_rows), "client_count": len(used_clients),
            "generation_count": len(used_generations), "attempt_count": len(used_requests), "dump_states": dict(states),
            "raw_attempt_count": len(raw_by_request), "raw_client_count": len(raw_by_client),
            "http_status_counts": dict(http_statuses), "success_http_status_unknown_count": success_http_status_unknown,
            "orphan_request_ids": sorted(set(raw_by_request) - used_requests),
            "all_attempt_usage": total_usage(all_attempt_usage), "delivered_usage": total_usage(all_success_usage),
            "trace_rows": trace_rows, "file_hashes": sorted(files.values(), key=lambda r: r["path"]),
            "limitations": ["No score recomputation; separately audited by the coordinator.",
                            "Success dump http_status=null is unknown, not a verified HTTP 200 status.",
                            "Provider cache null remains unknown; legacy cached_prompt_tokens=0 is not proof of zero cache.",
                            "Reasoning counts are provider-reported, not independently metered.",
                            "Pool input verification uses exact stored-history prefixes. This auditor does not reconstruct effective context trimming; future trimmed runs can be checked using the frozen deterministic trim function and recorded context/schema limits.",
                            "response_raw is a decoded/redacted client artifact, not a packet capture.",
                            "No independent verification of seed stochastic control."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--output-json", type=Path,
                        help="Optional new, single-use analysis artifact; refuses overwrite")
    args = parser.parse_args()
    if args.output_json is not None and args.output_json.exists():
        raise FileExistsError("Analysis output already exists")
    if args.output_json is not None and args.output_json.resolve().is_relative_to(args.run_dir.resolve()):
        raise ValueError("Independent analysis must be written outside the original run")
    result = audit(args.run_dir, args.authorization)
    result["auditor_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.output_json is not None:
        with args.output_json.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    if args.summary_only:
        result = {key: value for key, value in result.items() if key not in {"trace_rows", "file_hashes"}}
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
