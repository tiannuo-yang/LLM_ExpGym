"""Replay closed native-smoke dumps through the fixed CPU serving renderer.

No HTTP calls, model loading, CUDA initialization, rescoring or resampling.
Pass --native ROOT SUMMARY_SHA256 once per replica (at most four). Only completed,
passed two-case smokes are eligible; failures remain in their original dumps.
The optional output is fresh and restricted to this study, outside native inputs.
Persisted response_raw hashes are not advertised as original network-byte hashes.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
import urllib.parse


PATCHED_SOURCES = {
    "chat_encoding.py": "4cc93655ba72dabc45b40a23a107c76c2208cb7c5c612193f6832388fe2c624c",
    "encoding_dsv4.py": "764dcfb28a57c3196975475747cb525ccacb4110556e3d9d35f038d6283ca527",
    "serving_chat.py": "c6b6d725b96e6a9fd924a39bf7702af0fbe1c657aa0678c0a48841e73b018603",
}
FORCED_FINAL = "The tool has finished. Provide the final answer now; no further tool call is needed."
CLIENT_SHA256 = "59f1e78f518fb7e0e85fda51cc163b2e54c533de68f5d94607f3ac1e05dcd2c5"
TOOLS = [{"type": "function", "function": {
    "name": "read_note", "description": "Read the current run's note by its label.",
    "parameters": {"type": "object", "properties": {"label": {"type": "string"}},
                   "required": ["label"], "additionalProperties": False}}}]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_digest(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode())


def accepted_usage(record, decoder):
    response = record.get("response_json")
    usage = response.get("usage") if isinstance(response, dict) else None
    try:
        decoder._validate_usage(usage)
        json.dumps(usage, allow_nan=False)
    except (ValueError, TypeError, RecursionError):
        return None
    return usage


def reference_messages(payload, tool_definitions):
    """Independent text-only adaptation into the vendor encoder's interface."""
    messages = copy.deepcopy(payload["messages"])
    if messages[0]["role"] != "system":
        messages.insert(0, {"role": "system", "content": ""})
    messages[0]["tools"] = copy.deepcopy(tool_definitions)
    for message in messages:
        content = message.get("content")
        if isinstance(content, list):
            message["content"] = " ".join(part["text"] for part in content if isinstance(part, dict) and part.get("type") in ("text", "input_text"))
        elif content is None:
            message["content"] = ""
        for call in message.get("tool_calls") or []:
            if isinstance(call["function"]["arguments"], dict):
                call["function"]["arguments"] = json.dumps(call["function"]["arguments"], ensure_ascii=False)
    return messages


class Inputs:
    def __init__(self):
        self.files = {}

    def read(self, path, expected=None):
        path = Path(path).absolute()
        require(path.resolve() == path, f"Input symlinks/relative traversal are not accepted: {path}")
        if path not in self.files:
            before = path.stat()
            require(stat.S_ISREG(before.st_mode) and before.st_size <= 16 << 20, f"Not bounded regular metadata: {path}")
            raw = path.read_bytes()
            after = path.stat()
            identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            require(identity == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), f"Input changed during read: {path}")
            self.files[path] = (raw, identity, {"path": str(path), "bytes": len(raw), "sha256": digest(raw)})
        raw, _, item = self.files[path]
        require(expected is None or item["sha256"] == expected, f"Input SHA mismatch: {path}")
        return raw

    def json(self, path, expected=None):
        value = json.loads(self.read(path, expected))
        require(isinstance(value, dict), f"Expected JSON object: {path}")
        return value

    def finish(self):
        for path, (_, identity, _) in self.files.items():
            current = path.stat()
            require(path.resolve() == path, f"Input became a symlink: {path}")
            require(identity == (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns), f"Input changed after read: {path}")
        return [item for _, _, item in self.files.values()]


