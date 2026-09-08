#!/usr/bin/env python3
"""Frozen A21 runtime pilot; defaults to local preflight + runner --dry-run.

Real calls require a separately authorized --execute --allow-real invocation.
Fake execution uses real local data, not the native provider protocol. A pilot
is a Custom study for timing, never a confirmation/performance experiment.
This file also supplies a Python-3.7-compatible isolated identity/resume shim.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import random
import runpy
import subprocess
import sys
import time
from urllib.parse import urlsplit

HERE = Path(__file__).resolve()
WORKSPACE = HERE.parents[2]
DEFAULT_ACCEPTANCE = HERE.parents[1] / "validation/static_acceptance_v1.json"
DEFAULT_SOURCE = "f77028edf932db6e7626acd454748e7646f47e2cb6892bb150548383e93c3eb1"
TASKS = tuple("hpobench:paramnet:%s:steps" % name for name in ("adult", "higgs", "letter")) + tuple(
    "hpobench:nasbench101:" + name for name in ("A", "B", "C")) + tuple(
    "hpobench:nasbench201:" + name for name in ("cifar10-valid", "cifar100", "imagenet16-120"))
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STAGES = ("A1_hpo", "A2_search_audit")
PROBE_PREFIX = "PILOT_IDENTITY_JSON="


def helpers():
    if str(HERE.parent) not in sys.path:
        sys.path.insert(0, str(HERE.parent))
    module = importlib.import_module("scenario_smoke")
    if Path(module.__file__).resolve() != HERE.with_name("scenario_smoke.py"):
        raise RuntimeError("Wrong scenario_smoke helper origin")
    return module


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=WORKSPACE / "LLM_ExpGym")
    parser.add_argument("--python", type=Path)
    parser.add_argument("--legacy-runtime-dir", type=Path, default=WORKSPACE / "kimi_k3_eval/data_runtime")
    parser.add_argument("--static-acceptance", type=Path, default=DEFAULT_ACCEPTANCE,
                        help="An independently accepted receipt; every file and its source digest are verified.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New independent pilot_runs directory.")
    parser.add_argument("--backend", choices=("fake", "openai"), default="fake")
    parser.add_argument("--model", default="kimi-k3")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=1206)
    parser.add_argument("--schedule-seed", type=int, default=20260908)
    parser.add_argument("--server-context-tokens", type=int, default=524288,
                        help="Operator-declared server setting, not endpoint-verified by this harness.")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-real", action="store_true", help="Only after separate coordinator authorization.")
    args = parser.parse_args(argv)
    for key in ("repo_root", "legacy_runtime_dir", "static_acceptance", "output_dir", "api_key_file"):
        if getattr(args, key) is not None:
            setattr(args, key, getattr(args, key).expanduser().resolve())
    # Resolving this symlink would discard the native virtualenv selection.
    args.python = (args.python or args.repo_root / ".venv/bin/python").expanduser().absolute()
    if not 1 <= args.workers <= 4:
        parser.error("--workers must be between 1 and 4")
    if args.server_context_tokens <= 0:
        parser.error("--server-context-tokens must be positive")
    if args.base_url:
        url = urlsplit(args.base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username is not None or url.password is not None or url.query or url.fragment:
            parser.error("--base-url must be HTTP(S), without credentials/query/fragment")
    if args.backend == "fake" and (args.base_url or args.allow_real):
        parser.error("fake validation cannot carry an endpoint or --allow-real")
    if args.execute and args.backend == "openai" and (not args.allow_real or not args.base_url):
        parser.error("real execution requires separate authorization, --allow-real and explicit --base-url")
    try:
        args.output_dir.relative_to(args.repo_root)
    except ValueError:
        pass
    else:
        parser.error("pilot output must be outside the frozen repository")
    return args


def settings(args):
    return {
        "backend": args.backend, "model": args.model, "base_url": args.base_url,
        "seed": args.seed, "schedule_seed": args.schedule_seed, "workers": args.workers,
        "temperature": 1.0, "top_p": 1.0, "max_steps": 30, "max_evals": 30,
        "max_tokens": 32768, "reasoning_effort": "max",
        "chat_template_kwargs": {"thinking": True, "thinking_effort": "max"},
        "tool_protocol": "auto" if args.backend == "fake" else "native",
        "max_protocol_retries": 1, "tuning_final_policy": "legacy",
        "request_timeout_seconds": 1800, "http_max_retries": 2,
        "http_retry_base_seconds": 3, "http_retry_max_seconds": 30,
        "prompt_cache_scope": "disabled", "audit_order_index": 0,
        "network_route": "HTTP(S)/ALL proxy environment removed; NO_PROXY=*; explicit endpoint only",
        "search_data_source": "phantom_seed1", "cc_split": "cc-large",
        "expgym_context_cap": None, "operator_declared_server_context_tokens": args.server_context_tokens,
        "server_setting_verified_by_harness": False,
        "schedule_rule": "Random(schedule_seed) shuffles within A1 then A2; drain A1 before A2",
        "failed_job_retry": False, "semantic_zero_policy": "retain; never stop or retry on score",
        "interpretation": "Custom study: runtime pilot only; selected development items, one generation/cell; no performance/inference claim or formal-result reuse",
        "fake_limitation": "Real local scorers, auto/text FakeLLM; no native/API/timing representativeness" if args.backend == "fake" else None,
    }


def build_jobs(args):
    jobs = []
    cells = [(STAGES[0], "tuning", task, None, "cost_moderate") for task in TASKS]
    cells += [(STAGES[1], scenario, None, index, regime)
              for scenario, indices in (("restricted_search", (0, 18)), ("evidence_audit", (0, 2)))
              for index in indices for regime in REGIMES]
    profile = settings(args)
    for stage, scenario, task, index, regime in cells:
        runtime = "legacy_paramnet" if task and task.startswith("hpobench:paramnet:") else "native"
        python = args.legacy_runtime_dir / ".venv-hpo/bin/python" if runtime == "legacy_paramnet" else args.python
        selector = task.replace(":", "_") if task else str(index)
        job_id = "__".join((stage, scenario, selector, regime))
        output = args.output_dir / "results" / job_id
        command = [str(python), "-u", str(args.repo_root / "scripts/run_paper_sweep.py"),
                   "--backend", args.backend, "--models", "k3", "--model-alias", "k3=" + args.model,
                   "--output-dir", str(output), "--seed", str(args.seed),
                   "--max-steps", "30", "--max-evals", "30", "--max-tokens", "32768",
                   "--reasoning-effort", "max", "--chat-template-kwargs", json.dumps(profile["chat_template_kwargs"], sort_keys=True),
                   "--tool-protocol", profile["tool_protocol"], "--max-protocol-retries", "1",
                   "--tuning-final-policy", "legacy", "--request-timeout", "1800", "--max-retries", "2",
                   "--retry-base-seconds", "3", "--retry-max-seconds", "30",
                   "--api-key-file", str(args.api_key_file or Path("/dev/null")),
                   "--scenarios", scenario, "--cost-regimes", regime,
                   "--tuning-tasks", task or TASKS[0], "--search-indices", str(index or 0), "--audit-indices", str(index or 0),
                   "--search-data-source", "phantom_seed1", "--cc-split", "cc-large",
                   "--audit-orders", str(args.repo_root / "configs/audit_hypothesis_orders.json"),
                   "--tuning-reps", "1", "--search-reps", "1", "--audit-reps", "1",
                   "--temperature-tuning", "1", "--temperature-eval", "1",
                   "--trace-format", "v2", "--prompt-cache-scope", "disabled"]
        if args.base_url:
            command += ["--base-url", args.base_url]
        jobs.append({"id": job_id, "stage": stage, "system": "expgym", "scenario": scenario,
                     "tuning_task": task, "question_index": index, "regime": regime, "runtime": runtime,
                     "expected_traces": 1, "output_dir": str(output),
                     "dump_dir": str(args.output_dir / "dumps" / job_id), "command": command})
    rng, ordered = random.Random(args.schedule_seed), []
    for stage in STAGES:
        selected = [job for job in jobs if job["stage"] == stage]
        rng.shuffle(selected)
        ordered.extend(selected)
    for index, job in enumerate(ordered):
        job["dispatch_index"] = index
    return ordered


def source_paths(repo):
    paths = [path for name in ("expgym", "scripts", "schemas", "tests") for path in (repo / name).rglob("*")
             if path.is_file() and "__pycache__" not in path.parts and path.suffix.lower() in {".py", ".sh", ".json", ".yaml", ".yml", ".md"}]
    if (repo / "demo_experiment.py").is_file():
        paths.append(repo / "demo_experiment.py")
    return sorted(paths)


def verify_acceptance(repo, receipt_path):
    receipt = json.loads(receipt_path.read_text())
    files = receipt.get("files")
    if not isinstance(files, dict) or not files:
        raise RuntimeError("Static acceptance must enumerate actual accepted files")
    required = {path.relative_to(repo).as_posix() for path in source_paths(repo)}
    required.update(("README.MD", "configs/hpobench_tasks.yaml", "configs/audit_hypothesis_orders.json", "requirements.txt", "requirements-data.txt"))
    if not required.issubset(files):
        raise RuntimeError("Static acceptance omits runtime/config/source files")
    for relative, expected in files.items():
        path = repo / relative
        try:
            path.resolve().relative_to(repo.resolve())
        except ValueError:
            raise RuntimeError("Static acceptance contains a path outside the repository")
        if not path.is_file() or helpers().sha256(path) != expected:
            raise RuntimeError("Static acceptance file mismatch: " + relative)
    digest = hashlib.sha256()
    for path in source_paths(repo):
        digest.update(path.relative_to(repo).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
    source = digest.hexdigest()
    if source != receipt.get("source_tree_sha256"):
        raise RuntimeError("Static acceptance source digest mismatch")
    if receipt_path.resolve() == DEFAULT_ACCEPTANCE.resolve() and source != DEFAULT_SOURCE:
        raise RuntimeError("Default v1 receipt no longer matches its accepted source")
    return {"path": str(receipt_path), "sha256": helpers().sha256(receipt_path),
            "source_tree_sha256": source, "verified_files": files}


def environment_overrides(args, job):
    values = {"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
              "EXPGYM_API_DUMP_DIR": job["dump_dir"], "EXPGYM_RUN_ID": "pilot-a21:" + args.output_dir.name, "EXPGYM_HPO_THREADS": "1",
              "NO_PROXY": "*", "no_proxy": "*"}
    if job["runtime"] == "legacy_paramnet":
        values.update(HPOBENCH_ROOT=str(args.repo_root / "data/hpo_tuning/HPOBench"),
                      XDG_DATA_HOME=str(args.repo_root / "data/hpo_tuning/hpobench_data"),
                      XDG_CACHE_HOME=str(args.repo_root / "data/hpo_tuning/hpobench_cache"),
                      XDG_CONFIG_HOME=str(args.legacy_runtime_dir / "hpobench_config"))
    return values


def child_environment(args, job, secret=None):
    env = os.environ.copy()
    for name in ("PYTHONPATH", "EXPGYM_BASE_URL", "OPENAI_BASE_URL", "EXPGYM_PROMPT_CACHE_KEY", "OPENAI_API_KEY", "SUB2API_API_KEY", "SUB2API_BASE_URL", "HPOBENCH_ROOT", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME"):
        env.pop(name, None)
    for name in list(env):
        if name.lower() in {"http_proxy", "https_proxy", "all_proxy", "no_proxy"}:
            env.pop(name, None)
    env.update(environment_overrides(args, job))
    if secret:
        env["OPENAI_API_KEY"] = secret
    return env


def repository_module(repo, name):
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    module = importlib.import_module(name)
    try:
        Path(module.__file__).resolve().relative_to(repo.resolve())
    except ValueError:
        raise RuntimeError("Imported module is outside selected repository")
    return module


def guarded_runner(argv, identity_only=False):
    """Both modes forbid model construction/generation; score recomputation is allowed."""
    runner = Path(argv[0]).resolve()
    if runner.name != "run_paper_sweep.py" or runner.parent.name != "scripts" or (not identity_only and "--resume" not in argv):
        raise RuntimeError("Expected the authoritative ExpGym runner and guarded --resume")
    repo = runner.parent.parent

    def forbidden(*args, **kwargs):
        raise RuntimeError("PILOT_GUARD_MODEL_CALL_FORBIDDEN")

    demo = repository_module(repo, "demo_experiment")
    demo.build_llm = forbidden
    clients = repository_module(repo, "expgym.llm_clients")
    clients.OpenAICompatibleLLM.generate = forbidden
    demo.FakeLLM.generate = forbidden
    sys.argv = [str(runner)] + argv[1:]
    if not identity_only:
        runpy.run_path(str(runner), run_name="__main__")
        return
    scope = runpy.run_path(str(runner), run_name="pilot_identity_probe")
    parsed = scope["parse_args"]()
    jobs = scope["_build_jobs"](parsed)
    if len(jobs) != 1:
        raise RuntimeError("Every A21 invocation must resolve to exactly one trace")
    identity = scope["_job_evaluation_identity"](parsed, jobs[0])
    result = {"job": asdict(jobs[0]), "evaluation_identity": identity,
              "runtime": {"executable": sys.executable, "version": sys.version, "prefix": sys.prefix,
                          "base_prefix": sys.base_prefix, "machine": platform.machine()}}
    print(PROBE_PREFIX + json.dumps(result, sort_keys=True, allow_nan=False))


def guard_command(job, identity_only=False):
    command = job["command"]
    return command[:2] + [str(HERE), "--_identity-probe" if identity_only else "--_resume-guard"] + command[2:] + ([] if identity_only else ["--resume"])


def probe(args, job):
    completed = subprocess.run(guard_command(job, True), cwd=args.repo_root, env=child_environment(args, job),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
    if completed.returncode:
        raise RuntimeError("Local guarded identity probe failed for " + job["id"] + ": " + completed.stderr[-2000:])
    lines = [line[len(PROBE_PREFIX):] for line in completed.stdout.splitlines() if line.startswith(PROBE_PREFIX)]
    if len(lines) != 1:
        raise RuntimeError("Identity probe did not produce exactly one receipt")
    result = json.loads(lines[0])
    expected_version = "3.7." if job["runtime"] == "legacy_paramnet" else "3.11."
    if not result["runtime"]["version"].startswith(expected_version):
        raise RuntimeError("Unexpected Python version for " + job["runtime"])
    python = Path(job["command"][0])
    result["runtime"]["executable_sha256"] = helpers().sha256(python)
    config = python.parent.parent / "pyvenv.cfg"
    result["runtime"]["pyvenv_config_sha256"] = helpers().sha256(config) if config.is_file() else None
    return result


def snapshot(root):
    """All result/dump JSON, including file set and mtimes; excludes orchestration logs."""
    return helpers().snapshot_dumps(Path(root))


def run_child(args, job, command, log_name, secret):
    path = args.output_dir / "logs" / job["id"] / log_name
    if path.exists():
        raise FileExistsError("Refusing a repeated child invocation with an existing log: " + str(path))
    started, utc = time.monotonic(), helpers().utc_now()
    completed = subprocess.run(command, cwd=args.repo_root, env=child_environment(args, job, secret),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    output = completed.stdout.decode("utf-8", errors="replace")
    if secret:
        output = output.replace(secret, "[REDACTED]")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(output)
    return {"exit_code": completed.returncode, "started_utc": utc, "finished_utc": helpers().utc_now(),
            "elapsed_seconds": time.monotonic() - started, "log": str(path), "log_sha256": helpers().sha256(path)}, output


def redact_wire(value, secret, secret_field):
    """Mirror this profile's client redaction without constructing a client."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if secret_field(str(key)) else redact_wire(item, secret, secret_field) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_wire(item, secret, secret_field) for item in value]
    return value.replace(secret, "[REDACTED]") if secret and isinstance(value, str) else value


