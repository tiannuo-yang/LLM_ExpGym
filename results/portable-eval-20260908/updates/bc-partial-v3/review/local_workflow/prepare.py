#!/usr/bin/env python3
"""Explicit sealed partial-B/C inventory and original-rule security scan only."""
import json
import os
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
WORKSPACE=BASE.parents[1]
SHARD=BASE.parent/'shard_delivery_candidate_v2'
sys.path.insert(0,str(SHARD))
import common as c

KEY=WORKSPACE/'portable_eval_20260908/serving/runs/1203474/private/router_api_key'
RUN='portable_eval_20260908/pilot_runs/k3_bc312_1203474_v3'
PARTIAL='portable_eval_20260908/validation/bc_partial_independent_20260908T1046Z'
TRANSPORT='portable_eval_20260908/validation/bc_partial_transport_20260908T1055Z'
ROOT_DRAIN='portable_eval_20260908/validation/bc_partial_root_drain_20260908T1045Z.json'
PINS={
 PARTIAL+'/receipt.json':'c53de465cdbff775f772d3c3d9a1cf5011976e2a06fb63a140f85489e43f3e4f',
 PARTIAL+'/raw_partial.json':'61a49e92e8773a1c932027ae02cc9aada18ef373daa2fe2789483517b47fe14f',
 ROOT_DRAIN:'52455499cbeb6237dd7aad70332731bb85ae834fba3539ea87aea7ed3aeb4e9b',
 RUN+'/operator_interrupted_partial_receipt.json':'8a455a46af97c35a34c91f2a49e26b8b76a3bbd15d488447c2810918ec88bfd6',
 TRANSPORT+'/receipt.json':'9de144fe7d2ac535663bbfba7a8c7225826c7c55977f80bf169d6f89a3dbc0f0',
 TRANSPORT+'/router_requests_snapshot.jsonl':'2f7a45054f045554aa6f008ee60c812bba8eff203cc2765ee7f47a2a23af7c39',
 TRANSPORT+'/README.zh.md':'a5bacf6fb2cd23a601313e8ebacbb113c977f2bb4c0a04945cc00983366de480',
 'portable_eval_20260908/review/bc_partial_transport/validation/cpu_preparation_v1/receipt.json':'1593d0385e26b57fef80914e8d4ed0dd7b3abe221fff04b0f390f65456af5339',
 'publication/shard_delivery_candidate_v2/FREEZE.json':'2244f13fd000555fa172c5270123aa7e57c505e226889ad6525d936eebfa87df',
 'publication/shard_delivery_review_v2/REVIEW.json':'9fe2cfed2e90803c5634c70bdf50763855051d32c0b1ebd5899f050b5fc30e89',
}
DIRECTORIES=[
 (RUN,'operator_interrupted_partial_receipt.json'),
 (PARTIAL,'receipt.json'),(TRANSPORT,'receipt.json'),
 ('portable_eval_20260908/review/bc_partial_v3','validation/root_cpu_20260908T1046Z/receipt.json'),
 ('portable_eval_20260908/review/bc_partial_transport','validation/cpu_preparation_v1/receipt.json'),
 ('portable_eval_20260908/serving/reports/ready_capture_partial_20260908T1045Z','collection_receipt.json'),
]
# Exact supporting files, not a recursive source/runtime/environment sweep.
SUPPORT=[
 'kimi_k3_eval/data_runtime/run_hpo.sh',
 'portable_eval_20260908/harness/pilot_timing.py',
 'portable_eval_20260908/harness/poolact_pilot_timing.py',
 'portable_eval_20260908/harness/scenario_smoke.py',
 'portable_eval_20260908/harness/tests/test_poolact_pilot_timing.py',
 'portable_eval_20260908/patches/profile_parameterization_v2/candidate/harness/request_profile.py',
 'portable_eval_20260908/request_profiles/kimi-k3-v3.json',
 'portable_eval_20260908/review/BC_INDEPENDENT_AUDIT.md',
 'portable_eval_20260908/review/audit_bc_attempts_v3.py',
 'portable_eval_20260908/review/audit_bc_common.py',
 'portable_eval_20260908/review/audit_bc_score_child.py',
 'portable_eval_20260908/review/audit_bc_v3.py',
 'portable_eval_20260908/review/test_bc_auditors.py',
 'portable_eval_20260908/serving/bc312_authorization_v3.json',
 'portable_eval_20260908/serving/k3_v3_context_gate_binding.json',
 'portable_eval_20260908/serving/model_profiles.json',
 'portable_eval_20260908/serving/router.py',
 'portable_eval_20260908/serving/runs/1203474/deployment.json',
 'portable_eval_20260908/serving/reports/bc_router_rawjoin_v3/cpu_preparation_v2.json',
 'portable_eval_20260908/serving/reports/bc_router_rawjoin_v3/join.py',
 'portable_eval_20260908/serving/reports/bc_router_rawjoin_v3/root_prelaunch_health_20260908T0604Z.json',
 'portable_eval_20260908/serving/reports/bc_router_rawjoin_v3/summarize_usage.py',
 'portable_eval_20260908/serving/reports/bc_router_rawjoin_v3/test_collectors.py',
 'portable_eval_20260908/serving/reports/bc_retained_attempts_v3/audit.py',
 'portable_eval_20260908/serving/reports/bc_retained_attempts_v3/test_audit.py',
 'portable_eval_20260908/serving/reports/bc_retained_attempts_v3/CONTRACT.zh.md',
 'portable_eval_20260908/serving/reports/bc_retained_attempts_v3/prepare_cpu.py',
 'portable_eval_20260908/validation/bc_independent_auditor_peer_review.json',
 'portable_eval_20260908/validation/bc_independent_auditor_preparation_v1.json',
 'portable_eval_20260908/validation/pilot_bc_v3_root_prelaunch_20260908T0600Z.json',
 'portable_eval_20260908/validation/poolact_bc_v3/validation.json',
 'portable_eval_20260908/validation/static_acceptance_v3.json',ROOT_DRAIN,
 'portable_eval_20260908/validation/observe_bc_partial_drain_root.py',
 'portable_eval_20260908/design/k3_ready_capture_candidate_v2/collector.py',
 'portable_eval_20260908/design/k3_ready_capture_candidate_v2/CPU_RECEIPT.json',
]


