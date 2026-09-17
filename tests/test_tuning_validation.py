"""Model errors are typed; malformed backend numbers cannot become scores."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from expgym.errors import InvalidConfigurationError, ToolInputError
from expgym import task_tuning as tuning


class BackendValidationTest(unittest.TestCase):
    def setUp(self):
        self.backend = Mock(return_value={"function_value": 0.25, "cost": 12.5})
        self.space = SimpleNamespace(get_hyperparameters=lambda: [
            SimpleNamespace(name="x", lower=0, upper=1)])
        self.task = SimpleNamespace(benchmark=SimpleNamespace(objective_function=self.backend),
                                    config_space=self.space, fidelity={})

    def test_shared_exception_import_keeps_legacy_alias(self):
        self.assertIs(tuning.InvalidConfigurationError, InvalidConfigurationError)
        self.assertTrue(issubclass(InvalidConfigurationError, ToolInputError))

    def test_missing_backend_fields_do_not_default_to_zero(self):
        for result in ({}, {"cost": 1}, {"function_value": 0.25}):
            with self.subTest(result=result):
                self.backend.return_value = result
                with self.assertRaises(KeyError):
                    tuning.evaluate_hpobench_action(self.task, '{"x":0.5}')

    def test_bad_backend_values_fail_before_normalization(self):
        cases = [("function_value", value) for value in
                 (float("nan"), float("inf"), -float("inf"), -0.01, 100.01,
                  True, "0.25", None, 10 ** 400)]
        cases += [("cost", value) for value in
                  (float("nan"), float("inf"), -float("inf"), -0.01,
                   True, "12.5", None, 10 ** 400)]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.backend.return_value = dict({"function_value": 0.25, "cost": 12.5}, **{field: value})
                with self.assertRaises((TypeError, ValueError)) as caught:
                    tuning.evaluate_hpobench_action(self.task, '{"x":0.5}')
                self.assertNotIsInstance(caught.exception, ToolInputError)

    def test_nonmapping_backend_result_and_backend_exceptions_propagate(self):
        for result in (None, [], "Invalid config: backend table broken"):
            self.backend.return_value = result
            with self.assertRaises(TypeError):
                tuning.evaluate_hpobench_action(self.task, '{"x":0.5}')
        failure = ValueError("Invalid config: backend table broken")
        self.backend.side_effect = failure
        with self.assertRaises(ValueError) as caught:
            tuning.evaluate_hpobench_action(self.task, '{"x":0.5}')
        self.assertIs(caught.exception, failure)
        self.assertNotIsInstance(caught.exception, ToolInputError)

    def test_existing_valid_ratio_percent_and_zero_cost_semantics(self):
        for objective, perf in ((0.0, 1.0), (0.25, 0.75), (1.0, 0.0),
                                (25.0, 0.75), (100.0, 0.0)):
            self.backend.return_value = {"function_value": objective, "cost": 0.0}
            self.assertEqual(tuning._hpobench_evaluate(self.task, {}), (perf, 0.0))

    def test_model_input_errors_never_invoke_backend(self):
        for payload in (None, "not JSON", "null", "[]", "{}", '{"wrong":1}',
                        '{"x":NaN}', '{"x":Infinity}', '{"x":true}', '{"x":2}',
                        '[' * 2000 + '0' + ']' * 2000, '9' * 5000):
            with self.subTest(payload=payload), self.assertRaises(InvalidConfigurationError):
                tuning.evaluate_hpobench_action(self.task, payload)
        self.backend.assert_not_called()


class BuiltinValidationTest(unittest.TestCase):
    def setUp(self):
        self.config = dict(tuning.REFERENCE_CONFIGS[0])

    def test_builtin_rejects_wrong_shape_fields_and_noninteger_values(self):
        cases = [None, "bad JSON", "null", "[]", "{}", json.dumps(dict(self.config, extra=1)),
                 '[' * 2000 + '0' + ']' * 2000, '9' * 5000]
        for value in (True, "3", 3.5, None, [], float("nan"), float("inf"), 10 ** 400):
            cases.append(json.dumps(dict(self.config, num_layers=value)))
        with patch.object(tuning, "_performance") as backend:
            for payload in cases:
                with self.subTest(payload=payload), self.assertRaises(InvalidConfigurationError):
                    tuning.evaluate_config_action(payload)
            backend.assert_not_called()

    def test_builtin_integral_floats_keep_mathematical_value(self):
        as_float = {key: float(value) for key, value in self.config.items()}
        self.assertEqual(tuning.evaluate_config_action(json.dumps(as_float)),
                         tuning.evaluate_config(self.config))
        self.assertTrue(all(isinstance(value, float) for value in as_float.values()))

    def test_builtin_backend_numbers_cannot_be_masked(self):
        for function, values in (("_performance", (float("nan"), float("inf"), -0.1, 1.1, True)),
                                 ("_overhead", (float("nan"), float("inf"), -0.1, True))):
            for value in values:
                with self.subTest(function=function, value=value):
                    with patch.object(tuning, function, return_value=value):
                        with self.assertRaises((TypeError, ValueError)) as caught:
                            tuning.evaluate_config(self.config)
                        self.assertNotIsInstance(caught.exception, ToolInputError)

    def test_raw_builtin_nan_is_checked_before_clipping(self):
        with patch.object(tuning, "_hash_noise", return_value=float("nan")):
            for function in (tuning._performance, tuning._overhead):
                with self.assertRaisesRegex(ValueError, "must be finite"):
                    function(tuning._vectorize(self.config))


if __name__ == "__main__":
    unittest.main()
