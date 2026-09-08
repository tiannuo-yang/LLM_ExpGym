"""Read-only byte/set snapshots of manifest-selected result and API dump JSON."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

SNAPSHOT_SCHEMA = "kimi-k3.resume-integrity.snapshot.v1"
COMPARE_SCHEMA = "kimi-k3.resume-integrity.comparison.v1"


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def absolute_path(value, parent):
    path = Path(value).expanduser()
    return (path if path.is_absolute() else parent / path).resolve()


def beneath(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def read_manifest(path):
    path = path.resolve()
    raw = path.read_bytes()
    manifest = json.loads(raw)
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("Manifest must contain a nonempty jobs list")
    roots = []
    excluded = {str(path): "Input manifest is orchestration metadata"}
    job_ids = set()
    for job in jobs:
        if not isinstance(job, dict) or not isinstance(job.get("id"), str):
            raise ValueError("Every job requires a string id")
        if job["id"] in job_ids:
            raise ValueError("Duplicate job id: " + job["id"])
        job_ids.add(job["id"])
        for field, kind in [("output_dir", "output_json"), ("dump_dir", "api_dump_json")]:
            value = job.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError("Job {} requires {}".format(job["id"], field))
            roots.append({"job_id": job["id"], "kind": kind, "path": str(absolute_path(value, path.parent))})
        for field in ("status_path", "stdout_log"):
            if job.get(field):
                excluded[str(absolute_path(job[field], path.parent))] = "Job orchestration " + field
    if manifest.get("progress_path"):
        excluded[str(absolute_path(manifest["progress_path"], path.parent))] = "Study orchestration progress"
    return {
        "path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
        "job_count": len(jobs), "roots": sorted(roots, key=lambda item: (item["job_id"], item["kind"], item["path"])),
        "excluded_paths": excluded,
    }


def stat_signature(stat):
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def hash_file(path):
    before = path.stat()
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    after = path.stat()
    if stat_signature(before) != stat_signature(after) or size != after.st_size:
        raise RuntimeError("File changed while hashing: " + str(path))
    return {"bytes": size, "sha256": digest.hexdigest(), "_signature": stat_signature(after)}


def raise_walk_error(error):
    raise error


def enumerate_files(scope):
    owners = {}
    missing_roots = []
    excluded_seen = set()
    for root in scope["roots"]:
        directory = Path(root["path"])
        if not directory.exists():
            missing_roots.append(root)
            continue
        if not directory.is_dir():
            raise ValueError("Monitored root is not a directory: " + str(directory))
        for current, subdirectories, filenames in os.walk(str(directory), followlinks=False, onerror=raise_walk_error):
            for name in subdirectories:
                child = Path(current) / name
                if child.is_symlink():
                    raise ValueError("Symlink directory cannot be silently omitted: " + str(child))
            for name in filenames:
                if not name.endswith(".json"):
                    continue
                path = str(Path(current) / name)
                if str(Path(path).resolve()) in scope["excluded_paths"]:
                    excluded_seen.add(path)
                    continue
                owners.setdefault(path, set()).add((root["job_id"], root["kind"]))
    return owners, missing_roots, sorted(excluded_seen)


def summarize(files):
    by_kind = {kind: {"files": 0, "bytes": 0} for kind in ("output_json", "api_dump_json")}
    for record in files:
        for kind in {owner["kind"] for owner in record["owners"]}:
            by_kind[kind]["files"] += 1
            by_kind[kind]["bytes"] += record["bytes"]
    canonical = [{key: record[key] for key in ("path", "bytes", "sha256")} for record in files]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"total_files": len(files), "total_bytes": sum(record["bytes"] for record in files), "by_kind": by_kind, "file_set_sha256": hashlib.sha256(encoded).hexdigest()}


def collect(scope):
    owners, missing, excluded_seen = enumerate_files(scope)
    files = []
    signatures = {}
    for path in sorted(owners):
        hashed = hash_file(Path(path))
        signatures[path] = hashed.pop("_signature")
        record = {"path": path, **hashed, "owners": [{"job_id": job_id, "kind": kind} for job_id, kind in sorted(owners[path])]}
        files.append(record)
    owners_after, missing_after, excluded_after = enumerate_files(scope)
    if owners_after != owners or missing_after != missing or excluded_after != excluded_seen:
        raise RuntimeError("File collection changed while scanning; snapshot/compare requires quiescent jobs")
    for path, signature in signatures.items():
        if stat_signature(Path(path).stat()) != signature:
            raise RuntimeError("File changed before the scan completed: " + path)
    return {"files": files, "totals": summarize(files), "missing_roots": missing, "excluded_paths_encountered": excluded_seen}


def exclusions(scope):
    return {
        "included": ["Every .json file recursively under each job.output_dir, including summaries and agent traces", "Every .json file recursively under each job.dump_dir, including all request attempts/states"],
        "excluded": ["Paths outside manifest-selected job output/dump roots", "Non-JSON files, including logs and lock files", "The input manifest and explicitly identified orchestration progress/status/stdout paths", "Snapshot/comparison reports, which must be stored outside all monitored roots"],
        "explicit_paths": [{"path": path, "reason": reason} for path, reason in sorted(scope["excluded_paths"].items())],
        "manifest_policy": "Manifest byte hashes are recorded for provenance. Metadata-only changes are allowed; changed job ids, roots, or exclusion paths fail comparison.",
        "comparison_scope": "JSON file collection and raw bytes; this does not independently validate benchmark completeness or semantic scores.",
    }


def ensure_fresh_report(path, roots, protected):
    if os.path.lexists(str(path)):
        raise FileExistsError("Refusing to overwrite report: " + str(path))
    path = path.resolve()
    if path.exists():
        raise FileExistsError("Refusing to overwrite report: " + str(path))
    if path in protected:
        raise ValueError("Report cannot replace an input: " + str(path))
    for root in roots:
        if beneath(path, Path(root["path"])):
            raise ValueError("Report must be outside monitored roots: " + str(path))
    return path


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def compare(snapshot, current, scope):
    before = {record["path"]: record for record in snapshot["files"]}
    if len(before) != len(snapshot["files"]):
        raise ValueError("Snapshot contains duplicate file paths")
    after = {record["path"]: record for record in current["files"]}
    added = [after[path] for path in sorted(after.keys() - before.keys())]
    removed = [before[path] for path in sorted(before.keys() - after.keys())]
    changed = [{"path": path, "before": before[path], "after": after[path]} for path in sorted(before.keys() & after.keys()) if before[path] != after[path]]
    old_scope = snapshot["manifest"]
    scope_unchanged = old_scope["roots"] == scope["roots"] and old_scope["excluded_paths"] == scope["excluded_paths"]
    root_availability_unchanged = snapshot["missing_roots"] == current["missing_roots"]
    return {
        "passed": not added and not removed and not changed and scope_unchanged and root_availability_unchanged,
        "added": added, "removed": removed, "changed": changed,
        "difference_counts": {"added": len(added), "removed": len(removed), "changed": len(changed)},
        "before_totals": snapshot["totals"], "after_totals": current["totals"],
        "scope_unchanged": scope_unchanged,
        "root_availability_unchanged": root_availability_unchanged,
        "missing_roots_before": snapshot["missing_roots"],
        "missing_roots_after": current["missing_roots"],
        "scope_before": old_scope["roots"], "scope_after": scope["roots"],
        "manifest_bytes_unchanged": old_scope["sha256"] == scope["sha256"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("snapshot", "compare"):
        subparser = commands.add_parser(command)
        subparser.add_argument("--manifest", type=Path, required=True)
        subparser.add_argument("--report", type=Path, required=True, help="New report path outside monitored roots; existing reports are never overwritten.")
        if command == "compare":
            subparser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        scope = read_manifest(args.manifest)
        roots = list(scope["roots"])
        protected = {args.manifest.resolve()}
        baseline = None
        if args.command == "compare":
            baseline_bytes = args.snapshot.read_bytes()
            baseline = json.loads(baseline_bytes)
            if baseline.get("schema_version") != SNAPSHOT_SCHEMA:
                raise ValueError("Unrecognized baseline snapshot schema")
            if baseline["totals"] != summarize(baseline["files"]):
                raise ValueError("Baseline totals/file-set digest disagree with its records")
            roots.extend(baseline["manifest"]["roots"])
            protected.add(args.snapshot.resolve())
        output = ensure_fresh_report(args.report, roots, protected)
        current = collect(scope)
        common = {"created_at": utc_now(), "manifest": scope, "expected_exclusions": exclusions(scope), "missing_roots": current["missing_roots"], "excluded_paths_encountered": current["excluded_paths_encountered"]}
        if baseline is None:
            report = {"schema_version": SNAPSHOT_SCHEMA, **common, "files": current["files"], "totals": current["totals"]}
            status = 0
            terminal = {"snapshot": str(output), "totals": current["totals"]}
        else:
            report = {"schema_version": COMPARE_SCHEMA, **common, "baseline_snapshot": str(args.snapshot.resolve()), "baseline_snapshot_sha256": hashlib.sha256(baseline_bytes).hexdigest(), **compare(baseline, current, scope)}
            status = 0 if report["passed"] else 1
            terminal = {"report": str(output), "passed": report["passed"], "difference_counts": report["difference_counts"], "before_totals": report["before_totals"], "after_totals": report["after_totals"], "scope_unchanged": report["scope_unchanged"], "root_availability_unchanged": report["root_availability_unchanged"]}
        write_report(output, report)
        print(json.dumps(terminal, sort_keys=True))
        return status
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print("resume_integrity: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
