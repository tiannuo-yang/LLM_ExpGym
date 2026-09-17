#!/usr/bin/env python3
"""Create standalone plots from a complete six-model report's aggregate CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--output-dir", type=Path)
    args = p.parse_args()
    aggregate = args.bundle / "aggregate_metrics.csv"
    with aggregate.open(newline="") as f:
        rows = list(csv.DictReader(f))
    models = ("gpt", "kimi", "glm", "qwen", "deepseek", "gemini")
    betas = (1, 5, 10, 15, 20)
    by = {(r["model"], int(r["beta"])): r for r in rows}
    if len(rows) != 30 or set(by) != {(m, b) for m in models for b in betas}:
        raise ValueError("plot needs exactly six models by five budgets")
    for r in rows:
        if int(r["score_known"]) != 39 or int(r["expected_items"]) != 39 or not r["mean_f1"]:
            raise ValueError("plot requires complete 39/39 endpoints")
        score = float(r["mean_f1"])
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("invalid F1")
    output = args.output_dir or args.bundle / "figures"
    output.mkdir(parents=True, exist_ok=True)
    targets = [output / ("whois_six_model_budget." + ext) for ext in ("png", "pdf", "svg")]
    if any(path.exists() for path in targets):
        raise ValueError("plot files are create-only")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    names = dict(gpt="GPT", kimi="Kimi", glm="GLM", qwen="Qwen", deepseek="DeepSeek", gemini="Gemini")
    colors = dict(gpt="#0072B2", kimi="#009E73", glm="#CC79A7", qwen="#E69F00", deepseek="#666666", gemini="#D33132")
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(10.5, 6.4))
    fig.subplots_adjust(left=0.09, right=0.77, bottom=0.23, top=0.85)
    for model in models:
        values = {b: 100*float(by[model, b]["mean_f1"]) for b in betas}
        c, width = colors[model], 2.8 if model == "gemini" else 1.7
        order = 5 if model == "gemini" else 3
        for start, end in zip(betas, betas[1:]):
            ax.plot([start, end], [values[start], values[end]], color=c, lw=width, ls="--" if 10 in (start, end) else "-", alpha=0.94, zorder=order)
        new = (1, 5, 15, 20)
        ax.scatter(new, [values[b] for b in new], color=c, s=43 if model == "gemini" else 31, marker="o", zorder=order+1)
        ax.scatter([10], [values[10]], facecolor="white", edgecolor=c, linewidth=2.0, s=75 if model == "gemini" else 56, marker="D", zorder=order+2)
    ax.set_xlim(0.4, 20.6)
    ax.set_ylim(0, 100)
    ax.set_xticks(betas)
    ax.set_xlabel(r"Feedback budget multiplier $\beta$ (300 simulated seconds per unit)")
    ax.set_ylabel("Mean question F1 × 100")
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    model_handles = [Line2D([0], [0], color=colors[m], lw=2.8 if m == "gemini" else 1.7, marker="o", label=names[m]) for m in models]
    legend = ax.legend(handles=model_handles, loc="upper left", bbox_to_anchor=(1.025, 1.03), frameon=False, title="Model")
    ax.add_artist(legend)
    ax.legend(handles=[Line2D([0], [0], color="#333333", marker="D", markerfacecolor="white", ls="--", lw=1.4, label="Historical β=10"), Line2D([0], [0], color="#333333", marker="o", ls="-", lw=1.4, label="New sweep points")], loc="upper left", bbox_to_anchor=(1.025, 0.45), frameon=False, fontsize=9.5)
    fig.suptitle("Whois N1: six models across feedback budgets", x=0.09, y=0.965, ha="left", fontsize=16, fontweight="bold")
    fig.text(0.09, 0.902, "39 identical questions per point · one agent · one repetition · complete endpoint means", ha="left", fontsize=10.5, color="#444444")
    fig.text(0.09, 0.115, "All β=10 points reuse historical results; dashed segments cross historical cohorts.", fontsize=10, color="#333333")
    fig.text(0.09, 0.076, "Gemini: β=1/5/15/20 via OpenRouter; β=10 via Sub2. No β=10 experiment was rerun.", fontsize=10, color="#333333")
    fig.text(0.09, 0.037, "Curves describe these execution cohorts; they do not isolate a budget-only causal effect.", fontsize=10, color="#333333")
    for path in targets:
        fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)
    provenance = {"schema": "expgym.whois-six-model-figure.v1", "aggregate_path": str(aggregate.resolve()), "aggregate_sha256": hashlib.sha256(aggregate.read_bytes()).hexdigest(), "endpoint_count": 30, "questions_per_endpoint": 39, "historical_betas": [10], "missing_points_plotted_as_zero": False, "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "files": [{"path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in targets]}
    (output / "PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"written": [str(p) for p in targets], "endpoints": 30}))


if __name__ == "__main__":
    main()
