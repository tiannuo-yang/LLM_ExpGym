#!/usr/bin/env python3
"""Frozen-score report adapter; no models, scorers, raw payloads or archives.

The prior four-model CSV exports are imported unchanged. GPT metrics.csv already
contains scored single/strict-N4 endpoints. We regroup those scores for task
tables, fold Audit orders once, and retain native exports for cross-checks.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import re
import statistics
import subprocess

import report_tables as t

PIN = 'a79cbc100804a1bc8d374e084a4b9999e3697a91'
PRIOR = 'results/four-model-20260911/'
API = 'LLM_ExpGym_api_studies_20260910'
GPT_STUDY = 'studies/gpt56sol_medium_refmatrix_20260910_v1/'
API_REPORT = 'studies/api_20260910/full_report_v1/'
GPT = 'gpt-5.6-sol'
METRICS = {'F1': 'f1', 'EA': 'evidence_acc', 'LA': 'label_acc',
           'Gap': 'gap', 'raw_performance': 'raw_perf'}
BASE_KEYS = ['model', 'system', 'scenario', 'regime', 'strategy', 'metric']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def jb(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


SCOPE_PROJECTION = dict(
    source_bytes=1801,
    source_sha256='1a5cca49d04a1d0b9af6e26f0e758b8c5ceadca3a46850091a726ff4490f0c17',
    public_bytes=1759,
    public_sha256='fe015780248bff2980a4ec1e1099e4d56b3d08c3e76293952931bb84924afa1a',
    transform='Replace exactly two descriptive Authorization template values with [REDACTED]; '
              'responses and anthropic under headers_explicit_in_frozen_client_source. '
              'No experiment, score, source original or other metadata fields changed.')


def public_snapshot(spec, raw):
    if spec['id'] != 'api_request_scope':
        return raw, {}
    if (len(raw), sha(raw)) != (SCOPE_PROJECTION['source_bytes'], SCOPE_PROJECTION['source_sha256']):
        raise ValueError('Scope source identity changed')
    original = b'"Authorization": "<credential; omitted from dump>"'
    if raw.count(original) != 2:
        raise ValueError('Scope projection requires exactly two template fields')
    result = raw.replace(original, b'"Authorization": "[REDACTED]"')
    if (len(result), sha(result)) != (SCOPE_PROJECTION['public_bytes'], SCOPE_PROJECTION['public_sha256']):
        raise ValueError('Scope projection identity changed')
    return result, {'public_projection': SCOPE_PROJECTION}


def specs():
    rows = []
    def add(name, origin, path, count=None, digest=None):
        rows.append(dict(id=name, origin=origin, path=path, rows=count, sha256_expected=digest,
                         local_path='inputs/' + name + Path(path).suffix))
    for name, filename, count in [('absolute', 'absolute_settings.csv', 4760),
                                   ('blocks', 'by_outerseed.csv', 11208),
                                   ('contrasts', 'contrasts.csv', 4690)]:
        add('prior_' + name, 'published_git:' + PIN, PRIOR + filename, count)
    for name, filename, count, digest in [
        ('metrics', 'metrics.csv', 1611, '5d63a301b4fa50204a6fca669f41b4c25b31a282326dfd1723a9036ac070e8b0'),
        ('absolute', 'absolute_settings.csv', 165, '82c767b9ef91ab96666f55291afd268f4b9c8726dcf14d9d3388c11b08932be4'),
        ('repeats', 'by_repeat.csv', 333, 'e9d651a389bd49c4d045acc5c3bebf959725b648ea98bcad3ce56a5bcc38ad88'),
        ('contrasts', 'contrasts.csv', 165, '0cc21c70930486556cc9aef2382332830a45db0ec7757dcff6b623dc88454088'),
        ('validation', 'VALIDATION.json', None, '83b2f8b03775b863ca829c85fc16d2d60666bd29cfaaa7d01be08e337159e687')]:
        add('gpt_' + name, 'frozen_local_api_study', GPT_STUDY + 'analysis_v1/' + filename, count, digest)
    add('api_resources', 'frozen_local_api_study', API_REPORT + 'resources_by_setting.csv', 47,
        '254ef1cdddbca8e7d2d4807257b198d413ce7e5c57ff474b9552d283f59ad811')
    add('gpt_queue_config', 'frozen_local_api_study', GPT_STUDY + 'metadata/gpt56sol_medium_refmatrix_20260910_v1-queue-config.json')
    add('gpt_matrix_validation', 'frozen_local_api_study', GPT_STUDY + 'metadata/matrix-validation.json')
    add('api_request_scope', 'frozen_local_api_study', GPT_STUDY + 'metadata/api-observability-scope-v1.json')
    add('api_review', 'frozen_local_api_study', API_REPORT + 'INDEPENDENT_REVIEW.json')
    return rows


def freeze(workspace, root):
    if (root / 'INPUTS.json').exists() or (root / 'inputs').exists():
        raise ValueError('Frozen inputs already exist; never replace in place')
    entries, contents = [], []
    for spec in specs():
        if spec['origin'].startswith('published_git:'):
            raw = subprocess.check_output(['git', '-C', str(workspace / 'publication/four_model_report_20260911'),
                                           'show', PIN + ':' + spec['path']])
            origin = 'https://github.com/tiannuo-yang/LLM_ExpGym/blob/' + PIN + '/' + spec['path']
        else:
            path = workspace / API / spec['path']
            if path.is_symlink() or not path.is_file():
                raise ValueError('Expected regular frozen API export')
            raw = path.read_bytes()
            origin = str(path)
        if spec['sha256_expected'] and sha(raw) != spec['sha256_expected']:
            raise ValueError('Previously bound input changed: ' + spec['id'])
        if spec['rows'] is not None and len(list(csv.DictReader(io.StringIO(raw.decode())))) != spec['rows']:
            raise ValueError('Input row coverage changed: ' + spec['id'])
        raw, projection = public_snapshot(spec, raw)
        entries.append(dict(spec, bytes=len(raw), sha256=sha(raw), source=origin, **projection))
        contents.append((spec['local_path'], raw))
    (root / 'inputs').mkdir(parents=True)
    for path, raw in contents:
        (root / path).write_bytes(raw)
    (root / 'INPUTS.json').write_bytes(jb(dict(schema='five-model-report-inputs-v1', files=entries,
        policy='Explicit frozen scored exports/metadata only. No source payload rescoring. '
               'API raw remains local-only; copying a scored CSV does not publish its raw collection.')))


def read_inputs(root):
    manifest = json.loads((root / 'INPUTS.json').read_bytes())
    expected = {s['id']: s for s in specs()}
    if len(manifest['files']) != len(expected) or {s['id'] for s in manifest['files']} != set(expected):
        raise ValueError('Input identity coverage mismatch')
    result = {}
    for entry in manifest['files']:
        spec = expected[entry['id']]
        if any(entry[k] != v for k, v in spec.items()):
            raise ValueError('Input specification changed')
        if spec['origin'].startswith('published_git:') and entry['source'] != (
                'https://github.com/tiannuo-yang/LLM_ExpGym/blob/' + PIN + '/' + spec['path']):
            raise ValueError('Moving or incorrect published source URL')
        path = root / entry['local_path']
        if path.is_symlink():
            raise ValueError('No symlink inputs')
        raw = path.read_bytes()
        if (len(raw), sha(raw)) != (entry['bytes'], entry['sha256']):
            raise ValueError('Input SHA/size mismatch: ' + entry['id'])
        if entry['id'] == 'api_request_scope':
            if (entry.get('public_projection') != SCOPE_PROJECTION or
                (len(raw), sha(raw)) != (SCOPE_PROJECTION['public_bytes'], SCOPE_PROJECTION['public_sha256'])):
                raise ValueError('Scope public projection identity mismatch')
        if spec['rows'] is not None:
            rows = list(csv.DictReader(io.StringIO(raw.decode())))
            if len(rows) != spec['rows']:
                raise ValueError('Wrong row count')
            result[entry['id']] = rows
        else:
            result[entry['id']] = json.loads(raw)
    return result


def metric(row):
    suffix = '' if row['endpoint'] == 'single' else '_' + row['endpoint'].lower()
    return METRICS[row['metric']] + suffix


def folded_gpt(rows):
    grouped = defaultdict(list)
    seen = set()
    for i, row in enumerate(rows, 2):
        if row['model'] != GPT or row['execution_complete'] != 'True':
            raise ValueError('Unexpected GPT model or failed execution in fixed score export')
        identity = tuple(row[k] for k in ['job_id', 'metric', 'endpoint'])
        if identity in seen:
            raise ValueError('Duplicate scored metric identity')
        seen.add(identity)
        scenario = row['scenario']
        if scenario == 'tuning':
            if row['repeat'] != 'seed_' + row['seed']:
                raise ValueError('HPO repeat and seed disagree')
            outer = str(['2200', '2204', '2208'].index(row['seed']))
        else:
            outer = '0'
        r = dict(model=GPT, system=row['system'], scenario=scenario, regime=row['budget'],
                 strategy=row['strategy'], metric=metric(row), item=row['item'], outerrep=outer,
                 N=row['N'], unit=row['unit'], higher_is_better='True',
                 family='evidence_audit' if row['family'] == 'contract_nli' else row['family'])
        key = tuple(r[k] for k in BASE_KEYS + ['item', 'outerrep'])
        grouped[key].append((r, row, i))
    folded = []
    for records in grouped.values():
        r = dict(records[0][0])
        audit = r['system'] == 'expgym' and r['scenario'] == 'evidence_audit'
        expected = 3 if audit else 1
        if len(records) != expected:
            raise ValueError('Wrong per-item order/repeat multiplicity')
        if audit and {row['seed'] for _, row, _ in records} != {'2200', '2201', '2202'}:
            raise ValueError('Audit order identities incomplete')
        values = [t.number(row['value']) for _, row, _ in records]
        known = [v for v in values if v is not None]
        r['value'] = statistics.mean(known) if len(known) == expected else None
        r['component_subset_value'] = statistics.mean(known) if known else None
        r['source_components'] = expected
        r['known_source_components'] = len(known)
        r['source_rows'] = [i for _, _, i in records]
        r['seed_labels'] = sorted({int(row['seed']) for _, row, _ in records})
        # Strict N4 missing outcomes stay missing; a scored agent subset is never
        # read for a whole-pool MI/BoN endpoint here.
        for _, row, _ in records:
            if row['system'] == 'poolact' and row['scenario'] == 'tuning' and int(row['known_agents']) < 4:
                if t.number(row['value']) is not None:
                    raise ValueError('Incomplete strict N4 score is not unknown')
        folded.append(r)
    return folded


def groups(folded):
    result = defaultdict(list)
    for r in folded:
        slices = [('all', 'all'), ('family', r['family'])]
        if r['scenario'] == 'tuning':
            slices.append(('task', r['item']))
        for kind, name in slices:
            key = tuple(r[k] for k in BASE_KEYS) + (kind, name)
            result[key].append(r)
    return result


def aggregate(rows, block=False):
    r = {k: rows[0][k] for k in BASE_KEYS + ['N', 'unit', 'higher_is_better']}
    by_item = defaultdict(list)
    for row in rows:
        by_item[row['item']].append(row)
    lengths = {len(v) for v in by_item.values()}
    if len(lengths) != 1:
        raise ValueError('Unequal planned repeat counts')
    known = [row['value'] for row in rows if row['value'] is not None]
    item_known = [[x['value'] for x in v if x['value'] is not None] for v in by_item.values()]
    partial_mean = statistics.mean(statistics.mean(v) for v in item_known if v) if known else None
    all_known = len(known) == len(rows)
    r.update(expected_outcomes=str(len(rows)), known_outcomes=str(len(known)),
             missing_outcomes=str(len(rows) - len(known)), expected_items=str(len(by_item)),
             known_items=str(sum(bool(v) for v in item_known)),
             complete_items=str(sum(len(v) == len(by_item[item]) for item, v in zip(by_item, item_known))),
             full_mean=repr(partial_mean) if all_known else '',
             known_subset_item_weighted_mean='' if partial_mean is None else repr(partial_mean),
             min_repeats_per_item=str(min(lengths)), max_repeats_per_item=str(max(lengths)),
             original_logical_rows=str(sum(x['source_components'] for x in rows)),
             known_source_logical_rows=str(sum(x['known_source_components'] for x in rows)),
             source_input='gpt_metrics', source_row=json.dumps(sorted(i for x in rows for i in x['source_rows'])),
             source_url='inputs/gpt_metrics.csv',
             scope='GPT frozen scored endpoints; Audit document mean once; strict N4; no resource means imputed',
             analysis_unit='pool_aggregate_N4' if r['system'] == 'poolact' else
                           'document_mean_3_fixed_orders' if r['scenario'] == 'evidence_audit' else 'single_trace')
    if block:
        r['outerrep'] = rows[0]['outerrep']
        r['seed_labels'] = json.dumps(sorted({seed for x in rows for seed in x['seed_labels']}))
    else:
        blocks = sorted({x['outerrep'] for x in rows})
        r['repeat_blocks'] = str(len(blocks))
        block_means = [aggregate([x for x in rows if x['outerrep'] == b], True)['full_mean'] for b in blocks]
        r['descriptive_repeat_sd'] = (repr(statistics.stdev(float(v) for v in block_means))
                                      if len(blocks) > 1 and all_known else '')
    return r


def gpt_outputs(folded):
    absolute, blocks, contrasts = [], [], []
    grouped = groups(folded)
    for key, rows in sorted(grouped.items()):
        a = aggregate(rows)
        a.update(slice_kind=key[-2], slice=key[-1])
        absolute.append(a)
        for outer in sorted({r['outerrep'] for r in rows}):
            b = aggregate([r for r in rows if r['outerrep'] == outer], True)
            b.update(slice_kind=key[-2], slice=key[-1])
            blocks.append(b)
    for key, left in sorted(grouped.items()):
        head = dict(zip(BASE_KEYS + ['slice_kind', 'slice'], key))
        axis = 'regime' if head['system'] == 'expgym' else 'strategy'
        levels = t.REGIMES if axis == 'regime' else t.STRATEGIES
        for target in levels[levels.index(head[axis]) + 1:]:
            target_head = dict(head, **{axis: target})
            right = grouped[tuple(target_head[k] for k in BASE_KEYS + ['slice_kind', 'slice'])]
            ri = {(r['item'], r['outerrep']): r for r in right}
            if {(r['item'], r['outerrep']) for r in left} != set(ri):
                raise ValueError('Contrast item/repeat identity mismatch')
            pairs = []
            for a in left:
                b = ri[(a['item'], a['outerrep'])]
                known = a['value'] is not None and b['value'] is not None
                value = (a['value'] - b['value'] if axis == 'regime' else b['value'] - a['value']) if known else None
                pairs.append(dict(a, value=value, known_source_components=a['source_components'] if known else 0))
            pair, base, dest = aggregate(pairs), aggregate(left), aggregate(right)
            r = {k: pair[k] for k in BASE_KEYS + ['N', 'unit', 'higher_is_better', 'scope', 'expected_outcomes',
                    'known_outcomes', 'missing_outcomes', 'expected_items', 'known_items', 'complete_items',
                    'min_repeats_per_item', 'max_repeats_per_item', 'source_input', 'source_row', 'source_url']}
            r.update(slice_kind=key[-2], slice=key[-1], comparison_axis=axis,
                     baseline=head[axis], target=target,
                     baseline_full_mean=base['full_mean'], target_full_mean=dest['full_mean'],
                     effect_definition='baseline_minus_target' if axis == 'regime' else 'target_minus_baseline',
                     effect=pair['full_mean'], utility_effect=pair['full_mean'],
                     known_paired_subset_effect=pair['known_subset_item_weighted_mean'],
                     source_row_target=json.dumps(sorted(i for x in right for i in x['source_rows'])),
                     derivation='New paired descriptive contrast of frozen GPT metric values after Audit fold; no rescore')
            contrasts.append(r)
    return absolute, blocks, contrasts


def validate_native(inputs, absolute, blocks, contrasts):
    def identity(row):
        kind = 'all' if row['slice'] == 'all' else 'family'
        name = 'evidence_audit' if row['slice'] == 'contract_nli' else row['slice']
        return (GPT, row['system'], row['scenario'], kind, name, row['budget'], row['strategy'], metric(row))
    ai = {tuple(r[k] for k in t.IDENTITY): r for r in absolute}
    bi = {tuple(r[k] for k in t.IDENTITY) + (r['outerrep'],): r for r in blocks}
    ci = {tuple(r[k] for k in t.IDENTITY) + (r['baseline'], r['target']): r for r in contrasts}
    counts = defaultdict(int)
    def same(a, b):
        av, bv = t.number(a), t.number(b)
        if (av is None) != (bv is None) or (av is not None and not math.isclose(av, bv, abs_tol=1e-10, rel_tol=1e-11)):
            raise ValueError(('Native export disagreement', a, b))
    for r in inputs['gpt_absolute']:
        target = ai[identity(r)]
        for k in ['full_mean', 'known_subset_item_weighted_mean']:
            same(r[k], target[k])
        audit = r['system'] == 'expgym' and r['scenario'] == 'evidence_audit'
        factor = 3 if audit else 1
        for k in ['expected_outcomes', 'known_outcomes', 'missing_outcomes']:
            if int(r[k]) != factor * int(target[k]):
                raise ValueError('Native Audit/outcome denominator mismatch')
        if not audit:
            same(r['descriptive_repeat_sd'], target['descriptive_repeat_sd'])
        counts['absolute_native_crosschecks'] += 1
    for r in inputs['gpt_repeats']:
        if r['system'] == 'expgym' and r['scenario'] == 'evidence_audit':
            # These are fixed-order views retained in the source snapshot, not
            # the post-fold R1 block. Their all-order mean was checked above.
            counts['native_audit_order_rows_retained_separately'] += 1
            continue
        outer = '0' if r['repeat'] == 'R1' else str(['seed_2200', 'seed_2204', 'seed_2208'].index(r['repeat']))
        same(r['full_mean'], bi[identity(r) + (outer,)]['full_mean'])
        counts['repeat_native_crosschecks'] += 1
    for r in inputs['gpt_contrasts']:
        target = ci[identity(r) + (r['baseline'], r['target'])]
        for k in ['baseline_full_mean', 'target_full_mean', 'effect', 'known_paired_subset_effect']:
            same(r[k], target[k])
        factor = 3 if r['system'] == 'expgym' and r['scenario'] == 'evidence_audit' else 1
        for k in ['expected_outcomes', 'known_outcomes', 'missing_outcomes']:
            if int(r[k]) != factor * int(target[k]):
                raise ValueError('Native contrast denominator mismatch')
        counts['contrast_native_crosschecks'] += 1
    return dict(counts)


def resources_table(rows):
    selected = [r for r in rows if r['model'] == GPT and r['scope'] == 'setting']
    if len(selected) != 27:
        raise ValueError('GPT resource setting coverage changed')
    expected = {(system, scenario, budget, strategy)
                for system in ['expgym', 'poolact']
                for scenario in ['restricted_search', 'evidence_audit', 'tuning']
                for budget in (t.REGIMES if system == 'expgym' else t.REGIMES[1:])
                for strategy in (['single'] if system == 'expgym' else t.STRATEGIES)}
    if {(r['system'], r['scenario'], r['budget'], r['strategy']) for r in selected} != expected:
        raise ValueError('Duplicate or missing GPT resource setting identity')
    fields = ['total_input_tokens', 'output_tokens']
    values = []
    for r in selected:
        displayed = []
        for key in fields:
            known = r[key + '_known_sum']
            missing = r[key + '_unknown_attempts']
            displayed.append(known if int(missing) == 0 else 'unknown；已知小计 ' + known + '，未知尝试 ' + missing)
        values.append([r['system'] + '/' + r['scenario'], r['budget'][5:], r['strategy'],
                       r['execution_complete_jobs'] + '/' + r['planned_jobs'], r['physical_attempts']] + displayed +
                      [r['simulated_feedback_seconds_known_sum'], r['feedback_attempts_known_sum'],
                       r['request_wall_seconds_known_sum']])
    return t.table(['系统/场景', '预算', '策略', '完成/计划 jobs', '全部 HTTP 尝试', 'Input', 'Output',
                    '模拟反馈秒合计', '反馈尝试合计', 'HTTP wall 秒合计（非历时）'], values)


def generate(root):
    from rankings import build as rankings_build
    inputs = read_inputs(root)
    folded = folded_gpt(inputs['gpt_metrics'])
    ga, gb, gc = gpt_outputs(folded)
    native = validate_native(inputs, ga, gb, gc)
    absolute = inputs['prior_absolute'] + ga
    blocks = inputs['prior_blocks'] + gb
    contrasts = inputs['prior_contrasts'] + gc
    for rows in [absolute, blocks, contrasts]:
        rows.sort(key=lambda r: tuple(str(r.get(k, '')) for k in t.IDENTITY + ['outerrep', 'baseline', 'target']))
    t.check_rows(absolute)
    t.check_rows(blocks, True)
    t.check_contrasts(contrasts)
    markers = t.render(absolute, blocks, contrasts)
    rank_markers, rank_files, rank_summary = rankings_build(absolute)
    markers.update(rank_markers)
    markers['GPT_RESOURCES'] = resources_table(inputs['api_resources'])
    template = (root / 'REPORT_TEMPLATE.zh.md').read_text()
    for key, value in markers.items():
        marker = '{{' + key + '}}'
        if template.count(marker) != 1:
            raise ValueError('Expected exactly one marker: ' + marker)
        template = template.replace(marker, value)
    if re.search(r'\{\{[A-Z_]+\}\}', template):
        raise ValueError('Unresolved marker')
    files = dict(rank_files)
    files.update(t.detailed_files(absolute, blocks, contrasts))
    files.update({'README.zh.md': template.encode(), 'absolute_settings.csv': t.csv_bytes(absolute),
                  'by_outerseed.csv': t.csv_bytes(blocks), 'contrasts.csv': t.csv_bytes(contrasts)})
    files['AGGREGATE_CHECKS.json'] = jb(dict(schema='five-model-report-checks-v1',
        absolute_rows=len(absolute), block_rows=len(blocks), contrast_rows=len(contrasts),
        gpt_absolute_rows=len(ga), gpt_block_rows=len(gb), gpt_contrast_rows=len(gc),
        gpt_folded_metric_rows=len(folded), gpt_native_metric_rows=len(inputs['gpt_metrics']),
        native_crosschecks=native, rankings=rank_summary,
        input_manifest_sha256=sha((root / 'INPUTS.json').read_bytes()),
        template_sha256=sha((root / 'REPORT_TEMPLATE.zh.md').read_bytes()),
        scope='Frozen score regrouping, schema/display/rank checks; not independent review or raw verification. '
              'Prior normalized rows imported unchanged. GPT resources retain native all-attempt totals separately.'))
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--freeze-from-workspace', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.freeze_from_workspace:
        if args.check:
            parser.error('freeze and check are mutually exclusive')
        freeze(args.freeze_from_workspace.resolve(), args.output_dir.resolve())
        print('Frozen explicit input snapshots only.')
        return
    outputs = generate(args.output_dir)
    for name, raw in outputs.items():
        path = args.output_dir / name
        if args.check:
            if not path.is_file() or path.read_bytes() != raw:
                raise ValueError('Deterministic output mismatch: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps(dict(mode='check' if args.check else 'generate', files=len(outputs),
                          bytes=sum(map(len, outputs.values())))))


if __name__ == '__main__':
    main()
