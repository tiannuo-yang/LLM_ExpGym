#!/usr/bin/env python3
"""Independent stdlib-only aggregation of the completed HPO raw partition.

Does not import the official auditor/summarizer or call any LLM/evaluator.
Optional --summary compares against the official output when it exists.
"""
import argparse
import collections
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "kimi_k3_eval"
parser = argparse.ArgumentParser()
parser.add_argument("--manifest", type=Path, default=STUDY / "runs/full_v3/manifest.json")
parser.add_argument("--summary", type=Path)
parser.add_argument("--output", type=Path, help="Exclusively create new generated evidence; never overwrite existing files")
args = parser.parse_args()
if args.output and args.output.exists():
    parser.error("--output already exists; choose a new evidence filename")

def read(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def ref(path):
    path = Path(path).absolute()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

def numeric(value):
    assert isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), value
    return float(value)

manifest = read(args.manifest)
oracle_path = Path(manifest["data_provenance"]["oracle"]["path"])
assert ref(oracle_path)["sha256"] == manifest["data_provenance"]["oracle"]["sha256"]
oracle = read(oracle_path)["tasks"]
jobs = [job for job in manifest["jobs"] if job["scenario"] == "tuning"]
assert len(jobs) == 54
source_hash = manifest["source_tree_sha256"]
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
FAMILIES = ("paramnet", "nasbench201", "nasbench101")
STRATEGIES = ("naive", "cached", "poolact")

def family(task):
    return next(name for name in FAMILIES if ":" + name + ":" in task)

def gap(performance, task):
    baseline = numeric(oracle[task]["mean_perf"])
    best = numeric(oracle[task]["best_perf"])
    assert best > baseline
    return max(0.0, (numeric(performance) - baseline) / (best - baseline) * 100.0)

traces, pool_results, receipts = [], [], []
for job in jobs:
    status = read(job["status_path"])
    assert status["status"] == "completed" and status["returncode"] == 0 and not status["missing_outputs"], job["id"]
    receipts.append({"job_id": job["id"], **ref(job["status_path"]), "status": status["status"],
                     "returncode": status["returncode"], "stdout": ref(job["stdout_log"])})
    for output in job["expected_outputs"]:
        raw = read(output["path"])
        common = {"job_id": job["id"], "system": job["system"], "task": job["tuning_task"],
                  "family": family(job["tuning_task"]), "regime": job["cost_regime"]}
        if job["system"] == "expgym":
            assert raw["provenance"]["repository"]["source_tree_sha256"] == source_hash
            assert raw["task"]["item"]["id"] == common["task"] and raw["task"]["budget"]["regime"] == common["regime"]
            assert raw["run"]["model"]["id"] == manifest["settings"]["model"]
            assert raw["task"]["rep"] == output["rep"] and raw["outcome"]["validation"]["passed"] is True
            score = numeric(raw["outcome"]["score"]["value"])
            traces.append({**common, **ref(output["path"]), "rep": output["rep"], "strategy": None,
                           "agent_id": None, "raw_performance": score, "gap_pct": gap(score, common["task"]),
                           "answer_source": raw["outcome"].get("answer_source"),
                           "termination_reason": raw["outcome"].get("termination_reason"),
                           "score_cost_basis": raw["outcome"].get("score_cost_basis")})
        else:
            assert raw["implementation_sha256"]["source_tree"] == source_hash
            assert raw["config"]["tuning_task"] == common["task"] and raw["config"]["cost_regime"] == common["regime"]
            assert raw["config"]["model"] == manifest["settings"]["model"]
            assert raw["strategy"] == output["strategy"] and raw["agents"] == 4 and len(raw["agent_results"]) == 4
            assert raw["aggregate"]["method"] == "best_of_n"
            agents = []
            for index, path in enumerate(output["agent_paths"]):
                agent = read(path)
                assert agent == raw["agent_results"][index]
                assert agent["agent_id"] == index and agent["strategy"] == output["strategy"]
                assert agent["score_check"]["ok"] is True
                score = numeric(agent["answer_perf"])
                assert math.isclose(score, numeric(agent["score_check"]["recomputed_perf"]), abs_tol=1e-12)
                row = {**common, **ref(path), "rep": None, "strategy": output["strategy"], "agent_id": index,
                       "raw_performance": score, "gap_pct": gap(score, common["task"]),
                       "answer_source": agent.get("answer_source"), "answer_score_source": agent.get("answer_score_source"),
                       "aborted": agent.get("aborted"), "evaluations": agent.get("evaluations"),
                       "score_check": agent["score_check"]}
                traces.append(row)
                agents.append(row)
            individual = [agent["raw_performance"] for agent in agents]
            assert raw["aggregate"]["individual_perfs"] == individual
            best = numeric(raw["aggregate"]["answer_perf"])
            assert math.isclose(best, max(individual), abs_tol=1e-12)
            pool_results.append({**common, **ref(output["path"]), "strategy": output["strategy"],
                                 "raw_best": best, "raw_mean_individual": statistics.mean(individual),
                                 "BoN_Gap_pct": gap(best, common["task"]),
                                 "MI_Gap_pct": statistics.mean(agent["gap_pct"] for agent in agents),
                                 "agent_paths": [agent["path"] for agent in agents],
                                 "zero_raw_agents": sum(value == 0 for value in individual)})
