#!/usr/bin/env python3
"""Read-only, fixed-scope GLM public-controls byte verifier; stdout evidence only."""
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
OUTPUT = P / "glm_controls_local_verification_v2"
INVENTORY = OP / "glm_public_controls_subset_v1/inventory.json"
AUTHORITY = OP / "glm_public_controls_subset_v1/ROOT_SCOPE_DECISION.json"
BUNDLE = P / "glm_controls_local_delivery_v2/bundle"
RESTORE = P / "glm_controls_local_delivery_v2/restore"
EXPECTED_COUNT = 1114
EXPECTED_BYTES = 224903100
INDEX_SHA = "4356b1cab3762da71202d5e4ce3ddc909dd08e06b531823d6940e9c91660cf26"
EXCLUDED = "portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/seal_operator_glm_formal_v1/invocation.json"
PINS = {
    INVENTORY: "3c321f8bbecba16cb3570bd6be04ccdc3956fdf857ed8dbb669becdd9a66726a",
    AUTHORITY: "90df6e9b1301211278c290676c7ee387398c487a527c2df6851a5a0146f473c3",
    BUNDLE / "payload/INDEX.json": INDEX_SHA,
    BUNDLE / "COMPLETE.json": "6ab714cd95c3cb5e46e452b902c036ca826873364c4f22e08254a3b49a0bdcc4",
    RESTORE / "COMPLETE.json": "f9641d26f870b250687a804571c6463aa3806be55627b7fadf4e3be6568f482d",
    P / "shard_delivery_candidate_v2/common.py": "7147524d5799dc1264f088518db19251c5f906bc2da501854ce279f56d73263e",
}
PINS[P / "shard_delivery_candidate_v2/restore.py"] = "ec20a0e22c8f810b09e894e0ddc6cc8dec114a66be4fe23cab8a55f3b62ac710"
READS = {}
METADATA = {}
STAGE = "initial"

def need(ok, code):
    if not ok:
        raise ValueError(code)

def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       allow_nan=False, separators=(",", ":")) + "\n").encode()

def digest(value):
    return hashlib.sha256(value).hexdigest()

def relative(value):
    need(type(value) is str and value and len(value.encode()) <= 4096, "relative_type_length")
    path = PurePosixPath(value)
    need(not path.is_absolute() and path.as_posix() == value
         and all(part not in ("", ".", "..") for part in path.parts)
         and "\\" not in value and not any(ord(ch) < 32 for ch in value), "unsafe_relative")
    return path

def lexical(path):
    need(path.is_absolute() and ".." not in path.parts, "absolute_path")
    for ancestor in [*reversed(path.parents), path]:
        need(not stat.S_ISLNK(ancestor.lstat().st_mode), "symlink_component")
    return path

def signature(info):
    # Strings preserve full inode/nanosecond precision in downstream JSON readers.
    return {name: str(getattr(info, name)) for name in
            ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid",
             "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")}

def read_file(path, *, expected=None, limit=104857600, retain=False, group="metadata"):
    path = lexical(path)
    need(path not in READS, "duplicate_byte_read")
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, "file_type_size")
    sha = hashlib.sha256()
    chunks = []
    total = 0
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        opened = os.fstat(stream.fileno())
        while True:
            data = stream.read(1024 * 1024)
            if not data:
                break
            total += len(data)
            need(total <= limit, "file_grew")
            sha.update(data)
            if retain:
                chunks.append(data)
        after = os.fstat(stream.fileno())
    final = path.lstat()
    need(signature(before) == signature(opened) == signature(after) == signature(final)
         and total == before.st_size, "unstable_byte_read")
    ref = {"path": str(path), "bytes": total, "sha256": sha.hexdigest()}
    if expected is not None:
        need(ref["sha256"] == expected, "pinned_sha_mismatch")
    READS[path] = {"ref": ref, "stat": signature(before), "group": group}
    return ref, b"".join(chunks) if retain else None

def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("nonfinite_json")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)

def metadata(path, expected=None):
    ref, raw = read_file(path, expected=expected, limit=8 * 1024**2, retain=True)
    METADATA[path] = ref
    return strict_json(raw)

