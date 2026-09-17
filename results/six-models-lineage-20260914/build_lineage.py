"""Build six-model provenance from frozen metadata, without raw/model/scorer calls."""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = ["kimi-k3", "glm-5.3", "qwen3.8-2.4t-a95b-fp8", "deepseek-v4-flash-0731", "gpt-5.6-sol", "gemini-3.8-flash-medium"]
LABELS = dict(zip(MODELS, ["Kimi K3", "GLM 5.3", "Qwen 3.8", "DeepSeek V4 Flash 0731", "GPT-5.6-sol Medium", "Gemini 3.8 Flash Medium"]))
SCENES = {"tuning": "NAS101", "restricted_search": "Search whois", "evidence_audit": "Audit"}
BUDGETS = {"cost_free": "Free", "cost_moderate": "Moderate", "cost_tight": "Tight"}


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def csv_encoded(rows):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def build(workspace):
    inputs = []

    def read(relative):
        path = workspace / relative
        blob = path.read_bytes()
        inputs.append({"path": str(path), "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()})
        return blob

    source = json.loads(read("all_model_report_20260913/catalog/SOURCE_INDEX.json"))
    archive = json.loads(read("all_model_report_20260913/catalog/ARCHIVE_INDEX.json"))
    manifest = json.loads(read("all_model_report_20260913/report_v3/manifest.json"))
    scores = list(csv.DictReader(io.StringIO(read("all_model_report_20260913/report_v3/SCORE_COMPLETENESS.csv").decode())))
    gemini = json.loads(read("gemini_usability_review_20260914/integrity/CURRENT_INTEGRITY.json"))
    rows = [r for r in scores if r["model"] in MODELS]
    cohorts = [c for c in source["cohorts"] if c["model"] in MODELS]
    cmap = {c["id"]: c for c in cohorts}
    entries = {e["cohort_id"]: e for e in archive["cohort_entry_points"] if e["model"] in MODELS}
    assert len(rows) == 162 and len(cohorts) == 10
    assert len({tuple(r[k] for k in ("model", "system", "scenario", "regime", "strategy")) for r in rows}) == len(rows)
    assert not gemini["changed_slots"] and not gemini["issues"]
    final_by_model = {m["id"]: m for m in manifest["models"] if m["id"] in MODELS}
    totals = collections.Counter()
    replacements = collections.defaultdict(list)
    lineage = []
    for r in rows:
        c = cmap[r["cohort_id"]]
        totals[r["model"]] += int(r["planned_logical_jobs"])
        entry = entries.get(c["id"], {})
        if "rerun" in c["id"]:
            replacements[(r["model"], r["scenario"], r["regime"])].append(r)
        lineage.append({**r,
            "source_commits": ";".join(v.get("commit", "") for v in c["source_versions"]),
            "source_tree_sha256": ";".join(v.get("source_tree_sha256", "") for v in c["source_versions"]),
            "source_run_segments_json": json.dumps(c.get("execution_segments") or c.get("execution_timeline"), ensure_ascii=False, sort_keys=True),
            "local_raw_roots_json": json.dumps(c.get("local_raw_roots"), ensure_ascii=False),
            "local_member_source_index": c.get("full_source_index_path") or "",
            "raw_entry_url": entry.get("raw_entry_url") or "",
            "raw_index_url": entry.get("raw_archive_index_url") or "",
            "source_report_url": c.get("full_report_url") or "",
        })
    assert all(totals[m] == final_by_model[m]["planned"] == 783 for m in MODELS)
    assert len(replacements) == 9
    rerun_counts = collections.Counter()
    for (model, scenario, budget), selected in replacements.items():
        assert {r["strategy"] for r in selected} == {"naive", "cached", "poolact"}
        assert all(r["system"] == "poolact" for r in selected)
        rerun_counts[model] += sum(int(r["planned_logical_jobs"]) for r in selected)
    assert sum(rerun_counts.values()) == 369
    expected_counts = {"kimi-k3": 27, "glm-5.3": 66, "deepseek-v4-flash-0731": 249, "gpt-5.6-sol": 27}
    assert dict(rerun_counts) == expected_counts
    md = ["# 最终结果由哪些数据组成", "", "[主报告](README.zh.md) · [实验沿革](EXPERIMENT_LOG.zh.md) · [逐设置来源 CSV](DATA_LINEAGE.csv) · [原始数据索引](ARCHIVE_INDEX.md)", "",
          "最终使用六模型；Claude 仅保留在历史日志，不参加分数、排名或方向统计。Gemini 的 9 月 13 日快照经 9 月 14 日 23:45 UTC 核验，767 个完成项均未变化。", "",
          "## 一眼看清最终构成", "", "| 模型 | 原正式数据仍采用 | 9/12 重跑替换 | 最终完成 / 计划 |", "|---|---:|---:|---:|"]
    for model in MODELS:
        completed = final_by_model[model]["execution_complete"]
        n = rerun_counts[model]
        base = str(completed - n) if model != MODELS[-1] else "原始 76 + 恢复 691"
        md.append(f"| {LABELS[model]} | {base} | {n} | {completed} / 783 |")
    md.extend(["", "计数是逻辑执行项（N1 单次运行或 N4 整池），不是独立样本数。Kimi/GLM 的原始 Audit 将三个顺序合在一次进程里，因此原 705 次物理 invocation 对应 783 个逻辑项；这里统一按逻辑项计。重跑是替换，不额外增加最终样本量。", "",
               "## 哪些范围被重跑替换", "", "下表均为 **N4 × naive/cached/poolact 三策略完整替换**；同一组的新结果无论升降均采用，其余范围仍用原结果。所有 N1 结果都没有参与 9/12 的定向重跑。", "",
               "| 模型 | 场景 | 预算 | 替换池数 |", "|---|---|---|---:|"])
    for key in sorted(replacements, key=lambda k: (MODELS.index(k[0]), k[1], k[2])):
        model, scenario, budget = key
        n = sum(int(r["planned_logical_jobs"]) for r in replacements[key])
        md.append(f"| {LABELS[model]} | {SCENES[scenario]} | {BUDGETS[budget]} | {n} |")
    md.extend(["", "选择这 9 组时参考过旧结果，因此是定向、探索性重跑，不是盲选实验。旧新之间含代码、提示及部署变化，不能把差值全部归因于某一个补丁。旧分数和失败记录没有删除。", "",
               "## 来源与日期", "", "以下均为 2026 年 UTC，显示到分钟；原始时间戳和计时依据见 CSV / JSON。", "", "| 来源 ID | 实际运行 UTC | 代码版本 |", "|---|---|---|"])
    for c in cohorts:
        segments = c.get("execution_segments") or []
        if c["id"] == "gemini_snapshot":
            period = "09/11 起；最后完成 09/12 12:39；研究未关闭"
        elif segments:
            starts = [s["start_utc"] for s in segments if s.get("start_utc")]
            ends = [s["end_utc"] for s in segments if s.get("end_utc")]
            short = lambda t: t[:16].replace("2026-", "").replace("T", " ")
            period = (short(min(starts)) if starts else "未知") + " — " + (short(max(ends)) if ends else "未知")
        else:
            period = "见逐设置来源 CSV"
        versions = "; ".join(dict.fromkeys(v.get("commit", "unknown")[:12] for v in c["source_versions"]))
        md.append(f"| `{c['id']}` | {period} | `{versions}` |")
    md.extend(["", "上表不同来源的时间依据可能是队列首/末事件或 API 请求观察窗，不能相减后混充纯 GPU 计算时长。完整时间依据、源码指纹、请求配置及原始目录保留在 [SOURCE_INDEX.json](SOURCE_INDEX.json)。", "",
               "## 如何追到原件", "", "1. 在 `absolute_settings.csv` 找到设置及 `cohort_id`。", "2. 在 `DATA_LINEAGE.csv` / `SOURCE_SELECTION.csv` 查采用或被替换的来源；`source_row` 为去掉表头后的第几条数据记录，从 1 开始。", "3. 从 `ARCHIVE_INDEX.md` 进入该来源的 member/shard 清单；Gemini 通过来源索引和固定槽位映射找到原始/恢复的具体 job、completion、trace 与 API dump。", "",
               "失败、未启动及暂停项仍是 unknown；DeepSeek 的 11 个严格评分不完整项保留原严格缺失和单列 Gap0，不借用旧成功值。Gemini 未完成的 15 项不补零，也未用完成子集假冒完整 HPO 场景。", ""])

    selected_archives = [entries[c["id"]] for c in cohorts if c["id"] in entries]
    api = archive["original_api_local_delivery"]
    gpt_collections = [c for c in api["collections"] if "gpt" in (str(c.get("id", "")) + str(c.get("study_id", ""))).lower()]
    assert len(gpt_collections) == 1
    gemini_entry = next(x for x in archive["latest_local_source_indexes"] if x["model"] == MODELS[-1])
    arch = {"schema": "six-model-existing-archive-index.v1", "models": MODELS,
            "evidence_scope": "Inherited explicit archive/member/shard identities; no tar payload reread, reseal, remote verification, or original-data publication in this revision.",
            "cohort_entry_points": selected_archives,
            "published_four_model_parent": archive["published_four_model_parent"],
            "targeted_rerun": archive["targeted_rerun"],
            "original_gpt_local_delivery": {"delivery_root": api["delivery_root"], "public_raw_url": None,
                 "restore": api["restore"], "collections": gpt_collections,
                 "shared_metadata_note": "Original combined GPT/Claude delivery shared controls remain at the original delivery root; not extra performance results."},
            "gemini_snapshot": gemini_entry,
            "gemini_original_closed_segment": next(x for x in archive["claude_gemini_local_archives"] if "formal_segment" in x["reference_path"]),
            "gemini_current_integrity": str(workspace / "gemini_usability_review_20260914/integrity/CURRENT_INTEGRITY.json")}
    amd = ["# 原始 dump 与分析索引", "", "[主报告](README.zh.md) · [最终数据构成](DATA_LINEAGE.zh.md) · [机器索引](ARCHIVE_INDEX.json)", "",
           "本轮只生成六模型报告与实验沿革，没有重新打包或上传原始数据。公开链接固定到既有 commit；标注“本地”的路径不是 GitHub 下载地址。", "",
           "| 数据来源 | raw / member / shard 入口 |", "|---|---|"]
    for c in cohorts:
        e = entries.get(c["id"], {})
        link = e.get("model_index_url") or e.get("raw_entry_url")
        if link:
            text = f"[固定索引]({link})"
        elif c["id"] == "gpt_original":
            text = f"[本地 GPT 原始归档]({c['local_archive_root']}/manifest.json)；恢复器与逐原件映射见机器索引"
        else:
            text = f"[本地 Gemini 完整来源]({gemini_entry['full_source_index_path']})；含原始与恢复 job 的实际路径"
        amd.append(f"| `{c['id']}` | {text} |")
    amd.extend(["", "Gemini 当前完整 raw 仍在各 study 的 `invocations/<job>/api_dump/` 与 `result/`；已关闭归档仅覆盖原始中断段，不能把 recovery 快照说成完整封存。GPT 原始 raw 同样未公开；公开的 GPT 定向重跑包不等于全部原始 GPT raw 已公开。", "",
                "## 本报告附件", "", "- [全设置绝对值](absolute_settings.csv)、[全部比较](contrasts.csv)、[逐重复](by_repeat.csv)。", "- [详细设置与结果](DETAILS.zh.md)、[家族排名](family_rankings.csv)、[排名变化](rank_transitions.csv)。", "- [逐设置来源](DATA_LINEAGE.csv)、[采用/替换记录](SOURCE_SELECTION.csv)、[严格评分完整度](SCORE_COMPLETENESS.csv)。", "- [历史批次日志](EXPERIMENT_LOG.zh.md)、[逐批次机器日志](EXPERIMENT_LOG.csv)。", "- [资源口径与既有账本引用](resources.csv)：继承的设置均值、整池总量及不同来源账本不可直接相加；Gemini 尚无当前完整全尝试成本导出，未知不补零。", "",
                "`ARCHIVE_INDEX.json` 保留原归档身份、member/shard 映射和恢复入口；本次没有重读 tar 或做新远端核验。重复引用旧归档不代表新数据。", ""])
    out = {"DATA_LINEAGE.csv": csv_encoded(lineage), "DATA_LINEAGE.zh.md": "\n".join(md).encode(),
           "SOURCE_INDEX.json": encoded({"schema": "six-model-source-lineage.v1", "cohorts": cohorts,
                 "inherited_source_metadata": inputs[0], "replacement_policy": source["replacement_policy"],
                 "current_gemini_check": inputs[-1], "scope": "Only six selected models; historical Claude execution remains in EXPERIMENT_LOG, excluded from current performance."}),
           "ARCHIVE_INDEX.json": encoded(arch), "ARCHIVE_INDEX.md": "\n".join(amd).encode(),
           "LINEAGE_INPUTS.json": encoded({"inputs": inputs, "models": MODELS, "logical_rows": len(rows),
                 "rerun_cells": len(replacements), "rerun_pools": sum(rerun_counts.values()),
                 "planned": sum(totals.values()), "completed": sum(m["execution_complete"] for m in final_by_model.values()),
                 "strict_scored": sum(m["score_complete"] for m in final_by_model.values()),
                 "new_raw_reads_or_model_calls": False})}
    for p in inputs:
        assert hashlib.sha256(Path(p["path"]).read_bytes()).hexdigest() == p["sha256"]
    return out


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
