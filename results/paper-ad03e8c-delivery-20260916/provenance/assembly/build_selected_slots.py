#!/usr/bin/env python3
"""Assemble selected slots for exact ad03 report, without rescoring or raw reads.

Only frozen analysis CSVs, lineage and execution metadata are read. Canonical
result paths and historical identities are carried forward; current result
bytes/content hashes are intentionally left to the delivery copy validator.
"""
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

W = Path('/lustrefs/users/chufan.shi/codex_space_tn')
P = W / 'publication/five_model_report_20260911'
R = P / 'results/paper-analysis-20260916'
L = P / 'results/six-models-lineage-20260914'
O = Path(__file__).resolve().parent
COMMIT = 'ad03e8c42ca501016176ee1bc407b38499178506'
INPUTS = {}

def read(path):
    path = Path(path)
    data = path.read_bytes()
    INPUTS[str(path)] = dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    return data

def js(path):
    return json.loads(read(path))

def rows(path):
    return list(csv.DictReader(read(path).decode().splitlines()))

def jsonlines(path):
    return [json.loads(line) for line in read(path).splitlines() if line]

def yes(value):
    return value in (True, 'True', 'true', 1, '1')

COHORTS = {c['id']: c for c in js(L / 'SOURCE_INDEX.json')['cohorts']}
REPLACEMENTS = {
    ('kimi-k3', 'tuning', 'cost_tight'),
    ('glm-5.3', 'tuning', 'cost_tight'),
    ('glm-5.3', 'evidence_audit', 'cost_tight'),
    ('deepseek-v4-flash-0731', 'tuning', 'cost_moderate'),
    ('deepseek-v4-flash-0731', 'tuning', 'cost_tight'),
    ('deepseek-v4-flash-0731', 'evidence_audit', 'cost_moderate'),
    ('deepseek-v4-flash-0731', 'evidence_audit', 'cost_tight'),
    ('deepseek-v4-flash-0731', 'restricted_search', 'cost_moderate'),
    ('gpt-5.6-sol', 'tuning', 'cost_moderate'),
}

def slot_key(r):
    return tuple(r[k] for k in ('model','system','scenario','regime','strategy','item','outer_repeat','order'))

def base(model, scenario, regime, item, seed=2200, order='', strategy='single', cohort='', **kw):
    system = 'expgym' if strategy == 'single' else 'poolact'
    repeat = (int(seed)-2200)//4 if scenario == 'tuning' else 0
    r = dict(model=model, system=system, scenario=scenario, regime=regime,
             strategy=strategy, item=item, outer_repeat=repeat, order=order,
             seed=int(seed), N=1 if system=='expgym' else 4, cohort_id=cohort,
             expected=True, execution_complete=True, score_complete=True,
             status='completed', result_path='', result_sha256='', result_bytes='',
             trace_paths=[], source_job_id='', api_dump_root='', source_metadata='',
             source_row='', native_source_id='', primary_metrics={},
             archive_source_identity=cohort, snapshot_cutoff_utc='', **kw)
    return r

SELECTED = {}
SUPERSEDED = []
def add(r):
    key = slot_key(r)
    if r['system']=='poolact' and (r['model'],r['scenario'],r['regime']) in REPLACEMENTS and '_rerun_' not in r['cohort_id']:
        SUPERSEDED.append(r)
        return
    assert key not in SELECTED, ('duplicate_selected_slot', key)
    SELECTED[key] = r