def load_decoder(inputs, source_repo):
    """Compile pinned pure decoder/URL methods, never client transport."""
    source = Path(source_repo) / "expgym/llm_clients.py"
    tree = ast.parse(inputs.read(source, CLIENT_SHA256))
    owner = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "OpenAICompatibleLLM")
    names = {"_normalize_tool_calls", "_validate_usage", "_decode_response"}
    methods = [node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require(len(methods) == 3, "Pinned client decoder methods not found")
    normalizer = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_normalize_chat_completions_url")
    cls = ast.ClassDef(name="PinnedDecoder", bases=[], keywords=[], body=methods, decorator_list=[])
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), normalizer, cls], type_ignores=[])
    namespace = {"copy": copy, "json": json, "urllib": urllib}
    exec(compile(ast.fix_missing_locations(module), str(source), "exec"), namespace)
    namespace["PinnedDecoder"].normalize_endpoint = staticmethod(namespace["_normalize_chat_completions_url"])
    return namespace["PinnedDecoder"]


def wire_contract(case_name, spec, result, records, config, decoder):
    """Pure saved-artifact checks, independent of a tokenizer or GPU runtime."""
    require(result.get("delivered_without_exception") is True and result.get("multi_turn_exercised") is True, "Only closed, exercised native cases can be replayed")
    require(result.get("input_messages_unchanged") is True and result.get("continuation_messages_unchanged") is True, "Native smoke reported mutated caller history")
    require(result.get("final_has_no_tool_calls") is True, "Forced final still had tool calls")
    require(spec.get("label") == case_name, "Case label differs from directory")
    first, final = result["first"], result["final"]
    attempts = first["attempt_usage"] + final["attempt_usage"]
    ids = [item["request_id"] for item in attempts]
    require(len(set(ids)) == len(ids) and set(ids) == set(records), "Ledger/dump request IDs are not one-to-one")
    require(len({record["client_id"] for record in records.values()}) == 1, "One native case uses multiple clients")
    delivered = []
    for decision in (first, final):
        ledger = decision["attempt_usage"]
        require(bool(ledger), "Delivered decision has no physical attempts")
        require(len(ledger) == decision["request_attempts"], "Decision attempt count mismatch")
        require([item["attempt"] for item in ledger] == list(range(1, len(ledger) + 1)), "Attempt sequence is discontinuous")
        require(len({item["generation_id"] for item in ledger}) == 1, "Retries changed generation ID")
        require(len(ledger) <= config["max_retries"] + 1, "Attempt count exceeds planned retries")
        for index, item in enumerate(ledger):
            record = records[item["request_id"]]
            require(record["schema_version"] == "expgym.api_attempt.v1", "Unknown dump schema")
            require(record["request_id"] == item["request_id"], "Dump ID mismatch")
            for field in ("generation_id", "attempt", "state", "http_status"):
                require(record[field] == item[field], f"Ledger/dump {field} mismatch")
            require(record.get("finished_at_utc") is not None, "In-flight attempt cannot be replayed")
            require(record["run_id"] == "deepseek-flash-native-smoke-" + case_name, "Wrong native run namespace")
            require(record["max_attempts"] == config["max_retries"] + 1, "Dump retry policy differs from plan")
            endpoint = urllib.parse.urlsplit(decoder.normalize_endpoint(config["base_url"]))
            sanitized_endpoint = urllib.parse.urlunsplit((endpoint.scheme, endpoint.netloc.rsplit("@", 1)[-1], endpoint.path, "", ""))
            require(record["endpoint"] == sanitized_endpoint, "Dump endpoint differs from native plan")
            require(record["request_payload"] == records[ledger[0]["request_id"]]["request_payload"], "Transport retry changed request")
            last = index == len(ledger) - 1
            require(record["state"] == ("success" if last else "error"), "Non-transport retry or incomplete decision")
            require(record["will_retry"] is (not last), "Retry declaration mismatch")
            raw = record.get("response_raw")
            if raw is not None:
                try:
                    parsed = json.loads(raw)
                except (ValueError, RecursionError):
                    require(record.get("response_json") is None, "Non-JSON persisted raw has a parsed response")
                else:
                    require(parsed == record.get("response_json"), "Persisted response_raw/JSON mismatch")
            else:
                require(record.get("response_json") is None, "No persisted raw but a parsed response exists")
            require(accepted_usage(record, decoder) == item["usage"], "Attempt usage differs from dump")
            if not last:
                status = record["http_status"]
                error_type = (record.get("error") or {}).get("type")
                require(status in (429, 500, 502, 503, 504) or (status is None and error_type in ("URLError", "TimeoutError", "ConnectionError", "ConnectionResetError", "ConnectionRefusedError", "ConnectionAbortedError", "BrokenPipeError")), "Retry is not a permitted transport failure")
            if last:
                response = record["response_json"]
                require(isinstance(response, dict), "Success has no JSON response")
                require(json.loads(record["response_raw"]) == response, "Persisted response_raw/JSON mismatch")
                require(response.get("usage") == item["usage"], "Success usage differs from ledger")
                _, text, calls, message, finish = decoder._decode_response(record["response_raw"].encode())
                require(finish != "abort", "Provider abort cannot be a successful decision")
                require((text, calls, message, finish) == (decision["text"], decision["tool_calls"], decision["assistant_message"], decision["finish_reason"]), "Pinned decoder output differs from saved result")
                usage = response.get("usage") or {}
                prompt = usage.get("prompt_tokens")
                if prompt is None:
                    prompt = usage.get("input_tokens")
                completion = usage.get("completion_tokens")
                if completion is None:
                    completion = usage.get("output_tokens")
                details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
                cached = details.get("cached_tokens") if isinstance(details, dict) else None
                written = details.get("cache_write_tokens") if isinstance(details, dict) else None
                require((decision["prompt_tokens"], decision["completion_tokens"], decision["cached_prompt_tokens"], decision["cache_write_prompt_tokens"]) == (prompt, completion, cached, written), "Delivered usage scalar projection differs from source")
                delivered.append(record)
    require(first["attempt_usage"][0]["generation_id"] != final["attempt_usage"][0]["generation_id"], "Both decisions reuse one generation ID")
    initial, continuation = [record["request_payload"] for record in delivered]
    for payload in (initial, continuation):
        require(set(payload) == {"model", "messages", "temperature", "top_p", "seed", "max_tokens", "reasoning_effort", "chat_template_kwargs", "cache_salt", "tools", "tool_choice", "parallel_tool_calls"}, "Payload contains missing/extra fields outside the frozen native client contract")
        for field in ("model", "temperature", "top_p", "seed", "max_tokens", "reasoning_effort", "chat_template_kwargs"):
            require(payload[field] == config[field], f"Effective request {field} differs from plan")
        require(payload["reasoning_effort"] == "max" and payload["chat_template_kwargs"].get("thinking") is True, "Highest thinking setting is not effective")
        require(payload.get("parallel_tool_calls") is False, "Unexpected parallel tool mode")
        require("prompt_cache_key" not in payload and isinstance(payload.get("cache_salt"), str) and payload["cache_salt"], "Missing explicit cache_salt")
    require(initial["cache_salt"] == continuation["cache_salt"], "Case cache namespace changed within conversation")
    require(initial["cache_salt"] == "deepseek-flash-native-smoke-" + case_name, "Wrong cache salt namespace")
    require(initial["tool_choice"] == spec["tool_choice"], "Initial tool selection differs from case")
    expected_choice = "auto" if case_name == "auto" else {"type": "function", "function": {"name": "read_note"}}
    require(initial["tool_choice"] == expected_choice, "Native case is neither the expected auto nor named-tool path")
    require(continuation["tool_choice"] == "none", "Final request is not forced-none")
    require(initial["tools"] == continuation["tools"] == TOOLS, "Forced final lost or changed tool schemas")
    require(initial["messages"] == [
        {"role": "system", "content": "Use the provided tool to retrieve the run note. Do not invent its contents."},
        {"role": "user", "content": "Read the note with label " + case_name + ". After receiving it, answer with its exact text."},
    ], "Initial native prompt differs from recorded smoke implementation")
    calls = first["tool_calls"]
    require(len(calls) == 1 and calls[0]["function"]["name"] == "read_note", "No single expected native tool call")
    require(json.loads(calls[0]["function"]["arguments"]) == {"label": case_name}, "Tool arguments differ from planned label")
    expected_history = initial["messages"] + [
        first["assistant_message"],
        {"role": "tool", "tool_call_id": calls[0]["id"], "name": "read_note", "content": spec["note"]},
        {"role": "user", "content": FORCED_FINAL},
    ]
    require(continuation["messages"] == expected_history, "Final wire request did not preserve exact assistant/tool history")
    require(not final["tool_calls"] and not final["assistant_message"].get("tool_calls"), "Final native response contains a tool call")
    return delivered


