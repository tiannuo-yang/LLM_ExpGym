"""Read-only fixed26 persisted-result arithmetic; no scorer/backend/model import."""
import collections
import hashlib
import json
import math
from pathlib import Path
import stat
import statistics

OP = Path(__file__).absolute().parent.parent
RUN = OP.parents[1] / 'formal_runs/restart-20260909-v5-kimi-k3-infra8-recovery'
REFS = {}
CHECKS = []


def read(p, sha=None, size=None):
    p = Path(p); before = p.lstat()
    assert stat.S_ISREG(before.st_mode) and not p.is_symlink()
    blob = p.read_bytes(); after = p.lstat()
    assert before == after
    digest = hashlib.sha256(blob).hexdigest()
    assert sha is None or sha == digest
    assert size is None or size == len(blob)
    value = {'path': str(p), 'sha256': digest, 'bytes': len(blob)}
    assert str(p) not in REFS or REFS[str(p)] == value
    REFS[str(p)] = value
    return blob


def obj(ref):
    return json.loads(read(ref['path'], ref['sha256'], ref.get('bytes')))


def check(label, actual, expected):
    ok = type(actual) is type(expected) and actual == expected
    CHECKS.append({'check': label, 'passed': ok})
    assert ok, label


def num(label, actual, expected):
    ok = type(actual) in (int, float) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
    CHECKS.append({'check': label, 'actual': actual, 'expected': expected, 'delta': actual-expected, 'passed': ok})
    assert ok, label


def canonical(text):
    v = json.loads(text)
    assert type(v) in (dict, list)
    return json.dumps(v, sort_keys=isinstance(v, dict), separators=(',', ':'), allow_nan=False)


def gap(perf, oracle):
    assert all(type(x) in (int, float) and math.isfinite(x) for x in (perf, oracle['mean_perf'], oracle['best_perf']))
    assert 0 <= perf <= 1 and oracle['best_perf'] > oracle['mean_perf']
    return max(0.0, 100.0 * (perf-oracle['mean_perf']) / (oracle['best_perf']-oracle['mean_perf']))


def projection(p, pool):
    if pool:
        return {k: p.get(k) for k in ('answer', 'scoring_input', 'answer_perf', 'answer_metrics', 'answer_source', 'answer_score_source', 'score_status', 'terminal_status', 'missing_final_policy', 'terminal_origin', 'terminal_scenario')}
    o = p['outcome']; v = {k: o.get(k) for k in ('answer', 'scoring_input', 'answer_source', 'answer_score_source', 'score_status', 'terminal_status', 'missing_final_policy', 'terminal_origin', 'terminal_scenario')}
    assert set(o['score']) == {'value'}
    v.update(answer_perf=o['score']['value'], answer_metrics=None)
    return v


