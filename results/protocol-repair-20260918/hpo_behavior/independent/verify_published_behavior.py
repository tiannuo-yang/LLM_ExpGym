#!/usr/bin/env python3
"""Compare independent canonical calculations against the proposed behavior export."""
import csv
import hashlib
import json
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median
import check_hpo_behavior as independent

B = independent.OUT.parent
P = B/'observed_behavior486'
checked = Counter()
mismatches = []


def equal(actual, expected):
    if expected is None:
        return actual == ''
    if type(expected) in (float,int):
        return actual != '' and math.isclose(float(actual),expected,rel_tol=1e-11,abs_tol=1e-11)
    if isinstance(expected,dict):
        return json.loads(actual)==expected
    return actual==str(expected)


def check(filename, key, field, actual, expected):
    checked[filename]+=1
    if not equal(actual,expected):
        mismatches.append(dict(file=filename,key=key,field=field,actual=actual,expected=expected))


def summary_value(rs, field):
    if field == 'n':
        return len(rs)
    if field == 'score_source_counts':
        return dict(Counter(r['answer_score_source'] or 'missing' for r in rs))
    if field in {'natural_n','budget_n','cap_n','other_n'}:
        return sum(r['termination_class']==field[:-2] for r in rs)
    if field.startswith('natural_stop_budget_fraction_'):
        nums=[r['delivered_budget_fraction'] for r in rs if r['termination_class']=='natural' and r['delivered_budget_fraction'] is not None]
        return (mean(nums) if field.endswith('_mean') else median(nums)) if nums else None
    alias={'delivered_total':'delivered_evaluations','repeated_delivered_total':'repeated_delivered_evaluations'}
    if field in alias:
        return sum(r[alias[field]] for r in rs)
    for suffix in ('_fraction','_median','_mean','_total','_denom','_n'):
        if field.endswith(suffix):
            base=field[:-len(suffix)]
            nums=[r[base] for r in rs if r[base] is not None]
            if suffix=='_fraction':return sum(nums)/len(rs)
            if suffix=='_median':return median(nums) if nums else None
            if suffix=='_mean':return mean(nums) if nums else None
            if suffix=='_denom':return len(nums)
            return sum(nums)
    raise KeyError(field)


