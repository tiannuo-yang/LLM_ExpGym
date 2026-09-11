#!/usr/bin/env python3
"""Independent read-only arithmetic review; never imports the study analyzer.

Requires Python >=3.11 (the archived raw_answer CSV includes a literal NUL).
Reads only the delivered CSVs, oracle and rendered markdown; prints JSON.
No original raw records, archives, scoring code, model or accelerator are used.
"""
import csv
import hashlib
import html
import itertools
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
pins = {}
checks = Counter()
issues = []


def read(path):
    path = ROOT / path
    data = path.read_bytes()
    pins[str(path.relative_to(ROOT))] = {
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return data.decode()


def table(name):
    import io
    return list(csv.DictReader(io.StringIO(read('analysis/full_v2/' + name))))


def ok(condition, detail, category):
    checks[category] += 1
    if not condition:
        issues.append(detail)


def number(value):
    return None if value in ('', None, 'unknown') else float(value)


def avg(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def equal(got, want, detail, category='numeric_cells', display=False):
    if isinstance(want, bool):
        yes = got == str(want)
    elif isinstance(want, (list, dict)):
        yes = json.loads(got) == want
    elif isinstance(want, str):
        yes = got == want
    else:
        g = number(got)
        yes = g is None and want is None
        if g is not None and want is not None:
            yes = math.isclose(g, want, rel_tol=5.1e-6 if display else 2e-12,
                               abs_tol=5e-10 if display else 1e-10)
    ok(yes, {'at': detail, 'got': got, 'expected': want}, category)


def key(row, fields):
    return tuple(row[f] for f in fields)


def grouped(rows, fields):
    result = defaultdict(list)
    for row in rows:
        result[key(row, fields)].append(row)
    return result


UNIT = ['model', 'system', 'scenario', 'item', 'family', 'regime', 'strategy', 'N', 'outerrep']
SETTING = ['model', 'system', 'scenario', 'regime', 'strategy', 'N', 'metric',
           'unit', 'higher_is_better', 'scope', 'slice_kind', 'slice']
Q = {'f1', 'evidence_acc', 'label_acc', 'gap', 'raw_perf', 'f1_mi', 'f1_mv',
     'evidence_acc_mi', 'evidence_acc_mv', 'label_acc_mi', 'label_acc_mv',
     'gap_mi', 'gap_bon', 'raw_perf_mi', 'raw_perf_bon'}
execution = table('metrics_execution.csv')
normalized = table('normalized.csv')
terminals = table('raw_terminals.csv')
costs = table('all_attempt_costs.csv')
published = {name: table(name) for name in ('metrics.csv', 'absolute_settings.csv',
             'by_outerseed.csv', 'contrasts.csv')}

ok(len(normalized) == len({r['execution_id'] for r in normalized}) == 783,
   '783 unique execution identities', 'coverage')
ok(len(terminals) == len({(r['execution_id'], r['agent_id']) for r in terminals}) == 1881,
   '1881 unique agent identities', 'coverage')
ok(all(r['execution_complete'] == 'True' for r in normalized + terminals),
   'all executions/agents complete', 'coverage')
ok(len(execution) == len({(r['execution_id'], r['metric']) for r in execution}),
   'unique execution metric rows', 'coverage')
execution_ids = {r['execution_id'] for r in normalized}
ok({r['execution_id'] for r in execution} == execution_ids,
   'metric execution universe equals normalized', 'coverage')
expected_matrix = {('expgym', 'evidence_audit'): (13, 117, 117),
                   ('expgym', 'restricted_search'): (73, 219, 219),
                   ('expgym', 'tuning'): (9, 81, 81),
                   ('poolact', 'evidence_audit'): (13, 78, 312),
                   ('poolact', 'restricted_search'): (39, 234, 936),
                   ('poolact', 'tuning'): (3, 54, 216)}
matrix = {}
for k, rows in grouped(normalized, ['system', 'scenario']).items():
    counts = len({r['item'] for r in rows}), len(rows), sum(int(r['N']) for r in rows)
    matrix['/'.join(k)] = counts
    ok(counts == expected_matrix[k], {'matrix': k, 'got': counts}, 'coverage')
    for r in rows:
        ok(r['N'] == ('1' if r['system'] == 'expgym' else '4'), 'N=' + r['N'], 'coverage')
        if r['scenario'] == 'tuning':
            ok(int(r['seed']) == 2200 + 4 * int(r['outerrep']), 'tuning seed block', 'coverage')
        else:
            ok(r['outerrep'] == '0', 'R1 non-tuning', 'coverage')
        if r['system'] == 'poolact' and r['scenario'] == 'evidence_audit':
            ok(r['order'] == 'default', 'Pool Audit default order', 'coverage')

# Reconstruct order collapse from execution CSV, not metrics.csv components.
units = []
for k, rows in grouped(execution, UNIT + ['metric']).items():
    r = dict(rows[0])
    is_audit = r['system'] == 'expgym' and r['scenario'] == 'evidence_audit'
    ok(len(rows) == (3 if is_audit else 1), {'collapse_component_count': k}, 'collapse')
    if is_audit:
        ok({x['order'] for x in rows} == {'0', '1', '2'}, {'audit_orders': k}, 'collapse')
    values = [number(x['value']) for x in rows]
    known = sum(v is not None for v in values)
    r.update(value=avg(values) if known == len(rows) else None,
             known_component_subset_mean=avg(values), expected_components=len(rows),
             known_components=known, missing_components=len(rows) - known,
             orders=sorted({int(x['order']) if is_audit else x['order'] for x in rows}),
             seed_labels=sorted({int(x['seed']) for x in rows}))
    r['components'] = sorted([{'execution_id': x['execution_id'],
                              'order': int(x['order']) if is_audit else x['order'],
                              'seed': int(x['seed']), 'value': number(x['value'])}
                             for x in rows], key=lambda x: (str(x['order']), x['execution_id']))
    units.append(r)
unit_lookup = {key(r, UNIT + ['metric']): r for r in units}
ok(len(units) == len(published['metrics.csv']), 'collapsed row count', 'collapse')
ok(len({key(r, UNIT) for r in units}) == 705, '705 distinct analysis units', 'collapse')
for r in published['metrics.csv']:
    k = key(r, UNIT + ['metric'])
    expected = unit_lookup[k]
    for f in ('value', 'known_component_subset_mean', 'expected_components',
              'known_components', 'missing_components', 'components', 'orders', 'seed_labels'):
        equal(r[f], expected[f], ['metrics', k, f])


def summary(rows):
    items = grouped(rows, ['item'])
    means = [avg(x['value'] for x in v) for v in items.values()]
    partial = [avg(x['known_component_subset_mean'] for x in v) for v in items.values()]
    nk = sum(x['value'] is not None for x in rows)
    return dict(expected_outcomes=len(rows), known_outcomes=nk,
                missing_outcomes=len(rows) - nk, expected_items=len(items),
                known_items=sum(m is not None for m in means),
                complete_items=sum(all(x['value'] is not None for x in v) for v in items.values()),
                full_mean=avg(means) if nk == len(rows) else None,
                known_subset_item_weighted_mean=avg(means),
                known_component_subset_item_weighted_mean=avg(partial),
                expected_components=sum(x['expected_components'] for x in rows),
                known_components=sum(x['known_components'] for x in rows),
                missing_components=sum(x['missing_components'] for x in rows),
                min_repeats_per_item=min(len(v) for v in items.values()),
                max_repeats_per_item=max(len(v) for v in items.values()))


settings = defaultdict(list)
for r in units:
    slices = [('all', 'all'), ('family', r['family'])]
    if r['scenario'] == 'tuning':
        slices.append(('task', r['item']))
    for kind, name in slices:
        record = dict(r, slice_kind=kind, slice=name)
        settings[key(record, SETTING)].append(record)
absolute, blocks = {}, {}
for k, rows in settings.items():
    stats = summary(rows)
    repeat_rows = grouped(rows, ['outerrep'])
    block_stats = {rep: summary(v) for rep, v in repeat_rows.items()}
    item_sets = [frozenset(x['item'] for x in v) for v in repeat_rows.values()]
    bm = [v['full_mean'] for v in block_stats.values()]
    stats.update(repeat_blocks=len(repeat_rows), repeat_block_items_match=len(set(item_sets)) == 1,
                 descriptive_repeat_sd=statistics.stdev(bm) if len(bm) > 1 and all(x is not None for x in bm) and len(set(item_sets)) == 1 else None)
    absolute[k] = stats
    for rep, b in block_stats.items():
        b['seed_labels'] = sorted({seed for x in repeat_rows[rep] for seed in x['seed_labels']})
        blocks[k + rep] = b
for name, expected, extra in [('absolute_settings.csv', absolute, []),
                               ('by_outerseed.csv', blocks, ['outerrep'])]:
    ok(len(published[name]) == len(expected), {'table_count': name}, 'aggregate_universe')
    ok({key(r, SETTING + extra) for r in published[name]} == set(expected),
       {'table_keys': name}, 'aggregate_universe')
    for r in published[name]:
        k = key(r, SETTING + extra)
        for f, value in expected[k].items():
            equal(r[f], value, [name, k, f])

# Derive all legal paired contrasts from setting levels and full planned item/repeat keys.
contrasts = {}
for k, rows in settings.items():
    identity = dict(zip(SETTING, k))
    exp = identity['system'] == 'expgym'
    axis = 'regime' if exp else 'strategy'
    levels = ['cost_free', 'cost_moderate', 'cost_tight'] if exp else ['naive', 'cached', 'poolact']
    for target in levels[levels.index(identity[axis]) + 1:]:
        other = dict(identity, **{axis: target})
        other_k = key(other, SETTING)
        if other_k not in settings:
            continue
        aa = {key(r, ['item', 'outerrep']): r for r in rows}
        bb = {key(r, ['item', 'outerrep']): r for r in settings[other_k]}
        ok(aa.keys() == bb.keys(), {'paired_universe': k, 'target': target}, 'contrast_universe')
        pairs = []
        for pair, a in aa.items():
            av, bv = a['value'], bb[pair]['value']
            val = ((av - bv) if exp else (bv - av)) if av is not None and bv is not None else None
            pairs.append(dict(item=pair[0], value=val, known_component_subset_mean=val,
                              expected_components=1, known_components=int(val is not None), missing_components=int(val is None)))
        s = summary(pairs)
        effect = s.pop('full_mean')
        known_effect = s.pop('known_subset_item_weighted_mean')
        for f in ['known_component_subset_item_weighted_mean', 'expected_components', 'known_components', 'missing_components']:
            s.pop(f)
        base = absolute[k]['full_mean']
        s.update(comparison_axis=axis, effect_definition='baseline_minus_target' if exp else 'target_minus_baseline',
                 baseline_full_mean=base, target_full_mean=absolute[other_k]['full_mean'], effect=effect,
                 utility_effect=effect if identity['higher_is_better'] == 'True' else None,
                 known_paired_subset_effect=known_effect,
                 relative_effect_percent=100 * effect / abs(base) if effect is not None and base not in (0, None) else None)
        contrasts[k + (identity[axis], target)] = s
ok(len(contrasts) == len(published['contrasts.csv']), 'contrast row count', 'contrast_universe')
ok({key(r, SETTING + ['baseline', 'target']) for r in published['contrasts.csv']} == set(contrasts),
   'all contrast keys', 'contrast_universe')
for r in published['contrasts.csv']:
    k = key(r, SETTING + ['baseline', 'target'])
    for f, value in contrasts[k].items():
        equal(r[f], value, ['contrasts.csv', k, f])

# Independent HPO oracle transform from agent-level final-score CSV; no rescoring.
oracle = json.loads(read('study/provenance/oracle3.json'))['tasks']
terminal_groups = grouped(terminals, ['execution_id'])
exec_lookup = {(r['execution_id'], r['metric']): r for r in execution}
unknown_by_system = Counter()
incomplete_pools = 0
for (eid,), agents in terminal_groups.items():
    known = [r for r in agents if r['score_complete'] == 'True']
    for a in agents:
        if a['score_complete'] != 'True':
            unknown_by_system[a['system']] += 1
            ok(a['scenario'] == 'tuning' and a['raw_answer'] == '' and a['raw_answer_perf'] == '' and a['score_status'] == 'unscorable_missing_configuration',
               {'unknown_terminal': eid, 'agent': a['agent_id']}, 'terminal_semantics')
    pool = agents[0]['system'] == 'poolact'
    if pool and len(known) < len(agents):
        incomplete_pools += 1
        for (execution_id, metric), row in exec_lookup.items():
            if execution_id == eid and metric in Q:
                equal(row['value'], None, ['strict_pool_unknown', eid, metric], 'pool_policy')
    if agents[0]['scenario'] != 'tuning':
        continue
    o = oracle[agents[0]['item']]
    perfs = [number(a['raw_answer_perf']) for a in known]
    gaps = [max(0.0, 100 * (x - o['mean_perf']) / (o['best_perf'] - o['mean_perf'])) for x in perfs]
    complete = len(known) == len(agents)
    for metric, values in [('raw_perf', perfs), ('gap', gaps)]:
        mi = metric + ('_mi' if pool else '')
        equal(exec_lookup[eid, mi]['value'], avg(values) if complete else None, ['agent_transform', eid, mi], 'hpo_transform')
        equal(exec_lookup[eid, mi]['known_agent_subset_value'], avg(values), ['known_agent_transform', eid, mi], 'hpo_transform')
        if pool:
            bon = metric + '_bon'
            equal(exec_lookup[eid, bon]['value'], max(values) if complete else None, ['bon', eid, bon], 'hpo_transform')
            equal(exec_lookup[eid, bon]['known_agent_subset_value'], max(values) if values else None, ['known_bon', eid, bon], 'hpo_transform')
ok(dict(unknown_by_system) == {'expgym': 11, 'poolact': 81}, dict(unknown_by_system), 'terminal_semantics')

# Request ledger and per-execution inclusive token totals.
ok(len(costs) == len({r['request_id'] for r in costs}) == 14300, '14300 unique requests', 'costs')
totals = {f: sum(int(r[f]) for r in costs) for f in
          ['input_tokens', 'output_tokens', 'reasoning_tokens_included_in_output', 'total_tokens']}
ok(totals == dict(input_tokens=105359032, output_tokens=23345301,
                 reasoning_tokens_included_in_output=18484906, total_tokens=128704333), totals, 'costs')
for r in costs:
    ok(int(r['total_tokens']) == int(r['input_tokens']) + int(r['output_tokens']) and
       0 <= int(r['reasoning_tokens_included_in_output']) <= int(r['output_tokens']),
       {'inclusive_tokens': r['request_id']}, 'costs')
lengths = sum('length' in json.loads(r['finish_reasons']) for r in costs)
ok(lengths == 138, {'length': lengths}, 'costs')
for (eid,), rows in grouped(costs, ['execution_id']).items():
    for f in ('input_tokens', 'output_tokens'):
        equal(exec_lookup[eid, f]['value'], sum(int(r[f]) for r in rows if r['effective_slot'] == 'True'),
              ['execution_token_sum', eid, f], 'costs')

# All displayed quality/resource setting, difference and tuning-repeat rows.
display_fields = ['system', 'scenario', 'slice_kind', 'slice', 'regime', 'strategy', 'metric']
abs_display = {key(r, display_fields): r for r in published['absolute_settings.csv']}
repeat_display = {key(r, display_fields + ['outerrep']): r for r in published['by_outerseed.csv']}
con_display = {}
for r in published['contrasts.csv']:
    direction = (r['baseline'] + ' − ' + r['target']) if r['system'] == 'expgym' else (r['target'] + ' − ' + r['baseline'])
    con_display[(r['system'], r['scenario'], r['slice_kind'], r['slice'], r['regime'], r['metric'], direction)] = r
seen_abs, seen_con, seen_rep = set(), set(), set()
for name in ['report/README.zh.md', 'report/TABLES.md', 'report/REPEATS.md']:
    header = []
    for ln, line in enumerate(read(name).splitlines(), 1):
        if not line.startswith('| '):
            continue
        cells = [html.unescape(c.strip()) for c in line.split('|')[1:-1]]
        if cells[0] == '系统':
            header = cells
            continue
        if not cells or cells[0] not in ('expgym', 'poolact') or '层/切片' not in header:
            continue
        d = dict(zip(header, cells))
        kind, sl = d['层/切片'].split('/', 1)
        loc = [name, ln]
        if '完整均值' in d:
            k = (d['系统'], d['场景'], kind, sl, d['档位'], d['策略'], d['指标'])
            repeat = 'outerrep' in d
            if repeat:
                k += (d['outerrep'],)
                r = repeat_display[k]
                seen_rep.add(k)
            else:
                r = abs_display[k]
                seen_abs.add(k)
            for display, source in [('完整均值', 'full_mean'), ('missing', 'missing_outcomes')]:
                equal(d[display], number(r[source]), loc + [display], 'rendered_cells', True)
            equal(d['已知子集' if repeat else '已知子集均值'], number(r['known_subset_item_weighted_mean']), loc + ['subset'], 'rendered_cells', True)
            equal(d['单位'], r['unit'], loc + ['unit'], 'rendered_cells')
            equal(d['known/expected'], r['known_outcomes'] + '/' + r['expected_outcomes'], loc + ['denominator'], 'rendered_cells')
            if not repeat:
                equal(d['item 数'], number(r['expected_items']), loc + ['items'], 'rendered_cells')
                rep, sd = d['R / SD'].split(' / ')
                equal(rep, number(r['repeat_blocks']), loc + ['R'], 'rendered_cells')
                equal(sd, number(r['descriptive_repeat_sd']), loc + ['SD'], 'rendered_cells', True)
            else:
                equal(d['seed 标签'], json.loads(r['seed_labels']), loc + ['seed'], 'rendered_cells')
        elif '完整差值' in d:
            k = (d['系统'], d['场景'], kind, sl, d['档位'], d['指标'], d['差值方向'])
            r = con_display[k]
            seen_con.add(k)
            for display, source in [('完整差值', 'effect'), ('missing', 'missing_outcomes'), ('仅已知配对子集', 'known_paired_subset_effect')]:
                equal(d[display], number(r[source]), loc + [display], 'rendered_cells', True)
            equal(d['单位'], r['unit'], loc + ['unit'], 'rendered_cells')
            equal(d['配对 known/expected'], r['known_outcomes'] + '/' + r['expected_outcomes'], loc + ['denominator'], 'rendered_cells')
            effect = number(r['effect'])
            equal(d['百分点差'], (100 * effect if effect is not None else None) if r['unit'] == 'fraction' else '不适用', loc + ['percentage_points'], 'rendered_cells', True)
ok(seen_abs == set(abs_display), {'missing_rendered_settings': sorted(set(abs_display) - seen_abs)}, 'render_coverage')
ok(seen_con == set(con_display), {'missing_rendered_contrasts': sorted(set(con_display) - seen_con)}, 'render_coverage')
expected_repeats = {k for k, r in repeat_display.items() if r['scenario'] == 'tuning' and r['metric'] in Q}
ok(seen_rep == expected_repeats, {'missing_rendered_repeats': sorted(expected_repeats - seen_rep)}, 'render_coverage')

print(json.dumps(dict(status='PASS' if not issues else 'FAIL',
                     checks=dict(checks), issues=issues, input_pins=pins,
                     rows={**{k: len(v) for k, v in published.items()},
                           'metrics_execution.csv': len(execution), 'normalized.csv': len(normalized),
                           'raw_terminals.csv': len(terminals), 'all_attempt_costs.csv': len(costs)},
                     coverage=matrix, totals=totals, length_requests=lengths,
                     unscorable_agents=dict(unknown_by_system), incomplete_hpo_pools=incomplete_pools,
                     rendered_unique=dict(settings=len(seen_abs), contrasts=len(seen_con), tuning_repeats=len(seen_rep))),
                 ensure_ascii=False, indent=2))
sys.exit(bool(issues))
