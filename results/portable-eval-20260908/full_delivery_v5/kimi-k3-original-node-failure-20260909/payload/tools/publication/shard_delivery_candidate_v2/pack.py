#!/usr/bin/env python3
"""Build fresh, hash-bound, independent gzip tar shards. No upload support."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile

import common as c


class CompressedOverflow(Exception):
    pass


class CappedWriter:
    def __init__(self, target, maximum):
        self.target, self.maximum, self.total = target, maximum, 0
    def write(self, raw):
        self.total += len(raw)
        if self.total > self.maximum:
            raise CompressedOverflow()
        return self.target.write(raw)
    def flush(self):
        self.target.flush()


class HashReader:
    def __init__(self, source):
        self.source, self.digest, self.total = source, hashlib.sha256(), 0
    def read(self, size=-1):
        raw = self.source.read(size)
        self.digest.update(raw)
        self.total += len(raw)
        return raw


def member_manifest(rows):
    return c.encoded({"schema": "shard-members-v1", "files": rows})


def write_archive(path, rows, source_paths, compressed_limit):
    """Stream file bytes into tar -> gzip; no complete archive kept in RAM."""
    payload = member_manifest(rows)
    with path.open("xb") as raw_output:
        capped = CappedWriter(raw_output, compressed_limit)
        with gzip.GzipFile(filename="", mode="wb", fileobj=capped, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w|", format=tarfile.PAX_FORMAT) as archive:
                info = tarfile.TarInfo("FILES.json")
                info.size, info.mode = len(payload), 0o600
                archive.addfile(info, io.BytesIO(payload))
                for row in rows:
                    source_path = c.lexical(source_paths[row["path"]])
                    before = source_path.lstat()
                    info = tarfile.TarInfo("data/" + row["path"])
                    info.size, info.mode = row["bytes"], 0o600
                    with os.fdopen(os.open(source_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "rb") as source:
                        opened = os.fstat(source.fileno())
                        stream = HashReader(source)
                        archive.addfile(info, stream)
                        extra = source.read(1)
                        after = os.fstat(source.fileno())
                    c.need(not extra and stream.total == row["bytes"] and stream.digest.hexdigest() == row["sha256"]
                           and c.signature(before) == c.signature(opened) == c.signature(after) == c.signature(source_path.lstat()),
                           "source_changed_during_pack")
        raw_output.flush()
        os.fsync(raw_output.fileno())


def pack(manifest_path, manifest_sha256, workspace, output, secret_files,
         compressed_limit=c.COMPRESSED, expanded_limit=c.EXPANDED, files_per_shard=c.MAX_FILES):
    c.number(compressed_limit, c.COMPRESSED, "compressed_limit", 1024)
    c.number(expanded_limit, c.EXPANDED, "expanded_limit", 1024)
    c.number(files_per_shard, c.MAX_FILES, "files_per_shard", 1)
    workspace, output = c.lexical(workspace), c.fresh(output)
    validator = c.scanner()
    secrets = validator.load_secrets([c.lexical(p) for p in secret_files])
    c.need(secrets, "known_secret_source_required")
    manifest, original = c.load_json(manifest_path, manifest_sha256, secrets)
    c.need(manifest.get("approved") is True and manifest.get("artifacts"), "unapproved_manifest")
    c.need(all(a.get("sealed") is True and a.get("kind") in {"sealed_file", "sealed_directory"}
               and isinstance(a.get("files"), list) and a["files"] for a in manifest["artifacts"]), "unsupported_or_unsealed_input")
    for item in manifest["artifacts"]:
        c.relative(item["source"])
        c.relative(item["target"])
        c.relative(item["anchor"]["path"])
        for row in item["files"]:
            c.relative(row["path"])
        source_root = c.lexical(validator.safe_path(workspace, item["source"]))
        c.need(output != source_root and source_root not in output.parents, "output_inside_input")
    # Complete original rule scan happens before any output or spool is created.
    scan_receipt, _ = validator.validate(manifest, workspace, secrets, seal=False)
    c.need(scan_receipt["safe_to_stage"] is True and not scan_receipt["findings"], "complete_source_scan_failed")
    rows, source_paths = [], {}
    notes = []
    for record in scan_receipt["files"]:
        target = str(c.relative(record["target"]))
        c.need(target not in source_paths, "duplicate_target")
        path = c.lexical(validator.safe_path(workspace, record["source"]))
        raw = validator.stable_read(path)
        c.need(len(raw) == record["bytes"] and c.sha(raw) == record["sha256"], "source_after_scan_changed")
        advisory = c.scan(raw, path.name, secrets)
        if advisory:
            notes.append({"path": target, "rules": advisory})
        rows.append({"path": target, "bytes": record["bytes"], "sha256": record["sha256"]})
        source_paths[target] = path
    rows.sort(key=lambda row: row["path"])
    c.need(rows, "empty_sources")
    c.no_path_prefixes(source_paths)
    groups, group = [], []
    for row in rows:
        c.validate_rows([row])
        c.need(row["bytes"] + len(member_manifest([row])) <= expanded_limit, "oversized_original_not_chunked")
        trial = group + [row]
        if group and (len(trial) > files_per_shard or sum(r["bytes"] for r in trial) + len(member_manifest(trial)) > expanded_limit):
            groups.append(group)
            group = []
        group.append(row)
    if group:
        groups.append(group)
    # Private scratch is disposable; only a fully validated bundle is renamed.
    with tempfile.TemporaryDirectory(prefix=".shard-build-", dir=output.parent) as scratch_name:
        scratch = Path(scratch_name)
        bundle = scratch / "bundle"
        (bundle / "shards").mkdir(parents=True)
        (bundle / "indexes").mkdir()
        final_groups = []
        def emit(group):
            c.need(len(final_groups) < c.MAX_SHARDS, "shard_count_limit")
            number = len(final_groups) + 1
            path = bundle / "shards" / ("part-%06d.tar.gz" % number)
            try:
                write_archive(path, group, source_paths, compressed_limit)
            except CompressedOverflow:
                if path.exists():
                    path.unlink()  # Our private, exact scratch file only.
                c.need(len(group) > 1, "oversized_original_not_chunked")
                mid = len(group) // 2
                emit(group[:mid]); emit(group[mid:])
                return
            payload = member_manifest(group)
            c.need(len(payload) <= c.INDEX_LIMIT, "member_manifest_limit")
            name = "indexes/part-%06d.json" % number
            c.scan(payload, name, secrets)
            c.write_new(bundle / name, payload)
            size, digest = c.stream_hash(path, compressed_limit)
            final_groups.append({"archive": path.relative_to(bundle).as_posix(), "bytes": size, "sha256": digest,
                "index": name, "index_bytes": len(payload), "index_sha256": c.sha(payload),
                "file_count": len(group), "expanded_bytes": sum(r["bytes"] for r in group) + len(payload)})
        for group in groups:
            emit(group)
        receipt_raw = c.encoded(scan_receipt)
        c.need(len(receipt_raw) <= c.INDEX_LIMIT, "source_scan_index_limit")
        c.scan(receipt_raw, "SOURCE_SCAN.json", secrets)
        c.write_new(bundle / "SOURCE_SCAN.json", receipt_raw)
        index = {"schema": "shard-delivery-v1", "manifest_sha256": manifest_sha256,
            "scanner_sha256": c.SCANNER_SHA, "file_count": len(rows), "original_bytes": sum(r["bytes"] for r in rows),
            "limits": {"compressed_bytes": compressed_limit, "expanded_bytes": expanded_limit, "member_bytes": c.MEMBER, "files_per_shard": files_per_shard},
            "source_scan": {"path": "SOURCE_SCAN.json", "sha256": c.sha(receipt_raw), "bytes": len(receipt_raw)},
            "shards": final_groups, "known_secret_sources_checked": len(secrets), "additive_scan_advisories": notes,
            "preservation": "Complete original bytes and relative paths; no reserialization, summary substitution or chunking. POSIX ownership/timestamps/modes are not restored.",
            "publication_performed": False}
        index_raw = c.encoded(index)
        c.need(len(index_raw) <= c.INDEX_LIMIT, "root_index_limit")
        c.scan(index_raw, "INDEX.json", secrets)
        c.write_new(bundle / "INDEX.json", index_raw)
        # Independently validate the emitted format before making output visible.
        import restore
        verified = restore.verify_bundle_content(bundle / "INDEX.json", c.sha(index_raw), secrets)
        c.need(verified["files"] == rows, "emitted_inventory_differs")
        for row in rows:
            c.need(c.stream_hash(source_paths[row["path"]]) == (row["bytes"], row["sha256"]), "source_changed_after_pack")
        scan_again, _ = validator.validate(manifest, workspace, secrets, seal=False)
        c.need(scan_again["safe_to_stage"] is True and scan_again["files"] == scan_receipt["files"], "source_inventory_changed_after_pack")
        completion_sha = c.commit_new_directory(bundle, output, {"kind":"bundle","index_sha256":c.sha(index_raw)}, secrets)
    return {"passed": True, "file_count": len(rows), "original_bytes": index["original_bytes"],
        "shards": len(index["shards"]), "compressed_bytes": sum(s["bytes"] for s in index["shards"]),
        "index_sha256": c.sha(index_raw), "source_manifest_sha256": manifest_sha256,
        "scanner_sha256": c.SCANNER_SHA, "source_unchanged": True, "publication_performed": False,
        "index_relative_path":"payload/INDEX.json","completion_sha256":completion_sha}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--secret-file", action="append", default=[], type=Path)
    parser.add_argument("--compressed-limit", type=int, default=c.COMPRESSED)
    parser.add_argument("--expanded-limit", type=int, default=c.EXPANDED)
    args = parser.parse_args()
    result = pack(args.manifest,args.manifest_sha256,args.workspace,args.output_dir,args.secret_file,args.compressed_limit,args.expanded_limit)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"passed": False, "rule": str(exc) if isinstance(exc,c.DeliveryError) else "pack_failed", "publication_performed": False}))
        raise SystemExit(1)
