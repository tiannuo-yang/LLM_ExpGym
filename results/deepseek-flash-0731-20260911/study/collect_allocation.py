#!/usr/bin/env python3
"""Collect one bounded, top-level Slurm allocation ledger; never mutate jobs.

Example (one allocation, not four jobs for its four model replicas):
  collect_allocation.py --study-root ABS_STUDY --since 2026-09-11T00:00:00 \
    --job 1204605 ABS_LAUNCH PLAN_SHA deployment.json DEPLOYMENT_SHA \
    --output-dir ABS_STUDY/study/allocation_final

Repeat --job for every actual additional allocation, including failed startups.
Each five-value binding is JOB_ID LAUNCH_DIR PLAN_SHA RECORD_NAME RECORD_SHA;
RECORD_NAME is deployment.json, or submission.json for an early startup failure
without a deployment. The latter must contain a successful sbatch stdout job ID.
Only those two launch metadata files and plan.json can be opened; no private,
runtime, checkpoint or raw experiment files are read. Existing output is refused.

Outputs ACCOUNTING.json and ACCOUNTING.md, once. The JSON retains the exact sacct
command, controlled time environment, complete stdout/stderr and all parsed rows.
Duplicate identical allocation rows count once; contradictory duplicate IDs fail
closed with raw query evidence retained and all costs unknown. Steps are retained
but excluded. Missing/running/unknown records have no
final GPU-hours. Terminal GPU-hours use actual AllocTRES GPUs * ElapsedRaw / 3600,
never planned GPU count, replica count, request time or a made-up current end.
This is allocation accounting, not utilization, useful compute or formal-only cost.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess

FIELDS = ("JobIDRaw", "JobID", "Cluster", "Account", "Partition", "JobName", "State",
          "Submit", "Start", "End", "ElapsedRaw", "AllocNodes", "AllocTRES", "NodeList", "ExitCode")
FORMAT = ",".join(name + ("%1024" if name in {"AllocTRES", "NodeList"} else
                          "%200" if name == "JobName" else "%80" if name == "State" else "") for name in FIELDS)
TIME_ENV = {"TZ": "UTC", "LC_ALL": "C", "SLURM_TIME_FORMAT": "standard"}
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL", "OUT_OF_MEMORY",
            "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED"}
UNKNOWN = {"", "Unknown", "UNKNOWN", "N/A", "None", "NONE"}
FORBIDDEN_PART = re.compile(r"(^|[._-])(private|secrets?|credentials?|api[-_]?key|cache|venv|runtime|env)([._-]|$)", re.I)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def owned_path(value, root):
    path, root = Path(value).absolute(), Path(root).absolute()
    require('..' not in path.parts and path.is_relative_to(root), "path_outside_owned_scope")
    require(not any(FORBIDDEN_PART.search(part) for part in path.relative_to(root).parts),
            "private_runtime_or_cache_path_forbidden")
    for parent in (path.parent,) + tuple(path.parents):
        require(stat.S_ISDIR(parent.lstat().st_mode), "symlink_or_non_directory_parent")
    return path


def read_metadata(path, checksum):
    require(re.fullmatch(r"[0-9a-f]{64}", checksum or ""), "explicit_metadata_sha_required")
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= 4 * 1024 * 1024,
            "bounded_regular_launch_metadata_required")
    raw = path.read_bytes()
    after = path.lstat()
    signature = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    require(signature(before) == signature(after) and sha(raw) == checksum, "launch_metadata_changed_or_wrong_sha")
    return json.loads(raw), {"path": str(path), "bytes": len(raw), "sha256": checksum}


def bindings_for(root, jobs):
    result = {}
    for job_id, directory, plan_sha, record_name, record_sha in jobs:
        require(re.fullmatch(r"[1-9]\d*", job_id) and job_id not in result, "duplicate_or_nonallocation_expected_job_id")
        require(record_name in {"deployment.json", "submission.json"}, "launch_record_not_admitted")
        launch = owned_path(Path(directory) / "plan.json", root / "serving").parent
        plan, plan_pin = read_metadata(launch / "plan.json", plan_sha)
        record, record_pin = read_metadata(launch / record_name, record_sha)
        if record_name == "deployment.json":
            require(str(record.get("job_id")) == job_id and record.get("plan_sha256") == plan_sha,
                    "deployment_job_or_plan_binding_mismatch")
        else:
            require(type(record.get("exit_code")) is int and record["exit_code"] == 0
                    and isinstance(record.get("stdout"), str), "unsuccessful_submission_binding")
            submitted = record["stdout"].strip()
            require(re.fullmatch(r"[1-9]\d*(?:;[A-Za-z0-9_.-]+)?", submitted)
                    and submitted.split(";", 1)[0] == job_id, "submission_job_binding_mismatch")
        slurm, topology = plan["config"]["slurm"], plan["config"]["topology"]
        result[job_id] = {"job_id": job_id, "launch_dir": str(launch), "inputs": [plan_pin, record_pin],
            "plan_binding": "deployment_embedded_plan_sha256" if record_name == "deployment.json" else
                "operator_explicit_plan_pin_not_proven_by_submission",
            "model": plan["model"], "planned_account": slurm["account"], "planned_partition": slurm["partition"],
            "planned_nodes": slurm["nodes"], "planned_gpus": slurm["nodes"] * slurm["gpus_per_node"],
            "model_replicas": topology["replicas"]}
    require(result, "explicit_expected_jobs_required")
    return result


def integer(value):
    if value in UNKNOWN:
        return None
    require(re.fullmatch(r"\d+", value) is not None, "invalid_sacct_integer")
    return int(value)


def utc(value):
    if value in UNKNOWN:
        return None
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value) is not None,
            "sacct_timestamp_not_standard_utc")
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def gpu_count(text):
    if text in UNKNOWN:
        return None
    tres = {}
    for item in text.split(","):
        key, separator, value = item.partition("=")
        require(separator and key and key not in tres, "invalid_or_duplicate_alloc_tres")
        tres[key] = value
    generic = integer(tres["gres/gpu"]) if "gres/gpu" in tres else None
    typed = [integer(value) for key, value in tres.items() if key.startswith("gres/gpu:")]
    typed_total = sum(typed) if typed and all(value is not None for value in typed) else None
    require(generic is None or typed_total is None or generic == typed_total, "generic_typed_gpu_tres_conflict")
    return generic if generic is not None else typed_total


def parse_allocations(stdout, bindings):
    rows, unique, excluded = [], {}, []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        values = line.split("|")
        require(len(values) == len(FIELDS), "unexpected_sacct_field_count")
        row = dict(zip(FIELDS, values))
        rows.append(row)
        job_id = row["JobIDRaw"]
        if re.fullmatch(r"[1-9]\d*\.(?:[A-Za-z0-9_-]+)", job_id):
            require(job_id.split(".", 1)[0] in bindings, "unrequested_sacct_job")
            excluded.append({"row_index": len(rows) - 1, "reason": "job_step_not_allocation"})
            continue
        require(job_id in bindings and row["JobID"] == job_id, "unrequested_or_nonallocation_sacct_job")
        require(job_id not in unique or unique[job_id] == row, "contradictory_duplicate_allocation_rows")
        if job_id in unique:
            excluded.append({"row_index": len(rows) - 1, "reason": "identical_duplicate_allocation_row"})
        unique[job_id] = row
    allocations = []
    for job_id in sorted(bindings, key=int):
        binding, row = bindings[job_id], unique.get(job_id)
        if row is None:
            allocations.append({**binding, "state": "MISSING", "start_utc": None, "end_utc": None,
                "observed_elapsed_seconds": None, "final_elapsed_seconds": None, "allocated_nodes": None,
                "allocated_gpus": None, "allocation_gpu_hours": None, "terminal": False,
                "sacct_record": None, "allocation_matches_plan": None})
            continue
        state = row["State"].split()[0] if row["State"].split() else "UNKNOWN"
        start, end, elapsed = utc(row["Start"]), utc(row["End"]), integer(row["ElapsedRaw"])
        terminal = state in TERMINAL
        require(terminal or end is None, "nonterminal_sacct_record_has_end")
        span = None
        if start and end:
            span = (datetime.fromisoformat(end.replace("Z", "+00:00")) - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds()
            require(span >= 0, "sacct_end_precedes_start")
        gpus, nodes = gpu_count(row["AllocTRES"]), integer(row["AllocNodes"])
        final_elapsed = elapsed if terminal and start and end else None
        hours = gpus * final_elapsed / 3600 if gpus is not None and final_elapsed is not None else None
        require(hours is None or math.isfinite(hours), "allocation_gpu_hours_overflow")
        allocations.append({**binding, "state": state, "start_utc": start, "end_utc": end,
            "submit_utc": utc(row["Submit"]), "observed_elapsed_seconds": elapsed,
            "final_elapsed_seconds": final_elapsed, "timestamp_span_seconds": span,
            "elapsed_matches_timestamp_span": None if elapsed is None or span is None else abs(elapsed - span) <= 1,
            "allocated_nodes": nodes, "allocated_gpus": gpus, "allocation_gpu_hours": hours,
            "terminal": terminal, "sacct_record": row,
            "allocation_matches_plan": None if nodes is None or gpus is None else
                nodes == binding["planned_nodes"] and gpus == binding["planned_gpus"]
                and row["Account"] == binding["planned_account"] and row["Partition"] == binding["planned_partition"]})
    known = [row["allocation_gpu_hours"] for row in allocations if row["allocation_gpu_hours"] is not None]
    return {"expected_job_ids": sorted(bindings, key=int), "allocations": allocations, "sacct_rows": rows,
            "excluded_rows": excluded, "known_allocations": len(known), "expected_allocations": len(bindings),
            "allocation_gpu_hours": math.fsum(known) if len(known) == len(bindings) else None,
            "known_subset_allocation_gpu_hours": math.fsum(known)}


def markdown(record):
    def cell(value):
        return str("unknown" if value is None else value).replace("|", "&#124;").replace("\n", "<br>")
    columns = ("job_id", "state", "start_utc", "end_utc", "observed_elapsed_seconds", "final_elapsed_seconds",
               "allocated_nodes", "allocated_gpus", "model_replicas", "allocation_gpu_hours")
    lines = ["# 实际 Slurm allocation 账本", "", "| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    lines += ["| " + " | ".join(cell(row[key]) for key in columns) + " |" for row in record["allocations"]]
    lines += ["", "采集状态：%s；完整 allocation GPU-hours：%s；known/expected allocations：%d/%d；仅已知子集合计：%s。" %
              (cell(record.get("collection_status", "not_provided")),
               cell(record["allocation_gpu_hours"]), record["known_allocations"], record["expected_allocations"],
               cell(record["known_subset_allocation_gpu_hours"])), "",
              "只按唯一顶层 Slurm job 的实际 AllocTRES GPU 总数 × 终态 ElapsedRaw 秒 ÷ 3600 计算。四个模型副本不是四个 allocation，不额外乘副本数。",
              "RUNNING 或缺少实际起止/elapsed/GPU 字段时，最终成本保持 unknown；observed elapsed 仅保留查询时观测，不外推当前时间。时间戳区间不替换 Slurm ElapsedRaw。",
              "deployment 含原始 plan SHA；仅有 submission 的早期失败记录采用操作员显式 plan 关联，不声称 sbatch stdout 自身证明了实际使用的 plan。查询或解析失败会保留全部原始输出、成本置 unknown，并非有效的完整账本。",
              "包括加载、smoke、正式运行、等待与失败启动所属分配时间；不是 formal-only 成本、有效计算量或 GPU 利用率。原始查询命令、全部 sacct 行、被排除的 step/重复行及绑定见 [ACCOUNTING.json](ACCOUNTING.json)。", ""]
    return "\n\n".join(lines[:2]) + "\n" + "\n".join(lines[2:])


def collect(root, jobs, since, output_dir):
    root = Path(root).absolute()
    output = owned_path(output_dir, root / "study")
    require(not output.exists() and not output.is_symlink(), "fresh_output_directory_required")
    require(utc(since) is not None, "explicit_since_required")
    bindings = bindings_for(root, jobs)
    command = ["sacct", "-X", "-P", "-n", "--duplicates", "--jobs=" + ",".join(sorted(bindings, key=int)),
               "--starttime=" + since, "--format=" + FORMAT]
    process_env = os.environ.copy()
    process_env.update(TIME_ENV)
    def text_output(value):
        return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60, env=process_env)
        stdout, stderr, exit_code = completed.stdout, completed.stderr, completed.returncode
        query_status = "passed" if exit_code == 0 else "nonzero_exit"
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, exit_code = text_output(exc.stdout), text_output(exc.stderr), None
        query_status = "timeout"
    except OSError as exc:
        stdout, stderr, exit_code = "", str(exc), None
        query_status = "launch_error"
    parsed = parse_allocations("", bindings)
    parse_status, parse_error = "not_attempted", None
    if query_status == "passed":
        try:
            parsed = parse_allocations(stdout, bindings)
            parse_status = "passed"
        except (ValueError, KeyError, TypeError) as exc:
            parse_status = "failed"
            parse_error = str(exc) if re.fullmatch(r"[a-z0-9_]+", str(exc)) else type(exc).__name__
    record = {"schema": "deepseek-flash.allocation-accounting.v1", "study_root": str(root),
              "collected_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
              "command": command, "time_environment": TIME_ENV, "sacct_stdout": stdout,
              "sacct_stderr": stderr, "sacct_exit_code": exit_code, "sacct_raw_lines": stdout.splitlines(),
              "query_status": query_status, "parse_status": parse_status, "parse_error": parse_error,
              "collection_status": "passed" if query_status == parse_status == "passed" else "failed",
              **parsed,
              "scope": "Top-level actual Slurm allocations; no model calls, cancellations, raw scans or utilization inference"}
    output.mkdir()
    with (output / "ACCOUNTING.json").open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    with (output / "ACCOUNTING.md").open("x", encoding="utf-8") as handle:
        handle.write(markdown(record))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--study-root", type=Path, required=True)
    parser.add_argument("--since", required=True, help="Explicit UTC lower bound, e.g. 2026-09-11T00:00:00")
    parser.add_argument("--job", nargs=5, action="append", required=True,
                        metavar=("JOB_ID", "LAUNCH_DIR", "PLAN_SHA", "RECORD_NAME", "RECORD_SHA"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.study_root, args.job, args.since, args.output_dir)
    print(json.dumps({"output_dir": str(args.output_dir), "expected_allocations": result["expected_allocations"],
                      "collection_status": result["collection_status"], "known_allocations": result["known_allocations"],
                      "allocation_gpu_hours": result["allocation_gpu_hours"]}))
    return 0 if result["collection_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
