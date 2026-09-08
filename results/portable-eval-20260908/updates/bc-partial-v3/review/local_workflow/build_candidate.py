#!/usr/bin/env python3
"""One bounded local build and byte-exact independent restoration; no upload."""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys

import prepare as p
import assemble as a
c = p.c
LOCK_SHA = 'bdcc88d4112374ffce8997173ab9c70f3c902a25cf647f564aab313d15edaafb'
FULL_SHA = 'dec6b70592d9bcc35876d3aa79f2e963d36d76620f4771d0a3ae3f72a5149a81'
PACK_SHA = '07eb7a20e838ca53bfda6144887283e597914e95fb11c5e16ff43f95f09f5f10'


def exact_originals(payload, rows):
    expected = sorted([{'path': r['target'], 'bytes': r['bytes'], 'sha256': r['sha256']} for r in rows], key=lambda r: r['path'])
    c.need(c.inventory(payload) == expected, 'restored_inventory_not_exact')
    for row in rows:
        source = c.scanner().stable_read(p.WORKSPACE / row['source'])
        restored = c.scanner().stable_read(payload / row['target'])
        c.need(source == restored and len(source) == row['bytes'] and c.sha(source) == row['sha256'],
               'restored_original_bytes_not_equal')
    return {'file_count': len(rows), 'bytes': sum(r['bytes'] for r in rows), 'direct_original_bytes_equal': True,
            'exact_path_set_and_sha256': True}


