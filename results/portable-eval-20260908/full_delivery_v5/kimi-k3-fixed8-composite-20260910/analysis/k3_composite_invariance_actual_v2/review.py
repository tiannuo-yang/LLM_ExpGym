"""Final Python3.11 fixed8 composite: strict frozen-baseline metadata review."""
import collections
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import stat

OP = Path(__file__).absolute().parent.parent
OLD = OP/'actual_formal_export_k3_node_failure_v2'
NEW = OP/'actual_k3_fixed8_composite_export_v2_py311_final'
REFS = {}


def read(path, sha, size=None):
    p=Path(path);s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink()
    b=p.read_bytes();assert s==p.lstat() and hashlib.sha256(b).hexdigest()==sha
    assert size is None or len(b)==size
    r=dict(path=str(p),sha256=sha,bytes=len(b));assert str(p) not in REFS or REFS[str(p)]==r
    REFS[str(p)]=r;return b


def obj(ref):
    return json.loads(read(ref['path'],ref['sha256'],ref.get('bytes')))


def output_index(path,sha,all_files=False):
    index=json.loads(read(path/'EXPORT_INDEX.json',sha))
    assert {p.name for p in path.iterdir()}=={'EXPORT_INDEX.json',*index['files']}
    blobs={}
    if all_files:
        for name,ref in index['files'].items():blobs[name]=read(path/name,ref['sha256'],ref['bytes'])
    return index,blobs


