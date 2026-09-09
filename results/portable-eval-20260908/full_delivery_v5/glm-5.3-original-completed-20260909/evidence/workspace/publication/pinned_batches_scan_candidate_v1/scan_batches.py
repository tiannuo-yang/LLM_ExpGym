#!/usr/bin/env python3
"""Pinned single-inventory scan-only driver; no implicit GO or publication."""
import argparse
from collections import Counter
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import resource
import stat
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PREPARE = HERE.parent / "full_scope_batch_candidate_v1/prepare.py"
PREPARE_SHA = "77a69230c7ef2fd9de1767c63d237f8514411372ce10eac902d71b1d2af65c60"
assert hashlib.sha256(PREPARE.read_bytes()).hexdigest() == PREPARE_SHA
loader = importlib.util.spec_from_file_location("fixed_batch_metadata", PREPARE)
b = importlib.util.module_from_spec(loader)
loader.loader.exec_module(b)
c, s = b.c, b.validator
TOOLS = {str(PREPARE): PREPARE_SHA, str(b.COMMON): b.COMMON_SHA,
         str(HERE.parent / "validate_bundle_v2.py"): c.SCANNER_SHA}


def absolute(value):
    c.need(type(value) is str and value.startswith("/") and str(Path(value)) == value
           and ".." not in Path(value).parts and "\0" not in value, "absolute_path_required")
    return c.lexical(value)


class Metadata:
    def __init__(self):
        self.refs, self.blobs, self.caps, self.total = {}, {}, {}, 0

    def raw(self, ref, cap=c.INDEX_LIMIT):
        c.need(type(ref) is dict and set(ref) in ({"path", "sha256"}, {"path", "sha256", "bytes"}), "metadata_ref_schema")
        path = absolute(ref["path"])
        c.checksum(ref["sha256"])
        if str(path) not in self.blobs:
            raw = s.stable_read(path, limit=cap)
            self.total += len(raw)
            c.need(self.total <= 256 * 1024**2, "metadata_total_limit")
            self.blobs[str(path)] = raw
            self.caps[str(path)] = cap
        raw = self.blobs[str(path)]
        c.need(len(raw) <= cap and c.sha(raw) == ref["sha256"]
               and ("bytes" not in ref or type(ref["bytes"]) is int and ref["bytes"] == len(raw)),
               "metadata_pin_mismatch")
        self.refs[str(path)] = {"path": str(path), "sha256": ref["sha256"], "bytes": len(raw)}
        return raw

    def json(self, ref, cap=c.INDEX_LIMIT):
        return c.strict_json(self.raw(ref, cap))

    def recheck(self):
        for path, ref in self.refs.items():
            raw = s.stable_read(absolute(path), limit=self.caps[path])
            c.need(len(raw) == ref["bytes"] and c.sha(raw) == ref["sha256"], "metadata_after_changed")


