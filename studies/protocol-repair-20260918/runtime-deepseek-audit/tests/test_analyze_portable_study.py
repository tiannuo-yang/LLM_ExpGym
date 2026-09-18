import copy
import csv
import importlib.util
import itertools
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "analyze_portable_study.py"
SPEC = importlib.util.spec_from_file_location("analyze_portable_study", SCRIPT)
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


class PortableStudyTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest_path = self.root / "manifest.json"
        self.csv_path = self.root / "metrics.csv"
        self.receipt_path = self.root / "audit.json"
        self.manifest = {
            "schema_version": 1,
            "study_id": "arbitrary-model-custom-study",
            "registration": {"selection_rule": "fixed_manifest_no_outcome_selection",
                             "frozen_before_evaluation": True, "protocol_id": "unit-test-v1"},
            "bootstrap": {"samples": 4000, "seed": 19, "confidence": 0.95},
            "metrics": {
                "f1": {"unit": "fraction", "higher_is_better": True, "minimum": 0, "maximum": 1},
                "protocol_ok": {"unit": "fraction", "higher_is_better": True, "minimum": 0, "maximum": 1},
            },
            "artifacts": [], "quality_gates": [], "comparisons": [],
        }
        self.rows = []
        for system in ("expgym", "poolact"):
            for item in ("q0", "q1", "q2"):
                for seed in ("40", "41"):
                    conditions = (("cost_free", "single", 0.8), ("cost_tight", "single", 0.6)) if system == "expgym" else (
                        ("cost_tight", "naive", 0.7), ("cost_tight", "poolact", 0.6))
                    for regime, strategy, score in conditions:
                        name = f"artifacts/{system}_{item}_{seed}_{regime}_{strategy}.json"
                        path = self.root / name
                        path.parent.mkdir(exist_ok=True)
                        path.write_text(json.dumps({"test_fixture_score": score}), encoding="utf-8")
                        identity = dict(model="arbitrary/provider-model", system=system, scenario="restricted_search",
                                        item=item, regime=regime, strategy=strategy, outerseed=seed)
                        artifact = dict(identity, artifact=name, metrics=["f1", "protocol_ok"], split="heldout",
                                        unit="single_trace" if system == "expgym" else "pool_aggregate")
                        self.manifest["artifacts"].append(artifact)
                        for metric, value in (("f1", score), ("protocol_ok", 1.0)):
                            self.rows.append(dict(identity, metric=metric, value=value, artifact=name))
            gate_id = system + "_protocol"
            self.manifest["quality_gates"].append({"id": gate_id, "metric": "protocol_ok", "operator": ">=",
                                                    "threshold": 0.99, "selectors": dict(model="arbitrary/provider-model",
                                                    system=system, scenario="restricted_search", split="heldout")})
            comparison = dict(id=system + "_effect", kind="expgym_free_tight" if system == "expgym" else "poolact_vs_naive",
                              model="arbitrary/provider-model", scenario="restricted_search", split="heldout",
                              family="all_primary_endpoints", role="primary", metric="f1",
                              items=["q0", "q1", "q2"], outerseeds=["40", "41"], bootstrap_method="item_cluster",
                              minimum_items=3, minimum_outerseeds=2, minimum_effect=0.01,
                              scope={"data_snapshots": ["synthetic-fixed-snapshot"],
                                     "item_status": "prospectively_reserved",
                                     "inference_population": "registered_items_only",
                                     "outer_repetition_interpretation": "seed_labels_only"},
                              quality_gate_ids=[gate_id], strategy="single" if system == "expgym" else "poolact")
            if system == "poolact":
                comparison["regime"] = "cost_tight"
            self.manifest["comparisons"].append(comparison)
        self.save()

    def save(self, receipt=True):
        self.manifest_path.write_text(json.dumps(self.manifest, sort_keys=True), encoding="utf-8")
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=study.CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        self.manifest_hash = study.sha256_file(self.manifest_path)
        if receipt:
            hashes = {entry["artifact"]: study.sha256_file(self.root / entry["artifact"])
                      for entry in self.manifest["artifacts"] if (self.root / entry["artifact"]).is_file()}
            self.receipt_path.write_text(json.dumps({"schema_version": 1, "manifest_sha256": self.manifest_hash,
                "csv_sha256": study.sha256_file(self.csv_path), "artifact_sha256": hashes,
                "complete": True, "score_recomputation_passed": True}), encoding="utf-8")

    def analyze(self, receipt=True):
        return study.analyze(self.manifest_path, self.csv_path, self.manifest_hash,
                             self.receipt_path if receipt else None)

    def test_effect_direction_and_negative_result_retained(self):
        report = self.analyze()
        expgym, poolact = report["comparisons"]
        self.assertAlmostEqual(expgym["effect"], 0.2)
        self.assertAlmostEqual(poolact["effect"], -0.1)
        self.assertEqual(expgym["status"], "not_confirmatory")
        self.assertEqual(poolact["status"], "not_confirmatory")
        self.assertEqual(expgym["observed_direction"], "positive")
        self.assertEqual(poolact["observed_direction"], "negative")
        self.assertIsNone(report["all_primary_hypotheses_supported"])
        self.assertFalse(report["confirmatory_inference_available"])
        self.assertEqual(poolact["n_pairs"], 6)
        self.assertEqual(poolact["n_items"], 3)
        self.assertEqual(report["primary_families"], {"all_primary_endpoints": 2})
        self.assertAlmostEqual(poolact["family_adjusted_nominal_level"], 0.975)

    def test_item_cluster_is_invariant_to_duplicating_repeats(self):
        first = study.bootstrap_differences([[0, 2], [4, 6], [-2, 0]], "item_cluster", 1000, 42)
        duplicated = study.bootstrap_differences([[0, 2] * 20, [4, 6] * 20, [-2, 0] * 20], "item_cluster", 1000, 42)
        self.assertEqual(first, duplicated)

    def test_fixed_items_resamples_seed_blocks_not_item_times_seed_cells(self):
        # Perfectly offset items cancel within every seed block. Independent
        # within-item seed resampling would invent variance for this estimand.
        values = [[-1, 1], [1, -1]]
        draws = study.bootstrap_differences(values, "fixed_items_outer_repeats", 1000, 7)
        self.assertEqual(set(draws), {0.0})
        self.assertGreater(len(set(study.bootstrap_differences(values, "nested", 1000, 7))), 1)

    def test_bootstrap_deterministic_and_order_invariant(self):
        original = self.analyze()
        self.rows.reverse()
        for comparison in self.manifest["comparisons"]:
            comparison["items"].reverse()
            comparison["outerseeds"].reverse()
        self.save()
        changed = self.analyze()
        for old, new in zip(original["comparisons"], changed["comparisons"]):
            self.assertEqual(old["nominal_ci"], new["nominal_ci"])
            self.assertEqual(old["pairs"], new["pairs"])

    def test_missing_row_is_error_not_complete_case_analysis(self):
        self.rows.pop()
        self.save()
        with self.assertRaisesRegex(study.StudyError, "missing registered CSV rows"):
            self.analyze()

    def test_unregistered_and_duplicate_rows_rejected(self):
        self.rows.append(dict(self.rows[0]))
        self.save()
        with self.assertRaisesRegex(study.StudyError, "duplicate CSV row"):
            self.analyze()
        self.rows[-1]["item"] = "posthoc-easier-item"
        self.save()
        with self.assertRaisesRegex(study.StudyError, "unregistered CSV row"):
            self.analyze()

    def test_unpaired_comparison_rejected_even_when_export_complete(self):
        self.manifest["comparisons"][0]["outerseeds"].append("42")
        self.save()
        with self.assertRaisesRegex(study.StudyError, "unpaired registered comparison"):
            self.analyze()

    def test_agent_unit_and_duplicate_identity_rejected(self):
        artifact = next(row for row in self.manifest["artifacts"] if row["system"] == "poolact")
        artifact["unit"] = "individual_agent"
        self.save()
        with self.assertRaisesRegex(study.StudyError, "individual agents are not study units"):
            self.analyze()
        artifact["unit"] = "pool_aggregate"
        duplicate = dict(artifact, artifact="different-file-same-unit.json")
        self.manifest["artifacts"].append(duplicate)
        self.save()
        with self.assertRaisesRegex(study.StudyError, "duplicate artifact identity"):
            self.analyze()

    def test_frozen_hash_and_bound_receipt_detect_changes(self):
        with self.assertRaisesRegex(study.StudyError, "frozen manifest SHA256 mismatch"):
            study.analyze(self.manifest_path, self.csv_path, "0" * 64)
        self.rows[0]["value"] = 0.55
        self.save(receipt=False)
        with self.assertRaisesRegex(study.StudyError, "receipt CSV hash mismatch"):
            self.analyze()

    def test_artifact_changed_after_audit_rejected(self):
        artifact = self.root / self.manifest["artifacts"][0]["artifact"]
        artifact.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(study.StudyError, "artifact set/hash mismatch"):
            self.analyze()

    def test_artifact_missing_rejected_without_receipt(self):
        artifact = self.root / self.manifest["artifacts"][0]["artifact"]
        artifact.unlink()
        with self.assertRaisesRegex(study.StudyError, "missing declared artifact"):
            self.analyze(receipt=False)

    def test_nonfinite_out_of_range_and_metric_scale(self):
        for value in ("nan", "inf", "-inf", "not-a-number", 1.01):
            with self.subTest(value=value):
                self.rows[0]["value"] = value
                self.save()
                with self.assertRaises(study.StudyError):
                    self.analyze()

    def test_semantic_zero_not_dropped(self):
        self.rows[0]["value"] = 0.0
        self.save()
        report = self.analyze()
        self.assertEqual(report["n_rows"], len(self.rows))
        self.assertTrue(any(pair["baseline"] == 0 for pair in report["comparisons"][0]["pairs"]))

    def test_no_receipt_blocks_claim_not_descriptive_reporting(self):
        report = self.analyze(receipt=False)
        self.assertTrue(report["input_complete"])
        self.assertEqual(report["comparisons"][0]["status"], "not_confirmatory")
        self.assertIn("missing_or_failed_bound_recomputation_declaration", report["comparisons"][0]["confirmatory_blockers"])

    def test_failed_quality_gate_keeps_effect_and_blocks_claim(self):
        for row in self.rows:
            if row["system"] == "poolact" and row["metric"] == "protocol_ok":
                row["value"] = 0.5
        self.save()
        report = self.analyze()
        poolact = report["comparisons"][1]
        self.assertAlmostEqual(poolact["effect"], -0.1)
        self.assertEqual(poolact["status"], "not_confirmatory")
        self.assertIn("quality_gate_failed:poolact_protocol", poolact["confirmatory_blockers"])

    def test_wrong_model_quality_gate_not_accepted(self):
        self.manifest["quality_gates"][0]["selectors"]["model"] = "another-model"
        self.save()
        with self.assertRaisesRegex(study.StudyError, "different model/system/scenario/split"):
            self.analyze()

    def test_cross_split_item_reuse_rejected(self):
        self.manifest["artifacts"][0]["split"] = "development"
        self.save()
        with self.assertRaisesRegex(study.StudyError, "held-out contamination"):
            self.analyze()

    def test_secondary_does_not_expand_primary_family_or_claim_support(self):
        secondary = copy.deepcopy(self.manifest["comparisons"][0])
        secondary.update(id="secondary", role="secondary")
        self.manifest["comparisons"].append(secondary)
        self.save()
        report = self.analyze()
        self.assertEqual(report["primary_families"]["all_primary_endpoints"], 2)
        self.assertEqual(report["comparisons"][2]["status"], "exploratory_secondary")
        self.assertEqual(report["comparisons"][2]["family_adjusted_nominal_level"], 0.95)

    def test_low_monte_carlo_tail_resolution_and_sample_floor_block_claim(self):
        self.manifest["bootstrap"]["samples"] = 100
        self.manifest["comparisons"][0]["minimum_items"] = 10
        self.save()
        blockers = self.analyze()["comparisons"][0]["confirmatory_blockers"]
        self.assertIn("below_preregistered_minimum_items", blockers)
        self.assertIn("fewer_than_20_expected_bootstrap_draws_per_decision_tail", blockers)

    def test_single_outer_repeat_fixed_items_not_confirmatory(self):
        comparison = self.manifest["comparisons"][0]
        comparison.update(bootstrap_method="fixed_items_outer_repeats", outerseeds=["40"], minimum_outerseeds=1)
        self.save()
        result = self.analyze()["comparisons"][0]
        self.assertIn("outer_repeat_resampling_requires_at_least_two_repeats", result["confirmatory_blockers"])

    def test_lower_is_better_direction(self):
        self.manifest["metrics"]["f1"]["higher_is_better"] = False
        self.save()
        report = self.analyze()
        self.assertAlmostEqual(report["comparisons"][0]["effect"], -0.2)
        self.assertAlmostEqual(report["comparisons"][1]["effect"], 0.1)

    def test_equal_item_weight_not_repeat_count_weight(self):
        rows = [dict(model="m", system="expgym", scenario="s", regime="r", strategy="single", metric="x",
                     split="heldout", item="a", outerseed=str(i), value=0.0) for i in range(10)]
        rows += [dict(rows[0], item="b", outerseed="0", value=1.0)]
        result = study.aggregate_rows(rows)[0]
        self.assertEqual(result["mean"], 0.5)
        self.assertEqual(result["n_items"], 2)
        self.assertEqual(result["n_rows"], 11)

    def test_duplicate_json_key_rejected(self):
        self.manifest_path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        self.manifest_hash = study.sha256_file(self.manifest_path)
        with self.assertRaisesRegex(study.StudyError, "duplicate JSON key"):
            self.analyze()

    def test_output_tables_and_no_overwrite(self):
        report = self.analyze()
        output = self.root / "report"
        study.write_report(report, output)
        self.assertEqual({path.name for path in output.iterdir()}, {
            "report.json", "REPORT.md", "effects.csv", "paired_rows.csv", "paired_items.csv",
            "aggregate_metrics.csv", "by_outerseed.csv"})
        saved = json.loads((output / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["n_artifacts"], 24)
        self.assertIn("negative", (output / "effects.csv").read_text(encoding="utf-8"))
        self.assertIn("descriptive only", (output / "REPORT.md").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(study.StudyError, "already exists"):
            study.write_report(report, output)

    def test_cli_exit_zero_for_valid_negative_results(self):
        output = self.root / "cli-report"
        command = [sys.executable, str(SCRIPT), "--manifest", str(self.manifest_path), "--manifest-sha256",
                   self.manifest_hash, "--csv", str(self.csv_path), "--audit-receipt", str(self.receipt_path),
                   "--output-dir", str(output)]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIsNone(json.loads(completed.stdout)["all_primary_hypotheses_supported"])
        repeated = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(repeated.returncode, 2)

    def test_r09_all_eight_small_n_null_patterns_cannot_confirm(self):
        spec = copy.deepcopy(self.manifest["comparisons"][0])
        self.manifest["bootstrap"]["samples"] = 1000
        naive_false_positives = 0
        for signs in itertools.product((-1, 1), repeat=3):
            rows = copy.deepcopy(self.rows)
            for row in rows:
                row["split"] = "heldout"
                if row["system"] == "expgym" and row["metric"] == "f1":
                    sign = signs[int(row["item"][1:])]
                    row["value"] = float((sign == 1) == (row["regime"] == "cost_free"))
            result = study.compare(rows, spec, self.manifest, 1,
                                  {"receipt_declares_complete_recomputed_scores": True},
                                  {"expgym_protocol": {"passed": True}})
            naive_false_positives += result["nominal_ci"][0] > 0
            self.assertEqual(result["status"], "not_confirmatory")
            self.assertIn(study.NO_CONFIRMATORY_METHOD, result["confirmatory_blockers"])
            self.assertFalse(result["confirmatory_inference_available"])
        # At least the all-positive sample (probability 1/8 under this null)
        # defeats a purported 95% directional decision from bootstrap percentiles.
        self.assertGreaterEqual(naive_false_positives / 8, 0.125)

    def test_r09_all_bootstrap_methods_remain_descriptive_at_large_n(self):
        spec = copy.deepcopy(self.manifest["comparisons"][0])
        spec.update(items=["q" + str(i) for i in range(100)], outerseeds=["0", "1", "2", "3", "4"],
                    minimum_items=100, minimum_outerseeds=5)
        rows = []
        for item in spec["items"]:
            for seed in spec["outerseeds"]:
                for regime, value in (("cost_free", 0.9), ("cost_tight", 0.5)):
                    rows.append(dict(model=spec["model"], system="expgym", scenario=spec["scenario"], item=item,
                                     outerseed=seed, regime=regime, strategy="single", split="heldout", metric="f1",
                                     value=value, artifact=f"synthetic/{item}/{seed}/{regime}"))
        self.manifest["bootstrap"]["samples"] = 1000
        for method in study.METHODS:
            with self.subTest(method=method):
                spec["bootstrap_method"] = method
                result = study.compare(rows, spec, self.manifest, 1,
                                      {"receipt_declares_complete_recomputed_scores": True},
                                      {"expgym_protocol": {"passed": True}})
                self.assertEqual(result["status"], "not_confirmatory")
                self.assertIn(study.NO_CONFIRMATORY_METHOD, result["confirmatory_blockers"])
                self.assertTrue(result["observed_effect_exceeds_registered_minimum"])
                self.assertEqual(result["nominal_ci"][0], result["nominal_ci"][1])

    def test_r09_more_resampling_and_family_adjustment_never_unlock_confirmation(self):
        first = self.analyze()["comparisons"][0]
        self.manifest["bootstrap"]["samples"] = 12000
        self.save()
        second = self.analyze()["comparisons"][0]
        self.assertEqual(first["status"], second["status"])
        self.assertEqual(second["status"], "not_confirmatory")
        self.assertEqual(second["family_adjusted_descriptive_ci"][0], second["family_adjusted_descriptive_ci"][1])

    def test_scope_required_and_no_corpus_population_claim(self):
        del self.manifest["comparisons"][0]["scope"]
        self.save()
        with self.assertRaisesRegex(study.StudyError, "scope must explicitly"):
            self.analyze()
        self.manifest["comparisons"][0]["scope"] = copy.deepcopy(self.manifest["comparisons"][1]["scope"])
        self.manifest["comparisons"][0]["scope"]["inference_population"] = "all_corpora"
        self.save()
        with self.assertRaisesRegex(study.StudyError, "unseen-task or unseen-corpus"):
            self.analyze()

    def test_known_tasks_and_seed_labels_have_explicit_limits(self):
        self.manifest["comparisons"][0]["scope"]["item_status"] = "previously_inspected"
        self.save()
        result = self.analyze()["comparisons"][0]
        self.assertTrue(any("known or possibly inspected" in warning for warning in result["warnings"]))
        self.assertTrue(any("seed control" in warning for warning in result["warnings"]))
        self.assertIn("no item/corpus-population inference", result["inference_target"])

    def test_receipt_is_declaration_not_recomputed_score_truth(self):
        report = self.analyze()
        self.assertTrue(report["integrity"]["receipt_bound"])
        self.assertTrue(report["integrity"]["receipt_declares_complete_recomputed_scores"])
        self.assertFalse(report["integrity"]["scores_recomputed_by_analyzer"])
        self.assertIn("not independent score truth", report["integrity"]["note"])
        self.assertFalse(report["confirmatory_inference_available"])

    def test_distinct_hardlink_paths_cannot_duplicate_study_units(self):
        first, second = self.manifest["artifacts"][:2]
        alias = "artifacts/hardlink-alias.json"
        os.link(self.root / first["artifact"], self.root / alias)
        previous = second["artifact"]
        second["artifact"] = alias
        for row in self.rows:
            if row["artifact"] == previous:
                row["artifact"] = alias
        self.save()
        with self.assertRaisesRegex(study.StudyError, "hardlink aliases"):
            self.analyze()

    def test_csv_parsing_uses_hashed_snapshot_and_change_is_detected(self):
        load_rows = study.load_rows
        observed = []

        def change_before_parse(path, manifest, artifacts, payload=None):
            self.csv_path.write_bytes(self.csv_path.read_bytes().replace(b",0.8,", b",0.9,"))
            rows = load_rows(path, manifest, artifacts, payload)
            observed.extend(row["value"] for row in rows if row["system"] == "expgym"
                            and row["regime"] == "cost_free" and row["metric"] == "f1")
            return rows

        with mock.patch.object(study, "load_rows", side_effect=change_before_parse):
            with self.assertRaisesRegex(study.StudyError, "CSV changed during analysis"):
                self.analyze()
        self.assertEqual(set(observed), {0.8})

    def test_manifest_parsing_uses_hashed_snapshot_and_change_is_detected(self):
        read_json = study.read_json
        observed = []

        def change_before_parse(path, payload=None):
            if path == self.manifest_path:
                replacement = dict(self.manifest, study_id="unregistered-replacement")
                self.manifest_path.write_text(json.dumps(replacement), encoding="utf-8")
                value = read_json(path, payload)
                observed.append(value["study_id"])
                return value
            return read_json(path, payload)

        with mock.patch.object(study, "read_json", side_effect=change_before_parse):
            with self.assertRaisesRegex(study.StudyError, "manifest changed during analysis"):
                self.analyze()
        self.assertEqual(observed, [self.manifest["study_id"]])

    def test_receipt_parsing_uses_hashed_snapshot_and_change_is_detected(self):
        read_json = study.read_json
        observed = []

        def change_before_parse(path, payload=None):
            if path == self.receipt_path:
                receipt = read_json(path)
                receipt["score_recomputation_passed"] = False
                self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
                value = read_json(path, payload)
                observed.append(value["score_recomputation_passed"])
                return value
            return read_json(path, payload)

        with mock.patch.object(study, "read_json", side_effect=change_before_parse):
            with self.assertRaisesRegex(study.StudyError, "artifacts or receipt changed during analysis"):
                self.analyze()
        self.assertEqual(observed, [True, False])

    def test_end_guard_detects_artifact_change_without_receipt(self):
        compare = study.compare
        artifact = self.root / self.manifest["artifacts"][0]["artifact"]

        def change_during_comparison(*args, **kwargs):
            artifact.write_text('{"mutated":true}', encoding="utf-8")
            return compare(*args, **kwargs)

        with mock.patch.object(study, "compare", side_effect=change_during_comparison):
            with self.assertRaisesRegex(study.StudyError, "artifacts or receipt changed during analysis"):
                self.analyze(receipt=False)


if __name__ == "__main__":
    unittest.main()
