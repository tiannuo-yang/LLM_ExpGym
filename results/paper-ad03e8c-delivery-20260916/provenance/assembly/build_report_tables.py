#!/usr/bin/env python3
"""Export the immutable ad03 report and produce lossless wide comparisons.

Only reads Git objects; never reads or scores trajectories, changes experiment
selection, or substitutes known-subset means for missing complete means.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote

COMMIT = "ad03e8c42ca501016176ee1bc407b38499178506"
WORKSPACE = Path("/lustrefs/users/chufan.shi/codex_space_tn")
REPO = WORKSPACE / "publication/five_model_report_20260911"
DEST = WORKSPACE / "deliveries/paper-ad03e8c-20260916"
PAPER = "results/paper-analysis-20260916"
LINEAGE = "results/six-models-lineage-20260914"
MODELS = {
    "kimi-k3", "glm-5.3", "qwen3.8-2.4t-a95b-fp8",
    "deepseek-v4-flash-0731", "gpt-5.6-sol", "gemini-3.8-flash-medium",
}
CORE_CSV = (
    "absolute_settings.csv", "contrasts.csv", "by_repeat.csv",
    "main_expgym.csv", "main_poolact.csv", "family_rankings.csv",
    "rank_transitions.csv", "SOURCE_SELECTION.csv", "DATA_LINEAGE.csv",
    "SCORE_COMPLETENESS.csv", "EXPERIMENT_LOG.csv",
)
GROUP_FIELDS = (
    "model", "system", "scenario", "slice_kind", "slice", "metric", "unit", "N",
)
ARMS = ("free", "moderate", "tight", "naive", "cached", "poolact")
ARM_FIELDS = (
    "full_mean", "expected_units", "known_units", "missing_units",
    "absolute_record", "cohort_id",
)
DELTA_PAIRS = (
    ("moderate", "free"), ("tight", "free"), ("tight", "moderate"),
    ("cached", "naive"), ("poolact", "naive"), ("poolact", "cached"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jbytes(obj: object) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def read_csv(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def csv_bytes(rows: list[dict[str, str]], fields: list[str]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def number(value: str) -> Decimal | None:
    if not value.strip() or value.lower() in {"nan", "none", "null"}:
        return None
    value_d = Decimal(value)
    assert value_d.is_finite(), value
    return value_d


def difference(row: dict[str, str], to: str, before: str) -> str:
    a, b = number(row[f"{to}_full_mean"]), number(row[f"{before}_full_mean"])
    return "" if a is None or b is None else str(a - b)


def key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row[k] for k in GROUP_FIELDS)


def make_comparisons(absolute: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    groups: dict[tuple[str, ...], dict[str, tuple[int, dict[str, str]]]] = defaultdict(dict)
    for record, row in enumerate(absolute, 1):
        assert row["model"] in MODELS, row["model"]
        if row["system"] == "expgym":
            assert row["strategy"] == "single" and row["N"] == "1", row
            group = key(row) + ("",)
            arm = {"cost_free": "free", "cost_moderate": "moderate", "cost_tight": "tight"}[row["regime"]]
        else:
            assert row["system"] == "poolact" and row["N"] == "4", row
            assert row["regime"] in {"cost_moderate", "cost_tight"}, row
            group = key(row) + (row["regime"],)
            arm = row["strategy"]
            assert arm in {"naive", "cached", "poolact"}, row
        assert arm not in groups[group], (group, arm)
        groups[group][arm] = (record, row)
    fields = ["comparison", *GROUP_FIELDS, "regime", "analysis_unit", "report_scale", "report_score_unit", "report_delta_unit", "complete"]
    fields += [f"{arm}_{field}" for arm in ARMS for field in ARM_FIELDS]
    fields += [f"{a}_minus_{b}" for a, b in DELTA_PAIRS]
    output = []
    for group, arms in sorted(groups.items()):
        expect = {"free", "moderate", "tight"} if group[1] == "expgym" else {"naive", "cached", "poolact"}
        assert set(arms) == expect, (group, arms.keys())
        row = dict(zip((*GROUP_FIELDS, "regime"), group))
        row["comparison"] = "N1_budget" if group[1] == "expgym" else "N4_strategy"
        analysis_units = {r["analysis_unit"] for _, r in arms.values()}
        assert len(analysis_units) == 1, (group, analysis_units)
        row["analysis_unit"] = next(iter(analysis_units))
        row["report_scale"] = "100" if row["unit"] == "fraction" else "1"
        row["report_score_unit"] = "0–100" if row["unit"] == "fraction" else row["unit"]
        row["report_delta_unit"] = "percentage_points" if row["unit"] == "fraction" else row["unit"]
        row["complete"] = str(all(number(r["full_mean"]) is not None for _, r in arms.values())).lower()
        for arm in ARMS:
            for field in ARM_FIELDS:
                if arm not in arms:
                    row[f"{arm}_{field}"] = ""
                elif field == "absolute_record":
                    row[f"{arm}_{field}"] = str(arms[arm][0])
                else:
                    row[f"{arm}_{field}"] = arms[arm][1][field]
        for a, b in DELTA_PAIRS:
            row[f"{a}_minus_{b}"] = difference(row, a, b)
        output.append(row)
    return output, fields


def check_comparisons(rows: list[dict[str, str]], absolute: list[dict[str, str]], contrasts: list[dict[str, str]]) -> dict:
    reconstructed = 0
    for row in rows:
        for arm in ARMS:
            record = row[f"{arm}_absolute_record"]
            if not record:
                continue
            source = absolute[int(record) - 1]
            assert row[f"{arm}_full_mean"] == source["full_mean"]
            assert key(row) == key(source)
            for field in ARM_FIELDS:
                if field != "absolute_record":
                    assert row[f"{arm}_{field}"] == source[field]
            reconstructed += 1
    assert reconstructed == len(absolute)
    lookup = {key(row) + (row["regime"],): row for row in rows}
    checked = 0
    for old in contrasts:
        # A task can have different historical IDs in original and rerun
        # sources; cross-budget N4 comparisons do not belong to this view.
        if old["system"] == "poolact" and old["from_regime"] != old["to_regime"]:
            continue
        group = key(old) + (("" if old["system"] == "expgym" else old["from_regime"]),)
        row = lookup[group]
        if old["system"] == "expgym":
            a, b = old["to_regime"].removeprefix("cost_"), old["from_regime"].removeprefix("cost_")
        else:
            a, b = old["to_strategy"], old["from_strategy"]
        field = f"{a}_minus_{b}"
        if field not in row:
            continue
        got, expected = number(row[field]), number(old["delta"])
        assert (got is None) == (expected is None), (group, field)
        if got is not None:
            # Original contrasts used binary floats. New columns subtract exact
            # stored decimal strings; both must agree to negligible arithmetic error.
            assert abs(got - expected) < Decimal("1e-11"), (group, field, got, expected)
        checked += 1
    return {"all_absolute_rows_roundtripped": reconstructed, "contrasts_checked": checked}


def build(repo: Path, dest: Path, check: bool) -> dict:
    assert git(repo, "rev-parse", f"{COMMIT}^{{commit}}").decode().strip() == COMMIT
    paths = git(repo, "ls-tree", "-r", "--name-only", COMMIT, PAPER, LINEAGE).decode().splitlines()
    assert len([p for p in paths if p.startswith(PAPER + "/")]) == 70
    frozen = {path: git(repo, "show", f"{COMMIT}:{path}") for path in paths}
    outputs: dict[str, bytes] = {}
    exported = []
    for source, data in sorted(frozen.items()):
        targets = [f"report/{source}"]
        if source.startswith(LINEAGE + "/") and source.split("/")[-1] in CORE_CSV:
            targets.append("csv/" + source.split("/")[-1])
        if source.startswith(PAPER + "/") and source.endswith(".csv"):
            targets.append("csv/paper/" + source.removeprefix(PAPER + "/"))
        for target in targets:
            outputs[target] = data
        exported.append({
            "source_commit": COMMIT, "source_path": source,
            "git_blob": git(repo, "rev-parse", f"{COMMIT}:{source}").decode().strip(),
            "bytes": len(data), "sha256": sha(data), "destinations": targets,
        })
    source_csv = {name: read_csv(frozen[f"{LINEAGE}/{name}"]) for name in CORE_CSV}
    absolute = source_csv["absolute_settings.csv"]
    comparisons, fields = make_comparisons(absolute)
    checks = check_comparisons(comparisons, absolute, source_csv["contrasts.csv"])
    outputs["csv/COMPARISON.csv"] = csv_bytes(comparisons, fields)
    for system, filename, selected_arms in (
        ("expgym", "N1_BUDGET_COMPARISON.csv", {"free", "moderate", "tight"}),
        ("poolact", "N4_STRATEGY_COMPARISON.csv", {"naive", "cached", "poolact"}),
    ):
        selected_fields = [f for f in fields if not any(f.startswith(a + "_") for a in set(ARMS) - selected_arms)]
        selected_rows = [{f: row[f] for f in selected_fields} for row in comparisons if row["system"] == system]
        outputs[f"csv/{filename}"] = csv_bytes(selected_rows, selected_fields)
    primary_keys = {key(row) + ("" if row["system"] == "expgym" else row["regime"],)
                    for name in ("main_expgym.csv", "main_poolact.csv") for row in source_csv[name]}
    primary = [row for row in comparisons if key(row) + (row["regime"],) in primary_keys]
    assert len(primary) == len(primary_keys)
    outputs["csv/MAIN_COMPARISON.csv"] = csv_bytes(primary, fields)
    # Keep relative report links intact. Historical absolute local paths and
    # pinned GitHub URLs intentionally retain their original source meaning.
    links_checked = 0
    unresolved_relative_links = []
    for relative, data in outputs.items():
        if not relative.startswith("report/") or not relative.endswith(".md"):
            continue
        for target in re.findall(r"\]\(([^\s)]+)(?:\s+[^)]*)?\)", data.decode()):
            target = unquote(target.split("#", 1)[0])
            if not target or "://" in target or target.startswith(("/", "mailto:")):
                continue
            resolved = (dest / relative).parent.joinpath(target).resolve()
            try:
                local = str(resolved.relative_to(dest.resolve()))
            except ValueError:
                unresolved_relative_links.append({"file": relative, "target": target})
                continue
            if local not in outputs:
                unresolved_relative_links.append({"file": relative, "target": target})
            else:
                links_checked += 1
    assert not unresolved_relative_links, unresolved_relative_links
    checks.update({
        "source_commit": COMMIT, "git_source_files": len(frozen),
        "paper_source_files": 70, "relative_markdown_links_verified": links_checked,
        "comparison_rows": len(comparisons), "primary_comparison_rows": len(primary),
        "comparison_by_kind": dict(Counter(r["comparison"] for r in comparisons)),
        "incomplete_comparison_groups": sum(r["complete"] == "false" for r in comparisons),
        "models": sorted(MODELS), "no_model_calls": True, "no_rescoring": True,
        "source_bytes_unchanged": True, "missing_full_means_not_imputed": True,
    })
    outputs["report/EXPORTS.json"] = jbytes({
        "schema_version": 1, "source_commit": COMMIT,
        "note": "Immutable Git exports; CSV convenience copies are byte-identical. Historical local paths remain historical references; the delivery's relocated raw index is authoritative for bundled data.",
        "exports": exported,
    })
    dictionary = """# CSV 入口与比较口径

