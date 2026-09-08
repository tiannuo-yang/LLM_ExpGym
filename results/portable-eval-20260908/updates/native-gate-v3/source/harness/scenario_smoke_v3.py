#!/usr/bin/env python3
"""One-shot, Moderate-only native integration smoke (6 jobs / 21 traces).

This external coordinator does not modify or invoke the legacy harness main.
Default execution is a no-model-call dry-run. Real execution requires a separately
authorized immutable plan. Artifact integrity, prompt correctness and observed
native-path coverage are three separate gates; semantic scores never stop work.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit


HERE = Path(__file__).resolve()
PORTABLE = HERE.parents[1]
WORKSPACE = HERE.parents[2]
LEGACY_PATH = HERE.with_name("scenario_smoke.py")
PROFILE_PATH = PORTABLE / "patches/profile_parameterization_v2/candidate/harness/request_profile.py"
PINNED_HELPERS = {
    LEGACY_PATH: "9c85d0f8545fcc364ce27d2cea01009db6e9eb4d525e58fb44b3b2f660c9eeb1",
    PROFILE_PATH: "64f19f0de7c36a0c8b461ae28056e481aa73f2980ba3d91cd8d34a40a4f6eb70",
}
SCENARIOS = ("tuning", "restricted_search", "evidence_audit")
STRATEGIES = ("naive", "cached", "poolact")
COUNTS = {"child_jobs": 6, "expgym_traces": 3, "poolact_strategy_results": 9,
          "poolact_agent_traces": 18, "all_agent_traces": 21, "guarded_resume_skips": 12,
          "native_coverage_cells": 12}
FINAL_NOTE = "Respond immediately with Answer: <your final choice> and no other text."


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_external(name, path):
    if sha256(path) != PINNED_HELPERS[path]:
        raise RuntimeError("Frozen external helper differs: " + path.name)
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != path:
            raise RuntimeError("Wrong external helper origin")
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def helpers():
    return load_external("scenario_smoke_v3_legacy_helpers", LEGACY_PATH)


def profiles():
    return load_external("scenario_smoke_v3_request_profiles", PROFILE_PATH)


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError("Nonfinite JSON value")
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=nonfinite)


def same_json(left, right):
    return profiles().digest(left) == profiles().digest(right)


def generation_profile(args, override=None):
    """Shared profile validator, with this smoke's explicit K3-only scope.

    A future model expansion must receive new authorization and acceptance; the
    reusable profile library alone does not authorize changing this experiment.
    """
    selected = copy.deepcopy(profiles().DEFAULT_PROFILE)
    selected["randomness_contract"] = "seed_labels_only"
    baseline = profiles().validate_profile(selected)
    if override is None and hasattr(args, "_request_profile"):
        override = profiles().profile(args)
    selected = profiles().validate_profile(override if override is not None else baseline)
    for field in set(baseline) - {"expected_metadata"}:
        if not same_json(selected[field], baseline[field]):
            raise ValueError("This K3-only smoke does not authorize changing profile field: " + field)
    return selected


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=WORKSPACE / "LLM_ExpGym")
    parser.add_argument("--python", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--static-acceptance", type=Path, required=True)
    parser.add_argument("--serving-binding", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--backend", choices=("fake", "openai"), default="fake")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=1206)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-real", action="store_true")
    profiles().add_arguments(parser)
    args = parser.parse_args(argv)
    for field in ("repo_root", "output_dir", "static_acceptance", "serving_binding", "authorization", "api_key_file", "request_profile"):
        if getattr(args, field) is not None:
            setattr(args, field, getattr(args, field).expanduser().resolve())
    args.python = (args.python or args.repo_root / ".venv/bin/python").expanduser().absolute()
    try:
        supplied, raw_sha = profiles().load_profile(args.request_profile) if args.request_profile else (None, None)
        selected = generation_profile(args, supplied)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.model is not None and args.model != selected["model"]:
        parser.error("--model conflicts with the authorized K3-only request profile")
    if args.server_context_tokens is not None and args.server_context_tokens != selected["server_context_tokens"]:
        parser.error("--server-context-tokens conflicts with the request profile")
    args.model = selected["model"]
    args.server_context_tokens = selected["server_context_tokens"]
    args._request_profile = {"profile": selected, "sha256": profiles().digest(selected),
                             "source": {"path": str(args.request_profile) if args.request_profile else None, "file_sha256": raw_sha}}
    if args.model_alias is not None:
        parser.error("This smoke uses fixed output IDs; --model-alias is not supported")
    if not 1 <= args.workers <= 4 or args.seed != 1206:
        parser.error("This scope requires workers 1..4 and base seed 1206")
    if args.output_dir.is_relative_to(args.repo_root):
        parser.error("Smoke outputs must be outside the frozen repository")
    if args.base_url:
        url = urlsplit(args.base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username is not None or url.password is not None or url.query or url.fragment:
            parser.error("Endpoint must be HTTP(S) without credentials/query/fragment")
    if args.backend == "fake" and (args.base_url or args.allow_real or args.authorization or args.serving_binding):
        parser.error("Fake validation cannot carry serving authorization or an endpoint")
    if args.backend == "openai" and args.execute and not all((args.allow_real, args.base_url, args.api_key_file, args.serving_binding, args.authorization)):
        parser.error("Real execution requires --allow-real, endpoint, key file, serving binding and authorization")
    return args


def settings(args):
    result = helpers().settings(args)
    selected = generation_profile(args)
    result.update(max_steps=3, max_evals=2, regimes=["cost_moderate"],
                  request_profile=profiles().identity(args), top_p=selected["top_p"], top_k=selected["top_k"],
                  randomness_contract="seed_labels_only", counts=dict(COUNTS),
                  deviations_from_paper=["K3 self-serving integration smoke", "Moderate only; one item per scenario",
                                         "3 steps / 2 evaluations", "temperature 1 and extended reasoning max",
                                         "2 PoolAct agents", "no statistical reproduction claim"],
                  promotion_requires=["artifact_integrity", "trusted_prompt_gate", "observed_native_path_coverage"],
                  native_coverage_rule={
                      "version": "per-client-normal-graph__per-cell-continuation-forced-v1",
                      "cell_key": ["system", "scenario", "strategy"],
                      "expgym_strategy_label": "sequential",
                      "required_cells": 12,
                      "per_client_paths": ["normal_auto", "graph_context for coordinated PoolAct"],
                      "per_client_integrity": "every request must pass prompt/schema/wire checks",
                      "per_cell_union_paths": ["native_continuation", "forced_none"],
                      "cross_cell_borrowing": False,
                      "missing_path_policy": "coverage incomplete only; no additional API calls",
                      "history_policy": "complete ordered assistant sequence and immutable previous-request prefix; no trimming accepted"},
                  natural_early_answer_policy="retain; mark missing coverage; never automatically obtain extra samples",
                  logical_generation_upper_bound_per_agent=4,
                  http_attempt_upper_bound_per_agent=12,
                  concurrency_bound={"child_workers": args.workers, "pool_agents": 2,
                                     "conservative_request_upper_bound": min(2 * args.workers, 7),
                                     "measured_peak": None},
                  summary_resume_policy="Validate semantic and byte equality; summary mtime may be rewritten by the runner")
    return result


def build_jobs(args):
    jobs = [copy.deepcopy(job) for job in helpers().build_jobs(args) if job["regime"] == "cost_moderate"]
    for job in jobs:
        before = list(job["command"])
        command = job["command"]
        indices = []
        for flag, old, new in (("--max-steps", "6", "3"), ("--max-evals", "5", "2")):
            if command.count(flag) != 1:
                raise RuntimeError("Legacy command has duplicate/missing " + flag)
            index = command.index(flag) + 1
            if index >= len(command) or command[index] != old:
                raise RuntimeError("Legacy budget argument changed")
            command[index] = new
            indices.append(index)
        if [i for i, values in enumerate(zip(before, command)) if values[0] != values[1]] != sorted(indices):
            raise RuntimeError("Only the two budget values may change in the frozen command")
    actual = {(job["system"], job["scenario"], job["regime"]) for job in jobs}
    expected = {(system, scenario, "cost_moderate") for system in ("expgym", "poolact") for scenario in SCENARIOS}
    if len(jobs) != 6 or actual != expected or sum(job["expected_traces"] for job in jobs) != 21:
        raise RuntimeError("The six-job / 21-trace plan differs")
    return jobs


def validate_static_acceptance(args):
    receipt = read_json(args.static_acceptance)
    checks = receipt.get("checks", {})
    full, data = checks.get("full_check", {}), checks.get("data_check", {})
    if type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1 or receipt.get("classification") != "Static/fake validation":
        raise ValueError("Unsupported static acceptance schema/classification")
    if type(full.get("exit_code")) is not int or full["exit_code"] != 0 or type(data.get("exit_code")) is not int or data["exit_code"] != 0:
        raise ValueError("Static suite and data checks must both have succeeded")
    if full.get("expgym_fake_e2e") is not True or set(full.get("poolact_fake_e2e_strategies", [])) != set(STRATEGIES):
        raise ValueError("Static acceptance lacks both runners' fake integration checks")
    if checks.get("git_diff_check") != "passed":
        raise ValueError("Static acceptance diff check did not pass")
    if "legacy_python37_new_tests" in checks and checks["legacy_python37_new_tests"].get("exit_code") != 0:
        raise ValueError("Recorded legacy-runtime checks failed")
    files = receipt.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("Static acceptance lacks file bindings")
    for relative, expected in files.items():
        relative_path = Path(relative)
        path = (args.repo_root / relative_path).resolve()
        if relative_path.is_absolute() or ".." in relative_path.parts or not path.is_relative_to(args.repo_root):
            raise ValueError("Static acceptance file escapes the repository")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or not path.is_file() or sha256(path) != expected:
            raise ValueError("Static acceptance file binding differs")
    source = helpers().source_fingerprint(args.repo_root)
    module = helpers().repository_module(args.repo_root, "expgym.trace_v2")
    actual_files = {str(path.relative_to(args.repo_root)) for path in module._source_files(args.repo_root)}
    if not actual_files.issubset(files) or source != receipt.get("source_tree_sha256"):
        raise ValueError("Static acceptance source inventory/fingerprint differs")
    return {"path": str(args.static_acceptance), "sha256": sha256(args.static_acceptance),
            "source_tree_sha256": source, "file_count": len(files)}


def selected_data_identities(args):
    """Compute identities in the selected evaluation interpreter, without tools/API."""
    code = ("import argparse,json,pathlib; from expgym.evaluation_identity import evaluation_identity; "
            "r=pathlib.Path.cwd(); orders=json.loads((r/'configs/audit_hypothesis_orders.json').read_text())['orders'][0]; "
            "print(json.dumps({system+'__'+scenario:evaluation_identity(argparse.Namespace(scenario=scenario,"
            "data_source='phantom_seed1',question_index=0,cc_split='cc-large',tuning_task='hpobench:nasbench101:A',"
            "hypothesis_order=orders if system=='expgym' and scenario=='evidence_audit' else None),r) "
            "for system in ('expgym','poolact') for scenario in ('tuning','restricted_search','evidence_audit')},sort_keys=True))")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([str(args.python), "-B", "-c", code], cwd=args.repo_root, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError("Selected evaluation data/dependency preflight failed")
    return json.loads(result.stdout)


def serving_binding(args):
    if args.serving_binding is None:
        return None
    record = read_json(args.serving_binding)
    if type(record.get("schema_version")) is not int or record["schema_version"] != 1 or record.get("observed_transport_pass") is not True:
        raise ValueError("Serving binding lacks observed successful transport evidence")
    if record.get("model") != args.model or record.get("base_url") != args.base_url or not record.get("job_id"):
        raise ValueError("Serving endpoint/model/job binding differs")
    bound = record.get("planned_maximum_inflight_upper_bound")
    if type(bound) is not int or bound != settings(args)["concurrency_bound"]["conservative_request_upper_bound"]:
        raise ValueError("Serving binding does not declare the frozen dispatch bound")
    peak, slots = record.get("observed_completed_interval_peak"), record.get("effective_slots_per_replica")
    if type(peak) is not int or peak < 1 or type(slots) is not int or slots < 1:
        raise ValueError("Serving binding lacks observed peak/configured admission evidence")
    files = record.get("file_bindings")
    if not isinstance(files, dict) or not {"deployment", "profile", "capacity_source_receipt", "transport_receipt"}.issubset(files):
        raise ValueError("Serving binding must bind deployment/profile/capacity/transport evidence")
    for entry in files.values():
        path = Path(entry["path"])
        if not path.is_absolute():
            path = args.serving_binding.parent / path
        if not path.is_file() or sha256(path) != entry.get("sha256"):
            raise ValueError("Serving evidence file binding differs")
    return {"path": str(args.serving_binding), "sha256": sha256(args.serving_binding),
            "job_id": str(record["job_id"]), "planned_maximum_inflight_upper_bound": bound,
            "observed_completed_interval_peak": peak, "effective_slots_per_replica": slots,
            "file_bindings": files, "metadata_verified_by_harness": False,
            "interpretation": "Observed transport success and configured admission only; no saturation-throughput, queueing, prompt or strict-seed guarantee"}


def binding_identity(args):
    acceptance = validate_static_acceptance(args)
    return {"schema_version": 3, "repo_root": str(args.repo_root), "python": str(args.python),
            "runtime": helpers().runtime_identity(args), "selected_data_identities": selected_data_identities(args),
            "source_tree_sha256": acceptance["source_tree_sha256"], "harness_sha256": sha256(HERE),
            "external_dependencies": {str(path): sha256(path) for path in PINNED_HELPERS},
            "static_acceptance": acceptance, "settings": settings(args), "counts": dict(COUNTS),
            "request_profile": profiles().identity(args), "serving_binding": serving_binding(args),
            "jobs": build_jobs(args), "credential_source": str(args.api_key_file) if args.api_key_file else None,
            "authorization_policy": "Post-plan authorization binds existing manifest/commands; never part of this identity"}


def assert_bindings(args, identity):
    validate_output_tree(args.output_dir)
    if sha256(HERE) != identity["harness_sha256"]:
        raise RuntimeError("New harness source changed")
    for path, expected in identity["external_dependencies"].items():
        if sha256(path) != expected:
            raise RuntimeError("Frozen external dependency changed")
    if validate_static_acceptance(args) != identity["static_acceptance"] or not profiles().unchanged(args):
        raise RuntimeError("Static acceptance or request-profile bytes changed")
    if serving_binding(args) != identity["serving_binding"]:
        raise RuntimeError("Serving/capacity evidence changed")
    runtime = identity.get("runtime", {})
    if runtime.get("executable_sha256") and sha256(args.python) != runtime["executable_sha256"]:
        raise RuntimeError("Evaluation interpreter changed")
    config_path = args.python.parent.parent / "pyvenv.cfg"
    current_config_sha = sha256(config_path) if config_path.is_file() else None
    if current_config_sha != runtime.get("pyvenv_config_sha256"):
        raise RuntimeError("Evaluation virtual environment configuration changed")
    checked = set()
    def verify_inputs(value):
        if isinstance(value, dict):
            if "path" in value and "present" in value and "sha256" in value:
                path = Path(value["path"])
                if str(path) not in checked:
                    checked.add(str(path))
                    if bool(path.is_file()) != value["present"] or (value["present"] and sha256(path) != value["sha256"]):
                        raise RuntimeError("Selected data/evaluator dependency bytes changed")
            for nested in value.values():
                verify_inputs(nested)
        elif isinstance(value, list):
            for nested in value:
                verify_inputs(nested)
    verify_inputs(identity.get("selected_data_identities", {}))


def resume_command(job):
    command = job["command"]
    return command[:2] + [str(HERE), "--_resume-guard"] + command[2:] + ["--resume"]


def command_receipts(jobs):
    return {job["id"]: {"run": job["command"], "dry_run": job["command"] + ["--dry-run"],
                         "resume_guard": resume_command(job)} for job in jobs}


def validate_authorization(args, identity, manifest_path, commands_path):
    if args.authorization is None or identity["serving_binding"] is None:
        raise ValueError("Real execution lacks explicit authorization/serving binding")
    auth = read_json(args.authorization)
    expected = {"schema_version": 1, "authorized": True, "job_id": identity["serving_binding"]["job_id"],
                "model": args.model, "base_url": args.base_url, "output_dir": str(args.output_dir),
                "manifest_sha256": sha256(manifest_path), "commands_sha256": sha256(commands_path),
                "static_acceptance_sha256": identity["static_acceptance"]["sha256"],
                "source_tree_sha256": identity["source_tree_sha256"], "harness_sha256": identity["harness_sha256"],
                "harness_dependencies": identity["external_dependencies"],
                "serving_binding_sha256": identity["serving_binding"]["sha256"],
                "request_profile_sha256": identity["request_profile"]["sha256"],
                "request_profile_file_sha256": identity["request_profile"]["source"]["file_sha256"],
                "counts": {key: COUNTS[key] for key in ("child_jobs", "all_agent_traces", "guarded_resume_skips")}}
    if any(not same_json(auth.get(key), value) for key, value in expected.items()):
        raise ValueError("Authorization does not bind this exact frozen plan")
    return {"path": str(args.authorization), "sha256": sha256(args.authorization), **expected}


def _graph_suffix_check(text, args, agent_id):
    """Validate the bound unified renderer's owned syntax, not its data/state.

    Data rows stay opaque: names, queries and tool feedback may legitimately
    contain protocol-like literals. No claim of reconstructing time visibility,
    node values, cache behavior or the concurrently changing graph is made.
    """
    module = helpers().repository_module(args.repo_root, "expgym.extras.parallel_cache")
    graph = module.SharedExplorationGraph(n_agents=2, diversity_mode=True)
    template = graph._format_unified({}, {}, {}, {}, {}, agent_id=agent_id)
    header = template.splitlines()[:5]
    lines = text.splitlines()
    sections = ("== In Progress ==", "== Already Explored ==", "== Exploration Paths ==", "== Coverage Gap ==")
    if lines[:5] != header or any(lines.count(section) != 1 for section in sections):
        return False
    positions = [lines.index(section) for section in sections]
    if positions != sorted(positions) or positions[0] != 5:
        return False
    bodies = []
    for index, position in enumerate(positions):
        end = positions[index + 1] if index < 3 else len(lines)
        body = lines[position + 1:end]
        if index < 3:
            if not body or body[-1] != "":
                return False
            body = body[:-1]
        if not body or any(not row.startswith("  ") for row in body):
            return False
        bodies.append(body)
    progress, explored, paths, gap = bodies
    if progress != ["  None."] and not all(re.fullmatch(r"  .+ \[agent [01]\]", row) for row in progress):
        return False
    if explored != ["  None completed yet."] and not all(re.fullmatch(r"  .+ \[agents [01](?:,[01])*\](?: \(you\))?", row) for row in explored):
        return False
    if paths != ["  No multi-step paths recorded yet."] and not all(re.fullmatch(r"  .+ --> .+ \[(?:[1-9][0-9]*x, )?agents [01](?:,[01])*\]", row) for row in paths):
        return False
    if len(gap) == 1:
        if gap[0] in ("  No valid configuration found yet.", "  Select an action not listed above."):
            return True
        return bool(re.fullmatch(r"  [0-9]+ NDAs attempted so far\.", gap[0]) or
                    re.fullmatch(r"  [0-9]+ unique configs evaluated, best: -?[0-9]+\.[0-9]{6}", gap[0]))
    return len(gap) == 2 and bool(re.fullmatch(r"  [0-9]+ queries explored so far\.", gap[0])) and (
        gap[1] == "  Try a query not listed above." or
        bool(re.fullmatch(r"  Unfetched leads: \[[0-9]+(?:,[0-9]+)*\]", gap[1])))


def prompt_audit_hook(job, record, args):
    """Reconstruct frozen source-owned system/task instructions with no LLM.

    The v3 resolver is required. First-user context is byte-exact, except for a
    syntactically verified PoolAct-owned graph suffix. Every later user/tool
    message is checked for that same owned suffix; its data is never searched
    for bare Action/Thought literals. Model messages are outside this gate.
    """
    demo = helpers().repository_module(args.repo_root, "demo_experiment")
    resolver = getattr(demo, "_resolve_context", None)
    if resolver is None:
        return {"ready": False, "passed": False, "reason": "trusted_v3_context_resolver_not_ready"}
    protocol = helpers().repository_module(args.repo_root, "expgym.tool_protocol")
    loop = helpers().repository_module(args.repo_root, "expgym.react_loop")
    context = record.get("context", {})
    agent_id = context.get("agent_id", 0) if job["system"] == "poolact" else 0
    if type(agent_id) is not int or agent_id not in (0, 1):
        return {"ready": True, "passed": False, "reason": "invalid_agent_context"}
    order = None
    if job["system"] == "expgym" and job["scenario"] == "evidence_audit":
        order = read_json(args.repo_root / "configs/audit_hypothesis_orders.json")["orders"][0]
    namespace = argparse.Namespace(scenario=job["scenario"], question_index=0, data_source="phantom_seed1",
                                  tuning_task=helpers().TUNING_TASK, cc_split="cc-large", hypothesis_order=order,
                                  seed=args.seed + agent_id, system_prompt=None, tool_protocol="native")
    scenario = demo._SCENARIOS[job["scenario"]]
    # Moderate is time_aware; include_overhead is true only for time_focus.
    expected_context = resolver(scenario, False, namespace, argparse.Namespace(supports_native_tools=True)).strip()
    notes = demo._call_scenario(scenario["build_instruction_notes"], False, namespace)
    system = demo._resolve_system_prompt(scenario, False, namespace)
    expected_system = protocol.native_system_prompt(system or loop.build_system_prompt(instruction_notes=notes))
    # Constructing scenario tool closures reads metadata but does not execute a
    # feedback/evaluation tool or make a model request.
    expected_tools = protocol.native_tool_schemas(demo._resolve_tools(scenario, namespace))
    schemas_match = same_json(record.get("request_payload", {}).get("tools"), expected_tools)
    messages = record.get("request_payload", {}).get("messages", [])
    errors = []
    if not messages or messages[0] != {"role": "system", "content": expected_system} or sum(message.get("role") == "system" for message in messages) != 1:
        errors.append("source_owned_system_prompt_differs")
    if len(messages) < 2 or messages[1].get("role") != "user" or not isinstance(messages[1].get("content"), str):
        errors.append("source_owned_initial_task_context_missing")
        return {"ready": True, "passed": False, "errors": errors, "schema_passed": schemas_match}
    initial = messages[1]["content"]
    coordinated = job["system"] == "poolact" and context.get("strategy") == "poolact"
    marker = "\n\n[Parallel Exploration — Agent {} of 2]\n".format(agent_id)
    graph_receipts = []
    if initial != expected_context:
        suffix = initial[len(expected_context) + 2:] if initial.startswith(expected_context + marker) else None
        if not coordinated or suffix is None or not _graph_suffix_check(suffix, args, agent_id):
            errors.append("source_owned_initial_task_context_or_graph_suffix_differs")
    if coordinated:
        for index, message in enumerate(messages[1:], 1):
            content = message.get("content")
            if message.get("role") not in ("user", "tool") or not isinstance(content, str):
                continue
            # An unmodified first context is known dataset/task text, not a graph.
            if index == 1 and content == expected_context:
                continue
            if marker not in content:
                continue
            suffix = content.rsplit(marker, 1)[1]
            graph_text = marker[2:] + suffix
            valid = _graph_suffix_check(graph_text, args, agent_id)
            graph_receipts.append({"message_index": index, "renderer_owned_syntax_passed": valid,
                                   "suffix_sha256": profiles().digest(graph_text)})
            if not valid:
                errors.append("owned_graph_suffix_syntax_differs_at_message_" + str(index))
    return {"ready": True, "passed": not errors, "errors": errors, "schema_passed": schemas_match,
            "expected_tools_sha256": profiles().digest(expected_tools),
            "method": "exact_v3_system_and_task_context_plus_bound_unified_graph_grammar",
            "expected_system_sha256": profiles().digest(expected_system),
            "expected_task_context_sha256": profiles().digest(expected_context),
            "graph_context_verified": bool(graph_receipts) and all(item["renderer_owned_syntax_passed"] for item in graph_receipts),
            "graph_suffixes": graph_receipts,
            "graph_scope": "owned renderer syntax/instructions only; data values, causality and simulated-time visibility are not reconstructed"}


def _client_artifacts(job):
    root = Path(job["output_dir"])
    if job["system"] == "expgym":
        trace = read_json(next(root.glob("*/traces-v2/*.json")))
        return {trace["run"]["api_dump"]["client_id"]: {"seed": trace["run"]["seed"], "strategy": None, "agent_id": 0}}
    result = {}
    for path in root.glob("*/agents/agent_*.json"):
        agent = read_json(path)
        client = agent["api_dump"]["client_id"]
        if client in result:
            raise ValueError("Duplicate client artifact mapping")
        result[client] = {key: agent[key] for key in ("seed", "strategy", "agent_id")}
    return result


def classify_native_coverage(job, dump_root, args):
    if args.backend == "fake":
        return {"classification": "fake_text_not_native", "wire_passed": None, "prompt_gate_passed": False,
                "prompt_gate_ready": False, "coverage_complete": False, "promotion_eligible": False,
                "missing": ["real_native_requests"], "clients": {}, "cells": {}, "cell_count": 0}
    expected = _client_artifacts(job)
    clients = {key: {**value, "normal_auto": False, "native_continuation": False,
                     "forced_none": False, "graph_context": False, "requests": [],
                     "prompt_gate_passed": True, "schema_passed": True, "wire_passed": True}
               for key, value in expected.items()}
    rows = [(path, read_json(path)) for path in sorted(Path(dump_root).glob("*.json"))]
    rows.sort(key=lambda pair: pair[1].get("started_at_utc", ""))
    wire_errors, prompt_receipts, prior, expected_prefixes = [], [], {}, {}
    for path, record in rows:
        client_id = record.get("client_id")
        if client_id not in clients:
            wire_errors.append("Unknown client identity: " + path.name)
            continue
        client = clients[client_id]
        payload = record.get("request_payload", {})
        identifier = client.get("agent_id")
        valid_agent_id = type(identifier) is int and identifier in ((0, 1) if job["system"] == "poolact" else (0,))
        planned_seed = args.seed + identifier if valid_agent_id else args.seed
        local_errors = profiles().wire_errors(payload, args, seed=planned_seed)
        if not valid_agent_id or type(client.get("seed")) is not int or client["seed"] != planned_seed:
            local_errors.append("Artifact agent identity/seed differs from the immutable plan")
        context = record.get("context", {})
        if context.get("runner") != job["system"]:
            local_errors.append("Dump runner context differs")
        if job["system"] == "poolact" and any(context.get(key) != client[key] for key in ("seed", "strategy", "agent_id")):
            local_errors.append("Dump strategy/agent/seed context differs from artifact")
        schemas = payload.get("tools")
        schemas_ok = isinstance(schemas, list) and bool(schemas) and all(
            isinstance(tool, dict) and tool.get("type") == "function" and isinstance(tool.get("function", {}).get("parameters"), dict) for tool in schemas)
        if not schemas_ok or payload.get("tool_choice") not in ("auto", "none") or payload.get("parallel_tool_calls") is not False:
            local_errors.append("Native schemas/tool choice/parallel-call contract differs")
        messages = payload.get("messages", [])
        pending, paired, history_ok = [], 0, True
        actual_assistants = [message for message in messages if message.get("role") == "assistant"]
        # Membership alone accepts dropped, duplicated or reordered complete
        # pairs. Require every delivered assistant, once, in delivery order.
        if not same_json(actual_assistants, prior.get(client_id, [])):
            history_ok = False
        # Already transmitted tool feedback (including its graph augmentation),
        # task text and all message order are immutable in this three-step smoke.
        # A successful previous delivery adds its original assistant to the
        # required prefix; a transport retry preserves the previous request.
        prefix = expected_prefixes.get(client_id, [])
        if len(messages) < len(prefix) or not same_json(messages[:len(prefix)], prefix):
            history_ok = False
        for message in messages:
            role = message.get("role")
            if role == "assistant":
                if pending:
                    history_ok = False
                pending.extend(call.get("id") for call in message.get("tool_calls") or [])
            elif role == "tool":
                identifier = message.get("tool_call_id")
                if identifier not in pending:
                    history_ok = False
                else:
                    pending.remove(identifier)
                    paired += 1
            elif pending:
                history_ok = False
        if pending or not history_ok:
            local_errors.append("Native history or paired tool IDs differ from original responses")
        try:
            prompt = prompt_audit_hook(job, record, args)
        except Exception as exc:
            prompt = {"ready": False, "passed": False, "reason": "prompt_audit_exception", "error_type": type(exc).__name__}
        if prompt.get("schema_passed") is not True:
            local_errors.append("Actual native tool schemas differ from the trusted scenario schemas or could not be verified")
        client["prompt_gate_passed"] &= prompt.get("ready") is True and prompt.get("passed") is True
        client["schema_passed"] &= prompt.get("schema_passed") is True
        prompt_receipts.append({"request_id": record.get("request_id"), **prompt})
        response = record.get("response_json") or {}
        choices = response.get("choices") or []
        choice = choices[0] if choices and isinstance(choices[0], dict) else {}
        message = choice.get("message") or {}
        delivered = record.get("state") == "success" and isinstance(message, dict) and bool(message)
        if delivered:
            if payload.get("tool_choice") == "auto" and schemas_ok:
                client["normal_auto"] = True
                client["native_continuation"] |= paired > 0 and history_ok
            if payload.get("tool_choice") == "none" and schemas_ok:
                note = bool(messages and FINAL_NOTE in (messages[-1].get("content") or ""))
                client["forced_none"] |= note and history_ok and not message.get("tool_calls") and choice.get("finish_reason") == "stop" and bool(message.get("content"))
            client["graph_context"] |= prompt.get("graph_context_verified") is True
            prior.setdefault(client_id, []).append(copy.deepcopy(message))
        expected_prefixes[client_id] = copy.deepcopy(messages) + ([copy.deepcopy(message)] if delivered else [])
        client["wire_passed"] &= not local_errors
        wire_errors.extend(path.name + ": " + error for error in local_errors)
        client["requests"].append(record.get("request_id"))
    missing, cells = [], {}
    for client_id, client in clients.items():
        requirements = ["normal_auto"]
        if client["strategy"] == "poolact":
            requirements.append("graph_context")
        missing.extend(client_id + ":" + key for key in requirements if not client[key])
        strategy = client["strategy"] if job["system"] == "poolact" else "sequential"
        cell_key = "__".join((job["system"], job["scenario"], str(strategy)))
        cell = cells.setdefault(cell_key, {"system": job["system"], "scenario": job["scenario"],
                                          "strategy": strategy, "clients": [],
                                          "native_continuation": False, "forced_none": False})
        cell["clients"].append(client_id)
        for branch in ("native_continuation", "forced_none"):
            cell[branch] |= client[branch]
    for cell_key, cell in cells.items():
        branches = ("native_continuation", "forced_none")
        cell["coverage_complete"] = all(cell[branch] for branch in branches)
        missing.extend(cell_key + ":" + branch for branch in branches if not cell[branch])
    expected_cell_keys = {"__".join((job["system"], job["scenario"], strategy))
                          for strategy in (STRATEGIES if job["system"] == "poolact" else ("sequential",))}
    if set(cells) != expected_cell_keys:
        wire_errors.append("Coverage strategy cells differ from the immutable job plan")
        missing.append("expected_strategy_cells")
    expected_agents_per_cell = 2 if job["system"] == "poolact" else 1
    for cell_key, cell in cells.items():
        if len(cell["clients"]) != expected_agents_per_cell:
            wire_errors.append("Coverage cell client count differs: " + cell_key)
    if len(clients) != job["expected_traces"] or not rows:
        missing.append("expected_client_or_dump_count")
    ready = bool(prompt_receipts) and all(item.get("ready") is True for item in prompt_receipts)
    prompt_passed = ready and all(item.get("passed") is True for item in prompt_receipts)
    wire_passed = not wire_errors
    complete = not missing
    return {"classification": "Real smoke validation", "wire_passed": wire_passed, "wire_errors": wire_errors,
            "prompt_gate_ready": ready, "prompt_gate_passed": prompt_passed, "prompt_audits": prompt_receipts,
            "coverage_complete": complete, "missing": missing, "clients": clients,
            "cells": cells, "cell_count": len(cells),
            "promotion_eligible": wire_passed and prompt_passed and complete,
            "http_status_note": "Null success status is a dump-field limitation; router receipts supply external HTTP status evidence",
            "randomness_contract": "seed_labels_only"}


def validate_planned_artifacts(job, args, expected_data=None):
    root, errors = Path(job["output_dir"]), []
    selected = generation_profile(args)
    wanted_generation = {key: selected[key] for key in ("temperature", "top_p", "top_k", "reasoning_effort", "chat_template_kwargs")}
    wanted_generation["max_tokens"] = 32768
    def require(condition, message):
        if not condition:
            errors.append(message)
    if job["system"] == "expgym":
        trace = read_json(next(root.glob("*/traces-v2/*.json")))
        task, run = trace["task"], trace["run"]
        require(task.get("scenario") == job["scenario"] and task.get("budget", {}).get("regime") == "cost_moderate", "ExpGym task/regime differs")
        require(task.get("limits", {}).get("max_steps") == 3 and task.get("limits", {}).get("max_evaluations") == 2, "ExpGym actual budget is not 3/2")
        require(run.get("seed") == args.seed, "ExpGym seed differs")
        if args.backend != "fake":
            require(run.get("model", {}).get("id") == args.model, "ExpGym model differs")
            require(all(same_json(run.get("generation", {}).get(key), value) for key, value in wanted_generation.items()), "ExpGym generation differs")
        identity = run.get("evaluation_identity")
        if expected_data is not None:
            require(same_json(identity, expected_data), "ExpGym planned input/dependency identity differs")
    else:
        wanted = {"scenario": job["scenario"], "cost_regime": "cost_moderate", "max_steps": 3, "max_evals": 2,
                  "model": args.model, "backend": args.backend, "agents": 2, "seed": args.seed,
                  "agent_seeds": [args.seed, args.seed + 1],
                  "strategies": list(STRATEGIES), "repeats": 1, **wanted_generation}
        for path in root.glob("*/result.json"):
            result = read_json(path)
            config = result.get("config", {})
            require(all(same_json(config.get(key), value) for key, value in wanted.items()), "PoolAct planned configuration differs: " + path.parent.name)
            strategy = path.parent.name
            require(strategy in STRATEGIES, "PoolAct strategy path differs")
            agents = result.get("agent_results", [])
            require(len(agents) == 2, "PoolAct embedded agent count differs")
            valid_ids = []
            for agent in agents:
                agent_id = agent.get("agent_id")
                valid_id = type(agent_id) is int and agent_id in (0, 1)
                require(valid_id, "PoolAct embedded agent ID is not integer 0 or 1")
                if valid_id:
                    valid_ids.append(agent_id)
                    require(type(agent.get("seed")) is int and agent["seed"] == args.seed + agent_id,
                            "PoolAct embedded agent seed differs from the fixed plan")
                require(agent.get("strategy") == strategy, "PoolAct embedded agent strategy differs from its path")
            require(sorted(valid_ids) == [0, 1], "PoolAct embedded IDs must cover exactly 0 and 1")
            if expected_data is not None:
                require(same_json(config.get("evaluation_identity"), expected_data), "PoolAct planned input/dependency identity differs")
        for path in root.glob("*/agents/agent_*.json"):
            agent = read_json(path)
            match = re.fullmatch(r"agent_([01])\.json", path.name)
            strategy = path.parent.parent.name
            require(match is not None and strategy in STRATEGIES, "PoolAct separate agent artifact path differs")
            if match is not None:
                agent_id = int(match.group(1))
                require(type(agent.get("agent_id")) is int and agent["agent_id"] == agent_id,
                        "PoolAct separate agent ID differs from its filename")
                require(type(agent.get("seed")) is int and agent["seed"] == args.seed + agent_id,
                        "PoolAct separate agent seed differs from the fixed plan")
            require(agent.get("strategy") == strategy, "PoolAct separate agent strategy differs from its directory")
    return {"passed": not errors, "errors": errors}


def snapshot_summary(job):
    path = Path(job["output_dir"]) / "summary.json"
    if not path.exists():
        return None
    return {"sha256": sha256(path), "bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns,
            "semantic_sha256": profiles().digest(read_json(path))}


def _sanitize_environment():
    for name in list(os.environ):
        if "proxy" in name.lower():
            os.environ.pop(name, None)
    os.environ.update(NO_PROXY="*", no_proxy="*", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")


def validate_output_tree(output_dir):
    """Never let artifact/dump/log writes follow pre-existing subtree symlinks."""
    output_dir = Path(output_dir)
    for name in ("results", "dumps", "logs"):
        root = output_dir / name
        if root.is_symlink() or (root.exists() and not root.is_dir()):
            raise RuntimeError("Output subtree is a symlink or not a directory: " + name)
        if not root.exists():
            continue
        for directory, directories, files in os.walk(root, followlinks=False):
            for entry in directories + files:
                if (Path(directory) / entry).is_symlink():
                    raise RuntimeError("Output subtree contains a descendant symlink: " + name)


def _resume_guard(argv):
    runner = Path(argv[0]).resolve() if argv else None
    if runner is None or argv.count("--resume") != 1 or "--output-dir" not in argv:
        raise RuntimeError("Invalid guarded resume invocation")
    output = Path(argv[argv.index("--output-dir") + 1]).resolve()
    plan_root = output.parent.parent
    validate_output_tree(plan_root)
    manifest_path, commands_path = plan_root / "manifest.json", plan_root / "commands.json"
    launch = read_json(plan_root / "launch_receipt.json")
    if launch.get("manifest_sha256") != sha256(manifest_path) or launch.get("commands_sha256") != sha256(commands_path):
        raise RuntimeError("Resume manifest/commands differ from the launch receipt")
    authorization = launch.get("authorization")
    if authorization is not None:
        auth_path = Path(authorization["path"])
        if sha256(auth_path) != authorization.get("sha256"):
            raise RuntimeError("Resume authorization bytes changed")
        auth = read_json(auth_path)
        if any(not same_json(auth.get(key), value) for key, value in authorization.items() if key not in ("path", "sha256")):
            raise RuntimeError("Resume authorization no longer matches the launch receipt")
        if authorization.get("manifest_sha256") != sha256(manifest_path) or authorization.get("commands_sha256") != sha256(commands_path) or authorization.get("authorized") is not True:
            raise RuntimeError("Resume authorization does not approve this manifest/commands")
    manifest = read_json(manifest_path)
    identity = manifest["identity"]
    if identity["settings"]["backend"] != "fake" and authorization is None:
        raise RuntimeError("Real guarded resume has no launch authorization")
    if sha256(HERE) != identity["harness_sha256"]:
        raise RuntimeError("Resume harness changed")
    for path, digest in identity["external_dependencies"].items():
        if sha256(path) != digest:
            raise RuntimeError("Resume dependency changed")
    matches = [job for job in identity["jobs"] if job["command"][2:] + ["--resume"] == argv]
    if len(matches) != 1 or runner != Path(identity["repo_root"]) / "scripts" / ("run_paper_sweep.py" if matches[0]["system"] == "expgym" else "run_poolact.py"):
        raise RuntimeError("Guarded runner/argv differs from immutable plan")
    if helpers().source_fingerprint(Path(identity["repo_root"])) != identity["source_tree_sha256"]:
        raise RuntimeError("Resume repository source changed")
    if read_json(commands_path) != command_receipts(identity["jobs"]):
        raise RuntimeError("Resume commands receipt differs from the manifest")
    helpers().resume_guard(argv)


def main(argv=None):
    args = parse_args(argv)
    _sanitize_environment()
    legacy = helpers()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    validate_output_tree(args.output_dir)
    with (args.output_dir / ".harness.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        identity = binding_identity(args)
        jobs = identity["jobs"]
        manifest_path, commands_path = args.output_dir / "manifest.json", args.output_dir / "commands.json"
        commands = command_receipts(jobs)
        if manifest_path.exists():
            if read_json(manifest_path).get("identity") != identity or not commands_path.is_file() or read_json(commands_path) != commands:
                raise RuntimeError("Immutable plan differs; use a fresh directory")
        else:
            if commands_path.exists():
                raise RuntimeError("Orphan commands receipt exists")
            legacy.atomic_json(manifest_path, {"created_utc": legacy.utc_now(), "identity": identity})
            legacy.atomic_json(commands_path, commands)
        if any((args.output_dir / name).exists() for name in ("execution_started.json", "execution.json", "launch_receipt.json")):
            raise RuntimeError("This attempt already started; no automatic replay or replacement")
        secrets, authorization = [], None
        if args.execute:
            if any((args.output_dir / directory).exists() and any((args.output_dir / directory).rglob("*")) for directory in ("results", "dumps")):
                raise RuntimeError("Pre-existing results or orphan dumps; refuse result replacement")
            if args.backend == "openai":
                authorization = validate_authorization(args, identity, manifest_path, commands_path)
                if args.api_key_file.stat().st_mode & 0o077:
                    raise RuntimeError("The private key file must not be group/world accessible")
                key = args.api_key_file.read_text().strip()
                if not key:
                    raise RuntimeError("Real execution requires a nonempty private key file")
                secrets = [key]
            assert_bindings(args, identity)
            legacy.atomic_json(args.output_dir / "execution_started.json", {"created_utc": legacy.utc_now(),
                               "harness_pid": os.getpid(), "harness_sha256": identity["harness_sha256"],
                               "source_tree_sha256": identity["source_tree_sha256"], "counts": COUNTS,
                               "note": "One fixed attempt. All semantic outcomes retained; no automatic replacement."})
            legacy.atomic_json(args.output_dir / "launch_receipt.json", {"created_utc": legacy.utc_now(),
                               "manifest_sha256": sha256(manifest_path), "commands_sha256": sha256(commands_path),
                               "authorization": authorization, "proxy_policy": "all inherited proxy variables removed; NO_PROXY/no_proxy=*"})

        def worker(job):
            assert_bindings(args, identity)
            if authorization is not None and validate_authorization(args, identity, manifest_path, commands_path) != authorization:
                raise RuntimeError("Authorization changed before dispatch")
            command = job["command"] if args.execute else job["command"] + ["--dry-run"]
            receipt, output = legacy.run_child(command, args, job, "run.log" if args.execute else "dry_run.log", secrets)
            result = {"job_id": job["id"], "run": receipt, "passed": receipt["exit_code"] == 0}
            if args.execute and result["passed"]:
                validation = legacy.validate_job(job, identity["source_tree_sha256"], args.backend)
                planned = validate_planned_artifacts(job, args, identity["selected_data_identities"][job["system"] + "__" + job["scenario"]])
                result.update(validation=validation, planned_configuration=planned)
                result["passed"] = validation["passed"] and planned["passed"]
                before = legacy.snapshot_artifacts(job)
                dump_root = args.output_dir / "dumps" / job["id"]
                dumps_before, summary_before = legacy.snapshot_dumps(dump_root), snapshot_summary(job)
                if args.backend != "fake" and result["passed"]:
                    dump_validation = legacy.validate_api_dumps(job, dump_root)
                    result["dump_validation"] = dump_validation
                    result["passed"] = dump_validation["passed"]
                if result["passed"]:
                    validate_output_tree(args.output_dir)
                    resume, resume_output = legacy.run_child(resume_command(job), args, job, "resume.log", secrets)
                    skips = resume_output.count("skip verified") if job["system"] == "expgym" else resume_output.count("[resume] item=0 strategy=")
                    expected_skips = 1 if job["system"] == "expgym" else 3
                    unchanged, no_api = before == legacy.snapshot_artifacts(job), dumps_before == legacy.snapshot_dumps(dump_root)
                    after_validation = legacy.validate_job(job, identity["source_tree_sha256"], args.backend)
                    summary_after = snapshot_summary(job)
                    summary_equal = (summary_before is None and summary_after is None) or (
                        summary_before is not None and summary_after is not None and all(summary_before[key] == summary_after[key] for key in ("sha256", "bytes", "semantic_sha256")))
                    result["resume"] = {**resume, "protective_model_call_guard": True, "verified_skips": skips,
                                        "expected_skips": expected_skips, "trace_bytes_and_mtimes_unchanged": unchanged,
                                        "api_dump_bytes_and_mtimes_unchanged": no_api, "post_resume_validation": after_validation,
                                        "summary_bytes_and_semantics_unchanged": summary_equal,
                                        "summary_before": summary_before, "summary_after": summary_after,
                                        "summary_mtime_may_be_rewritten": True}
                    result["passed"] = resume["exit_code"] == 0 and skips == expected_skips and unchanged and no_api and summary_equal and after_validation["passed"] and "rerun" not in resume_output.lower()
                result.update(artifacts=before, api_dumps=dumps_before)
                # Wire/profile/history corruption is integrity failure. Missing
                # paths from natural early answers never stop the fixed jobs.
                result["native_coverage"] = classify_native_coverage(job, dump_root, args)
                if args.backend != "fake" and result["native_coverage"]["wire_passed"] is not True:
                    result["passed"] = False
            assert_bindings(args, identity)
            legacy.atomic_json(args.output_dir / "logs" / job["id"] / ("status.json" if args.execute else "dry_run_status.json"), result)
            return result

        def safe_worker(job):
            try:
                return worker(job)
            except Exception as exc:
                result = {"job_id": job["id"], "passed": False,
                          "error_type": type(exc).__name__, "failure_policy": "failed_closed; no automatic retry"}
                # In particular, do not write the diagnostic itself through an
                # unsafe logs subtree discovered by the failed binding check.
                validate_output_tree(args.output_dir)
                legacy.atomic_json(args.output_dir / "logs" / job["id"] / ("status.json" if args.execute else "dry_run_status.json"), result)
                return result

        started = time.monotonic()
        report = legacy.run_bounded(jobs, safe_worker, args.workers)
        integrity = not report["failed"] and not report["unstarted"]
        coverage = [item.get("native_coverage", {}) for item in report["results"]]
        prompt_passed = args.backend == "openai" and len(coverage) == len(jobs) and all(item.get("prompt_gate_passed") is True for item in coverage)
        paths_complete = args.backend == "openai" and len(coverage) == len(jobs) and all(item.get("coverage_complete") is True and item.get("wire_passed") is True for item in coverage)
        promotion = bool(args.execute and integrity and prompt_passed and paths_complete)
        report.update(created_utc=legacy.utc_now(), elapsed_seconds=time.monotonic() - started,
                      classification="Real smoke validation" if args.execute and args.backend == "openai" else "Static/fake validation",
                      executed=args.execute, passed=integrity, artifact_integrity_passed=integrity,
                      prompt_gate_passed=prompt_passed, coverage_complete=paths_complete, promotion_eligible=promotion,
                      source_tree_sha256=identity["source_tree_sha256"], harness_sha256=identity["harness_sha256"],
                      external_dependencies=identity["external_dependencies"], counts=COUNTS,
                      observed_coverage_cell_count=sum(item.get("cell_count", 0) for item in coverage),
                      validated_trace_count=sum(item.get("validation", {}).get("trace_count", 0) for item in report["results"]),
                      verified_resume_skips=sum(item.get("resume", {}).get("verified_skips", 0) for item in report["results"]),
                      semantic_zero_count=sum(item.get("validation", {}).get("semantic_zero_count", 0) for item in report["results"]),
                      randomness_contract="seed_labels_only", no_additional_api_for_missing_coverage=True)
        if args.execute and integrity and (report["validated_trace_count"] != 21 or report["verified_resume_skips"] != 12):
            report["passed"] = report["artifact_integrity_passed"] = report["promotion_eligible"] = False
        if args.execute and args.backend == "openai" and report["observed_coverage_cell_count"] != 12:
            report["coverage_complete"] = report["promotion_eligible"] = False
        try:
            assert_bindings(args, identity)
        except Exception as exc:
            report["passed"] = report["artifact_integrity_passed"] = report["promotion_eligible"] = False
            report["final_binding_check"] = {"passed": False, "error_type": type(exc).__name__}
        legacy.atomic_json(args.output_dir / ("execution.json" if args.execute else "dry_run.json"), report)
        print(json.dumps({key: report[key] for key in ("passed", "executed", "classification", "validated_trace_count", "verified_resume_skips", "prompt_gate_passed", "coverage_complete", "promotion_eligible", "unstarted")}, indent=2))
        return 0 if report["passed"] and (not args.execute or args.backend == "fake" or report["promotion_eligible"]) else 1


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--_resume-guard":
            _resume_guard(sys.argv[2:])
        else:
            raise SystemExit(main())
    except Exception as exc:
        # Do not serialize arbitrary exception text, which may contain secrets.
        print(json.dumps({"passed": False, "error_type": type(exc).__name__}), file=sys.stderr)
        raise SystemExit(1)
