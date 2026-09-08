#!/usr/bin/env python3
"""Independent stdlib-only Audit scoring from gold and raw final answers.

No repository evaluator, aggregator, summarizer, model, or feedback is imported/called.
Prints JSON to stdout or creates a new --output file exclusively; never writes inputs or existing reports. Before every Audit
receipt/artifact is complete it emits complete=false, metrics=null, exit status 2.
"""
import argparse
import collections
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "kimi_k3_eval"
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STRATEGIES = ("naive", "cached", "poolact")
EXPECTED = {"jobs": 78, "expgym_traces": 117, "poolact_results": 117, "poolact_agent_traces": 468}
EXPECTED_SOURCE_TREE = "c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e"


def read(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def ref(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equal_number(actual, expected, context):
    if expected is None:
        require(actual is None, context + ": expected null")
    else:
        require(isinstance(actual, (float, int)) and not isinstance(actual, bool) and math.isfinite(actual)
                and math.isclose(actual, expected, rel_tol=0, abs_tol=1e-10),
                context + ": %r != %r" % (actual, expected))


def parse_final_for_score(answer):
    """Match evaluator cleanup only, not PoolAct's stricter voting parser."""
    require(isinstance(answer, str), "final answer must be the recorded string")
    try:
        data = json.loads(answer)
        parse_mode = "direct_json"
    except json.JSONDecodeError:
        cleaned = answer.strip().rstrip(";").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            data = json.loads(cleaned)
            parse_mode = "cleanup_json"
        except json.JSONDecodeError:
            return {}, "invalid_json"
    return (data, parse_mode) if isinstance(data, dict) else ({}, "non_object_json")


def exact_evidence(value):
    # Deliberately whole-conversion fallback, matching the frozen evaluator.
    try:
        return set(int(item) for item in value), False
    except Exception:
        return set(), True


def diagnostic_value(value):
    """Encode permissive inner-JSON NaN/Inf only for strict report serialization.

    Scoring always uses the original value. Raw answer text remains in its hashed
    source file; this explicit marker is diagnostic representation, not a repair.
    """
    if isinstance(value, float) and not math.isfinite(value):
        return {"$python_json_nonfinite": str(value)}
    if isinstance(value, list):
        return [diagnostic_value(item) for item in value]
    if isinstance(value, dict):
        return {key: diagnostic_value(item) for key, item in value.items()}
    return value


def score_answer(answer, gold, tool_records=()):
    parsed, parse_mode = parse_final_for_score(answer)
    verified = collections.defaultdict(list)
    # The native evaluator exits before tool parsing for invalid/non-object JSON.
    for tool_name, argument, _ in (tool_records if parse_mode in ("direct_json", "cleanup_json") else ()):
        if tool_name != "human_feedback":
            continue
        try:
            payload = json.loads(argument)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            payload = payload[0]
        if not isinstance(payload, dict) or not isinstance(payload.get("nda_id"), str) or not isinstance(payload.get("evidence_ids"), list):
            continue
        evidence, conversion_failed = exact_evidence(payload["evidence_ids"])
        if not conversion_failed:
            verified[payload["nda_id"]].append(evidence)
    hypotheses = []
    for hypothesis_id, annotation in gold.items():
        entry = parsed.get(hypothesis_id)
        present = isinstance(entry, dict)
        evidence, conversion_failed = exact_evidence(entry.get("evidence_ids", [])) if present else (set(), False)
        gold_evidence = set(int(value) for value in annotation.get("spans", []))
        label_correct = present and entry.get("label") == annotation["choice"]
        # Missing whole hypothesis gets 0, unlike a present {} with default [].
        evidence_correct = present and evidence == gold_evidence
        fully_correct = label_correct and evidence_correct
        verified_correct = fully_correct and any(evidence == submission for submission in verified.get(hypothesis_id, []))
        hypotheses.append({"hypothesis_id": hypothesis_id, "entry_present_object": present,
                           "predicted_label": diagnostic_value(entry.get("label")) if present else None,
                           "predicted_evidence_raw": diagnostic_value(entry.get("evidence_ids", [])) if present else None,
                           "normalized_evidence_ids": sorted(evidence), "evidence_conversion_failed": conversion_failed,
                           "label_correct": label_correct, "evidence_correct": evidence_correct,
                           "fully_correct": fully_correct, "verified_correct": verified_correct})
    total = len(gold)
    labels = sum(row["label_correct"] for row in hypotheses)
    evidence = sum(row["evidence_correct"] for row in hypotheses)
    full = sum(row["fully_correct"] for row in hypotheses)
    verified_count = sum(row["verified_correct"] for row in hypotheses)
    return {"parse_mode": parse_mode, "label_acc": labels / total if total else 0.0,
            "evidence_acc": evidence / total if total else 0.0,
            "verification_eff": verified_count / full if full else None,
            "label_correct": labels, "evidence_correct": evidence, "fully_correct": full,
            "verified_correct": verified_count, "denominator": total, "hypotheses": hypotheses}


def canonical_vote_label(value):
    token = re.sub(r"[^a-z]", "", str(value or "").lower())
    return {"entailment": "Entailment", "entailed": "Entailment", "contradiction": "Contradiction",
            "contradicted": "Contradiction", "notmentioned": "NotMentioned", "neutral": "NotMentioned"}.get(token, str(value or "").strip())


def canonical_vote_evidence(value):
    if not isinstance(value, list):
        return ()
    normalized = set()
    for item in value:
        try:
            normalized.add(int(item))
        except (TypeError, ValueError):
            normalized.add(str(item))
    return tuple(sorted(normalized, key=lambda item: (str(type(item)), str(item))))


def first_plurality(values):
    counts = collections.Counter(values)
    maximum = max(counts.values())
    tied = [value for value in counts if counts[value] == maximum]
    return tied[0], len(tied) > 1


def vote_answers(answers):
    parsed = []
    for answer in answers:
        try:
            value = json.loads(answer) if isinstance(answer, str) else answer
        except (json.JSONDecodeError, TypeError):
            value = {}
        parsed.append(value if isinstance(value, dict) else {})
    voted, diagnostics = {}, []
    for hypothesis_id in sorted({key for value in parsed for key in value}):
        entries = [(index, value[hypothesis_id]) for index, value in enumerate(parsed)
                   if isinstance(value.get(hypothesis_id), dict)]
        if not entries:
            continue
        labels = [canonical_vote_label(entry.get("label")) for _, entry in entries]
        label, label_tie = first_plurality(labels)
        supporters = [(index, entry) for (index, entry), vote in zip(entries, labels) if vote == label]
        evidence_values = [canonical_vote_evidence(entry.get("evidence_ids")) for _, entry in supporters]
        evidence, evidence_tie = first_plurality(evidence_values)
        voted[hypothesis_id] = {"label": label, "evidence_ids": list(evidence)}
        diagnostics.append({"hypothesis_id": hypothesis_id, "voting_agent_indices": [index for index, _ in entries],
                            "labels_in_agent_order": labels, "winning_label": label, "label_tie": label_tie,
                            "winning_label_agent_indices": [index for index, _ in supporters],
                            "evidence_in_supporter_order": [list(value) for value in evidence_values],
                            "winning_evidence_ids": list(evidence), "evidence_tie": evidence_tie})
    return json.dumps(voted, sort_keys=True), diagnostics


def extract_final(trace):
    outcome = trace["outcome"]
    if outcome.get("answer_override") is not None:
        return outcome["answer_override"], "outcome.answer_override"
    message_id = outcome["answer_message_id"]
    messages = {message["id"]: message for message in trace["messages"]}
    require(len(messages) == len(trace["messages"]), "duplicate message IDs")
    message = messages[message_id]
    require(message["role"] == "assistant", "final referenced message is not assistant")
    if "content" in message:
        content = str(message["content"])
    else:
        tools = {tool["id"]: tool for tool in trace["tool_calls"]}
        content = str(tools[message["content_ref"]["tool_call_id"]]["observation"])
    lines = content.splitlines()
    for index, line in enumerate(lines):
        clean = line.strip()
        while clean and clean[0] in "*_ -":
            clean = clean[1:].lstrip()
        if clean.startswith("Answer:"):
            first = clean.split("Answer:", 1)[1].strip()
            tail = "\n".join(lines[index + 1:]).strip()
            answer = first + "\n" + tail if first and tail else first or tail
            return answer or content, "messages.%s:first_normalized_line_start_Answer" % message_id
    return content, "messages.%s:whole_content" % message_id


def trace_tools(trace):
    rows = []
    for tool in trace["tool_calls"]:
        argument = tool["arguments"]
        if isinstance(argument, dict) and set(argument) == {"raw", "encoding"} and argument["encoding"] == "text":
            argument = argument["raw"]
        else:
            argument = json.dumps(argument, ensure_ascii=False)
        rows.append((tool["name"], argument, None))
    return rows


def check_metrics(stored, scored, context):
    require(isinstance(stored, dict), context + ": missing recorded metric dict")
    for key in ("label_acc", "evidence_acc", "verification_eff"):
        equal_number(stored.get(key), scored[key], context + "." + key)


def readiness(manifest):
    jobs = [job for job in manifest["jobs"] if job["scenario"] == "evidence_audit"]
    expected_slots = {(system, index, regime, slot) for system in ("expgym", "poolact") for index in range(13)
                      for regime in REGIMES for slot in (range(3) if system == "expgym" else STRATEGIES)}
    slots, counts, pending, missing, issues, receipts = [], collections.Counter(jobs=len(jobs)), [], [], [], []
    for job in jobs:
        try:
            status = read(job["status_path"])
            receipts.append({"job_id": job["id"], **ref(job["status_path"]), "status": status.get("status"),
                             "returncode": status.get("returncode")})
            if status.get("status") != "completed" or status.get("returncode") != 0 or status.get("missing_outputs"):
                pending.append({"job_id": job["id"], "status": status.get("status"), "returncode": status.get("returncode")})
        except (OSError, ValueError) as error:
            pending.append({"job_id": job["id"], "status": "missing_or_unreadable_receipt", "error": str(error)})
        for output in job["expected_outputs"]:
            slots.append((job["system"], int(job["item_id"]), job["cost_regime"], output.get("rep", output.get("strategy"))))
            counts["expgym_traces" if job["system"] == "expgym" else "poolact_results"] += 1
            paths = [output["path"]]
            if job["system"] == "poolact":
                agents = output.get("agent_paths", [])
                counts["poolact_agent_traces"] += len(agents)
                if len(agents) != 4 or job["agents"] != 4:
                    issues.append("expected four agents: " + job["id"])
                paths.extend(agents)
            missing.extend({"job_id": job["id"], "path": path} for path in paths if not Path(path).is_file())
        if job.get("summary_path") and not Path(job["summary_path"]).is_file():
            missing.append({"job_id": job["id"], "path": job["summary_path"]})
    if set(slots) != expected_slots or len(slots) != len(expected_slots) or dict(counts) != EXPECTED:
        issues.append("Audit manifest partition is not the exact 13 docs x three regimes x required repeats/strategies")
    return jobs, {"complete": not pending and not missing and not issues, "expected_counts": EXPECTED,
                  "manifest_counts": dict(counts), "pending_or_failed_jobs": pending, "missing_paths": missing,
                  "issues": issues, "receipts": receipts}


def build_metrics(traces, results):
    documents, aggregate = [], []
    for regime in REGIMES:
        for system in ("expgym", "poolact"):
            for strategy in ((None,) if system == "expgym" else STRATEGIES):
                metrics = ("LA_pct", "EA_pct") if system == "expgym" else ("LA_pct", "EA_pct", "MI_LA_pct", "MI_EA_pct")
                for index in range(13):
                    rows = [row for row in (traces if system == "expgym" else results) if row["system"] == system
                            and row["item_index"] == index and row["regime"] == regime and row["strategy"] == strategy]
                    require(len(rows) == (3 if system == "expgym" else 1), "incomplete document metric")
                    for metric in metrics:
                        raw_key = {"LA_pct": "label_acc", "EA_pct": "evidence_acc",
                                   "MI_LA_pct": "mean_individual_label_acc", "MI_EA_pct": "mean_individual_evidence_acc"}[metric]
                        value = statistics.mean(row[raw_key] * 100 for row in rows)
                        documents.append({"system": system, "item_index": index, "regime": regime, "strategy": strategy,
                                          "metric": metric, "value": value, "paths": [row["path"] for row in rows]})
                for metric in metrics:
                    rows = [row for row in documents if row["system"] == system and row["regime"] == regime
                            and row["strategy"] == strategy and row["metric"] == metric]
                    require(len(rows) == 13, "incomplete macro metric")
                    aggregate.append({"system": system, "regime": regime, "strategy": strategy, "metric": metric,
                                      "value": statistics.mean(row["value"] for row in rows), "documents": 13})
    return {"document_metrics": documents, "aggregate_metrics": aggregate}


def compare_summary(report, summary_path):
    summary = read(summary_path)
    require(summary["complete"] is True and summary["manifest_sha256"] == report["manifest"]["sha256"], "summary incomplete or manifest mismatch")
    comparisons = {"aggregate": [], "document": [], "agent": [], "poolact_result": [], "paper_subset": []}
    for kind, local_key, official_key in (("aggregate", "aggregate_metrics", "aggregate_metrics"), ("document", "document_metrics", "task_metrics")):
        for row in report["metrics"][local_key]:
            matches = [value for value in summary[official_key] if value["subset"] == "full" and value["scenario"] == "evidence_audit"
                       and value["system"] == row["system"] and value["cost_regime"] == row["regime"]
                       and value.get("strategy") == row["strategy"] and value["metric"] == row["metric"]
                       and (kind != "document" or value["item_id"] == str(row["item_index"]))]
            require(len(matches) == 1 and matches[0]["complete"] is True, "missing/duplicate/incomplete summary metric")
            equal_number(matches[0]["value"], row["value"], "summary " + kind)
            comparisons[kind].append({**row, "official_value": matches[0]["value"], "difference": matches[0]["value"] - row["value"]})
    for kind, local_key, official_key in (("agent", "traces", "agents"), ("poolact_result", "poolact_results", "artifacts")):
        official = {value["path"]: value for value in summary[official_key]}
        require(len(official) == len(summary[official_key]), "duplicate summary paths")
        for row in report[local_key]:
            match = official[row["path"]]
            require(match["sha256"] == row["sha256"] and match["status"] == "valid", "summary raw integrity mismatch")
            equal_number(match["label_acc"], row["label_acc"], "summary LA")
            equal_number(match["evidence_acc"], row["evidence_acc"], "summary EA")
            comparisons[kind].append({"path": row["path"], "sha256": row["sha256"], "LA_difference": match["label_acc"] - row["label_acc"],
                                      "EA_difference": match["evidence_acc"] - row["evidence_acc"]})
    for row in report["metrics"]["aggregate_metrics"]:
        if row["system"] != "poolact" or row["regime"] == "cost_free":
            continue
        matches = [value for value in summary["aggregate_metrics"] if value["subset"] == "paper_poolact" and value["scenario"] == "evidence_audit"
                   and value["system"] == "poolact" and value["cost_regime"] == row["regime"] and value.get("strategy") == row["strategy"]
                   and value["metric"] == row["metric"]]
        require(len(matches) == 1 and matches[0]["complete"] is True, "missing paper Audit metric")
        equal_number(matches[0]["value"], row["value"], "paper Audit metric")
        comparisons["paper_subset"].append({**row, "official_value": matches[0]["value"], "difference": matches[0]["value"] - row["value"]})
    require({key: len(value) for key, value in comparisons.items()} == {"aggregate": 42, "document": 546, "agent": 585, "poolact_result": 117, "paper_subset": 24}, "comparison count mismatch")
    return {**ref(summary_path), "complete": True, "counts": {key: len(value) for key, value in comparisons.items()}, "comparisons": comparisons}


def run(manifest_path, summary_path=None, ready_only=False):
    manifest = read(manifest_path)
    require(manifest["source_tree_sha256"] == EXPECTED_SOURCE_TREE, "this independent implementation is pinned to full_v3 evaluator semantics; re-review a changed source")
    jobs, ready = readiness(manifest)
    report = {"schema": {"name": "kimi.audit.independent_raw_review", "version": 1},
              "created_at": datetime.now(timezone.utc).isoformat(), "complete": False,
              "classification": "read-only Audit partition independent gold scoring; not a new model run or claim of full-study acceptance",
              "source_tree_sha256": manifest["source_tree_sha256"], "manifest": ref(manifest_path), "script": ref(__file__),
              "readiness": ready, "metrics": None, "summary_comparison": None, "issues": []}
    if ready_only or not ready["complete"]:
        report["readiness_only"] = ready_only
        return report
    dataset_ref = manifest["data_provenance"]["dataset_manifest"]
    require(ref(dataset_ref["path"])["sha256"] == dataset_ref["sha256"], "dataset manifest hash mismatch")
    dataset = read(dataset_ref["path"])
    gold_path = Path(manifest["repo_root"]) / "data/contract-nli/test_segments.json"
    gold_ref = ref(gold_path)
    declaration, = [value for value in dataset["files"] if value["path"] == "data/contract-nli/test_segments.json"]
    require(gold_ref["sha256"] == declaration["sha256"] and gold_ref["bytes"] == declaration["bytes"], "gold hash mismatch")
    data = read(gold_path)
    ids = list(data["labels"])
    require(len(ids) == 17 and dataset["audit"]["selected_count"] == 13, "gold selection mismatch")
    gold_documents = []
    for index in range(13):
        doc = data["documents"][index]
        gold = {key: value for key, value in doc["annotation_sets"][0]["annotations"].items() if key in ids}
        selection = dataset["audit"]["items"][index]
        require(len(gold) == 17 and selection["index"] == index and selection["doc_id"] == int(doc["id"]), "selected document mismatch")
        gold_documents.append({"item_index": index, "doc_id": int(doc["id"]), "file_name": doc["file_name"],
                               "json_pointer": "/documents/%d/annotation_sets/0/annotations" % index, "gold": gold})
    report["gold"] = {**gold_ref, "dataset_manifest": dataset_ref, "hypothesis_ids": ids, "documents": gold_documents}
    report["semantic_source_files"] = [ref(Path(manifest["repo_root"]) / path) for path in
                                       ("expgym/task_evidence_audit.py", "expgym/poolact.py", "expgym/react_loop.py", "expgym/trace_v2.py")]
    traces, results = [], []
    for job in jobs:
        for output in job["expected_outputs"]:
            try:
                raw = read(output["path"])
                common = {"job_id": job["id"], "system": job["system"], "item_index": int(job["item_id"]),
                          "regime": job["cost_regime"], "strategy": output.get("strategy")}
                gold = gold_documents[common["item_index"]]["gold"]
                if job["system"] == "expgym":
                    require(raw["provenance"]["repository"]["source_tree_sha256"] == manifest["source_tree_sha256"], "source mismatch")
                    require(raw["run"]["model"]["id"] == manifest["settings"]["model"], "model mismatch")
                    require(raw["task"]["scenario"] == "evidence_audit" and raw["task"]["item"] == {"kind": "document", "id": common["item_index"], "split": "cc-large"}, "item mismatch")
                    require(raw["task"]["budget"]["regime"] == common["regime"] and raw["task"]["rep"] == output["rep"], "regime/rep mismatch")
                    require(raw["task"]["hypothesis_order"] == output["hypothesis_order"] and set(output["hypothesis_order"]) == set(ids), "order mismatch")
                    require(raw["task"]["dataset"]["revision"]["test_segments_sha256"] == gold_ref["sha256"], "trace gold mismatch")
                    require(raw["outcome"]["validation"]["passed"] is True, "trace validation failed")
                    answer, location = extract_final(raw)
                    scored = score_answer(answer, gold, trace_tools(raw))
                    check_metrics(raw["outcome"]["score"].get("metrics"), scored, "trace stored")
                    traces.append({**common, **ref(output["path"]), "rep": output["rep"], "agent_id": None,
                                   "answer_location": location, "answer_source": raw["outcome"].get("answer_source"),
                                   "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(), **scored})
                else:
                    require(raw["implementation_sha256"]["source_tree"] == manifest["source_tree_sha256"], "source mismatch")
                    require(raw["config"]["model"] == manifest["settings"]["model"] and raw["config"]["scenario"] == "evidence_audit"
                            and raw["config"]["cc_split"] == "cc-large" and raw["config"]["question_index"] == common["item_index"]
                            and raw["config"]["cost_regime"] == common["regime"], "PoolAct config mismatch")
                    require(raw["strategy"] == output["strategy"] and raw["agents"] == 4 and len(raw["agent_results"]) == 4, "strategy/agents mismatch")
                    if output["strategy"] == "poolact":
                        require(raw["shared_state"]["graph"]["pending_claims"] == 0, "pending graph claims")
                    agents, answers, perfs = [], [], []
                    for index, path in enumerate(output["agent_paths"]):
                        agent = read(path)
                        require(agent == raw["agent_results"][index] and agent["agent_id"] == index and agent["strategy"] == output["strategy"], "per-agent/embedded mismatch")
                        require(agent["score_check"]["ok"] is True, "agent score_check failed")
                        answer = agent["answer"]
                        scored = score_answer(answer, gold, agent["tool_records"])
                        check_metrics(agent.get("answer_metrics"), scored, "agent stored")
                        check_metrics(agent["score_check"].get("recomputed_metrics"), scored, "agent score_check")
                        equal_number(agent["answer_perf"], scored["label_acc"], "agent primary")
                        agents.append({**common, **ref(path), "rep": None, "agent_id": index, "answer_location": "answer",
                                       "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(), **scored})
                        answers.append(answer)
                        perfs.append(agent["answer_perf"])
                    voted, voting = vote_answers(answers)
                    aggregate = raw["aggregate"]
                    require(aggregate["method"] == "per_hypothesis_majority_vote" and aggregate["answer"] == voted, "voted answer mismatch")
                    require(aggregate["individual_answers"] == answers and aggregate["individual_perfs"] == perfs, "aggregate individual mismatch")
                    scored = score_answer(voted, gold, [])
                    check_metrics(aggregate.get("answer_metrics"), scored, "aggregate stored")
                    equal_number(aggregate["answer_perf"], scored["label_acc"], "aggregate primary")
                    results.append({**common, **ref(output["path"]), "voted_answer": voted, "voting": voting, **scored,
                                    "agent_paths": output["agent_paths"],
                                    "mean_individual_label_acc": statistics.mean(row["label_acc"] for row in agents),
                                    "mean_individual_evidence_acc": statistics.mean(row["evidence_acc"] for row in agents)})
                    traces.extend(agents)
            except Exception as error:
                report["issues"].append({"job_id": job["id"], "path": output["path"], "error_type": type(error).__name__, "error": str(error)})
    report["traces"], report["poolact_results"] = traces, results
    report["valid_counts"] = {"expgym_traces": sum(row["system"] == "expgym" for row in traces),
                              "poolact_results": len(results), "poolact_agent_traces": sum(row["system"] == "poolact" for row in traces)}
    require(len({row["path"] for row in traces}) == len(traces), "duplicate raw paths")
    if report["issues"] or report["valid_counts"] != {key: EXPECTED[key] for key in ("expgym_traces", "poolact_results", "poolact_agent_traces")}:
        return report
    report["metrics"] = build_metrics(traces, results)
    report["complete"] = True
    if summary_path:
        report["summary_comparison"] = compare_summary(report, summary_path)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=STUDY / "runs/full_v3/manifest.json")
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--ready-only", action="store_true", help="Read only manifest/receipts/file existence, not model results")
    parser.add_argument("--output", type=Path, help="Create this new generated JSON evidence file exclusively; existing paths are never overwritten")
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("--output already exists; choose a new evidence filename")
    report = run(args.manifest, args.summary, args.ready_only)
    encoded = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2)
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
        print(json.dumps({"complete": report["complete"], "readiness_complete": report["readiness"]["complete"],
                          "valid_counts": report.get("valid_counts"), "issues": report["issues"], "output": ref(args.output)}, ensure_ascii=False))
    else:
        print(encoded)
    return 0 if report["complete"] or (args.ready_only and report["readiness"]["complete"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
