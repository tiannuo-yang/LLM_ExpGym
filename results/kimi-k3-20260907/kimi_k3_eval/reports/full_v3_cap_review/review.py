"""Read-only cap review: JSON/schema checks only, never tools or model calls.

Run from kimi_k3_eval with PYTHONDONTWRITEBYTECODE=1; prints JSON to stdout.
"""
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[1]
BASE = STUDY.parent
REPO = BASE / "LLM_ExpGym"
sys.path.insert(0, str(REPO))
from expgym.react_loop import _extract_action, _extract_answer, _normalize_label

REPORT = STUDY / "reports/full_v3_protocol_final.json"
DUMPS = STUDY / "dumps/full-full_v3-ad4275b6"
CAP_MARKER = "\n[... output truncated due to excessive length ...]"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = json.loads(REPORT.read_text())
assert report["schema_version"] == 2
assert report["groups"]["all"]["normal_responses_over_8000_chars"] == 71
assert report["groups"]["all"]["cap_removed_action_parser_candidates"] == 22
assert report["groups"]["all"]["cap_removed_known_tool_json_candidates"] == 18
assert sum(row["normal_responses_over_8000_chars"] for row in report["trace_rows"]) == 71
assert sum(row["cap_removed_action_parser_candidates"] for row in report["trace_rows"]) == 22
rows_by_client = defaultdict(list)
for row in report["trace_rows"]:
    rows_by_client[row["client_id"]].append(row)
raw_by_request = defaultdict(list)
for path in DUMPS.rglob("*.json"):
    raw_by_request[path.stem].append(path)
assert all(len(paths) == 1 for paths in raw_by_request.values())
audit_data_path = REPO / "data/contract-nli/test_segments.json"
audit_data = json.loads(audit_data_path.read_text())
interpretations = {}
for name in ("interpretation_even.json", "interpretation_odd.json"):
    path = HERE / name
    if path.exists():
        data = json.loads(path.read_text())
        cases = data if isinstance(data, list) else data.get("cases", data.get("entries", data.get("items")))
        for case in cases:
            case = dict(case)
            original = case["classification"]
            case["original_classification"] = original
            if original.startswith("explicit_tool_intent"):
                case["classification"] = "explicit_tool_intent"
            elif original == "thought_reference":
                case["classification"] = "thought_quote"
            assert case["request_id"] not in interpretations
            interpretations[case["request_id"]] = case

