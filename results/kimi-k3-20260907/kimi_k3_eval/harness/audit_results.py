#!/usr/bin/env python3
"""Read-only manifest-driven result audit; compatible with the ParamNet Python 3.7.

Never glob arbitrary JSON as traces. Each expected artifact is checked, scored
again using the current repository, and indexed with its SHA256. Run receipts,
source/config fingerprints, PoolAct individual files and summaries are required.
The output directory must be new, so earlier audits and raw data are preserved.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


FULL_COUNTS = {"expgym_traces": 303, "poolact_results": 513,
               "poolact_agent_traces": 2052, "total_agent_traces": 2355,
               "poolact_paper_results": 192, "poolact_paper_agent_traces": 768}
TUNING_TASKS = ["hpobench:paramnet:%s:steps" % x for x in ("adult", "higgs", "letter")] + [
    "hpobench:nasbench101:%s" % x for x in ("A", "B", "C")] + [
    "hpobench:nasbench201:%s" % x for x in ("cifar10-valid", "cifar100", "imagenet16-120")]
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STRATEGIES = ("naive", "cached", "poolact")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values and all(finite(x) for x in values) else None


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_json(path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate JSON key: %s" % key)
            out[key] = value
        return out
    def bad_number(value):
        raise ValueError("nonfinite JSON number: %s" % value)
    value = json.loads(Path(path).read_text(encoding="utf-8"),
                       object_pairs_hook=pairs, parse_constant=bad_number)
    json.dumps(value, allow_nan=False)  # Also rejects overflow such as 1e999.
    return value


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def write_csv(path, rows, fields=None):
    if fields is None:
        fields = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, allow_nan=False)
                             if isinstance(value, (dict, list)) else value for key, value in row.items()})


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_json_schema(value, schema, root=None, at="$",):
    """Validate the complete keyword vocabulary in the checked-in v2 schema.

    A small dependency-free validator lets identical checks run in Python 3.7.
    Unknown validation keywords fail closed if the repository schema evolves.
    """
    root = root or schema
    supported = {"$schema", "$id", "$defs", "$ref", "title", "description", "type",
                 "additionalProperties", "required", "properties", "const", "items",
                 "oneOf", "not", "minimum", "minLength"}
    require(not (set(schema) - supported), "unsupported schema keywords: %s" % (set(schema) - supported))
    if "$ref" in schema:
        ref = schema["$ref"]
        require(ref.startswith("#/"), "nonlocal schema reference")
        target = root
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        validate_json_schema(value, target, root, at)
    predicates = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
                  "string": lambda x: isinstance(x, str), "number": finite,
                  "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
                  "boolean": lambda x: isinstance(x, bool), "null": lambda x: x is None}
    if "type" in schema:
        kinds = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        require(any(predicates[kind](value) for kind in kinds), "%s: wrong type" % at)
    if "const" in schema:
        require(value == schema["const"], "%s: wrong constant" % at)
    if isinstance(value, dict):
        require(not (set(schema.get("required", [])) - set(value)), "%s: missing required fields" % at)
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            require(not (set(value) - set(properties)), "%s: unexpected fields" % at)
        for key in set(value) & set(properties):
            validate_json_schema(value[key], properties[key], root, "%s.%s" % (at, key))
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate_json_schema(item, schema["items"], root, "%s[%d]" % (at, index))
    if "minimum" in schema and finite(value):
        require(value >= schema["minimum"], "%s: below minimum" % at)
    if "minLength" in schema and isinstance(value, str):
        require(len(value) >= schema["minLength"], "%s: below minimum length" % at)
    def matches(candidate):
        try:
            validate_json_schema(value, candidate, root, at)
            return True
        except ValueError:
            return False
    if "oneOf" in schema:
        require(sum(matches(candidate) for candidate in schema["oneOf"]) == 1, "%s: oneOf failed" % at)
    if "not" in schema:
        require(not matches(schema["not"]), "%s: forbidden shape" % at)


def load_runners(repo):
    repo = Path(repo).resolve()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    result = []
    for name in ("run_paper_sweep", "run_poolact"):
        key = "kimi_audit_" + name
        if key not in sys.modules:
            spec = importlib.util.spec_from_file_location(key, repo / "scripts" / (name + ".py"))
            module = importlib.util.module_from_spec(spec)
            sys.modules[key] = module
            spec.loader.exec_module(module)
        result.append(sys.modules[key])
    return tuple(result)


def parsed_command(job, runner):
    command = job["command"]
    target = "run_paper_sweep.py" if job["system"] == "expgym" else "run_poolact.py"
    positions = [i for i, arg in enumerate(command) if Path(arg).name == target]
    require(len(positions) == 1, "command must identify exactly one repository runner")
    previous = sys.argv
    try:
        sys.argv = [target] + command[positions[0] + 1:]
        args = runner.parse_args()
    finally:
        sys.argv = previous
    require(args.output_dir.resolve() == Path(job["output_dir"]).resolve(), "command/output_dir mismatch")
    return args


def paper_subset(job):
    if job["system"] != "poolact" or job["cost_regime"] not in ("cost_moderate", "cost_tight"):
        return False
    if job["scenario"] == "tuning":
        return job.get("tuning_task") == "hpobench:nasbench101:A"
    index = int(job["question_index"])
    return 0 <= index < (18 if job["scenario"] == "restricted_search" else 13)


def validate_manifest(manifest):
    issues, counts, paths, keys = [], collections.Counter(), set(), set()
    settings = manifest["settings"]
    orders_path = Path(settings["audit_orders_path"])
    require(sha256(orders_path) == settings["audit_orders_sha256"], "audit ordering file changed")
    require(strict_json(orders_path)["orders"] == settings["audit_orders"], "manifest hypothesis order data differs")
    orders = settings["audit_orders"]
    require(len(orders) == 3 and len({tuple(order) for order in orders}) == 3
            and all(len(order) == 17 and len(set(order)) == 17 and set(order) == set(orders[0]) for order in orders),
            "three distinct complete 17-hypothesis orderings required")
    for name, source in manifest.get("data_provenance", {}).items():
        require(source.get("sha256") and sha256(source["path"]) == source["sha256"],
                "data provenance differs: " + name)
        if name == "dataset_manifest":
            dataset = strict_json(source["path"])
            require(dataset.get("passed") is True and dataset.get("files"), "dataset inventory did not pass")
            hpo_root = Path(manifest["repo_root"]) / "data/hpo_tuning/HPOBench"
            for command, expected in ((["rev-parse", "HEAD"], dataset.get("hpobench_commit")),
                                      (["status", "--porcelain"], dataset.get("hpobench_git_status"))):
                actual = subprocess.check_output(["git", "-C", str(hpo_root)] + command,
                                                 universal_newlines=True).strip()
                require(expected is not None and actual == expected, "HPOBench evaluator source changed")
            for entry in dataset["files"]:
                file_path = Path(entry["path"])
                if not file_path.is_absolute():
                    file_path = Path(manifest["repo_root"]) / file_path
                require(file_path.stat().st_size == entry["bytes"] and sha256(file_path) == entry["sha256"],
                        "frozen dataset file changed: " + str(file_path))
    counts["subprocess_jobs"] = len(manifest["jobs"])
    for job in manifest["jobs"]:
        require(job["id"] not in keys, "duplicate manifest job id")
        keys.add(job["id"])
        require(bool(job.get("paper_subset")) == paper_subset(job), "incorrect paper_subset on %s" % job["id"])
        for output in job["expected_outputs"]:
            artifact_paths = [output["path"]] + output.get("agent_paths", [])
            for path in artifact_paths:
                require(Path(path).is_absolute(), "artifact paths must be absolute")
                require(path not in paths, "duplicate expected artifact path: %s" % path)
                paths.add(path)
            if output["kind"] == "expgym_trace":
                counts["expgym_traces"] += 1
            elif output["kind"] == "poolact_result":
                counts["poolact_results"] += 1
                counts["poolact_agent_traces"] += len(output["agent_paths"])
                require(len(output["agent_paths"]) == job["agents"], "agent count mismatch")
                if paper_subset(job):
                    counts["poolact_paper_results"] += 1
                    counts["poolact_paper_agent_traces"] += len(output["agent_paths"])
            else:
                raise ValueError("unsupported output kind")
    counts["total_agent_traces"] = counts["expgym_traces"] + counts["poolact_agent_traces"]
    for key, count in counts.items():
        if manifest.get("counts", {}).get(key) != count:
            issues.append("manifest counts.%s differs from enumerated %d" % (key, count))
    if manifest.get("stage") == "full":
        for key, expected in FULL_COUNTS.items():
            if counts[key] != expected:
                issues.append("full matrix %s requires %d, got %d" % (key, expected, counts[key]))
        actual = collections.Counter()
        for job in manifest["jobs"]:
            for output in job["expected_outputs"]:
                slot = output.get("rep") if job["system"] == "expgym" else output.get("strategy")
                actual[(job["system"], job["scenario"], str(job["item_id"]), job["cost_regime"], slot)] += 1
            if job["system"] == "poolact" and job["agents"] != 4:
                issues.append("full PoolAct requires four agents: " + job["id"])
        wanted = collections.Counter()
        for system in ("expgym", "poolact"):
            for scenario, items in (("tuning", TUNING_TASKS), ("restricted_search", range(35)), ("evidence_audit", range(13))):
                slots = (range(1 if scenario == "restricted_search" else 3) if system == "expgym" else STRATEGIES)
                for item in items:
                    for regime in REGIMES:
                        for slot in slots:
                            wanted[(system, scenario, str(item), regime, slot)] += 1
        if actual != wanted:
            issues.append("full matrix identity mismatch: missing=%s extra=%s" % (list((wanted - actual).items()), list((actual - wanted).items())))
    return dict(counts), issues


def base_record(job, output):
    return {"job_id": job["id"], "system": job["system"], "scenario": job["scenario"],
            "item_id": str(job["item_id"]), "tuning_task": job.get("tuning_task"),
            "question_index": job.get("question_index"), "cost_regime": job["cost_regime"],
            "paper_subset": paper_subset(job), "kind": output["kind"], "path": output["path"],
            "rep": output.get("rep"), "seed": output.get("seed", job["seed"]),
            "strategy": output.get("strategy"), "status": "missing", "issues": [], "agent_records": [],
            "expected_agent_paths": output.get("agent_paths", [])}


def trace_to_result(trace):
    from expgym.react_loop import _extract_answer
    from expgym.trace_v2 import materialize_message
    outcome, score = trace["outcome"], trace["outcome"]["score"]
    answer = outcome.get("answer_override")
    if answer is None and outcome.get("answer_message_id") is not None:
        content = materialize_message(trace, outcome["answer_message_id"])["content"]
        answer = _extract_answer(content) or content
    records = []
    for tool in trace["tool_calls"]:
        argument = tool["arguments"]
        if isinstance(argument, dict) and set(argument) == {"raw", "encoding"} and argument["encoding"] == "text":
            argument = argument["raw"]
        else:
            argument = json.dumps(argument, ensure_ascii=False)
        records.append((tool["name"], argument, tool.get("structured_result", tool.get("withheld_result"))))
    return {"answer": answer, "answer_perf": score.get("metrics", {}).get("label_acc", score.get("value")),
            "answer_metrics": score.get("metrics"), "tool_records": records, "eval_records": []}


def raw_metrics(result, trace=None):
    metrics = result.get("answer_metrics") or {}
    row = {"answer_perf": result.get("answer_perf"), "label_acc": metrics.get("label_acc"),
           "evidence_acc": metrics.get("evidence_acc"), "verification_eff": metrics.get("verification_eff"),
           "raw_metrics": result.get("answer_metrics"), "wall_time_seconds": result.get("wall_time_seconds"),
           "simulated_cost_seconds": result.get("total_overhead"), "evaluations": result.get("evaluations"),
           "logical_api_calls": result.get("api_calls"), "input_tokens": result.get("prompt_tokens"),
           "output_tokens": result.get("completion_tokens"), "cached_input_tokens": result.get("cached_prompt_tokens"),
           "llm_time_seconds": result.get("llm_time"), "aborted": result.get("aborted")}
    if trace:
        calls, tools = trace["llm_calls"], trace["tool_calls"]
        def token_sum(field):
            values = [(call.get("usage") or {}).get(field) for call in calls]
            return sum(values) if values and all(finite(x) for x in values) else None
        caches = [((call.get("usage") or {}).get("cache") or {}) for call in calls]
        row.update(wall_time_seconds=trace["timing"].get("wall_time_seconds"),
                   simulated_cost_seconds=sum(tool["simulated_cost_seconds"] for tool in tools),
                   evaluations=len(tools), logical_api_calls=len(calls),
                   request_attempts=sum(call["request_attempts"] for call in calls),
                   input_tokens=token_sum("input_tokens"), output_tokens=token_sum("output_tokens"),
                   cached_input_tokens=sum((x.get("read_tokens") or 0) for x in caches) if caches and all(x.get("reported") for x in caches) else None,
                   llm_time_seconds=sum(call["latency_seconds"] for call in calls),
                   aborted=trace["outcome"]["status"] != "completed",
                   termination_reason=trace["outcome"]["termination_reason"])
    return row


def check_command_identity(job, args, manifest):
    settings = manifest["settings"]
    require(args.seed == job["seed"], "manifest/command seed differs")
    require(args.seed == settings["seed"], "command/settings base seed differs")
    require(args.backend == settings["backend"], "manifest/command backend differs")
    require(args.base_url == settings["base_url"], "command/settings base URL differs")
    require(args.max_steps == settings["max_steps"] and args.max_evals == settings["max_evals"],
            "command/settings horizon differs")
    for field in ("max_tokens", "chat_template_kwargs", "request_timeout", "max_retries",
                  "retry_base_seconds", "retry_max_seconds"):
        require(getattr(args, field, None) == settings.get(field), "command/settings %s differs" % field)
    if manifest.get("stage") == "full":
        require(args.max_steps == 30 and args.max_evals == 30, "full study requires 30 steps/evaluations")
        temperature = (args.temperature_tuning if job["scenario"] == "tuning" else args.temperature_eval) if job["system"] == "expgym" else args.temperature
        expected_temp = 0.7 if job["system"] == "poolact" or job["scenario"] == "tuning" else 0.0
        require(temperature == expected_temp, "full study temperature differs from protocol")
    if job["system"] == "poolact":
        require(args.model == settings["model"], "PoolAct command/settings model differs")
        require(args.temperature == job["temperature"] == settings["temperature_poolact"],
                "PoolAct command/settings temperature differs")
        require(args.agents == settings["poolact_agents"], "PoolAct command/settings agents differs")
        require(args.scenario == job["scenario"] and args.cost_regime == job["cost_regime"], "PoolAct manifest/command scenario or regime differs")
        require(args.agents == job["agents"] and args.strategies == job["strategies"], "PoolAct manifest/command agents or strategies differs")
        require(args.question_index == job["question_index"], "PoolAct manifest/command index differs")
        if args.scenario == "tuning":
            require(args.tuning_task == job["tuning_task"], "PoolAct manifest/command tuning task differs")
    if job["scenario"] == "restricted_search":
        source = args.search_data_source if job["system"] == "expgym" else args.data_source
        require(source == "phantom_seed1", "study requires pinned phantom_seed1 search source")
    if job["scenario"] == "evidence_audit":
        require(args.cc_split == "cc-large", "study requires cc-large audit")


def audit_job(job, manifest):
    repo = Path(manifest["repo_root"]).resolve()
    sweep, pool = load_runners(repo)
    from expgym.trace_v2 import source_tree_sha256, validate_trace_v2, _task_metadata
    current_source = source_tree_sha256(repo)
    outputs = [base_record(job, output) for output in job["expected_outputs"]]
    try:
        args = parsed_command(job, sweep if job["system"] == "expgym" else pool)
        check_command_identity(job, args, manifest)
        source = manifest.get("source_tree_sha256", manifest.get("settings", {}).get("source_tree_sha256"))
        require(source == current_source, "manifest source_tree_sha256 does not match current repository")
        if job["system"] == "expgym":
            require(args.trace_format == "v2", "study requires ExpGym trace v2")
            native_jobs = {str(sweep._trace_path(args.output_dir, native, "v2").resolve()): native for native in sweep._build_jobs(args)}
            require(set(native_jobs) == {out["path"] for out in job["expected_outputs"]}, "manifest outputs differ from runner-expanded jobs")
        else:
            c_base = pool.resolve_base_cost(args.scenario, args)
            time_budget, _ = pool.resolve_cost_regime(args, c_base)
            config = pool._resolved_config(args, time_budget)
    except Exception as exc:
        for row in outputs:
            row.update(status="invalid", issues=["configuration: %s: %s" % (type(exc).__name__, exc)])
        return outputs
    for output, row in zip(job["expected_outputs"], outputs):
        path = Path(output["path"])
        if not path.is_file():
            row["issues"].append("expected artifact missing")
            continue
        try:
            data = strict_json(path)
            row["sha256"] = sha256(path)
            if job["system"] == "expgym":
                native = native_jobs[str(path)]
                require(native.model_id == manifest["settings"]["model"]
                        and native.model_alias == manifest["settings"]["model_alias"], "ExpGym command/settings model differs")
                require(native.scenario == job["scenario"] and native.cost_regime == job["cost_regime"], "manifest logical identity mismatch")
                require(str(native.tuning_task if native.scenario == "tuning" else native.question_index) == str(job["item_id"]), "manifest item mismatch")
                require(native.rep == output["rep"] and native.seed == output["seed"], "manifest repeat/seed mismatch")
                require(native.hypothesis_order == output.get("hypothesis_order"), "manifest hypothesis order mismatch")
                validate_json_schema(data, strict_json(repo / "schemas" / "trace-v2.schema.json"))
                validate_trace_v2(data)
                require(sweep._resume_trace_is_valid(path, args, native), "repository resume rejected trace")
                require(data["provenance"]["repository"]["source_tree_sha256"] == current_source, "trace source mismatch")
                require(data["outcome"]["validation"] == {"passed": True, "method": "repository_score_recompute"}, "invalid score validation marker")
                expected_task = _task_metadata(vars(native), repo)
                require(all(data["task"].get(key) == value for key, value in expected_task.items()), "trace task/data provenance mismatch")
                require(data["run"]["seed"] == native.seed and data["run"]["model"]["id"] == native.model_id, "trace model/seed mismatch")
                namespace = sweep._namespace_for_job(args, native, None)
                expected_temperature = manifest["settings"]["temperature_tuning" if native.scenario == "tuning" else "temperature_eval"]
                require(namespace.temperature == job["temperature"] == expected_temperature, "ExpGym command/settings temperature differs")
                require(data["run"]["backend"]["name"] == args.backend, "trace backend mismatch")
                from expgym.llm_clients import _normalize_chat_completions_url
                expected_url = _normalize_chat_completions_url(args.base_url) if args.backend != "fake" else args.base_url
                require(data["run"]["backend"]["base_url"] == expected_url, "trace base URL mismatch")
                if args.backend != "fake":
                    require(data["run"]["generation"].get("temperature") == namespace.temperature, "trace generation temperature mismatch")
                    require(data["run"]["generation"].get("seed") == namespace.seed, "trace generation seed mismatch")
                    for field in ("max_tokens", "chat_template_kwargs"):
                        expected = getattr(namespace, field, None)
                        if field == "chat_template_kwargs":
                            expected = expected or {}
                        require(data["run"]["generation"].get(field) == expected, "trace generation %s mismatch" % field)
                require(data["task"]["limits"]["max_steps"] == args.max_steps and data["task"]["limits"]["max_evaluations"] == args.max_evals, "trace horizon mismatch")
                require(1 <= len(data["llm_calls"]) <= args.max_steps + 1, "trace logical call count violates horizon")
                require(len(data["tool_calls"]) <= args.max_evals, "trace evaluation count violates limit")
                require(data["run"].get("prompt_cache") == sweep._prompt_cache_config(args, native), "trace prompt cache config mismatch")
                require(finite(data["timing"]["wall_time_seconds"]), "trace wall time is missing/nonfinite")
                c_base = sweep.resolve_base_cost(native.scenario, namespace)
                if native.scenario == "tuning" and native.tuning_task.startswith("hpobench:"):
                    oracle_task = strict_json(repo / "data/hpo_tuning/oracle3.json")["tasks"][native.tuning_task]
                    require(c_base == oracle_task["best_cost"], "tuning base cost did not use the oracle")
                time_budget, modes = sweep.resolve_cost_regime(namespace, c_base)
                require(data["task"]["budget"] == {"regime": native.cost_regime, "mode": modes[0],
                                                  "base_cost_seconds": c_base, "limit_seconds": time_budget},
                        "trace resolved budget mismatch")
                tools = sweep._resolve_tools(sweep._SCENARIOS[native.scenario], namespace)
                evaluator = sweep._resolve_answer_evaluator(sweep._SCENARIOS[native.scenario], namespace)
                result = trace_to_result(data)
                check = sweep._score_check(result, tools, evaluator)
                require(check.get("ok") is True, "independent score recomputation failed: %s" % check)
                row.update(raw_metrics(result, data))
                row.update(score_recompute=check, model_id=native.model_id)
            else:
                strategy = output["strategy"]
                if args.scenario == "tuning" and args.tuning_task.startswith("hpobench:"):
                    oracle_task = strict_json(repo / "data/hpo_tuning/oracle3.json")["tasks"][args.tuning_task]
                    require(c_base == oracle_task["best_cost"], "PoolAct tuning base cost did not use the oracle")
                require(path == Path(job["output_dir"]) / strategy / "result.json", "unexpected PoolAct path")
                require(data.get("config") == config, "PoolAct config mismatch")
                require(data.get("implementation_sha256") == {"source_tree": current_source}, "PoolAct source mismatch")
                require(data.get("strategy") == strategy and data.get("agents") == args.agents, "PoolAct strategy/agents mismatch")
                agents = data.get("agent_results")
                require(isinstance(agents, list) and len(agents) == args.agents, "embedded agents missing")
                require(all(isinstance(a, dict) for a in agents), "bad agent shape")
                require({a.get("agent_id") for a in agents} == set(range(args.agents)), "agent IDs are not complete and unique")
                expected_paths = [str(path.parent / "agents" / ("agent_%d.json" % i)) for i in range(args.agents)]
                require(sorted(expected_paths) == sorted(output["agent_paths"]), "manifest agent paths mismatch")
                by_id = {a["agent_id"]: a for a in agents}
                for agent_id, agent_path in enumerate(expected_paths):
                    agent = by_id[agent_id]
                    agent_row = {"agent_id": agent_id, "path": agent_path, "status": "invalid"}
                    row["agent_records"].append(agent_row)
                    require(strict_json(agent_path) == agent, "per-agent file differs from embedded agent %d" % agent_id)
                    require(agent.get("seed") == args.seed + agent_id and agent.get("strategy") == strategy, "agent seed/strategy mismatch")
                    require((agent.get("score_check") or {}).get("ok") is True, "agent score marker failed")
                    require(all(key in agent for key in ("messages", "tool_records", "eval_records", "answer", "answer_perf", "answer_metrics", "api_calls", "wall_time_seconds")), "agent trace fields missing")
                    require(finite(agent["answer_perf"]), "agent score nonfinite")
                    require(isinstance(agent["api_calls"], int) and not isinstance(agent["api_calls"], bool)
                            and 1 <= agent["api_calls"] <= args.max_steps + 1, "agent API count violates horizon")
                    require(isinstance(agent["tool_records"], list)
                            and agent.get("evaluations") == len(agent["tool_records"])
                            and len(agent["tool_records"]) <= args.max_evals, "agent evaluation counter mismatch")
                    for field in ("wall_time_seconds", "total_overhead", "llm_time"):
                        require(finite(agent.get(field)) and agent[field] >= 0, "invalid agent time/cost: " + field)
                    namespace = pool._agent_namespace(args, strategy, agent_id, None)
                    tools = pool._resolve_tools(pool._SCENARIOS[args.scenario], namespace)
                    evaluator = pool._resolve_answer_evaluator(pool._SCENARIOS[args.scenario], namespace)
                    check = sweep._score_check(agent, tools, evaluator)
                    require(check.get("ok") is True, "agent %d recomputation failed: %s" % (agent_id, check))
                    agent_row.update(raw_metrics(agent))
                    agent_row.update(status="valid", sha256=sha256(agent_path), seed=agent["seed"], score_recompute=check)
                state = data.get("shared_state")
                if strategy == "poolact":
                    require(isinstance(state, dict) and isinstance(state.get("graph"), dict)
                            and state["graph"].get("pending_claims") == 0,
                            "PoolAct requires shared_state.graph.pending_claims=0")
                if isinstance(state, dict) and "pending_claims" in state:
                    require(state["pending_claims"] == 0, "shared pending_claims must be zero")
                evaluator = pool._resolve_answer_evaluator(pool._SCENARIOS[args.scenario], args)
                compatible = pool._load_resumable_result(path, item_output_dir=Path(job["output_dir"]), strategy=strategy,
                                                        config=config, implementation={"source_tree": current_source},
                                                        agents=args.agents, answer_evaluator=evaluator)
                require(compatible is not None, "repository resume/aggregate recomputation rejected PoolAct result")
                summary_path = Path(job["summary_path"])
                summary = strict_json(summary_path)
                require(summary.get("config") == config and summary.get("implementation_sha256") == data["implementation_sha256"], "item summary config/source mismatch")
                require(set(summary.get("strategies", {})) == set(args.strategies), "item summary strategy set mismatch")
                require(summary["strategies"][strategy] == data["aggregate"], "item summary aggregate mismatch")
                aggregate = data["aggregate"]
                row.update(raw_metrics(aggregate))
                row.update(model_id=args.model, aggregate_method=aggregate["method"],
                           individual_perfs=aggregate["individual_perfs"], shared_state=state,
                           mean_individual_perf=mean(aggregate["individual_perfs"]),
                           summary_path=str(summary_path), summary_sha256=sha256(summary_path))
            require(finite(row.get("answer_perf")), "artifact has no finite final score")
            row["status"] = "valid"
        except FileNotFoundError as exc:
            row.update(status="missing", issues=["required component missing: %s" % exc])
        except Exception as exc:
            row.update(status="invalid", issues=["%s: %s" % (type(exc).__name__, exc)])
    return outputs


def receipt_issues(job):
    """Require successful process receipts; model performance is not a status."""
    path = job.get("status_path")
    if not path or not Path(path).is_file():
        return ["successful subprocess receipt missing"], None
    metadata = None
    try:
        receipt = strict_json(path)
        log_path = Path(job["stdout_log"])
        metadata = {"path": str(path), "sha256": sha256(path), "receipt": receipt,
                    "stdout_log": str(log_path),
                    "stdout_sha256": sha256(log_path) if log_path.is_file() else None}
        require(receipt.get("returncode") == 0, "subprocess returncode is not zero")
        require(receipt.get("status") in ("completed", "skipped", "success", "succeeded"), "subprocess receipt is not complete")
        require(log_path.is_file(), "subprocess stdout log missing")
        require(receipt.get("job_id") == job["id"], "subprocess receipt job ID differs")
        log_bytes = log_path.read_bytes()
        start, end = receipt.get("stdout_start_byte"), receipt.get("stdout_end_byte")
        require(isinstance(start, int) and isinstance(end, int) and 0 <= start <= end <= len(log_bytes),
                "subprocess stdout byte range missing/invalid")
        log = log_bytes[start:end].decode("utf-8", errors="replace")
        if job["system"] == "expgym":
            markers = sum("wrote " in line and "score_check=ok" in line for line in log.splitlines())
            markers += sum("skip verified " in line for line in log.splitlines())
            require(markers >= len(job["expected_outputs"]), "ExpGym stdout lacks score_check/verified-resume markers for every trace")
        else:
            require(log.count("POOLACT RESULT |") + log.count("[resume] item=") >= len(job["expected_outputs"]), "PoolAct stdout lacks per-strategy completion markers")
        return [], metadata
    except Exception as exc:
        return ["receipt: %s" % exc], metadata


def scoring_environment(repo):
    environment = os.environ.copy()
    environment.update(PYTHONNOUSERSITE="1", PYTHONPATH=str(repo),
                       HPOBENCH_ROOT=str(repo / "data/hpo_tuning/HPOBench"),
                       XDG_DATA_HOME=str(repo / "data/hpo_tuning/hpobench_data"),
                       XDG_CACHE_HOME=str(repo / "data/hpo_tuning/hpobench_cache"),
                       XDG_CONFIG_HOME=str(Path(__file__).resolve().parents[1] / "data_runtime/hpobench_config"),
                       OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    for key in ("EXPGYM_MAX_TOKENS", "EXPGYM_CHAT_TEMPLATE_KWARGS", "EXPGYM_PROMPT_CACHE_KEY"):
        environment.pop(key, None)
    return environment


def audit_promotion(manifest, records):
    path = manifest.get("promotion_map")
    if not path:
        return None, []
    try:
        plan = strict_json(path)
        require(plan.get("operation") == "audited_pilot_to_full", "unsupported promotion operation")
        require(plan.get("status") in ("copied_pending_full_runner_resume", "completed"),
                "promotion copy is not complete")
        require(plan.get("source_tree_sha256") == manifest["source_tree_sha256"], "promotion source differs")
        known_jobs = {job["id"] for job in manifest["jobs"]}
        promoted = plan["jobs"]
        require(len({job["job_id"] for job in promoted}) == len(promoted), "duplicate promoted job")
        for job in promoted:
            require(job["job_id"] in known_jobs, "promotion refers to a job outside manifest")
            require(sha256(job["preserved_status_path"]) == job["source_status_sha256"], "preserved pilot receipt changed")
            require(sha256(job["preserved_stdout_log"]) == job["source_stdout_sha256"], "preserved pilot stdout changed")
            receipt = strict_json(job["preserved_status_path"])
            require(receipt == job["source_execution"], "promotion execution copy differs from receipt")
            require(receipt.get("returncode") == 0 and receipt.get("status") == "completed", "promoted source execution failed")
        mapped = {entry["target"]: entry["sha256"] for entry in plan["files"]}
        promoted_ids = {job["job_id"] for job in promoted}
        for record in records:
            if record["job_id"] in promoted_ids:
                record["promotion_source"] = path
                record["artifact_reused_from_pilot"] = record.get("sha256") == mapped.get(record["path"])
        return {"path": path, "sha256": sha256(path), "plan": plan}, []
    except Exception as exc:
        return {"path": path, "complete": False}, ["promotion provenance: %s" % exc]


def run_audit(manifest_path, legacy_python=None):
    manifest_path = Path(manifest_path).resolve()
    # Preserve the venv interpreter symlink: resolving it selects the bare
    # bootstrap Python and silently loses all installed evaluator packages.
    legacy_python = Path(legacy_python).absolute() if legacy_python else None
    manifest = strict_json(manifest_path)
    counts, manifest_issues = validate_manifest(manifest)
    repo = Path(manifest["repo_root"]).resolve()
    records, receipts = [], []
    previous_cwd = Path.cwd()
    previous_environment = os.environ.copy()
    try:
        os.chdir(str(repo))
        environment = scoring_environment(repo)
        os.environ.clear()
        os.environ.update(environment)
        load_runners(repo)
        from expgym.trace_v2 import source_tree_sha256
        current_source = source_tree_sha256(repo)
        if manifest.get("source_tree_sha256") != current_source:
            manifest_issues.append("manifest source_tree_sha256 differs from current repository")
        for number, job in enumerate(manifest["jobs"], 1):
            if not any(Path(out["path"]).is_file() for out in job["expected_outputs"]):
                rows = [base_record(job, output) for output in job["expected_outputs"]]
                for row in rows:
                    row["issues"] = ["expected artifact missing"]
            elif "paramnet:" in str(job.get("tuning_task")) and legacy_python:
                try:
                    process = subprocess.run([str(legacy_python), str(Path(__file__).resolve()), "--worker"],
                                             input=json.dumps({"job": job, "manifest": {key: value for key, value in manifest.items() if key != "jobs"}}),
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                                             timeout=600, cwd=str(repo), env=environment)
                    require(process.returncode == 0, "legacy scoring process failed: %s" % process.stderr[-3000:])
                    rows = json.loads(process.stdout)
                except Exception as exc:
                    rows = [base_record(job, output) for output in job["expected_outputs"]]
                    for row in rows:
                        row.update(status="invalid", issues=[str(exc)])
            else:
                rows = audit_job(job, manifest)
            problems, receipt = receipt_issues(job)
            if receipt:
                receipts.append({"job_id": job["id"], **receipt})
            for row in rows:
                row["execution_status"] = receipt["receipt"].get("status") if receipt else "receipt_missing"
                row["artifact_integrity_status"] = row["status"]
                if problems:
                    row["issues"].extend(problems)
                    if row["status"] == "valid":
                        row["status"] = "unverified_execution"
            records.extend(rows)
            if number % 25 == 0:
                print("audited %d/%d subprocess jobs" % (number, len(manifest["jobs"])), file=sys.stderr, flush=True)
    finally:
        os.chdir(str(previous_cwd))
        os.environ.clear()
        os.environ.update(previous_environment)
    statuses = collections.Counter(row["status"] for row in records)
    promotion, promotion_issues = audit_promotion(manifest, records)
    manifest_issues.extend(promotion_issues)
    valid_counts = collections.Counter()
    for row in records:
        if row["status"] == "valid":
            valid_counts["expgym_traces" if row["system"] == "expgym" else "poolact_results"] += 1
            if row["system"] == "poolact":
                valid_counts["poolact_agent_traces"] += len(row["agent_records"])
                if row["paper_subset"]:
                    valid_counts["poolact_paper_results"] += 1
                    valid_counts["poolact_paper_agent_traces"] += len(row["agent_records"])
    return {"schema": {"name": "kimi.expgym.audit", "version": 1}, "created_at": utc_now(),
            "auditor_path": str(Path(__file__).resolve()), "auditor_sha256": sha256(__file__),
            "manifest_path": str(manifest_path), "manifest_sha256": sha256(manifest_path),
            "repo_root": str(repo), "stage": manifest.get("stage"), "study_type": manifest.get("study_type"),
            "source_tree_sha256": current_source, "model_id": manifest.get("settings", {}).get("model"),
            "backend": manifest.get("settings", {}).get("backend"),
            "data_provenance": manifest.get("data_provenance", {}),
            "data_verification": "actual dataset_manifest.files sizes and SHA256 plus HPOBench commit/worktree checked before scoring",
            "promotion": promotion,
            "legacy_python": str(legacy_python) if legacy_python else None,
            "complete": not manifest_issues and len(records) > 0 and statuses.get("valid", 0) == len(records),
            "expected_counts": counts, "valid_counts": dict(valid_counts), "statuses": dict(statuses),
            "execution_statuses": dict(collections.Counter(record["receipt"].get("status") for record in receipts)),
            "manifest_issues": manifest_issues, "records": records, "receipts": receipts}


def export_audit(audit, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    write_json(output_dir / "audit.json", audit)
    rows = [{key: value for key, value in row.items() if key != "agent_records"} for row in audit["records"]]
    write_csv(output_dir / "artifact_index.csv", rows)
    write_json(output_dir / "missing.json", [row for row in rows if row["status"] == "missing"])
    write_json(output_dir / "failed.json", [row for row in rows if row["status"] not in ("valid", "missing")])
    write_json(output_dir / "execution_failures.json", [record for record in audit["receipts"]
                                                       if record["receipt"].get("returncode") != 0])
    checksums = {}
    for row in audit["records"]:
        for artifact in [row] + row["agent_records"]:
            if artifact.get("sha256"):
                checksums[artifact["path"]] = artifact["sha256"]
        if row.get("summary_sha256"):
            checksums[row["summary_path"]] = row["summary_sha256"]
    write_json(output_dir / "raw_checksums.json", checksums)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--legacy-python", type=Path, help="Python 3.7 interpreter for ParamNet offline score recomputation")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        payload = json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):
            rows = audit_job(payload["job"], payload["manifest"])
        print(json.dumps(rows, ensure_ascii=False, allow_nan=False))
        return 0
    parser.error("--manifest is required") if not args.manifest else None
    output = args.output_dir or args.manifest.resolve().parent / ("audit_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
    require(not output.exists(), "audit output directory already exists; use a new path")
    audit = run_audit(args.manifest, args.legacy_python)
    export_audit(audit, output)
    print(json.dumps({"complete": audit["complete"], "expected": audit["expected_counts"],
                      "valid": audit["valid_counts"], "statuses": audit["statuses"], "output_dir": str(output)}, ensure_ascii=False))
    return 0 if audit["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
