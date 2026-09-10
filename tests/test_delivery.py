import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

from expgym import delivery


REPO = Path(__file__).resolve().parents[1]


class DeliveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="expgym-delivery-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "source"
        self.root.mkdir()
        (self.root / "nested").mkdir()
        (self.root / "nested/trace.json").write_text('{"score": 0, "status": "missing"}\n')
        (self.root / "analysis.csv").write_text("metric,value\nf1,0\n")
        self.names = ["nested/trace.json", "analysis.csv"]
        self.out = self.base / "sealed"

    def seal(self, **kwargs):
        return delivery.seal(self.root, self.names, self.out, **kwargs)

    def scanner(self):
        keys = []
        for number in range(4):
            path = self.base / ("fake-source-%s" % number)
            path.write_text("fixture-only-token-value-%s" % number)
            keys.append(path)
        return delivery.OriginalScanner(REPO / "tools/publication/validate_bundle_v2.py", keys)

    def replace_archive(self, manifest, members):
        path = self.out / "part-000001.tar.gz"
        with tarfile.open(path, "w:gz") as archive:
            for name, payload, kind in members:
                info = tarfile.TarInfo(name)
                info.type = kind
                info.size = len(payload) if kind == tarfile.REGTYPE else 0
                if kind == tarfile.SYMTYPE:
                    info.linkname = "../../outside"
                archive.addfile(info, io.BytesIO(payload) if info.isfile() else None)
        raw = path.read_bytes()
        manifest["archives"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
        manifest["archives"][0]["bytes"] = len(raw)

    def test_roundtrip_and_default_no_extraction(self):
        manifest = self.seal()
        result = delivery.verify(self.out, manifest)
        self.assertEqual(result["restored_files"], 0)
        self.assertEqual(set(p.name for p in self.out.iterdir()), {"part-000001.tar.gz", "manifest.json"})
        restored = self.base / "restored"
        result = delivery.verify(self.out, manifest,
                                 restore_dir=restored, selected=["analysis.csv"])
        self.assertEqual(result["restored_files"], 1)
        self.assertEqual((restored / "analysis.csv").read_bytes(), (self.root / "analysis.csv").read_bytes())
        self.assertFalse((restored / "nested").exists())

    def test_deterministic_archive_and_manifest(self):
        first = self.seal()
        other = self.base / "again"
        second = delivery.seal(self.root, list(reversed(self.names)), other)
        self.assertEqual(first, second)
        self.assertEqual((self.out / "part-000001.tar.gz").read_bytes(), (other / "part-000001.tar.gz").read_bytes())

    def test_path_and_secret_path_rejection(self):
        for name in ("../x", "/x", "a//x", "a/./x", "a\\x", "a/../x", "a\nx",
                     "private/token", ".env", "nested/.env.prod", "router_api_key", "keys.pem", "weights/a"):
            with self.subTest(name=name), self.assertRaises(delivery.DeliveryError):
                delivery.validate_paths([name])

    def test_duplicate_and_prefix_paths(self):
        for names in (["a", "a"], ["a", "a/b"], []):
            with self.assertRaises(delivery.DeliveryError):
                delivery.validate_paths(names)

    def test_symlink_leaf_and_parent_rejected(self):
        (self.root / "alias.json").symlink_to(self.root / "analysis.csv")
        (self.root / "alias").symlink_to(self.root / "nested", target_is_directory=True)
        for number, name in enumerate(("alias.json", "alias/trace.json")):
            with self.assertRaises(OSError):
                delivery.seal(self.root, [name], self.base / ("link-%s" % number))

    def test_fifo_rejected_without_blocking(self):
        os.mkfifo(self.root / "pipe")
        with self.assertRaises(delivery.DeliveryError):
            delivery.seal(self.root, ["pipe"], self.out)

    def test_no_overwrite(self):
        manifest = self.seal()
        with self.assertRaises(FileExistsError):
            self.seal()
        restored = self.base / "existing"
        restored.mkdir()
        with self.assertRaises(FileExistsError):
            delivery.verify(self.out, manifest,
                            restore_dir=restored, selected=self.names)

    def test_changed_source_rejected_without_manifest(self):
        addfile = tarfile.TarFile.addfile

        def mutate(archive, info, fileobj=None):
            result = addfile(archive, info, fileobj)
            (self.root / info.name).write_bytes(b"changed")
            return result

        with mock.patch.object(tarfile.TarFile, "addfile", mutate), self.assertRaises(delivery.DeliveryError):
            self.seal()
        self.assertFalse((self.out / "manifest.json").exists())
        self.assertEqual(stat.S_IMODE(self.out.stat().st_mode), 0o700)

    def test_changed_previous_source_detected_by_final_metadata_fence(self):
        addfile = tarfile.TarFile.addfile

        def mutate(archive, info, fileobj=None):
            result = addfile(archive, info, fileobj)
            if info.name == "nested/trace.json":
                (self.root / "analysis.csv").write_text("late change")
            return result

        with mock.patch.object(tarfile.TarFile, "addfile", mutate), self.assertRaises(delivery.DeliveryError):
            self.seal()

    def test_outer_hash_mismatch(self):
        manifest = self.seal()
        manifest["archives"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(delivery.DeliveryError, "archive_bytes_mismatch"):
            delivery.verify(self.out, manifest)

    def test_inner_hash_mismatch_even_when_outer_hash_updated(self):
        manifest = self.seal()
        row = manifest["files"][0]
        members = [(r["path"], b"x" * r["bytes"], tarfile.REGTYPE) for r in manifest["files"]]
        self.replace_archive(manifest, members)
        with self.assertRaisesRegex(delivery.DeliveryError, "member_bytes_mismatch"):
            delivery.verify(self.out, manifest)

    def test_duplicate_missing_traversal_and_link_archive_members(self):
        original = self.seal()
        members = [(name, (self.root / name).read_bytes(), tarfile.REGTYPE) for name in sorted(self.names)]
        for invalid in (members + [members[0]], members[:1],
                        [("../escape", b"", tarfile.REGTYPE)],
                        [(members[0][0], b"", tarfile.SYMTYPE)]):
            with self.subTest(members=[r[0] for r in invalid]):
                manifest = copy.deepcopy(original)
                self.replace_archive(manifest, invalid)
                with self.assertRaises(delivery.DeliveryError):
                    delivery.verify(self.out, manifest)

    def test_unselected_corruption_still_rejected(self):
        manifest = self.seal()
        manifest["files"][1]["sha256"] = "0" * 64
        with self.assertRaises(delivery.DeliveryError):
            delivery.verify(self.out, manifest,
                            restore_dir=self.base / "partial", selected=["analysis.csv"])

    def test_payload_reads_are_bounded(self):
        path = self.root / "large.txt"
        path.write_bytes(b"a" * (delivery.BLOCK * 3 + 17))
        self.names.append("large.txt")
        original = delivery.HashStream.read
        observed = []

        def bounded(reader, size=-1):
            observed.append(size)
            self.assertGreaterEqual(size, 0)
            self.assertLessEqual(size, delivery.BLOCK)
            return original(reader, size)

        with mock.patch.object(delivery.HashStream, "read", bounded):
            manifest = self.seal()
            delivery.verify(self.out, manifest)
        self.assertTrue(observed)

    def test_local_is_not_public_clearance(self):
        manifest = self.seal()
        with self.assertRaisesRegex(delivery.DeliveryError, "local_only_not_publishable"):
            delivery.verify(self.out, manifest, require_public_scan=True)

    def test_original_scanner_public_pass_and_core_disabled(self):
        scanner = self.scanner()
        manifest = self.seal(scanner=scanner)
        result = delivery.verify(self.out, manifest, require_public_scan=True)
        self.assertTrue(result["public_scan_declaration"])
        self.assertEqual(manifest["security"]["known_secret_sources"], 4)
        self.assertEqual(delivery.resource.getrlimit(delivery.resource.RLIMIT_CORE), (0, 0))

    def test_original_scanner_rejects_known_value_and_credential_metadata(self):
        scanner = self.scanner()
        for number, payload in enumerate((b'{"note":"fixture-only-token-value-0"}',
                                          b'{"authorization":"a narrative, not an actual key"}',
                                          b'\xff\xfe', b'{"bad json"')):
            (self.root / "nested/trace.json").write_bytes(payload)
            out = self.base / ("rejected-%s" % number)
            with self.assertRaisesRegex(delivery.DeliveryError, "original_security_policy_rejected_payload"):
                delivery.seal(self.root, self.names, out, scanner)
            self.assertFalse((out / "manifest.json").exists())

    def test_compressed_known_value_boundary_check(self):
        output = io.BytesIO()
        stream = delivery.HashStream(output, forbidden=[b"fixture-only-token"])
        stream.write(b"prefix fixture-only-")
        with self.assertRaises(delivery.DeliveryError):
            stream.write(b"token suffix")

    def test_scanner_identity_and_four_sources_required(self):
        with self.assertRaises(delivery.DeliveryError):
            delivery.OriginalScanner(REPO / "tools/publication/validate_bundle_v2.py", [])
        fake = self.base / "scanner.py"
        fake.write_text("raise RuntimeError('must not execute')")
        with self.assertRaisesRegex(delivery.DeliveryError, "scanner_identity_mismatch"):
            delivery.OriginalScanner(fake, [self.base / str(i) for i in range(4)])

    def test_duplicate_json_keys_and_malformed_inventory(self):
        path = self.base / "invalid.json"
        path.write_text('{"x": 1, "x": 2}')
        with self.assertRaises(delivery.DeliveryError):
            delivery.read_json(path)
        manifest = self.seal()
        manifest["files"][0]["bytes"] = True
        with self.assertRaises(delivery.DeliveryError):
            delivery.verify(self.out, manifest)

    def test_automatic_multi_shard_global_manifest(self):
        manifest = self.seal(shard_files=1)
        self.assertEqual(len(manifest["archives"]), 2)
        self.assertEqual([row["archive"] for row in manifest["files"]],
                         ["part-000001.tar.gz", "part-000002.tar.gz"])
        result = delivery.verify(self.out, manifest, restore_dir=self.base / "all-small-fixture",
                                 selected=self.names)
        self.assertEqual((result["archives"], result["restored_files"]), (2, 2))
        for name in self.names:
            self.assertEqual((self.base / "all-small-fixture" / name).read_bytes(),
                             (self.root / name).read_bytes())

    def test_byte_limit_auto_shards_and_public_scan(self):
        manifest = self.seal(shard_bytes=1, scanner=self.scanner())
        self.assertEqual(len(manifest["archives"]), 2)
        self.assertTrue(delivery.verify(self.out, manifest, require_public_scan=True)["passed"])

    def test_cross_shard_duplicate_prefix_and_wrong_assignment(self):
        original = self.seal(shard_files=1)
        for new_name in ("analysis.csv", "analysis.csv/child"):
            manifest = copy.deepcopy(original)
            manifest["files"][1]["path"] = new_name
            with self.assertRaises(delivery.DeliveryError):
                delivery.verify(self.out, manifest)
        manifest = copy.deepcopy(original)
        manifest["files"][0]["archive"], manifest["files"][1]["archive"] = (
            manifest["files"][1]["archive"], manifest["files"][0]["archive"])
        with self.assertRaisesRegex(delivery.DeliveryError, "member_in_wrong_archive"):
            delivery.verify(self.out, manifest)

    def test_nonselected_shard_corruption_is_checked(self):
        manifest = self.seal(shard_files=1)
        manifest["archives"][1]["sha256"] = "0" * 64
        with self.assertRaises(delivery.DeliveryError):
            delivery.verify(self.out, manifest, restore_dir=self.base / "partial-selection",
                            selected=["analysis.csv"])

    def test_gzip_crc_footer_and_hidden_trailing_archives_rejected(self):
        original = self.seal()
        path = self.out / "part-000001.tar.gz"
        compressed = path.read_bytes()
        tar_bytes = gzip.decompress(compressed)
        extra = io.BytesIO()
        with tarfile.open(fileobj=extra, mode="w") as archive:
            info = tarfile.TarInfo("hidden.txt")
            info.size = 6
            archive.addfile(info, io.BytesIO(b"hidden"))
        crc = bytearray(compressed)
        crc[-8] ^= 1
        cases = [bytes(crc), compressed[:-8],
                 gzip.compress(tar_bytes + extra.getvalue()),
                 compressed + gzip.compress(extra.getvalue()),
                 gzip.compress(tar_bytes + b"nonzero trailing garbage"),
                 compressed + b"not another gzip"]
        for number, invalid in enumerate(cases):
            with self.subTest(case=number):
                path.write_bytes(invalid)
                manifest = copy.deepcopy(original)
                manifest["archives"][0].update(bytes=len(invalid), sha256=hashlib.sha256(invalid).hexdigest())
                with self.assertRaises((delivery.DeliveryError, OSError, EOFError, tarfile.TarError)):
                    delivery.verify(self.out, manifest)

    def test_pax_long_relative_path_is_preserved(self):
        folder = "l" * 105
        (self.root / folder).mkdir()
        name = folder + "/trace.json"
        (self.root / name).write_text("{}")
        manifest = delivery.seal(self.root, [name], self.out)
        result = delivery.verify(self.out, manifest)
        self.assertTrue(result["passed"])
        self.assertEqual(manifest["files"][0]["path"], name)

    def test_cli_small_fixture(self):
        file_list = self.base / "files.json"
        file_list.write_text(json.dumps(self.names))
        script = str(REPO / "scripts/package_run.py")
        subprocess.run([sys.executable, "-B", script, "seal", "--root", str(self.root),
                        "--files", str(file_list), "--output-dir", str(self.out), "--local-only"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = subprocess.run([sys.executable, "-B", script, "verify", "--manifest", str(self.out / "manifest.json"),
                                 "--archive-dir", str(self.out)],
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(json.loads(result.stdout)["restored_files"], 0)


if __name__ == "__main__":
    unittest.main()
