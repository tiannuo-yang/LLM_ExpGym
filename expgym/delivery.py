"""Explicit-list, bounded-payload-memory delivery; no models or recursive walks.

Integrity is not secret clearance. Public sealing reuses the exact historical
scanner; local-only archives are deliberately marked unsuitable for publication.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import stat
import tarfile
import types
from typing import BinaryIO, Optional, Sequence


BLOCK = 1024 * 1024
SHARD_BYTES = 64 * 1024 * 1024
SHARD_FILES = 2000
SCHEMA = "expgym.delivery.v1"
SCANNER_SHA256 = "aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116"
DENIED_PARTS = {
    "private", ".git", ".ssh", ".aws", ".config", ".venv", "venv", "env",
    "uv", ".uv", "environments", "cache", ".cache", "__pycache__", "weights",
    "ckpts", "checkpoints", "node_modules", "router_api_key", "id_rsa",
    "id_ed25519", "credentials",
}
DENIED_SUFFIXES = {
    ".safetensors", ".bin", ".pt", ".pth", ".ckpt", ".pkl", ".pickle",
    ".pem", ".key", ".p12", ".pfx", ".pyc", ".so", ".dll",
}


class DeliveryError(ValueError):
    """Constant diagnostics only: never include payload or credential values."""


def require(ok: bool, rule: str) -> None:
    if not ok:
        raise DeliveryError(rule)


def canonical_path(value: str) -> str:
    require(isinstance(value, str) and bool(value), "invalid_relative_path")
    require(not any(ord(c) < 32 for c in value) and "\\" not in value,
            "invalid_relative_path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(p not in ("", ".", "..")
            for p in value.split("/")), "path_escape_or_ambiguity")
    for part in path.parts:
        lower = part.lower()
        require(lower not in DENIED_PARTS and lower != ".env"
                and not lower.startswith(".env.")
                and not lower.endswith(("_api_key", "_private_key")), "forbidden_path")
    require(path.suffix.lower() not in DENIED_SUFFIXES, "forbidden_path")
    return value


def validate_paths(paths: Sequence[str]) -> list[str]:
    require(isinstance(paths, (list, tuple)) and bool(paths), "explicit_nonempty_list_required")
    result = sorted(canonical_path(p) for p in paths)
    require(len(set(result)) == len(result), "duplicate_path")
    names = set(result)
    require(not any(str(parent) in names for name in result
                    for parent in PurePosixPath(name).parents if str(parent) != "."),
            "file_directory_prefix_conflict")
    return result


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def read_json(path: Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=_object)


def _signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def _root(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        require(stat.S_ISDIR(current.lstat().st_mode), "non_directory_or_symlink_root")
    return path


def _open_source(root: Path, name: str) -> BinaryIO:
    """Walk via directory descriptors: no intermediate or leaf symlink follows."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    descriptor = os.open(root, flags | os.O_DIRECTORY)
    try:
        for part in PurePosixPath(name).parts[:-1]:
            child = os.open(part, flags | os.O_DIRECTORY, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        leaf = os.open(PurePosixPath(name).name, flags, dir_fd=descriptor)
    finally:
        os.close(descriptor)
    handle = os.fdopen(leaf, "rb")
    if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
        handle.close()
        raise DeliveryError("non_regular_source")
    return handle


class HashStream:
    def __init__(self, handle: BinaryIO, collect: bool = False, forbidden: Sequence[bytes] = ()):
        self.handle = handle
        self.digest = hashlib.sha256()
        self.size = 0
        self.collected = bytearray() if collect else None
        self.forbidden = forbidden
        self.tail = b""
        self.overlap = max((len(value) - 1 for value in forbidden), default=0)

    def read(self, size: int = -1) -> bytes:
        require(size >= 0, "unbounded_payload_read")
        data = self.handle.read(size)
        self.digest.update(data)
        self.size += len(data)
        if self.collected is not None:
            self.collected.extend(data)
        return data

    def write(self, data: bytes) -> int:
        # Original inspect_archive also rejects known values in compressed
        # bytes. Preserve that rule without buffering the complete archive.
        if self.forbidden:
            sample = self.tail + data
            require(not any(value in sample for value in self.forbidden),
                    "original_security_policy_rejected_compressed_bytes")
            self.tail = sample[-self.overlap:] if self.overlap else b""
        count = self.handle.write(data)
        require(count == len(data), "short_archive_write")
        self.digest.update(data)
        self.size += count
        return count

    def flush(self):
        self.handle.flush()


class OriginalScanner:
    """Reuse policy bytes, including JSON semantics, four known values and limits."""
    def __init__(self, scanner_path: Path, secret_paths: Sequence[Path]):
        require(len(secret_paths) == 4 and len({os.path.abspath(p) for p in secret_paths}) == 4,
                "four_distinct_secret_sources_required")
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        raw = Path(scanner_path).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == SCANNER_SHA256, "scanner_identity_mismatch")
        module = types.ModuleType("expgym_original_publication_scanner")
        exec(compile(raw, "pinned_validate_bundle_v2.py", "exec"), module.__dict__)
        self.policy = module
        self.secrets = module.load_secrets(secret_paths)
        self.advisories = 0

    def scan(self, data: bytes, name: str) -> None:
        errors, notes = self.policy.scan_bytes(data, name, self.secrets)
        require(not errors, "original_security_policy_rejected_payload")
        self.advisories += sum(notes.values())


