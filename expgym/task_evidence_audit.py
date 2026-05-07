"""Evidence audit scenario for contract NLI."""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from expgym.react_loop import build_system_prompt as build_react_system_prompt

_REPO_DATA = os.path.join(os.path.dirname(__file__), "..", "data")
_DATA_ROOT = os.environ.get("EXPGYM_DATA_ROOT", _REPO_DATA)
EVIDENCE_PATH = os.path.join(_DATA_ROOT, "contract-nli", "test_segments.json")

# The hints file is shipped with the repo (it is not part of the upstream
# ContractNLI release). Resolution order: a copy under EXPGYM_DATA_ROOT
# wins if present, otherwise fall back to the bundled file at
# ``data/contract-nli/test_nda_span_dims.json``.
HINTS_PATH = os.path.join(_DATA_ROOT, "contract-nli", "test_nda_span_dims.json")
_BUNDLED_HINTS_PATH = os.path.join(_REPO_DATA, "contract-nli", "test_nda_span_dims.json")
if not os.path.isfile(HINTS_PATH) and os.path.isfile(_BUNDLED_HINTS_PATH):
    HINTS_PATH = _BUNDLED_HINTS_PATH

HUMAN_OVERHEAD_SECONDS = 300.0  # nominal; actual per-call cost uses _stable_overhead
OVERHEAD_LOW = 280.0
OVERHEAD_HIGH = 320.0


def _stable_float(seed_str: str, low: float, high: float) -> float:
    """Deterministic float in [low, high] from a hash seed."""
    digest = hashlib.sha256(seed_str.encode("utf-8")).digest()
    raw = int.from_bytes(digest[:4], "big") / 2**32
    return low + (high - low) * raw


def _stable_overhead(seed: str) -> float:
    """Deterministic overhead in [280, 320] from a hash seed."""
    return _stable_float(seed, OVERHEAD_LOW, OVERHEAD_HIGH)

# CC-split hypothesis subsets (from outline.md footnote [^2])
CC_SPLITS: Dict[str, List[str]] = {
    "cc-small": ["nda-4", "nda-7", "nda-11", "nda-16"],
    "cc-medium": [
        "nda-1", "nda-3", "nda-4", "nda-5",
        "nda-7", "nda-8", "nda-11", "nda-16",
    ],
    "cc-large": [],  # empty means all hypotheses
}


@dataclass(frozen=True)
class Document:
    doc_id: int
    file_name: str
    segments: List[dict]
    annotations: Dict[str, dict]


_DATA_CACHE: Optional[dict] = None
_HINTS_CACHE: Optional[dict] = None


def _load_data() -> dict:
    global _DATA_CACHE
    if _DATA_CACHE is None:
        with open(EVIDENCE_PATH, "r", encoding="utf-8") as handle:
            _DATA_CACHE = json.load(handle)
    return _DATA_CACHE