def catalogue(inventory_ref, index_ref, seal_ref, workspace, expected, reader=None):
    """Metadata only, including exact seal-part rows; never scan/load credentials."""
    r = reader or Metadata()
    w = absolute(workspace)
    for path, digest in TOOLS.items():
        r.raw({"path": path, "sha256": digest})
    inv = r.json(inventory_ref, c.MEMBER)
    index_raw = r.raw(index_ref)
    index = c.strict_json(index_raw)
    seal = r.json(seal_ref)
    c.need(set(expected) == {"file_count", "original_bytes", "batch_count"}
           and all(type(v) is int and v >= 0 for v in expected.values()), "expected_totals_schema")
    authority = {"path": Path(seal_ref["path"]).relative_to(w).as_posix(), "sha256": seal_ref["sha256"]}
    c.need(inv.get("authority_ref") == authority and index.get("authority_ref") == authority, "seal_authority_binding")
    limits = index["limits"]
    c.need(set(limits) == {"max_files", "manifest_bytes", "original_file_bytes", "index_bytes"}
           and limits["original_file_bytes"] == c.MEMBER and limits["index_bytes"] == c.INDEX_LIMIT, "fixed_caps_changed")
    c.number(limits["max_files"], 2000, "batch_file_cap", 1)
    c.number(limits["manifest_bytes"], b.MANIFEST_BYTES, "manifest_cap", 1)
    # Regenerate unchanged frozen format: exact comparison covers path/anchor/IDs,
    # flags, ordering, full union, prefix conflicts and encoded byte accounting.
    docs = b.build(inv, inventory_ref["sha256"], limits["max_files"], limits["manifest_bytes"])
    c.need(docs["INDEX.candidate.json"] == index_raw, "candidate_index_not_exact_frozen_output")
    c.need({k: index[k] for k in ("file_count", "batch_count")} ==
           {k: expected[k] for k in ("file_count", "batch_count")}
           and index["original_bytes"] == expected["original_bytes"], "expected_totals_mismatch")
    c.need(seal["schema_version"] == "restart-closed-run-inventory-v1"
           and seal["full_second_read_equal"] is True
           and type(seal.get("original_execution_complete")) is bool
           and type(seal.get("original_score_complete")) is bool
           and seal["file_count"] == expected["file_count"] and seal["total_bytes"] == expected["original_bytes"],
           "closed_seal_totals_mismatch")
    root = Path(seal["run_root"])
    c.need(root.is_absolute() and str(root) == seal["run_root"] and ".." not in root.parts
           and root != w and w in root.parents, "original_run_root")
    original_rows = []
    for part in seal["file_parts"]:
        c.need(Path(part["path"]).parent == Path(seal_ref["path"]).parent, "seal_part_outside_metadata_root")
        rows = r.json({k: part[k] for k in ("path", "sha256", "bytes")}, c.MEMBER)
        c.need(type(rows) is list and len(rows) == part["file_count"]
               and sum(x["bytes"] for x in rows) == part["total_bytes"], "seal_part_count_bytes")
        for row in rows:
            rel = b.relative(row["relative_path"])
            c.need(row["path"] == str(root / rel) and stat.S_ISREG(row["mode"]), "seal_original_path_type")
            original_rows.append({"path": (root / rel).relative_to(w).as_posix(),
                                  "bytes": row["bytes"], "sha256": row["sha256"]})
    c.need(sorted(original_rows, key=lambda x: x["path"]) == inv["files"], "seal_to_inventory_union")
    batches = []
    for ref in index["batches"]:
        c.need(Path(ref["path"]).name == ref["path"], "batch_name")
        source = {"path": str(Path(index_ref["path"]).parent / ref["path"]),
                  "sha256": ref["sha256"], "bytes": ref["bytes"]}
        raw = r.raw(source, b.MANIFEST_BYTES)
        c.need(raw == docs[ref["path"]], "candidate_batch_not_exact_frozen_output")
        batches.append({"candidate_ref": source, "spec": c.strict_json(raw),
                        "file_count": ref["file_count"], "original_bytes": ref["original_bytes"]})
    return batches, index, seal, r


def check_keys(paths):
    c.need(type(paths) is list and len(paths) == len(set(paths)) == 3, "exact_three_secret_paths")
    for value in paths:
        p = absolute(value)
        info = p.lstat()  # Path/type/owner/mode only. Values read only by original main.
        c.need(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
               and stat.S_IMODE(info.st_mode) == 0o600, "secret_source_type_owner_mode")


def write(path, raw):
    c.write_new(path, raw)
    return {"path": str(path), "bytes": len(raw), "sha256": c.sha(raw)}


