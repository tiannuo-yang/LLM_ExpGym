#!/usr/bin/env python3
"""Append only ad03's 16 missing Gemini slots and publish a separate supplement.

This reads saved scalar scores, never calls a model/evaluator, and never writes
upstream inputs. Historical rows remain byte-for-byte equal at the CSV field
level unless their registered missing slot was supplied. Provider identity is
explicit: these are mixed historical Sub2 and new OpenRouter Gemini results.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
GEMINI = "gemini-3.8-flash-medium"
MODEL_NAMES = {"kimi-k3": "Kimi", "glm-5.3": "GLM", "qwen3.8-2.4t-a95b-fp8": "Qwen", "deepseek-v4-flash-0731": "DeepSeek", "gpt-5.6-sol": "GPT", GEMINI: "Gemini*"}
CORE = ("model", "system", "scenario", "regime", "strategy")
NUMERICAL = ("expected_units", "known_units", "missing_units", "expected_items", "complete_items", "repeats_min", "repeats_max", "full_mean", "known_subset_mean")
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
DIMENSIONS = (("Search whois", "restricted_search", "whois", "f1"), ("Search whatis", "restricted_search", "whatis", "f1"), ("Audit EA", "evidence_audit", "evidence_audit", "evidence_acc"), ("Audit LA", "evidence_audit", "evidence_audit", "label_acc"), ("ParamNet", "tuning", "paramnet", "gap0"), ("NAS101", "tuning", "nasbench101", "gap0"), ("NAS201", "tuning", "nasbench201", "gap0"))


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def yes(value):
    return str(value).lower() == "true"


def number(value):
    if value in (None, ""):
        return None
    result = float(value)
    require(math.isfinite(result), "non-finite scalar")
    return result


def same(a, b):
    a, b = number(a), number(b)
    return a is b if a is None or b is None else math.isclose(a, b, abs_tol=1e-9, rel_tol=1e-11)


def mean_complete(values):
    return mean(values) if values and all(v is not None for v in values) else None


def identity(path):
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def json_write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def csv_read(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def csv_write(path, rows, fields=None):
    require(bool(rows) or fields is not None, "empty CSV needs explicit schema")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fields or list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_baseline(bindings_path):
    manifest = json.loads(bindings_path.read_text())
    data = {}
    for key, spec in manifest["inputs"].items():
        raw = Path(spec["path"]).read_bytes()
        require(len(raw) == spec["bytes"] and hashlib.sha256(raw).hexdigest() == spec["sha256"], "frozen input changed: " + key)
        data[key] = raw
    slots = csv_read(data["selected_slots"])
    scalars = csv_read(data["old_scalars"])
    audit = json.loads(data["old_scalar_audit"])
    require(audit["status"] == "PASS" and audit["errors"] == 0, "historical saved-score audit failed")
    require(len(slots) == len(scalars) == 4698, "wrong frozen denominator")
    slot_by_id = {r["slot_id"]: r for r in slots}
    require(len(slot_by_id) == 4698 and len({r['slot_id'] for r in scalars}) == 4698, "duplicate baseline slot")
    for row in scalars:
        source = slot_by_id[row["slot_id"]]
        require(all(row[k] == source[k] for k in (*CORE, "item", "outer_repeat", "order", "seed", "execution_complete", "score_complete")), "scalar source mismatch: " + row["slot_id"])
        row["metrics"] = json.loads(row["metrics_json"])
    missing = {r['slot_id'] for r in slots if not r['trajectory_file']}
    require(len(missing) == 16 and all(slot_by_id[s]["model"] == GEMINI and not yes(slot_by_id[s]["execution_complete"]) for s in missing), "unexpected baseline missing set")
    require(sum(yes(r["execution_complete"]) for r in scalars) == 4682, "historical execution count changed")
    require(sum(r["model"] == GEMINI and yes(r["execution_complete"]) for r in scalars) == 767, "historical Gemini selection changed")
    return manifest, data, slots, scalars, missing


def normal_abstention(outcome, perf):
    return (outcome.get("terminal_origin") == "normal_loop_return"
            and outcome.get("score_status") == "unscorable_missing_configuration"
            and outcome.get("missing_final_policy") == "task-abstention-v1"
            and outcome.get("terminal_status", {}).get("terminal_classification") == "model_no_answer"
            and outcome.get("answer") is None and perf is None)


def extract_new(obj, slot, oracle, new_provider=True):
    """Identical saved-score/Gap0 conventions to the audited frozen reconstruction."""
    def gap(perf):
        if perf is None:
            return None
        ref = oracle[slot["item"]]
        return max(0.0, 100 * (perf - ref["mean_perf"]) / (ref["best_perf"] - ref["mean_perf"]))

    if slot["system"] == "expgym":
        task, run, outcome = obj["task"], obj["run"], obj["outcome"]
        require(task["scenario"] == slot["scenario"] == "tuning", "new N1 slot is not planned HPO")
        require(task["budget"]["regime"] == slot["regime"] and task["item"]["id"] == slot["item"] and int(run["seed"]) == int(slot["seed"]), "new N1 task/budget/seed mismatch")
        if new_provider:
            require(run["backend"]["name"] == "openrouter", "new N1 provider is not OpenRouter")
            require(run["model"]["id"] in ("gemini-3.8-flash-medium-openrouter", "google/gemini-3.8-flash"), "new N1 model identity mismatch")
        perf = number(outcome["score"].get("value"))
        metrics = {"raw_perf": perf, "gap": gap(perf), "gap0": 0.0 if normal_abstention(outcome, perf) else gap(perf)}
        status = outcome["terminal_status"]
        api_model = run["model"]["id"]
    else:
        cfg, aggregate = obj["config"], obj["aggregate"]
        require(cfg["scenario"] == slot["scenario"] and cfg["cost_regime"] == slot["regime"] and obj["strategy"] == slot["strategy"] and int(cfg["seed"]) == int(slot["seed"]), "new N4 task/budget/strategy/seed mismatch")
        item = cfg["tuning_task"] if slot["scenario"] == "tuning" else cfg["data_source"] + ":" + str(cfg["question_index"])
        require(item == slot["item"] and int(cfg["agents"]) == 4, "new N4 item/agent count mismatch")
        if new_provider:
            require(cfg["backend"] == "openrouter" and cfg["model"] == "google/gemini-3.8-flash", "new N4 provider/model identity mismatch")
        agents = obj["agent_results"]
        require(len(agents) == 4 and {int(a["agent_id"]) for a in agents} == {0, 1, 2, 3}, "incomplete/duplicate N4 members")
        require({int(a["seed"]) for a in agents} == set(range(int(slot["seed"]), int(slot["seed"]) + 4)), "new N4 member seed mismatch")
        perfs = [number(a.get("answer_perf")) for a in agents]
        require(perfs == aggregate["individual_perfs"] and same(mean_complete(perfs), aggregate.get("mean_individual_perf")), "saved N4 MI mismatch")
        if slot["scenario"] == "restricted_search":
            require(aggregate["method"] == "majority_vote", "wrong N4 Search aggregation")
            metrics = {"f1_mi": mean_complete(perfs), "f1_mv": number(aggregate.get("answer_perf"))}
        else:
            require(slot["scenario"] == "tuning" and aggregate["method"] == "best_of_n", "wrong new N4 HPO aggregation")
            gaps = [gap(perf) for perf in perfs]
            zero_gaps = [0.0 if normal_abstention(agent, perf) else g for agent, perf, g in zip(agents, perfs, gaps)]
            bon = max(perfs) if all(p is not None for p in perfs) else None
            require(same(bon, aggregate.get("answer_perf")), "saved N4 BoN mismatch")
            metrics = {"raw_perf_mi": mean_complete(perfs), "raw_perf_bon": bon, "gap_mi": mean_complete(gaps), "gap_bon": max(gaps) if all(g is not None for g in gaps) else None, "gap0_mi": mean_complete(zero_gaps), "gap0_bon": max(zero_gaps) if all(g is not None for g in zero_gaps) else None}
        status = obj["terminal_status"]
        api_model = cfg["model"]
    if not yes(status["execution_complete"]):
        # Never promote a partial/failed attempt to a complete endpoint.
        metrics = {k: None for k in metrics}
    return metrics, status, api_model


def select_rows(record, groups):
    selected = groups[tuple(record[k] for k in CORE)]
    if record["slice_kind"] == "family":
        selected = [r for r in selected if r["family"] == record["slice"]]
    elif record["slice_kind"] == "task":
        selected = [r for r in selected if r["item"] == record["slice"]]
    else:
        require(record["slice_kind"] == "all", "unknown slice kind")
    if "repeat" in record:
        rep = record["repeat"]
        if rep.startswith("seed_"):
            selected = [r for r in selected if r["seed"] == rep.removeprefix("seed_")]
        elif rep.startswith("R"):
            selected = [r for r in selected if int(r["outer_repeat"]) == int(rep[1:]) - 1]
        elif int(rep) >= 2200:
            selected = [r for r in selected if r["seed"] == rep]
        else:
            selected = [r for r in selected if r["outer_repeat"] == rep]
    require(bool(selected), "aggregate row selects no registered slot")
    return selected


def aggregate(record, selected):
    units = [(r["item"], r["metrics"].get(record["metric"])) for r in selected]
    if record["system"] == "expgym" and record["scenario"] == "evidence_audit" and record["model"] != GEMINI:
        documents = defaultdict(list)
        for item, val in units:
            documents[item].append(val)
        require(set(map(len, documents.values())) == {3}, "wrong fixed Audit order count")
        units = [(item, mean_complete(vals)) for item, vals in documents.items()]
    items = defaultdict(list)
    for item, val in units:
        items[item].append(val)
    known = sum(val is not None for _, val in units)
    available_item_means = [mean(v for v in vals if v is not None) for vals in items.values() if any(v is not None for v in vals)]
    known_mean = mean(available_item_means) if available_item_means else None
    return {"expected_units": len(units), "known_units": known, "missing_units": len(units) - known, "expected_items": len(items), "complete_items": sum(all(v is not None for v in vs) for vs in items.values()), "repeats_min": min(map(len, items.values())), "repeats_max": max(map(len, items.values())), "known_subset_mean": known_mean, "full_mean": known_mean if known == len(units) else None}


def group_slots(scalars):
    groups = defaultdict(list)
    for r in scalars:
        groups[tuple(r[k] for k in CORE)].append(r)
    return groups


def display(record):
    val = number(record["full_mean"])
    return "unknown" if val is None else f"{val * (100 if record['unit'] == 'fraction' else 1):.2f}"


def table(header, body):
    return "\n".join(["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |", *["| " + " | ".join(map(str, row)) + " |" for row in body]])


def ranks(absolute):
    index = {(r["model"], r["scenario"], r["slice_kind"], r["slice"], r["regime"], r["metric"]): r for r in absolute if r["system"] == "expgym"}
    result = []
    for dimension, scenario, family, metric in DIMENSIONS:
        for regime in REGIMES:
            rows = [index[m, scenario, "family", family, regime, metric] for m in MODEL_NAMES]
            vals = [number(r["full_mean"]) for r in rows]
            all_complete = all(v is not None for v in vals)
            for r, v in zip(rows, vals):
                rank = None if v is None else 1 + sum(x > v and not math.isclose(x, v, abs_tol=1e-9, rel_tol=0) for x in vals if x is not None)
                result.append(dict(dimension=dimension, model=r["model"], regime=regime, metric=metric, full_mean=r["full_mean"], display_value=display(r), complete=v is not None, rank_among_complete=rank, all_six_complete=all_complete, overall_winner=bool(all_complete and rank == 1), cohort_id=r["cohort_id"]))
    return result


def findings(primary, rank_rows):
    result = {"n1_budget": {}, "poolact": {}, "dimension_leader_changes": []}
    for scenario, metric in (("restricted_search", "f1"), ("evidence_audit", "evidence_acc"), ("tuning", "gap0")):
        deltas = {}
        for model in MODEL_NAMES:
            free = number(primary[model, "expgym", scenario, "cost_free", "single", metric]["full_mean"])
            tight = number(primary[model, "expgym", scenario, "cost_tight", "single", metric]["full_mean"])
            if free is not None and tight is not None:
                deltas[model] = (tight - free) * (1 if scenario == "tuning" else 100)
        result["n1_budget"][scenario] = dict(complete_models=len(deltas), declined=sum(v < 0 for v in deltas.values()), unchanged=sum(v == 0 for v in deltas.values()), improved=sum(v > 0 for v in deltas.values()), tight_minus_free=deltas)
    pool_cells = []
    for model in MODEL_NAMES:
        for regime in REGIMES[1:]:
            for scenario, metric in (("restricted_search", "f1_mv"), ("evidence_audit", "evidence_acc_mv"), ("tuning", "gap0_mi")):
                values = {strategy: number(primary[model, "poolact", scenario, regime, strategy, metric]["full_mean"]) for strategy in ("naive", "cached", "poolact")}
                complete = all(v is not None for v in values.values())
                pool_cells.append(dict(model=model, regime=regime, scenario=scenario, complete=complete, poolact_above_both=(values["poolact"] > max(values["naive"], values["cached"])) if complete else None))
    for label, selected in (("all", pool_cells), ("tight", [r for r in pool_cells if r["regime"] == "cost_tight"])):
        result["poolact"][label] = dict(planned=len(selected), complete=sum(r["complete"] for r in selected), poolact_above_both=sum(r["poolact_above_both"] is True for r in selected))
    for dimension, *_ in DIMENSIONS:
        winners = {regime: [r["model"] for r in rank_rows if r["dimension"] == dimension and r["regime"] == regime and r["overall_winner"]] for regime in REGIMES}
        result["dimension_leader_changes"].append(dict(dimension=dimension, winners=winners, complete_free_tight=bool(winners[REGIMES[0]] and winners[REGIMES[2]]), free_tight_leader_changed=set(winners[REGIMES[0]]) != set(winners[REGIMES[2]]) if winners[REGIMES[0]] and winners[REGIMES[2]] else None))
    return result


def build(args):
    require(not args.output.exists(), "output must be a new directory; preserve earlier reports")
    manifest, data, slots, old_scalars, missing = load_baseline(args.bindings)
    oracle = json.loads(data["oracle"])["tasks"]
    old_groups = group_slots(old_scalars)
    sources = {r["slot_id"]: r for r in slots}
    new_specs = [] if args.new_results is None else json.loads(args.new_results.read_text())["results"]
    require(len({r['slot_id'] for r in new_specs}) == len(new_specs), "duplicate new result selection")
    require({r["slot_id"] for r in new_specs} <= missing, "new result would overwrite an already retained slot")
    scalars = [dict(r) for r in old_scalars]
    merged = {r["slot_id"]: r for r in scalars}
    new_identities = []
    for spec in new_specs:
        slot_id = spec["slot_id"]
        path = Path(spec["result_path"]).resolve()
        actual = identity(path)
        require(actual["sha256"] == spec["sha256"], "new result SHA mismatch: " + slot_id)
        metrics, status, api_model = extract_new(json.loads(path.read_bytes()), sources[slot_id], oracle)
        row = merged[slot_id]
        row.update(metrics=metrics, metrics_json=json.dumps(metrics, sort_keys=True), execution_complete=str(yes(status["execution_complete"])), score_complete=str(yes(status["score_complete"])))
        new_identities.append(dict(slot_id=slot_id, job_id=spec.get("job_id", ""), provider="openrouter", provider_model=api_model, cohort_id="gemini_openrouter_missing_main_20260917", **actual))
    adopted = {r["slot_id"] for r in new_identities}
    if args.require_complete:
        require(adopted == missing and all(yes(merged[s]["execution_complete"]) for s in missing), "not all 16 registered missing slots have execution-complete results")
    new_groups = group_slots(scalars)
    outputs, changes = {}, []
    baseline_checks = 0
    for filename in ("absolute_settings.csv", "by_repeat.csv", "main_expgym.csv", "main_poolact.csv"):
        original_rows = csv_read(data[filename])
        updated_rows = []
        for record, old in enumerate(original_rows, 1):
            before_selected = select_rows(old, old_groups)
            before = aggregate(old, before_selected)
            require(all(same(before[k], old[k]) for k in NUMERICAL), f"baseline scalar replay mismatch: {filename}:{record}")
            baseline_checks += 1
            relevant = {r["slot_id"] for r in before_selected} & adopted
            new = dict(old)
            if relevant:
                after = aggregate(old, select_rows(old, new_groups))
                for k, val in after.items():
                    new[k] = "" if val is None else str(val)
                selected_cohorts = {"gemini_openrouter_missing_main_20260917" if r["slot_id"] in adopted else sources[r["slot_id"]]["cohort_id"] for r in before_selected}
                new.update(cohort_id="+".join(sorted(selected_cohorts)), source_input="slot_scalars.csv", source_row=json.dumps(sorted(r["slot_id"] for r in before_selected)), latest_selection="retain_all_frozen_completed_slots_append_only_registered_missing_slots")
                if "display_value" in new:
                    new["display_value"] = display(new)
                    new["status"] = "known" if new["full_mean"] else "unknown"
                for field in NUMERICAL:
                    if not same(old[field], new[field]):
                        changes.append(dict(file=filename, record=record, model=old["model"], system=old["system"], scenario=old["scenario"], regime=old["regime"], strategy=old["strategy"], slice_kind=old["slice_kind"], slice=old["slice"], metric=old["metric"], field=field, before=old[field], after=new[field], added_slots=";".join(sorted(relevant))))
            else:
                require(new == old, "untouched frozen record changed")
            updated_rows.append(new)
        outputs[filename] = updated_rows
    require(baseline_checks == 7767, "incomplete frozen aggregate replay")
    args.output.mkdir(parents=True)
    for filename, rows in outputs.items():
        csv_write(args.output / filename, rows)
    new_by_slot = {r["slot_id"]: r for r in new_identities}
    public_sources, scalar_rows = [], []
    for r in scalars:
        slot, sid = sources[r["slot_id"]], r["slot_id"]
        provider = "openrouter" if sid in adopted else "sub2api" if r["model"] == GEMINI and yes(r["execution_complete"]) else "historical_other" if yes(r["execution_complete"]) else "not_executed"
        cohort = new_by_slot[sid]["cohort_id"] if sid in adopted else slot["cohort_id"]
        scalar_rows.append({**{k: v for k, v in r.items() if k != "metrics"}, "provider_cohort": provider, "cohort_id": cohort})
        public_sources.append(dict(slot_id=sid, model=r["model"], system=r["system"], scenario=r["scenario"], item=r["item"], regime=r["regime"], strategy=r["strategy"], seed=r["seed"], order=r["order"], outer_repeat=r["outer_repeat"], execution_complete=r["execution_complete"], score_complete=r["score_complete"], provider=provider, cohort_id=cohort, selection="new_missing_slot" if sid in adopted else "retained_frozen", result_sha256=new_by_slot[sid]["sha256"] if sid in adopted else slot["trajectory_sha256"], historical_trajectory=slot["trajectory_file"], new_result_index=(1 + next(i for i, x in enumerate(new_identities) if x["slot_id"] == sid)) if sid in adopted else ""))
    csv_write(args.output / "slot_scalars.csv", scalar_rows)
    csv_write(args.output / "SOURCE_SELECTION.csv", public_sources)
    change_fields = ("file", "record", "model", "system", "scenario", "regime", "strategy", "slice_kind", "slice", "metric", "field", "before", "after", "added_slots")
    csv_write(args.output / "CHANGES.csv", changes, change_fields)
    rank_rows = ranks(outputs["absolute_settings.csv"])
    csv_write(args.output / "dimension_rankings.csv", rank_rows)
    helper_path = Path(manifest["inputs"]["comparison_helper"]["path"])
    spec = importlib.util.spec_from_file_location("frozen_comparison_helpers", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    comparisons, fields = helper.make_comparisons(outputs["absolute_settings.csv"])
    csv_write(args.output / "COMPARISON.csv", comparisons, fields)
    counts = {"planned_slots": 4698, "historical_canonicals_retained": 4682, "historical_gemini_canonicals_retained": 767, "new_result_files": len(adopted), "execution_complete": sum(yes(r["execution_complete"]) for r in scalars), "score_complete": sum(yes(r["score_complete"]) for r in scalars), "gemini_execution_complete": sum(r["model"] == GEMINI and yes(r["execution_complete"]) for r in scalars), "baseline_aggregate_rows_replayed": baseline_checks, "changed_numeric_fields": len(changes), "planned_missing_slots_remaining": sorted(missing - adopted), "new_incomplete_slots": sorted(s for s in adopted if not yes(merged[s]["execution_complete"]))}
    json_write(args.output / "CHECKS.json", {"status": "COMPLETE" if counts["execution_complete"] == 4698 else "INCOMPLETE", **counts, "boundary": "Saved scalar extraction and deterministic aggregation; not an independent re-execution of the task evaluator. Only normal HPO abstention is zero in Gap0; incomplete execution is never zero."})
    json_write(args.output / "INPUTS.json", {"frozen": manifest, "new_result_manifest": identity(args.new_results) if args.new_results else None, "new_results": new_identities, "method": "Preserve all 4682 frozen canonical records; append only the fixed missing 16. CSV full means use equal item weights after within-item repetition means. Existing provider and new OpenRouter provider are explicitly separate cohorts."})
    primary = {}
    for row in outputs["absolute_settings.csv"]:
        if row["slice_kind"] == "all":
            primary[tuple(row[k] for k in (*CORE, "metric"))] = row
    n1 = [[MODEL_NAMES[m], *[" / ".join(display(primary[m, "expgym", scenario, regime, "single", metric]) for regime in REGIMES) for scenario, metric in (("restricted_search", "f1"), ("evidence_audit", "evidence_acc"), ("tuning", "gap0"))]] for m in MODEL_NAMES]
    n4 = [[MODEL_NAMES[m], regime.removeprefix("cost_"), *[" / ".join(display(primary[m, "poolact", scenario, regime, strategy, metric]) for strategy in ("naive", "cached", "poolact")) for scenario, metric in (("restricted_search", "f1_mv"), ("evidence_audit", "evidence_acc_mv"), ("tuning", "gap0_mi"))]] for m in MODEL_NAMES for regime in REGIMES[1:]]
    lines = ["# Gemini OpenRouter 主实验补充报告", "", f"冻结来源：`{manifest['source_report_commit']}`。此目录是独立补充版，未修改冻结报告。执行完成 **{counts['execution_complete']}/4698**；严格评分完整 **{counts['score_complete']}**；Gemini **{counts['gemini_execution_complete']}/783**。", "", "本版保留原 4682 份采用结果（其中 Gemini 767 份），只补原先注册但没有采用完成结果的 16 项。新项使用 OpenRouter；原 Gemini 项使用 Sub2 API。星号 Gemini* 表示混合提供方的数据组合，不是全套 OpenRouter 重跑。协议、思考与采样参数尽量对应，但提供方切换的影响不能从这批数据单独识别。", "", "F1 / EA 显示 0–100；Gap0 使用原 points。完整均值缺失仍为 unknown；不把部分成功均值用作完整结果。HPO 先在任务内平均 3 重复，再对任务等权；Gap0 仅将正常结束的无配置结果计零，失败或未执行不计零。", "", "## N1：Free / Moderate / Tight", "", table(["模型", "Search F1", "Audit EA", "HPO Gap0"], n1), "", "## N4：naive / cached / PoolAct", "", "Search 为 whois 39 题；Audit 13 文档；HPO 为 NAS101 A/B/C × 3 重复。", "", table(["模型", "预算", "Search F1-MV", "Audit EA-MV", "HPO Gap0-MI"], n4), "", "## 家族与预算排名", "", "[dimension_rankings.csv](dimension_rankings.csv)含 7 维 × 6 模型 × 3 预算，缺失保留；只有六模型完整时标记全体冠军，并列保持。", "", "[完整聚合](absolute_settings.csv) · [逐重复](by_repeat.csv) · [合并比较](COMPARISON.csv) · [逐字段变化](CHANGES.csv) · [4698 项来源](SOURCE_SELECTION.csv) · [逐项分数](slot_scalars.csv) · [输入哈希](INPUTS.json) · [检查结果](CHECKS.json)", "", "原有 Search / Audit N1 分数不变。本次补齐会改变 Gemini HPO 完整均值、相关家族与模型排名、N4 Search Moderate naive 及部分 NAS 端点。不得将旧报告中的“未齐”、冠军数、三策略完整组数或宏均值描述直接复制为本版结论。", ""]
    updated_findings = findings(primary, rank_rows)
    json_write(args.output / "FINDINGS.json", updated_findings)
    winner_table = []
    for entry in updated_findings["dimension_leader_changes"]:
        winner_table.append([entry["dimension"], *[" / ".join(MODEL_NAMES[m] for m in entry["winners"][regime]) or "unknown" for regime in REGIMES]])
    complete_dimensions = sum(r["complete_free_tight"] for r in updated_findings["dimension_leader_changes"])
    changed_dimensions = sum(r["free_tight_leader_changed"] is True for r in updated_findings["dimension_leader_changes"])
    pool = updated_findings["poolact"]
    lines += ["## 本版重新计算的结论", "", f"N1 Free→Tight：Search {updated_findings['n1_budget']['restricted_search']['declined']}/{updated_findings['n1_budget']['restricted_search']['complete_models']}、Audit {updated_findings['n1_budget']['evidence_audit']['declined']}/{updated_findings['n1_budget']['evidence_audit']['complete_models']}、HPO {updated_findings['n1_budget']['tuning']['declined']}/{updated_findings['n1_budget']['tuning']['complete_models']} 个完整模型下降。", "", f"PoolAct 三策略比较完整 {pool['all']['complete']}/{pool['all']['planned']} 组，其中 {pool['all']['poolact_above_both']} 组严格高于 naive 与 cached；Tight 为 {pool['tight']['poolact_above_both']}/{pool['tight']['complete']}。这是当前任务与设置下的方向计数。", "", f"以下 {complete_dimensions} 个维度在 Free/Tight 均具六模型完整结果，其中 {changed_dimensions} 个第一名集合改变。Audit LA 与 EA 是同一 Audit 场景的两个指标，不能当作两个独立任务。", "", table(["维度", "Free 第一名", "Moderate 第一名", "Tight 第一名"], winner_table), "", "汇总数字见 [FINDINGS.json](FINDINGS.json)。不跨场景合成总分，不据此作显著性或单一提供方效应的因果判断。", ""]
    (args.output / "README.zh.md").write_text("\n".join(lines))
    print(json.dumps(counts, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, default=HERE / "BASELINE_BINDINGS.json")
    parser.add_argument("--new-results", type=Path, help='JSON {"results": [{"slot_id":..., "result_path":..., "sha256":..., "job_id":...}]}')
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-complete", action="store_true")
    build(parser.parse_args())


if __name__ == "__main__":
    main()
