"""Bounded synthetic contracts; no model, raw archive, or network access."""
import copy
import hashlib
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_archive_index as subject


def artifact(path, size=1):
    return {"url": subject.link("a" * 40, path), "repo_path": path,
            "bytes": size, "sha256": "b" * 64}


def legacy_fixture():
    models = {}
    for model in subject.MODELS[:2]:
        base = model + "/"
        totals = {"bundles": 1, "tar_shards": 1, "original_files": 2,
                  "original_bytes": 8, "compressed_bytes": 4}
        models[model] = {
            "collection_index": artifact(base + "collection.json"),
            "totals": totals,
            "bundles": [{**totals, "index": artifact(base + "INDEX.json"),
                         "shards": [{"archive": artifact(base + "one.tar.gz", 4),
                                     "member_inventory": artifact(base + "members.json"),
                                     "original_files": 2, "original_bytes": 8}]}],
            "analysis_exports": [{"name": name, "role": "fixture",
                                  "artifact": artifact(base + name)}
                                 for name in ("metrics.csv", "effects.csv", "paired_rows.csv",
                                              "source_index.json", "EXPORT_INDEX.json")],
            "navigation": [], "analysis_python": "CPython fixture"}
    return {"schema": "expgym-public-formal-archive-index-v1",
            "input_commit": subject.PINS["legacy"]["data_commit"], "models": models,
            "totals": {k: 2 * v for k, v in totals.items()},
            "scope": {"k3_old34_counted_once": True, "limits": ["fixture controls limit"]},
            "restore_and_relocation_tools": [],
            "shared_report_and_costs": [{"name": "成稿后独立科学复核", "artifact": artifact("review.md")} ]}


def current_fixture(key="qwen"):
    qwen = key == "qwen"
    analysis = "analysis/full_v1/" if qwen else "analysis/full_v2/"
    return {"schema": "qwen38.archive-index.v1" if qwen else "deepseek-flash.archive-index.v1",
            "model": subject.MODELS[2 if qwen else 3],
            "data": {"commit": subject.PINS[key]["data_commit"]},
            "manifest": {**artifact(key + "/manifest.json"), "schema": "expgym.delivery.v1"},
            "totals": {"global_manifests": 1, "shards": 1, "members": 2,
                       "member_original_bytes": 8, "shard_compressed_bytes": 4,
                       "outer_attachments": 11, "outer_attachment_bytes": 11,
                       "outer_member_copies": 0, "outer_member_copy_bytes": 0},
            "archives": [{**artifact(key + "/one.tar.gz", 4), "path": "one.tar.gz",
                          "members": 2, "original_bytes": 8}],
            "member_roles": [{"members": 2, "original_bytes": 8}],
            "outer_attachments": [{**artifact(key + "/" + analysis + str(i)),
                                   "path": analysis + str(i), "description": "fixture"} for i in range(11)],
            "attachment_inventory": artifact(key + "/attachments.json"),
            "restore": {"analyzer_arbitrary_root_relocation_supported": False,
                        "original_analysis_replay_requires_frozen_absolute_layout": True,
                        "source_commit": "a" * 40,
                        "package_run": subject.link("a" * 40, "scripts/package_run.py"),
                        "delivery": subject.link("a" * 40, "expgym/delivery.py")}}


class ContractTests(unittest.TestCase):
    def test_legacy_fixture_sums(self):
        result = subject.legacy_models(legacy_fixture())
        self.assertEqual([m["counts"]["original_files"] for m in result], [2, 2])

    def test_legacy_wrong_count_rejected(self):
        source = legacy_fixture()
        source["models"]["kimi-k3"]["bundles"][0]["original_files"] += 1
        with self.assertRaisesRegex(ValueError, "bundle original_files"):
            subject.legacy_models(source)

    def test_duplicate_physical_tar_rejected(self):
        source = legacy_fixture()
        source["models"]["glm-5.3"]["bundles"][0]["shards"][0]["archive"] = copy.deepcopy(
            source["models"]["kimi-k3"]["bundles"][0]["shards"][0]["archive"])
        with self.assertRaisesRegex(ValueError, "duplicate physical"):
            subject.legacy_models(source)

    def test_duplicate_model_rejected(self):
        models = [{"model": x, "counts": {k: 0 for k in subject.COUNTS}} for x in subject.MODELS]
        models[-1]["model"] = models[0]["model"]
        with self.assertRaisesRegex(ValueError, "duplicate model"):
            subject.validate_model_set(models)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            json.loads('{"kimi-k3":1,"kimi-k3":2}', object_pairs_hook=subject.no_duplicates)

    def test_moving_and_wrong_origin_urls_rejected(self):
        for url in (subject.REPO + "/blob/main/data.json",
                    "https://example.org/blob/" + "a" * 40 + "/data.json",
                    subject.REPO + "/blob/" + "a" * 40 + "/../data.json"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                subject.fixed_url(url)

    def test_tampered_sha_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "fixture"
            source.write_bytes(b"fixture")
            digest = hashlib.sha256(b"fixture").hexdigest()
            self.assertEqual(subject.read_bound(source, digest)[1]["bytes"], 7)
            source.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "input SHA256 mismatch"):
                subject.read_bound(source, digest)

    def test_noninteger_counts_rejected(self):
        for value in (-1, True, 1.5, "1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                subject.nonnegative(value)

    def test_current_fixture_and_wrong_counts(self):
        source = current_fixture()
        result = subject.current_model(source, "qwen", subject.MODELS[2], subject.LABELS[2])
        self.assertEqual(result["counts"]["single_manifest_collections"], 1)
        source["totals"]["members"] += 1
        with self.assertRaisesRegex(ValueError, "shard totals"):
            subject.current_model(source, "qwen", subject.MODELS[2], subject.LABELS[2])

    def test_attachment_copy_count_rejected(self):
        source = current_fixture()
        source["totals"]["outer_member_copies"] = 1
        with self.assertRaisesRegex(ValueError, "attachment copy"):
            subject.current_model(source, "qwen", subject.MODELS[2], subject.LABELS[2])

    def test_relocation_claim_rejected(self):
        source = current_fixture()
        source["restore"]["analyzer_arbitrary_root_relocation_supported"] = True
        with self.assertRaisesRegex(ValueError, "replay capability"):
            subject.current_model(source, "qwen", subject.MODELS[2], subject.LABELS[2])

    def test_cli_check_is_read_only_and_detects_output_change(self):
        fixtures = {"legacy": legacy_fixture(), "qwen": current_fixture(),
                    "deepseek": current_fixture("deepseek")}
        pins = copy.deepcopy(subject.PINS)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = ["--output-dir", str(root / "output")]
            for key, source in fixtures.items():
                for arg, suffix, payload in (("index", "json", json.dumps(source).encode()),
                                             ("guide", "md", b"fixture guide\n")):
                    path = root / (key + "." + suffix)
                    path.write_bytes(payload)
                    pins[key][suffix + "_sha256"] = hashlib.sha256(payload).hexdigest()
                    args.extend([f"--{key}-{arg}", str(path)])
            with patch.object(subject, "PINS", pins), redirect_stdout(io.StringIO()):
                subject.main(args)
                paths = list((root / "output").iterdir())
                before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in paths}
                subject.main(args + ["--check"])
                self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in paths})
                paths[0].write_bytes(b"modified output")
                with self.assertRaisesRegex(ValueError, "output differs"):
                    subject.main(args + ["--check"])
                self.assertEqual(paths[0].read_bytes(), b"modified output")


if __name__ == "__main__":
    unittest.main()
