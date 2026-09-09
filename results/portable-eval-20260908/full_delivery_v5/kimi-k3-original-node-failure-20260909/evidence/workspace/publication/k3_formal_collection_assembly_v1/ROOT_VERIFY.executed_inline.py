from pathlib import Path
import json, hashlib, stat
from datetime import datetime,timezone
W=Path('/lustrefs/users/chufan.shi/codex_space_tn'); P=W/'publication'; H=P/'k3_formal_collection_assembly_v1'; D=H/'payload'
refs={}
def read(p,sha=None,parse=True):
 p=Path(p); assert p.resolve()==p; s=p.stat(); assert stat.S_ISREG(s.st_mode) and s.st_size<100*1024*1024
 b=p.read_bytes(); t=p.stat(); assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns)
 r={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if sha:assert r['sha256']==sha
 if str(p) in refs:assert refs[str(p)]==r
 refs[str(p)]=r; return (json.loads(b) if parse else b),r
sel,selref=read(H/'ROOT_SELECTION.json','08223899650c4cb2f668a96ee618f9bc2d3976bf5ac28a0257db3762d61f71e9')
go,goref=read(H/'ROOT_GO.json','8c43169a88de3122336391251ba84da28a2dd8880f427bbd76c3267ccefd03c8')
receipt,rref=read(D/'ASSEMBLY_RECEIPT.json','a6b627972d5102b8805f588b46a90b68e43d0c3a89c02516e6c303f7c5fe0e41')
release,lref=read(D/'RELEASE_FILES.json','f530860764b04b90494fa2e11f79dbab4925f881ba5c77b755418a042e0a7e4b')
collection,cref=read(D/'collection/INDEX.json','a78227369423e71e8c4380e46416b8a4ed88464f3e8a502fe1747e7e703103f5')
assert receipt['passed'] is True and receipt['source_and_copied_bundle_bytes_sha_equal'] is True and receipt['global_original_paths_unique'] is True
assert [receipt[k] for k in ('bundle_count','file_count','original_bytes')]==[34,65105,1521531633]
for k in ('publication_performed','remote_restore_performed','full_project_complete','original_execution_complete','original_score_complete'):assert receipt[k] is False
assert receipt['new_pack_or_restore_calls']==receipt['private_key_reads']==0
assert collection['bundle_count']==len(collection['bundles'])==34 and collection['file_count']==65105 and collection['original_bytes']==1521531633
assert receipt['collection_index_sha256']==cref['sha256'] and receipt['release_files_sha256']==lref['sha256']
for r in receipt['input_refs']:read(r['path'],r['sha256'])
assert release['excludes_only']==['RELEASE_FILES.json','ASSEMBLY_RECEIPT.json']
rows=release['files']; assert len(rows)==receipt['release_payload_files']==630
names={r['path'] for r in rows}; assert len(names)==630
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
raw,_=read(P/'k3_formal_original_scope_candidate_v1/candidate/inventory.json','8877bf050b9ecea2fc3c06c421916bd1c039fb161cf70c8bf5d6cbfe2b681281')
controls,_=read(W/'portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/k3_delivery_controls_sealed_v1/inventory.json','7afbe4dae74e2925dafa19d73170a828a9437d9c08944a704b7ee80395464367')
expected={r['path']:{k:r[k] for k in ('path','bytes','sha256')} for r in raw['files']+controls['files']}
assert len(expected)==65105 and original_rows==expected
assert (n_shards,compressed)==(261,275003805)
for name,pin in receipt['tool_pins'].items():
 _,a=read(P/name,pin,False); _,b=read(D/'tools/publication'/name,pin,False);assert a['bytes']==b['bytes']
for p,ref in list(refs.items()):read(p,ref['sha256'],False)
proof=dict(schema='root-k3-34-bundle-local-assembly-verification-v1',issuer='ROOT',passed=True,verified_utc=datetime.now(timezone.utc).isoformat(),selection_ref=selref,go_ref=goref,assembly_receipt_ref=rref,release_files_ref=lref,collection_index_ref=cref,actual_assembly_process=dict(session_id=72243,start_chunk='9a935b',exit_chunk='b0eb34',exit_code=0),bundle_count=34,original_file_count=65105,original_bytes=1521531633,archive_count=261,compressed_bytes=275003805,payload_files=632,payload_total_bytes=sum(refs[str(D/p)]['bytes'] for p in actual),maximum_payload_file_bytes=max(refs[str(D/p)]['bytes'] for p in actual),all_release_file_bytes_sha_and_exact_tree_equal=True,all_original_and_copied_bundle_bytes_equal=True,global_member_union_equals_original_raw_and_controls_scope=True,all_five_restore_tools_exact=True,metadata_and_payload_refs_rechecked=len(refs),new_pack_restore_or_model_calls=0,private_key_reads=0,publication_performed=False,remote_restore_performed=False,analysis_replay_performed=False,original_execution_complete=False,original_score_complete=False,full_project_complete=False)
print(json.dumps(proof,ensure_ascii=False,allow_nan=False))
