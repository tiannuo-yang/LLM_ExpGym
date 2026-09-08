#!/usr/bin/env python3
"""Seven bounded public-style restores, then opaque original-byte comparison."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
WORKSPACE = BASE.parent.parent
PREPARE_SHA = 'cf2a159b93b4b6da551c9d8f29c6b45c066d71f6f1d7dd41ce7765918393f003'
GO_SHA = '256d215f51692893ece124f7d7ba64da971cbf0b24b28bf0b3942ac8add45c22'
LOCK_SHA = '1b64e8f9cc2ca1ea30b47a7cec0b58cccc30e730494a70ca93bc73d623feec26'
SCOPE_SHA = 'ac5bb183bdf42d67fa26a84f21ce3d186f3d3dc412c9af31e0101e16285f2a4b'
INDEX_SHA = '0044ee0569058c371afe7fa6774f0a0313d1ef04b96186c520eb9b27c621bf18'
DEADLINE = datetime(2026, 9, 8, 19, 30, tzinfo=timezone.utc)


def utc():
    return datetime.now(timezone.utc).isoformat()


def opaque_compare(c, paths, expected):
    """Original/full/single bytes compared directly, never decoded or parsed."""
    paths = [c.lexical(path) for path in paths]
    stamps = [c.signature(path.lstat()) for path in paths]
    handles = []
    hashes = [hashlib.sha256() for _ in paths]
    total = 0
    try:
        for path, stamp in zip(paths, stamps):
            handle = os.fdopen(os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)), 'rb')
            handles.append(handle)
            c.need(c.signature(os.fstat(handle.fileno())) == stamp, 'byte_check_input_changed')
        while True:
            chunks = [handle.read(c.BLOCK) for handle in handles]
            c.need(chunks[0] == chunks[1] == chunks[2], 'restored_bytes_not_original')
            if not chunks[0]:
                break
            total += len(chunks[0])
            c.need(total <= expected['bytes'], 'restored_size_overrun')
            for digest, chunk in zip(hashes, chunks):
                digest.update(chunk)
        c.need(total == expected['bytes'] and all(d.hexdigest() == expected['sha256'] for d in hashes), 'byte_or_sha_mismatch')
        for handle, path, stamp in zip(handles, paths, stamps):
            c.need(c.signature(os.fstat(handle.fileno())) == stamp == c.signature(path.lstat()), 'byte_check_input_changed')
    finally:
        for handle in handles:
            handle.close()


def main():
    if hashlib.sha256((BASE / 'prepare.py').read_bytes()).hexdigest() != PREPARE_SHA:
        raise RuntimeError('prepare_identity')
    spec = importlib.util.spec_from_file_location('glm_frozen_prepare', BASE / 'prepare.py')
    p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p)
    c = p.c
    c.write_new(HERE / 'once_entry.json', c.encoded({'created_utc': utc(), 'one_batch_only': True,
                'authority_sha256': GO_SHA, 'maximum_restore_cli_calls': 7, 'credentials_read': False}))
    record = {'schema': 'glm-public-style-restore-operator-v1', 'started_utc': utc(), 'authority_sha256': GO_SHA,
              'calls': [], 'passed': False, 'credentials_read': False, 'network_or_git_performed': False,
              'publication_performed': False, 'model_scores_or_answers_interpreted': False}
    try:
        p.verify_tools()
        go, _ = c.load_json(BASE / 'ROOT_LOCAL_RESTORE_GO.json', GO_SHA)
        scope, _ = c.load_json(BASE / 'checks/metadata_v1/SCOPE.json', SCOPE_SHA)
        lock, _ = c.load_json(BASE / 'checks/seal_v1/lock.json', LOCK_SHA)
        bundle = BASE / 'checks/pack_v1'
        index_path = bundle / 'payload/INDEX.json'
        index, _ = c.load_json(index_path, INDEX_SHA)
        c.load_json(bundle / 'COMPLETE.json', go['complete_sha256'])
        c.load_json(BASE / 'operator_pack_20260908T1909Z/RECEIPT.json', go['pack_operator_receipt_sha256'])
        c.need(scope['files'] == p.metadata_rows(WORKSPACE, p.DIRECTORIES, p.fixed_files()), 'scope_metadata_changed')
        restore_path = WORKSPACE / 'publication/shard_delivery_candidate_v2/restore.py'
        full = BASE / 'checks/restore_v1'
        single_parent = BASE / 'checks/restore_single_v1'
        c.need(go['restore_authorized'] is True and go['publication_authorized'] is False
               and go['index'] == {'path': str(index_path), 'sha256': INDEX_SHA}
               and go['restore_source'] == {'path': str(restore_path), 'sha256': p.TOOLS['publication/shard_delivery_candidate_v2/restore.py']}
               and go['full_output_dir'] == str(full) and go['single_output_parent'] == str(single_parent), 'root_go_arguments_mismatch')
        c.fresh(full)
        c.fresh(single_parent).mkdir(mode=0o700)
        c.need(len(index['shards']) == 6, 'shard_count_changed')
        calls = [('full', '--index', index_path, INDEX_SHA, full)]
        single_sources = {}
        for number, shard in enumerate(index['shards'], 1):
            part = 'part-%06d' % number
            c.need(shard['archive'] == 'shards/' + part + '.tar.gz' and shard['index'] == 'indexes/' + part + '.json', 'shard_name_changed')
            page, _ = c.load_json(bundle / 'payload' / shard['index'], shard['index_sha256'])
            destination = c.fresh(single_parent / part)
            calls.append((part, '--archive', bundle / 'payload' / shard['archive'], shard['sha256'], destination))
            for row in page['files']:
                c.need(row['path'] not in single_sources, 'duplicate_original_across_shards')
                single_sources[row['path']] = (destination / 'payload' / c.relative(row['path']), row)
        for name, mode, source, digest, destination in calls:
            c.need(datetime.now(timezone.utc) < DEADLINE, 'root_start_deadline_expired')
            call_dir = c.fresh(HERE / name)
            call_dir.mkdir(mode=0o700)
            command = [sys.executable, '-B', str(restore_path), mode, str(source), '--sha256', digest, '--output-dir', str(destination)]
            entry = {'name': name, 'argv': command, 'cwd': str(WORKSPACE), 'started_utc': utc(),
                     'secret_file_argument_supplied': False, 'authority_sha256': GO_SHA}
            c.write_new(call_dir / 'ENTRY.json', c.encoded(entry))
            with (call_dir / 'stdout.log').open('xb') as stdout, (call_dir / 'stderr.log').open('xb') as stderr:
                result = subprocess.run(command, cwd=WORKSPACE, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, check=False)
            entry.update({'finished_utc': utc(), 'exit_code': result.returncode})
            c.write_new(call_dir / 'EXIT.json', c.encoded(entry))
            record['calls'].append(entry)
            c.need(result.returncode == 0, 'restore_cli_failed')
            status = c.strict_json((call_dir / 'stdout.log').read_bytes())
            c.need(status['passed'] is True and status['known_secret_sources_checked'] == 0, 'restore_status_or_credential_scope')
        expected = {}
        for artifact in lock['artifacts']:
            c.need(artifact['kind'] == 'sealed_file' and len(artifact['files']) == 1 and artifact['source'] == artifact['target'], 'unexpected_lock_mapping')
            row = artifact['files'][0]
            name = artifact['target']
            c.relative(name)
            c.need(name not in expected, 'duplicate_lock_path')
            expected[name] = {'path': name, 'bytes': row['bytes'], 'sha256': row['sha256'], 'source': artifact['source']}
        c.need(len(expected) == 1370 and sum(row['bytes'] for row in expected.values()) == 166769588, 'lock_total_changed')
        c.need(c.tree(full / 'payload') == set(expected) == set(single_sources), 'full_or_union_path_set')
        for name, mode, source, digest, destination in calls:
            wanted = set(expected) if name == 'full' else {r for r, (path, _row) in single_sources.items() if destination in path.parents}
            c.need(c.tree(destination / 'payload') == wanted, 'single_payload_path_set')
            c.need(c.tree(destination) == {'COMPLETE.json'} | {'payload/' + r for r in wanted}, 'restore_wrapper_extra_or_missing_file')
        verified = []
        for name, row in sorted(expected.items()):
            single_path, single_row = single_sources[name]
            c.need(single_row == {key: row[key] for key in ('path', 'bytes', 'sha256')}, 'single_index_differs_from_lock')
            opaque_compare(c, [WORKSPACE / row['source'], full / 'payload' / name, single_path], row)
            verified.append({key: row[key] for key in ('path', 'bytes', 'sha256')})
        c.need(scope['files'] == p.metadata_rows(WORKSPACE, p.DIRECTORIES, p.fixed_files()), 'scope_metadata_changed_after')
        c.write_new(HERE / 'VERIFIED_ORIGINALS.json', c.encoded(verified))
        record.update({'passed': True, 'restore_cli_calls': len(record['calls']), 'full_files': len(verified),
                       'single_shard_union_files': len(single_sources), 'disjoint_single_union': True,
                       'original_bytes': sum(r['bytes'] for r in verified), 'zero_byte_originals': sum(r['bytes'] == 0 for r in verified),
                       'full_and_single_union_direct_bytes_sha_paths_equal_originals_and_lock': True,
                       'scope_metadata_unchanged_after': True, 'verified_inventory_sha256': c.sha(c.encoded(verified)),
                       'index_sha256': INDEX_SHA, 'lock_sha256': LOCK_SHA})
    except Exception as exc:
        record['rule'] = str(exc) if isinstance(exc, c.DeliveryError) else 'restore_operator_failed'
    record['finished_utc'] = utc()
    c.write_new(HERE / 'RECEIPT.json', c.encoded(record))
    print(json.dumps(record, indent=2))
    return 0 if record['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
