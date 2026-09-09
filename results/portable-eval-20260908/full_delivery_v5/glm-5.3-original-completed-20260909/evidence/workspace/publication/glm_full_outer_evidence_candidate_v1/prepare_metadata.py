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
OUT = P / 'glm_full_outer_evidence_candidate_v1'
LEAF = 'results/portable-eval-20260908/full_delivery_v5/glm-5.3-original-completed-20260909'
R = P / 'glm_formal_original_local_delivery_v1'
S = P / 'glm_formal_original_scan_v1'
C = P / 'glm_controls_local_delivery_v2'
groups = {}

def add(group, root, names):
    groups.setdefault(group, []).extend(root / name for name in names)

for i in range(1, 37):
    b = 'batch-%06d' % i
    add('raw_batch_proofs', R / 'batches' / b, [
        'RESULT.json', 'WHOLE_FILE_COMPARISON.json', 'restore/COMPLETE.json',
        'pack.started.json', 'pack.exit.json', 'pack.stdout.json', 'pack.stderr.log',
        'restore.started.json', 'restore.exit.json', 'restore.stdout.json', 'restore.stderr.log'])
    add('raw_scan_outputs', S, ['specs/' + b + '.json', b + '/manifest.json',
        b + '/lock.json', b + '.status.json', b + '.receipt.json'])
    add('raw_scope_candidates', P / 'glm_formal_original_scope_candidate_v1/candidate',
        ['batches/' + b + '.candidate.json'])
add('raw_run_operator_metadata', R, ['PREFLIGHT.json', 'STARTED.json', 'SUMMARY.json'])
add('raw_scan_outputs', S, ['PREPARED.json', 'SCAN_RECEIPT.json'])
add('raw_scan_controls', P, [
    'glm_formal_original_scope_candidate_v1/ROOT_SCAN_GO.json',
    'glm_formal_original_delivery_candidate_v1/ROOT_METADATA_GATE_ACCEPTANCE.json',
    'glm_formal_original_delivery_candidate_v1/ACTUAL_METADATA_GATE_v2.json'])
add('preserved_metadata_preflight_failure', P / 'glm_formal_original_delivery_candidate_v1',
    ['ACTUAL_METADATA_GATE.json'])
add('raw_scope_candidates', P / 'glm_formal_original_scope_candidate_v1/candidate',
    ['inventory.json', 'ASSEMBLY_RECEIPT.candidate.json', 'batches/INDEX.candidate.json'])
add('raw_root_proofs', R, ['ROOT_OPERATOR_COMPLETION.json', 'ROOT_LOCAL_PROOF.json'])
add('raw_pack_go', P / 'glm_formal_original_delivery_candidate_v1', ['ROOT_DELIVERY_GO.json'])
add('controls_scan_metadata', P, [
    'glm_controls_scan_v2/lock.json', 'glm_controls_scan_v2/manifest.json',
    'glm_controls_public_batches_v2/ROOT_SCAN_SPEC.json',
    'glm_controls_public_batches_v2/ROOT_SCAN_ACCEPTANCE.json'])
add('controls_public_scope', OP / 'glm_public_controls_subset_v1',
    ['ROOT_SCOPE_DECISION.json', 'inventory.json'])
add('controls_byte_verification', P / 'glm_controls_local_verification_v2',
    ['verify.py', 'ACTUAL_BYTE_VERIFICATION.json', 'CLI_RECEIPT.json', 'README.md'])
add('controls_local_proofs', C, ['ROOT_LOCAL_PROOF.json', 'OPERATOR_COMPLETION.json',
    'ROOT_PACK_GO.json', 'ROOT_RESTORE_GO.json', 'restore/COMPLETE.json'])
add('frozen_practical_code', P / 'glm_formal_original_delivery_candidate_v1',
    ['operator.py', 'README.zh.md', 'PRODUCTION_DIFF.patch', 'CPU_RECEIPT.json', 'CPU_ADDENDUM.zh.md'])
add('frozen_practical_code', P, ['restart_v5_closed_local_delivery_v1/operator.py',
    'pinned_batches_scan_candidate_v1/scan_batches.py', 'full_scope_batch_candidate_v1/prepare.py'])