def main():
    baseline=obj(dict(path=str(OP/'k3_composite_invariance_review_v1/BASELINE.json'),sha256='d3719a4cc74d36a46b0f0ee72570de9cac877484ab051f995f95698274aa90dc'))
    oi,_=output_index(OLD,'ababd4141ab276e32dfa9ec07b39c6b68a571850b6469f3657033f65bd882ba7')
    ni,nb=output_index(NEW,'fc68a5a057c45056924b17b91f054311d6cd43dc8174da85892265f8d7758f86',True)
    assert len(ni['files'])==17
    def old(name):return read(OLD/name,oi['files'][name]['sha256'],oi['files'][name]['bytes'])
    manifest=old('manifest.json');assert nb['manifest.json']==manifest
    m=json.loads(manifest);logical={r['logical_id']:r for r in m['logical_rows']}
    oldrecords=json.loads(old('records.json'))['records'];newrecords=json.loads(nb['records.json'])['records']
    a={r['logical_id']:r for r in oldrecords};b={r['logical_id']:r for r in newrecords}
    fixed={r['invocation_id'] for r in baseline['fixed8_identity_fields']};fixedlids={r['logical_id'] for r in baseline['fixed8_identity_fields']}
    assert len(a)==len(b)==len(logical)==783 and set(a)==set(b)==set(logical)
    unchanged=set(a)-fixedlids;assert len(unchanged)==775 and all(a[k]==b[k] for k in unchanged)
    def csvrows(blob):return list(csv.DictReader(io.StringIO(blob.decode())))
    before={r['comparison']:r for r in csvrows(old('effects.csv'))};after={r['comparison']:r for r in csvrows(nb['effects.csv'])}
    assert len(before)==len(after)==514 and set(before)==set(after)
    allowed=set(baseline['allowed_changed_effect_ids']);invariant=set(before)-allowed
    assert len(invariant)==341 and all(before[k]==after[k] for k in invariant)
    changes=[k for k in before if before[k]!=after[k]]
    assert len(changes)==162 and set(changes)<=allowed
    assert all(before[k]['status']=='unknown_incomplete_endpoint' and after[k]['status']=='descriptive_complete' for k in changes)
    assert all(before[k]==after[k] for k in baseline['required_preserved_negative_performance_ids'])
    assert all(before[k]==after[k] for k in baseline['required_unchanged_primary_ids'])
    assert all(not v['ci'] and not v['p_value'] for v in after.values())
    def ident(r):return tuple(r[k] for k in ('model','system','scenario','item','regime','strategy','outerseed','metric'))
    oldmetrics={ident(r):r for r in csvrows(old('metrics.csv'))};newmetrics={ident(r):r for r in csvrows(nb['metrics.csv'])}
    fixedident={tuple(r[k] for k in ('model','system','scenario','item','regime','strategy'))+('outer_00002',) for r in baseline['fixed8_identity_fields']}
    assert set(oldmetrics)==set(newmetrics)
    invariant_metrics=[k for k in oldmetrics if k[:-1] not in fixedident]
    assert len(invariant_metrics)==7588 and all(oldmetrics[k]==newmetrics[k] for k in invariant_metrics)
    cp=json.loads(nb['COMPOSITE_PROVENANCE.json']);selection=cp['effective_selection']
    assert len(selection)==705 and len({s['invocation_id'] for s in selection})==705
    for s in selection:
        iid=s['invocation_id'];segment='recovery' if iid in fixed else 'base'
        assert s['selected_segment']==segment and s['attempt_ordinal']==int(segment=='recovery') and s['selected_run_id']==cp['segments'][segment]['run_id']
        assert set(s['logical_ids'])=={r['logical_id'] for r in logical.values() if r['invocation_id']==iid}
        assert s['selection_basis']=='fixed pre-result infra scope, never scores'
    assert cp['not_a_single_fresh_705_run'] is True and cp['model_calls']==cp['scorer_calls']==0
    source_index=json.loads(nb['source_index.json']);rich=cp['effective_source_map']
    assert len(source_index)==len(rich)==2247 and {k:v['path'] for k,v in rich.items()}==source_index
    for relative,v in rich.items():
        segment='recovery' if v['invocation_id'] in fixed else 'base'
        assert v['segment']==segment and v['run_id']==cp['segments'][segment]['run_id'] and v['attempt_ordinal']==int(segment=='recovery')
        candidates=[r for lid,r in b.items() if logical[lid]['invocation_id']==v['invocation_id'] and relative in r['source_sha256']]
        assert candidates and all(r['source_sha256'][relative]==v['sha256'] for r in candidates)
    ledger=json.loads(nb['ALL_ATTEMPT_COST_LEDGER.json']);requests=ledger['requests']
    assert len(requests)==16609 and len({(r['run_id'],r['request_id']) for r in requests})==16609
    oldpaths={};oldids=set();oldowners={};iid_ids=collections.defaultdict(set)
    for rec in oldrecords:
        iid=logical[rec['logical_id']]['invocation_id'];side=rec['telemetry_sidecar']
        for path,h in side['raw_source_sha256'].items():assert path not in oldpaths;oldpaths[path]=h;oldowners[path]=iid
        for rid in side['raw_request_ids']:assert rid not in oldids;oldids.add(rid);iid_ids[iid].add(rid)
    segments={s:[r for r in requests if r['segment']==s] for s in ('base','recovery')}
    assert len(segments['base'])==16320 and len(segments['recovery'])==289
    base=segments['base'];assert {r['source_ref']['path']:r['source_ref']['sha256'] for r in base}==oldpaths and {r['request_id'] for r in base}==oldids
    actual_iid_ids=collections.defaultdict(set)
    for r in base:assert r['invocation_id']==oldowners[r['source_ref']['path']];actual_iid_ids[r['invocation_id']].add(r['request_id'])
    assert dict(actual_iid_ids)==dict(iid_ids)
    totals={};states={}
    for seg,rows in list(segments.items())+[('all',requests)]:
        totals[seg]={};states[seg]=dict(collections.Counter(r['state'] for r in rows))
        for field in ('input_tokens','output_tokens','reasoning_tokens'):
            values=[r['usage'][field] for r in rows]
            for v in values:
                assert v['attempts']==1 and type(v['known_sum']) is int and v['known_sum']>=0 and type(v['unknown_attempts']) is int and v['unknown_attempts'] in (0,1)
                assert v['complete_total']==(None if v['unknown_attempts'] else v['known_sum'])
            known=sum(v['known_sum'] for v in values);unknown=sum(v['unknown_attempts'] for v in values)
            totals[seg][field]=dict(attempts=len(rows),known_sum=known,unknown_attempts=unknown,complete_total=None if unknown else known)
    assert totals['base']==baseline['old_persisted_usage_from_783_disjoint_logical_sidecars'] and totals['all']==ledger['usage']
    assert states['base']=={'success':16257,'error':63} and states['recovery']=={'success':289} and states['all']==ledger['raw_state_counts']
    for seg in segments:
        closure=obj(cp[seg]['closure_ref']);assert closure['raw_count']==len(segments[seg]) and closure['raw_states']==states[seg]
    for r in requests:
        assert r['run_id']==cp['segments'][r['segment']]['run_id'] and r['attempt_ordinal']==int(r['segment']=='recovery')
        u=r['usage'];reason=u['reasoning_tokens']['complete_total'];completion=u['output_tokens']['complete_total']
        assert reason is None or completion is None or reason<=completion
    assert ledger['physical_invocations_started']==ledger['physical_invocations_planned']==len(ledger['invocation_attempts'])==713
    assert (ledger['statistical_invocations'],ledger['statistical_logical_rows'],ledger['statistical_agent_slots'])==(705,783,1881)
    assert ledger['provider_billing_completeness_proven'] is False and ledger['provider_billed_total'] is None and ledger['allocation_wall_and_gpu_costs'] is None
    # Separately produced independent actual289 usage proof, no raw reread here.
    peer=obj(dict(path=str(OP/'k3_fixed8_science_review_v1/usage_peer/summary.json'),sha256='9297cd6b20996b1bfd7a333dcc6513918483dbbab102653a0559f45580b9d0a1'))
    attempts=obj(dict(path=str(OP/'k3_fixed8_science_review_v1/usage_peer/attempts.json'),sha256='2c1d96c877792cd5872871180a2b721d6f3b49d8c3701b147808de78c70ed92a'))
    assert peer['usage']==totals['recovery'] and peer['raw_count']==289
    actuals={(r['run_id'],r['request_id']):r for r in attempts};assert len(actuals)==289
    for r in segments['recovery']:
        v=actuals[(r['run_id'],r['request_id'])]
        assert v['invocation_id']==r['invocation_id'] and v['state']==r['state'] and all(v['raw_ref'][k]==r['source_ref'][k] for k in ('path','sha256'))
        assert all(v['usage'][f]==r['usage'][f]['complete_total'] for f in ('input_tokens','output_tokens','reasoning_tokens'))
    arithmetic=obj(dict(path=str(OP/'k3_fixed8_science_review_v1/ARITHMETIC.json'),sha256='72bc09214db70b73038a10b59131d5096b8aff5b68893bb35f463dd665ae1474'))
    metric_checks=[]
    for u in arithmetic['units']:
        prefix=('kimi-k3',u['system'],'tuning',u['item'],u['regime'],u['strategy'],'outer_00002')
        for name,expected in u['metrics'].items():
            actual=float(newmetrics[prefix+(name,)]['value']);assert math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12)
            metric_checks.append(dict(logical_id=u['logical_id'],metric=name,actual=actual,independent_expected=expected,delta=actual-expected))
    for ref in list(REFS.values()):read(ref['path'],ref['sha256'],ref['bytes'])
    print(json.dumps(dict(status='PASS_STRICT_ORIGINAL_BASELINE',strict_invariance_passed=True,counts=dict(new_files=18,new_bytes=sum(v['bytes'] for v in ni['files'].values())+1991,logical=783,unchanged_records=775,unchanged_metric_rows=7588,effects=514,allowed=173,required_invariant_exact=341,all_effect_rows_exact=352,changed=162,old_negative_exact=23,primary_exact=5,selected_base=697,selected_recovery=8,agent_slots=1881,source_keys=2247,physical_attempts=713,base_raw=16320,recovery_raw=289),ci_p_all_null=True,original_manifest_bytes_equal=True,fixed_selection_no_best_of_attempts=True,segment_usage=totals,raw_states=states,new289_independent_usage_exact=True,new8_metric_checks=metric_checks,changed_comparison_ids=changes,input_refs=list(REFS.values()),limitations=['Strict341/775 checks are exact, without tolerance; independent new8 arithmetic uses explicitly recorded 1e-12 numerical comparison.','Old raw usage is preserved-ledger/accepted-sidecar/closure metadata verification, not new old-raw parsing.','New26 local table proof and post-report review are separate.','No model/scorer/AN2/backend/merge executed by this program.']),indent=2))


if __name__=='__main__':
    main()
