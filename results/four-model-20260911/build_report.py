#!/usr/bin/env python3
"""Report-only adapter: immutable published exports -> four-model tables.

No scorer, model client, raw dump, archive payload, or serving dependency is used.
Default operation reads local SHA-bound snapshots. --freeze-from-workspace is a
one-time, read-only git-object import into a new inputs/ directory.
"""
import argparse
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import re
import subprocess

MODELS = ['kimi-k3', 'glm-5.3', 'qwen3.8-2.4t-a95b-fp8', 'deepseek-v4-flash-0731']
LABELS = dict(zip(MODELS, ['Kimi-K3', 'GLM-5.3', 'Qwen3.8', 'DeepSeek-0731']))
REGIMES = ['cost_free', 'cost_moderate', 'cost_tight']
STRATEGIES = ['naive', 'cached', 'poolact']
QUALITY = {'f1', 'f1_mi', 'f1_mv', 'evidence_acc', 'evidence_acc_mi',
           'evidence_acc_mv', 'label_acc', 'label_acc_mi', 'label_acc_mv',
           'gap', 'gap_mi', 'gap_bon', 'raw_perf', 'raw_perf_mi', 'raw_perf_bon'}
IDENTITY = ['model', 'system', 'scenario', 'slice_kind', 'slice', 'regime', 'strategy', 'metric']
GH = 'https://github.com/tiannuo-yang/LLM_ExpGym/blob/'
OLD_REPORT = '0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91'
OLD_DATA = '6119f9d136c9ed1f06a7bedd7371be0deb9b5d59'
QWEN = 'ff8c572b6a00c33964a00a8fb991fd79dcf900e4'
DEEP = '8c79111de3398d12fb36ba349d8f4266f2330200'
OLD_ROOT = 'results/portable-eval-20260908/'
OLD_BUNDLE = OLD_ROOT + 'full_delivery_v5/kimi-k3-fixed8-composite-20260910/analysis/'
REPOS = {
    'old': 'publication/restart_v5_remote_base.oDCT5P/repo',
    'qwen': 'publication/qwen38_delivery_20260911',
    'deep': 'publication/deepseek_flash_delivery_20260911',
}


def specs():
    result = []
    def add(name, repo, commit, path, rows=None):
        result.append(dict(id=name, repo=repo, commit=commit, path=path, expected_rows=rows))
    old = OLD_ROOT + 'full_matrix_report_v1/'
    add('old_absolute', 'old', OLD_REPORT, old + 'aggregate_metrics.csv', 2270)
    add('old_blocks', 'old', OLD_REPORT, old + 'by_outerseed.csv', 5494)
    add('old_analysis_inputs', 'old', OLD_REPORT, old + 'INPUTS.json')
    add('old_costs', 'old', OLD_DATA, OLD_BUNDLE + 'dual_model_analysis_fixed8_v2/COSTS.json')
    add('old_setting_evidence', 'old', OLD_DATA, OLD_BUNDLE + 'claim_setting_preflight_v1/EVIDENCE.json')
    for tag, commit, root, version in [
            ('qwen', QWEN, 'results/qwen38-20260910/', 'full_v1'),
            ('deep', DEEP, 'results/deepseek-flash-0731-20260911/', 'full_v2')]:
        for name, filename, rows in [('absolute', 'absolute_settings.csv', 1245),
                                     ('blocks', 'by_outerseed.csv', 2857),
                                     ('contrasts', 'contrasts.csv', 1227),
                                     ('costs', 'COSTS.json', None),
                                     ('analysis_inputs', 'INPUTS.json', None)]:
            add(tag + '_' + name, tag, commit, root + 'analysis/' + version + '/' + filename, rows)
    add('qwen_accounting', 'qwen', QWEN, 'results/qwen38-20260910/study/accounting.json')
    add('deep_accounting', 'deep', DEEP, 'results/deepseek-flash-0731-20260911/study/allocation_final/ACCOUNTING.json')
    add('deep_provider', 'deep', DEEP, 'results/deepseek-flash-0731-20260911/study/provider_contract.json')
    return result


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def freeze(workspace, output):
    if (output / 'INPUTS.json').exists() or (output / 'inputs').exists():
        raise ValueError('Refusing to replace existing frozen inputs')
    prepared, entries = [], []
    for spec in specs():
        raw = subprocess.check_output(['git', '-C', str(workspace / REPOS[spec['repo']]),
                                       'show', spec['commit'] + ':' + spec['path']])
        local = 'inputs/' + spec['id'] + Path(spec['path']).suffix
        entry = {**spec, 'local_path': local, 'bytes': len(raw), 'sha256': sha(raw),
                 'url': GH + spec['commit'] + '/' + spec['path']}
        if spec['expected_rows'] is not None:
            actual = len(list(csv.DictReader(io.StringIO(raw.decode()))))
            if actual != spec['expected_rows']:
                raise ValueError((spec['id'], actual, spec['expected_rows']))
        prepared.append((local, raw))
        entries.append(entry)
    (output / 'inputs').mkdir(parents=True)
    for local, raw in prepared:
        (output / local).write_bytes(raw)
    (output / 'INPUTS.json').write_bytes(json_bytes({
        'schema': 'four-model-report-inputs-v1', 'files': entries,
        'scope': 'Exact published git blob snapshots; no raw/tar/scorer reads. '
                 'Native inputs and known-subset fields are preserved, not re-scored.',
        'template_url': GH + OLD_REPORT + '/' + OLD_ROOT + 'full_matrix_report_v1/README.zh.md',
    }))


