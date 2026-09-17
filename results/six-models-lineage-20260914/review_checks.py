"""Independent report-only checks against frozen 2026-09-13 exports.

Does not import the report generators, run scorers, read raw dumps, or call models.
"""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[3]
OLD = WORK / "all_model_report_20260913/report_v3"
MODELS = {
    "kimi-k3", "glm-5.3", "qwen3.8-2.4t-a95b-fp8",
    "deepseek-v4-flash-0731", "gpt-5.6-sol", "gemini-3.8-flash-medium",
}
SEEN = {}


def read(path):
    data = path.read_bytes()
    SEEN[str(path)] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return data.decode()


def rows(path):
    return list(csv.DictReader(read(path).splitlines()))


def js(path):
    return json.loads(read(path))


def fingerprint(row):
    return tuple(sorted(row.items()))


def main():
    out = {"scope": "independent frozen-export numerical and provenance review; no raw/scorer/model calls"}
    old_abs = rows(OLD / "absolute_settings.csv")
    selected = [r for r in old_abs if r["model"] in MODELS]
    preserved = {}
    for name in (
        "absolute_settings.csv", "by_repeat.csv", "contrasts.csv",
        "main_expgym.csv", "main_poolact.csv", "inherited_resources.csv",
        "SOURCE_SELECTION.csv", "SCORE_COMPLETENESS.csv",
    ):
        before = [r for r in rows(OLD / name) if r["model"] in MODELS]
        after = rows(ROOT / name)
        assert Counter(map(fingerprint, before)) == Counter(map(fingerprint, after)), name
        assert all(r["model"] in MODELS for r in after), name
        preserved[name] = len(after)
    out["exact_frozen_rows_preserved"] = preserved
    key_fields = ("model", "system", "scenario", "slice_kind", "slice", "regime", "strategy", "metric")
    index = {tuple(r[k] for k in key_fields): r for r in selected}
    assert len(index) == len(selected)

    def get(model, system, scenario, regime, strategy, metric, kind="all", item="all"):
        return index[(model, system, scenario, kind, item, regime, strategy, metric)]

    budget = {}
    for scenario, metric in [("restricted_search", "f1"), ("evidence_audit", "evidence_acc"), ("tuning", "gap0")]:
        deltas = {}
        for model in sorted(MODELS):
            f = get(model, "expgym", scenario, "cost_free", "single", metric)
            t = get(model, "expgym", scenario, "cost_tight", "single", metric)
            deltas[model] = float(t["full_mean"]) - float(f["full_mean"]) if f["full_mean"] and t["full_mean"] else None
        budget[scenario] = {"complete": sum(v is not None for v in deltas.values()),
                            "degraded": sum(v is not None and v < 0 for v in deltas.values()),
                            "unknown": sum(v is None for v in deltas.values()), "deltas": deltas}
    assert [(budget[s]["complete"], budget[s]["degraded"]) for s in budget] == [(6, 6), (6, 6), (5, 4)]
    out["independently_recomputed_budget"] = budget
    pool = []
    for model in sorted(MODELS):
        for scenario, metric in [("restricted_search", "f1_mv"), ("evidence_audit", "evidence_acc_mv"), ("tuning", "gap0_mi")]:
            for regime in ["cost_moderate", "cost_tight"]:
                vals = {s: get(model, "poolact", scenario, regime, s, metric)["full_mean"] for s in ["naive", "cached", "poolact"]}
                complete = all(vals.values())
                win = complete and float(vals["poolact"]) > max(float(vals["naive"]), float(vals["cached"]))
                pool.append({"model": model, "scenario": scenario, "regime": regime, "complete": complete, "wins_both": bool(win)})
    counts = {"planned": len(pool), "complete": sum(c["complete"] for c in pool), "wins_both": sum(c["wins_both"] for c in pool),
              "tight_complete": sum(c["complete"] and c["regime"] == "cost_tight" for c in pool),
              "tight_wins_both": sum(c["wins_both"] and c["regime"] == "cost_tight" for c in pool)}
    assert counts == {"planned": 36, "complete": 33, "wins_both": 29, "tight_complete": 17, "tight_wins_both": 16}
    out["independently_recomputed_poolact"] = counts
    out["nonwinning_complete_poolact_cells"] = [c for c in pool if c["complete"] and not c["wins_both"]]
    out["incomplete_poolact_cells"] = [c for c in pool if not c["complete"]]

    ranks = rows(ROOT / "family_rankings.csv")
    rank_index = {(r["family"], r["regime"], r["model"]): r for r in ranks}
    assert len(ranks) == len(rank_index) == 108
    winners = {}
    for family, scenario, metric in [("whois", "restricted_search", "f1"), ("whatis", "restricted_search", "f1"),
                                     ("evidence_audit", "evidence_audit", "evidence_acc"), ("paramnet", "tuning", "gap0"),
                                     ("nasbench101", "tuning", "gap0"), ("nasbench201", "tuning", "gap0")]:
        winners[family] = {}
        for regime in ["cost_free", "cost_moderate", "cost_tight"]:
            vals = {m: get(m, "expgym", scenario, regime, "single", metric, "family", family)["full_mean"] for m in MODELS}
            known = {m: float(v) for m, v in vals.items() if v}
            highest = max(known.values())
            top = sorted(m for m, v in known.items() if v == highest)
            for m in MODELS:
                row = rank_index[(family, regime, m)]
                assert row["full_mean"] == vals[m]
                assert int(row["planned_candidates"]) == 6 and int(row["known_candidates"]) == len(known)
                assert (row["overall_winner"] == "True") == (len(known) == 6 and m in top)
            winners[family][regime] = {"known_candidates": len(known), "known_highest": top, "complete": len(known) == 6}
    complete = [f for f, w in winners.items() if w["cost_free"]["complete"] and w["cost_tight"]["complete"]]
    reshuffled = [f for f in complete if winners[f]["cost_free"]["known_highest"] != winners[f]["cost_tight"]["known_highest"]]
    assert len(complete) == 4 and set(reshuffled) == {"whois", "whatis", "nasbench201"}
    out["independently_recomputed_ranking"] = {"complete_free_tight_families": complete, "winner_changed": reshuffled, "families": winners}
    transitions = rows(ROOT / "rank_transitions.csv")
    for row in transitions:
        assert set(row["eligible_models"].split(";")) <= MODELS
        assert set(filter(None, row["excluded_models"].split(";"))) <= MODELS

    score = rows(ROOT / "SCORE_COMPLETENESS.csv")
    lineage = rows(ROOT / "DATA_LINEAGE.csv")
    score_fields = list(score[0])
    assert Counter(map(fingerprint, score)) == Counter(fingerprint({k: r[k] for k in score_fields}) for r in lineage)
    assert len(lineage) == 162
    planned = sum(int(r["planned_logical_jobs"]) for r in score)
    scored = sum(int(r["fully_scored_logical_jobs"]) for r in score)
    assert (planned, scored) == (4698, 4671)
    model_counts = {}
    for model in sorted(MODELS):
        selected_score = [r for r in score if r["model"] == model]
        model_counts[model] = {"planned": sum(int(r["planned_logical_jobs"]) for r in selected_score),
                               "strict_scored": sum(int(r["fully_scored_logical_jobs"]) for r in selected_score)}
    integrity = js(WORK / "gemini_usability_review_20260914/integrity/CURRENT_INTEGRITY.json")
    assert integrity["status_counts"] == {"completed": 767, "failed": 1, "incomplete_started": 1, "unstarted": 14}
    assert integrity["checks"]["canonical_same_as_snapshot"] == 767 and not integrity["changed_slots"]
    assert 5 * 783 + integrity["status_counts"]["completed"] == 4682
    out["logical_counts"] = {"planned": planned, "executed_complete": 4682, "strict_scored": scored, "by_model": model_counts,
                              "gemini_status_observed_at_utc": integrity["observed_at_utc"], "gemini_status": integrity["status_counts"]}
    source = js(ROOT / "SOURCE_INDEX.json")
    cohorts = {c["id"]: c for c in source["cohorts"]}
    assert len(cohorts) == 10 and {r["cohort_id"] for r in lineage} == set(cohorts)
    old_catalog = js(WORK / "all_model_report_20260913/catalog/SOURCE_INDEX.json")
    old_cohorts = {c["id"]: c for c in old_catalog["cohorts"]}
    assert all(c == old_cohorts[cid] for cid, c in cohorts.items())
    reruns = defaultdict(list)
    source_jobs = Counter()
    for r in lineage:
        source_jobs[r["cohort_id"]] += int(r["planned_logical_jobs"])
        if "rerun_20260912" in r["cohort_id"]:
            assert r["system"] == "poolact"
            reruns[(r["model"], r["scenario"], r["regime"])].append(r)
    assert len(reruns) == 9
    for cell in reruns.values():
        assert {r["strategy"] for r in cell} == {"naive", "cached", "poolact"} and len(cell) == 3
    assert sum(sum(int(r["planned_logical_jobs"]) for r in cell) for cell in reruns.values()) == 369
    assert {k: v for k, v in source_jobs.items() if "rerun" in k} == {
        "kimi_rerun_20260912": 27, "glm_rerun_20260912": 66,
        "deepseek_rerun_20260912": 249, "gpt_rerun_20260912": 27,
    }
    out["lineage"] = {"settings": len(lineage), "cohorts": len(cohorts), "rerun_three_strategy_cells": len(reruns),
                       "replacement_pools": 369, "planned_jobs_by_cohort": dict(source_jobs),
                       "all_cohort_metadata_exactly_inherited_from_frozen_catalog": True}
    archive = js(ROOT / "ARCHIVE_INDEX.json")
    assert set(archive["models"]) == MODELS
    assert {c["cohort_id"] for c in archive["cohort_entry_points"]} | {archive["gemini_snapshot"]["id"]} == set(cohorts)
    entries = {c["cohort_id"]: c for c in archive["cohort_entry_points"]}
    assert entries["gpt_original"]["raw_entry_url"] is None
    assert archive["gemini_snapshot"]["full_source_index_path"].startswith(str(WORK))
    assert "local" in entries["gpt_original"]["raw_visibility"]
    out["archive_scope"] = "9 cohort_entry_points plus a separate Gemini snapshot entry cover 10 cohorts; original GPT and complete Gemini raw local only; published identities inherited, payload not reverified"
    claimed = js(ROOT / "REPORT_CHECKS.json")
    assert claimed["claims"]["poolact"] == counts
    history = js(ROOT / "EXPERIMENT_LOG.json")
    history_rows = rows(ROOT / "EXPERIMENT_LOG.csv")
    history_source = []
    for name in ["selfserve_history.json", "api_history.json"]:
        history_source.extend(js(WORK / "six_model_report_20260914/history" / name))
    original_events = {r["event_id"]: r for r in history_source}
    events = {r["event_id"]: r for r in history["events"]}
    csv_events = {r["event_id"]: r for r in history_rows}
    assert len(events) == len(history["events"]) == len(history_rows) == len(original_events) == 72
    assert events.keys() == original_events.keys() == csv_events.keys()
    for eid, original in original_events.items():
        assert all(events[eid][key] == value for key, value in original.items()), eid
        assert json.loads(csv_events[eid]["models"]) == original["models"]
        assert json.loads(csv_events[eid]["evidence"]) == original["evidence"]
        for key in ["run_id", "phase", "matrix", "issue_found", "followup", "final_selection"]:
            assert csv_events[eid][key] == original[key], (eid, key)
        is_claude = any("claude" in model.lower() for model in original["models"])
        assert (csv_events[eid]["excluded_model_in_current_report"] == "True") == is_claude
        if original.get("start_utc") and original.get("end_utc"):
            assert datetime.fromisoformat(original["start_utc"].replace("Z", "+00:00")) <= datetime.fromisoformat(original["end_utc"].replace("Z", "+00:00"))
    evidence = {p for r in events.values() for p in r["evidence"]}
    local_evidence = [p for p in evidence if not p.startswith("https://")]
    assert all(Path(p).exists() for p in local_evidence)
    out["history"] = {"records": 72, "all_original_fields_preserved": True, "local_evidence_paths_exist": len(local_evidence),
                      "remote_references_inherited_not_verified": len(evidence) - len(local_evidence),
                      "scope": "72 identifiable phases, including validation and plans, not 72 independent complete experiments"}
    out["status"] = "pass"
    out["inputs"] = SEEN
    (ROOT / "REVIEW_CHECKS.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in {"inputs", "independently_recomputed_ranking", "independently_recomputed_budget"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
