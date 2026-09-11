"""Synthetic metadata fixtures only; never open real study payloads or use GPUs."""
from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from build_archive_index import (ATTACHMENT_SCHEMA, SOURCE_COMMIT, OLD_REPORT_COMMIT,
                                 SCANNER_SHA256, build, classify, decode, main,
                                 markdown, read_pinned, sha, validate_manifest)


class ArchiveIndexTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="qwen_archive_index_fixture_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = {
            "schema": "expgym.delivery.v1",
            "archives": [{"path": "part-000001.tar.gz", "bytes": 100, "sha256": "a" * 64},
                         {"path": "part-000002.tar.gz", "bytes": 200, "sha256": "b" * 64}],
            "files": [
                {"path": "analysis/metrics.csv", "archive": "part-000001.tar.gz", "bytes": 11, "sha256": "c" * 64},
                {"path": "formal/invocations/job_one/api_dump/call.json", "archive": "part-000001.tar.gz", "bytes": 22, "sha256": "d" * 64},
                {"path": "formal/queue/controller.lock", "archive": "part-000002.tar.gz", "bytes": 0, "sha256": sha(b"")},
                {"path": "serving/launch01/failed.log", "archive": "part-000002.tar.gz", "bytes": 33, "sha256": "e" * 64}],
            "security": {"public_scan_passed": False, "scanner_sha256": None,
                         "known_secret_sources": 0, "advisory_count": None}}
        self.attachments = {"schema": ATTACHMENT_SCHEMA, "study_id": "qwen-fixture", "model": "Qwen fixture",
                            "files": [{"path": "analysis/metrics.csv", "bytes": 11, "sha256": "c" * 64,
                                       "role": "analysis", "description": "逐 item 指标", "member_path": "analysis/metrics.csv"},
                                      {"path": "study/helper.py", "bytes": 44, "sha256": "f" * 64,
                                       "role": "study_provenance", "description": "冻结 helper"}]}
        self.manifest_pin = {"bytes": 600, "sha256": "1" * 64}
        self.attachments_pin = {"bytes": 700, "sha256": "2" * 64}
        self.kwargs = {"data_commit": "3" * 40, "base_path": "results/qwen-fixture"}

    def build(self, **kwargs):
        return build(self.manifest, self.manifest_pin, self.attachments, self.attachments_pin,
                     **dict(self.kwargs, **kwargs))

    def put_json(self, path, obj):
        path.write_bytes((json.dumps(obj, sort_keys=True) + "\n").encode())
        return sha(path.read_bytes())

    def cli_args(self):
        self.manifest_path = self.root / "manifest.json"
        self.attachments_path = self.root / "attachments.json"
        return ["--manifest", str(self.manifest_path), "--manifest-sha256", self.put_json(self.manifest_path, self.manifest),
                "--attachments", str(self.attachments_path), "--attachments-sha256", self.put_json(self.attachments_path, self.attachments),
                "--data-commit", self.kwargs["data_commit"], "--base-path", self.kwargs["base_path"],
                "--output-dir", str(self.root / "report")]

    def call(self, args):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return main(args)

    def test_totals_distinguish_raw_compressed_outer_copies_controls(self):
        index = self.build()
        t = index["totals"]
        self.assertEqual(t["shards"], 2)
        self.assertEqual(t["members"], 4)
        self.assertEqual(t["member_original_bytes"], 66)
        self.assertEqual(t["shard_compressed_bytes"], 300)
        self.assertEqual(t["outer_attachments"], 2)
        self.assertEqual(t["outer_attachment_bytes"], 55)
        self.assertEqual(t["outer_member_copies"], 1)
        self.assertEqual(t["outer_member_copy_bytes"], 11)
        self.assertEqual(t["unique_logical_payload_paths"], 5)
        self.assertEqual(t["unique_logical_payload_bytes"], 110)
        self.assertEqual(t["listed_physical_files"], 6)
        self.assertEqual(t["listed_physical_file_bytes"], 1655)
        self.assertEqual(sum(r["members"] for r in index["member_roles"]), 4)
        self.assertEqual(sum(r["original_bytes"] for r in index["archives"]), 66)
        self.assertNotIn("files", index)  # Member list is not duplicated.

    def test_roles_cover_current_layout_and_keep_unknown(self):
        cases = {
            "formal/invocations/job_x/api_dump/attempt.json": "formal_api",
            "formal/invocations/job_x/result/model/traces-v2/trace.json": "formal_trace",
            "formal/invocations/job_x/result/naive/result.json": "formal_terminal",
            "formal/invocations/job_x/result/naive/agents/agent_0.json": "formal_terminal",
            "formal/invocations/job_x/terminal_evidence/answer.json": "formal_terminal",
            "formal/invocations/job_x/worker.json": "formal_other",
            "formal/queue/sessions/one/summary.json": "formal_queue",
            "task_smoke01/queue/controller.lock": "task_smoke_queue",
            "task_smoke01/invocations/x/api_dump/a.json": "task_smoke",
            "native_smoke01/attempt.json": "native_smoke",
            "serving/launch01/failed.log": "serving_launch01",
            "serving/launch02/running.log": "serving_launch02",
            "analysis/raw_terminals.csv": "analysis",
            "study/metadata.json": "study_provenance", "runtime/uv.lock": "study_provenance",
            "PLAN.zh.md": "study_provenance", "report/README.zh.md": "report", "unusual/file.json": "other"}
        for path, role in cases.items():
            with self.subTest(path=path):
                self.assertEqual(classify(path), role)

    def test_restoration_boundaries_and_fixed_tool_old_report_urls(self):
        index = self.build()
        body = markdown(index).decode()
        for phrase in ("恢复 **0 个文件**", "仍校验全部分片与全部未选中成员", "CLI exit 0",
                       "没有 `--relocate` 或 `--path-map`", "controller.lock", "input identity",
                       "不推荐用 symlink", "不是 Git clone 大小", "local-only", "更晚提交"):
            self.assertIn(phrase, body)
        self.assertIn("/%s/scripts/package_run.py" % SOURCE_COMMIT, body)
        self.assertIn("/%s/expgym/delivery.py" % SOURCE_COMMIT, body)
        self.assertIn("/%s/results/portable-eval-20260908" % OLD_REPORT_COMMIT, body)
        self.assertFalse(index["previous_study"]["included_in_current_totals"])
        self.assertFalse(index["restore"]["analyzer_arbitrary_root_relocation_supported"])

    def test_metadata_does_not_infer_run_success_scan_or_remote_presence(self):
        index = self.build()
        evidence = index["evidence"]
        self.assertEqual(evidence["experiment_execution_or_score_status"], "not_evaluated")
        self.assertFalse(evidence["remote_git_checked"])
        self.assertFalse(evidence["new_secret_scan_performed"])
        self.assertEqual(evidence["referenced_payload_files_read"], 0)
        self.assertEqual(evidence["outer_attachment_publication_clearance"], "not_evaluated")

    def test_valid_public_declaration_is_only_inherited(self):
        self.manifest["security"] = {"public_scan_passed": True, "scanner_sha256": SCANNER_SHA256,
                                     "known_secret_sources": 4, "advisory_count": 2}
        index = self.build()
        self.assertEqual(index["evidence"]["seal_security_declaration_inherited"]["advisory_count"], 2)
        self.assertFalse(index["evidence"]["new_secret_scan_performed"])
        self.assertIn("这里只继承该声明", markdown(index).decode())

    def test_invalid_manifest_schema_inventory_and_scan_flags_rejected(self):
        original = copy.deepcopy(self.manifest)
        mutations = [lambda m: m.update(schema="other"),
                     lambda m: m["files"].reverse(),
                     lambda m: m["files"][0].update(bytes=True),
                     lambda m: m["files"][0].update(sha256="bad"),
                     lambda m: m["files"][0].update(archive="part-999999.tar.gz"),
                     lambda m: m["archives"][0].update(path="other.tar.gz"),
                     lambda m: m["security"].update(public_scan_passed=True),
                     lambda m: m["security"].update(public_scan_passed=1)]
        for mutation in mutations:
            self.manifest = copy.deepcopy(original)
            mutation(self.manifest)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.build()

    def test_unsafe_duplicate_and_prefix_paths_rejected(self):
        original = copy.deepcopy(self.manifest)
        for path in ("../escape.json", "/absolute.json", "bad//path.json", "private/file.json", "weights/model.safetensors"):
            self.manifest = copy.deepcopy(original)
            self.manifest["files"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.build()
        self.manifest = copy.deepcopy(original)
        self.manifest["files"][1]["path"] = self.manifest["files"][0]["path"]
        with self.assertRaisesRegex(ValueError, "duplicate_path"):
            self.build()
        self.manifest["files"][1]["path"] = self.manifest["files"][0]["path"] + "/child.json"
        with self.assertRaisesRegex(ValueError, "file_directory_conflict"):
            self.build()

    def test_outer_copy_pins_binding_and_duplicate_physical_paths(self):
        original = copy.deepcopy(self.attachments)
        mutations = [lambda a: a["files"][0].update(bytes=12),
                     lambda a: a["files"][0].pop("member_path"),
                     lambda a: a["files"][0].update(member_path="missing"),
                     lambda a: a["files"].append(copy.deepcopy(a["files"][0])),
                     lambda a: a["files"][1].update(path="sealed/manifest.json"),
                     lambda a: a["files"][1].update(path="study/archive_attachments.json"),
                     lambda a: a["files"][1].update(path="sealed/part-000001.tar.gz"),
                     lambda a: a["files"][1].update(role="passed")]
        for mutation in mutations:
            self.attachments = copy.deepcopy(original)
            mutation(self.attachments)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.build()

    def test_mutable_or_unsafe_layout_rejected_and_url_encoded(self):
        for changes in ({"data_commit": "main"}, {"data_commit": "A" * 40}, {"base_path": "../results"},
                        {"archive_subdir": "/tmp/sealed"}, {"attachments_path": "sealed/manifest.json"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.build(**changes)
        index = self.build(base_path="results/qwen study", archive_subdir="sealed files")
        self.assertIn("qwen%20study/sealed%20files/manifest.json", index["manifest"]["url"])
        self.assertIn("'/downloaded/release/sealed files/manifest.json'", markdown(index).decode())

    def test_cli_only_reads_two_metadata_inputs_and_is_deterministic(self):
        args = self.cli_args()
        original = Path.read_bytes
        permitted = {self.manifest_path, self.attachments_path}
        seen = []
        def metadata_only(path):
            self.assertIn(path, permitted)
            seen.append(path)
            return original(path)
        with mock.patch.object(Path, "read_bytes", metadata_only):
            self.assertEqual(self.call(args), 0)
        self.assertCountEqual(seen, permitted)
        outputs = sorted((self.root / "report").iterdir())
        self.assertEqual([p.name for p in outputs], ["ARCHIVE_INDEX.json", "ARCHIVE_INDEX.md"])
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in outputs}
        self.assertEqual(self.call(args + ["--check"]), 0)
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in outputs})
        self.assertEqual(self.call(args), 1)  # Never overwrite either output.
        outputs[0].write_bytes(b"changed\n")
        self.assertEqual(self.call(args + ["--check"]), 1)

    def test_sha_duplicate_keys_nonfinite_and_symlinks_rejected(self):
        args = self.cli_args()
        args[args.index("--manifest-sha256") + 1] = "0" * 64
        self.assertEqual(self.call(args), 1)
        for raw in (b'{"schema":1,"schema":2}', b'{"n":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(raw)
        link = self.root / "linked.json"
        link.symlink_to(self.manifest_path)
        with self.assertRaisesRegex(ValueError, "symlink"):
            read_pinned(link, sha(self.manifest_path.read_bytes()))
        linked_dir = self.root / "linked-directory"
        actual_dir = self.root / "actual-directory"
        actual_dir.mkdir()
        linked_dir.symlink_to(actual_dir, target_is_directory=True)
        args = self.cli_args()
        args[args.index("--output-dir") + 1] = str(linked_dir / "new-output")
        self.assertEqual(self.call(args), 1)
        self.assertFalse((actual_dir / "new-output").exists())

    def test_empty_outer_inventory_is_honest(self):
        self.attachments["files"] = []
        index = self.build()
        self.assertEqual(index["totals"]["outer_attachments"], 0)
        self.assertIn("无明确列件", markdown(index).decode())
        self.assertFalse(index["scope"]["later_report_or_index_files_implicitly_included"])

    def test_accepts_actual_synthetic_delivery_seal_manifest(self):
        source = Path(__file__).resolve().parents[2] / "LLM_ExpGym-qwen38-20260910"
        sys.path.insert(0, str(source))
        try:
            from expgym.delivery import seal, _manifest
        finally:
            sys.path.remove(str(source))
        source_root = self.root / "synthetic_source"
        source_root.mkdir()
        (source_root / "fixture.json").write_bytes(b'{"fixture":true}\n')
        actual = seal(source_root, ["fixture.json"], self.root / "synthetic_sealed", None)
        self.assertEqual(validate_manifest(actual), _manifest(actual))
        self.manifest = actual
        self.attachments["files"] = []
        index = self.build()
        self.assertEqual(index["totals"]["members"], 1)
        self.assertEqual(index["member_roles"][0]["role"], "other")


if __name__ == "__main__":
    unittest.main()
