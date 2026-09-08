#!/usr/bin/env python3
"""Bounded smoke orchestration of the frozen, authoritative ExpGym runners.

Default invocation only writes a plan and runs each runner's data-free dry-run.
--execute runs the fixed 15-job matrix and a fail-closed no-model-call resume
check. Fake replay exercises real data/scorers, but intentionally uses auto/text
because the repository FakeLLM does not implement native tool messages.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit


HERE = Path(__file__).resolve()
WORKSPACE = HERE.parents[2]
SCENARIOS = ("tuning", "restricted_search", "evidence_audit")
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STRATEGIES = ("naive", "cached", "poolact")
TUNING_TASK = "hpobench:nasbench101:A"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=WORKSPACE / "LLM_ExpGym")
    parser.add_argument("--python", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--backend", choices=("fake", "openai"), default="fake")
    parser.add_argument("--model", default="kimi-k3")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=1206)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-real", action="store_true",
                        help="Explicit coordinator permission, after an endpoint is supplied.")
    args = parser.parse_args(argv)
    args.repo_root = args.repo_root.expanduser().resolve()
    # Do not resolve the Python symlink: the venv path selects site-packages.
    args.python = (args.python or args.repo_root / ".venv/bin/python").expanduser().absolute()
    args.output_dir = args.output_dir.expanduser().resolve()
    if args.api_key_file is not None:
        args.api_key_file = args.api_key_file.expanduser().resolve()
    if not 1 <= args.workers <= 4:
        parser.error("--workers must be between 1 and 4")
    if args.base_url:
        url = urlsplit(args.base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username is not None or url.password is not None or url.query or url.fragment:
            parser.error("--base-url must be an HTTP(S) endpoint without credentials/query/fragment")
    if args.backend == "openai" and args.execute and (not args.allow_real or not args.base_url):
        parser.error("real execution requires both --allow-real and an explicit --base-url supplied by the coordinator")
    if args.backend == "fake" and args.base_url:
        parser.error("fake validation must not carry a real endpoint")
    return args


def settings(args):
    return {
        "backend": args.backend, "model": args.model, "base_url": args.base_url,
        "seed": args.seed, "temperature": 1.0, "max_steps": 6, "max_evals": 5,
        "max_tokens": 32768, "reasoning_effort": "max",
        "chat_template_kwargs": {"thinking": True, "thinking_effort": "max"},
        "tool_protocol": "auto" if args.backend == "fake" else "native",
        "max_protocol_retries": 1, "tuning_final_policy": "legacy",
        "http_max_retries": 2, "request_timeout_seconds": 1800,
        "http_retry_base_seconds": 3, "http_retry_max_seconds": 30,
        "poolact_agents": 2, "poolact_repeats": 1, "poolact_strategies": list(STRATEGIES),
        "poolact_max_context_tokens": 131072, "expgym_max_context_tokens": None,
        "context_limitation": "ExpGym performs no runner-level context trim; PoolAct input estimate cap is 131072. Server context must be recorded separately (K3 candidate 524288).",
        "tuning_task": TUNING_TASK, "search_data_source": "phantom_seed1",
        "search_index": 0, "audit_index": 0, "cc_split": "cc-large",
        "expgym_audit_order": "configs/audit_hypothesis_orders.json order 0",
        "poolact_audit_order": "repository default (no override CLI)",
        "workers": args.workers, "retry_failed_jobs": False,
        "deviations_from_paper": ["Kimi-K3 self-serving", "1 item per scenario", "6 steps / 5 evaluations", "temperature 1 and extended reasoning max", "2 PoolAct agents", "no statistical reproduction claim"],
        "fake_limitation": "FakeLLM auto resolves to text; no native provider/dump validation" if args.backend == "fake" else None,
    }


def build_jobs(args):
    config = settings(args)
    jobs = []
    for system in ("expgym", "poolact"):
        for scenario in SCENARIOS:
            for regime in REGIMES if system == "expgym" else REGIMES[1:]:
                job_id = "__".join((system, scenario, regime))
                output = args.output_dir / "results" / job_id
                command = [str(args.python), "-u", str(args.repo_root / "scripts" / ("run_paper_sweep.py" if system == "expgym" else "run_poolact.py")),
                           "--backend", args.backend, "--output-dir", str(output),
                           "--seed", str(args.seed), "--max-steps", "6", "--max-evals", "5",
                           "--max-tokens", "32768", "--reasoning-effort", "max",
                           "--chat-template-kwargs", json.dumps(config["chat_template_kwargs"], sort_keys=True),
                           "--tool-protocol", config["tool_protocol"], "--max-protocol-retries", "1",
                           "--tuning-final-policy", "legacy", "--request-timeout", "1800",
                           "--max-retries", "2", "--retry-base-seconds", "3", "--retry-max-seconds", "30",
                           "--api-key-file", str(args.api_key_file or Path("/dev/null"))]
                if args.base_url:
                    command += ["--base-url", args.base_url]
                if system == "expgym":
                    command += ["--models", "smoke-model", "--model-alias", "smoke-model=" + args.model,
                                "--scenarios", scenario, "--cost-regimes", regime,
                                "--tuning-tasks", TUNING_TASK, "--search-indices", "0", "--audit-indices", "0",
                                "--search-data-source", "phantom_seed1", "--cc-split", "cc-large",
                                "--audit-orders", str(args.repo_root / "configs/audit_hypothesis_orders.json"),
                                "--tuning-reps", "1", "--search-reps", "1", "--audit-reps", "1",
                                "--temperature-tuning", "1", "--temperature-eval", "1",
                                "--trace-format", "v2", "--prompt-cache-scope", "disabled"]
                else:
                    command += ["--model", args.model, "--scenario", scenario, "--cost-regime", regime,
                                "--tuning-task", TUNING_TASK, "--question-index", "0",
                                "--data-source", "phantom_seed1", "--cc-split", "cc-large",
                                "--strategies", ",".join(STRATEGIES), "--agents", "2", "--repeats", "1",
                                "--temperature", "1", "--max-context-tokens", "131072"]
                jobs.append({"id": job_id, "system": system, "scenario": scenario, "regime": regime,
                             "expected_traces": 1 if system == "expgym" else 6,
                             "output_dir": str(output), "command": command})
    return jobs


def repository_module(repo_root, name):
    repo_root = str(Path(repo_root).resolve())
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    module = importlib.import_module(name)
    if not Path(module.__file__).resolve().is_relative_to(Path(repo_root)):
        raise RuntimeError("Refusing an already imported module from a different repository")
    return module


def source_fingerprint(repo_root):
    module = repository_module(repo_root, "expgym.trace_v2")
    module._source_files.cache_clear()
    module.source_tree_sha256.cache_clear()
    return module.source_tree_sha256(Path(repo_root))


def runtime_identity(args):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    command = [str(args.python), "-c", "import json,sys,platform; print(json.dumps(dict(executable=sys.executable,version=sys.version,prefix=sys.prefix,base_prefix=sys.base_prefix,machine=platform.machine())))"]
    completed = subprocess.run(command, cwd=args.repo_root, env=environment, capture_output=True, text=True, check=True)
    record = json.loads(completed.stdout)
    record["executable_sha256"] = sha256(args.python)
    config_path = args.python.parent.parent / "pyvenv.cfg"
    record["pyvenv_config_sha256"] = sha256(config_path) if config_path.is_file() else None
    record["evaluation_dependencies"] = "Captured per selected task in every result's evaluation_identity; no full environment attestation."
    return record


def snapshot_artifacts(job):
    root = Path(job["output_dir"])
    if job["system"] == "expgym":
        paths = sorted(root.glob("*/traces-v2/*.json"))
    else:
        paths = sorted(root.glob("*/result.json")) + sorted(root.glob("*/agents/agent_*.json"))
    return {str(path.relative_to(root)): {"sha256": sha256(path), "bytes": path.stat().st_size,
                                        "mtime_ns": path.stat().st_mtime_ns} for path in paths}


def snapshot_dumps(path):
    return {str(item.relative_to(path)): {"sha256": sha256(item), "bytes": item.stat().st_size,
                                         "mtime_ns": item.stat().st_mtime_ns}
            for item in sorted(Path(path).rglob("*.json")) if item.is_file()}


def validate_job(job, expected_source, backend):
    root = Path(job["output_dir"])
    errors, scores, identities, terminals = [], [], [], []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def score(value, label):
        require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), label + ": nonfinite/missing score")
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            scores.append(float(value))

    try:
        if job["system"] == "expgym":
            paths = sorted(root.glob("*/traces-v2/*.json"))
            require(len(paths) == 1, "expected exactly one ExpGym v2 trace")
            for path in paths:
                trace = json.loads(path.read_text())
                module = importlib.import_module("expgym.trace_v2")
                module.validate_trace_v2(trace)
                outcome, run = trace["outcome"], trace["run"]
                require(outcome["validation"].get("passed") is True, "ExpGym score recomputation did not pass")
                require(trace["provenance"]["repository"]["source_tree_sha256"] == expected_source, "ExpGym source fingerprint differs")
                require(isinstance(run.get("evaluation_identity"), dict), "ExpGym data/dependency identity missing")
                identities.append(run.get("evaluation_identity"))
                require(outcome.get("tool_protocol") == ("text" if backend == "fake" else "native"), "ExpGym resolved protocol differs")
                saved_score = outcome["score"]
                primary = (saved_score.get("metrics", {}).get(saved_score.get("primary_metric"))
                           if "metrics" in saved_score else saved_score.get("value"))
                score(primary, str(path))
                terminals.append({key: outcome.get(key) for key in ("termination_reason", "answer_source", "answer_score_source")})
            count = len(paths)
        else:
            result_paths = sorted(root.glob("*/result.json"))
            require({path.parent.name for path in result_paths} == set(STRATEGIES), "PoolAct strategy set differs")
            require(len(result_paths) == 3, "expected three PoolAct strategy results")
            expected_agent_paths = {str(Path(strategy) / "agents" / ("agent_%d.json" % agent)) for strategy in STRATEGIES for agent in range(2)}
            require({str(path.relative_to(root)) for path in root.glob("*/agents/agent_*.json")} == expected_agent_paths, "PoolAct agent artifact set differs")
            count = 0
            aggregates, configs = {}, []
            for path in result_paths:
                result = json.loads(path.read_text())
                aggregates[path.parent.name] = result.get("aggregate")
                configs.append(result.get("config"))
                require(result.get("implementation_sha256", {}).get("source_tree") == expected_source, "PoolAct source fingerprint differs")
                identity = result.get("config", {}).get("evaluation_identity")
                require(isinstance(identity, dict), "PoolAct data/dependency identity missing")
                identities.append(identity)
                state = result.get("shared_state")
                require(state is None or (type(state.get("pending_claims", 0)) is int and state.get("pending_claims", 0) == 0
                                         and type(state.get("graph", {}).get("pending_claims", 0)) is int
                                         and state.get("graph", {}).get("pending_claims", 0) == 0), "PoolAct pending claims remain")
                if path.parent.name == "poolact":
                    require(isinstance(state, dict) and state.get("graph", {}).get("pending_claims") == 0, "Coordinated PoolAct pending-claim receipt missing")
                aggregate_score = result.get("aggregate", {}).get("answer_perf")
                require(isinstance(aggregate_score, (int, float)) and not isinstance(aggregate_score, bool) and math.isfinite(aggregate_score), "PoolAct aggregate not finite")
                agents = result.get("agent_results", [])
                require(len(agents) == 2 and {agent.get("agent_id") for agent in agents} == {0, 1}, "PoolAct agent IDs/count differs")
                for agent in agents:
                    require(agent.get("score_check", {}).get("ok") is True, "PoolAct independent score check failed")
                    require(agent.get("tool_protocol") == ("text" if backend == "fake" else "native"), "PoolAct resolved protocol differs")
                    saved = json.loads((path.parent / "agents" / ("agent_%d.json" % agent["agent_id"])).read_text())
                    require(saved == agent, "PoolAct separate agent artifact differs")
                    score(agent.get("answer_perf"), str(path))
                    terminals.append({key: agent.get(key) for key in ("termination_reason", "answer_source", "answer_score_source")})
                    count += 1
            summary = json.loads((root / "summary.json").read_text())
            require(set(summary.get("strategies", {})) == set(STRATEGIES), "PoolAct summary incomplete")
            require(summary.get("strategies") == aggregates, "PoolAct summary aggregate contents differ")
            require(summary.get("implementation_sha256", {}).get("source_tree") == expected_source, "PoolAct summary source differs")
            require(all(summary.get("config") == config for config in configs), "PoolAct summary configuration differs")
        require(count == job["expected_traces"], "trace count does not match fixed matrix")
    except Exception as exc:
        errors.append("artifact validation raised " + type(exc).__name__)
        count = len(scores)
    return {"passed": not errors, "errors": errors, "trace_count": count,
            "semantic_zero_count": sum(value == 0 for value in scores), "agent_scores": scores,
            "evaluation_identities": identities, "terminal_diagnostics": terminals,
            "interpretation": "Validated zero scores are semantic outcomes, not infrastructure failures."}


def validate_api_dumps(job, dump_root):
    """Account for every HTTP attempt by the public client identity, no old auditor."""
    root = Path(job["output_dir"])
    expected = {}
    if job["system"] == "expgym":
        trace = json.loads(next(root.glob("*/traces-v2/*.json")).read_text())
        expected[trace["run"]["api_dump"]["client_id"]] = trace["outcome"]["http_request_attempts"]
    else:
        for path in root.glob("*/agents/agent_*.json"):
            agent = json.loads(path.read_text())
            identifier = agent["api_dump"]["client_id"]
            if identifier in expected:
                raise ValueError("Duplicate agent client identity")
            expected[identifier] = agent["http_request_attempts"]
    errors, actual, states = [], {}, {}
    for path in sorted(Path(dump_root).glob("*.json")):
        record = json.loads(path.read_text())
        identifier = record.get("client_id")
        actual[identifier] = actual.get(identifier, 0) + 1
        state = record.get("state")
        states[state] = states.get(state, 0) + 1
        if record.get("schema_version") != "expgym.api_attempt.v1" or state not in {"success", "error", "malformed_response"}:
            errors.append("Incomplete/unsupported HTTP attempt: " + path.name)
        if path.stem != record.get("request_id") or not record.get("finished_at_utc"):
            errors.append("HTTP attempt receipt identity/completion differs: " + path.name)
    if len(expected) != job["expected_traces"] or any(type(count) is not int or count < 1 for count in expected.values()) or actual != expected:
        errors.append("HTTP attempts do not exactly cover each agent's recorded client identity/count")
    return {"passed": not errors, "errors": errors, "per_client_attempts": actual, "states": states}


def run_bounded(jobs, worker, max_workers=4):
    if not 1 <= max_workers <= 4:
        raise ValueError("max_workers must be between 1 and 4")
    next_index, pending, results = 0, {}, []
    stopped = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        while pending or (next_index < len(jobs) and not stopped):
            while not stopped and next_index < len(jobs) and len(pending) < max_workers:
                job = jobs[next_index]
                pending[pool.submit(worker, job)] = job
                next_index += 1
            done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                job = pending.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"job_id": job["id"], "passed": False, "error_type": type(exc).__name__}
                results.append(result)
                stopped = stopped or result.get("passed") is not True
    return {"results": results, "failed": [result for result in results if result.get("passed") is not True],
            "unstarted": [job["id"] for job in jobs[next_index:]]}


def resume_command(job):
    command = job["command"]
    return command[:2] + [str(HERE), "--_resume-guard"] + command[2:] + ["--resume"]


def resume_guard(argv):
    runner = Path(argv[0]).resolve()
    repo = runner.parent.parent
    if runner.name not in {"run_paper_sweep.py", "run_poolact.py"} or runner.parent.name != "scripts" or "--resume" not in argv:
        raise RuntimeError("Resume guard only accepts an authoritative runner with --resume")
    demo = repository_module(repo, "demo_experiment")

    def deny_model(*args, **kwargs):
        raise RuntimeError("RESUME_GUARD_MODEL_CALL_FORBIDDEN")

    demo.build_llm = deny_model
    client = repository_module(repo, "expgym.llm_clients")
    client.OpenAICompatibleLLM.generate = deny_model
    sys.argv = [str(runner)] + argv[1:]
    runpy.run_path(str(runner), run_name="__main__")


def run_child(command, args, job, log_name, secrets):
    environment = os.environ.copy()
    environment.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       EXPGYM_API_DUMP_DIR=str(args.output_dir / "dumps" / job["id"]),
                       EXPGYM_RUN_ID="scenario-smoke:" + args.output_dir.name,
                       OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    # Remove ambient endpoint/cache overrides; all intended settings are explicit.
    for name in ("PYTHONPATH", "EXPGYM_BASE_URL", "OPENAI_BASE_URL", "EXPGYM_PROMPT_CACHE_KEY"):
        environment.pop(name, None)
    if args.backend == "openai" and secrets:
        environment["OPENAI_API_KEY"] = secrets[0]
    started = time.monotonic()
    completed = subprocess.run(command, cwd=args.repo_root, env=environment,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    output = completed.stdout.decode("utf-8", errors="replace")
    for secret in secrets:
        if secret:
            output = output.replace(secret, "[REDACTED]")
    target = args.output_dir / "logs" / job["id"] / log_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(output, encoding="utf-8")
    return {"exit_code": completed.returncode, "elapsed_seconds": time.monotonic() - started,
            "log": str(target), "log_sha256": sha256(target)}, output


def main(argv=None):
    args = parse_args(argv)
    jobs = build_jobs(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / ".harness.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        source = source_fingerprint(args.repo_root)
        identity = {"schema_version": 1, "repo_root": str(args.repo_root), "python": str(args.python),
                    "runtime": runtime_identity(args),
                    "source_tree_sha256": source, "harness_sha256": sha256(HERE),
                    "settings": settings(args), "jobs": jobs,
                    "counts": {"child_jobs": 15, "expgym_traces": 9, "poolact_strategy_results": 18,
                               "poolact_agent_traces": 36, "all_agent_traces": 45},
                    "credential_source": str(args.api_key_file) if args.api_key_file else "OPENAI_API_KEY environment (real only)",
                    "resume_validation": "same runner/config with --resume; build_llm and HTTP-client generation forbidden; offline task evaluation remains enabled"}
        manifest_path = args.output_dir / "manifest.json"
        if manifest_path.exists():
            if json.loads(manifest_path.read_text())["identity"] != identity:
                raise RuntimeError("Immutable plan differs; choose a fresh output directory")
        else:
            atomic_json(manifest_path, {"created_utc": utc_now(), "identity": identity})
            atomic_json(args.output_dir / "commands.json", {job["id"]: {"run": job["command"], "dry_run": job["command"] + ["--dry-run"], "resume_guard": resume_command(job)} for job in jobs})
        if (args.output_dir / "execution_started.json").exists() or (args.output_dir / "execution.json").exists():
            raise RuntimeError("This fixed attempt already has an execution receipt; no automatic retries or result replacement")
        secrets = []
        if args.execute and args.backend == "openai":
            key = args.api_key_file.read_text().strip() if args.api_key_file else os.environ.get("OPENAI_API_KEY", "").strip()
            if not key:
                raise RuntimeError("Real execution requires a nonempty API key file or OPENAI_API_KEY")
            secrets = [key]
        if args.execute:
            if any(snapshot_artifacts(job) for job in jobs):
                raise RuntimeError("Pre-existing artifacts without an execution receipt; refusing to overwrite")
            atomic_json(args.output_dir / "execution_started.json", {"created_utc": utc_now(),
                        "harness_pid": os.getpid(), "source_tree_sha256": source,
                        "harness_sha256": identity["harness_sha256"],
                        "note": "One fixed attempt only. Failure/interruption requires explicit review, never automatic answer resampling."})

        def worker(job):
            if source_fingerprint(args.repo_root) != source or sha256(HERE) != identity["harness_sha256"]:
                return {"job_id": job["id"], "passed": False, "error": "source changed before dispatch"}
            command = job["command"] if args.execute else job["command"] + ["--dry-run"]
            receipt, output = run_child(command, args, job, "run.log" if args.execute else "dry_run.log", secrets)
            result = {"job_id": job["id"], "run": receipt, "passed": receipt["exit_code"] == 0}
            if args.execute and result["passed"]:
                validation = validate_job(job, source, args.backend)
                result["validation"] = validation
                result["passed"] = validation["passed"]
                before = snapshot_artifacts(job)
                dump_root = args.output_dir / "dumps" / job["id"]
                dumps_before = snapshot_dumps(dump_root)
                if args.backend != "fake" and not dumps_before:
                    result["passed"] = False
                    result["error"] = "real run has no HTTP attempt dumps"
                if args.backend != "fake" and result["passed"]:
                    try:
                        result["dump_validation"] = validate_api_dumps(job, dump_root)
                    except Exception as exc:
                        result["dump_validation"] = {"passed": False, "error_type": type(exc).__name__}
                    result["passed"] = result["dump_validation"]["passed"]
                if result["passed"]:
                    resume, resume_output = run_child(resume_command(job), args, job, "resume.log", secrets)
                    skips = resume_output.count("skip verified") if job["system"] == "expgym" else resume_output.count("[resume] item=0 strategy=")
                    unchanged = before == snapshot_artifacts(job)
                    no_api = dumps_before == snapshot_dumps(dump_root)
                    expected_skips = 1 if job["system"] == "expgym" else 3
                    result["resume"] = {**resume, "protective_model_call_guard": True, "verified_skips": skips,
                                        "expected_skips": expected_skips, "trace_bytes_and_mtimes_unchanged": unchanged,
                                        "api_dump_bytes_and_mtimes_unchanged": no_api}
                    result["passed"] = resume["exit_code"] == 0 and skips == expected_skips and unchanged and no_api and "rerun" not in resume_output.lower()
                result["artifacts"] = before
                result["api_dumps"] = dumps_before
            if source_fingerprint(args.repo_root) != source:
                result["passed"] = False
                result["error"] = "source changed during execution"
            atomic_json(args.output_dir / "logs" / job["id"] / ("status.json" if args.execute else "dry_run_status.json"), result)
            return result

        started = time.monotonic()
        report = run_bounded(jobs, worker, args.workers)
        report.update(created_utc=utc_now(), elapsed_seconds=time.monotonic() - started,
                      classification=("Real smoke validation" if args.backend == "openai" else "Static/fake validation") if args.execute else "Static/fake validation",
                      executed=args.execute, passed=not report["failed"] and not report["unstarted"],
                      source_tree_sha256=source, harness_sha256=identity["harness_sha256"],
                      validated_trace_count=sum(item.get("validation", {}).get("trace_count", 0) for item in report["results"]),
                      semantic_zero_count=sum(item.get("validation", {}).get("semantic_zero_count", 0) for item in report["results"]))
        atomic_json(args.output_dir / ("execution.json" if args.execute else "dry_run.json"), report)
        print(json.dumps({key: report[key] for key in ("passed", "executed", "classification", "elapsed_seconds", "validated_trace_count", "semantic_zero_count", "unstarted")}, indent=2))
        return 0 if report["passed"] else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--_resume-guard":
        resume_guard(sys.argv[2:])
    else:
        raise SystemExit(main())
