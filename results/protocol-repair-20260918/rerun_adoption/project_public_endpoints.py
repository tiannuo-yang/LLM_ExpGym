#!/usr/bin/env python3
"""Publish endpoint-opaque copies; original scientific files remain untouched.

This capture step needs the private frozen source directory. Public replay needs
only its hash-bound projection receipt. No endpoint values are printed or placed
in that receipt. Result, runtime, original configuration and scientific gate
identities retain their original meaning.
"""
import argparse
import copy
import csv
import gzip
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

FILES = ('progress/scoring_inputs.jsonl.gz', 'progress/verified_sources.csv',
         'new_official/SOURCE_INVENTORY.csv')
PUBLIC_HOSTS = {'openrouter.ai', 'api.openai.com'}
PREFIX = 'endpoint_sha256:'

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        allow_nan=False, separators=(',', ':')).encode()).hexdigest()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def endpoint_sha(value): return hashlib.sha256(str(value or '').encode()).hexdigest()
def csv_read(path):
    with path.open(newline='') as f:
        reader=csv.DictReader(f); return reader.fieldnames, list(reader)
def csv_bytes(fields, rows):
    out=io.StringIO(newline=''); writer=csv.DictWriter(out,fieldnames=fields,lineterminator='\n')
    writer.writeheader(); writer.writerows(rows); return out.getvalue().encode()
