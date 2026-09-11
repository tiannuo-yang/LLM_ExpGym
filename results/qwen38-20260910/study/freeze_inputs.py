#!/usr/bin/env python3
"""One explicit pre-execution provenance record; never hashes TB weight payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def file_record(path):
    before = path.stat()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError('Input changed during freeze: ' + str(path))
    return {'path': str(path.absolute()), 'bytes': before.st_size, 'sha256': digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-root', type=Path, required=True)
    parser.add_argument('--source-repo', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--matrix-dir', type=Path, required=True)
    parser.add_argument('--launch-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, repo = args.study_root.absolute(), args.source_repo.absolute()
    plan = json.loads(args.plan.read_text())
    if plan['schema'] != 'expgym.study-queue-plan.v1' or len(plan['jobs']) != 783:
        raise ValueError('Expected complete formal queue plan, not smoke')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True).strip():
        raise ValueError('Execution source worktree must be clean')
    sys.path.insert(0, str(repo))
    from expgym.trace_v2 import source_tree_sha256
    if source_tree_sha256(repo) != plan['source_tree_sha256']:
        raise ValueError('Execution source changed since queue freeze')
    launch = args.launch_dir.absolute()
    server = json.loads((launch / 'plan.json').read_text())
    deployment = json.loads((launch / 'deployment.json').read_text())
    if any(job['endpoints'] != deployment['endpoints'] for job in plan['jobs']):
        raise ValueError('Queue endpoint differs from recorded allocation')
    checkpoint = Path(server['checkpoint'])
    weight_index = json.loads((checkpoint / 'model.safetensors.index.json').read_text())
    shards = []
    for name in sorted(set(weight_index['weight_map'].values())):
        if Path(name).name != name:
            raise ValueError('Unexpected weight shard path')
        path = checkpoint / name
        if not path.is_file():
            raise ValueError('Missing weight shard')
        value = path.stat()
        shards.append({'name': name, 'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns})
    names = ['config.json', 'generation_config.json', 'tokenizer_config.json',
             'tokenizer.json', 'chat_template.jinja', 'model.safetensors.index.json']
    inputs = [args.plan, args.matrix_dir / 'matrix.json', args.matrix_dir / 'coverage.json',
              args.matrix_dir / 'runtime_environment.json', root / 'study/data_inventory.json',
              root / 'runtime/pyproject.toml', root / 'runtime/uv.lock', root / 'runtime/runtime-env.sh',
              root / 'runtime/versions.json', launch / 'plan.json', launch / 'deployment.json',
              root / 'study/python_main', root / 'study/python_hpo', root / 'study/cpu_runtime.py',
              root / 'study/build_matrix.py', repo / 'configs/audit_hypothesis_orders.json',
              repo / 'configs/hpobench_tasks.yaml', repo / 'data/hpo_tuning/oracle3.json']
    result = {'schema': 'qwen38.run-inputs.v1',
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
              'source_tree_sha256': plan['source_tree_sha256'], 'study_id': plan['study_id'],
              'queue_jobs': len(plan['jobs']), 'gpu_job_id': deployment['job_id'],
              'inputs': [file_record(p) for p in inputs],
              'checkpoint_metadata': [file_record(checkpoint / name) for name in names],
              'weight_shards': shards,
              'weight_index_declared_tensor_bytes': weight_index['metadata']['total_size'],
              'weight_shard_bytes': sum(s['bytes'] for s in shards),
              'weight_payload_hashes_verified': False,
              'data_payload_verification': 'Inherited completed copy+SHA validation from study/data_inventory.json; not repeated here',
              'scope': 'Identity record only; not inference readiness, scientific completion, or publication safety validation'}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'output': str(args.output), 'queue_jobs': len(plan['jobs']),
                      'weight_shards': len(shards), 'weight_payloads_hashed': False}))


if __name__ == '__main__':
    main()
