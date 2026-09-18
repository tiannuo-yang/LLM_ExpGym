#!/usr/bin/env python3
"""Offline verification of the public protocol-repair delivery (no model calls).

The default/--components mode verifies completed public components. --full also
requires the final rerun adoption and fairness gate. Rebuilds use a fresh output
directory; published inputs and tables must remain byte-identical. HPO's normal
lightweight replay uses hash-bound benchmark certificates, not fresh benchmarks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

BASELINE = "297c3d00a006f33fc5a8ca799ce91d327d92839e"
DEFAULT_BUNDLE = Path("results/protocol-repair-20260918")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"}}


class Verification:
    def __init__(self, args, output):
        self.args = args
        self.repo = args.repo.resolve()
        self.bundle = (args.bundle or self.repo / DEFAULT_BUNDLE).resolve()
        self.output = output.resolve()
        self.commands = []
        self.comparisons = []
        self.checks = {}
        self.environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        self.environment.pop("PYTHONOPTIMIZE", None)

    def run(self, name, script, *options, python=None, env=None):
        command = [str(python or self.args.python), "-B", str(script), *map(str, options)]
        started = time.monotonic()
        completed = subprocess.run(command, cwd=self.repo, env=env or self.environment,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log = self.output / "logs" / (name + ".log")
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(completed.stdout, encoding="utf-8")
        self.commands.append({"name": name, "argv": command, "cwd": str(self.repo),
                              "returncode": completed.returncode,
                              "seconds": round(time.monotonic() - started, 3),
                              "log": str(log), "log_sha256": sha(log), "script_sha256": sha(script)})
        require(completed.returncode == 0, f"{name} failed; see {log}")
        print(f"PASS {name}", flush=True)
        return completed.stdout

    def compare(self, published, rebuilt, paths, label):
        require(bool(paths), f"{label}: no tables selected")
        for relative in paths:
            left, right = published / relative, rebuilt / relative
            require(right.is_file(), f"{label}: missing rebuilt {relative}")
            old, new = sha(left), sha(right)
            require(old == new, f"{label}: byte mismatch in {relative}")
            self.comparisons.append({"component": label, "path": str(left.relative_to(self.repo)) if left.is_relative_to(self.repo) else str(left),
                                     "sha256": old, "replay_sha256": new, "byte_identical": True})

    def csv_paths(self, published, rebuilt, *, recursive=True):
        def names(directory):
            iterator = directory.rglob("*.csv") if recursive else directory.glob("*.csv")
            return {path.relative_to(directory).as_posix() for path in iterator}
        expected, actual = names(rebuilt), names(published)
        require(expected == actual, f"CSV inventory mismatch at {published}: missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}")
        return sorted(expected)

    def preflight(self):
        require(self.repo.is_dir() and (self.repo / "expgym/tool_protocol.py").is_file(), "--repo must be a source checkout")
        require(self.bundle.is_dir(), "Public protocol repair bundle not found")
        require(not self.output.is_relative_to(self.bundle), "Output must not be inside the published bundle")
        capsule = self.repo / "tools/historical_scorers" / BASELINE
        manifest_path = capsule / "MANIFEST.json"
        require(manifest_path.is_file(), "Public historical scorer source capsule is required; no Git history or network fetch is needed")
        historical = read_json(manifest_path)
        require(historical.get("commit") == BASELINE, "Historical capsule commit mismatch")
        declared_scoring = read_json(self.bundle / "rescore/search_audit/CHECKS.json")
        expected = declared_scoring["legacy_code_sha256"]
        core_identities = {name: value for name, value in declared_scoring["code_sha256"].items() if name.startswith("expgym/")}
        for name, value in core_identities.items():
            require(sha(self.repo / name) == value, "Current scientific scorer differs from the frozen public rescore identity: " + name)
        self.checks["frozen_scoring_sources"] = core_identities
        names = {"expgym/task_evidence_audit.py": "audit", "expgym/poolact.py": "pool",
                 "expgym/task_restricted_search.py": "search", "expgym/tool_protocol.py": "protocol"}
        require({item["path"] for item in historical["files"]} == set(names), "Incomplete historical scorer capsule")
        for item in historical["files"]:
            source = capsule / item["path"]
            require(sha(source) == item["sha256"] == expected[names[item["path"]]], "Historical scorer identity mismatch")
        self.checks["historical_source"] = {"commit": BASELINE, "capsule_manifest_sha256": sha(manifest_path), "git_object_access": False}
        require((self.repo / "data/hpo_tuning/oracle3.json").is_file(), "Tracked small oracle3.json is required, not the full HPO data")
        self.checks["dependencies"] = {"default": ["Python >= 3.10 standard library", "public historical scorer source capsule", "tracked oracle3.json"],
                                       "benchmark_only": ["frozen benchmark data", "NumPy 2.4.6 NAS interpreter", "historical ParamNet Python 3.7/NumPy 1.18.5/sklearn 0.23.2 interpreter", "immutable raw/source version maps"],
                                       "baseline_commit": BASELINE}
        publication = self.bundle / "rescore/PUBLICATION_INPUTS.json"
        manifest = read_json(publication)
        for item in manifest["files"]:
            path = self.bundle / "rescore" / item["path"]
            require(path.is_file() and sha(path) == item["sha256"] and path.stat().st_size == item["bytes"],
                    "Published rescore input identity mismatch: " + item["path"])
        self.checks["rescore_publication_files_verified"] = len(manifest["files"])

    def historical_component(self, name):
        preserved = self.bundle / (name + "_existing_trace")
        return preserved if preserved.is_dir() else self.bundle / name

    def require_global_gate(self):
        path = self.bundle / "control_flow_adoption/FAIRNESS_MANIFEST.json"
        require(path.is_file(), "--full requires the global HPO97 + Search/Audit21 + sweep1 manifest")
        gate = read_json(path)
        require(gate.get("schema") == "expgym.total-runtime-adoption.v1", "Unexpected global adoption schema")
        require(gate.get("status") == "PASS" and gate.get("adoption_ready") is True
                and gate.get("total_main_runtime_adoption") is True, "Global runtime adoption is not complete")
        for key, expected in [("main_slots", 4698), ("hpo_verified_pools", 97),
                              ("auxiliary_verified_main_slots", 21), ("auxiliary_verified_members", 78),
                              ("sweep_additional_slots", 1)]:
            require(gate.get(key) == expected, f"Global adoption {key} must equal {expected}")
        sweep = gate.get("sweep_control_gate", {})
        require(sweep.get("required") is True and sweep.get("status") == "PASS"
                and sweep.get("registered_slots") == sweep.get("verified_slots") == 1
                and sweep.get("main_overlap_slots") == 0,
                "Required sweep runtime control is incomplete or overlaps main")
        require(gate.get("hpo_stage_ready") is True and gate.get("auxiliary_stage_ready") is True,
                "A declared runtime stage is not ready")
        for key, expected in [("hpo_required_pools", 97), ("auxiliary_required_main_slots", 21), ("auxiliary_required_members", 78)]:
            require(gate.get(key) == expected, "Unexpected registered runtime control population")
        for relative, expected_sha in gate.get("code_sha256", {}).items():
            require(sha(self.repo / relative) == expected_sha, "Global gate scientific implementation mismatch")
        self.checks["global_adoption_gate"] = {"sha256": sha(path), "manifest": gate}
        return gate

    def final_analysis(self, final):
        tools = self.bundle / "tools"
        rebuilt = self.output / "final_analysis"
        rebuilt.mkdir()
        main = rebuilt / "main"
        versions = read_json(self.bundle / "main/SCORE_VERSIONS.json")
        require(versions["new"]["adoption_state"] == "official", "Published main is still a candidate")
        self.run("final_main_all_aggregates", tools / "rebuild_analysis.py", "--repo", self.repo,
                 "--baseline", self.repo / "results/gemini-openrouter-20260917/main",
                 "--scalars", final / "slot_scalars.csv", "--selection", final / "SOURCE_SELECTION.csv",
                 "--output", main, "--score-identity", versions["new"]["identity"],
                 "--code-commit", versions["new"]["code_commit"], "--adoption-state", "official",
                 "--fairness-manifest", self.bundle / "control_flow_adoption/FAIRNESS_MANIFEST.json")
        self.compare(self.bundle / "main", main,
                     self.csv_paths(self.bundle / "main", main), "final_main")
        self.compare(self.bundle / "main", main, ["FINDINGS.json", "SCORE_VERSIONS.json"], "final_main_findings")
        display = rebuilt / "display"
        self.run("final_display", tools / "recompute_display.py", "--source", main, "--output", display)
        self.compare(self.bundle / "display", display, self.csv_paths(self.bundle / "display", display), "final_display")
        secondary = rebuilt / "secondary"
        self.run("final_secondary", tools / "rebuild_secondary.py", "--repo", self.repo, "--source", main, "--output", secondary)
        for name in ["search", "poolact", "cases"]:
            self.compare(self.bundle / name, secondary / name,
                         self.csv_paths(self.bundle / name, secondary / name), "final_" + name)
        docs = rebuilt / "docs"
        self.run("final_report_render", tools / "render_report.py", "--repo", self.repo,
                 "--main", main, "--display", display, "--secondary", secondary,
                 "--audit", self.bundle / "audit", "--hpo", self.bundle / "hpo_behavior/official_rescored486",
                 "--existing-rescore", self.output / "rescore/main", "--output", docs)
        self.compare(self.bundle, docs, ["conclusion_delta.csv", "RENDER_CHECKS.json"], "final_conclusions")
        self.compare(self.repo / "results/paper-analysis-20260916", docs,
                     ["README.zh.md", "APPENDIX.zh.md", "ABSTRACT.en.md"], "final_report")
        layers = self.bundle / "score_layers"
        rebuilt_layers = rebuilt / "score_layers"
        self.run("final_score_layers", layers / "compare_score_layers.py", "--main", self.output / "rescore/main",
                 "--reference", layers, "--output", rebuilt_layers,
                 "--official", final / "slot_scalars.csv", "--official-sources", final / "SOURCE_SELECTION.csv",
                 "--adoption", final / "SOURCE_SELECTION.csv", "--adoption-layer-column", "selection")
        self.compare(layers, rebuilt_layers, ["score_layer_comparison.csv", "audit_layer_group_means.csv", "CHECKS.json"], "final_score_layers")
        layer_rows = rows(rebuilt_layers / "score_layer_comparison.csv")
        require(len(layer_rows) == 4698 and all(row["final_official_status"] == "adopted_from_supplied_manifest"
                and row["final_official_metrics_json"] for row in layer_rows), "Final score layer has missing or pending rows")
        require(read_json(rebuilt_layers / "CHECKS.json")["official_adoption_complete"] is True, "Final score layer adoption incomplete")
        self.checks["final_analysis"] = {"all_main_slots": 4698, "aggregate_rows": 7767, "ranks": 126,
                                         "comparisons": 1298, "final_score_layers": 4698,
                                         "source": "Rebuilt adoption scalars; all published CSVs and rendered report bytes checked."}

    def final_audit(self, final, aux):
        audit = self.bundle / "audit"
        rebuilt = self.output / "audit_official"
        require((self.bundle / "audit_existing_trace").is_dir(), "Final Audit must preserve audit_existing_trace separately")
        self.run("audit_official_behavior", audit / "recompute_audit.py", "--replay-public", audit, "--output", rebuilt)
        self.compare(audit, rebuilt, self.csv_paths(audit, rebuilt), "audit_official")
        require(read_json(audit / "CHECKS.json")["case_population"] == read_json(rebuilt / "CHECKS.json")["case_population"],
                "Official Audit report case population differs from public recomputation")
        expected = {(row["slot_id"], row["agent_id"]): {"source_sha256": row["source_sha256"],
                    "metrics": json.loads(row["new_metrics_json"])} for row in rows(self.output / "rescore/search_audit/agent_rows.csv")
                    if row["scenario"] == "evidence_audit"}
        replacements = 0
        for row in rows(aux / "agent_rows.csv"):
            if row["scenario"] != "evidence_audit":
                continue
            key = row["slot_id"], row["agent_id"]
            require(key in expected, "Unregistered Audit auxiliary member")
            expected[key] = {"source_sha256": row["result_sha256"], "metrics": json.loads(row["new_runtime_metrics_json"])}
            replacements += 1
        seen = set()
        for relative in ["n1/trace_metrics.csv", "coordination/audit_agents.csv"]:
            for row in rows(audit / relative):
                key = row["slot_id"], row["agent_id"]
                require(key not in seen, "Duplicate official Audit member")
                seen.add(key)
                target = expected[key]
                require(row["source_sha256"] == target["source_sha256"], "Official Audit behavior/source mismatch")
                for metric in ["label_acc", "evidence_acc", "verification_eff"]:
                    value = target["metrics"][metric]
                    require(row[metric] == "" if value is None else math.isclose(float(row[metric]), value, rel_tol=0, abs_tol=1e-12), "Official Audit behavior/scorer mismatch")
        require(seen == set(expected) and len(seen) == 2574, "Official Audit member coverage mismatch")
        scalars = {row["slot_id"]: row for row in rows(final / "slot_scalars.csv")}
        sources = {row["slot_id"]: row for row in rows(final / "SOURCE_SELECTION.csv")}
        pools = rows(audit / "coordination/audit_pools.csv")
        require(len(pools) == 468 and len({row["slot_id"] for row in pools}) == 468, "Official Audit pool coverage mismatch")
        for row in pools:
            require(row["source_sha256"] == sources[row["slot_id"]]["result_sha256"], "Official Audit pool/source mismatch")
            metrics = json.loads(scalars[row["slot_id"]]["metrics_json"])
            for metric in ["label_acc", "evidence_acc"]:
                require(math.isclose(float(row[metric]), metrics[metric + "_mv"], rel_tol=0, abs_tol=1e-12), "Official Audit pool/scorer mismatch")
        self.checks["final_audit"] = {"members": 2574, "pools": 468, "members_from_new_controls": replacements,
                                     "scores_bound_to_replayed_members_and_final_adoption": True}

    def scorer_components(self):
        public = self.bundle / "rescore"
        replay = self.output / "rescore"
        sa = replay / "search_audit"
        self.run("search_audit_parser_scorer", self.repo / "tools/rescore_protocol.py",
                 "--inputs", public / "search_audit/scoring_inputs.jsonl.gz", "--output", sa)
        self.compare(public / "search_audit", sa, self.csv_paths(public / "search_audit", sa), "search_audit")
        checks = read_json(sa / "CHECKS.json")
        require(checks["scanned_slots"] == 3888 and checks["scanned_members"] == 9504, "Search/Audit replay coverage mismatch")
        self.checks["search_audit"] = {"actual_parser_task_scorer_and_pool_revote": True, "slots": 3888, "members": 9504, "private_trajectory_access": False}
        hpo = replay / "hpo"
        # This child flag verifies certificates in --inputs mode. It is NOT
        # exposed as a claim of fresh benchmark execution by this wrapper.
        self.run("hpo_terminal_and_certificate_replay", self.repo / "tools/rescore_hpo_protocol.py",
                 "--inputs", public / "hpo/scoring_inputs.jsonl.gz", "--output", hpo, "--verify-benchmarks")
        self.compare(public / "hpo", hpo, self.csv_paths(public / "hpo", hpo) + ["scoring_inputs.jsonl.gz"], "hpo")
        checks = read_json(hpo / "CHECKS.json")
        require(checks["agents"] == 1782 and checks["slots"] == 810, "HPO terminal replay coverage mismatch")
        require(checks["saved_benchmark_certificate_verification"] is True and checks["benchmark_verification"] is False,
                "Unexpected HPO lightweight benchmark scope")
        self.checks["hpo"] = {"parser_visible_configuration_matching_fallback_and_aggregation_replayed": True,
                              "members": 1782, "slots": 810, "benchmark_certificate_uses": checks["benchmark_certificates_used"],
                              "fresh_benchmark_evaluations": 0,
                              "full_assistant_turn_audit": "Retained source-hashed historical attestation; not reexecuted from this terminal-only package."}
        sweep = replay / "sweep"
        shutil.copytree(public / "sweep", sweep)
        self.run("whois1170_parser_scorer", self.repo / "tools/rescore_whois_protocol.py",
                 "--inputs", sweep / "scoring_inputs.jsonl.gz", "--output", sweep)
        self.run("whois_beta10_main_join", public / "sweep/check_beta10_main.py", "--sweep", sweep, "--main", sa)
        self.compare(public / "sweep", sweep, ["BETA10_MAIN_JOIN.csv"], "sweep_join")
        self.checks["whois_scorer"] = {"actual_parser_and_name_f1_replayed": True, "slots": 1170, "main_overlap": 234,
                                       "unique_additional_slots": 936, "stored_scalar_aggregation_only": False}
        main = replay / "main"
        self.run("merge4698_rescored", self.repo / "tools/merge_protocol_rescore.py", "--search-audit", sa,
                 "--hpo", hpo, "--sweep", sweep, "--output", main)
        self.compare(public / "main", main, self.csv_paths(public / "main", main), "rescore_main")
        checks = read_json(main / "CHECKS.json")
        require(checks["registered_slots"] == 4698 and checks["registered_members"] == 11286, "Merged coverage mismatch")
        self.checks["existing_trace_rescore_coverage"] = {"main_slots": 4698, "main_members": 11286, "unique_main_plus_sweep_slots": 5634, "unique_members": 12222,
                                                        "fresh_runtime_actions_replayed": False}

    def behavior_components(self):
        hpo = self.bundle / "hpo_behavior"
        for layer in ["observed_behavior486", "official_rescored486"]:
            target = self.output / ("hpo_" + layer + ".json")
            self.run("hpo_behavior_" + layer, hpo / "verify_public_behavior.py", "--behavior", hpo / layer, "--output", target)
            self.checks["hpo_behavior_" + layer] = read_json(target)
        attached = self.output / "hpo_behavior_attached"
        self.run("attach_formal_hpo486", hpo / "attach_rescored.py", "--observed", hpo / "observed_behavior486",
                 "--agent-rows", self.output / "rescore/hpo/agent_rows.csv", "--output", attached,
                 "--scoring-version", "final-answer-boundary-v2/existing_trace_rescored")
        self.compare(hpo / "official_rescored486", attached, self.csv_paths(hpo / "official_rescored486", attached), "hpo_official_behavior")
        audit = self.historical_component("audit")
        rebuilt = self.output / "audit"
        self.run("audit_public_behavior_rebuild", audit / "recompute_audit.py", "--replay-public", audit, "--output", rebuilt)
        self.compare(audit, rebuilt, self.csv_paths(audit, rebuilt), "audit_behavior")
        # Bind behavior primitives to the freshly replayed scorer outputs;
        # Audit public aggregation alone does not reexecute task scoring.
        scored_agents = {(r["slot_id"], r["agent_id"]): r for r in rows(self.output / "rescore/search_audit/agent_rows.csv")
                         if r["scenario"] == "evidence_audit"}
        linked_agents = set()
        for relative in ["n1/trace_metrics.csv", "coordination/audit_agents.csv"]:
            for row in rows(audit / relative):
                key = row["slot_id"], row["agent_id"]
                require(key not in linked_agents, "Duplicate Audit behavior agent")
                linked_agents.add(key)
                scored = scored_agents[key]
                require(row["source_sha256"] == scored["source_sha256"], "Audit behavior source identity mismatch")
                metrics = json.loads(scored["new_metrics_json"])
                for metric in ["label_acc", "evidence_acc", "verification_eff"]:
                    if metrics[metric] is None:
                        require(row[metric] == "", "Audit behavior/scorer null mismatch")
                    else:
                        require(math.isclose(float(row[metric]), metrics[metric], abs_tol=1e-12, rel_tol=0), "Audit behavior/scorer " + metric + " mismatch")
        require(len(linked_agents) == 2574 and linked_agents == set(scored_agents), "Audit behavior member coverage mismatch")
        scored_slots = {r["slot_id"]: r for r in rows(self.output / "rescore/search_audit/slot_scalars.csv")}
        linked_pools = 0
        for row in rows(audit / "coordination/audit_pools.csv"):
            metrics = json.loads(scored_slots[row["slot_id"]]["metrics_json"])
            for metric in ["label_acc", "evidence_acc"]:
                require(math.isclose(float(row[metric]), metrics[metric + "_mv"], abs_tol=1e-12, rel_tol=0), "Audit pool/scorer mismatch")
            linked_pools += 1
        require(linked_pools == 468, "Audit behavior pool coverage mismatch")
        self.checks["audit_score_to_behavior_join"] = {"members": 2574, "pools": 468, "passed": True}
        whois = self.historical_component("whois")
        require(sha(whois / "inputs/formal_score_rows.csv") == sha(self.output / "rescore/sweep/agent_rows.csv"), "Whois analysis inputs differ from scorer-verified rows")
        self.checks["whois_score_to_analysis_join"] = {"slots": 1170, "byte_identical": True}
        self.run("whois_analysis_check", whois / "build_report.py", "--bundle", whois, "--check")
        rebuilt = self.output / "whois"
        self.run("whois_analysis_rebuild", whois / "build_report.py", "--bundle", whois, "--rebuild", rebuilt)
        self.compare(whois, rebuilt, self.csv_paths(whois, rebuilt), "whois_analysis")
        self.checks["behavior_scope"] = "Event/trajectory CSV fields, summaries and pairing populations are rebuilt from public primitives; private original prompts/actions are not reread. Figures are not included in byte comparisons."

    def verify_benchmarks(self):
        if not self.args.verify_benchmarks:
            self.checks["optional_full_benchmarks"] = {"executed": False, "reason": "Not requested; HPO default uses published measurement certificates."}
            return
        names = ["archive", "source_map", "versions", "paramnet_python", "benchmark_python", "hpobench_root", "benchmark_data"]
        require(all(getattr(self.args, name) is not None for name in names),
                "--verify-benchmarks requires " + ", ".join("--" + name.replace("_", "-") for name in names))
        env = dict(self.environment, HPOBENCH_ROOT=str(self.args.hpobench_root.resolve()), XDG_DATA_HOME=str(self.args.benchmark_data.resolve()))
        output = self.output / "full_benchmark_rescore"
        self.run("full_data_hpo_benchmarks", self.repo / "tools/rescore_hpo_protocol.py",
                 "--archive", self.args.archive, "--source-map", self.args.source_map, "--versions", self.args.versions,
                 "--paramnet-python", self.args.paramnet_python, "--output", output, "--verify-benchmarks",
                 python=self.args.benchmark_python, env=env)
        checks = read_json(output / "CHECKS.json")
        require(checks["benchmark_verification"] is True and checks["replay_mode"] == "full_immutable_trajectories", "Full benchmark mode did not reevaluate data")
        self.compare(self.bundle / "rescore/hpo", output, [p.name for p in sorted((self.bundle / "rescore/hpo").glob("*.csv"))], "full_hpo_benchmarks")
        self.checks["optional_full_benchmarks"] = {"executed": True, "fresh_evaluations": checks["unique_benchmark_evaluations"], "complete_checks": checks}

    def final_whois(self, final):
        preserved = self.bundle / "whois_existing_trace"
        require(preserved.is_dir(), "Final Whois must preserve whois_existing_trace separately")
        gate = self.checks["global_adoption_gate"]["manifest"]["sweep_control_gate"]
        sweep_inputs = self.bundle / "control_flow_adoption/sweep_rescore/scoring_inputs.jsonl.gz"
        require(sha(sweep_inputs) == gate["scoring_inputs_sha256"], "Sweep control inputs differ from the final gate")
        require(sha(sweep_inputs.parent / "COLLECTION_CHECKS.json") == gate["source_checks_sha256"],
                "Sweep collection identity differs from the final gate")
        require(gate.get("slot_id") == "whois:glm:beta20:phantom_seed2:5:R1"
                and gate.get("score_based_selection") is False and gate.get("actual_cost_ledger_verified_slots") == 1,
                "Sweep control registration or cost-evidence scope mismatch")
        output = self.output / "whois_official"
        self.run("whois_new_runtime_overlay", self.repo / "tools/build_whois_control_flow_overlay.py",
                 "--base-whois", preserved, "--existing-sweep", self.output / "rescore/sweep",
                 "--new-inputs", sweep_inputs,
                 "--output", output)
        whois = self.bundle / "whois"
        require(sha(whois / "slot_scalars.csv") == gate["official_scalar_sha256"]
                and sha(whois / "CHECKS.json") == gate["official_checks_sha256"], "Official Whois differs from global adoption identity")
        self.compare(whois, output, self.csv_paths(whois, output), "whois_official")
        self.compare(whois, output, ["README.zh.md", "CHECKS.json", "BETA10_MAIN_JOIN_CHECK.json"], "whois_official_documentation")
        official = {row["slot_id"]: row for row in rows(final / "slot_scalars.csv")}
        sources = {row["slot_id"]: row for row in rows(final / "SOURCE_SELECTION.csv")}
        overlap = [row for row in rows(output / "slot_scalars.csv") if row["main_overlap_slot_id"]]
        require(len(overlap) == 234, "Final Whois main overlap coverage mismatch")
        for row in overlap:
            key = row["main_overlap_slot_id"]
            require(row["source_sha256"] == sources[key]["result_sha256"], "Final Whois/main source mismatch")
            require(math.isclose(float(row["f1"]), json.loads(official[key]["metrics_json"])["f1"], rel_tol=0, abs_tol=1e-12), "Final Whois/main F1 mismatch")
        self.checks["official_whois"] = {"existing_terminals_replayed": 1170, "new_runtime_control_replayed": 1,
                                          "artifact": str(output), "full_benchmark_dataset_required": False}

    def full_adoption(self):
        if not self.args.full:
            self.checks["official_adoption"] = {"checked": False, "reason": "Component mode; does not certify HPO97 + Search/Audit21 + sweep1 final runtime adoption."}
            return
        gate = self.require_global_gate()
        global_adoption = self.bundle / "control_flow_adoption"
        global_manifest = global_adoption / "FAIRNESS_MANIFEST.json"
        sweep_gate = gate["sweep_control_gate"]
        require(sweep_gate.get("required") is True and sweep_gate.get("status") == "PASS"
                and sweep_gate.get("registered_slots") == sweep_gate.get("verified_slots") == 1,
                "Required sweep runtime control is incomplete")
        require(gate.get("hpo_stage_ready") is True and gate.get("auxiliary_stage_ready") is True,
                "A declared runtime stage is not ready")
        for key, expected in [("hpo_required_pools", 97), ("auxiliary_required_main_slots", 21), ("auxiliary_required_members", 78)]:
            require(gate.get(key) == expected, "Unexpected registered runtime control population")
        hpo_versions = self.bundle / "hpo_versions"
        self.run("hpo_public_version_tables", hpo_versions / "tools/verify_public_tables.py", "--package", hpo_versions,
                 "--output", self.output / "hpo_public_version_checks.json")
        self.checks["hpo_public_versions"] = "Package joins, frozen identities and declared evidence hashes checked; does not re-read private calls or validate auxiliary deployment by itself."
        aux_versions = self.bundle / "review/aux_controls"
        self.run("auxiliary_public_version_tables", aux_versions / "tools/verify_public_tables.py", "--package", aux_versions,
                 "--output", self.output / "auxiliary_public_version_checks.json")
        self.checks["auxiliary_public_versions"] = "Public registered configuration/source declarations checked; original prompt-equivalence and new execution evidence remain separate collector attestations."
        adoption = self.bundle / "rerun_adoption"
        hpo_manifest = adoption / "FAIRNESS_MANIFEST.json"
        manifest = read_json(hpo_manifest)
        require(manifest.get("status") == "PASS" and manifest.get("adoption_ready") is True
                and manifest.get("verified_complete_pools") == 97, "HPO stage is incomplete")
        require(sha(hpo_manifest) == gate["hpo_stage_manifest_sha256"], "Global gate binds a different HPO stage")
        hpo_rebuilt = self.output / "hpo_rebuilt_adoption"
        receipt = self.output / "rerun_public_replay.json"
        self.run("hpo_rerun_adoption", adoption / "replay_hpo_reruns.py", "--repo", self.repo,
                 "--adoption", adoption, "--base-scalars", self.output / "rescore/main/slot_scalars.csv",
                 "--base-sources", self.output / "rescore/main/SOURCE_SELECTION.csv", "--rebuild-output", hpo_rebuilt, "--output", receipt)
        replay = read_json(receipt)
        require(replay.get("completed_pools") == 97 and replay.get("completed_members") == 388,
                "HPO replay did not cover the complete registered stage")
        self.compare(adoption / "new_official", hpo_rebuilt, ["slot_scalars.csv", "SOURCE_SELECTION.csv"], "hpo_adoption")
        adopted_versions = self.output / "adopted_hpo_versions"
        self.run("hpo_adopted_code_versions", adoption / "build_adopted_versions.py",
                 "--historical-input", adoption / "historical_hpo_versions_input.csv",
                 "--adoption", adoption, "--output", adopted_versions)
        self.compare(adoption, adopted_versions,
                     ["adopted_hpo_code_versions.csv", "adopted_hpo_model_budget_strategy.csv", "ADOPTED_CODE_VERSION_CHECKS.json"],
                     "hpo_adopted_code_versions")
        self.checks["hpo_adopted_code_versions"] = {"slots": 810, "model_budget_strategy_groups": 54,
                                                    "source_hash_attestations_used": True,
                                                    "private_historical_source_trees_reopened": False}
        runtime_comparison = self.output / "hpo_runtime_comparison"
        self.run("hpo_runtime_score_comparison", adoption / "rebuild_runtime_comparison.py",
                 "--historical-scalars", self.output / "rescore/main/slot_scalars.legacy.csv",
                 "--rescored-scalars", self.output / "rescore/main/slot_scalars.csv",
                 "--runtime-scalars", hpo_rebuilt / "completed_slot_scalars.csv",
                 "--adoption", adoption, "--output", runtime_comparison)
        self.compare(adoption, runtime_comparison, ["NEW_RUNTIME_COMPARISON.csv"], "hpo_runtime_comparison")
        hpo_registered = {row["slot_id"] for row in rows(hpo_versions / "hpo_rerun_slots.csv")}
        hpo_completed = {row["slot_id"] for row in rows(hpo_rebuilt / "completed_slot_scalars.csv")}
        require(len(hpo_registered) == 97 and hpo_completed == hpo_registered, "HPO replay differs from the preregistered 97-slot set")
        aux = self.output / "auxiliary_runtime_rescore"
        aux_inputs = global_adoption / "aux_rescore/scoring_inputs.jsonl.gz"
        require(sha(aux_inputs) == gate["public_aux_scoring_inputs_sha256"], "Auxiliary input identity differs from final gate")
        self.run("auxiliary_runtime_parser_scorer", self.repo / "tools/replay_control_flow_results.py", "--inputs", aux_inputs, "--output", aux)
        self.compare(global_adoption / "aux_rescore", aux,
                     ["slot_scalars.csv", "agent_rows.csv", "sample_diff.csv", "SOURCE_INVENTORY.csv"], "auxiliary_runtime_scores")
        checks = read_json(aux / "CHECKS.json")
        require(checks.get("slots") == 21 and checks.get("members") == 78, "Auxiliary replay population mismatch")
        registration_path = self.bundle / "review/search_audit_control_flow/AFFECTED_WHOLE_SLOTS.csv"
        require(sha(registration_path) == gate["selection_csv_sha256"], "Auxiliary preregistration identity differs from total gate")
        registered_rows = rows(registration_path)
        registered = {row["slot_id"]: row for row in registered_rows}
        require(len(registered_rows) == len(registered) == 21 and sum(int(row["N"]) for row in registered_rows) == 78
                and sum(row["system"] == "expgym" for row in registered_rows) == 2,
                "Unexpected auxiliary preregistered whole-slot population")
        scored = {row["slot_id"]: row for row in rows(aux / "slot_scalars.csv")}
        new_sources = {row["slot_id"]: row for row in rows(aux / "SOURCE_INVENTORY.csv")}
        require(set(scored) == set(new_sources) == set(registered), "Auxiliary replays do not cover exactly the preregistered slots")
        members = rows(aux / "agent_rows.csv")
        for slot_id, registration in registered.items():
            require(new_sources[slot_id]["old_result_sha256"] == registration["trajectory_sha256"], "Auxiliary historical source differs from registration")
            for key in ["model", "system", "scenario", "regime", "strategy", "item", "outer_repeat", "order", "seed"]:
                require(scored[slot_id][key] == registration[key], "Auxiliary experiment identity differs from registration")
            selected_members = [row for row in members if row["slot_id"] == slot_id]
            expected_ids = {"-1"} if registration["system"] == "expgym" else {"0", "1", "2", "3"}
            require(len(selected_members) == int(registration["N"]) and {row["agent_id"] for row in selected_members} == expected_ids,
                    "Auxiliary whole-slot member identity mismatch")
        self.checks["runtime_preregistration_joins"] = {"hpo_slots": 97, "auxiliary_slots": 21, "auxiliary_members": 78,
                                                       "all_identified_before_scores": True}
        final = self.output / "final_adoption"
        self.run("global_source_assignment", self.repo / "tools/rebuild_control_flow_adoption.py",
                 "--hpo-stage", hpo_rebuilt, "--hpo-manifest", hpo_manifest, "--aux-dir", aux,
                 "--base-legacy-scalars", self.output / "rescore/main/slot_scalars.legacy.csv",
                 "--base-rescored-scalars", self.output / "rescore/main/slot_scalars.csv",
                 "--base-sources", self.output / "rescore/main/SOURCE_SELECTION.csv",
                 "--total-manifest", global_manifest, "--output", final)
        self.compare(global_adoption / "new_official", final,
                     self.csv_paths(global_adoption / "new_official", final), "global_adoption")
        final_rows = rows(final / "slot_scalars.csv")
        require(len(final_rows) == len({row["slot_id"] for row in final_rows}) == 4698, "Incomplete final main adoption")
        self.final_audit(final, aux)
        self.final_whois(final)
        self.final_analysis(final)
        self.checks["official_adoption"] = {"checked": True, "main_slots": 4698, "hpo_rerun_pools": 97,
                                             "auxiliary_main_slots": 21, "auxiliary_members": 78, "additional_sweep_slots": 1,
                                             "derivation": "Public terminal scoring -> HPO stage reconstruction -> auxiliary source replacement -> final analysis/behavior/score-layer rebuild"}

    def execute(self):
        self.preflight()
        if self.args.full:
            self.require_global_gate()
        before = inventory(self.bundle)
        source_before = {directory: inventory(self.repo / directory) for directory in ["expgym", "tools"]}
        self.scorer_components()
        self.behavior_components()
        self.verify_benchmarks()
        self.full_adoption()
        require(before == inventory(self.bundle), "Published bundle changed during verification")
        require(source_before == {directory: inventory(self.repo / directory) for directory in ["expgym", "tools"]}, "Scorer/replay source changed during verification")
        return {"status": "PASS", "mode": "full" if self.args.full else "components", "model_calls": 0,
                "published_files_unchanged": len(before), "repo": str(self.repo), "bundle": str(self.bundle),
                "python": str(self.args.python), "python_version": sys.version, "checks": self.checks,
                "source_file_sha256": source_before, "verifier_sha256": sha(Path(__file__)),
                "commands": self.commands, "byte_comparisons": self.comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--output", type=Path, help="New empty verification directory; defaults to a fresh system temporary directory")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--components", action="store_true", help="Verify all completed public components (default)")
    modes.add_argument("--full", action="store_true", help="Also require final adoption/fairness and final analysis rebuild")
    parser.add_argument("--verify-benchmarks", action="store_true", help="Optional full immutable-trajectory/frozen-benchmark reevaluation; never certificate-only")
    for name in ["archive", "source-map", "versions", "paramnet-python", "benchmark-python", "hpobench-root", "benchmark-data"]:
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    require(not sys.flags.optimize, "Do not use python -O; child replay tools use explicit scientific assertions")
    output = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix="protocol-repair-verify-"))
    require(not output.exists() or not any(output.iterdir()), "--output must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    verifier = Verification(args, output)
    try:
        result = verifier.execute()
    except Exception as error:
        result = {"status": "FAIL", "error": str(error), "commands": verifier.commands,
                  "checks": verifier.checks, "byte_comparisons": verifier.comparisons}
        (output / "VERIFICATION.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(f"FAIL: {error}\nReceipt: {output / 'VERIFICATION.json'}", file=sys.stderr)
        return 1
    (output / "VERIFICATION.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"PASS ({result['mode']}): {output / 'VERIFICATION.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