def seal(root: Path, paths: Sequence[str], output_dir: Path,
         scanner: Optional[OriginalScanner] = None, *,
         shard_bytes: int = SHARD_BYTES, shard_files: int = SHARD_FILES) -> dict:
    """Read each original once. Failed partial output stays private; no manifest."""
    root = _root(root)
    paths = validate_paths(paths)
    require(type(shard_bytes) is int and shard_bytes > 0
            and type(shard_files) is int and shard_files > 0, "invalid_shard_limits")
    output_dir = Path(output_dir)
    _root(output_dir.parent)
    # A fresh private directory avoids replacing an earlier accepted release.
    output_dir.mkdir(mode=0o700)
    # Metadata planning only; content is read once below. A file is never split
    # or renamed, so every original remains independently retrievable.
    groups, current, current_bytes, planned = [], [], 0, {}
    for name in paths:
        with _open_source(root, name) as handle:
            planned[name] = _signature(os.fstat(handle.fileno()))
            size = planned[name][3]
        if current and (len(current) >= shard_files or current_bytes + size > shard_bytes):
            groups.append(current)
            current, current_bytes = [], 0
        current.append(name)
        current_bytes += size
    if current:
        groups.append(current)
    entries, signatures, archives = [], {}, []
    for number, group in enumerate(groups, 1):
        archive_name = "part-%06d.tar.gz" % number
        partial = output_dir / (archive_name + ".partial")
        expanded = 0
        with partial.open("xb") as raw_archive:
            os.fchmod(raw_archive.fileno(), 0o600)
            stream = HashStream(raw_archive, forbidden=[value for value, _ in scanner.secrets] if scanner else ())
            with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as archive:
                    for name in group:
                        if scanner:
                            require(not scanner.policy.denied(name), "original_security_policy_denied_path")
                            scanner.scan(json.dumps({"path": name}).encode(), "member_metadata.json")
                        with _open_source(root, name) as source:
                            before = _signature(os.fstat(source.fileno()))
                            require(before == planned[name], "source_changed_since_shard_plan")
                            size = before[3]
                            expanded += size
                            if scanner:
                                require(size <= scanner.policy.MAX_BYTES, "original_member_size_limit")
                                require(expanded <= scanner.policy.MAX_ARCHIVE_EXPANDED,
                                        "original_archive_expansion_limit")
                            reader = HashStream(source, collect=scanner is not None)
                            header = tarfile.TarInfo(name)
                            header.size, header.mode = size, 0o644
                            archive.addfile(header, reader)
                            require(reader.size == size and not source.read(1), "source_size_changed")
                            require(_signature(os.fstat(source.fileno())) == before, "source_changed_during_seal")
                            if scanner:
                                scanner.scan(bytes(reader.collected), name)
                            entries.append({"path": name, "archive": archive_name,
                                            "bytes": size, "sha256": reader.digest.hexdigest()})
                            signatures[name] = before
            raw_archive.flush()
            os.fsync(raw_archive.fileno())
            archive_size, archive_hash = stream.size, stream.digest.hexdigest()
        if scanner:
            require(archive_size <= scanner.policy.MAX_BYTES, "original_archive_size_limit")
        partial.rename(output_dir / archive_name)
        archives.append({"path": archive_name, "bytes": archive_size, "sha256": archive_hash})
    # Metadata-only end fence; not a second payload read or an atomic snapshot.
    for name in paths:
        with _open_source(root, name) as source:
            require(_signature(os.fstat(source.fileno())) == signatures[name], "source_changed_before_seal_end")
    security = {"public_scan_passed": scanner is not None,
                "scanner_sha256": SCANNER_SHA256 if scanner else None,
                "known_secret_sources": 4 if scanner else 0,
                "advisory_count": scanner.advisories if scanner else None}
    manifest = {"schema": SCHEMA, "archives": archives, "files": entries, "security": security}
    payload = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    if scanner:
        require(len(payload) <= scanner.policy.MAX_BYTES, "original_manifest_size_limit")
        scanner.scan(payload, "manifest.json")
    with (output_dir / "manifest.json").open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return manifest


