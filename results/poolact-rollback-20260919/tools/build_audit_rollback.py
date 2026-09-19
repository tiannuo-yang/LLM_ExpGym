#!/usr/bin/env python3
"""Build the explicitly hybrid Audit report from immutable public leaf tables.

Keep all 702 adopted N1 traces from 7776f70; restore all 468 N4 pools and
1,872 members to the pre-repair scoring/source layer. No model or scorer runs.
"""
import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

SCHEMA = "expgym.audit-n4-rollback.v1"
SOURCE_COMMIT = "7776f700902db194c69124b1a5f59d985379cfb3"
SOURCE_REL = Path("results/protocol-repair-20260918/audit")
PINNED_INPUTS = {
    "n1/trace_metrics.csv": "6392a2e3cae19b91b22ac2cbe6ffeaf0a57a2c3738d2aac5e70cd42cd0abb3df",
    "n1/hypothesis_metrics.csv": "ac4dc13be5be1d6c5bc9f731b4c482b7edb79fb89c0f6c47fd2192cd51dedaaf",
    "old/n1/trace_metrics.csv": "fb9a329b4ad3f9c50c6ddca12deee4d0b6d9fd1b9d06aefb09b0b0269622f7d7",
    "old/n1/hypothesis_metrics.csv": "989578a94ba588d3359f12d130e811bb0c9f5138b7e799f728b1d32d170b1688",
    "old/coordination/audit_pools.csv": "1f916f5e0fd9ae0bc3f1b298d6ca6bac44dbe9dbbdaf45bb8269cb997babe58d",
    "old/coordination/audit_agents.csv": "8b4466c78887338e095d332411354eb02a5ffe1e524809eeab8be395c7fdc3f5",
    "recompute_audit.py": "d1dea43e8b6aec321263d02d969ccb8a19016aea7b39f861c7b12033238b5180",
    "_historical_n1.py": "e01bbc4222fe72510c638314739ff195eb7ae3a0f722da2724f2e72a311cc1db",
    "_historical_coordination.py": "d0ba3fd868852565d3957d1f8e3deca2848ac5b34e532aa1438a592b56bab95c",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def require(ok, details):
    if not ok:
        raise AssertionError(details)


def module(path):
    spec = importlib.util.spec_from_file_location("audit_rollback_aggregation", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def expected_inputs(repo):
    current = repo / "results/protocol-repair-20260918/main"
    historical = repo / "results/gemini-openrouter-20260917/main"
    expected = {}
    for filename in ("slot_scalars.csv", "SOURCE_SELECTION.csv"):
        current_rows = load_csv(current / filename)
        old_rows = load_csv(historical / filename)
        rows = [r for r in current_rows if r["system"] == "expgym"]
        rows += [r for r in old_rows if r["system"] == "poolact"]
        expected[filename] = {r["slot_id"]: r for r in rows
                              if r["scenario"] == "evidence_audit"}
        require(len(expected[filename]) == 1170, filename)
    return expected


def check_main(repo, new, scalars_path, selection_path):
    expected = expected_inputs(repo)
    scalar = {r["slot_id"]: r for r in load_csv(scalars_path)
              if r["scenario"] == "evidence_audit"}
    selection = {r["slot_id"]: r for r in load_csv(selection_path)
                 if r["scenario"] == "evidence_audit"}
    leaves = {r["slot_id"]: r for r in new["traces"] + new["pools"]}
    require(scalar.keys() == selection.keys() == leaves.keys()
            == expected["slot_scalars.csv"].keys(), "Audit cohort mismatch")
    source_rows = []
    for slot_id, leaf in sorted(leaves.items()):
        score = scalar[slot_id]
        source = selection[slot_id]
        before = expected["slot_scalars.csv"][slot_id]
        source_before = expected["SOURCE_SELECTION.csv"][slot_id]
        require(source["result_sha256"] == source_before["result_sha256"]
                == leaf["source_sha256"], (slot_id, "source hash"))
        require(score["system"] == source["system"] == before["system"],
                (slot_id, "system"))
        for key in ("model", "regime", "strategy", "item", "order", "outer_repeat"):
            require(score[key] == source[key] == before[key], (slot_id, key))
        metrics = json.loads(score["metrics_json"])
        expected_metrics = json.loads(before["metrics_json"])
        require(metrics == expected_metrics, (slot_id, "main metrics changed"))
        for metric in ("label_acc", "evidence_acc"):
            scalar_key = metric if score["system"] == "expgym" else metric + "_mv"
            require(math.isclose(leaf[metric], metrics[scalar_key], abs_tol=1e-12),
                    (slot_id, scalar_key, leaf[metric], metrics[scalar_key]))
            if score["system"] == "poolact":
                members = [r for r in new["agents"] if r["slot_id"] == slot_id]
                require(len(members) == 4 and all(r["source_sha256"] == leaf["source_sha256"]
                                                for r in members), (slot_id, "member sources"))
                mi = sum(r[metric] for r in members) / 4
                require(math.isclose(mi, metrics[metric + "_mi"], abs_tol=1e-12),
                        (slot_id, metric + "_mi", mi, metrics[metric + "_mi"]))
        safe = {key: source[key] for key in (
            "slot_id", "model", "system", "scenario", "item", "regime", "strategy",
            "seed", "order", "outer_repeat", "execution_complete", "score_complete",
            "provider", "cohort_id", "selection", "result_sha256") if key in source}
        safe.update(source_sha256=leaf["source_sha256"],
                    source_origin=("retained_7776f70_n1" if score["system"] == "expgym"
                                   else "historical_n4_rollback"))
        source_rows.append(safe)
    return source_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--main-scalars", type=Path, required=True)
    parser.add_argument("--main-selection", type=Path, required=True)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    source = repo / SOURCE_REL
    require(source not in [output, *output.parents], "Cannot write into historical package")
    for name, expected_sha in PINNED_INPUTS.items():
        require(digest(source / name) == expected_sha, (name, "historical input changed"))
    require(json.loads((source / "CHECKS.json").read_text())["status"] == "PASS",
            "Historical report was not validated")
    helper = module(source / "recompute_audit.py")
    old = helper.read_leaf_dataset(source / "old")
    new = copy.deepcopy(old)
    new["traces"] = helper.read_csv(source / "n1/trace_metrics.csv")
    new["hypotheses"] = helper.read_csv(source / "n1/hypothesis_metrics.csv")
    for dataset in ("pools", "agents"):
        for row in new[dataset]:
            row.update(score_version="new", source_origin="historical_n4_rollback",
                       historical_source_sha256=row["source_sha256"],
                       answer_change_reason="user_requested_historical_n4_rollback")
    source_rows = check_main(repo, new, args.main_scalars, args.main_selection)
    versions = {"old": old, "new": new}
    output.mkdir(parents=True, exist_ok=True)
    for version, data in versions.items():
        base = output / "old" if version == "old" else output
        helper.aggregate_n1(data, base / "n1")
        helper.aggregate_coordination(data, base / "coordination")
    changed, population = helper.changes(versions, output)
    require(changed["pools"] == changed["agents"] == 0, "N4 rollback must equal historical scores and behavior")
    # Old reference tables and the current N1 tables must be preserved exactly.
    unchanged = []
    for original in sorted((source / "old").rglob("*.csv")):
        relative = original.relative_to(source)
        require(original.read_bytes() == (output / relative).read_bytes(), str(relative))
        unchanged.append({"path": str(relative), "sha256": digest(original)})
    for original in sorted((source / "n1").glob("*.csv")):
        relative = original.relative_to(source)
        require(original.read_bytes() == (output / relative).read_bytes(), str(relative))
        unchanged.append({"path": str(relative), "sha256": digest(original)})
    # A separate process rebuilds every CSV only from the newly exported leaves.
    published_csvs = {str(p.relative_to(output)) for p in output.rglob("*.csv")}
    require(len(published_csvs) == 31, sorted(published_csvs))
    with tempfile.TemporaryDirectory(prefix="audit-n4-rollback-replay-") as tmp:
        replay = Path(tmp)
        subprocess.run([sys.executable, str(source / "recompute_audit.py"),
                        "--replay-public", str(output), "--output", str(replay)],
                       check=True, stdout=subprocess.DEVNULL)
        replayed_csvs = {str(p.relative_to(replay)) for p in replay.rglob("*.csv")}
        require(published_csvs == replayed_csvs, "Replay file set differs")
        for relative in sorted(published_csvs):
            require((output / relative).read_bytes() == (replay / relative).read_bytes(),
                    (relative, "Replay bytes differ"))
        require(json.loads((replay / "CHECKS.json").read_text())["case_population"] == population,
                "Case population replay differs")
    files = [{"path": name, "sha256": digest(output / name),
              "bytes": (output / name).stat().st_size} for name in sorted(published_csvs)]
    checks = dict(
        schema=SCHEMA, status="PASS", mode="public_leaf_hybrid_rebuild",
        score_layer="hybrid_official_retained_n1_historical_n4",
        score_version_alias={"old": "historical_frozen_scoring_all_systems",
                             "new": "hybrid_official_retained_7776f70_n1_and_historical_n4"},
        source_commit=SOURCE_COMMIT, source_count=1170, n1_traces=702,
        n1_hypothesis_presentations=11934, n4_pools=468, n4_agents=1872,
        n1_policy="Retain the 7776f70 adopted source, scores, and actual behavior, including 2 N1 runtime controls.",
        n4_policy="Restore every strategy's pre-repair source, member answers, pool vote and scores; no member mixing.",
        old_layer="historical_frozen_scoring", changed_samples=changed,
        case_population=population, source_files=source_rows, model_calls=0,
        raw_trajectory_reparsed=False, scientific_scorer_reexecuted=False,
        public_replay_rebuilds_exported_leaf_aggregates_only=True,
        full_main_source_sha_checks=1170, member_source_sha_checks=1872,
        main_la_ea_value_checks=3276,
        unchanged_source_tables=unchanged, public_csv_replayed=31,
        main_scalars_sha256=digest(args.main_scalars),
        main_selection_sha256=digest(args.main_selection),
        builder_sha256=digest(Path(__file__)),
        frozen_input_sha256=PINNED_INPUTS,
        verification_eff_semantics="Historical scorer: fraction of jointly correct final hypotheses whose exact evidence set was attempted in human_feedback, including withheld results; null with zero denominator. N1 visible_verification_eff is separately retained.",
    )
    save_json(output / "CHECKS.json", checks)
    save_json(output / "PUBLIC_REPLAY_CHECK.json", dict(
        status="PASS", replayed_csvs=31, case_population_replayed=True,
        source_hashes_checked=1170, label_evidence_score_values_checked=3276,
        unchanged_original_tables=17, files=files))
    (output / "README.zh.md").write_text("# Audit：保留单智能体，回退全部 N4 对照\n\n"
        "当前采用层是 **hybrid official**：702 条 N1 轨迹、11,934 次假设展示保留提交 `7776f70` 的正式来源、评分和行为；468 个 N4 池、1,872 个成员（naive、cached、POOLACT 全部策略）恢复到修复前的完整池来源和旧评分。没有拼接成员，没有重新调用模型。\n\n"
        "`old/` 的 10 张表完整保留历史基线。当前 `n1/` 的 7 张表与 7776f70 逐字节相同；`coordination/` 的成员、池及 36 组统计由历史 N4 叶表生成。`changes/` 全部重新计算，比较历史全旧层与本次混合采用层。因此 N4 的 changes 为空；N1 修复带来的证据质量及配对变化继续保留。\n\n"
        "`score_version=new` 在本包中只是当前采用层的兼容标签，不表示 N4 使用新评分器。所有 N4 行显式标注 `source_origin=historical_n4_rollback`。修复版仍完整保存在 [20260918 历史交付](../../protocol-repair-20260918/README.zh.md)。\n\n"
        "复算入口（在仓库根目录运行，输出到新目录）：\n\n"
        "```bash\npython3 results/poolact-rollback-20260919/tools/build_audit_rollback.py \\\n  --repo . --output /tmp/audit-rollback-rebuilt \\\n  --main-scalars results/poolact-rollback-20260919/main/slot_scalars.csv \\\n  --main-selection results/poolact-rollback-20260919/main/SOURCE_SELECTION.csv\n```\n\n"
        "该命令校验冻结输入，重建 31 张 CSV，并在独立进程中再次从导出叶表重建，逐字节比较全部 CSV。另逐项核对 1,170 个主表来源 SHA、1,872 个成员来源和 3,276 个 LA/EA 数值（包含 N4 的 MI 与 MV）。此处复算的是公开叶表及聚合，未重新读取完整私有轨迹或重新执行科学评分器；完整私有轨迹的历史核验保留在原包。\n\n"
        "证据复用和固定案例基于对应采用来源，不能将修复版的运行时动作归给本次恢复的旧池。VE 沿用历史定义，包含实际尝试但未收到结果的反馈调用；N1 的可见反馈 VE 单独保留。\n"
        )
    allowed_files = [{"path": str(p.relative_to(output)), "sha256": digest(p), "bytes": p.stat().st_size}
                     for p in sorted(output.rglob("*")) if p.is_file() and p.name != "ALLOWED.json"]
    save_json(output / "ALLOWED.json", dict(schema=SCHEMA, files=allowed_files,
                                            excluded=["ALLOWED.json"], status="PASS"))
    print(json.dumps({key: checks[key] for key in ("status", "score_layer", "source_count",
                     "n1_traces", "n4_pools", "n4_agents", "changed_samples", "public_csv_replayed")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
