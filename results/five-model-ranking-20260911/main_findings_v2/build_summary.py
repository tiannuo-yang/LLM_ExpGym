#!/usr/bin/env python3
"""Concise five-model report from frozen scores and an explicit Gap0 supplement.

No raw payload access, scoring, model calls or changes to historical endpoints.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PIN = '9e11134af27102327d8c41dade83211ec5a26da2'
PARENT_ABSOLUTE_SHA = '007d2b59d8b21a001bd4c0f1c30279f19c11d0fa4d0236902408eb104d5d9b68'
MODELS = ['kimi-k3', 'glm-5.3', 'qwen3.8-2.4t-a95b-fp8', 'deepseek-v4-flash-0731', 'gpt-5.6-sol']
LABELS = dict(zip(MODELS, ['Kimi', 'GLM', 'Qwen', 'DeepSeek', 'GPT (medium)']))
BUDGETS = ['cost_free', 'cost_moderate', 'cost_tight']
STRATEGIES = ['naive', 'cached', 'poolact']
KEYS = ['model', 'system', 'scenario', 'regime', 'strategy', 'slice_kind', 'slice', 'metric']
TIE = 1e-12


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_csv(path):
    return list(csv.DictReader(io.StringIO(path.read_text())))


def index(rows):
    result = {}
    for r in rows:
        key = tuple(r[k] for k in KEYS)
        if key in result:
            raise ValueError('Duplicate metric identity')
        result[key] = r
    return result


def score(idx, model, system, scenario, budget, strategy, metric, kind='all', sl='all', field='full_mean'):
    r = idx[(model, system, scenario, budget, strategy, kind, sl, metric)]
    raw = r[field]
    if raw in ('', None):
        raise ValueError('Main-table endpoint unexpectedly incomplete')
    value = float(raw)
    if not math.isfinite(value) or value < 0:
        raise ValueError('Non-finite or negative utility')
    return value


def csv_bytes(rows):
    f = io.StringIO(newline='')
    writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue().encode()


def table(headers, rows):
    def line(r):
        return '| ' + ' | '.join(str(x) for x in r) + ' |\n'
    return line(headers) + line(['---'] * len(headers)) + ''.join(line(r) for r in rows)


def fmt(value, signed=False):
    return format(value, '+.2f' if signed else '.2f')


def winner_set(values):
    top = max(values.values())
    return [m for m in MODELS if top - values[m] <= TIE]


def non_hpo_sentence(data):
    fields = ['planned', 'raw_null', 'scored_empty', 'exec_incomplete', 'score_incomplete']
    totals = {r['model']: r for r in data['totals']}
    if set(totals) != set(MODELS[-2:]) or len(data['totals']) != 2 or len(data['settings']) != 36:
        raise ValueError('Unexpected non-HPO coverage')
    expected = {(system, scenario, budget, strategy)
                for system in ['expgym', 'poolact']
                for scenario in ['restricted_search', 'evidence_audit']
                for budget in (BUDGETS if system == 'expgym' else BUDGETS[1:])
                for strategy in (['single'] if system == 'expgym' else STRATEGIES)}
    for m, total in totals.items():
        rows = [r for r in data['settings'] if r['model'] == m]
        if len(rows) != 18 or {(r['system'], r['scenario'], r['regime'], r['strategy']) for r in rows} != expected:
            raise ValueError('Missing/duplicate non-HPO setting')
        for r in rows:
            if any(type(r[k]) is not int or r[k] < 0 for k in fields):
                raise ValueError('Invalid non-HPO count')
            if r['raw_null'] != r['scored_empty'] or r['raw_null'] > r['planned'] or r['exec_incomplete'] or r['score_incomplete']:
                raise ValueError('Empty prediction is not complete original scoring')
        if any(sum(r[k] for r in rows) != total[k] for k in fields):
            raise ValueError('Non-HPO totals mismatch')
    d, g = (totals[m] for m in MODELS[-2:])
    return (f"Search/Audit的低分另作区分：GPT空回答为{g['raw_null']}/{g['planned']}，并无缺答；"
            f"DeepSeek为{d['raw_null']}/{d['planned']}（{100*d['raw_null']/d['planned']:.1f}%）。"
            "这些空答已由原评估器按空预测计入现有分数，不是unknown，不再次补零或剔除；"
            "也不能据此把DeepSeek全部低分归因于缺答。[计数来源](NON_HPO_OUTPUTS.json)\n")


def make_tables(absolute, gap0):
    a, g = index(absolute), index(gap0)
    exp, pool, family = [], [], []
    scenarios = [('Search', 'restricted_search', 'f1', 'f1_mv', 100, '分 (0–100)'),
                 ('Audit', 'evidence_audit', 'evidence_acc', 'evidence_acc_mv', 100, '分 (0–100)'),
                 ('HPO/NAS', 'tuning', 'gap0', 'gap0_mi', 1, 'Gap0点')]
    for label, scenario, single_metric, pool_metric, scale, unit in scenarios:
        src, field = (g, 'value') if scenario == 'tuning' else (a, 'full_mean')
        for model in MODELS:
            vals = [score(src, model, 'expgym', scenario, b, 'single', single_metric, field=field) * scale for b in BUDGETS]
            exp.append(dict(scenario=label, model=model, metric=single_metric, unit=unit,
                            free=vals[0], moderate=vals[1], tight=vals[2], free_minus_tight=vals[0] - vals[2]))
            for budget in BUDGETS[1:]:
                vals = [score(src, model, 'poolact', scenario, budget, s, pool_metric, field=field) * scale for s in STRATEGIES]
                pool.append(dict(scenario='NAS' if scenario == 'tuning' else label, model=model,
                                 regime=budget, metric=pool_metric, unit=unit, naive=vals[0], cached=vals[1], poolact=vals[2],
                                 cached_minus_naive=vals[1] - vals[0], poolact_minus_cached=vals[2] - vals[1],
                                 poolact_minus_naive=vals[2] - vals[0]))
    endpoints = [('Search whois', 'restricted_search', 'whois', 'f1', 100),
                 ('Search whatis', 'restricted_search', 'whatis', 'f1', 100),
                 ('Audit', 'evidence_audit', 'evidence_audit', 'evidence_acc', 100),
                 ('ParamNet', 'tuning', 'paramnet', 'gap0', 1),
                 ('NAS101', 'tuning', 'nasbench101', 'gap0', 1),
                 ('NAS201', 'tuning', 'nasbench201', 'gap0', 1)]
    for label, scenario, sl, metric, scale in endpoints:
        src, field = (g, 'value') if scenario == 'tuning' else (a, 'full_mean')
        winners = []
        for b in BUDGETS:
            kind, selected_slice = ('all', 'all') if scenario == 'evidence_audit' else ('family', sl)
            vals = {m: score(src, m, 'expgym', scenario, b, 'single', metric, kind, selected_slice, field) for m in MODELS}
            winning = winner_set(vals)
            winners.append(winning)
            top = max(vals.values())
            sorted_values = sorted(vals.values(), reverse=True)
            for m in MODELS:
                family.append(dict(family=label, model=m, regime=b, metric=metric,
                                   value=vals[m] * scale, winner=m in winning, winner_set=';'.join(winning),
                                   candidate_count=5, first_second_margin=(top - sorted_values[1]) * scale,
                                   unit='Gap0点' if metric == 'gap0' else '分 (0–100)'))
        for r in family[-15:]:
            r['free_to_tight_winner_changed'] = set(winners[0]) != set(winners[2])
    return exp, pool, family


def main_content(exp, pool, family, non_hpo):
    exp_table = table(['场景 / 主指标', '模型', 'Free', 'Moderate', 'Tight', 'Free−Tight ↓'],
        [[r['scenario'] + (' / Gap0' if r['metric'] == 'gap0' else ' / F1' if r['metric'] == 'f1' else ' / EA'), LABELS[r['model']],
          fmt(r['free']), fmt(r['moderate']), fmt(r['tight']), fmt(r['free_minus_tight'], True)] for r in exp])
    pool_tables = {}
    for budget in BUDGETS[1:]:
        pool_tables[budget] = table(['场景 / 主指标', '模型', 'naive', 'cached', 'PoolAct', 'PoolAct−naive', 'PoolAct−cached'],
            [[r['scenario'] + (' / Gap0-MI' if r['metric'] == 'gap0_mi' else ' / F1-MV' if r['metric'] == 'f1_mv' else ' / EA-MV'), LABELS[r['model']],
              fmt(r['naive']), fmt(r['cached']), fmt(r['poolact']), fmt(r['poolact_minus_naive'], True), fmt(r['poolact_minus_cached'], True)]
             for r in pool if r['regime'] == budget])
    ranked = []
    for name in dict.fromkeys(r['family'] for r in family):
        rows = [r for r in family if r['family'] == name]
        cells = []
        for b in BUDGETS:
            wins = [r for r in rows if r['regime'] == b and r['winner']]
            cells.append(' = '.join(LABELS[r['model']] for r in wins) + ' (' + fmt(wins[0]['value']) + ')')
        ranked.append([name + (' / Gap0' if rows[0]['metric'] == 'gap0' else ''), *cells,
                       '是' if rows[0]['free_to_tight_winner_changed'] else '否'])
    markers = {'NON_HPO': non_hpo_sentence(non_hpo), 'EXPGYM': exp_table, 'POOL_MODERATE': pool_tables[BUDGETS[1]], 'POOL_TIGHT': pool_tables[BUDGETS[2]],
               'FAMILY_WINNERS': table(['任务家族', 'Free 最优', 'Moderate 最优', 'Tight 最优', 'Free→Tight换位'], ranked)}
    template = (ROOT / 'SUMMARY_TEMPLATE.zh.md').read_text()
    for k, v in markers.items():
        token = '{{' + k + '}}'
        if template.count(token) != 1:
            raise ValueError('Missing or repeated table marker')
        template = template.replace(token, v)
    if '{{' in template:
        raise ValueError('Unexpanded marker')
    return template.encode()


def detail_content(rows):
    rendered = []
    for r in rows:
        pool = r['system'] == 'poolact'
        known, planned = (r['valid_pools'], r['planned_pools']) if pool else (r['valid_agents'], r['planned_agents'])
        strict = fmt(float(r['strict_value'])) if r['strict_value'] != '' else 'unknown (' + known + '/' + planned + ')'
        rendered.append([LABELS[r['model']], 'Pool' if pool else 'ExpGym', r['slice'],
                         r['regime'].replace('cost_', ''), r['strategy'], r['metric'], strict, fmt(float(r['value'])),
                         r['valid_agents'] + '/' + r['planned_agents'],
                         r['valid_pools'] + '/' + r['planned_pools'] if pool else '—',
                         fmt(float(r['known_agent_mean'])) if r['known_agent_mean'] != '' else 'unknown'])
    intro = '''# Gap0：未交付结果的数值比较补充

[主问题精简版](README.zh.md) · [完整历史详细报告](../README.zh.md) · [原始dump与完整索引](../ARCHIVE_INDEX.md)

## 指标与来源

这是本次用户请求下新增的回顾性交付效用，不重评分、不改写原严格端点。仅已执行、正常返回且缺最终配置的agent效用取0；已评分agent的原Gap不变，保留冻结legacy final-selection规则，Gap允许超过100。异常、未开始或缺失执行记录不会自动计零。

对池p：MI0 = Σ已交付成员Gap / 4；BoN0 = max({已交付成员Gap}∪{0})。先在每个item内平均原3个重复，再对item等权。三成员有结果的池保留这三人的贡献，不把全池作零；四人均缺配置的正常结束池才MI0=BoN0=0。后者不是把无法计算的原真实Gap补成零。

本研究的调优重复/N固定且均衡，因此MI0也能写成有效成员比例×已评分成员平均Gap；此恒等式仅描述本研究权重，不推广给不均衡任务，更不适用于BoN0。条件均值只看已评分成员，含选择偏差，不能作为完整端点或用它选择候选模型。

来源与投影字段：[GAP0_INPUTS.json](GAP0_INPUTS.json)。五份已有评分/终态CSV经显式字段投影后冻结于inputs，保存源SHA、源数据行号和投影SHA；不含回答正文。DeepSeek/GPT各135个调优执行单元、297名agent均校验身份和终态。另三个模型的原严格端点完整，按同一规则其Gap0等于原Gap；不重新访问其raw。

GPT缺失1名成员，终止原因为本地上下文上限。DeepSeek缺失92名，均为正常返回的missing configuration；原终态导出无更细loop终止原因，不推断其全部由context或输出长度引起。

## 全设置数值

原严格列中：ExpGym分母为单agent重复，Pool分母为四人全有效池；“成员有效”分母是agent，两者不同。条件成员Gap列始终为已评分agent平均，即使当前行展示BoN也不是条件BoN。原未知端点保持unknown，Gap0只在独立新列中展示。

'''
    result = intro + table(['模型', '系统', '范围', '预算', '策略', '新指标', '原严格指标', 'Gap0', '成员有效', '全有效池', '条件成员Gap'], rendered)
    result += '''
## 文件与重建

- [gap0_settings.csv](gap0_settings.csv)：完整原值、新效用、成员/池分母、条件均值。
- [missing_output_summary.csv](missing_output_summary.csv)：配置缺失、其他异常、终止原因的设置级计数，不含task/question ID。
- [GAP0_CHECKS.json](GAP0_CHECKS.json)：有限输入与聚合检查；[gap0.py](gap0.py)及[test_gap0.py](test_gap0.py)为生成器和窄测试。
- [build_summary.py](build_summary.py)与[test_summary.py](test_summary.py)：三主问题数据和展示适配；[SUMMARY_CHECKS.json](SUMMARY_CHECKS.json)绑定父报告与本版输入。

在本目录、CPython3.11.15下执行 `python3 -B gap0.py --check` 和 `python3 -B build_summary.py --check`。前者从冻结投影重建数值；父报告absolute_settings.csv须保留原相对位置与SHA。重建摘要不等于重新验证原模型回复的评分正确性，也不证明本次观察具有统计显著性。
'''
    return result.encode()


def generate():
    parent = ROOT.parent / 'absolute_settings.csv'
    raw = parent.read_bytes()
    if sha(raw) != PARENT_ABSOLUTE_SHA:
        raise ValueError('Parent frozen scored export identity changed')
    absolute = list(csv.DictReader(io.StringIO(raw.decode())))
    if len(absolute) != 5051:
        raise ValueError('Unexpected frozen row coverage')
    gap0 = read_csv(ROOT / 'gap0_settings.csv')
    non_hpo_raw = (ROOT / 'NON_HPO_OUTPUTS.json').read_bytes()
    non_hpo = json.loads(non_hpo_raw)
    exp, pool, family = make_tables(absolute, gap0)
    checks = dict(schema='main-findings-render-checks-v1', prior_commit=PIN,
                  parent_absolute_sha256=sha(raw), gap0_settings_sha256=sha((ROOT / 'gap0_settings.csv').read_bytes()),
                  template_sha256=sha((ROOT / 'SUMMARY_TEMPLATE.zh.md').read_bytes()),
                  non_hpo_counts_sha256=sha(non_hpo_raw),
                  expgym_rows=len(exp), pool_rows=len(pool), family_model_budget_rows=len(family),
                  family_champion_changes=sum(r['free_to_tight_winner_changed'] for r in family) // 15,
                  ranking_candidates=5, model_calls=0, scorer_calls=0, raw_payload_reads=0)
    outputs = {'README.zh.md': main_content(exp, pool, family, non_hpo), 'GAP0_DETAILS.zh.md': detail_content(gap0), 'main_expgym.csv': csv_bytes(exp),
               'main_poolact.csv': csv_bytes(pool), 'main_family_rankings.csv': csv_bytes(family),
               'SUMMARY_CHECKS.json': (json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()}
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = generate()
    for name, raw in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_bytes() != raw:
                raise ValueError('Generated output differs: ' + name)
        else:
            path.write_bytes(raw)
    print(json.dumps(dict(mode='check' if args.check else 'generate', files=len(outputs), bytes=sum(map(len, outputs.values())))))


if __name__ == '__main__':
    main()
