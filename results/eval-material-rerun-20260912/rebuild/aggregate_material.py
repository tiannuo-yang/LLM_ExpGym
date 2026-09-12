#!/usr/bin/env python3
"""Explicit-input descriptive adapter for a targeted PoolAct rerun.

No runner/scorer imports, model/network calls, globbing, automatic recovery or
complete-case selection. See INPUT_SCHEMA.md. This is not a score auditor.
"""
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

STRATEGIES = ("naive", "cached", "poolact")
METRICS = {
    "restricted_search": ("f1_mi", "f1_mv"),
    "evidence_audit": ("evidence_acc_mi", "evidence_acc_mv", "label_acc_mi", "label_acc_mv"),
    "tuning": ("raw_perf_mi", "raw_perf_bon", "gap_mi", "gap_bon", "gap0_mi", "gap0_bon"),
}
PRIMARY = {"restricted_search": "f1_mv", "evidence_audit": "evidence_acc_mv", "tuning": "gap_mi"}
LABELS = {"restricted_search": "Search whois", "evidence_audit": "Audit", "tuning": "NAS101"}
BASE = ("model", "scenario", "regime", "strategy", "metric")
HISTORICAL = "https://github.com/tiannuo-yang/LLM_ExpGym/blob/6c63f1c03c88683fa55be5cafcbb8122ac8fadaa/results/five-model-ranking-20260911/"
HISTORICAL_MODELS = ("kimi-k3", "glm-5.3", "qwen3.8-2.4t-a95b-fp8", "deepseek-v4-flash-0731", "gpt-5.6-sol")
HISTORICAL_LABELS = dict(zip(HISTORICAL_MODELS, ("Kimi", "GLM", "Qwen", "DeepSeek", "GPT (medium)")))
HISTORICAL_FAMILIES = ("Search whois", "Search whatis", "Audit", "ParamNet", "NAS101", "NAS201")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def jb(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def number(value):
    if value is None or value == "":
        return None
    require(not isinstance(value, bool), "boolean is not a score")
    value = float(value)
    require(math.isfinite(value), "nonfinite number")
    return value


def full_mean(values):
    return statistics.mean(values) if values and all(x is not None for x in values) else None


def close(a, b):
    return a is b if a is None or b is None else math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)