这组表固定于报告提交 `ad03e8c42ca501016176ee1bc407b38499178506`；不采用后续报告或运行状态。
原始表逐字节导出；新增宽表只对 `absolute_settings.csv` 的未舍入 `full_mean` 做透视与减法，未重评分。

## 先看哪张表

| 文件 | 每行代表什么 | 用途 |
| --- | --- | --- |
| [MAIN_COMPARISON.csv](MAIN_COMPARISON.csv) | 一个模型 × 主场景 × 主指标；N1 三预算或 N4 同预算三策略 | 最短比较入口，指标范围对应冻结 `main_expgym/main_poolact` |
| [COMPARISON.csv](COMPARISON.csv) | 一个模型 × 场景 × 切片 × 指标；N1 三预算或 N4 同预算三策略 | 全指标合并宽表，包含家族/具体任务与次指标 |
| [N1_BUDGET_COMPARISON.csv](N1_BUDGET_COMPARISON.csv) | 一个模型 × 场景 × 切片 × 指标 | Free / Moderate / Tight 及预算差 |
| [N4_STRATEGY_COMPARISON.csv](N4_STRATEGY_COMPARISON.csv) | 一个模型 × 场景 × 切片 × 指标 × 预算 | naive / cached / poolact 及策略差 |
| [absolute_settings.csv](absolute_settings.csv) | 一个模型—预算—策略—切片—指标设置 | 完整原均值、已知子集均值、分母、时间和来源 |
| [contrasts.csv](contrasts.csv) | 一个有方向的同指标比较 | 原报告逐比较差值、可比完整度 |
| [by_repeat.csv](by_repeat.csv) | 一个设置 × 已有重复/顺序标签 | 冻结重复层出口；不能把 R1 伪装成多次重复 |
| [main_expgym.csv](main_expgym.csv)、[main_poolact.csv](main_poolact.csv) | 主指标设置 | 原报告主表入口，保留显示值和完整状态 |
| [family_rankings.csv](family_rankings.csv)、[rank_transitions.csv](rank_transitions.csv) | 家族—预算排名或相同候选集的排名变化 | 必须保留可比模型集，不跨缺失集合比较冠军 |
| [SOURCE_SELECTION.csv](SOURCE_SELECTION.csv) | 被采用/替换的来源设置记录 | 解释哪些原运行由注册的重跑整组替换 |
| [DATA_LINEAGE.csv](DATA_LINEAGE.csv) | 一个模型—系统—场景—预算—策略主指标 | 运行来源、时间、原始 dump 入口与原提交 |
| [SCORE_COMPLETENESS.csv](SCORE_COMPLETENESS.csv) | 一个来源/设置的计划与评分计数 | 区分已执行、可评分、失败和未完成 |
| [EXPERIMENT_LOG.csv](EXPERIMENT_LOG.csv) | 一次实验/修补/恢复批次 | 历史日志含被排除的 Claude 批次，不进入六模型比较 |

