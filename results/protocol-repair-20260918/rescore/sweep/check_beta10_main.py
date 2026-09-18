#!/usr/bin/env python3
"""Verify all 234 beta10 Whois slots against the formally rescored main cohort."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path


def read(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--main", type=Path, required=True,
                        help="Directory containing main agent_rows.csv and slot_scalars.csv")
    args = parser.parse_args()
    sweep = read(args.sweep / "agent_rows.csv")
    candidates = [r for r in read(args.main / "agent_rows.csv") if r["system"] == "expgym"
                  and r["scenario"] == "restricted_search" and r["regime"] == "cost_moderate"]
    agents = {r["slot_id"]: r for r in candidates}
    assert len(agents) == len(candidates)
    slots = {r["slot_id"]: r for r in read(args.main / "slot_scalars.csv")}
    joined = []
    for row in sweep:
        if not row["main_overlap_slot_id"]:
            continue
        agent = agents[row["main_overlap_slot_id"]]
        slot = slots[row["main_overlap_slot_id"]]
        assert int(row["beta"]) == 10
        assert (agent["model"], agent["item"], agent["source_sha256"]) == (
            row["model_id"], row["item"], row["source_sha256"])
        old = json.loads(agent["old_metrics_json"])["f1"]
        new = json.loads(agent["new_metrics_json"])["f1"]
        adopted = json.loads(slot["metrics_json"])["f1"]
        assert math.isclose(float(row["old_score"]), old, rel_tol=0, abs_tol=1e-12)
        assert math.isclose(float(row["new_score"]), new, rel_tol=0, abs_tol=1e-12)
        assert math.isclose(new, adopted, rel_tol=0, abs_tol=1e-12)
        joined.append({"sweep_slot_id": row["slot_id"], "main_slot_id": agent["slot_id"],
                       "model": row["model"], "model_id": agent["model"], "beta": 10,
                       "item": row["item"], "source_sha256": row["source_sha256"],
                       "sweep_old_f1": row["old_score"], "main_old_f1": old,
                       "sweep_new_f1": row["new_score"], "main_new_f1": new,
                       "main_adopted_new_f1": adopted, "passed": True})
    assert len(joined) == 234
    assert Counter(r["model"] for r in joined) == {
        m: 39 for m in ("gpt", "kimi", "glm", "qwen", "deepseek", "gemini")}
    destination = args.sweep / "BETA10_MAIN_JOIN.csv"
    with destination.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(joined[0]))
        writer.writeheader()
        writer.writerows(joined)
    receipt = {
        "passed": True, "overlap_slots": 234, "per_model_slots": 39,
        "source_hash_matches": 234, "old_scores_match": 234,
        "new_scores_match": 234, "main_adopted_slot_scores_match": 234,
        "deduplication": "1170 sweep slots include 234 main report slots; only 936 independent additions",
        "inputs": [{"path": str(path), "sha256": sha(path)} for path in (
            args.sweep / "agent_rows.csv", args.main / "agent_rows.csv", args.main / "slot_scalars.csv")],
        "join_output_sha256": sha(destination), "script_sha256": sha(Path(__file__)),
    }
    (args.sweep / "BETA10_MAIN_JOIN_CHECK.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
