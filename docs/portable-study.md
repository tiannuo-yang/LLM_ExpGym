# Portable study: frozen-input descriptive analysis

This is a **Custom study** analysis contract, not paper-exact reproduction or a
model-serving entry point. `scripts/analyze_portable_study.py` is standard-library
only and makes no model, network, evaluator, or runner calls. It never recursively
collects results, chooses successful seeds, retries negative results, or modifies
the supplied artifacts. Existing runner CLIs are unchanged by this analyzer.

**R09 boundary: this version implements no validated confirmatory inference.**
All bootstrap intervals are descriptive at every sample size. Neither a positive
interval nor passing integrity/quality/sample gates can produce `supported`,
`refuted`, significance, or equivalence. This is deliberately conservative until
an applicable method and its assumptions are explicitly registered and validated.

## Freeze before evaluating

1. Identify actual model/provider/checkpoint identities, protocol/source/data
   hashes, reasoning/tool mode, output and step caps, budgets, task encodings,
   agent count, and final-answer scoring policy. Bind these in the registration
   record referenced by `registration.protocol_id`. Different protocols or model
   revisions require a different study identity, not overwritten result files.
2. Freeze task identities, development/held-out assignment, repetitions and
   outerseed identities, all output artifact paths, endpoints, expected direction,
   minimum important effects, quality gates, descriptive bootstrap method, sample minima,
   and multiplicity families. Save the manifest SHA256 in an independently
   retained dated registration record **before examining evaluation outcomes**.
3. Do provider/parser/score plumbing development on the development partition.
   Do not select held-out questions for favorable results, replace failed items
   with easier ones, tune prompts on held-out scores, or call old inspected K3
   items previously unseen. Reusing inspected items is legitimate, but label it
   exploratory/development. `split` labels alone do not establish real holdout.
4. Freeze transport retry policy and execution acceptance separately from semantic
   performance. A valid wrong answer or zero is data; a missing/corrupt result is
   incomplete evidence. A protocol failure may itself have a valid score and must
   remain in the intention-to-evaluate endpoint. Do not condition score inclusion
   on successful tool use or favorable answer parsing.
5. Export all planned rows, independently recompute their scores, and issue the
   hash-bound integrity receipt below. The analyzer verifies receipt bindings,
   but does not implement or independently attest the upstream score audit.
6. Run once with the pre-recorded manifest hash, then retain every endpoint and
   descriptive interval, including zero/negative outcomes. A valid negative analysis exits 0;
   malformed/incomplete evidence exits 2. Do not increase repetitions until an
   effect becomes significant. Any planned sequential design needs a separate
   stopping/error-control protocol; this analyzer assumes one fixed final look.

No task count or model name is hardcoded. In particular, do not assume a proposed
60-item Search set exists, is fresh, or matches the old 18-whois set without an
explicit data inventory. A study of three selected models supports statements
about those models/settings, not the model population in general.

## Endpoints and comparisons

A sensible starting registration, to approve before results, is:

| System / scenario | Primary effect endpoint | Secondary endpoints |
|---|---|---|
| ExpGym Search | Set F1, Free minus Tight | Moderate scores, calls, costs |
| ExpGym Audit | Exact evidence-set accuracy, Free minus Tight | Label accuracy, verification efficiency |
| ExpGym tuning | Normalized Gap under the frozen final policy, Free minus Tight | Raw accuracy, invalid-final rate |
| PoolAct Search | Voted set F1, PoolAct minus Naive | Mean-individual F1, Cached contrast |
| PoolAct Audit | Voted exact evidence-set accuracy, PoolAct minus Naive | Voted label accuracy |
| PoolAct tuning | Mean-individual Gap, PoolAct minus Naive | Best-of-N Gap, raw accuracy |

These are candidate scientific endpoints, not validated hypothesis tests in this
analyzer. These choices are not universal defaults: the frozen manifest must name every
metric, comparison, role and family explicitly. Paper Table 3's tuning improvement
column uses MI **Gap points**, not BoN; Audit uses EA, not LA. BoN can remain high
despite one failed agent. If deployment utility requires BoN primary, preregister
that choice and describe the departure. Do not switch endpoints after seeing MI.

The study's default tuning policy remains explicit `legacy` unless a different
protocol is prospectively authorized. `submitted` scores the actual submitted
configuration and is a separately named new-study estimand, not a formatting fix
or a silently interchangeable replacement for historical best-observed fallback.
All compared strategies must use the same frozen policy; this analyzer does not
inspect the raw runner configuration to prove that they do.

