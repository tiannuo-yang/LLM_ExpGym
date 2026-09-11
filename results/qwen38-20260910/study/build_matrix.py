#!/usr/bin/env python3
"""Build the third-model matrix from fixed historical selectors, without model calls.

Offline --check-only needs no endpoint/auth file. --draft writes a fail-closed
offline matrix for inspection; a runnable matrix requires explicit endpoint(s).
No-auth wrappers use a fixed nonsecret placeholder, never inherited credentials.
This does NOT freeze a queue plan or attest endpoint readiness.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

MODEL = "qwen3.8-2.4t-a95b-fp8"
PUBLICATION_COMMIT = "6119f9d136c9ed1f06a7bedd7371be0deb9b5d59"
MANIFEST_SHA256 = "cdb8fe32b0904f49e8dd3f083e40378c18213fdb6c0004bd1d49c9beff6302d3"
MANIFEST = Path("/lustrefs/users/chufan.shi/codex_space_tn/publication/restart_v5_remote_base.oDCT5P/repo/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/actual_k3_fixed8_composite_export_v2_py311_final/manifest.json")
COMMON = ["--backend", "openai", "--max-steps", "30", "--max-evals", "30",
          "--prompt-cache-key-field", "cache_salt",
          "--max-tokens", "32768", "--tool-protocol", "native", "--max-protocol-retries", "1",
          "--max-retries", "2", "--request-timeout", "3600", "--retry-base-seconds", "3",
          "--retry-max-seconds", "30", "--tuning-final-policy", "legacy",
          "--missing-final-policy", "task-abstention-v1", "--top-p", "0.95", "--top-k", "20",
          "--reasoning-effort", "xhigh", "--chat-template-kwargs",
          '{"enable_thinking":true,"preserve_thinking":true}']
MERGE = {"expgym": {"--cost-regimes", "--search-indices", "--audit-indices", "--tuning-tasks"},
         "poolact": {"--strategies", "--question-index"}}
SELECTOR_FLAGS = {"--scenarios", "--cost-regimes", "--seed", "--models", "--model-alias",
                  "--tuning-reps", "--search-reps", "--audit-reps", "--trace-format",
                  "--search-data-source", "--search-indices", "--audit-indices", "--cc-split",
                  "--audit-orders", "--tuning-tasks", "--scenario", "--cost-regime", "--model",
                  "--agents", "--repeats", "--strategies", "--data-source", "--question-index",
                  "--tuning-task"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_manifest(path):
    raw = path.read_bytes()
    require(sha(raw) == MANIFEST_SHA256, "historical manifest SHA256 mismatch")
    manifest = json.loads(raw)
    require(manifest["schema_version"] == "restart-mixed-matrix-v1", "wrong manifest schema")
    require(len(manifest["invocations"]) == 705 and len(manifest["logical_rows"]) == 783,
            "historical matrix count mismatch")
    require(sum(len(row["agent_artifacts"]) for row in manifest["logical_rows"]) == 1881,
            "historical agent count mismatch")
    return manifest


def selector_mapping(argv):
    require(len(argv) % 2 == 0, "selector argv is not flag/value pairs")
    result = {}
    for flag, value in zip(argv[::2], argv[1::2]):
        require(flag in SELECTOR_FLAGS and flag not in result, "unknown/duplicate historical selector flag")
        require(isinstance(value, str), "selector value is not a string")
        result[flag] = value
    return result


def compact_indices(values):
    indices = sorted(int(value) for value in values)
    require(len(indices) == len(set(indices)) and indices and indices[0] >= 0,
            "invalid merged indices")
    if indices == list(range(indices[0], indices[-1] + 1)):
        return "%d:%d" % (indices[0], indices[-1] + 1)
    return ",".join(map(str, indices))


def endpoints_from_values(values):
    result = []
    for value in values:
        parsed = urlsplit(value)
        require(parsed.scheme in {"http", "https"} and parsed.hostname and not
                (parsed.username or parsed.password or parsed.query or parsed.fragment),
                "endpoint must not contain credentials/query/fragment")
        result.append(value.rstrip("/"))
    require(len(result) == len(set(result)), "duplicate endpoints")
    return result


def build_stages(manifest, source_repo, python, python_hpo, *, endpoints=(), auth_file=None):
    require(auth_file is None, "this private no-auth study does not support auth-file")
    endpoints = endpoints_from_values(endpoints)
    groups = defaultdict(list)
    for invocation in manifest["invocations"]:
        system = invocation["system"]
        argv = selector_mapping(invocation["selection_argv"])
        require(system in MERGE, "unknown runner")
        require(invocation["runtime_profile_required"] in {"native", "paramnet_legacy"}, "unknown runtime")
        for flag in ("--models", "--model"):
            if flag in argv:
                argv[flag] = MODEL
        if "--model-alias" in argv:
            argv["--model-alias"] = MODEL + "=" + MODEL
        if "--audit-orders" in argv:
            argv["--audit-orders"] = str(source_repo / "configs/audit_hypothesis_orders.json")
        fixed = {flag: value for flag, value in argv.items() if flag not in MERGE[system]}
        key = (system, invocation["runtime_profile_required"], canonical(fixed))
        groups[key].append(argv)
    stages = []
    for (system, runtime, fixed), original in sorted(groups.items()):
        options = json.loads(fixed)
        for flag in sorted(MERGE[system]):
            selected = {argv[flag] for argv in original if flag in argv}
            if not selected:
                continue
            if flag in {"--search-indices", "--audit-indices", "--question-index"}:
                options["--questions" if flag == "--question-index" else flag] = compact_indices(selected)
            elif flag == "--strategies":
                options[flag] = ",".join(v for v in ("naive", "cached", "poolact") if v in selected)
            else:
                options[flag] = ",".join(sorted(selected))
        argv = [value for pair in sorted(options.items()) for value in pair] + COMMON
        argv += (["--temperature-tuning", "1", "--temperature-eval", "1"] if system == "expgym"
                 else ["--temperature", "1", "--max-context-tokens", "131072", "--probes", "4"])
        if endpoints:
            # Do not let make_plan capture a stale OPENAI_BASE_URL from the shell.
            # The queue still binds each job to one of its explicit endpoints.
            argv += ["--base-url", endpoints[0]]
        stage = {"label": "qwen38-%03d-%s-%s" % (len(stages), system, runtime),
                 "runner": system, "python": str(python_hpo if runtime == "paramnet_legacy" else python),
                 "args": argv}
        if endpoints:
            stage["endpoints"] = list(endpoints)
        stages.append(stage)
    return {"stages": stages}


def item_lookup_key(system, scenario, *, task=None, source=None, index=None, split=None):
    return (system, scenario, task if scenario == "tuning" else source if scenario == "restricted_search"
            else split, None if scenario == "tuning" else index)


def row_key(row):
    return canonical({name: row[name] for name in
                      ("system", "scenario", "item", "selector", "regime", "strategy", "outerrep",
                       "order", "hypothesis_order", "sampling_seed_labels")})


def expand_and_validate(matrix, manifest, source_repo, *, python, python_hpo,
                        endpoints=(), auth_file=None):
    """Use the source runners' actual selectors, without preflight/model/data loads."""
    require(auth_file is None, "this private no-auth study does not support auth-file")
    sys.path.insert(0, str(source_repo))
    sweep = importlib.import_module("scripts.run_paper_sweep")
    pool = importlib.import_module("scripts.run_poolact")
    for module in (sweep, pool):
        require(Path(module.__file__).resolve().parents[1] == source_repo.resolve(),
                "different source repository already imported")
    search = importlib.import_module("expgym.task_restricted_search")
    search_filter = manifest["source_and_inputs"]["search_filter"]
    require(search.SWEET_SPOT_TYPES == search_filter["types"]
            and search.MAX_ANSWER_COUNT == search_filter["max_answer_count"],
            "Search question filter changed")
    # The frozen source loader uses a stable Python sort with (type, difficulty).
    # Pin its implementation in the final source plan; do not read large parquet here.
    require(search_filter["stable_sort"] == ["type", "difficulty"], "unknown Search sorting contract")
    endpoints = endpoints_from_values(endpoints)
    items = {}
    expected = Counter(row_key(row) for row in manifest["logical_rows"])
    require(len(expected) == 783 and all(n == 1 for n in expected.values()), "duplicate historical logical identity")
    for row in manifest["logical_rows"]:
        selector = row["selector"]
        key = item_lookup_key(row["system"], row["scenario"], task=selector.get("tuning_task"),
                              source=selector.get("data_source"), index=selector.get("question_index"),
                              split=selector.get("cc_split"))
        selected = {"item": row["item"], "selector": selector}
        require(key not in items or items[key] == selected, "inconsistent historical item identity")
        items[key] = selected
    actual, groups, runtime_counts = Counter(), Counter(), Counter()
    agents, labels, stage_units = 0, set(), []
    for stage in matrix["stages"]:
        require(set(stage) <= {"label", "runner", "python", "args", "endpoints"}, "unknown stage fields")
        require(stage["label"] not in labels, "duplicate stage label")
        labels.add(stage["label"])
        system = stage["runner"]
        require(system in MERGE, "unknown runner")
        require(stage.get("endpoints", []) == endpoints, "stage endpoints differ from admitted deployment")
        args = (sweep if system == "expgym" else pool).parse_args(stage["args"])
        require(args.api_key is None and args.backend == "openai", "credential literal or wrong backend")
        require(args.prompt_cache_key_field == "cache_salt", "SGLang prompt-cache field mismatch")
        require(args.api_key_file is None, "this private no-auth study does not support auth-file")
        require(args.base_url == (endpoints[0] if endpoints else None), "base URL differs from explicit deployment")
        require(not args.dry_run and not args.resume and args.terminal_evidence_dir is None,
                "runner flags interfere with queue ownership")
        require(args.max_steps == args.max_evals == 30 and args.max_tokens == 32768,
                "generation horizon mismatch")
        require(args.tool_protocol == "native" and args.max_protocol_retries == 1
                and args.max_retries == 2 and args.request_timeout == 3600
                and args.retry_base_seconds == 3 and args.retry_max_seconds == 30,
                "protocol/transport mismatch")
        require(args.top_p == .95 and args.top_k == 20 and args.reasoning_effort == "xhigh"
                and args.chat_template_kwargs == {"enable_thinking": True, "preserve_thinking": True},
                "Qwen profile mismatch")
        require(args.tuning_final_policy == "legacy" and args.missing_final_policy == "task-abstention-v1",
                "endpoint policy mismatch")
        selected = []
        if system == "expgym":
            require(args.temperature_tuning == args.temperature_eval == 1, "Exp temperature mismatch")
            require(args.trace_format == "v2", "Exp trace format mismatch")
            for job in sweep._build_jobs(args):
                require(job.model_id == job.model_alias == MODEL, "Exp model/alias mismatch")
                key = item_lookup_key(system, job.scenario, task=job.tuning_task, source=job.data_source,
                                      index=job.question_index, split=job.cc_split)
                require(key in items, "Exp selected an unregistered item")
                outer = (job.seed - 2200) // 4 if job.scenario == "tuning" else 0
                row = {**items[key], "system": system, "scenario": job.scenario,
                       "regime": job.cost_regime, "strategy": "single", "outerrep": outer,
                       "order": job.rep if job.scenario == "evidence_audit" else "none",
                       "hypothesis_order": job.hypothesis_order, "sampling_seed_labels": [job.seed]}
                selected.append(row)
        else:
            require(args.model == MODEL, "Pool model mismatch")
            require(args.agents == 4 and args.repeats == 1 and args.temperature == 1
                    and args.max_context_tokens == 131072 and args.probes == 4
                    and not args.vllm_disable_thinking, "Pool N/repeat/context/temperature/probes/thinking mismatch")
            questions = args.questions if args.questions is not None else [args.question_index or 0]
            for repeat in range(args.repeats):
                repeated = pool._repeat_namespace(args, repeat)
                for question in questions:
                    for strategy in args.strategies:
                        key = item_lookup_key(system, args.scenario, task=args.tuning_task,
                                              source=args.data_source, index=question, split=args.cc_split)
                        require(key in items, "Pool selected an unregistered item")
                        row = {**items[key], "system": system, "scenario": args.scenario,
                               "regime": args.cost_regime, "strategy": strategy,
                               "outerrep": (repeated.seed - 2200) // 4 if args.scenario == "tuning" else 0,
                               "order": "default" if args.scenario == "evidence_audit" else "none",
                               "hypothesis_order": None,
                               "sampling_seed_labels": [repeated.seed + agent for agent in range(4)]}
                        selected.append(row)
        for row in selected:
            legacy = row["scenario"] == "tuning" and row["selector"]["tuning_task"].startswith("hpobench:paramnet:")
            require(stage["python"] == str(python_hpo if legacy else python), "task runtime wrapper mismatch")
            actual[row_key(row)] += 1
            groups[(system, row["scenario"])] += 1
            runtime_counts[stage["python"]] += 1
            agents += 4 if system == "poolact" else 1
        stage_units.append({"stage": stage["label"], "system": system,
                            "scenarios": sorted({row["scenario"] for row in selected}),
                            "queue_jobs": len(selected),
                            "scientific_outerreps": sorted({row["outerrep"] for row in selected}),
                            "orders": sorted({str(row["order"]) for row in selected}),
                            "agent_seed_blocks": sorted({tuple(row["sampling_seed_labels"]) for row in selected}),
                            "runner_repeat_index_note": "HPO stages use R1; recover outerrep from seed blocks, not runner rep=0"})
    require(actual == expected, "new matrix differs in item/selector/regime/strategy/repeat/order/seed identity")
    require(sum(actual.values()) == 783 and agents == 1881, "new matrix coverage mismatch")
    return {"stages": len(matrix["stages"]), "queue_jobs": sum(actual.values()),
            "logical_outcomes": sum(actual.values()), "agent_traces": agents,
            "groups": [{"system": key[0], "scenario": key[1], "queue_jobs": n} for key, n in sorted(groups.items())],
            "jobs_by_python": dict(runtime_counts), "full_canonical_identity_matches": True,
            "deployment_and_profile_match_explicit_inputs": True, "stage_units": stage_units,
            "search_filter": search_filter,
            "canonical_identity_sha256": sha(canonical(sorted(actual)).encode())}


