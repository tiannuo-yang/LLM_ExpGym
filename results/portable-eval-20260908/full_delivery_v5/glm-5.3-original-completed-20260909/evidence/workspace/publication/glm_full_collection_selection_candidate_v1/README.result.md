# GLM closed metadata verification and 37-bundle selection candidate

The single authorized real metadata verification passed: session 65434, start chunk 6f6508, actual exit 0 at cded6e; reaped. Original raw operator session 13206 was owned only by ROOT and had already naturally exited 0 at 895e99.

This is an **unapproved candidate**, not an assembly GO or publication result. ROOT_LOCAL_PROOF for the raw delivery remains pending ROOT acceptance. No archive/original/restored payload bytes were read by this checker, no scanner/pack/restore/assembler was invoked, and no key file was statted or read.

## Verified scope

- 36 raw bundles: 70,520 originals / 3,242,213,793 B.
- One unchanged public-controls bundle: 1,114 originals / 224,903,100 B.
- Total selection: 37 bundles / 71,634 originals / 3,467,116,893 B.
- Actual archive counts from the pinned indexes: 283 raw + 5 controls = 288. This is not a publisher scan result.
- All 72 child exit receipts matched the SUMMARY and per-batch results: actual integer exit 0, confirmed reaped, one natural wait each, no poll fallback, wait exception, or failure layer.
- All 36 comparison row sets matched the accepted raw inventory exactly and were globally disjoint from controls.
- All 37 INDEX files, 288 member-index pages, SOURCE_SCAN metadata, and bundle/restore COMPLETE bindings matched their actual bytes/SHA refs and canonical inventories.
- All 594 read metadata/tool refs passed two full metadata hash passes with stable exact stat values. No original experimental bytes were rehashed.

Archive SHA/byte entries themselves were checked as declared metadata, not by re-reading tar.gz. The actual original byte integrity proof comes from the just-completed frozen original operator's full final check, plus the previous independently accepted controls byte verifier.

## Files

- `SELECTION_CANDIDATE.json`: canonical approved=false envelope containing the exact original eight-field proposed selection. ROOT must separately adopt/extract it and issue a new exact GO.
- `CLOSED_METADATA_REVIEW.json`: detailed scope, closure, metadata digest and per-batch review.
- `ACTUAL.stdout.json`: unchanged stdout of the real verifier; read back and compared verbatim to the tool result.
- `CLI_RECEIPT.json`: actual process evidence and preserved checks.
- `verify_selection.py`: fixed-scope standard-library verifier, no production imports and stdout only.

The candidate's canonical SHA256 is fcbf3570d94d72340165ca08f6c67f9f58b94b4835126dbd32ecabccd8a4e12a. The review SHA256 is 1d2c1eb31c6507991705e97a24c39250b2436c1232e4aefa15936288c8f77b08.

## Honest failure and boundary record

The pure in-memory precheck first failed on the path "." because PurePosixPath gives it empty parts. The new verifier was corrected before any actual main execution; all 23 pure guards then passed. The first failure is retained in `GUARD_SELFTEST_FIRST_FAILURE.json`. No original frozen tool changed.

A later saved-file check failed only when reverse-reconstructing the pre-fix script: it initially omitted restoring the redundant final newline normalized by apply_patch. The candidate SHA assertion had already passed. A corrected metadata-only diagnostic confirmed the exact old SHA after reversing the one guard change and restoring that newline. The actual metadata verifier was not rerun.

The public nonexperimental invocation.json omission is unchanged; the original failed scan and private original remain preserved. The public internal audit-reference chain is not claimed completely self-contained. The original 3-key scan records are unchanged; the future fourth outgoing key was not accessed or applied here.

The accepted ROOT actual-exit receipt contains command-line key-file path strings. Its metadata was read under the explicit proof scope; no key file was accessed, and the command body was not copied into the candidate.

