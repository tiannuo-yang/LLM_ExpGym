"""Versioned, normalized ExpGym trace artifacts.

Trace v2 stores each message once. LLM and tool calls reference message IDs,
while summaries such as token totals and printable steps are derived by readers.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4


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
    source_digest = hashlib.sha256()
    for path in sorted(source_paths):
        relative = path.relative_to(repo_root).as_posix()
        source_digest.update(relative.encode("utf-8"))
        source_digest.update(b"\0")
        source_digest.update(path.read_bytes())
        source_digest.update(b"\0")
    return {
        "commit": commit,
        "dirty": bool(status_lines),
        "changed_files": [line[3:] for line in status_lines],
        "tracked_diff_sha256": (
            hashlib.sha256(diff.encode("utf-8")).hexdigest() if diff else None
        ),
        "source_tree_sha256": source_digest.hexdigest(),
        "source_file_count": len(source_paths),
    }


def _environment_provenance() -> Dict[str, object]:
    packages: Dict[str, Optional[str]] = {}
    for name in ("openai", "numpy", "pyyaml", "huggingface-hub", "pyarrow"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
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


def _message_key(message: Dict[str, str]) -> Tuple[str, str]:
    return str(message.get("role", "")), str(message.get("content", ""))


def _map_input_messages(
    input_messages: Iterable[Dict[str, str]],
    history: List[Dict[str, str]],
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
        message_records.append(
            {
                "id": message_id,
                "role": key[0],
                "content": key[1],
                "request_only": True,
            }
        )
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
    capture = result.get("_trace_v2_capture")
    runtime = result.get("_trace_v2_runtime")
    if not isinstance(capture, dict) or not isinstance(runtime, dict):
        raise ValueError("Trace v2 capture/runtime metadata is missing")

    history: List[Dict[str, str]] = list(result["messages"])
    captured_tools: List[Dict[str, object]] = list(capture.get("tool_calls") or [])
    tool_by_message: Dict[int, str] = {}
    for index, tool in enumerate(captured_tools, start=1):
        result_index = tool.get("result_message_index")
        if isinstance(result_index, int):
            tool_by_message[result_index] = f"tool{index:04d}"

    messages: List[Dict[str, object]] = []
    for index, message in enumerate(history):
        record: Dict[str, object] = {
            "id": f"m{index + 1:04d}",
            "role": message["role"],
        }
        tool_id = tool_by_message.get(index)
        if tool_id is not None:
            record["content_ref"] = {
                "kind": "tool_observation",
                "tool_call_id": tool_id,
            }
        else:
            record["content"] = message["content"]
        messages.append(record)

    llm_calls: List[Dict[str, object]] = []
    for index, captured in enumerate(capture.get("llm_calls") or [], start=1):
        call: Dict[str, object] = {
            "id": f"llm{index:04d}",
            "input_message_ids": _map_input_messages(
                captured.get("input_messages") or [], history, messages
            ),
            "output_message_id": None,
            "forced": bool(captured.get("forced")),
            "latency_seconds": captured.get("latency_seconds"),
            "request_attempts": captured.get("request_attempts", 1),
            "usage": captured.get("usage") or {},
        }
        output_index = captured.get("output_message_index")
        if isinstance(output_index, int):
            call["output_message_id"] = f"m{output_index + 1:04d}"
        if "raw_output" in captured:
            call["raw_output"] = captured["raw_output"]
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
        for optional in ("observation", "withheld_result", "structured_result"):
            if optional in captured:
                tool[optional] = captured[optional]
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
            "metrics": result["answer_metrics"],
            "primary_metric": "label_acc",
        }
    else:
        score = {"value": result.get("answer_perf")}

    answer_source = capture.get("answer_source")
    outcome: Dict[str, object] = {
        "status": "terminated" if result.get("aborted") else "completed",
        "termination_reason": _termination_code(
            capture.get("termination_reason"), bool(result.get("aborted"))
        ),
        "answer_source": answer_source,
        "answer_message_id": answer_message_id,
        "score": score,
        "score_cost_basis": (
            "total_simulated_cost"
            if result.get("answer_metrics") is not None or not result.get("eval_records")
            else "matching_tool_call"
        ),
        "validation": {
            "passed": bool((result.get("score_check") or {}).get("ok")),
            "method": "repository_score_recompute",
        },
    }
    if answer_source == "best_evaluated_fallback":
        outcome["answer_override"] = result.get("answer")

    cost = result.get("cost_regime_resolved") or {}
    task = _task_metadata(result["job"], repo_root)
    task["budget"] = {
        "regime": result["job"].get("cost_regime"),
        "mode": cost.get("mode"),
        "base_cost_seconds": cost.get("c_base"),
        "limit_seconds": cost.get("time_budget"),
    }
    task["limits"] = runtime.get("limits") or {}

    trace: Dict[str, object] = {
        "schema": {"name": TRACE_SCHEMA_NAME, "version": TRACE_SCHEMA_VERSION},
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
    validate_trace_v2(trace)
    return trace


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
    """Validate v2 shape and all cross-record references."""
    errors: List[str] = []
    required = {
        "schema", "trace_id", "provenance", "run", "task", "messages",
        "llm_calls", "tool_calls", "outcome", "timing",
    }
    legacy = {"steps", "tool_records", "eval_records", "answer", "score_check"}
    missing = required - set(trace)
    if missing:
        errors.append(f"missing root fields: {sorted(missing)}")
    present_legacy = legacy & set(trace)
    if present_legacy:
        errors.append(f"legacy duplicated fields are forbidden: {sorted(present_legacy)}")
    schema = trace.get("schema") or {}
    if not isinstance(schema, dict) or schema.get("name") != TRACE_SCHEMA_NAME or schema.get("version") != TRACE_SCHEMA_VERSION:
        errors.append("unsupported schema name/version")

    messages = trace.get("messages") if isinstance(trace.get("messages"), list) else []
    llm_calls = trace.get("llm_calls") if isinstance(trace.get("llm_calls"), list) else []
    tool_calls = trace.get("tool_calls") if isinstance(trace.get("tool_calls"), list) else []
    message_map = _id_map(messages, "message", errors)
    llm_map = _id_map(llm_calls, "llm call", errors)
    tool_map = _id_map(tool_calls, "tool call", errors)

    for message_id, message in message_map.items():
        has_content = "content" in message
        has_ref = "content_ref" in message
        if has_content == has_ref:
            errors.append(f"{message_id} must contain exactly one of content/content_ref")
        ref = message.get("content_ref")
        if isinstance(ref, dict) and ref.get("tool_call_id") not in tool_map:
            errors.append(f"{message_id} references unknown tool call")
    for call_id, call in llm_map.items():
        for message_id in call.get("input_message_ids") or []:
            if message_id not in message_map:
                errors.append(f"{call_id} references unknown input message {message_id}")
        output_id = call.get("output_message_id")
        if output_id is not None and output_id not in message_map:
            errors.append(f"{call_id} references unknown output message {output_id}")
        cache = ((call.get("usage") or {}).get("cache") or {})
        if not cache.get("reported") and (
            cache.get("read_tokens") is not None or cache.get("write_tokens") is not None
        ):
            errors.append(f"{call_id} has cache tokens but reported=false")
    for tool_id, tool in tool_map.items():
        if tool.get("request_message_id") not in message_map:
            errors.append(f"{tool_id} references unknown request message")
        result_id = tool.get("result_message_id")
        if result_id is not None and result_id not in message_map:
            errors.append(f"{tool_id} references unknown result message")
        if bool(tool.get("visible_to_model")) != (result_id is not None):
            errors.append(f"{tool_id} visibility/result reference mismatch")
    outcome = trace.get("outcome") or {}
    if isinstance(outcome, dict):
        answer_id = outcome.get("answer_message_id")
        if answer_id is not None and answer_id not in message_map:
            errors.append("outcome references unknown answer message")
        if not ((outcome.get("validation") or {}).get("passed")):
            errors.append("score validation did not pass")
    try:
        json.dumps(trace, allow_nan=False)
    except (TypeError, ValueError) as exc:
        errors.append(f"not strict JSON: {exc}")
    if errors:
        raise ValueError("Invalid ExpGym trace v2:\n- " + "\n- ".join(errors))


def materialize_message(trace: Dict[str, object], message_id: str) -> Dict[str, str]:
    """Resolve a normalized message into the exact role/content sent on the wire."""
    messages = {record["id"]: record for record in trace["messages"]}
    tools = {record["id"]: record for record in trace["tool_calls"]}
    record = messages[message_id]
    if "content" in record:
        content = record["content"]
    else:
        tool_id = record["content_ref"]["tool_call_id"]
        content = tools[tool_id]["observation"]
    return {"role": str(record["role"]), "content": str(content)}


def materialize_llm_input(trace: Dict[str, object], call_id: str) -> List[Dict[str, str]]:
    calls = {record["id"]: record for record in trace["llm_calls"]}
    return [
        materialize_message(trace, message_id)
        for message_id in calls[call_id]["input_message_ids"]
    ]


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
        temp_path.unlink(missing_ok=True)
        raise
