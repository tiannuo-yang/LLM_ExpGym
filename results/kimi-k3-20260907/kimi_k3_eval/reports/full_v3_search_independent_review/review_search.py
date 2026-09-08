#!/usr/bin/env python3
"""Recompute only the complete Search partition directly from frozen artifacts.

Uses the repository answer parser/name-F1 and vote-key normalization; this is
independent of audit_results/summarize_results, not a new independent scorer.
No model, search tool, API, or network operation is called.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[3]
REPO = BASE / "LLM_ExpGym"
sys.path.insert(0, str(REPO))
from expgym.react_loop import _extract_answer
from expgym.task_restricted_search import _extract_names, _name_f1, _normalize_name
from expgym.poolact import _search_vote_key, aggregate_results
from expgym.trace_v2 import materialize_message, source_tree_sha256, validate_trace_v2

REGIMES = ("cost_free", "cost_moderate", "cost_tight")
STRATEGIES = ("naive", "cached", "poolact")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reference(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def read(path, expected=None):
    ref = reference(path)
    if expected is not None:
        require(ref["sha256"] == expected, "file SHA differs: " + ref["path"])
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    require(reference(path) == ref, "file changed while read: " + ref["path"])
    return data, ref


def equal_number(left, right, label):
    require(all(not isinstance(x, bool) and isinstance(x, (int, float)) and math.isfinite(x) for x in (left, right))
            and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12), "numeric mismatch: " + label)


def score(answer, gold):
    answer = answer or ""
    require(isinstance(answer, str), "non-text Search answer")
    predicted = _extract_names(answer)
    expected = {_normalize_name(value) for value in gold}
    # A separate algebraic check reuses extraction but not _name_f1's formula.
    direct = (2 * len(predicted & expected) / (len(predicted) + len(expected))
              if predicted or expected else 1.0)
    value = _name_f1(answer, gold)
    equal_number(value, direct, "name-set F1 formula")
    return value, sorted(predicted), sorted(expected)


def vote(answers):
    keys = [_search_vote_key(answer) for answer in answers]
    counts = Counter(keys)
    maximum = max(counts.values())
    leaders = [key for key in counts if counts[key] == maximum]
    eligible = [key for key in leaders if key] or leaders
    winning_key = next(key for key in keys if key in eligible)
    winner = keys.index(winning_key)
    return {"answer": str(answers[winner] or ""), "winner_agent_id": winner,
            "tie_at_maximum_count": len(leaders) > 1,
            "empty_nonempty_tie": () in leaders and any(leaders),
            "groups": [{"key": list(key), "votes": count, "first_agent_id": keys.index(key)}
                       for key, count in counts.items()]}


def self_test():
    equal_number(score('Alice, Bob', ['alice', 'Cara'])[0], .5, "partial F1")
    equal_number(score('', [])[0], 1, "empty gold and prediction")
    equal_number(score('Alice', [])[0], 0, "empty gold with prediction")
    equal_number(score('one two three four five six', ['one two three four five six'])[0], 0, "non-JSON long phrase filtered")
    equal_number(score('["one two three four five six"]', ['one two three four five six'])[0], 1, "JSON long phrase retained")
    require(vote(['', '', 'Alice', 'ALICE'])["winner_agent_id"] == 2, "tie favors nonempty")
    require(vote(['Alice', 'Bob', 'Alice', 'Bob'])["winner_agent_id"] == 0, "tie favors first agent")
    require(vote(['A, B', '["b", "a"]', 'C', 'D'])["winner_agent_id"] == 0, "set ordering shares vote")
    answers = ['["1. Alice"]', 'Alice', 'Bob', 'Carol']
    require(vote(answers)["winner_agent_id"] == 0 and score(answers[0], ['Alice'])[0] == 0,
            "score raw winner, not normalized vote key")
    for answers in [['', '', 'Alice', 'ALICE'], ['Alice', 'Bob', 'Alice', 'Bob'], ['A, B', '["b", "a"]', 'C', 'D']]:
        actual = aggregate_results("restricted_search", [{"answer": answer, "answer_perf": 0} for answer in answers],
                                   answer_evaluator=lambda answer: _name_f1(answer, ['Alice']))
        require(actual["answer"] == vote(answers)["answer"], "independent vote differs from repository")
    return {"passed": True, "cases": 12}


def summarize_questions(rows):
    groups = defaultdict(list)
    for row in rows:
        for subset in ["full"] + (["paper_poolact"] if row["system"] == "poolact" and row["dimension"] == "whois"
                                  and row["cost_regime"] != "cost_free" else []):
            for metric, value in row["metrics"].items():
                groups[(subset, row["system"], row["dimension"], row["cost_regime"], row["strategy"], metric)].append(value)
    aggregates = []
    for key, values in sorted(groups.items(), key=lambda item: str(item[0])):
        subset, system, dimension, regime, strategy, metric = key
        count = 18 if dimension == "whois" else 17
        require(len(values) == count, "group lacks exact question coverage: " + str(key))
        aggregates.append({"subset": subset, "system": system, "dimension": dimension, "cost_regime": regime,
                           "strategy": strategy, "metric": metric, "value": sum(values) / len(values),
                           "questions": len(values), "unit": "percent"})
    return aggregates


def review(manifest_path):
    checks = self_test()
    manifest, manifest_ref = read(manifest_path)
    require(manifest["stage"] == "full" and manifest["settings"]["search_data_source"] == "phantom_seed1", "not requested full seed-1 matrix")
    require(source_tree_sha256(REPO) == manifest["source_tree_sha256"], "current scorer source differs from manifest")
    progress, progress_ref = read(manifest["progress_path"])
    dataset, dataset_ref = read(manifest["data_provenance"]["dataset_manifest"]["path"],
                                manifest["data_provenance"]["dataset_manifest"]["sha256"])
    qa_file = next(row for row in dataset["files"] if row["path"].endswith("question-answer/depth_20_size_5000_seed_1-00000-of-00001.parquet"))
    qa_ref = reference(REPO / qa_file["path"])
    require(qa_ref["sha256"] == qa_file["sha256"], "gold QA parquet differs from pinned dataset manifest")
    import pyarrow.parquet as pq
    questions = pq.read_table(qa_ref["path"], columns=["question", "answer", "type", "difficulty"]).to_pylist()
    questions = [row for row in questions if row["type"] in (11, 12, 27, 28) and len(row["answer"]) <= 20]
    questions.sort(key=lambda row: (row["type"], row["difficulty"]))
    require(len(questions) == 35 and all(row["type"] in (11, 12) for row in questions[:18])
            and all(row["type"] in (27, 28) for row in questions[18:]), "whois/whatis split differs")
    require([dict(row, index=index) for index, row in enumerate(questions)] == dataset["search"]["items"], "gold question identities differ from dataset manifest")
    jobs = [job for job in manifest["jobs"] if job["scenario"] == "restricted_search"]
    expected_jobs = {(system, index, regime) for system in ("expgym", "poolact") for index in range(35) for regime in REGIMES}
    require(len(jobs) == 210 and {(job["system"], job["question_index"], job["cost_regime"]) for job in jobs} == expected_jobs,
            "Search manifest matrix differs")
    questions_out, agents_out, files, statuses = [], [], [], []
    for job in jobs:
        state = progress["jobs"][job["id"]]
        require(state["status"] == "completed" and state["returncode"] == 0, "Search job not completed: " + job["id"])
        statuses.append({"job_id": job["id"], "status": state["status"], "returncode": state["returncode"]})
        index = job["question_index"]
        gold = questions[index]["answer"]
        expected_strategies = set(STRATEGIES) if job["system"] == "poolact" else {None}
        require({row.get("strategy") for row in job["expected_outputs"]} == expected_strategies
                and len(job["expected_outputs"]) == len(expected_strategies), "unexpected output slots")
        item_summary = None
        if job["system"] == "poolact":
            item_summary, ref = read(job["summary_path"])
            files.append(dict(ref, role="poolact_item_summary"))
        for output in job["expected_outputs"]:
            data, ref = read(output["path"])
            files.append(dict(ref, role=output["kind"]))
            common = {"job_id": job["id"], "system": job["system"], "question_index": index, "item_id": str(index),
                      "dimension": "whois" if index < 18 else "whatis", "cost_regime": job["cost_regime"],
                      "strategy": output.get("strategy"), "path": ref["path"], "sha256": ref["sha256"]}
            if job["system"] == "expgym":
                validate_trace_v2(data)
                task, outcome = data["task"], data["outcome"]
                require(data["provenance"]["repository"]["source_tree_sha256"] == manifest["source_tree_sha256"], "trace source mismatch")
                require(task["scenario"] == "restricted_search" and task["item"]["id"] == index
                        and task["item"]["source"] == "phantom_seed1" and task["budget"]["regime"] == job["cost_regime"], "trace task mismatch")
                require(data["run"]["model"]["id"] == manifest["settings"]["model"] and data["run"]["seed"] == output["seed"], "trace model/seed mismatch")
                require(outcome["validation"]["passed"] is True, "saved trace validation failed")
                text = materialize_message(data, outcome["answer_message_id"])["content"] if outcome.get("answer_message_id") else ""
                answer = outcome.get("answer_override", _extract_answer(text) or text)
                f1, predicted, normalized_gold = score(answer, gold)
                equal_number(outcome["score"]["value"], f1, ref["path"])
                row = dict(common, answer=answer, saved_answer_perf=outcome["score"]["value"], recomputed_answer_perf=f1,
                           predicted_names=predicted, gold_names=normalized_gold, metrics={"F1_pct": f1 * 100})
                questions_out.append(row)
                agents_out.append(dict(common, agent_id=None, answer=answer, recomputed_answer_perf=f1,
                                       saved_answer_perf=outcome["score"]["value"]))
                continue
            require(data["implementation_sha256"]["source_tree"] == manifest["source_tree_sha256"], "PoolAct source mismatch")
            config = data["config"]
            require(config["question_index"] == index and config["data_source"] == "phantom_seed1" and config["scenario"] == "restricted_search"
                    and config["cost_regime"] == job["cost_regime"] and config["model"] == manifest["settings"]["model"], "PoolAct task/model mismatch")
            require(data["strategy"] == output["strategy"] and data["agents"] == 4 and len(data["agent_results"]) == 4
                    and len(output["agent_paths"]) == 4, "PoolAct strategy/agent count mismatch")
            require([row["agent_id"] for row in data["agent_results"]] == list(range(4)), "agent order not canonical")
            shared = data.get("shared_state") or {}
            if output["strategy"] == "poolact":
                require(shared.get("graph", {}).get("pending_claims") == 0, "unclosed PoolAct graph claims")
            if "pending_claims" in shared:
                require(shared["pending_claims"] == 0, "unclosed shared claims")
            answers, perfs = [], []
            for agent_id, (agent, path) in enumerate(zip(data["agent_results"], output["agent_paths"])):
                separate, agent_ref = read(path)
                files.append(dict(agent_ref, role="poolact_agent"))
                require(agent == separate, "embedded/separate agent mismatch: " + str(path))
                require(agent["seed"] == output["agent_seeds"][agent_id] and agent["strategy"] == output["strategy"], "agent seed/strategy mismatch")
                require(agent["score_check"]["ok"] is True, "saved agent score_check failed")
                f1, predicted, normalized_gold = score(agent["answer"], gold)
                for value in (agent["answer_perf"], agent["score_check"]["reported_perf"], agent["score_check"]["recomputed_perf"]):
                    equal_number(value, f1, str(path))
                answers.append(agent["answer"] or "")
                perfs.append(f1)
                agent_common = dict(common, path=agent_ref["path"], sha256=agent_ref["sha256"])
                agents_out.append(dict(agent_common, agent_id=agent_id, parent_result_path=ref["path"], answer=agent["answer"],
                                       saved_answer_perf=agent["answer_perf"], recomputed_answer_perf=f1,
                                       predicted_names=predicted, gold_names=normalized_gold))
            selected = vote(answers)
            aggregate = data["aggregate"]
            require(aggregate["method"] == "majority_vote" and aggregate["answer"] == selected["answer"], "saved majority-vote answer differs")
            require(aggregate["individual_answers"] == answers, "saved aggregate answer list differs")
            for left, right in zip(aggregate["individual_perfs"], perfs):
                equal_number(left, right, "aggregate individual score")
            require(len(aggregate["individual_perfs"]) == 4, "aggregate individual score count")
            mv, predicted, normalized_gold = score(selected["answer"], gold)
            equal_number(aggregate["answer_perf"], mv, "saved aggregate F1")
            original = aggregate_results("restricted_search", data["agent_results"], answer_evaluator=lambda answer: _name_f1(answer, gold))
            require(original == aggregate, "repository aggregation cross-check differs")
            require(item_summary["strategies"][output["strategy"]] == aggregate and item_summary["config"] == config
                    and item_summary["implementation_sha256"] == data["implementation_sha256"], "item summary differs from strategy result")
            questions_out.append(dict(common, answer=selected["answer"], saved_answer_perf=aggregate["answer_perf"], recomputed_answer_perf=mv,
                                      predicted_names=predicted, gold_names=normalized_gold, vote=selected,
                                      metrics={"MV_F1_pct": mv * 100, "MI_F1_pct": sum(perfs) / 4 * 100}))
    require(len(questions_out) == 420 and len(agents_out) == 1365, "final Search partition counts differ")
    require(len({row["path"] for row in files}) == len(files), "duplicate selected artifact path")
    for item in files:
        require(reference(item["path"])["sha256"] == item["sha256"], "artifact changed during review")
    require(source_tree_sha256(REPO) == manifest["source_tree_sha256"], "scorer source changed during review")
    return {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "complete": True,
            "scope": "Custom study; Search partition only. Does not establish full-matrix completion, raw API integrity, or model protocol correctness.",
            "manifest": manifest_ref, "source_tree_sha256": manifest["source_tree_sha256"], "model_id": manifest["settings"]["model"],
            "progress_snapshot": {"reference": progress_ref, "observed_status": progress["status"], "job_counts": progress["job_counts"], "search_jobs": statuses},
            "counts": {"search_jobs": 210, "expgym_traces": 105, "poolact_strategy_results": 315, "poolact_agents": 1260},
            "dataset_manifest": dataset_ref, "gold_qa_parquet": qa_ref, "gold_questions": questions,
            "method": {"f1": "Repository _name_f1 with independently checked set-F1 formula 2*intersection/(pred+gold); empty sets scored as repository specifies.",
                       "mv": "Independently group repository semantic vote keys; most votes, nonempty wins a count tie, then earliest agent. Score the original winning answer, not a reconstructed normalized string.",
                       "mi": "Arithmetic mean of four independently recomputed agent F1 values per question, then equal mean over 18 whois or 17 whatis questions.",
                       "independence_boundary": "No audit_results or summarize_results code/values used; repository answer extraction/name scorer/vote-key normalizer and schema validator reused, so not a fully independent reimplementation of the scorer."},
            "source_references": [reference(REPO / path) for path in ("expgym/task_restricted_search.py", "expgym/poolact.py", "expgym/react_loop.py", "expgym/trace_v2.py")],
            "paper_reference": dict(reference(BASE / "expgym-paper/versions/iclr2026/main.tex"),
                                    relevant_lines="293; 582-589", note="Paper defines task macro F1 and four-agent MV/MI; tie and normalization details are current repository behavior, not specified paper rules."),
            "script": reference(__file__), "boundary_checks": checks, "files": files,
            "questions": questions_out, "agents": agents_out, "aggregate_metrics": summarize_questions(questions_out),
            "tie_results": sum(row.get("vote", {}).get("tie_at_maximum_count", False) for row in questions_out),
            "empty_nonempty_tie_results": sum(row.get("vote", {}).get("empty_nonempty_tie", False) for row in questions_out)}


def comparison(review_path, summary_path):
    reviewed, review_ref = read(review_path)
    summary, summary_ref = read(summary_path)
    require(reviewed["complete"] is True and summary.get("complete") is True and summary["stage"] == "full", "review/summary is not passed full-stage evidence")
    require(summary["manifest_sha256"] == reviewed["manifest"]["sha256"] and summary["model_id"] == reviewed["model_id"], "summary belongs to another run")
    for item in reviewed["files"]:
        require(reference(item["path"])["sha256"] == item["sha256"], "reviewed raw file changed before summary comparison")
    counts = {}
    for key, expected in (("artifacts", reviewed["questions"]), ("agents", reviewed["agents"])):
        selected = [row for row in summary[key] if row["scenario"] == "restricted_search"]
        wanted = {row["path"]: row for row in expected}
        require(len(selected) == len(wanted) and {row["path"] for row in selected} == set(wanted), "summary Search path set differs: " + key)
        for row in selected:
            other = wanted[row["path"]]
            require(row["status"] == "valid" and row["sha256"] == other["sha256"], "summary raw identity differs")
            equal_number(row["answer_perf"], other["recomputed_answer_perf"], "summary " + key)
        counts[key] = len(selected)
    def identity(row, with_item=False):
        return (row["subset"], row["system"], row["dimension"], row["cost_regime"], row["strategy"], row["metric"]) + ((row["item_id"],) if with_item else ())
    wanted = {identity(row): row for row in reviewed["aggregate_metrics"]}
    selected = [row for row in summary["aggregate_metrics"] if row["scenario"] == "restricted_search"]
    require(len(selected) == len(wanted) and {identity(row) for row in selected} == set(wanted), "summary aggregate Search cells differ")
    for row in selected:
        other = wanted[identity(row)]
        require(row["complete"] is True and row["expected_tasks"] == row["numeric_tasks"] == other["questions"], "summary group coverage differs")
        equal_number(row["value"], other["value"], "summary aggregate F1/MV/MI")
    counts["aggregate_metric_cells"] = len(selected)
    wanted = {}
    for row in reviewed["questions"]:
        for subset in ["full"] + (["paper_poolact"] if row["system"] == "poolact" and row["dimension"] == "whois" and row["cost_regime"] != "cost_free" else []):
            for metric, value in row["metrics"].items():
                item = dict(row, subset=subset, metric=metric, value=value)
                wanted[identity(item, True)] = item
    selected = [row for row in summary["task_metrics"] if row["scenario"] == "restricted_search"]
    require(len(selected) == len(wanted) and {identity(row, True) for row in selected} == set(wanted), "summary question metric cells differ")
    for row in selected:
        other = wanted[identity(row, True)]
        require(row["complete"] is True and row["paths"] == [other["path"]], "summary question path differs")
        equal_number(row["value"], other["value"], "summary per-question F1/MV/MI")
    counts["question_metric_cells"] = len(selected)
    return {"schema_version": 1, "complete": True, "scope": "Search partition comparison only", "created_at": datetime.now(timezone.utc).isoformat(),
            "independent_review": review_ref, "summary": summary_ref, "matched_counts": counts, "comparison_script": reference(__file__)}


def write_json(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--compare-summary", type=Path)
    parser.add_argument("--comparison-output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test()))
    elif args.compare_summary:
        require(args.review is not None and args.comparison_output is not None, "comparison requires --review and --comparison-output")
        data = comparison(args.review, args.compare_summary)
        write_json(args.comparison_output, data)
        print(json.dumps(data))
    else:
        require(args.manifest is not None and args.output_dir is not None, "review requires --manifest and --output-dir")
        data = review(args.manifest)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "review.json", data)
        for key in ("aggregate_metrics", "questions", "agents"):
            rows = data[key]
            with (args.output_dir / (key + ".csv")).open("x", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(key for row in rows for key in row)))
                writer.writeheader()
                writer.writerows({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value for key, value in row.items()} for row in rows)
        print(json.dumps({"complete": data["complete"], "counts": data["counts"], "aggregate_metrics": data["aggregate_metrics"], "tie_results": data["tie_results"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
