#!/usr/bin/env python3
"""Replay six retained responses: no transport, no repository/output mutation."""
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "LLM_ExpGym"
STUDY = ROOT / "kimi_k3_eval"
data = REPO / "data/hpo_tuning"
os.environ.update(HPOBENCH_ROOT=str(data / "HPOBench"), XDG_DATA_HOME=str(data / "hpobench_data"),
                  XDG_CACHE_HOME=str(data / "hpobench_cache"), XDG_CONFIG_HOME=str(STUDY / "data_runtime/hpobench_config"),
                  PYTHONNOUSERSITE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
sys.path.insert(0, str(REPO))
from expgym import react_loop
from expgym.extras.parallel_cache import AgentClock, SharedExplorationGraph, make_graph_augmenter
from expgym.task_tuning import _load_hpobench, evaluate_hpobench_action
from expgym.trace_v2 import source_tree_sha256
from scripts import run_poolact
from scripts.run_paper_sweep import _score_result

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

job_id = "poolact__tuning__hpobench_nasbench101_C__cost_moderate"
manifest_path = STUDY / "runs/full_v2/manifest.json"
manifest = json.loads(manifest_path.read_text())
job = next(job for job in manifest["jobs"] if job["id"] == job_id)
rows = []
for path in Path(job["dump_dir"]).glob("*.json"):
    raw = json.loads(path.read_text())
    if raw["context"].get("agent_id") == 3 and raw["context"].get("strategy") == "naive":
        rows.append((path, raw))
rows.sort(key=lambda row: row[1]["started_at_utc"])
assert len(rows) == 6 and len({raw["client_id"] for _, raw in rows}) == 1
with patch.object(sys, "argv", job["command"][2:]):
    args = run_poolact.parse_args()
base_cost = run_poolact.resolve_base_cost(args.scenario, args)
time_budget, baselines = run_poolact.resolve_cost_regime(args, base_cost)
task = _load_hpobench(args.tuning_task)
first_messages = rows[0][1]["request_payload"]["messages"]
tools = {"evaluate_config": lambda payload: evaluate_hpobench_action(task, payload)}

class RecordedResponses:
    def __init__(self):
        self.index = 0
        self.request_matches = []

    def generate(self, messages):
        path, raw = rows[self.index]
        expected = raw["request_payload"]["messages"]
        match = messages == expected
        self.request_matches.append({"path": str(path), "messages_exact_match": match})
        assert match, "offline trajectory differs from recorded request %d" % self.index
        self.index += 1
        message = raw["response_json"]["choices"][0]["message"]
        usage = raw["response_json"]["usage"]
        return react_loop.LLMOutput(text=message["content"], prompt_tokens=usage["prompt_tokens"],
                                    completion_tokens=usage["completion_tokens"])

def replay(lookup=None):
    llm = RecordedResponses()
    original = react_loop._lookup_answer_metrics
    with patch.object(react_loop, "_lookup_answer_metrics", lookup or original):
        result = react_loop.run_react_loop(llm=llm, tools=tools, time_budget=time_budget,
                    max_steps=args.max_steps, max_evals=args.max_evals, max_context_tokens=args.max_context_tokens,
                    context=first_messages[1]["content"], system_prompt=first_messages[0]["content"],
                    include_cost_in_observation=True, answer_evaluator=None)
        check = _score_result(result, tools, None)
    assert llm.index == len(rows)
    return {"requests": llm.request_matches, "responses_consumed": llm.index, "score_check": check,
            "result": {key: result.get(key) for key in ("answer", "answer_source", "answer_perf", "answer_overhead",
                      "answer_score_source", "api_calls", "evaluations", "total_overhead", "eval_time",
                      "eval_records", "tool_records", "aborted", "steps", "messages")}}

def canonical_only_json_lookup(answer_text, eval_records):
    canonical_answer = react_loop._canonicalize_payload(answer_text)
    for raw, canonical, perf, overhead in reversed(eval_records):
        if canonical is not None:
            if canonical_answer == canonical:
                return perf, overhead
        elif canonical_answer is None and raw in answer_text:
            return perf, overhead
    return None, None

current = replay()
candidate = replay(canonical_only_json_lookup)
assert current["score_check"]["ok"] is False
assert candidate["score_check"]["ok"] is True
assert current["result"]["api_calls"] == candidate["result"]["api_calls"] == 6
assert current["result"]["evaluations"] == candidate["result"]["evaluations"] == 5
assert current["result"]["eval_records"] == candidate["result"]["eval_records"]
assert current["result"]["tool_records"] == candidate["result"]["tool_records"]

graphs = []
for outcome in (current, candidate):
    graph = SharedExplorationGraph(n_agents=4, diversity_mode=True)
    for raw, canonical, perf, overhead in outcome["result"]["eval_records"]:
        graph.record_evaluate_config(3, canonical, raw, perf, overhead, completion_time=0.0)
    graph.record_end(3, outcome["result"]["answer"])
    clock = AgentClock()
    graphs.append({"prompt_with_current_clock_wiring": make_graph_augmenter(graph, clock=clock, agent_id=1)("Observation: example"),
                   "prompt_without_time_gate": graph.format_for_injection(visible_before=None, agent_id=1),
                   "end_node_count": len(graph._end_nodes)})

report = {"classification": "offline recorded-response replay only; no new LLM calls or replacement official results",
          "source_tree_sha256": source_tree_sha256(REPO), "manifest_path": str(manifest_path), "manifest_sha256": sha(manifest_path),
          "stdout_path": job["stdout_log"], "stdout_sha256": sha(job["stdout_log"]),
          "job_id": job_id, "agent_id": 3, "strategy": "naive", "client_id": rows[0][1]["client_id"],
          "base_cost": base_cost, "time_budget": time_budget, "baselines": baselines,
          "raw_files": [{"path": str(path), "sha256": sha(path), "request_id": raw["request_id"],
                         "started_at_utc": raw["started_at_utc"], "state": raw["state"],
                         "finish_reason": raw["response_json"]["choices"][0]["finish_reason"]} for path, raw in rows],
          "current_source_replay": current, "in_memory_candidate_replay": candidate,
          "candidate_scope": "one process replaces only _lookup_answer_metrics, does not change any source file",
          "shared_end_evidence": {"graph_records_end": True,
              "current_clock_gated_prompts_equal": graphs[0]["prompt_with_current_clock_wiring"] == graphs[1]["prompt_with_current_clock_wiring"],
              "unclocked_prompts_equal": graphs[0]["prompt_without_time_gate"] == graphs[1]["prompt_without_time_gate"], "graphs": graphs}}
print(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2))
