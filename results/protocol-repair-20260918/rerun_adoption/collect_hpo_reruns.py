#!/usr/bin/env python3
"""Collect exactly the pre-registered 97 HPO N4 controls without model calls.

Incomplete queues produce progress exports only. The 4,698-row adopted table is
written only after all 97 complete pools, identities, immutable artifacts, final
answers, benchmark scores and shared graph checks pass. No selection by score.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
from collections import Counter

EXPECTED={'gemini':49,'gpt':9,'glm':10,'kimi':9,'qwen':19,'deepseek':1}
CORE=('slot_id','model','system','scenario','regime','strategy','item','outer_repeat','order','seed','family')
PRESERVED=('temperature','max_tokens','top_p','top_k','reasoning_effort','chat_template_kwargs',
           'max_context_tokens','max_steps','max_evals','agents','cost_regime','tuning_task',
           'strategies','tool_protocol','max_protocol_retries','tuning_final_policy','missing_final_policy',
           'probes','request_timeout','max_retries','retry_base_seconds','retry_max_seconds')
DATA_FILES=('task_configuration','budget_oracle','table','decoder_source','table_manifest')
METRICS=('raw_perf_mi','raw_perf_bon','gap_mi','gap_bon','gap0_mi','gap0_bon')
HASH_CACHE={}


def jload(path):return json.loads(path.read_text())
def jdump(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))
def digest(value):return hashlib.sha256(jdump(value).encode()).hexdigest()
def sha(path):
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular file: '+str(path))
    st=path.stat();key=(str(path),st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    if key not in HASH_CACHE:
        h=hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        end=path.stat();assert (end.st_ino,end.st_size,end.st_mtime_ns,end.st_ctime_ns)==key[1:]
        HASH_CACHE[key]=h.hexdigest()
    return HASH_CACHE[key]
def read_csv(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))
def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
    temp.replace(path)
def write_csv(path,rows,fields=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    keys=fields or list(dict.fromkeys(k for row in rows for k in row))
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(rows)
    temp.replace(path)
def nullable_bool(v):return v in (True,'True','true',1,'1')
def close(a,b):
    if a is None or b is None:return a is b
    return type(a) in (int,float) and type(b) in (int,float) and math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m
def portable(path,root):
    try:return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:return str(path)


def inventory(path):
    answer={}
    for p in sorted(path.rglob('*')):
        if p.is_symlink():raise ValueError('Symlink in completed invocation: '+str(p))
        if p.is_file():answer[p.relative_to(path).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
    return answer


def assert_identity(binding,job,planned,old_config,tree):
    sid=planned['slot_id']
    assert binding['old_slot_id']==sid and job['stage']=='repair-'+sid
    assert binding['new_job_id']==job['job_id']=='job_'+digest(job['identity'])
    assert binding['model']==planned['model'] and binding['outer_repeat']==int(planned['outer_repeat'])
    assert binding['source_trajectory_sha256']==planned['trajectory_sha256']
    assert binding['source_trajectory']==planned['trajectory']
    assert binding['selection']==job['selection']
    assert binding['output_dir']==job['args']['output_dir']
    assert job['runner']=='poolact' and job['identity']['source_tree_sha256']==tree
    for field in ('runner','selection','python','endpoints'):
        assert job[field]==job['identity'][field],(sid,field,'job/identity mismatch')
    assert set(job['args'])-set(job['identity']['args'])=={'output_dir','repeats'}
    for field,value in job['identity']['args'].items():
        if field!='prompt_cache_key':assert job['args'][field]==value,(sid,field,'effective args differ from hashed identity')
    expected_cache=None if planned['model'] in ('glm-5.3','kimi-k3') else 'queue-'+digest(job['identity'])[:40]
    assert job['args']['prompt_cache_key']==expected_cache,(sid,'undeclared cache namespace override')
    if planned['model']=='gemini-3.8-flash-medium':
        assert (job['args']['model'],job['args']['backend'])==('google/gemini-3.8-flash','openrouter')
    else:
        assert job['args']['model']==old_config['model'] and job['args']['backend']==old_config['backend']
    assert job['selection']['strategy']==planned['strategy']
    assert job['args']['seed']==int(planned['seed'])==old_config['seed']
    assert job['args']['tuning_task']==planned['item'] and job['args']['cost_regime']==planned['regime']
    for field in PRESERVED:assert job['args'].get(field)==old_config.get(field),(sid,field,'plan differs from original')
    assert job['args']['agents']==4 and job['args']['repeats']==1
    assert job['args']['resume'] is False and job['args']['api_key'] is None and job['args']['api_key_file'] is None


def verify_data(config,old_config):
    new=config['evaluation_identity'];old=old_config['evaluation_identity'];checked=[]
    assert new['selected']==old['selected']
    for name in DATA_FILES:
        a,b=new['files'].get(name),old['files'].get(name)
        assert (a is None)==(b is None),(name,'presence')
        if a is None:continue
        for field in ('present','sha256','bytes'):assert a.get(field)==b.get(field),(name,field)
        if a.get('present'):
            p=Path(a['path']);assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256'],name
            checked.append({'role':name,'sha256':a['sha256'],'bytes':a['bytes']})
    assert new['semantics']==old['semantics'],'NumPy tie semantics changed'
    for name in ('numpy','ConfigSpace','PyYAML'):
        a,b=new['dependencies'].get(name),old['dependencies'].get(name)
        assert a['version']==b['version'],(name,'version')
        for mod,rec in a['modules'].items():
            prior=b['modules'][mod]
            assert rec['sha256']==prior['sha256'],(name,mod,'dependency module changed')
            p=Path(rec['path']);assert sha(p)==rec['sha256']
    return checked


class RuntimeChecks:
    def __init__(self,runtime,repo,output):
        sys.path.insert(0,str(runtime))
        from expgym import tool_protocol
        from expgym.trace_v2 import source_tree_sha256
        from scripts import run_study_queue,run_poolact
        self.protocol=tool_protocol;self.tree=source_tree_sha256(runtime)
        self.queue=run_study_queue;self.pool=run_poolact
        self.helper=module(repo/'tools/rescore_hpo_protocol.py','_hpo_repair_formal_rescorer')
        assert Path(tool_protocol.__file__).resolve()==(runtime/'expgym/tool_protocol.py').resolve()
        assert sha(repo/'expgym/tool_protocol.py')==sha(runtime/'expgym/tool_protocol.py')
        self.helper.Evaluator # Ensure documented formal helper exists before accepting any result.
        self.evaluator=self.helper.Evaluator()
        self.graph=module(Path(__file__).with_name('verify_graph.py'),'_hpo_repair_graph_acceptance')
        self.oracle_path=runtime/'data/hpo_tuning/oracle3.json'
        self.oracle=jload(self.oracle_path)['tasks']
        self.runtime=runtime;self.repo=repo;self.output=output

    def verify(self,binding,job,result,old_config,path,completion):
        sid=binding['old_slot_id'];cfg=result['config'];agents=result['agent_results']
        assert result['strategy']==job['selection']['strategy'] and result['agents']==4
        assert len(agents)==4 and [a['agent_id'] for a in agents]==[0,1,2,3]
        assert [a['seed'] for a in agents]==list(range(job['args']['seed'],job['args']['seed']+4))
        assert all(a['api_dump']['run_id']==binding['new_job_id'] for a in agents),'Member from a different invocation'
        assert len({a['api_dump']['client_id'] for a in agents})==4,'Distinct member API clients required'
        assert cfg['agent_seeds']==[a['seed'] for a in agents]
        assert all(a['strategy']==result['strategy'] and a['repeat_index']==0 for a in agents)
        assert result['implementation_sha256']=={'source_tree':self.tree}
        assert cfg['poolact_protocol']=='paper-graph-lock-v4'
        assert cfg['time_budget']==old_config['time_budget']
        for field in PRESERVED:assert cfg.get(field)==job['args'].get(field),(sid,field,'result differs from plan')
        for field in ('model','backend','base_url','prompt_cache_key','prompt_cache_key_field','seed'):
            assert cfg.get(field)==job['args'].get(field),(sid,field,'actual setting differs')
        assert result['terminal_status']['execution_complete'] is True
        assert result['terminal_status']['expected_model_terminals']==result['terminal_status']['reported_model_terminals']==4
        assert all(a['terminal_status']['execution_complete'] is True for a in agents)
        data=verify_data(cfg,old_config)
        # Read-only production revalidation includes exact config/data identity,
        # independent task scoring and raw/terminal artifact consistency.
        self.queue.verify_result(job,self.queue.namespace(job['args']))
        final_rows=[];packages=[];perfs=[];finals=[]
        for a in agents:
            agent,record_ids,turns=self.helper.n4_agent(a)
            assert all(self.helper.parse_turn(t,a['tool_protocol'],self.protocol.parse_final_answer) is None
                       for t in turns if not t['is_terminal']),(sid,a['agent_id'],'runtime skipped an accepted final before its recorded terminal')
            terminal=[t for t in turns if t['is_terminal']];assert len(terminal)==1
            turn=terminal[0]
            extracted=self.helper.parse_turn(turn,a['tool_protocol'],self.protocol.parse_final_answer)
            answer,perf,source,record,reason=self.helper.select_answer(extracted,a['eval_records'],record_ids,cfg['tuning_task'],self.evaluator)
            assert answer==a.get('answer') and close(perf,a.get('answer_perf')),(sid,a['agent_id'],'saved final disagrees with frozen parser/scorer')
            assert source==a.get('answer_score_source'),(sid,a['agent_id'],'score-source mismatch')
            if perf is not None:
                measured,_=self.evaluator.evaluate(cfg['tuning_task'],answer)
                assert close(measured,perf),(sid,a['agent_id'],'benchmark mismatch')
            if perf is None:assert answer is None,'Unexpected unscorable nonempty final; hold for explicit review'
            assert a['terminal_status']['score_complete']==(perf is not None)
            perfs.append(perf);finals.append(answer)
            final_rows.append(dict(slot_id=sid,new_job_id=binding['new_job_id'],agent_id=a['agent_id'],seed=a['seed'],
                final_answer=answer,extracted_answer=extracted,performance=perf,score_complete=perf is not None,
                answer_score_source=source,selected_record=record,reason=reason,
                assistant_turns_checked=len(turns),nonterminal_accepted_finals=0,
                terminal_classification=a['terminal_status']['terminal_classification'],
                result_sha256=sha(path),parser_sha256=sha(self.runtime/'expgym/tool_protocol.py')))
            projected_turn={**turn,'message':{'role':'assistant','content':turn['message'].get('content'),
                                             'tool_calls':bool(turn['message'].get('tool_calls'))}}
            packages.append(dict(agent_id=a['agent_id'],seed=a['seed'],terminal_turn=projected_turn,extracted_answer=extracted,
                eval_records=a['eval_records'],record_ids=record_ids,final_answer=answer,performance=perf,
                answer_score_source=source,selected_record=record,reason=reason,
                assistant_turns_checked=len(turns),nonterminal_accepted_finals=0,
                benchmark_certificate={'item':cfg['tuning_task'],'answer':answer,'performance':perf} if perf is not None else None))
        metrics=self.helper.perfs_metrics(perfs,finals,cfg['tuning_task'],self.oracle)
        assert all(metrics[k] is not None for k in ('gap0_mi','gap0_bon')),'Incomplete normal endpoint'
        agg=result['aggregate']
        # Runtime's presentation list uses '' for absent answers; scientific
        # finals and strict metrics retain None. Do not reject normal abstention.
        assert agg['individual_answers']==[v or '' for v in finals] and len(agg['individual_perfs'])==4
        assert all(close(x,y) for x,y in zip(agg['individual_perfs'],perfs))
        assert close(agg.get('mean_individual_perf'),metrics['raw_perf_mi'])
        assert close(agg.get('answer_perf'),metrics['raw_perf_bon'])
        assert result['terminal_status']['score_complete']==all(v is not None for v in perfs)
        graph=self.graph.verify_graph(result)
        assert graph['ok'],(sid,'graph acceptance failed',graph)
        return dict(metrics=metrics,agents=final_rows,graph=graph,data=data,package=dict(
            slot_id=sid,model=binding['model'],item=cfg['tuning_task'],regime=cfg['cost_regime'],strategy=result['strategy'],
            seed=cfg['seed'],outer_repeat=binding['outer_repeat'],result_sha256=sha(path),
            result_bytes=path.stat().st_size,new_job_id=binding['new_job_id'],source_tree_sha256=self.tree,
            config=cfg,oracle_reference=self.oracle[cfg['tuning_task']],agents=packages,metrics=metrics,
            execution_complete=True,score_complete=all(v is not None for v in perfs),graph_check=graph))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repair-root',type=Path,required=True)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--require-complete',action='store_true')
    a=p.parse_args();root=a.repair_root.resolve();repo=a.repo.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    analysis_code={path:sha(path) for path in (Path(__file__),Path(__file__).with_name('verify_graph.py'),repo/'tools/rescore_hpo_protocol.py')}
    runtime=root/'runtime';planning=root/'planning/hpo_versions';queues=root/'operations/queues-v2'
    selected_path=planning/'hpo_rerun_slots.csv';config_path=planning/'hpo_n4_original_configs.json'
    selected=read_csv(selected_path);wanted={r['slot_id']:r for r in selected}
    assert len(selected)==len(wanted)==97 and all(r['system']=='poolact' for r in selected)
    configs=jload(config_path);old=read_csv(repo/'results/gemini-openrouter-20260917/main/slot_scalars.csv')
    baseline=read_csv(root/'analysis/rescore/main/slot_scalars.csv')
    source_rows=read_csv(repo/'results/gemini-openrouter-20260917/main/SOURCE_SELECTION.csv')
    old_by={r['slot_id']:r for r in old};new_by={r['slot_id']:r for r in baseline};sources={r['slot_id']:r for r in source_rows}
    assert len(baseline)==len(new_by)==len(old_by)==len(sources)==4698
    assert set(new_by)==set(old_by)==set(sources) and set(wanted)<=set(new_by)
    runtime_manifest=jload(root/'runtime_build/RUNTIME_SOURCE_MANIFEST.json')
    mapping=jload(root/'runtime_build/SOURCE_MAPPING.json');tree=runtime_manifest['source_tree_sha256']
    release_path=root/'operations/EXECUTION_RELEASE.json'
    release=jload(release_path) if release_path.exists() else None
    if release:
        assert release['source_tree_sha256']==tree and release['whole_pools']==97 and release['agents']==388
        assert release['score_based_reruns'] is False
    assert runtime_manifest['status']=='FROZEN'
    for rec in runtime_manifest['files']:
        f=runtime/rec['path'];assert sha(f)==rec['sha256'] and f.stat().st_size==rec['bytes']
    os.environ.update(HPOBENCH_ROOT=str(runtime/'data/hpo_tuning/HPOBench'),XDG_DATA_HOME=str(runtime/'data/hpo_tuning/hpobench_data'),PYTHONDONTWRITEBYTECODE='1')
    manifests=[];bound={};errors=[]
    for alias,count in EXPECTED.items():
        directory=queues/alias;binding_path=directory/'BINDINGS.json'
        if not binding_path.exists():continue
        b=jload(binding_path);plan_path=directory/'queue-plan.json';plan=jload(plan_path)
        assert sha(plan_path)==b['plan_sha256'] and sha(directory/'matrix.json')==b['matrix_sha256']
        assert b['source_tree_sha256']==plan['source_tree_sha256']==tree
        if release:assert alias in release['models'] and release['plan_sha256'][alias]==b['plan_sha256']
        assert b['selection_csv_sha256']==sha(selected_path) and b['original_configs_sha256']==sha(config_path)
        assert b['automatic_score_based_reruns'] is False and b['attempt']==1
        jobs={j['job_id']:j for j in plan['jobs']};assert len(b['jobs'])==len(jobs)==count
        for binding in b['jobs']:
            sid=binding['old_slot_id'];assert sid not in bound and sid in wanted
            job=jobs[binding['new_job_id']]
            assert_identity(binding,job,wanted[sid],configs[sid],tree)
            assert sha(Path(binding['source_trajectory']))==binding['source_trajectory_sha256']==sources[sid]['result_sha256']
            bound[sid]=(alias,binding,job,plan)
        manifests.append(dict(model_alias=alias,binding_sha256=sha(binding_path),plan_sha256=sha(plan_path),matrix_sha256=b['matrix_sha256'],pools=count))
    statuses=[];candidates=[];comparisons=[];agents=[];packages=[];verified_sources=[];checker=None
    for sid,planned in sorted(wanted.items()):
        record=dict(slot_id=sid,model=planned['model'],item=planned['item'],regime=planned['regime'],
            strategy=planned['strategy'],seed=planned['seed'],outer_repeat=planned['outer_repeat'],
            rerun_reason=planned['planned_reason'],state='awaiting_binding',new_job_id='',result_sha256='',
            completion_sha256='',execution_complete=None,score_complete=None,error='')
        verified=None
        if sid in bound:
            alias,binding,job,plan=bound[sid];record['new_job_id']=binding['new_job_id']
            path=Path(binding['output_dir'])/planned['strategy']/'result.json'
            completion=Path(plan['output_root'])/'queue/jobs'/binding['new_job_id']/'completion.json'
            record['state']='awaiting_completion'
            if completion.exists():
                try:
                    receipt=jload(completion)
                    assert release is not None,'Completed job has no frozen execution release'
                    assert receipt['exit_code']==0 and receipt['identity_sha256']==digest(job['identity'])
                    assert receipt['job_id']==binding['new_job_id'] and receipt['mode']=='execute'
                    assert receipt['endpoint'] in job['endpoints']
                    assert receipt['artifacts']==inventory(Path(binding['output_dir']).parent),'Completed invocation artifact hash mismatch'
                    result=jload(path)
                    if checker is None:checker=RuntimeChecks(runtime,repo,out)
                    assert checker.tree==tree
                    verified=checker.verify(binding,job,result,configs[sid],path,receipt)
                    record.update(state='verified_complete',result_sha256=sha(path),completion_sha256=sha(completion),execution_complete=True,score_complete=result['terminal_status']['score_complete'])
                    r=dict(new_by[sid]);r.update(metrics_json=jdump(verified['metrics']),execution_complete='True',
                        score_complete=str(result['terminal_status']['score_complete']),
                        provider_cohort='openrouter_google_ai_studio' if alias=='gemini' else 'preserved_historical_provider',
                        cohort_id='hpo_protocol_repair_20260918_'+alias+'_v2')
                    assert all(r[k]==new_by[sid][k] for k in CORE)
                    new_source=dict(slot_id=sid,model=r['model'],cohort_id=r['cohort_id'],
                        source_kind='new_runtime_complete_pool',old_result_sha256=sources[sid]['result_sha256'],
                        result_sha256=sha(path),result_bytes=path.stat().st_size,result_path=portable(path,root),
                        completion_sha256=sha(completion),new_job_id=binding['new_job_id'],runtime_source_tree_sha256=tree,
                        runtime_core_commit=mapping['repair_frozen_git_commit'],parser_sha256=sha(runtime/'expgym/tool_protocol.py'),
                        runtime_snapshot_commit=release['runtime_code_commit'],
                        graph_sha256=sha(runtime/'expgym/extras/parallel_cache.py'),poolact_protocol=result['config']['poolact_protocol'],
                        provider_backend=result['config']['backend'],provider_model=result['config']['model'],
                        provider_base_url=result['config']['base_url'],data_identities_json=jdump(verified['data']),
                        config_sha256=digest(result['config']),members=4,graph_check_status=verified['graph']['status'],
                        rerun_reason=planned['planned_reason'])
                    candidates.append(r);agents.extend(verified['agents']);packages.append(verified['package']);verified_sources.append(new_source)
                except Exception as exc:
                    record.update(state='validation_failed',error=type(exc).__name__+': '+str(exc))
                    errors.append({'slot_id':sid,'error':record['error']})
            elif (queues/alias/'RECOVERY_HOLD.json').exists():
                record['state']='operational_hold'
        statuses.append(record)
        before=json.loads(old_by[sid]['metrics_json']);rescored=json.loads(new_by[sid]['metrics_json'])
        current=verified['metrics'] if verified is not None and record['state']=='verified_complete' else {}
        for metric in METRICS:
            first,second,third=before[metric],rescored[metric],current.get(metric)
            comparisons.append(dict(slot_id=sid,model=planned['model'],task=planned['item'],regime=planned['regime'],strategy=planned['strategy'],
                seed=planned['seed'],outer_repeat=planned['outer_repeat'],metric=metric,state=record['state'],
                historical_score=first,existing_trace_rescored=second,new_runtime_score=third,
                extraction_delta=second-first if second is not None and first is not None else None,
                runtime_delta=third-second if third is not None and second is not None else None,
                old_result_sha256=sources[sid]['result_sha256'],new_result_sha256=record['result_sha256'],
                new_job_id=record['new_job_id'],reason=planned['planned_reason']))
    assert all(sha(path)==checksum for path,checksum in analysis_code.items()),'Analysis code changed during collection; rerun with frozen files'
    progress=out/'progress';write_csv(progress/'slot_status.csv',statuses)
    write_csv(progress/'completed_slot_scalars.csv',candidates,list(baseline[0]))
    write_csv(progress/'member_scores.csv',agents,list(agents[0]) if agents else ['slot_id','new_job_id','agent_id','performance','score_complete'])
    write_csv(out/'NEW_RUNTIME_COMPARISON.csv',comparisons)
    write_csv(progress/'verified_sources.csv',verified_sources,list(verified_sources[0]) if verified_sources else ['slot_id','result_sha256','new_job_id'])
    package_path=progress/'scoring_inputs.jsonl.gz'
    package_tmp=progress/'scoring_inputs.jsonl.gz.tmp'
    with package_tmp.open('wb') as f:
        with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0) as gz:
            for item in packages:gz.write((jdump(item)+'\n').encode())
    package_tmp.replace(package_path)
    ready=len(candidates)==97 and len(bound)==97 and not errors
    result_manifest=dict(schema='expgym.hpo-rerun-adoption.v1',status='PASS' if ready else ('FAIL' if errors else 'PENDING'),
        adoption_ready=ready,adoption_scope='hpo97_stage_only',global_formal_adoption_claim=False,
        requires_auxiliary_control_flow_stage=True,
        pre_registered_pools=97,pre_registered_members=388,verified_complete_pools=len(candidates),
        verified_complete_members=len(agents),status_counts=dict(Counter(r['state'] for r in statuses)),
        expected_model_counts=EXPECTED,verified_model_counts=dict(Counter(alias for sid,(alias,*_) in bound.items() if next(r for r in statuses if r['slot_id']==sid)['state']=='verified_complete')),
        runtime_source_tree_sha256=tree,runtime_core_commit=mapping['repair_frozen_git_commit'],
        runtime_snapshot_commit=release['runtime_code_commit'] if release else None,
        execution_release_sha256=sha(release_path) if release else None,
        parser_sha256=sha(runtime/'expgym/tool_protocol.py'),graph_sha256=sha(runtime/'expgym/extras/parallel_cache.py'),
        formal_scoring_helper_sha256=sha(repo/'tools/rescore_hpo_protocol.py'),graph_verifier_sha256=sha(Path(__file__).with_name('verify_graph.py')),
        public_scoring_inputs_sha256=sha(package_path),completed_slot_scalars_sha256=sha(progress/'completed_slot_scalars.csv'),
        source_plan_sha256=sha(selected_path),bindings=manifests,collector_sha256=sha(Path(__file__)),
        existing_trace_rescored_scalars_sha256=sha(root/'analysis/rescore/main/slot_scalars.csv'),
        historical_scalars_sha256=sha(repo/'results/gemini-openrouter-20260917/main/slot_scalars.csv'),
        errors=errors,model_calls=0,selection_policy='All 97 pre-registered pools, complete four-member first attempts; never rank/select attempts by scores.',
        missing_policy='Normal None remains None for strict endpoints and receives the existing Gap0 no-answer treatment. Pending or infrastructure failure receives no numeric replacement.',
        scope='Runtime/parser graph controls for the 97 pre-registered affected or provider-matched HPO pools; other HPO pools retain independently justified equivalent protocols. N1 behavior unchanged.')
    if ready:
        assert len(agents)==388 and len({r['slot_id'] for r in candidates})==97
        replacements={r['slot_id']:r for r in candidates};merged=[replacements.get(r['slot_id'],r) for r in baseline]
        assert len(merged)==4698 and sum(r['slot_id'] not in replacements and r==new_by[r['slot_id']] for r in merged)==4601
        adopted=[];source_new={r['slot_id']:r for r in verified_sources}
        for src in source_rows:
            r=dict(src)
            if r['slot_id'] in replacements:
                replacement=replacements[r['slot_id']];new_source=source_new[r['slot_id']]
                r.update(old_result_sha256=r['result_sha256'],result_sha256=new_source['result_sha256'],
                    cohort_id=replacement['cohort_id'],selection='new_runtime_protocol_repair',provider=replacement['provider_cohort'],
                    execution_complete=replacement['execution_complete'],score_complete=replacement['score_complete'],
                    historical_trajectory='',new_result_index='',old_historical_trajectory=r.get('historical_trajectory',''),
                    old_new_result_index=r.get('new_result_index',''),
                    new_result_path=new_source['result_path'],new_job_id=new_source['new_job_id'],
                    runtime_source_tree_sha256=tree,runtime_core_commit=mapping['repair_frozen_git_commit'])
                r['runtime_snapshot_commit']=release['runtime_code_commit']
            adopted.append(r)
        official=out/'new_official';write_csv(official/'slot_scalars.csv',merged,list(baseline[0]))
        write_csv(official/'SOURCE_SELECTION.csv',adopted);write_csv(official/'hpo_rerun_slot_scalars.csv',candidates,list(baseline[0]))
        write_csv(official/'SOURCE_INVENTORY.csv',verified_sources)
        result_manifest.update(adopted_main_slots=4698,replaced_slots=97,unchanged_rescored_slots=4601,
            official_slot_scalars_sha256=sha(official/'slot_scalars.csv'),official_source_selection_sha256=sha(official/'SOURCE_SELECTION.csv'))
    elif (out/'new_official').exists():
        # Keep a prior derived release as history but remove its official path
        # when the current complete-cohort gate no longer passes.
        archived=out/'invalidated_official'/str(time.time_ns())
        archived.parent.mkdir(parents=True,exist_ok=True)
        (out/'new_official').rename(archived)
        previous=out/'FAIRNESS_MANIFEST.json'
        if previous.exists():(archived/'PREVIOUS_FAIRNESS_MANIFEST.json').write_bytes(previous.read_bytes())
        write_json(archived/'INVALIDATED.json',{'reason':'Current full-cohort adoption gate failed or became pending','status_counts':result_manifest['status_counts']})
        result_manifest['prior_derived_official_archived']=portable(archived,out)
    write_json(out/'FAIRNESS_MANIFEST.json',result_manifest)
    print(json.dumps({k:result_manifest[k] for k in ('status','adoption_ready','verified_complete_pools','verified_complete_members','status_counts')},indent=2))
    if a.require_complete and not ready:raise SystemExit(2)


if __name__=='__main__':main()
