#!/usr/bin/env python3
"""Version 2: explicit sealed files and JSONL, retaining the v1 fail-closed policy.

Forked from validate_bundle.py SHA256
33613ed9b1f35f78cf48c147f4102eb6aaf5549545f9b5e2dbc9c6dfeb0a6295.
No git/network/copy/extraction. The original validator and locks are unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile


WARN_BYTES = 50 * 1024 * 1024
MAX_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_EXPANDED = 512 * 1024 * 1024
DENY_PARTS = {"private", ".git", ".ssh", ".aws", ".config", ".venv", "venv", "env", "uv", ".uv", "environments", "cache", ".cache", "__pycache__", "weights", "ckpts", "checkpoints", "node_modules"}
DENY_SUFFIXES = {".safetensors", ".bin", ".pt", ".pth", ".ckpt", ".pkl", ".pickle", ".pem", ".key", ".p12", ".pfx", ".pyc", ".so", ".dll"}
FIELDS = {"authorization", "proxy_authorization", "api_key", "apikey", "x_api_key", "access_token", "refresh_token", "client_secret", "password", "secret"}
SAFE_PLACEHOLDERS = {"[REDACTED]", "Bearer [REDACTED]", "REDACTED", "EXPGYM_SMOKE_NOAUTH_PLACEHOLDER_20260908_NOT_A_SECRET", "EXPGYM_LOCAL_NOAUTH_PLACEHOLDER_20260907"}
TOKEN_PATTERNS = [
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


class CheckError(Exception):
    """Only safe constant rule identifiers belong in exception messages."""


def relative(value):
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise CheckError("invalid_relative_path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"..", "."} for part in value.split("/")):
        raise CheckError("path_escape_or_ambiguous_path")
    if any(ord(char) < 32 for char in value):
        raise CheckError("control_character_in_path")
    return path


def denied(value):
    path = relative(value)
    for part in path.parts:
        lower = part.lower()
        if (lower in DENY_PARTS or lower == ".env" or lower.startswith(".env.")
                or lower in {"router_api_key", "id_rsa", "id_ed25519", "credentials"}
                or lower.endswith(("_api_key", "_private_key"))):
            return True
    return path.suffix.lower() in DENY_SUFFIXES


def safe_path(workspace, value):
    path = relative(value)
    if denied(value):
        raise CheckError("forbidden_path")
    current = workspace
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise CheckError("symlink_forbidden")
    return current


def stable_read(path, limit=MAX_BYTES):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise CheckError("non_regular_file")
    if before.st_size > limit:
        raise CheckError("github_file_size_block" if limit == MAX_BYTES else "expanded_file_size_block")
    descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            raw = handle.read(limit + 1)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = path.lstat()
    signature = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
    if not (signature(before) == signature(opened) == signature(after) == signature(final)) or len(raw) != before.st_size:
        raise CheckError("file_changed_during_read")
    return raw


def load_secrets(paths):
    """No secret hashing, serialization, snippets or exception values."""
    values = []
    for path in paths:
        # These explicit private inputs are never part of the source whitelist.
        raw = stable_read(Path(path), limit=16384).rstrip(b"\r\n")
        if len(raw) < 8:
            raise CheckError("secret_source_invalid")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise CheckError("secret_source_encoding_invalid")
        values.append((raw, text))
    return values


def business_path(path):
    # Only actual payload content/schema subtrees, not arbitrary metadata keys.
    if "parameters" in path and "tools" in path:
        return True
    if "arguments" in path and ("tool_calls" in path or "function" in path):
        return True
    return "content" in path and ("messages" in path or "message" in path or "tool_result" in path)


def scan_bytes(raw, name, secrets):
    findings, advisories = Counter(), Counter()
    for secret, _ in secrets:
        if secret in raw:
            findings["known_secret_value"] += 1
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        findings["unreviewed_binary_file"] += 1
        return findings, advisories
    for pattern in TOKEN_PATTERNS:
        findings["high_confidence_credential_pattern"] += len(pattern.findall(text))

    def walk(value, path=(), depth=0):
        if depth > 80:
            findings["json_nesting_limit"] += 1
            return
        if isinstance(value, dict):
            if not path and value.get("state") == "in_progress":
                findings["in_progress_artifact"] += 1
            for key, item in value.items():
                key = str(key)
                for _, secret in secrets:
                    if secret in key:
                        findings["known_secret_value"] += 1
                normalized = key.lower().replace("-", "_")
                credential = normalized in FIELDS or normalized.endswith(("_api_key", "_access_token", "_client_secret"))
                if credential and isinstance(item, str) and item.strip() and item not in SAFE_PLACEHOLDERS:
                    if business_path(path + (key,)):
                        advisories["credential_named_business_field"] += 1
                    else:
                        findings["credential_metadata_field"] += 1
                walk(item, path + (key,), depth + 1)
        elif isinstance(value, list):
            for item in value:
                walk(item, path + ("[]",), depth + 1)
        elif isinstance(value, str):
            for _, secret in secrets:
                if secret in value:
                    findings["known_secret_value"] += 1
            for pattern in TOKEN_PATTERNS:
                findings["high_confidence_credential_pattern"] += len(pattern.findall(value))
            # Decode the protocol's explicit raw envelope, not arbitrary user prose.
            if path and path[-1] == "response_raw":
                try:
                    nested = json.loads(value)
                except ValueError:
                    pass
                else:
                    walk(nested, path + ("decoded_envelope",), depth + 1)
    if name.lower().endswith(".jsonl"):
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except (ValueError, RecursionError):
                findings["invalid_jsonl_file"] += 1
            else:
                walk(value)
    elif name.lower().endswith(".json"):
        try:
            value = json.loads(text)
        except (ValueError, RecursionError):
            findings["invalid_json_file"] += 1
        else:
            walk(value)
    return +findings, +advisories


def inspect_archive(raw, secrets):
    members, findings, advisories = [], Counter(), Counter()
    expanded, seen = 0, set()
    for secret, _ in secrets:
        if secret in raw:
            findings["known_secret_value"] += 1
    try:
        with tarfile.open(fileobj=BytesIO(raw), mode="r:gz") as archive:
            errors, notes = scan_bytes(json.dumps(archive.pax_headers).encode(), "archive_header.json", secrets)
            findings.update(errors); advisories.update(notes)
            for member in archive:
                name = member.name.rstrip("/")
                errors, notes = scan_bytes(json.dumps({"name": name, "pax_headers": member.pax_headers,
                                                       "uname": member.uname, "gname": member.gname}).encode(), "member_metadata.json", secrets)
                findings.update(errors); advisories.update(notes)
                if errors:
                    continue
                try:
                    if denied(name):
                        raise CheckError("forbidden_archive_member")
                except CheckError:
                    findings["forbidden_archive_member"] += 1
                    continue
                if name in seen:
                    findings["duplicate_archive_member"] += 1
                seen.add(name)
                if member.isdir():
                    continue
                if not member.isfile():
                    findings["archive_link_or_special_member"] += 1
                    continue
                expanded += member.size
                if member.size > MAX_BYTES or expanded > MAX_ARCHIVE_EXPANDED:
                    findings["archive_expansion_limit"] += 1
                    break
                handle = archive.extractfile(member)
                if handle is None:
                    findings["archive_read_error"] += 1
                    continue
                data = handle.read(MAX_BYTES + 1)
                if len(data) != member.size:
                    findings["archive_member_size_mismatch"] += 1
                    continue
                errors, notes = scan_bytes(data, name, secrets)
                findings.update(errors); advisories.update(notes)
                # Never produce a SHA inventory for rejected secret-bearing data.
                if not errors:
                    members.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    except (tarfile.TarError, OSError, EOFError, ValueError):
        findings["invalid_source_archive"] += 1
    return members, +findings, +advisories


def tree_files(root):
    result = []
    for directory, names, files in os.walk(root, followlinks=False):
        for name in names:
            path = Path(directory) / name
            relative_name = path.relative_to(root).as_posix()
            if path.is_symlink() or denied(relative_name):
                raise CheckError("forbidden_or_linked_directory")
        for name in files:
            path = Path(directory) / name
            relative_name = path.relative_to(root).as_posix()
            if path.is_symlink() or denied(relative_name):
                raise CheckError("forbidden_or_linked_file")
            result.append(relative_name)
    return sorted(result)


def validate(spec, workspace, secrets, seal=False):
    """All errors contain only rule codes and safe relative source paths."""
    if spec.get("approved") is not True or not spec.get("artifacts"):
        raise CheckError("spec_not_approved_or_empty")
    spec_errors, _ = scan_bytes(json.dumps(spec).encode(), "spec.json", secrets)
    if spec_errors:
        raise CheckError("unsafe_spec")
    if spec.get("require_secret_sources") is True and not secrets:
        raise CheckError("required_secret_scan_missing")
    artifacts = spec["artifacts"]
    if any(item.get("sealed") is not True for item in artifacts):
        raise CheckError("active_or_unsealed_artifact")
    workspace = Path(workspace).resolve()
    result = {"schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": spec.get("scope"), "safe_to_stage": False, "publication_performed": False,
              "secret_sources_checked": len(secrets), "files": [], "archive_members": [],
              "findings": [], "advisories": [], "artifacts": []}
    result["spec_canonical_sha256"] = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    result["validator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    identities, targets = set(), set()
    lock = json.loads(json.dumps(spec))
    for item, locked in zip(artifacts, lock["artifacts"]):
        artifact_id = item["id"]
        if not isinstance(artifact_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", artifact_id) or artifact_id in identities:
            raise CheckError("invalid_or_duplicate_artifact_id")
        identities.add(artifact_id)
        source_name = relative(item["source"]).as_posix()
        target_root = relative(item["target"]).as_posix()
        if denied(target_root):
            raise CheckError("forbidden_target_path")
        artifact_errors, artifact_notes = Counter(), Counter()
        records, member_records = [], []
        try:
            source = safe_path(workspace, source_name)
            kind = item["kind"]
            if kind not in {"sealed_directory", "source_archive", "sealed_file"}:
                raise CheckError("unknown_artifact_kind")
            if not isinstance(item.get("anchor"), dict):
                raise CheckError("missing_sealed_anchor")
            anchor = item["anchor"]
            if not re.fullmatch(r"[0-9a-f]{64}", anchor.get("sha256", "")):
                raise CheckError("invalid_anchor_sha256")
            if kind == "sealed_directory":
                if not source.is_dir():
                    raise CheckError("source_not_directory")
                before = tree_files(source)
                relative(anchor["path"])
                if anchor["path"] not in before:
                    raise CheckError("anchor_not_in_artifact")
                files = before
            else:
                if kind == "source_archive" and not source_name.endswith(".tar.gz"):
                    raise CheckError("source_archive_must_be_tar_gz")
                if anchor.get("path") != source.name:
                    raise CheckError("archive_anchor_path_mismatch")
                before = [source.name]
                files = [source.name]
            expected = {entry["path"]: entry for entry in item.get("files", [])}
            if not seal and (len(expected) != len(item.get("files", [])) or sorted(expected) != before):
                raise CheckError("file_inventory_mismatch")
            stamps = {}
            signature = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
            for name in files:
                path = source / name if kind == "sealed_directory" else source
                file_source = source_name + "/" + name if kind == "sealed_directory" else source_name
                target = target_root + "/" + name if kind == "sealed_directory" else target_root
                if target in targets:
                    raise CheckError("duplicate_target_path")
                targets.add(target)
                stamps[path] = signature(path.lstat())
                raw = stable_read(path)
                if kind == "source_archive":
                    members, errors, notes = inspect_archive(raw, secrets)
                    member_records = [{"artifact_id": artifact_id, **entry} for entry in members]
                else:
                    errors, notes = scan_bytes(raw, name, secrets)
                artifact_errors.update(errors); artifact_notes.update(notes)
                for rule, count in errors.items():
                    result["findings"].append({"artifact_id": artifact_id, "path": file_source, "rule": rule, "count": count})
                for rule, count in notes.items():
                    result["advisories"].append({"artifact_id": artifact_id, "path": file_source, "rule": rule, "count": count})
                if errors:
                    continue
                checksum = hashlib.sha256(raw).hexdigest()
                record = {"artifact_id": artifact_id, "source": file_source, "target": target,
                          "path": name, "bytes": len(raw), "sha256": checksum}
                if not seal and (expected[name]["bytes"] != len(raw) or expected[name]["sha256"] != checksum):
                    artifact_errors["file_digest_or_size_mismatch"] += 1
                if name == anchor.get("path") or kind == "source_archive":
                    if anchor.get("sha256") != checksum:
                        artifact_errors["sealed_anchor_sha_mismatch"] += 1
                if len(raw) > WARN_BYTES:
                    result["advisories"].append({"artifact_id": artifact_id, "path": file_source, "rule": "github_file_size_warning", "count": 1})
                records.append(record)
            if kind == "sealed_directory" and tree_files(source) != before:
                artifact_errors["directory_changed_during_scan"] += 1
            if any(signature(path.lstat()) != stamp for path, stamp in stamps.items()):
                artifact_errors["file_changed_during_scan"] += 1
        except (OSError, KeyError, TypeError, ValueError, CheckError) as exc:
            artifact_errors[str(exc) if isinstance(exc, CheckError) else "source_or_spec_read_error"] += 1
        if artifact_errors:
            existing = {entry["rule"] for entry in result["findings"] if entry["artifact_id"] == artifact_id}
            for rule, count in artifact_errors.items():
                if rule not in existing:
                    result["findings"].append({"artifact_id": artifact_id, "path": source_name, "rule": rule, "count": count})
        else:
            result["files"].extend(records)
            result["archive_members"].extend(member_records)
            locked["files"] = [{key: record[key] for key in ("path", "bytes", "sha256")} for record in records]
        result["artifacts"].append({"id": artifact_id, "sealed": item["sealed"], "file_count": len(records), "passed": not artifact_errors})
    result["safe_to_stage"] = not result["findings"]
    missing = sorted(set(spec.get("required_stages", [])) - identities)
    result["missing_required_stages"] = missing
    result["all_required_stages_present"] = not missing
    result["complete_project_publishable"] = result["safe_to_stage"] and not missing
    result["total_bytes"] = sum(item["bytes"] for item in result["files"])
    result["github_regular_git_limits_bytes"] = {"warning_above": WARN_BYTES, "block_above": MAX_BYTES}
    result["finding_counts"] = dict(Counter({rule: sum(x["count"] for x in result["findings"] if x["rule"] == rule) for rule in {x["rule"] for x in result["findings"]}}))
    return result, lock


def main(argv=None):
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            raise CheckError("invalid_arguments")
    try:
        parser = SafeParser(description=__doc__)
        parser.add_argument("--spec", required=True)
        parser.add_argument("--workspace", default=str(Path(__file__).resolve().parent.parent))
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--secret-file", action="append", default=[])
        parser.add_argument("--seal", action="store_true", help="Build a complete inventory only for explicitly approved sealed artifacts.")
        args = parser.parse_args(argv)
        spec = json.loads(Path(args.spec).read_text())
        if spec.get("approved") is not True:
            raise CheckError("spec_not_approved_or_empty")
        secrets = load_secrets(args.secret_file)
        result, lock = validate(spec, args.workspace, secrets, seal=args.seal)
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=False)
        # Generated reports contain no input snippets or secret fingerprints.
        for name, value in (("manifest.json", result), ("lock.json", lock if result["safe_to_stage"] else {"valid": False, "reason": "security_or_integrity_check_failed"})):
            with (output / name).open("x", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
        print(json.dumps({"safe_to_stage": result["safe_to_stage"], "complete_project_publishable": result["complete_project_publishable"], "files": len(result["files"]), "findings": len(result["findings"]), "publication_performed": False}))
        return 0 if result["safe_to_stage"] else 1
    except Exception as exc:
        print(json.dumps({"safe_to_stage": False, "rule": str(exc) if isinstance(exc, CheckError) else "validation_failed", "publication_performed": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
