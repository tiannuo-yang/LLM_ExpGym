"""Descriptive rankings of the frozen five-model study; no scorer or model calls.

Study-specific endpoint/model identities are explicit.  Input values must already
use the normalized absolute-settings schema and the original scientific units.
Only the ExpGym endpoints below are consumed.  Each endpoint keeps the same
candidate set across Free/Moderate/Tight: a candidate needs its full endpoint in
all three regimes.  Excluded candidates' original rows remain in RANKINGS.csv.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from typing import Iterable


TIE_ATOL = 1e-12
MODELS = (
    "kimi-k3",
    "glm-5.3",
    "qwen3.8-2.4t-a95b-fp8",
    "deepseek-v4-flash-0731",
    "gpt-5.6-sol",
)
MODEL_LABELS = dict(zip(MODELS, ("Kimi", "GLM", "Qwen", "DeepSeek", "GPT")))
REGIMES = ("cost_free", "cost_moderate", "cost_tight")
REGIME_LABELS = dict(zip(REGIMES, ("Free", "Moderate", "Tight")))


@dataclass(frozen=True)
class Endpoint:
    key: str
    category: str
    label: str
    scenario: str
    slice_kind: str
    slice: str
    metric: str
    unit: str


ENDPOINTS = (
    Endpoint("whois_f1", "family", "Search whois / F1", "restricted_search", "family", "whois", "f1", "fraction"),
    Endpoint("whatis_f1", "family", "Search whatis / F1", "restricted_search", "family", "whatis", "f1", "fraction"),
    Endpoint("audit_ea", "family", "Audit / EA", "evidence_audit", "all", "all", "evidence_acc", "fraction"),
    Endpoint("paramnet_gap", "family", "ParamNet / Gap", "tuning", "family", "paramnet", "gap", "Gap points"),
    Endpoint("nas101_gap", "family", "NAS101 / Gap", "tuning", "family", "nasbench101", "gap", "Gap points"),
    Endpoint("nas201_gap", "family", "NAS201 / Gap", "tuning", "family", "nasbench201", "gap", "Gap points"),
) + tuple(
    Endpoint("task_" + task.replace(":", "_"), "task", label, "tuning", "task", "hpobench:" + task, "gap", "Gap points")
    for task, label in (
        ("nasbench101:A", "NAS101 A"),
        ("nasbench101:B", "NAS101 B"),
        ("nasbench101:C", "NAS101 C"),
        ("nasbench201:cifar10-valid", "NAS201 cifar10-valid"),
        ("nasbench201:cifar100", "NAS201 cifar100"),
        ("nasbench201:imagenet16-120", "NAS201 imagenet16-120"),
        ("paramnet:adult:steps", "ParamNet adult"),
        ("paramnet:higgs:steps", "ParamNet higgs"),
        ("paramnet:letter:steps", "ParamNet letter"),
    )
) + (
    Endpoint("search_all_f1", "secondary", "Search all / F1", "restricted_search", "all", "all", "f1", "fraction"),
    Endpoint("hpo_all_gap", "secondary", "HPO all / Gap", "tuning", "all", "all", "gap", "Gap points"),
    Endpoint("audit_la", "secondary", "Audit / LA（次指标）", "evidence_audit", "all", "all", "label_acc", "fraction"),
)


def _integer(row: dict[str, str], key: str) -> int:
    try:
        value = int(row[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer {key}: {row.get(key)!r}") from exc
    if value < 0:
        raise ValueError(f"Negative {key}")
    return value


def _read_value(row: dict[str, str], endpoint: Endpoint) -> float | None:
    expected = _integer(row, "expected_outcomes")
    known = _integer(row, "known_outcomes")
    missing = _integer(row, "missing_outcomes")
    items = _integer(row, "expected_items")
    known_items = _integer(row, "known_items")
    complete_items = _integer(row, "complete_items")
    if expected == 0 or items == 0 or known + missing != expected:
        raise ValueError("Invalid expected/known/missing outcome accounting")
    if not 0 <= complete_items <= known_items <= items or items > expected:
        raise ValueError("Invalid item accounting")
    if row.get("N") != "1" or row.get("slice_kind") != endpoint.slice_kind:
        raise ValueError("Wrong N or slice_kind for ranking endpoint")
    if row.get("unit") != endpoint.unit:
        raise ValueError("Scientific ranking unit changed")
    if str(row.get("higher_is_better", "")).lower() != "true":
        raise ValueError("Ranking endpoints require explicit higher_is_better=True")
    raw = row.get("full_mean")
    if raw in (None, ""):
        if missing == 0 and complete_items == items:
            raise ValueError("Complete endpoint has no full_mean")
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid full_mean") from exc
    if not math.isfinite(value) or value < 0 or (endpoint.unit == "fraction" and value > 1):
        raise ValueError("Invalid scientific score range; Gap has no upper cap")
    if missing != 0 or complete_items != items:
        raise ValueError("Incomplete endpoint cannot have a full_mean")
    return value


def _rank(values: dict[str, float]) -> tuple[list[list[str]], dict[str, int]]:
    """Descending competition ranks; ties compare to each group's top anchor.

    A~B and B~C does not imply A~C.  Names only stabilize display order among
    mathematically equal scores, never decide a winner.  Relative tolerance is 0.
    """
    ordered = sorted(values, key=lambda model: (-values[model], model))
    groups: list[list[str]] = []
    ranks: dict[str, int] = {}
    for position, model in enumerate(ordered, 1):
        if groups and abs(values[groups[-1][0]] - values[model]) <= TIE_ATOL:
            groups[-1].append(model)
            ranks[model] = ranks[groups[-1][0]]
        else:
            groups.append([model])
            ranks[model] = position
    return groups, ranks


def _csv_bytes(rows: list[dict[str, object]], fields: list[str]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def _score(value: float | None) -> str:
    return "unknown" if value is None else f"{value:.6f}"


def _names(models: Iterable[str]) -> str:
    return " = ".join(MODEL_LABELS[model] for model in models)


def _table(header: list[str], rows: Iterable[list[str]]) -> str:
    return "\n".join([
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
        *("| " + " | ".join(row) + " |" for row in rows),
    ])


def build(absolute_rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, bytes], dict[str, object]]:
    """Return three README markers, three file payloads and JSON-safe checks.

    Missing/duplicate planned model×endpoint×regime rows fail closed.  A present
    unknown endpoint is preserved, and excludes that model from all three
    rankings for that endpoint (not from the source data).  Fewer than two fixed
    complete candidates yields no ranks and is omitted from change-rate
    denominators, with planned/rankable counts both explicitly retained.
    """
    wanted = {(e.scenario, e.slice, e.metric): e for e in ENDPOINTS}
    selected: dict[tuple[str, str, str], dict[str, str]] = {}
    numeric: dict[tuple[str, str, str], float | None] = {}
    for row in absolute_rows:
        if row.get("system") != "expgym" or row.get("strategy") != "single":
            continue
        endpoint = wanted.get((row.get("scenario"), row.get("slice"), row.get("metric")))
        if endpoint is None:
            continue
        model, regime = row.get("model"), row.get("regime")
        if model not in MODELS or regime not in REGIMES:
            raise ValueError("Unexpected model/regime in planned ranking endpoint")
        key = (endpoint.key, model, regime)
        if key in selected:
            raise ValueError(f"Duplicate ranking row: {key}")
        selected[key] = row
        numeric[key] = _read_value(row, endpoint)
    for endpoint in ENDPOINTS:
        for model in MODELS:
            for regime in REGIMES:
                if (endpoint.key, model, regime) not in selected:
                    raise ValueError(f"Missing planned ranking row: {(endpoint.key, model, regime)}")

    rank_rows: list[dict[str, object]] = []
    transition_rows: list[dict[str, object]] = []
    records = []
    for endpoint in ENDPOINTS:
        candidates = [m for m in MODELS if all(numeric[(endpoint.key, m, r)] is not None for r in REGIMES)]
        excluded = [m for m in MODELS if m not in candidates]
        rankable = len(candidates) >= 2
        regime_data = {}
        for regime in REGIMES:
            vals = {m: numeric[(endpoint.key, m, regime)] for m in candidates}
            groups, ranks = _rank(vals) if rankable else ([], {})
            winners = groups[0] if groups else []
            ordered = [m for group in groups for m in group]
            runner_up_margin = (
                (0.0 if len(winners) > 1 else vals[ordered[0]] - vals[ordered[1]])
                if rankable else None
            )
            regime_data[regime] = {
                "values": vals, "groups": groups, "ranks": ranks,
                "winners": winners, "runner_up_margin": runner_up_margin,
            }
            for model in MODELS:
                source = selected[(endpoint.key, model, regime)]
                incomplete = [r for r in REGIMES if numeric[(endpoint.key, model, r)] is None]
                rank_rows.append({
                    "category": endpoint.category, "endpoint": endpoint.key,
                    "endpoint_label": endpoint.label, "model": model,
                    "system": "expgym", "scenario": endpoint.scenario,
                    "slice_kind": endpoint.slice_kind, "slice": endpoint.slice,
                    "metric": endpoint.metric, "unit": endpoint.unit,
                    "regime": regime, "strategy": "single", "N": 1,
                    "full_mean": source["full_mean"],
                    "expected_outcomes": source["expected_outcomes"],
                    "known_outcomes": source["known_outcomes"],
                    "missing_outcomes": source["missing_outcomes"],
                    "expected_items": source["expected_items"],
                    "known_items": source["known_items"],
                    "complete_items": source["complete_items"],
                    "eligible_fixed_fmt": model in candidates,
                    "fixed_candidate_count": len(candidates),
                    "fixed_candidates": ";".join(candidates),
                    "excluded_reason": "incomplete_full_endpoint:" + ";".join(incomplete) if incomplete else "",
                    "rankable_at_least_two_fixed_candidates": rankable,
                    "rank": ranks.get(model, ""),
                    "winner": model in winners,
                    "winner_set": ";".join(winners),
                    "winner_score": vals[winners[0]] if winners else "",
                    "winner_runner_up_margin": runner_up_margin if runner_up_margin is not None else "",
                    "tie_rule": "absolute_1e-12_group_highest_anchor_no_chaining",
                    "source_input": source.get("source_input", ""),
                    "source_row": source.get("source_row", ""),
                    "source_url": source.get("source_url", ""),
                })
        winners = {r: regime_data[r]["winners"] for r in REGIMES}
        changed = set(winners[REGIMES[0]]) != set(winners[REGIMES[2]]) if rankable else None
        transition = {
            "category": endpoint.category, "endpoint": endpoint.key,
            "endpoint_label": endpoint.label, "metric": endpoint.metric,
            "unit": endpoint.unit, "planned_model_count": len(MODELS),
            "fixed_candidate_count": len(candidates), "fixed_candidates": ";".join(candidates),
            "excluded_candidates": ";".join(excluded),
            "rankable_at_least_two_fixed_candidates": rankable,
            "strict_five_complete": len(candidates) == len(MODELS),
            "free_winners": ";".join(winners[REGIMES[0]]),
            "moderate_winners": ";".join(winners[REGIMES[1]]),
            "tight_winners": ";".join(winners[REGIMES[2]]),
            "free_to_tight_winner_set_changed": changed if changed is not None else "",
            "free_to_moderate_winner_set_changed": (set(winners[REGIMES[0]]) != set(winners[REGIMES[1]])) if rankable else "",
            "moderate_to_tight_winner_set_changed": (set(winners[REGIMES[1]]) != set(winners[REGIMES[2]])) if rankable else "",
            "change_definition": "winner_set_inequality; fixed_FMT_candidates; unknown_not_ranked",
        }
        transition_rows.append(transition)
        records.append({"endpoint": endpoint, "candidates": candidates, "excluded": excluded,
                        "regimes": regime_data, "rankable": rankable, "changed": changed})

    categories = {}
    for category in ("family", "task", "secondary"):
        rows = [t for t in transition_rows if t["category"] == category]
        categories[category] = {
            "planned": len(rows),
            "rankable": sum(t["rankable_at_least_two_fixed_candidates"] for t in rows),
            "changed": sum(t["free_to_tight_winner_set_changed"] is True for t in rows),
            "strict_five_complete": sum(t["strict_five_complete"] for t in rows),
            "strict_five_changed": sum(t["strict_five_complete"] and t["free_to_tight_winner_set_changed"] is True for t in rows),
        }

    def winner_cell(record, regime):
        data = record["regimes"][regime]
        return "; ".join(MODEL_LABELS[m] + " " + _score(data["values"][m]) for m in data["winners"]) or "unknown（不足两候选）"

    def winner_table(category):
        return _table(
            ["端点", "三档固定完整候选", "Free 观察第一", "Moderate 观察第一", "Tight 观察第一", "Free→Tight"],
            ([r["endpoint"].label, " / ".join(MODEL_LABELS[m] for m in r["candidates"]) or "无",
              *(winner_cell(r, regime) for regime in REGIMES),
              "换位" if r["changed"] else ("不变" if r["rankable"] else "unknown")]
             for r in records if r["endpoint"].category == category),
        )

    def order_table(category):
        return _table(
            ["端点", "Free 完整排序", "Moderate 完整排序", "Tight 完整排序"],
            ([r["endpoint"].label,
              *(" > ".join(_names(g) for g in r["regimes"][regime]["groups"]) or "unknown" for regime in REGIMES)]
             for r in records if r["endpoint"].category == category),
        )

    method = (
        "排名仅使用同一端点、同一预算的原指标，先在每个端点固定 F/M/T 三档均完整的候选集，"
        "不按每档已知结果动态增减模型。原计划五模型的所有原值、分母及排除原因保留在 "
        "[RANKINGS.csv](RANKINGS.csv)。HPO 缺失模型不补零、不用已知子集均值参与完整端点排名；"
        "排除后第一仅是该固定候选集内的观察第一。并列按未舍入分数与本组最高分 anchor 的绝对差 ≤1e-12，"
        "不使用相邻分数传递链；这是浮点等分规则，不是统计等价。名次采用 competition rank（1、2、2、4）。"
        "runner-up margin 为第一与第二个候选的分数差；并列第一记 0，不用它声称显著性。"
    )
    family, task = categories["family"], categories["task"]
    count_text = (
        f"六类家族主端点的固定完整候选排名中，Free→Tight 冠军集合换位 **{family['changed']}/{family['rankable']}**"
        f"（计划 {family['planned']} 个端点）；严格五模型全三档完整的家族子集为 "
        f"**{family['strict_five_changed']}/{family['strict_five_complete']}**。九个 HPO task 的对应计数为 "
        f"**{task['changed']}/{task['rankable']}**（计划 {task['planned']} 个），严格五模型子集为 "
        f"**{task['strict_five_changed']}/{task['strict_five_complete']}**。"
        "分子比较 Free 与 Tight 的冠军集合，不把 Moderate 暂时并列混入；"
        "Search/HPO all 与 Audit LA 只作次级展示，不再加入这些分母。"
    )
    complete_family_records = [r for r in records if r["endpoint"].category == "family" and len(r["candidates"]) == len(MODELS)]
    no_shared_winner = {}
    for regime in REGIMES:
        sets = [set(r["regimes"][regime]["winners"]) for r in complete_family_records]
        no_shared_winner[regime] = not set.intersection(*sets) if len(sets) >= 2 else None
    no_shared_text = "；".join(REGIME_LABELS[r] for r in REGIMES if no_shared_winner[r])
    interpretation = (
        (f"在五模型全完整的家族中，{no_shared_text} 都不存在跨家族共同第一名。" if no_shared_text else "")
        + "这里考察部署反馈预算程度（deployment budget degree）下的相对表现："
        "整体排序和局部冠军是否随任务、预算变化，而不是构造跨指标总榜。"
        "观察换位不意味着每个家族都会换位，也不是不同 effort、API/自部署设置已受控的纯模型因果排名。"
    )
    markers = {
        "RANK_FAMILY": method + "\n\n" + winner_table("family") + "\n\n" + order_table("family"),
        "RANK_TASK": winner_table("task") + "\n\n九 task 保持既有 item 内三次重复平均；原 Gap 不重新评分、不截断到 100。",
        "RANK_SUMMARY": count_text + "\n\n" + interpretation,
    }

    details = ["# 五模型任务 × 预算观察排名", method, count_text, interpretation]
    for category, label in (("family", "家族主端点"), ("task", "九个 HPO task"), ("secondary", "次级端点：不加入家族/task 换位分母")):
        details.extend(["## " + label, winner_table(category), order_table(category)])
        margin_rows = []
        for record in records:
            if record["endpoint"].category != category:
                continue
            margin_rows.append([record["endpoint"].label, *(_score(record["regimes"][regime]["runner_up_margin"]) for regime in REGIMES)])
        details.extend(["第一与第二候选的未标准化分差（F1/EA/LA 为 fraction，Gap 为 Gap points）：",
                        _table(["端点", "Free margin", "Moderate margin", "Tight margin"], margin_rows)])
    details.append("## 所有原计划模型：原值与分母（不完整的值不进入排名）")
    for endpoint in ENDPOINTS:
        display_rows = []
        for model in MODELS:
            cells = []
            for regime in REGIMES:
                source = selected[(endpoint.key, model, regime)]
                cells.append(f"{_score(numeric[(endpoint.key, model, regime)])} [{source['known_outcomes']}/{source['expected_outcomes']}]")
            record = next(r for r in records if r["endpoint"] == endpoint)
            missing_regimes = [REGIME_LABELS[r] for r in REGIMES if numeric[(endpoint.key, model, r)] is None]
            reason = "三档固定候选" if model in record["candidates"] else "完整端点缺失：" + "/".join(missing_regimes)
            display_rows.append([MODEL_LABELS[model], *cells, reason])
        details.extend(["### " + endpoint.label,
                        _table(["模型", "Free [known/expected]", "Moderate [known/expected]", "Tight [known/expected]", "固定候选状态"], display_rows)])
    details.append("数据为观察排名，不产生 p 值、显著性或跨指标统一总分。来源行和固定链接见 RANKINGS.csv；完整冠军集合转换见 RANK_TRANSITIONS.csv。")
    summary = {
        "schema": "five-model-fixed-fmt-ranking-v1",
        "models": list(MODELS), "regimes": list(REGIMES),
        "endpoints": len(ENDPOINTS), "ranking_rows": len(rank_rows),
        "transition_rows": len(transition_rows), "categories": categories,
        "full_five_family_no_shared_winner": no_shared_winner,
        "tie_absolute_tolerance": TIE_ATOL, "tie_relative_tolerance": 0,
        "tie_group_rule": "highest_score_anchor; no_transitive_chaining",
        "rank_rule": "descending_competition_rank",
        "winner_change_rule": "Free_vs_Tight_winner_set_inequality",
        "minimum_fixed_candidates_for_rank": 2,
        "new_scoring": False, "confirmatory_inference": False,
        "fixed_candidate_sets": {r["endpoint"].key: r["candidates"] for r in records},
    }
    files = {
        "RANKINGS.csv": _csv_bytes(rank_rows, list(rank_rows[0])),
        "RANK_TRANSITIONS.csv": _csv_bytes(transition_rows, list(transition_rows[0])),
        "RANKINGS.md": ("\n\n".join(details) + "\n").encode("utf-8"),
    }
    return markers, files, summary
