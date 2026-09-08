#!/usr/bin/env python3
"""Manifest-selected audit -> raw CSV, paper metrics, Chinese report.

Missing/failed rows remain empty. Gap is clipped separately for each trace or
agent, averaged within each task, then equally across tasks in each family.
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime, timezone
from pathlib import Path

from audit_results import finite, load_runners, mean, require, sha256, strict_json, write_csv, write_json


def gap(performance, task, oracles):
    oracle = oracles.get(task) or {}
    baseline, best = oracle.get("mean_perf"), oracle.get("best_perf")
    if not all(finite(x) for x in (performance, baseline, best)) or best <= baseline:
        return None
    return max(0.0, (performance - baseline) / (best - baseline) * 100.0)


def dimension(record):
    if record["scenario"] == "tuning":
        for name in ("paramnet", "nasbench101", "nasbench201"):
            if ":%s:" % name in record["tuning_task"]:
                return name
        return record["tuning_task"]
    if record["scenario"] == "restricted_search":
        return "whois" if int(record["question_index"]) < 18 else "whatis"
    return "audit"


def percentage(value):
    return value * 100 if finite(value) else None


def metric_values(record, oracles):
    if record["status"] != "valid":
        return {}
    agents = record["agent_records"]
    if record["scenario"] == "tuning":
        result = {"raw_performance": record["answer_perf"],
                  "Gap_pct": gap(record["answer_perf"], record["tuning_task"], oracles)}
        if record["system"] == "poolact":
            result["BoN_Gap_pct"] = result.pop("Gap_pct")
            result["MI_Gap_pct"] = mean(gap(agent["answer_perf"], record["tuning_task"], oracles) for agent in agents)
            result["MI_raw_performance"] = mean(agent["answer_perf"] for agent in agents)
        return result
    if record["scenario"] == "restricted_search":
        if record["system"] == "poolact":
            return {"MV_F1_pct": percentage(record["answer_perf"]),
                    "MI_F1_pct": mean(percentage(agent["answer_perf"]) for agent in agents)}
        return {"F1_pct": percentage(record["answer_perf"])}
    result = {"LA_pct": percentage(record.get("label_acc")), "EA_pct": percentage(record.get("evidence_acc")),
              "verification_eff_pct": percentage(record.get("verification_eff"))}
    if record["system"] == "poolact":
        result["MI_LA_pct"] = mean(percentage(agent.get("label_acc")) for agent in agents)
        result["MI_EA_pct"] = mean(percentage(agent.get("evidence_acc")) for agent in agents)
    return result


def metric_names(system, scenario):
    if scenario == "tuning":
        return ["Gap_pct", "raw_performance"] if system == "expgym" else ["BoN_Gap_pct", "MI_Gap_pct", "raw_performance", "MI_raw_performance"]
    if scenario == "restricted_search":
        return ["F1_pct"] if system == "expgym" else ["MV_F1_pct", "MI_F1_pct"]
    return ["LA_pct", "EA_pct", "verification_eff_pct"] + (["MI_LA_pct", "MI_EA_pct"] if system == "poolact" else [])


def all_numeric_sum(records, key):
    values = [row.get(key) for row in records]
    return sum(values) if values and all(finite(value) for value in values) else None


def verify_dump_trace_links(audit, dump):
    """A stable manifest alone cannot identify artifacts replaced by resume."""
    if audit.get("backend") == "fake" or not (audit.get("complete") and dump.get("complete")):
        return
    expected = []
    for record in audit["records"]:
        rows = [record] if record["system"] == "expgym" else record["agent_records"]
        expected.extend((str(Path(row["path"]).absolute()), row["sha256"]) for row in rows)
    observed = []
    for record in dump.get("records", []):
        require(record.get("status") == "valid", "completed raw dump audit contains a nonvalid trace")
        observed.append((str(Path(record["trace_path"]).absolute()), record["trace_sha256"]))
    require(len(expected) == len({path for path, _ in expected}), "duplicate result-audit trace paths")
    require(len(observed) == len({path for path, _ in observed}), "duplicate dump-audit trace paths")
    require(set(expected) == set(observed), "dump audit trace paths/SHA256 differ from current result audit")


def summarize(audit, oracle_path):
    oracles = strict_json(oracle_path)["tasks"]
    artifacts, agent_rows, metric_issues = [], [], []
    for record in audit["records"]:
        row = {key: value for key, value in record.items() if key != "agent_records"}
        row["dimension"] = dimension(record)
        row["paper_metrics"] = metric_values(record, oracles)
        if record["status"] == "valid" and record["scenario"] == "tuning" and gap(record["answer_perf"], record["tuning_task"], oracles) is None:
            metric_issues.append("missing/invalid tuning normalization oracle: " + record["path"])
        artifacts.append(row)
        if record["system"] == "expgym":
            agent_rows.append({**row, "agent_id": None, "parent_result_path": None,
                               "Gap_pct": gap(row.get("answer_perf"), row.get("tuning_task"), oracles) if row["status"] == "valid" else None})
        else:
            agents = {agent["agent_id"]: agent for agent in record["agent_records"]}
            for agent_id, agent_path in enumerate(record["expected_agent_paths"]):
                agent = agents.get(agent_id, {"agent_id": agent_id, "path": agent_path, "status": "missing"})
                out = {key: record.get(key) for key in ("job_id", "system", "scenario", "item_id", "tuning_task", "question_index", "cost_regime", "paper_subset", "rep", "strategy")}
                out.update(agent)
                out["parent_result_path"] = record["path"]
                out["parent_status"] = record["status"]
                out["Gap_pct"] = gap(agent.get("answer_perf"), record.get("tuning_task"), oracles) if record["status"] == "valid" else None
                agent_rows.append(out)
    grouped = collections.defaultdict(list)
    for row in artifacts:
        for subset in ["full"] + (["paper_poolact"] if row["paper_subset"] else []):
            key = (subset, row["system"], audit.get("model_id"), row["scenario"], row["dimension"], row["cost_regime"], row.get("strategy"))
            grouped[key].append(row)
    aggregate_rows, task_rows = [], []
    for key, rows in sorted(grouped.items(), key=lambda item: str(item[0])):
        subset, system, model_id, scenario, group, regime, strategy = key
        identity = {"subset": subset, "system": system, "model_id": model_id, "scenario": scenario,
                    "dimension": group, "cost_regime": regime, "strategy": strategy}
        by_task = collections.defaultdict(list)
        for row in rows:
            by_task[row["item_id"]].append(row)
        for metric in metric_names(system, scenario):
            task_values = []
            for item, task_records in sorted(by_task.items()):
                values = [row["paper_metrics"].get(metric) for row in task_records if row["status"] == "valid"]
                numeric = [value for value in values if finite(value)]
                complete = len(values) == len(task_records) and len(numeric) == len(task_records)
                # Verification efficiency can be mathematically undefined.
                optional = metric == "verification_eff_pct"
                value = mean(numeric) if complete or optional else None
                task_values.append(value)
                task_rows.append({**identity, "item_id": item, "metric": metric, "value": value,
                                  "available_mean": mean(numeric), "expected_results": len(task_records),
                                  "valid_results": sum(row["status"] == "valid" for row in task_records),
                                  "numeric_results": len(numeric), "complete": complete,
                                  "paths": [row["path"] for row in task_records]})
            numeric_tasks = [value for value in task_values if finite(value)]
            valid_results = sum(row["status"] == "valid" for row in rows)
            complete = valid_results == len(rows) and len(numeric_tasks) == len(by_task)
            aggregate_rows.append({**identity, "metric": metric, "value": mean(numeric_tasks) if complete else None,
                                   "available_task_mean": mean(numeric_tasks), "expected_results": len(rows),
                                   "valid_results": valid_results, "expected_tasks": len(by_task),
                                   "numeric_tasks": len(numeric_tasks), "complete": complete,
                                   "aggregation": "per_trace_or_agent_metric -> per_task_mean -> equal_task_mean",
                                   "paths": [row["path"] for row in rows]})
    return {"schema": {"name": "kimi.expgym.summary", "version": 1},
            "created_at": datetime.now(timezone.utc).isoformat(), "audit_complete": audit["complete"],
            "complete": audit["complete"] and not metric_issues, "model_id": audit.get("model_id"),
            "stage": audit.get("stage"), "study_type": audit.get("study_type"), "backend": audit.get("backend"),
            "manifest_path": audit["manifest_path"], "manifest_sha256": audit["manifest_sha256"],
            "oracle_path": str(Path(oracle_path).resolve()), "oracle_sha256": sha256(oracle_path),
            "expected_counts": audit["expected_counts"], "valid_counts": audit["valid_counts"],
            "statuses": audit["statuses"], "manifest_issues": audit["manifest_issues"], "metric_issues": metric_issues,
            "artifacts": artifacts, "agents": agent_rows, "task_metrics": task_rows,
            "aggregate_metrics": aggregate_rows, "resources": resource_summary(audit, agent_rows),
            "promotion": audit.get("promotion"),
            "metric_definitions": {
                "Gap_pct": "max(0,(raw_perf-oracle.mean_perf)/(oracle.best_perf-oracle.mean_perf)*100); may exceed 100",
                "BoN_Gap_pct": "Gap(max(agent raw_perf))",
                "MI_Gap_pct": "mean(Gap(agent raw_perf)); clip each agent before averaging",
                "MV_F1_pct": "repository semantic-majority-vote answer F1 * 100",
                "LA_pct": "per-hypothesis label accuracy * 100",
                "EA_pct": "per-hypothesis exact evidence-set accuracy * 100; independent of label correctness",
                "aggregation": "per trace/agent metric, then equal-weight repeats within task, then equal-weight tasks",
                "missing": "missing/failed/unverified artifacts do not contribute scores; incomplete main cells are null",
                "usage": "trace counters cover returned logical calls; retry and hidden usage require raw API dumps"}}


def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def resource_summary(audit, agent_rows):
    valid = [row for row in agent_rows if row.get("status") == "valid" and row.get("parent_status", "valid") == "valid"]
    elapsed, starts, ends, stage_elapsed, pilot_elapsed = [], [], [], [], []
    missing_wall, stage_missing, pilot_missing, missing_times = 0, 0, 0, 0
    receipts = [(record["job_id"], "stage", record["receipt"]) for record in audit.get("receipts", [])]
    for job in ((audit.get("promotion") or {}).get("plan") or {}).get("jobs", []):
        receipts.append((job["job_id"], "promoted_pilot", job["source_execution"]))
    seen_attempts = set()
    for job_id, origin, receipt in receipts:
        for attempt in receipt.get("attempts") or [receipt]:
            identity = (job_id, attempt.get("started_at"), attempt.get("finished_at"), attempt.get("pid"))
            if identity in seen_attempts:
                continue
            seen_attempts.add(identity)
            start, end = parse_time(attempt.get("started_at")), parse_time(attempt.get("finished_at"))
            if start is not None:
                starts.append(start)
            if end is not None:
                ends.append(end)
            if start is None or end is None:
                missing_times += 1
            duration = attempt.get("wall_time_seconds")
            if finite(duration):
                elapsed.append(duration)
                (stage_elapsed if origin == "stage" else pilot_elapsed).append(duration)
            else:
                missing_wall += 1
                if origin == "stage":
                    stage_missing += 1
                else:
                    pilot_missing += 1
    return {"valid_agent_rows": len(valid),
            "sum_agent_wall_seconds": all_numeric_sum(valid, "wall_time_seconds"),
            "sum_simulated_feedback_cost_seconds": all_numeric_sum(valid, "simulated_cost_seconds"),
            "sum_logical_api_calls": all_numeric_sum(valid, "logical_api_calls"),
            "sum_trace_input_tokens": all_numeric_sum(valid, "input_tokens"),
            "sum_trace_output_tokens": all_numeric_sum(valid, "output_tokens"),
            "sum_subprocess_attempt_wall_seconds": sum(elapsed) if elapsed and not missing_wall else None,
            "known_subprocess_attempt_wall_seconds": sum(elapsed) if elapsed else None,
            "missing_subprocess_attempt_wall_count": missing_wall,
            "sum_stage_subprocess_attempt_wall_seconds": sum(stage_elapsed) if stage_elapsed and not stage_missing else None,
            "known_stage_subprocess_attempt_wall_seconds": sum(stage_elapsed) if stage_elapsed else None,
            "missing_stage_attempt_wall_count": stage_missing,
            "sum_promoted_pilot_subprocess_attempt_wall_seconds": sum(pilot_elapsed) if pilot_elapsed and not pilot_missing else None,
            "known_promoted_pilot_subprocess_attempt_wall_seconds": sum(pilot_elapsed) if pilot_elapsed else None,
            "missing_promoted_pilot_attempt_wall_count": pilot_missing,
            "study_execution_span_seconds": max(ends) - min(starts) if starts and ends and not missing_times else None,
            "known_execution_span_seconds": max(ends) - min(starts) if starts and ends else None,
            "missing_attempt_start_or_end_count": missing_times,
            "execution_span_includes_idle_and_retry_gaps": True,
            "notes": "Subprocess totals include preserved promoted pilot attempts plus current stage, deduplicated by job/start/end/pid. Agent and subprocess sums double-count concurrent time. Span includes pilot-to-full idle gaps. Simulated cost is budget accounting, not Slurm wall time. Trace usage may exclude unsuccessful HTTP attempts."}


def fmt(value):
    return "—" if value is None else "%.3f" % value if isinstance(value, float) else str(value)


def report_markdown(summary):
    state = "通过" if summary["complete"] else "未完成/未通过，以下仅报告已验证数据"
    description = ("Static/fake validation；确定性 fake backend 仅验证程序与报告，不是 Kimi-K3 性能结果。"
                   if summary.get("backend") == "fake" else
                   "Custom study；本地 Kimi-K3 + SGLang，按论文主设置新增模型，最终目标覆盖仓库全矩阵。")
    lines = ["# Kimi-K3：ExpGym / PoolAct 实验结果", "", "实验类型：" + description, "",
             "验收状态：**%s**。阶段：%s。" % (state, summary["stage"]), "",
             "| 验收项 | 计划 | 通过 |", "|---|---:|---:|"]
    for field, label in (("expgym_traces", "ExpGym traces"), ("poolact_results", "PoolAct results"),
                         ("poolact_agent_traces", "PoolAct agent traces"), ("poolact_paper_results", "论文 PoolAct subset results")):
        lines.append("| %s | %s | %s |" % (label, summary["expected_counts"].get(field, 0), summary["valid_counts"].get(field, 0)))
    lines += ["", "缺失/失败状态：%s。缺失轨迹不补 0；有效模型零分保留。" % summary["statuses"], ""]
    tables = [("ExpGym 主表（%）", "full", "expgym", {"Gap_pct", "F1_pct", "LA_pct", "EA_pct"}),
              ("PoolAct 论文子集（%）", "paper_poolact", "poolact", {"BoN_Gap_pct", "MI_Gap_pct", "MV_F1_pct", "MI_F1_pct", "LA_pct", "EA_pct"}),
              ("PoolAct 全量扩展（%）", "full", "poolact", {"BoN_Gap_pct", "MI_Gap_pct", "MV_F1_pct", "MI_F1_pct", "LA_pct", "EA_pct"})]
    for title, subset, system, metrics in tables:
        lines += ["## " + title, "", "| Regime | Strategy | 维度 | 指标 | 值 | 通过/计划 |", "|---|---|---|---|---:|---:|"]
        for row in summary["aggregate_metrics"]:
            if row["subset"] == subset and row["system"] == system and row["metric"] in metrics:
                lines.append("| %s | %s | %s | %s | %s | %s/%s |" % (row["cost_regime"], row["strategy"] or "single", row["dimension"], row["metric"], fmt(row["value"]), row["valid_results"], row["expected_results"]))
        lines.append("")
    lines += ["## 耗时与费用口径", "", "| 项目 | 秒/次/token |", "|---|---:|"]
    for key, value in summary["resources"].items():
        if key not in {"notes", "execution_span_includes_idle_and_retry_gaps"}:
            lines.append("| %s | %s |" % (key, fmt(value)))
    lines += ["", "模拟反馈费用只表示 benchmark 预算；并发 agent/subprocess 墙钟求和会重复计时。真实执行跨度为最早开始至最晚结束，包含排队/重试/空档；完整 HTTP 尝试与 usage 以原始 API dump 为准。", "",
              "## 查验路径与指标", "",
              "逐项索引见 artifacts.csv，逐 agent 原始指标见 agents.csv，逐任务分数见 task_metrics.csv，汇总见 aggregate_metrics.csv / summary.json。每条记录保留原始路径与 SHA256；各输出为新目录，原始结果不覆盖。", "",
              "Gap 按每条有效性能计算 max(0,(perf−mean)/(best−mean)×100)，先均值各 task 的 repeats、后均值各 family 的 tasks；可以超过 100。PoolAct MI 先分别计算每 agent 的 clipped Gap。Audit EA 是证据集合精确匹配，独立于 label 是否正确。", "",
              "Kimi-K3/本地提供商是新增设置；PoolAct 使用当前 corrected locked 协议，历史论文含 locked/prelock 混合行，不能声称字节级或原模型复现。论文 tuning outer repeat 历史设定未公开；正式 full 阶段为一个 N=4 pool，smoke 为 N=2。非 full 阶段表格仅表示本阶段选定子集。设置与偏离详见 protocol/PAPER_ALIGNMENT.md。", "",
              "归一化 oracle：%s，SHA256 %s。" % (summary["oracle_path"], summary["oracle_sha256"]),
              "Manifest：%s，SHA256 %s。" % (summary["manifest_path"], summary["manifest_sha256"]), ""]
    if summary.get("dump_audit"):
        lines += ["原始 API dump 完整性：%s。当前结果对应调用与历史重跑调用分开保留；详见 summary.json 的 dump_audit 字段。" %
                  ("通过" if summary["dump_audit"]["complete"] else "未通过"), ""]
    if summary["manifest_issues"] or summary["metric_issues"]:
        lines += ["待处理：", ""] + ["- " + issue for issue in summary["manifest_issues"] + summary["metric_issues"]] + [""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dump-audit", type=Path, help="raw_dump_audit.json from audit_dumps.py; required for a completed real full study")
    parser.add_argument("--allow-partial", action="store_true", help="write an explicitly incomplete draft; missing cells stay null")
    args = parser.parse_args()
    audit = strict_json(args.audit)
    require(audit.get("schema") == {"name": "kimi.expgym.audit", "version": 1}, "input is not a supported integrity audit")
    require(sha256(audit["manifest_path"]) == audit["manifest_sha256"], "manifest changed after audit; re-audit first")
    load_runners(audit["repo_root"])
    from expgym.trace_v2 import source_tree_sha256
    require(source_tree_sha256(Path(audit["repo_root"])) == audit["source_tree_sha256"], "repository changed after audit")
    for source in audit.get("data_provenance", {}).values():
        require(sha256(source["path"]) == source["sha256"], "dataset/config/oracle provenance changed after audit")
    for record in audit["records"]:
        if record["status"] == "valid":
            for artifact in [record] + record["agent_records"]:
                require(sha256(artifact["path"]) == artifact["sha256"], "raw artifact changed after audit: " + artifact["path"])
            if record.get("summary_path"):
                require(sha256(record["summary_path"]) == record["summary_sha256"], "PoolAct summary changed after audit")
    for receipt in audit.get("receipts", []):
        require(sha256(receipt["path"]) == receipt["sha256"], "execution receipt changed after audit")
        require(not receipt.get("stdout_sha256") or sha256(receipt["stdout_log"]) == receipt["stdout_sha256"],
                "execution receipt/log changed after audit")
    promotion = audit.get("promotion")
    if promotion and promotion.get("sha256"):
        require(sha256(promotion["path"]) == promotion["sha256"], "promotion map changed after audit")
        for job in promotion["plan"]["jobs"]:
            require(sha256(job["preserved_status_path"]) == job["source_status_sha256"]
                    and sha256(job["preserved_stdout_log"]) == job["source_stdout_sha256"],
                    "preserved pilot execution evidence changed")
    require(audit["complete"] or args.allow_partial, "audit incomplete; use --allow-partial for incomplete draft")
    oracle = args.oracle or Path(audit["repo_root"]) / "data/hpo_tuning/oracle3.json"
    output = args.output_dir or args.audit.resolve().parent / ("summary_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
    require(not output.exists(), "report output directory already exists; use a new path")
    summary = summarize(audit, oracle)
    summary["audit_path"], summary["audit_sha256"] = str(args.audit.resolve()), sha256(args.audit)
    summary["summarizer_path"], summary["summarizer_sha256"] = str(Path(__file__).resolve()), sha256(__file__)
    if args.dump_audit:
        dump = strict_json(args.dump_audit)
        require(dump["manifest_sha256"] == audit["manifest_sha256"], "dump audit belongs to a different manifest")
        require(dump["complete"] or args.allow_partial, "raw API dump audit incomplete")
        verify_dump_trace_links(audit, dump)
        for record in dump.get("files", []):
            if record.get("sha256"):
                require(sha256(record["path"]) == record["sha256"], "raw API dump changed after audit: " + record["path"])
        summary["dump_audit"] = {key: dump.get(key) for key in ("complete", "totals", "selected_totals",
                                                              "selected_success_totals", "historical_totals", "issues", "warnings")}
        summary["dump_audit"].update(path=str(args.dump_audit.resolve()), sha256=sha256(args.dump_audit))
        summary["dump_audit"]["usage_notes"] = "selected_success_totals are trace-comparable logical successes; selected_totals include their retry attempts. reasoning_tokens are already included in output_tokens."
        summary["complete"] = summary["complete"] and dump["complete"]
    elif audit["complete"] and audit["stage"] == "full" and audit.get("backend") != "fake":
        raise ValueError("completed real full study requires --dump-audit to verify retained raw API calls")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "summary.json", summary)
    for key in ("artifacts", "agents", "task_metrics", "aggregate_metrics"):
        write_csv(output / (key + ".csv"), summary[key])
    with (output / "REPORT.zh.md").open("x", encoding="utf-8") as handle:
        handle.write(report_markdown(summary))
    print("Report: %s (complete=%s)" % (output / "REPORT.zh.md", summary["complete"]))
    return 0 if summary["complete"] or args.allow_partial else 2


if __name__ == "__main__":
    raise SystemExit(main())
