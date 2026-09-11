#!/usr/bin/env python3
"""One report-only independent review. No imports of author report modules.

Reads this report's frozen small inputs and report exports, plus the explicit
original local request-scope metadata to check its public projection.
No model, network, evaluator, archive, or runtime imports/calls. Emits JSON to
stdout; it never changes source inputs or report outputs.
"""
import csv
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
GPT = 'gpt-5.6-sol'
MODELS = ['kimi-k3', 'glm-5.3', 'qwen3.8-2.4t-a95b-fp8',
          'deepseek-v4-flash-0731', GPT]
LABELS = dict(zip(MODELS, ['Kimi-K3', 'GLM-5.3', 'Qwen3.8',
                         'DeepSeek-0731', 'GPT-5.6-sol (medium)']))
SHORT = dict(zip(MODELS, ['Kimi', 'GLM', 'Qwen', 'DeepSeek', 'GPT']))
REGIMES = ['cost_free', 'cost_moderate', 'cost_tight']
STRATEGIES = ['naive', 'cached', 'poolact']
IDENTITY = ['model', 'system', 'scenario', 'slice_kind', 'slice', 'regime', 'strategy', 'metric']
ALIASES = {'F1': 'f1', 'EA': 'evidence_acc', 'LA': 'label_acc',
           'Gap': 'gap', 'raw_performance': 'raw_perf'}
COUNTS = Counter()
FILES = {}


def read(name):
    raw = (ROOT / name).read_bytes()
    FILES[name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    return raw


def rows(name):
    return list(csv.DictReader(read(name).decode().splitlines()))


def num(v):
    if v in ('', None):
        return None
    v = float(v)
    assert math.isfinite(v)
    return v


def eq(a, b):
    a, b = num(a), num(b)
    assert (a is None) == (b is None), (a, b)
    assert a is None or math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-10), (a, b)
    COUNTS['numeric_comparisons'] += 1


def key(r):
    return tuple(r[k] for k in IDENTITY)


def avg(values):
    return math.fsum(values) / len(values) if values else None


def summary(points):
    by_item = defaultdict(list)
    for p in points:
        by_item[p['item']].append(p['v'])
    partial = [avg([v for v in vs if v is not None]) for vs in by_item.values() if any(v is not None for v in vs)]
    k = sum(p['v'] is not None for p in points)
    repeat_counts = [len(vs) for vs in by_item.values()]
    result = dict(expected_outcomes=len(points), known_outcomes=k, missing_outcomes=len(points)-k,
                  expected_items=len(by_item), known_items=len(partial),
                  complete_items=sum(all(v is not None for v in vs) for vs in by_item.values()),
                  full_mean=avg(partial) if k == len(points) else None,
                  known_subset_item_weighted_mean=avg(partial),
                  min_repeats_per_item=min(repeat_counts), max_repeats_per_item=max(repeat_counts))
    return result


def compare_summary(actual, points):
    for field, expected in summary(points).items():
        eq(actual[field], expected)


def metric(r):
    return ALIASES[r['metric']] + ('' if r['endpoint'] == 'single' else '_' + r['endpoint'].lower())


def group(points, tasks=True):
    answer = defaultdict(list)
    for p in points:
        slices = [('all', 'all'), ('family', p['family'])]
        if tasks and p['scenario'] == 'tuning':
            slices.append(('task', p['item']))
        for kind, name in slices:
            r = dict(p, model=GPT, slice_kind=kind, slice=name)
            answer[key(r)].append(p)
    return answer