def without(row, key): return {k:v for k,v in row.items() if k!=key}
def private(value):
    if not value: return False
    url=urlsplit(value)
    return not (url.scheme=='https' and url.hostname in PUBLIC_HOSTS and not url.username and not url.password)

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source',type=Path,required=True)
    cli.add_argument('--output',type=Path,required=True)
    args=cli.parse_args(); source=args.source.resolve(); target=args.output.resolve()
    assert source!=target and source not in target.parents and target not in source.parents
    manifest=json.loads((source/'FAIRNESS_MANIFEST.json').read_text())
    assert manifest['status']=='PASS' and manifest['adoption_ready'] is True
    assert sha(target/'FAIRNESS_MANIFEST.json')==sha(source/'FAIRNESS_MANIFEST.json')
    assert sha(source/FILES[0])==manifest['public_scoring_inputs_sha256']
    original_receipt=json.loads((source/'PUBLIC_REPLAY_CHECKS.json').read_text())
    assert original_receipt['status']=='PASS' and original_receipt['adoption_ready'] is True
    assert original_receipt['source_manifest_sha256']==sha(source/'FAIRNESS_MANIFEST.json')
    assert original_receipt['input_package_sha256']==sha(source/FILES[0])
    assert original_receipt['verified_sources_sha256']==sha(source/FILES[1])==sha(source/FILES[2])
    packages=[json.loads(line) for line in gzip.decompress((source/FILES[0]).read_bytes()).decode().splitlines()]
    assert len(packages)==len({p['slot_id'] for p in packages})==97
    fields, originals=csv_read(source/FILES[1]); originals_by={r['slot_id']:r for r in originals}
    assert len(originals)==len(originals_by)==97
    output_packages=copy.deepcopy(packages); bindings=[]
    projected_endpoints={}; changed=0
    for original, output in zip(packages, output_packages):
        sid=original['slot_id']; old=original['config']; item=originals_by[sid]
        assert digest(old)==item['config_sha256'], sid+' original configuration identity mismatch'
        assert item['provider_base_url']==str(old.get('base_url') or ''), sid+' source endpoint mismatch'
        value=old.get('base_url'); redacted=private(value)
        hashed=endpoint_sha(value)
        if redacted: output['config']['base_url']=PREFIX+hashed; changed+=1
        projected_endpoints[sid]=str(output['config'].get('base_url') or '')
        assert without(old,'base_url')==without(output['config'],'base_url')
        assert without(original,'config')==without(output,'config')
        bindings.append(dict(slot_id=sid, endpoint_redacted=redacted,
            original_endpoint_sha256=hashed, original_config_sha256=digest(old),
            public_config_sha256=digest(output['config']),
            config_without_endpoint_sha256=digest(without(old,'base_url')),
            source_without_endpoint_sha256=digest(without(item,'provider_base_url')),
            original_result_sha256=original['result_sha256'], new_job_id=original['new_job_id']))
    raw=''.join(json.dumps(p,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n'
                for p in output_packages).encode()
    stream=io.BytesIO()
    with gzip.GzipFile(fileobj=stream,mode='wb',filename='',mtime=0) as f: f.write(raw)
    outputs={FILES[0]:stream.getvalue()}
    for relative in FILES[1:]:
        cols, oldrows=csv_read(source/relative)
        assert len(oldrows)==97 and {r['slot_id'] for r in oldrows}==set(originals_by)
        newrows=copy.deepcopy(oldrows)
        for oldrow,newrow in zip(oldrows,newrows):
            sid=oldrow['slot_id']; assert oldrow==originals_by[sid]
            newrow['provider_base_url']=projected_endpoints[sid]
            assert without(oldrow,'provider_base_url')==without(newrow,'provider_base_url')
        outputs[relative]=csv_bytes(cols,newrows)
    source_before={str(p.relative_to(source)):sha(p) for p in [source/x for x in FILES]+[source/'FAIRNESS_MANIFEST.json']}
    file_bindings=[]
    for relative,blob in outputs.items():
        path=target/relative; path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(blob)
        file_bindings.append(dict(path=relative, original_sha256=sha(source/relative),
                                  public_sha256=sha(path), endpoint_fields_changed=changed))
    assert all(sha(source/path)==value for path,value in source_before.items())
    # These are the scientific artifacts whose bytes the projection must preserve.
    unchanged=('FAIRNESS_MANIFEST.json','progress/slot_status.csv','progress/completed_slot_scalars.csv',
        'progress/member_scores.csv','new_official/slot_scalars.csv','new_official/SOURCE_SELECTION.csv',
        'new_official/hpo_rerun_slot_scalars.csv','NEW_RUNTIME_COMPARISON.csv',
        'adopted_hpo_code_versions.csv','adopted_hpo_model_budget_strategy.csv')
    unchanged_hashes={name:sha(source/name) for name in unchanged}
    assert all(sha(target/name)==value for name,value in unchanged_hashes.items())
    (target/'ORIGINAL_PUBLIC_REPLAY_CHECKS.json').write_bytes((source/'PUBLIC_REPLAY_CHECKS.json').read_bytes())
    report=dict(schema='expgym.hpo-public-endpoint-projection.v1',status='PASS',
        original_scientific_manifest_sha256=sha(source/'FAIRNESS_MANIFEST.json'),
        original_public_replay_receipt_sha256=sha(source/'PUBLIC_REPLAY_CHECKS.json'),
        original_replay_script_sha256=sha(source/'replay_hpo_reruns.py'),
        public_replay_script_sha256=sha(target/'replay_hpo_reruns.py'),
        projection_tool_sha256=sha(__file__), slots=97, redacted_slots=changed,
        preserved_public_or_empty_slots=97-changed, fields_changed=3*changed,
        files=file_bindings, slot_bindings=bindings, unchanged_scientific_artifacts=unchanged_hashes,
        allowed_public_hosts=sorted(PUBLIC_HOSTS), endpoint_identity_scheme='sha256 of the exact original UTF-8 value',
        replacement_prefix=PREFIX, all_non_endpoint_values_identical=True,
        original_private_files_unchanged=True, model_calls=0,
        scope='Publication-only endpoint projection. The original scientific manifest, runtime/result/config identities and scores are unchanged.',
        limitations=['Only capture mode reads the private originals and proves that non-endpoint values are unchanged.',
            'Public replay validates the projection receipt and public bytes; opaque endpoint digests cannot reconstruct original private endpoint values.',
            'Original configuration hashes identify executed configurations. Public configuration hashes identify endpoint-projected publication copies.'])
    # The publication replayer pins the receipt payload. Exclude its own script
    # hash and the payload digest to avoid a self-referential hash definition.
    payload={k:v for k,v in report.items() if k!='public_replay_script_sha256'}
    report['projection_payload_sha256']=digest(payload)
    script_path=target/'replay_hpo_reruns.py'; script=script_path.read_text()
    script,count=re.subn(r"^PUBLIC_ENDPOINT_PROJECTION_PAYLOAD_SHA256 = '[0-9a-f]{64}'$",
        "PUBLIC_ENDPOINT_PROJECTION_PAYLOAD_SHA256 = '"+report['projection_payload_sha256']+"'",
        script,flags=re.MULTILINE)
    assert count==1, 'Publication replayer must declare exactly one projection payload anchor'
    script_path.write_text(script)
    report['public_replay_script_sha256']=sha(script_path)
    (target/'PUBLIC_ENDPOINT_PROJECTION.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','slots','redacted_slots','fields_changed','all_non_endpoint_values_identical')},indent=2))

if __name__=='__main__': main()
