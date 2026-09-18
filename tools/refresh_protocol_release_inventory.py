#!/usr/bin/env python3
"""Refresh release identities after staging a complete protocol-repair delivery.

This does not run models or scores. It refuses pending rerun adoption, changes to
the frozen ad03 exports, or changes to the committed scientific core. Stage the
intended public files first; the Git index defines the publication inventory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess


CORE = "0e6c51b6d86f42437038518c2fc8adc510901c0b"
RUNTIME = "ffca5704580b75e254f6e52dd4fe9dff104b1be8"
DEEPSEEK_RUNTIME = "885a5bd70dffe02b8dd610f1699e9f675da2b926"
INTERIM = "2a78fc8ef0d0882d0e94080f0bbfec1fc789946a"
BASE = "297c3d00a006f33fc5a8ca799ce91d327d92839e"
REPAIR = "results/protocol-repair-20260918"
MANIFEST = "LIGHTWEIGHT_MANIFEST.json"
SUMS = "SHA256SUMS"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.repo.resolve()
    manifest = json.loads((root / MANIFEST).read_text())
    fairness_path = root / REPAIR / "control_flow_adoption/FAIRNESS_MANIFEST.json"
    fairness = json.loads(fairness_path.read_text())
    require(fairness.get("status") == "PASS" and fairness.get("adoption_ready") is True,
            "Refusing publication: unified runtime adoption is not ready")
    require(fairness.get("total_main_runtime_adoption") is True
            and fairness.get("hpo_verified_pools") == 97
            and fairness.get("auxiliary_verified_main_slots") == 21,
            "Expected all 97 HPO pools and 21 Search/Audit main controls")
    hpo_path = root / REPAIR / "rerun_adoption/FAIRNESS_MANIFEST.json"
    hpo = json.loads(hpo_path.read_text())
    require(hpo.get("status") == "PASS" and hpo.get("adoption_ready") is True
            and hpo.get("verified_complete_pools") == 97
            and hpo.get("verified_complete_members") == 388,
            "The HPO stage must independently validate all 97 pools / 388 members")
    scalars_path = root / REPAIR / "main/slot_scalars.csv"
    source_path = root / REPAIR / "main/SOURCE_SELECTION.csv"
    scalars = read_csv(scalars_path)
    sources = read_csv(source_path)
    require(len(scalars) == 4698 and len({r["slot_id"] for r in scalars}) == 4698,
            "Expected all 4698 unique formal main slots")
    require({r["slot_id"] for r in sources} == {r["slot_id"] for r in scalars}
            and len(sources) == 4698, "Formal source selection must cover exactly all slots")
    require(digest(scalars_path) == digest(root / REPAIR / "control_flow_adoption/new_official/slot_scalars.csv"),
            "Published main scores differ from the final combined runtime adoption")
    freeze = json.loads((root / REPAIR / "review/PARSER_CODE_FREEZE.json").read_text())
    for path, expected in freeze["source_sha256"].items():
        require(digest(root / path) == expected, "Frozen code changed: " + path)
    for row in manifest["frozen_exports"]:
        require(digest(root / row["path"]) == row["sha256"],
                "Historical frozen export changed: " + row["path"])
    for name in ("README.zh.md", "APPENDIX.zh.md", "ABSTRACT.en.md", "MANIFEST.json", "REVIEW.zh.md"):
        bits = name.split(".", 1)
        archive = bits[0] + ".pre-repair-297c3d0." + bits[1]
        relative = "results/paper-analysis-20260916/" + name
        historical = subprocess.check_output(["git", "-C", str(root), "show", BASE + ":" + relative])
        require((root / "results/paper-analysis-20260916" / archive).read_bytes() == historical,
                "Historical pre-repair document changed: " + archive)
    paths = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"]).decode().split("\0")
    paths = sorted(p for p in paths if p and p not in {MANIFEST, SUMS})
    require(any(p.startswith(REPAIR + "/") for p in paths), "Stage the repair delivery first")
    inventory = []
    for path in paths:
        local = root / path
        require(local.is_file() and not local.is_symlink(), "Invalid release file: " + path)
        inventory.append({"path": path, "bytes": local.stat().st_size, "sha256": digest(local)})
    manifest["historical_source_code_commit"] = manifest.get("historical_source_code_commit", manifest["source_code_commit"])
    manifest["source_code_commit"] = CORE
    manifest["runtime_code_commit"] = RUNTIME
    manifest["deepseek_audit_runtime_code_commit"] = DEEPSEEK_RUNTIME
    manifest["parent_commit"] = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"]).decode().strip()
    manifest["scope"] = "Full protocol repair and all-slot rescoring, with 97 validated HPO whole-pool replacements and 21 Search/Audit runtime controls. All reruns use the frozen repaired parser/graph core and preserve their historical task prompts. Frozen ad03 files and pre-repair report archives retain their original bytes and historical score meaning."
    manifest["files"] = inventory
    previous_report = manifest.get("current_report", {})
    manifest["current_report"] = {
        "path": "results/paper-analysis-20260916/README.zh.md",
        "update_date": "2026-09-18",
        "base_main_commit": BASE,
        "scoring_layer": "new_official",
        "final_runtime_adoption_ready": True,
        "interim_main_commit_preserved": INTERIM,
        "completed_slots": sum(r["execution_complete"].lower() == "true" for r in scalars),
        "strict_score_complete": sum(r["score_complete"].lower() == "true" for r in scalars),
        "source_selection": str(source_path.relative_to(root)),
        "source_selection_sha256": digest(source_path),
        "slot_scalars": str(scalars_path.relative_to(root)),
        "slot_scalars_sha256": digest(scalars_path),
        "fairness_manifest": str(fairness_path.relative_to(root)),
        "fairness_manifest_sha256": digest(fairness_path),
        "hpo_runtime_source_tree_sha256": hpo["runtime_source_tree_sha256"],
        "hpo_rerun_pools": 97,
        "hpo_rerun_members": 388,
        "additional_main_runtime_slots": 21,
        "additional_sweep_runtime_slots": fairness.get("sweep_additional_slots", 0),
        "hpo_single_agent_behavior_rows": 486,
        "frozen_document_remaps": previous_report.get("frozen_document_remaps", []),
        "historical_pre_repair_document_suffix": ".pre-repair-297c3d0.*",
    }
    manifest["protocol_repair"] = {
        "entry": REPAIR + "/README.zh.md",
        "all_score_layers": REPAIR + "/score_layers/README.zh.md",
        "original_frozen_counts_unchanged": True,
        "current_source_commit_is_scientific_core": True,
        "runtime_source_location": "studies/protocol-repair-20260918/runtime",
        "deepseek_audit_runtime_source_location": "studies/protocol-repair-20260918/runtime-deepseek-audit",
        "raw_api_archives_and_full_trajectories": "local archive only",
    }
    (root / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sums = {row["path"]: row["sha256"] for row in inventory}
    sums[MANIFEST] = digest(root / MANIFEST)
    (root / SUMS).write_text("".join(f"{value}  {key}\n" for key, value in sorted(sums.items())), encoding="utf-8")
    print(json.dumps({"status": "PASS", "files": len(inventory), "completed_slots": manifest["current_report"]["completed_slots"], "strict_score_complete": manifest["current_report"]["strict_score_complete"]}))


if __name__ == "__main__":
    main()
