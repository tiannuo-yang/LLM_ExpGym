"""Pure, missing-aware units and tables for the fixed third-model study.

No file access, runner imports, scoring, sampling, or model calls. Input rows
must include every planned execution/metric, including explicit None values.
The caller binds the execution universe and provenance to the frozen queue.
"""
from collections import defaultdict
import hashlib
import json
import math
import statistics


UNIT_FIELDS = ("model", "system", "scenario", "item", "family", "regime",
               "strategy", "N", "outerrep")
SETTING_FIELDS = ("model", "system", "scenario", "regime", "strategy", "N",
                  "metric", "unit", "higher_is_better", "scope")
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STRATEGIES = ("naive", "cached", "poolact")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _mean(values):
    return math.fsum(values) / len(values) if values else None


def _metric_spec(row, metric_defs):
    definition = (metric_defs or {}).get(row["metric"], {})
    _require(isinstance(definition, dict), "metric definition must be an object")
    for name in ("unit", "higher_is_better", "scope"):
        if name in row and name in definition:
            _require(row[name] == definition[name], "row/definition metric metadata differ: " + name)
    unit = row["unit"]
    higher = row.get("higher_is_better", definition.get("higher_is_better"))
    scope = row.get("scope", definition.get("scope", "unspecified"))
    _require(higher is None or type(higher) is bool, "higher_is_better must be bool or None")
    _require(isinstance(unit, str) and unit.strip(), "metric unit must be nonempty")
    _require(isinstance(scope, str) and scope.strip(), "metric scope must be nonempty")
    return {"unit": unit, "higher_is_better": higher, "scope": scope}


def _row(row, metric_defs):
    _require(type(row) is dict, "metric row must be an object")
    required = set(UNIT_FIELDS) | {"execution_id", "order", "seed", "metric", "value", "unit"}
    _require(required <= set(row), "metric row is missing required fields")
    for key in ("execution_id", "model", "scenario", "item", "family", "metric"):
        _require(type(row[key]) is str and bool(row[key].strip()), key + " must be a nonempty string")
    _require(row["system"] in ("expgym", "poolact"), "unknown system")
    _require(row["scenario"] in ("restricted_search", "evidence_audit", "tuning"), "unknown scenario")
    _require(row["regime"] in REGIMES, "unknown regime")
    _require(type(row["N"]) is int and row["N"] > 0, "N must be a positive integer")
    _require(type(row["outerrep"]) is int and row["outerrep"] >= 0, "outerrep must be a nonnegative integer")
    _require(type(row["seed"]) is int and row["seed"] >= 0, "seed must be a nonnegative integer")
    _require(row["value"] is None or _finite(row["value"]), "value must be finite numeric or None")
    if row["system"] == "expgym":
        _require(row["N"] == 1 and row["strategy"] == "single", "ExpGym requires N=1 and single strategy")
    else:
        _require(row["strategy"] in STRATEGIES, "unknown PoolAct strategy")
    audit = row["system"] == "expgym" and row["scenario"] == "evidence_audit"
    if audit:
        _require(row["outerrep"] == 0, "this study's Audit orders belong to outerrep 0")
        _require(type(row["order"]) is int and row["order"] in (0, 1, 2), "Audit order must be 0, 1 or 2")
    else:
        expected_order = "default" if row["scenario"] == "evidence_audit" else "none"
        _require(row["order"] == expected_order, "non-Exp-Audit order must be " + expected_order)
    if row["scenario"] != "tuning":
        _require(row["outerrep"] == 0, "Search/Pool Audit are R1 in this study")
    return {**row, **_metric_spec(row, metric_defs)}


