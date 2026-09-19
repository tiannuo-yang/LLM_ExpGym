#!/usr/bin/env python3
"""Verify the selected PoolAct rollback and rebuild its public analyses offline.

This is an adoption and analysis check, not a claim of model calls or fresh
scoring of the private original trajectories. The 2026-09-18 protocol-repair
delivery is preserved as historical evidence and has its own pinned verifier.
Only Python's standard library and files shipped in the checkout are needed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


BASELINE_COMMIT = "7776f700902db194c69124b1a5f59d985379cfb3"
BUNDLE = Path("results/poolact-rollback-20260919")
CURRENT = Path("results/protocol-repair-20260918")
PRE_REPAIR = Path("results/gemini-openrouter-20260917")
REQUIRED_CODE = {
    "expgym/tool_protocol.py": "6b09495845fa6c1dc324a82ba471bcfba59265aaa4912ff0acf8307239e84bed",
    "expgym/task_evidence_audit.py": "54927bb505e4853fbee8898b788a31c5645367427d91918a9e42296fbc87930a",
    "expgym/task_restricted_search.py": "9e92858b4202e544e889a66b4b2c3887e2331a97610f1e287ebc62684b332819",
    "expgym/poolact.py": "3638b3f75fc253e6a971c409e116fc352512984bccb24892d3d62a6d7fc834d2",
    "expgym/extras/parallel_cache.py": "e5600eeef5389551cdf2761ccae716f5378c40e3443c8d1fe354f1cf2b53bcfa",
    "expgym/extras/aggregation_diagnostics.py": "2579504061d06bb8e4d2ad853b6bce9989f2bf27e136a5b2bc2d2b0a15d35220",
    "expgym/poolact_legacy_tool_protocol.py": "60dbe2f9391ac3afcc29991a2e1dc498eef9ff0f076d072bfac5b422b4cd139d",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_rows(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def indexed(values, label):
    answer = {row["slot_id"]: row for row in values}
    require(len(answer) == len(values), label + ": duplicate slot IDs")
    return answer


def files(root):
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }


def verify_selected_rows(current, old, selected, current_sources, old_sources, selected_sources):
    """Independently validate row-level policy; no builder helper is imported."""
    maps = [indexed(rows, label) for rows, label in [
        (current, "current scalars"), (old, "old scalars"),
        (selected, "selected scalars"), (current_sources, "current sources"),
        (old_sources, "old sources"), (selected_sources, "selected sources")]]
    now, before, new, now_source, old_source, new_source = maps
    require(len(now) == 4698, "Expected the frozen 4,698-slot main population")
    require(all(set(value) == set(now) for value in maps), "Slot coverage differs between input/output layers")
    counts = Counter()
    prior_runtime_changes = Counter()
    metric_changes = Counter()
    for slot_id, prior in now.items():
        system = prior["system"]
        require(system in {"expgym", "poolact"}, "Unexpected system: " + system)
        require(before[slot_id]["system"] == system, "System identity changed: " + slot_id)
        expected = prior if system == "expgym" else before[slot_id]
        require(new[slot_id] == expected, "Selected scalar row differs from required source: " + slot_id)
        expected_source = now_source[slot_id] if system == "expgym" else old_source[slot_id]
        for key, value in expected_source.items():
            require(new_source[slot_id].get(key) == value,
                    "Selected source field differs: " + slot_id + ":" + key)
        if system == "poolact":
            # Current-run-only provenance must not survive on an old N4 result.
            for key in set(now_source[slot_id]) - set(expected_source):
                require(new_source[slot_id].get(key, "") == "",
                        "Withdrawn runtime provenance still attached to N4: " + slot_id + ":" + key)
        counts[system] += 1
        if now_source[slot_id]["result_sha256"] != old_source[slot_id]["result_sha256"]:
            prior_runtime_changes[system] += 1
            require(new_source[slot_id]["result_sha256"] == expected_source["result_sha256"],
                    "Fresh runtime retention/withdrawal mismatch: " + slot_id)
        if json.loads(prior["metrics_json"]) != json.loads(new[slot_id]["metrics_json"]):
            metric_changes[system] += 1
    require(counts == {"expgym": 2502, "poolact": 2196}, "N1/N4 population mismatch")
    require(prior_runtime_changes == {"expgym": 2, "poolact": 116}, "Runtime control scope mismatch")
    require(metric_changes["expgym"] == 0, "N1 score changed during rollback")
    completion = Counter(
        (row["system"], row["selection"])
        for row in new_source.values() if row["selection"] == "new_missing_slot")
    require(completion == {("expgym", "new_missing_slot"): 6,
                           ("poolact", "new_missing_slot"): 10},
            "The pre-existing Gemini completion slots were not preserved")
    return {"main_slots": len(new), "n1_rows_retained": counts["expgym"],
            "n4_rows_restored": counts["poolact"],
            "new_runtime_n4_sources_withdrawn": prior_runtime_changes["poolact"],
            "new_runtime_n1_sources_retained": prior_runtime_changes["expgym"],
            "n1_metric_rows_changed": metric_changes["expgym"],
            "n4_metric_rows_changed_from_7776": metric_changes["poolact"],
            "gemini_completion_n1_slots_retained": 6,
            "gemini_completion_n4_slots_retained": 10}


class Verification:
    def __init__(self, repo, output, python):
        self.repo, self.output, self.python = repo.resolve(), output.resolve(), python
        self.bundle = self.repo / BUNDLE
        self.checks, self.comparisons, self.commands = {}, [], []

    def scientific_sources(self):
        for relative, expected in REQUIRED_CODE.items():
            require(sha(self.repo / relative) == expected, "Scientific policy source mismatch: " + relative)
        manifest_path = self.bundle / "review/CODE_SOURCE_MANIFEST.json"
        manifest = read_json(manifest_path)
        require(manifest["status"] == "PASS", "Current code source manifest is incomplete")
        require(manifest["n4_policy"] == "poolact-answer-297c3d0"
                and manifest["n1_default_policy"] == "final-answer-boundary-v2",
                "Code policy manifest does not distinguish N1 and N4")
        for item in manifest["files"]:
            require(sha(self.repo / item["path"]) == item["sha256"],
                    "Current code differs from reviewed source: " + item["path"])
        for item in manifest["unchanged_single_agent_files"]:
            require(sha(self.repo / item["path"]) == item["sha256"],
                    "Single-agent source changed: " + item["path"])
        for relative in manifest["removed_root_v4_tests"]:
            require(not (self.repo / relative).exists(), "Withdrawn current-version test is still present: " + relative)
        source_paths = []
        for directory in ["expgym", "scripts", "schemas", "tests"]:
            source_paths.extend(path for path in (self.repo / directory).rglob("*")
                                if path.is_file() and "__pycache__" not in path.parts
                                and path.suffix.lower() in {".py", ".sh", ".json", ".yaml", ".yml", ".md"})
        source_paths.append(self.repo / "demo_experiment.py")
        digest = hashlib.sha256()
        for path in sorted(source_paths):
            digest.update(path.relative_to(self.repo).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
        require(digest.hexdigest() == manifest["source_tree_sha256"],
                "Current runtime/scripts/schemas/tests tree differs from reviewed code")
        self.checks["scientific_sources"] = {
            "manifest_sha256": sha(manifest_path), "reviewed_files": len(manifest["files"]),
            "runtime_source_files": len(source_paths), "source_tree_sha256": digest.hexdigest(),
            "independently_bound_original_file_hashes": REQUIRED_CODE,
            "n1_default_policy": manifest["n1_default_policy"], "n4_policy": manifest["n4_policy"]}

    def preservation(self):
        manifest_path = self.bundle / "verification/BASELINE_INPUTS.json"
        manifest = read_json(manifest_path)
        require(manifest["baseline_commit"] == BASELINE_COMMIT, "Wrong preservation baseline")
        listed = {item["path"]: item for item in manifest["files"]}
        require(len(listed) == manifest["file_count"] == 854, "Preservation inventory coverage changed")
        actual = {}
        for relative in manifest["roots"]:
            root = self.repo / relative
            require(root.is_dir(), "Missing preserved evidence: " + relative)
            actual.update({str(Path(relative) / name): path for name, path in files(root).items()})
        require(set(actual) == set(listed), "Preserved evidence file set differs from baseline")
        for name, path in actual.items():
            item = listed[name]
            require(path.stat().st_size == item["bytes"] and sha(path) == item["sha256"],
                    "Historical evidence changed: " + name)
        self.checks["historical_evidence"] = {
            "baseline_commit": BASELINE_COMMIT, "files": len(listed),
            "manifest_sha256": sha(manifest_path), "git_access_required": False,
            "all_published_historical_bytes_unchanged": True}

    def selection(self):
        def scalar(root): return read_rows(self.repo / root / "main/slot_scalars.csv")
        def source(root): return read_rows(self.repo / root / "main/SOURCE_SELECTION.csv")
        selected = self.bundle / "selection"
        self.checks["selection"] = verify_selected_rows(
            scalar(CURRENT), scalar(PRE_REPAIR), read_rows(selected / "slot_scalars.csv"),
            source(CURRENT), source(PRE_REPAIR), read_rows(selected / "SOURCE_SELECTION.csv"))
        # The published main inputs must be the same selected rows, including order.
        for name in ["slot_scalars.csv", "SOURCE_SELECTION.csv"]:
            require(sha(selected / name) == sha(self.bundle / "main" / name),
                    "Published main differs from selection: " + name)
        gate = read_json(selected / "ROLLBACK_MANIFEST.json")
        require(gate.get("status") == "PASS", "Rollback selection gate is incomplete")
        require(gate.get("schema") != "expgym.total-runtime-adoption.v1",
                "Rollback must not reuse the former 97-pool adoption gate")
        self.checks["rollback_manifest_sha256"] = sha(selected / "ROLLBACK_MANIFEST.json")

    def retained_single_agent_analyses(self):
        hpo = self.repo / CURRENT / "hpo_behavior/official_rescored486/trajectories.csv"
        traces = read_rows(hpo)
        require(len(traces) == 486, "HPO N1 behavior must retain 486 rows")
        require(Counter(row["regime"] for row in traces) ==
                {"cost_free": 162, "cost_moderate": 162, "cost_tight": 162},
                "HPO N1 per-budget coverage differs")
        sweep = self.repo / CURRENT / "whois"
        rows = read_rows(sweep / "SOURCE_SELECTION.csv")
        require(len(rows) == 1170, "Whois N1 sweep must retain 1,170 rows")
        replaced = [row for row in rows if row["runtime_source_replaced"] == "True"]
        require(len(replaced) == 1 and replaced[0]["slot_id"] == "whois:glm:beta20:phantom_seed2:5:R1",
                "The single-agent beta20 control must be retained")
        gate = read_json(self.repo / CURRENT / "control_flow_adoption/SWEEP_CONTROL_GATE.json")
        require(replaced[0]["result_sha256"] == gate["new_result_sha256"],
                "Retained sweep source mismatch")
        self.checks["retained_single_agent_analyses"] = {
            "hpo_behavior_rows": 486, "hpo_rows_per_budget": 162,
            "whois_sweep_slots": 1170, "sweep_runtime_controls_retained": 1,
            "hpo_trajectory_table_sha256": sha(hpo),
            "sweep_source_selection_sha256": sha(sweep / "SOURCE_SELECTION.csv")}

    def rebuild(self):
        script = self.bundle / "tools/rebuild_rollback.py"
        rebuilt = self.output / "rebuild"
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment.pop("PYTHONOPTIMIZE", None)
        command = [str(self.python), "-B", str(script), "--repo", str(self.repo),
                   "--output", str(rebuilt)]
        start = time.monotonic()
        completed = subprocess.run(command, cwd=self.repo, env=environment,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log = self.output / "rebuild.log"
        log.write_text(completed.stdout, encoding="utf-8")
        self.commands.append({"name": "rebuild_rollback", "argv": command,
                              "returncode": completed.returncode,
                              "seconds": round(time.monotonic() - start, 3),
                              "script_sha256": sha(script), "log_sha256": sha(log)})
        require(completed.returncode == 0, "Public rebuild failed; see " + str(log))
        generated = files(rebuilt)
        require(len(generated) >= 50, "Public rebuild returned too few outputs")
        for name, replay in generated.items():
            relative = Path(name)
            if relative.parts[0] == "docs":
                published = (self.repo / "results/paper-analysis-20260916" / relative.name
                             if relative.name in {"README.zh.md", "APPENDIX.zh.md", "ABSTRACT.en.md"}
                             else self.bundle / relative.name)
            else:
                published = self.bundle / relative
            require(published.is_file(), "Missing published rebuilt output: " + str(published.relative_to(self.repo)))
            require(sha(published) == sha(replay), "Rebuild byte mismatch: " + name)
            self.comparisons.append({"path": str(published.relative_to(self.repo)),
                                     "rebuild_path": name, "sha256": sha(published),
                                     "byte_identical": True})
        for component in ["selection", "main", "display", "search", "poolact", "cases", "audit"]:
            expected_csv = {name for name in files(self.bundle / component) if name.endswith(".csv")}
            actual_csv = {name for name in files(rebuilt / component) if name.endswith(".csv")}
            require(expected_csv == actual_csv, "Published/rebuilt CSV set differs: " + component)
        self.checks["rebuilt_products"] = len(self.comparisons)
        self.checks["rebuild_scope"] = {
            "model_calls": 0, "network_required": False, "git_required": False,
            "private_trajectory_files_required": False,
            "fresh_all_original_trajectory_rescoring": False,
            "operation": "Select frozen score/source rows by system, recompute public analyses and render report"}

    def run(self):
        self.scientific_sources()
        print("PASS isolated N1/N4 scientific sources", flush=True)
        self.preservation()
        print("PASS historical preservation", flush=True)
        self.selection()
        print("PASS row-level N1/N4 selection", flush=True)
        self.retained_single_agent_analyses()
        print("PASS retained HPO486 and Whois1170", flush=True)
        self.rebuild()
        print("PASS offline analysis/report rebuild", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="new or empty directory for rebuild and receipt")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix="expgym-poolact-rollback-verify-"))
    require(not output.exists() or (output.is_dir() and not any(output.iterdir())),
            "--output must be a new or empty directory")
    output.mkdir(parents=True, exist_ok=True)
    require(not output.resolve().is_relative_to((args.repo / BUNDLE).resolve()),
            "Output must not be inside the public rollback bundle")
    verify = Verification(args.repo, output, args.python)
    status, error = "PASS", None
    try:
        verify.run()
    except Exception as exc:
        status, error = "FAIL", str(exc)
    receipt = {"schema": "expgym.poolact-rollback-verification.v1", "status": status,
               "verifier_sha256": sha(Path(__file__)), "baseline_commit": BASELINE_COMMIT,
               "checks": verify.checks, "comparisons": verify.comparisons,
               "commands": verify.commands}
    if error:
        receipt["error"] = error
    target = output / "VERIFICATION.json"
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status + ": " + str(target), flush=True)
    if error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
