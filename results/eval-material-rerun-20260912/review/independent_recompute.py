#!/usr/bin/env python3
"""Independent saved-scalar audit. No expgym/report imports, scorers, API, or globbing.

Only explicitly SHA-bound plans/indices/results/summaries/receipts are read.
Result JSON contains embedded histories; these fields are never inspected/output.
Generated outputs are review evidence, not replacements for scientific records.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
import statistics
import subprocess

S = Path('/lustrefs/users/chufan.shi/codex_space_tn/eval_material_rerun_20260912')
OUT = S / 'review/final_material_review'
COMMIT = '6c63f1c03c88683fa55be5cafcbb8122ac8fadaa'
MODEL = {'deepseek': 'deepseek-v4-flash-0731', 'kimi': 'kimi-k3', 'gpt': 'gpt-5.6-sol', 'glm': 'glm-5.3'}
STRATS = ('naive', 'cached', 'poolact')
COUNTS = {'deepseek': 249, 'kimi': 27, 'gpt': 27, 'glm': 66}
checks = Counter()
bound_inputs = {}


def checked_json(spec):
    p = Path(spec['path'])
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    assert h == spec['sha256'], ('SHA mismatch', str(p))
    assert 'bytes' not in spec or len(b) == spec['bytes'], ('size mismatch', str(p))
    bound_inputs[str(p)] = {'sha256': h, 'bytes': len(b)}
    checks['bound_json_files'] += 1
    return json.loads(b)


def strict_mean(values):
    return statistics.mean(values) if values and all(v is not None for v in values) else None


def strict_max(values):
    return max(values) if values and all(v is not None for v in values) else None


def gap_value(perf, mean, best):
    assert best > mean
    return max(0.0, 100.0 * (perf - mean) / (best - mean))


def numeric(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def equal(a, b):
    if a is None or b is None:
        assert a is None and b is None, (a, b)
    else:
        assert numeric(a) and numeric(b) and math.isclose(a, b, abs_tol=1e-10), (a, b)


def expected_slots(model):
    scenarios = []
    if model == 'deepseek':
        scenarios += [('restricted_search', 'cost_moderate')]
        scenarios += [('evidence_audit', r) for r in ('cost_moderate', 'cost_tight')]
        scenarios += [('tuning', r) for r in ('cost_moderate', 'cost_tight')]
    else:
        scenarios += [('tuning', 'cost_moderate' if model == 'gpt' else 'cost_tight')]
        if model == 'glm':
            scenarios += [('evidence_audit', 'cost_tight')]
    result = set()
    for scene, regime in scenarios:
        if scene == 'tuning':
            items = ['hpobench:nasbench101:' + x for x in 'ABC']
            seeds = [2200, 2204, 2208]
        elif scene == 'evidence_audit':
            items = ['audit:' + str(x) for x in range(13)]
            seeds = [2200]
        else:
            items = [f'phantom_seed{s}:{q}' for s, n in [(2, 20), (3, 19)] for q in range(n)]
            seeds = [2200]
        for st in STRATS:
            for item in items:
                for seed in seeds:
                    result.add((scene, regime, st, item, seed))
    return result


def plan_slot(args, selection):
    scene = args['scenario']
    item = args['tuning_task'] if scene == 'tuning' else (
        'audit:' + str(args['question_index']) if scene == 'evidence_audit'
        else args['data_source'] + ':' + str(args['question_index']))
    assert args['agents'] == 4 and args['repeats'] == 1 and selection['repeat_index'] == 0
    assert args['max_steps'] == args['max_evals'] == 30
    assert args['missing_final_policy'] == 'task-abstention-v1' and args['tuning_final_policy'] == 'legacy'
    return scene, args['cost_regime'], selection['strategy'], item, args['seed']


def read_model(model, config, oracle):
    plan = checked_json(config['plans'][model])
    jobs = {j['job_id']: j for j in plan['jobs']}
    assert len(jobs) == COUNTS[model]
    got_slots = {plan_slot(j['args'], j['selection']) for j in jobs.values()}
    assert len(got_slots) == len(jobs) and got_slots == expected_slots(model)
    if model == 'gpt':
        manifest = json.loads((S / 'gpt/final_inventory/delivery_manifest.json').read_text())
        mapping_spec = next(x for x in manifest['outputs'] if x['path'].endswith('/effective_mapping.json'))
        assert mapping_spec == config['gpt']['effective_mapping']
        mapping = checked_json(mapping_spec)
        assert mapping['scientific_slots'] == 27 and len(mapping['physical_jobs']) == 28
        assert len(mapping['approved_recoveries']) == 1 and mapping['approved_recoveries'][0]['retained_old_transport_attempts'] == 12
        entries = {x['scientific_slot_job_id']: x for x in mapping['jobs']}
        checks['gpt_explicit_replacements'] += sum(x['replacement_applied'] for x in entries.values())
        assert sum(x['replacement_applied'] for x in entries.values()) == 1
    else:
        ex = checked_json(config['selfhosted'][model]['terminal_export'])
        assert ex['controller_drained'] and ex['counts'] == {'completed': COUNTS[model], 'failed': 0, 'not_started': 0}
        ei = dict(ex['output_identities']['execution_index.json'])
        ei['path'] = str(S / model / 'queue/terminal_export/execution_index.json')
        entries = {x['logical_job_id']: x for x in checked_json(ei)['jobs']}
    assert entries.keys() == jobs.keys()
    rows = []
    for jid, j in jobs.items():
        e = entries[jid]
        slot = plan_slot(j['args'], j['selection'])
        scene, regime, strategy, item, seed = slot
        if model == 'gpt':
            receipt = checked_json({'path': e['queue_receipt_path'], 'sha256': e['queue_receipt_sha256']})
            assert receipt['job_id'] == e['effective_physical_job_id']
            artifact_root = Path(e['invocation_path'])
            def spec_for(path):
                rel = str(Path(path).relative_to(artifact_root))
                return dict(receipt['artifacts'][rel], path=path)
            result = checked_json(spec_for(e['result_path']))
            summary = checked_json(spec_for(e['summary_path']))
            assert e['receipt_artifact_inventory_verified'] and all(a['recorded_score_check_ok'] for a in e['agents'])
            ep = checked_json({'path': e['plan_path'], 'sha256': e['plan_sha256']})
            effective = next(x for x in ep['jobs'] if x['job_id'] == e['effective_physical_job_id'])
            assert plan_slot(effective['args'], effective['selection']) == slot
        else:
            assert e['execution_status'] == 'completed' and e['identity_score_verification_passed'] is True
            result = checked_json(e['result'])
            summary = checked_json(e['summary'])
            receipt = checked_json(e['completion'])
            assert receipt['job_id'] == e['effective_job_id'] == jid and receipt['exit_code'] == 0
        cfg = result['config']
        for name in ('scenario', 'cost_regime', 'agents', 'seed', 'repeats', 'max_steps', 'max_evals', 'tool_protocol', 'missing_final_policy', 'tuning_final_policy'):
            assert cfg[name] == j['args'][name], (model, jid, name)
        assert cfg['agent_seeds'] == list(range(seed, seed + 4))
        assert cfg['question_index'] == j['args']['question_index']
        if scene == 'tuning':
            assert cfg['tuning_task'] == item
            assert cfg['evaluation_identity']['files']['budget_oracle']['sha256'] == config['oracle']['sha256']
        elif scene == 'restricted_search':
            assert cfg['data_source'] == j['args']['data_source']
        agg = result['aggregate']
        assert summary['strategies'][strategy] == agg
        assert result['agents'] == 4 and result['strategy'] == strategy
        agents = sorted(result['agent_results'], key=lambda x: x['agent_id'])
        assert [a['agent_id'] for a in agents] == [0, 1, 2, 3]
        term = result['terminal_status']
        assert term['expected_model_terminals'] == term['reported_model_terminals'] == 4 and term['execution_complete']
        assert agg['terminal_status'] == term
        valid, model_missing, other_missing, empty_scored = 0, 0, 0, 0
        perfs, gap, gap0 = [], [], []
        for a in agents:
            at = a['terminal_status']
            assert at['execution_complete'] and at['expected_model_terminals'] == at['reported_model_terminals'] == 1
            p = a.get('answer_perf')
            assert p is None or numeric(p)
            known = p is not None and at['score_complete']
            if known:
                assert a['score_check']['ok'] is True
                valid += 1
                if not str(a.get('answer') or '').strip():
                    empty_scored += 1
            else:
                assert p is None, ('score incomplete but scalar present', model, jid)
            normal_missing = not known and at['model_no_answer_count'] == 1 and at['execution_complete']
            model_missing += int(normal_missing)
            other_missing += int(not known and not normal_missing)
            perfs.append(p if known else None)
            if scene == 'tuning':
                o = oracle['tasks'][item]
                assert o['best_perf'] > o['mean_perf']
                g = gap_value(p, o['mean_perf'], o['best_perf']) if known else None
                gap.append(g)
                gap0.append(g if known else (0.0 if normal_missing else None))
        assert term['score_complete'] == (valid == 4)
        assert term['model_no_answer_count'] == sum(a['terminal_status']['model_no_answer_count'] for a in agents)
        equal(agg.get('mean_individual_perf'), strict_mean(perfs))
        assert agg['individual_perfs'] == perfs
        row = dict(model=model, scenario=scene, regime=regime, strategy=strategy, item=item, seed=seed,
                   logical_job_id=jid, agents=4, valid_agents=valid, normal_model_missing=model_missing,
                   other_unknown_agents=other_missing, empty_scored_agents=empty_scored,
                   execution_complete=True, score_complete=(valid == 4),
                   raw_mi=strict_mean(perfs), raw_bon=strict_max(perfs), raw_aggregate=agg.get('answer_perf'))
        if scene == 'tuning':
            row.update(gap_mi=strict_mean(gap), gap_bon=strict_max(gap), gap0_mi=strict_mean(gap0), gap0_bon=strict_max(gap0))
            equal(agg.get('answer_perf'), strict_max(perfs))
        elif scene == 'restricted_search':
            row.update(f1_mv=agg.get('answer_perf'), f1_mi=strict_mean(perfs), f1_bon=strict_max(perfs))
        else:
            row['label_acc_mv'] = agg['answer_metrics'].get('label_acc')
            row['evidence_acc_mv'] = agg['answer_metrics'].get('evidence_acc')
            for name in ('label_acc', 'evidence_acc'):
                vals = [a['answer_metrics'].get(name) for a in agents]
                row[name + '_mi'] = strict_mean(vals)
                row[name + '_bon'] = strict_max(vals)
        rows.append(row)
        checks['N4_results_checked'] += 1
    return rows


def aggregate(rows):
    groups = defaultdict(list)
    exclude = {'model','scenario','regime','strategy','item','seed','logical_job_id','agents','valid_agents','normal_model_missing','other_unknown_agents','empty_scored_agents','execution_complete','score_complete'}
    for r in rows:
        groups[tuple(r[k] for k in ('model','scenario','regime','strategy'))].append(r)
    out = []
    for key, group in sorted(groups.items()):
        items = defaultdict(list)
        for r in group:
            items[r['item']].append(r)
        repeats = 3 if key[1] == 'tuning' else 1
        assert all(len(v) == repeats for v in items.values())
        metrics = sorted(set().union(*(r.keys() for r in group)) - exclude)
        for metric in metrics:
            item_means = [strict_mean([r.get(metric) for r in v]) for v in items.values()]
            out.append(dict(zip(('model','scenario','regime','strategy'), key), metric=metric,
                value=strict_mean(item_means), expected_items=len(items), expected_pools=len(group), N=4,
                repeats_per_item=repeats, valid_agents=sum(r['valid_agents'] for r in group),
                planned_agents=4*len(group), complete_pools=sum(r['score_complete'] for r in group),
                normal_model_missing=sum(r['normal_model_missing'] for r in group),
                other_unknown_agents=sum(r['other_unknown_agents'] for r in group),
                empty_scored_agents=sum(r['empty_scored_agents'] for r in group)))
    return out


def old_comparison(aggs, config):
    def old_csv(rel):
        b = subprocess.check_output(['git','-C',config['historical_git_repo'],'show',COMMIT+':results/five-model-ranking-20260911/'+rel])
        bound_inputs['git:'+COMMIT+':'+rel] = {'bytes':len(b), 'sha256':hashlib.sha256(b).hexdigest()}
        return list(csv.DictReader(io.StringIO(b.decode())))
    strict = old_csv('absolute_settings.csv')
    gap0 = old_csv('main_findings_v2/gap0_settings.csv')
    gpt_source = old_csv('inputs/gpt_metrics.csv')
    old_models = {r['model'] for r in strict}
    gpt_names = [x for x in old_models if x.lower().startswith('gpt')]
    assert len(gpt_names) == 1
    MODEL['gpt'] = gpt_names[0]
    compared, consumed = [], []
    for a in aggs:
        primary = 'gap_mi' if a['scenario']=='tuning' else ('f1_mv' if a['scenario']=='restricted_search' else 'evidence_acc_mv')
        if a['metric'] not in {primary, 'gap0_mi'}:
            continue
        m = MODEL[a['model']]
        def common(r):
            return all(r[k] == v for k,v in [('model',m),('system','poolact'),('scenario',a['scenario']),('regime',a['regime']),('strategy',a['strategy'])])
        sr = [r for r in strict if common(r) and r['slice_kind']=='all' and r['slice']=='all' and r['metric']==primary]
        assert len(sr) == 1, (a, len(sr))
        sr = sr[0]
        for name, expected in [('N',4),('expected_outcomes',a['expected_pools']),('expected_items',a['expected_items']),('min_repeats_per_item',a['repeats_per_item']),('max_repeats_per_item',a['repeats_per_item']),('repeat_blocks',a['repeats_per_item'])]:
            assert int(sr[name]) == expected, (m, a['scenario'], name, sr[name], expected)
        assert sr['analysis_unit']=='pool_aggregate_N4'
        if a['model'] == 'gpt':
            # Old GPT adapter left repeat_block_items_match blank. Verify its
            # actual immutable scalar source's complete ABC x three-seed grid.
            gs=[r for r in gpt_source if r['model']==m and r['system']=='poolact' and r['scenario']=='tuning'
                and r['strategy']==a['strategy'] and r['budget']==a['regime'] and r['metric']=='Gap' and r['endpoint']=='MI']
            assert len(gs)==9 and {(r['item'],int(r['seed'])) for r in gs}=={('hpobench:nasbench101:'+x,s) for x in 'ABC' for s in (2200,2204,2208)}
            assert all(r['N']=='4' and r['expected_agents']=='4' and r['execution_complete']=='True' for r in gs)
            assert int(sr['original_logical_rows'])==9
            assert sum(r['value']!='' for r in gs)==int(sr['known_outcomes'])
            old_direct=strict_mean([float(r['value']) if r['value'] else None for r in gs])
            equal(old_direct,float(sr['full_mean']) if sr['full_mean'] else None)
            consumed.extend(gs)
        else:
            assert sr['repeat_block_items_match'] in ('True','')
            if sr['repeat_block_items_match']=='':
                assert sr['source_input']=='old_absolute' and int(sr['original_logical_rows'])==a['expected_pools']
                checks['legacy_absent_repeat_match_bound_by_explicit_item_repeat_counts'] += 1
        family = {'tuning':'nasbench101','restricted_search':'whois','evidence_audit':'evidence_audit'}[a['scenario']]
        fr = [r for r in strict if common(r) and r['slice_kind']=='family' and r['slice']==family and r['metric']==primary]
        if not fr:
            assert a['scenario']=='evidence_audit' and sr['source_input']=='old_absolute'
            checks['legacy_audit_all13_without_duplicate_family_row'] += 1
        else:
            assert len(fr)==1
            for k in ('N','expected_outcomes','expected_items','min_repeats_per_item','max_repeats_per_item','full_mean','known_outcomes','missing_outcomes'):
                assert fr[0][k] == sr[k], (m, family, k)
        if a['scenario']=='tuning':
            tr = [r for r in strict if common(r) and r['slice_kind']=='task' and r['metric']==primary]
            assert {r['slice'] for r in tr} == {'hpobench:nasbench101:'+x for x in 'ABC'}
            for r in tr:
                assert all(int(r[k])==v for k,v in [('N',4),('expected_items',1),('expected_outcomes',3),('min_repeats_per_item',3),('max_repeats_per_item',3)])
        if a['metric']=='gap0_mi':
            gr = [r for r in gap0 if common(r) and r['slice_kind']=='all' and r['slice']=='all' and r['metric']=='gap0_mi']
            assert len(gr)==1
            gr = gr[0]
            assert int(gr['planned_agents'])==36 and int(gr['planned_pools'])==9
            assert int(gr['valid_pools'])==int(sr['known_outcomes'])
            assert 0<=int(gr['valid_agents'])<=36 and 0<=int(gr['any_valid_pools'])<=9
            assert gr['strict_value']==sr['full_mean'] or (gr['strict_value'] and sr['full_mean'] and math.isclose(float(gr['strict_value']),float(sr['full_mean']),abs_tol=1e-10))
            old = float(gr['value']) if gr['value'] else None
            consumed.append(gr)
        else:
            old = float(sr['full_mean']) if sr['full_mean'] else None
            if a['scenario']!='tuning' and old is not None:
                old *= 100
        new = a['value']
        if a['scenario']!='tuning' and new is not None:
            new *= 100
        compared.append(dict(model=a['model'], scenario=a['scenario'],regime=a['regime'],strategy=a['strategy'],metric=a['metric'],old_value=old,new_value=new,change=None if old is None or new is None else new-old))
        consumed.extend([sr]+fr)
        checks['historical_rows_with_N_item_repeat_binding'] += 1
    contrasts = []
    groups = defaultdict(dict)
    for r in compared:
        groups[(r['model'],r['scenario'],r['regime'],r['metric'])][r['strategy']]=r
    for k,g in sorted(groups.items()):
        assert set(g)==set(STRATS)
        row = dict(zip(('model','scenario','regime','metric'), k))
        for st in STRATS:
            row['new_'+st]=g[st]['new_value']
            row['old_'+st]=g[st]['old_value']
        for baseline in ('naive','cached'):
            for period in ('old','new'):
                x,y=g['poolact'][period+'_value'],g[baseline][period+'_value']
                row[period+'_pool_minus_'+baseline]=None if x is None or y is None else x-y
        for period in ('old','new'):
            x,y=g['cached'][period+'_value'],g['naive'][period+'_value']
            row[period+'_cached_minus_naive']=None if x is None or y is None else x-y
        contrasts.append(row)
    return compared, contrasts, consumed


def resource_review(rows, config):
    result = {}
    def bound_csv(spec):
        b=Path(spec['path']).read_bytes()
        assert len(b)==spec['bytes'] and hashlib.sha256(b).hexdigest()==spec['sha256']
        bound_inputs[spec['path']]={'bytes':len(b),'sha256':spec['sha256']}
        return list(csv.DictReader(io.StringIO(b.decode())))
    for model in sorted({r['model'] for r in rows}):
        if model=='gpt':
            g=checked_json(config['gpt']['token_usage_summary'])
            a,e,s=[g[k] for k in ('all_physical_attempts','effective_attempts','superseded_attempts')]
            assert (a['physical_transport_attempts'],e['physical_transport_attempts'],s['physical_transport_attempts'])==(1415,1403,12)
            assert a['states']=={'success':1403,'error':12} and s['states']=={'error':12}
            for metric in ('input_tokens','output_tokens','reasoning_tokens','cached_tokens'):
                assert a['tokens'][metric]['known_sum']==e['tokens'][metric]['known_sum']
                assert a['tokens'][metric]['unknown_attempts']==s['tokens'][metric]['unknown_attempts']==12
                assert a['tokens'][metric]['total_if_fully_known'] is None and s['tokens'][metric]['known_sum'] is None
            assert e['tokens']['input_tokens']['known_sum']+e['tokens']['output_tokens']['known_sum']==e['tokens']['input_plus_output_tokens']['known_sum']
            result[model]={'formal_successful_requests':1403,'superseded_transport_errors':12,
                'known_input_tokens':e['tokens']['input_tokens']['known_sum'],'known_output_tokens':e['tokens']['output_tokens']['known_sum'],
                'known_reasoning_tokens_subset_output':e['tokens']['reasoning_tokens']['known_sum'],
                'known_cached_tokens_subset_input':e['tokens']['cached_tokens']['known_sum'],
                'all_physical_usage_unknown_attempts':12,'all_physical_complete_token_total':None}
            continue
        ex=checked_json(config['selfhosted'][model]['resource_export'])
        pools,settings=[] ,[]
        for filename,target in [('resources_by_pool.csv',pools),('resources_by_setting.csv',settings)]:
            spec=dict(ex['output_identities'][filename],path=str(S/model/'queue/resource_export'/filename))
            target.extend(bound_csv(spec))
        assert len(pools)==COUNTS[model]
        assert {p['logical_job_id'] for p in pools}=={r['logical_job_id'] for r in rows if r['model']==model}
        grouping=defaultdict(list)
        for p in pools:
            assert p['execution_status']=='completed' and p['raw_inventory_complete']=='True'
            grouping[(p['scenario'],p['cost_regime'],p['strategy'])].append(p)
        assert len(grouping)==len(settings)
        additive=('planned_pools','planned_agents','physical_attempts_known_subtotal','successful_replies_known_subtotal',
                  'errored_attempts_known_subtotal','retry_attempts_known_subtotal','input_tokens_known_subtotal',
                  'output_tokens_known_subtotal','reasoning_tokens_known_subtotal','usage_anomaly_observed_attempts',
                  'raw_projection_error_observed_attempts','request_wall_seconds_known_subtotal','pool_wall_seconds_known_subtotal')
        for st in settings:
            ps=grouping[(st['scenario'],st['cost_regime'],st['strategy'])]
            for field in additive:
                equal(sum(float(p[field]) for p in ps),float(st[field]))
            for field in ('errored_attempts_known_subtotal','retry_attempts_known_subtotal','usage_anomaly_observed_attempts','raw_projection_error_observed_attempts'):
                assert float(st[field])==0
        result[model]={k:sum(float(r[k]) for r in settings) for k in additive}
        result[model]['scope']=ex['scope']
        result[model]['request_wall_is_overlapping_sum_not_fleet']=True
    return result


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f,fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--models',nargs='+',default=['deepseek','kimi','gpt'])
    ap.add_argument('--reuse-three',action='store_true')
    ap.add_argument('--reuse-saved-stage',action='store_true')
    args=ap.parse_args()
    config=json.loads((S/'report/preparation_config.json').read_text())
    oracle=checked_json(config['oracle'])
    stage='final' if args.reuse_three else 'three_frozen_models'
    target=OUT/stage
    target.mkdir(parents=True,exist_ok=True)
    rows=[]
    if args.reuse_saved_stage:
        rows=json.loads((target/'scalar_rows.json').read_text())
        prior=json.loads((target/'SCALAR_CHECKS.json').read_text())
        checks.update(prior['checks'])
        bound_inputs.update(prior['bound_inputs'])
    if args.reuse_three and not args.reuse_saved_stage:
        prior=json.loads((OUT/'three_frozen_models/CHECKS.json').read_text())
        previous=checked_json(prior['scalar_cache_identity'])
        rows.extend(previous)
        checks.update(prior['checks'])
        bound_inputs.update(prior['bound_inputs'])
        assert set(args.models)=={'glm'}
    if not args.reuse_saved_stage:
        for model in args.models:
            rows.extend(read_model(model,config,oracle))
        (target/'scalar_rows.json').write_text(json.dumps(rows,indent=2)+'\n')
        (target/'SCALAR_CHECKS.json').write_text(json.dumps({'checks':dict(checks),'bound_inputs':bound_inputs},indent=2)+'\n')
    aggs=aggregate(rows)
    comparisons, contrasts, consumed=old_comparison(aggs,config)
    resources=resource_review(rows,config)
    write_csv(target/'pool_scalar_metrics.csv',rows)
    write_csv(target/'aggregate_metrics.csv',aggs)
    write_csv(target/'old_new_settings.csv',comparisons)
    write_csv(target/'contrasts.csv',contrasts)
    (target/'scalar_rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    (target/'historical_consumed_rows.json').write_text(json.dumps(consumed,indent=2)+'\n')
    (target/'RESOURCE_CHECKS.json').write_text(json.dumps(resources,indent=2)+'\n')
    report=dict(stage=stage,passed=True,scope='Independent saved-scalar aggregation and identity/count validation, not rescore or raw semantics review',
        pools=len(rows),agents=4*len(rows),valid_agents=sum(r['valid_agents'] for r in rows),
        normal_model_missing=sum(r['normal_model_missing'] for r in rows),
        other_unknown_agents=sum(r['other_unknown_agents'] for r in rows),
        empty_scored_agents=sum(r['empty_scored_agents'] for r in rows),checks=dict(checks),bound_inputs=bound_inputs,
        scalar_cache_identity={'path':str(target/'scalar_rows.json'),'bytes':(target/'scalar_rows.json').stat().st_size,
            'sha256':hashlib.sha256((target/'scalar_rows.json').read_bytes()).hexdigest()})
    (target/'CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='bound_inputs'},indent=2))
    print(json.dumps(contrasts,indent=2))


if __name__=='__main__':
    main()
