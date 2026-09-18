#!/usr/bin/env python3
"""Rescore every adopted HPO endpoint from immutable saved interaction evidence.

No models are called. The historical tuning_final_policy=legacy is retained:
match the submitted configuration to visible evaluations; if unmatched, use
the best visible evaluation only when an answer was emitted. With no visible
evaluation, score the submitted configuration independently with the original
benchmark. Hidden feedback never supplies a selected performance.

The output is existing_trace_rescored. It is not a counterfactual replay of a
changed interaction policy; control-flow changes and graph versions are kept
explicit for the separately run controls.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import gzip
import json
import math
import os
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from expgym import tool_protocol
from expgym.errors import InvalidConfigurationError
from expgym.react_loop import _lookup_answer_metrics, _parse_tool_return
from expgym.trace_v2 import materialize_message

BASELINE = "297c3d00a006f33fc5a8ca799ce91d327d92839e"
IDENTITY = ("slot_id", "model", "system", "scenario", "item", "regime", "strategy", "seed", "outer_repeat")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def jdump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def csv_read(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def csv_write(path, rows, fields=None):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def close(a, b):
    return a is b if a is None or b is None else math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9)


def complete_mean(values):
    return mean(values) if values and all(x is not None for x in values) else None


def json_configuration(answer):
    try:
        return isinstance(tool_protocol.parse_json_answer(answer), (dict, list))
    except (ValueError, TypeError):
        return False


def old_parser(commit, source_root=None):
    raw = (Path(source_root) / "expgym/tool_protocol.py").read_bytes() if source_root else subprocess.check_output(["git", "show", commit + ":expgym/tool_protocol.py"], cwd=REPO)
    module = types.ModuleType("_historical_hpo_tool_protocol_" + sha(raw)[:16])
    sys.modules[module.__name__] = module
    exec(compile(raw, commit + ":expgym/tool_protocol.py", "exec"), module.__dict__)
    return module, sha(raw)


def baseline_final(module, text, allow_unlabelled):
    if module.extract_text_action(text) is not None:
        return None
    answer = module.extract_text_answer(text)
    if allow_unlabelled:
        answer = answer or module.structured_final_answer(text) or (module.unlabelled_final_answer(text) if hasattr(module, "unlabelled_final_answer") else text)
    return answer


def n1_agent(trace):
    o = trace["outcome"]
    records, provenance = [], []
    for t in trace["tool_calls"]:
        if t["included_in_eval_records"]:
            assert t["visible_to_model"]
            records.append([t["raw_arguments"], t["canonical_argument"], t["performance"], t["simulated_cost_seconds"]])
            provenance.append(t["id"])
    messages = [materialize_message(trace, m["id"]) for m in trace["messages"] if not m.get("request_only")]
    agent = dict(o, answer_perf=o["score"].get("value"), eval_records=records,
                 messages=messages, agent_id=0, seed=trace["run"]["seed"])
    turns = []
    for idx, c in enumerate(trace["llm_calls"], 1):
        m = materialize_message(trace, c["output_message_id"])
        turns.append(dict(message=m, message_id=c["output_message_id"], call_index=idx,
                          forced=bool(c.get("forced")), finish_reason=c.get("finish_reason"),
                          is_terminal=c["output_message_id"] == o["answer_message_id"]))
    return agent, provenance, turns


def n4_agent(agent):
    failures = {x["llm_call_index"]: x for x in agent.get("protocol_failures", [])}
    messages = [(i, m) for i, m in enumerate(agent["messages"]) if m.get("role") == "assistant"]
    turns = []
    for idx, (message_index, message) in enumerate(messages, 1):
        failure = failures.get(idx, {})
        terminal = idx == len(messages)
        turns.append(dict(message=message, message_id="messages[" + str(message_index) + "]", call_index=idx,
                          forced=bool(failure.get("forced") or (terminal and agent.get("aborted"))),
                          finish_reason=failure.get("finish_reason"), is_terminal=terminal))
    assert len(messages) == agent["api_calls"], "Cannot map N4 assistant decisions to recorded API calls"
    return agent, ["eval_records[" + str(i) + "]" for i in range(len(agent["eval_records"]))], turns


def parse_turn(turn, protocol, parser, baseline=None):
    m = turn["message"]
    if turn["finish_reason"] == "length" or m.get("tool_calls"):
        return None
    text = (m.get("content") or "").strip()
    if not isinstance(text, str) or not text:
        return None
    allow = protocol == "native" or turn["forced"]
    return baseline_final(baseline, text, allow) if baseline else parser(text, allow_unlabelled=allow)


class Evaluator:
    def __init__(self, certificates=None, paramnet_python=None, worker_state=None):
        self.tools = {}
        self.cache = {}
        self.calls = 0
        self.certificates = certificates
        self.certificate_uses = 0
        self.paramnet_python = paramnet_python
        self.worker = None
        self.worker_state = worker_state

    def evaluate(self, item, answer):
        key = item, answer
        if key in self.cache:
            return self.cache[key]
        if self.certificates is not None:
            ref = self.certificates[(item, sha(answer.encode()))]
            assert ref["answer"] == answer
            result = ref["performance"], ref["evaluation_reason"]
            self.cache[key] = result
            self.certificate_uses += 1
            return result
        if item.startswith("hpobench:paramnet:") and self.paramnet_python:
            if self.worker is None:
                data_root = Path(os.environ["HPOBENCH_ROOT"]).resolve().parent
                self.worker = subprocess.Popen([str(self.paramnet_python), str(REPO / "tools/rescore_hpo_paramnet_worker.py"), "--repo", str(REPO), "--data-root", str(data_root), "--state-root", str(self.worker_state)],
                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
            self.worker.stdin.write(jdump(dict(item=item, answer=answer)) + "\n")
            self.worker.stdin.flush()
            response_line = self.worker.stdout.readline()
            if not response_line:
                raise RuntimeError("ParamNet evaluator exited without a response; inspect its stderr")
            response = json.loads(response_line)
            if "error" in response:
                raise RuntimeError("ParamNet independent evaluator failed: " + str(response["error"]))
            result = response["performance"], response["evaluation_reason"]
            self.calls += 1
            self.cache[key] = result
            return result
        from expgym.task_tuning import build_tools
        if item not in self.tools:
            self.tools[item] = build_tools(tuning_task=item)["evaluate_config"]
        self.calls += 1
        try:
            perf, _, _ = _parse_tool_return(self.tools[item](answer))
            assert finite(perf)
            result = perf, "benchmark_evaluation"
        except InvalidConfigurationError:
            result = 0.0, "invalid_configuration_zero"
        self.cache[key] = result
        return result


def select_answer(answer, records, record_ids, item, evaluator):
    if answer is None:
        return None, None, None, None, "no_accepted_final_configuration"
    perf, _ = _lookup_answer_metrics(answer, records)
    if perf is not None:
        # Derive exactly which visible record the reverse matching policy used.
        matched = next(i for i in range(len(records) - 1, -1, -1)
                       if _lookup_answer_metrics(answer, [records[i]])[0] is not None)
        return answer, perf, "matching_tool_call", record_ids[matched], "visible_configuration_match"
    scored = [(i, r) for i, r in enumerate(records) if finite(r[2])]
    if scored:
        index, selected = max(scored, key=lambda pair: pair[1][2])
        return selected[0], selected[2], "best_evaluated_fallback", record_ids[index], "legacy_best_visible_fallback"
    if records:
        return answer, None, None, None, "legacy_visible_records_without_numeric_score"
    perf, reason = evaluator.evaluate(item, answer)
    return answer, perf, "offline_final_answer", "offline_submitted_configuration", reason


def perfs_metrics(perfs, finals, item, oracle):
    ref = oracle[item]
    def gap(p):
        return None if p is None else max(0.0, 100 * (p - ref["mean_perf"]) / (ref["best_perf"] - ref["mean_perf"]))
    gaps = [gap(p) for p in perfs]
    gaps0 = [0.0 if p is None and a is None else g for p, a, g in zip(perfs, finals, gaps)]
    if len(perfs) == 1:
        return dict(raw_perf=perfs[0], gap=gaps[0], gap0=gaps0[0])
    return dict(raw_perf_mi=complete_mean(perfs), raw_perf_bon=max(perfs) if all(p is not None for p in perfs) else None,
                gap_mi=complete_mean(gaps), gap_bon=max(gaps) if all(g is not None for g in gaps) else None,
                gap0_mi=complete_mean(gaps0), gap0_bon=max(gaps0) if all(g is not None for g in gaps0) else None)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, default=REPO / "results/gemini-openrouter-20260917/main")
    p.add_argument("--archive", type=Path)
    p.add_argument("--inputs", type=Path, help="Replay published minimal scoring_inputs.jsonl.gz; no raw trajectories required")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source-map", type=Path, help="Optional JSON list or {sources:list}, paths may override saved INPUTS paths")
    p.add_argument("--baseline-commit", default=BASELINE)
    p.add_argument("--versions", type=Path, help="Source-tree-verified per-slot runtime mapping; required for complete control-flow audit")
    p.add_argument("--verify-benchmarks", action="store_true", help="Also independently evaluate every old and new selected configuration")
    p.add_argument("--paramnet-python", type=Path, help="Optional historical Python executable for ParamNet sklearn-0.23 pickle evaluator")
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    parser_source_hash = sha((REPO / "expgym/tool_protocol.py").read_bytes())
    script_source_hash = sha(Path(__file__).read_bytes())
    package_by_id = {}
    certificates = None
    if args.inputs:
        with gzip.open(args.inputs, "rt") as handle:
            packages = [json.loads(line) for line in handle]
        package_by_id = {r["source"]["slot_id"]: r for r in packages}
        sources = [r["source"] for r in packages]
        scalars = {r["source"]["slot_id"]: r["scalar"] for r in packages}
        certificates = {(e["item"], e["answer_sha256"]): e for r in packages for e in r["benchmark_certificates"]}
        new_paths = {}
    else:
        if not args.archive:
            p.error("--archive is required for full-trace mode")
        sources = csv_read(args.report / "SOURCE_SELECTION.csv")
        scalars = {r["slot_id"]: r for r in csv_read(args.report / "slot_scalars.csv")}
        inputs = json.loads((args.report / "INPUTS.json").read_text())
        new_paths = {r["slot_id"]: r["path"] for r in inputs["new_results"]}
    overrides = {}
    if args.source_map:
        smap = json.loads(args.source_map.read_text())
        for r in smap if isinstance(smap, list) else smap["sources"]:
            overrides[r["slot_id"]] = r["source_path"]
    oracle_path = REPO / "data/hpo_tuning/oracle3.json"
    if not args.inputs:
        assert sha(oracle_path.read_bytes()) == inputs["frozen"]["inputs"]["oracle"]["sha256"]
    oracle = json.loads(oracle_path.read_text())["tasks"]
    if args.inputs:
        assert all(r["oracle_reference"] == oracle[r["source"]["item"]] for r in packages)
        assert all(r["parser_sha256"] == sha((REPO / "expgym/tool_protocol.py").read_bytes()) for r in packages)
    old, old_sha = (None, packages[0]["baseline_parser_sha256"]) if args.inputs else old_parser(args.baseline_commit)
    versions = {r["slot_id"]: r for r in csv_read(args.versions)} if args.versions else {}
    runtime_parsers = {}
    evaluator = Evaluator(certificates, args.paramnet_python, args.output / "paramnet_worker_state")
    agents, slots, turn_changes, inventory = [], [], [], []
    packages_out = []
    total_turns = 0
    for src in sources:
        if src["scenario"] != "tuning":
            continue
        sid = src["slot_id"]
        n1 = src["system"] == "expgym"
        package = package_by_id.get(sid)
        if not package and versions:
            runtime_version = versions[sid]
            assert runtime_version["source_tree_verified"] == "True"
            runtime_root = runtime_version["source_root"]
            if runtime_root not in runtime_parsers:
                runtime_parsers[runtime_root] = old_parser(args.baseline_commit, runtime_root)
            runtime_old, runtime_old_sha = runtime_parsers[runtime_root]
        else:
            runtime_old, runtime_old_sha = old, old_sha
        if package:
            path = Path(package["source_path"])
            source_bytes = package["source_bytes"]
            collection = [(a["agent"], a["record_ids"], [a["terminal_turn"]]) for a in package["agents"]]
            version = package["poolact_protocol"]
        else:
            path = Path(overrides[sid]) if sid in overrides else (args.archive / src["historical_trajectory"] if src["historical_trajectory"] else Path(new_paths[sid]))
            raw = path.read_bytes()
            source_bytes = len(raw)
            assert sha(raw) == src["result_sha256"], (sid, "source hash mismatch")
            obj = json.loads(raw)
            collection = [n1_agent(obj)] if n1 else [n4_agent(a) for a in obj["agent_results"]]
            version = obj.get("config", {}).get("poolact_protocol", "n1")
        assert len(collection) == (1 if n1 else 4)
        ident = {k: src[k] for k in IDENTITY}
        slot_agents = []
        projected_agents = []
        for ai, (agent, record_ids, turns) in enumerate(collection):
            turn_count = package["agents"][ai]["assistant_turns_checked"] if package else len(turns)
            total_turns += turn_count
            protocol = agent.get("tool_protocol", "native")
            assert agent.get("tuning_final_policy", "legacy") == "legacy"
            changed_turns = list(package["agents"][ai]["full_trace_turn_changes"]) if package else []
            if package:
                turn_changes.extend(changed_turns)
            for turn in ([] if package else turns):
                before = parse_turn(turn, protocol, None, baseline=runtime_old)
                after = parse_turn(turn, protocol, tool_protocol.parse_final_answer)
                if before != after:
                    change = dict(ident, agent_id=agent["agent_id"], call_index=turn["call_index"], message_id=turn["message_id"],
                                  is_terminal=turn["is_terminal"], old_accepts_final=before is not None, new_accepts_final=after is not None,
                                  action_control_flow_changed=(before is None) != (after is None), old_payload=before, new_payload=after,
                                  source_sha256=src["result_sha256"])
                    turn_changes.append(change)
                    changed_turns.append(change)
            finals = [t for t in turns if t["is_terminal"]]
            assert len(finals) == 1, (sid, "ambiguous terminal")
            final_turn = finals[0]
            historical_extracted = package["agents"][ai]["historical_terminal_payload"] if package else parse_turn(final_turn, protocol, None, baseline=runtime_old)
            # This is the only assistant text needed to recompute final scoring.
            # Nonterminal acceptance audit is supplied as a separate, explicitly
            # historical attestation in lightweight replay.
            projected_agents.append(dict(
                agent={k: agent.get(k) for k in ("answer", "answer_perf", "answer_score_source", "score_status", "eval_records", "agent_id", "seed", "tool_protocol", "tuning_final_policy")},
                historical_terminal_payload=historical_extracted,
                record_ids=record_ids, terminal_turn={**final_turn, "message": {"role": "assistant", "content": final_turn["message"].get("content"), "tool_calls": bool(final_turn["message"].get("tool_calls"))}},
                assistant_turns_checked=turn_count, full_trace_turn_changes=changed_turns))
            extracted = parse_turn(final_turn, protocol, tool_protocol.parse_final_answer)
            answer, perf, score_source, record_id, selection_reason = select_answer(extracted, agent["eval_records"], record_ids, src["item"], evaluator)
            old_answer, old_perf = agent.get("answer"), agent.get("answer_perf")
            if old_perf is not None:
                if agent.get("answer_score_source") == "offline_final_answer":
                    reproduced, _ = evaluator.evaluate(src["item"], old_answer)
                else:
                    reproduced, _ = _lookup_answer_metrics(old_answer, agent["eval_records"])
                assert close(reproduced, old_perf), (sid, agent["agent_id"], "old score cannot be reproduced", old_perf, reproduced)
            benchmark_old = benchmark_new = None
            if args.verify_benchmarks:
                for which, selected, saved in (("old", old_answer, old_perf), ("new", answer, perf)):
                    if saved is not None:
                        measured, _ = evaluator.evaluate(src["item"], selected)
                        assert close(measured, saved), (sid, agent["agent_id"], which, "benchmark mismatch", measured, saved)
                        if which == "old": benchmark_old = measured
                        else: benchmark_new = measured
            answer_changed = old_answer != answer
            score_changed = not close(old_perf, perf)
            control_changed = any(c["action_control_flow_changed"] for c in changed_turns)
            reason = ("final_boundary_reparsed;" if any(c["is_terminal"] for c in changed_turns) else "") + selection_reason
            row = dict(ident, agent_id=agent["agent_id"], agent_seed=agent.get("seed"),
                       scoring_release="existing_trace_rescored", tuning_final_policy="legacy", poolact_protocol=version,
                       old_answer=old_answer, old_extracted_answer=historical_extracted, new_extracted_answer=extracted, new_answer=answer,
                       old_perf=old_perf, new_perf=perf, delta_perf=(perf-old_perf) if perf is not None and old_perf is not None else None,
                       old_final_present=old_answer is not None, new_final_present=answer is not None,
                       old_final_json_configuration=json_configuration(old_answer), new_final_json_configuration=json_configuration(answer),
                       new_model_final_json_configuration=json_configuration(extracted),
                       old_score_complete=finite(old_perf), new_score_complete=finite(perf),
                       old_score_status=agent.get("score_status"),
                       new_score_status="scored_final_answer" if finite(perf) else ("unscorable_missing_configuration" if answer is None else "unscorable_configuration"),
                       old_answer_score_source=agent.get("answer_score_source"), new_answer_score_source=score_source,
                       visible_eval_count=len(agent["eval_records"]), selected_visible_record=record_id,
                       answer_changed=answer_changed, score_changed=score_changed, reason=reason,
                       extracted_answer_changed=historical_extracted != extracted,
                       score_source_changed=agent.get("answer_score_source") != score_source,
                       action_control_flow_changed=control_changed, assistant_turns_checked=turn_count,
                       changed_terminal_acceptance=any(c["is_terminal"] and c["action_control_flow_changed"] for c in changed_turns),
                       earlier_acceptance_changed=any(not c["is_terminal"] and c["action_control_flow_changed"] for c in changed_turns),
                       benchmark_old_perf=benchmark_old, benchmark_new_perf=benchmark_new,
                       historical_parser_sha256=package["historical_parser_sha256"] if package else runtime_old_sha,
                       old_metrics_json=jdump(perfs_metrics([old_perf], [old_answer], src["item"], oracle)),
                       new_metrics_json=jdump(perfs_metrics([perf], [answer], src["item"], oracle)),
                       terminal_message_id=final_turn["message_id"], source_sha256=src["result_sha256"], source_path=str(path))
            agents.append(row)
            slot_agents.append(row)
        old_metrics = perfs_metrics([a["old_perf"] for a in slot_agents], [a["old_answer"] for a in slot_agents], src["item"], oracle)
        saved_metrics = json.loads(scalars[sid]["metrics_json"])
        assert old_metrics.keys() == saved_metrics.keys() and all(close(old_metrics[k], saved_metrics[k]) for k in old_metrics), (sid, "old scalar mismatch")
        new_metrics = perfs_metrics([a["new_perf"] for a in slot_agents], [a["new_answer"] for a in slot_agents], src["item"], oracle)
        slots.append(dict(ident, scoring_release="existing_trace_rescored", poolact_protocol=version,
                          old_metrics_json=jdump(saved_metrics), new_metrics_json=jdump(new_metrics),
                          old_score_complete=all(a["old_score_complete"] for a in slot_agents),
                          new_score_complete=all(a["new_score_complete"] for a in slot_agents),
                          new_final_present=all(a["new_final_present"] for a in slot_agents),
                          answer_changed=any(a["answer_changed"] for a in slot_agents),
                          extracted_answer_changed=any(a["extracted_answer_changed"] for a in slot_agents),
                          score_source_changed=any(a["score_source_changed"] for a in slot_agents),
                          score_changed=any(not close(old_metrics[k], new_metrics[k]) for k in old_metrics),
                          action_control_flow_changed=any(a["action_control_flow_changed"] for a in slot_agents),
                          reason=";".join(sorted({a["reason"] for a in slot_agents})),
                          source_sha256=src["result_sha256"], source_path=str(path)))
        inventory.append(dict(slot_id=sid, source_path=str(path), source_sha256=src["result_sha256"], bytes=source_bytes))
        benchmark_certificates = [dict(item=item, answer=answer, answer_sha256=sha(answer.encode()), performance=value[0], evaluation_reason=value[1])
                                  for (item, answer), value in evaluator.cache.items()
                                  if item == src["item"] and any(answer in (a["old_answer"], a["new_answer"], a["new_extracted_answer"]) for a in slot_agents)]
        table_identity = package["evaluation_identity"] if package else obj.get("run", obj.get("config", {})).get("evaluation_identity", {})
        packages_out.append(dict(schema="expgym.hpo-scoring-input.v1", source=src, scalar=scalars[sid], source_path=str(path), source_bytes=source_bytes,
                                 poolact_protocol=version, oracle_reference=oracle[src["item"]], agents=projected_agents,
                                 benchmark_certificates=benchmark_certificates, evaluation_identity=table_identity,
                                 baseline_parser_sha256=old_sha,
                                 historical_parser_sha256=package["historical_parser_sha256"] if package else runtime_old_sha,
                                 parser_sha256=sha((REPO / "expgym/tool_protocol.py").read_bytes())))
    assert len(slots) == 810 and len(agents) == 1782
    assert Counter(r["system"] for r in slots) == {"expgym": 486, "poolact": 324}
    assert sha((REPO / "expgym/tool_protocol.py").read_bytes()) == parser_source_hash, "Parser changed during rescoring; rerun with frozen code"
    assert sha(Path(__file__).read_bytes()) == script_source_hash, "Rescorer changed during execution; rerun with frozen code"
    csv_write(args.output / "agent_rows.csv", agents)
    csv_write(args.output / "slot_metrics.csv", slots)
    csv_write(args.output / "affected_agents.csv", [r for r in agents if any(r[k] for k in ("answer_changed", "score_changed", "action_control_flow_changed", "extracted_answer_changed", "score_source_changed"))], list(agents[0]))
    csv_write(args.output / "affected_slots.csv", [r for r in slots if any(r[k] for k in ("answer_changed", "score_changed", "action_control_flow_changed", "extracted_answer_changed", "score_source_changed"))], list(slots[0]))
    turn_fields = [*IDENTITY, "agent_id", "call_index", "message_id", "is_terminal", "old_accepts_final", "new_accepts_final", "action_control_flow_changed", "old_payload", "new_payload", "source_sha256"]
    csv_write(args.output / "turn_parser_changes.csv", turn_changes, turn_fields)
    csv_write(args.output / "SOURCE_INVENTORY.csv", inventory)
    with (args.output / "scoring_inputs.jsonl.gz").open("wb") as raw_output:
        with gzip.GzipFile(fileobj=raw_output, mode="wb", filename="", mtime=0) as compressed:
            for package in packages_out:
                compressed.write((jdump(package) + "\n").encode())
    checks = dict(schema="expgym.hpo-protocol-rescore.v1", status="PASS", slots=len(slots), n1=486, n4=324,
                  agents=len(agents), assistant_turns_checked=total_turns, turn_payload_changes=len(turn_changes),
                  agent_answer_changes=sum(r["answer_changed"] for r in agents), agent_score_changes=sum(r["score_changed"] for r in agents),
                  terminal_payload_changes=sum(r["extracted_answer_changed"] for r in agents), score_source_changes=sum(r["score_source_changed"] for r in agents),
                  slot_score_changes=sum(r["score_changed"] for r in slots), control_flow_changed_slots=sum(r["action_control_flow_changed"] for r in slots),
                  old_scored_agents=sum(r["old_score_complete"] for r in agents), new_scored_agents=sum(r["new_score_complete"] for r in agents),
                  benchmark_verification=bool(args.verify_benchmarks and not args.inputs), unique_benchmark_evaluations=evaluator.calls,
                  saved_benchmark_certificate_verification=bool(args.inputs and args.verify_benchmarks),
                  baseline_commit=args.baseline_commit, baseline_parser_sha256=old_sha,
                  actual_runtime_parsers_used=len(runtime_parsers),
                  parser_sha256=sha((REPO / "expgym/tool_protocol.py").read_bytes()),
                  script_sha256=sha(Path(__file__).read_bytes()), oracle_sha256=sha(oracle_path.read_bytes()),
                  source_selection_sha256=sha((args.report / "SOURCE_SELECTION.csv").read_bytes()),
                  old_slot_scalars_sha256=sha((args.report / "slot_scalars.csv").read_bytes()),
                  source_hashes_verified=0 if args.inputs else len(inventory), model_calls=0,
                  replay_mode="minimal_scoring_inputs" if args.inputs else "full_immutable_trajectories",
                  benchmark_certificates_used=evaluator.certificate_uses,
                  benchmark_certificate_scope="In lightweight replay, benchmark performances are recorded data-backed measurements with configuration hashes and table/dependency identities; use full-trace --verify-benchmarks with frozen data for independent benchmark reevaluation.",
                  control_flow_audit_scope="Full mode rereads every assistant turn. Lightweight mode replays terminal scoring and preserves the previously source-hashed full-turn audit; it does not independently reexecute the full-turn audit.",
                  score_policy="legacy matching visible evaluation then best visible fallback; independent final benchmark only without visible eval_records; historical Gap0 normal no-answer zero retained",
                  limitation="Existing trace rescoring does not repair runtime graph sharing. Changed final acceptance identifies interactions needing a fresh control, not recoverable counterfactual decisions.")
    (args.output / "CHECKS.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
