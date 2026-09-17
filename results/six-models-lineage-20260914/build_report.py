#!/usr/bin/env python3
"""Six-model descriptive report from immutable, already-scored exports.

No scorer, model request, raw dump, task resampling or upstream write occurs.
The published sibling report provides hash-recorded numeric helper functions;
its historical prose and seven-model denominators are not reused.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
from collections import Counter
from pathlib import Path

MODELS = (
    "kimi-k3", "glm-5.3", "qwen3.8-2.4t-a95b-fp8",
    "deepseek-v4-flash-0731", "gpt-5.6-sol", "gemini-3.8-flash-medium",
)
SHORT = dict(zip(MODELS, ("Kimi K3", "GLM 5.3", "Qwen 3.8", "DeepSeek V4 Flash", "GPT-5.6-sol", "Gemini 3.8 Flash")))
SCENES = ("restricted_search", "evidence_audit", "tuning")
SCENE_LABELS = dict(zip(SCENES, ("Search", "Audit", "HPO")))
FROZEN_FILES = (
    "manifest.json", "render_report.py", "absolute_settings.csv", "by_repeat.csv",
    "SOURCE_SELECTION.csv", "SCORE_COMPLETENESS.csv", "resources.csv", "inherited_resources.csv",
)
COPIED_CSV = tuple(f for f in FROZEN_FILES if f.endswith(".csv"))
PUBLIC_COMMIT = "0245b2d1ef8a88e5d579f137fb711eea2027e3c5"
CHECKED_GEMINI_UTC = "2026-09-14T23:45:00Z"


def load_helpers(path):
    spec = importlib.util.spec_from_file_location("frozen_report_numeric_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return list(reader.fieldnames), rows


def as_csv(rows, fields):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def as_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def selected_manifest(manifest, models=MODELS):
    lookup = {m["id"]: m for m in manifest["models"]}
    missing = set(models) - set(lookup)
    if missing:
        raise ValueError(f"Models absent from source manifest: {sorted(missing)}")
    return {
        "models": [dict(lookup[m]) for m in models],
        "scope_plan": [dict(r) for r in manifest.get("scope_plan", []) if r.get("model") in models],
        "cutoff_utc": manifest["cutoff_utc"],
        "study_type": "Custom study: retrospective six-model scope, frozen scores",
    }


def claim_counts(report, helper, rankings):
    budget = {}
    pool = {"planned": 0, "complete": 0, "wins_both": 0, "tight_complete": 0, "tight_wins_both": 0}
    pool_cells = []
    for scene in SCENES:
        changes = []
        planned = 0
        for model in report.model_ids:
            if report.planned(model, "expgym", scene, "cost_free", "single"):
                planned += 1
                a, b = [report.find(model, "expgym", scene, r, "single", helper.PRIMARY["expgym"][scene]) for r in ("cost_free", "cost_tight")]
                if not report._delta(a, b).startswith("unknown"):
                    changes.append((b["full_mean"] - a["full_mean"]) * (100 if helper._fraction(a) else 1))
            for regime in helper.REGIMES[1:]:
                if not all(report.planned(model, "poolact", scene, regime, s) for s in ("naive", "cached", "poolact")):
                    continue
                pool["planned"] += 1
                rows = [report.find(model, "poolact", scene, regime, s, helper.PRIMARY["poolact"][scene]) for s in ("naive", "cached", "poolact")]
                comparable = all(not report._delta(rows[0], r).startswith("unknown") for r in rows[1:])
                win = comparable and rows[2]["full_mean"] > max(r["full_mean"] for r in rows[:2])
                pool["complete"] += int(comparable)
                pool["wins_both"] += int(win)
                if regime == "cost_tight":
                    pool["tight_complete"] += int(comparable)
                    pool["tight_wins_both"] += int(win)
                pool_cells.append({"model": model, "scenario": scene, "regime": regime, "complete": comparable, "poolact_strictly_above_both": bool(win) if comparable else None})
        budget[scene] = {"planned": planned, "complete": len(changes), "degraded": sum(v < 0 for v in changes), "unchanged": sum(v == 0 for v in changes), "improved": sum(v > 0 for v in changes), "unknown": planned - len(changes), "deltas_display_units": changes}
    rank_changes = []
    complete_families = []
    for family in helper.FAMILIES:
        winners = [[r["model"] for r in rankings if r["family"] == family and r["regime"] == regime and r["overall_winner"]] for regime in ("cost_free", "cost_tight")]
        if all(winners):
            complete_families.append(family)
            if set(winners[0]) != set(winners[1]):
                rank_changes.append({"family": family, "free": winners[0], "tight": winners[1]})
    return {"budget": budget, "poolact": pool, "poolact_cells": pool_cells, "ranking": {"complete_families": complete_families, "changed_families": rank_changes}}


def score_cell(report, helper, model, system, scene, regime, strategy, metric=None, coverage=False):
    row = report.find(model, system, scene, regime, strategy, metric or helper.PRIMARY[system][scene])
    return report.cell(row) if coverage or row is None or row["full_mean"] is None else helper._display(row)


def best_known(rankings, family, regime, helper):
    rows = [r for r in rankings if r["family"] == family and r["regime"] == regime]
    best = [r for r in rows if r["rank"] == 1]
    if not best:
        return "unknown"
    label = " / ".join(f"{SHORT[r['model']]} {r['display_value']}" for r in best)
    return label if all(r["ranking_status"] == "known" for r in rows) else "未齐；已知最高 " + label


def readme(report, helper, rankings, counts):
    p = counts["poolact"]
    b = counts["budget"]
    ranking = counts["ranking"]
    models = report.models
    total = {key: sum(m[key] for m in models) for key in ("planned", "execution_complete", "score_complete")}
    lines = [
        "# 六模型综合报告", "",
        "范围：Kimi、GLM、Qwen、DeepSeek、GPT、Gemini；按用户要求排除 Claude。本次只更新报告，没有新增实验或重评分。", "",
        f"沿用 2026-09-13 冻结分数；Gemini 于 2026-09-14 23:45 UTC 复查，完成项未变化。合计执行完成 **{total['execution_complete']:,}/{total['planned']:,}**，严格评分完整 **{total['score_complete']:,}**。", "",
        "[每次实验记录](EXPERIMENT_LOG.zh.md) · [最终数据来自哪里](DATA_LINEAGE.zh.md) · [原始 dump / CSV 存档](ARCHIVE_INDEX.md) · [完整设置与详细数据](DETAILS.zh.md) · [独立复核](INDEPENDENT_REVIEW.zh.md)", "",
        "## 三个结论", "",
        f"1. **预算收紧，表现下降。** Free→Tight：Search {b['restricted_search']['degraded']}/{b['restricted_search']['complete']}、Audit {b['evidence_audit']['degraded']}/{b['evidence_audit']['complete']} 个模型下降；HPO {b['tuning']['degraded']}/{b['tuning']['complete']} 个完整模型下降，Gemini 全场景 HPO 未齐。",
        f"2. **PoolAct 通常改善同预算表现。** {p['complete']}/{p['planned']} 组三策略数据完整，其中 {p['wins_both']} 组高于 naive 和 cached；Tight 为 {p['tight_wins_both']}/{p['tight_complete']}。这是方向计数，不是每个模型、每个任务都改善。",
        f"3. **最佳模型随任务和部署预算变化。** 六模型在 Free/Tight 都完整的 {len(ranking['complete_families'])} 个任务家族中，{len(ranking['changed_families'])} 个更换第一名，见下表。模型选择需要结合 task family 和 budget。", "",
        "这些是当前部署设置下的描述性结果，不是显著性或单一算法的因果结论。排除 Claude 是用户指定的回顾性范围调整，不构成稳健性检验；未删除其历史记录。", "",
        "## 数据范围", "",
        helper._table(["模型", "effort", "执行完成/计划", "严格评分完整"], [[SHORT[m["id"]], m["effort"], f"{m['execution_complete']}/{m['planned']}", m["score_complete"]] for m in models]), "",
        "每模型计划：ExpGym N1 417 项（Free/Moderate/Tight）+ N4 366 池（Moderate/Tight × naive/cached/poolact）。DeepSeek 有 11 项严格评分缺失；Gemini 保留 1 个 Search 池失败和 15 个 HPO 未完成项，不能视为全量。", "",
        "## 1. ExpGym：Free → Moderate → Tight", "",
        "F1、EvidenceAcc 显示为 0–100；Gap0 保持原 points。不同场景不合成总分。", "",
        helper._table(["模型", "Search F1：F / M / T", "Audit EA：F / M / T", "HPO Gap0：F / M / T"], [[SHORT[m], *[" / ".join(score_cell(report, helper, m, "expgym", s, r, "single") for r in helper.REGIMES) for s in SCENES]] for m in report.model_ids]), "",
        "## 2. N4：naive / cached / PoolAct", "",
        "每格依次为 naive / cached / poolact；Search 为 whois 子集的 F1-MV，Audit 为 EA-MV，HPO 为 Gap0-MI。N4 Search 与 N1 的 73 题全集不同，不直接互减。", "",
        helper._table(["模型", "预算", "Search F1-MV", "Audit EA-MV", "HPO Gap0-MI"], [[SHORT[m], helper.REGIME_LABELS[r], *[" / ".join(score_cell(report, helper, m, "poolact", s, r, strategy) for strategy in ("naive", "cached", "poolact")) for s in SCENES]] for m in report.model_ids for r in helper.REGIMES[1:]]), "",
        "## 3. 任务家族与预算的排名重排", "",
        helper._table(["任务家族", "Free 最高", "Moderate 最高", "Tight 最高"], [[f, *[best_known(rankings, f, r, helper) for r in helper.REGIMES]] for f in helper.FAMILIES]), "",
        "“未齐；已知最高”不代表六模型冠军。排名只使用 N1，同一端点、同一家族；并列保留。", "",
        "unknown 不补零、不用成功子集冒充全量。Gap0 仅把正常结束但无有效 HPO 配置记 0；严格 Gap 仍缺失，失败/未完成不适用。所有负差保留在详细表和 CSV。", "",
        "[详细报告](DETAILS.zh.md)含完整预算、策略、严格 Gap / Gap0、全部次指标和重复层入口。[实验记录](EXPERIMENT_LOG.zh.md)说明何时发现问题、哪些组重跑及最终采用哪份数据。", "",
    ]
    return "\n".join(lines)


def details(report, helper, rankings, transitions, counts):
    lines = [
        "# 六模型详细报告", "",
        "[主报告](README.zh.md) · [实验记录](EXPERIMENT_LOG.zh.md) · [数据来源](DATA_LINEAGE.zh.md) · [完整存档](ARCHIVE_INDEX.md)", "",
        "## 设置与口径", "",
        "Custom study：复用冻结分数，按用户要求限定六模型。原始分数、正常缺答、负值、失败与未完成全部保留在各自口径内。没有新增实验、重评分或重新选择成功任务。", "",
        "ExpGym N1：Search 73 题（whois 39、whatis 34）R1；Audit 13 文档 × 3 固定顺序；HPO 9 任务 × 3 重复。PoolAct N4：whois 39 题、Audit 13 文档，均 R1；NAS101 A/B/C × 3 重复；Moderate/Tight × naive/cached/poolact。N4 的 Free 未计划。", "",
        "Free 隐藏且不限制模拟反馈成本，但仍受步骤、上下文及输出上限约束。Moderate=10×、Tight=3× 基准成本；Search/Audit 基准 300 秒，HPO 使用冻结 oracle best_cost。真实推理时间不是模拟反馈成本。", "",
        "先在 item 内平均重复/顺序，再对 item 等权平均；Audit 三顺序不是三次独立生成重复，N4 四名 agent 不是四次独立重复。沿用原 legacy HPO 最终配置选择规则，不改为 submitted-only。", "",
        "F1/EA/LA 比例显示为 0–100；Gap/Gap0 为原 points。MV=原投票聚合，MI=池内个体分数均值，BoN=原最佳成员端点；端点之间不互换。`[known/expected]` 使用来源导出的分析单元，不是 API 请求数；Audit 的一些导出已折叠顺序，另一些保留 39 单元，两者都按原 item 权重读数。", "",
        "完整均值缺失时写 unknown；已知子集均值单独列，不填完整端点。Gap0 仅对正常结束而缺有效 HPO 配置的成员赋 0；严格 Gap/Gap-MI 仍未知，失败、暂停、未启动不补零。", "",
        "不同模型的 effort、native/text 协议、API/自托管部署和执行源码并不完全相同；9 月 12 日定向重跑同时涉及代码/提示与部署变动，不能把前后差异全部归因于一个 bug。具体身份、日期和整组替换记录见数据来源与实验日志。", "",
        "Gemini 已完成 767/783，9 月 14 日 23:45 UTC 检查与 9 月 13 日快照一致。1 个 Search Moderate naive 池失败，15 个未完成项集中在 HPO 第三重复：N1 6 项、N4 9 项；不能假设缺失随机。", "",
        "## ExpGym N1：完整预算", "",
    ]
    for scene in SCENES:
        metric = helper.PRIMARY["expgym"][scene]
        body = []
        for model in report.model_ids:
            rows = [report.find(model, "expgym", scene, r, "single", metric) for r in helper.REGIMES]
            body.append([SHORT[model], *[report.cell(r) for r in rows], report._delta(rows[0], rows[1]), report._delta(rows[1], rows[2]), report._delta(rows[0], rows[2])])
        lines += [f"### {SCENE_LABELS[scene]} — {helper.METRIC_LABELS[metric]}", "", helper._table(["模型", "Free", "Moderate", "Tight", "Δ M−F", "Δ T−M", "Δ T−F"], body), ""]
    lines += ["## N4：全部预算与三种策略", ""]
    for scene in SCENES:
        metric = helper.PRIMARY["poolact"][scene]
        body = []
        for model in report.model_ids:
            for regime in helper.REGIMES[1:]:
                rows = [report.find(model, "poolact", scene, regime, s, metric) for s in ("naive", "cached", "poolact")]
                body.append([SHORT[model], helper.REGIME_LABELS[regime], *[report.cell(r) for r in rows], report._delta(rows[0], rows[1]), report._delta(rows[0], rows[2]), report._delta(rows[1], rows[2])])
        lines += [f"### {SCENE_LABELS[scene]} — {helper.METRIC_LABELS[metric]}", "", helper._table(["模型", "预算", "naive", "cached", "poolact", "Δ cached−naive", "Δ poolact−naive", "Δ poolact−cached"], body), ""]
    lines += ["## HPO：严格 Gap 与 Gap0 分开", "", "未知旁括号内为已知子集均值，只供核查，不进入完整组比较。", ""]
    for system, metric, label in (("expgym", "gap", "N1 严格 Gap"), ("poolact", "gap_mi", "N4 严格 Gap-MI")):
        body = []
        for model in report.model_ids:
            for regime in (helper.REGIMES if system == "expgym" else helper.REGIMES[1:]):
                strategies = ("single",) if system == "expgym" else ("naive", "cached", "poolact")
                values = []
                for strategy in strategies:
                    r = report.find(model, system, "tuning", regime, strategy, metric)
                    value = report.cell(r)
                    if r and r["full_mean"] is None:
                        value += "（已知子集 " + helper._display(r, "known_subset_mean") + "）"
                    values.append(value)
                body.append([SHORT[model], helper.REGIME_LABELS[regime], *values])
        lines += [f"### {label}", "", helper._table(["模型", "预算", *(["single"] if system == "expgym" else ["naive", "cached", "poolact"])], body), ""]
    lines += ["## 家族分数与排名", "", "只比较 N1；每行同时给六模型分数，unknown 保留。全候选未齐时不宣布全体最佳。", ""]
    for family in helper.FAMILIES:
        body = []
        for regime in helper.REGIMES:
            selected = {r["model"]: r for r in rankings if r["family"] == family and r["regime"] == regime}
            body.append([helper.REGIME_LABELS[regime], *[selected.get(m, {}).get("display_value", "unknown") for m in report.model_ids], best_known(rankings, family, regime, helper)])
        lines += [f"### {family}", "", helper._table(["预算", *[SHORT[m] for m in report.model_ids], "已知最高及资格"], body), ""]
    lines += [
        "完整排名：[family_rankings.csv](family_rankings.csv)；同一全预算已知候选集上的重排：[rank_transitions.csv](rank_transitions.csv)。后者显式记录缺失候选，不能用子集排名宣称六模型冠军。", "",
        "## 全场景所有端点", "",
        "以下不只列主指标；逐任务/家族、全设置和次指标全量行见 [absolute_settings.csv](absolute_settings.csv)。已知子集与完整均值分列。", "",
    ]
    all_rows = [r for r in report.rows if r["slice_kind"] == "all" and r["slice"] == "all"]
    lines += [helper._table(["模型", "系统", "场景", "预算", "策略", "指标", "完整均值 [known/expected]", "已知子集均值", "来源 cohort"], [[SHORT[r["model"]], r["system"], SCENE_LABELS[r["scenario"]], helper.REGIME_LABELS[r["regime"]], r["strategy"], r["metric"], report.cell(r), helper._display(r, "known_subset_mean"), r["cohort_id"]] for r in all_rows]), ""]
    lines += [
        "## 重复、资源和来源", "",
        "[by_repeat.csv](by_repeat.csv)保留原重复层/顺序标签与分母；R1 不制造 SD。[contrasts.csv](contrasts.csv)保留家族/任务/所有端点的预算差、cached−naive、poolact−naive、poolact−cached，均先用未舍入值计算。", "",
        "[resources.csv](resources.csv)保留六模型的原资源账本口径；[inherited_resources.csv](inherited_resources.csv)保留未被整组替换设置的原资源出口。reference-only 与不完整总量不冒充完整成本；Gemini 尚无关闭运行的全尝试成本总账，不记为零。并发 wall 不能相加作总历时，allocation GPU-hours 不能当作正式实验利用量。", "",
        "[SOURCE_SELECTION.csv](SOURCE_SELECTION.csv)列出保留/替换理由、源行号和 cohort；[SCORE_COMPLETENESS.csv](SCORE_COMPLETENESS.csv)记录逻辑计划项和严格评分完整数。按 9 月 12 日已注册的完整三策略组替换，不在新旧结果间择优；其他设置继承旧正式数据。", "",
        "[EXPERIMENT_LOG.zh.md](EXPERIMENT_LOG.zh.md)回答每次跑了什么、发现什么问题、是否重跑；[DATA_LINEAGE.zh.md](DATA_LINEAGE.zh.md)回答最终每部分从哪里来；[ARCHIVE_INDEX.md](ARCHIVE_INDEX.md)定位原始 dump、归档和 CSV。", "",
        "## 可重建性", "",
        "在本目录执行 `python build_report.py --check` 和 `python -m unittest test_build_report.py`；仅标准库，记录环境为 CPython 3.11.15。默认读取相邻的冻结 `../all-models-latest-20260913/`，也可用 `--input-dir` 指定同一组输入。`--check` 逐字节核对本生成器拥有的输出，不写文件；不读取原始请求、不重新评分。", "",
        "[REPORT_INPUTS.json](REPORT_INPUTS.json)记录实际输入和 SHA256；[REPORT_CHECKS.json](REPORT_CHECKS.json)记录六模型分母、缺失、胜负和排名重算。源码固定输入的 `render_report.py` 仅用于数字助手；旧报告文字与七模型计数未复用。独立复核与来源/存档文件由本次报告工作流另行检查，不由本生成器覆盖。", "",
    ]
    return "\n".join(lines)


def build(input_dir):
    helper = load_helpers(input_dir / "render_report.py")
    manifest = selected_manifest(json.loads((input_dir / "manifest.json").read_text()))
    csv_inputs = {name: read_csv(input_dir / name) for name in COPIED_CSV}
    filtered = {name: (fields, [r for r in rows if r["model"] in MODELS]) for name, (fields, rows) in csv_inputs.items()}
    report = helper.Report(filtered["absolute_settings.csv"][1], manifest)
    if tuple(report.model_ids) != MODELS:
        raise ValueError("Unexpected model scope/order")
    rankings, transitions = report.rankings()
    contrasts = report.contrasts()
    counts = claim_counts(report, helper, rankings)
    totals = {key: sum(m[key] for m in manifest["models"]) for key in ("planned", "execution_complete", "score_complete", "failed", "inflight", "unstarted")}
    checks = {"scope": "six-model retrospective report; no model/scorer/raw calls", "models": list(MODELS), "totals": totals, "claims": counts, "filtered_rows": {name: len(rows) for name, (_, rows) in filtered.items()}, "recomputed_rows": {"contrasts": len(contrasts), "family_rankings": len(rankings), "rank_transitions": len(transitions)}, "strict_score_counts_by_model": {m: sum(int(r["fully_scored_logical_jobs"]) for r in filtered["SCORE_COMPLETENESS.csv"][1] if r["model"] == m) for m in MODELS}, "numerical_policy": "original means/unknowns preserved; negative differences and exact ties retained; no significance test"}
    for m in manifest["models"]:
        if checks["strict_score_counts_by_model"][m["id"]] != m["score_complete"]:
            raise ValueError("Strict scoring count differs from manifest: " + m["id"])
    inventory = []
    for name in FROZEN_FILES:
        data = (input_dir / name).read_bytes()
        inventory.append({"path": "../all-models-latest-20260913/" + name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    inputs = {"source_commit": PUBLIC_COMMIT, "score_cutoff_utc": manifest["cutoff_utc"], "gemini_last_readonly_check_utc": CHECKED_GEMINI_UTC, "gemini_completion_changed_since_source_snapshot": False, "models": manifest["models"], "selection": "Explicit user requested six-model scope; scores inherited from frozen report, registered rerun groups unchanged", "inputs": inventory}
    outputs = {name: as_csv(rows, fields) for name, (fields, rows) in filtered.items()}
    outputs.update({"contrasts.csv": helper._csv(contrasts, helper.CONTRAST_FIELDS), "family_rankings.csv": helper._csv(rankings, helper.RANK_FIELDS), "rank_transitions.csv": helper._csv(transitions, helper.TRANSITION_FIELDS)})
    for system in ("expgym", "poolact"):
        outputs[f"main_{system}.csv"] = helper._csv(report.main_rows(system), (*helper.CORE_FIELDS, "display_value", "display_unit", "status"))
    outputs["README.zh.md"] = readme(report, helper, rankings, counts)
    outputs["DETAILS.zh.md"] = details(report, helper, rankings, transitions, counts)
    outputs["REPORT_INPUTS.json"] = as_json(inputs)
    outputs["REPORT_CHECKS.json"] = as_json(checks)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path(__file__).resolve().parent.parent / "all-models-latest-20260913")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--check", action="store_true", help="Compare generated bytes without writing files")
    args = parser.parse_args()
    outputs = build(args.input_dir)
    mismatches = []
    if not args.check:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        path = args.output_dir / name
        data = value.encode("utf-8")
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                mismatches.append(name)
        else:
            path.write_bytes(data)
    if mismatches:
        raise SystemExit("Mismatched outputs: " + ", ".join(mismatches))
    print(json.dumps({"mode": "check" if args.check else "write", "artifacts": len(outputs), "status": "ok"}))


if __name__ == "__main__":
    main()
