#!/usr/bin/env python3
"""Rescore all 1,170 adopted Whois sweep slots without model or tool calls.

Raw replay requires the separately retained trajectory archive and pyarrow.
``--check-public`` needs only this repository and the generated scalar CSVs.
Answers and raw model text are deliberately absent from the public output.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
MODELS = ("gpt", "kimi", "glm", "qwen", "deepseek", "gemini")
BETAS = (1, 5, 10, 15, 20)
MODEL_IDS = {"gpt": "gpt-5.6-sol", "kimi": "kimi-k3", "glm": "glm-5.3",
             "qwen": "qwen3.8-2.4t-a95b-fp8", "deepseek": "deepseek-v4-flash-0731",
             "gemini": "gemini-3.8-flash-medium"}
QUESTIONS = tuple((s, q) for s, n in (("phantom_seed2", 20), ("phantom_seed3", 19))
                  for q in range(n))


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def value_sha(value):
    return sha_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode())


def csv_read(path):
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))


def csv_write(path, rows, fields=None):
    if fields is None:
        fields = list(rows[0])
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def json_write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    sort_keys=True, allow_nan=False) + "\n")


def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-12)


def truth(value):
    return value is True or str(value).lower() == "true"


def relocated(path, workspace):
    """Resolve original local archive paths after moving the workspace."""
    path = Path(path)
    for name in ("gemini_openrouter_20260917", "deliveries", "whois_budget_20260916"):
        if name in path.parts:
            return workspace.joinpath(*path.parts[path.parts.index(name):])
    return path if path.is_absolute() else workspace / path


def source_rows(workspace, report):
    items = csv_read(report / "whois/inputs/items.csv")
    main = csv_read(report / "main/SOURCE_SELECTION.csv")
    selected_main = [r for r in main if r["system"] == "expgym" and r["scenario"] == "restricted_search"
                     and r["regime"] == "cost_moderate"]
    index = {(r["model"], r["item"]): r for r in selected_main}
    assert len(index) == len(selected_main) == 438
    adopted_rows = csv_read(report / "whois/adoption_sources.csv")
    adoption = {r["active_job_id"]: r for r in adopted_rows}
    assert len(adoption) == len(adopted_rows) == 156
    seen = set()
    sources = []
    for item in items:
        model, beta = item["model"], int(float(item["beta"]))
        ds, qi = item["data_source"], int(item["question_index"])
        key = model, beta, ds, qi
        assert key not in seen, key
        seen.add(key)
        overlap = ""
        expected = item["result_sha256"]
        if beta == 10:
            parent = index[(MODEL_IDS[model], f"{ds}:{qi}")]
            overlap = parent["slot_id"]
            path = workspace / "deliveries/paper-ad03e8c-20260916" / parent["historical_trajectory"]
            if expected:
                assert expected == parent["result_sha256"]
            expected = parent["result_sha256"]
        elif model == "gemini":
            adopted = adoption[item["job_id"]]
            path = relocated(adopted["result_path"], workspace)
            assert expected == adopted["result_sha256"]
        else:
            path = workspace / "whois_budget_20260916/raw" / item["result_collection"] / item["result_member"]
        assert item["repeat"] == "R1"
        assert truth(item["execution_complete"]) and truth(item["score_complete"])
        # Avoid machine-specific absolute paths in public metadata.
        local_path = path.relative_to(workspace).as_posix()
        sources.append((item, path, {
            "slot_id": f"whois:{model}:beta{beta}:{ds}:{qi}:R1",
            "model": model, "model_id": MODEL_IDS[model], "beta": beta,
            "item": f"{ds}:{qi}", "data_source": ds, "question_index": qi,
            "seed": 2200, "repeat": "R1", "system": "expgym",
            "scenario": "restricted_search", "strategy": "single",
            "main_overlap_slot_id": overlap,
            "count_as_additional_main_sample": not bool(overlap),
            "source_path": local_path, "source_sha256": expected,
            "source_collection": item["result_collection"],
            "original_execution_cohort": item["execution_cohort"],
            "original_source_tree_sha256": item["source_tree_sha256"],
        }))
    assert seen == {(m, b, s, q) for m in MODELS for b in BETAS for s, q in QUESTIONS}
    assert sum(bool(r[2]["main_overlap_slot_id"]) for r in sources) == 234
    return sources


def derive(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["model"], int(row["beta"])].append(row)
    aggregates = []
    for model in MODELS:
        for beta in BETAS:
            rr = grouped[model, beta]
            assert len(rr) == 39
            old = sum(float(r["old_score"]) for r in rr) / 39
            new = sum(float(r["new_score"]) for r in rr) / 39
            aggregates.append({
                "model": model, "beta": beta, "expected_items": 39,
                "old_score_known": 39, "new_score_known": 39,
                "old_mean_f1": old, "new_mean_f1": new,
                "delta_mean_f1": new - old,
                "answer_changed_items": sum(truth(r["answer_changed"]) for r in rr),
                "score_changed_items": sum(truth(r["score_changed"]) for r in rr),
                "old_missing_final_items": sum(truth(r["old_missing_final"]) for r in rr),
                "new_missing_final_items": sum(truth(r["new_missing_final"]) for r in rr),
                "main_overlap_items": sum(bool(r["main_overlap_slot_id"]) for r in rr),
                "provider_cohort": ("historical_sub2api" if beta == 10 else "openrouter")
                if model == "gemini" else "historical_original_provider",
            })
    by = {(r["model"], r["beta"]): r for r in aggregates}
    differences = []
    for model in MODELS:
        for beta in (1, 5, 10, 15):
            old = by[model, beta]["old_mean_f1"] - by[model, 20]["old_mean_f1"]
            new = by[model, beta]["new_mean_f1"] - by[model, 20]["new_mean_f1"]
            differences.append({
                "model": model, "target_beta": beta, "baseline_beta": 20,
                "direction": "target minus beta20", "paired_expected": 39,
                "old_mean_f1_difference": old, "new_mean_f1_difference": new,
                "delta_difference": new - old,
                "historical_cohort_comparison": beta == 10,
                "provider_cohort_change": model == "gemini" and beta == 10,
            })
    ranks = []
    for beta in BETAS:
        for model in MODELS:
            row = by[model, beta]
            ranks.append({
                "beta": beta, "model": model,
                "old_rank": 1 + sum(by[other, beta]["old_mean_f1"] > row["old_mean_f1"] + 1e-12
                                    for other in MODELS),
                "new_rank": 1 + sum(by[other, beta]["new_mean_f1"] > row["new_mean_f1"] + 1e-12
                                    for other in MODELS),
                "old_mean_f1": row["old_mean_f1"], "new_mean_f1": row["new_mean_f1"],
            })
    return aggregates, differences, ranks


def public_check(output):
    rows = csv_read(output / "agent_rows.csv")
    slots = csv_read(output / "slot_metrics.csv")
    sources = csv_read(output / "SOURCE_SELECTION.csv")
    assert len(rows) == len(slots) == len(sources) == 1170
    expected = {(m, b, f"{s}:{q}") for m in MODELS for b in BETAS for s, q in QUESTIONS}
    assert {(r["model"], int(r["beta"]), r["item"]) for r in rows} == expected
    assert len({r["slot_id"] for r in rows}) == 1170
    assert sum(bool(r["main_overlap_slot_id"]) for r in rows) == 234
    for agent, slot, source in zip(rows, slots, sources):
        assert agent["slot_id"] == slot["slot_id"] == source["slot_id"]
        assert agent["source_sha256"] == source["source_sha256"]
        assert len(agent["source_sha256"]) == 64
        assert all(0 <= float(agent[k]) <= 1 for k in ("old_score", "new_score"))
        assert truth(agent["score_changed"]) == (not close(agent["old_score"], agent["new_score"]))
        assert truth(agent["answer_changed"]) == (agent["old_answer_sha256"] != agent["new_answer_sha256"])
        for version in ("old", "new"):
            assert json.loads(slot[f"{version}_metrics_json"])["f1"] == float(agent[f"{version}_score"])
    aggregates, differences, ranks = derive(rows)
    for name, expected_rows in (("aggregate_metrics.csv", aggregates),
                                ("budget_differences.csv", differences),
                                ("rankings.csv", ranks)):
        encoded = [{k: str(v) for k, v in r.items()} for r in expected_rows]
        assert encoded == csv_read(output / name), name
    affected = csv_read(output / "affected_samples.csv")
    assert affected == [r for r in rows if truth(r["answer_changed"]) or truth(r["score_changed"])]
    check = json.loads((output / "CHECKS.json").read_text())
    for entry in check["output_files"]:
        assert sha_file(output / entry["path"]) == entry["sha256"], entry["path"]
    return {"passed": True, "slots": 1170, "additional_nonoverlap_slots": 936,
            "main_overlap_slots": 234, "aggregate_rows": 30, "budget_differences": 24,
            "ranking_rows": 30, "affected_answers": sum(truth(r["answer_changed"]) for r in rows),
            "affected_scores": sum(truth(r["score_changed"]) for r in rows),
            "raw_or_network_access": False}


def replay_inputs(inputs, output):
    """Re-execute parser and original Search scorer from minimal public input."""
    sys.path.insert(0, str(REPO))
    from expgym.tool_protocol import parse_final_answer
    from expgym.task_restricted_search import _name_f1
    public = public_check(output)
    checks = json.loads((output / "CHECKS.json").read_text())
    recorded_inputs = next(r for r in checks["output_files"] if r["path"] == "scoring_inputs.jsonl.gz")
    assert sha_file(inputs) == recorded_inputs["sha256"]
    assert all(sha_file(REPO / r["path"]) == r["sha256"] for r in checks["code_files"])
    expected = {r["slot_id"]: r for r in csv_read(output / "agent_rows.csv")}
    seen = set()
    runtime_responses = 0
    with gzip.open(inputs, "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            slot_id = record["slot_id"]
            assert slot_id not in seen and slot_id in expected
            seen.add(slot_id)
            row = expected[slot_id]
            assert record["source_sha256"] == row["source_sha256"]
            assert record["main_overlap_slot_id"] == row["main_overlap_slot_id"]
            text = record["terminal_text"]
            old = record["old_answer"]
            assert value_sha(old) == row["old_answer_sha256"]
            assert value_sha(text) == row["terminal_text_sha256"]
            assert close(record["old_metrics"]["f1"], row["old_score"])
            if record["terminal_finish_reason"] == "length":
                new, extraction = None, "terminal_rejected_completion_limit"
            elif record["terminal_has_tool_calls"]:
                new, extraction = None, "terminal_rejected_native_tool_call"
            elif old is None and not record["terminal_forced"]:
                new, extraction = None, "missing_final_without_forced_terminal_evidence"
            else:
                new = parse_final_answer(text.strip(), allow_unlabelled=True)
                extraction = "parse_final_answer_native_terminal"
            assert value_sha(new) == row["new_answer_sha256"], slot_id
            assert extraction == row["extraction_source"]
            assert close(_name_f1(old or "", record["gold_answers"]), row["old_score"]), slot_id
            assert close(_name_f1(new or "", record["gold_answers"]), row["new_score"]), slot_id
            n = sum(parse_final_answer(r["content"].strip(), allow_unlabelled=True) is not None
                    for r in record["nonterminal_eligible_responses"])
            assert n == int(row["runtime_counterfactual_responses"])
            runtime_responses += n
    assert len(seen) == 1170
    # This stage reads saved terminal text from the minimal public package;
    # the CSV-only stage's broader no-raw-access label does not apply here.
    public.pop("raw_or_network_access", None)
    return {**public, "saved_raw_terminal_inputs_reparsed": len(seen),
            "old_scores_recomputed": len(seen), "new_scores_recomputed": len(seen),
            "runtime_counterfactual_responses_replayed": runtime_responses,
            "minimal_inputs_sha256": sha_file(inputs), "private_trajectory_access": False,
            "network_access": False, "full_raw_trace_access": False,
            "minimal_public_terminal_text_access": True}


def rescore(args):
    workspace, report, output = args.workspace.resolve(), args.report.resolve(), args.output.resolve()
    sources = source_rows(workspace, report)
    tracked_code = ("tools/rescore_whois_protocol.py", "expgym/tool_protocol.py",
                    "expgym/task_restricted_search.py")
    code_files = [{"path": p, "sha256": sha_file(REPO / p)} for p in tracked_code]
    sys.path.insert(0, str(REPO))
    from expgym.tool_protocol import parse_final_answer
    from expgym import task_restricted_search as search
    output.mkdir(parents=True, exist_ok=True)
    assert not list(output.glob("*.csv")), "Use a fresh output directory; never overwrite a scored delivery"
    agents, slots, source_index, counterfactuals, minimal_inputs = [], [], [], [], []
    dataset_checks = {}
    question_rows = {}
    provenance = Counter()
    terminal_reasons = Counter()
    for item, path, source in sources:
        raw = path.read_bytes()
        assert sha_bytes(raw) == source["source_sha256"], str(path)
        trace = json.loads(raw)
        assert trace["schema"]["name"] == "expgym.trace"
        assert trace["task"]["scenario"] == "restricted_search"
        assert trace["run"]["protocol"]["tool_protocol"] == "native"
        assert trace["run"]["seed"] == source["seed"]
        assert trace["task"]["item"]["source"] == source["data_source"]
        assert int(trace["task"]["item"]["id"]) == source["question_index"]
        budget = trace["task"]["budget"]
        if "beta" in budget:
            assert close(budget["beta"], source["beta"])
        else:
            assert source["beta"] == 10 and budget["regime"] == "cost_moderate"
        assert close(budget["limit_seconds"], source["beta"] * 300)
        outcome = trace["outcome"]
        old_answer = outcome["answer"]
        old_score = search_score = float(outcome["score"]["value"])
        assert close(old_score, item["f1"])
        identity = trace["run"]["evaluation_identity"]["files"]["questions"]
        ds = source["data_source"]
        if ds not in dataset_checks:
            original = Path(identity["path"])
            dataset = original if original.is_file() else workspace / "LLM_ExpGym/data/phantom-wiki/blobs" / identity["sha256"]
            if not dataset.is_file():
                candidates = list((workspace / "LLM_ExpGym/data/phantom-wiki").glob("datasets--*/blobs/" + identity["sha256"]))
                assert len(candidates) == 1, f"Cannot locate dataset SHA {identity['sha256']}"
                dataset = candidates[0]
            assert sha_file(dataset) == identity["sha256"]
            import pyarrow.parquet as pq
            qa = pq.read_table(dataset, columns=["question", "answer", "type", "difficulty"]).to_pylist()
            qa = [r for r in qa if r["type"] in search.SWEET_SPOT_TYPES and len(r["answer"]) <= search.MAX_ANSWER_COUNT]
            qa.sort(key=lambda r: (r["type"], r["difficulty"]))
            question_rows[ds] = qa
            dataset_checks[ds] = {"sha256": identity["sha256"], "bytes": dataset.stat().st_size,
                                  "filtered_questions": len(qa), "source_identity_verified": True}
        assert dataset_checks[ds]["sha256"] == identity["sha256"]
        gold = question_rows[ds][source["question_index"]]["answer"]
        search_score = search._name_f1(old_answer or "", gold)
        assert close(search_score, old_score), (source["slot_id"], search_score, old_score)
        answer_id = outcome["answer_message_id"]
        messages = [m for m in trace["messages"] if m["id"] == answer_id]
        calls = [c for c in trace["llm_calls"] if c["output_message_id"] == answer_id]
        assert len(messages) == len(calls) == 1
        message, call = messages[0], calls[0]
        assert message["role"] == "assistant"
        assert next(m for m in reversed(trace["messages"]) if m["role"] == "assistant")["id"] == answer_id
        text = message.get("content") or ""
        assert isinstance(text, str)
        assert (call["output_message"].get("content") or "") == text
        # Only this recorded terminal response is eligible. A rejected length
        # completion or attempted tool call never becomes an offline answer.
        if call.get("finish_reason") == "length":
            new_answer, extraction = None, "terminal_rejected_completion_limit"
        elif message.get("tool_calls") or call["output_message"].get("tool_calls"):
            new_answer, extraction = None, "terminal_rejected_native_tool_call"
        elif old_answer is None and not call["forced"]:
            new_answer, extraction = None, "missing_final_without_forced_terminal_evidence"
        else:
            new_answer = parse_final_answer(text.strip(), allow_unlabelled=True)
            extraction = "parse_final_answer_native_terminal"
        new_score = search._name_f1(new_answer or "", gold)
        runtime_count = 0
        intermediate_inputs = []
        for call_index, intermediate in enumerate(trace["llm_calls"]):
            if intermediate["output_message_id"] == answer_id:
                continue
            candidate = intermediate.get("output_message") or {}
            if candidate.get("tool_calls") or intermediate.get("finish_reason") == "length":
                continue
            content = candidate.get("content") or ""
            assert isinstance(content, str)
            later_message_ids = {c["output_message_id"] for c in trace["llm_calls"][call_index + 1:]}
            later_tools = sum(t["request_message_id"] in later_message_ids for t in trace["tool_calls"])
            intermediate_inputs.append({"message_id": intermediate["output_message_id"],
                                        "llm_call_id": intermediate["id"], "content": content,
                                        "subsequent_llm_calls": len(trace["llm_calls"]) - call_index - 1,
                                        "subsequent_tool_calls": later_tools})
            parsed = parse_final_answer(content.strip(), allow_unlabelled=True)
            if parsed is not None:
                # Observed history continued past this response. A newly
                # accepted nonterminal final would have stopped the agent.
                runtime_count += 1
                counterfactuals.append({
                    "slot_id": source["slot_id"], "model": source["model"], "beta": source["beta"],
                    "item": source["item"], "source_sha256": source["source_sha256"],
                    "message_id": intermediate["output_message_id"], "llm_call_id": intermediate["id"],
                    "raw_content_sha256": value_sha(content), "parsed_answer_sha256": value_sha(parsed),
                    "subsequent_llm_calls": len(trace["llm_calls"]) - call_index - 1,
                    "subsequent_tool_calls": later_tools,
                    "matches_recorded_terminal_answer": parsed == new_answer,
                    "reason": "new_parser_accepts_recorded_nonterminal_response",
                    "adopted_as_terminal": False,
                })
        changed = old_answer != new_answer
        score_changed = not close(old_score, new_score)
        if not changed:
            reason = "unchanged_recomputed_from_terminal_response"
        elif old_answer is None:
            reason = "terminal_answer_recovered_by_repaired_parser"
        elif new_answer is None:
            reason = "terminal_response_rejected_by_repaired_protocol"
        elif old_answer == text.strip():
            reason = "explicit_final_directive_recovered_from_raw_response"
        elif isinstance(old_answer, str) and old_answer.startswith(("**", "__")):
            reason = "closing_label_markup_removed_from_payload"
        else:
            reason = "answer_boundary_or_label_wrapper_corrected"
        source.update(source_bytes=len(raw), source_schema_version=trace["schema"]["version"],
                      source_repository_commit=trace["provenance"]["repository"]["commit"],
                      source_repository_tree_sha256=trace["provenance"]["repository"]["source_tree_sha256"],
                      evaluation_questions_sha256=identity["sha256"])
        provenance[source["source_repository_commit"] or "unrecorded"] += 1
        terminal_reasons[outcome["termination_reason"]] += 1
        row = {**source, "agent_id": 0, "terminal_message_id": answer_id,
               "terminal_llm_call_id": call["id"], "terminal_text_sha256": value_sha(text),
               "terminal_forced": call["forced"], "terminal_finish_reason": call.get("finish_reason"),
               "extraction_source": extraction, "old_answer_source": outcome.get("answer_source"),
               "termination_reason": outcome["termination_reason"],
               "old_missing_final": old_answer is None, "new_missing_final": new_answer is None,
               "old_answer_sha256": value_sha(old_answer), "new_answer_sha256": value_sha(new_answer),
               "old_score": old_score, "old_score_recomputed": search_score,
               "new_score": new_score, "delta_score": new_score - old_score,
               "execution_complete": True, "old_score_complete": True, "new_score_complete": True,
               "old_metrics_json": json.dumps({"f1": old_score}, sort_keys=True),
               "new_metrics_json": json.dumps({"f1": new_score}, sort_keys=True),
               "answer_changed": changed, "score_changed": score_changed,
               "runtime_counterfactual_changed": runtime_count > 0,
               "runtime_counterfactual_responses": runtime_count,
               "reason": reason, "new_scoring_status": "formal_protocol_repair_v1",
               "old_scoring_status": "historical_adopted"}
        agents.append(row)
        slots.append({k: row[k] for k in ("slot_id", "model", "model_id", "beta", "item", "seed",
                                         "main_overlap_slot_id", "source_path", "source_sha256",
                                         "old_metrics_json", "new_metrics_json", "old_score", "new_score",
                                         "delta_score", "answer_changed", "score_changed", "reason",
                                         "old_scoring_status", "new_scoring_status")})
        source_index.append(source)
        minimal_inputs.append({
            "schema": "expgym.whois-minimal-scoring-input.v1",
            "slot_id": source["slot_id"], "model": source["model"], "beta": source["beta"],
            "item": source["item"], "seed": source["seed"],
            "main_overlap_slot_id": source["main_overlap_slot_id"],
            "source_sha256": source["source_sha256"],
            "task_questions_sha256": identity["sha256"], "gold_answers": gold,
            "terminal_message_id": answer_id, "terminal_llm_call_id": call["id"],
            "terminal_text": text, "terminal_finish_reason": call.get("finish_reason"),
            "terminal_forced": call["forced"],
            "terminal_has_tool_calls": bool(message.get("tool_calls") or call["output_message"].get("tool_calls")),
            "old_answer": old_answer, "old_metrics": {"f1": old_score},
            "old_answer_source": outcome.get("answer_source"),
            "nonterminal_eligible_responses": intermediate_inputs,
        })
    aggregate, differences, ranks = derive(agents)
    published_aggregates = {(r["model"], int(r["beta"])): r
                            for r in csv_read(report / "whois/aggregate_metrics.csv")}
    published_differences = {(r["model"], int(r["target_beta"])): r
                             for r in csv_read(report / "whois/budget_differences.csv")}
    assert len(published_aggregates) == 30 and len(published_differences) == 24
    assert all(close(r["old_mean_f1"], published_aggregates[r["model"], r["beta"]]["mean_f1"])
               for r in aggregate)
    assert all(close(r["old_mean_f1_difference"],
                     published_differences[r["model"], r["target_beta"]]["mean_f1_difference"])
               for r in differences)
    for name, rows in (("agent_rows.csv", agents), ("slot_metrics.csv", slots),
                       ("SOURCE_SELECTION.csv", source_index), ("aggregate_metrics.csv", aggregate),
                       ("budget_differences.csv", differences), ("rankings.csv", ranks)):
        csv_write(output / name, rows)
    csv_write(output / "affected_samples.csv",
              [r for r in agents if r["answer_changed"] or r["score_changed"]], list(agents[0]))
    csv_write(output / "runtime_counterfactual.csv", counterfactuals,
              ["slot_id", "model", "beta", "item", "source_sha256", "message_id", "llm_call_id",
               "raw_content_sha256", "parsed_answer_sha256", "subsequent_llm_calls", "subsequent_tool_calls",
               "matches_recorded_terminal_answer", "reason", "adopted_as_terminal"])
    payload = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
                      for r in minimal_inputs).encode()
    (output / "scoring_inputs.jsonl.gz").write_bytes(gzip.compress(payload, mtime=0))
    checks = {
        "schema": "expgym.whois-protocol-rescore.v1", "passed": True,
        "slots": 1170, "sources_hash_verified": 1170, "historical_scores_recomputed": 1170,
        "historical_aggregate_rows_verified": 30, "historical_budget_differences_verified": 24,
        "additional_nonoverlap_slots": 936, "main_overlap_slots": 234,
        "affected_answers": sum(r["answer_changed"] for r in agents),
        "affected_scores": sum(r["score_changed"] for r in agents),
        "runtime_counterfactual_slots": sum(r["runtime_counterfactual_changed"] for r in agents),
        "runtime_counterfactual_responses": len(counterfactuals),
        "changes_by_model": {m: {"answers": sum(r["answer_changed"] for r in agents if r["model"] == m),
                                  "scores": sum(r["score_changed"] for r in agents if r["model"] == m)}
                             for m in MODELS},
        "all_original_trajectory_files_unchanged": True, "model_calls": 0, "tool_calls": 0,
        "new_scoring_status": "formal_protocol_repair_v1", "old_scoring_status": "historical_adopted",
        "score_unit": "name-level F1 in [0,1]", "diagnostic_scores_adopted": False,
        "terminal_selection_policy": "Only recorded outcome.answer_message_id; native tool calls and length rejected; no earlier-message search or answer completion.",
        "deduplication": "All 234 beta10 positions reuse main-report N1 Moderate slots; count 936 other positions as additional independent sweep slots.",
        "datasets": dataset_checks,
        "runtime_source_commits": dict(sorted(provenance.items())),
        "termination_reasons": dict(sorted(terminal_reasons.items())),
        "code_base_commit": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "code_files": code_files,
        "input_files": [{"path": p, "sha256": sha_file(report / p)} for p in (
            "whois/inputs/items.csv", "whois/adoption_sources.csv", "main/SOURCE_SELECTION.csv",
            "whois/aggregate_metrics.csv", "whois/budget_differences.csv")],
        "output_files": [{"path": p.name, "sha256": sha_file(p)} for p in
                         sorted(list(output.glob("*.csv")) + [output / "scoring_inputs.jsonl.gz"])],
    }
    # Code may be under simultaneous review; fail if parser changed mid-run.
    end_code_files = [{"path": p, "sha256": sha_file(REPO / p)} for p in tracked_code]
    assert code_files == end_code_files, "Scoring code changed during replay; regenerate with frozen code"
    checks["code_files_at_completion"] = end_code_files
    checks["code_hash_stable_during_replay"] = True
    json_write(output / "CHECKS.json", checks)
    result = public_check(output)
    json_write(output / "PUBLIC_REPLAY_CHECK.json", result)
    json_write(output / "SCORE_REPLAY_CHECK.json", replay_inputs(output / "scoring_inputs.jsonl.gz", output))
    print(json.dumps(result, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=REPO.parent)
    parser.add_argument("--report", type=Path, default=REPO / "results/gemini-openrouter-20260917")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-public", action="store_true")
    parser.add_argument("--inputs", type=Path,
                        help="Reparse and re-score the minimal public JSONL gzip; requires no private trajectories or pyarrow")
    args = parser.parse_args()
    if args.inputs:
        print(json.dumps(replay_inputs(args.inputs, args.output), sort_keys=True))
    elif args.check_public:
        print(json.dumps(public_check(args.output), sort_keys=True))
    else:
        rescore(args)


if __name__ == "__main__":
    main()
