from pathlib import Path
import json, hashlib, os, stat
from datetime import datetime, timezone
W=Path('/lustrefs/users/chufan.shi/codex_space_tn'); P=W/'publication'; R=P/'k3_formal_original_local_delivery_v2'
refs={}
keys=[W/'portable_eval_20260908/serving/phase_candidates'/a/'runs'/b/c/'private/router_api_key' for a,b,c in [('dual_glm_v1','1203652','glm_formal'),('dual_k3_v1','1203653','k3_formal'),('gumbel_midpoint_v3','1203577','k3_formal')]]
key_ids=set()
for p in keys:
 s=p.lstat(); assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600
 key_ids.add((s.st_dev,s.st_ino))
def sig(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink)
def read(p, expected=None, parse=True):
 p=Path(p); assert p.is_absolute() and p.resolve()==p and p not in keys
 s=p.lstat(); assert stat.S_ISREG(s.st_mode) and (s.st_dev,s.st_ino) not in key_ids and s.st_size<=100*1024*1024
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:
  assert sig(os.fstat(f.fileno()))==sig(s); b=f.read(); assert sig(os.fstat(f.fileno()))==sig(s)
 assert sig(p.lstat())==sig(s)
 ref={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if expected:
  assert all(ref[k]==expected[k] for k in ('path','sha256'))
  if 'bytes' in expected:assert ref['bytes']==expected['bytes']
 if str(p) in refs:assert refs[str(p)]==ref
 refs[str(p)]=ref
 return (json.loads(b) if parse else b),ref
def bound(r):return read(r['path'],r)[0]
def enc(d):return (json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()
def completion(rows,binding):
 return dict(schema='completed-directory-v1',complete=True,payload='payload',binding=binding,file_count=len(rows),bytes=sum(r['bytes'] for r in rows),inventory_sha256=hashlib.sha256(b''.join(enc(r) for r in rows)).hexdigest())
def tree(root):
 out=set()
 for directory,dirs,files in os.walk(root,followlinks=False):
  for name in dirs+files:assert not (Path(directory)/name).is_symlink()
  for name in files:out.add((Path(directory)/name).relative_to(root).as_posix())
 return out
summary,sref=read(R/'SUMMARY.json'); pre,pref=read(R/'PREFLIGHT.json'); start,startref=read(R/'STARTED.json')
assert summary['schema_version']=='k3-original-local-delivery-operator-v2'
for k in ('passed','metadata_after_unchanged','whole_final_source_restore_path_bytes_sha_complete','all_started_children_reaped'):assert summary[k] is True
for k in ('publication_performed','network_performed','remote_restore_performed','implicit_retry_performed','original_execution_complete','original_score_complete','full_project_complete'):assert summary[k] is False
assert summary['local_workers']==0 and summary['unresolved_started_pids']==summary['unstarted_batch_ids']==[]
assert [summary[k] for k in ('finished_batches','file_count','original_bytes','compressed_bytes','shards')]==[33,64188,1268512973,248634906,257]
assert start['operator_sha256']=='cc1b646b46d258d3071e9fe94bfe849683500beafeca68bca7fbbc56c14ccb14' and start['pid']==1211435 and not Path('/proc/1211435').exists()
assert pre['passed'] is True and pre['helper_root_rebound_to']==str(R)
assert bound(pre['go_ref'])['driver_sha256']==start['operator_sha256']
assert pre['go_ref']['sha256']=='2ae2a5220e35a347d5bd3b4f09fab7daef5f28f2646536f727913075330123db'
for r in pre['metadata_refs']:read(r['path'],r,False)
scope,scoperef=read(P/'k3_formal_original_scope_candidate_v1/candidate/inventory.json',{'path':str(P/'k3_formal_original_scope_candidate_v1/candidate/inventory.json'),'sha256':'8877bf050b9ecea2fc3c06c421916bd1c039fb161cf70c8bf5d6cbfe2b681281'})
expected={r['path']:r for r in scope['files']}; assert len(expected)==len(scope['files'])==64188
children={(x['work'],x['stage']):x for x in summary['children']}; assert len(children)==len(summary['children'])==66
for child in children.values():
 assert child['confirmed_reaped'] is True and child['closure_evidence']=='wait' and child['exit_code']==0 and child['failure_layers']==[] and child['wait_attempts']==1 and child['wait_had_exception'] is False
 assert not Path('/proc',str(child['pid'])).exists()
seen={}; batches=[]; selection=[]
for n,b in enumerate(summary['batches'],1):
 bid='batch-%06d'%n; d=R/'batches'/bid; assert b['batch_id']==bid and b['passed'] is True and b['whole_originals_and_restored_verified'] is True
 assert b['file_count']==(2000 if n<33 else 188)
 result,resultref=read(d/'RESULT.json'); assert result=={k:v for k,v in b.items() if k!='retained_child_exit_refs'}
 whole=bound(b['whole_file_comparison_ref']); assert whole['all_source_and_restored_bytes_sha_match'] is True and whole['full_restored_path_set_equal'] is True
 rows=whole['rows']; assert rows==sorted(rows,key=lambda x:x['path']) and len(rows)==b['file_count']
 assert sum(x['bytes'] for x in rows)==b['original_bytes']
 for row in rows:assert row['path'] not in seen and expected[row['path']]==row; seen[row['path']]=row
 spec=bound(b['spec_ref']); scan=bound(b['original_scan_ref'])
 assert spec['approved'] is True and spec['candidate'] is False
 assert scan['findings']==scan['advisories']==[] and scan['safe_to_stage'] is True
 assert rows==[{'path':x['target'],'bytes':x['bytes'],'sha256':x['sha256']} for x in scan['files']]
 index=bound(b['index_ref']); pack_complete=bound(b['pack_complete_ref']); restore_complete=bound(b['restore_complete_ref'])
 assert b['index_ref']['path']==str(d/'bundle/payload/INDEX.json') and b['pack_complete_ref']['path']==str(d/'bundle/COMPLETE.json')
 assert b['restore_complete_ref']['path']==str(d/'restore/COMPLETE.json')
 assert restore_complete==completion(rows,{'kind':'restored-originals','input_sha256':b['index_ref']['sha256'],'single_archive':False})
 assert index['file_count']==b['file_count'] and index['original_bytes']==b['original_bytes'] and len(index['shards'])==b['shards']
 members=[]; names={'INDEX.json','SOURCE_SCAN.json'}; compressed=0
 for i,sh in enumerate(index['shards'],1):
  assert sh['index']=='indexes/part-%06d.json'%i and sh['archive']=='shards/part-%06d.tar.gz'%i
  page,_=read(d/'bundle/payload'/sh['index'],{'path':str(d/'bundle/payload'/sh['index']),'bytes':sh['index_bytes'],'sha256':sh['index_sha256']})
  members+=page['files']; names.update((sh['index'],sh['archive']))
  _,ar=read(d/'bundle/payload'/sh['archive'],parse=False)
  assert ar['bytes']==sh['bytes'] and ar['sha256']==sh['sha256']; compressed+=ar['bytes']
 assert members==rows and compressed==b['compressed_bytes']
 payload_rows=[]
 for name in sorted(names):
  _,rr=read(d/'bundle/payload'/name,parse=False); payload_rows.append({'path':name,'bytes':rr['bytes'],'sha256':rr['sha256']})
 assert pack_complete==completion(payload_rows,{'kind':'bundle','index_sha256':b['index_ref']['sha256']})
 assert tree(d/'bundle')=={'COMPLETE.json'}|{'payload/'+x for x in names}
 exitrefs=[]
 for stage in ('pack','restore'):
  ex,exref=read(d/(stage+'.exit.json')); st,stref=read(d/(stage+'.started.json')); child=children[(str(d),stage)]
  assert ex==b[stage+'_exit'] and ex['pid']==st['pid']==child['pid'] and ex['stage']==st['stage']==stage
  assert ex['exit_code']==0 and ex['wait_returned'] is True and ex['confirmed_reaped'] is True and ex['failure_layers']==[]
  out=bound(ex['stdout_ref']); _,err=read(ex['stderr_ref']['path'],ex['stderr_ref'],False)
  assert err['bytes']==0 and out['passed'] is True and out['publication_performed'] is False and out['file_count']==b['file_count'] and out['original_bytes']==b['original_bytes']
  if stage=='pack':assert out['index_sha256']==b['index_ref']['sha256'] and out['source_manifest_sha256']==b['spec_ref']['sha256'] and out['source_unchanged'] is True
  else:assert out['index_or_archive_sha256']==b['index_ref']['sha256'] and out['byte_exact_full_path_set'] is True and out['known_secret_sources_checked']==3
  assert out['completion_sha256']==b[stage+'_complete_ref']['sha256'];exitrefs.append(exref)
 assert b['retained_child_exit_refs']==exitrefs
 batches.append(dict(batch_id=bid,result_ref=resultref,local_proof_ref=b['whole_file_comparison_ref'],exit_refs=exitrefs,index_ref=b['index_ref'],complete_ref=b['pack_complete_ref'],restore_complete_ref=b['restore_complete_ref'],file_count=b['file_count'],original_bytes=b['original_bytes']))
 selection.append(dict(bundle_id=bid,category='original-node-failure',bundle_root=str(d/'bundle'),index_ref=b['index_ref'],complete_ref=b['pack_complete_ref'],file_count=b['file_count'],original_bytes=b['original_bytes'],local_proof_ref=b['whole_file_comparison_ref'],local_verification=dict(pack_exit_code=0,restore_exit_code=0,complete_original_and_restored_path_bytes_sha_match=True,all_started_children_reaped=True)))
assert seen==expected
for p,r in list(refs.items()):read(p,r,False)
proof=dict(schema='root-k3-original-local-delivery-metadata-acceptance-v1',issuer='ROOT',passed=True,verified_utc=datetime.now(timezone.utc).isoformat(),summary_ref=sref,preflight_ref=pref,start_ref=startref,scope_ref=scoperef,actual_operator_exit=dict(session_id=45418,exit_code=0,tool_chunk_id='f55554',observed_utc='2026-09-09T17:28:02Z'),finished_utc=summary['finished_utc'],file_count=64188,original_bytes=1268512973,batch_count=33,shards=257,compressed_bytes=248634906,exact_source_comparison_member_scope_equal=True,all_66_actual_child_exit_receipts_wait_confirmed=True,all_67_recorded_pids_absent=True,all_bundle_compressed_bytes_and_exact_trees_checked=True,all_restore_completion_records_bound_to_exact_original_inventory=True,frozen_root_owned_operator_global_original_and_restored_bytes_check_passed=True,root_additional_uncompressed_payload_reread_performed=False,metadata_refs_second_read_equal=True,metadata_and_archive_refs_checked=len(refs),private_key_values_read_or_hashed=False,batches=batches,original_execution_complete=False,original_score_complete=False,remote_restore_performed=False,publication_performed=False,limitations=['ROOT checks all exact bundle bytes, exit receipts, proof rows and fixed source scope. The final full original/restored payload reread is performed by the frozen ROOT-owned operator, not repeated here.','No provider, science completeness, POSIX metadata or remote restore claim.'])
print(json.dumps({'proof':proof,'selection_rows':selection},ensure_ascii=False,allow_nan=False))