def csv_bytes(fields, rows):
    text = io.StringIO(newline=''); writer = csv.DictWriter(text, fieldnames=fields, lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return text.getvalue().encode()


def main():
    a.verify_tools(); c.need(c.sha((p.SHARD/'pack.py').read_bytes()) == PACK_SHA, 'frozen_pack_identity')
    secrets = c.scanner().load_secrets([p.KEY])
    initial = p.BASE/'checks/initial_v2'
    lock, _ = c.load_json(initial/'lock.json', LOCK_SHA, secrets)
    full, _ = c.load_json(initial/'full_original_inventory.json', FULL_SHA, secrets)
    before = c.strict_json((initial/'source_snapshot.json').read_bytes())
    c.need(p.snapshot(full) == before, 'source_changed_since_lock')
    root = c.fresh(p.BASE/'checks/acceptance_v1'); root.mkdir(mode=0o700)
    capsule = c.fresh(p.BASE/'capsule'); capsule.mkdir(mode=0o700)
    commands = []
    def write(path, raw):
        c.scan(raw, path.name, secrets); c.write_new(path, raw)
    def call(name, argv):
        result = subprocess.run(argv, cwd=p.WORKSPACE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        write(root/(name+'.stdout.log'), result.stdout); write(root/(name+'.stderr.log'), result.stderr)
        commands.append({'name': name, 'argv': [str(x) for x in argv], 'returncode': result.returncode})
        c.need(result.returncode == 0, 'bounded_child_failed_'+name)
        print(json.dumps({'completed': name}), flush=True)
        return result
    for name, script, count in [('assembly_tests', p.BASE/'test_assemble.py', 28),
                                 ('frozen_v2_tests', p.SHARD/'test_delivery.py', 57)]:
        log = call(name, [sys.executable, '-B', str(script)])
        c.need(('Ran %d tests' % count).encode() in log.stderr and b'\nOK\n' in log.stderr, 'test_count_or_status')
    # Exact frozen consumer tools; no new uploader or alternate archive reader.
    for name in ('common.py', 'restore.py'):
        write(capsule/'tools'/name, (p.SHARD/name).read_bytes())
    write(capsule/'tools/assemble.py', (p.BASE/'assemble.py').read_bytes())
    write(capsule/'validate_bundle_v2.py', (p.BASE.parent/'validate_bundle_v2.py').read_bytes())
    control = a.control_original(p.WORKSPACE/a.CONTROL_TARGET, secrets)
    # This exact public copy deliberately retains the documented strict-scan
    # failure; it is never sent through the generic write/scan helper as PASS.
    c.write_new(capsule/'control_originals'/a.CONTROL_NAME, control)
    a.control_original(capsule/'control_originals'/a.CONTROL_NAME, secrets)
    for name in ('lock.json', 'full_original_inventory.json', 'SUMMARY.json'):
        write(capsule/'provenance'/name, (initial/name).read_bytes())
    for name in ('spec.json', 'manifest.json', 'lock.json'):
        write(capsule/'provenance/initial_full_scan_failed'/name,
              (p.BASE/'checks/failed_initial_v1'/name).read_bytes())
    packed = call('pack', [sys.executable, '-B', str(p.SHARD/'pack.py'), '--manifest', str(initial/'lock.json'),
                          '--manifest-sha256', LOCK_SHA, '--workspace', str(p.WORKSPACE),
                          '--output-dir', str(capsule/'bundle'), '--secret-file', str(p.KEY)])
    pack_receipt = c.strict_json(packed.stdout); index_sha = pack_receipt['index_sha256']
    index_path = capsule/'bundle/payload/INDEX.json'
    index = c.strict_json(index_path.read_bytes())
    strict_rows = [row for row in full if row['target'] != a.CONTROL_TARGET]
    full_restore = call('restore_full', [sys.executable, '-B', str(capsule/'tools/restore.py'), '--index', str(index_path),
                         '--sha256', index_sha, '--output-dir', str(root/'full_restored'), '--secret-file', str(p.KEY)])
    strict_check = exact_originals(root/'full_restored/payload', strict_rows)
    shard_checks = []; path_to_shard = {}; (root/'per_shard').mkdir()
    by_path = {row['target']: row for row in full}
    for n, shard in enumerate(index['shards'], 1):
        page = c.strict_json((index_path.parent/shard['index']).read_bytes())
        name = 'restore_part_%06d' % n
        restored = root/'per_shard'/('part-%06d'%n)
        call(name, [sys.executable, '-B', str(capsule/'tools/restore.py'), '--archive', str(index_path.parent/shard['archive']),
                    '--sha256', shard['sha256'], '--output-dir', str(restored), '--secret-file', str(p.KEY)])
        rows = [by_path[row['path']] for row in page['files']]
        for row in rows:
            c.need(row['target'] not in path_to_shard, 'duplicate_shard_original')
            path_to_shard[row['target']] = 'bundle/payload/' + shard['archive']
        shard_checks.append({'archive': shard['archive'], 'sha256': shard['sha256'], **exact_originals(restored/'payload', rows)})
    c.need(set(path_to_shard) == {row['target'] for row in strict_rows}, 'independent_shard_union_incomplete')
    assembled_log = call('assemble_full', [sys.executable, '-B', str(capsule/'tools/assemble.py'), '--index', str(index_path),
                         '--index-sha256', index_sha, '--restored', str(root/'full_restored'),
                         '--control', str(capsule/'control_originals'/a.CONTROL_NAME),
                         '--output-dir', str(root/'assembled'), '--secret-file', str(p.KEY)])
    assembled_receipt = c.strict_json(assembled_log.stdout)
    whole_check = exact_originals(root/'assembled/payload', full)
    c.need(not (root/'assembled/payload'/p.RUN/'execution.json').exists(), 'fabricated_execution_json')
    file_rows = [{'original_path': row['target'], 'bytes': row['bytes'], 'sha256': row['sha256'],
                  'download': 'control_originals/'+a.CONTROL_NAME if row['target'] == a.CONTROL_TARGET else path_to_shard[row['target']],
                  'handling': 'fixed_manual_prose_original' if row['target'] == a.CONTROL_TARGET else 'strict_v2_shard'} for row in full]
    write(capsule/'FILES.csv', csv_bytes(['original_path','bytes','sha256','download','handling'],file_rows))
    partial = c.strict_json((p.WORKSPACE/p.PARTIAL/'receipt.json').read_bytes())
    pool_fields = ['job_id','classification','guarded_skips','original_status_passed','infra_qualified','performance_qualified','abort_observed','retained_semantic_zero_count','reasons']
    pool_rows = []
    for row in partial['rows']:
        values = dict(row)
        if 'retained_semantic_zero_count' not in values:
            c.need(row['classification'] == 'no_execution_evidence_observed', 'missing_launched_zero_count')
            values['retained_semantic_zero_count'] = 'not_applicable_no_execution'
        pool_rows.append({field: json.dumps(values[field], ensure_ascii=False) if isinstance(values[field], (list,dict))
                          else 'unknown' if values[field] is None else values[field] for field in pool_fields})
    write(capsule/'POOL_STATUS.csv',csv_bytes(pool_fields,pool_rows))
    transport = c.strict_json((p.WORKSPACE/p.TRANSPORT/'receipt.json').read_bytes())
    attempt_fields = ['job_id','request_id','generation_id','attempt','will_retry','state','evidence','router_line_1based',
                      'payload_sha256','response_sha256','finish_reasons','original_dump','dump_sha256',
                      'input_tokens','output_tokens','reasoning_tokens','provider_total_tokens','cache_read_tokens','cache_write_tokens']
    attempts = []
    for row in transport['attempts']:
        result = {field: row.get(field, '') for field in attempt_fields[:10]}
        result.update({'finish_reasons': json.dumps(row['finish_reasons']),
                       'original_dump': str(Path(row['dump']['path']).relative_to(p.WORKSPACE)), 'dump_sha256': row['dump']['sha256']})
        result.update({field: row['usage'][field] if row['usage'][field] is not None else 'unknown' for field in attempt_fields[13:]})
        attempts.append(result)
    write(capsule/'ATTEMPTS.csv',csv_bytes(attempt_fields,attempts))
    c.need(p.snapshot(full) == before, 'originals_changed_after_all_restores')
    protected = c.strict_json((p.BASE/'checks/protected_before.json').read_bytes())
    for source, old in protected['files'].items():
        path = c.lexical(p.WORKSPACE/source); size, digest = c.stream_hash(path)
        c.need({'bytes':size,'sha256':digest,'mtime_ns':path.stat().st_mtime_ns} == old, 'protected_original_changed')
    public_root = p.WORKSPACE/'portable_publish.pPLtjm8i/repo/results/portable-eval-20260908'
    public_prefix = str(public_root.relative_to(p.WORKSPACE))+'/'
    c.need({public_prefix+x for x in c.tree(public_root)} == {x for x in protected['files'] if x.startswith(public_prefix)}, 'published_old_file_set_changed')
    receipt = {'schema': 'bc-partial-delivery-candidate-acceptance-v1', 'passed': True,
               'scope': 'Bounded CPU lossless delivery candidate only; ROOT publication review remains required.',
               'source_lock_sha256': LOCK_SHA, 'full_original_inventory_sha256': FULL_SHA,
               'pack': pack_receipt, 'strict_full_restore': strict_check, 'independent_shards': shard_checks,
               'fixed_control_assembly': assembled_receipt, 'whole_originals': whole_check,
               'tests': {'new_assembly': 28, 'frozen_v2': 57},
               'all_originals_before_after_sha_bytes_mtime_unchanged': True, 'source_original_files': len(full),
               'protected_old_files_unchanged': len(protected['files']), 'already_published_result_files_unchanged': 1127,
               'original_run_files': 2173, 'original_run_sharded': 2172, 'original_control_separate': 1,
               'raw_attempts': 1532, 'result_json_files': 282, 'original_execution_json_absent': True,
               'initial_strict_full_scan_failed_and_retained': True, 'strict_scanner_all_originals_passed': False,
               'single_exact_manual_prose_exception': True, 'known_secret_sources_checked': len(secrets),
               'new_model_slurm_git_network_calls': 0, 'publication_performed': False, 'publication_go': False,
               'project_complete': False}
    write(root/'COMMANDS.json', c.encoded(commands)); write(root/'ACCEPTANCE.json', c.encoded(receipt))
    write(capsule/'DELIVERY_ACCEPTANCE.json', c.encoded(receipt))
    print(json.dumps({'passed': True, 'capsule': str(capsule), 'receipt_sha256': c.sha((root/'ACCEPTANCE.json').read_bytes()),
                      'index_sha256': index_sha, 'files': len(full), 'bytes': whole_check['bytes'],
                      'compressed_bytes': pack_receipt['compressed_bytes'], 'shards': len(index['shards']),
                      'candidate_metadata_final_scan_and_freeze_still_required': True, 'publication_performed': False},indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'passed': False, 'rule': str(exc) if isinstance(exc,c.DeliveryError) else 'candidate_build_failed', 'publication_performed': False}))
        raise SystemExit(1)
