#!/usr/bin/env python3
"""Retrospective delivered-configuration utility; never replaces frozen Gap.

Reads only explicit scored exports / their minimal frozen projections. No scorer,
runner, network, raw archive, or model calls. Missing execution is an error, not 0.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
WORKSPACE = Path('/lustrefs/users/chufan.shi/codex_space_tn')
OLD_COMMIT = '9e11134af27102327d8c41dade83211ec5a26da2'
DEEP_COMMIT = '8c79111de3398d12fb36ba349d8f4266f2330200'
MODELS = ('kimi-k3', 'glm-5.3', 'qwen3.8-2.4t-a95b-fp8',
          'deepseek-v4-flash-0731', 'gpt-5.6-sol')
REGIMES = ('cost_free', 'cost_moderate', 'cost_tight')
STRATEGIES = ('naive', 'cached', 'poolact')
FIELDS = ('model system scenario regime strategy slice_kind slice metric value '
          'strict_value valid_agents planned_agents valid_pools planned_pools '
          'any_valid_pools valid_configuration_rate known_agent_mean').split()
COVERAGE_FIELDS = ('model system scenario regime strategy slice_kind slice '
                   'valid_agents planned_agents missing_configuration_agents '
                   'other_failure_agents valid_configuration_rate valid_pools '
                   'planned_pools any_valid_pools expected_units missing_units '
                   'termination_reason_counts evidence').split()
METRIC_FIELDS = ('source_row execution_id model system scenario family item regime '
                 'strategy N outerrep seed metric value known_agent_subset_value '
                 'expected_agents known_agents missing_agents').split()
TERMINAL_FIELDS = ('source_row execution_id model system scenario family item regime '
                   'strategy N seed agent_id execution_complete score_complete '
                   'score_status terminal_classification policy_version '
                   'terminal_origin termination_reason raw_answer_is_null '
                   'raw_answer_perf_is_null').split()
ABS_FIELDS = ('source_row model system scenario slice_kind slice regime strategy '
              'metric N expected_outcomes known_outcomes expected_items '
              'full_mean min_repeats_per_item max_repeats_per_item').split()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csv_bytes(rows, fields):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def parse_csv(data):
    return list(csv.DictReader(io.StringIO(data.decode())))


def number(value):
    if value in ('', None):
        return None
    result = float(value)
    require(math.isfinite(result) and result >= 0, 'invalid frozen Gap')
    return result


def truth(value):
    require(value in ('True', 'False', 'true', 'false', True, False), 'invalid boolean')
    return value in ('True', 'true', True)


def freeze(root=ROOT):
    """One explicit projection pass; records source SHA and CSV data-row ordinal.

    source_row is 1-based DATA row (header excluded), not byte/physical-line offset.
    Answer body/performance never copied; nullness booleans only.
    """
    require(not (root / 'GAP0_INPUTS.json').exists(), 'frozen inputs already exist')
    sources = []
    outputs = {}

    def project(name, path, kind, model=None, url=None):
        data = path.read_bytes()
        original = parse_csv(data)
        result = []
        for i, r in enumerate(original, 1):
            if r['scenario'] != 'tuning':
                continue
            if kind == 'absolute':
                if r['slice_kind'] not in ('all', 'family') or (r['system'] == 'poolact' and r['slice_kind'] != 'all'):
                    continue
                if r['metric'] not in ('gap', 'gap_mi', 'gap_bon'):
                    continue
                result.append({k: str(i) if k == 'source_row' else r[k] for k in ABS_FIELDS})
                continue
            common = dict(source_row=str(i), execution_id=r.get('execution_id', r.get('job_id')),
                          model=model, system=r['system'], scenario=r['scenario'],
                          family=r['family'], item=r['item'], regime=r.get('regime', r.get('budget')),
                          strategy=r['strategy'], N=r['N'], seed=r['seed'])
            if kind == 'metric':
                metric = r['metric']
                if model == 'gpt-5.6-sol':
                    if metric != 'Gap':
                        continue
                    metric = {'single': 'gap', 'MI': 'gap_mi', 'BoN': 'gap_bon'}[r['endpoint']]
                elif metric not in ('gap', 'gap_mi', 'gap_bon'):
                    continue
                common.update(outerrep=str((int(r['seed']) - 2200) // 4), metric=metric,
                              value=r['value'], known_agent_subset_value=r['known_agent_subset_value'],
                              expected_agents=r.get('expected_agents', ''), known_agents=r.get('known_agents', ''),
                              missing_agents=r.get('missing_agents', ''))
            else:
                terminal = json.loads(r['terminal_status'])
                common.update(agent_id=r['agent_id'], execution_complete=r['execution_complete'],
                              score_complete=r['score_complete'], score_status=r['score_status'],
                              terminal_classification=terminal['terminal_classification'],
                              policy_version=terminal['policy_version'], terminal_origin=r.get('terminal_origin', ''),
                              termination_reason=r.get('termination_reason', ''),
                              raw_answer_is_null=str(r['raw_answer'] in ('', 'null')),
                              raw_answer_perf_is_null=str(r['raw_answer_perf'] in ('', 'null')))
                require(terminal['execution_complete'] == truth(r['execution_complete']), 'terminal execution mismatch')
                require(terminal['score_complete'] == truth(r['score_complete']), 'terminal scoring mismatch')
            result.append(common)
        fields = {'absolute': ABS_FIELDS, 'metric': METRIC_FIELDS, 'terminal': TERMINAL_FIELDS}[kind]
        payload = csv_bytes(result, fields)
        rel = f'inputs/{name}.csv'
        outputs[rel] = payload
        sources.append(dict(name=name, local_source=str(path), source_url=url, source_bytes=len(data),
                            source_sha256=sha(data), source_rows=len(original), projected_path=rel,
                            projected_bytes=len(payload), projected_sha256=sha(payload), projected_rows=len(result),
                            selected_fields=fields, projection_kind=kind))

    base = root.parent
    project('strict_absolute', base / 'absolute_settings.csv', 'absolute',
            url=f'https://github.com/tiannuo-yang/LLM_ExpGym/blob/{OLD_COMMIT}/results/five-model-ranking-20260911/absolute_settings.csv')
    for tag, model, directory in (
        ('deep', MODELS[3], WORKSPACE / 'deepseek_flash_eval_20260911/analysis/full_v2'),
        ('gpt', MODELS[4], WORKSPACE / 'LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1'),
    ):
        for kind, filename in [('metric', 'metrics_execution.csv' if tag == 'deep' else 'metrics.csv'),
                               ('terminal', 'raw_terminals.csv')]:
            url = (f'https://github.com/tiannuo-yang/LLM_ExpGym/blob/{DEEP_COMMIT}/results/deepseek-flash-0731-20260911/analysis/full_v2/{filename}'
                   if tag == 'deep' else None)
            project(f'{tag}_{kind}', directory / filename, kind, model, url)
    for rel, data in outputs.items():
        path = root / rel
        require(not path.exists(), 'projection already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    manifest = dict(schema='gap0.frozen-projections.v1', study_type='retrospective Custom study',
                    new_endpoint='delivered-configuration utility Gap0; original strict Gap remains unchanged',
                    source_row_semantics='1-based CSV data-row ordinal; header excluded; not a physical line number',
                    projection='tuning only; exact saved Gap / known-agent subset Gap; selected terminal classifications and nullness only; no answer text, raw performance, prompt or request body',
                    sources=sources)
    (root / 'GAP0_INPUTS.json').write_bytes(json_bytes(manifest))


def load(root):
    manifest = json.loads((root / 'GAP0_INPUTS.json').read_bytes())
    result = {}
    for s in manifest['sources']:
        data = (root / s['projected_path']).read_bytes()
        require(len(data) == s['projected_bytes'] and sha(data) == s['projected_sha256'], 'frozen projection changed')
        rows = parse_csv(data)
        require(len(rows) == s['projected_rows'], 'projection row count mismatch')
        result[s['name']] = rows
    return result


def classify_terminal(t):
    require(truth(t['execution_complete']), 'execution failure or unstarted job cannot become Gap0')
    if truth(t['score_complete']):
        require(t['score_status'] == 'scored_final_answer', 'unexpected scored terminal')
        require(not truth(t['raw_answer_is_null']) and not truth(t['raw_answer_perf_is_null']), 'scored terminal has no configuration/performance')
        return True
    require(t['score_status'] == 'unscorable_missing_configuration', 'tool/scorer/transport failure cannot become Gap0')
    require(t['terminal_classification'] == 'model_no_answer', 'missing terminal is not model no-answer')
    require(t['policy_version'] == 'task-abstention-v1', 'missing policy mismatch')
    require(t['terminal_origin'] in ('', 'normal_loop_return'), 'exceptional terminal cannot become Gap0')
    require(truth(t['raw_answer_is_null']) and truth(t['raw_answer_perf_is_null']), 'missing terminal carries an answer/performance')
    return False


def utility(strict, known, k, n, metric):
    require(n in (1, 4) and 0 <= k <= n, 'invalid N/valid count')
    require(metric in ('gap', 'gap_mi', 'gap_bon'), 'unexpected metric')
    require((metric == 'gap') == (n == 1), 'metric/N mismatch')
    if k == n:
        require(strict is not None and known is not None, 'complete unit missing score')
        require(math.isclose(strict, known, rel_tol=0, abs_tol=1e-10), 'complete known/strict mismatch')
        return strict
    require(strict is None, 'incomplete unit incorrectly has strict score')
    if k == 0:
        require(known is None, 'zero valid agents unexpectedly have a known score')
        return 0.0
    require(known is not None, 'valid agents lack saved known-agent score')
    return known * k / n if metric == 'gap_mi' else known


def make_units(metrics, terminals, model):
    terms = defaultdict(list)
    for t in terminals:
        require(t['model'] == model, 'terminal model mismatch')
        terms[t['execution_id']].append(t)
    grouped = defaultdict(dict)
    for m in metrics:
        require(m['model'] == model, 'metric model mismatch')
        require(m['metric'] not in grouped[m['execution_id']], 'duplicate endpoint')
        grouped[m['execution_id']][m['metric']] = m
    require(set(grouped) == set(terms), 'metric/terminal execution mismatch')
    units = []
    for execution, mm in grouped.items():
        first = next(iter(mm.values()))
        ts = terms[execution]
        n = int(first['N'])
        require(len(ts) == n and {int(t['agent_id']) for t in ts} == set(range(n)), 'incomplete/duplicate agent slots')
        require(set(mm) == ({'gap'} if n == 1 else {'gap_mi', 'gap_bon'}), 'missing endpoint')
        for row in [*ts, *mm.values()]:
            for field in ('execution_id', 'model', 'system', 'scenario', 'family', 'item', 'regime', 'strategy', 'N', 'seed'):
                require(row[field] == first[field], 'within-unit identity mismatch')
        k = sum(classify_terminal(t) for t in ts)
        out = {key: first[key] for key in ('execution_id', 'model', 'system', 'scenario', 'family', 'item', 'regime', 'strategy', 'seed')}
        out.update(n=n, k=k, strict={}, gap0={}, known={}, terminals=ts)
        for metric, row in mm.items():
            if row['expected_agents']:
                require((int(row['expected_agents']), int(row['known_agents']), int(row['missing_agents'])) == (n, k, n-k), 'source counts contradict terminals')
            strict, known = number(row['value']), number(row['known_agent_subset_value'])
            out['strict'][metric] = strict
            out['known'][metric] = known
            out['gap0'][metric] = utility(strict, known, k, n, metric)
        units.append(out)
    validate_plan(units)
    return units


def validate_plan(units):
    require(len(units) == 135, 'expected exactly 135 planned tuning units per model')
    for system in ('expgym', 'poolact'):
        selected = [u for u in units if u['system'] == system]
        items = {u['item'] for u in selected}
        require(len(items) == (9 if system == 'expgym' else 3), 'unexpected tuning item count')
        expected = {(item, regime, strategy, seed) for item in items
                    for regime in (REGIMES if system == 'expgym' else REGIMES[1:])
                    for strategy in (('single',) if system == 'expgym' else STRATEGIES)
                    for seed in ('2200', '2204', '2208')}
        actual = [(u['item'], u['regime'], u['strategy'], u['seed']) for u in selected]
        require(len(actual) == len(set(actual)) and set(actual) == expected, 'missing/extra planned tuning slots')
        require(all(u['n'] == (1 if system == 'expgym' else 4) for u in selected), 'wrong plan N')
    require(len({u['item'] for u in units if u['family'] == 'paramnet'}) == 3, 'wrong ParamNet scope')
    require(len({u['item'] for u in units if u['family'] == 'nasbench101'}) == 3, 'wrong NAS101 scope')
    require(len({u['item'] for u in units if u['family'] == 'nasbench201'}) == 3, 'wrong NAS201 scope')


def item_mean(units, values):
    by_item = defaultdict(list)
    for u, value in zip(units, values):
        by_item[u['item']].append(value)
    require(bool(by_item), 'empty aggregate')
    return mean(mean(v) for v in by_item.values())


def build(root=ROOT):
    """Return (120 setting rows, 90 coverage rows, checks), all JSON serializable.

    valid_pools is ALL N configs delivered; any_valid_pools is >=1 config.
    Both pool counters are null for ExpGym. known_agent_mean is the pooled mean
    over actually scored agents (explicitly a selected subset, not full endpoint).
    """
    root = Path(root)
    inputs = load(root)
    units = {model: make_units(inputs[tag + '_metric'], inputs[tag + '_terminal'], model)
             for tag, model in (('deep', MODELS[3]), ('gpt', MODELS[4]))}
    rows, coverage = [], []
    source_rows = inputs['strict_absolute']
    seen = set()
    for native in source_rows:
        model, system, metric = native['model'], native['system'], native['metric']
        require(model in MODELS, 'unexpected model')
        keyfields = ('model', 'system', 'scenario', 'regime', 'strategy', 'slice_kind', 'slice')
        key = tuple(native[k] for k in keyfields)
        require((*key, metric) not in seen, 'duplicate aggregate endpoint')
        seen.add((*key, metric))
        row = {k: native[k] for k in keyfields}
        row['metric'] = {'gap': 'gap0', 'gap_mi': 'gap0_mi', 'gap_bon': 'gap0_bon'}[metric]
        strict = number(native['full_mean'])
        if model in units:
            us = [u for u in units[model] if u['system'] == system and u['regime'] == native['regime']
                  and u['strategy'] == native['strategy']
                  and (native['slice_kind'] == 'all' or u['family'] == native['slice'])]
            require(len(us) == int(native['expected_outcomes']), 'native expected units mismatch')
            require(sum(u['strict'][metric] is not None for u in us) == int(native['known_outcomes']), 'native known units mismatch')
            require(len({u['item'] for u in us}) == int(native['expected_items']), 'native item count mismatch')
            value = item_mean(us, [u['gap0'][metric] for u in us])
            strict_values = [u['strict'][metric] for u in us]
            reconstructed = item_mean(us, strict_values) if all(v is not None for v in strict_values) else None
            require((strict is None) == (reconstructed is None), 'strict missingness mismatch')
            if strict is not None:
                require(math.isclose(strict, reconstructed, rel_tol=0, abs_tol=1e-10), 'strict aggregate mismatch')
            valid, planned = sum(u['k'] for u in us), sum(u['n'] for u in us)
            valid_pools = sum(u['k'] == u['n'] for u in us) if system == 'poolact' else None
            planned_pools = len(us) if system == 'poolact' else None
            any_valid = sum(u['k'] > 0 for u in us) if system == 'poolact' else None
            mi_metric = 'gap' if system == 'expgym' else 'gap_mi'
            known_mean = sum((u['known'][mi_metric] or 0) * u['k'] for u in us) / valid if valid else None
            reasons = Counter(t['termination_reason'] or 'not_exported_in_terminal_projection'
                              for u in us for t in u['terminals'] if not truth(t['score_complete']))
            evidence = 'explicit_per_agent_normal_terminal_and_saved_scores'
        else:
            require(strict is not None and native['known_outcomes'] == native['expected_outcomes'], 'historical complete endpoint missing')
            require(native['min_repeats_per_item'] == native['max_repeats_per_item'] == '3', 'historical repeat mismatch')
            value = strict
            valid = planned = int(native['expected_outcomes']) * int(native['N'])
            valid_pools = planned_pools = any_valid = int(native['expected_outcomes']) if system == 'poolact' else None
            # For BoN, use the matching complete MI aggregate for mean-agent Gap.
            if metric == 'gap_bon':
                match = [r for r in source_rows if tuple(r[k] for k in keyfields) == key and r['metric'] == 'gap_mi']
                require(len(match) == 1, 'complete MI counterpart missing')
                known_mean = number(match[0]['full_mean'])
            else:
                known_mean = strict
            reasons, evidence = {}, 'previously_validated_complete_strict_endpoint_N_times_expected_outcomes'
        row.update(value=value, strict_value=strict, valid_agents=valid, planned_agents=planned,
                   valid_pools=valid_pools, planned_pools=planned_pools, any_valid_pools=any_valid,
                   valid_configuration_rate=valid/planned, known_agent_mean=known_mean)
        rows.append(row)
        if metric in ('gap', 'gap_mi'):
            c = {k: native[k] for k in keyfields}
            c.update(valid_agents=valid, planned_agents=planned, missing_configuration_agents=planned-valid,
                     other_failure_agents=0, valid_configuration_rate=valid/planned,
                     valid_pools=valid_pools, planned_pools=planned_pools, any_valid_pools=any_valid,
                     expected_units=int(native['expected_outcomes']), missing_units=0,
                     termination_reason_counts=json.dumps(dict(reasons), ensure_ascii=False, sort_keys=True), evidence=evidence)
            coverage.append(c)
    sortkey = lambda r: (MODELS.index(r['model']), r['system'], r['slice_kind'], r['slice'], REGIMES.index(r['regime']), r['strategy'], r.get('metric', ''))
    rows.sort(key=sortkey)
    coverage.sort(key=sortkey)
    require(len(rows) == 120 and len(coverage) == 90, 'aggregate matrix row count mismatch')
    checks = dict(schema='gap0.checks.v1', retrospective=True, original_strict_gap_unchanged=True,
                  setting_rows=len(rows), coverage_rows=len(coverage), zero_for_execution_failures=False,
                  scorer_calls=0, raw_request_or_trace_artifact_reads=0, model_calls=0,
                  plan_complete={m: len(us) for m, us in units.items()},
                  terminal_counts={m: dict(planned=sum(u['n'] for u in us), valid=sum(u['k'] for u in us),
                                           missing_configuration=sum(u['n']-u['k'] for u in us), other_failure=0)
                                   for m, us in units.items()},
                  strict_endpoint_identity_checks=len(source_rows),
                  strict_aggregate_recomputed_checks=sum(r['model'] in units for r in source_rows),
                  inherited_complete_endpoint_checks=sum(r['model'] not in units for r in source_rows),
                  input_manifest_sha256=sha((root/'GAP0_INPUTS.json').read_bytes()),
                  rules=['Only completed normal task-abstention missing configuration receives utility 0; no invented evaluated configuration.',
                         'Scored agent Gap retained; no upper clip at 100.',
                         'MI0 = sum delivered-agent Gap / fixed N4; BoN0 = maximum delivered-agent Gap or 0 if none.',
                         'Average repetitions within item, then weight planned items equally.',
                         'Original strict Gap and its unknown entries are preserved, not replaced.',
                         'Known-agent mean is a selected-agent description and is not the full endpoint.',
                         'DeepSeek detailed loop termination reason is absent from this frozen export; only normal return / missing configuration is established.'])
    return rows, coverage, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze-from-workspace', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.freeze_from_workspace:
        require(not args.check, 'cannot freeze while checking')
        freeze()
    rows, coverage, checks = build()
    outputs = {'gap0_settings.csv': csv_bytes(rows, FIELDS),
               'missing_output_summary.csv': csv_bytes(coverage, COVERAGE_FIELDS),
               'GAP0_CHECKS.json': json_bytes(checks)}
    for name, data in outputs.items():
        path = ROOT / name
        if args.check:
            require(path.read_bytes() == data, f'generated output mismatch: {name}')
        else:
            path.write_bytes(data)
    print(json.dumps(dict(checked=args.check, outputs=len(outputs), setting_rows=len(rows), coverage_rows=len(coverage))))


if __name__ == '__main__':
    main()