cases = []
for index, evidence in enumerate(report["cap_candidate_evidence"]):
    client_id, request_id = evidence["client_id"], evidence["request_id"]
    assert len(rows_by_client[client_id]) == 1
    row = rows_by_client[client_id][0]
    assert row["raw_success_request_ids"].count(request_id) == 1
    raw_path = raw_by_request[request_id][0]
    assert raw_path == (BASE / evidence["path"])
    raw = json.loads(raw_path.read_text())
    assert raw["state"] == "success" and raw["client_id"] == client_id and raw["request_id"] == request_id
    request = raw["request_payload"]
    assert not any("System: Loop aborted (" in m.get("content", "") for m in request["messages"][-1:])
    content = raw["response_json"]["choices"][0]["message"]["content"]
    stripped = content.strip()
    processed = stripped[:8000] + CAP_MARKER
    candidate = _extract_action(stripped)
    assert len(stripped) > 8000 and candidate and _extract_action(processed) is None
    assert _extract_answer(processed) is None
    tool, payload = candidate
    assert tool == evidence["extracted_tool"]
    expected_tool = {"evidence_audit": "human_feedback", "restricted_search": "search", "tuning": "evaluate_config"}[row["scenario"]]
    trace_path = BASE / row["path"]
    trace = json.loads(trace_path.read_text())
    messages = trace["messages"]
    assistants = [m["content"] for m in messages if m["role"] == "assistant"]
    ordinal = row["raw_success_request_ids"].index(request_id)
    assert assistants[ordinal] == processed
    assistant_message_indices = [i for i, message in enumerate(messages) if message["role"] == "assistant"]
    next_messages = messages[assistant_message_indices[ordinal] + 1:]
    next_user = next((m["content"] for m in next_messages if m["role"] == "user"), None)
    forced_missing_action = bool(next_user and "System: Loop aborted (Missing Action directive)." in next_user)
    assert row["reason"] == "missing_action" and forced_missing_action
    try:
        argument = json.loads(payload)
        json_error = None
    except ValueError as exc:
        argument, json_error = None, str(exc)
    assert (json_error is None) == evidence["payload_json_valid"]
    static = {"checked": json_error is None, "passed": False, "not_executed": True}
    if json_error is None:
        context = raw.get("context", {})
        job = context.get("job", context)
        if tool == "human_feedback":
            doc_index = int(job["question_index"])
            doc = audit_data["documents"][doc_index]
            annotations = doc["annotation_sets"][0]["annotations"]
            segments = {int(segment["span_index"]) for segment in doc["segments"]}
            shape = isinstance(argument, dict) and isinstance(argument.get("nda_id"), str) and isinstance(argument.get("evidence_ids"), list) and all(type(value) is int for value in argument["evidence_ids"])
            known_nda = shape and argument["nda_id"].strip() in annotations
            known_segments = shape and all(value in segments for value in argument["evidence_ids"])
            static.update({"passed": bool(shape and known_nda and known_segments), "object_with_string_nda_and_integer_list": shape,
                           "known_nda_id": known_nda, "all_evidence_ids_exist": known_segments,
                           "document_index": doc_index, "document_id": doc["id"],
                           "notes": "Document membership only; no gold labels/evidence correctness or feedback output was computed. Extra keys are ignored by the tool; segment existence is a stronger contextual check than its input parser requires."})
        elif tool == "search":
            shape = isinstance(argument, dict) and isinstance(argument.get("query"), str) and bool(argument["query"].strip())
            static.update({"passed": shape, "nonempty_string_query": shape,
                           "notes": "No article lookup, cache lookup, search execution or answer scoring performed."})
        elif tool == "evaluate_config":
            assert job["tuning_task"] == "hpobench:nasbench101:B"
            choices = {}
            for line in request["messages"][1]["content"].splitlines():
                match = re.match(r"^- ([^:]+): choices=(\[.*\]) \(default=", line)
                if match:
                    choices[match.group(1)] = ast.literal_eval(match.group(2))
            expected_keys = {"edge_{}".format(i) for i in range(9)} | {"op_node_{}".format(i) for i in range(5)}
            assert set(choices) == expected_keys
            missing = sorted(expected_keys - set(argument))
            extra = sorted(set(argument) - expected_keys)
            invalid = [name for name, value in argument.items() if name in choices and value not in choices[name]]
            strict_types = all(type(argument.get("edge_{}".format(i))) is int for i in range(9)) and all(isinstance(argument.get("op_node_{}".format(i)), str) for i in range(5))
            static.update({"passed": not missing and not extra and not invalid and strict_types,
                           "task": job["tuning_task"], "expected_parameters": 14,
                           "missing_parameters": missing, "extra_parameters": extra, "values_outside_declared_choices": invalid,
                           "edge_integer_and_operation_string_types": strict_types,
                           "notes": "Checked all 14 keys/types/choices against the actual request context and NAS101B configuration-space source. B uses nine categorical edge selectors with choices 0..20, not A's 21 binary fields. No graph/performance/cost evaluation performed."})
    literals = []
    for match in re.finditer("Action:", stripped):
        offset = match.start()
        line_start = stripped.rfind("\n", 0, offset) + 1
        line_end = stripped.find("\n", offset)
        if line_end == -1:
            line_end = len(stripped)
        line = stripped[line_start:line_end]
        literals.append({"character_offset_zero_based": offset, "line_number_one_based": stripped.count("\n", 0, offset) + 1,
                         "strict_line_start": line.lstrip().startswith("Action:"),
                         "normalized_line_start": _normalize_label(line).startswith("Action:"),
                         "after_character_cap": offset >= 8000,
                         "context_excerpt": stripped[max(0, offset - 180):min(len(stripped), offset + 450)]})
    assert len(literals) == 1 and literals[0]["after_character_cap"]
    cases.append({"index": index, "request_id": request_id, "client_id": client_id,
                  "raw_path": str(raw_path), "raw_file_sha256": sha(raw_path), "trace_path": str(trace_path), "trace_file_sha256": sha(trace_path),
                  "response_content_sha256": hashlib.sha256(content.encode()).hexdigest(), "response_chars": len(content),
                  "stripped_response_chars": len(stripped), "saved_assistant_chars": len(assistants[ordinal]),
                  "saved_assistant_sha256": hashlib.sha256(assistants[ordinal].encode()).hexdigest(),
                  "raw_success_ordinal_zero_based": ordinal, "runner": row["runner"], "scenario": row["scenario"],
                  "regime": row["regime"], "strategy": row["strategy"], "agent_id": row["agent_id"],
                  "expected_tool": expected_tool, "extracted_tool": tool, "expected_tool_match": tool == expected_tool,
                  "extracted_payload": payload, "payload_json_valid": json_error is None, "payload_json_error": json_error,
                  "static_argument_checks": static, "action_literals": literals,
                  "uncapped_answer_parser_match": _extract_answer(stripped) is not None,
                  "cap_exactly_matches_saved_assistant": True, "cap_removes_parser_candidate": True,
                  "saved_next_prompt_forces_missing_action": forced_missing_action,
                  "next_user_prompt_excerpt": next_user[:600],
                  "interpretation": interpretations.get(request_id),
                  "no_tool_execution_or_counterfactual_score_claim": True})

