#!/usr/bin/env python3
"""Copy an audited, configuration-identical pilot into the full study.

Default behavior writes promotion_plan.json without copying any artifacts.
--apply copies original bytes, refusing conflicting destinations, and writes
promotion_map.json. The full runner must subsequently use --resume to create
its own verified execution receipts. No model/API calls are made here.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

import audit_results as audit
import run_study as study


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def hash_file(path: Path) -> str:
    return audit.sha256(path)


def compare_data(source: dict, target: dict) -> dict:
    snapshot = source.get("data_provenance")
    require(bool(snapshot), "source manifest has no data_provenance snapshot")
    require(snapshot == target.get("data_provenance"), "source/target data provenance differs")
    for name, entry in snapshot.items():
        path = Path(entry["path"])
        require(bool(entry.get("sha256")) and path.is_file(), f"missing frozen data provenance: {name}")
        require(hash_file(path) == entry["sha256"], f"frozen data provenance changed: {name}")
    dataset = audit.strict_json(snapshot["dataset_manifest"]["path"])
    files = dataset.get("files", [])
    require(bool(files), "dataset manifest contains no file checksums")
    repo = Path(source["repo_root"]).resolve()
    total_bytes = 0
    for record in files:
        path = (repo / record["path"]).resolve()
        require(path.is_relative_to(repo), "dataset path escapes the repository")
        require(path.is_file() and hash_file(path) == record["sha256"],
                f"dataset checksum mismatch: {record['path']}")
        total_bytes += path.stat().st_size
    return {"snapshot": snapshot, "verified_dataset_files": len(files), "verified_dataset_bytes": total_bytes}


def comparable_namespace(args: argparse.Namespace) -> dict:
    # Output paths and resume control do not affect benchmark identities.
    return {key: value for key, value in vars(args).items() if key not in {"output_dir", "resume"}}


def native_identity(source_job: dict, target_job: dict, repo: Path) -> dict:
    sweep, pool = audit.load_runners(repo)
    runner = sweep if source_job["system"] == "expgym" else pool
    source_args = audit.parsed_command(source_job, runner)
    target_args = audit.parsed_command(target_job, runner)
    require(source_job["command"][0] == target_job["command"][0], "source/target interpreter differs")
    source_config, target_config = comparable_namespace(source_args), comparable_namespace(target_args)
    changed = sorted(key for key in set(source_config) | set(target_config)
                     if source_config.get(key) != target_config.get(key))
    require(not changed, "source/target runner arguments differ: " + ", ".join(changed))
    if source_job["system"] == "expgym":
        source_expanded, target_expanded = sweep._build_jobs(source_args), sweep._build_jobs(target_args)
        require(source_expanded == target_expanded, "expanded ExpGym logical jobs differ")
        keys = []
        for left, right in zip(source_expanded, target_expanded):
            key = sweep._resume_key(source_args, left)
            require(key == sweep._resume_key(target_args, right), "native ExpGym resume key differs")
            source_path = sweep._trace_path(source_args.output_dir, left, "v2")
            require(sweep._resume_trace_is_valid(source_path, source_args, left),
                    f"native ExpGym resume rejected source trace: {source_path}")
            keys.append(key)
        return {"method": "native_expgym_resume_key_equality_and_source_resume_validation", "resume_keys": keys}
    source_budget, _ = pool.resolve_cost_regime(source_args, pool.resolve_base_cost(source_args.scenario, source_args))
    target_budget, _ = pool.resolve_cost_regime(target_args, pool.resolve_base_cost(target_args.scenario, target_args))
    source_config, target_config = pool._resolved_config(source_args, source_budget), pool._resolved_config(target_args, target_budget)
    require(source_config == target_config, "native PoolAct resolved config differs")
    return {"method": "native_poolact_resolved_config_equality_after_complete_source_audit",
            "config_sha256": hashlib.sha256(json.dumps(source_config, sort_keys=True).encode()).hexdigest()}


def output_pairs(source_job: dict, target_job: dict) -> list[tuple[str, str, str]]:
    def key(output: dict) -> tuple:
        return output["kind"], output.get("rep"), output.get("strategy")
    target_outputs = {key(output): output for output in target_job["expected_outputs"]}
    require(len(target_outputs) == len(source_job["expected_outputs"]), "expected artifact count differs")
    pairs = []
    for source in source_job["expected_outputs"]:
        require(key(source) in target_outputs, "source artifact has no full-study counterpart")
        target = target_outputs[key(source)]
        for field in ("seed", "hypothesis_order", "agent_seeds"):
            require(source.get(field) == target.get(field), f"artifact {field} differs")
        pairs.append(("result", source["path"], target["path"]))
        require(len(source.get("agent_paths", [])) == len(target.get("agent_paths", [])), "agent count differs")
        pairs.extend(("agent", left, right) for left, right in
                     zip(source.get("agent_paths", []), target.get("agent_paths", [])))
    if source_job["summary_path"]:
        require(bool(target_job["summary_path"]), "target summary path is missing")
        pairs.append(("summary", source_job["summary_path"], target_job["summary_path"]))
    return pairs


def build_promotion(args: argparse.Namespace) -> dict:
    source = audit.strict_json(args.source_manifest)
    target = audit.strict_json(args.target_manifest)
    source_audit = audit.strict_json(args.source_audit)
    require(source.get("stage") == "pilot" and target.get("stage") == "full", "promotion requires pilot -> full stages")
    require(source.get("study_type") == target.get("study_type") == "Custom study", "promotion requires real Custom study manifests")
    require(source_audit.get("complete") is True, "source audit is not complete")
    require(source_audit.get("manifest_sha256") == hash_file(args.source_manifest), "source manifest changed since its audit")
    require(Path(source_audit["manifest_path"]).resolve() == args.source_manifest.resolve(), "audit is for a different source manifest")
    require(source["repo_root"] == target["repo_root"], "source/target repository paths differ")
    require(source["settings"] == target["settings"], "source/target fixed settings differ")
    repo = Path(source["repo_root"]).resolve()
    require(source["source_tree_sha256"] == target["source_tree_sha256"] == study.source_fingerprint(repo),
            "source/target/current repository fingerprints differ")
    require(source["counts"] == source["full_stage_counts"], "source must contain the complete pilot stage")
    require(target["counts"] == target["full_stage_counts"], "target must contain the complete full-stage plan")
    _, source_issues = audit.validate_manifest(source)
    _, target_issues = audit.validate_manifest(target)
    require(not source_issues and not target_issues, "source/target manifest matrix validation failed")
    data_validation = compare_data(source, target)

    raw_checksums = {}
    audit_records = source_audit.get("records", [])
    require(len(audit_records) == source["counts"]["expgym_traces"] + source["counts"]["poolact_results"],
            "audit record count does not match source matrix")
    for record in audit_records:
        require(record.get("status") == "valid", "source contains a non-valid audited result")
        for artifact in [record] + record.get("agent_records", []):
            require(bool(artifact.get("sha256")), "audited artifact checksum missing")
            raw_checksums[artifact["path"]] = artifact["sha256"]
        if record.get("summary_path"):
            raw_checksums[record["summary_path"]] = record["summary_sha256"]
    receipts = {entry["job_id"]: entry for entry in source_audit.get("receipts", [])}
    targets = {job["id"]: job for job in target["jobs"]}
    mappings, files = [], []

    def add_file(kind: str, job_id: str, left: str | Path, right: str | Path,
                 expected_hash: str | None = None) -> None:
        source_path, target_path = Path(left), Path(right)
        require(source_path.resolve() != target_path.resolve(), "source and destination refer to the same file")
        require(source_path.is_file(), f"source file is missing: {source_path}")
        digest = hash_file(source_path)
        if expected_hash is not None:
            require(digest == expected_hash, f"source changed after audit: {source_path}")
        require(not target_path.exists() or (target_path.is_file() and hash_file(target_path) == digest),
                f"destination exists with different content: {target_path}")
        files.append({"kind": kind, "job_id": job_id, "source": str(source_path), "target": str(target_path),
                      "sha256": digest, "bytes": source_path.stat().st_size,
                      "action": "existing_identical" if target_path.exists() else "copy"})

    for number, source_job in enumerate(source["jobs"], 1):
        job_id = source_job["id"]
        require(job_id in targets, f"pilot job has no target: {job_id}")
        target_job = targets[job_id]
        require(job_id in receipts, f"audited execution receipt is missing: {job_id}")
        receipt = receipts[job_id]
        require(hash_file(Path(source_job["status_path"])) == receipt["sha256"], "source execution status changed since audit")
        require(hash_file(Path(source_job["stdout_log"])) == receipt["stdout_sha256"], "source log changed since audit")
        identity = native_identity(source_job, target_job, repo)
        for kind, left, right in output_pairs(source_job, target_job):
            require(left in raw_checksums, f"required output was not included in the source audit: {left}")
            add_file(kind, job_id, left, right, raw_checksums[left])
        source_dump, target_dump = Path(source_job["dump_dir"]), Path(target_job["dump_dir"])
        dump_files = sorted(path for path in source_dump.rglob("*") if path.is_file())
        require(bool(dump_files), f"real pilot API dumps are missing: {source_dump}")
        for dump in dump_files:
            require(dump.suffix == ".json", f"unrecognized file in API dump directory: {dump}")
            add_file("api_dump", job_id, dump, target_dump / dump.relative_to(source_dump))
        cost_receipt_dir = Path(target["output_dir"]) / "promotion_sources" / "pilot" / job_id
        add_file("source_status", job_id, source_job["status_path"], cost_receipt_dir / "status.json", receipt["sha256"])
        add_file("source_stdout", job_id, source_job["stdout_log"], cost_receipt_dir / "stdout.log", receipt["stdout_sha256"])
        mappings.append({
            "job_id": job_id, "system": source_job["system"], "scenario": source_job["scenario"],
            "source_output_dir": source_job["output_dir"], "target_output_dir": target_job["output_dir"],
            "source_dump_dir": str(source_dump), "target_dump_dir": str(target_dump),
            "source_status_path": source_job["status_path"], "source_stdout_log": source_job["stdout_log"],
            "source_status_sha256": receipt["sha256"], "source_stdout_sha256": receipt["stdout_sha256"],
            "preserved_status_path": str(cost_receipt_dir / "status.json"),
            "preserved_stdout_log": str(cost_receipt_dir / "stdout.log"),
            "source_execution": receipt["receipt"], "native_identity": identity,
        })
        if number % 6 == 0:
            print(f"validated promotion jobs {number}/{len(source['jobs'])}", file=sys.stderr, flush=True)
    require(len({entry["target"] for entry in files}) == len(files), "promotion contains duplicate destination paths")
    return {
        "schema_version": 1, "operation": "audited_pilot_to_full", "created_at": study.utc_now(),
        "status": "planned", "source_manifest": str(args.source_manifest), "target_manifest": str(args.target_manifest),
        "source_audit": str(args.source_audit), "source_manifest_sha256": hash_file(args.source_manifest),
        "target_manifest_sha256": hash_file(args.target_manifest), "source_audit_sha256": hash_file(args.source_audit),
        "source_tree_sha256": source["source_tree_sha256"], "data_validation": data_validation,
        "counts": source["counts"], "required_json_files": sum(entry["kind"] in {"result", "agent", "summary"} for entry in files),
        "api_dump_files": sum(entry["kind"] == "api_dump" for entry in files),
        "total_bytes": sum(entry["bytes"] for entry in files), "jobs": mappings, "files": files,
        "accounting": {"raw_dump_bytes_unchanged": True, "keep_original_run_id_and_context": True,
                       "deduplicate_across_pilot_and_full_by": "request_id",
                       "cost_and_timing_source": "source_execution and preserved pilot status/log/API dump; full resume time is additional validation overhead"},
        "next_step": "run the complete full stage with run_study.py --resume; then audit its canonical manifest.json",
    }


def copy_unchanged(entry: dict) -> None:
    source, target = Path(entry["source"]), Path(entry["target"])
    require(hash_file(source) == entry["sha256"], f"source changed before copy: {source}")
    if target.exists():
        require(target.is_file() and hash_file(target) == entry["sha256"], f"destination conflict: {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=target.name + ".promotion.", dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copyfile(source, temporary)
        require(hash_file(temporary) == entry["sha256"], f"copied data checksum mismatch: {target}")
        # link() publishes atomically and refuses a destination created by a
        # concurrent writer. Unlike replace(), it cannot overwrite that file.
        try:
            os.link(temporary, target)
        except FileExistsError:
            require(target.is_file() and hash_file(target) == entry["sha256"], f"concurrent destination conflict: {target}")
    finally:
        temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--target-manifest", type=Path, required=True)
    parser.add_argument("--source-audit", type=Path, required=True, help="complete audit.json for the source pilot manifest")
    parser.add_argument("--output", type=Path, help="default: full output directory / promotion_plan.json or promotion_map.json")
    parser.add_argument("--apply", action="store_true", help="copy already-validated source bytes into the full-study paths")
    parser.add_argument("--dry-run", action="store_true", help="explicitly select the default plan-only behavior")
    args = parser.parse_args()
    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run are mutually exclusive")
    for field in ("source_manifest", "target_manifest", "source_audit"):
        setattr(args, field, getattr(args, field).expanduser().absolute())
    if args.output:
        args.output = args.output.expanduser().absolute()
    return args


def main() -> int:
    args = parse_args()
    try:
        source, target = audit.strict_json(args.source_manifest), audit.strict_json(args.target_manifest)
        roots = sorted({Path(source["output_dir"]).resolve(), Path(target["output_dir"]).resolve()})
        with ExitStack() as stack:
            for root in roots:
                require(root.is_dir(), f"study output directory does not exist: {root}")
                lock = stack.enter_context((root / ".harness.lock").open("a"))
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    raise ValueError(f"study is currently running: {root}") from error
            plan = build_promotion(args)
            output = args.output or Path(target["output_dir"]) / ("promotion_map.json" if args.apply else "promotion_plan.json")
            if output.exists():
                previous = audit.strict_json(output)
                require(previous.get("source_manifest_sha256") == plan["source_manifest_sha256"] and
                        previous.get("target_manifest_sha256") == plan["target_manifest_sha256"],
                        "promotion report already exists for different manifests; use --output")
                study.atomic_json(output.parent / "promotion_history" / f"{time.time_ns()}.{output.name}", previous)
            if args.apply:
                plan["status"] = "copying"
                study.atomic_json(output, plan)
                try:
                    for number, entry in enumerate(plan["files"], 1):
                        copy_unchanged(entry)
                        if number % 100 == 0:
                            print(f"copied/verified files {number}/{len(plan['files'])}", file=sys.stderr, flush=True)
                    plan["status"] = "copied_pending_full_runner_resume"
                    plan["finished_at"] = study.utc_now()
                except Exception as error:
                    plan["status"] = "copy_failed"
                    plan["error"] = f"{type(error).__name__}: {error}"
                    study.atomic_json(output, plan)
                    raise
            study.atomic_json(output, plan)
            print(json.dumps({"status": plan["status"], "output": str(output), "counts": plan["counts"],
                              "required_json_files": plan["required_json_files"], "api_dump_files": plan["api_dump_files"]}), flush=True)
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"promotion error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
