#!/usr/bin/env python3
"""Verify the closed public operations bundle using only its published files.

This checks hashes, identities and public ledger arithmetic. It does not replay
private model requests or claim to reperform the separate source-record audit.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path, PurePosixPath


ALIASES = {
    "gemini-3.8-flash-medium": "gemini", "gpt-5.6-sol": "gpt",
    "glm-5.3": "glm", "kimi-k3": "kimi",
    "qwen3.8-2.4t-a95b-fp8": "qwen", "deepseek-v4-flash-0731": "deepseek",
}
REGISTERED = {"main": (97, 388), "aux": (22, 79)}
RESOURCE_GPUS = {"glm": 16, "kimi": 16, "qwen": 32, "deepseek": 8}
TERMINAL = {"COMPLETED", "CANCELLED", "FAILED", "TIMEOUT", "NODE_FAIL",
            "OUT_OF_MEMORY", "BOOT_FAIL", "DEADLINE", "PREEMPTED", "REVOKED"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def relative_path(value):
    need(isinstance(value, str) and value and "\\" not in value, "Invalid relative path")
    path = PurePosixPath(value)
    need(not path.is_absolute() and ".." not in path.parts and "." not in path.parts,
         "Manifest path must be relative and normalized")
    need(path.as_posix() == value, "Manifest path must be normalized")
    return path


def read_json(path):
    def reject_constant(_):
        raise ValueError("Non-finite JSON number")
    def no_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant,
                      object_pairs_hook=no_duplicate_keys)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        need(reader.fieldnames and len(set(reader.fieldnames)) == len(reader.fieldnames),
             "Missing or duplicate CSV columns")
        result = list(reader)
    need(all(None not in row and None not in row.values() for row in result),
         "Malformed CSV record")
    return result


def number(value, label, *, nullable=True):
    if value is None or value == "":
        need(nullable, label + " must not be null")
        return None
    need(not isinstance(value, bool), label + " cannot be boolean")
    result = float(value)
    need(math.isfinite(result), label + " must be finite")
    return result


def integer(value, label, *, nullable=False):
    result = number(value, label, nullable=nullable)
    if result is None:
        return None
    need(result.is_integer() and result >= 0, label + " must be a nonnegative integer")
    return int(result)


def boolean(value, label):
    if value is True or value == "True":
        return True
    if value is False or value == "False":
        return False
    raise ValueError(label + " must be boolean")


def same_number(actual, expected, label):
    actual = number(actual, label)
    expected = number(expected, label)
    if actual is None or expected is None:
        need(actual is None and expected is None, label + " null/value mismatch")
    else:
        need(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-9),
             label + " numeric mismatch")


def reported_sum(values):
    present = [number(value, "reported cost") for value in values if value is not None and value != ""]
    need(all(value >= 0 for value in present), "Negative reported cost")
    return math.fsum(present) if present else None


def check_file(root, name, entry):
    path = root.joinpath(*relative_path(name).parts)
    need(path.is_file() and not path.is_symlink(), "Missing regular file: " + name)
    raw = path.read_bytes()
    need(type(entry.get("bytes")) is int and entry["bytes"] == len(raw), "File size mismatch: " + name)
    need(entry.get("sha256") == digest(raw), "File SHA256 mismatch: " + name)


def check_manifests(root):
    manifest = read_json(root / "MANIFEST.json")
    files = manifest["files"]
    need(isinstance(files, dict) and files, "Empty root manifest")
    need("MANIFEST.json" not in files and "ALLOWLIST.json" in files, "Root manifest ownership mismatch")
    actual = set()
    for path in root.rglob("*"):
        need(not path.is_symlink(), "Bundle must not contain symlinks")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    need(actual == set(files) | {"MANIFEST.json"}, "Root manifest does not close the actual file set")
    need(manifest["closed_file_count"] == len(actual), "Root closed file count mismatch")
    for name, entry in files.items():
        check_file(root, name, entry)
    allowlist = read_json(root / "ALLOWLIST.json")
    need(manifest["allowlist_sha256"] == digest((root / "ALLOWLIST.json").read_bytes()),
         "Allowlist hash mismatch")
    entries = allowlist["entries"]
    destinations = [entry["destination"] for entry in entries]
    need(len(set(destinations)) == len(destinations), "Duplicate allowlist destination")
    need(set(destinations) == set(files) - {"ALLOWLIST.json"}, "Allowlist does not close payload files")
    need(allowlist["payload_file_count"] == len(entries), "Payload file count mismatch")
    need(allowlist["closed_file_count"] == len(actual), "Allowlist closed file count mismatch")
    for entry in entries:
        check_file(root, entry["destination"], {"bytes": entry["destination_bytes"],
                                                "sha256": entry["destination_sha256"]})
    for scope in ("main", "aux", "resource_usage"):
        inner = read_json(root / scope / "MANIFEST.json")
        for name, entry in inner["files"].items():
            check_file(root / scope, name, entry)
    return manifest, len(actual)


def verify_scope(root, scope):
    directory = root / scope
    slot_name = "pool_run_ledger.csv" if scope == "main" else "slot_run_ledger.csv"
    slots = read_csv(directory / slot_name)
    attempts = read_csv(directory / "request_attempt_ledger.csv")
    profiles = read_json(directory / "request_profiles.json")
    summary = read_json(directory / "USAGE_SUMMARY.json")
    expected_slots, expected_agents = REGISTERED[scope]
    need(len(slots) == expected_slots, scope + " registered slot count mismatch")
    by_job = {row["job_id"]: row for row in slots}
    need(len(by_job) == len(slots) and all(by_job), scope + " duplicate/empty job identity")
    need(len({row["old_slot_id"] for row in slots}) == len(slots), scope + " duplicate old slot")
    need(all(row["model"] in ALIASES for row in slots), scope + " unknown model")
    agents = sum(integer(row["agents"], "agent count") for row in slots)
    need(agents == expected_agents, scope + " registered agent count mismatch")
    if scope == "main":
        need(all(row["agents"] == "4" for row in slots), "Main slots must be whole four-agent pools")
    else:
        need(sum(row["runner"] == "poolact" for row in slots) == 19, "Aux whole pool count mismatch")
        need(sum(row["runner"] == "expgym" for row in slots) == 3, "Aux N1 count mismatch")
        need(sum(row["old_slot_id"].startswith("whois:") for row in slots) == 1, "Aux sweep cohort mismatch")
        for row in slots:
            selection = json.loads(row["selection_json"])
            if row["runner"] == "expgym":
                need(row["agents"] == "1", "N1 member count mismatch")
                need(row["requested_model"] == selection["model_id"], "N1 requested model mismatch")
                need(row["scenario"] == selection["scenario"] and row["regime"] == selection["cost_regime"],
                     "N1 scenario/budget identity mismatch")
                same_number(row["seed"], selection["seed"], "N1 seed")
                same_number(row["beta"], selection["beta"], "N1 custom beta")
            else:
                need(row["agents"] == "4", "Aux pool member count mismatch")
    for key, profile in profiles.items():
        need(key == digest(json.dumps(profile, sort_keys=True).encode()), "Request profile hash mismatch")
    grouped = collections.defaultdict(list)
    request_ids, logical_attempts, used_profiles = set(), set(), set()
    for attempt in attempts:
        job_id = attempt["job_id"]
        need(job_id in by_job, scope + " request references unknown slot")
        slot = by_job[job_id]
        need(attempt["old_slot_id"] == slot["old_slot_id"] and attempt["model"] == slot["model"],
             "Request source identity mismatch")
        request_id, generation_id = attempt["request_id"], attempt["generation_id"]
        need(request_id and request_id not in request_ids and generation_id, "Duplicate/empty request identity")
        request_ids.add(request_id)
        index = integer(attempt["attempt"], "HTTP attempt index")
        maximum = integer(attempt["max_attempts"], "maximum HTTP attempts")
        need(1 <= index <= maximum, "HTTP attempt index outside configured range")
        logical_key = (job_id, generation_id, index)
        need(logical_key not in logical_attempts, "Duplicate generation attempt")
        logical_attempts.add(logical_key)
        profile_id = attempt["request_profile_sha256"]
        need(profile_id in profiles, "Request references missing profile")
        profile = profiles[profile_id]
        used_profiles.add(profile_id)
        need(profile.get("model") == slot["requested_model"], "Requested profile model mismatch")
        same_number(attempt["wire_seed"], profile.get("seed"), "Wire/profile seed")
        context_seed = integer(attempt["context_seed"], "context seed", nullable=True)
        member = integer(attempt["context_agent_id"], "context member", nullable=True)
        if member is not None:
            need(member < integer(slot["agents"], "agent count"), "Context member outside pool")
        if context_seed is not None:
            need(context_seed == integer(slot["seed"], "slot seed") + (member or 0), "Context/slot seed mismatch")
        need(bool(attempt["state"]), "Empty request state")
        final = boolean(attempt["raw_record_final"], "raw record final")
        receipt = boolean(attempt["queue_artifact_verified"], "queue artifact verified")
        need(final == (attempt["state"] != "in_progress"), "Request final state mismatch")
        need(not receipt or final, "In-progress request cannot be receipt verified")
        if slot["status"] == "validated_complete":
            need(final and receipt, "Complete slot contains an unsealed request")
        grouped[job_id].append(attempt)
    need(used_profiles == set(profiles), "Unreferenced request profiles")
    for slot in slots:
        rows = grouped[slot["job_id"]]
        counts = {"http_attempts": len(rows),
                  "successful_http_attempts": sum(row["state"] == "success" for row in rows),
                  "error_http_attempts": sum(row["state"] not in ("success", "in_progress") for row in rows),
                  "logical_generations": len({row["generation_id"] for row in rows}),
                  "cost_report_count": sum(row["reported_cost_usd"] != "" for row in rows)}
        for field, value in counts.items():
            need(integer(slot[field], field) == value, scope + " slot count mismatch: " + field)
        same_number(slot["reported_cost_usd"], reported_sum(row["reported_cost_usd"] for row in rows),
                    "slot reported cost")
        attempt_field = "whole_pool_attempt" if scope == "main" else "whole_slot_attempt"
        need(integer(slot[attempt_field], attempt_field) == 1, "Unexpected whole-slot attempt count")
        if slot["status"] == "validated_complete":
            need(rows and slot["result_sha256"] and slot["completion_receipt_sha256"], "Incomplete completion identity")
    count_field, validated_field = (("pools", "validated_pools") if scope == "main"
                                    else ("slots", "validated_slots"))
    validated = sum(row["status"] == "validated_complete" for row in slots)
    need(summary[count_field] == len(slots) and summary[validated_field] == validated,
         scope + " summary slot count mismatch")
    need(summary["attempt_records"] == len(attempts), scope + " summary request count mismatch")
    need(summary["all_complete"] is (validated == len(slots)), scope + " summary completion mismatch")
    aliases = {ALIASES[row["model"]] for row in slots}
    need(set(summary["models"]) == aliases, scope + " summary model set mismatch")
    model_results = {}
    for alias in sorted(aliases):
        rows = [row for row in slots if ALIASES[row["model"]] == alias]
        model = summary["models"][alias]
        counts = {"planned": len(rows), "validated": sum(row["status"] == "validated_complete" for row in rows),
                  "http_attempts": sum(integer(row["http_attempts"], "HTTP attempts") for row in rows),
                  "error_http_attempts": sum(integer(row["error_http_attempts"], "HTTP errors") for row in rows)}
        for field, value in counts.items():
            need(model[field] == value, scope + " model summary mismatch: " + field)
        cost = reported_sum(row["reported_cost_usd"] for row in rows)
        same_number(model["reported_cost_usd"], cost, "model reported cost")
        model_results[alias] = {**counts, "reported_cost_usd": cost}
    return {"registered_slots": len(slots), "validated_slots": validated, "agent_slots": agents,
            "http_attempts": len(attempts),
            "error_http_attempts": sum(row["state"] not in ("success", "in_progress") for row in attempts),
            "reported_cost_usd": reported_sum(row["reported_cost_usd"] for row in attempts),
            "all_complete": validated == len(slots), "models": model_results,
            "job_ids": set(by_job), "old_slot_ids": {row["old_slot_id"] for row in slots}}


def verify_resource(root):
    directory = root / "resource_usage"
    value = read_json(directory / "RESOURCE_USAGE.json")
    rows = read_csv(directory / "resource_usage.csv")
    jobs = value["jobs"]
    need(len(jobs) == value["expected_jobs"] == len(rows) == 4, "Resource job count mismatch")
    by_id = {row["job_id"]: row for row in rows}
    need(len(by_id) == 4 and len({job["job_id"] for job in jobs}) == 4, "Duplicate resource job")
    need({job["model"] for job in jobs} == set(RESOURCE_GPUS), "Resource model set mismatch")
    hours = []
    for job in jobs:
        need(job["job_id"] in by_id, "Resource CSV/JSON job mismatch")
        row = by_id[job["job_id"]]
        need(set(row) == set(job), "Resource CSV/JSON columns differ")
        for key, item in job.items():
            if item is None:
                need(row[key] == "", "Null resource field must stay empty")
            elif isinstance(item, bool):
                need(boolean(row[key], key) is item, "Resource boolean mismatch")
            elif isinstance(item, (int, float)):
                same_number(row[key], item, "resource " + key)
            else:
                need(row[key] == item, "Resource text field mismatch")
        gpu = integer(job["gpu_count"], "allocated GPUs", nullable=True)
        elapsed = integer(job["elapsed_allocation_seconds"], "elapsed allocation", nullable=True)
        if gpu is not None:
            need(gpu == RESOURCE_GPUS[job["model"]], "Resource allocated GPU count mismatch")
        requested = integer(job["requested_gpu_count"], "requested GPUs", nullable=True)
        if requested is not None:
            need(requested == RESOURCE_GPUS[job["model"]], "Resource requested GPU count mismatch")
        expected = gpu * elapsed / 3600 if gpu is not None and elapsed is not None else None
        same_number(job["gpu_allocation_hours"], expected, "resource GPU hours")
        if job["state"] == "PENDING" or job["start_at_utc"] is None:
            need(gpu is None and elapsed is None and expected is None, "Pending/unknown resource must not imply usage")
        need(job["reported_cost_usd"] is None, "GPU allocation must not be priced in USD")
        if job["allocation_final"]:
            need(job["state"] in TERMINAL and job["end_at_utc"] is not None
                 and job["start_at_utc"] is not None and expected is not None
                 and job["allocation_history_review_required"] is False
                 and job["ownership_verified"] is True
                 and job["accounting_record_present"] is True,
                 "Resource marked final without a settled allocation")
        if expected is not None:
            hours.append(expected)
    all_final = all(job["allocation_final"] for job in jobs)
    need(value["all_allocations_final"] is all_final, "Resource final summary mismatch")
    need(value["verified_accounting_jobs"] == sum(job["ownership_verified"] for job in jobs),
         "Resource ownership summary mismatch")
    need(value["gpu_allocation_hours_complete"] is (len(hours) == len(jobs)), "Resource known-hours coverage mismatch")
    same_number(value["known_gpu_allocation_hours"], math.fsum(hours) if hours else None, "Resource total GPU hours")
    need(value["reported_cost_usd"] is None, "Resource total USD must stay null")
    inner = read_json(directory / "MANIFEST.json")
    need(inner["all_allocations_final"] is all_final, "Resource manifest final mismatch")
    checks = read_json(directory / "CHECKS.json")
    need(checks["passed"] is True and checks["exporter_sha256"] == inner["exporter_sha256"],
         "Resource exporter checks do not match frozen exporter")
    return {"jobs": len(jobs), "all_final": all_final,
            "known_gpu_allocation_hours": math.fsum(hours) if hours else None,
            "hours_complete": len(hours) == len(jobs), "reported_cost_usd": None}


def verify_audit(root):
    review = read_json(root / "audit" / "INDEPENDENT_REVIEW.json")
    reexport = read_json(root / "audit" / "REEXPORT_REVIEW.json")
    need(review["passed"] is True and not review.get("issues"), "Independent source review did not pass")
    need(reexport["passed"] is True, "Independent reexport review did not pass")
    counts = {}
    for scope, audit_scope in (("main", "hpo"), ("aux", "aux")):
        original, replay = review["ledgers"][audit_scope], reexport["results"][audit_scope]
        need(replay["passed"] is True and replay["manifest_all_files_verified"] is True,
             "Scope reexport review did not pass")
        need(original["snapshot_manifest_sha256"] == replay["before_manifest_sha256"],
             "Audit snapshot/reexport source mismatch")
        need(replay["after_manifest_sha256"] == digest((root / scope / "MANIFEST.json").read_bytes()),
             "Audit reexport does not bind current public ledger")
        inner = read_json(root / scope / "MANIFEST.json")
        need(original["exporter_sha256"] == replay["exporter_sha256"] == inner["exporter_sha256"],
             "Audit exporter version mismatch")
        count = integer(original["completed_slots_fully_audited"], "audited completed slots")
        need(count <= REGISTERED[scope][0], "Audit exceeds registered cohort")
        need(replay["sealed_slots_byte_value_equal"] == count, "Reexport audited slot count mismatch")
        need(replay["sealed_attempt_rows_byte_value_equal"] == original["completed_attempt_rows_fully_audited"],
             "Reexport audited request count mismatch")
        counts[scope] = count
    return {"passed": True, "source_audited_slots": counts,
            "full_cohort_coverage": all(counts[name] == REGISTERED[name][0] for name in REGISTERED)}


def verify(root: Path, require_complete: bool = False) -> dict:
    root = Path(root)
    manifest, file_count = check_manifests(root)
    scopes = {scope: verify_scope(root, scope) for scope in REGISTERED}
    need(not scopes["main"]["job_ids"] & scopes["aux"]["job_ids"], "Cross-cohort duplicate job")
    need(not scopes["main"]["old_slot_ids"] & scopes["aux"]["old_slot_ids"], "Cross-cohort duplicate source slot")
    for scope in scopes.values():
        scope.pop("job_ids")
        scope.pop("old_slot_ids")
    resource = verify_resource(root)
    audit = verify_audit(root)
    ready = (all(scope["all_complete"] for scope in scopes.values())
             and audit["full_cohort_coverage"] and resource["all_final"])
    complete = boolean(manifest["complete"], "Root complete")
    # An explicitly requested preview may stay incomplete even when ready.
    need(not complete or ready, "Root completion claim exceeds frozen evidence")
    status = read_json(root / "DELIVERY_STATUS.json")
    need(status["complete"] is complete, "Delivery status/root completion mismatch")
    expected_status = "final" if complete else "partial_preview_not_final"
    need(status["status"] == expected_status, "Delivery status label mismatch")
    for field, value in {
            "registered_slots": 119, "registered_agent_members": 467,
            "hpo_slots": 97, "aux_slots": 22,
            "validated_slots": sum(x["validated_slots"] for x in scopes.values()),
            "attempt_records": sum(x["http_attempts"] for x in scopes.values()),
            "http_error_attempts": sum(x["error_http_attempts"] for x in scopes.values())}.items():
        need(status[field] == value, "Delivery aggregate mismatch: " + field)
    need(status["resource_all_final"] is resource["all_final"], "Delivery resource completion mismatch")
    need(status["model_calls_by_packager"] == 0, "Packager must not invoke models")
    aliases = set().union(*(set(scope["models"]) for scope in scopes.values()))
    need(set(status["reported_cost_usd_by_model"]) == aliases, "Delivery cost model set mismatch")
    for alias in aliases:
        expected_cost = reported_sum(scope["models"][alias]["reported_cost_usd"]
                                     for scope in scopes.values() if alias in scope["models"])
        same_number(status["reported_cost_usd_by_model"][alias], expected_cost,
                    "Delivery model reported cost")
    need(not require_complete or complete, "Public bundle is verified but not yet complete")
    return {"schema": "expgym.public-operations-replay.v1", "passed": True,
            "closed_files": file_count, "registered_slots": sum(x["registered_slots"] for x in scopes.values()),
            "validated_slots": sum(x["validated_slots"] for x in scopes.values()),
            "agent_slots": sum(x["agent_slots"] for x in scopes.values()),
            "http_attempts": sum(x["http_attempts"] for x in scopes.values()),
            "error_http_attempts": sum(x["error_http_attempts"] for x in scopes.values()),
            "reported_cost_usd": reported_sum(x["reported_cost_usd"] for x in scopes.values()),
            "complete": complete, "ready_for_final": ready,
            "scopes": scopes, "resource": resource, "audit": audit,
            "private_source_replayed": False, "model_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    result = verify(args.root, require_complete=args.require_complete)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