def _manifest(value: dict) -> dict:
    require(isinstance(value, dict) and set(value) == {
        "schema", "archives", "files", "security"}, "invalid_manifest")
    require(value["schema"] == SCHEMA, "invalid_manifest")
    require(isinstance(value["archives"], list) and bool(value["archives"]), "invalid_archives")
    for number, row in enumerate(value["archives"], 1):
        require(isinstance(row, dict) and set(row) == {"path", "bytes", "sha256"}, "invalid_archive_entry")
        require(row["path"] == "part-%06d.tar.gz" % number, "invalid_archive_path")
        require(type(row["bytes"]) is int and row["bytes"] > 0, "invalid_archive_size")
    archive_names = {row["path"] for row in value["archives"]}
    require(isinstance(value["files"], list) and bool(value["files"]), "invalid_file_inventory")
    for row in value["files"]:
        require(isinstance(row, dict) and set(row) == {"path", "archive", "bytes", "sha256"}, "invalid_file_entry")
        require(isinstance(row["archive"], str) and row["archive"] in archive_names, "invalid_file_archive")
        require(type(row["bytes"]) is int and row["bytes"] >= 0, "invalid_file_size")
    paths = validate_paths([row["path"] for row in value["files"]])
    require(paths == [row["path"] for row in value["files"]], "inventory_not_canonical")
    require({row["archive"] for row in value["files"]} == archive_names, "empty_archive")
    for digest in [row["sha256"] for row in value["archives"] + value["files"]]:
        require(isinstance(digest, str) and len(digest) == 64
                and all(c in "0123456789abcdef" for c in digest), "invalid_sha256")
    security = value["security"]
    require(isinstance(security, dict) and set(security) == {
        "public_scan_passed", "scanner_sha256", "known_secret_sources", "advisory_count"}, "invalid_scan_declaration")
    require(type(security["public_scan_passed"]) is bool, "invalid_scan_declaration")
    if security["public_scan_passed"]:
        require(security["scanner_sha256"] == SCANNER_SHA256
                and type(security["known_secret_sources"]) is int and security["known_secret_sources"] == 4
                and type(security["advisory_count"]) is int and security["advisory_count"] >= 0,
                "invalid_scan_declaration")
    else:
        require(security == {"public_scan_passed": False, "scanner_sha256": None,
                            "known_secret_sources": 0, "advisory_count": None}, "invalid_scan_declaration")
    return value