# Old physical invocation reports carry exact trace/result -> invocation/dump
# links. Kimi's original failed eight are excluded via completed_scored; the
# registered recovery cohort supplies these slots without duplicate selection.
OLD_ARTIFACTS = {}
OLD_POOL_ROWS = []
for cid in ('kimi_original','glm_original'):
    for root_text in COHORTS[cid]['local_raw_roots']:
        root = Path(root_text)
        meta = root / 'execution.json'
        execution = js(meta)
        for record in execution['reports']:
            if record.get('decision',{}).get('classification') not in ('completed_scored','model_no_answer'):
                continue
            iid = record['invocation_id']
            artifacts = record['report'].get('artifacts',[])
            artifact_run_ids={Path(a['path']).relative_to(root).parts[1] for a in artifacts}
            assert len(artifact_run_ids)==1,(root,iid,artifact_run_ids)
            artifact_run_id=next(iter(artifact_run_ids))
            context = dict(source_job_id=iid, api_dump_root=str(root/'dumps'/artifact_run_id/iid),
                           source_metadata=str(meta), native_source_id=root.name)
            for a in artifacts:
                OLD_ARTIFACTS[a['path']] = dict(**context, sha256=a['sha256'])
                path = Path(a['path'])
                if path.name != 'result.json' or '/poolact/' not in str(path):
                    continue
                parts = path.parts
                n = parts.index('poolact')
                scenario, item_path, regime, strategy = parts[n+1:n+5]
                outer = int(parts[n-1].split('_')[1])
                if scenario == 'restricted_search':
                    match = re.fullmatch(r'(phantom_seed\d+)-q(\d+)',item_path)
                    assert match, item_path
                    item = ':'.join(match.groups())
                elif scenario == 'evidence_audit':
                    match = re.fullmatch(r'audit-index(\d+)-doc(\d+)',item_path)
                    assert match,item_path
                    item = 'cc-large:'+match.group(1)
                else:
                    assert item_path.startswith('hpobench_nasbench101_'),item_path
                    item = 'hpobench:nasbench101:'+item_path[-1]
                r=base(COHORTS[cid]['model'],scenario,regime,item,2200+4*outer,strategy=strategy,cohort=cid)
                r.update(context,result_path=str(path),result_sha256=a['sha256'],
                         trace_paths=[x['path'] for x in artifacts if '/agents/agent_' in x['path']])
                OLD_POOL_ROWS.append(r)

def attach_n1(r,path,sha,meta,rownum):
    path = str(path)
    r.update(result_path=path,result_sha256=sha,trace_paths=[path],source_metadata=str(meta),source_row=rownum,
             metric_metadata_path=str(meta),metric_metadata_row=rownum)
    if path in OLD_ARTIFACTS:
        context=OLD_ARTIFACTS[path]
        assert context['sha256']==sha, path
        r.update({k:v for k,v in context.items() if k!='sha256'})
    elif '/invocations/' in path:
        before,after=path.split('/invocations/',1)
        job=after.split('/',1)[0]
        r.update(source_job_id=job,api_dump_root=before+'/invocations/'+job+'/api_dump',native_source_id=Path(before).name)
    else:
        raise AssertionError(('unsupported_n1_path',path))
    add(r)

meta=R/'search/trajectory_metrics.csv'
for i,x in enumerate(rows(meta),1):
    r=base(x['model'],'restricted_search',x['regime'],x['source']+':'+x['question_id'],cohort=x['cohort'])
    r['primary_metrics']={'f1':float(x['score'])}
    attach_n1(r,x['trace_path'],x['trace_sha256'],meta,i)
meta=R/'audit/trace_metrics.csv'
for i,x in enumerate(rows(meta),1):
    order=int(x['order'])
    r=base(x['model'],'evidence_audit',x['budget'],'cc-large:'+x['doc_index'],2200+order,order,cohort=x['source_cohort'])
    r['primary_metrics']={k:float(x[k]) for k in ('label_acc','evidence_acc','joint_acc')}
    r['result_bytes']=int(x['trace_bytes'])
    attach_n1(r,x['trace_path'],x['trace_sha256'],meta,i)
meta=R/'hpo/trajectories.csv'
for i,x in enumerate(rows(meta),1):
    r=base(x['model'],'tuning',x['regime'],x['task'],x['seed'],cohort=x['cohort'])
    r['score_complete']=yes(x['score_complete'])
    r['status']='completed' if r['score_complete'] else 'completed_unscored_normal_missing_configuration'
    r['primary_metrics']={'raw_perf':float(x['final_performance']) if x['final_performance'] else None}
    attach_n1(r,x['trace_path'],x['trace_sha256'],meta,i)
assert len(SELECTED)==2496,len(SELECTED)

for r in OLD_POOL_ROWS:
    add(r)

