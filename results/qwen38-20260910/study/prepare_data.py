#!/usr/bin/env python3
"""One-time physical copy of this study's explicitly inventoried CPU inputs."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat

WORKSPACE = Path('/lustrefs/users/chufan.shi/codex_space_tn')
STUDY_ROOT = WORKSPACE / 'qwen38_eval_20260910'
SOURCE_ROOT = WORKSPACE / 'LLM_ExpGym_api_studies_20260910/data'
SOURCE_INVENTORY = SOURCE_ROOT.parent / 'studies/api_20260910/common/data_inventory.json'
SOURCE_RUNTIME = SOURCE_INVENTORY.with_name('runtime_manifest.json')
INVENTORY_SHA256 = '0dcd364d3642ddd76dff4e492855fc8a60059a2cda6f243ec65fe742290b64b7'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def signature(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def source_file(relative):
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or not parsed.parts or '..' in parsed.parts or str(parsed) != relative:
        raise ValueError('Unsafe inventory relative path')
    path = SOURCE_ROOT
    for part in parsed.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Source inventory must refer to physical non-symlink files')
    value = path.stat()
    if not stat.S_ISREG(value.st_mode) or value.st_mode & 0o222:
        raise ValueError('Source must be an already frozen ordinary file: ' + relative)
    return path, signature(value)


def main():
    body = SOURCE_INVENTORY.read_bytes()
    if hashlib.sha256(body).hexdigest() != INVENTORY_SHA256:
        raise ValueError('Pinned source inventory identity changed')
    inventory = json.loads(body)
    runtime = json.loads(SOURCE_RUNTIME.read_text())
    if runtime['data_inventory']['sha256'] != INVENTORY_SHA256 or not runtime['passed']:
        raise ValueError('Existing CPU preparation does not bind the pinned data inventory')
    rows = inventory['files']
    if (inventory['schema'] != 'expgym.cpu-data-copy.v1'
            or inventory['destination_root'] != str(SOURCE_ROOT)
            or len(rows) != 249 or sum(row['bytes'] for row in rows) != 240303980
            or len({row['path'] for row in rows}) != len(rows)
            or SOURCE_ROOT.is_symlink()):
        raise ValueError('Unexpected source inventory or source-root identity')
    prepared = []
    for row in rows:
        source, before = source_file(row['path'])
        if before[3] != row['bytes']:
            raise ValueError('Source size differs from inventory: ' + row['path'])
        prepared.append((row, source, before))
    destination = STUDY_ROOT / 'data'
    manifest_path = STUDY_ROOT / 'study/data_inventory.json'
    if destination.exists() or destination.is_symlink() or manifest_path.exists():
        raise ValueError('Fresh data destination and manifest required; never overwrite')
    destination.mkdir(mode=0o755)
    for row, source, before in prepared:
        target = destination / row['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(source), str(target), follow_symlinks=False)
        if signature(source.stat()) != before:
            raise ValueError('Source changed during copy: ' + row['path'])
        if target.stat().st_size != row['bytes'] or sha256(target) != row['sha256']:
            raise ValueError('Copied input failed pinned integrity check: ' + row['path'])
        if (target.stat().st_dev, target.stat().st_ino) == (before[0], before[1]):
            raise ValueError('Destination must not hard-link source')
        target.chmod(0o444)
    for row, source, before in prepared:
        if signature(source.stat()) != before:
            raise ValueError('Source changed before copy completed: ' + row['path'])
    directories = {destination}
    for row in rows:
        parent = (destination / row['path']).parent
        while parent != destination:
            directories.add(parent)
            parent = parent.parent
    for path in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        path.chmod(0o555)
    result = {
        'schema': 'expgym.cpu-data-copy.v1', 'source_root': str(SOURCE_ROOT),
        'destination_root': str(destination), 'file_count': len(rows),
        'bytes': sum(row['bytes'] for row in rows), 'files': rows,
        'excluded_mutable_names': inventory['excluded_mutable_names'],
        'source_inventory': {'path': str(SOURCE_INVENTORY), 'bytes': len(body),
                             'sha256': INVENTORY_SHA256},
        'original_source_root': inventory['source_root'],
        'source_runtime_manifest': {'path': str(SOURCE_RUNTIME),
                                    'bytes': SOURCE_RUNTIME.stat().st_size,
                                    'sha256': sha256(SOURCE_RUNTIME)},
        'verification': 'All destination files SHA256-verified once against the pinned source inventory; source metadata checked before/after copy; no hard links or symlinks; destination files/directories read-only.',
    }
    with manifest_path.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(json.dumps({'file_count': len(rows), 'bytes': result['bytes'],
                      'inventory': str(manifest_path), 'passed': True}))


if __name__ == '__main__':
    main()
