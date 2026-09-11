#!/usr/bin/env python3
"""Deterministic, metadata-only Qwen archive index; never open payloads or Git.

Inputs are a package_run.py expgym.delivery.v1 manifest and this explicit outer
attachment inventory (both require their independently recorded SHA256):
  {"schema":"qwen38.archive-attachments.v1", "study_id":"...", "model":"...",
   "files":[{"path":"analysis/metrics.csv", "bytes":123, "sha256":"...",
             "role":"analysis", "description":"逐 item 指标",
             "member_path":"analysis/metrics.csv"}]}
Paths are relative to --base-path in --data-commit. member_path is optional;
when an outer file is a copy of a tar member, supply its original member path.
Its size/hash must match. The inventory itself is a separate metadata control,
not one of its own files. Only list files already present in that data commit;
later reports/indexes are not implicitly included. No mutable branch URLs.

CLI: --manifest FILE --manifest-sha256 SHA --attachments FILE
     --attachments-sha256 SHA --data-commit 40HEX --base-path REPO_REL_PATH
     --archive-subdir sealed --attachments-path study/archive_attachments.json
     --output-dir DIR [--check]
Outputs only ARCHIVE_INDEX.md and ARCHIVE_INDEX.json. No timestamps, network,
raw traversal, payload hashes, scoring, secret scans or success-state inference.
The two input JSON files are read/hash-checked; every referenced object's pin
and scan declaration is inherited, not reverified by this index generator.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import stat
import sys
from urllib.parse import quote

SCHEMA = "qwen38.archive-index.v1"
ATTACHMENT_SCHEMA = "qwen38.archive-attachments.v1"
SOURCE_COMMIT = "21b4de99b2a014874e3cec1595eaa40762b0c564"
OLD_REPORT_COMMIT = "0ee6f4a2f69a463fdf98f8d787b4ce5662a5af91"
SCANNER_SHA256 = "aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116"
# Frozen delivery.py path policy; tests exercise its real synthetic seal output.
DENIED_PARTS = {"private", ".git", ".ssh", ".aws", ".config", ".venv", "venv", "env",
                "uv", ".uv", "environments", "cache", ".cache", "__pycache__", "weights",
                "ckpts", "checkpoints", "node_modules", "router_api_key", "id_rsa",
                "id_ed25519", "credentials"}
DENIED_SUFFIXES = {".safetensors", ".bin", ".pt", ".pth", ".ckpt", ".pkl", ".pickle",
                   ".pem", ".key", ".p12", ".pfx", ".pyc", ".so", ".dll"}
REPOSITORY = "https://github.com/tiannuo-yang/LLM_ExpGym"
OUTER_ROLES = {"analysis", "study_provenance", "restoration_tools", "validation", "report"}
ROLES = {
    "formal_api": ("正式 API 请求/回复", "formal/invocations/*/api_dump/；包含已保存的全部尝试，不按答案/得分筛选。"),
    "formal_trace": ("正式 ExpGym 轨迹", "formal/invocations/* 下 traces-v2 或 traces；终态可能内嵌于轨迹。"),
    "formal_terminal": ("正式 Pool 结果/agent 与终态证据", "result.json、agents/agent_*.json 或 terminal_evidence；Pool 文件也可含完整轨迹。"),
    "formal_other": ("正式 invocation 其他原件", "其余已选择的 worker、配置、运行日志等；分类不判断运行成功。"),
    "formal_queue": ("正式调度元数据", "formal/queue/；保留所有所选 session、completion、日志和 controller.lock。"),
    "task_smoke_queue": ("任务 smoke 调度元数据", "task_smoke01/queue/，与正式队列分开。"),
    "task_smoke": ("任务 smoke 原件", "task_smoke01/ 的任务 dump/结果/诊断；不混入正式指标/HTTP 成本分母。"),
    "native_smoke": ("原生协议 smoke", "native_smoke01/；用于协议诊断，不是正式实验结果。"),
    "serving_launch01": ("服务 launch01 诊断", "serving/launch01/；保留所选原件，不从目录名推断最终状态。"),
    "serving_launch02": ("服务 launch02 诊断", "serving/launch02/；保留所选原件，不从目录名推断最终状态。"),
    "analysis": ("分析与全设置比较", "逐 execution/item 指标、聚合/重复/比较、SOURCE_INDEX、INPUTS 和全部尝试成本；raw_terminals.csv 是终态投影，不是 HTTP dump。"),
    "study_provenance": ("研究/运行身份", "study/、runtime/ 的明确选件与 PLAN.zh.md；不等于复制权重、环境或数据集。"),
    "report": ("已有报告附件", "只计入清单明确列出的既有报告；后续报告不自动包含。"),
    "restoration_tools": ("恢复工具外层副本", "明确选择的工具副本；原冻结源码入口另列。"),
    "validation": ("有限检查附件", "明确选择的检查记录；其内容未由索引器重新执行。"),
    "other": ("其他明确封存原件", "未命中以上路径分类的成员；仍完整计入全局 manifest，不丢弃。"),
}
OUTPUTS = ("ARCHIVE_INDEX.md", "ARCHIVE_INDEX.json")


def require(ok, rule):
    if not ok:
        raise ValueError(rule)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "invalid_sha256")
    return value


def relative(value):
    require(isinstance(value, str) and bool(value) and not any(ord(c) < 32 for c in value)
            and "\\" not in value and not PurePosixPath(value).is_absolute()
            and all(p not in ("", ".", "..") for p in value.split("/")), "invalid_relative_path")
    for part in PurePosixPath(value).parts:
        lower = part.lower()
        require(lower not in DENIED_PARTS and lower != ".env" and not lower.startswith(".env.")
                and not lower.endswith(("_api_key", "_private_key")), "forbidden_path")
    require(PurePosixPath(value).suffix.lower() not in DENIED_SUFFIXES, "forbidden_path")
    return value


def unique_paths(paths):
    checked = [relative(name) for name in paths]
    require(len(set(checked)) == len(checked), "duplicate_path")
    names = set(checked)
    require(not any(str(parent) in names for name in names
                    for parent in PurePosixPath(name).parents if str(parent) != "."), "file_directory_conflict")
    return checked


def pin(row, *, positive=False):
    require(type(row["bytes"]) is int and row["bytes"] >= (1 if positive else 0), "invalid_bytes")
    digest(row["sha256"])


def decode(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def regular_path(path):
    path = Path(os.path.abspath(path))
    for parent in reversed(path.parents):
        require(stat.S_ISDIR(parent.lstat().st_mode), "symlink_or_non_directory_parent")
    require(stat.S_ISREG(path.lstat().st_mode), "symlink_or_non_regular_input")
    return path


def read_pinned(path, expected):
    digest(expected)
    path = regular_path(path)
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    signature = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    require(signature(before) == signature(after) and len(raw) == before.st_size, "input_changed")
    require(sha(raw) == expected, "input_sha256_mismatch")
    return decode(raw), {"bytes": len(raw), "sha256": expected}


def validate_manifest(value):
    """Validate the actual delivery.v1 structure, without importing a runtime.

    This is metadata validation only, not a replacement for delivery.verify().
    Fixture tests also feed an actual synthetic package_run seal manifest here.
    """
    require(isinstance(value, dict) and set(value) == {"schema", "archives", "files", "security"}
            and value["schema"] == "expgym.delivery.v1", "invalid_manifest_schema")
    require(isinstance(value["archives"], list) and value["archives"], "invalid_archives")
    for number, row in enumerate(value["archives"], 1):
        require(isinstance(row, dict) and set(row) == {"path", "bytes", "sha256"}
                and row["path"] == "part-%06d.tar.gz" % number, "invalid_archive_entry")
        pin(row, positive=True)
    archive_names = {row["path"] for row in value["archives"]}
    require(isinstance(value["files"], list) and value["files"], "invalid_member_inventory")
    for row in value["files"]:
        require(isinstance(row, dict) and set(row) == {"path", "archive", "bytes", "sha256"}
                and row["archive"] in archive_names, "invalid_member_entry")
        pin(row)
    names = unique_paths([row["path"] for row in value["files"]])
    require(names == sorted(names), "noncanonical_member_order")
    require({row["archive"] for row in value["files"]} == archive_names, "empty_archive")
    security = value["security"]
    require(isinstance(security, dict) and set(security) == {
        "public_scan_passed", "scanner_sha256", "known_secret_sources", "advisory_count"}, "invalid_scan_declaration")
    require(type(security["public_scan_passed"]) is bool, "invalid_scan_declaration")
    if security["public_scan_passed"]:
        require(security["scanner_sha256"] == SCANNER_SHA256
                and type(security["known_secret_sources"]) is int and security["known_secret_sources"] == 4
                and type(security["advisory_count"]) is int and security["advisory_count"] >= 0,
                "invalid_scan_declaration")
    else:
        require(security == {"public_scan_passed": False, "scanner_sha256": None,
                            "known_secret_sources": 0, "advisory_count": None}, "invalid_scan_declaration")
    return value


def classify(path):
    parts = PurePosixPath(path).parts
    if path.startswith("formal/queue/"):
        return "formal_queue"
    if path.startswith("formal/invocations/"):
        if "api_dump" in parts:
            return "formal_api"
        if "traces-v2" in parts or "traces" in parts:
            return "formal_trace"
        if (parts[-1] == "result.json" or "terminal_evidence" in parts
                or ("agents" in parts and re.fullmatch(r"agent_\d+\.json", parts[-1]))):
            return "formal_terminal"
        return "formal_other"
    for prefix, role in (("task_smoke01/queue/", "task_smoke_queue"),
                         ("task_smoke01/", "task_smoke"), ("native_smoke01/", "native_smoke"),
                         ("serving/launch01/", "serving_launch01"), ("serving/launch02/", "serving_launch02")):
        if path.startswith(prefix):
            return role
    if parts[0] == "analysis":
        return "analysis"
    if parts[0] in {"study", "runtime"} or path == "PLAN.zh.md":
        return "study_provenance"
    if parts[0] in {"report", "reports"}:
        return "report"
    return "other"


def text_field(value):
    require(isinstance(value, str) and bool(value.strip())
            and not any(ord(c) < 32 for c in value), "invalid_text_field")
    return value


def escaped(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("[", "&#91;").replace("]", "&#93;")


def build(manifest, manifest_pin, attachments, attachments_pin, *, data_commit,
          base_path, archive_subdir="sealed", attachments_path="study/archive_attachments.json"):
    validate_manifest(manifest)
    pin(manifest_pin)
    pin(attachments_pin)
    require(isinstance(data_commit, str) and re.fullmatch(r"[0-9a-f]{40}", data_commit), "immutable_data_commit_required")
    for value in (base_path, archive_subdir, attachments_path):
        relative(value)
    require(isinstance(attachments, dict) and set(attachments) == {"schema", "study_id", "model", "files"}
            and attachments["schema"] == ATTACHMENT_SCHEMA, "invalid_attachment_schema")
    text_field(attachments["study_id"])
    text_field(attachments["model"])
    require(isinstance(attachments["files"], list), "invalid_attachment_inventory")
    members = {row["path"]: row for row in manifest["files"]}
    url = lambda path: "%s/blob/%s/%s" % (REPOSITORY, data_commit, quote(base_path + "/" + path, safe="/"))
    outer = []
    for row in attachments["files"]:
        require(isinstance(row, dict) and set(row) in (
            {"path", "bytes", "sha256", "role", "description"},
            {"path", "bytes", "sha256", "role", "description", "member_path"}), "invalid_attachment_entry")
        relative(row["path"])
        pin(row)
        require(row["role"] in OUTER_ROLES, "invalid_attachment_role")
        text_field(row["description"])
        member_path = row.get("member_path")
        require(row["path"] not in members or member_path == row["path"], "same_path_copy_requires_member_binding")
        if member_path is not None:
            require(member_path in members and all(row[key] == members[member_path][key]
                    for key in ("bytes", "sha256")), "outer_member_copy_mismatch")
        outer.append({**row, "url": url(row["path"]), "pin_evidence": "inherited_attachment_inventory"})
    outer.sort(key=lambda row: row["path"])
    manifest_path = archive_subdir + "/manifest.json"
    physical_paths = [manifest_path, attachments_path] + [archive_subdir + "/" + row["path"] for row in manifest["archives"]] + [row["path"] for row in outer]
    unique_paths(physical_paths)
    counts = defaultdict(lambda: {"members": 0, "original_bytes": 0})
    by_archive = defaultdict(lambda: {"members": 0, "original_bytes": 0})
    for row in manifest["files"]:
        for counter in (counts[classify(row["path"])], by_archive[row["archive"]]):
            counter["members"] += 1
            counter["original_bytes"] += row["bytes"]
    archives = [{**row, **by_archive[row["path"]], "url": url(archive_subdir + "/" + row["path"]),
                 "pin_evidence": "inherited_seal_manifest"} for row in manifest["archives"]]
    copies = [row for row in outer if row.get("member_path") is not None]
    outer_only = [row for row in outer if row.get("member_path") is None]
    original_bytes = sum(row["bytes"] for row in manifest["files"])
    compressed_bytes = sum(row["bytes"] for row in archives)
    outer_bytes = sum(row["bytes"] for row in outer)
    control_bytes = manifest_pin["bytes"] + attachments_pin["bytes"]
    source_url = lambda path: "%s/blob/%s/%s" % (REPOSITORY, SOURCE_COMMIT, path)
    old_base = "%s/blob/%s/results/portable-eval-20260908/full_matrix_report_v1/" % (REPOSITORY, OLD_REPORT_COMMIT)
    index = {
        "schema": SCHEMA, "study_id": attachments["study_id"], "model": attachments["model"],
        "data": {"repository": REPOSITORY, "commit": data_commit, "base_path": base_path},
        "manifest": {"path": manifest_path, **manifest_pin, "url": url(manifest_path),
                     "schema": manifest["schema"], "member_mapping": "files[].{path,archive,bytes,sha256}"},
        "attachment_inventory": {"path": attachments_path, **attachments_pin, "url": url(attachments_path)},
        "totals": {"global_manifests": 1, "shards": len(archives), "members": len(members),
                   "member_original_bytes": original_bytes, "shard_compressed_bytes": compressed_bytes,
                   "outer_attachments": len(outer), "outer_attachment_bytes": outer_bytes,
                   "outer_member_copies": len(copies), "outer_member_copy_bytes": sum(row["bytes"] for row in copies),
                   "unique_logical_payload_paths": len(members) + len(outer_only),
                   "unique_logical_payload_bytes": original_bytes + sum(row["bytes"] for row in outer_only),
                   "metadata_controls": 2, "metadata_control_bytes": control_bytes,
                   "listed_physical_files": len(physical_paths),
                   "listed_physical_file_bytes": compressed_bytes + outer_bytes + control_bytes},
        "member_roles": [{"role": role, "label": ROLES[role][0], "scope": ROLES[role][1], **counts[role]}
                         for role in ROLES if role in counts],
        "archives": archives, "outer_attachments": outer,
        "evidence": {"input_metadata_files_read_and_sha256_checked": 2,
                     "referenced_payload_files_read": 0, "archive_contents_verified_by_indexer": False,
                     "new_secret_scan_performed": False, "remote_git_checked": False,
                     "experiment_execution_or_score_status": "not_evaluated",
                     "seal_security_declaration_inherited": manifest["security"],
                     "outer_attachment_publication_clearance": "not_evaluated"},
        "restore": {"source_commit": SOURCE_COMMIT,
                    "package_run": source_url("scripts/package_run.py"), "delivery": source_url("expgym/delivery.py"),
                    "default_verify_restored_files": 0, "selective_restore_still_verifies_every_member": True,
                    "analyzer_arbitrary_root_relocation_supported": False,
                    "original_analysis_replay_requires_frozen_absolute_layout": True},
        "previous_study": {"report": old_base + "README.zh.md", "archive_index": old_base + "ARCHIVE_INDEX.md",
                           "included_in_current_totals": False},
        "scope": {"later_report_or_index_files_implicitly_included": False,
                  "member_inventory_copied_into_index": False,
                  "listed_bytes_are_git_clone_size": False},
    }
    return index


def markdown(index):
    t = index["totals"]
    link = lambda label, target: "[%s](%s)" % (escaped(label), target)
    lines = ["# Qwen 完整存档索引", "", "%s · `%s`。本索引只整理明确清单，不新增模型调用、评分或内容扫描。" % (
        escaped(index["model"]), escaped(index["study_id"])), "",
        "固定数据提交：`%s`；仓库内根目录：`%s`。本索引/后续报告可属于更晚提交，不能据此宣称它们已包含于该数据提交。" % (
            index["data"]["commit"], escaped(index["data"]["base_path"])), "",
        "## 入口与范围", "",
        "- %s：唯一逐原件映射；`files[]` 给出原相对路径、所属 shard、原字节和 SHA-256。索引不再复制逐原件长清单。" % link("全局 manifest", index["manifest"]["url"]),
        "- %s：数据提交中明确选择的外层 CSV/JSON/代码等；只下载 tar 不足以取得这些文件。" % link("外层附件 inventory", index["attachment_inventory"]["url"]),
        "- 既有 %s / %s 独立保留，不重复计入本次 Qwen 大小或文件数。" % (
            link("Kimi-K3 / GLM-5.3 报告", index["previous_study"]["report"]),
            link("旧研究存档索引", index["previous_study"]["archive_index"])), "",
        "| 范围 | 文件/分片数 | 字节（B） |", "| --- | ---: | ---: |",
        "| tar.gz 分片 | %d | %d（压缩文件） |" % (t["shards"], t["shard_compressed_bytes"]),
        "| tar 原件 members | %d | %d（原件，不含 tar/gzip 结构开销） |" % (t["members"], t["member_original_bytes"]),
        "| 外层附件 | %d | %d |" % (t["outer_attachments"], t["outer_attachment_bytes"]),
        "| 其中：与 member 身份一致的外层副本 | %d | %d（已包含于上一行） |" % (t["outer_member_copies"], t["outer_member_copy_bytes"]),
        "| metadata controls（manifest + 附件 inventory） | 2 | %d |" % t["metadata_control_bytes"],
        "| 已列物理文件合计（分片 + 外层 + controls） | %d | %d |" % (t["listed_physical_files"], t["listed_physical_file_bytes"]), "",
        "members 与外层副本去重后为 %d 个逻辑原件路径、%d B；只按显式 `member_path` 身份绑定去重，不把相同内容的不同实验文件合并。上述大小不是 Git clone 大小，也不自动包含本索引、后续报告、权重、完整环境或外部数据集。" % (
            t["unique_logical_payload_paths"], t["unique_logical_payload_bytes"]), "",
        "## tar 内路径分类", "", "以下为互斥的路径用途分类，不是运行/评分成功率。完整路径与 hash 仍以全局 manifest 为准。", "",
        "| 用途 | members | 原字节（B） | 路径/口径 |", "| --- | ---: | ---: | --- |"]
    for row in index["member_roles"]:
        lines.append("| %s | %d | %d | %s |" % (escaped(row["label"]), row["members"], row["original_bytes"], escaped(row["scope"])))
    lines += ["", "## 分片下载", "", "| 分片 | members | 原字节（B） | 压缩字节（B） | SHA-256（继承） |", "| --- | ---: | ---: | ---: | --- |"]
    for row in index["archives"]:
        lines.append("| %s | %d | %d | %d | `%s` |" % (link(row["path"], row["url"]), row["members"], row["original_bytes"], row["bytes"], row["sha256"]))
    lines += ["", "## 外层附件", "", "这些链接只指向所给固定数据提交；生成器不访问 GitHub 来确认远端对象。`member_path` 表示 tar 中保留的同一原件副本，其大小/hash 已在两份 metadata 间比对。", "",
              "| 文件 | 用途 | 字节（B） | tar member 副本 |", "| --- | --- | ---: | --- |"]
    for row in index["outer_attachments"]:
        lines.append("| %s | %s | %d | %s |" % (link(row["path"], row["url"]), escaped(row["description"]), row["bytes"], escaped(row.get("member_path", "无"))))
    if not index["outer_attachments"]:
        lines.append("| 无明确列件 | 不推断缺失或未来附件 | 0 | — |")
    lines += ["", "外层附件 SHA-256 见机器索引 `outer_attachments` 与原 inventory；它们是继承声明，不是本次对附件内容的重新哈希。", "",
              "## 实际检查范围", "",
              "本生成器仅实读并 SHA-256 校验两份输入 metadata；没有打开 tar/member 或外层附件 payload，没有重新读密钥、扫描、评分，也没有查询 Git/Slurm。运行是否完成、终态是否可评分及远端是否存在均不由本索引推断。", "",
              "| 本次实读输入 | 字节（B） | SHA-256 |", "| --- | ---: | --- |"]
    for key, label in (("manifest", "manifest"), ("attachment_inventory", "外层 inventory")):
        row = index[key]
        lines.append("| %s | %d | `%s` |" % (label, row["bytes"], row["sha256"]))
    security = index["evidence"]["seal_security_declaration_inherited"]
    if security["public_scan_passed"]:
        lines += ["", "manifest 原有声明为 `public_scan_passed=true`，scanner SHA 为 `%s`，已知密钥来源数 %d，advisory 数 %d。这里只继承该声明；它不是新扫描或独立签名，也不自动放行外层/后续报告文件。" % (
            security["scanner_sha256"], security["known_secret_sources"], security["advisory_count"])]
    else:
        lines += ["", "manifest 原有声明为 `public_scan_passed=false`：这是 local-only 封包，不能据此视为公开发布通过；下述 `--require-public-scan` 会拒绝它。"]
    lines += ["", "最终索引生成器见 [同一报告提交的 build_archive_index.py](../study/build_archive_index.py)。数据提交和 tar 内工具是封存时的历史版本；成稿复核后的文案修订版本随本报告提交，不应混淆。此修订没有改动原件、分析值或 archive identity。", "",
              "## 验证、选择性恢复与分析重放", "",
              "使用冻结源码 `%s` 中的 %s 与 %s；先核对下载提交/manifest 身份，再调用对应版本。" % (
                  SOURCE_COMMIT, link("scripts/package_run.py", index["restore"]["package_run"]), link("expgym/delivery.py", index["restore"]["delivery"])), "",
              "默认验证全部 shard 和全部 member，恢复 **0 个文件**：", "", "```bash",
              "python -B /absolute/frozen-source/scripts/package_run.py verify \\",
              "  --manifest %s \\" % shlex.quote("/downloaded/release/" + index["manifest"]["path"]),
              "  --archive-dir %s --require-public-scan" % shlex.quote("/downloaded/release/" + str(PurePosixPath(index["manifest"]["path"]).parent)),
              "```", "", "如果只需部分原件，以原 member 相对路径写非空 JSON 字符串数组作为选择清单；增加：", "", "```bash",
              "  --select /absolute/selected-member-paths.json \\",
              "  --restore-dir /absolute/fresh-selected-inputs", "```", "",
              "`--select` / `--restore-dir` 只决定写出哪些文件，仍校验全部分片与全部未选中成员。恢复目录必须事先不存在；失败可能留下不完整私有目录。只有 CLI exit 0 表示该次完整性验证完成，目录存在不等于成功；完整性不等于重新评分或科学真实性证明。外层附件作为独立文件分发；有 member_path 身份绑定的副本也存在于 tar 中，无副本的附件须另取并按其继承 pin 校验。", "",
              "`--require-public-scan` 只检查可信 manifest 的原扫描声明，不重新读取密钥或扫描内容。未核对 manifest 的来源时，一个手写 true 不构成可信证据。", "",
              "当前 `analyze_qwen.py` 内部绑定绝对 state/artifact/authorization 路径，没有 `--relocate` 或 `--path-map`。任意新根可用于查看/验证 raw 与 CSV，不自动支持原样 raw→analysis 重放。原重放需要冻结的绝对布局、脚本/Python 身份和全部实际读取依赖（包括 controller.lock、session 元数据及所选授权记录），以及新的输出目录；不能假定只恢复几份 CSV 足够。需要逐字节重放时还应保留记录中的实际输入/脚本路径和解释器版本。", "",
              "不推荐用 symlink 绕过布局：分析器拒绝 symlink 父目录。修改绑定路径会形成新的 input identity，不能宣称已经通过原身份的重放；本索引未尝试这种迁移。原始源码/数据/权重的身份记录不代表其实体已收入当前 tar。", ""]
    return "\n".join(lines).encode("utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("manifest", "attachments"):
        parser.add_argument("--" + name, type=Path, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--data-commit", required=True)
    parser.add_argument("--base-path", required=True)
    parser.add_argument("--archive-subdir", default="sealed")
    parser.add_argument("--attachments-path", default="study/archive_attachments.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest, manifest_pin = read_pinned(args.manifest, args.manifest_sha256)
        attachments, attachments_pin = read_pinned(args.attachments, args.attachments_sha256)
        index = build(manifest, manifest_pin, attachments, attachments_pin,
                      data_commit=args.data_commit, base_path=args.base_path,
                      archive_subdir=args.archive_subdir, attachments_path=args.attachments_path)
        outputs = {"ARCHIVE_INDEX.md": markdown(index),
                   "ARCHIVE_INDEX.json": (json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2,
                                                     allow_nan=False) + "\n").encode("utf-8")}
        if args.check:
            for name, raw in outputs.items():
                require(regular_path(args.output_dir / name).read_bytes() == raw, "output_bytes_differ")
        else:
            require(not args.output_dir.is_symlink(), "symlink_output_directory")
            for parent in args.output_dir.parents:
                require(stat.S_ISDIR(parent.lstat().st_mode), "symlink_or_non_directory_parent")
            args.output_dir.mkdir(exist_ok=True)
            require(stat.S_ISDIR(args.output_dir.lstat().st_mode), "symlink_or_non_directory_parent")
            require(all(not (args.output_dir / name).exists() and not (args.output_dir / name).is_symlink()
                        for name in OUTPUTS), "fresh_output_files_required")
            for name, raw in outputs.items():
                with (args.output_dir / name).open("xb") as handle:
                    handle.write(raw)
        print(json.dumps({"index_metadata_checked": True, "check_only": args.check,
                          "outputs": list(OUTPUTS), "referenced_payload_files_read": 0,
                          "new_secret_scan_performed": False}, sort_keys=True))
        return 0
    except Exception as error:
        rule = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z0-9_]+", str(error)) else "archive_index_failed"
        print(json.dumps({"index_metadata_checked": False, "rule": rule}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
