#!/usr/bin/env python3
"""Refresh the lightweight file inventory after explicitly staging release files.

Reads tracked files only. Verifies the complete frozen results directories
against the baseline Git commit before writing either root inventory file.
Does not commit, push, read credential files, or call a model/provider.
"""

import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[3]
BASE = "3070739c6ef868eb230ecfdb05f9a99aea0dd965"
MANIFEST = "LIGHTWEIGHT_MANIFEST.json"
SUMS = "SHA256SUMS"
SUPPLEMENT = "results/gemini-openrouter-20260917"
FROZEN = (
    "results/paper-analysis-20260916/",
    "results/six-models-lineage-20260914/",
    "results/paper-ad03e8c-delivery-20260916/",
)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    baseline = json.loads(git("show", BASE + ":" + MANIFEST))
    paths = sorted(p.decode() for p in git("ls-files", "-z").split(b"\0") if p)
    original = {row["path"]: row for row in baseline["files"]}
    entries = []
    for name in paths:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("not a regular release file: " + name)
        if name.lower().endswith((".key", ".pem", ".p12", ".pfx", ".tar.gz", ".tgz", ".bundle")):
            raise ValueError("credential/archive filename in tracked inventory: " + name)
        if name in {MANIFEST, SUMS}:
            continue
        data = path.read_bytes()
        entry = {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if name.startswith(FROZEN) and entry != original.get(name):
            raise ValueError("frozen results file changed or added: " + name)
        if entry != original.get(name):
            if re.search(rb"sk-or-v1-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", data):
                raise ValueError("credential pattern in changed file: " + name)
            if name.startswith(SUPPLEMENT + "/") and len(data) > 10 * 1024 * 1024:
                raise ValueError("unexpectedly large supplement file: " + name)
        entries.append(entry)
    if {name for name in original if name.startswith(FROZEN)} != {name for name in paths if name.startswith(FROZEN)}:
        raise ValueError("frozen results file set changed")
    baseline["scope"] = "Frozen ad03 report and datasets, with separately versioned Gemini OpenRouter supplements. Frozen counts retain their original cohort meaning."
    baseline["counts_scope"] = "Original frozen ad03 cohort only; supplement completion counts are in its own CHECKS.json files."
    baseline["supplements"] = [{"path": SUPPLEMENT + "/README.zh.md", "base_commit": BASE}]
    baseline["files"] = entries
    (ROOT / MANIFEST).write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n")
    sums = {row["path"]: row["sha256"] for row in entries}
    sums[MANIFEST] = hashlib.sha256((ROOT / MANIFEST).read_bytes()).hexdigest()
    (ROOT / SUMS).write_text("".join(digest + "  " + name + "\n" for name, digest in sorted(sums.items())))
    print(json.dumps({"status": "PASS", "inventoried_files": len(entries), "frozen_result_files": sum(name.startswith(FROZEN) for name in paths), "tracked_bytes": sum(row["bytes"] for row in entries)}, indent=2))


if __name__ == "__main__":
    main()
