"""Final-answer boundary and scorer/vote consistency, without model calls."""
import json
import unittest
from unittest.mock import patch

from expgym.poolact import aggregate_results
from expgym.react_loop import LLMOutput, run_react_loop
from expgym.task_evidence_audit import Document, build_answer_evaluator
from expgym.task_restricted_search import _extract_names, _name_f1
from expgym.tool_protocol import (
    ANSWER_PROTOCOL_VERSION, AUDIT_ANSWER_PROTOCOL_VERSION, AUDIT_FIELD_PROTOCOL_VERSION,
    audit_evidence_key,
    extract_text_answer, parse_audit_answer, parse_final_answer,
    parse_json_answer, parse_search_answer,
)


PAYLOAD = '{\n  "nda-1": {"label": "Entailment", "evidence_ids": [1]}\n}'
FENCED = '```json\n' + PAYLOAD + '\n```'


class AnswerBoundaryV2Test(unittest.TestCase):
    def test_prose_mentions_do_not_override_a_unique_final_directive(self):
        for prefix in ('I will answer: after checking the evidence.\n\n',
                       'Thought: consider Answer: {"candidate":2}\n',
                       'The answer: should be supplied as JSON.\n'):
            with self.subTest(prefix=prefix):
                self.assertEqual(parse_final_answer(prefix + '**Answer:**\n' + PAYLOAD), PAYLOAD)
        self.assertEqual(parse_final_answer('Thought: consider Answer: {"x":2}.Answer: {"x":1}'),
                         '{"x": 1}')

    def test_observed_markdown_and_intro_failures_preserve_payload(self):
        for prefix in ('**Answer:**\n', '__Answer:__\n', '**Answer**:\n',
                       '__Answer__:\n', 'Here is my final answer:\n\n**Answer:**\n',
                       'Final answer:\n\n**Answer:**\n', '- **Final Answer:**\n'):
            for suffix in (FENCED, FENCED + '\nKey rationale: evidence [1] supports this.'):
                with self.subTest(prefix=prefix, suffix=suffix):
                    self.assertEqual(extract_text_answer(prefix + suffix), suffix)
                    self.assertEqual(parse_final_answer(prefix + suffix), suffix)
                    self.assertEqual(parse_audit_answer(suffix), json.loads(PAYLOAD))

    def test_payload_markdown_and_literals_are_not_label_markup(self):
        for value in ('**Ada Lovelace**', '__Ada Lovelace__', '*Ada*', '_Ada_',
                      '{"note":"Answer: fake; Action: fake; <think>"}'):
            with self.subTest(value=value):
                self.assertEqual(parse_final_answer('Answer: ' + value), value)

    def test_whole_submission_emphasis_preserves_historical_payload_and_tail(self):
        for tail in ('', '\n\nReasoning: this is the selected name.'):
            raw = '**Answer: Ada Lovelace**' + tail
            self.assertEqual(parse_final_answer(raw), 'Ada Lovelace**' + tail)
        self.assertEqual(parse_final_answer("Grandmother **Bettye Gendron**'s sisters agree.\n"
                                            'Answer: Leana Wick, Tonia Wick'),
                         'Leana Wick, Tonia Wick')

    def test_empty_heading_chain_is_distinct_from_multiple_submissions(self):
        self.assertEqual(parse_final_answer('Answer:\nFinal Answer:\n' + PAYLOAD), PAYLOAD)
        for raw in ('Answer: thinking\nAnswer: ' + PAYLOAD,
                    'Answer: {}\n**Answer:** ' + PAYLOAD,
                    '{}\n**Answer:** ' + PAYLOAD,
                    '```json\n{}\n```\n__Answer:__ ' + PAYLOAD,
                    'Answer: one\nAnswer: two'):
            with self.subTest(raw=raw):
                self.assertIsNone(extract_text_answer(raw))
                self.assertIsNone(parse_final_answer(raw))

    def test_quoted_examples_and_tools_cannot_submit_an_answer(self):
        for raw in ('Thought: Example:\nAnswer: ' + PAYLOAD,
                    '> **Answer:** ' + PAYLOAD,
                    '"Answer: wrong"', '```text\nAnswer: wrong\n```',
                    '<think>Answer: wrong</think>', '<think>Answer: wrong',
                    'Action: search {"q":"x"}\nAnswer: ' + PAYLOAD,
                    'Answer: ' + PAYLOAD + '\nAction: search {"q":"x"}'):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_final_answer(raw))

    def test_text_transport_bare_prose_is_not_implicitly_promoted(self):
        self.assertIsNone(parse_final_answer('Ada Lovelace', allow_unlabelled=False))
        self.assertEqual(parse_final_answer('Ada Lovelace'), 'Ada Lovelace')
        self.assertEqual(parse_final_answer('Answer: Ada Lovelace', allow_unlabelled=False),
                         'Ada Lovelace')


