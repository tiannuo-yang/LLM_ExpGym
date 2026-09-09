#!/usr/bin/env python3
"""Post-CLI byte/path verification only; no parsing restored experimental payloads."""
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import stat

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent / 'k3_full_remote.0bzBaFG7/repo/results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909'
COLLECTION = RELEASE / 'payload/collection/INDEX.json'
COLLECTION_SHA = 'a78227369423e71e8c4380e46416b8a4ed88464f3e8a502fe1747e7e703103f5'
OUTPUT = HERE / 'restored'
metadata = {}


def need(condition, code):
    if not condition:
        raise RuntimeError(code)


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n').encode()


def signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def path_safe(path):
    need('..' not in path.parts, 'parent_component')
    need(all(not p.is_symlink() for p in [path, *path.parents]), 'symlink')


def digest(path, limit=100 * 1024**2):
    path_safe(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'file_type_or_size')
    sha, count = hashlib.sha256(), 0
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as handle:
        opened = os.fstat(handle.fileno())
        for chunk in iter(lambda: handle.read(1024**2), b''):
            count += len(chunk); need(count <= limit, 'size_growth'); sha.update(chunk)
        after = os.fstat(handle.fileno())
    need(signature(before) == signature(opened) == signature(after) == signature(path.lstat()) and count == before.st_size, 'unstable_file')
    return count, sha.hexdigest()


def load(path, expected=None):
    size, actual = digest(path, 8 * 1024**2)
    need(expected is None or actual == expected, 'metadata_sha')
    raw = path.read_bytes()
    need((len(raw), hashlib.sha256(raw).hexdigest()) == (size, actual), 'metadata_changed')
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate_key'); result[key] = value
        return result
    def reject(_value):
        raise RuntimeError('nonfinite_number')
    metadata[path] = (size, actual)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)


def relative(name):
    need(type(name) is str and name, 'relative_type')
    p = PurePosixPath(name)
    need(not p.is_absolute() and '..' not in p.parts and p.as_posix() == name, 'unsafe_relative')
    return p


