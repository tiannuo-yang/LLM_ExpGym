#!/usr/bin/env python3
"""Portable Whois report rebuild from frozen historical inputs + formal rescoring.

No model/scorer calls, raw trajectories, network, or original workspace paths
are needed for --check or --rebuild. Source staging additionally verifies the
formal rescoring receipt and 234 overlapping main-experiment scores.
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
import shutil

import frozen_aggregation as agg

HERE = Path(__file__).resolve().parent
MODELS = agg.MODELS
BETAS = agg.BETAS
NAMES = dict(gpt="GPT", kimi="Kimi", glm="GLM", qwen="Qwen", deepseek="DeepSeek", gemini="Gemini")
MODEL_IDS = dict(gpt="gpt-5.6-sol", kimi="kimi-k3", glm="glm-5.3", qwen="qwen3.8-2.4t-a95b-fp8", deepseek="deepseek-v4-flash-0731", gemini="gemini-3.8-flash-medium")
SCORE_FIELDS = {"mean_f1", "known_subset_mean_f1", "zero_score_items"}
VERSION = "formal_protocol_repair_v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_read(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def csv_bytes(rows, fields=None):
    require(bool(rows) or fields is not None, "empty CSV requires explicit fields")
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode()


def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def strings(row):
    return {k: "" if v is None else str(v) for k, v in row.items()}


def key(row):
    return row["model"], int(row["beta"]), row["data_source"], int(row["question_index"])


def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12)


def f1(value):
    result = float(value)
    require(math.isfinite(result) and 0 <= result <= 1, "invalid complete F1")
    return result


def check_source_receipt(rescored, baseline):
    checks = json.loads((rescored / "CHECKS.json").read_text())
    require(checks["schema"] == "expgym.whois-protocol-rescore.v1" and checks["passed"] is True, "not a passed formal sweep rescore")
    require(checks["new_scoring_status"] == VERSION and checks["diagnostic_scores_adopted"] is False, "diagnostic/unknown score version rejected")
    require(checks["code_hash_stable_during_replay"] is True and checks["code_files"] == checks["code_files_at_completion"], "scoring code changed during replay")
    require(checks["slots"] == checks["sources_hash_verified"] == checks["historical_scores_recomputed"] == 1170 and checks["main_overlap_slots"] == 234, "formal rescore coverage mismatch")
    require(checks["model_calls"] == checks["tool_calls"] == 0 and checks["all_original_trajectory_files_unchanged"] is True, "unexpected rescore side effects")
    for record in checks["output_files"]:
        require(sha(rescored / record["path"]) == record["sha256"], "formal rescore output SHA mismatch: " + record["path"])
    for name in ("PUBLIC_REPLAY_CHECK.json", "SCORE_REPLAY_CHECK.json"):
        replay = json.loads((rescored / name).read_text())
        require(replay["passed"] is True and replay["slots"] == 1170, "formal public score replay failed")
    source_hashes = {r["path"]: r["sha256"] for r in checks["input_files"]}
    for name in ("inputs/items.csv", "adoption_sources.csv", "aggregate_metrics.csv", "budget_differences.csv"):
        require(sha(baseline / name) == source_hashes["whois/" + name], "baseline differs from formal rescore input: " + name)
    return checks


def stage_inputs(args):
    require(not args.output.exists(), "output must be a new directory")
    checks = check_source_receipt(args.rescored, args.baseline)
    scores = csv_read(args.rescored / "agent_rows.csv")
    overlap_ids = {r["main_overlap_slot_id"] for r in scores if int(r["beta"]) == 10}
    require(len(overlap_ids) == 234 and "" not in overlap_ids, "wrong main overlap IDs")
    main_rows = [r for r in csv_read(args.main_scalars) if r["slot_id"] in overlap_ids]
    require(len(main_rows) == 234 and {r["slot_id"] for r in main_rows} == overlap_ids, "main rescore does not cover all beta10 slots")
    original_main_sha = next(r["sha256"] for r in checks["input_files"] if r["path"] == "main/SOURCE_SELECTION.csv")
    require(sha(args.main_sources) == original_main_sha, "historical main source index differs from formal rescore input")
    main_sources = [r for r in csv_read(args.main_sources) if r["slot_id"] in overlap_ids]
    require(len(main_sources) == 234 and {r["slot_id"] for r in main_sources} == overlap_ids, "historical main sources do not cover beta10")
    # This local path is only provenance. Portable replay reads the exact copied
    # 234-row projection and never follows any historical absolute source path.
    args.output.mkdir(parents=True)
    inputs = args.output / "inputs"
    inputs.mkdir()
    copy_specs = {
        "baseline_items.csv": args.baseline / "inputs/items.csv",
        "agents.csv": args.baseline / "inputs/agents.csv",
        "attempts.csv": args.baseline / "inputs/attempts.csv",
        "baseline_aggregate_metrics.csv": args.baseline / "aggregate_metrics.csv",
        "baseline_budget_differences.csv": args.baseline / "budget_differences.csv",
        "formal_score_rows.csv": args.rescored / "agent_rows.csv",
        "formal_aggregate_metrics.csv": args.rescored / "aggregate_metrics.csv",
        "formal_budget_differences.csv": args.rescored / "budget_differences.csv",
        "formal_rankings.csv": args.rescored / "rankings.csv",
        "runtime_counterfactual.csv": args.rescored / "runtime_counterfactual.csv",
        "rescore_checks.json": args.rescored / "CHECKS.json",
        "score_replay_check.json": args.rescored / "SCORE_REPLAY_CHECK.json",
        "rescore_public_replay_check.json": args.rescored / "PUBLIC_REPLAY_CHECK.json",
        "beta10_main_join_check.json": args.rescored / "BETA10_MAIN_JOIN_CHECK.json",
    }
    sources = []
    for target, source in copy_specs.items():
        shutil.copyfile(source, inputs / target)
        sources.append(dict(path="inputs/" + target, source_path=str(source.resolve()), sha256=sha(source), bytes=source.stat().st_size))
    (inputs / "main_beta10_scores.csv").write_bytes(csv_bytes(main_rows))
    sources.append(dict(path="inputs/main_beta10_scores.csv", source_path=str(args.main_scalars.resolve()), source_full_sha256=sha(args.main_scalars), sha256=sha(inputs / "main_beta10_scores.csv"), bytes=(inputs / "main_beta10_scores.csv").stat().st_size))
    (inputs / "main_beta10_sources.csv").write_bytes(csv_bytes(main_sources))
    sources.append(dict(path="inputs/main_beta10_sources.csv", source_path=str(args.main_sources.resolve()), source_full_sha256=original_main_sha, sha256=sha(inputs / "main_beta10_sources.csv"), bytes=(inputs / "main_beta10_sources.csv").stat().st_size))
    for name in ("provider_cohorts.csv", "adoption_sources.csv"):
        shutil.copyfile(args.baseline / name, args.output / name)
        sources.append(dict(path=name, source_path=str((args.baseline / name).resolve()), sha256=sha(args.output / name), bytes=(args.output / name).stat().st_size))
    for name in ("build_report.py", "frozen_aggregation.py", "plot_whois.py"):
        require((HERE / name).is_file(), "portable tool not ready: " + name)
        shutil.copyfile(HERE / name, args.output / name)
    manifest = dict(schema="expgym.whois-repaired-report.inputs.v1", source_report=str(args.baseline.resolve()), source_rescore=str(args.rescored.resolve()), scoring_version=VERSION, frozen_scoring_code=checks["code_files"], files=sources, model_calls=0, boundary="Saved formal F1 to report aggregation. Formal parser/scorer replay is separately evidenced in copied upstream receipts; this builder does not rescore answers.")
    (args.output / "INPUTS.json").write_bytes(json_bytes(manifest))


def validate_inputs(bundle):
    manifest = json.loads((bundle / "INPUTS.json").read_text())
    require(manifest["schema"] == "expgym.whois-repaired-report.inputs.v1" and manifest["scoring_version"] == VERSION, "wrong report input schema/version")
    for entry in manifest["files"]:
        path = bundle / entry["path"]
        require(path.stat().st_size == entry["bytes"] and sha(path) == entry["sha256"], "portable input SHA mismatch: " + entry["path"])
    return manifest


def summarize(items, agents, attempts):
    result = agg.summarize(items, agents, attempts)
    for row in result:
        if row["model"] == "gemini" and row["beta"] != 10:
            row["cohort"] = "new_openrouter_20260917"
    return result


def outputs(bundle):
    validate_inputs(bundle)
    inputs = bundle / "inputs"
    old_items, agents, attempts = [csv_read(inputs / name) for name in ("baseline_items.csv", "agents.csv", "attempts.csv")]
    old_aggregate = csv_read(inputs / "baseline_aggregate_metrics.csv")
    require([strings(r) for r in summarize(old_items, agents, attempts)] == old_aggregate, "historical aggregate replay mismatch")
    score_rows = csv_read(inputs / "formal_score_rows.csv")
    scores = {key(r): r for r in score_rows}
    expected = {(m, b, s, q) for m in MODELS for b in BETAS for s, q in agg.QUESTIONS}
    require(len(old_items) == len(score_rows) == len(scores) == 1170 and set(scores) == {key(r) for r in old_items} == expected, "1170-position matrix changed")
    require(len({r["slot_id"] for r in score_rows}) == 1170, "duplicate formal score slot")
    main = {r["slot_id"]: r for r in csv_read(inputs / "main_beta10_scores.csv")}
    require(len(main) == 234, "wrong main overlap projection")
    main_sources = {r["slot_id"]: r for r in csv_read(inputs / "main_beta10_sources.csv")}
    require(len(main_sources) == 234 and set(main_sources) == set(main), "main identity projection differs from new score projection")
    new_items, changes = [], []
    overlap_checked = 0
    for old in old_items:
        row = scores[key(old)]
        require(row["new_scoring_status"] == VERSION and row["old_scoring_status"] == "historical_adopted", "unapproved score version")
        require(close(f1(row["old_score"]), f1(old["f1"])), "score mismatch with historical input")
        if old["result_sha256"]:
            require(row["source_sha256"] == old["result_sha256"], "canonical source SHA mismatch with historical input")
        else:
            # Original five-model beta10 projection omitted result hashes.
            # Use its registered main slot, never an assumed or empty hash.
            require(int(row["beta"]) == 10 and row["model"] != "gemini", "unexpected missing historical result SHA")
        require(all(agg.truth(row[k]) for k in ("execution_complete", "old_score_complete", "new_score_complete")), "incomplete formal endpoint")
        require(agg.truth(old["execution_complete"]) and agg.truth(old["score_complete"]), "historical endpoint incomplete")
        new_score = f1(row["new_score"])
        require(close(new_score - f1(row["old_score"]), row["delta_score"]), "item delta mismatch")
        require(close(json.loads(row["new_metrics_json"])["f1"], new_score) and close(json.loads(row["old_metrics_json"])["f1"], row["old_score"]), "formal metric JSON mismatch")
        require(agg.truth(row["score_changed"]) == (not close(row["old_score"], new_score)), "formal score change flag mismatch")
        if int(row["beta"]) == 10:
            source = main[row["main_overlap_slot_id"]]
            original_main = main_sources[row["main_overlap_slot_id"]]
            require(original_main["result_sha256"] == row["source_sha256"] and all(original_main[k] == source[k] for k in ("slot_id", "model", "system", "scenario", "regime", "item", "seed")), "main/sweep original canonical identity mismatch")
            require(source["model"] == MODEL_IDS[row["model"]] and source["system"] == "expgym" and source["scenario"] == "restricted_search" and source["regime"] == "cost_moderate" and source["family"] == "whois", "beta10 main setting mismatch")
            require(source["item"] == row["data_source"] + ":" + row["question_index"], "beta10 main question mismatch")
            require(agg.truth(source["execution_complete"]) and agg.truth(source["score_complete"]) and close(json.loads(source["metrics_json"])["f1"], new_score), "beta10 main/sweep new F1 mismatch")
            overlap_checked += 1
        else:
            require(row["main_overlap_slot_id"] == "", "non-beta10 row incorrectly overlaps main")
        # Preserve every historical item field except the explicitly versioned
        # score. Original result SHA continues to identify the unmodified trace.
        new_items.append({**old, "f1": str(new_score)})
        changes.append(dict(model=row["model"], beta=int(row["beta"]), data_source=row["data_source"], question_index=int(row["question_index"]), slot_id=row["slot_id"], main_overlap_slot_id=row["main_overlap_slot_id"], source_sha256=row["source_sha256"], old_f1=f1(row["old_score"]), new_f1=new_score, delta_f1=new_score - f1(row["old_score"]), answer_changed=agg.truth(row["answer_changed"]), score_changed=agg.truth(row["score_changed"]), old_missing_final=agg.truth(row["old_missing_final"]), new_missing_final=agg.truth(row["new_missing_final"]), extraction_source=row["extraction_source"], reason=row["reason"], score_version=VERSION))
    require(overlap_checked == 234, "not all beta10 scores checked against main")
    new_aggregate = summarize(new_items, agents, attempts)
    old_by = {(r["model"], int(r["beta"])): r for r in old_aggregate}
    new_by = {(r["model"], r["beta"]): r for r in new_aggregate}
    formal_by = {(r["model"], int(r["beta"])): r for r in csv_read(inputs / "formal_aggregate_metrics.csv")}
    grouped = defaultdict(list)
    for row in changes:
        grouped[row["model"], row["beta"]].append(row)
    comparison, rankings = [], []
    cost_fields_checked = 0
    for k, row in new_by.items():
        before = old_by[k]
        for field, value in row.items():
            if field not in SCORE_FIELDS:
                require(strings({field: value})[field] == before[field], "historical cost/execution projection changed: " + field)
                cost_fields_checked += 1
        require(close(row["mean_f1"], formal_by[k]["new_mean_f1"]), "independent formal mean mismatch")
        selected = grouped[k]
        comparison.append(dict(model=k[0], beta=k[1], expected_items=39, old_mean_f1=float(before["mean_f1"]), new_mean_f1=row["mean_f1"], delta_f1=row["mean_f1"] - float(before["mean_f1"]), changed_questions=sum(r["score_changed"] for r in selected), answer_changed_questions=sum(r["answer_changed"] for r in selected), old_missing_final_items=sum(r["old_missing_final"] for r in selected), new_missing_final_items=sum(r["new_missing_final"] for r in selected), main_overlap_items=39 if k[1] == 10 else 0, score_version=VERSION))
    for beta in BETAS:
        for model in MODELS:
            k = model, beta
            old_val, new_val = float(old_by[k]["mean_f1"]), new_by[k]["mean_f1"]
            old_rank = 1 + sum(float(old_by[m, beta]["mean_f1"]) > old_val + 1e-12 for m in MODELS)
            new_rank = 1 + sum(new_by[m, beta]["mean_f1"] > new_val + 1e-12 for m in MODELS)
            rankings.append(dict(beta=beta, model=model, old_rank=old_rank, new_rank=new_rank, old_mean_f1=old_val, new_mean_f1=new_val))
    formal_ranks = csv_read(inputs / "formal_rankings.csv")
    require(len(formal_ranks) == 30, "formal rank count mismatch")
    for actual, expected_rank in zip(rankings, formal_ranks):
        require(all(str(actual[k]) == expected_rank[k] for k in ("beta", "model", "old_rank", "new_rank")), "independent formal rank mismatch")
    differences, difference_changes = [], []
    old_diffs = {(r["model"], int(r["target_beta"])): r for r in csv_read(inputs / "baseline_budget_differences.csv")}
    formal_diffs = {(r["model"], int(r["target_beta"])): r for r in csv_read(inputs / "formal_budget_differences.csv")}
    require(len(old_diffs) == len(formal_diffs) == 24, "budget difference denominator mismatch")
    for model in MODELS:
        for beta in (1, 5, 10, 15):
            delta = new_by[model, beta]["mean_f1"] - new_by[model, 20]["mean_f1"]
            old = old_diffs[model, beta]
            require(close(old["mean_f1_difference"], float(old_by[model, beta]["mean_f1"]) - float(old_by[model, 20]["mean_f1"])), "historical budget difference mismatch")
            require(close(formal_diffs[model, beta]["new_mean_f1_difference"], delta), "independent formal budget difference mismatch")
            differences.append({**old, "mean_f1_difference": str(delta)})
            difference_changes.append(dict(model=model, baseline_beta=20, target_beta=beta, paired_expected=39, old_difference_f1=float(old["mean_f1_difference"]), new_difference_f1=delta, delta_difference_f1=delta - float(old["mean_f1_difference"]), historical_cohort_comparison=beta == 10))
    changed = [r for r in changes if r["answer_changed"] or r["score_changed"]]
    checks = dict(schema="expgym.whois-repaired-report.checks.v1", passed=True, slots=1170, endpoint_rows=30, questions_per_endpoint=39, budget_difference_rows=24, rank_rows=30, main_overlap_rows_verified=overlap_checked, additional_nonoverlap_slots=936, changed_answer_items=sum(r["answer_changed"] for r in changes), changed_score_items=sum(r["score_changed"] for r in changes), changed_endpoint_means=sum(not close(r["old_mean_f1"], r["new_mean_f1"]) for r in comparison), changed_rank_positions=sum(r["old_rank"] != r["new_rank"] for r in rankings), historical_nonscore_aggregate_fields_unchanged=cost_fields_checked, historical_agent_rows_preserved=len(agents), historical_attempt_rows_preserved=len(attempts), original_item_nonscore_fields_preserved=True, score_version=VERSION, model_calls=0, task_scorer_calls=0, boundary="Aggregates rebuilt from formal saved F1. Costs and runtime behavior remain historical; offline reparse is not a new rollout.")
    result = {"inputs/items.csv": csv_bytes(new_items), "aggregate_metrics.csv": csv_bytes(new_aggregate), "budget_differences.csv": csv_bytes(differences), "old_vs_new_metrics.csv": csv_bytes(comparison), "old_vs_new_budget_differences.csv": csv_bytes(difference_changes), "rankings.csv": csv_bytes(rankings), "item_changes.csv": csv_bytes(changes), "affected_samples.csv": csv_bytes(changed, list(changes[0])), "CHECKS.json": json_bytes(checks)}
    result["README.zh.md"] = readme(new_by, comparison, checks).encode()
    return result


def readme(new_by, comparison, checks):
    lines = ["# 六模型 Whois N1：统一终答协议后的全量重评分", "", f"本版使用正式 `{VERSION}` 对全部 **1,170** 个既有位置的重评分结果重建分析。六模型 × β=1/5/10/15/20 × 39 题，N1、R1，分母不变；本报告构建没有新增模型调用，也没有改写原轨迹或旧报告。", "", f"共有 **{checks['changed_answer_items']}** 项最终答案提取变化、**{checks['changed_score_items']}** 项 F1 变化；30 个模型×预算均值中 **{checks['changed_endpoint_means']}** 个变化，30 个排名位置中 **{checks['changed_rank_positions']}** 个变化。答案文字变化不必然改变 F1。", "", "| 模型 | β1 | β5 | β10（历史） | β15 | β20 |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for model in MODELS:
        lines.append("| " + " | ".join([NAMES[model], *[f"{100 * new_by[model, beta]['mean_f1']:.2f}" for beta in BETAS]]) + " |")
    lines += ["", "表中为逐题 F1 等权平均 ×100；CSV 保存 0–1 原值。每格 39/39 已评分；有效零分保留，不用已知子集代替完整均值。排名采用并列竞争排名，绝对差不超过 1e-12 视为并列。", "", "## 与旧版的逐格差异", "", "| 模型 | β | 旧 F1×100 | 新 F1×100 | 差值（百分点） | 分数变化题数 | 提取变化题数 |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in comparison:
        lines.append(f"| {NAMES[r['model']]} | {r['beta']} | {100*r['old_mean_f1']:.2f} | {100*r['new_mean_f1']:.2f} | {100*r['delta_f1']:+.2f} | {r['changed_questions']} | {r['answer_changed_questions']} |")
    lines += ["", "[逐题新旧分数](item_changes.csv) · [变化样本](affected_samples.csv) · [全部新旧均值](old_vs_new_metrics.csv) · [排名](rankings.csv) · [相对 β20 差值](budget_differences.csv) · [预算差值新旧对照](old_vs_new_budget_differences.csv)", "", "## 来源与比较范围", "", "β=10 的 **234** 个位置与主实验 N1 Moderate 完全重叠；已通过 `main_overlap_slot_id` 将原件身份及新 F1 逐项连接。跨主实验和 sweep 计数时，sweep 仅额外贡献 **936** 个位置，不能再把 β10 计算一遍。公开输入保留这 234 条主实验分数投影。", "", "Gemini 的 β1/5/15/20 沿用 OpenRouter `google/gemini-3.8-flash` 的既有轨迹，β10 沿用历史 Sub2 Gemini native 轨迹。这是不同提供方/日期执行结果的描述性比较，不是同一部署只改变预算的实验。其他模型也保留原部署与代码版本边界。此次统一解析器重评分不能消除历史运行输入和交互路径的差异。", "", "首次8个 Gemini sweep 结果仍对应原执行后的离线导出恢复；其余148个仍对应 schema 修复后的首次执行。两批执行/导出源码身份保留在 [adoption_sources.csv](adoption_sources.csv)，没有重新运行这156项。", "", "β×300 为模拟反馈预算秒数，即300/1500/3000/4500/6000秒；seed2200、最多30步/30评价，N4 不进入该报告。姓名级 F1 的 gold 与计算公式未改；本版接入的是正式统一提取器的全量分数，不是抽查修正或诊断分数。", "", "## 成本与行为边界", "", "[agents.csv](inputs/agents.csv) 与 [attempts.csv](inputs/attempts.csv) 保持旧文件原字节。所有已发表 token、请求次数、模拟反馈费用、运行时长和原运行协议事件均照旧；历史 β10 的请求/token/wall time 未知仍为空，不能记零。Gemini 原8项的模型执行 wall time 未记录，仍为未知。", "", "`aggregate_metrics.csv` 中 `missing_final_agents`、`protocol_affected_agents` 描述原运行事件；新的离线终答是否缺失见 `old_vs_new_metrics.csv` 的 `old_missing_final_items` / `new_missing_final_items`。重解析可能改变最终答案，不意味着原运行会在同一步停止；运行路径的反事实差异由统一重评分交付另列，不伪造新的调用量或成本。", "", "## 图表", "", "![修复后六模型预算曲线](figures/whois_six_model_budget.png)", "", "[PDF](figures/whois_six_model_budget.pdf) · [SVG](figures/whois_six_model_budget.svg)", "", "![新旧分数变化](figures/whois_rescoring_delta.png)", "", "[变化图 PDF](figures/whois_rescoring_delta.pdf) · [变化图 SVG](figures/whois_rescoring_delta.svg)", "", "β10 用历史轨迹标记；跨历史点的连线保留虚线。图表全部从本版正式 CSV 重新生成；来源 SHA 与绘图脚本版本见 `figures/PROVENANCE.json`。", "", "## 公开回放", "", "本目录包含最小聚合输入，不依赖私有 raw、原工作目录或网络：", "", "```bash", "python3 -B build_report.py --bundle . --check", "python3 -B build_report.py --bundle . --rebuild /path/to/new-empty-output", "python3 -B plot_whois.py --bundle . --output-dir /path/to/new-empty-figures --source-version formal_protocol_repair_v1", "```", "", "前两条仅需 Python 标准库；绘图使用 matplotlib。聚合回放核验全部1,170项、234个主实验连接、30个均值/排名、24个预算差值及成本字段不变。正式 parser/scorer 从原终答文本到 F1 的全量回放由独立重评分工具负责，其源码 SHA 和回放收据复制在 `inputs/rescore_checks.json`、`inputs/score_replay_check.json`；本聚合器不冒充再次执行评分器。", "", "[输入身份](INPUTS.json) · [检查结果](CHECKS.json) · [正式逐题评分投影](inputs/formal_score_rows.csv) · [Gemini 提供方](provider_cohorts.csv)", ""]
    return "\n".join(lines)


def write_outputs(bundle, expected, check=False):
    for relative, raw in expected.items():
        path = bundle / relative
        if check:
            require(path.is_file() and path.read_bytes() == raw, "derived file mismatch: " + relative)
        else:
            require(not path.exists(), "derived output already exists: " + relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", type=Path)
    p.add_argument("--rescored", type=Path)
    p.add_argument("--main-scalars", type=Path)
    p.add_argument("--main-sources", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--bundle", type=Path, default=HERE)
    p.add_argument("--check", action="store_true")
    p.add_argument("--rebuild", type=Path)
    args = p.parse_args()
    if args.check:
        require(args.rebuild is None and args.output is None, "choose one mode")
        write_outputs(args.bundle, outputs(args.bundle), check=True)
        print(json.dumps(dict(passed=True, slots=1170, aggregates=30, main_overlap=234, comparisons=24, mode="portable_check", raw_or_network_access=False)))
    elif args.rebuild:
        require(not args.rebuild.exists() and args.output is None, "rebuild destination must be new")
        validate_inputs(args.bundle)
        args.rebuild.mkdir(parents=True)
        shutil.copytree(args.bundle / "inputs", args.rebuild / "inputs", ignore=shutil.ignore_patterns("items.csv"))
        for name in ("INPUTS.json", "provider_cohorts.csv", "adoption_sources.csv", "build_report.py", "frozen_aggregation.py", "plot_whois.py"):
            shutil.copyfile(args.bundle / name, args.rebuild / name)
        write_outputs(args.rebuild, outputs(args.rebuild))
        print(json.dumps(dict(passed=True, mode="portable_rebuild", destination=str(args.rebuild))))
    else:
        require(all((args.baseline, args.rescored, args.main_scalars, args.main_sources, args.output)), "staging requires --baseline, --rescored, --main-scalars, --main-sources, --output")
        stage_inputs(args)
        expected = outputs(args.output)
        write_outputs(args.output, expected)
        print(expected["CHECKS.json"].decode())


if __name__ == "__main__":
    main()
