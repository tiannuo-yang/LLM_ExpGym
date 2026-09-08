#!/usr/bin/env python3
"""Offline usage/runtime supplement for completed A21 byte-joined attempts."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", type=Path, required=True)
    final = parser.parse_args().final.resolve()
    inventory_path = final / "response_inventory.jsonl"
    receipt_path = final / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "PASS"
    assert sha(inventory_path) == receipt["artifacts"]["inventory"]["sha256"]
    rows = [json.loads(line) for line in inventory_path.read_text().splitlines()]
    totals, finish, max_tokens_requested, detail_types, per_replica = Counter(), Counter(), Counter(), Counter(), {}
    samples = {k: [] for k in ("prompt_tokens", "completion_tokens", "reasoning_tokens", "total_tokens")}
    durations = []
    first, last, sum_mismatches = [], [], []
    for row in rows:
        path = Path(row["dump"])
        assert sha(path) == row["dump_sha256"]
        dump = json.loads(path.read_text())
        usage = dump["response_json"]["usage"]
        for key in samples:
            value = usage[key]
            assert isinstance(value, int) and not isinstance(value, bool) and value >= 0
            totals[key] += value
            samples[key].append(value)
        if usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]:
            sum_mismatches.append(row["client_request_id"])
        detail_types[type(usage.get("prompt_tokens_details")).__name__] += 1
        for choice in dump["response_json"]["choices"]:
            finish[str(choice.get("finish_reason"))] += 1
        max_tokens_requested[str(dump["request_payload"].get("max_tokens"))] += 1
        replica = str(row["router_receipt"]["replica"])
        stats = per_replica.setdefault(replica, Counter())
        stats["requests"] += 1
        stats["prompt_tokens"] += usage["prompt_tokens"]
        stats["completion_tokens"] += usage["completion_tokens"]
        durations.append(dump["wall_time_seconds"])
        first.append(dump["started_at_utc"])
        last.append(dump["finished_at_utc"])
    execution_path = Path(receipt["bound_sources"]["completion_receipt"]["path"])
    assert sha(execution_path) == receipt["bound_sources"]["completion_receipt"]["sha256"]
    execution = json.loads(execution_path.read_text())
    elapsed = execution["elapsed_seconds_including_preflight_resume"]
    result = {
        "schema_version": "portable_eval.a21_usage_runtime.v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "All client response usage records in this selected namespace already byte-joined to router receipts; no network or generation",
        "receipt_sha256": sha(receipt_path), "inventory_sha256": sha(inventory_path),
        "execution_sha256": sha(execution_path), "collector_sha256": sha(Path(__file__)),
        "requests": len(rows), "response_reported_token_sums": dict(totals),
        "total_equals_prompt_plus_completion_mismatches": sum_mismatches,
        "response_reported_token_ranges": {k: {"min": min(v), "max": max(v), "mean": statistics.mean(v)} for k, v in samples.items()},
        "per_replica": per_replica, "finish_reason_counts": dict(finish),
        "request_max_tokens_counts": dict(max_tokens_requested),
        "prompt_tokens_details_types": dict(detail_types),
        "harness_elapsed_seconds": elapsed, "harness_elapsed_minutes": elapsed / 60,
        "first_client_attempt_started_utc": min(first), "last_client_attempt_finished_utc": max(last),
        "client_attempt_wall_seconds": {"min": min(durations), "max": max(durations), "mean": statistics.mean(durations), "sum_overlapping": sum(durations)},
        "workflow_completion_tokens_per_harness_second": totals["completion_tokens"] / elapsed,
        "interpretation": [
            "Token counts are SGLang response-reported usage, not independently re-tokenized hardware FLOPs or billed cost. Reasoning tokens are a subset of completion tokens and are not added again to total_tokens.",
            "The client/provider reports prompt_tokens_details as null; this does not prove prefix caching was disabled or no cache hits occurred.",
            "Harness elapsed time includes workflow activity and guarded resume checks; completion_tokens/harness_second is a realized workflow rate, not pure engine decoding or saturated serving throughput.",
            "Per-attempt wall times overlap under concurrency and their sum is not elapsed runtime.",
            "Reported prompt length and requested max_tokens are distinct from effective input/output/KV limits. Refer to the immutable capacity receipt; this supplement makes no full-context or future-load guarantee.",
            "Transport success and these usage totals do not establish native prompt/path compatibility or strict seed control. Earlier failures remain preserved; A21 is timing-only and cannot be promoted into formal effect results.",
        ],
    }
    output = final / "usage_runtime_receipt.json"
    with output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"path": str(output), "sha256": sha(output), "summary": result}, indent=2))


if __name__ == "__main__":
    main()
