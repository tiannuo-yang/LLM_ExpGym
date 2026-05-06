"""Tests for scripts/download_data.py — only the network-free pieces.

We don't actually hit HuggingFace or GitHub from the unit tests; we just
verify the layout-detection logic. The real download is exercised by
running the script by hand.
"""
import importlib.util
import os
import sys
import tempfile
import unittest


# Load the script as a module without polluting sys.path permanently.
_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "download_data.py",
)
_spec = importlib.util.spec_from_file_location("download_data", _SCRIPT_PATH)
download_data = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(download_data)


class CheckOnlyNoNetworkTest(unittest.TestCase):
    """In --check mode the helpers must never touch the network."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_env = {
            "EXPGYM_DATA_ROOT": os.environ.get("EXPGYM_DATA_ROOT"),
            "PHANTOM_WIKI_ROOT": os.environ.get("PHANTOM_WIKI_ROOT"),
        }
        os.environ["EXPGYM_DATA_ROOT"] = os.path.join(self._tmp, "data")
        os.environ["PHANTOM_WIKI_ROOT"] = os.path.join(self._tmp, "data", "phantom-wiki")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)
        for k, v in self._old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_phantom_wiki_check_reports_missing(self):
        ok, msg = download_data.fetch_phantom_wiki(check_only=True)
        self.assertFalse(ok)
        self.assertIn("MISSING", msg)
        self.assertIn("phantom-wiki", msg)

    def test_contract_nli_check_reports_missing_and_lists_files(self):
        ok, msg = download_data.fetch_contract_nli(check_only=True)
        self.assertFalse(ok)
        self.assertIn("MISSING", msg)
        # Both expected files must appear in the instructions.
        for fname in download_data.CONTRACT_NLI_FILES:
            self.assertIn(fname, msg)

    def test_phantom_wiki_check_succeeds_when_dirs_exist(self):
        snap = download_data._phantom_wiki_snapshot_dir()
        os.makedirs(os.path.join(snap, "question-answer"), exist_ok=True)
        os.makedirs(os.path.join(snap, "text-corpus"), exist_ok=True)
        ok, msg = download_data.fetch_phantom_wiki(check_only=True)
        self.assertTrue(ok, msg)
        self.assertIn("already present", msg)

    def test_contract_nli_check_succeeds_when_files_exist(self):
        target = os.path.join(os.environ["EXPGYM_DATA_ROOT"], "contract-nli")
        os.makedirs(target, exist_ok=True)
        for f in download_data.CONTRACT_NLI_FILES:
            with open(os.path.join(target, f), "w") as h:
                h.write("{}")
        ok, msg = download_data.fetch_contract_nli(check_only=True)
        self.assertTrue(ok, msg)
        self.assertIn("already present", msg)


class StepsRegistrationTest(unittest.TestCase):
    """The driver must enumerate all three datasets."""

    def test_three_steps_registered(self):
        names = [name for name, _ in download_data.STEPS]
        self.assertEqual(set(names), {"Phantom Wiki", "HPOBench", "ContractNLI"})


if __name__ == "__main__":
    unittest.main()
