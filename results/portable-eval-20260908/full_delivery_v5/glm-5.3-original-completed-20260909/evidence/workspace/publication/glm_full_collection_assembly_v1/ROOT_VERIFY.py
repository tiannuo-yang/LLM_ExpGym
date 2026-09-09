from pathlib import Path
import json, hashlib, stat
from datetime import datetime,timezone
W=Path('/lustrefs/users/chufan.shi/codex_space_tn'); P=W/'publication'; H=P/'glm_full_collection_assembly_v1'; D=H/'payload'
refs={}
def read(p,sha=None,parse=True):
 p=Path(p); assert p.resolve()==p; s=p.stat(); assert stat.S_ISREG(s.st_mode) and s.st_size<100*1024*1024
 b=p.read_bytes(); t=p.stat(); assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns)
 r={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if sha:assert r['sha256']==sha
 if str(p) in refs:assert refs[str(p)]==r
 refs[str(p)]=r; return (json.loads(b) if parse else b),r
sel,selref=read(H/'ROOT_SELECTION.json','24d92d89090191de7ff857b55fc70a15166ec4c0195dd584d4e121c6b0486d4b')
go,goref=read(H/'ROOT_ASSEMBLY_GO.json','fee5f95e3fadded369a8e3e97bd4386b5a93ac5c33f84dd7278dbc5120ffd20c')
receipt,rref=read(D/'ASSEMBLY_RECEIPT.json','3e00fdd4aff5b33215595d932997c86b2c68c296be0bf76651c9c9a4ef5abe23')
release,lref=read(D/'RELEASE_FILES.json','f30444a1ac33c76b2f812018ca8b4be8c4813abc66924811c8d5c1a1a6bed65c')
collection,cref=read(D/'collection/INDEX.json','9d4433461c3cf0a3017220003c2d70b5085e715c5db82303449d57e48c8cca09')
assert receipt['passed'] is True and receipt['source_and_copied_bundle_bytes_sha_equal'] is True and receipt['global_original_paths_unique'] is True
assert [receipt[k] for k in ('bundle_count','file_count','original_bytes')]==[37,71634,3467116893]
for k in ('publication_performed','remote_restore_performed','full_project_complete'):assert receipt[k] is False
for k in ('original_execution_complete','original_score_complete'):assert receipt[k] is True
assert receipt['new_pack_or_restore_calls']==receipt['private_key_reads']==0
assert collection['bundle_count']==len(collection['bundles'])==37 and collection['file_count']==71634 and collection['original_bytes']==3467116893
assert receipt['collection_index_sha256']==cref['sha256'] and receipt['release_files_sha256']==lref['sha256']
for r in receipt['input_refs']:read(r['path'],r['sha256'])
assert release['excludes_only']==['RELEASE_FILES.json','ASSEMBLY_RECEIPT.json']
rows=release['files']; assert len(rows)==receipt['release_payload_files']==693
names={r['path'] for r in rows}; assert len(names)==693
actual={p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file()}; assert actual==names|{'RELEASE_FILES.json','ASSEMBLY_RECEIPT.json'}
assert not any(p.is_symlink() for p in D.rglob('*'))
for row in rows:
 _,ref=read(D/row['path'],row['sha256'],False); assert ref['bytes']==row['bytes']
selected={r['bundle_id']:r for r in sel['bundles']}; original_rows={}; n_shards=0; compressed=0
for bundle in collection['bundles']:
 bid=bundle['bundle_id']; chosen=selected[bid]
 assert bundle['index']==bid+'/payload/INDEX.json' and bundle['sha256']==chosen['index_ref']['sha256']
 assert (bundle['file_count'],bundle['original_bytes'])==(chosen['file_count'],chosen['original_bytes'])
 index,_=read(D/'collection'/bundle['index'],bundle['sha256']); members=[]
 for shard in index['shards']:
  page,_=read(D/'collection'/bid/'payload'/shard['index'],shard['index_sha256']);members+=page['files']; n_shards+=1;compressed+=shard['bytes']
 assert len(members)==bundle['file_count'] and sum(r['bytes'] for r in members)==bundle['original_bytes']
 for row in members:assert row['path'] not in original_rows; original_rows[row['path']]=row
 for path in sorted(p for p in names if p.startswith('collection/'+bid+'/')):
  relative=path[len('collection/'+bid+'/'):]; _,source=read(Path(chosen['bundle_root'])/relative,parse=False); copied=refs[str(D/path)]
  assert (source['bytes'],source['sha256'])==(copied['bytes'],copied['sha256'])
raw,_=read(P/'glm_formal_original_scope_candidate_v1/candidate/inventory.json','78610fabac42cf3606dca00a19a3148647eb9eaa413843658bc38f504ec47489')
controls,_=read(W/'portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/glm_public_controls_subset_v1/inventory.json','3c321f8bbecba16cb3570bd6be04ccdc3956fdf857ed8dbb669becdd9a66726a')
expected={r['path']:{k:r[k] for k in ('path','bytes','sha256')} for r in raw['files']+controls['files']}
assert len(expected)==71634 and original_rows==expected
assert (n_shards,compressed)==(288,772603212)
for name,pin in receipt['tool_pins'].items():
 _,a=read(P/name,pin,False); _,b=read(D/'tools/publication'/name,pin,False);assert a['bytes']==b['bytes']
for p,ref in list(refs.items()):read(p,ref['sha256'],False)
proof=dict(schema='root-glm-37-bundle-local-assembly-verification-v1',issuer='ROOT',passed=True,verified_utc=datetime.now(timezone.utc).isoformat(),selection_ref=selref,go_ref=goref,assembly_receipt_ref=rref,release_files_ref=lref,collection_index_ref=cref,actual_assembly_process=dict(session_id=82096,start_chunk='d6fd81',exit_chunk='fd6c28',exit_code=0),bundle_count=37,original_file_count=71634,original_bytes=3467116893,archive_count=288,compressed_bytes=772603212,payload_files=695,payload_total_bytes=sum(refs[str(D/p)]['bytes'] for p in actual),maximum_payload_file_bytes=max(refs[str(D/p)]['bytes'] for p in actual),all_release_file_bytes_sha_and_exact_tree_equal=True,all_original_and_copied_bundle_bytes_equal=True,global_member_union_equals_original_raw_and_controls_scope=True,all_five_restore_tools_exact=True,metadata_and_payload_refs_rechecked=len(refs),new_pack_restore_or_model_calls=0,private_key_reads=0,publication_performed=False,remote_restore_performed=False,analysis_replay_performed=False,original_execution_complete=True,original_score_complete=True,full_project_complete=False)
print(json.dumps(proof,ensure_ascii=False,allow_nan=False))
