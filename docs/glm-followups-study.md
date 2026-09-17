# GLM scaling, Low thinking, and PoolAct ablations

This is a custom study, with scope confirmed on 2026-09-17. It uses GLM-5.3
only. The frozen six-model report remains the authority for task selection,
repetitions, hypothesis orders, scoring, and historical Max results. The study
does not rerun a new 417-trace Max ExpGym arm.

| Component | New logical executions | New agent trajectories |
|---|---:|---:|
| Audit scaling, Moderate/Tight, N=2/4/6/8 | 234 pools | 1,248 |
| ExpGym Low, all tasks, Free/Moderate/Tight | 417 single-agent runs | 417 |
| N4 Tight ablation, three PoolAct scenarios, after reuse | 266 pools | 1,064 |
| Total formal execution | 917 | 2,729 |

These counts exclude a separate 19-execution, 58-trajectory technical pilot,
transport attempts, and offline subset computations. Historical Max contributes
417 existing comparison records without new model calls.

## Scaling

Use the same 13 Audit documents and default hypothesis order as the historical
PoolAct matrix, R1, Max thinking. Moderate/Tight use per-agent feedback budgets
of beta 10/3 and c_base 300 simulated seconds. Increasing N increases the total
potential pool budget; this is not a fixed total-compute comparison.

Run cached and PoolAct independently for all four N values. Run naive only at
N8, then average the scores of all C(8,N) subsets for each smaller N. Apply the
original per-hypothesis vote and scorer to each subset before averaging; retain
the original member order for vote ties. There are 28, 70, 28, and 1 subsets for
N=2,4,6,8. Overlapping subsets are not independent replications. A member-level
mean averaged over all subsets must equal the full N8 mean at every N.

The primary score is evidence-set accuracy after voting. Label accuracy and
mean-individual scores remain secondary. An execution failure in the source N8
pool does not authorize silently dropping that member and reporting a complete
subset curve.

## Low versus historical Max

Each budget has 73 Search questions (39 Whois and 34 Whatis), 13 Audit documents
with three fixed orders, and nine HPO tasks with three repeats: 139 trajectories.
Low runs all three budgets, giving 417 trajectories. The HPO tasks are ParamNet
adult/higgs/letter, NAS101 A/B/C, and NAS201 cifar10-valid/cifar100/imagenet16-120.

Low still enables thinking. The deployed GLM template consumes low/max through
both the request reasoning_effort field and the corresponding template kwarg;
the latter can override the former, so both must agree. Preserve clear_thinking
false and the remaining registered generation parameters. Request values and
template rendering establish parameter transmission, not a guarantee of fewer
reasoning tokens or higher scores.

Historical Max is valid evidence for its recorded protocol. It used an earlier
code and Audit prompt version, and the original N1 results were not replaced by
the later N4 reruns. Consequently, the new Low versus historical Max comparison
is a comparison across both effort and execution cohorts. Report those identities
and do not attribute the entire difference to effort. Keep original scores and
raw artifacts unchanged.

## Ablation

Use N4, Tight, Max thinking on 39 Whois questions, 13 Audit documents, and
NAS101 A/B/C with three repeats: 61 positions per method.

| Method | Observation cache | Shared model context | Reasoning/claim lock |
|---|---|---|---|
| naive | no | none | no |
| cached | yes | no proactive peer context | no |
| peer_context (b) | yes | complete visible peer actions/results | no |
| graph_no_lock (a) | yes | graph, paths, coverage, and claims | no |
| poolact | yes | same graph protocol | yes |

The ablation removes the reasoning critical section, not the internal locks that
protect shared data structures. All variants preserve strict budget boundaries,
completion-time visibility, isolated agent clocks, and cleanup on exceptional
paths. Peer context contains completed, visible tool action/result records from
other agents; it excludes private reasoning and pending results. Thus b-to-a is
the addition of the existing graph information package, including pending-state
information, not a pure serialization-format comparison.

The 305 result positions reuse 39 Audit positions from the new scaling study:
cached/PoolAct N4 and naive's N4 subset mean, all at Tight. Therefore only 266
additional pools execute. The Search and NAS naive baselines run directly at N4.

Show separate five-column figures for Whois F1-MV, Audit EA-MV, and NAS Gap-MI.
Do not average their different units into a single score. Keep signed adjacent
contrasts, including regressions and ties. A highest PoolAct column is a
hypothesis, not an execution or publication acceptance condition.

## Execution and delivery

Use a clean integrated code revision, the fixed checkpoint/runtime/data
identities, isolated outputs and caches, and native multi-turn pilot validation.
The planned serving topology is 32 H200 GPUs in two independent TP16 replicas;
one pool stays on one replica. The pilot reads concrete trajectories and checks
parameter transmission, scoring, forced final, strict budget visibility, N8
concurrency, and all new context mechanisms. ParamNet requires the verified
legacy evaluator environment.

Resume only valid completed outputs or first-execute unstarted jobs. Preserve
begun failures and all attempts; do not silently resample valid zero scores,
missing answers, or negative effects. Record execution and score completeness
separately. Report all planned settings and actual or unknown resource usage.

Full sanitized API dumps, trajectories, failures, and operational archives remain
local. Publish only reviewed code, reports, figures, metric tables, and relative
path/size/SHA provenance indexes. The final report receives one independent
numerical/logical review, then a security scan of the actual Git publication
delta and verification of the remote commit.

See [PoolAct implementation](poolact.md), [portable analysis](portable-study.md),
[queue semantics](scheduling.md), and [report workflow](full-setting-report.md).
