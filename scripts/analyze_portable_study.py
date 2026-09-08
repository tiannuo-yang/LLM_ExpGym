#!/usr/bin/env python3
"""Describe an explicitly registered, model-independent paired benchmark study.

This script never runs a model, discovers result files recursively, repairs a
score, or selects items using their outcomes. Bootstrap intervals are descriptive
only: no implemented method can confirm or reject a hypothesis. See
docs/portable-study.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


IDENTITY = ("model", "system", "scenario", "item", "regime", "strategy", "outerseed")
CSV_FIELDS = IDENTITY + ("metric", "value", "artifact")
GROUP_FIELDS = ("model", "system", "scenario", "regime", "strategy", "metric", "split")
METHODS = ("item_cluster", "nested", "fixed_items_outer_repeats")
NO_CONFIRMATORY_METHOD = "bootstrap_is_descriptive_no_validated_confirmatory_method"


class StudyError(ValueError):
    """Invalid or incomplete evidence; never substitute a zero score."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StudyError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _unique_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path: Path, payload: Optional[bytes] = None) -> Dict[str, Any]:
    value = json.loads(path.read_bytes() if payload is None else payload,
                       object_pairs_hook=_unique_object)
    require(isinstance(value, dict), "JSON root must be an object: " + str(path))
    return value


def _string(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), label + " must be a nonempty string")
    return value


def _number(value: Any, label: str) -> float:
    require(not isinstance(value, bool), label + " must be numeric, not bool")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise StudyError(label + " must be numeric") from exc
    require(math.isfinite(number), label + " must be finite")
    return number


def _integer(value: Any, label: str, minimum: int) -> int:
    require(type(value) is int and value >= minimum, label + " must be an integer >= " + str(minimum))
    return value


def _strings(value: Any, label: str) -> List[str]:
    require(isinstance(value, list) and bool(value), label + " must be a nonempty list")
    values = [_string(x, label) for x in value]
    require(len(set(values)) == len(values), label + " contains duplicates")
    return values


