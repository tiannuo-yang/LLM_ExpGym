# Task abstention and evidence: v5 usage

The v5 changes apply to the shared ExpGym and PoolAct runners, not to a
particular model. They do not establish a performance improvement or a completed
experiment.

## Enable the policy explicitly

Append this supported option to your existing `scripts/run_paper_sweep.py` or
`scripts/run_poolact.py` command:

```text
--missing-final-policy task-abstention-v1
```

The default remains `--missing-final-policy error` for backward compatibility.
The new policy acts after a normal agent-loop return; it does not change model
requests, sampling, tool budgets, or the number of permitted decisions. Do not
mix policies within a pool or silently relabel historical runs as v5.

## What a missing final answer means

- **Search and Audit:** when the returned raw answer is `None` (JSON `null`),
  preserve it unchanged. Pass an empty prediction, `scoring_input=""`, to the
  original task evaluator. Record its actual score and
  `score_status="scored_empty_prediction"`; do not substitute a universal zero.
- **HPO/tuning:** when the returned raw answer is `None`, no final configuration
  exists to score.
  Keep `scoring_input`, performance, and metrics null, with
  `score_status="unscorable_missing_configuration"`. Do not evaluate an invented
  configuration or use a best-observed fallback for this missing endpoint.
- **Full N4 tuning pools:** if any agent lacks a final configuration, the full
  pool endpoint remains unknown. Full-pool MI/BoN reporting must not replace it
  with an available-agent mean or maximum. Known-subset summaries are separate,
  explicitly labelled descriptions with their original denominators.

This does **not** remove the existing `tuning_final_policy=legacy` behavior for
non-missing answers, including its historical final-selection/fallback rules.
Missing-answer handling and tuning-final policy are separate choices.

## Completion is not always a score

Only a normally returned loop enters task-abstention handling. Unhandled HTTP
errors, provider aborts, tool or scorer exceptions, and persistence/integrity failures remain
failures; do not convert them into model abstentions or successful zero scores.
Retain their raw attempts and incurred or unknown costs. This policy does not
add retries, repeatedly resample missing answers, or relax resume validation.

Normalized ExpGym trace-v2 output uses schema **2.1.0**, retaining the raw answer,
scoring projection, policy, and terminal status. Read `execution_complete` and
`score_complete` separately. Separate terminal-evidence sidecars preserve loop
snapshots and exceptional paths; they are not standalone completion markers or
independent proof that a score is correct. Preserve them alongside traces and
raw request/response records.

## Blinding and exact reproduction

The prompt changes remove explicit benchmark-identity cues and the Search
gold-answer-count hint. They do not prove that training contamination, dataset
recognition, or all structural clues are absent.

For a particular study, use its exact frozen manifest and source commit for
model/request settings, seeds, item selectors, Audit orders, repetitions,
budgets, Pool size/strategy, and tuning-final policy. Enabling this one flag is
not a substitute for that configuration or for a fresh, independent review of
the final results.