def snapshot(records):
 result={}
 for row in records:
  path=c.lexical(WORKSPACE/row['source']);info=path.stat();size,digest=c.stream_hash(path)
  c.need((size,digest)==(row['bytes'],row['sha256']),'source_binding_changed')
  result[row['source']]={'bytes':size,'sha256':digest,'mtime_ns':info.st_mtime_ns}
 return result


def main():
 secrets=c.scanner().load_secrets([KEY]);validator=c.scanner()
 for name,digest in PINS.items():
  raw=validator.stable_read(c.lexical(WORKSPACE/name));c.need(c.sha(raw)==digest,'external_anchor_changed');c.scan(raw,name,secrets)
 partial=c.strict_json((WORKSPACE/PARTIAL/'receipt.json').read_bytes())
 transport=c.strict_json((WORKSPACE/TRANSPORT/'receipt.json').read_bytes())
 c.need(partial['overall_complete'] is False and partial['classifications']=={'closed_original_pool':47,'no_execution_evidence_observed':31},'partial_classification')
 c.need(transport['association_integrity']=='PASS' and transport['all_attempts_double_sha'] is False and transport['whole_matrix_complete'] is False,'transport_scope')
 c.need(not (WORKSPACE/RUN/'execution.json').exists(),'unexpected_normal_execution_json')
 # Rehash only explicitly selected source evidence, not arbitrary dependency
 # paths in receipts (those can include excluded runtimes/datasets).
 known={**partial['file_bindings'],**transport['file_bindings']}
 artifacts=[]
 for number,(source,anchor) in enumerate(DIRECTORIES):
  digest=c.sha(validator.stable_read(c.lexical(WORKSPACE/source/anchor)))
  artifacts.append({'id':'directory_%02d'%number,'kind':'sealed_directory','sealed':True,'source':source,'target':source,
                    'anchor':{'path':anchor,'sha256':digest}})
 for number,source in enumerate(SUPPORT):
  path=c.lexical(WORKSPACE/source);raw=validator.stable_read(path);digest=c.sha(raw)
  binding=known.get(str(path))
  if binding:c.need(len(raw)==binding['bytes'] and digest==binding['sha256'],'support_receipt_binding_changed')
  artifacts.append({'id':'support_%02d'%number,'kind':'sealed_file','sealed':True,'source':source,'target':source,
                    'anchor':{'path':path.name,'sha256':digest}})
 spec={'schema_version':1,'approved':True,'require_secret_sources':True,
  'scope':'Explicit ROOT-authorized terminal interrupted B/C v3 evidence only. Complete originals retained; not full 78 pools or project acceptance. No Git/network/model calls.',
  'source_tree_sha256':'d1606db7d6036c8975ce9d3e556daf7fa2ce4604879f2b3878435b0f96aebb78',
  'source_archive_reference':{'path':'source/accepted-source-v3.tar.gz','sha256':'97ecfe148a2c47e811dbf15e0b820f28979972c1ad7a5939cc065b1f4ee0e15b','already_published':True,'included_again':False},
  'required_stages':[a['id'] for a in artifacts]+['formal_complete_matrix','whole_project_final_review'],
  'transport_owner_receipt_complete':True,'transport_ROOT_acceptance_not_assumed':True,
  'exclusions':['No fabricated execution.json','No weights, private credential files, environments, runtime binaries, standalone dataset payloads or live router log',
                'No repackaging current main/dirty source tree or relabeling frozen source-v3 results','Already-published A21/source-v3 dependencies are referenced by their unchanged SHA'],
  'publication_performed':False,'artifacts':artifacts}
 result,locked=validator.validate(spec,WORKSPACE,secrets,seal=True)
 if result['findings'] or result['safe_to_stage'] is not True:
  failed=BASE/'checks';failed.mkdir(exist_ok=True);failed=c.fresh(failed/'failed_initial_v1');failed.mkdir(mode=0o700)
  for name,value in [('spec.json',spec),('manifest.json',result),('lock.json',{'valid':False,'reason':'security_or_integrity_check_failed'})]:
   raw=c.encoded(value);c.scan(raw,name,secrets);c.write_new(failed/name,raw)
  print(json.dumps({'failed_scan_receipt':str(failed),'findings':result['findings'],'publication_performed':False},indent=2))
 c.need(result['safe_to_stage'] is True and not result['findings'],'complete_original_rule_scan_failed')
 for row in result['files']:
  raw=validator.stable_read(WORKSPACE/row['source']);c.scan(raw,row['target'],secrets)
  c.need(c.sha(raw)==row['sha256'] and len(raw)==row['bytes'],'source_changed_after_scan')
  binding=known.get(str(WORKSPACE/row['source']))
  if binding:c.need((row['bytes'],row['sha256'])==(binding['bytes'],binding['sha256']),'source_receipt_binding_changed')
 run_rows=[r for r in result['files'] if r['source'].startswith(RUN+'/')]
 counts={'all_run_files':len(run_rows),'all_run_bytes':sum(r['bytes'] for r in run_rows),
  'raw_files':sum('/dumps/' in r['source'] for r in run_rows),'result_files':sum('/results/' in r['source'] for r in run_rows),
  'logs_directory_files':sum('/logs/' in r['source'] for r in run_rows),'execution_log_files':sum(r['source'].endswith('/execution.log') for r in run_rows)}
 c.need(counts=={'all_run_files':2173,'all_run_bytes':99498860,'raw_files':1532,'result_files':282,'logs_directory_files':344,'execution_log_files':47},'run_inventory_counts')
 stamps=snapshot(result['files'])
 out=BASE/'checks';out.mkdir(exist_ok=True);out=c.fresh(out/'initial');out.mkdir(mode=0o700)
 summary={'passed':True,'scope':'Partial B/C delivery preparation; not performance or publication GO','file_count':len(result['files']),
  'original_bytes':result['total_bytes'],'largest_file':max(result['files'],key=lambda r:r['bytes']),
  'run_counts':counts,'known_secret_sources_checked':len(secrets),'source_tree_sha256':spec['source_tree_sha256'],
  'no_normal_execution_json':True,'all_required_project_stages_present':result['all_required_stages_present'],'publication_performed':False}
 for name,value in [('spec.json',spec),('lock.json',locked),('manifest.json',result),('source_snapshot.json',stamps),('SUMMARY.json',summary)]:
  raw=c.encoded(value);c.scan(raw,name,secrets);c.write_new(out/name,raw)
 print(json.dumps({**summary,'lock_sha256':c.sha((out/'lock.json').read_bytes()),'output':str(out)},indent=2))


if __name__=='__main__':
 try:main()
 except Exception as exc:
  print(json.dumps({'passed':False,'rule':str(exc) if isinstance(exc,c.DeliveryError) else 'prepare_failed','publication_performed':False}));raise SystemExit(1)
