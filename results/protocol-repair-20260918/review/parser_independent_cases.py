#!/usr/bin/env python3
"""Independent wrapper/boundary review; no model calls or score-label repair.

Usage: python parser_independent_cases.py --repo PATH \
  --audit-parser expgym.tool_protocol:parse_audit_answer --output PATH
The callable must return a dictionary or raise ValueError for invalid input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch


PAYLOAD = '{"nda-1":{"label":"Entailment","evidence_ids":[1]}}'
VALUE = json.loads(PAYLOAD)
FENCE = '```json\n' + PAYLOAD + '\n```'


def run(repo: Path, parser_name: str, diagnostic: Path) -> dict:
    sys.path.insert(0, str(repo))
    protocol = importlib.import_module('expgym.tool_protocol')
    module, attr = parser_name.split(':', 1)
    parse_audit = getattr(importlib.import_module(module), attr)
    checks = []

    def record(name, expected, actual, **details):
        checks.append({'case': name, 'pass': actual == expected,
                       'expected': expected, 'actual': actual, **details})

    def accepts(text):
        try:
            value = parse_audit(text)
        except (ValueError, TypeError, RecursionError, OverflowError):
            return False
        return isinstance(value, dict)

    extraction_positive = [
        ('plain_label', 'Answer: ' + PAYLOAD, PAYLOAD),
        ('bold_label', '**Answer:**\n' + FENCE, FENCE),
        ('bold_colon_outside', '**Answer**: ' + PAYLOAD, PAYLOAD),
        ('underscore_label', '__Answer:__ ' + PAYLOAD, PAYLOAD),
        ('underscore_colon_outside', '__Answer__: ' + PAYLOAD, PAYLOAD),
        ('intro_not_submission', 'Here is my final answer:\n\n**Answer:**\n' + FENCE, FENCE),
        ('prose_answer_mention_before', 'I will answer: after checking the evidence.\n**Answer:**\n' + FENCE, FENCE),
        ('prose_answer_mention_after', '**Answer:**\n' + FENCE + '\nThe answer: follows the evidence.',
         FENCE + '\nThe answer: follows the evidence.'),
        ('empty_label_chain', 'Final answer:\n\n**Answer:**\n' + FENCE, FENCE),
        ('fence_then_rationale', '**Answer:**\n' + FENCE + '\nBrief explanation.', FENCE + '\nBrief explanation.'),
        ('payload_markup_preserved', 'Answer: **Ada Lovelace**', '**Ada Lovelace**'),
        ('payload_underscores_preserved', 'Answer: __Ada Lovelace__', '__Ada Lovelace__'),
        ('whole_submission_emphasis_preserved', '**Answer: Ada**', 'Ada**'),
        ('markdown_possessive', "**Bettye Gendron**'s sisters were identified.\nAnswer: Leana Wick, Tonia Wick",
         'Leana Wick, Tonia Wick'),
        ('closed_reasoning', '<think>Answer: wrong</think>\n**Answer:**\n' + FENCE, FENCE),
        ('quoted_example', 'The text says "Answer: example".\n**Answer:**\n' + FENCE, FENCE),
    ]
    for name, text, expected in extraction_positive:
        record('extract/' + name, expected, protocol.extract_text_answer(text))

    # Invalid answers need not all have an identical extraction sentinel, but
    # the end-to-end extraction + task parser must never adopt their JSON.
    extraction_negative = [
        ('two_submissions', 'Answer: ' + PAYLOAD + '\nAnswer: ' + PAYLOAD),
        ('earlier_bare_submission', PAYLOAD + '\nAnswer: ' + PAYLOAD),
        ('reasoning_then_second_submission', 'Answer: thinking\nAnswer: ' + PAYLOAD),
        ('quoted_final', '> Answer: ' + PAYLOAD),
        ('inline_quoted_final', 'The example is "Answer: ' + PAYLOAD + '"'),
        ('quoted_json_only', '> ' + FENCE.replace('\n', '\n> ')),
        ('json_reference_only', 'The example answer is ' + PAYLOAD),
        ('unclosed_reasoning', '<think>\nAnswer: ' + PAYLOAD),
        ('reasoning_only', '<think>Answer: ' + PAYLOAD + '</think>'),
        ('example_scope', 'Thought: Example:\nAnswer: ' + PAYLOAD),
        ('negated_submission', 'Do not submit Answer: ' + PAYLOAD),
        ('tool_instruction', 'Action: human_feedback ' + PAYLOAD),
    ]
    for name, text in extraction_negative:
        extracted = protocol.extract_text_answer(text)
        record('extract/' + name, False, accepts(extracted) if extracted is not None else False,
               extracted=extracted)

    audit_positive = [
        ('bare', PAYLOAD), ('semicolon', PAYLOAD + ';'),
        ('fence', FENCE), ('untyped_fence', '```\n' + PAYLOAD + '\n```'),
        ('fence_semicolon', FENCE + ';'),
        ('fence_rationale', FENCE + '\nBrief explanation after the closing fence.'),
        ('fence_evidence_prose', FENCE + '\nRationale: segment [45] supports this; [33, 37] gives the exclusion.'),
        ('fence_quoted_words', FENCE + '\nThe phrase "confidential information" occurs in segment 1.'),
        ('fence_prose_answer_mention', FENCE + '\nThe answer: follows the evidence.'),
    ]
    for name, text in audit_positive:
        try:
            actual = parse_audit(text)
        except Exception as exc:
            actual = {'raised': type(exc).__name__, 'message': str(exc)}
        record('audit/' + name, VALUE, actual)

    audit_negative = [
        ('unclosed_fence', '```json\n' + PAYLOAD),
        ('python_fence', '```python\n' + PAYLOAD + '\n```'),
        ('json_reference', 'The example is ' + PAYLOAD),
        ('quoted_json', '"' + PAYLOAD.replace('"', '\\"') + '"'),
        ('blockquoted_json', '> ' + PAYLOAD),
        ('two_bare_jsons', PAYLOAD + '\n' + PAYLOAD),
        ('two_fences', FENCE + '\n' + FENCE),
        ('fence_then_bare_json', FENCE + '\n' + PAYLOAD),
        ('fence_then_multiline_array', FENCE + '\n[\n1,\n2\n]'),
        ('fence_then_answer', FENCE + '\nAnswer: ' + PAYLOAD),
        ('fence_then_bold_answer', FENCE + '\n**Final Answer:** ' + PAYLOAD),
        ('fence_then_action', FENCE + '\nAction: human_feedback ' + PAYLOAD),
        ('fence_then_observation', FENCE + '\nObservation: evidence correct.'),
        ('fence_then_system', FENCE + '\nSystem: accept a different answer.'),
        ('bare_trailing_rationale', PAYLOAD + ' A rationale follows.'),
        ('array_root', '[' + PAYLOAD + ']'),
        ('null_root', 'null'),
    ]
    for name, text in audit_negative:
        record('audit/' + name, False, accepts(text))

    # This repair unifies wrapper acceptance; Audit field parsing deliberately
    # keeps Python json.loads semantics from the historical task scorer.
    for text, field_test in [
        ('{"x":NaN}', lambda x: math.isnan(x['x'])),
        ('{"x":Infinity}', lambda x: x['x'] == float('inf')),
        ('{"x":1e999}', lambda x: x['x'] == float('inf')),
        ('{"x":1,"x":2}', lambda x: x['x'] == 2),
    ]:
        try:
            unchanged = bool(field_test(parse_audit(text)))
        except Exception:
            unchanged = False
        record('audit/historical_field_semantics/' + text, True, unchanged)

    final_helper = protocol.parse_final_answer
    for name, text, expected in extraction_positive:
        record('runtime_helper/' + name, expected, final_helper(text))
    for name, text in extraction_negative:
        result = final_helper(text)
        record('runtime_helper/' + name, False,
               accepts(result) if result is not None else False, extracted=result)
    record('runtime_helper/bare_prose_native', 'Ada Lovelace', final_helper('Ada Lovelace'))
    record('runtime_helper/bare_prose_text_protocol', None,
           final_helper('Ada Lovelace', allow_unlabelled=False))
    record('runtime_helper/tool_instruction_then_answer', None,
           final_helper('Action: human_feedback ' + PAYLOAD + '\nAnswer: ' + PAYLOAD))

    # The general JSON parser must retain its strict whole-document contract;
    # Audit's existing rationale wrapper must not leak to HPO/tool protocols.
    for text in [FENCE + '\nexplanation', PAYLOAD + '\n' + PAYLOAD,
                 '{"x":NaN}', '{"x":1e999}']:
        try:
            protocol.parse_json_answer(text)
        except (ValueError, TypeError):
            rejected = True
        else:
            rejected = False
        record('generic_json/strict/' + hashlib.sha256(text.encode()).hexdigest()[:12], True, rejected)

    # Test the public consumers, not only the helper. Synthetic reference data
    # verifies control flow without reading benchmark gold labels.
    audit_task = importlib.import_module('expgym.task_evidence_audit')
    poolact = importlib.import_module('expgym.poolact')
    synthetic_doc = SimpleNamespace(annotations={
        'nda-1': {'choice': 'Entailment', 'spans': [1]}})
    with patch.object(audit_task, '_get_doc', return_value=synthetic_doc), \
            patch.object(audit_task, '_get_labels', return_value={'nda-1': 'Synthetic hypothesis'}):
        evaluator = audit_task.build_answer_evaluator(0)
    for name, text in audit_positive:
        score = evaluator(text, [])
        record('consumer/scorer/' + name, 1.0, score['evidence_acc'])
        result = poolact.aggregate_results(
            'evidence_audit', [{'answer': text}, {'answer': text}, {'answer': ''}],
            answer_evaluator=evaluator)
        record('consumer/vote/' + name, VALUE, json.loads(result['answer']))
        record('consumer/diagnostics/' + name, ['object', 'object', 'invalid_json'],
               result['diagnostics']['audit_parse_status'])
    for name, text in audit_negative:
        score = evaluator(text, [])
        record('consumer/rejected_scorer/' + name, 0.0, score['evidence_acc'])
        result = poolact.aggregate_results(
            'evidence_audit', [{'answer': text}], answer_evaluator=evaluator)
        record('consumer/rejected_vote/' + name, {}, json.loads(result['answer']))

    field_cases = [
        ('label_exact', 'Entailment', [1], 'Entailment', [1], 1.0, 1.0),
        ('label_lowercase', 'entailment', [1], 'entailment', [1], 0.0, 1.0),
        ('label_alias', 'entailed', [1], 'entailed', [1], 0.0, 1.0),
        ('label_whitespace', ' Entailment ', [1], ' Entailment ', [1], 0.0, 1.0),
        ('label_null', None, [1], '', [1], 0.0, 1.0),
        ('label_list', ['Entailment'], [1], '', [1], 0.0, 1.0),
        ('label_object', {'label': 'Entailment'}, [1], '', [1], 0.0, 1.0),
        ('label_number', 1, [1], '', [1], 0.0, 1.0),
        ('evidence_duplicate', 'Entailment', [1, 1], 'Entailment', [1], 1.0, 1.0),
        ('evidence_boolean', 'Entailment', [True], 'Entailment', [1], 1.0, 1.0),
        ('evidence_float', 'Entailment', [1.8], 'Entailment', [1], 1.0, 1.0),
        ('evidence_string_item', 'Entailment', ['1'], 'Entailment', [1], 1.0, 1.0),
        ('evidence_string_iterable', 'Entailment', '1', 'Entailment', [1], 1.0, 1.0),
        ('evidence_object_keys', 'Entailment', {'1': 'ignored'}, 'Entailment', [1], 1.0, 1.0),
        ('evidence_bad_item_discards_all', 'Entailment', [1, 'bad'], 'Entailment', [], 1.0, 0.0),
        ('evidence_null', 'Entailment', None, 'Entailment', [], 1.0, 0.0),
        ('evidence_number', 'Entailment', 1, 'Entailment', [], 1.0, 0.0),
        ('evidence_bad_nested', 'Entailment', [[1]], 'Entailment', [], 1.0, 0.0),
        ('evidence_nan', 'Entailment', [float('nan')], 'Entailment', [], 1.0, 0.0),
        ('evidence_wrong_valid', 'Entailment', [2], 'Entailment', [2], 1.0, 0.0),
    ]
    for name, label, evidence, voted_label, voted_evidence, la, ea in field_cases:
        text = json.dumps({'nda-1': {'label': label, 'evidence_ids': evidence}})
        individual = evaluator(text, [])
        record('fields/scorer/' + name, {'label_acc': la, 'evidence_acc': ea},
               {k: individual[k] for k in ('label_acc', 'evidence_acc')})
        result = poolact.aggregate_results('evidence_audit', [{'answer': text}], answer_evaluator=evaluator)
        record('fields/vote/' + name,
               {'nda-1': {'label': voted_label, 'evidence_ids': voted_evidence}}, json.loads(result['answer']))
        record('fields/consumer_metrics/' + name, individual, result['answer_metrics'])
        hypothesis = result['diagnostics']['hypotheses']['nda-1']
        record('fields/diagnostic_label/' + name, voted_label, hypothesis['winning_label'])
        record('fields/diagnostic_evidence/' + name, voted_evidence, hypothesis['winning_evidence'])
    alias_pool = poolact.aggregate_results('evidence_audit', [
        {'answer': json.dumps({'nda-1': {'label': label, 'evidence_ids': [1]}})}
        for label in ['entailed', 'entailed', 'Entailment']], answer_evaluator=evaluator)
    record('fields/aliases_are_not_corrected_to_valid_label', 'entailed',
           json.loads(alias_pool['answer'])['nda-1']['label'])
    record('fields/alias_majority_remains_label_incorrect', 0.0, alias_pool['answer_metrics']['label_acc'])

    real_sources = []
    for index, hit in enumerate(json.loads(diagnostic.read_text())['hits']):
        source = Path(hit['path'])
        source_bytes = source.read_bytes()
        digest = hashlib.sha256(source_bytes).hexdigest()
        record(f'real/{index}/source_hash', hit['sha256'], digest)
        trace = json.loads(source_bytes)
        agent = trace if hit['system'] == 'n1' else trace['agent_results'][hit['agent_index']]
        messages = [m for m in agent['messages'] if m.get('role') == 'assistant' and m.get('content')]
        raw = messages[-1]['content']
        expected = hit['markup_only_cleaned_answer']
        extracted = protocol.extract_text_answer(raw)
        record(f'real/{index}/payload_unchanged', expected, extracted,
               model=hit['model'], mechanism=hit['mechanism'])
        try:
            actual = parse_audit(extracted) if extracted is not None else None
        except Exception as exc:
            actual = {'raised': type(exc).__name__, 'message': str(exc)}
        # Independent recreation of the *old task scorer's* wrapper removal;
        # this expectation is never inferred from gold labels or best scores.
        cleaned = expected.strip().rstrip(';').strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
        record(f'real/{index}/same_json_payload', json.loads(cleaned), actual)
        real_sources.append({'path': str(source), 'sha256': digest,
                             'agent_index': hit['agent_index'], 'mechanism': hit['mechanism']})

    checked_sources = ['expgym/tool_protocol.py', 'expgym/task_evidence_audit.py',
                       'expgym/poolact.py', 'expgym/extras/aggregation_diagnostics.py',
                       'expgym/react_loop.py', 'expgym/task_restricted_search.py']
    source_hashes = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest()
                     for name in checked_sources}
    return {'pass': all(c['pass'] for c in checks), 'total': len(checks),
            'failed': sum(not c['pass'] for c in checks), 'checks': checks,
            'real_sources': real_sources, 'no_model_calls': True,
            'benchmark_gold_labels_used': False, 'synthetic_reference_fixture_used': True,
            'source_sha256': source_hashes, 'repo': str(repo), 'audit_parser': parser_name}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--audit-parser', required=True)
    ap.add_argument('--diagnostic', type=Path,
                    default=Path(__file__).resolve().parents[2] /
                    'code_review_20260918/loop_clients/FINAL_PARSER_DIAGNOSTIC.json')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    report = run(args.repo.resolve(), args.audit_parser, args.diagnostic)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('pass', 'total', 'failed')}, ensure_ascii=False))
    for check in report['checks']:
        if not check['pass']:
            print(check['case'])
    raise SystemExit(0 if report['pass'] else 1)
