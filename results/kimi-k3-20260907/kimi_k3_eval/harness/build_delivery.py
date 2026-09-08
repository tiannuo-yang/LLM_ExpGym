#!/usr/bin/env python3
"""Build concise, evidence-linked delivery tables from a passed result summary.

This is a presentation step: no benchmark execution or new LLM calls. Input
JSON/CSV and audit fingerprints must agree. Output must be a new directory.
Unknown optional evidence remains null; smoke/pilot never masquerade as full.
"""
from __future__ import annotations

import argparse
import collections
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from audit_results import FULL_COUNTS, finite, require, sha256, strict_json, write_csv, write_json
from summarize_results import summarize, verify_dump_trace_links


REGIMES = ("cost_free", "cost_moderate", "cost_tight")
REGIME_LABELS = {"cost_free": "Free", "cost_moderate": "Moderate", "cost_tight": "Tight"}
STRATEGIES = ("naive", "cached", "poolact")
EXP_COLUMNS = [
    ("ParamNet Gap", "paramnet", "Gap_pct"),
    ("NAS201 Gap", "nasbench201", "Gap_pct"),
    ("NAS101 Gap", "nasbench101", "Gap_pct"),
    ("whois F1", "whois", "F1_pct"),
    ("whatis F1", "whatis", "F1_pct"),
    ("Audit LA", "audit", "LA_pct"),
    ("Audit EA", "audit", "EA_pct"),
]
POOL_COLUMNS = [
    ("whois MV", "whois", "MV_F1_pct"),
    ("whois MI", "whois", "MI_F1_pct"),
    ("Audit LA", "audit", "LA_pct"),
    ("Audit EA", "audit", "EA_pct"),
    ("NAS101A BoN", "nasbench101", "BoN_Gap_pct"),
    ("NAS101A MI", "nasbench101", "MI_Gap_pct"),
]


def reference(path):
    path = Path(path).absolute()
    require(path.is_file(), "evidence file missing: " + str(path))
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def optional_json(path):
    return {"reference": reference(path), "data": strict_json(path)} if path else None


def verify_reference(path, expected, description):
    result = reference(path)
    require(result["sha256"] == expected, description + " changed after validation")
    return result