def dump_profile(args, job, secret=None):
    coverage = helpers().validate_api_dumps(job, Path(job["dump_dir"]))
    errors = list(coverage["errors"])
    attempts, generations, by_request = [], {}, {}
    clients = repository_module(args.repo_root, "expgym.llm_clients")
    trace_module = repository_module(args.repo_root, "expgym.trace_v2")
    if set(Path(job["dump_dir"]).rglob("*.json")) != set(Path(job["dump_dir"]).glob("*.json")):
        errors.append("Unexpected nested raw JSON outside the flat client namespace")
    for path in sorted(Path(job["dump_dir"]).glob("*.json")):
        record = json.loads(path.read_text())
        payload = record.get("request_payload", {})
        expected = {"model": args.model, "temperature": 1.0, "top_p": 1.0, "max_tokens": 32768, "seed": args.seed,
                    "reasoning_effort": "max", "chat_template_kwargs": settings(args)["chat_template_kwargs"]}
        if any(payload.get(key) != value for key, value in expected.items()):
            errors.append("HTTP request generation profile differs: " + path.name)
        tools = payload.get("tools")
        if not isinstance(tools, list) or not tools or payload.get("tool_choice") not in ("auto", "none"):
            errors.append("Native tool schema/choice missing: " + path.name)
        if payload.get("parallel_tool_calls") is not False:
            errors.append("Parallel tools must be disabled: " + path.name)
        if "prompt_cache_key" in payload:
            errors.append("Unexpected enabled prompt-cache key: " + path.name)
        endpoint = clients._normalize_chat_completions_url(args.base_url)
        if record.get("endpoint") != endpoint or record.get("run_id") != "pilot-a21:" + args.output_dir.name:
            errors.append("HTTP endpoint/run namespace differs: " + path.name)
        if record.get("context", {}).get("job") != job["preflight"]["job"]:
            errors.append("HTTP selected-job context differs: " + path.name)
        generation = record.get("generation_id")
        if not isinstance(generation, str) or not generation or record.get("max_attempts") != 3 or type(record.get("attempt")) is not int:
            errors.append("HTTP generation/attempt metadata invalid: " + path.name)
        else:
            generations.setdefault(generation, []).append(record)
        by_request[record.get("request_id")] = record
        response = record.get("response_json") or {}
        choices = response.get("choices") if isinstance(response, dict) else None
        attempts.append({"request_id": record.get("request_id"), "client_id": record.get("client_id"),
                         "path": str(path), "sha256": helpers().sha256(path), "state": record.get("state"),
                         "wall_time_seconds": record.get("wall_time_seconds"),
                         "usage": response.get("usage") if isinstance(response, dict) else None,
                         "finish_reasons": [choice.get("finish_reason") for choice in choices if isinstance(choice, dict)] if isinstance(choices, list) else []})
    for generation, records in generations.items():
        ordered = sorted(records, key=lambda record: record["attempt"])
        if [record["attempt"] for record in ordered] != list(range(1, len(ordered) + 1)) or len(ordered) > 3:
            errors.append("Noncontiguous/duplicate HTTP retry attempts: " + generation)
        if any(record.get("will_retry") is not True for record in ordered[:-1]) or ordered[-1].get("will_retry") is not False:
            errors.append("Incomplete retry chain: " + generation)
        if any(record.get("request_payload") != ordered[0].get("request_payload") for record in ordered[1:]):
            errors.append("Retry mutated request payload: " + generation)
    trace = json.loads(next(Path(job["output_dir"]).glob("*/traces-v2/*.json")).read_text())
    if len(generations) != len(trace.get("llm_calls", [])):
        errors.append("Generation set does not cover trace LLM calls")
    linked_requests, linked_generations = [], []
    for call in trace.get("llm_calls", []):
        ledger = call.get("attempt_usage")
        if not isinstance(ledger, list) or not ledger:
            errors.append("Trace call lacks its HTTP attempt ledger: " + str(call.get("id")))
            continue
        linked_generations.append(ledger[0].get("generation_id"))
        expected_messages = redact_wire(trace_module.materialize_llm_input(trace, call["id"]), secret, clients.OpenAICompatibleLLM._is_secret_field)
        for entry in ledger:
            request_id = entry.get("request_id")
            linked_requests.append(request_id)
            record = by_request.get(request_id)
            if record is None:
                errors.append("Trace request missing from raw dumps: " + str(request_id))
                continue
            if any(entry.get(key) != record.get(key) for key in ("generation_id", "attempt", "state", "http_status")):
                errors.append("Trace/raw attempt metadata differs: " + str(request_id))
            if entry.get("generation_id") != ledger[0].get("generation_id"):
                errors.append("One trace call uses multiple generation IDs")
            payload = record.get("request_payload", {})
            if payload.get("messages") != expected_messages:
                errors.append("Trace/raw wire messages differ: " + str(request_id))
            if payload.get("tool_choice") != ("none" if call.get("forced") else "auto"):
                errors.append("Trace forced flag and native tool choice differ: " + str(request_id))
            response = record.get("response_json")
            usage = response.get("usage") if isinstance(response, dict) else None
            if "usage_error" not in entry and entry.get("usage") != usage:
                errors.append("Trace/raw provider usage differs: " + str(request_id))
        delivered = by_request.get(ledger[-1].get("request_id"))
        if delivered is not None:
            response = delivered.get("response_json")
            choices = response.get("choices") if isinstance(response, dict) else None
            message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
            if not isinstance(message, dict):
                errors.append("Delivered trace call lacks a raw assistant message")
            else:
                message = dict(message)
                message.setdefault("role", "assistant")
                if message != redact_wire(call.get("output_message"), secret, clients.OpenAICompatibleLLM._is_secret_field) or choices[0].get("finish_reason") != call.get("finish_reason"):
                    errors.append("Trace/raw delivered assistant message or finish reason differs")
            if delivered.get("state") != "success":
                errors.append("Delivered trace call does not end in transport success")
    if len(set(linked_requests)) != len(linked_requests) or set(linked_requests) != set(by_request):
        errors.append("Trace and raw request IDs are not a bijection")
    if len(set(linked_generations)) != len(linked_generations) or set(linked_generations) != set(generations):
        errors.append("Trace calls and raw generations are not a bijection")
    return {"passed": not errors, "errors": errors, "coverage": coverage, "attempts": attempts,
            "usage_limitation": "Raw provider usage per attempt, including retry attempts; absent usage is unknown, not zero. No billing or unreported reasoning inference."}


