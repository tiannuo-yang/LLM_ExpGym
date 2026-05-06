"""Generate V10 experiment figures."""
import json
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = "budget_sweep_results/v10"
MODELS = ["dsv3", "gpt52", "gemini3", "haiku45", "qwen3max"]
MODEL_NAMES = {
    "dsv3": "DSV3",
    "gpt52": "GPT-5.2",
    "gemini3": "Gemini-3-Flash",
    "haiku45": "Haiku-4.5",
    "qwen3max": "Qwen3-Max",
}
MODES = ["free", "low", "high"]
MODE_LABELS = {"free": "non-EEI (0.0x)", "low": "EEI (0.3x)", "high": "EEI-extreme (1.0x)"}
COLORS = {"dsv3": "#1f77b4", "gpt52": "#ff7f0e", "gemini3": "#2ca02c", "haiku45": "#d62728", "qwen3max": "#9467bd"}
OUT_DIR = "docs/v10_figures"

# Oracle best/mean values for normalized gap score
# Loaded from oracle3.json; keys use underscore format matching trace filenames
def _load_oracle_values():
    oracle_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "hpo_tuning", "oracle3.json",
    )
    with open(oracle_path) as f:
        data = json.load(f)
    result = {}
    for task_key, task_data in data["tasks"].items():
        # Convert colon-separated task key to underscore format used in filenames
        fname_key = task_key.replace(":", "_").replace("/", "_")
        result[fname_key] = {
            "best": task_data["best_perf"],
            "mean": task_data["mean_perf"],
        }
    return result

ORACLE_VALUES = _load_oracle_values()

os.makedirs(OUT_DIR, exist_ok=True)


def load_traces(models=None):
    models = models or MODELS
    results = []
    for model in models:
        for mode in MODES:
            trace_dir = os.path.join(BASE, "%s_%s" % (model, mode), "traces")
            if not os.path.isdir(trace_dir):
                continue
            for fn in sorted(os.listdir(trace_dir)):
                if not fn.endswith(".json"):
                    continue
                with open(os.path.join(trace_dir, fn)) as fh:
                    data = json.load(fh)
                if fn.startswith("tuning"):
                    scenario = "tuning"
                elif fn.startswith("restricted_search"):
                    scenario = "search"
                elif fn.startswith("evidence_audit"):
                    scenario = "audit"
                else:
                    continue
                results.append({
                    "model": model, "mode": mode, "scenario": scenario,
                    "perf": data.get("answer_perf"),
                    "evals": data.get("evaluations"),
                    "aborted": data.get("aborted", False),
                    "file": fn, "answer": data.get("answer", ""),
                    "steps": data.get("steps", []),
                })
    return results


def compute_audit_detail(results):
    """Compute label_acc, evidence_acc, verification_eff for audit traces."""
    sys.path.insert(0, ".")
    from expgym.task_evidence_audit import build_answer_evaluator
    audit_metrics = []
    for r in results:
        if r["scenario"] != "audit":
            continue
        parts = r["file"].replace(".json", "").split("_")
        doc_idx = int(parts[3])
        evaluator = build_answer_evaluator(doc_idx, "cc-large")
        tool_records = []
        if isinstance(r["steps"], list):
            for msg in r["steps"]:
                if isinstance(msg, str) and msg.startswith("Action: human_feedback"):
                    arg = msg.replace("Action: human_feedback ", "").strip()
                    tool_records.append(("human_feedback", arg, None))
        m = evaluator(r["answer"], tool_records)
        m["model"] = r["model"]
        m["mode"] = r["mode"]
        audit_metrics.append(m)
    return audit_metrics


def mean(vals):
    return sum(vals) / len(vals) if vals else None


def get_task_name(fn):
    return fn.replace("tuning_", "").split("_m3")[0]


def to_pct_oracle(perf, task_name):
    """Convert raw performance to normalized gap score (0=mean, 100=oracle)."""
    vals = ORACLE_VALUES.get(task_name)
    if vals:
        gap = vals["best"] - vals["mean"]
        if gap > 0:
            return (perf - vals["mean"]) / gap * 100.0
    return perf * 100.0


def fig1_tuning_grouped_bar(results):
    """Grouped bar chart: Tuning %oracle by model x mode."""
    tuning = [r for r in results if r["scenario"] == "tuning"]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(MODELS))
    width = 0.25

    for i, mode in enumerate(MODES):
        vals = []
        for model in MODELS:
            perfs = []
            for r in tuning:
                if r["model"] == model and r["mode"] == mode and r["perf"] is not None:
                    task = get_task_name(r["file"])
                    perfs.append(to_pct_oracle(r["perf"], task))
            vals.append(mean(perfs) if perfs else 0)
        ax.bar(x + i * width, vals, width, label=MODE_LABELS[mode],
               color=["#4CAF50", "#FF9800", "#F44336"][i], alpha=0.85)

    ax.set_ylabel("%Oracle", fontsize=12)
    ax.set_title("Tuning Performance (%Oracle)", fontsize=14)
    ax.set_xticks(x + width)
    ax.set_xticklabels([MODEL_NAMES[m] for m in MODELS], fontsize=11)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 105)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig1_tuning_pct_oracle.png"), dpi=150)
    plt.close()
    print("Saved fig1_tuning_pct_oracle.png")


