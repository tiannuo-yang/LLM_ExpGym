#!/usr/bin/env python3
"""Collect pre-registered whole Search/Audit controls and gate total adoption.

The existing-trace rescoring release is immutable. New scores replace complete
registered invocations only after receipt, source, configuration, terminal API,
parser and scorer checks. Global adoption additionally requires the HPO97 gate.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path


def load(path):
    return json.loads(path.read_text())


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected regular artifact: " + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    temporary.replace(path)


def read_package(path):
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_package(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as handle:
            for row in rows:
                handle.write((canonical(row) + "\n").encode())


def inventory(path):
    return {p.relative_to(path).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)}
            for p in sorted(path.rglob("*")) if p.is_file()}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def relative(path, root):
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def terminal(obj, agent, n1, dump_root, job_id):
    messages = obj["messages"] if n1 else agent["messages"]
    candidates = [(i, m) for i, m in enumerate(messages) if m.get("role") == "assistant"]
    assert candidates, "No terminal assistant message"
    pointer = agent.get("answer_message_id") if n1 else None
    selected = [(i, m) for i, m in candidates if m.get("id") == pointer] if pointer else candidates[-1:]
    assert len(selected) == 1
    index, message = selected[0]
    if n1:
        calls = [c for c in obj["llm_calls"] if c["output_message_id"] == message["id"]]
        assert len(calls) == 1
        call = calls[0]; attempt = call["attempt_usage"][-1]
        api = obj["run"]["api_dump"]
    else:
        ordinal = next(i for i, (mid, _) in enumerate(candidates, 1) if mid == index)
        calls = [c for c in agent["usage_attempts"] if c["llm_call_index"] == ordinal]
        assert len(calls) == 1
        call = calls[0]; attempt = call["attempts"][-1]
        api = agent["api_dump"]
    request_id = attempt["request_id"]
    path = dump_root / (request_id + ".json")
    raw = load(path)
    assert raw["request_id"] == request_id and raw["client_id"] == api["client_id"]
    assert api["run_id"] == raw["run_id"] == job_id
    assert raw["generation_id"] == attempt["generation_id"]
    assert raw["state"] == attempt["state"] == "success"
    response = raw["response_json"]["choices"][0]
    output = response["message"]
    if n1:
        assert call.get("finish_reason") == response.get("finish_reason")
    assert output.get("content") == message.get("content")
    assert output.get("tool_calls") == message.get("tool_calls")
    if not n1:
        assert raw["context"]["agent_id"] == agent["agent_id"]
    prompt = next((m.get("content", "") for m in reversed(raw["request_payload"]["messages"]) if m.get("role") == "user"), "")
    forced = "System: Loop aborted (" in prompt and "Respond immediately with Answer:" in prompt
    if n1:
        assert forced == call["forced"]
    return {"content": output.get("content") or "", "finish_reason": response.get("finish_reason"),
            "native_tool_calls_present": bool(output.get("tool_calls")), "forced": forced,
            "api_state": raw["state"], "raw_request_id": request_id, "raw_dump_sha256": sha(path),
            "raw_generation_id": raw["generation_id"], "raw_run_id": raw["run_id"],
            "message_index": index, "message_id": message.get("id")}


def config_checks(old, new, row, job, tree):
    n1 = row["system"] == "expgym"
    if n1:
        assert new["provenance"]["repository"]["source_tree_sha256"] == tree
        assert new["task"]["scenario"] == old["task"]["scenario"] == row["scenario"]
        assert new["task"]["item"] == old["task"]["item"]
        assert new["task"]["hypothesis_order"] == old["task"]["hypothesis_order"]
        old_budget, new_budget = old["task"]["budget"], new["task"]["budget"]
        assert all(new_budget.get(k) == v for k, v in old_budget.items()), "Historical budget semantics changed"
        assert set(new_budget) - set(old_budget) <= {"beta"}, "Unexpected added budget field"
        if "beta" in new_budget:
            expected_beta = None if new_budget["limit_seconds"] is None else new_budget["limit_seconds"] / new_budget["base_cost_seconds"]
            assert new_budget["beta"] == expected_beta, "Explicit beta disagrees with budget seconds"
        assert new["task"]["limits"] == old["task"]["limits"]
        assert new["run"]["seed"] == old["run"]["seed"] == int(row["seed"])
        assert new["run"]["model"] == old["run"]["model"]
        for key in ("temperature", "top_p", "top_k", "max_tokens", "reasoning_effort", "chat_template_kwargs"):
            assert new["run"]["generation"].get(key) == old["run"]["generation"].get(key), (key, "generation changed")
        for key in ("tool_protocol", "max_protocol_retries", "tuning_final_policy"):
            assert new["run"]["protocol"].get(key) == old["run"]["protocol"].get(key)
        new_identity, old_identity = new["run"]["evaluation_identity"], old["run"]["evaluation_identity"]
        old_members, new_members = [old], [new]
    else:
        assert new["implementation_sha256"] == {"source_tree": tree}
        assert new["config"]["poolact_protocol"] == "paper-graph-lock-v4"
        assert new["strategy"] == row["strategy"] and new["agents"] == 4
        assert [a["agent_id"] for a in new["agent_results"]] == [0, 1, 2, 3]
        assert [a["seed"] for a in new["agent_results"]] == list(range(int(row["seed"]), int(row["seed"]) + 4))
        assert len({a["api_dump"]["client_id"] for a in new["agent_results"]}) == 4
        fields = ("scenario", "question_index", "data_source", "cc_split", "cost_regime", "time_budget", "agents", "seed", "temperature", "max_tokens", "top_p", "top_k", "chat_template_kwargs", "reasoning_effort", "tool_protocol", "max_protocol_retries", "tuning_final_policy", "max_steps", "max_evals", "max_context_tokens", "missing_final_policy", "model", "backend")
        for key in fields:
            assert new["config"].get(key) == old["config"].get(key), (row["slot_id"], key, "preserved setting changed")
        new_identity, old_identity = new["config"]["evaluation_identity"], old["config"]["evaluation_identity"]
        old_members, new_members = old["agent_results"], new["agent_results"]
    assert new_identity["selected"] == old_identity["selected"]
    assert new_identity["semantics"] == old_identity["semantics"]
    data = []
    for key in ("questions", "corpus", "evidence", "hints"):
        if key not in old_identity["files"]:
            continue
        before, after = old_identity["files"][key], new_identity["files"][key]
        assert all(before.get(k) == after.get(k) for k in ("present", "bytes", "sha256"))
        if after.get("present"):
            path = Path(after["path"])
            assert path.stat().st_size == after["bytes"] and hashlib.sha256(path.read_bytes()).hexdigest() == after["sha256"]
        data.append({"role": key, "sha256": after.get("sha256"), "bytes": after.get("bytes")})
    prompt_checks = []
    for old_member, new_member in zip(old_members, new_members):
        for position in (0, 1):
            before, after = old_member["messages"][position], new_member["messages"][position]
            assert before["role"] == after["role"]
            before_text, after_text = before.get("content"), after.get("content")
            dynamic = False
            if not n1 and row["strategy"] == "poolact" and position == 1:
                # Later agents can begin after another agent posts a claim.
                # Compare the complete static task and shared-state header,
                # while binding the dynamic suffix to this run's actual API.
                aid = new_member["agent_id"]
                marker = "\n\n[Parallel Exploration — Agent {} of 4]\n".format(aid)
                assert before_text.count(marker) <= 1 and after_text.count(marker) <= 1, "Ambiguous initial graph boundary"
                old_prefix, _, old_graph = before_text.partition(marker)
                new_prefix, _, new_graph = after_text.partition(marker)
                assert old_prefix == new_prefix, (row["slot_id"], aid, "static task prompt changed")
                section = "\n== In Progress ==\n"
                expected_header = "You are one of 4 agents solving this task in parallel.\nShared state below shows what other agents have explored and are exploring.\nUse this to plan your next action — prioritize paths not yet explored.\n"
                for graph in (old_graph, new_graph):
                    if graph:
                        assert section in graph and graph.split(section, 1)[0] == expected_header, "Shared-state instructions changed"
                dynamic = old_graph != new_graph
                static_hash = digest(new_prefix)
            else:
                assert before_text == after_text, (row["slot_id"], position, "static initial prompt changed")
                static_hash = digest(after_text)
            prompt_checks.append({"agent_id": -1 if n1 else new_member["agent_id"], "position": position,
                                  "static_sha256": static_hash, "old_full_sha256": digest(before_text),
                                  "new_full_sha256": digest(after_text), "dynamic_shared_state_changed": dynamic})
    return data, prompt_checks


def collect_one(row, binding, job, plan, old_package, original_path, runtime, repo, root, scorer, release):
    sid = row["slot_id"]
    output = Path(binding["output_dir"])
    completion_path = Path(plan["output_root"]) / "queue/jobs" / job["job_id"] / "completion.json"
    if not completion_path.exists():
        return None
    assert release, "Completed auxiliary invocation has no frozen execution release"
    completion = load(completion_path)
    assert completion["mode"] == "execute" and completion["exit_code"] == 0
    assert completion["job_id"] == job["job_id"] == "job_" + digest(job["identity"])
    assert completion["identity_sha256"] == digest(job["identity"])
    assert completion["endpoint"] in job["endpoints"]
    assert completion["artifacts"] == inventory(output.parent), "Completed invocation changed"
    if row["system"] == "poolact":
        path = output / row["strategy"] / "result.json"
    else:
        paths = list(output.rglob("traces-v2/*.json"))
        assert len(paths) == 1, "Exactly one N1 result is required"
        path = paths[0]
    obj = load(path); old = load(original_path)
    assert sha(original_path) == row["trajectory_sha256"]
    tree = plan["source_tree_sha256"]
    assert tree == job["identity"]["source_tree_sha256"]
    # Different historical prompt restorations share the frozen scientific
    # core. Run the production artifact verifier in a fresh interpreter rooted
    # at this job's snapshot, so Python's module cache cannot substitute another
    # model's task/prompt implementation.
    verification_job = root / "analysis/control_flow_adoption/private/job_verification" / (job["job_id"] + ".json")
    write_json(verification_job, job)
    verify_code = """import json,sys; from pathlib import Path
