#!/usr/bin/env python3
"""Run the fixed Kimi-K3 custom study through the repository's own runners.

The orchestration process requires Python 3.11 and only the standard library.
It never skips results itself: --resume delegates validation to each runner.
PoolAct's three strategies remain in one subprocess with its original locks.

Send SIGUSR1 to this harness PID to stop dispatching and let submitted jobs
finish normally (progress: drained; exit: 75). SIGINT/SIGTERM interrupt active
children instead (exit: 130). Never send SIGUSR1 to an older harness version.
SIGUSR1 is reserved for the harness; its worker threads and child runners
inherit a blocked SIGUSR1 mask. SIGINT/SIGTERM retain their existing behavior.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit


STUDY_ROOT = Path(__file__).resolve().parents[1]
REGIMES = ["cost_free", "cost_moderate", "cost_tight"]
STRATEGIES = ["naive", "cached", "poolact"]
HPO_TASKS = [
    "hpobench:paramnet:adult:steps",
    "hpobench:paramnet:higgs:steps",
    "hpobench:paramnet:letter:steps",
    "hpobench:nasbench101:A",
    "hpobench:nasbench101:B",
    "hpobench:nasbench101:C",
    "hpobench:nasbench201:cifar10-valid",
    "hpobench:nasbench201:cifar100",
    "hpobench:nasbench201:imagenet16-120",
]
SEED = 1206
DRAIN_EXIT_CODE = 75


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "x"


def source_fingerprint(repo_root: Path) -> str:
    # Invoke the authoritative implementation without importing optional HPO
    # dependencies or replicating its source-file selection rules.
    spec = importlib.util.spec_from_file_location(
        "study_trace_v2", repo_root / "expgym" / "trace_v2.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load repository trace fingerprint implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.source_tree_sha256(repo_root)


def git_commit(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root,
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def data_provenance(repo_root: Path) -> dict:
    paths = {
        "dataset_manifest": STUDY_ROOT / "data_runtime/dataset_manifest.json",
        "oracle": repo_root / "data/hpo_tuning/oracle3.json",
        "audit_orders": repo_root / "configs/audit_hypothesis_orders.json",
    }
    return {name: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
                   if path.is_file() else None} for name, path in paths.items()}


def settings_for(args: argparse.Namespace) -> dict:
    smoke = args.stage == "smoke"
    orders_path = args.repo_root / "configs" / "audit_hypothesis_orders.json"
    orders_data = load_json(orders_path)
    orders = orders_data.get("orders", [])
    if len(orders) != 3 or any(len(order) != 17 or len(set(order)) != 17 for order in orders):
        raise ValueError("the study requires exactly three complete 17-hypothesis audit orders")
    if any(set(order) != set(orders[0]) for order in orders):
        raise ValueError("the three audit orders must permute the same hypotheses")
    if len({tuple(order) for order in orders}) != 3:
        raise ValueError("the three audit hypothesis orders must be distinct")
    return {
        "backend": "openai", "model": args.model, "model_alias": "Kimi-K3",
        "seed": SEED, "expgym_seed_rule": "1206 + rep", "poolact_seed_rule": "1206 + agent_id",
        "max_steps": 4 if smoke else 30, "max_evals": 3 if smoke else 30,
        "temperature_tuning": 0.7, "temperature_eval": 0.0, "temperature_poolact": 0.7,
        "tuning_reps": 1 if smoke else 3, "search_reps": 1, "audit_reps": 1 if smoke else 3,
        "poolact_agents": 2 if smoke else 4, "poolact_strategies": STRATEGIES,
        "search_data_source": "phantom_seed1", "cc_split": "cc-large",
        "audit_orders_path": str(orders_path), "audit_orders": orders,
        "audit_orders_sha256": hashlib.sha256(orders_path.read_bytes()).hexdigest(),
        "poolact_hypothesis_order": None,
        "max_tokens": args.max_tokens, "chat_template_kwargs": args.chat_template_kwargs,
        "base_url": args.base_url, "request_timeout": args.request_timeout,
        "max_retries": args.max_retries, "retry_base_seconds": args.retry_base_seconds,
        "retry_max_seconds": args.retry_max_seconds,
        "prompt_cache": "disabled", "trace_format": "v2",
        "poolact_protocol": "paper-graph-lock-v2",
    }


def stage_items(stage: str) -> list[tuple[str, str | int]]:
    if stage == "smoke":
        return [("tuning", HPO_TASKS[3]), ("restricted_search", 0), ("evidence_audit", 0)]
    if stage == "pilot":
        return [
            ("tuning", HPO_TASKS[0]), ("tuning", HPO_TASKS[3]), ("tuning", HPO_TASKS[6]),
            ("restricted_search", 0), ("restricted_search", 18), ("evidence_audit", 0),
        ]
    return ([("tuning", task) for task in HPO_TASKS]
            + [("restricted_search", index) for index in range(35)]
            + [("evidence_audit", index) for index in range(13)])


def make_job(args: argparse.Namespace, settings: dict, system: str,
             scenario: str, item: str | int, regime: str) -> dict:
    job_id = "__".join([system, scenario, slug(str(item)), regime])
    output_dir = args.output_dir / system / scenario / slug(str(item)) / regime
    log_dir = args.logs_dir / args.run_namespace / job_id
    is_tuning = scenario == "tuning"
    task = str(item) if is_tuning else None
    index = 0 if is_tuning else int(item)
    is_paramnet = bool(task and task.startswith("hpobench:paramnet:"))
    python = args.paramnet_python if is_paramnet else args.python
    runner = "run_paper_sweep.py" if system == "expgym" else "run_poolact.py"
    command = [str(python), "-u", str(args.repo_root / "scripts" / runner),
               "--backend", "openai", "--base-url", args.base_url,
               "--output-dir", str(output_dir), "--seed", str(SEED),
               "--max-steps", str(settings["max_steps"]),
               "--max-evals", str(settings["max_evals"]),
               "--request-timeout", str(args.request_timeout),
               "--max-retries", str(args.max_retries),
               "--retry-base-seconds", str(args.retry_base_seconds),
               "--retry-max-seconds", str(args.retry_max_seconds)]
    if args.max_tokens is not None:
        command += ["--max-tokens", str(args.max_tokens)]
    if args.chat_template_kwargs is not None:
        command += ["--chat-template-kwargs", json.dumps(args.chat_template_kwargs, sort_keys=True)]
    if args.resume:
        command.append("--resume")
    expected = []
    rep_count = 1
    if system == "expgym":
        command += ["--models", "Kimi-K3", "--model-alias", f"Kimi-K3={args.model}", "--scenarios", scenario,
                    "--cost-regimes", regime, "--trace-format", "v2",
                    "--prompt-cache-scope", "disabled",
                    "--temperature-tuning", "0.7", "--temperature-eval", "0.0",
                    "--tuning-reps", str(settings["tuning_reps"]),
                    "--search-reps", str(settings["search_reps"]),
                    "--audit-reps", str(settings["audit_reps"]),
                    "--audit-orders", settings["audit_orders_path"],
                    "--cc-split", "cc-large", "--search-data-source", "phantom_seed1"]
        selector = {"tuning": "--tuning-tasks", "restricted_search": "--search-indices",
                    "evidence_audit": "--audit-indices"}[scenario]
        command += [selector, str(item)]
        rep_count = settings[{"tuning": "tuning_reps", "restricted_search": "search_reps",
                              "evidence_audit": "audit_reps"}[scenario]]
        for rep in range(rep_count):
            seed = SEED + rep
            if is_tuning:
                filename = f"tuning_{slug(task)}_r{rep}_s{seed}.json"
            elif scenario == "restricted_search":
                filename = f"restricted_search_phantom_seed1_{index}_r{rep}_s{seed}.json"
            else:
                filename = f"evidence_audit_cc-large_{index}_r{rep}_s{seed}.json"
            path = output_dir / f"Kimi-K3_{regime}" / "traces-v2" / filename
            expected.append({"kind": "expgym_trace", "path": str(path), "rep": rep,
                             "seed": seed, "hypothesis_order": settings["audit_orders"][rep]
                             if scenario == "evidence_audit" else None})
    else:
        command += ["--model", args.model, "--scenario", scenario,
                    "--cost-regime", regime, "--strategies", ",".join(STRATEGIES),
                    "--agents", str(settings["poolact_agents"]), "--temperature", "0.7",
                    "--cc-split", "cc-large", "--data-source", "phantom_seed1"]
        command += ["--question-index", str(index)]
        if is_tuning:
            command += ["--tuning-task", task]
        for strategy in STRATEGIES:
            expected.append({
                "kind": "poolact_result", "path": str(output_dir / strategy / "result.json"),
                "strategy": strategy,
                "agent_paths": [str(output_dir / strategy / "agents" / f"agent_{agent}.json")
                                for agent in range(settings["poolact_agents"])],
                "agent_seeds": [SEED + agent for agent in range(settings["poolact_agents"])],
            })
    paper_subset = (system == "poolact" and regime != "cost_free" and
                    (scenario == "evidence_audit" or
                     (scenario == "restricted_search" and index < 18) or
                     (is_tuning and task == "hpobench:nasbench101:A")))
    return {
        "id": job_id, "system": system, "scenario": scenario, "item_id": str(item),
        "tuning_task": task, "question_index": index, "cost_regime": regime,
        "rep_count": rep_count, "temperature": 0.7 if system == "poolact" or is_tuning else 0.0,
        "agents": settings["poolact_agents"] if system == "poolact" else 1,
        "strategies": STRATEGIES if system == "poolact" else [], "seed": SEED,
        "runtime": "paramnet_legacy" if is_paramnet else "main_uv",
        "output_dir": str(output_dir), "dump_dir": str(args.dumps_dir / args.run_namespace / job_id),
        "stdout_log": str(log_dir / "stdout.log"), "status_path": str(log_dir / "status.json"),
        "command": command, "paper_subset": paper_subset, "expected_outputs": expected,
        "summary_path": str(output_dir / "summary.json") if system == "poolact" else None,
    }


def count_jobs(jobs: list[dict]) -> dict:
    expgym = sum(len(job["expected_outputs"]) for job in jobs if job["system"] == "expgym")
    poolact = sum(len(job["expected_outputs"]) for job in jobs if job["system"] == "poolact")
    agents = sum(len(job["expected_outputs"]) * job["agents"] for job in jobs if job["system"] == "poolact")
    paper = [job for job in jobs if job["paper_subset"]]
    return {
        "subprocess_jobs": len(jobs), "expgym_traces": expgym,
        "poolact_results": poolact, "poolact_agent_traces": agents,
        "total_agent_traces": expgym + agents,
        "poolact_paper_results": sum(len(job["expected_outputs"]) for job in paper),
        "poolact_paper_agent_traces": sum(len(job["expected_outputs"]) * job["agents"] for job in paper),
    }


def build_manifest(args: argparse.Namespace) -> dict:
    settings = settings_for(args)
    jobs = []
    # Interleave systems and regimes so a limited pilot samples both runners.
    for scenario, item in stage_items(args.stage):
        for regime in REGIMES:
            for system in ("expgym", "poolact"):
                if args.stage == "smoke" and system == "poolact" and regime == "cost_free":
                    continue
                jobs.append(make_job(args, settings, system, scenario, item, regime))
    stage_counts = count_jobs(jobs)
    if args.stage == "full" and stage_counts != {
        "subprocess_jobs": 342, "expgym_traces": 303, "poolact_results": 513,
        "poolact_agent_traces": 2052, "total_agent_traces": 2355,
        "poolact_paper_results": 192, "poolact_paper_agent_traces": 768,
    }:
        raise AssertionError(f"full study matrix drifted: {stage_counts}")
    if args.part != "both":
        jobs = [job for job in jobs if job["system"] == args.part]
    if args.job_ids:
        selected = {item.strip() for item in args.job_ids.split(",") if item.strip()}
        unknown = selected - {job["id"] for job in jobs}
        if unknown:
            raise ValueError("unknown or excluded --job-ids: " + ", ".join(sorted(unknown)))
        jobs = [job for job in jobs if job["id"] in selected]
    if args.limit is not None:
        jobs = jobs[:args.limit]
    if not jobs:
        raise ValueError("the selected matrix is empty")
    manifest = {
        "schema_version": 1, "study_type": "Custom study", "stage": args.stage,
        "created_at": utc_now(), "dry_run": args.dry_run,
        "repo_root": str(args.repo_root), "repo_commit": git_commit(args.repo_root),
        "source_tree_sha256": source_fingerprint(args.repo_root),
        "data_provenance": data_provenance(args.repo_root),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "output_dir": str(args.output_dir), "run_namespace": args.run_namespace,
        "progress_path": str(args.output_dir / "progress.json"),
        "settings": settings, "full_stage_counts": stage_counts, "counts": count_jobs(jobs),
        "selection": {"part": args.part, "job_ids": args.job_ids, "limit": args.limit},
        "workers": args.workers, "resume": args.resume,
        "resume_policy": "every selected job invokes the original runner; only the runner validates/skips",
        "credential_environment_names": ["OPENAI_API_KEY"],
        "jobs": jobs,
    }
    promotion_path = args.output_dir / "promotion_map.json"
    if promotion_path.is_file():
        manifest["promotion_map"] = str(promotion_path)
    return manifest


def runtime_environment(args: argparse.Namespace, job: dict) -> dict:
    environment = os.environ.copy()
    # Local serving uses a fixed dummy key. Never serialize this environment.
    environment["OPENAI_API_KEY"] = "EXPGYM_LOCAL_NOAUTH_PLACEHOLDER_20260907"
    environment["OPENAI_BASE_URL"] = args.base_url
    environment["EXPGYM_API_DUMP_DIR"] = job["dump_dir"]
    environment["EXPGYM_RUN_ID"] = f"kimi-k3/{args.run_namespace}/{job['id']}"
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONUNBUFFERED"] = "1"
    environment["PYTHONPATH"] = str(args.repo_root)
    environment["HPOBENCH_ROOT"] = str(args.repo_root / "data/hpo_tuning/HPOBench")
    environment["XDG_DATA_HOME"] = str(args.repo_root / "data/hpo_tuning/hpobench_data")
    environment["XDG_CACHE_HOME"] = str(args.repo_root / "data/hpo_tuning/hpobench_cache")
    environment["XDG_CONFIG_HOME"] = str(STUDY_ROOT / "data_runtime/hpobench_config")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        environment[name] = str(args.hpo_threads)
    # Make generation settings depend only on explicit CLI arguments.
    for name in ("EXPGYM_MAX_TOKENS", "EXPGYM_CHAT_TEMPLATE_KWARGS", "EXPGYM_PROMPT_CACHE_KEY"):
        environment.pop(name, None)
    return environment


def expected_files(job: dict) -> list[Path]:
    paths = [Path(output["path"]) for output in job["expected_outputs"]]
    paths.extend(Path(path) for output in job["expected_outputs"] for path in output.get("agent_paths", []))
    if job["summary_path"]:
        paths.append(Path(job["summary_path"]))
    return paths


def execute_job(args: argparse.Namespace, job: dict, stop: threading.Event) -> dict:
    status_path = Path(job["status_path"])
    previous = load_json(status_path)
    attempts = previous.get("attempts", [])
    attempt = {
        "number": len(attempts) + 1, "started_at": utc_now(), "finished_at": None,
        "wall_time_seconds": None, "returncode": None, "status": "running",
        "stdout_log": job["stdout_log"],
    }
    status = {"job_id": job["id"], **attempt, "attempts": attempts + [attempt]}
    atomic_json(status_path, status)
    log_path = Path(job["stdout_log"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    Path(job["dump_dir"]).mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    process = None
    try:
        with log_path.open("ab", buffering=0) as log:
            log.write(("\nHARNESS ATTEMPT " + json.dumps(attempt, sort_keys=True) + "\n").encode())
            attempt["stdout_start_byte"] = log.tell()
            if stop.is_set():
                raise InterruptedError("study interrupted before job launch")
            process = subprocess.Popen(job["command"], cwd=args.repo_root,
                                       env=runtime_environment(args, job), stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            attempt["pid"] = process.pid
            atomic_json(status_path, {**status, **attempt})
            while process.poll() is None:
                if stop.wait(timeout=1):
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    break
            attempt["returncode"] = process.returncode
            attempt["stdout_end_byte"] = log.tell()
        missing = [str(path) for path in expected_files(job) if not path.is_file()]
        attempt["missing_outputs"] = missing
        if attempt["returncode"] == 0 and missing:
            attempt["returncode"] = 66
            attempt["error"] = "runner returned zero but required output files are missing"
        attempt["status"] = ("completed" if attempt["returncode"] == 0 else
                             "interrupted" if stop.is_set() else "failed")
    except Exception as error:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        attempt["returncode"] = 130 if stop.is_set() else 70
        attempt["status"] = "interrupted" if stop.is_set() else "failed"
        attempt["error"] = f"{type(error).__name__}: {error}"
    attempt["finished_at"] = utc_now()
    attempt["wall_time_seconds"] = time.monotonic() - start
    status = {"job_id": job["id"], **attempt, "attempts": attempts + [attempt]}
    atomic_json(status_path, status)
    return status


def execute_study(args: argparse.Namespace, manifest: dict) -> int:
    jobs = manifest["jobs"]
    missing_runtimes = sorted({job["command"][0] for job in jobs if not os.access(job["command"][0], os.X_OK)})
    if missing_runtimes:
        raise ValueError("runner Python executable is unavailable: " + ", ".join(missing_runtimes))
    stop = threading.Event()
    drain = threading.Event()
    drain_requested = False

    def request_drain(_number: int, _frame: object) -> None:
        nonlocal drain_requested
        # Python handlers can be reentered by another USR1. Latch with a
        # simple assignment before Event.set() takes its non-reentrant lock.
        if drain_requested:
            return
        drain_requested = True
        drain.set()

    old_handlers = {signum: signal.signal(signum, lambda _number, _frame: stop.set())
                    for signum in (signal.SIGINT, signal.SIGTERM)}
    old_handlers[signal.SIGUSR1] = signal.signal(signal.SIGUSR1, request_drain)
    started_at, start = utc_now(), time.monotonic()
    statuses = {job["id"]: {"status": "pending", "returncode": None} for job in jobs}
    progress_path = Path(manifest["progress_path"])

    def write_progress(final: bool = False, control: tuple[bool, bool] | None = None) -> None:
        interrupted, draining = control if control is not None else (stop.is_set(), drain.is_set())
        tally = {state: sum(value["status"] == state for value in statuses.values())
                 for state in ("pending", "running", "completed", "failed", "interrupted")}
        completed = [job for job in jobs if statuses[job["id"]]["status"] == "completed"]
        atomic_json(progress_path, {
            "schema_version": 1, "stage": args.stage, "started_at": started_at,
            "updated_at": utc_now(), "finished_at": utc_now() if final else None,
            "wall_time_seconds": time.monotonic() - start,
            "status": ("interrupted" if interrupted else "drained" if draining else
                       "failed" if tally["failed"] else "completed") if final else
                      ("interrupting" if interrupted else "draining" if draining else "running"),
            "drain_requested": draining, "interruption_requested": interrupted,
            "all_selected_jobs_complete": tally["completed"] == len(jobs),
            "exit_code": (130 if interrupted else DRAIN_EXIT_CODE if draining else
                          1 if tally["completed"] != len(jobs) else 0) if final else None,
            "job_counts": tally, "expected_counts": manifest["counts"],
            "completed_counts": count_jobs(completed), "jobs": statuses,
        })

    iterator = iter(jobs)
    futures: dict[concurrent.futures.Future, dict] = {}
    last_update = time.monotonic()
    drain_announced = False
    try:
        write_progress()
        print("Harness controls: SIGUSR1 stops new dispatch and waits for active jobs (exit 75); "
              "SIGINT/SIGTERM interrupt active jobs (exit 130).", flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            while True:
                if drain.is_set() and not drain_announced:
                    print("SIGUSR1 drain requested: no new jobs will be dispatched; "
                          "submitted jobs will finish and persist their results.", flush=True)
                    drain_announced = True
                    write_progress()
                submitted = False
                while len(futures) < args.workers and not stop.is_set() and not drain.is_set():
                    # Selection/submission is one short dispatch transaction.
                    # Defer USR1 until it ends, so an accepted drain cannot fall
                    # between checking the gate and submitting another job.
                    # Pool workers inherit the mask; USR1 is a harness-only
                    # control signal. SIGINT/SIGTERM remain unmasked.
                    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGUSR1})
                    try:
                        if stop.is_set() or drain.is_set():
                            break
                        job = next(iterator, None)
                        if job is None:
                            break
                        future = executor.submit(execute_job, args, job, stop)
                        futures[future] = job
                        statuses[job["id"]] = {"status": "running", "returncode": None,
                                                "status_path": job["status_path"]}
                        submitted = True
                    finally:
                        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
                if submitted:
                    write_progress()
                if not futures:
                    break
                done, _ = concurrent.futures.wait(futures, timeout=1,
                                                  return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    job = futures.pop(future)
                    try:
                        statuses[job["id"]] = future.result()
                    except Exception as error:
                        statuses[job["id"]] = {"status": "failed", "returncode": 70,
                                                "error": f"{type(error).__name__}: {error}"}
                    status = statuses[job["id"]]
                    done_count = sum(value["status"] in {"completed", "failed", "interrupted"}
                                     for value in statuses.values())
                    print(f"[{done_count}/{len(jobs)}] {job['id']}: {status['status']} "
                          f"rc={status['returncode']}", flush=True)
                if done or time.monotonic() - last_update >= 30:
                    write_progress()
                    last_update = time.monotonic()
        # All submitted jobs have returned, including their final receipt
        # writes. Snapshot control once: a late signal during JSON writing
        # must not disagree with the final status and process exit code.
        terminal_control = (stop.is_set(), drain.is_set())
        write_progress(final=True, control=terminal_control)
        exit_code = (130 if terminal_control[0] else DRAIN_EXIT_CODE if terminal_control[1] else
                     1 if any(value["status"] != "completed" for value in statuses.values()) else 0)
        if terminal_control[1] and not terminal_control[0]:
            pending = sum(value["status"] == "pending" for value in statuses.values())
            print(f"Harness drained: all submitted jobs settled; {pending} jobs remain pending; "
                  f"exit {DRAIN_EXIT_CODE}.", flush=True)
    finally:
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
    return exit_code


def json_object(value: str) -> dict:
    try:
        result = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"invalid JSON: {error}") from error
    if not isinstance(result, dict):
        raise argparse.ArgumentTypeError("must be a JSON object")
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("smoke", "pilot", "full"), required=True)
    parser.add_argument("--base-url", required=True, help="local SGLang OpenAI API URL, including /v1")
    parser.add_argument("--model", default="kimi-k3", help="served API model ID (study artifact alias remains Kimi-K3)")
    parser.add_argument("--repo-root", type=Path, default=STUDY_ROOT.parent / "LLM_ExpGym")
    parser.add_argument("--python", type=Path, default=None, help="default: REPO/.venv/bin/python")
    parser.add_argument("--paramnet-python", type=Path, default=STUDY_ROOT / "data_runtime/.venv-hpo/bin/python")
    parser.add_argument("--output-dir", type=Path, help="default: STUDY/runs/STAGE")
    parser.add_argument("--logs-dir", type=Path, default=STUDY_ROOT / "logs")
    parser.add_argument("--dumps-dir", type=Path, default=STUDY_ROOT / "dumps")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--hpo-threads", type=int, default=1)
    parser.add_argument("--part", choices=("both", "expgym", "poolact"), default="both")
    parser.add_argument("--job-ids", help="comma-separated stable job IDs from the manifest")
    parser.add_argument("--limit", type=int, help="select the first N jobs after other filters")
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--chat-template-kwargs", type=json_object, default=None)
    parser.add_argument("--request-timeout", type=float, default=600.0)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--retry-base-seconds", type=float, default=1.0)
    parser.add_argument("--retry-max-seconds", type=float, default=30.0)
    parser.add_argument("--resume", action="store_true", help="ask original runners to verify existing results before skipping")
    parser.add_argument("--dry-run", action="store_true", help="write manifest.dry-run.json; no runner/API calls")
    args = parser.parse_args(argv)
    if args.workers < 1 or args.hpo_threads < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--workers, --hpo-threads, and --limit must be positive")
    if args.max_tokens is not None and args.max_tokens < 1:
        parser.error("--max-tokens must be positive")
    if args.request_timeout <= 0 or args.max_retries < 0 or min(args.retry_base_seconds, args.retry_max_seconds) < 0:
        parser.error("invalid timeout or retry settings")
    parsed_url = urlsplit(args.base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        parser.error("--base-url must be an http(s) URL")
    if parsed_url.username or parsed_url.password or parsed_url.query or parsed_url.fragment:
        parser.error("--base-url must not contain credentials, query parameters, or fragments")
    args.repo_root = args.repo_root.expanduser().absolute()
    args.python = (args.python or args.repo_root / ".venv/bin/python").expanduser().absolute()
    args.paramnet_python = args.paramnet_python.expanduser().absolute()
    args.output_dir = (args.output_dir or STUDY_ROOT / "runs" / args.stage).expanduser().absolute()
    args.run_namespace = args.stage if args.output_dir == STUDY_ROOT / "runs" / args.stage else (
        f"{args.stage}-{slug(args.output_dir.name)}-"
        + hashlib.sha256(str(args.output_dir).encode()).hexdigest()[:8]
    )
    args.logs_dir = args.logs_dir.expanduser().absolute()
    args.dumps_dir = args.dumps_dir.expanduser().absolute()
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = build_manifest(args)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with (args.output_dir / ".harness.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("another harness process holds this output directory") from error
            manifest_path = args.output_dir / ("manifest.dry-run.json" if args.dry_run else "manifest.json")
            if not args.dry_run and not args.resume and any(Path(job["status_path"]).exists() or
                    any(path.exists() for path in expected_files(job)) for job in manifest["jobs"]):
                raise ValueError("selected jobs already have artifacts; rerun with --resume for runner validation")
            invocation_path = args.output_dir / "manifest.invocation.json"
            if args.dry_run:
                atomic_json(manifest_path, manifest)
            else:
                # A one-job repair must not replace the complete study plan.
                # Audit the canonical manifest; use the invocation manifest
                # and progress for the actual selection run this time.
                canonical_args = argparse.Namespace(**{
                    **vars(args), "part": "both", "job_ids": None, "limit": None,
                })
                canonical = build_manifest(canonical_args)
                if canonical["source_tree_sha256"] != manifest["source_tree_sha256"]:
                    raise ValueError("repository source changed while preparing the plan; rerun after edits finish")
                canonical["manifest_role"] = "complete_stage"
                canonical["latest_invocation_selection"] = manifest["selection"]
                canonical["invocation_manifest_path"] = str(invocation_path)
                manifest["manifest_role"] = "invocation"
                manifest["canonical_manifest_path"] = str(manifest_path)
                stamp = time.time_ns()
                for existing in (manifest_path, invocation_path):
                    if existing.exists():
                        history = args.output_dir / "manifest_history" / f"{stamp}.{existing.name}"
                        atomic_json(history, load_json(existing))
                atomic_json(manifest_path, canonical)
                atomic_json(invocation_path, manifest)
            print(json.dumps({"manifest": str(manifest_path),
                              "invocation_manifest": None if args.dry_run else str(invocation_path), "stage": args.stage,
                              "counts": manifest["counts"], "workers": args.workers,
                              "dry_run": args.dry_run}, ensure_ascii=False), flush=True)
            if args.dry_run:
                return 0
            return execute_study(args, manifest)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"study error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
