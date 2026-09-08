#!/usr/bin/env python3
"""Offline scan of all retained raw files for the six nonzero old-full jobs."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "LLM_ExpGym"
STUDY = ROOT / "kimi_k3_eval"
data = REPO / "data/hpo_tuning"
os.environ.update(HPOBENCH_ROOT=str(data / "HPOBench"), XDG_DATA_HOME=str(data / "hpobench_data"),
                  XDG_CACHE_HOME=str(data / "hpobench_cache"), XDG_CONFIG_HOME=str(STUDY / "data_runtime/hpobench_config"),
                  PYTHONNOUSERSITE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
sys.path.insert(0, str(REPO))
from expgym.react_loop import _extract_answer
from expgym.task_tuning import _load_hpobench, evaluate_hpobench_action
from expgym.trace_v2 import source_tree_sha256
from scripts.run_paper_sweep import _score_result

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

audit_path = STUDY / "reports/archived_full_v1_audit_20260907_0936/execution_failures.json"
failures = json.loads(audit_path.read_text())
manifest_path = STUDY / "runs/full/manifest.json"
manifest = json.loads(manifest_path.read_text())
jobs = {row["id"]: row for row in manifest["jobs"]}
result = {"classification": "read-only archived v1 failure diagnosis; not new model results", "new_source_tree_sha256": source_tree_sha256(REPO),
          "execution_failures_path": str(audit_path), "execution_failures_sha256": digest(audit_path),
          "manifest_path": str(manifest_path), "manifest_sha256": digest(manifest_path), "jobs": [], "nas101b_replays": []}
for failure in failures:
    job = jobs[failure["job_id"]]
    assert digest(failure["path"]) == failure["sha256"]
    assert digest(failure["stdout_log"]) == failure["stdout_sha256"]
    log_bytes = Path(failure["stdout_log"]).read_bytes()
    receipt = failure["receipt"]
    log = log_bytes[receipt["stdout_start_byte"]:receipt["stdout_end_byte"]].decode()
    row = {"job_id": job["id"], "receipt_status": receipt["status"], "returncode": receipt["returncode"],
           "stdout_log": failure["stdout_log"], "stdout_sha256": failure["stdout_sha256"],
           "attempt_stdout": log, "files": [], "sessions": [], "tool_error_observations": []}
    sessions = collections.defaultdict(list)
    observations = set()
    states, finish, transport_errors = collections.Counter(), collections.Counter(), []
    for path in sorted(Path(job["dump_dir"]).glob("*.json")):
        raw = json.loads(path.read_text())
        context = raw["context"].get("job", raw["context"])
        assert context["scenario"] == "tuning"
        choices = (raw.get("response_json") or {}).get("choices", [])
        content = "\n".join(choice.get("message", {}).get("content") or "" for choice in choices)
        fields = {"path": str(path), "sha256": digest(path), "request_id": raw["request_id"],
                  "client_id": raw["client_id"], "context": raw["context"], "state": raw["state"],
                  "error": raw.get("error"), "will_retry": raw.get("will_retry"),
                  "finish_reasons": [choice.get("finish_reason") for choice in choices],
                  "response_chars": len(content), "response_exceeds_existing_8000char_loop_cap": len(content) > 8000}
        row["files"].append(fields)
        states[raw["state"]] += 1
        for reason in fields["finish_reasons"]:
            finish[reason] += 1
        if raw.get("error") or raw.get("state") != "success":
            transport_errors.append(fields)
        sessions[raw["client_id"]].append((raw, fields, content))
        for message in raw["request_payload"].get("messages", []):
            if message.get("role") != "user":
                continue
            text = message.get("content") or ""
            observations.update(re.findall(r"Tool error: ([^\n]*)", text))
    row.update(raw_files=len(row["files"]), states=dict(states), finish_reasons=dict(finish),
               transport_error_files=transport_errors, tool_error_observations=sorted(observations))
    for client_id, calls in sessions.items():
        calls.sort(key=lambda entry: entry[0]["started_at_utc"])
        raw, fields, content = calls[-1]
        answer = _extract_answer(content) or content
        session = {"client_id": client_id, "calls": len(calls), "context": raw["context"], "last_raw": fields,
                   "last_content": content, "new_extracted_answer": answer}
        row["sessions"].append(session)
        context = raw["context"].get("job", raw["context"])
        if job["tuning_task"] != "hpobench:nasbench101:B":
            continue
        config = None
        try:
            config = json.loads(answer)
        except (TypeError, ValueError):
            pass
        task = _load_hpobench(job["tuning_task"])
        names = {hp.name for hp in task.config_space.get_hyperparameters()}
        unknown = sorted(set(config) - names) if isinstance(config, dict) else []
        if not unknown:
            continue
        guard = Mock(side_effect=AssertionError("invalid input must not call benchmark"))
        guarded = SimpleNamespace(name=task.name, config_space=task.config_space, fidelity=task.fidelity,
                                  benchmark=SimpleNamespace(objective_function=guard))
        candidate = {"answer": answer, "answer_perf": None, "eval_records": []}
        check = _score_result(candidate, {"evaluate_config": lambda payload: evaluate_hpobench_action(guarded, payload)}, None)
        result["nas101b_replays"].append({"job_id": job["id"], "context": context, "raw": fields,
                                         "unknown_keys": unknown, "score_check": check,
                                         "candidate": candidate, "backend_objective_calls": guard.call_count,
                                         "scope": "offline final input classification, not replayed trajectory or replacement score"})
    result["jobs"].append(row)
result["totals"] = {"jobs": len(result["jobs"]), "raw_files": sum(row["raw_files"] for row in result["jobs"]),
                    "transport_error_files": sum(len(row["transport_error_files"]) for row in result["jobs"]),
                    "nas101b_unknown_final_replays": len(result["nas101b_replays"]),
                    "nas101b_replays_fixed": sum(row["score_check"]["ok"] for row in result["nas101b_replays"])}
print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
