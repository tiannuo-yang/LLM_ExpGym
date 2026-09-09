# GLM 37-bundle collection selection: pending candidate plan

Status: design only; approved=false. No selection rows have been assembled, no final SUMMARY has been read, and no collection assembler has been run. This document does not authorize any operation.

## Frozen reuse contract

Use the existing `publication/glm_formal_collection_assembly_candidate_v2/assemble.py` unchanged:

- SHA256: `5255f2f390632bd9686ce379f0868fac8ddddc0e8c2304000ee017f236d6f9f6`
- Bytes: 13368
- ROOT candidate acceptance SHA256: `2b7bb0850a515bf8e00e8e4cbe294d11e7a2f44def47de467070a27d3405a458`
- Raw scope: 36 bundles, 70,520 original files, 3,242,213,793 original bytes.
- Controls scope: one bundle, 1,114 original files, 224,903,100 original bytes.
- Total: 37 bundles, 71,634 original files, 3,467,116,893 original bytes.
- Raw IDs: batch-000001 through batch-000036; first 35 contain 2,000 originals each, last contains 520.
- Raw category: original-completed. Original execution_complete and score_complete are both true.
- Raw bundle roots: `publication/glm_formal_original_local_delivery_v1/batches/<batch-id>/bundle`.
- Controls bundle root: `publication/glm_controls_local_delivery_v2/bundle`.

Controls operator/proof pins remain:

- `OPERATOR_COMPLETION.json`: `1551eb73c38405d8b4247fdf200d44a0e94aa8bd7c93dedd6fdd51511e9f6dc5`.
- `ROOT_LOCAL_PROOF.json`: `4ef732ce297aaf31c948e6a8ba7f114e67d4143586ab165615a3caee488adebe`.
- INDEX: `4356b1cab3762da71202d5e4ce3ddc909dd08e06b531823d6940e9c91660cf26`.
- Bundle COMPLETE: `6ab714cd95c3cb5e46e452b902c036ca826873364c4f22e08254a3b49a0bdcc4`.
- Public subset inventory: `3c321f8bbecba16cb3570bd6be04ccdc3956fdf857ed8dbb669becdd9a66726a`.

The approved omission of one nonexperimental invocation.json is unchanged. No additional exclusion, replacement, rescoring, or invented proof is permitted.

## Monitoring and closure gate

ROOT remains sole owner of raw operator session 13206. This agent never calls write_stdin on it.

While running, inspect only SUMMARY existence and regular per-batch RESULT.json markers, no more than once per minute. As an additional conservative boundary, read a RESULT only after its mtime is at least 60 seconds old and require stable before/after stat. Do not read other active-run files, raw payloads, archives, restore payloads, logs, key files or key paths. Report changed batch milestones, not per-file output.

SUMMARY existence is an alert only. Wait for ROOT's independently observed actual process exit evidence before reading SUMMARY or creating selection rows. A completed batch is not a completed entire run; the operator performs another final cross-batch source/restore and completion check before SUMMARY.

## Metadata-only verification after ROOT actual exit 0

Without importing production modules or invoking their functions:

