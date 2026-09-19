#!/usr/bin/env python3
"""Verify the lightweight release's identities and counts without rescoring.

Uses the Python standard library and, in a Git checkout, ``git ls-files``.
It reads only release files; archived trajectories, APIs and models are not used.
Git blob identities are computed directly, so historical commits need not be
present in the lightweight checkout. They authenticate bytes against the
recorded export inventory, not the availability of old GitHub commits.
"""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REPORT_COMMIT = "ad03e8c42ca501016176ee1bc407b38499178506"
DELIVERY = "results/paper-ad03e8c-delivery-20260916"
MANIFEST = "LIGHTWEIGHT_MANIFEST.json"
CHECKSUMS = "SHA256SUMS"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class VerificationError(Exception):
    """A release file failed an explicit identity or consistency check."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


class Release:
    def __init__(self, root):
        self.root = root.resolve()
        self.cache = {}

    def relative(self, value, base="", allow_parent=False):
        require(isinstance(value, str) and bool(value), "empty or invalid path")
        require("\\" not in value and not any(ord(c) < 32 for c in value),
                "invalid path characters: {!r}".format(value))
        part = PurePosixPath(value)
        require(not part.is_absolute(), "absolute release path: " + value)
        require(allow_parent or (".." not in part.parts and "." not in value.split("/")),
                "noncanonical release path: " + value)
        joined = self.root / base / value
        resolved = joined.resolve()
        try:
            relative = resolved.relative_to(self.root).as_posix()
        except ValueError:
            raise VerificationError("path escapes release: " + value)
        current = self.root
        # Resolve parent components lexically only after checking their symlinks.
        for component in (PurePosixPath(base) / part).parts:
            current = current / component
            require(not current.is_symlink(), "symlink in release path: " + value)
        require(resolved.is_file(), "missing release file: " + relative)
        return relative

    def read(self, path):
        path = self.relative(path)
        if path not in self.cache:
            self.cache[path] = (self.root / path).read_bytes()
        return self.cache[path]

    def json(self, path):
        return json.loads(self.read(path).decode("utf-8"))

    def csv(self, path):
        reader = csv.DictReader(io.StringIO(self.read(path).decode("utf-8"), newline=""))
        require(bool(reader.fieldnames), "CSV has no header: " + path)
        rows = list(reader)
        require(all(None not in row and None not in row.values() for row in rows),
                "malformed CSV row: " + path)
        return rows

    def identity(self, entry, base="", allow_parent=False, blob=False):
        path = self.relative(entry["path"], base, allow_parent)
        data = self.read(path)
        require(type(entry["bytes"]) is int and entry["bytes"] == len(data),
                "byte count mismatch: " + path)
        require(isinstance(entry["sha256"], str) and HEX64.fullmatch(entry["sha256"]),
                "invalid SHA256 in manifest: " + path)
        require(hashlib.sha256(data).hexdigest() == entry["sha256"],
                "SHA256 mismatch: " + path)
        if blob:
            header = ("blob " + str(len(data)) + "\0").encode("ascii")
            require(hashlib.sha1(header + data).hexdigest() == entry["git_blob"],
                    "Git blob identity mismatch: " + path)
        return path


def unique_paths(paths, label):
    require(len(paths) == len(set(paths)), "duplicate paths in " + label)
    return set(paths)


def flag(value):
    require(value in {"True", "False", "true", "false"}, "invalid Boolean in selected_slots.csv")
    return value.lower() == "true"


def verify(root=ROOT):
    release = Release(root)
    manifest = release.json(MANIFEST)
    require(bool(manifest.get("schema")), "missing manifest schema")
    require(manifest["report_commit"] == REPORT_COMMIT, "unexpected frozen report commit")
    require(isinstance(manifest["source_code_commit"], str)
            and HEX40.fullmatch(manifest["source_code_commit"]), "invalid source code commit")

    files = unique_paths([release.identity(row) for row in manifest["files"]], "manifest files")
    require(MANIFEST not in files and CHECKSUMS not in files,
            "manifest files must exclude the manifest and SHA256SUMS")
    coverage = files | {MANIFEST, CHECKSUMS}
    if (release.root / ".git").exists():
        result = subprocess.run(["git", "-C", str(release.root), "ls-files", "-z"],
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tracked = {p.decode("utf-8") for p in result.stdout.split(b"\0") if p}
        require(tracked == coverage,
                "tracked inventory mismatch; absent from manifest: {}; not tracked: {}".format(
                    sorted(tracked - coverage), sorted(coverage - tracked)))
        tracked_check = "verified"
    else:
        tracked_check = "not available (source archive without .git)"

    sums = {}
    for line in release.read(CHECKSUMS).decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line)
        require(match is not None, "invalid SHA256SUMS line")
        digest, value = match.groups()
        path = release.relative(value)
        require(path not in sums, "duplicate SHA256SUMS path: " + path)
        require(hashlib.sha256(release.read(path)).hexdigest() == digest,
                "SHA256SUMS mismatch: " + path)
        sums[path] = digest
    require(set(sums) == files | {MANIFEST}, "SHA256SUMS coverage mismatch")

    exports = manifest["frozen_exports"]
    require(len(exports) == 102, "expected 102 frozen exports")
    frozen = unique_paths([release.identity(row, blob=True) for row in exports], "frozen exports")
    require(frozen <= files, "frozen export missing from file inventory")
    require(all(row["source_commit"] == REPORT_COMMIT for row in exports),
            "frozen export source commit mismatch")
    paper = "results/paper-analysis-20260916/"
    lineage = "results/six-models-lineage-20260914/"
    require(sum(p.startswith(paper) for p in frozen) == 70,
            "expected 70 frozen paper files")
    require(sum(p.startswith(lineage) for p in frozen) == 32,
            "expected 32 frozen lineage files")

    generated = release.json(DELIVERY + "/csv/GENERATED.json")
    require(generated["source_commit"] == REPORT_COMMIT, "CSV source commit mismatch")
    csv_entries = generated["csv_files"]
    require(len(csv_entries) == 53, "expected 53 generated CSV entries")
    csv_paths = []
    for entry in csv_entries:
        path = release.identity(entry, base=DELIVERY, allow_parent=True)
        require(path in files, "generated CSV missing from file inventory: " + path)
        require(len(release.csv(path)) == entry["rows"], "CSV row count mismatch: " + path)
        csv_paths.append(path)
    unique_paths(csv_paths, "generated CSV entries")

    selected_path = DELIVERY + "/index/selected_slots.csv"
    selected = release.csv(selected_path)
    require(len(selected) == 4698, "expected 4698 selected slots")
    require(len({row["slot_id"] for row in selected}) == len(selected), "duplicate selected slot")
    require(all(row["report_commit"] == REPORT_COMMIT for row in selected),
            "selected slot source commit mismatch")
    require(all(flag(row["expected"]) for row in selected), "unexpected selected slot")
    completed = [row for row in selected if flag(row["execution_complete"])]
    scored = [row for row in selected if flag(row["score_complete"])]
    require(len(completed) == 4682, "expected 4682 completed slots")
    require(len(scored) == 4671, "expected 4671 strictly scored slots")
    require(all(flag(row["execution_complete"]) for row in scored), "score without completed slot")
    require(Counter(row["system"] for row in completed) == {"expgym": 2496, "poolact": 2186},
            "completed ExpGym/PoolAct totals mismatch")
    require(sum(int(row["embedded_agents"]) for row in completed) == 11240,
            "expected 11240 embedded agent trajectories")
    joins = release.json(DELIVERY + "/index/JOIN_CHECKS.json")
    require(joins["report_commit"] == REPORT_COMMIT, "JOIN_CHECKS source commit mismatch")
    for key, value in (("planned_slots", len(selected)), ("completed_slots", len(completed)),
                       ("strict_score_complete", len(scored))):
        require(joins[key] == value, "JOIN_CHECKS count mismatch: " + key)
    require(joins["selected_slots_sha256"] == hashlib.sha256(release.read(selected_path)).hexdigest(),
            "JOIN_CHECKS selected_slots identity mismatch")

    comparison_counts = {}
    for filename, expected in (("COMPARISON.csv", 1298), ("MAIN_COMPARISON.csv", 72)):
        rows = release.csv(DELIVERY + "/csv/" + filename)
        require(len(rows) == expected, "unexpected comparison row count: " + filename)
        comparison_counts[filename] = len(rows)

    return {
        "status": "PASS",
        "files_verified": len(files),
        "sha256sum_files_verified": len(sums),
        "tracked_inventory": tracked_check,
        "frozen_exports_verified": len(frozen),
        "generated_csvs_verified": len(csv_entries),
        "counts_scope": "The following top-level slot and comparison counts describe the unchanged historical ad03 export.",
        "planned_slots": len(selected),
        "completed_slots": len(completed),
        "strict_score_complete": len(scored),
        "comparison_rows": comparison_counts,
        "current_report_recorded": {
            key: manifest.get("current_report", {}).get(key)
            for key in ("path", "scoring_layer", "completed_slots",
                        "strict_score_complete", "final_runtime_adoption_ready",
                        "rollback_complete", "retained_single_agent_slots",
                        "restored_multi_agent_slots")
            if key in manifest.get("current_report", {})
        },
        "model_calls": 0,
        "rescoring": False,
        "scope": "Release bytes, recorded Git blob identities, CSV rows and slot metadata; "
                 "raw archives and original trajectory contents are outside this lightweight check.",
    }


def main():
    try:
        result = verify()
    except (VerificationError, OSError, ValueError, KeyError, TypeError,
            subprocess.CalledProcessError) as error:
        print("FAIL: {}".format(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