def _load_hints() -> dict:
    global _HINTS_CACHE
    if _HINTS_CACHE is None:
        with open(HINTS_PATH, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        by_doc = {}
        for item in raw:
            doc_id = int(item["doc_id"])
            span_map = {int(k): v for k, v in item["span_to_dimension"].items()}
            by_doc[doc_id] = span_map
        _HINTS_CACHE = by_doc
    return _HINTS_CACHE


def _get_doc(row_index: int) -> Document:
    data = _load_data()
    docs = data["documents"]
    if row_index < 0:
        row_index = len(docs) + row_index
    if row_index < 0 or row_index >= len(docs):
        raise IndexError(f"row_index {row_index} outside [0, {len(docs)})")
    doc = docs[row_index]
    annotations = doc["annotation_sets"][0]["annotations"]
    return Document(
        doc_id=int(doc["id"]),
        file_name=doc["file_name"],
        segments=doc["segments"],
        annotations=annotations,
    )


def _get_labels(cc_split: str = "cc-large") -> Dict[str, dict]:
    all_labels = _load_data()["labels"]
    subset_ids = CC_SPLITS.get(cc_split, [])
    if not subset_ids:
        return all_labels
    return {k: v for k, v in all_labels.items() if k in subset_ids}


def _format_segments(segments: Sequence[dict]) -> List[str]:
    lines: List[str] = []
    for seg in segments:
        idx = seg.get("span_index")
        text = seg.get("text", "").strip()
        text = re.sub(r"\s+", " ", text)
        lines.append(f"[{idx}] {text}")
    return lines


def _format_hypotheses(
    cc_split: str = "cc-large",
    hypothesis_order: Optional[List[str]] = None,
) -> List[str]:
    labels = _get_labels(cc_split)
    if hypothesis_order is not None:
        # Reorder to match the provided ordering; skip unknown IDs
        ordered_ids = [nid for nid in hypothesis_order if nid in labels]
    else:
        ordered_ids = list(labels.keys())
    lines: List[str] = []
    for nda_id in ordered_ids:
        meta = labels[nda_id]
        short = meta.get("short_description", "")
        hypothesis = meta.get("hypothesis", "")
        lines.append(f"- {nda_id}: {short} | {hypothesis}")
    return lines


def _parse_payload(payload: str) -> Dict[str, object]:
    payload = payload.strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        data, end = decoder.raw_decode(payload)
        trailing = payload[end:].strip()
        if trailing:
            raise
    if not isinstance(data, dict):
        if isinstance(data, list) and data and isinstance(data[0], dict):
            data = data[0]
        else:
            raise ValueError("Payload must be a JSON object.")
    return data


def _normalize_evidence(value: object) -> List[int]:
    if value is None:
        return []
    if isinstance(value, list):
        return [int(v) for v in value]
    raise TypeError("evidence_ids must be a list of ints")


def _build_missing_hints(doc_id: int, missing: Sequence[int]) -> str:
    hint_map = _load_hints().get(doc_id, {})
    parts = []
    for span_id in sorted(missing):
        dim = hint_map.get(span_id)
        if dim:
            parts.append(dim)
    if not parts:
        return "<none>"
    return ", ".join(sorted(set(parts)))


class EvidenceAuditTools:
    """Tools for evidence audit with human feedback."""

    def __init__(self, row_index: int) -> None:
        self._doc = _get_doc(row_index)

    def human_feedback(self, payload: str) -> Tuple[str, float]:
        data = _parse_payload(payload)
        nda_id = str(data.get("nda_id", "")).strip()
        evidence_ids = _normalize_evidence(data.get("evidence_ids"))
        evidence_set = set(evidence_ids)
        if nda_id not in self._doc.annotations:
            raise ValueError(f"Unknown nda_id: {nda_id}")

        # Deterministic overhead in [280, 320] per (doc, nda_id, evidence) call
        ev_key = ",".join(str(e) for e in sorted(evidence_set))
        overhead = _stable_overhead(
            f"audit:{self._doc.doc_id}:{nda_id}:{ev_key}"
        )

        gold = self._doc.annotations[nda_id]
        gold_choice = gold["choice"]
        gold_spans = set(int(s) for s in gold.get("spans", []))

        if gold_choice == "NotMentioned":
            if evidence_set:
                return "Contain Irrelevant Evidences", overhead
            return "Evidence Correct", overhead

        if not evidence_set:
            missing = _build_missing_hints(self._doc.doc_id, gold_spans)
            return f"Evidence Incomplete | missing: {missing}", overhead

        if evidence_set == gold_spans:
            return "Evidence Correct", overhead

        if evidence_set.issubset(gold_spans):
            missing = _build_missing_hints(self._doc.doc_id, gold_spans - evidence_set)
            return f"Evidence Incomplete | missing: {missing}", overhead

        return "Contain Irrelevant Evidences", overhead


def _load_example(row_index: int) -> Document:
    return _get_doc(row_index)


def _build_context(
    doc: Document,
    include_overhead: bool,
    cc_split: str = "cc-large",
    hypothesis_order: Optional[List[str]] = None,
) -> str:
    num_hyp = len(_get_labels(cc_split))
    notes = [
        "You are auditing a legal document against {} hypotheses.".format(num_hyp),
        "Your goal: maximize the correctness of ALL labels and evidence IDs in your final answer.",
        "For each hypothesis, determine: Entailment, Contradiction, or NotMentioned.",
        "For Entailment/Contradiction, identify the exact evidence segment IDs.",
        "",
        "Tool: human_feedback — verify your proposed evidence for a hypothesis. Can be called multiple times.",
        "  Input: {{\"nda_id\": \"...\", \"evidence_ids\": [segment_ids]}}",
        "",
        "Use human feedback to improve the correctness of your labels and evidence IDs.",
    ]
    notes.extend(
        [
            "",
            "Action: human_feedback {\"nda_id\": \"nda-11\", \"evidence_ids\": [3, 7]}",
            "Answer: {\"nda-11\": {\"label\": \"...\", \"evidence_ids\": [...]}, ...}",
            "Your final answer MUST include ALL {} hypotheses.".format(num_hyp),
            "",
            "Document segments:",
        ]
    )
    notes.extend(_format_segments(doc.segments))
    notes.append("")
    notes.append("Hypotheses:")
    notes.extend(_format_hypotheses(cc_split, hypothesis_order=hypothesis_order))
    return "\n".join(notes)


def build_context(
    include_overhead: bool,
    *,
    row_index: int = 0,
    cc_split: str = "cc-large",
    hypothesis_order: Optional[List[str]] = None,
) -> str:
    doc = _load_example(row_index)
    return _build_context(
        doc, include_overhead, cc_split=cc_split,
        hypothesis_order=hypothesis_order,
    )


def build_instruction_notes(_: bool) -> List[str]:
    return []


def build_system_prompt(include_overhead: bool) -> str:
    notes = []
    if include_overhead:
        notes.append("Note: Human feedback is slow; use it sparingly.")
    return build_react_system_prompt(instruction_notes=notes)


def build_fake_plan(probes: int, *, row_index: int = 0, cc_split: str = "cc-large") -> List[tuple[str, str]]:
    labels = list(_get_labels(cc_split).keys())
    limited = labels[: max(1, probes)]
    plan = []
    for nda_id in limited:
        payload = {"nda_id": nda_id, "evidence_ids": []}
        plan.append(("human_feedback", json.dumps(payload)))
    return plan


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
    doc = _get_doc(row_index)
    split_labels = _get_labels(cc_split)
    gold = {k: v for k, v in doc.annotations.items() if k in split_labels}

    def _evaluator(
        prediction: str, tool_records: List[Tuple[str, str, Optional[object]]]
    ) -> Dict[str, object]:
        empty = {"label_acc": 0.0, "evidence_acc": 0.0, "verification_eff": None}
        try:
            data = json.loads(prediction)
        except json.JSONDecodeError:
            # Strip trailing non-JSON chars (e.g. ";", markdown fences)
            cleaned = prediction.strip().rstrip(";").strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError:
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
            except json.JSONDecodeError:
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


def build_tools(row_index: int = 0, cc_split: str = "cc-large") -> Dict[str, Callable[[str], Tuple[str, float]]]:
    tools = EvidenceAuditTools(row_index)
    return {"human_feedback": tools.human_feedback}


SCENARIO = {
    "name": "evidence_audit",
    "tools": build_tools,
    "build_context": build_context,
    "build_instruction_notes": build_instruction_notes,
    "build_fake_plan": build_fake_plan,
    "build_answer_evaluator": build_answer_evaluator,
    "build_system_prompt": build_system_prompt,
}
