"""Explicit historical PoolAct answer policy, isolated from single-agent defaults.

The tool protocol companion is byte-identical to commit 297c3d0. The Audit
builder below is the exact historical function apart from qualifying its two
data lookups through the current task module. No process globals are patched.
"""
from __future__ import annotations

import json
from typing import Callable, Dict, List, Optional, Tuple

from expgym import poolact_legacy_tool_protocol as protocol
from expgym import task_evidence_audit as _audit

LEGACY_POOL_ANSWER_PROTOCOL = "poolact-answer-297c3d0"


def parse_final_answer(text: str) -> Optional[str]:
    """Reproduce the historical native/forced-final fallback order exactly."""
    return (protocol.extract_text_answer(text)
            or protocol.structured_final_answer(text)
            or protocol.unlabelled_final_answer(text))


def build_answer_evaluator(
    row_index: int, cc_split: str = "cc-large",
) -> Callable[[str, List[Tuple[str, str, Optional[object]]]], Dict[str, object]]:
    """Build an evaluator that returns a metrics dict.

    Returned dict keys:
        label_acc:  fraction of hypotheses with correct entailment label.
        evidence_acc:  fraction of hypotheses with exact-match evidence IDs.
        verification_eff:  among fully-correct hypotheses (label + evidence),
            the fraction that were verified via human_feedback.  ``None`` when
            no hypothesis is fully correct (denominator = 0).
    """
    doc = _audit._get_doc(row_index)
    split_labels = _audit._get_labels(cc_split)
    gold = {k: v for k, v in doc.annotations.items() if k in split_labels}

    def _evaluator(
        prediction: str, tool_records: List[Tuple[str, str, Optional[object]]]
    ) -> Dict[str, object]:
        empty = {"label_acc": 0.0, "evidence_acc": 0.0, "verification_eff": None}
        try:
            data = json.loads(prediction)
        except (ValueError, RecursionError, OverflowError):
            # Strip trailing non-JSON chars (e.g. ";", markdown fences)
            cleaned = prediction.strip().rstrip(";").strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            try:
                data = json.loads(cleaned)
            except (ValueError, RecursionError, OverflowError):
                return empty
        if not isinstance(data, dict):
            return empty

        # Collect all verified submissions from tool records
        audited: Dict[str, List[set]] = {}
        for tool_name, argument, _ in tool_records:
            if tool_name != "human_feedback":
                continue
            try:
                payload = json.loads(argument)
            except (ValueError, RecursionError, OverflowError):
                continue
            if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                payload = payload[0]
            if not isinstance(payload, dict):
                continue
            nda_id = payload.get("nda_id")
            evidence_ids = payload.get("evidence_ids")
            if not isinstance(nda_id, str) or not isinstance(evidence_ids, list):
                continue
            try:
                submission = set(int(v) for v in evidence_ids)
            except Exception:
                continue
            audited.setdefault(nda_id, []).append(submission)

        total = len(gold)
        if total == 0:
            return empty

        label_correct = 0
        evidence_correct = 0
        fully_correct = 0
        verified_correct = 0

        for nda_id, gold_entry in gold.items():
            if nda_id not in data:
                continue
            entry = data[nda_id]
            if not isinstance(entry, dict):
                continue

            pred_label = entry.get("label")
            pred_evidence = entry.get("evidence_ids", [])
            gold_choice = gold_entry["choice"]
            gold_spans = set(int(s) for s in gold_entry.get("spans", []))

            # (1) Label accuracy
            label_ok = pred_label == gold_choice
            if label_ok:
                label_correct += 1

            # (2) Evidence accuracy (exact match, binary)
            try:
                evidence_set = set(int(v) for v in pred_evidence)
            except Exception:
                evidence_set = set()
            evidence_ok = evidence_set == gold_spans
            if evidence_ok:
                evidence_correct += 1

            # (3) Verification efficiency (only for fully correct)
            if label_ok and evidence_ok:
                fully_correct += 1
                audited_submissions = audited.get(nda_id, [])
                if any(s == evidence_set for s in audited_submissions):
                    verified_correct += 1

        label_acc = label_correct / total
        evidence_acc = evidence_correct / total
        verification_eff = (
            verified_correct / fully_correct if fully_correct > 0 else None
        )

        return {
            "label_acc": label_acc,
            "evidence_acc": evidence_acc,
            "verification_eff": verification_eff,
        }

    return _evaluator
