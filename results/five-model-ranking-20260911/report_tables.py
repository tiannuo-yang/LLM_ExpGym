"""Report display/check helpers adapted from the frozen four-model report.
Source a79cbc100804a1bc8d374e084a4b9999e3697a91; no execution/scoring dependency.
GPT resources retain their separate native accounting table, not these means.
"""
import csv, io, itertools, math
MODELS = ['kimi-k3','glm-5.3','qwen3.8-2.4t-a95b-fp8','deepseek-v4-flash-0731','gpt-5.6-sol']
RESOURCE_MODELS = MODELS[:4]
LABELS = dict(zip(MODELS,['Kimi-K3','GLM-5.3','Qwen3.8','DeepSeek-0731','GPT-5.6-sol (medium)']))
REGIMES = ['cost_free','cost_moderate','cost_tight']
STRATEGIES = ['naive','cached','poolact']
IDENTITY = ['model','system','scenario','slice_kind','slice','regime','strategy','metric']


def number(value):
    if value in ('', None):
        return None
    v = float(value)
    if not math.isfinite(v):
        raise ValueError('Non-finite value')
    return v


def check_rows(rows, block=False):
    seen = set()
    for r in rows:
        key = tuple(r[k] for k in IDENTITY) + ((r['outerrep'],) if block else ())
        if key in seen:
            raise ValueError('Duplicate aggregate identity: ' + str(key))
        seen.add(key)
        n, k, m = (int(r[x]) for x in ('expected_outcomes', 'known_outcomes', 'missing_outcomes'))
        if n <= 0 or k < 0 or m < 0 or n != k + m:
            raise ValueError('Invalid denominator')
        v = number(r['full_mean'])
        if (m > 0) != (v is None):
            raise ValueError('Full endpoint must be unknown iff required outcomes are missing')
        sd = number(r.get('descriptive_repeat_sd', ''))
        if sd is not None and (block or int(r['repeat_blocks']) < 2 or m):
            raise ValueError('Invalid repeat SD')
        if int(r['expected_items']) * int(r['max_repeats_per_item']) != n:
            raise ValueError('Unexpected repeat/item denominator')
        if r['metric'].startswith('gap') and v is not None and v < -1e-9:
            raise ValueError('Gap must be lower-clipped only; no upper cap')
    return seen


def check_contrasts(rows):
    seen = set()
    for r in rows:
        axis = r['comparison_axis']
        key = tuple(r[k] for k in IDENTITY if k != axis) + (axis, r['baseline'], r['target'])
        if key in seen:
            raise ValueError('Duplicate contrast')
        seen.add(key)
        n, k, m = (int(r[x]) for x in ('expected_outcomes', 'known_outcomes', 'missing_outcomes'))
        if n <= 0 or min(k, m) < 0 or n != k + m:
            raise ValueError('Invalid contrast denominator')
        v = number(r['effect'])
        if (m > 0) != (v is None):
            raise ValueError('Incomplete contrast must remain unknown')
        if v is not None:
            a, b = number(r['baseline_full_mean']), number(r['target_full_mean'])
            wanted = a - b if r['effect_definition'] == 'baseline_minus_target' else b - a
            if not math.isclose(v, wanted, abs_tol=1e-10, rel_tol=1e-10):
                raise ValueError('Contrast direction/value mismatch')


def csv_bytes(rows):
    fields = list(dict.fromkeys(IDENTITY + [k for r in rows for k in r]))
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
    return f.getvalue().encode()


def fmt(value, signed=False):
    v = number(value)
    return 'unknown' if v is None else format(v, '+.6f' if signed else '.6f')


def cell(row, field='full_mean', signed=False):
    s = fmt(row.get(field, ''), signed)
    if s == 'unknown':
        s += ' (' + row['known_outcomes'] + '/' + row['expected_outcomes'] + ')'
    return s


def table(headers, rows):
    def line(row):
        return '| ' + ' | '.join(str(x).replace('|', '\\|').replace('\n', ' ') for x in row) + ' |\n'
    return line(headers) + line(['---'] * len(headers)) + ''.join(line(r) for r in rows)


