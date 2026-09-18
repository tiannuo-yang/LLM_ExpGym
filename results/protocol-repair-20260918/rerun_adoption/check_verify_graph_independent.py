#!/usr/bin/env python3
"""Independent saved-fixture and runtime-synthetic verification; no model calls."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME = ROOT / 'runtime'
sys.path.insert(0, str(RUNTIME))
from expgym.extras.parallel_cache import SharedExplorationGraph, _parse_evaluate_config

TARGET = HERE / 'verify_graph.py'
spec = importlib.util.spec_from_file_location('independently_loaded_verify_graph', TARGET)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
verify_graph = module.verify_graph
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
tests = []

def exercise(name, result, expected_ok, expected_applicable=True, required_errors=(), fixture=None):
    before = copy.deepcopy(result)
    actual = verify_graph(result)
    same = result == before
    errors = actual.get('error_counts', {})
    passed = (actual['ok'] == expected_ok and actual['applicable'] == expected_applicable
              and same and all(errors.get(code, 0) > 0 for code in required_errors))
    tests.append({'name': name, 'passed': passed, 'expected_ok': expected_ok,
                  'expected_applicable': expected_applicable, 'input_not_mutated': same,
                  'required_errors': list(required_errors), 'fixture': fixture, 'actual': actual})
    return actual

inventory_path = HERE / 'graph_fixture_inventory.json'
inventory = json.loads(inventory_path.read_text())
for row in inventory['fixtures']:
    p = Path(row['path'])
    if sha(p) != row['sha256']:
        raise AssertionError('Fixture SHA mismatch: ' + str(p))
    expected_ok = row['label'] != 'historical_v3_collision'
    applicable = row['strategy'] == 'poolact'
    exercise(row['label'], json.loads(p.read_text()), expected_ok, applicable,
             ('rendered_identity_collision', 'path_endpoint_ambiguous') if not expected_ok else (),
             {'path': str(p), 'sha256': row['sha256']})

# Runtime-generated honest self-loop: two calls of config A, plus distinct config B.
# Canonical A and B intentionally share their first 80 characters.
config_a = {'long_padding': 'x' * 120, 'variant': 1}
config_b = {'long_padding': 'x' * 120, 'variant': 2}
payload_a = json.dumps(config_a, sort_keys=True, separators=(',', ':'))
payload_b = json.dumps(config_b, sort_keys=True, separators=(',', ':'))
assert payload_a[:80] == payload_b[:80] and payload_a != payload_b
parsed_a = _parse_evaluate_config(payload_a, '0.7')
parsed_b = _parse_evaluate_config(payload_b, '0.8')
graph = SharedExplorationGraph(n_agents=2, diversity_mode=True)
graph.record_evaluate_config(0, parsed_a[0], parsed_a[1], 0.7, 1.0, completion_time=1.0)
graph.record_evaluate_config(0, parsed_a[0], parsed_a[1], 0.7, 1.0, completion_time=2.0)
graph.record_evaluate_config(1, parsed_b[0], parsed_b[1], 0.8, 1.0, completion_time=1.0)
text = graph.format_for_injection(visible_before=3.0, agent_id=0)
base = {'strategy': 'poolact', 'agents': 2, 'config': {'scenario': 'tuning',
        'poolact_protocol': 'paper-graph-lock-v4'}, 'agent_results': [
        {'agent_id': 0, 'messages': [{'role': 'tool', 'content': text}],
         'tool_records': [['evaluate_config', payload_a, '0.7']] * 2,
         'eval_records': [[payload_a, parsed_a[0], 0.7, 1.0]] * 2},
        {'agent_id': 1, 'messages': [],
         'tool_records': [['evaluate_config', payload_b, '0.8']],
         'eval_records': [[payload_b, parsed_b[0], 0.8, 1.0]]}]}
selfloop = exercise('runtime_true_same_long_config_selfloop', base, True)
assert selfloop['counters']['unambiguous_same_configuration_self_loops'] == 1
alias_a = 'E:h:' + hashlib.sha256(payload_a.encode()).hexdigest()[:12]
alias_b = 'E:h:' + hashlib.sha256(payload_b.encode()).hexdigest()[:12]
assert alias_a in text and alias_b in text

mut = copy.deepcopy(base)
mut['agent_results'][0]['tool_records'] = mut['agent_results'][0]['tool_records'][:1]
mut['agent_results'][0]['eval_records'] = mut['agent_results'][0]['eval_records'][:1]
exercise('mutation_selfloop_without_repeated_source_configuration', mut, False,
         required_errors=('self_loop_without_repeated_source_configuration',))

mut = copy.deepcopy(base)
mut['agent_results'][0]['messages'][0]['content'] = text.replace(alias_b, alias_a)
exercise('mutation_two_payloads_one_alias', mut, False, required_errors=(
    'hash_alias_payload_mismatch', 'rendered_identity_collision', 'path_endpoint_ambiguous'))
mut = copy.deepcopy(base)
mut['agent_results'][0]['messages'][0]['content'] = text.replace(
    alias_a + ' --> ' + alias_a, alias_a + ' --> E:h:' + '0' * 12)
exercise('mutation_missing_path_endpoint', mut, False, required_errors=('path_endpoint_missing',))
mut = copy.deepcopy(base)
mut['agent_results'][0]['messages'][0]['content'] = text.replace(alias_a + ' ', '', 1)
exercise('mutation_modern_long_node_missing_alias', mut, False,
         required_errors=('modern_long_node_missing_hash_alias', 'path_endpoint_missing'))
mut = copy.deepcopy(base)
mut['agent_results'][0]['tool_records'] = []
mut['agent_results'][0]['eval_records'] = []
exercise('mutation_missing_source_payload', mut, False,
         required_errors=('node_payload_missing', 'path_endpoint_missing'))
mut = copy.deepcopy(base)
mut['agent_results'][0]['messages'][0]['content'] = [{'type': 'text', 'text': text}]
exercise('content_blocks_supported', mut, True)
mut = copy.deepcopy(base)
mut['agent_results'][0]['messages'][0]['role'] = 'user'
exercise('user_graph_messages_supported', mut, True)
mut = copy.deepcopy(base)
mut['agent_results'][0]['messages'][0]['role'] = 'assistant'
exercise('assistant_graph_is_not_input_evidence', mut, False,
         required_errors=('missing_all_graph_snapshots',))
mut = copy.deepcopy(base)
mut['agent_results'][0]['messages'] = []
exercise('missing_graph_with_recorded_evaluation', mut, False,
         required_errors=('missing_all_graph_snapshots',))
exercise('non_hpo_scope_boundary', {'strategy': 'poolact', 'config': {'scenario': 'evidence_audit'}},
         True, False)
exercise('unknown_strategy_rejected', {'strategy': 'unknown', 'config': {'scenario': 'tuning'}},
         False, required_errors=('unknown_strategy', 'missing_agent_results'))
exercise('missing_agents_rejected', {'strategy': 'poolact', 'config': {'scenario': 'tuning'}},
         False, required_errors=('missing_agent_results',))

# Default graph mode also binds the same complete long payload correctly.
default_graph = SharedExplorationGraph(n_agents=2)
default_graph.record_evaluate_config(0, parsed_a[0], parsed_a[1], 0.7, 1.0, completion_time=1.0)
mut = copy.deepcopy(base)
mut['agent_results'][0]['messages'][0]['content'] = default_graph.format_for_injection(
    visible_before=3.0, agent_id=0)
exercise('runtime_default_graph_layout', mut, True)

# The verifier must remain independent of runtime implementation imports.
tree = ast.parse(TARGET.read_text())
imports = sorted({node.module.split('.')[0] for node in ast.walk(tree)
                  if isinstance(node, ast.ImportFrom) and node.module} |
                 {item.name.split('.')[0] for node in ast.walk(tree)
                  if isinstance(node, ast.Import) for item in node.names})
imports_stdlib_only = all(name in sys.stdlib_module_names or name == '__future__' for name in imports)
output = {
    'schema_version': 'expgym.graph-validation-independent-tests.v1',
    'scope': 'Existing source fixtures and synthetic local runtime graph objects only; no models, API requests, production trace mutation, commit or push.',
    'passed': all(t['passed'] for t in tests) and imports_stdlib_only,
    'tests': len(tests), 'test_passes': sum(t['passed'] for t in tests),
    'module_boundary': {'runtime_implementation_not_imported_by_verifier': imports_stdlib_only,
                        'imports': imports, 'all_inputs_unchanged': all(t['input_not_mutated'] for t in tests)},
    'sources': [{'path': str(p), 'sha256': sha(p)} for p in (
        TARGET, inventory_path, Path(__file__), RUNTIME/'expgym/extras/parallel_cache.py')],
    'synthetic_runtime_selfloop': {'config_a': payload_a, 'config_b': payload_b,
        'same_first_80_characters': True, 'rendered_graph': text,
        'runtime_selfloop_count': 1, 'source_result': base},
    'results': tests,
}
(HERE/'GRAPH_VALIDATION_TESTS.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'passed': output['passed'], 'tests': output['tests'],
                  'passes': output['test_passes'], 'module_boundary': output['module_boundary'],
                  'output_sha256': sha(HERE/'GRAPH_VALIDATION_TESTS.json')}, indent=2))
if not output['passed']:
    raise SystemExit(1)
