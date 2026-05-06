import json
import os
import unittest

from expgym.task_evidence_audit import (
    EVIDENCE_PATH,
    HINTS_PATH,
    EvidenceAuditTools,
    build_answer_evaluator,
    build_context,
    _format_hypotheses,
    _get_doc,
    _get_labels,
)

_HAS_AUDIT_DATA = os.path.exists(EVIDENCE_PATH) and os.path.exists(HINTS_PATH)
_AUDIT_SKIP_REASON = (
    "ContractNLI data not found at {} / {}; set EXPGYM_DATA_ROOT to the parent "
    "of contract-nli/ to enable these tests."
).format(EVIDENCE_PATH, HINTS_PATH)


@unittest.skipUnless(_HAS_AUDIT_DATA, _AUDIT_SKIP_REASON)
class EvidenceAuditTest(unittest.TestCase):
    def test_human_feedback_not_mentioned(self) -> None:
        tools = EvidenceAuditTools(0)
        payload = json.dumps({"nda_id": "nda-11", "evidence_ids": []})
        text, overhead = tools.human_feedback(payload)
        self.assertEqual(text, "Evidence Correct")
        self.assertGreater(overhead, 0.0)

        payload = json.dumps({"nda_id": "nda-11", "evidence_ids": [1]})
        text, _ = tools.human_feedback(payload)
        self.assertEqual(text, "Contain Irrelevant Evidences")

    def test_human_feedback_entailment(self) -> None:
        tools = EvidenceAuditTools(0)
        payload = json.dumps({"nda_id": "nda-16", "evidence_ids": [84]})
        text, _ = tools.human_feedback(payload)
        self.assertTrue(text.startswith("Evidence Incomplete"))

        payload = json.dumps({"nda_id": "nda-16", "evidence_ids": [84, 85, 86]})
        text, _ = tools.human_feedback(payload)
        self.assertEqual(text, "Evidence Correct")

    def test_answer_evaluator_exact_match(self) -> None:
        doc = _get_doc(0)
        answer = {}
        for nda_id, entry in doc.annotations.items():
            answer[nda_id] = {
                "label": entry["choice"],
                "evidence_ids": entry["spans"],
            }
        evaluator = build_answer_evaluator(0)
        tool_records = [
            ("human_feedback", json.dumps({"nda_id": nda_id, "evidence_ids": entry["spans"]}), None)
            for nda_id, entry in doc.annotations.items()
        ]
        metrics = evaluator(json.dumps(answer), tool_records)
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["label_acc"], 1.0)
        self.assertEqual(metrics["evidence_acc"], 1.0)
        self.assertEqual(metrics["verification_eff"], 1.0)

    def test_answer_evaluator_label_only(self) -> None:
        """Correct labels but wrong evidence → label_acc=1, evidence_acc<1."""
        doc = _get_doc(0)
        answer = {}
        for nda_id, entry in doc.annotations.items():
            answer[nda_id] = {
                "label": entry["choice"],
                "evidence_ids": [999],  # wrong evidence
            }
        evaluator = build_answer_evaluator(0)
        metrics = evaluator(json.dumps(answer), [])
        self.assertEqual(metrics["label_acc"], 1.0)
        # NotMentioned hypotheses have empty gold spans; [999] != [] → wrong
        self.assertLess(metrics["evidence_acc"], 1.0)
        # No fully correct → verification_eff is None
        self.assertIsNone(metrics["verification_eff"])

    def test_answer_evaluator_no_verification(self) -> None:
        """Fully correct answers but never called human_feedback."""
        doc = _get_doc(0)
        answer = {}
        for nda_id, entry in doc.annotations.items():
            answer[nda_id] = {
                "label": entry["choice"],
                "evidence_ids": entry["spans"],
            }
        evaluator = build_answer_evaluator(0)
        metrics = evaluator(json.dumps(answer), [])  # no tool records
        self.assertEqual(metrics["label_acc"], 1.0)
        self.assertEqual(metrics["evidence_acc"], 1.0)
        self.assertEqual(metrics["verification_eff"], 0.0)

    def test_answer_evaluator_partial_verification(self) -> None:
        """Verify only some of the correct hypotheses."""
        doc = _get_doc(0)
        answer = {}
        for nda_id, entry in doc.annotations.items():
            answer[nda_id] = {
                "label": entry["choice"],
                "evidence_ids": entry["spans"],
            }
        # Only verify the first hypothesis
        first_nda = list(doc.annotations.keys())[0]
        first_entry = doc.annotations[first_nda]
        tool_records = [
            ("human_feedback", json.dumps({"nda_id": first_nda, "evidence_ids": first_entry["spans"]}), None)
        ]
        evaluator = build_answer_evaluator(0)
        metrics = evaluator(json.dumps(answer), tool_records)
        self.assertEqual(metrics["label_acc"], 1.0)
        self.assertEqual(metrics["evidence_acc"], 1.0)
        total_hyp = len(doc.annotations)
        self.assertAlmostEqual(metrics["verification_eff"], 1.0 / total_hyp, places=4)

    def test_answer_evaluator_empty_prediction(self) -> None:
        evaluator = build_answer_evaluator(0)
        metrics = evaluator("not json", [])
        self.assertEqual(metrics["label_acc"], 0.0)
        self.assertEqual(metrics["evidence_acc"], 0.0)
        self.assertIsNone(metrics["verification_eff"])


