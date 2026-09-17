"""Merge evidence-backed history; never run models or reinterpret old scores."""
import argparse
import collections
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def cell(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def build(workspace):
    events, inputs = [], []
    for lane in ("selfserve", "api"):
        path = workspace / "six_model_report_20260914/history" / f"{lane}_history.json"
        blob = path.read_bytes()
        rows = json.loads(blob)
        inputs.append({"path": str(path), "sha256": hashlib.sha256(blob).hexdigest(),
                       "bytes": len(blob), "records": len(rows)})
        # Preserve every original field and accounting scope, including started,
        # failed and api_attempts, rather than treating completion as attempts.
        events.extend({"history_lane": lane, **row} for row in rows)
    assert len(events) == 72
    assert len({r["event_id"] for r in events}) == len(events)
    evidence, remote_refs = set(), set()
    for row in events:
        assert row["time_basis"] and row["matrix"] and row["evidence"]
        for ref in row["evidence"]:
            assert isinstance(ref, str), ref
            if ref.startswith(("https://", "http://")):
                remote_refs.add(ref)  # Inherited reference, not a new remote check.
            else:
                assert Path(ref).exists(), ref
                evidence.add(ref)
        if row.get("start_utc") and row.get("end_utc"):
            parse = lambda t: datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
            assert parse(row["start_utc"]) <= parse(row["end_utc"]), row["event_id"]
    events.sort(key=lambda row: (row.get("start_utc") or "9999", row["event_id"]))
    normalized = []
    accounted = {
        "history_lane", "event_id", "models", "run_id", "start_utc", "end_utc",
        "time_basis", "phase", "matrix", "planned", "executed", "scored",
        "scored_known", "count_unit", "issue_found", "followup", "final_selection",
        "evidence", "knownlimitations", "known_limitations",
    }
    for row in events:
        normalized.append({
            "event_id": row["event_id"], "lane": row["history_lane"],
            "models": row["models"], "run_id": row["run_id"],
            "start_utc": row.get("start_utc"), "end_utc": row.get("end_utc"),
            "time_basis": row["time_basis"], "phase": row["phase"],
            "matrix": row["matrix"], "planned": row.get("planned"),
            "execution_accounting": row.get("executed"),
            "score_accounting": row.get("scored", row.get("scored_known")),
            "count_unit": row.get("count_unit", "Units and scope remain explicit in each accounting object; not necessarily logical slots or strict scores."),
            "issue_found": row.get("issue_found"), "followup": row.get("followup"),
            "final_selection": row["final_selection"],
            "excluded_model_in_current_report": any("claude" in m.lower() for m in row["models"]),
            "evidence": row["evidence"],
            "known_limitations": row.get("known_limitations", row.get("knownlimitations", [])),
            "additional_accounting": {k: v for k, v in row.items() if k not in accounted},
        })
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(normalized[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows({k: cell(v) for k, v in row.items()} for row in normalized)
    md = """# 实验沿革：跑了什么，哪些被替换

[综合报告](README.zh.md) · [最终数据构成](DATA_LINEAGE.zh.md) · [全部批次 CSV](EXPERIMENT_LOG.csv) · [原字段与证据 JSON](EXPERIMENT_LOG.json)

本页只讲主线；CSV/JSON 保留 **72 条可证实的批次/阶段记录**，含模型、矩阵、实际 UTC 时间、发现的问题、后续处理、最终取舍及原记录路径。它们包括 smoke、pilot、正式运行、计划和恢复，**不是 72 次独立完整实验**。记录整理于 2026-09-15 UTC，沿用 9/13 冻结结果及 9/14 Gemini 核验。

## 矩阵口径

下表“正式矩阵”均指每模型 **783 个逻辑项**：

- ExpGym N1：417 项，Free/Moderate/Tight；Search 73 题 × R1，Audit 13 文档 × 3 固定顺序，HPO 9 任务 × R3。
- N4：366 池，Moderate/Tight × naive/cached/poolact；Search whois 39 题 × R1，Audit 13 文档 × R1，NAS101 A/B/C × R3。

旧 Kimi textual 和旧双模型 R3 使用不同矩阵，不与当前 783 项混算。N1 单体、N4 整池、进程 invocation 和 API 调用也不是同一单位。

## 主时间线（2026 年，UTC）

| 时间 | 模型与实际运行范围 | 后来发现的问题 | 后续 / 最终采用 |
|---|---|---|---|
| 9/7 | Kimi textual v1、v2；各计划 342 进程，对应 303 N1 + 513 N4 池；分别完成 40、45 进程后停止 | v1 答案标签误解析、无效 NAS 配置异常；v2 子串匹配错绑配置 | 修复后统一 v3；旧结果不采用，保留原件 |
| 9/7 | Kimi textual v3；342/342 进程完成，含同版本 pilot 推广 | 后续识别 textual/native 提示适配、截断及 NAS 提示边界 | 转为 native 新研究；v3 不进入当前报告 |
| 9/8–9 | Kimi/GLM native 协议、任务 smoke、pilot 与开发验证 | 文本 Action 指令与 native 工具冲突；provider abort 错当成功；部分严格协议验证失败；一次 Slurm 取消 | 修复后另建验证 cohort；原失败保留，不混入正式分母 |
| 9/9 | 旧双模型 R3：各计划 1,845 invocations；Kimi 闭合 295，GLM 闭合 67（64 工程通过、3 失败） | GLM 缺答触发整池失败及终态落盘问题；用户调整重复设计 | 旧 R3 可恢复归档，未删除；改为当前正式矩阵另跑 |
| 9/9 | GLM 正式矩阵：783/783 | 59 名 agent 缺最终答案，按当时任务政策保留；后续发现 NAS 图身份和 Audit 提示问题 | 原结果保留 717 项；9/12 替换 66 池 |
| 9/9–10 | Kimi 正式：705 invocations 中 697 完成、8 NODE_FAIL；固定八项恢复后 783 逻辑项完整 | 节点故障；后续发现 NAS 图身份问题 | 八项仅作基础设施恢复；其后保留 756 项，9/12 替换 27 池 |
| 9/10–11 | Qwen 正式矩阵：首 session 真执行 388，续跑真执行剩余 395 | 正式前 Mamba page-size 启动兼容问题已修；后来发现通用图/提示问题，但未选为重大影响重跑范围 | 全部 783 项保留；续跑核验的 388 项没有再次调用模型 |
| 9/10–11 | GPT Medium 正式矩阵：783 执行完成、782 严格评分完整 | 一池 NAS 有 agent 达到本地上下文准入上限，未交最终配置 | 9/12 修订本地上限并整组三策略重跑 27 池；原结果保留 756 项 |
| 9/10–12 | Claude High：仅 N4 366 池；原段 108 + recovery v1 148 + v2 110；312 池严格评分完整 | 额度耗尽及调度/传输恢复问题；大量显式拒答，NAS 缺配置 | 历史与恢复记录保留；按本次要求从所有结果比较中排除，无 Claude N1 |
| 9/11 | DeepSeek 正式矩阵：783 执行完成、728 严格评分完整 | 92 名 agent 缺 NAS 配置；后查有异常生成、NAS 图身份碰撞及 native Audit 提示冲突 | 原结果保留 534 项，9/12 替换 249 池；reasoning-token 字段修订只影响分析投影，不是模型重跑 |
| 9/11 | Gemini 非流式/流式探针、smoke、33 项 pilot、9 项修订 pilot | 非流式工具协议不完整；网关签名/会话问题及 integer enum schema 兼容问题 | 正式前完成传输/协议修正；pilot 不加入正式结果；v1/v2 未启动的正式计划不算执行 |
| 9/11–12 | Gemini 正式 v3：原段完成 76，恢复仅补未开始项 691，共 767/783 | 保留 1 个上游 MALFORMED_FUNCTION_CALL 失败；另有 15 个 HPO 未完成项，研究仍暂停 | 当前采用这 767 项；9/14 核验未变化。不以完成子集冒充完整 HPO |
| 9/12 | DeepSeek 40 次选定首请求回放；DeepSeek/GLM 共 13 个完成的 N2 诊断池，12 个用于 matched 对照 | 一个 helper 改了 schema 顺序；GLM 两池未启动，随后补做完整三策略诊断；修复图/提示，并有限验证 DeepSeek 多流重叠关闭候选 | 原件保留，修订 helper 后继续验证；旧 GLM 一池被新匹配组替换，全部仅作诊断，不进正式 N4 分母 |
| 9/12 | 定向 N4：Kimi NAS Tight 27；GLM NAS Tight 27 + Audit Tight 39；DeepSeek Audit M/T 78 + NAS M/T 54 + Search Moderate 117 | 针对已确认的重要影响；DeepSeek 同时调整 serving 设置 | 合计 342 池全部采用新结果，均同题同预算整组三策略替换；不是只保留升分项 |
| 9/12 | GPT NAS Moderate 三策略 × R3：27 池 | 首池发生连接失败，12 次失败 HTTP 尝试保留；另有未进入 API 的启动失败 | 连接恢复后首池 1 + 剩余 26，27 池全采用；实际池尝试 28 次，不是 28 个科学槽 |

## 最终报告到底用了哪几轮

| 模型 | 最终采用的逻辑项 |
|---|---|
| Kimi | 9/9–10 正式/固定八项恢复中保留 756 + 9/12 重跑 27 = **783** |
| GLM | 9/9 正式保留 717 + 9/12 重跑 66 = **783** |
| Qwen | 9/10–11 正式 **783**，没有 9/12 定向重跑 |
| DeepSeek | 9/11 正式保留 534 + 9/12 重跑 249 = **783** |
| GPT | 9/10–11 正式保留 756 + 9/12 重跑 27 = **783** |
| Gemini | 原段 76 + 仅补未开始项 691 = **767**；另 1 失败、15 未完成 |

重跑共 **369 池**，替换旧槽而非新增样本。所有 N1 预算退化和排名结果仍来自各模型原正式单体数据。精确到设置、版本、执行时间和原始 dump 的映射见 [DATA_LINEAGE](DATA_LINEAGE.zh.md) 与 [存档索引](ARCHIVE_INDEX.md)。

## 查阅规则

- **不要把各阶段计划量相加。** pilot 推广、断点续跑、固定槽恢复与定向替换有重叠；Claude 的 366/258/110 计划不是 734 个独立池。
- **执行完成不等于有严格分数。** CSV 的 API `execution_accounting` 是完成量；已开始但失败的 GPT 首池另记在 `additional_accounting` 的 started/failed/api_attempts。自托管字段保留各自单位；早期 progress/journal 账数不是新做的独立评分验证。
- **问题不等于已证明性能因果。** 9/12 范围参考旧结果后固定，属于定向探索；多项代码/提示/部署修订并存。未重跑范围仍保留原版本，不能称“六模型全量同版重跑”。
- **覆盖边界明确。** 72 条覆盖现有记录可证实的 cohort、主要探针、恢复及未执行计划；不声称重建未留日志的临时命令。未知起止时间为 null；有时间的记录注明来自队列、请求或控制器，不能互换成 GPU 时长。
- 9/13 综合分析、9/14 Gemini/Claude 只读复核、本次六模型重排均不是新实验。本次没有新增 API/GPU、重评分、删除原数据或重新封包。

机器日志的 `used/mixed/replaced/validation_only/not_used` 表示历史段最终取舍；`mixed` 是部分被新结果替换。Claude 的验证记录虽保留历史含义，但均不进入当前报告。原字段和所有证据路径保留在 JSON，不把局部探针通过写成整套评测无问题。
"""
    scope = {
        "schema": "evidence-backed-experiment-history.v1",
        "compiled_utc_date": "2026-09-15",
        "coverage": "Identifiable retained cohorts, major probes, recoveries and plan-only records; not every HTTP request or unlogged command.",
        "count_warning": "Overlapping plans, continuations and replacements are not independent experiments. Preserve each accounting unit and scope.",
        "claude": "History only; excluded from all current performance comparisons.",
        "input_files": inputs, "events": events,
    }
    checks = {"inputs": inputs, "records": len(events), "unique_ids": len(events),
              "evidence_paths_exist": len(evidence),
              "inherited_remote_refs_not_rechecked": sorted(remote_refs),
              "phase_record_counts_not_experiment_totals": dict(collections.Counter(r["phase"] for r in events)),
              "unknown_start_records": sum(not r.get("start_utc") for r in events),
              "unknown_end_records": sum(not r.get("end_utc") for r in events),
              "input_fields_preserved": True, "new_model_or_scorer_calls": False}
    for item in inputs:
        assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() == item["sha256"]
    return {"EXPERIMENT_LOG.json": encoded(scope), "EXPERIMENT_LOG.csv": out.getvalue().encode(),
            "EXPERIMENT_LOG.zh.md": md.encode(), "HISTORY_INPUTS.json": encoded(checks)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=HERE.parents[3])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build(args.workspace)
    for name, blob in outputs.items():
        path = HERE / name
        if args.check:
            assert path.read_bytes() == blob, name
        else:
            path.write_bytes(blob)
    print(json.dumps({"files": len(outputs), "check": args.check, "passed": True}))
