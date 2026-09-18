#!/usr/bin/env python3
"""Plot a complete, offline-rescored Whois sweep without executing experiments.

Example:
  python plot_whois.py --bundle /path/to/report --source-version repair-v1

The bundle must contain aggregate_metrics.csv and old_vs_new_metrics.csv.
The output directory (default: <bundle>/figures) must not already exist.
Only the Python standard library and matplotlib are required; no raw trajectories,
network access, API keys, or benchmark environment are needed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
from pathlib import Path
from typing import Any


GENERATOR_VERSION = "expgym.whois-protocol-repair-figures.v1"
MODELS = ("gpt", "kimi", "glm", "qwen", "deepseek", "gemini")
BETAS = (1, 5, 10, 15, 20)
QUESTIONS_PER_ENDPOINT = 39
NAMES = dict(gpt="GPT", kimi="Kimi", glm="GLM", qwen="Qwen", deepseek="DeepSeek", gemini="Gemini")
COLORS = dict(gpt="#0072B2", kimi="#009E73", glm="#CC79A7", qwen="#E69F00", deepseek="#666666", gemini="#D33132")
FORMATS = ("png", "pdf", "svg")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_endpoints(path: Path) -> dict[tuple[str, int], dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected = {(model, beta) for model in MODELS for beta in BETAS}
    indexed: dict[tuple[str, int], dict[str, str]] = {}
    for row in rows:
        key = (row["model"], int(row["beta"]))
        if key in indexed:
            raise ValueError(f"{path.name}: duplicate endpoint {key}")
        indexed[key] = row
    if len(rows) != 30 or set(indexed) != expected:
        raise ValueError(f"{path.name}: exactly six models by five budgets are required")
    return indexed


def finite_number(row: dict[str, str], field: str, lower: float, upper: float) -> float:
    value = float(row[field])
    if not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError(f"invalid {field} for {row['model']}, beta={row['beta']}: {value}")
    return value


def load_inputs(bundle: Path) -> tuple[dict, dict, dict]:
    aggregate_path = bundle / "aggregate_metrics.csv"
    comparison_path = bundle / "old_vs_new_metrics.csv"
    aggregate = read_endpoints(aggregate_path)
    comparison = read_endpoints(comparison_path)
    endpoints: dict[tuple[str, int], dict[str, Any]] = {}
    comparison_fields: dict[str, str] | None = None
    for key in aggregate:
        row, old_new = aggregate[key], comparison[key]
        if int(row["score_known"]) != QUESTIONS_PER_ENDPOINT or int(row["expected_items"]) != QUESTIONS_PER_ENDPOINT:
            raise ValueError(f"aggregate_metrics.csv: endpoint {key} must have 39/39 known scores")
        for field, expected_value in (("execution_complete", 39), ("score_unknown", 0)):
            if row.get(field, "") and int(row[field]) != expected_value:
                raise ValueError(f"aggregate_metrics.csv: invalid {field} at {key}")
        mean = finite_number(row, "mean_f1", 0, 1)
        old_mean = finite_number(old_new, "old_mean_f1", 0, 1)
        new_mean = finite_number(old_new, "new_mean_f1", 0, 1)
        # The aliases also permit use with the rescorer's standalone summary.
        delta_field = "delta_f1" if "delta_f1" in old_new else "delta_mean_f1"
        count_field = "changed_questions" if "changed_questions" in old_new else "score_changed_items"
        fields = {"delta": delta_field, "changed_questions": count_field}
        if comparison_fields is not None and comparison_fields != fields:
            raise ValueError("inconsistent comparison column names")
        comparison_fields = fields
        delta = finite_number(old_new, delta_field, -1, 1)
        changed = int(old_new[count_field])
        if not 0 <= changed <= QUESTIONS_PER_ENDPOINT:
            raise ValueError(f"old_vs_new_metrics.csv: invalid changed-question count at {key}")
        for field in ("expected_items", "old_score_known", "new_score_known"):
            if old_new.get(field, "") and int(old_new[field]) != QUESTIONS_PER_ENDPOINT:
                raise ValueError(f"old_vs_new_metrics.csv: incomplete {field} at {key}")
        if not math.isclose(new_mean, mean, rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"new score differs between input tables at {key}")
        if not math.isclose(delta, new_mean - old_mean, rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"old-to-new delta does not match endpoint means at {key}")
        if changed == 0 and not math.isclose(delta, 0, rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"nonzero delta with no changed questions at {key}")
        if abs(delta) > changed / QUESTIONS_PER_ENDPOINT + 1e-12:
            raise ValueError(f"delta exceeds the possible contribution of changed questions at {key}")
        endpoints[key] = {"old_mean_f1": old_mean, "new_mean_f1": new_mean, "delta_f1": delta, "changed_questions": changed}
    return endpoints, {"aggregate": aggregate_path, "old_vs_new": comparison_path}, comparison_fields or {}


def save_figure(fig: Any, output: Path, basename: str) -> list[Path]:
    written = []
    for extension in FORMATS:
        path = output / f"{basename}.{extension}"
        # Suppress timestamp metadata so the source version and hashes identify
        # the figure content without recording incidental render time.
        metadata = {"Date": None} if extension == "svg" else {"CreationDate": None, "ModDate": None} if extension == "pdf" else None
        fig.savefig(path, dpi=220, facecolor="white", metadata=metadata)
        written.append(path)
    return written


def budget_figure(plt: Any, endpoints: dict) -> Any:
    from matplotlib.lines import Line2D

    fig, ax = plt.subplots(figsize=(11.8, 7.2))
    fig.subplots_adjust(left=0.09, right=0.76, bottom=0.27, top=0.81)
    for model in MODELS:
        values = {beta: 100 * endpoints[model, beta]["new_mean_f1"] for beta in BETAS}
        color, width = COLORS[model], 2.8 if model == "gemini" else 1.7
        order = 5 if model == "gemini" else 3
        for start, end in zip(BETAS, BETAS[1:]):
            ax.plot([start, end], [values[start], values[end]], color=color, lw=width, ls="--" if 10 in (start, end) else "-", alpha=0.94, zorder=order)
        sweep_betas = (1, 5, 15, 20)
        ax.scatter(sweep_betas, [values[beta] for beta in sweep_betas], color=color, s=43 if model == "gemini" else 31, marker="o", zorder=order + 1)
        ax.scatter([10], [values[10]], facecolor="white", edgecolor=color, linewidth=2, s=75 if model == "gemini" else 56, marker="D", zorder=order + 2)
    ax.set(xlim=(0.4, 20.6), ylim=(0, 100), xticks=BETAS, ylabel="Mean question F1 × 100")
    ax.set_xlabel(r"Feedback budget multiplier $\beta$ (300 simulated seconds per unit)")
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    model_handles = [Line2D([0], [0], color=COLORS[model], lw=2.8 if model == "gemini" else 1.7, marker="o", label=NAMES[model]) for model in MODELS]
    legend = ax.legend(handles=model_handles, loc="upper left", bbox_to_anchor=(1.025, 1.03), frameon=False, title="Model")
    ax.add_artist(legend)
    ax.legend(handles=[Line2D([0], [0], color="#333333", marker="D", markerfacecolor="white", ls="--", lw=1.4, label="Historical β=10 traces"), Line2D([0], [0], color="#333333", marker="o", ls="-", lw=1.4, label="Existing sweep traces")], loc="upper left", bbox_to_anchor=(1.025, 0.43), frameon=False, fontsize=9.5)
    fig.suptitle("Whois N1: six models across feedback budgets", x=0.09, y=0.965, ha="left", fontsize=16, fontweight="bold")
    fig.text(0.09, 0.905, "Protocol-repaired offline rescoring", fontsize=12, color="#333333", fontweight="bold")
    fig.text(0.09, 0.86, "39 identical questions per point · one agent · one repetition · all 1,170 scores known", fontsize=10.5, color="#444444")
    fig.text(0.09, 0.145, "β=10 reuses 234 main-experiment trajectories; dashed segments cross historical cohorts.", fontsize=10, color="#333333")
    fig.text(0.09, 0.101, "Gemini: β=1/5/15/20 via OpenRouter; β=10 via Sub2. All trajectories are existing executions.", fontsize=10, color="#333333")
    fig.text(0.09, 0.057, "Scores were repaired offline. These cohorts do not isolate a budget-only causal effect.", fontsize=10, color="#333333")
    return fig


def delta_figure(plt: Any, endpoints: dict) -> Any:
    values = [[100 * endpoints[model, beta]["delta_f1"] for beta in BETAS] for model in MODELS]
    maximum = max(abs(value) for row in values for value in row)
    limit = maximum if maximum > 1e-10 else 1.0
    fig, ax = plt.subplots(figsize=(10.4, 6.9))
    fig.subplots_adjust(left=0.13, right=0.87, bottom=0.24, top=0.79)
    mesh = ax.imshow(values, cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks(range(len(BETAS)), ["1", "5", "10*", "15", "20"])
    ax.set_yticks(range(len(MODELS)), [NAMES[model] for model in MODELS])
    ax.set_xlabel(r"Feedback budget multiplier $\beta$")
    ax.tick_params(axis="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([index - 0.5 for index in range(1, len(BETAS))], minor=True)
    ax.set_yticks([index - 0.5 for index in range(1, len(MODELS))], minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)
    for row_index, model in enumerate(MODELS):
        for column_index, beta in enumerate(BETAS):
            item = endpoints[model, beta]
            value = 100 * item["delta_f1"]
            # Avoid visually misleading negative zero after rounding.
            label = "0.00" if abs(value) < 0.005 else f"{value:+.2f}"
            color = "white" if abs(value) > 0.62 * limit else "#222222"
            ax.text(column_index, row_index, f"{label}\n{item['changed_questions']}/39 changed", ha="center", va="center", color=color, fontsize=10, linespacing=1.45)
    if maximum > 1e-10:
        colorbar = fig.colorbar(mesh, ax=ax, fraction=0.032, pad=0.035)
        colorbar.set_label("New − old F1 (percentage points)", fontsize=10)
    fig.suptitle("Whois N1: score changes after offline protocol repair", x=0.09, y=0.965, ha="left", fontsize=15, fontweight="bold")
    if not any(item["changed_questions"] for item in endpoints.values()):
        subtitle = "All 1,170 question F1 scores unchanged · 0.00 pp at every endpoint"
    elif maximum <= 1e-10:
        subtitle = "All 30 endpoint means unchanged; some question-level scores changed"
    else:
        subtitle = "Same existing trajectories and questions · 30 paired endpoint comparisons"
    fig.text(0.09, 0.905, subtitle, fontsize=11, color="#444444")
    fig.text(0.09, 0.85, "Each cell: mean F1 change in percentage points; questions with a changed score / 39.", fontsize=10, color="#444444")
    fig.text(0.09, 0.14, "* β=10 reuses main-experiment trajectories. The repair includes these historical results.", fontsize=10, color="#333333")
    fig.text(0.09, 0.095, "Gemini: β=1/5/15/20 via OpenRouter; β=10 via Sub2. No new experiments were run for this repair.", fontsize=10, color="#333333")
    fig.text(0.09, 0.05, "A zero mean change can include offsetting question-level changes; counts refer to score changes.", fontsize=10, color="#333333")
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bundle", type=Path, required=True, help="directory containing the two final CSV inputs")
    parser.add_argument("--output-dir", type=Path, help="new directory; defaults to <bundle>/figures")
    parser.add_argument("--source-version", required=True, help="explicit report/scoring version recorded in PROVENANCE.json")
    args = parser.parse_args()
    if not args.source_version.strip():
        parser.error("--source-version must not be empty")
    source_paths = {"aggregate": args.bundle / "aggregate_metrics.csv", "old_vs_new": args.bundle / "old_vs_new_metrics.csv"}
    input_hashes = {name: sha256(path) for name, path in source_paths.items()}
    endpoints, inputs, comparison_fields = load_inputs(args.bundle)
    if any(sha256(path) != input_hashes[name] for name, path in inputs.items()):
        raise ValueError("a source CSV changed while being read")
    output = args.output_dir or args.bundle / "figures"
    if output.exists() or output.is_symlink():
        raise ValueError(f"figure directory is create-only and already exists: {output}")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "svg.fonttype": "none", "svg.hashsalt": GENERATOR_VERSION})
    output.mkdir(parents=True, exist_ok=False)
    written = []
    for builder, basename in ((budget_figure, "whois_six_model_budget"), (delta_figure, "whois_rescoring_delta")):
        figure = builder(plt, endpoints)
        try:
            written.extend(save_figure(figure, output, basename))
        finally:
            plt.close(figure)
    # Inputs must remain unchanged throughout a render; an interrupted or
    # concurrently changed input never receives a completed provenance manifest.
    if any(sha256(path) != input_hashes[name] for name, path in inputs.items()):
        raise ValueError("a source CSV changed while figures were being rendered")
    provenance = {
        "schema": GENERATOR_VERSION,
        "source_version": args.source_version,
        "scoring": "protocol-repaired offline rescoring of existing trajectories",
        "new_model_executions": 0,
        "endpoint_count": 30,
        "questions_per_endpoint": QUESTIONS_PER_ENDPOINT,
        "total_question_results": 1170,
        "models": list(MODELS),
        "betas": list(BETAS),
        "historical_main_betas": [10],
        "historical_main_question_results_reused": 234,
        "gemini_provider_cohorts": {"OpenRouter": [1, 5, 15, 20], "Sub2": [10]},
        "missing_points_plotted_as_zero": False,
        "delta_units": "F1 percentage points (100 * (new_mean_f1 - old_mean_f1))",
        "changed_question_definition": "number of questions whose F1 score changed, not merely whose answer changed",
        "comparison_columns": comparison_fields,
        "inputs": {name: {"path": os.path.relpath(path.resolve(), output.resolve()), "sha256": input_hashes[name], "bytes": path.stat().st_size} for name, path in inputs.items()},
        "generator": {"name": Path(__file__).name, "version": GENERATOR_VERSION, "sha256": sha256(Path(__file__))},
        "runtime": {"python": platform.python_version(), "matplotlib": matplotlib.__version__},
        "files": [{"path": path.name, "sha256": sha256(path), "bytes": path.stat().st_size} for path in written],
    }
    with (output / "PROVENANCE.json").open("x", encoding="utf-8") as stream:
        json.dump(provenance, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"written": [str(path) for path in written], "manifest": str(output / "PROVENANCE.json"), "source_version": args.source_version, "endpoints": 30}, ensure_ascii=False))


if __name__ == "__main__":
    main()
