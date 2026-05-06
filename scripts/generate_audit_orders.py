"""Generate shuffled hypothesis orderings for evidence audit experiments.

Produces configs/audit_hypothesis_orders.json with N shuffled orderings
of the cc-large NDA IDs, one per repetition.

Usage:
    python scripts/generate_audit_orders.py [--reps 3] [--seed 1206]
"""
from __future__ import annotations

import argparse
import json
import os
import random


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate shuffled audit hypothesis orderings."
    )
    parser.add_argument("--reps", type=int, default=3,
                        help="Number of shuffled orderings to generate.")
    parser.add_argument("--seed", type=int, default=1206,
                        help="Random seed for reproducibility.")
    parser.add_argument("--cc-split", default="cc-large",
                        help="CC split to use for hypothesis IDs.")
    parser.add_argument("--output", default="configs/audit_hypothesis_orders.json",
                        help="Output JSON file path.")
    args = parser.parse_args()

    # Import here to avoid top-level data load
    from expgym.task_evidence_audit import _get_labels

    labels = _get_labels(args.cc_split)
    nda_ids = list(labels.keys())
    print(f"Found {len(nda_ids)} NDA IDs for {args.cc_split}: {nda_ids}")

    rng = random.Random(args.seed)
    orders = []
    for rep in range(args.reps):
        shuffled = list(nda_ids)
        rng.shuffle(shuffled)
        orders.append(shuffled)
        print(f"  rep {rep}: {shuffled}")

    output = {
        "seed": args.seed,
        "cc_split": args.cc_split,
        "n_hypotheses": len(nda_ids),
        "n_reps": args.reps,
        "orders": orders,
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved {args.reps} orderings to {args.output}")


if __name__ == "__main__":
    main()
