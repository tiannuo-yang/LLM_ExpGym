import argparse
import ast
import collections
import hashlib
import json
import pathlib
import random
import subprocess
import sys
import types

parser = argparse.ArgumentParser(description='Independent, no-model graph identity checks')
parser.add_argument('--repo', required=True, type=pathlib.Path)
parser.add_argument('--base-commit', default='297c3d00a006f33fc5a8ca799ce91d327d92839e')
parser.add_argument('--output', type=pathlib.Path, default=pathlib.Path(__file__).with_name('graph_identity_independent_checks.json'))
args = parser.parse_args()
REPO = args.repo.resolve()
REFERENCE_SHA256 = 'f7da6a20cdee00f47fc72632a4ba1bd86059c32c54f78a911d210bcd07ea41d7'
REL = 'expgym/extras/parallel_cache.py'
sys.path.insert(0, str(REPO))
from expgym.extras import parallel_cache as fixed

old_source = subprocess.check_output(['git', 'show', args.base_commit + ':' + REL], cwd=REPO).decode()
new_source = (REPO / REL).read_text()
assert hashlib.sha256(new_source.encode()).hexdigest() == REFERENCE_SHA256
old = types.ModuleType('_independent_old_parallel_cache')
sys.modules[old.__name__] = old
exec(compile(old_source, 'baseline:' + REL, 'exec'), old.__dict__)

def function_map(source):
    out = {}
    for n in ast.parse(source).body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[n.name] = ast.dump(n, include_attributes=False)
        elif isinstance(n, ast.ClassDef):
            for method in n.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[n.name + '.' + method.name] = ast.dump(method, include_attributes=False)
    return out

before, after = function_map(old_source), function_map(new_source)
changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
allowed = ['SharedExplorationGraph.' + name for name in (
    '__init__', '_eval_key', '_eval_display_keys', 'record_evaluate_config',
    'format_for_injection', '_format_unified', '_format_tuning_default')]
assert changed == sorted(allowed), changed

rng = random.Random(20260918)
configs = [json.dumps({'common': 'a' * 100, 'variant': i}, sort_keys=True, separators=(',', ':')) for i in range(128)]
configs += [json.dumps({'x': i}, separators=(',', ':')) for i in range(32)]
configs += [json.dumps({'x': 'b' * (length - 8)}, separators=(',', ':')) for length in (79, 80, 81)]
events = []
for index in range(1000):
    key = configs[rng.randrange(len(configs))]
    events.append((index / 4, rng.randrange(4), key, rng.randrange(1, 1000) / 1000))
graph = fixed.SharedExplorationGraph(n_agents=4, diversity_mode=True)
legacy = old.SharedExplorationGraph(n_agents=4, diversity_mode=True)
for t, agent, key, perf in events:
    for obj in (graph, legacy):
        obj.record_evaluate_config(agent, key, key, perf, 1, completion_time=t)
assert graph._observations == legacy._observations
for key in graph._eval_nodes:
    assert vars(graph._eval_nodes[key]) == vars(legacy._eval_nodes[key])

for cutoff in (0, 1, 10, 30, 100, 200, 249.75):
    for strict in (None, cutoff):
        selected = [event for event in events if event[0] <= cutoff and (strict is None or event[0] < strict)]
        counts = collections.Counter()
        agents = collections.defaultdict(set)
        last = {}
        seen = set()
        for _, agent, key, _ in selected:
            seen.add(key)
            if agent in last:
                edge = (last[agent], key)
                counts[edge] += 1
                agents[edge].add(agent)
            last[agent] = key
        aliases = {key: ('E:' + key if len(key) <= 80 else 'E:h:' + hashlib.sha256(key.encode()).hexdigest()[:12]) for key in seen}
        rendered = graph.format_for_injection(visible_before=cutoff, completion_before=strict)
        if not selected:
            assert rendered == ''
            continue
        paths = rendered.split('== Exploration Paths ==', 1)[1].split('== Coverage Gap ==', 1)[0]
        expected = set()
        for edge, count in counts.items():
            suffix = ('%sx, agents ' % count if count > 1 else 'agents ') + ','.join(map(str, sorted(agents[edge])))
            expected.add('  %s --> %s [%s]' % (aliases[edge[0]], aliases[edge[1]], suffix))
        actual = {line for line in paths.splitlines() if '-->' in line}
        assert actual == expected, (cutoff, strict, actual ^ expected)
        if cutoff >= 1:
            future_key = json.dumps({'common': 'a' * 100, 'future': cutoff})
            graph.record_evaluate_config(9, future_key, 'SHOULD_NOT_APPEAR', .999999, 0, completion_time=10000)
            assert rendered == graph.format_for_injection(visible_before=cutoff, completion_before=strict)

# Exercise wrappers against the baseline: out-of-order/future completion,
# exact budget boundary, canonical dict reordering, repeated cache lookup.
def exercise(module):
    graph = module.SharedExplorationGraph(n_agents=2, diversity_mode=True)
    cache = module.SharedObservationCache()
    calls = []
    outputs = []
    clocks = [module.AgentClock(), module.AgentClock()]
    def evaluate(payload):
        key = json.dumps(json.loads(payload), sort_keys=True, separators=(',', ':'))
        calls.append(key)
        return (.9 if 'variant' in payload else .4, 3.)
    wrappers = [module.wrap_tools_with_poolact({'evaluate_config': evaluate}, cache, graph, i, clock=clocks[i], time_budget=10) for i in range(2)]
    for agent, payload, advance in [(0, configs[0], 3), (1, configs[0], 3), (0, configs[1], 3), (1, configs[0], 0), (0, configs[2], 3), (0, configs[3], 3)]:
        outputs.append(wrappers[agent]['evaluate_config'](payload))
        clocks[agent].advance(advance)
    return {'outputs': outputs, 'calls': calls, 'cache': cache.stats(),
            'clocks': [clock.now for clock in clocks], 'observations': graph._observations,
            'claims': {str(k): [vars(c) for c in v] for k, v in graph._claims.items()}}
old_run, new_run = exercise(old), exercise(fixed)
assert old_run == new_run
result = {
    'status': 'PASS',
    'baseline_commit': subprocess.check_output(['git', 'rev-parse', args.base_commit], cwd=REPO).decode().strip(),
    'reference_commit': '5bf5e5af817c2c6add48c7bae4eec4fe6e8110e9',
    'source_sha256': hashlib.sha256(new_source.encode()).hexdigest(),
    'reference_byte_identical': True,
    'changed_functions': changed,
    'other_functions_ast_unchanged': len(before) - 6,
    'property_events': len(events),
    'property_configs': len(configs),
    'snapshot_cases': 14,
    'future_append_snapshot_invariance_cases': 12,
    'cache_and_budget_runtime_equivalent': True,
    'model_calls': 0,
}
output = args.output
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
