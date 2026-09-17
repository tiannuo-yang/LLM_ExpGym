#!/usr/bin/env python3
"""Deterministic descriptive N1 budget/ranking/regret analysis; no rescoring.

Input scores remain immutable. All numbers are based on item means after repeat
means. Ties are retained at 1e-9 absolute tolerance, not resolved by model order.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

ROOT = Path('/lustrefs/users/chufan.shi/codex_space_tn')
SOURCE = ROOT / 'publication/five_model_report_20260911/results/six-models-lineage-20260914'
OUT = Path(__file__).resolve().parent
REGIMES = ('cost_free', 'cost_moderate', 'cost_tight')
SHORT = {'kimi-k3': 'Kimi', 'glm-5.3': 'GLM', 'qwen3.8-2.4t-a95b-fp8': 'Qwen',
         'deepseek-v4-flash-0731': 'DeepSeek', 'gpt-5.6-sol': 'GPT',
         'gemini-3.8-flash-medium': 'Gemini'}
MODELS = tuple(SHORT)
FIXED5 = tuple(m for m in MODELS if SHORT[m] != 'Gemini')
DEEP = 'deepseek-v4-flash-0731'
GEMINI = 'gemini-3.8-flash-medium'
DIMENSIONS = (
    ('Search whois', 'restricted_search', 'whois', 'f1'),
    ('Search whatis', 'restricted_search', 'whatis', 'f1'),
    ('Audit evidence accuracy', 'evidence_audit', 'evidence_audit', 'evidence_acc'),
    ('Audit label accuracy', 'evidence_audit', 'evidence_audit', 'label_acc'),
    ('ParamNet', 'tuning', 'paramnet', 'gap0'),
    ('NAS101', 'tuning', 'nasbench101', 'gap0'),
    ('NAS201', 'tuning', 'nasbench201', 'gap0'),
)


def read_csv(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


ABS = read_csv(SOURCE / 'absolute_settings.csv')
REP = read_csv(SOURCE / 'by_repeat.csv')
KEYS = ('model', 'scenario', 'slice_kind', 'slice', 'regime', 'metric')
IDX = {}
for number, row in enumerate(ABS, 1):
    if row['system'] != 'expgym':
        continue
    key = tuple(row[x] for x in KEYS)
    assert key not in IDX
    IDX[key] = dict(row, frozen_record=number)


def get(model, scenario, kind, slicename, regime, metric):
    return IDX.get((model, scenario, kind, slicename, regime, metric))


def value(row):
    return float(row['full_mean']) if row and row['full_mean'] != '' else None


def winners(scores):
    best = max(scores.values())
    return tuple(m for m in MODELS if m in scores and math.isclose(scores[m], best, abs_tol=1e-9, rel_tol=0))


def names(models):
    return ' / '.join(SHORT[m] for m in models)


def write_csv(name, rows):
    assert rows
    with (OUT / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


dimension_scores = []
dimension_ranking = []
for label, scenario, family, metric in DIMENSIONS:
    multiplier = 1 if scenario == 'tuning' else 100
    scores = {}
    for model in MODELS:
        scores[model] = {}
        for regime in REGIMES:
            row = get(model, scenario, 'family', family, regime, metric)
            x = value(row)
            scores[model][regime] = x * multiplier if x is not None else None
            dimension_scores.append(dict(
                dimension=label, model=model, regime=regime, metric=metric,
                score=scores[model][regime], unit='Gap points' if scenario == 'tuning' else '0-100',
                complete=x is not None, known_units=row['known_units'], expected_units=row['expected_units'],
                source_file='absolute_settings.csv', source_record=row['frozen_record']))
    complete_endpoint = tuple(m for m in MODELS if all(scores[m][r] is not None for r in (REGIMES[0], REGIMES[2])))
    for mode, available in (('same_complete_endpoint_models', complete_endpoint), ('fixed_five_models', FIXED5)):
        free = {m: scores[m][REGIMES[0]] for m in available}
        tight = {m: scores[m][REGIMES[2]] for m in available}
        fwin, twin = winners(free), winners(tight)
        regrets = [max(tight.values()) - tight[m] for m in fwin]
        dimension_ranking.append(dict(
            comparison=mode, dimension=label, metric=metric, n_models=len(available),
            included_models=';'.join(available), excluded_models=';'.join(m for m in MODELS if m not in available),
            free_leaders=';'.join(fwin), free_best=max(free.values()),
            tight_leaders=';'.join(twin), tight_best=max(tight.values()),
            free_leaders_tight_scores=';'.join(str(tight[m]) for m in fwin),
            leader_set_changed=set(fwin) != set(twin), no_common_leader=not set(fwin).intersection(twin),
            regret_min=min(regrets), regret_max=max(regrets)))
write_csv('dimension_scores.csv', dimension_scores)
write_csv('dimension_rankings.csv', dimension_ranking)

# Task Gap0 is already present for Gemini. For older five models, task-level
# strict Gap is used when complete; all their N1 HPO experiments executed.
# DeepSeek's 11 missing strict N1 scores are precisely normal no-config outcomes
# already represented as zero in the frozen family Gap0. Apply that existing
# convention to task means, and independently verify every family and all-task
# mean against the supplied Gap0. No failures or unexecuted work receive zero.
tasks = sorted({row['slice'] for row in ABS if row['system'] == 'expgym' and row['scenario'] == 'tuning' and row['slice_kind'] == 'task'})
assert len(tasks) == 9
task_scores = []
T = {}
repeat_checks = 0
deep_missing = 0
for model in MODELS:
    for task in tasks:
        family = task.split(':')[1]
        for regime in REGIMES:
            metric = 'gap0' if model == GEMINI else 'gap'
            row = get(model, 'tuning', 'task', task, regime, metric)
            known, expected = int(row['known_units']), int(row['expected_units'])
            assert expected == 3
            x = value(row)
            derivation = 'frozen_gap0' if metric == 'gap0' else 'complete_strict_gap_equals_gap0'
            if model == DEEP and x is None:
                x = float(row['known_subset_mean'] or 0) * known / expected
                derivation = 'normal_no_config_zero_as_existing_frozen_gap0'
                deep_missing += expected-known
            relevant = [r for r in REP if r['model'] == model and r['system'] == 'expgym' and r['scenario'] == 'tuning'
                        and r['slice_kind'] == 'task' and r['slice'] == task and r['regime'] == regime and r['metric'] == metric]
            assert len(relevant) == 3
            repeat_values = [value(r) for r in relevant]
            if model == DEEP:
                repeat_values = [v if v is not None else 0 for v in repeat_values]
            if all(v is not None for v in repeat_values):
                assert math.isclose(mean(repeat_values), x, abs_tol=1e-9)
            else:
                assert x is None
            repeat_checks += 1
            T[model, task, regime] = x
            task_scores.append(dict(model=model, task=task, family=family, regime=regime,
                                    gap0=x, strict_gap=value(get(model, 'tuning', 'task', task, regime, 'gap')),
                                    strict_known=known, expected=expected, gap0_complete=x is not None,
                                    derivation=derivation, source_record=row['frozen_record']))
assert deep_missing == 11
family_checks = 0
for model in MODELS:
    for regime in REGIMES:
        for family in ('paramnet', 'nasbench101', 'nasbench201', 'all'):
            samples = [T[model, task, regime] for task in tasks if family == 'all' or task.split(':')[1] == family]
            row = get(model, 'tuning', 'all' if family == 'all' else 'family', family, regime, 'gap0')
            if all(x is not None for x in samples):
                assert math.isclose(mean(samples), value(row), abs_tol=1e-9)
            else:
                assert value(row) is None
            family_checks += 1
write_csv('hpo_task_scores.csv', task_scores)

regret_rows = []
for task in tasks:
    endpoint_models = tuple(m for m in MODELS if T[m,task,REGIMES[0]] is not None and T[m,task,REGIMES[2]] is not None)
    for comparison, available in (('same_complete_endpoint_models', endpoint_models), ('fixed_five_models', FIXED5)):
        free = {m: T[m, task, REGIMES[0]] for m in available}
        tight = {m: T[m, task, REGIMES[2]] for m in available}
        fwin, twin = winners(free), winners(tight)
        regrets = [max(tight.values()) - tight[m] for m in fwin]
        missing = []
        for m in MODELS:
            if m not in available and comparison == 'same_complete_endpoint_models':
                for regime in (REGIMES[0], REGIMES[2]):
                    row = get(m, 'tuning', 'task', task, regime, 'gap0')
                    if value(row) is None:
                        missing.append(f'{m}:{regime}:{row["known_units"]}/{row["expected_units"]}')
        regret_rows.append(dict(
            comparison=comparison, task=task, family=task.split(':')[1], n_models=len(available),
            included_models=';'.join(available), excluded_models=';'.join(m for m in MODELS if m not in available),
            incomplete_endpoints=';'.join(missing), free_leaders=';'.join(fwin), free_best=max(free.values()),
            tight_leaders=';'.join(twin), tight_best=max(tight.values()),
            free_leaders_tight_scores=';'.join(str(tight[m]) for m in fwin),
            free_tied=len(fwin)>1, leader_set_changed=set(fwin)!=set(twin),
            no_common_leader=not set(fwin).intersection(twin),
            regret_min=min(regrets), regret_max=max(regrets)))
write_csv('hpo_task_regret.csv', regret_rows)

budget_rows = []
for label, scenario, metric in (('Search F1','restricted_search','f1'), ('Audit EA','evidence_audit','evidence_acc'),
                                ('Audit LA','evidence_audit','label_acc'), ('HPO Gap0','tuning','gap0')):
    scale = 1 if scenario == 'tuning' else 100
    for model in MODELS:
        values = [value(get(model,scenario,'all','all',regime,metric)) for regime in REGIMES]
        values = [x*scale if x is not None else None for x in values]
        complete = all(x is not None for x in values)
        f,m,t = values
        budget_rows.append(dict(scenario=label,model=model,free=f,moderate=m,tight=t,complete=complete,
                                free_minus_tight=f-t if complete else None,
                                relative_loss_pct=100*(f-t)/f if complete and f else None,
                                monotonic_decline=f>m>t if complete else None))
write_csv('budget_effects.csv', budget_rows)

summary = {'source_sha256':{f:hashlib.sha256((SOURCE/f).read_bytes()).hexdigest() for f in ('absolute_settings.csv','by_repeat.csv')},
           'repeat_mean_checks': repeat_checks, 'frozen_gap0_aggregation_checks':family_checks,
           'deepseek_normal_no_config_zero_count':deep_missing,
           'dimension_definition':[x[0] for x in DIMENSIONS], 'significance_test':False}
for mode in ('same_complete_endpoint_models','fixed_five_models'):
    rows = [r for r in dimension_ranking if r['comparison']==mode]
    summary[mode+'_dimension_leader_changes'] = sum(r['leader_set_changed'] for r in rows)
    summary[mode+'_dimension_count'] = len(rows)
    rs = [r for r in regret_rows if r['comparison']==mode]
    summary[mode+'_task_regret_max'] = max(r['regret_max'] for r in rs)
    summary[mode+'_task_regret_max_optimistic_tie'] = max(r['regret_min'] for r in rs)
    summary[mode+'_task_positive_regret_optimistic_tie'] = sum(r['regret_min']>1e-9 for r in rs)
    summary[mode+'_task_positive_regret_pessimistic_tie'] = sum(r['regret_max']>1e-9 for r in rs)
    summary[mode+'_task_regret_mean_optimistic_tie'] = mean(r['regret_min'] for r in rs)
    summary[mode+'_task_regret_mean_pessimistic_tie'] = mean(r['regret_max'] for r in rs)
complete6 = [r for r in dimension_ranking if r['comparison']=='same_complete_endpoint_models' and r['n_models']==6]
summary['complete_six_model_dimension_leader_changes'] = sum(r['leader_set_changed'] for r in complete6)
summary['complete_six_model_dimension_count'] = len(complete6)
summary['complete_six_model_hpo_tasks'] = sum(r['n_models']==6 for r in regret_rows if r['comparison']=='same_complete_endpoint_models')
assert (summary['complete_six_model_dimension_leader_changes'], summary['complete_six_model_dimension_count']) == (3, 5)
assert summary['fixed_five_models_dimension_leader_changes'] == 2
assert summary['same_complete_endpoint_models_dimension_leader_changes'] == 4
assert math.isclose(summary['same_complete_endpoint_models_task_regret_max'], 7.448358424481455, abs_tol=1e-9)
assert math.isclose(summary['fixed_five_models_task_regret_max'], 11.389404646294523, abs_tol=1e-9)
summary['headline_count_regression_assertions'] = 'PASS'
summary['budget'] = {}
for scenario in ('Search F1','Audit EA','Audit LA','HPO Gap0'):
    rows = [r for r in budget_rows if r['scenario']==scenario and r['complete']]
    summary['budget'][scenario] = dict(n_models=len(rows), n_decline=sum(r['free_minus_tight']>0 for r in rows),
                                      n_monotonic_decline=sum(r['monotonic_decline'] for r in rows),
                                      macro_free=mean(r['free'] for r in rows), macro_moderate=mean(r['moderate'] for r in rows),
                                      macro_tight=mean(r['tight'] for r in rows),
                                      loss_min=min(r['free_minus_tight'] for r in rows),loss_max=max(r['free_minus_tight'] for r in rows),
                                      loss_median=median(r['free_minus_tight'] for r in rows))
(OUT/'checks_and_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')

lines = ['# Budget, ranking, and deployment regret: analysis notes', '',
         'Frozen input: six-model report, 2026-09-14 lineage edition. Descriptive observed means; no new model calls, rescoring, or significance claims.', '',
         '## 1. Budget tightening is a strong effect, but not uniform across metrics', '']
for scenario,d in summary['budget'].items():
    lines.append(f'- {scenario}: {d["n_decline"]}/{d["n_models"]} complete models decline Free→Tight; model-macro mean {d["macro_free"]:.2f} → {d["macro_moderate"]:.2f} → {d["macro_tight"]:.2f}; median decline {d["loss_median"]:.2f} points.')
lines += ['', 'Search and evidence accuracy are the strong central results. Label accuracy falls less and is not monotonic for every model; it should not substitute for evidential correctness. HPO is more heterogeneous: four of five complete models decline. Gemini aggregate HPO is incomplete, and DeepSeek Gap0 includes normal no-config outcomes under the existing scoring rule.', '',
          '## 2. Best model depends on task and deployment budget', '',
          'Seven transparent dimensions = two Search families, two Audit metrics, three HPO families. Audit EA and LA are correlated measures of the same tasks, not independent datasets.', '',
          '| Dimension | Comparable models | Free leader (score) | Tight leader (score) | Free-leader deployment regret |',
          '| --- | ---: | --- | --- | ---: |']
for r in dimension_ranking:
    if r['comparison']!='same_complete_endpoint_models':continue
    lines.append(f'| {r["dimension"]} | {r["n_models"]} | {names(r["free_leaders"].split(";"))} ({r["free_best"]:.2f}) | {names(r["tight_leaders"].split(";"))} ({r["tight_best"]:.2f}) | {r["regret_min"]:.2f}–{r["regret_max"]:.2f} |')
lines += ['', 'Six models are complete at both endpoints for five dimensions; leaders change in **3/5**, not 7/7. ParamNet and NAS101 lack complete Gemini endpoints. With the same five fully complete models in every dimension, leaders change in **2/7**. Counting same-complete models separately per dimension gives 4/7; neither supports “all 7.” At Tight, different dimensions favor GLM, DeepSeek, Gemini, or GPT, so there is no universal best model.', '',
          '## 3. Selecting a model under Free can incur Tight deployment regret', '',
          'Regret = best Tight mean in the same eligible model set − Tight mean of the Free leader. Select with the Free mean, deploy/evaluate with the Tight mean. The dataset is descriptive and retrospective; it is not an independently held-out model-selection trial. A Free tie is reported as a regret interval rather than broken after observing Tight.', '',
          '| HPO task | Comparable models | Free leader | Tight leader | Tight regret, Gap points |',
          '| --- | ---: | --- | --- | ---: |']
for r in regret_rows:
    if r['comparison']!='same_complete_endpoint_models':continue
    lines.append(f'| {r["task"].removeprefix("hpobench:")} | {r["n_models"]} | {names(r["free_leaders"].split(";"))} | {names(r["tight_leaders"].split(";"))} | {r["regret_min"]:.2f}–{r["regret_max"]:.2f} |')
lines += ['', 'The maximum is **7.45 Gap points**, depending on the Free tie in CIFAR10 (Gemini/Kimi). Selecting Gemini incurs 1.99; selecting Kimi incurs 7.45. The largest regret with a unique Free leader is **5.34** on Adult among five complete models. Across all nine tasks with fixed five-model eligibility, the maximum is **11.39** on Higgs; Gemini’s addition changes the Free leader there and removes that selection regret. These are different estimands and must not be combined. The abstract’s **33.9** is not supported by current task means.', '',
          'A useful central example without a Free tie is NAS101: among five complete models, GLM leads Free (99.06), GPT leads Tight (97.03), and selecting GLM leaves 6.27 Gap points at Tight. This is a family-average comparison, not the nine-task maximum.', '',
          '## Suggested paper framing', '',
          'Feedback scarcity reduces performance and changes which capabilities are useful. The ranking effect is deployment-specific rather than a universal reshuffle: Free leadership is informative but not sufficient for budgeted selection. Importantly, ranking change and practical loss are different quantities: NAS201 changes family leader by only 0.21 Gap points, while NAS101 has 6.27 points of five-model deployment regret. Report regret alongside ranks to avoid overstating near-ties.', '',
          '## Reproducibility', '',
          '- `dimension_scores.csv`: all seven dimensions × six models × three budgets, including explicit missingness.',
          '- `dimension_rankings.csv`: same-complete endpoint sets and fixed-five-model sensitivity.',
          '- `hpo_task_scores.csv`: all nine tasks, strict Gap and adopted Gap0, derivation and source record.',
          '- `hpo_task_regret.csv`: all nine task regret intervals and exact model eligibility.',
          '- `budget_effects.csv`: per-model budget effects.',
          '- `checks_and_summary.json`: deterministic assertions, source hashes, unrounded aggregate values.',
          f'- {repeat_checks} task means independently checked against repeat rows; {family_checks} derived means checked against frozen family/all Gap0. DeepSeek normal no-config zero count = {deep_missing}; no missing Gemini score is filled.', '']
(OUT/'ANALYSIS.md').write_text('\n'.join(lines))
print(json.dumps(summary,indent=2))
