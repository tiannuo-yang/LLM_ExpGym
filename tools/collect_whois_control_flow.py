#!/usr/bin/env python3
"""Verify the registered GLM beta20 control and produce a minimal public replay.

This private-source collector performs no model calls. It consumes the first
pre-registered successful execution unconditionally, including lower scores.
Portable public replay is provided by build_whois_control_flow_overlay.py.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO))
import collect_control_flow_adoption as common
import replay_control_flow_results as scorer
import build_whois_control_flow_overlay as builder
from expgym.trace_v2 import materialize_llm_input

TARGET = builder.TARGET


def collect(root, repo, output, build_report=False, plots=False):
    root, repo = root.resolve(), repo.resolve()
    out = root / "analysis/control_flow_adoption/sweep_rescore"
    out.mkdir(parents=True, exist_ok=True)
    queue = root / "operations/aux-controls/queues/glm"
    binding_path = queue / "BINDINGS.json"
    bindings = common.load(binding_path)
    plan_path = queue / "queue-plan.json"
    plan = common.load(plan_path)
    certificate_path = root / "review/search_audit_control_flow/SWEEP_GLM_CONTROL_FLOW.json"
    assert bindings["source_selection_sha256"] == common.sha(certificate_path)
    assert bindings["plan_sha256"] == common.sha(plan_path)
    assert bindings["matrix_sha256"] == common.sha(queue / "matrix.json")
    assert bindings["settings_equivalence_sha256"] == common.sha(queue / "SETTINGS_EQUIVALENCE.json")
    assert bindings["attempt"] == 1 and bindings["automatic_score_based_reruns"] is False
    assert len(bindings["jobs"]) == len(plan["jobs"]) == 1
    binding, job = bindings["jobs"][0], plan["jobs"][0]
    assert binding["old_slot_id"] == TARGET and binding["scope"] == "separate_sweep_beta20_no_main_overlap"
    assert job["job_id"] == binding["new_job_id"] == "job_" + common.digest(job["identity"])
    assert binding["output_dir"] == job["args"]["output_dir"]
    assert job["args"]["resume"] is False
    tree = plan["source_tree_sha256"]
    assert tree == bindings["source_tree_sha256"] == job["identity"]["source_tree_sha256"]
    release_path = root / "operations/aux-controls/EXECUTION_RELEASE.json"
    release = common.load(release_path)
    assert "glm" in release["models"]
    for name, expected in (("plan_sha256", common.sha(plan_path)), ("matrix_sha256", bindings["matrix_sha256"]),
                           ("bindings_sha256", common.sha(binding_path)), ("source_tree_sha256", tree)):
        assert release[name]["glm"] == expected
    completion_path = Path(plan["output_root"]) / "queue/jobs" / job["job_id"] / "completion.json"
    gate_path = root / "analysis/control_flow_adoption/SWEEP_CONTROL_GATE.json"
    if not completion_path.exists():
        gate = {"required": True, "status": "PENDING", "registered_slots": 1, "verified_slots": 0,
                "main_overlap_slots": 0, "slot_id": TARGET, "new_job_id": job["job_id"], "score_based_selection": False}
        common.write_json(gate_path, gate)
        return gate
    receipt = common.load(completion_path)
    assert receipt["mode"] == "execute" and receipt["exit_code"] == 0
    assert receipt["job_id"] == job["job_id"] and receipt["identity_sha256"] == common.digest(job["identity"])
    assert receipt["endpoint"] in job["endpoints"]
    assert receipt["artifacts"] == common.inventory(Path(binding["output_dir"]).parent), "Invocation changed after completion"
    runtime = Path(bindings["runtime_root"])
    private_job = root / "analysis/control_flow_adoption/private/job_verification" / (job["job_id"] + ".json")
    common.write_json(private_job, job)
    verification = """import json,sys; from pathlib import Path