def main():
    source=list(csv.DictReader((independent.SOURCE/'SOURCE_SELECTION.csv').open()))
    source=[s for s in source if s['scenario']=='tuning' and s['system']=='expgym']
    new={r['slot_id']:r for r in json.loads((independent.SOURCE/'INPUTS.json').read_text())['new_results']}
    jobs=[(s,independent.FROZEN/s['historical_trajectory'] if s['historical_trajectory'] else independent.Path(new[s['slot_id']]['path'])) for s in source]
    with ThreadPoolExecutor(max_workers=12) as executor:rows=list(executor.map(independent.consume,jobs))
    lookup={r['slot_id']:r for r in rows}
    for actual in csv.DictReader((P/'trajectories.csv').open()):
        expected=lookup[actual['slot_id']]
        for field in actual.keys() & expected.keys() - {'trace_path','cohort'}:
            check('trajectories.csv',actual['slot_id'],field,actual[field],expected[field])
    tables={'by_regime.csv':('regime',),'by_model_regime.csv':('model','regime'),
        'by_family_regime.csv':('family','regime'),'by_model_family_regime.csv':('model','family','regime'),
        'matched_free_tight_by_model.csv':('model','regime'),'matched_free_tight_by_regime.csv':('regime',)}
    for filename,fields in tables.items():
        for actual in csv.DictReader((P/filename).open()):
            rs=[r for r in rows if all(str(r[k])==actual[k] for k in fields)]
            for field,value in actual.items():
                if field not in fields:
                    expected=summary_value(rs,field)
                    check(filename,'/'.join(actual[f] for f in fields),field,value,expected)
    for actual in csv.DictReader((P/'free_tight_pairs.csv').open()):
        free,tight=lookup[actual['free_slot_id']],lookup[actual['tight_slot_id']]
        for budget,r in [('free',free),('tight',tight)]:
            for field,source in [('delivered','delivered_evaluations'),('stopping','termination_class'),('first_best','first_best_observation_index'),('final','final_performance'),('score_complete','score_complete'),('slot_id','slot_id')]:
                check('free_tight_pairs.csv',actual['free_slot_id'],budget+'_'+field,actual[budget+'_'+field],r[source])
        for f in ('model','task','seed','rep'):
            check('free_tight_pairs.csv',actual['free_slot_id'],f,actual[f],free[f])
            assert free[f]==tight[f]
    for actual in csv.DictReader((P/'termination_reasons.csv').open()):
        rs=[r for r in rows if all(str(r[k])==actual[k] for k in ('model','regime','termination','termination_class'))]
        check('termination_reasons.csv',str(actual),'n',actual['n'],len(rs))
    attempt_rows={(r['slot_id'],int(r['tool_index'])):r for r in csv.DictReader((P/'evaluation_events.csv').open())}
    delivered_rows={(r['slot_id'],int(r['delivered_index'])):r for r in csv.DictReader((P/'delivered_events.csv').open())}
    def numeric_normalize(v):
        if isinstance(v,dict):return {k:numeric_normalize(x) for k,x in v.items()}
        if isinstance(v,list):return [numeric_normalize(x) for x in v]
        return int(v) if type(v) in (int,float) and independent.finite(v) and int(v)==v else v
    for selected,path in jobs:
        trace=json.loads(path.read_bytes())
        slot=selected['slot_id']
        row=lookup[slot]
        seen=set();n=0;best=float('-inf');record_best=float('-inf')
        for i,tool in enumerate(trace['tool_calls'],1):
            valid=independent.finite(tool['performance'])
            visible=tool['visible_to_model']
            config=hashlib.sha256(json.dumps(numeric_normalize(tool['arguments']),sort_keys=True,separators=(',',':')).encode()).hexdigest()
            valid_visible=valid and visible
            repeated=config in seen if valid_visible else None
            if valid_visible:
                n+=1;seen.add(config)
            expected={k:row[k] for k in ('slot_id','model','task','regime','seed','rep')}
            expected.update(tool_index=i,tool_name=tool['name'],visible_to_model=visible,
                valid_performance=valid,delivered_valid=valid_visible,delivered_index=n if valid_visible else None,
                repeated_delivered_configuration=repeated,configuration_sha256=config,
                performance=tool['performance'] if valid else None,simulated_cost_seconds=tool['simulated_cost_seconds'])
            actual=attempt_rows.pop((slot,i))
            assert set(actual)==set(expected)
            for field,value in expected.items():check('evaluation_events.csv',slot+':'+str(i),field,actual[field],value)
            if valid_visible:
                p=tool['performance'];best=max(best,p);is_new=p>record_best+1e-12
                if is_new:record_best=p
                actual=delivered_rows.pop((slot,n))
                expected={k:row[k] for k in ('slot_id','model','task','regime','seed','rep')}
                expected.update(delivered_index=n,performance=p,is_new_record=is_new,best_so_far=best)
                assert set(actual)==set(expected)
                for field,value in expected.items():check('delivered_events.csv',slot+':'+str(n),field,actual[field],value)
    assert not attempt_rows and not delivered_rows
    report=dict(status='PASS' if not mismatches else 'FAIL', independent_canonical_reads=486,
        compared_fields_by_file=dict(checked),total_compared_fields=sum(checked.values()),mismatches=mismatches,
        verifier_sha256=hashlib.sha256(independent.Path(__file__).read_bytes()).hexdigest(),
        independent_extractor_sha256=hashlib.sha256(independent.Path(independent.__file__).read_bytes()).hexdigest(),
        source_files=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(P.glob('*.csv'))],
        score_semantics_caution='Two non-JSON DeepSeek model terminals have historical offline zero scores. Nonfallback score completeness is not valid JSON configuration submission.')
    (independent.OUT/'PUBLICATION_CHECKS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    assert not mismatches


if __name__=='__main__':main()