assert len(traces) == 405 and sum(row["system"] == "expgym" for row in traces) == 81
assert len(pool_results) == 81
assert len({row["path"] for row in traces}) == 405
tasks = sorted({job["tuning_task"] for job in jobs})
assert len(tasks) == 9
task_metrics = []
for task in tasks:
    for regime in REGIMES:
        rows = [row for row in traces if row["system"] == "expgym" and row["task"] == task and row["regime"] == regime]
        assert len(rows) == 3 and {row["rep"] for row in rows} == {0, 1, 2}
        task_metrics.append({"system": "expgym", "task": task, "family": family(task), "regime": regime,
                             "strategy": None, "metric": "Gap_pct", "value": statistics.mean(row["gap_pct"] for row in rows),
                             "raw_mean": statistics.mean(row["raw_performance"] for row in rows), "traces": len(rows),
                             "zero_raw_traces": sum(row["raw_performance"] == 0 for row in rows),
                             "paths": [row["path"] for row in rows]})
        for strategy in STRATEGIES:
            result, = [row for row in pool_results if row["task"] == task and row["regime"] == regime and row["strategy"] == strategy]
            for metric in ("BoN_Gap_pct", "MI_Gap_pct"):
                task_metrics.append({"system": "poolact", "task": task, "family": family(task), "regime": regime,
                                     "strategy": strategy, "metric": metric, "value": result[metric], "traces": 4,
                                     "raw_best": result["raw_best"], "raw_mean_individual": result["raw_mean_individual"],
                                     "zero_raw_traces": result["zero_raw_agents"], "paths": [result["path"]]})
family_metrics = []
for system in ("expgym", "poolact"):
    for regime in REGIMES:
        for name in FAMILIES:
            for strategy in ((None,) if system == "expgym" else STRATEGIES):
                for metric in (("Gap_pct",) if system == "expgym" else ("BoN_Gap_pct", "MI_Gap_pct")):
                    rows = [row for row in task_metrics if row["system"] == system and row["family"] == name
                            and row["regime"] == regime and row["strategy"] == strategy and row["metric"] == metric]
                    assert len(rows) == 3
                    family_metrics.append({"system": system, "family": name, "regime": regime, "strategy": strategy,
                                           "metric": metric, "value": statistics.mean(row["value"] for row in rows),
                                           "tasks": [row["task"] for row in rows]})
