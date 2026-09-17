#!/usr/bin/env python3
"""Portable synthetic tests: no experiment payloads or original workspace needed."""
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("find_record", Path(__file__).with_name("find_record.py"))
finder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(finder)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class FindRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="expgym-find-record-")
        self.root = Path(self.tmp.name) / "relocated-delivery"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def fixture(self, *, legacy=False, fallback=False, tampered=False, unsafe=False, link=False):
        payload = b'{"synthetic":true}\n'
        member = "run/api_dump/request.json"
        tar_member = ("data/" if legacy else "") + member
        archive = self.root / "raw_archives/test/part-000001.tar.gz"
        archive.parent.mkdir(parents=True)
        with tarfile.open(archive, "w:gz") as handle:
            info = tarfile.TarInfo(tar_member)
            body = b'{"synthetic":True}\n' if tampered else payload
            if link:
                info.type = tarfile.SYMTYPE
                info.linkname = "/outside/secret"
                handle.addfile(info)
            else:
                info.size = len(body)
                handle.addfile(info, io.BytesIO(body))
            extra = tarfile.TarInfo("run/api_dump-neighbor/not-selected.json")
            extra.size = 3
            handle.addfile(extra, io.BytesIO(b"{}\n"))
        row = dict(cohort_id="cohort", archive_file="raw_archives/test/part-000001.tar.gz",
                   member_path=member, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
                   original_path="/old/run/api_dump/" + ("../escape.json" if unsafe else "request.json"))
        if not fallback:
            row["tar_member_path"] = tar_member
        else:
            row["source_id"] = row.pop("cohort_id")
        write_csv(self.root / "raw_archives/MEMBERS.csv", [row])
        slot = dict(slot_id="s1", model="test-model", system="expgym", scenario="restricted_search",
                    regime="cost_tight", strategy="single", item="q1", cohort_id="cohort",
                    api_dump_root="/old/run/api_dump", dump_member_table="raw_archives/MEMBERS.csv",
                    dump_member_count="1", dump_bytes=str(len(payload)), trajectory_file="trajectories/s1.json",
                    report_commit="fixed", status="completed")
        write_csv(self.root / "index/selected_slots.csv", [slot])
        return slot, payload

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return finder.main(list(args), root=self.root)

    def test_listing_is_portable_and_payload_free(self):
        self.fixture()
        result = self.call("--model", "test-model", "--regime", "cost_tight")
        self.assertEqual(result["matched_slots"], 1)
        self.assertNotIn("synthetic", json.dumps(result))
        self.assertEqual(result["slots"][0]["trajectory_file"], "trajectories/s1.json")
        self.assertEqual(self.call("--model", "absent")["matched_slots"], 0)

    def test_modern_explicit_tar_name(self):
        _, payload = self.fixture()
        listed = self.call("--slot", "s1", "--dump-members")
        self.assertEqual(listed["total_members"], 1)
        out = self.root.parent / "restored"
        result = self.call("--slot", "s1", "--restore-dumps", "--output", str(out))
        self.assertEqual(result["restored_files"], 1)
        self.assertEqual((out / "files/request.json").read_bytes(), payload)
        self.assertTrue((out / "RESTORED_MANIFEST.json").is_file())
        self.assertFalse((out / ".incomplete").exists())

    def test_gemini_modern_fallback(self):
        self.fixture(fallback=True)
        result = self.call("--slot", "s1", "--restore-dumps", "--output", str(self.root.parent / "restored"))
        self.assertEqual(result["status"], "PASS")

    def test_legacy_data_prefix(self):
        self.fixture(legacy=True)
        result = self.call("--slot", "s1", "--restore-dumps", "--output", str(self.root.parent / "restored"))
        self.assertEqual(result["status"], "PASS")

    def test_tampered_payload_cannot_get_success_manifest(self):
        self.fixture(tampered=True)
        out = self.root.parent / "restored"
        with self.assertRaises(finder.RecordError):
            self.call("--slot", "s1", "--restore-dumps", "--output", str(out))
        self.assertFalse((out / "RESTORED_MANIFEST.json").exists())
        self.assertTrue((out / "RESTORE_FAILED.json").is_file())

    def test_unsafe_output_relative_rejected_before_create(self):
        self.fixture(unsafe=True)
        out = self.root.parent / "restored"
        with self.assertRaises(finder.RecordError):
            self.call("--slot", "s1", "--restore-dumps", "--output", str(out))
        self.assertFalse(out.exists())

    def test_tar_symlink_rejected(self):
        self.fixture(link=True)
        out = self.root.parent / "restored"
        with self.assertRaises(finder.RecordError):
            self.call("--slot", "s1", "--restore-dumps", "--output", str(out))
        self.assertFalse((out / "files/request.json").exists())

    def test_existing_output_not_overwritten(self):
        self.fixture()
        out = self.root.parent / "existing"
        out.mkdir()
        sentinel = out / "keep"
        sentinel.write_bytes(b"keep")
        with self.assertRaises(finder.RecordError):
            self.call("--slot", "s1", "--restore-dumps", "--output", str(out))
        self.assertEqual(sentinel.read_bytes(), b"keep")

    def test_archive_symlink_rejected(self):
        self.fixture()
        archive = self.root / "raw_archives/test/part-000001.tar.gz"
        replacement = archive.with_name("actual.tar.gz")
        archive.rename(replacement)
        archive.symlink_to(replacement.name)
        out = self.root.parent / "restored"
        with self.assertRaises(finder.RecordError):
            self.call("--slot", "s1", "--restore-dumps", "--output", str(out))
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