def render(absolute, blocks, contrasts):
    idx = {tuple(r[k] for k in IDENTITY): r for r in absolute}
    bidx = {tuple(r[k] for k in IDENTITY) + (r['outerrep'],): r for r in blocks}
    def get(model, system, scenario, regime, strategy, metric, slice_name='all'):
        kind, s = slice_name.split('=', 1) if '=' in slice_name else ('all' if slice_name == 'all' else 'family', slice_name)
        return idx[(model, system, scenario, kind, s, regime, strategy, metric)]
    def show4(system, scenario, metric, slice_name='all'):
        for regime in REGIMES if system == 'expgym' else REGIMES[1:]:
            for strategy in ['single'] if system == 'expgym' else STRATEGIES:
                rs = [get(m, system, scenario, regime, strategy, metric, slice_name) for m in MODELS]
                yield [slice_name, metric, regime[5:], strategy, rs[0]['expected_items']] + [cell(r) for r in rs]
    hdr = ['切片', '指标', '预算', '策略', 'items'] + [LABELS[m] for m in MODELS]
    sa = []
    for s in ['all', 'whois', 'whatis']:
        sa.extend(show4('expgym', 'restricted_search', 'f1', s))
    for metric in ['evidence_acc', 'label_acc']:
        sa.extend(show4('expgym', 'evidence_audit', metric))
    slices = ['all', 'family=paramnet', 'family=nasbench101', 'family=nasbench201'] + [
        'task=' + t for t in sorted({r['slice'] for r in absolute if r['slice_kind'] == 'task'})]
    hpo = [row for s in slices for metric in ['gap', 'raw_perf']
           for row in show4('expgym', 'tuning', metric, s)]
    out = {'EXP_SEARCH_AUDIT': table(hdr, sa), 'EXP_HPO': table(hdr, hpo)}
    for token, scenario, metrics, selected in [
            ('POOL_SEARCH', 'restricted_search', ['f1_mi', 'f1_mv'], ['all']),
            ('POOL_AUDIT', 'evidence_audit', ['evidence_acc_mi', 'evidence_acc_mv', 'label_acc_mi', 'label_acc_mv'], ['all']),
            ('POOL_NAS', 'tuning', ['gap_mi', 'gap_bon', 'raw_perf_mi', 'raw_perf_bon'],
             ['all'] + ['task=hpobench:nasbench101:' + x for x in 'ABC'])]:
        out[token] = table(hdr, [row for s in selected for metric in metrics
                                for row in show4('poolact', scenario, metric, s)])
    cr = []
    for model, regime, metric in itertools.product(MODELS, REGIMES[1:],
                                                  ['f1_mv', 'evidence_acc_mv', 'label_acc_mv', 'gap_mi', 'gap_bon']):
        values = []
        for baseline, target in [('naive', 'cached'), ('cached', 'poolact'), ('naive', 'poolact')]:
            matched = [r for r in contrasts if r['model'] == model and r['system'] == 'poolact'
                       and r['regime'] == regime and r['metric'] == metric and r['slice_kind'] == 'all'
                       and r['baseline'] == baseline and r['target'] == target]
            if len(matched) != 1:
                raise ValueError('Missing/duplicate overview contrast')
            values.append(cell(matched[0], 'effect', True))
        cr.append([LABELS[model], regime[5:], metric] + values)
    out['POOL_CONTRASTS'] = table(['模型', '预算', '指标', 'cached − naive', 'poolact − cached', 'poolact − naive'], cr)
    for system, token, metrics in [('expgym', 'EXP_REPEATS', ['gap', 'raw_perf']),
                                   ('poolact', 'POOL_REPEATS', ['gap_mi', 'gap_bon', 'raw_perf_mi', 'raw_perf_bon'])]:
        rows = []
        for model, regime, strategy, metric in itertools.product(
                MODELS, REGIMES if system == 'expgym' else REGIMES[1:],
                ['single'] if system == 'expgym' else STRATEGIES, metrics):
            a = get(model, system, 'tuning', regime, strategy, metric)
            key = tuple(a[k] for k in IDENTITY)
            rows.append([LABELS[model], regime[5:], strategy, metric] +
                        [cell(bidx[key + (str(i),)]) for i in range(3)] +
                        [cell(a), fmt(a.get('descriptive_repeat_sd', ''))])
        out[token] = table(['模型', '预算', '策略', '指标', '2200', '2204', '2208', '三块均值', '描述 SD'], rows)
    resources = ['input_tokens', 'output_tokens', 'feedback_cost_seconds', 'wall_time_seconds',
                 'feedback_attempts', 'duplicate_action_attempts', 'feedback_visible', 'budget_utilization',
                 'protocol_failure_rate']
    rr = []
    for model in RESOURCE_MODELS:
        for system, scenario in itertools.product(['expgym', 'poolact'], ['restricted_search', 'evidence_audit', 'tuning']):
            for regime, strategy in itertools.product(REGIMES if system == 'expgym' else REGIMES[1:],
                                                      ['single'] if system == 'expgym' else STRATEGIES):
                rr.append([LABELS[model], system + '/' + scenario, regime[5:], strategy] +
                          [('不适用' if metric == 'budget_utilization' and regime == 'cost_free' else
                            cell(get(model, system, scenario, regime, strategy, metric))) for metric in resources])
    out['RESOURCES'] = table(['模型', '系统/场景', '预算', '策略'] + resources, rr)
    return out