F1/LA/EA normally use fractions in [0,1]; a difference of 0.02 is 2 percentage
points. Gap normally uses [0,infinity): 100 is a finite-search reference and
values above 100 are valid. Compute per-agent Gap with the frozen oracle and
zero-clipping **before** averaging MI. Use the repository's frozen PoolAct voting
and tie handling; never choose the best Search answer after the fact. EA is exact
evidence-set matching and does not implicitly require a correct label.

ExpGym's positive effect means degradation; PoolAct's positive effect means
improvement. Both use `higher_is_better` to orient lower-is-better metrics if
explicitly chosen. Relative percentages divide the oriented effect by the absolute
baseline mean, and are null for a zero baseline. The main effect/CI remains in the
declared metric unit; relative changes are descriptive, not separate tests.

Put all confirmatory endpoints across the selected models, regimes and scenarios
in a predeclared multiplicity family (or justify genuinely distinct claim families
beforehand). Primary descriptive displays use two-sided percentile bootstrap at
`1 - (1-confidence)/family_size` (Bonferroni). Nominal CIs are also retained.
Secondary intervals are nominal and exploratory, never confirmatory. No p-values
are manufactured from bootstrap sign frequencies. Bonferroni addresses the declared
family only if individual intervals have valid coverage. This implementation
does not establish that premise, so its Bonferroni-form quantile adjustment is
only a descriptive display and does not establish familywise error control.

## Independent units and bootstrap targets

Each input row is one metric of a complete ExpGym trace or a **whole PoolAct
pool aggregate**. Agents within a pool are correlated and are never rows for
inferential replication. MI is one aggregate metric per pool, not four samples.
Audit's 17 hypotheses are not 17 independent documents. All paired comparisons
require the exact registered item × outerseed Cartesian product on both sides;
there is no silent complete-case intersection. An `outerseed` names a repeated
full pool (or ExpGym repeat/order), not the seed of one member agent.

The point estimate always first averages paired effects over repetitions within
each item, then gives every registered item equal weight. Three NAS tasks with
three pools each means three task clusters and three outer repetitions, not nine
independent tasks or 36 independent agents. No cross-model pooling is implicit.

Choose `bootstrap_method` for each endpoint before looking at scores:

- `item_cluster`: resample items with replacement; keep each sampled item's full
  paired outerseed set intact. This describes sensitivity within the listed fixed
  snapshots and recorded seeds, not an established item-population CI. It does not
  separately estimate unobserved-seed variance. Copying every repeat does not
  increase the independent item count or narrow this descriptive interval.
- `nested`: resample items, then paired outerseeds within each sampled item.
  This descriptive hierarchical resampling additionally assumes repeat variation
  is independent between items; do not use it if an outer repetition creates
  shared run/session effects across items. It can be conservative in small
  hierarchical samples. The analyzer does not verify that assumption or confer
  valid coverage. Document the stochastic hierarchy, not merely “bootstrap”.
- `fixed_items_outer_repeats`: hold all registered items fixed and resample
  **shared outerseed blocks across every item**. It describes empirical repetition
  variation on exactly these tasks, not validated generation-population or unseen-task
  inference. Actual independent generation repeats require external evidence;
  identical seed labels do not establish effective provider seed control. This is the
  narrower alternative for a tiny NAS A/B/C set. With three outerseeds there are
  only three repetition blocks: adding agents or hypotheses does not improve it.

The script records unmet preregistered sample minima and method requirements, but
**no sample count makes these bootstrap outputs confirmatory**. There is no magic
minimum N that proves reliability. Three tasks × three repeats can yield
descriptive intervals, not a cross-task portability claim. Even a large or
constant-effect sample remains `not_confirmatory` in this implementation.

The small-sample problem is concrete. Suppose independent paired effects are +1
or -1 with equal probability under a zero-effect population. With three pairs,
the event that all are +1 has probability 1/8 = 12.5%. Conditional on that sample,
every empirical bootstrap draw is +1 and every percentile interval is [1,1],
regardless of resampling count or family-tail adjustment. Reading it as 95%
confirmation would already give at least 12.5% false directional confirmation.
A zero-width interval is explicitly flagged, never evidence of certainty. Tests
enumerate all eight sign patterns and ensure no output can confirm a hypothesis.

No sign/permutation test is silently substituted: a sign test would concern a
sign-probability/median estimand under suitable independent-unit assumptions,
not automatically the mean effect above. A paired randomization test needs a
justified exchangeability/randomization design and null. A future method requires
a new explicit preregistered contract, exact small-sample handling, tests and
review before any confirmation status is enabled.

Question-level resampling does not create independent corpora: many PhantomWiki
questions in one snapshot share a world. This schema records fixed snapshots but
does not implement corpus-level inference. Known Audit documents or NAS tasks do
not become unseen holdout by changing generation seeds; report fixed-known-task
results as such. Two new corpora do not give as many independent worlds as there
are questions in those corpora.