# Qwen/DeepSeek invocation-normalized CSVs preserve all execution slots; read
# only terminal scalar CSV for strict completeness, not any trace/API payload.
for cid,rel in [('qwen_original','qwen38_eval_20260910/analysis/full_v1'),
                ('deepseek_original','deepseek_flash_eval_20260911/analysis/full_v2')]:
    analysis=W/rel
    terminals={}
    for x in rows(analysis/'raw_terminals.csv'):
        terminals.setdefault(x['execution_id'],[]).append(yes(x['score_complete']))
    root=Path(COHORTS[cid]['local_raw_roots'][0])
    jobs={j['id']:j for j in js(root/'queue/definition.json')['jobs']}
    meta=analysis/'normalized.csv'
    for i,x in enumerate(rows(meta),1):
        if x['system']!='poolact': continue
        j=jobs[x['execution_id']]
        selection=j['identity']['selection']
        if x['scenario']=='evidence_audit':
            item='cc-large:'+str(selection['question_index'])
        elif x['scenario']=='restricted_search':
            match=re.fullmatch(r'(phantom_seed\d+)/q(\d+)',x['item'])
            assert match,x['item']
            item=':'.join(match.groups())
        else:
            item=x['item']
        r=base(x['model'],x['scenario'],x['regime'],item,x['seed'],strategy=x['strategy'],cohort=cid)
        artifact=Path(x['artifact_root'])
        result=artifact/'result'/x['strategy']/'result.json'
        scoreflags=terminals[x['execution_id']]
        assert len(scoreflags)==4,(cid,x['execution_id'],scoreflags)
        r.update(execution_complete=yes(x['execution_complete']),score_complete=all(scoreflags),
                 result_path=str(result),trace_paths=[str(result.parent/'agents'/('agent_'+str(a)+'.json')) for a in range(4)],
                 source_job_id=x['execution_id'],api_dump_root=str(artifact/'api_dump'),
                 source_metadata=str(meta),source_row=i,native_source_id=j['identity']['study_id'])
        add(r)

# GPT and Gemini already have frozen explicit logical slots with source jobs.
# Gemini includes every failed/unstarted slot from the report's original cutoff.
for cid,meta,default_root in [
    ('gpt_original',W/'LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1/analysis_v1/normalized.jsonl',
     W/'LLM_ExpGym_api_studies_20260910/studies/gpt56sol_medium_refmatrix_20260910_v1'),
    ('gemini_snapshot',P/'results/all-models-latest-20260913/provenance/gemini/normalized.jsonl',None),
]:
    for i,x in enumerate(jsonlines(meta),1):
        if x['system']=='expgym' and yes(x['execution_complete']):
            continue # exact reviewed trajectory already present
        root=Path(x.get('source_root') or default_root)
        path=Path(x['planned_result'])
        if not path.is_absolute(): path=root/path
        order=(int(x['seed'])-2200) if x['scenario']=='evidence_audit' and x['system']=='expgym' else ''
        item=('cc-large:'+str(x['question_index'])) if x['scenario']=='evidence_audit' else x['item']
        r=base(x['model'],x['scenario'],x['budget'],item,x['seed'],order,strategy=x['strategy'],cohort=cid)
        job=x.get('source_job_id') or x['job_id']
        r.update(execution_complete=yes(x['execution_complete']),score_complete=yes(x['score_complete']),status=x['queue_status'],
                 result_path=str(path),result_sha256=x.get('result_sha256',''),
                 trace_paths=[str(path)] if x['N']==1 else [str(path.parent/'agents'/('agent_'+str(a)+'.json')) for a in range(4)],
                 source_job_id=job,api_dump_root=str(root/'invocations'/job/'api_dump'),
                 source_metadata=str(meta),source_row=i,native_source_id=x.get('source_id') or x['study_id'],
                 snapshot_cutoff_utc=x.get('snapshot_cutoff_utc',''))
        # A planned path is not evidence that failed/unstarted output exists.
        if not r['execution_complete']:
            r['trace_paths']=[]
        add(r)

