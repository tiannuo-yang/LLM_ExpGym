#!/usr/bin/env python3
"""Inventory every retained API attempt across any number of study manifests.

Includes failed runs and historical client sessions. Identical promoted copies
are counted once by request_id; conflicting bytes for one ID fail the inventory.
No APIs are called, no benchmark scores are evaluated, and no inputs are edited.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

import audit_dumps as audit


TOKEN_FIELDS = ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_input_tokens", "reasoning_tokens")
CSV_FIELDS = (
    "request_id", "sha256", "run_id", "client_id", "generation_id", "attempt", "max_attempts",
    "state", "http_status", "started_at_utc", "finished_at_utc", "wall_time_seconds",
    "will_retry", "retry_delay_seconds", "model", "seed", "max_tokens", "chat_template_kwargs",
    "input_tokens", "output_tokens", "cached_input_tokens", "cache_write_input_tokens", "reasoning_tokens",
    "reasoning_tokens_selected_source", "reasoning_token_sources_conflict", "reasoning_content_chars",
    "nonempty_reasoning_content", "finish_reason", "error_type", "location_count", "source_count",
    "source_ids", "locations", "reasoning_warnings",
)


def stamp(path):
    info = Path(path).stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def read_snapshot(path):
    path = Path(path)
    before = stamp(path)
    raw = path.read_bytes()
    audit.require(stamp(path) == before, "input changed while being read: " + str(path))

    def reject(_value):
        raise ValueError("non-finite JSON")

    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=reject)
        json.dumps(value, allow_nan=False)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("input is not strict JSON: " + str(path)) from None
    return value, hashlib.sha256(raw).hexdigest(), before


def validate_attempt(record):
    audit.require(isinstance(record, dict) and record.get("schema_version") == audit.SCHEMA, "unknown API attempt schema")
    if record.get("state") != "in_progress":
        audit.audit_attempt(record)
        return
    # A project inventory can describe an unfinished snapshot. The result audit
    # intentionally rejects this state, so validate its pending shape here.
    audit.require(not any(key.startswith("_") for key in record), "reserved raw attempt field")
    for field in ("request_id", "generation_id", "client_id", "run_id"):
        audit.require(isinstance(record.get(field), str) and record[field], "pending attempt lacks " + field)
    for field in ("pid", "thread_id"):
        audit.require(audit.token(record.get(field)) and record[field] > 0, "pending attempt lacks " + field)
    audit.require(isinstance(record.get("context"), dict), "pending context missing")
    audit.require(audit.token(record.get("attempt")) and record["attempt"] > 0, "invalid pending attempt number")
    audit.require(audit.token(record.get("max_attempts")) and record["max_attempts"] >= record["attempt"], "invalid pending attempt limit")
    audit.require(isinstance(record.get("request_payload"), dict), "pending request payload missing")
    audit.require(isinstance(record["request_payload"].get("model"), str)
                  and record["request_payload"]["model"], "pending request model missing")
    audit.messages_projection(record["request_payload"].get("messages"))
    audit.timestamp(record.get("started_at_utc"))
    audit.require(all(field in record for field in ("finished_at_utc", "response_raw", "response_json", "error")), "pending response fields missing")
    audit.require(record.get("finished_at_utc") is None and record.get("response_raw") is None
                  and record.get("response_json") is None and record.get("error") is None, "pending attempt contains final response data")
    audit.require(record.get("http_status") is None and record.get("will_retry") is False
                  and record.get("retry_delay_seconds") is None, "pending attempt has a terminal or retry disposition")
    audit.require(audit.number(record.get("wall_time_seconds")) and record["wall_time_seconds"] >= 0, "invalid pending wall duration")


def accounting(records, scope_complete=True):
    """Expose provider-known sums without presenting unreported usage as zero."""
    totals = audit.totals(records)
    totals["states"] = dict(Counter(record["state"] for record in records))
    totals["all_requests_terminal"] = totals["in_progress_http_attempts"] == 0
    for field in TOKEN_FIELDS:
        known = totals.pop(field)
        reported = totals[field + "_reported_attempts"]
        fully_reported = reported == len(records) and totals["all_requests_terminal"] and scope_complete
        if field == "reasoning_tokens" and totals["reasoning_tokens_conflicting_attempts"]:
            fully_reported = False
        totals[field + "_known_sum"] = known
        totals[field + "_complete_total"] = known if fully_reported else None
        totals[field + "_unreported_attempts"] = len(records) - reported
    return totals


def csv_row(record, digest):
    payload = record["request_payload"]
    compact = audit.compact_attempt(record)
    normalized = audit.usage(record)
    reasoning = audit.reasoning_usage(record)
    error = record.get("error")
    row = {field: record.get(field) for field in CSV_FIELDS if field in record}
    row.update(sha256=digest, model=payload.get("model"), seed=payload.get("seed"),
               max_tokens=payload.get("max_tokens"), chat_template_kwargs=payload.get("chat_template_kwargs"),
               **normalized)
    row.update(reasoning_tokens_selected_source=reasoning["selected_source"],
               reasoning_token_sources_conflict=reasoning["conflict"],
               reasoning_content_chars=compact["_reasoning_chars"],
               nonempty_reasoning_content=(compact["_reasoning_chars"] or 0) > 0,
               finish_reason=compact["_finish_reason"], error_type=error.get("type") if isinstance(error, dict) else None,
               reasoning_warnings=audit.reasoning_warnings(record))
    return row, compact


def inventory(manifest_paths):
    sources, entries, locations, snapshots, directories, repeated_inputs = [], {}, {}, {}, {}, []
    source_paths = set()
    for given_path in manifest_paths:
        manifest_path = Path(given_path).resolve()
        if str(manifest_path) in source_paths:
            repeated_inputs.append(str(manifest_path))
            continue
        source_paths.add(str(manifest_path))
        manifest, manifest_hash, manifest_stamp = read_snapshot(manifest_path)
        audit.require(isinstance(manifest, dict) and isinstance(manifest.get("jobs"), list), "manifest jobs missing")
        snapshots[str(manifest_path)] = manifest_stamp
        source_id = "source_%03d" % (len(sources) + 1)
        source = {
            "source_id": source_id, "manifest_path": str(manifest_path), "manifest_sha256": manifest_hash,
            "stage": manifest.get("stage"), "run_namespace": manifest.get("run_namespace"),
            "source_tree_sha256": manifest.get("source_tree_sha256"),
            "backend": (manifest.get("settings") or {}).get("backend"),
            "model": (manifest.get("settings") or {}).get("model"),
            "manifest_jobs": len(manifest["jobs"]), "dump_directories": [],
            "_request_ids": set(), "_locations": set(), "_temporary_files": set(),
        }
        sources.append(source)
        for job in manifest["jobs"]:
            audit.require(isinstance(job, dict) and isinstance(job.get("dump_dir"), str), "manifest job dump_dir missing")
            directory = Path(job["dump_dir"]).absolute()
            directory_key = str(directory)
            audit.require(not directory.exists() or directory.is_dir(), "dump_dir is not a directory: " + directory_key)
            if directory_key not in directories:
                json_paths = sorted(str(path.absolute()) for path in directory.rglob("*.json"))
                temporary_paths = sorted(str(path.absolute()) for path in directory.rglob("*.tmp"))
                directories[directory_key] = {"exists": directory.is_dir(), "json_paths": json_paths,
                                              "temporary_paths": temporary_paths}
            found = directories[directory_key]
            source["dump_directories"].append({"job_id": job.get("id"), "path": directory_key,
                                                "exists": found["exists"], "json_files": len(found["json_paths"])})
            source["_temporary_files"].update(found["temporary_paths"])
            for path_text in found["json_paths"]:
                source["_locations"].add(path_text)
                if path_text not in locations:
                    record, digest, file_stamp = read_snapshot(path_text)
                    snapshots[path_text] = file_stamp
                    try:
                        validate_attempt(record)
                    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                        raise ValueError("invalid API attempt: " + path_text) from None
                    request_id = record["request_id"]
                    if request_id in entries:
                        audit.require(entries[request_id]["sha256"] == digest,
                                      "conflicting bytes for one request_id: " + entries[request_id]["first_location"] + " and " + path_text)
                    else:
                        row, compact = csv_row(record, digest)
                        entries[request_id] = {"sha256": digest, "first_location": path_text, "row": row,
                                               "compact": compact, "locations": set(), "source_ids": set()}
                    entries[request_id]["locations"].add(path_text)
                    locations[path_text] = {"path": path_text, "sha256": digest, "request_id": request_id,
                                            "size_bytes": file_stamp[2], "source_jobs": {}}
                location = locations[path_text]
                request_id = location["request_id"]
                location["source_jobs"].setdefault(source_id, set()).add(str(job.get("id")))
                entries[request_id]["source_ids"].add(source_id)
                source["_request_ids"].add(request_id)
    audit.require(sources, "at least one manifest is required")
    # Refuse a moving snapshot, including requests published while directories
    # were being scanned. A later invocation can inventory the completed files.
    for path, previous in snapshots.items():
        audit.require(stamp(path) == previous, "input changed during inventory: " + path)
    for path, previous in directories.items():
        directory = Path(path)
        audit.require(directory.is_dir() == previous["exists"]
                      and sorted(str(entry.absolute()) for entry in directory.rglob("*.json")) == previous["json_paths"]
                      and sorted(str(entry.absolute()) for entry in directory.rglob("*.tmp")) == previous["temporary_paths"],
                      "dump directory changed during inventory: " + path)
    rows = []
    for request_id, entry in sorted(entries.items()):
        row = dict(entry["row"])
        row["locations"] = [
            {"path": path, "sha256": locations[path]["sha256"], "size_bytes": locations[path]["size_bytes"],
             "sources": [{"source_id": source_id, "job_ids": sorted(job_ids)}
                         for source_id, job_ids in sorted(locations[path]["source_jobs"].items())]}
            for path in sorted(entry["locations"])
        ]
        row.update(source_ids=sorted(entry["source_ids"]), location_count=len(entry["locations"]),
                   source_count=len(entry["source_ids"]))
        rows.append(row)
    temporary_files = sorted({path for source in sources for path in source["_temporary_files"]})
    for source in sources:
        ids = source.pop("_request_ids")
        raw_locations = source.pop("_locations")
        source_temporary = source.pop("_temporary_files")
        source.update(unique_requests=len(ids), raw_file_locations=len(raw_locations),
                      duplicated_locations_within_source=len(raw_locations) - len(ids),
                      shared_requests_with_other_sources=sum(len(entries[request_id]["source_ids"]) > 1 for request_id in ids),
                      exclusive_requests=sum(len(entries[request_id]["source_ids"]) == 1 for request_id in ids),
                      missing_dump_directories=sum(not item["exists"] for item in source["dump_directories"]),
                      unfinalized_temporary_files=sorted(source_temporary),
                      totals=accounting([entries[request_id]["compact"] for request_id in sorted(ids)], not source_temporary))
    all_records = [entry["compact"] for entry in entries.values()]
    report = {
        "schema_version": "kimi_k3.project_attempt_inventory.v1", "created_at": datetime.now(timezone.utc).isoformat(),
        "inventory_complete": not temporary_files, "all_requests_terminal": all(record["state"] != "in_progress" for record in all_records),
        "benchmark_results_validated": False,
        "script_path": str(Path(__file__).resolve()), "script_sha256": audit.sha256(__file__),
        "accounting_helper_path": str(Path(audit.__file__).resolve()), "accounting_helper_sha256": audit.sha256(audit.__file__),
        "sources": sources, "repeated_manifest_arguments_ignored": repeated_inputs,
        "distinct_raw_file_locations": len(locations), "unique_requests": len(entries),
        "duplicate_raw_file_locations": len(locations) - len(entries),
        "overlapping_manifest_request_memberships": sum(source["unique_requests"] for source in sources) - len(entries),
        "conflicting_request_ids": 0, "unfinalized_temporary_files": temporary_files,
        "totals": accounting(all_records, not temporary_files),
        "notes": [
            "Scope is all retained API attempts under the supplied manifest dump directories, including historical sessions and runs with failed parsing or scoring.",
            "Serving acceptance probes and background health generations outside these manifest dump directories are excluded; this inventory is evaluation API usage, not every inference performed by the service. Slurm allocation accounting includes their occupied time.",
            "One request_id is counted once project-wide; every identical raw file location is retained in the CSV index. Different bytes for the same ID abort the inventory.",
            "Per-source totals deduplicate within that source but can overlap across sources; do not add them to obtain the project total.",
            "Token known_sum fields add only reported provider usage. complete_total is null if any selected attempt lacks that field, is unfinished, or the retained snapshot contains temporary files.",
            "Reasoning counts are provider-reported, not inferred from text. Reported zero can coexist with nonempty reasoning_content; reasoning tokens must not be added again to output tokens.",
            "Missing dump directories do not prove zero computation or successful benchmark completion; they only have no retained attempts in this snapshot.",
            "Request wall durations overlap during concurrent execution and exclude unrecorded server work; their sum is not project elapsed time or GPU-hours.",
        ],
    }
    return report, rows


def write_inventory(report, rows, output_dir):
    output_dir = Path(output_dir).absolute()
    output_dir.mkdir(parents=True, exist_ok=False)
    csv_path = output_dir / "unique_raw_requests.csv"
    descriptor, temporary = tempfile.mkstemp(prefix=".unique_raw_requests.", dir=str(output_dir))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
                                 if isinstance(value, (dict, list)) else value for key, value in row.items()})
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, str(csv_path))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    report["unique_raw_index"] = {"path": str(csv_path), "sha256": audit.sha256(csv_path), "rows": len(rows)}
    destination = output_dir / "project_usage_inventory.json"
    audit.write_json(destination, report)
    return destination


def self_test():
    def record(request_id, state="success", known=True):
        response = {"choices": [{"message": {"content": "Answer" if state == "success" else None, "reasoning_content": "think"}}]}
        if known:
            response["usage"] = {"prompt_tokens": 5, "completion_tokens": 3, "reasoning_tokens": 0}
        return {
            "schema_version": audit.SCHEMA, "request_id": request_id, "generation_id": request_id + "-generation",
            "client_id": "client-" + request_id, "run_id": "fixture", "attempt": 1, "max_attempts": 1,
            "pid": 1, "thread_id": 1, "context": {}, "state": state, "wall_time_seconds": .1,
            "request_payload": {"model": "fixture", "messages": [{"role": "user", "content": "Prompt"}]},
            "started_at_utc": "2026-09-07T00:00:00+00:00",
            "finished_at_utc": None if state == "in_progress" else "2026-09-07T00:00:01+00:00",
            "will_retry": False, "retry_delay_seconds": None,
            "error": {"type": "ValueError", "message": "fixture"} if state in {"error", "malformed_response"} else None,
            "response_json": None if state == "in_progress" else response,
            "response_raw": None if state == "in_progress" else json.dumps(response),
        }

    with tempfile.TemporaryDirectory(prefix="project-attempt-inventory-") as temporary:
        root = Path(temporary)
        for field in ("pid", "context"):
            malformed_pending = record("pending", "in_progress", False)
            malformed_pending.pop(field)
            try:
                validate_attempt(malformed_pending)
            except ValueError:
                pass
            else:
                raise AssertionError("self-test accepted incomplete pending metadata")
        malformed_pending = record("pending", "in_progress", False)
        malformed_pending.update(http_status=500, will_retry=True, retry_delay_seconds=-1)
        try:
            validate_attempt(malformed_pending)
        except ValueError:
            pass
        else:
            raise AssertionError("self-test accepted pending retry disposition")
        for source_name in ("one", "two"):
            audit.write_json(root / (source_name + ".json"), {"stage": source_name, "settings": {"backend": "openai"},
                "jobs": [{"id": "job", "dump_dir": str(root / source_name)}, {"id": "unrun", "dump_dir": str(root / "absent")} ]})
        shared = record("shared")
        for source_name in ("one", "two"):
            audit.write_json(root / source_name / "shared.json", shared)
        audit.write_json(root / "one/error.json", record("failed", "error", False))
        audit.write_json(root / "one/malformed.json", record("malformed", "malformed_response"))
        audit.write_json(root / "one/pending.json", record("pending", "in_progress", False))
        audit.write_json(root / "two/other.json", record("other"))
        report, rows = inventory([root / "one.json", root / "two.json", root / "one.json"])
        audit.require(report["unique_requests"] == 5 and report["distinct_raw_file_locations"] == 6
                      and report["duplicate_raw_file_locations"] == 1, "self-test deduplication")
        audit.require(report["totals"]["states"] == {"success": 2, "error": 1, "malformed_response": 1, "in_progress": 1}, "self-test attempt states")
        audit.require(report["totals"]["input_tokens_known_sum"] == 15 and report["totals"]["input_tokens_complete_total"] is None, "self-test unknown usage")
        audit.require(report["totals"]["nonempty_reasoning_content_attempts"] == 4
                      and report["totals"]["reasoning_tokens_known_sum"] == 0, "self-test reasoning text separation")
        audit.require(report["sources"][1]["totals"]["input_tokens_complete_total"] == 10, "self-test fully reported subset")
        audit.require(report["sources"][1]["totals"]["cache_write_input_tokens_complete_total"] is None, "self-test unreported cache is unknown")
        destination = write_inventory(report, rows, root / "output")
        saved = audit.strict_json(destination)
        with Path(saved["unique_raw_index"]["path"]).open(newline="", encoding="utf-8") as stream:
            index = list(csv.DictReader(stream))
        shared_row = next(row for row in index if row["request_id"] == "shared")
        audit.require(len(json.loads(shared_row["locations"])) == 2, "self-test location retention")
        audit.require((root / "one/shared.json").is_file() and (root / "two/shared.json").is_file(), "self-test preserved inputs")
        try:
            write_inventory(report, rows, root / "output")
        except FileExistsError:
            pass
        else:
            raise AssertionError("self-test overwrote existing output")
        conflict = record("shared")
        conflict["response_json"]["usage"]["prompt_tokens"] = 9
        conflict["response_raw"] = json.dumps(conflict["response_json"])
        audit.write_json(root / "two/shared.json", conflict)
        try:
            inventory([root / "one.json", root / "two.json"])
        except ValueError as error:
            audit.require("conflicting bytes" in str(error), "self-test wrong conflict failure")
        else:
            raise AssertionError("self-test accepted conflicting request bytes")
    return {"self_test": "passed", "cases": 13}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", help="repeat for smoke, pilot, full, and later reruns")
    parser.add_argument("--output-dir", type=Path, help="new directory; existing reports are never overwritten")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test()))
        return 0
    if not args.manifest or args.output_dir is None:
        parser.error("--manifest and --output-dir are required")
    try:
        report, rows = inventory(args.manifest)
        destination = write_inventory(report, rows, args.output_dir)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, "inventory failed: " + str(error) + "\n")
    print(json.dumps({"inventory_complete": report["inventory_complete"], "all_requests_terminal": report["all_requests_terminal"],
                      "unique_requests": report["unique_requests"], "duplicate_raw_file_locations": report["duplicate_raw_file_locations"],
                      "report": str(destination)}, ensure_ascii=False))
    return 0 if report["inventory_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
