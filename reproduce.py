"""Reproduce paper numbers from a small bundled trace fixture.

Loads 324 pre-computed traces from ``data/repro/v17_search_whois_traces.json``
and recomputes the search-F1 column of Table 2 in the paper. Prints the
recomputed values next to the paper-stated values; any cell that diverges
by more than the tolerance is marked DIFF in the output. The script does
not call an LLM and needs no API key, so a reviewer with a clean clone
can verify reproduction in a few seconds.

Usage:
    python reproduce.py
    python reproduce.py --traces path/to/other/traces.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

DEFAULT_TRACES = os.path.join(
    os.path.dirname(__file__), "data", "repro", "v17_search_whois_traces.json"
)

# Paper2 Table 2, "wh" (whois) column. Six models x three cost regimes.
# Numbers are search F1 averaged across 18 questions/reps per cell.
PAPER_TABLE: Dict[str, Dict[str, float]] = {
    # model_tag -> {eei_mode: F1}
    "gpt52":   {"noneei": 0.722, "eei": 0.636, "eei_extreme": 0.300},
    "haiku45": {"noneei": 0.607, "eei": 0.598, "eei_extreme": 0.262},
    "gemini3": {"noneei": 0.611, "eei": 0.553, "eei_extreme": 0.265},
    "dsv32":   {"noneei": 0.776, "eei": 0.621, "eei_extreme": 0.248},
    "mistral": {"noneei": 0.609, "eei": 0.425, "eei_extreme": 0.212},
    "gpt41":   {"noneei": 0.551, "eei": 0.526, "eei_extreme": 0.259},
}

# Display order. Each tuple is (model_tag, paper-display-name).
MODEL_ORDER: List[Tuple[str, str]] = [
    ("gpt52",   "GPT-5.2"),
    ("haiku45", "Haiku-4.5"),
    ("gemini3", "Gemini-3"),
    ("dsv32",   "DSV3.2"),
    ("mistral", "Mistral"),
    ("gpt41",   "GPT-4.1"),
]

REGIME_ORDER: List[Tuple[str, str]] = [
    ("noneei",      "Cost-Free"),
    ("eei",         "Cost-Moderate"),
    ("eei_extreme", "Cost-Tight"),
]

# Three decimals match the paper's table precision; this is the tolerance
# at which we declare a cell "matches" the paper.
TOLERANCE = 5e-4


def load_traces(path: str) -> List[dict]:
    with open(path, "r") as f:
        traces = json.load(f)
    if not isinstance(traces, list):
        raise ValueError(f"Expected a JSON list of trace records at {path}")
    return traces


def compute_f1_table(traces: List[dict]) -> Dict[str, Dict[str, Tuple[float, int]]]:
    """Aggregate traces by (model_tag, eei_mode); return mean F1 and N per cell."""
    buckets: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for r in traces:
        if r.get("scenario", "restricted_search") != "restricted_search":
            continue
        if r.get("data_source") != "phantom_seed1":  # whois subset only
            continue
        buckets[(r["model_tag"], r["eei_mode"])].append(float(r["answer_perf"]))
    table: Dict[str, Dict[str, Tuple[float, int]]] = {}
    for (model, mode), perfs in buckets.items():
        table.setdefault(model, {})[mode] = (sum(perfs) / len(perfs), len(perfs))
    return table


def render(
    table: Dict[str, Dict[str, Tuple[float, int]]],
    paper: Dict[str, Dict[str, float]],
) -> bool:
    """Print side-by-side table; return True iff every cell matches."""
    header = (
        f"{'Model':<11} | "
        + " | ".join(
            f"{label} (computed / paper)".ljust(34) for _, label in REGIME_ORDER
        )
    )
    print(header)
    print("-" * len(header))

    all_match = True
    for model_tag, display in MODEL_ORDER:
        row = f"{display:<11} |"
        for mode, _ in REGIME_ORDER:
            computed, n = table.get(model_tag, {}).get(mode, (float("nan"), 0))
            stated = paper[model_tag][mode]
            match = abs(computed - stated) < TOLERANCE
            mark = "OK" if match else "DIFF"
            if not match:
                all_match = False
            row += f" {computed:.3f} / {stated:.3f} (n={n:>2}, {mark})".ljust(35) + "|"
        print(row)
    print()
    return all_match


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--traces",
        default=DEFAULT_TRACES,
        help="Path to the trace JSON fixture (default: %(default)s).",
    )
    args = parser.parse_args()

    print("Reproducing search-F1 (whois) column of paper Table 2.")
    print(f"Loading traces from: {args.traces}")
    traces = load_traces(args.traces)
    print(f"Loaded {len(traces)} traces.\n")

    table = compute_f1_table(traces)
    ok = render(table, PAPER_TABLE)

    if ok:
        print("Result: ALL 18 CELLS MATCH the paper to within "
              f"{TOLERANCE:g} (3-decimal precision).")
        return 0
    print("Result: at least one cell DIFFERS from the paper. "
          "See per-cell DIFF flag above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
