#!/usr/bin/env python3
"""Re-score every adopted Search/Audit terminal with the versioned protocol.

Two deliberately separate operations are supported: build a small, hash-bound
scoring-input package from privately retained traces, then replay that package
using the actual public parser, scorer and PoolAct aggregator. No API calls,
trace mutations, new observations, or early-stop counterfactuals are performed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import re
import statistics
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import expgym.poolact as pool
import expgym.task_evidence_audit as audit
import expgym.task_restricted_search as search
import expgym.tool_protocol as protocol

BASELINE = "297c3d00a006f33fc5a8ca799ce91d327d92839e"
VERSION = "existing-trace-rescore-v1"
CODE_FILES = ("expgym/tool_protocol.py", "expgym/task_restricted_search.py", "expgym/task_evidence_audit.py", "expgym/poolact.py", "tools/rescore_protocol.py")
START_CODE_SHA = {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in CODE_FILES}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def text_hash(value):
    return sha_bytes(canonical(value).encode())


def csv_read(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def csv_write(path, rows):
    if not rows:
        Path(path).write_text("")
        return
    with Path(path).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def legacy_module(name, relative):
    raw = subprocess.check_output(["git", "-C", str(REPO), "show", f"{BASELINE}:{relative}"])
    module = types.ModuleType(name)
    module.__file__ = str(REPO / relative)
    sys.modules[name] = module
    exec(compile(raw, f"{BASELINE}:{relative}", "exec"), module.__dict__)
    return module, sha_bytes(raw)


OLD_AUDIT, OLD_AUDIT_SHA = legacy_module("_rescore_legacy_audit", "expgym/task_evidence_audit.py")
OLD_POOL, OLD_POOL_SHA = legacy_module("_rescore_legacy_pool", "expgym/poolact.py")
OLD_SEARCH, OLD_SEARCH_SHA = legacy_module("_rescore_legacy_search", "expgym/task_restricted_search.py")
OLD_PROTOCOL, OLD_PROTOCOL_SHA = legacy_module("_rescore_legacy_protocol", "expgym/tool_protocol.py")


def old_parse(raw, allow_unlabelled):
    if OLD_PROTOCOL.extract_text_action(raw) is not None:
        return None
    result = OLD_PROTOCOL.extract_text_answer(raw)
    if result is None and allow_unlabelled:
        result = OLD_PROTOCOL.structured_final_answer(raw)
    if result is None and allow_unlabelled:
        result = OLD_PROTOCOL.unlabelled_final_answer(raw)
    return result


def same(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(same(left[k], right[k]) for k in left)
    if left is None or right is None:
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-12)
    return left == right


def final_message(messages, outcome, n1):
    pointer = outcome.get("answer_message_id") if n1 else None
    candidates = [(i, m) for i, m in enumerate(messages) if m.get("role") == "assistant"]
    if pointer:
        matching = [(i, m) for i, m in candidates if m.get("id") == pointer]
        if len(matching) != 1:
            raise ValueError(f"Invalid answer message pointer {pointer}")
        return *matching[0], "answer_message_id"
    if candidates:
        return *candidates[-1], "last_assistant_terminal"
    return -1, {}, "no_assistant_message"


def finish_reason(call):
    if not isinstance(call, dict):
        return None
    return call.get("finish_reason") or (call.get("response") or {}).get("finish_reason")


def pack_agent(obj, a, row, agent_id):
    n1 = row["system"] == "expgym"
    messages = obj["messages"] if n1 else a["messages"]
    index, message, pointer = final_message(messages, a, n1)
    raw = message.get("content") or ""
    if not isinstance(raw, str):
        raise TypeError("Terminal content must be textual")
    calls = obj.get("llm_calls", []) if n1 else []
    call_by_message = {c.get("output_message_id"): c for c in calls if c.get("output_message_id")}
    final_call = call_by_message.get(message.get("id"), {})
    final_finish = finish_reason(final_call) or message.get("finish_reason")
    # A previously unparsed forced terminal can be recovered only when its
    # canonical call explicitly proves a completed final-only response. Never
    # substitute an arbitrary previous thinking/action turn for an abstention.
    recoverable_missing = bool(n1 and final_call.get("forced") is True and final_finish == "stop"
                               and calls and final_call.get("id") == calls[-1].get("id"))
    eligible = (a.get("answer") is not None or recoverable_missing) and not message.get("tool_calls") and final_finish != "length"
    allow = a.get("tool_protocol", obj.get("run", {}).get("tool_protocol", "native")) == "native" or a.get("answer_source") == "forced_model_answer"
    intermediates = []
    for mid, m in enumerate(messages):
        if mid >= index or m.get("role") != "assistant" or m.get("tool_calls"):
            continue
        text = m.get("content") or ""
        call = call_by_message.get(m.get("id"), {})
        if not isinstance(text, str) or finish_reason(call) == "length":
            continue
        previous = old_parse(text, allow)
        repaired = protocol.parse_final_answer(text, allow_unlabelled=allow)
        if previous != repaired:
            intermediates.append({"message_index": mid, "message_id": m.get("id"), "raw_sha256": text_hash(text), "old_answer_sha256": text_hash(previous), "new_answer_sha256": text_hash(repaired), "old_accepts": previous is not None, "new_accepts": repaired is not None})
    if n1:
        records = [[c["name"], c.get("raw_arguments", canonical(c.get("arguments", {}))), c.get("tool_result")] for c in obj.get("tool_calls", [])]
        # Verification_eff is explicitly historical attempted-feedback semantics.
        # The visible-only variant is exported separately for interpretation.
        visible = [rec for rec, c in zip(records, obj.get("tool_calls", [])) if c.get("visible_to_model")]
        old_metrics = a.get("score", {}).get("metrics")
        old_perf = a.get("score", {}).get("value")
    else:
        records = a.get("tool_records", [])
        visible = None  # Legacy PoolAct does not export per-tool visibility flags.
        old_metrics = a.get("answer_metrics")
        old_perf = a.get("answer_perf")
    return {"agent_id": agent_id, "raw_final_text": raw, "raw_final_sha256": text_hash(raw), "raw_final_chars": len(raw), "final_eligible": eligible,
            "allow_unlabelled": allow, "terminal_message_index": index, "terminal_message_id": message.get("id"),
            "terminal_locator": pointer, "finish_reason": final_finish, "native_tool_calls_present": bool(message.get("tool_calls")),
            "forced_terminal": final_call.get("forced"), "missing_terminal_recovery_proven": recoverable_missing,
            "old_answer": a.get("answer"), "old_scoring_input": a.get("scoring_input", a.get("answer") or ""),
            "old_answer_perf": old_perf, "old_answer_metrics": old_metrics,
            "answer_source": a.get("answer_source"), "termination_reason": a.get("termination_reason"),
            "tool_records": records if row["scenario"] == "evidence_audit" else [],
            "visible_tool_records": visible if row["scenario"] == "evidence_audit" else [],
            "intermediate_parser_differences": intermediates}


def build_inputs(args):
    selections = csv_read(args.source / "SOURCE_SELECTION.csv")
    scalars = {r["slot_id"]: r for r in csv_read(args.source / "slot_scalars.csv")}
    bindings = json.loads((args.source / "INPUTS.json").read_text())
    additions = {r["slot_id"]: r for r in bindings["new_results"]}
    selected = [r for r in selections if r["scenario"] != "tuning"]
    path_rows = [(row, args.delivery / row["historical_trajectory"] if row["historical_trajectory"] else Path(additions[row["slot_id"]]["path"])) for row in selected]
    terminal_evidence = {}
    if args.terminal_evidence:
        evidence = json.loads(args.terminal_evidence.read_text())
        evidence = evidence if isinstance(evidence, list) else evidence.get("records", evidence.get("rows", []))
        terminal_evidence = {(r["slot_id"], int(r["agent_id"])): r for r in evidence}
    # Bind minimal gold to the actual recorded evaluator-input SHA, not a
    # regenerated current dataset. No model-visible contract/corpus is exported.
    qa_cache = {}
    evidence_cache = {}
    for row, path in path_rows:
        if row["scenario"] == "restricted_search" and row["item"].split(":")[0] in qa_cache:
            continue
        if row["scenario"] == "evidence_audit" and evidence_cache:
            continue
        d = json.loads(path.read_text())
        identity = (d.get("run") or d.get("config"))["evaluation_identity"]
        if row["scenario"] == "restricted_search":
            binding = identity["files"]["questions"]
            raw = Path(binding["path"]).read_bytes()
            assert sha_bytes(raw) == binding["sha256"]
            import pyarrow.parquet as pq
            table = pq.read_table(binding["path"], columns=["question", "answer", "type", "difficulty"]).to_pylist()
            table = [r for r in table if r["type"] in search.SWEET_SPOT_TYPES and len(r["answer"]) <= search.MAX_ANSWER_COUNT]
            table.sort(key=lambda r: (r["type"], r["difficulty"]))
            qa_cache[row["item"].split(":")[0]] = (table, binding["sha256"])
        else:
            binding = identity["files"]["evidence"]
            raw = Path(binding["path"]).read_bytes()
            assert sha_bytes(raw) == binding["sha256"]
            evidence_cache.update(data=json.loads(raw), sha256=binding["sha256"])

    def pack(pair):
        row, path = pair
        raw = path.read_bytes()
        assert sha_bytes(raw) == row["result_sha256"], f"Source changed: {row['slot_id']}"
        d = json.loads(raw)
        n1 = row["system"] == "expgym"
        identity = (d.get("run") or d.get("config"))["evaluation_identity"]
        source, item_index = row["item"].split(":")
        if row["scenario"] == "restricted_search":
            table, gold_sha = qa_cache[source]
            assert identity["files"]["questions"]["sha256"] == gold_sha
            gold = {"answers": table[int(item_index)]["answer"], "dataset_sha256": gold_sha}
        else:
            data = evidence_cache["data"]
            gold_sha = evidence_cache["sha256"]
            assert identity["files"]["evidence"]["sha256"] == gold_sha
            gold = {"annotations": data["documents"][int(item_index)]["annotation_sets"][0]["annotations"], "labels": data["labels"], "cc_split": source, "dataset_sha256": gold_sha}
        agents = [pack_agent(d, d["outcome"], row, -1)] if n1 else [pack_agent(d, a, row, a["agent_id"]) for a in d["agent_results"]]
        for agent in agents:
            if agent["old_answer"] is None and not n1:
                evidence = terminal_evidence.get((row["slot_id"], agent["agent_id"]))
                if evidence is None:
                    raise ValueError(f"Missing raw terminal evidence {row['slot_id']}/{agent['agent_id']}")
                if evidence["eligible"]:
                    assert evidence["final_raw_text"] == agent["raw_final_text"]
                agent.update(final_eligible=bool(evidence["eligible"]), finish_reason=evidence["finish_reason"],
                             forced_terminal=evidence["forced"], missing_terminal_recovery_proven=bool(evidence["eligible"]),
                             terminal_raw_source_sha256=evidence["raw_source_sha256"],
                             terminal_raw_source_locator=evidence.get("frozen_archive_member", evidence.get("request_id", "")))
            if not agent["final_eligible"]:
                # Rejected/truncated raw text is unnecessary for scoring and
                # stays in the private source. Its hash and refusal proof remain.
                agent["raw_final_text"] = ""
        return {"schema": VERSION, "slot": scalars[row["slot_id"]], "selection": row,
                "source_locator": row["historical_trajectory"] or f"gemini-main-new-result:{row['new_result_index']}",
                "source_path_private": str(path), "source_sha256": row["result_sha256"],
                "gold": gold, "agents": agents, "old_aggregate": None if n1 else {k: d["aggregate"].get(k) for k in ("answer", "answer_perf", "answer_metrics", "mean_individual_perf")}}

    args.output.mkdir(parents=True, exist_ok=True)
    private = args.output / "private"
    private.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        rows = list(executor.map(pack, path_rows))
    with (private / "source_paths.json").open("w") as handle:
        json.dump({r["slot"]["slot_id"]: r.pop("source_path_private") for r in rows}, handle, indent=2)
    with (args.output / "scoring_inputs.jsonl.gz").open("wb") as raw_out:
        with gzip.GzipFile(fileobj=raw_out, mode="wb", filename="", mtime=0) as handle:
            for row in rows:
                handle.write((canonical(row) + "\n").encode())
    return rows


def audit_evaluator(module, gold):
    # Use the repository's real scorer unchanged, binding only its two dataset
    # accessors to the minimal frozen annotations in this public replay package.
    module._get_doc = lambda index: types.SimpleNamespace(annotations=gold["annotations"])
    module._get_labels = lambda split: {k: v for k, v in gold["labels"].items() if not module.CC_SPLITS.get(split) or k in module.CC_SPLITS[split]}
    return module.build_answer_evaluator(0, gold["cc_split"])


def reason(old, new, raw, scenario, score_changed):
    why = []
    if old != new:
        if new is None:
            labels = re.findall(r"(?im)^\s*(?:\*\*)?(?:Final\s+)?Answer\s*:", raw)
            why.append("two_nonempty_final_directives" if len(labels) > 1 else "ambiguous_or_protocol_text_rejected")
        elif isinstance(old, str) and old.startswith("**"):
            why.append("closing_markdown_label_removed")
        elif old == raw:
            why.append("explicit_terminal_label_selected_from_full_response")
        else:
            why.append("terminal_answer_boundary_repaired")
    elif score_changed:
        why.append("versioned_payload_acceptance_changed")
    return ";".join(why) or "unchanged"


def content_key(answer, scenario):
    """Task-accepted content, independently of whitespace/serialization."""
    if answer is None:
        return ("missing",)
    if scenario == "restricted_search":
        return ("name_set", tuple(sorted(protocol.parse_search_answer(answer))))
    try:
        return ("audit_object", canonical(protocol.parse_audit_answer(answer)))
    except (ValueError, TypeError, RecursionError, OverflowError):
        return ("invalid_audit_payload",)


def replay(rows, args):
    agents_out, slots_out, diffs, overlays, runtime, decompositions = [], [], [], [], [], []
    verification = Counter()
    for row in rows:
        slot = row["slot"]
        scenario = slot["scenario"]
        if scenario == "evidence_audit":
            old_eval = audit_evaluator(OLD_AUDIT, row["gold"])
            new_eval = audit_evaluator(audit, row["gold"])
        else:
            old_eval = lambda text, records=None: OLD_SEARCH._name_f1(text, row["gold"]["answers"])
            new_eval = lambda text, records=None: search._name_f1(text, row["gold"]["answers"])
        old_agents, new_agents = [], []
        why_slot = set()
        for a in row["agents"]:
            old_answer = a["old_answer"]
            new_answer = protocol.parse_final_answer(a["raw_final_text"], allow_unlabelled=a["allow_unlabelled"]) if a["final_eligible"] else None
            old_score = old_eval(a["old_scoring_input"] or "", a["tool_records"])
            new_score = new_eval(new_answer or "", a["tool_records"])
            old_metrics = old_score if isinstance(old_score, dict) else {"f1": old_score}
            new_metrics = new_score if isinstance(new_score, dict) else {"f1": new_score}
            reported = a["old_answer_metrics"] if scenario == "evidence_audit" else {"f1": a["old_answer_perf"]}
            if not same(old_metrics, reported):
                raise AssertionError(f"Historical scorer mismatch {slot['slot_id']} agent {a['agent_id']}: {old_metrics} != {reported}")
            verification["historical_member_scores_recomputed"] += 1
            old_perf = old_metrics["label_acc"] if scenario == "evidence_audit" else old_metrics["f1"]
            new_perf = new_metrics["label_acc"] if scenario == "evidence_audit" else new_metrics["f1"]
            old_agents.append({"answer": old_answer, "answer_perf": old_perf, "answer_metrics": old_score if isinstance(old_score, dict) else None})
            new_agents.append({"answer": new_answer, "answer_perf": new_perf, "answer_metrics": new_score if isinstance(new_score, dict) else None})
            changed = not same(old_metrics, new_metrics)
            content_changed = content_key(old_answer, scenario) != content_key(new_answer, scenario)
            why = reason(old_answer, new_answer, a["raw_final_text"], scenario, changed)
            if old_answer != new_answer and not content_changed and not changed:
                why = "serialization_only"
            if why != "unchanged":
                why_slot.add(why)
            visible = new_eval(new_answer or "", a["visible_tool_records"]) if scenario == "evidence_audit" and a["visible_tool_records"] is not None else None
            output = {k: slot[k] for k in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item", "outer_repeat", "order", "seed")}
            output.update(agent_id=a["agent_id"], source_locator=row["source_locator"], source_sha256=row["source_sha256"], terminal_message_index=a["terminal_message_index"], terminal_message_id=a["terminal_message_id"], terminal_locator=a["terminal_locator"], raw_final_sha256=a["raw_final_sha256"], old_answer_sha256=text_hash(old_answer), new_answer_sha256=text_hash(new_answer), old_answer_present=old_answer is not None, new_answer_present=new_answer is not None, old_metrics_json=canonical(old_metrics), new_metrics_json=canonical(new_metrics), answer_changed=old_answer != new_answer, score_changed=changed, change_reason=why, score_layer="existing_trace_rescored", answer_protocol=protocol.ANSWER_PROTOCOL_VERSION, visible_verification_eff=visible.get("verification_eff") if visible else None, runtime_counterfactual_changes=len(a["intermediate_parser_differences"]))
            output.update(parsed_content_changed=content_changed, formatting_only=(old_answer != new_answer and not content_changed and not changed))
            agents_out.append(output)
            overlays.append({**{k: output[k] for k in ("slot_id", "agent_id", "model", "system", "scenario", "regime", "strategy", "item", "source_sha256")}, "new_answer": new_answer, "new_scoring_input": new_answer or "", "old_answer": old_answer, "new_score_metrics": new_metrics, "answer_changed_reason": why})
            for difference in a["intermediate_parser_differences"]:
                runtime.append({"slot_id": slot["slot_id"], "agent_id": a["agent_id"], **difference})
        if slot["system"] == "expgym":
            new_metrics = new_agents[0]["answer_metrics"] if scenario == "evidence_audit" else {"f1": new_agents[0]["answer_perf"]}
            if scenario == "evidence_audit":
                new_metrics = {k: new_metrics[k] for k in ("evidence_acc", "label_acc")}
            aggregate_answer_changed = False
            aggregate_content_changed = False
        else:
            old_aggregate = OLD_POOL.aggregate_results(scenario, old_agents, answer_evaluator=old_eval)
            extraction_aggregate = OLD_POOL.aggregate_results(scenario, new_agents, answer_evaluator=old_eval)
            payload_aggregate = OLD_POOL.aggregate_results(scenario, new_agents, answer_evaluator=new_eval)
            new_aggregate = pool.aggregate_results(scenario, new_agents, answer_evaluator=new_eval)
            key = "answer_metrics" if scenario == "evidence_audit" else "answer_perf"
            assert same(old_aggregate[key], row["old_aggregate"][key]), f"Historical pool mismatch {slot['slot_id']}"
            verification["historical_pool_scores_recomputed"] += 1
            if scenario == "evidence_audit":
                new_metrics = {**{f"{m}_mv": new_aggregate["answer_metrics"][m] for m in ("evidence_acc", "label_acc")}, **{f"{m}_mi": statistics.mean(a["answer_metrics"][m] for a in new_agents) for m in ("evidence_acc", "label_acc")}}
            else:
                new_metrics = {"f1_mi": statistics.mean(a["answer_perf"] for a in new_agents), "f1_mv": new_aggregate["answer_perf"]}
            aggregate_answer_changed = old_aggregate["answer"] != new_aggregate["answer"]
            aggregate_content_changed = content_key(old_aggregate["answer"], scenario) != content_key(new_aggregate["answer"], scenario)
            vote_answer_changed = payload_aggregate["answer"] != new_aggregate["answer"]
            if vote_answer_changed:
                why_slot.add("audit_vote_payload_acceptance_unified" if scenario == "evidence_audit" else "search_vote_name_set_unified")
            if not same(extraction_aggregate[key], payload_aggregate[key]):
                why_slot.add("versioned_aggregate_payload_acceptance_changed")
            decompositions.append({"slot_id": slot["slot_id"], "model": slot["model"], "scenario": scenario,
                                   "regime": slot["regime"], "strategy": slot["strategy"], "source_sha256": row["source_sha256"],
                                   "historical_aggregate_metrics": canonical(old_aggregate[key]),
                                   "terminal_extraction_only_metrics": canonical(extraction_aggregate[key]),
                                   "plus_payload_policy_metrics": canonical(payload_aggregate[key]),
                                   "plus_vote_policy_metrics": canonical(new_aggregate[key]),
                                   "extraction_only_score_changed": not same(old_aggregate[key], extraction_aggregate[key]),
                                   "payload_policy_score_changed": not same(extraction_aggregate[key], payload_aggregate[key]),
                                   "vote_policy_score_changed": not same(payload_aggregate[key], new_aggregate[key]),
                                   "vote_policy_answer_changed": vote_answer_changed})
            overlays.append({"slot_id": slot["slot_id"], "agent_id": "aggregate", "scenario": scenario, "source_sha256": row["source_sha256"], "old_answer": old_aggregate["answer"], "new_answer": new_aggregate["answer"], "new_scoring_input": new_aggregate["answer"], "new_score_metrics": new_aggregate[key]})
        old_metrics = json.loads(slot["metrics_json"])
        assert set(old_metrics) == set(new_metrics), (slot["slot_id"], old_metrics, new_metrics)
        changed = not same(old_metrics, new_metrics)
        updated = dict(slot, metrics_json=json.dumps(new_metrics, sort_keys=True), score_complete=str(all(v is not None for v in new_metrics.values())))
        slots_out.append(updated)
        endpoint_keys = [m for m in new_metrics if not m.endswith("_mi")]
        endpoint_changed = any(not same(old_metrics[m], new_metrics[m]) for m in endpoint_keys)
        diffs.append({**{k: slot[k] for k in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item", "outer_repeat", "order", "seed")}, "source_sha256": row["source_sha256"], "old_metrics_json": canonical(old_metrics), "new_metrics_json": canonical(new_metrics), "score_changed": changed, "aggregate_answer_changed": aggregate_answer_changed, "aggregate_parsed_content_changed": aggregate_content_changed, "endpoint_score_changed": endpoint_changed, "change_reason": ";".join(sorted(why_slot)) or "unchanged", "score_layer": "existing_trace_rescored"})
    args.output.mkdir(parents=True, exist_ok=True)
    csv_write(args.output / "agent_rows.csv", agents_out)
    csv_write(args.output / "slot_scalars.csv", slots_out)
    csv_write(args.output / "sample_diff.csv", diffs)
    csv_write(args.output / "affected_samples.csv", [r for r in diffs if r["score_changed"] or r["change_reason"] != "unchanged"])
    csv_write(args.output / "runtime_counterfactual.csv", runtime)
    csv_write(args.output / "pool_decomposition.csv", decompositions)
    csv_write(args.output / "SOURCE_SELECTION.csv", [dict(r["selection"], scoring_source_locator=r["source_locator"], score_layer="existing_trace_rescored", answer_protocol=protocol.ANSWER_PROTOCOL_VERSION) for r in rows])
    private = args.output / "private"
    private.mkdir(exist_ok=True)
    with (private / "answer_overlays.jsonl").open("w") as handle:
        for row in overlays:
            handle.write(canonical(row) + "\n")
    end_code_sha = {p: sha_bytes((REPO / p).read_bytes()) for p in CODE_FILES}
    assert end_code_sha == START_CODE_SHA, "Scoring implementation changed during execution; repeat with frozen code"
    all_agents = [a for r in rows for a in r["agents"]]
    checks = {"status": "PASS", "schema": VERSION, "base_commit": BASELINE, "answer_protocol": protocol.ANSWER_PROTOCOL_VERSION, "audit_payload_protocol": protocol.AUDIT_ANSWER_PROTOCOL_VERSION, "search_payload_protocol": protocol.SEARCH_ANSWER_PROTOCOL_VERSION, "scanned_slots": len(rows), "scanned_members": len(agents_out), "counts_by_system_scenario": dict(Counter(r["system"] + "/" + r["scenario"] for r in slots_out)), "source_hashes_verified_at_packaging": len(rows), "old_score_replay": dict(verification), "changed_individual_answers": sum(r["answer_changed"] for r in agents_out), "changed_individual_metrics": sum(r["score_changed"] for r in agents_out), "changed_slot_metrics": sum(r["score_changed"] for r in diffs), "changed_aggregate_answers": sum(r["aggregate_answer_changed"] for r in diffs), "runtime_counterfactual_records": len(runtime), "runtime_counterfactual_slots": len({r["slot_id"] for r in runtime}), "terminal_locators": dict(Counter(a["terminal_locator"] for a in all_agents)), "terminal_finish_reasons": dict(Counter(str(a["finish_reason"]) for a in all_agents)), "raw_empty_terminals": sum(not a["raw_final_text"].strip() for a in all_agents), "old_missing_answers": sum(a["old_answer"] is None for a in all_agents), "old_missing_recovery_eligible": sum(a["old_answer"] is None and a["final_eligible"] for a in all_agents), "model_calls": 0, "runtime_actions_modified": False, "graph_runtime_repaired": False, "code_sha256": START_CODE_SHA, "code_stable_during_run": True, "legacy_code_sha256": {"audit": OLD_AUDIT_SHA, "pool": OLD_POOL_SHA, "search": OLD_SEARCH_SHA, "protocol": OLD_PROTOCOL_SHA}, "verification_eff_policy": "historical attempted feedback; N1 received-feedback variant exported separately", "layer": "existing_trace_rescored; authoritative adoption is a separate publication manifest"}
    checks.update(changed_individual_parsed_content=sum(r["parsed_content_changed"] for r in agents_out), formatting_only_individual_answers=sum(r["formatting_only"] for r in agents_out), changed_aggregate_parsed_content=sum(r["aggregate_parsed_content_changed"] for r in diffs), changed_slot_endpoint_scores=sum(r["endpoint_score_changed"] for r in diffs), core_repair_commit="0e6c51b6d86f42437038518c2fc8adc510901c0b")
    (args.output / "CHECKS.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(checks, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=REPO / "results/gemini-openrouter-20260917/main")
    parser.add_argument("--delivery", type=Path, default=REPO.parent / "deliveries/paper-ad03e8c-20260916")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, help="Public scoring_inputs.jsonl.gz, requires no private traces or full dataset")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--terminal-evidence", type=Path, help="Verified forced-response evidence for every PoolAct legacy missing terminal")
    args = parser.parse_args()
    if args.inputs:
        with gzip.open(args.inputs, "rt") as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
    else:
        rows = build_inputs(args)
    replay(rows, args)


if __name__ == "__main__":
    main()
