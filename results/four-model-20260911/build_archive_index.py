#!/usr/bin/env python3
"""Metadata-only federation of three immutable published archive indexes.

This study-specific adapter never opens a tar, raw member, manifest or linked
analysis payload. Six explicit local input files are bound to fixed URLs/SHA256.
Python standard library only; --check compares outputs without modifying them.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

REPO = "https://github.com/tiannuo-yang/LLM_ExpGym"
PINS = {
    "legacy": {
        "commit": "0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91",
        "data_commit": "6119f9d136c9ed1f06a7bedd7371be0deb9b5d59",
        "base": "results/portable-eval-20260908/full_matrix_report_v1",
        "json_sha256": "1372ef13e22ccf6d7cbfa9726abee5d03878ab3a6b12045d7f5fc286b374d136",
        "md_sha256": "fefd11aa95692549fdb684f93cb889239168144b8993338021a824b5b8099c59",
    },
    "qwen": {
        "commit": "ff8c572b6a00c33964a00a8fb991fd79dcf900e4",
        "data_commit": "03dd6ef0ed9a63cb673a7b4e62a5a19026015225",
        "base": "results/qwen38-20260910/report",
        "json_sha256": "9201a74f45fff5709f954ef369c00caa1f9977a4bd09af5f55ea6952f6aef7e4",
        "md_sha256": "10f91f477eb3be146ac1fbb95c9047f45784d2d212429fab2ec2dcf5e4d31e39",
    },
    "deepseek": {
        "commit": "8c79111de3398d12fb36ba349d8f4266f2330200",
        "data_commit": "41ec233f849aff05d8d91443118b6b2392d1cc40",
        "base": "results/deepseek-flash-0731-20260911/report",
        "json_sha256": "431496f24b7cb8f602adb4d5792dc4ef98ebbaeb79e73c1b6a099bf9723c154f",
        "md_sha256": "b5607cd125ee5382aa54303647fe63aef399ecc0ae4707affaf94de0ab2f44d7",
    },
}
MODELS = ("kimi-k3", "glm-5.3", "qwen3.8-2.4t-a95b-fp8", "deepseek-v4-flash-0731")
LABELS = ("Kimi-K3", "GLM-5.3", "Qwen3.8-2.4T-A95B-FP8", "DeepSeek-V4-Flash-0731")
COUNTS = ("legacy_bundles", "single_manifest_collections", "tar_shards",
          "original_files", "original_bytes", "compressed_bytes")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def fixed_url(url):
    require(isinstance(url, str) and re.fullmatch(
        re.escape(REPO) + r"/(?:blob|tree)/[0-9a-f]{40}/[^?#\s]+", url),
        "expected immutable repository URL")
    path = url.split("/", 7)[-1]
    require(not any(x in (".", "..") for x in path.split("/")) and "%" not in path,
            "unsafe URL path")
    return url


def link(commit, path):
    return fixed_url(f"{REPO}/blob/{commit}/{path}")


def input_link(key, suffix):
    pin = PINS[key]
    return link(pin["commit"], f"{pin['base']}/{suffix}")


def no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value


def read_bound(path, expected_sha):
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha), "invalid expected SHA256")
    payload = Path(path).read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    require(actual == expected_sha, "input SHA256 mismatch")
    return payload, {"bytes": len(payload), "sha256": actual,
                     "evidence_basis": "this_generator_read_and_sha256_checked"}


def validate_urls(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "url":
                fixed_url(child)
            else:
                validate_urls(child)
    elif isinstance(value, list):
        for child in value:
            validate_urls(child)


def nonnegative(value):
    require(type(value) is int and value >= 0, "count must be nonnegative integer")
    return value


def inherited(artifact):
    fixed_url(artifact["url"])
    require(re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]), "invalid inherited SHA256")
    return {"url": artifact["url"], "bytes": nonnegative(artifact["bytes"]),
            "sha256": artifact["sha256"],
            "evidence_basis": "inherited_from_bound_child_index_not_payload_read"}


def named(name, artifact, role):
    return {"name": name, "role": role, **inherited(artifact)}


def reports(key):
    return {"report": input_link(key, "README.zh.md"),
            "tables": input_link(key, "TABLES.md"),
            "archive_index_json": input_link(key, "ARCHIVE_INDEX.json"),
            "archive_index_md": input_link(key, "ARCHIVE_INDEX.md")}


def legacy_models(source):
    require(source["schema"] == "expgym-public-formal-archive-index-v1", "legacy schema mismatch")
    require(source["input_commit"] == PINS["legacy"]["data_commit"], "legacy commit mismatch")
    require(set(source["models"]) == set(MODELS[:2]), "legacy model set mismatch")
    require(source["scope"]["k3_old34_counted_once"] is True, "composite deduplication not declared")
    output, physical = [], set()
    for model in MODELS[:2]:
        old = source["models"][model]
        totals = old["totals"]
        sums = {"bundles": len(old["bundles"]), "tar_shards": 0,
                "original_files": 0, "original_bytes": 0, "compressed_bytes": 0}
        for bundle in old["bundles"]:
            inherited(bundle["index"])
            require(bundle["tar_shards"] == len(bundle["shards"]), "bundle shard count mismatch")
            shard_sums = {"original_files": 0, "original_bytes": 0, "compressed_bytes": 0}
            for shard in bundle["shards"]:
                archive = inherited(shard["archive"])
                inherited(shard["member_inventory"])
                require(archive["url"] not in physical, "duplicate physical tar")
                physical.add(archive["url"])
                shard_sums["compressed_bytes"] += archive["bytes"]
                for field in ("original_files", "original_bytes"):
                    shard_sums[field] += nonnegative(shard[field])
            for field, amount in shard_sums.items():
                require(amount == bundle[field], f"bundle {field} mismatch")
                sums[field] += amount
            sums["tar_shards"] += bundle["tar_shards"]
        require(sums == totals, "legacy model totals mismatch")
        exported = [named(x["name"], x["artifact"], x["role"]) for x in old["analysis_exports"]]
        required = {"metrics.csv", "effects.csv", "paired_rows.csv", "source_index.json", "EXPORT_INDEX.json"}
        require(required <= {x["name"] for x in exported}, "legacy analysis navigation incomplete")
        count = {"legacy_bundles": totals["bundles"], "single_manifest_collections": 0,
                 **{k: totals[k] for k in COUNTS[2:]}}
        tools = [named(x["artifact"]["repo_path"].rsplit("/", 1)[-1], x["artifact"],
                       "旧格式恢复/重定位工具")
                 for x in source["restore_and_relocation_tools"] if x["model"] in (model, "shared")]
        output.append({"model": model, "label": LABELS[len(output)], "format": "legacy-collection-bundle-shards",
                       "index_key": "legacy", "data_commit": source["input_commit"],
                       "navigation": reports("legacy"), "counts": count,
                       "raw_entry": inherited(old["collection_index"]),
                       "raw_mapping": f"ARCHIVE_INDEX.json models[{model!r}].bundles[].shards[]: archive + member_inventory；完整原件在所指 inventory 中",
                       "analysis_files": exported,
                       "delivery_and_replay": [inherited(x) for x in old["navigation"]],
                       "restore_tools": tools, "analysis_python": old["analysis_python"],
                       "scope": ("正式 collection 的 raw 与 controls；"
                                 + ("Kimi composite 旧 34 包仅计一次，失败尝试保留；" if model == "kimi-k3" else "")
                                 + "历史 smoke/DEV 不纳入该计数。"),
                       "review": {"kind": "published_historical_review",
                                  "url": next(x["artifact"]["url"] for x in source["shared_report_and_costs"] if x["name"] == "成稿后独立科学复核")}})
    require({key: sum(source["models"][m]["totals"][key] for m in MODELS[:2])
             for key in source["totals"]} == source["totals"], "legacy study totals mismatch")
    return output


def current_model(source, key, model, label):
    schema = {"qwen": "qwen38.archive-index.v1", "deepseek": "deepseek-flash.archive-index.v1"}[key]
    require(source["schema"] == schema and source["model"] == model, "single-manifest identity mismatch")
    require(source["data"]["commit"] == PINS[key]["data_commit"], "data commit mismatch")
    require(source["manifest"]["schema"] == "expgym.delivery.v1", "manifest schema mismatch")
    t = source["totals"]
    require(t["global_manifests"] == 1 and len(source["archives"]) == t["shards"], "manifest/shard count mismatch")
    seen = set()
    for a in source["archives"]:
        inherited(a)
        require(a["path"] not in seen, "duplicate physical tar")
        seen.add(a["path"])
    for field, archive_field in (("members", "members"), ("member_original_bytes", "original_bytes"),
                                 ("shard_compressed_bytes", "bytes")):
        require(sum(nonnegative(x[archive_field]) for x in source["archives"]) == t[field], "shard totals mismatch")
    for field, role_field in (("members", "members"), ("member_original_bytes", "original_bytes")):
        require(sum(nonnegative(x[role_field]) for x in source["member_roles"]) == t[field], "role totals mismatch")
    require(len(source["outer_attachments"]) == t["outer_attachments"], "attachment count mismatch")
    require(sum(nonnegative(x["bytes"]) for x in source["outer_attachments"]) == t["outer_attachment_bytes"], "attachment byte mismatch")
    require(sum("member_path" in x for x in source["outer_attachments"]) == t["outer_member_copies"], "attachment copy mismatch")
    restore = source["restore"]
    require(restore["analyzer_arbitrary_root_relocation_supported"] is False and
            restore["original_analysis_replay_requires_frozen_absolute_layout"] is True,
            "unexpected replay capability")
    fixed_url(restore["package_run"])
    fixed_url(restore["delivery"])
    analysis_prefix = "analysis/full_v1/" if key == "qwen" else "analysis/full_v2/"
    analysis = [named(x["path"], x, x["description"]) for x in source["outer_attachments"]
                if x["path"].startswith(analysis_prefix)]
    require(len(analysis) == 11, "expected eleven current analysis outputs")
    provenance = [named(x["path"], x, x["description"]) for x in source["outer_attachments"]
                  if x["path"] in ("study/accounting.json", "study/formal_analysis_states.json")
                  or x["path"].startswith("study/RUN_INPUTS")
                  or x["path"].endswith("/coverage.json")
                  or x["path"].endswith("/matrix.json")]
    review = ({"kind": "published_historical_review", "url": input_link(key, "review/REVIEW.md")}
              if key == "deepseek" else
              {"kind": "report_process_description_only_not_review_artifact",
               "url": input_link(key, "README.zh.md"),
               "limit": "固定报告提交未提供独立 review 原件链接；不据报告流程说明宣称已提供复核原件。"})
    return {"model": model, "label": label, "format": "expgym.delivery.v1-single-manifest",
            "index_key": key, "data_commit": source["data"]["commit"],
            "navigation": {**reports(key), "repeats": input_link(key, "REPEATS.md")},
            "counts": {"legacy_bundles": 0, "single_manifest_collections": 1,
                       "tar_shards": t["shards"], "original_files": t["members"],
                       "original_bytes": t["member_original_bytes"], "compressed_bytes": t["shard_compressed_bytes"]},
            "raw_entry": inherited(source["manifest"]),
            "raw_mapping": "manifest files[].{path,archive,bytes,sha256}；子索引 archives[] 提供每个分片固定链接与 SHA",
            "analysis_files": analysis, "study_and_cost_context": provenance,
            "attachment_inventory": inherited(source["attachment_inventory"]),
            "attachment_counts": {k: t[k] for k in ("outer_attachments", "outer_attachment_bytes", "outer_member_copies", "outer_member_copy_bytes")},
            "member_roles": source["member_roles"], "restore": restore, "review": review,
            "scope": "全封存选件：正式 dump/trace/queue，加明确选入的 smoke、服务诊断、analysis、study/runtime 原件；不等同纯正式请求集合。"}


def validate_model_set(models):
    names = [x["model"] for x in models]
    require(len(names) == len(set(names)), "duplicate model")
    require(tuple(names) == MODELS, "expected exact four-model order/set")
    for model in models:
        require(set(model["counts"]) == set(COUNTS), "count fields mismatch")
        for value in model["counts"].values():
            nonnegative(value)


def build(sources, input_evidence):
    for source in sources.values():
        validate_urls(source)
    models = legacy_models(sources["legacy"])
    models.extend(current_model(sources[key], key, MODELS[i], LABELS[i])
                  for key, i in (("qwen", 2), ("deepseek", 3)))
    validate_model_set(models)
    totals = {key: sum(m["counts"][key] for m in models) for key in COUNTS}
    return {"schema": "four-model.archive-navigation.v1", "study": "four-model-20260911",
            "models": models, "tar_payload_totals": totals,
            "inputs_read_this_generation": input_evidence,
            "legacy_shared_analysis_and_costs": [named(x["name"], x["artifact"], "历史双模型分析/成本/复核")
                                                  for x in sources["legacy"]["shared_report_and_costs"]],
            "scope": {"counts_are_archive_members_not_experiment_samples": True,
                      "not_cross_model_content_deduplicated": True,
                      "k3_composite_original34_counted_once": True,
                      "tar_payload_totals_exclude_outer_attachments_and_current_report": True,
                      "new_models_include_selected_smoke_serving_analysis_controls": True,
                      "legacy_bundles_and_single_manifest_collections_are_distinct": True,
                      "member_inventory_expanded_here": False,
                      "excluded_entities": ["model weights", "virtual environments", "complete upstream datasets", "private credentials"],
                      "legacy_public_control_limit": sources["legacy"]["scope"]["limits"][0]},
            "evidence": {"input_files_read_and_sha256_checked": len(input_evidence),
                         "child_manifest_member_shard_hashes": "inherited_only",
                         "arithmetic_checks": "child metadata sums and duplicate physical tar paths",
                         "payload_or_tar_files_read": 0, "files_restored": 0,
                         "model_calls": 0, "remote_content_verified_by_generator": False,
                         "new_secret_scan_by_generator": False,
                         "scientific_or_execution_status_evaluated_by_generator": False}}


def md_link(label, url):
    return f"[{label}]({url})"


def render(index):
    lines = ["# 四模型完整存档导航", "",
             "本页集合 Kimi-K3、GLM-5.3、Qwen3.8 与 DeepSeek-V4-Flash-0731 的冻结原档、完整分析、原比较、成本与恢复入口；不新增实验，不重新封存，也不把规范化记录当作原始 dump。",
             "", "机器可读导航见 [ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)，四模型主报告见 [README.zh.md](README.zh.md)。完整逐原件与逐分片身份沿固定子索引/manifest 获取，不在此复制数万行。",
             "", "## 1. 模型级入口", "", "| 模型 | 原完整报告 | 人读 / 机器索引 | raw collection / manifest |", "| --- | --- | --- | --- |"]
    for m in index["models"]:
        n = m["navigation"]
        lines.append(f"| {m['label']} | {md_link('报告', n['report'])} | {md_link('索引', n['archive_index_md'])} / {md_link('JSON', n['archive_index_json'])} | {md_link('原档入口', m['raw_entry']['url'])} |")
    lines += ["", "## 2. 封存载荷计数与边界", "",
              "| 模型 | 旧 bundle | 新 single-manifest collection | tar | 原件 | 原字节 | 压缩字节 |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for m in index["models"]:
        lines.append("| " + m["label"] + " | " + " | ".join(f"{m['counts'][k]:,}" for k in COUNTS) + " |")
    lines.append("| 合计（分格式） | " + " | ".join(f"{index['tar_payload_totals'][k]:,}" for k in COUNTS) + " |")
    lines += ["", "73 个旧 bundle 与 2 个新 single-manifest collection 是不同容器层级，不能合称 75 bundles。Kimi 36 包＝旧 34 包＋固定 8 项恢复 raw 1 包＋新 controls 1 包，旧包只计一次；有效合并不抹去旧失败尝试。",
              "", "这些是各模型既有发布范围内的 tar 载荷相加：不跨模型内容去重；旧两模型为正式 collection（含 controls），新两模型还包括明确选入的 smoke、服务诊断、分析与运行身份原件。因此合计不是纯正式 dump 数、请求数或实验样本数。",
              "", "原字节不含旧 tar 内嵌 member inventory 的额外开销，也不含外层附件及本次四模型报告；压缩字节只是 tar.gz 载荷，不是 Git clone 大小。完整存档还须保留子索引列出的外层 CSV/JSON/报告/代码/恢复说明，以及各固定报告提交和本次报告。外层与 tar 中同路径副本不再加入本表。",
              "", "## 3. 每模型原件与完整分析导航"]
    for m in index["models"]:
        lines += ["", f"### {m['label']}", "", m["scope"], "",
                  f"数据提交：`{m['data_commit']}`。原件映射：{m['raw_mapping']}。", "",
                  f"原档入口 SHA-256（继承子索引声明）：`{m['raw_entry']['sha256']}`；{m['raw_entry']['bytes']:,} B。",
                  "", "| 完整分析文件 | 用途 |", "| --- | --- |"]
        for a in m["analysis_files"]:
            lines.append(f"| {md_link(a['name'], a['url'])} | {a['role']} |")
        if "study_and_cost_context" in m:
            lines += ["", "运行矩阵、身份与 Slurm 成本上下文：", ""]
            for a in m["study_and_cost_context"]:
                lines.append(f"- {md_link(a['name'], a['url'])}")
            t = m["attachment_counts"]
            lines += ["", f"全部外层附件由 {md_link('附件清单', m['attachment_inventory']['url'])} 和子索引列举：{t['outer_attachments']} 件 / {t['outer_attachment_bytes']:,} B；其中 {t['outer_member_copies']} 件 / {t['outer_member_copy_bytes']:,} B 有 tar member 身份副本，其余须另存。当前报告/复核等后续附件不自动算入历史清单。"]
        else:
            lines += ["", "交付和最终恢复验收：", ""]
            for a in m["delivery_and_replay"]:
                lines.append(f"- {md_link(a['url'].rsplit('/', 1)[-1], a['url'])}")
        review = m["review"]
        lines += ["", (f"历史独立复核：{md_link('已发布复核', review['url'])}。" if review["kind"] == "published_historical_review" else
                         f"复核导航边界：{review['limit']} {md_link('固定报告说明', review['url'])}。")]
    lines += ["", "### 旧两模型共享成本与原报告比较", ""]
    for a in index["legacy_shared_analysis_and_costs"]:
        lines.append(f"- {md_link(a['name'], a['url'])}")
    lines += ["", "旧 `effects.csv` / `results.json` 保留原比较定义；新 `contrasts.csv`、`absolute_settings.csv`、`by_outerseed.csv` 保留新分析定义。`raw_terminals.csv` 是终态/评分投影，不是 HTTP dump。Kimi 成本保留旧失败及恢复；reasoning 已包含于 output，不能再加一次；未知值不补 0。",
              "", "## 4. 恢复与重放：按归档格式选择", "", "### Kimi / GLM 旧格式", "",
              "从 source_index 查来源相对路径，再沿 collection → bundle INDEX → member inventory → tar 找原件。旧恢复器还原为 `<恢复根>/<bundle_id>/payload/<workspace-relative-path>`，原 tar member 为 `data/<path>`。需要原 AN2 分析时使用匹配 relocator 和已记录 Python；不要直接执行 source_index 中原机器绝对路径。旧恢复/重放最终状态看各模型 REPLAY_VERIFIED，而非较早说明里的 pending。"]
    for m in index["models"][:2]:
        lines += ["", f"{m['label']} 分析解释器：{m['analysis_python']}；匹配工具：", ""]
        for a in m["restore_tools"]:
            lines.append(f"- {md_link(a['name'], a['url'])}")
    lines += ["", "旧格式不能交给新的 package_run.py 直接恢复。公共 controls 已排除有记录的非实验回执，私有审计引用链并非全部自包含；详见旧子索引。模型权重、环境实体、完整上游数据与私密凭据不在原档内。",
              "", "### Qwen / DeepSeek 单 manifest 格式", ""]
    for m in index["models"][2:]:
        lines.append(f"- {m['label']}：{md_link('package_run.py', m['restore']['package_run'])} / {md_link('delivery.py', m['restore']['delivery'])}，版本 `{m['restore']['source_commit']}`。")
    lines += ["", "先核对固定数据提交与 manifest 身份，再用对应源码运行：", "", "```bash",
              "python -B /absolute/frozen-source/scripts/package_run.py verify \\",
              "  --manifest /downloaded/release/sealed/manifest.json \\",
              "  --archive-dir /downloaded/release/sealed --require-public-scan", "```", "",
              "默认校验全部 shard 与 member，恢复 0 件。需部分原件时加 `--select <非空 JSON 路径数组>` 与 `--restore-dir <事先不存在的新目录>`；仍校验全部未提取成员。只有 CLI exit 0 表示该次完整性验证结束，目录存在不是成功，完整性也不是重新评分或科学真实性证明。`--require-public-scan` 只检查可信 manifest 中的历史扫描声明，不重新读取密钥扫描。",
              "", "两份新模型 analyzer 都没有任意 root 的 `--relocate` / `--path-map` 能力。新根可浏览/验证 raw 和 CSV，但原样 raw→analysis 重放要求冻结的绝对 state/artifact/authorization 布局、controller.lock 与 session 等所有真实依赖、冻结脚本/Python 身份，以及新的输出目录。更改路径会改变输入身份；不能用 symlink 绕过，也不能承诺只恢复几份 CSV 就可原身份重放。",
              "", "## 5. 本次实读证据与继承身份", "",
              "本生成器实读并核对下列 6 份输入（JSON 用于元数据聚合，Markdown 固定恢复说明来源）。所有被链接的 collection、manifest、member、tar、分析及工具 SHA/大小均继承这些已发布索引；本步骤未打开它们。计数自检只核对既有元数据求和和物理 tar 路径唯一性，不是新内容验证、恢复、模型执行或科学复核。",
              "", "| 本次实读输入 | 字节 | SHA-256 |", "| --- | ---: | --- |"]
    for a in index["inputs_read_this_generation"]:
        lines.append(f"| {md_link(a['id'], a['url'])} | {a['bytes']:,} | `{a['sha256']}` |")
    lines += ["", "生成器为 [build_archive_index.py](build_archive_index.py)，窄契约测试为 [test_archive_index.py](test_archive_index.py)。完整性通过固定子索引导航提供，未把数万 member 复制进本索引。这里的元数据自检不替代四模型正文成稿后的一次独立数字/逻辑复核，也不替代新发布文件的安全扫描。",
              "", "复建只需将上述六份固定输入下载为文件；输入路径可变化，但内容 SHA 和固定来源不能变化：", "", "```bash",
              "python -B build_archive_index.py \\",
              "  --legacy-index /inputs/legacy/ARCHIVE_INDEX.json --legacy-guide /inputs/legacy/ARCHIVE_INDEX.md \\",
              "  --qwen-index /inputs/qwen/ARCHIVE_INDEX.json --qwen-guide /inputs/qwen/ARCHIVE_INDEX.md \\",
              "  --deepseek-index /inputs/deepseek/ARCHIVE_INDEX.json --deepseek-guide /inputs/deepseek/ARCHIVE_INDEX.md \\",
              "  --output-dir /path/to/four-model-report --check", "```", "",
              "`--check` 仅读取既有两份输出并逐字节比较，不写文件；省略时生成这两份索引，不更改实验数据或其他报告。脚本不联网、不扫描/解压 tar、不调用模型。", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in PINS:
        parser.add_argument(f"--{key}-index", required=True, type=Path)
        parser.add_argument(f"--{key}-guide", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    sources, evidence = {}, []
    for key, pin in PINS.items():
        for arg, suffix in (("index", "json"), ("guide", "md")):
            payload, item = read_bound(getattr(args, f"{key}_{arg}"), pin[f"{suffix}_sha256"])
            item.update({"id": f"{key}/ARCHIVE_INDEX.{suffix}",
                         "url": input_link(key, f"ARCHIVE_INDEX.{suffix}")})
            evidence.append(item)
            if suffix == "json":
                sources[key] = json.loads(payload, object_pairs_hook=no_duplicates)
            else:
                payload.decode("utf-8")
    result = build(sources, evidence)
    outputs = {"ARCHIVE_INDEX.json": json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
               "ARCHIVE_INDEX.md": render(result)}
    if not args.check:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        destination = args.output_dir / name
        if args.check:
            require(destination.read_bytes() == value.encode(), f"output differs: {name}")
        else:
            destination.write_bytes(value.encode())
    print(json.dumps({"check": args.check, "outputs": list(outputs),
                      "inputs_read": len(evidence), "totals": result["tar_payload_totals"]}, sort_keys=True))


if __name__ == "__main__":
    main()
