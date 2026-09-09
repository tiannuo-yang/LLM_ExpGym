"""Synthetic-only tests of the minimally rebound outer metadata preparer."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("glm_outer_metadata_candidate", HERE / "prepare_metadata.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DECLARED_COUNT = sum(len(items) for items in MODULE.groups.values())

class OuterMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="glm-outer-cpu-")
        self.base = Path(self.tmp.name)
        self.originals = {key: getattr(MODULE, key) for key in ("W", "OUT", "LEAF", "groups", "PINS", "hashed")}
        self.input = self.base / "inputs"; self.input.mkdir()
        self.output = self.base / "out"; self.output.mkdir()
        self.paths = []
        for n in range(DECLARED_COUNT):
            path = self.input / ("file-%06d.json" % n)
            path.write_bytes(('{"synthetic":%d}\n' % n).encode())
            self.paths.append(path)
        MODULE.W, MODULE.OUT, MODULE.LEAF = self.base, self.output, "synthetic/cpu-only"
        MODULE.groups = {"synthetic": self.paths}
        MODULE.PINS = {self.paths[0]: hashlib.sha256(self.paths[0].read_bytes()).hexdigest()}

    def tearDown(self):
        for key, value in self.originals.items():
            setattr(MODULE, key, value)
        self.tmp.cleanup()

    def run_main(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            MODULE.main()
        return json.loads(stdout.getvalue())

    def assert_no_products(self):
        self.assertFalse((self.output / "FILES.candidate.json").exists())
        self.assertFalse((self.output / "HASH_RECEIPT.json").exists())

    def test_success_exact_scope_two_full_hashes(self):
        original = MODULE.hashed
        calls = []
        def counted(path):
            calls.append(path)
            return original(path)
        MODULE.hashed = counted
        result = self.run_main()
        self.assertTrue(result["passed"])
        self.assertEqual(len(calls), 2 * DECLARED_COUNT)
        manifest = json.loads((self.output / "FILES.candidate.json").read_bytes())
        receipt = json.loads((self.output / "HASH_RECEIPT.json").read_bytes())
        self.assertIs(manifest["approved"], False)
        self.assertIs(manifest["original_execution_complete"], True)
        self.assertIs(manifest["original_score_complete"], True)
        self.assertEqual(manifest["file_count"], DECLARED_COUNT)
        self.assertEqual(receipt["full_hash_passes"], 2)
        self.assertIs(receipt["stable_stat_and_all_bytes_equal"], True)
        for row in manifest["files"]:
            raw = Path(row["source_path"]).read_bytes()
            self.assertEqual((row["bytes"], row["sha256"]), (len(raw), hashlib.sha256(raw).hexdigest()))
            self.assertEqual(row["target_path"], "evidence/workspace/" + Path(row["source_path"]).relative_to(self.base).as_posix())

    def test_existing_manifest_is_not_overwritten(self):
        destination = self.output / "FILES.candidate.json"
        destination.write_bytes(b"preserve-synthetic-existing")
        with self.assertRaisesRegex(ValueError, "refuse_existing_output"):
            self.run_main()
        self.assertEqual(destination.read_bytes(), b"preserve-synthetic-existing")
        self.assertFalse((self.output / "HASH_RECEIPT.json").exists())

    def test_duplicate_scope_rejected_before_hashing(self):
        MODULE.groups = {"synthetic": [self.paths[0], *self.paths[:-1]]}
        with self.assertRaisesRegex(ValueError, "exact_scope_or_duplicate"):
            self.run_main()
        self.assert_no_products()

    def test_missing_scope_rejected(self):
        MODULE.groups = {"synthetic": self.paths[:-1]}
        with self.assertRaisesRegex(ValueError, "exact_scope_or_duplicate"):
            self.run_main()
        self.assert_no_products()

    def test_pin_outside_scope_rejected(self):
        MODULE.PINS[self.base / "unselected"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "pin_outside_scope"):
            self.run_main()
        self.assert_no_products()

    def test_wrong_sha_pin_rejected(self):
        MODULE.PINS[self.paths[0]] = "0" * 64
        with self.assertRaisesRegex(ValueError, "external_pin_changed"):
            self.run_main()
        self.assert_no_products()

    def test_symlink_rejected(self):
        target = self.input / "outside-enumeration.json"
        target.write_bytes(b"synthetic-target")
        self.paths[-1].unlink()
        self.paths[-1].symlink_to(target)
        with self.assertRaisesRegex(ValueError, "noncanonical_source"):
            self.run_main()
        self.assert_no_products()

    def test_second_full_hash_detects_content_change(self):
        original = MODULE.hashed
        calls = 0
        target = self.paths[-1]
        def mutate_after_first_pass(path):
            nonlocal calls
            value = original(path)
            calls += 1
            if calls == DECLARED_COUNT:
                target.write_bytes(b"synthetic-content-changed")
            return value
        MODULE.hashed = mutate_after_first_pass
        with self.assertRaisesRegex(ValueError, "second_full_hash_or_stat_changed"):
            self.run_main()
        self.assert_no_products()

    def test_second_pass_detects_stat_only_change(self):
        original = MODULE.hashed
        calls = 0
        target = self.paths[-1]
        def change_mode_after_first_pass(path):
            nonlocal calls
            value = original(path)
            calls += 1
            if calls == DECLARED_COUNT:
                target.chmod(0o600)
            return value
        # Files are created with the process umask; force a known different initial mode.
        target.chmod(0o644)
        MODULE.hashed = change_mode_after_first_pass
        with self.assertRaisesRegex(ValueError, "second_full_hash_or_stat_changed"):
            self.run_main()
        self.assert_no_products()

if __name__ == "__main__":
    unittest.main()

