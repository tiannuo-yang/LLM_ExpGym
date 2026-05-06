"""Tests for reproduce.py — paper-number reproduction from bundled traces."""
import json
import os
import sys
import tempfile
import unittest

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import reproduce


class LoadTracesTest(unittest.TestCase):
    def test_default_fixture_present_and_valid(self):
        """The shipped fixture must exist and parse as a list of records."""
        traces = reproduce.load_traces(reproduce.DEFAULT_TRACES)
        self.assertIsInstance(traces, list)
        self.assertGreater(len(traces), 0)
        # Spot-check one record has the fields compute_f1_table needs.
        for key in ("model_tag", "eei_mode", "data_source", "answer_perf"):
            self.assertIn(key, traces[0], f"fixture missing key {key!r}")

    def test_default_fixture_has_324_whois_records(self):
        """Fixture must have the 324 whois records reproduce.py expects."""
        traces = reproduce.load_traces(reproduce.DEFAULT_TRACES)
        whois = [t for t in traces if t.get("data_source") == "phantom_seed1"]
        self.assertEqual(len(whois), 324)

    def test_load_rejects_non_list(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"oops": "not a list"}, f)
            path = f.name
        try:
            with self.assertRaises(ValueError):
                reproduce.load_traces(path)
        finally:
            os.unlink(path)


class ComputeF1TableTest(unittest.TestCase):
    def test_aggregates_by_model_and_mode(self):
        traces = [
            {"scenario": "restricted_search", "data_source": "phantom_seed1",
             "model_tag": "x", "eei_mode": "noneei", "answer_perf": 1.0},
            {"scenario": "restricted_search", "data_source": "phantom_seed1",
             "model_tag": "x", "eei_mode": "noneei", "answer_perf": 0.0},
            {"scenario": "restricted_search", "data_source": "phantom_seed1",
             "model_tag": "x", "eei_mode": "eei", "answer_perf": 0.5},
        ]
        table = reproduce.compute_f1_table(traces)
        self.assertAlmostEqual(table["x"]["noneei"][0], 0.5, places=6)
        self.assertEqual(table["x"]["noneei"][1], 2)
        self.assertAlmostEqual(table["x"]["eei"][0], 0.5, places=6)
        self.assertEqual(table["x"]["eei"][1], 1)

    def test_filters_out_non_whois_and_other_scenarios(self):
        traces = [
            # Should be excluded: wrong data_source.
            {"scenario": "restricted_search", "data_source": "phantom_seed1:whatis",
             "model_tag": "x", "eei_mode": "noneei", "answer_perf": 0.9},
            # Should be excluded: wrong scenario.
            {"scenario": "tuning", "data_source": "phantom_seed1",
             "model_tag": "x", "eei_mode": "noneei", "answer_perf": 0.9},
            # Should be included.
            {"scenario": "restricted_search", "data_source": "phantom_seed1",
             "model_tag": "x", "eei_mode": "noneei", "answer_perf": 0.4},
        ]
        table = reproduce.compute_f1_table(traces)
        self.assertEqual(table["x"]["noneei"], (0.4, 1))


class ReproductionMatchesPaperTest(unittest.TestCase):
    """The key claim the README makes: 18/18 cells match the paper."""

    def test_default_fixture_matches_paper_table(self):
        traces = reproduce.load_traces(reproduce.DEFAULT_TRACES)
        table = reproduce.compute_f1_table(traces)

        diffs = []
        for model_tag in reproduce.PAPER_TABLE:
            for mode, paper_value in reproduce.PAPER_TABLE[model_tag].items():
                computed, n = table[model_tag][mode]
                if abs(computed - paper_value) >= reproduce.TOLERANCE:
                    diffs.append((model_tag, mode, computed, paper_value))
                self.assertEqual(n, 18, f"expected n=18 for {model_tag}/{mode}")
        self.assertEqual(diffs, [], f"cells diverged from paper: {diffs}")


if __name__ == "__main__":
    unittest.main()
