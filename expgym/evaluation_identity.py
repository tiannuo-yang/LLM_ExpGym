"""Content identities for the selected evaluation inputs, not entire machines.

No checkpoint, unrelated dataset, credential, or environment dump is inspected.
Call only for execution/resume, never for a data-free ``--dry-run``. The manifest
binds actual selected data bytes, task configuration, dependency versions and
critical loaded implementation files; it is not a full virtualenv attestation.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    from importlib import metadata
except ImportError:  # Python 3.7 in the legacy HPOBench environment.
    import importlib_metadata as metadata


IDENTITY_VERSION = "expgym.evaluation-inputs.v1"
_BINDINGS: Dict[str, Optional[str]] = {}


def bind_evaluation_identity(identity: Dict[str, Any]) -> None:
    """Refuse mid-process input changes instead of using stale loader caches.

    Task modules cache parsed corpora/tables. A fresh CLI process can bind a
    changed dataset, but an already-running process must restart to reload it.
    """
    records = list(identity["files"].values())
    for dependency in identity["dependencies"].values():
        records.extend(dependency["modules"].values())
    for record in records:
        path = record["path"]
        checksum = record.get("sha256")
        if path in _BINDINGS and _BINDINGS[path] != checksum:
            raise RuntimeError(f"Evaluation input changed after binding; restart to reload task caches: {path}")
    for record in records:
        _BINDINGS[record["path"]] = record.get("sha256")


def _stat_key(path: Path) -> Tuple[int, int, int, int]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino


@lru_cache(maxsize=512)
def _content_hash(path: str, stat_key: Tuple[int, int, int, int]) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    if _stat_key(Path(path)) != stat_key:
        raise RuntimeError(f"Evaluation input changed while hashing: {path}")
    return digest.hexdigest()


def file_identity(path: Path, *, required: bool = True) -> Dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"Selected evaluation input is missing: {path}")
        return {"path": str(path), "present": False}
    stat_key = _stat_key(path)
    return {
        "path": str(path), "present": True, "bytes": stat_key[0],
        "sha256": _content_hash(str(path), stat_key),
    }


def _module_identity(module_name: str) -> Dict[str, Any]:
    module = importlib.import_module(module_name)
    origin = getattr(module, "__file__", None)
    if not origin:
        raise RuntimeError(f"Cannot fingerprint dependency module: {module_name}")
    return file_identity(Path(origin))


def _dependency_identity(distribution: str, modules: List[str]) -> Dict[str, Any]:
    try:
        version: Optional[str] = metadata.version(distribution)
    except metadata.PackageNotFoundError:
        version = None  # Source checkouts can be importable without wheel metadata.
    return {
        "version": version,
        "modules": {name: _module_identity(name) for name in modules},
    }


def _first_importable(names: List[str]) -> str:
    for name in names:
        try:
            importlib.import_module(name)
            return name
        except ImportError:
            continue
    raise ImportError(f"Cannot locate required dependency implementation: {names}")


def evaluation_identity(args: Any, repo_root: Path) -> Dict[str, Any]:
    """Resolve and hash only the data/dependencies used by one selected task."""
    scenario = str(args.scenario)
    selected: Dict[str, Any] = {"scenario": scenario}
    files: Dict[str, Dict[str, Any]] = {}
    dependencies: Dict[str, Any] = {}
    semantics: Dict[str, Any] = {}
    if scenario == "restricted_search":
        from expgym import task_restricted_search as task

        source = getattr(args, "data_source", None) or "phantom_seed1"
        seed = task._resolve_seed(source)
        filename = f"depth_20_size_5000_seed_{seed}-00000-of-00001.parquet"
        files["questions"] = file_identity(Path(task.QA_DIR) / filename)
        files["corpus"] = file_identity(Path(task.CORPUS_DIR) / filename)
        selected.update(data_source=source, question_index=getattr(args, "question_index", 0))
        semantics.update(filter_types=list(task.SWEET_SPOT_TYPES), max_answer_count=task.MAX_ANSWER_COUNT)
        dependencies["pyarrow"] = _dependency_identity("pyarrow", ["pyarrow", "pyarrow.lib", "pyarrow.parquet"])
    elif scenario == "evidence_audit":
        from expgym import task_evidence_audit as task

        files["evidence"] = file_identity(Path(task.EVIDENCE_PATH))
        files["hints"] = file_identity(Path(task.HINTS_PATH))
        selected.update(
            question_index=getattr(args, "question_index", 0),
            cc_split=getattr(args, "cc_split", "cc-large"),
            hypothesis_order=getattr(args, "hypothesis_order", None),
        )
        semantics["evidence_scoring_protocol"] = getattr(task, "EVIDENCE_SCORING_PROTOCOL", None)
    elif scenario == "tuning":
        from expgym import task_tuning as task

        name = getattr(args, "tuning_task", "neural_network_training")
        selected["tuning_task"] = name
        if name != "neural_network_training":
            files["task_configuration"] = file_identity(task.HPOBENCH_CONFIG_PATH, required=False)
            files["budget_oracle"] = file_identity(repo_root / "data/hpo_tuning/oracle3.json", required=False)
            numpy_core = _first_importable(["numpy._core._multiarray_umath", "numpy.core._multiarray_umath"])
            dependencies["numpy"] = _dependency_identity("numpy", ["numpy", numpy_core])
            dependencies["ConfigSpace"] = _dependency_identity("ConfigSpace", ["ConfigSpace", "ConfigSpace.configuration_space"])
            dependencies["PyYAML"] = _dependency_identity("PyYAML", ["yaml"])
            if name.startswith("hpobench:nasbench101:"):
                from expgym import compact_nasbench101 as compact
                import numpy as np

                files["table"] = file_identity(compact.default_data_path())
                files["decoder_source"] = file_identity(Path(compact.__file__))
                files["table_manifest"] = file_identity(compact.default_data_path().with_suffix(".manifest.json"), required=False)
                semantics["numpy_21_way_default_argsort_tie_order"] = np.argsort(np.zeros(21)).tolist()
            elif name.startswith("hpobench:nasbench201:"):
                from expgym import compact_nasbench201 as compact

                dataset = name.split(":")[2]
                files["table"] = file_identity(compact.default_data_dir() / compact.DATASET_FILES[dataset])
                files["decoder_source"] = file_identity(Path(compact.__file__))
                files["table_manifest"] = file_identity(compact.default_data_dir() / "manifest.json", required=False)
            elif name.startswith("hpobench:paramnet:"):
                # Match the task loader's import path and use HPOBench's resolved
                # config, which may override XDG_DATA_HOME in .hpobenchrc.
                if task.HPOBENCH_ROOT not in sys.path:
                    sys.path.insert(0, task.HPOBENCH_ROOT)
                hpobench = importlib.import_module("hpobench")
                dataset = name.split(":")[2]
                data_dir = Path(hpobench.config_file.data_dir) / "Surrogates"
                for label, prefix in (("objective_surrogate", "rf_surrogate"), ("cost_surrogate", "rf_cost_surrogate")):
                    files[label] = file_identity(data_dir / f"{prefix}_paramnet_{dataset}.pkl")
                files["hpobench_configuration"] = file_identity(Path(hpobench.config_file.config_file), required=False)
                dependencies["hpobench"] = _dependency_identity("hpobench", [
                    "hpobench", "hpobench.config", "hpobench.abstract_benchmark",
                    "hpobench.util.data_manager", "hpobench.benchmarks.surrogates.paramnet_benchmark",
                ])
                forest = _first_importable(["sklearn.ensemble._forest", "sklearn.ensemble.forest"])
                dependencies["scikit-learn"] = _dependency_identity("scikit-learn", ["sklearn", forest, "sklearn.tree._tree"])
                dependencies["scipy"] = _dependency_identity("scipy", ["scipy"])
            else:
                raise ValueError(f"No verified input identity adapter for tuning task: {name}")
    else:
        raise ValueError(f"No verified input identity adapter for scenario: {scenario}")

    body: Dict[str, Any] = {
        "version": IDENTITY_VERSION, "selected": selected, "files": files,
        "dependencies": dependencies, "semantics": semantics,
        "python": {
            "version": platform.python_version(), "implementation": platform.python_implementation(),
            "machine": platform.machine(), "byteorder": sys.byteorder,
        },
        "scope": "selected input bytes and critical dependency modules; not a full environment attestation",
    }
    encoded = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {**body, "sha256": hashlib.sha256(encoded).hexdigest()}