def expected_inputs(manifest, source_repo, data_root):
    old_data_root = Path(manifest["source_and_inputs"]["files"]["hpo.oracle"]["path"]).parents[1]
    result, changed = {}, {}
    for name, record in manifest["source_and_inputs"]["files"].items():
        if name in {"paramnet.runtime_config", "paramnet.wrapper"}:
            changed[name] = {**record, "disposition": "historical_runtime_path_not_reused; new per-job wrapper/config recorded separately"}
            continue
        if name == "audit.orders":
            path = source_repo / "configs/audit_hypothesis_orders.json"
        elif name == "hpo.config":
            path = source_repo / "configs/hpobench_tasks.yaml"
        else:
            path = data_root / Path(record["path"]).relative_to(old_data_root)
        result[name] = {"path": str(path), "bytes": record["bytes"], "sha256": record["sha256"]}
        if name in {"audit.orders", "hpo.config"}:
            require(sha(path.read_bytes()) == record["sha256"], "source task/order configuration changed")
    return {"required_unchanged_inputs": result, "historical_runtime_references": changed,
            "large_data_bytes_verified_here": False,
            "data_copy_and_runtime_identity_acceptance": "parent must verify isolated copies/wrappers before final queue plan"}


def runtime_environment(source_repo, data_root):
    return {"source_repo": str(source_repo), "data_root": str(data_root),
            "static": {"EXPGYM_DATA_ROOT": str(data_root),
                       "PHANTOM_WIKI_ROOT": str(data_root / "phantom-wiki"),
                       "HPOBENCH_ROOT": str(data_root / "hpo_tuning/HPOBench"),
                       "XDG_DATA_HOME": str(data_root / "hpo_tuning/hpobench_data"),
                       "PYTHONNOUSERSITE": "1", "OMP_NUM_THREADS": "1",
                       "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                       "OPENAI_API_KEY": "EXPGYM_LOCAL_NOAUTH_PLACEHOLDER_20260907"},
            "per_job_wrapper_contract": {
                "do_not_override": ["EXPGYM_RUN_ID", "EXPGYM_API_DUMP_DIR"],
                "state_root": "parent(absolute EXPGYM_API_DUMP_DIR)/runtime/hpobench",
                "XDG_CONFIG_HOME": "state_root/config", "XDG_CACHE_HOME": "state_root/cache",
                "hpobench_sockets": "state_root/sockets",
                "main_and_hpo_wrappers": "transparent argv forwarding; cd new source; HPO config/cache/sockets per job",
                "credentials": "private no-auth study only; wrapper overrides inherited OPENAI_API_KEY with nonsecret placeholder; builder rejects auth-file because runner env takes precedence"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--python-hpo", type=Path, required=True)
    parser.add_argument("--auth-file", type=Path,
                        help="Unsupported for this private no-auth study; explicit use is rejected")
    endpoint = parser.add_mutually_exclusive_group()
    endpoint.add_argument("--endpoint", action="append", default=[])
    endpoint.add_argument("--endpoint-file", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--draft", action="store_true",
                        help="Write offline inspection assets; pending-deployment stage marker makes queue reject this draft")
    args = parser.parse_args()
    source_repo, data_root = args.source_repo.absolute(), args.data_root.absolute()
    values = json.loads(args.endpoint_file.read_text())["endpoints"] if args.endpoint_file else args.endpoint
    endpoints = endpoints_from_values(values)
    require(not (args.draft and args.check_only), "choose draft or check-only")
    if args.draft:
        require(args.output_dir is not None and not endpoints and args.auth_file is None,
                "offline draft requires output-dir and no endpoint/auth-file")
    elif not args.check_only:
        require(args.output_dir is not None and endpoints,
                "writing runnable matrix requires output-dir and parent-supplied endpoint(s)")
    manifest = load_manifest(args.manifest)
    matrix = build_stages(manifest, source_repo, args.python.absolute(), args.python_hpo.absolute(),
                          endpoints=endpoints, auth_file=args.auth_file.absolute() if args.auth_file else None)
    coverage = {"schema_version": "qwen38-fixed-matrix-coverage-v1", "model": MODEL,
                "origin_manifest": {"path": str(args.manifest.absolute()), "sha256": MANIFEST_SHA256,
                                    "publication_commit": PUBLICATION_COMMIT},
                "original_invocations": 705,
                "audit_execution_change": "39 three-order invocations become 117 separate jobs; retain document-level three-order averaging",
                "new_source_hash_finalization": "pending; final run_study_queue plan step only",
                "readiness_verified": False, "new_model_calls": 0, "credentials_read": False,
                "deployment_pending": not bool(endpoints),
                "auth_mode": "wrapper_nonsecret_placeholder",
                **expand_and_validate(matrix, manifest, source_repo,
                                      python=args.python.absolute(), python_hpo=args.python_hpo.absolute(),
                                      endpoints=endpoints, auth_file=args.auth_file.absolute() if args.auth_file else None),
                **expected_inputs(manifest, source_repo, data_root)}
    if args.check_only:
        print(json.dumps({key: value for key, value in coverage.items() if key not in
                          {"required_unchanged_inputs", "historical_runtime_references", "stage_units"}}, indent=2, sort_keys=True))
        return
    if args.draft:
        for stage in matrix["stages"]:
            # run_study_queue rejects unknown stage fields. Inspection is safe,
            # but a draft cannot accidentally inherit an old API endpoint.
            stage["deployment_pending"] = True
        coverage["draft_note"] = "Not executable: regenerate without --draft and with explicit endpoints before queue plan"
    outputs = {"matrix.json": matrix, "coverage.json": coverage,
               "runtime_environment.json": runtime_environment(source_repo, data_root)}
    require(not any((args.output_dir / name).exists() for name in outputs), "output exists; choose fresh directory")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        with (args.output_dir / name).open("x", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    print(json.dumps({"output_dir": str(args.output_dir.absolute()), "stages": coverage["stages"],
                      "queue_jobs": coverage["queue_jobs"], "agent_traces": coverage["agent_traces"],
                      "queue_plan_not_yet_frozen": True}, sort_keys=True))


if __name__ == "__main__":
    main()
