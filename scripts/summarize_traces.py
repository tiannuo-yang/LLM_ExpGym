#!/usr/bin/env python3
"""Summarize ExpGym trace JSON files as a small TSV table."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


FIELDS = [
    "trace",
    "scenario",
    "item",
    "model",
    "cost_regime",
    "answer_perf",
    "score_check",
    "evaluations",
    "api_calls",
    "aborted",
    "wall_time_seconds",
]


def iter_trace_files(paths: Iterable[Path]) -> List[Path]:
    files: List[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".json":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
    return sorted(files)


def trace_item(job: Dict[str, Any]) -> str:
    scenario = job.get("scenario")
    if scenario == "tuning":
        return str(job.get("tuning_task", ""))
    if scenario == "restricted_search":
        source = job.get("data_source") or "phantom_seed1"
        return f"{source}[{job.get('question_index')}]"
    if scenario == "evidence_audit":
        return f"{job.get('cc_split', 'cc-large')}[{job.get('question_index')}]"
    return str(job.get("question_index", ""))


def summarize_trace(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    job = data.get("job") or {}
    score_check = data.get("score_check") or {}
    return {
        "trace": str(path),
        "scenario": job.get("scenario", ""),
        "item": trace_item(job),
        "model": job.get("model_id", ""),
        "cost_regime": job.get("cost_regime", ""),
        "answer_perf": data.get("answer_perf"),
        "score_check": "ok" if score_check.get("ok") else "failed",
        "evaluations": data.get("evaluations"),
        "api_calls": data.get("api_calls"),
        "aborted": data.get("aborted"),
        "wall_time_seconds": data.get("wall_time_seconds"),
    }


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def print_tsv(rows: List[Dict[str, Any]]) -> None:
    print("\t".join(FIELDS))
    for row in rows:
        print("\t".join(format_value(row.get(field)) for field in FIELDS))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Trace JSON file(s) or directories containing traces.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = iter_trace_files(args.paths)
    rows = [summarize_trace(path) for path in files]
    print_tsv(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