sys.path.insert(0,sys.argv[1])
from scripts import run_study_queue as q
from expgym.trace_v2 import source_tree_sha256
j=json.loads(Path(sys.argv[2]).read_text())
assert source_tree_sha256(Path(sys.argv[1]))==j['identity']['source_tree_sha256']
q.verify_result(j,q.namespace(j['args']))
print('VERIFIED')
"""
    environment = dict(os.environ, PYTHONPATH=str(runtime), EXPGYM_DATA_ROOT=str(runtime / "data"))
    checked = subprocess.run([job["python"], "-c", verify_code, str(runtime), str(verification_job)],
                             cwd=runtime, env=environment, text=True, capture_output=True)
    assert checked.returncode == 0 and checked.stdout.strip().endswith("VERIFIED"), "Production artifact verification failed: " + checked.stderr[-2000:]
    # The approved ffca transport snapshot additionally preserves signed
    # histories for immutable-history providers. Its complete source tree was
    # verified above against the execution release; parser/voter/graph must
    # still be byte-identical to the scientific repair core.
    for core_file in ("expgym/tool_protocol.py", "expgym/poolact.py", "expgym/extras/parallel_cache.py"):
        assert sha(runtime / core_file) == sha(repo / core_file), "Frozen scientific code differs: " + core_file
    data, prompts = config_checks(old, obj, row, job, tree)
    n1 = row["system"] == "expgym"
    members = [obj["outcome"]] if n1 else obj["agent_results"]
    # Prove every complete initial prompt, including its dynamic graph state,
    # was actually sent in this invocation rather than accepting an arbitrary
    # suffix in a derived transcript.
    for member in ([obj] if n1 else members):
        if n1:
            initial_attempt = member["llm_calls"][0]["attempt_usage"][-1]
            api_identity = member["run"]["api_dump"]
        else:
            initial_attempt = member["usage_attempts"][0]["attempts"][-1]
            api_identity = member["api_dump"]
        first_raw = load(output.parent / "api_dump" / (initial_attempt["request_id"] + ".json"))
        assert first_raw["request_id"] == initial_attempt["request_id"]
        assert first_raw["client_id"] == api_identity["client_id"]
        assert first_raw["run_id"] == job["job_id"]
        for position in (0, 1):
            actual, saved = first_raw["request_payload"]["messages"][position], member["messages"][position]
            assert actual["role"] == saved["role"] and actual.get("content") == saved.get("content"), "Initial prompt differs from original API request"
    assert (obj["outcome"] if n1 else obj)["terminal_status"]["execution_complete"] is True
    old_by = {a["agent_id"]: a for a in old_package["agents"]}
    agents = []
    for a in members:
        aid = -1 if n1 else a["agent_id"]
        raw = terminal(obj, a, n1, output.parent / "api_dump", job["job_id"])
        if n1:
            records = [[c["name"], c.get("raw_arguments", canonical(c.get("arguments", {}))), c.get("tool_result")] for c in obj.get("tool_calls", [])]
            perf = a["score"].get("value")
            metrics = a["score"].get("metrics")
            if row["scenario"] == "evidence_audit":
                perf = metrics[a["score"].get("primary_metric", "label_acc")]
        else:
            records = a["tool_records"]
            perf, metrics = a.get("answer_perf"), a.get("answer_metrics")
        assert a["terminal_status"]["execution_complete"] is True
        saved_metrics = metrics if row["scenario"] == "evidence_audit" else {"f1": perf}
        agents.append({"agent_id": aid, "terminal": raw, "allow_unlabelled": True,
                       "saved_answer": a.get("answer"), "saved_metrics": saved_metrics, "saved_perf": perf,
                       "tool_records": records if row["scenario"] == "evidence_audit" else [],
                       "legacy_metrics": old_by[aid]["old_answer_metrics"] if row["scenario"] == "evidence_audit" else {"f1": old_by[aid]["old_answer_perf"]},
                       "existing_trace_rescored_metrics": old_by[aid].get("rescored_metrics")})
    source = {"slot_id": sid, "model": row["model"], "members": len(agents), "new_job_id": job["job_id"],
              "old_result_sha256": row["trajectory_sha256"], "result_sha256": sha(path), "result_bytes": path.stat().st_size,
              "result_path": relative(path, root), "completion_sha256": sha(completion_path),
              "runtime_source_tree_sha256": tree, "runtime_core_commit": scorer.CORE_COMMIT,
              "runtime_snapshot_commit": release["code_commit"][binding["model_alias"]],
              "parser_sha256": sha(runtime / "expgym/tool_protocol.py"), "graph_sha256": sha(runtime / "expgym/extras/parallel_cache.py"),
              "react_loop_sha256": sha(runtime / "expgym/react_loop.py"),
              "source_layer": "new_runtime_control", "config_identity_sha256": digest(obj["run"] if n1 else obj["config"]),
              "data_identities_json": canonical(data), "initial_prompt_hashes_json": canonical(prompts), "selection_reason": row["selection_reason"]}
    package = {"schema": "expgym.aux-runtime-scoring.v1", "model_alias": "deepseek" if row["model"].startswith("deepseek") else "qwen",
               "slot": old_package["slot"], "legacy_metrics": old_package["legacy_slot_metrics"], "gold": old_package["gold"],
               "agents": agents, "source": source,
               "saved_aggregate": None if n1 else {k: obj["aggregate"].get(k) for k in ("answer", "answer_perf", "answer_metrics")}}
    scorer.score_slot(package)
    return package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    root, repo = args.repair_root.resolve(), args.repo.resolve()
    out = root / "analysis/control_flow_adoption"; out.mkdir(parents=True, exist_ok=True)
    selected_path = root / "review/search_audit_control_flow/AFFECTED_WHOLE_SLOTS.csv"
    wanted = {r["slot_id"]: r for r in read_csv(selected_path)}
    assert len(wanted) == 21 and sum(int(r["N"]) for r in wanted.values()) == 78
    original_sources = {r["slot_id"]: r for r in load(root / "analysis/rescore/resolved_sources.json")}
    baseline = read_csv(root / "analysis/rescore/main/slot_scalars.csv")
    baseline_by = {r["slot_id"]: r for r in baseline}
    old_packages = {r["slot"]["slot_id"]: r for r in read_package(root / "analysis/rescore/search_audit/scoring_inputs.jsonl.gz")}
    old_members = {(r["slot_id"], int(r["agent_id"])): r for r in read_csv(root / "analysis/rescore/search_audit/agent_rows.csv")}
    for sid in wanted:
        package = old_packages[sid]
        package["legacy_slot_metrics"] = json.loads(package["slot"]["metrics_json"])
        package["slot"] = baseline_by[sid]
        for agent in package["agents"]:
            agent["rescored_metrics"] = json.loads(old_members[sid, agent["agent_id"]]["new_metrics_json"])
    scorer = module(repo / "tools/replay_control_flow_results.py", "_aux_public_scorer")
    release_path = root / "operations/aux-controls/EXECUTION_RELEASE.json"
    release = load(release_path) if release_path.exists() else None
    bindings, binding_records, errors = {}, [], []
    for directory in sorted((root / "operations/aux-controls/queues").glob("*")):
        if not directory.is_dir() or not (directory / "BINDINGS.json").exists():
            continue
        binding_manifest = load(directory / "BINDINGS.json")
        if not any(b.get("old_slot_id", b.get("slot_id")) in wanted for b in binding_manifest["jobs"]):
            continue  # Separate sweep registration is verified by its own gate.
        plan_path = directory / "queue-plan.json"; plan = load(plan_path)
        assert binding_manifest["plan_sha256"] == sha(plan_path)
        assert binding_manifest["matrix_sha256"] == sha(directory / "matrix.json")
        assert binding_manifest["source_selection_sha256"] == sha(selected_path)
        assert binding_manifest["automatic_score_based_reruns"] is False and binding_manifest["attempt"] == 1
        assert binding_manifest["source_tree_sha256"] == plan["source_tree_sha256"]
        if release:
            assert directory.name in release["models"]
            assert release["plan_sha256"][directory.name] == sha(plan_path)
            assert release["matrix_sha256"][directory.name] == binding_manifest["matrix_sha256"]
            assert release["bindings_sha256"][directory.name] == sha(directory / "BINDINGS.json")
            assert release["source_tree_sha256"][directory.name] == plan["source_tree_sha256"]
        jobs = {j["job_id"]: j for j in plan["jobs"]}
        runtime = Path(binding_manifest.get("runtime_root", binding_manifest.get("runtime", plan.get("repo", ""))))
        if not runtime.is_absolute():
            runtime = root / runtime
        for b in binding_manifest["jobs"]:
            sid = b.get("old_slot_id", b.get("slot_id"))
            if sid not in wanted:
                continue  # A separately registered sweep control is gated below.
            assert sid not in bindings
            job = jobs[b["new_job_id"]]
            assert job["job_id"] == "job_" + digest(job["identity"])
            assert b["output_dir"] == job["args"]["output_dir"]
            assert b.get("source_trajectory_sha256", wanted[sid]["trajectory_sha256"]) == wanted[sid]["trajectory_sha256"]
            assert job["args"]["resume"] is False
            bindings[sid] = (b, job, plan, runtime)
        binding_records.append({"model_alias": directory.name, "binding_sha256": sha(directory / "BINDINGS.json"), "plan_sha256": sha(plan_path), "runtime_source_tree_sha256": plan["source_tree_sha256"]})
    statuses, packages = [], []
    for sid, row in sorted(wanted.items()):
        state = {"slot_id": sid, "model": row["model"], "system": row["system"], "scenario": row["scenario"], "state": "awaiting_binding", "new_job_id": "", "error": ""}
        if sid in bindings:
            b, job, plan, runtime = bindings[sid]; state.update(state="awaiting_completion", new_job_id=job["job_id"])
            try:
                package = collect_one(row, b, job, plan, old_packages[sid], Path(original_sources[sid]["source_path"]), runtime, repo, root, scorer, release)
                if package is not None:
                    packages.append(package); state["state"] = "verified_complete"
            except Exception as exc:
                state.update(state="validation_failed", error=type(exc).__name__ + ": " + str(exc)); errors.append(dict(state))
        statuses.append(state)
    progress = out / "progress"; write_csv(progress / "STATUS.csv", statuses)
    aux = out / "aux_rescore"
    write_package(aux / "scoring_inputs.jsonl.gz", packages)
    if packages:
        scorer.replay(packages, aux)
    hpo_path = root / "analysis/rerun_adoption/FAIRNESS_MANIFEST.json"
    hpo = load(hpo_path) if hpo_path.exists() else {}
    hpo_ready = hpo.get("status") == "PASS" and hpo.get("adoption_ready") is True and hpo.get("verified_complete_pools") == 97
    aux_ready = len(packages) == 21 and not errors
    # A qualified extra sweep control, when registered, is never silently
    # omitted from the global completion gate.
    sweep_gate_path = out / "SWEEP_CONTROL_GATE.json"
    sweep_gate = load(sweep_gate_path) if sweep_gate_path.exists() else {"required": False, "status": "NOT_REGISTERED", "registered_slots": 0, "verified_slots": 0}
    sweep_ready = not sweep_gate.get("required") or (sweep_gate.get("status") == "PASS" and sweep_gate.get("verified_slots") == sweep_gate.get("registered_slots"))
    ready = hpo_ready and aux_ready and sweep_ready
    manifest = {"schema": "expgym.total-runtime-adoption.v1", "status": "PASS" if ready else "INCOMPLETE", "adoption_ready": ready,
                "total_main_runtime_adoption": True, "main_slots": 4698, "hpo_verified_pools": hpo.get("verified_complete_pools", 0),
                "hpo_required_pools": 97, "auxiliary_verified_main_slots": len(packages), "auxiliary_required_main_slots": 21,
                "auxiliary_verified_members": sum(len(p["agents"]) for p in packages), "auxiliary_required_members": 78,
                "sweep_additional_slots": sweep_gate.get("registered_slots", 0), "sweep_control_gate": sweep_gate,
                "hpo_stage_ready": hpo_ready, "auxiliary_stage_ready": aux_ready, "status_counts": dict(Counter(r["state"] for r in statuses)),
                "hpo_stage_manifest_sha256": sha(hpo_path) if hpo_path.exists() else None,
                "runtime_core_commit": scorer.CORE_COMMIT, "runtime_snapshot_commit": hpo.get("runtime_snapshot_commit"),
                "auxiliary_runtime_snapshot_commits": release.get("code_commit", {}) if release else {},
                "auxiliary_execution_release_sha256": sha(release_path) if release_path.exists() else None,
                "runtime_source_trees": sorted({p["source"]["runtime_source_tree_sha256"] for p in packages}), "bindings": binding_records,
                "parser_sha256": sha(repo / "expgym/tool_protocol.py"), "graph_sha256": sha(repo / "expgym/extras/parallel_cache.py"),
                "code_sha256": {p: sha(repo / p) for p in scorer.CODE_FILES}, "core_repair_commit": scorer.CORE_COMMIT,
                "selection_csv_sha256": sha(selected_path), "collector_sha256": sha(Path(__file__)), "replay_script_sha256": sha(repo / "tools/replay_control_flow_results.py"),
                "base_input_sha256": {"legacy_scalars": sha(repo / "results/gemini-openrouter-20260917/main/slot_scalars.csv"),
                                      "rescored_scalars": sha(root / "analysis/rescore/main/slot_scalars.csv"),
                                      "source_selection": sha(root / "analysis/rescore/main/SOURCE_SELECTION.csv")},
                "public_aux_scoring_inputs_sha256": sha(aux / "scoring_inputs.jsonl.gz"), "errors": errors,
                "selection_policy": "All pre-registered whole invocations; no score-based selection, no member splicing.", "model_calls": 0}
    if ready:
        hpo_official = root / "analysis/rerun_adoption/new_official"
        stage = read_csv(hpo_official / "slot_scalars.csv"); selected = read_csv(hpo_official / "SOURCE_SELECTION.csv")
        assert sha(hpo_official / "slot_scalars.csv") == hpo["official_slot_scalars_sha256"]
        assert sha(hpo_official / "SOURCE_SELECTION.csv") == hpo["official_source_selection_sha256"]
        replacements = {r["slot_id"]: r for r in read_csv(aux / "slot_scalars.csv")}
        new_sources = {r["slot_id"]: r for r in read_csv(aux / "SOURCE_INVENTORY.csv")}
        merged = [replacements.get(r["slot_id"], r) for r in stage]
        assert len(merged) == 4698 and len(replacements) == 21
        assert sum(r["slot_id"] not in replacements and r == stage[i] for i, r in enumerate(merged)) == 4677
        for row in selected:
            sid = row["slot_id"]
            if sid in replacements:
                source, scalar = new_sources[sid], replacements[sid]
                row.update(old_result_sha256=row["result_sha256"], old_historical_trajectory=row.get("historical_trajectory", ""), old_new_result_index=row.get("new_result_index", ""),
                           result_sha256=source["result_sha256"], cohort_id=scalar["cohort_id"], provider=scalar["provider_cohort"],
                           selection="new_runtime_terminal_protocol_control", historical_trajectory="", new_result_index="",
                           new_result_path=source["result_path"], new_job_id=source["new_job_id"], runtime_source_tree_sha256=source["runtime_source_tree_sha256"],
                           runtime_core_commit=source["runtime_core_commit"], runtime_snapshot_commit=source["runtime_snapshot_commit"], execution_complete=scalar["execution_complete"], score_complete=scalar["score_complete"])
        official = out / "new_official"; write_csv(official / "slot_scalars.csv", merged, list(stage[0])); write_csv(official / "SOURCE_SELECTION.csv", selected)
        write_csv(official / "auxiliary_slot_diff.csv", read_csv(aux / "sample_diff.csv"))
        legacy = {r["slot_id"]: r for r in read_csv(repo / "results/gemini-openrouter-20260917/main/slot_scalars.csv")}
        selected_by = {r["slot_id"]: r for r in selected}
        final_diffs = []
        for row in merged:
            sid = row["slot_id"]; original = original_sources[sid]; adopted = selected_by[sid]
            before, middle, after = [json.loads(r["metrics_json"]) for r in (legacy[sid], baseline_by[sid], row)]
            final_diffs.append({**{k: row[k] for k in ("slot_id", "model", "system", "scenario", "regime", "strategy", "item", "outer_repeat", "order", "seed")},
                                "legacy_metrics_json": canonical(before), "existing_trace_rescored_metrics_json": canonical(middle),
                                "new_official_metrics_json": canonical(after), "changed_from_legacy": not scorer.same(before, after),
                                "changed_from_existing_trace_rescore": not scorer.same(middle, after),
                                "legacy_source_sha256": original["result_sha256"], "adopted_source_sha256": adopted["result_sha256"],
                                "source_changed": original["result_sha256"] != adopted["result_sha256"],
                                "adoption_reason": "terminal_protocol_runtime_control" if sid in replacements else "hpo_graph_runtime_control" if adopted.get("new_result_path") else "retained_existing_trace_rescore"})
        write_csv(official / "sample_diff.csv", final_diffs)
        private = official / "private"; private.mkdir(exist_ok=True)
        resolved = []
        for row in selected:
            sid = row["slot_id"]; old = original_sources[sid]
            path = str(root / row["new_result_path"]) if row.get("new_result_path") else old["source_path"]
            resolved.append(dict(row, source_path=path, source_sha256=row["result_sha256"], historical_source_path=old["source_path"], historical_source_sha256=old["result_sha256"], source_origin="new_runtime_control" if row.get("new_result_path") else "existing_trace_rescored"))
        write_json(private / "resolved_sources.json", resolved)
        old_overlays = [json.loads(line) for line in (root / "analysis/rescore/search_audit/private/answer_overlays.jsonl").read_text().splitlines()]
        new_overlays = [json.loads(line) for line in (aux / "private/answer_overlays.jsonl").read_text().splitlines()]
        all_overlays = [r for r in old_overlays if r["slot_id"] not in replacements] + new_overlays
        source_by = {r["slot_id"]: r for r in resolved}
        for row in all_overlays:
            source = source_by[row["slot_id"]]
            row.update(source_path=source["source_path"], source_sha256=source["source_sha256"], historical_source_sha256=source["historical_source_sha256"], source_origin=source["source_origin"])
        (private / "answer_overlays.jsonl").write_text("".join(canonical(r) + "\n" for r in all_overlays))
        manifest.update(official_slot_scalars_sha256=sha(official / "slot_scalars.csv"), official_source_selection_sha256=sha(official / "SOURCE_SELECTION.csv"),
                        official_sample_diff_sha256=sha(official / "sample_diff.csv"),
                        replaced_main_slots=118, retained_existing_trace_slots=4580, official_strict_score_complete=sum(str(r["score_complete"]).lower() == "true" for r in merged))
        write_json(official / "CHECKS.json", manifest)
    elif (out / "new_official").exists():
        target = out / "invalidated_official" / str(time.time_ns()); target.parent.mkdir(parents=True, exist_ok=True)
        (out / "new_official").rename(target)
    write_json(out / "FAIRNESS_MANIFEST.json", manifest)
    print(json.dumps({k: manifest[k] for k in ("status", "adoption_ready", "hpo_verified_pools", "auxiliary_verified_main_slots", "status_counts")}, indent=2))
    if args.require_complete and not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
