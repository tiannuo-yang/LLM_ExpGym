#!/usr/bin/env python3
"""Rebuild the requested N4 rollback from two immutable public score cohorts.

No model calls, Git objects, private trajectories or external Python packages
are required. Selection is by system only, never by the resulting score.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PRIOR = '7776f700902db194c69124b1a5f59d985379cfb3'
HISTORICAL = '297c3d00a006f33fc5a8ca799ce91d327d92839e'
IDENTITY = 'official-n4-rollback-20260919'
ROLLBACK_CODE_COMMIT = 'ba4b39ed46b445288c2ba04f65dade33621c64a5'
PINNED_SELECTION_INPUTS = {
    'results/gemini-openrouter-20260917/main/slot_scalars.csv': '884ddd3369c57ea1dfe0a3d03e3694b17c9613c39a1bfaddbfb1e2da1187dbbf',
    'results/gemini-openrouter-20260917/main/SOURCE_SELECTION.csv': 'fb52849c2967ead9c5fd1a0e29e4177fe441203c899cb8a6fed58b4c7e7c7a9c',
    'results/protocol-repair-20260918/main/slot_scalars.csv': 'acd86425eef098dab8a8f89307afbca52b7a34d856cae8f5b174577e6572fbe0',
    'results/protocol-repair-20260918/main/SOURCE_SELECTION.csv': 'b6a28c7414714dfdf3975519cd52c42730209ed7206f65e34478a6d136099144',
}


def rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        out = csv.DictWriter(stream, fields or list(data[0]), lineterminator='\n')
        out.writeheader()
        out.writerows(data)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def select(repo, output):
    for path, expected in PINNED_SELECTION_INPUTS.items():
        assert sha(repo/path) == expected, ('Frozen selection input changed', path)
    original = repo / 'results/gemini-openrouter-20260917/main'
    previous = repo / 'results/protocol-repair-20260918/main'
    old = rows(original / 'slot_scalars.csv')
    last = rows(previous / 'slot_scalars.csv')
    old_sources = rows(original / 'SOURCE_SELECTION.csv')
    last_sources = rows(previous / 'SOURCE_SELECTION.csv')
    index_old = {r['slot_id']: r for r in old}
    index_last = {r['slot_id']: r for r in last}
    sources_old = {r['slot_id']: r for r in old_sources}
    sources_last = {r['slot_id']: r for r in last_sources}
    assert len(old) == len(last) == len(index_old) == len(index_last) == 4698
    assert index_old.keys() == index_last.keys() == sources_old.keys() == sources_last.keys()
    selected, selected_sources, comparison = [], [], []
    source_fields = list(dict.fromkeys([*old_sources[0], *last_sources[0],
                                      'adoption_layer', 'adoption_source_commit', 'adoption_reason']))
    for historical in old:
        sid = historical['slot_id']
        prior = index_last[sid]
        assert historical['system'] == prior['system']
        n1 = prior['system'] == 'expgym'
        assert n1 or prior['system'] == 'poolact'
        chosen = dict(prior if n1 else historical)
        source = sources_last[sid] if n1 else sources_old[sid]
        reason = ('retain_all_2502_n1_scores_and_sources_from_7776f70' if n1 else
                  'restore_all_2196_n4_scores_and_sources_from_297c3d0_including_naive_cached_poolact')
        selected.append(chosen)
        output_source = {field: source.get(field, '') for field in source_fields}
        output_source.update(adoption_layer='retained_n1_repair' if n1 else 'restored_n4_historical',
                             adoption_source_commit=PRIOR if n1 else HISTORICAL,
                             adoption_reason=reason)
        selected_sources.append(output_source)
        before_metrics = json.loads(prior['metrics_json'])
        after_metrics = json.loads(chosen['metrics_json'])
        changed_fields = sorted(key for key in before_metrics.keys() | after_metrics.keys()
                                if before_metrics.get(key) != after_metrics.get(key))
        primary_key = ({'restricted_search': 'f1', 'evidence_audit': 'evidence_acc', 'tuning': 'gap0'}
                       if n1 else {'restricted_search': 'f1_mv', 'evidence_audit': 'evidence_acc_mv', 'tuning': 'gap0_mi'})[prior['scenario']]
        comparison.append(dict(slot_id=sid, model=chosen['model'], system=chosen['system'],
                               scenario=chosen['scenario'], regime=chosen['regime'], strategy=chosen['strategy'],
                               adoption_reason=reason,
                               previous_score_identity='official-protocol-repair-v1',
                               current_score_identity=IDENTITY,
                               previous_metrics_json=prior['metrics_json'], current_metrics_json=chosen['metrics_json'],
                               metrics_changed=bool(changed_fields), changed_metric_keys=';'.join(changed_fields),
                               primary_metric=primary_key,
                               primary_score_changed=before_metrics.get(primary_key) != after_metrics.get(primary_key),
                               previous_source_sha256=sources_last[sid]['result_sha256'],
                               current_source_sha256=source['result_sha256'],
                               source_changed=sources_last[sid]['result_sha256'] != source['result_sha256'],
                               previous_score_complete=prior['score_complete'],
                               current_score_complete=chosen['score_complete']))
    assert sum(r['system'] == 'expgym' for r in selected) == 2502
    assert sum(r['system'] == 'poolact' for r in selected) == 2196
    assert all(r == index_last[r['slot_id']] for r in selected if r['system'] == 'expgym')
    assert all(r == index_old[r['slot_id']] for r in selected if r['system'] == 'poolact')
    for r in selected_sources:
        source = sources_last[r['slot_id']] if r['system'] == 'expgym' else sources_old[r['slot_id']]
        assert all(r[k] == v for k, v in source.items())
    destination = output / 'selection'
    write(destination / 'slot_scalars.csv', selected)
    write(destination / 'SOURCE_SELECTION.csv', selected_sources, source_fields)
    write(destination / 'sample_rollback.csv', comparison)
    manifest = dict(status='PASS', adoption_policy='retain_7776_n1_restore_297_n4',
                    score_identity=IDENTITY, total_main_runtime_adoption=False,
                    rollback_selection_verified=True, retained_n1_slots=2502, restored_n4_slots=2196,
                    withdrawn_main_n4_runtime_replacements=116, withdrawn_hpo_pool_replacements=97,
                    withdrawn_search_audit_n4_replacements=19, retained_main_n1_runtime_replacements=2,
                    runtime_reruns_performed_by_this_rollback=0,
                    selected_scalars_sha256=sha(destination / 'slot_scalars.csv'),
                    selected_sources_sha256=sha(destination / 'SOURCE_SELECTION.csv'),
                    changed_metric_slots=sum(r['metrics_changed'] for r in comparison),
                    changed_primary_metric_slots=sum(r['primary_score_changed'] for r in comparison),
                    changed_source_slots=sum(r['source_changed'] for r in comparison),
                    n1_fields_retained_exactly=True, n4_fields_restored_exactly=True,
                    all_three_n4_strategies_restored=True,
                    no_score_based_selection=True, all_gemini_backfills_retained=True,
                    retained_whois_sweep='results/protocol-repair-20260918/whois',
                    archived_repair_commit=PRIOR, restored_n4_commit=HISTORICAL,
                    inputs=[dict(path=str(path.relative_to(repo)), sha256=sha(path))
                            for path in (original/'slot_scalars.csv', original/'SOURCE_SELECTION.csv',
                                         previous/'slot_scalars.csv', previous/'SOURCE_SELECTION.csv')])
    assert manifest['changed_source_slots'] == 116
    dump(destination / 'ROLLBACK_MANIFEST.json', manifest)
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True, help='New empty output directory')
    ap.add_argument('--code-commit', default=ROLLBACK_CODE_COMMIT,
                    help='Fixed rollback code commit; does not relabel historical execution versions')
    ap.add_argument('--selection-only', action='store_true')
    args = ap.parse_args()
    repo, out = args.repo.resolve(), args.output.resolve()
    assert not out.exists(), 'Use a fresh output directory'
    out.mkdir(parents=True)
    manifest = select(repo, out)
    if args.selection_only:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return
    scripts = Path(__file__).resolve().parent

    def run(script, *arguments):
        subprocess.run([sys.executable, str(scripts/script), *map(str, arguments)],
                       check=True, stdout=subprocess.DEVNULL)

    run('rebuild_analysis.py', '--repo', repo,
        '--baseline', repo/'results/gemini-openrouter-20260917/main',
        '--scalars', out/'selection/slot_scalars.csv', '--selection', out/'selection/SOURCE_SELECTION.csv',
        '--output', out/'main', '--score-identity', IDENTITY,
        '--code-commit', args.code_commit,
        '--adoption-state', 'official', '--fairness-manifest', out/'selection/ROLLBACK_MANIFEST.json')
    run('recompute_display.py', '--source', out/'main', '--output', out/'display')
    run('rebuild_secondary.py', '--repo', repo, '--source', out/'main', '--output', out/'secondary')
    for directory in ('search', 'poolact', 'cases'):
        shutil.move(str(out/'secondary'/directory), str(out/directory))
    shutil.move(str(out/'secondary/CHECKS.json'), str(out/'SECONDARY_CHECKS.json'))
    (out/'secondary').rmdir()
    run('build_audit_rollback.py', '--repo', repo, '--output', out/'audit',
        '--main-scalars', out/'main/slot_scalars.csv', '--main-selection', out/'main/SOURCE_SELECTION.csv')
    run('render_report.py', '--repo', repo, '--main', out/'main', '--display', out/'display',
        '--secondary', out, '--audit', out/'audit',
        '--hpo', repo/'results/protocol-repair-20260918/hpo_behavior/official_rescored486',
        '--existing-rescore', repo/'results/protocol-repair-20260918/rescore/main', '--output', out/'docs')
    shutil.copyfile(out/'docs/conclusion_delta.csv', out/'conclusion_delta.csv')
    prior_conclusions={r['conclusion']:r for r in rows(repo/'results/protocol-repair-20260918/conclusion_delta.csv')}
    current_conclusions=rows(out/'conclusion_delta.csv')
    conclusion_rows=[]
    for row in current_conclusions:
        previous=prior_conclusions[row['conclusion']]
        conclusion_rows.append(dict(conclusion=row['conclusion'], previous=previous['new'], current=row['new'],
                                    changed=previous['new'] != row['new'], unit=row['unit'], evidence=row['evidence'],
                                    previous_identity='official-protocol-repair-v1', current_identity=IDENTITY))
    write(out/'rollback_conclusion_delta.csv',conclusion_rows)
    findings = json.loads((out/'main/FINDINGS.json').read_text())
    (out/'README.zh.md').write_text(f'''# POOLACT 回退交付（2026-09-19）

[当前主报告](../paper-analysis-20260916/README.zh.md) · [完整比较 CSV](main/COMPARISON.csv) · [逐样本回退对照](selection/sample_rollback.csv)

本版恢复全部 **2,196 个 N4 槽位**的修复前结果与来源，覆盖 naive、cached、POOLACT 三种策略和已补齐的 Gemini。**2,502 个 N1 槽位**保留 `7776f70` 的分数与来源，包括单体终答修复、两个 Audit 实际控制流补跑、Gemini 补齐和 486 条 HPO 行为。独立 Whois N1 sweep 也保持不变。

这次是完整范围的版本回退；未调用模型，未按分数挑选槽位或拼接池成员。旧运行仍保持真实的执行版本，不标为由当前代码重新生成。此前诊断和修复候选独立留作历史材料，当前 N4 采用既有运行结果。

相对上一正式版 `7776f70`，共有 **{manifest['changed_metric_slots']}** 个槽位的任一指标改变，其中 **{manifest['changed_primary_metric_slots']}** 个论文主指标改变；**{manifest['changed_source_slots']}** 个来源恢复为旧原件。所有变化均属于 N4，N1 逐字段不变。恢复的运行来源包括 97 个 HPO 池和 19 个 Search/Audit N4 槽位。

POOLACT 高于两基线的组合数恢复为 **{findings['poolact']['all']['poolact_above_both']}/36**，Tight 为 **{findings['poolact']['tight']['poolact_above_both']}/18**。[相对回退前 7776f70 的结论对照](rollback_conclusion_delta.csv)与[相对 297c3d0 的结论对照](conclusion_delta.csv)分别列出，避免混淆比较基准。

| 内容 | 入口 |
| --- | --- |
| 4,698 个标量、原件 SHA、逐槽恢复原因 | [selection](selection/ROLLBACK_MANIFEST.json)、[来源](main/SOURCE_SELECTION.csv) |
| 7,767 行聚合、126 行排名、1,298 行比较 | [main](main/CHECKS.json)、[排名](main/dimension_rankings.csv)、[比较](main/COMPARISON.csv) |
| N1 主成绩与 regret | [展示表](display/n1_main.csv)、[逐任务 regret](display/hpo_task_regret.csv) |
| N4 三策略全部指标和主增益 | [全部指标](poolact/poolact_all_metrics.csv)、[主增益](poolact/poolact_primary.csv) |
| Audit：N1 当前、N4 历史的行为与证据 | [方法与重放](audit/README.zh.md) |
| 保留的 486 条 HPO 行为导出 | [行为 CSV](../protocol-repair-20260918/hpo_behavior/README.zh.md) |
| 保留的 Whois sweep | [预算表与图](../protocol-repair-20260918/whois/README.zh.md) |
| 当前代码回退清单 | [源码恢复与N1保留](review/CODE_SOURCE_MANIFEST.json)；固定代码提交 `ba4b39ed46b445288c2ba04f65dade33621c64a5` |
| 本次公开构建核验 | [CHECKS](CHECKS.json)、[独立采用规则](selection/ROLLBACK_MANIFEST.json) |

公开重建只需 Python 标准库，在仓库根目录执行：

```bash
python3 results/poolact-rollback-20260919/tools/rebuild_rollback.py --repo . --output /tmp/poolact-rollback-rebuilt
```

输出包括选择、主表、展示、Search、POOLACT、案例、Audit 的全量重建及 `docs/` 三份报告。四份分数/来源输入均固定 SHA256；N1/N4 按 system 字段确定性选择。Audit 从对应版本的公开假设/成员叶表重建 31 张 CSV，并与主表检查来源和 LA/EA。此命令复算选择及聚合，不重新调用模型或重新执行已撤回的 N4 评分器。

[7776f70 完整历史交付](https://github.com/tiannuo-yang/LLM_ExpGym/tree/7776f700902db194c69124b1a5f59d985379cfb3/results/protocol-repair-20260918)保留旧分、诊断、修复评分、修复补跑、行为、代码与复算材料；仓库中的 `results/protocol-repair-20260918/` 保持原字节。本包独立采用清单明确 `total_main_runtime_adoption=false`，不会把修复版的 97 池完成闸门冒充本次采用依据。
''')
    checks = dict(status='PASS', main_slots=4698, retained_n1_slots=2502, restored_n4_slots=2196,
                  input_manifest='selection/ROLLBACK_MANIFEST.json', model_calls=0,
                  historical_protocol_repair_package_modified=False,
                  main_aggregates=json.loads((out/'main/CHECKS.json').read_text()),
                  audit=json.loads((out/'audit/CHECKS.json').read_text()),
                  findings=findings,
                  scripts=[dict(path=str(path.relative_to(repo)), sha256=sha(path))
                           for path in sorted(scripts.glob('*.py'))],
                  outputs=[dict(path=str(path.relative_to(out)), sha256=sha(path))
                           for path in sorted(out.rglob('*')) if path.is_file()])
    dump(out/'CHECKS.json', checks)
    print(json.dumps({k: checks[k] for k in ('status','main_slots','retained_n1_slots','restored_n4_slots','model_calls')}, indent=2))


if __name__ == '__main__':
    main()
