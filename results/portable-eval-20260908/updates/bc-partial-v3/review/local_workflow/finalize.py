#!/usr/bin/env python3
"""Freeze the bounded candidate after byte-exact assembly, never stage/push."""
import json
from pathlib import Path
import re
import subprocess
import sys

import prepare as p
import assemble as a
import build_candidate as b
c = p.c
INDEX_SHA = 'f756064abe54adc4a0fc21d10e9e0ef6d76ac863c3eae325dc58fb5913c413b0'


def main():
    a.verify_tools()
    secrets = c.scanner().load_secrets([p.KEY]); validator = c.scanner()
    capsule = p.BASE/'capsule'; accepted = p.BASE/'checks/acceptance_v1/ACCEPTANCE.json'
    acceptance, _ = c.load_json(accepted, secrets=secrets)
    c.need(acceptance['passed'] and acceptance['whole_originals']['file_count'] == 2348
           and acceptance['pack']['index_sha256'] == INDEX_SHA, 'build_acceptance_missing_or_wrong')
    out = c.fresh(p.BASE/'checks/final_v1'); out.mkdir(mode=0o700)
    def write(path, raw):
        c.need(len(raw) <= c.INDEX_LIMIT, 'candidate_metadata_limit')
        c.scan(raw, path.name, secrets); c.write_new(path, raw)
    # Public fixtures use only the fixed public control original plus synthetic
    # data and a synthetic local known marker. Frozen producer copied unchanged.
    write(capsule/'tools/pack.py', (p.SHARD/'pack.py').read_bytes())
    write(capsule/'tools/test_assemble.py', (p.BASE/'test_assemble.py').read_bytes())
    tests = subprocess.run([sys.executable, '-B', str(capsule/'tools/test_assemble.py')],
                           cwd=p.WORKSPACE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    write(out/'public_tests.stdout.log', tests.stdout); write(out/'public_tests.stderr.log', tests.stderr)
    c.need(tests.returncode == 0 and b'Ran 28 tests' in tests.stderr and b'\nOK\n' in tests.stderr,
           'portable_public_fixture_failed')
    write(capsule/'review/assembly_tests.log', tests.stdout + tests.stderr)
    metadata_tests = subprocess.run([sys.executable, '-B', str(p.BASE/'test_metadata.py')],
                                    cwd=p.WORKSPACE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c.need(metadata_tests.returncode == 0 and b'Ran 5 tests' in metadata_tests.stderr and b'\nOK\n' in metadata_tests.stderr,
           'metadata_fixture_failed')
    write(out/'metadata_tests.stdout.log', metadata_tests.stdout); write(out/'metadata_tests.stderr.log', metadata_tests.stderr)
    write(capsule/'review/metadata_tests.log', metadata_tests.stdout + metadata_tests.stderr)
    difference = subprocess.run(['diff', '-u', '--label', '/dev/null', '--label',
                                 'b/publication/bc_partial_delivery_v3/assemble.py', '/dev/null',
                                 str(p.BASE/'assemble.py')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c.need(difference.returncode == 1 and not difference.stderr, 'wrapper_added_diff_failed')
    write(capsule/'review/assemble.added.diff', difference.stdout)
    for name in ('assemble.py','test_assemble.py','prepare.py','prepare_v2.py','build_candidate.py','metadata_completion.py','test_metadata.py','finalize.py','DEVELOPMENT.md'):
        # Source of the local workflow is available for ROOT review; only the
        # portable consumer/fixture is needed by downloaders. All copied bytes
        # remain exact, not a rewritten approximation of the source.
        write(capsule/'review/local_workflow'/name, (p.BASE/name).read_bytes())
    for name in ('build_candidate.failed_original.py','receipt.json'):
        write(capsule/'review/development_csv_failure_v1'/name,
              (p.BASE/'checks/development_csv_failure_v1'/name).read_bytes())
    references = {'frozen_v2_producer_sha256': b.PACK_SHA, 'frozen_common_sha256': a.TOOL_PINS['common.py'],
                  'frozen_restore_sha256': a.TOOL_PINS['restore.py'], 'frozen_scanner_sha256': c.SCANNER_SHA,
                  'accepted_v2_freeze_sha256': p.PINS['publication/shard_delivery_candidate_v2/FREEZE.json'],
                  'independent_v2_review_sha256': p.PINS['publication/shard_delivery_review_v2/REVIEW.json'],
                  'full_source_lock_sha256': b.LOCK_SHA, 'whole_original_inventory_sha256': b.FULL_SHA,
                  'whole_originals_strict_scan_passed': False,
                  'single_fixed_control_original': {'path': 'control_originals/'+a.CONTROL_NAME, 'bytes': a.CONTROL_BYTES,
                      'sha256': a.CONTROL_SHA, 'original_path': a.CONTROL_TARGET,
                      'original_scanner_findings': {'credential_metadata_field': 1}},
                  'source_v3_tree_sha256': 'd1606db7d6036c8975ce9d3e556daf7fa2ce4604879f2b3878435b0f96aebb78',
                  'prior_source_archive_sha256': '97ecfe148a2c47e811dbf15e0b820f28979972c1ad7a5939cc065b1f4ee0e15b',
                  'preservation': 'Original bytes and relative paths, including all failures/unknowns; summaries never substitute originals.',
                  'publication_performed': False, 'project_complete': False}
    write(capsule/'PROVENANCE.json', c.encoded(references))
    # A source-package link is deliberately external to this appended capsule;
    # validate it against the already-published exact blob, not a live worktree.
    links = re.findall(r'\[[^\]]*\]\(([^)]+)\)', (capsule/'README.zh.md').read_text())
    for link in links:
        if link == '../../source/accepted-source-v3.tar.gz':
            path = p.WORKSPACE/'portable_publish.pPLtjm8i/repo/results/portable-eval-20260908/source/accepted-source-v3.tar.gz'
            c.need(c.stream_hash(path)[1] == references['prior_source_archive_sha256'], 'existing_source_reference_changed')
        else:
            c.relative(link)
            # SHA256SUMS is generated immediately below and then checked again.
            c.need(link == 'SHA256SUMS' or c.lexical(capsule/link).is_file(), 'broken_public_readme_link')
    base_rows = c.inventory(capsule)
    manifest = {'schema': 'bc-partial-capsule-file-manifest-v1',
                'scope': 'All capsule files except this MANIFEST.json and SHA256SUMS; SHA256SUMS also binds this manifest.',
                'file_count': len(base_rows), 'bytes': sum(x['bytes'] for x in base_rows), 'files': base_rows,
                'bundle_index_sha256': INDEX_SHA, 'whole_original_files': 2348, 'whole_original_bytes': 120489460,
                'strict_all_originals_passed': False, 'manual_exception_exactly_one': True, 'publication_performed': False}
    write(capsule/'MANIFEST.json', c.encoded(manifest))
    checksum_rows = c.inventory(capsule)
    write(capsule/'SHA256SUMS', ''.join(x['sha256']+'  '+x['path']+'\n' for x in checksum_rows).encode())
    expected_files = {x['path'] for x in checksum_rows} | {'SHA256SUMS'}
    c.need(c.tree(capsule) == expected_files, 'candidate_exact_path_set')
    for row in checksum_rows:
        c.need(c.stream_hash(capsule/row['path']) == (row['bytes'],row['sha256']), 'candidate_after_manifest_changed')
    # Original frozen validator scans every public plain file and every archive
    # member. The one fixed control is separate and its original FAIL retained.
    artifacts = []; control_name = 'control_originals/'+a.CONTROL_NAME
    for n, name in enumerate(sorted(expected_files)):
        path = c.lexical(capsule/name)
        if name == control_name:
            a.control_original(path, secrets)
            continue
        size, digest = c.stream_hash(path)
        artifacts.append({'id': 'candidate_%03d'%n, 'kind': 'source_archive' if name.endswith('.tar.gz') else 'sealed_file',
                          'sealed': True, 'source': str(path.relative_to(p.WORKSPACE)), 'target': name,
                          'anchor': {'path': path.name, 'sha256': digest}})
    spec = {'schema_version': 1, 'approved': True, 'require_secret_sources': True, 'artifacts': artifacts,
            'scope': 'Strict scan of every capsule file/archive except one fixed ROOT-reviewed prose control original; no whole strict PASS claim.',
            'required_stages': [x['id'] for x in artifacts]+['ROOT_publication_review','complete_formal_matrix'],
            'publication_performed': False}
    print(json.dumps({'phase':'final_frozen_capsule_scan','public_files':len(expected_files)}),flush=True)
    scan, lock = validator.validate(spec, p.WORKSPACE, secrets, seal=True)
    c.need(scan['safe_to_stage'] and not scan['findings'], 'capsule_strict_subset_scan_failed')
    for name in sorted(expected_files):
        if name.endswith('.tar.gz') or name == control_name:
            continue
        c.scan(validator.stable_read(capsule/name), name, secrets)
    verified = a.restore.verify_bundle(capsule/'bundle/payload/INDEX.json', INDEX_SHA, secrets)
    c.need(len(verified['files']) == 2347 and a.CONTROL_TARGET not in {x['path'] for x in verified['files']}, 'fixed_control_not_separate')
    full, _ = c.load_json(p.BASE/'checks/initial_v2/full_original_inventory.json', b.FULL_SHA, secrets)
    before = c.strict_json((p.BASE/'checks/initial_v2/source_snapshot.json').read_bytes())
    c.need(p.snapshot(full) == before, 'source_immutability_after_final_scan')
    protected = c.strict_json((p.BASE/'checks/protected_before.json').read_bytes())
    for source, old in protected['files'].items():
        path = c.lexical(p.WORKSPACE/source); size, digest = c.stream_hash(path)
        c.need({'bytes':size,'sha256':digest,'mtime_ns':path.stat().st_mtime_ns} == old, 'protected_original_changed')
    c.need(c.tree(capsule) == expected_files, 'candidate_file_set_changed_during_final_scan')
    for row in checksum_rows:
        c.need(c.stream_hash(capsule/row['path']) == (row['bytes'],row['sha256']), 'candidate_bytes_changed_during_final_scan')
    for name,value in [('strict_spec.json',spec),('strict_lock.json',lock),('strict_manifest.json',scan)]:
        write(out/name,c.encoded(value))
    public_rows = c.inventory(capsule)
    final = {'schema': 'bc-partial-candidate-final-v1', 'passed': True, 'publication_go': False,
             'scope': 'Frozen local candidate for ROOT independent publication review only, not full/formal project acceptance.',
             'whole_original_files': 2348, 'whole_original_bytes': 120489460, 'original_run_files': 2173,
             'strict_sharded_originals': 2347, 'fixed_manual_control_originals': 1,
             'strict_scanner_all_originals_passed': False, 'original_full_scan_failure_preserved': True,
             'public_file_count': len(public_rows), 'public_bytes': sum(x['bytes'] for x in public_rows),
             'largest_public_file': max(public_rows,key=lambda x:x['bytes']), 'archive_shards': 10,
             'compressed_archive_bytes': 21400125, 'index_sha256': INDEX_SHA,
             'capsule_manifest_sha256': c.sha((capsule/'MANIFEST.json').read_bytes()),
             'sha256sums_sha256': c.sha((capsule/'SHA256SUMS').read_bytes()),
             'new_assembly_tests': 28, 'frozen_v2_tests': 57, 'public_portable_tests': 28,
             'metadata_tests': 5,
             'python_version': sys.version,
             'full_and_individual_shards_and_assembled_bytes': acceptance['whole_originals'],
             'strict_public_subset_scan_findings': scan['findings'], 'public_readme_links_checked': len(links),
             'full_original_snapshot_unchanged': True, 'protected_old_files_unchanged': len(protected['files']),
             'known_secret_sources_checked': len(secrets), 'project_complete': False,
             'git_network_model_slurm_calls': 0, 'publication_performed': False}
    write(out/'FINAL.json',c.encoded(final))
    # Payloads from verification are bound by their full inventory COMPLETE
    # markers; do not duplicate thousands of restored rows into the freeze.
    frozen = []
    for name in sorted(c.tree(p.BASE)):
        if name == 'FREEZE.json':
            raise c.DeliveryError('freeze_already_exists')
        if name.startswith('checks/acceptance_v1/') and '/payload/' in name:
            continue
        path = p.BASE/name; size,digest = c.stream_hash(path)
        frozen.append({'path':name,'bytes':size,'sha256':digest,'mtime_ns':path.stat().st_mtime_ns})
    freeze = {'schema':'bc-partial-candidate-freeze-v1','scope':final['scope'],'files':frozen,
              'file_count':len(frozen),'final_receipt_sha256':c.sha((out/'FINAL.json').read_bytes()),
              'restored_payloads_bound_by_complete_full_inventory':True,'publication_go':False,
              'strict_scanner_all_originals_passed':False,'fixed_control_manual_exception_count':1,
              'publication_performed':False,'project_complete':False}
    write(p.BASE/'FREEZE.json',c.encoded(freeze))
    print(json.dumps({**final,'freeze_sha256':c.sha((p.BASE/'FREEZE.json').read_bytes()),
                      'final_receipt_sha256':freeze['final_receipt_sha256']},indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'passed':False,'rule':str(exc) if isinstance(exc,c.DeliveryError) else 'candidate_finalize_failed','publication_performed':False}))
        raise SystemExit(1)
