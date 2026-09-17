#!/usr/bin/env python3
"""Finalize the delivery inventory, reusing verified immutable payload hashes."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import stat


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--delivery", type=Path, required=True)
    args = p.parse_args()
    root = args.delivery
    known = {}

    def add(path, size, digest, scope):
        current = dict(path=path, bytes=int(size), sha256=digest, identity_evidence=scope)
        if path in known:
            assert known[path]["bytes"] == current["bytes"] and known[path]["sha256"] == digest
        known[path] = current

    for row in json.loads((root / "report/EXPORTS.json").read_text())["exports"]:
        for destination in row["destinations"]:
            add(destination, row["bytes"], row["sha256"], "byte_identical_git_ad03_export")
    for row in json.loads((root / "csv/GENERATED.json").read_text())["csv_files"]:
        add(row["path"], row["bytes"], row["sha256"], "checked_frozen_csv_or_deterministic_pivot")
    for row in csv.DictReader((root / "index/selected_slots.csv").open(newline="")):
        if row["trajectory_file"]:
            assert row["result_archive_identity"] == "copied_canonical_bytes_match_archived_member_sha256"
            add(row["trajectory_file"], row["trajectory_bytes"], row["trajectory_sha256"], "copy_hash_matches_archived_member_identity")
    inherited = json.loads((root / "raw_archives/ARCHIVES.json").read_text())
    for row in inherited["copied_files_inventory"]:
        add(row["path"], row["bytes"], row["sha256"], "existing_source_identity_checked_during_copy")
    gemini_root = root / "raw_archives/gemini_snapshot"
    gemini = json.loads((gemini_root / "INDEX.json").read_text())
    for group in gemini["archive_sets"]:
        manifest_path = gemini_root / group["manifest"]
        manifest = json.loads(manifest_path.read_text())
        for row in manifest["archives"]:
            path = (manifest_path.parent / row["path"]).relative_to(root).as_posix()
            add(path, row["bytes"], row["sha256"], "new_seal_and_full_stream_verified" if group["kind"] == "recovery_v1" else "existing_archive_sha_checked_during_copy")
    for row in gemini["snapshot_controls"]:
        add("raw_archives/gemini_snapshot/" + row["path"], row["bytes"], row["sha256"], "frozen_snapshot_control_copy")
    excluded = {"FILE_MANIFEST.json", "SHA256SUMS"}
    result = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("delivery must not depend on symlinks")
        if path.is_dir():
            continue
        name = path.relative_to(root).as_posix()
        if name in excluded:
            continue
        info = path.stat()
        assert stat.S_ISREG(info.st_mode)
        if name in known:
            row = known.pop(name)
            assert info.st_size == row["bytes"], ("changed file size", name)
        else:
            row = dict(path=name, bytes=info.st_size, sha256=sha(path), identity_evidence="metadata_or_tool_hashed_at_finalization")
        result.append(row)
    assert not known, ("missing expected delivery files", sorted(known)[:5])
    counts = dict(files=len(result), bytes=sum(x["bytes"] for x in result), archives=sum(x["path"].endswith(".tar.gz") for x in result), archive_bytes=sum(x["bytes"] for x in result if x["path"].endswith(".tar.gz")))
    manifest = dict(schema="expgym.ad03.complete-local-delivery.v1", report_commit="ad03e8c42ca501016176ee1bc407b38499178506", data_commit="4b9f565e34e03c382cf71ffd7dd86d015593bc4f", scope="Complete local delivery. Public metadata-only mirror intentionally omits raw archives and trajectories. No model reruns or rescoring.", hash_scope="All regular delivery files except this manifest and SHA256SUMS. Previously checked payload identities reused with size fence; metadata newly hashed. sha256sum -c SHA256SUMS independently rereads bytes when desired.", counts=counts, files=result)
    manifest_path = root / "FILE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    lines = [f"{x['sha256']}  {x['path']}\n" for x in result]
    lines.append(f"{sha(manifest_path)}  FILE_MANIFEST.json\n")
    (root / "SHA256SUMS").write_text("".join(lines))
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
