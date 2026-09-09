# GLM public-controls local byte verification v2

This directory is a narrow, independent integrity check of the already completed public-controls local restore. It is not an experiment analysis, a new scanner, another restore, publication, or final project acceptance.

## Accepted input boundary

- Public subset inventory: 1,114 originals, 224,903,100 bytes; SHA256 `3c321f8bbecba16cb3570bd6be04ccdc3956fdf857ed8dbb669becdd9a66726a`.
- The one explicitly approved nonexperimental `seal_operator_glm_formal_v1/invocation.json` omission stays omitted; no original payload was rewritten and no failed scan was relabeled.
- Original source reads are restricted to that exact whitelist. No broad source-tree enumeration or payload interpretation was performed.
- Only bundle and restore trees under `glm_controls_local_delivery_v2` are inspected; no active raw delivery, key file, network, or Git access.

## Procedure and actual result

`verify.py` is a fixed-scope, standard-library-only verifier. It does not import or invoke frozen common/restore/scanner modules. It hash-pins the original common/restore source and reconstructs their canonical COMPLETE metadata in memory.

The single authorized actual CLI was:

```text
/usr/bin/prlimit --core=0:0 -- /usr/bin/python3 -B /lustrefs/users/chufan.shi/codex_space_tn/publication/glm_controls_local_verification_v2/verify.py
```

It completed with actual exit 0: own session 18021, start chunk c7b70a, exit chunk 7fa466. `ACTUAL_BYTE_VERIFICATION.json` is its unmodified stdout, and `CLI_RECEIPT.json` records process provenance and review.

Every source original and restored counterpart was fully streamed and matched by path, byte count, and SHA256. Five compressed archive files and their member metadata were verified without decompression. The exact member union equals the input inventory.

The whole restore wrapper has 1,115 files (1,114 originals plus COMPLETE.json) and 91 directories including its root. The bundle wrapper has 13 files and 4 directories including its root. Both entire file sets and ancestor-directory sets were equal before/after; extra empty directories are also rejected.

For all 2,247 byte-read files (including metadata/tools/archives), the check compares lstat before, opened fstat, final fstat, and immediate lstat, then performs a final fixed-snapshot lstat pass. Source and restored modes/owners/timestamps need not equal each other; each individual file must remain stable. This is one full byte-hash pass, not two. POSIX modes/timestamps/ownership preservation by the restore is explicitly not claimed.

## Review and preserved boundaries

The peer `archive_contract` statically read the complete frozen verifier and original completion contracts. Its sole conditional concern—duplicate preloaded paths in the original whitelist—was resolved by a metadata-only empty-intersection check (9163fc exit 0), before the actual verifier ran.

The verifier produces stdout only. This script, exact stdout evidence, and process receipt were added solely with apply_patch. No pack/restore/scan or child process was launched by the verifier. ROOT's final acceptance and operator receipt are separate responsibilities.
