#!/usr/bin/env python3
"""Read-only recomposition of frozen PoolAct setting means (no rescoring)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

W = Path('/lustrefs/users/chufan.shi/codex_space_tn')
SOURCE = W / 'publication/five_model_report_20260911/results/six-models-lineage-20260914'
OUT = Path(__file__).resolve().parent
MODELS = ['kimi-k3', 'glm-5.3', 'qwen3.8-2.4t-a95b-fp8',
          'deepseek-v4-flash-0731', 'gpt-5.6-sol', 'gemini-3.8-flash-medium']
LABEL = dict(zip(MODELS, ['Kimi', 'GLM', 'Qwen', 'DeepSeek', 'GPT', 'Gemini']))
SCENARIOS = ['restricted_search', 'evidence_audit', 'tuning']
PRIMARY = dict(zip(SCENARIOS, ['f1_mv', 'evidence_acc_mv', 'gap0_mi']))
STRATEGIES = ['naive', 'cached', 'poolact']
REGIMES = ['cost_moderate', 'cost_tight']


def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def number(x):
    return float(x) if x not in ('', None) else None


def complete_mean(row):
    if row is None:
        return None
    value = number(row['full_mean'])
    if value is not None:
        assert int(row['expected_items']) == int(row['complete_items'])
        assert int(row['missing_units']) == 0
    return value


def main():
    rows = list(csv.DictReader((SOURCE / 'absolute_settings.csv').open()))
    groups = defaultdict(dict)
    for row in rows:
        if row['system'] == 'poolact' and row['slice_kind'] == 'all' and row['slice'] == 'all':
            key = tuple(row[x] for x in ['model', 'scenario', 'regime', 'metric'])
            assert row['strategy'] not in groups[key]
            groups[key][row['strategy']] = row
    contrasts = []
    for (model, scenario, regime, metric), cells in sorted(groups.items()):
        assert set(cells) == set(STRATEGIES)
        scale = 100.0 if cells['poolact']['unit'] == 'fraction' else 1.0
        vals = {s: complete_mean(cells[s]) for s in STRATEGIES}
        complete = all(v is not None for v in vals.values())
        record = dict(model=model, scenario=scenario, regime=regime, metric=metric,
                      reported_unit='0-100' if scale == 100 else cells['poolact']['unit'],
                      complete_three_strategy=complete)
        for s in STRATEGIES:
            record[s] = vals[s] * scale if vals[s] is not None else None
            record[s + '_raw'] = vals[s]
            record[s + '_complete_items'] = cells[s]['complete_items']
            record[s + '_expected_items'] = cells[s]['expected_items']
            record[s + '_cohort'] = cells[s]['cohort_id']
            record[s + '_source_input'] = cells[s]['source_input']
            record[s + '_source_row'] = cells[s]['source_row']
        p = vals['poolact']
        for b in ['naive', 'cached']:
            v = vals[b]
            record['delta_vs_' + b] = (p - v) * scale if p is not None and v is not None else None
            record['relative_percent_vs_' + b] = (p / v - 1) * 100 if p is not None and v not in (None, 0) else None
        record['delta_vs_stronger_baseline'] = (p - max(vals['naive'], vals['cached'])) * scale if complete else None
        contrasts.append(record)
    assert len(contrasts) == 144
    write_csv('poolact_all_metrics.csv', contrasts)
    by_key = {(r['model'], r['scenario'], r['regime'], r['metric']):r for r in contrasts}
    tuning_spread = []
    for model in MODELS:
        for regime in REGIMES:
            mi = by_key[model, 'tuning', regime, 'gap0_mi']
            strict = by_key[model, 'tuning', regime, 'gap_mi']
            bon = by_key[model, 'tuning', regime, 'gap0_bon']
            for strategy in STRATEGIES:
                if mi[strategy] is None or strict[strategy] is None:
                    assert mi[strategy] is strict[strategy]
                else:
                    assert math.isclose(mi[strategy], strict[strategy], rel_tol=0, abs_tol=1e-10)
            tuning_spread.append(dict(
                model=model, regime=regime,
                complete_three_strategy=mi['complete_three_strategy'],
                **{s+'_bon_minus_mi': bon[s]-mi[s] if bon[s] is not None and mi[s] is not None else None for s in STRATEGIES},
            ))
    write_csv('nas_best_minus_mean.csv', tuning_spread)
    primaries = [r for r in contrasts if r['metric'] == PRIMARY[r['scenario']]]
    assert len(primaries) == 36
    assert sum(r['complete_three_strategy'] for r in primaries) == 33
    assert sum(r['delta_vs_stronger_baseline'] > 0 for r in primaries if r['complete_three_strategy']) == 29
    write_csv('poolact_primary.csv', primaries)
    summaries = []
    for scenario in SCENARIOS:
        for regime in REGIMES:
            matched = [r for r in primaries if r['scenario'] == scenario and r['regime'] == regime and r['complete_three_strategy']]
            d = dict(scenario=scenario, regime=regime, metric=PRIMARY[scenario],
                     matched_models=len(matched), models=';'.join(sorted(r['model'] for r in matched)))
            for s in STRATEGIES:
                d[s + '_model_macro'] = statistics.mean(r[s] for r in matched)
            for baseline in ['naive', 'cached', 'stronger_baseline']:
                deltas = [r['delta_vs_' + baseline] for r in matched]
                d['mean_delta_vs_' + baseline] = statistics.mean(deltas)
                d['median_delta_vs_' + baseline] = statistics.median(deltas)
                d['positive_vs_' + baseline] = sum(v > 0 for v in deltas)
                d['min_delta_vs_' + baseline] = min(deltas)
                d['max_delta_vs_' + baseline] = max(deltas)
            summaries.append(d)
    write_csv('poolact_scenario_summary.csv', summaries)
    tight_search = [r for r in primaries if r['scenario'] == 'restricted_search' and r['regime'] == 'cost_tight']
    checks = dict(
        primary_complete_groups=33,
        primary_planned_groups=36,
        primary_win_both=29,
        tight_win_both=sum(r['delta_vs_stronger_baseline'] > 0 for r in primaries if r['regime'] == 'cost_tight' and r['complete_three_strategy']),
        tight_complete=sum(r['complete_three_strategy'] for r in primaries if r['regime'] == 'cost_tight'),
        max_search_relative_gain_naive=max(r['relative_percent_vs_naive'] for r in tight_search),
        max_search_relative_gain_naive_model=max(tight_search, key=lambda r:r['relative_percent_vs_naive'])['model'],
        median_search_tight_relative_gain_naive=statistics.median(r['relative_percent_vs_naive'] for r in tight_search),
        median_search_tight_absolute_gain_naive=statistics.median(r['delta_vs_naive'] for r in tight_search),
        median_search_tight_absolute_gain_cached=statistics.median(r['delta_vs_cached'] for r in tight_search),
        search_tight_macro_relative_gain_naive=(statistics.mean(r['poolact_raw'] for r in tight_search) / statistics.mean(r['naive_raw'] for r in tight_search) - 1) * 100,
        interpretation='Descriptive model macro means within each scenario only; no pooled cross-scenario score, significance claim, or causal attribution.',
    )
    (OUT / 'checks.json').write_text(json.dumps(checks, indent=2, ensure_ascii=False) + '\n')
    inventory = []
    for name in ['absolute_settings.csv', 'main_poolact.csv', 'SOURCE_INDEX.json', 'SOURCE_SELECTION.csv']:
        p = SOURCE / name
        data = p.read_bytes()
        inventory.append(dict(path=str(p), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    (OUT / 'inputs.json').write_text(json.dumps(dict(
        inputs=inventory,
        method='Use frozen full_mean values only, no known_subset substitution. Source rows are 1-based CSV data-record indices, excluding header. Display scales fractions by 100; Gap scores retain points.',
        missingness='Gemini Search Moderate naive missing one of 39 questions; tuning incomplete strategy cells remain unknown. Contrast to a complete single baseline remains available even when the three-way group is incomplete.',
        no_rescoring=True,
    ), indent=2, ensure_ascii=False) + '\n')
    lines = ['# PoolAct quantitative analysis', '',
             'Frozen six-model data; contrasts below are PoolAct minus the baseline. Search/Audit are percentage points, tuning is Gap points. N4 search uses 39 whois questions. Audit uses 13 documents; N4 tuning uses NAS101 A/B/C, each with three repeats. A missing full mean stays unknown.', '',
             '| Model | Budget | Search F1-MV Δnaive / Δcached | Audit EA-MV Δnaive / Δcached | NAS Gap-MI Δnaive / Δcached |',
             '| --- | --- | --- | --- | --- |']
    lookup = {(r['model'],r['scenario'],r['regime']):r for r in primaries}
    fmt = lambda x: 'unknown' if x is None else f'{x:+.2f}'
    for model in MODELS:
        for regime in REGIMES:
            cells=[]
            for scenario in SCENARIOS:
                r=lookup[model,scenario,regime]
                cells.append(fmt(r['delta_vs_naive'])+' / '+fmt(r['delta_vs_cached']))
            lines.append('| '+ ' | '.join([LABEL[model], regime.removeprefix('cost_'), *cells])+' |')
    lines += ['', '## Scenario-level descriptive summaries', '',
              '| Scenario | Budget | Complete models | Naive / Cached / PoolAct | PoolAct gain over naive / cached |',
              '| --- | --- | --- | --- | --- |']
    for r in summaries:
        lines.append('| '+' | '.join([r['scenario'],r['regime'],str(r['matched_models']),
                     ' / '.join(f"{r[s+'_model_macro']:.2f}" for s in STRATEGIES),
                     f"{r['mean_delta_vs_naive']:+.2f} / {r['mean_delta_vs_cached']:+.2f}"])+' |')
    lines += ['', '## Interpretation', '',
              '- Benefits are not confined to comparison with independent rollouts: PoolAct beats both naive and cached in 29/33 complete primary-setting groups, including 16/17 Tight groups.',
              '- Tight search improves over naive in all six models; gains over the stronger of naive/cached occur in five. Moderate search benefits are smaller / mixed: three of five complete groups beat both. The additional complete Gemini cached comparison is effectively flat/slightly negative, not promoted into a complete three-way comparison.',
              '- Audit evidence accuracy improves over both baselines in all twelve model-budget groups. Evidence gains exceed label gains in magnitude: an accuracy-only account would understate the coordination benefit. EA and LA are independently scored endpoints, not a joint correctness metric.',
              '- In the five complete NAS101 model groups, Tight mean individual Gap improves in every model. The gap between a strong best-of-four and the mean individual is smaller under PoolAct; the main improvement is often greater consistency across agents, not just a better best trajectory. BoN is oracle best-of-four, not a deployable selector.',
              '- Current N4 tuning strict Gap-MI equals Gap0-MI wherever complete; DeepSeek missing-final problems reside elsewhere in the selected dataset and do not explain current complete N4 gains.',
              '- The abstract maximum of 52% is not reproduced by current selected search F1-MV. Relative improvements must name their baseline and denominator: DeepSeek Tight is about +190.2% vs a 2.56 baseline, while Gemini Tight is about +63.5% (20.43→33.40); headline maxima are denominator-sensitive. Prefer the absolute cross-model range and scenario macro results.',
              '- No p-values or causal identification are asserted. Models are a fixed selected set; experiment groups include protocol-fixed replacements. Matching per-agent budgets does not force equal realized feedback spend or observations; trajectory analysis is needed for mechanism.', '']
    (OUT / 'NOTES.md').write_text('\n'.join(lines))
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
