#!/usr/bin/env python3
"""Recompute all adopted Audit behavior/evidence rows, or replay public tables.

Private mode reads every selected raw trace and versioned scoring overlay.
Public replay needs only the exported per-hypothesis/per-trace/per-agent rows.
Neither mode calls a model, alters a raw trace, or infers new actions.
"""
import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


TEXT_FIELDS = {'slot_id', 'model', 'budget', 'regime', 'strategy', 'source_cohort',
               'source_sha256', 'trace_sha256', 'result_sha256', 'cohort_id',
               'hypothesis', 'gold_label', 'gold_evidence_ids', 'submitted_evidence_ids',
               'first_visible_evidence_ids', 'first_visible_feedback_status',
               'termination_reason', 'answer_source', 'answer_change_reason',
               'score_version', 'free_slot_id', 'tight_slot_id', 'free_source_sha256',
               'tight_source_sha256', 'free_first_partial_and_tight_final_ids',
               'source_origin', 'historical_source_sha256', 'old_source_sha256', 'new_source_sha256'}

PUBLIC_SOURCE_FIELDS = {'slot_id', 'model', 'system', 'scenario', 'item', 'regime',
                        'strategy', 'seed', 'order', 'outer_repeat', 'execution_complete',
                        'score_complete', 'provider', 'cohort_id', 'selection',
                        'result_sha256', 'source_sha256', 'historical_source_sha256',
                        'source_origin'}


def read_leaf_dataset(base):
    return {'traces': read_csv(base / 'n1/trace_metrics.csv'),
            'hypotheses': read_csv(base / 'n1/hypothesis_metrics.csv'),
            'pools': read_csv(base / 'coordination/audit_pools.csv'),
            'agents': read_csv(base / 'coordination/audit_agents.csv')}


def read_csv(path):
    rows = list(csv.DictReader(path.open()))
    for row in rows:
        for key, value in row.items():
            if key in TEXT_FIELDS or value == '':
                continue
            try:
                row[key] = int(value)
            except ValueError:
                try:
                    row[key] = float(value)
                except ValueError:
                    pass
    return rows


class MemorySource:
    """Feed a copy to old pure analysis code without editing source files."""
    def __init__(self, obj, slot_id):
        self.raw = json.dumps(obj, ensure_ascii=False).encode()
        self.slot_id = slot_id

    def read_bytes(self):
        return self.raw

    def __str__(self):
        return self.slot_id


def safe_audit_parser(parser, invalid_result=None):
    def parse(value):
        try:
            return parser(value)
        except (ValueError, TypeError, OverflowError, RecursionError):
            return invalid_result
    return parse


