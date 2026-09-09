"""Hash only the ROOT-enumerated closed outer metadata; no reference following."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

W = Path('/lustrefs/users/chufan.shi/codex_space_tn')
P = W / 'publication'
OP = W / 'portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909'
OUT = P / 'k3_formal_outer_evidence_candidate_v1'
LEAF = 'results/portable-eval-20260908/full_delivery_v5/kimi-k3-original-node-failure-20260909'
R = P / 'k3_formal_original_local_delivery_v2'
S = P / 'k3_formal_original_scan_v1'
C = P / 'k3_controls_local_delivery_v1'
groups = {}

def add(group, root, names):
    groups.setdefault(group, []).extend(root / name for name in names)

for i in range(1, 34):
    b = 'batch-%06d' % i
    add('raw_batch_proofs', R / 'batches' / b, [
        'RESULT.json', 'WHOLE_FILE_COMPARISON.json', 'restore/COMPLETE.json',
        'pack.started.json', 'pack.exit.json', 'pack.stdout.json', 'pack.stderr.log',
        'restore.started.json', 'restore.exit.json', 'restore.stdout.json', 'restore.stderr.log'])
    add('raw_scan_outputs', S, ['specs/' + b + '.json', b + '/manifest.json',
        b + '/lock.json', b + '.status.json', b + '.receipt.json'])
    add('raw_scope_candidates', P / 'k3_formal_original_scope_candidate_v1/candidate',
        ['batches/' + b + '.candidate.json'])
add('raw_run_operator_metadata', R, ['PREFLIGHT.json', 'STARTED.json', 'SUMMARY.json'])
add('raw_scan_outputs', S, ['PREPARED.json', 'SCAN_RECEIPT.json'])
add('raw_scan_controls', P, ['ROOT_K3_ORIGINAL_SCAN_GO_20260909.json', 'k3_formal_original_scan_operator_v1/COMPLETION.json'])
add('raw_scope_candidates', P / 'k3_formal_original_scope_candidate_v1/candidate',
    ['inventory.json', 'ASSEMBLY_RECEIPT.candidate.json', 'batches/INDEX.candidate.json'])
add('raw_root_proofs', P / 'k3_formal_original_local_delivery_v2_operator',
    ['ROOT_START_ACCEPTANCE.json', 'ROOT_COMPLETION.json', 'ROOT_LOCAL_PROOF.json', 'ROOT_METADATA_CHECK.executed_inline.py'])
add('raw_pack_go', P, ['ROOT_K3_ORIGINAL_PACK_GO_20260909.json'])
add('controls_scan_metadata', P, ['k3_controls_scan_v1/lock.json', 'k3_controls_scan_v1/manifest.json',
    'k3_controls_scan_v1_inputs/ROOT_APPROVED_SPEC.json', 'ROOT_K3_CONTROLS_SCAN_GO_20260909.json',
    'k3_controls_scan_v1_operator/ROOT_COMPLETION.json'])
add('controls_seal_metadata', OP, ['k3_delivery_controls_sealed_v1/STARTED.json',
    'k3_delivery_controls_sealed_v1/CLOSURE.json', 'k3_delivery_controls_sealed_v1/inventory.json',
    'ROOT_K3_CONTROLS_HASH_GO_20260909.json', 'k3_delivery_controls_sealed_v1_operator/ROOT_COMPLETION.json'])
add('controls_batch_candidates', P / 'k3_controls_batches_candidate_v1', ['INDEX.candidate.json', 'batch-000001.candidate.json'])
add('controls_local_proofs', C, ['ROOT_LOCAL_PROOF.json', 'OPERATOR_COMPLETION.json',
    'ROOT_PACK_GO.json', 'ROOT_RESTORE_GO.json', 'restored/COMPLETE.json'])
add('frozen_practical_code', P / 'k3_formal_original_delivery_candidate_v2',
    ['operator.py', 'README.zh.md', 'PRODUCTION_DIFF.patch', 'CPU_RECEIPT.json'])
add('frozen_practical_code', P, ['restart_v5_closed_local_delivery_v1/operator.py',
    'pinned_batches_scan_candidate_v1/scan_batches.py', 'full_scope_batch_candidate_v1/prepare.py'])
add('frozen_practical_code', P / 'k3_formal_collection_assembly_candidate_v1',
    ['assemble.py', 'README.zh.md', 'PRODUCTION_DIFF.patch', 'CPU_RECEIPT.json'])
add('assembly_selection_and_go', P / 'k3_formal_collection_assembly_v1', ['ROOT_SELECTION.json', 'ROOT_GO.json'])

PINS = {
 R / 'SUMMARY.json': '39a90746673767bc414c99e186a45eb734c8470f1b98b44439dad423b7950c84',
 P / 'k3_formal_original_local_delivery_v2_operator/ROOT_LOCAL_PROOF.json': '5fbd9dc15963bd8cfbf13733e181a131f4fb015c1241460c0b623f58ee7e1642',
 P / 'k3_formal_original_local_delivery_v2_operator/ROOT_COMPLETION.json': 'fc031239eee39b28d541b290afe80b927dfe163fe5ac62b8294f97706039ee12',
 P / 'k3_formal_collection_assembly_v1/ROOT_SELECTION.json': '08223899650c4cb2f668a96ee618f9bc2d3976bf5ac28a0257db3762d61f71e9',
 P / 'k3_formal_collection_assembly_v1/ROOT_GO.json': '8c43169a88de3122336391251ba84da28a2dd8880f427bbd76c3267ccefd03c8',
 S / 'PREPARED.json': 'bd7501f4dec50f94000f3bcabcfd49c4da8d916d2e1873a33b534482dffb513a',
 S / 'SCAN_RECEIPT.json': '03aa4521c42511fe5088ac46393dcd4f3f2dbc434c60db46a95c3a0018e7f70d',
 P / 'ROOT_K3_ORIGINAL_SCAN_GO_20260909.json': '6ec91d9ca4513d9aacc9412145c41858ebed1202d95f78db3d2542f3dd346a8c',
 P / 'k3_formal_original_scan_operator_v1/COMPLETION.json': '31f55eb67b333d5d79dde1cf7df96aaf4c15f11aa19d22825cec94b24c30a02d',
 P / 'ROOT_K3_ORIGINAL_PACK_GO_20260909.json': '2ae2a5220e35a347d5bd3b4f09fab7daef5f28f2646536f727913075330123db',
 P / 'k3_formal_original_scope_candidate_v1/candidate/inventory.json': '8877bf050b9ecea2fc3c06c421916bd1c039fb161cf70c8bf5d6cbfe2b681281',
 P / 'k3_formal_original_scope_candidate_v1/candidate/batches/INDEX.candidate.json': '0a4f98032deb59447da592def5ad9f8c070b1964a228e7527e81851b7adec84a',
 P / 'k3_controls_scan_v1/lock.json': '61df73d8f69804c8a18044ff0665ef182cafa3b671ea0212de77db868fc5d1d4',
 P / 'k3_controls_scan_v1/manifest.json': '272d85c5744dce845b06308280379a2c6a1a45bcd4bec8d0caf12bf962b71534',
 OP / 'k3_delivery_controls_sealed_v1/inventory.json': '7afbe4dae74e2925dafa19d73170a828a9437d9c08944a704b7ee80395464367',
 OP / 'k3_delivery_controls_sealed_v1/CLOSURE.json': 'daf5b8748a9add0941f55b878f7931060d439a64b5a82285d650624562205c5a',
 C / 'ROOT_LOCAL_PROOF.json': 'fb22ee36c3bff2e9037ae21831186ccdc7bf1059fe04d016533f67f2d8a6277e',
 C / 'OPERATOR_COMPLETION.json': '57f35cb4d08d9b784888af69612d1ceefba0823754ea5d1cf431cdd27a47a8d4',
 C / 'ROOT_PACK_GO.json': 'd602510aca363891422c687b677c4eff4c36bef56f858057aa7f79f91e612b53',
 C / 'ROOT_RESTORE_GO.json': 'c6fd97735275419bcde8170a4a6b9081e2da04849ab721a0dfaa87271f971d59',
 C / 'restored/COMPLETE.json': '6fb311c14ff07374cf5ebf048237a724fae9381fd2c36e6fe4ec08918a7c7c2e',
 P / 'k3_formal_original_delivery_candidate_v2/operator.py': 'cc1b646b46d258d3071e9fe94bfe849683500beafeca68bca7fbbc56c14ccb14',
 P / 'k3_formal_original_delivery_candidate_v2/README.zh.md': '268b57b53902a01ee3b2ab3b29bd3e4280cf6b42675fdfc54a8a20b5c658c9a2',
 P / 'k3_formal_original_delivery_candidate_v2/PRODUCTION_DIFF.patch': '014b1d226709e4b7f78cb12eee2887baaa7b66126d3c032cf99ea93f85dec31b',
 P / 'k3_formal_original_delivery_candidate_v2/CPU_RECEIPT.json': 'c7bef23eb4e52a5e75b6993b88b8232a136c0240e24a7f54c61347101da13c80',
 P / 'restart_v5_closed_local_delivery_v1/operator.py': '979fd024d739eb927825d156048cbd6a1850fb27ddc6a5c5677abba1e4d7d497',
 P / 'pinned_batches_scan_candidate_v1/scan_batches.py': '5b3dbdf84f789dec731a3f8c821c2981a0f00e61f4b951141e022fab491b568b',
 P / 'full_scope_batch_candidate_v1/prepare.py': '77a69230c7ef2fd9de1767c63d237f8514411372ce10eac902d71b1d2af65c60',
 P / 'k3_formal_collection_assembly_candidate_v1/assemble.py': 'c90254493efd692e58a79a5bc1de766bf61ae3554a04d76f9024cf6e5fbc14dc',
 P / 'k3_formal_collection_assembly_candidate_v1/README.zh.md': 'b109afe4fa40ccaf379b5db3ac5faa282fdea96ca38e287cc78c5c93bc3e08b2',
 P / 'k3_formal_collection_assembly_candidate_v1/PRODUCTION_DIFF.patch': 'dd13fff4bfdcfcc020c372c6b112da5c2e450ac5e4c4073102ff29d6bd9f88c0',
 P / 'k3_formal_collection_assembly_candidate_v1/CPU_RECEIPT.json': '8454c53f911b516d83a6f88a51f42af9760f4af853b9724ae892d7d77dac32f3',
}

def need(test, code):
    if not test: raise ValueError(code)

def fingerprint(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_mode)

def hashed(path):
    need(path.is_absolute() and path.resolve(strict=True) == path, 'noncanonical_source')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_size < 100 * 1024**2, 'source_type_or_blob_limit')
        digest = hashlib.sha256(); size = 0
        for block in iter(lambda: stream.read(1024**2), b''):
            digest.update(block); size += len(block)
            need(size <= before.st_size, 'source_grew')
        after = os.fstat(stream.fileno())
    need(fingerprint(before) == fingerprint(after) == fingerprint(path.lstat()) and size == before.st_size, 'source_changed')
    h = digest.hexdigest()
    need(path not in PINS or h == PINS[path], 'external_pin_changed')
    return size, h, fingerprint(after)

def write_new(name, obj):
    raw = (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    with os.fdopen(os.open(OUT / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as out:
        out.write(raw); out.flush(); os.fsync(out.fileno())
    return {'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def main():
    paths = [(p, g) for g, ps in groups.items() for p in ps]
    need(len(paths) == 606 and len({p for p, g in paths}) == 606, 'exact_scope_or_duplicate')
    need(set(PINS) <= {p for p, g in paths}, 'pin_outside_scope')
    for name in ('FILES.candidate.json', 'HASH_RECEIPT.json'):
        need(not (OUT / name).exists(), 'refuse_existing_output')
    rows, stats = [], {}
    for p, group in sorted(paths):
        size, h, f = hashed(p); rel = p.relative_to(W).as_posix(); stats[p] = f
        rows.append({'source_path': str(p), 'target_path': 'evidence/workspace/' + rel,
            'bytes': size, 'sha256': h, 'group': group,
            'pin_basis': 'externally_supplied_sha_checked' if p in PINS else 'observed_complete_sha_this_step'})
    rows.sort(key=lambda row: row['target_path'])
    targets = [r['target_path'] for r in rows]
    need(targets == sorted(targets) and len(set(targets)) == len(targets), 'target_order_or_duplicate')
    need(not any(b.startswith(a + '/') for a, b in zip(targets, targets[1:])), 'target_prefix_conflict')
    for row in rows:
        p = Path(row['source_path']); size, h, f = hashed(p)
        need((size, h) == (row['bytes'], row['sha256']) and f == stats[p], 'second_full_hash_or_stat_changed')
    manifest = {'schema': 'k3-formal-outer-evidence-files-candidate-v1', 'candidate': True, 'approved': False,
        'workspace': str(W), 'leaf': LEAF, 'file_count': len(rows), 'total_bytes': sum(r['bytes'] for r in rows),
        'original_execution_complete': False, 'original_score_complete': False,
        'copy_performed': False, 'content_scan_performed': False, 'publication_performed': False, 'files': rows}
    ref = write_new('FILES.candidate.json', manifest)
    counts = {g: {'files': len(ps), 'bytes': sum(r['bytes'] for r in rows if r['group'] == g)} for g, ps in groups.items()}
    receipt = {'schema': 'k3-formal-outer-evidence-hash-receipt-v1', 'candidate_only': True, 'approved': False,
        'manifest_ref': ref, 'file_count': len(rows), 'total_bytes': manifest['total_bytes'], 'groups': counts,
        'external_sha_pins_checked': len(PINS), 'full_hash_passes': 2, 'stable_stat_and_all_bytes_equal': True,
        'all_sources_canonical_regular': True, 'exact_unique_sorted_targets_and_no_prefix_conflict': True,
        'maximum_single_file': max(rows, key=lambda r: r['bytes']),
        'source_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'no_reference_following': True, 'source_payloads_parsed': False, 'private_key_reads': 0,
        'archive_or_raw_or_restored_payload_reads': 0, 'active_glm_reads': 0,
        'copy_or_content_scan_or_pack_or_restore_or_git_performed': False,
        'assembly_payload_or_actual_receipt_read': False, 'remote_complete_claimed': False, 'scientific_complete_claimed': False,
        'posix_metadata_restore_claimed': False, 'not_a_fresh_scientific_review': True}
    final_ref = write_new('HASH_RECEIPT.json', receipt)
    print(json.dumps({'passed': True, 'candidate_only': True, 'file_count': len(rows), 'total_bytes': manifest['total_bytes'],
        'manifest_ref': ref, 'receipt_ref': final_ref, 'groups': counts}, sort_keys=True))

if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(json.dumps({'passed': False, 'reason': 'exact_metadata_preparation_failed', 'error_type': type(error).__name__}))
        sys.exit(1)