def fig2_tuning_per_task(results):
    """Per-task tuning %oracle breakdown."""
    tuning = [r for r in results if r["scenario"] == "tuning"]
    tasks = sorted(set(get_task_name(r["file"]) for r in tuning))

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    task_short = {
        "hpobench_nasbench101_C": "NAS-101:C",
        "hpobench_nasbench201_imagenet16-120": "NAS-201:ImgNet",
        "hpobench_paramnet_letter_steps": "ParamNet:Letter",
    }

    for ti, task in enumerate(tasks):
        ax = axes[ti]
        x = np.arange(len(MODELS))
        width = 0.25
        for i, mode in enumerate(MODES):
            vals = []
            for model in MODELS:
                perfs = [to_pct_oracle(r["perf"], task) for r in tuning
                         if r["model"] == model and r["mode"] == mode
                         and task in r["file"] and r["perf"] is not None]
                vals.append(mean(perfs) if perfs else 0)
            ax.bar(x + i * width, vals, width, label=MODE_LABELS[mode] if ti == 0 else "",
                   color=["#4CAF50", "#FF9800", "#F44336"][i], alpha=0.85)

        ax.set_title(task_short.get(task, task), fontsize=12)
        ax.set_xticks(x + width)
        ax.set_xticklabels([MODEL_NAMES[m] for m in MODELS], fontsize=9, rotation=15)
        ax.set_ylim(0, 105)
        ax.grid(axis="y", alpha=0.3)
        if ti == 0:
            ax.set_ylabel("%Oracle", fontsize=11)

    axes[0].legend(fontsize=9)
    plt.suptitle("Per-Task Tuning Performance (%Oracle)", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig2_tuning_per_task.png"), dpi=150)
    plt.close()
    print("Saved fig2_tuning_per_task.png")


def fig3_search_bar(results):
    """Search F1 grouped bar chart."""
    search = [r for r in results if r["scenario"] == "search"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    x = np.arange(len(MODELS))
    width = 0.25

    # F1 scores
    for i, mode in enumerate(MODES):
        vals = []
        for model in MODELS:
            perfs = [r["perf"] for r in search if r["model"] == model and r["mode"] == mode and r["perf"] is not None]
            vals.append(mean(perfs) * 100 if perfs else 0)
        ax1.bar(x + i * width, vals, width, label=MODE_LABELS[mode],
                color=["#4CAF50", "#FF9800", "#F44336"][i], alpha=0.85)

    ax1.set_ylabel("F1 (%)", fontsize=12)
    ax1.set_title("Search Accuracy (F1)", fontsize=13)
    ax1.set_xticks(x + width)
    ax1.set_xticklabels([MODEL_NAMES[m] for m in MODELS], fontsize=10)
    ax1.legend(fontsize=9)
    ax1.set_ylim(0, 55)
    ax1.grid(axis="y", alpha=0.3)

    # Abort rates
    for i, mode in enumerate(MODES):
        vals = []
        for model in MODELS:
            total = len([r for r in search if r["model"] == model and r["mode"] == mode])
            aborted = sum(1 for r in search if r["model"] == model and r["mode"] == mode and r["aborted"])
            vals.append(100 * aborted / total if total else 0)
        ax2.bar(x + i * width, vals, width, label=MODE_LABELS[mode],
                color=["#4CAF50", "#FF9800", "#F44336"][i], alpha=0.85)

    ax2.set_ylabel("Abort Rate (%)", fontsize=12)
    ax2.set_title("Search Abort Rate", fontsize=13)
    ax2.set_xticks(x + width)
    ax2.set_xticklabels([MODEL_NAMES[m] for m in MODELS], fontsize=10)
    ax2.set_ylim(0, 100)
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig3_search_f1_abort.png"), dpi=150)
    plt.close()
    print("Saved fig3_search_f1_abort.png")


def fig4_audit_metrics(results, audit_metrics):
    """Audit label_acc, evidence_acc, verification_eff as line plot."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    metric_names = ["label_acc", "evidence_acc", "verification_eff"]
    metric_titles = ["Label Accuracy", "Evidence Accuracy", "Verification Efficiency"]

    x_pos = [0, 1, 2]  # free, low, high

    for mi, (metric, title) in enumerate(zip(metric_names, metric_titles)):
        ax = axes[mi]
        for model in MODELS:
            vals = []
            for mode in MODES:
                m_vals = [m[metric] for m in audit_metrics
                          if m["model"] == model and m["mode"] == mode and m[metric] is not None]
                vals.append(mean(m_vals) * 100 if m_vals else None)
            # Plot as line
            valid = [(x, v) for x, v in zip(x_pos, vals) if v is not None]
            if valid:
                xs, vs = zip(*valid)
                ax.plot(xs, vs, "o-", color=COLORS[model], label=MODEL_NAMES[model],
                        linewidth=2, markersize=8)

        ax.set_title(title, fontsize=13)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(["non-EEI", "EEI", "EEI-ext"], fontsize=10)
        ax.set_ylabel("%" if mi == 0 else "", fontsize=11)
        ax.set_ylim(0, 105)
        ax.grid(alpha=0.3)
        if mi == 0:
            ax.legend(fontsize=9)

    plt.suptitle("Audit Metrics by EEI Mode", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig4_audit_metrics.png"), dpi=150)
    plt.close()
    print("Saved fig4_audit_metrics.png")


def fig5_eval_counts(results):
    """Avg eval counts by scenario and mode."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    scenario_names = [("tuning", "Tuning"), ("search", "Search"), ("audit", "Audit")]

    for si, (sc, sc_title) in enumerate(scenario_names):
        ax = axes[si]
        sc_data = [r for r in results if r["scenario"] == sc]
        x_pos = [0, 1, 2]

        for model in MODELS:
            vals = []
            for mode in MODES:
                evals = [r["evals"] for r in sc_data if r["model"] == model and r["mode"] == mode and r["evals"] is not None]
                vals.append(mean(evals) if evals else 0)
            ax.plot(x_pos, vals, "o-", color=COLORS[model], label=MODEL_NAMES[model],
                    linewidth=2, markersize=8)

        ax.set_title(sc_title, fontsize=13)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(["non-EEI", "EEI", "EEI-ext"], fontsize=10)
        ax.set_ylabel("Avg Evaluations" if si == 0 else "", fontsize=11)
        ax.grid(alpha=0.3)
        if si == 0:
            ax.legend(fontsize=9)

    plt.suptitle("Average Evaluations by EEI Mode", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig5_eval_counts.png"), dpi=150)
    plt.close()
    print("Saved fig5_eval_counts.png")


def fig6_cross_scenario_summary(results, audit_metrics):
    """Heatmap: model x scenario, averaged across modes."""
    fig, ax = plt.subplots(figsize=(8, 5))

    tuning = [r for r in results if r["scenario"] == "tuning"]
    search = [r for r in results if r["scenario"] == "search"]

    data = np.zeros((len(MODELS), 4))
    col_labels = ["Tuning\n(%Oracle)", "Search\n(F1%)", "Audit\n(Label%)", "Audit\n(Evidence%)"]

    for mi, model in enumerate(MODELS):
        # Tuning: %oracle
        t_vals = []
        for r in tuning:
            if r["model"] == model and r["perf"] is not None:
                task = get_task_name(r["file"])
                t_vals.append(to_pct_oracle(r["perf"], task))
        data[mi, 0] = mean(t_vals) if t_vals else 0

        # Search F1
        s_vals = [r["perf"] * 100 for r in search if r["model"] == model and r["perf"] is not None]
        data[mi, 1] = mean(s_vals) if s_vals else 0

        # Audit label
        a_label = [m["label_acc"] * 100 for m in audit_metrics if m["model"] == model]
        data[mi, 2] = mean(a_label) if a_label else 0

        # Audit evidence
        a_evid = [m["evidence_acc"] * 100 for m in audit_metrics if m["model"] == model]
        data[mi, 3] = mean(a_evid) if a_evid else 0

    im = ax.imshow(data, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
    ax.set_xticks(range(4))
    ax.set_xticklabels(col_labels, fontsize=10)
    ax.set_yticks(range(len(MODELS)))
    ax.set_yticklabels([MODEL_NAMES[m] for m in MODELS], fontsize=11)

    for i in range(len(MODELS)):
        for j in range(4):
            ax.text(j, i, "%.1f" % data[i, j], ha="center", va="center",
                    fontsize=11, fontweight="bold",
                    color="white" if data[i, j] > 60 else "black")

    plt.colorbar(im, ax=ax, label="%")
    ax.set_title("Cross-Scenario Summary (all modes averaged)", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig6_cross_scenario_heatmap.png"), dpi=150)
    plt.close()
    print("Saved fig6_cross_scenario_heatmap.png")


if __name__ == "__main__":
    results = load_traces()
    print("Loaded %d traces" % len(results))
    audit_metrics = compute_audit_detail(results)
    print("Computed %d audit detail metrics" % len(audit_metrics))

    fig1_tuning_grouped_bar(results)
    fig2_tuning_per_task(results)
    fig3_search_bar(results)
    fig4_audit_metrics(results, audit_metrics)
    fig5_eval_counts(results)
    fig6_cross_scenario_summary(results, audit_metrics)
    print("\nAll figures saved to %s/" % OUT_DIR)
