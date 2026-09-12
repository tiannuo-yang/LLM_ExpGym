# Explicit report input contract

Preparation code only. Do not run final aggregation while selected input files are changing. No recursive result search, model/scorer calls, automatic successful-run selection, bootstrap or p-values are implemented.

## Entry point

```bash
/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/.venv/bin/python -B \
  aggregate_material.py --spec /absolute/final-report-inputs.json \
  --output /absolute/new-report-directory
```

The output directory must not exist. `--check` byte-compares the same frozen inputs against an existing directory without writing. The generator does not seal, scan, publish, restore raw, or produce an independent-review claim.

All file references below use the same object:

```json
{"path": "relative/to/report-spec/or/absolute/file.json", "bytes": 123, "sha256": "actual SHA256"}
```

Every consumed input is hash-bound, recorded in generated `INPUTS.json`, and checked for stability. The SHA verifies identity, not scoring truth or prospective timing. Only report fixtures have been aggregated during preparation.

## Public reconstruction inputs

`prepare_inputs.py` combines the existing final metadata/usage exports after **all four** models have terminal inputs. `preparation_config.json` pins the currently available source identities; a null GLM export blocks preparation rather than manufacturing unstarted rows. Fill its last terminal/resource and public accounting entries from the owners' final receipts, then run once:

```bash
python -B prepare_inputs.py --config preparation_config.json --output inputs_v1
```

It copies the four exact original logical plans, the necessary GPT recovery plan, oracle, fixed historical CSVs and consumed small metadata/resource projections into a new directory. It emits the unified 369-slot `execution_index.json`, `spec.json`, `ALL_ATTEMPTS_INDEX.json`, resource CSV, explicit `PUBLIC_INPUT_FILES.json`, input/output identities and per-model restoration selections. It never opens result, agent or API-dump payloads; their bound hashes/lengths come from the owners' verified completion inventories. It does not create a scientific report at this stage. Private GPT `PREPARED.json` / credential-source control files are not copied.

Published model payload layout is `bundles/<model>/payload/manifest.json`, with members relative to each model's original owned root. Restore only the selections needed for report reproduction into fresh `restored-study/<model>` roots using the existing verified package CLI (all payload members are still stream-verified):

```bash
python -B rebuild/scripts/package_run.py verify \
  --manifest bundles/kimi/payload/manifest.json \
  --archive-dir bundles/kimi/payload --require-public-scan \
  --select restore_selections/kimi.json \
  --restore-dir /absolute/restored-study/kimi
```

Apply the same command to `deepseek`, `glm` and `gpt` with their own selected-member arrays and fresh restore directories. The package tool requires a trusted manifest/publication identity; this example does not itself verify a remote release. Full original dumps remain available in the same bundles without being copied into the shared report inputs.

Public report input paths are either relative to `spec.json` (copied shared inputs) or `@study/<model>/<original-member>` (bound payload files). Use:

```bash
python -B rebuild/aggregate_material.py \
  --spec spec.json \
  --artifact-root /absolute/restored-study \
  --output /absolute/new-rebuilt-report
```

Run the public commands from `results/eval-material-rerun-20260912/` using the recorded CPython **3.11.15**. Private preparation uses `report/inputs_v1/` and `report/full_report_v1/`; publication places their members directly at the public study root (`spec.json`, `plans/`, `historical/`, `restore_selections/`, etc.), with scripts/tests under `rebuild/`. Same-name files are deduplicated only when bytes and SHA match. The shared archive index and reconstruction instructions follow this layout; there is no extra public `inputs_v1/` layer.

The same `--artifact-root` interface works against the original local study root. Original plan/result bytes, including historical absolute paths recorded inside their provenance, are never rewritten. The adapter records logical input labels rather than the chosen restore directory, so moving restoration roots does not change report bytes. Two-root synthetic reproduction is tested. Raw resources are **not** reread: self-hosted tables and GPT physical-attempt/token projections are consumed as already frozen. Missing GPT request/pool timing in that projection remains unknown; superseded transport attempts stay in the separate complete-attempt input.

