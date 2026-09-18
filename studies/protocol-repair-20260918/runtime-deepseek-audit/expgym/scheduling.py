"""Bounded, stage-barrier-free subprocess scheduling; no model/scorer code here."""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Exclusive creation: previous attempts/results are never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def file_record(path: Path) -> Dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("expected regular artifact: %s" % path)
    before = path.stat()
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_ino) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_ino):
        raise ValueError("artifact changed while reading")
    return {"bytes": before.st_size, "sha256": checksum.hexdigest()}


def inventory(root: Path) -> Dict[str, Any]:
    """Only this invocation's owned directory; never walk unrelated study files."""
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlink in invocation output")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = file_record(path)
    if not result:
        raise ValueError("worker produced no artifacts")
    return result


@dataclass(frozen=True)
class QueueJob:
    job_id: str
    identity: Mapping[str, Any]
    command: Sequence[str]
    verify_command: Sequence[str]
    output_dir: Path
    cwd: Path
    environment: Mapping[str, str]
    endpoints: Sequence[str] = ()


def run_queue(jobs: Sequence[QueueJob], *, state_dir: Path, workers: int,
              resume: bool = False, stop_file: Optional[Path] = None,
              max_wall_seconds: Optional[float] = None) -> Dict[str, Any]:
    """Stop admission on a failed child and naturally drain other children.

    Threads only launch/wait for *separate processes*. A complete set of newly
    finished futures is inspected before admission resumes. Scores are never
    inspected, and no attempt is automatically retried. The lock is advisory
    (POSIX flock); all cooperating queue writers must use this entry point.
    """
    if type(workers) is not int or workers < 1:
        raise ValueError("workers must be positive")
    if max_wall_seconds is not None and (not math.isfinite(max_wall_seconds) or max_wall_seconds <= 0):
        raise ValueError("max_wall_seconds must be positive")
    ids = [job.job_id for job in jobs]
    if len(set(ids)) != len(ids) or any(not value or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in value) for value in ids):
        raise ValueError("unique safe job ids required")
    roots = [job.output_dir.resolve() for job in jobs]
    for index, root in enumerate(roots):
        for other in roots[:index]:
            if root == other or root in other.parents or other in root.parents:
                raise ValueError("overlapping invocation output directories")
    state_dir.mkdir(parents=True, exist_ok=True)
    import fcntl
    with (state_dir / "controller.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _run_locked(jobs, state_dir, workers, resume, stop_file, max_wall_seconds)


def _run_locked(jobs, state_dir, workers, resume, stop_file, max_wall_seconds):
    definition = {"schema": "expgym.queue-definition.v1", "jobs": [
        {"id": j.job_id, "identity": j.identity, "command": list(j.command),
         "verify_command": list(j.verify_command), "output": str(j.output_dir.resolve()),
         "cwd": str(j.cwd.resolve()), "environment": dict(j.environment),
         "endpoints": list(j.endpoints)} for j in jobs]}
    definition_path = state_dir / "definition.json"
    if definition_path.exists():
        if not resume or json.loads(definition_path.read_text()) != definition:
            raise ValueError("existing queue requires --resume and exact definition")
    else:
        write_json(definition_path, definition)
    attempts = state_dir / "sessions"
    attempts.mkdir(exist_ok=True)
    session = attempts / ("%d-%d" % (time.time_ns(), os.getpid()))
    session.mkdir()
    events = (session / "events.jsonl").open("x", encoding="utf-8")
    start = time.monotonic()
    active, reports, stops = {}, [], []
    max_active, next_index = 0, 0

    def event(kind, **fields):
        record = {"event": kind, "wall_time_ns": time.time_ns(),
                  "elapsed_seconds": time.monotonic() - start, "active": len(active), **fields}
        events.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        events.flush()

    for job in jobs:
        event("queued", job_id=job.job_id)

    def worker(job, endpoint):
        receipt_path = state_dir / "jobs" / job.job_id / "completion.json"
        begun_path = receipt_path.parent / "started.json"
        mode = "execute"
        try:
            if begun_path.exists():
                if not resume or not receipt_path.exists():
                    raise ValueError("prior begun attempt is incomplete; explicit recovery required")
                prior = json.loads(receipt_path.read_text())
                if (prior.get("identity_sha256") != digest(job.identity)
                        or type(prior.get("exit_code")) is not int or prior["exit_code"] != 0
                        or prior.get("artifacts") != inventory(job.output_dir)):
                    raise ValueError("prior completion identity/artifact mismatch")
                mode = "verify_resume"
                endpoint = json.loads(begun_path.read_text()).get("endpoint")
            else:
                if job.output_dir.exists():
                    raise ValueError("unowned output already exists")
                write_json(begun_path, {"identity_sha256": digest(job.identity),
                                       "started_time_ns": time.time_ns(), "endpoint": endpoint})
            env = os.environ.copy()
            env.update(job.environment)
            if endpoint:
                env["EXPGYM_QUEUE_ENDPOINT"] = endpoint
            command = job.verify_command if mode == "verify_resume" else job.command
            with (session / (job.job_id + ".stdout.log")).open("xb") as out, (
                    session / (job.job_id + ".stderr.log")).open("xb") as err:
                process = subprocess.Popen(list(command), cwd=job.cwd, env=env,
                                           stdout=out, stderr=err, start_new_session=True)
                code = process.wait()
            report = {"job_id": job.job_id, "mode": mode, "exit_code": code,
                      "pid": process.pid, "identity_sha256": digest(job.identity),
                      "endpoint": endpoint}
            if code == 0 and mode == "execute":
                report["artifacts"] = inventory(job.output_dir)
                write_json(receipt_path, report)
            report["passed"] = code == 0
            return report
        except BaseException as exc:
            return {"job_id": job.job_id, "mode": mode, "passed": False,
                    "error_type": type(exc).__name__, "error": str(exc)}

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            while active or (next_index < len(jobs) and not stops):
                if not stops and ((stop_file is not None and stop_file.exists()) or (
                        max_wall_seconds is not None and time.monotonic() - start >= max_wall_seconds)):
                    stops.append({"reason": "stop_file_or_admission_deadline"})
                    event("stop_new", reason=stops[-1]["reason"])
                while not stops and next_index < len(jobs) and len(active) < workers:
                    job = jobs[next_index]
                    next_index += 1
                    counts = {url: sum(assigned == url for _, assigned in active.values())
                              for url in job.endpoints}
                    endpoint = min(counts, key=counts.get) if counts else None
                    future = executor.submit(worker, job, endpoint)
                    active[future] = (job.job_id, endpoint)
                    max_active = max(max_active, len(active))
                    event("start", job_id=job.job_id, endpoint=endpoint)
                if not active:
                    break
                try:
                    completed, _ = wait(active, timeout=0.2, return_when=FIRST_COMPLETED)
                except KeyboardInterrupt:
                    stops.append({"reason": "keyboard_interrupt_stop_new_natural_drain"})
                    event("stop_new", reason=stops[-1]["reason"])
                    continue
                for future in completed:
                    job_id, endpoint = active.pop(future)
                    report = future.result()
                    reports.append(report)
                    write_json(session / (job_id + ".json"), report)
                    event("end", job_id=job_id, passed=report["passed"],
                          mode=report.get("mode"), exit_code=report.get("exit_code"))
                    if not report["passed"]:
                        stops.append({"reason": "worker_failed", "job_id": job_id})
                        event("stop_new", reason="worker_failed", job_id=job_id)
        result = {"schema": "expgym.study-queue-summary.v1", "passed": not stops,
                  "planned": len(jobs), "finished": len(reports),
                  "unstarted": [j.job_id for j in jobs[next_index:]],
                  "max_active_workers": max_active, "workers": workers,
                  "elapsed_seconds": time.monotonic() - start, "stop_reasons": stops,
                  "reports": reports, "session_dir": str(session),
                  "provider_quiescence_proven": False}
        event("drained", unstarted=len(result["unstarted"]))
        write_json(session / "summary.json", result)
        return result
    finally:
        events.close()