def rows(value):
    need(type(value) is list, "rows_list")
    result = {}
    for row in value:
        need(type(row) is dict and set(row) == {"path", "bytes", "sha256"}, "row_shape")
        name = str(relative(row["path"]))
        need(name not in result, "duplicate_row")
        need(type(row["bytes"]) is int and 0 <= row["bytes"] <= 104857600, "row_bytes")
        need(type(row["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", row["sha256"]), "row_sha")
        result[name] = row
    return result

def ordered(mapping):
    return [mapping[name] for name in sorted(mapping)]

def completion(originals, binding):
    sha = hashlib.sha256()
    for row in originals:
        sha.update(encoded(row))
    return {"schema": "completed-directory-v1", "complete": True, "payload": "payload",
            "binding": binding, "file_count": len(originals),
            "bytes": sum(row["bytes"] for row in originals), "inventory_sha256": sha.hexdigest()}

def expected_dirs(file_set):
    dirs = {""}
    for filename in file_set:
        for parent in PurePosixPath(filename).parents:
            if str(parent) != ".":
                dirs.add(str(parent))
    return dirs

def tree(root):
    lexical(root)
    need(stat.S_ISDIR(root.lstat().st_mode), "tree_root")
    files, dirs, states = set(), {""}, {}
    for base, directory_names, filenames in os.walk(root, followlinks=False):
        base = Path(base)
        for name in [".", *directory_names]:
            item = base if name == "." else base / name
            info = item.lstat()
            need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), "tree_directory")
            rel = item.relative_to(root).as_posix()
            rel = "" if rel == "." else str(relative(rel))
            dirs.add(rel)
            states[rel] = signature(info)
        for name in filenames:
            item = base / name
            need(stat.S_ISREG(item.lstat().st_mode), "tree_regular_file")
            files.add(str(relative(item.relative_to(root).as_posix())))
    return files, dirs, states

def validate_tree(root, expected):
    found = tree(root)
    need(found[0] == expected and found[1] == expected_dirs(expected), "exact_tree_mismatch")
    return found

def tree_proof(value):
    return {"files": len(value[0]), "directories_including_root": len(value[1]),
            "file_set_sha256": digest(encoded(sorted(value[0]))),
            "directory_set_sha256": digest(encoded(sorted(value[1]))),
            "directory_stat_sha256": digest(encoded(value[2]))}

