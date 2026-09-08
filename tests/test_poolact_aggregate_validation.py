"""Aggregation input validation without changing the original voting rules."""
import json
import unittest

from expgym.poolact import aggregate_results


class AggregateValidationTest(unittest.TestCase):
    def test_audit_vote_acceptance_preserves_historical_json_loads_policy(self):
        answer = '{"h":{"label":"Entailment","evidence_ids":[1]}}'
        plain = aggregate_results('evidence_audit', [{'answer': answer, 'answer_perf': 1.}])
        self.assertEqual(json.loads(answer), json.loads(plain['answer']))
        for wrapped in (answer + ';', '```json\n' + answer + '\n```',
                        '```\n' + answer + '\n```;'):
            with self.subTest(wrapped=wrapped):
                actual = aggregate_results('evidence_audit', [{'answer': wrapped, 'answer_perf': 1.}])
                self.assertEqual('{}', actual['answer'])
                self.assertEqual('legacy_json_loads_v1', actual['diagnostics']['audit_parse_policy'])

    def test_finite_zero_scores_remain_valid(self):
        actual = aggregate_results('tuning', [{'answer': '{}', 'answer_perf': 0.}])
        self.assertEqual(0., actual['answer_perf'])

    def test_nonfinite_agent_scores_fail_explicitly_for_every_scenario(self):
        for scenario in ('tuning', 'restricted_search', 'evidence_audit'):
            for invalid in (float('nan'), float('inf'), -float('inf')):
                with self.subTest(scenario=scenario, invalid=invalid):
                    with self.assertRaisesRegex(ValueError, 'Non-finite score'):
                        aggregate_results(scenario, [
                            {'answer': '{}', 'answer_perf': invalid},
                            {'answer': '{}', 'answer_perf': .9},
                        ])

    def test_nonfinite_agent_metrics_are_not_hidden_by_valid_primary(self):
        with self.assertRaisesRegex(ValueError, 'answer_metrics.evidence_acc'):
            aggregate_results('evidence_audit', [{'answer': '{}', 'answer_perf': .9,
                                                 'answer_metrics': {'evidence_acc': float('nan')}}])

    def test_nonfinite_evaluator_output_fails_not_zero(self):
        for score in (float('nan'), {'label_acc': .9, 'evidence_acc': float('inf')}):
            with self.subTest(score=score):
                with self.assertRaisesRegex(ValueError, 'aggregate evaluator score'):
                    aggregate_results('evidence_audit', [{'answer': '{}'}],
                                      answer_evaluator=lambda answer, records: score)

    def test_evaluator_internal_type_error_is_not_retried(self):
        calls = []

        def evaluator(answer, records=None):
            calls.append((answer, records))
            raise TypeError('internal evaluator failure')

        with self.assertRaisesRegex(TypeError, 'internal evaluator failure'):
            aggregate_results('restricted_search', [{'answer': 'A'}], answer_evaluator=evaluator)
        self.assertEqual(1, len(calls))

    def test_legacy_one_argument_evaluator_runs_exactly_once(self):
        calls = []

        def evaluator(answer):
            calls.append(answer)
            return .25

        actual = aggregate_results('restricted_search', [{'answer': 'A'}], answer_evaluator=evaluator)
        self.assertEqual(.25, actual['answer_perf'])
        self.assertEqual(['A'], calls)

    def test_default_tie_and_empty_majority_rules_are_unchanged(self):
        tied = aggregate_results('restricted_search', [{'answer': 'refusal text'}, {'answer': 'B'}])
        self.assertEqual('refusal text', tied['answer'])
        self.assertEqual('highest_count_then_nonempty_key_then_first_agent',
                         tied['diagnostics']['tie_break_rule'])
        empty = aggregate_results('restricted_search', [{'answer': ''}, {'answer': ''}, {'answer': 'B'}])
        self.assertEqual('', empty['answer'])

    def test_audit_nonfinite_evidence_id_is_invalid_text_not_crash(self):
        actual = aggregate_results('evidence_audit', [{'answer': json.dumps({
            'h': {'label': 'Entailment', 'evidence_ids': [float('inf')]},
        })}])
        self.assertEqual(['inf'], json.loads(actual['answer'])['h']['evidence_ids'])

    def test_audit_exact_evidence_set_vote_still_only_uses_winning_label_supporters(self):
        answers = [
            {'h': {'label': 'Entailment', 'evidence_ids': [1, 2]}},
            {'h': {'label': 'Entailment', 'evidence_ids': [2, 1]}},
            {'h': {'label': 'Contradiction', 'evidence_ids': [3]}},
        ]
        actual = aggregate_results('evidence_audit', [{'answer': json.dumps(a)} for a in answers])
        self.assertEqual({'h': {'label': 'Entailment', 'evidence_ids': [1, 2]}},
                         json.loads(actual['answer']))


if __name__ == '__main__':
    unittest.main()