Use enough bootstrap draws that each adjusted tail has at least 20 expected
draws for Monte Carlo resolution; insufficiency is recorded separately.
For nominal level .95 and M primary displays,
this requires at least `800*M` draws; 50,000 is a reasonable computation-only
starting point for moderately sized families. More draws only reduce Monte Carlo
noise; they do not add independent observations or establish coverage. Resampling is deterministic from
the registered seed plus comparison ID, and independent of input row order.

## CSV and frozen manifest schema v1

The CSV is ten-column **long format** (the requested metric/value row schema):

```csv
model,system,scenario,item,regime,strategy,outerseed,metric,value,artifact
model-x,poolact,restricted_search,question-001,cost_tight,naive,1206,f1_mv,0.5,runs/model-x/q001/1206/naive/result.json
```

All identity fields and seeds are nonempty strings. `system` is `expgym` or
`poolact`. `artifact` exactly matches a manifest entry: a relative path is resolved
against the manifest directory, not the CSV directory or current shell directory.
Each metric row must match that artifact's complete identity. One artifact may
have several metric rows, but two artifacts cannot have the same identity and
two path aliases cannot refer to the same physical file (resolved-path/symlink
and filesystem device/inode hardlink checks). Byte-identical independent copies
are not rejected; proving genuinely separate generation still belongs to the run
audit, not file-name or hash heuristics. CSV columns are exact:
extra agent IDs, omitted fields, duplicate rows, extra/unregistered items,
NaN/infinity, missing values and out-of-range values are errors.

Manifest shape (illustrative excerpt; list **all** actual artifacts and compared
items, not just the single example entry):

```json
{
  "schema_version": 1,
  "study_id": "portable-registered-v1",
  "registration": {
    "selection_rule": "fixed_manifest_no_outcome_selection",
    "frozen_before_evaluation": true,
    "protocol_id": "path-or-identifier-of-frozen-protocol-with-source-data-model-hashes"
  },
  "bootstrap": {"samples": 50000, "seed": 20260908, "confidence": 0.95},
  "metrics": {
    "f1_mv": {"unit": "fraction", "higher_is_better": true, "minimum": 0, "maximum": 1},
    "protocol_failure_rate": {"unit": "fraction", "higher_is_better": false, "minimum": 0, "maximum": 1},
    "gap_mi": {"unit": "Gap points", "higher_is_better": true, "minimum": 0, "maximum": null}
  },
  "artifacts": [{
    "artifact": "runs/model-x/q001/1206/naive/result.json",
    "model": "model-x", "system": "poolact", "scenario": "restricted_search",
    "item": "question-001", "regime": "cost_tight", "strategy": "naive", "outerseed": "1206",
    "unit": "pool_aggregate", "split": "heldout",
    "metrics": ["f1_mv", "protocol_failure_rate"]
  }],
  "quality_gates": [{
    "id": "model-x-search-protocol", "metric": "protocol_failure_rate",
    "operator": "<=", "threshold": 0.01,
    "selectors": {"model": "model-x", "system": "poolact", "scenario": "restricted_search", "split": "heldout"}
  }],
  "comparisons": [{
    "id": "model-x-search-tight", "kind": "poolact_vs_naive",
    "model": "model-x", "scenario": "restricted_search", "regime": "cost_tight",
    "strategy": "poolact", "split": "heldout", "metric": "f1_mv",
    "scope": {
      "data_snapshots": ["phantom-seed2-exact-snapshot-hash"],
      "item_status": "prospectively_reserved",
      "inference_population": "registered_items_only",
      "outer_repetition_interpretation": "seed_labels_only"
    },
    "items": ["question-001", "question-002"], "outerseeds": ["1206", "1207", "1208"],
    "role": "primary", "family": "all_portability_primaries",
    "bootstrap_method": "item_cluster", "minimum_items": 10,
    "minimum_outerseeds": 3, "minimum_effect": 0.02,
    "quality_gate_ids": ["model-x-search-protocol"]
  }]
}
```

For ExpGym, use `unit: "single_trace"`, `kind: "expgym_free_tight"`, an explicit
single-agent strategy string such as `single`, and omit comparison `regime`.
Free and Tight are paired automatically. PoolAct comparison `strategy` can be
`poolact` or `cached` against `naive`; register Cached secondary unless justified
otherwise. Moderate/all other extra registered rows remain in aggregate tables.
The same `(scenario,item)` cannot appear under different splits anywhere in the
manifest. Bootstrap/sample/effect/gate parameters have no outcome-derived defaults.

