# Tuning trajectories: acquisition depth and stopping

This analysis covers all 480 execution-complete, selected single-agent tuning trajectories: 81 each for Kimi, GLM, Qwen, DeepSeek and GPT, and 75 for Gemini. It includes unscored completed trajectories when measuring behavior; score absence is not imputed. Six unfinished Gemini single-agent slots are excluded. All inputs are the original N1 cohorts selected by the current six-model report.

## 1. Tight budgets compress the number of distinct hypotheses that can actually be tested

On 159 matched task/seed Free–Tight pairs, the mean number of delivered performance observations falls from **24.58 to 3.39**. Across all available trajectories, the respective Free / Moderate / Tight means are **24.61 / 10.52 / 3.42**. The decline occurs for each of the six models. This is a loss of observed search breadth, not simply an increase in repeated single-agent evaluations: there are just **16 repeated configurations in 6,168 delivered evaluations (0.26%)**, and **none in the 547 Tight observations**.

The useful distinction is between requesting a test and acquiring its result. At the budget boundary the last requested performance is withheld. Counting this request as an observation would overstate the information available to the agent.

## 2. Stopping shifts from an interaction cap to the feedback-budget frontier

| Regime | Available trajectories | Natural answer | Feedback-budget termination | Step/evaluation cap | Other termination | Mean delivered observations |
|---|---:|---:|---:|---:|---:|---:|
| Free | 160 | 48 | 0 | 94 | 18 | 24.61 |
| Moderate | 160 | 126 | 23 | 4 | 7 | 10.52 |
| Tight | 160 | 87 | 66 | 0 | 7 | 3.42 |

The rate of natural completion is therefore **not monotonic** in budget. The Moderate group more often ends with an explicit answer, whereas Free frequently reaches the 30-step cap and Tight more frequently crosses the feedback boundary. Natural completion is not synonymous with leaving a large budget unused: naturally completed Moderate and Tight trajectories have already delivered observations costing **90.7% and 93.0%**, respectively, of their feedback budgets on average. All **66 Tight budget-terminated trajectories** contain one withheld final evaluation. This is consistent with budget-aware stopping, but does not establish that a particular unchosen next test would have been unaffordable.

Suggested interpretation: stopping is consistent with awareness of the remaining feedback budget, but budget-crossing attempts remain common. Agents often stop near the budget frontier, while a substantial fraction attempt one evaluation that cannot return usable evidence. These observed stopping codes and cost fractions do not by themselves identify the model's internal reason for deciding to stop. Free removes the feedback-budget constraint and cost visibility, while feedback costs are still recorded; it is **not unlimited interaction**.

## 3. The useful depth of exploration is task-dependent, not a universal early-stop rule

In Free trajectories, the final best observed configuration is first reached after the fifth observation in **141/159 trajectories with any delivered performance**. Late record-setting is common, but its magnitude must not be exaggerated: the median increase in raw performance after the first five observations is about **0.45 percentage points** on the matched Free trajectories, versus a mean of 1.85 points. Thus, "best appears late" does not mean every late improvement is large.

A more stable task-level pattern is the shape of discovery:

| Free tuning family | First occurrence of final observed best, mean fraction of delivered sequence | Mean strict record improvements after the first observation |
|---|---:|---:|
| NAS101 | 74.8% | 5.24 |
| NAS201 | 55.4% | 2.96 |
| ParamNet | 84.7% | 7.10 |

**Every one of the six models** reaches its final observed best later in its own ParamNet sequences than in its NAS201 sequences, and every model makes more strict record improvements on ParamNet. This supports task-dependent acquisition depth: in this dataset, ParamNet looks more like continued iterative refinement, while NAS201 tends to establish its best observed candidate earlier and continue testing alternatives afterward. The claim describes the observed sequences; it is not proof of convergence, nor evidence that the same ordering would survive a fixed-prefix intervention.

## Scoring boundary: avoid a false final-selection claim

In all 464 trajectories with both an observed performance and a scored final answer, the scored answer equals the best observed performance within 1e-6. **This must not be reported as perfect model selection:** 74 trajectories use the inherited `best_evaluated_fallback` scoring path, which can replace an unmatched submitted answer with the best evaluated configuration. Fallback is not synonymous with an empty answer and can involve parsing or numerical representation. This analysis therefore uses delivered observations and stopping behavior for the main tuning insights rather than claiming flawless final configuration selection.

## Reproduction and traceability

- Run `python -B analyze_hpo.py` in this directory's parent workspace environment; no model calls or rescoring occur.
- `INPUT_INVENTORY.json`: selected source manifests plus SHA-256, size and path of every canonical input trace.
- `trajectories.csv`: one row per execution-complete trajectory, including original termination, source, configuration counts and discovery positions.
- `delivered_events.csv`: each visible finite performance, in acquisition order. Hidden over-budget performances are excluded.
- `by_regime.csv`, `by_model_regime.csv`, `by_family_regime.csv`, `by_model_family_regime.csv`: descriptive summaries.
- `free_tight_pairs.csv`, `matched_free_tight_by_regime.csv`, `matched_free_tight_by_model.csv`: within-model, same-task, same-seed matched comparisons without imputing missing Gemini slots.

The summaries pool repeated trajectories descriptively; they are not confidence intervals or causal effect estimates. Configuration identity compares complete argument objects, treating numerically equal integer/float values as equal. "Record improvement" means a strictly larger visible performance by more than 1e-12. The first-best position uses the first occurrence of the observed maximum; it does not peek at withheld results.
