#!/usr/bin/env python3
"""Record a staged N4 rollback without altering the archived repair delivery."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

FROZEN = "7776f700902db194c69124b1a5f59d985379cfb3"
BASE = "297c3d00a006f33fc5a8ca799ce91d327d92839e"
PACKAGE = "results/poolact-rollback-20260919"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        result = list(csv.DictReader(stream))
    assert len({r["slot_id"] for r in result}) == len(result)
    return {r["slot_id"]: r for r in result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    assert subprocess.check_output(["git", "-C", str(repo), "cat-file", "-t", args.code_commit]).strip() == b"commit"
    manifest_path = repo / "LIGHTWEIGHT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    old_manifest = json.loads(subprocess.check_output(["git", "-C", str(repo), "show", FROZEN + ":LIGHTWEIGHT_MANIFEST.json"]))
    scalar_path = repo / PACKAGE / "main/slot_scalars.csv"
    source_path = repo / PACKAGE / "main/SOURCE_SELECTION.csv"
    current, current_sources = rows(scalar_path), rows(source_path)
    retained = rows(repo / "results/protocol-repair-20260918/main/slot_scalars.csv")
    restored = rows(repo / "results/gemini-openrouter-20260917/main/slot_scalars.csv")
    retained_sources = rows(repo / "results/protocol-repair-20260918/main/SOURCE_SELECTION.csv")
    restored_sources = rows(repo / "results/gemini-openrouter-20260917/main/SOURCE_SELECTION.csv")
    assert len(current) == len(current_sources) == 4698
    assert current.keys() == retained.keys() == restored.keys() == current_sources.keys()
    counts = {"expgym": 0, "poolact": 0}
    for sid, row in current.items():
        system = row["system"]
        expected = retained[sid] if system == "expgym" else restored[sid]
        expected_source = retained_sources[sid] if system == "expgym" else restored_sources[sid]
        for key, value in expected.items():
            assert row[key] == value, (sid, key, "unexpected scalar alteration")
        for key in ("result_sha256", "historical_trajectory", "new_result_index", "provider", "cohort_id"):
            assert current_sources[sid][key] == expected_source[key], (sid, key, "unexpected source alteration")
        counts[system] += 1
    assert counts == {"expgym": 2502, "poolact": 2196}, counts
    for entry in old_manifest["files"]:
        if entry["path"].startswith(("results/protocol-repair-20260918/", "studies/protocol-repair-20260918/")):
            assert sha(repo / entry["path"]) == entry["sha256"], ("archived repair changed", entry["path"])
    for entry in manifest["frozen_exports"]:
        assert sha(repo / entry["path"]) == entry["sha256"], ("historical ad03 export changed", entry["path"])
    archive = json.loads((repo / PACKAGE / "review/HISTORICAL_REPORT_ARCHIVES.json").read_text())
    for entry in archive["files"]:
        assert sha(repo / entry["path"]) == entry["sha256"]
    paths = sorted(p for p in subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z"]).decode().split("\0") if p and p not in {"LIGHTWEIGHT_MANIFEST.json", "SHA256SUMS"})
    inventory = []
    for name in paths:
        path = repo / name
        assert path.is_file() and not path.is_symlink(), name
        inventory.append({"path": name, "bytes": path.stat().st_size, "sha256": sha(path)})
    manifest["files"] = inventory
    manifest["source_code_commit"] = args.code_commit
    manifest["parent_commit"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    manifest["scope"] = "Retain repaired N1 results and restore every N4 strategy, score and source to the Gemini-complete pre-repair baseline. Preserve withdrawn repair results and frozen runtimes as historical artifacts. No new model runs."
    manifest["historical_protocol_repair"] = {
        "release_commit": FROZEN,
        "prior_current_report": old_manifest["current_report"],
        "source_code_commit": old_manifest["source_code_commit"],
        "runtime_code_commit": old_manifest.get("runtime_code_commit"),
        "deepseek_audit_runtime_code_commit": old_manifest.get("deepseek_audit_runtime_code_commit"),
        "status": "N4 adoption withdrawn; N1 adoption retained",
    }
    manifest.pop("runtime_code_commit", None)
    manifest.pop("deepseek_audit_runtime_code_commit", None)
    manifest["protocol_repair"]["current_source_commit_is_scientific_core"] = False
    manifest["protocol_repair"]["reproduction_checkout"] = FROZEN
    manifest["protocol_repair"]["adoption_status"] = "Historical N4 candidate; retained N1 results"
    manifest["current_report"] = {
        "path": "results/paper-analysis-20260916/README.zh.md",
        "update_date": "2026-09-19",
        "scoring_layer": "n1_repaired_n4_restored",
        "rollback_complete": True,
        "completed_slots": sum(r["execution_complete"].lower() == "true" for r in current.values()),
        "strict_score_complete": sum(r["score_complete"].lower() == "true" for r in current.values()),
        "retained_single_agent_slots": 2502,
        "restored_multi_agent_slots": 2196,
        "poolact_baseline_commit": BASE,
        "retained_n1_release_commit": FROZEN,
        "slot_scalars": str(scalar_path.relative_to(repo)),
        "slot_scalars_sha256": sha(scalar_path),
        "source_selection": str(source_path.relative_to(repo)),
        "source_selection_sha256": sha(source_path),
        "hpo_single_agent_behavior_rows": 486,
        "entry": PACKAGE + "/README.zh.md",
        "frozen_document_remaps": old_manifest["current_report"].get("frozen_document_remaps", []),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    sums = {r["path"]: r["sha256"] for r in inventory}
    sums["LIGHTWEIGHT_MANIFEST.json"] = sha(manifest_path)
    (repo / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(sums.items())))
    print(json.dumps({"status": "PASS", "files": len(inventory), **counts, "completed_slots": manifest["current_report"]["completed_slots"]}))


if __name__ == "__main__":
    main()
