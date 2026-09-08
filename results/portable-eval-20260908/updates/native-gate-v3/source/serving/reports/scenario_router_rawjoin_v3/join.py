#!/usr/bin/env python3
"""Offline v3 scenario byte join. Same checks as frozen v2 collector; revised historical limitations only."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact(path: Path) -> dict:
    return {"path": str(path.resolve()), "sha256": sha(path.read_bytes())}


def timestamp(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario-root", type=Path, required=True)
    p.add_argument("--router-jsonl", type=Path, required=True)
    p.add_argument("--completion-receipt", type=Path, required=True)
    p.add_argument("--static-acceptance", type=Path, required=True)
    p.add_argument("--client-source", type=Path, required=True)
    p.add_argument("--router-source", type=Path, required=True)
    p.add_argument("--capacity-receipt", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    # Prevent accidental replacement of evidence from an earlier observation.
    args.out.mkdir(parents=True, exist_ok=False)
    manifest_path = args.scenario_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    jobs = manifest["identity"]["jobs"]
    job_ids = {j["id"] for j in jobs}
    raw_router = args.router_jsonl.read_bytes()
    router_rows = [json.loads(line) for line in raw_router.splitlines() if line.strip()]
    pairs = defaultdict(list)
    for index, row in enumerate(router_rows):
        pairs[(row.get("payload_sha256"), row.get("response_sha256"))].append(index)
    inventory, errors, matched = [], [], set()
    states, per_replica, attempts, contexts = Counter(), Counter(), Counter(), Counter()
    client_http_statuses = Counter()
    acceptance = json.loads(args.static_acceptance.read_text())
    if acceptance["source_tree_sha256"] != manifest["identity"]["source_tree_sha256"]:
        errors.append({"kind": "static_acceptance_source_tree_mismatch"})
    if acceptance["files"]["expgym/llm_clients.py"] != sha(args.client_source.read_bytes()):
        errors.append({"kind": "client_source_differs_from_frozen_acceptance"})
    completion = json.loads(args.completion_receipt.read_text())
    completion_summary = {k: completion.get(k) for k in
                          ("created_utc", "executed", "passed", "failed", "unstarted",
                           "classification", "source_tree_sha256", "harness_sha256", "validated_trace_count")}
    if args.completion_receipt.resolve() != (args.scenario_root / "execution.json").resolve():
        errors.append({"kind": "completion_receipt_outside_expected_namespace"})
    if not (completion.get("executed") is True and completion.get("passed") is True
            and completion.get("failed") == [] and completion.get("unstarted") == []):
        errors.append({"kind": "scenario_execution_not_all_passed"})
    completed_jobs = completion.get("results", [])
    if len(completed_jobs) != len(job_ids) or {j.get("job_id") for j in completed_jobs} != job_ids:
        errors.append({"kind": "completion_job_set_mismatch"})
    for job in completed_jobs:
        if job.get("passed") is not True or job.get("run", {}).get("exit_code") != 0:
            errors.append({"kind": "completion_job_not_success", "job_id": job.get("job_id")})
    for field in ("source_tree_sha256", "harness_sha256"):
        if completion.get(field) != manifest["identity"][field]:
            errors.append({"kind": "completion_identity_mismatch", "field": field})
    if completion.get("validated_trace_count") != sum(j["expected_traces"] for j in jobs):
        errors.append({"kind": "completion_trace_count_mismatch"})
    window_starts, window_ends = [], []
    for path in sorted((args.scenario_root / "dumps").rglob("*.json")):
        relative = path.relative_to(args.scenario_root / "dumps")
        if relative.parts[0] not in job_ids:
            errors.append({"kind": "unexpected_dump_namespace", "path": str(path)})
            continue
        data = path.read_bytes()
        dump = json.loads(data)
        if dump.get("schema_version") != "expgym.api_attempt.v1":
            errors.append({"kind": "unexpected_dump_schema", "path": str(path)})
            continue
        states[dump["state"]] += 1
        client_http_statuses[str(dump.get("http_status"))] += 1
        attempts[str(dump.get("attempt"))] += 1
        context = dump.get("context", {})
        contexts[relative.parts[0]] += 1
        window_starts.append(timestamp(dump["started_at_utc"]))
        if dump.get("finished_at_utc"):
            window_ends.append(timestamp(dump["finished_at_utc"]))
        # llm_clients._build_request uses default json.dumps and UTF-8. The
        # dump writer preserves dict insertion order. A secret-redacted or
        # otherwise transformed dump cannot silently pass exact hash matching.
        payload_hash = sha(json.dumps(dump["request_payload"]).encode("utf-8"))
        response = dump.get("response_raw")
        response_hash = sha(response.encode("utf-8")) if response is not None else None
        candidates = pairs.get((payload_hash, response_hash), [])
        item = {"dump": str(path.resolve()), "dump_sha256": sha(data),
                "client_request_id": dump["request_id"],
                "generation_id": dump.get("generation_id"),
                "context": context, "job_id": relative.parts[0],
                "state": dump["state"], "attempt": dump.get("attempt"),
                "will_retry": dump.get("will_retry"),
                "http_status": dump.get("http_status"),
                "started_at_utc": dump["started_at_utc"],
                "finished_at_utc": dump.get("finished_at_utc"),
                "reconstructed_payload_sha256": payload_hash,
                "response_raw_utf8_sha256": response_hash,
                "router_candidate_count": len(candidates)}
        if len(candidates) != 1:
            errors.append({"kind": "missing_or_ambiguous_byte_join", "dump": str(path),
                           "candidate_count": len(candidates)})
        else:
            index = candidates[0]
            row = router_rows[index]
            if index in matched:
                errors.append({"kind": "router_row_reused", "router_index": index})
            matched.add(index)
            per_replica[str(row["replica"])] += 1
            item["router_line_1based"] = index + 1
            item["router_receipt"] = row
            item["payload_bytes_match"] = True
            item["response_bytes_match"] = True
            if not (row.get("complete") and row.get("upstream_close_started")
                    and row.get("upstream_close_completed")
                    and not row.get("upstream_close_error")
                    and row.get("http_status") == 200):
                errors.append({"kind": "router_completion_or_http_failure", "router_index": index})
        if dump["state"] != "success" or dump.get("http_status") not in (None, 200):
            errors.append({"kind": "client_not_success", "dump": str(path), "state": dump["state"]})
        if dump.get("will_retry") or dump.get("attempt") != 1:
            # Dump metadata is one-based: _request_with_retries stores attempt + 1.
            errors.append({"kind": "client_retry_or_noninitial_attempt", "dump": str(path),
                           "attempt": dump.get("attempt"), "will_retry": dump.get("will_retry")})
        inventory.append(item)
    if not inventory or not window_ends:
        errors.append({"kind": "empty_or_unfinished_namespace"})
    if set(contexts) != job_ids:
        errors.append({"kind": "manifest_jobs_without_client_attempts",
                       "missing_job_ids": sorted(job_ids - set(contexts))})
    unmatched = []
    window = [min(window_starts), max(window_ends)] if window_starts and window_ends else None
    for index, row in enumerate(router_rows):
        if index in matched:
            continue
        in_window = bool(window and window[0] - 1 <= row["started_unix"] <= window[1] + 1)
        unmatched.append({"router_line_1based": index + 1, "within_scenario_time_window": in_window,
                          "router_receipt": row})
        if in_window:
            errors.append({"kind": "unmatched_router_inside_scenario_window", "router_index": index})
    interval_events = []
    per_replica_events = defaultdict(list)
    for index in matched:
        row = router_rows[index]
        events = [(row["started_unix"], 1),
                  (row["started_unix"] + row["elapsed_seconds"], -1)]
        interval_events.extend(events)
        per_replica_events[str(row["replica"])].extend(events)

    def peak(events: list) -> int:
        current = maximum = 0
        # Half-open [start, finish) intervals: ends sort before starts at a tie.
        for _, change in sorted(events):
            current += change
            maximum = max(maximum, current)
        return maximum

    raw_snapshot_path = args.out / "router_requests_snapshot.jsonl"
    raw_snapshot_path.write_bytes(raw_router)
    inventory_path = args.out / "response_inventory.jsonl"
    inventory_path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in inventory))
    unmatched_path = args.out / "unmatched_router_rows.json"
    unmatched_path.write_text(json.dumps(unmatched, indent=2) + "\n")
    receipt = {
        "schema_version": "portable_eval.router_raw_byte_join.v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not errors else "FAIL",
        "mode": "offline_no_network_no_generation",
        "scenario_namespace": str(args.scenario_root.resolve()),
        "bound_sources": {"manifest": artifact(manifest_path),
                          "completion_receipt": artifact(args.completion_receipt),
                          "static_acceptance": artifact(args.static_acceptance),
                          "client_source": artifact(args.client_source),
                          "router_source": artifact(args.router_source),
                          "capacity_receipt": artifact(args.capacity_receipt),
                          "collector": artifact(Path(__file__))},
        "source_tree_sha256": manifest["identity"].get("source_tree_sha256"),
        "completion_summary": completion_summary,
        "job_count": len(jobs), "expected_trace_count": sum(j["expected_traces"] for j in jobs),
        "client_attempt_count": len(inventory), "client_states": dict(states),
        "client_http_statuses": dict(client_http_statuses),
        "attempt_indices": dict(attempts), "attempts_per_job": dict(contexts),
        "matched_router_count": len(matched), "matches_per_replica": dict(per_replica),
        "completed_router_interval_peak_concurrency": peak(interval_events),
        "completed_router_interval_peak_per_replica": {k: peak(v) for k, v in per_replica_events.items()},
        "router_snapshot_count": len(router_rows), "unmatched_router_count": len(unmatched),
        "scenario_window_unix": window,
        "artifacts": {"router_snapshot": artifact(raw_snapshot_path),
                      "inventory": artifact(inventory_path), "unmatched_router": artifact(unmatched_path)},
        "errors": errors,
        "limitations": [
            "This is transport-byte fidelity and completion evidence, not semantic model, seed reproducibility, benchmark quality, or GPU cache correctness evidence.",
            "Client raw-response UTF-8 re-encoding and default json.dumps reconstruction are accepted only where exact router SHA256 values match; redacted or transformed records do not silently pass.",
            "The frozen client leaves http_status null for successful attempts. HTTP 200 assertions here come from the matched router receipt, not that missing client field.",
            "Matching is fail-closed for duplicate request/response hash pairs; no arbitrary duplicate assignment is made.",
            "Router snapshot contains completion receipts, not all request starts. The namespace execution receipt is checked for all jobs passed, zero exit codes, source/harness identity and expected trace count, but this offline scan does not itself establish zero live requests.",
            "The capacity receipt and current router source are hash-bound as evidence references only. This join does not independently re-accept capacity, launch authorization or service configuration.",
            "A transient 3/4 router health observation belonged to the earlier v2 run, not this v3 namespace. Periodic health snapshots do not exclude short gaps and this collector makes no continuous-health claim.",
            "Strict initial seed-repeatability and nonce failures remain preserved; this scenario was authorized as seed_labels_only, not strict deterministic acceptance.",
            "Earlier v2 native task-prompt conflicts and costs remain preserved. The current v3 namespace has a separate source and prompt/path acceptance gate; transport PASS alone does not authorize A21 or prove benchmark performance.",
        ],
    }
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"receipt": str((args.out / "receipt.json").resolve()),
                      "sha256": sha((args.out / "receipt.json").read_bytes()),
                      "status": receipt["status"], "client_attempt_count": len(inventory),
                      "matched_router_count": len(matched), "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
