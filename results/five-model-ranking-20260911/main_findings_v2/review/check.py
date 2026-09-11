#!/usr/bin/env python3
"""Independent report-only check. Does not import any author generator.

Reaggregates saved execution scores, not raw replies or evaluator outputs.
Source terminal CSVs are read only for classification/nullness; body fields are
never emitted. Prints a compact evidence summary, writes no files.
"""
import csv
import hashlib
import io
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['kimi-k3', 'glm-5.3', 'qwen3.8-2.4t-a95b-fp8', 'deepseek-v4-flash-0731', 'gpt-5.6-sol']
LABELS = dict(zip(MODELS, ['Kimi', 'GLM', 'Qwen', 'DeepSeek', 'GPT (medium)']))
BUDGETS = ['cost_free', 'cost_moderate', 'cost_tight']
ID = ['model', 'system', 'scenario', 'regime', 'strategy', 'slice_kind', 'slice']
checks = Counter()


def require(ok, label):
    if not ok:
        raise AssertionError(label)
    checks[label] += 1


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_csv(path):
    return list(csv.DictReader(io.StringIO(path.read_text())))


def near(x, y, label='numeric equality'):
    if x in ('', None) or y in ('', None):
        require(x in ('', None) and y in ('', None), label)
    else:
        require(math.isclose(float(x), float(y), rel_tol=0, abs_tol=1e-10), label)


def truth(x):
    require(x in ('True', 'False', 'true', 'false'), 'valid Boolean')
    return x.lower() == 'true'


def key(r, metric=False):
    return tuple(r[f] for f in ID + (['metric'] if metric else []))


manifest = json.loads((ROOT / 'GAP0_INPUTS.json').read_text())
data, originals, source_info = {}, {}, []
for s in manifest['sources']:
    raw = Path(s['local_source']).read_bytes()
    require(sha(raw) == s['source_sha256'] and len(raw) == s['source_bytes'], 'source SHA and size')
    original = list(csv.DictReader(io.StringIO(raw.decode())))
    require(len(original) == s['source_rows'], 'source row count')
    p = ROOT / s['projected_path']
    require(sha(p.read_bytes()) == s['projected_sha256'] and p.stat().st_size == s['projected_bytes'], 'projection SHA and size')
    projected = read_csv(p)
    require(len(projected) == s['projected_rows'], 'projection row count')
    selected = []
    for ordinal, r in enumerate(original, 1):
        if r['scenario'] != 'tuning':
            continue
        kind = s['projection_kind']
        if kind == 'absolute' and not (r['metric'] in ('gap', 'gap_mi', 'gap_bon') and r['slice_kind'] in ('all', 'family') and (r['system'] != 'poolact' or r['slice_kind'] == 'all')):
            continue
        if kind == 'metric' and r['metric'] not in ('Gap', 'gap', 'gap_mi', 'gap_bon'):
            continue
        selected.append(ordinal)
    require([int(p['source_row']) for p in projected] == selected, 'projection exhaustive selection')
    for p in projected:
        r = original[int(p['source_row']) - 1]
        terminal = json.loads(r['terminal_status']) if s['projection_kind'] == 'terminal' else None
        for field, actual in p.items():
            if field == 'source_row':
                continue
            if field == 'execution_id':
                expected = r.get('execution_id', r.get('job_id'))
            elif field == 'regime':
                expected = r.get('regime', r.get('budget'))
            elif field == 'outerrep':
                expected = {'2200': '0', '2204': '1', '2208': '2'}[r['seed']]
            elif field == 'metric' and r['metric'] == 'Gap':
                expected = {'single': 'gap', 'MI': 'gap_mi', 'BoN': 'gap_bon'}[r['endpoint']]
            elif field in ('terminal_classification', 'policy_version'):
                expected = terminal[field]
            elif field in ('raw_answer_is_null', 'raw_answer_perf_is_null'):
                expected = str(r[field.removesuffix('_is_null')] in ('', 'null'))
            elif field == 'model' and s['name'] != 'strict_absolute':
                expected = MODELS[3] if s['name'].startswith('deep') else MODELS[4]
                require(r['model'] == expected, 'original model identity')
            else:
                expected = r.get(field, '')
            require(actual == expected, 'source field mapping')
        if terminal:
            require(terminal['execution_complete'] == truth(p['execution_complete']), 'terminal embedded execution')
            require(terminal['score_complete'] == truth(p['score_complete']), 'terminal embedded score')
    data[s['name']], originals[s['name']] = projected, original
    source_info.append({'name': s['name'], 'source_sha256': sha(raw), 'projected_rows': len(projected)})