## 新增宽表字段

- `comparison`：`N1_budget` 或 `N4_strategy`。N1 的 `regime` 留空，因为一行同时容纳三档；N4 的 `regime` 指明 Moderate/Tight。
- `slice_kind` / `slice`：`all`、家族或具体任务等原切片身份。不同层级重叠，不可把所有行再平均。
- `metric` / `unit` / `N` / `analysis_unit`：继承原指标、原单位、智能体数和聚合单位。不同指标不可合成总分。
- `{arm}_full_mean`：原 CSV 的完整均值字符串；未舍入、未缩放、未填补。`arm` 为 free/moderate/tight/naive/cached/poolact。
- `*_minus_*`：列名方向的差值，例如 `tight_minus_free`、`poolact_minus_cached`；用原均值十进制字符串相减，不用两位显示值。
- `unit=fraction` 时均值和差值仍是原 0–1 数值；乘 `report_scale=100` 才是报告 0–100 分数及百分点差。其他单位原样保留，`report_scale=1`。`report_score_unit` / `report_delta_unit` 仅说明转换后的单位，不表示数据已转换。
- `{arm}_absolute_record`：`absolute_settings.csv` 的一基数据记录号，不含表头；可定位完整时间、上游源行、重复分母、已知子集等字段。不是含表头的文本行号。
- `{arm}_cohort_id`：原运行/重跑身份；同一模型的 N1 与 N4 可能来自不同批次。来源不因新旧分数高低重新选择。
- `{arm}_expected_units` / `known_units` / `missing_units`：原冻结聚合单位计数；调优按任务、审计按文档，不等于所有逻辑运行数或池内成员数。
- `complete`：该行三个有效实验臂的 `full_mean` 均存在。两臂可比时仍保留该对差值，即使第三臂不完整。