class Renderer:
    def __init__(self, inputs, checkpoint, cpu_file, cpu_sha):
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "Set CUDA_VISIBLE_DEVICES='' first")
        require(os.environ.get("HF_HUB_OFFLINE") == "1" and os.environ.get("TRANSFORMERS_OFFLINE") == "1", "Use the offline runtime environment")
        self.network_attempts = []
        def network_guard(event, args):
            if event in ("socket.connect", "socket.getaddrinfo"):
                self.network_attempts.append(event)
                raise RuntimeError("Native dump replay forbids all network connections")
        sys.addaudithook(network_guard)
        sys.dont_write_bytecode = True
        cpu = inputs.json(cpu_file, cpu_sha)
        require(cpu["status"] == "passed_cpu_only_not_native_or_gpu_validation", "Not the accepted runtime CPU result")
        root = Path(cpu_file).resolve().parent
        require(Path(sys.prefix).resolve() == root / ".venv", "Wrong replay interpreter")
        checkpoint = Path(checkpoint).resolve(strict=True)
        require(str(checkpoint) == cpu["checkpoint"], "Wrong replay checkpoint")
        for name, version in cpu["fixed_distribution_versions"].items():
            require(importlib.metadata.version(name) == version, f"Runtime version changed: {name}")
        for name in ("uv.lock", "runtime-env.sh", "pyproject.toml"):
            inputs.read(root / name, cpu["runtime_inputs"][name]["sha256"])
        import torch
        import sglang
        from transformers import AutoConfig, AutoTokenizer
        from sglang.srt.entrypoints.openai import chat_encoding, encoding_dsv4, serving_chat
        from sglang.srt.entrypoints.openai.protocol import ChatCompletionRequest
        require(not torch.cuda.is_initialized(), "Renderer imports initialized CUDA")
        source = Path(sglang.__file__).resolve().parent / "srt/entrypoints/openai"
        for name, expected in PATCHED_SOURCES.items():
            require(cpu["patched_sources"][name]["sha256"] == expected, "CPU result identifies a different encoder patch")
            inputs.read(source / name, expected)
        for name in ("config.json", "tokenizer_config.json", "tokenizer.json", "encoding/encoding_dsv4.py"):
            inputs.read(checkpoint / name, cpu["model_metadata"][name]["sha256"])
        config = AutoConfig.from_pretrained(checkpoint, local_files_only=True, trust_remote_code=False)
        tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True, trust_remote_code=False)
        self.profile = chat_encoding.resolve_dsv4_reasoning_effort_profile(model_path=str(checkpoint))
        require(self.profile == "official", "Not the official 0731 maximum-effort profile")
        require(chat_encoding.resolve_chat_encoding_spec(hf_config=config, tokenizer=tokenizer, tool_call_parser="deepseekv4") == "dsv4", "Wrong encoding dispatch")
        self.prefix = encoding_dsv4.REASONING_EFFORT_PROFILES[self.profile]["max"]
        require(digest(self.prefix.encode()) == cpu["maximum_effort_prefix"]["sha256"], "Maximum prefix changed")
        self.renderer = serving_chat.OpenAIServingChat.__new__(serving_chat.OpenAIServingChat)
        self.renderer.chat_encoding_spec = "dsv4"
        self.renderer._dsv4_reasoning_effort_profile = self.profile
        self.renderer.template_manager = SimpleNamespace(jinja_template_content_format="string")
        self.renderer.tokenizer_manager = SimpleNamespace(tokenizer=tokenizer)
        self.tokenizer, self.request_type, self.torch = tokenizer, ChatCompletionRequest, torch
        self.reference = {"__name__": "pinned_deepseek_native_reference"}
        ref_file = checkpoint / "encoding/encoding_dsv4.py"
        exec(compile(inputs.read(ref_file), str(ref_file), "exec"), self.reference)

    def replay(self, record):
        payload = record["request_payload"]
        request = self.request_type(**copy.deepcopy(payload))
        before = request.model_dump()
        # Mirrors _process_messages' tool-list selection, without instantiating
        # a server/grammar engine; dsv4 itself retains request.tools for none.
        choice = request.tool_choice
        tools = None
        if request.tools and choice != "none":
            tools = [t.model_dump() for t in request.tools]
            if not isinstance(choice, str):
                tools = [t for t in tools if t["function"]["name"] == choice.function.name]
        actual = self.renderer._apply_jinja_template(request, tools, False)
        require(request.model_dump() == before, "CPU renderer mutated saved request")
        vendor_messages = reference_messages(payload, [t.model_dump() for t in request.tools])
        expected = self.reference["encode_messages"](vendor_messages, thinking_mode="thinking", reasoning_effort="max")
        require(expected.startswith(self.reference["bos_token"] + self.prefix), "Maximum prefix absent from reconstructed prompt")
        require(actual.prompt_ids == self.tokenizer.encode(expected), "Actual runtime token IDs differ from checkpoint reference")
        usage = record["response_json"].get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens")
        if prompt_tokens is None:
            prompt_tokens = usage.get("input_tokens")
        require(type(prompt_tokens) is int and prompt_tokens == len(actual.prompt_ids), "Server prompt_tokens differ from CPU replay")
        require("Available Tool Schemas" in expected, "Tool schema missing from rendered prompt")
        history = []
        for position, message in enumerate(payload["messages"]):
            if message["role"] == "assistant":
                reasoning = message.get("reasoning_content")
                require(reasoning is None or isinstance(reasoning, str), "Unexpected reasoning representation")
                require(not reasoning or reasoning in expected, "Prior reasoning lost from rendered prompt")
                history.append({"position": position, "role": "assistant", "message_json_sha256": json_digest(message), "reasoning_characters": len(reasoning or ""), "reasoning_present_in_render": bool(reasoning)})
            elif message["role"] == "tool":
                require(message["content"] in expected, "Tool response lost from rendered prompt")
                history.append({"position": position, "role": "tool", "message_json_sha256": json_digest(message), "content_present_in_render": True})
        return {
            "request_id": record["request_id"], "generation_id": record["generation_id"],
            "tool_choice": payload["tool_choice"], "request_payload_json_sha256": json_digest(payload),
            "reconstructed_client_request_serialization_sha256": digest(json.dumps(payload).encode()),
            "persisted_response_raw_utf8_sha256": digest(record["response_raw"].encode()),
            "response_json_sha256": json_digest(record["response_json"]),
            "rendered_prompt_utf8_sha256": digest(expected.encode()),
            "rendered_token_ids_json_sha256": json_digest(actual.prompt_ids),
            "server_prompt_tokens": prompt_tokens, "replayed_prompt_tokens": len(actual.prompt_ids),
            "maximum_prefix_present": True, "tool_definitions_retained": True,
            "checkpoint_reference_exact_token_match": True, "history": history,
        }