def main():
    acceptance = obj({'path': str(OP/'k3_recovery_root_v1/SEAL_V2_ACCEPTANCE.json'), 'sha256': 'd4b3cf79b91d9d3ac41bc8d1c33272bc4404f8035538c08fca8e1679d2bae219'})
    inventory = obj(acceptance['inventory_ref']); closure = obj(acceptance['closure_ref'])
    assert inventory['run_root'] == str(RUN) and inventory['full_second_read_equal'] is True
    sealed = {}
    for part in inventory['file_parts']:
        for ref in obj(part):
            assert ref['path'] not in sealed
            sealed[ref['path']] = ref
    assert len(sealed) == 1072 and sum(r['bytes'] for r in sealed.values()) == 34520799
    execution = obj(closure['execution_ref']); plan = obj(closure['plan_ref'])
    assert execution['execution_complete'] is True and execution['score_complete'] is True
    assert plan['config']['output_root'] == str(RUN) and len(plan['jobs']) == len(plan['logical_rows']) == 8
    jobmap = {j['invocation_id']: j for j in plan['jobs']}
    reports = {r['invocation_id']: r['report'] for r in execution['reports']}
    baseline = obj({'path': str(OP/'k3_composite_invariance_review_v1/BASELINE.json'), 'sha256': 'd3719a4cc74d36a46b0f0ee72570de9cac877484ab051f995f95698274aa90dc'})
    assert set(jobmap) == {r['invocation_id'] for r in baseline['fixed8_identity_fields']}
    payloads = {}; artifact_refs = []
    for iid, job in jobmap.items():
        actual = reports[iid]['artifacts']; expected = set(job['expected_files'])
        assert len(actual) == len(expected) and {r['path'] for r in actual} == expected
        for ref in actual:
            p = Path(ref['path']); assert RUN in p.parents and str(p) in sealed and str(p) not in payloads
            s = sealed[str(p)]; assert ref['sha256'] == s['sha256']
            payloads[str(p)] = obj(s); artifact_refs.append(REFS[str(p)])
    assert len(payloads) == 38
    repo = Path(plan['config']['repo_root'])
    for name in ('expgym/react_loop.py', 'expgym/poolact.py', 'expgym/task_tuning.py', 'expgym/compact_nasbench101.py'):
        p = repo/name; read(p, plan['file_bindings'][str(p)])
    oracle_path = next(p for p in plan['file_bindings'] if p.endswith('/oracle3.json'))
    oracle = obj({'path': oracle_path, 'sha256': plan['file_bindings'][oracle_path]})
    agents_out, units, source_counts = [], [], collections.Counter()
    for row in plan['logical_rows']:
        iid, lid = row['invocation_id'], row['logical_id']; job = jobmap[iid]; pool = row['system'] == 'poolact'
        assert row['scenario'] == 'tuning' and row['outerrep'] == 2 and row['item'].startswith('hpobench:nasbench101:')
        result_path = str(RUN/row['result_artifact']); original = payloads[result_path]
        paths = [str(RUN/p) for p in row['agent_artifacts']]
        assert len(paths) == (4 if pool else 1)
        originals = [payloads[p] for p in paths]; agents = [projection(p, pool) for p in originals]
        if pool:
            cfg = original['config']
            check(lid+'/identity', (cfg['scenario'],cfg['cost_regime'],cfg['model'],cfg['tuning_task'],original['strategy'],cfg['agent_seeds']),
                  (row['scenario'],row['regime'],row['model_id'],row['selector']['tuning_task'],row['strategy'],row['sampling_seed_labels']))
            check(lid+'/agent_ids', [p['agent_id'] for p in originals], list(range(4)))
            check(lid+'/embedded', [projection(p,True) for p in original['agent_results']], agents)
            summary = payloads[str(RUN/job['summary_artifact'])]
            check(lid+'/summary_aggregate', summary['strategies'][row['strategy']], original['aggregate'])
        else:
            check(lid+'/identity', (original['task']['scenario'],original['task']['budget']['regime'],original['run']['model']['id'],original['task']['item']['id']),
                  (row['scenario'],row['regime'],row['model_id'],row['selector']['tuning_task']))
        perfs, gaps = [], []
        for i,(agent,payload,path) in enumerate(zip(agents,originals,paths)):
            pointer = lid+'/agent/'+str(i); answer = agent['answer']; assert type(answer) is str and answer
            check(pointer+'/scoring_input', agent['scoring_input'], answer)
            check(pointer+'/policy', (agent['missing_final_policy'],agent['terminal_origin'],agent['terminal_scenario'],agent['score_status']),
                  ('task-abstention-v1','normal_loop_return','tuning','scored_final_answer'))
            status = dict(schema_version='expgym.execution-terminal.v1',policy_version='task-abstention-v1',execution_complete=True,score_complete=True,terminal_classification='completed_scored',model_no_answer_count=0,expected_model_terminals=1,reported_model_terminals=1)
            check(pointer+'/terminal',agent['terminal_status'],status)
            perf = agent['answer_perf']; g = gap(perf,oracle['tasks'][row['item']]); perfs.append(perf);gaps.append(g)
            if pool:
                records = payload['eval_records']; assert payload['tuning_final_policy']=='legacy'
                check(pointer+'/existing_score_check',payload['score_check']['ok'],True)
                num(pointer+'/existing_recomputed_perf',payload['score_check']['recomputed_perf'],perf)
            else:
                records = [(c['raw_arguments'],c['canonical_argument'],c['performance'],c['simulated_cost_seconds']) for c in payload['tool_calls'] if c['included_in_eval_records']]
                assert payload['outcome']['tuning_final_policy']=='legacy'
            normalized = canonical(answer)
            matching = [v for v in records if v[1] is not None and v[1] == normalized]
            assert matching, pointer+'/final_must_match_original_evaluated_config'
            num(pointer+'/last_matching_tool_perf',perf,matching[-1][2])
            assert agent['answer_score_source'] in ('matching_tool_call','best_evaluated_fallback')
            source_counts[(agent['answer_source'],agent['answer_score_source'])] += 1
            if agent['answer_source']=='best_evaluated_fallback':
                best = max((x for x in records if x[2] is not None),key=lambda x:x[2]);check(pointer+'/fallback_answer',answer,best[0]);num(pointer+'/fallback_perf',perf,best[2])
            agents_out.append({'logical_id':lid,'invocation_id':iid,'agent_id':i,'item':row['item'],'system':row['system'],'regime':row['regime'],'strategy':row['strategy'],'artifact_ref':REFS[path],'answer_sha256':hashlib.sha256(answer.encode()).hexdigest(),'answer_json_type':type(json.loads(answer)).__name__,'reported_perf':perf,'independent_gap':g,'answer_source':agent['answer_source'],'answer_score_source':agent['answer_score_source'],'matching_eval_records':len(matching),'backend_table_truth':'pending_separate_ROOT_GO'})
        if pool:
            agg=original['aggregate']; winner=max(range(4),key=lambda i:perfs[i])
            check(lid+'/method',agg['method'],'best_of_n');check(lid+'/aggregate_answer',agg['answer'],agents[winner]['answer']);num(lid+'/aggregate_perf',agg['answer_perf'],perfs[winner])
            check(lid+'/individual_perfs',agg['individual_perfs'],perfs);num(lid+'/mean_individual_perf',agg['mean_individual_perf'],statistics.mean(perfs))
            pool_status=dict(agents[0]['terminal_status'],expected_model_terminals=4,reported_model_terminals=4)
            check(lid+'/aggregate_terminal',agg['terminal_status'],pool_status);check(lid+'/pool_terminal',original['terminal_status'],pool_status)
            metrics=dict(gap_mi=statistics.mean(gaps),gap_bon=max(gaps),raw_perf_mi=statistics.mean(perfs),raw_perf_bon=max(perfs))
        else:
            winner=0;metrics=dict(gap=gaps[0],raw_perf=perfs[0])
        units.append({'logical_id':lid,'invocation_id':iid,'item':row['item'],'system':row['system'],'regime':row['regime'],'strategy':row['strategy'],'outerrep':2,'agent_count':len(perfs),'earliest_max_agent':winner,'metrics':metrics})
    assert len(agents_out)==26 and len(units)==8 and all(a['answer_json_type']=='dict' for a in agents_out)
    for ref in list(REFS.values()):read(ref['path'],ref['sha256'],ref['bytes'])
    print(json.dumps({'status':'passed_persisted_score_and_oracle_arithmetic_only','backend_table_truth_verified':False,'counts':{'invocations':8,'agents':26,'result_files':38,'checks':len(CHECKS)},'gap_definition':'max(0,100*(perf-mean_perf)/(best_perf-mean_perf)); no upper clipping','tuning_pool_endpoints':'MI of all four per-agent clipped gaps/raw perfs; BoN maximum; not majority vote','source_counts':[{'answer_source':a,'answer_score_source':b,'count':n} for (a,b),n in source_counts.items()],'agents':agents_out,'units':units,'checks':CHECKS,'input_refs':list(REFS.values()),'limits':['No backend/scorer/AN2/model code executed.','Source-matching perf and oracle arithmetic do not prove table lookup truth; separate one-shot backend check pending.','26 configs fixed before scores; no selection/resample; whole N4 all from recovery.']},indent=2))


if __name__=='__main__':
    main()
