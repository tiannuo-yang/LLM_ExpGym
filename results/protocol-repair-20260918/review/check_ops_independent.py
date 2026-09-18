#!/usr/bin/env python3
"""Offline queue compile and mocked controller/release tests; never model calls."""
import collections, contextlib, csv, hashlib, importlib.util, io, json, pathlib, subprocess, sys, tempfile
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
OPS=ROOT/'operations'
OUT=ROOT/'review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j))
build_path=OPS/'build_hpo_queues.py';run_path=OPS/'run_hpo_queues.py'
before={str(p.relative_to(ROOT)):sha(p) for p in [build_path,run_path]}
b=load('ops_build',build_path);s=load('ops_run',run_path)
rows=list(csv.DictReader((b.PLANNING/'hpo_rerun_slots.csv').open()));configs=json.loads((b.PLANNING/'hpo_n4_original_configs.json').read_text())
assert len(rows)==97
assert collections.Counter(b.ALIASES[r['model']] for r in rows)==b.EXPECTED
real_endpoints={a:b.endpoint(a) for a in b.EXPECTED}
assert real_endpoints['gemini']=='https://openrouter.ai/api/v1'
assert real_endpoints['gpt']=='http://127.0.0.1:8080/v1'
for alias in set(real_endpoints)-{'gemini','gpt'}:assert real_endpoints[alias].startswith('http://')
compiler_output=io.StringIO();job_total=0;bindings=[]
with tempfile.TemporaryDirectory(prefix='hpo-ops-independent-') as tmp:
 t=pathlib.Path(tmp);b.OUT=t/'operations';b.ROOT=t;b.endpoint=lambda alias:real_endpoints[alias]
 b.OUT.mkdir();
 with patch.object(sys,'argv',[str(build_path),'--compile']),contextlib.redirect_stdout(compiler_output):b.main()
 queue_root=getattr(b,'QUEUES',None)
 # Locate only fixture plans; output-root paths contain no executed artifacts.
 plans=list(t.rglob('queue-plan.json'));assert len(plans)==len(b.EXPECTED)
 for pp in plans:
  plan=json.loads(pp.read_text());binding=json.loads((pp.parent/'BINDINGS.json').read_text())
  assert sha(pp)==binding['plan_sha256']
  assert binding['source_tree_sha256']==plan['source_tree_sha256']
  assert binding['automatic_score_based_reruns'] is False
  job_total+=len(plan['jobs'])
  for job in plan['jobs']:
   sid=job['stage'].removeprefix('repair-');old=configs[sid];args=job['args'];model=next(r['model'] for r in rows if r['slot_id']==sid);alias=b.ALIASES[model]
   for key in ['seed','agents','temperature','max_tokens','top_p','top_k','reasoning_effort','chat_template_kwargs','max_context_tokens','max_steps','max_evals','cost_regime','tuning_task','strategies','tool_protocol','tuning_final_policy','max_protocol_retries','request_timeout','max_retries','retry_base_seconds','retry_max_seconds']:
    assert args.get(key)==old.get(key),(sid,key,args.get(key),old.get(key))
   assert args['base_url']==real_endpoints[alias]
   if alias=='gemini':assert args['backend']=='openrouter' and args['model']=='google/gemini-3.8-flash'
   else:assert args['backend']==old['backend'] and args['model']==old['model']
   if alias in ('glm','kimi'):assert args['prompt_cache_key'] is None
   if alias in ('qwen','deepseek'):assert args['prompt_cache_key_field']=='cache_salt'
   bindings.append((sid,job['job_id']))
 assert job_total==97 and len(set(sid for sid,_ in bindings))==97
 # Test actual release guard with fully mocked Slurm subprocesses.
 release_cases=[]
 for alias,jobid in s.OWNED_JOBS.items():
  for scenario in ('owned_running','foreign_command','already_terminal'):
   d=t/f'release-{alias}-{scenario}';d.mkdir();calls=[]
   expected=OPS/'serving'/alias
   if alias!='qwen':expected/='replica0'
   expected/='serve.sbatch'
   command=str(expected) if scenario!='foreign_command' else '/foreign/job.sh'
   state='COMPLETED' if scenario=='already_terminal' else 'RUNNING'
   raw=f'JobId={jobid} JobName=protocol-hpo-{alias} UserId={s.getpass.getuser()}(1) Account=k2p Command={command} JobState={state}'
   def fake_run(argv,**kwargs):
    calls.append(argv);return subprocess.CompletedProcess(argv,0,stdout=raw,stderr='')
   rejected=False
   with patch.object(s.subprocess,'run',side_effect=fake_run):
    try:s.release_service(alias,d)
    except AssertionError:rejected=True
   scancels=[x for x in calls if x[0]=='scancel']
   assert (len(scancels)==1)==(scenario=='owned_running')
   assert rejected==(scenario=='foreign_command')
   release_cases.append({'model':alias,'scenario':scenario,'scancel_calls':len(scancels),'rejected':rejected})
 for alias in ('gemini','gpt'):
  with patch.object(s.subprocess,'run',side_effect=AssertionError('must not call Slurm')):s.release_service(alias,t)
 # Supervisor schema matches scheduler: queue/jobs/*/completion.json and queue/sessions/*/summary.json.
 supervision=[]
 for case,code,completed,summary_passed in [('success',0,2,True),('worker_failure',1,1,False),('incomplete_even_exit_zero',0,1,True)]:
  d=t/f'supervise-{case}';d.mkdir();rr=t/f'runs-{case}';plan={'output_root':str(rr),'jobs':[{},{}]};binding={'plan_sha256':'fixture','source_tree_sha256':'fixture'}
  for n in range(completed):write(rr/f'queue/jobs/job{n}/completion.json',{'schema':'fixture'})
  write(rr/'queue/sessions/session1/summary.json',{'schema':'expgym.study-queue-summary.v1','passed':summary_passed})
  class P:
   pid=123
   def wait(self):return code
  released=[]
  with patch.object(s,'binding',return_value=(d,binding,plan)),patch.object(s,'environment',return_value={}),patch.object(s.subprocess,'Popen',return_value=P()),patch.object(s,'release_service',side_effect=lambda *args:released.append(args)):
   rc=s.supervise('glm',1)
  assert bool(released)==(case=='success')
  assert (d/'RECOVERY_HOLD.json').exists()==(case!='success')
  assert json.loads((d/'QUEUE_EXIT.json').read_text())['automatic_resampling'] is False
  supervision.append({'case':case,'returncode':rc,'service_released':bool(released),'failed_attempts_retained':True})
for p in [build_path,run_path]:assert sha(p)==before[str(p.relative_to(ROOT))],'Reviewed source changed during check'
report={'status':'PASS','reviewed_file_sha256':before,'matrix_slots':len(rows),'compiled_fixture_jobs':job_total,'same_old_settings_except_documented_provider_and_graph_parser':True,'model_provider_endpoints_checked':real_endpoints,'queue_job_identity_and_plan_hash_bindings_verified':True,'score_based_resampling':False,'owned_job_ids':s.OWNED_JOBS,'release_guard_mock_cases':release_cases,'supervisor_mock_cases':supervision,'model_calls':0,'slurm_mutations':0,'production_queue_launches':0,'scope':'Real production compiler invoked only into a temporary directory. Controller and Slurm operations fully mocked. Final source freeze/EXECUTION_RELEASE remains an actual launch gate.'}
(OUT/'OPS_INDEPENDENT_CHECK.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','compiled_jobs':job_total,'release_cases':len(release_cases),'supervisor_cases':len(supervision),'model_calls':0}))
