#!/usr/bin/env python3
"""Public, sequential whole-file collection restore; no merge or private keys."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import resource
import sys

TOOLS = Path(__file__).resolve().parents[1] / 'shard_delivery_candidate_v2'
PINS = {'common.py': '7147524d5799dc1264f088518db19251c5f906bc2da501854ce279f56d73263e',
        'restore.py': 'ec20a0e22c8f810b09e894e0ddc6cc8dec114a66be4fe23cab8a55f3b62ac710',
        '../validate_bundle_v2.py': 'aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116'}
MAX_BUNDLES, MAX_METADATA = 512, 256 * 1024**2


def frozen_tools():
    bodies = {name: (TOOLS / name).read_bytes() for name in PINS}
    if any(hashlib.sha256(bodies[name]).hexdigest() != digest for name, digest in PINS.items()):
        raise ValueError('frozen_tool_identity')
    modules = []
    for name, filename in [('common', 'common.py'), ('collection_original_restore', 'restore.py')]:
        spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(bodies[filename], str(TOOLS / filename), 'exec'), module.__dict__)
        modules.append(module)
    return modules


def preflight(index_path, expected_sha, c):
    expected_sha = c.checksum(expected_sha)
    index_path = c.lexical(index_path)
    metadata, total_read = [], 0
    def read(path, digest=None):
        nonlocal total_read
        obj, raw = c.load_json(path, digest)
        total_read += len(raw)
        c.need(total_read <= MAX_METADATA, 'collection_metadata_limit')
        metadata.append((c.lexical(path), c.sha(raw), len(raw)))
        return obj, raw
    collection, raw = read(index_path, expected_sha)
    c.need(set(collection) == {'schema', 'bundle_count', 'file_count', 'original_bytes', 'bundles'}
           and collection['schema'] == 'whole-file-collection-v1', 'collection_schema')
    bundles = collection['bundles']
    c.need(type(bundles) is list and 0 < len(bundles) <= MAX_BUNDLES, 'collection_bundle_limit')
    c.number(collection['bundle_count'], MAX_BUNDLES, 'bundle_count', 1)
    c.need(collection['bundle_count'] == len(bundles), 'bundle_count_mismatch')
    owners, ids, roots, prepared, total_files, total_bytes = set(), set(), set(), [], 0, 0
    for row in bundles:
        c.need(type(row) is dict and set(row) == {'bundle_id', 'category', 'index', 'sha256', 'file_count', 'original_bytes'}, 'bundle_row_schema')
        for key in ('bundle_id', 'category'):
            c.need(type(row[key]) is str and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', row[key]), 'bundle_id_or_category')
        bid = row['bundle_id']
        c.need(bid not in ids and bid != 'metadata', 'duplicate_or_reserved_bundle_id'); ids.add(bid)
        target = c.lexical(index_path.parent / c.relative(row['index']))
        c.need(target.name == 'INDEX.json' and target.parent.name == 'payload', 'bundle_index_layout')
        root = target.parent.parent
        c.need(root not in roots and all(root not in r.parents and r not in root.parents for r in roots), 'duplicate_or_nested_bundle_root'); roots.add(root)
        index, _ = read(target, c.checksum(row['sha256']))
        c.need(index.get('schema') == 'shard-delivery-v1' and index.get('scanner_sha256') == c.SCANNER_SHA, 'bundle_index_schema')
        shards = index['shards']
        c.need(type(shards) is list and 0 < len(shards) <= c.MAX_SHARDS, 'shard_count_limit')
        original_rows, copies = [], [(target, 'INDEX.json')]
        expected_tree = {'COMPLETE.json', 'payload/INDEX.json', 'payload/SOURCE_SCAN.json'}
        complete, _ = read(root / 'COMPLETE.json')
        c.need(index['source_scan']['path'] == 'SOURCE_SCAN.json', 'source_scan_name')
        _, scan_raw = read(target.parent / 'SOURCE_SCAN.json', c.checksum(index['source_scan']['sha256']))
        c.need(len(scan_raw) == index['source_scan']['bytes'], 'source_scan_size')
        for number, shard in enumerate(shards, 1):
            page_name, archive_name = 'indexes/part-%06d.json' % number, 'shards/part-%06d.tar.gz' % number
            c.need(shard['index'] == page_name and shard['archive'] == archive_name, 'noncanonical_shard_path')
            page, page_raw = read(target.parent / page_name, c.checksum(shard['index_sha256']))
            c.need(set(page) == {'schema', 'files'} and page['schema'] == 'shard-members-v1'
                   and len(page_raw) == shard['index_bytes'] and len(page['files']) == shard['file_count'], 'member_page_schema_or_count')
            c.validate_rows(page['files'])
            original_rows.extend(page['files']); copies.append((target.parent / page_name, page_name))
            expected_tree.update(('payload/' + page_name, 'payload/' + archive_name))
        original_rows.sort(key=lambda r: r['path'])
        paths = [r['path'] for r in original_rows]
        c.need(len(set(paths)) == len(paths) and not owners.intersection(paths), 'duplicate_global_original_path')
        owners.update(paths)
        count, size = len(paths), sum(r['bytes'] for r in original_rows)
        for obj in (index, row):
            c.number(obj['file_count'], c.MAX_SHARDS * c.MAX_FILES, 'file_count', 1)
            c.number(obj['original_bytes'], c.MAX_SHARDS * c.EXPANDED, 'original_bytes')
            c.need((obj['file_count'], obj['original_bytes']) == (count, size), 'bundle_totals_mismatch')
        c.need(complete.get('binding') == {'kind': 'bundle', 'index_sha256': row['sha256']}
               and complete.get('complete') is True, 'bundle_completion_binding')
        c.need(c.tree(root) == expected_tree, 'bundle_extra_or_missing_file')
        binding = {'kind': 'restored-originals', 'input_sha256': row['sha256'], 'single_archive': False}
        prepared.append(dict(row=row, path=target, expected=c.completion_record(original_rows, binding), copies=copies))
        total_files += count; total_bytes += size
    c.no_path_prefixes(owners)
    c.number(collection['file_count'], MAX_BUNDLES * c.MAX_SHARDS * c.MAX_FILES, 'collection_file_count', 1)
    c.number(collection['original_bytes'], MAX_BUNDLES * c.MAX_SHARDS * c.EXPANDED, 'collection_original_bytes')
    c.need((total_files, total_bytes) == (collection['file_count'], collection['original_bytes']), 'collection_totals_mismatch')
    return collection, raw, prepared, metadata


def restore_collection(index_path, expected_sha, output):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    c, original = frozen_tools()
    output = c.fresh(output)
    collection, raw, prepared, metadata = preflight(index_path, expected_sha, c)
    index_path = c.lexical(index_path)
    protected = [index_path.parent, c.lexical(TOOLS), *(v['path'].parent.parent for v in prepared)]
    c.need(all(output != p and p not in output.parents and output not in p.parents for p in protected), 'output_input_overlap')
    output.mkdir(mode=0o700)
    completed, navigation, expected_files, copied = [], [], {'COLLECTION_INDEX.json'}, []
    try:
        c.write_new(output / 'COLLECTION_INDEX.json', raw)
        for item in prepared:
            row, bid = item['row'], item['row']['bundle_id']
            result = original.restore(item['path'], row['sha256'], output / bid, secret_files=())
            actual, _ = c.load_json(output / bid / 'COMPLETE.json')
            c.need(result.get('passed') is True and actual == item['expected']
                   and result['file_count'] == row['file_count'] and result['original_bytes'] == row['original_bytes'], 'restored_bundle_mismatch')
            digest = c.verify_completion(output / bid, item['expected']['binding'])
            c.need(digest == result['completion_sha256'], 'restored_completion_digest')
            completed.append({'bundle_id': bid, 'completion_sha256': digest})
            expected_files.update(bid + '/' + name for name in c.tree(output / bid))
            for path, relative in item['copies']:
                entry = next(v for v in metadata if v[0] == path)
                _, page_raw = c.load_json(path, entry[1])
                destination = output / 'metadata' / bid / relative
                c.write_new(destination, page_raw)
                copied.append((destination, entry[1], entry[2]))
                expected_files.add(destination.relative_to(output).as_posix())
            navigation.append({**row, 'restored_payload': bid + '/payload',
                               'copied_member_index': 'metadata/' + bid + '/INDEX.json'})
        for path, digest, size in metadata + copied:
            c.need(c.stream_hash(path, c.INDEX_LIMIT) == (size, digest), 'metadata_changed_after_restore')
        c.need(c.stream_hash(output / 'COLLECTION_INDEX.json', c.INDEX_LIMIT) == (len(raw), expected_sha), 'copied_collection_changed')
        c.need(all(hashlib.sha256((TOOLS / name).read_bytes()).hexdigest() == digest for name, digest in PINS.items()), 'tool_changed_after_restore')
        for item, ref in zip(prepared, completed):
            c.need(c.verify_completion(output / ref['bundle_id'], item['expected']['binding']) == ref['completion_sha256'], 'final_bundle_changed')
        ownership = c.encoded({'schema': 'collection-path-ownership-v1', 'bundles': navigation,
                              'lookup': 'Read copied_member_index then its indexes/*.json; row.path belongs under restored_payload. Copied metadata is not a standalone archive bundle.'})
        c.need(len(ownership) <= c.INDEX_LIMIT, 'ownership_index_limit')
        c.scan(ownership, 'OWNERSHIP_INDEX.json', ())
        c.write_new(output / 'OWNERSHIP_INDEX.json', ownership)
        expected_files.add('OWNERSHIP_INDEX.json')
        c.need(c.tree(output) == expected_files and c.stream_hash(output / 'OWNERSHIP_INDEX.json', c.INDEX_LIMIT)
               == (len(ownership), c.sha(ownership)), 'collection_output_extra_missing_or_changed')
        receipt = dict(schema='whole-file-collection-complete-v1', complete=True, input_sha256=expected_sha,
                       bundle_count=len(completed), file_count=collection['file_count'], original_bytes=collection['original_bytes'],
                       bundles=completed, ownership_index_sha256=c.sha(ownership), known_secret_sources_checked=0,
                       modes_timestamps_ownership_preserved=False, publication_performed=False, remote_restore_performed=False)
        c.write_new(output / 'COLLECTION_COMPLETE.json', c.encoded(receipt))
        c.sync_directory(output); c.sync_directory(output.parent)
        return receipt
    except Exception:
        try:
            c.write_new(output / 'COLLECTION_INCOMPLETE.json', c.encoded({'complete': False, 'completed_bundles': completed, 'rule': 'collection_restore_failed_no_retry'}))
        except Exception:
            pass
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', required=True, type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = restore_collection(args.index, args.sha256, args.output_dir)
        print(json.dumps({k: result[k] for k in ('complete', 'bundle_count', 'file_count', 'original_bytes')}))
    except Exception:
        print(json.dumps({'complete': False, 'rule': 'collection_restore_failed_no_retry'}))
        raise SystemExit(1)