def read_inputs(output):
    manifest = json.loads((output / 'INPUTS.json').read_bytes())
    entries = manifest['files']
    expected = {s['id']: s for s in specs()}
    if len(entries) != len(expected) or {e['id'] for e in entries} != set(expected):
        raise ValueError('Input identity/coverage mismatch')
    result = {}
    for entry in entries:
        spec = expected[entry['id']]
        if any(entry[k] != v for k, v in spec.items()):
            raise ValueError('Input pinned specification mismatch: ' + entry['id'])
        if entry['url'] != GH + spec['commit'] + '/' + spec['path']:
            raise ValueError('Moving or incorrect input URL')
        p = Path(entry['local_path'])
        if p.is_absolute() or '..' in p.parts or p.parts[0] != 'inputs':
            raise ValueError('Unsafe snapshot path')
        if (output / p).is_symlink():
            raise ValueError('Snapshot must not be a symlink')
        raw = (output / p).read_bytes()
        if (len(raw), sha(raw)) != (entry['bytes'], entry['sha256']):
            raise ValueError('Snapshot bytes/SHA mismatch: ' + entry['id'])
        if spec['expected_rows'] is not None:
            rows = list(csv.DictReader(io.StringIO(raw.decode())))
            if len(rows) != spec['expected_rows']:
                raise ValueError('Row count mismatch: ' + entry['id'])
            result[entry['id']] = [dict(row, source_input=entry['id'],
                source_row=str(i + 2), source_url=entry['url']) for i, row in enumerate(rows)]
        else:
            result[entry['id']] = json.loads(raw)
    return result


def number(value):
    if value in ('', None):
        return None
    v = float(value)
    if not math.isfinite(v):
        raise ValueError('Non-finite value')
    return v


def unit(metric):
    if metric.startswith('gap'):
        return 'Gap points'
    if metric.endswith('_tokens'):
        return 'tokens'
    if metric.endswith('_seconds'):
        return 'seconds'
    if metric in QUALITY or metric in {'budget_utilization', 'protocol_failure_rate'}:
        return 'fraction'
    return 'count'


def old_common(row):
    r = {k: row[k] for k in ['model', 'system', 'scenario', 'regime', 'strategy', 'metric',
                             'source_input', 'source_row', 'source_url']}
    s = row['slice']
    r['slice_kind'], r['slice'] = s.split('=', 1) if '=' in s else ('all' if s == 'all' else 'family', s)
    r.update(N='4' if row['system'] == 'poolact' else '1', unit=unit(row['metric']),
             higher_is_better='True' if row['metric'] in QUALITY else '',
             analysis_unit=row['unit'],
             scope='legacy_frozen_export; Audit_mean_once; pool_wall_whole_subprocess',
             expected_outcomes=row['n_rows'], known_outcomes=row['n_known_rows'],
             missing_outcomes=row['n_missing_rows'], expected_items=row['n_items'],
             complete_items=row.get('n_complete_items', row['n_known_rows']),
             full_mean=row['mean'],
             known_subset_item_weighted_mean=row['known_subset_mean_not_complete_endpoint'],
             original_logical_rows=row['n_original_logical_rows'],
             native_slice=row['slice'])
    # Old frozen exports in this study have no partially known aggregate: only
    # Pool feedback_visible is entirely unknown. Do not generalize to future data.
    if int(r['known_outcomes']) not in (0, int(r['expected_outcomes'])):
        raise ValueError('Old adapter needs an explicit partial-coverage implementation')
    r['known_items'] = r['expected_items'] if int(r['known_outcomes']) else '0'
    return r


