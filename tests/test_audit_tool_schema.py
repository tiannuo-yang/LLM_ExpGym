"""Canonical native Audit inputs preserve the explicitly legacy metric."""
import json
import unittest
from unittest.mock import patch

from expgym.errors import ToolInputError
from expgym import task_evidence_audit as audit


class AuditToolSchemaTest(unittest.TestCase):
    def setUp(self):
        self.doc = audit.Document(doc_id=7, file_name="fixture", segments=[
            {"span_index": 1, "text": "A fixture clause."}], annotations={
                "nda-1": {"choice": "Entailment", "spans": [1]},
                "nda-2": {"choice": "NotMentioned", "spans": []}})
        self.doc_patch = patch.object(audit, "_get_doc", return_value=self.doc)
        self.doc_patch.start()
        self.addCleanup(self.doc_patch.stop)

    def test_schema_matches_dynamic_tool_hypotheses_and_flat_dispatch(self):
        function = audit.build_tools(row_index=0, cc_split="cc-small")["human_feedback"]
        schema = function.__expgym_tool_schema__
        self.assertEqual(schema["name"], "human_feedback")
        self.assertTrue(schema["description"])
        parameters = schema["parameters"]
        self.assertEqual(parameters["required"], ["nda_id", "evidence_ids"])
        self.assertIs(parameters["additionalProperties"], False)
        self.assertEqual(parameters["properties"]["nda_id"]["enum"], ["nda-1", "nda-2"])
        self.assertEqual(parameters["properties"]["evidence_ids"]["items"], {"type": "integer"})
        self.assertEqual(json.loads(json.dumps(schema, allow_nan=False)), schema)
        payload = '{"nda_id":"nda-1","evidence_ids":[1]}'
        self.assertEqual(function(payload), audit.EvidenceAuditTools(0).human_feedback(payload))
        with patch.object(audit.EvidenceAuditTools, "human_feedback", return_value=("ok", 1.0)) as method:
            self.assertEqual(function(payload), ("ok", 1.0))
            method.assert_called_once_with(payload)

    def test_model_input_failures_are_typed(self):
        function = audit.build_tools()["human_feedback"]
        for payload in (None, "bad JSON", "null", "[]", '{}',
                        '{"nda_id":"unknown","evidence_ids":[]}',
                        '{"nda_id":"nda-1","evidence_ids":"1"}',
                        '{"nda_id":"nda-1","evidence_ids":[null]}',
                        '{"nda_id":"nda-1","evidence_ids":[Infinity]}'):
            with self.subTest(payload=payload), self.assertRaises(ToolInputError):
                function(payload)

    def test_legacy_feedback_coercion_and_list_payload_are_unchanged(self):
        function = audit.build_tools()["human_feedback"]
        for evidence in ([1], [1.9], [True]):
            payload = json.dumps({"nda_id": "nda-1", "evidence_ids": evidence})
            self.assertEqual(function(payload)[0], "Evidence Correct")
            self.assertEqual(function("[" + payload + "]")[0], "Evidence Correct")
        self.assertEqual(function('{"nda_id":"nda-2","evidence_ids":null}')[0], "Evidence Correct")

    def test_hints_backend_errors_are_not_model_input_errors(self):
        function = audit.build_tools()["human_feedback"]
        failure = FileNotFoundError("Missing evidence hints")
        with patch.object(audit, "_load_hints", side_effect=failure):
            with self.assertRaises(FileNotFoundError) as caught:
                function('{"nda_id":"nda-1","evidence_ids":[]}')
        self.assertIs(caught.exception, failure)

    def test_legacy_metric_remains_independent_ea_with_int_coercion(self):
        with patch.object(audit, "_get_labels", return_value={"nda-1": {}, "nda-2": {}}):
            evaluator = audit.build_answer_evaluator(0)
        answer = {"nda-1": {"label": "WRONG", "evidence_ids": [1.9]},
                  "nda-2": {"label": "WRONG", "evidence_ids": None}}
        self.assertEqual(evaluator(json.dumps(answer), []),
                         {"label_acc": 0.0, "evidence_acc": 1.0, "verification_eff": None})
        self.assertEqual(audit.EVIDENCE_SCORING_PROTOCOL, "legacy-int-coercion-independent-ea-v1")

    def test_rejected_json_limit_payloads_cannot_crash_final_replay(self):
        function = audit.build_tools()["human_feedback"]
        with patch.object(audit, "_get_labels", return_value={"nda-1": {}}):
            evaluator = audit.build_answer_evaluator(0)
        answer = '{"nda-1":{"label":"Entailment","evidence_ids":[1]}}'
        for invalid in ('[' * 2000 + '0' + ']' * 2000, '9' * 5000):
            payload = '{"nda_id":"nda-1","evidence_ids":' + invalid + '}'
            with self.subTest(payload_kind=invalid[:1]), self.assertRaises(ToolInputError):
                function(payload)
            metrics = evaluator(answer, [("human_feedback", payload, "Tool error")])
            self.assertEqual(metrics, {"label_acc": 1.0, "evidence_acc": 1.0, "verification_eff": 0.0})
        malformed = '[' * 2000 + '0' + ']' * 2000
        self.assertEqual(evaluator(malformed, []),
                         {"label_acc": 0.0, "evidence_acc": 0.0, "verification_eff": None})


if __name__ == "__main__":
    unittest.main()
