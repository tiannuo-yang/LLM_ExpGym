"""Execute ROOT's fixed 30 closed-history pack/local-restore commands, max 2."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent
GO = Path('/lustrefs/users/chufan.shi/codex_space_tn/publication/restart_v5_closed_delivery_candidate_v1/ROOT_PACK_GO.json')
GO_SHA = '3918cf47e1a7742df7769e442a5d09d82c2f0b787151c8662c0145ee67eaf471'
STOP = threading.Event()


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def pin(ref, parse=False):
    p = Path(ref['path'])
    require(p.is_absolute() and '..' not in p.parts and p.resolve() == p and p.is_file(), 'metadata_path')
    before = p.stat()
    raw = p.read_bytes()
    after = p.stat()
    require((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns), 'metadata_changed')
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'] and ('bytes' not in ref or ref['bytes'] == len(raw)), 'metadata_pin')
    return json.loads(raw) if parse else {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write_new(p, value):
    raw = encoded(value)
    with p.open('xb') as stream:
        stream.write(raw)
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def observed(p):
    raw = p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def preflight():
    go = pin({'path':str(GO),'sha256':GO_SHA}, True)
    require(go['approved'] is True and go['issuer']=='ROOT' and go['action']=='pack_and_local_restore_exact_30_batches'
            and go['output_root']==str(ROOT) and go['max_parallel_batches']==2 and go['python']=='/usr/bin/python3'
            and len(go['secret_files'])==3 and go['publication_authorized'] is False and go['network_authorized'] is False, 'go_scope')
    refs = [{'path':str(GO),'sha256':GO_SHA},go['prepared_ref'],go['scan_receipt_ref']] + go['tool_refs']
    prepared, receipt = [pin(go[k],True) for k in ('prepared_ref','scan_receipt_ref')]
    refs += prepared['metadata_refs']
    for ref in refs:
        pin(ref)
    require(receipt['all_closed_history_batches_passed'] is True and receipt['metadata_after_unchanged'] is True
            and receipt['batch_count']==30 and receipt['file_count']==47083 and receipt['original_bytes']==906655448, 'scan_totals')
    reports = {b['batch_id']:b for b in receipt['batches']}
    require(len(reports)==len(receipt['batches'])==len(prepared['batches'])==30, 'batch_counts')
    targets, sources, total, batches = set(),set(),0,[]
    for batch in prepared['batches']:
        report = reports[batch['batch_id']]
        require(report['passed'] is True and report['exit_code']==0 and report['rule'] is None, 'original_scan_failed')
        for ref in [batch['candidate_ref'],batch['spec_ref'],*report['reports'].values()]:
            pin(ref)
            refs.append(ref)
        spec = pin(batch['spec_ref'],True)
        scan = pin(report['reports']['manifest.json'],True)
        lock = pin(report['reports']['lock.json'],True)
        status = pin(report['reports']['validator_status.json'],True)
        require(spec['approved'] is True and spec['require_secret_sources'] is True and spec==lock, 'approved_spec_lock_mismatch')
        require(scan['safe_to_stage'] is True and scan['findings']==scan['advisories']==[] and scan['secret_sources_checked']==3
                and scan['validator_sha256']==go['tool_refs'][-1]['sha256'] and scan['all_required_stages_present'] is True
                and scan['spec_canonical_sha256']==hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()
                and status['safe_to_stage'] is True and status['findings']==0, 'original_scan_binding')
        expected=[]
        for item in spec['artifacts']:
            require(item['kind']=='sealed_file' and item['sealed'] is True and len(item['files'])==1, 'exact_sealed_file_scope')
            row=item['files'][0]
            require(item['source']==item['target'] and row['path']==Path(item['source']).name
                    and item['anchor']=={'path':row['path'],'sha256':row['sha256']}, 'original_mapping')
            expected.append({'artifact_id':item['id'],'source':item['source'],'target':item['target'],
                             'path':row['path'],'bytes':row['bytes'],'sha256':row['sha256']})
        require(expected==scan['files'] and len(expected)==batch['expected_files']==status['files']
                and sum(r['bytes'] for r in expected)==scan['total_bytes'], 'full_batch_mapping')
        for row in expected:
            require(row['target'] not in targets and row['source'] not in sources, 'duplicate_global_original')
            targets.add(row['target']); sources.add(row['source']); total+=row['bytes']
        batches.append({**batch,'original_scan_ref':report['reports']['manifest.json'],'rows':expected})
    require(len(targets)==go['expected_files']==47083 and total==go['expected_bytes']==906655448, 'complete_union')
    require(len({b['batch_id'].split('__batch_')[0] for b in batches})==9, 'nine_scopes')
    require(not (ROOT/'STARTED.json').exists(), 'no_operator_retry_or_resume')
    return go,batches,refs


def invoke(argv, stage, work):
    began=utc(); clock=time.perf_counter()
    env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(ROOT/'scratch'))
    with (work/(stage+'.stdout.json')).open('xb') as out, (work/(stage+'.stderr.log')).open('xb') as err:
        child=subprocess.Popen(argv,stdout=out,stderr=err,stdin=subprocess.DEVNULL,env=env)
        write_new(work/(stage+'.started.json'), {'pid':child.pid,'started_utc':began,'stage':stage,
            'core_dump_limit':list(resource.getrlimit(resource.RLIMIT_CORE)), 'argv':argv})
        code=child.wait()
    result={'stage':stage,'exit_code':code,'pid':child.pid,'started_utc':began,'finished_utc':utc(),
            'elapsed_seconds':time.perf_counter()-clock,'wait_returned':True,
            'stdout_ref':observed(work/(stage+'.stdout.json')),'stderr_ref':observed(work/(stage+'.stderr.log'))}
    write_new(work/(stage+'.exit.json'),result)
    if code:
        STOP.set()
    require(code==0, stage+'_nonzero_exit')
    body=json.loads((work/(stage+'.stdout.json')).read_bytes())
    require(body.get('passed') is True and body.get('publication_performed') is False, stage+'_not_passed')
    return body,result


def batch_run(go,batch,common):
    work=ROOT/'batches'/batch['batch_id']; work.mkdir(mode=0o700)
    result={'batch_id':batch['batch_id'],'spec_ref':batch['spec_ref'],'original_scan_ref':batch['original_scan_ref'],
            'started_utc':utc(),'passed':False,'publication_performed':False,'remote_restore_performed':False}
    try:
        for ref in go['tool_refs']+[batch['spec_ref']]:
            pin(ref)
        require(resource.getrlimit(resource.RLIMIT_CORE)==(0,0),'core_limit')
        secret_args=[word for p in go['secret_files'] for word in ('--secret-file',p)]
        packed,pack_exit=invoke([go['python'],'-B',go['tool_refs'][0]['path'],'--manifest',batch['spec_ref']['path'],
            '--manifest-sha256',batch['spec_ref']['sha256'],'--workspace',go['workspace'],'--output-dir',str(work/'bundle'),
            *secret_args],'pack',work)
        result['pack_exit']=pack_exit
        require(packed['source_unchanged'] is True and packed['file_count']==len(batch['rows'])
                and packed['original_bytes']==sum(r['bytes'] for r in batch['rows']), 'pack_counts')
        index_path=work/'bundle/payload/INDEX.json'
        index=pin({'path':str(index_path),'sha256':packed['index_sha256']},True)
        require(index['additive_scan_advisories']==[] and index['limits']=={'compressed_bytes':48*1024**2,
            'expanded_bytes':256*1024**2,'member_bytes':100*1024**2,'files_per_shard':256}, 'default_limits_or_advisory')
        restored,restore_exit=invoke([go['python'],'-B',go['tool_refs'][2]['path'],'--index',str(index_path),
            '--sha256',packed['index_sha256'],'--output-dir',str(work/'restore'),*secret_args],'restore',work)
        result['restore_exit']=restore_exit
        require(restored['byte_exact_full_path_set'] is True and restored['independent_single_shard'] is False
                and restored['file_count']==len(batch['rows']) and restored['original_bytes']==packed['original_bytes']
                and restored['known_secret_sources_checked']==3, 'restore_counts')
        expected=sorted([{'path':r['target'],'bytes':r['bytes'],'sha256':r['sha256']} for r in batch['rows']],key=lambda r:r['path'])
        payload=work/'restore/payload'
        require(common.tree(payload)=={r['path'] for r in expected}, 'restored_complete_path_set')
        for row in expected:
            require(common.stream_hash(payload/row['path'])==(row['bytes'],row['sha256'])
                    and common.stream_hash(Path(go['workspace'])/row['path'])==(row['bytes'],row['sha256']), 'whole_original_or_restored_mismatch')
        for wrapper,binding,expected_sha in [(work/'bundle',{'kind':'bundle','index_sha256':packed['index_sha256']},packed['completion_sha256']),
             (work/'restore',{'kind':'restored-originals','input_sha256':packed['index_sha256'],'single_archive':False},restored['completion_sha256'])]:
            require(common.verify_completion(wrapper,binding)==expected_sha, 'complete_marker_mismatch')
        rows_ref=write_new(work/'WHOLE_FILE_COMPARISON.json',{'rows':expected,'all_source_and_restored_bytes_sha_match':True,
             'full_restored_path_set_equal':True,'posix_metadata_preserved':False})
        result.update(passed=True,file_count=len(expected),original_bytes=packed['original_bytes'],shards=packed['shards'],
            compressed_bytes=packed['compressed_bytes'],index_ref=observed(index_path),
            pack_complete_ref=observed(work/'bundle/COMPLETE.json'),restore_complete_ref=observed(work/'restore/COMPLETE.json'),
            whole_file_comparison_ref=rows_ref,whole_originals_and_restored_verified=True)
    except Exception as error:
        STOP.set()
        result.update(error_type=type(error).__name__,rule=str(error) if isinstance(error,ValueError) else 'bounded_batch_failed',
                      preserved_failed_outputs=True)
    result['finished_utc']=utc()
    write_new(work/'RESULT.json',result)
    print(json.dumps({k:result[k] for k in ('batch_id','passed','finished_utc')},sort_keys=True),flush=True)
    return result


def main():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    go,batches,refs=preflight()
    for name in ('batches','scratch'):
        (ROOT/name).mkdir(mode=0o700)
    common_path=go['tool_refs'][1]['path']
    spec=importlib.util.spec_from_file_location('closed_delivery_frozen_common',common_path)
    common=importlib.util.module_from_spec(spec); spec.loader.exec_module(common)
    # No load_secrets call in the operator; only exact frozen child CLI calls.
    write_new(ROOT/'PREFLIGHT.json',{'passed':True,'bound_metadata_refs':refs,'file_count':47083,'original_bytes':906655448,
        'batch_count':30,'known_secret_paths_from_go_only':True,'secret_content_read_by_operator':False,
        'operator_ref':observed(Path(__file__).resolve()),'original_content_read_during_preflight':False})
    write_new(ROOT/'STARTED.json',{'pid':os.getpid(),'started_utc':utc(),'go_ref':{'path':str(GO),'sha256':GO_SHA},
        'max_parallel_batches':2,'core_dump_limit':0,'python':sys.version,'publication_performed':False})
    results=[]; next_index=0
    with ThreadPoolExecutor(max_workers=2) as executor:
        active={}
        while active or (next_index<len(batches) and not STOP.is_set()):
            while len(active)<2 and next_index<len(batches) and not STOP.is_set():
                batch=batches[next_index]; next_index+=1
                active[executor.submit(batch_run,go,batch,common)]=batch['batch_id']
            if not active:
                break
            done,_=wait(active,timeout=60,return_when=FIRST_COMPLETED)
            for future in done:
                active.pop(future); results.append(future.result())
            if not done:
                print(json.dumps({'progress':True,'finished_batches':len(results),'active_batches':list(active.values()),
                                  'stop_new':STOP.is_set(),'utc':utc()}),flush=True)
    metadata_unchanged=True
    try:
        for ref in refs:
            pin(ref)
    except Exception:
        metadata_unchanged=False
    summary={'schema_version':'closed-history-local-delivery-operator-v1','finished_utc':utc(),
        'passed':len(results)==30 and all(r['passed'] for r in results) and metadata_unchanged,
        'batches':results,'finished_batches':len(results),'unstarted_batch_ids':[b['batch_id'] for b in batches[next_index:]],
        'metadata_after_unchanged':metadata_unchanged,'local_workers':0,'stop_new_join_policy':True,
        'file_count':sum(r.get('file_count',0) for r in results),'original_bytes':sum(r.get('original_bytes',0) for r in results),
        'compressed_bytes':sum(r.get('compressed_bytes',0) for r in results),'shards':sum(r.get('shards',0) for r in results),
        'whole_restored_path_bytes_sha_verified':all(r['passed'] for r in results),'posix_metadata_preserved':False,
        'publication_performed':False,'remote_restore_performed':False,'full_project_complete':False}
    ref=write_new(ROOT/'SUMMARY.json',summary)
    print(json.dumps({'passed':summary['passed'],'finished_batches':len(results),'summary_ref':ref}),flush=True)
    return 0 if summary['passed'] else 2


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'passed':False,'stage':'operator','error_type':type(error).__name__,'rule':'operator_failed_no_implicit_retry'}),flush=True)
        raise SystemExit(2)
