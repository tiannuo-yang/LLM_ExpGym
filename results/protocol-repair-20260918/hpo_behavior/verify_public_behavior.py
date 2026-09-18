#!/usr/bin/env python3
"""Verify public HPO per-evaluation exports and deterministic group replay."""
import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


def rows(p):
    with p.open(newline='') as f: return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--behavior',type=Path,required=True)
    p.add_argument('--events',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    events=rows(a.events or a.behavior/'evaluation_events.csv')
    grouped=defaultdict(list)
    for event in events:grouped[event['slot_id']].append(event)
    trajectories=rows(a.behavior/'trajectories.csv')
    checks=0
    for r in trajectories:
        ev=sorted(grouped[r['slot_id']],key=lambda x:int(x['tool_index']))
        assert [int(e['tool_index']) for e in ev]==list(range(1,len(ev)+1))
        visible=[e for e in ev if e['visible_to_model']=='True']
        delivered=[e for e in ev if e['delivered_valid']=='True']
        perfs=[float(e['performance']) for e in delivered]
        unique={e['configuration_sha256'] for e in delivered}
        expected=dict(attempted_evaluations=len(ev),visible_results=len(visible),
            delivered_evaluations=len(delivered),unique_delivered_configs=len(unique),
            repeated_delivered_evaluations=len(delivered)-len(unique),
            withheld_evaluations=len(ev)-len(visible),visible_error_results=len(visible)-len(delivered),
            delivered_cost_seconds=sum(float(e['simulated_cost_seconds']) for e in delivered),
            all_attempted_cost_seconds=sum(float(e['simulated_cost_seconds']) for e in ev),
            all_visible_cost_seconds=sum(float(e['simulated_cost_seconds']) for e in visible))
        if perfs:
            expected['best_observed_performance']=max(perfs)
            expected['first_best_observation_index']=perfs.index(max(perfs))+1
        if r['limit_seconds']:
            expected['delivered_budget_fraction']=expected['delivered_cost_seconds']/float(r['limit_seconds'])
        for field,value in expected.items():
            assert math.isclose(float(r[field]),value,rel_tol=1e-12,abs_tol=1e-12),(r['slot_id'],field,r[field],value)
            checks+=1
        assert [int(e['delivered_index']) for e in delivered]==list(range(1,len(delivered)+1))
        assert sum(e['repeated_delivered_configuration']=='True' for e in delivered)==len(delivered)-len(unique)
    replay=[]
    with tempfile.TemporaryDirectory(prefix='expgym-hpo-behavior-') as tmp:
        out=Path(tmp)
        subprocess.run([sys.executable,str(Path(__file__).with_name('build_behavior.py')),
            '--replay-trajectories',str(a.behavior/'trajectories.csv'),'--output',str(out)],check=True,capture_output=True,text=True)
        for generated in sorted(out.glob('*.csv')):
            existing=a.behavior/generated.name
            assert generated.read_bytes()==existing.read_bytes(),generated.name
            replay.append(dict(file=generated.name,sha256=hashlib.sha256(generated.read_bytes()).hexdigest()))
    result=dict(status='PASS',traces=len(trajectories),evaluation_events=len(events),
        per_trace_event_field_checks=checks,byte_identical_replayed_tables=replay,
        limitation='Checks public extracted scalars/events; raw trace SHA256 verification is performed separately by build_behavior.py full mode.')
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','traces':len(trajectories),'event_fields':checks,'tables':len(replay)}))


if __name__=='__main__':main()