def extract_all(args):
    implementation_names = ('expgym/tool_protocol.py', 'expgym/task_evidence_audit.py', 'expgym/poolact.py')
    implementation_sha = {name: sha((args.repo / name).read_bytes()) for name in implementation_names}
    overlay_sha = sha(args.overlays.read_bytes())
    score_checks_path = args.score_checks or args.overlays.parent.parent / 'CHECKS.json'
    score_checks_raw = score_checks_path.read_bytes()
    score_checks = json.loads(score_checks_raw)
    assert score_checks['status'] == 'PASS'
    assert all(score_checks['code_sha256'][name] == digest for name, digest in implementation_sha.items()), 'Overlay and behavior scorer source must match'
    sys.path.insert(0, str(args.repo.resolve()))
    from expgym.tool_protocol import parse_audit_answer, ANSWER_PROTOCOL_VERSION
    old_n1 = module('audit_old_n1', '_historical_n1.py')
    new_n1 = module('audit_new_n1', '_historical_n1.py')
    old_coord = module('audit_old_coord', '_historical_coordination.py')
    new_coord = module('audit_new_coord', '_historical_coordination.py')
    new_n1.parse_answer = safe_audit_parser(parse_audit_answer, {})
    new_coord.parse_answer = safe_audit_parser(parse_audit_answer)
    sources = json.loads(args.sources.read_text())
    sources = [r for r in sources if r['scenario'] == 'evidence_audit']
    assert Counter(r['system'] for r in sources) == {'expgym': 702, 'poolact': 468}
    overlays = {}
    for line in args.overlays.open():
        row = json.loads(line)
        if row['scenario'] == 'evidence_audit':
            key = (row['slot_id'], str(row['agent_id']))
            assert key not in overlays
            overlays[key] = row
    expected_overlay_count = 702 + 468 * 5
    assert len(overlays) == expected_overlay_count, (len(overlays), expected_overlay_count)
    gold_raw = args.gold.read_bytes()
    gold_sha = sha(gold_raw)
    gold_docs = json.loads(gold_raw)['documents']

    def one(source):
        raw = Path(source['source_path']).read_bytes()
        digest = sha(raw)
        assert digest == source['result_sha256'], source['slot_id']
        stored = json.loads(raw)
        item_index = int(source['item'].rsplit(':', 1)[1])
        if source['system'] == 'expgym':
            assert int(stored['task']['item']['id']) == item_index
            assert stored['task']['budget']['regime'] == source['regime']
            assert int(stored['task']['rep']) == int(source['order'])
        else:
            assert int(stored['config']['question_index']) == item_index
            assert stored['config']['cost_regime'] == source['regime']
            assert stored['strategy'] == source['strategy']
        origin = source.get('source_origin', 'existing_trace_rescored')
        historical_sha = source.get('historical_source_sha256', digest)
        common = dict(slot_id=source['slot_id'], source_sha256=digest,
                      source_origin=origin, historical_source_sha256=historical_sha)
        result = {'source': {k: source[k] for k in source if k in PUBLIC_SOURCE_FIELDS}}
        for version in (('new',) if args.baseline_report else ('old', 'new')):
            obj = copy.deepcopy(stored)
            if source['system'] == 'expgym':
                overlay = overlays[(source['slot_id'], '-1')]
                assert overlay['source_sha256'] == digest
                if version == 'new':
                    obj['outcome'].update(answer=overlay['new_answer'],
                                          scoring_input=overlay['new_scoring_input'])
                    obj['outcome']['score']['metrics'] = overlay['new_score_metrics']
                helper = old_n1 if version == 'old' else new_n1
                trace, hypotheses = helper.analyze(
                    (source['model'], source['cohort_id'], MemorySource(obj, source['slot_id'])),
                    gold_docs, gold_sha)
                for row in [trace] + hypotheses:
                    row.pop('trace_path', None)
                    row.update(common, agent_id=-1, score_version=version,
                               answer_change_reason=(overlay.get('answer_changed_reason', overlay.get('reason', '')) or ''))
                    if digest != historical_sha:
                        row['answer_change_reason'] = 'adopted_complete_runtime_control:' + row['answer_change_reason']
                trace.update(trace_sha256=digest, trace_bytes=len(raw),
                             verification_eff=obj['outcome']['score']['metrics'].get('verification_eff'))
                joint = sum(h['joint_correct'] for h in hypotheses)
                trace['visible_verification_eff'] = (
                    sum(h['joint_correct'] and h['submitted_exactly_verified'] for h in hypotheses)
                    / joint if joint else None)
                result[version] = {'traces': [trace], 'hypotheses': hypotheses}
            else:
                for index, agent in enumerate(obj['agent_results']):
                    aid = agent.get('agent_id', index)
                    overlay = overlays[(source['slot_id'], str(aid))]
                    assert overlay['source_sha256'] == digest
                    if version == 'new':
                        agent.update(answer=overlay['new_answer'],
                                     scoring_input=overlay['new_scoring_input'],
                                     answer_metrics=overlay['new_score_metrics'])
                    scoring_helper = old_n1 if version == 'old' else new_n1
                    prediction = scoring_helper.parse_answer(agent.get('scoring_input', agent.get('answer')))
                    gold = gold_docs[int(obj['config']['question_index'])]['annotation_sets'][0]['annotations']
                    labels = evidence = 0
                    for hypothesis, entry in gold.items():
                        submitted = prediction.get(hypothesis)
                        if not isinstance(submitted, dict):
                            continue
                        labels += submitted.get('label') == entry['choice']
                        evidence += (scoring_helper.ids(submitted.get('evidence_ids', []))
                                     == scoring_helper.ids(entry.get('spans', [])))
                    for metric, actual in [('label_acc', labels/len(gold)), ('evidence_acc', evidence/len(gold))]:
                        assert math.isclose(actual, agent['answer_metrics'][metric], abs_tol=1e-12), (
                            source['slot_id'], aid, version, metric, actual, agent['answer_metrics'][metric])
                aggregate_overlay = overlays[(source['slot_id'], 'aggregate')]
                assert aggregate_overlay['source_sha256'] == digest
                if version == 'new':
                    obj['aggregate'].update(answer=aggregate_overlay['new_answer'],
                                            answer_metrics=aggregate_overlay['new_score_metrics'])
                config = obj['config']
                selected = {(config['model'], config['cost_regime'], obj['strategy']): source['cohort_id']}
                helper = old_coord if version == 'old' else new_coord
                pool, agents = helper.extract(
                    (source['cohort_id'], MemorySource(obj, source['slot_id']), None), selected)
                for row in [pool] + agents:
                    row.pop('result_path', None)
                    row.update(common, model=source['model'], score_version=version)
                pool.update(result_sha256=digest, bytes=len(raw))
                pool['answer_change_reason'] = 'member_terminal_extraction_and_common_audit_wrapper_acceptance'
                if digest != historical_sha:
                    pool['answer_change_reason'] = 'adopted_complete_runtime_control_and_uniform_final_scoring'
                pool.update({key: obj['aggregate']['answer_metrics'].get(key)
                             for key in ('label_acc', 'evidence_acc', 'verification_eff')})
                for row in agents:
                    overlay = overlays[(source['slot_id'], str(row['agent_id']))]
                    row['answer_change_reason'] = (overlay.get('answer_changed_reason', overlay.get('reason', '')) or '')
                    if digest != historical_sha:
                        row['answer_change_reason'] = 'adopted_complete_runtime_control:' + row['answer_change_reason']
                    actual = next(a for i, a in enumerate(obj['agent_results'])
                                  if a.get('agent_id', i) == row['agent_id'])
                    row['verification_eff'] = actual['answer_metrics'].get('verification_eff')
                result[version] = {'pools': [pool], 'agents': agents}
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        extracted = list(pool.map(one, sources))
    versions = {v: {k: [] for k in ('traces', 'hypotheses', 'pools', 'agents')}
                for v in ('old', 'new')}
    for item in extracted:
        for version in versions:
            for key, rows in item.get(version, {}).items():
                versions[version][key].extend(rows)
    if args.baseline_report:
        versions['old'] = read_leaf_dataset(args.baseline_report / 'old')
        baseline_hashes = {r['slot_id']: r['source_sha256'] for group in ('traces', 'pools')
                           for r in versions['old'][group]}
        assert set(baseline_hashes) == {r['slot_id'] for r in sources}
        for source in sources:
            expected_historical = source.get('historical_source_sha256', source['result_sha256'])
            assert expected_historical == baseline_hashes[source['slot_id']], source['slot_id']
            if source['result_sha256'] != expected_historical:
                assert source.get('source_origin') == 'new_runtime_control', source['slot_id']
    for data in versions.values():
        data['traces'].sort(key=lambda r: (r['model'], r['budget'], r['doc_index'], r['order']))
        data['hypotheses'].sort(key=lambda r: (r['model'], r['budget'], r['doc_index'], r['order'], r['position']))
        data['pools'].sort(key=lambda r: (r['model'], r['regime'], r['strategy'], r['question_index']))
        data['agents'].sort(key=lambda r: (r['model'], r['regime'], r['strategy'], r['question_index'], r['agent_id']))
    metadata = {'mode': 'private_full_census', 'answer_protocol_version': ANSWER_PROTOCOL_VERSION,
                'sources_sha256': sha(args.sources.read_bytes()),
                'overlays_sha256': overlay_sha, 'gold_sha256': gold_sha,
                'source_count': len(sources), 'raw_files_sha_verified': len(sources),
                'overlay_count': len(overlays), 'model_calls': 0,
                'source_files': [item['source'] for item in extracted]}
    replacements = [r for r in sources if r.get('historical_source_sha256', r['result_sha256']) != r['result_sha256']]
    metadata['adopted_source_replacements'] = dict(Counter(r['system'] for r in replacements))
    metadata['adopted_source_replacement_count'] = len(replacements)
    if args.require_adopted_controls:
        assert Counter(r['system'] for r in replacements) == {'expgym': 2, 'poolact': 18}, replacements
    if args.baseline_report:
        metadata['frozen_baseline_leaf_sha256'] = {
            name: sha((args.baseline_report / 'old' / name).read_bytes()) for name in
            ('n1/trace_metrics.csv', 'n1/hypothesis_metrics.csv', 'coordination/audit_pools.csv', 'coordination/audit_agents.csv')}
    metadata['upstream_score_checks_sha256'] = sha(score_checks_raw)
    metadata['core_repair_commit'] = score_checks.get('core_repair_commit')
    assert overlay_sha == sha(args.overlays.read_bytes()), 'Scoring overlays changed during analysis'
    assert implementation_sha == {name: sha((args.repo / name).read_bytes()) for name in implementation_names}, 'Scoring source changed during analysis'
    metadata['implementation_sha256'] = implementation_sha
    return versions, metadata


