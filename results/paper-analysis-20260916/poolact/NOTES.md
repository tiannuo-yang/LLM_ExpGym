# PoolAct quantitative analysis

Frozen six-model data; contrasts below are PoolAct minus the baseline. Search/Audit are percentage points, tuning is Gap points. N4 search uses 39 whois questions. Audit uses 13 documents; N4 tuning uses NAS101 A/B/C, each with three repeats. A missing full mean stays unknown.

| Model | Budget | Search F1-MV Δnaive / Δcached | Audit EA-MV Δnaive / Δcached | NAS Gap-MI Δnaive / Δcached |
| --- | --- | --- | --- | --- |
| Kimi | moderate | +2.15 / +2.54 | +19.91 / +17.19 | +0.52 / +0.60 |
| Kimi | tight | +9.15 / +11.71 | +7.69 / +8.14 | +1.87 / +2.57 |
| GLM | moderate | +3.71 / +0.07 | +16.74 / +13.12 | +1.09 / +0.90 |
| GLM | tight | +9.15 / +9.15 | +15.84 / +16.29 | +8.40 / +7.76 |
| Qwen | moderate | +2.27 / +2.31 | +24.89 / +19.00 | +1.95 / +1.15 |
| Qwen | tight | +2.39 / -2.63 | +7.69 / +3.62 | +5.65 / +5.51 |
| DeepSeek | moderate | +1.05 / -0.47 | +24.89 / +22.17 | +2.01 / +2.47 |
| DeepSeek | tight | +4.88 / +3.17 | +9.50 / +9.50 | +12.09 / +12.31 |
| GPT | moderate | -1.71 / -3.17 | +2.71 / +2.26 | -0.14 / -0.24 |
| GPT | tight | +2.74 / +1.61 | +10.86 / +3.62 | +0.63 / +1.22 |
| Gemini | moderate | unknown / -0.07 | +17.19 / +10.41 | unknown / unknown |
| Gemini | tight | +12.97 / +12.50 | +4.98 / +2.26 | unknown / unknown |

## Scenario-level descriptive summaries

| Scenario | Budget | Complete models | Naive / Cached / PoolAct | PoolAct gain over naive / cached |
| --- | --- | --- | --- | --- |
| restricted_search | cost_moderate | 5 | 62.08 / 63.33 / 63.58 | +1.50 / +0.25 |
| restricted_search | cost_tight | 6 | 17.10 / 18.06 / 23.98 | +6.88 / +5.92 |
| evidence_audit | cost_moderate | 6 | 73.08 / 76.77 / 90.80 | +17.72 / +14.03 |
| evidence_audit | cost_tight | 6 | 59.95 / 62.14 / 69.38 | +9.43 / +7.24 |
| tuning | cost_moderate | 5 | 97.53 / 97.64 / 98.62 | +1.09 / +0.97 |
| tuning | cost_tight | 5 | 90.01 / 89.86 / 95.74 | +5.73 / +5.87 |

## Interpretation

- Benefits are not confined to comparison with independent rollouts: PoolAct beats both naive and cached in 29/33 complete primary-setting groups, including 16/17 Tight groups.
- Tight search improves over naive in all six models; gains over the stronger of naive/cached occur in five. Moderate search benefits are smaller / mixed: three of five complete groups beat both. The additional complete Gemini cached comparison is effectively flat/slightly negative, not promoted into a complete three-way comparison.
- Audit evidence accuracy improves over both baselines in all twelve model-budget groups. Evidence gains exceed label gains in magnitude: an accuracy-only account would understate the coordination benefit. EA and LA are independently scored endpoints, not a joint correctness metric.
- In the five complete NAS101 model groups, Tight mean individual Gap improves in every model. The gap between a strong best-of-four and the mean individual is smaller under PoolAct; the main improvement is often greater consistency across agents, not just a better best trajectory. BoN is oracle best-of-four, not a deployable selector.
- Current N4 tuning strict Gap-MI equals Gap0-MI wherever complete; DeepSeek missing-final problems reside elsewhere in the selected dataset and do not explain current complete N4 gains.
- The abstract maximum of 52% is not reproduced by current selected search F1-MV. Relative improvements must name their baseline and denominator: DeepSeek Tight is about +190.2% vs a 2.56 baseline, while Gemini Tight is about +63.5% (20.43→33.40); headline maxima are denominator-sensitive. Prefer the absolute cross-model range and scenario macro results.
- No p-values or causal identification are asserted. Models are a fixed selected set; experiment groups include protocol-fixed replacements. Matching per-agent budgets does not force equal realized feedback spend or observations; trajectory analysis is needed for mechanism.
