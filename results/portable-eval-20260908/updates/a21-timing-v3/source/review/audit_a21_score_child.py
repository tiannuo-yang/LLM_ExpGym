#!/usr/bin/env python3
"""Python-3.7-compatible, stdin-driven read-only A21 scorer/context checker.

Never calls runner main/resume; stdout is the sole output. Run with each job's
frozen interpreter and environment. No API key is read or model instantiated.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import socket
import sys


def main():
    specification = json.load(sys.stdin)
    repo = Path(specification["repo_root"]).resolve()
    sys.path.insert(0, str(repo))
    sys.dont_write_bytecode = True
    blocked = []

    def deny(*args, **kwargs):
        blocked.append(True)
        raise RuntimeError("A21_INDEPENDENT_NO_MODEL_OR_NETWORK")

    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = deny
    import demo_experiment as demo
    from expgym import llm_clients as clients
    from expgym import tool_protocol as protocol
    from expgym.trace_v2 import materialize_llm_input, result_for_score_check
    from scripts import run_paper_sweep as sweep

    demo.build_llm = sweep.build_llm = deny
    demo.FakeLLM.generate = clients.OpenAICompatibleLLM.generate = deny
    selected = specification["job"]
    sys.argv = selected["command"][2:]
    args = sweep.parse_args()
    jobs = sweep._build_jobs(args)
    if len(jobs) != 1:
        raise ValueError("A21 child must resolve exactly one selected trace")
    job = jobs[0]
    identity = sweep._job_evaluation_identity(args, job)
    if asdict(job) != selected["preflight"]["job"] or identity != selected["preflight"]["evaluation_identity"]:
        raise ValueError("Independent selected job/data identity differs")
    trace_path = Path(specification["trace_path"])
    trace = json.loads(trace_path.read_text())
    resume_valid = sweep._resume_trace_is_valid(trace_path, args, job)
    namespace = sweep._namespace_for_job(args, job, None)
    sweep.bind_evaluation_identity(identity)
    scenario = sweep._SCENARIOS[job.scenario]
    tools = sweep._resolve_tools(scenario, namespace)
    evaluator = sweep._resolve_answer_evaluator(scenario, namespace)
    score = sweep._score_check(result_for_score_check(trace), tools, evaluator)

    base_cost = sweep.resolve_base_cost(job.scenario, namespace)
    time_budget, modes = sweep.resolve_cost_regime(namespace, base_cost)
    if len(modes) != 1:
        raise ValueError("Unexpected multiple A21 modes")
    include_overhead = modes[0] == "time_focus"
    context = demo._resolve_context(scenario, include_overhead, namespace,
                                    argparse.Namespace(supports_native_tools=True)).strip()
    system = protocol.native_system_prompt(demo._resolve_system_prompt(scenario, include_overhead, namespace))
    expected_schemas = protocol.native_tool_schemas(tools)
    errors, requests = [], []
    for call in trace["llm_calls"]:
        expected_input = materialize_llm_input(trace, call["id"])
        if expected_input[:2] != [{"role": "system", "content": system}, {"role": "user", "content": context}]:
            errors.append("Trusted complete task/system differs: " + call["id"])
        if sum(message.get("role") == "system" for message in expected_input) != 1:
            errors.append("System count differs: " + call["id"])
        for attempt in call["attempt_usage"]:
            request_id = attempt["request_id"]
            raw = json.loads((Path(selected["dump_dir"]) / (request_id + ".json")).read_text())
            payload = raw["request_payload"]
            if payload["messages"] != expected_input or payload.get("tools") != expected_schemas:
                errors.append("Raw context/schema differs: " + request_id)
            if raw.get("context") != namespace._api_dump_context:
                errors.append("Raw selected job/trace path differs: " + request_id)
            requests.append(request_id)
    runtime = {"executable": sys.executable, "version": sys.version, "prefix": sys.prefix,
               "base_prefix": sys.base_prefix, "machine": platform.machine()}
    python = Path(selected["command"][0])
    runtime["executable_sha256"] = hashlib.sha256(python.read_bytes()).hexdigest()
    config = python.parent.parent / "pyvenv.cfg"
    runtime["pyvenv_config_sha256"] = hashlib.sha256(config.read_bytes()).hexdigest() if config.is_file() else None
    result = {"job_id": selected["id"], "passed": resume_valid and score.get("ok") is True and not errors and not blocked,
              "resume_identity_score_valid": resume_valid, "score_check": score,
              "evaluation_identity": identity, "runtime": runtime,
              "runtime_matches_preflight": runtime == selected["preflight"]["runtime"],
              "trusted_prompt_schema_passed": not errors, "request_ids": requests,
              "prompt_errors": errors, "model_or_network_attempts": len(blocked),
              "cost_regime": {"base_cost": base_cost, "time_budget": time_budget, "mode": modes[0]},
              "forced_call_count_observed": sum(call.get("forced") is True for call in trace["llm_calls"]),
              "forced_call_required": False}
    result["passed"] = result["passed"] and result["runtime_matches_preflight"]
    print("A21_INDEPENDENT_JSON=" + json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
