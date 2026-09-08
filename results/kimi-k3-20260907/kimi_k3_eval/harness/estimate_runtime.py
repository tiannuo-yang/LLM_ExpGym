#!/usr/bin/env python3
"""Extrapolate measured pilot wall times to the manifest's exact full matrix."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def stratum(job: dict) -> str:
    scenario = job["scenario"]
    family = (job["tuning_task"].split(":")[1] if scenario == "tuning" else
              "whois" if scenario == "restricted_search" and job["question_index"] < 18 else
              "whatis" if scenario == "restricted_search" else "audit")
    return "/".join([job["system"], family, job["cost_regime"]])


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(len(ordered) * fraction) - 1)]


def collect_api_usage(jobs: list[dict]) -> tuple[dict, list[float]]:
    """Count every job's HTTP attempts, including unfinished/failed jobs.

    An in-progress request has no completed latency observation. Its attempt
    is counted, but its initial/zero elapsed time must not enter percentiles.
    """
    usage = {"attempts": 0, "successful_attempts": 0, "failed_attempts": 0, "in_progress_attempts": 0,
             "prompt_tokens": 0, "completion_tokens": 0, "truncated_completions": 0}
    request_latencies = []
    for job in jobs:
        for path in Path(job["dump_dir"]).glob("*.json"):
            record = load(path)
            if record.get("schema_version") != "expgym.api_attempt.v1":
                continue
            usage["attempts"] += 1
            state = record.get("state")
            if state == "in_progress":
                usage["in_progress_attempts"] += 1
            elif record.get("error"):
                usage["failed_attempts"] += 1
            else:
                usage["successful_attempts"] += 1
            if state != "in_progress":
                request_latencies.append(float(record.get("wall_time_seconds") or 0))
            response = record.get("response_json") or {}
            tokens = response.get("usage") or {}
            for key in ("prompt_tokens", "completion_tokens"):
                usage[key] += int(tokens.get(key) or 0)
            usage["truncated_completions"] += sum(choice.get("finish_reason") == "length" for choice in response.get("choices", []))
    return usage, request_latencies


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-manifest", type=Path, required=True)
    parser.add_argument("--full-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--assume-pilot-reused", action="store_true")
    args = parser.parse_args()
    pilot, full = load(args.pilot_manifest), load(args.full_manifest)
    settings_keys = ["model", "backend", "max_steps", "max_evals", "max_tokens", "chat_template_kwargs",
                     "temperature_tuning", "temperature_eval", "temperature_poolact", "poolact_agents",
                     "tuning_reps", "search_reps", "audit_reps", "seed", "base_url"]
    mismatches = [key for key in settings_keys if pilot["settings"].get(key) != full["settings"].get(key)]
    if mismatches or pilot["source_tree_sha256"] != full["source_tree_sha256"]:
        raise SystemExit("Pilot and full are not comparable: " + ", ".join(mismatches or ["source fingerprint"]))
    buckets = defaultdict(list)
    completed_ids = set()
    starts, finishes = [], []
    usage, request_latencies = collect_api_usage(pilot["jobs"])
    for job in pilot["jobs"]:
        status_path = Path(job["status_path"])
        if not status_path.exists():
            continue
        status = load(status_path)
        # A verified resume may take milliseconds; use the original completed
        # attempt that actually generated results, not the latest skip duration.
        completed = [attempt for attempt in status.get("attempts", []) if attempt.get("status") == "completed"]
        if not completed:
            continue
        attempt = max(completed, key=lambda value: value["wall_time_seconds"])
        duration = float(attempt["wall_time_seconds"])
        buckets[stratum(job)].append(duration)
        completed_ids.add(job["id"])
        starts.append(datetime.fromisoformat(attempt["started_at"]))
        finishes.append(datetime.fromisoformat(attempt["finished_at"]))
    rows, missing = [], []
    totals = defaultdict(lambda: {"full_job_seconds": 0.0, "remaining_job_seconds": 0.0})
    full_buckets = defaultdict(list)
    for job in full["jobs"]:
        full_buckets[stratum(job)].append(job)
    for key, jobs in sorted(full_buckets.items()):
        durations = buckets.get(key, [])
        if not durations:
            missing.append(key)
            continue
        predicted = mean(durations)
        reused = sum(job["id"] in completed_ids for job in jobs) if args.assume_pilot_reused else 0
        total, remaining = predicted * len(jobs), predicted * (len(jobs) - reused)
        system = jobs[0]["system"]
        totals[system]["full_job_seconds"] += total
        totals[system]["remaining_job_seconds"] += remaining
        rows.append({"stratum": key, "pilot_jobs": len(durations), "full_jobs": len(jobs),
                     "reused_jobs": reused, "mean_job_seconds": predicted, "median_job_seconds": median(durations),
                     "full_job_seconds": total, "remaining_job_seconds": remaining})
    measured_wall = (max(finishes) - min(starts)).total_seconds() if finishes else None
    job_seconds = sum(sum(values) for values in buckets.values())
    observed_parallelism = job_seconds / measured_wall if measured_wall else None
    effective_parallelism = min(pilot["workers"], full["workers"], observed_parallelism) if observed_parallelism else None
    total_work = sum(value["full_job_seconds"] for value in totals.values())
    remaining_work = sum(value["remaining_job_seconds"] for value in totals.values())
    estimated = remaining_work / effective_parallelism if effective_parallelism and not missing else None
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(), "pilot_manifest": str(args.pilot_manifest.resolve()),
        "full_manifest": str(args.full_manifest.resolve()), "pilot_completed_jobs": len(completed_ids),
        "pilot_wall_time_seconds": measured_wall, "observed_effective_parallelism": observed_parallelism,
        "extrapolation_parallelism": effective_parallelism, "missing_strata": missing,
        "assumes_pilot_reused_after_validation": args.assume_pilot_reused,
        "full_sum_job_seconds": total_work, "remaining_sum_job_seconds": remaining_work,
        "remaining_wall_time_seconds_point": estimated,
        "remaining_wall_time_hours_range": [estimated / 3600 * 1.3, estimated / 3600 * 1.5] if estimated else None,
        "by_system": dict(totals), "strata": rows, "usage": usage,
        "request_latency_seconds": {"median": median(request_latencies) if request_latencies else None,
                                    "p95": percentile(request_latencies, 0.95)},
        "limitations": ["Uses actual wall time; simulated tool fees are excluded.",
                        "One item per stratum is a capacity pilot, not a confidence interval for the full task distribution.",
                        "No linear throughput gain is assumed for worker counts above the measured pilot.",
                        "The range adds 30–50% variance/retry margin; it excludes further queue delay and service cold starts.",
                        "Pilot reuse requires configuration/source/score validation; this script itself does not move artifacts."],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "runtime_estimate.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    lines = ["# Kimi-K3 全量耗时估计", "", f"实测 pilot 完成 {len(completed_ids)}/{len(pilot['jobs'])} 个独立 job。"]
    if estimated:
        low, high = result["remaining_wall_time_hours_range"]
        lines += ["", f"按实测并发效率，剩余正式运行约 **{low:.2f}–{high:.2f} 小时**（含30–50%波动余量）。",
                  f"pilot 墙钟 {measured_wall / 60:.2f} 分钟，有效并发 {observed_parallelism:.2f}；完整原始预测见同目录JSON。"]
    else:
        lines += ["", "尚缺完整代表性观测，不给出全量墙钟承诺。缺失分层：" + ", ".join(missing)]
    lines += ["", f"已记录 {usage['attempts']} 次HTTP尝试，input tokens={usage['prompt_tokens']}，output tokens={usage['completion_tokens']}。",
              "", "此时间是实际推理与编排耗时；论文中模拟的实验费用不用于替代墙钟时间。单项代表样本不足以构成统计置信区间。"]
    (args.output_dir / "RUNTIME_ESTIMATE.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output_dir": str(args.output_dir), "remaining_hours_range": result["remaining_wall_time_hours_range"],
                      "missing_strata": missing}, ensure_ascii=False))


if __name__ == "__main__":
    main()
