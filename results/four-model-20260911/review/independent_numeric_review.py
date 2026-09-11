#!/usr/bin/env python3
"""Independent, report-only check. Does not import or run the author generator.

Reads the report's explicit small frozen inputs, their immutable local Git blobs,
and report tables. No raw/tar, scorer, model, network, or runner dependency.
"""
import argparse
import collections
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import time


KEY = ('model', 'system', 'scenario', 'slice_kind', 'slice', 'regime', 'strategy', 'metric')
MODELS = {'Kimi-K3': 'kimi-k3', 'GLM-5.3': 'glm-5.3',
          'Qwen3.8': 'qwen3.8-2.4t-a95b-fp8', 'DeepSeek-0731': 'deepseek-v4-flash-0731'}
QUALITY = {'f1', 'f1_mi', 'f1_mv', 'evidence_acc', 'evidence_acc_mi', 'evidence_acc_mv',
           'label_acc', 'label_acc_mi', 'label_acc_mv', 'gap', 'gap_mi', 'gap_bon',
           'raw_perf', 'raw_perf_mi', 'raw_perf_bon'}


def main():
    start = time.monotonic()
    utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--workspace', type=Path,
                        default=Path('/lustrefs/users/chufan.shi/codex_space_tn'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.report
    counts = collections.Counter()
    files = {}
    errors = []

    def require(ok, message):
        counts['assertions'] += 1
        if not ok:
            errors.append(str(message))

    def read(path):
        data = (root / path).read_bytes()
        files[str(path)] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        return data

    def csvread(path):
        import io
        return list(csv.DictReader(io.StringIO(read(path).decode())))

    def numeric(value):
        return None if value == '' else float(value)

    def same_num(actual, wanted, label):
        a = numeric(actual)
        b = numeric(wanted) if isinstance(wanted, str) else wanted
        require(a is None and b is None or a is not None and b is not None and
                math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-9), (label, a, b))
        counts['numeric_checks'] += 1

    manifest = json.loads(read('INPUTS.json'))
    repositories = {
        'old': args.workspace / 'publication/restart_v5_remote_base.oDCT5P/repo',
        'qwen': args.workspace / 'publication/qwen38_delivery_20260911',
        'deep': args.workspace / 'publication/deepseek_flash_delivery_20260911',
    }
    sources, entries = {}, {}
    for entry in manifest['files']:
        path = entry['local_path']
        data = read(path)
        require(files[path] == {k: entry[k] for k in ('bytes', 'sha256')}, ('input identity', path))
        require(re.fullmatch('[a-f0-9]{40}', entry['commit']) is not None, ('commit', path))
        expected_url = 'https://github.com/tiannuo-yang/LLM_ExpGym/blob/' + entry['commit'] + '/' + entry['path']
        require(entry['url'] == expected_url, ('source URL', path))
        original = subprocess.check_output(['git', '-C', str(repositories[entry['repo']]),
                                            'show', entry['commit'] + ':' + entry['path']])
        require(data == original, ('snapshot vs immutable Git blob', path))
        entries[entry['id']] = entry
        sources[entry['id']] = csvread(path) if path.endswith('.csv') else json.loads(data)
        if entry['expected_rows'] is not None:
            require(len(sources[entry['id']]) == entry['expected_rows'], ('input rows', path))
        counts['input_blobs_compared_to_immutable_git'] += 1

    absolute, blocks, contrasts = (csvread(p) for p in
                                  ('absolute_settings.csv', 'by_outerseed.csv', 'contrasts.csv'))
    require((len(absolute), len(blocks), len(contrasts)) == (4760, 11208, 4690), 'output row counts')
    abs_index, block_index = {}, {}
    for rows, is_block, index in ((absolute, False, abs_index), (blocks, True, block_index)):
        coverage = collections.defaultdict(set)
        for row in rows:
            srcid = row['source_input']
            source_line = int(row['source_row'])
            source = sources[srcid][source_line - 2]
            require(source_line not in coverage[srcid], ('duplicate source row', srcid, source_line))
            coverage[srcid].add(source_line)
            require(row['source_url'] == entries[srcid]['url'], ('row source URL', srcid, source_line))
            identity = tuple(row[k] for k in KEY) + ((row['outerrep'],) if is_block else ())
            require(identity not in index, ('duplicate normalized identity', identity))
            index[identity] = row
            if not srcid.startswith('old_'):
                for name, value in source.items():
                    require(row[name] == value, ('native field changed', srcid, source_line, name))
                    counts['native_fields_preserved'] += 1
                require(row['native_slice'] == source['slice'], ('native slice copy', identity))
            else:
                for name in ('model', 'system', 'scenario', 'regime', 'strategy', 'metric'):
                    require(row[name] == source[name], ('old identity', identity, name))
                sl = source['slice']
                if '=' in sl:
                    kind, slname = sl.split('=', 1)
                elif sl == 'all':
                    kind, slname = 'all', 'all'
                else:
                    kind, slname = 'family', sl
                require((row['slice_kind'], row['slice'], row['native_slice']) == (kind, slname, sl),
                        ('old slice', identity))
                mapping = {'analysis_unit': 'unit', 'expected_outcomes': 'n_rows',
                           'known_outcomes': 'n_known_rows', 'missing_outcomes': 'n_missing_rows',
                           'expected_items': 'n_items', 'full_mean': 'mean',
                           'known_subset_item_weighted_mean': 'known_subset_mean_not_complete_endpoint',
                           'original_logical_rows': 'n_original_logical_rows'}
                for destination, origin in mapping.items():
                    require(row[destination] == source[origin], ('old mapped field', identity, destination))
                    counts['old_fields_mapped'] += 1
                wanted_unit = ('Gap points' if row['metric'].startswith('gap') else
                               'tokens' if row['metric'].endswith('_tokens') else
                               'seconds' if row['metric'].endswith('_seconds') else
                               'fraction' if row['metric'] in QUALITY | {'budget_utilization', 'protocol_failure_rate'}
                               else 'count')
                require(row['unit'] == wanted_unit, ('old metric unit distinct from analysis unit', identity))
                require(row['N'] == ('1' if row['system'] == 'expgym' else '4'), ('N', identity))
                require(row['known_items'] == (source['n_items'] if int(source['n_known_rows']) else '0'),
                        ('old known item denominator', identity))
                require(row['complete_items'] == source['n_known_rows' if is_block else 'n_complete_items'],
                        ('old complete item denominator', identity))
                if is_block:
                    require(row['outerrep'] == str(int(source['outerseed'].split('_')[-1])), ('outer block', identity))
                    require(row['seed_labels'] == source['requested_seed_block_label'], ('seed labels', identity))
                    require(row['min_repeats_per_item'] == row['max_repeats_per_item'] == '1', ('block repeats', identity))
                else:
                    require(row['min_repeats_per_item'] == row['max_repeats_per_item'] == row['repeat_blocks'] == source['n_repeats'],
                            ('aggregate repeats', identity))
                    require(row['descriptive_repeat_sd'] == source['seedblock_descriptive_sd'], ('SD source', identity))
            n, k, m = [int(row[x]) for x in ('expected_outcomes', 'known_outcomes', 'missing_outcomes')]
            require(n > 0 and n == k + m and min(k, m) >= 0, ('denominator', identity))
            require((row['full_mean'] == '') == (m > 0), ('unknown vs full denominator', identity))
            require(n == int(row['expected_items']) * int(row['max_repeats_per_item']), ('balanced item/repeats', identity))
            if row['metric'].startswith('gap') and row['full_mean']:
                require(float(row['full_mean']) >= 0, ('Gap lower bound', identity))
                counts['gap_values_above_100_preserved'] += float(row['full_mean']) > 100
            if not is_block and (row['repeat_blocks'] == '1' or m):
                require(row['descriptive_repeat_sd'] == '', ('invalid/fake SD', identity))
        for srcid, lines in coverage.items():
            require(lines == set(range(2, len(sources[srcid]) + 2)), ('full source coverage', srcid))

    grouped = collections.defaultdict(list)
    for key, row in block_index.items():
        grouped[key[:-1]].append(row)
    for key, row in abs_index.items():
        br = grouped[key]
        require(len(br) == int(row['repeat_blocks']), ('block count', key))
        for col in ('expected_outcomes', 'known_outcomes', 'missing_outcomes'):
            require(sum(int(b[col]) for b in br) == int(row[col]), ('block count sum', key, col))
        if row['full_mean']:
            values = [float(b['full_mean']) for b in br]
            same_num(row['full_mean'], statistics.fmean(values), ('block to full mean', key))
            if len(values) > 1:
                same_num(row['descriptive_repeat_sd'], statistics.stdev(values), ('block SD', key))
                counts['repeat_sds_recomputed'] += 1
        if row['source_input'] == 'old_absolute':
            src = sources['old_absolute'][int(row['source_row']) - 2]
            published = json.loads(src['outerseed_means'])
            for b in br:
                same_num(b['full_mean'], published['outer_' + b['outerrep'].zfill(5)], ('old embedded block', key))

    contrast_index = {}
    contrast_coverage = collections.defaultdict(set)
    old_pair_keys = set()
    for row in contrasts:
        axis = row['comparison_axis']
        identity = tuple(row[k] for k in KEY if k != axis) + (axis, row['baseline'], row['target'])
        require(identity not in contrast_index, ('duplicate contrast', identity))
        contrast_index[identity] = row
        if row['source_input'] != 'old_absolute':
            srcid, line = row['source_input'], int(row['source_row'])
            source = sources[srcid][line - 2]
            contrast_coverage[srcid].add(line)
            for name, value in source.items():
                require(row[name] == value, ('native contrast field', srcid, line, name))
                counts['native_contrast_fields_preserved'] += 1
            require(row['source_url'] == entries[srcid]['url'], ('contrast source URL', identity))
        else:
            base = dict(row, **{axis: row['baseline']})
            target = dict(row, **{axis: row['target']})
            a, b = [abs_index[tuple(x[k] for k in KEY)] for x in (base, target)]
            old_pair_keys.add((tuple(a[k] for k in KEY), tuple(b[k] for k in KEY)))
            require(row['baseline_full_mean'] == a['full_mean'] and row['target_full_mean'] == b['full_mean'], ('old contrast source means', identity))
            require(row['source_row'] == a['source_row'] and row['source_row_target'] == b['source_row'], ('old contrast source rows', identity))
            for col in ('expected_outcomes', 'expected_items', 'min_repeats_per_item', 'max_repeats_per_item'):
                require(row[col] == a[col] == b[col], ('old paired denominator', identity, col))
            complete = bool(a['full_mean'] and b['full_mean'])
            for col, wanted in [('known_outcomes', a['expected_outcomes'] if complete else '0'),
                                ('missing_outcomes', '0' if complete else a['expected_outcomes']),
                                ('known_items', a['expected_items'] if complete else '0'),
                                ('complete_items', a['expected_items'] if complete else '0')]:
                require(row[col] == wanted, ('old contrast count', identity, col))
            require(row['known_paired_subset_effect'] == row['effect'], ('old full paired effect', identity))
        n, k, m = [int(row[x]) for x in ('expected_outcomes', 'known_outcomes', 'missing_outcomes')]
        require(n == k + m, ('contrast accounting', identity))
        require((row['effect'] == '') == (m > 0), ('contrast unknown', identity))
        require(row['effect_definition'] == ('baseline_minus_target' if axis == 'regime' else 'target_minus_baseline'), ('contrast direction', identity))
        if row['effect']:
            a, b = float(row['baseline_full_mean']), float(row['target_full_mean'])
            wanted = a - b if axis == 'regime' else b - a
            same_num(row['effect'], wanted, ('unrounded difference', identity))
            if row['metric'] in QUALITY:
                same_num(row['utility_effect'], wanted, ('higher better quality', identity))
    for srcid, lines in contrast_coverage.items():
        require(lines == set(range(2, len(sources[srcid]) + 2)), ('all native contrasts', srcid))
    expected_pairs = set()
    for key, row in abs_index.items():
        if row['source_input'] != 'old_absolute':
            continue
        axis = 'regime' if row['system'] == 'expgym' else 'strategy'
        order = ['cost_free', 'cost_moderate', 'cost_tight'] if axis == 'regime' else ['naive', 'cached', 'poolact']
        for target in order[order.index(row[axis]) + 1:]:
            b = dict(row, **{axis: target})
            expected_pairs.add((key, tuple(b[k] for k in KEY)))
    require(old_pair_keys == expected_pairs, 'all old regime/strategy pairs')
    counts['old_derived_contrasts_checked'] = len(old_pair_keys)

    def displayed(value, signed=False):
        return 'unknown' if value == '' else format(float(value), '+.6f' if signed else '.6f')

    def cell(row, field='full_mean', signed=False):
        v = displayed(row[field], signed)
        return v + (' (' + row['known_outcomes'] + '/' + row['expected_outcomes'] + ')' if v == 'unknown' else '')

    def check_text(value, wanted, label):
        require(value == wanted, ('rendered numeric cell', label, value, wanted))
        counts['rendered_numeric_cells_checked'] += 1

    def get(model, system, scenario, slice_text, budget, strategy, metric):
        if '=' in slice_text:
            kind, sl = slice_text.split('=', 1)
        else:
            kind, sl = ('all', 'all') if slice_text == 'all' else ('family', slice_text)
        return abs_index[(model, system, scenario, kind, sl, 'cost_' + budget, strategy, metric)]

    # Parse rendered tables independently by their actual headers, not template markers.
    header = None
    section = ''
    for lineno, line in enumerate(read('README.zh.md').decode().splitlines(), 1):
        if line.startswith('## '):
            section = line
        if not line.startswith('| '):
            header = None
            continue
        cells = [x.strip() for x in line.strip().strip('|').split('|')]
        if header is None:
            header = cells
            continue
        if all(re.fullmatch(':?-+:?', x) for x in cells):
            continue
        if header[0] == '切片':
            sl, metric, budget, strategy, items = cells[:5]
            system = 'expgym' if section.startswith('## 2.') else 'poolact'
            scenario = 'restricted_search' if metric.startswith('f1') else 'evidence_audit' if metric.startswith(('evidence_', 'label_')) else 'tuning'
            for label, value in zip(header[5:], cells[5:]):
                row = get(MODELS[label], system, scenario, sl, budget, strategy, metric)
                check_text(items, row['expected_items'], ('main items', lineno, label))
                check_text(value, cell(row), ('main absolute', lineno, label))
            counts['main_absolute_rows'] += 1
        elif 'cached − naive' in header:
            label, budget, metric = cells[:3]
            for value, (base, target) in zip(cells[3:], [('naive', 'cached'), ('cached', 'poolact'), ('naive', 'poolact')]):
                candidates = [r for r in contrasts if r['model'] == MODELS[label] and r['regime'] == 'cost_' + budget
                              and r['metric'] == metric and r['slice_kind'] == 'all' and r['system'] == 'poolact'
                              and r['baseline'] == base and r['target'] == target]
                require(len(candidates) == 1, ('display contrast identity', lineno))
                check_text(value, cell(candidates[0], 'effect', True), ('main contrast', lineno, base, target))
            counts['main_contrast_rows'] += 1
        elif '三块均值' in header:
            label, budget, strategy, metric = cells[:4]
            system = 'expgym' if section.startswith('## 2.') else 'poolact'
            row = get(MODELS[label], system, 'tuning', 'all', budget, strategy, metric)
            key = tuple(row[k] for k in KEY)
            for rep, value in enumerate(cells[4:7]):
                check_text(value, cell(block_index[key + (str(rep),)]), ('main block', lineno, rep))
            check_text(cells[7], cell(row), ('main block overall', lineno))
            check_text(cells[8], displayed(row['descriptive_repeat_sd']), ('main block SD', lineno))
            counts['main_repeat_rows'] += 1
        elif 'input_tokens' in header:
            label, syssc, budget, strategy = cells[:4]
            system, scenario = syssc.split('/')
            for metric, value in zip(header[4:], cells[4:]):
                if metric == 'budget_utilization' and budget == 'free':
                    wanted = '不适用'
                else:
                    row = get(MODELS[label], system, scenario, 'all', budget, strategy, metric)
                    wanted = cell(row)
                check_text(value, wanted, ('main resource', lineno, metric))
            counts['main_resource_rows'] += 1

    # The per-model detail pages must represent every normalized absolute/block row once.
    for label, model in MODELS.items():
        slug = model.replace('.', '_')
        for directory, is_block, source_index in [('tables', False, abs_index), ('repeats', True, block_index)]:
            used = set()
            for lineno, line in enumerate(read(directory + '/' + slug + '.md').decode().splitlines(), 1):
                if not line.startswith('| expgym/') and not line.startswith('| poolact/'):
                    continue
                cells = [x.strip() for x in line.strip().strip('|').split('|')]
                system, scenario = cells[0].split('/')
                kind, sl = cells[1].split(':', 1)
                budget, strategy = cells[2].split('/')
                key = (model, system, scenario, kind, sl, 'cost_' + budget, strategy, cells[3])
                offset = 4
                if is_block:
                    rep, seed = cells[4].split('/', 1)
                    key += (rep,)
                    offset += 1
                row = source_index[key]
                require(key not in used, ('duplicate detailed display', directory, lineno))
                used.add(key)
                if is_block:
                    check_text(seed, row['seed_labels'], ('detail seed', directory, lineno))
                expected = [displayed(row['full_mean']), row['known_outcomes'] + '/' + row['expected_outcomes'],
                            row['expected_items'], displayed(row['known_subset_item_weighted_mean'])]
                if not is_block:
                    expected += [row['repeat_blocks'], displayed(row['descriptive_repeat_sd'])]
                require(len(cells[offset:]) == len(expected), ('detail columns', directory, lineno))
                for value, wanted in zip(cells[offset:], expected):
                    check_text(value, wanted, ('detailed row', directory, lineno))
            expected_keys = {k for k in source_index if k[0] == model}
            require(used == expected_keys, ('complete per-model detail rows', model, directory))
            counts['detail_block_rows' if is_block else 'detail_absolute_rows'] += len(used)

    # Focused semantic statements required by the user's main questions.
    for model in MODELS.values():
        for metric, scenario in [('f1', 'restricted_search'), ('evidence_acc', 'evidence_audit')]:
            values = [float(get(model, 'expgym', scenario, 'all', budget, 'single', metric)['full_mean'])
                      for budget in ('free', 'moderate', 'tight')]
            require(values[0] > values[1] > values[2], ('all model Search/EA degradation', model, metric))
        a = get(model, 'poolact', 'restricted_search', 'all', 'tight', 'naive', 'f1_mv')
        b = get(model, 'poolact', 'restricted_search', 'all', 'tight', 'poolact', 'f1_mv')
        require(float(b['full_mean']) > float(a['full_mean']), ('all model Tight Search gain', model))
    deep = 'deepseek-v4-flash-0731'
    for budget in ('free', 'moderate', 'tight'):
        require(get(deep, 'expgym', 'tuning', 'all', budget, 'single', 'gap')['full_mean'] == '', ('Deep full HPO unknown', budget))
    for budget in ('moderate', 'tight'):
        for strategy in ('naive', 'cached', 'poolact'):
            require(get(deep, 'poolact', 'tuning', 'all', budget, strategy, 'gap_mi')['full_mean'] == '',
                    ('Deep full NAS unknown', budget, strategy))
    counts.update({'absolute_rows': len(absolute), 'block_rows': len(blocks), 'contrast_rows': len(contrasts)})
    report = {'schema': 'four-model-independent-numerical-review-v1', 'started_utc': utc,
              'elapsed_seconds': time.monotonic() - start,
              'reviewer': '/root/four_model_postdraft_review',
              'status': 'pass' if not errors else 'fail', 'errors': errors,
              'counts': dict(counts), 'read_file_identities': files,
              'scope': 'Independent source-field/identity/denominator checks, complete block-mean/SD recomputation, '
                       'all normalized contrasts, all generated README numerical tables and per-model detail rows. '
                       'No import or invocation of author build_report.py; no raw/tar, model, scorer, network, '
                       'archive payload or upstream scientific re-evaluation. Static prose/settings/cost/index review is separate.'}
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': report['status'], 'errors': errors[:20], 'counts': report['counts'],
                      'elapsed_seconds': report['elapsed_seconds']}, ensure_ascii=False))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
