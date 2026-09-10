"""Report-only extraction from sealed CSV/JSON; no scorer, raw or writes."""
import collections
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import sys

OP = Path(__file__).resolve().parent.parent
REFS = {}
PERFORMANCE = {'f1', 'f1_mi', 'f1_mv', 'evidence_acc', 'evidence_acc_mi',
               'evidence_acc_mv', 'label_acc', 'label_acc_mi', 'label_acc_mv',
               'gap', 'gap_mi', 'gap_bon', 'raw_perf', 'raw_perf_mi', 'raw_perf_bon'}


def read(path, expected=None):
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
    ref = {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if expected:
        assert ref['sha256'] == expected['sha256']
        if 'bytes' in expected:
            assert ref['bytes'] == expected['bytes']
    REFS[str(path)] = ref
    return data


def export(name, pin):
    directory = OP / name
    index = json.loads(read(directory / 'EXPORT_INDEX.json', {'sha256': pin}))
    assert set(p.name for p in directory.iterdir()) == set(index['files']) | {'EXPORT_INDEX.json'}
    return {name: read(directory / name, ref) for name, ref in index['files'].items()}


def rows(data):
    return list(csv.DictReader(io.StringIO(data.decode())))


def affected(r):
    if r['scenario'] != 'tuning':
        return False
    common = {'all', 'family=nasbench101', 'task=hpobench:nasbench101:C'}
    if r['system'] == 'expgym':
        return r['slice'] in common
    if r['regime'] == 'cost_moderate':
        permitted = common if r['strategy'] == 'cached' else common | {'task=hpobench:nasbench101:A', 'task=hpobench:nasbench101:B'}
        return r['strategy'] in {'cached', 'poolact'} and r['slice'] in permitted
    return r['regime'] == 'cost_tight' and r['strategy'] == 'poolact' and r['slice'] in common


def sign(r):
    if not r['effect']:
        return 'unknown'
    value = float(r['effect'])
    return 'positive' if value > 0 else 'negative' if value < 0 else 'zero'


def model_summary(data):
    effects = rows(data['effects.csv'])
    metrics = rows(data['metrics.csv'])
    logical = rows(data['logical_outcomes.csv'])
    result = json.loads(data['results.json'])
    assert len(effects) == 514 and len(metrics) == 7687 and len(logical) == 783
    assert len(rows(data['paired_rows.csv'])) == 5393
    assert all(not r['ci'] and not r['p_value'] for r in effects)
    primary = [r for r in effects if r['role'] == 'primary']
    assert len(primary) == 6
    for r in primary:
        values = json.loads(r['outer_bundle_effects'])
        assert abs(statistics.mean(values) - float(r['effect'])) < 1e-12
        if len(values) == 3:
            assert r['outerrep_descriptive_sd'] and float(r['outerrep_descriptive_sd']) >= 0
        else:
            assert not r['outerrep_descriptive_sd']
    return {
        'primary_csv_exact': primary,
        'all_effect_counts': dict(collections.Counter(sign(r) for r in effects)),
        'negative_performance_csv_exact': [r for r in effects if r['metric'] in PERFORMANCE and sign(r) == 'negative'],
        'unknown_comparison_metrics': dict(collections.Counter(r['metric'] for r in effects if sign(r) == 'unknown')),
        'null_metric_cells': dict(collections.Counter(r['metric'] for r in metrics if not r['value'])),
        'logical_execution_counts': dict(collections.Counter(r['execution_state'] for r in logical)),
        'logical_score_counts': dict(collections.Counter(r['score_state'] for r in logical)),
        'model_no_answer_agents': sum(int(r['model_no_answer_count']) for r in logical),
        'logical_with_model_no_answer': sum(int(r['model_no_answer_count']) > 0 for r in logical),
        'cost_coverage': result['cost_coverage'],
        'gap_above_100_cells': [r for r in metrics if r['metric'] in {'gap', 'gap_mi', 'gap_bon'} and r['value'] and float(r['value']) > 100],
    }


assert sys.executable == '/usr/bin/python3' and sys.version_info[:3] == (3, 10, 12)
old = export('actual_formal_export_k3_node_failure_v2', 'ababd4141ab276e32dfa9ec07b39c6b68a571850b6469f3657033f65bd882ba7')
new = export('actual_k3_fixed8_composite_export_v2_py311_final', 'fc68a5a057c45056924b17b91f054311d6cd43dc8174da85892265f8d7758f86')
glm = export('actual_formal_export_glm_completed_v2', 'e32cab1af07054e76503aab79c66b76bcc216d2021cf0f46cd638340023bbca7')
old_effects = {r['comparison']: r for r in rows(old['effects.csv'])}
new_effects = {r['comparison']: r for r in rows(new['effects.csv'])}
assert set(old_effects) == set(new_effects) and len(old_effects) == 514
impact = [k for k, r in old_effects.items() if affected(r)]
assert len(impact) == 173
sd_deltas = []
for key, a in old_effects.items():
    b = new_effects[key]
    changes = [f for f in a if a[f] != b[f]]
    if key not in impact:
        assert not changes, (key, changes)
assert not sd_deltas
old_logical = {r['logical_id']: r for r in rows(old['logical_outcomes.csv'])}
new_logical = {r['logical_id']: r for r in rows(new['logical_outcomes.csv'])}
changed_logical = [k for k in old_logical if old_logical[k] != new_logical[k]]
selection = json.loads(new['COMPOSITE_PROVENANCE.json'])['effective_selection']
recovery_ids = {r['invocation_id'] for r in selection if r['selected_segment'] == 'recovery'}
assert len(recovery_ids) == 8
assert len(changed_logical) == 8 and {new_logical[k]['invocation_id'] for k in changed_logical} == recovery_ids
assert all(old_effects[k] == new_effects[k] for k in old_effects if old_effects[k]['role'] == 'primary' and k != 'kimi-k3__E-H')
old_negative = [r for r in old_effects.values() if r['metric'] in PERFORMANCE and sign(r) == 'negative']
assert len(old_negative) == 23 and all(r == new_effects[r['comparison']] for r in old_negative)
fixed_keys = {tuple(new_logical[k][f] for f in ['model','system','scenario','item','regime','strategy','outerseed']) for k in changed_logical}
old_metrics, new_metrics = rows(old['metrics.csv']), rows(new['metrics.csv'])
fields = ['model','system','scenario','item','regime','strategy','outerseed']
assert len(old_metrics) == len(new_metrics)
unaffected_cells = 0
for a, b in zip(old_metrics, new_metrics):
    assert tuple(a[f] for f in fields+['metric']) == tuple(b[f] for f in fields+['metric'])
    if tuple(a[f] for f in fields) not in fixed_keys:
        assert a == b
        unaffected_cells += 1
output = {
    'schema': 'dual-model-fixed8-report-numerical-check-v2',
    'scope': 'sealed export metadata only; no raw/scorer/model; author check, not independent scientific acceptance',
    'runtime': {'executable': sys.executable, 'version': sys.version},
    'models': {'kimi-k3': model_summary(new), 'glm-5.3': model_summary(glm)},
    'invariance': {
        'comparisons': 514, 'task_affected_comparisons': 173, 'task_unaffected_comparisons': 341,
        'whole_csv_rows_exact': sum(old_effects[k] == new_effects[k] for k in old_effects),
        'became_complete': sum(a['status'] == 'unknown_incomplete_endpoint' and new_effects[k]['status'] == 'descriptive_complete' for k,a in old_effects.items()),
        'sd_only_deltas': sd_deltas, 'strict_task_unaffected_rows_exact': 341,
        'analysis_profiles': {'kimi-k3': 'CPython 3.11.15 final merge', 'glm-5.3': 'CPython 3.10.12 public-byte replay'},
        'historical_python_identity_not_inferred': True,
        'fixed8_invocation_ids': sorted(recovery_ids), 'changed_logical_rows': 8,
        'unchanged_logical_rows_including_source_sha': 775, 'unchanged_metric_rows_outside_fixed8': unaffected_cells,
        'old_negative_performance_rows_exact': 23, 'five_k3_primary_rows_exact': True,
    },
    'author_source_ref': {'path': str(Path(__file__).resolve()), 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    'input_refs': list(REFS.values()),
}
print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