def csv_value(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    return str(value)


def verify_csv(path, expected):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        actual = list(reader)
        fields = reader.fieldnames
        wanted = set(key for row in expected for key in row)
        require(fields and len(fields) == len(set(fields)) and set(fields) == wanted,
                "CSV field list differs from JSON: " + str(path))
    require(len(actual) == len(expected), "CSV row count differs from JSON: " + str(path))
    for number, (left, right) in enumerate(zip(actual, expected), 2):
        for key in fields:
            expected_value = right.get(key)
            equal = json.loads(left[key]) == expected_value if isinstance(expected_value, (dict, list)) else left[key] == csv_value(expected_value)
            require(equal, "CSV differs from summary JSON at %s:%d (%s)" % (path, number, key))
    return reference(path)


def metric_index(summary):
    result = {}
    for row in summary["aggregate_metrics"]:
        key = (row["subset"], row["system"], row["cost_regime"], row.get("strategy"), row["dimension"], row["metric"])
        require(key not in result, "duplicate aggregate metric identity: " + str(key))
        result[key] = row
    return result


def wide_tables(summary):
    index = metric_index(summary)
    cells, expgym, poolact = [], [], []
    def cell(subset, system, regime, strategy, label, dimension, metric):
        row = index.get((subset, system, regime, strategy, dimension, metric))
        value = row.get("value") if row and row.get("complete") is True else None
        require(value is None or finite(value), "nonfinite presentation value")
        cells.append({"table": "expgym" if system == "expgym" else "poolact_paper",
                      "regime": regime, "strategy": strategy, "column": label, "value": value,
                      "source_metric": row, "unit": "percent"})
        return value
    for regime in REGIMES:
        row = {"Regime": REGIME_LABELS[regime]}
        for label, dimension, metric in EXP_COLUMNS:
            row[label] = cell("full", "expgym", regime, None, label, dimension, metric)
        expgym.append(row)
    for regime in REGIMES[1:]:
        for strategy in STRATEGIES:
            row = {"Regime": REGIME_LABELS[regime], "Strategy": strategy}
            for label, dimension, metric in POOL_COLUMNS:
                row[label] = cell("paper_poolact", "poolact", regime, strategy, label, dimension, metric)
            poolact.append(row)
    if summary["stage"] == "full":
        require(all(cell["value"] is not None for cell in cells), "full delivery has missing primary metric cells")
        paper_tasks = {row["item_id"] for row in summary["task_metrics"]
                       if row["subset"] == "paper_poolact" and row["scenario"] == "tuning"}
        require(paper_tasks == {"hpobench:nasbench101:A"}, "paper tuning subset is not exactly NAS101A")
    extension = [row for row in summary["aggregate_metrics"] if row["subset"] == "full" and row["system"] == "poolact"]
    return {"expgym": expgym, "poolact_paper": poolact, "poolact_full_extension": extension, "cells": cells}


def coverage(summary, audit):
    expected, valid = summary["expected_counts"], summary["valid_counts"]
    observed = collections.Counter()
    for row in summary["artifacts"]:
        require(row["status"] == "valid", "nonvalid artifact in passed summary")
        observed["expgym_traces" if row["system"] == "expgym" else "poolact_results"] += 1
        if row["system"] == "poolact" and row["paper_subset"]:
            observed["poolact_paper_results"] += 1
    for row in summary["agents"]:
        if row["system"] == "poolact":
            observed["poolact_agent_traces"] += 1
            if row["paper_subset"]:
                observed["poolact_paper_agent_traces"] += 1
    observed["total_agent_traces"] = observed["expgym_traces"] + observed["poolact_agent_traces"]
    require(expected == audit["expected_counts"] and valid == audit["valid_counts"], "summary/audit coverage mismatch")
    for field in FULL_COUNTS:
        require(observed[field] == expected.get(field, 0), "observed/expected coverage differs: " + field)
        if field != "total_agent_traces":
            require(observed[field] == valid.get(field, 0), "observed/validated coverage differs: " + field)
    if summary["stage"] == "full":
        require(all(observed[key] == value for key, value in FULL_COUNTS.items()), "full coverage differs from fixed study")
    return [{"metric": key, "expected_this_stage": expected.get(key), "validated_this_stage": observed[key],
             "full_target": target} for key, target in FULL_COUNTS.items()]


def usage_view(group):
    if group is None:
        return None
    result = {key: group.get(key) for key in (
        "http_attempts", "successful_logical_calls", "failed_http_attempts", "in_progress_http_attempts",
        "usage_unreported_http_attempts", "retry_delay_seconds_sum", "request_wall_seconds_sum",
        "request_latency_seconds_p50", "request_latency_seconds_p95", "request_latency_seconds_max",
        "finish_reasons", "finish_reason_length_attempts", "reasoning_content_chars_reported_attempts",
        "reasoning_content_chars_nonempty_attempts", "nonempty_reasoning_content_attempts", "reasoning_content_chars_sum",
        "reasoning_tokens_top_level_reported_attempts", "reasoning_tokens_nested_reported_attempts",
        "reasoning_tokens_conflicting_attempts", "nonempty_reasoning_content_with_zero_reported_tokens_attempts",
        "reasoning_tokens_selected_sources", "reasoning_warning_counts")}
    attempts = group.get("http_attempts")
    for token in ("input_tokens", "output_tokens", "reasoning_tokens", "cached_input_tokens"):
        reported = group.get(token + "_reported_attempts")
        result[token + "_known_sum"] = group.get(token)
        result[token + "_reported_attempts"] = reported
        result[token + "_total"] = group.get(token) if reported == attempts and attempts is not None else None
    return result


def diagnostics_from_summary(summary):
    output = {}
    for system in ("expgym", "poolact"):
        rows = [row for row in summary["agents"] if row["system"] == system]
        output[system] = {"agent_traces": len(rows),
                          "aborted_true": sum(row.get("aborted") is True for row in rows),
                          "aborted_false": sum(row.get("aborted") is False for row in rows),
                          "aborted_unreported": sum(row.get("aborted") is None for row in rows),
                          "termination_reasons": dict(collections.Counter(row["termination_reason"] for row in rows if row.get("termination_reason") is not None)),
                          "termination_reason_unreported": sum(row.get("termination_reason") is None for row in rows)}
    return output


def protocol_view(attachment, manifest, dump):
    """Present schema-2 inferences separately, bound to audited client sessions."""
    if attachment is None or not isinstance(attachment["data"], dict) or attachment["data"].get("schema_version") != 2:
        return None
    data = attachment["data"]
    for field in ("stage", "settings", "source_tree_sha256"):
        require(data.get(field) == manifest.get(field), "protocol diagnostic %s differs from manifest" % field)
    require(data.get("expected_counts") == manifest.get("counts"), "protocol diagnostic expected_counts differs from manifest")
    require(dump is not None, "schema-2 protocol diagnostic requires an audited raw dump")
    expected = {row["client_id"]: row for row in dump["records"] if row.get("status") == "valid"}
    rows = data.get("trace_rows")
    require(isinstance(rows, list), "protocol diagnostic trace_rows missing")
    require(len(rows) == len(expected) and {row.get("client_id") for row in rows} == set(expected),
            "protocol diagnostic client sessions differ from audited traces")
    for row in rows:
        selected = expected[row["client_id"]]
        trace_path = Path(row["path"])
        if not trace_path.is_absolute():
            trace_path = Path(__file__).resolve().parents[2] / trace_path
        require(trace_path.resolve() == Path(selected["trace_path"]).resolve(),
                "protocol diagnostic path differs from audited trace")
        require(row.get("runner") == selected["system"] and row.get("raw_success_request_ids") ==
                [call["successful_request_id"] for call in selected["calls"]],
                "protocol diagnostic successful requests differ from audited traces")
    fields = ("forced_final_calls", "raw_native_responses", "raw_native_calls", "trace_native_messages",
              "native_before_missing_action", "normal_responses_over_8000_chars",
              "cap_removed_action_parser_candidates", "cap_removed_known_tool_json_candidates")
    groups = {}
    for system in ("all", "expgym", "poolact"):
        selected = [row for row in rows if system == "all" or row["runner"] == system]
        group = data.get("groups", {}).get(system)
        require(isinstance(group, dict), "protocol diagnostic group missing: " + system)
        require(group.get("traces") == len(selected) and group.get("termination_reasons") ==
                dict(collections.Counter(row.get("reason") for row in selected)),
                "protocol diagnostic group trace/termination counts differ")
        for field in fields:
            require(all(isinstance(row.get(field), int) and row[field] >= 0 for row in selected)
                    and group.get(field) == sum(row[field] for row in selected),
                    "protocol diagnostic group count differs: " + field)
        require(group["cap_removed_known_tool_json_candidates"] <= group["cap_removed_action_parser_candidates"]
                <= group["normal_responses_over_8000_chars"], "protocol diagnostic cap candidate counts inconsistent")
        groups[system] = {field: group[field] for field in fields}
        groups[system].update(traces=group["traces"], termination_reasons=group["termination_reasons"],
                              missing_action=group["termination_reasons"].get("missing_action", 0),
                              termination_reason_sources=dict(collections.Counter(row.get("reason_source") for row in selected)))
    return {"reference": attachment["reference"], "schema_version": 2, "groups": groups,
            "interpretation": "Diagnostic observations/inferences, not additional serialized result fields or a causal estimate."}


def nas101_hints_view(references, manifest):
    """Only disclose this study-specific retained-hint issue with explicit evidence."""
    evidence = references.get("nas101_hints_status")
    if evidence is None:
        return None
    data = strict_json(evidence["path"])
    require(data.get("schema_version") == 1 and data.get("source_tree_sha256") == manifest["source_tree_sha256"],
            "NAS101 hints evidence belongs to a different source")
    require(data.get("retained_original_paper_hints") is True and data.get("candidate_patch_applied") is False,
            "NAS101 hints evidence does not establish retained original hints")
    files = data.get("files")
    require(isinstance(files, list) and {row.get("role") for row in files} >= {"prompt", "encoding", "candidate_patch"},
            "NAS101 hints evidence lacks prompt/encoding/candidate patch fingerprints")
    for row in files:
        verify_reference(row["path"], row["sha256"], "NAS101 " + row["role"] + " evidence")
    return {"reference": evidence, "source_tree_sha256": data["source_tree_sha256"],
            "retained_original_paper_hints": True, "candidate_patch_applied": False, "files": files,
            "affected_variants": ["B", "C"],
            "interpretation": "A-style original paper/repository hints retained although B/C use different encodings; limits interpretation of B/C results, not a measured causal effect."}


def observed_reasoning(dump, settings):
    """Use raw response fields for nonempty reasoning; zero token count is separate."""
    all_selected, selected_nonempty, chars = 0, 0, 0
    policy_present, policy_matched, request_attempts = 0, 0, 0
    length_responses = []
    for row in dump.get("files", []):
        if row.get("classification") != "selected" or row.get("duplicate_of"):
            continue
        data = strict_json(row["path"])
        request_attempts += 1
        payload = data.get("request_payload")
        if isinstance(payload, dict):
            policy_present += 1
            policy_matched += (payload.get("chat_template_kwargs") == settings.get("chat_template_kwargs")
                               and payload.get("max_tokens") == settings.get("max_tokens"))
        if any(choice.get("finish_reason") == "length" for choice in (data.get("response_json") or {}).get("choices", [])):
            length_responses.append({"path": row["path"], "sha256": row["sha256"],
                                     "request_id": row.get("request_id"), "client_id": row.get("client_id")})
        if data.get("error") or data.get("state") == "in_progress":
            continue
        all_selected += 1
        values = [(choice.get("message") or {}).get("reasoning_content")
                  for choice in (data.get("response_json") or {}).get("choices", [])]
        text = "".join(value for value in values if isinstance(value, str))
        if text:
            selected_nonempty += 1
            chars += len(text)
    return {"selected_success_http_responses": all_selected,
            "responses_with_nonempty_reasoning_content": selected_nonempty,
            "reasoning_content_chars": chars,
            "selected_request_attempts": request_attempts,
            "request_payloads_available": policy_present,
            "request_payloads_matching_thinking_and_token_cap": policy_matched,
            "length_responses": length_responses,
            "source": "selected raw dump response_json.choices[].message.reasoning_content"}


def service_view(service, slurm):
    service_data = service["data"] if service and isinstance(service["data"], dict) else {}
    slurm_data = slurm["data"] if slurm and isinstance(slurm["data"], dict) else {}
    selected = slurm_data
    allocations = slurm_data.get("allocations")
    if isinstance(allocations, list):
        target_id = service_data.get("job_id")
        matching = [row for row in allocations if target_id is not None
                    and str(row.get("JobIDRaw", row.get("job_id"))) == str(target_id)]
        require(len(matching) <= 1, "duplicate Slurm allocation job identity")
        if target_id is not None:
            require(bool(matching), "Slurm receipt does not contain the service job")
        selected = matching[0] if matching else allocations[0] if len(allocations) == 1 else {}
    normalized = {"job_id": selected.get("job_id", selected.get("JobIDRaw")),
                  "account": selected.get("account", selected.get("Account")),
                  "state": selected.get("final_state", selected.get("state", selected.get("State"))),
                  "elapsed_seconds": selected.get("elapsed_seconds"), "gpu_count": selected.get("gpu_count"),
                  "final": selected.get("final", slurm_data.get("final"))}
    if service_data.get("gpu_count") is not None and normalized["gpu_count"] is not None:
        require(service_data["gpu_count"] == normalized["gpu_count"], "service/Slurm allocation GPU count differs")
    def first(key):
        return service_data[key] if key in service_data else normalized.get(key, slurm_data.get(key))
    nodes, replicas = first("nodes"), first("replicas")
    result = {"job_id": first("job_id"), "account": normalized["account"], "partition": selected.get("partition", selected.get("Partition")),
            "nodes": nodes, "node_count": len(nodes) if isinstance(nodes, list) else None,
            "gpu_count": first("gpu_count"),
            "replica_count": len(replicas) if isinstance(replicas, list) else replicas,
            "parallelism_per_replica": first("parallelism_per_replica"),
            "ready_for_benchmark": service_data.get("ready_for_benchmark"),
            "sglang_version": service_data.get("sglang_version"),
            "slurm_final": normalized["final"],
            "slurm_observed_state": normalized["state"],
            "slurm_final_state": normalized["state"] if normalized["final"] is True else None,
            "slurm_elapsed_seconds": normalized["elapsed_seconds"] if normalized["final"] is True else None,
            "slurm_known_elapsed_seconds": normalized["elapsed_seconds"],
            "owned_allocations_final": slurm_data.get("final"),
            "owned_allocations_known_allocated_gpu_hours": slurm_data.get("known_allocated_gpu_hours"),
            "owned_allocations_final_allocated_gpu_hours": slurm_data.get("known_allocated_gpu_hours") if slurm_data.get("final") is True else None,
            "benchmark_request_policy": service_data.get("benchmark_request_policy"),
            "service_receipt": service["reference"] if service else None,
            "slurm_receipt": slurm["reference"] if slurm else None}
    result["allocated_gpu_hours"] = (result["gpu_count"] * result["slurm_elapsed_seconds"] / 3600
                                     if finite(result["gpu_count"]) and finite(result["slurm_elapsed_seconds"]) else None)
    result["known_allocated_gpu_hours"] = (result["gpu_count"] * result["slurm_known_elapsed_seconds"] / 3600
                                           if finite(result["gpu_count"]) and finite(result["slurm_known_elapsed_seconds"]) else None)
    return result


def build(args):
    summary_path = args.summary.absolute()
    summary = strict_json(summary_path)
    require(summary.get("schema") == {"name": "kimi.expgym.summary", "version": 1}, "unsupported summary schema")
    require(summary.get("complete") is True, "delivery requires a passed summary")
    references = {"summary": reference(summary_path)}
    audit_path = args.audit or Path(summary["audit_path"])
    references["audit"] = verify_reference(audit_path, summary["audit_sha256"], "result audit")
    audit = strict_json(audit_path)
    require(audit.get("complete") is True, "result audit did not pass")
    manifest_path = Path(summary["manifest_path"])
    references["manifest"] = verify_reference(manifest_path, summary["manifest_sha256"], "manifest")
    manifest = strict_json(manifest_path)
    require(audit["manifest_sha256"] == summary["manifest_sha256"], "result audit belongs to a different manifest")
    require(manifest["stage"] == summary["stage"] == audit["stage"], "stage identity mismatch")
    require(manifest["settings"]["model"] == summary["model_id"] == audit["model_id"], "model identity mismatch")
    require(manifest["settings"]["backend"] == summary["backend"] == audit["backend"], "backend identity mismatch")
    require(manifest["study_type"] == summary["study_type"] == audit["study_type"], "study type identity mismatch")
    require(manifest["source_tree_sha256"] == audit["source_tree_sha256"], "source identity mismatch")
    verify_reference(summary["oracle_path"], summary["oracle_sha256"], "normalization oracle")
    require(summary["oracle_sha256"] == manifest["data_provenance"]["oracle"]["sha256"], "summary uses another normalization oracle")
    reconstructed = summarize(audit, Path(summary["oracle_path"]))
    for key in ("artifacts", "agents", "task_metrics", "aggregate_metrics", "resources"):
        require(reconstructed[key] == summary[key], "summary %s differs from reconstruction using audited metrics" % key)
    for kind in ("artifacts", "agents", "task_metrics", "aggregate_metrics"):
        references[kind + "_csv"] = verify_csv(summary_path.parent / (kind + ".csv"), summary[kind])
    for name, source in manifest.get("data_provenance", {}).items():
        references[name] = verify_reference(source["path"], source["sha256"], "data provenance " + name)
    for row in audit["records"]:
        for artifact in [row] + row["agent_records"]:
            verify_reference(artifact["path"], artifact["sha256"], "raw result")
        if row.get("summary_sha256"):
            verify_reference(row["summary_path"], row["summary_sha256"], "PoolAct item summary")
    dump_path = args.dump_audit or (Path(summary["dump_audit"]["path"]) if summary.get("dump_audit") else None)
    dump = None
    if dump_path:
        dump = strict_json(dump_path)
        require(dump.get("complete") is True and dump["manifest_sha256"] == summary["manifest_sha256"], "raw dump audit did not pass or belongs to another manifest")
        verify_dump_trace_links(audit, dump)
        if summary.get("dump_audit"):
            require(sha256(dump_path) == summary["dump_audit"]["sha256"], "dump audit differs from summarized evidence; regenerate summary first")
        references["dump_audit"] = reference(dump_path)
        for row in dump.get("files", []):
            if row.get("sha256"):
                verify_reference(row["path"], row["sha256"], "raw API dump")
    require(dump is not None or summary.get("backend") == "fake", "real delivery requires passed raw dump audit")
    attachments = {name: optional_json(getattr(args, name)) for name in
                   ("runtime_estimate", "protocol_diagnostics", "service_receipt", "slurm_receipt")}
    service = attachments["service_receipt"]
    slurm = attachments["slurm_receipt"]
    if service and isinstance(service["data"], dict) and service["data"].get("base_url"):
        require(service["data"]["base_url"].rstrip("/") == manifest["settings"]["base_url"].rstrip("/"),
                "service receipt endpoint differs from evaluated endpoint")
    if service and slurm and isinstance(service["data"], dict) and isinstance(slurm["data"], dict):
        for field in ("job_id", "gpu_count"):
            if service["data"].get(field) is not None and slurm["data"].get(field) is not None:
                require(str(service["data"][field]) == str(slurm["data"][field]), "service/Slurm receipt %s differs" % field)
    for name, value in attachments.items():
        if value:
            references[name] = value["reference"]
            data = value["data"]
            if isinstance(data, dict) and data.get("raw_file") and data.get("raw_sha256"):
                references[name + "_raw"] = verify_reference(data["raw_file"], data["raw_sha256"], name + " raw evidence")
    if args.paper_alignment:
        references["paper_alignment"] = reference(args.paper_alignment)
    for specification in args.evidence:
        name, separator, path = specification.partition("=")
        require(separator and name and name not in references, "--evidence must be a unique NAME=PATH")
        references[name] = reference(path)
    settings = manifest["settings"]
    tables = wide_tables(summary)
    full = summary["stage"] == "full" and summary.get("backend") != "fake"
    usage = {key: usage_view(dump.get(key)) if dump else None for key in
             ("totals", "selected_totals", "selected_success_totals", "historical_totals", "unassigned_totals")}
    return {"schema": {"name": "kimi.expgym.delivery", "version": 1},
            "created_at": datetime.now(timezone.utc).isoformat(), "builder_path": str(Path(__file__).resolve()),
            "builder_sha256": sha256(__file__), "stage": summary["stage"], "backend": summary.get("backend"),
            "model_id": summary["model_id"], "study_type": summary["study_type"],
            "this_stage_audited_complete": True, "official_full_matrix_complete": full,
            "coverage": coverage(summary, audit), "tables": tables, "references": references,
            "execution_resources": summary["resources"], "usage": usage,
            "observed_reasoning": observed_reasoning(dump, settings) if dump else None,
            "request_policy": {key: settings.get(key) for key in (
                "max_steps", "max_evals", "poolact_agents", "temperature_tuning", "temperature_eval",
                "temperature_poolact", "seed", "chat_template_kwargs", "max_tokens", "poolact_protocol")},
            "diagnostics": diagnostics_from_summary(summary),
            "protocol_inferences": protocol_view(attachments["protocol_diagnostics"], manifest, dump),
            "nas101_hints_status": nas101_hints_view(references, manifest),
            "runtime_estimate": attachments["runtime_estimate"],
            "protocol_diagnostics": attachments["protocol_diagnostics"],
            "service": service_view(attachments["service_receipt"], attachments["slurm_receipt"]),
            "promotion": summary.get("promotion"), "dump_warnings": dump.get("warnings") if dump else None}


def fmt(value, digits=2):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return ("%." + str(digits) + "f") % value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def md_table(rows):
    if not rows:
        return ["无可用数据。"]
    fields = list(rows[0])
    return ["| " + " | ".join(fields) + " |", "|" + "|".join("---" for _ in fields) + "|"] + [
        "| " + " | ".join(fmt(row.get(field)).replace("|", "\\|") for field in fields) + " |" for row in rows]


def md_link(label, path, output):
    relative = Path(os.path.relpath(str(path), str(output))).as_posix()
    return "[%s](<%s>)" % (label, relative)


def overview(delivery, output):
    full = delivery["official_full_matrix_complete"]
    stage = delivery["stage"].upper()
    title = "Kimi-K3：ExpGym / PoolAct 全量结果" if full else "%s 验证报告：非正式全量结果" % stage
    if delivery["backend"] == "fake":
        title = "STATIC/FAKE 验证：不代表 Kimi-K3 性能"
    lines = ["# " + title, ""]
    if not full:
        lines += ["> 本报告只验证 %s 所选子集；不代表 303 ExpGym + 513 PoolAct 的正式矩阵完成，也不表示论文设定的统计结果。" % stage, ""]
    audit_statement = ("本阶段结果和原始 API dump 均通过对应审计。" if delivery["observed_reasoning"] is not None else
                       "本阶段为 fake backend 程序验证，无真实 API dump。")
    lines += ["模型：" + delivery["model_id"] + "；实验类型：" + delivery["study_type"] + "。" + audit_statement, "",
              "## 覆盖与核心结果", ""]
    labels = {"expgym_traces": "ExpGym traces", "poolact_results": "PoolAct results",
              "poolact_agent_traces": "PoolAct agent traces", "total_agent_traces": "全部 agent traces",
              "poolact_paper_results": "论文 PoolAct 子集 results", "poolact_paper_agent_traces": "论文 PoolAct 子集 agents"}
    rows = [{"项目": labels[row["metric"]], "本阶段通过/计划": "%s/%s" % (row["validated_this_stage"], row["expected_this_stage"]),
             "正式全量目标": row["full_target"]} for row in delivery["coverage"]]
    lines += md_table(rows) + [""]
    title_suffix = "" if full else "（%s 所选小样本）" % stage
    lines += ["### ExpGym：" + "七维度宽表" + title_suffix, "",
              "数值单位为 %，所有指标均为越高越好；Gap 是相对随机均值的改进比例，不是剩余误差。Gap 每 trace 先归一化并裁剪至不低于 0，再按 repeats/task 与 tasks/family 求均值，可以超过 100。", ""]
    lines += md_table(delivery["tables"]["expgym"]) + [""]
    lines += ["### PoolAct：论文子集" + title_suffix, "",
              "Moderate/Tight；正式子集为 18 whois + 13 Audit + NAS101:A。MV 是多数票、MI 是 agent 均值、BoN 是 best-of-N；Tuning MI 逐 agent 先算 clipped Gap。", ""]
    lines += md_table(delivery["tables"]["poolact_paper"]) + [""]
    if not full:
        lines += ["上表空白表示本阶段未覆盖；非空格也只来自本阶段所选 task。每格的样本数和原始路径保存在 delivery.json 的 tables.cells。", ""]
    extension_label = ("全量扩展（含 cost_free、whatis 和其余 HPO tasks）" if full else
                       "%s 本阶段已覆盖的 PoolAct 扩展（尚非全量）" % stage)
    lines += [extension_label + "独立导出：" +
              md_link("PoolAct full extension CSV", output / "poolact_full_extension.csv", output) + "。", ""]
    if full:
        exp_rows = delivery["tables"]["expgym"]
        delta = ["%s %+.2f" % (label, exp_rows[2][label] - exp_rows[0][label])
                 for label, _, _ in EXP_COLUMNS if finite(exp_rows[0][label]) and finite(exp_rows[2][label])]
        lines += ["Free→Tight 变化（百分点）：" + "；".join(delta) + "。", ""]
        for regime in ("Moderate", "Tight"):
            by_strategy = {row["Strategy"]: row for row in delivery["tables"]["poolact_paper"] if row["Regime"] == regime}
            delta = ["%s %+.2f" % (label, by_strategy["poolact"][label] - by_strategy["naive"][label])
                     for label in ("whois MV", "Audit LA", "NAS101A BoN")]
            lines += ["%s 下 PoolAct−naive（百分点）：%s。" % (regime, "；".join(delta)), ""]
    lines += ["## 耗时、调用与运行证据", ""]
    resources = delivery["execution_resources"]
    selected = delivery["usage"]["selected_totals"] or {}
    logical = delivery["usage"]["selected_success_totals"] or {}
    historical = delivery["usage"]["historical_totals"] or {}
    rows = [{"指标": name, "值": value} for name, value in (
        ("真实执行跨度（秒）", resources.get("study_execution_span_seconds")),
        ("全部 subprocess 尝试累计（秒，含并发重叠）", resources.get("sum_subprocess_attempt_wall_seconds")),
        ("其中复用 pilot 的原始尝试（秒）", resources.get("sum_promoted_pilot_subprocess_attempt_wall_seconds")),
        ("历史尝试缺失耗时条数", resources.get("missing_subprocess_attempt_wall_count")),
        ("模拟反馈预算合计（秒，非实际墙钟）", resources.get("sum_simulated_feedback_cost_seconds")),
        ("当前结果逻辑成功调用", logical.get("successful_logical_calls")),
        ("当前结果 HTTP 尝试（含重试）", selected.get("http_attempts")),
        ("当前结果失败 HTTP 尝试", selected.get("failed_http_attempts")),
        ("当前结果 input tokens（含重试）", selected.get("input_tokens_total")),
        ("当前结果 output tokens（含重试）", selected.get("output_tokens_total")),
        ("历史未选中 HTTP 尝试", historical.get("http_attempts")),
        ("finish_reason=length 次数", selected.get("finish_reason_length_attempts")))]
    lines += md_table(rows) + ["", "并发累计秒数不可当作端到端墙钟；复用 pilot 的原始执行成本单列。reasoning tokens 若被提供，已包含在 output tokens 中，不再加一次。未知时间或未完整报告的 token 总量保留 null（表中 —）。", ""]
    project_usage = delivery["references"].get("project_usage_inventory")
    if project_usage:
        lines += ["以上调用统计仅覆盖本阶段 manifest，不是整个开发/恢复过程的总消耗。跨阶段已留存评测请求及其去重范围见 " +
                  md_link("项目 API 消耗清单", project_usage["path"], output) +
                  "；其他版本、smoke 与失败任务不混入本表成绩。服务验收探针和后台 health 请求不属于评测 dump 清单；Slurm 分配时长仍包含服务占用时间。", ""]
    truncated = (delivery.get("observed_reasoning") or {}).get("length_responses") or []
    if truncated:
        lines += ["已观察到 provider 标记的 length 截断，这是输出 token cap 的实现边界及协议诊断信息；保留原始回答和评分。示例：" +
                  "、".join(md_link("dump %d" % (index + 1), row["path"], output) for index, row in enumerate(truncated[:3])) +
                  "；全部路径见 delivery.json 的 observed_reasoning.length_responses。", ""]
    service = delivery["service"]
    rows = [{"Slurm job": service["job_id"], "Account": service["account"], "Nodes": service["node_count"],
             "GPUs": service["gpu_count"], "Replicas": service["replica_count"],
             "每副本并行": service["parallelism_per_replica"], "采集时状态": service["slurm_observed_state"],
             "最终状态": service["slurm_final_state"]}]
    lines += md_table(rows) + [""]
    rows = [{"Allocated GPU-hours 范围": label, "采集时已知值": known, "最终值": final}
            for label, known, final in (
                ("服务 allocation", service["known_allocated_gpu_hours"], service["allocated_gpu_hours"]),
                ("本项目全部 owned allocations", service["owned_allocations_known_allocated_gpu_hours"],
                 service["owned_allocations_final_allocated_gpu_hours"]))]
    lines += md_table(rows) + ["", "Slurm 最终状态和最终总量只取明确 final=true 的 receipt；服务 ready 或部署文件不等于作业已结束。运行中快照不是最终成本。Allocated GPU-hours 为已确认分配 GPU 数 × allocation 墙钟，包含加载、验证及空闲，不代表 GPU 利用率，也不重复累加 step/extern。", ""]
    runtime = delivery["runtime_estimate"]
    if runtime:
        estimate = runtime["data"] if isinstance(runtime["data"], dict) else {}
        lines += ["Pilot 外推证据：" + md_link("runtime estimate", runtime["reference"]["path"], output) +
                  "；原预测剩余小时范围 " + fmt(estimate.get("remaining_wall_time_hours_range")) +
                  "，这是当时预测，不替代上述实测耗时。", ""]
    else:
        lines += ["Runtime estimate：未附证据（null）。", ""]
    lines += ["## 设置、偏离与协议诊断", ""]
    policy = delivery["request_policy"]
    lines += ["请求参数：chat_template_kwargs=%s；max_tokens=%s；max_steps/max_evals=%s/%s；PoolAct agents=%s；协议=%s。" %
              (fmt(policy["chat_template_kwargs"]), fmt(policy["max_tokens"]), fmt(policy["max_steps"]),
               fmt(policy["max_evals"]), fmt(policy["poolact_agents"]), fmt(policy["poolact_protocol"])), ""]
    observed = delivery["observed_reasoning"]
    if observed:
        lines += ["原始选中请求里 %s/%s 条匹配上述 thinking/token cap，%s 条保留 request payload。" %
                  (observed["request_payloads_matching_thinking_and_token_cap"], observed["selected_request_attempts"],
                   observed["request_payloads_available"]), ""]
        lines += ["实际选中响应中 %s/%s 条含非空 reasoning_content，共 %s 字符。thinking=false 表示请求设定；reasoning_content 也可能来自服务 parser 对标记的分段，不能仅据此判断模型中途开启思考，或凭 token counter 为 0 声称没有该文本字段。" %
                  (observed["responses_with_nonempty_reasoning_content"], observed["selected_success_http_responses"], observed["reasoning_content_chars"]), ""]
        lines += ["Provider reasoning token counter：%s（%s/%s 次有报告，嵌套/顶层来源冲突 %s 次）；非空 reasoning 文本且报告 0 token 的响应 %s 次。字段来源冲突与文本/计数观察警告均保留在 delivery.json 的 dump_warnings。" %
                  (fmt(selected.get("reasoning_tokens_total")), fmt(selected.get("reasoning_tokens_reported_attempts")),
                   fmt(selected.get("http_attempts")), fmt(selected.get("reasoning_tokens_conflicting_attempts")),
                   fmt(selected.get("nonempty_reasoning_content_with_zero_reported_tokens_attempts"))), ""]
    service_policy = service.get("benchmark_request_policy") or {}
    if service_policy.get("deviation_from_k3_recommendation") is True:
        lines += ["服务验收另有明确偏差：本次 thinking=false 请求不同于 K3 推荐的 always-thinking 用法；服务原生默认未被修改。", ""]
    lines += ["Kimi-K3 与本地 SGLang 是论文外的新模型/提供商；max_tokens=%s 是本次记录的实现参数。当前协议记录为 %s；paper-graph-lock-v2 为修正后的 locked 实现，论文历史表含 locked/prelock 两类。历史 tuning outer-repeat 数量未公开。Audit EA 为证据集合精确匹配，不要求 label 同时正确。" %
              (fmt(policy["max_tokens"]), fmt(policy["poolact_protocol"])), ""]
    hints = delivery.get("nas101_hints_status")
    if hints:
        lines += ["NAS101 B/C 提示与编码差异（仅适用于证据绑定的本次 source）：B/C 原提示沿用 A 型二进制边描述，但实际 B 为反序 column bit-ID 编码，C 为 top-k 边优先值编码。本次保留原 paper/repo 提示，候选修正 patch 未应用；这限制 B/C 结果的解释，不代表已测得该差异对分数的因果影响。证据：" +
                  md_link("NAS101 hints status", hints["reference"]["path"], output) + "。", ""]
    else:
        lines += ["NAS101 B/C 提示/编码差异状态：未附与本次 source 绑定的显式证据（null），不推定其他研究具有相同问题。", ""]
    diag_rows = [{"系统": system, "aborted=true": value["aborted_true"], "总 agents": value["agent_traces"],
                  "原字段记录到的终止原因": value["termination_reasons"] or None,
                  "终止原因未记录": value["termination_reason_unreported"]} for system, value in delivery["diagnostics"].items()]
    lines += md_table(diag_rows) + ["", "上表仅统计序列化原字段；未记录显示 null（—），不代表终止次数为零。aborted 可由预算、horizon 或指令解析触发，随后仍可能强制回答并通过重评分；不把有效语义零分标成软件失败。", ""]
    inference = delivery.get("protocol_inferences")
    if inference:
        lines += ["### 独立诊断观察与推断（不补写原字段）", "",
                  "以下仅使用与已审计 client_id/成功 request_id 对齐的 schema2 诊断。ExpGym 的 trace_v2_outcome 来源为原字段；PoolAct 的 inferred_from_saved_forced_prompt 来源是保存的强制回答提示与 aborted 标记推断，不能当作已序列化的 termination_reason。", ""]
        groups = inference["groups"]
        rows = [{"范围": system, "agents": group["traces"], "missing_action（含推断）": group["missing_action"],
                 "forced-final 调用": group["forced_final_calls"], "原始 native 响应": group["raw_native_responses"],
                 "native 后 missing_action traces": group["native_before_missing_action"]}
                for system, group in groups.items()]
        lines += md_table(rows) + ["", "native 是响应中的 K3 XTML 工具标记观察；与 missing_action 的先后共现不单独证明因果，也不等于工具实际执行或语义评分失败。", ""]
        rows = [{"范围": system, "常规响应 >8000 字符": group["normal_responses_over_8000_chars"],
                 "cap 后丢失 Action 解析候选": group["cap_removed_action_parser_candidates"],
                 "其中已知工具名 + 合法 JSON 候选": group["cap_removed_known_tool_json_candidates"]}
                for system, group in groups.items()]
        lines += md_table(rows) + ["", "8000 字符 cap 是常规响应解析前的字符上限，独立于 API 的 max_tokens；forced-final 不受此字符 cap 约束。解析候选可能只是 Thought 中引用的 Action:。已知工具名 + 合法 JSON 仅为静态检查，不证明参数 schema 合法、工具可执行或截断导致最终得分变化；额外逐例复核的结论应查其独立证据。", ""]
    else:
        lines += ["schema2 分组诊断推断：未附适用证据（null）；不从未序列化字段推定 missing_action、forced-final 或 native 次数。", ""]
    if delivery["protocol_diagnostics"]:
        lines += ["补充诊断：" + md_link("protocol diagnostics", delivery["protocol_diagnostics"]["reference"]["path"], output) + "。", ""]
    else:
        lines += ["独立 protocol diagnostics：未附证据（null）；上表仅从已审计 traces 直接计数。", ""]
    lines += ["## 查验入口", ""]
    for name in ("manifest", "summary", "audit", "dump_audit", "artifacts_csv", "agents_csv",
                 "dataset_manifest", "oracle", "paper_alignment", "service_receipt", "slurm_receipt"):
        if name in delivery["references"]:
            lines.append("- " + md_link(name, delivery["references"][name]["path"], output))
    listed = {"manifest", "summary", "audit", "dump_audit", "artifacts_csv", "agents_csv", "dataset_manifest",
              "oracle", "paper_alignment", "service_receipt", "slurm_receipt"}
    for name, value in delivery["references"].items():
        if name not in listed:
            lines.append("- " + md_link(name, value["path"], output))
    lines += ["", "完整文件路径、SHA256、输入 CSV/JSON 一致性和逐格来源见 " +
              md_link("delivery.json", output / "delivery.json", output) + "；原始数据及 dump 保留在索引指向的位置。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--dump-audit", type=Path)
    parser.add_argument("--runtime-estimate", type=Path)
    parser.add_argument("--protocol-diagnostics", type=Path)
    parser.add_argument("--service-receipt", type=Path)
    parser.add_argument("--slurm-receipt", type=Path)
    parser.add_argument("--paper-alignment", type=Path, default=Path(__file__).resolve().parents[1] / "protocol/PAPER_ALIGNMENT.md")
    parser.add_argument("--evidence", action="append", default=[], metavar="NAME=PATH")
    args = parser.parse_args()
    output = args.output_dir.absolute()
    require(not output.exists(), "delivery directory exists; use a new path")
    delivery = build(args)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "delivery.json", delivery)
    write_csv(output / "expgym_wide.csv", delivery["tables"]["expgym"])
    write_csv(output / "poolact_paper_wide.csv", delivery["tables"]["poolact_paper"])
    write_csv(output / "poolact_full_extension.csv", delivery["tables"]["poolact_full_extension"])
    with (output / "OVERVIEW.zh.md").open("x", encoding="utf-8") as handle:
        handle.write(overview(delivery, output))
    print(json.dumps({"overview": str(output / "OVERVIEW.zh.md"), "stage": delivery["stage"],
                      "official_full_matrix_complete": delivery["official_full_matrix_complete"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
