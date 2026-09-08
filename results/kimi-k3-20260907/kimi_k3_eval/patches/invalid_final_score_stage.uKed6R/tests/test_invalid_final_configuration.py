"""Invalid model configurations score zero; evaluator failures remain failures."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from expgym.task_tuning import InvalidConfigurationError, evaluate_hpobench_action
from scripts.run_paper_sweep import _score_check, _score_result


class UniformIntegerHyperparameter:
    name = "count"
    lower = 0
    upper = 3


class TestInvalidFinalConfiguration(unittest.TestCase):
    def setUp(self):
        self.parameters = [UniformIntegerHyperparameter(),
                           SimpleNamespace(name="edge", choices=[0, 1, 2]),
                           SimpleNamespace(name="op", choices=["conv", "pool"])]
        self.benchmark = SimpleNamespace(objective_function=Mock(return_value={"function_value": 0.25, "cost": 12.5}))
        self.task = SimpleNamespace(config_space=SimpleNamespace(get_hyperparameters=lambda: self.parameters),
                                    fidelity={"epochs": 108}, benchmark=self.benchmark)
        self.valid = {"count": 1, "edge": 1, "op": "conv"}
        self.tools = {"evaluate_config": lambda payload: evaluate_hpobench_action(self.task, payload)}

    def check_invalid(self, payload):
        result = {"answer": payload, "answer_perf": None, "eval_records": [],
                  "api_calls": 3, "evaluations": 2, "total_overhead": 17.0, "tool_records": []}
        check = _score_result(result, self.tools, None)
        self.assertTrue(check["ok"], check)
        self.assertEqual(result["answer_perf"], 0.0)
        self.assertEqual(result["answer_score_source"], "offline_final_answer")
        self.assertEqual((result["api_calls"], result["evaluations"], result["total_overhead"]), (3, 2, 17.0))
        self.assertEqual(result["tool_records"], [])
        self.benchmark.objective_function.assert_not_called()

    def test_invalid_json_missing_unknown_and_list_shape_score_zero(self):
        for payload in ("not JSON", "{}", json.dumps(dict(self.valid, edge_20=1)),
                        "[]", "[1, 1, \"conv\", 99]", "null", "42", "true"):
            with self.subTest(payload=payload):
                self.check_invalid(payload)

    def test_invalid_types_ranges_and_nonfinite_numbers_score_zero(self):
        for key, value in (("count", "1"), ("count", 1.5), ("count", True),
                           ("count", 4), ("count", None), ("count", []),
                           ("count", {}), ("count", float("nan")), ("count", float("inf")),
                           ("count", 10 ** 400), ("edge", 1.5), ("edge", "1"),
                           ("edge", True), ("op", 1), ("op", "unknown")):
            with self.subTest(key=key, value=value):
                self.check_invalid(json.dumps(dict(self.valid, **{key: value})))

    def test_existing_validation_observations_and_zero_overhead_are_preserved(self):
        output, overhead = evaluate_hpobench_action(self.task, "{}")
        self.assertEqual(output, "Invalid config: missing count, edge, op. You must specify ALL parameters.")
        self.assertEqual(overhead, 0.0)
        output, overhead = evaluate_hpobench_action(self.task, json.dumps(dict(self.valid, count=9)))
        self.assertEqual(output, "Invalid config: count out of range")
        self.assertEqual(overhead, 0.0)
        with self.assertRaisesRegex(InvalidConfigurationError, "Unknown hyperparameter"):
            evaluate_hpobench_action(self.task, json.dumps(dict(self.valid, edge_20=1)))

    def test_integral_floats_are_normalized_before_backend(self):
        self.assertEqual(evaluate_hpobench_action(self.task, '{"count": 1.0, "edge": 1.0, "op": "conv"}'), (0.75, 12.5))
        config = self.benchmark.objective_function.call_args[1]["configuration"]
        self.assertIs(type(config["count"]), int)
        self.assertIs(type(config["edge"]), int)

    def test_fidelity_keys_keep_existing_ignored_override_behavior(self):
        evaluate_hpobench_action(self.task, json.dumps(dict(self.valid, epochs=1)))
        kwargs = self.benchmark.objective_function.call_args[1]
        self.assertEqual(kwargs["configuration"], self.valid)
        self.assertEqual(kwargs["fidelity"], {"epochs": 108})

    def test_backend_exceptions_are_not_invalid_configurations(self):
        for error in (ValueError("Unknown hyperparameter in backend"), FileNotFoundError("Missing data"),
                      TypeError("backend bug"), RuntimeError("invalid table")):
            with self.subTest(error=error):
                self.benchmark.objective_function.side_effect = error
                check = _score_result({"answer": json.dumps(self.valid), "answer_perf": None, "eval_records": []}, self.tools, None)
                self.assertFalse(check["ok"])
                self.assertNotIn("recomputed_perf", check)

    def test_generic_error_messages_and_missing_numeric_scores_still_fail(self):
        for tool_result in ((None, 1.0), ("Missing data", 1.0), ("Tool error: invalid table", 0.0),
                            ("invalid backend", 0.0), ("out of range cache offset", 0.0)):
            for reported in (None, 0.0):
                with self.subTest(tool_result=tool_result, reported=reported):
                    check = _score_result({"answer": "{}", "answer_perf": reported, "eval_records": []},
                                          {"evaluate_config": lambda _payload: tool_result}, None)
                    self.assertFalse(check["ok"])
                    self.assertIsNone(check.get("recomputed_perf"))

    def test_nonzero_reported_invalid_score_is_not_silently_replaced(self):
        for payload in ("{}", json.dumps(dict(self.valid, edge_20=1))):
            result = {"answer": payload, "answer_perf": 0.8, "eval_records": []}
            check = _score_result(result, self.tools, None)
            self.assertFalse(check["ok"])
            self.assertEqual(check["recomputed_perf"], 0.0)
            self.assertEqual(result["answer_perf"], 0.8)

    def test_existing_evaluation_records_are_not_overridden(self):
        result = {"answer": "{}", "answer_perf": None, "eval_records": [("old", "old", 0.8, 1.0)]}
        self.assertFalse(_score_result(result, self.tools, None)["ok"])
        self.assertIsNone(result["answer_perf"])

    def test_numeric_zero_degenerate_score_preserves_simulated_cost(self):
        self.benchmark.objective_function.return_value = {"function_value": 1.0, "cost": 12.5}
        output, perf, cost = evaluate_hpobench_action(self.task, json.dumps(self.valid))
        self.assertIn("invalid or degenerate", output)
        self.assertEqual((perf, cost), (0.0, 12.5))

    def test_real_configspace_integral_normalization(self):
        import ConfigSpace as CS
        from ConfigSpace.hyperparameters import UniformIntegerHyperparameter as IntegerHP, CategoricalHyperparameter
        config_space = CS.ConfigurationSpace()
        config_space.add_hyperparameters([IntegerHP("count", 0, 3), CategoricalHyperparameter("edge", [0, 1, 2])])
        def objective(configuration, fidelity):
            del fidelity
            CS.Configuration(config_space, values=configuration)
            return {"function_value": 0.25, "cost": 12.5}
        task = SimpleNamespace(config_space=config_space, fidelity={}, benchmark=SimpleNamespace(objective_function=objective))
        self.assertEqual(evaluate_hpobench_action(task, '{"count": 1.0, "edge": 1.0}'), (0.75, 12.5))


if __name__ == "__main__":
    unittest.main()
