#!/usr/bin/env python3
"""Project one completed N1 Whois trace and every API attempt to public costs.

The output fields and scalar meanings match Whois ``inputs/agents.csv`` and
``inputs/attempts.csv``.  This module reads local files only, calls no model or
scorer, and never emits prompts, answers, reasoning, endpoints or headers.
Unknown usage remains None (an empty field when written by csv.DictWriter).
Reasoning tokens are a separate reported subset, never added to total tokens.

Source collection must independently verify queue completion and adoption.
``checks['ready_for_adoption']`` additionally requires an exact one-to-one
canonical attempt/API dump ledger, with no incomplete or orphan requests.
Orphan dumps are retained in the returned rows even when this gate is false.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any

TOKENS = ("input_tokens", "output_tokens", "total_tokens", "reasoning_tokens", "cached_input_tokens")
AGENT_FIELDS = ("model", "beta", "job_id", "data_source", "question_index", "repeat", "score_status", "missing_final", "protocol_failure_events", "evaluations", "simulated_feedback_seconds", "agent_wall_seconds", "http_request_attempts")
ATTEMPT_FIELDS = ("model", "beta", "job_id", "data_source", "question_index", "repeat", "request_id", "llm_call_index", "attempt", "state", "http_status") + TOKENS + ("dump_collection", "dump_member")


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _read(path: Path) -> tuple[dict, dict]:
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ino) ==
            (after.st_size, after.st_mtime_ns, after.st_ino), "source changed while reading")
    value = json.loads(raw)
    require(isinstance(value, dict), "source must be a JSON object")
    return value, dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def _number(value: Any, name: str) -> int | float | None:
    if value is None:
        return None
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0, "invalid nonnegative number: " + name)
    return value


def usage_fields(value: Any) -> dict:
    """Same provider-field precedence as the historical Whois exporter."""
    u = value if isinstance(value, dict) else {}
    details = u.get("input_tokens_details") or u.get("prompt_tokens_details") or {}
    output = u.get("output_tokens_details") or u.get("completion_tokens_details") or {}
    require(isinstance(details, dict) and isinstance(output, dict), "invalid token details")
    row = {
        "input_tokens": u.get("input_tokens", u.get("prompt_tokens")),
        "output_tokens": u.get("output_tokens", u.get("completion_tokens")),
        "total_tokens": u.get("total_tokens"),
        "reasoning_tokens": output.get("reasoning_tokens", u.get("reasoning_tokens")),
        "cached_input_tokens": details.get("cached_tokens", u.get("cache_read_input_tokens", u.get("cached_prompt_tokens"))),
    }
    return {k: _number(v, k) for k, v in row.items()}


def _dump_usage(dump: dict) -> Any:
    if isinstance(dump.get("usage"), dict):
        return dump["usage"]
    response = dump.get("response_json")
    if not isinstance(response, dict):
        raw = dump.get("response_raw")
        try:
            response = json.loads(raw) if isinstance(raw, str) else None
        except (ValueError, TypeError):
            response = None
    return response.get("usage") if isinstance(response, dict) else None


def derive_cost_rows(
    trace_path: str | Path,
    api_dump_root: str | Path,
    *,
    model: str,
    beta: int,
    job_id: str,
    data_source: str,
    question_index: int,
    dump_collection: str,
    dump_member_prefix: str | None = None,
    expected_trace_sha256: str | None = None,
) -> dict:
    """Return agent_row, attempt_rows and hash/coverage checks; write nothing.

    ``dump_member_prefix`` is a relative public provenance label; the default
    is ``invocations/<job_id>/api_dump``.  ``dump_collection`` names the root
    against which those labels resolve.  Neither grants access to raw files.
    The caller should include ``checks`` in its immutable collection receipt.
    """
    trace_path, api_dump_root = Path(trace_path), Path(api_dump_root)
    require(isinstance(beta, int) and not isinstance(beta, bool) and beta > 0, "integer beta required")
    require(isinstance(question_index, int) and question_index >= 0, "question index required")
    require(bool(model) and bool(dump_collection) and bool(data_source), "missing slot identity")
    require(re.fullmatch(r"[A-Za-z0-9_-]+", job_id), "unsafe job ID")
    prefix = PurePosixPath(dump_member_prefix or f"invocations/{job_id}/api_dump")
    require(not prefix.is_absolute() and ".." not in prefix.parts, "dump member prefix must be relative")
    trace, trace_identity = _read(trace_path)
    if expected_trace_sha256 is not None:
        require(trace_identity["sha256"] == expected_trace_sha256, "trace SHA mismatch")
    require(trace.get("schema", {}).get("name") == "expgym.trace" and
            trace["schema"].get("version") in {"2.0.0", "2.1.0"}, "canonical N1 trace required")
    task, run = trace["task"], trace["run"]
    require(task.get("scenario") == "restricted_search" and task.get("rep") == 0, "wrong scenario or repeat")
    require(task.get("item") == {"kind": "question", "id": question_index, "source": data_source}, "question identity mismatch")
    require(task.get("budget", {}).get("beta") == beta, "trace beta mismatch")
    require(run.get("api_dump", {}).get("run_id") == job_id, "trace run ID mismatch")
    model_id = run.get("model", {}).get("id")
    # Alias/model-ID equivalence is deliberately not guessed for unknown models.
    aliases = {"glm": "glm-5.3", "gpt": "gpt-5.6-sol", "kimi": "kimi-k3", "qwen": "qwen3.8-2.4t-a95b-fp8", "deepseek": "deepseek-v4-flash-0731", "gemini": "gemini-3.8-flash-medium"}
    require(model_id == aliases.get(model, model), "trace model mismatch")
    outcome = trace["outcome"]
    terminal = outcome.get("terminal_status", {})
    require(terminal.get("execution_complete") is True, "trace is not execution-complete")
    calls, tool_calls = trace.get("llm_calls"), trace.get("tool_calls")
    require(isinstance(calls, list) and isinstance(tool_calls, list), "canonical call ledgers required")
    failures = outcome.get("protocol_failures")
    require(failures is None or isinstance(failures, list), "invalid protocol-failure ledger")
    timing = trace.get("timing", {})
    dim = dict(model=model, beta=beta, job_id=job_id, data_source=data_source, question_index=question_index, repeat="R1")
    agent = {
        **dim,
        "score_status": outcome.get("score_status"),
        "missing_final": outcome.get("answer") is None or outcome.get("answer") == "",
        "protocol_failure_events": len(failures) if failures is not None else None,
        "evaluations": len(tool_calls),
        "simulated_feedback_seconds": _number(timing.get("total_simulated_cost_seconds"), "feedback seconds"),
        "agent_wall_seconds": _number(timing.get("wall_time_seconds"), "wall seconds"),
        "http_request_attempts": _number(outcome.get("http_request_attempts"), "attempt count"),
    }
    require(tuple(agent) == AGENT_FIELDS, "agent field order mismatch")
    saved = {}
    issues = []
    for index, call in enumerate(calls, 1):
        ledger = call.get("attempt_usage")
        if not isinstance(ledger, list):
            issues.append(dict(kind="missing_canonical_attempt_ledger", llm_call_index=index))
            continue
        if call.get("request_attempts") != len(ledger):
            issues.append(dict(kind="canonical_call_attempt_count_mismatch", llm_call_index=index))
        for ordinal, entry in enumerate(ledger, 1):
            rid = entry.get("request_id")
            require(isinstance(rid, str) and re.fullmatch(r"[A-Za-z0-9_-]+", rid), "unsafe request ID")
            require(rid not in saved, "duplicate canonical request ID")
            require(entry.get("attempt") == ordinal, "nonconsecutive canonical retries")
            saved[rid] = (index, entry)
    require(api_dump_root.is_dir() and not api_dump_root.is_symlink(), "missing or symlink dump directory")
    paths = sorted(api_dump_root.iterdir())
    require(all(p.is_file() and not p.is_symlink() and p.suffix == ".json" for p in paths), "unexpected API dump directory entry")
    actual, identities, attempts = set(), [], []
    for path in paths:
        dump, identity = _read(path)
        rid = dump.get("request_id")
        require(dump.get("schema_version") == "expgym.api_attempt.v1", "unknown API dump schema")
        require(rid == path.stem and rid not in actual, "API dump request identity mismatch")
        require(dump.get("run_id") == job_id and dump.get("client_id") == run["api_dump"].get("client_id"), "API dump invocation mismatch")
        context = dump.get("context", {}).get("job", {})
        require(context.get("scenario") == "restricted_search" and context.get("data_source") == data_source
                and context.get("question_index") == question_index and context.get("rep") == 0
                and context.get("beta") == beta and context.get("model_id") == model_id,
                "API dump slot mismatch")
        actual.add(rid)
        usage = usage_fields(_dump_usage(dump))
        if rid in saved:
            call_index, entry = saved[rid]
            for field in ("attempt", "state", "http_status", "generation_id"):
                require(entry.get(field) == dump.get(field), "canonical/API dump metadata mismatch: " + field)
            require(usage_fields(entry.get("usage")) == usage, "canonical/API dump token usage mismatch")
        else:
            call_index = None
            issues.append(dict(kind="orphan_API_dump", request_id=rid))
        if dump.get("state") not in {"success", "error"}:
            issues.append(dict(kind="incomplete_API_attempt", request_id=rid, state=dump.get("state")))
        member = str(prefix / path.name)
        attempts.append({**dim, "request_id": rid, "llm_call_index": call_index,
                         "attempt": dump.get("attempt"), "state": dump.get("state"),
                         "http_status": dump.get("http_status"), **usage,
                         "dump_collection": dump_collection, "dump_member": member})
        identities.append(dict(dump_collection=dump_collection, dump_member=member, request_id=rid, **identity))
    for rid in sorted(set(saved) - actual):
        # Keep the saved request in the full ledger even though raw provenance
        # is incomplete; callers must not adopt a failed coverage check.
        index, entry = saved[rid]
        issues.append(dict(kind="missing_API_dump", request_id=rid))
        attempts.append({**dim, "request_id": rid, "llm_call_index": index,
                         "attempt": entry.get("attempt"), "state": entry.get("state"),
                         "http_status": entry.get("http_status"), **usage_fields(entry.get("usage")),
                         "dump_collection": dump_collection, "dump_member": str(prefix / (rid + ".json"))})
    attempts.sort(key=lambda r: r["request_id"])
    require(all(tuple(row) == ATTEMPT_FIELDS for row in attempts), "attempt field order mismatch")
    if agent["http_request_attempts"] != len(attempts):
        issues.append(dict(kind="reported_vs_full_attempt_count_mismatch", reported=agent["http_request_attempts"], observed=len(attempts)))
    checks = dict(
        schema="expgym.whois-control-flow-cost-projection.v1",
        passed=not issues,
        ready_for_adoption=not issues,
        model_calls=0, tool_calls=0, trace_identity=trace_identity,
        code_source_tree_sha256=trace.get("provenance", {}).get("repository", {}).get("source_tree_sha256"),
        canonical_llm_calls=len(calls), canonical_attempts=len(saved), api_dumps=len(actual),
        attempt_rows=len(attempts), error_attempts=sum(r["state"] == "error" for r in attempts),
        retry_attempts=sum((r["attempt"] or 0) > 1 for r in attempts),
        missing_dump_requests=sorted(set(saved) - actual), orphan_dump_requests=sorted(actual - set(saved)),
        token_unknown_attempts={k: sum(r[k] is None for r in attempts) for k in TOKENS},
        token_known_sums={k: sum(r[k] for r in attempts if r[k] is not None) for k in TOKENS},
        raw_sources=identities, issues=issues,
        scope="Saved actual execution costs only; queue closure and score adoption are external gates. No counterfactual cost subtraction.",
    )
    return dict(agent_row=agent, attempt_rows=attempts, checks=checks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--api-dump-root", type=Path, required=True)
    parser.add_argument("--model", default="glm")
    parser.add_argument("--beta", type=int, default=20)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--data-source", default="phantom_seed2")
    parser.add_argument("--question-index", type=int, default=5)
    parser.add_argument("--dump-collection", required=True)
    parser.add_argument("--dump-member-prefix")
    parser.add_argument("--expected-trace-sha256")
    parser.add_argument("--compare-inputs", type=Path, help="Independently compare this slot to historical agents.csv and attempts.csv")
    args = parser.parse_args()
    result = derive_cost_rows(args.trace, args.api_dump_root, model=args.model, beta=args.beta,
                              job_id=args.job_id, data_source=args.data_source,
                              question_index=args.question_index, dump_collection=args.dump_collection,
                              dump_member_prefix=args.dump_member_prefix, expected_trace_sha256=args.expected_trace_sha256)
    if args.compare_inputs:
        for filename, rows in (("agents.csv", [result["agent_row"]]), ("attempts.csv", result["attempt_rows"])):
            with (args.compare_inputs / filename).open(newline="") as handle:
                expected = [r for r in csv.DictReader(handle) if r["model"] == args.model and r["job_id"] == args.job_id]
            projected = [{k: "" if v is None else str(v) for k, v in r.items()} for r in rows]
            require(projected == expected, "historical projection differs: " + filename)
        result["checks"]["historical_agent_and_attempt_cells_equal"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