assert len(cases) == 22 and sum(c["payload_json_valid"] for c in cases) == 18
assert sum(c["static_argument_checks"]["passed"] for c in cases) == 18
assert len(interpretations) == 22
assert all(c["interpretation"]["strict_line_start"] == c["action_literals"][0]["strict_line_start"] for c in cases)
assert all((c["interpretation"]["classification"] == "explicit_tool_intent") == c["static_argument_checks"]["passed"] for c in cases)
summary = {"cases": 22, "all_checks_passed": True, "all_linked_uniquely_by_client_and_request": True,
           "all_cap_text_equal_saved_assistant": True, "all_saved_next_prompts_missing_action": True,
           "known_tool_and_valid_json": 18, "static_schema_and_context_checks_pass": 18,
           "invalid_json_candidates": 4, "strict_line_start_action_candidates": sum(c["action_literals"][0]["strict_line_start"] for c in cases),
           "inline_action_candidates": sum(not c["action_literals"][0]["strict_line_start"] for c in cases),
           "explicit_requests_line_start": sum(c["static_argument_checks"]["passed"] and c["action_literals"][0]["strict_line_start"] for c in cases),
           "explicit_requests_inline": sum(c["static_argument_checks"]["passed"] and not c["action_literals"][0]["strict_line_start"] for c in cases),
           "interpretation_records": len(interpretations), "interpretation_counts": dict(Counter(c["interpretation"]["classification"] for c in cases if c["interpretation"]))}
print(json.dumps({"schema_version": 1, "scope": "Read-only static review of 22 cap candidates; no model or environment tool execution",
                  "source_report": str(REPORT), "source_report_sha256": sha(REPORT), "dump_namespace": str(DUMPS),
                  "source_tree_sha256": report["source_tree_sha256"], "react_loop_sha256": sha(REPO / "expgym/react_loop.py"),
                  "schema_source_sha256": {name: sha(REPO / name) for name in ("expgym/task_evidence_audit.py", "expgym/task_restricted_search.py", "expgym/compact_nasbench101.py")},
                  "audit_document_data_sha256": sha(audit_data_path), "summary": summary, "cases": cases,
                  "limits": ["71 overlong normal responses is the supplied report total, cross-checked against its trace-row sum; this review independently rereads the 22 selected raw responses only.",
                             "Line start and offsets use stripped Unicode text/Python character indices, not token counts or UTF-8 byte offsets.",
                             "Static schema/context validity is not proof that a tool would execute, remain in budget, return useful feedback or improve final performance.",
                             "The original 8000-character cap and all source/results/raw dumps remain unchanged."]}, indent=2, ensure_ascii=False, sort_keys=True))
