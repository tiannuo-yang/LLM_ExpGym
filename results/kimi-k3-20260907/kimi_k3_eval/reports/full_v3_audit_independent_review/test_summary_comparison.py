#!/usr/bin/env python3
"""Synthetic summary-comparison checks: no results, official code, or APIs read.

Every call replaces compute.read and compute.ref with memory-only mocks.  These
tests check the comparator's declared coverage, not the independent scorer or
whether a producer's supplied SHA is an actual file digest.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compute


SUMMARY_PATH = Path("/memory-fixtures/audit-summary.json")
COUNTS = {"aggregate": 42, "document": 546, "agent": 585,
          "poolact_result": 117, "paper_subset": 24}
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STRATEGIES = ("naive", "cached", "poolact")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


SUMMARY_REF = {"path": str(SUMMARY_PATH), "sha256": digest("synthetic summary"),
               "bytes": 123456}


def make_fixture():
    """Build every comparison cell independently of compute.build_metrics."""
    report = {"manifest": {"sha256": digest("synthetic manifest")},
              "metrics": {"aggregate_metrics": [], "document_metrics": []},
              "traces": [], "poolact_results": []}
    summary = {"complete": True, "manifest_sha256": report["manifest"]["sha256"],
               "aggregate_metrics": [], "task_metrics": [], "agents": [],
               "artifacts": []}

    def official_metric(local, subset="full"):
        official = {"subset": subset, "scenario": "evidence_audit",
                    "system": local["system"], "cost_regime": local["regime"],
                    "strategy": local["strategy"], "metric": local["metric"],
                    "value": local["value"], "complete": True}
        if "item_index" in local:
            official["item_id"] = str(local["item_index"])
        return official

    for regime_index, regime in enumerate(REGIMES):
        systems = [("expgym", None, ("LA_pct", "EA_pct"))]
        systems += [("poolact", strategy,
                     ("LA_pct", "EA_pct", "MI_LA_pct", "MI_EA_pct"))
                    for strategy in STRATEGIES]
        for system_index, (system, strategy, metrics) in enumerate(systems):
            for metric_index, metric in enumerate(metrics):
                values = []
                for index in range(13):
                    value = 10 * regime_index + 5 * system_index + metric_index + index / 16
                    values.append(value)
                    row = {"system": system, "regime": regime, "strategy": strategy,
                           "metric": metric, "item_index": index, "value": value}
                    report["metrics"]["document_metrics"].append(row)
                    summary["task_metrics"].append(official_metric(row))
                row = {"system": system, "regime": regime, "strategy": strategy,
                       "metric": metric, "value": sum(values) / 13, "documents": 13}
                report["metrics"]["aggregate_metrics"].append(row)
                summary["aggregate_metrics"].append(official_metric(row))
                if system == "poolact" and regime != "cost_free":
                    summary["aggregate_metrics"].append(official_metric(row, "paper_poolact"))

    def add_record(local_key, official_key, path, sequence, **identity):
        row = {"path": path, "sha256": digest(path),
               "label_acc": sequence % 18 / 17,
               "evidence_acc": (sequence * 7 + 3) % 18 / 17, **identity}
        report[local_key].append(row)
        summary[official_key].append({**row, "status": "valid"})

    for index in range(13):
        for regime in REGIMES:
            for repetition in range(3):
                add_record("traces", "agents",
                           f"/memory-fixtures/expgym/{index}/{regime}/trace-{repetition}.json",
                           len(report["traces"]), system="expgym", item_index=index,
                           regime=regime, strategy=None, repetition=repetition)
            for strategy in STRATEGIES:
                prefix = f"/memory-fixtures/poolact/{index}/{regime}/{strategy}"
                for agent_id in range(4):
                    add_record("traces", "agents", f"{prefix}/agent-{agent_id}.json",
                               len(report["traces"]), system="poolact", item_index=index,
                               regime=regime, strategy=strategy, agent_id=agent_id)
                add_record("poolact_results", "artifacts", f"{prefix}/result.json",
                           len(report["poolact_results"]), system="poolact", item_index=index,
                           regime=regime, strategy=strategy)
    return report, summary


def comparison_rows(summary, kind):
    if kind == "aggregate":
        return [row for row in summary["aggregate_metrics"] if row["subset"] == "full"]
    if kind == "paper_subset":
        return [row for row in summary["aggregate_metrics"] if row["subset"] == "paper_poolact"]
    return summary[{"document": "task_metrics", "agent": "agents",
                    "poolact_result": "artifacts"}[kind]]


class SummaryComparisonTests(unittest.TestCase):
    def setUp(self):
        self.report, self.summary = make_fixture()

    def compare(self, report=None, summary=None):
        report = self.report if report is None else report
        summary = self.summary if summary is None else summary
        with patch.object(compute, "read", return_value=summary) as read_mock, \
                patch.object(compute, "ref", return_value=copy.deepcopy(SUMMARY_REF)) as ref_mock:
            result = compute.compare_summary(report, SUMMARY_PATH)
            read_mock.assert_called_once_with(SUMMARY_PATH)
            ref_mock.assert_called_once_with(SUMMARY_PATH)
        return result

    def reject(self, report=None, summary=None, exception=ValueError, message=None):
        report = self.report if report is None else report
        summary = self.summary if summary is None else summary
        with patch.object(compute, "read", return_value=summary) as read_mock, \
                patch.object(compute, "ref", return_value=copy.deepcopy(SUMMARY_REF)) as ref_mock:
            if message is None:
                with self.assertRaises(exception):
                    compute.compare_summary(report, SUMMARY_PATH)
            else:
                with self.assertRaisesRegex(exception, message):
                    compute.compare_summary(report, SUMMARY_PATH)
            read_mock.assert_called_once_with(SUMMARY_PATH)
            ref_mock.assert_not_called()

    def test_complete_fixture_has_all_1314_comparisons_and_zero_differences(self):
        result = self.compare()
        self.assertIs(result["complete"], True)
        self.assertEqual(result["counts"], COUNTS)
        self.assertEqual(sum(result["counts"].values()), 1314)
        for key, value in SUMMARY_REF.items():
            self.assertEqual(result[key], value)
        for kind, rows in result["comparisons"].items():
            self.assertEqual(len(rows), COUNTS[kind])
            for row in rows:
                for key in ("difference", "LA_difference", "EA_difference"):
                    if key in row:
                        self.assertEqual(row[key], 0)
        json.dumps(result, allow_nan=False)

    def test_fixture_represents_each_expected_identity_once(self):
        traces = self.report["traces"]
        self.assertEqual(sum(row["system"] == "expgym" for row in traces), 117)
        self.assertEqual(sum(row["system"] == "poolact" for row in traces), 468)
        self.assertEqual(len({row["path"] for row in traces}), 585)
        self.assertEqual(len({row["path"] for row in self.report["poolact_results"]}), 117)
        for kind in COUNTS:
            self.assertEqual(len(comparison_rows(self.summary, kind)), COUNTS[kind])

    def test_strict_json_round_trip_preserves_fixture_and_result(self):
        report = json.loads(json.dumps(self.report, allow_nan=False))
        summary = json.loads(json.dumps(self.summary, allow_nan=False))
        result = self.compare(report, summary)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_summary_order_is_not_identity(self):
        for key in ("aggregate_metrics", "task_metrics", "agents", "artifacts"):
            self.summary[key].reverse()
        self.assertEqual(self.compare()["counts"], COUNTS)

    def test_expgym_official_strategy_may_be_absent(self):
        for key in ("aggregate_metrics", "task_metrics"):
            for row in self.summary[key]:
                if row["system"] == "expgym":
                    del row["strategy"]
        self.assertEqual(self.compare()["counts"], COUNTS)

    def test_each_aggregate_metric_kind_single_value_tamper(self):
        for system, metric in (("expgym", "LA_pct"), ("expgym", "EA_pct"),
                               ("poolact", "LA_pct"), ("poolact", "EA_pct"),
                               ("poolact", "MI_LA_pct"), ("poolact", "MI_EA_pct")):
            with self.subTest(system=system, metric=metric):
                summary = copy.deepcopy(self.summary)
                row = next(row for row in comparison_rows(summary, "aggregate")
                           if row["system"] == system and row["metric"] == metric)
                row["value"] += 1e-6
                self.reject(summary=summary, message="summary aggregate")

    def test_document_and_paper_single_value_tamper(self):
        for kind, message in (("document", "summary document"),
                              ("paper_subset", "paper Audit metric")):
            for metric in ("LA_pct", "EA_pct", "MI_LA_pct", "MI_EA_pct"):
                with self.subTest(kind=kind, metric=metric):
                    summary = copy.deepcopy(self.summary)
                    row = next(row for row in comparison_rows(summary, kind)
                               if row["system"] == "poolact" and row["metric"] == metric)
                    row["value"] += 1e-6
                    self.reject(summary=summary, message=message)

    def test_agent_and_result_single_accuracy_tamper(self):
        for kind in ("agent", "poolact_result"):
            for field, message in (("label_acc", "summary LA"), ("evidence_acc", "summary EA")):
                with self.subTest(kind=kind, field=field):
                    summary = copy.deepcopy(self.summary)
                    comparison_rows(summary, kind)[-1][field] += 1e-6
                    self.reject(summary=summary, message=message)

    def test_agent_and_result_sha_tamper(self):
        for kind in ("agent", "poolact_result"):
            with self.subTest(kind=kind):
                summary = copy.deepcopy(self.summary)
                comparison_rows(summary, kind)[-1]["sha256"] = digest("tampered raw")
                self.reject(summary=summary, message="summary raw integrity mismatch")

    def test_manifest_sha_tamper(self):
        self.summary["manifest_sha256"] = digest("different manifest")
        self.reject(message="summary incomplete or manifest mismatch")

    def test_summary_complete_is_strict_boolean_true(self):
        for value in (False, None, 0, 1, "true"):
            with self.subTest(value=value):
                summary = copy.deepcopy(self.summary)
                summary["complete"] = value
                self.reject(summary=summary, message="summary incomplete or manifest mismatch")

    def test_every_metric_group_complete_is_strict_boolean_true(self):
        for kind in ("aggregate", "document", "paper_subset"):
            for value in (False, None, 1, "true"):
                with self.subTest(kind=kind, value=value):
                    summary = copy.deepcopy(self.summary)
                    comparison_rows(summary, kind)[0]["complete"] = value
                    self.reject(summary=summary, message="summary metric|paper Audit metric")

    def test_agent_and_result_invalid_status(self):
        for kind in ("agent", "poolact_result"):
            for status in ("incomplete", "invalid", "VALID", None):
                with self.subTest(kind=kind, status=status):
                    summary = copy.deepcopy(self.summary)
                    comparison_rows(summary, kind)[0]["status"] = status
                    self.reject(summary=summary, message="summary raw integrity mismatch")

    def test_nonfinite_boolean_string_and_null_metrics_rejected(self):
        for kind in COUNTS:
            field = "label_acc" if kind in ("agent", "poolact_result") else "value"
            for value in (True, False, "0", None, float("nan"), float("inf"), -float("inf")):
                with self.subTest(kind=kind, value=repr(value)):
                    summary = copy.deepcopy(self.summary)
                    comparison_rows(summary, kind)[0][field] = value
                    self.reject(summary=summary)

    def test_absolute_tolerance_boundary(self):
        # First document has exactly zero as its baseline: no subtraction rounding.
        self.assertEqual(self.report["metrics"]["document_metrics"][0]["value"], 0)
        self.summary["task_metrics"][0]["value"] = 1e-10
        result = self.compare()
        self.assertEqual(result["comparisons"]["document"][0]["difference"], 1e-10)
        self.summary["task_metrics"][0]["value"] = 1.0001e-10
        self.reject(message="summary document")

    def test_missing_or_duplicate_official_metric(self):
        for kind, key in (("aggregate", "aggregate_metrics"), ("document", "task_metrics"),
                          ("paper_subset", "aggregate_metrics")):
            for operation in ("missing", "duplicate"):
                with self.subTest(kind=kind, operation=operation):
                    summary = copy.deepcopy(self.summary)
                    row = comparison_rows(summary, kind)[0]
                    if operation == "missing":
                        summary[key].remove(row)
                    else:
                        summary[key].append(copy.deepcopy(row))
                    self.reject(summary=summary, message="summary metric|paper Audit metric")

    def test_duplicate_official_raw_path(self):
        for key in ("agents", "artifacts"):
            with self.subTest(key=key):
                summary = copy.deepcopy(self.summary)
                summary[key].append(copy.deepcopy(summary[key][0]))
                self.reject(summary=summary, message="duplicate summary paths")

    def test_missing_official_raw_path(self):
        for key in ("agents", "artifacts"):
            with self.subTest(key=key):
                summary = copy.deepcopy(self.summary)
                summary[key].pop()
                self.reject(summary=summary, exception=KeyError)

    def test_metric_identity_tamper(self):
        for kind in ("aggregate", "document", "paper_subset"):
            for field in ("subset", "scenario", "system", "cost_regime", "strategy", "metric"):
                with self.subTest(kind=kind, field=field):
                    summary = copy.deepcopy(self.summary)
                    comparison_rows(summary, kind)[0][field] = "not-the-required-identity"
                    self.reject(summary=summary, message="summary metric|paper Audit metric")

    def test_document_item_id_requires_matching_string(self):
        for value in (0, "00", "another-document", None):
            with self.subTest(value=value):
                summary = copy.deepcopy(self.summary)
                summary["task_metrics"][0]["item_id"] = value
                self.reject(summary=summary, message="summary metric")

    def test_local_row_count_shortfall_or_excess(self):
        for key in ("aggregate_metrics", "document_metrics", "traces", "poolact_results"):
            for operation in ("missing", "extra"):
                with self.subTest(key=key, operation=operation):
                    report = copy.deepcopy(self.report)
                    rows = report["metrics"][key] if key.endswith("metrics") else report[key]
                    if operation == "missing":
                        rows.pop(0)
                    else:
                        rows.append(copy.deepcopy(rows[0]))
                    self.reject(report=report, message="comparison count mismatch")

    def test_missing_required_summary_collections_or_manifest(self):
        for key in ("complete", "manifest_sha256", "aggregate_metrics", "task_metrics", "agents", "artifacts"):
            with self.subTest(key=key):
                summary = copy.deepcopy(self.summary)
                del summary[key]
                self.reject(summary=summary, exception=KeyError)

    def test_missing_required_metric_and_raw_fields(self):
        for kind in COUNTS:
            fields = (("path", "sha256", "status", "label_acc", "evidence_acc")
                      if kind in ("agent", "poolact_result") else ("complete", "value"))
            for field in fields:
                with self.subTest(kind=kind, field=field):
                    summary = copy.deepcopy(self.summary)
                    del comparison_rows(summary, kind)[0][field]
                    self.reject(summary=summary, exception=KeyError)

    def test_invalid_json_read_error_is_not_converted_to_complete(self):
        failure = json.JSONDecodeError("synthetic malformed envelope", "{", 1)
        with patch.object(compute, "read", side_effect=failure) as read_mock, \
                patch.object(compute, "ref") as ref_mock:
            with self.assertRaises(json.JSONDecodeError):
                compute.compare_summary(self.report, SUMMARY_PATH)
            read_mock.assert_called_once_with(SUMMARY_PATH)
            ref_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
