#!/usr/bin/env python3
"""Export NEW presentation CSVs from independently computed final evidence."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "independent_post_resume_final.json"
report = json.loads(SOURCE.read_text())
assert report["complete"] and report["summary_comparison"]["complete"]
metrics = report["metrics"]["aggregate_metrics"]
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STRATEGIES = ("naive", "cached", "poolact")


def value(system, regime, strategy, metric):
    row, = [row for row in metrics if row["system"] == system and row["regime"] == regime
            and row["strategy"] == strategy and row["metric"] == metric]
    return row["value"]


expgym = [{"regime": regime, "LA_pct": value("expgym", regime, None, "LA_pct"),
           "EA_pct": value("expgym", regime, None, "EA_pct"), "documents": 13, "orders_per_document": 3}
          for regime in REGIMES]
poolact = [{"regime": regime, "strategy": strategy, "paper_subset": regime != "cost_free", "documents": 13, "agents_per_document": 4,
            **{metric: value("poolact", regime, strategy, metric) for metric in ("LA_pct", "EA_pct", "MI_LA_pct", "MI_EA_pct")}}
           for regime in REGIMES for strategy in STRATEGIES]
traces = [{key: row[key] for key in ("system", "item_index", "regime", "strategy", "rep", "agent_id", "path", "sha256",
                                    "parse_mode", "label_acc", "evidence_acc", "verification_eff", "denominator",
                                    "label_correct", "evidence_correct", "fully_correct")}
          for row in report["traces"]]
exports = {"expgym_final_wide.csv": expgym, "poolact_final_wide.csv": poolact,
           "document_metrics_final.csv": report["metrics"]["document_metrics"], "trace_metrics_final.csv": traces}
assert all(not (HERE / name).exists() for name in exports), "CSV evidence already exists; do not overwrite"
for name, rows in exports.items():
    with (HERE / name).open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                             for key, value in row.items()})
print(json.dumps({"classification": "presentation only from independently scored final evidence", "files": list(exports)}, ensure_ascii=False))
