"""Bounded helpers; the original publication scanner is hash-pinned, not edited."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat

SCANNER_SHA = "aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116"
COMPRESSED = 48 * 1024**2
EXPANDED = 256 * 1024**2
MEMBER = 100 * 1024**2
INDEX_LIMIT = 8 * 1024**2
MAX_FILES = 256
MAX_SHARDS = 4096
BLOCK = 1024 * 1024
_SCANNER = None


class DeliveryError(Exception):
    pass


def need(value, code):
    if not value:
        raise DeliveryError(code)


def scanner():
    global _SCANNER
    path = Path(__file__).resolve().parents[1] / "validate_bundle_v2.py"
    need(hashlib.sha256(path.read_bytes()).hexdigest() == SCANNER_SHA, "scanner_identity")
    if _SCANNER is not None:
        return _SCANNER
    spec = importlib.util.spec_from_file_location("frozen_delivery_scanner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _SCANNER = module
    return module


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checksum(value):
    need(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "invalid_sha256")
    return value


def number(value, maximum, code, minimum=0):
    need(type(value) is int and minimum <= value <= maximum, code)
    return value


def relative(value):
    s = scanner()
    path = s.relative(value)
    need(path.as_posix() == value and not s.denied(value), "unsafe_relative_path")
    need(len(value.encode()) <= 4096, "path_too_long")
    return path


def lexical(path):
    path = Path(path)
    need(".." not in path.parts, "parent_path_component")
    path = path.absolute()
    for part in [*reversed(path.parents), path]:
        need(not part.is_symlink(), "symlink_path")
    return path


def fresh(path):
    path = lexical(path)
    need(not path.exists() and path.parent.is_dir(), "destination_not_fresh_or_parent_missing")
    return path


def signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def stream_hash(path, limit=MEMBER):
    path = lexical(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size <= limit, "file_type_or_size")
    digest = hashlib.sha256()
    with os.fdopen(os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "rb") as source:
        opened = os.fstat(source.fileno())
        total = 0
        while True:
            chunk = source.read(BLOCK)
            if not chunk:
                break
            total += len(chunk)
            need(total <= limit, "file_grew_over_limit")
            digest.update(chunk)
        after = os.fstat(source.fileno())
    need(signature(before) == signature(opened) == signature(after) == signature(path.lstat())
         and total == before.st_size, "file_changed_during_read")
    return total, digest.hexdigest()


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    def reject(_value):
        raise DeliveryError("nonfinite_json")
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=reject)
    except (ValueError, RecursionError, UnicodeError):
        raise DeliveryError("invalid_json") from None


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode()


def scan(raw, name, secrets):
    """Original full-buffer rules plus strict JSON and cross-field known secrets.

    Additive fail-closed check: concatenate decoded string values in document
    order (keys separately), retaining only a secret-length rolling suffix.
    It may conservatively reject coincidental field concatenations. No content
    or secret fingerprint is returned or written.
    """
    errors, notes = scanner().scan_bytes(raw, name, secrets)
    need(not errors, "security_scan_failed")
    if name.lower().endswith((".json", ".jsonl")):
        values = [strict_json(line) for line in raw.splitlines() if line.strip()] if name.lower().endswith(".jsonl") else [strict_json(raw)]
        width = max([len(secret) for _, secret in secrets] + [1])
        tails = {"keys": "", "values": "", "tokens": ""}
        def consume(text, kind):
            joined = tails[kind] + text
            need(not any(secret in joined for _, secret in secrets), "known_secret_across_fields")
            tails[kind] = joined[-(width - 1):] if width > 1 else ""
        def walk(value, depth=0, field=None):
            need(depth <= 80, "json_nesting_limit")
            if isinstance(value, dict):
                for key, child in value.items():
                    consume(key, "keys")
                    consume(key, "tokens")
                    walk(child, depth + 1, key)
            elif isinstance(value, list):
                for child in value:
                    walk(child, depth + 1)
            elif isinstance(value, str):
                consume(value, "values")
                consume(value, "tokens")
                if field == "response_raw":
                    try:
                        nested = strict_json(value)
                    except DeliveryError:
                        # Non-JSON response text is allowed; JSON-looking broken
                        # protocol envelopes are not a duplicate-key bypass.
                        need(not value.lstrip().startswith(("{", "[")), "invalid_nested_envelope")
                    else:
                        walk(nested, depth + 1)
        for value in values:
            walk(value)
    return dict(notes)


def load_json(path, expected=None, secrets=()):
    path = lexical(path)
    raw = scanner().stable_read(path, limit=INDEX_LIMIT)
    if expected is not None:
        need(sha(raw) == checksum(expected), "external_digest_mismatch")
    scan(raw, path.name, secrets)
    return strict_json(raw), raw


def validate_rows(rows):
    need(isinstance(rows, list) and 0 < len(rows) <= MAX_FILES, "member_count_limit")
    seen = set()
    for row in rows:
        need(isinstance(row, dict) and set(row) == {"path", "bytes", "sha256"}, "member_row_schema")
        path = str(relative(row["path"]))
        need(path not in seen, "duplicate_original_path")
        seen.add(path)
        number(row["bytes"], MEMBER, "member_size_limit")
        checksum(row["sha256"])
    need(rows == sorted(rows, key=lambda x: x["path"]), "member_order")
    no_path_prefixes(seen)
    return seen


def no_path_prefixes(paths):
    paths = set(paths)
    for path in paths:
        need(not any(parent.as_posix() in paths for parent in relative(path).parents
                     if parent.as_posix() != "."), "file_directory_path_collision")


def inventory(root):
    rows = []
    for name in sorted(tree(root)):
        size,digest = stream_hash(root/name)
        rows.append({"path":name,"bytes":size,"sha256":digest})
    need(rows,"empty_committed_payload")
    return rows


def completion_record(rows, binding):
    # Hash of canonical sorted whole-file rows; root metadata remains small.
    digest = hashlib.sha256()
    for row in rows:
        digest.update(encoded(row))
    return {"schema":"completed-directory-v1","complete":True,"payload":"payload","binding":binding,
            "file_count":len(rows),"bytes":sum(row["bytes"] for row in rows),"inventory_sha256":digest.hexdigest()}


def verify_completion(root, binding, secrets=()):
    root = lexical(root)
    record,raw = load_json(root/"COMPLETE.json",secrets=secrets)
    rows = inventory(root/"payload")
    need(record == completion_record(rows,binding),"completion_identity_or_inventory")
    need(tree(root) == {"COMPLETE.json"} | {"payload/"+r["path"] for r in rows},"completion_unlisted_file")
    return sha(raw)


def commit_new_directory(source, destination, binding, secrets=()):
    """Exclusive mkdir + verified payload + COMPLETE last; no directory rename.

    Lustre may not support RENAME_NOREPLACE. A crash may leave an incomplete
    wrapper, never a success marker unless the exact payload is validated.
    No overwrite, automatic resume or deletion of a failed output is provided.
    Scratch and destination share a filesystem: only our scratch files are
    hardlinked into fresh paths, not any original source artifact.
    """
    source = lexical(source)
    rows = inventory(source)
    destination = fresh(destination)
    try:
        destination.mkdir(mode=0o700)
    except FileExistsError:
        raise DeliveryError("destination_claim_failed") from None
    payload = destination/"payload"; payload.mkdir(mode=0o700)
    for row in rows:
        target = payload/row["path"]
        lexical(target.parent)
        target.parent.mkdir(parents=True,exist_ok=True)
        lexical(target)
        os.link(source/row["path"],target,follow_symlinks=False)
    need(inventory(payload) == rows,"committed_payload_differs")
    # Persist payload and directory entries before the success marker.
    for row in rows:
        descriptor = os.open(payload/row["path"],os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    directories = [Path(root) for root,_dirs,_files in os.walk(payload)]
    for directory in reversed(directories):
        sync_directory(directory)
    sync_directory(destination)
    raw = encoded(completion_record(rows,binding))
    scan(raw,"COMPLETE.json",secrets)
    write_new(destination/"COMPLETE.json",raw)
    sync_directory(destination)
    sync_directory(destination.parent)
    return verify_completion(destination,binding,secrets)


def sync_directory(path):
    lexical(path)
    descriptor = os.open(path,os.O_RDONLY|getattr(os,"O_DIRECTORY",0)|getattr(os,"O_NOFOLLOW",0))
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def tree(root):
    root = lexical(root)
    result = set()
    def onerror(_error):
        raise DeliveryError("directory_read_error")
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
        for name in dirs + files:
            path = Path(directory) / name
            lexical(path)
            relative(path.relative_to(root).as_posix())
        for name in files:
            path = Path(directory) / name
            need(stat.S_ISREG(path.lstat().st_mode), "non_regular_tree_member")
            result.add(path.relative_to(root).as_posix())
    return result


def write_new(path, raw):
    lexical(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
