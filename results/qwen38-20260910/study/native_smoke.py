#!/usr/bin/env python3
"""A bounded native-tool smoke for this study; never a performance selector."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

PLACEHOLDER = "EXPGYM_LOCAL_NOAUTH_PLACEHOLDER_20260907"
TOOLS = [{"type": "function", "function": {
    "name": "read_note", "description": "Read the current run's note by its label.",
    "parameters": {"type": "object", "properties": {"label": {"type": "string"}},
                   "required": ["label"], "additionalProperties": False}}}]


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def exercise(client, label, nonce, choice):
    messages = [{"role": "system", "content": "Use the provided tool to retrieve the run note. Do not invent its contents."},
                {"role": "user", "content": "Read the note with label " + label + ". After receiving it, answer with its exact text."}]
    initial = copy.deepcopy(messages)
    first = client.generate(messages, tools=TOOLS, tool_choice=choice)
    item = {"first": asdict(first), "input_messages_unchanged": messages == initial,
            "native_tool_observed": bool(first.tool_calls), "tool_arguments_valid": False,
            "multi_turn_exercised": False, "nonce_match_descriptive_only": None}
    if len(first.tool_calls) != 1:
        item["not_exercised_reason"] = "No single native call; retained without resampling."
        return item
    call = first.tool_calls[0]
    try:
        arguments = json.loads(call["function"]["arguments"])
    except (ValueError, TypeError):
        return item
    if call["function"]["name"] != "read_note" or arguments != {"label": label}:
        return item
    item["tool_arguments_valid"] = True
    messages += [copy.deepcopy(first.assistant_message),
                 {"role": "tool", "tool_call_id": call["id"], "name": "read_note", "content": nonce},
                 {"role": "user", "content": "The tool has finished. Provide the final answer now; no further tool call is needed."}]
    history = copy.deepcopy(messages)
    final = client.generate(messages, tools=TOOLS, tool_choice="none")
    item.update(final=asdict(final), multi_turn_exercised=True,
                continuation_messages_unchanged=messages == history,
                final_has_no_tool_calls=not final.tool_calls,
                nonce_match_descriptive_only=final.text.strip() == nonce)
    return item


def self_test(client_type):
    requests = []
    original = {"role": "assistant", "content": None, "reasoning_content": "Preserve this reasoning.",
                "tool_calls": [{"id": "smoke-call", "type": "function", "function": {
                    "name": "read_note", "arguments": '{"label":"case"}'}}]}
    responses = [
        {"choices": [{"message": original, "finish_reason": "tool_calls"}],
         "usage": {"prompt_tokens": 12, "completion_tokens": 9}},
        {"choices": [{"message": {"role": "assistant", "content": "SMOKE_VALUE"}, "finish_reason": "stop"}],
         "usage": {"prompt_tokens": 27, "completion_tokens": 4}}]

    def transport(request, timeout):
        requests.append(json.loads(request.data))
        return json.dumps(responses.pop(0)).encode()

    client = client_type(api_key=PLACEHOLDER, transport=transport, max_retries=0,
                         prompt_cache_key='qwen38-smoke-unit', prompt_cache_key_field='cache_salt')
    result = exercise(client, "case", "SMOKE_VALUE", "auto")
    assert result["multi_turn_exercised"] and result["nonce_match_descriptive_only"]
    assert result["input_messages_unchanged"] and result["continuation_messages_unchanged"]
    assert requests[1]["messages"][2] == original
    assert requests[1]["tools"] == TOOLS and requests[1]["tool_choice"] == "none"
    assert all(r['cache_salt'] == 'qwen38-smoke-unit' and 'prompt_cache_key' not in r for r in requests)
    assert len(requests) == 2
    print(json.dumps({"passed": True, "synthetic_requests": 2, "real_model_calls": 0}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--endpoint")
    parser.add_argument("--model", default="qwen3.8-2.4t-a95b-fp8")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_repo.resolve()))
    from expgym.llm_clients import OpenAICompatibleLLM
    from expgym.trace_v2 import source_tree_sha256
    if args.self_test:
        self_test(OpenAICompatibleLLM)
        return 0
    if not args.endpoint or args.output_dir is None:
        parser.error("real execution requires --endpoint and fresh --output-dir")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    key = args.api_key_file.read_text().strip() if args.api_key_file else PLACEHOLDER
    config = {"model": args.model, "temperature": 1.0, "top_p": 0.95, "top_k": 20,
              "seed": 2200, "max_tokens": 32768, "reasoning_effort": "xhigh",
              "chat_template_kwargs": {"enable_thinking": True, "preserve_thinking": True},
              "max_retries": 2, "retry_base_seconds": 3, "retry_max_seconds": 30,
              "timeout": 3600, "base_url": args.endpoint,
              "prompt_cache_key_field": "cache_salt"}
    write_json(output / "plan.json", {"config": config, "source_tree_sha256": source_tree_sha256(args.source_repo),
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "planned_cases": ["auto", "named-tool"], "max_delivered_decisions": 4,
               "description": "Native plumbing only; exact nonce behavior is not a performance gate."})
    started = time.monotonic()
    results = []
    for name, choice in [("auto", "auto"), ("named-tool", {"type": "function", "function": {"name": "read_note"}})]:
        case = output / name
        case.mkdir()
        os.environ["EXPGYM_API_DUMP_DIR"] = str(case / "api_dump")
        os.environ["EXPGYM_RUN_ID"] = "qwen38-native-smoke-" + name
        nonce = "SMOKE_NOTE_" + uuid.uuid4().hex[:12]
        write_json(case / "case.json", {"label": name, "note": nonce, "tool_choice": choice})
        client = OpenAICompatibleLLM(api_key=key, prompt_cache_key='qwen38-native-smoke-' + name, **config)
        try:
            result = exercise(client, name, nonce, choice)
            result["delivered_without_exception"] = True
        except Exception as exc:
            result = {"delivered_without_exception": False, "exception_type": type(exc).__name__,
                      "attempt_usage": getattr(exc, "attempt_usage", None)}
        write_json(case / "result.json", result)
        results.append(result)
        print(json.dumps({"case": name, "delivered_without_exception": result["delivered_without_exception"],
                          "multi_turn_exercised": result.get("multi_turn_exercised", False)}), flush=True)
    passed = all(r["delivered_without_exception"] and r.get("multi_turn_exercised")
                 and r.get("input_messages_unchanged") and r.get("continuation_messages_unchanged")
                 and r.get("final_has_no_tool_calls") for r in results)
    write_json(output / "summary.json", {"passed": passed, "wall_seconds": time.monotonic() - started,
               "planned_cases": 2, "cases": results, "nonce_is_not_a_performance_gate": True,
               "failed_or_unexercised_cases_retained_without_resampling": True})
    print(json.dumps({"passed": passed, "output_dir": str(output)}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
