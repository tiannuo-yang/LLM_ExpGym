# Full v3 final output sanity

Read-only audit on 2026-09-07, after all 342 jobs and the verified-resume pass
completed. Scope is **only the full_v3 manifest's dump directories**, including
the original-byte pilot dumps already promoted into that namespace. Smoke,
standalone pilot, request histories, and serving probes were not counted.
No API requests, GPU jobs, restarts, source edits, or data changes were made.

## Results

| Check | Full v3 result |
| --- | ---: |
| Manifest jobs complete / failed | 342 / 0 |
| Unique successful response choices | 9,068 |
| Actual `[PAD]` occurrences in content / reasoning | 0 / 0 |
| Media placeholder `<\|media_pad\|>` occurrences in content / reasoning | 0 / 0 |
| Empty, missing, null, or whitespace-only content | 0 |
| Unsupported output field types / missing response choices | 0 / 0 |
| Duplicate identities skipped / conflicting identities | 0 / 0 |
| Nonempty server-parsed reasoning fields | 170 |
| `finish_reason=stop` / `finish_reason=length` | 9,064 / 4 |

The four output-limit completions are listed with IDs, context, and hashes in
[length_finish_cases.json](length_finish_cases.json). They are not padding or
empty-content findings and are not HTTP failures, but should not be described
as untruncated answers. Reasoning fields remain possible under requested
`thinking=false`; see the [reasoning-mode diagnostic](../../REASONING_MODE_DIAGNOSTIC.md).

## Evidence and identity

- [summary.json](summary.json) records aggregate/per-job counts, exact marker
  definitions, checkpoint/source hashes, manifest/progress hashes, and limits.
- `inventory/full-full_v3-ad4275b6/<job-id>.jsonl` contains **9,068** response-choice
  records in **342** job files. Every case preserves request/attempt/choice ID,
  original context and dump path, dump and response-choice SHA-256, field hashes
  and lengths, finish reason, and tool-call count. Full text remains in the
  referenced original dump.
- [inventory_verification.json](inventory_verification.json) confirms the saved
  inventory matches the scan summary, all 9,068 IDs are unique, and every record
  has context. The inventory digest is
  `7a72a2482165d9463637b5a68e74a9ab54e13363dc3817c448a5a1c3a274390a`.

The manifest SHA-256 is
`7016deb285696ff95c0aa970088c0580d0daf60cb0c6695ce8515e0fe85df854`;
evaluation source is
`c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`.
The observed progress snapshot records the completed verified-resume invocation
at `2026-09-07T11:52:28.704143+00:00` with all 342 jobs complete. This is not a new
generation pass; the scanner reads the existing full-stage responses once.

## Interpretation limits

`[PAD]` is the checkpoint's configured padding token, ID **163839**
(`tokenizer_config.json:123–129,148`, `config.json:17,195`).
`<|media_pad|>` is a distinct image-feature placeholder, ID **163605**
(`tokenizer_config.json:99–105`, `kimi_k3_vision_processing.py:54–57`), and is
counted separately. The stale docstring string
`<|reserved_special_token_250|>` is not the configured PAD and was not treated
as an alias.

Only `response_json.choices[*].message.content` and `reasoning_content` are
scanned. Request history and `response_raw` are excluded to avoid repeated
counting. Identity is `(request_id, attempt, choice.index)`. This is decoded-text
inspection, not inspection of generated token IDs: a hypothetical match could
also be quoted ordinary text. **Zero marker matches does not establish that
all KV-cache, numerical, semantic, or protocol errors are absent.** This audit
does not replace the benchmark's integrity audit or verify answer correctness.

## Reproduce

The unchanged scanner SHA-256 is
`ac01ae8f4c0288d6db597fb0296f6a0d8a0ad2780ebde0e68308398df5988d6a`.
It is standard-library-only, writes no files, makes no network calls, and
prints the summary to stdout:

```bash
python3 /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/output_sanity_scan.py \
  --manifest /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/full_v3/manifest.json
```

Add `--inventory` for all response records, or also `--job-id JOB_ID` for a
single partition. The same scanner previously passed all
[eight offline fixture tests](../v3_output_sanity_snapshot/offline_tests.log).
