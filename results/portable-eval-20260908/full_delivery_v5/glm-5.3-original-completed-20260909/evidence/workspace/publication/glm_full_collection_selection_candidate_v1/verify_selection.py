#!/usr/bin/env python3
"""Closed GLM metadata verification and unapproved selection projection; stdout only."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from datetime import datetime, timezone

W = Path("/lustrefs/users/chufan.shi/codex_space_tn")
P = W / "publication"
OP = W / "portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909"
R = P / "glm_formal_original_local_delivery_v1"
C = P / "glm_controls_local_delivery_v2"
OUT = P / "glm_full_collection_selection_candidate_v1"
RAW_INVENTORY = P / "glm_formal_original_scope_candidate_v1/candidate/inventory.json"
CONTROL_INVENTORY = OP / "glm_public_controls_subset_v1/inventory.json"
PINS = {
    R / "SUMMARY.json": "1b717138400e03811d69df4f15a95804def484cf83884037c62629870ab1a5e3",
    R / "ROOT_OPERATOR_COMPLETION.json": "fae187007ea6ad13d6abd4533273df3b8dcd3f9d20bc1fd3551049f3ea41a5a5",
    RAW_INVENTORY: "78610fabac42cf3606dca00a19a3148647eb9eaa413843658bc38f504ec47489",
    CONTROL_INVENTORY: "3c321f8bbecba16cb3570bd6be04ccdc3956fdf857ed8dbb669becdd9a66726a",
    C / "ROOT_LOCAL_PROOF.json": "4ef732ce297aaf31c948e6a8ba7f114e67d4143586ab165615a3caee488adebe",
    C / "OPERATOR_COMPLETION.json": "1551eb73c38405d8b4247fdf200d44a0e94aa8bd7c93dedd6fdd51511e9f6dc5",
    P / "glm_controls_local_verification_v2/ACTUAL_BYTE_VERIFICATION.json": "ef89fafeec3ef9d64015ac6a7401325ea03848442664e74923df5d14e8f2e16f",
    P / "glm_controls_local_verification_v2/CLI_RECEIPT.json": "c22570b27dbd31b8b2d516a51309f27ad8499686fae52f10c62e96e5566b930c",
    OP / "glm_public_controls_subset_v1/ROOT_SCOPE_DECISION.json": "90df6e9b1301211278c290676c7ee387398c487a527c2df6851a5a0146f473c3",
    P / "glm_formal_original_delivery_candidate_v1/operator.py": "2124e9929f29531d48960ece983eea10d493660244bfc1dc8938696ebfd79d3d",
    P / "restart_v5_closed_local_delivery_v1/operator.py": "979fd024d739eb927825d156048cbd6a1850fb27ddc6a5c5677abba1e4d7d497",
    P / "glm_formal_collection_assembly_candidate_v2/assemble.py": "5255f2f390632bd9686ce379f0868fac8ddddc0e8c2304000ee017f236d6f9f6",
    P / "shard_delivery_candidate_v2/common.py": "7147524d5799dc1264f088518db19251c5f906bc2da501854ce279f56d73263e",
}
RESULT_PINS = {
    "batch-000001": "437def01ff1903c485d9eff81204de35146eb43b7eac336c88b299c72c222225",
    "batch-000002": "dbd090819372b5b711208c6fbd6c691164612c6965a881c941111046793c0ea2",
    "batch-000003": "4472dfd746c1a6e166ea72afc52038b0e3e87689077e66cdd15589c8cdaff561",
    "batch-000004": "049508c31e96016a0b5e8410a39063f9b49080c3fa3a04c7cdada2c0356284eb",
    "batch-000005": "b3136990fe1b4a2d544c88466f5b0b39c6872b0a8e12b88232717ed05c047f3d",
    "batch-000006": "dae46662b1b0e40ee94f3ba9abce22253feb161671dac3c36abedb5f54475bb8",
    "batch-000007": "df3381e7ca88e811a45bfe793865a938421618674a56d23c242a227efa0270d4",
    "batch-000008": "7e0a64ef19f51395db0e21c7ae4c7ee408b45a534e110d5b0ee0e7a4a4ad18c1",
    "batch-000009": "11027fd4352b0f0cc17a3195a3e88150904c695c9725448beed04ff8c0f41175",
    "batch-000010": "cdfda141ab84ad4743ad3d919b5f34f3def72efc6bf8cea2073be47f73bfa4f6",
    "batch-000011": "552f2601e57af8869d99f0e544280f1b38e3720ad9fb94bd08b8920c3e04bdca",
    "batch-000012": "53cb4808249706a8dfbe86603f9934a3cdbd3104d881d738a104aea4b1934862",
    "batch-000013": "a217b0190a1a97880adf374cb9192663a38e05e287bf6871626ed6e40ff30d60",
    "batch-000014": "74bcfb897ffb8bb6662969626271c649ce44185577b3e92f6900f4f23967b1ad",
    "batch-000015": "4a7cde37da180a88e3d23dca640ae0acd521ce2c67ee9ccdc4fd1f09abc43d0d",
    "batch-000016": "e6cd53dea5521b34a148d64cd7a4f70b271950881f1435ce34f7cf67dd9887f7",
    "batch-000017": "63e3a08eaaf55821badd8368807838d0c6938fa4298f908d4f73c74524c47bad",
    "batch-000018": "0039c5d49a6387a9a11355bef859aa841f83de2a57925aa5e6d9c09ae27af776",
    "batch-000019": "9f897d02834f7def2ff16f450d6c1a400f0d7cd093b774a907276951eebdfb6f",
    "batch-000020": "31ebc5f753e8a3618fe3ff57d586fdb452aa1f3a2bc73046c47689ad15f0c714",
    "batch-000021": "e79b407befd28689a776ba0db3e0a11e832c96cbcd68cfab988199f51e314763",
    "batch-000022": "2a68369dc54e6d6d48b88196cf3b87710e9f48a5a05bbe28b052645c7611d2aa",
    "batch-000023": "3a1c3f35b55f4da60e5e3d3ecf5e5ed2f6de89724fcb4cf5ac1e582007a8cca9",
    "batch-000024": "4e099cd83e80a7d703eb9fcbd6f132ac524ceebca251bbbe0b3d4e7fdfe30b55",
    "batch-000025": "03e3d00381e0f2ac3e1162e9921aaee4164320e4898cfabf0af45e2d289fc719",
    "batch-000026": "1e1ec1d744fd62398bab926cca9e504b8f4bf848a6d33c0c4dc935f89cf6898e",
    "batch-000027": "8a0a97d98a44ed9cd3d0ca1363d6e06f05d054cb35a090acac0a3c632a990a15",
    "batch-000028": "7e073380900f6eb4de677024a94279f019166d9fc0f92dac983389fe5908400b",
    "batch-000029": "d489ebaa6fc3c694f692b887332a94cdd53f2f1ee4cf1257366dcd58c8072cb2",
    "batch-000030": "9b088246fd9bc5fbdaab132429a623bb5b4c9687c6145f1da2dda13161cd8e39",
    "batch-000031": "fcc4b41453b8bd64ae1e7e17210dc25c7819bfb6cbbf15b3aefa2427224b13d8",
    "batch-000032": "99adcd0fdf9bfd6edaf595e269ca246246a94e454e70ad6dc063e72766c57b48",
    "batch-000033": "ccf4d1979aae54aaf65450e327d0214bbbf2862d0ec7476b4d885d6a8ab2e31f",
    "batch-000034": "b7279698c2d3c7b8923fc6807676f5afc762c9acd0c38f29cebb3f601695a9c1",
    "batch-000035": "242d1a6fe8c1475d7dccff93b2e03f3042e5cb1b45360891294d5f8efe30ca48",
    "batch-000036": "11d8158b540e4712c7f5ec769b76838c26b64554860334d8fc1335c4ab81eb74"
}
RAW_COUNTS = {"batch-%06d" % i: 2000 if i < 36 else 520 for i in range(1, 37)}
READS = {}
STAGE = "initial"

def need(value, code):
    if not value:
        raise ValueError(code)

def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    def reject(_):
        raise ValueError("nonfinite_json")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)

def relative(value):
    need(type(value) is str and value and len(value.encode()) <= 4096, "relative_type_length")
    path = PurePosixPath(value)
    need(value != "." and not path.is_absolute() and path.as_posix() == value and
         all(x not in ("", ".", "..") for x in path.parts) and
         "\\" not in value and not any(ord(c) < 32 for c in value), "relative_path")
    return path

def integer(value, minimum=0):
    need(type(value) is int and value >= minimum, "exact_integer")
    return value

def shape_ref(ref, expected_path):
    need(type(ref) is dict and set(ref) == {"path", "bytes", "sha256"}, "ref_schema")
    need(ref["path"] == str(expected_path), "ref_exact_path")
    integer(ref["bytes"])
    need(type(ref["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", ref["sha256"]), "ref_sha")
    return ref

def signature(info):
    return {k: str(getattr(info, k)) for k in
            ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode", "st_nlink")}

def boundary(path):
    need(path.is_absolute() and ".." not in path.parts, "absolute_path")
    text = str(path)
    need(not text.endswith((".tar", ".tar.gz", ".tgz", ".gz"))
         and "/restore/payload/" not in text and "/private/" not in text
         and "/formal_runs/" not in text, "forbidden_original_archive_key_path")
    if "payload" in path.parts:
        need(path.name in ("INDEX.json", "SOURCE_SCAN.json") or
             (path.parent.name == "indexes" and re.fullmatch("part-[0-9]{6}\\.json", path.name)),
             "payload_directory_metadata_only")
    for parent in [*reversed(path.parents), path]:
        need(not stat.S_ISLNK(parent.lstat().st_mode), "symlink_component")

def digest_file(path, limit):
    boundary(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, "regular_metadata_limit")
    parts, size, digest = [], 0, hashlib.sha256()
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        opened = os.fstat(stream.fileno())
        for block in iter(lambda: stream.read(1024**2), b""):
            size += len(block)
            need(size <= limit, "metadata_grew")
            digest.update(block)
            parts.append(block)
        after = os.fstat(stream.fileno())
    need(signature(before) == signature(opened) == signature(after) == signature(path.lstat())
         and size == before.st_size, "metadata_unstable_read")
    return b"".join(parts), {"path": str(path), "bytes": size, "sha256": digest.hexdigest()}, signature(before)

def read(path, expected_sha=None, expected_bytes=None, parse=True, group="metadata"):
    need(path not in READS, "duplicate_metadata_read")
    limit = 32 * 1024**2 if path == RAW_INVENTORY else 8 * 1024**2
    raw, ref, state = digest_file(path, limit)
    expected_sha = expected_sha or PINS.get(path)
    need(expected_sha is None or ref["sha256"] == expected_sha, "external_sha_mismatch")
    need(expected_bytes is None or ref["bytes"] == expected_bytes, "external_size_mismatch")
    READS[path] = {"ref": ref, "stat": state, "limit": limit, "group": group}
    return strict_json(raw) if parse else ref

def pinned(ref, path, group="metadata", parse=True):
    shape_ref(ref, path)
    return read(path, ref["sha256"], ref["bytes"], parse, group)

def rows(value):
    need(type(value) is list, "rows_list")
    result = {}
    for row in value:
        need(type(row) is dict and set(row) == {"path", "bytes", "sha256"}, "row_schema")
        name = str(relative(row["path"]))
        need(name not in result and integer(row["bytes"]) <= 100 * 1024**2
             and type(row["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", row["sha256"]), "row_identity")
        result[name] = row
    need(value == [result[n] for n in sorted(result)], "sorted_rows")
    return result

def row_digest(mapping):
    digest = hashlib.sha256()
    for name in sorted(mapping):
        digest.update(encoded(mapping[name]))
    return digest.hexdigest()

def complete(mapping, binding):
    return {"schema": "completed-directory-v1", "complete": True, "payload": "payload",
            "binding": binding, "file_count": len(mapping),
            "bytes": sum(r["bytes"] for r in mapping.values()), "inventory_sha256": row_digest(mapping)}

def bundle_metadata(root, index_ref, complete_ref, original_rows):
    shape_ref(index_ref, root / "payload/INDEX.json")
    shape_ref(complete_ref, root / "COMPLETE.json")
    index = pinned(index_ref, root / "payload/INDEX.json", "bundle_index")
    marker = pinned(complete_ref, root / "COMPLETE.json", "bundle_complete")
    need(index["schema"] == "shard-delivery-v1" and type(index["shards"]) is list
         and 0 < len(index["shards"]) <= 4096 and index["additive_scan_advisories"] == [], "bundle_index_schema")
    need(index["limits"] == {"compressed_bytes": 48 * 1024**2, "expanded_bytes": 256 * 1024**2,
                             "member_bytes": 100 * 1024**2, "files_per_shard": 256}, "frozen_limits")
    need(integer(index["file_count"], 1) == len(original_rows)
         and integer(index["original_bytes"]) == sum(r["bytes"] for r in original_rows.values()), "bundle_original_totals")
    need(index["known_secret_sources_checked"] == 3 and type(index["known_secret_sources_checked"]) is int,
         "preserved_original_three_key_scan")
    entries = {"INDEX.json": {**index_ref, "path": "INDEX.json"}}
    union, archive_bytes, expanded_bytes = {}, 0, 0
    for n, shard in enumerate(index["shards"], 1):
        page = "indexes/part-%06d.json" % n
        archive = "shards/part-%06d.tar.gz" % n
        need(shard["index"] == page and shard["archive"] == archive, "canonical_shard_paths")
        page_ref = {"path": str(root / "payload" / page), "bytes": shard["index_bytes"],
                    "sha256": shard["index_sha256"]}
        contents = pinned(page_ref, root / "payload" / page, "member_index")
        need(contents["schema"] == "shard-members-v1", "member_page_schema")
        member_rows = rows(contents["files"])
        need(0 < integer(shard["file_count"]) <= 256 and len(member_rows) == shard["file_count"]
             and not set(member_rows).intersection(union), "member_union")
        need(integer(shard["bytes"], 1) <= 48 * 1024**2
             and integer(shard["expanded_bytes"]) <= 256 * 1024**2, "archive_caps")
        need(type(shard["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", shard["sha256"]), "archive_declared_sha")
        union.update(member_rows)
        entries[page] = {"path": page, "bytes": page_ref["bytes"], "sha256": page_ref["sha256"]}
        entries[archive] = {"path": archive, "bytes": shard["bytes"], "sha256": shard["sha256"]}
        archive_bytes += shard["bytes"]
        expanded_bytes += shard["expanded_bytes"]
    need(union == original_rows, "member_union_not_exact_comparison")
    source = index["source_scan"]
    need(source["path"] == "SOURCE_SCAN.json", "source_scan_name")
    source_ref = {"path": str(root / "payload/SOURCE_SCAN.json"),
                  "bytes": source["bytes"], "sha256": source["sha256"]}
    pinned(source_ref, root / "payload/SOURCE_SCAN.json", "source_scan_metadata", parse=False)
    entries["SOURCE_SCAN.json"] = {**source_ref, "path": "SOURCE_SCAN.json"}
    need(marker == complete(entries, {"kind": "bundle", "index_sha256": index_ref["sha256"]}),
         "bundle_complete_metadata_inventory")
    return {"shards": len(index["shards"]), "compressed_bytes": archive_bytes,
            "expanded_bytes_from_index": expanded_bytes}

def verified_exit(value, child, stage, work):
    need(value["stage"] == child["stage"] == stage and child["work"] == str(work), "child_stage_work")
    need(integer(value["pid"], 1) == integer(child["pid"], 1), "child_pid")
    need(integer(value["exit_code"]) == integer(child["exit_code"]) == 0
         and value["confirmed_reaped"] is True and child["confirmed_reaped"] is True
         and value["closure_evidence"] == child["closure_evidence"] == "wait"
         and value["wait_returned"] is True and integer(child["wait_attempts"], 1) == 1
         and child["poll_attempted"] is False and child["wait_had_exception"] is False
         and value["failure_layers"] == child["failure_layers"] == [], "clean_real_wait_exit")
    for suffix, key in (("stdout.json", "stdout_ref"), ("stderr.log", "stderr_ref")):
        shape_ref(value[key], work / (stage + "." + suffix))
    # The log refs are validated structurally; no logs or argv/started receipts are read.

def main():
    global STAGE
    started = datetime.now(timezone.utc).isoformat()
    STAGE = "anchors_and_actual_exit"
    need(Path(__file__).absolute() == OUT / "verify_selection.py", "own_script_path")
    read(OUT / "verify_selection.py", parse=False, group="tool")
    summary = read(R / "SUMMARY.json", expected_bytes=161128, group="root_anchor")
    operator = read(R / "ROOT_OPERATOR_COMPLETION.json", expected_bytes=2374, group="root_anchor")
    need(operator["issuer"] == "ROOT" and operator["schema_version"] == "root-glm-original-local-delivery-direct-cli-exit-v1"
         and integer(operator["actual_exit_code"]) == 0 and integer(operator["session_id"]) == 13206
         and integer(operator["operator_invocations"], 1) == 1 and operator["natural_completion"] is True
         and operator["root_cancel_or_interrupt_performed"] is False and operator["stdout_passed"] is True
         and operator["stdout_finished_batches"] == 36, "actual_root_exit")
    need(operator["completion_tool_result"]["chunk_id"] == "895e99"
         and integer(operator["completion_tool_result"]["exit_code"]) == 0
         and operator["initial_tool_result"]["chunk_id"] == "2155fa", "root_actual_process_refs")
    for path in PINS:
        if path.suffix == ".py":
            read(path, parse=False, group="tool")
    need(operator["operator_ref"] == {"path": str(P / "glm_formal_original_delivery_candidate_v1/operator.py"),
                                     "sha256": PINS[P / "glm_formal_original_delivery_candidate_v1/operator.py"]},
         "actual_driver_pin")
    need(summary["schema_version"] == "glm-original-local-delivery-operator-v1"
         and summary["expected_totals"] == {"batch_count": 36, "file_count": 70520, "original_bytes": 3242213793}
         and integer(summary["finished_batches"]) == 36 and integer(summary["file_count"]) == 70520
         and integer(summary["original_bytes"]) == 3242213793 and integer(summary["local_workers"]) == 0
         and integer(summary["shards"]) == 283 and integer(summary["compressed_bytes"]) == 746949323,
         "exact_summary_totals")
    for key in ("passed", "metadata_after_unchanged", "whole_final_source_restore_path_bytes_sha_complete",
                "original_execution_complete", "original_score_complete", "all_started_children_reaped",
                "stop_new_join_policy"):
        need(summary[key] is True, "summary_true_identity")
    for key in ("implicit_retry_performed", "posix_metadata_preserved", "network_performed",
                "publication_performed", "remote_restore_performed", "full_project_complete"):
        need(summary[key] is False, "summary_false_identity")
    need(summary["unresolved_started_pids"] == summary["unstarted_batch_ids"] == []
         and len(summary["batches"]) == 36 and len(summary["children"]) == 72, "exact_closure_lists")
    expected_pairs = [(str(R / "batches" / bid), stage) for bid in RAW_COUNTS for stage in ("pack", "restore")]
    need([(x["work"], x["stage"]) for x in summary["children"]] == expected_pairs, "72_ordered_children")
    need([x["batch_id"] for x in summary["batches"]] == list(RAW_COUNTS), "36_ordered_batches")
    raw_inventory = read(RAW_INVENTORY, expected_bytes=23061643, group="scope_inventory")
    controls_inventory = read(CONTROL_INVENTORY, expected_bytes=320562, group="scope_inventory")
    for inventory in (raw_inventory, controls_inventory):
        need(inventory["schema_version"] == "sealed-publication-file-inventory-v1"
             and inventory["issuer"] == "ROOT" and inventory["sealed"] is True, "sealed_inventory")
    raw_expected, controls_expected = rows(raw_inventory["files"]), rows(controls_inventory["files"])
    need((len(raw_expected), sum(x["bytes"] for x in raw_expected.values())) == (70520, 3242213793), "raw_scope")
    need((len(controls_expected), sum(x["bytes"] for x in controls_expected.values())) == (1114, 224903100)
         and not set(raw_expected).intersection(controls_expected), "controls_scope_disjoint")

    STAGE = "36_batch_metadata_and_72_real_exits"
    proposed, union, batch_receipts = [], {}, []
    for pos, summary_batch in enumerate(summary["batches"]):
        bid = summary_batch["batch_id"]; work = R / "batches" / bid
        result = read(work / "RESULT.json", RESULT_PINS[bid], group="batch_result")
        need(result == {k: v for k, v in summary_batch.items() if k != "retained_child_exit_refs"},
             "summary_vs_disk_result")
        need(result["passed"] is True and result["whole_originals_and_restored_verified"] is True
             and result["publication_performed"] is False and result["remote_restore_performed"] is False
             and integer(result["file_count"], 1) == RAW_COUNTS[bid], "batch_pass_counts")
        comparison = pinned(result["whole_file_comparison_ref"], work / "WHOLE_FILE_COMPARISON.json",
                            "whole_file_comparison")
        need(comparison["all_source_and_restored_bytes_sha_match"] is True
             and comparison["full_restored_path_set_equal"] is True
             and comparison["posix_metadata_preserved"] is False, "whole_file_flags")
        originals = rows(comparison["rows"])
        need(len(originals) == result["file_count"]
             and sum(x["bytes"] for x in originals.values()) == integer(result["original_bytes"])
             and not set(originals).intersection(union), "batch_comparison_totals")
        union.update(originals)
        need(len(summary_batch["retained_child_exit_refs"]) == 2, "two_retained_exits")
        for j, stage in enumerate(("pack", "restore")):
            child = summary["children"][2 * pos + j]
            exit_ref = summary_batch["retained_child_exit_refs"][j]
            exit_value = pinned(exit_ref, work / (stage + ".exit.json"), "child_exit")
            need(exit_value == result[stage + "_exit"], "exit_receipt_projection")
            verified_exit(exit_value, child, stage, work)
        restored_complete = pinned(result["restore_complete_ref"], work / "restore/COMPLETE.json", "restore_complete")
        need(restored_complete == complete(originals, {"kind": "restored-originals",
             "input_sha256": result["index_ref"]["sha256"], "single_archive": False}), "restore_complete_rows")
        stats = bundle_metadata(work / "bundle", result["index_ref"], result["pack_complete_ref"], originals)
        need(stats["shards"] == integer(result["shards"], 1)
             and stats["compressed_bytes"] == integer(result["compressed_bytes"]), "batch_archive_metadata_totals")
        proposed.append({"bundle_id": bid, "category": "original-completed", "bundle_root": str(work / "bundle"),
            "index_ref": result["index_ref"], "complete_ref": result["pack_complete_ref"],
            "file_count": result["file_count"], "original_bytes": result["original_bytes"],
            "operator_ref": READS[work / "RESULT.json"]["ref"],
            "local_proof_ref": result["whole_file_comparison_ref"],
            "local_verification": {"pack_exit_code": result["pack_exit"]["exit_code"],
                "restore_exit_code": result["restore_exit"]["exit_code"],
                "complete_original_and_restored_path_bytes_sha_match":
                    comparison["all_source_and_restored_bytes_sha_match"] and comparison["full_restored_path_set_equal"],
                "all_started_children_reaped": all(summary["children"][2 * pos + j]["confirmed_reaped"] is True for j in (0, 1))}})
        batch_receipts.append({"batch_id": bid, "file_count": len(originals), "original_bytes": result["original_bytes"],
                               "row_sha256": row_digest(originals), **stats})
    need(union == raw_expected and sum(x["shards"] for x in batch_receipts) == 283
         and sum(x["compressed_bytes"] for x in batch_receipts) == 746949323, "global_raw_union_totals")

    STAGE = "controls_existing_closed_proofs"
    proof = read(C / "ROOT_LOCAL_PROOF.json", group="controls_proof")
    cop = read(C / "OPERATOR_COMPLETION.json", group="controls_proof")
    need(proof["issuer"] == cop["issuer"] == "ROOT" and proof["passed"] is True and cop["passed"] is True
         and proof["file_count"] == 1114 and proof["original_bytes"] == 224903100
         and proof["complete_original_and_restored_path_bytes_sha_match"] is True
         and proof["exact_restored_file_and_directory_sets_before_and_after"] is True
         and proof["bundle_member_union_matches_sealed_inventory"] is True
         and proof["all_started_children_reaped"] is True and cop["all_started_children_reaped"] is True
         and proof["public_nonexperimental_invocation_omission_preserved"] is True
         and proof["public_audit_reference_chain_fully_closed"] is False, "controls_proof_pass")
    need(proof["inventory_ref"] == READS[CONTROL_INVENTORY]["ref"]
         and proof["bundle_root"] == str(C / "bundle") and proof["restored_root"] == str(C / "restore"), "controls_scope_refs")
    for stage in ("pack", "restore"):
        need(integer(proof[stage + "_exit_code"]) == 0
             and proof[stage + "_actual_process"] == cop[stage]["actual_process"]
             and integer(cop[stage]["actual_process"]["exit_code"]) == 0
             and cop[stage]["stdout"]["passed"] is True, "controls_actual_exit")
    byte_proof = pinned(proof["independent_complete_byte_verification_ref"],
                        P / "glm_controls_local_verification_v2/ACTUAL_BYTE_VERIFICATION.json", "controls_proof")
    byte_cli = pinned(proof["independent_operator_receipt_ref"],
                      P / "glm_controls_local_verification_v2/CLI_RECEIPT.json", "controls_proof")
    need(byte_proof["passed"] is True and byte_proof["original_path_bytes_sha256"] ==
         byte_proof["restored_path_bytes_sha256"] == row_digest(controls_expected)
         and byte_proof["inventory_ref"] == READS[CONTROL_INVENTORY]["ref"]
         and byte_cli["passed"] is True and integer(byte_cli["actual_process"]["exit_code"]) == 0
         and byte_cli["actual_process"]["exit_chunk"] == "7fa466", "controls_independent_byte_proof")
    controls_marker = pinned(proof["restore_complete_ref"], C / "restore/COMPLETE.json", "restore_complete")
    need(controls_marker == complete(controls_expected, {"kind": "restored-originals",
         "input_sha256": proof["index_ref"]["sha256"], "single_archive": False}), "controls_restore_complete")
    control_stats = bundle_metadata(C / "bundle", proof["index_ref"], proof["pack_complete_ref"], controls_expected)
    need(control_stats["shards"] == cop["pack"]["stdout"]["shards"] == 5, "controls_shards")
    decision = read(OP / "glm_public_controls_subset_v1/ROOT_SCOPE_DECISION.json", group="controls_omission")
    excluded = decision["excluded_files"]
    need(decision["issuer"] == "ROOT" and decision["approved"] is True and len(excluded) == 1
         and excluded[0]["path"] not in controls_expected and excluded[0]["path"] not in raw_expected
         and decision["retained_count"] == 1114 and decision["retained_bytes"] == 224903100
         and decision["original_run_exclusions"] == 0, "preserved_omission")
    proposed.append({"bundle_id": "controls", "category": "controls", "bundle_root": str(C / "bundle"),
        "index_ref": proof["index_ref"], "complete_ref": proof["pack_complete_ref"], "file_count": 1114,
        "original_bytes": 224903100, "operator_ref": READS[C / "OPERATOR_COMPLETION.json"]["ref"],
        "local_proof_ref": READS[C / "ROOT_LOCAL_PROOF.json"]["ref"],
        "local_verification": {"pack_exit_code": proof["pack_exit_code"], "restore_exit_code": proof["restore_exit_code"],
            "complete_original_and_restored_path_bytes_sha_match": proof["complete_original_and_restored_path_bytes_sha_match"],
            "all_started_children_reaped": proof["all_started_children_reaped"]}})
    all_originals = {**raw_expected, **controls_expected}
    need(len(proposed) == 37 and len(all_originals) == 71634 and
         sum(x["bytes"] for x in all_originals.values()) == 3467116893, "collection_totals")
    for name in all_originals:
        need(not any(str(parent) in all_originals for parent in PurePosixPath(name).parents
                     if str(parent) != "."), "global_original_path_prefix_conflict")

    STAGE = "fixed_snapshot_second_metadata_hash"
    snapshot = tuple(READS.items())
    before_digest, after_digest = hashlib.sha256(), hashlib.sha256()
    groups = {}
    for path, item in sorted(snapshot):
        before_digest.update(encoded({"ref": item["ref"], "stat": item["stat"]}))
        _, ref, state = digest_file(path, item["limit"])
        need(ref == item["ref"] and state == item["stat"], "second_metadata_hash_or_stat_changed")
        after_digest.update(encoded({"ref": ref, "stat": state}))
        groups[item["group"]] = groups.get(item["group"], 0) + 1
    need(before_digest.hexdigest() == after_digest.hexdigest() and len(READS) == len(snapshot), "fixed_ledger_stability")
    selection = {"schema": "root-glm-collection-selection-v1", "issuer": "ROOT",
                 "original_execution_complete": summary["original_execution_complete"],
                 "original_score_complete": summary["original_score_complete"],
                 "bundle_count": 37, "file_count": 71634, "original_bytes": 3467116893, "bundles": proposed}
    envelope = {"schema_version": "glm-full-collection-selection-candidate-envelope-v1", "issuer": "glm_delivery_reuse",
                "candidate": True, "approved": False, "actual_assembly_authorized": False,
                "proposed_selection": selection, "root_actual_exit_ref": READS[R / "ROOT_OPERATOR_COMPLETION.json"]["ref"],
                "closed_summary_ref": READS[R / "SUMMARY.json"]["ref"],
                "note": "ROOT-shaped projection only; ROOT must separately adopt the selection and issue an exact assembly GO."}
    receipt = {"schema_version": "glm-full-collection-closed-metadata-review-v1", "passed": True, "approved": False,
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "root_operator_actual_process": {"session_id": 13206, "start_chunk": "2155fa", "exit_chunk": "895e99", "exit_code": 0},
        "source_verifier_ref": READS[OUT / "verify_selection.py"]["ref"],
        "root_exit_ref": READS[R / "ROOT_OPERATOR_COMPLETION.json"]["ref"],
        "closed_summary_ref": READS[R / "SUMMARY.json"]["ref"],
        "raw_inventory_ref": READS[RAW_INVENTORY]["ref"], "controls_inventory_ref": READS[CONTROL_INVENTORY]["ref"],
        "controls_operator_ref": READS[C / "OPERATOR_COMPLETION.json"]["ref"],
        "controls_root_proof_ref": READS[C / "ROOT_LOCAL_PROOF.json"]["ref"],
        "tool_refs": [item["ref"] for _, item in snapshot if item["group"] == "tool"],
        "metadata_refs_count": len(snapshot), "metadata_read_group_counts": groups, "metadata_full_hash_passes": 2,
        "metadata_ref_stat_before_sha256": before_digest.hexdigest(), "metadata_ref_stat_after_sha256": after_digest.hexdigest(),
        "metadata_ref_inventory_sha256": sha(encoded([item["ref"] for _, item in sorted(snapshot)])),
        "input_stat_integer_values_stringified": True, "fixed_snapshot_no_ledger_growth": True,
        "all_declared_metadata_bytes_and_sha_pins_match": True,
        "72_real_exit_receipts_verified": True, "children": 72, "unresolved_children": 0, "natural_waits": 72,
        "each_child_wait_attempts": 1, "poll_fallbacks": 0, "wait_exceptions": 0, "child_failure_layers": 0,
        "disk_results_equal_summary_except_added_exit_refs": True, "comparison_sets_exact_raw_inventory": True,
        "raw_file_count": 70520, "raw_original_bytes": 3242213793, "raw_shards": 283, "raw_compressed_bytes": 746949323,
        "controls_file_count": 1114, "controls_original_bytes": 224903100, "controls_shards": control_stats["shards"],
        "controls_compressed_bytes": control_stats["compressed_bytes"],
        "collection_bundle_count": 37, "collection_original_file_count": 71634, "collection_original_bytes": 3467116893,
        "collection_tar_count_from_indexes": 283 + control_stats["shards"],
        "raw_row_sha256": row_digest(raw_expected), "controls_row_sha256": row_digest(controls_expected),
        "global_row_sha256": row_digest(all_originals), "global_original_paths_unique_and_prefix_free": True,
        "bundle_index_member_union_and_complete_metadata_verified": True,
        "restore_complete_rows_and_bindings_verified": True,
        "index_archive_bytes_sha_are_declared_metadata_not_new_archive_hashes": True,
        "original_global_byte_comparison_basis": "Frozen original operator final pass plus actual natural exit 0 and pinned SUMMARY.",
        "controls_original_byte_comparison_basis": "Previously accepted independent whole-file controls verification and ROOT_LOCAL_PROOF.",
        "original_execution_complete": True, "original_score_complete": True,
        "public_controls_omission_preserved": True, "public_internal_audit_chain_fully_closed": False,
        "original_three_key_records_unchanged": True, "new_fourth_key_not_accessed_or_applied": True,
        "archive_or_original_or_restored_payload_bytes_read": 0, "key_files_statted_or_read": 0,
        "operator_command_metadata_seen_but_not_republished_in_candidate": True,
        "started_receipts_or_logs_read": False, "scanner_imported_or_invoked": False,
        "production_modules_imported_or_called": False, "pack_restore_assembly_git_network_called": False,
        "new_ROOT_LOCAL_PROOF_created_or_assumed": False, "ROOT_local_proof_status": "pending ROOT acceptance",
        "candidate_envelope_sha256": sha(encoded(envelope)), "proposed_selection_sha256": sha(encoded(selection)),
        "batch_metadata_summaries": batch_receipts, "full_project_complete": False}
    STAGE = "complete"
    return {"candidate_envelope": envelope, "review_receipt": receipt}

if __name__ == "__main__":
    try:
        value = main()
    except Exception as error:
        print(json.dumps({"passed": False, "stage": STAGE, "error_type": type(error).__name__,
                          "error": str(error), "completed_metadata_reads": len(READS)}, sort_keys=True), flush=True)
        raise
    print(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False), flush=True)