@unittest.skipUnless(_HAS_AUDIT_DATA, _AUDIT_SKIP_REASON)
class TestHypothesisOrder(unittest.TestCase):
    """Tests for hypothesis_order parameter in _format_hypotheses / build_context."""

    def test_format_hypotheses_default_order(self) -> None:
        """Default (no order) returns all hypotheses in original dict order."""
        lines = _format_hypotheses("cc-large")
        labels = _get_labels("cc-large")
        self.assertEqual(len(lines), len(labels))
        # Each line should start with the NDA ID in dict order
        for line, nda_id in zip(lines, labels.keys()):
            self.assertTrue(line.startswith(f"- {nda_id}:"), line)

    def test_format_hypotheses_reorder(self) -> None:
        """Providing hypothesis_order reorders the output."""
        labels = _get_labels("cc-large")
        original_ids = list(labels.keys())
        # Reverse the order
        reversed_ids = list(reversed(original_ids))
        lines = _format_hypotheses("cc-large", hypothesis_order=reversed_ids)
        self.assertEqual(len(lines), len(original_ids))
        for line, nda_id in zip(lines, reversed_ids):
            self.assertTrue(line.startswith(f"- {nda_id}:"), line)

    def test_format_hypotheses_partial_order(self) -> None:
        """hypothesis_order with unknown IDs skips them gracefully."""
        labels = _get_labels("cc-large")
        original_ids = list(labels.keys())
        # Include an unknown ID — should be skipped
        order = [original_ids[2], "nda-999", original_ids[0]]
        lines = _format_hypotheses("cc-large", hypothesis_order=order)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith(f"- {original_ids[2]}:"))
        self.assertTrue(lines[1].startswith(f"- {original_ids[0]}:"))

    def test_build_context_with_hypothesis_order(self) -> None:
        """build_context passes hypothesis_order through to output."""
        labels = _get_labels("cc-large")
        original_ids = list(labels.keys())
        reversed_ids = list(reversed(original_ids))

        ctx_default = build_context(False, row_index=0, cc_split="cc-large")
        ctx_reordered = build_context(
            False, row_index=0, cc_split="cc-large",
            hypothesis_order=reversed_ids,
        )

        # Both should contain all hypothesis IDs
        for nda_id in original_ids:
            self.assertIn(nda_id, ctx_default)
            self.assertIn(nda_id, ctx_reordered)

        # Extract hypothesis lines from the "Hypotheses:" section
        def _extract_hyp_ids(ctx):
            lines = ctx.split("\n")
            in_hyp = False
            ids = []
            for line in lines:
                if line.strip() == "Hypotheses:":
                    in_hyp = True
                    continue
                if in_hyp and line.startswith("- nda-"):
                    nda_id = line.split(":")[0].strip("- ")
                    ids.append(nda_id)
            return ids

        default_hyp_ids = _extract_hyp_ids(ctx_default)
        reordered_hyp_ids = _extract_hyp_ids(ctx_reordered)

        self.assertEqual(default_hyp_ids, original_ids)
        self.assertEqual(reordered_hyp_ids, reversed_ids)

    def test_build_context_none_hypothesis_order(self) -> None:
        """hypothesis_order=None behaves identically to no argument."""
        ctx1 = build_context(False, row_index=0, cc_split="cc-large")
        ctx2 = build_context(
            False, row_index=0, cc_split="cc-large", hypothesis_order=None,
        )
        self.assertEqual(ctx1, ctx2)


if __name__ == "__main__":
    unittest.main()
