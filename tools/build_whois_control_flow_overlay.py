#!/usr/bin/env python3
"""Re-score 1170 saved Whois inputs, then adopt the registered new GLM run.

Public, portable input only: no original trajectories, Git history, API calls,
Parquet or workspace-specific paths. The single control is adopted regardless
of its score; its actual attempt and behavior rows replace the old execution.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
TARGET = "whois:glm:beta20:phantom_seed2:5:R1"
VERSION = "formal_protocol_runtime_control_v1"
MODELS = ("gpt", "kimi", "glm", "qwen", "deepseek", "gemini")
BETAS = (1, 5, 10, 15, 20)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_read(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def csv_write(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def json_write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n")


def number(value):
    return None if value in (None, "", "null", "None") else float(value)


def close(a, b):
    return a is b if a is None or b is None else math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12)


def key(row):
    return row["model"], int(row["beta"]), row["data_source"], int(row["question_index"])


def plots_for(output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"svg.hashsalt": VERSION, "svg.fonttype": "none", "pdf.fonttype": 42})
    rows = {(r["model"], int(r["beta"])): r for r in csv_read(output / "aggregate_metrics.csv")}
    changes = {(r["model"], int(r["beta"])): r for r in csv_read(output / "old_vs_new_metrics.csv")}
    directory = output / "figures"
    directory.mkdir()
    fig, ax = plt.subplots(figsize=(10.5, 6.7))
    for model in MODELS:
        ax.plot(BETAS, [100 * float(rows[model, b]["mean_f1"]) for b in BETAS], marker="o", label=model)
    ax.set(xticks=BETAS, ylim=(0, 100), xlabel="Feedback budget multiplier beta", ylabel="Mean question F1 × 100")
    ax.legend(ncol=3)
    ax.grid(axis="y", alpha=.25)
    fig.suptitle("Whois N1: formal scores after protocol repair and runtime control")
    fig.text(.09, .025, "1,169 existing executions + 1 new GLM beta20 control; 39 questions per point.\n"
             "Beta10 reuses 234 main-report traces; Gemini beta10 Sub2, other betas OpenRouter.", fontsize=9)
    fig.tight_layout(rect=(0, .085, 1, .94))
    written = []
    def save(figure, name):
        for extension in ("png", "pdf", "svg"):
            p = directory / f"{name}.{extension}"
            metadata = {"Date": None} if extension == "svg" else {"CreationDate": None, "ModDate": None} if extension == "pdf" else None
            figure.savefig(p, dpi=220, metadata=metadata)
            written.append(p)
        plt.close(figure)
    save(fig, "whois_six_model_budget")
    values = [[100 * float(changes[m, b]["delta_f1"]) for b in BETAS] for m in MODELS]
    limit = max(1.0, max(abs(v) for r in values for v in r))
    fig, ax = plt.subplots(figsize=(9.5, 6.3))
    im = ax.imshow(values, vmin=-limit, vmax=limit, cmap="RdBu_r", aspect="auto")
    ax.set_xticks(range(5), BETAS); ax.set_yticks(range(6), MODELS)
    ax.set_xlabel("Feedback budget multiplier beta")
    for i, m in enumerate(MODELS):
        for j, b in enumerate(BETAS):
            ax.text(j, i, f"{values[i][j]:+.2f} pp\n{changes[m,b]['changed_questions']}/39", ha="center", va="center")
    fig.colorbar(im, ax=ax, label="Official − historical mean F1 (percentage points)")
    fig.suptitle("Whois: historical to official score changes")
    fig.text(.08, .025, "The existing-trace parser repair changed 0 F1 scores. This panel also includes the one new runtime control.\n"
             "Actual new execution costs are recorded separately; no hypothetical cost savings are substituted.", fontsize=9)
    fig.tight_layout(rect=(0, .08, 1, .94))
    save(fig, "whois_runtime_delta")
    json_write(directory / "PROVENANCE.json", {"version": VERSION, "new_runtime_slots": 1, "existing_runtime_slots": 1169,
        "inputs": [{"path": n, "sha256": sha(output / n)} for n in ("aggregate_metrics.csv", "old_vs_new_metrics.csv")],
        "files": [{"path": p.name, "sha256": sha(p)} for p in written]})


def build_overlay(base_whois, existing_sweep, new_inputs, output, plots=False):
    for value in (base_whois, existing_sweep, new_inputs):
        assert value.exists(), str(value)
    assert not output.exists(), "Official overlay output must be a fresh directory"
    old_replay = module(REPO / "tools/rescore_whois_protocol.py", "_whois_old_true_replay")
    old_replay_checks = old_replay.replay_inputs(existing_sweep / "scoring_inputs.jsonl.gz", existing_sweep)
    assert old_replay_checks["new_scores_recomputed"] == 1170
    source_manifest = json.loads((base_whois / "INPUTS.json").read_text())
    for record in source_manifest["files"]:
        assert sha(base_whois / record["path"]) == record["sha256"]
    aggregate = module(base_whois / "frozen_aggregation.py", "_whois_runtime_frozen_aggregate")
    scorer = module(REPO / "tools/replay_control_flow_results.py", "_whois_new_true_scorer")
    with gzip.open(new_inputs, "rt") as f:
        controls = [json.loads(line) for line in f if line.strip()]
    assert len(controls) == 1 and controls[0]["slot"]["slot_id"] == TARGET
    control = controls[0]
    assert control["slot"]["system"] == "expgym" and control["slot"]["scenario"] == "restricted_search"
    assert control["slot"]["model"] == "glm-5.3" and control["slot"]["item"] == "phantom_seed2:5"
    assert control["slot"]["seed"] == "2200" and control["model_alias"] == "glm"
    assert control["source"]["parser_sha256"] == sha(REPO / "expgym/tool_protocol.py")
    new_scalar, new_members, new_diff, _ = scorer.score_slot(control)
    new_f1 = json.loads(new_scalar["metrics_json"])["f1"]
    scores = csv_read(existing_sweep / "agent_rows.csv")
    old_score = next(r for r in scores if r["slot_id"] == TARGET)
    assert old_score["main_overlap_slot_id"] == ""
    assert control["source"]["old_result_sha256"] == old_score["source_sha256"]
    assert close(json.loads(control["slot"]["metrics_json"])["f1"], old_score["new_score"])
    items = csv_read(base_whois / "inputs/items.csv")
    agents = csv_read(base_whois / "inputs/agents.csv")
    attempts = csv_read(base_whois / "inputs/attempts.csv")
    original_items = [dict(r) for r in items]
    assert len(items) == len(scores) == 1170
    by_key = {key(r): r for r in scores}
    assert all(close(r["f1"], by_key[key(r)]["new_score"]) for r in items)
    changed_item = next(r for r in items if key(r) == ("glm", 20, "phantom_seed2", 5))
    old_job = changed_item["job_id"]
    costs = control["whois_costs"]
    new_agent, new_attempts = costs["agent_row"], costs["attempt_rows"]
    assert costs["checks"]["passed"] is True
    assert costs["checks"]["trace_identity"]["sha256"] == control["source"]["result_sha256"]
    assert costs["checks"]["code_source_tree_sha256"] == control["source"]["runtime_source_tree_sha256"]
    assert new_agent["job_id"] == control["source"]["new_job_id"] != old_job
    assert key(new_agent) == ("glm", 20, "phantom_seed2", 5)
    assert all(a["job_id"] == new_agent["job_id"] and a["model"] == "glm" for a in new_attempts)
    assert len(new_attempts) == int(new_agent["http_request_attempts"])
    assert len({a["request_id"] for a in new_attempts}) == len(new_attempts)
    old_agents = [r for r in agents if r["model"] == "glm" and r["job_id"] == old_job]
    old_attempts = [r for r in attempts if r["model"] == "glm" and r["job_id"] == old_job]
    assert len(old_agents) == 1 and old_attempts
    agents = [r for r in agents if not (r["model"] == "glm" and r["job_id"] == old_job)] + [new_agent]
    attempts = [r for r in attempts if not (r["model"] == "glm" and r["job_id"] == old_job)] + new_attempts
    changed_item.update(f1=str(new_f1), job_id=control["source"]["new_job_id"],
        cohort="runtime_control_20260918", execution_cohort="first_registered_execution", source_input="new_runtime_control",
        source_tree_sha256=control["source"]["runtime_source_tree_sha256"],
        result_collection="protocol_repair_aux_controls_glm_20260918", result_member=control["source"]["result_path"],
        result_bytes=str(control["source"]["result_bytes"]), result_sha256=control["source"]["result_sha256"],
        status="completed", execution_complete="True", score_complete="True")
    assert sum(a != b for a, b in zip(items, original_items)) == 1
    summary = aggregate.summarize(items, agents, attempts)
    for r in summary:
        if r["model"] == "gemini" and r["beta"] != 10:
            r["cohort"] = "new_openrouter_20260917"
        if (r["model"], r["beta"]) == ("glm", 20):
            r["cohort"] = "mixed_existing_plus_runtime_control_20260918"
    previous = {(r["model"], int(r["beta"])): r for r in csv_read(base_whois / "aggregate_metrics.csv")}
    historical = {(r["model"], int(r["beta"])): r for r in csv_read(base_whois / "inputs/baseline_aggregate_metrics.csv")}
    now = {(r["model"], r["beta"]): r for r in summary}
    comparisons, ranks, differences, item_changes, scalar_rows, source_rows = [], [], [], [], [], []
    for r in scores:
        adopted = r["slot_id"] == TARGET
        final = new_f1 if adopted else float(r["new_score"])
        source_sha = control["source"]["result_sha256"] if adopted else r["source_sha256"]
        item_changes.append({"slot_id": r["slot_id"], "model": r["model"], "beta": r["beta"], "item": r["item"],
            "historical_f1": r["old_score"], "existing_trace_f1": r["new_score"], "official_f1": final,
            "score_changed_from_historical": not close(r["old_score"], final),
            "score_changed_from_existing_trace": not close(r["new_score"], final),
            "runtime_source_replaced": adopted, "old_source_sha256": r["source_sha256"], "official_source_sha256": source_sha,
            "main_overlap_slot_id": r["main_overlap_slot_id"], "source_layer": "new_runtime_control" if adopted else "existing_trace_rescored"})
        scalar_rows.append({"slot_id": r["slot_id"], "model": r["model"], "model_id": r["model_id"], "beta": r["beta"],
            "data_source": r["data_source"], "question_index": r["question_index"], "item": r["item"], "seed": r["seed"],
            "system": "expgym", "scenario": "restricted_search", "strategy": "single",
            "metrics_json": json.dumps({"f1": final}, sort_keys=True), "f1": final, "execution_complete": True,
            "score_complete": True, "source_sha256": source_sha, "main_overlap_slot_id": r["main_overlap_slot_id"],
            "score_layer": "new_runtime_control" if adopted else "existing_trace_rescored", "official_version": VERSION})
        source_rows.append({"slot_id": r["slot_id"], "model": r["model"], "beta": r["beta"], "item": r["item"],
            "old_source_sha256": r["source_sha256"], "result_sha256": source_sha,
            "source_path": control["source"]["result_path"] if adopted else r["source_path"],
            "new_job_id": control["source"]["new_job_id"] if adopted else "", "runtime_source_replaced": adopted,
            "main_overlap_slot_id": r["main_overlap_slot_id"], "adoption_rule": "registered_first_complete_execution_no_score_selection" if adopted else "preserved_existing_trace"})
    for m in MODELS:
        for b in BETAS:
            cur, old, prior = now[m, b], historical[m, b], previous[m, b]
            changed = sum(r["score_changed_from_historical"] for r in item_changes if r["model"] == m and int(r["beta"]) == b)
            comparisons.append({"model": m, "beta": b, "expected_items": 39, "old_mean_f1": float(old["mean_f1"]),
                "existing_trace_mean_f1": float(prior["mean_f1"]), "new_mean_f1": cur["mean_f1"],
                "delta_f1": cur["mean_f1"] - float(old["mean_f1"]), "changed_questions": changed,
                "runtime_replaced_questions": int(m == "glm" and b == 20), "score_version": VERSION})
            if (m, b) != ("glm", 20):
                assert all(("" if v is None else str(v)) == prior[k] for k, v in cur.items()), (m, b)
    for b in BETAS:
        for m in MODELS:
            old, new = float(historical[m, b]["mean_f1"]), now[m, b]["mean_f1"]
            ranks.append({"beta": b, "model": m, "old_rank": 1 + sum(float(historical[o,b]["mean_f1"]) > old + 1e-12 for o in MODELS),
                          "new_rank": 1 + sum(now[o,b]["mean_f1"] > new + 1e-12 for o in MODELS),
                          "old_mean_f1": old, "new_mean_f1": new})
    for m in MODELS:
        for b in (1, 5, 10, 15):
            old = float(historical[m,b]["mean_f1"]) - float(historical[m,20]["mean_f1"])
            new = now[m,b]["mean_f1"] - now[m,20]["mean_f1"]
            differences.append({"model": m, "baseline_beta": 20, "target_beta": b, "direction": "target minus beta20",
                "paired_expected": 39, "paired_known": 39, "old_mean_f1_difference": old,
                "mean_f1_difference": new, "delta_difference": new - old,
                "historical_cohort_comparison": b == 10, "provider_cohort_change": m == "gemini" and b == 10})
    main = {r["slot_id"]: r for r in csv_read(base_whois / "inputs/main_beta10_scores.csv")}
    overlap = [r for r in scalar_rows if r["main_overlap_slot_id"]]
    assert len(overlap) == 234
    for r in overlap:
        assert close(r["f1"], json.loads(main[r["main_overlap_slot_id"]]["metrics_json"])["f1"])
    behavior = [{"field": k, "old_value": old_agents[0].get(k), "new_value": new_agent.get(k),
                 "changed": str(old_agents[0].get(k)) != str(new_agent.get(k))}
                for k in ("missing_final", "http_request_attempts", "evaluations", "simulated_feedback_seconds",
                          "agent_wall_seconds", "protocol_failure_events")]
    for field in ("input_tokens", "output_tokens", "total_tokens", "reasoning_tokens", "cached_input_tokens"):
        old_vals, new_vals = [number(r[field]) for r in old_attempts], [number(r[field]) for r in new_attempts]
        old_sum, new_sum = sum(v for v in old_vals if v is not None), sum(v for v in new_vals if v is not None)
        behavior.extend([{"field": field + "_known_sum", "old_value": old_sum,
                          "new_value": new_sum, "changed": old_sum != new_sum},
                         {"field": field + "_unknown_attempts", "old_value": old_vals.count(None),
                          "new_value": new_vals.count(None), "changed": old_vals.count(None) != new_vals.count(None)}])
    output.mkdir(parents=True)
    (output / "inputs").mkdir()
    for name, rows in (("inputs/items.csv", items), ("inputs/agents.csv", agents), ("inputs/attempts.csv", attempts),
                       ("aggregate_metrics.csv", summary), ("old_vs_new_metrics.csv", comparisons),
                       ("budget_differences.csv", differences), ("rankings.csv", ranks), ("item_changes.csv", item_changes),
                       ("slot_scalars.csv", scalar_rows), ("SOURCE_SELECTION.csv", source_rows),
                       ("runtime_behavior_changes.csv", behavior), ("runtime_adoption_sources.csv", [control["source"]])):
        csv_write(output / name, rows)
    csv_write(output / "affected_samples.csv", [r for r in item_changes if r["runtime_source_replaced"] or r["score_changed_from_historical"]], list(item_changes[0]))
    for name in ("provider_cohorts.csv", "adoption_sources.csv"):
        shutil.copyfile(base_whois / name, output / name)
    shutil.copyfile(new_inputs, output / "inputs/runtime_control_scoring_inputs.jsonl.gz")
    checks = {"schema": "expgym.whois-runtime-overlay.v1", "passed": True, "version": VERSION, "slots": 1170,
        "existing_inputs_actually_rescored": 1170, "new_runtime_inputs_actually_rescored": 1,
        "runtime_replaced_slots": 1, "preserved_existing_slots": 1169, "main_overlap_slots_verified": 234,
        "additional_nonoverlap_slots": 936, "new_runtime_members": 1, "new_runtime_score": new_f1,
        "old_existing_trace_score": float(old_score["new_score"]),
        "changed_score_items": sum(r["score_changed_from_historical"] for r in item_changes),
        "changed_rank_positions": sum(r["old_rank"] != r["new_rank"] for r in ranks),
        "replaced_old_attempt_rows": len(old_attempts), "adopted_actual_new_attempt_rows": len(new_attempts),
        "replaced_actual_agent_cost_rows": 1, "cost_scope": "actual new saved attempts and trajectory behavior; unknown usage retained, no hypothetical early-stop cost subtraction",
        "model_calls_by_builder": 0, "new_results_selected_by_score": False,
        "parser_sha256": sha(REPO / "expgym/tool_protocol.py"), "builder_sha256": sha(Path(__file__)),
        "old_sweep_inputs_sha256": sha(existing_sweep / "scoring_inputs.jsonl.gz"), "new_inputs_sha256": sha(new_inputs),
        "old_report_inputs_sha256": sha(base_whois / "INPUTS.json")}
    json_write(output / "CHECKS.json", checks)
    json_write(output / "PUBLIC_REPLAY_CHECK.json", {**checks, "full_private_trace_access": False, "network_access": False})
    json_write(output / "BETA10_MAIN_JOIN_CHECK.json", {"passed": True, "overlap_slots": 234, "changed_overlap_sources": 0,
        "main_projection_sha256": sha(base_whois / "inputs/main_beta10_scores.csv")})
    text = ["# Whois：正式运行控制后的六模型预算分析", "",
        "本版保留原 1,170 个实验位置，对所有旧终答先重新评分，再无条件采用预注册的一个新 GLM β=20 运行。"
        "其余 1,169 个位置继续采用既有轨迹重评分结果。历史结果、旧轨迹修复评分、新运行正式采用三个层次分别保留。", "",
        f"新运行位置为 `{TARGET}`。该题旧/修复分数为 {float(old_score['new_score']):.6f}，新运行 F1 为 {new_f1:.6f}。"
        f"全表有 {checks['changed_score_items']} 个 F1、{checks['changed_rank_positions']} 个排名位置相对历史变化。", "",
        "| 模型 | β1 | β5 | β10 | β15 | β20 |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for m in MODELS:
        text.append("| " + m + " | " + " | ".join(f"{100*now[m,b]['mean_f1']:.2f}" for b in BETAS) + " |")
    text += ["", "数值为 F1×100，每点39题。β=10的234位置复用主实验，不能再算独立样本；其余936位置为独立预算实验。"
        "Gemini β=10来自历史Sub2，其他β来自OpenRouter，保留提供方/批次差异。", "",
        "旧轨迹全量终答修复原本导致2个提取文本变化、0个F1变化；本页的新运行变化应与该旧轨迹诊断分开解释。"
        "除GLM β=20及涉及它的排名/预算差值外，其余29个模型×预算设置的成绩和成本完全保留。", "",
        f"成本也替换成此次真实新运行：移除旧任务 {len(old_attempts)} 条attempt，采用新任务 {len(new_attempts)} 条attempt。"
        "所有重试和未知usage保持原义；详见 `runtime_behavior_changes.csv` 和 `inputs/agents.csv`、`inputs/attempts.csv`。", "",
        "复算：`tools/build_whois_control_flow_overlay.py --base-whois WHOIS_EXISTING_TRACE --existing-sweep RESCORE_SWEEP "
        "--new-inputs CONTROL_SWEEP/scoring_inputs.jsonl.gz --output NEW_DIR --plots`。该入口真实调用解析器及任务评分器，"
        "无需私有原件、Parquet、Git或网络；绘图另需matplotlib。"]
    (output / "README.zh.md").write_text("\n".join(text) + "\n")
    if plots:
        plots_for(output)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-whois", type=Path, required=True)
    parser.add_argument("--existing-sweep", type=Path, required=True)
    parser.add_argument("--new-inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plots", action="store_true")
    a = parser.parse_args()
    print(json.dumps(build_overlay(a.base_whois, a.existing_sweep, a.new_inputs, a.output, a.plots), indent=2))


if __name__ == "__main__":
    main()
