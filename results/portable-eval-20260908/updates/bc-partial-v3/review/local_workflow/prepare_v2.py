#!/usr/bin/env python3
"""ROOT-authorized exact control-original split; never edit original scanners."""
import json
from pathlib import Path
import prepare as p
import assemble as a
c = p.c

ROOT_TRANSPORT = 'portable_eval_20260908/validation/bc_partial_transport_root_20260908T1100Z'
ROOT_ACCEPT = 'portable_eval_20260908/validation/bc_partial_root_acceptance_20260908T1112Z.json'


def main():
    validator = c.scanner(); secrets = validator.load_secrets([p.KEY])
    a.verify_tools()
    pins = {**p.PINS, ROOT_TRANSPORT + '/receipt.json': '406c98a07a3ac8c397aa76f392070586c160688715a556471ee83a46450b7625',
            ROOT_ACCEPT: '83572c23398112b37593b496960723aad0f56fb2f2c3ff0a41fbfc3aaeafae56'}
    for source, expected in pins.items():
        raw = validator.stable_read(c.lexical(p.WORKSPACE / source)); c.scan(raw, source, secrets)
        c.need(c.sha(raw) == expected, 'external_anchor_changed')
    control = a.control_original(p.WORKSPACE / a.CONTROL_TARGET, secrets)
    run_names = validator.tree_files(p.WORKSPACE / p.RUN)
    c.need(len(run_names) == 2173 and a.CONTROL_NAME in run_names and 'execution.json' not in run_names,
           'original_run_scope_changed')
    dirs = list(p.DIRECTORIES[1:]) + [(ROOT_TRANSPORT, 'receipt.json')]
    # Three original subtrees remain complete sealed directories. All root
    # files except the exact manual control original are individual artifacts.
    roots = []
    for name in run_names:
        if '/' not in name and name != a.CONTROL_NAME:
            roots.append(p.RUN + '/' + name)
    c.need(len(roots) == 14, 'run_root_file_count')
    for name in ('dumps', 'results', 'logs'):
        names = validator.tree_files(p.WORKSPACE / p.RUN / name)
        c.need(names, 'empty_run_subtree')
        dirs.append((p.RUN + '/' + name, names[0]))
    artifacts = []
    for i, (source, anchor) in enumerate(dirs):
        digest = c.sha(validator.stable_read(c.lexical(p.WORKSPACE / source / anchor)))
        artifacts.append({'id': 'directory_%02d' % i, 'kind': 'sealed_directory', 'sealed': True,
                          'source': source, 'target': source, 'anchor': {'path': anchor, 'sha256': digest}})
    for i, source in enumerate(p.SUPPORT + roots + [ROOT_ACCEPT]):
        path = c.lexical(p.WORKSPACE / source); raw = validator.stable_read(path)
        artifacts.append({'id': 'file_%03d' % i, 'kind': 'sealed_file', 'sealed': True,
                          'source': source, 'target': source, 'anchor': {'path': path.name, 'sha256': c.sha(raw)}})
    spec = {'schema_version': 1, 'approved': True, 'require_secret_sources': True,
            'scope': 'Strict frozen-scanner subset of retained interrupted B/C v3. Exactly one fixed manual control original is separate, never silently dropped.',
            'artifacts': artifacts, 'required_stages': [x['id'] for x in artifacts] + ['formal_complete_matrix', 'whole_project_final_review'],
            'source_tree_sha256': 'd1606db7d6036c8975ce9d3e556daf7fa2ce4604879f2b3878435b0f96aebb78',
            'control_original_separate': {'source': a.CONTROL_TARGET, 'target': 'control_originals/' + a.CONTROL_NAME,
                                         'bytes': len(control), 'sha256': a.CONTROL_SHA, 'manual_prose_exception': True},
            'strict_scanner_all_originals_passed': False, 'initial_full_scan_failure_retained': True,
            'publication_performed': False}
    result, lock = validator.validate(spec, p.WORKSPACE, secrets, seal=True)
    c.need(result['safe_to_stage'] is True and result['findings'] == [], 'strict_subset_scan_failed')
    bindings = {}
    for source in (p.PARTIAL, p.TRANSPORT, ROOT_TRANSPORT):
        bindings.update(c.strict_json((p.WORKSPACE / source / 'receipt.json').read_bytes())['file_bindings'])
    for row in result['files']:
        raw = validator.stable_read(p.WORKSPACE / row['source']); c.scan(raw, row['target'], secrets)
        c.need((len(raw), c.sha(raw)) == (row['bytes'], row['sha256']), 'source_changed_after_scan')
        prior = bindings.get(str(p.WORKSPACE / row['source']))
        if prior:
            c.need((row['bytes'], row['sha256']) == (prior['bytes'], prior['sha256']), 'prior_receipt_binding_changed')
    full = result['files'] + [{'artifact_id': 'manual_fixed_control', 'source': a.CONTROL_TARGET,
                             'target': a.CONTROL_TARGET, 'path': a.CONTROL_NAME,
                             'bytes': a.CONTROL_BYTES, 'sha256': a.CONTROL_SHA}]
    full.sort(key=lambda row: row['target'])
    run_rows = [row for row in full if row['source'].startswith(p.RUN + '/')]
    c.need({row['source'][len(p.RUN)+1:] for row in run_rows} == set(run_names), 'whole_original_run_path_set')
    c.need(sum(row['bytes'] for row in run_rows) == 99498860, 'whole_original_run_bytes')
    stamps = p.snapshot(full)
    out = c.fresh(p.BASE / 'checks' / 'initial_v2'); out.mkdir(mode=0o700)
    summary = {'passed': True, 'strict_subset_files': len(result['files']), 'control_original_files': 1,
               'whole_original_files': len(full), 'whole_original_bytes': sum(row['bytes'] for row in full),
               'run_files': len(run_rows), 'run_bytes': sum(row['bytes'] for row in run_rows),
               'run_sharded_files': len(run_rows)-1, 'run_control_original_files': 1,
               'strict_scanner_all_originals_passed': False, 'manual_exact_prose_exception_count': 1,
               'known_secret_sources_checked': len(secrets), 'original_execution_json_absent': True,
               'ROOT_partial_transport_limited_acceptance_included': True, 'publication_performed': False}
    for name, value in [('spec.json', spec), ('lock.json', lock), ('manifest.json', result),
                        ('full_original_inventory.json', full), ('source_snapshot.json', stamps), ('SUMMARY.json', summary)]:
        raw = c.encoded(value); c.scan(raw, name, secrets); c.write_new(out / name, raw)
    print(json.dumps({**summary, 'lock_sha256': c.sha((out/'lock.json').read_bytes()), 'output': str(out)}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'passed': False, 'rule': str(exc) if isinstance(exc, c.DeliveryError) else 'prepare_v2_failed', 'publication_performed': False}))
        raise SystemExit(1)
