"""Small synthetic contracts; no model, scorer, raw or network dependency."""
import unittest
import copy
import build_summary as b


def fixture():
    original, utility = [], []
    for mi, model in enumerate(b.MODELS):
        for scenario, metric, pool_metric, families in [
            ('restricted_search', 'f1', 'f1_mv', ['whois', 'whatis']),
            ('evidence_audit', 'evidence_acc', 'evidence_acc_mv', ['evidence_audit']),
            ('tuning', 'gap0', 'gap0_mi', ['paramnet', 'nasbench101', 'nasbench201'])]:
            target, field = (utility, 'value') if scenario == 'tuning' else (original, 'full_mean')
            for bi, budget in enumerate(b.BUDGETS):
                value = 105 + mi - bi if scenario == 'tuning' else .9 - .01 * mi - .1 * bi
                for kind, sl in [('all', 'all')] + [('family', f) for f in families]:
                    target.append(dict(model=model, system='expgym', scenario=scenario, regime=budget,
                                       strategy='single', slice_kind=kind, slice=sl, metric=metric, **{field: value}))
                if bi:
                    for si, strategy in enumerate(b.STRATEGIES):
                        target.append(dict(model=model, system='poolact', scenario=scenario, regime=budget,
                                           strategy=strategy, slice_kind='all', slice='all', metric=pool_metric,
                                           **{field: value + (.01 if scenario != 'tuning' else 1) * si}))
    return original, utility


class SummaryTests(unittest.TestCase):
    def test_non_hpo_counts_complete_cartesian_and_empty_scoring(self):
        rows = []
        for m in b.MODELS[-2:]:
            for system in ['expgym', 'poolact']:
                for scenario in ['restricted_search', 'evidence_audit']:
                    for budget in (b.BUDGETS if system == 'expgym' else b.BUDGETS[1:]):
                        for strategy in (['single'] if system == 'expgym' else b.STRATEGIES):
                            rows.append(dict(model=m, system=system, scenario=scenario, regime=budget, strategy=strategy,
                                             planned=10, raw_null=0, scored_empty=0, exec_incomplete=0, score_incomplete=0))
        totals = [dict(model=m, planned=180, raw_null=0, scored_empty=0, exec_incomplete=0, score_incomplete=0) for m in b.MODELS[-2:]]
        data = dict(settings=rows, totals=totals)
        self.assertIn('0/180', b.non_hpo_sentence(data))
        for field in ['scored_empty', 'exec_incomplete', 'score_incomplete']:
            changed = copy.deepcopy(data)
            changed['settings'][0][field] = 1
            with self.assertRaises(ValueError):
                b.non_hpo_sentence(changed)
        changed = copy.deepcopy(data)
        changed['settings'][0] = changed['settings'][1]
        with self.assertRaises(ValueError):
            b.non_hpo_sentence(changed)

    def test_complete_main_matrix_and_scales(self):
        exp, pool, family = b.make_tables(*fixture())
        self.assertEqual((len(exp), len(pool), len(family)), (15, 30, 90))
        self.assertAlmostEqual(exp[0]['free'], 90)
        self.assertAlmostEqual(exp[0]['free_minus_tight'], 20)
        self.assertAlmostEqual(pool[0]['poolact_minus_naive'], 2)
        self.assertAlmostEqual(pool[0]['poolact_minus_cached'], 1)
        self.assertEqual(exp[10]['free'], 105)  # no upper cap or second scaling
        self.assertEqual({r['candidate_count'] for r in family}, {5})

    def test_missing_endpoint_not_silently_imputed_by_summary(self):
        a, g = fixture()
        g[0]['value'] = ''
        with self.assertRaises(ValueError):
            b.make_tables(a, g)

    def test_audit_uses_common_all_export_not_optional_family_alias(self):
        a, g = fixture()
        a = [r for r in a if not (r['scenario'] == 'evidence_audit' and r['slice_kind'] == 'family')]
        _, _, family = b.make_tables(a, g)
        self.assertEqual(len([r for r in family if r['family'] == 'Audit']), 15)

    def test_duplicate_rejected(self):
        a, g = fixture()
        with self.assertRaises(ValueError):
            b.make_tables(a + [a[0]], g)

    def test_nonfinite_rejected(self):
        a, g = fixture()
        a[0]['full_mean'] = 'nan'
        with self.assertRaises(ValueError):
            b.make_tables(a, g)

    def test_ties_are_anchored_at_top(self):
        values = dict(zip(b.MODELS, [1, 1 - .75e-12, 1 - 1.5e-12, .1, .2]))
        self.assertEqual(b.winner_set(values), b.MODELS[:2])

    def test_family_change_uses_same_five_candidates(self):
        a, g = fixture()
        for r in g:
            if r['model'] == b.MODELS[0] and r['regime'] == b.BUDGETS[2] and r['system'] == 'expgym' and r['slice'] == 'paramnet':
                r['value'] = 120
        _, _, family = b.make_tables(a, g)
        affected = [r for r in family if r['family'] == 'ParamNet']
        self.assertEqual(len(affected), 15)
        self.assertTrue(all(r['free_to_tight_winner_changed'] for r in affected))
        tight = [r['model'] for r in affected if r['regime'] == b.BUDGETS[2] and r['winner']]
        self.assertEqual(tight, [b.MODELS[0]])


if __name__ == '__main__':
    unittest.main()