def collect_native(inputs, root, summary_sha, decoder):
    root = Path(root).absolute()
    summary = inputs.json(root / "summary.json", summary_sha)
    require(summary.get("passed") is True and summary.get("planned_cases") == 2, "Native smoke failed, partial or unexercised; do not resample")
    require(len(summary["cases"]) == 2, "Unexpected summary case count")
    plan = inputs.json(root / "plan.json")
    inputs.read(Path(__file__).with_name("native_smoke.py"), plan["script_sha256"])
    require(plan["planned_cases"] == ["auto", "named-tool"], "Unexpected native plan cases")
    require(plan["config"]["reasoning_effort"] == "max", "Native plan did not request maximum effort")
    rows, all_attempts = [], []
    for index, name in enumerate(("auto", "named-tool")):
        directory = root / name
        spec = inputs.json(directory / "case.json")
        result = inputs.json(directory / "result.json")
        require(result == summary["cases"][index], "Summary differs from saved case result")
        paths = sorted((directory / "api_dump").glob("*.json"))
        require(2 <= len(paths) <= 6, "Unexpected native attempt count")
        records = {}
        for path in paths:
            record = inputs.json(path)
            request_id = record["request_id"]
            require(path.name == request_id + ".json" and request_id not in records, "Dump filename/ID mismatch")
            records[request_id] = record
            all_attempts.append({
                "path": str(path), "request_id": request_id, "generation_id": record["generation_id"],
                "attempt": record["attempt"], "state": record["state"], "http_status": record["http_status"],
                "usage": accepted_usage(record, decoder),
                "request_payload_json_sha256": json_digest(record["request_payload"]),
                "persisted_response_raw_utf8_sha256": digest(record["response_raw"].encode()) if record.get("response_raw") is not None else None,
            })
        delivered = wire_contract(name, spec, result, records, plan["config"], decoder)
        rows.append({"case": name, "delivered": delivered, "nonce_match_descriptive_only": result.get("nonce_match_descriptive_only")})
    require(rows[0]["delivered"][0]["request_payload"]["cache_salt"] != rows[1]["delivered"][0]["request_payload"]["cache_salt"], "Independent native cases share cache salt")
    require(rows[0]["delivered"][0]["client_id"] != rows[1]["delivered"][0]["client_id"], "Independent native cases share client identity")
    return {"root": str(root), "summary_sha256": summary_sha, "endpoint": plan["config"]["base_url"], "cases": rows, "all_attempts": all_attempts}