def aggregate_n1(data, target):
    helper = module('audit_aggregate_n1', '_historical_n1.py')
    traces, hypotheses = data['traces'], data['hypotheses']
    assert len(traces) == 702 and len(hypotheses) == 11934
    assert len({(r['model'], r['budget'], r['doc_index'], r['order']) for r in traces}) == 702
    excluded = {'doc_index', 'doc_id', 'order', 'trace_bytes', 'hypothesis_count', 'agent_id'}
    metrics = list(dict.fromkeys(k for r in traces for k, v in r.items()
                                if isinstance(v, (int, float)) and k not in excluded))
    docs = helper.aggregate(traces, ['model', 'budget', 'doc_index'], metrics)
    models = helper.aggregate(docs, ['model', 'budget'], metrics)
    budgets = helper.aggregate(models, ['budget'], metrics)
    for name, rows in [('trace_metrics', traces), ('hypothesis_metrics', hypotheses),
                       ('document_metrics', docs), ('model_budget_metrics', models), ('budget_metrics', budgets)]:
        write_csv(target / (name + '.csv'), rows)
    counts = []
    for budget in ('cost_free', 'cost_moderate', 'cost_tight'):
        group = [r for r in hypotheses if r['budget'] == budget]
        for model in ['ALL'] + sorted({r['model'] for r in group}):
            sub = group if model == 'ALL' else [r for r in group if r['model'] == model]
            for subset in ('all', 'nonempty', 'empty'):
                selected = sub if subset == 'all' else [r for r in sub if bool(r['gold_nonempty']) == (subset == 'nonempty')]
                row = dict(budget=budget, model=model, gold_subset=subset, n_hypothesis_presentations=len(selected))
                for key in ('label_correct', 'evidence_exact', 'joint_correct', 'label_correct_wrong_evidence',
                            'missing_any', 'extra_any', 'queried', 'ever_exact_proposal', 'wrong_first_final_exact',
                            'exact_seen_final_wrong', 'revised_after_wrong'):
                    row[key] = sum(r[key] for r in selected)
                row['queried_first_wrong'] = sum(r['first_proposal_exact'] == 0 for r in selected)
                row['queried_first_correct'] = sum(r['first_proposal_exact'] == 1 for r in selected)
                counts.append(row)
    write_csv(target / 'diagnostic_counts.csv', counts)
    paired = {(r['model'], r['budget'], r['doc_index'], r['order'], r['hypothesis']): r for r in hypotheses}
    patterns = []
    for free in hypotheses:
        if free['budget'] != 'cost_free' or not free['joint_correct'] or free['first_visible_feedback_status'] != 'Evidence Incomplete':
            continue
        tight = paired[(free['model'], 'cost_tight', free['doc_index'], free['order'], free['hypothesis'])]
        if not tight['label_correct'] or not tight['missing_any'] or tight['extra_any'] or tight['queried']:
            continue
        if free['first_visible_evidence_ids'] != tight['submitted_evidence_ids']:
            continue
        patterns.append(dict(model=free['model'], doc_index=free['doc_index'], order=free['order'],
                             hypothesis=free['hypothesis'], gold_evidence_ids=free['gold_evidence_ids'],
                             free_first_partial_and_tight_final_ids=tight['submitted_evidence_ids'],
                             free_feedback_calls=free['visible_feedback_calls'],
                             free_exact_feedback_seen=free['ever_exact_proposal'],
                             free_slot_id=free['slot_id'], tight_slot_id=tight['slot_id'],
                             free_source_sha256=free['source_sha256'], tight_source_sha256=tight['source_sha256']))
    write_csv(target / 'paired_completion_patterns.csv', patterns)
    data.update(documents=docs, model_budgets=models, budgets=budgets, diagnostic_counts=counts, patterns=patterns)


