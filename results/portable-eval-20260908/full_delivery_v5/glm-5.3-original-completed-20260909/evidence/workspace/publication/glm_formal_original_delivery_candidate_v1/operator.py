#!/usr/bin/env python3
"""Exact GLM original-run local delivery; frozen single-batch helpers, no uploader."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import threading

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PUB = HERE.parent
WORKSPACE = str(PUB.parent)
EXPECTED = dict(batch_count=36, file_count=70520, original_bytes=3242213793)
SCOPE = {
    "inventory_ref": {"path": str(PUB / "glm_formal_original_scope_candidate_v1/candidate/inventory.json"),
        "sha256": "78610fabac42cf3606dca00a19a3148647eb9eaa413843658bc38f504ec47489"},
    "index_ref": {"path": str(PUB / "glm_formal_original_scope_candidate_v1/candidate/batches/INDEX.candidate.json"),
        "sha256": "843ee297489da15af9976a65d0ba97f12b634153320bf863e49ceb40049fe5b5"},
    "seal_ref": {"path": WORKSPACE + "/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/sealed_restart_runs_v1/glm-5.3-formal-completed-20260909/inventory.json",
        "sha256": "da5b89e1041e396c04673b6f363dd01a3f6d64b61bfd9fe6d60f0a6617957f22"}}
HELPERS = {
    "scan": (PUB / "pinned_batches_scan_candidate_v1/scan_batches.py", "5b3dbdf84f789dec731a3f8c821c2981a0f00e61f4b951141e022fab491b568b"),
    "batch": (PUB / "restart_v5_closed_local_delivery_v1/operator.py", "979fd024d739eb927825d156048cbd6a1850fb27ddc6a5c5677abba1e4d7d497")}
TOOL_PINS = [
    ("shard_delivery_candidate_v2/pack.py", "07eb7a20e838ca53bfda6144887283e597914e95fb11c5e16ff43f95f09f5f10"),
    ("shard_delivery_candidate_v2/common.py", "7147524d5799dc1264f088518db19251c5f906bc2da501854ce279f56d73263e"),
    ("shard_delivery_candidate_v2/restore.py", "ec20a0e22c8f810b09e894e0ddc6cc8dec114a66be4fe23cab8a55f3b62ac710"),
    ("validate_bundle_v2.py", "aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116"),
    ("collection_restore_candidate_v2/restore_collection.py", "24a2ff6da7521c7920ce50ea7491aa682310e78874ba2d552649e9d2d88bb6b2")]
TOOL_REFS = [{"path": str(PUB / p), "sha256": h} for p, h in TOOL_PINS]


def load_helper(kind):
    path, digest = HELPERS[kind]
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("frozen_helper_identity")
    spec = importlib.util.spec_from_file_location("glm_delivery_" + kind, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


d = load_helper("scan")
c = d.c


def identity(ref):
    return {k: ref[k] for k in ("path", "sha256")}


def collect(reader, refs):
    for path, ref in reader.refs.items():
        c.need(path not in refs or refs[path] == ref, "conflicting_metadata_ref")
        refs[path] = ref


def recheck(refs):
    # Independent bounded reads, not one cached copy of all 36 reports/locks.
    for ref in refs.values():
        d.Metadata().raw(ref, c.MEMBER)


def scan_metadata(scan_go_ref, prepared_ref, scan_receipt_ref):
    """Pinned scan/catalogue metadata only; no new GO, credential stat/read or child."""
    r, refs = d.Metadata(), {}
    go = {"scan_go_ref": scan_go_ref, "prepared_ref": prepared_ref, "scan_receipt_ref": scan_receipt_ref}
    scan_go = r.json(go["scan_go_ref"])
    secret_files = scan_go["secret_files"]  # Paths only; this function never opens them.
    prepared, receipt = r.json(go["prepared_ref"]), r.json(go["scan_receipt_ref"])
    scan_root = d.absolute(scan_go["output_dir"])
    c.need(Path(go["prepared_ref"]["path"]) == scan_root / "PREPARED.json"
        and Path(go["scan_receipt_ref"]["path"]) == scan_root / "SCAN_RECEIPT.json", "fixed_scan_output_layout")
    c.need(scan_go["schema_version"] == "root-pinned-batches-scan-go-v1" and scan_go["issuer"] == "ROOT"
        and scan_go["approved"] is True and scan_go["action"] == "scan_only"
        and scan_go["driver_sha256"] == HELPERS["scan"][1]
        and scan_go["workspace"] == WORKSPACE and scan_go["expected_totals"] == EXPECTED
        and scan_go["secret_files"] == secret_files and scan_go["publication_authorized"] is False
        and scan_go["pack_authorized"] is False and scan_go["scan_all_batches_once"] is True
        and all(identity(scan_go[k]) == SCOPE[k] for k in SCOPE), "original_scan_go_binding")
    c.need(identity(prepared["root_go_ref"]) == identity(go["scan_go_ref"])
        and identity(receipt["root_go_ref"]) == identity(go["scan_go_ref"])
        and prepared["secret_source_count"] == receipt["secret_source_count"] == 3
        and receipt["all_batches_passed"] is True and receipt["metadata_and_private_specs_after_unchanged"] is True
        and all(receipt[k] == EXPECTED[k] for k in EXPECTED)
        and receipt["original_execution_complete"] is True and receipt["original_score_complete"] is True
        and receipt["implicit_retry_performed"] is False, "original_scan_not_complete")
    for ref in prepared["metadata_refs"]:
        # Each original source ref has its original pin, including >8 MiB inventory parts.
        d.Metadata().raw(ref, c.MEMBER)
        c.need(ref["path"] not in refs or refs[ref["path"]] == ref, "prepared_metadata_conflict")
        refs[ref["path"]] = ref
    collect(r, refs)
    del r
    candidates, index, seal, r = d.catalogue(SCOPE["inventory_ref"], SCOPE["index_ref"], SCOPE["seal_ref"], WORKSPACE, EXPECTED)
    c.need(seal["original_execution_complete"] is True and seal["original_score_complete"] is True, "original_completion_identity")
    collect(r, refs)
    del r
    c.need(len(prepared["batches"]) == len(receipt["batches"]) == len(candidates) == EXPECTED["batch_count"], "exact_batch_count")
    batches, targets, total = [], set(), 0
    for number, (item, prior, report) in enumerate(zip(candidates, prepared["batches"], receipt["batches"]), 1):
        name = "batch-%06d" % number
        c.need(prior["name"] == report["batch"] == name and prior["candidate_ref"] == item["candidate_ref"]
            and prior["file_count"] == item["file_count"] and prior["original_bytes"] == item["original_bytes"]
            and report["passed"] is True and type(report["validator_main_returncode"]) is int
            and report["validator_main_returncode"] == 0 and report["reason"] is None
            and report["finding_counts"] == report["advisory_counts"] == {}, "ordered_scan_batch_binding")
        r = d.Metadata()
        c.need(Path(prior["private_spec_ref"]["path"]) == scan_root / "specs" / (name + ".json"), "private_spec_layout")
        spec = r.json(prior["private_spec_ref"], d.b.MANIFEST_BYTES)
        expected_spec = {**item["spec"], "approved": True, "candidate": False,
                         "required_stages": [a["id"] for a in item["spec"]["artifacts"]]}
        c.need(spec == expected_spec, "private_spec_original_rows_changed")
        c.need(set(report["reports"]) == {"status", "manifest.json", "lock.json"}, "exact_original_reports")
        values = {}
        for key, ref in report["reports"].items():
            expected_path = scan_root / (name + ".status.json") if key == "status" else scan_root / name / key
            c.need(Path(ref["path"]) == expected_path, "original_report_layout")
            values[key] = r.json(ref)
        scan, lock, status = values["manifest.json"], values["lock.json"], values["status"]
        c.need(lock == spec and scan["safe_to_stage"] is True and scan["findings"] == scan["advisories"] == []
            and scan["secret_sources_checked"] == 3 and scan["validator_sha256"] == c.SCANNER_SHA
            and scan["all_required_stages_present"] is True
            and scan["spec_canonical_sha256"] == hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
            and status["safe_to_stage"] is True and status["findings"] == 0
            and status["publication_performed"] is False, "original_scan_manifest_lock_status")
        rows = []
        for item_artifact in spec["artifacts"]:
            row = item_artifact["files"][0]
            rows.append({"artifact_id": item_artifact["id"], "source": item_artifact["source"], "target": item_artifact["target"],
                "path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]})
            c.need(item_artifact["target"] not in targets, "duplicate_global_original")
            targets.add(item_artifact["target"]); total += row["bytes"]
        c.need(rows == scan["files"] and len(rows) == status["files"] == prior["file_count"]
            and sum(x["bytes"] for x in rows) == scan["total_bytes"] == prior["original_bytes"], "complete_batch_scan_rows")
        collect(r, refs)
        batches.append({"batch_id": name, "spec_ref": prior["private_spec_ref"], "original_scan_ref": report["reports"]["manifest.json"], "rows": rows})
    c.no_path_prefixes(targets)
    c.need((len(targets), total) == (EXPECTED["file_count"], EXPECTED["original_bytes"]), "complete_original_union")
    recheck(refs)
    return scan_go, batches, refs, Path(seal["run_root"])


def preflight(go_ref, secret_files):
    r, refs = d.Metadata(), {}
    go = r.json(go_ref)
    fields = {"schema_version", "issuer", "approved", "action", "driver_sha256", "workspace", "output_dir",
        "python", "expected_totals", "inventory_ref", "index_ref", "seal_ref", "scan_go_ref", "prepared_ref",
        "scan_receipt_ref", "secret_files", "tool_refs", "max_parallel_batches", "publication_authorized", "network_authorized"}
    c.need(set(go) == fields and go["schema_version"] == "root-glm-original-delivery-go-v1"
        and go["issuer"] == "ROOT" and go["approved"] is True
        and go["action"] == "pack_and_local_restore_exact_36_batches"
        and go["workspace"] == WORKSPACE and go["python"] == "/usr/bin/python3"
        and go["expected_totals"] == EXPECTED and type(go["max_parallel_batches"]) is int
        and go["max_parallel_batches"] == 1 and go["publication_authorized"] is False
        and go["network_authorized"] is False and go["tool_refs"] == TOOL_REFS, "exact_root_delivery_go")
    c.need(secret_files == go["secret_files"], "caller_secret_paths_mismatch")
    d.check_keys(secret_files)  # Only canonical path, file type, owner and mode; never values.
    for key, ref in SCOPE.items():
        c.need(identity(go[key]) == ref, "fixed_glm_scope")
    output = c.fresh(d.absolute(go["output_dir"]))
    r.raw({"path": str(Path(__file__).resolve()), "sha256": go["driver_sha256"]})
    for ref in TOOL_REFS + [{"path": str(p), "sha256": h} for p, h in HELPERS.values()]:
        r.raw(ref)
    collect(r, refs)
    scan_go, batches, scan_refs, run_root = scan_metadata(go["scan_go_ref"], go["prepared_ref"], go["scan_receipt_ref"])
    c.need(scan_go["secret_files"] == secret_files, "scan_delivery_secret_paths_differ")
    for path, ref in scan_refs.items():
        c.need(path not in refs or refs[path] == ref, "scan_delivery_metadata_conflict")
        refs[path] = ref
    protected = [run_root, Path(scan_go["output_dir"]), HERE, *[Path(p) for p in refs], *[Path(p) for p in secret_files]]
    c.need(all(output != p and p not in output.parents and output not in p.parents for p in protected), "output_input_overlap")
    recheck(refs)
    return go, batches, refs, output


def natural_wait(child, state):
    """At most two blocking waits, then one poll; never infer a missing exit code."""
    pending = None
    for _ in range(2):
        state["wait_attempts"] += 1
        try:
            code = child.wait()
            c.need(type(code) is int, "invalid_child_exit_status")
            state.update(confirmed_reaped=True, exit_code=code, closure_evidence="wait")
            return pending
        except BaseException as error:
            state["wait_had_exception"] = True
            if pending is None or isinstance(error, (KeyboardInterrupt, SystemExit)):
                pending = error
    state["poll_attempted"] = True
    try:
        code = child.poll()
        if type(code) is int:
            state.update(confirmed_reaped=True, exit_code=code, closure_evidence="final_poll")
    except BaseException as error:
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            pending = error
    return pending


def safe_invoke(argv, stage, work, helper, children):
    """Keep logs open until bounded natural wait even if started metadata fails."""
    began, clock = helper.utc(), helper.time.perf_counter()
    state, pending, layer = None, None, "open_logs"
    stdout, stderr = work / (stage + ".stdout.json"), work / (stage + ".stderr.log")
    result = {}
    try:
        with stdout.open("xb") as out, stderr.open("xb") as err:
            layer = "popen"
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(helper.ROOT / "scratch"))
            child = helper.subprocess.Popen(argv, stdout=out, stderr=err, stdin=helper.subprocess.DEVNULL, env=env)
            state = {"pid": child.pid, "stage": stage, "work": str(work), "confirmed_reaped": False,
                "exit_code": None, "closure_evidence": None, "wait_attempts": 0, "poll_attempted": False,
                "wait_had_exception": False, "failure_layers": []}
            children.append(state)
            try:
                layer = "started_receipt"
                helper.write_new(work / (stage + ".started.json"), {"pid": child.pid, "started_utc": began,
                    "stage": stage, "core_dump_limit": list(resource.getrlimit(resource.RLIMIT_CORE)), "argv": argv})
            except BaseException as error:
                pending = error
                state["failure_layers"].append(layer)
            finally:
                waited_error = natural_wait(child, state)
                if waited_error is not None:
                    state["failure_layers"].append("wait_exception")
                    if pending is None or isinstance(waited_error, (KeyboardInterrupt, SystemExit)):
                        pending = waited_error
            layer = "close_logs"
        layer = "log_refs"
        result.update(stdout_ref=helper.observed(stdout), stderr_ref=helper.observed(stderr))
    except BaseException as error:
        if pending is None or isinstance(error, (KeyboardInterrupt, SystemExit)):
            pending = error
        if state is not None:
            state["failure_layers"].append(layer)
    if state is None:
        raise pending
    result.update(stage=stage, pid=state["pid"], exit_code=state["exit_code"], started_utc=began,
        finished_utc=helper.utc(), elapsed_seconds=helper.time.perf_counter() - clock,
        wait_returned=state["closure_evidence"] == "wait", confirmed_reaped=state["confirmed_reaped"],
        closure_evidence=state["closure_evidence"], failure_layers=list(state["failure_layers"]))
    try:
        helper.write_new(work / (stage + ".exit.json"), result)
    except BaseException as error:
        state["failure_layers"].append("exit_receipt")
        if pending is None or isinstance(error, (KeyboardInterrupt, SystemExit)):
            pending = error
    if not state["confirmed_reaped"]:
        helper.STOP.set()
        state["failure_layers"].append("closure_unknown")
        if not isinstance(pending, (KeyboardInterrupt, SystemExit)):
            pending = c.DeliveryError("child_closure_unknown_no_retry")
    if pending is not None:
        helper.STOP.set()
        raise pending
    try:
        helper.require(state["exit_code"] == 0, stage + "_nonzero_exit")
        body = json.loads(stdout.read_bytes())
        helper.require(body.get("passed") is True and body.get("publication_performed") is False, stage + "_not_passed")
        return body, result
    except BaseException:
        state["failure_layers"].append("nonzero_or_stdout_validation")
        helper.STOP.set()
        raise


def execute(go_ref, secret_files):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0)); os.umask(0o077)
    go, batches, refs, output = preflight(go_ref, secret_files)
    helper = load_helper("batch")
    helper.ROOT, helper.STOP = output, threading.Event()
    children = []
    helper.invoke = lambda argv, stage, work: safe_invoke(argv, stage, work, helper, children)
    output.mkdir(mode=0o700)
    for name in ("batches", "scratch"):
        (output / name).mkdir(mode=0o700)
    c.write_new(output / "PREFLIGHT.json", c.encoded({"passed": True, "go_ref": go_ref, "metadata_refs": list(refs.values()),
        "expected_totals": EXPECTED, "helper_root_rebound_to": str(output), "old_preflight_or_main_called": False,
        "old_go_or_payload_read": False, "helper_sha256": HELPERS["batch"][1], "secret_values_read_by_operator": False}))
    c.write_new(output / "STARTED.json", c.encoded({"pid": os.getpid(), "started_utc": helper.utc(), "core_dump_limit": 0,
        "max_parallel_batches": 1, "go_ref": go_ref, "operator_sha256": go["driver_sha256"], "publication_performed": False}))
    results, interruption = [], None
    for batch in batches:
        d.check_keys(secret_files)
        try:
            result = helper.batch_run(go, batch, c)  # Only invoke is replaced; pack/restore logic unchanged.
        except BaseException as error:
            interruption = error
            helper.STOP.set()
            result = {"batch_id": batch["batch_id"], "passed": False, "failure_layer": "batch_interrupted",
                      "publication_performed": False, "remote_restore_performed": False}
        result["retained_child_exit_refs"] = [helper.observed(p) for p in (
            output / "batches" / batch["batch_id"] / "pack.exit.json",
            output / "batches" / batch["batch_id"] / "restore.exit.json") if p.exists()]
        results.append(result)
        if not result["passed"] or helper.STOP.is_set():
            break
    stable = True
    try:
        recheck(refs)
    except Exception:
        stable = False
    unresolved = [x["pid"] for x in children if not x["confirmed_reaped"]]
    passed = len(results) == len(batches) and all(x["passed"] for x in results) and stable and not unresolved
    if passed:
        try:
            # Final cross-batch source/restore recheck, not merely earlier per-batch success.
            for batch, result in zip(batches, results):
                restored = output / "batches" / batch["batch_id"] / "restore"
                c.need(c.tree(restored / "payload") == {r["target"] for r in batch["rows"]}, "final_path_set")
                for row in batch["rows"]:
                    expected = row["bytes"], row["sha256"]
                    c.need(c.stream_hash(Path(WORKSPACE) / row["source"]) == expected
                        and c.stream_hash(restored / "payload" / row["target"]) == expected, "final_original_or_restored_changed")
                for key, binding, root in (("pack_complete_ref", {"kind": "bundle", "index_sha256": result["index_ref"]["sha256"]}, restored.parent / "bundle"),
                    ("restore_complete_ref", {"kind": "restored-originals", "input_sha256": result["index_ref"]["sha256"], "single_archive": False}, restored)):
                    c.need(c.verify_completion(root, binding) == result[key]["sha256"], "final_completion_changed")
        except Exception:
            passed = False
    try:
        recheck(refs)
    except Exception:
        stable = passed = False
    summary = {"schema_version": "glm-original-local-delivery-operator-v1", "passed": passed, "batches": results,
        "expected_totals": EXPECTED, "finished_batches": len(results), "unstarted_batch_ids": [b["batch_id"] for b in batches[len(results):]],
        "file_count": sum(x.get("file_count", 0) for x in results), "original_bytes": sum(x.get("original_bytes", 0) for x in results),
        "compressed_bytes": sum(x.get("compressed_bytes", 0) for x in results), "shards": sum(x.get("shards", 0) for x in results),
        "metadata_after_unchanged": stable, "whole_final_source_restore_path_bytes_sha_complete": passed,
        "original_execution_complete": True, "original_score_complete": True, "local_workers": None if unresolved else 0,
        "children": children, "unresolved_started_pids": unresolved, "all_started_children_reaped": not unresolved,
        "stop_new_join_policy": True, "implicit_retry_performed": False, "posix_metadata_preserved": False,
        "network_performed": False, "publication_performed": False, "remote_restore_performed": False,
        "full_project_complete": False, "finished_utc": helper.utc()}
    c.write_new(output / "SUMMARY.json", c.encoded(summary)); c.sync_directory(output)
    if interruption is not None:
        raise interruption
    return summary


def main(argv=None):
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            raise c.DeliveryError("invalid_arguments")
    try:
        parser = Parser(description=__doc__)
        parser.add_argument("--go", required=True); parser.add_argument("--go-sha256", required=True)
        parser.add_argument("--secret-file", action="append", required=True)
        args = parser.parse_args(argv)
        result = execute({"path": args.go, "sha256": args.go_sha256}, args.secret_file)
        print(json.dumps({k: result[k] for k in ("passed", "finished_batches", "publication_performed")}))
        return 0 if result["passed"] else 2
    except BaseException as error:
        print(json.dumps({"passed": False, "rule": "glm_original_delivery_failed_no_retry", "publication_performed": False}))
        return 130 if isinstance(error, KeyboardInterrupt) else 2


if __name__ == "__main__":
    raise SystemExit(main())
