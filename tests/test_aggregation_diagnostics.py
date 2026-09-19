import copy
import json
import unittest

from expgym.extras.aggregation_diagnostics import build_aggregation_diagnostics


class AggregationDiagnosticsTest(unittest.TestCase):
    def test_search_records_normalized_groups_without_mutating_results(self):
        results = [
            {"answer": "Bob, Alice", "agent_id": 9},
            {"answer": "Alice, Bob", "agent_id": 2},
            {"answer": "Carol", "agent_id": 0},
        ]
        original = copy.deepcopy(results)
        out = build_aggregation_diagnostics(
            "restricted_search", results,
            search_keys=[("alice", "bob"), ("alice", "bob"), ("carol",)],
            selected_agent_index=0,
        )
        self.assertEqual(results, original)
        self.assertEqual(out["vote_groups"][0], {
            "key": ["alice", "bob"], "count": 2, "agent_indices": [0, 1],
        })
        self.assertEqual(out["selection_reason"], "highest_vote_count")
        self.assertTrue(out["winner_has_strict_majority"])
        self.assertEqual(out["agent_provenance"][0]["agent_id"], 9)
        self.assertIsNone(out["agent_provenance"][0]["termination_reason"])
        self.assertIsNone(out["agent_provenance"][0]["answer_source"])
        self.assertIsNone(out["abstention"]["declared_count"])
        json.dumps(out, allow_nan=False)

    def test_empty_vote_keys_are_counted_not_discarded(self):
        out = build_aggregation_diagnostics(
            "restricted_search", [{"answer": ""}, {"answer": "[]"}, {"answer": "Alice"}],
            search_keys=[(), (), ("alice",)], selected_agent_index=0,
        )
        self.assertEqual(out["empty_answer_agent_indices"], [0])
        self.assertEqual(out["empty_vote_key_agent_indices"], [0, 1])
        self.assertEqual(out["vote_groups"][0]["count"], 2)
        self.assertEqual(out["selected_agent_index"], 0)
        self.assertIsNone(out["abstention"]["declared_count"])

    def test_nonempty_tie_and_refusal_tie_preserve_first_input_rules(self):
        nonempty = build_aggregation_diagnostics(
            "restricted_search", [{"answer": ""}, {"answer": "Alice"}],
            search_keys=[(), ("alice",)],
        )
        self.assertEqual(nonempty["selection_reason"], "nonempty_key_tiebreak")
        self.assertEqual(nonempty["selected_agent_index"], 1)
        self.assertEqual(nonempty["tied_keys"], [[], ["alice"]])
        self.assertFalse(nonempty["winner_has_strict_majority"])
        refusal = build_aggregation_diagnostics(
            "restricted_search", [{"answer": "I do not know"}, {"answer": "Alice"}],
            search_keys=[("i do not know",), ("alice",)],
        )
        self.assertEqual(refusal["selection_reason"], "first_agent_tiebreak")
        self.assertEqual(refusal["selected_agent_index"], 0)
        self.assertIsNone(refusal["abstention"]["declared_count"])

    def test_only_explicit_boolean_abstention_is_recorded_and_not_excluded(self):
        out = build_aggregation_diagnostics(
            "restricted_search",
            [{"answer": "Alice", "abstained": True},
             {"answer": "Bob", "abstained": False},
             {"answer": "I do not know", "abstained": "true"}],
            search_keys=[("alice",), ("bob",), ("i do not know",)],
        )
        self.assertEqual(out["abstention"]["reported_agent_indices"], [0, 1])
        self.assertEqual(out["abstention"]["declared_count"], 1)
        self.assertEqual(out["abstention"]["declared_agent_indices"], [0])
        self.assertEqual(out["selected_agent_index"], 0)
        self.assertEqual(len(out["vote_groups"]), 3)
        self.assertIsNone(out["agent_provenance"][2]["abstained"])

    def test_tuning_does_not_read_scores_and_preserves_provenance(self):
        class NoScoreAccess(dict):
            def get(self, key, *args):
                if key in {"answer_perf", "answer_metrics", "score_check"}:
                    raise AssertionError("diagnostics must not read scores")
                return super().get(key, *args)

        out = build_aggregation_diagnostics("tuning", [NoScoreAccess({
            "answer": "{}", "termination_reason": "Max steps reached",
            "answer_source": "forced_model_answer", "answer_score_source": "offline_final_answer",
        })], selected_agent_index=0)
        self.assertEqual(out["selected_agent_index"], 0)
        self.assertEqual(out["agent_provenance"][0]["answer_source"], "forced_model_answer")
        self.assertEqual(out["agent_provenance"][0]["answer_score_source"], "offline_final_answer")

    def test_audit_label_tie_and_evidence_vote_use_only_label_supporters(self):
        parsed = [
            {"h": {"label": "entailed", "evidence_ids": [2, "1", 2]}},
            {"h": {"label": "Contradiction", "evidence_ids": [9]}},
            {"h": {"label": "Entailment", "evidence_ids": [3]}},
            {"h": {"label": "contradicted", "evidence_ids": [9]}},
        ]
        out = build_aggregation_diagnostics(
            "evidence_audit", [{"answer": json.dumps(value)} for value in parsed],
            parsed_answers=parsed,
        )
        vote = out["hypotheses"]["h"]
        self.assertTrue(vote["label_tied"])
        self.assertEqual(vote["winning_label"], "Entailment")
        self.assertEqual(vote["label_votes"][0]["agent_indices"], [0, 2])
        self.assertTrue(vote["evidence_tied"])
        self.assertEqual(vote["winning_evidence"], [1, 2])
        self.assertEqual([group["agent_indices"] for group in vote["evidence_votes"]], [[0], [2]])

    def test_audit_missing_invalid_and_empty_labels_remain_distinct(self):
        results = [
            {"answer": "bad JSON"}, {"answer": "[]"},
            {"answer": {"h": "not an object"}}, {"answer": {"h": {}}},
        ]
        out = build_aggregation_diagnostics("evidence_audit", results)
        self.assertEqual(out["audit_parse_status"], ["invalid_json", "not_object", "object", "object"])
        self.assertEqual(out["observed_hypothesis_ids"], ["h"])
        vote = out["hypotheses"]["h"]
        self.assertEqual(vote["missing_agent_indices"], [0, 1])
        self.assertEqual(vote["invalid_entry_agent_indices"], [2])
        self.assertEqual(vote["winning_label"], "")
        self.assertEqual(vote["winning_evidence"], [])
        self.assertEqual(vote["label_votes"][0]["agent_indices"], [3])

    def test_precomputed_audit_votes_are_reused_without_recanonicalization(self):
        results = [{"answer": {"h": {"label": "raw", "evidence_ids": [1]}}}]
        out = build_aggregation_diagnostics(
            "evidence_audit", results,
            audit_votes={"h": [{"agent_index": 0, "label": "AlreadyCanonical", "evidence_key": (7,)}]},
        )
        self.assertEqual(out["hypotheses"]["h"]["winning_label"], "AlreadyCanonical")
        self.assertEqual(out["hypotheses"]["h"]["winning_evidence"], [7])

    def test_empty_audit_objects_are_valid_and_do_not_invent_missing_hypotheses(self):
        results = [{"answer": {}}, {"answer": "{}"}]
        original = copy.deepcopy(results)
        out = build_aggregation_diagnostics("evidence_audit", results)
        self.assertEqual(results, original)
        self.assertEqual(out["audit_parse_status"], ["object", "object"])
        self.assertEqual(out["observed_hypothesis_ids"], [])
        self.assertEqual(out["hypotheses"], {})

    def test_audit_plain_json_matches_legacy_aggregation_for_every_strategy(self):
        from expgym.poolact import aggregate_results

        payload = json.dumps({"h": {"label": "Entailment", "evidence_ids": [1]}})
        for strategy in ("naive", "cached", "poolact"):
            with self.subTest(strategy=strategy):
                results = [{"answer": payload, "strategy": strategy}]
                out = build_aggregation_diagnostics("evidence_audit", results)
                aggregate = aggregate_results("evidence_audit", results)
                self.assertEqual(out["audit_parse_policy"], "legacy_json_loads_v1")
                self.assertEqual(out["audit_parse_status"], ["object"])
                self.assertEqual(out["hypotheses"]["h"]["winning_label"], "Entailment")
                self.assertEqual(out["hypotheses"]["h"]["winning_evidence"], [1])
                self.assertEqual(json.loads(aggregate["answer"]), json.loads(payload))

    def test_audit_wrapped_json_is_not_accepted_by_legacy_aggregation(self):
        from expgym.poolact import aggregate_results

        payload = json.dumps({"h": {"label": "Entailment", "evidence_ids": [1]}})
        for answer in (
            payload + ";",
            "```json\n" + payload + "\n```",
            "```\n" + payload + ";\n```;",
        ):
            for strategy in ("naive", "cached", "poolact"):
                with self.subTest(answer=answer, strategy=strategy):
                    results = [{"answer": answer, "strategy": strategy}]
                    out = build_aggregation_diagnostics("evidence_audit", results)
                    aggregate = aggregate_results("evidence_audit", results)
                    self.assertEqual(out["audit_parse_policy"], "legacy_json_loads_v1")
                    self.assertEqual(out["audit_parse_status"], ["invalid_json"])
                    self.assertEqual(out["observed_hypothesis_ids"], [])
                    self.assertEqual(out["hypotheses"], {})
                    self.assertEqual(json.loads(aggregate["answer"]), {})

    def test_audit_parser_does_not_extract_examples_from_prose_or_broken_fences(self):
        payload = json.dumps({"h": {"label": "Entailment", "evidence_ids": [1]}})
        for answer in ("For example: " + payload, "```json\n" + payload):
            with self.subTest(answer=answer):
                out = build_aggregation_diagnostics("evidence_audit", [{"answer": answer}])
                self.assertEqual(out["audit_parse_status"], ["invalid_json"])
                self.assertEqual(out["observed_hypothesis_ids"], [])
                self.assertEqual(out["hypotheses"], {})

    def test_diagnostics_do_not_override_caller_selection(self):
        out = build_aggregation_diagnostics(
            "restricted_search", [{"answer": "Alice"}, {"answer": "Bob"}],
            search_keys=[("alice",), ("bob",)], selected_agent_index=1,
        )
        self.assertEqual(out["selected_agent_index"], 1)
        self.assertFalse(out["selection_matches_rule"])

    def test_invalid_shapes_raise_without_scoring(self):
        with self.assertRaises(ValueError):
            build_aggregation_diagnostics("tuning", [])
        with self.assertRaises(ValueError):
            build_aggregation_diagnostics("unknown", [{}])
        with self.assertRaises(ValueError):
            build_aggregation_diagnostics("restricted_search", [{}])
        with self.assertRaises(ValueError):
            build_aggregation_diagnostics("tuning", [{}], selected_agent_index=2)


if __name__ == "__main__":
    unittest.main()
