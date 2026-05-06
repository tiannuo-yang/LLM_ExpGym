import os
import unittest

from scripts.compute_hpobench_oracle import _summarize_task


def _has_hpobench_deps() -> bool:
    try:
        import ConfigSpace  # noqa: F401
        import nasbench  # noqa: F401
        import tabular_benchmarks  # noqa: F401
    except Exception:
        return False
    return True


class TestHPOBenchOracle(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("EXPGYM_ENABLE_HPOBENCH_TESTS") == "1" and _has_hpobench_deps(),
        "HPOBench deps not installed or tests disabled.",
    )
    def test_oracle_summary_smoke(self) -> None:
        summary = _summarize_task("hpobench:svm_surrogate", samples=5, seed=1206)
        self.assertEqual(summary["task"], "hpobench:svm_surrogate")
        self.assertEqual(summary["samples"], 5)
        self.assertIn("best_perf", summary)
        self.assertIn("best_config", summary)
        self.assertIsInstance(summary["unique_perf_count"], int)
