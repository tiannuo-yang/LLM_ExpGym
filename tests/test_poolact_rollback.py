"""N4 rollback must restore control flow without changing concurrent N1 runs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import tempfile
import unittest
from unittest.mock import patch

from demo_experiment import _SCENARIOS, _resolve_answer_evaluator
from expgym.extras.parallel_cache import SharedExplorationGraph
from expgym.poolact import aggregate_results, POOLACT_PROTOCOL_VERSION
from expgym.poolact_legacy import LEGACY_POOL_ANSWER_PROTOCOL
from expgym import poolact_legacy_tool_protocol as legacy
from expgym.react_loop import LLMOutput, run_react_loop
from expgym.task_evidence_audit import Document
from expgym.tool_protocol import ANSWER_PROTOCOL_VERSION
from scripts import run_poolact


class Replay:
    supports_native_tools = True

    def __init__(self, outputs, barrier=None):
        self.outputs = iter(outputs)
        self.barrier = barrier

    def generate(self, messages, **kwargs):
        if self.barrier is not None:
            barrier, self.barrier = self.barrier, None
            barrier.wait(timeout=5)
        return LLMOutput(next(self.outputs))


class PoolActRollbackTest(unittest.TestCase):
    def test_frozen_protocol_is_the_historical_public_source(self):
        repo = Path(__file__).resolve().parents[1]
        historical = repo / 'tools/historical_scorers/297c3d00a006f33fc5a8ca799ce91d327d92839e/expgym/tool_protocol.py'
        self.assertEqual(Path(legacy.__file__).read_bytes(), historical.read_bytes())

    def test_n1_and_n4_boundaries_remain_isolated_in_the_same_process(self):
        barrier = threading.Barrier(2)
        raw = 'Answer: first\nAnswer: second'

        def run(policy):
            kwargs = {} if policy is None else {'answer_protocol': policy}
            return run_react_loop(Replay([raw, 'Answer: final'], barrier), {}, max_steps=1, **kwargs)

        with ThreadPoolExecutor(max_workers=2) as executor:
            n1_future = executor.submit(run, None)
            n4_future = executor.submit(run, LEGACY_POOL_ANSWER_PROTOCOL)
            n1, n4 = n1_future.result(), n4_future.result()
        self.assertEqual((n1['answer'], n1['api_calls']), ('final', 2))
        self.assertEqual((n4['answer'], n4['api_calls']), ('first\nAnswer: second', 1))
        self.assertEqual(n1['answer_protocol_version'], ANSWER_PROTOCOL_VERSION)
        self.assertEqual(n4['answer_protocol_version'], LEGACY_POOL_ANSWER_PROTOCOL)

    def test_n4_natural_and_forced_native_finals_keep_historical_markup(self):
        for max_steps in (0, 1):
            for transport in ('native', 'text'):
                with self.subTest(max_steps=max_steps, transport=transport):
                    old = run_react_loop(Replay(['**Answer:** Ada Lovelace']), {},
                                         max_steps=max_steps, tool_protocol=transport,
                                         answer_protocol=LEGACY_POOL_ANSWER_PROTOCOL)
                    new = run_react_loop(Replay(['**Answer:** Ada Lovelace']), {},
                                         max_steps=max_steps, tool_protocol=transport)
                    self.assertEqual(old['answer'], '** Ada Lovelace')
                    self.assertEqual(new['answer'], 'Ada Lovelace')

    def test_n4_action_masking_is_historical_too(self):
        raw = "Grandmother **Bettye Gendron**'s sisters agree.\nAction: ping {}"
        counts = []
        tools = {'ping': lambda payload: counts.append(payload) or (1., 0.)}
        common = dict(max_steps=1, tool_protocol='text', answer_evaluator=lambda answer: 1.)
        new = run_react_loop(Replay([raw, 'Answer: done']), tools, **common)
        self.assertEqual(counts, ['{}'])
        counts.clear()
        old = run_react_loop(Replay([raw, 'Answer: done']), tools,
                             answer_protocol=LEGACY_POOL_ANSWER_PROTOCOL, **common)
        self.assertEqual(counts, [])
        self.assertEqual((new['answer'], old['answer']), ('done', 'done'))

    def test_n4_audit_evaluator_does_not_mutate_the_n1_scenario(self):
        document = Document(1, 'fixture', [], {'nda-1': {'choice': 'Entailment', 'spans': [1]}})
        raw = '```python\n{"nda-1":{"label":"Entailment","evidence_ids":[1]}}\n```'
        args = argparse.Namespace(question_index=0, cc_split='cc-large')
        original_builder = _SCENARIOS['evidence_audit']['build_answer_evaluator']
        with patch('expgym.task_evidence_audit._get_doc', return_value=document), \
                patch('expgym.task_evidence_audit._get_labels', return_value={'nda-1': {}}):
            n4 = run_poolact._resolve_answer_evaluator(_SCENARIOS['evidence_audit'], args)
            n1 = _resolve_answer_evaluator(_SCENARIOS['evidence_audit'], args)
        self.assertEqual(n4(raw, [])['label_acc'], 1.)
        self.assertEqual(n1(raw, [])['label_acc'], 0.)
        self.assertIs(_SCENARIOS['evidence_audit']['build_answer_evaluator'], original_builder)

    def test_historical_audit_vote_rejects_fences_and_normalizes_aliases(self):
        answer = '{"h":{"label":"entailed","evidence_ids":["1"]}}'
        voted = aggregate_results('evidence_audit', [{'answer': answer}])
        self.assertEqual(json.loads(voted['answer'])['h'], {'label': 'Entailment', 'evidence_ids': [1]})
        rejected = aggregate_results('evidence_audit', [{'answer': '```json\n' + answer + '\n```'}])
        self.assertEqual(json.loads(rejected['answer']), {})
        self.assertEqual(rejected['diagnostics']['audit_parse_policy'], 'legacy_json_loads_v1')

    def test_historical_search_vote_keeps_long_prose_in_vote_key(self):
        voted = aggregate_results('restricted_search', [
            {'answer': 'Grace Hopper'}, {'answer': 'Ada Lovelace'},
            {'answer': 'Ada Lovelace\nThis explanatory sentence has more than five separate words'},
        ])
        self.assertEqual(voted['answer'], 'Grace Hopper')

    def test_historical_graph_path_identity_and_protocol_are_restored(self):
        first = '{"long":"' + 'x' * 100 + '","edge_15":0}'
        second = first[:-2] + '1}'
        graph = SharedExplorationGraph()
        self.assertNotEqual(first, second)
        self.assertEqual(graph._eval_key(first), 'E:' + first[:80])
        self.assertEqual(graph._eval_key(first), graph._eval_key(second))
        self.assertEqual(POOLACT_PROTOCOL_VERSION, 'paper-graph-lock-v3')

    def test_every_pool_strategy_passes_the_legacy_policy_and_records_it(self):
        with tempfile.TemporaryDirectory() as directory:
            args = run_poolact.parse_args(['--backend', 'fake', '--agents', '1',
                                           '--output-dir', directory])
            config = run_poolact._resolved_config(args, None)
            self.assertEqual(config['answer_protocol'], LEGACY_POOL_ANSWER_PROTOCOL)
            for strategy in ('naive', 'cached', 'poolact'):
                with self.subTest(strategy=strategy), \
                        patch.object(run_poolact, 'run_react_loop', return_value={
                            'answer': '{}', 'answer_perf': .75,
                        }) as loop, \
                        patch.object(run_poolact, '_score_result', return_value={'ok': True}):
                    run_poolact._run_strategy(args, strategy, None, None, 'no_budget')
                    self.assertEqual(loop.call_args.kwargs['answer_protocol'], LEGACY_POOL_ANSWER_PROTOCOL)

    def test_unknown_answer_policy_fails_before_model_request(self):
        with self.assertRaisesRegex(ValueError, 'Unknown answer protocol'):
            run_react_loop(Replay([]), {}, answer_protocol='typo')


if __name__ == '__main__':
    unittest.main()