def execute(go_ref, secret_files):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.umask(0o077)
    r = Metadata()
    go = r.json(go_ref)
    keys = {"schema_version", "issuer", "approved", "action", "driver_sha256", "workspace",
            "inventory_ref", "index_ref", "seal_ref", "expected_totals", "secret_files",
            "output_dir", "publication_authorized", "pack_authorized", "scan_all_batches_once"}
    c.need(set(go) == keys and go["schema_version"] == "root-pinned-batches-scan-go-v1"
           and go["issuer"] == "ROOT" and go["approved"] is True and go["action"] == "scan_only"
           and go["publication_authorized"] is False and go["pack_authorized"] is False
           and go["scan_all_batches_once"] is True, "independent_root_scan_go_required")
    r.raw({"path": str(Path(__file__).resolve()), "sha256": go["driver_sha256"]})
    c.need(secret_files == go["secret_files"], "caller_secret_paths_mismatch")
    output = c.fresh(absolute(go["output_dir"]))
    batches, index, seal, r = catalogue(go["inventory_ref"], go["index_ref"], go["seal_ref"],
                                      go["workspace"], go["expected_totals"], r)
    c.need(Path(seal["run_root"]) not in output.parents, "output_inside_original_run")
    check_keys(secret_files)
    r.recheck()  # Still no secret values or original payload reads.
    output.mkdir(mode=0o700)
    prepared = []
    for i, item in enumerate(batches, 1):
        spec = c.strict_json(c.encoded(item["spec"]))
        spec.update(approved=True, candidate=False, required_stages=[a["id"] for a in spec["artifacts"]])
        c.need({k: v for k, v in spec.items() if k not in ("approved", "candidate", "required_stages")} ==
               {k: v for k, v in item["spec"].items() if k not in ("approved", "candidate", "required_stages")},
               "private_spec_rewrite")
        private_raw = c.encoded(spec)
        c.need(len(private_raw) <= b.MANIFEST_BYTES, "private_spec_manifest_cap")
        prepared.append({**item, "name": "batch-%06d" % i,
                         "private_spec_ref": write(output / "specs" / ("batch-%06d.json" % i), private_raw)})
    write(output / "PREPARED.json", c.encoded({"root_go_ref": go_ref, "metadata_refs": list(r.refs.values()),
        "batches": [{k:v for k,v in x.items() if k != "spec"} for x in prepared],
        "secret_source_count": 3, "publication_authorized": False, "pack_performed": False}))
    results = []
    for item in prepared:
        code, refs, report, passed = None, {}, None, False
        try:
            check_keys(secret_files)
            argv = ["--spec", item["private_spec_ref"]["path"], "--workspace", go["workspace"],
                    "--output-dir", str(output / item["name"])]
            for path in secret_files:
                argv += ["--secret-file", path]
            status = io.StringIO()
            with contextlib.redirect_stdout(status), contextlib.redirect_stderr(io.StringIO()):
                code = s.main(argv)  # Unchanged original API, once; never --seal.
            c.need(type(code) is int and code in (0, 1, 2), "validator_returncode")
            raw = status.getvalue().encode()
            summary = c.strict_json(raw)
            c.need(summary.get("publication_performed") is False, "validator_status")
            refs["status"] = write(output / (item["name"] + ".status.json"), raw)
            for name in ("manifest.json", "lock.json"):
                p = output / item["name"] / name
                if p.exists():
                    data = s.stable_read(c.lexical(p), limit=c.INDEX_LIMIT)
                    refs[name] = {"path": str(p), "bytes": len(data), "sha256": c.sha(data)}
                    if name == "manifest.json":
                        report = c.strict_json(data)
            passed = bool(code == 0 and report and report["safe_to_stage"] is True
                and report["all_required_stages_present"] is True and report["validator_sha256"] == c.SCANNER_SHA
                and report["secret_sources_checked"] == 3 and len(report["files"]) == item["file_count"]
                and report["total_bytes"] == item["original_bytes"])
        except Exception:
            pass  # Never echo arbitrary exception text, captured stderr or payload.
        result = {"batch": item["name"], "validator_main_returncode": code, "passed": passed, "reports": refs,
            "finding_counts": report.get("finding_counts") if report else None,
            "advisory_counts": dict(Counter({a["rule"]: sum(x["count"] for x in report["advisories"] if x["rule"] == a["rule"])
                                              for a in report["advisories"]})) if report else None,
            "reason": None if passed else "batch_scan_not_passed", "partial_outputs_retained": not passed}
        write(output / (item["name"] + ".receipt.json"), c.encoded(result))
        results.append(result)  # Findings do not skip later batches or cause retries.
    stable = True
    try:
        r.recheck()
        for item in prepared:
            ref = item["private_spec_ref"]
            c.need(c.stream_hash(ref["path"]) == (ref["bytes"], ref["sha256"]), "private_spec_after_changed")
    except Exception:
        stable = False
    passed = stable and len(results) == index["batch_count"] and all(x["passed"] for x in results)
    result = {"root_go_ref": go_ref, "all_batches_passed": passed, "batches": results,
        "batch_count": len(results), "file_count": index["file_count"], "original_bytes": index["original_bytes"],
        "metadata_and_private_specs_after_unchanged": stable, "secret_source_count": 3, "core_dump_limit": 0,
        "original_execution_complete": seal["original_execution_complete"], "original_score_complete": seal["original_score_complete"],
        "implicit_retry_performed": False, "complete_project_publishable": False,
        "publication_performed": False, "pack_performed": False, "restore_performed": False}
    write(output / "SCAN_RECEIPT.json", c.encoded(result))
    c.sync_directory(output)
    return result


def main(argv=None):
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            raise c.DeliveryError("invalid_arguments")
    try:
        parser = Parser(description=__doc__)
        parser.add_argument("--go", required=True)
        parser.add_argument("--go-sha256", required=True)
        parser.add_argument("--secret-file", action="append", required=True)
        args = parser.parse_args(argv)
        result = execute({"path": args.go, "sha256": args.go_sha256}, args.secret_file)
        print(json.dumps({k: result[k] for k in ("all_batches_passed", "batch_count", "complete_project_publishable", "publication_performed")}))
        return 0 if result["all_batches_passed"] else 1
    except BaseException:
        print(json.dumps({"all_batches_passed": False, "rule": "pinned_batches_scan_failed",
                          "complete_project_publishable": False, "publication_performed": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
