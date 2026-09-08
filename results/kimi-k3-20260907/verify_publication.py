#!/usr/bin/env python3
"""Offline integrity checks for this publication; no third-party packages or API."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    base = Path(__file__).resolve().parent
    manifest = json.loads((base / 'PUBLICATION_MANIFEST.json').read_text())
    failures = []
    checked = 0
    cached = {}

    def check(relative, size, expected):
        nonlocal checked
        path = (base / relative).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            failures.append({'path': relative, 'error': 'missing_or_unsafe'})
            return
        if relative not in cached:
            cached[relative] = (path.stat().st_size, sha256(path))
        actual_size, actual_hash = cached[relative]
        if actual_size != size or actual_hash != expected:
            failures.append({'path': relative, 'error': 'size_or_sha256_mismatch'})
        checked += 1

    for entry in manifest['artifacts']:
        check(entry['path'], entry['bytes'], entry['sha256'])
    frozen = json.loads((base / 'kimi_k3_eval/reports/final/file_integrity.json').read_text())
    prefix = manifest['original_workspace_prefix']
    for entry in frozen['official_generated_files']:
        assert entry['path'].startswith(prefix)
        check(entry['path'][len(prefix):], entry['bytes'], entry['sha256'])
    for reference in frozen['delivery_references']:
        entry = reference['expected']
        assert entry['path'].startswith(prefix)
        check(entry['path'][len(prefix):], entry['bytes'], entry['sha256'])

    links_checked = 0
    for relative in ['README.md', 'kimi_k3_eval/reports/final/OVERVIEW.zh.md']:
        path = base / relative
        for link in re.findall(r'\]\((?:<([^>]+)>|([^\s)]+))\)', path.read_text()):
            target = next(value for value in link if value)
            if target.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            target_path = (path.parent / unquote(target.split('#')[0])).resolve()
            if not target_path.is_relative_to(base) or not target_path.exists():
                failures.append({'path': relative, 'error': 'broken_local_link', 'target': target})
            links_checked += 1

    checksum_path = base / 'PUBLICATION_CHECKSUMS.json'
    if not checksum_path.is_file():
        failures.append({'path': checksum_path.name, 'error': 'missing_publication_checksums'})
    else:
        checksums = json.loads(checksum_path.read_text())
        expected_files = set()
        for entry in checksums['files']:
            expected_files.add(entry['path'])
            check(entry['path'], entry['bytes'], entry['sha256'])
        actual_files = {p.relative_to(base).as_posix() for p in base.rglob('*')
                        if p.is_file() and '__pycache__' not in p.parts and p != checksum_path}
        if actual_files != expected_files:
            failures.append({'error': 'publication_file_set_mismatch',
                             'missing': sorted(expected_files - actual_files),
                             'unexpected': sorted(actual_files - expected_files)})
    result = {'complete': not failures, 'hash_checks': checked,
              'unique_files_hashed': len(cached), 'local_links_checked': links_checked,
              'original_artifact_count': manifest['artifact_count'],
              'original_artifact_bytes': manifest['artifact_bytes'], 'failures': failures}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())
