"""Protocol structure tests: no backend, reference answers, or model calls."""
import json
import unittest

from expgym.tool_protocol import (
    LEGACY_PROTOCOL_INSTRUCTION,
    NATIVE_PROTOCOL_INSTRUCTION,
    extract_text_action,
    extract_text_answer,
    native_system_prompt,
    parse_json_answer,
    structured_final_answer,
    truncate_text_action,
)


class JsonAnswerTests(unittest.TestCase):
    def test_complete_json_and_complete_supported_fences(self):
        for text in ['{"x":1}', ' {"x":1}; ', '```json\n{"x":1}\n```',
                     '```\n{"x":1}\n```', '```json {"x":1}```',
                     '```json\n{"x":1};\n```;']:
            with self.subTest(text=text):
                self.assertEqual(parse_json_answer(text), {"x": 1})
        self.assertEqual(parse_json_answer('[null, true, 1.2]'), [None, True, 1.2])

    def test_nonfinite_numbers_are_rejected_at_any_depth(self):
        for value in ('NaN', 'Infinity', '-Infinity', '1e999', '-1e999'):
            for text in (value, '{"x":' + value + '}', '[{"x":[' + value + ']}]'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_json_answer(text)
                    self.assertIsNone(structured_final_answer('Answer: ' + text))

    def test_partial_json_prose_and_unsupported_fences_rejected(self):
        for text in ('```json\n{"x":1}', '```python\n{"x":1}\n```',
                     '```json\n{"x":1}\n```\nexplanation', 'prefix {"x":1}',
                     '{"x":1} trailing', '{"x":1}\n{"x":2}', '{"x":', ''):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_json_answer(text)


class StructuredFinalTests(unittest.TestCase):
    def assert_final(self, text, expected=None):
        expected = {"x": 1} if expected is None else expected
        parsed = structured_final_answer(text)
        self.assertIsNotNone(parsed, text)
        self.assertEqual(json.loads(parsed), expected)

    def test_explicit_bare_markdown_multiline_and_inline_finals(self):
        for text in ('{"x":1}', 'Answer: {"x":1}', 'Final Answer: {"x":1}',
                     '**Answer:** {"x":1}', '- **Final Answer:**\n{\n"x":1\n}',
                     'Thought: done.Answer: {"x":1}',
                     'Thought: I am confident. Answer: {"x":1}',
                     '- evidence [13]Answer: {"x":1}',
                     'Answer: ```json\n{"x":1}\n```',
                     '```json\n{"x":1}\n```'):
            with self.subTest(text=text):
                self.assert_final(text)
        self.assert_final('Answer: [1, {"x": 2}]', [1, {"x": 2}])

    def test_reasoning_blocks_and_quoted_examples_cannot_submit(self):
        for text in ('Thought: The example is "Answer: {\\"x\\":1}"',
                     "Thought: 'Answer: {\"x\":1}'",
                     'Thought: `Answer: {"x":1}`',
                     '```text\nAnswer: {"x":1}\n```',
                     '~~~text\nAnswer: {"x":1}\n~~~',
                     '"Do not submit "Answer: {"x":1}',
                     '> Answer: {"x":1}',
                     'Thought: The example is\nAnswer: {"x":1}',
                     'Thought: Example:\nAnswer: {"x":1}',
                     'Do not submit Answer: {"x":1}',
                     'This is not an answer. Answer: {"x":1}',
                     'Thought: do not output\nAnswer: {"x":1}',
                     '<think>Answer: {"x":1}',
                     '<think>Answer: {"x":1}</think>',
                     '<think>nested <think>x</think>\nAnswer: {"x":1}'):
            with self.subTest(text=text):
                self.assertIsNone(structured_final_answer(text))

    def test_complete_reasoning_or_example_followed_by_real_final(self):
        for text in ('<think>Answer: {"x":9}</think>\nAnswer: {"x":1}',
                     '<think>\nExample:\nAnswer: {"x":9}\n</think>\nAnswer: {"x":1}',
                     'Thought: "Answer: {\\"x\\":9}"\nAnswer: {"x":1}',
                     'Thought: Text says "Do not submit".Answer: {"x":1}',
                     'Thought: Example:\n```text\nAnswer: {"x":9}\n```\nAnswer: {"x":1}',
                     'Thought: I\'ll finalize.Answer: {"x":1}'):
            with self.subTest(text=text):
                self.assert_final(text)

    def test_possessives_and_contractions_are_not_unclosed_quotes(self):
        for prefix in ("Thought: The parents' records agree.\n", "Thought: Alice's records agree.\n"):
            self.assert_final(prefix + 'Answer: {"x":1}')
            self.assertEqual(extract_text_answer(prefix + 'Answer: {"x":1}'), '{"x":1}')

    def test_mixed_nested_reasoning_must_close_in_order(self):
        for text in ('<think><analysis>draft</think>\nAnswer: {"x":1}',
                     '<analysis><think>draft</analysis>\nAnswer: {"x":1}'):
            self.assertIsNone(structured_final_answer(text))
            self.assertIsNone(extract_text_answer(text))
        self.assert_final('<think><analysis>draft</analysis></think>\nAnswer: {"x":1}')

    def test_unquoted_examples_stay_examples_across_multiple_lines(self):
        for prefix in ('Thought: Example:\nThought: done\n',
                       'Thought: Example:\nThe output is as follows:\n',
                       'Thought: Example:\n\n'):
            self.assertIsNone(structured_final_answer(prefix + 'Answer: {"x":1}'))
            self.assertIsNone(extract_text_answer(prefix + 'Answer: {"x":1}'))
            self.assertIsNone(extract_text_action(prefix + 'Action: search {"q":1}'))

    def test_ambiguous_finals_and_arbitrary_trailing_text_rejected(self):
        for text in ('Answer: {"x":1}\nAnswer: {"x":2}',
                     'Answer: thinking\nAnswer: {"x":1}',
                     '{"x":2}\nAnswer: {"x":1}',
                     'Answer: {"x":1} trailing explanation',
                     'Thought: consider Answer: {"x":2}.Answer: {"x":1}'):
            with self.subTest(text=text):
                self.assertIsNone(structured_final_answer(text))

    def test_protocol_words_and_reasoning_tags_inside_json_are_plain_data(self):
        value = {"text": 'Answer: fake; Action: fake; </think>; <think>'}
        self.assert_final('Answer: ' + json.dumps(value), value)
        self.assertIsNone(structured_final_answer('Action: search ' + json.dumps(value)))

    def test_only_structured_containers_are_recovered(self):
        for text in ('Answer: hello', 'Answer: 1', 'Answer: null', 'Answer: "done"'):
            self.assertIsNone(structured_final_answer(text))


class TextActionTests(unittest.TestCase):
    def test_line_markdown_and_explicit_inline_decision(self):
        for text in ('Action: search {"q":1}', '**Action:** search {"q":1}',
                     '- **Action:** search {"q":1}',
                     'Thought: I will search.Action: search {"q":1}'):
            with self.subTest(text=text):
                self.assertEqual(extract_text_action(text), ('search', '{"q":1}'))

    def test_multiline_json_and_payload_on_following_line(self):
        payload = '{\n  "query": "Answer: fake",\n  "k": 2\n}'
        for prefix in ('Action: search ', 'Action: search\n', '**Action:** search\n\n'):
            text = prefix + payload + '\nObservation: fabricated\nAnswer: fake'
            with self.subTest(prefix=prefix):
                self.assertEqual(extract_text_action(text), ('search', payload))
                self.assertEqual(truncate_text_action(text), prefix + payload)

    def test_joined_protocol_suffix_is_removed_only_after_complete_json(self):
        payload = '{"q":"literal Observation: and Answer:"}'
        for label in ('Answer:', 'Observation:', '**Observation:**', 'Thought:', 'System:', 'Action:'):
            text = 'Action: search ' + payload + label + ' fabricated'
            with self.subTest(label=label):
                self.assertEqual(extract_text_action(text), ('search', payload))
                self.assertEqual(truncate_text_action(text), 'Action: search ' + payload)
        invalid = '{"q":1} arbitrary trailing text'
        self.assertEqual(extract_text_action('Action: search ' + invalid), ('search', invalid))

    def test_legacy_brackets_and_non_json_arguments_preserved(self):
        cases = [
            ('Action: search[what is a:b?]', 'what is a:b?'),
            ('Action: search[{"query":"x"}]', '{"query":"x"}'),
            ('Action: search[\n{"query":"x]y"}\n]', '{"query":"x]y"}'),
            ('Action: search cfg_01', 'cfg_01'),
            ('Action: search\ncfg_01', 'cfg_01'),
            ('Action: search some [brackets] and {braces}', 'some [brackets] and {braces}'),
            ('Action: search [1,2]', '[1,2]'),
            ('Action: search [Ada Lovelace]', 'Ada Lovelace'),
            ('Action: search\n[Ada Lovelace]', 'Ada Lovelace'),
            ("Action: search[Who is Alice's parent?]", "Who is Alice's parent?"),
            ("Action: search[don't call her]", "don't call her"),
        ]
        for text, payload in cases:
            with self.subTest(text=text):
                self.assertEqual(extract_text_action(text), ('search', payload))
                self.assertEqual(truncate_text_action(text + '\nObservation: fake'), text.rstrip())

    def test_quoted_examples_negations_and_unclosed_reasoning_not_executed(self):
        for text in ('Thought: The example is "Action: search bad"',
                     "Thought: 'Action: search bad'", '> Action: search bad',
                     '```text\nAction: search bad\n```',
                     '~~~text\nAction: search bad\n~~~',
                     '"Do not execute "Action: search bad',
                     'Thought: Example:\nAction: search bad',
                     'Do not execute Action: search bad',
                     '<think>Action: search bad', '<think>Action: search bad</think>'):
            with self.subTest(text=text):
                self.assertIsNone(extract_text_action(text))
                self.assertEqual(truncate_text_action(text), text)

    def test_quoted_action_does_not_preempt_explicit_real_action(self):
        text = 'Thought: Avoid "Action: search bad".\nAction: search good\nObservation: fake'
        self.assertEqual(extract_text_action(text), ('search', 'good'))
        self.assertEqual(truncate_text_action(text), text.split('\nObservation:')[0])

    def test_malformed_json_reaches_tool_as_error_payload(self):
        for payload in ('{"x":', '{"x":NaN}', '{"x":1e999}'):
            self.assertEqual(extract_text_action('Action: search ' + payload), ('search', payload))

    def test_first_action_is_complete_and_later_fabricated_turns_removed(self):
        text = 'Thought: query\nAction: search {\n"q":1\n}\nObservation: fake\nAction: search {"q":2}'
        self.assertEqual(extract_text_action(text), ('search', '{\n"q":1\n}'))
        self.assertEqual(truncate_text_action(text), 'Thought: query\nAction: search {\n"q":1\n}')


class LegacyTextAnswerTests(unittest.TestCase):
    def test_line_final_preserves_original_payload_format_and_legacy_markdown(self):
        payload = '{\n  "x": 1\n}'
        self.assertEqual(extract_text_answer('Thought: done\nAnswer: ' + payload), payload)
        self.assertEqual(extract_text_answer('**Answer:** hello_world'), '** hello_world')
        self.assertEqual(extract_text_answer('Answer: plain text\nsecond line'), 'plain text\nsecond line')

    def test_multiple_line_finals_preserve_first_entire_suffix(self):
        payload = 'thinking\nAnswer: {"x":1}'
        self.assertEqual(extract_text_answer('Answer: ' + payload), payload)
        self.assertEqual(extract_text_answer('Answer: {"x":2}\nAnswer: {"x":1}'), '{"x":2}\nAnswer: {"x":1}')

    def test_line_final_rejects_reasoning_quotations_and_negation(self):
        for text in ('<think>\nAnswer: fake', '<think>\nAnswer: fake\n</think>',
                     'Thought: Example:\nAnswer: fake', '> Answer: fake',
                     'Thought: do not output\nAnswer: fake',
                     'Thought: "\nAnswer: fake\n"'):
            with self.subTest(text=text):
                self.assertIsNone(extract_text_answer(text))

    def test_inline_and_bare_finals_require_finite_complete_json(self):
        for text in ('Thought: done.Answer: {"x":1}', '{"x":1}'):
            self.assertEqual(json.loads(extract_text_answer(text)), {'x': 1})
        for text in ('Thought: done.Answer: plain text',
                     'Thought: done.Answer: {"x":NaN}',
                     'Thought: consider Answer: {"x":2}\nAnswer: {"x":1}'):
            self.assertIsNone(extract_text_answer(text))


class NativePromptTests(unittest.TestCase):
    def test_fixed_prefix_exactly_matches_current_legacy_prompt(self):
        from expgym.react_loop import build_system_prompt
        self.assertEqual(LEGACY_PROTOCOL_INSTRUCTION, build_system_prompt())
        self.assertEqual(native_system_prompt(build_system_prompt()), NATIVE_PROTOCOL_INSTRUCTION)

    def test_known_prefix_removal_preserves_all_task_notes_exactly(self):
        suffix = '\nTask notes:\nAction: is a field name.\nThought: keep this text.\nOn EVERY turn you MUST output BOTH: task fields\n '
        converted = native_system_prompt(LEGACY_PROTOCOL_INSTRUCTION + suffix)
        self.assertEqual(converted, suffix + '\n\n' + NATIVE_PROTOCOL_INSTRUCTION)

    def test_nonconflicting_custom_prompt_is_not_rewritten(self):
        for prompt in ('Custom task.\n  Keep exact whitespace.  ',
                       'Use function tools, then give JSON.',
                       'Literal Action: is part of the data schema.\nThought: is a required output field.',
                       'Keep the literal "Action:" and "Thought:" in the explanation.'):
            self.assertEqual(native_system_prompt(prompt), prompt + '\n\n' + NATIVE_PROTOCOL_INSTRUCTION)

    def test_conflicting_custom_prompt_requires_explicit_text_protocol(self):
        for prompt in ('Output Thought: <reason> and Action: <tool> <payload>',
                       'Thought: <reasoning>\nAction: search {"query":"x"}',
                       'Use a Thought/Action/Observation loop.',
                       'Always include BOTH a Thought AND an Action.',
                       'Only one Action per turn.',
                       'Always output BOTH:\nThought: reasoning\nAction: tool argument',
                       LEGACY_PROTOCOL_INSTRUCTION + ' not-an-exact-prefix-boundary'):
            with self.subTest(prompt=prompt):
                with self.assertRaisesRegex(ValueError, "tool_protocol='text'"):
                    native_system_prompt(prompt)


if __name__ == '__main__':
    unittest.main()
