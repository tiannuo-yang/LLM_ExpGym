import unittest
from gap0 import classify_terminal, utility, item_mean, number


class UtilityTests(unittest.TestCase):
    def test_complete_unchanged(self):
        self.assertEqual(utility(103, 103, 4, 4, 'gap_mi'), 103)

    def test_fixed_n_not_available_case_mean(self):
        self.assertEqual(utility(None, 80, 3, 4, 'gap_mi'), 60)

    def test_bon_known_max(self):
        self.assertEqual(utility(None, 92, 2, 4, 'gap_bon'), 92)

    def test_all_missing(self):
        self.assertEqual(utility(None, None, 0, 4, 'gap_bon'), 0)
        self.assertEqual(utility(None, None, 0, 4, 'gap_mi'), 0)
        self.assertEqual(utility(None, None, 0, 1, 'gap'), 0)

    def test_known_zero_is_not_missing(self):
        self.assertEqual(utility(None, 0, 2, 4, 'gap_mi'), 0)

    def test_nonfinite_or_negative_gap_rejected(self):
        for value in ('NaN', 'Infinity', '-1'):
            with self.assertRaises(ValueError):
                number(value)

    def test_wrong_pool_n_rejected(self):
        with self.assertRaises(ValueError):
            utility(None, 80, 2, 3, 'gap_mi')

    def test_inconsistent_strict_rejected(self):
        with self.assertRaises(ValueError):
            utility(90, 90, 3, 4, 'gap_mi')
        with self.assertRaises(ValueError):
            utility(None, None, 4, 4, 'gap_mi')

    def test_equal_item_weight(self):
        units = [dict(item='a'), dict(item='a'), dict(item='b')]
        self.assertEqual(item_mean(units, [20, 40, 90]), 60)

    @staticmethod
    def terminal():
        return dict(execution_complete='True', score_complete='False',
                    score_status='unscorable_missing_configuration',
                    terminal_classification='model_no_answer', policy_version='task-abstention-v1',
                    terminal_origin='normal_loop_return', raw_answer_is_null='True',
                    raw_answer_perf_is_null='True')

    def test_normal_missing_only(self):
        self.assertFalse(classify_terminal(self.terminal()))

    def test_failed_execution_not_zero(self):
        t = self.terminal()
        t['execution_complete'] = 'False'
        with self.assertRaises(ValueError):
            classify_terminal(t)

    def test_scorer_exception_not_zero(self):
        t = self.terminal()
        t['score_status'] = 'scorer_exception'
        with self.assertRaises(ValueError):
            classify_terminal(t)

    def test_exception_origin_not_zero(self):
        t = self.terminal()
        t['terminal_origin'] = 'exception'
        with self.assertRaises(ValueError):
            classify_terminal(t)

    def test_present_but_unscored_not_zero(self):
        t = self.terminal()
        t['raw_answer_is_null'] = 'False'
        with self.assertRaises(ValueError):
            classify_terminal(t)


if __name__ == '__main__':
    unittest.main()
