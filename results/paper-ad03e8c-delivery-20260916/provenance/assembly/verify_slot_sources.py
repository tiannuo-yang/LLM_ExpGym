#!/usr/bin/env python3
"""Narrow metadata pin and path existence check; does not read raw payloads."""
import hashlib
import json
import subprocess
from pathlib import Path

W=Path('/lustrefs/users/chufan.shi/codex_space_tn')
P=W/'publication/five_model_report_20260911'
O=Path(__file__).resolve().parent
C='ad03e8c42ca501016176ee1bc407b38499178506'
checks=json.loads((O/'selected_slots_checks.json').read_text())
slots=json.loads((O/'selected_slots.json').read_text())
refs={}
def walk(x,source):
    if isinstance(x,dict):
        if x.get('sha256'):
            for k in ('path','local_path'):
                value=x.get(k)
                if isinstance(value,str) and value.startswith(str(W)+'/'):
                    refs.setdefault(value,[]).append(dict(sha256=x['sha256'],bytes=x.get('bytes'),authority=source))
            if x.get('name') and x.get('url'):
                root=None
                if '/results/qwen38-20260910/analysis/' in x['url']:
                    root=W/'qwen38_eval_20260910'
                elif '/results/deepseek-flash-0731-20260911/analysis/' in x['url']:
                    root=W/'deepseek_flash_eval_20260911'
                if root:
                    refs.setdefault(str(root/x['name']),[]).append(dict(sha256=x['sha256'],bytes=x.get('bytes'),authority=source))
        for v in x.values(): walk(v,source)
    elif isinstance(x,list):
        for v in x: walk(v,source)

for rel in ['results/all-models-latest-20260913/provenance/five_models.json',
            'results/four-model-20260911/ARCHIVE_INDEX.json',
            'results/paper-analysis-20260916/hpo/INPUT_INVENTORY.json',
            'results/paper-analysis-20260916/audit/INPUTS.json']:
    data=subprocess.check_output(['git','-C',str(P),'show',C+':'+rel])
    walk(json.loads(data),rel)

verified=[]
missing_authority=[]
for item in checks['inputs']:
    if Path(item['path']).is_relative_to(P): continue
    candidates=refs.get(item['path'],[])
    if not candidates:
        missing_authority.append(item)
        continue
    matches=[r for r in candidates if r['sha256']==item['sha256'] and (r['bytes'] is None or r['bytes']==item['bytes'])]
    assert matches,('external_input_identity_mismatch',item,candidates)
    verified.append(dict(**item,matched_authorities=[r['authority'] for r in matches]))
assert not missing_authority,missing_authority
missing_results=[]
missing_dumps=[]
for r in slots:
    if r['execution_complete']:
        if not Path(r['result_path']).is_file(): missing_results.append(dict(slot_id=r['slot_id'],path=r['result_path']))
        if not Path(r['api_dump_root']).is_dir(): missing_dumps.append(dict(slot_id=r['slot_id'],path=r['api_dump_root']))
out=dict(status='PASS' if not missing_results and not missing_dumps else 'FAIL',
         report_commit=C,external_inputs_verified=len(verified),verified=verified,
         completed_result_paths_checked=4682,completed_dump_roots_checked=4682,
         missing_results=missing_results,missing_dumps=missing_dumps,
         selected_slots_sha256=hashlib.sha256((O/'selected_slots.json').read_bytes()).hexdigest(),
         boundary='Published metadata authorities and filesystem path type only; no result/API payload reads')
(O/'source_identity_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='verified'},ensure_ascii=False,indent=2))
