"""Small synthetic report contracts; never invokes models/scorers/raw archives."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_report as b


def row(**changes):
    r = dict(model='kimi-k3', system='expgym', scenario='tuning', slice_kind='all', slice='all',
             regime='cost_free', strategy='single', metric='gap', N='1', unit='Gap points',
             higher_is_better='True', scope='fixture', expected_outcomes='3', known_outcomes='3',
             missing_outcomes='0', expected_items='1', known_items='1', complete_items='1',
             full_mean='101.2', known_subset_item_weighted_mean='101.2',
             min_repeats_per_item='3', max_repeats_per_item='3', repeat_blocks='3',
             descriptive_repeat_sd='0.1', source_input='old_absolute', source_row='2', source_url='fixture')
    r.update(changes)
    return r


class ReportTests(unittest.TestCase):
    def test_gap_above_100_preserved(self):
        b.check_rows([row()])
        self.assertEqual(b.cell(row()), '101.200000')

    def test_unknown_is_not_zero_or_subset(self):
        r = row(known_outcomes='2', missing_outcomes='1', full_mean='', descriptive_repeat_sd='')
        b.check_rows([r])
        self.assertEqual(b.cell(r), 'unknown (2/3)')
        with self.assertRaises(ValueError):
            b.check_rows([dict(r, full_mean='0')])

    def test_incomplete_sd_rejected(self):
        with self.assertRaises(ValueError):
            b.check_rows([row(known_outcomes='2', missing_outcomes='1', full_mean='')])

    def test_r1_sd_not_fabricated(self):
        r = row(expected_outcomes='1', known_outcomes='1', repeat_blocks='1',
                min_repeats_per_item='1', max_repeats_per_item='1', descriptive_repeat_sd='0')
        with self.assertRaises(ValueError):
            b.check_rows([r])
        b.check_rows([dict(r, descriptive_repeat_sd='')])

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            b.check_rows([row(), row()])

    def test_invalid_denominators(self):
        for updates in [dict(missing_outcomes='1'), dict(expected_items='2'),
                        dict(known_outcomes='-1', missing_outcomes='4')]:
            with self.assertRaises(ValueError):
                b.check_rows([row(**updates)])

    def test_exp_direction_from_unrounded_values(self):
        values = [row(regime=r, full_mean=str(v), source_row=str(i + 2))
                  for i, (r, v) in enumerate(zip(b.REGIMES, [99.123456789, 95.12345678, 90.1234567]))]
        contrasts = b.legacy_contrasts(values)
        b.check_contrasts(contrasts)
        self.assertAlmostEqual(float(contrasts[0]['effect']), 4.000000009)
        self.assertEqual(len(contrasts), 3)

    def test_pool_cached_intermediate_negative_retained(self):
        values = [row(system='poolact', regime='cost_tight', strategy=s, full_mean=str(v))
                  for s, v in zip(b.STRATEGIES, [90, 99, 95])]
        c = b.legacy_contrasts(values)
        b.check_contrasts(c)
        self.assertEqual(float(next(x for x in c if x['baseline'] == 'cached')['effect']), -4)

    def test_wholly_unknown_old_contrast_stays_unknown(self):
        values = [row(regime=r, metric='feedback_visible', known_outcomes='0', missing_outcomes='3',
                      full_mean='', descriptive_repeat_sd='') for r in b.REGIMES]
        c = b.legacy_contrasts(values)
        b.check_contrasts(c)
        self.assertTrue(all(x['effect'] == '' and x['known_outcomes'] == '0' for x in c))

    def test_native_paired_subset_not_replaced(self):
        native = {'known_paired_subset_effect': '1.25', 'effect': '', 'known_outcomes': '1', 'expected_outcomes': '9'}
        copied = dict(native, derivation='unchanged native frozen paired contrast')
        self.assertEqual(copied['known_paired_subset_effect'], '1.25')
        self.assertEqual(b.cell(copied, 'effect'), 'unknown (1/9)')

    def test_sha_binding_and_pinned_url(self):
        spec = dict(id='fixture', repo='old', commit='a' * 40, path='published.json', expected_rows=None)
        raw = b'{}\n'
        entry = dict(spec, local_path='inputs/fixture.json', bytes=len(raw), sha256=b.sha(raw),
                     url=b.GH + spec['commit'] + '/' + spec['path'])
        with tempfile.TemporaryDirectory() as tmp, patch.object(b, 'specs', return_value=[spec]):
            root = Path(tmp)
            (root / 'inputs').mkdir()
            (root / entry['local_path']).write_bytes(raw)
            manifest = {'files': [entry]}
            (root / 'INPUTS.json').write_bytes(b.json_bytes(manifest))
            self.assertEqual(b.read_inputs(root), {'fixture': {}})
            (root / entry['local_path']).write_bytes(b'{"changed":true}')
            with self.assertRaisesRegex(ValueError, 'SHA'):
                b.read_inputs(root)
            (root / entry['local_path']).write_bytes(raw)
            bad = copy.deepcopy(manifest)
            bad['files'][0]['url'] = b.GH + 'main/published.json'
            (root / 'INPUTS.json').write_bytes(b.json_bytes(bad))
            with self.assertRaisesRegex(ValueError, 'URL'):
                b.read_inputs(root)

    def test_nonfinite_disallowed(self):
        for v in ['nan', 'inf', '-inf']:
            with self.assertRaises(ValueError):
                b.number(v)


if __name__ == '__main__':
    unittest.main()
