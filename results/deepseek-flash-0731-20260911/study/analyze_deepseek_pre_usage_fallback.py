#!/usr/bin/env python3
"""Offline DeepSeek Flash export; no runners, scorers, models or archive restoration.

CLI requires SHA-bound --plan, --coverage, --reference-manifest, --oracle and
--states (each with --NAME-sha256), plus a fresh --output-dir. No default paths.
State input schema deepseek-flash.analysis-states.v1:
  {"plan_sha256": ..., "roots": [{"path": ABS_QUEUE_ROOT,
    "sessions": [SESSION_BASENAME, ...]}],
   "unreceipted_artifacts": {ABS_INVOCATION_ROOT: {RELATIVE_PATH: {bytes,sha256}}},
   "effective_attempt": {JOB_ID: {"state_root": ABS_QUEUE_ROOT,
     "authorization": {"path": ABS_FILE, "bytes": INT, "sha256": SHA}}}}
The last mapping is required only for repeated begun attempts. Each declared
session needs its closed summary. Actual controller locks are held while reading.
All supplied epochs' attempts remain in costs; only the selected slot is scored.
This adapter emits tables/indexes, not a scientific conclusion or publication.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
import csv
import fcntl
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import stat
import sys

from analyze_deepseek_metrics import aggregate, collapse

SCHEMA = "deepseek-flash.analysis.v1"
IDENTITY = ("model", "system", "scenario", "item", "family", "regime", "strategy", "N", "outerrep", "order", "seed")
QUALITY = {
    ("expgym", "restricted_search"): ("f1",),
    ("expgym", "evidence_audit"): ("evidence_acc", "label_acc"),
    ("expgym", "tuning"): ("gap", "raw_perf"),
    ("poolact", "restricted_search"): ("f1_mi", "f1_mv"),
    ("poolact", "evidence_audit"): ("evidence_acc_mi", "evidence_acc_mv", "label_acc_mi", "label_acc_mv"),
    ("poolact", "tuning"): ("gap_mi", "gap_bon", "raw_perf_mi", "raw_perf_bon"),
}
RESOURCE = ("input_tokens", "output_tokens", "feedback_attempts", "feedback_visible",
            "duplicate_action_attempts", "feedback_cost_seconds", "wall_time_seconds",
            "protocol_failure_rate")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha(canonical(value).encode())


def read_json_bytes(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def total(values):
    return sum(values) if all(v is not None for v in values) else None


def mean(values):
    return total(values) / len(values) if values and all(v is not None for v in values) else None


def pin_ok(pin):
    return (type(pin) is dict and set(pin) == {"bytes", "sha256"}
            and type(pin["bytes"]) is int and pin["bytes"] >= 0
            and isinstance(pin["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]))


def safe_relative(root, name):
    relative = Path(name)
    require(isinstance(name, str) and name and not relative.is_absolute()
            and ".." not in relative.parts, "unsafe relative artifact path")
    return root / relative


class Inputs:
    def __init__(self):
        self.files = {}
        self.directories = {}

    def _directory(self, path):
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode), "non-directory/symlink input parent")
        identity = (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))
        name = str(path)
        require(self.directories.setdefault(name, identity) == identity, "input parent changed during analysis")

    def _parents(self, path):
        # Cache only until finish's complete ancestor-identity check. This is
        # a cooperative stability guard, not an adversarial symlink-safe open.
        unchecked = []
        for parent in path.parents:
            if str(parent) in self.directories:
                break  # Its ancestors were checked together on first use.
            unchecked.append(parent)
        for parent in reversed(unchecked):
            self._directory(parent)

    def register(self, path, role, pin=None):
        path = Path(path).absolute()
        self._parents(path)
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode), "nonregular/symlink input")
        signature = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        name = str(path)
        entry = self.files.setdefault(name, {"path": name, "roles": [], "signature": signature})
        require(entry["signature"] == signature, "input changed during analysis")
        if role not in entry["roles"]:
            entry["roles"].append(role)
        if pin is not None:
            require(pin_ok(pin) and pin["bytes"] == info.st_size, "invalid/mismatched input pin")
            require("sha256" not in entry or entry["sha256"] == pin["sha256"], "conflicting input pin")
            entry.update(pin)
            entry.setdefault("evidence", "inherited_inventory_pin_size_checked")
        return entry

    def read(self, path, role, expected_sha=None, pin=None):
        entry = self.register(path, role, pin)
        raw = Path(path).read_bytes()
        checksum = sha(raw)
        require(expected_sha is None or checksum == expected_sha, "input SHA mismatch")
        require("sha256" not in entry or checksum == entry["sha256"], "content differs from inventory")
        entry.update(bytes=len(raw), sha256=checksum, evidence="content_SHA256_verified")
        self.register(path, role)
        return raw

    def json(self, path, role, expected_sha=None, pin=None):
        return read_json_bytes(self.read(path, role, expected_sha, pin))

    def finish(self):
        # Content used for calculations was SHA-checked at read time. This final
        # stat check detects ordinary concurrent changes, not adversarial writes
        # hidden by filesystem timestamp/attribute caching.
        for name, entry in list(self.files.items()):
            self.register(name, entry["roles"][0])
            require("sha256" in entry, "unidentified input")
        # Directory identity, unlike mtime, changes when a cached parent is
        # replaced. Recheck each unique ancestor once, not once per artifact.
        for name in self.directories:
            self._directory(Path(name))
        return [{key: value for key, value in entry.items() if key != "signature"}
                for _, entry in sorted(self.files.items())]


def metadata(plan, coverage, reference):
    """Bind actual queue selections to the already fixed scientific catalogue."""
    require(plan.get("schema") == "expgym.study-queue-plan.v1", "wrong queue schema")
    require(coverage.get("schema_version") == "deepseek-flash-fixed-matrix-coverage-v1", "wrong coverage schema")
    require(not coverage.get("deployment_pending") and coverage.get("full_canonical_identity_matches") is True,
            "draft/unvalidated coverage is not a formal input")
    jobs = plan["jobs"]
    require(len(jobs) == coverage["queue_jobs"] == coverage["logical_outcomes"] == 783,
            "formal plan must have 783 execution slots; smoke is separate")
    catalog = {}
    for row in reference["logical_rows"]:
        key = (row["system"], row["scenario"], row["regime"], row["strategy"], row["outerrep"], str(row["order"]),
               canonical(row["selector"]))
        require(key not in catalog, "duplicate reference scientific slot")
        catalog[key] = row
    require(len(catalog) == 783, "wrong reference matrix")
    output, seen, canonical_rows = {}, set(), []
    for job in jobs:
        identity, args, selection = job["identity"], job["args"], job["selection"]
        require(job["job_id"] == "job_" + digest(identity) and job["job_id"] not in output, "job identity/uniqueness mismatch")
        require(identity["study_id"] == plan["study_id"] and identity["source_tree_sha256"] == plan["source_tree_sha256"]
                and identity["selection"] == selection and identity["runner"] == job["runner"], "plan identity mismatch")
        system = job["runner"]
        source = selection if system == "expgym" else args
        scenario, regime = source["scenario"], source["cost_regime"]
        n = 1 if system == "expgym" else args["agents"]
        seed = selection["seed"] if system == "expgym" else args["seed"] + selection["repeat_index"] * n
        require(type(seed) is int and n == (1 if system == "expgym" else 4), "invalid seed/agent count")
        outer = {2200: 0, 2204: 1, 2208: 2}.get(seed) if scenario == "tuning" else 0
        require(outer is not None, "unregistered tuning seed block")
        order = selection["rep"] if system == "expgym" and scenario == "evidence_audit" else "default" if scenario == "evidence_audit" else "none"
        strategy = "single" if system == "expgym" else selection["strategy"]
        candidates = []
        for key, row in catalog.items():
            if key[:6] != (system, scenario, regime, strategy, outer, str(order)):
                continue
            selector = row["selector"]
            observed = {field: (selection["question_index"] if field == "question_index" else source.get(field))
                        for field in selector if field in {"tuning_task", "data_source", "question_index", "cc_split"}}
            if all(observed[field] == selector[field] for field in observed):
                candidates.append((key, row))
        require(len(candidates) == 1, "queue selection outside reference matrix")
        key, row = candidates[0]
        require(key not in seen, "duplicate scientific slot across queue jobs")
        seen.add(key)
        require(row["sampling_seed_labels"] == [seed + i for i in range(n)], "agent seed block differs")
        require(selection.get("hypothesis_order") == row["hypothesis_order"], "Audit hypothesis order differs")
        model = selection["model_id"] if system == "expgym" else args["model"]
        require(model == coverage["model"], "model differs from coverage")
        family = row["selector"].get("question_family", row["selector"].get("family", "evidence_audit"))
        output[job["job_id"]] = dict(zip(IDENTITY, (model, system, scenario, row["item"], family, regime, strategy, n, outer, order, seed)))
        canonical_rows.append(canonical({field: row[field] for field in
            ("system", "scenario", "item", "selector", "regime", "strategy", "outerrep", "order", "hypothesis_order", "sampling_seed_labels")}))
    require(seen == set(catalog) and sum(m["N"] for m in output.values()) == coverage["agent_traces"] == 1881,
            "reference Cartesian coverage mismatch")
    require(sha(canonical(sorted(canonical_rows)).encode()) == coverage["canonical_identity_sha256"], "canonical scientific identity hash differs")
    return output


def planned_result(job, root):
    args, s = job["args"], job["selection"]
    relative_root = Path("result")
    if job["runner"] == "poolact":
        if args["repeats"] > 1:
            relative_root /= "repeat_%d" % s["repeat_index"]
        return root / relative_root / s["strategy"] / "result.json"
    clean = lambda v: re.sub(r"[^A-Za-z0-9_.-]+", "_", str(v)).strip("_") or "x"
    if s["scenario"] == "tuning":
        prefix = "tuning_" + clean(s["tuning_task"])
    elif s["scenario"] == "restricted_search":
        prefix = "restricted_search_%s_%s" % (clean(s.get("data_source") or "phantom_seed1"), s["question_index"])
    else:
        prefix = "evidence_audit_%s_%s" % (clean(s.get("cc_split", "cc-large")), s["question_index"])
    return root / relative_root / (s["model_alias"] + "_" + s["cost_regime"]) / "traces-v2" / ("%s_r%s_s%s.json" % (prefix, s["rep"], s["seed"]))


def states(plan, spec, inputs, stack):
    require(spec.get("schema") == "deepseek-flash.analysis-states.v1" and spec.get("roots"), "explicit state roots required")
    jobs = {j["job_id"]: j for j in plan["jobs"]}
    attempts, declared = defaultdict(list), set()
    roots = [str(Path(row["path"]).absolute()) for row in spec["roots"]]
    require(len(roots) == len(set(roots)), "duplicate state root")
    for config, root_name in zip(spec["roots"], roots):
        root = Path(root_name)
        lock_path = root / "controller.lock"
        require(lock_path.is_file() and not lock_path.is_symlink(), "actual queue controller lock missing")
        lock = stack.enter_context(lock_path.open("rb"))
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        definition = inputs.json(root / "definition.json", "queue_definition")
        require(definition.get("schema") == "expgym.queue-definition.v1", "wrong queue definition")
        by_id = {r["id"]: r for r in definition["jobs"]}
        require(len(by_id) == len(definition["jobs"]), "duplicate definition job")
        for job_id, row in by_id.items():
            require(job_id in jobs and row["identity"] == jobs[job_id]["identity"], "state identity outside plan")
            declared.add(job_id)
        require(type(config.get("sessions")) is list and len(config["sessions"]) == len(set(config["sessions"])), "explicit unique sessions required")
        actual_sessions = {p.name for p in (root / "sessions").iterdir() if p.is_dir()}
        require(actual_sessions == set(config["sessions"]), "state input omitted or added a queue session")
        reports = defaultdict(list)
        for session_name in config["sessions"]:
            require(isinstance(session_name, str) and re.fullmatch(r"[A-Za-z0-9_-]+", session_name), "unsafe session name")
            session = root / "sessions" / session_name
            summary = inputs.json(session / "summary.json", "closed_queue_session")
            require(summary.get("schema") == "expgym.study-queue-summary.v1"
                    and summary["planned"] == len(by_id) and summary["finished"] == len(summary["reports"]), "unclosed/inconsistent session")
            reported = [r["job_id"] for r in summary["reports"]]
            unstarted = summary.get("unstarted")
            require(type(unstarted) is list and len(reported) == len(set(reported))
                    and len(unstarted) == len(set(unstarted)) and not set(reported) & set(unstarted)
                    and set(reported) | set(unstarted) == set(by_id), "incomplete/duplicated closed session partition")
            for report in summary["reports"]:
                require(report["job_id"] in by_id, "session report outside definition")
                reports[report["job_id"]].append(report)
            # Retain the event input, but do not mislabel its envelope as pool wall.
            events = [read_json_bytes(line) for line in inputs.read(session / "events.jsonl", "queue_events").splitlines() if line.strip()]
            require(events and events[-1].get("event") == "drained"
                    and events[-1].get("active") == 0 and events[-1].get("unstarted") == len(unstarted),
                    "session missing final natural drain")
        for job_id, row in by_id.items():
            directory = root / "jobs" / job_id
            begun = inputs.json(directory / "started.json", "queue_started") if (directory / "started.json").exists() else None
            receipt = inputs.json(directory / "completion.json", "queue_completion") if (directory / "completion.json").exists() else None
            for value in (begun, receipt):
                require(value is None or value.get("identity_sha256") == digest(jobs[job_id]["identity"]), "state receipt identity mismatch")
            require(not receipt or begun, "completion without start")
            if receipt:
                require(type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0 and receipt.get("artifacts"), "invalid completion receipt")
            artifact_root = Path(row["output"]).absolute()
            attempts[job_id].append({"state_root": root_name, "artifact_root": artifact_root,
                                    "started": begun, "receipt": receipt, "reports": reports[job_id]})
    require(declared == set(jobs), "state definitions omit planned jobs")
    effective = spec.get("effective_attempt", {})
    require(set(effective) <= set(jobs), "recovery mapping outside plan")
    for job_id, values in attempts.items():
        begun = [row for row in values if row["started"]]
        require(len({str(row["artifact_root"]) for row in begun}) == len(begun), "multiple executions reused mutable output root")
        chosen = effective.get(job_id)
        require(len(begun) <= 1 or chosen is not None, "multiple begun attempts need explicit authorized winner")
        if chosen:
            authorization = chosen["authorization"]
            inputs.read(authorization["path"], "recovery_authorization", pin={k: authorization[k] for k in ("bytes", "sha256")})
            selected = [row for row in begun if row["state_root"] == str(Path(chosen["state_root"]).absolute())]
            require(len(selected) == 1, "effective attempt must select exactly one begun slot")
        else:
            selected = begun or values[:1]
        default_root = Path(jobs[job_id]["args"]["output_dir"]).absolute().parent
        require(selected[0]["artifact_root"] == default_root or chosen is not None,
                "relocated/recovered effective output requires explicit authorization")
        for row in values:
            row["effective"] = row is selected[0]
    return attempts


def chat_usage(record, job_id, effective, path):
    require(record.get("schema_version") == "expgym.api_attempt.v1" and record.get("run_id") == job_id, "attempt schema/owner mismatch")
    require(record.get("state") in {"success", "error", "malformed_response", "in_progress"}, "unknown attempt state")
    require((record.get("context") or {}).get("api_protocol", "chat") == "chat", "only frozen Chat transport supported")
    request, response = record.get("request_payload") or {}, record.get("response_json") or {}
    response = response if type(response) is dict else {}
    usage = response.get("usage") or {}
    require(type(usage) is dict, "malformed usage")
    def count(container, key):
        value = container.get(key)
        require(value is None or type(value) is int and value >= 0, "invalid token count")
        return value
    incoming, outgoing = count(usage, "prompt_tokens"), count(usage, "completion_tokens")
    details = usage.get("completion_tokens_details") or {}
    require(type(details) is dict, "invalid completion details")
    reasoning = count(details, "reasoning_tokens")
    require(reasoning is None or outgoing is None or reasoning <= outgoing, "reasoning exceeds inclusive output")
    unfinished = record["state"] == "in_progress"
    if unfinished:
        incoming = outgoing = reasoning = None  # Durable crash marker, not a finished usage report.
    choices = response.get("choices") or []
    return {"execution_id": job_id, "effective_slot": effective, "artifact": str(path),
            "request_id": record.get("request_id"), "client_id": record.get("client_id"),
            "generation_id": record.get("generation_id"), "attempt": record.get("attempt"),
            "state": record.get("state"), "http_status": record.get("http_status"),
            "input_tokens": incoming, "output_tokens": outgoing,
            "reasoning_tokens_included_in_output": reasoning,
            "total_tokens": incoming + outgoing if incoming is not None and outgoing is not None else None,
            "request_wall_seconds": None if unfinished else number(record.get("wall_time_seconds")),
            "finish_reasons": [c.get("finish_reason") for c in choices if type(c) is dict],
            "effective_request_parameters": {k: request[k] for k in ("model", "temperature", "top_p", "top_k", "seed", "max_tokens", "reasoning_effort", "chat_template_kwargs", "tool_choice", "prompt_cache_key", "cache_salt") if k in request}}


def agent_projection(payload, trace=False):
    if not trace:
        return payload
    outcome, score = payload["outcome"], payload["outcome"]["score"]
    metrics = score.get("metrics")
    return {**outcome, "answer_perf": metrics.get(score["primary_metric"]) if metrics is not None else score.get("value"),
            "answer_metrics": metrics, "score_check": {"ok": outcome["validation"]["passed"]},
            "total_overhead": payload["timing"].get("total_simulated_cost_seconds"),
            "wall_time_seconds": payload["timing"].get("wall_time_seconds"),
            "evaluations": len(payload["tool_calls"]), "api_calls": len(payload["llm_calls"]),
            "tool_records": [(t["name"], t.get("raw_arguments", t["arguments"])) for t in payload["tool_calls"]],
            "feedback_visible": sum(t["visible_to_model"] for t in payload["tool_calls"]),
            "expected_request_attempts": outcome.get("http_request_attempts"),
            "request_ids": [a["request_id"] for c in payload["llm_calls"] for a in c.get("attempt_usage", [])]}


def score_values(agent, scenario, oracle):
    value = number(agent.get("answer_perf"))
    require(value is None or 0 <= value <= 1, "score outside fraction range")
    if scenario == "tuning":
        span = oracle["best_perf"] - oracle["mean_perf"]
        require(span > 0, "invalid oracle span")
        return {"gap": max(0.0, 100 * (value - oracle["mean_perf"]) / span) if value is not None else None,
                "raw_perf": value}
    if scenario == "restricted_search":
        return {"f1": value}
    metrics = agent.get("answer_metrics") or {}
    result = {key: number(metrics.get(key)) for key in ("evidence_acc", "label_acc")}
    require(all(v is None or 0 <= v <= 1 for v in result.values()), "Audit score outside fraction range")
    return result


def project(meta, agents, voted, accepted, oracle, attempts, budget=None):
    """Pure numeric projection. Accepted means inherited queue validation only."""
    n, scenario = meta["N"], meta["scenario"]
    require(len(agents) == n, "explicit expected agent slots required")
    per_agent, terminals = [], []
    for agent_id, agent in enumerate(agents):
        known = accepted and agent is not None and (agent.get("score_check") or {}).get("ok") is True
        names = ("gap", "raw_perf") if scenario == "tuning" else ("f1",) if scenario == "restricted_search" else ("evidence_acc", "label_acc")
        values = score_values(agent or {}, scenario, oracle) if known else {name: None for name in names}
        if accepted:
            status = (agent or {}).get("terminal_status") or {}
            require(status.get("execution_complete") is True and type(status.get("score_complete")) is bool
                    and status["score_complete"] == known, "agent score/terminal status mismatch")
            require(not known or all(v is not None for v in values.values()), "claimed complete score has missing metric")
            if not known:
                require(scenario == "tuning" and agent.get("answer") is None and agent.get("answer_perf") is None
                        and agent.get("score_status") == "unscorable_missing_configuration", "unqualified unknown score")
        per_agent.append(values)
        status = (agent or {}).get("terminal_status") or {}
        terminals.append({**meta, "agent_id": agent_id, "execution_complete": accepted,
                          "score_complete": known, "raw_answer": (agent or {}).get("answer"),
                          "raw_answer_perf": (agent or {}).get("answer_perf"), "terminal_status": status or None,
                          **{key: (agent or {}).get(key) for key in ("score_status", "missing_final_policy", "terminal_origin", "answer_score_source")},
                          "agent_wall_seconds": number((agent or {}).get("wall_time_seconds"))})
    values, subsets = {}, {}
    voted_values = None
    if meta["system"] == "poolact" and accepted and all(all(v is not None for v in a.values()) for a in per_agent):
        voted_values = score_values(voted or {}, scenario, oracle)
        require(all(v is not None for v in voted_values.values()), "claimed complete pool aggregate has missing metric")
    for metric in per_agent[0]:
        all_values = [row[metric] for row in per_agent]
        known_values = [v for v in all_values if v is not None]
        key = metric if meta["system"] == "expgym" else metric + "_mi"
        values[key] = mean(all_values)
        subsets[key] = sum(known_values) / len(known_values) if known_values else None
        if meta["system"] == "poolact":
            aggregate_key = metric + ("_bon" if scenario == "tuning" else "_mv")
            values[aggregate_key] = voted_values[metric] if voted_values is not None else None
            subsets[aggregate_key] = max(known_values) if known_values and scenario == "tuning" else None
    resources = {key: None for key in RESOURCE}
    selected_attempts = [row for row in attempts if row["effective_slot"]]
    if accepted:
        resources.update(input_tokens=total([a["input_tokens"] for a in selected_attempts]),
                         output_tokens=total([a["output_tokens"] for a in selected_attempts]))
        resources["feedback_cost_seconds"] = total([number(a.get("total_overhead")) for a in agents])
        resources["feedback_attempts"] = total([number(a.get("evaluations")) for a in agents])
        actions = [(a[0], canonical(a[1])) for agent in agents for a in agent.get("tool_records", [])]
        if resources["feedback_attempts"] == len(actions):
            resources["duplicate_action_attempts"] = len(actions) - len(set(actions))
        resources["feedback_visible"] = total([number(a.get("feedback_visible")) for a in agents])
        if not actions and resources["feedback_attempts"] == 0:
            resources["feedback_visible"] = 0
        calls = total([number(a.get("api_calls")) for a in agents])
        failures = [len(a["protocol_failures"]) if type(a.get("protocol_failures")) is list else None for a in agents]
        resources["protocol_failure_rate"] = total(failures) / calls if calls and total(failures) is not None else None
        if meta["system"] == "expgym":
            resources["wall_time_seconds"] = number(agents[0].get("wall_time_seconds"))
    values.update(resources)
    if meta["regime"] != "cost_free":
        cost = resources["feedback_cost_seconds"]
        values["budget_utilization"] = cost / (n * budget) if cost is not None and number(budget) is not None and budget > 0 else None
    rows = []
    for metric, value in values.items():
        unit = "Gap points" if metric.startswith("gap") else "tokens" if metric in ("input_tokens", "output_tokens") else "seconds" if metric.endswith("seconds") else "count" if metric in RESOURCE and metric != "protocol_failure_rate" else "fraction"
        rows.append({**meta, "metric": metric, "unit": unit, "value": value,
                     "higher_is_better": None if metric in RESOURCE or metric == "budget_utilization" else True,
                     "scope": "planned_analysis_unit; Audit_mean_once; pool_resources_N_sum_except_wall",
                     "known_agent_subset_value": subsets.get(metric),
                     "missing_reason": None if value is not None else "whole_pool_subprocess_wall_not_recorded" if metric == "wall_time_seconds" and n > 1 else "missing_or_unscorable_required_component"})
    return rows, terminals


def collect(job, meta, attempt, inputs, spec, oracle):
    root, receipt = attempt["artifact_root"], attempt["receipt"]
    inventory = receipt["artifacts"] if receipt else spec.get("unreceipted_artifacts", {}).get(str(root), {})
    require(not attempt["started"] or receipt or str(root) in spec.get("unreceipted_artifacts", {}),
            "begun failed attempt needs explicit artifact inventory (including empty)")
    for relative, pin in inventory.items():
        inputs.register(safe_relative(root, relative), "invocation_artifact", pin)
    calls = []
    for relative, pin in sorted(inventory.items()):
        if relative.startswith("api_dump/") and relative.endswith(".json"):
            path = safe_relative(root, relative)
            calls.append(chat_usage(inputs.json(path, "physical_API_attempt", pin=pin), job["job_id"], attempt["effective"], path))
    result_path = planned_result(job, root)
    # Unreceipted output may be truncated or internally inconsistent. Keep its
    # explicit inventory pin, but never parse/promote it into scientific scores.
    data = inputs.json(result_path, "planned_result", pin=inventory[result_path.relative_to(root).as_posix()]) if receipt and result_path.relative_to(root).as_posix() in inventory else None
    require(not receipt or data is not None, "completion missing planned result")
    accepted = receipt is not None and attempt["effective"]
    agents, voted, budget = [None] * meta["N"], None, None
    if data is not None:
        if meta["system"] == "expgym":
            require(data.get("schema") == {"name": "expgym.trace", "version": "2.1.0"}, "wrong trace schema")
            if receipt:
                require(data["provenance"]["repository"]["source_tree_sha256"] == job["identity"]["source_tree_sha256"]
                        and data["run"]["model"]["id"] == meta["model"], "completed trace source/model mismatch")
            agents[0] = agent_projection(data, True)
            budget = data["task"]["budget"].get("limit_seconds")
        else:
            require(data["agents"] == meta["N"] and data["strategy"] == meta["strategy"], "pool topology mismatch")
            if receipt:
                require(data["implementation_sha256"]["source_tree"] == job["identity"]["source_tree_sha256"]
                        and data["config"]["model"] == meta["model"], "completed pool source/model mismatch")
            seen = set()
            for agent in data["agent_results"]:
                index = agent["agent_id"]
                require(type(index) is int and 0 <= index < meta["N"] and index not in seen, "invalid/duplicate pool agent")
                seen.add(index)
                agents[index] = agent
                if receipt:
                    path = result_path.parent / "agents" / ("agent_%d.json" % index)
                    require(inputs.json(path, "pool_agent", pin=inventory[path.relative_to(root).as_posix()]) == agent, "embedded/separate agent mismatch")
            require(not receipt or len(seen) == meta["N"], "completion missing required agent")
            voted = data.get("aggregate")
            budget = data["config"].get("time_budget")
            if receipt:
                complete_score = all((a.get("terminal_status") or {}).get("score_complete") is True for a in agents)
                status = (voted or {}).get("terminal_status") or {}
                require(status.get("execution_complete") is True and status.get("score_complete") is complete_score,
                        "pool aggregate terminal status mismatch")
                if not complete_score:
                    require(all(voted.get(k) is None for k in ("answer", "answer_perf", "answer_metrics")),
                            "unknown full pool improperly uses known subset")
        if receipt:
            for agent in agents:
                require((agent.get("terminal_status") or {}).get("execution_complete") is True, "completed result missing terminal evidence")
            request_ids = []
            for agent in agents:
                request_ids += agent.get("request_ids", [a["request_id"] for c in agent.get("usage_attempts", []) for a in c["attempts"]])
                count = agent.get("expected_request_attempts", agent.get("http_request_attempts"))
                actual = agent.get("request_ids", [a["request_id"] for c in agent.get("usage_attempts", []) for a in c["attempts"]])
                require(type(count) is int and count >= 0 and count == len(actual), "missing/incomplete agent attempt ledger")
            require(len(request_ids) == len(set(request_ids)) and set(request_ids) == {a["request_id"] for a in calls}, "attempt ledger/dump mismatch")
    rows, terminals = project(meta, agents, voted, accepted, oracle, calls, budget)
    return rows, terminals, calls


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: canonical(v) if isinstance(v, (dict, list, tuple)) else v for k, v in row.items()})


def analyze(paths, pins, output_dir):
    output_dir = Path(output_dir).absolute()
    require(not output_dir.exists(), "output must be fresh")
    inputs = Inputs()
    objects = {name: inputs.json(path, name, pins[name]) for name, path in paths.items()}
    plan, coverage, reference, oracle, state_spec = (objects[k] for k in ("plan", "coverage", "reference_manifest", "oracle", "states"))
    require(state_spec["plan_sha256"] == pins["plan"], "state input bound to different plan")
    require(coverage["origin_manifest"]["sha256"] == pins["reference_manifest"], "reference pin differs from coverage")
    require(coverage["required_unchanged_inputs"]["hpo.oracle"]["sha256"] == pins["oracle"], "oracle differs from fixed input")
    meta_by_id = metadata(plan, coverage, reference)
    inputs.read(Path(__file__), "analysis_source")
    inputs.read(Path(__file__).with_name("analyze_deepseek_metrics.py"), "analysis_source")
    metrics, terminals, costs, normalized = [], [], [], []
    with ExitStack() as stack:
        state = states(plan, state_spec, inputs, stack)
        for job in plan["jobs"]:
            meta = {"execution_id": job["job_id"], **meta_by_id[job["job_id"]]}
            for attempt in state[job["job_id"]]:
                rows, raw, calls = collect(job, meta, attempt, inputs, state_spec, oracle["tasks"].get(meta["item"]))
                costs.extend(calls)
                if attempt["effective"]:
                    metrics.extend(rows)
                    terminals.extend(raw)
                    normalized.append({**meta, "execution_complete": bool(attempt["receipt"]),
                                       "state_root": attempt["state_root"], "artifact_root": str(attempt["artifact_root"])})
        ids = [row["request_id"] for row in costs]
        require(all(isinstance(x, str) and x for x in ids) and len(ids) == len(set(ids)), "duplicate/missing physical request identity")
        scientific = collapse(metrics)
        absolute, repeats, contrasts = aggregate(scientific)
        require(len({r["analysis_id"] for r in scientific}) == 705 and len(normalized) == 783 and len(terminals) == 1881,
                "formal analysis unit coverage differs")
        source_index = inputs.finish()
        ledger = {}
        for scope, subset in (("all_physical_attempts", costs), ("effective_slots", [r for r in costs if r["effective_slot"]])):
            ledger[scope] = {name: {"complete_total": total([r[name] for r in subset]),
                                   "known_subset_total": sum(r[name] for r in subset if r[name] is not None),
                                   "known": sum(r[name] is not None for r in subset), "expected": len(subset)}
                             for name in ("input_tokens", "output_tokens", "reasoning_tokens_included_in_output", "total_tokens", "request_wall_seconds")}
        output_dir.mkdir(parents=True)
        tables = {"metrics_execution.csv": metrics, "metrics.csv": scientific, "absolute_settings.csv": absolute,
                  "by_outerseed.csv": repeats, "contrasts.csv": contrasts, "raw_terminals.csv": terminals,
                  "all_attempt_costs.csv": costs, "normalized.csv": normalized}
        for name, rows in tables.items():
            write_csv(output_dir / name, rows)
        documents = {"SOURCE_INDEX.json": {"schema": SCHEMA, "files": source_index}, "COSTS.json": ledger,
                     "INPUTS.json": {"schema": SCHEMA, "input_pins": pins, "python": platform.python_version(),
                                    "execution_slots": 783, "analysis_units": 705, "agent_slots": 1881,
                                    "score_recomputation": False, "model_calls": 0,
                                    "independent_postdraft_review": "not performed by generator",
                                    "archive_content_verification": False,
                                    "limits": ["reasoning included in output", "Pool subprocess wall not recorded; no agent sum/max substitution",
                                               "Audit metrics averaged once, attempts billed per execution", "locks protect declared cooperating queues only; provider quiescence not proven"]}}
        for name, value in documents.items():
            with (output_dir / name).open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return {"schema": SCHEMA, "files": sorted([*tables, *documents]), "execution_slots": len(normalized),
            "analysis_units": len({r["analysis_id"] for r in scientific}), "model_calls": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    names = ("plan", "coverage", "reference_manifest", "oracle", "states")
    for name in names:
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
        parser.add_argument("--" + name.replace("_", "-") + "-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(analyze({name: getattr(args, name) for name in names},
                             {name: getattr(args, name + "_sha256") for name in names}, args.output_dir), sort_keys=True))


if __name__ == "__main__":
    main()
