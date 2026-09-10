#!/usr/bin/env python3
"""Reaggregate the two frozen final exports; no model, scorer, raw-data or network IO."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import statistics

HERE = Path(__file__).resolve().parent
COMMIT = "6119f9d136c9ed1f06a7bedd7371be0deb9b5d59"
BASE = Path("results/portable-eval-20260908/full_delivery_v5")
SOURCES = {
    "kimi-k3": ("kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final",
                "fc68a5a057c45056924b17b91f054311d6cd43dc8174da85892265f8d7758f86"),
    "glm-5.3": ("glm-5.3-original-completed-20260909/analysis/actual_formal_export_glm_completed_v2",
                "e32cab1af07054e76503aab79c66b76bcc216d2021cf0f46cd638340023bbca7"),
}
IDENTITY = ("model", "system", "scenario", "item", "regime", "strategy", "outerseed")
KEY = ("model", "system", "scenario", "slice", "regime", "strategy", "metric")
QUALITY = {"f1", "f1_mi", "f1_mv", "evidence_acc", "evidence_acc_mi", "evidence_acc_mv",
           "label_acc", "label_acc_mi", "label_acc_mv", "gap", "gap_mi", "gap_bon",
           "raw_perf", "raw_perf_mi", "raw_perf_bon"}
RESOURCES = {"feedback_attempts", "feedback_visible", "duplicate_action_attempts",
             "feedback_cost_seconds", "input_tokens", "output_tokens", "wall_time_seconds",
             "protocol_failure_rate", "budget_utilization"}
QUALITY_CATALOGUE = {
    ("expgym", "restricted_search"): {"f1"},
    ("expgym", "evidence_audit"): {"evidence_acc", "label_acc"},
    ("expgym", "tuning"): {"gap", "raw_perf"},
    ("poolact", "restricted_search"): {"f1_mi", "f1_mv"},
    ("poolact", "evidence_audit"): {"evidence_acc_mi", "evidence_acc_mv", "label_acc_mi", "label_acc_mv"},
    ("poolact", "tuning"): {"gap_mi", "gap_bon", "raw_perf_mi", "raw_perf_bon"},
}
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
AGG_FIELDS = [*KEY, "unit", "n_items", "n_repeats", "n_rows", "n_original_logical_rows",
              "n_known_rows", "n_missing_rows", "n_complete_items", "mean",
              "known_subset_mean_not_complete_endpoint", "seedblock_descriptive_sd",
              "outerseed_means", "status"]
BLOCK_FIELDS = [*KEY, "outerseed", "requested_seed_block_label", "unit", "n_items", "n_rows",
                "n_original_logical_rows", "n_known_rows", "n_missing_rows", "mean",
                "known_subset_mean_not_complete_endpoint", "status"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_number(value):
    if value == "":
        return None
    result = float(value)
    require(math.isfinite(result), "nonfinite metric value")
    return result


def strict_mean(values):
    return statistics.mean(values) if values and all(v is not None for v in values) else None


def slice_names(row):
    if row["scenario"] == "restricted_search":
        family = row["selector"]["question_family"]
        require(family in {"whois", "whatis"}, "unknown Search family")
        return ["all", family]
    if row["scenario"] == "tuning":
        return ["all", "family=" + row["selector"]["family"], "task=" + row["item"]]
    require(row["scenario"] == "evidence_audit", "unknown scenario")
    return ["all"]


def unit(system, scenario):
    return ("pool_aggregate_N4" if system == "poolact" else
            "document_mean_3_fixed_orders" if scenario == "evidence_audit" else "single_trace")


def read_sources(repo_root):
    all_rows, all_effects, metadata = [], [], {}
    inputs = {"source_commit": COMMIT, "source_files": [],
              "analysis_runtime": {"python": platform.python_version(), "implementation": platform.python_implementation()},
              "source_score_recomputation_performed": False,
              "new_model_calls": 0, "raw_artifact_reads": 0}
    checks = {}
    for model, (relative, index_hash) in SOURCES.items():
        folder = BASE / relative
        index_raw = (repo_root / folder / "EXPORT_INDEX.json").read_bytes()
        require(sha(index_raw) == index_hash, model + " final export index changed")
        index = json.loads(index_raw)
        blobs = {"EXPORT_INDEX.json": index_raw}
        for name in ("metrics.csv", "effects.csv", "manifest.json"):
            raw = (repo_root / folder / name).read_bytes()
            require({"bytes": len(raw), "sha256": sha(raw)} == index["files"][name], name + " pin mismatch")
            blobs[name] = raw
        for name, raw in blobs.items():
            inputs["source_files"].append({"model": model, "path": str(folder / name),
                                          "bytes": len(raw), "sha256": sha(raw)})
        manifest = json.loads(blobs["manifest.json"])
        require(manifest["schema_version"] == "restart-mixed-matrix-v1", "wrong manifest type")
        require(len(manifest["logical_rows"]) == 783, "incomplete manifest")
        logical = defaultdict(list)
        for row in manifest["logical_rows"]:
            require(row["model"] == model, "manifest model mismatch")
            key = tuple(row[k] for k in IDENTITY[:-1]) + ("outer_%05d" % row["outerrep"],)
            logical[key].append(row)
        require(len(logical) == 705, "wrong distinct analysis-unit count")
        for key, components in logical.items():
            audit = key[1:3] == ("expgym", "evidence_audit")
            require(len(components) == (3 if audit else 1), "wrong order collapse count")
            if audit:
                require({r["order"] for r in components} == {0, 1, 2}, "missing Audit order")
            require(all(r["selector"] == components[0]["selector"] for r in components), "selector mismatch")
            metadata[key] = components
        reader = csv.DictReader(io.StringIO(blobs["metrics.csv"].decode()))
        require(reader.fieldnames == [*IDENTITY, "metric", "value", "artifact"], "metric schema mismatch")
        rows = list(reader)
        require(len(rows) == 7687, "incomplete metrics export")
        cells, metrics_by_unit, artifact_by_unit = set(), defaultdict(set), {}
        for row in rows:
            key = tuple(row[k] for k in IDENTITY)
            require(key in logical, "metric outside manifest identity")
            cell = key + (row["metric"],)
            require(cell not in cells, "duplicate metric cell")
            cells.add(cell)
            metrics_by_unit[key].add(row["metric"])
            if key in artifact_by_unit:
                require(artifact_by_unit[key] == row["artifact"], "unit maps to multiple artifacts")
            artifact_by_unit[key] = row["artifact"]
            row["value"] = parse_number(row["value"])
        require(set(metrics_by_unit) == set(logical), "missing complete analysis unit")
        for key, actual in metrics_by_unit.items():
            expected = QUALITY_CATALOGUE[key[1:3]] | RESOURCES
            if key[4] == "cost_free":
                expected = expected - {"budget_utilization"}
            require(actual == expected, "missing/extra metric in planned unit")
        effects = list(csv.DictReader(io.StringIO(blobs["effects.csv"].decode())))
        require(len(effects) == 514 and all(r["model"] == model for r in effects), "wrong effects scope")
        all_rows += rows
        all_effects += effects
        checks[model] = {"source_metric_rows": len(rows), "source_logical_rows": len(manifest["logical_rows"]),
                         "analysis_units": len(logical), "source_effect_rows": len(effects),
                         "missing_metric_cells": sum(r["value"] is None for r in rows),
                         "missing_by_metric": dict(Counter(r["metric"] for r in rows if r["value"] is None)),
                         "performance_missing_cells": sum(r["value"] is None and r["metric"] in QUALITY for r in rows)}
    return all_rows, all_effects, metadata, inputs, checks


def aggregate(rows, metadata):
    groups = defaultdict(list)
    for row in rows:
        identity = tuple(row[k] for k in IDENTITY)
        for subset in slice_names(metadata[identity][0]):
            groups[(row["model"], row["system"], row["scenario"], subset,
                    row["regime"], row["strategy"], row["metric"])].append(row)
    aggregates, blocks = [], []
    for key, group in sorted(groups.items()):
        descriptor = dict(zip(KEY, key))
        expected_repeats = 3 if descriptor["scenario"] == "tuning" else 1
        expected_outers = {"outer_%05d" % i for i in range(expected_repeats)}
        items = defaultdict(dict)
        for row in group:
            require(row["outerseed"] not in items[row["item"]], "duplicate item/outer in metric group")
            items[row["item"]][row["outerseed"]] = row["value"]
        require(all(set(values) == expected_outers for values in items.values()), "incomplete repeated item")
        row_unit = unit(descriptor["system"], descriptor["scenario"])
        components = 3 if row_unit == "document_mean_3_fixed_orders" else 1
        item_means = [strict_mean(list(values.values())) for values in items.values()]
        known_items = [statistics.mean([v for v in values.values() if v is not None])
                       for values in items.values() if any(v is not None for v in values.values())]
        block_means = {}
        for outer in sorted(expected_outers):
            values = [item[outer] for item in items.values()]
            known = [v for v in values if v is not None]
            mean = strict_mean(values)
            block_means[outer] = mean
            blocks.append({**descriptor, "outerseed": outer,
                           "requested_seed_block_label": 2200 + 4 * int(outer.removeprefix("outer_"))
                           if descriptor["scenario"] == "tuning" else None,
                           "unit": row_unit, "n_items": len(items), "n_rows": len(values),
                           "n_original_logical_rows": len(values) * components,
                           "n_known_rows": len(known), "n_missing_rows": len(values) - len(known),
                           "mean": mean, "known_subset_mean_not_complete_endpoint": statistics.mean(known) if known else None,
                           "status": "complete" if mean is not None else "unknown_incomplete_endpoint"})
        complete = all(v is not None for v in block_means.values())
        aggregates.append({**descriptor, "unit": row_unit, "n_items": len(items),
                           "n_repeats": expected_repeats, "n_rows": len(group),
                           "n_original_logical_rows": len(group) * components,
                           "n_known_rows": sum(r["value"] is not None for r in group),
                           "n_missing_rows": sum(r["value"] is None for r in group),
                           "n_complete_items": sum(v is not None for v in item_means),
                           "mean": strict_mean(item_means),
                           "known_subset_mean_not_complete_endpoint": statistics.mean(known_items) if known_items else None,
                           "seedblock_descriptive_sd": statistics.stdev(block_means.values()) if complete and expected_repeats > 1 else None,
                           "outerseed_means": json.dumps(block_means, sort_keys=True, separators=(",", ":")),
                           "status": "complete" if complete else "unknown_incomplete_endpoint"})
    return aggregates, blocks


def compare_effects(aggregates, effects):
    index = {tuple(r[k] for k in KEY): r for r in aggregates}
    checked, nulls, max_difference, max_relative = 0, 0, 0.0, 0.0
    quality_checks, resource_checks = 0, 0
    for effect in effects:
        prefix = tuple(effect[k] for k in KEY[:4])
        baseline = index[prefix + (("cost_free", "single") if effect["system"] == "expgym"
                                   else (effect["regime"], "naive")) + (effect["metric"],)]
        target = index[prefix + (("cost_tight", "single") if effect["system"] == "expgym"
                                 else (effect["regime"], effect["strategy"])) + (effect["metric"],)]
        require(baseline["n_items"] == target["n_items"] == int(effect["n_items"]), "effect item denominator mismatch")
        require(baseline["n_repeats"] == target["n_repeats"] == int(effect["n_outer_repeats"]), "effect repeat denominator mismatch")
        require(baseline["n_rows"] == target["n_rows"] == int(effect["n_pairs_descriptive_not_independent_n"]), "effect pair denominator mismatch")
        for field, derived in (("baseline", baseline["mean"]), ("target", target["mean"])):
            original = parse_number(effect[field])
            if original is None or derived is None:
                require(original is derived is None, "effect null mismatch")
                nulls += 1
            else:
                difference = abs(original - derived)
                quality = effect["metric"] in QUALITY
                require(math.isclose(original, derived, rel_tol=0.0 if quality else 1e-12, abs_tol=1e-12),
                        "effect mean differs: %s/%s" % (effect["comparison"], field))
                max_difference = max(max_difference, difference)
                max_relative = max(max_relative, difference / max(abs(original), abs(derived))
                                   if original or derived else 0.0)
                quality_checks += int(quality)
                resource_checks += int(not quality)
                checked += 1
    return {"comparisons_checked": len(effects), "baseline_target_numeric_checks": checked,
            "baseline_target_null_checks": nulls, "quality_numeric_checks": quality_checks,
            "resource_numeric_checks": resource_checks, "quality_absolute_tolerance": 1e-12,
            "resource_tolerance": {"relative": 1e-12, "absolute": 1e-12},
            "maximum_absolute_difference": max_difference, "maximum_relative_difference": max_relative,
            "all_passed": True}


def csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(str(v) for v in row) + " |" for row in rows])


def render_tables(rows, blocks):
    index = {tuple(r[k] for k in KEY): r for r in rows}
    block_index = {tuple(r[k] for k in KEY) + (r["outerseed"],): r for r in blocks}
    def value(model, system, scenario, subset, regime, strategy, metric):
        row = index[(model, system, scenario, subset, regime, strategy, metric)]
        return "unknown" if row["mean"] is None else format(row["mean"], ".6f")
    models = ("kimi-k3", "glm-5.3")
    regimes = {"cost_free": "Free", "cost_moderate": "Moderate", "cost_tight": "Tight"}
    text = ["# 全设置绝对指标表（自动生成）", "",
            "输入固定为提交 `" + COMMIT + "` 的两模型最终导出。只聚合冻结 CSV，不调用模型、投票器或 scorer。", "",
            "先在每 item 内等权平均 outer repeats，再跨 item 等权。Exp Audit 已在原导出内将三个固定 orders 文档内等权平均；N4 pool 是一个单元。", "",
            "分数保留原单位：F1/EA/LA/raw 为 0–1，Gap 为 points（本库定义越高越好，可超过 100）。表显示六位小数；全部原精度均值、完整分母、unknown 和 seedblock 描述 SD 见 [aggregate_metrics.csv](aggregate_metrics.csv)，三个 HPO seed blocks 的所有 task/setting 见 [by_outerseed.csv](by_outerseed.csv)。R1 SD 是 null，不是零；没有 CI/p 或总体推广。", "",
            "## ExpGym：Search / Audit", ""]
    lines = []
    for scenario, subsets, metrics in [("restricted_search", ["all", "whois", "whatis"], ["f1"]),
                                       ("evidence_audit", ["all"], ["evidence_acc", "label_acc"])]:
        for subset in subsets:
            for regime in REGIMES:
                for metric in metrics:
                    sample = index[(models[0], "expgym", scenario, subset, regime, "single", metric)]
                    lines.append([scenario, subset, regimes[regime], metric, sample["n_items"],
                                  *[value(m, "expgym", scenario, subset, regime, "single", metric) for m in models]])
    text += [table(["场景", "切片", "预算", "指标", "items / R1", "Kimi-K3", "GLM-5.3"], lines), "",
             "## ExpGym：HPO 全体、家族及逐任务（R3）", ""]
    subsets = sorted({r["slice"] for r in rows if r["system"] == "expgym" and r["scenario"] == "tuning"})
    lines = []
    for subset in subsets:
        for regime in REGIMES:
            sample = index[(models[0], "expgym", "tuning", subset, regime, "single", "gap")]
            lines.append([subset, regimes[regime], sample["n_items"],
                          *[value(m, "expgym", "tuning", subset, regime, "single", metric)
                            for m in models for metric in ("gap", "raw_perf")]])
    text += [table(["切片", "预算", "items（每项 R=3）", "K3 Gap", "K3 raw", "GLM Gap", "GLM raw"], lines), "",
             "## PoolAct：Search whois / Audit（N4，R1）", "",
             "Search 仅39 whois，故 all=whois；无 Pool whatis 设置。Audit 为原 default order；MI 为四 agent 指标均值，MV 为冻结投票输出指标。", ""]
    metrics = [("restricted_search", "f1_mi"), ("restricted_search", "f1_mv"),
               ("evidence_audit", "evidence_acc_mi"), ("evidence_audit", "evidence_acc_mv"),
               ("evidence_audit", "label_acc_mi"), ("evidence_audit", "label_acc_mv")]
    lines = [[m, regimes[regime], strategy,
              *[value(m, "poolact", scenario, "all", regime, strategy, metric) for scenario, metric in metrics]]
             for m in models for regime in REGIMES[1:] for strategy in ("naive", "cached", "poolact")]
    text += [table(["模型", "预算", "策略", "F1 MI", "F1 MV", "EA MI", "EA MV", "LA MI", "LA MV"], lines), "",
             "## PoolAct：NAS101 A/B/C（N4，R3）", "",
             "all 即 NAS101 三任务等权；不含 ParamNet/NAS201。BoN 与 MI 均原样保留，不能只看最高值。", ""]
    subsets = ["all", *sorted(s for s in {r["slice"] for r in rows if r["system"] == "poolact" and r["scenario"] == "tuning"} if s.startswith("task="))]
    lines = [[m, subset, regimes[regime], strategy,
              *[value(m, "poolact", "tuning", subset, regime, strategy, metric)
                for metric in ("gap_mi", "gap_bon", "raw_perf_mi", "raw_perf_bon")]]
             for m in models for subset in subsets for regime in REGIMES[1:] for strategy in ("naive", "cached", "poolact")]
    text += [table(["模型", "切片", "预算", "策略", "Gap MI", "Gap BoN", "raw MI", "raw BoN"], lines), "",
             "## R3 seed blocks", "",
             "直接展示上述全体任务的三个等权 seedblock 均值：Exp HPO 为九任务，Pool NAS 为三任务。outer0/1/2 对应请求 base seed 标签2200/2204/2208；不是已验证的独立随机重复。SD 是这三个均值的样本描述 SD，不是标准误、置信区间或显著性。完整逐 task 数据仍见 by_outerseed.csv。", ""]
    lines = []
    for m in models:
        for system in ("expgym", "poolact"):
            for regime in REGIMES if system == "expgym" else REGIMES[1:]:
                for strategy in ("single",) if system == "expgym" else ("naive", "cached", "poolact"):
                    for metric in ("gap",) if system == "expgym" else ("gap_mi", "gap_bon"):
                        key = (m, system, "tuning", "all", regime, strategy, metric)
                        values = [block_index[key + ("outer_%05d" % outer,)]["mean"] for outer in range(3)]
                        values.append(index[key]["seedblock_descriptive_sd"])
                        lines.append([m, system, regimes[regime], strategy, metric,
                                      *["unknown" if v is None else format(v, ".6f") for v in values]])
    text += [table(["模型", "系统", "预算", "策略", "指标", "outer0", "outer1", "outer2", "描述 SD"], lines), "",
             "## 场景级资源均值", "",
             "以下均取同一分析单元的冻结遥测，再按 item/repeat 等权；不是整项 study 总账。Input/Output 为 token；reasoning 已包含于 Output，不能再相加。反馈秒是模拟工具反馈成本，不是 GPU 秒。Exp Audit 列为每文档三个 orders 的均值，不是三 orders 合计。", "",
             "Pool input/output tokens、feedback成本/次数为四 agents 合计；Pool wall 是整个 pool 子进程实际 source_capture.elapsed_seconds，不是 agent wall 的 sum/max。Exp wall 为单 agent 实测（Audit再平均三个orders）。不能相加推导整个并行 study 实际耗时或 GPU-hour；总账另见主报告。每个 Pool 的 feedback_visible 原导出缺失，在 CSV 保留 unknown，未补零；本表展示可用的反馈尝试数。", "",
             "Free 的反馈预算为无限且不展示成本，不意味着实际反馈成本为零。budget_utilization 保留在 CSV，有限预算下 Pool 为四 agents 总反馈成本/(4×单 agent 预算)；允许最后一次工具越界带来大于1的值。", ""]
    lines = []
    for m in models:
        for system in ("expgym", "poolact"):
            for scenario in ("restricted_search", "evidence_audit", "tuning"):
                for regime in REGIMES if system == "expgym" else REGIMES[1:]:
                    for strategy in ("single",) if system == "expgym" else ("naive", "cached", "poolact"):
                        lines.append([m, system, scenario, regimes[regime], strategy,
                                      *[value(m, system, scenario, "all", regime, strategy, metric)
                                        for metric in ("input_tokens", "output_tokens", "feedback_cost_seconds", "wall_time_seconds", "feedback_attempts")]])
    text += [table(["模型", "系统", "场景", "预算", "策略", "Input tokens", "Output tokens", "反馈秒", "冻结 wall 秒", "反馈尝试数"], lines), "",
             "## 复算", "",
             "```bash", "python3.11 results/portable-eval-20260908/full_matrix_report_v1/aggregate_settings.py --output-dir /absolute/new-output-directory", "```", "",
             "脚本仅读取两份 final export 的 EXPORT_INDEX/manifest/metrics/effects 共8文件，核固定哈希；输出5个文件，已有文件拒绝覆盖。`--check` 只读比较当前5文件与重算字节。原 effects 的全部 baseline/target 与新绝对均值逐一核对：质量指标绝对容差 1e-12；资源指标相对/绝对容差均1e-12，以容纳大数两层浮点平均的末位舍入。null 也按原样匹配；该核对不是新独立评分或统计假设检验。", ""]
    return "\n".join(text).encode()


def build(repo_root):
    rows, effects, metadata, inputs, checks = read_sources(repo_root)
    aggregates, blocks = aggregate(rows, metadata)
    effect_checks = compare_effects(aggregates, effects)
    quality_groups = [r for r in aggregates if r["metric"] in QUALITY]
    result_checks = {"schema": "full-matrix-absolute-aggregation-checks-v1", "source_commit": COMMIT,
                     "model_checks": checks, "aggregate_rows": len(aggregates), "seedblock_rows": len(blocks),
                     "quality_aggregate_rows": len(quality_groups),
                     "unknown_aggregate_rows": sum(r["mean"] is None for r in aggregates),
                     "quality_unknown_aggregate_rows": sum(r["mean"] is None for r in quality_groups),
                     "frozen_effect_alignment": effect_checks,
                     "unit_weighting": "mean_within_item_then_equal_item_mean; strict_null_complete_endpoint",
                     "sd": "sample_SD_of_equal_item_outerseed_means_if_R_greater_than_1_and_all_known",
                     "R1_SD": None, "CI": None, "p_values": None,
                     "raw_score_recomputation": False, "model_calls": 0,
                     "not_confirmatory_or_population_inference": True,
                     "free_budget_utilization": "not_defined_in_original_catalogue; not inserted as a measured metric"}
    encode = lambda value: (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    return {"aggregate_metrics.csv": csv_bytes(aggregates, AGG_FIELDS),
            "by_outerseed.csv": csv_bytes(blocks, BLOCK_FIELDS),
            "aggregate_checks.json": encode(result_checks), "INPUTS.json": encode(inputs),
            "TABLES.md": render_tables(aggregates, blocks)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=HERE.parents[2])
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--check", action="store_true", help="compare existing generated files without writing")
    args = parser.parse_args()
    outputs = build(args.repo_root)
    if args.check:
        for name, raw in outputs.items():
            require((args.output_dir / name).read_bytes() == raw, "recomputed output differs: " + name)
    else:
        require(not any((args.output_dir / name).exists() for name in outputs), "output exists; choose a fresh directory")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, raw in outputs.items():
            with (args.output_dir / name).open("xb") as stream:
                stream.write(raw)
    print(json.dumps({"passed": True, "check_only": args.check,
                      "outputs": {name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in outputs.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