## Study spec

Required top-level keys:

| Key | Value / source |
| --- | --- |
| `schema` | `expgym.material-report-inputs.v1` |
| `study_id` | `eval-material-rerun-20260912-v1` |
| `expected_jobs` / `expected_cells` | `369` / `9` |
| `plans` | Four pinned master-plan file references; use original logical plans, not the recovery plan as an extra study |
| `execution_index` | One explicit effective-source mapping, described below |
| `oracle` | Frozen `data/hpo_tuning/oracle3.json`, 28,814 bytes, SHA `f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e` |
| `historical_absolute` | Fixed five-model `absolute_settings.csv` |
| `historical_gap0` | Fixed five-model `main_findings_v2/gap0_settings.csv` |
| `historical_expgym_summary` | Fixed five-model `main_findings_v2/main_expgym.csv`; the compact main-report Free→Tight table consumes its existing display-unit scores |
| `historical_family_rankings` | Fixed five-model `main_findings_v2/main_family_rankings.csv`; the six-family Free/Tight winners are taken from this same historical cohort |
| `resources_by_setting` | A pinned setting-level resource CSV with documented units and unknown denominators; copied unchanged |
| `all_attempts_index` | A pinned JSON index to all attempts/cost ledgers, including original failures and allocated startup/smoke costs; copied unchanged |

Master plans are `deepseek/queue/master_plan.json`, `glm/queue/master_plan.json`, `kimi/queue/master_plan.json`, `gpt/queue-plan.json`, all relative to the new study root. Plan-only validation of these exact four files passed: 369 pools, 9 cells, four model identifiers matching the historical exports. This check read no results.

Historical input files must be bound to commit `6c63f1c03c88683fa55be5cafcbb8122ac8fadaa`, `results/five-model-ranking-20260911/`. Do not re-export or rescore historical raw for this report. The old strict and Gap0 CSVs have distinct metric names; they remain distinct endpoints.

The two new historical display inputs were read from that exact local Git commit (not a moving-branch source):

| File | SHA256 |
| --- | --- |
| `main_findings_v2/main_expgym.csv` | `a877a88f63279984f903fa4f6bcd96eb949e4f19098e1d2d78c933e900c19443` |
| `main_findings_v2/main_family_rankings.csv` | `2ed27ed6385103a9f77983558d71adbaa629c4575410947c774ee4490719cfd6` |

Both are copied unchanged into the generated report. Question 1 displays five model rows with Search/Audit/tuning Free→Tight values and signed decreases; the original CSV retains Moderate. Question 3 displays all six family winner sets and Free/Tight changes, preserving tied winners. These tables explicitly say **frozen historical single-agent cohort, not this rerun's new validation**. The adapter checks saved arithmetic/winner flags, never reads old raw or injects new PoolAct scores. Historical HPO/NAS uses the old authorized Gap0 display; new NAS strict/Gap0 endpoints remain separately labelled in question 2.

## Effective execution mapping

```json
{
  "schema": "expgym.material-execution-index.v1",
  "jobs": [
    {
      "logical_job_id": "original frozen master job ID",
      "execution_status": "completed",
      "cohort": "explicit authorized cohort",
      "effective_plan": {"path": "bound single-pool plan", "bytes": 123, "sha256": "actual SHA256"},
      "effective_job_id": "job ID inside effective plan",
      "result": {"path": "effective result/strategy/result.json", "bytes": 123, "sha256": "actual SHA256"},
      "summary": {"path": "effective result/summary.json", "bytes": 123, "sha256": "actual SHA256"},
      "verification_receipt": {"path": "existing final worker receipt", "bytes": 123, "sha256": "actual SHA256"},
      "identity_score_verification_passed": true
    }
  ]
}
```