meta=P/'results/eval-material-rerun-20260912/pool_status.csv'
for i,x in enumerate(rows(meta),1):
    model=x['model']
    short={'kimi-k3':'kimi','glm-5.3':'glm','deepseek-v4-flash-0731':'deepseek','gpt-5.6-sol':'gpt'}[model]
    cid=short+'_rerun_20260912'
    path=x['result_path'].replace('@study/',str(W/'eval_material_rerun_20260912')+'/')
    result=Path(path)
    assert '/invocations/' in path,path
    before,after=path.split('/invocations/',1)
    job=after.split('/',1)[0]
    r=base(model,x['scenario'],x['regime'],x['item'],x['seed'],strategy=x['strategy'],cohort=cid)
    r.update(execution_complete=x['execution_status']=='completed',score_complete=x['scored_agents']==x['expected_agents'],
             status=x['execution_status'],result_path=path,
             trace_paths=[str(result.parent/'agents'/('agent_'+str(a)+'.json')) for a in range(4)],
             source_job_id=job,api_dump_root=before+'/invocations/'+job+'/api_dump',source_metadata=str(meta),source_row=i,
             native_source_id=x['effective_cohort'])
    add(r)

# Existing Audit pool inventory adds historical byte/hash identities for all
# selected 468 Audit pools and independently checks scenario/source routing.
for x in rows(R/'poolact/coordination/audit_pools.csv'):
    probe=base(x['model'],'evidence_audit',x['regime'],'cc-large:'+x['question_index'],strategy=x['strategy'],cohort=x['cohort_id'])
    r=SELECTED[slot_key(probe)]
    assert r['result_path']==x['result_path'],(r,x['result_path'])
    assert r['cohort_id']==x['cohort_id']
    if r['result_sha256']: assert r['result_sha256']==x['result_sha256']
    r.update(result_sha256=x['result_sha256'],result_bytes=int(x['bytes']))

result=[]
for key,r in sorted(SELECTED.items()):
    r['slot_id']=hashlib.sha256(json.dumps(key,separators=(',',':')).encode()).hexdigest()[:24]
    r['report_commit']=COMMIT
    result.append(r)
assert len(result)==4698,len(result)
assert len({r['slot_id'] for r in result})==4698
assert sum(r['execution_complete'] for r in result)==4682
assert sum(r['score_complete'] for r in result)==4671
assert len(SUPERSEDED)==369,len(SUPERSEDED)
counts={}
template_slots=None
for model in sorted({r['model'] for r in result}):
    rr=[r for r in result if r['model']==model]
    assert len(rr)==783,(model,len(rr))
    counts[model]=dict(planned=len(rr),completed=sum(r['execution_complete'] for r in rr),
                       score_complete=sum(r['score_complete'] for r in rr),
                       completed_by_cohort=dict(Counter(r['cohort_id'] for r in rr if r['execution_complete'])),
                       states=dict(Counter(r['status'] for r in rr)))
    assert sum(r['system']=='expgym' for r in rr)==417
    assert sum(r['system']=='poolact' for r in rr)==366
    scientific_slots={slot_key(r)[1:] for r in rr}
    if template_slots is None:
        template_slots=scientific_slots
    else:
        assert scientific_slots==template_slots,(model,'mismatched_slot_domain',list(scientific_slots-template_slots)[:5],list(template_slots-scientific_slots)[:5])

def export(name,rr):
    (O/(name+'.json')).write_text(json.dumps(rr,ensure_ascii=False,indent=2)+'\n')
    flat=[]
    for r in rr:
        flat.append({k+'_json' if isinstance(v,(list,dict)) else k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(list,dict)) else v for k,v in r.items()})
    with (O/(name+'.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
export('selected_slots',result)
export('superseded_slots',SUPERSEDED)
checks=dict(status='PASS',report_commit=COMMIT,planned=4698,completed=4682,score_complete=4671,
            superseded_original_pools=369,counts=counts,
            inputs=list(INPUTS.values()),read_boundary='frozen CSV/JSON execution metadata only; no result/API payload reads; no score recomputation',
            note='Paths are source provenance references. Noncompleted result_path is planned, not asserted available. Copy stage must bind final portable paths and content identities.')
git_checked=[]
for entry in INPUTS.values():
    path=Path(entry['path'])
    if path.is_relative_to(P):
        rel=path.relative_to(P)
        pinned=subprocess.check_output(['git','-C',str(P),'show',COMMIT+':'+str(rel)])
        assert len(pinned)==entry['bytes'] and hashlib.sha256(pinned).hexdigest()==entry['sha256'],('input_differs_from_ad03',str(rel))
        git_checked.append(str(rel))
checks['git_inputs_equal_ad03']=git_checked
(O/'selected_slots_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k!='inputs'},ensure_ascii=False,indent=2))
