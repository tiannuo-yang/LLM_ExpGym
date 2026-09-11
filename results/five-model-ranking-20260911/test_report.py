"""Focused synthetic fixtures for GPT frozen-score integration, no live calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_report as b


def native(**updates):
    r = dict(model=b.GPT, execution_complete='True', job_id='job1', metric='EA', endpoint='single',
             system='expgym', scenario='evidence_audit', family='contract_nli', item='doc1',
             budget='cost_free', strategy='single', N='1', unit='fraction', seed='2200',
             repeat='seed_2200', value='0.3', known_agent_subset_value='0.3',
             known_agents='1', expected_agents='1', stage_repeat_index='0')
    r.update(updates)
    return r


class AdapterTests(unittest.TestCase):
    def test_scope_public_projection_is_exact_and_source_bound(self):
        root = Path(__file__).resolve().parent
        public = (root / 'inputs/api_request_scope.json').read_bytes()
        source = public.replace(b'"Authorization": "[REDACTED]"',
                                b'"Authorization": "<credential; omitted from dump>"')
        result, metadata = b.public_snapshot({'id': 'api_request_scope'}, source)
        self.assertEqual(result, public)
        self.assertEqual(metadata['public_projection'], b.SCOPE_PROJECTION)
        with self.assertRaises(ValueError):
            b.public_snapshot({'id': 'api_request_scope'}, source + b' ')
        self.assertEqual(b.public_snapshot({'id': 'scores'}, b'unmodified'), (b'unmodified', {}))

    def test_fixed_audit_orders_fold_once(self):
        rows = [native(job_id='j' + str(i), seed=str(2200 + i), repeat='seed_' + str(2200 + i),
                       value=str(.3 * (i + 1))) for i in range(3)]
        folded = b.folded_gpt(rows)
        self.assertEqual(len(folded), 1)
        self.assertAlmostEqual(folded[0]['value'], .6)
        a = b.aggregate(folded)
        self.assertEqual((a['expected_outcomes'], a['original_logical_rows']), ('1', '3'))
        self.assertEqual((a['repeat_blocks'], a['descriptive_repeat_sd']), ('1', ''))
        self.assertEqual(a['analysis_unit'], 'document_mean_3_fixed_orders')

    def test_incomplete_audit_order_set_rejected(self):
        with self.assertRaises(ValueError):
            b.folded_gpt([native()])

    def test_duplicate_metric_identity_rejected(self):
        with self.assertRaises(ValueError):
            b.folded_gpt([native(), native()])

    def test_hpo_uses_seed_not_stage_repeat_index(self):
        rows = [native(job_id='j' + str(i), scenario='tuning', family='nasbench101', metric='Gap',
                       item='hpobench:nasbench101:A', seed=seed, repeat='seed_' + seed,
                       value=str(100 + i), unit='Gap points')
                for i, seed in enumerate(['2200', '2204', '2208'])]
        f = b.folded_gpt(rows)
        self.assertEqual({r['outerrep'] for r in f}, {'0', '1', '2'})
        a = b.aggregate(f)
        self.assertEqual(float(a['full_mean']), 101)
        self.assertEqual(float(a['descriptive_repeat_sd']), 1)

    def test_strict_pool_unknown_not_known_agent_subset(self):
        r = native(system='poolact', scenario='tuning', family='nasbench101', metric='Gap',
                   endpoint='MI', strategy='poolact', N='4', known_agents='3', expected_agents='4',
                   value='', known_agent_subset_value='98.4')
        folded = b.folded_gpt([r])
        a = b.aggregate(folded)
        self.assertEqual(a['full_mean'], '')
        self.assertEqual(a['known_subset_item_weighted_mean'], '')
        with self.assertRaises(ValueError):
            b.folded_gpt([dict(r, value='98.4')])

    def test_item_weighted_subset_and_complete_endpoint(self):
        f = []
        for item, values in [('a', [0, 0, 0]), ('b', [1, None, None])]:
            for i, v in enumerate(values):
                row = native(job_id=item + str(i), scenario='tuning', family='nasbench101', metric='Gap',
                             item=item, seed=str(2200 + i * 4), repeat='seed_' + str(2200 + i * 4),
                             value='' if v is None else str(v))
                f.extend(b.folded_gpt([row]))
        a = b.aggregate(f)
        self.assertEqual(a['full_mean'], '')
        self.assertEqual(float(a['known_subset_item_weighted_mean']), .5)
        self.assertEqual(a['descriptive_repeat_sd'], '')
        self.assertEqual(a['complete_items'], '1')

    def test_paired_difference_not_difference_of_known_subsets(self):
        rows = []
        for regime, values in zip(b.t.REGIMES, [[1, None, 0], [None, 0, .5], [0, 0, 0]]):
            for i, value in enumerate(values):
                rows.append(native(job_id=regime + str(i), scenario='tuning', family='nasbench101',
                                   metric='Gap', item='task-a', budget=regime, seed=str(2200 + 4 * i),
                                   repeat='seed_' + str(2200 + 4 * i), value='' if value is None else str(value)))
        a, blocks, contrasts = b.gpt_outputs(b.folded_gpt(rows))
        c = next(r for r in contrasts if r['slice_kind'] == 'all' and r['baseline'] == 'cost_free'
                 and r['target'] == 'cost_moderate')
        self.assertEqual(c['effect'], '')
        self.assertEqual(c['known_outcomes'], '1')
        self.assertEqual(float(c['known_paired_subset_effect']), -.5)
        b.t.check_rows(a)
        b.t.check_rows(blocks, True)
        b.t.check_contrasts(contrasts)

    def test_snapshot_sha_and_count_binding(self):
        spec = dict(id='x', origin='local', path='x.csv', rows=1, sha256_expected=None, local_path='inputs/x.csv')
        raw = b'a,b\n1,2\n'
        entry = dict(spec, bytes=len(raw), sha256=b.sha(raw), source='fixture')
        with tempfile.TemporaryDirectory() as tmp, patch.object(b, 'specs', return_value=[spec]):
            root = Path(tmp)
            (root / 'inputs').mkdir()
            (root / 'inputs/x.csv').write_bytes(raw)
            (root / 'INPUTS.json').write_bytes(b.jb({'files': [entry]}))
            self.assertEqual(b.read_inputs(root)['x'], [{'a': '1', 'b': '2'}])
            (root / 'inputs/x.csv').write_bytes(b'a,b\n9,9\n')
            with self.assertRaisesRegex(ValueError, 'SHA'):
                b.read_inputs(root)

    def test_duplicate_resource_setting_rejected(self):
        r = dict(model=b.GPT, scope='setting', system='expgym', scenario='tuning',
                 budget='cost_free', strategy='single')
        with self.assertRaisesRegex(ValueError, 'identity'):
            b.resources_table([copy.deepcopy(r) for _ in range(27)])


if __name__ == '__main__':
    unittest.main()
