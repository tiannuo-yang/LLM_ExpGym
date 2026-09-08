#!/usr/bin/env python3
"""One ROOT-authorized local seal; record failures without retries or data edits."""
from datetime import datetime, timezone
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
GO_SHA = '26f1894ca57ebf3eb4cba77435615b3071a785ec4bf317123c103914b0ded635'
SCOPE_SHA = 'ac5bb183bdf42d67fa26a84f21ce3d186f3d3dc412c9af31e0101e16285f2a4b'
ACCEPT_SHA = '58e5b820fea6519d70f8aa841e1c7dd6bf8f3939d8724a26333cc30bb156325e'
DEADLINE = datetime(2026, 9, 8, 19, 20, tzinfo=timezone.utc)


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    import hashlib
    if hashlib.sha256((BASE / 'prepare.py').read_bytes()).hexdigest() != PREPARE_SHA:
        raise RuntimeError('prepare_identity')
    spec = importlib.util.spec_from_file_location('glm_frozen_prepare', BASE / 'prepare.py')
    p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p)
    c = p.c
    c.write_new(HERE / 'once_entry.json', c.encoded({'created_utc': utc(), 'one_attempt_only': True,
                'authority_sha256': GO_SHA, 'publication_performed': False}))
    record = {'schema': 'glm-local-seal-operator-v1', 'started_utc': utc(), 'command_started': False,
              'authority_sha256': GO_SHA, 'prepare_sha256': PREPARE_SHA, 'scope_sha256': SCOPE_SHA,
              'root_prepare_acceptance_sha256': ACCEPT_SHA, 'pack_performed': False,
              'restore_performed': False, 'network_or_git_performed': False, 'publication_performed': False}
    try:
        p.verify_tools()
        scope_path = BASE / 'checks/metadata_v1/SCOPE.json'
        go_path = BASE / 'ROOT_LOCAL_SCAN_GO.json'
        scope, _ = c.load_json(scope_path, SCOPE_SHA)
        c.load_json(go_path, GO_SHA)
        c.load_json(BASE / 'ROOT_PREPARE_ACCEPTANCE.json', ACCEPT_SHA)
        c.need(scope['files'] == p.metadata_rows(WORKSPACE, p.DIRECTORIES, p.fixed_files()), 'original_metadata_changed')
        # Metadata only: neither this operator nor its record reads/hashes key.
        key_path = c.lexical(WORKSPACE / p.KEY)
        c.need(stat.S_ISREG(key_path.lstat().st_mode), 'key_not_regular_file')
        record['key_ancestor_metadata'] = {'no_symlink': True, 'leaf_regular_file': True, 'contents_read_by_operator': False}
        destination = c.fresh(BASE / 'checks/seal_v1')
        command = [sys.executable, '-B', str(BASE / 'prepare.py'), 'seal', '--scope', str(scope_path),
                   '--scope-sha256', SCOPE_SHA, '--root-scan-go', str(go_path), '--root-scan-go-sha256', GO_SHA,
                   '--output-dir', str(destination)]
        c.need(datetime.now(timezone.utc) < DEADLINE, 'root_start_deadline_expired')
        record.update({'argv': command, 'cwd': str(WORKSPACE), 'command_started_utc': utc(), 'command_started': True})
        c.write_new(HERE / 'COMMAND.json', c.encoded(record))
        with (HERE / 'stdout.log').open('xb') as stdout, (HERE / 'stderr.log').open('xb') as stderr:
            child = subprocess.run(command, cwd=WORKSPACE, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, check=False)
        record.update({'exit_code': child.returncode, 'command_finished_utc': utc(), 'passed': child.returncode == 0})
        # Only the new local scanner status JSON is read, never result payloads.
        failure = destination / 'INITIAL_SCAN_FAIL.json'
        if failure.exists():
            status = c.strict_json(failure.read_bytes())
            record['failure'] = {'path': status['path'], 'rule': status['rule']}
        if child.returncode == 0:
            record['lock_sha256'] = c.stream_hash(destination / 'lock.json')[1]
        record['scope_metadata_unchanged_after'] = scope['files'] == p.metadata_rows(WORKSPACE, p.DIRECTORIES, p.fixed_files())
    except Exception as exc:
        record.update({'passed': False, 'operator_rule': str(exc) if isinstance(exc, c.DeliveryError) else 'operator_check_failed'})
    record['finished_utc'] = utc()
    c.write_new(HERE / 'RECEIPT.json', c.encoded(record))
    print(json.dumps(record, indent=2))
    return 0 if record.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
