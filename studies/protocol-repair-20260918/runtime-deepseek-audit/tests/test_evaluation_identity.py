"""Selected-input fingerprint tests with temporary files and fake dependencies."""

from contextlib import ExitStack, contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import expgym
from expgym import compact_nasbench201
from expgym import evaluation_identity as identity
from expgym import task_evidence_audit as audit
from expgym import task_restricted_search as search
from expgym import task_tuning as tuning


class EvaluationIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="expgym-identity-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        identity._content_hash.cache_clear()
        self.addCleanup(identity._content_hash.cache_clear)

    def write(self, relative_path, contents=b"fixture data"):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        return path

    def assert_sealed(self, result):
        body = {key: value for key, value in result.items() if key != "sha256"}
        canonical = json.dumps(
            body, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(result["sha256"], hashlib.sha256(canonical).hexdigest())

    @contextmanager
    def fake_dependencies(self, *, legacy_numpy=False, legacy_forest=False):
        """Import no actual NumPy, ConfigSpace, PyArrow, or HPO dependencies."""
        numpy_core = ("numpy.core._multiarray_umath" if legacy_numpy
                      else "numpy._core._multiarray_umath")
        forest = "sklearn.ensemble.forest" if legacy_forest else "sklearn.ensemble._forest"
        module_names = (
            "numpy", numpy_core, "ConfigSpace", "ConfigSpace.configuration_space", "yaml",
            "pyarrow", "pyarrow.lib", "pyarrow.parquet", "hpobench", "hpobench.config",
            "hpobench.abstract_benchmark", "hpobench.util.data_manager",
            "hpobench.benchmarks.surrogates.paramnet_benchmark", "sklearn", forest,
            "sklearn.tree._tree", "scipy",
        )
        modules = {}
        for name in module_names:
            module = ModuleType(name)
            module.__file__ = str(self.write("dependencies/" + name + ".bin", name.encode()))
            modules[name] = module
        modules["numpy"].zeros = lambda count: [0.0] * count
        modules["numpy"].argsort = lambda values: SimpleNamespace(tolist=lambda: list(range(len(values))))
        modules["hpobench"].config_file = SimpleNamespace(
            data_dir=str(self.root / "resolved-hpobench-data"),
            config_file=str(self.root / "hpobench-user-config.json"),
        )
        versions = {name: "test-version-1" for name in (
            "numpy", "ConfigSpace", "PyYAML", "pyarrow", "hpobench", "scikit-learn", "scipy",
        )}

        def import_dependency(name):
            if name not in modules:
                raise ImportError("Unavailable test dependency: " + name)
            return modules[name]

        with ExitStack() as stack:
            importer = stack.enter_context(patch.object(
                identity.importlib, "import_module", side_effect=import_dependency,
            ))
            version = stack.enter_context(patch.object(
                identity.metadata, "version", side_effect=lambda name: versions[name],
            ))
            stack.enter_context(patch.dict(sys.modules, {"numpy": modules["numpy"]}))
            yield SimpleNamespace(modules=modules, versions=versions,
                                  importer=importer, version=version)

    @contextmanager
    def search_paths(self, seed=2):
        filename = "depth_20_size_5000_seed_{}-00000-of-00001.parquet".format(seed)
        questions = self.write("qa/" + filename, b"selected questions")
        corpus = self.write("corpus/" + filename, b"selected corpus")
        with patch.object(search, "QA_DIR", str(questions.parent)), patch.object(
            search, "CORPUS_DIR", str(corpus.parent),
        ):
            yield questions, corpus

    @contextmanager
    def hpo_paths(self):
        config = self.write("configs/hpobench_tasks.yaml", b"tasks: {}")
        oracle = self.write("data/hpo_tuning/oracle3.json", b"{}")
        with patch.object(tuning, "HPOBENCH_CONFIG_PATH", config), patch.object(
            tuning, "HPOBENCH_ROOT", str(self.root / "hpobench-source"),
        ), patch.object(sys, "path", list(sys.path)):
            yield config, oracle

    def test_builtin_has_no_external_file_reads_or_optional_dependencies(self):
        args = SimpleNamespace(scenario="tuning", tuning_task="neural_network_training")
        with patch.object(identity, "file_identity", side_effect=AssertionError("external data read")), \
                patch.object(identity, "_dependency_identity", side_effect=AssertionError("optional dependency")), \
                patch.object(Path, "open", side_effect=AssertionError("file open")):
            result = identity.evaluation_identity(args, self.root / "missing-repository")
        self.assertEqual(result["selected"], {
            "scenario": "tuning", "tuning_task": "neural_network_training",
        })
        self.assertEqual(result["files"], {})
        self.assertEqual(result["dependencies"], {})
        self.assert_sealed(result)

    def test_search_fingerprints_only_selected_seed_files_and_dependency_modules(self):
        with self.search_paths(seed=2) as (questions, corpus), self.fake_dependencies() as deps:
            # Other seeds exist but are not inputs to this selected task.
            self.write("qa/depth_20_size_5000_seed_1-00000-of-00001.parquet", b"unrelated")
            self.write("corpus/depth_20_size_5000_seed_3-00000-of-00001.parquet", b"unrelated")
            with patch.object(identity, "file_identity", wraps=identity.file_identity) as reads:
                result = identity.evaluation_identity(SimpleNamespace(
                    scenario="restricted_search", data_source="phantom_seed2", question_index=5,
                ), self.root)
        expected = {questions.resolve(), corpus.resolve()} | {
            Path(deps.modules[name].__file__).resolve()
            for name in ("pyarrow", "pyarrow.lib", "pyarrow.parquet")
        }
        self.assertEqual({Path(call.args[0]).resolve() for call in reads.call_args_list}, expected)
        self.assertEqual(result["selected"], {
            "scenario": "restricted_search", "data_source": "phantom_seed2", "question_index": 5,
        })
        self.assertEqual(result["semantics"]["filter_types"], search.SWEET_SPOT_TYPES)
        self.assertEqual(result["semantics"]["max_answer_count"], search.MAX_ANSWER_COUNT)
        self.assertEqual(set(result["dependencies"]), {"pyarrow"})
        self.assert_sealed(result)

    def test_search_default_and_item_or_filter_changes_have_distinct_identities(self):
        with self.search_paths(seed=1), self.fake_dependencies():
            args = SimpleNamespace(scenario="restricted_search", data_source=None, question_index=0)
            initial = identity.evaluation_identity(args, self.root)
            self.assertEqual(initial["selected"]["data_source"], "phantom_seed1")
            self.assertEqual(identity.evaluation_identity(args, self.root), initial)
            args.question_index = 1
            different_item = identity.evaluation_identity(args, self.root)
            with patch.object(search, "MAX_ANSWER_COUNT", search.MAX_ANSWER_COUNT + 1):
                different_filter = identity.evaluation_identity(args, self.root)
        self.assertNotEqual(initial["sha256"], different_item["sha256"])
        self.assertNotEqual(different_item["sha256"], different_filter["sha256"])

    def test_audit_uses_actual_module_resolved_paths_not_repo_or_environment_guesses(self):
        evidence = self.write("external-audit/test_segments.json", b'{"documents": []}')
        hints = self.write("bundled-fallback/test_nda_span_dims.json", b"[]")
        with patch.object(audit, "EVIDENCE_PATH", str(evidence)), patch.object(
            audit, "HINTS_PATH", str(hints),
        ), patch.dict(os.environ, {"EXPGYM_DATA_ROOT": str(self.root / "not-the-loaded-path")}), \
                patch.object(identity, "_dependency_identity", side_effect=AssertionError("unexpected import")):
            result = identity.evaluation_identity(SimpleNamespace(
                scenario="evidence_audit", question_index=3, cc_split="cc-small",
                hypothesis_order="shuffle_9",
            ), self.root / "unrelated-repository")
        self.assertEqual(result["files"], {
            "evidence": identity.file_identity(evidence), "hints": identity.file_identity(hints),
        })
        self.assertEqual(result["selected"], {
            "scenario": "evidence_audit", "question_index": 3, "cc_split": "cc-small",
            "hypothesis_order": "shuffle_9",
        })
        self.assertEqual(result["dependencies"], {})
        self.assertEqual(result["semantics"]["evidence_scoring_protocol"], audit.EVIDENCE_SCORING_PROTOCOL)
        self.assert_sealed(result)

    def test_nas201_uses_selected_compact_table_and_optional_manifest(self):
        table = self.write("compact201/cifar100.pkl", b"compact selected table")
        self.write("compact201/cifar10-valid.pkl", b"unrelated table")
        args = SimpleNamespace(scenario="tuning", tuning_task="hpobench:nasbench201:cifar100")
        with self.hpo_paths() as (config, oracle), self.fake_dependencies(), patch.object(
            compact_nasbench201, "default_data_dir", return_value=table.parent,
        ):
            initial = identity.evaluation_identity(args, self.root)
            self.assertEqual(set(initial["files"]), {
                "task_configuration", "budget_oracle", "table", "table_manifest", "decoder_source",
            })
            self.assertEqual(initial["files"]["table"], identity.file_identity(table))
            self.assertEqual(initial["files"]["task_configuration"], identity.file_identity(config))
            self.assertEqual(initial["files"]["budget_oracle"], identity.file_identity(oracle))
            self.assertEqual(initial["files"]["table_manifest"], {
                "path": str(table.parent / "manifest.json"), "present": False,
            })
            manifest = self.write("compact201/manifest.json", b'{"source":"fixture"}')
            with_manifest = identity.evaluation_identity(args, self.root)
        self.assertEqual(with_manifest["files"]["table_manifest"], identity.file_identity(manifest))
        self.assertNotEqual(initial["sha256"], with_manifest["sha256"])
        self.assertEqual(set(initial["dependencies"]), {"numpy", "ConfigSpace", "PyYAML"})
        self.assert_sealed(initial)
        self.assert_sealed(with_manifest)

    def test_nas101_compact_table_optional_manifest_and_tie_order_are_bound(self):
        table = self.write("compact101/nasbench_101_compact.pkl", b"compact101 fixture")
        manifest = self.write("compact101/nasbench_101_compact.manifest.json", b"{}")
        decoder = self.write("compact101/decoder.py", b"# fake NAS101 decoder")
        compact = SimpleNamespace(default_data_path=lambda: table, __file__=str(decoder))
        args = SimpleNamespace(scenario="tuning", tuning_task="hpobench:nasbench101:C")
        with self.hpo_paths(), self.fake_dependencies() as deps, patch.object(
            expgym, "compact_nasbench101", compact, create=True,
        ):
            initial = identity.evaluation_identity(args, self.root)
            self.assertEqual(initial["files"]["table"], identity.file_identity(table))
            self.assertEqual(initial["files"]["table_manifest"], identity.file_identity(manifest))
            self.assertEqual(initial["files"]["decoder_source"], identity.file_identity(decoder))
            self.assertEqual(initial["semantics"]["numpy_21_way_default_argsort_tie_order"], list(range(21)))
            deps.modules["numpy"].argsort = lambda values: SimpleNamespace(
                tolist=lambda: list(reversed(range(len(values)))),
            )
            changed = identity.evaluation_identity(args, self.root)
        self.assertNotEqual(initial["sha256"], changed["sha256"])
        self.assert_sealed(initial)

    def test_paramnet_uses_hpobench_resolved_configuration_and_selected_surrogates(self):
        objective = self.write("resolved-hpobench-data/Surrogates/rf_surrogate_paramnet_adult.pkl")
        cost = self.write("resolved-hpobench-data/Surrogates/rf_cost_surrogate_paramnet_adult.pkl")
        self.write("resolved-hpobench-data/Surrogates/rf_surrogate_paramnet_higgs.pkl", b"not selected")
        hpobench_config = self.write("hpobench-user-config.json", b"{}")
        with self.hpo_paths(), self.fake_dependencies(legacy_numpy=True, legacy_forest=True) as deps, \
                patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root / "not-resolved-hpobench-data")}):
            result = identity.evaluation_identity(SimpleNamespace(
                scenario="tuning", tuning_task="hpobench:paramnet:adult:steps",
            ), self.root)
            imported = [call.args[0] for call in deps.importer.call_args_list]
        self.assertEqual(result["files"]["objective_surrogate"], identity.file_identity(objective))
        self.assertEqual(result["files"]["cost_surrogate"], identity.file_identity(cost))
        self.assertEqual(result["files"]["hpobench_configuration"], identity.file_identity(hpobench_config))
        self.assertIn("numpy.core._multiarray_umath", imported)
        self.assertIn("sklearn.ensemble.forest", imported)
        self.assertEqual(set(result["dependencies"]), {
            "numpy", "ConfigSpace", "PyYAML", "hpobench", "scikit-learn", "scipy",
        })
        self.assert_sealed(result)

    def test_file_identity_missing_required_and_directory_fail_optional_records_absence(self):
        absent = self.root / "missing-input"
        for path in (absent, self.root):
            with self.subTest(path=path), self.assertRaisesRegex(FileNotFoundError, "Selected evaluation input"):
                identity.file_identity(path)
        self.assertEqual(identity.file_identity(absent, required=False), {
            "path": str(absent), "present": False,
        })

    def test_missing_search_corpus_fails_before_dependencies(self):
        with self.search_paths(seed=2) as (_, corpus), patch.object(
            identity, "_dependency_identity", side_effect=AssertionError("must fail before dependency import"),
        ):
            corpus.unlink()
            with self.assertRaises(FileNotFoundError):
                identity.evaluation_identity(SimpleNamespace(
                    scenario="restricted_search", data_source="phantom_seed2",
                ), self.root)

    def test_missing_audit_hints_is_required(self):
        evidence = self.write("audit/evidence.json", b"{}")
        with patch.object(audit, "EVIDENCE_PATH", str(evidence)), patch.object(
            audit, "HINTS_PATH", str(self.root / "missing-hints.json"),
        ), self.assertRaises(FileNotFoundError):
            identity.evaluation_identity(SimpleNamespace(scenario="evidence_audit"), self.root)

    def test_missing_compact_table_fails_even_with_manifest(self):
        manifest = self.write("compact201/manifest.json", b"{}")
        with self.hpo_paths(), self.fake_dependencies(), patch.object(
            compact_nasbench201, "default_data_dir", return_value=manifest.parent,
        ), self.assertRaises(FileNotFoundError):
            identity.evaluation_identity(SimpleNamespace(
                scenario="tuning", tuning_task="hpobench:nasbench201:cifar100",
            ), self.root)

    def test_missing_paramnet_surrogate_fails(self):
        self.write("resolved-hpobench-data/Surrogates/rf_surrogate_paramnet_adult.pkl")
        with self.hpo_paths(), self.fake_dependencies(), self.assertRaises(FileNotFoundError):
            identity.evaluation_identity(SimpleNamespace(
                scenario="tuning", tuning_task="hpobench:paramnet:adult:steps",
            ), self.root)

    def test_same_length_data_change_invalidates_cached_file_and_evaluation_hash(self):
        with self.search_paths(seed=2) as (questions, _), self.fake_dependencies():
            args = SimpleNamespace(scenario="restricted_search", data_source="phantom_seed2")
            initial = identity.evaluation_identity(args, self.root)
            original = questions.stat()
            replacement = b"x" * original.st_size
            questions.write_bytes(replacement)
            # No timing/sleep dependency, including filesystems with coarse mtimes.
            os.utime(questions, ns=(original.st_atime_ns, original.st_mtime_ns + 2_000_000_000))
            changed = identity.evaluation_identity(args, self.root)
        before = initial["files"]["questions"]
        after = changed["files"]["questions"]
        self.assertEqual(before["bytes"], after["bytes"])
        self.assertEqual(after["sha256"], hashlib.sha256(replacement).hexdigest())
        self.assertNotEqual(before["sha256"], after["sha256"])
        self.assertNotEqual(initial["sha256"], changed["sha256"])

    def test_dependency_version_and_same_length_loaded_module_change_identity(self):
        with self.search_paths(seed=2), self.fake_dependencies() as deps:
            args = SimpleNamespace(scenario="restricted_search", data_source="phantom_seed2")
            initial = identity.evaluation_identity(args, self.root)
            deps.versions["pyarrow"] = "test-version-2"
            new_version = identity.evaluation_identity(args, self.root)
            module = Path(deps.modules["pyarrow.lib"].__file__)
            original = module.stat()
            module.write_bytes(b"z" * original.st_size)
            os.utime(module, ns=(original.st_atime_ns, original.st_mtime_ns + 2_000_000_000))
            new_module = identity.evaluation_identity(args, self.root)
        self.assertNotEqual(initial["sha256"], new_version["sha256"])
        self.assertNotEqual(new_version["sha256"], new_module["sha256"])
        self.assertEqual(new_module["dependencies"]["pyarrow"]["version"], "test-version-2")

    def test_importable_source_dependency_without_wheel_metadata_is_still_hashed(self):
        with self.search_paths(seed=2), self.fake_dependencies() as deps:
            deps.version.side_effect = identity.metadata.PackageNotFoundError("fixture")
            result = identity.evaluation_identity(SimpleNamespace(
                scenario="restricted_search", data_source="phantom_seed2",
            ), self.root)
        self.assertIsNone(result["dependencies"]["pyarrow"]["version"])
        self.assertEqual(len(result["dependencies"]["pyarrow"]["modules"]), 3)
        self.assertTrue(all(item["present"] for item in result["dependencies"]["pyarrow"]["modules"].values()))

    def test_dependency_without_file_or_required_module_fails_closed(self):
        with self.search_paths(seed=2), self.fake_dependencies() as deps:
            args = SimpleNamespace(scenario="restricted_search", data_source="phantom_seed2")
            deps.modules["pyarrow.lib"].__file__ = None
            with self.assertRaisesRegex(RuntimeError, "Cannot fingerprint dependency module"):
                identity.evaluation_identity(args, self.root)
            del deps.modules["pyarrow.lib"]
            with self.assertRaises(ImportError):
                identity.evaluation_identity(args, self.root)

    def test_no_directory_scans_or_checkpoint_reads(self):
        checkpoint = self.write("ckpts/Kimi-K3/model-00001.safetensors", b"do not read")
        with self.search_paths(seed=2) as selected_paths, self.fake_dependencies() as deps, ExitStack() as stack:
            for name in ("glob", "rglob", "iterdir"):
                stack.enter_context(patch.object(Path, name, side_effect=AssertionError("directory scan")))
            stack.enter_context(patch.object(os, "walk", side_effect=AssertionError("directory scan")))
            stack.enter_context(patch.object(os, "scandir", side_effect=AssertionError("directory scan")))
            stack.enter_context(patch.dict(os.environ, {
                "MODEL_PATH": str(checkpoint.parent), "CHECKPOINT_PATH": str(checkpoint.parent),
            }))
            allowed = {path.resolve() for path in selected_paths} | {
                Path(deps.modules[name].__file__).resolve()
                for name in ("pyarrow", "pyarrow.lib", "pyarrow.parquet")
            }
            original_open = Path.open

            def checked_open(path, *args, **kwargs):
                self.assertIn(path.resolve(), allowed, "must not read unselected files or checkpoints")
                return original_open(path, *args, **kwargs)

            stack.enter_context(patch.object(Path, "open", checked_open))
            result = identity.evaluation_identity(SimpleNamespace(
                scenario="restricted_search", data_source="phantom_seed2",
                model_path=str(checkpoint.parent), checkpoint=str(checkpoint.parent),
            ), self.root)
        self.assertNotIn("Kimi-K3", json.dumps(result))
        self.assert_sealed(result)

    def test_unknown_scenario_and_tuning_task_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "No verified input identity adapter for scenario"):
            identity.evaluation_identity(SimpleNamespace(scenario="unknown"), self.root)
        with self.hpo_paths(), self.fake_dependencies(), self.assertRaisesRegex(
            ValueError, "No verified input identity adapter for tuning task",
        ):
            identity.evaluation_identity(SimpleNamespace(
                scenario="tuning", tuning_task="hpobench:unknown",
            ), self.root)

    def test_identical_bytes_after_timestamp_change_keep_identity(self):
        path = self.write("unchanged.dat", b"same bytes")
        initial = identity.file_identity(path)
        original = path.stat()
        os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns + 2_000_000_000))
        self.assertEqual(identity.file_identity(path), initial)

    def test_file_changed_during_hashing_is_rejected(self):
        path = self.write("changing.dat", b"fixture")
        initial_stat = identity._stat_key(path)
        changed_stat = (initial_stat[0], initial_stat[1] + 1, initial_stat[2], initial_stat[3])
        with patch.object(identity, "_stat_key", side_effect=[initial_stat, changed_stat]), \
                self.assertRaisesRegex(RuntimeError, "changed while hashing"):
            identity.file_identity(path)

    def test_binding_is_idempotent_and_allows_new_items_using_same_files(self):
        with self.search_paths(seed=2), self.fake_dependencies(), patch.dict(identity._BINDINGS, {}, clear=True):
            args = SimpleNamespace(scenario="restricted_search", data_source="phantom_seed2", question_index=0)
            first = identity.evaluation_identity(args, self.root)
            identity.bind_evaluation_identity(first)
            bound = dict(identity._BINDINGS)
            identity.bind_evaluation_identity(first)
            self.assertEqual(identity._BINDINGS, bound)
            args.question_index = 5
            next_item = identity.evaluation_identity(args, self.root)
            self.assertNotEqual(first["sha256"], next_item["sha256"])
            identity.bind_evaluation_identity(next_item)
            self.assertEqual(identity._BINDINGS, bound)

    def test_binding_rejects_same_length_changed_data_but_fresh_process_can_rebind(self):
        with self.search_paths(seed=2) as (questions, _), self.fake_dependencies(), \
                patch.dict(identity._BINDINGS, {}, clear=True):
            args = SimpleNamespace(scenario="restricted_search", data_source="phantom_seed2")
            first = identity.evaluation_identity(args, self.root)
            identity.bind_evaluation_identity(first)
            original = questions.stat()
            questions.write_bytes(b"x" * original.st_size)
            os.utime(questions, ns=(original.st_atime_ns, original.st_mtime_ns + 2_000_000_000))
            changed = identity.evaluation_identity(args, self.root)
            self.assertNotEqual(first["sha256"], changed["sha256"])
            with self.assertRaisesRegex(RuntimeError, "restart to reload task caches"):
                identity.bind_evaluation_identity(changed)
            # A fresh process with empty bindings may intentionally run new data.
            with patch.dict(identity._BINDINGS, {}, clear=True):
                identity.bind_evaluation_identity(changed)
                self.assertEqual(identity._BINDINGS[str(questions.resolve())],
                                 changed["files"]["questions"]["sha256"])

    def test_binding_rejects_changed_dependency_module(self):
        with self.search_paths(seed=2), self.fake_dependencies() as deps, \
                patch.dict(identity._BINDINGS, {}, clear=True):
            args = SimpleNamespace(scenario="restricted_search", data_source="phantom_seed2")
            identity.bind_evaluation_identity(identity.evaluation_identity(args, self.root))
            module = Path(deps.modules["pyarrow.lib"].__file__)
            original = module.stat()
            module.write_bytes(b"x" * original.st_size)
            os.utime(module, ns=(original.st_atime_ns, original.st_mtime_ns + 2_000_000_000))
            with self.assertRaisesRegex(RuntimeError, "restart to reload task caches"):
                identity.bind_evaluation_identity(identity.evaluation_identity(args, self.root))

    def test_binding_rejects_optional_file_appearing_or_disappearing(self):
        table = self.write("compact201/cifar100.pkl", b"compact selected table")
        manifest = table.parent / "manifest.json"
        args = SimpleNamespace(scenario="tuning", tuning_task="hpobench:nasbench201:cifar100")
        with self.hpo_paths(), self.fake_dependencies(), patch.object(
            compact_nasbench201, "default_data_dir", return_value=table.parent,
        ):
            for initially_present in (False, True):
                with self.subTest(initially_present=initially_present), \
                        patch.dict(identity._BINDINGS, {}, clear=True):
                    if initially_present:
                        manifest.write_bytes(b"{}")
                    else:
                        manifest.unlink(missing_ok=True)
                    identity.bind_evaluation_identity(identity.evaluation_identity(args, self.root))
                    if initially_present:
                        manifest.unlink()
                    else:
                        manifest.write_bytes(b"{}")
                    with self.assertRaisesRegex(RuntimeError, "restart to reload task caches"):
                        identity.bind_evaluation_identity(identity.evaluation_identity(args, self.root))

    def test_binding_failure_is_atomic_without_registering_earlier_new_files(self):
        evidence = self.write("audit/first_evidence.json", b"{}")
        other_evidence = self.write("audit/other_evidence.json", b"[]")
        hints = self.write("audit/hints.json", b"{}")
        args = SimpleNamespace(scenario="evidence_audit")
        with patch.object(audit, "EVIDENCE_PATH", str(evidence)), patch.object(
            audit, "HINTS_PATH", str(hints),
        ), patch.dict(identity._BINDINGS, {}, clear=True):
            identity.bind_evaluation_identity(identity.evaluation_identity(args, self.root))
            initial_bindings = dict(identity._BINDINGS)
            original = hints.stat()
            hints.write_bytes(b"[]")
            os.utime(hints, ns=(original.st_atime_ns, original.st_mtime_ns + 2_000_000_000))
            with patch.object(audit, "EVIDENCE_PATH", str(other_evidence)):
                changed = identity.evaluation_identity(args, self.root)
            with self.assertRaises(RuntimeError):
                identity.bind_evaluation_identity(changed)
            self.assertEqual(identity._BINDINGS, initial_bindings)
            self.assertNotIn(str(other_evidence), identity._BINDINGS)


if __name__ == "__main__":
    unittest.main()