def adapt_old(row, block=False):
    r = old_common(row)
    if block:
        r['outerrep'] = str(int(row['outerseed'].split('_')[-1]))
        r['seed_labels'] = row['requested_seed_block_label']
        r['min_repeats_per_item'] = r['max_repeats_per_item'] = '1'
    else:
        r['min_repeats_per_item'] = r['max_repeats_per_item'] = row['n_repeats']
        r['repeat_blocks'] = row['n_repeats']
        r['descriptive_repeat_sd'] = row['seedblock_descriptive_sd']
    return r


def adapt_new(row):
    r = dict(row)
    r['native_slice'] = row['slice']
    r['analysis_unit'] = ('pool_aggregate_N4' if r['system'] == 'poolact' else
                          'document_mean_3_fixed_orders' if r['scenario'] == 'evidence_audit' else 'single_trace')
    # expected_components means Audit orders, otherwise analysis outcomes. It is
    # NOT the number of member agents of an N4 pool. Preserve native semantics.
    return r


def check_rows(rows, block=False):
    seen = set()
    for r in rows:
        key = tuple(r[k] for k in IDENTITY) + ((r['outerrep'],) if block else ())
        if key in seen:
            raise ValueError('Duplicate aggregate identity: ' + str(key))
        seen.add(key)
        n, k, m = (int(r[x]) for x in ('expected_outcomes', 'known_outcomes', 'missing_outcomes'))
        if n <= 0 or k < 0 or m < 0 or n != k + m:
            raise ValueError('Invalid denominator')
        v = number(r['full_mean'])
        if (m > 0) != (v is None):
            raise ValueError('Full endpoint must be unknown iff required outcomes are missing')
        sd = number(r.get('descriptive_repeat_sd', ''))
        if sd is not None and (block or int(r['repeat_blocks']) < 2 or m):
            raise ValueError('Invalid repeat SD')
        if int(r['expected_items']) * int(r['max_repeats_per_item']) != n:
            raise ValueError('Unexpected repeat/item denominator')
        if r['metric'].startswith('gap') and v is not None and v < -1e-9:
            raise ValueError('Gap must be lower-clipped only; no upper cap')
    return seen


def legacy_contrasts(rows):
    idx = {tuple(r[k] for k in IDENTITY): r for r in rows}
    result = []
    for a in rows:
        axis = 'regime' if a['system'] == 'expgym' else 'strategy'
        levels = REGIMES if axis == 'regime' else STRATEGIES
        for target in levels[levels.index(a[axis]) + 1:]:
            key = dict(a, **{axis: target})
            b = idx[tuple(key[k] for k in IDENTITY)]
            if any(a[x] != b[x] for x in ['expected_outcomes', 'expected_items', 'min_repeats_per_item']):
                raise ValueError('Unmatched contrast denominator')
            # Every old endpoint is completely known or wholly absent; no
            # intersection is inferred from separate partially known subsets.
            complete = not int(a['missing_outcomes']) and not int(b['missing_outcomes'])
            av, bv = number(a['full_mean']), number(b['full_mean'])
            effect = (av - bv if axis == 'regime' else bv - av) if complete else None
            r = {k: a[k] for k in IDENTITY + ['N', 'unit', 'higher_is_better', 'scope',
                    'expected_outcomes', 'expected_items', 'min_repeats_per_item', 'max_repeats_per_item']}
            r.update(comparison_axis=axis, baseline=a[axis], target=target,
                     effect_definition='baseline_minus_target' if axis == 'regime' else 'target_minus_baseline',
                     baseline_full_mean=a['full_mean'], target_full_mean=b['full_mean'],
                     effect='' if effect is None else repr(effect),
                     utility_effect='' if effect is None or a['metric'] not in QUALITY else repr(effect),
                     known_paired_subset_effect='' if effect is None else repr(effect),
                     known_outcomes=a['expected_outcomes'] if complete else '0',
                     missing_outcomes='0' if complete else a['expected_outcomes'],
                     known_items=a['expected_items'] if complete else '0',
                     complete_items=a['expected_items'] if complete else '0',
                     source_input='old_absolute', source_row=a['source_row'],
                     source_row_target=b['source_row'], source_url=a['source_url'],
                     derivation='new descriptive difference of complete frozen unrounded means; no re-scoring')
            result.append(r)
    return result