1. Pin the closed SUMMARY, all 36 RESULT objects, all 36 WHOLE_FILE_COMPARISON objects, all 72 pack/restore exit receipts, and their declared metadata references using exact bytes/SHA and stable before/after stat. Do not read started receipts containing argv or key-file paths.
2. Require the exact 36 sequential batch IDs, passed=true for every batch, 70,520 files / 3,242,213,793 bytes, no unstarted batches, stable metadata, final complete source/restore path-byte-SHA flag=true, original true/true status, no unresolved PIDs and local_workers=0.
3. Require exactly 72 children and exactly one pack plus one restore for every batch. Validate real integer exit_code=0, confirmed_reaped=true, closure_evidence=wait, positive bounded wait_attempts, no poll fallback or wait exceptions/failure layers for the clean pass. Cross-bind each child to the batch work path and exact exit receipt PID/stage/status; no process liveness inference from a missing PID.
4. Compare each on-disk RESULT with its SUMMARY projection, allowing only the known added retained_child_exit_refs field. Verify each retained exit ref matches its actual closed receipt. Validate whole_originals_and_restored_verified and each comparison's all_source_and_restored_bytes_sha_match/full_restored_path_set_equal flags.
5. Validate each comparison row as a unique path / exact-int bytes / SHA256 tuple, enforce per-batch counts and bytes and global raw totals/unique path union. Compare with already accepted source-scope metadata if needed using metadata only; no new original byte hash.
6. Validate each bundle INDEX and bundle/restore COMPLETE metadata ref pins and canonical completion bindings. Member-index pages may be read as metadata to compare their union to the whole-file comparison rows. Compressed archives and original/restored payloads are not read or rehashed in this candidate stage.
7. Re-pin the closed controls operator/proof and its named metadata refs. Require their actual pack/restore exits and complete byte-proof booleans, exact 1,114 / 224,903,100, and the unchanged controls omission policy.
8. Final fixed-snapshot stat/ref recheck; never append to a ledger being iterated. Preserve any counterexample without retry or rewriting historical output.

The metadata selection review does not substitute for the already completed original byte comparisons. It projects and binds their real proofs; later original assembly performs its own frozen bundle copy/integrity work only after a separate ROOT GO.

## Exact selection representation

The original select() accepts only eight top-level fields: schema, issuer, original_execution_complete, original_score_complete, bundle_count, file_count, original_bytes, bundles. It rejects an added approved field.

Therefore an unapproved candidate should be stored inside a separate envelope with approved=false and proposed_selection containing the exact eight-field ROOT-shaped proposal. This envelope is not a directly consumable selection or GO. ROOT alone may review and extract/adopt the exact proposed selection into a separately authorized file; no production schema is modified to accept candidate flags.

Each of the 37 proposed rows has exactly ten fields:

- bundle_id, category, bundle_root;
- index_ref, complete_ref;
- file_count, original_bytes;
- operator_ref, local_proof_ref, local_verification.

All refs have exactly absolute path, bytes, sha256. For raw rows, operator_ref is the exact closed batch RESULT.json and local_proof_ref is its exact WHOLE_FILE_COMPARISON.json. The separate candidate verification receipt pins final SUMMARY and ROOT's actual exit evidence; the selection row is not used to hide final closure dependencies. For controls, operator_ref and local_proof_ref are the existing ROOT operator/proof above.

local_verification contains exactly four fields: integer pack_exit_code=0, integer restore_exit_code=0, complete_original_and_restored_path_bytes_sha_match=true, all_started_children_reaped=true. These values must be derived from the verified real proofs, not generated from expected outcomes.

No new reusable proof framework or replacement operator is needed. The eventual metadata builder is a bounded one-shot projection of these fixed closed inputs into the candidate envelope and receipt.

## Later ROOT-only assembly authorization

No GO or actual output is created by this plan. After review, the existing CLI is:

```text
/usr/bin/prlimit --core=0:0 -- /usr/bin/python3 -B /lustrefs/users/chufan.shi/codex_space_tn/publication/glm_formal_collection_assembly_candidate_v2/assemble.py
  --go /ABS/ROOT_GO.json --go-sha256 EXTERNAL_GO_SHA
  --output-dir /ABS/FRESH_OUTER/payload
```

The original nine-field GO schema is unchanged: schema=root-glm-collection-assembly-go-v1, issuer=ROOT, approved=true, action=assemble_local_only, assembler_sha256, selection_ref, output_dir, publication_authorized=false, network_authorized=false.

The frozen assembler calls content-validation helpers while it verifies/copies existing bundles. This plan does not invoke it; "no new pack/restore" is not the same as "metadata-only assembly." Actual assembler execution requires ROOT's later GO.
