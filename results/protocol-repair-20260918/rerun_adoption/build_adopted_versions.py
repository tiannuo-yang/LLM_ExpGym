#!/usr/bin/env python3
"""Portable 810-slot original/adopted HPO execution and scoring code inventory.

Capture mode reads verified local historical source trees once. Build mode uses
only the portable captured input and completed HPO adoption exports; no model or
raw trajectory access is needed. Execution parser and offline scorer stay separate.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

MODULES = {'parser': 'expgym/tool_protocol.py', 'react_loop': 'expgym/react_loop.py',
           'graph': 'expgym/extras/parallel_cache.py', 'poolact': 'expgym/poolact.py'}
IDENTITY = ('slot_id', 'model', 'system', 'regime', 'strategy', 'item', 'seed', 'outer_repeat')
KEEP = IDENTITY + ('cohort_id', 'trajectory_sha256', 'code_commit', 'source_tree_sha256',
    'source_tree_verified', 'graph_protocol', 'backend', 'api_protocol', 'temperature',
    'top_p', 'top_k', 'reasoning_effort', 'chat_template_kwargs', 'max_tokens_config',
    'max_context_tokens', 'max_steps', 'max_evals', 'time_budget', 'tool_protocol',
    'tuning_final_policy', 'evaluation_identity_sha256', 'task_config_sha256',
    'budget_oracle_sha256', 'table_sha256', 'decoder_sha256', 'numpy_version',
    'configspace_version', 'python_version', 'numpy_tie_semantics', 'planned_action',
    'planned_reason', 'parser_control_flow_changed', 'parser_control_flow_turns')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def rows(path):
    with Path(path).open(newline='') as f: return list(csv.DictReader(f))
def jwrite(path, value): Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n')
def cwrite(path, data):
    with Path(path).open('w', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=list(data[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(data)
def packed(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def capture(a):
    planning=a.capture_planning.resolve(); source=planning/'hpo_all_slots.csv'
    original=rows(source); assert len(original)==810
    spec=importlib.util.spec_from_file_location('capture_trace_v2', a.repo/'expgym/trace_v2.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    components={}; output=[]
    for row in original:
        tree=row['source_tree_sha256']; root=Path(row['source_root'])
        assert row['source_tree_verified']=='True'
        if tree not in components:
            assert module.source_tree_sha256(root)==tree, f'Historical source tree changed: {tree}'
            components[tree]={k:sha(root/path) for k,path in MODULES.items()}
        out={k:row[k] for k in KEEP}
        out.update({f'{k}_sha256':v for k,v in components[tree].items()})
        output.append(out)
    a.output.mkdir(parents=True, exist_ok=True)
    path=a.output/'historical_hpo_versions_input.csv'; cwrite(path, output)
    jwrite(a.output/'HISTORICAL_CODE_INPUT_CHECKS.json', dict(status='PASS', slots=810,
        source_trees=len(components), source_tree_verified_slots=810,
        source_planning_sha256=sha(source), portable_input_sha256=sha(path),
        modules=MODULES, components_by_source_tree=components,
        provenance='Complete historical source trees rehashed before module capture; no Git commit invented when original run omitted it.'))

def build(a):
    adoption=a.adoption.resolve(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    manifest=load(adoption/'FAIRNESS_MANIFEST.json')
    assert manifest['status']=='PASS' and manifest['adoption_ready'] is True, 'All 97 HPO pools must pass before adopted code versions are emitted'
    assert manifest['adoption_scope']=='hpo97_stage_only'
    assert manifest['verified_complete_pools']==97 and manifest['verified_complete_members']==388
    original_path=a.historical_input or Path(__file__).with_name('historical_hpo_versions_input.csv')
    capture_checks=load(original_path.with_name('HISTORICAL_CODE_INPUT_CHECKS.json'))
    assert capture_checks['status']=='PASS' and sha(original_path)==capture_checks['portable_input_sha256']
    old=rows(original_path); assert len(old)==len({r['slot_id'] for r in old})==810
    source_path=adoption/'new_official/SOURCE_SELECTION.csv'
    scalar_path=adoption/'new_official/slot_scalars.csv'
    assert sha(source_path)==manifest['official_source_selection_sha256']
    assert sha(scalar_path)==manifest['official_slot_scalars_sha256']
    source_rows=rows(source_path); scalar_rows=rows(scalar_path)
    sources={r['slot_id']:r for r in source_rows}
    scalars={r['slot_id']:r for r in scalar_rows}
    new_path=adoption/'progress/verified_sources.csv'
    replacement_rows=rows(new_path)
    replacements={r['slot_id']:r for r in replacement_rows}
    assert len(source_rows)==len(sources) and len(scalar_rows)==len(scalars)
    assert len(replacement_rows)==len(replacements)
    assert len(sources)==len(scalars)==4698 and len(replacements)==97
    planned={r['slot_id'] for r in old if r['planned_action']=='rerun'}
    assert set(replacements)==planned
    adopted=[]
    for row in old:
        sid=row['slot_id']; src=sources[sid]; scalar=scalars[sid]; new=replacements.get(sid)
        assert all(row[k]==scalar[k] for k in IDENTITY)
        assert src['result_sha256']==(new['result_sha256'] if new else row['trajectory_sha256'])
        if new:
            assert new['old_result_sha256']==row['trajectory_sha256']
            assert new['members']=='4' and row['system']=='poolact'
            assert new['model']==row['model']==src['model']
            assert new['cohort_id']==scalar['cohort_id']==src['cohort_id']
            assert new['new_job_id']==src['new_job_id']
            assert new['runtime_source_tree_sha256']==manifest['runtime_source_tree_sha256']
            assert new['runtime_source_tree_sha256']==src['runtime_source_tree_sha256']
            assert new['runtime_core_commit']==manifest['runtime_core_commit']==src['runtime_core_commit']
            assert new['runtime_snapshot_commit']==manifest['runtime_snapshot_commit']
            assert new['runtime_snapshot_commit']==src['runtime_snapshot_commit']
            assert new['parser_sha256']==manifest['parser_sha256']
            assert new['graph_sha256']==manifest['graph_sha256']
        item={k:row[k] for k in IDENTITY}
        item.update(original_result_sha256=row['trajectory_sha256'], adopted_result_sha256=src['result_sha256'],
            original_code_commit=row['code_commit'], original_source_tree_sha256=row['source_tree_sha256'],
            adopted_code_commit=new['runtime_snapshot_commit'] if new else row['code_commit'],
            adopted_core_repair_commit=new['runtime_core_commit'] if new else '',
            adopted_source_tree_sha256=new['runtime_source_tree_sha256'] if new else row['source_tree_sha256'],
            original_run_parser_module=MODULES['parser'], original_run_parser_sha256=row['parser_sha256'],
            original_run_react_loop_sha256=row['react_loop_sha256'],
            adopted_run_parser_module=MODULES['parser'], adopted_run_parser_sha256=new['parser_sha256'] if new else row['parser_sha256'],
            original_graph_module=MODULES['graph'], original_graph_sha256=row['graph_sha256'],
            adopted_graph_sha256=new['graph_sha256'] if new else row['graph_sha256'],
            original_graph_protocol=row['graph_protocol'], adopted_graph_protocol=new['poolact_protocol'] if new else row['graph_protocol'],
            graph_consumed=row['strategy']=='poolact',
            scoring_parser_sha256=manifest['parser_sha256'], scoring_protocol='final-answer-boundary-v2',
            scoring_helper_sha256=manifest['formal_scoring_helper_sha256'],
            scoring_layer='new_runtime_rescored' if new else 'existing_trace_rescored',
            adoption_action='replace_entire_four_member_pool' if new else 'reuse_original_execution_with_full_rescore',
            reuse_or_replacement_reason=row['planned_reason'],
            original_provider_backend=row['backend'], adopted_provider_backend=new['provider_backend'] if new else row['backend'],
            original_cohort_id=row['cohort_id'], adopted_cohort_id=scalar['cohort_id'],
            new_job_id=new['new_job_id'] if new else '', source_tree_verified=row['source_tree_verified'],
            parser_control_flow_changed=row['parser_control_flow_changed'],
            numpy_version=row['numpy_version'], configspace_version=row['configspace_version'],
            generation_controls_preserved=True, historical_code_commit_recorded=bool(row['code_commit']))
        adopted.append(item)
    assert Counter(r['system'] for r in adopted)=={'expgym':486,'poolact':324}
    assert sum(r['adoption_action']=='replace_entire_four_member_pool' for r in adopted)==97
    keyfields=('model','system','regime','strategy'); groups=defaultdict(list)
    for row in adopted: groups[tuple(row[k] for k in keyfields)].append(row)
    grouped=[]
    for key, members in sorted(groups.items()):
        row=dict(zip(keyfields,key)); row.update(slots=len(members),
            replaced_pools=sum(bool(m['new_job_id']) for m in members),
            reused_original_runs=sum(not m['new_job_id'] for m in members))
        for col in ('original_code_commit','adopted_code_commit','adopted_core_repair_commit',
                    'original_source_tree_sha256','adopted_source_tree_sha256','original_run_parser_sha256',
                    'adopted_run_parser_sha256','scoring_parser_sha256','original_graph_sha256',
                    'adopted_graph_sha256','original_graph_protocol','adopted_graph_protocol',
                    'original_provider_backend','adopted_provider_backend','scoring_layer',
                    'reuse_or_replacement_reason','numpy_version','configspace_version'):
            row[col]=packed(sorted({m[col] for m in members}))
        row['original_commit_not_recorded_slots']=sum(not m['historical_code_commit_recorded'] for m in members)
        grouped.append(row)
    assert len(grouped)==54
    paths=[out/'adopted_hpo_code_versions.csv', out/'adopted_hpo_model_budget_strategy.csv']
    cwrite(paths[0],adopted); cwrite(paths[1],grouped)
    jwrite(out/'ADOPTED_CODE_VERSION_CHECKS.json', dict(status='PASS', adoption_scope='hpo97_stage_only',
        global_formal_adoption_claim=False, slots=810, N1_unchanged=486, N4_reused=227, N4_replaced=97,
        model_budget_strategy_groups=54, original_commit_not_recorded_slots=sum(not r['historical_code_commit_recorded'] for r in adopted),
        source_tree_verified_slots=810, scoring_parser_sha256=manifest['parser_sha256'],
        inputs={str(p.name):sha(p) for p in (original_path,adoption/'FAIRNESS_MANIFEST.json',source_path,scalar_path,new_path)},
        outputs={p.name:sha(p) for p in paths}, builder_sha256=sha(__file__),
        notes=['Original blank Git commits remain blank; historical source-tree hashes are authoritative.',
               'adopted_run_parser identifies actual model execution, while scoring_parser identifies offline final scoring.',
               'Legacy parser behavior also depended on react_loop.py; its original module hash is provided.',
               'A graph module hash does not imply that a single-agent or naive/cached run consumed a shared graph.',
               'The complete source tree binds all runtime modules and the inventory does not claim reused runs executed patched code.']))
    print(packed({'status':'PASS','slots':810,'groups':54,'replaced':97,'reused':713}))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-planning',type=Path)
    parser.add_argument('--repo',type=Path)
    parser.add_argument('--historical-input',type=Path)
    parser.add_argument('--adoption',type=Path,default=Path(__file__).parent)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    if a.capture_planning:
        if not a.repo: parser.error('--capture-planning requires --repo')
        capture(a)
    else: build(a)
if __name__=='__main__': main()
