import unittest

from expgym.tools_experiment import CONFIGS, run_config


class ToolsExperimentTest(unittest.TestCase):
    def test_run_config_returns_expected_pair(self) -> None:
        config_id = next(iter(CONFIGS))
        perf, overhead = run_config(config_id)
        self.assertEqual(perf, CONFIGS[config_id]["perf"])
        self.assertEqual(overhead, CONFIGS[config_id]["overhead"])

    def test_run_config_unknown_config_raises(self) -> None:
        with self.assertRaises(KeyError):
            run_config("missing_cfg")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
