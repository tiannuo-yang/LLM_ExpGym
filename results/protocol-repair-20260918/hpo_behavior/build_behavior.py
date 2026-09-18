#!/usr/bin/env python3
"""Rebuild observed HPO N1 behavior, preserving historical and repaired scores.

No model calls or trajectory mutation.  Full mode verifies and reads all 486
adopted records.  Public replay mode rebuilds group/pair tables from exported
per-trajectory CSVs; raw-source SHA256 verification still requires local archives.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    assert rows, path
    with path.open('w', newline='') as f:
        out = csv.DictWriter(f, fieldnames=list(rows[0]))
        out.writeheader()
        out.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def canon(v):
    if isinstance(v, dict):
        return tuple(sorted((k, canon(x)) for k, x in v.items()))
    if isinstance(v, list):
        return tuple(canon(x) for x in v)
    return v


def configuration_digest(v):
    # Match canonical numerical equivalence used in historical distinct counts.
    def normalize(x):
        if isinstance(x, dict): return {k:normalize(v) for k,v in sorted(x.items())}
        if isinstance(x, list): return [normalize(v) for v in x]
        if isinstance(x, (int,float)) and math.isfinite(x) and int(x)==x: return int(x)
        return x
    return hashlib.sha256(json.dumps(normalize(v),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def scientific_key(row):
    return row['model'], row['task'], row['regime'], int(row['seed']), int(row['rep'])


def extract(slot, trace, source_path, old=None):
    task, outcome = trace['task'], trace['outcome']
    assert task['scenario'] == 'tuning'
    assert outcome['terminal_status']['execution_complete']
    calls = trace['tool_calls']
    assert all(t['name'] == 'evaluate_config' for t in calls)
    visible = [t for t in calls if t['visible_to_model']]
    delivered = [t for t in visible if isinstance(t.get('performance'), (int, float)) and math.isfinite(t['performance'])]
    unique = {canon(t['arguments']) for t in delivered}
    perfs = [t['performance'] for t in delivered]
    best = max(perfs) if perfs else None
    first_best = perfs.index(best) + 1 if perfs else None
    records, running = [], -float('inf')
    for i, p in enumerate(perfs, 1):
        if p > running + 1e-12:
            records.append(i)
            running = p
    budget = task['budget']['limit_seconds']
    valid_cost = sum(t['simulated_cost_seconds'] for t in delivered)
    final = outcome['score']['value']
    reason = outcome['termination_reason']
    reason_class = ('budget' if reason == 'time_budget_exceeded' else
                    'cap' if reason in ('max_steps_reached', 'max_evaluations_reached') else
                    'natural' if reason == 'natural_answer' else 'other')
    task_id = task['item']['id']
    score_source = outcome.get('answer_score_source')
    try: final_json_object=isinstance(json.loads(outcome.get('answer') or ''),dict)
    except (ValueError,TypeError): final_json_object=False
    row = dict(model=slot['model'], cohort=old['cohort'] if old else slot['cohort_id'],
               task=task_id, family=task_id.split(':')[1], regime=task['budget']['regime'],
               seed=trace['run']['seed'], rep=task['rep'], termination=reason,
               termination_class=reason_class, answer_source=outcome['answer_source'],
               score_cost_basis=outcome['score_cost_basis'], answer_score_source=score_source,
               score_status=outcome.get('score_status'), score_complete=outcome['terminal_status']['score_complete'],
               max_steps=task['limits']['max_steps'], max_evaluations=task['limits']['max_evaluations'],
               agent_steps=outcome.get('agent_steps'), attempted_evaluations=len(calls),
               delivered_evaluations=len(delivered), unique_delivered_configs=len(unique),
               repeated_delivered_evaluations=len(delivered)-len(unique),
               withheld_evaluations=len(calls)-len(visible), visible_error_results=len(visible)-len(delivered),
               limit_seconds=budget, delivered_cost_seconds=valid_cost,
               delivered_budget_fraction=valid_cost/budget if budget else None,
               best_observed_performance=best, first_best_observation_index=first_best,
               first_best_fraction=first_best/len(delivered) if first_best else None,
               observations_after_first_best=len(delivered)-first_best if first_best else None,
               strict_record_improvements=max(0,len(records)-1),
               best_performance_gain_after_first3=(best-max(perfs[:3])) if perfs else None,
               best_performance_gain_after_first5=(best-max(perfs[:5])) if perfs else None,
               observed_best_reached_by_first3=(first_best <= 3) if first_best else None,
               observed_best_reached_by_first5=(first_best <= 5) if first_best else None,
               observed_best_reached_in_first_half=(first_best <= math.ceil(len(delivered)/2)) if first_best else None,
               final_performance=final,
               final_below_observed_best=(final < best-1e-6) if best is not None and final is not None else None,
               final_above_observed_best=(final > best+1e-6) if best is not None and final is not None else None,
               trace_path=source_path, trace_sha256=slot['result_sha256'])
    row.update(slot_id=slot['slot_id'], outer_repeat=int(slot['outer_repeat']),
               source_selection=slot['selection'], source_cohort=slot['cohort_id'],
               source_commit=trace['provenance']['repository']['commit'],
               source_tree_sha256=trace['provenance']['repository'].get('source_tree_sha256'),
               source_dirty=trace['provenance']['repository'].get('dirty'),
               visible_results=len(visible), all_attempted_cost_seconds=sum(t['simulated_cost_seconds'] for t in calls),
               all_visible_cost_seconds=sum(t['simulated_cost_seconds'] for t in visible),
               model_final_present=bool(outcome.get('answer')) and outcome['answer_source'] in ('natural_model_answer','forced_model_answer'),
               nonfallback_terminal_scored=outcome['terminal_status']['score_complete'] and score_source in ('matching_tool_call','offline_final_answer'),
               submitted_json_object_scored=outcome['terminal_status']['score_complete'] and score_source in ('matching_tool_call','offline_final_answer') and final_json_object,
               final_json_object=final_json_object,
               fallback_scored=score_source == 'best_evaluated_fallback', scoring_version='historical_adopted')
    events = [dict(model=row['model'], task=task_id, regime=row['regime'], seed=row['seed'],
                   delivered_index=i, performance=p, is_new_record=i in records,
                   best_so_far=max(perfs[:i]), slot_id=slot['slot_id'], rep=row['rep'])
              for i,p in enumerate(perfs,1)]
    attempted_events=[]
    seen_configs=set(); delivered_index=0
    for i,t in enumerate(calls,1):
        valid=isinstance(t.get('performance'),(int,float)) and math.isfinite(t['performance'])
        delivered_valid=t['visible_to_model'] and valid
        config=configuration_digest(t['arguments'])
        repeated=config in seen_configs if delivered_valid else None
        if delivered_valid:
            delivered_index+=1
            seen_configs.add(config)
        attempted_events.append(dict(slot_id=slot['slot_id'],model=row['model'],task=task_id,regime=row['regime'],
            seed=row['seed'],rep=row['rep'],tool_index=i,tool_name=t['name'],visible_to_model=t['visible_to_model'],
            valid_performance=valid,delivered_valid=delivered_valid,delivered_index=delivered_index if delivered_valid else None,
            repeated_delivered_configuration=repeated,configuration_sha256=config,
            performance=t.get('performance') if valid else None,simulated_cost_seconds=t['simulated_cost_seconds']))
    return row, events, attempted_events


OLD_MEAN_FIELDS = ('delivered_evaluations','unique_delivered_configs','repeated_delivered_evaluations',
                   'withheld_evaluations','delivered_budget_fraction','first_best_fraction',
                   'observations_after_first_best','strict_record_improvements',
                   'best_performance_gain_after_first3','best_performance_gain_after_first5')
OLD_BOOL_FIELDS = ('final_below_observed_best','final_above_observed_best',
                   'observed_best_reached_by_first3','observed_best_reached_by_first5',
                   'observed_best_reached_in_first_half')


def summarize(rows, fields):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in fields)].append(row)
    out=[]
    for key, rs in sorted(groups.items()):
        item = dict(zip(fields,key))
        item.update(n=len(rs), score_complete_n=sum(r['score_complete'] for r in rs),
                    delivered_total=sum(r['delivered_evaluations'] for r in rs),
                    repeated_delivered_total=sum(r['repeated_delivered_evaluations'] for r in rs))
        fractions=[r['delivered_budget_fraction'] for r in rs if r['termination_class']=='natural' and r['delivered_budget_fraction'] is not None]
        item['natural_stop_budget_fraction_mean']=mean(fractions) if fractions else None
        item['natural_stop_budget_fraction_median']=median(fractions) if fractions else None
        for reason in ('natural','budget','cap','other'):
            item[reason+'_n']=sum(r['termination_class']==reason for r in rs)
        for field in OLD_MEAN_FIELDS+('attempted_evaluations','visible_results','visible_error_results','agent_steps','all_attempted_cost_seconds','all_visible_cost_seconds'):
            values=[r[field] for r in rs if r[field] is not None]
            item[field+'_mean']=mean(values) if values else None
            item[field+'_median']=median(values) if values else None
        for field in OLD_BOOL_FIELDS+('model_final_present','nonfallback_terminal_scored','submitted_json_object_scored','final_json_object','fallback_scored'):
            values=[r[field] for r in rs if r[field] is not None]
            item[field+'_n']=sum(values)
            item[field+'_denom']=len(values)
        item['score_source_counts']=json.dumps(dict(sorted(Counter(r['answer_score_source'] or 'missing' for r in rs).items())))
        item['score_complete_fraction']=item['score_complete_n']/len(rs)
        item['nonfallback_terminal_scored_fraction']=item['nonfallback_terminal_scored_n']/len(rs)
        item['submitted_json_object_scored_fraction']=item['submitted_json_object_scored_n']/len(rs)
        for field in ('attempted_evaluations','visible_results','visible_error_results','withheld_evaluations','unique_delivered_configs'):
            item[field+'_total']=sum(r[field] for r in rs)
        out.append(item)
    return out


GROUPS={'by_model_regime.csv':('model','regime'), 'by_family_regime.csv':('family','regime'),
        'by_regime.csv':('regime',), 'by_model_family_regime.csv':('model','family','regime')}


def build_tables(rows):
    tables={name:summarize(rows,fields) for name,fields in GROUPS.items()}
    paired=defaultdict(dict)
    for row in rows:
        paired[(row['model'],row['task'],row['seed'],row['rep'])][row['regime']]=row
    pairs=[]
    for key, regimes in sorted(paired.items()):
        if not all(r in regimes for r in ('cost_free','cost_tight')):
            continue
        free,tight=regimes['cost_free'],regimes['cost_tight']
        pairs.append(dict(model=key[0],task=key[1],seed=key[2],rep=key[3],
                          free_delivered=free['delivered_evaluations'],tight_delivered=tight['delivered_evaluations'],
                          free_stopping=free['termination_class'],tight_stopping=tight['termination_class'],
                          free_first_best=free['first_best_observation_index'],tight_first_best=tight['first_best_observation_index'],
                          free_final=free['final_performance'],tight_final=tight['final_performance'],
                          free_slot_id=free['slot_id'],tight_slot_id=tight['slot_id'],
                          free_score_complete=free['score_complete'],tight_score_complete=tight['score_complete']))
    tables['free_tight_pairs.csv']=pairs
    matched=[r for r in rows if r['regime'] in ('cost_free','cost_tight') and all(k in paired[(r['model'],r['task'],r['seed'],r['rep'])] for k in ('cost_free','cost_tight'))]
    tables['matched_free_tight_by_regime.csv']=summarize(matched,('regime',))
    tables['matched_free_tight_by_model.csv']=summarize(matched,('model','regime'))
    return tables


def termination_table(rows):
    counts=Counter((r['model'],r['regime'],r['termination'],r['termination_class']) for r in rows)
    return [dict(model=k[0],regime=k[1],termination=k[2],termination_class=k[3],n=n)
            for k,n in sorted(counts.items())]


def same_value(x,y):
    if x is None: x=''
    if y is None: y=''
    if str(x)==str(y): return True
    try: return math.isclose(float(x),float(y),rel_tol=1e-12,abs_tol=1e-12)
    except (ValueError,TypeError): return False


def compare_tables(old, new, fields, table, only_old_fields=False):
    a={tuple(str(r[f]) for f in fields):r for r in old}
    b={tuple(str(r[f]) for f in fields):r for r in new}
    out=[]
    for key in sorted(a.keys()|b.keys()):
        x,y=a.get(key,{}),b.get(key,{})
        for field in sorted((x.keys() if only_old_fields else x.keys()|y.keys())-set(fields)):
            xv,yv=x.get(field),y.get(field)
            try: delta=float(yv)-float(xv)
            except (ValueError,TypeError): delta=None
            out.append(dict(table=table, group=json.dumps(dict(zip(fields,key)),sort_keys=True),metric=field,
                            old=xv,new=yv,delta=delta,changed=not same_value(xv,yv)))
    return out


TEXT_FIELDS={'model','cohort','task','family','regime','termination','termination_class','answer_source',
             'score_cost_basis','answer_score_source','score_status','trace_path','trace_sha256','slot_id',
             'source_selection','source_cohort','source_commit','source_tree_sha256','scoring_version'}


def typed_csv(path):
    rows=read_csv(path)
    for row in rows:
        for k,v in row.items():
            if k in TEXT_FIELDS: continue
            if v=='': row[k]=None
            elif v in ('True','False'): row[k]=v=='True'
            else:
                try: row[k]=int(v)
                except ValueError:
                    try: row[k]=float(v)
                    except ValueError: pass
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path)
    p.add_argument('--workspace-root',type=Path)
    p.add_argument('--frozen-delivery',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--replay-trajectories',type=Path)
    args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    if args.replay_trajectories:
        rows=typed_csv(args.replay_trajectories)
        tables=build_tables(rows)
        tables['termination_reasons.csv']=termination_table(rows)
        for name,rs in tables.items(): write_csv(args.output/name,rs)
        write_json(args.output/'REPLAY_CHECKS.json',dict(status='PASS',traces=len(rows),input_sha256=sha(args.replay_trajectories),tables={name:len(rs) for name,rs in tables.items()}))
        print(json.dumps({'replay':'PASS','traces':len(rows)})); return
    assert args.repo and args.workspace_root and args.frozen_delivery
    base=args.repo/'results/gemini-openrouter-20260917/main'
    frozen=args.repo/'results/paper-analysis-20260916/hpo'
    selection=read_csv(base/'SOURCE_SELECTION.csv')
    slots=[s for s in selection if s['system']=='expgym' and s['scenario']=='tuning']
    new={x['slot_id']:x for x in json.loads((base/'INPUTS.json').read_text())['new_results']}
    old_rows=read_csv(frozen/'trajectories.csv'); old={scientific_key(r):r for r in old_rows}
    rows=[]; events=[]; attempted_events=[]; inventory=[]; comparisons=[]
    for s in slots:
        if s['historical_trajectory']:
            path=args.frozen_delivery/s['historical_trajectory']
            portable='frozen_delivery/'+s['historical_trajectory']
        else:
            historical=Path(new[s['slot_id']]['path'])
            # Historical manifest has absolute producer paths. Use only its
            # workspace-relative suffix, and require explicit archive root.
            suffix=str(historical).split('/gemini_openrouter_20260917/',1)[1]
            portable='gemini_openrouter_20260917/'+suffix
            path=args.workspace_root/portable
        raw=path.read_bytes(); actual=hashlib.sha256(raw).hexdigest()
        assert actual==s['result_sha256'],(s['slot_id'],actual,s['result_sha256'])
        t=json.loads(raw)
        key=(s['model'],t['task']['item']['id'],t['task']['budget']['regime'],t['run']['seed'],t['task']['rep'])
        row,ev,attempted=extract(s,t,portable,old.get(key)); rows.append(row);events.extend(ev);attempted_events.extend(attempted)
        if key in old:
            for f,v in old[key].items():
                if f=='trace_path': continue
                comparisons.append(dict(slot_id=s['slot_id'],field=f,old=v,new=row[f],equal=same_value(v,row[f])))
        inventory.append(dict(slot_id=s['slot_id'],model=s['model'],task=s['item'],regime=s['regime'],
                              seed=s['seed'],outer_repeat=s['outer_repeat'],selection=s['selection'],
                              source_path=portable,sha256=actual,bytes=len(raw),source_commit=row['source_commit'],
                              source_tree_sha256=row['source_tree_sha256'],source_dirty=row['source_dirty']))
    rows.sort(key=scientific_key); events.sort(key=lambda r:(r['model'],r['task'],r['regime'],r['seed'],r['rep'],r['delivered_index']))
    attempted_events.sort(key=lambda r:(r['model'],r['task'],r['regime'],r['seed'],r['rep'],r['tool_index']))
    assert len(rows)==486 and len({scientific_key(r) for r in rows})==486
    assert set(Counter(r['model'] for r in rows).values())=={81}
    assert set(Counter(r['regime'] for r in rows).values())=={162}
    assert len(comparisons)==480*(len(old_rows[0])-1)
    assert all(r['equal'] for r in comparisons), [r for r in comparisons if not r['equal']][:5]
    added=[r for r in rows if scientific_key(r) not in old]
    assert len(added)==6 and all(r['model']=='gemini-3.8-flash-medium' for r in added)
    out=args.output/'observed_behavior486'
    write_csv(out/'trajectories.csv',rows);write_csv(out/'delivered_events.csv',events)
    write_csv(out/'evaluation_events.csv',attempted_events)
    tables=build_tables(rows)
    tables['termination_reasons.csv']=termination_table(rows)
    for name,rs in tables.items():write_csv(out/name,rs)
    write_csv(args.output/'SOURCE_SELECTION.csv',inventory)
    write_csv(args.output/'added_gemini_six.csv',added)
    old_subset=[r for r in rows if scientific_key(r) in old]
    old_tables=build_tables(old_subset)
    differences=[];reproduction=[]
    for name,fields in list(GROUPS.items())+[('matched_free_tight_by_regime.csv',('regime',)),('matched_free_tight_by_model.csv',('model','regime'))]:
        historic=read_csv(frozen/name)
        reproduction.extend(compare_tables(historic,old_tables[name],fields,name,True))
        differences.extend(compare_tables(old_tables[name],tables[name],fields,name))
    historic_pairs=read_csv(frozen/'free_tight_pairs.csv')
    reproduction.extend(compare_tables(historic_pairs,old_tables['free_tight_pairs.csv'],('model','task','seed','rep'),'free_tight_pairs.csv',True))
    assert all(not x['changed'] for x in reproduction), [x for x in reproduction if x['changed']][:5]
    write_csv(args.output/'old480_reproduction.csv',reproduction)
    write_csv(args.output/'old480_vs_observed486.csv',differences)
    write_json(args.output/'CHECKS.json',dict(schema='expgym.hpo-observed-behavior.v2',status='PASS',
        observed_traces=486,frozen_traces_reproduced=480,new_gemini_traces=6,model_counts=dict(Counter(r['model'] for r in rows)),
        regime_counts=dict(Counter(r['regime'] for r in rows)), old_trajectory_field_checks=len(comparisons),
        old_aggregate_field_checks=len(reproduction),old_field_mismatches=0,source_hashes_checked=486,
        free_tight_pairs_old=len(historic_pairs),free_tight_pairs_new=len(tables['free_tight_pairs.csv']),
        delivered_events=len(events),attempted_evaluation_events=len(attempted_events),historical_score_complete=sum(r['score_complete'] for r in rows),
        script_sha256=sha(Path(__file__)),inputs={str(x.relative_to(args.repo)):sha(x) for x in (base/'SOURCE_SELECTION.csv',base/'INPUTS.json',frozen/'trajectories.csv')},
        limits='Observed actions are unchanged. This output uses historical adopted scores; repaired scores are a separate join. Hidden performance never enters best-observed metrics. Score complete includes legacy best-evaluated fallback; nonfallback_terminal_scored excludes fallback but includes two non-JSON zero-score terminals. submitted_json_object_scored also requires a JSON object; JSON shape alone does not certify valid task configuration.'))
    print(json.dumps({'status':'PASS','traces':486,'events':len(events),'old_fields_checked':len(comparisons),'aggregate_fields_checked':len(reproduction)},indent=2))


if __name__=='__main__':
    main()