units = {}
non_hpo = {}
non_hpo_settings = []
for tag, model in [('deep', MODELS[3]), ('gpt', MODELS[4])]:
    all_terms = originals[tag + '_terminal']
    non = [r for r in all_terms if r['scenario'] != 'tuning']
    require(len(non) == 1584 and len(all_terms) == 1881, 'non-HPO denominator')
    require(all(truth(r['execution_complete']) and truth(r['score_complete']) for r in non), 'non-HPO execution and scoring complete')
    nulls = sum(r['raw_answer'] in ('', 'null') for r in non)
    empties = sum(r['score_status'] == 'scored_empty_prediction' for r in non)
    require(nulls == empties == (506 if tag == 'deep' else 0), 'non-HPO empty answer count')
    non_hpo[model] = dict(agent_count=len(non), raw_null=nulls, scored_empty_prediction=empties)
    extra_blanks = 0
    for r in non:
        if r['raw_answer'] in ('', 'null'):
            continue
        try:
            decoded = json.loads(r['raw_answer'])
        except (TypeError, ValueError):
            decoded = r['raw_answer']
        extra_blanks += isinstance(decoded, str) and not decoded.strip()
    require(extra_blanks == 0, 'no omitted JSON-empty or whitespace answer')
    grouped_non = defaultdict(list)
    for r in non:
        scenario = 'evidence_audit' if r['family'] == 'contract_nli' or r['scenario'] == 'evidence_audit' else r['scenario']
        grouped_non[(r['system'], scenario, r.get('regime', r.get('budget')), r['strategy'])].append(r)
    require(len(grouped_non) == 18, '18 non-HPO settings per model')
    for (system, scenario, budget, strategy), rs in grouped_non.items():
        non_hpo_settings.append(dict(model=model, system=system, scenario=scenario, regime=budget, strategy=strategy, planned=len(rs), raw_null=sum(r['raw_answer'] in ('', 'null') for r in rs), scored_empty=sum(r['score_status'] == 'scored_empty_prediction' for r in rs), exec_incomplete=sum(not truth(r['execution_complete']) for r in rs), score_incomplete=sum(not truth(r['score_complete']) for r in rs)))
    terms, metrics = defaultdict(list), defaultdict(dict)
    for t in data[tag + '_terminal']:
        terms[t['execution_id']].append(t)
    for m in data[tag + '_metric']:
        require(m['metric'] not in metrics[m['execution_id']], 'unique execution metric')
        metrics[m['execution_id']][m['metric']] = m
    require(set(terms) == set(metrics) and len(terms) == 135, 'complete execution identities')
    us = []
    for execution, ts in terms.items():
        t = ts[0]
        n = int(t['N'])
        require(len(ts) == n and sorted(int(x['agent_id']) for x in ts) == list(range(n)), 'complete member slots')
        require(set(metrics[execution]) == ({'gap'} if n == 1 else {'gap_mi', 'gap_bon'}), 'complete endpoint slots')
        for r in ts + list(metrics[execution].values()):
            require(all(t[f] == r[f] for f in ('model', 'system', 'scenario', 'family', 'item', 'regime', 'strategy', 'N', 'seed')), 'unit identity agreement')
        valid = 0
        for x in ts:
            require(truth(x['execution_complete']), 'executed terminal only')
            scored = truth(x['score_complete'])
            if scored:
                require(x['score_status'] == 'scored_final_answer' and not truth(x['raw_answer_is_null']) and not truth(x['raw_answer_perf_is_null']), 'valid scored configuration')
                valid += 1
            else:
                require(x['score_status'] == 'unscorable_missing_configuration' and x['terminal_classification'] == 'model_no_answer' and x['policy_version'] == 'task-abstention-v1', 'normal missing configuration')
                require(x['terminal_origin'] in ('', 'normal_loop_return') and truth(x['raw_answer_is_null']) and truth(x['raw_answer_perf_is_null']), 'missing is not execution failure')
        values, strict, saved = {}, {}, {}
        for metric, r in metrics[execution].items():
            strict[metric] = float(r['value']) if r['value'] else None
            saved[metric] = float(r['known_agent_subset_value']) if r['known_agent_subset_value'] else None
            require((strict[metric] is not None) == (valid == n), 'strict missingness retained')
            if r['expected_agents']:
                require(tuple(int(r[f]) for f in ('expected_agents', 'known_agents', 'missing_agents')) == (n, valid, n-valid), 'saved agent counts')
            require((saved[metric] is not None) == (valid > 0), 'subset score existence')
            if valid == n:
                near(strict[metric], saved[metric], 'full versus subset score')
            values[metric] = 0 if not valid else saved[metric] * (valid / n if metric == 'gap_mi' else 1)
            require(values[metric] >= 0, 'nonnegative utility')
        us.append(dict(t, n=n, valid=valid, values=values, strict=strict, saved=saved, terminals=ts))
    for system in ('expgym', 'poolact'):
        subset = [u for u in us if u['system'] == system]
        item_set = {u['item'] for u in subset}
        require(len(item_set) == (9 if system == 'expgym' else 3), 'planned tuning item count')
        wanted = {(i, b, s, seed) for i in item_set for b in (BUDGETS if system == 'expgym' else BUDGETS[1:]) for s in (['single'] if system == 'expgym' else ['naive', 'cached', 'poolact']) for seed in ['2200', '2204', '2208']}
        actual = [(u['item'], u['regime'], u['strategy'], u['seed']) for u in subset]
        require(len(set(actual)) == len(actual) and set(actual) == wanted, 'planned Cartesian product')
    units[model] = us