def check_contrasts(rows):
    seen = set()
    for r in rows:
        axis = r['comparison_axis']
        key = tuple(r[k] for k in IDENTITY if k != axis) + (axis, r['baseline'], r['target'])
        if key in seen:
            raise ValueError('Duplicate contrast')
        seen.add(key)
        n, k, m = (int(r[x]) for x in ('expected_outcomes', 'known_outcomes', 'missing_outcomes'))
        if n <= 0 or min(k, m) < 0 or n != k + m:
            raise ValueError('Invalid contrast denominator')
        v = number(r['effect'])
        if (m > 0) != (v is None):
            raise ValueError('Incomplete contrast must remain unknown')
        if v is not None:
            a, b = number(r['baseline_full_mean']), number(r['target_full_mean'])
            wanted = a - b if r['effect_definition'] == 'baseline_minus_target' else b - a
            if not math.isclose(v, wanted, abs_tol=1e-10, rel_tol=1e-10):
                raise ValueError('Contrast direction/value mismatch')


def csv_bytes(rows):
    fields = list(dict.fromkeys(IDENTITY + [k for r in rows for k in r]))
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
    return f.getvalue().encode()


def fmt(value, signed=False):
    v = number(value)
    return 'unknown' if v is None else format(v, '+.6f' if signed else '.6f')


def cell(row, field='full_mean', signed=False):
    s = fmt(row.get(field, ''), signed)
    if s == 'unknown':
        s += ' (' + row['known_outcomes'] + '/' + row['expected_outcomes'] + ')'
    return s


def table(headers, rows):
    def line(row):
        return '| ' + ' | '.join(str(x).replace('|', '\\|').replace('\n', ' ') for x in row) + ' |\n'
    return line(headers) + line(['---'] * len(headers)) + ''.join(line(r) for r in rows)


def render(absolute, blocks, contrasts):
    idx = {tuple(r[k] for k in IDENTITY): r for r in absolute}
    bidx = {tuple(r[k] for k in IDENTITY) + (r['outerrep'],): r for r in blocks}
    def get(model, system, scenario, regime, strategy, metric, slice_name='all'):
        kind, s = slice_name.split('=', 1) if '=' in slice_name else ('all' if slice_name == 'all' else 'family', slice_name)
        return idx[(model, system, scenario, kind, s, regime, strategy, metric)]
    def show4(system, scenario, metric, slice_name='all'):
        for regime in REGIMES if system == 'expgym' else REGIMES[1:]:
            for strategy in ['single'] if system == 'expgym' else STRATEGIES:
                rs = [get(m, system, scenario, regime, strategy, metric, slice_name) for m in MODELS]
                yield [slice_name, metric, regime[5:], strategy, rs[0]['expected_items']] + [cell(r) for r in rs]
    hdr = ['切片', '指标', '预算', '策略', 'items'] + [LABELS[m] for m in MODELS]
    sa = []
    for s in ['all', 'whois', 'whatis']:
        sa.extend(show4('expgym', 'restricted_search', 'f1', s))
    for metric in ['evidence_acc', 'label_acc']:
        sa.extend(show4('expgym', 'evidence_audit', metric))
    slices = ['all', 'family=paramnet', 'family=nasbench101', 'family=nasbench201'] + [
        'task=' + t for t in sorted({r['slice'] for r in absolute if r['slice_kind'] == 'task'})]
    hpo = [row for s in slices for metric in ['gap', 'raw_perf']
           for row in show4('expgym', 'tuning', metric, s)]
    out = {'EXP_SEARCH_AUDIT': table(hdr, sa), 'EXP_HPO': table(hdr, hpo)}
    for token, scenario, metrics, selected in [
            ('POOL_SEARCH', 'restricted_search', ['f1_mi', 'f1_mv'], ['all']),
            ('POOL_AUDIT', 'evidence_audit', ['evidence_acc_mi', 'evidence_acc_mv', 'label_acc_mi', 'label_acc_mv'], ['all']),
            ('POOL_NAS', 'tuning', ['gap_mi', 'gap_bon', 'raw_perf_mi', 'raw_perf_bon'],
             ['all'] + ['task=hpobench:nasbench101:' + x for x in 'ABC'])]:
        out[token] = table(hdr, [row for s in selected for metric in metrics
                                for row in show4('poolact', scenario, metric, s)])
    cr = []
    for model, regime, metric in itertools.product(MODELS, REGIMES[1:],
                                                  ['f1_mv', 'evidence_acc_mv', 'label_acc_mv', 'gap_mi', 'gap_bon']):
        values = []
        for baseline, target in [('naive', 'cached'), ('cached', 'poolact'), ('naive', 'poolact')]:
            matched = [r for r in contrasts if r['model'] == model and r['system'] == 'poolact'
                       and r['regime'] == regime and r['metric'] == metric and r['slice_kind'] == 'all'
                       and r['baseline'] == baseline and r['target'] == target]
            if len(matched) != 1:
                raise ValueError('Missing/duplicate overview contrast')
            values.append(cell(matched[0], 'effect', True))
        cr.append([LABELS[model], regime[5:], metric] + values)
    out['POOL_CONTRASTS'] = table(['模型', '预算', '指标', 'cached − naive', 'poolact − cached', 'poolact − naive'], cr)
    for system, token, metrics in [('expgym', 'EXP_REPEATS', ['gap', 'raw_perf']),
                                   ('poolact', 'POOL_REPEATS', ['gap_mi', 'gap_bon', 'raw_perf_mi', 'raw_perf_bon'])]:
        rows = []
        for model, regime, strategy, metric in itertools.product(
                MODELS, REGIMES if system == 'expgym' else REGIMES[1:],
                ['single'] if system == 'expgym' else STRATEGIES, metrics):
            a = get(model, system, 'tuning', regime, strategy, metric)
            key = tuple(a[k] for k in IDENTITY)
            rows.append([LABELS[model], regime[5:], strategy, metric] +
                        [cell(bidx[key + (str(i),)]) for i in range(3)] +
                        [cell(a), fmt(a.get('descriptive_repeat_sd', ''))])
        out[token] = table(['模型', '预算', '策略', '指标', '2200', '2204', '2208', '三块均值', '描述 SD'], rows)
    resources = ['input_tokens', 'output_tokens', 'feedback_cost_seconds', 'wall_time_seconds',
                 'feedback_attempts', 'duplicate_action_attempts', 'feedback_visible', 'budget_utilization',
                 'protocol_failure_rate']
    rr = []
    for model in MODELS:
        for system, scenario in itertools.product(['expgym', 'poolact'], ['restricted_search', 'evidence_audit', 'tuning']):
            for regime, strategy in itertools.product(REGIMES if system == 'expgym' else REGIMES[1:],
                                                      ['single'] if system == 'expgym' else STRATEGIES):
                rr.append([LABELS[model], system + '/' + scenario, regime[5:], strategy] +
                          [('不适用' if metric == 'budget_utilization' and regime == 'cost_free' else
                            cell(get(model, system, scenario, regime, strategy, metric))) for metric in resources])
    out['RESOURCES'] = table(['模型', '系统/场景', '预算', '策略'] + resources, rr)
    return out


