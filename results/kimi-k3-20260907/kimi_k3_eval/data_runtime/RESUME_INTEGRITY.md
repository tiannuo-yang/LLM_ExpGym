`resume_integrity.py` is independent of the experiment runners. It only reads the supplied manifest and monitored files, then creates a new report. It does not import the harness, execute resume, or contact a model.

After every full_v2 job has finished, take the baseline from `kimi_k3_eval/`:

```bash
../LLM_ExpGym/.venv/bin/python data_runtime/resume_integrity.py snapshot \
  --manifest runs/full_v2/manifest.json \
  --report reports/resume_full_v2.before.json
```

After the separately authorized full verified-resume command finishes, compare against that baseline:

```bash
../LLM_ExpGym/.venv/bin/python data_runtime/resume_integrity.py compare \
  --manifest runs/full_v2/manifest.json \
  --snapshot reports/resume_full_v2.before.json \
  --report reports/resume_full_v2.comparison.json
```

Use fresh report names for another check. Existing files, including dangling report symlinks, are rejected. Reports cannot be placed under any monitored output/dump root, so reporting cannot change the collection being checked. Relative paths inside the manifest are resolved against its parent directory.

The snapshot enumerates all `.json` files recursively under every `job.output_dir` and `job.dump_dir`. This includes result/summary/agent JSON and every API attempt regardless of completion state. It records absolute paths, owning jobs, byte lengths, individual SHA256 hashes, counts/bytes by category, and a SHA256 over the sorted path/size/hash collection.

Explicit expected exclusions are saved in both report types: the input manifest; manifest-declared progress, status and stdout paths; non-JSON files; and all paths outside the selected job roots. Result summaries are included. Manifest metadata may change during resume, so its before/after byte hashes are recorded without making metadata-only changes fail. Changing job IDs, monitored roots, exclusion paths, or root availability does fail.

Comparison exit status is 0 only when the selected file collection, raw bytes, and monitoring scope are unchanged. Any added, removed, or changed file produces exit 1 and a report containing each difference, before/after hashes and totals. Even JSON formatting or key-order changes count as byte differences. Invalid input, unreadable files, detected writes during scanning, or an unsafe report destination produce exit 2 and an error message. Monitoring requires quiescent jobs; the tool checks file identities/timestamps while reading and again before completing the scan.

Identical raw-dump collection and bytes demonstrate that verified resume left the persisted API-attempt history untouched. This check supplements the existing result/dump completeness audit; it does not replace it or prove benchmark scores independently.

Six temporary-fixture CLI tests cover unchanged payloads with changed orchestration metadata; simultaneous added raw/removed agent/changed summary; report overwrite and monitored-root rejection; root-scope changes; dangling report symlinks; and empty-root removal:

```bash
../LLM_ExpGym/.venv/bin/python -m unittest -v data_runtime/test_resume_integrity.py
```

The tests only use temporary directories. No real full_v2 snapshot or resume was executed while implementing this tool.
