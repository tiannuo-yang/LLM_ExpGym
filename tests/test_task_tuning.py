import json
import unittest

from expgym.task_tuning import (
    PARAMETER_RANGES,
    REFERENCE_CONFIGS,
    describe_parameter_ranges,
    evaluate_config,
    evaluate_config_action,
    format_config,
    summarize_goal,
)


class ToolsTuningTest(unittest.TestCase):
    def test_evaluate_config_returns_reasonable_values(self) -> None:
        config = REFERENCE_CONFIGS[0]
        perf, overhead = evaluate_config(config)
        self.assertGreaterEqual(perf, 0.0)
        self.assertLessEqual(perf, 1.0)
        self.assertGreaterEqual(overhead, 0.2)
        self.assertIn("Goal:", summarize_goal(include_overhead=True))

    def test_evaluate_config_rejects_invalid_value(self) -> None:
        config = dict(REFERENCE_CONFIGS[0])
        config[PARAMETER_RANGES[0].name] = PARAMETER_RANGES[0].high + 1
        with self.assertRaises(ValueError):
            evaluate_config(config)

    def test_evaluate_config_action_accepts_list_payload(self) -> None:
        config = REFERENCE_CONFIGS[1]
        payload = [config[p.name] for p in PARAMETER_RANGES]
        perf_action, _ = evaluate_config_action(json.dumps(payload))
        perf_direct, _ = evaluate_config(config)
        self.assertEqual(perf_action, perf_direct)

    def test_format_config_orders_keys(self) -> None:
        config = REFERENCE_CONFIGS[2]
        encoded = format_config(config)
        decoded = json.loads(encoded)
        ordered_names = [p.name for p in PARAMETER_RANGES]
        self.assertEqual(list(decoded.keys()), ordered_names)

    def test_describe_parameter_ranges_lists_every_param(self) -> None:
        description = describe_parameter_ranges()
        for param in PARAMETER_RANGES:
            self.assertIn(param.name, description)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
