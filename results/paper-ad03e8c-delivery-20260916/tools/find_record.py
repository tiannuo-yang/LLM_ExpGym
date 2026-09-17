#!/usr/bin/env python3
"""Find frozen experiment slots and optionally restore only one slot's API dumps.

Uses only delivery-relative indexes. Listing never prints payload contents.
Restoration verifies selected member sizes/SHA256, not whole archives or public
release suitability; Audit orders may share one physical invocation dump root.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tarfile

FILTERS = ("model", "system", "scenario", "regime", "strategy", "item")
SUMMARY_FIELDS = (
    "slot_id", "model", "system", "scenario", "regime", "strategy", "item",
    "outer_repeat", "order", "seed", "status", "execution_complete",
    "score_complete", "cohort_id", "trajectory_file", "trajectory_sha256",
    "dump_status", "dump_member_count", "dump_bytes", "dump_scope",
    "dump_member_table", "source_job_id", "report_commit",
)


class RecordError(Exception):
    """An unsafe path, incomplete index, or failed content verification."""


def require(ok, message):
    if not ok:
        raise RecordError(message)


def safe_relative(value):
    path = PurePosixPath(value)
    require(bool(value) and bool(path.parts) and not path.is_absolute() and value == path.as_posix()
            and ".." not in path.parts and "." not in path.parts
            and "\\" not in value and "\x00" not in value,
            "Unsafe relative path in index")
    return path


def no_symlinks(path):
    """Check existing components without silently following a symlink."""
    absolute = path.absolute()
    for component in (absolute, *absolute.parents):
        if component.exists() or component.is_symlink():
            require(not component.is_symlink(), "Symlink paths are not accepted")
    return absolute


def local_file(root, relative):
    target = root / safe_relative(relative)
    no_symlinks(target)
    require(target.is_file() and stat.S_ISREG(target.stat().st_mode),
            "Required delivery-relative file is absent or not regular: " + relative)
    return target


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


def selected_members(root, slot):
    tables = slot.get("dump_member_table", "")
    require(bool(tables), "No archived dump-member table for this slot; the snapshot may be incomplete")
    api_root = slot.get("api_dump_root", "").rstrip("/")
    require(bool(api_root), "Slot has no original API dump root")
    prefix = api_root + "/"
    cohort = slot["cohort_id"]
    selected = {}
    destinations = set()
    for table in sorted(set(tables.split(";"))):
        for row in read_rows(local_file(root, table)):
            if (row.get("cohort_id") or row.get("source_id")) != cohort:
                continue
            if not row.get("original_path", "").startswith(prefix):
                continue
            relative = row["original_path"][len(prefix):]
            safe_relative(relative)
            safe_relative(row["archive_file"])
            safe_relative(row["member_path"])
            tar_member = row.get("tar_member_path") or row["member_path"]
            safe_relative(tar_member)
            require(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None,
                    "Invalid expected SHA256 in member index")
            try:
                size = int(row["bytes"])
            except (ValueError, TypeError):
                raise RecordError("Invalid expected size in member index") from None
            require(size >= 0, "Negative expected member size")
            member = dict(cohort_id=cohort, archive_file=row["archive_file"],
                          member_path=row["member_path"], tar_member_path=tar_member,
                          bytes=size, sha256=row["sha256"],
                          original_path=row["original_path"], output_path="files/" + relative,
                          member_table=table)
            identity = (member["archive_file"], member["tar_member_path"])
            if identity in selected:
                old = selected[identity]
                require(all(member[k] == old[k] for k in member if k != "member_table"),
                        "Conflicting duplicate member identity")
                continue
            require(member["output_path"] not in destinations,
                    "Two selected archive members would overwrite the same output")
            destinations.add(member["output_path"])
            selected[identity] = member
    members = sorted(selected.values(), key=lambda r: (r["archive_file"], r["tar_member_path"]))
    require(bool(members), "No archived dump members match this frozen slot")
    if slot.get("dump_member_count"):
        require(len(members) == int(slot["dump_member_count"]), "Slot/member count mismatch")
    if slot.get("dump_bytes"):
        require(sum(r["bytes"] for r in members) == int(slot["dump_bytes"]), "Slot/member byte-count mismatch")
    return members


def write_exclusive(path, payload):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags, 0o600), "wb") as handle:
        handle.write(payload)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def restore_dumps(root, slot, members, output):
    output = no_symlinks(output)
    require(not output.exists(), "Restore output must be a fresh, nonexistent directory")
    require(output.parent.is_dir(), "Restore output parent must already exist")
    archives = {}
    for member in members:
        archive = member["archive_file"]
        if archive not in archives:
            archives[archive] = (local_file(root, archive), {})
        archives[archive][1][member["tar_member_path"]] = member
    output.mkdir(mode=0o700)
    (output / ".incomplete").mkdir(mode=0o700)
    restored = []
    manifest = {
        "schema": "expgym.selected-dump-restore.v1", "slot_id": slot["slot_id"],
        "report_commit": slot.get("report_commit", ""), "cohort_id": slot["cohort_id"],
        "original_api_dump_root": slot["api_dump_root"],
        "scope": slot.get("dump_scope", "physical_invocation_may_cover_multiple_audit_orders"),
        "verification": "Selected regular-file member bytes/SHA256 only; not a whole-archive verification or a public-release/security clearance. Unselected members are not restored. Streaming may stop after the last selected member.",
        "files": restored,
    }
    try:
        for archive_name, (archive_path, expected) in sorted(archives.items()):
            found = set()
            with tarfile.open(archive_path, mode="r|*") as archive:
                for member in archive:
                    if member.name not in expected:
                        continue
                    require(member.name not in found, "Duplicate selected tar member")
                    require(member.isfile() and not member.issym() and not member.islnk(),
                            "Selected tar member is not a regular file")
                    spec = expected[member.name]
                    require(member.size == spec["bytes"], "Selected member tar size mismatch")
                    partial = output / ".incomplete" / (str(len(restored)) + ".part")
                    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
                    digest, size = hashlib.sha256(), 0
                    source = archive.extractfile(member)
                    require(source is not None, "Selected member has no payload")
                    with source, os.fdopen(os.open(partial, flags, 0o600), "wb") as target:
                        while chunk := source.read(1 << 20):
                            digest.update(chunk)
                            size += len(chunk)
                            require(size <= spec["bytes"], "Selected member exceeds expected bytes")
                            target.write(chunk)
                    require((size, digest.hexdigest()) == (spec["bytes"], spec["sha256"]),
                            "Selected member SHA256/size mismatch")
                    final = output / safe_relative(spec["output_path"])
                    final.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    no_symlinks(final.parent)
                    # Hard-link promotion is atomic and never overwrites a target.
                    os.link(partial, final, follow_symlinks=False)
                    partial.unlink()
                    restored.append(dict(spec))
                    found.add(member.name)
                    if len(found) == len(expected):
                        break
            require(found == set(expected), "Some selected members were absent from the archive")
        manifest.update(status="PASS", restored_files=len(restored),
                        restored_bytes=sum(r["bytes"] for r in restored))
        write_exclusive(output / "RESTORED_MANIFEST.json", json_bytes(manifest))
        (output / ".incomplete").rmdir()
    except Exception as exc:
        failure = {"status": "FAIL", "slot_id": slot["slot_id"],
                   "verified_files_before_failure": len(restored),
                   "error_type": type(exc).__name__,
                   "note": "Partial output retained. No successful restoration manifest exists; .incomplete payloads are not verified."}
        write_exclusive(output / "RESTORE_FAILED.json", json_bytes(failure))
        raise
    return {"status": "PASS", "slot_id": slot["slot_id"], "output": str(output),
            "manifest": str(output / "RESTORED_MANIFEST.json"),
            "restored_files": len(restored), "restored_bytes": manifest["restored_bytes"],
            "verification": manifest["verification"]}


def main(argv=None, *, root=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in FILTERS:
        parser.add_argument("--" + name, help="Exact frozen-index value")
    parser.add_argument("--slot", help="Exact slot_id from a previous listing")
    parser.add_argument("--limit", type=int, default=20, help="Maximum metadata records to print; 0 means all (default 20)")
    parser.add_argument("--dump-members", action="store_true", help="With --slot: list archived dump metadata, not contents")
    parser.add_argument("--restore-dumps", action="store_true", help="With --slot and --output: stream-verify and restore that invocation's dumps")
    parser.add_argument("--output", type=Path, help="Fresh nonexistent output directory; parent must exist")
    args = parser.parse_args(argv)
    require(args.limit >= 0, "--limit must be nonnegative")
    require(not (args.dump_members and args.restore_dumps), "Choose listing or restoration, not both")
    require(not (args.dump_members or args.restore_dumps) or args.slot,
            "Dump operations require an exact --slot")
    require(bool(args.output) == bool(args.restore_dumps), "--restore-dumps requires --output, and --output is only for restoration")
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    rows = [r for r in read_rows(local_file(root, "index/selected_slots.csv"))
            if all(getattr(args, k) is None or r.get(k) == getattr(args, k) for k in FILTERS)
            and (args.slot is None or r.get("slot_id") == args.slot)]
    if args.dump_members or args.restore_dumps:
        require(len(rows) == 1, "Exact slot query must select precisely one row")
        members = selected_members(root, rows[0])
        if args.restore_dumps:
            result = restore_dumps(root, rows[0], members, args.output)
        else:
            result = {"slot_id": args.slot, "total_members": len(members),
                      "shown_members": min(args.limit, len(members)) if args.limit else len(members),
                      "total_bytes": sum(r["bytes"] for r in members),
                      "scope": rows[0].get("dump_scope", ""),
                      "members": members[:args.limit] if args.limit else members}
    else:
        selected = rows[:args.limit] if args.limit else rows
        result = {"matched_slots": len(rows), "shown_slots": len(selected),
                  "slots": [{k: row.get(k, "") for k in SUMMARY_FIELDS} for row in selected]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    try:
        main()
    except (RecordError, OSError, tarfile.TarError, ValueError) as exc:
        print(json.dumps({"status": "ERROR", "error_type": type(exc).__name__,
                          "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