def validate_manifest(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    require(type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1,
            "expected integer manifest schema_version=1")
    _string(manifest.get("study_id"), "study_id")
    registration = manifest.get("registration", {})
    require(isinstance(registration, dict), "registration must be an object")
    require(registration.get("selection_rule") == "fixed_manifest_no_outcome_selection",
            "registration.selection_rule must prohibit outcome-based selection")
    require(type(registration.get("frozen_before_evaluation")) is bool,
            "declare registration.frozen_before_evaluation (a declaration, not independently verified)")
    _string(registration.get("protocol_id"), "registration.protocol_id")
    config = manifest.get("bootstrap", {})
    require(isinstance(config, dict), "bootstrap must be an object")
    _integer(config.get("samples"), "bootstrap.samples", 100)
    _integer(config.get("seed"), "bootstrap.seed", 0)
    confidence = _number(config.get("confidence"), "bootstrap.confidence")
    require(0 < confidence < 1, "bootstrap.confidence must be between 0 and 1")
    config["confidence"] = confidence
    metrics = manifest.get("metrics")
    require(isinstance(metrics, dict) and bool(metrics), "metrics must be a nonempty object")
    for name, spec in metrics.items():
        _string(name, "metric name")
        require(isinstance(spec, dict), "metric definition must be an object")
        _string(spec.get("unit"), name + ".unit")
        require(type(spec.get("higher_is_better")) is bool, name + ".higher_is_better must be bool")
        for bound in ("minimum", "maximum"):
            if spec.get(bound) is not None:
                spec[bound] = _number(spec[bound], name + "." + bound)
        if spec.get("minimum") is not None and spec.get("maximum") is not None:
            require(spec["minimum"] <= spec["maximum"], name + " has reversed bounds")
    artifacts = manifest.get("artifacts")
    require(isinstance(artifacts, list) and bool(artifacts), "artifacts must be a nonempty explicit list")
    by_path: Dict[str, Dict[str, Any]] = {}
    identities = set()
    item_splits: Dict[Tuple[str, str], str] = {}
    for artifact in artifacts:
        require(isinstance(artifact, dict), "artifact entry must be an object")
        path = _string(artifact.get("artifact"), "artifact path")
        key = tuple(_string(artifact.get(field), "artifact." + field) for field in IDENTITY)
        require(path not in by_path, "duplicate artifact path: " + path)
        require(key not in identities, "duplicate artifact identity: " + repr(key))
        identities.add(key)
        system = artifact["system"]
        require(system in ("expgym", "poolact"), "system must be expgym or poolact")
        unit = "single_trace" if system == "expgym" else "pool_aggregate"
        require(artifact.get("unit") == unit, "expected " + unit + "; individual agents are not study units")
        split = _string(artifact.get("split"), "artifact.split")
        split_key = (artifact["scenario"], artifact["item"])
        require(split_key not in item_splits or item_splits[split_key] == split,
                "same item occurs in different splits (held-out contamination): " + repr(split_key))
        item_splits[split_key] = split
        for metric in _strings(artifact.get("metrics"), "artifact.metrics"):
            require(metric in metrics, "unknown metric: " + metric)
        by_path[path] = artifact
    gates = manifest.get("quality_gates")
    require(isinstance(gates, list), "quality_gates must be an explicit list (possibly empty)")
    gate_ids = set()
    for gate in gates:
        require(isinstance(gate, dict), "quality gate must be an object")
        gate_id = _string(gate.get("id"), "quality gate id")
        require(gate_id not in gate_ids, "duplicate quality gate id: " + gate_id)
        gate_ids.add(gate_id)
        require(gate.get("metric") in metrics, "unknown quality gate metric")
        require(gate.get("operator") in ("<=", ">="), "quality gate operator must be <= or >=")
        gate["threshold"] = _number(gate.get("threshold"), "quality gate threshold")
        selectors = gate.get("selectors")
        require(isinstance(selectors, dict) and bool(selectors), "quality gate selectors must be explicit")
        require(all(field in selectors for field in ("model", "system", "scenario", "split")),
                "quality gates must bind model, system, scenario, and split; do not hide one model's failures in another")
        for field, value in selectors.items():
            require(field in IDENTITY + ("split",), "unknown quality gate selector: " + field)
            _string(value, "quality gate selector")
    comparisons = manifest.get("comparisons")
    require(isinstance(comparisons, list) and bool(comparisons), "comparisons must be a nonempty list")
    comparison_ids = set()
    for comparison in comparisons:
        require(isinstance(comparison, dict), "comparison must be an object")
        name = _string(comparison.get("id"), "comparison.id")
        require(name not in comparison_ids, "duplicate comparison id: " + name)
        comparison_ids.add(name)
        require(comparison.get("kind") in ("expgym_free_tight", "poolact_vs_naive"), "unknown comparison kind")
        for field in ("model", "scenario", "split", "family"):
            _string(comparison.get(field), name + "." + field)
        scope = comparison.get("scope")
        require(isinstance(scope, dict), name + ".scope must explicitly delimit descriptive scope")
        _strings(scope.get("data_snapshots"), name + ".scope.data_snapshots")
        require(scope.get("item_status") in ("previously_inspected", "prospectively_reserved", "mixed_or_unknown"),
                name + ".scope.item_status must describe actual exposure, not merely a split label")
        require(scope.get("inference_population") == "registered_items_only",
                "bootstrap analysis cannot establish unseen-task or unseen-corpus generalization")
        require(scope.get("outer_repetition_interpretation") in
                ("seed_labels_only", "verified_generation_repeats", "fixed_orders"),
                name + ".scope.outer_repetition_interpretation must be explicit")
        _strings(comparison.get("items"), name + ".items")
        _strings(comparison.get("outerseeds"), name + ".outerseeds")
        require(comparison.get("metric") in metrics, "unknown comparison metric")
        require(comparison.get("role") in ("primary", "secondary"), "comparison.role must be primary or secondary")
        require(comparison.get("bootstrap_method") in METHODS, "unknown bootstrap_method")
        _integer(comparison.get("minimum_items"), name + ".minimum_items", 1)
        _integer(comparison.get("minimum_outerseeds"), name + ".minimum_outerseeds", 1)
        comparison["minimum_effect"] = _number(comparison.get("minimum_effect"), name + ".minimum_effect")
        require(comparison["minimum_effect"] >= 0,
                "minimum_effect must be nonnegative and in the declared metric unit")
        required_gates = comparison.get("quality_gate_ids")
        require(isinstance(required_gates, list), name + ".quality_gate_ids must be explicit")
        for gate_id in required_gates:
            _string(gate_id, "comparison quality gate id")
        require(all(x in gate_ids for x in required_gates), "comparison references unknown quality gate")
        require(len(required_gates) == len(set(required_gates)), "duplicate comparison quality gate")
        system = "expgym" if comparison["kind"] == "expgym_free_tight" else "poolact"
        for gate in gates:
            if gate["id"] in required_gates:
                required_selectors = dict(system=system, **{field: comparison[field] for field in ("model", "scenario", "split")})
                require(all(gate["selectors"][field] == value for field, value in required_selectors.items()),
                        "comparison quality gate binds a different model/system/scenario/split: " + gate["id"])
        if comparison["kind"] == "poolact_vs_naive":
            _string(comparison.get("regime"), name + ".regime")
            require(comparison.get("strategy", "poolact") in ("poolact", "cached"), "invalid candidate strategy")
        else:
            _string(comparison.get("strategy"), name + ".strategy")
    return by_path


def load_rows(csv_path: Path, manifest: Dict[str, Any], artifacts: Dict[str, Dict[str, Any]],
              payload: Optional[bytes] = None) -> List[Dict[str, Any]]:
    expected = {(tuple(a[field] for field in IDENTITY), metric): path
                for path, a in artifacts.items() for metric in a["metrics"]}
    observed = set()
    rows = []
    csv_bytes = csv_path.read_bytes() if payload is None else payload
    with io.StringIO(csv_bytes.decode("utf-8"), newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None and len(reader.fieldnames) == len(CSV_FIELDS)
                and set(reader.fieldnames) == set(CSV_FIELDS), "CSV must contain exactly: " + ",".join(CSV_FIELDS))
        for line, row in enumerate(reader, 2):
            require(None not in row and all(value is not None for value in row.values()), "malformed CSV row " + str(line))
            key = (tuple(row[field] for field in IDENTITY), row["metric"])
            require(key in expected, "unregistered CSV row " + str(line) + ": " + repr(key))
            require(key not in observed, "duplicate CSV row " + str(line) + ": " + repr(key))
            require(row["artifact"] == expected[key], "CSV artifact/identity mismatch on line " + str(line))
            observed.add(key)
            row["value"] = _number(row["value"], "CSV value line " + str(line))
            spec = manifest["metrics"][row["metric"]]
            for bound, predicate in (("minimum", lambda x, y: x >= y), ("maximum", lambda x, y: x <= y)):
                if spec.get(bound) is not None:
                    require(predicate(row["value"], spec[bound]), "CSV value outside declared metric range on line " + str(line))
            row["split"] = artifacts[row["artifact"]]["split"]
            rows.append(row)
    missing = set(expected) - observed
    require(not missing, "missing registered CSV rows: " + str(len(missing)) + "; no complete-case filtering allowed")
    return sorted(rows, key=lambda row: tuple(row[field] for field in IDENTITY) + (row["metric"],))


def audit_artifacts(manifest_path: Path, artifacts: Dict[str, Dict[str, Any]], manifest_hash: str,
                    csv_hash: str, receipt_path: Optional[Path]) -> Dict[str, Any]:
    hashes = {}
    resolved_paths = set()
    physical_files = set()
    for name in sorted(artifacts):
        path = Path(name)
        path = (path if path.is_absolute() else manifest_path.parent / path).resolve()
        require(path.is_file(), "missing declared artifact: " + str(path))
        require(path not in resolved_paths, "multiple artifact aliases resolve to the same file: " + str(path))
        resolved_paths.add(path)
        stat = path.stat()
        physical_key = (stat.st_dev, stat.st_ino)
        require(physical_key not in physical_files, "multiple artifact hardlink aliases identify the same physical file: " + str(path))
        physical_files.add(physical_key)
        hashes[name] = sha256_file(path)
    result = {"artifact_sha256": hashes, "receipt_bound": False,
              "receipt_declares_complete_recomputed_scores": False,
              "scores_recomputed_by_analyzer": False,
              "note": "Receipt binding is an export contract and an external declaration, not independent score truth. This analyzer never recomputes benchmark scores or attests auditor independence."}
    if receipt_path is not None:
        receipt_bytes = receipt_path.read_bytes()
        receipt = read_json(receipt_path, receipt_bytes)
        require(type(receipt.get("schema_version")) is int and receipt["schema_version"] == 1,
                "invalid integrity receipt schema")
        require(receipt.get("manifest_sha256") == manifest_hash, "integrity receipt manifest hash mismatch")
        require(receipt.get("csv_sha256") == csv_hash, "integrity receipt CSV hash mismatch")
        require(receipt.get("artifact_sha256") == hashes, "integrity receipt artifact set/hash mismatch")
        require(type(receipt.get("complete")) is bool and type(receipt.get("score_recomputation_passed")) is bool,
                "receipt must explicitly declare completeness and independent score recomputation")
        result["receipt_bound"] = True
        result["receipt_declares_complete_recomputed_scores"] = receipt["complete"] and receipt["score_recomputation_passed"]
        result["receipt_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()
        result["receipt_path"] = str(receipt_path.resolve())
    return result


def aggregate_rows(rows: List[Dict[str, Any]], by_outerseed: bool = False) -> List[Dict[str, Any]]:
    fields = GROUP_FIELDS + (("outerseed",) if by_outerseed else ())
    groups: Dict[Tuple[str, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in fields)].append(row)
    output = []
    for key, values in sorted(groups.items()):
        items: Dict[str, List[float]] = defaultdict(list)
        for row in values:
            items[row["item"]].append(row["value"])
        item_means = [statistics.mean(items[item]) for item in sorted(items)]
        entry = dict(zip(fields, key))
        entry.update(mean=statistics.mean(item_means), n_items=len(items), n_rows=len(values),
                     n_outerseeds=len({row["outerseed"] for row in values}),
                     item_mean_min=min(item_means), item_mean_max=max(item_means))
        output.append(entry)
    return output


def evaluate_quality_gates(rows: List[Dict[str, Any]], gates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output = []
    for gate in gates:
        selected = [row for row in rows if row["metric"] == gate["metric"]
                    and all(row[field] == value for field, value in gate["selectors"].items())]
        require(bool(selected), "quality gate selects no rows: " + gate["id"])
        items: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        for row in selected:
            items[(row["scenario"], row["item"])].append(row["value"])
        mean = statistics.mean(statistics.mean(values) for values in items.values())
        passed = mean <= gate["threshold"] if gate["operator"] == "<=" else mean >= gate["threshold"]
        output.append(dict(gate, value=mean, passed=passed, n_items=len(items), n_rows=len(selected),
                           aggregation="equal item weight; equal selected rows within item"))
    return output


def quantile(sorted_values: Sequence[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower)


def bootstrap_differences(item_deltas: Sequence[Sequence[float]], method: str,
                          samples: int, seed: int) -> List[float]:
    """Pairs are indivisible; agents/hypotheses never enter this resampler."""
    rng = random.Random(seed)
    item_means = [statistics.mean(values) for values in item_deltas]
    count = len(item_deltas)
    estimates = []
    for _ in range(samples):
        if method == "fixed_items_outer_repeats":
            # Same seed index across fixed items forms one repetition block.
            # Do not turn item x seed cells into independent replicates.
            repeats = len(item_deltas[0])
            indices = [rng.randrange(repeats) for _ in range(repeats)]
            estimates.append(sum(sum(values[index] for index in indices) / repeats
                                 for values in item_deltas) / count)
            continue
        indices = [rng.randrange(count) for _ in range(count)]
        means = []
        for index in indices:
            if method == "item_cluster":
                means.append(item_means[index])
            else:
                values = item_deltas[index]
                means.append(sum(values[rng.randrange(len(values))] for _ in values) / len(values))
        estimates.append(sum(means) / count)
    return sorted(estimates)


def compare(rows: List[Dict[str, Any]], spec: Dict[str, Any], manifest: Dict[str, Any],
            family_size: int, integrity: Dict[str, Any], gate_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    is_expgym = spec["kind"] == "expgym_free_tight"
    system = "expgym" if is_expgym else "poolact"
    baseline_regime = "cost_free" if is_expgym else spec["regime"]
    target_regime = "cost_tight" if is_expgym else spec["regime"]
    baseline_strategy = spec["strategy"] if is_expgym else "naive"
    target_strategy = spec["strategy"] if is_expgym else spec.get("strategy", "poolact")
    indexed = {(tuple(row[field] for field in IDENTITY), row["metric"]): row for row in rows}
    metric = manifest["metrics"][spec["metric"]]
    orientation = (1 if metric["higher_is_better"] else -1) * (-1 if is_expgym else 1)
    paired_rows = []
    clusters = []
    item_deltas = []
    for item in sorted(spec["items"]):
        item_pairs = []
        for seed in sorted(spec["outerseeds"]):
            base_key = ((spec["model"], system, spec["scenario"], item, baseline_regime, baseline_strategy, seed), spec["metric"])
            target_key = ((spec["model"], system, spec["scenario"], item, target_regime, target_strategy, seed), spec["metric"])
            require(base_key in indexed and target_key in indexed,
                    "unpaired registered comparison " + spec["id"] + " item=" + item + " outerseed=" + seed)
            baseline, target = indexed[base_key], indexed[target_key]
            require(baseline["split"] == target["split"] == spec["split"], "comparison split mismatch: " + spec["id"])
            pair = {"comparison": spec["id"], "item": item, "outerseed": seed,
                    "baseline": baseline["value"], "target": target["value"],
                    "effect": orientation * (target["value"] - baseline["value"]),
                    "baseline_artifact": baseline["artifact"], "target_artifact": target["artifact"]}
            paired_rows.append(pair)
            item_pairs.append(pair)
        cluster = {"comparison": spec["id"], "item": item, "n_outerseeds": len(item_pairs)}
        cluster.update({field: statistics.mean(pair[field] for pair in item_pairs) for field in ("baseline", "target", "effect")})
        clusters.append(cluster)
        item_deltas.append([pair["effect"] for pair in item_pairs])
    item_effects = [cluster["effect"] for cluster in clusters]
    estimate = statistics.mean(item_effects)
    baseline_mean = statistics.mean(cluster["baseline"] for cluster in clusters)
    target_mean = statistics.mean(cluster["target"] for cluster in clusters)
    config = manifest["bootstrap"]
    alpha = 1 - config["confidence"]
    adjusted_alpha = alpha / family_size if spec["role"] == "primary" else alpha
    seed_material = (str(config["seed"]) + "\0" + spec["id"]).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    distribution = bootstrap_differences(item_deltas, spec["bootstrap_method"], config["samples"], seed)
    interval = lambda a: [quantile(distribution, a / 2), quantile(distribution, 1 - a / 2)]
    nominal_ci, adjusted_ci = interval(alpha), interval(adjusted_alpha)
    # Percentile bootstrap has no finite-sample validity guarantee here. In
    # particular, n=3 iid null effects +/-1 are all +1 with probability 1/8;
    # every bootstrap draw then equals +1, for any resampling count/family size.
    # Metadata, sample minima, and a passing receipt cannot establish coverage.
    blockers = [NO_CONFIRMATORY_METHOD]
    warnings = []
    if not manifest["registration"]["frozen_before_evaluation"]:
        blockers.append("not_declared_preregistered")
    if not integrity["receipt_declares_complete_recomputed_scores"]:
        blockers.append("missing_or_failed_bound_recomputation_declaration")
    if not spec["quality_gate_ids"]:
        blockers.append("no_preregistered_quality_gates")
    for gate_id in spec["quality_gate_ids"]:
        if not gate_results[gate_id]["passed"]:
            blockers.append("quality_gate_failed:" + gate_id)
    if len(clusters) < spec["minimum_items"]:
        blockers.append("below_preregistered_minimum_items")
    if len(spec["outerseeds"]) < spec["minimum_outerseeds"]:
        blockers.append("below_preregistered_minimum_outerseeds")
    method = spec["bootstrap_method"]
    if method in ("item_cluster", "nested") and len(clusters) < 2:
        blockers.append("item_resampling_requires_at_least_two_items")
    if method in ("nested", "fixed_items_outer_repeats") and len(spec["outerseeds"]) < 2:
        blockers.append("outer_repeat_resampling_requires_at_least_two_repeats")
    if config["samples"] * adjusted_alpha / 2 < 20:
        blockers.append("fewer_than_20_expected_bootstrap_draws_per_decision_tail")
    warnings.append("all sample sizes remain descriptive; neither count thresholds nor additional bootstrap draws validate coverage")
    warnings.append("fixed data snapshots only; shared-corpus dependence is not modeled as independent corpus replication")
    if spec["scope"]["item_status"] != "prospectively_reserved":
        warnings.append("known or possibly inspected items; split naming does not establish held-out evaluation")
    if spec["scope"]["outer_repetition_interpretation"] != "verified_generation_repeats":
        warnings.append("outerseed labels/orders do not establish independent generation repeats or effective provider seed control")
    else:
        warnings.append("generation-repeat independence is externally declared, not verified by this analyzer")
    if distribution[0] == distribution[-1]:
        warnings.append("degenerate_empirical_bootstrap; zero interval width is not proof of zero population uncertainty")
    if method == "item_cluster":
        inference = "descriptive resampling of registered items within fixed listed snapshots; retains the recorded outerseed/order set; no item/corpus-population inference"
    elif method == "nested":
        inference = "descriptive two-level resampling of registered items and paired within-item repeats; independent within-item variation is an unverified assumption; no item/corpus-population inference"
    else:
        inference = "descriptive resampling of shared outerseed blocks across the fixed registered items; no unverified-generation or task/corpus-population generalization"
    sd = statistics.stdev(item_effects) if len(item_effects) > 1 else 0.0
    status = "not_confirmatory" if spec["role"] == "primary" else "exploratory_secondary"
    return {
        "id": spec["id"], "specification": spec, "effect_definition":
        ("free minus tight, oriented by metric utility" if is_expgym else "candidate minus naive, oriented by metric utility"),
        "unit": metric["unit"], "baseline_mean": baseline_mean, "target_mean": target_mean,
        "effect": estimate, "relative_effect_percent": 100 * estimate / abs(baseline_mean) if baseline_mean != 0 else None,
        "paired_item_dz_descriptive": estimate / sd if sd > 0 and method != "fixed_items_outer_repeats" else None,
        "fraction_items_positive": sum(value > 0 for value in item_effects) / len(item_effects),
        "n_items": len(clusters), "n_outerseeds": len(spec["outerseeds"]), "n_pairs": len(paired_rows),
        "nominal_ci": nominal_ci, "family_adjusted_descriptive_ci": adjusted_ci,
        "nominal_level": config["confidence"], "family_adjusted_nominal_level": 1 - adjusted_alpha,
        "interval_use": "descriptive_only_not_a_validated_confidence_guarantee",
        "primary_family_size": family_size if spec["role"] == "primary" else None,
        "multiplicity": "Bonferroni-form tail adjustment for descriptive display only; familywise error control not established" if spec["role"] == "primary"
        else "unadjusted exploratory percentile interval; not a confirmatory test",
        "bootstrap_seed": seed, "bootstrap_samples": config["samples"], "inference_target": inference,
        "status": status, "confirmatory_inference_available": False,
        "observed_direction": "positive" if estimate > 0 else "negative" if estimate < 0 else "zero",
        "observed_effect_exceeds_registered_minimum": estimate > spec["minimum_effect"],
        "confirmatory_blockers": blockers, "warnings": warnings,
        "pairs": paired_rows, "items": clusters,
    }


def analyze(manifest_path: Path, csv_path: Path, expected_manifest_sha256: str,
            audit_receipt: Optional[Path] = None) -> Dict[str, Any]:
    manifest_bytes = manifest_path.read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    require(manifest_hash == expected_manifest_sha256, "frozen manifest SHA256 mismatch")
    manifest = read_json(manifest_path, manifest_bytes)
    artifacts = validate_manifest(manifest)
    csv_bytes = csv_path.read_bytes()
    csv_hash = hashlib.sha256(csv_bytes).hexdigest()
    rows = load_rows(csv_path, manifest, artifacts, csv_bytes)
    integrity = audit_artifacts(manifest_path, artifacts, manifest_hash, csv_hash, audit_receipt)
    gates = evaluate_quality_gates(rows, manifest["quality_gates"])
    gate_results = {gate["id"]: gate for gate in gates}
    families = Counter(comparison["family"] for comparison in manifest["comparisons"] if comparison["role"] == "primary")
    comparisons = [compare(rows, spec, manifest, families[spec["family"]], integrity, gate_results)
                   for spec in manifest["comparisons"]]
    # Detect ordinary concurrent changes before handing off a report. This is
    # not an atomic filesystem snapshot or protection against change-and-revert.
    require(sha256_file(manifest_path) == manifest_hash, "manifest changed during analysis")
    require(sha256_file(csv_path) == csv_hash, "CSV changed during analysis")
    final_integrity = audit_artifacts(manifest_path, artifacts, manifest_hash, csv_hash, audit_receipt)
    require(final_integrity == integrity, "artifacts or receipt changed during analysis")
    integrity["end_of_analysis_stability_guard_passed"] = True
    return {"schema_version": 1, "study_id": manifest["study_id"], "run_classification": "Custom study",
            "manifest_sha256": manifest_hash, "csv_sha256": csv_hash,
            "manifest_path": str(manifest_path.resolve()), "csv_path": str(csv_path.resolve()),
            "analysis_source_sha256": sha256_file(Path(__file__)), "registration": manifest["registration"],
            "input_complete": True, "integrity": integrity, "quality_gates": gates,
            "primary_families": dict(sorted(families.items())), "comparisons": comparisons,
            "aggregate_metrics": aggregate_rows(rows), "by_outerseed": aggregate_rows(rows, True),
            "n_rows": len(rows), "n_artifacts": len(artifacts),
            "confirmatory_inference_available": False,
            "all_primary_hypotheses_supported": None,
            "interpretation": [
                "All bootstrap intervals are descriptive; no implemented method can establish supported, refuted, or equivalent hypotheses at any sample size.",
                "Successful analysis is not evidence of a positive treatment effect. All observed positive, zero and negative effects are retained.",
                "Manifest hash pinning detects changes, but cannot independently prove the preregistration date or unseen held-out status.",
                "Pairs share item and outerseed; individual pool agents, audit hypotheses, and repeated draws are not independent items.",
                "Fixed snapshots and registered items only: no unseen-corpus, unseen-task, generation-population, causal or cross-model inference is established.",
                "An externally bound recomputation receipt is a declared export contract; this analyzer does not establish auditor independence or recompute score truth.",
                "Manifest/CSV/receipt hashes bind their parsed byte snapshots; an end-of-analysis stability guard is not an atomic or adversarial concurrent-write guarantee.",
                "No missing/integrity-failed row is silently dropped or assigned zero; semantic zero scores are retained.",
            ]}


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    require(bool(rows), "refusing to write an empty table: " + str(path))
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(report: Dict[str, Any], output_dir: Path) -> None:
    require(not output_dir.exists(), "output directory already exists; choose a new path: " + str(output_dir))
    output_dir.mkdir(parents=True, exist_ok=False)
    comparisons = report["comparisons"]
    write_csv(output_dir / "paired_rows.csv", [row for result in comparisons for row in result["pairs"]])
    write_csv(output_dir / "paired_items.csv", [row for result in comparisons for row in result["items"]])
    write_csv(output_dir / "aggregate_metrics.csv", report["aggregate_metrics"])
    write_csv(output_dir / "by_outerseed.csv", report["by_outerseed"])
    effects = [{"comparison": result["id"], "role": result["specification"]["role"],
                "family": result["specification"]["family"], "model": result["specification"]["model"],
                "scenario": result["specification"]["scenario"], "metric": result["specification"]["metric"],
                "baseline": result["baseline_mean"], "target": result["target_mean"], "effect": result["effect"],
                "unit": result["unit"], "relative_effect_percent": result["relative_effect_percent"],
                "nominal_ci_low": result["nominal_ci"][0], "nominal_ci_high": result["nominal_ci"][1],
                "adjusted_descriptive_ci_low": result["family_adjusted_descriptive_ci"][0],
                "adjusted_descriptive_ci_high": result["family_adjusted_descriptive_ci"][1],
                "status": result["status"], "observed_direction": result["observed_direction"],
                "n_items": result["n_items"], "n_outerseeds": result["n_outerseeds"],
                "n_pairs": result["n_pairs"], "blockers": ";".join(result["confirmatory_blockers"])} for result in comparisons]
    write_csv(output_dir / "effects.csv", effects)
    with (output_dir / "report.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    lines = ["# Portable study: " + report["study_id"], "", "Custom study; all registered comparisons are shown, including negative outcomes.", "",
             "Input coverage complete: true. Bound receipt declares complete recomputed scores: "
             + str(report["integrity"]["receipt_declares_complete_recomputed_scores"]).lower() + ". This is an external declaration, not score truth verified by this analyzer.", "",
             "Confirmatory inference is unavailable at every sample size. Bootstrap intervals are descriptive only; no supported/refuted decision is made.", "",
             "Positive effects mean Free-to-Tight degradation for ExpGym, or candidate-over-Naive improvement for PoolAct.",
             "Intervals use the metric's declared units (fraction is not percentage points).", "",
             "| Comparison | Baseline | Target | Effect | Descriptive interval | Status | Items × repeats |",
             "|---|---:|---:|---:|---|---|---:|"]
    for result in comparisons:
        low, high = result["family_adjusted_descriptive_ci"]
        safe_id = result["id"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {safe_id} | {result['baseline_mean']:.6g} | {result['target_mean']:.6g} | {result['effect']:.6g} | [{low:.6g}, {high:.6g}] | {result['status']} | {result['n_items']} × {result['n_outerseeds']} |")
    lines += ["", "Primary displays use Bonferroni-form tail adjustment, but neither nominal coverage nor familywise error control is established. Secondary displays are exploratory too.", ""]
    for result in comparisons:
        lines += ["## " + result["id"].replace("\n", " "), "", "Descriptive scope: " + result["inference_target"] + ".", "",
                  "Confirmatory blockers: " + (", ".join(result["confirmatory_blockers"]) or "none") + ".", "",
                  "Warnings: " + ("; ".join(result["warnings"]) or "none") + ".", ""]
    lines += ["## Limits", ""] + ["- " + message for message in report["interpretation"]]
    lines += ["", "See [effects.csv](effects.csv), [paired_items.csv](paired_items.csv), [paired_rows.csv](paired_rows.csv), [aggregate_metrics.csv](aggregate_metrics.csv), [by_outerseed.csv](by_outerseed.csv), and [report.json](report.json).", ""]
    with (output_dir / "REPORT.md").open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True, help="Hash recorded before outcome inspection, not a newly calculated replacement.")
    parser.add_argument("--csv", type=Path, required=True, help="Explicit ten-column pool/trace-level metric export.")
    parser.add_argument("--audit-receipt", type=Path, help="External recomputation declaration bound to this manifest, CSV, and all artifacts; not independently verified score truth.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Must not already exist; historical reports are never overwritten.")
    args = parser.parse_args(argv)
    try:
        require(not args.output_dir.exists(), "output directory already exists: " + str(args.output_dir))
        report = analyze(args.manifest, args.csv, args.manifest_sha256, args.audit_receipt)
        write_report(report, args.output_dir)
    except (StudyError, OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
        print("[portable-study] invalid evidence: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"output_dir": str(args.output_dir), "input_complete": True,
                      "comparisons": len(report["comparisons"]),
                      "all_primary_hypotheses_supported": report["all_primary_hypotheses_supported"]}))
    return 0  # Negative effects are valid results, never a request to rerun until positive.


if __name__ == "__main__":
    raise SystemExit(main())
