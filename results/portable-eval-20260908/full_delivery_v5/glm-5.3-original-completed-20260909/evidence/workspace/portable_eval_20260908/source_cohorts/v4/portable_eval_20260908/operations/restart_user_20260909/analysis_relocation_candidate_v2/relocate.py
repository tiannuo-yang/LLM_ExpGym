#!/usr/bin/env python3
"""Relocate a pinned AN2 source index by exact restored collection ownership."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import stat

MIB = 1024**2
SCANNER_SHA = "aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116"
INPUT_NAMES = {"manifest", "records", "oracle", "input_pins", "source_index"}


def need(ok, code):
    if not ok:
        raise ValueError(code)


def checksum(value):
    need(type(value) is str and re.fullmatch("[0-9a-f]{64}", value), "invalid_sha256")
    return value


def relative(value):
    need(type(value) is str and value and len(value.encode()) <= 4096
         and not any(ord(c) < 32 for c in value) and "\\" not in value, "invalid_relative_path")
    p = PurePosixPath(value)
    need(not p.is_absolute() and ".." not in p.parts and p.as_posix() == value and value != ".", "invalid_relative_path")
    return p


def absolute(value, existing=False):
    need(type(value) is str and not any(ord(c) < 32 or ord(c) == 127 for c in value)
         and Path(value).is_absolute() and Path(value).anchor == "/" and str(Path(value)) == value
         and ".." not in Path(value).parts, "invalid_absolute_path")
    p = Path(value)
    if existing:
        for item in [*reversed(p.parents), p]:
            need(not item.is_symlink(), "symlink_path")
    return p


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()


def parse(raw):
    def pairs(values):
        result = {}
        for k, v in values:
            need(k not in result, "duplicate_json_key")
            result[k] = v
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: need(False, "nonfinite_json"))


def number(value, maximum):
    need(type(value) is int and 0 <= value <= maximum, "invalid_count")
    return value


class Reader:
    """Metadata <=256 MiB; selected payloads streamed, no archive/full-tree scan."""
    def __init__(self):
        self.checked, self.metadata_bytes = {}, 0

    @staticmethod
    def signature(s):
        return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns

    def read(self, path, digest, limit=8*MIB, keep=True):
        checksum(digest)
        path = absolute(str(path), existing=True)
        before = path.lstat()
        need(stat.S_ISREG(before.st_mode) and before.st_size <= limit, "file_type_or_size")
        h, parts, size = hashlib.sha256(), [], 0
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            need(self.signature(os.fstat(stream.fileno())) == self.signature(before), "file_changed")
            while True:
                block = stream.read(MIB)
                if not block:
                    break
                size += len(block)
                need(size <= limit, "file_too_large")
                h.update(block)
                if keep:
                    parts.append(block)
            need(self.signature(os.fstat(stream.fileno())) == self.signature(before), "file_changed")
        need(self.signature(path.lstat()) == self.signature(before) and h.hexdigest() == digest, "file_changed_or_sha")
        ref = {"path": str(path), "sha256": digest, "bytes": size}
        need(path not in self.checked or self.checked[path][0] == ref, "conflicting_file_ref")
        self.checked[path] = (ref, self.signature(before))
        if keep:
            self.metadata_bytes += size
            need(self.metadata_bytes <= 256*MIB, "metadata_total_limit")
            return b"".join(parts)
        return ref

    def json(self, path, digest, limit=8*MIB):
        return parse(self.read(path, digest, limit))

    def final_stability(self):
        for path, (_ref, signature) in self.checked.items():
            absolute(str(path), existing=True)
            need(self.signature(path.lstat()) == signature, "file_changed_after_check")


def ownership(spec, reader):
    root = absolute(spec["restore_root"], existing=True)
    incomplete = root/"COLLECTION_INCOMPLETE.json"
    need(root.is_dir() and not incomplete.exists() and not incomplete.is_symlink(), "restore_not_complete")
    pins = spec["collection"]
    need(set(pins) == {"index_sha256", "ownership_sha256", "complete_sha256"}, "collection_pin_schema")
    collection = reader.json(root/"COLLECTION_INDEX.json", pins["index_sha256"])
    nav = reader.json(root/"OWNERSHIP_INDEX.json", pins["ownership_sha256"])
    complete = reader.json(root/"COLLECTION_COMPLETE.json", pins["complete_sha256"])
    need(set(collection) == {"schema", "bundle_count", "file_count", "original_bytes", "bundles"}
         and collection["schema"] == "whole-file-collection-v1", "collection_schema")
    bundles = collection["bundles"]
    need(type(bundles) is list and 0 < len(bundles) <= 512
         and number(collection["bundle_count"], 512) == len(bundles), "bundle_count")
    need(set(nav) == {"schema", "bundles", "lookup"} and nav["schema"] == "collection-path-ownership-v1"
         and type(nav["bundles"]) is list and len(nav["bundles"]) == len(bundles), "ownership_schema")
    need(complete.get("schema") == "whole-file-collection-complete-v1" and complete.get("complete") is True
         and complete.get("input_sha256") == pins["index_sha256"]
         and complete.get("ownership_index_sha256") == pins["ownership_sha256"]
         and all(complete.get(k) == collection[k] for k in ("bundle_count", "file_count", "original_bytes"))
         and type(complete.get("bundles")) is list and len(complete["bundles"]) == len(bundles), "collection_completion_binding")
    for key in ("bundle_count", "file_count", "original_bytes"):
        number(complete[key], 512*4096*256*MIB)
    members, ids, total_size = {}, set(), 0
    for row, navigation, done in zip(bundles, nav["bundles"], complete["bundles"]):
        need(type(row) is dict and set(row) == {"bundle_id", "category", "index", "sha256", "file_count", "original_bytes"}, "bundle_row")
        bid = row["bundle_id"]
        need(all(type(row[k]) is str and re.fullmatch("[a-z0-9][a-z0-9_-]{0,63}", row[k]) for k in ("bundle_id","category"))
             and bid not in ids and bid != "metadata", "bundle_id")
        ids.add(bid)
        original_index = relative(row["index"])
        need(original_index.name == "INDEX.json" and original_index.parent.name == "payload", "original_index_layout")
        need(navigation == dict(row, restored_payload=bid+"/payload", copied_member_index="metadata/"+bid+"/INDEX.json"), "ownership_not_exact")
        need(set(done) == {"bundle_id", "completion_sha256"} and done["bundle_id"] == bid, "bundle_completion_owner")
        index_path = root/"metadata"/bid/"INDEX.json"
        index = reader.json(index_path, row["sha256"])
        need(index.get("schema") == "shard-delivery-v1" and index.get("scanner_sha256") == SCANNER_SHA, "bundle_index_schema")
        shards = index["shards"]
        need(type(shards) is list and 0 < len(shards) <= 4096, "shard_count")
        rows = []
        for n, shard in enumerate(shards, 1):
            page_name = "indexes/part-%06d.json" % n
            need(shard["index"] == page_name and shard["archive"] == "shards/part-%06d.tar.gz" % n, "shard_path")
            page_raw = reader.read(index_path.parent/page_name, shard["index_sha256"])
            page = parse(page_raw)
            need(set(page) == {"schema", "files"} and page["schema"] == "shard-members-v1"
                 and number(shard["index_bytes"], 8*MIB) == len(page_raw)
                 and type(page["files"]) is list and 0 < len(page["files"]) <= 256
                 and number(shard["file_count"], 256) == len(page["files"]), "member_page")
            for member in page["files"]:
                need(type(member) is dict and set(member) == {"path", "sha256", "bytes"}, "member_row")
                rel = relative(member["path"])
                checksum(member["sha256"]); number(member["bytes"], 100*MIB)
                need(str(rel) not in members, "duplicate_global_member")
                members[str(rel)] = {**member, "bundle_id": bid, "restored_path": str(root/bid/"payload"/rel)}
            need(page["files"] == sorted(page["files"], key=lambda r: r["path"]), "member_order")
            rows.extend(page["files"])
        rows.sort(key=lambda r: r["path"])
        size = sum(r["bytes"] for r in rows)
        for obj in (row, index):
            need(number(obj["file_count"], 4096*256) == len(rows)
                 and number(obj["original_bytes"], 4096*256*MIB) == size, "bundle_totals")
        expected = {"schema":"completed-directory-v1","complete":True,"payload":"payload",
                    "binding":{"kind":"restored-originals","input_sha256":row["sha256"],"single_archive":False},
                    "file_count":len(rows),"bytes":size,
                    "inventory_sha256":hashlib.sha256(b"".join(encoded(r) for r in rows)).hexdigest()}
        need(reader.json(root/bid/"COMPLETE.json", done["completion_sha256"]) == expected, "bundle_inventory_completion")
        total_size += size
    for name in members:
        need(not any(str(parent) in members for parent in PurePosixPath(name).parents if str(parent) != "."), "global_prefix_collision")
    need(number(collection["file_count"], 512*4096*256) == len(members)
         and number(collection["original_bytes"], 512*4096*256*MIB) == total_size, "collection_totals")
    return members


def relocate(spec_path, spec_sha, output):
    reader = Reader()
    spec = reader.json(spec_path, spec_sha)
    need(set(spec) == {"schema", "old_workspace", "restore_root", "collection", "original_inputs"}
         and spec["schema"] == "analysis-source-relocation-v1", "spec_schema")
    old = absolute(spec["old_workspace"])
    need(old != Path("/"), "old_workspace_too_broad")
    root, output = absolute(spec["restore_root"], existing=True), absolute(str(output), existing=True)
    need(not output.exists() and output.parent.is_dir()
         and output != root and root not in output.parents and output not in root.parents
         and output != absolute(str(spec_path)) and output not in absolute(str(spec_path)).parents, "output_not_fresh_or_overlap")
    members = ownership(spec, reader)
    inputs = spec["original_inputs"]
    need(type(inputs) is dict and set(inputs) == INPUT_NAMES, "original_input_schema")
    originals, original_refs = {}, {}
    for name, ref in inputs.items():
        need(type(ref) is dict and set(ref) == {"member", "sha256"}, "original_input_ref")
        key = str(relative(ref["member"]))
        need(key in members and members[key]["sha256"] == checksum(ref["sha256"]), "original_input_owner_or_sha")
        member = members[key]
        raw = reader.read(member["restored_path"], ref["sha256"], 100*MIB)
        need(len(raw) == member["bytes"], "original_input_size")
        originals[name] = parse(raw)
        original_refs[name] = {"member":key, "bundle_id":member["bundle_id"], "path":member["restored_path"], "sha256":ref["sha256"]}
    pins = originals["input_pins"]
    need(pins == {name+"_sha256": inputs[name]["sha256"] for name in ("manifest","records","oracle")}, "original_input_pins")
    bundle, manifest, source_index = originals["records"], originals["manifest"], originals["source_index"]
    need(bundle.get("schema_version") == "restart-analysis-records-v1"
         and bundle.get("manifest_sha256") == inputs["manifest"]["sha256"]
         and bundle.get("source_tree_sha256") == manifest["source_and_inputs"]["source_tree_sha256"]
         and manifest["source_and_inputs"]["files"]["hpo.oracle"]["sha256"] == inputs["oracle"]["sha256"], "record_manifest_oracle_binding")
    expected = {}
    need(type(bundle["records"]) is list, "records_schema")
    for record in bundle["records"]:
        need(type(record["source_sha256"]) is dict, "record_source_schema")
        for key, digest in record["source_sha256"].items():
            relative(key); checksum(digest)
            need(key not in expected or expected[key] == digest, "conflicting_source_sha")
            expected[key] = digest
    need(type(source_index) is dict and set(source_index) == set(expected), "source_index_key_set")
    relocated, mappings, old_seen = {}, [], set()
    for key, old_location in source_index.items():
        location = absolute(old_location)
        need(old in location.parents and old_location not in old_seen, "old_source_outside_or_duplicate")
        old_seen.add(old_location)
        member_key = location.relative_to(old).as_posix()
        need(member_key in members and members[member_key]["sha256"] == expected[key], "source_member_owner_or_sha")
        member = members[member_key]
        fact = reader.read(member["restored_path"], expected[key], 100*MIB, keep=False)
        need(fact["bytes"] == member["bytes"], "source_member_size")
        relocated[key] = member["restored_path"]
        mappings.append({"key":key,"old_path":old_location,"workspace_member":member_key,
                         "bundle_id":member["bundle_id"],"restored_path":member["restored_path"],"sha256":expected[key],"bytes":fact["bytes"]})
    reader.final_stability()
    relocated_raw = encoded(relocated)
    evidence = {"schema":"analysis-source-relocation-evidence-v1","spec_sha256":spec_sha,"collection":spec["collection"],
                "original_inputs":original_refs,"source_count":len(relocated),"mapping":mappings,
                "relocated_index_sha256":hashlib.sha256(relocated_raw).hexdigest(),
                "checked_original_refs":[r for r,_s in reader.checked.values()],
                "all_collection_member_metadata_checked":True,"all_collection_payload_bytes_rechecked":False,
                "selected_source_bytes_and_five_inputs_checked":True,"analysis_executed":False,"scorer_calls":0,
                "exporter_executed":False,"fresh_scientific_review":False}
    evidence_raw = encoded(evidence)
    need(len(relocated_raw) <= 100*MIB and len(evidence_raw) <= 100*MIB, "derived_output_limit")
    output.mkdir(mode=0o700)
    for name, raw in (("source_index.relocated.json",relocated_raw),("MAPPING_EVIDENCE.json",evidence_raw)):
        with (output/name).open("xb") as f:
            f.write(raw)
    return {"source_count":len(relocated),"relocated_index_sha256":evidence["relocated_index_sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        print(json.dumps(relocate(args.spec, args.sha256, args.output_dir)))
    except Exception:
        print(json.dumps({"complete":False,"rule":"analysis_relocation_failed_no_retry"}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