def collapse(rows, metric_defs=None):
    """Fold three Exp Audit orders once; retain all other execution units.

    Required input fields: execution_id, model, system, scenario, item, family,
    regime, strategy, N, outerrep, order, seed, metric, value, unit. Non-Audit
    order is 'none', Pool Audit order is 'default', Exp Audit orders are ints
    0/1/2. Optional metric_defs maps metric to unit/higher_is_better/scope.

    Output retains UNIT_FIELDS and metric metadata, with analysis_id, value,
    components [{execution_id, order, seed, value}], expected/known/missing
    component counts, known_component_subset_mean, orders and seed_labels.
    analysis_id identifies the scientific unit and deliberately excludes metric.
    Missing execution rows are an error: planned missing values must be None.
    """
    groups, executions, slots, seen, definitions = defaultdict(list), {}, {}, set(), {}
    for source in rows:
        row = _row(source, metric_defs)
        marker = (row["execution_id"], row["metric"])
        _require(marker not in seen, "duplicate execution/metric row")
        seen.add(marker)
        identity = tuple(row[name] for name in UNIT_FIELDS)
        execution_identity = identity + (row["order"], row["seed"])
        prior = executions.setdefault(row["execution_id"], execution_identity)
        _require(prior == execution_identity, "one execution_id has conflicting metadata")
        slot = identity + (row["order"],)
        component = (row["execution_id"], row["seed"])
        _require(slots.setdefault(slot, component) == component,
                 "one planned component has different executions across metrics")
        spec = tuple(row[name] for name in ("unit", "higher_is_better", "scope"))
        _require(definitions.setdefault(row["metric"], spec) == spec, "inconsistent metric definition")
        groups[identity + (row["metric"],)].append(row)
    _require(bool(groups), "no planned metric rows")
    output = []
    for key in sorted(groups, key=_canonical):
        selected = sorted(groups[key], key=lambda row: (str(row["order"]), row["execution_id"]))
        first = selected[0]
        audit = first["system"] == "expgym" and first["scenario"] == "evidence_audit"
        if audit:
            _require(len(selected) == 3 and {row["order"] for row in selected} == {0, 1, 2},
                     "Audit analysis unit requires exactly three planned orders; use explicit None for missing")
        else:
            _require(len(selected) == 1, "non-Audit analysis unit requires exactly one execution")
        identity = {name: first[name] for name in UNIT_FIELDS}
        known = [row["value"] for row in selected if row["value"] is not None]
        complete = len(known) == len(selected)
        output.append({**identity, "metric": first["metric"],
                       **{name: first[name] for name in ("unit", "higher_is_better", "scope")},
                       "analysis_id": "analysis_" + hashlib.sha256(_canonical(identity).encode()).hexdigest(),
                       "value": _mean(known) if complete else None,
                       "known_component_subset_mean": _mean(known),
                       "expected_components": len(selected), "known_components": len(known),
                       "missing_components": len(selected) - len(known),
                       "components": [{name: row[name] for name in ("execution_id", "order", "seed", "value")}
                                      for row in selected],
                       "orders": [row["order"] for row in selected],
                       "seed_labels": sorted({row["seed"] for row in selected})})
    return output


def _slices(row):
    result = [("all", "all"), ("family", row["family"])]
    if row["scenario"] == "tuning":
        result.append(("task", row["item"]))
    return result


def _summary(rows):
    items = defaultdict(list)
    for row in rows:
        items[row["item"]].append(row)
    item_means, component_means = [], []
    for item in sorted(items):
        selected = items[item]
        values = [row["value"] for row in selected if row["value"] is not None]
        partial = [row["known_component_subset_mean"] for row in selected
                   if row["known_component_subset_mean"] is not None]
        if values:
            item_means.append(_mean(values))
        if partial:
            component_means.append(_mean(partial))
    known = sum(row["value"] is not None for row in rows)
    return {"expected_outcomes": len(rows), "known_outcomes": known,
            "missing_outcomes": len(rows) - known,
            "expected_items": len(items), "known_items": len(item_means),
            "complete_items": sum(all(row["value"] is not None for row in values) for values in items.values()),
            "full_mean": _mean(item_means) if known == len(rows) else None,
            "known_subset_item_weighted_mean": _mean(item_means),
            "known_component_subset_item_weighted_mean": _mean(component_means),
            "expected_components": sum(row["expected_components"] for row in rows),
            "known_components": sum(row["known_components"] for row in rows),
            "missing_components": sum(row["missing_components"] for row in rows),
            "min_repeats_per_item": min(map(len, items.values())),
            "max_repeats_per_item": max(map(len, items.values()))}