sys.path.insert(0,sys.argv[1])
from scripts import run_study_queue as q
from expgym.trace_v2 import source_tree_sha256
j=json.loads(Path(sys.argv[2]).read_text())
assert source_tree_sha256(Path(sys.argv[1]))==j['identity']['source_tree_sha256']
q.verify_result(j,q.namespace(j['args']))
print('VERIFIED')
"""
    checked = subprocess.run([job["python"], "-c", verification, str(runtime), str(private_job)],
        cwd=runtime, env=dict(os.environ, PYTHONPATH=str(runtime), EXPGYM_DATA_ROOT=str(runtime / "data")),
        text=True, capture_output=True)
    assert checked.returncode == 0 and checked.stdout.strip().endswith("VERIFIED"), checked.stderr[-2000:]
    core = ("expgym/tool_protocol.py", "expgym/react_loop.py", "expgym/poolact.py", "expgym/extras/parallel_cache.py")
    hashes_before = {name: common.sha(repo / name) for name in core}
    runtime_hashes = {name: common.sha(runtime / name) for name in core}
    for name in core:
        if name != "expgym/react_loop.py":
            assert hashes_before[name] == runtime_hashes[name]
    # Root-approved immutable-history adapter is part of the execution release,
    # not a parser/scorer change. Bind its exact snapshot and complete tree.
    assert release["code_commit"]["glm"] == "ffca5704580b75e254f6e52dd4fe9dff104b1be8"
    assert tree == "cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02"
    assert runtime_hashes["expgym/react_loop.py"] == "80d58f390299f0551b29aae5b88a7a98a998dcb4e8ba8df37db1d53600532253"
    old_path, path = Path(binding["source_trajectory"]), Path(binding["result_path"])
    assert common.sha(old_path) == binding["source_trajectory_sha256"]
    old, new = common.load(old_path), common.load(path)
    assert new["provenance"]["repository"]["source_tree_sha256"] == tree
    for field in ("scenario", "item", "budget", "limits", "hypothesis_order"):
        assert old["task"].get(field) == new["task"].get(field), field
    assert new["task"]["scenario"] == "restricted_search"
    assert new["run"]["seed"] == old["run"]["seed"] == 2200
    assert new["run"]["model"] == old["run"]["model"]
    for field in ("temperature", "top_p", "top_k", "max_tokens", "reasoning_effort", "chat_template_kwargs"):
        assert new["run"]["generation"].get(field) == old["run"]["generation"].get(field), field
    for field in ("tool_protocol", "max_protocol_retries", "tuning_final_policy"):
        assert new["run"]["protocol"].get(field) == old["run"]["protocol"].get(field), field
    before, after = old["run"]["evaluation_identity"], new["run"]["evaluation_identity"]
    assert before["selected"] == after["selected"] and before["semantics"] == after["semantics"]
    data = []
    for name in before["files"]:
        b, a = before["files"][name], after["files"][name]
        assert all(b.get(k) == a.get(k) for k in ("present", "bytes", "sha256"))
        if a.get("present"):
            assert Path(a["path"]).stat().st_size == a["bytes"] and common.sha(Path(a["path"])) == a["sha256"]
        data.append({"role": name, "sha256": a.get("sha256"), "bytes": a.get("bytes")})
    prompts = []
    for i in (0, 1):
        assert new["messages"][i]["role"] == old["messages"][i]["role"]
        assert new["messages"][i].get("content") == old["messages"][i].get("content")
        prompts.append(common.digest(new["messages"][i].get("content")))
    outcome = new["outcome"]
    assert outcome["terminal_status"]["execution_complete"] is True
    raw = common.terminal(new, outcome, True, Path(binding["api_dump_root"]), job["job_id"])
    assert raw["message_index"] == max(i for i, m in enumerate(new["messages"]) if m["role"] == "assistant")
    assert raw["message_id"] == outcome["answer_message_id"]
    call = next(c for c in new["llm_calls"] if c["output_message_id"] == raw["message_id"])
    dump = common.load(Path(binding["api_dump_root"]) / (raw["raw_request_id"] + ".json"))
    assert dump["request_payload"]["messages"] == materialize_llm_input(new, call["id"])
    old_packages = common.read_package(root / "analysis/rescore/sweep/scoring_inputs.jsonl.gz")
    baseline = next(p for p in old_packages if p["slot_id"] == TARGET)
    assert baseline["source_sha256"] == common.sha(old_path) and not baseline["main_overlap_slot_id"]
    assert baseline["task_questions_sha256"] == after["files"]["questions"]["sha256"]
    costs_module = common.module(out / "cost_helpers.py", "_glm_control_actual_costs")
    costs = costs_module.derive_cost_rows(path, Path(binding["api_dump_root"]), model="glm", beta=20,
        job_id=job["job_id"], data_source="phantom_seed2", question_index=5,
        dump_collection="protocol_repair_aux_controls_glm_20260918",
        dump_member_prefix="api_dump", expected_trace_sha256=common.sha(path))
    assert costs["checks"]["passed"] is True
    source = {"slot_id": TARGET, "model": "glm-5.3", "members": 1, "new_job_id": job["job_id"],
        "old_result_sha256": common.sha(old_path), "result_sha256": common.sha(path), "result_bytes": path.stat().st_size,
        "result_path": common.relative(path, root), "completion_sha256": common.sha(completion_path),
        "runtime_source_tree_sha256": tree, "runtime_core_commit": scorer.CORE_COMMIT,
        "runtime_snapshot_commit": release["code_commit"]["glm"], "parser_sha256": hashes_before["expgym/tool_protocol.py"],
        "graph_sha256": runtime_hashes["expgym/extras/parallel_cache.py"], "react_loop_sha256": runtime_hashes["expgym/react_loop.py"],
        "source_layer": "new_runtime_control", "data_identities_json": common.canonical(data),
        "initial_prompt_hashes_json": common.canonical(prompts), "selection_reason": "raw_API_verified_earlier_natural_stop"}
    package = {"schema": "expgym.aux-runtime-scoring.v1", "model_alias": "glm",
        "slot": {"slot_id": TARGET, "model": "glm-5.3", "system": "expgym", "scenario": "restricted_search",
                 "regime": "custom", "strategy": "single", "item": "phantom_seed2:5", "seed": "2200", "beta": 20,
                 "metrics_json": common.canonical(baseline["old_metrics"])},
        "legacy_metrics": baseline["old_metrics"], "gold": {"answers": baseline["gold_answers"]},
        "agents": [{"agent_id": -1, "terminal": raw, "allow_unlabelled": True,
                    "saved_answer": outcome.get("answer"), "saved_metrics": {"f1": outcome["score"]["value"]},
                    "saved_perf": outcome["score"]["value"], "tool_records": [],
                    "legacy_metrics": baseline["old_metrics"], "existing_trace_rescored_metrics": baseline["old_metrics"]}],
        "source": source, "saved_aggregate": None, "whois_costs": costs}
    scorer.score_slot(package)
    inputs = out / "scoring_inputs.jsonl.gz"
    common.write_package(inputs, [package])
    replay = scorer.replay([package], out)
    common.write_csv(out / "actual_agents.csv", [costs["agent_row"]])
    common.write_csv(out / "actual_attempts.csv", costs["attempt_rows"])
    common.write_json(out / "COST_CHECKS.json", costs["checks"])
    assert hashes_before == {name: common.sha(repo / name) for name in core}
    checks = {"passed": True, "registered_slots": 1, "verified_slots": 1, "main_overlap_slots": 0,
        "first_registered_execution": True, "score_based_selection": False, "model_calls_by_collector": 0,
        "raw_terminal_input_exactly_reconstructed": True, "completion_inventory_exact": True,
        "task_settings_initial_prompts_preserved": True, "actual_new_costs_recomputed": True,
        "source": source, "code_sha256": hashes_before, "runtime_code_sha256": runtime_hashes,
        "runtime_adapter": "release-bound immutable-history admission adapter; parser/poolact/graph match frozen core exactly",
        "code_unchanged_during_scoring": True,
        "bindings_sha256": common.sha(binding_path), "plan_sha256": common.sha(plan_path),
        "execution_release_sha256": common.sha(release_path), "qualification_sha256": common.sha(certificate_path),
        "scoring_inputs_sha256": common.sha(inputs), "replay": replay}
    common.write_json(out / "COLLECTION_CHECKS.json", checks)
    (out / "README.zh.md").write_text("# Whois 独立运行控制\n\n仅包含预注册 GLM β20、phantom_seed2:5、seed2200 的首次完整新运行。无条件采用其分数与实际成本，不按高分筛选。其与主实验 β10 不重复。\n\n`scoring_inputs.jsonl.gz` 可用 `tools/replay_control_flow_results.py` 真正重提取终答并重评分；其中只保留终答、任务 gold、终端资格、哈希和成本标量。实际成本由新 trajectory 和全部 API attempt 核验后导出，不含 HTTP 内容或 reasoning。\n\n`actual_agents.csv`、`actual_attempts.csv` 包含全部实际重试、工具次数、时长与未知 usage；`COLLECTION_CHECKS.json`、`COST_CHECKS.json` 记录来源验证。\n")
    report = builder.build_overlay(root / "analysis/whois/final", root / "analysis/rescore/sweep", inputs, output, plots) if build_report else None
    gate = {"required": True, "status": "PASS" if report else "VERIFIED_AWAITING_REPORT", "registered_slots": 1,
        "verified_slots": 1, "main_overlap_slots": 0, "slot_id": TARGET, "new_job_id": job["job_id"],
        "new_result_sha256": common.sha(path), "old_result_sha256": common.sha(old_path),
        "scoring_inputs_sha256": common.sha(inputs), "source_checks_sha256": common.sha(out / "COLLECTION_CHECKS.json"),
        "actual_cost_ledger_verified_slots": 1, "score_based_selection": False,
        "official_report_slots": report["slots"] if report else 0,
        "official_scalar_sha256": common.sha(output / "slot_scalars.csv") if report else None,
        "official_checks_sha256": common.sha(output / "CHECKS.json") if report else None,
        "new_runtime_f1": outcome["score"]["value"], "runtime_core_commit": scorer.CORE_COMMIT,
        "parser_sha256": hashes_before["expgym/tool_protocol.py"]}
    common.write_json(gate_path, gate)
    return gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-report", action="store_true")
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    print(json.dumps(collect(args.repair_root, args.repo, args.output, args.build_report, args.plots), indent=2))


if __name__ == "__main__":
    main()
