"""Tempfile-only CLI checks; never invoke a study or inspect real run outputs."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("resume_integrity.py").resolve()


class ResumeIntegrityCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="resume_integrity_test_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "output"
        self.dump = self.root / "dump"
        self.reports = self.root / "reports"
        for directory in (self.output, self.dump, self.reports):
            directory.mkdir()
        self.summary = self.write(self.output / "summary.json", b'{"a":1,"b":2}\n')
        self.agent = self.write(self.output / "agents" / "one.json", b'{"agent":1}\n')
        self.raw = self.write(self.dump / "allraw.json", b'{"raw":[1]}\n')
        self.metadata = [
            self.write(self.output / name, b'{"state":"before"}\n')
            for name in ("progress.json", "status.json", "stdout.json")
        ]
        self.ignored = self.write(self.dump / "notes.txt", b"ignored\n")
        self.manifest = self.root / "manifest.json"
        self.manifest_data = {
            "jobs": [{
                "id": "fixture_job",
                "output_dir": "output",
                "dump_dir": str(self.dump),
                "status_path": "output/status.json",
                "stdout_log": "output/stdout.json",
            }],
            "progress_path": "output/progress.json",
        }
        self.save_manifest()

    @staticmethod
    def write(path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def save_manifest(self):
        self.manifest.write_text(json.dumps(self.manifest_data, indent=2), encoding="utf-8")

    def invoke(self, command, report, snapshot=None):
        args = [sys.executable, str(SCRIPT), command,
                "--manifest", str(self.manifest), "--report", str(report)]
        if snapshot is not None:
            args.extend(["--snapshot", str(snapshot)])
        return subprocess.run(args, cwd=str(self.root), capture_output=True, text=True)

    def run_report(self, command, name, expected_code=0, snapshot=None):
        report = self.reports / name
        self.assertFalse(report.exists(), "Each successful report must use a fresh path")
        result = self.invoke(command, report, snapshot)
        self.assertEqual(result.returncode, expected_code, result.stdout + result.stderr)
        self.assertTrue(report.is_file(), result.stdout + result.stderr)
        return report, json.loads(report.read_text(encoding="utf-8"))

    def expected_totals(self, output_paths, dump_paths):
        groups = {"output_json": output_paths, "api_dump_json": dump_paths}
        by_kind = {
            kind: {"files": len(paths), "bytes": sum(p.stat().st_size for p in paths)}
            for kind, paths in groups.items()
        }
        return {
            "total_files": sum(value["files"] for value in by_kind.values()),
            "total_bytes": sum(value["bytes"] for value in by_kind.values()),
            "by_kind": by_kind,
        }

    def monitored_bytes(self):
        return {
            str(path): path.read_bytes()
            for directory in (self.output, self.dump)
            for path in directory.rglob("*") if path.is_file()
        }

    def assert_totals(self, actual, expected):
        self.assertEqual({key: actual[key] for key in expected}, expected)

    def test_unchanged_payloads_ignore_orchestration_metadata(self):
        baseline, initial = self.run_report("snapshot", "baseline.json")
        self.assertIn("schema_version", initial)
        expected_paths = {str(self.summary), str(self.agent), str(self.raw)}
        self.assertEqual({item["path"] for item in initial["files"]}, expected_paths)
        for item in initial["files"]:
            path = Path(item["path"])
            payload = path.read_bytes()
            self.assertEqual(item["bytes"], len(payload))
            self.assertEqual(item["sha256"], hashlib.sha256(payload).hexdigest())
            kind = "api_dump_json" if path == self.raw else "output_json"
            self.assertEqual(item["owners"], [{"job_id": "fixture_job", "kind": kind}])
        expected = self.expected_totals([self.summary, self.agent], [self.raw])
        self.assert_totals(initial["totals"], expected)

        for path in self.metadata:
            path.write_bytes(b'{"state":"after","count":100}\n')
        self.ignored.write_bytes(b"also ignored after changing\n")
        self.manifest.write_text(json.dumps(self.manifest_data), encoding="utf-8")
        _, comparison = self.run_report("compare", "unchanged.json", snapshot=baseline)
        self.assertIs(comparison["passed"], True)
        for key in ("added", "removed", "changed"):
            self.assertEqual(comparison[key], [])
        self.assert_totals(comparison["before_totals"], expected)
        self.assert_totals(comparison["after_totals"], expected)

    def test_added_raw_removed_agent_and_byte_changed_summary(self):
        baseline, initial = self.run_report("snapshot", "baseline.json")
        before_summary = self.summary.read_bytes()
        self.summary.write_bytes(b'{"b": 2, "a": 1}\n')
        self.assertEqual(json.loads(before_summary), json.loads(self.summary.read_bytes()))
        self.agent.unlink()
        added = self.write(self.dump / "nested" / "new_raw.json", b'{"raw":[2,3]}\n')

        _, comparison = self.run_report("compare", "differences.json", 1, baseline)
        self.assertIs(comparison["passed"], False)
        self.assertEqual({item["path"] for item in comparison["added"]}, {str(added)})
        self.assertEqual({item["path"] for item in comparison["removed"]}, {str(self.agent)})
        self.assertEqual(len(comparison["changed"]), 1)
        change = comparison["changed"][0]
        self.assertEqual(change["path"], str(self.summary))
        self.assertEqual(change["before"]["sha256"], hashlib.sha256(before_summary).hexdigest())
        self.assertEqual(change["after"]["sha256"], hashlib.sha256(self.summary.read_bytes()).hexdigest())
        self.assertEqual(comparison["before_totals"], initial["totals"])
        self.assert_totals(comparison["after_totals"], self.expected_totals([self.summary], [self.raw, added]))

    def test_reject_existing_and_monitored_report_paths_without_mutation(self):
        baseline, _ = self.run_report("snapshot", "baseline.json")
        for command in ("snapshot", "compare"):
            with self.subTest(command=command, location="existing"):
                report = self.write(self.reports / (command + "_existing.json"), b"preserve me\n")
                before = self.monitored_bytes()
                result = self.invoke(command, report, baseline if command == "compare" else None)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(report.read_bytes(), b"preserve me\n")
                self.assertEqual(self.monitored_bytes(), before)
            for directory in (self.output, self.dump):
                with self.subTest(command=command, location=str(directory)):
                    report = directory / (command + "_forbidden_report.json")
                    before = self.monitored_bytes()
                    result = self.invoke(command, report, baseline if command == "compare" else None)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertFalse(report.exists())
                    self.assertEqual(self.monitored_bytes(), before)

    def test_empty_root_scope_change_fails_with_identical_file_set(self):
        for name in ("empty_before", "empty_after", "empty_dump"):
            (self.root / name).mkdir()
        self.manifest_data["jobs"].append({
            "id": "empty_job", "output_dir": "empty_before", "dump_dir": "empty_dump",
        })
        self.save_manifest()
        baseline, initial = self.run_report("snapshot", "baseline.json")
        self.manifest_data["jobs"][1]["output_dir"] = "empty_after"
        self.save_manifest()

        _, comparison = self.run_report("compare", "scope_changed.json", 1, baseline)
        self.assertIs(comparison["passed"], False)
        for key in ("added", "removed", "changed"):
            self.assertEqual(comparison[key], [])
        self.assertEqual(comparison["before_totals"], initial["totals"])
        self.assertEqual(comparison["after_totals"], initial["totals"])

    def test_dangling_report_symlink_is_rejected_without_creating_target(self):
        baseline, _ = self.run_report("snapshot", "baseline.json")
        for command in ("snapshot", "compare"):
            with self.subTest(command=command):
                target = self.reports / (command + "_absent_target.json")
                report = self.reports / (command + "_dangling_report.json")
                report.symlink_to(target)
                before = self.monitored_bytes()

                result = self.invoke(command, report, baseline if command == "compare" else None)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(report.is_symlink())
                self.assertEqual(report.resolve(), target)
                self.assertFalse(target.exists())
                self.assertEqual(self.monitored_bytes(), before)

    def test_deleted_empty_root_fails_with_identical_file_set(self):
        empty_output = self.root / "empty_output"
        empty_output.mkdir()
        (self.root / "empty_dump").mkdir()
        self.manifest_data["jobs"].append({
            "id": "empty_job", "output_dir": "empty_output", "dump_dir": "empty_dump",
        })
        self.save_manifest()
        baseline, initial = self.run_report("snapshot", "baseline.json")
        empty_output.rmdir()

        _, comparison = self.run_report("compare", "root_deleted.json", 1, baseline)
        self.assertIs(comparison["passed"], False)
        self.assertIs(comparison["scope_unchanged"], True)
        self.assertIs(comparison["root_availability_unchanged"], False)
        for key in ("added", "removed", "changed"):
            self.assertEqual(comparison[key], [])
        self.assertEqual(comparison["before_totals"], initial["totals"])
        self.assertEqual(comparison["after_totals"], initial["totals"])


if __name__ == "__main__":
    unittest.main()
