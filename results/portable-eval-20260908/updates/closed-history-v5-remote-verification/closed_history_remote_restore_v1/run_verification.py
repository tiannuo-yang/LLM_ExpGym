#!/usr/bin/env python3
"""Capture one post-restore verifier process without retry or restored writes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

HERE = Path(__file__).resolve().parent
VERIFIER = HERE / 'verify_restored_files.py'
EXPECTED = '512a4c1199a7e919f199236b6c4b4f506f8d3373c7754e2cd30d513963b61017'
ARGV = ['/usr/bin/python3', '-B', str(VERIFIER)]


def write(name, obj):
    with (HERE / name).open('x') as handle:
        json.dump(obj, handle, sort_keys=True, separators=(',', ':'))
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
assert hashlib.sha256(VERIFIER.read_bytes()).hexdigest() == EXPECTED
assert json.loads((HERE / 'CLI_EXIT.json').read_bytes())['actual_exit_code'] == 0
with (HERE / 'verification.stdout.log').open('xb') as stdout, (HERE / 'verification.stderr.log').open('xb') as stderr:
    child = subprocess.Popen(ARGV, stdout=stdout, stderr=stderr)
    write('VERIFICATION_STARTED.json', dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), pid=child.pid, argv=ARGV, verifier_sha256=EXPECTED))
    code = child.wait()
write('VERIFICATION_EXIT.json', dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), actual_exit_code=code, pid=child.pid, argv=ARGV, verifier_sha256=EXPECTED))
print(json.dumps(dict(actual_verifier_exit_code=code)), flush=True)
sys.exit(code)
