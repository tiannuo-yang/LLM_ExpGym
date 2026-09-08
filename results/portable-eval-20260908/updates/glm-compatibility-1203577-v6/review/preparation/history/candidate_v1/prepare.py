#!/usr/bin/env python3
"""GLM-only metadata snapshot; sealing requires a separately pinned ROOT GO.

No Git, network, model, Slurm, archive creation or score interpretation here.
The original validator and accepted shard reader/writer are reused unchanged.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import stat

BASE = Path(__file__).resolve().parent
WORKSPACE = BASE.parent.parent
OLD = 'portable_eval_20260908'
NEW = OLD + '/source_cohorts/v4/portable_eval_20260908'
OP = NEW + '/operations/development_runs/glm_compatibility_1203577_v6'
V5 = OLD + '/review/development_protocol_v5'
PHASE = OLD + '/serving/phase_candidates/gumbel_midpoint_v3'
RUN = PHASE + '/runs/1203577'
SERVING = RUN + '/glm_compatibility'
STOP = RUN + '/operator_stop_glm_v1'
KEY = SERVING + '/private/router_api_key'  # Path only; snapshot never opens it.
PREFIX = 'results/portable-eval-20260908/updates/glm-compatibility-1203577-v6'
PARENT = '0220353cd0330c55494057a1f9d9782c229890f4'
TOOLS = {
    'publication/validate_bundle_v2.py': 'aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116',
    'publication/shard_delivery_candidate_v2/common.py': '7147524d5799dc1264f088518db19251c5f906bc2da501854ce279f56d73263e',
    'publication/shard_delivery_candidate_v2/pack.py': '07eb7a20e838ca53bfda6144887283e597914e95fb11c5e16ff43f95f09f5f10',
    'publication/shard_delivery_candidate_v2/restore.py': 'ec20a0e22c8f810b09e894e0ddc6cc8dec114a66be4fe23cab8a55f3b62ac710',
}
spec = importlib.util.spec_from_file_location('glm_delivery_common', WORKSPACE / 'publication/shard_delivery_candidate_v2/common.py')
c = importlib.util.module_from_spec(spec)
# Check the helper before executing it; no credential source is accessed.
import hashlib
if hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest() != TOOLS['publication/shard_delivery_candidate_v2/common.py']:
    raise RuntimeError('frozen_helper_identity')
spec.loader.exec_module(c)

DIAGNOSTICS = (
    'metadata_v1', 'metadata_post_development_v1', 'operator_metadata_v1',
    'operator_metadata_post_development_v1', 'memory_io_snapshot_v1',
    'nonblocking_stack_snapshot_v1', 'progress_delta_snapshot_v1',
    'readonly_prefetch_trial_v1', 'readonly_state_snapshot_v1',
    'readonly_state_snapshot_v2', 'readonly_state_snapshot_v3',
)
DIRECTORIES = [OP, V5, OLD + '/review/development_protocol_v5_peer',
               OLD + '/review/development_protocol_v4_preflight_failure_20260908', STOP]
DIRECTORIES += [SERVING + '/' + name for name in DIAGNOSTICS]
PHASE_SOURCES = ('checkpoint_preflight.py', 'gpu_import_validation.py', 'hardware_preflight.py',
                 'model_profiles.json', 'phase_8nodes.sbatch', 'phase_common.py',
                 'phase_controller.py', 'profile_contract.py', 'queue_control.py',
                 'router.py', 'runtime.sh', 'serve_node.py')
ROOT_PINS = {
    OP + '/ROOT_ACTUAL_PROTOCOL_ACCEPTANCE.json': '30203f810a82163f779d38169478e578971665143526a6a2b2ef131e6715fa9f',
    OP + '/fresh_roles_v1/manifest.json': 'e367e182555d53b43773edb0c587c00ed1c1ef1c9cf3ef280bae76be826c4b7f',
    STOP + '/receipt.json': 'f257e6af16b1771a73ac63b4912f4e4c86696f7f2c96901e14c5ecac2e83431c',
    STOP + '/closed_originals.json': '8f4716fcac63f3f052f90703422e749d1dd41f77bd88e4d22832d3e2962f6635',
    STOP + '/controller_events_through_stop.jsonl': 'c33c18f07f2e10fa5d9bd37d018c7c113692d12e05d4c960e0f043ea9da96357',
    NEW + '/validation/development_independent_auditor_root_acceptance_v5.json': '4c8f034a9c820630877c722fdfd1db4b9d319d62d43738f7240b36b158e66cf4',
    V5 + '/FREEZE_RECEIPT.json': 'dec52c52e2067da8e5f91fe342ffd650278914f02a12ad8d62348a57b207b750',
    OLD + '/review/development_protocol_v4_preflight_failure_20260908/receipt.json': '111cefeb483b35720367b941913d083df7614aae2b4ae0213de98380bbe4f196',
    OLD + '/serving/runtime_candidates/gumbel_midpoint_v1/manifests/validation_v6.json': '6ae2baf43591acaad1be8b4f0dfe7fc705996313d1f588ce7cb63990cb892111',
}


def fixed_files():
    names = ['ROOT_LOADING_DIAGNOSIS.zh.md', 'checkpoint_structural.json', 'deployment.json', 'inventory.json']
    names += ['node%d-inventory.%s' % (i, suffix) for i in range(8) for suffix in ('command.json', 'exit.json', 'stderr', 'stdout')]
    for replica in range(4):
        for rank in range(2):
            stem = 'replica%d-rank%d' % (replica, rank)
            names += [stem + suffix for suffix in ('-hardware.json', '-launch.json', '.command.json', '.exit.json', '.log')]
    names += ['router.command.json', 'router.exit.json', 'router.log', 'router_requests.jsonl']
    return ([SERVING + '/' + name for name in names] + [PHASE + '/' + name for name in PHASE_SOURCES]
            + [RUN + '/commands/0002.json', RUN + '/commands/0002.ready',
               NEW + '/validation/development_independent_auditor_root_acceptance_v5.json',
               OLD + '/serving/runtime_candidates/gumbel_midpoint_v1/manifests/validation_v6.json'])


def verify_tools():
    for digest in ROOT_PINS.values():
        c.checksum(digest)
    for path, digest in TOOLS.items():
        c.need(c.stream_hash(WORKSPACE / path)[1] == digest, 'frozen_tool_changed')


def metadata_rows(workspace, directories, files):
    """No payload read/hash: full paths plus stat identity, including empty files."""
    names = list(files)
    for root in directories:
        c.relative(root)
        path = c.lexical(workspace / root)
        c.need(path.is_dir(), 'scope_directory_missing')
        names += [root + '/' + name for name in sorted(c.tree(path))]
    c.need(len(names) == len(set(names)), 'duplicate_scope_path')
    c.no_path_prefixes(names)
    rows = []
    for name in sorted(names):
        c.relative(name)
        path = c.lexical(workspace / name)
        info = path.lstat()
        c.need(stat.S_ISREG(info.st_mode) and info.st_size <= c.MEMBER, 'scope_type_or_member_size')
        rows.append({'path': name, 'bytes': info.st_size, 'stamp': list(c.signature(info))})
    return rows


def closed_bindings():
    # Only this ROOT-pinned control JSON is read during metadata preparation.
    raw = c.scanner().stable_read(c.lexical(WORKSPACE / STOP / 'closed_originals.json'))
    c.need(c.sha(raw) == ROOT_PINS[STOP + '/closed_originals.json'], 'stop_control_identity')
    obj = c.strict_json(raw)
    expected = {SERVING + '/replica%d-rank%d.%s' % (i, j, suffix)
                for i in range(4) for j in range(2) for suffix in ('log', 'exit.json', 'command.json')}
    expected |= {SERVING + '/' + name for name in ('router.log', 'router.exit.json', 'router.command.json', 'router_requests.jsonl', 'deployment.json')}
    expected |= {RUN + '/commands/0002.json', RUN + '/commands/0002.ready'}
    rows = obj['files'] + list(obj['sources'].values())
    bound = {}
    for row in rows:
        path = Path(row['path']).relative_to(WORKSPACE).as_posix()
        c.relative(path)
        c.need(path not in bound, 'duplicate_stop_binding')
        bound[path] = {'bytes': row['bytes'], 'sha256': c.checksum(row['sha256'])}
    c.need(set(bound) == expected | {PHASE + '/' + name for name in PHASE_SOURCES}, 'stop_binding_scope')
    # controller_prefix_after is deliberately NOT followed: RUN/events is live.
    return bound


def fresh_output(path):
    path = c.lexical(path)
    path.relative_to(BASE / 'checks')
    path.parent.mkdir(parents=True, exist_ok=True)
    c.fresh(path).mkdir(mode=0o700)
    return path


def snapshot(output):
    verify_tools()
    bindings = closed_bindings()
    rows = metadata_rows(WORKSPACE, DIRECTORIES, fixed_files())
    c.need(rows == metadata_rows(WORKSPACE, DIRECTORIES, fixed_files()), 'scope_changed_during_snapshot')
    by_name = {row['path']: row for row in rows}
    c.need(set(ROOT_PINS) <= set(by_name) and set(bindings) <= set(by_name), 'missing_control_or_bound_source')
    c.need(all(by_name[p]['bytes'] == row['bytes'] for p, row in bindings.items()), 'stop_bound_size_changed')
    record = {'schema': 'glm-delivery-metadata-snapshot-v1', 'approved': False, 'publication_authorized': False,
              'workspace': str(WORKSPACE), 'directories': DIRECTORIES, 'single_files': fixed_files(),
              'files': rows, 'file_count': len(rows), 'total_bytes': sum(r['bytes'] for r in rows),
              'external_root_pins': ROOT_PINS, 'closed_original_bindings': bindings, 'tools': TOOLS,
              'raw_content_read': False, 'raw_content_hash_inventory_created': False, 'known_key_read': False,
              'security_scan_performed': False, 'pack_performed': False, 'publication_performed': False,
              'proposed_prefix': PREFIX, 'expected_remote_parent': PARENT,
              'limits': {'compressed_bytes': c.COMPRESSED, 'expanded_bytes': c.EXPANDED, 'member_bytes': c.MEMBER, 'index_bytes': c.INDEX_LIMIT}}
    out = fresh_output(output)
    encoded = c.encoded(record)
    c.write_new(out / 'SCOPE.json', encoded)
    template = {'schema': 'glm-local-scan-go-v1', 'local_scan_authorized': False, 'publication_authorized': False,
                'scope_sha256': c.sha(encoded), 'prepare_sha256': c.stream_hash(Path(__file__))[1],
                'workspace': str(WORKSPACE), 'secret_source_path': str(WORKSPACE / KEY)}
    c.write_new(out / 'ROOT_SCAN_GO.template.json', c.encoded(template))
    return {key: record[key] for key in ('file_count', 'total_bytes', 'security_scan_performed', 'pack_performed', 'publication_performed')} | {'scope_sha256': c.sha(encoded)}


def seal(scope_path, scope_sha, go_path, go_sha, output):
    """Not run in the initial prepare turn; no prose/credential exceptions."""
    verify_tools()
    scope, _ = c.load_json(scope_path, scope_sha)
    go, _ = c.load_json(go_path, go_sha)
    c.need(go == {'schema': 'glm-local-scan-go-v1', 'local_scan_authorized': True, 'publication_authorized': False,
                  'scope_sha256': scope_sha, 'prepare_sha256': c.stream_hash(Path(__file__))[1],
                  'workspace': str(WORKSPACE), 'secret_source_path': str(WORKSPACE / KEY)}, 'root_scan_go_mismatch')
    c.need(scope['directories'] == DIRECTORIES and scope['single_files'] == fixed_files()
           and scope['external_root_pins'] == ROOT_PINS and scope['tools'] == TOOLS, 'fixed_scope_changed')
    c.need(scope['files'] == metadata_rows(WORKSPACE, DIRECTORIES, fixed_files()), 'snapshot_changed_before_scan')
    validator = c.scanner()
    secrets = validator.load_secrets([WORKSPACE / KEY])  # Only reached after exact new GO.
    # Names/control metadata must pass known-secret checks before an error report
    # can serialize any selected path. The initial snapshot was not public-safe.
    c.scan(c.encoded(scope), 'SCOPE.json', secrets)
    c.scan(c.encoded(go), 'ROOT_SCAN_GO.json', secrets)
    out = fresh_output(output)
    artifacts = []
    pins = {path: row['sha256'] for path, row in scope['closed_original_bindings'].items()} | ROOT_PINS
    for i, row in enumerate(scope['files']):
        name = row['path']
        raw = validator.stable_read(c.lexical(WORKSPACE / name))
        try:
            c.scan(raw, name, secrets)
        except c.DeliveryError as exc:
            c.write_new(out / 'INITIAL_SCAN_FAIL.json', c.encoded({'passed': False, 'path': name, 'rule': str(exc),
                        'input_rewritten': False, 'exception_allowed': False, 'publication_performed': False}))
            raise
        digest = c.sha(raw)
        c.need(name not in pins or digest == pins[name], 'root_or_stop_sha_changed')
        artifacts.append({'id': 'file_%05d' % i, 'kind': 'sealed_file', 'sealed': True, 'source': name, 'target': name,
                          'anchor': {'path': Path(name).name, 'sha256': digest}})
    spec = {'schema_version': 1, 'approved': True, 'require_secret_sources': True,
            'scope': 'Closed GLM compatibility development checkpoint only; not formal results or publication GO.',
            'artifacts': artifacts, 'required_stages': ['formal_matrix', 'final_project_acceptance'],
            'metadata_scope_sha256': scope_sha, 'root_local_scan_go_sha256': go_sha, 'publication_performed': False}
    result, lock = validator.validate(spec, WORKSPACE, secrets, seal=True)
    c.write_new(out / 'manifest.json', c.encoded(result))
    c.need(result['safe_to_stage'] is True and not result['findings'], 'original_full_scanner_failed')
    c.need(scope['files'] == metadata_rows(WORKSPACE, DIRECTORIES, fixed_files()), 'snapshot_changed_after_scan')
    for filename, obj in [('spec.json', spec), ('lock.json', lock)]:
        raw = c.encoded(obj)
        c.need(len(raw) <= c.INDEX_LIMIT, 'index_limit')
        c.scan(raw, filename, secrets)
        c.write_new(out / filename, raw)
    return {'passed': True, 'files': len(result['files']), 'bytes': result['total_bytes'],
            'lock_sha256': c.stream_hash(out / 'lock.json')[1], 'publication_performed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('snapshot', 'verify', 'seal'))
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--scope', type=Path)
    parser.add_argument('--scope-sha256')
    parser.add_argument('--root-scan-go', type=Path)
    parser.add_argument('--root-scan-go-sha256')
    args = parser.parse_args()
    if args.mode == 'snapshot':
        c.need(args.output_dir is not None, 'missing_output')
        result = snapshot(args.output_dir)
    elif args.mode == 'verify':
        c.need(args.scope is not None and args.scope_sha256 is not None, 'missing_scope_binding')
        verify_tools()
        obj, _ = c.load_json(args.scope, args.scope_sha256)
        c.need(obj['files'] == metadata_rows(WORKSPACE, DIRECTORIES, fixed_files()), 'scope_metadata_changed')
        result = {'metadata_unchanged': True, 'security_scan_performed': False, 'publication_performed': False}
    else:
        c.need(all((args.output_dir, args.scope, args.scope_sha256, args.root_scan_go, args.root_scan_go_sha256)), 'missing_seal_argument')
        result = seal(args.scope, args.scope_sha256, args.root_scan_go, args.root_scan_go_sha256, args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'passed': False, 'rule': str(exc) if isinstance(exc, c.DeliveryError) else 'prepare_failed', 'publication_performed': False}))
        raise SystemExit(1)
