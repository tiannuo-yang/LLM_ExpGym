"""Tests for scripts/download_data.py — only the network-free pieces.

We don't actually hit HuggingFace or GitHub from the unit tests; we just
verify the layout-detection logic. The real download is exercised by
running the script by hand.
"""
import importlib.util
import hashlib
import json
import os
import shutil
import tempfile
import unittest
import zipfile


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
            download_data.CONTRACT_NLI_ARCHIVE_ENV: os.environ.get(
                download_data.CONTRACT_NLI_ARCHIVE_ENV
            ),
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
        self.assertIn(download_data.CONTRACT_NLI_PAGE, msg)
        self.assertIn("--contract-nli-archive", msg)
        # Both expected files must appear in the instructions.
        for fname in download_data.CONTRACT_NLI_FILES:
            self.assertIn(fname, msg)

    def test_contract_nli_data_links_use_official_source(self):
        msg = download_data.contract_nli_data_links()
        self.assertIn(download_data.CONTRACT_NLI_PAGE, msg)
        self.assertIn(download_data.CONTRACT_NLI_ZIP_URL, msg)
        self.assertIn("--contract-nli-archive", msg)

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

    def test_contract_nli_archive_extracts_public_test_json_name(self):
        archive = os.path.join(self._tmp, "contract-nli.zip")
        payload = {
            "documents": [
                {
                    "id": 1,
                    "text": "alpha beta",
                    "spans": [[0, 5], [6, 10]],
                    "annotation_sets": [{"annotations": {}}],
                }
            ],
            "labels": {},
        }
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("contract-nli/test.json", json.dumps(payload))
        os.environ[download_data.CONTRACT_NLI_ARCHIVE_ENV] = archive

        ok, msg = download_data.fetch_contract_nli(check_only=False)

        self.assertTrue(ok, msg)
        self.assertIn("test_segments.json", msg)
        target = os.path.join(
            os.environ["EXPGYM_DATA_ROOT"], "contract-nli", "test_segments.json"
        )
        with open(target, encoding="utf-8") as handle:
            extracted = json.load(handle)
        self.assertEqual(extracted["documents"][0]["segments"][0]["text"], "alpha")
        self.assertEqual(extracted["documents"][0]["segments"][1]["span_index"], 1)

    def test_contract_nli_auto_download_extracts_public_zip(self):
        payload = {
            "documents": [
                {
                    "id": 1,
                    "text": "alpha beta",
                    "spans": [[0, 5], [6, 10]],
                    "annotation_sets": [{"annotations": {}}],
                }
            ],
            "labels": {},
        }

        def fake_download(target_dir):
            archive = os.path.join(target_dir, "contract-nli.zip")
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("contract-nli/test.json", json.dumps(payload))
            return archive

        old_download = download_data._download_contract_nli_archive
        download_data._download_contract_nli_archive = fake_download
        try:
            ok, msg = download_data.fetch_contract_nli(check_only=False)
        finally:
            download_data._download_contract_nli_archive = old_download

        self.assertTrue(ok, msg)
        self.assertIn("downloaded", msg)
        target = os.path.join(
            os.environ["EXPGYM_DATA_ROOT"], "contract-nli", "test_segments.json"
        )
        with open(target, encoding="utf-8") as handle:
            extracted = json.load(handle)
        self.assertEqual(extracted["documents"][0]["segments"][0]["text"], "alpha")


class StepsRegistrationTest(unittest.TestCase):
    """The driver must enumerate all three datasets."""

    def test_three_steps_registered(self):
        names = [name for name, _ in download_data.STEPS]
        self.assertEqual(set(names), {"Phantom Wiki", "HPOBench", "ContractNLI"})

    def test_only_selects_requested_datasets_in_stable_order(self):
        selected = download_data._select_steps("contract-nli,phantom-wiki")
        self.assertEqual(
            [name for name, _ in selected],
            ["Phantom Wiki", "ContractNLI"],
        )

    def test_only_all_selects_every_dataset(self):
        self.assertEqual(download_data._select_steps("all"), download_data.STEPS)

    def test_only_rejects_unknown_dataset(self):
        with self.assertRaisesRegex(ValueError, "unknown dataset"):
            download_data._select_steps("phantom-wiki,nope")


class HPOBenchDataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.code_dir = os.path.join(self.tmp, "HPOBench")
        self.target_dir = os.path.join(self.tmp, "data", "Surrogates")
        self.source_dir = os.path.join(self.tmp, "offline")
        os.makedirs(self.code_dir)
        os.makedirs(self.source_dir)
        with open(os.path.join(self.code_dir, "setup.py"), "w") as handle:
            handle.write("# test fixture\n")

        self.payload = b"pinned model"
        blob_sha1 = hashlib.sha1(
            f"blob {len(self.payload)}\0".encode("ascii") + self.payload
        ).hexdigest()
        self.filename = "rf_surrogate_paramnet_test.pkl"
        self.old_files = download_data.HPOBENCH_PARAMNET_FILES
        self.old_code_dir = download_data._hpobench_dir
        self.old_target_dir = download_data._hpobench_surrogate_dir
        self.old_source_ready = download_data._hpobench_source_ready
        self.old_prepare_nasbench101 = download_data._prepare_nasbench101
        self.old_prepare_nasbench201 = download_data._prepare_nasbench201
        self.old_offline = os.environ.get(download_data.HPOBENCH_SURROGATES_DIR_ENV)
        download_data.HPOBENCH_PARAMNET_FILES = {
            self.filename: (len(self.payload), blob_sha1)
        }
        download_data._hpobench_dir = lambda: self.code_dir
        download_data._hpobench_surrogate_dir = lambda: self.target_dir
        download_data._hpobench_source_ready = lambda target, ref: True
        download_data._prepare_nasbench101 = lambda check_only: (
            True,
            "NASBench101 test fixture",
        )
        download_data._prepare_nasbench201 = lambda check_only: (
            True,
            "NASBench201 test fixture",
        )
        os.environ[download_data.HPOBENCH_SURROGATES_DIR_ENV] = self.source_dir

    def tearDown(self):
        download_data.HPOBENCH_PARAMNET_FILES = self.old_files
        download_data._hpobench_dir = self.old_code_dir
        download_data._hpobench_surrogate_dir = self.old_target_dir
        download_data._hpobench_source_ready = self.old_source_ready
        download_data._prepare_nasbench101 = self.old_prepare_nasbench101
        download_data._prepare_nasbench201 = self.old_prepare_nasbench201
        if self.old_offline is None:
            os.environ.pop(download_data.HPOBENCH_SURROGATES_DIR_ENV, None)
        else:
            os.environ[download_data.HPOBENCH_SURROGATES_DIR_ENV] = self.old_offline
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_check_requires_verified_paramnet_files(self):
        ok, message = download_data.fetch_hpobench(check_only=True)
        self.assertFalse(ok)
        self.assertIn("pinned ParamNet", message)

    def test_offline_install_is_atomic_and_verified(self):
        with open(os.path.join(self.source_dir, self.filename), "wb") as handle:
            handle.write(self.payload)

        ok, message = download_data.fetch_hpobench(check_only=False)

        self.assertTrue(ok, message)
        target = os.path.join(self.target_dir, self.filename)
        with open(target, "rb") as handle:
            self.assertEqual(handle.read(), self.payload)
        self.assertFalse(os.path.exists(target + ".download"))
        self.assertTrue(download_data.fetch_hpobench(check_only=True)[0])

    def test_checksum_failure_leaves_no_partial_file(self):
        with open(os.path.join(self.source_dir, self.filename), "wb") as handle:
            handle.write(b"wrong")

        ok, message = download_data.fetch_hpobench(check_only=False)

        self.assertFalse(ok)
        self.assertIn("checksum", message)
        target = os.path.join(self.target_dir, self.filename)
        self.assertFalse(os.path.exists(target))
        self.assertFalse(os.path.exists(target + ".download"))


class NATSConversionHelpersTest(unittest.TestCase):
    def test_architecture_maps_to_named_edge_order(self):
        architecture = (
            "|avg_pool_3x3~0|+"
            "|nor_conv_3x3~0|avg_pool_3x3~1|+"
            "|skip_connect~0|nor_conv_3x3~1|skip_connect~2|"
        )
        self.assertEqual(download_data._nats_configuration_id(architecture), "434131")

    def test_rejects_malformed_architecture(self):
        with self.assertRaisesRegex(ValueError, "unexpected NATS architecture"):
            download_data._nats_configuration_id("|none~0|")


if __name__ == "__main__":
    unittest.main()