def write_fresh(path, value, study, native_roots):
    path = Path(path).absolute()
    parent = path.parent.resolve(strict=True)
    require(parent.is_relative_to(study), "Output must stay inside this DeepSeek study")
    require(not any(parent.is_relative_to(root) for root in native_roots), "Output cannot alter a native input directory")
    require(not parent.is_relative_to(study / "runtime"), "Output cannot alter the frozen runtime")
    require(not path.exists() and not path.is_symlink(), "Output must be fresh")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags, 0o644), "w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", nargs=2, action="append", metavar=("ROOT", "SUMMARY_SHA256"), required=True)
    parser.add_argument("--cpu-acceptance", type=Path, required=True)
    parser.add_argument("--cpu-acceptance-sha256", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    require(1 <= len(args.native) <= 4, "Supply one through four native replicas")
    roots = [Path(path).resolve(strict=True) for path, _ in args.native]
    require(len(set(roots)) == len(roots), "Native roots are duplicated")
    study = Path(__file__).resolve().parent.parent
    require(all(root.is_relative_to(study) for root in roots), "Native inputs must belong to this DeepSeek study")
    if args.output:
        require(not args.output.exists() and not args.output.is_symlink(), "Output must be fresh")
    inputs = Inputs()
    decoder = load_decoder(inputs, args.source_repo)
    datasets = [collect_native(inputs, root, pin, decoder) for root, (_, pin) in zip(roots, args.native)]
    require(len({data["endpoint"] for data in datasets}) == len(datasets), "Replica native roots have duplicate endpoints")
    renderer = Renderer(inputs, args.checkpoint, args.cpu_acceptance, args.cpu_acceptance_sha256)
    replay_count = 0
    for data in datasets:
        for case in data["cases"]:
            case["requests"] = [renderer.replay(record) for record in case.pop("delivered")]
            replay_count += len(case["requests"])
    require(not renderer.torch.cuda.is_initialized() and not renderer.network_attempts, "Replay accessed GPU/network")
    files = inputs.finish()
    result = {
        "schema": "deepseek0731.native-contract-replay.v1", "passed": True,
        "scope": "saved real native transport artifacts plus CPU prompt reconstruction; no new inference",
        "replicas_checked": len(datasets), "delivered_requests_replayed": replay_count,
        "all_attempts_retained": sum(len(data["all_attempts"]) for data in datasets),
        "api_requests_made_by_replay": 0, "cuda_initialized": False,
        "effort_profile": renderer.profile, "maximum_prefix_utf8_sha256": digest(renderer.prefix.encode()),
        "patched_runtime_source_sha256": PATCHED_SOURCES,
        "helper_sha256": digest(Path(__file__).read_bytes()), "input_files": files, "replicas": datasets,
        "limitations": [
            "summary/case equality checks copies for consistency, not independent scientific evidence.",
            "response_raw is persisted/deidentified UTF-8 text, not guaranteed original network bytes.",
            "Request serialization SHA is reconstructed from saved payload, not a packet capture.",
            "CPU renderer matches saved server prompt-token counts; token IDs were not dumped by the server.",
            "Caller-history mutation flags were recorded by native_smoke; dumps alone cannot independently prove in-memory immutability.",
            "Nonce correctness is descriptive; no inference retries or score selection occur here.",
            "Reasoning preservation is observed only when the saved assistant supplied nonempty reasoning.",
        ],
    }
    if args.output:
        write_fresh(args.output, result, study, roots)
        print(json.dumps({"passed": True, "replicas": len(datasets), "requests_replayed": replay_count, "output": str(args.output)}))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
