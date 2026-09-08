#!/usr/bin/env python3
"""Capture reproducible inputs without reading multi-terabyte tensor payloads."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import tarfile
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent / "LLM_ExpGym"
PAPER = ROOT.parent / "expgym-paper"
CHECKPOINT = Path("/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Kimi-K3")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def command(args: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def checkpoint_manifest() -> dict:
    index_path = CHECKPOINT / "model.safetensors.index.json"
    index = json.loads(index_path.read_text())
    expected: dict[str, set[str]] = {}
    for tensor, filename in index["weight_map"].items():
        expected.setdefault(filename, set()).add(tensor)
    records = []
    for filename, names in sorted(expected.items()):
        path = CHECKPOINT / filename
        size = path.stat().st_size
        with path.open("rb") as handle:
            header_size = struct.unpack("<Q", handle.read(8))[0]
            if not 0 < header_size < size - 8:
                raise ValueError(f"Invalid safetensors header length: {path}")
            header_raw = handle.read(header_size)
            header = json.loads(header_raw)
        actual = set(header) - {"__metadata__"}
        if names != actual:
            raise ValueError(f"Tensor index/header mismatch: {path}")
        offsets = sorted(tuple(header[name]["data_offsets"]) for name in actual)
        cursor = 0
        for start, end in offsets:
            if start != cursor or end < start:
                raise ValueError(f"Invalid/noncontiguous tensor offsets: {path}")
            cursor = end
        if cursor + 8 + header_size != size:
            raise ValueError(f"Truncated or oversized tensor payload: {path}")
        records.append({
            "file": filename,
            "bytes": size,
            "mtime_ns": path.stat().st_mtime_ns,
            "tensor_count": len(actual),
            "header_sha256": hashlib.sha256(header_raw).hexdigest(),
            "index_header_and_size_valid": True,
        })
    small_files = {}
    for path in sorted(CHECKPOINT.iterdir()):
        if path.is_file() and path.suffix != ".safetensors":
            small_files[path.name] = {"bytes": path.stat().st_size, "sha256": digest(path)}
    return {
        "path": str(CHECKPOINT),
        "config": json.loads((CHECKPOINT / "config.json").read_text()),
        "tensor_file_count": len(records),
        "tensor_count": len(index["weight_map"]),
        "total_tensor_file_bytes": sum(record["bytes"] for record in records),
        "validation_scope": "All tensor names, shard headers, offsets, and file sizes; tensor payload bytes are not fully hashed. SGLang load is a separate acceptance gate.",
        "shards": records,
        "metadata_files": small_files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="initial")
    parser.add_argument("--checkpoint", action="store_true")
    args = parser.parse_args()
    if not args.label or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in args.label):
        parser.error("--label must contain letters, digits, hyphens, or underscores")
    out = ROOT / "provenance" / args.label
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(REPO))
    from expgym.trace_v2 import source_tree_sha256
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "host": platform.node(),
        "python": sys.version,
        "uv": command(["uv", "--version"]),
        "repo": str(REPO),
        "repo_commit": command(["git", "rev-parse", "HEAD"], REPO),
        "repo_status": command(["git", "status", "--short"], REPO),
        "source_tree_sha256": source_tree_sha256(REPO),
        "paper_commit": command(["git", "rev-parse", "HEAD"], PAPER),
        "paper_version": "versions/iclr2026",
        "config_hashes": {str(p.relative_to(REPO)): digest(p) for p in sorted((REPO / "configs").rglob("*")) if p.is_file()},
        "policy": "No environment variables, API keys, or request headers are collected.",
    }
    (out / "native-requirements.freeze.txt").write_text(command(["uv", "pip", "freeze", "--python", str(REPO / ".venv/bin/python")]) + "\n")
    (out / "source-changes.patch").write_text(command(["git", "diff", "--binary", "HEAD"], REPO) + "\n")
    tracked = command(["git", "ls-files", "--others", "--exclude-standard"], REPO).splitlines()
    result["untracked_source_hashes"] = {name: digest(REPO / name) for name in tracked if (REPO / name).is_file()}
    # Include untracked tests and runtime edits so the recorded fingerprint can
    # be reconstructed from this bundle even without the original worktree.
    source_paths = []
    for directory in ("expgym", "scripts", "schemas", "tests", "configs"):
        source_paths.extend(path for path in (REPO / directory).rglob("*")
                            if path.is_file() and "__pycache__" not in path.parts
                            and path.suffix in {".py", ".sh", ".json", ".yaml", ".yml", ".md"})
    source_paths.extend(REPO / name for name in ("demo_experiment.py", "README.MD", "requirements.txt", "requirements-data.txt"))
    bundle = out / "evaluation-source.tar.gz"
    with tarfile.open(bundle, "w:gz") as archive:
        for path in sorted(source_paths):
            archive.add(path, arcname=path.relative_to(REPO), recursive=False)
    result["source_bundle"] = {"path": str(bundle), "sha256": digest(bundle), "files": len(source_paths)}
    (out / "manifest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if args.checkpoint:
        ckpt = checkpoint_manifest()
        (out / "checkpoint.json").write_text(json.dumps(ckpt, indent=2, ensure_ascii=False) + "\n")
        print(f"checkpoint_valid: {ckpt['tensor_file_count']} shards, {ckpt['tensor_count']} tensors, {ckpt['total_tensor_file_bytes']} bytes")
    print(f"provenance: {out}")


if __name__ == "__main__":
    main()
