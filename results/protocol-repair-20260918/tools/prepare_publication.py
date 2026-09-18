#!/usr/bin/env python3
"""Prepare an explicit publication allowlist without changing the live report.

Only generated public tables, analysis code and report candidates are listed.
Raw traces, API payloads, temporary drafts and arbitrary directory contents are
never included. Root publication can copy these named files after final gates.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MAIN=('CHECKS.json','COMPARISON.csv','FINDINGS.json','INPUTS.json','SCORE_VERSIONS.json','SOURCE_SELECTION.csv','absolute_settings.csv','all_aggregate_comparisons.csv','by_repeat.csv','changed_aggregate_fields.csv','conclusion_changes.csv','dimension_rankings.csv','main_expgym.csv','main_poolact.csv','ranking_changes.csv','slot_scalars.csv')
HISTORICAL=('absolute_settings.csv','by_repeat.csv','main_expgym.csv','main_poolact.csv','slot_scalars.csv','dimension_rankings.csv','FINDINGS.json')
DISPLAY=('CHECKS.json','budget_effects.csv','dimension_selection.csv','hpo_task_regret.csv','hpo_task_scores.csv','n1_main.csv','nas_best_minus_mean.csv','poolact_primary.csv','poolact_scenario_summary.csv')
SEARCH=('by_family_regime.csv','by_model_family_regime.csv','by_model_regime.csv','free_tight_paired.csv','overall_regime.csv','paired_direction_summary.csv','representative_case_index.csv','score_comparison.csv','trajectory_metrics.csv')
POOL=('poolact_all_metrics.csv','poolact_primary.csv','poolact_scenario_summary.csv')
CASES=('CASE_INDEX.zh.md','deepseek_delivery.csv','deepseek_delivery_transitions.csv','deepseek_paired_delivery.csv','fixed_case_scores.csv')
TOOLS=('rebuild_analysis.py','recompute_display.py','rebuild_secondary.py','render_report.py','prepare_publication.py')
DOCS=('README.zh.md','APPENDIX.zh.md','ABSTRACT.en.md')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--main',type=Path,required=True)
    ap.add_argument('--display',type=Path,required=True)
    ap.add_argument('--secondary',type=Path,required=True)
    ap.add_argument('--docs',type=Path,required=True)
    ap.add_argument('--tools',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--require-official',action='store_true')
    args=ap.parse_args()
    repo=args.repo.resolve()
    bundle=Path('results/protocol-repair-20260918')
    paper=Path('results/paper-analysis-20260916')
    versions=json.loads((args.main/'SCORE_VERSIONS.json').read_text())
    fairness=versions.get('runtime_fairness') or versions.get('hpo_fairness') or {}
    ready=versions['new']['adoption_state']=='official' and fairness.get('status')=='PASS' and fairness.get('adoption_ready') is True and fairness.get('total_main_runtime_adoption') is True
    if args.require_official:
        assert ready,'Do not publish partially completed runtime controls as adopted results'
    mapping=[]
    for directory,names,relative in [(args.main,MAIN,'main'),(args.main/'historical',HISTORICAL,'main/historical'),(args.display,DISPLAY,'display'),(args.secondary/'search',SEARCH,'search'),(args.secondary/'poolact',POOL,'poolact'),(args.secondary/'cases',CASES,'cases'),(args.tools,TOOLS,'tools')]:
        for name in names:
            mapping.append((directory/name,bundle/relative/name,'public_analysis'))
    mapping.extend([(args.secondary/'CHECKS.json',bundle/'SECONDARY_CHECKS.json','public_analysis'),(args.docs/'conclusion_delta.csv',bundle/'conclusion_delta.csv','public_analysis'),(args.docs/'RENDER_CHECKS.json',bundle/'RENDER_CHECKS.json','public_analysis')])
    for name in DOCS:
        mapping.append((args.docs/name,paper/name,'report_candidate_root_copies_only'))
    assert len({str(dest) for _,dest,_ in mapping})==len(mapping)
    manifest=[];virtual={}
    for source,dest,role in mapping:
        assert source.is_file(),source
        data=source.read_bytes()
        record=dict(source=str(source),destination=str(dest),role=role,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        manifest.append(record)
        virtual[(repo/dest).resolve()]=source
    links=[];missing=[]
    for source,dest,_ in mapping:
        if source.suffix!='.md':
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',source.read_text()):
            if target.startswith(('https://','http://','#','mailto:')):
                continue
            target=target.split('#',1)[0]
            actual=(repo/dest.parent/target).resolve()
            ok=actual in virtual or actual.is_file()
            links.append(dict(document=str(dest),target=target,exists=ok))
            if not ok:
                missing.append(links[-1])
    info=dict(schema='expgym.analysis-publication-allowlist.v1',adoption_ready=ready,status='PASS' if not missing else 'MISSING_LINK_TARGETS',files=manifest,file_count=len(manifest),total_bytes=sum(r['bytes'] for r in manifest),local_links_checked=len(links),missing_link_targets=missing,score_identity=versions['new']['identity'],core_code_commit=versions['new']['code_commit'],runtime_snapshot_commit=fairness.get('runtime_snapshot_commit'),writes_to_report=False,exclusions=['private trajectories','raw API requests/responses','answer overlays','draft outputs','__pycache__','credentials'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in info.items() if k!='files'},indent=2,ensure_ascii=False))
    if missing:
        raise SystemExit(1)

if __name__=='__main__':main()