def tree(root):
    found = set()
    def error(_exc):
        raise RuntimeError('directory_read')
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=error):
        for name in dirs + files:
            path = Path(directory) / name; path_safe(path)
        for name in files:
            path = Path(directory) / name
            need(stat.S_ISREG(path.lstat().st_mode), 'nonregular_member')
            found.add(path.relative_to(root).as_posix())
    return found


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    exit_record = load(HERE / 'CLI_EXIT.json')
    need(exit_record['actual_exit_code'] == 0 and exit_record['collection_index_sha256'] == COLLECTION_SHA
         and exit_record['remote_commit'] == 'ac9a621c98ade026d3562a3c1b50206de16e4a89', 'cli_not_success')
    need(not (OUTPUT / 'COLLECTION_INCOMPLETE.json').exists(), 'collection_incomplete')
    collection = load(COLLECTION, COLLECTION_SHA)
    need((collection['bundle_count'], collection['file_count'], collection['original_bytes']) == (34, 65105, 1521531633), 'collection_totals')
    need(load(OUTPUT / 'COLLECTION_INDEX.json', COLLECTION_SHA) == collection, 'copied_collection')
    complete = load(OUTPUT / 'COLLECTION_COMPLETE.json')
    expected_files = {'COLLECTION_INDEX.json', 'COLLECTION_COMPLETE.json', 'OWNERSHIP_INDEX.json'}
    owners, completed, navigation, receipts = set(), [], [], []
    for row in collection['bundles']:
        bid = row['bundle_id']; relative(bid)
        source_index = COLLECTION.parent / relative(row['index'])
        index = load(source_index, row['sha256'])
        copied_index = OUTPUT / 'metadata' / bid / 'INDEX.json'
        need(load(copied_index, row['sha256']) == index, 'copied_index')
        expected_files.add(copied_index.relative_to(OUTPUT).as_posix())
        rows = []
        for shard in index['shards']:
            source_page = source_index.parent / relative(shard['index'])
            page = load(source_page, shard['index_sha256'])
            need(metadata[source_page][0] == shard['index_bytes'] and len(page['files']) == shard['file_count'], 'member_page_totals')
            copied_page = OUTPUT / 'metadata' / bid / relative(shard['index'])
            need(load(copied_page, shard['index_sha256']) == page, 'copied_page')
            expected_files.add(copied_page.relative_to(OUTPUT).as_posix())
            rows.extend(page['files'])
        rows.sort(key=lambda item: item['path'])
        paths = [item['path'] for item in rows]
        need(len(set(paths)) == len(paths) and not owners.intersection(paths), 'duplicate_original_path')
        owners.update(paths)
        size = sum(item['bytes'] for item in rows)
        need((len(rows), size) == (row['file_count'], row['original_bytes']) == (index['file_count'], index['original_bytes']), 'bundle_totals')
        for item in rows:
            path = OUTPUT / bid / 'payload' / relative(item['path'])
            need(digest(path) == (item['bytes'], item['sha256']), 'restored_original_byte_sha')
            expected_files.add(path.relative_to(OUTPUT).as_posix())
        inventory_sha = hashlib.sha256(b''.join(encoded(item) for item in rows)).hexdigest()
        record = dict(schema='completed-directory-v1', complete=True, payload='payload',
                      binding=dict(kind='restored-originals', input_sha256=row['sha256'], single_archive=False),
                      file_count=len(rows), bytes=size, inventory_sha256=inventory_sha)
        complete_path = OUTPUT / bid / 'COMPLETE.json'
        need(load(complete_path) == record, 'bundle_complete')
        expected_files.add(complete_path.relative_to(OUTPUT).as_posix())
        completed.append(dict(bundle_id=bid, completion_sha256=metadata[complete_path][1]))
        navigation.append({**row, 'restored_payload': bid + '/payload', 'copied_member_index': 'metadata/' + bid + '/INDEX.json'})
        receipts.append(dict(bundle_id=bid, file_count=len(rows), original_bytes=size, complete_path_bytes_sha_match=True,
                             original_inventory_sha256=inventory_sha, completion_sha256=metadata[complete_path][1]))
        print(json.dumps(dict(verified_bundles=len(receipts), verified_files=sum(v['file_count'] for v in receipts))), flush=True)
    need(len(owners) == 65105 and sum(v['original_bytes'] for v in receipts) == 1521531633, 'global_totals')
    need(all(not any(p.as_posix() in owners for p in PurePosixPath(name).parents if p.as_posix() != '.') for name in owners), 'path_prefix_collision')
    ownership = load(OUTPUT / 'OWNERSHIP_INDEX.json')
    need(ownership == dict(schema='collection-path-ownership-v1', bundles=navigation,
         lookup='Read copied_member_index then its indexes/*.json; row.path belongs under restored_payload. Copied metadata is not a standalone archive bundle.'), 'ownership')
    expected_complete = dict(schema='whole-file-collection-complete-v1', complete=True, input_sha256=COLLECTION_SHA,
          bundle_count=34, file_count=65105, original_bytes=1521531633, bundles=completed,
          ownership_index_sha256=metadata[OUTPUT / 'OWNERSHIP_INDEX.json'][1], known_secret_sources_checked=0,
          modes_timestamps_ownership_preserved=False, publication_performed=False, remote_restore_performed=False)
    need(complete == expected_complete and tree(OUTPUT) == expected_files, 'complete_or_exact_output_tree')
    need(all(digest(path, 8 * 1024**2) == expected for path, expected in metadata.items()), 'metadata_changed_after')
    receipt = dict(schema='remote-public-restore-independent-file-verification-v1', passed=True,
          utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), remote_commit=exit_record['remote_commit'],
          root_remote_verification_sha256='7712d9884774e4f4e8750c2bdb3788d04bc78341dd6c10377d02e60fa9fbcc5e',
          collection_index_sha256=COLLECTION_SHA, collection_complete_sha256=metadata[OUTPUT / 'COLLECTION_COMPLETE.json'][1],
          cli_exit_receipt_sha256=metadata[HERE / 'CLI_EXIT.json'][1], verifier_sha256=digest(Path(__file__))[1],
          bundle_count=34, file_count=65105, original_bytes=1521531633, restored_output_file_count=len(expected_files),
          complete_original_path_bytes_sha_match=True, exact_output_file_set=True, incomplete_absent=True,
          remote_clone_inputs=True, private_keys_read=False, restored_experimental_payload_parsed=False,
          posix_metadata_preserved=False, restore_retry=False, bundles=receipts)
    with (HERE / 'POST_RESTORE_VERIFICATION.json').open('xb') as handle:
        handle.write(encoded(receipt)); handle.flush(); os.fsync(handle.fileno())
    print(json.dumps(dict(passed=True, bundle_count=34, file_count=65105, original_bytes=1521531633)), flush=True)


if __name__ == '__main__':
    main()