Every comparison requires `scope`: `data_snapshots` lists fixed data identities;
`item_status` is `previously_inspected`, `prospectively_reserved`, or
`mixed_or_unknown`; `inference_population` must be `registered_items_only`.
`outer_repetition_interpretation` is `seed_labels_only`, `fixed_orders`, or
`verified_generation_repeats`. The last is an external declaration whose evidence
belongs in the run audit; the analyzer cannot independently verify it. These
fields describe scope, never expand inferential authority. Cross-corpus or
cross-model-population generalization is not implemented.

Quality gates are prospectively selected metric thresholds, not score filters.
Examples include protocol-failure rate and valid-result fraction; define the
denominator and failure taxonomy in the exporter protocol. Selectors must bind
model, system, scenario, split; optionally bind regime/strategy/seed/item. The
value is an equal-item mean, with equal selected rows within each item. Register
separate per-strategy/regime gates when a global mean would mask a bad condition.
One model's good parsing cannot satisfy another model's gate. Missing or failed
gates are additional blockers; passing every gate still leaves bootstrap outputs
descriptive. The receipt/gates must not become outcome-dependent filters that
hide failure-bearing score rows.

An independent audit receipt is created **after** export, without modifying the
frozen manifest. Its exact artifact path keys must match the manifest:

```json
{
  "schema_version": 1,
  "manifest_sha256": "the-preregistered-manifest-hash",
  "csv_sha256": "hash-of-exact-export-bytes",
  "artifact_sha256": {"runs/model-x/q001/1206/naive/result.json": "hash-of-result-bytes"},
  "complete": true,
  "score_recomputation_passed": true
}
```

The actual receipt must cover every artifact. Have an independent validator bind
the CSV values to recomputed raw scores, aggregate/vote semantics, source/config
identity, expected agent files and empty pending-claim state. Merely generating
these hashes and setting `true` is not score validation. The report distinguishes
`receipt_bound`, `receipt_declares_complete_recomputed_scores`, and
`scores_recomputed_by_analyzer` (always false). A successfully bound receipt is an
export contract containing someone else's declaration, not proof of score truth
or that the auditor is independent. It never unlocks statistical support.
SHA pinning detects changed content; it cannot independently prove registration
timing or that humans had not already inspected a held-out item's outcomes.
Manifest, CSV and receipt each use one byte snapshot for both hashing and parsing.
The analyzer also rechecks inputs/artifacts/receipt after computing statistics;
ordinary concurrent changes fail closed. This is a stability guard, not an atomic
filesystem snapshot, protection against change-and-revert, or a guarantee against
changes after the guard. Keep inputs immutable during analysis and retain the
receipt/artifact inventory with the report.

## Run and inspect

```bash
.venv/bin/python scripts/analyze_portable_study.py \
  --manifest /absolute/study/registered_manifest.json \
  --manifest-sha256 PREVIOUSLY_RECORDED_SHA256 \
  --csv /absolute/study/metrics.csv \
  --audit-receipt /absolute/study/independent_audit_receipt.json \
  --output-dir /absolute/study/reports/analysis_v1
```

Output directory must not exist. Seven files are written: `report.json` with
input/analyzer fingerprints and all gates; `REPORT.md`; `effects.csv` with nominal
and family-tail-adjusted descriptive intervals; `paired_rows.csv` with both artifact links;
`paired_items.csv`; `aggregate_metrics.csv`; and `by_outerseed.csv`. Aggregates
retain all models/scenarios/regimes/strategies/metrics/splits, with no implicit
cross-model averaging. They give items equal weight, not heavy-repeated items
extra weight. Pair count is descriptive; it is never labeled independent sample N.

Every primary is `not_confirmatory`; every secondary is `exploratory_secondary`.
`confirmatory_inference_available` is false and `all_primary_hypotheses_supported`
is null (not tested, not “all hypotheses disproved”). Numerical observed direction,
effect size, nominal/family-adjusted descriptive intervals, and whether the point
estimate exceeds the registered minimum remain visible. There is no path to
`supported`, `opposite_direction` as a hypothesis decision, or equivalence. Valid
negative observations still exit 0. Statistical acceptance requires an additional
applicable validated method; this descriptive exporter does not complete it.

Fixed per-agent budget does not mean fixed system total expense. Performance
contrasts alone do not establish cost efficiency, universal PoolAct superiority,
native-vs-text causal effects, six-model ranking replication, or N=1…8 scaling.
Register those additional estimands/designs separately instead of reinterpreting
this report. Preserve actual token/API/GPU cost, simulated feedback cost, protocol
diagnostics, all rejected executions and historical results alongside it.

No-cost analyzer validation:

```bash
.venv/bin/python -m unittest discover -s tests -p test_analyze_portable_study.py
```

This validates the statistical/data contract on synthetic files, not real provider
compatibility, native tool behavior, or the power of any planned real study.