non_meta = json.loads((ROOT / 'NON_HPO_OUTPUTS.json').read_text())
sort_non = lambda r: tuple(r[f] for f in ('model', 'system', 'scenario', 'regime', 'strategy'))
require(sorted(non_hpo_settings, key=sort_non) == sorted(non_meta['settings'], key=sort_non), 'all non-HPO settings exact')
for r in non_meta['totals']:
    actual = non_hpo[r['model']]
    require(r['planned'] == actual['agent_count'] and r['raw_null'] == actual['raw_null'] and r['scored_empty'] == actual['scored_empty_prediction'] and r['exec_incomplete'] == r['score_incomplete'] == 0, 'non-HPO total exact')
for s in non_meta['sources']:
    known = next(x for x in manifest['sources'] if x['projection_kind'] == 'terminal' and x['local_source'] == s['path'])
    require(s['bytes'] == known['source_bytes'] and s['sha256'] == known['source_sha256'] and s['source_rows'] == known['source_rows'] and s['selected_rows'] == 1584, 'non-HPO source identity')


def item_average(selected, metric, which):
    items = defaultdict(list)
    for u in selected:
        items[u['item']].append(u[which][metric])
    require(all(len(v) == 3 for v in items.values()), 'three repeats per item')
    if any(x is None for vals in items.values() for x in vals):
        return None
    return mean(mean(vals) for vals in items.values())


