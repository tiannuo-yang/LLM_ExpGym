#!/usr/bin/env python3
"""Index frozen public metadata only; never read tar/raw/model/key contents."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from urllib.parse import quote

COMMIT = "6119f9d136c9ed1f06a7bedd7371be0deb9b5d59"
BASE = "results/portable-eval-20260908/full_delivery_v5/"
K3 = BASE + "kimi-k3-fixed8-composite-20260910/"
OLD_K3 = BASE + "kimi-k3-original-node-failure-20260909/"
GLM = BASE + "glm-5.3-original-completed-20260909/"
EXPORTS = {
    "kimi-k3": K3 + "analysis/actual_k3_fixed8_composite_export_v2_py311_final/",
    "glm-5.3": GLM + "analysis/actual_formal_export_glm_completed_v2/",
}
COLLECTIONS = {
    "kimi-k3": BASE + "INDEX.kimi-k3-composite-v1.json",
    "glm-5.3": GLM + "payload/collection/INDEX.json",
}
COLLECTION_SHA256 = {
    "kimi-k3": "a462bde564618f52b46b863095bfed5d2a97eb9c3ce4c730a34ac6fdad91a0f7",
    "glm-5.3": "9d4433461c3cf0a3017220003c2d70b5085e715c5db82303449d57e48c8cca09",
}
EXPECTED = {
    "kimi-k3": (36, 268, 66643, 1751137861, 305870108),
    "glm-5.3": (37, 288, 71634, 3467116893, 772603212),
}
ROLE = {
    "EXPORT_INDEX.json": "完整导出清单；哈希/大小权威来源",
    "OUTPUT_INDEX.json": "原分析十输出清单；字节重现基线",
    "SUMMARY.zh.md": "原分析摘要（不是全矩阵宽表）",
    "metrics.csv": "逐 item / strategy / regime / outerseed 的绝对指标长表",
    "effects.csv": "514 条基线/目标/效应比较，包括 cached 和 PoolAct",
    "paired_rows.csv": "比较的逐题配对明细",
    "results.json": "全部聚合比较及分析结果；机器可读",
    "records.json": "规范化正式结果记录；不等于 HTTP raw dump",
    "manifest.json": "实际实验矩阵、计划单元及输入选择",
    "source_index.json": "原件来源路径、大小和哈希；原路径重放前需重定位",
    "input_pins.json": "固定分析输入身份绑定",
    "oracle.json": "冻结HPO/NAS参考性能与成本",
    "provenance.json": "分析 provenance / 输入来源",
    "raw_terminals.csv": "agent终态、答案与评分投影；不是HTTP用量清单",
    "logical_outcomes.csv": "逻辑单元终态及缺失分类",
    "known_subsets.csv": "可观测子集汇总；不得冒充完整未知成本",
    "ALL_ATTEMPT_COST_LEDGER.json": "K3 旧运行及固定8项恢复的全部尝试成本账本",
    "COMPOSITE_PROVENANCE.json": "K3 697+8 有效合并与旧失败来源映射",
    "EXPORT_EVIDENCE.json": "GLM 正式导出 provenance / HTTP 全部尝试证据",
}


class Metadata:
    def __init__(self, repo):
        self.repo, self.cache, self.references = Path(repo), {}, set()
        self.tree = {}
        for line in self.git("ls-tree", "-rlz", COMMIT).split(b"\0"):
            if line:
                header, name = line.split(b"\t", 1)
                mode, kind, oid, size = header.decode().split()
                assert kind == "blob"
                self.tree[name.decode()] = {"mode": mode, "git_blob": oid, "bytes": int(size)}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo)

    def blob(self, path):
        assert path in self.tree and self.tree[path]["mode"] in ("100644", "100755"), path
        assert not path.endswith((".tar.gz", ".tgz")), "Archive reads forbidden"
        assert self.tree[path]["bytes"] <= 2 * 1024 * 1024, "Only small metadata may be read"
        if path not in self.cache:
            self.cache[path] = self.git("show", COMMIT + ":" + path)
        assert len(self.cache[path]) == self.tree[path]["bytes"]
        return self.cache[path]

    def value(self, path):
        return json.loads(self.blob(path))

    def ref(self, path, pin=None, source=None):
        assert path in self.tree, path
        self.references.add(path)
        meta = self.tree[path]
        if pin is None:
            digest = hashlib.sha256(self.blob(path)).hexdigest()
            basis = "small metadata Git blob SHA256 computed by this index builder"
        else:
            assert meta["bytes"] == pin["bytes"], path
            digest = pin["sha256"]
            assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
            basis = "SHA256 copied from existing frozen metadata; Git blob size/path checked only"
        return {"repo_path": path, "bytes": meta["bytes"], "sha256": digest,
                "git_blob": meta["git_blob"], "url": url(path), "sha256_basis": basis,
                **({"metadata_source": source} if source else {})}


def url(path):
    return "https://github.com/tiannuo-yang/LLM_ExpGym/blob/" + COMMIT + "/" + quote(path, safe="/")


def join(parent, child):
    p = PurePosixPath(child)
    assert not p.is_absolute() and all(x not in ("", ".", "..") for x in child.split("/"))
    return str(PurePosixPath(parent) / p)


def build(meta):
    models, archive_paths = {}, set()
    archived_code = []
    for model, collection_path in COLLECTIONS.items():
        collection_ref = meta.ref(collection_path)
        assert collection_ref["sha256"] == COLLECTION_SHA256[model]
        collection = meta.value(collection_path)
        bundles, seen_originals = [], set()
        for row in collection["bundles"]:
            index_path = join(PurePosixPath(collection_path).parent, row["index"])
            index_raw = meta.blob(index_path)
            assert hashlib.sha256(index_raw).hexdigest() == row["sha256"]
            index = json.loads(index_raw)
            assert (index["file_count"], index["original_bytes"]) == (row["file_count"], row["original_bytes"])
            index_ref = meta.ref(index_path, {"bytes": len(index_raw), "sha256": row["sha256"]}, collection_path)
            shards, member_bytes, member_count = [], 0, 0
            for shard in index["shards"]:
                archive_path = join(PurePosixPath(index_path).parent, shard["archive"])
                member_path = join(PurePosixPath(index_path).parent, shard["index"])
                assert archive_path not in archive_paths, "Duplicate physical archive"
                archive_paths.add(archive_path)
                archive_ref = meta.ref(archive_path, shard, index_path)
                member_pin = {"bytes": shard["index_bytes"], "sha256": shard["index_sha256"]}
                member_ref = meta.ref(member_path, member_pin, index_path)
                member_raw = meta.blob(member_path)
                assert hashlib.sha256(member_raw).hexdigest() == member_pin["sha256"]
                members = json.loads(member_raw)["files"]
                assert len(members) == shard["file_count"]
                original_bytes = sum(x["bytes"] for x in members)
                assert original_bytes + len(member_raw) == shard["expanded_bytes"]
                for original in members:
                    path = original["path"]
                    assert path not in seen_originals, "Duplicate original within a model collection"
                    seen_originals.add(path)
                    if path.endswith(("/analysis_candidate_v2/analysis.py", "/analysis_relocation_candidate_v2/relocate.py")):
                        archived_code.append({"model": model, "bundle_id": row["bundle_id"],
                                              "workspace_relative_path": path, "bytes": original["bytes"],
                                              "sha256": original["sha256"], "archive_repo_path": archive_path,
                                              "member_index_repo_path": member_path,
                                              "restored_relative_path": row["bundle_id"] + "/payload/" + path,
                                              "sha256_basis": "existing member inventory, not original payload read"})
                member_count += len(members)
                member_bytes += original_bytes
                shards.append({"archive": archive_ref, "member_inventory": member_ref,
                               "original_files": len(members), "original_bytes": original_bytes,
                               "expanded_bytes_including_embedded_inventory": shard["expanded_bytes"]})
            assert (member_count, member_bytes) == (row["file_count"], row["original_bytes"])
            # The file named controls in K3's old collection has the original
            # category label too; distinguish payload/control purpose explicitly.
            purpose = "controls" if "controls" in row["bundle_id"] else "raw"
            segment = "fixed8-recovery" if row["bundle_id"].startswith("recovery-") else "original-formal"
            source_scan = index.get("source_scan")
            bundles.append({"bundle_id": row["bundle_id"], "category": row["category"],
                            "purpose": purpose, "segment": segment, "index": index_ref,
                            "original_files": member_count, "original_bytes": member_bytes,
                            "tar_shards": len(shards), "compressed_bytes": sum(x["archive"]["bytes"] for x in shards),
                            "shards": shards,
                            "original_pack_known_secret_sources": index["known_secret_sources_checked"],
                            "source_scan": meta.ref(join(PurePosixPath(index_path).parent, source_scan["path"]),
                                                    source_scan, index_path) if source_scan else None})
        for path in seen_originals:
            assert not any(str(parent) in seen_originals for parent in PurePosixPath(path).parents
                           if str(parent) != "."), "File/directory prefix conflict"
        totals = (len(bundles), sum(x["tar_shards"] for x in bundles), len(seen_originals),
                  sum(x["original_bytes"] for x in bundles), sum(x["compressed_bytes"] for x in bundles))
        assert totals == EXPECTED[model], (model, totals)
        assert totals[0] == collection["bundle_count"] and totals[2] == collection["file_count"]
        assert totals[3] == collection["original_bytes"]
        export_path = EXPORTS[model] + "EXPORT_INDEX.json"
        export_index = meta.value(export_path)
        analysis = [{"name": "EXPORT_INDEX.json", "role": ROLE["EXPORT_INDEX.json"],
                     "artifact": meta.ref(export_path)}]
        for name, pin in export_index["files"].items():
            analysis.append({"name": name, "role": ROLE[name],
                             "artifact": meta.ref(EXPORTS[model] + name, pin, export_path)})
        leaf = K3 if model == "kimi-k3" else GLM
        replay = "replay_verified_v1/" if model == "kimi-k3" else "replay_verified_v2/"
        models[model] = {"collection_index": collection_ref,
                         "totals": dict(zip(("bundles", "tar_shards", "original_files", "original_bytes", "compressed_bytes"), totals)),
                         "bundles": bundles, "analysis_exports": analysis,
                         "navigation": [meta.ref(leaf + "FULL_DELIVERY.zh.md"),
                                        meta.ref(leaf + ("README.zh.md" if model == "kimi-k3" else "RESULTS.zh.md")),
                                        meta.ref(leaf + replay + "REPLAY_VERIFIED.zh.md"),
                                        meta.ref(leaf + replay + "FILE_MANIFEST.json")],
                         "analysis_python": "CPython 3.11.15" if model == "kimi-k3" else "CPython 3.10.12"}
    report_dir = K3 + "analysis/dual_model_analysis_fixed8_v2/"
    report_index = meta.value(report_dir + "INDEX.json")
    report_names = ["REPORT.zh.md", "PRIMARY_RESULTS.csv", "NEGATIVE_PERFORMANCE.csv", "COSTS.json", "INPUT_REFS.json"]
    shared = [{"name": name, "artifact": meta.ref(report_dir + name, report_index["files"][name], report_dir + "INDEX.json")}
              for name in report_names]
    shared.append({"name": "report INDEX.json", "artifact": meta.ref(report_dir + "INDEX.json")})
    review_dir = K3 + "analysis/dual_model_post_report_review_fixed8_v2/"
    # No receipt chain is recursively copied into this reader-facing inventory.
    shared.append({"name": "成稿后独立科学复核", "artifact": meta.ref(review_dir + "REVIEW.zh.md")})
    shared.append({"name": "最终科学验收（限定范围）", "artifact": meta.ref(K3 + "analysis/k3_recovery_root_v1/FINAL_SCIENTIFIC_ACCEPTANCE.json")})
    tools = []
    for model, leaf in (("kimi-k3", OLD_K3), ("glm-5.3", GLM)):
        prefix = leaf + "payload/tools/publication/"
        for relative in ("collection_restore_candidate_v2/restore_collection.py", "shard_delivery_candidate_v2/restore.py",
                         "shard_delivery_candidate_v2/common.py", "shard_delivery_candidate_v2/pack.py", "validate_bundle_v2.py"):
            tools.append({"model": model, "artifact": meta.ref(prefix + relative)})
    relocation = GLM + "evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/relocate.py"
    tools.append({"model": "shared", "artifact": meta.ref(relocation)})
    result = {"schema": "expgym-public-formal-archive-index-v1", "input_commit": COMMIT,
              "results_branch": "results/portable-eval-20260908", "models": models,
              "shared_report_and_costs": shared, "restore_and_relocation_tools": tools,
              "analysis_code_inside_archives": archived_code,
              "scope": {"formal_collections_only": True, "k3_old34_counted_once": True,
                        "k3_composite": "original 697 effective + fixed8 recovery; old failed attempts retained",
                        "no_cross_model_deduplication_of_shared_controls": True,
                        "excluded": ["historical smoke/DEV/invalidated runs from formal totals", "private credentials", "model weights", "virtual environments", "complete upstream datasets"],
                        "limits": ["Public controls omit documented nonexperimental receipts; private audit reference chains are not fully self-contained.",
                                   "Frozen pending fields describe earlier observation times; final replay addenda provide completed status.",
                                   "New index reads Git tree plus small metadata only; tar SHA256 values are inherited, not newly verified."]},
              "self_check": {"all_referenced_paths_exist_in_frozen_git_tree": True,
                             "all_declared_sizes_match_frozen_git_blobs": True,
                             "all_collection_and_member_index_sha256_checked": True,
                             "all_bundle_member_counts_and_original_bytes_match": True,
                             "no_duplicate_physical_tar_paths": True,
                             "unique_tar_files": len(archive_paths),
                             "tar_contents_read": False, "raw_contents_read": False,
                             "models_called": False}}
    result["totals"] = {key: sum(m["totals"][key] for m in models.values()) for key in next(iter(models.values()))["totals"]}
    assert result["totals"]["bundles"] == 73 and len(archive_paths) == 556
    result["self_check"]["referenced_git_files"] = len(meta.references)
    result["self_check"]["small_metadata_files_read"] = len(meta.cache)
    return result


def markdown(index):
    lines = ["# 上一次正式运行：完整存档与结果索引", "",
             "这是原始数据、逐题指标、全部聚合比较与恢复入口的统一导航；不是只列六个主比较。", "",
             f"所有原数据链接固定到 `{COMMIT}`；本页新增索引不改写该提交中的实验结果。机器可读的逐包/逐 tar 分片完整路径、大小、SHA-256 见 [ARCHIVE_INDEX.json](ARCHIVE_INDEX.json)。", "",
             "## 一次取回完整原档", "", "```bash",
             "git clone --single-branch --branch results/portable-eval-20260908 https://github.com/tiannuo-yang/LLM_ExpGym.git LLM_ExpGym-results",
             "cd LLM_ExpGym-results", f"git checkout --detach {COMMIT}", "```", "",
             "完整存档＝该固定提交的仓库文件（tar、外层CSV/JSON/报告/工具与重放说明）＋本次新增索引/完整报告。**仅下载556个tar不等于存齐全部外层报告与附件。** 上面checkout会回到旧数据提交；本新报告属于后续提交，需另保留当前报告目录，或保留最新完整clone并用旧提交校验原数据。已有clone可fetch，不必重复clone。数据读取不需要模型、GPU或API密钥；权重、虚拟环境及完整上游数据不在此归档中。", "",
             "## 范围与去重", "", "| 模型 | bundle 包数 | tar 分片 | 原文件 | 原字节 | 压缩字节 |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for model, info in index["models"].items():
        t = info["totals"]
        lines.append("| " + model + " | " + " | ".join(f"{t[k]:,}" for k in ("bundles", "tar_shards", "original_files", "original_bytes", "compressed_bytes")) + " |")
    t = index["totals"]
    lines.append("| 合计 | " + " | ".join(f"{t[k]:,}" for k in ("bundles", "tar_shards", "original_files", "original_bytes", "compressed_bytes")) + " |")
    lines += ["", "K3 的36包＝旧34包＋固定8项恢复 raw 1包＋新 controls 1包；**不再把旧34包作为第三份 collection 重复计数**。GLM为36个正式 raw 包＋1个 controls 包。不同模型自带的共享 controls 原件按各自归档计数，不跨模型物理去重；文件数不是模型调用数或独立实验样本数。历史 smoke/DEV 不混入正式分母。", "",
              "## 先看哪份表", "", "| 想查什么 | 文件 |", "| --- | --- |",
              "| 每个题目/任务、预算、策略、重复的绝对得分 | `metrics.csv`（含 Free/Moderate/Tight；PoolAct实际只跑Moderate/Tight） |",
              "| 聚合基线、目标策略与差值 | `effects.csv` / `results.json`；每模型514比较，包含资源与缺失项，不是514个独立性能实验 |",
              "| 每条比较的逐题配对 | `paired_rows.csv` |",
              "| 具体跑了什么、结果和来源 | `manifest.json`、`records.json`、`source_index.json` |",
              "| agent终态、答案与评分投影 / 逻辑单元缺失分类 | `raw_terminals.csv` / `logical_outcomes.csv`；不是HTTP请求或usage清单 |",
              "| 完整请求/回复、HTTP失败、token与所有尝试 | 原始dump、K3 `ALL_ATTEMPT_COST_LEDGER.json`、GLM `EXPORT_EVIDENCE.json` |",
              "| 全 raw 原始请求/回复/trace | 下方完整 collection → bundle INDEX → member inventory → tar；不是用规范化 records 替代原始 dump |", "",
              "`effects.csv` 中 PoolAct 的 baseline=naive，target=该行 cached/poolact；ExpGym 比较为Free/Tight，不能因比较表的regime空白就认为Moderate没跑。`metrics.csv` 才是所有实际档位/策略绝对分数长表。Free下的PoolAct和未注册任务/档位组合未跑，不能补成0。", ""]
    for model, info in index["models"].items():
        lines += [f"### {model}：完整分析文件", "", f"字节重放解释器：**{info['analysis_python']}**。", "", "| 文件 | 用途 | 字节 |", "| --- | --- | ---: |"]
        for item in info["analysis_exports"]:
            a = item["artifact"]
            lines.append(f"| [{item['name']}]({a['url']}) | {item['role']} | {a['bytes']:,} |")
        lines.append("")
    lines += ["## 综合报告、成本与反例", ""]
    for item in index["shared_report_and_costs"]:
        lines.append(f"- [{item['name']}]({item['artifact']['url']})")
    lines += ["", "K3成本须同时保留旧失败运行与固定8项恢复；有效697+8结果不能覆盖旧失败尝试。未知usage保留unknown/null，不按0计；reasoning已包含于completion，不能重复相加。所有负向比较照存。", "", "## 原始数据与恢复导航", ""]
    for model, info in index["models"].items():
        collection = info["collection_index"]
        lines += [f"### {model}", "", f"[完整 collection INDEX]({collection['url']})，{collection['bytes']:,} B，SHA-256：`{collection['sha256']}`。", ""]
        for ref in info["navigation"]:
            lines.append(f"- [{PurePosixPath(ref['repo_path']).name}]({ref['url']})")
        lines += ["", "| bundle（点开原清单） | 原件类别/来源段 | 原文件 | 原字节 | tar分片 | 压缩字节 |", "| --- | --- | ---: | ---: | ---: | ---: |"]
        for bundle in info["bundles"]:
            lines.append(f"| [{bundle['bundle_id']}]({bundle['index']['url']}) | {bundle['purpose']} / {bundle['segment']} | {bundle['original_files']:,} | {bundle['original_bytes']:,} | {bundle['tar_shards']} | {bundle['compressed_bytes']:,} |")
        lines.append("")
    lines += ["## 怎么找到某个原件并重现", "",
              "1. 在该模型 `source_index.json` 查原来源路径；去掉原 workspace 根后得到 workspace-relative 路径。",
              "2. 从 collection 找 bundle INDEX，再查其 `indexes/part-*.json`（本索引JSON逐片列出链接）。member行的 `path`、`bytes`、`sha256` 就是完整原件身份，对应同片tar里的 `data/<path>`。",
              "3. 用已发布恢复器保留相对布局恢复：输出为 `<新恢复根>/<bundle_id>/payload/<workspace-relative-path>`。原 OWNERSHIP_INDEX 和复制的member indexes可查归属；不直接运行 `source_index` 内的旧机器绝对路径。",
              "4. 先按原 relocator 重定位来源索引，再以对应Python运行原AN2；分析代码的包内位置见JSON的 `analysis_code_inside_archives`。不重跑模型，不重新评分，不覆盖旧输出。", "",
              "原恢复/重定位程序入口（整库clone会保留依赖的相对布局）：", ""]
    for tool in index["restore_and_relocation_tools"]:
        a = tool["artifact"]
        if a["repo_path"].endswith(("restore_collection.py", "/relocate.py")):
            lines.append(f"- {tool['model']} [{PurePosixPath(a['repo_path']).name}]({a['url']})")
    lines += ["", "完整恢复会写出数万小文件；只需查看指标时直接下载上述CSV/JSON即可，不必先恢复raw。原工具与已发布分片是一套旧格式，不能把新的打包CLI直接当作旧collection恢复器。", "",
              "## 证据与公开范围", "",
              "本新索引只读固定Git树、collection/bundle/member/导出索引及小型说明。所有引用路径在同一提交存在、Git blob大小与既有清单一致；collection及member索引哈希和原件计数/字节和进行了元数据级自检。**556个tar的SHA来自原封存清单，本步骤没有重读或重新哈希tar/raw，也没有重新恢复或运行模型。**原件内容恢复/AN2十输出重现的验收证据见各模型最终 replay addendum，不能把导航生成误称为新一次全量内容验证。", "",
              "GLM旧 `FULL_DELIVERY.zh.md` 和部分冻结导出/报告里的pending是当时状态，最终状态以各自 `REPLAY_VERIFIED.zh.md` 为准。公共controls有已记录的非实验回执未公开（GLM4,783 B；K3新controls1,292 B，外层另10,383 B），不是原实验成绩删选；私有引用链并非完全自包含。保留所有实验dump与科学分母不意味着可以下载密钥、权重或每一份私有审计文件。", "",
              "复建本索引（只处理小元数据）：`python build_archive_index.py --repo /path/to/LLM_ExpGym-results --check`。没有递归复制审计链，也不把本索引自身纳入它所验证的旧提交。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--check", action="store_true", help="Compare generated index bytes, do not write")
    args = parser.parse_args()
    index = build(Metadata(args.repo))
    output = Path(__file__).resolve().parent
    documents = {"ARCHIVE_INDEX.json": json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                 "ARCHIVE_INDEX.md": markdown(index)}
    for name, text in documents.items():
        path = output / name
        if args.check:
            assert path.read_bytes() == text.encode(), name
        else:
            path.write_text(text, encoding="utf-8")
    print(json.dumps({"passed": True, "mode": "check" if args.check else "generate", "input_commit": COMMIT,
                      "totals": index["totals"], "self_check": index["self_check"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
