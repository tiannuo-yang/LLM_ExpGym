#!/usr/bin/env python3
"""Bounded, read-only PP-local page-cache warming; no serving/model changes."""
import argparse
import json
import os
from pathlib import Path
import stat
import time
import urllib.request

ROOT = Path('/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Qwen3.8-2.4T-A95B-FP8')
SHARDS = [list(range(1, 54)) + [60], list(range(54, 106)),
          list(range(106, 157)) + [159], list(range(157, 185)) + list(range(187, 214))]
RESERVE = 384 * 1024**3


def memory_headroom():
    mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(mem['MemAvailable'].split()[0]) * 1024
    bounds = []
    for line in Path('/proc/self/cgroup').read_text().splitlines():
        hierarchy, controllers, location = line.split(':', 2)
        if hierarchy == '0' and controllers == '':
            cgroot = Path('/sys/fs/cgroup')
            current = cgroot / location.lstrip('/')
            while current == cgroot or cgroot in current.parents:
                cap = current / 'memory.max'
                used = current / 'memory.current'
                if cap.exists() and used.exists():
                    limit = cap.read_text().strip()
                    if limit != 'max':
                        bounds.append(int(limit) - int(used.read_text().strip()))
                if current == cgroot:
                    break
                current = current.parent
            return min([available] + bounds)
    raise RuntimeError('Expected unified cgroup; refuse unchecked memory limits')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=900)
    args = parser.parse_args()
    rank = int(os.environ['SLURM_PROCID'])
    expected = 'azure-uk-hpc-H200-instance-' + str(446 + rank)
    if rank not in range(4) or os.uname().nodename.split('.')[0] != expected:
        raise RuntimeError('Unexpected PP rank/node mapping')
    paths = [ROOT / ('model-%05d-of-00213.safetensors' % n) for n in reversed(SHARDS[rank])]
    expected_bytes = sum(path.stat().st_size for path in paths)
    if expected_bytes > 800 * 1000**3 or memory_headroom() < expected_bytes + RESERVE:
        raise RuntimeError('Insufficient initial memory headroom')
    start = time.monotonic()
    read_bytes = 0
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    health_url = 'http://azure-uk-hpc-H200-instance-446:31240/health'
    next_mem = next_health = 0
    reason = 'completed'

    def emit(event, **fields):
        print(json.dumps(dict(event=event, rank=rank, node=expected,
                              elapsed_seconds=round(time.monotonic()-start, 3),
                              bytes_read=read_bytes, **fields)), flush=True)

    emit('start', expected_bytes=expected_bytes, files=len(paths), reserve_bytes=RESERVE)
    try:
        for path in paths:
            before = path.stat()
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb', buffering=0) as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise RuntimeError('Non-regular checkpoint shard')
                os.posix_fadvise(stream.fileno(), 0, 0, os.POSIX_FADV_SEQUENTIAL)
                while True:
                    now = time.monotonic()
                    if now - start > args.seconds:
                        reason = 'time_limit'
                        return
                    if now >= next_mem:
                        if memory_headroom() < RESERVE:
                            reason = 'memory_reserve'
                            return
                        next_mem = now + 1
                    if now >= next_health:
                        try:
                            with opener.open(health_url, timeout=0.3) as response:
                                if response.status == 200:
                                    reason = 'server_healthy'
                                    return
                        except (OSError, urllib.error.URLError):
                            pass
                        next_health = now + 5
                    block = stream.read(16 * 1024**2)
                    if not block:
                        break
                    read_bytes += len(block)
            after = path.stat()
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise RuntimeError('Checkpoint shard changed during read')
            emit('shard_complete', shard=path.name)
    except BaseException:
        reason = 'exception'
        raise
    finally:
        emit('stop', reason=reason)


if __name__ == '__main__':
    main()