class AuditWrapperV2Test(unittest.TestCase):
    def setUp(self):
        doc = Document(1, 'fixture', [], {'nda-1': {'choice': 'Entailment', 'spans': [1]}})
        with patch('expgym.task_evidence_audit._get_doc', return_value=doc), \
                patch('expgym.task_evidence_audit._get_labels', return_value={'nda-1': {}}):
            self.evaluator = build_answer_evaluator(0)

    def test_scorer_and_vote_share_wrapper_acceptance(self):
        for value in (PAYLOAD, PAYLOAD + ';', FENCED, FENCED + ';',
                      '```\n' + PAYLOAD + ';\n```;',
                      FENCED + '\nThe answer: follows the evidence in segment [1].',
                      FENCED + '\nReasoning: segment [1] is explicit.'):
            with self.subTest(value=value):
                score = self.evaluator(value, [])
                aggregate = aggregate_results('evidence_audit', [
                    {'answer': value, 'answer_perf': score['label_acc']},
                ], answer_evaluator=self.evaluator)
                self.assertEqual(score['label_acc'], 1.)
                self.assertEqual(score['evidence_acc'], 1.)
                self.assertEqual(aggregate['answer_metrics'], score)
                self.assertEqual(aggregate['diagnostics']['audit_parse_policy'],
                                 AUDIT_ANSWER_PROTOCOL_VERSION)

    def test_three_fenced_votes_beat_one_conflicting_plain_vote(self):
        wrong = '{"nda-1":{"label":"Contradiction","evidence_ids":[2]}}'
        aggregate = aggregate_results('evidence_audit', [
            {'answer': answer} for answer in (FENCED, FENCED, FENCED, wrong)
        ], answer_evaluator=self.evaluator)
        self.assertEqual(aggregate['answer_metrics']['label_acc'], 1.)
        self.assertEqual(aggregate['answer_metrics']['evidence_acc'], 1.)
        self.assertEqual(aggregate['diagnostics']['audit_parse_status'], ['object'] * 4)

    def test_ambiguous_wrappers_are_rejected_in_both_paths(self):
        for value in ('For example: ' + PAYLOAD, '```json\n' + PAYLOAD,
                      '```python\n' + PAYLOAD + '\n```',
                      FENCED + '\nAnswer: {}', FENCED + '\nAction: search {}',
                      FENCED + '\n{}', FENCED + '\n[1, 2]',
                      FENCED + '\n[\n1,\n2\n]', FENCED + '\n```json\n{}\n```'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_audit_answer(value)
                score = self.evaluator(value, [])
                aggregate = aggregate_results('evidence_audit', [{'answer': value}],
                                              answer_evaluator=self.evaluator)
                self.assertEqual(score['label_acc'], 0.)
                self.assertEqual(score['evidence_acc'], 0.)
                self.assertEqual(json.loads(aggregate['answer']), {})
                self.assertEqual(aggregate['answer_metrics'], score)

    def test_audit_wrapper_policy_does_not_relax_generic_json(self):
        value = FENCED + '\nExplanation of evidence [1].'
        self.assertEqual(parse_audit_answer(value), json.loads(PAYLOAD))
        with self.assertRaises(ValueError):
            parse_json_answer(value)

    def test_fields_and_historical_evidence_coercion_are_unchanged(self):
        value = '{"nda-1":{"label":"entailed","evidence_ids":["1"]}}'
        self.assertEqual(parse_audit_answer(value), json.loads(value))
        score = self.evaluator(value, [])
        self.assertEqual(score['label_acc'], 0.)  # Do not repair label spelling.
        self.assertEqual(score['evidence_acc'], 1.)  # Historical int coercion.

    def test_votes_cannot_repair_individually_incorrect_label_spellings(self):
        for label in ('entailed', 'entailment', ' Entailment ', 'neutral',
                      'not_mentioned', 'Entailment!', None, ['Entailment']):
            value = json.dumps({'nda-1': {'label': label, 'evidence_ids': [1]}})
            with self.subTest(label=label):
                individual = self.evaluator(value, [])
                aggregate = aggregate_results('evidence_audit', [{'answer': value}],
                                              answer_evaluator=self.evaluator)
                self.assertEqual(individual['label_acc'], 0.)
                self.assertEqual(aggregate['answer_metrics'], individual)
                self.assertEqual(aggregate['diagnostics']['audit_field_policy'],
                                 AUDIT_FIELD_PROTOCOL_VERSION)

    def test_vote_evidence_keys_match_scorer_iterable_and_all_or_empty_semantics(self):
        for value, expected in ((['1', 1.9, True], (1,)), ('1', (1,)),
                                ({'1': 'ignored'}, (1,)), ([1, 'bad'], ()),
                                (None, ()), (1, ()), ([float('inf')], ())):
            with self.subTest(value=value):
                self.assertEqual(audit_evidence_key(value), expected)
                answer = json.dumps({'nda-1': {'label': 'Entailment', 'evidence_ids': value}})
                individual = self.evaluator(answer, [])
                aggregate = aggregate_results('evidence_audit', [{'answer': answer}],
                                              answer_evaluator=self.evaluator)
                self.assertEqual(aggregate['answer_metrics'], individual)


class SearchAcceptanceV2Test(unittest.TestCase):
    def test_vote_uses_scorer_name_set_including_long_prose_filter(self):
        plain = 'Ada Lovelace'
        prose = 'Ada Lovelace\nThis explanatory sentence has more than five separate words'
        self.assertEqual(_extract_names(plain), _extract_names(prose))
        aggregate = aggregate_results('restricted_search', [
            {'answer': 'Grace Hopper'}, {'answer': plain}, {'answer': prose},
        ], answer_evaluator=lambda prediction: _name_f1(prediction, ['Ada Lovelace']))
        self.assertEqual(aggregate['answer'], plain)
        self.assertEqual(aggregate['answer_perf'], 1.)

    def test_parser_preserves_historical_json_array_and_text_rules(self):
        cases = {
            '1. Ada Lovelace; - Grace Hopper': {'ada lovelace', 'grace hopper'},
            '["Ada Lovelace", "Grace Hopper"]': {'ada lovelace', 'grace hopper'},
            '["1. Ada Lovelace"]': {'1. ada lovelace'},
            'This has six words in total': set(),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(parse_search_answer(value), expected)
                self.assertEqual(_extract_names(value), expected)


class RuntimeBoundaryV2Test(unittest.TestCase):
    def test_ambiguous_turn_requires_new_final_instead_of_choosing_a_payload(self):
        class Replay:
            supports_native_tools = True

            def __init__(self):
                self.outputs = iter(('Answer: first\nAnswer: second', 'Answer: final'))

            def generate(self, messages, **kwargs):
                return LLMOutput(next(self.outputs))

        result = run_react_loop(Replay(), {}, max_steps=1)
        self.assertEqual(result['answer'], 'final')
        self.assertEqual(result['answer_source'], 'forced_model_answer')
        self.assertEqual(result['api_calls'], 2)
        self.assertTrue(result['protocol_failures'])

    def test_natural_and_forced_final_use_same_parser_and_version(self):
        class Replay:
            supports_native_tools = True

            def generate(self, messages, **kwargs):
                return LLMOutput('Here is my final answer:\n**Answer:**\n' + FENCED)

        for max_steps in (0, 1):
            with self.subTest(max_steps=max_steps):
                result = run_react_loop(Replay(), {}, max_steps=max_steps)
                self.assertEqual(result['answer'], FENCED)
                self.assertEqual(result['answer_protocol_version'], ANSWER_PROTOCOL_VERSION)
                self.assertEqual(result['api_calls'], 1)
                self.assertEqual(result['answer_source'],
                                 'natural_model_answer' if max_steps else 'forced_model_answer')


if __name__ == '__main__':
    unittest.main()
