# V3 output sanity snapshot

Offline inspection on 2026-09-07 of the completed v3 smoke and pilot, restricted
to the dump directories named by their manifests. Both manifests identify
evaluation source `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`.
Serving configuration and Slurm job `1203299` were not changed. No model API
requests, probes, GPU jobs, or restarts were performed for this audit.

## Result

| Scope | Successful response choices | `[PAD]` content / reasoning occurrences | `<\|media_pad\|>` content / reasoning occurrences | Empty content | Nonempty reasoning field |
| --- | ---: | ---: | ---: | ---: | ---: |
| smoke_v3 | 146 | 0 / 0 | 0 / 0 | 0 | 4 |
| pilot_v3 | 1,193 | 0 / 0 | 0 / 0 | 0 | 21 |
| Combined | 1,339 | 0 / 0 | 0 / 0 | 0 | 25 |

There were no unsupported content types, missing response choices, input-scope
errors, or duplicate response identities in this snapshot. Empty content means
missing, null, empty, or whitespace-only textual content; tool-call count and
finish reason are retained so that a future tool-only response is not
automatically interpreted as a serving failure.

Only `response_json.choices[*].message.content` and `reasoning_content` were
scanned. Request history and `response_raw` were not scanned, so repeated
assistant history and the second serialization of the same HTTP response do
not multiply the counts. Unique identity is `(request_id, attempt, choice.index)`.
Copied/promoted identities are counted once when multiple manifests are supplied;
conflicting response contents under the same identity are reported as errors.

The scope is not the currently running full_v3. The smoke finished at
`2026-09-07T10:30:26.192139+00:00`; the pilot finished at
`2026-09-07T10:43:27.127730+00:00`. Manifest and progress file hashes are recorded
in [summary.json](summary.json), together with counts for all 51 manifest jobs.

## Token identity and limits

Checkpoint root:

```text
/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Kimi-K3
```

- `[PAD]`, token ID **163839**, is the actual configured sequence-padding token:
  `tokenizer_config.json:123–129,148`, `config.json:17,195`.
- `<|media_pad|>`, token ID **163605**, is a separate media-feature placeholder:
  `tokenizer_config.json:99–105`, `config.json:15`,
  `kimi_k3_vision_processing.py:54–57`. It is reported separately and must not be
  equated with sequence or KV-cache padding.
- `<|reserved_special_token_250|>` appears only in an old docstring
  (`tokenization_kimi.py:39`). The actual constructor uses the configured pad
  token (`:71,123,147`); this string is not a PAD alias and was not guessed into
  the scan. Generic `<|reserved_token_ID|>` names (`:99–104`) are not padding
  aliases either. Image-preprocessor placeholders without a padding role were
  not classified as PAD.

Source hashes and exact scanned marker definitions are in `summary.json`.
This is a literal scan of decoded text, not an inspection of generated token
IDs. The tokenizer allows special-token spellings to be handled as structural
tokens or ordinary text (`tokenization_kimi.py:173–183`), so a hypothetical hit
could also be a quoted literal. **Zero marker matches does not prove the
absence of all KV-cache, numerical, semantic, or protocol errors.** The generic
KV-padding backport's previously documented coverage limits still apply.

Nonempty parsed reasoning fields remain possible with requested
`thinking=false`; they are not padding indicators. See the separate
[reasoning-mode diagnostic](../../REASONING_MODE_DIAGNOSTIC.md). Its earlier
136-request smoke statistics are a different run, not this v3 snapshot.

## Auditable response inventory

`inventory/<manifest-run-namespace>/<job-id>.jsonl` contains all **1,339** unique
response-choice records, partitioned into **51** manifest job files. Every
record preserves case ID, generation/response ID, original context, exact dump
path, dump SHA-256, response-choice SHA-256, content/reasoning hashes and lengths,
finish reason, tool-call count, and marker findings. No response text is copied
into clean records; original full responses remain available at their dump paths.
If markers are found, their field, exact tag, count, offsets, and a short local
excerpt are included.

The SHA-256 of canonical inventory lines, joined in manifest/job/dump/choice
order with newline separators and no final newline, is:

```text
b507ad66ffd9ad9d9239ea2a45d6199d1e0ce5b94bf21ff2080106c771d45310
```

This was independently recomputed from the saved inventory and matched the
scanner summary. Per-job dump-file inventories also have hashes in the summary.

## Repeat after full_v3 finishes

The scanner is [output_sanity_scan.py](../../output_sanity_scan.py), standard
library only. It reads saved files and prints JSON to stdout without writing
files or contacting a service:

```bash
python3 /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/output_sanity_scan.py \
  --manifest /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/full_v3/manifest.json
```

Use the full manifest alone: promoted pilot dumps already reside in its defined
dump directories. Add `--inventory` to print all per-choice JSONL evidence;
optionally add `--job-id JOB_ID` to partition that inventory. The default command
refuses an unfinished progress snapshot. `--allow-incomplete` is available only
when an explicitly partial snapshot is wanted and labels completeness false.

To reproduce this snapshot's exact scope:

```bash
python3 /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/output_sanity_scan.py \
  --manifest /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/smoke_v3/manifest.json \
  --manifest /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/runs/pilot_v3/manifest.json
```

[Eight offline tests](offline_tests.log) passed, covering exact checkpoint
token identity, ignored request history, per-field and per-marker counting,
empty/tool-only responses, whitespace, copied-response deduplication,
unfinished-run gating, and unsupported content types. Re-run them with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/test_output_sanity_scan.py
```
