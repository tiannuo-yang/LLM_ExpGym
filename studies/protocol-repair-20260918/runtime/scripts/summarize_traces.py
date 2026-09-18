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
    "label_acc",
    "evidence_acc",
    "verification_eff",
    "score_check",
    "evaluations",
    "api_calls",
    "cached_prompt_tokens",
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
    schema = data.get("schema") or {}
    if schema.get("name") == "expgym.trace" and schema.get("version") == "2.0.0":
        return summarize_trace_v2(path, data)
    job = data.get("job") or {}
    answer_metrics = data.get("answer_metrics") or {}
    score_check = data.get("score_check") or {}
    return {
        "trace": str(path),
        "scenario": job.get("scenario", ""),
        "item": trace_item(job),
        "model": job.get("model_id", ""),
        "cost_regime": job.get("cost_regime", ""),
        "answer_perf": data.get("answer_perf"),
        "label_acc": answer_metrics.get("label_acc"),
        "evidence_acc": answer_metrics.get("evidence_acc"),
        "verification_eff": answer_metrics.get("verification_eff"),
        "score_check": "ok" if score_check.get("ok") else "failed",
        "evaluations": data.get("evaluations"),
        "api_calls": data.get("api_calls"),
        "cached_prompt_tokens": data.get("cached_prompt_tokens"),
        "aborted": data.get("aborted"),
        "wall_time_seconds": data.get("wall_time_seconds"),
    }


def summarize_trace_v2(path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
    task = data.get("task") or {}
    item_data = task.get("item") or {}
    scenario = task.get("scenario", "")
    if scenario == "tuning":
        item = str(item_data.get("id", ""))
    elif scenario == "restricted_search":
        item = f"{item_data.get('source', 'phantom_seed1')}[{item_data.get('id')}]"
    elif scenario == "evidence_audit":
        item = f"{item_data.get('split', 'cc-large')}[{item_data.get('id')}]"
    else:
        item = str(item_data.get("id", ""))

    outcome = data.get("outcome") or {}
    score = outcome.get("score") or {}
    metrics = score.get("metrics") or {}
    cache_details = [
        ((call.get("usage") or {}).get("cache") or {})
        for call in data.get("llm_calls") or []
    ]
    cache_reported = any(detail.get("reported") for detail in cache_details)
    cached_tokens = (
        sum(int(detail.get("read_tokens") or 0) for detail in cache_details)
        if cache_reported
        else None
    )
    return {
        "trace": str(path),
        "scenario": scenario,
        "item": item,
        "model": ((data.get("run") or {}).get("model") or {}).get("id", ""),
        "cost_regime": (task.get("budget") or {}).get("regime", ""),
        "answer_perf": metrics.get("label_acc", score.get("value")),
        "label_acc": metrics.get("label_acc"),
        "evidence_acc": metrics.get("evidence_acc"),
        "verification_eff": metrics.get("verification_eff"),
        "score_check": "ok" if (outcome.get("validation") or {}).get("passed") else "failed",
        "evaluations": len(data.get("tool_calls") or []),
        "api_calls": len(data.get("llm_calls") or []),
        "cached_prompt_tokens": cached_tokens,
        "aborted": outcome.get("status") != "completed",
        "wall_time_seconds": (data.get("timing") or {}).get("wall_time_seconds"),
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