def compare_contrast(actual, left, right):
    l = {(p['item'], p['outer']): p for p in left}
    r = {(p['item'], p['outer']): p for p in right}
    assert len(l) == len(left) and len(r) == len(right) and l.keys() == r.keys()
    sign = 1 if actual['system'] == 'expgym' else -1
    diff = [dict(a, v=sign*(a['v']-r[i]['v']) if a['v'] is not None and r[i]['v'] is not None else None)
            for i, a in l.items()]
    s = summary(diff)
    for field in ['expected_outcomes', 'known_outcomes', 'missing_outcomes', 'expected_items',
                  'known_items', 'complete_items', 'min_repeats_per_item', 'max_repeats_per_item']:
        eq(actual[field], s[field])
    eq(actual['effect'], s['full_mean'])
    eq(actual['known_paired_subset_effect'], s['known_subset_item_weighted_mean'])
    eq(actual['baseline_full_mean'], summary(left)['full_mean'])
    eq(actual['target_full_mean'], summary(right)['full_mean'])


def f(v, signed=False):
    value = num(v)
    return 'unknown' if value is None else format(value, '+.6f' if signed else '.6f')


def cell(r, field='full_mean', signed=False):
    value = f(r[field], signed)
    return value + (' ('+r['known_outcomes']+'/'+r['expected_outcomes']+')' if value == 'unknown' else '')


def mdrow(cells):
    return '| ' + ' | '.join(str(x).replace('|', '\\|').replace('\n', ' ') for x in cells) + ' |'


