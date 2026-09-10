#!/usr/bin/env python3
"""Freeze existing runner matrices, then execute one flat subprocess queue."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from expgym.scheduling import QueueJob, digest, run_queue, write_json
from expgym.trace_v2 import source_tree_sha256

PATH_ARGUMENTS = {"output_dir", "terminal_evidence_dir", "api_key_file", "audit_orders"}
SWEEP_SELECTORS = {"models", "model_alias", "scenarios", "cost_regimes", "tuning_tasks",
                   "search_indices", "search_data_source", "audit_indices", "cc_split",
                   "audit_orders", "tuning_reps", "search_reps", "audit_reps", "seed",
                   "shuffle", "limit"}


def namespace(value):
    return argparse.Namespace(**{key: Path(item) if key in PATH_ARGUMENTS and item is not None
                                 else item for key, item in value.items()})


def load_plan(path, checksum):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError("plan SHA256 mismatch")
    plan = json.loads(raw)
    if plan.get("schema") != "expgym.study-queue-plan.v1":
        raise ValueError("unknown queue plan schema")
    if plan["source_tree_sha256"] != source_tree_sha256(REPO_ROOT):
        raise ValueError("source changed since plan freeze; create a new study")
    return plan


def check_endpoint(value):
    url = urlsplit(value)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("endpoint must be an HTTP URL without embedded credentials/query")
    return value.rstrip("/")


def make_plan(matrix, *, study_id, output_root, default_python, endpoints=()):
    """Use the production runner selectors, never a separately retyped matrix."""
    from scripts import run_paper_sweep as sweep, run_poolact as pool
    if not study_id or not matrix.get("stages"):
        raise ValueError("study_id and nonempty stages required")
    root = output_root.absolute()
    plan = {"schema": "expgym.study-queue-plan.v1", "study_id": study_id,
            "source_tree_sha256": source_tree_sha256(REPO_ROOT),
            "output_root": str(root), "jobs": []}
    seen, labels = set(), set()
    for stage in matrix["stages"]:
        if set(stage) - {"label", "runner", "args", "python", "endpoints"}:
            raise ValueError("unknown stage fields")
        label = stage["label"]
        if label in labels:
            raise ValueError("duplicate stage label")
        labels.add(label)
        runner = stage["runner"]
        module = {"expgym": sweep, "poolact": pool}[runner]
        args = module.parse_args(stage["args"])
        if args.api_key is not None:
            raise ValueError("--api-key is forbidden in persisted plans; use env or key-file")
        if args.dry_run or args.resume or args.terminal_evidence_dir is not None:
            raise ValueError("queue owns dry-run/resume/evidence paths; omit those runner flags")
        if args.base_url is None:
            args.base_url = module._backend_base_url(args.backend)
        if args.base_url:
            check_endpoint(args.base_url)
        if runner == "expgym":
            if not args.models.strip():
                args.models = sweep._backend_model(args.backend)
            expanded = [(asdict(job), None) for job in sweep._build_jobs(args)]
        else:
            if not args.model:
                args.model = pool._backend_model(args.backend)
            if args.repeats < 1 or args.agents < 1:
                raise ValueError("positive repeats and agents required")
            if args.scenario == "tuning" and args.questions is not None:
                raise ValueError("tuning does not support questions")
            questions = args.questions if args.questions is not None else [args.question_index or 0]
            expanded = [(dict(question_index=q, strategy=s, repeat_index=r), r)
                        for r in range(args.repeats) for q in questions for s in args.strategies]
        resolved = {key: str(value.absolute()) if isinstance(value, Path) else value
                    for key, value in vars(args).items() if key != "output_dir"}
        python = str(Path(stage.get("python", default_python)).absolute())
        # Do not resolve the executable symlink: doing so would lose a venv identity.
        if not Path(python).is_file() or not os.access(python, os.X_OK):
            raise ValueError("verified Python executable required: %s" % python)
        stage_endpoints = [check_endpoint(url) for url in stage.get("endpoints", endpoints)]
        if len(stage_endpoints) != len(set(stage_endpoints)):
            raise ValueError("duplicate endpoints")
        for selection, repeat in expanded:
            job_args = dict(resolved)
            if runner == "poolact":
                job_args.update(questions=None, question_index=selection["question_index"],
                                strategies=[selection["strategy"]])
            # User cache namespace remains an input to identity; actual namespace
            # additionally binds study + full invocation, even when seed repeats.
            identity_args = {key: value for key, value in job_args.items()
                             if (key not in SWEEP_SELECTORS if runner == "expgym"
                                 else key != "repeats")}
            identity = {"study_id": study_id, "runner": runner, "args": identity_args,
                        "selection": selection, "python": python,
                        "source_tree_sha256": plan["source_tree_sha256"],
                        "endpoints": stage_endpoints}
            job_id = "job_" + digest(identity)
            if job_id in seen:
                raise ValueError("duplicate logical invocation across stages")
            seen.add(job_id)
            job_args.update(output_dir=str(root / "invocations" / job_id / "result"),
                            prompt_cache_key="queue-" + digest(identity)[:40],
                            terminal_evidence_dir=None, resume=False)
            if runner == "expgym":
                # Fake has no API config/cache field; do not claim it sent one.
                job_args["prompt_cache_scope"] = "disabled" if args.backend == "fake" else "job"
            plan["jobs"].append({"job_id": job_id, "stage": label, "runner": runner,
                                 "identity": identity, "args": job_args,
                                 "selection": selection, "python": python,
                                 "endpoints": stage_endpoints})
    if not plan["jobs"]:
        raise ValueError("matrix selected no jobs")
    return plan


def verify_result(job, args):
    from scripts import run_paper_sweep as sweep, run_poolact as pool
    if job["runner"] == "expgym":
        selected = sweep.Job(**job["selection"])
        path = sweep._trace_path(args.output_dir, selected, args.trace_format)
        if not sweep._resume_trace_is_valid(path, args, selected):
            raise ValueError("ExpGym exact identity/score resume validation failed")
    else:
        args = pool._repeat_namespace(args, job["selection"]["repeat_index"])
        args._evaluation_identity = pool.evaluation_identity(args, REPO_ROOT)
        pool.bind_evaluation_identity(args._evaluation_identity)
        scenario = pool._SCENARIOS[args.scenario]
        cost = pool.resolve_base_cost(args.scenario, args)
        budget, _ = pool.resolve_cost_regime(args, cost)
        strategy = job["selection"]["strategy"]
        result = pool._load_resumable_result(
            args.output_dir / strategy / "result.json", item_output_dir=args.output_dir,
            strategy=strategy, config=pool._resolved_config(args, budget),
            implementation=pool._implementation_manifest(), agents=args.agents,
            answer_evaluator=pool._resolve_answer_evaluator(scenario, args),
            score_tools=pool._resolve_tools(scenario, args))
        if result is None:
            raise ValueError("PoolAct exact identity/score resume validation failed")
        summary = json.loads((args.output_dir / "summary.json").read_text())
        if (summary.get("config") != result["config"] or summary.get("strategies") != {
                strategy: result["aggregate"]} or summary.get("implementation_sha256") != result["implementation_sha256"]):
            raise ValueError("PoolAct summary mismatch")


def worker(plan, job_id, verify_only):
    from scripts import run_paper_sweep as sweep, run_poolact as pool
    selected = [row for row in plan["jobs"] if row["job_id"] == job_id]
    if len(selected) != 1:
        raise ValueError("unknown or duplicate job id")
    job = selected[0]
    args = namespace(job["args"])
    if job["endpoints"]:
        endpoint = os.environ.get("EXPGYM_QUEUE_ENDPOINT")
        if endpoint not in job["endpoints"]:
            raise ValueError("worker requires an admitted endpoint")
        args.base_url = endpoint
    if verify_only:
        verify_result(job, args)
        return 0
    if args.output_dir.exists():
        raise ValueError("fresh worker refuses existing output")
    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir.parent / "worker.json", {
        "job_id": job_id, "pid": os.getpid(), "python_executable": sys.executable,
        "python_version": platform.python_version(), "selection": job["selection"],
        "identity_sha256": digest(job["identity"]), "base_url": args.base_url,
        "run_id": os.environ.get("EXPGYM_RUN_ID"),
        "dump_dir": os.environ.get("EXPGYM_API_DUMP_DIR"),
        "prompt_cache_namespace": args.prompt_cache_key})
    if job["runner"] == "expgym":
        code = sweep.main(args, selected_job=sweep.Job(**job["selection"]))
    else:
        code = pool.main(args, selected_repeat=job["selection"]["repeat_index"])
    if code == 0:
        verify_result(job, args)
    return code


def queue_jobs(plan, path, checksum):
    jobs = []
    for row in plan["jobs"]:
        root = Path(row["args"]["output_dir"]).parent
        command = [row["python"], "-B", str(Path(__file__).resolve()), "worker",
                   "--plan", str(path.absolute()), "--sha256", checksum,
                   "--job-id", row["job_id"]]
        jobs.append(QueueJob(row["job_id"], row["identity"], command,
                             command + ["--verify-only"], root, REPO_ROOT,
                             {"EXPGYM_RUN_ID": row["job_id"],
                              "EXPGYM_API_DUMP_DIR": str(root / "api_dump"),
                              "PYTHONDONTWRITEBYTECODE": "1"}, row["endpoints"]))
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    create = subs.add_parser("plan", help="expand runner selectors; no data/API/GPU calls")
    create.add_argument("--matrix", type=Path, required=True)
    create.add_argument("--study-id", required=True)
    create.add_argument("--output-root", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--python", default=sys.executable)
    create.add_argument("--endpoint-file", type=Path)
    for name in ("run", "worker"):
        sub = subs.add_parser(name)
        sub.add_argument("--plan", type=Path, required=True)
        sub.add_argument("--sha256", required=True)
        if name == "run":
            sub.add_argument("--workers", type=int)
            sub.add_argument("--serving-config", type=Path,
                             default=REPO_ROOT / "configs/serving/slurm_tp16.json")
            sub.add_argument("--resume", action="store_true")
            sub.add_argument("--stop-file", type=Path)
            sub.add_argument("--max-wall-seconds", type=float)
        else:
            sub.add_argument("--job-id", required=True)
            sub.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.action == "plan":
        endpoints = json.loads(args.endpoint_file.read_text())["endpoints"] if args.endpoint_file else []
        plan = make_plan(json.loads(args.matrix.read_text()), study_id=args.study_id,
                         output_root=args.output_root, default_python=args.python, endpoints=endpoints)
        write_json(args.output, plan)
        print(json.dumps({"jobs": len(plan["jobs"]), "plan": str(args.output),
                          "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))
        return 0
    plan = load_plan(args.plan, args.sha256)
    if args.action == "worker":
        return worker(plan, args.job_id, args.verify_only)
    workers = args.workers
    if workers is None:
        workers = json.loads(args.serving_config.read_text())["dispatch"]["max_workers"]
    result = run_queue(queue_jobs(plan, args.plan, args.sha256),
                       state_dir=Path(plan["output_root"]) / "queue", workers=workers,
                       resume=args.resume, stop_file=args.stop_file,
                       max_wall_seconds=args.max_wall_seconds)
    print(json.dumps({key: value for key, value in result.items() if key != "reports"}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
