"""Focused report-layer fixtures; never invoke models, tools or scorers."""
import csv
import io
import json
import unittest
from pathlib import Path

import build_report as build

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "all-models-latest-20260913"
H = build.load_helpers(INPUT / "render_report.py")


def row(model="unfamiliar-a", value=.5, regime="cost_moderate", strategy="naive", system="poolact", scene="restricted_search", metric="f1_mv", **extra):
    data = dict(model=model, system=system, scenario=scene, slice_kind="all", slice="all", regime=regime, strategy=strategy, metric=metric, unit="fraction", N=4 if system == "poolact" else 1, expected_units=2, known_units=2 if value is not None else 1, missing_units=0 if value is not None else 1, expected_items=2, complete_items=2 if value is not None else 1, repeats_min=1, repeats_max=1, full_mean=value, known_subset_mean=.8, cohort_id="fixture", source_input="fixture.csv", source_row=2)
    data.update(extra)
    return data


def report(rows, models=("unfamiliar-a",)):
    scope = []
    for model in models:
        for system in ("expgym", "poolact"):
            for scene in build.SCENES:
                for regime in H.REGIMES:
                    for strategy in (("single",) if system == "expgym" else ("naive", "cached", "poolact")):
                        matching = any(r["model"] == model and r["system"] == system and r["scenario"] == scene and r["regime"] == regime and r["strategy"] == strategy for r in rows)
                        scope.append(dict(model=model, system=system, scenario=scene, regime=regime, strategy=strategy, planned=matching))
    return H.Report(rows, {"models": [{"id": m} for m in models], "scope_plan": scope})


class NumericFixtures(unittest.TestCase):
    def test_scope_filter_preserves_model_order_and_strips_unselected(self):
        source = {"models": [{"id": x} for x in ("unwanted", "b", "a")], "scope_plan": [{"model": x} for x in ("unwanted", "a", "b")], "cutoff_utc": "fixed"}
        got = build.selected_manifest(source, ("a", "b"))
        self.assertEqual([m["id"] for m in got["models"]], ["a", "b"])
        self.assertEqual({m["model"] for m in got["scope_plan"]}, {"a", "b"})
        self.assertEqual(len(source["models"]), 3)

    def test_unknown_not_replaced_with_known_subset_or_zero(self):
        r = report([row(value=None)])
        found = r.find("unfamiliar-a", "poolact", "restricted_search", "cost_moderate", "naive", "f1_mv")
        self.assertIsNone(found["full_mean"])
        self.assertEqual(r.cell(found), "unknown [1/2]")
        self.assertEqual(found["known_subset_mean"], .8)

    def test_wins_require_all_three_known_and_strictly_greater(self):
        rows = [row(value=value, strategy=strategy) for strategy, value in (("naive", .4), ("cached", .5), ("poolact", .6))]
        r = report(rows)
        counts = build.claim_counts(r, H, [])
        self.assertEqual(counts["poolact"]["complete"], 1)
        self.assertEqual(counts["poolact"]["wins_both"], 1)
        rows[2]["full_mean"] = .5
        self.assertEqual(build.claim_counts(report(rows), H, [])["poolact"]["wins_both"], 0)
        rows[0]["full_mean"] = None
        self.assertEqual(build.claim_counts(report(rows), H, [])["poolact"]["complete"], 0)

    def test_negative_differences_use_unrounded_values(self):
        r = report([row(value=.63274, strategy="cached"), row(value=.63265, strategy="poolact")])
        c = next(r for r in r.contrasts() if r["from_strategy"] == "cached" and r["to_strategy"] == "poolact")
        self.assertLess(c["delta"], 0)
        self.assertAlmostEqual(c["delta"], -.00009)
        self.assertEqual(c["display_delta"], "-0.01")

    def test_gap_not_multiplied_or_clipped(self):
        self.assertEqual(H._display({"metric": "gap0", "unit": "gap_points", "full_mean": 110.2}), "110.20")
        self.assertEqual(H._display({"metric": "gap", "unit": "gap_points", "full_mean": -7.2}), "-7.20")

    def test_rank_ties_and_missing_candidate_block_universal_winner(self):
        rows = [row(model=m, value=.7, regime=g, strategy="single", system="expgym", metric="f1", slice_kind="family", slice="whois") for m in ("unfamiliar-a", "unfamiliar-b") for g in H.REGIMES]
        r = report(rows, ("unfamiliar-a", "unfamiliar-b"))
        ranks, _ = r.rankings()
        self.assertTrue(all(x["rank"] == 1 and x["overall_winner"] for x in ranks))
        rows[-1]["full_mean"] = None
        ranks, transitions = report(rows, ("unfamiliar-a", "unfamiliar-b")).rankings()
        tight = [x for x in ranks if x["regime"] == "cost_tight"]
        self.assertFalse(any(x["overall_winner"] for x in tight))
        self.assertTrue(all(x["eligible_models"] == "unfamiliar-a" for x in transitions))
        self.assertTrue(all(x["excluded_models"] == "unfamiliar-b" for x in transitions))

    def test_duplicate_setting_cannot_be_chosen(self):
        r = report([row(value=.1), row(value=.9)])
        self.assertIsNone(r.find("unfamiliar-a", "poolact", "restricted_search", "cost_moderate", "naive", "f1_mv"))


class FrozenInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build.build(INPUT)

    def test_deterministic_rebuild_and_no_claude_numeric_rows(self):
        self.assertEqual(self.outputs, build.build(INPUT))
        for filename, text in self.outputs.items():
            if filename.endswith(".csv"):
                rows = list(csv.DictReader(io.StringIO(text)))
                self.assertTrue(all(r["model"] in build.MODELS for r in rows), filename)

    def test_original_numeric_rows_retained_without_rescoring(self):
        for filename in build.COPIED_CSV:
            _, source = build.read_csv(INPUT / filename)
            expected = [r for r in source if r["model"] in build.MODELS]
            actual = list(csv.DictReader(io.StringIO(self.outputs[filename])))
            self.assertEqual(actual, expected)

    def test_current_coverage_and_counts(self):
        checks = json.loads(self.outputs["REPORT_CHECKS.json"])
        self.assertEqual(checks["totals"]["execution_complete"], 4682)
        self.assertEqual(checks["totals"]["planned"], 4698)
        self.assertEqual(checks["totals"]["score_complete"], 4671)
        self.assertEqual(checks["claims"]["poolact"], {"planned": 36, "complete": 33, "wins_both": 29, "tight_complete": 17, "tight_wins_both": 16})
        self.assertLessEqual(len(self.outputs["README.zh.md"].splitlines()), 90)


if __name__ == "__main__":
    unittest.main()