absolute = {key(r, True): r for r in data['strict_absolute']}
settings = read_csv(ROOT / 'gap0_settings.csv')
coverage = read_csv(ROOT / 'missing_output_summary.csv')
require(len(settings) == len({key(r, True) for r in settings}) == 120, '120 unique settings')
require(len(coverage) == len({key(r) for r in coverage}) == 90, '90 unique coverage rows')
setting_idx = {key(r, True): r for r in settings}
coverage_idx = {key(r): r for r in coverage}
for r in settings:
    metric = r['metric'].replace('gap0', 'gap')
    native = absolute[(*key(r), metric)]
    near(r['strict_value'], native['full_mean'], 'original strict endpoint preserved')
    n = int(native['N'])
    c = coverage_idx[key(r)]
    if r['model'] in units:
        selected = [u for u in units[r['model']] if all(u[f] == r[f] for f in ('system', 'regime', 'strategy')) and (r['slice_kind'] == 'all' or u['family'] == r['slice'])]
        require(len(selected) == int(native['expected_outcomes']), 'expected execution denominator')
        require(len({u['item'] for u in selected}) == int(native['expected_items']), 'expected item denominator')
        require(sum(u['strict'][metric] is not None for u in selected) == int(native['known_outcomes']), 'known execution denominator')
        near(r['value'], item_average(selected, metric, 'values'), 'independent Gap0 aggregate')
        near(r['strict_value'], item_average(selected, metric, 'strict'), 'independent strict aggregate')
        k = sum(u['valid'] for u in selected)
        total = sum(u['n'] for u in selected)
        all_valid = sum(u['valid'] == u['n'] for u in selected)
        any_valid = sum(u['valid'] > 0 for u in selected)
        member_metric = 'gap' if n == 1 else 'gap_mi'
        conditional = sum((u['saved'][member_metric] or 0) * u['valid'] for u in selected) / k if k else None
        reasons = Counter(x['termination_reason'] or 'not_exported_in_terminal_projection' for u in selected for x in u['terminals'] if not truth(x['score_complete']))
        evidence = 'explicit_per_agent_normal_terminal_and_saved_scores'
    else:
        require(native['expected_outcomes'] == native['known_outcomes'] and native['min_repeats_per_item'] == native['max_repeats_per_item'] == '3', 'inherited complete aggregate')
        near(r['value'], native['full_mean'], 'complete Gap0 equals inherited Gap')
        k = total = int(native['expected_outcomes']) * n
        all_valid = any_valid = int(native['expected_outcomes'])
        conditional = absolute[(*key(r), 'gap_mi')]['full_mean'] if metric == 'gap_bon' else native['full_mean']
        reasons = {}
        evidence = 'previously_validated_complete_strict_endpoint_N_times_expected_outcomes'
    near(r['known_agent_mean'], conditional, 'conditional member mean')
    for obj in (r, c):
        require(int(obj['valid_agents']) == k and int(obj['planned_agents']) == total, 'member denominator')
        near(obj['valid_configuration_rate'], k / total, 'valid configuration rate')
        require(obj['valid_pools'] == (str(all_valid) if n == 4 else '') and obj['planned_pools'] == (str(total // n) if n == 4 else '') and obj['any_valid_pools'] == (str(any_valid) if n == 4 else ''), 'pool denominators')
    require(int(c['missing_configuration_agents']) == total-k and int(c['other_failure_agents']) == int(c['missing_units']) == 0, 'coverage failures and missing')
    require(c['expected_units'] == native['expected_outcomes'] and json.loads(c['termination_reason_counts']) == dict(reasons) and c['evidence'] == evidence, 'coverage source scope')

parent_rows = read_csv(ROOT.parent / 'absolute_settings.csv')
parent = {key(r, True): r for r in parent_rows}
exp = read_csv(ROOT / 'main_expgym.csv')
pool = read_csv(ROOT / 'main_poolact.csv')
family = read_csv(ROOT / 'main_family_rankings.csv')
require((len(exp), len(pool), len(family)) == (15, 30, 90), 'core row coverage')


def lookup(model, system, scenario, budget, strategy, metric, kind='all', sl='all'):
    k = (model, system, scenario, budget, strategy, kind, sl, metric)
    return float(setting_idx[k]['value']) if metric.startswith('gap0') else 100 * float(parent[k]['full_mean'])


for r in exp:
    scenario = {'Search': 'restricted_search', 'Audit': 'evidence_audit', 'HPO/NAS': 'tuning'}[r['scenario']]
    vs = [lookup(r['model'], 'expgym', scenario, b, 'single', r['metric']) for b in BUDGETS]
    for f, x in zip(['free', 'moderate', 'tight', 'free_minus_tight'], [*vs, vs[0]-vs[2]]):
        near(r[f], x, 'core ExpGym value')
for r in pool:
    scenario = {'Search': 'restricted_search', 'Audit': 'evidence_audit', 'NAS': 'tuning'}[r['scenario']]
    vs = [lookup(r['model'], 'poolact', scenario, r['regime'], s, r['metric']) for s in ['naive', 'cached', 'poolact']]
    for f, x in zip(['naive', 'cached', 'poolact', 'cached_minus_naive', 'poolact_minus_cached', 'poolact_minus_naive'], [*vs, vs[1]-vs[0], vs[2]-vs[1], vs[2]-vs[0]]):
        near(r[f], x, 'core PoolAct value')
family_groups = defaultdict(list)
for r in family:
    fam = r['family']
    scenario, kind, sl = {'Search whois': ('restricted_search', 'family', 'whois'), 'Search whatis': ('restricted_search', 'family', 'whatis'), 'Audit': ('evidence_audit', 'all', 'all'), 'ParamNet': ('tuning', 'family', 'paramnet'), 'NAS101': ('tuning', 'family', 'nasbench101'), 'NAS201': ('tuning', 'family', 'nasbench201')}[fam]
    v = lookup(r['model'], 'expgym', scenario, r['regime'], 'single', r['metric'], kind, sl)
    near(r['value'], v, 'family original score')
    family_groups[(fam, r['regime'])].append(r)
champions = {}
for (fam, budget), rs in family_groups.items():
    require(len(rs) == 5 and {r['model'] for r in rs} == set(MODELS), 'fixed five candidates')
    scale = 1 if rs[0]['metric'] == 'gap0' else 100
    vals = {r['model']: float(r['value']) / scale for r in rs}
    top = max(vals.values())
    winners = [m for m in MODELS if top - vals[m] <= 1e-12]
    champions[(fam, budget)] = winners
    for r in rs:
        require(truth(r['winner']) == (r['model'] in winners) and r['winner_set'] == ';'.join(winners) and r['candidate_count'] == '5', 'family winner')
        near(r['first_second_margin'], (top-sorted(vals.values(), reverse=True)[1])*scale, 'family runner-up margin')
for r in family:
    require(truth(r['free_to_tight_winner_changed']) == (champions[(r['family'], BUDGETS[0])] != champions[(r['family'], BUDGETS[2])]), 'family transition')
changed = [fam for fam in dict.fromkeys(r['family'] for r in family) if champions[(fam, BUDGETS[0])] != champions[(fam, BUDGETS[2])]]
require(changed == ['Search whatis', 'NAS101'], 'two family winner changes')

readme = (ROOT / 'README.zh.md').read_text()
lines = [line for line in readme.splitlines() if line.startswith('| ')]
for r in exp:
    label = r['scenario'] + ' / ' + {'f1': 'F1', 'evidence_acc': 'EA', 'gap0': 'Gap0'}[r['metric']]
    row = '| ' + ' | '.join([label, LABELS[r['model']], *(format(float(r[f]), '.2f') for f in ['free', 'moderate', 'tight']), format(float(r['free_minus_tight']), '+.2f')]) + ' |'
    require(row in lines, 'README ExpGym rendering')
for r in pool:
    label = r['scenario'] + ' / ' + {'f1_mv': 'F1-MV', 'evidence_acc_mv': 'EA-MV', 'gap0_mi': 'Gap0-MI'}[r['metric']]
    row = '| ' + ' | '.join([label, LABELS[r['model']], *(format(float(r[f]), '.2f') for f in ['naive', 'cached', 'poolact']), *(format(float(r[f]), '+.2f') for f in ['poolact_minus_naive', 'poolact_minus_cached'])]) + ' |'
    require(row in lines, 'README PoolAct rendering')
for fam in dict.fromkeys(r['family'] for r in family):
    cells = [fam + (' / Gap0' if fam in ('ParamNet', 'NAS101', 'NAS201') else '')]
    for b in BUDGETS:
        rs = family_groups[(fam, b)]
        win = champions[(fam, b)]
        value = next(r['value'] for r in rs if r['model'] == win[0])
        cells.append(' = '.join(LABELS[m] for m in win) + ' (' + format(float(value), '.2f') + ')')
    cells.append('是' if fam in changed else '否')
    require('| ' + ' | '.join(cells) + ' |' in lines, 'README family rendering')
for r in settings:
    pool_row = r['system'] == 'poolact'
    strict = format(float(r['strict_value']), '.2f') if r['strict_value'] else 'unknown (' + r['valid_pools' if pool_row else 'valid_agents'] + '/' + r['planned_pools' if pool_row else 'planned_agents'] + ')'
    cells = [LABELS[r['model']], 'Pool' if pool_row else 'ExpGym', r['slice'], r['regime'].replace('cost_', ''), r['strategy'], r['metric'], strict, format(float(r['value']), '.2f'), r['valid_agents'] + '/' + r['planned_agents'], r['valid_pools'] + '/' + r['planned_pools'] if pool_row else '—', format(float(r['known_agent_mean']), '.2f') if r['known_agent_mean'] else 'unknown']
    require('| ' + ' | '.join(cells) + ' |' in (ROOT / 'GAP0_DETAILS.zh.md').read_text(), 'detail setting rendering')
require(not re.search(r'job_[a-f0-9]|hpobench:|question[-_][0-9]|task[-_][0-9]', readme), 'no concrete item IDs in main text')
require(all(float(r['free_minus_tight']) > 0 for r in exp if r['scenario'] in ('Search', 'Audit')), 'Search and Audit all degrade')
require(next(float(r['free_minus_tight']) for r in exp if r['model'] == MODELS[3] and r['scenario'] == 'HPO/NAS') < 0, 'Deep tuning improves with tighter budget')
require(all(float(r['poolact_minus_naive']) > 0 for r in pool if r['regime'] == 'cost_tight' and r['scenario'] in ('Search', 'NAS')), 'Tight Search and NAS positive versus naive')
require(all(float(r['poolact_minus_naive']) < 0 for r in pool if r['model'] == MODELS[3] and r['scenario'] == 'Audit'), 'Deep Audit negative in both budgets')
require(next(float(r['poolact_minus_naive']) for r in pool if r['model'] == MODELS[4] and r['regime'] == 'cost_moderate' and r['scenario'] == 'NAS') < 0, 'GPT Moderate NAS negative')
for model, expected in [(MODELS[3], (70, 81, 135, 216, 10, 54)), (MODELS[4], (81, 81, 215, 216, 53, 54))]:
    singles = [u for u in units[model] if u['system'] == 'expgym']
    pools = [u for u in units[model] if u['system'] == 'poolact']
    actual = (sum(u['valid'] for u in singles), len(singles), sum(u['valid'] for u in pools), sum(u['n'] for u in pools), sum(u['valid'] == 4 for u in pools), len(pools))
    require(actual == expected, 'main coverage totals')
require(Counter(t['termination_reason'] for u in units[MODELS[4]] for t in u['terminals'] if not truth(t['score_complete'])) == {'Context token budget exceeded': 1}, 'GPT context limit classification')
require(Counter((t['terminal_origin'], t['termination_reason']) for u in units[MODELS[3]] for t in u['terminals'] if not truth(t['score_complete'])) == {('normal_loop_return', ''): 92}, 'Deep detailed stop reason not exported')
require('39道whois' in readme and '两系统的Search/HPO任务全集不同' in readme and 'Moderate−25.79、Tight−42.99' in readme, 'narrow prose fixes present')
require('DeepSeek/GPT各135个' in (ROOT / 'GAP0_DETAILS.zh.md').read_text(), 'detail typo fixed')
require('0/1584' in readme and '506/1584（31.9%）' in readme and '不再次补零或剔除' in readme, 'non-HPO count prose scope')
pending_links = []
for name in ('README.zh.md', 'GAP0_DETAILS.zh.md', 'SUMMARY_TEMPLATE.zh.md'):
    for target in re.findall(r'\]\(([^)]+)\)', (ROOT / name).read_text()):
        if target.startswith(('http:', 'https:', '#')):
            continue
        target = target.split('#')[0]
        if not (ROOT / target).exists():
            require(target in ('VALIDATION.json', 'REVIEW.md', 'REVIEW.json', 'PUBLICATION.json'), 'only publication-stage links may be pending')
            pending_links.append(target)
        else:
            checks['valid local report link'] += 1

repo = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip()
old_paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '9e11134af27102327d8c41dade83211ec5a26da2', '--', 'results/five-model-ranking-20260911'], cwd=repo, text=True).splitlines()
for path in old_paths:
    old = subprocess.check_output(['git', 'show', '9e11134af27102327d8c41dade83211ec5a26da2:' + path], cwd=repo)
    require(Path(repo, path).read_bytes() == old, 'previous detailed report file unchanged')

reviewed = ['README.zh.md', 'GAP0_DETAILS.zh.md', 'gap0_settings.csv', 'missing_output_summary.csv', 'main_expgym.csv', 'main_poolact.csv', 'main_family_rankings.csv', 'GAP0_INPUTS.json', 'NON_HPO_OUTPUTS.json', 'SUMMARY_TEMPLATE.zh.md', 'review/check.py']
print(json.dumps(dict(status='passed', independent=True, author_modules_imported=False, checks=dict(checks), sources=source_info, gap0_settings=120, independent_saved_execution_reaggregates=48, inherited_complete_endpoints=72, coverage_rows=90, core_expgym_rows=15, core_pool_rows=30, family_scores=90, champion_changes=changed, non_hpo=non_hpo, prior_report_files_unchanged=len(old_paths), pending_publication_links=sorted(set(pending_links)), reviewed_sha256={name: sha((ROOT / name).read_bytes()) for name in reviewed}, limits=['Saved per-execution full/subset Gap MI and BoN are inputs; individual Gap is not rescored.', 'Three complete models inherit 72 complete prior strict aggregates.', 'No model, evaluator, raw HTTP/trace, archive or GPU work.']), ensure_ascii=False, indent=2))
