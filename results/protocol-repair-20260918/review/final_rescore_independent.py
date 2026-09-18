#!/usr/bin/env python3
"""Read-only final version/count and Audit field/vote audit; never calls a model."""
from collections import Counter, defaultdict
import argparse
import csv
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def different(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) != set(b) or any(different(a[k], b[k]) for k in a)
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return abs(a - b) > 1e-12
    return a != b


def historical_label(value):
    key = re.sub('[^a-z]', '', str(value or '').lower())
    return {'entailment': 'Entailment', 'entailed': 'Entailment',
            'contradiction': 'Contradiction', 'contradicted': 'Contradiction',
            'notmentioned': 'NotMentioned', 'neutral': 'NotMentioned'}.get(
                key, str(value or '').strip())


def historical_evidence(value):
    if not isinstance(value, list):
        return ()
    result = set()
    for entry in value:
        try:
            result.add(int(entry))
        except (ValueError, TypeError, OverflowError):
            result.add(str(entry))
    return tuple(sorted(result, key=lambda x: (str(type(x)), str(x))))


def literal_label(value):
    return value if isinstance(value, str) else ''


def legacy_individual_evidence(value):
    try:
        result = set(int(entry) for entry in value)
    except Exception:
        result = set()
    return tuple(sorted(result, key=str))


def vote(parsed, label_key, evidence_key):
    result = {}
    for hypothesis in sorted({key for answer in parsed for key in answer}):
        entries = [answer[hypothesis] for answer in parsed
                   if isinstance(answer.get(hypothesis), dict)]
        labels = [label_key(entry.get('label')) for entry in entries]
        if not labels:
            continue
        label = Counter(labels).most_common(1)[0][0]
        evidence = [evidence_key(entry.get('evidence_ids'))
                    for entry, choice in zip(entries, labels) if choice == label]
        result[hypothesis] = {'label': label,
                             'evidence_ids': list(Counter(evidence).most_common(1)[0][0])}
    return result


