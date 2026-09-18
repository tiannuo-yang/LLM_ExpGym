#!/usr/bin/env python3
"""Verify the portable HPO provenance package using only its public files.

This checks table joins, declared evidence digests, frozen identities and the
optional ALLOWED.json file inventory. It does not reopen private trajectories,
rerun models, or repeat the historical graph replay. A PASS attests to public
package consistency, not independent verification of undisclosed raw evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import sys


EXPECTED_FREEZE = {
    "core_code_commit": "0e6c51b6d86f42437038518c2fc8adc510901c0b",
    "runtime_code_commit": "ffca5704580b75e254f6e52dd4fe9dff104b1be8",
    "source_tree_sha256": "cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02",
}
EXPECTED_PARSER_ADDITIONS = {
    "e70fbde891a064ec706ccf50", "bcb19e920f5a231e46770072",
    "a0dae4e0f6c10847f6d8ea0b",
}
EXPECTED_RERUN_MODELS = {
    "deepseek-v4-flash-0731": 1, "gemini-3.8-flash-medium": 49,
    "glm-5.3": 10, "gpt-5.6-sol": 9, "kimi-k3": 9,
    "qwen3.8-2.4t-a95b-fp8": 19,
}
GROUP_FIELDS = ("model", "system", "regime", "strategy")
IDENTITY_FIELDS = ("model", "system", "item", "regime", "strategy", "seed", "outer_repeat")
SET_FIELDS = (
    "code_commit", "source_tree_sha256", "graph_protocol", "backend",
    "api_protocol", "max_context_tokens", "temperature", "top_p", "top_k",
    "reasoning_effort", "chat_template_kwargs", "max_tokens_config", "max_steps",
    "max_evals", "numpy_version", "configspace_version", "planned_action",
)
MODULES = {
    "expgym/react_loop.py", "expgym/poolact.py", "expgym/extras/parallel_cache.py",
    "expgym/task_tuning.py", "expgym/compact_nasbench101.py",
    "expgym/llm_clients.py", "scripts/run_poolact.py", "scripts/run_paper_sweep.py",
}
SCIENTIFIC_FIELDS = {
    "poolact_protocol", "missing_final_policy", "backend", "model", "scenario", "tuning_task",
    "question_index", "data_source", "cc_split", "cost_regime", "time_budget", "strategies",
    "agents", "seed", "base_seed", "repeat_index", "repeats", "agent_seeds", "seed_semantics",
    "temperature", "max_tokens", "top_p", "top_k", "chat_template_kwargs", "reasoning_effort",
    "api_protocol", "tool_protocol", "max_protocol_retries", "tuning_final_policy", "max_steps",
    "max_evals", "max_context_tokens", "probes", "vllm_disable_thinking", "request_timeout",
    "max_retries", "retry_base_seconds", "retry_max_seconds", "prompt_cache_key_field",
    "evaluation_identity", "prompt_cache_namespace_semantics", "provider_identity",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest_ok(value, size=64):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % size, value) is not None


def truth(value):
    require(value in (True, False, "True", "False"), f"Invalid boolean: {value!r}")
    return value is True or value == "True"


def keyed(rows, label, key="slot_id"):
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), f"Duplicate {key} in {label}")
    return result


class Package:
    def __init__(self, root):
        self.root = root.resolve()
        self.inputs = {}
        self.checks = {}

    def path(self, name):
        rel = Path(name)
        require(not rel.is_absolute() and ".." not in rel.parts, f"Unsafe package path: {name}")
        path = self.root / rel
        require(not path.is_symlink() and path.resolve().is_relative_to(self.root), f"External symlink: {name}")
        return path

    def read(self, name):
        data = self.path(name).read_bytes()
        self.inputs[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        return data.decode("utf-8")

    def csv(self, name):
        import io
        reader = csv.DictReader(io.StringIO(self.read(name)))
        require(reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)), f"Invalid CSV header: {name}")
        rows = list(reader)
        require(all(None not in row and None not in row.values() for row in rows), f"Malformed CSV row: {name}")
        return rows

    def json(self, name):
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                require(key not in result, f"Duplicate JSON key in {name}: {key}")
                result[key] = value
            return result
        return json.loads(self.read(name), object_pairs_hook=unique_pairs)


def verify_tables(p):
    rows = p.csv("hpo_all_slots.csv")
    slots = keyed(rows, "all slots")
    require(len(rows) == 810, "Expected 810 adopted HPO slots")
    require(len({tuple(r[k] for k in IDENTITY_FIELDS) for r in rows}) == 810, "Duplicate experimental coordinate")
    counts = Counter((r["system"], r["strategy"]) for r in rows)
    require(counts == {("expgym", "single"): 486, ("poolact", "naive"): 108,
                       ("poolact", "cached"): 108, ("poolact", "poolact"): 108}, "N1/N4 cohort differs")
    for row in rows:
        sid = row["slot_id"]
        require(digest_ok(sid, 24), f"Invalid slot ID: {sid}")
        for field in ("trajectory_sha256", "source_tree_sha256", "evaluation_identity_sha256",
                      "task_config_sha256", "budget_oracle_sha256"):
            require(digest_ok(row[field]), f"Invalid {field}: {sid}")
        for field in ("table_sha256", "decoder_sha256"):
            require(not row[field] or digest_ok(row[field]), f"Invalid optional {field}: {sid}")
        require(not row["code_commit"] or digest_ok(row["code_commit"], 40), f"Invalid Git commit: {sid}")
        require(truth(row["source_tree_verified"]), f"Unverified source tree declaration: {sid}")
        for field in ("prefix_collision_groups", "ambiguous_path_messages", "same_name_selfloop_messages", "saved_full_history_estimate_max"):
            require(int(row[field]) >= 0, f"Negative {field}: {sid}")
        require(truth(row["parser_control_flow_changed"]) == bool(json.loads(row["parser_control_flow_turns"])), f"Parser flag/turn mismatch: {sid}")
    require(len({r["source_tree_sha256"] for r in rows}) == 8, "Expected eight adopted historical source trees")
    require(Counter(r["regime"] for r in rows if r["system"] == "expgym") ==
            {"cost_free": 162, "cost_moderate": 162, "cost_tight": 162}, "N1 budget counts differ")
    p.checks["cohort"] = {"slots": 810, "N1": 486, "N4": 324, "N1_per_budget": 162}

    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in GROUP_FIELDS)].append(row)
    summary = p.csv("hpo_model_budget_strategy.csv")
    summary_by_key = {tuple(r[k] for k in GROUP_FIELDS): r for r in summary}
    require(len(groups) == len(summary) == len(summary_by_key) == 54, "Expected 54 unique summary groups")
    require(set(groups) == set(summary_by_key), "Summary group keys differ")
    for key, members in groups.items():
        reported = summary_by_key[key]
        require(len(members) == (27 if key[1] == "expgym" else 9), f"Unbalanced group: {key}")
        expected = {
            "slots": len(members),
            "prefix_collision_slots": sum(int(r["prefix_collision_groups"]) > 0 for r in members),
            "ambiguous_path_slots": sum(int(r["ambiguous_path_messages"]) > 0 for r in members),
            "same_name_selfloop_slots": sum(int(r["same_name_selfloop_messages"]) > 0 for r in members),
            "source_tree_verified_slots": sum(truth(r["source_tree_verified"]) for r in members),
            "full_history_estimate_max": max(int(r["saved_full_history_estimate_max"]) for r in members),
        }
        for field, value in expected.items():
            require(int(reported[field]) == value, f"Summary {field} differs: {key}")
        for field in SET_FIELDS:
            values = sorted({r[field] if r[field] != "" else "None" for r in members})
            require(json.loads(reported[field]) == values, f"Summary {field} set differs: {key}")
    p.checks["summary_groups_recomputed"] = 54

    reruns = keyed(p.csv("hpo_rerun_slots.csv"), "rerun slots")
    initial = keyed(p.csv("hpo_rerun_slots.initial94.csv"), "initial rerun slots")
    expected_reruns = {sid: row for sid, row in slots.items() if row["planned_action"] == "rerun"}
    require(len(reruns) == 97 and reruns == expected_reruns, "97 rerun rows must exactly match adopted-slot table")
    require(len(initial) == 94 and set(initial) <= set(reruns), "Initial 94 must be a subset of final 97")
    for sid, old in initial.items():
        require(all(reruns[sid].get(k) == v for k, v in old.items()), f"Initial row provenance changed: {sid}")
    additions = set(reruns) - set(initial)
    require(additions == EXPECTED_PARSER_ADDITIONS, "Initial-to-final additions differ from three parser-control slots")
    parser_ids = {sid for sid, r in slots.items() if truth(r["parser_control_flow_changed"])}
    require(parser_ids == additions, "Parser-control slots differ from final additions")
    require(Counter(r["model"] for r in reruns.values()) == EXPECTED_RERUN_MODELS, "Rerun model counts differ")
    old_graph = {sid for sid, r in slots.items() if r["strategy"] == "poolact" and r["graph_protocol"] == "paper-graph-lock-v3"}
    migrated = {sid for sid, r in slots.items() if r["system"] == "poolact" and
                r["model"] == "gemini-3.8-flash-medium" and r["strategy"] in ("naive", "cached") and r["backend"] == "sub2api"}
    require(len(old_graph) == 63 and len(migrated) == 31 and set(initial) == old_graph | migrated, "Initial rerun reasons do not reconstruct 63 graph + 31 provider controls")
    require(Counter(r["planned_action"] for r in rows) == {"reuse_with_full_rescore": 486,
            "conditional_reuse_with_full_rescore": 227, "rerun": 97}, "Planned action counts differ")
    p.checks["reruns"] = {"initial": 94, "final": 97, "agents": 388, "graph_protocol": 63,
                           "provider_matched_controls": 31, "parser_additions": sorted(additions),
                           "by_model": EXPECTED_RERUN_MODELS}
    for name, rerun_count in (("CHECKS.json", 97), ("CHECKS.initial94.json", 94)):
        checks = p.json(name)
        expected = {"adopted_slots": 810, "N1": 486, "N4": 324,
                    "all_trajectory_hashes_match": True, "input_hashes_checked": 197,
                    "input_hashes_match": True, "unmatched_source_tree_hashes": [],
                    "source_tree_verified_slots": 810, "rerun_slots": rerun_count,
                    "rerun_agent_trajectories": 4 * rerun_count,
                    "planned_action_counts": {"reuse_with_full_rescore": 486,
                        "conditional_reuse_with_full_rescore": 324 - rerun_count, "rerun": rerun_count}}
        for field, value in expected.items():
            require(checks[field] == value, f"Historical audit declaration differs: {name}/{field}")
    p.checks["current_and_initial_audit_declarations"] = "consistent with their respective 97/94 cohorts"
    return slots


def verify_sources(p, slots):
    modules = p.csv("module_hashes.csv")
    require(len(modules) == 71, "Expected 71 historical module declarations")
    module_map = {(r["source_tree_sha256"], r["module"]): r for r in modules}
    require(len(module_map) == len(modules), "Duplicate historical source/module pair")
    trees = {r["source_tree_sha256"] for r in slots.values()}
    require({r["source_tree_sha256"] for r in modules} == trees, "Module/source cohort mismatch")
    roots = p.json("source_roots.json")
    require(all(digest_ok(r["source_tree_sha256"]) for r in roots), "Invalid declared source-root digest")
    require(trees <= {r["source_tree_sha256"] for r in roots}, "Adopted source tree absent from root declarations")
    for row in modules:
        require(digest_ok(row["sha256"]) and digest_ok(row["source_tree_sha256"]), "Invalid module digest")
        require(row["match_status"] == "verified_complete_tree", "Unverified historical module declaration")
    for tree in trees:
        require(all((tree, module) in module_map for module in MODULES), f"Missing core modules for {tree}")
    runtime_rows = p.csv("code_diff/runtime_source_hashes.csv") + p.csv("code_diff/extra_runtime_source_hashes.csv")
    runtime_modules = {(r["source_tree_sha256"], r["path"]): r["sha256"] for r in runtime_rows}
    require(len(runtime_modules) == 211 and len(runtime_rows) == 236, "Historical runtime module inventory differs")
    require(all(runtime_modules[(r["source_tree_sha256"], r["path"])] == r["sha256"] for r in runtime_rows),
            "Duplicate source/path has conflicting runtime module digests")
    for key, row in module_map.items():
        require(runtime_modules.get(key) == row["sha256"], f"Module digest differs from runtime inventory: {key}")
    inputs = p.csv("input_hashes.csv")
    require(len(inputs) == 197, "Expected 197 input hash comparisons")
    require(len({(r["kind"], r["path"]) for r in inputs}) == 197, "Duplicate input evidence identity")
    for row in inputs:
        require(digest_ok(row["recorded_sha256"]) and row["recorded_sha256"] == row["actual_sha256"] and truth(row["match"]), "Input digest comparison differs")
    known_inputs = {(r["kind"], r["recorded_sha256"]) for r in inputs}
    for sid, row in slots.items():
        for field, kind in (("task_config_sha256", "task_configuration"), ("budget_oracle_sha256", "budget_oracle"),
                            ("table_sha256", "table"), ("decoder_sha256", "decoder_source")):
            require(not row[field] or (kind, row[field]) in known_inputs, f"Slot input absent from input evidence: {sid}/{field}")
    p.checks["source_hash_declarations"] = {"historical_trees": 8, "modules": 71, "matched_inputs": 197,
                                             "raw_files_reopened": False}
    return module_map


def verify_graph(p, slots, modules):
    graphs = keyed(p.csv("hpo_graph_slots.csv"), "graph slots")
    expected = {sid for sid, r in slots.items() if r["system"] == "poolact" and r["strategy"] == "poolact"}
    require(len(graphs) == 108 and set(graphs) == expected, "Expected exact 108 shared-graph pools")
    for sid, graph in graphs.items():
        row = slots[sid]
        mapping = {"model": "model", "item": "item", "regime": "regime", "strategy": "strategy",
                   "outer_repeat": "outer_repeat", "selection": "selection", "protocol": "graph_protocol",
                   "source_tree": "source_tree_sha256", "trajectory_sha256": "trajectory_sha256",
                   "collision_groups": "prefix_collision_groups", "path_ambiguous_messages": "ambiguous_path_messages",
                   "selfloop_messages": "same_name_selfloop_messages"}
        for field, slot_field in mapping.items():
            require(graph[field] == row[slot_field], f"Graph evidence mismatch: {sid}/{field}")
    require(Counter(g["protocol"] for g in graphs.values()) == {"paper-graph-lock-v3": 63, "paper-graph-lock-v4": 45}, "Graph protocol counts differ")
    require(sum(int(g["path_ambiguous_messages"]) > 0 for g in graphs.values()) == 60, "Expected 60 observed ambiguous-path pools")
    require(all(not int(g["path_ambiguous_messages"]) and not int(g["selfloop_messages"]) for g in graphs.values() if g["protocol"].endswith("v4")), "Unexpected observed v4 path collision")
    evidence = p.json("code_diff/HISTORICAL_V4_EQUIVALENCE.json")
    require(evidence["status"] == "PASS" and evidence["historical_eval_docs_equals_gpt_equals_unified_bytes"] is True, "Historical v4 equivalence declaration not PASS")
    require(digest_ok(evidence["graph_module_sha256"]), "Invalid graph module digest")
    v4 = {sid for sid, g in graphs.items() if g["protocol"] == "paper-graph-lock-v4"}
    pools = keyed(evidence["pools"], "v4 equivalence pools")
    require(set(pools) == v4, "Equivalence evidence must cover all 45 v4 pools, including parser reruns")
    for sid, item in pools.items():
        row = slots[sid]
        for field, slot_field in (("model", "model"), ("item", "item"), ("regime", "regime"),
                                  ("source_tree", "source_tree_sha256"), ("trajectory_sha256", "trajectory_sha256")):
            require(item[field] == row[slot_field], f"v4 source evidence differs: {sid}/{field}")
        require(digest_ok(item["snapshot_stream_sha256"]), f"Invalid snapshot digest: {sid}")
        require(int(item["events"]) >= 0 and int(item["snapshots"]) > 0, f"Invalid v4 event count: {sid}")
        require(modules[(row["source_tree_sha256"], "expgym/extras/parallel_cache.py")]["sha256"] == evidence["graph_module_sha256"], f"v4 module hash differs: {sid}")
    require(sum(int(v["events"]) for v in pools.values()) == 986 and sum(int(v["snapshots"]) for v in pools.values()) == 9568, "v4 replay totals differ")
    require(evidence["counts"] == {"pools": 45, "source_eval_records": 986, "replay_events": 986, "snapshots": 9568}, "v4 summary counts differ")
    p.checks["graph"] = {"pools": 108, "v3": 63, "v4": 45, "observed_ambiguous_pools": 60,
                          "equivalence_pools": 45, "declared_replayed_evaluations": 986,
                          "declared_equal_snapshots": 9568, "raw_replay_repeated": False}
    return evidence["graph_module_sha256"]


def verify_freeze(p, graph_hash):
    freeze = p.json("CODE_FREEZE.json")
    for field, value in EXPECTED_FREEZE.items():
        require(freeze.get(field) == value, f"Frozen identity differs: {field}")
    require(freeze["graph_module_sha256"] == graph_hash, "Frozen graph module differs from equivalence evidence")
    require(digest_ok(freeze["source_inventory_sha256"]), "Invalid source inventory digest")
    require(digest_ok(freeze["parser_source_sha256"]), "Invalid frozen parser digest")
    require(freeze["parser_source_sha256"] == freeze["core_module_sha256"]["expgym/tool_protocol.py"], "Frozen parser/core module mismatch")
    for field in ("core_module_sha256", "plan_sha256"):
        require(isinstance(freeze[field], dict) and freeze[field], f"Missing frozen {field} mapping")
        require(all(digest_ok(v) for v in freeze[field].values()), f"Invalid frozen {field} digest")
    require(set(freeze["plan_sha256"]) == {"gemini", "gpt", "glm", "kimi", "qwen", "deepseek"}, "Frozen queue models differ")
    require(freeze["whole_pools"] == 97 and freeze["agents"] == 388 and freeze["score_based_reruns"] is False, "Frozen plan cohort differs")
    bindings = keyed(p.csv("RERUN_BINDINGS.csv"), "rerun bindings", "old_slot_id")
    reruns = keyed(p.csv("hpo_rerun_slots.csv"), "rerun slots")
    require(set(bindings) == set(reruns) and len({r["new_job_id"] for r in bindings.values()}) == 97, "Rerun binding IDs differ")
    for sid, row in bindings.items():
        old = reruns[sid]
        for field, old_field in (("model", "model"), ("outer_repeat", "outer_repeat"),
                                  ("source_trajectory_sha256", "trajectory_sha256"), ("rerun_reason", "planned_reason")):
            require(row[field] == old[old_field], f"Rerun binding differs: {sid}/{field}")
        require(re.fullmatch(r"job_[0-9a-f]{64}", row["new_job_id"]) is not None, f"Invalid rerun job ID: {sid}")
        model_key = next(k for k in freeze["plan_sha256"] if row["model"].startswith(k))
        require(row["plan_sha256"] == freeze["plan_sha256"][model_key], f"Rerun queue-plan digest differs: {sid}")
        require(row["source_tree_sha256"] == freeze["source_tree_sha256"], f"Rerun runtime source differs: {sid}")
    p.checks["freeze"] = {**EXPECTED_FREEZE, "graph_module_sha256": graph_hash,
                           "source_inventory_sha256": freeze["source_inventory_sha256"], "rerun_bindings": 97}


def verify_scientific_settings(p, slots):
    settings = p.json("HPO_SCIENTIFIC_SETTINGS.json")
    require(len(settings["allowed_fields"]) == len(SCIENTIFIC_FIELDS) and set(settings["allowed_fields"]) == SCIENTIFIC_FIELDS,
            "Scientific-setting whitelist differs")
    configs = settings["slots"]
    n4_ids = {sid for sid, row in slots.items() if row["system"] == "poolact"}
    require(len(configs) == 324 and set(configs) == n4_ids, "Scientific settings must cover exact 324 historical N4 slots")
    for sid, config in configs.items():
        row = slots[sid]
        require(set(config) <= SCIENTIFIC_FIELDS, f"Non-whitelisted scientific-setting field: {sid}")
        require(config["agents"] == 4 and config["scenario"] == "tuning", f"N4 task/agent setting differs: {sid}")
        require(config["strategies"] == [row["strategy"]], f"Strategy setting differs: {sid}")
        require(config["agent_seeds"] == [int(row["seed"]) + i for i in range(4)], f"Per-agent seed setting differs: {sid}")
        expected_model = "google/gemini-3.8-flash" if row["backend"] == "openrouter" else row["model"]
        require(config["model"] == expected_model, f"Model setting differs: {sid}")
        for field, slot_field in (("poolact_protocol", "graph_protocol"), ("backend", "backend"),
                                  ("tuning_task", "item"), ("cost_regime", "regime"),
                                  ("reasoning_effort", "reasoning_effort"), ("tool_protocol", "tool_protocol"),
                                  ("tuning_final_policy", "tuning_final_policy")):
            require(config[field] == row[slot_field], f"Scientific setting differs: {sid}/{field}")
        for field, slot_field in (("seed", "seed"), ("temperature", "temperature"), ("top_p", "top_p"),
                                  ("top_k", "top_k"), ("max_tokens", "max_tokens_config"),
                                  ("max_context_tokens", "max_context_tokens"), ("max_steps", "max_steps"),
                                  ("max_evals", "max_evals"), ("time_budget", "time_budget")):
            value = config.get(field)
            require((value is None and row[slot_field] == "") or
                    (value is not None and row[slot_field] != "" and float(value) == float(row[slot_field])),
                    f"Numeric scientific setting differs: {sid}/{field}")
        require((config.get("api_protocol") or "chat_completions") == row["api_protocol"], f"API protocol setting differs: {sid}")
        require(config.get("chat_template_kwargs") == json.loads(row["chat_template_kwargs"]), f"Thinking template differs: {sid}")
        identity = config["evaluation_identity"]
        require(identity["sha256"] == row["evaluation_identity_sha256"], f"Evaluation identity differs: {sid}")
        body = {k: v for k, v in identity.items() if k != "sha256"}
        encoded = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        require(hashlib.sha256(encoded).hexdigest() == identity["sha256"], f"Evaluation identity digest does not recompute: {sid}")
        require(identity["selected"]["scenario"] == "tuning" and identity["selected"]["tuning_task"] == row["item"], f"Evaluation task differs: {sid}")
        for field, kind in (("task_config_sha256", "task_configuration"), ("budget_oracle_sha256", "budget_oracle"),
                            ("table_sha256", "table"), ("decoder_sha256", "decoder_source")):
            require(identity["files"].get(kind, {}).get("sha256", "") == row[field], f"Evaluation input differs: {sid}/{kind}")
        require(identity["dependencies"]["numpy"]["version"] == row["numpy_version"] and
                identity["dependencies"]["ConfigSpace"]["version"] == row["configspace_version"], f"Evaluation dependency version differs: {sid}")
    p.checks["scientific_settings"] = {"slots": 324, "allowed_fields": len(SCIENTIFIC_FIELDS), "evaluation_identity_digests_recomputed": 324}


def verify_parser_changes(p, slots):
    changes = p.csv("parser_control_flow.csv")
    require(len(changes) == 4, "Expected four changed parser payload turns")
    require(len({(r["slot_id"], r["agent_id"], r["call_index"], r["message_id"]) for r in changes}) == 4, "Duplicate parser-change turn")
    grouped = defaultdict(list)
    for row in changes:
        sid = row["slot_id"]
        require(sid in slots, f"Unknown parser slot: {sid}")
        old = slots[sid]
        for field in IDENTITY_FIELDS:
            require(row[field] == old[field], f"Parser turn identity differs: {sid}/{field}")
        require(row["source_sha256"] == old["trajectory_sha256"], f"Parser turn source differs: {sid}")
        require(row["agent_id"] in ("0", "1", "2", "3") and int(row["call_index"]) >= 0, f"Invalid parser agent/turn: {sid}")
        changed = truth(row["action_control_flow_changed"])
        acceptance_changed = truth(row["old_accepts_final"]) != truth(row["new_accepts_final"])
        require(changed == acceptance_changed and not (changed and truth(row["is_terminal"])), f"Parser change/control-flow mismatch: {sid}")
        if changed:
            require(not truth(row["old_accepts_final"]) and truth(row["new_accepts_final"]), f"Unexpected parser acceptance direction: {sid}")
            grouped[sid].append({k: row[k] for k in ("agent_id", "call_index", "message_id", "old_accepts_final", "new_accepts_final")})
    require(set(grouped) == EXPECTED_PARSER_ADDITIONS, "Parser changed-slot set differs")
    for sid, row in slots.items():
        require(json.loads(row["parser_control_flow_turns"]) == grouped.get(sid, []), f"Parser control-flow turn list differs: {sid}")
    checks = p.json("RESCORE_CHECKS.json")
    freeze = p.json("CODE_FREEZE.json")
    expected = {"status": "PASS", "slots": 810, "n1": 486, "n4": 324, "agents": 1782,
                "assistant_turns_checked": 18093, "source_hashes_verified": 810, "actual_runtime_parsers_used": 8,
                "control_flow_changed_slots": 3, "turn_payload_changes": 4, "terminal_payload_changes": 1,
                "model_calls": 0, "parser_sha256": freeze["parser_source_sha256"]}
    for field, value in expected.items():
        require(checks[field] == value, f"Historical rescore declaration differs: {field}")
    p.checks["parser_control_flow"] = {"declared_assistant_turns_checked": 18093, "payload_changes": 4,
                                       "control_flow_changed_slots": 3, "terminal_payload_changes": 1,
                                       "raw_turn_audit_repeated": False}


def verify_inventory(p):
    if not p.path("ALLOWED.json").exists():
        p.checks["inventory"] = {"status": "NOT_PRESENT", "checked": False}
        return
    inventory = p.json("ALLOWED.json")
    entries = inventory["files"]
    by_path = keyed(entries, "inventory", "path")
    require("ALLOWED.json" not in by_path, "Inventory cannot include its own hash")
    for name, entry in by_path.items():
        path = p.path(name)
        require(path.is_file(), f"Missing inventoried file: {name}")
        data = path.read_bytes()
        require(digest_ok(entry["sha256"]), f"Invalid inventory digest: {name}")
        require(len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"], f"Inventory hash/size differs: {name}")
    excluded = {"ALLOWED.json", "PUBLIC_CHECKS.json"}
    actual = {str(f.relative_to(p.root)) for f in p.root.rglob("*") if f.is_file()
              and "__pycache__" not in f.relative_to(p.root).parts and str(f.relative_to(p.root)) not in excluded}
    require(set(by_path) == actual, f"Inventory file set differs: missing={sorted(actual-set(by_path))}, extra={sorted(set(by_path)-actual)}")
    require(set(p.inputs) - excluded <= set(by_path), "Verifier inputs missing from inventory")
    p.checks["inventory"] = {"status": "PASS", "checked": True, "files": len(entries)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Optional JSON check report; default is stdout only")
    args = parser.parse_args()
    p = Package(args.package)
    try:
        slots = verify_tables(p)
        modules = verify_sources(p, slots)
        graph_hash = verify_graph(p, slots, modules)
        verify_freeze(p, graph_hash)
        verify_scientific_settings(p, slots)
        verify_parser_changes(p, slots)
        verify_inventory(p)
        report = {"status": "PASS", "scope": "Public package consistency only; no private source files or model calls.", "checks": p.checks, "inputs": p.inputs}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {"status": "FAIL", "error": str(exc), "checks_completed": p.checks, "inputs": p.inputs}
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