Exactly one mapping row is required for each of the 369 original slots. `completed` means normal execution finished; NAS may still have an unknown strict score. `failed` and `not_started` instead require a concrete `reason`, do not supply a contributing result, and emit unknown for **all** scientific metrics, including Gap0. Running/undrained jobs are not accepted as a final input.

The explicit verification declaration must be backed by the existing queue worker's identity-and-score validation/exit record. The adapter reads and pins that receipt but does not claim it independently validates raw or reruns the scorer. Preserve the receipt's original schema and scope. Final report review remains separate and is performed once after both reports exist.

Self-hosted effective plans are the dynamic dispatcher's per-logical-job bound plans, not a guessed round-robin endpoint. GPT recovery uses the prospectively retained `gpt/recovery_001/attempt-mapping.json`: its new job is mapped back to the single old C/PoolAct/2208 logical slot, **not** counted as a 370th pool. The original 12 Connection-refused transport attempts remain in the all-attempt index. The adapter never searches for the newest successful result.

Recovery source SHA and scientific/model arguments must match the original logical slot. Only explicit execution-location fields (`output_dir`, endpoint, cache namespace, terminal evidence directory and credential file path) may differ. Model ID, data selector, task, seed, N, strategies, reasoning/sampling/output/context/step limits and policies may not change silently. Identical scientific arguments are also required across each matched three-arm block, apart from strategy itself.

## Saved-score contract

- Search: saved `answer_perf` supplies member F1; saved aggregate supplies F1-MV.
- Audit: saved `answer_metrics.evidence_acc` / `label_acc` supply separate EA/LA MI/MV. Aggregate `answer_perf` is not substituted for EA.
- NAS: saved member raw performances are transformed one member at a time using `max(0, 100 * (perf - oracle.mean_perf)/(oracle.best_perf - oracle.mean_perf))`; no upper clip. This is the exact old API exporter contract (`common/analyze_api_studies.py:225–237, 434–450`). Original strict MI/BoN stays unknown if any required member lacks a final configuration.
- Gap0: only `task-abstention-v1`, normal-loop, unscorable-missing-configuration members receive zero alternative deployment utility. It never fills an HTTP/provider/tool/scorer/persistence failure. MI divides by four; BoN is the maximum delivered Gap or zero if all four normally abstained.
- Arithmetic checks against saved NAS raw aggregate do not constitute independent answer scoring. Search/Audit voting is consumed as saved, not reimplemented.

## Final handoff

Generated files include main/detail reports, every planned pool/metric/status, all setting means and three contrasts, task/repeat tables, historical comparisons, source settings, resource copies and input identities. All finite values, negatives, genuine zeros and unknowns remain visible. NAS R3 is folded within task before equal task averaging. Incomplete comparisons never silently take a known-only intersection.

The final packaging owner adds the shared `ARCHIVE_INDEX.md` and `ARCHIVE_INDEX.json` linked directly from both reports; these must map original dumps to inventories/shards and include restoration paths. The report adapter intentionally does not invent archive hashes or publication URLs before sealing. Add actual deployment/fidelity/latency interpretation and result-dependent prose after completion; do not publish the preparation note as a final scientific conclusion.

Validation:

```bash
/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/.venv/bin/python -B \
  -m unittest -v test_aggregate_material.py
```

Twenty-two synthetic tests currently cover unknown versus zero, full-pool denominators, clipping-before-averaging, negative effects, exact matched design, recovery configuration drift, input tampering, deterministic generation, retention of old counterexamples/new unknowns, unchanged historical display units, tied old winners, rejection of historical matrix/flag drift and retaining unknown cells in overall direction-count denominators. They are report-only tests, not actual model/GPU verification.

`test_prepare_inputs.py` adds seven small interface fixtures for terminal-input gating, inherited artifact identities without payload reads, producer export descriptors, GPT receipt/resource adaptation, superseded-attempt retention and relocation-invariant rebuilds. No new audit agent or additional scientific review pass is involved.
