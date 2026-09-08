#!/usr/bin/env python3
"""Read-only scan of retained v2 tuning results; no tool evaluation or API use."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "LLM_ExpGym"))
from expgym.react_loop import _canonicalize_payload, _extract_action, _extract_answer, _lookup_answer_metrics
from expgym.trace_v2 import materialize_message


def read(path):
    path = Path(path).resolve()
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), str(path)
    return json.loads(raw), {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def finite(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def parses_json(value):
    if not isinstance(value, str):
        return False
    try:
        json.loads(value)
    except ValueError:
        return False
    return True


def proposed_lookup(answer, records):
    canonical = _canonicalize_payload(answer)
    for raw, expected, perf, overhead in reversed(records):
        if expected is not None:
            if canonical == expected:
                return perf, overhead
        elif canonical is None and raw in answer:
            return perf, overhead
    return None, None


def boundary_checks():
    records = [['{"x": 1}', '{"x":1}', .9, 1], ['{"x": 2}', '{"x":2}', 0, 2]]
    valid = '{"x": 2}'
    malformed = 'Prose before config {"x": 2}'
    assert _lookup_answer_metrics(valid, records) == proposed_lookup(valid, records) == (0, 2)
    assert _lookup_answer_metrics(malformed, records) == (0, 2)
    assert proposed_lookup(malformed, records) == (None, None)
    best = max(records, key=lambda row: row[2])
    assert best[2] == .9
    legacy = [["nonjson", None, .2, 3]]
    assert _lookup_answer_metrics("prefix nonjson", legacy) == proposed_lookup("prefix nonjson", legacy) == (.2, 3)
    return {"passed": True, "cases": 3, "synthetic_zero_score_counterexample": {
        "classification": "synthetic mechanism illustration only; not an observed model result or an evaluator run",
        "answer": malformed, "eval_records": records, "current_lookup_perf": 0,
        "conditional_scorecheck": "If the task's malformed-final recomputation returns 0, the current reported 0 could pass despite the malformed final.",
        "proposed_lookup_perf": None, "existing_fallback_perf": best[2],
        "meaning": "A source-level fix can affect valid-zero cases in principle; the observed completed-result scan determines whether any were actually present."}}


def normalize(data, system):
    if system == "poolact":
        last = next((m["content"] for m in reversed(data["messages"]) if m["role"] == "assistant"), None)
        return {"answer": data["answer"], "answer_perf": data["answer_perf"], "score_check": data["score_check"],
                "scorecheck_passed": data["score_check"].get("ok"), "answer_source": None,
                "client_id": data["api_dump"]["client_id"], "eval_records": data["eval_records"],
                "eval_records_source": "serialized eval_records", "original_model_final_message": last,
                "original_model_final_answer": (_extract_answer(last) or last) if last is not None else None}
    outcome = data["outcome"]
    last = materialize_message(data, outcome["answer_message_id"])["content"] if outcome.get("answer_message_id") else None
    model_answer = (_extract_answer(last) or last) if last is not None else None
    records = []
    for tool in data["tool_calls"]:
        if tool["name"] != "evaluate_config" or tool.get("visible_to_model") is not True or not finite(tool.get("performance")):
            continue
        action = _extract_action(materialize_message(data, tool["request_message_id"])["content"])
        assert action is not None and action[0] == tool["name"], tool["id"]
        raw = action[1]
        assert json.loads(raw) == tool["arguments"], tool["id"]
        records.append([raw, _canonicalize_payload(raw), tool["performance"], tool["simulated_cost_seconds"]])
    return {"answer": outcome.get("answer_override", model_answer), "answer_perf": outcome["score"].get("value"),
            "score_check": outcome["validation"], "scorecheck_passed": outcome["validation"].get("passed"),
            "answer_source": outcome.get("answer_source"), "client_id": data["run"]["api_dump"]["client_id"],
            "eval_records": records, "original_model_final_message": last, "original_model_final_answer": model_answer,
            "eval_records_source": "reconstructed in tool-call order from visible evaluate_config calls with numeric performance; exact raw from request_message_id/_extract_action; withheld/over-budget excluded"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", action="append", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source_path = BASE / "LLM_ExpGym/expgym/react_loop.py"
    source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    checks = boundary_checks()
    sources, scanned, unique, missing = [], [], {}, []
    for run_dir in args.run_dir:
        manifest, manifest_ref = read(run_dir / "manifest.json")
        progress, progress_ref = read(run_dir / "progress.json")
        source = {"manifest": manifest_ref, "progress_snapshot_reference": progress_ref, "progress_snapshot": progress,
                  "source_tree_sha256": manifest["source_tree_sha256"], "run_dir": str(run_dir.resolve())}
        sources.append(source)
        for job in manifest["jobs"]:
            if job["scenario"] != "tuning":
                continue
            status = progress.get("jobs", {}).get(job["id"], {}).get("status")
            for output in job["expected_outputs"]:
                paths = [output["path"]] if job["system"] == "expgym" else output["agent_paths"]
                for path in paths:
                    if not Path(path).is_file():
                        missing.append({"path": path, "job_id": job["id"], "parent_job_status_at_snapshot": status})
                        continue
                    data, ref = read(path)
                    row = normalize(data, job["system"])
                    answer, perf, records = row["answer"], row["answer_perf"], row["eval_records"]
                    row.update(system=job["system"], item_id=job["item_id"], cost_regime=job["cost_regime"],
                               strategy=output.get("strategy"), serialized_answer_is_json=parses_json(answer),
                               original_model_final_answer_is_json=parses_json(row["original_model_final_answer"]))
                    row["canonical_raw_substring_matching_eval_indices"] = [i for i, rec in enumerate(records)
                        if isinstance(answer, str) and rec[1] is not None and rec[0] in answer]
                    row["candidate"] = (isinstance(answer, str) and not row["serialized_answer_is_json"] and finite(perf)
                                        and bool(row["canonical_raw_substring_matching_eval_indices"]))
                    if isinstance(answer, str):
                        row["current_lookup_perf_overhead"] = _lookup_answer_metrics(answer, records)
                        row["proposed_lookup_perf_overhead"] = proposed_lookup(answer, records)
                        row["lookup_would_change"] = row["current_lookup_perf_overhead"] != row["proposed_lookup_perf_overhead"]
                    else:
                        row["lookup_would_change"] = False
                    if row["candidate"]:
                        best = max((rec for rec in records if finite(rec[2])), key=lambda rec: rec[2], default=None)
                        row["existing_best_evaluated_fallback_record"] = best
                        row["would_enter_existing_fallback"] = row["proposed_lookup_perf_overhead"] == (None, None) and best is not None
                        row["fallback_performance_would_change"] = row["would_enter_existing_fallback"] and best[2] != perf
                    location = dict(ref, run_dir=str(run_dir.resolve()), manifest_sha256=manifest_ref["sha256"], job_id=job["id"],
                                    parent_job_status_at_snapshot=status, result_completion_marker_exists=Path(output["path"]).is_file())
                    key = (row["system"], row["client_id"])
                    if key in unique:
                        assert unique[key]["locations"][0]["sha256"] == ref["sha256"], "same client_id but different result bytes"
                        unique[key]["locations"].append(location)
                    else:
                        row["locations"] = [location]
                        unique[key] = row
                    scanned.append(dict(location, client_id=row["client_id"], system=row["system"], item_id=row["item_id"],
                                        scorecheck_passed=row["scorecheck_passed"], answer_perf=perf,
                                        answer_is_json=row["serialized_answer_is_json"], candidate=row["candidate"],
                                        lookup_would_change=row["lookup_would_change"]))
    for row in scanned:
        assert hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() == row["sha256"], "result changed during scan"
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_digest, "lookup source changed during scan"
    records = list(unique.values())
    candidates = [row for row in records if row["candidate"]]
    failed, failed_ref = read(BASE / "kimi_k3_eval/reports/nas101c_moderate_agent3_diagnostic/evidence.json")
    failed_result = failed["current_source_replay"]["result"]
    failed_answer, failed_records = failed_result["answer"], failed_result["eval_records"]
    failed_matches = [i for i, row in enumerate(failed_records) if row[1] is not None and row[0] in failed_answer]
    assert not parses_json(failed_answer) and failed_matches
    assert _lookup_answer_metrics(failed_answer, failed_records)[0] == failed_result["answer_perf"]
    assert proposed_lookup(failed_answer, failed_records) == (None, None)
    failure = {"classification": "independent check of previously saved offline replay, not a serialized passed result or a new replay",
               "reference": failed_ref, "job_id": failed["job_id"], "agent_id": failed["agent_id"],
               "strategy": failed["strategy"], "client_id": failed["client_id"],
               "raw_files": failed["raw_files"], "original_answer": failed_answer, "answer_perf": failed_result["answer_perf"],
               "eval_records": failed_records, "canonical_raw_substring_matching_eval_indices": failed_matches,
               "current_source_scorecheck": failed["current_source_replay"]["score_check"],
               "candidate_replay_scorecheck": failed["in_memory_candidate_replay"]["score_check"],
               "candidate_answer": failed["in_memory_candidate_replay"]["result"]["answer"],
               "candidate_answer_source": failed["in_memory_candidate_replay"]["result"]["answer_source"]}
    report = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "study_type": "Custom study; offline diagnostic only",
              "script_path": str(Path(__file__).resolve()), "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "lookup_source_path": str(source_path), "lookup_source_sha256": source_digest,
              "sources": sources, "scanned_locations": len(scanned), "unique_client_results": len(records),
              "duplicate_promoted_result_locations": len(scanned) - len(records),
              "scanned_location_counts_by_run": dict(Counter(row["run_dir"] for row in scanned)),
              "candidate_unique_results": len(candidates), "candidate_passed_scorecheck_results": sum(row["scorecheck_passed"] is True for row in candidates),
              "numeric_nonjson_unique_results": sum(finite(row["answer_perf"]) and not row["serialized_answer_is_json"] for row in records),
              "lookup_policy_changed_unique_results": sum(row["lookup_would_change"] for row in records),
              "all_scanned_scorechecks_passed": all(row["scorecheck_passed"] is True for row in records),
              "candidates": candidates, "completed_records": records, "missing_expected_locations": missing,
              "separate_unsaved_failure_evidence": failure, "boundary_checks": checks,
              "limitations": [
                  "Only retained finalized tuning trace/agent files present when scanned; unfinished/missing expected paths are listed and not called zero-score results.",
                  "Progress files are live snapshot references with their full observed JSON preserved here; they may change after this report. Result files and lookup source were checked unchanged during the scan.",
                  "Promotion copies are deduplicated by system/client_id with byte-equality assertion; all original locations and SHA256 retained.",
                  "No API, objective evaluator, model rerun, or rescoring was performed. Hypothetical fallback uses only already recorded evaluations and original max-selection semantics.",
                  "The separate known failed NAS101C agent did not serialize a passed result and is not counted among completed records; consult its independent offline replay evidence.",
                  "Zero candidates in this snapshot does not prove future or unrecorded outputs immune to the bug. A revised source requires a distinct provenance and a uniform newly validated matrix, not silent mixing with old-source results."
              ]}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with (args.output_dir / "evidence.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    with (args.output_dir / "scanned_results.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(scanned[0]))
        writer.writeheader()
        writer.writerows(scanned)
    print(json.dumps({key: report[key] for key in ("scanned_locations", "unique_client_results", "duplicate_promoted_result_locations",
                     "candidate_unique_results", "candidate_passed_scorecheck_results", "lookup_policy_changed_unique_results",
                     "scanned_location_counts_by_run")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
