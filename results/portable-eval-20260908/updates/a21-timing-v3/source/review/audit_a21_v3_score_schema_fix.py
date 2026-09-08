#!/usr/bin/env python3
"""Read-only post-drain A21 audit: same-runtime scores, inputs, prompts, snapshots.

No runner main or resume execution. The isolated scoring child forbids models
and network; its only output is stdout. Existing evidence is never rewritten.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from audit_a21_attempts_v3 import strict_dump_inventory

ROOT = Path(__file__).resolve().parents[1]
CHILD = Path(__file__).with_name("audit_a21_score_child.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def reject(value):
        raise ValueError("Non-finite JSON constant")
    return json.loads(Path(path).read_text(), object_pairs_hook=unique, parse_constant=reject)


def load(path):
    spec = importlib.util.spec_from_file_location("a21_independent_pilot", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(run, authorization, raw_receipt):
    # Inspect the caller's lexical path before resolve() could erase a symlink.
    # This precedes every evidence/authorization read and scoring import.
    initial_dump_paths = strict_dump_inventory(run)
    run, authorization, raw_receipt = [Path(path).resolve() for path in (run, authorization, raw_receipt)]
    execution = read(run / "execution.json")  # Explicit drain is also required by the operator.
    auth = read(authorization)
    if sha(authorization) != "b9f4a483b1d52c0cc0de1ee7fcd4fde482193284a7a7c95e251919b2386ee74f":
        raise ValueError("This auditor only accepts the frozen one-shot A21 v3 authority")
    manifest, commands, raw = read(run / "manifest.json"), read(run / "commands.json"), read(raw_receipt)
    identity = manifest["identity"]
    errors, bindings, rows = [], {}, []
    def require(condition, message):
        if not condition:
            errors.append(message)
    def bind(path, expected=None):
        path = str(Path(path).resolve())
        checksum = sha(path)
        if path in bindings:
            require(bindings[path] == checksum, "Evidence changed during audit: " + path)
        bindings[path] = checksum
        require(expected is None or checksum == expected, "SHA binding differs: " + path)
        return checksum

    bind(authorization)
    for path, checksum in auth["file_bindings"].items():
        bind(path, checksum)
    bind(run / "execution.json")
    bind(run / "execution_started.json")
    bind(run / "manifest.json", auth["manifest_sha256"])
    bind(run / "commands.json", auth["commands_sha256"])
    bind(raw_receipt)
    bind(CHILD)
    bind(Path(__file__).with_name("audit_a21_attempts_v3.py"))
    harness_path = ROOT / "harness/pilot_timing.py"
    if sha(harness_path) != auth["harness_sha256"]:
        raise ValueError("Refuse importing a changed A21 harness")
    pilot = load(harness_path)
    args = pilot.parse_args(auth["resolved_argv"][3:])
    require(args.output_dir == run == Path(auth["output_dir"]), "Authorized run directory differs")
    require(auth["authorized"] is True and auth["authorization_kind"] == "kimi-k3-a21-runtime-pilot-v3", "Authority type differs")
    require(pilot.settings(args) == identity["settings"], "Frozen generation/settings differ")
    require(identity["settings"]["tool_protocol"] == "native" and identity["settings"]["max_steps"] == identity["settings"]["max_evals"] == 30, "A21 protocol/horizon differs")
    require(pilot.verify_acceptance(args.repo_root, args.static_acceptance) == identity["static_acceptance"], "Current source acceptance differs")
    require(identity["static_acceptance"]["source_tree_sha256"] == auth["source_tree_sha256"], "Authorized source differs")
    for path, checksum in identity["harness_files"].items():
        bind(path, checksum)
    require(len(identity["harness_files"]) == 4, "A21 helper file set differs")
    planned = pilot.build_jobs(args)
    jobs = identity["jobs"]
    require(len(jobs) == 21 and len({job["id"] for job in jobs}) == 21, "Not the fixed 21 unique A21 jobs")
    require([{key: value for key, value in job.items() if key not in ("preflight", "environment_overrides")} for job in jobs] == planned, "Frozen A21 task selection/order/commands differ")
    require(identity["counts"] == {"jobs": 21, "agent_traces": 21, "A1": 9, "A2": 12, "legacy_paramnet": 3, "native": 18}, "A21 counts differ")
    statuses = {row["job_id"]: row for row in execution["results"]}
    expected_ids = {job["id"] for job in jobs}
    require(len(execution["results"]) == 21 and set(statuses) == expected_ids and execution["unstarted"] == [], "Not all planned jobs completed")
    require(execution["executed"] is True and execution["passed"] is True and execution["classification"] == "Custom study", "Execution status/classification differs")
    require(raw["passed"] is True and raw["run_directory"] == str(run) and raw["trace_count"] == 21, "Independent raw audit not accepted for this scope")
    require(raw["manifest_sha256"] == sha(run / "manifest.json") and raw["execution_sha256"] == sha(run / "execution.json"), "Raw receipt identity differs")
    require(set(commands) == expected_ids, "Command namespace differs")
    for kind in ("results", "dumps"):
        require({path.name for path in (run / kind).iterdir() if path.is_dir()} == expected_ids, kind + " namespace differs")

    snapshots, skips, zero_count, protocols, requests = {}, 0, 0, [], []
    for job in jobs:
        job_id = job["id"]
        status = statuses[job_id]
        require(status["passed"] is True and type(status["run"]["exit_code"]) is int and status["run"]["exit_code"] == 0, job_id + ": child did not pass")
        path = run / "logs" / job_id / "execution_status.json"
        bind(path)
        require(read(path) == status, job_id + ": status and final execution differ")
        require(commands[job_id] == {"run": job["command"], "dry_run": job["command"] + ["--dry-run"], "resume_guard": pilot.guard_command(job)}, job_id + ": command receipt differs")
        require(job["environment_overrides"] == pilot.environment_overrides(args, job), job_id + ": data/runtime environment differs")
        require(Path(job["output_dir"]) == run / "results" / job_id and Path(job["dump_dir"]) == run / "dumps" / job_id, job_id + ": output namespace differs")
        current = {"results": pilot.snapshot(job["output_dir"]), "dumps": pilot.snapshot(job["dump_dir"])}
        require(current == status["before_resume"] == status["resume"]["after"], job_id + ": result/raw SHA/size/mtime differs")
        snapshots[job_id] = current
        resume = status["resume"]
        require(resume["model_calls_forbidden"] is True and resume["before_equals_after"] is True and resume["verified_skips"] == 1 and type(resume["exit_code"]) is int and resume["exit_code"] == 0, job_id + ": guarded skip not accepted")
        for receipt in (status["run"], resume):
            bind(receipt["log"], receipt["log_sha256"])
        text = Path(resume["log"]).read_text()
        require(text.count("skip verified") == 1 and "rerun" not in text.lower() and "PILOT_GUARD_MODEL_CALL_FORBIDDEN" not in text, job_id + ": guarded skip log differs")
        skips += resume["verified_skips"]
        traces = sorted(Path(job["output_dir"]).glob("*/traces-v2/*.json"))
        require(len(traces) == 1, job_id + ": expected one trace")
        trace = read(traces[0])
        outcome = trace["outcome"]
        zero_count += (outcome["score"]["metrics"][outcome["score"]["primary_metric"]] if "metrics" in outcome["score"] else outcome["score"]["value"]) == 0
        if outcome["protocol_failures"] or outcome["protocol_retries"]:
            protocols.append({"job_id": job_id, "path": str(traces[0]), "failures": outcome["protocol_failures"], "retries": outcome["protocol_retries"]})
        if job["scenario"] == "evidence_audit":
            order = read(args.repo_root / "configs/audit_hypothesis_orders.json")["orders"][0]
            require(job["preflight"]["job"]["hypothesis_order"] == order, job_id + ": audit ordering differs from order0")
        child_command = [job["command"][0], "-B", str(CHILD)]
        completed = subprocess.run(child_command, input=json.dumps({"repo_root": str(args.repo_root), "job": job, "trace_path": str(traces[0])}),
                                   cwd=args.repo_root, env=pilot.child_environment(args, job), text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300, check=False)
        lines = [line[len("A21_INDEPENDENT_JSON="):] for line in completed.stdout.splitlines() if line.startswith("A21_INDEPENDENT_JSON=")]
        require(completed.returncode == 0 and len(lines) == 1, job_id + ": isolated score/context process failed")
        if len(lines) != 1:
            raise RuntimeError("Isolated scorer returned no unique receipt: " + job_id)
        result = json.loads(lines[0])
        require(result["passed"] is True, job_id + ": score/identity/runtime/prompt recomputation failed")
        expected_version = "3.7." if job["runtime"] == "legacy_paramnet" else "3.11."
        require(result["runtime"]["version"].startswith(expected_version), job_id + ": wrong actual interpreter")
        requests.extend(result["request_ids"])
        rows.append({"job_id": job_id, "runtime_kind": job["runtime"], "child_command": child_command,
                     "child_exit_code": completed.returncode, "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
                     "trace_path": str(traces[0]), "trace_sha256": sha(traces[0]), "result": result})
    require(skips == 21 and execution["validated_trace_count"] == 21, "Final trace or skip count differs")
    require(zero_count == execution["semantic_zero_count"], "Semantic zeros were not retained")
    require(len(requests) == len(set(requests)) == raw["attempt_count"], "Prompt audit/raw request coverage differs")
    require(set(requests) == {Path(row["path"]).stem for row in raw["file_hashes"] if Path(row["path"]).parent.parent == run / "dumps"}, "Prompt audit/raw request identity set differs")
    for job in jobs:
        require(snapshots[job["id"]] == {"results": pilot.snapshot(job["output_dir"]), "dumps": pilot.snapshot(job["dump_dir"])}, job["id"] + ": audit modified evidence")
    require(strict_dump_inventory(run) == initial_dump_paths, "Full recursive dump inventory changed during audit")
    require(pilot.verify_acceptance(args.repo_root, args.static_acceptance) == identity["static_acceptance"], "Source changed during audit")
    for path, checksum in bindings.items():
        require(sha(path) == checksum, "Evidence binding changed during audit: " + path)
    return {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(), "passed": not errors,
            "classification": "Custom study; independent post-drain A21 integrity audit", "run_directory": str(run),
            "errors": errors, "file_bindings": bindings, "rows": rows, "validated_traces": len(rows),
            "actual_runtime_counts": dict(Counter(row["runtime_kind"] for row in rows)), "guarded_skips": skips,
            "semantic_zero_count_preserved": zero_count, "protocol_events_preserved": protocols,
            "raw_requests_prompt_checked": len(requests), "raw_receipt_sha256": sha(raw_receipt),
            "source_tree_sha256": auth["source_tree_sha256"], "auditor_sha256": sha(__file__),
            "limitations": ["All raw transport/usage/history checks are in the separate byte-bound raw receipt; router HTTP status/completion evidence remains separate.",
                            "Scoring/context validation uses each job's pinned runtime and the original frozen evaluator, not an independently reimplemented metric.",
                            "Native continuation/forced-none are observed, not required per trace; legitimate early answers never trigger replacement sampling.",
                            "This development pilot is timing-only; no formal performance reuse, effect inference, strict seed or hardware-cache claim.",
                            "This audit neither starts nor authorizes B/C, a formal matrix, another model, or another GPU allocation."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--raw-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.exists() or args.receipt.resolve().is_relative_to(args.run.resolve()):
        parser.error("Receipt must be new and outside the original run")
    sys.dont_write_bytecode = True
    result = audit(args.run, args.authorization, args.raw_receipt)
    with args.receipt.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("passed", "errors", "validated_traces", "actual_runtime_counts", "guarded_skips", "semantic_zero_count_preserved", "raw_requests_prompt_checked")}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
