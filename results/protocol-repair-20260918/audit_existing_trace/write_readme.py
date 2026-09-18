#!/usr/bin/env python3
"""Render the Audit findings from computed tables, with no raw-data access."""
import argparse
import csv
import json
from pathlib import Path


def rows(path):
    return list(csv.DictReader(path.open()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.root
    old = {r['budget']: r for r in rows(root / 'old/n1/budget_metrics.csv')}
    new = {r['budget']: r for r in rows(root / 'n1/budget_metrics.csv')}
    populations = {r['score_version']: r for r in rows(root / 'changes/case_population.csv')}
    checks = json.loads((root / 'CHECKS.json').read_text())
    lines = ['# Audit：全量终答重评分后的证据与行为统计', '',
             '完整读取并校验 702 条 N1、468 个 N4 池（1,872 个成员），不是只修改已发现的异常案例。'
             'N1 共 11,934 个假设呈现；旧分数与旧分析保存在 `old/`，当前新规则结果在 `n1/` 和 `coordination/`。'
             '原始动作、实际可见反馈和轨迹文件没有改写。正式采用的评分版本与提交号以本交付总入口为准。', '',
             '## 证据质量的主要变化', '',
             '以下为等模型、等文档的宏平均百分比；每个文档先折叠三个固定顺序，不能把顺序当成独立任务。', '',
             '| 指标 | Free 旧→新 | Moderate 旧→新 | Tight 旧→新 |',
             '|---|---:|---:|---:|']
    names = [('标签正确', 'label_acc'), ('证据集合精确匹配', 'evidence_acc'),
             ('标签与证据同时正确', 'joint_acc'),
             ('非空金标准：标签正确', 'nonempty_label_correct'),
             ('非空金标准：精确证据', 'nonempty_evidence_exact'),
             ('非空金标准：联合正确', 'nonempty_joint_correct'),
             ('非空金标准：缺少至少一项', 'nonempty_missing_any'),
             ('非空金标准：额外证据', 'nonempty_extra_any')]
    for title, field in names:
        values = [f'{100*float(old[b][field]):.2f}→{100*float(new[b][field]):.2f}'
                  for b in ('cost_free', 'cost_moderate', 'cost_tight')]
        lines.append('| ' + title + ' | ' + ' | '.join(values) + ' |')
    la_drop = 100 * (float(new['cost_free']['label_acc']) - float(new['cost_tight']['label_acc']))
    ea_drop = 100 * (float(new['cost_free']['evidence_acc']) - float(new['cost_tight']['evidence_acc']))
    nonempty_drop = 100 * (float(new['cost_free']['nonempty_evidence_exact']) - float(new['cost_tight']['nonempty_evidence_exact']))
    lines += ['', f'新规则下，Free→Tight 的标签下降为 {la_drop:.2f} 个百分点，证据精确匹配下降为 {ea_drop:.2f} 个百分点；'
              f'非空金标准的证据精确匹配下降为 {nonempty_drop:.2f} 个百分点。'
              '“预算收紧使证据完整性损失大于标签准确率损失”的结论仍成立，但旧宏平均与差值应替换为这里的新数值。', '',
              '## 反馈补全配对及现有案例', '',
              '| 严格匹配人口统计 | 旧 | 新 |', '|---|---:|---:|']
    for title, field in [('匹配假设呈现', 'matched_hypothesis_presentations'),
                         ('Free 实际看到完整证据确认', 'free_exact_confirmation'),
                         ('模型×文档×假设去重', 'unique_model_doc_hypotheses'),
                         ('模型×文档去重', 'model_document_combinations'),
                         ('模型数', 'models'), ('文档数', 'documents'),
                         ('原 Qwen 案例候选数', 'qwen_case_candidates'),
                         ('原 PoolAct 案例候选数', 'pool_case_candidates')]:
        lines.append(f'| {title} | {populations["old"][field]} | {populations["new"][field]} |')
    lines += ['', '匹配规则保持原定义：Free 最终标签和证据都正确、首次可见反馈为 Evidence Incomplete；'
              '同模型/文档/顺序/假设的 Tight 标签正确、只缺证据且没有该假设的可见查询，Tight 最终集合等于 Free 的首次部分提案。'
              '修复终答解析后新识别出的配对有完整逐行来源，不是重新挑选高增益案例。', '',
              f'原 Qwen doc_index=10、order=1、nda-13 案例仍符合条件：{populations["new"]["qwen_frozen_case_still_qualifies"]}；'
              f'原 Kimi Moderate doc_index=3 池案例仍符合条件：{populations["new"]["kimi_frozen_case_still_qualifies"]}。'
              f'PoolAct 原排序规则的上中位案例为 `{populations["new"]["pool_rule_upper_median_key"]}`。'
              '保留既有案例身份，其新旧终值及策略对照在 [retained_cases.csv](changes/retained_cases.csv)。', '',
              '## PoolAct 共享证据的接受规则更新', '',
              '| PoolAct，分母均为 312 成员 | Moderate 旧→新 | Tight 旧→新 |', '|---|---:|---:|']
    for title, field in [('最终答案可解析成员', 'parsed_agents'),
                         ('至少一个 peer-only 非空最终证据匹配的成员', 'peer_only_nonempty_match_agents'),
                         ('peer-only 非空最终匹配假设数', 'peer_only_nonempty_match_hypotheses')]:
        values = [f'{populations["old"][b+"_"+field]}→{populations["new"][b+"_"+field]}'
                  for b in ('cost_moderate', 'cost_tight')]
        lines.append('| ' + title + ' | ' + ' | '.join(values) + ' |')
    lines += ['', '现在行为统计与正式评分、投票使用相同的 Audit 终答接受规则，接受合法 JSON 包装，'
              '不再用仅接受直接 json.loads 的分析分支漏掉合法终答。空对象仍是可解析但缺失所有假设的提交；非法文本不计可解析。'
              'peer-only 指其他成员可见核验正确，而本成员未对该集合获得可见核验；最终匹配不证明复制或因果影响。', '',
              f'动作及反馈可见性没有变化，PoolAct 覆盖高于 cached 的模型×预算组仍为 '
              f'{populations["new"]["poolact_coverage_above_cached_groups"]}/12，高于 naive 仍为 '
              f'{populations["new"]["poolact_coverage_above_naive_groups"]}/12。'
              '原“更广覆盖、较少请求重合”的行为结论保持；证据传播检测率和最终评分需更新。', '',
              '## 评分和复算口径', '',
              '- `verification_eff` 继续保留历史官方口径：提交过完全正确的证据集合即可计入，包含返回被预算隐藏的提交。'
              '未将其悄悄改成可见反馈指标。另导出的 N1 `visible_verification_eff` 仅计实际可见的正确集合。',
              '- 所有工具次数、停止原因、查询覆盖及可见性从已有动作复算；新的终答只改变与最终提交相关的指标。'
              '历史动作本身不具有修复后运行时反事实含义。',
              '- [旧分析基线校验](OLD_BASELINE_CHECK.json) 对冻结七张 N1 表和三张协调表的共同字段作逐项对照。'
              '新增的来源字段使用 slot_id、agent_id 与原件 SHA-256，不公开私有绝对路径。',
              '- [逐样本变化](changes/traces.csv)、[逐假设变化](changes/hypotheses.csv)、'
              '[逐成员变化](changes/agents.csv)、[逐池变化](changes/pools.csv) 保留旧值、新值和变化原因。',
              '- [CHECKS.json](CHECKS.json) 记录输入校验和完整采用集合；旧诊断文件保留在原交付中，'
              '本目录以全量新规则回算取代只改已知异常样本的诊断。', '',
              '原件模式（不发起模型请求）：', '', '```bash',
              'python3 recompute_audit.py --repo /path/to/LLM_ExpGym \\',
              '  --sources /private/resolved_sources.json --overlays /private/answer_overlays.jsonl \\',
              '  --gold /private/contract-nli/test_segments.json --output /tmp/audit-recomputed',
              '```', '', '仅用公开逐假设/逐轨迹/逐成员/逐池 CSV 重建汇总、差异及配对人口：', '', '```bash',
              'python3 recompute_audit.py --replay-public . --output /tmp/audit-public-replay',
              '```', '', '公开回放检验汇总，不假装重新读取未公开的原始 prompt。证据集合 exact match 是注释集完整性，不是独立法律充分性判断。', '']
    (root / 'README.zh.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
