#!/usr/bin/env python3
"""Render the fixed DeepSeek Flash analysis without running analysis or raw scans.

CLI: --inputs FILE --inputs-sha256 SHA --output-dir FRESH_DIR
     --archive-index URL_OR_SIBLING --archive-index-json URL_OR_SIBLING
     --previous-report FIXED_URL [--check]

Archive navigation may use exactly ARCHIVE_INDEX.md / ARCHIVE_INDEX.json in
the report's own directory. This avoids circular self-commit URLs: publish data
and the provider contract at fixed commits, then the report and indexes together.
Inputs, context, provider evidence and the previous report still require immutable
GitHub URLs. Relative index existence/content is checked by publication, not
assumed by this renderer.

Input description schema deepseek-flash.report-inputs.v1:
  {"schema": "deepseek-flash.report-inputs.v1",
   "files": {ANALYZER_OUTPUT_NAME: {"path": ABS_PATH, "bytes": INT,
              "sha256": SHA256, "url": FIXED_GITHUB_BLOB_URL}, ...},
   "context": {"plan": PIN, "coverage": PIN, "run_inputs": PIN,
               "serving_plan": PIN, "oracle": PIN, "provider_contract": PIN}}
Each context PIN has the same path/bytes/sha256/url fields. All eleven analysis
outputs must be indexed. Only six small report dependencies and five required
context files plus provider_contract are read/hash-verified; linked-only
originals retain their inherited pins.
The frozen RUN_INPUTS list must bind the supplied plan, coverage and serving
plan and oracle. Do not replace these with today's configuration or a handwritten
setting. The named-budget interpretation is restricted to the reviewed source
commit below; unknown tuning costs and custom/overridden budgets are rejected.
Outputs: README.zh.md, TABLES.md, REPEATS.md. --check compares exact bytes and
does not create or edit files. No runtime, scorer, network or archive imports.

The sixth required context is a SHA-bound provider_contract. It binds the
actual serving plan, explicit model profile, reviewed source and runtime encoder
identities, and records the operator's real native-validation scope/status.
Linked evidence pins are inherited references, not additional raw reads.
Allocation accounting is maintained separately; this renderer never infers
GPU-hours from requests, agent wall time, current time or planned hardware.

provider_contract schema (create after archive URLs are immutable; never rewrite
the execution RUN_INPUTS to make a circular binding):
  {"schema": "deepseek-flash.provider-contract.v1", "model": MODEL,
   "source_commit": REVIEWED_EXECUTION_COMMIT,
   "serving_plan_sha256": SHA, "model_profile_sha256": SHA,
   "runtime_encoding_files": [RUN_INPUTS_ENCODING_PIN, ...],
   "precision": {"weights": "FP4 experts (mixed checkpoint)",
                 "dense_weights": "FP8", "backend": "Marlin",
                 "arithmetic": "W4A16 MoE"},
   "vendor_recommended_max_output_label": "384K",
   "speculative_decoding": false, "mtp_used": false,
   "validation": {"status": "passed|static_only|unverified", "scope": TEXT,
     "evidence": {"native_wire": PIN, "cpu_encoder_replay": PIN}},
   "forced_final": {
     "wire_tools_retained": {"value": true, "evidence": ["native_wire"]},
     "rendered_tool_definitions_retained":
         {"value": true, "evidence": ["cpu_encoder_replay"]},
     "assistant_reasoning_history_retained":
         {"value": true, "evidence": ["native_wire", "cpu_encoder_replay"]},
     "tool_history_retained":
         {"value": true, "evidence": ["native_wire", "cpu_encoder_replay"]}}}
PIN is path/bytes/sha256/url as above. Evidence records are frozen operator
artifacts describing actual wire dumps and replay with the actual encoder, not
model-name assumptions. If unverified, use null values with no evidence refs;
"passed" requires all four true with their corresponding evidence. The renderer
validates bindings and links but does not read raw evidence or rerun encoding.

"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import stat

SCHEMA = "deepseek-flash.report-inputs.v1"
FILES = ("INPUTS.json", "COSTS.json", "SOURCE_INDEX.json", "normalized.csv",
         "metrics_execution.csv", "metrics.csv", "absolute_settings.csv",
         "by_outerseed.csv", "contrasts.csv", "raw_terminals.csv", "all_attempt_costs.csv")
READ_FILES = {"INPUTS.json", "COSTS.json", "normalized.csv", "absolute_settings.csv",
              "by_outerseed.csv", "contrasts.csv"}
CONTEXT = {"plan", "coverage", "run_inputs", "serving_plan", "oracle", "provider_contract"}
# Fixed-study adapter, not a budget resolver for arbitrary future runner code.
# Reviewed demo_experiment.py:38-108 plus both frozen runner call sites.
REVIEWED_BUDGET_SOURCE_COMMITS = {"5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8"}
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STRATEGIES = ("naive", "cached", "poolact")
QUALITY = {
    ("expgym", "restricted_search"): ("f1",),
    ("expgym", "evidence_audit"): ("evidence_acc", "label_acc"),
    ("expgym", "tuning"): ("gap", "raw_perf"),
    ("poolact", "restricted_search"): ("f1_mi", "f1_mv"),
    ("poolact", "evidence_audit"): ("evidence_acc_mi", "evidence_acc_mv", "label_acc_mi", "label_acc_mv"),
    ("poolact", "tuning"): ("gap_mi", "gap_bon", "raw_perf_mi", "raw_perf_bon"),
}
RESOURCE = ("input_tokens", "output_tokens", "feedback_attempts", "feedback_visible",
            "duplicate_action_attempts", "feedback_cost_seconds", "wall_time_seconds", "protocol_failure_rate")
UNIT_FIELDS = ("model", "system", "scenario", "item", "family", "regime", "strategy", "N", "outerrep")
KEY = ("model", "system", "scenario", "regime", "strategy", "N", "metric", "slice_kind", "slice")
INTS = {"N", "outerrep", "seed", "expected_outcomes", "known_outcomes", "missing_outcomes", "expected_items",
        "known_items", "complete_items", "expected_components", "known_components", "missing_components",
        "min_repeats_per_item", "max_repeats_per_item", "repeat_blocks"}
NUMBERS = {"full_mean", "known_subset_item_weighted_mean", "known_component_subset_item_weighted_mean",
           "descriptive_repeat_sd", "baseline_full_mean", "target_full_mean", "effect", "utility_effect",
           "known_paired_subset_effect", "relative_effect_percent"}
BOOLEANS = {"execution_complete", "higher_is_better", "repeat_block_items_match"}
ARG_FIELDS = ("backend", "tool_protocol", "missing_final_policy", "tuning_final_policy", "temperature",
              "temperature_eval", "temperature_tuning", "top_p", "top_k", "reasoning_effort", "chat_template_kwargs",
              "max_tokens", "max_steps", "max_evals", "max_context_tokens", "max_protocol_retries", "max_retries",
              "request_timeout", "retry_base_seconds", "retry_max_seconds", "prompt_cache_scope", "prompt_cache_key_field")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def fixed_url(value):
    require(isinstance(value, str) and re.fullmatch(
        r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:blob|tree)/[0-9a-f]{40}/[^\s?#()<>]+", value),
        "link must name an explicit immutable GitHub commit")
    return value


def navigation_link(name, value):
    siblings = {"archive_index": "ARCHIVE_INDEX.md", "archive_index_json": "ARCHIVE_INDEX.json"}
    if name in siblings and value == siblings[name]:
        return value
    return fixed_url(value)


def read_csv(raw):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    require(reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)), "missing/duplicate CSV header")
    result = []
    for row in reader:
        require(None not in row and all(v is not None for v in row.values()), "malformed CSV row")
        parsed = {}
        for key, value in row.items():
            if value == "":
                value = None
            elif key in INTS:
                require(re.fullmatch(r"-?\d+", value), "noninteger CSV count")
                value = int(value)
            elif key in NUMBERS:
                value = float(value)
                require(math.isfinite(value), "nonfinite CSV value")
            elif key in BOOLEANS:
                require(value in ("True", "False"), "invalid CSV boolean")
                value = value == "True"
            elif key == "seed_labels":
                value = decode_json(value)
            parsed[key] = value
        result.append(parsed)
    return result


class FrozenInputs:
    """Small explicit dependency set, not a recursive result inventory."""
    def __init__(self):
        self.signatures = {}
        self.parents = {}

    def register(self, path):
        path = Path(path).absolute()
        for parent in reversed(path.parents):
            name = str(parent)
            if name not in self.parents:
                info = parent.lstat()
                require(stat.S_ISDIR(info.st_mode), "symlink/non-directory input parent")
                self.parents[name] = (info.st_dev, info.st_ino)
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode), "symlink/nonregular report input")
        signature = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        require(self.signatures.setdefault(str(path), signature) == signature, "report input changed")
        return path, info

    def read(self, path, checksum, size=None):
        path, info = self.register(path)
        raw = path.read_bytes()
        require(sha(raw) == checksum and (size is None or len(raw) == size), "report input SHA/size mismatch")
        self.register(path)
        return raw

    def pin(self, value, read):
        require(set(value) == {"path", "bytes", "sha256", "url"}, "invalid report input pin fields")
        require(Path(value["path"]).is_absolute() and type(value["bytes"]) is int and value["bytes"] >= 0
                and re.fullmatch(r"[0-9a-f]{64}", value["sha256"]), "invalid report input pin")
        fixed_url(value["url"])
        _, info = self.register(value["path"])
        require(info.st_size == value["bytes"], "linked input size mismatch")
        return self.read(value["path"], value["sha256"], value["bytes"]) if read else None

    def finish(self):
        for name in self.signatures:
            self.register(name)
        for name, identity in self.parents.items():
            info = Path(name).lstat()
            require(stat.S_ISDIR(info.st_mode) and identity == (info.st_dev, info.st_ino), "report input parent changed")


def metric_unit(metric):
    return ("Gap points" if metric.startswith("gap") else "tokens" if metric in ("input_tokens", "output_tokens")
            else "seconds" if metric.endswith("seconds") else "count" if metric in RESOURCE and metric != "protocol_failure_rate" else "fraction")


def slices(unit):
    return [("all", "all"), ("family", unit["family"])] + ([("task", unit["item"])] if unit["scenario"] == "tuning" else [])


def completeness(row, expected, items, components=None):
    require(row["expected_outcomes"] == expected and row["expected_items"] == items
            and 0 <= row["known_outcomes"] <= expected
            and row["missing_outcomes"] == expected - row["known_outcomes"], "table denominator differs from fixed units")
    if "full_mean" in row:
        require((row["full_mean"] is None) == (row["known_outcomes"] != expected), "full mean/unknown contradiction")
    if components is not None:
        require(row["expected_components"] == components and 0 <= row["known_components"] <= components
                and row["missing_components"] == components - row["known_components"], "component denominator mismatch")


def validate(data, context, description):
    info, norm = data["INPUTS.json"], data["normalized.csv"]
    plan, coverage, run, serving = (context[k] for k in ("plan", "coverage", "run_inputs", "serving_plan"))
    require(info.get("schema") == "deepseek-flash.analysis.v1" and (info["execution_slots"], info["analysis_units"], info["agent_slots"]) == (783, 705, 1881), "wrong analysis schema/counts")
    require(plan.get("schema") == "expgym.study-queue-plan.v1" and coverage.get("schema_version") == "deepseek-flash-fixed-matrix-coverage-v1"
            and run.get("schema") == "deepseek-flash.run-inputs.v1", "wrong context schema")
    require(coverage["queue_jobs"] == 783 and coverage["agent_traces"] == 1881
            and coverage["full_canonical_identity_matches"] is True and not coverage["deployment_pending"], "nonformal coverage")
    for name in ("plan", "coverage", "oracle"):
        require(info["input_pins"][name] == description["context"][name]["sha256"], "analysis/context pin mismatch")
    require(run["study_id"] == plan["study_id"] and run["source_tree_sha256"] == plan["source_tree_sha256"], "runtime/source identity differs")
    require(re.fullmatch(r"[0-9a-f]{40}", run["source_commit"])
            and re.fullmatch(r"[0-9a-f]{64}", run["source_tree_sha256"]), "invalid frozen source identity")
    for name in ("plan", "coverage", "serving_plan", "oracle"):
        pin = description["context"][name]
        require(any(row.get("sha256") == pin["sha256"] and row.get("bytes") == pin["bytes"] for row in run["inputs"]), "context not bound by RUN_INPUTS")
    require(serving["model"] == coverage["model"], "serving model differs")
    job_ids = [row["job_id"] for row in plan["jobs"]]
    executions = [row["execution_id"] for row in norm]
    require(len(executions) == len(set(executions)) == len(job_ids) == len(set(job_ids)) == 783
            and set(executions) == set(job_ids) and sum(row["N"] for row in norm) == 1881, "execution universe differs")
    provider_contract(context, description)
    budget_rows(plan, run, context["oracle"], norm)
    units = {}
    actual_settings = set()
    outer_blocks = defaultdict(set)
    for row in norm:
        require(row["model"] == coverage["model"] and type(row["execution_complete"]) is bool, "normalized model/status mismatch")
        require((row["system"], row["scenario"]) in QUALITY and row["regime"] in REGIMES
                and row["N"] == (1 if row["system"] == "expgym" else 4), "invalid normalized setting")
        actual_settings.add(tuple(row[k] for k in ("system", "scenario", "regime", "strategy", "N")))
        outer_blocks[tuple(row[k] for k in UNIT_FIELDS[:-1])].add(row["outerrep"])
        if row["scenario"] == "tuning":
            require(row["outerrep"] in (0, 1, 2) and row["seed"] == 2200 + 4 * row["outerrep"], "tuning block label differs")
        marker = tuple(row[k] for k in UNIT_FIELDS)
        unit = units.setdefault(marker, {**{k: row[k] for k in UNIT_FIELDS}, "components": []})
        unit["components"].append(row)
    require(len(units) == 705, "scientific unit count differs")
    required_settings = {(system, scenario, regime, strategy, 1 if system == "expgym" else 4)
                         for system, scenario in QUALITY
                         for regime in (REGIMES if system == "expgym" else REGIMES[1:])
                         for strategy in (("single",) if system == "expgym" else STRATEGIES)}
    require(actual_settings == required_settings, "missing/extra formal regime or strategy")
    require(all(blocks == ({0, 1, 2} if key[2] == "tuning" else {0}) for key, blocks in outer_blocks.items()), "incomplete per-item outerrep blocks")
    expected = defaultdict(list)
    for unit in units.values():
        audit = unit["system"] == "expgym" and unit["scenario"] == "evidence_audit"
        require(len(unit["components"]) == (3 if audit else 1), "Audit fold/execution count differs")
        if audit:
            require({str(r["order"]) for r in unit["components"]} == {"0", "1", "2"}, "Audit order set differs")
        metrics = QUALITY[unit["system"], unit["scenario"]] + RESOURCE + (() if unit["regime"] == "cost_free" else ("budget_utilization",))
        for metric in metrics:
            for kind, name in slices(unit):
                key = tuple(unit[k] for k in KEY[:6]) + (metric, kind, name)
                expected[key].append(unit)
    absolute = {}
    for row in data["absolute_settings.csv"]:
        key = tuple(row[k] for k in KEY)
        require(key in expected and key not in absolute, "missing/extra/duplicate absolute setting")
        selected = expected[key]
        completeness(row, len(selected), len({u["item"] for u in selected}), sum(len(u["components"]) for u in selected))
        require(row["unit"] == metric_unit(row["metric"])
                and row["higher_is_better"] is (True if quality(row) else None), "metric unit/direction mismatch")
        blocks = {u["outerrep"] for u in selected}
        require(row["repeat_blocks"] == len(blocks) and (len(blocks) > 1 or row["descriptive_repeat_sd"] is None), "repeat/SD mismatch")
        absolute[key] = row
    require(set(absolute) == set(expected), "absolute tables omit planned family/task/metric")
    wanted_repeats = {(key, outer): [u for u in selected if u["outerrep"] == outer]
                      for key, selected in expected.items() for outer in {u["outerrep"] for u in selected}}
    seen = set()
    for row in data["by_outerseed.csv"]:
        marker = (tuple(row[k] for k in KEY), row["outerrep"])
        require(marker in wanted_repeats and marker not in seen, "missing/extra/duplicate repeat table row")
        selected = wanted_repeats[marker]
        completeness(row, len(selected), len({u["item"] for u in selected}), sum(len(u["components"]) for u in selected))
        require(row["unit"] == metric_unit(row["metric"])
                and row["higher_is_better"] is (True if quality(row) else None), "repeat metric unit/direction mismatch")
        require(row["seed_labels"] == sorted({r["seed"] for u in selected for r in u["components"]}), "repeat seed labels differ")
        seen.add(marker)
    require(seen == set(wanted_repeats), "repeat tables omit planned blocks")
    wanted_contrasts = {}
    for key, base in absolute.items():
        axis, levels = ("regime", REGIMES) if base["system"] == "expgym" else ("strategy", STRATEGIES)
        for target in levels[levels.index(base[axis]) + 1:]:
            other = {**base, axis: target}
            target_key = tuple(other[k] for k in KEY)
            if target_key in absolute:
                require({(u["item"], u["outerrep"]) for u in expected[key]} == {(u["item"], u["outerrep"]) for u in expected[target_key]}, "unpaired setting universes")
                wanted_contrasts[key, target] = absolute[target_key]
    seen = set()
    for row in data["contrasts.csv"]:
        key = tuple(row[k] for k in KEY)
        marker = (key, row["target"])
        require(marker in wanted_contrasts and marker not in seen, "missing/extra/duplicate contrast")
        base, target = absolute[key], wanted_contrasts[marker]
        require(row["unit"] == base["unit"] and row["higher_is_better"] is base["higher_is_better"], "contrast metric unit/direction mismatch")
        exp = row["system"] == "expgym"
        require(row["baseline"] == row["regime" if exp else "strategy"] and row["comparison_axis"] == ("regime" if exp else "strategy")
                and row["effect_definition"] == ("baseline_minus_target" if exp else "target_minus_baseline"), "contrast direction changed")
        require(row["baseline_full_mean"] == base["full_mean"] and row["target_full_mean"] == target["full_mean"], "contrast absolute means differ")
        if base["full_mean"] is None or target["full_mean"] is None:
            require(row["effect"] is None, "unknown endpoint improperly filled by paired subset")
        else:
            effect = (base["full_mean"] - target["full_mean"]) * (1 if exp else -1)
            require(row["effect"] is not None and math.isclose(row["effect"], effect, rel_tol=1e-10, abs_tol=1e-10), "contrast arithmetic differs")
        completeness(row, base["expected_outcomes"], base["expected_items"])
        require((row["effect"] is None) == (row["known_outcomes"] != row["expected_outcomes"]), "contrast completeness differs")
        seen.add(marker)
    require(seen == set(wanted_contrasts), "contrast table omits planned comparisons")
    validate_costs(data["COSTS.json"])
    return list(units.values())


def provider_contract(context, description):
    plan, run, serving, coverage, provider = (context[k] for k in
        ("plan", "run_inputs", "serving_plan", "coverage", "provider_contract"))
    require(provider.get("schema") == "deepseek-flash.provider-contract.v1"
            and provider["model"] == coverage["model"]
            and provider["source_commit"] == run["source_commit"], "provider contract identity differs")
    require(provider["serving_plan_sha256"] == description["context"]["serving_plan"]["sha256"]
            and provider["model_profile_sha256"] == coverage["model_profile"]["sha256"],
            "provider serving/profile binding differs")
    profile = coverage["model_profile"]["value"]
    require(profile["model"] == provider["model"] and profile["reasoning_effort"] == "max"
            and profile["chat_template_kwargs"] == {"thinking": True}, "maximum thinking profile differs")
    require(any(row.get("sha256") == coverage["model_profile"]["sha256"]
                and row.get("bytes") == coverage["model_profile"]["bytes"] for row in run["inputs"]),
            "model profile not bound by RUN_INPUTS")
    encodings = provider["runtime_encoding_files"]
    require(isinstance(encodings, list) and encodings and encodings == run["runtime_encoding_files"],
            "provider actual runtime encoder identity differs")
    for pin in encodings:
        require(set(pin) == {"path", "bytes", "sha256"} and Path(pin["path"]).is_absolute()
                and type(pin["bytes"]) is int and pin["bytes"] >= 0
                and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]), "invalid runtime encoder pin")
    topology, slurm = serving["config"]["topology"], serving["config"]["slurm"]
    require(slurm["nodes"] == 4 and slurm["gpus_per_node"] == 8
            and topology["replicas"] == 4 and topology["tp_size"] == 8
            and topology.get("pp_size", 1) == 1 and topology["nodes_per_replica"] == 1,
            "DeepSeek serving topology differs")
    require(type(serving["context_length"]) is int and serving["context_length"] >= 32768,
            "invalid explicit serving context length")
    require(provider["precision"] == {"weights": "FP4 experts (mixed checkpoint)",
            "dense_weights": "FP8", "backend": "Marlin", "arithmetic": "W4A16 MoE"},
            "DeepSeek mixed-checkpoint precision differs")
    require(provider["vendor_recommended_max_output_label"] == "384K"
            and provider["speculative_decoding"] is False and provider["mtp_used"] is False,
            "vendor recommendation or no-spec/MTP contract differs")
    for job in plan["jobs"]:
        args = job["args"]
        require(args.get("reasoning_effort") == "max" and args.get("chat_template_kwargs") == {"thinking": True}
                and args.get("top_k") is None and args.get("top_p") == .95
                and args.get("max_tokens") == 32768 and args.get("max_steps") == args.get("max_evals") == 30
                and args.get("request_timeout") == 7200 and args.get("max_retries") == 2,
                "DeepSeek request profile/transport differs")
        require(args.get("temperature") == 1 if job["runner"] == "poolact" else
                args.get("temperature_eval") == args.get("temperature_tuning") == 1,
                "DeepSeek request temperature differs")
    validation = provider["validation"]
    require(validation["status"] in {"passed", "static_only", "unverified"}
            and isinstance(validation["scope"], str) and validation["scope"].strip(),
            "invalid provider validation scope/status")
    evidence = validation["evidence"]
    require(isinstance(evidence, dict) and set(evidence) <= {"native_wire", "cpu_encoder_replay"},
            "unknown provider evidence scope")
    for pin in evidence.values():
        require(set(pin) == {"path", "bytes", "sha256", "url"} and Path(pin["path"]).is_absolute()
                and type(pin["bytes"]) is int and pin["bytes"] >= 0
                and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]), "invalid provider evidence pin")
        fixed_url(pin["url"])
    expected = {"wire_tools_retained": {"native_wire"},
                "rendered_tool_definitions_retained": {"cpu_encoder_replay"},
                "assistant_reasoning_history_retained": {"native_wire", "cpu_encoder_replay"},
                "tool_history_retained": {"native_wire", "cpu_encoder_replay"}}
    require(set(provider["forced_final"]) == set(expected), "forced-final property scope differs")
    for name, required in expected.items():
        observed = provider["forced_final"][name]
        require(set(observed) == {"value", "evidence"} and
                (observed["value"] is None or type(observed["value"]) is bool)
                and isinstance(observed["evidence"], list)
                and len(observed["evidence"]) == len(set(observed["evidence"]))
                and set(observed["evidence"]) <= set(evidence), "invalid forced-final property evidence")
        require(observed["value"] is None or required <= set(observed["evidence"]),
                "forced-final property lacks actual wire/encoder evidence")
        require(validation["status"] != "passed" or observed["value"] is True,
                "passed provider record must verify each forced-final property")
    return provider


def budget_rows(plan, run, oracle, normalized):
    """Audited named presets, without importing a runner or fallback costs."""
    require(run["source_commit"] in REVIEWED_BUDGET_SOURCE_COMMITS, "budget contract source commit was not reviewed")
    by_id = {row["execution_id"]: row for row in normalized}
    overrides = ("beta", "time_budget", "c_base", "baseline", "show_cost", "include_cost",
                 "include_cost_in_observation", "include_overhead", "include_overhead_in_observation",
                 "cost_scale", "overhead_scale")
    for job in plan["jobs"]:
        args = job["args"]
        selection = job["selection"]
        source = selection if job["runner"] == "expgym" else args
        expected = by_id[job["job_id"]]
        require(source.get("scenario") == expected["scenario"] and source.get("cost_regime") == expected["regime"]
                and source.get("cost_regime") in REGIMES, "custom or mismatched budget regime")
        for parameters in (args, selection, job.get("identity", {}).get("args", {})):
            require(all(parameters.get(key) is None for key in overrides), "budget/cost-visibility override is outside fixed study")
        if args.get("cost_regime") is not None:
            require(args["cost_regime"] == expected["regime"], "argument budget regime mismatch")
        if args.get("cost_regimes") is not None:
            regimes = args["cost_regimes"].split(",")
            require(set(regimes) <= set(REGIMES) and expected["regime"] in regimes, "custom budget requested by plan")
        if expected["scenario"] == "tuning":
            require(source.get("tuning_task") == expected["item"], "budget task selector differs from analyzed item")
    tasks = sorted({row["item"] for row in normalized if row["scenario"] == "tuning"})
    require(len(tasks) == 9 and isinstance(oracle.get("tasks"), dict), "fixed budget table needs nine tuning tasks and oracle")
    result = [["restricted_search", "expgym / poolact", 300, "无上限；成本隐藏", 3000, 900],
              ["evidence_audit", "expgym / poolact", 300, "无上限；成本隐藏", 3000, 900]]
    for task in tasks:
        entry = oracle["tasks"].get(task)
        require(isinstance(entry, dict), "tuning task missing from bound budget oracle")
        cost = entry.get("best_cost")
        require(type(cost) in (int, float) and math.isfinite(cost) and cost > 0,
                "tuning oracle best_cost must be finite and positive; no fallback")
        systems = sorted({row["system"] for row in normalized if row["scenario"] == "tuning" and row["item"] == task})
        result.append([task, " / ".join(systems), cost, "无上限；成本隐藏", 10 * cost, 3 * cost])
    return result


def validate_costs(costs):
    keys = ("input_tokens", "output_tokens", "reasoning_tokens_included_in_output", "total_tokens", "request_wall_seconds")
    require(set(costs) == {"all_physical_attempts", "effective_slots"}, "cost scopes differ")
    for scope in costs.values():
        require(set(scope) == set(keys), "cost fields differ")
        require(len({r["expected"] for r in scope.values()}) == 1, "cost ledger denominators differ")
        for row in scope.values():
            require(type(row["known"]) is int and type(row["expected"]) is int and 0 <= row["known"] <= row["expected"], "cost count invalid")
            require((row["complete_total"] is None) == (row["known"] != row["expected"]), "cost total/completeness differs")
            require(all(v is None or type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in (row["complete_total"], row["known_subset_total"])), "invalid cost total")
        incoming, outgoing, total = (scope[k]["complete_total"] for k in ("input_tokens", "output_tokens", "total_tokens"))
        if incoming is not None and outgoing is not None:
            require(total == incoming + outgoing, "reasoning was double-counted or total tokens differ")
        reasoning = scope["reasoning_tokens_included_in_output"]["complete_total"]
        require(reasoning is None or outgoing is None or reasoning <= outgoing, "reasoning exceeds inclusive output")


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("`", "&#96;").replace("[", "&#91;").replace("]", "&#93;").replace("\n", "<br>").replace("\r", "")


def fmt(value, signed=False):
    if value is None:
        return "unknown"
    if type(value) is bool:
        return str(value).lower()
    if type(value) in (int, float):
        return format(value, "+.6g" if signed else ".6g")
    return canonical(value) if isinstance(value, (dict, list)) else str(value)


def table(headers, rows):
    return "\n".join(["| " + " | ".join(map(esc, headers)) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
                     + ["| " + " | ".join(esc(fmt(value)) for value in row) + " |" for row in rows]) + "\n"


def quality(row):
    return row["metric"] in QUALITY[row["system"], row["scenario"]]


def ordered(rows):
    return sorted(rows, key=lambda r: tuple(str(r.get(k, "")) for k in KEY) + (str(r.get("outerrep", "")), str(r.get("target", ""))))


def absolute_table(rows):
    headers = ("系统", "场景", "层/切片", "档位", "策略", "指标", "单位", "完整均值", "known/expected", "missing", "item 数", "已知子集均值", "R / SD")
    return table(headers, [[r["system"], r["scenario"], r["slice_kind"] + "/" + r["slice"], r["regime"], r["strategy"], r["metric"], r["unit"], r["full_mean"],
                            "%s/%s" % (r["known_outcomes"], r["expected_outcomes"]), r["missing_outcomes"], r["expected_items"], r["known_subset_item_weighted_mean"],
                            "%s / %s" % (r["repeat_blocks"], fmt(r["descriptive_repeat_sd"]))] for r in ordered(rows)])


def contrast_table(rows):
    headers = ("系统", "场景", "层/切片", "档位", "指标", "差值方向", "完整差值", "单位", "百分点差", "配对 known/expected", "missing", "仅已知配对子集")
    output = []
    for r in ordered(rows):
        direction = r["baseline"] + " − " + r["target"] if r["system"] == "expgym" else r["target"] + " − " + r["baseline"]
        output.append([r["system"], r["scenario"], r["slice_kind"] + "/" + r["slice"], r["regime"], r["metric"], direction, fmt(r["effect"], True), r["unit"],
                       fmt(r["effect"] * 100 if r["effect"] is not None else None, True) if r["unit"] == "fraction" else "不适用",
                       "%s/%s" % (r["known_outcomes"], r["expected_outcomes"]), r["missing_outcomes"], r["known_paired_subset_effect"]])
    return table(headers, output)


def direction_summary(rows):
    return "正向 %d、零 %d、负向 %d、unknown %d" % tuple(sum(predicate(r["effect"]) for r in rows) for predicate in (
        lambda v: v is not None and v > 0, lambda v: v == 0, lambda v: v is not None and v < 0, lambda v: v is None))


def render(description, data, context, units, links, descriptor_sha):
    model = context["coverage"]["model"]
    norm, absolute, contrasts, repeats = (data[k] for k in ("normalized.csv", "absolute_settings.csv", "contrasts.csv", "by_outerseed.csv"))
    plan, run, serving = (context[k] for k in ("plan", "run_inputs", "serving_plan"))
    all_quality = [r for r in absolute if quality(r) and r["slice_kind"] == "all"]
    all_effects = [r for r in contrasts if quality(r) and r["slice_kind"] == "all"]
    exp = [r for r in all_effects if r["system"] == "expgym" and r["baseline"] == "cost_free" and r["target"] == "cost_tight"
           and r["metric"] in ("f1", "evidence_acc", "gap")]
    pool = [r for r in all_effects if r["system"] == "poolact" and r["baseline"] == "naive" and r["target"] == "poolact"
            and r["metric"] in ("f1_mv", "evidence_acc_mv", "gap_mi")]
    require(len(exp) == 3 and len(pool) == 6, "main display endpoint coverage differs")
    groups = defaultdict(list)
    for row in norm:
        groups[row["system"], row["scenario"]].append(row)
    matrix_rows = []
    for (system, scenario), selected in sorted(groups.items()):
        count_units = sum(u["system"] == system and u["scenario"] == scenario for u in units)
        matrix_rows.append([system, scenario, len({r["item"] for r in selected}), sorted({r["regime"] for r in selected}), sorted({r["strategy"] for r in selected}),
                            sorted({r["N"] for r in selected}), sorted({r["outerrep"] for r in selected}), len(selected), count_units,
                            sum(r["N"] for r in selected), sum(r["execution_complete"] for r in selected)])
    request_rows = []
    for system in ("expgym", "poolact"):
        jobs = [j for j in plan["jobs"] if j["runner"] == system]
        for field in ARG_FIELDS:
            values = sorted({canonical(j["args"].get(field)) for j in jobs})
            request_rows.append([system, field, "; ".join(values), "计划请求值；null 表示该参数未显式记录"])
    topology = serving["config"]["topology"]
    slurm = serving["config"]["slurm"]
    cost_rows = []
    for scope, ledger in data["COSTS.json"].items():
        for name, row in ledger.items():
            cost_rows.append([scope, name, "seconds" if name == "request_wall_seconds" else "tokens", row["complete_total"], row["known_subset_total"],
                              "%s/%s" % (row["known"], row["expected"])])
    input_rows = []
    for section in ("files", "context"):
        for name, pin in sorted(description[section].items()):
            checked = section == "context" or name in READ_FILES
            input_rows.append([name, pin["bytes"], pin["sha256"], "本次读取并校验 SHA" if checked else "仅继承冻结 pin、核大小并提供链接"])
    file_links = "\n".join("- [%s](%s)" % (esc(name), pin["url"]) for name, pin in sorted(description["files"].items()))
    context_links = " · ".join("[%s](%s)" % (name, pin["url"]) for name, pin in sorted(description["context"].items()))
    provider = context["provider_contract"]
    protocol = provider["forced_final"]
    validation = provider["validation"]
    provider_rows = [
        ["expert weight format / backend / arithmetic", [provider["precision"][k] for k in ("weights", "backend", "arithmetic")]],
        ["checkpoint 同时包含的 dense 权重格式", provider["precision"]["dense_weights"]],
        ["vendor high/max recommended output", provider["vendor_recommended_max_output_label"]],
        ["实际每请求输出上限", 32768],
        ["forced-final tool_choice", "none"],
        ["speculative decoding / MTP used", [provider["speculative_decoding"], provider["mtp_used"]]],
        *[[key, {"observed": value["value"], "evidence": value["evidence"]}] for key, value in sorted(protocol.items())],
        ["运行方 native 验收记录状态", validation["status"]],
        ["运行方记录的实际检查范围", validation["scope"]],
    ]
    provider_evidence = " · ".join("[%s](%s)" % (esc(name), pin["url"])
                                    for name, pin in sorted(validation["evidence"].items())) or "尚未提供实际 wire/encoder 证据"
    text = ["# %s：ExpGym / PoolAct 全设置描述性报告" % esc(model),
            "本报告只展示冻结分析结果，不新增实验、不重评分、不恢复 raw。属于固定已知任务的 Custom study，不自动等于 paper-exact reproduction。输入身份冻结与回顾性矩阵不构成预注册或显著性证据。",
            "## 1. 主要发现与适用范围",
            "主要展示端点（展示选择，不冒充事前注册）：ExpGym 的 F1 / EA / Gap，Free−Tight 为%s；PoolAct 的 F1-MV / EA-MV / Gap-MI，两个预算下 poolact−naive 为%s。所有端点和相邻档位/缓存对照见后文，包含负值和 unknown。" % (direction_summary(exp), direction_summary(pool)),
            "这里 ExpGym 的正差表示预算收紧后下降，PoolAct 的正差表示在该固定比较中改善。汇总改善不代表每个任务或每次重复都改善；本模型的方向也不能替代其他模型的证据。未完成或不可评分的完整端点不以已知子集均值代替。",
            contrast_table(exp + pool),
            "## 2. 实际设置、覆盖和分析单元",
            "固定分母为 **783 个执行槽位、1881 个 agent 槽位、705 个分析单元**；已完成执行 %d / 783。执行完成不等于分数完整，质量表另列 known/expected/missing。" % sum(r["execution_complete"] for r in norm),
            table(("系统", "场景", "item 数", "档位", "策略", "N", "outerrep 标签", "执行槽", "分析单元", "agent 槽", "执行完成"), matrix_rows),
            "ExpGym Audit 每文档的三种固定顺序拆成三个进程，报告中只平均一次；不是三组独立文档。Search 与 Pool Audit 为 R1；tuning 的 outerrep 0/1/2 对应三个 R1 stage 的 seed block 2200/2204/2208。种子只是请求标签，不证明独立或可重复生成。N=4 的池是一个分析结果，不是四次独立重复。",
            "冻结源码的 PoolAct 协议为 paper-graph-lock-v3：同 pool 的共享图注入、一次 LLM 决策与待执行动作登记由同一推理锁串行保护，工具执行在锁外。因此 PoolAct 内部的 LLM 并发与 naive/cached 不同；全局动态队列并行的是独立 pool，不能把队列 workers×N 直接当成 PoolAct 同时推理数。",
            "两个系统的 all 不是同一任务全集：表中 Search 的 item 范围分别呈现，tuning 亦分别呈现；本报告不从两套 all 直接计算跨系统胜负，也不把旧双模型结果合并成相同样本。",
            "实际计划、身份记录与服务计划：" + context_links,
            "源码提交 `%s`；源码树 SHA256 `%s`。" % (esc(run["source_commit"]), esc(run["source_tree_sha256"])),
            "### 2.1 模拟反馈预算与成本可见性",
            "按已审阅冻结源码 demo_experiment.py:38–108 的具名档位：Free 无模拟反馈预算上限且成本隐藏；Moderate = 10×c_base、Tight = 3×c_base，二者成本可见。Search/Audit 的 c_base 固定为 300 模拟秒；全部九个 tuning 任务采用绑定 oracle3.json 的 best_cost。这里不使用缺失任务的 100 秒 fallback。",
            table(("任务/场景", "适用系统", "c_base（模拟秒）", "Free（仅 ExpGym）", "Moderate 每 agent（模拟秒；成本可见）", "Tight 每 agent（模拟秒；成本可见）"),
                  budget_rows(plan, run, context["oracle"], norm)),
            "以上是模拟反馈预算，不是推理墙钟或 GPU 时间。PoolAct 只运行 Moderate/Tight，N=4 的每个 agent 各有同一 B；不能称整个池共用一个 B，N×B 是池级名义预算口径而非实际开销测量。Free 仍有步骤、评估次数和输出等限制，不表示无限推理。此预算解释只接受已审阅源码提交且拒绝 custom、beta/time_budget 或成本可见性覆盖；切换源码需重新核对契约。",
            "### 2.2 服务与请求配置",
            table(("服务计划字段", "冻结值"), [["model", serving["model"]], ["checkpoint", serving.get("checkpoint")],
                   ["nodes × GPUs/node", "%s × %s" % (slurm.get("nodes"), slurm.get("gpus_per_node"))],
                   ["replicas / TP / PP / EP", [topology.get("replicas"), topology.get("tp_size"), topology.get("pp_size", 1), serving.get("ep_size")]],
                   ["server context_length", serving.get("context_length")], ["reasoning_parser", serving.get("reasoning_parser")],
                   ["tool_call_parser", serving.get("tool_call_parser")], ["server_args", serving.get("server_args")],
                   ["weight_payload_hashes_verified（RUN_INPUTS 声明）", run.get("weight_payload_hashes_verified")]]),
            "以上是绑定的服务配置：4 节点 × 每节点 8 GPU，共四个独立的单节点 TP8 副本，不是跨四节点的一份模型。量化与协议检查范围见以下冻结 provider_contract；本报告不把配置值或 HTTP health 自动提升为真实 native 验收。",
            table(("Provider 契约字段", "冻结记录"), provider_rows),
            "FP4 仅描述 experts；该混合 checkpoint 同时包含 FP8 dense 等格式，W4A16 指 Marlin 的 MoE 执行路径，不是全模型统一 4-bit 算术。本次不开 speculative decoding，也不使用 MTP。",
            "最大 thinking 使用 reasoning_effort=max 与 thinking=true；每请求输出最多 32768 token。厂商 checkpoint README 对 high/max 推荐最大输出长度为 %s token，本 Custom study 沿用跨模型比较的 32768 上限，未采用厂商该推荐长输出设置；因此不是厂商性能的完全复现。冻结 server context_length=%s 也不是最大输出长度，两者不可互换；该服务值直接读取实际 serving plan，不沿用其他模型的上限。" % (esc(provider["vendor_recommended_max_output_label"]), esc(serving["context_length"])),
            "上表逐项记录 dsv4 forced-final（tool_choice=none）是否保留 wire tools、渲染后工具定义、assistant reasoning 与 tool 历史。每项观察值都绑定其实际 wire dump / CPU 实际 encoder 重放的证据；没有验证的属性保持 null。本报告只转述运行方冻结验证状态和具体范围，不将自身离线生成视为新增 native 实测。证据入口：" + provider_evidence,
            table(("系统", "参数", "冻结计划值集合", "口径"), request_rows),
            "请求字段不等于服务端已验证的行为。上下文字段也不自动代表精确 tokenizer 计数；未显式给出的其他 runner 默认值，本报告不从旧报告反推，需沿固定源码/原件入口核查。预算秒数已经由上方冻结源码/绑定 oracle 表明确给出，不从结果均值倒推。",
            "## 3. 预算收紧与 ExpGym 表现",
            "绝对分数按 item 内先平均重复、再对 item 等权平均；Audit 先按文档折叠顺序一次。F1 / EA / LA 与 raw performance 为 0–1 分数；Gap 是效用型归一化分数（越高越好），每个 agent 先按冻结 oracle 截零后再算 MI，不能从汇总 raw performance 重新反推。",
            absolute_table([r for r in all_quality if r["system"] == "expgym"]),
            "以下包含 Free−Moderate、Free−Tight、Moderate−Tight。差值保留原单位；fraction 的 0.02 在百分点列为 2，不是 0.02%。",
            contrast_table([r for r in all_effects if r["system"] == "expgym"]),
            "## 4. 缓存、协调与 PoolAct 表现",
            "两个实际预算档位均展示 naive / cached / poolact，保留 MI 与 MV/BoN 的区别。MI/MV/BoN 都是池级端点；任一必需 agent 不可评分时，完整池端点保持 unknown。",
            absolute_table([r for r in all_quality if r["system"] == "poolact"]),
            "cached−naive 描述共享缓存对照；poolact−cached 描述在该设置下进一步协调的差异；poolact−naive 是整体差异，不能据此分离所有机制或宣称相同 GPU 成本。",
            contrast_table([r for r in all_effects if r["system"] == "poolact"]),
            "全部预定义 family / tuning task 的绝对值及对应差值见 [TABLES.md](TABLES.md)，R3 明细见 [REPEATS.md](REPEATS.md)。不按结果方向删减家族或任务。",
            "## 5. 资源与时间",
            "### 5.1 实际分配成本与正式队列墙钟",
            "allocation GPU-hours 与正式队列墙钟由独立冻结的真实分配账本记录；本报告不从请求、agent 时长、当前时间或计划 GPU 数量推算。未提供该账本时，本报告中这些量均为 unknown。",
            "### 5.2 HTTP 尝试成本与分析单元资源",
            "下表为完整 HTTP 尝试账本的独立总计：all_physical_attempts 包含保留的失败/恢复前尝试，effective_slots 只属于最终授权槽位。reasoning 已包含在 output，不能再加一次。unknown 表示必要用量缺失，旁列仅是已知尝试子集。",
            table(("范围", "指标", "单位", "完整总计", "已知子集合计", "known/expected 尝试"), cost_rows),
            "每分析单元资源均值如下；完整 family/task 资源表在 TABLES.md。Pool 的 token、反馈和模拟成本按池内 N 个 agent 合计；Exp Audit 资源按三个顺序均值展示，物理尝试成本则仍逐执行计入上表。",
            absolute_table([r for r in absolute if not quality(r) and r["slice_kind"] == "all"]),
            "feedback_cost_seconds 是模拟反馈秒，不是 GPU 推理时长；预算利用率也不是 GPU 利用率。Pool 整个子进程 wall 未被该 exporter 记录，因此保持 unknown，不能以 agent wall 求和/最大值冒充。HTTP request wall 合计不是并发实验总历时；真实分配账本与正式 queue wall 单独记录，此处没有 formal-only GPU 利用量，故不据此推算有效算力或速度优越性。",
            "## 6. 主张、缺失与限制",
            "当前表格能回答本模型、这些固定任务与设置下的方向和幅度；不能证明模型总体普适、未见任务泛化或统计显著性。负向结果保留，unknown 不补零。task-abstention-v1 下正常 Search/Audit 空回答可有合法零分；HPO 缺配置不可评分，不把二者当作同一种故障。",
            "完整均值只在全部计划端点已知时给出；已知子集仅作诊断。配对差值使用完整计划 item×outerrep 范围，不静默取交集。R3 的 SD 是三个 block 的描述性变化，不是标准误、置信区间或独立生成证据；R1 不提供重复 SD。",
            "## 7. 完整原件、聚合和存档入口",
            "[原始 dump 存档索引](%s) · [机器可读存档索引](%s) · [旧双模型完整报告](%s)" % (links["archive_index"], links["archive_index_json"], links["previous_report"]),
            "存档索引应定位 collection/bundle → member inventory → tar 分片及匹配恢复工具。这里引用其固定版本，不重新扫描 tar、不声称已恢复或验证全部内容，也不把新 collection 引用的旧包再计作一份新物理副本。旧双模型报告仅供独立比较入口，不与本模型 all 直接合并。",
            file_links,
            "metrics_execution 是执行层；metrics 是 Audit 已折叠一次的分析层；normalized 是唯一有效槽位映射；raw_terminals 是终态投影，不是 HTTP 回复。all_attempt_costs 与原始请求/回复的完整映射入口分别是成本表和 SOURCE_INDEX/存档索引。",
            table(("显式输入", "字节", "SHA256", "本次使用范围"), input_rows),
            "## 8. 生成与有限验收",
            "报告输入描述 SHA256：`%s`；生成器 SHA256：`%s`。没有模型调用、重评分、raw 恢复或归档内容扫描。" % (descriptor_sha, sha(Path(__file__).read_bytes())),
            "生成器检查 schema、固定输入 SHA、覆盖/分母、对照方向与均值差（1e-10 浮点容差）及固定提交链接格式；显示保留六位有效数字，真实 CSV 值不改写。`--check` 只比较这三份 Markdown 的精确字节，不写文件。链接实际可达性与一次成稿后的独立数值/逻辑复核仍由发布流程完成；本生成器不把自身检查称为独立复核。"]
    appendix = ["# 全部 family / task 与资源表", "本附件直接展示冻结聚合表，不重新评分。unknown 与已知子集严格区分；层级 all/family/task 不相加当作额外样本。",
                "## 质量：预定义 family / task", absolute_table([r for r in absolute if quality(r) and r["slice_kind"] != "all"]),
                "## 质量：全部对应差值", contrast_table([r for r in contrasts if quality(r) and r["slice_kind"] != "all"]),
                "## 资源：全部层次", absolute_table([r for r in absolute if not quality(r)]),
                "## 资源：全部差值", "资源差值只描述消耗变化；正负不能单独解释为性能改善。", contrast_table([r for r in contrasts if not quality(r)])]
    repeat_rows = [r for r in repeats if r["scenario"] == "tuning" and quality(r)]
    repeated = ["# Tuning R3 明细", "outerrep 0/1/2 对应三个独立队列 stage 的 seed block 2200/2204/2208；seed 标签不是独立生成保证。所有 tuning 指标、family/task/all、档位和策略均保留。Search / Pool Audit 是 R1；Exp Audit 三顺序已经按文档平均一次，不再冒充 R3。完整含资源的 block 数据请见主报告链接的 by_outerseed.csv。",
                table(("系统", "场景", "层/切片", "档位", "策略", "指标", "单位", "outerrep", "seed 标签", "完整均值", "known/expected", "missing", "已知子集"),
                      [[r["system"], r["scenario"], r["slice_kind"] + "/" + r["slice"], r["regime"], r["strategy"], r["metric"], r["unit"], r["outerrep"], r["seed_labels"], r["full_mean"],
                        "%s/%s" % (r["known_outcomes"], r["expected_outcomes"]), r["missing_outcomes"], r["known_subset_item_weighted_mean"]] for r in ordered(repeat_rows)])]
    return {"README.zh.md": "\n\n".join(text) + "\n", "TABLES.md": "\n\n".join(appendix) + "\n", "REPEATS.md": "\n\n".join(repeated) + "\n"}


def generate(inputs_path, inputs_sha256, output_dir, links, check=False):
    output_dir = Path(output_dir)
    require(output_dir.is_dir() if check else not output_dir.exists(), "report check requires an existing directory; creation requires a fresh one")
    require(set(links) == {"archive_index", "archive_index_json", "previous_report"}, "explicit archive and prior-report links required")
    links = {name: navigation_link(name, url) for name, url in links.items()}
    inputs = FrozenInputs()
    description = decode_json(inputs.read(inputs_path, inputs_sha256))
    require(description.get("schema") == SCHEMA and set(description.get("files", {})) == set(FILES)
            and set(description.get("context", {})) == CONTEXT, "explicit complete analysis/context inventory required")
    data, context = {}, {}
    for name in FILES:
        raw = inputs.pin(description["files"][name], name in READ_FILES)
        if raw is not None:
            data[name] = read_csv(raw) if name.endswith(".csv") else decode_json(raw)
    for name in sorted(description["context"]):
        context[name] = decode_json(inputs.pin(description["context"][name], True))
    units = validate(data, context, description)
    outputs = render(description, data, context, units, links, inputs_sha256)
    inputs.finish()
    if check:
        for name, value in outputs.items():
            require((output_dir / name).read_bytes() == value.encode("utf-8"), "report output differs: " + name)
    else:
        require(not output_dir.exists(), "report output directory must be fresh")
        output_dir.mkdir(parents=True)
        for name, value in outputs.items():
            with (output_dir / name).open("x", encoding="utf-8") as stream:
                stream.write(value)
    return {"files": sorted(outputs), "check": check, "execution_slots": 783, "analysis_units": 705,
            "agent_slots": 1881, "model_calls": 0, "raw_reads": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    for name in ("archive-index", "archive-index-json", "previous-report"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(generate(args.inputs, args.inputs_sha256, args.output_dir,
                              {name: getattr(args, name) for name in ("archive_index", "archive_index_json", "previous_report")}, args.check), sort_keys=True))


if __name__ == "__main__":
    main()
