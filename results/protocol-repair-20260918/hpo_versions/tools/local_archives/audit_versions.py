#!/usr/bin/env python3
"""Read and hash every adopted HPO slot; no API requests or scorer mutations."""
import collections, csv, hashlib, json, pathlib, sys

# REQUIRES LOCAL ARCHIVES: this is not the public-table-only verifier.
import argparse
_archive_cli = argparse.ArgumentParser(description="Requires original private trajectories, frozen source trees and benchmark files; no model calls")
_archive_cli.add_argument('--workspace', required=True, help='Original archive workspace root; recorded source paths must resolve')
_archive_cli.add_argument('--output', required=True, help='Separate audit output directory; do not overwrite the public package')
_archive_args = _archive_cli.parse_args()
ROOT = pathlib.Path(_archive_args.workspace).resolve()
OUT = pathlib.Path(_archive_args.output).resolve()
OUT.mkdir(parents=True, exist_ok=True)
REPO=ROOT/'LLM_ExpGym-lightweight-20260917'
sys.path.insert(0,str(REPO))
from expgym.react_loop import _estimate_tokens
from expgym.trace_v2 import source_tree_sha256

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write_csv(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

selected=list(csv.DictReader((REPO/'results/gemini-openrouter-20260917/main/SOURCE_SELECTION.csv').open()))
new={x['slot_id']:x for x in json.loads((ROOT/'gemini_openrouter_20260917/planning/main/main-completed-result-paths.json').read_text())['results']}
graph={x['slot_id']:x for x in csv.DictReader((ROOT/'code_review_20260918/poolact/hpo_graph_slots.csv').open())}
control_file=ROOT/'protocol_repair_20260918/analysis/rescore/hpo/turn_parser_changes.csv'
control_changes={}
if control_file.exists():
    for x in csv.DictReader(control_file.open()):
        if x['action_control_flow_changed']=='True':control_changes.setdefault(x['slot_id'],[]).append(x)
roots=json.loads((ROOT/'protocol_repair_20260918/planning/hpo_versions/source_roots.json').read_text())
root_by_sha={x['source_tree_sha256']:pathlib.Path(x['path']) for x in roots}
keyfiles=['expgym/react_loop.py','expgym/poolact.py','expgym/extras/parallel_cache.py','expgym/task_tuning.py','expgym/task_tuning_hpobench.py','expgym/compact_nasbench101.py','expgym/llm_clients.py','expgym/native_responses_client.py','expgym/native_gemini_client.py','expgym/openrouter_gemini_client.py','scripts/run_poolact.py','scripts/run_paper_sweep.py']
allrows=[]; keyrows=[]; configs={}; unidentified=set(); seen=set(); inputs={}
for r in selected:
    if r['scenario']!='tuning':continue
    p=ROOT/'deliveries/paper-ad03e8c-20260916'/r['historical_trajectory'] if r['historical_trajectory'] else pathlib.Path(new[r['slot_id']]['result_path'])
    assert sha(p)==r['result_sha256']; j=json.loads(p.read_text())
    ispool=r['system']=='poolact'
    if ispool:
        c=j['config']; prov={}; tree=j['implementation_sha256']['source_tree']; identity=c['evaluation_identity']; gen={k:c.get(k) for k in ('temperature','top_p','top_k','chat_template_kwargs','reasoning_effort','max_tokens','api_protocol')}; limits={'max_context_tokens':c.get('max_context_tokens'),'max_steps':c.get('max_steps'),'max_evaluations':c.get('max_evals')}; backend=c.get('backend'); base_url=c.get('base_url'); protocol=c.get('poolact_protocol'); agents=j['agent_results']; budget=c.get('time_budget'); configs[r['slot_id']]=c
    else:
        c=j['run'];prov=j['provenance']['repository']; tree=prov['source_tree_sha256'];identity=c['evaluation_identity'];gen=c['generation']; limits=j['task']['limits']; backend=c['backend']['name']; base_url=c['backend'].get('base_url');protocol='single';agents=[];budget=j['task']['budget'].get('limit_seconds')
    matching=root_by_sha.get(tree)
    # A metadata path locates historical code, but is not proof that its current
    # contents are the executed snapshot. Only an exact source-tree match is.
    candidate=pathlib.Path(identity['files']['task_configuration']['path']).parents[1]
    if not matching:unidentified.add(tree)
    if tree not in seen:
        seen.add(tree)
        if matching: assert source_tree_sha256(matching)==tree
        for rel in keyfiles:
            fp=(matching or candidate)/rel
            if fp.is_file():keyrows.append({'source_tree_sha256':tree,'module':rel,'sha256':sha(fp),'match_status':'verified_complete_tree' if matching else 'candidate_path_only','local_path':str(fp)})
    files=identity.get('files',{}); deps=identity.get('dependencies',{})
    for kind,info in files.items():
        ip=pathlib.Path(info['path'])
        ikey=(kind,str(ip.resolve()))
        if ikey not in inputs:
            actual=sha(ip) if ip.is_file() else None
            inputs[ikey]={'kind':kind,'path':str(ip.resolve()),'recorded_sha256':info.get('sha256'),'actual_sha256':actual,'match':actual==info.get('sha256')}
        assert inputs[ikey]['match'],(r['slot_id'],kind,info['path'])
    graphrow=graph.get(r['slot_id'],{})
    # Full saved histories provide a conservative upper bound on any sent prefix.
    # Terminal assistant included, so below-cap proves cap non-binding.
    full_history_max=max([_estimate_tokens(a['messages']) for a in agents] or [0])
    row={k:r[k] for k in ('slot_id','model','system','item','regime','strategy','seed','outer_repeat','cohort_id','selection')}
    row.update(trajectory=str(p),trajectory_sha256=r['result_sha256'],code_commit=prov.get('commit'),source_tree_sha256=tree,source_root=str(matching) if matching else '',source_tree_verified=bool(matching),graph_protocol=protocol,backend=backend,api_protocol=gen.get('api_protocol') or c.get('api_protocol') or 'chat_completions',base_url=base_url,temperature=gen.get('temperature'),top_p=gen.get('top_p'),top_k=gen.get('top_k'),reasoning_effort=gen.get('reasoning_effort'),chat_template_kwargs=pack(gen.get('chat_template_kwargs')),max_tokens_config=gen.get('max_tokens'),max_context_tokens=limits.get('max_context_tokens'),max_steps=limits.get('max_steps'),max_evals=limits.get('max_evaluations'),time_budget=budget,tool_protocol=c.get('tool_protocol') if ispool else c['protocol'].get('tool_protocol'),tuning_final_policy=c.get('tuning_final_policy') if ispool else c['protocol'].get('tuning_final_policy'),evaluation_identity_sha256=identity.get('sha256'),task_config_sha256=files.get('task_configuration',{}).get('sha256'),budget_oracle_sha256=files.get('budget_oracle',{}).get('sha256'),table_sha256=files.get('table',{}).get('sha256'),decoder_sha256=files.get('decoder_source',{}).get('sha256'),numpy_version=deps.get('numpy',{}).get('version'),configspace_version=deps.get('ConfigSpace',{}).get('version'),python_version=identity.get('python',{}).get('version'),numpy_tie_semantics=pack(identity.get('semantics')),saved_full_history_estimate_max=full_history_max,prefix_collision_groups=graphrow.get('collision_groups',0),ambiguous_path_messages=graphrow.get('path_ambiguous_messages',0),same_name_selfloop_messages=graphrow.get('selfloop_messages',0))
    if not ispool:
        decision='reuse_with_full_rescore'; reason='single agent does not consume shared graph'
    elif r['strategy']=='poolact' and protocol.endswith('v3'):
        decision='rerun';reason='entire legacy graph protocol cohort; includes no-observed-collision slots'
    elif r['model'].startswith('gemini') and r['strategy'] in ('naive','cached') and not r['new_result_index']:
        decision='rerun';reason='paired control migration from Sub2 Gemini to fixed OpenRouter provider'
    else:
        decision='conditional_reuse_with_full_rescore';reason='graph-independent control or already-fixed v4; require runtime/parser acceptance equivalence'
    changes=control_changes.get(r['slot_id'],[])
    if changes:
        decision='rerun';reason+='; deterministic final-parser control-flow divergence in saved intermediate assistant turn'
    row.update(planned_action=decision,planned_reason=reason,parser_control_flow_changed=bool(changes),parser_control_flow_turns=pack([{k:x[k] for k in ('agent_id','call_index','message_id','old_accepts_final','new_accepts_final')} for x in changes]))
    allrows.append(row)

write_csv('hpo_all_slots.csv',allrows)
write_csv('module_hashes.csv',keyrows)
write_csv('input_hashes.csv',list(inputs.values()))
write_csv('hpo_rerun_slots.csv',[x for x in allrows if x['planned_action']=='rerun'])
(OUT/'hpo_n4_original_configs.json').write_text(json.dumps(configs,indent=2,ensure_ascii=False)+'\n')
groups=collections.defaultdict(list)
for r in allrows:groups[(r['model'],r['system'],r['regime'],r['strategy'])].append(r)
summary=[]
for key,rs in sorted(groups.items()):
    d=dict(zip(('model','system','regime','strategy'),key)); d['slots']=len(rs)
    for k in ('code_commit','source_tree_sha256','graph_protocol','backend','api_protocol','max_context_tokens','temperature','top_p','top_k','reasoning_effort','chat_template_kwargs','max_tokens_config','max_steps','max_evals','numpy_version','configspace_version','planned_action'):
        d[k]=pack(sorted({str(x[k]) for x in rs}))
    d['prefix_collision_slots']=sum(int(x['prefix_collision_groups'])>0 for x in rs);d['ambiguous_path_slots']=sum(int(x['ambiguous_path_messages'])>0 for x in rs);d['same_name_selfloop_slots']=sum(int(x['same_name_selfloop_messages'])>0 for x in rs);d['source_tree_verified_slots']=sum(x['source_tree_verified'] for x in rs);d['full_history_estimate_max']=max(x['saved_full_history_estimate_max'] for x in rs)
    summary.append(d)
write_csv('hpo_model_budget_strategy.csv',summary)
checks={'adopted_slots':len(allrows),'N1':sum(x['system']=='expgym' for x in allrows),'N4':sum(x['system']=='poolact' for x in allrows),'all_trajectory_hashes_match':True,'input_hashes_checked':len(inputs),'input_hashes_match':all(v['match'] for v in inputs.values()),'unmatched_source_tree_hashes':sorted(unidentified),'source_tree_verified_slots':sum(x['source_tree_verified'] for x in allrows),'rerun_slots':sum(x['planned_action']=='rerun' for x in allrows),'rerun_agent_trajectories':4*sum(x['planned_action']=='rerun' for x in allrows),'full_history_bound_scope':'N4 final saved messages, terminal assistant included; conservative bound without tool schema; add schema before asserting cap non-binding','planned_action_counts':dict(collections.Counter(x['planned_action'] for x in allrows))}
(OUT/'CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
