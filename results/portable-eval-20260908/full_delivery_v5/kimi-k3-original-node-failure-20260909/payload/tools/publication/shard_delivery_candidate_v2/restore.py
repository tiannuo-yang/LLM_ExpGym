#!/usr/bin/env python3
"""Independent bounded archive verification and fresh byte-exact restoration."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tarfile
import tempfile
import zlib

import common as c


@contextmanager
def inspect_shard(path, expected_sha256, secrets=(), compressed_limit=c.COMPRESSED,
                  expanded_limit=c.EXPANDED, files_per_shard=c.MAX_FILES):
    """Spool only bounded decompressed tar bytes; never trust archive paths."""
    c.number(compressed_limit,c.COMPRESSED,"compressed_limit",1024)
    c.number(expanded_limit,c.EXPANDED,"expanded_limit",1024)
    c.number(files_per_shard,c.MAX_FILES,"files_per_shard",1)
    path = c.lexical(path)
    _, digest = c.stream_hash(path, compressed_limit)
    c.need(digest == c.checksum(expected_sha256), "archive_digest")
    # Enough bounded header/PAX space for max 4096-byte paths, plus tar padding.
    tar_limit = expanded_limit + (files_per_shard + 1) * 8192 + 10240
    with tempfile.TemporaryFile() as spool:
        expanded_tar = 0
        with os.fdopen(os.open(path, os.O_RDONLY | getattr(os,"O_NOFOLLOW",0)),"rb") as compressed:
            header = compressed.read(10)
            c.need(len(header) == 10 and header[:3] == b"\x1f\x8b\x08" and header[3] == 0
                   and header[4:8] == b"\0"*4, "gzip_header_metadata")
            compressed.seek(0)
            source = zlib.decompressobj(31)
            while True:
                pending = compressed.read(c.BLOCK)
                if not pending:
                    break
                while pending:
                    chunk = source.decompress(pending,min(c.BLOCK,tar_limit-expanded_tar+1))
                    expanded_tar += len(chunk)
                    c.need(expanded_tar <= tar_limit, "decompression_limit")
                    spool.write(chunk)
                    c.need(not source.unused_data, "multiple_or_trailing_gzip_data")
                    pending = source.unconsumed_tail
                if source.eof:
                    c.need(not compressed.read(1), "multiple_or_trailing_gzip_data")
                    break
            c.need(source.eof, "truncated_gzip")
        c.need(c.stream_hash(path,compressed_limit)[1] == digest, "archive_changed_during_read")
        spool.seek(0)
        with tarfile.open(fileobj=spool, mode="r:") as archive:
            members = []
            for member in archive:
                members.append(member)
                c.need(len(members) <= files_per_shard + 1, "archive_member_count")
                c.number(member.size,c.MEMBER,"member_size_limit")
            c.need(1 < len(members) <= files_per_shard + 1, "archive_member_count")
            c.need(not archive.pax_headers, "global_pax_forbidden")
            names, expanded, expected_offset = set(), 0, 0
            for member in members:
                c.relative(member.name)
                c.need(member.name not in names, "duplicate_archive_member")
                names.add(member.name)
                c.need(member.isreg() and member.type in (tarfile.REGTYPE,tarfile.AREGTYPE), "archive_link_or_special_member")
                c.need(set(member.pax_headers) <= {"path"}, "unsupported_pax_metadata")
                c.need(member.offset == expected_offset, "unaccounted_tar_gap")
                # Compare ALL original header bytes, not a reserialization of
                # parsed metadata (which discards NUL suffixes and other bytes).
                # Fresh producer defaults also forbid regular-file linkname,
                # noncanonical fields/padding and hidden PAX header content.
                header_size = member.offset_data - member.offset
                c.need(512 <= header_size <= 8192, "raw_header_size_limit")
                canonical = tarfile.TarInfo(member.name)
                canonical.size, canonical.mode = member.size, 0o600
                expected_header = canonical.tobuf(format=tarfile.PAX_FORMAT, encoding="utf-8", errors="strict")
                spool.seek(member.offset)
                c.need(spool.read(header_size) == expected_header, "noncanonical_raw_tar_header")
                expected_offset = member.offset_data + ((member.size + 511)//512)*512
                spool.seek(member.offset_data + member.size)
                c.need(not any(spool.read(expected_offset-member.offset_data-member.size)), "nonzero_member_padding")
                c.number(member.size,c.MEMBER,"member_size_limit")
                expanded += member.size
                c.need(expanded <= expanded_limit, "expanded_member_sum_limit")
                c.scan(c.encoded({"name":member.name,"pax_headers":member.pax_headers,"uname":member.uname,"gname":member.gname}), "metadata.json", secrets)
            # Reject hidden members/nonzero garbage after tar's first EOF marker.
            spool.seek(expected_offset)
            tail_bytes = 0
            while True:
                chunk = spool.read(c.BLOCK)
                if not chunk:
                    break
                tail_bytes += len(chunk)
                c.need(not any(chunk), "nonzero_tar_tail")
            c.need(tail_bytes >= 1024, "missing_tar_end_markers")
            first = members[0]
            c.need(first.name == "FILES.json" and first.size <= c.INDEX_LIMIT, "missing_member_manifest")
            payload = archive.extractfile(first).read(c.INDEX_LIMIT+1)
            c.need(len(payload) == first.size, "member_manifest_size")
            c.scan(payload,"FILES.json",secrets)
            manifest = c.strict_json(payload)
            c.need(set(manifest) == {"schema","files"} and manifest["schema"] == "shard-members-v1", "member_manifest_schema")
            rows = manifest["files"]
            c.validate_rows(rows)
            c.need(len(rows) <= files_per_shard and len(members) == len(rows)+1, "manifest_member_count")
            for member, row in zip(members[1:],rows):
                c.need(member.name == "data/"+row["path"] and member.size == row["bytes"], "manifest_member_mapping")
                raw = archive.extractfile(member).read(c.MEMBER+1)
                c.need(len(raw) == row["bytes"] and c.sha(raw) == row["sha256"], "member_bytes_digest")
                c.scan(raw,row["path"],secrets)
            yield {"files":rows,"manifest_bytes":payload,"expanded_bytes":expanded,
                   "archive":archive,"members":members[1:]}


def verify_bundle_content(index_path, expected_sha256, secrets=()):
    index_path = c.lexical(index_path)
    c.need(index_path.name == "INDEX.json", "root_index_name")
    root = index_path.parent
    index, _ = c.load_json(index_path, expected_sha256, secrets)
    c.need(index.get("schema") == "shard-delivery-v1" and index.get("scanner_sha256") == c.SCANNER_SHA, "root_index_schema_or_scanner")
    c.checksum(index["manifest_sha256"])
    limits = index["limits"]
    c.need(set(limits) == {"compressed_bytes","expanded_bytes","member_bytes","files_per_shard"}, "limit_schema")
    c.number(limits["compressed_bytes"],c.COMPRESSED,"compressed_limit",1024)
    c.number(limits["expanded_bytes"],c.EXPANDED,"expanded_limit",1024)
    c.need(limits["member_bytes"] == c.MEMBER, "member_limit_override")
    c.number(limits["files_per_shard"],c.MAX_FILES,"files_per_shard",1)
    shards = index["shards"]
    c.need(isinstance(shards,list) and 0 < len(shards) <= c.MAX_SHARDS, "shard_count_limit")
    scan_ref = index["source_scan"]
    c.need(scan_ref["path"] == "SOURCE_SCAN.json", "scan_receipt_name")
    scan_receipt, scan_raw = c.load_json(root/scan_ref["path"],scan_ref["sha256"],secrets)
    c.need(len(scan_raw) == scan_ref["bytes"] and scan_receipt["safe_to_stage"] is True
           and scan_receipt["findings"] == [] and scan_receipt["secret_sources_checked"] >= 1
           and scan_receipt["validator_sha256"] == c.SCANNER_SHA, "source_scan_receipt")
    expected_paths = {"INDEX.json","SOURCE_SCAN.json"}
    all_rows, original_paths = [], set()
    for number, shard in enumerate(shards,1):
        archive_name = "shards/part-%06d.tar.gz" % number
        page_name = "indexes/part-%06d.json" % number
        c.need(shard["archive"] == archive_name and shard["index"] == page_name, "noncanonical_shard_paths")
        expected_paths.update((archive_name,page_name))
        c.number(shard["bytes"],limits["compressed_bytes"],"compressed_size",1)
        page,page_raw = c.load_json(root/page_name,shard["index_sha256"],secrets)
        c.need(len(page_raw) == shard["index_bytes"] and page.get("schema") == "shard-members-v1", "index_page_metadata")
        with inspect_shard(root/archive_name,shard["sha256"],secrets,limits["compressed_bytes"],limits["expanded_bytes"],limits["files_per_shard"]) as verified:
            c.need(c.stream_hash(root/archive_name,limits["compressed_bytes"])[0] == shard["bytes"], "compressed_size_mismatch")
            c.need(verified["manifest_bytes"] == page_raw and verified["expanded_bytes"] == shard["expanded_bytes"]
                   and len(verified["files"]) == shard["file_count"], "shard_index_contents")
            for row in verified["files"]:
                c.need(row["path"] not in original_paths, "duplicate_original_across_shards")
                original_paths.add(row["path"])
                all_rows.append(row)
    all_rows.sort(key=lambda row:row["path"])
    c.no_path_prefixes(original_paths)
    source_rows = [{"path":r["target"],"bytes":r["bytes"],"sha256":r["sha256"]} for r in scan_receipt["files"]]
    c.need(all_rows == sorted(source_rows,key=lambda row:row["path"]), "source_receipt_full_set_mismatch")
    c.need(len(all_rows) == index["file_count"] and sum(row["bytes"] for row in all_rows) == index["original_bytes"], "global_file_count_or_bytes")
    c.need(c.tree(root) == expected_paths, "bundle_missing_or_extra_file")
    return {"files":all_rows,"index":index,"root":root}


def verify_bundle(index_path, expected_sha256, secrets=()):
    index_path = c.lexical(index_path)
    c.need(index_path.parent.name == "payload","bundle_wrapper_payload")
    c.verify_completion(index_path.parent.parent,{"kind":"bundle","index_sha256":expected_sha256},secrets)
    return verify_bundle_content(index_path,expected_sha256,secrets)


def restore(index_path, expected_sha256, output, secret_files=(), single_archive=False):
    output = c.fresh(output)
    secrets = c.scanner().load_secrets([c.lexical(p) for p in secret_files])
    index_path = c.lexical(index_path)
    if not single_archive:
        c.need(output != index_path.parent and index_path.parent not in output.parents, "output_inside_bundle")
    if single_archive:
        with inspect_shard(index_path,expected_sha256,secrets) as verified:
            rows = verified["files"]
        shards = [(index_path,expected_sha256,c.COMPRESSED,c.EXPANDED,c.MAX_FILES)]
    else:
        verified = verify_bundle(index_path,expected_sha256,secrets)
        rows,index = verified["files"],verified["index"]
        lim = index["limits"]
        shards = [(verified["root"]/s["archive"],s["sha256"],lim["compressed_bytes"],lim["expanded_bytes"],lim["files_per_shard"]) for s in index["shards"]]
    # Every shard has been validated before any original output is written.
    with tempfile.TemporaryDirectory(prefix=".shard-restore-",dir=output.parent) as scratch_name:
        restored = Path(scratch_name)/"originals"
        restored.mkdir(mode=0o700)
        for path,digest,compressed,expanded,count in shards:
            with inspect_shard(path,digest,secrets,compressed,expanded,count) as valid:
                for member,row in zip(valid["members"],valid["files"]):
                    destination = restored / str(c.relative(row["path"]))
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    c.lexical(destination)
                    descriptor = os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
                    digest_state,total = hashlib.sha256(),0
                    with os.fdopen(descriptor,"wb") as target:
                        source = valid["archive"].extractfile(member)
                        while True:
                            block = source.read(c.BLOCK)
                            if not block:
                                break
                            total += len(block)
                            c.need(total <= row["bytes"],"restore_member_grew")
                            digest_state.update(block)
                            target.write(block)
                        target.flush(); os.fsync(target.fileno())
                    c.need(total == row["bytes"] and digest_state.hexdigest() == row["sha256"],"restore_bytes_digest")
        expected = {row["path"] for row in rows}
        c.need(c.tree(restored) == expected,"restored_path_set")
        for row in rows:
            c.need(c.stream_hash(restored/row["path"]) == (row["bytes"],row["sha256"]),"restored_final_digest")
        binding = {"kind":"restored-originals","input_sha256":expected_sha256,"single_archive":single_archive}
        completion_sha = c.commit_new_directory(restored,output,binding,secrets)
    return {"passed":True,"file_count":len(rows),"original_bytes":sum(row["bytes"] for row in rows),
        "index_or_archive_sha256":expected_sha256,"independent_single_shard":single_archive,
        "known_secret_sources_checked":len(secrets),"byte_exact_full_path_set":True,
        "modes_timestamps_ownership_preserved":False,"publication_performed":False,
        "originals_relative_path":"payload","completion_sha256":completion_sha}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--index",type=Path)
    mode.add_argument("--archive",type=Path)
    parser.add_argument("--sha256",required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--secret-file",action="append",type=Path,default=[])
    args = parser.parse_args()
    print(json.dumps(restore(args.index or args.archive,args.sha256,args.output_dir,args.secret_file,args.archive is not None),indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"passed":False,"rule":str(exc) if isinstance(exc,c.DeliveryError) else "restore_failed","publication_performed":False}))
        raise SystemExit(1)