def csv_bytes(rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    require(fields, "empty output table")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


class Inputs:
    """Every supplied entry is path+size+SHA pinned before analysis starts."""
    def __init__(self, base, artifact_root=None):
        self.base = Path(base)
        self.artifact_root = Path(artifact_root) if artifact_root is not None else None
        self.files = {}
        self.read_paths = {}

    def read(self, entry, role):
        label = str(entry["path"])
        if label.startswith("@study/"):
            require(self.artifact_root is not None, "@study input requires --artifact-root")
            relative = Path(label[len("@study/"):])
            require(not relative.is_absolute() and ".." not in relative.parts, "invalid artifact-relative path")
            path = self.artifact_root / relative
        else:
            path = Path(label)
        if not path.is_absolute() and not label.startswith("@study/"):
            path = self.base / path
        require(not path.is_symlink() and path.is_file(), "expected regular input: " + str(path))
        raw = path.read_bytes()
        require(len(raw) == entry["bytes"] and sha(raw) == entry["sha256"], "input identity mismatch: " + str(path))
        current = dict(path=label, bytes=len(raw), sha256=sha(raw), role=role)
        if label in self.files:
            require(self.files[label]["sha256"] == current["sha256"], "input changed during read")
        else:
            self.files[label] = current
            self.read_paths[label] = path.resolve()
        return raw

    def json(self, entry, role):
        return json.loads(self.read(entry, role))

    def recheck(self):
        for entry in self.files.values():
            raw = self.read_paths[entry["path"]].read_bytes()
            require((len(raw), sha(raw)) == (entry["bytes"], entry["sha256"]), "input changed during aggregation")


def plan_rows(plan):
    require(plan["schema"] == "expgym.study-queue-plan.v1", "unsupported queue plan")
    rows = []
    for job in plan["jobs"]:
        args = job["args"]
        require(job["runner"] == "poolact" and len(args["strategies"]) == 1, "expected single-pool job")
        scenario = args["scenario"]
        require(scenario in METRICS and args["strategies"][0] in STRATEGIES, "unsupported setting")
        require(args["agents"] == 4 and args["missing_final_policy"] == "task-abstention-v1", "unsupported policy/N")
        require(args["repeats"] == 1, "expanded jobs must contain one pool")
        item = args["tuning_task"] if scenario == "tuning" else (
            str(args["cc_split"] if scenario == "evidence_audit" else args["data_source"]) + ":" + str(args["question_index"]))
        rows.append(dict(job_id=job["job_id"], model=args["model"], scenario=scenario, item=item,
                         regime=args["cost_regime"], strategy=args["strategies"][0], seed=str(args["seed"]),
                         N=args["agents"], source_tree_sha256=plan["source_tree_sha256"],
                         plan_study_id=plan["study_id"], args=args, job=job))
    return rows


def validate_matrix(rows, expected_jobs=None, expected_cells=None):
    require(rows and (expected_jobs is None or len(rows) == expected_jobs), "planned pool count differs")
    require(len({r["job_id"] for r in rows}) == len(rows), "duplicate planned job")
    seen, settings, signatures = set(), defaultdict(lambda: defaultdict(set)), defaultdict(set)
    for row in rows:
        identity = tuple(row[k] for k in ("model", "scenario", "regime", "strategy", "item", "seed"))
        require(identity not in seen, "duplicate logical pool identity")
        seen.add(identity)
        cell = tuple(row[k] for k in ("model", "scenario", "regime"))
        settings[cell][row["strategy"]].add((row["item"], row["seed"]))
        signature_key = cell + (row["item"], row["seed"])
        signatures[signature_key].add(sha(jb([row["source_tree_sha256"], scientific_args(row["args"], comparison=True)])))
    require(expected_cells is None or len(settings) == expected_cells, "planned cell count differs")
    for cell, arms in settings.items():
        require(set(arms) == set(STRATEGIES), "missing planned comparison arm")
        require(all(arms[s] == arms["naive"] for s in STRATEGIES), "unpaired task/repeat design")
        by_item = defaultdict(set)
        for item, seed in arms["naive"]:
            by_item[item].add(seed)
        require(len({tuple(sorted(seeds)) for seeds in by_item.values()}) == 1, "unequal item repetition blocks")
    require(all(len(values) == 1 for values in signatures.values()), "comparison arms differ in model/scientific args")
    return settings


def scientific_args(args, comparison=False):
    omitted = {"output_dir", "base_url", "prompt_cache_key", "terminal_evidence_dir", "api_key_file"}
    if comparison:
        omitted.add("strategies")
    return {k: v for k, v in args.items() if k not in omitted}


def gap(perf, task, oracle):
    """Frozen API exporter contract: agent first, lower clip only, no 100 cap."""
    if perf is None:
        return None
    ref = oracle["tasks"][task]
    center, best = number(ref["mean_perf"]), number(ref["best_perf"])
    require(best > center, "oracle gap denominator must be positive")
    return max(0.0, 100.0 * (perf - center) / (best - center))


def endpoints(result, row, oracle):
    """Arithmetic on saved scalar scores; does NOT reevaluate/vote answers."""
    agents, aggregate, n = result["agent_results"], result["aggregate"], row["N"]
    require(result["agents"] == n and len(agents) == n, "wrong pool agent count")
    require([a["agent_id"] for a in agents] == list(range(n)), "wrong agent IDs/order")
    require(result["strategy"] == row["strategy"], "wrong result strategy")
    require(result["terminal_status"] == aggregate["terminal_status"], "aggregate terminal mismatch")
    terminal = result["terminal_status"]
    require(terminal["execution_complete"] is True and terminal["policy_version"] == "task-abstention-v1", "incomplete result")
    missing, known = 0, 0
    for agent in agents:
        status = agent["terminal_status"]
        require(status["execution_complete"] is True and status["policy_version"] == "task-abstention-v1", "agent execution failure")
        if agent["answer"] is None:
            missing += 1
        if status["score_complete"] is True:
            require(number(agent["answer_perf"]) is not None, "scored agent has no scalar")
            known += 1
        else:
            require(row["scenario"] == "tuning" and agent["answer"] is None and agent["answer_perf"] is None
                    and agent["answer_metrics"] is None and agent.get("scoring_input") is None
                    and agent.get("score_status") == "unscorable_missing_configuration"
                    and agent.get("terminal_origin") == "normal_loop_return"
                    and status["terminal_classification"] == "model_no_answer", "failure cannot become Gap0")
    require(terminal["model_no_answer_count"] == missing, "missing-answer count disagrees")
    require(terminal["expected_model_terminals"] == n and terminal["reported_model_terminals"] == n, "terminal denominator differs")
    values = {}
    if row["scenario"] == "tuning":
        raw = [number(a["answer_perf"]) for a in agents]
        gaps = [gap(v, row["item"], oracle) for v in raw]
        complete = known == n
        require(terminal["score_complete"] is complete, "strict NAS completion differs")
        values.update(raw_perf_mi=full_mean(raw), raw_perf_bon=max(raw) if complete else None,
                      gap_mi=full_mean(gaps), gap_bon=max(gaps) if complete else None,
                      gap0_mi=statistics.mean(0.0 if x is None else x for x in gaps),
                      gap0_bon=max(0.0 if x is None else x for x in gaps))
        require(close(number(aggregate["answer_perf"]), values["raw_perf_bon"]), "saved strict NAS BoN mismatch")
        require(close(number(aggregate["mean_individual_perf"]), values["raw_perf_mi"]), "saved strict NAS MI mismatch")
    elif row["scenario"] == "restricted_search":
        require(known == n and terminal["score_complete"] is True, "Search empty-pred scores must remain known")
        values.update(f1_mi=full_mean([number(a["answer_perf"]) for a in agents]),
                      f1_mv=number(aggregate["answer_perf"]))
    else:
        require(known == n and terminal["score_complete"] is True, "Audit empty-pred scores must remain known")
        for metric in ("evidence_acc", "label_acc"):
            values[metric + "_mi"] = full_mean([number(a["answer_metrics"][metric]) for a in agents])
            values[metric + "_mv"] = number(aggregate["answer_metrics"][metric])
    for metric, value in values.items():
        if value is not None:
            require(value >= 0 and (metric.startswith("gap") or value <= 1), "score range violation")
    return values, dict(expected_agents=n, scored_agents=known, missing_answer_agents=missing,
                        missing_configuration_agents=n-known if row["scenario"] == "tuning" else 0)


def grouped_metrics(rows, by_seed=False, by_item=False):
    groups = defaultdict(list)
    axes = BASE + (("seed",) if by_seed else ()) + (("item",) if by_item else ())
    for row in rows:
        groups[tuple(row[k] for k in axes)].append(row)
    output = []
    for key, records in sorted(groups.items()):
        by_task = defaultdict(list)
        for r in records:
            by_task[r["item"]].append(r["value"])
        complete_items = [full_mean(v) for v in by_task.values()]
        known_items = [statistics.mean([x for x in v if x is not None]) for v in by_task.values() if any(x is not None for x in v)]
        repeats = {len(v) for v in by_task.values()}
        require(len(repeats) == 1, "unequal expected repeats during aggregation")
        n_known = sum(r["value"] is not None for r in records)
        out = dict(zip(axes, key))
        out.update(unit=records[0]["unit"], expected_pools=len(records), known_pools=n_known,
                   missing_pools=len(records)-n_known, expected_items=len(by_task),
                   complete_items=sum(v is not None for v in complete_items), repeats_per_item=next(iter(repeats)),
                   full_mean=full_mean(complete_items), known_subset_item_weighted_mean=statistics.mean(known_items) if known_items else None)
        output.append(out)
    return output


def comparisons(rows):
    groups = defaultdict(dict)
    keys = ("model", "scenario", "regime", "item", "seed", "metric")
    for row in rows:
        group = groups[tuple(row[k] for k in keys)]
        require(row["strategy"] not in group, "duplicate strategy metric")
        group[row["strategy"]] = row
    paired = []
    for key, arms in sorted(groups.items()):
        require(set(arms) == set(STRATEGIES), "comparison cannot silently intersect arms")
        for baseline, target in (("naive", "cached"), ("cached", "poolact"), ("naive", "poolact")):
            a, b = arms[baseline]["value"], arms[target]["value"]
            paired.append(dict(zip(keys, key), baseline=baseline, target=target, unit=arms[baseline]["unit"],
                               baseline_value=a, target_value=b, value=b-a if a is not None and b is not None else None,
                               strategy=target+"_minus_"+baseline,
                               baseline_job_id=arms[baseline]["job_id"], target_job_id=arms[target]["job_id"]))
    aggregates = grouped_metrics(paired)
    for row in aggregates:
        row["target"], row["baseline"] = row["strategy"].split("_minus_")
        row["effect_definition"] = "target_minus_baseline"
    return paired, aggregates


def fmt(value, metric="", signed=False):
    if value is None:
        return "unknown"
    scale = 100 if metric.startswith(("f1", "evidence_acc", "label_acc", "raw_perf")) else 1
    return format(value * scale, "+.2f" if signed else ".2f")


def table(headers, rows):
    def line(values):
        return "| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in values) + " |\n"
    return line(headers) + line(["---"] * len(headers)) + "".join(line(r) for r in rows)


def main_table(aggregates, metrics):
    index = {tuple(r[k] for k in BASE): r for r in aggregates}
    cells = sorted({tuple(r[k] for k in ("model", "scenario", "regime")) for r in aggregates})
    rows = []
    for model, scenario, regime in cells:
        metric = metrics.get(scenario)
        if metric is None:
            continue
        values = [index[(model, scenario, regime, s, metric)]["full_mean"] for s in STRATEGIES]
        differences = [values[t]-values[b] if values[t] is not None and values[b] is not None else None for b,t in ((0,1),(1,2),(0,2))]
        rows.append([model, LABELS[scenario], regime.removeprefix("cost_"), metric] + [fmt(v, metric) for v in values] + [fmt(v, metric, True) for v in differences])
    return table(["模型", "场景", "预算", "指标", "naive", "cached", "PoolAct", "cached−naive", "PoolAct−cached", "PoolAct−naive"], rows)


def overall_primary_summary(aggregates):
    cells = defaultdict(dict)
    for row in aggregates:
        if row["metric"] == PRIMARY[row["scenario"]]:
            cells[(row["model"], row["scenario"], row["regime"])][row["strategy"]] = row["full_mean"]
    counts = {control: Counter() for control in ("naive", "cached")}
    tight_total = tight_both_up = tight_unknown = 0
    for key, arms in cells.items():
        require(set(arms) == set(STRATEGIES), "overall primary summary lacks a registered arm")
        for control in counts:
            before, after = arms[control], arms["poolact"]
            state = "unknown" if before is None or after is None else "up" if after > before else "down" if after < before else "tie"
            counts[control][state] += 1
        if key[2] == "cost_tight":
            tight_total += 1
            if any(value is None for value in arms.values()):
                tight_unknown += 1
            elif arms["poolact"] > arms["naive"] and arms["poolact"] > arms["cached"]:
                tight_both_up += 1
    total = len(cells)
    text = f"在全部 {total} 个登记主端点单元中，PoolAct 高于 naive {counts['naive']['up']}/{total}，高于 cached {counts['cached']['up']}/{total}"
    text += (f"（两项比较的未知单元分别为 {counts['naive']['unknown']}、{counts['cached']['unknown']}，仍计入总分母；"
             f"并列分别为 {counts['naive']['tie']}、{counts['cached']['tie']}）。")
    if tight_total:
        text += f"Tight 单元中 {tight_both_up}/{tight_total} 高于两臂，未知 {tight_unknown}。"
    return text + "这是登记设置上的描述性计数，不是显著性检验或模型总体的普遍结论。\n\n"


def nas_gap0_matches_strict(aggregates, statuses):
    nas_statuses = [r for r in statuses if r["scenario"] == "tuning"]
    if not nas_statuses or any(r["execution_status"] != "completed" or r["scored_agents"] != r["N"] for r in nas_statuses):
        return False
    index = {tuple(r[k] for k in BASE): r["full_mean"] for r in aggregates}
    for row in aggregates:
        if row["scenario"] == "tuning" and row["metric"] in ("gap_mi", "gap_bon"):
            counterpart = tuple(row[k] if k != "metric" else row[k].replace("gap_", "gap0_", 1) for k in BASE)
            if row["full_mean"] is None or not close(row["full_mean"], index[counterpart]):
                return False
    return True


def result_summary(historical, statuses=()):
    """Describe ALL registered cells; never select executions or change endpoints.

    Historical NAS exceptions were stated using Gap0; their before/after summary
    must use the same explicitly labelled sensitivity, not a strict-known subset.
    """
    cells = defaultdict(dict)
    for row in historical:
        chosen = "gap0_mi" if row["scenario"] == "tuning" else PRIMARY[row["scenario"]]
        if row["metric"] == chosen:
            cells[(row["model"], row["scenario"], row["regime"], chosen)][row["strategy"]] = row
    classified, transitions = defaultdict(Counter), []
    statuses_by_cell, negative_without_missing = defaultdict(list), []
    for status in statuses:
        statuses_by_cell[(status["model"], status["scenario"], status["regime"])].append(status)
    for key, arms in sorted(cells.items()):
        require(set(arms) == set(STRATEGIES), "historical summary requires all arms")
        old = [arms[s]["historical_value"] for s in STRATEGIES]
        new = [arms[s]["rerun_value"] for s in STRATEGIES]
        if any(v is None for v in old):
            old_group = "旧端点未知"
        else:
            old_group = "旧负差" if old[2] < old[0] or old[2] < old[1] else "旧非负对照"
        if any(v is None for v in new):
            direction = "本轮未知"
        elif new[2] < new[0] or new[2] < new[1]:
            direction = "低于至少一臂"
        elif new[2] > new[0] and new[2] > new[1]:
            direction = "高于两臂"
        else:
            direction = "不低于两臂但有并列"
        classified[old_group][direction] += 1
        slot_statuses = statuses_by_cell.get(key[:3], [])
        if direction == "低于至少一臂" and slot_statuses and all(
                r["execution_status"] == "completed" and r["missing_answer_agents"] == 0 for r in slot_statuses):
            negative_without_missing.append(HISTORICAL_LABELS.get(key[0], key[0])+" / "+LABELS[key[1]]+" / "+key[2].removeprefix("cost_"))
        metric = key[3]
        delta = lambda vals, baseline: vals[2]-vals[baseline] if vals[2] is not None and vals[baseline] is not None else None
        transitions.append([key[0], LABELS[key[1]], key[2].removeprefix("cost_"), metric,
                            fmt(delta(old, 0), metric, True), fmt(delta(new, 0), metric, True),
                            fmt(delta(old, 1), metric, True), fmt(delta(new, 1), metric, True)])
    statements = []
    for name in ("旧负差", "旧非负对照", "旧端点未知"):
        counts = classified.get(name)
        if counts:
            statements.append(f"{name}共 {sum(counts.values())} 个单元：" + "，".join(f"{label} {counts[label]} 个" for label in (
                "高于两臂", "不低于两臂但有并列", "低于至少一臂", "本轮未知") if counts[label]) + "。")
    if negative_without_missing:
        statements.append("残余负差单元（"+"；".join(negative_without_missing)+
                          "）的三臂均无缺最终回答，故这些负差不能归因于本轮缺答；这不排除 legacy 等其他评价边界。")
    return ("\n### 旧反例与正对照的变化\n\n"
            "以下按同一端点比较修前/后；NAS 此小节特指旧主报告使用的 Gap0-MI 敏感性，不能替代上方原严格端点。"
            "‘旧负差’指历史 PoolAct 低于 naive 或 cached 中至少一个；所有登记单元均进入计数，不按本轮表现选样。\n\n" +
            " ".join(statements) + "\n\n" + table(["模型", "场景", "预算", "指标", "旧 P−naive", "新 P−naive", "旧 P−cached", "新 P−cached"], transitions))


def historical_budget_data(raw):
    """Read the published summary scores, already in display units; no rescore."""
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    expected = {(scenario, model) for scenario in ("Search", "Audit", "HPO/NAS") for model in HISTORICAL_MODELS}
    require(len(rows) == len(expected) and {(r["scenario"], r["model"]) for r in rows} == expected,
            "historical budget summary is not the fixed five-model/three-scenario matrix")
    metric_by_scenario = {"Search": "f1", "Audit": "evidence_acc", "HPO/NAS": "gap0"}
    for row in rows:
        require(row["metric"] == metric_by_scenario[row["scenario"]], "historical single endpoint changed")
        expected_unit = "Gap0点" if row["metric"] == "gap0" else "分 (0–100)"
        require(row["unit"] == expected_unit, "historical display unit changed")
        for field in ("free", "moderate", "tight", "free_minus_tight"):
            row[field] = number(row[field])
        for field in ("free", "moderate", "tight"):
            value = row[field]
            require(value is None or value >= 0 and (row["metric"] == "gap0" or value <= 100), "historical score range changed")
        expected_delta = row["free"]-row["tight"] if row["free"] is not None and row["tight"] is not None else None
        require(close(row["free_minus_tight"], expected_delta), "historical Free-minus-Tight differs")
    return rows


def historical_budget_display(rows):
    index = {(r["scenario"], r["model"]): r for r in rows}
    display = []
    for model in HISTORICAL_MODELS:
        values = [HISTORICAL_LABELS[model]]
        for scenario in ("Search", "Audit", "HPO/NAS"):
            row = index[(scenario, model)]
            values.extend((fmt(row["free"])+" → "+fmt(row["tight"]), fmt(row["free_minus_tight"], signed=True)))
        display.append(values)
    observations = []
    improvements = []
    for scenario in ("Search", "Audit", "HPO/NAS"):
        selected = [r for r in rows if r["scenario"] == scenario]
        declines = sum(r["free_minus_tight"] is not None and r["free_minus_tight"] > 0 for r in selected)
        observations.append(f"{scenario} 有 {declines}/{len(selected)} 个模型从 Free 到 Tight 下降")
        improvements.extend(f"{HISTORICAL_LABELS[r['model']]} 的 {scenario} 反而改善 {fmt(-r['free_minus_tight'])} 点"
                            for r in selected if r["free_minus_tight"] is not None and r["free_minus_tight"] < 0)
    narrative = "冻结旧数据中，" + "，".join(observations) + "。"
    if improvements:
        narrative += "；".join(improvements) + "，因此不能概括为所有模型和端点必然退化。"
    return table(["模型", "Search F1：Free→Tight", "F−T", "Audit EA：Free→Tight", "F−T", "HPO/NAS Gap0：Free→Tight", "F−T"], display) + "\n" + narrative + "\n\n"


def historical_ranking_data(raw):
    """Consume frozen winner sets; do not insert any new PoolAct scores."""
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    regimes = ("cost_free", "cost_moderate", "cost_tight")
    expected = {(family, model, regime) for family in HISTORICAL_FAMILIES for model in HISTORICAL_MODELS for regime in regimes}
    require(len(rows) == len(expected) and {(r["family"], r["model"], r["regime"]) for r in rows} == expected,
            "historical ranking summary is not the fixed six-family/five-model matrix")
    groups = defaultdict(list)
    for row in rows:
        require(row["winner"] in ("True", "False") and row["free_to_tight_winner_changed"] in ("True", "False"),
                "invalid historical ranking flag")
        require(int(row["candidate_count"]) == len(HISTORICAL_MODELS), "historical ranking candidate set changed")
        row["value"] = number(row["value"])
        row["winner"] = row["winner"] == "True"
        expected_metric = "f1" if row["family"].startswith("Search") else "evidence_acc" if row["family"] == "Audit" else "gap0"
        require(row["metric"] == expected_metric, "historical ranking endpoint changed")
        require(row["unit"] == ("Gap0点" if expected_metric == "gap0" else "分 (0–100)"), "historical ranking unit changed")
        require(row["value"] is not None and row["value"] >= 0 and (expected_metric == "gap0" or row["value"] <= 100),
                "frozen historical ranking unexpectedly incomplete or out of range")
        groups[(row["family"], row["regime"])].append(row)
    winners = {}
    for key, selected in groups.items():
        recorded = {r["winner_set"] for r in selected}
        require(len(recorded) == 1, "historical winner sets disagree within family/budget")
        winner_models = set(next(iter(recorded)).split(";"))
        require(winner_models and winner_models == {r["model"] for r in selected if r["winner"]}, "historical winner flag/set mismatch")
        # Match the old summary's tie tolerance after its display-unit scaling.
        tolerance = 1e-12 if selected[0]["metric"] == "gap0" else 1e-10
        top = max(r["value"] for r in selected)
        require(winner_models == {r["model"] for r in selected if top-r["value"] <= tolerance}, "historical winner set disagrees with saved scores")
        winners[key] = [r for r in selected if r["winner"]]
    for family in HISTORICAL_FAMILIES:
        free = {r["model"] for r in winners[(family, "cost_free")]}
        tight = {r["model"] for r in winners[(family, "cost_tight")]}
        require(all((r["free_to_tight_winner_changed"] == "True") == (free != tight) for r in rows if r["family"] == family),
                "historical winner-transition flag mismatch")
    return rows, winners


def historical_ranking_display(winners):
    display, changes = [], 0
    for family in HISTORICAL_FAMILIES:
        free, tight = winners[(family, "cost_free")], winners[(family, "cost_tight")]
        changed = {r["model"] for r in free} != {r["model"] for r in tight}
        changes += int(changed)
        def label(selected):
            by_model = {r["model"]: r for r in selected}
            return " / ".join(HISTORICAL_LABELS[model]+" ("+fmt(by_model[model]["value"])+")"
                              for model in HISTORICAL_MODELS if model in by_model)
        metric = "F1" if family.startswith("Search") else "EA" if family == "Audit" else "Gap0"
        display.append([family+" / "+metric, label(free), label(tight), "是" if changed else "否"])
    shared_by_budget = [set.intersection(*({r["model"] for r in winners[(family, budget)]} for family in HISTORICAL_FAMILIES))
                        for budget in ("cost_free", "cost_tight")]
    narrative = f"旧 cohort 的 {len(HISTORICAL_FAMILIES)} 个家族中，{changes} 个在 Free→Tight 时发生最优模型集合变化。"
    if not any(shared_by_budget):
        narrative += "Free 和 Tight 两档都不存在横跨所有家族的同一最优模型，选型依赖目标任务及反馈预算。"
    return table(["任务家族 / 指标", "Free 最优（分数）", "Tight 最优（分数）", "最优集合改变"], display) + "\n" + narrative + "\n\n"


def render(spec, status, aggregates, blocks, effects, historical, historical_budget, historical_winners):
    counts = Counter(r["execution_status"] for r in status)
    nav = ("[详细报告](DETAILS.zh.md) · [逐池 CSV](pool_metrics.csv) · [全部设置 CSV](aggregate_metrics.csv) · "
           "[比较 CSV](contrasts.csv) · [原始 dump / 完整存档索引](ARCHIVE_INDEX.md) · [机器存档索引](ARCHIVE_INDEX.json)\n\n")
    scope = (f"本次是已见任务上的定向、探索性修复后复核：{len(status)} 个计划 N4 池、"
             f"{len({(r['model'],r['scenario'],r['regime']) for r in status})} 个模型×场景×预算单元；"
             f"终态计数 `{json.dumps(dict(sorted(counts.items())), ensure_ascii=False)}`。"
             "旧反例与正对照在新模型调用前固定，选择已参考旧效果；不构成全矩阵或未见任务检验。\n\n")
    old = HISTORICAL + "main_findings_v2/README.zh.md"
    main = "# 修复后定向重跑：三问与核心数据\n\n" + nav + scope
    main += "[实际执行设置与解释](EXECUTION_NOTES.zh.md)。\n\n"
    main += ("## 1. 预算收紧是否导致性能下降？\n\n"
             "下表直接复用冻结旧五模型单体 cohort（`6c63f1c`），不是本轮修复后的新验证。Search F1 / Audit EA 为 0–100 分，"
             "调参为旧报告已授权的 Gap0 部署效用；F−T 为正表示下降。\n\n")
    main += historical_budget_display(historical_budget)
    main += (f"[旧完整预算报告]({old}) · [原封保留的 Free/Moderate/Tight CSV](historical_expgym_summary.csv)。"
             "本轮未重跑单体矩阵，旧源码/部署限制仍适用；新 N4 结果不混入此表。\n\n")
    main += ("## 2. 缓存与 PoolAct 的收益或损失有多大？\n\n"
             "同预算、同 N4、同任务/重复范围比较；正差表示 target 较高。Search F1 / Audit EA 按 0–100 分展示；NAS 是逐成员计算的 Gap 点，100 不是上限。NAS 原严格端点只要缺一个必需成员就保留 unknown；不使用已知子集替代。\n\n")
    main += overall_primary_summary(aggregates)
    main += main_table(aggregates, PRIMARY)
    if nas_gap0_matches_strict(aggregates, status):
        nas_agents = sum(r["N"] for r in status if r["scenario"] == "tuning")
        main += (f"\n本轮 NAS 的 {nas_agents} 个计划成员全部可评分，各 setting 的原严格 Gap-MI/BoN 与已授权 Gap=0 敏感性数值相同，"
                 "因此不重复展示同值表；完整两种口径仍保留在[聚合 CSV](aggregate_metrics.csv)和详细版。\n\n")
    else:
        main += ("\n### 已授权 Gap=0 敏感性（不是原评分）\n\n"
                 "仅正常结束但无最终配置的成员赋 0 部署效用；MI 仍除以固定 N4，BoN 取已交付者最佳或全空时 0。"
                 "基础设施失败与未运行仍是 unknown，不计零。\n\n")
        main += main_table(aggregates, {"tuning": "gap0_mi"})
    main += result_summary(historical, status)
    if all(r["execution_status"] == "completed" and r["missing_answer_agents"] == 0 for r in status):
        main += ("\n本轮全部计划成员均交付了最终回答，残余负差不能归因于本轮缺答；"
                 "完整评分并不排除 legacy 等评价边界，具体见[详细报告](DETAILS.zh.md)。\n")
    main += ("\n全部正、零、负与未知均保留；来源变化包含源码、提示和部署候选，修前修后差不能唯一归因于某一个补丁。"
             "[历史/本轮逐 setting 比较](historical_comparison.csv)分开保留两个 cohort。"
             "[资源表](resources_by_setting.csv)和[全部尝试账本](ALL_ATTEMPTS_INDEX.json)包含其声明范围；同反馈预算不等于同 token、GPU 或真实时间。\n\n")
    main += ("## 3. 最优模型是否随任务和预算重排？\n\n"
             "下表同样直接引用冻结旧单体 cohort（`6c63f1c`）：每家族都使用当时相同的五模型候选集，"
             "并列最优全部保留；不混合不同指标为总榜，不加入本轮 PoolAct 新分数。\n\n")
    main += historical_ranking_display(historical_winners)
    main += (f"[旧家族排名完整报告]({old}) · [原封保留的五模型×六家族×三预算 CSV](historical_family_rankings.csv)。"
             "这描述当时任务与部署条件的依赖性，不意味着小差值具有显著性；本轮定向 N4 矩阵不能更新这一单体排名。\n\n")
    main += "## 查验入口\n\n" + nav + "[输入身份](INPUTS.json) · [逐池执行/缺答分母](pool_status.csv) · [逐重复 CSV](by_outerseed.csv)。\n"
    detail = "# 修复后定向重跑：完整设置与数据\n\n[简明主报告](README.zh.md)\n\n" + nav + scope
    detail += ("## 契约与来源\n\n"
               "启动前范围见 [PLAN.zh.md](PLAN.zh.md)，动态执行规则见 [EXECUTION_CONTRACT.zh.md](EXECUTION_CONTRACT.zh.md)，"
               "实际重试/并发、服务拓扑、GPT恢复与context验证范围见 [EXECUTION_NOTES.zh.md](EXECUTION_NOTES.zh.md)。\n\n"
               "每 item 内先折叠全部注册重复，再 item 等权；NAS 三个任务×R3 不是 36 个独立样本。"
               "Search/Audit R1 不计算重复 SD。不做显著性检验、不取配对交集。"
               "严格未知、零分、正常缺答、执行失败与未执行分别保存。评分为 legacy / task-abstention-v1；"
               "Gap=max(0,100×(agent_perf−oracle.mean_perf)/(oracle.best_perf−oracle.mean_perf))，逐成员变换后求 MI。"
               "本程序只读取已保存的标量与固定来源，不重新调用 scorer，也不代替原队列身份/评分校验或独立最终复核。\n\n"
               "模型请求参数和源码分支见 [plan 设置投影](settings.json)，包括各自 source SHA；"
               "GPT native Responses 的实际 wire 参数省略规则不能从 nominal max_tokens 推断。"
               "执行恢复必须有显式映射，失败历史保留在完整尝试账本，不自动选最新成功文件。\n\n")
    detail += ("NAS 仍沿用 legacy / task-abstention-v1，未升级 task-abstention-v5。"
               "提交 peer 配置但该配置不在自身 trace 时，原 legacy 评分可能回退自身 best，"
               "并不等同于重新评估所提交配置。本轮未改这个旧契约，也未事后把轨迹最优配置填给无回答成员。"
               "因此完整评分只能排除相应的缺答/未知问题，不能据此声称不存在其他评价局限；"
               "严格 Gap 与已授权 Gap0 敏感性都应在这一边界内解读。\n\n")
    detail += ("主报告问1/问3直接读取同一冻结旧 cohort 的 [single 预算 CSV](historical_expgym_summary.csv) 和 "
               "[家族排名 CSV](historical_family_rankings.csv)，原值已是展示单位，不再次乘100或重算旧 raw。"
               "它们不是修复后数据；下列全部策略表才是本轮定向重跑，两个来源不拼成新的模型排行榜。\n\n")
    detail += "## 全部策略设置\n\n"
    detail += table(["模型", "场景", "预算", "策略", "指标", "完整均值", "已知/预期池", "完整 items", "R"], [
        [r["model"], LABELS[r["scenario"]], r["regime"].removeprefix("cost_"), r["strategy"], r["metric"], fmt(r["full_mean"], r["metric"]),
         f"{r['known_pools']}/{r['expected_pools']}", f"{r['complete_items']}/{r['expected_items']}", r["repeats_per_item"]] for r in aggregates])
    detail += "\n## 全部方向对照\n\n"
    detail += table(["模型", "场景", "预算", "指标", "target−baseline", "差值", "已知/预期配对池"], [
        [r["model"], LABELS[r["scenario"]], r["regime"].removeprefix("cost_"), r["metric"], r["strategy"], fmt(r["full_mean"], r["metric"], True), f"{r['known_pools']}/{r['expected_pools']}"] for r in effects])
    detail += ("\n逐 task/question 不挤入主报告；[逐池原分](pool_metrics.csv)、[逐 task 汇总](by_item.csv)、[逐 seed block](by_outerseed.csv)、"
               "[三策略配对](paired_rows.csv)保留完整细节。[修前修后对照](historical_comparison.csv)使用未舍入值，历史文件不重写。\n\n"
               "## 资源与原始数据\n\n"
               "[设置级资源](resources_by_setting.csv)是资源 exporter 已记录的范围，不代表所有失败尝试。"
               "[全部尝试账本](ALL_ATTEMPTS_INDEX.json)另计冷启动、验证、失败、未完成及获准恢复；并发 pool wall 之和不能推导总历时。"
               "reasoning 若包含在 output 不再次相加；模拟反馈秒不是实际 GPU 秒，allocation GPU-hours 可含空闲。\n\n" + nav)
    return {"README.zh.md": main.encode(), "DETAILS.zh.md": detail.encode()}


def load_study(spec_path, artifact_root=None):
    raw = Path(spec_path).read_bytes()
    spec = json.loads(raw)
    require(spec["schema"] == "expgym.material-report-inputs.v1", "unsupported report inputs")
    inputs = Inputs(Path(spec_path).resolve().parent, artifact_root)
    inputs.files["@report_spec"] = dict(path="@report_spec", bytes=len(raw), sha256=sha(raw), role="report_spec")
    inputs.read_paths["@report_spec"] = Path(spec_path).resolve()
    planned, plan_metadata = [], []
    for entry in spec["plans"]:
        plan = inputs.json(entry, "frozen_master_plan")
        planned.extend(plan_rows(plan))
        plan_metadata.append(dict(study_id=plan["study_id"], source_tree_sha256=plan["source_tree_sha256"], plan=entry))
    validate_matrix(planned, spec["expected_jobs"], spec["expected_cells"])
    executions = inputs.json(spec["execution_index"], "explicit_effective_source_mapping")
    require(executions["schema"] == "expgym.material-execution-index.v1", "unsupported execution mapping")
    require(len(executions["jobs"]) == len(planned), "execution slot count differs")
    mapped = {r["logical_job_id"]: r for r in executions["jobs"]}
    require(len(mapped) == len(planned) and set(mapped) == {r["job_id"] for r in planned}, "execution mapping coverage differs")
    oracle = inputs.json(spec["oracle"], "frozen_oracle")
    metrics, statuses = [], []
    for row in planned:
        record = mapped[row["job_id"]]
        state = record["execution_status"]
        require(state in ("completed", "failed", "not_started"), "nonterminal/unsupported execution status")
        base = {k: row[k] for k in ("job_id", "model", "scenario", "regime", "strategy", "item", "seed", "N")}
        status = dict(base, execution_status=state, source_tree_sha256=row["source_tree_sha256"],
                      effective_cohort=record["cohort"], reason=record.get("reason", ""), result_path=None,
                      expected_agents=row["N"], scored_agents=None, missing_answer_agents=None, missing_configuration_agents=None)
        values = {metric: None for metric in METRICS[row["scenario"]]}
        if state == "completed":
            effective_plan = inputs.json(record["effective_plan"], "bound_execution_plan")
            matches = [r for r in plan_rows(effective_plan) if r["job_id"] == record["effective_job_id"]]
            require(len(matches) == 1, "effective plan job missing")
            effective = matches[0]
            for key in ("model", "scenario", "regime", "strategy", "item", "seed", "N", "source_tree_sha256"):
                require(effective[key] == row[key], "recovery changed scientific setting: " + key)
            require(scientific_args(effective["args"]) == scientific_args(row["args"]), "recovery changed model/scientific args")
            result = inputs.json(record["result"], "saved_pool_result")
            summary = inputs.json(record["summary"], "saved_pool_summary")
            inputs.json(record["verification_receipt"], "existing_worker_identity_score_verification_receipt")
            require(record.get("identity_score_verification_passed") is True,
                    "completed result lacks explicit existing identity/score verification declaration")
            require(result["implementation_sha256"]["source_tree"] == row["source_tree_sha256"], "result source differs")
            config = result["config"]
            for key in ("model", "scenario", "tuning_task", "question_index", "data_source", "cc_split", "cost_regime", "strategies", "agents", "seed",
                        "temperature", "max_steps", "max_evals", "max_context_tokens", "missing_final_policy"):
                require(config[key] == effective["args"][key], "result config differs: " + key)
            require(summary["config"] == config and summary["strategies"] == {row["strategy"]: result["aggregate"]}
                    and summary["implementation_sha256"] == result["implementation_sha256"], "summary differs from saved result")
            values, counts = endpoints(result, row, oracle)
            status.update(counts, result_path=record["result"]["path"])
        else:
            require(record.get("reason"), "unexecuted/failed slot needs explicit reason")
            require(not record.get("result"), "failed slot cannot silently contribute partial scores")
        statuses.append(status)
        for metric in METRICS[row["scenario"]]:
            metrics.append(dict(base, metric=metric, unit="Gap points" if metric.startswith("gap") else "fraction",
                                value=values[metric], execution_status=state, effective_cohort=record["cohort"],
                                result_path=status["result_path"]))
    return spec, inputs, planned, plan_metadata, metrics, statuses


def old_comparisons(inputs, spec, aggregates):
    old = list(csv.DictReader(io.StringIO(inputs.read(spec["historical_absolute"], "frozen_historical_absolute").decode())))
    old0 = list(csv.DictReader(io.StringIO(inputs.read(spec["historical_gap0"], "frozen_historical_gap0").decode())))
    index = {}
    for rows, value_key in ((old, "full_mean"), (old0, "value")):
        for r in rows:
            if r["system"] != "poolact" or r["slice_kind"] != "all" or r["slice"] != "all":
                continue
            key = tuple(r[k] for k in BASE)
            require(key not in index, "duplicate historical setting")
            index[key] = number(r[value_key])
    output = []
    for r in aggregates:
        key = tuple(r[k] for k in BASE)
        require(key in index, "historical comparison lacks exact setting: " + str(key))
        before, after = index[key], r["full_mean"]
        output.append(dict(zip(BASE, key), unit=r["unit"], historical_value=before, rerun_value=after,
                           rerun_minus_historical=after-before if before is not None and after is not None else None,
                           historical_cohort="five-model-6c63f1c", rerun_cohort=spec["study_id"],
                           not_single_patch_causal_effect=True))
    return output


def generate(spec_path, artifact_root=None):
    spec, inputs, planned, plan_meta, metrics, statuses = load_study(spec_path, artifact_root)
    aggregates, blocks, by_item = grouped_metrics(metrics), grouped_metrics(metrics, by_seed=True), grouped_metrics(metrics, by_item=True)
    paired, effects = comparisons(metrics)
    historical = old_comparisons(inputs, spec, aggregates)
    old_budget_raw = inputs.read(spec["historical_expgym_summary"], "frozen_historical_single_budget_summary")
    old_rank_raw = inputs.read(spec["historical_family_rankings"], "frozen_historical_single_family_rankings")
    old_budget = historical_budget_data(old_budget_raw)
    _, old_winners = historical_ranking_data(old_rank_raw)
    files = {"pool_metrics.csv": csv_bytes(metrics), "pool_status.csv": csv_bytes(statuses),
             "aggregate_metrics.csv": csv_bytes(aggregates), "by_outerseed.csv": csv_bytes(blocks),
             "by_item.csv": csv_bytes(by_item), "paired_rows.csv": csv_bytes(paired),
             "contrasts.csv": csv_bytes(effects), "historical_comparison.csv": csv_bytes(historical)}
    files["historical_expgym_summary.csv"] = old_budget_raw
    files["historical_family_rankings.csv"] = old_rank_raw
    files.update(render(spec, statuses, aggregates, blocks, effects, historical, old_budget, old_winners))
    for name, key, role in (("resources_by_setting.csv", "resources_by_setting", "formal_resource_export"),
                            ("ALL_ATTEMPTS_INDEX.json", "all_attempts_index", "all_attempts_resources")):
        files[name] = inputs.read(spec[key], role)
    settings = [{k: r[k] for k in ("job_id", "model", "scenario", "item", "regime", "strategy", "seed", "N", "source_tree_sha256", "args")} for r in planned]
    # Avoid copying credentials, even if a malformed plan supplied them.
    require(all(r["args"].get("api_key") is None for r in settings), "credential in plan is forbidden")
    files["settings.json"] = jb(dict(plans=plan_meta, jobs=settings))
    inputs.recheck()
    files["INPUTS.json"] = jb(dict(schema="expgym.material-report-read-inventory.v1", study_id=spec["study_id"],
                                  files=list(inputs.files.values()), python=platform.python_version(),
                                  analyzer_sha256=sha(Path(__file__).read_bytes()),
                                  scores_recomputed_by_analyzer=False, independent_final_review=False))
    files["CHECKS.json"] = jb(dict(schema="expgym.material-report-checks.v1", expected_pools=len(planned),
                                  metric_rows=len(metrics), aggregate_rows=len(aggregates), comparison_rows=len(effects),
                                  execution_status_counts=dict(Counter(r["execution_status"] for r in statuses)),
                                  no_complete_case_selection=True, inferential_significance_tested=False,
                                  no_model_or_scorer_calls=True,
                                  output_sha256={name: sha(raw) for name, raw in sorted(files.items())}))
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, help="restored owned roots containing <model>/<original member>")
    parser.add_argument("--check", action="store_true", help="byte-check an existing report, never write")
    args = parser.parse_args()
    files = generate(args.spec, args.artifact_root)
    if args.check:
        for name, raw in files.items():
            require((args.output / name).read_bytes() == raw, "deterministic output differs: " + name)
    else:
        require(not args.output.exists(), "refuse to replace existing report")
        args.output.mkdir(parents=True)
        for name, raw in files.items():
            (args.output / name).write_bytes(raw)
    print(json.dumps({"files": len(files), "check": args.check, "output": str(args.output)}))


if __name__ == "__main__":
    main()