def main():
    inputs = json.loads(read('INPUTS.json'))
    for entry in inputs['files']:
        raw = read(entry['local_path'])
        assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256']
    projection = next(e for e in inputs['files'] if e['id']=='api_request_scope')
    original = Path(projection['source']).read_bytes()
    derived = read(projection['local_path'])
    provenance = projection['public_projection']
    assert (len(original),hashlib.sha256(original).hexdigest()) == (provenance['source_bytes'],provenance['source_sha256'])
    assert (len(derived),hashlib.sha256(derived).hexdigest()) == (provenance['public_bytes'],provenance['public_sha256'])
    origin_object,public_object = json.loads(original),json.loads(derived)
    for provider in ['responses','anthropic']:
        parent=origin_object['headers_explicit_in_frozen_client_source'][provider]
        assert parent['Authorization']=='<credential; omitted from dump>'
        parent['Authorization']='[REDACTED]'
    assert origin_object==public_object
    COUNTS['public_projection_exact_metadata_field_replacements']=2
    COUNTS['frozen_input_hashes'] = len(inputs['files'])
    absolute, blocks, contrasts = [rows(n) for n in ('absolute_settings.csv', 'by_outerseed.csv', 'contrasts.csv')]
    for source, actual in [('prior_absolute', absolute), ('prior_blocks', blocks), ('prior_contrasts', contrasts)]:
        prior = rows('inputs/'+source+'.csv')
        cols = list(prior[0])
        preserved = [r for r in actual if r['model'] != GPT]
        assert len(preserved) == len(prior)
        assert Counter(tuple(r[k] for k in cols) for r in prior) == Counter(tuple(r[k] for k in cols) for r in preserved)
        assert all(not any(v for k, v in r.items() if k not in cols) for r in preserved)
        COUNTS[source+'_unchanged_rows'] = len(prior)
    ai = {key(r): r for r in absolute}
    bi = {key(r)+(r['outerrep'],): r for r in blocks}
    ci = {key(r)+(r['baseline'], r['target']): r for r in contrasts}
    assert len(ai)==len(absolute) and len(bi)==len(blocks) and len(ci)==len(contrasts)
    raw = rows('inputs/gpt_metrics.csv')
    assert len(raw) == 1611
    assert len({(r['job_id'], r['metric'], r['endpoint']) for r in raw}) == len(raw)
    jobs = {r['job_id'] for r in raw}
    missing = {r['job_id'] for r in raw if r['score_complete'] != 'True'}
    assert len(jobs)==783 and len(missing)==1
    assert all(r['execution_complete']=='True' and r['model']==GPT for r in raw)
    native_points = []
    for r in raw:
        if r['system']=='poolact' and r['scenario']=='tuning' and int(r['known_agents'])<4:
            assert r['value']=='' and r['known_agent_subset_value']!=''
            assert r['seed']=='2208' and r['item']=='hpobench:nasbench101:C' and r['budget']=='cost_moderate' and r['strategy']=='poolact'
            COUNTS['strict_missing_pool_metric_rows'] += 1
        if r['scenario']=='tuning':
            outer = str(['2200', '2204', '2208'].index(r['seed']))
            assert r['repeat']=='seed_'+r['seed']
        elif r['system']=='expgym' and r['scenario']=='evidence_audit':
            outer = r['seed']
        else:
            outer = '0'
        native_points.append(dict(system=r['system'], scenario=r['scenario'], family='evidence_audit' if r['family']=='contract_nli' else r['family'],
                                  regime=r['budget'], strategy=r['strategy'], metric=metric(r), item=r['item'], outer=outer,
                                  seed=r['seed'], v=num(r['value']), source_row=len(native_points)+2))
    audit = defaultdict(list)
    points = []
    for p in native_points:
        if p['system']=='expgym' and p['scenario']=='evidence_audit':
            audit[(p['regime'],p['metric'],p['item'])].append(p)
        else:
            points.append(p)
    for ps in audit.values():
        assert len(ps)==3 and {p['seed'] for p in ps}=={'2200','2201','2202'}
        assert len({p['v'] is not None for p in ps})==1
        points.append(dict(ps[0], outer='0', v=avg([p['v'] for p in ps]) if ps[0]['v'] is not None else None))
    assert len(points)==1455 and len(audit)==78
    grouped = group(points)
    assert len(grouped)==291
    assert {k for k in ai if k[0]==GPT} == set(grouped)
    for k, ps in grouped.items():
        compare_summary(ai[k], ps)
        outers = sorted({p['outer'] for p in ps})
        eq(ai[k]['repeat_blocks'], len(outers))
        bmeans = []
        for outer in outers:
            bp = [p for p in ps if p['outer']==outer]
            compare_summary(bi[k+(outer,)], bp)
            assert set(json.loads(bi[k+(outer,)]['seed_labels'])) == ({2200,2201,2202} if ps[0]['system']=='expgym' and ps[0]['scenario']=='evidence_audit' else {int(p['seed']) for p in bp})
            bmeans.append(summary(bp)['full_mean'])
            COUNTS['gpt_blocks_independently_regrouped'] += 1
        eq(ai[k]['descriptive_repeat_sd'], statistics.stdev(bmeans) if len(outers)>1 and None not in bmeans else None)
        COUNTS['gpt_absolute_independently_regrouped'] += 1
    expected_c = set()
    for k, ps in grouped.items():
        axis_index = 5 if k[1]=='expgym' else 6
        levels = REGIMES if k[1]=='expgym' else STRATEGIES
        for target in levels[levels.index(k[axis_index])+1:]:
            kk = tuple(target if i==axis_index else v for i,v in enumerate(k))
            ck = k+(k[axis_index],target)
            expected_c.add(ck)
            compare_contrast(ci[ck], ps, grouped[kk])
            eq(ci[ck]['utility_effect'], ci[ck]['effect'])
    assert {k for k in ci if k[0]==GPT}==expected_c
    COUNTS['gpt_contrasts_independently_paired'] = len(expected_c)
    # Recompute native exports at their own original Audit order unit, instead
    # of declaring their fold-equivalent denominator to have been the original.
    native_grouped = group(native_points, tasks=False)
    def native_key(r):
        name = 'evidence_audit' if r['slice']=='contract_nli' else r['slice']
        return (GPT,r['system'],r['scenario'],'all' if name=='all' else 'family',name,r['budget'],r['strategy'],metric(r))
    for r in rows('inputs/gpt_absolute.csv'):
        ps = native_grouped[native_key(r)]
        compare_summary(r,ps)
        bm = [summary([p for p in ps if p['outer']==b])['full_mean'] for b in sorted({p['outer'] for p in ps})]
        eq(r['descriptive_repeat_sd'],statistics.stdev(bm) if len(bm)>1 and None not in bm else None)
        COUNTS['native_absolute_rows'] += 1
    for r in rows('inputs/gpt_repeats.csv'):
        ps = native_grouped[native_key(r)]
        repeat = r['repeat']
        if repeat=='R1':
            selected = ps
        else:
            selected = [p for p in ps if p['seed']==repeat[5:]]
        compare_summary(r,selected)
        COUNTS['native_repeat_rows_including_all_audit_orders'] += 1
    for r in rows('inputs/gpt_contrasts.csv'):
        k = native_key(r)
        axis = 5 if r['system']=='expgym' else 6
        kk = tuple(r['target'] if i==axis else v for i,v in enumerate(k))
        compare_contrast(r,native_grouped[k],native_grouped[kk])
        COUNTS['native_contrast_rows'] += 1
    # Independent rank derivation from checked absolute cells. No import of
    # rankings.py, and no use of reported winners to choose candidate sets.
    ranks = rows('RANKINGS.csv')
    transitions = rows('RANK_TRANSITIONS.csv')
    assert len(ranks)==270 and len(transitions)==18
    categories = Counter(r['category'] for r in transitions)
    assert categories=={'family':6,'task':9,'secondary':3}
    rankgroups = defaultdict(list)
    for r in ranks:
        rankgroups[r['endpoint']].append(r)
        source = ai[key(r)]
        for field in ['full_mean','expected_outcomes','known_outcomes','missing_outcomes','expected_items','known_items','complete_items','source_input','source_row','source_url']:
            assert r[field]==source[field]
    result = {}
    rank_markdown=read('RANKINGS.md').decode().splitlines()
    for tr in transitions:
        rs = rankgroups[tr['endpoint']]
        ri = {(r['model'],r['regime']):r for r in rs}
        assert len(ri)==15 and set(ri)=={(m,b) for m in MODELS for b in REGIMES}
        eligible = [m for m in MODELS if all(ri[m,b]['full_mean']!='' for b in REGIMES)]
        assert tr['fixed_candidates'].split(';')==eligible
        assert int(tr['fixed_candidate_count'])==len(eligible)
        assert (tr['strict_five_complete']=='True')==(len(eligible)==5)
        ws = []
        winner_cells,order_cells,margin_cells=[],[],[]
        for b in REGIMES:
            order = sorted(eligible,key=lambda m:(-float(ri[m,b]['full_mean']),m))
            group_rank = {}
            winner = []
            anchor = None
            for pos,m in enumerate(order,1):
                score=float(ri[m,b]['full_mean'])
                if anchor is None or abs(anchor-score)>1e-12:
                    anchor=score
                    current_rank=pos
                group_rank[m]=current_rank
                if current_rank==1:
                    winner.append(m)
            ws.append(set(winner))
            margin=0.0 if len(winner)>1 else float(ri[order[0],b]['full_mean'])-float(ri[order[1],b]['full_mean'])
            winner_cells.append('; '.join(SHORT[m]+' '+f(ri[m,b]['full_mean']) for m in winner))
            rank_groups=defaultdict(list)
            for m in order:
                rank_groups[group_rank[m]].append(m)
            order_cells.append(' > '.join(' = '.join(SHORT[m] for m in ms) for ms in rank_groups.values()))
            margin_cells.append(f(margin))
            for m in MODELS:
                r=ri[m,b]
                assert (r['eligible_fixed_fmt']=='True')==(m in eligible)
                assert r['rank']==(str(group_rank[m]) if m in eligible else '')
                assert (r['winner']=='True')==(m in winner)
                assert set(r['winner_set'].split(';'))==set(winner)
                eq(r['winner_score'],ri[order[0],b]['full_mean'])
                eq(r['winner_runner_up_margin'],margin)
                incomplete=[x for x in REGIMES if ri[m,x]['full_mean']=='']
                assert r['excluded_reason']==('incomplete_full_endpoint:'+';'.join(incomplete) if incomplete else '')
                COUNTS['ranking_rows'] += 1
        assert mdrow([tr['endpoint_label'],' / '.join(SHORT[m] for m in eligible)]+winner_cells+['换位' if ws[0]!=ws[2] else '不变']) in rank_markdown
        assert mdrow([tr['endpoint_label']]+order_cells) in rank_markdown
        assert mdrow([tr['endpoint_label']]+margin_cells) in rank_markdown
        COUNTS['ranking_markdown_summary_rows']+=3
        for m in MODELS:
            shown=[f(ri[m,b]['full_mean'])+' ['+ri[m,b]['known_outcomes']+'/'+ri[m,b]['expected_outcomes']+']' for b in REGIMES]
            reason='三档固定候选' if m in eligible else '完整端点缺失：'+'/'.join(b[5:].capitalize() for b in REGIMES if ri[m,b]['full_mean']=='')
            assert mdrow([SHORT[m]]+shown+[reason]) in rank_markdown
            COUNTS['ranking_markdown_model_rows']+=1
        for field,a,b in [('free_to_tight_winner_set_changed',0,2),('free_to_moderate_winner_set_changed',0,1),('moderate_to_tight_winner_set_changed',1,2)]:
            assert (tr[field]=='True')==(ws[a]!=ws[b])
        for field,winners in zip(['free_winners','moderate_winners','tight_winners'],ws):
            assert set(tr[field].split(';'))==winners
        cat=tr['category']
        result.setdefault(cat,Counter())
        result[cat]['planned']+=1
        result[cat]['changed']+=ws[0]!=ws[2]
        result[cat]['strict_five_complete']+=len(eligible)==5
        result[cat]['strict_five_changed']+=(len(eligible)==5 and ws[0]!=ws[2])
        COUNTS['rank_transitions'] += 1
    assert result['family']=={'planned':6,'changed':2,'strict_five_complete':3,'strict_five_changed':1}
    assert result['task']=={'planned':9,'changed':7,'strict_five_complete':2,'strict_five_changed':1}
    # Check every rendered aggregate/block row against its corresponding CSV.
    for model in MODELS:
        slug=model.replace('.','_')
        for prefix,src in [('tables',absolute),('repeats',blocks)]:
            name=prefix+'/'+slug+'.md'
            actual_lines=read(name).decode().splitlines()
            expected=[]
            for r in src:
                if r['model']!=model:
                    continue
                cells=[r['system']+'/'+r['scenario'],r['slice_kind']+':'+r['slice'],r['regime'][5:]+'/'+r['strategy'],r['metric']]
                if prefix=='repeats':
                    cells.append(r['outerrep']+'/'+r['seed_labels'])
                cells += [f(r['full_mean']),r['known_outcomes']+'/'+r['expected_outcomes'],r['expected_items'],f(r['known_subset_item_weighted_mean'])]
                if prefix=='tables':
                    cells += [r['repeat_blocks'],f(r['descriptive_repeat_sd'])]
                expected.append(mdrow(cells))
            observed=[line for line in actual_lines if line.startswith('| expgym/') or line.startswith('| poolact/')]
            assert Counter(expected)==Counter(observed), name
            COUNTS['detail_markdown_rows']+=len(observed)
    # Main cross-model quality, contrast, repetition, and four-model mean cost
    # rows are located by their displayed identity, independently of template.
    current_system=None
    for line in read('README.zh.md').decode().splitlines():
        if line.startswith('## 2.'):
            current_system='expgym'
        elif line.startswith('## 3.'):
            current_system='poolact'
        if not line.startswith('| '):
            continue
        cells=[x.strip() for x in line.strip('|').split('|')]
        if len(cells)==10 and cells[1] in {'f1','evidence_acc','label_acc','gap','raw_perf','f1_mi','f1_mv','evidence_acc_mi','evidence_acc_mv','label_acc_mi','label_acc_mv','gap_mi','gap_bon','raw_perf_mi','raw_perf_bon'}:
            sl,met,budget,strategy=cells[:4]
            scenario='restricted_search' if met.startswith('f1') else 'evidence_audit' if met.startswith(('evidence','label')) else 'tuning'
            kind,name=sl.split('=',1) if '=' in sl else ('all' if sl=='all' else 'family',sl)
            for m,shown in zip(MODELS,cells[5:]):
                rr=ai[(m,current_system,scenario,kind,name,'cost_'+budget,strategy,met)]
                assert shown==cell(rr) and cells[4]==rr['expected_items']
                COUNTS['main_quality_cells']+=1
        elif len(cells)==6 and cells[0] in LABELS.values() and cells[1] in {'moderate','tight'}:
            model=next(m for m in MODELS if LABELS[m]==cells[0])
            budget,met=cells[1:3]
            scenario='restricted_search' if met.startswith('f1') else 'evidence_audit' if met.startswith(('evidence','label')) else 'tuning'
            for (base,target),shown in zip([('naive','cached'),('cached','poolact'),('naive','poolact')],cells[3:]):
                rr=ci[(model,'poolact',scenario,'all','all','cost_'+budget,base,met,base,target)]
                assert shown==cell(rr,'effect',True)
                COUNTS['main_contrast_cells']+=1
        elif len(cells)==9 and cells[0] in LABELS.values() and cells[1] in {'free','moderate','tight'}:
            model=next(m for m in MODELS if LABELS[m]==cells[0])
            budget,strategy,met=cells[1:4]
            system='expgym' if strategy=='single' else 'poolact'
            kk=(model,system,'tuning','all','all','cost_'+budget,strategy,met)
            assert cells[4:7]==[cell(bi[kk+(str(i),)]) for i in range(3)]
            assert cells[7]==cell(ai[kk]) and cells[8]==f(ai[kk]['descriptive_repeat_sd'])
            COUNTS['main_repeat_cells']+=5
    # Main scientific sign claims; outcomes remain descriptive.
    primary={'restricted_search':'f1','evidence_audit':'evidence_acc','tuning':'gap'}
    for m in MODELS:
        for sc,met in primary.items():
            a=ai[(m,'expgym',sc,'all','all','cost_free','single',met)]
            b=ai[(m,'expgym',sc,'all','all','cost_tight','single',met)]
            if sc!='tuning' or m!=MODELS[3]:
                assert float(a['full_mean'])>float(b['full_mean'])
                COUNTS['primary_budget_degradation_cases']+=1
        p=ci[(m,'poolact','restricted_search','all','all','cost_tight','naive','f1_mv','naive','poolact')]
        assert float(p['effect'])>0
        COUNTS['tight_search_poolact_positive_models']+=1
    gpt_sign=Counter()
    for b in REGIMES[1:]:
        for sc,met in [('restricted_search','f1_mv'),('evidence_audit','evidence_acc_mv'),('tuning','gap_mi')]:
            v=num(ci[(GPT,'poolact',sc,'all','all',b,'naive',met,'naive','poolact')]['effect'])
            gpt_sign['unknown' if v is None else 'positive' if v>0 else 'negative' if v<0 else 'zero']+=1
    assert gpt_sign=={'positive':4,'negative':1,'unknown':1}
    COUNTS['gpt_execution_complete_jobs']=len(jobs)
    COUNTS['gpt_score_complete_jobs']=len(jobs)-len(missing)
    COUNTS['folded_gpt_metric_rows']=len(points)
    COUNTS['audit_document_metric_groups_folded_once']=len(audit)
    print(json.dumps({'schema':'independent-five-model-review-v1','status':'pass','checks':dict(COUNTS),
                      'ranking_categories':result,'gpt_main_pool_signs':gpt_sign,'files_read':FILES,
                      'numeric_tolerance':{'absolute':1e-10,'relative':1e-11},
                      'ranking_tie_tolerance':{'absolute':1e-12,'relative':0},
                      'author_modules_imported':False,'raw_or_archives_read':False,
                      'models_or_scorers_called':False},sort_keys=True,indent=2))


if __name__=='__main__':
    main()
