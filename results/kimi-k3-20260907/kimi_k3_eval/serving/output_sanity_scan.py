#!/usr/bin/env python3
"""Read-only, standard-library audit of manifest-scoped saved response fields.

Print JSON summary (default) or JSONL response inventory (--inventory).
No output files, network calls, model imports, or accelerator work are performed.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


BASE = Path(__file__).resolve().parent
DEFAULT_CKPT = Path("/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Kimi-K3")
METRICS = (
    "response_choices", "empty_content", "nonempty_reasoning_content",
    "unsupported_field_types", "choices_with_padding_marker",
    "content_padding_marker_occurrences", "reasoning_content_padding_marker_occurrences",
    "sequence_padding_choices", "media_placeholder_choices",
    "sequence_padding_content_occurrences", "sequence_padding_reasoning_content_occurrences",
    "media_placeholder_content_occurrences", "media_placeholder_reasoning_content_occurrences",
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def read_json(path):
    raw = path.read_bytes()
    return json.loads(raw), digest(raw)


def load_padding_tokens(checkpoint):
    tokenizer, tok_hash = read_json(checkpoint / "tokenizer_config.json")
    config, cfg_hash = read_json(checkpoint / "config.json")
    pad = tokenizer["pad_token"]
    if isinstance(pad, dict):
        pad = pad["content"]
    definitions = tokenizer["added_tokens_decoder"]
    # The configured PAD and separately defined media placeholder are audited;
    # they are not treated as interchangeable sequence-padding tokens.
    candidates = [
        {"text": item["content"], "token_id": int(key),
         "role": "sequence_padding" if item["content"] == pad else "media_placeholder",
         "special": item.get("special", False)}
        for key, item in definitions.items()
        if item["content"] == pad or item["content"] == "<|media_pad|>"
    ]
    actual = next(item for item in candidates if item["text"] == pad)
    assert actual["token_id"] == config["pad_token_id"]
    if "text_config" in config and "pad_token_id" in config["text_config"]:
        assert actual["token_id"] == config["text_config"]["pad_token_id"]
    return candidates, {
        "checkpoint": str(checkpoint), "pad_token": pad,
        "pad_token_id": actual["token_id"], "scanned_exact_markers": candidates,
        "tokenizer_config_sha256": tok_hash, "config_sha256": cfg_hash,
        "tokenization_source_sha256": digest((checkpoint / "tokenization_kimi.py").read_bytes()),
        "vision_processing_source_sha256": digest((checkpoint / "kimi_k3_vision_processing.py").read_bytes()),
        "references": {"tokenizer_config.json": [99, 105, 123, 129, 148],
                       "config.json": [15, 17, 195], "tokenization_kimi.py": [39, 71, 99, 104, 123, 147, 173, 183],
                       "kimi_k3_vision_processing.py": [54, 57]},
        "docstring_note": "reserved_special_token_250 is only a stale docstring default, not the configured padding token",
        "media_note": "media_pad is a defined media placeholder, reported separately from sequence PAD; a literal match alone does not establish a cache defect",
    }


def text_value(value):
    if value is None:
        return "", False
    if isinstance(value, str):
        return value, False
    if isinstance(value, list):
        if all(isinstance(p, dict) and p.get("type") in ("text", "output_text") and isinstance(p.get("text"), str) for p in value):
            return "".join(p["text"] for p in value), False
    return "", True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CKPT)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--job-id", help="Limit to one manifest job; useful for partitioned inventory")
    args = parser.parse_args()
    markers, tokenizer_evidence = load_padding_tokens(args.checkpoint.resolve())
    seen = {}
    duplicate_records = []
    records = []
    findings = []
    manifests = []
    errors = []
    aggregate = Counter({metric: 0 for metric in METRICS})
    for manifest_path in args.manifest:
        manifest_path = manifest_path.resolve()
        manifest, manifest_hash = read_json(manifest_path)
        progress_path = Path(manifest["progress_path"])
        progress, progress_hash = read_json(progress_path)
        complete = bool(progress.get("all_selected_jobs_complete") and progress.get("finished_at"))
        if not complete and not args.allow_incomplete:
            raise SystemExit(f"Refusing to label an unfinished run complete: {progress_path}; use --allow-incomplete for a partial snapshot")
        selected_jobs = [j for j in manifest["jobs"] if args.job_id is None or j["id"] == args.job_id]
        if not selected_jobs:
            raise SystemExit(f"No selected jobs in {manifest_path}")
        stage = {"manifest": str(manifest_path), "manifest_sha256": manifest_hash,
                 "source_tree_sha256": manifest["source_tree_sha256"],
                 "stage": manifest["stage"], "run_namespace": manifest["run_namespace"],
                 "progress_path": str(progress_path), "progress_sha256": progress_hash,
                 "finished_at": progress.get("finished_at"), "complete_at_snapshot": complete,
                 "progress_job_counts": progress.get("job_counts"), "jobs": []}
        stage_counts = Counter({metric: 0 for metric in METRICS})
        for job in selected_jobs:
            job_counts = Counter({metric: 0 for metric in METRICS})
            states = Counter()
            file_hashes = []
            dump_dir = Path(job["dump_dir"])
            paths = sorted(dump_dir.glob("*.json"))
            if not paths:
                errors.append({"kind": "empty_or_missing_dump_directory", "path": str(dump_dir), "job_id": job["id"]})
            for path in paths:
                obj, file_hash = read_json(path)
                file_hashes.append({"path": str(path), "sha256": file_hash})
                states[obj.get("state", "missing")] += 1
                response = obj.get("response_json") or {}
                choices = response.get("choices") or []
                if not choices:
                    errors.append({"kind": "no_response_choices", "path": str(path), "sha256": file_hash, "state": obj.get("state"), "job_id": job["id"]})
                for position, choice in enumerate(choices):
                    message = choice.get("message") or {}
                    identity = [obj.get("request_id") or str(path), obj.get("attempt"), choice.get("index", position)]
                    key = canonical(identity)
                    choice_hash = digest(canonical(choice).encode())
                    if key in seen:
                        duplicate_records.append({"case_id": key, "first_dump": seen[key]["path"], "duplicate_dump": str(path), "same_choice_sha256": seen[key]["hash"] == choice_hash})
                        if seen[key]["hash"] != choice_hash:
                            errors.append({"kind": "duplicate_identity_with_different_response", "case_id": key})
                        continue
                    seen[key] = {"path": str(path), "hash": choice_hash}
                    counts = Counter({metric: 0 for metric in METRICS})
                    counts["response_choices"] = 1
                    field_details = {}
                    matches = []
                    for field in ("content", "reasoning_content"):
                        value = message.get(field)
                        text, unsupported = text_value(value)
                        counts["unsupported_field_types"] += unsupported
                        field_details[field] = {"characters": len(text), "sha256": digest(text.encode()), "json_type": type(value).__name__, "unsupported": unsupported}
                        if field == "content":
                            counts["empty_content"] = int(not unsupported and not text.strip())
                        else:
                            counts["nonempty_reasoning_content"] = int(bool(text.strip()))
                        for marker in markers:
                            offsets = []
                            cursor = 0
                            while True:
                                offset = text.find(marker["text"], cursor)
                                if offset < 0:
                                    break
                                offsets.append(offset)
                                cursor = offset + len(marker["text"])
                            if offsets:
                                matches.append({"field": field, "marker": marker, "occurrences": len(offsets), "character_offsets": offsets, "first_excerpt": text[max(0, offsets[0] - 100):offsets[0] + len(marker["text"]) + 100]})
                                counts[field + "_padding_marker_occurrences"] += len(offsets)
                                counts[marker["role"] + "_" + field + "_occurrences"] += len(offsets)
                                counts[marker["role"] + "_choices"] = 1
                    counts["choices_with_padding_marker"] = int(bool(matches))
                    row = {"case_id": identity, "manifest": str(manifest_path), "job_id": job["id"],
                           "dump_path": str(path), "dump_sha256": file_hash,
                           "response_choice_sha256": choice_hash, "generation_id": obj.get("generation_id"),
                           "response_id": response.get("id"), "run_id": obj.get("run_id"),
                           "state": obj.get("state"), "context": obj.get("context"),
                           "finish_reason": choice.get("finish_reason"), "fields": field_details,
                           "tool_call_count": len(message.get("tool_calls") or []),
                           "empty_content": bool(counts["empty_content"]), "marker_matches": matches}
                    records.append(row)
                    if matches or counts["empty_content"] or counts["unsupported_field_types"]:
                        findings.append(row)
                    job_counts.update(counts)
                    stage_counts.update(counts)
                    aggregate.update(counts)
            stage["jobs"].append({"job_id": job["id"], "dump_directory": str(dump_dir),
                                  "dump_files": len(paths), "dump_states": dict(states),
                                  "file_inventory_sha256": digest(canonical(file_hashes).encode()),
                                  "counts": dict(job_counts)})
        stage["counts"] = dict(stage_counts)
        manifests.append(stage)
    if args.inventory:
        for row in records:
            print(canonical(row))
        return
    output = {"schema_version": 1, "scanner_sha256": digest(Path(__file__).read_bytes()),
              "scope": "Only manifest jobs' saved response_json.choices[*].message.content and reasoning_content; never request history or response_raw",
              "counting_unit": "Unique request_id, attempt, choice.index; copied/promoted duplicate identities counted once across supplied manifests",
              "tokenizer_evidence": tokenizer_evidence, "manifests": manifests,
              "counts": dict(aggregate), "findings": findings, "input_errors": errors,
              "duplicates_skipped": duplicate_records,
              "response_inventory_sha256": digest("\n".join(canonical(row) for row in records).encode()),
              "limits": ["Literal decoded-text matches are not raw generated token-ID observations", "An occurrence can be a quoted literal, not necessarily cache corruption", "No padding markers does not exclude other KV-cache, numerical, semantic, or protocol defects", "Empty content may be intentional for tool-only or reasoning-only responses; tool-call count and finish reason are retained", "Only snapshots of the supplied manifests are covered; no unscanned full-stage claim is made"]}
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
