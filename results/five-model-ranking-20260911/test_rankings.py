"""Synthetic contract tests only; no frozen-study/raw/model/evaluator access."""

import copy
import csv
import io
import json
import random
import unittest

import rankings


def fixture():
    rows = []
    for endpoint in rankings.ENDPOINTS:
        for index, model in enumerate(rankings.MODELS):
            for regime in rankings.REGIMES:
                value = (0.1 + index * 0.1) if endpoint.unit == "fraction" else (90 + index)
                count = 3 if endpoint.scenario == "tuning" else 1
                rows.append({
                    "model": model, "system": "expgym", "scenario": endpoint.scenario,
                    "slice_kind": endpoint.slice_kind, "slice": endpoint.slice,
                    "regime": regime, "strategy": "single", "metric": endpoint.metric,
                    "N": "1", "unit": endpoint.unit, "higher_is_better": "True",
                    "expected_outcomes": str(count), "known_outcomes": str(count),
                    "missing_outcomes": "0", "expected_items": "1", "known_items": "1",
                    "complete_items": "1", "full_mean": str(value),
                    "source_input": "synthetic", "source_row": str(len(rows) + 2),
                    "source_url": "https://example.invalid/frozen-fixture",
                })
    return rows


def find(rows, key="whois_f1", model=rankings.MODELS[0], regime="cost_free"):
    endpoint = next(e for e in rankings.ENDPOINTS if e.key == key)
    return next(r for r in rows if r["model"] == model and r["regime"] == regime
                and r["scenario"] == endpoint.scenario and r["slice"] == endpoint.slice
                and r["metric"] == endpoint.metric)


def csv_rows(files, name="RANKINGS.csv"):
    return list(csv.DictReader(io.StringIO(files[name].decode())))


class RankingTests(unittest.TestCase):
    def test_interface_counts_determinism_and_secondary_denominators(self):
        rows = fixture()
        markers, files, summary = rankings.build(rows)
        self.assertEqual(set(markers), {"RANK_FAMILY", "RANK_TASK", "RANK_SUMMARY"})
        self.assertTrue(all(isinstance(value, str) for value in markers.values()))
        self.assertEqual(set(files), {"RANKINGS.csv", "RANK_TRANSITIONS.csv", "RANKINGS.md"})
        self.assertTrue(all(isinstance(value, bytes) for value in files.values()))
        self.assertEqual(summary["ranking_rows"], 270)
        self.assertEqual(summary["transition_rows"], 18)
        self.assertEqual([summary["categories"][k]["planned"] for k in ("family", "task", "secondary")], [6, 9, 3])
        json.dumps(summary, allow_nan=False)
        random.Random(42).shuffle(rows)
        self.assertEqual(rankings.build(rows), (markers, files, summary))

    def test_winner_changes_are_data_derived(self):
        rows = fixture()
        find(rows)["full_mean"] = "0.9"
        _, files, summary = rankings.build(rows)
        self.assertEqual(summary["categories"]["family"]["changed"], 1)
        self.assertEqual(summary["categories"]["task"]["changed"], 0)
        transition = next(r for r in csv_rows(files, "RANK_TRANSITIONS.csv") if r["endpoint"] == "whois_f1")
        self.assertEqual(transition["free_winners"], rankings.MODELS[0])
        self.assertEqual(transition["tight_winners"], rankings.MODELS[-1])

    def test_incomplete_candidate_excluded_across_all_regimes_not_zeroed(self):
        rows = fixture()
        model = rankings.MODELS[-1]
        row = find(rows, model=model)
        row.update(full_mean="", known_outcomes="0", missing_outcomes="1", known_items="0", complete_items="0")
        _, files, summary = rankings.build(rows)
        chosen = [r for r in csv_rows(files) if r["endpoint"] == "whois_f1" and r["model"] == model]
        self.assertEqual(len(chosen), 3)
        self.assertTrue(all(r["rank"] == "" and r["eligible_fixed_fmt"] == "False" for r in chosen))
        self.assertEqual(chosen[0]["full_mean"], "")
        self.assertEqual(chosen[1]["full_mean"], "0.5")
        self.assertTrue(all(r["excluded_reason"] == "incomplete_full_endpoint:cost_free" for r in chosen))
        self.assertEqual(summary["categories"]["family"]["strict_five_complete"], 5)

    def test_exact_tie_winner_set_and_margin(self):
        rows = fixture()
        find(rows, model=rankings.MODELS[0])["full_mean"] = "0.5"
        _, files, summary = rankings.build(rows)
        top = [r for r in csv_rows(files) if r["endpoint"] == "whois_f1" and r["regime"] == "cost_free" and r["winner"] == "True"]
        self.assertEqual(len(top), 2)
        self.assertTrue(all(r["rank"] == "1" and float(r["winner_runner_up_margin"]) == 0 for r in top))
        self.assertEqual(summary["categories"]["family"]["changed"], 1)

    def test_tie_anchor_prevents_transitive_chaining(self):
        groups, ranks = rankings._rank({"a": 0.5, "b": 0.5 - 0.75e-12, "c": 0.5 - 1.5e-12})
        self.assertEqual(groups, [["a", "b"], ["c"]])
        self.assertEqual(ranks, {"a": 1, "b": 1, "c": 3})

    def test_gap_above_100_preserved_and_zero_is_known(self):
        rows = fixture()
        find(rows, key="nas101_gap")["full_mean"] = "100.124052"
        find(rows)["full_mean"] = "0.0"
        _, files, _ = rankings.build(rows)
        above = next(r for r in csv_rows(files) if r["endpoint"] == "nas101_gap" and r["model"] == rankings.MODELS[0] and r["regime"] == "cost_free")
        self.assertEqual(above["full_mean"], "100.124052")
        zero = next(r for r in csv_rows(files) if r["endpoint"] == "whois_f1" and r["model"] == rankings.MODELS[0] and r["regime"] == "cost_free")
        self.assertEqual(zero["eligible_fixed_fmt"], "True")

    def test_fewer_than_two_candidates_not_ranked_or_counted(self):
        rows = fixture()
        for model in rankings.MODELS[1:]:
            find(rows, model=model).update(full_mean="", known_outcomes="0", missing_outcomes="1", known_items="0", complete_items="0")
        _, files, summary = rankings.build(rows)
        self.assertEqual(summary["categories"]["family"]["planned"], 6)
        self.assertEqual(summary["categories"]["family"]["rankable"], 5)
        self.assertTrue(all(r["rank"] == "" for r in csv_rows(files) if r["endpoint"] == "whois_f1"))

    def test_duplicate_and_missing_rows_fail_closed(self):
        rows = fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            rankings.build(rows + [copy.deepcopy(rows[0])])
        with self.assertRaisesRegex(ValueError, "Missing"):
            rankings.build(rows[1:])

    def test_invalid_accounting_mean_range_and_direction_fail(self):
        cases = [
            {"known_outcomes": "0"},
            {"known_outcomes": "0", "missing_outcomes": "1", "known_items": "0", "complete_items": "0"},
            {"full_mean": ""}, {"full_mean": "NaN"}, {"full_mean": "inf"},
            {"full_mean": "-0.01"}, {"full_mean": "1.1"}, {"higher_is_better": "False"},
            {"N": "4"}, {"slice_kind": "all"}, {"unit": "wrong"},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                rows = fixture()
                find(rows).update(changes)
                with self.assertRaises(ValueError):
                    rankings.build(rows)


if __name__ == "__main__":
    unittest.main()