def main(repo, base, output):
    sys.path.insert(0, str(repo))
    protocol = importlib.import_module('expgym.tool_protocol')
    core = '0e6c51b6d86f42437038518c2fc8adc510901c0b'
    checks = {name: json.loads((base / name / 'CHECKS.json').read_text())
              for name in ('main', 'search_audit', 'hpo', 'sweep')}
    input_paths = [base / name / 'CHECKS.json' for name in checks]
    input_paths += [base / 'main' / name for name in
                    ('slot_scalars.csv', 'slot_scalars.legacy.csv', 'sample_diff.csv')]
    input_paths += [base / 'search_audit' / name for name in
                    ('private/answer_overlays.jsonl', 'agent_rows.csv', 'scoring_inputs.jsonl.gz')]
    input_paths += [base / 'sweep/agent_rows.csv', base / 'hpo/slot_metrics.csv',
                    repo / 'configs/audit_hypothesis_orders.json']
    inputs = {str(path): sha(path) for path in input_paths}
    assertions = []

    def check(name, condition):
        assertions.append({'name': name, 'passed': bool(condition)})

    hashes = {}
    for name, expected in checks['search_audit']['code_sha256'].items():
        actual = sha(repo / name)
        committed = (hashlib.sha256(subprocess.check_output(
            ['git', '-C', str(repo), 'show', core + ':' + name])).hexdigest()
            if name.startswith('expgym/') else None)
        hashes[name] = {'actual': actual, 'rescore': expected, 'commit': committed}
        check('current/rescore:' + name, actual == expected)
        if committed is not None:
            check('current/core:' + name, actual == committed)
    for name in ('expgym/extras/aggregation_diagnostics.py', 'expgym/react_loop.py',
                 'expgym/trace_v2.py'):
        current = sha(repo / name)
        committed = hashlib.sha256(subprocess.check_output(
            ['git', '-C', str(repo), 'show', core + ':' + name])).hexdigest()
        hashes[name] = {'actual': current, 'commit': committed}
        check('current/core:' + name, current == committed)
    check('hpo parser identity', checks['hpo']['parser_sha256'] == hashes[
        'expgym/tool_protocol.py']['actual'])
    for item in checks['sweep']['code_files']:
        check('sweep code:' + item['path'], sha(repo / item['path']) == item['sha256'])
    for item in checks['sweep']['output_files']:
        check('sweep output:' + item['path'],
              sha(base / 'sweep' / item['path']) == item['sha256'])

    current_rows = rows(base / 'main/slot_scalars.csv')
    old_rows = rows(base / 'main/slot_scalars.legacy.csv')
    diffs = rows(base / 'main/sample_diff.csv')
    current = {row['slot_id']: row for row in current_rows}
    historical = {row['slot_id']: row for row in old_rows}
    indexed_diffs = {row['slot_id']: row for row in diffs}
    check('4698 unique complete joined slots',
          len(current_rows) == len(current) == len(historical) == len(indexed_diffs) == 4698
          and current.keys() == historical.keys() == indexed_diffs.keys())
    changed = Counter()
    endpoints = Counter()
    primary = Counter()
    endpoint_keys = {('expgym', 'evidence_audit'): 'evidence_acc',
                     ('poolact', 'evidence_audit'): 'evidence_acc_mv',
                     ('expgym', 'restricted_search'): 'f1',
                     ('poolact', 'restricted_search'): 'f1_mv',
                     ('expgym', 'tuning'): 'gap0',
                     ('poolact', 'tuning'): 'gap0_mi'}
    disagreements = []
    for slot, row in current.items():
        old = json.loads(historical[slot]['metrics_json'])
        new = json.loads(row['metrics_json'])
        diff = indexed_diffs[slot]
        group = row['system'] + '/' + row['scenario']
        state = different(old, new)
        key = endpoint_keys[(row['system'], row['scenario'])]
        primary_state = different(old.get(key), new.get(key))
        label_endpoint = ('label_acc_mv' if row['system'] == 'poolact' else 'label_acc')
        endpoint_state = (primary_state or (row['scenario'] == 'evidence_audit'
                          and different(old.get(label_endpoint), new.get(label_endpoint))))
        changed[group] += int(state)
        endpoints[group] += int(endpoint_state)
        primary[group] += int(primary_state)
        if (different(old, json.loads(diff['old_metrics_json']))
                or different(new, json.loads(diff['new_metrics_json']))
                or state != (diff['score_changed'] == 'True')
                or endpoint_state != (diff['endpoint_score_changed'] == 'True')):
            disagreements.append(slot)
    check('main CSV metric/diff flags agree', not disagreements)
    check('57 metric changed slots', sum(changed.values()) == 57)
    check('41 task endpoint changed slots (Audit LA or EA)', sum(endpoints.values()) == 41)
    check('39 paper primary endpoint changed slots (Audit EA)', sum(primary.values()) == 39)
    check('CHECKS metric group counts', {k: v for k, v in changed.items() if v}
          == checks['main']['score_changed_by_system_scenario'])
    complete_before = sum(r['score_complete'] == 'True' for r in old_rows)
    complete_after = sum(r['score_complete'] == 'True' for r in current_rows)
    check('4687 complete scores in both layers', complete_before == complete_after == 4687)
    sweep = rows(base / 'sweep/agent_rows.csv')
    sweep_changed = sum(different(float(r['old_score']), float(r['new_score'])) for r in sweep)
    check('1170 sweep rows with zero score changes', len(sweep) == 1170 and sweep_changed == 0)
    hpo = rows(base / 'hpo/slot_metrics.csv')
    hpo_changed = sum(different(json.loads(r['old_metrics_json']), json.loads(r['new_metrics_json']))
                      for r in hpo)
    check('810 HPO slots with zero score changes', len(hpo) == 810 and hpo_changed == 0)

    orders = json.loads((repo / 'configs/audit_hypothesis_orders.json').read_text())['orders']
    public_ids = set(orders[0])
    check('17 public Audit hypothesis IDs', len(public_ids) == 17)
    members = []
    pools = {}
    for line in (base / 'search_audit/private/answer_overlays.jsonl').open():
        obj = json.loads(line)
        if obj['scenario'] != 'evidence_audit':
            continue
        if obj['agent_id'] == 'aggregate':
            pools[obj['slot_id']] = obj
        else:
            members.append(obj)
    check('2574 Audit members and 468 pools', len(members) == 2574 and len(pools) == 468)
    field_counts = Counter()
    field_differences = []
    groups = defaultdict(list)
    for member in members:
        if member['system'] == 'poolact':
            groups[member['slot_id']].append(member)
        for column in ('old_answer', 'new_scoring_input'):
            try:
                parsed = protocol.parse_audit_answer(member[column])
            except (ValueError, TypeError, RecursionError, OverflowError):
                continue
            for key, entry in parsed.items():
                if not isinstance(entry, dict):
                    continue
                field_counts[column + '/entries'] += 1
                before_label = historical_label(entry.get('label'))
                after_label = literal_label(entry.get('label'))
                before_evidence = historical_evidence(entry.get('evidence_ids'))
                after_evidence = legacy_individual_evidence(entry.get('evidence_ids'))
                check_current = (after_label == protocol.audit_label_key(entry.get('label'))
                                 and after_evidence == protocol.audit_evidence_key(entry.get('evidence_ids')))
                if not check_current:
                    raise AssertionError('independent field interpretation differs from production')
                if before_label != after_label or before_evidence != after_evidence:
                    field_counts[column + '/field_difference_entries'] += 1
                    field_counts[column + '/public_hypothesis_difference_entries'] += int(key in public_ids)
                    field_differences.append({k: member[k] for k in
                                              ('slot_id', 'agent_id', 'system', 'model', 'regime', 'strategy')}
                        | {'column': column, 'hypothesis_id': key, 'public_hypothesis': key in public_ids,
                           'label_before': before_label, 'label_after': after_label,
                           'evidence_before': list(before_evidence), 'evidence_after': list(after_evidence)})
    check('no valid hypothesis field interpretation changes', all(
        not item['public_hypothesis'] for item in field_differences))
    field_only_pool_changes = []
    vote_mismatches = []
    old_vote_mismatches = []
    for slot, agents in groups.items():
        agents.sort(key=lambda obj: int(obj['agent_id']))
        old_parsed = []
        new_parsed = []
        for agent in agents:
            try:
                value = json.loads(agent['old_answer'])
                old_parsed.append(value if isinstance(value, dict) else {})
            except (ValueError, TypeError, RecursionError, OverflowError):
                old_parsed.append({})
            try:
                new_parsed.append(protocol.parse_audit_answer(agent['new_scoring_input']))
            except (ValueError, TypeError, RecursionError, OverflowError):
                new_parsed.append({})
        previous = vote(old_parsed, historical_label, historical_evidence)
        current_vote = vote(new_parsed, literal_label, legacy_individual_evidence)
        old_fields = vote(new_parsed, historical_label, historical_evidence)
        if previous != json.loads(pools[slot]['old_answer']):
            old_vote_mismatches.append(slot)
        if current_vote != json.loads(pools[slot]['new_scoring_input']):
            vote_mismatches.append(slot)
        if current_vote != old_fields:
            affected_ids = [key for key in set(current_vote) | set(old_fields)
                            if current_vote.get(key) != old_fields.get(key)]
            field_only_pool_changes.append({'slot_id': slot, 'hypotheses': affected_ids,
                                            'public_hypotheses': sorted(set(affected_ids) & public_ids)})
    check('all 468 historical votes independently reproduced',
          len(groups) == 468 and not old_vote_mismatches)
    check('all 468 repaired votes independently reproduced', not vote_mismatches)
    check('field-only pool changes never affect a public hypothesis',
          all(not item['public_hypotheses'] for item in field_only_pool_changes))
    overlay_members = {(row['slot_id'], str(row['agent_id'])): row for row in members}
    scored_rows = {(row['slot_id'], row['agent_id']): row
                   for row in rows(base / 'search_audit/agent_rows.csv')
                   if row['scenario'] == 'evidence_audit'}
    parser_mismatches, score_mismatches = [], []
    changed_member_reasons = Counter()
    total_audit_sources, total_audit_members = 0, 0

    def old_payload(text):
        try:
            value = json.loads(text)
        except (ValueError, TypeError, RecursionError, OverflowError):
            cleaned = (text or '').strip().rstrip(';').strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
            try:
                value = json.loads(cleaned)
            except (ValueError, TypeError, RecursionError, OverflowError):
                return {}
        return value if isinstance(value, dict) else {}

    def score(payload, annotations):
        label_correct, evidence_correct = 0, 0
        for hypothesis, gold in annotations.items():
            entry = payload.get(hypothesis)
            if not isinstance(entry, dict):
                continue
            label_correct += entry.get('label') == gold['choice']
            evidence_correct += set(legacy_individual_evidence(entry.get('evidence_ids', []))) == set(
                int(value) for value in gold.get('spans', []))
        return {'label_acc': label_correct / len(annotations),
                'evidence_acc': evidence_correct / len(annotations)}

    with gzip.open(base / 'search_audit/scoring_inputs.jsonl.gz', 'rt') as handle:
        for line in handle:
            pack = json.loads(line)
            if pack['slot']['scenario'] != 'evidence_audit':
                continue
            total_audit_sources += 1
            slot = pack['slot']['slot_id']
            for agent in pack['agents']:
                total_audit_members += 1
                identity = (slot, str(agent['agent_id']))
                overlay, row = overlay_members[identity], scored_rows[identity]
                text = agent['raw_final_text']
                extracted = None
                if agent['final_eligible']:
                    if agent['native_tool_calls_present'] or agent['finish_reason'] == 'length':
                        raise AssertionError('eligible final contradicts provider envelope')
                    extracted = protocol.parse_final_answer(text, allow_unlabelled=agent['allow_unlabelled'])
                if extracted != overlay['new_answer']:
                    parser_mismatches.append({'slot_id': slot, 'agent_id': agent['agent_id']})
                old_score = score(old_payload(agent['old_scoring_input']), pack['gold']['annotations'])
                try:
                    new_payload = protocol.parse_audit_answer(overlay['new_scoring_input'])
                except (ValueError, TypeError, RecursionError, OverflowError):
                    new_payload = {}
                new_score = score(new_payload, pack['gold']['annotations'])
                if (any(different(value, json.loads(row['old_metrics_json'])[key])
                        for key, value in old_score.items())
                        or any(different(value, json.loads(row['new_metrics_json'])[key])
                               for key, value in new_score.items())):
                    score_mismatches.append({'slot_id': slot, 'agent_id': agent['agent_id']})
                if different(old_score, new_score):
                    changed_member_reasons[row['change_reason']] += 1
    check('all 2574 Audit final extractions reproduced',
          total_audit_sources == 1170 and total_audit_members == 2574 and not parser_mismatches)
    check('all 2574 old/new Audit LA/EA independently recomputed', not score_mismatches)
    check('stable inputs during audit', inputs == {str(path): sha(path) for path in input_paths})
    report = {'status': 'PASS' if all(item['passed'] for item in assertions) else 'FAIL',
              'core_repair_commit': core, 'source_sha256': hashes,
              'input_sha256': inputs, 'checks': assertions,
              'main': {'slots': len(current_rows), 'old_score_complete': complete_before,
                       'new_score_complete': complete_after, 'changed_metric_slots': sum(changed.values()),
                       'changed_task_endpoint_slots': sum(endpoints.values()),
                       'changed_paper_primary_endpoint_slots': sum(primary.values()),
                       'metric_changes_by_group': dict(changed), 'task_endpoint_changes_by_group': dict(endpoints),
                       'paper_primary_changes_by_group': dict(primary),
                       'csv_disagreements': disagreements},
              'hpo': {'slots': len(hpo), 'score_changes': hpo_changed},
              'sweep': {'slots': len(sweep), 'score_changes': sweep_changed},
              'audit': {'members': len(members), 'pools': len(pools),
                        'field_counts': dict(field_counts), 'field_differences': field_differences,
                        'field_only_pool_changes': field_only_pool_changes,
                        'audit_sources_replayed': total_audit_sources,
                        'audit_terminal_extraction_mismatches': parser_mismatches,
                        'audit_LA_EA_recompute_mismatches': score_mismatches,
                        'changed_member_reasons': dict(changed_member_reasons),
                        'independent_historical_vote_mismatches': old_vote_mismatches,
                        'independent_repaired_vote_mismatches': vote_mismatches},
              'model_calls': 0, 'production_modified': False, 'rescore_outputs_modified': False,
              'gold_used_to_select_parse_or_vote': False,
              'packed_reference_annotations_used_only_after_parsing_to_verify_LA_EA': True,
              'scope': 'Full saved CSV/count/version audit and independent Audit vote replay; not another model run or reexecution of runtime graph decisions.'}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('status', 'main', 'hpo', 'sweep')}, ensure_ascii=False))
    print(json.dumps(report['audit'], ensure_ascii=False))
    return report['status']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--rescore', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = main(args.repo.resolve(), args.rescore.resolve(), args.output.resolve())
    raise SystemExit(0 if result == 'PASS' else 1)