def detailed_files(absolute, blocks, contrasts):
    result = {}
    nav = ['# 完整聚合表\n\n全部 4 模型、所有原生切片、指标与预算/策略均保留。每模型页面避免单一巨型 Markdown 超出渲染上限。'
           '分母是分析 outcomes，不是 HTTP 请求或 Pool 成员数；unknown 不记为零。\n\n']
    repnav = ['# 完整 seed-block 表\n\nSearch 为 R1；Exp Audit 已折叠三个固定顺序一次；仅 tuning 为三个 blocks。'
              'R1 不计算 SD，seed 标签不证明独立采样。\n\n']
    for model in MODELS:
        slug = model.replace('.', '_')
        paths = ['tables/' + slug + '.md', 'repeats/' + slug + '.md']
        ar = [r for r in absolute if r['model'] == model]
        br = [r for r in blocks if r['model'] == model]
        nav.append('- [' + LABELS[model] + '](' + paths[0] + ')：' + str(len(ar)) + ' 行。\n')
        repnav.append('- [' + LABELS[model] + '](' + paths[1] + ')：' + str(len(br)) + ' 行。\n')
        for path, rows, block in [(paths[0], ar, False), (paths[1], br, True)]:
            body = '# ' + LABELS[model] + (' · blocks' if block else ' · 全部聚合') + '\n\n'
            body += 'known subset 仅供诊断，不替代 full mean；旧源的 original logical rows 与新源 components 原样保留在 CSV/输入中。\n\n'
            headers = ['系统/场景', '切片', '预算/策略', '指标'] + (['block/seed'] if block else []) + [
                '完整均值', '已知/预期 outcomes', 'items', 'known subset（非完整端点）'] + ([] if block else ['R', '描述 SD'])
            values = []
            for r in rows:
                values.append([r['system'] + '/' + r['scenario'], r['slice_kind'] + ':' + r['slice'],
                               r['regime'][5:] + '/' + r['strategy'], r['metric']] +
                              ([r['outerrep'] + '/' + r['seed_labels']] if block else []) +
                              [fmt(r['full_mean']), r['known_outcomes'] + '/' + r['expected_outcomes'],
                               r['expected_items'], fmt(r['known_subset_item_weighted_mean'])] +
                              ([] if block else [r['repeat_blocks'], fmt(r.get('descriptive_repeat_sd', ''))]))
            result[path] = (body + table(headers, values)).encode()
    nav.append('\n机器完整表：[absolute_settings.csv](absolute_settings.csv)；所有方向与配对分母：[contrasts.csv](contrasts.csv)。\n')
    repnav.append('\n机器完整表：[by_outerseed.csv](by_outerseed.csv)。\n')
    result['TABLES.md'] = ''.join(nav).encode()
    result['REPEATS.md'] = ''.join(repnav).encode()
    return result


