#!/usr/bin/env python3
"""Read-only independent inventory of nine specified experiment job-dump scopes.

No project accounting/audit module is imported. Input bytes are never modified.
Only this review's new report is written, with exclusive creation.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone


STAGES = (
    "smoke", "pilot", "full", "smoke_v2", "pilot_v2", "full_v2",
    "smoke_v3", "pilot_v3", "full_v3",
)
TOKEN_PATHS = {
    "input_tokens": ("prompt_tokens",),
    "output_tokens": ("completion_tokens",),
    "provider_total_tokens": ("total_tokens",),
    "cached_input_tokens": ("prompt_tokens_details", "cached_tokens"),
    "cache_write_input_tokens": ("prompt_tokens_details", "cache_write_tokens"),
    "top_level_reasoning_tokens": ("reasoning_tokens",),
    "completion_details_reasoning_tokens": ("completion_tokens_details", "reasoning_tokens"),
    "output_details_reasoning_tokens": ("output_tokens_details", "reasoning_tokens"),
}


def stable_stat(path):
    value = path.stat()
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


def read_json(path, snapshots):
    before = stable_stat(path)
    raw = path.read_bytes()
    after = stable_stat(path)
    if before != after:
        raise ValueError("File changed while reading: {}".format(path))
    snapshots[str(path)] = after
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest(), len(raw)


def token_value(usage, keys):
    value = usage
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError("Invalid nonnegative integer usage {}: {!r}".format(keys, value))
    return value


def summarize_record(record, path):
    if not isinstance(record, dict) or record.get("schema_version") != "expgym.api_attempt.v1":
        raise ValueError("Unexpected raw schema: {}".format(path))
    request_id = record.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("Missing request_id: {}".format(path))
    if path.stem != request_id:
        raise ValueError("Filename does not match request_id: {}".format(path))
    response = record.get("response_json")
    usage = response.get("usage") if isinstance(response, dict) else None
    tokens = {name: token_value(usage, keys) for name, keys in TOKEN_PATHS.items()}
    selected_reasoning = next((tokens[name] for name in (
        "completion_details_reasoning_tokens", "output_details_reasoning_tokens",
        "top_level_reasoning_tokens",
    ) if tokens[name] is not None), None)
    tokens["selected_reasoning_tokens"] = selected_reasoning
    reason_values = {tokens[name] for name in (
        "completion_details_reasoning_tokens", "output_details_reasoning_tokens",
        "top_level_reasoning_tokens",
    ) if tokens[name] is not None}
    choices = response.get("choices", []) if isinstance(response, dict) else []
    if not isinstance(choices, list):
        raise ValueError("Response choices is not a list: {}".format(path))
    reasoning_texts = []
    for choice in choices:
        if not isinstance(choice, dict):
            raise ValueError("Response choice is not an object: {}".format(path))
        message = choice.get("message", {})
        if not isinstance(message, dict):
            raise ValueError("Response message is not an object: {}".format(path))
        reasoning = message.get("reasoning_content")
        if reasoning is not None and not isinstance(reasoning, str):
            raise ValueError("reasoning_content is not a string: {}".format(path))
        reasoning_texts.append(reasoning or "")
    return {
        "request_id": request_id,
        "state": record.get("state"),
        "attempt": record.get("attempt"),
        "client_id": record.get("client_id"),
        "generation_id": record.get("generation_id"),
        "tokens": tokens,
        "usage_object_present": isinstance(usage, dict),
        "reasoning_token_fields_conflict": len(reason_values) > 1,
        "reasoning_content_chars": sum(len(value) for value in reasoning_texts),
        "nonempty_reasoning_content": any(reasoning_texts),
        "choice_count": len(choices),
        "wall_time_seconds": record.get("wall_time_seconds"),
    }


def aggregate(request_ids, records, scope_complete):
    selected = [records[request_id] for request_id in request_ids]
    states = dict(sorted(collections.Counter(item["state"] for item in selected).items()))
    terminal = all(item["state"] in ("success", "error") for item in selected)
    token_summary = {}
    token_names = list(TOKEN_PATHS) + ["selected_reasoning_tokens"]
    for name in token_names:
        values = [item["tokens"][name] for item in selected]
        present = [value for value in values if value is not None]
        token_summary[name] = {
            "known_sum": sum(present),
            "reported_attempts": len(present),
            "missing_attempts": len(values) - len(present),
            "complete_total": sum(present) if len(values) == len(present) and terminal and scope_complete else None,
            "nonzero_reported_attempts": sum(value != 0 for value in present),
        }
    consistency_failures = []
    for item in selected:
        values = item["tokens"]
        if all(values[name] is not None for name in ("input_tokens", "output_tokens", "provider_total_tokens")):
            if values["input_tokens"] + values["output_tokens"] != values["provider_total_tokens"]:
                consistency_failures.append(item["request_id"])
    return {
        "unique_requests": len(selected),
        "unique_logical_generations": len({(item["client_id"], item["generation_id"]) for item in selected}),
        "states": states,
        "all_requests_terminal": terminal,
        "attempt_numbers": dict(sorted(collections.Counter(str(item["attempt"]) for item in selected).items())),
        "usage_object_present_attempts": sum(item["usage_object_present"] for item in selected),
        "usage_object_missing_attempts": sum(not item["usage_object_present"] for item in selected),
        "tokens": token_summary,
        "reasoning_token_fields_conflict_attempts": sum(item["reasoning_token_fields_conflict"] for item in selected),
        "nonempty_reasoning_content_attempts": sum(item["nonempty_reasoning_content"] for item in selected),
        "reasoning_content_chars": sum(item["reasoning_content_chars"] for item in selected),
        "top_level_reasoning_zero_with_nonempty_text_attempts": sum(
            item["tokens"]["top_level_reasoning_tokens"] == 0 and item["nonempty_reasoning_content"] for item in selected
        ),
        "response_choice_counts": dict(sorted(collections.Counter(str(item["choice_count"]) for item in selected).items())),
        "prompt_plus_completion_vs_total_mismatch_request_ids": consistency_failures,
        "request_wall_time_seconds_known_sum": sum(
            item["wall_time_seconds"] for item in selected
            if isinstance(item["wall_time_seconds"], (int, float)) and not isinstance(item["wall_time_seconds"], bool)
        ),
        "request_wall_time_seconds_missing_attempts": sum(item["wall_time_seconds"] is None for item in selected),
    }


def scan(base):
    records, snapshots, directory_snapshots = {}, {}, {}
    sources, source_sets, path_memberships = {}, {}, collections.defaultdict(list)
    path_cache = {}
    raw_hashes, locations = {}, collections.defaultdict(set)
    temporary_files = set()
    for stage in STAGES:
        manifest_path = (base / "runs" / stage / "manifest.json").resolve()
        manifest, manifest_sha, manifest_size = read_json(manifest_path, snapshots)
        unique_paths = set()
        missing_dirs, directory_jobs = [], collections.defaultdict(list)
        for job in manifest["jobs"]:
            dump_dir = pathlib.Path(job["dump_dir"])
            if not dump_dir.is_absolute():
                raise ValueError("Relative dump_dir has undefined scope: {}".format(dump_dir))
            directory_jobs[str(dump_dir.absolute())].append(job["id"])
        extras = []
        for directory_name, job_ids in sorted(directory_jobs.items()):
            directory = pathlib.Path(directory_name)
            if not directory.exists():
                missing_dirs.append({"path": directory_name, "job_ids": job_ids})
                directory_snapshots[directory_name] = None
                continue
            entries = sorted(str(path) for path in directory.iterdir())
            previous = directory_snapshots.setdefault(directory_name, entries)
            if previous != entries:
                raise ValueError("Directory changed between manifest scans: {}".format(directory))
            for filename in entries:
                path = pathlib.Path(filename)
                if path.suffix != ".json" or not path.is_file():
                    extras.append(filename)
                    if ".tmp" in path.name:
                        temporary_files.add(filename)
                    continue
                unique_paths.add(filename)
                path_memberships[filename].append({"stage": stage, "job_ids": job_ids})
        request_ids = set()
        for filename in sorted(unique_paths):
            if filename not in path_cache:
                path = pathlib.Path(filename)
                record, sha, size = read_json(path, snapshots)
                compact = summarize_record(record, path)
                request_id = compact["request_id"]
                if request_id in raw_hashes and raw_hashes[request_id] != sha:
                    raise ValueError("Same request_id has different raw bytes: {} {}".format(request_id, filename))
                raw_hashes[request_id] = sha
                records.setdefault(request_id, compact)
                locations[request_id].add(filename)
                path_cache[filename] = {"request_id": request_id, "sha256": sha, "size_bytes": size}
            request_ids.add(path_cache[filename]["request_id"])
        source_sets[stage] = request_ids
        sources[stage] = {
            "manifest_path": str(manifest_path), "manifest_sha256": manifest_sha,
            "manifest_size_bytes": manifest_size,
            "manifest_stage": manifest.get("stage"), "run_namespace": manifest.get("run_namespace"),
            "job_count": len(manifest["jobs"]), "unique_dump_directories": len(directory_jobs),
            "existing_dump_directories": len(directory_jobs) - len(missing_dirs),
            "missing_dump_directories": missing_dirs,
            "raw_file_locations": len(unique_paths), "unique_request_ids": len(request_ids),
            "non_json_or_non_file_entries": extras,
        }
    for filename, before in snapshots.items():
        if stable_stat(pathlib.Path(filename)) != before:
            raise ValueError("Input changed after reading: {}".format(filename))
    for directory_name, before in directory_snapshots.items():
        directory = pathlib.Path(directory_name)
        after = sorted(str(path) for path in directory.iterdir()) if directory.exists() else None
        if before != after:
            raise ValueError("Input directory changed after reading: {}".format(directory_name))
    complete = not temporary_files
    for stage, source in sources.items():
        source["totals"] = aggregate(source_sets[stage], records, complete)
    versions = {
        "v1": source_sets["smoke"] | source_sets["pilot"] | source_sets["full"],
        "v2": source_sets["smoke_v2"] | source_sets["pilot_v2"] | source_sets["full_v2"],
        "v3": source_sets["smoke_v3"] | source_sets["pilot_v3"] | source_sets["full_v3"],
    }
    promotion_overlaps = {}
    for version, suffix in (("v1", ""), ("v2", "_v2"), ("v3", "_v3")):
        pilot = source_sets["pilot" + suffix]
        full = source_sets["full" + suffix]
        promotion_overlaps[version] = {
            "pilot_unique_requests": len(pilot), "full_unique_requests": len(full),
            "shared_request_ids_with_identical_bytes": len(pilot & full),
            "pilot_only_request_ids": len(pilot - full), "full_only_request_ids": len(full - pilot),
        }
    return {
        "schema_version": "kimi_k3.independent_project_attempt_review.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_script": {"path": str(pathlib.Path(__file__).resolve()), "sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()},
        "scope": {
            "included": "Only direct *.json files in jobs[].dump_dir from the nine explicitly named manifests; includes all retained historical/failed/unselected sessions in those directories.",
            "excluded": "Service probes, health checks, service warm-up, and any API calls outside these manifest job dump directories. Not a complete service-lifetime billing statement.",
            "deduplication": "Exact request_id equality and original-byte SHA256 equality; differing bytes for one request_id fail. No content/similarity deduplication.",
            "missing_directories": "Reported as no retained dump directory, not proof of zero calls or successful matrix completion.",
        },
        "input_snapshot_stable": True,
        "temporary_files": sorted(temporary_files),
        "inventory_complete_for_retained_json_files": complete,
        "benchmark_results_validated": False,
        "sources": sources,
        "all_manifests_raw_file_memberships": sum(source["raw_file_locations"] for source in sources.values()),
        "unique_raw_file_locations": len(path_cache),
        "unique_request_ids": len(records),
        "duplicate_copy_locations": len(path_cache) - len(records),
        "duplicate_request_id_different_bytes_conflicts": 0,
        "physical_paths_shared_by_multiple_manifests": {path: refs for path, refs in path_memberships.items() if len({ref["stage"] for ref in refs}) > 1},
        "promotion_overlaps": promotion_overlaps,
        "generation_unique_request_ids": {version: len(ids) for version, ids in versions.items()},
        "cross_generation_shared_request_ids": {
            "v1_v2": len(versions["v1"] & versions["v2"]),
            "v1_v3": len(versions["v1"] & versions["v3"]),
            "v2_v3": len(versions["v2"] & versions["v3"]),
        },
        "totals": aggregate(set(records), records, complete),
        "notes": [
            "Token missing/null fields are not zero; known sums and complete totals are separate.",
            "Reasoning token fields and reasoning text are independent observations; provider-reported zero does not mean absent reasoning text.",
            "reasoning_content_chars sums string lengths over all response choices; nonempty is literal string length > 0, without whitespace stripping.",
            "Request wall time sums overlap for concurrent calls and are neither elapsed time nor GPU-hours.",
            "Stage totals overlap because promoted pilot raw files are copied into full; only project-level request_id dedup totals may be used as the combined total.",
            "This script neither imports nor calls inventory_project_attempts.py or audit_dumps.py.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path(__file__).with_name("independent_project_usage.json"))
    args = parser.parse_args()
    report = scan(args.base.resolve())
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"report": str(args.output.resolve()), "unique_request_ids": report["unique_request_ids"], "unique_raw_file_locations": report["unique_raw_file_locations"], "totals": report["totals"]}, ensure_ascii=False))
    if not report["totals"]["all_requests_terminal"] or not report["inventory_complete_for_retained_json_files"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
