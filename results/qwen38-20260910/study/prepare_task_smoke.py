#!/usr/bin/env python3
"""Select bounded plumbing checks, never formal results or score-based samples."""
import argparse
import copy
import json
from pathlib import Path


def options(stage):
    argv = stage['args']
    if len(argv) % 2:
        raise ValueError('Expected explicit flag/value pairs')
    result = dict(zip(argv[::2], argv[1::2]))
    if len(result) * 2 != len(argv):
        raise ValueError('Duplicate options')
    return result


def select(matrix):
    chosen = {}
    for stage in matrix['stages']:
        value = options(stage)
        runner = stage['runner']
        scenario = value.get('--scenarios', value.get('--scenario'))
        kind = None
        if runner == 'expgym' and scenario == 'restricted_search' and value.get('--search-data-source') == 'phantom_seed2':
            kind = 'exp-search'
            value.update({'--search-indices': '0', '--search-reps': '1'})
        elif runner == 'expgym' and scenario == 'evidence_audit':
            kind = 'exp-audit'
            value.update({'--audit-indices': '0', '--audit-reps': '1'})
        elif runner == 'expgym' and scenario == 'tuning' and 'hpobench:paramnet:adult:steps' in value.get('--tuning-tasks', '').split(','):
            kind = 'exp-paramnet'
            value.update({'--tuning-tasks': 'hpobench:paramnet:adult:steps', '--tuning-reps': '1'})
        elif runner == 'poolact' and scenario == 'tuning' and value.get('--tuning-task') == 'hpobench:nasbench101:A':
            kind = 'pool-nas101'
            value.update({'--strategies': 'naive,cached,poolact', '--repeats': '1'})
        if kind is None or kind in chosen:
            continue
        value.update({'--max-steps': '3', '--max-evals': '2', '--seed': '2200',
                      '--cost-regimes' if runner == 'expgym' else '--cost-regime': 'cost_tight'})
        selected = copy.deepcopy(stage)
        selected['label'] = 'smoke-' + kind
        selected['args'] = [part for pair in sorted(value.items()) for part in pair]
        chosen[kind] = selected
    expected = ['exp-search', 'exp-audit', 'exp-paramnet', 'pool-nas101']
    if set(chosen) != set(expected):
        raise ValueError('Smoke selectors absent: ' + ','.join(sorted(set(expected) - set(chosen))))
    return {'stages': [chosen[kind] for kind in expected]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = select(json.loads(args.matrix.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'stages': len(result['stages']), 'planned_jobs': 6,
                      'planned_agents': 15, 'max_steps': 3, 'max_evals': 2,
                      'formal_results': False, 'output': str(args.output)}))


if __name__ == '__main__':
    main()
