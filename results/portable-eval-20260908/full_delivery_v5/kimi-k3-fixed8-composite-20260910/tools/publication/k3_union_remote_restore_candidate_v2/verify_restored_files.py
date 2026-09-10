#!/usr/bin/env python3
"""Post-CLI byte/path verification only; no parsing restored experimental payloads."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import re
import stat

TOTALS = (36, 66643, 1751137861)
RAW_COUNTS = {**{'batch-%06d' % i: 2000 if i < 33 else 188 for i in range(1, 34)},
              'recovery-raw-000001': 1072}
RAW_TOTALS = (65260, 1303033772)
CONTROL_TOTALS = {'controls': (917, 253018660),
                  'recovery-controls-000001': (466, 195085429)}
RAW_CATEGORIES = {**{'batch-%06d' % i: 'original-node-failure' for i in range(1, 34)},
                  'recovery-raw-000001': 'recovery-raw'}
CONTROL_CATEGORIES = {'controls': 'controls', 'recovery-controls-000001': 'recovery-controls'}
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


def main(args):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    RELEASE, OUTPUT = args.release_root, args.restored_root
    COLLECTION = RELEASE / 'INDEX.kimi-k3-composite-v1.json'
    COLLECTION_SHA, REMOTE_COMMIT = args.collection_sha256, args.remote_commit
    for value in (COLLECTION_SHA, args.root_remote_proof_sha256, args.cli_exit_sha256):
        need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'explicit_sha256_required')
    need(type(REMOTE_COMMIT) is str and re.fullmatch('[0-9a-f]{40}', REMOTE_COMMIT) is not None, 'explicit_commit_required')
    paths = (RELEASE, OUTPUT, args.root_remote_proof, args.cli_exit, args.output_receipt)
    for p in paths:
        need(p.is_absolute() and p.resolve() == p, 'absolute_nonalias_binding')
        path_safe(p)
    need(RELEASE.is_dir() and OUTPUT.is_dir(), 'existing_release_and_restored_roots_required')
    need(not args.output_receipt.exists() and args.output_receipt.parent.is_dir(), 'fresh_receipt_required')
    need(all(args.output_receipt != p and p not in args.output_receipt.parents
             and args.output_receipt not in p.parents for p in (RELEASE, OUTPUT)), 'receipt_input_overlap')
    need(args.output_receipt not in (args.root_remote_proof, args.cli_exit), 'receipt_control_overlap')
    metadata.clear()
    # ROOT validates the Git/fresh-clone proof's semantics before actual GO.
    # This post-verifier binds its bytes, and never claims to rerun Git verification.
    need(type(load(args.root_remote_proof, args.root_remote_proof_sha256)) is dict, 'root_proof_object')
    exit_record = load(args.cli_exit, args.cli_exit_sha256)
    need(type(exit_record['actual_exit_code']) is int and exit_record['actual_exit_code'] == 0
         and exit_record['collection_index_sha256'] == COLLECTION_SHA
         and exit_record['remote_commit'] == REMOTE_COMMIT, 'cli_not_success')
    need(not (OUTPUT / 'COLLECTION_INCOMPLETE.json').exists(), 'collection_incomplete')
    collection = load(COLLECTION, COLLECTION_SHA)
    need((collection['bundle_count'], collection['file_count'], collection['original_bytes']) == TOTALS, 'collection_totals')
    need(collection.get('schema') == 'whole-file-collection-v1'
         and type(collection.get('bundles')) is list and len(collection['bundles']) == TOTALS[0], 'collection_shape')
    ids = [row['bundle_id'] for row in collection['bundles']]
    need(all(type(bid) is str for bid in ids) and len(set(ids)) == len(ids)
         and set(ids) == set(RAW_COUNTS) | set(CONTROL_TOTALS), 'exact_K3_union_bundle_ids')
    for row in collection['bundles']:
        count, size = row['file_count'], row['original_bytes']
        need(type(count) is int and type(size) is int and count > 0 and size >= 0, 'exact_member_counts')
        if row['bundle_id'] in CONTROL_TOTALS:
            need(row['category'] == CONTROL_CATEGORIES[row['bundle_id']]
                 and (count, size) == CONTROL_TOTALS[row['bundle_id']], 'public_controls_scope')
        else:
            need(row['category'] == RAW_CATEGORIES[row['bundle_id']]
                 and count == RAW_COUNTS[row['bundle_id']], 'fixed_raw_scope')
    raw = [row for row in collection['bundles'] if row['bundle_id'] in RAW_COUNTS]
    need((sum(row['file_count'] for row in raw), sum(row['original_bytes'] for row in raw)) == RAW_TOTALS, 'raw_scope_totals')
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
    need(len(owners) == TOTALS[1] and sum(v['original_bytes'] for v in receipts) == TOTALS[2], 'global_totals')
    need(all(not any(p.as_posix() in owners for p in PurePosixPath(name).parents if p.as_posix() != '.') for name in owners), 'path_prefix_collision')
    ownership = load(OUTPUT / 'OWNERSHIP_INDEX.json')
    need(ownership == dict(schema='collection-path-ownership-v1', bundles=navigation,
         lookup='Read copied_member_index then its indexes/*.json; row.path belongs under restored_payload. Copied metadata is not a standalone archive bundle.'), 'ownership')
    expected_complete = dict(schema='whole-file-collection-complete-v1', complete=True, input_sha256=COLLECTION_SHA,
          bundle_count=TOTALS[0], file_count=TOTALS[1], original_bytes=TOTALS[2], bundles=completed,
          ownership_index_sha256=metadata[OUTPUT / 'OWNERSHIP_INDEX.json'][1], known_secret_sources_checked=0,
          modes_timestamps_ownership_preserved=False, publication_performed=False, remote_restore_performed=False)
    need(complete == expected_complete and tree(OUTPUT) == expected_files, 'complete_or_exact_output_tree')
    need(all(digest(path, 8 * 1024**2) == expected for path, expected in metadata.items()), 'metadata_changed_after')
    receipt = dict(schema='remote-public-restore-independent-file-verification-v1', passed=True,
          utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), remote_commit=exit_record['remote_commit'],
          root_remote_verification_sha256=args.root_remote_proof_sha256,
          root_remote_proof_semantics='ROOT reviewed before actual GO; this verifier binds bytes only',
          collection_index_sha256=COLLECTION_SHA, collection_complete_sha256=metadata[OUTPUT / 'COLLECTION_COMPLETE.json'][1],
          cli_exit_receipt_sha256=metadata[args.cli_exit][1], verifier_sha256=digest(Path(__file__))[1],
          bundle_count=TOTALS[0], file_count=TOTALS[1], original_bytes=TOTALS[2], restored_output_file_count=len(expected_files),
          complete_original_path_bytes_sha_match=True, exact_output_file_set=True, incomplete_absent=True,
          remote_clone_inputs=True, private_keys_read=False, restored_experimental_payload_parsed=False,
          posix_metadata_preserved=False, restore_retry=False, bundles=receipts)
    with args.output_receipt.open('xb') as handle:
        handle.write(encoded(receipt)); handle.flush(); os.fsync(handle.fileno())
    print(json.dumps(dict(passed=True, bundle_count=TOTALS[0], file_count=TOTALS[1], original_bytes=TOTALS[2])), flush=True)


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('release-root', 'restored-root', 'root-remote-proof', 'cli-exit', 'output-receipt'):
        parser.add_argument('--' + name, required=True, type=Path)
    for name in ('collection-sha256', 'remote-commit', 'root-remote-proof-sha256', 'cli-exit-sha256'):
        parser.add_argument('--' + name, required=True)
    main(parser.parse_args())


if __name__ == '__main__':
    cli()
