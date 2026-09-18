#!/usr/bin/env python3
"""Read-only graph equivalence replay; does not recreate physical concurrency."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

# REQUIRES LOCAL ARCHIVES: this is not the public-table-only verifier.
import argparse
_archive_cli = argparse.ArgumentParser(description="Requires original private trajectories, frozen source trees and benchmark files; no model calls")
_archive_cli.add_argument('--workspace', required=True, help='Original archive workspace root; recorded source paths must resolve')
_archive_cli.add_argument('--output', required=True, help='Separate audit output directory; do not overwrite the public package')
_archive_args = _archive_cli.parse_args()
ROOT = Path(_archive_args.workspace).resolve()
OUT = Path(_archive_args.output).resolve()
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'LLM_ExpGym-lightweight-20260917'))
REL = 'expgym/extras/parallel_cache.py'


def module(name, repo):
    path = ROOT / repo / REL
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj, hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old, old_sha = module('historical_v4_graph', 'LLM_ExpGym-eval-docs-20260912')
    gpt, gpt_sha = module('historical_gpt_v4_graph', 'LLM_ExpGym-gpt-material-rerun-20260912')
    new, new_sha = module('unified_v4_graph', 'LLM_ExpGym-protocol-repair-20260918')
    assert old_sha == gpt_sha == new_sha
    rows = list(csv.DictReader((ROOT / 'code_review_20260918/poolact/hpo_graph_slots.csv').open()))
    rows = [r for r in rows if r['protocol'] == 'paper-graph-lock-v4']
    assert len(rows) == 45
    totals = dict(pools=0, source_eval_records=0, replay_events=0, snapshots=0)
    per_pool = []
    for row in rows:
        path = Path(row['trajectory'])
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['trajectory_sha256']
        data = json.loads(raw)
        events = []
        budget = data['config']['time_budget']
        for aid, agent in enumerate(data['agent_results']):
            clock = 0.0
            for i, record in enumerate(agent['eval_records']):
                payload, key, perf, cost = record
                totals['source_eval_records'] += 1
                start = clock
                clock += cost
                # A controlled replay of saved evaluations; assertions compare
                # two implementations, not reconstructed physical scheduling.
                if clock < budget:
                    events.append((clock, aid, i, start, payload, perf, cost))
        events.sort()
        digest = hashlib.sha256()
        pool_snapshots = 0
        for diversity in (False, True):
            graphs = [m.SharedExplorationGraph(n_agents=4, diversity_mode=diversity)
                      for m in (old, gpt, new)]
            for clock, aid, i, start, payload, perf, cost in events:
                for m, graph in zip((old, gpt, new), graphs):
                    graph.record_claim('evaluate_config', payload, aid, start_time=start)
                    key, display, parsed_perf = m._parse_evaluate_config(
                        payload, 'perf={:.6f}, cost={:.0f}s'.format(perf, cost))
                    if key:
                        graph.record_evaluate_config(aid, key, display, parsed_perf,
                                                     cost, completion_time=clock)
                    graph.complete_claim('evaluate_config', payload, aid,
                                         completion_time=clock)
            for aid, agent in enumerate(data['agent_results']):
                for graph in graphs:
                    graph.record_end(aid, agent['answer'])
            times = sorted({0.0, budget / 4, budget / 2, budget, *[x[0] for x in events]})
            for visible_at in [None] + times:
                for aid in range(4):
                    outputs = [graph.format_for_injection(visible_before=visible_at,
                                agent_id=aid, completion_before=budget)
                               for graph in graphs]
                    assert outputs[0] == outputs[1] == outputs[2], (row['slot_id'], visible_at, aid)
                    digest.update(outputs[0].encode())
                    digest.update(b'\0')
                    pool_snapshots += 1
        totals['pools'] += 1
        totals['replay_events'] += len(events)
        totals['snapshots'] += pool_snapshots
        per_pool.append({**{k:row[k] for k in ['slot_id','model','item','regime','source_tree','trajectory_sha256']},
                         'events':len(events), 'snapshots':pool_snapshots,
                         'snapshot_stream_sha256':digest.hexdigest()})
    result = {'status':'PASS', 'graph_module_sha256':new_sha,
              'historical_eval_docs_equals_gpt_equals_unified_bytes':True,
              'scope':'All 45 historical v4 PoolAct sources hash-verified; controlled, common-order replay of saved eligible eval records. Full node rows, exploration paths, claims and visibility rendering compared byte-for-byte in both formats. This is implementation-equivalence evidence, not a reconstruction of real thread interleaving or real API inputs.',
              'counts':totals, 'pools':per_pool}
    (OUT / 'HISTORICAL_V4_EQUIVALENCE.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='pools'}, indent=2))


if __name__ == '__main__':
    main()
