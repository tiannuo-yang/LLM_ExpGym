#!/usr/bin/env python3
"""Reproduce the four report figures using frozen, public metric tables only.

Custom study; descriptive results, not new experiments or significance tests.
Usage: python plot_paper.py --output-dir OUTPUT --formats svg pdf png
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "metrics/unified_settings.csv": "d2d86592e8cbbc530fd0a6fe20bc0e2a69a767909169777b4b2ea8ca006b7fdc",
    "metrics/scaling_positions.csv": "8f3c0ecc3ae63d8d29b2f3a6f48ecc7e93047b8368c5de9b800846464a29be76",
}
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
METHODS = ("naive", "cached", "peer_context", "graph_no_lock", "poolact")
COLORS = dict(zip(METHODS, ("#666666", "#0072B2", "#56B4E9", "#E69F00", "#D55E00")))
LOW, MAX = "#0072B2", "#D55E00"
PANEL_SPECS = (
    ("restricted_search", "F1", "Search", "F1 (%)"),
    ("evidence_audit", "EA", "Audit", "EA (%)"),
    ("tuning", "Gap", "HPO", "Gap (points)"),
)


def read_inputs():
    loaded = {}
    for name, expected in INPUTS.items():
        content = (ROOT / name).read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError(f"Frozen input changed: {name}")
        with (ROOT / name).open(newline="") as stream:
            loaded[name] = list(csv.DictReader(stream))
    return loaded


def pick(rows, **criteria):
    matches = [r for r in rows if all(r[k] == str(v) for k, v in criteria.items())]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one setting: {criteria}")
    r = matches[0]
    if r["missing_items"] != "0" or r["missing_units"] != "0" or not r["mean"]:
        raise ValueError("A complete endpoint is required; never fill unknown scores")
    value = float(r["mean"]) * (100 if r["unit"] == "fraction" else 1)
    if not math.isfinite(value):
        raise ValueError("Nonfinite metric")
    return r, value


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9,
        "axes.titlesize": 10, "axes.titleweight": "semibold",
        "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "legend.frameon": False,
        "axes.linewidth": .65, "axes.edgecolor": "#444444",
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.major.width": .65, "ytick.major.width": .65,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "path", "svg.hashsalt": "glm-followups-paper-v2",
        "hatch.linewidth": .45, "savefig.facecolor": "white",
    })


def clean_axis(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#E4E4E4", linewidth=.55)
    ax.tick_params(pad=3)


def record(data, chart, panel, row, value, *, n=None, derivation="published aggregate"):
    data.append({
        "figure": chart, "panel": panel, "scenario": row["scenario"],
        "regime": row["regime"], "series": row["strategy"] if chart in
        ("audit_scaling_EA_MV", "tight_N4_ablation") else row["cohort"],
        "reported_agents": n if n is not None else row["reported_agents"],
        "source_metric": row["metric"], "display_value": format(value, ".15g"),
        "display_unit": "percent" if row["unit"] == "fraction" else "points",
        "expected_items": row["expected_items"], "expected_units": row["expected_units"],
        "source": "metrics/unified_settings.csv", "source_group": row["study_group"],
        "source_cohort": row["cohort"], "source_agents": row["reported_agents"],
        "derivation": derivation,
    })


def scaling(rows, positions, data):
    name = "audit_scaling_EA_MV"
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=True)
    specs = (("naive", "o", (0, (4, 2))), ("cached", "s", (0, (2, 1))),
             ("poolact", "^", "-"))
    for panel, ax, regime in zip(("a", "b"), axes, REGIMES[1:]):
        for method, marker, line in specs:
            ns, ys = [], []
            if method == "naive":
                r, val = pick(rows, study_group="scaling", scenario="evidence_audit",
                              regime=regime, strategy=method, reported_agents=8, metric="EA_MI")
                pool_rows = [p for p in positions if p["regime"] == regime
                             and p["strategy"] == "naive" and p["reported_agents"] == "8"]
                if len(pool_rows) != 13 or len({p["item"] for p in pool_rows}) != 13:
                    raise ValueError("N1 derivation requires all 13 unique N8 pools")
                singleton_mean = sum(json.loads(p["metrics"])["EA_MI"] for p in pool_rows) / 13 * 100
                if not math.isclose(singleton_mean, val, abs_tol=1e-10):
                    raise ValueError("Singleton mean disagrees with frozen N8 MI")
                ns.append(1); ys.append(val)
                record(data, name, panel, r, val, n=1,
                       derivation="individual-agent mean from naive N8 EA_MI; 13 documents x 8 agents; no singleton re-vote")
            for n in (2, 4, 6, 8):
                r, val = pick(rows, study_group="scaling", scenario="evidence_audit",
                              regime=regime, strategy=method, reported_agents=n, metric="EA_MV")
                ns.append(n); ys.append(val)
                record(data, name, panel, r, val)
            ax.plot(ns, ys, color=COLORS[method], marker=marker, linestyle=line,
                    markersize=4.3, linewidth=1.5, markeredgewidth=.7,
                    markerfacecolor="white" if method != "poolact" else COLORS[method],
                    label={"naive": "Naive (N=1: MI)", "cached": "Cached", "poolact": "PoolAct"}[method])
            ax.annotate(f"{ys[-1]:.1f}", (8, ys[-1]), xytext=(6, 0),
                        textcoords="offset points", va="center", color=COLORS[method], fontsize=8)
        r, val = pick(rows, study_group="thinking_same_version", scenario="evidence_audit",
                      regime=regime, strategy="single", effort="max", metric="EA")
        ax.plot([1], [val], marker="D", markersize=4.6, markerfacecolor="white",
                markeredgecolor="#222222", linestyle="none", label="ExpGym N=1 (ref.)", zorder=5)
        record(data, name, panel, r, val,
               derivation="separate ExpGym Max reference; 13 documents x 3 orders; not a shared curve anchor")
        ax.set(title=f"({panel}) {'Moderate' if panel == 'a' else 'Tight'}",
               xlabel="Number of agents, N", xlim=(.6, 9.1), ylim=(50, 104),
               xticks=[1, 2, 4, 6, 8], yticks=[50, 60, 70, 80, 90, 100])
        clean_axis(ax)
    axes[0].set_ylabel("Evidence accuracy (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.53, 1.005),
               ncol=4, columnspacing=1.3, handlelength=2.2, handletextpad=.5)
    fig.subplots_adjust(left=.085, right=.98, bottom=.17, top=.78, wspace=.14)
    return name, fig


def thinking(rows, data, historical=False):
    name = "thinking_low_new_max_rescored" if historical else "thinking_same_version"
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.8))
    cohorts = ("same_version_low", "historical") if historical else ("same_version_low", "same_version_max")
    for panel, ax, (scenario, metric, title, ylabel) in zip("abc", axes, PANEL_SPECS):
        for i, regime in enumerate(REGIMES):
            for shift, effort, cohort, color, hatch in zip((-.19, .19), ("low", "max"),
                                                          cohorts, (LOW, MAX), ("", "///")):
                group = "thinking_historical_reference" if cohort == "historical" else "thinking_same_version"
                r, val = pick(rows, study_group=group, scenario=scenario, regime=regime,
                              effort=effort, cohort=cohort, metric=metric)
                ax.bar(i+shift, val, width=.34, color=color, alpha=.92,
                       edgecolor="white", linewidth=.5, hatch=hatch, zorder=3)
                record(data, name, panel, r, val)
        ax.set(title=f"({panel}) {title}", ylabel=ylabel, ylim=(0, 111),
               yticks=[0, 25, 50, 75, 100], xticks=[0, 1, 2],
               xticklabels=["Free", "Mod.", "Tight"], xlim=(-.6, 2.6))
        clean_axis(ax)
    labels = ("Low (current)", "Max (historical; rescored)") if historical else ("Low", "Max (same version)")
    fig.legend(handles=[Patch(facecolor=LOW, label=labels[0]),
                        Patch(facecolor=MAX, edgecolor="white", hatch="///", label=labels[1])],
               loc="upper center", bbox_to_anchor=(.53, 1.005), ncol=2,
               columnspacing=2, handlelength=1.7)
    fig.subplots_adjust(left=.07, right=.995, bottom=.13, top=.77, wspace=.48)
    return name, fig


def ablation(rows, data):
    name = "tight_N4_ablation"
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9))
    specs = (("restricted_search", "F1_MV", "Whois", "F1-MV (%)", 37, [0, 10, 20, 30]),
             ("evidence_audit", "EA_MV", "Audit", "EA-MV (%)", 105, [0, 25, 50, 75, 100]),
             ("tuning", "Gap_MI", "NAS101", "Gap-MI (points)", 108, [0, 25, 50, 75, 100]))
    for panel, ax, (scenario, metric, title, ylabel, top, ticks) in zip("abc", axes, specs):
        for i, (method, hatch) in enumerate(zip(METHODS, ("", "//", "..", "\\\\", ""))):
            r, val = pick(rows, study_group="ablation", scenario=scenario, metric=metric,
                          strategy=method, reported_agents=4, regime="cost_tight")
            ax.bar(i, val, width=.68, color=COLORS[method], edgecolor="white",
                   hatch=hatch, linewidth=.6, zorder=3)
            ax.annotate(f"{val:.1f}", (i, val), xytext=(0, 3),
                        textcoords="offset points", ha="center", fontsize=8,
                        fontweight="bold" if method == "poolact" else "normal")
            record(data, name, panel, r, val)
        ax.set(title=f"({panel}) {title}", ylabel=ylabel, ylim=(0, top), yticks=ticks,
               xticks=range(5), xticklabels=["Naive", "Cache", "Peer", "Graph", "PoolAct"])
        plt.setp(ax.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor")
        clean_axis(ax)
    fig.subplots_adjust(left=.075, right=.995, bottom=.22, top=.88, wspace=.48)
    return name, fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--formats", nargs="+", choices=("svg", "pdf", "png"), default=["svg"])
    args = parser.parse_args()
    if matplotlib.__version__ != "3.9.4":
        raise ValueError("Reproduce with matplotlib 3.9.4")
    loaded = read_inputs()
    rows = loaded["metrics/unified_settings.csv"]
    if len(rows) != 210:
        raise ValueError("Expected the frozen 210-setting table")
    style()
    data = []
    figures = [scaling(rows, loaded["metrics/scaling_positions.csv"], data),
               thinking(rows, data), ablation(rows, data), thinking(rows, data, historical=True)]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name, fig in figures:
        fig.canvas.draw()
        for ext in args.formats:
            path = args.output_dir / f"{name}.{ext}"
            metadata = {"Date": None} if ext == "svg" else {
                "CreationDate": None, "ModDate": None} if ext == "pdf" else {}
            fig.savefig(path, dpi=300, metadata=metadata)
            outputs.append(path)
        plt.close(fig)
    table = args.output_dir / "PLOT_DATA.csv"
    with table.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader(); writer.writerows(data)
    outputs.append(table)
    manifest = {
        "schema": "glm-followups.paper-figures.v2", "matplotlib": matplotlib.__version__,
        "width_inches": 7.0, "minimum_text_points": 8.0,
        "new_model_calls": 0, "new_scoring_calls": 0, "raw_files_read": 0,
        "statistical_scope": "descriptive means; no independent-repeat confidence intervals",
        "inputs": [{"path": k, "sha256": v, "bytes": (ROOT/k).stat().st_size} for k,v in INPUTS.items()],
        "generator": {"path": "reproduce/plot_paper.py", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "plotted_values": len(data),
        "files": [{"path": p.name, "bytes": p.stat().st_size,
                   "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in outputs],
    }
    (args.output_dir/"FIGURE_INDEX.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"figures": len(figures), "values": len(data), "formats": args.formats}))


if __name__ == "__main__":
    main()
