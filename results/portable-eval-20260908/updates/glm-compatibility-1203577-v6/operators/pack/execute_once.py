#!/usr/bin/env python3
"""Exactly one approved frozen-pack CLI; no separate restore or upload."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
WORKSPACE = BASE.parent.parent
PREPARE_SHA = 'cf2a159b93b4b6da551c9d8f29c6b45c066d71f6f1d7dd41ce7765918393f003'
GO_SHA = '04bcc769c6c447800c8f36c37901449276a575392fb35da9dd9605133e7c2e87'
LOCK_SHA = '1b64e8f9cc2ca1ea30b47a7cec0b58cccc30e730494a70ca93bc73d623feec26'
SCOPE_SHA = 'ac5bb183bdf42d67fa26a84f21ce3d186f3d3dc412c9af31e0101e16285f2a4b'
DEADLINE = datetime(2026, 9, 8, 19, 25, tzinfo=timezone.utc)


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    if hashlib.sha256((BASE / 'prepare.py').read_bytes()).hexdigest() != PREPARE_SHA:
        raise RuntimeError('prepare_identity')
    spec = importlib.util.spec_from_file_location('glm_frozen_prepare', BASE / 'prepare.py')
    p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p)
    c = p.c
    c.write_new(HERE / 'once_entry.json', c.encoded({'created_utc': utc(), 'one_attempt_only': True,
                'authority_sha256': GO_SHA, 'publication_performed': False}))
    record = {'schema': 'glm-local-pack-operator-v1', 'started_utc': utc(), 'command_started': False,
              'authority_sha256': GO_SHA, 'source_manifest_sha256': LOCK_SHA,
              'separate_restore_performed': False, 'network_or_git_performed': False, 'publication_performed': False}
    try:
        p.verify_tools()
        go, _ = c.load_json(BASE / 'ROOT_LOCAL_PACK_GO.json', GO_SHA)
        scope, _ = c.load_json(BASE / 'checks/metadata_v1/SCOPE.json', SCOPE_SHA)
        lock_path = BASE / 'checks/seal_v1/lock.json'
        c.load_json(lock_path, LOCK_SHA)
        c.load_json(BASE / 'checks/seal_v1/manifest.json', go['accepted_source_scan']['manifest_sha256'])
        c.load_json(BASE / 'operator_seal_20260908T1906Z/RECEIPT.json', go['accepted_source_scan']['operator_receipt_sha256'])
        c.need(scope['files'] == p.metadata_rows(WORKSPACE, p.DIRECTORIES, p.fixed_files()), 'original_metadata_changed')
        key_path = c.lexical(WORKSPACE / p.KEY)
        c.need(stat.S_ISREG(key_path.lstat().st_mode), 'key_not_regular_file')
        record['key_ancestor_metadata'] = {'no_symlink': True, 'leaf_regular_file': True, 'contents_read_by_operator': False}
        destination = c.fresh(BASE / 'checks/pack_v1')
        pack_path = WORKSPACE / 'publication/shard_delivery_candidate_v2/pack.py'
        limits = {'compressed_bytes': c.COMPRESSED, 'expanded_bytes': c.EXPANDED, 'member_bytes': c.MEMBER,
                  'files_per_shard': c.MAX_FILES, 'index_bytes': c.INDEX_LIMIT}
        c.need(go['pack_authorized'] is True and go['publication_authorized'] is False
               and go['limits'] == limits and go['manifest'] == {'path': str(lock_path), 'sha256': LOCK_SHA}
               and go['pack_source'] == {'path': str(pack_path), 'sha256': p.TOOLS['publication/shard_delivery_candidate_v2/pack.py']}
               and go['workspace'] == str(WORKSPACE) and go['output_dir'] == str(destination)
               and go['secret_file'] == str(key_path), 'root_go_arguments_mismatch')
        command = [sys.executable, '-B', str(pack_path), '--manifest', str(lock_path), '--manifest-sha256', LOCK_SHA,
                   '--workspace', str(WORKSPACE), '--output-dir', str(destination), '--secret-file', str(key_path)]
        c.need(datetime.now(timezone.utc) < DEADLINE, 'root_start_deadline_expired')
        record.update({'argv': command, 'cwd': str(WORKSPACE), 'command_started_utc': utc(),
                       'command_started': True, 'limits': limits, 'frozen_tools': p.TOOLS})
        c.write_new(HERE / 'COMMAND.json', c.encoded(record))
        with (HERE / 'stdout.log').open('xb') as stdout, (HERE / 'stderr.log').open('xb') as stderr:
            child = subprocess.run(command, cwd=WORKSPACE, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, check=False)
        record.update({'exit_code': child.returncode, 'command_finished_utc': utc(), 'passed': child.returncode == 0})
        if child.returncode == 0:
            # Read only pack's own small metadata; no independent restore/verify.
            result = c.strict_json((HERE / 'stdout.log').read_bytes())
            c.need(result['passed'] is True and result['file_count'] == 1370 and result['original_bytes'] == 166769588,
                   'pack_return_scope_mismatch')
            for name, expected in [('COMPLETE.json', result['completion_sha256']), ('payload/INDEX.json', result['index_sha256'])]:
                data = c.scanner().stable_read(c.lexical(destination / name), limit=c.INDEX_LIMIT)
                c.need(c.sha(data) == expected, 'returned_output_metadata_sha_mismatch')
            record['pack_result'] = result
            record['complete_path'] = str(destination / 'COMPLETE.json')
            record['index_path'] = str(destination / 'payload/INDEX.json')
        record['scope_metadata_unchanged_after'] = scope['files'] == p.metadata_rows(WORKSPACE, p.DIRECTORIES, p.fixed_files())
        c.need(record['scope_metadata_unchanged_after'], 'original_metadata_changed_after')
    except Exception as exc:
        record.update({'passed': False, 'operator_rule': str(exc) if isinstance(exc, c.DeliveryError) else 'operator_check_failed'})
    record['finished_utc'] = utc()
    c.write_new(HERE / 'RECEIPT.json', c.encoded(record))
    print(json.dumps(record, indent=2))
    return 0 if record.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
