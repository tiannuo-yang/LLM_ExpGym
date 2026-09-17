"""Versioned, normalized ExpGym trace artifacts.

Trace v2 stores each message once. LLM and tool calls reference message IDs,
while summaries such as token totals and printable steps are derived by readers.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

try:  # Python 3.7 is required by the pinned HPOBench container.
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - exercised only in the HPOBench image
    import importlib_metadata  # type: ignore[no-redef]


TRACE_SCHEMA_NAME = "expgym.trace"
TRACE_SCHEMA_VERSION = "2.0.0"


def _sha256_file(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=4)
def _source_files(repo_root: Path) -> Tuple[Path, ...]:
    source_paths: List[Path] = []
    for directory in ("expgym", "scripts", "schemas", "tests"):
        root = repo_root / directory
        if root.is_dir():
            source_paths.extend(
                path
                for path in root.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix.lower()
                in {".py", ".sh", ".json", ".yaml", ".yml", ".md"}
            )
    entrypoint = repo_root / "demo_experiment.py"
    if entrypoint.is_file():
        source_paths.append(entrypoint)
    return tuple(sorted(source_paths))


@lru_cache(maxsize=4)
def source_tree_sha256(repo_root: Path) -> str:
    """Hash runtime, scripts, schemas, and tests for resume/provenance checks."""
    source_digest = hashlib.sha256()
    for path in _source_files(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        source_digest.update(relative.encode("utf-8"))
        source_digest.update(b"\0")
        source_digest.update(path.read_bytes())
        source_digest.update(b"\0")
    return source_digest.hexdigest()


def _git_provenance(repo_root: Path) -> Dict[str, object]:
    def run(*args: str) -> str:
        try:
            return subprocess.check_output(
                ["git", *args], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return ""

    commit = run("rev-parse", "HEAD") or None
    try:
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain=v1"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        status_output = ""
    status_lines = [line for line in status_output.splitlines() if line]
    diff = run("diff", "--binary", "HEAD")
    return {
        "commit": commit,
        "dirty": bool(status_lines),
        "changed_files": [line[3:] for line in status_lines],
        "tracked_diff_sha256": (
            hashlib.sha256(diff.encode("utf-8")).hexdigest() if diff else None
        ),
        "source_tree_sha256": source_tree_sha256(repo_root),
        "source_file_count": len(_source_files(repo_root)),
    }


def _environment_provenance() -> Dict[str, object]:
    packages: Dict[str, Optional[str]] = {}
    for name in ("openai", "numpy", "pyyaml", "huggingface-hub", "pyarrow"):
        try:
            packages[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
    }


def _task_metadata(job: Dict[str, object], repo_root: Path) -> Dict[str, object]:
    scenario = str(job["scenario"])
    task: Dict[str, object] = {
        "scenario": scenario,
        "rep": int(job.get("rep", 0)),
    }
    if scenario == "tuning":
        name = str(job.get("tuning_task", "neural_network_training"))
        task["item"] = {"kind": "tuning_task", "id": name}
        task["dataset"] = {
            "name": "builtin" if name == "neural_network_training" else "hpobench",
            "revision": "repository-source",
        }
    elif scenario == "restricted_search":
        source = str(job.get("data_source") or "phantom_seed1")
        task["item"] = {
            "kind": "question",
            "id": int(job.get("question_index", 0)),
            "source": source,
        }
        task["dataset"] = {
            "name": "phantom-wiki-v1",
            "revision": "9369f9c64655f4e8146afee75ae5d3e3a95d7df5",
        }
    else:
        split = str(job.get("cc_split", "cc-large"))
        task["item"] = {
            "kind": "document",
            "id": int(job.get("question_index", 0)),
            "split": split,
        }
        data_dir = repo_root / "data" / "contract-nli"
        task["dataset"] = {
            "name": "contract-nli",
            "revision": {
                "test_segments_sha256": _sha256_file(data_dir / "test_segments.json"),
                "hints_sha256": _sha256_file(data_dir / "test_nda_span_dims.json"),
            },
        }
    hypothesis_order = job.get("hypothesis_order")
    if hypothesis_order is not None:
        task["hypothesis_order"] = hypothesis_order
    return task


def _message_key(message: Dict[str, Any]) -> str:
    """Intern the complete wire object, not just its visible text."""
    if not isinstance(message, dict):
        raise ValueError("Wire message must be an object")
    return json.dumps(message, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _message_record(message: Dict[str, Any], message_id: str) -> Dict[str, Any]:
    if not isinstance(message, dict):
        raise ValueError("Wire message must be an object")
    if {"id", "request_only", "content_ref"} & set(message):
        raise ValueError("Wire message conflicts with normalized trace metadata")
    return dict(copy.deepcopy(message), id=message_id)


def _map_input_messages(
    input_messages: Iterable[Dict[str, Any]],
    history: List[Dict[str, Any]],
    message_records: List[Dict[str, object]],
) -> List[str]:
    """Map a request snapshot to history IDs, interning trimmed request-only messages."""
    refs: List[str] = []
    search_from = 0
    for message in input_messages:
        key = _message_key(message)
        match: Optional[int] = None
        for index in range(search_from, len(history)):
            if _message_key(history[index]) == key:
                match = index
                break
        if match is not None:
            refs.append(f"m{match + 1:04d}")
            search_from = match + 1
            continue
        message_id = f"x{sum(str(record['id']).startswith('x') for record in message_records) + 1:04d}"
        record = _message_record(message, message_id)
        record["request_only"] = True
        message_records.append(record)
        refs.append(message_id)
    return refs


def _termination_code(reason: Optional[str], aborted: bool) -> str:
    if not aborted:
        return "natural_answer"
    mapping = {
        "Time budget exceeded": "time_budget_exceeded",
        "Maximum evaluations reached": "max_evaluations_reached",
        "Maximum steps reached": "max_steps_reached",
        "Prompt token budget exceeded": "prompt_token_budget_exceeded",
        "Context token budget exceeded": "context_token_budget_exceeded",
        "LLM returned empty response": "empty_model_response",
        "Missing Action directive": "missing_action",
    }
    if reason in mapping:
        return mapping[reason]
    if reason and reason.startswith("Unknown tool"):
        return "unknown_tool"
    return "aborted"


def build_trace_v2(result: Dict[str, Any], *, repo_root: Path) -> Dict[str, object]:
    """Normalize an internal loop result into the public v2 artifact."""
    if not isinstance(result, dict):
        raise ValueError("Trace v2 result must be an object")
    capture = result.get("_trace_v2_capture")
    runtime = result.get("_trace_v2_runtime")
    if not isinstance(capture, dict) or not isinstance(runtime, dict):
        raise ValueError("Trace v2 capture/runtime metadata is missing")
    if not isinstance(result.get("messages"), list) or not isinstance(result.get("job"), dict):
        raise ValueError("Trace v2 history/job must be an array/object")
    if not isinstance(result.get("score_check"), dict) or type(result.get("aborted")) is not bool:
        raise ValueError("Trace v2 score_check/aborted must be an object/boolean")
    if result.get("answer_metrics") is not None and not isinstance(result["answer_metrics"], dict):
        raise ValueError("Trace v2 answer_metrics must be an object or null")
    for field in ("llm_calls", "tool_calls"):
        if not isinstance(capture.get(field), list) or not all(isinstance(item, dict) for item in capture[field]):
            raise ValueError("Trace v2 capture " + field + " must be an array of objects")
    capture, runtime = copy.deepcopy(capture), copy.deepcopy(runtime)

    history: List[Dict[str, Any]] = copy.deepcopy(result["messages"])
    captured_tools: List[Dict[str, object]] = list(capture.get("tool_calls") or [])
    tool_by_message: Dict[int, str] = {}
    for index, tool in enumerate(captured_tools, start=1):
        result_index = tool.get("result_message_index")
        if isinstance(result_index, int):
            tool_by_message[result_index] = f"tool{index:04d}"

    messages: List[Dict[str, object]] = []
    for index, message in enumerate(history):
        record = _message_record(message, f"m{index + 1:04d}")
        tool_id = tool_by_message.get(index)
        # Graph injection may have augmented the stored observation. A content
        # reference is lossless only when the actual wire text is identical.
        if (tool_id is not None and "observation" in captured_tools[int(tool_id[4:]) - 1]
                and message.get("content") == captured_tools[int(tool_id[4:]) - 1]["observation"]):
            record.pop("content")
            record["content_ref"] = {
                "kind": "tool_observation",
                "tool_call_id": tool_id,
            }
        messages.append(record)

    llm_calls: List[Dict[str, object]] = []
    for index, captured in enumerate(capture.get("llm_calls") or [], start=1):
        if not isinstance(captured.get("input_messages"), list):
            raise ValueError("Trace v2 captured input_messages must be an array")
        call: Dict[str, object] = {
            "id": f"llm{index:04d}",
            "input_message_ids": _map_input_messages(
                captured.get("input_messages") or [], history, messages
            ),
            "output_message_id": None,
            "forced": captured.get("forced"),
            "latency_seconds": captured.get("latency_seconds"),
            "request_attempts": captured.get("request_attempts", 1),
            "usage": captured.get("usage") or {},
        }
        output_index = captured.get("output_message_index")
        if isinstance(output_index, int):
            call["output_message_id"] = f"m{output_index + 1:04d}"
        if "raw_output" in captured:
            call["raw_output"] = captured["raw_output"]
        for optional in ("output_message", "finish_reason", "attempt_usage"):
            if optional in captured:
                call[optional] = copy.deepcopy(captured[optional])
        llm_calls.append(call)

    tool_calls: List[Dict[str, object]] = []
    for index, captured in enumerate(captured_tools, start=1):
        request_index = int(captured["request_message_index"])
        result_index = captured.get("result_message_index")
        tool: Dict[str, object] = {
            "id": f"tool{index:04d}",
            "request_message_id": f"m{request_index + 1:04d}",
            "result_message_id": (
                f"m{int(result_index) + 1:04d}" if isinstance(result_index, int) else None
            ),
            "name": captured["name"],
            "arguments": captured["arguments"],
            "performance": captured.get("performance"),
            "simulated_cost_seconds": captured["simulated_cost_seconds"],
            "visible_to_model": captured["visible_to_model"],
        }
        for optional in ("observation", "withheld_result", "structured_result", "response_kind",
                         "raw_arguments", "canonical_argument", "included_in_eval_records", "tool_result"):
            if optional in captured:
                tool[optional] = copy.deepcopy(captured[optional])
        tool_calls.append(tool)

    output_message_ids = [
        str(call["output_message_id"])
        for call in llm_calls
        if call.get("output_message_id") is not None
    ]
    answer_message_id = output_message_ids[-1] if output_message_ids else None
    score: Dict[str, object]
    if isinstance(result.get("answer_metrics"), dict):
        score = {
            "metrics": copy.deepcopy(result["answer_metrics"]),
            "primary_metric": "label_acc",
        }
    else:
        score = {"value": result.get("answer_perf")}

    answer_source = result.get("answer_source", capture.get("answer_source"))
    score_source = result.get("answer_score_source")
    if score_source == "offline_final_answer":
        score_cost_basis = "offline_final_answer"
    elif score_source == "offline_empty_prediction":
        score_cost_basis = "total_simulated_cost"
    elif score_source == "answer_evaluator":
        score_cost_basis = "total_simulated_cost"
    else:
        score_cost_basis = ("total_simulated_cost"
                            if result.get("answer_metrics") is not None or not result.get("eval_records")
                            else "matching_tool_call")
    outcome: Dict[str, object] = {
        "status": "terminated" if result.get("aborted") else "completed",
        "termination_reason": _termination_code(
            capture.get("termination_reason"), bool(result.get("aborted"))
        ),
        "answer_source": answer_source,
        # Store the evaluated final answer explicitly: native final answers must
        # not be reconstructed later by reparsing assistant prose.
        "answer": copy.deepcopy(result.get("answer")),
        "answer_overhead": result.get("answer_overhead"),
        "answer_message_id": answer_message_id,
        "score": score,
        "score_cost_basis": score_cost_basis,
        "validation": {
            "passed": result["score_check"].get("ok"),
            "method": "repository_score_recompute",
        },
    }
    if score_source is not None:
        outcome["answer_score_source"] = score_source
    for optional in ("tool_protocol", "tuning_final_policy", "protocol_failures", "protocol_retries", "agent_steps", "http_request_attempts"):
        if optional in result:
            outcome[optional] = copy.deepcopy(result[optional])
    if result.get("missing_final_policy") == "task-abstention-v1":
        for field in ("missing_final_policy", "terminal_origin", "terminal_scenario", "scoring_input", "score_status", "terminal_status"):
            outcome[field] = copy.deepcopy(result[field])
        if result["terminal_status"]["score_complete"] is False:
            outcome["validation"]["method"] = "explicit_model_terminal_unscored"
            outcome["score_cost_basis"] = "unscored_terminal"
    if answer_source == "best_evaluated_fallback":
        outcome["answer_override"] = result.get("answer")

    cost = result.get("cost_regime_resolved") or {}
    task = _task_metadata(copy.deepcopy(result["job"]), repo_root)
    task["budget"] = {
        "regime": result["job"].get("cost_regime"),
        "mode": cost.get("mode"),
        "base_cost_seconds": cost.get("c_base"),
        "limit_seconds": cost.get("time_budget"),
    }
    task["limits"] = runtime.get("limits") or {}

    trace: Dict[str, object] = {
        "schema": {"name": TRACE_SCHEMA_NAME, "version": "2.1.0" if result.get("missing_final_policy") == "task-abstention-v1" else TRACE_SCHEMA_VERSION},
        "trace_id": str(uuid4()),
        "provenance": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "repository": _git_provenance(repo_root),
            "environment": _environment_provenance(),
            "runner": "scripts/run_paper_sweep.py",
        },
        "run": runtime.get("run") or {},
        "task": task,
        "messages": messages,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "outcome": outcome,
        "timing": {"wall_time_seconds": result.get("wall_time_seconds")},
    }
    for source, target in (("total_overhead", "total_simulated_cost_seconds"),
                           ("llm_time", "llm_latency_seconds"), ("eval_time", "tool_simulated_cost_seconds")):
        if source in result:
            trace["timing"][target] = result[source]
    validate_trace_v2(trace)
    return trace


def _schema_errors(value: Any, rule: Dict[str, Any], schema: Dict[str, Any], path: str) -> List[str]:
    """Evaluate the small, explicit JSON Schema vocabulary used by our schema.

    Avoid a new dependency in the Python 3.7 HPO runtime. Unsupported keywords
    fail closed, so extending the schema cannot silently weaken validation.
    This is not intended as a general JSON Schema implementation.
    """
    supported = {"$schema", "$id", "$defs", "$ref", "title", "description", "type", "const",
                 "enum", "required", "properties", "additionalProperties", "items", "oneOf",
                 "anyOf", "allOf", "not", "minimum", "maximum", "minLength"}
    unknown = set(rule) - supported
    if unknown:
        raise ValueError("Unsupported trace schema keywords: " + str(sorted(unknown)))
    errors: List[str] = []
    if "$ref" in rule:
        ref = rule["$ref"]
        if not ref.startswith("#/$defs/") or ref[8:] not in schema["$defs"]:
            raise ValueError("Unsupported trace schema reference: " + ref)
        errors.extend(_schema_errors(value, schema["$defs"][ref[8:]], schema, path))
    types = rule.get("type")
    checks = {"object": isinstance(value, dict), "array": isinstance(value, list),
              "string": isinstance(value, str), "null": value is None, "boolean": type(value) is bool,
              "integer": isinstance(value, int) and not isinstance(value, bool),
              "number": ((isinstance(value, int) and not isinstance(value, bool))
                         or (isinstance(value, float) and math.isfinite(value)))}
    if types is not None and not any(checks[name] for name in ([types] if isinstance(types, str) else types)):
        return errors + [f"{path} must have type {types}"]
    if "const" in rule and (type(value) is not type(rule["const"]) or value != rule["const"]):
        errors.append(f"{path} must equal {rule['const']!r}")
    if "enum" in rule and not any(type(value) is type(option) and value == option for option in rule["enum"]):
        errors.append(f"{path} is outside the supported enum")
    for branch in rule.get("allOf", []):
        errors.extend(_schema_errors(value, branch, schema, path))
    for keyword in ("oneOf", "anyOf"):
        if keyword in rule:
            matches = sum(not _schema_errors(value, branch, schema, path) for branch in rule[keyword])
            if (keyword == "oneOf" and matches != 1) or (keyword == "anyOf" and matches == 0):
                errors.append(f"{path} does not satisfy {keyword}")
    if "not" in rule and not _schema_errors(value, rule["not"], schema, path):
        errors.append(f"{path} contains a forbidden field combination")
    if isinstance(value, dict):
        for field in rule.get("required", []):
            if field not in value:
                errors.append(f"{path} missing required field {field}")
        properties = rule.get("properties", {})
        for field, item in value.items():
            if field in properties:
                errors.extend(_schema_errors(item, properties[field], schema, f"{path}.{field}"))
            elif rule.get("additionalProperties") is False:
                errors.append(f"{path} has unexpected field {field}")
            elif isinstance(rule.get("additionalProperties"), dict):
                errors.extend(_schema_errors(item, rule["additionalProperties"], schema, f"{path}.{field}"))
    if isinstance(value, list) and "items" in rule:
        for index, item in enumerate(value):
            errors.extend(_schema_errors(item, rule["items"], schema, f"{path}[{index}]"))
    if isinstance(value, str) and len(value) < rule.get("minLength", 0):
        errors.append(f"{path} must be nonempty")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in rule and value < rule["minimum"]:
            errors.append(f"{path} is below its minimum")
        if "maximum" in rule and value > rule["maximum"]:
            errors.append(f"{path} exceeds its maximum")
    return errors


def _strict_json_errors(value: Any, path: str = "trace") -> List[str]:
    if value is None or isinstance(value, (str, bool, int)):
        return []
    if isinstance(value, float):
        return [] if math.isfinite(value) else [f"{path} is not finite"]
    if isinstance(value, list):
        return [error for index, item in enumerate(value)
                for error in _strict_json_errors(item, f"{path}[{index}]")]
    if isinstance(value, dict):
        return [error for key, item in value.items()
                for error in ([f"{path} has a non-string object key"] if not isinstance(key, str)
                              else _strict_json_errors(item, f"{path}.{key}"))]
    return [f"{path} is not a strict JSON value"]


def _id_map(records: Iterable[Dict[str, object]], label: str, errors: List[str]) -> Dict[str, Dict[str, object]]:
    result: Dict[str, Dict[str, object]] = {}
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"{label} record has no valid id")
        elif record_id in result:
            errors.append(f"duplicate {label} id: {record_id}")
        else:
            result[record_id] = record
    return result


def validate_trace_v2(trace: Dict[str, object]) -> None:
    """Validate strict artifact shape and references; this does not rescore it."""
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "trace-v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        errors = _strict_json_errors(trace)
        errors.extend(_schema_errors(trace, schema, schema, "trace"))
    except (RecursionError, OverflowError) as exc:
        raise ValueError("Invalid ExpGym trace v2: non-JSON recursion/numeric representation") from exc
    # No cross-reference code may dereference unvalidated containers or IDs.
    if errors:
        raise ValueError("Invalid ExpGym trace v2:\n- " + "\n- ".join(errors))
    messages, llm_calls, tool_calls = trace["messages"], trace["llm_calls"], trace["tool_calls"]
    message_map = _id_map(messages, "message", errors)
    llm_map = _id_map(llm_calls, "llm call", errors)
    tool_map = _id_map(tool_calls, "tool call", errors)

    for message_id, message in message_map.items():
        ref = message.get("content_ref")
        if ref is not None:
            tool = tool_map.get(ref["tool_call_id"])
            if tool is None:
                errors.append(f"{message_id} references unknown tool call")
            elif "observation" not in tool or tool.get("result_message_id") != message_id:
                errors.append(f"{message_id} content_ref does not identify its recorded observation")
    for call_id, call in llm_map.items():
        for message_id in call.get("input_message_ids") or []:
            if message_id not in message_map:
                errors.append(f"{call_id} references unknown input message {message_id}")
        output_id = call.get("output_message_id")
        if output_id is not None and output_id not in message_map:
            errors.append(f"{call_id} references unknown output message {output_id}")
        elif output_id is not None and message_map[output_id]["role"] != "assistant":
            errors.append(f"{call_id} output message must be assistant")
        if "output_message" in call and call["output_message"]["role"] != "assistant":
            errors.append(f"{call_id} provider output_message must be assistant")
        cache = ((call.get("usage") or {}).get("cache") or {})
        if not cache.get("reported") and (
            cache.get("read_tokens") is not None or cache.get("write_tokens") is not None
        ):
            errors.append(f"{call_id} has cache tokens but reported=false")
        if "attempt_usage" in call:
            attempts = call["attempt_usage"]
            # [] explicitly means this backend supplied no per-attempt data
            # (e.g. FakeLLM), not zero HTTP attempts or zero token usage.
            if attempts and (len(attempts) != call["request_attempts"] or [item["attempt"] for item in attempts] != list(range(1, call["request_attempts"] + 1))):
                errors.append(f"{call_id} attempt_usage does not cover every request attempt in order")
    for tool_id, tool in tool_map.items():
        if tool.get("request_message_id") not in message_map:
            errors.append(f"{tool_id} references unknown request message")
        elif message_map[tool["request_message_id"]]["role"] != "assistant":
            errors.append(f"{tool_id} request message must be assistant")
        result_id = tool.get("result_message_id")
        if result_id is not None and result_id not in message_map:
            errors.append(f"{tool_id} references unknown result message")
        elif result_id is not None and message_map[result_id]["role"] not in ("user", "tool"):
            errors.append(f"{tool_id} result message must be user or tool")
        if tool["visible_to_model"] and result_id is None:
            errors.append(f"{tool_id} visibility/result reference mismatch")
        if not tool["visible_to_model"] and result_id is not None:
            if tool.get("response_kind") != "withheld_notice" or "observation" not in tool:
                errors.append(f"{tool_id} invisible result message requires an explicit withheld_notice")
            elif tool["observation"] not in (
                "Observation: [over-budget — result withheld. This evaluation reached or exceeded the time budget.]",
                "Observation: [over-budget — result withheld. This evaluation exceeded the time budget.]",
            ):
                errors.append(f"{tool_id} withheld_notice must contain only the fixed withheld observation")
            elif not errors and result_id in message_map and materialize_message(trace, result_id).get("content") != tool["observation"]:
                errors.append(f"{tool_id} withheld notice differs from recorded observation")
        if tool.get("included_in_eval_records") is True and (not tool["visible_to_model"] or tool["performance"] is None):
            errors.append(f"{tool_id} cannot include an unobserved/non-numeric evaluation")
    outcome = trace["outcome"]
    answer_id = outcome["answer_message_id"]
    if answer_id is not None and answer_id not in message_map:
        errors.append("outcome references unknown answer message")
    elif answer_id is not None and message_map[answer_id]["role"] != "assistant":
        errors.append("outcome answer message must be assistant")
    if outcome.get("answer_score_source") == "offline_final_answer" and outcome.get("score_cost_basis") == "matching_tool_call":
        errors.append("offline final answer must not claim matching_tool_call score cost basis")
    score = outcome["score"]
    policy_fields = {"missing_final_policy", "terminal_origin", "terminal_scenario", "scoring_input", "score_status", "terminal_status"}
    if trace["schema"]["version"] == "2.1.0":
        from expgym.missing_final import POLICY, terminal_publishable
        if not policy_fields.issubset(outcome) or outcome.get("terminal_scenario") != trace["task"].get("scenario"):
            errors.append("Explicit terminal trace requires policy fields and matching scenario")
        else:
            view = {key: copy.deepcopy(outcome[key]) for key in policy_fields}
            view.update(answer=outcome.get("answer"), answer_perf=(score["metrics"].get(score.get("primary_metric"))
                if isinstance(score.get("metrics"), dict) else score.get("value")), answer_metrics=score.get("metrics"))
            check = {"ok": outcome["validation"]["passed"]}
            if check["ok"] is False:
                check.update(reason="unscorable_missing_configuration", score_complete=False, policy_version=POLICY)
                if outcome["validation"]["method"] != "explicit_model_terminal_unscored":
                    errors.append("Unknown task score must not claim repository score acceptance")
                if outcome.get("score_cost_basis") != "unscored_terminal":
                    errors.append("Unknown task score requires unscored_terminal cost basis")
            elif outcome["validation"]["method"] != "repository_score_recompute":
                errors.append("Scored terminal requires repository recompute validation")
            if not terminal_publishable(view, check):
                errors.append("Terminal execution/score status is inconsistent")
            if outcome.get("answer") is None and check["ok"] is True and (
                    outcome.get("terminal_scenario") not in {"restricted_search", "evidence_audit"}
                    or outcome.get("scoring_input") != "" or outcome.get("score_status") != "scored_empty_prediction"
                    or outcome.get("answer_score_source") != "offline_empty_prediction"):
                errors.append("Missing final score requires explicit empty prediction policy")
    elif (policy_fields.intersection(outcome) or outcome["validation"]["passed"] is not True
          or outcome["validation"]["method"] != "repository_score_recompute"
          or outcome.get("answer_score_source") == "offline_empty_prediction"
          or outcome.get("score_cost_basis") == "unscored_terminal"):
        errors.append("Legacy v2.0 requires complete independent score acceptance and no new terminal policy")
    if "metrics" in score and (score["primary_metric"] not in score["metrics"] or score["metrics"][score["primary_metric"]] is None):
        errors.append("outcome primary_metric must identify a numeric score")
    if errors:
        raise ValueError("Invalid ExpGym trace v2:\n- " + "\n- ".join(errors))


def materialize_message(trace: Dict[str, object], message_id: str) -> Dict[str, Any]:
    """Resolve a message without coercing nulls or dropping native wire fields."""
    messages = {record["id"]: record for record in trace["messages"]}
    tools = {record["id"]: record for record in trace["tool_calls"]}
    record = messages[message_id]
    result = {key: copy.deepcopy(value) for key, value in record.items()
              if key not in {"id", "content_ref", "request_only"}}
    if "content_ref" in record:
        tool_id = record["content_ref"]["tool_call_id"]
        result["content"] = copy.deepcopy(tools[tool_id]["observation"])
    return result


def materialize_llm_input(trace: Dict[str, object], call_id: str) -> List[Dict[str, Any]]:
    calls = {record["id"]: record for record in trace["llm_calls"]}
    return [
        materialize_message(trace, message_id)
        for message_id in calls[call_id]["input_message_ids"]
    ]


def result_for_score_check(trace: Dict[str, object]) -> Dict[str, Any]:
    """Restore evaluator inputs, failing closed when old traces lost evidence.

    Reading an old v2 artifact remains supported. Restoring a score check is
    stricter: formatted observation prose cannot reconstruct a raw tool result.
    This function never invokes a model/tool or trusts validation.passed as a
    substitute for the caller's independent repository score recomputation.
    """
    validate_trace_v2(trace)
    outcome, score = trace["outcome"], trace["outcome"]["score"]
    if "total_simulated_cost_seconds" not in trace["timing"]:
        raise ValueError("Cannot restore exact cost without timing.total_simulated_cost_seconds")
    if "answer" in outcome:
        answer = copy.deepcopy(outcome["answer"])
    elif "answer_override" in outcome:
        answer = copy.deepcopy(outcome["answer_override"])
    else:
        protocol = (trace["run"].get("protocol") or {}).get("tool_protocol")
        native_messages = any(message.get("role") == "tool" or message.get("tool_calls") for message in trace["messages"])
        if outcome.get("tool_protocol") == "native" or protocol == "native" or native_messages:
            raise ValueError("Cannot restore native final answer without outcome.answer")
        message_id = outcome["answer_message_id"]
        content = materialize_message(trace, message_id).get("content") if message_id else None
        if not isinstance(content, str):
            raise ValueError("Cannot restore historical final answer")
        from expgym.react_loop import _extract_answer
        answer = _extract_answer(content) or content.strip()
    tool_records, eval_records = [], []
    for tool in trace["tool_calls"]:
        if "raw_arguments" not in tool or "tool_result" not in tool:
            raise ValueError("Cannot restore exact historical tool_records; raw_arguments/tool_result missing")
        argument, output = tool["raw_arguments"], copy.deepcopy(tool["tool_result"])
        tool_records.append((tool["name"], argument, output))
        if "included_in_eval_records" not in tool:
            raise ValueError("Cannot restore evaluation visibility without included_in_eval_records")
        if tool["included_in_eval_records"]:
            if "canonical_argument" not in tool:
                raise ValueError("Cannot restore evaluation without canonical_argument")
            eval_records.append((argument, tool["canonical_argument"], tool["performance"], tool["simulated_cost_seconds"]))
    metrics = copy.deepcopy(score.get("metrics"))
    result = {
        "answer": answer,
        "answer_perf": metrics[score["primary_metric"]] if metrics is not None else score.get("value"),
        "answer_metrics": metrics, "answer_overhead": outcome.get("answer_overhead"),
        "tool_records": tool_records, "eval_records": eval_records,
        "total_overhead": trace["timing"]["total_simulated_cost_seconds"],
        "evaluations": len(trace["tool_calls"]), "api_calls": len(trace["llm_calls"]),
        "aborted": outcome["status"] == "terminated", "termination_reason": outcome["termination_reason"],
        "answer_source": outcome["answer_source"], "answer_score_source": outcome.get("answer_score_source"),
        "messages": [materialize_message(trace, message["id"]) for message in trace["messages"] if not message.get("request_only")],
    }
    for field in ("tuning_final_policy", "missing_final_policy", "terminal_origin", "terminal_scenario",
                  "scoring_input", "score_status", "terminal_status"):
        if field in outcome:
            result[field] = copy.deepcopy(outcome[field])
    return result


def load_trace_v2(path: Path) -> Dict[str, object]:
    trace = json.loads(path.read_text(encoding="utf-8"))
    validate_trace_v2(trace)
    return trace


def write_trace_v2(path: Path, trace: Dict[str, object]) -> None:
    """Validate and atomically write a strict-JSON v2 artifact."""
    validate_trace_v2(trace)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            json.dump(trace, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise
