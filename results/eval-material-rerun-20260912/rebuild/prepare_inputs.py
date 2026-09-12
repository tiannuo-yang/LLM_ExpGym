#!/usr/bin/env python3
"""Build portable, explicit report inputs AFTER all four terminal exports exist.

Reads only frozen plans, mappings, completion metadata and usage projections.
Never opens result/agent/API-dump payloads; result identities come from already
verified completion receipts. No score, model, archive or network calls.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import io
import json
from pathlib import Path
import subprocess

import aggregate_material as a

MODELS = ("deepseek", "glm", "kimi", "gpt")
HISTORY_COMMIT = "6c63f1c03c88683fa55be5cafcbb8122ac8fadaa"
HISTORY_PREFIX = "results/five-model-ranking-20260911/"
ORACLE_SHA = "f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e"
RESOURCE_FIELDS = ("model", "scenario", "cost_regime", "strategy", "cohort", "planned_pools", "completed_pools", "failed_pools", "not_started_pools",
                   "planned_agents", "physical_attempts_known_subtotal", "physical_attempts_complete_total", "successful_replies_known_subtotal",
                   "errored_attempts_known_subtotal", "logical_generation_calls_known_subtotal", "logical_generation_calls_complete_total",
                   "input_tokens_known_subtotal", "input_tokens_unknown_observed_attempts", "input_tokens_complete_total",
                   "output_tokens_known_subtotal", "output_tokens_unknown_observed_attempts", "output_tokens_complete_total",
                   "reasoning_tokens_known_subtotal", "reasoning_tokens_unknown_observed_attempts", "reasoning_tokens_complete_total",
                   "request_wall_seconds_known_subtotal", "request_wall_seconds_unknown_observed_attempts", "request_wall_seconds_complete_total",
                   "pool_wall_seconds_known_subtotal", "pool_wall_seconds_unknown_begun_pools", "pool_wall_seconds_complete_total",
                   "unindexed_begun_pools", "resource_scope", "source_export")


def descriptor(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=a.sha(raw))


def exported_file(stage_entry, stage, name):
    identity = stage["output_identities"][name]
    return dict(path=str(Path(stage_entry["path"]).parent / name), bytes=identity["bytes"], sha256=identity["sha256"])


class Preparation:
    def __init__(self, config):
        self.config = config
        self.root = Path(config["study_root"]).resolve()
        self.files, self.sources, self.copies = {}, {}, {}
        self.selections = {model: set() for model in MODELS}

    def read(self, entry, role):
        path = Path(entry["path"])
        a.require(path.is_absolute() and path.is_file() and not path.is_symlink(), "regular absolute frozen metadata required")
        # Fail closed if a caller accidentally supplies a scientific/raw payload.
        a.require("api_dump" not in path.parts and not (path.name == "result.json" and "invocations" in path.parts)
                  and not ("agents" in path.parts and path.name.startswith("agent_")), "preparation must not open result/agent/raw payload")
        raw = path.read_bytes()
        actual = descriptor(path, raw)
        a.require(actual["bytes"] == entry["bytes"] and actual["sha256"] == entry["sha256"], "frozen metadata changed: " + str(path))
        self.sources[str(path)] = dict(actual, role=role)
        return raw

    def read_digest(self, path, checksum, role):
        path = Path(path)
        return self.read(dict(path=str(path), bytes=path.stat().st_size, sha256=checksum), role)

    def add(self, name, raw):
        a.require(name not in self.files or self.files[name] == raw, "different bytes for copied input")
        self.files[name] = raw
        return descriptor(name, raw)

    def copy(self, source_entry, name, role):
        raw = self.read(source_entry, role)
        result = self.add(name, raw)
        self.copies[str(Path(source_entry["path"]).resolve())] = result
        return result

    def artifact(self, entry):
        """Relocate a bound identity; deliberately do NOT read payload bytes."""
        path = Path(entry["path"])
        resolved = str(path.resolve())
        if resolved in self.copies:
            copied = self.copies[resolved]
            a.require((copied["bytes"], copied["sha256"]) == (entry["bytes"], entry["sha256"]), "copied plan identity differs")
            return copied
        relative = path.relative_to(self.root)
        a.require(relative.parts and relative.parts[0] in MODELS and ".." not in relative.parts, "artifact outside model owned root")
        model, member = relative.parts[0], Path(*relative.parts[1:]).as_posix()
        a.require(member and entry["bytes"] >= 0 and len(entry["sha256"]) == 64, "invalid inherited artifact descriptor")
        self.selections[model].add(member)
        return dict(path="@study/" + model + "/" + member, bytes=entry["bytes"], sha256=entry["sha256"])

    def check_metadata_stability(self):
        for entry in self.sources.values():
            raw = Path(entry["path"]).read_bytes()
            a.require((len(raw), a.sha(raw)) == (entry["bytes"], entry["sha256"]), "metadata changed during preparation")


def adapt_gpt_mapping(p, source_entry):
    original = json.loads(p.read(source_entry, "frozen_gpt_effective_mapping"))
    a.require(original["schema"] == "expgym.gpt-effective-delivery-mapping.v1" and len(original["jobs"]) == 27, "GPT final mapping schema/scope differs")
    jobs = []
    for row in original["jobs"]:
        a.require(row["pool_terminal_status"]["execution_complete"] is True and row["receipt_artifact_inventory_verified"] is True,
                  "GPT row is not a verified normal completed execution")
        plan_path = Path(row["plan_path"])
        if str(plan_path.resolve()) not in p.copies:
            plan_raw = p.read_digest(plan_path, row["plan_sha256"], "frozen_gpt_effective_plan")
            parsed = json.loads(plan_raw)
            a.require(all(j["args"].get("api_key") is None and j["args"].get("api_key_file") is None for j in parsed["jobs"]),
                      "private credentials/source path in plan; requires explicit public handling")
            name = "plans/gpt_effective_" + row["plan_sha256"][:12] + ".json"
            p.copies[str(plan_path.resolve())] = p.add(name, plan_raw)
        plan_ref = p.copies[str(plan_path.resolve())]
        receipt_path = Path(row["queue_receipt_path"])
        receipt_raw = p.read_digest(receipt_path, row["queue_receipt_sha256"], "gpt_existing_completion_receipt")
        receipt = json.loads(receipt_raw)
        a.require(receipt["exit_code"] == 0 and receipt["job_id"] == row["effective_physical_job_id"], "GPT completion receipt mismatch")
        invocation = Path(row["invocation_path"])
        def member(path):
            rel = Path(path).relative_to(invocation).as_posix()
            entry = receipt["artifacts"][rel]
            return p.artifact(dict(path=path, bytes=entry["bytes"], sha256=entry["sha256"]))
        jobs.append(dict(logical_job_id=row["scientific_slot_job_id"], execution_status="completed",
                         cohort="gpt-material-recovery-001" if row["replacement_applied"] else "gpt-material-original-v1",
                         effective_job_id=row["effective_physical_job_id"], effective_plan=plan_ref,
                         result=member(row["result_path"]), summary=member(row["summary_path"]),
                         verification_receipt=p.artifact(descriptor(receipt_path, receipt_raw)),
                         identity_score_verification_passed=True))
    return jobs, original


def adapt_selfhosted_mapping(p, stage_entry, model):
    stage = json.loads(p.read(stage_entry, model + "_terminal_export"))
    a.require(stage["controller_drained"] is True, "self-hosted controller has not drained")
    execution_entry = exported_file(stage_entry, stage, "execution_index.json")
    execution = json.loads(p.read(execution_entry, model + "_explicit_execution_mapping"))
    a.require(execution["schema"] == "expgym.material-execution-index.v1", "unsupported self-hosted terminal mapping")
    converted = []
    for old in execution["jobs"]:
        row = {key: old[key] for key in ("logical_job_id", "execution_status", "cohort")}
        if old["execution_status"] == "completed":
            row.update(effective_job_id=old["effective_job_id"], identity_score_verification_passed=old["identity_score_verification_passed"])
            for key in ("effective_plan", "result", "summary", "verification_receipt"):
                row[key] = p.artifact(old[key])
        else:
            a.require(old["execution_status"] in ("failed", "not_started"), "in-flight self-hosted row forbidden")
            row["reason"] = old["reason"]
        converted.append(row)
    attempts = p.copy(exported_file(stage_entry, stage, "all_attempts_index.json"), "attempts/"+model+"_all_attempts_index.json", model+"_all_attempts_index")
    return converted, attempts


def selfhosted_resources(p, stage_entry, model):
    stage = json.loads(p.read(stage_entry, model + "_frozen_resource_export"))
    a.require(stage["schema"] == "expgym.material-resource-export.v1", "unsupported resource export")
    original = exported_file(stage_entry, stage, "resources_by_setting.csv")
    copied = p.copy(original, "resource_exports/"+model+"_resources_by_setting.csv", model+"_resource_table")
    p.copy(exported_file(stage_entry, stage, "resources_by_pool.csv"), "resource_exports/"+model+"_resources_by_pool.csv", model+"_pool_resources")
    rows = list(csv.DictReader(io.StringIO(p.files[copied["path"]].decode())))
    projected = []
    for row in rows:
        out = {field: row.get(field, "") for field in RESOURCE_FIELDS}
        out.update(resource_scope="effective_formal_queue_only; original full projection retained", source_export=copied["path"])
        projected.append(out)
    return projected, copied


def gpt_resources(p, metadata, mapping, planned):
    token_ref = p.copy(metadata["token_usage_summary"], "resource_exports/gpt_token_usage_summary.json", "gpt_frozen_usage_projection")
    attempts_ref = p.copy(metadata["physical_attempts"], "resource_exports/gpt_physical_attempts.csv", "gpt_frozen_physical_attempt_projection")
    usage = json.loads(p.files[token_ref["path"]])
    attempt_rows = list(csv.DictReader(io.StringIO(p.files[attempts_ref["path"]].decode())))
    logical_plan = {row["job_id"]: row for row in planned if row["model"] == "gpt-5.6-sol"}
    grouped = defaultdict(list)
    for row in mapping["jobs"]:
        logical = logical_plan[row["scientific_slot_job_id"]]
        grouped[(logical["model"], logical["scenario"], logical["regime"], logical["strategy"])].append(row)
    out = []
    for key, jobs in sorted(grouped.items()):
        physical = {j["effective_physical_job_id"] for j in jobs}
        attempts = [r for r in attempt_rows if r["physical_job_id"] in physical]
        blocks = [usage["by_physical_job"][job] for job in sorted(physical)]
        a.require(len(attempts) == sum(b["physical_transport_attempts"] for b in blocks), "GPT projected attempt count differs")
        logical_calls = {(r["physical_job_id"], r["generation_id"]) for r in attempts if r["generation_id"]}
        generation_unknown = sum(not r["generation_id"] for r in attempts)
        row = dict(zip(("model", "scenario", "cost_regime", "strategy"), key))
        row.update(cohort="gpt-material-effective-v1", planned_pools=len(jobs), completed_pools=len(jobs), failed_pools=0, not_started_pools=0,
                   planned_agents=4*len(jobs), physical_attempts_known_subtotal=len(attempts), physical_attempts_complete_total=len(attempts),
                   successful_replies_known_subtotal=sum(b["states"].get("success", 0) for b in blocks),
                   errored_attempts_known_subtotal=sum(b["states"].get("error", 0) for b in blocks),
                   logical_generation_calls_known_subtotal=len(logical_calls), logical_generation_calls_complete_total=None if generation_unknown else len(logical_calls),
                   request_wall_seconds_known_subtotal=None, request_wall_seconds_unknown_observed_attempts=len(attempts), request_wall_seconds_complete_total=None,
                   pool_wall_seconds_known_subtotal=None, pool_wall_seconds_unknown_begun_pools=len(jobs), pool_wall_seconds_complete_total=None,
                   unindexed_begun_pools=0, resource_scope="effective_formal_only; superseded transport attempts retained separately; timing absent from this frozen projection",
                   source_export=token_ref["path"]+";"+attempts_ref["path"])
        for metric in ("input_tokens", "output_tokens", "reasoning_tokens"):
            tokens = [b["tokens"][metric] for b in blocks]
            row[metric+"_known_subtotal"] = sum(t["known_sum"] for t in tokens)
            row[metric+"_unknown_observed_attempts"] = sum(t["unknown_attempts"] for t in tokens)
            row[metric+"_complete_total"] = (sum(t["total_if_fully_known"] for t in tokens)
                                                if all(t["total_if_fully_known"] is not None for t in tokens) else None)
        out.append({field: row[field] for field in RESOURCE_FIELDS})
    return out, dict(token_usage=token_ref, physical_attempts=attempts_ref,
                     scope="all 28 physical jobs, including the original failed transport cohort; token totals retain unknown usage")


def prepare(config):
    a.require(config["schema"] == "expgym.material-input-preparation.v1", "unsupported preparation config")
    a.require(set(config["selfhosted"]) == {"deepseek", "glm", "kimi"}, "all three self-hosted terminal inputs required")
    a.require(all(config["selfhosted"][m].get("terminal_export") and config["selfhosted"][m].get("resource_export") for m in config["selfhosted"]),
              "not all terminal exports are supplied; do not invent not_started GLM slots")
    p = Preparation(config)
    plans, planned = [], []
    for model in MODELS:
        source = config["plans"][model]
        copied = p.copy(source, "plans/"+model+".json", model+"_logical_master_plan")
        parsed = json.loads(p.files[copied["path"]])
        a.require(all(j["args"].get("api_key") is None and j["args"].get("api_key_file") is None for j in parsed["jobs"]),
                  "plan contains credentials or private credential-source path")
        plans.append(copied)
        planned.extend(a.plan_rows(parsed))
    a.validate_matrix(planned, 369, 9)
    oracle = p.copy(config["oracle"], "oracle.json", "frozen_oracle")
    a.require(oracle["sha256"] == ORACLE_SHA, "frozen oracle identity differs")
    oldfiles = {"historical_absolute": "absolute_settings.csv", "historical_gap0": "main_findings_v2/gap0_settings.csv",
                "historical_expgym_summary": "main_findings_v2/main_expgym.csv", "historical_family_rankings": "main_findings_v2/main_family_rankings.csv"}
    historical = {}
    for key, member in oldfiles.items():
        raw = subprocess.check_output(["git", "-C", config["historical_git_repo"], "show", HISTORY_COMMIT+":"+HISTORY_PREFIX+member])
        historical[key] = p.add("historical/"+Path(member).name, raw)
    jobs, attempt_indexes, resources = [], {}, []
    for model in ("deepseek", "glm", "kimi"):
        rows, attempt_indexes[model] = adapt_selfhosted_mapping(p, config["selfhosted"][model]["terminal_export"], model)
        jobs.extend(rows)
        rows, _ = selfhosted_resources(p, config["selfhosted"][model]["resource_export"], model)
        resources.extend(rows)
    rows, gpt_mapping = adapt_gpt_mapping(p, config["gpt"]["effective_mapping"])
    jobs.extend(rows)
    rows, attempt_indexes["gpt"] = gpt_resources(p, config["gpt"], gpt_mapping, planned)
    resources.extend(rows)
    a.require(len(jobs) == 369 and {j["logical_job_id"] for j in jobs} == {r["job_id"] for r in planned}, "effective mapping is not exactly 369 registered slots")
    a.require(len(resources) == 27 and sum(int(r["planned_pools"]) for r in resources) == 369, "resource setting coverage differs")
    actual_resource_keys = {(r["model"], r["scenario"], r["cost_regime"], r["strategy"]) for r in resources}
    expected_resource_keys = {(r["model"], r["scenario"], r["regime"], r["strategy"]) for r in planned}
    a.require(actual_resource_keys == expected_resource_keys, "resource rows not the planned settings")
    jobs.sort(key=lambda r: r["logical_job_id"])
    execution = p.add("execution_index.json", a.jb(dict(schema="expgym.material-execution-index.v1", jobs=jobs)))
    resource_entry = p.add("resources_by_setting.csv", a.csv_bytes(resources))
    allocation = []
    for model, entry in config.get("public_accounting", {}).items():
        allocation.append(dict(model=model, source=p.copy(entry, "accounting/"+model+"_public_metadata.json", model+"_public_accounting")))
    attempts = p.add("ALL_ATTEMPTS_INDEX.json", a.jb(dict(schema="expgym.material-report-all-attempts-index.v1",
                     formal_and_superseded_attempt_sources=attempt_indexes, public_allocation_metadata=allocation,
                     scope="formal resource projections are not total study cost; allocation includes reported loading/warmup/idle/drain; historical diagnostic study remains separate",
                     allocation_models_missing=sorted(set(("deepseek", "glm", "kimi"))-set(config.get("public_accounting", {}))),
                     request_timing_note="GPT timing is not present in the consumed frozen usage projection and is not reconstructed from raw")))
    spec = dict(schema="expgym.material-report-inputs.v1", study_id="eval-material-rerun-20260912-v1", expected_jobs=369, expected_cells=9,
                plans=plans, execution_index=execution, oracle=oracle, resources_by_setting=resource_entry, all_attempts_index=attempts, **historical)
    p.add("spec.json", a.jb(spec))
    p.add("RESTORE_SELECTIONS.json", a.jb({model: sorted(members) for model, members in p.selections.items()}))
    for model, members in p.selections.items():
        p.add("restore_selections/"+model+".json", a.jb(sorted(members)))
    p.check_metadata_stability()
    p.add("PUBLIC_INPUT_FILES.json", a.jb(sorted([*p.files, "PUBLIC_INPUT_FILES.json", "PREPARATION.json"])))
    p.add("PREPARATION.json", a.jb(dict(schema="expgym.material-report-preparation-receipt.v1", source_metadata=list(p.sources.values()),
                  historical_git_commit=HISTORY_COMMIT, historical_repo_path=HISTORY_PREFIX,
                  scientific_payloads_read=False, score_recomputed=False, artifact_reference_prefix="@study/<model>/<owned-root-relative-member>",
                  output_identities={name: descriptor(name, raw) for name, raw in sorted(p.files.items())})))
    return p.files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    a.require(not args.output.exists(), "refuse to overwrite prepared inputs")
    files = prepare(json.loads(args.config.read_bytes()))
    args.output.mkdir(parents=True)
    for name, raw in files.items():
        path = args.output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    print(json.dumps({"files": len(files), "scientific_slots": 369, "scientific_payloads_read": False, "output": str(args.output)}))


if __name__ == "__main__":
    main()