def aggregate(rows, metric_defs=None):
    """Return (absolute, by_outerseed, contrasts) from collapse() output.

    Absolute means first average outerrep within item, then give items equal
    weight. 'known_subset' uses only complete analysis units; the separately
    named 'known_component_subset' may use known Audit orders in partial units.
    All full means/differences stay None if any planned endpoint is unknown.
    Slice identity is (slice_kind, slice), avoiding family/task name collisions.

    Contrast effect is Free-Moderate/Free-Tight/Moderate-Tight for ExpGym, and
    cached-naive/poolact-naive/poolact-cached for PoolAct. It is a raw difference
    in the declared unit, not automatically a quality claim. utility_effect is
    sign-oriented only when higher_is_better is explicitly bool, otherwise None.
    """
    groups, seen, definitions = defaultdict(list), set(), {}
    for source in rows:
        row = {**source, **_metric_spec(source, metric_defs)}
        marker = tuple(row[name] for name in UNIT_FIELDS) + (row["metric"],)
        _require(marker not in seen, "duplicate scientific analysis unit/metric")
        seen.add(marker)
        _require(row["value"] is None or _finite(row["value"]), "invalid collapsed value")
        spec = tuple(row[name] for name in ("unit", "higher_is_better", "scope"))
        _require(definitions.setdefault(row["metric"], spec) == spec, "inconsistent metric definition")
        for slice_kind, slice_name in _slices(row):
            groups[tuple(row[name] for name in SETTING_FIELDS) + (slice_kind, slice_name)].append(row)
    _require(bool(groups), "no planned analysis rows")
    fields = SETTING_FIELDS + ("slice_kind", "slice")
    absolute, by_outerseed, lookup = [], [], {}
    for key in sorted(groups, key=_canonical):
        selected = sorted(groups[key], key=lambda row: (row["item"], row["outerrep"]))
        _require(len({(row["item"], row["outerrep"]) for row in selected}) == len(selected),
                 "duplicate planned item/outerrep within setting")
        identity = dict(zip(fields, key))
        summary = _summary(selected)
        blocks = defaultdict(list)
        for row in selected:
            blocks[row["outerrep"]].append(row)
        block_means, block_items = [], []
        for outerrep, block_rows in sorted(blocks.items()):
            block = _summary(block_rows)
            block_means.append(block["full_mean"])
            block_items.append({row["item"] for row in block_rows})
            by_outerseed.append({**identity, "outerrep": outerrep,
                                 "seed_labels": sorted({seed for row in block_rows for seed in row["seed_labels"]}),
                                 **block})
        same_items = all(items == block_items[0] for items in block_items)
        summary.update(repeat_blocks=len(blocks), repeat_block_items_match=same_items,
                       descriptive_repeat_sd=statistics.stdev(block_means)
                       if len(blocks) > 1 and same_items and all(value is not None for value in block_means) else None)
        record = {**identity, **summary}
        absolute.append(record)
        lookup[key] = record
    contrasts = []
    for key in sorted(groups, key=_canonical):
        identity = dict(zip(fields, key))
        expgym = identity["system"] == "expgym"
        axis, levels = ("regime", REGIMES) if expgym else ("strategy", STRATEGIES)
        for target in levels[levels.index(identity[axis]) + 1:]:
            other = {**identity, axis: target}
            target_key = tuple(other[name] for name in fields)
            if target_key not in groups:
                continue  # Unplanned combinations are not missing outcomes.
            first = {(row["item"], row["outerrep"]): row for row in groups[key]}
            second = {(row["item"], row["outerrep"]): row for row in groups[target_key]}
            _require(set(first) == set(second), "contrast planned item/outerrep universes differ; no intersection allowed")
            pairs = []
            for pair in sorted(first):
                a, b = first[pair]["value"], second[pair]["value"]
                value = (a - b if expgym else b - a) if a is not None and b is not None else None
                pairs.append({"item": pair[0], "value": value,
                              "known_component_subset_mean": value,
                              "expected_components": 1, "known_components": int(value is not None),
                              "missing_components": int(value is None)})
            paired = _summary(pairs)
            effect = paired.pop("full_mean")
            known_effect = paired.pop("known_subset_item_weighted_mean")
            # These are pairs of complete scientific units, not Audit orders.
            for name in ("known_component_subset_item_weighted_mean", "expected_components", "known_components", "missing_components"):
                paired.pop(name)
            orientation = identity["higher_is_better"]
            utility = effect * (1 if orientation else -1) if effect is not None and orientation is not None else None
            baseline = lookup[key]["full_mean"]
            contrasts.append({**identity, "comparison_axis": axis, "baseline": identity[axis], "target": target,
                              "effect_definition": "baseline_minus_target" if expgym else "target_minus_baseline",
                              "baseline_full_mean": baseline, "target_full_mean": lookup[target_key]["full_mean"],
                              "effect": effect, "utility_effect": utility,
                              "known_paired_subset_effect": known_effect,
                              "relative_effect_percent": 100 * effect / abs(baseline)
                              if effect is not None and baseline not in (None, 0) else None,
                              **paired})
    return absolute, by_outerseed, contrasts
