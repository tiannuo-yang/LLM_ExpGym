#!/usr/bin/env python3
"""One exact completed build's metadata repair; no archive/restore mutation."""
import json
from pathlib import Path
import prepare as p
import assemble as a
import build_candidate as b
c = p.c
INDEX_SHA = 'f756064abe54adc4a0fc21d10e9e0ef6d76ac863c3eae325dc58fb5913c413b0'
POOL_FIELDS = ['job_id','classification','guarded_skips','original_status_passed','infra_qualified','performance_qualified','abort_observed','retained_semantic_zero_count','reasons']


def pool_rows_for_csv(rows):
    result = []
    for row in rows:
        values = dict(row)
        if 'retained_semantic_zero_count' not in values:
            c.need(row['classification'] == 'no_execution_evidence_observed', 'missing_launched_zero_count')
            values['retained_semantic_zero_count'] = 'not_applicable_no_execution'
        result.append({field: json.dumps(values[field],ensure_ascii=False) if isinstance(values[field],(list,dict))
                       else 'unknown' if values[field] is None else values[field] for field in POOL_FIELDS})
    return result


def main():
    a.verify_tools(); secrets=c.scanner().load_secrets([p.KEY])
    root=p.BASE/'checks/acceptance_v1'; capsule=p.BASE/'capsule'
    out=c.fresh(p.BASE/'checks/metadata_completion_v1');out.mkdir(mode=0o700)
    def write(path,raw):
        c.scan(raw,path.name,secrets);c.write_new(path,raw)
    full,_=c.load_json(p.BASE/'checks/initial_v2/full_original_inventory.json',b.FULL_SHA,secrets)
    before=c.strict_json((p.BASE/'checks/initial_v2/source_snapshot.json').read_bytes())
    c.need(p.snapshot(full)==before,'original_source_changed')
    strict=[r for r in full if r['target']!=a.CONTROL_TARGET]
    c.verify_completion(capsule/'bundle',{'kind':'bundle','index_sha256':INDEX_SHA},secrets)
    index,_=c.load_json(capsule/'bundle/payload/INDEX.json',INDEX_SHA,secrets)
    pack_receipt,_=c.load_json(root/'pack.stdout.log',secrets=secrets)
    c.need(pack_receipt['passed'] and pack_receipt['index_sha256']==INDEX_SHA,'prior_pack_receipt')
    child_logs=[]
    for name,count in [('assembly_tests',28),('frozen_v2_tests',57)]:
        raw=(root/(name+'.stderr.log')).read_bytes();c.scan(raw,name+'.log',secrets)
        c.need(('Ran %d tests'%count).encode() in raw and b'\nOK\n' in raw,'prior_tests_receipt')
    def restored(name,path,rows,input_sha,single):
        receipt,_=c.load_json(root/(name+'.stdout.log'),secrets=secrets)
        c.need(receipt['passed'] and receipt['index_or_archive_sha256']==input_sha
               and receipt['independent_single_shard'] is single,'prior_restore_receipt')
        marker=c.verify_completion(path,{'kind':'restored-originals','input_sha256':input_sha,'single_archive':single},secrets)
        c.need(marker==receipt['completion_sha256'],'prior_restore_marker')
        child_logs.append({'name':name,'stdout_sha256':c.sha((root/(name+'.stdout.log')).read_bytes())})
        return b.exact_originals(path/'payload',rows)
    strict_check=restored('restore_full',root/'full_restored',strict,INDEX_SHA,False)
    by_path={r['target']:r for r in full};path_to_shard={};shard_checks=[]
    for n,shard in enumerate(index['shards'],1):
        page,_=c.load_json(capsule/'bundle/payload'/shard['index'],shard['index_sha256'],secrets)
        rows=[by_path[r['path']] for r in page['files']]
        for row in rows:
            c.need(row['target'] not in path_to_shard,'duplicate_shard_original')
            path_to_shard[row['target']]='bundle/payload/'+shard['archive']
        check=restored('restore_part_%06d'%n,root/'per_shard'/('part-%06d'%n),rows,shard['sha256'],True)
        shard_checks.append({'archive':shard['archive'],'sha256':shard['sha256'],**check})
    c.need(set(path_to_shard)=={r['target'] for r in strict},'shard_union_incomplete')
    assembled,_=c.load_json(root/'assemble_full.stdout.log',secrets=secrets)
    c.need(assembled['passed'] and assembled['control_sha256']==a.CONTROL_SHA
           and assembled['index_sha256']==INDEX_SHA,'prior_assembly_receipt')
    marker=c.verify_completion(root/'assembled',assembled['binding'],secrets)
    c.need(marker==assembled['completion_sha256'],'prior_assembly_marker')
    a.control_original(capsule/'control_originals'/a.CONTROL_NAME,secrets)
    whole=b.exact_originals(root/'assembled/payload',full)
    c.need(not (root/'assembled/payload'/p.RUN/'execution.json').exists(),'fabricated_execution_json')
    files=[{'original_path':r['target'],'bytes':r['bytes'],'sha256':r['sha256'],
            'download':'control_originals/'+a.CONTROL_NAME if r['target']==a.CONTROL_TARGET else path_to_shard[r['target']],
            'handling':'fixed_manual_prose_original' if r['target']==a.CONTROL_TARGET else 'strict_v2_shard'} for r in full]
    c.need((capsule/'FILES.csv').read_bytes()==b.csv_bytes(['original_path','bytes','sha256','download','handling'],files),'existing_files_csv_changed')
    partial=c.strict_json((p.WORKSPACE/p.PARTIAL/'receipt.json').read_bytes())
    pools=pool_rows_for_csv(partial['rows'])
    c.need(len(pools)==78 and sum(r['retained_semantic_zero_count']=='not_applicable_no_execution' for r in pools)==31,'unstarted_not_zero')
    c.need(sum(r['retained_semantic_zero_count'] for r in pools if r['performance_qualified'] is True)==14,'qualified_semantic_zero_count')
    write(capsule/'POOL_STATUS.csv',b.csv_bytes(POOL_FIELDS,pools))
    transport=c.strict_json((p.WORKSPACE/p.TRANSPORT/'receipt.json').read_bytes())
    fields=['job_id','request_id','generation_id','attempt','will_retry','state','evidence','router_line_1based',
            'payload_sha256','response_sha256','finish_reasons','original_dump','dump_sha256',
            'input_tokens','output_tokens','reasoning_tokens','provider_total_tokens','cache_read_tokens','cache_write_tokens']
    attempts=[]
    for row in transport['attempts']:
        result={field:row.get(field) if row.get(field) is not None else 'unknown' for field in fields[:10]}
        result.update({'finish_reasons':json.dumps(row['finish_reasons']),
                       'original_dump':str(Path(row['dump']['path']).relative_to(p.WORKSPACE)),'dump_sha256':row['dump']['sha256']})
        result.update({field:row['usage'][field] if row['usage'][field] is not None else 'unknown' for field in fields[13:]})
        attempts.append(result)
    c.need(len(attempts)==1532 and sum(r['input_tokens']=='unknown' for r in attempts)==1,'unknown_attempt_not_zero')
    write(capsule/'ATTEMPTS.csv',b.csv_bytes(fields,attempts))
    c.need(p.snapshot(full)==before,'originals_changed_after_metadata_recheck')
    protected=c.strict_json((p.BASE/'checks/protected_before.json').read_bytes())
    for source,old in protected['files'].items():
        path=c.lexical(p.WORKSPACE/source);size,digest=c.stream_hash(path)
        c.need({'bytes':size,'sha256':digest,'mtime_ns':path.stat().st_mtime_ns}==old,'protected_original_changed')
    public_root=p.WORKSPACE/'portable_publish.pPLtjm8i/repo/results/portable-eval-20260908'
    prefix=str(public_root.relative_to(p.WORKSPACE))+'/'
    c.need({prefix+x for x in c.tree(public_root)}=={x for x in protected['files'] if x.startswith(prefix)},'old_public_set_changed')
    receipt={'schema':'bc-partial-delivery-candidate-acceptance-v1','passed':True,
             'scope':'Bounded CPU lossless delivery candidate; metadata completion after documented CSV development failure, not a successful first build run.',
             'first_build_driver_completed':False,'metadata_recovery_only':True,'original_completed_payloads_modified':False,
             'source_lock_sha256':b.LOCK_SHA,'full_original_inventory_sha256':b.FULL_SHA,'pack':pack_receipt,
             'strict_full_restore':strict_check,'independent_shards':shard_checks,'fixed_control_assembly':assembled,'whole_originals':whole,
             'tests':{'new_assembly':28,'frozen_v2':57},'all_originals_before_after_sha_bytes_mtime_unchanged':True,
             'source_original_files':len(full),'protected_old_files_unchanged':len(protected['files']),
             'already_published_result_files_unchanged':1127,'original_run_files':2173,'original_run_sharded':2172,
             'original_control_separate':1,'raw_attempts':1532,'result_json_files':282,'original_execution_json_absent':True,
             'initial_strict_full_scan_failed_and_retained':True,'strict_scanner_all_originals_passed':False,
             'single_exact_manual_prose_exception':True,'known_secret_sources_checked':len(secrets),
             'csv_unstarted_not_applicable_rows':31,'csv_unknown_attempt_usage_rows':1,
             'new_model_slurm_git_network_calls':0,'publication_performed':False,'publication_go':False,'project_complete':False}
    for path in (out/'ACCEPTANCE.json',root/'ACCEPTANCE.json',capsule/'DELIVERY_ACCEPTANCE.json'):
        write(path,c.encoded(receipt))
    write(out/'VERIFIED_CHILD_LOGS.json',c.encoded(child_logs))
    print(json.dumps({'passed':True,'file_count':len(full),'bytes':whole['bytes'],
                      'acceptance_sha256':c.sha((root/'ACCEPTANCE.json').read_bytes()),'publication_performed':False},indent=2))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'passed':False,'rule':str(exc) if isinstance(exc,c.DeliveryError) else 'metadata_completion_failed','publication_performed':False}));raise SystemExit(1)
