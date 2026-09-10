"""One ROOT-authorized fixed26 local table check, not a model/scorer rerun."""
import hashlib
import io
import json
import math
from pathlib import Path
import pickle
import resource
import stat
import sys
import types

HERE = Path(__file__).absolute().parent
OP = HERE.parent
REFS = {}


def read(ref):
    p = Path(ref['path']); before = p.lstat()
    assert stat.S_ISREG(before.st_mode) and not p.is_symlink()
    blob = p.read_bytes(); assert before == p.lstat()
    assert hashlib.sha256(blob).hexdigest() == ref['sha256']
    assert 'bytes' not in ref or len(blob) == ref['bytes']
    REFS[str(p)] = dict(path=str(p), sha256=ref['sha256'], bytes=len(blob))
    return blob


class BuiltinContainersOnly(pickle.Unpickler):
    def find_class(self, module, name):
        raise ValueError('GLOBAL object construction forbidden')

    def persistent_load(self, pid):
        raise ValueError('Persistent object construction forbidden')


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    assert sys.version_info[:3] == (3, 11, 15) and sys.dont_write_bytecode
    go_ref = dict(path=str(OP/'k3_recovery_root_v1/NAS26_TABLE_VALIDATION_GO.json'), sha256='9bfdab7affb5db7914b890bfd7cb4175b29111f4645ad0e4a9d0b5790b2e85cb')
    go = json.loads(read(go_ref))
    assert go['issuer']=='ROOT' and go['approved'] is True and go['lookup_invocations']==1
    assert go['model_calls_allowed'] is False and go['network_allowed'] is False and go['original_data_writes_allowed'] is False
    refs = {Path(r['path']).name:r for r in go['inputs']}
    module_blob = read(refs['compact_nasbench101.py'])
    table_blob = read(refs['nasbench_101_compact.pkl'])
    manifest = json.loads(read(refs['nasbench_101_compact.manifest.json']))
    assert manifest['architectures_count']==423624 and manifest['file_sha256']==refs['nasbench_101_compact.pkl']['sha256']
    arithmetic_ref = dict(path=str(HERE/'ARITHMETIC.json'),sha256='72bc09214db70b73038a10b59131d5096b8aff5b68893bb35f463dd665ae1474')
    arithmetic = json.loads(read(arithmetic_ref)); agents=arithmetic['agents']
    assert len(agents)==26 and len({(a['invocation_id'],a['agent_id']) for a in agents})==26
    configs=[]
    for a in agents:
        payload=json.loads(read(a['artifact_ref']))
        answer=payload['answer'] if a['system']=='poolact' else payload['outcome']['answer']
        assert hashlib.sha256(answer.encode()).hexdigest()==a['answer_sha256']
        config=json.loads(answer)
        assert type(config) is dict, 'Vector requires separate ROOT ordering approval'
        assert all(type(v) in (str,int,float) and (not isinstance(v,(int,float)) or math.isfinite(v)) for v in config.values())
        configs.append(config)
    # One restricted deserialization of one exact SHA-pinned data blob. No find_class fallback.
    stream=io.BytesIO(table_blob); table=BuiltinContainersOnly(stream).load()
    assert stream.read()==b'' and type(table) is dict
    assert table['schema']==manifest['schema']=='expgym.nasbench101-maxfidelity.v1'
    architectures=table['architectures'];assert type(architectures) is dict
    assert table['architectures_count']==len(architectures)==423624
    for key,value in architectures.items():
        assert type(key) is str and len(key)==32 and all(c in '0123456789abcdef' for c in key)
        assert type(value) in (list,tuple) and len(value)==3
        assert all(type(x) in (int,float) and math.isfinite(x) for x in value)
    module=types.ModuleType('pinned_nas26_configuration_hash')
    module.__file__=refs['compact_nasbench101.py']['path']
    exec(compile(module_blob,module.__file__,'exec'),module.__dict__)
    assert module.np.__version__=='2.4.6'
    rows=[]
    for a,config in zip(agents,configs):
        variant=a['item'].rsplit(':',1)[1]
        architecture=module.configuration_hash(config,variant)
        value=architectures.get(architecture) if architecture is not None else None
        validation_error=1.0 if value is None else float(value[0])
        assert 0<=validation_error<=100
        expected=max(0.0,min(1.0,1.0-validation_error/100.0 if validation_error>1.0 else 1.0-validation_error))
        actual=a['reported_perf'];matched=actual==expected
        rows.append(dict(invocation_id=a['invocation_id'],agent_id=a['agent_id'],item=a['item'],artifact_ref=a['artifact_ref'],answer_sha256=a['answer_sha256'],architecture_hash=architecture,found_in_pinned_table=value is not None,validation_error=validation_error,table_cost=None if value is None else value[2],reported_perf=actual,table_expected_perf=expected,exact_equal=matched,delta=actual-expected))
    for ref in list(REFS.values()):read(ref)
    passed=all(r['exact_equal'] and r['found_in_pinned_table'] for r in rows)
    print(json.dumps(dict(status='passed_local_pinned_table_consistency' if passed else 'failed_local_table_comparison',passed=passed,source_hash_calls=26,restricted_table_deserializations=1,table_entries=423624,benchmark_instances=0,objective_or_scorer_calls=0,model_calls=0,ConfigSpace_calls=0,core_limit=list(resource.getrlimit(resource.RLIMIT_CORE)),rows=rows,input_refs=list(REFS.values()),limitations=['Same pinned configuration_hash implementation is reused, not an independent canonical-graph algorithm proof.','This verifies the local pinned maxfidelity table, not authenticity/completeness of conversion from official TFRecord, training contamination, or any fresh training.','No original result overwritten or alternate score selected.']),indent=2))
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