class TarFramingReader:
    """Check physical tar EOF while tarfile handles PAX names and file payloads.

    gzip.GzipFile validates CRC/footer and concatenated streams; this fence
    rejects hidden tar members/garbage after the first tar end marker.
    """
    def __init__(self, handle):
        self.handle = handle
        self.pending = bytearray()
        self.payload_blocks = 0
        self.zero_blocks = 0

    def read(self, size):
        require(size >= 0, "unbounded_payload_read")
        data = self.handle.read(size)
        self.pending.extend(data)
        complete = len(self.pending) // tarfile.BLOCKSIZE * tarfile.BLOCKSIZE
        for offset in range(0, complete, tarfile.BLOCKSIZE):
            block = bytes(self.pending[offset:offset + tarfile.BLOCKSIZE])
            if self.payload_blocks:
                self.payload_blocks -= 1
            elif block == tarfile.NUL * tarfile.BLOCKSIZE:
                self.zero_blocks += 1
            else:
                require(not self.zero_blocks, "nonzero_data_after_tar_end")
                info = tarfile.TarInfo.frombuf(block, "utf-8", "surrogateescape")
                require(info.size >= 0, "invalid_tar_header_size")
                self.payload_blocks = (info.size + tarfile.BLOCKSIZE - 1) // tarfile.BLOCKSIZE
        del self.pending[:complete]
        if not data:
            require(not self.pending and self.payload_blocks == 0 and self.zero_blocks >= 2,
                    "truncated_tar_framing")
        return data


def verify(archive_dir: Path, manifest: dict, *, restore_dir: Optional[Path] = None,
           selected: Optional[Sequence[str]] = None, require_public_scan: bool = False) -> dict:
    """One compressed/member stream; optionally write selected files only.

    A failing restore directory is incomplete, private, and not rolled back.
    The returned success (or CLI exit zero) is its completion gate.
    """
    manifest = _manifest(manifest)
    archive_dir = _root(archive_dir)
    require(not require_public_scan or manifest["security"]["public_scan_passed"], "local_only_not_publishable")
    expected = {row["path"]: row for row in manifest["files"]}
    wanted = set(validate_paths(selected)) if selected is not None else set()
    require(wanted <= set(expected), "selected_path_not_in_inventory")
    require((restore_dir is not None) == bool(wanted), "restore_requires_explicit_nonempty_selection")
    if restore_dir is not None:
        restore_dir = Path(restore_dir)
        _root(restore_dir.parent)
        restore_dir.mkdir(mode=0o700)
    seen, total = set(), 0
    for archive_row in manifest["archives"]:
        with _open_source(archive_dir, archive_row["path"]) as source:
            before = _signature(os.fstat(source.fileno()))
            require(before[3] == archive_row["bytes"], "archive_size_mismatch")
            stream = HashStream(source)
            with gzip.GzipFile(fileobj=stream, mode="rb") as compressed:
                framed = TarFramingReader(compressed)
                with tarfile.open(fileobj=framed, mode="r|") as archive:
                    for member in archive:
                        name = canonical_path(member.name)
                        require(member.isfile() and not member.issparse(), "archive_link_or_special_member")
                        require(name not in seen and name in expected, "duplicate_or_unexpected_member")
                        require(expected[name]["archive"] == archive_row["path"], "member_in_wrong_archive")
                        require(member.size == expected[name]["bytes"], "member_size_mismatch")
                        seen.add(name)
                        payload = archive.extractfile(member)
                        require(payload is not None, "missing_member_payload")
                        destination = None
                        if name in wanted:
                            target = restore_dir / name
                            target.parent.mkdir(parents=True, exist_ok=True)
                            _root(target.parent)
                            destination = target.open("xb")
                        digest, count = hashlib.sha256(), 0
                        try:
                            while True:
                                block = payload.read(BLOCK)
                                if not block:
                                    break
                                digest.update(block)
                                count += len(block)
                                if destination:
                                    destination.write(block)
                        finally:
                            if destination:
                                destination.close()
                        require(count == expected[name]["bytes"] and digest.hexdigest() == expected[name]["sha256"],
                                "member_bytes_mismatch")
                        total += count
                # Drain through the gzip/framing validators, not around them.
                while framed.read(BLOCK):
                    pass
            require(stream.size == archive_row["bytes"]
                    and stream.digest.hexdigest() == archive_row["sha256"], "archive_bytes_mismatch")
            require(_signature(os.fstat(source.fileno())) == before, "archive_changed_during_verify")
    require(seen == set(expected), "missing_archive_member")
    return {"passed": True, "files": len(seen), "original_bytes": total,
            "archives": len(manifest["archives"]), "restored_files": len(wanted),
            "public_scan_declaration": manifest["security"]["public_scan_passed"]}