add('frozen_practical_code', P / 'glm_formal_collection_assembly_candidate_v2',
    ['assemble.py', 'README.zh.md', 'PRODUCTION_DIFF.patch', 'CPU_RECEIPT.json'])
add('closed_selection_evidence', P / 'glm_full_collection_selection_candidate_v1',
    ['verify_selection.py', 'CLOSED_METADATA_REVIEW.json', 'CLI_RECEIPT.json', 'README.result.md',
     'GUARD_SELFTEST_FIRST_FAILURE.json', 'README.plan.md', 'SELECTION_CANDIDATE.json', 'ACTUAL.stdout.json'])
add('closed_selection_peer_review', P / 'glm_full_collection_selection_peer_v1', ['README.zh.md'])
add('assembly_selection_and_proofs', P / 'glm_full_collection_assembly_v1',
    ['ROOT_SELECTION.json', 'ROOT_ASSEMBLY_GO.json', 'ROOT_OPERATOR_COMPLETION.json',
     'ROOT_LOCAL_PROOF.json', 'ROOT_VERIFY.py'])

PINS = {
 R / 'SUMMARY.json': '1b717138400e03811d69df4f15a95804def484cf83884037c62629870ab1a5e3',
 R / 'ROOT_OPERATOR_COMPLETION.json': 'fae187007ea6ad13d6abd4533273df3b8dcd3f9d20bc1fd3551049f3ea41a5a5',
 R / 'ROOT_LOCAL_PROOF.json': '4733365f0e78ac461c920c4db6af4fc699993217b1141244e29af6e0f878fb7e',
 S / 'PREPARED.json': '2a3286328e1951fa41b3233e477a01a0fdcb57ccecd01d64cd373c831c9e6375',
 S / 'SCAN_RECEIPT.json': '7d2610f3489c430dd15ee0d3c597d884a518a4c7ca8f48cba6d3a983f6c52727',
 P / 'glm_formal_original_scope_candidate_v1/ROOT_SCAN_GO.json': 'e68c1d901b3cfee210cdde318fd72b765993984efd828bb9cde3e4a7be28b1b6',
 P / 'glm_formal_original_delivery_candidate_v1/ROOT_METADATA_GATE_ACCEPTANCE.json': '8ff776e9af76f879ba6bc36f4fa2b174e16cbb64c9ba47bc3ddd8c3305173b0f',
 P / 'glm_formal_original_delivery_candidate_v1/ACTUAL_METADATA_GATE_v2.json': '3c7c5ffa19904c086155b12b0dfb75539f137151a7df8010ccae48513846cda3',
 P / 'glm_formal_original_delivery_candidate_v1/ACTUAL_METADATA_GATE.json': 'aaf7741f0ea2b283666a6964d90890467157456e2cffa9471869f8590a55d984',
 P / 'glm_formal_original_scope_candidate_v1/candidate/inventory.json': '78610fabac42cf3606dca00a19a3148647eb9eaa413843658bc38f504ec47489',
 P / 'glm_formal_original_scope_candidate_v1/candidate/batches/INDEX.candidate.json': '843ee297489da15af9976a65d0ba97f12b634153320bf863e49ceb40049fe5b5',
 P / 'glm_formal_original_scope_candidate_v1/candidate/ASSEMBLY_RECEIPT.candidate.json': '6ed17c05328fd97687370bde8fd1e73f6906f85b3521474999a534dbbe5533bf',
 P / 'glm_formal_original_delivery_candidate_v1/ROOT_DELIVERY_GO.json': 'b8ddb4452b2214aee9fae013ce016bd23a953b5eae737508003bf0dca5d0fce5',
 P / 'glm_controls_scan_v2/lock.json': '0bff9a91e9b05103f8f9863f161e828b2f68be254a5be2aa21750d3d7fc42c6c',
 P / 'glm_controls_scan_v2/manifest.json': 'a474a0cf306e11bdc5a0e6b76ca544f1ced61099b9c69c3bc07d374d8101880e',
 P / 'glm_controls_public_batches_v2/ROOT_SCAN_SPEC.json': '492917fe8faba5c3b5f572af537227e86dce051d06be4645069d5b7dfd149f1e',
 P / 'glm_controls_public_batches_v2/ROOT_SCAN_ACCEPTANCE.json': '82e7e9e040fb2d581af44ffc4eb089095d629751bdb34ff343e5108bbc071bae',
 OP / 'glm_public_controls_subset_v1/ROOT_SCOPE_DECISION.json': '90df6e9b1301211278c290676c7ee387398c487a527c2df6851a5a0146f473c3',
 OP / 'glm_public_controls_subset_v1/inventory.json': '3c321f8bbecba16cb3570bd6be04ccdc3956fdf857ed8dbb669becdd9a66726a',
 P / 'glm_controls_local_verification_v2/verify.py': 'c0fabf8dc9c9c06352073a9048f504bc46a17897f73cf8f1a98b47e9bbe5b5e5',
 P / 'glm_controls_local_verification_v2/ACTUAL_BYTE_VERIFICATION.json': 'ef89fafeec3ef9d64015ac6a7401325ea03848442664e74923df5d14e8f2e16f',
 P / 'glm_controls_local_verification_v2/CLI_RECEIPT.json': 'c22570b27dbd31b8b2d516a51309f27ad8499686fae52f10c62e96e5566b930c',
 P / 'glm_controls_local_verification_v2/README.md': 'b771356fe2026db1b3c1517e65f7a321679b2931acb6b63564d9c6637c21048c',
 C / 'ROOT_LOCAL_PROOF.json': '4ef732ce297aaf31c948e6a8ba7f114e67d4143586ab165615a3caee488adebe',
 C / 'OPERATOR_COMPLETION.json': '1551eb73c38405d8b4247fdf200d44a0e94aa8bd7c93dedd6fdd51511e9f6dc5',
 C / 'ROOT_PACK_GO.json': '8d0746f7f3cefc9ad0ee2865523f96b7805b4f8ea462bf9c83e761ab1065f002',
 C / 'ROOT_RESTORE_GO.json': '3c3f78560b3a9acf50bd748de49cfbf075bd4af068af313285ef2d174fb53208',
 C / 'restore/COMPLETE.json': 'f9641d26f870b250687a804571c6463aa3806be55627b7fadf4e3be6568f482d',
 P / 'glm_formal_original_delivery_candidate_v1/operator.py': '2124e9929f29531d48960ece983eea10d493660244bfc1dc8938696ebfd79d3d',
 P / 'glm_formal_original_delivery_candidate_v1/README.zh.md': 'aabf86631f7aea618f4b7a02dbda13972b004a7aa9fd3ce70f0675afce12520b',
 P / 'glm_formal_original_delivery_candidate_v1/PRODUCTION_DIFF.patch': '2b7d075f9e5ff32e2d51bb5038f9f59546066e7012686c041684b7957990a4be',
 P / 'glm_formal_original_delivery_candidate_v1/CPU_RECEIPT.json': '9a819e7d19ee20eb3be3ce27d3987eb7ec9afa5ca268c21e497f191cd5793404',
 P / 'glm_formal_original_delivery_candidate_v1/CPU_ADDENDUM.zh.md': '2b8b4078cc7ac08c274577911be1b2e66275d2877ff521728ac51957b0eeac11',
 P / 'restart_v5_closed_local_delivery_v1/operator.py': '979fd024d739eb927825d156048cbd6a1850fb27ddc6a5c5677abba1e4d7d497',
 P / 'pinned_batches_scan_candidate_v1/scan_batches.py': '5b3dbdf84f789dec731a3f8c821c2981a0f00e61f4b951141e022fab491b568b',
 P / 'full_scope_batch_candidate_v1/prepare.py': '77a69230c7ef2fd9de1767c63d237f8514411372ce10eac902d71b1d2af65c60',
 P / 'glm_formal_collection_assembly_candidate_v2/assemble.py': '5255f2f390632bd9686ce379f0868fac8ddddc0e8c2304000ee017f236d6f9f6',
 P / 'glm_formal_collection_assembly_candidate_v2/README.zh.md': '3248de8e8c29034bb5d7a49b7bd9a8d97fe3b2eedc14a8ee2f97a4c7c30da0ca',
 P / 'glm_formal_collection_assembly_candidate_v2/PRODUCTION_DIFF.patch': 'c47d1d552cc8060451fcb3c4f9e0437e05001b4764f8a1723afb5740f29fae96',
 P / 'glm_formal_collection_assembly_candidate_v2/CPU_RECEIPT.json': 'c3ac9c8bcf1f92cfcf6ceccf2fba8256e1ea5182ea2f375801c905fab4214762',
 P / 'glm_full_collection_selection_candidate_v1/verify_selection.py': '8c126bd89f744ec6c4c48bfd51301711b018025a55d2717f0ca3711cd73688ae',
 P / 'glm_full_collection_selection_candidate_v1/CLOSED_METADATA_REVIEW.json': '1d2c1eb31c6507991705e97a24c39250b2436c1232e4aefa15936288c8f77b08',
 P / 'glm_full_collection_selection_candidate_v1/CLI_RECEIPT.json': '6ab9fca2b71bfa39b3bc021512b63b633c200d400ec32b8074088e15ac4ece4c',
 P / 'glm_full_collection_selection_candidate_v1/README.result.md': 'b6f664d2ea4a007a24d709792832dda3a6332cd6d53e7c2e586a5254e47f97c7',
 P / 'glm_full_collection_selection_candidate_v1/GUARD_SELFTEST_FIRST_FAILURE.json': '7c1c13469bccea93906cfea1ce4211950669bbd989e9b5d10277d99dee88e4ce',
 P / 'glm_full_collection_selection_candidate_v1/README.plan.md': 'd03e614b2dca0439d4fb3c1151a39aa3f5bfbf31554f7a3a63a8a1130448df75',
 P / 'glm_full_collection_selection_candidate_v1/SELECTION_CANDIDATE.json': 'fcbf3570d94d72340165ca08f6c67f9f58b94b4835126dbd32ecabccd8a4e12a',
 P / 'glm_full_collection_selection_candidate_v1/ACTUAL.stdout.json': 'ec55ef6741dd47d68d1454792c9d9ada12949d8d291204fceb3df7d2c4e849db',
 P / 'glm_full_collection_selection_peer_v1/README.zh.md': 'cdaf03e8f796036adf851cd9ffa8f2f409c5a391fb27275ff638aa441d3c5282',
 P / 'glm_full_collection_assembly_v1/ROOT_SELECTION.json': '24d92d89090191de7ff857b55fc70a15166ec4c0195dd584d4e121c6b0486d4b',
 P / 'glm_full_collection_assembly_v1/ROOT_ASSEMBLY_GO.json': 'fee5f95e3fadded369a8e3e97bd4386b5a93ac5c33f84dd7278dbc5120ffd20c',
 P / 'glm_full_collection_assembly_v1/ROOT_OPERATOR_COMPLETION.json': '863454515473aa069a4f3e7b7f11c21a632ab5e8a0a8b7e4a4357ddd1f15c950',
 P / 'glm_full_collection_assembly_v1/ROOT_LOCAL_PROOF.json': '9f7bfd1346f98c82e31a92c2a3ff6aa8260e732ff4976187a010868f149e040c',
 P / 'glm_full_collection_assembly_v1/ROOT_VERIFY.py': 'cff97af78f68ba98278de2c28c9a5a16968514728c5bd2952533ee3a6098645c',
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
    need(len(paths) == 668 and len({p for p, g in paths}) == 668, 'exact_scope_or_duplicate')
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
    manifest = {'schema': 'glm-formal-outer-evidence-files-candidate-v1', 'candidate': True, 'approved': False,
        'workspace': str(W), 'leaf': LEAF, 'file_count': len(rows), 'total_bytes': sum(r['bytes'] for r in rows),
        'original_execution_complete': True, 'original_score_complete': True,
        'copy_performed': False, 'content_scan_performed': False, 'publication_performed': False, 'files': rows}
    ref = write_new('FILES.candidate.json', manifest)
    counts = {g: {'files': len(ps), 'bytes': sum(r['bytes'] for r in rows if r['group'] == g)} for g, ps in groups.items()}
    receipt = {'schema': 'glm-formal-outer-evidence-hash-receipt-v1', 'candidate_only': True, 'approved': False,
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