def detailed_files(absolute, blocks, contrasts):
    result = {}
    nav = ['# 完整聚合表\n\n全部 5 模型、所有原生切片、指标与预算/策略均保留。每模型页面避免单一巨型 Markdown 超出渲染上限。'
           '分母是分析 outcomes，不是 HTTP 请求或 Pool 成员数；unknown 不记为零。\n\n']
    repnav = ['# 完整 seed-block 表\n\nSearch 为 R1；Exp Audit 已折叠三个固定顺序一次；仅 tuning 为三个 blocks。'
              'R1 不计算 SD，seed 标签不证明独立采样。\n\n']
    for model in MODELS:
        slug = model.replace('.', '_')
        paths = ['tables/' + slug + '.md', 'repeats/' + slug + '.md']
        ar = [r for r in absolute if r['model'] == model]
        br = [r for r in blocks if r['model'] == model]
        nav.append('- [' + LABELS[model] + '](' + paths[0] + ')：' + str(len(ar)) + ' 行。\n')
        repnav.append('- [' + LABELS[model] + '](' + paths[1] + ')：' + str(len(br)) + ' 行。\n')
        for path, rows, block in [(paths[0], ar, False), (paths[1], br, True)]:
            body = '# ' + LABELS[model] + (' · blocks' if block else ' · 全部聚合') + '\n\n'
            body += 'known subset 仅供诊断，不替代 full mean；旧源的 original logical rows 与新源 components 原样保留在 CSV/输入中。\n\n'
            headers = ['系统/场景', '切片', '预算/策略', '指标'] + (['block/seed'] if block else []) + [
                '完整均值', '已知/预期 outcomes', 'items', 'known subset（非完整端点）'] + ([] if block else ['R', '描述 SD'])
            values = []
            for r in rows:
                values.append([r['system'] + '/' + r['scenario'], r['slice_kind'] + ':' + r['slice'],
                               r['regime'][5:] + '/' + r['strategy'], r['metric']] +
                              ([r['outerrep'] + '/' + r['seed_labels']] if block else []) +
                              [fmt(r['full_mean']), r['known_outcomes'] + '/' + r['expected_outcomes'],
                               r['expected_items'], fmt(r['known_subset_item_weighted_mean'])] +
                              ([] if block else [r['repeat_blocks'], fmt(r.get('descriptive_repeat_sd', ''))]))
            result[path] = (body + table(headers, values)).encode()
    nav.append('\n机器完整表：[absolute_settings.csv](absolute_settings.csv)；所有方向与配对分母：[contrasts.csv](contrasts.csv)。\n')
    repnav.append('\n机器完整表：[by_outerseed.csv](by_outerseed.csv)。\n')
    result['TABLES.md'] = ''.join(nav).encode()
    result['REPEATS.md'] = ''.join(repnav).encode()
    return result