summary_comparison = None
if args.summary:
    summary = read(args.summary)
    assert summary["complete"] is True and summary["manifest_sha256"] == ref(args.manifest)["sha256"]
    comparisons, task_comparisons, agent_comparisons, paper_comparisons = [], [], [], []
    for row in family_metrics:
        match, = [item for item in summary["aggregate_metrics"] if item["subset"] == "full" and item["system"] == row["system"]
                  and item["dimension"] == row["family"] and item["cost_regime"] == row["regime"]
                  and item.get("strategy") == row["strategy"] and item["metric"] == row["metric"]]
        assert match["complete"] is True and math.isclose(row["value"], match["value"], abs_tol=1e-10)
        comparisons.append({**row, "official_value": match["value"], "difference": row["value"] - match["value"]})
    for row in task_metrics:
        match, = [item for item in summary["task_metrics"] if item["subset"] == "full" and item["system"] == row["system"]
                  and item["item_id"] == row["task"] and item["cost_regime"] == row["regime"]
                  and item.get("strategy") == row["strategy"] and item["metric"] == row["metric"]]
        assert match["complete"] is True and math.isclose(row["value"], match["value"], abs_tol=1e-10)
        task_comparisons.append({**row, "official_value": match["value"], "difference": row["value"] - match["value"]})
    official_agents = {row["path"]: row for row in summary["agents"]}
    assert len(official_agents) == len(summary["agents"]), "duplicate agent paths in official summary"
    for row in traces:
        match = official_agents[row["path"]]
        assert match["sha256"] == row["sha256"] and match["status"] == "valid"
        assert math.isclose(row["raw_performance"], match["answer_perf"], abs_tol=1e-12)
        assert math.isclose(row["gap_pct"], match["Gap_pct"], abs_tol=1e-10)
        agent_comparisons.append({"path": row["path"], "sha256": row["sha256"],
                                  "raw_difference": row["raw_performance"] - match["answer_perf"],
                                  "gap_difference": row["gap_pct"] - match["Gap_pct"]})
    for row in task_metrics:
        if row["system"] != "poolact" or row["task"] != "hpobench:nasbench101:A" or row["regime"] == "cost_free":
            continue
        match, = [item for item in summary["aggregate_metrics"] if item["subset"] == "paper_poolact" and item["system"] == row["system"]
                  and item["dimension"] == "nasbench101" and item["cost_regime"] == row["regime"]
                  and item.get("strategy") == row["strategy"] and item["metric"] == row["metric"]]
        assert match["complete"] is True and math.isclose(row["value"], match["value"], abs_tol=1e-10)
        paper_comparisons.append({**row, "official_value": match["value"], "difference": row["value"] - match["value"]})
    assert (len(comparisons), len(task_comparisons), len(agent_comparisons), len(paper_comparisons)) == (63, 189, 405, 12)
    summary_comparison = {**ref(args.summary), "complete": True,
                          "family_cells_checked": len(comparisons), "task_cells_checked": len(task_comparisons),
                          "agent_records_checked": len(agent_comparisons), "paper_nas101a_cells_checked": len(paper_comparisons),
                          "family_cells": comparisons, "task_cells": task_comparisons,
                          "agent_records": agent_comparisons, "paper_nas101a_cells": paper_comparisons}
report = {"schema": {"name": "kimi.hpo.independent_raw_review", "version": 1},
          "created_at": datetime.now(timezone.utc).isoformat(),
          "classification": "completed HPO partition only; not a claim that the full study is complete; not a new run",
          "method": "stdlib-only direct parsing; Gap=max(0,(perf-oracle.mean)/(oracle.best-oracle.mean)*100), no upper cap; per-trace/agent clipping then per-task and family means",
          "source_tree_sha256": source_hash, "manifest": ref(args.manifest), "oracle": ref(oracle_path), "script": ref(__file__),
          "coverage": {"completed_hpo_subprocess_jobs": 54, "expgym_traces": 81, "poolact_results": 81,
                       "poolact_agent_traces": 324, "all_hpo_agent_traces": 405},
          "oracles": {task: {key: oracle[task][key] for key in ("mean_perf", "best_perf")} for task in tasks},
          "receipts": receipts, "traces": traces, "poolact_results": pool_results,
          "task_metrics": task_metrics, "family_metrics": family_metrics,
          "zero_raw_traces": [row for row in traces if row["raw_performance"] == 0],
          "zero_gap_nonzero_raw_traces": [row for row in traces if row["gap_pct"] == 0 and row["raw_performance"] != 0],
          "above100_gap_traces": [row for row in traces if row["gap_pct"] > 100],
          "summary_comparison": summary_comparison}
encoded = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2)
if args.output:
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(encoded + "\n")
    print(json.dumps({"coverage": report["coverage"], "summary_comparison_complete": (summary_comparison or {}).get("complete"),
                      "comparison_counts": {key: value for key, value in (summary_comparison or {}).items() if key.endswith("_checked")},
                      "output": ref(args.output)}, ensure_ascii=False))
else:
    print(encoded)
