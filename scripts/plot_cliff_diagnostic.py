"""Plot diagnostic evidence from audit and search (Figure in Appendix).

Two panels:
(a) Audit: label accuracy (solid) vs evidence accuracy (dashed) across 3 cost regimes.
(b) Search: F1 across 3 cost regimes (35 whois+whatis questions).

All 6 models shown.

Outputs:
- paper2/figures/fig3_cliff_v12.pdf
"""
from __future__ import annotations

import json
import glob
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
V16 = os.path.join(ROOT, "budget_sweep_results", "v16")
V17 = os.path.join(ROOT, "budget_sweep_results", "v17")

MODELS = ["dsv32", "gpt52", "gpt41", "gemini3", "haiku45", "mistral"]
MODEL_LABELS = {
    "dsv32": "DSV3.2", "gpt52": "GPT-5.2", "gpt41": "GPT-4.1",
    "gemini3": "Gemini-3", "haiku45": "Haiku-4.5", "mistral": "Mistral",
}
MODES = ["noneei", "eei", "eei_extreme"]
MODE_LABELS = ["Cost-Free", "Cost-Moderate", "Cost-Tight"]

COLORS = {
    "dsv32": "#2ca02c", "gpt52": "#ff7f0e", "gpt41": "#d62728",
    "gemini3": "#9467bd", "haiku45": "#1f77b4", "mistral": "#8c564b",
}


def load_traces(base_dir, model, mode, prefix):
    d = os.path.join(base_dir, f"{model}_{mode}", "traces")
    if not os.path.isdir(d):
        return []
    traces = []
    for fp in sorted(glob.glob(os.path.join(d, f"{prefix}*.json"))):
        traces.append(json.load(open(fp)))
    return traces


# ── AUDIT DATA ──────────────────────────────────────────────────────
audit_label = defaultdict(list)   # (model, mode) -> [label_acc]
audit_evid = defaultdict(list)    # (model, mode) -> [evidence_acc]

for model in MODELS:
    for mode in MODES:
        traces = load_traces(V16, model, mode, "evidence_audit_")
        for t in traces:
            p = t.get("answer_perf")
            if p is not None:
                audit_label[(model, mode)].append(p)
            am = t.get("answer_metrics") or {}
            ea = am.get("evidence_acc")
            if ea is not None:
                audit_evid[(model, mode)].append(ea)

# ── SEARCH DATA ─────────────────────────────────────────────────────
search_f1 = defaultdict(list)  # (model, mode) -> [f1]

for model in MODELS:
    for mode in MODES:
        traces = load_traces(V17, model, mode, "restricted_search_")
        # whois + whatis only (exclude howmany)
        for t in traces:
            p = t.get("answer_perf")
            if p is not None:
                search_f1[(model, mode)].append(p)

# ── PLOT ────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

x = np.arange(len(MODES))

# Panel (a): Audit — label (solid) and evidence (dashed)
for model in MODELS:
    label_means = [np.mean(audit_label[(model, m)]) if audit_label[(model, m)] else 0
                   for m in MODES]
    evid_means = [np.mean(audit_evid[(model, m)]) if audit_evid[(model, m)] else 0
                  for m in MODES]
    color = COLORS[model]
    ax1.plot(x, label_means, "-o", color=color, linewidth=2, markersize=6,
             label=MODEL_LABELS[model])
    ax1.plot(x, evid_means, "--s", color=color, linewidth=1.5, markersize=5,
             alpha=0.7)

ax1.set_xticks(x)
ax1.set_xticklabels(MODE_LABELS, fontsize=10)
ax1.set_ylabel("Accuracy", fontsize=11)
ax1.set_title("(a) Audit: Label (solid) vs Evidence (dashed)", fontsize=12,
              fontweight="bold")
ax1.legend(fontsize=8, loc="lower left", ncol=2)
ax1.set_ylim(0.3, 1.0)
ax1.grid(axis="y", alpha=0.3)

# Panel (b): Search — F1
for model in MODELS:
    # Filter: gpt41 only has whois+whatis (35 Qs), others have 55
    # For consistency, count what we have
    f1_means = [np.mean(search_f1[(model, m)]) if search_f1[(model, m)] else 0
                for m in MODES]
    color = COLORS[model]
    ax2.plot(x, f1_means, "-o", color=color, linewidth=2, markersize=6,
             label=MODEL_LABELS[model])

ax2.set_xticks(x)
ax2.set_xticklabels(MODE_LABELS, fontsize=10)
ax2.set_ylabel("F1", fontsize=11)
ax2.set_title("(b) Search (whois+whatis)", fontsize=12, fontweight="bold")
ax2.legend(fontsize=8, loc="upper right", ncol=2)
ax2.set_ylim(0, 0.75)
ax2.grid(axis="y", alpha=0.3)

plt.tight_layout()
out = os.path.join(ROOT, "paper2", "figures", "fig3_cliff_v12.pdf")
plt.savefig(out, bbox_inches="tight", dpi=150)
print(f"Saved: {out}")

# Print data for verification
print("\nAudit label accuracy:")
for model in MODELS:
    vals = [f"{np.mean(audit_label[(model, m)]):.3f}" if audit_label[(model, m)] else "---"
            for m in MODES]
    print(f"  {MODEL_LABELS[model]:>10}: {', '.join(vals)}")

print("\nAudit evidence accuracy:")
for model in MODELS:
    vals = [f"{np.mean(audit_evid[(model, m)]):.3f}" if audit_evid[(model, m)] else "---"
            for m in MODES]
    print(f"  {MODEL_LABELS[model]:>10}: {', '.join(vals)}")

print("\nSearch F1:")
for model in MODELS:
    vals = [f"{np.mean(search_f1[(model, m)]):.3f}" if search_f1[(model, m)] else "---"
            for m in MODES]
    n = len(search_f1[(model, MODES[0])])
    print(f"  {MODEL_LABELS[model]:>10}: {', '.join(vals)} (n={n})")