def trace_timing(job):
    trace = json.loads(next(Path(job["output_dir"]).glob("*/traces-v2/*.json")).read_text())
    return {"trace_timing": trace.get("timing"), "budget": trace["task"].get("budget"),
            "outcome": {key: trace["outcome"].get(key) for key in ("termination_reason", "answer_source", "answer_score_source", "protocol_failures", "protocol_retries", "agent_steps", "http_request_attempts")},
            "llm_call_count": len(trace.get("llm_calls", [])), "tool_call_count": len(trace.get("tool_calls", [])),
            "forced_call_count": sum(call.get("forced") is True for call in trace.get("llm_calls", [])),
            "tool_costs": [{key: call.get(key) for key in ("id", "name", "simulated_cost_seconds", "visible_to_model")} for call in trace.get("tool_calls", [])],
            "llm_usage": [call.get("usage") for call in trace.get("llm_calls", [])]}


def main(argv=None):
    args, h = parse_args(argv), helpers()
    acceptance = verify_acceptance(args.repo_root, args.static_acceptance)
    repository_module(args.repo_root, "expgym.trace_v2")
    jobs = build_jobs(args)
    # Deliberately data-aware, read-only local preflight; each underlying runner
    # --dry-run itself remains data-free. Nothing here constructs an LLM.
    for job in jobs:
        job["environment_overrides"] = environment_overrides(args, job)
        job["preflight"] = probe(args, job)
    code_hashes = {str(path): h.sha256(path) for path in (HERE, HERE.with_name("scenario_smoke.py"), HERE.parent / "tests/test_pilot_timing.py", args.legacy_runtime_dir / "run_hpo.sh")}
    identity = {"schema_version": 1, "static_acceptance": acceptance, "settings": settings(args),
                "repo_root": str(args.repo_root), "harness_files": code_hashes, "jobs": jobs,
                "counts": {"jobs": 21, "agent_traces": 21, "A1": 9, "A2": 12, "legacy_paramnet": 3, "native": 18},
                "credential_source": str(args.api_key_file) if args.api_key_file else "OPENAI_API_KEY (real execution only)",
                "resume_audit": "Guard forbids model construction and both client generators; offline independent scoring allowed. Snapshot every result/dump JSON path, bytes, SHA256 and mtime before/after. Orchestrator logs/status excluded."}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / ".harness.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        phase = "execution" if args.execute else "dry_run"
        manifest = args.output_dir / "manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text())["identity"] != identity:
                raise RuntimeError("Immutable manifest differs; use a NEW output directory")
        elif any(path.name != ".harness.lock" for path in args.output_dir.iterdir()):
            raise RuntimeError("Unrecognized nonempty output directory; refusing to overwrite")
        else:
            h.atomic_json(manifest, {"created_utc": h.utc_now(), "identity": identity})
            h.atomic_json(args.output_dir / "commands.json", {job["id"]: {"run": job["command"], "dry_run": job["command"] + ["--dry-run"], "resume_guard": guard_command(job)} for job in jobs})
        if any((args.output_dir / name).exists() for name in (phase + "_started.json", phase + ".json", "execution_started.json", "execution.json")):
            raise RuntimeError("This attempt/phase already started; no overwrite, retry or answer resampling")
        if any(snapshot(job["output_dir"]) or snapshot(job["dump_dir"]) for job in jobs):
            raise RuntimeError("Existing result/raw JSON; refusing to overwrite")
        secret = None
        if args.execute and args.backend == "openai":
            secret = args.api_key_file.read_text().strip() if args.api_key_file else os.environ.get("OPENAI_API_KEY", "").strip()
            if not secret:
                raise RuntimeError("Real execution needs a nonempty key file or OPENAI_API_KEY; secrets are never serialized")
        h.atomic_json(args.output_dir / (phase + "_started.json"), {"created_utc": h.utc_now(), "pid": os.getpid(), "identity_sha256": h.sha256(manifest)})

        def unchanged():
            return (verify_acceptance(args.repo_root, args.static_acceptance) == acceptance
                    and all(h.sha256(Path(path)) == checksum for path, checksum in code_hashes.items()))

        def worker(job):
            if not unchanged() or probe(args, job) != job["preflight"]:
                raise RuntimeError("Source/runtime/data changed before dispatch")
            command = job["command"] + ([] if args.execute else ["--dry-run"])
            run, output = run_child(args, job, command, phase + ".log", secret)
            result = {"job_id": job["id"], "stage": job["stage"], "run": run, "passed": run["exit_code"] == 0}
            if args.execute and result["passed"]:
                result["validation"] = h.validate_job(job, acceptance["source_tree_sha256"], args.backend)
                result["passed"] = (result["validation"]["passed"] and "score_check=ok" in output
                                    and result["validation"]["evaluation_identities"] == [job["preflight"]["evaluation_identity"]])
                result["timing"] = trace_timing(job)
                before = {"results": snapshot(job["output_dir"]), "dumps": snapshot(job["dump_dir"])}
                result["before_resume"] = before
                if args.backend == "openai":
                    result["dump_validation"] = dump_profile(args, job, secret)
                    result["passed"] = result["passed"] and result["dump_validation"]["passed"]
                elif before["dumps"]:
                    result["passed"] = False
                    result["error"] = "Fake execution unexpectedly produced HTTP dumps"
                if result["passed"]:
                    resumed, text = run_child(args, job, guard_command(job), "resume.log", secret)
                    after = {"results": snapshot(job["output_dir"]), "dumps": snapshot(job["dump_dir"])}
                    result["resume"] = {**resumed, "model_calls_forbidden": True, "verified_skips": text.count("skip verified"), "before_equals_after": before == after, "after": after}
                    result["passed"] = resumed["exit_code"] == 0 and text.count("skip verified") == 1 and before == after and "rerun" not in text.lower()
            if not unchanged() or probe(args, job) != job["preflight"]:
                result["passed"] = False
                result["error"] = "Source/runtime/data changed during dispatch"
            h.atomic_json(args.output_dir / "logs" / job["id"] / (phase + "_status.json"), result)
            return result

        started, stages, results, unstarted = time.monotonic(), [], [], []
        for stage in STAGES:
            selected = [job for job in jobs if job["stage"] == stage]
            if any(item.get("passed") is not True for item in results):
                unstarted.extend(job["id"] for job in selected)
                continue
            stage_start = time.monotonic()
            report = h.run_bounded(selected, worker, args.workers)
            results.extend(report["results"])
            unstarted.extend(report["unstarted"])
            stages.append({"stage": stage, "elapsed_seconds_including_preflight_resume": time.monotonic() - stage_start})
        report = {"created_utc": h.utc_now(), "executed": args.execute,
                  "classification": "Custom study" if args.execute and args.backend == "openai" else "Static/fake validation",
                  "purpose": "A21 runtime pilot only; no confirmation inference; fake timings are not model runtime estimates",
                  "passed": len(results) == 21 and not unstarted and all(item.get("passed") is True for item in results),
                  "elapsed_seconds_including_preflight_resume": time.monotonic() - started,
                  "stages": stages, "results": results, "unstarted": unstarted,
                  "validated_trace_count": sum(item.get("validation", {}).get("trace_count", 0) for item in results),
                  "semantic_zero_count": sum(item.get("validation", {}).get("semantic_zero_count", 0) for item in results),
                  "raw_timing_rows": [{"job_id": item["job_id"], "stage": item.get("stage"),
                                       "passed": item.get("passed"), "run_wall_seconds": item.get("run", {}).get("elapsed_seconds"),
                                       "timing": item.get("timing")} for item in results],
                  "timing_note": "Per-job run.elapsed_seconds excludes orchestrator identity probes and guarded resume. Includes child import/loading/scoring. Stage elapsed includes probes/resume; HTTP attempt time and raw usage separate. Simulated tool cost is not wall time."}
        h.atomic_json(args.output_dir / (phase + ".json"), report)
        print(json.dumps({key: report[key] for key in ("passed", "executed", "classification", "elapsed_seconds_including_preflight_resume", "validated_trace_count", "semantic_zero_count", "unstarted")}, indent=2))
        return 0 if report["passed"] else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"--_resume-guard", "--_identity-probe"}:
        guarded_runner(sys.argv[2:], identity_only=sys.argv[1] == "--_identity-probe")
    else:
        raise SystemExit(main())