空值有两种原因：不适用的臂（N1 无三种池策略；N4 无 Free 池），或已计划但缺少完整分数。
前者没有 `absolute_record`，后者有来源记录与缺失分母。只在两端完整时计算差值。
正常结束但未交付配置的零效用只属于原定义的 Gap0；严格 Gap 仍缺失。失败/未完成均不补零。

## 论文派生表与 trajectory

`paper/` 按原报告目录收齐所有分析 CSV；这些是已冻结的派生表，不是对新轨迹的重新运行：

- `paper/rank/`：预算效应、七维度分数/候选集合、任务级 regret。
- `paper/search/`：一行一条 N1 Search trajectory、模型/家族汇总、Free/Tight 配对与代表例。
- `paper/hpo/`：一行一条 HPO trajectory、逐可见配置评估事件、配对和聚合。
- `paper/audit/`：轨迹、文档、假设呈现、证据补全配对；假设呈现不是独立文档。
- `paper/poolact/`：主要/全部指标与场景宏均值；`coordination/` 分别是审计池、池内成员、模型—预算—策略汇总。
- `paper/cases/`：DeepSeek 交付分解与成对明细；四个案例原件索引见 `../report/results/paper-analysis-20260916/cases/`。

原报告及方法附件保留原文，不修订其论述。报告侧源文件、Git blob 和 SHA256 见 `../report/EXPORTS.json`；
新增宽表校验见 `COMPARISON_CHECKS.json`，文件身份与行数见 `GENERATED.json`。
原 CSV 中绝对路径和历史链接仍用于证明原来源，不自动改写；交付包内 raw/trajectory 的新位置以包级索引为准。
"""
    outputs["csv/CSV_DICTIONARY.zh.md"] = dictionary.encode()
    outputs["csv/COMPARISON_CHECKS.json"] = jbytes(checks)
    csv_inventory = []
    for relative, data in sorted(outputs.items()):
        if relative.startswith("csv/") and relative.endswith(".csv"):
            csv_inventory.append({"path": relative, "bytes": len(data), "sha256": sha(data), "rows": len(read_csv(data))})
    outputs["csv/GENERATED.json"] = jbytes({
        "source_commit": COMMIT, "source": f"report/{LINEAGE}/absolute_settings.csv",
        "arithmetic": "Full source decimal strings preserved; deltas calculated with Decimal without presentation rounding.",
        "source_export_index": "../report/EXPORTS.json", "csv_files": csv_inventory,
        "note": "The four COMPARISON-named files are new views; all other CSVs are exact immutable source copies.",
    })
    for relative, data in sorted(outputs.items()):
        target = dest / relative
        if check:
            assert target.is_file(), relative
            assert target.read_bytes() == data, f"Mismatch: {relative}"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return {**checks, "output_files": len(outputs), "output_bytes": sum(map(len, outputs.values())),
            "csv_files": len(csv_inventory), "mode": "check" if check else "write", "status": "PASS"}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=REPO)
    p.add_argument("--dest", type=Path, default=DEST)
    p.add_argument("--check", action="store_true", help="Reconstruct expected output and compare without writes")
    args = p.parse_args()
    print(json.dumps(build(args.repo.resolve(), args.dest.resolve(), args.check), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
