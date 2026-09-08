#!/usr/bin/env python3
"""V3 read-only post-drain audit. Writes one exclusive, new external receipt.

Derived from audit_scenario_v2.py; original reports and auditor remain unmodified.

Calls score/resume validators, never runner main or guarded resume, which would
rewrite PoolAct summaries. The model and network are explicitly denied.
"""
import argparse
from collections import Counter
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate receipt or artifact JSON key")
            result[key] = value
        return result

    def reject(_value):
        raise ValueError("Non-finite receipt or artifact JSON constant")

    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique, parse_constant=reject)


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def audit(run, authorization, raw_receipt):
    run, authorization, raw_receipt = map(lambda p: Path(p).resolve(), (run, authorization, raw_receipt))
    # Final execution is written after bounded executor joins its child tasks.
    # Independent runner drain confirmation remains an invocation precondition.
    execution = read(run / "execution.json")
    auth, identity = read(authorization), read(run / "manifest.json")["identity"]
    repo = Path(identity["repo_root"])
    harness_path = ROOT / "harness/scenario_smoke_v3.py"
    if sha(harness_path) != "1a0df7f627519c7bfd464c9bf32bd7b5a830d4bfcd042d2bbc0b89dad0d76bc3":
        raise ValueError("Frozen v3 harness changed; refuse importing unreviewed code")
    harness = load_module(harness_path, "scenario_smoke_v3_readonly_audit")
    legacy = harness.helpers()
    errors, records, bindings = [], [], []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def bind(path, expected=None):
        path = Path(path)
        digest = sha(path)
        bindings.append({"path": str(path), "sha256": digest})
        require(expected is None or expected == digest, "binding differs: " + str(path))
        return digest

    bind(authorization)
    bind(run / "manifest.json", auth["manifest_sha256"])
    bind(run / "commands.json", auth["commands_sha256"])
    bind(run / "dry_plan_receipt.json", auth["root_review"]["dry_plan_receipt_sha256"])
    bind(harness_path, auth["harness_sha256"])
    bind(ROOT / "validation/static_acceptance_v3.json", auth["static_acceptance_sha256"])
    for name in ("execution.json", "execution_started.json", "launch_receipt.json"):
        bind(run / name)
    bind(raw_receipt)
    launch, raw = read(run / "launch_receipt.json"), read(raw_receipt)
    dry = read(run / "dry_plan_receipt.json")
    # parse_args only resolves paths/profile; it does not read the API key.
    audit_args = harness.parse_args(dry["resolved_argv"][3:] + [
        "--authorization", str(authorization), "--execute", "--allow-real"])
    expected_authorization = harness.validate_authorization(
        audit_args, identity, run / "manifest.json", run / "commands.json")
    require(launch.get("authorization") == expected_authorization, "launch authorization differs")
    require(launch.get("manifest_sha256") == sha(run / "manifest.json"), "launch manifest differs")
    require(launch.get("commands_sha256") == sha(run / "commands.json"), "launch commands differ")
    require(harness.settings(audit_args) == identity["settings"], "planned generation/settings differ")
    require(harness.build_jobs(audit_args) == identity["jobs"], "planned jobs differ")
    require(auth.get("authorized") is True and Path(auth["output_dir"]).resolve() == run, "authorization scope differs")
    require(auth["scope"]["native_coverage_rule"] == identity["settings"]["native_coverage_rule"], "authorized coverage policy differs")
    require(auth["scope"]["authorizes_a21"] is False, "unexpected expanded A21 authorization")
    require(auth["scope"]["randomness_contract"] == "seed_labels_only", "randomness contract differs")
    bind(run / "dry_run.json", dry["dry_run_sha256"])
    bind(auth["root_review"]["independent_admission_path"], auth["root_review"]["independent_admission_sha256"])
    for path, digest in identity["external_dependencies"].items():
        bind(path, digest)
    profile = identity["request_profile"]
    bind(profile["source"]["path"], profile["source"]["file_sha256"])
    bind(identity["serving_binding"]["path"], identity["serving_binding"]["sha256"])
    require(identity["source_tree_sha256"] == auth["source_tree_sha256"], "manifest source differs")
    require(identity["harness_sha256"] == sha(harness_path), "manifest harness differs")
    harness.assert_bindings(audit_args, identity)
    require(execution.get("passed") is True and execution.get("executed") is True, "execution not successful and executed")
    require(execution.get("failed") == [] and execution.get("unstarted") == [], "failed/unstarted jobs exist")
    require(execution.get("classification") == "Real smoke validation", "execution classification differs")
    require(execution.get("source_tree_sha256") == identity["source_tree_sha256"], "execution source differs")
    require(execution.get("harness_sha256") == identity["harness_sha256"], "execution harness differs")
    require(raw.get("passed", raw.get("complete")) is True, "independent raw audit did not pass")
    require(raw.get("run_directory") == str(run), "raw independent run identity differs")
    require(raw.get("manifest_sha256") == sha(run / "manifest.json"), "raw independent manifest binding differs")
    require(raw.get("execution_sha256") == sha(run / "execution.json"), "raw independent execution binding differs")
    require(raw.get("trace_count") == 21, "raw independent trace count differs")

    source_files = read(ROOT / "validation/static_acceptance_v3.json")["files"]
    require(len(source_files) == 81, "static receipt expected 81 files")
    for relative, digest in source_files.items():
        require(sha(repo / relative) == digest, "current accepted source changed: " + relative)
    require(legacy.source_fingerprint(repo) == identity["source_tree_sha256"], "current source tree changed")

    commands = read(run / "commands.json")
    expected_ids = {"__".join((system, scenario, "cost_moderate"))
                    for system in ("expgym", "poolact")
                    for scenario in ("tuning", "restricted_search", "evidence_audit")}
    jobs = identity["jobs"]
    require(len(jobs) == 6 and {job["id"] for job in jobs} == expected_ids, "6-job exact matrix differs")
    statuses = {item["job_id"]: item for item in execution["results"]}
    require(len(execution["results"]) == 6 and set(statuses) == expected_ids, "execution job set differs")
    require(set(commands) == expected_ids, "command job set differs")
    for kind in ("results", "dumps"):
        require({path.name for path in (run / kind).iterdir() if path.is_dir()} == expected_ids, kind + " directory job set differs")

    sys.path.insert(0, str(repo))
    import demo_experiment as demo
    import expgym.llm_clients as client
    from scripts import run_paper_sweep as sweep
    from scripts import run_poolact as pool

    blocked_calls = []

    def deny(*args, **kwargs):
        blocked_calls.append("network_or_model_attempt")
        raise RuntimeError("INDEPENDENT_AUDIT_NETWORK_AND_MODEL_FORBIDDEN")

    snapshots, terminals, protocol_events = {}, Counter(), []
    independent_coverages = []
    scores, skips, result_count = [], 0, 0
    previous_cwd = Path.cwd()
    try:
        os.chdir(repo)
        with ExitStack() as stack:
            for target, name in ((demo, "build_llm"), (sweep, "build_llm"), (pool, "build_llm"),
                                 (client.OpenAICompatibleLLM, "generate"), (socket.socket, "connect"),
                                 (socket.socket, "connect_ex"), (socket, "create_connection")):
                stack.enter_context(mock.patch.object(target, name, deny))
            for job in jobs:
                job_id, root = job["id"], Path(job["output_dir"])
                require(root == run / "results" / job_id, job_id + ": output path differs")
                status_path = run / "logs" / job_id / "status.json"
                status = read(status_path)
                bind(status_path)
                require(status == statuses[job_id], job_id + ": status differs from execution")
                require(status.get("passed") is True, job_id + ": status not passed")
                require(commands[job_id] == {"run": job["command"], "dry_run": job["command"] + ["--dry-run"],
                                             "resume_guard": harness.resume_command(job)}, job_id + ": commands differ")
                for name in ("run", "resume"):
                    receipt = status[name]
                    bind(receipt["log"], receipt["log_sha256"])
                    require(receipt["exit_code"] == 0, job_id + ": nonzero " + name)
                resume = status["resume"]
                resume_text = Path(resume["log"]).read_text()
                count = resume_text.count("skip verified") if job["system"] == "expgym" else resume_text.count("[resume] item=0 strategy=")
                expected = 1 if job["system"] == "expgym" else 3
                require(count == expected == resume["verified_skips"] == resume["expected_skips"], job_id + ": skip count differs")
                require("rerun" not in resume_text.lower() and "RESUME_GUARD_MODEL_CALL_FORBIDDEN" not in resume_text, job_id + ": resume attempted rerun")
                for field in ("protective_model_call_guard", "trace_bytes_and_mtimes_unchanged", "api_dump_bytes_and_mtimes_unchanged"):
                    require(resume.get(field) is True, job_id + ": resume guard false: " + field)
                skips += count
                current_artifacts = legacy.snapshot_artifacts(job)
                current_dumps = legacy.snapshot_dumps(run / "dumps" / job_id)
                require(current_artifacts == status["artifacts"], job_id + ": protected artifact SHA/size/mtime differs")
                require(current_dumps == status["api_dumps"], job_id + ": dump SHA/size/mtime differs")
                snapshots[job_id] = (current_artifacts, current_dumps)
                validation = legacy.validate_job(job, identity["source_tree_sha256"], "openai")
                require(validation == status["validation"] and validation["passed"], job_id + ": current artifact validation differs")
                planned = harness.validate_planned_artifacts(job, audit_args,
                    identity["selected_data_identities"][job["system"] + "__" + job["scenario"]])
                require(planned["passed"] and planned == status["planned_configuration"], job_id + ": planned scenario/config/data identity differs")
                coverage = harness.classify_native_coverage(job, run / "dumps" / job_id, audit_args)
                independent_coverages.append({"job_id": job_id, **coverage})
                require(coverage == status["native_coverage"], job_id + ": reconstructed prompt/wire/coverage differs")
                require(coverage["wire_passed"] is True, job_id + ": reconstructed native wire/history failed")
                summary_after = harness.snapshot_summary(job)
                expected_summary = status["resume"]["summary_after"]
                summary_equal = (summary_after is None and expected_summary is None) or (
                    summary_after is not None and expected_summary is not None and
                    all(summary_after[key] == expected_summary[key] for key in ("sha256", "bytes", "semantic_sha256")))
                require(summary_equal, job_id + ": current summary bytes/semantics differ from final snapshot")
                scores.extend(validation["agent_scores"])
                for terminal in validation["terminal_diagnostics"]:
                    terminals[json.dumps(terminal, sort_keys=True)] += 1
                agent_paths = (sorted(root.glob("*/traces-v2/*.json")) if job["system"] == "expgym"
                               else sorted(root.glob("*/agents/agent_*.json")))
                for path in agent_paths:
                    saved = read(path)
                    outcome = saved["outcome"] if job["system"] == "expgym" else saved
                    failures, retries = outcome.get("protocol_failures"), outcome.get("protocol_retries")
                    require(isinstance(failures, list) and type(retries) is int and retries >= 0,
                            str(path) + ": protocol outcome accounting missing")
                    if failures or retries:
                        protocol_events.append({"path": str(path), "failures": failures, "protocol_retries": retries,
                                                "agent_steps": outcome.get("agent_steps"),
                                                "http_request_attempts": outcome.get("http_request_attempts"),
                                                "termination_reason": outcome.get("termination_reason")})
                if job["system"] == "expgym":
                    with mock.patch.object(sys, "argv", job["command"][2:]):
                        args = sweep.parse_args()
                    native_jobs = sweep._build_jobs(args)
                    require(len(native_jobs) == 1, job_id + ": native ExpGym selection differs")
                    paths = list(root.glob("*/traces-v2/*.json"))
                    valid = len(paths) == 1 and sweep._resume_trace_is_valid(paths[0], args, native_jobs[0])
                    require(valid, job_id + ": independent ExpGym data/config/schema/score recomputation failed")
                else:
                    with mock.patch.object(sys, "argv", job["command"][2:]):
                        args = pool._repeat_namespace(pool.parse_args(), 0)
                    args.questions = None
                    args._evaluation_identity = pool.evaluation_identity(args, repo)
                    pool.bind_evaluation_identity(args._evaluation_identity)
                    time_budget, _ = pool.resolve_cost_regime(args, pool.resolve_base_cost(args.scenario, args))
                    config = pool._resolved_config(args, time_budget)
                    tools = pool._resolve_tools(pool._SCENARIOS[args.scenario], args)
                    evaluator = pool._resolve_answer_evaluator(pool._SCENARIOS[args.scenario], args)
                    valid = True
                    for strategy in ("naive", "cached", "poolact"):
                        result = pool._load_resumable_result(root / strategy / "result.json", item_output_dir=root,
                            strategy=strategy, config=config, implementation=pool._implementation_manifest(),
                            agents=2, answer_evaluator=evaluator, score_tools=tools)
                        require(result is not None, job_id + ": independent score/config/aggregate failed: " + strategy)
                        valid = valid and result is not None
                        result_count += 1
                    bind(root / "summary.json")
                records.append({"job_id": job_id, "score_config_identity_recomputed": bool(valid),
                                "trace_count": validation["trace_count"], "guarded_skips": count,
                                "protected_artifacts": len(current_artifacts), "protected_dumps": len(current_dumps)})
            for job in jobs:
                require(snapshots[job["id"]] == (legacy.snapshot_artifacts(job), legacy.snapshot_dumps(run / "dumps" / job["id"])),
                        job["id"] + ": audit changed protected evidence")
    finally:
        os.chdir(previous_cwd)
    require(not blocked_calls, "audit tried to generate or connect")
    require(len(scores) == execution["validated_trace_count"] == 21, "trace count differs from 21")
    require(result_count == 9 and skips == 12, "strategy results/guarded skips differs from 9/12")
    require(sum(value == 0 for value in scores) == execution["semantic_zero_count"], "zero outcome accounting differs")
    require(legacy.source_fingerprint(repo) == identity["source_tree_sha256"], "source changed during audit")
    for binding in bindings:
        require(sha(binding["path"]) == binding["sha256"], "bound evidence changed during audit: " + binding["path"])
    harness.assert_bindings(audit_args, identity)
    prompt_passed = all(row["prompt_gate_passed"] is True for row in independent_coverages)
    paths_complete = all(row["coverage_complete"] is True and row["wire_passed"] is True for row in independent_coverages)
    cells = {key: cell for row in independent_coverages for key, cell in row["cells"].items()}
    require(len(cells) == execution["observed_coverage_cell_count"] == 12, "12-cell identity differs")
    require(prompt_passed == execution["prompt_gate_passed"], "execution prompt gate differs")
    require(paths_complete == execution["coverage_complete"], "execution path coverage differs")
    require((not errors and prompt_passed and paths_complete) == execution["promotion_eligible"], "execution promotion gate differs")
    compatibility = {
        "passed": prompt_passed, "native_path_coverage_complete": paths_complete,
        "coverage_policy": identity["settings"]["native_coverage_rule"], "cells": cells,
        "jobs": independent_coverages,
        "interpretation": "Recomputed exact frozen source-owned prompt/schema plus ordered original assistant/history prefix checks. No text cleaning, score filtering or replacement sampling."
    }
    return {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(), "passed": not errors,
            "pass_scope": "Artifact/config/score/resume/raw integrity only; native-prompt compatibility is a separate gate below.",
            "native_prompt_compatibility": compatibility,
            "overall_compatibility_acceptance": not errors and compatibility["passed"] and paths_complete,
            "classification": "Real smoke validation", "scope": "One fixed 6-job/21-agent actual-loop compatibility smoke; not A21 HPO or paper performance reproduction",
            "run_directory": str(run), "source_tree_sha256": identity["source_tree_sha256"],
            "accepted_source_file_count": len(source_files), "bindings": bindings, "errors": errors,
            "records": records, "validated_trace_count": len(scores), "poolact_strategy_results": result_count,
            "guarded_skips": skips, "semantic_zero_count_preserved": sum(value == 0 for value in scores),
            "protocol_events_preserved": protocol_events,
            "protocol_failure_count": sum(len(event["failures"]) for event in protocol_events),
            "model_protocol_retry_count": sum(event["protocol_retries"] for event in protocol_events),
            "terminal_diagnostics": [{"fields": json.loads(key), "count": count} for key, count in sorted(terminals.items())],
            "blocked_model_or_network_attempts": len(blocked_calls),
            "raw_independent_receipt": {"path": str(raw_receipt), "sha256": sha(raw_receipt), "report_passed": raw.get("passed", raw.get("complete"))},
            "preservation_scope": "ExpGym traces, PoolAct result+agent JSON, and every raw dump: SHA256/size/mtime. PoolAct summaries independently checked for final aggregates/config/source only; no summary mtime invariant is claimed.",
            "limitations": ["Historical guarded-resume before snapshots are receipt evidence; current snapshots are independently matched, not retroactively reconstructed.",
                            "Offline scoring uses frozen evaluator/resume helpers with model/network denied; it is not an independent reimplementation of task semantics.",
                            "Success client dumps may have http_status=null; this is not standalone evidence of HTTP 200.",
                            "Original strict protocol remains failed; request seeds are labels only, not iid/common-random-number or deterministic guarantees.",
                            "Prompt and path classification reuse frozen audited harness helpers; they are independently rerun, not an independent parser implementation.",
                            "Graph renderer instruction grammar is checked without reconstructing graph data values or simulated-time causality.",
                            "Coverage incomplete is preserved without extra requests. This receipt does not itself authorize A21, B/C or a formal matrix."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--raw-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.resolve().is_relative_to(args.run.resolve()) or args.receipt.exists():
        parser.error("receipt must be new and outside the evidence run directory")
    sys.dont_write_bytecode = True
    result = audit(args.run, args.authorization, args.raw_receipt)
    result["audit_script_sha256"] = sha(__file__)
    with args.receipt.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("passed", "pass_scope", "overall_compatibility_acceptance",
                      "errors", "validated_trace_count", "poolact_strategy_results", "guarded_skips",
                      "protocol_failure_count", "model_protocol_retry_count")}, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
