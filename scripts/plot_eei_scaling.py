"""Plot EEI interactions vs performance scatter (Figure 3 in paper).

Three subplots: Search (whois, F1), Audit (evidence acc), Tuning (NB101:A running BoK).
Each point is one (agent, task) observation; performance is normalized within each
(model, task) pair to control for difficulty and capability.
Trend lines: linear regression.

Outputs:
- paper2/figures/fig_eei_scaling.pdf
"""
from __future__ import annotations

import json
import glob
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
    "font.size": 11,
    "mathtext.default": "regular",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

ROOT = os.path.join(os.path.dirname(__file__), "..")
V16 = os.path.join(ROOT, "budget_sweep_results", "v16")
V17 = os.path.join(ROOT, "budget_sweep_results", "v17")
ORACLE_PATH = os.path.join(ROOT, "data", "hpo_tuning", "oracle3.json")

MODELS = ["dsv32", "gpt52", "gpt41", "gemini3", "haiku45", "mistral"]
MODES = ["noneei", "eei", "eei_extreme"]

with open(ORACLE_PATH) as f:
    ORACLE = json.load(f)["tasks"]


def gap_score(perf, task_name):
    if task_name not in ORACLE:
        return None
    v = ORACLE[task_name]
    best, mean = v["best_perf"], v["mean_perf"]
    if best == mean:
        return 0
    return (perf - mean) / (best - mean) * 100


def normalize_within_group(xs, ys, groups):
    """Within-(model, question/task) normalization: subtract group mean.

    Groups with <2 observations or range <0.02 are excluded
    (no cross-mode variation to normalize).
    """
    group_vals = defaultdict(list)
    for x, y, g in zip(xs, ys, groups):
        if y is not None:
            group_vals[g].append((x, y))

    norm_xs, norm_ys = [], []
    for g, vals in group_vals.items():
        if len(vals) < 2:
            continue
        ys_g = [v[1] for v in vals]
        rng = max(ys_g) - min(ys_g)
        if rng < 0.02:
            continue
        mean = np.mean(ys_g)
        for x, y in vals:
            norm_xs.append(x)
            norm_ys.append(y - mean)
    return norm_xs, norm_ys


# ── SEARCH ──────────────────────────────────────────────────────────
# Use whois only (18 Qs × 6 models × 3 modes)
search_xs, search_ys, search_groups = [], [], []
for model in MODELS:
    for mode in MODES:
        d = os.path.join(V17, f"{model}_{mode}", "traces")
        if not os.path.isdir(d):
            continue
        for fp in sorted(glob.glob(os.path.join(d, "restricted_search_phantom_seed1_*"))):
            bn = os.path.basename(fp)
            if "whatis" in bn or "howmany" in bn:
                continue
            t = json.load(open(fp))
            perf = t.get("answer_perf")
            evals = t.get("evaluations", 0)
            if perf is None:
                continue
            # Group by (model, question) — normalize across modes
            q_key = bn.split("_m")[0]
            group = (model, q_key)
            search_xs.append(evals)
            search_ys.append(perf)
            search_groups.append(group)

search_nx, search_ny = normalize_within_group(
    search_xs, search_ys, search_groups
)

# ── AUDIT ───────────────────────────────────────────────────────────
audit_xs, audit_ys, audit_groups = [], [], []
for model in MODELS:
    for mode in MODES:
        d = os.path.join(V16, f"{model}_{mode}", "traces")
        if not os.path.isdir(d):
            continue
        for fp in sorted(glob.glob(os.path.join(d, "evidence_audit_*"))):
            t = json.load(open(fp))
            am = t.get("answer_metrics") or {}
            ea = am.get("evidence_acc")
            evals = t.get("evaluations", 0)
            if ea is None:
                continue
            bn = os.path.basename(fp)
            q_key = bn.split("_m")[0]
            group = (model, q_key)
            audit_xs.append(evals)
            audit_ys.append(ea)
            audit_groups.append(group)

