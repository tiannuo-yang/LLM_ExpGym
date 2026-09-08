#!/usr/bin/env python3
"""Offline-only audit: read saved JSON/source, print evidence; never contact a server."""

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Optional


BASE = Path(__file__).resolve().parent
EVAL = BASE.parent
SRT = BASE / "independent/.venv/lib/python3.12/site-packages/sglang/srt"
CHECKPOINT = Path("/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Kimi-K3")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    records = []
    key_counts = Counter()
    constraints = []
    for path in sorted((EVAL / "dumps/smoke").rglob("*.json")):
        obj = json.loads(path.read_text())
        response = obj.get("response_json")
        if not isinstance(response, dict) or not response.get("choices"):
            continue
        request = obj["request_payload"]
        key_counts.update(request.keys())
        for key in ("response_format", "json_schema", "regex", "ebnf", "grammar", "custom_logit_processor", "logit_bias"):
            if request.get(key) is not None:
                constraints.append({"dump": str(path.relative_to(EVAL)), "field": key})
        choice = response["choices"][0]
        message = choice["message"]
        reasoning = message.get("reasoning_content") or ""
        content = message.get("content") or ""
        records.append({
            "dump": str(path.relative_to(EVAL)),
            "dump_sha256": sha256(path),
            "request_id": obj.get("request_id"),
            "state": obj.get("state"),
            "thinking": request.get("chat_template_kwargs", {}).get("thinking"),
            "stream": request.get("stream", False),
            "message_count": len(request.get("messages", [])),
            "usage_reasoning_tokens": response.get("usage", {}).get("reasoning_tokens"),
            "completion_tokens": response.get("usage", {}).get("completion_tokens"),
            "finish_reason": choice.get("finish_reason"),
            "reasoning_characters": len(reasoning),
            "reasoning_sha256": hashlib.sha256(reasoning.encode()).hexdigest(),
            "content_characters": len(content),
            "content_has_native_tools_open": "<|open|>tools<|sep|>" in content,
            "raw_http_body_is_parsed_json": isinstance(obj.get("response_raw"), str),
        })

    # Compile only the original result class and non-stream detector method.
    # This avoids importing SGLang, torch, CUDA, or any networking dependencies.
    parser_path = SRT / "parser/reasoning_parser.py"
    tree = ast.parse(parser_path.read_text())
    result_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "StreamingParseResult")
    detector = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "KimiK3Detector")
    method = next(n for n in detector.body if isinstance(n, ast.FunctionDef) and n.name == "detect_and_parse")
    selected = ast.Module(body=[result_class, method], type_ignores=[])
    namespace = {"Optional": Optional}
    exec(compile(selected, str(parser_path), "exec"), namespace)
    marker_tree = ast.parse((SRT / "function_call/kimik3_format.py").read_text())
    markers = {n.targets[0].id: ast.literal_eval(n.value) for n in marker_tree.body if isinstance(n, ast.Assign)}
    instance = SimpleNamespace(
        _in_reasoning=False,
        think_start_token=markers["THINK_OPEN"],
        think_end_token=markers["THINK_CLOSE"],
        tool_start_token=markers["TOOLS_OPEN"],
        # These fixtures contain no response wrappers or tools, so cleanup is identity.
        _clean_content=lambda value: value,
    )
    text = "Thought: ordinary visible deliberation"
    action = "Action: evaluate_config {}"
    fixture_inputs = {
        "ordinary_text_only": text + "\n" + action,
        "orphan_think_close": text + markers["THINK_CLOSE"] + action,
        "explicit_think_open_and_close": markers["THINK_OPEN"] + text + markers["THINK_CLOSE"] + action,
    }
    fixtures = {}
    for name, value in fixture_inputs.items():
        result = namespace["detect_and_parse"](instance, value)
        fixtures[name] = {"input_generated_text": value, "parsed": {"reasoning_content": result.reasoning_text, "content": result.normal_text}}
    assert fixtures["orphan_think_close"]["parsed"] == fixtures["explicit_think_open_and_close"]["parsed"]
    assert not fixtures["ordinary_text_only"]["parsed"]["reasoning_content"]

    source_lines = {
        SRT / "parser/reasoning_parser.py": [64, 415, 452, 464, 470, 481, 1635],
        SRT / "entrypoints/openai/serving_chat.py": [803, 829, 1022, 1056, 1670, 1683, 2033, 2189, 2193],
        SRT / "entrypoints/openai/protocol.py": [203, 931, 944],
        SRT / "entrypoints/openai/usage_processor.py": [35, 36],
        SRT / "managers/schedule_batch.py": [811, 815, 820, 825, 1676, 1688],
        SRT / "managers/scheduler_components/batch_result_processor.py": [990, 992],
        SRT / "managers/scheduler.py": [744, 748],
        SRT / "sampling/sampling_batch_info.py": [293, 297],
        SRT / "sampling/custom_logit_processor.py": [47, 58],
        SRT / "managers/tokenizer_manager.py": [1088, 1095],
        SRT / "constrained/grammar_manager.py": [117, 129],
        SRT / "constrained/reasoner_grammar_backend.py": [102, 110, 183, 200],
        SRT / "function_call/kimik3_format.py": [1, 7],
        CHECKPOINT / "tokenization_kimi.py": [357, 362, 386],
        CHECKPOINT / "encoding_k3.py": [409, 426, 642, 644],
        CHECKPOINT / "README.md": [625, 629],
        BASE / "serve_node.sh": [13, 18, 21],
    }
    nonempty = [r for r in records if r["reasoning_characters"]]
    log = (BASE / "runs/1203299/replica0-rank0.log").read_text()
    evidence = {
        "schema_version": 1,
        "scope": "Completed 136-request smoke; offline source and saved HTTP JSON inspection only",
        "job_id": "1203299",
        "sglang_version": "0.5.16+pr32477",
        "no_service_requests_or_mutations": True,
        "summary": {
            "responses": len(records),
            "thinking_false_requests": sum(r["thinking"] is False for r in records),
            "nonstream_requests": sum(not r["stream"] for r in records),
            "reported_zero_reasoning_tokens": sum(r["usage_reasoning_tokens"] == 0 for r in records),
            "nonempty_reasoning_content_responses": len(nonempty),
            "reasoning_content_characters": sum(r["reasoning_characters"] for r in nonempty),
            "nonempty_reasoning_first_turn_responses": sum(r["message_count"] == 2 for r in nonempty),
            "nonempty_reasoning_content_with_native_tools": sum(r["content_has_native_tools_open"] for r in nonempty),
        },
        "request_payload_key_counts": dict(sorted(key_counts.items())),
        "constraints": {
            "explicit_constraint_request_fields": constraints,
            "custom_logit_processor_enabled": "enable_custom_logit_processor=True" in log,
            "server_log_explicitly_disables_custom_logit_processor": "enable_custom_logit_processor=False" in log,
            "statement": "No explicit grammar/regex/schema/response_format/logit_bias/custom processor in smoke requests; server custom-logit-processor feature disabled. Model-specific structural think-channel hard mask not enabled.",
        },
        "interpretation": {
            "label": "requested thinking=false; 6/136 responses contain nonempty server-parsed reasoning_content",
            "usage_zero_proves_absence_of_reasoning": False,
            "actual_think_open_emission_identifiable_from_saved_http_json": False,
            "strict_non_thinking_guaranteed": False,
            "counter_explanation": "thinking=false sets require_reasoning=false, which gates scheduler reasoning-token accumulation; usage does not re-tokenize parsed reasoning_content",
            "parser_ambiguity": "With force_reasoning=false, an orphan think-close routes all preceding text into reasoning_content, producing the same parsed fields as explicit think-open plus think-close",
            "semantic_reasoning_note": "Channel suppression would constrain structural output only; it cannot establish absence of semantic reasoning or internal computation",
        },
        "synthetic_parser_fixtures": fixtures,
        "nonempty_reasoning_responses": nonempty,
        "all_response_file_hashes": [{"dump": r["dump"], "sha256": r["dump_sha256"]} for r in records],
        "fixed_source_references": [{"path": str(p), "sha256": sha256(p), "relevant_lines": lines} for p, lines in source_lines.items()],
        "audit_script_sha256": sha256(Path(__file__)),
    }
    assert evidence["summary"]["responses"] == 136
    assert evidence["summary"]["reasoning_content_characters"] == 21707
    assert not constraints
    assert evidence["constraints"]["server_log_explicitly_disables_custom_logit_processor"]
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
