#!/usr/bin/env python3
"""One approved public CLI, with real child exit/logs; no retry or payload reads."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PUB = HERE.parent
RELEASE = PUB / 'closed_history_remote.vpLmvNvV/repo/results/portable-eval-20260908/closed_history_v5_20260909'
PROOF = PUB / 'closed_history_publication_stage_v1/ROOT_REMOTE_VERIFICATION.json'
PROOF_SHA = '4428b85cc8126703bc9c687d226c36ce1157a780dc66187f2292ef4dc36a87d5'
COMMIT = 'c4aca97c2ef7ce6826b58de10755a9a8c4a237f6'
INDEX = RELEASE / 'payload/collection/INDEX.json'
INDEX_SHA = 'ee080ed22ea8ccd2bf03bbb011369cc8329009c981f95c00f8d66aa4aa47d078'
TOOLS = RELEASE / 'payload/tools/publication'
WRAPPER = TOOLS / 'collection_restore_candidate_v2/restore_collection.py'
PINS = {
    WRAPPER: '24a2ff6da7521c7920ce50ea7491aa682310e78874ba2d552649e9d2d88bb6b2',
    TOOLS / 'shard_delivery_candidate_v2/common.py': '7147524d5799dc1264f088518db19251c5f906bc2da501854ce279f56d73263e',
    TOOLS / 'shard_delivery_candidate_v2/restore.py': 'ec20a0e22c8f810b09e894e0ddc6cc8dec114a66be4fe23cab8a55f3b62ac710',
    TOOLS / 'validate_bundle_v2.py': 'aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116',
    INDEX: INDEX_SHA, PROOF: PROOF_SHA,
}
OUTPUT = HERE / 'restored'
ARGV = ['/usr/bin/python3', '-B', str(WRAPPER), '--index', str(INDEX),
        '--sha256', INDEX_SHA, '--output-dir', str(OUTPUT)]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8') as handle:
        json.dump(obj, handle, sort_keys=True, separators=(',', ':'))
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if OUTPUT.exists() or OUTPUT.is_symlink():
        raise RuntimeError('output_not_fresh')
    for path, expected in PINS.items():
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('input_pin_mismatch')
    proof = json.loads(PROOF.read_bytes())
    if not (proof['passed'] is True and proof['clean'] is True
            and proof['complete_paths_working_bytes_sha_git_blob_sha_mode_verified'] is True
            and proof['commit'] == COMMIT
            and proof['tree'] == '856326c1bacb5bf8fc58239e3f0d918672050602'
            and proof['parent'] == 'f8c7f153493493e5ec4946e1996d67e4703e6f68'
            and Path(proof['repository']) / proof['prefix'] == RELEASE):
        raise RuntimeError('remote_proof_binding')
    collection = json.loads(INDEX.read_bytes())
    if (collection['bundle_count'], collection['file_count'], collection['original_bytes']) != (32, 47529, 1055374017):
        raise RuntimeError('expected_collection_totals')
    write('STARTED.json', dict(schema='public-collection-cli-start-v1', utc=now(), operator_pid=os.getpid(),
          argv=ARGV, input_refs=[dict(path=str(p), sha256=s) for p, s in PINS.items()],
          remote_commit=COMMIT, root_push_session=83472, root_push_exit_code=0,
          root_freshclone_session=29781, root_freshclone_exit_code=0,
          root_remote_verification_session=33918, root_remote_verification_exit_code=0,
          private_keys_read=False, retry=False, caps_changed=False, core_limit=[0, 0]))
    with (HERE / 'restore.stdout.log').open('xb') as stdout, (HERE / 'restore.stderr.log').open('xb') as stderr:
        child = subprocess.Popen(ARGV, stdout=stdout, stderr=stderr)
        write('CHILD_STARTED.json', dict(pid=child.pid, utc=now(), argv=ARGV))
        code = child.wait()
    write('CLI_EXIT.json', dict(schema='public-collection-cli-exit-v1', utc=now(), actual_exit_code=code,
          pid=child.pid, argv=ARGV, remote_commit=COMMIT, collection_index_sha256=INDEX_SHA))
    print(json.dumps(dict(actual_cli_exit_code=code, output=str(OUTPUT), verification_not_yet_run=True)), flush=True)
    return code


if __name__ == '__main__':
    sys.exit(main())