audit_nx, audit_ny = normalize_within_group(
    audit_xs, audit_ys, audit_groups
)

# ── TUNING (running best-of-k within each trace) ────────────────────
# NB101:A only. Each eval step within a trace contributes one point.
# Skip invalid configs (perf=0) in the running best.
tuning_xs, tuning_ys, tuning_groups = [], [], []
for model in MODELS:
    for mode in MODES:
        d = os.path.join(V16, f"{model}_{mode}", "traces")
        if not os.path.isdir(d):
            continue
        for fp in sorted(glob.glob(os.path.join(d, "tuning_*nasbench101_A*"))):
            t = json.load(open(fp))
            msgs = t.get("messages", [])

            # Extract per-eval performance from observations
            eval_perfs = []
            for m in msgs:
                if isinstance(m, dict) and m.get("role") == "user":
                    content = m.get("content", "")
                elif isinstance(m, str):
                    content = m
                else:
                    continue
                if "perf=" in content and "over-budget" not in content:
                    try:
                        ps = content.split("perf=")[1].split(",")[0].split(" ")[0]
                        pv = float(ps.rstrip("."))
                        eval_perfs.append(pv)
                    except (ValueError, IndexError):
                        continue

            if not eval_perfs:
                continue

            bn = os.path.basename(fp)
            q_key = bn.split("_m")[0]
            group = (model, q_key)

            # Running best-of-k; skip invalid (perf=0) for gap score
            best_so_far = 0.0
            valid_k = 0
            for p in eval_perfs:
                if p <= 0:
                    continue  # invalid architecture, skip
                valid_k += 1
                best_so_far = max(best_so_far, p)
                gs = gap_score(best_so_far, "hpobench:nasbench101:A")
                if gs is not None and gs >= 0:
                    tuning_xs.append(valid_k)
                    tuning_ys.append(gs)
                    tuning_groups.append(group)

tuning_nx, tuning_ny = normalize_within_group(
    tuning_xs, tuning_ys, tuning_groups
)

# ── PLOT ────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 3.8))

# Paper teal (#068d9d from main.tex cFree/cBlue) — unified across panels
SCATTER_COLOR = "#068d9d"
TREND_COLOR = "#04524d"

datasets = [
    (search_nx, search_ny, "Search (whois)", "# Costly Interactions",
     "Normalized F1", "search"),
    (audit_nx, audit_ny, "Audit", "# Costly Interactions",
     "Normalized Evidence Acc", "audit"),
    (tuning_nx, tuning_ny, "Tuning (NB101:A)", "# Costly Interactions",
     "Normalized Gap Score", "tuning"),
]

for ax, (xs, ys, title, xlabel, ylabel, scenario) in zip(axes, datasets):
    xs, ys = np.array(xs), np.array(ys)
    ax.scatter(xs, ys, alpha=0.45, s=18, color=SCATTER_COLOR,
               edgecolors="white", linewidths=0.3, zorder=2)

    # Linear regression + trend line
    if len(xs) > 2:
        slope, intercept, r_value, p_value, _ = stats.linregress(xs, ys)
        x_line = np.linspace(xs.min(), xs.max(), 100)
        ax.plot(x_line, slope * x_line + intercept, color=TREND_COLOR,
                linewidth=2.5, zorder=3,
                label=f"r = {r_value:.2f}, p < {p_value:.0e}")
        ax.legend(fontsize=10, loc="lower right", framealpha=0.9,
                  edgecolor="lightgray")

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--", zorder=1)
    ax.grid(alpha=0.12, zorder=0)
    ax.tick_params(labelsize=10)

plt.tight_layout(w_pad=2.5)
out = os.path.join(ROOT, "paper2", "figures", "fig_eei_scaling.pdf")
plt.savefig(out, bbox_inches="tight", dpi=200)
print(f"Saved: {out}")
print(f"Search: {len(search_nx)} pts, Audit: {len(audit_nx)}, Tuning: {len(tuning_nx)}")
