#!/usr/bin/env python3
"""Check public auxiliary-control tables without private sources or model calls.

The published scientific checks describe earlier full-prompt and controlled
graph replay audits. This program joins those declarations and checks digests;
it does not reconstruct withheld prompts or rerun those private-source audits.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

MODELS = {
    "qwen": {"model": "qwen3.8-2.4t-a95b-fp8", "slots": 12, "agents": 42, "snapshots": 4248,
             "old_source": "58f8663d62864940cf16c9454d9c3d7230b77c2858748f5df491ce5d10a77251",
             "runtime": "cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02",
             "code_commit": "ffca5704580b75e254f6e52dd4fe9dff104b1be8"},
    "deepseek": {"model": "deepseek-v4-flash-0731", "slots": 9, "agents": 36, "snapshots": 8208,
                 "old_source": "e96575475b66e9e25b59115301dee10d04850a1f14f9d6b4d499f0651da47a78",
                 "runtime": "4f28d240bfbb6e38d68a1db3466b8c78b8cdbb0b13962b99509a66f713cc0765",
                 "code_commit": "885a5bd70dffe02b8dd610f1699e9f675da2b926"},
    "glm": {"model": "glm-5.3", "slots": 1, "agents": 1, "snapshots": 0,
            "old_source": "a7d5db962f50322564a27fe7a0632fcf3384aee35c1cac133c9c0dd9d2c8e1e4",
            "runtime": "cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02",
            "code_commit": "ffca5704580b75e254f6e52dd4fe9dff104b1be8"},
}
LAUNCHER_SHA = "dc62794f78f5f9ac35167eed7b1fd33e44cbd0d1044a09a28b4f4f2da3b37263"
SYSTEM_SHA = "ca63ee209053765d947e9c79e27f77dc116368e8dca3c066f66775ca774cf641"
SETTING_FIELDS = {"backend", "model", "api_protocol", "generation", "protocol", "limits", "transport",
                  "prompt_cache", "budget", "task", "agents", "strategy", "graph_protocol", "inputs"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def valid_sha(value, size=64):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % size, value) is not None


def unique(rows, key, label):
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
        require(not rel.is_absolute() and ".." not in rel.parts, f"Unsafe public path: {name}")
        path = self.root / rel
        require(not path.is_symlink() and path.resolve().is_relative_to(self.root), f"External public symlink: {name}")
        return path

    def read(self, name):
        data = self.path(name).read_bytes()
        self.inputs[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        return data.decode("utf-8")

    def json(self, name):
        def pairs(items):
            out = {}
            for key, value in items:
                require(key not in out, f"Duplicate JSON key: {name}/{key}")
                out[key] = value
            return out
        return json.loads(self.read(name), object_pairs_hook=pairs)

    def csv(self, name):
        reader = csv.DictReader(io.StringIO(self.read(name)))
        require(reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)), f"Invalid CSV header: {name}")
        rows = list(reader)
        require(all(None not in r and None not in r.values() for r in rows), f"Malformed CSV: {name}")
        return rows


def verify_science(p, settings):
    slots = unique(settings["slots"], "slot_id", "scientific settings")
    selection = unique(p.csv("SELECTION.csv"), "slot_id", "selection")
    require(len(slots) == 22 and set(slots) == set(selection), "Expected exact 22-slot selection/settings join")
    require(len({r["new_job_id"] for r in slots.values()}) == 22, "Duplicate new job identity")
    require(sum(r["N"] for r in slots.values()) == 79, "Expected 79 agents")
    require(Counter(r["model"] for r in slots.values()) == {v["model"]: v["slots"] for v in MODELS.values()}, "Model slot counts differ")
    require(Counter((r["system"], r["N"]) for r in slots.values()) == {("expgym", 1): 3, ("poolact", 4): 19}, "N1/N4 cohort differs")
    require(Counter(r["scope"] for r in slots.values()) == {"main_experiment": 21, "separate_budget_sweep": 1}, "Main/sweep cohort differs")
    for sid, row in slots.items():
        for field, value in selection[sid].items():
            require(field in row and str(row[field]) == value, f"Selection/scientific metadata differs: {sid}/{field}")
        for field in ("source_sha256", "old_source_tree_sha256", "plan_sha256", "matrix_sha256", "new_runtime_source_tree_sha256"):
            require(valid_sha(row[field]), f"Invalid scientific digest: {sid}/{field}")
        require(re.fullmatch(r"job_[0-9a-f]{64}", row["new_job_id"]) is not None, f"Invalid new job ID: {sid}")
    seen, prompts, graph_snapshots = set(), 0, 0
    for alias, expected in MODELS.items():
        evidence = p.json(alias.upper() + "_SCIENCE_CHECKS.json")
        require(evidence["status"] == "PASS" and evidence["model"] == alias, f"Science declaration failed: {alias}")
        require(evidence["model_calls"] == evidence["production_mutations"] == 0, f"Unexpected scientific audit side effects: {alias}")
        require(evidence["slots"] == expected["slots"] and evidence["agents"] == expected["agents"], f"Science cohort count differs: {alias}")
        require(evidence["runtime_source_tree_sha256"] == expected["runtime"] and
                evidence["old_source_tree_sha256"] == expected["old_source"], f"Science runtime/source differs: {alias}")
        checks = unique(evidence["slots_checked"], "slot_id", alias + " science checks")
        expected_slots = {sid for sid, row in slots.items() if row["model"] == expected["model"]}
        require(set(checks) == expected_slots, f"Science slot evidence differs: {alias}")
        require(sum(slots[sid]["N"] for sid in checks) == expected["agents"], f"Science agent count differs: {alias}")
        snapshots = 0
        for sid, item in checks.items():
            row = slots[sid]
            for field in ("model", "system", "scenario", "source_sha256", "new_runtime_source_tree_sha256"):
                require(item[field] == row[field], f"Science evidence join differs: {sid}/{field}")
            require(item["strategy"] == row["old_scientific"]["strategy"] and
                    item["regime"] == row["old_scientific"]["budget"]["regime"], f"Science strategy/regime differs: {sid}")
            require(item["source_tree_sha256"] == row["old_source_tree_sha256"] == expected["old_source"], f"Historical source differs: {sid}")
            require(row["plan_sha256"] == evidence["plan_sha256"] and row["matrix_sha256"] == evidence["matrix_sha256"], f"Frozen plan/matrix differs: {sid}")
            prompt_checks = item["prompt_checks"]
            require(len(prompt_checks) == row["N"], f"Prompt agent coverage differs: {sid}")
            require({x["agent_id"] for x in prompt_checks} == (set(range(4)) if row["N"] == 4 else {-1}), f"Prompt agent IDs differ: {sid}")
            require(len({x["system_sha256"] for x in prompt_checks}) == len({x["task_context_sha256"] for x in prompt_checks}) == 1, f"Within-slot prompt base differs: {sid}")
            for prompt in prompt_checks:
                require(prompt["system_sha256"] == SYSTEM_SHA, f"Native system prompt identity differs: {sid}")
                require(valid_sha(prompt["task_context_sha256"]) and valid_sha(prompt["saved_initial_user_sha256"]), f"Invalid prompt evidence digest: {sid}")
                require(type(prompt["graph_suffix_present"]) is bool, f"Invalid graph suffix declaration: {sid}")
                require((prompt["task_context_sha256"] != prompt["saved_initial_user_sha256"]) == prompt["graph_suffix_present"], f"Prompt suffix/digest relationship differs: {sid}")
                if row["N"] == 1:
                    require(not prompt["graph_suffix_present"], f"N1 unexpectedly has shared graph suffix: {sid}")
            require(item["graph_byte_equality"] is True, f"Controlled graph equality declaration failed: {sid}")
            require(item["controlled_graph_events"] >= 0 and item["controlled_graph_snapshots"] >= 0, f"Negative graph replay count: {sid}")
            if row["N"] == 1:
                require(item["controlled_graph_events"] == item["controlled_graph_snapshots"] == 0, f"N1 shared-graph replay declared: {sid}")
            snapshots += item["controlled_graph_snapshots"]
            prompts += len(prompt_checks)
            seen.add(sid)
        require(snapshots == evidence["graph_controlled_snapshots_equal"] == expected["snapshots"], f"Graph replay snapshot totals differ: {alias}")
        graph_snapshots += snapshots
    require(seen == set(slots) and prompts == 79 and graph_snapshots == 12456, "Aggregate scientific evidence coverage differs")
    p.checks["science"] = {"slots": 22, "agents": 79, "N1": 3, "N4": 19,
                            "declared_prompt_checks": prompts, "declared_equal_graph_snapshots": graph_snapshots,
                            "raw_prompts_read": False, "raw_graph_replay_repeated": False}
    return slots


def verify_settings(p, settings, slots):
    for key in ("allowed_old_fields", "allowed_new_fields"):
        require(len(settings[key]) == len(SETTING_FIELDS) and set(settings[key]) == SETTING_FIELDS, f"Scientific whitelist differs: {key}")
    comparisons, changed_tags = 0, 0
    for sid, row in slots.items():
        old, new = row["old_scientific"], row["new_scientific"]
        require(set(old) == set(new) == SETTING_FIELDS, f"Scientific fields differ from whitelist: {sid}")
        actual_differences = sorted(key for key in SETTING_FIELDS if old[key] != new[key])
        require(actual_differences == sorted(row["permitted_differences"]), f"Undeclared scientific difference: {sid}")
        require(set(actual_differences) <= {"graph_protocol"}, f"Unexpected scientific setting changed: {sid}")
        expected = MODELS[row["model_alias"]]
        require(row["model"] == expected["model"] and row["new_code_commit"] == expected["code_commit"], f"Model/code alias mismatch: {sid}")
        require(new["model"] == row["model"] and new["agents"] == row["N"] and
                new["task"]["scenario"] == row["scenario"], f"Scientific slot identity differs: {sid}")
        require(new["backend"] == "openai" and new["api_protocol"] == "chat", f"Backend/API identity differs: {sid}")
        require(new["protocol"]["tool_protocol"] == "native", f"Native tool protocol differs: {sid}")
        if actual_differences:
            require(row["model_alias"] == "qwen" and row["system"] == "poolact" and
                    old["graph_protocol"] == "paper-graph-lock-v3" and new["graph_protocol"] == "paper-graph-lock-v4", f"Unexpected graph tag migration: {sid}")
            changed_tags += 1
        elif row["system"] == "expgym":
            require(new["graph_protocol"] == "not_used", f"N1 graph declaration differs: {sid}")
        else:
            require(new["graph_protocol"] == "paper-graph-lock-v4", f"N4 graph declaration differs: {sid}")
        budget = new["budget"]
        if budget["regime"] == "cost_free":
            require(budget["beta"] is None and budget["limit_seconds"] is None and budget["mode"] == "no_budget", f"Free-budget setting differs: {sid}")
        else:
            require(budget["limit_seconds"] == budget["beta"] * budget["base_cost_seconds"] and budget["mode"] == "time_aware", f"Budget scalar relationship differs: {sid}")
        inputs = new["inputs"]
        require(inputs["selected"]["scenario"] == row["scenario"] and
                inputs["selected"]["question_index"] == new["task"]["question_index"], f"Input task identity differs: {sid}")
        require(set(inputs["files"]) == ({"evidence", "hints"} if row["scenario"] == "evidence_audit" else {"questions", "corpus"}), f"Input evidence coverage differs: {sid}")
        for name, record in inputs["files"].items():
            require(set(record) == {"present", "bytes", "sha256"} and record["present"] is True and
                    type(record["bytes"]) is int and record["bytes"] > 0 and valid_sha(record["sha256"]), f"Input file digest declaration differs: {sid}/{name}")
        if row["scope"] == "separate_budget_sweep":
            require(row["model_alias"] == "glm" and row["N"] == 1 and budget["beta"] == 20 and
                    new["generation"]["seed"] == 2200 and new["task"]["data_source"] == "phantom_seed2" and
                    new["task"]["question_index"] == 5 and new["task"]["rep"] == 0,
                    "Separate GLM sweep slot identity differs")
        comparisons += len(SETTING_FIELDS) - len(actual_differences)
    require(changed_tags == 10, "Expected ten Qwen N4 graph-version tag changes")
    p.checks["settings"] = {"slots": 22, "main_slots": 21, "sweep_slots": 1,
                             "equal_top_level_fields": comparisons, "declared_graph_tag_changes": changed_tags,
                             "other_scientific_differences": 0}


def verify_freeze(p, slots):
    freeze = p.json("CODE_FREEZE.json")
    require(freeze["core_code_commit"] == "0e6c51b6d86f42437038518c2fc8adc510901c0b", "Frozen core commit differs")
    require(freeze["fixed_parser_sha256"] == "6b09495845fa6c1dc324a82ba471bcfba59265aaa4912ff0acf8307239e84bed", "Frozen parser differs")
    require(freeze["fixed_graph_sha256"] == "f7da6a20cdee00f47fc72632a4ba1bd86059c32c54f78a911d210bcd07ea41d7", "Frozen graph differs")
    require(freeze["launcher_sha256"] == LAUNCHER_SHA, "Frozen launcher differs")
    require((freeze["main_slots"], freeze["sweep_slots"], freeze["agents"]) == (21, 1, 79), "Frozen cohort counts differ")
    for field in ("plan_sha256", "matrix_sha256", "bindings_sha256", "source_tree_sha256", "code_commit", "scientific_review_sha256"):
        require(set(freeze[field]) == set(MODELS), f"Frozen per-model mapping differs: {field}")
        require(all(valid_sha(value, 40 if field == "code_commit" else 64) for value in freeze[field].values()), f"Invalid frozen digest: {field}")
    for alias, expected in MODELS.items():
        require(freeze["source_tree_sha256"][alias] == expected["runtime"] and freeze["code_commit"][alias] == expected["code_commit"], f"Frozen runtime/code identity differs: {alias}")
        name = alias.upper() + "_SCIENCE_CHECKS.json"
        require(freeze["scientific_review_sha256"][alias] == p.inputs[name]["sha256"], f"Frozen scientific review digest differs: {alias}")
        for row in slots.values():
            if row["model_alias"] == alias:
                for field in ("plan_sha256", "matrix_sha256"):
                    require(row[field] == freeze[field][alias], f"Slot/freeze differs: {row['slot_id']}/{field}")
    mechanical = p.json("AUX_LAUNCHER_INDEPENDENT_CHECK.json")
    require(p.inputs["AUX_LAUNCHER_INDEPENDENT_CHECK.json"]["sha256"] == freeze["mechanical_review_sha256"], "Frozen mechanical review digest differs")
    require(mechanical["status"] == "PASS" and mechanical["passed"] == mechanical["total"] == 56,
            "Expected final 56/56 mechanical mock checks")
    require(mechanical["launcher_sha256"] == LAUNCHER_SHA and mechanical["launcher_unchanged_during_review"] is True, "Mechanically reviewed launcher identity differs")
    require(len(mechanical["checks"]) == 56 and all(r["passed"] is True for r in mechanical["checks"]), "Mechanical check entries differ")
    require(mechanical["actual_model_calls"] == mechanical["actual_process_launches"] == mechanical["actual_slurm_mutations"] == 0,
            "Mechanical audit declares external actions")
    real_plans = next(r["detail"] for r in mechanical["checks"] if r["name"] == "real_frozen_plans_22_slots")
    for alias, expected in MODELS.items():
        require(real_plans[alias]["slots"] == expected["slots"], f"Mechanical plan cohort differs: {alias}")
        for field in ("plan_sha256", "matrix_sha256", "bindings_sha256", "source_tree_sha256"):
            require(real_plans[alias][field] == freeze[field][alias], f"Mechanical plan/freeze digest differs: {alias}/{field}")
    preserve = p.json("DEEPSEEK_PROMPT_PRESERVATION.json")
    require(preserve["status"] == "PASS" and preserve["aux_runtime_source_tree_sha256"] == MODELS["deepseek"]["runtime"] and
            preserve["base_runtime_source_tree_sha256"] == MODELS["qwen"]["runtime"] and
            preserve["aux_code_commit"] == MODELS["deepseek"]["code_commit"], "DeepSeek prompt-preservation runtime identity differs")
    require(preserve["historical_source_tree_sha256"] == MODELS["deepseek"]["old_source"], "DeepSeek historical source differs")
    for field in ("other_module_AST_equal", "all_other_regular_files_equal", "fixed_parser_graph_and_scorer_retained"):
        require(preserve[field] is True, f"DeepSeek prompt-preservation declaration failed: {field}")
    require(preserve["independently_checked_regular_files"] == 117, "DeepSeek file audit count differs")
    p.read("deepseek_historical_context_function.txt")
    require(p.inputs["deepseek_historical_context_function.txt"]["sha256"] == preserve["historical_context_function_sha256"], "Historical prompt construction function digest differs")
    p.checks["freeze"] = {"models": sorted(MODELS), "launcher_sha256": LAUNCHER_SHA,
                          "mechanical_checks": 56, "deepseek_distinct_prompt_preserving_runtime": True,
                          "historical_context_function_hash_verified": True}


def verify_provenance(p):
    provenance = p.json("SOURCE_PROVENANCE.json")
    files = unique(provenance["files"], "path", "source provenance")
    expected = {alias.upper() + "_SCIENCE_CHECKS.json" for alias in MODELS} | {"AUX_LAUNCHER_INDEPENDENT_CHECK.json"}
    require(set(files) == expected, "Expected four original audit provenance entries")
    for name, item in files.items():
        require(item["transform"].startswith("byte-identical"), f"Audit provenance transform differs: {name}")
        require(item["source_sha256"] == p.inputs[name]["sha256"], f"Public audit bytes differ from recorded source digest: {name}")
    require(valid_sha(provenance["private_audit_script_sha256"]) and valid_sha(provenance["public_export_script_sha256"]), "Invalid audit/export script digest")
    require(provenance["requires_local_archives_for_full_prompt_recheck"] is True, "Raw-source replay limitation missing")
    for field in ("raw_prompts_or_traces_exported", "serving_configuration_exported", "credentials_read"):
        require(provenance[field] is False, f"Unexpected public export declaration: {field}")
    p.checks["source_provenance"] = {"byte_identical_audit_files": len(files), "private_source_paths_read": False}


def verify_inventory(p):
    if not p.path("ALLOWED.json").exists():
        p.checks["inventory"] = {"status": "NOT_PRESENT", "checked": False}
        return
    inventory = p.json("ALLOWED.json")
    by_path = unique(inventory["files"], "path", "inventory")
    excluded = {"ALLOWED.json", "PUBLIC_CHECKS.json"}
    require(not set(by_path) & excluded, "Inventory includes dynamic/self digest")
    for name, entry in by_path.items():
        data = p.path(name).read_bytes()
        require(valid_sha(entry["sha256"]), f"Invalid inventory digest: {name}")
        require(len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"], f"Inventory bytes/hash differ: {name}")
    actual = {str(f.relative_to(p.root)) for f in p.root.rglob("*") if f.is_file()
              and "__pycache__" not in f.relative_to(p.root).parts and str(f.relative_to(p.root)) not in excluded}
    require(set(by_path) == actual, "Inventory file set differs")
    require(set(p.inputs) - excluded <= set(by_path), "Unlisted verifier input")
    p.checks["inventory"] = {"status": "PASS", "checked": True, "files": len(by_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Optional external JSON report; default stdout only")
    args = parser.parse_args()
    p = Package(args.package)
    try:
        settings = p.json("SCIENTIFIC_SETTINGS.json")
        slots = verify_science(p, settings)
        verify_settings(p, settings, slots)
        verify_freeze(p, slots)
        verify_provenance(p)
        verify_inventory(p)
        report = {"status": "PASS", "scope": "Public table and file consistency only. No private prompts, source trajectories, model calls, or graph replay.", "checks": p.checks, "inputs": p.inputs}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {"status": "FAIL", "error": str(exc), "checks_completed": p.checks, "inputs": p.inputs}
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return int(report["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