def aggregate_coordination(data, target):
    pools, agents = data['pools'], data['agents']
    assert len(pools) == 468 and len(agents) == 1872
    groups = defaultdict(list)
    for row in pools:
        groups[(row['model'], row['regime'], row['strategy'])].append(row)
    assert len(groups) == 36 and all(len(g) == 13 for g in groups.values())
    numeric = list(dict.fromkeys(k for row in pools for k, v in row.items()
                                if isinstance(v, (int, float)) and k not in {'question_index', 'bytes'}))
    aggregates = []
    for key, group in sorted(groups.items()):
        row = dict(model=key[0], regime=key[1], strategy=key[2], pools=len(group))
        for name in numeric:
            values = [r[name] for r in group if isinstance(r.get(name), (int, float))]
            row['mean_' + name] = statistics.mean(values) if values else ''
        aggregates.append(row)
    for name, rows in [('audit_pools', pools), ('audit_agents', agents), ('audit_groups', aggregates)]:
        write_csv(target / (name + '.csv'), rows)
    data['groups'] = aggregates


def changes(versions, output):
    old, new = versions['old'], versions['new']
    def same(left, right):
        # CSV encodes an unavailable scalar as an empty field, while raw JSON
        # uses null. A source override must not create a spurious behavior delta.
        return left == right or (left in (None, '') and right in (None, ''))
    unchanged_behavior_fields = {
        'traces': ('tool_calls', 'visible_tool_calls', 'distinct_hypotheses', 'repeat_calls',
                   'first_fixed_example', 'termination_reason', 'answer_source', 'agent_steps',
                   'simulated_feedback_cost', 'budget_limit', 'visible_distinct_hypotheses',
                   'visible_repeat_calls', 'hidden_result_count'),
        'pools': ('feedback_attempts', 'feedback_visible', 'unique_query_attempts',
                  'unique_visible_queries', 'visible_hypotheses', 'cache_hits', 'cache_size',
                  'semantic_redundancy_fraction', 'peer_snapshot_count'),
        'agents': ('feedback_attempts', 'feedback_visible', 'withheld', 'unique_query_attempts',
                   'unique_visible_queries', 'visible_hypotheses', 'termination_reason',
                   'peer_snapshot_count', 'own_verified_correct_queries',
                   'peer_verified_correct_queries', 'peer_only_verified_correct_queries')}
    changed_counts = {}
    for dataset, keys in [('traces', ('slot_id',)), ('hypotheses', ('slot_id', 'hypothesis')),
                          ('agents', ('slot_id', 'agent_id')), ('pools', ('slot_id',))]:
        before = {tuple(r[k] for k in keys): r for r in old[dataset]}
        after = {tuple(r[k] for k in keys): r for r in new[dataset]}
        assert before.keys() == after.keys()
        rows = []
        for key, a in before.items():
            b = after[key]
            source_replaced = a['source_sha256'] != b['source_sha256']
            if not source_replaced:
                for behavior in unchanged_behavior_fields.get(dataset, ()):
                    assert same(a[behavior], b[behavior]), (dataset, key, behavior)
            for field in a.keys() | b.keys():
                if field in {'score_version', 'answer_change_reason', 'source_origin',
                             'historical_source_sha256'} or same(a.get(field), b.get(field)):
                    continue
                av, bv = a.get(field), b.get(field)
                if isinstance(av, (float, int)) and isinstance(bv, (float, int)) and math.isclose(av, bv, abs_tol=1e-12):
                    continue
                row = {k: a[k] for k in keys}
                row.update(model=a['model'], budget=a.get('budget', a.get('regime')),
                           strategy=a.get('strategy', 'single'), metric=field, old=av, new=bv,
                           delta=(bv-av if isinstance(av, (float, int)) and isinstance(bv, (float, int)) else ''),
                           source_sha256=b['source_sha256'], old_source_sha256=a['source_sha256'],
                           new_source_sha256=b['source_sha256'], source_replaced=int(source_replaced),
                           reason=b.get('answer_change_reason', 'accepted_final_answer_changed'))
                rows.append(row)
        rows.sort(key=lambda r: tuple(str(r[k]) for k in keys) + (r['metric'],))
        write_csv(output / 'changes' / (dataset + '.csv'), rows)
        changed_counts[dataset] = len({tuple(r[k] for k in keys) for r in rows})
    summaries = []
    for version, data in versions.items():
        patterns = data['patterns']
        candidates = [r for r in patterns if r['model'] == 'qwen3.8-2.4t-a95b-fp8'
                      and len(json.loads(r['gold_evidence_ids'])) == 2
                      and len(json.loads(r['free_first_partial_and_tight_final_ids'])) == 1]
        summary = dict(score_version=version, matched_hypothesis_presentations=len(patterns),
                       free_exact_confirmation=sum(r['free_exact_feedback_seen'] for r in patterns),
                       unique_model_doc_hypotheses=len({(r['model'], r['doc_index'], r['hypothesis']) for r in patterns}),
                       model_document_combinations=len({(r['model'], r['doc_index']) for r in patterns}),
                       models=len({r['model'] for r in patterns}), documents=len({r['doc_index'] for r in patterns}),
                       qwen_case_candidates=len(candidates),
                       qwen_frozen_case_still_qualifies=int(any(r['doc_index'] == 10 and r['order'] == 1 and r['hypothesis'] == 'nda-13' for r in candidates)))
        arms = defaultdict(dict)
        for row in data['pools']:
            arms[(row['model'], row['regime'], str(row['question_index']))][row['strategy']] = row
        pool_candidates = []
        for key, group in arms.items():
            if key[1] != 'cost_moderate':
                continue
            n, c, p = (group[s] for s in ('naive', 'cached', 'poolact'))
            gain = p['visible_hypotheses'] - max(n['visible_hypotheses'], c['visible_hypotheses'])
            if p['feedback_visible'] <= n['feedback_visible'] and gain > 0 and p['final_matches_peer_only_verified_nonempty'] > 0:
                pool_candidates.append((gain, key))
        pool_candidates.sort()
        summary['pool_case_candidates'] = len(pool_candidates)
        frozen_key = ('kimi-k3', 'cost_moderate', '3')
        summary['kimi_frozen_case_still_qualifies'] = int(any(k == frozen_key for _, k in pool_candidates))
        summary['pool_rule_upper_median_key'] = json.dumps(pool_candidates[len(pool_candidates)//2][1])
        group_map = {(r['model'], r['regime'], r['strategy']): r for r in data['groups']}
        summary['poolact_coverage_above_cached_groups'] = sum(
            r['mean_visible_hypotheses'] > group_map[m,b,'cached']['mean_visible_hypotheses']
            for (m,b,s), r in group_map.items() if s == 'poolact')
        summary['poolact_coverage_above_naive_groups'] = sum(
            r['mean_visible_hypotheses'] > group_map[m,b,'naive']['mean_visible_hypotheses']
            for (m,b,s), r in group_map.items() if s == 'poolact')
        for budget in ('cost_moderate', 'cost_tight'):
            selected = [r for r in data['agents'] if r['regime'] == budget and r['strategy'] == 'poolact']
            summary[budget + '_peer_only_nonempty_match_agents'] = sum(r['final_matches_peer_only_verified_nonempty'] > 0 for r in selected)
            summary[budget + '_peer_only_nonempty_match_hypotheses'] = sum(r['final_matches_peer_only_verified_nonempty'] for r in selected)
            summary[budget + '_parsed_agents'] = sum(r['final_answer_parsed'] for r in selected)
            summary[budget + '_denominator_agents'] = len(selected)
        summaries.append(summary)
    write_csv(output / 'changes' / 'case_population.csv', summaries)
    cases = []
    for version, data in versions.items():
        for row in data['traces']:
            if row['model'] == 'qwen3.8-2.4t-a95b-fp8' and row['doc_index'] == 10 and row['order'] == 1 and row['budget'] in ('cost_free', 'cost_tight'):
                hypothesis = next(h for h in data['hypotheses'] if h['slot_id'] == row['slot_id'] and h['hypothesis'] == 'nda-13')
                cases.append(dict(case='audit_correct_label_incomplete_evidence', score_version=version,
                                  model=row['model'], budget=row['budget'], strategy='single',
                                  slot_id=row['slot_id'], source_sha256=row['source_sha256'],
                                  evidence_acc=row['evidence_acc'], label_acc=row['label_acc'],
                                  target_label_correct=hypothesis['label_correct'], target_evidence_exact=hypothesis['evidence_exact'],
                                  target_evidence_ids=hypothesis['submitted_evidence_ids'],
                                  feedback_visible=row['visible_tool_calls'], visible_hypotheses=row['visible_distinct_hypotheses'],
                                  frozen_case_still_qualifies=next(s['qwen_frozen_case_still_qualifies'] for s in summaries if s['score_version']==version)))
        for row in data['pools']:
            if row['model'] == 'kimi-k3' and row['regime'] == 'cost_moderate' and row['question_index'] == 3:
                cases.append(dict(case='poolact_coverage_and_verified_observation_reuse', score_version=version,
                                  model=row['model'], budget=row['regime'], strategy=row['strategy'],
                                  slot_id=row['slot_id'], source_sha256=row['source_sha256'],
                                  evidence_acc=row['evidence_acc'], label_acc=row['label_acc'],
                                  feedback_visible=row['feedback_visible'], visible_hypotheses=row['visible_hypotheses'],
                                  final_matches_peer_only_verified_nonempty=row['final_matches_peer_only_verified_nonempty'],
                                  frozen_case_still_qualifies=next(s['kimi_frozen_case_still_qualifies'] for s in summaries if s['score_version']==version)))
    write_csv(output / 'changes' / 'retained_cases.csv', cases)
    for dataset, keys in [('budgets', ('budget',)), ('model_budgets', ('model', 'budget')),
                          ('groups', ('model', 'regime', 'strategy')),
                          ('diagnostic_counts', ('model', 'budget', 'gold_subset'))]:
        before = {tuple(r[k] for k in keys): r for r in old[dataset]}
        after = {tuple(r[k] for k in keys): r for r in new[dataset]}
        assert before.keys() == after.keys()
        delta_rows = []
        for key, a in before.items():
            b = after[key]
            for metric in a:
                if metric in keys or a[metric] == b[metric]:
                    continue
                av, bv = a[metric], b[metric]
                if isinstance(av, (int, float)) and isinstance(bv, (int, float)) and math.isclose(av, bv, abs_tol=1e-12):
                    continue
                row = dict(zip(keys, key))
                row.update(metric=metric, old=av, new=bv,
                           delta=bv-av if isinstance(av, (int, float)) and isinstance(bv, (int, float)) else '')
                delta_rows.append(row)
        delta_rows.sort(key=lambda r: tuple(str(r[k]) for k in keys) + (r['metric'],))
        write_csv(output / 'changes' / (dataset + '.csv'), delta_rows)
    keys = ('model', 'doc_index', 'order', 'hypothesis')
    pattern_before = {tuple(r[k] for k in keys): r for r in old['patterns']}
    pattern_after = {tuple(r[k] for k in keys): r for r in new['patterns']}
    pair_sources = {
        version: {(r['model'], r['budget'], r['doc_index'], r['order']): r['source_sha256']
                  for r in data['traces']}
        for version, data in versions.items()}
    membership = []
    for key in sorted(pattern_before.keys() | pattern_after.keys()):
        row = dict(pattern_after.get(key, pattern_before.get(key)))
        model, doc_index, order, _ = key
        paired_hashes = {
            f'{version}_{label}_source_sha256': pair_sources[version][model, budget, doc_index, order]
            for version in ('old', 'new')
            for label, budget in (('free', 'cost_free'), ('tight', 'cost_tight'))}
        source_replaced = any(paired_hashes[f'old_{label}_source_sha256'] !=
                              paired_hashes[f'new_{label}_source_sha256']
                              for label in ('free', 'tight'))
        change_cause = 'runtime_control_adoption' if source_replaced else 'terminal_repair'
        row.update(paired_hashes, source_replaced=int(source_replaced))
        row.update(old_included=int(key in pattern_before), new_included=int(key in pattern_after),
                   change=('unchanged' if key in pattern_before and key in pattern_after else
                           'newly_recognized_after_' + change_cause if key in pattern_after else
                           'no_longer_matches_after_' + change_cause))
        membership.append(row)
    write_csv(output / 'changes' / 'paired_pattern_membership.csv', membership)
    return changed_counts, summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--sources', type=Path)
    parser.add_argument('--overlays', type=Path)
    parser.add_argument('--score-checks', type=Path,
                        help='Defaults to the scoring CHECKS.json beside the private overlay directory')
    parser.add_argument('--gold', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay-public', type=Path)
    parser.add_argument('--baseline-report', type=Path,
                        help='Original completed Audit report; read its old/ leaf tables as immutable old-score baseline')
    parser.add_argument('--require-adopted-controls', action='store_true',
                        help='Require exactly 2 N1 and 18 N4 Audit source replacements before producing official output')
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    if args.replay_public:
        versions = {}
        for version in ('old', 'new'):
            base = args.replay_public / 'old' if version == 'old' else args.replay_public
            versions[version] = read_leaf_dataset(base)
        metadata = {'mode': 'public_row_replay', 'model_calls': 0}
    else:
        for name in ('repo', 'sources', 'overlays', 'gold'):
            if getattr(args, name) is None:
                parser.error('--' + name + ' is required without --replay-public')
        versions, metadata = extract_all(args)
    for version, data in versions.items():
        base = args.output / 'old' if version == 'old' else args.output
        aggregate_n1(data, base / 'n1')
        aggregate_coordination(data, base / 'coordination')
    changed, population = changes(versions, args.output)
    metadata.update(status=('PENDING_PUBLIC_REPLAY' if args.require_adopted_controls and not args.replay_public else 'PASS'),
                    n1_traces=702, n1_hypothesis_presentations=11934,
                    n4_pools=468, n4_agents=1872, changed_samples=changed,
                    case_population=population,
                    verification_eff_semantics='Among hypotheses with a jointly correct final label and evidence set, the fraction whose exact evidence set was submitted to human_feedback, including withheld results; null when the denominator is zero. visible_verification_eff uses the same denominator and requires a visible correct verification.',
                    no_raw_trajectory_mutation=True, analysis_makes_no_model_calls=True,
                    n1_and_n4_individual_la_ea_checked_against_official_scores=not bool(args.replay_public),
                    public_replay_rebuilds_exported_leaf_aggregates_only=bool(args.replay_public),
                    behavior_unchanged_for_retained_source_hashes=True,
                    replaced_sources_use_actual_new_runtime_actions=True,
                    score_layer=('public_replay_of_exported_rows' if args.replay_public else
                                 'new_official_with_required_runtime_controls' if args.require_adopted_controls else
                                 'analysis_only_without_adoption_gate'),
                    required_runtime_adoption_checked=bool(args.require_adopted_controls and not args.replay_public),
                    old_layer='historical_frozen_scoring',
                    diagnostic_layer='audit_existing_trace',
                    analysis_scripts_sha256={name: sha((HERE / name).read_bytes()) for name in
                        ('recompute_audit.py', '_historical_n1.py', '_historical_coordination.py')})
    (args.output / 'CHECKS.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in metadata.items() if k != 'source_files'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
