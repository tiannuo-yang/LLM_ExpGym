#!/usr/bin/env python3
"""Fixed NotMentioned/empty-evidence reference; no model or feedback calls."""
import collections
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "LLM_ExpGym"
STUDY = ROOT / "kimi_k3_eval"
os.environ["EXPGYM_DATA_ROOT"] = str(REPO / "data")
sys.path.insert(0, str(REPO))
from expgym import task_evidence_audit as audit
from expgym.trace_v2 import source_tree_sha256

def reference(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}

LABELS = ("Entailment", "Contradiction", "NotMentioned")
FIXED_PREDICTED_LABEL = "NotMentioned"
ids = list(audit._get_labels("cc-large"))
assert len(ids) == 17
# Policy is fixed in advance, independent of gold labels; only task IDs vary.
prediction = {nda: {"label": FIXED_PREDICTED_LABEL, "evidence_ids": []} for nda in ids}
prediction_text = json.dumps(prediction, ensure_ascii=False)
dataset_path = STUDY / "data_runtime/dataset_manifest.json"
dataset = json.loads(dataset_path.read_text())
evidence_ref = reference(audit.EVIDENCE_PATH)
declared = next(row for row in dataset["files"] if row["path"] == "data/contract-nli/test_segments.json")
assert evidence_ref["sha256"] == declared["sha256"] and evidence_ref["bytes"] == declared["bytes"]
assert dataset["audit"]["selected_count"] == 13
documents = []
all_counts = collections.Counter()
by_hypothesis = {nda: collections.Counter() for nda in ids}
for index in range(13):
    doc = audit._get_doc(index)
    assert set(doc.annotations) == set(ids)
    selected = dataset["audit"]["items"][index]
    assert (selected["index"], selected["doc_id"], selected["hypotheses"]) == (index, doc.doc_id, 17)
    hypotheses = []
    counts = collections.Counter()
    for nda in ids:
        gold = doc.annotations[nda]
        label = gold["choice"]
        assert label in LABELS
        spans = sorted(set(int(span) for span in gold.get("spans", [])))
        counts[label] += 1
        by_hypothesis[nda][label] += 1
        hypotheses.append({"hypothesis_id": nda, "gold_label": label, "gold_evidence_ids": spans,
                           "gold_json_pointer": "/documents/%d/annotation_sets/0/annotations/%s" % (index, nda),
                           "constant_label_correct": label == FIXED_PREDICTED_LABEL,
                           "constant_evidence_correct": spans == [],
                           "constant_fully_correct": label == FIXED_PREDICTED_LABEL and spans == []})
    metrics = audit.build_answer_evaluator(index, "cc-large")(prediction_text, [])
    label_correct = sum(row["constant_label_correct"] for row in hypotheses)
    evidence_correct = sum(row["constant_evidence_correct"] for row in hypotheses)
    fully_correct = sum(row["constant_fully_correct"] for row in hypotheses)
    assert math.isclose(metrics["label_acc"], label_correct / 17, abs_tol=1e-12)
    assert math.isclose(metrics["evidence_acc"], evidence_correct / 17, abs_tol=1e-12)
    assert metrics["verification_eff"] == (0.0 if fully_correct else None)
    all_counts.update(counts)
    documents.append({"row_index": index, "doc_id": doc.doc_id, "file_name": doc.file_name,
                      "hypothesis_count": 17, "label_counts": {label: counts[label] for label in LABELS},
                      "empty_gold_evidence_count": evidence_correct,
                      "label_correct": label_correct, "evidence_correct": evidence_correct,
                      "fully_correct": fully_correct, "verified_correct": 0,
                      "metrics": metrics, "hypotheses": hypotheses})
total = sum(row["hypothesis_count"] for row in documents)
assert total == 221
label_correct = sum(row["label_correct"] for row in documents)
evidence_correct = sum(row["evidence_correct"] for row in documents)
macro = {key: sum(row["metrics"][key] for row in documents) / len(documents)
         for key in ("label_acc", "evidence_acc", "verification_eff")}
micro = {"label_acc": label_correct / total, "evidence_acc": evidence_correct / total}
for key in micro:
    assert math.isclose(micro[key], macro[key], abs_tol=1e-12)
empty_mismatch = [{"row_index": doc["row_index"], **hyp} for doc in documents for hyp in doc["hypotheses"]
                  if (hyp["gold_evidence_ids"] == []) != (hyp["gold_label"] == "NotMentioned")]
smoke_path = STUDY / "runs/smoke_v3/manifest.json"
smoke = json.loads(smoke_path.read_text())
source_hash = source_tree_sha256(REPO)
assert source_hash == smoke["source_tree_sha256"]
result = {"schema": {"name": "kimi.audit.constant_label_reference", "version": 1},
          "created_at": datetime.now(timezone.utc).isoformat(), "python": sys.version,
          "classification": "offline fixed constant baseline; not Kimi-K3 measurement; not part of official study matrix",
          "scope": {"cc_split": "cc-large", "row_indices": list(range(13)), "document_count": 13,
                    "hypotheses_per_document": 17, "document_hypothesis_pairs": total,
                    "hypothesis_ids": ids, "annotation_set_index": 0},
          "policy": {"label": FIXED_PREDICTED_LABEL, "evidence_ids": [], "prediction": prediction,
                     "definition": "same fixed answer for all documents, all hypotheses; no gold-conditioned choices",
                     "llm_api_calls": 0, "human_feedback_calls": 0, "tool_records": []},
          "source": {"repo_root": str(REPO), "source_tree_sha256": source_hash,
                     "evaluator": reference(REPO / "expgym/task_evidence_audit.py"),
                     "script": reference(__file__), "context_manifest": reference(smoke_path),
                     "context_manifest_note": "used only to bind current source hash; no model scores read or compared"},
          "data": {"evidence": evidence_ref, "dataset_manifest": reference(dataset_path),
                   "selection_protocol": reference(STUDY / "protocol/PAPER_ALIGNMENT.md")},
          "overall": {"label_counts": {label: all_counts[label] for label in LABELS},
                      "label_proportions": {label: all_counts[label] / total for label in LABELS},
                      "label_correct": label_correct, "evidence_correct": evidence_correct, "denominator": total,
                      "document_macro_metrics": macro, "hypothesis_micro_metrics": micro,
                      "per_document_label_acc_min": min(row["metrics"]["label_acc"] for row in documents),
                      "per_document_label_acc_max": max(row["metrics"]["label_acc"] for row in documents),
                      "empty_evidence_iff_notmentioned_on_selected_data": not empty_mismatch,
                      "empty_evidence_label_mismatches": empty_mismatch},
          "per_hypothesis": [{"hypothesis_id": nda, "description": audit._get_labels("cc-large")[nda],
                              "documents": 13, "label_counts": {label: by_hypothesis[nda][label] for label in LABELS}}
                             for nda in ids], "documents": documents,
          "interpretation": {"EA_definition": "exact equality of evidence sets, independent of label correctness",
              "LA_EA_equality_here": "coincidence of the fixed NotMentioned/[] prediction and selected gold: empty evidence iff NotMentioned",
              "verification_eff_definition": "fraction verified among jointly correct label-and-evidence hypotheses; no feedback implies 0 when denominator is nonempty",
              "limitations": ["NotMentioned and Entailment are tied, not a single overwhelmingly dominant NotMentioned class",
                              "This fixed baseline does not explain approximately 94% model label accuracy",
                              "No claim is made about statistical significance or model advantage without matched full results",
                              "Baseline has no model rollout, budget consumption, strategy interaction, or official trace count"]}}
print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