def generate(output):
    inputs = read_inputs(output)
    absolute = [adapt_old(r) for r in inputs['old_absolute']]
    blocks = [adapt_old(r, True) for r in inputs['old_blocks']]
    contrasts = legacy_contrasts(absolute)
    for tag in ['qwen', 'deep']:
        absolute.extend(adapt_new(r) for r in inputs[tag + '_absolute'])
        blocks.extend(adapt_new(r) for r in inputs[tag + '_blocks'])
        contrasts.extend(dict(r, derivation='unchanged native frozen paired contrast') for r in inputs[tag + '_contrasts'])
    for rows in [absolute, blocks, contrasts]:
        rows.sort(key=lambda r: tuple(str(r.get(k, '')) for k in IDENTITY + ['outerrep', 'comparison_axis', 'baseline', 'target']))
    check_rows(absolute)
    check_rows(blocks, True)
    check_contrasts(contrasts)
    if {r['model'] for r in absolute} != set(MODELS) or len(absolute) != 4760 or len(blocks) != 11208:
        raise ValueError('Four-model coverage changed')
    rendered = render(absolute, blocks, contrasts)
    template = (output / 'REPORT_TEMPLATE.zh.md').read_text()
    for key, value in rendered.items():
        marker = '{{' + key + '}}'
        if template.count(marker) != 1:
            raise ValueError('Each table marker must occur once: ' + marker)
        template = template.replace(marker, value)
    if re.search(r'\{\{[A-Z_]+\}\}', template):
        raise ValueError('Unresolved table marker')
    result = {'README.zh.md': template.encode(), 'absolute_settings.csv': csv_bytes(absolute),
              'by_outerseed.csv': csv_bytes(blocks), 'contrasts.csv': csv_bytes(contrasts)}
    result.update(detailed_files(absolute, blocks, contrasts))
    result['AGGREGATE_CHECKS.json'] = json_bytes({
        'schema': 'four-model-report-checks-v1', 'absolute_rows': len(absolute),
        'block_rows': len(blocks), 'contrast_rows': len(contrasts),
        'models': MODELS, 'input_manifest_sha256': sha((output / 'INPUTS.json').read_bytes()),
        'template_sha256': sha((output / 'REPORT_TEMPLATE.zh.md').read_bytes()),
        'missing_full_means': {model: sum(not r['full_mean'] for r in absolute if r['model'] == model) for model in MODELS},
        'scope': 'Schema/identity/denominator/direction/display checks only. '
                 'Independent post-draft review is separate; this is not a scorer re-run or raw verification.',
        'native_extra_slices': 'New-model family=evidence_audit duplicates all by design and is retained, never added twice.',
        'unit_mapping': 'Old unit -> analysis_unit; metric unit is separate. Native new components count Audit orders '
                        'or outcomes, not N4 member agents. Legacy original_logical_rows remains separate.',
    })
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--freeze-from-workspace', type=Path)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    if args.freeze_from_workspace:
        if args.check:
            p.error('--check cannot freeze inputs')
        freeze(args.freeze_from_workspace.resolve(), args.output_dir.resolve())
        print('Frozen immutable report inputs; no report generated.')
        return
    files = generate(args.output_dir)
    for name, raw in files.items():
        path = args.output_dir / name
        if args.check:
            if not path.is_file() or path.read_bytes() != raw:
                raise ValueError('Deterministic output mismatch: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps({'mode': 'check' if args.check else 'generate', 'files': len(files),
                      'bytes': sum(map(len, files.values()))}))


if __name__ == '__main__':
    main()