def main():
    global STAGE
    started = datetime.now(timezone.utc).isoformat()
    STAGE = "pinned_metadata"
    need(Path(__file__).absolute() == OUTPUT / "verify.py", "script_location")
    read_file(OUTPUT / "verify.py", limit=1048576, group="tool")
    inventory = metadata(INVENTORY, PINS[INVENTORY])
    authority = metadata(AUTHORITY, PINS[AUTHORITY])
    index = metadata(BUNDLE / "payload/INDEX.json", INDEX_SHA)
    bundle_complete = metadata(BUNDLE / "COMPLETE.json", PINS[BUNDLE / "COMPLETE.json"])
    restored_complete = metadata(RESTORE / "COMPLETE.json", PINS[RESTORE / "COMPLETE.json"])
    for helper in (P / "shard_delivery_candidate_v2/common.py",
                   P / "shard_delivery_candidate_v2/restore.py"):
        read_file(helper, expected=PINS[helper], limit=1048576, group="tool")
    need(inventory["schema_version"] == "sealed-publication-file-inventory-v1"
         and inventory["issuer"] == "ROOT" and inventory["sealed"] is True, "sealed_inventory")
    need(inventory["authority_ref"] == {"path": AUTHORITY.relative_to(W).as_posix(),
                                      "sha256": PINS[AUTHORITY]}, "authority_binding")
    wanted = rows(inventory["files"])
    need(len(wanted) == EXPECTED_COUNT and sum(r["bytes"] for r in wanted.values()) == EXPECTED_BYTES,
         "scope_totals")
    need(authority["issuer"] == "ROOT" and authority["approved"] is True
         and authority["action"] == "derive_exact_public_inventory_minus_one_nonexperimental_operator_receipt"
         and len(authority["excluded_files"]) == 1
         and authority["excluded_files"][0]["path"] == EXCLUDED
         and EXCLUDED not in wanted
         and authority["retained_count"] == EXPECTED_COUNT
         and authority["retained_bytes"] == EXPECTED_BYTES, "omission_authority")
    need(index["schema"] == "shard-delivery-v1"
         and type(index["file_count"]) is int and index["file_count"] == EXPECTED_COUNT
         and type(index["original_bytes"]) is int and index["original_bytes"] == EXPECTED_BYTES,
         "index_totals")
    need(type(index["shards"]) is list and 0 < len(index["shards"]) <= 4096, "shards_count")
    bundle_rows = {"INDEX.json": {**METADATA[BUNDLE / "payload/INDEX.json"], "path": "INDEX.json"}}
    declared = {"INDEX.json"}
    for shard in index["shards"]:
        for name in (shard["index"], shard["archive"]):
            name = str(relative(name))
            need(name not in declared, "duplicate_bundle_path")
            declared.add(name)
    scan_ref = index["source_scan"]
    scan_path = str(relative(scan_ref["path"]))
    need(scan_path == "SOURCE_SCAN.json" and scan_path not in declared, "source_scan_path")
    declared.add(scan_path)
    expected_bundle = {"COMPLETE.json"} | {"payload/" + name for name in declared}
    expected_restore = {"COMPLETE.json"} | {"payload/" + name for name in wanted}
    before_bundle = validate_tree(BUNDLE, expected_bundle)
    before_restore = validate_tree(RESTORE, expected_restore)

    STAGE = "bundle_bytes_and_member_union"
    combined = {}
    for shard in index["shards"]:
        page_path = BUNDLE / "payload" / shard["index"]
        page = metadata(page_path, shard["index_sha256"])
        page_ref = METADATA[page_path]
        need(page_ref["bytes"] == shard["index_bytes"] and page["schema"] == "shard-members-v1", "member_page")
        page_rows = rows(page["files"])
        need(type(shard["file_count"]) is int and 0 < shard["file_count"] <= 256
             and len(page_rows) == shard["file_count"] and not (set(page_rows) & set(combined)), "page_union")
        combined.update(page_rows)
        bundle_rows[shard["index"]] = {**page_ref, "path": shard["index"]}
        archive_ref, _ = read_file(BUNDLE / "payload" / shard["archive"],
                                  expected=shard["sha256"], limit=48 * 1024**2, group="bundle_archive")
        need(archive_ref["bytes"] == shard["bytes"], "archive_bytes")
        bundle_rows[shard["archive"]] = {**archive_ref, "path": shard["archive"]}
    need(combined == wanted, "member_union_not_exact_inventory")
    source_ref, _ = read_file(BUNDLE / "payload" / scan_path, expected=scan_ref["sha256"],
                              limit=8 * 1024**2, group="bundle_metadata")
    need(source_ref["bytes"] == scan_ref["bytes"], "source_scan_bytes")
    bundle_rows[scan_path] = {**source_ref, "path": scan_path}
    need(bundle_complete == completion(ordered(bundle_rows), {"kind": "bundle", "index_sha256": INDEX_SHA}),
         "bundle_completion")
    expected_completion = completion(ordered(wanted), {"kind": "restored-originals",
                                                      "input_sha256": INDEX_SHA, "single_archive": False})
    need(restored_complete == expected_completion, "restored_completion")

    STAGE = "full_source_and_restored_bytes"
    source_digest = hashlib.sha256()
    restored_digest = hashlib.sha256()
    for name, row in sorted(wanted.items()):
        for base, group, accumulator in ((W, "original", source_digest),
                                        (RESTORE / "payload", "restored", restored_digest)):
            ref, _ = read_file(base / name, expected=row["sha256"], group=group)
            need(ref["bytes"] == row["bytes"], "original_restored_byte_count")
            accumulator.update(encoded({"path": name, "bytes": ref["bytes"], "sha256": ref["sha256"]}))
    need(source_digest.hexdigest() == restored_digest.hexdigest() == expected_completion["inventory_sha256"],
         "full_row_digest")

    STAGE = "final_stability_and_exact_tree"
    # Fixed snapshot; the final lstat pass never appends to READS.
    snapshot = tuple(READS.items())
    before_stat = hashlib.sha256()
    after_stat = hashlib.sha256()
    for path, item in sorted(snapshot):
        before_stat.update(encoded({"path": str(path), "stat": item["stat"]}))
        final = signature(lexical(path).lstat())
        need(final == item["stat"], "file_changed_after_hash")
        after_stat.update(encoded({"path": str(path), "stat": final}))
    need(before_stat.hexdigest() == after_stat.hexdigest(), "whole_check_stat_digest")
    after_bundle = validate_tree(BUNDLE, expected_bundle)
    after_restore = validate_tree(RESTORE, expected_restore)
    need(before_bundle == after_bundle and before_restore == after_restore, "tree_changed_during_check")
    need(len(READS) == len(snapshot), "fixed_read_ledger")
    STAGE = "complete"
    groups = {}
    for _, item in snapshot:
        groups[item["group"]] = groups.get(item["group"], 0) + 1
    return {
        "schema_version": "glm-public-controls-whole-file-verification-v2",
        "passed": True, "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "file_count": EXPECTED_COUNT, "original_bytes": EXPECTED_BYTES,
        "bundle_root": str(BUNDLE), "restored_root": str(RESTORE), "shard_count": len(index["shards"]),
        "inventory_ref": METADATA[INVENTORY], "authority_ref": METADATA[AUTHORITY],
        "index_ref": METADATA[BUNDLE / "payload/INDEX.json"],
        "pack_complete_ref": METADATA[BUNDLE / "COMPLETE.json"],
        "restore_complete_ref": METADATA[RESTORE / "COMPLETE.json"],
        "tool_refs": [item["ref"] for _, item in snapshot if item["group"] == "tool"],
        "bundle_payload_refs": ordered(bundle_rows),
        "original_path_bytes_sha256": source_digest.hexdigest(),
        "restored_path_bytes_sha256": restored_digest.hexdigest(),
        "complete_original_and_restored_path_bytes_sha_match": True,
        "bundle_member_union_matches_sealed_inventory": True,
        "exact_entire_bundle_and_restore_file_and_directory_sets_before_and_after": True,
        "bundle_tree_before": tree_proof(before_bundle), "bundle_tree_after": tree_proof(after_bundle),
        "restore_tree_before": tree_proof(before_restore), "restore_tree_after": tree_proof(after_restore),
        "stable_file_refs_checked": len(snapshot), "read_counts": groups,
        "file_stat_before_sha256": before_stat.hexdigest(), "file_stat_after_sha256": after_stat.hexdigest(),
        "stat_fields": list(next(iter(READS.values()))["stat"]), "exact_integer_stat_values_stringified": True,
        "each_file_stable_across_lstat_open_fstat_read_fstat_lstat_and_final_recheck": True,
        "public_nonexperimental_invocation_omission_preserved": True,
        "excluded_path": EXCLUDED, "excluded_file_not_statted_or_read": True,
        "original_scan_failure_retained": True, "pack_or_restore_invoked": False,
        "scanner_invoked": False, "archive_decompression_performed": False,
        "payloads_semantically_parsed_or_rescored": False, "key_contents_or_key_paths_accessed": False,
        "network_git_or_publication_performed": False, "source_or_restore_writes_performed": False,
        "modes_timestamps_ownership_preserved_by_restore": False,
        "restore_actual_process_as_reported_by_ROOT": {
            "session_id": 17903, "start_chunk": "1a1124", "exit_chunk": "edbe0a", "exit_code": 0,
            "basis": "Parent task report; this verifier did not poll or re-run that process."},
        "verification_process_exit_recorded_separately_by_operator": True,
        "full_project_complete": False,
    }

if __name__ == "__main__":
    try:
        result = main()
    except Exception as error:
        print(json.dumps({"schema_version": "glm-public-controls-whole-file-verification-v2",
                          "passed": False, "stage": STAGE, "error_type": type(error).__name__,
                          "error": str(error), "completed_byte_reads": len(READS)}, sort_keys=True), flush=True)
        raise
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2), flush=True)
