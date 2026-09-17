#!/usr/bin/env python3
"""Seal explicit run files or stream-verify a delivery without full extraction."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from expgym.delivery import DeliveryError, OriginalScanner, SHARD_BYTES, SHARD_FILES, read_json, seal, verify


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("seal", help="One original read; fresh output directory only")
    pack.add_argument("--root", type=Path, required=True)
    pack.add_argument("--files", type=Path, required=True, help="JSON array of explicit root-relative file paths")
    pack.add_argument("--output-dir", type=Path, required=True)
    pack.add_argument("--shard-bytes", type=int, default=SHARD_BYTES, help="Target original bytes per archive (default 64 MiB)")
    pack.add_argument("--shard-files", type=int, default=SHARD_FILES, help="Maximum original files per archive (default 2000)")
    mode = pack.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local-only", action="store_true", help="Integrity only: NOT cleared for publication")
    mode.add_argument("--scanner", type=Path, help="Exact historical validate_bundle_v2.py; SHA is enforced")
    pack.add_argument("--secret-file", type=Path, action="append", default=[], help="Public seal requires four distinct original sources")
    check = commands.add_parser("verify", help="Archive + every member SHA in one stream, no extraction by default")
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--archive-dir", type=Path, required=True)
    check.add_argument("--require-public-scan", action="store_true")
    check.add_argument("--restore-dir", type=Path)
    check.add_argument("--select", type=Path, help="JSON array of analysis input paths; never implicitly extract all")
    args = parser.parse_args(argv)
    try:
        if args.command == "seal":
            if args.local_only and args.secret_file:
                raise DeliveryError("local_only_must_not_load_secrets")
            scanner = OriginalScanner(args.scanner, args.secret_file) if args.scanner else None
            manifest = seal(args.root, read_json(args.files), args.output_dir, scanner,
                            shard_bytes=args.shard_bytes, shard_files=args.shard_files)
            result = {"sealed": True, "files": len(manifest["files"]),
                      "archives": len(manifest["archives"]),
                      "public_scan_passed": manifest["security"]["public_scan_passed"]}
        else:
            result = verify(args.archive_dir, read_json(args.manifest), restore_dir=args.restore_dir,
                            selected=read_json(args.select) if args.select else None,
                            require_public_scan=args.require_public_scan)
    except Exception as error:
        # Arbitrary OS/scanner exceptions can contain paths; do not print their
        # values when a credential source may be involved.
        code = str(error) if type(error) is DeliveryError else "delivery_operation_failed"
        print(json.dumps({"passed": False, "rule": code}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
