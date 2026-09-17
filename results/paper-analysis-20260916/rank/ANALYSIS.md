# Budget, ranking, and deployment regret: analysis notes

Frozen input: six-model report, 2026-09-14 lineage edition. Descriptive observed means; no new model calls, rescoring, or significance claims.

## 1. Budget tightening is a strong effect, but not uniform across metrics

- Search F1: 6/6 complete models decline Free→Tight; model-macro mean 61.12 → 50.68 → 17.29; median decline 46.86 points.
- Audit EA: 6/6 complete models decline Free→Tight; model-macro mean 80.29 → 69.83 → 55.66; median decline 21.87 points.
- Audit LA: 4/6 complete models decline Free→Tight; model-macro mean 84.44 → 84.24 → 78.91; median decline 8.14 points.
- HPO Gap0: 4/5 complete models decline Free→Tight; model-macro mean 90.59 → 91.23 → 85.79; median decline 8.83 points.

Search and evidence accuracy are the strong central results. Label accuracy falls less and is not monotonic for every model; it should not substitute for evidential correctness. HPO is more heterogeneous: four of five complete models decline. Gemini aggregate HPO is incomplete, and DeepSeek Gap0 includes normal no-config outcomes under the existing scoring rule.

## 2. Best model depends on task and deployment budget

Seven transparent dimensions = two Search families, two Audit metrics, three HPO families. Audit EA and LA are correlated measures of the same tasks, not independent datasets.

| Dimension | Comparable models | Free leader (score) | Tight leader (score) | Free-leader deployment regret |
| --- | ---: | --- | --- | ---: |
| Search whois | 6 | Gemini (73.86) | GLM (23.06) | 2.63–2.63 |
| Search whatis | 6 | Gemini (69.93) | DeepSeek (15.93) | 1.08–1.08 |
| Audit evidence accuracy | 6 | Gemini (97.59) | Gemini (72.10) | 0.00–0.00 |
| Audit label accuracy | 6 | Gemini (97.29) | Gemini (88.24) | 0.00–0.00 |
| ParamNet | 5 | GPT (97.31) | GPT (85.69) | 0.00–0.00 |
| NAS101 | 5 | GLM (99.06) | GPT (97.03) | 6.27–6.27 |
| NAS201 | 6 | Kimi (99.77) | Gemini (94.87) | 0.21–0.21 |

Six models are complete at both endpoints for five dimensions; leaders change in **3/5**, not 7/7. ParamNet and NAS101 lack complete Gemini endpoints. With the same five fully complete models in every dimension, leaders change in **2/7**. Counting same-complete models separately per dimension gives 4/7; neither supports “all 7.” At Tight, different dimensions favor GLM, DeepSeek, Gemini, or GPT, so there is no universal best model.

## 3. Selecting a model under Free can incur Tight deployment regret

Regret = best Tight mean in the same eligible model set − Tight mean of the Free leader. Select with the Free mean, deploy/evaluate with the Tight mean. The dataset is descriptive and retrospective; it is not an independently held-out model-selection trial. A Free tie is reported as a regret interval rather than broken after observing Tight.

| HPO task | Comparable models | Free leader | Tight leader | Tight regret, Gap points |
| --- | ---: | --- | --- | ---: |
| nasbench101:A | 6 | Gemini | GPT | 2.32–2.32 |
| nasbench101:B | 6 | Gemini | Gemini | 0.00–0.00 |
| nasbench101:C | 5 | GLM | GPT | 2.48–2.48 |
| nasbench201:cifar10-valid | 6 | Kimi / Gemini | GPT | 1.99–7.45 |
| nasbench201:cifar100 | 6 | Kimi / Gemini | Gemini | 0.00–1.10 |
| nasbench201:imagenet16-120 | 6 | Kimi | Kimi | 0.00–0.00 |
| paramnet:adult:steps | 5 | GPT | Kimi | 5.34–5.34 |
| paramnet:higgs:steps | 6 | Gemini | Gemini | 0.00–0.00 |
| paramnet:letter:steps | 5 | Kimi | GPT | 1.13–1.13 |

The maximum is **7.45 Gap points**, depending on the Free tie in CIFAR10 (Gemini/Kimi). Selecting Gemini incurs 1.99; selecting Kimi incurs 7.45. The largest regret with a unique Free leader is **5.34** on Adult among five complete models. Across all nine tasks with fixed five-model eligibility, the maximum is **11.39** on Higgs; Gemini’s addition changes the Free leader there and removes that selection regret. These are different estimands and must not be combined. The abstract’s **33.9** is not supported by current task means.

A useful central example without a Free tie is NAS101: among five complete models, GLM leads Free (99.06), GPT leads Tight (97.03), and selecting GLM leaves 6.27 Gap points at Tight. This is a family-average comparison, not the nine-task maximum.

## Suggested paper framing

Feedback scarcity reduces performance and changes which capabilities are useful. The ranking effect is deployment-specific rather than a universal reshuffle: Free leadership is informative but not sufficient for budgeted selection. Importantly, ranking change and practical loss are different quantities: NAS201 changes family leader by only 0.21 Gap points, while NAS101 has 6.27 points of five-model deployment regret. Report regret alongside ranks to avoid overstating near-ties.

## Reproducibility

- `dimension_scores.csv`: all seven dimensions × six models × three budgets, including explicit missingness.
- `dimension_rankings.csv`: same-complete endpoint sets and fixed-five-model sensitivity.
- `hpo_task_scores.csv`: all nine tasks, strict Gap and adopted Gap0, derivation and source record.
- `hpo_task_regret.csv`: all nine task regret intervals and exact model eligibility.
- `budget_effects.csv`: per-model budget effects.
- `checks_and_summary.json`: deterministic assertions, source hashes, unrounded aggregate values.
- 162 task means independently checked against repeat rows; 72 derived means checked against frozen family/all Gap0. DeepSeek normal no-config zero count = 11; no missing Gemini score is filled.
