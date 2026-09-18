"""Download the external datasets ExpGym needs and verify the layout.

Usage:
    python scripts/download_data.py            # download everything that is missing
    python scripts/download_data.py --only phantom-wiki
                                              # download only Search data
    python scripts/download_data.py --check    # only verify the layout, do not fetch
    python scripts/download_data.py --print-data-links
                                              # show official data source links
    python scripts/download_data.py --contract-nli-archive /path/to/contract-nli.zip
                                              # optional offline ContractNLI override

Three dataset groups are needed for the full experiment sweep:
    1. Phantom Wiki    (auto-download from HuggingFace)
    2. HPOBench        (pinned code, ParamNet, NASBench101, and NASBench201)
    3. ContractNLI     (auto-download from the official GitHub-hosted zip)

The script reads ``EXPGYM_DATA_ROOT`` and ``PHANTOM_WIKI_ROOT`` from the
environment if set; otherwise it places the data under ``./data/`` relative
to the repo root. It is safe to re-run: each dataset is skipped when its
expected files are already present.
"""
from __future__ import annotations

import argparse
import base64
import bz2
import hashlib
import json
import os
import pickle
import shutil
import struct
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from typing import Callable, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Per-dataset config
# ---------------------------------------------------------------------------

PHANTOM_WIKI_HF_REPO = "kilian-group/phantom-wiki-v1"
PHANTOM_WIKI_HF_REV = "9369f9c64655f4e8146afee75ae5d3e3a95d7df5"  # snapshot used in the paper

HPOBENCH_GIT_URL = "https://github.com/automl/HPOBench.git"
# Commit verified by this repository. Override with HPOBENCH_GIT_REF if needed.
HPOBENCH_GIT_REF_DEFAULT = "47bf141f79e6bdfb26d1f1218b5d5aac09d7d2ce"

# HPOBench's original automl.org archive disappeared in 2026.  These are the
# exact ParamNet blobs from the old official HPOlib2 ``surrogates`` branch,
# retained by an early public fork.  Pin the commit and Git blob hashes so a
# moved branch or damaged download can never silently change an experiment.
HPOBENCH_PARAMNET_SOURCE_REPO = "LoneKnightz/HPOlib2"
HPOBENCH_PARAMNET_SOURCE_REF = "de88ab3aa2a39a86ccf8c85e9069f3441c1cfc61"
HPOBENCH_SURROGATES_DIR_ENV = "HPOBENCH_SURROGATES_DIR"
HPOBENCH_PARAMNET_FILES = {
    "rf_surrogate_paramnet_adult.pkl": (57408198, "c4e0814a71ce795119a12f1c14e831a306d53540"),
    "rf_cost_surrogate_paramnet_adult.pkl": (8095179, "f6df8e698158408286e16dd2961f3ead53b46d75"),
    "rf_surrogate_paramnet_higgs.pkl": (57436470, "a8e991e95b6aea95920355de57c25063a7c3d768"),
    "rf_cost_surrogate_paramnet_higgs.pkl": (8096715, "4026854c55c578a68b566f10b0a5acf338d3edfd"),
    "rf_surrogate_paramnet_letter.pkl": (57575097, "06e6ff8b5d3ab01e692ca8b54d7dcd70ae499f19"),
    "rf_cost_surrogate_paramnet_letter.pkl": (8073678, "33ac25783749a3bc4fd1cfb5db84fdeb2d2dd1eb"),
}

NASBENCH101_URL = "https://storage.googleapis.com/nasbench/nasbench_full.tfrecord"
NASBENCH101_SIZE = 2085986016
NASBENCH101_MD5 = "7bff458f43238c7a5f08e9074c903f83"
NASBENCH101_FILE_ENV = "HPOBENCH_NASBENCH101_FILE"
NASBENCH101_COMPACT_SCHEMA = "expgym.nasbench101-maxfidelity.v1"
NASBENCH101_ARCHITECTURES = 423624
NASBENCH101_BEST_VALIDATION_ERROR = 0.04944576819737756

# Official NATS-Bench topology-space archive.  We retain only the epoch-200
# objective and exact HPOBench cost for each architecture, because that is the
# sole fidelity used by this repository's paper matrix.
NATS_TSS_FILE_ID = "17_saCsj_krKjlCBLOJEpNtzPXArMCqxU"
NATS_TSS_URL = (
    "https://drive.usercontent.google.com/download"
    f"?id={NATS_TSS_FILE_ID}&export=download&confirm=t"
)
NATS_TSS_SIZE = 1145989120
NATS_TSS_SHA256 = "580fd8f3425fed9f495640b0f12ccb7744f89dec7aff263bd75aed37ab0b8bb6"
NATS_TSS_ARCHIVE_ENV = "HPOBENCH_NATS_TSS_ARCHIVE"
NASBENCH201_COMPACT_SCHEMA = "expgym.nasbench201-maxfidelity.v2"
NASBENCH201_COMPACT_FILES = (
    "cifar10-valid.pkl",
    "cifar100.pkl",
    "imagenet16-120.pkl",
)

CONTRACT_NLI_PAGE = (
    "https://github.com/stanfordnlp/contract-nli/blob/gh-pages/"
    "resources/contract-nli.zip"
)
CONTRACT_NLI_ZIP_URL = (
    "https://raw.githubusercontent.com/stanfordnlp/contract-nli/"
    "gh-pages/resources/contract-nli.zip"
)
# Only test_segments.json needs the Stanford download.
# test_nda_span_dims.json (the hints file) ships with this repo at
# data/contract-nli/test_nda_span_dims.json and is loaded from there
# automatically; the script does not check for it here.
CONTRACT_NLI_FILES = [
    "test_segments.json",
]
CONTRACT_NLI_ARCHIVE_ENV = "CONTRACT_NLI_ARCHIVE"
CONTRACT_NLI_ARCHIVE_MEMBERS = [
    "contract-nli/test_segments.json",
    "test_segments.json",
    # The public ContractNLI archive names the test split this way; ExpGym
    # consumes the same JSON schema under the historical test_segments.json name.
    "contract-nli/test.json",
    "test.json",
]


def contract_nli_data_links() -> str:
    target_dir = os.path.join(_data_root(), "contract-nli")
    return (
        "ContractNLI data source:\n"
        f"  Official GitHub page: {CONTRACT_NLI_PAGE}\n"
        f"  Direct zip URL: {CONTRACT_NLI_ZIP_URL}\n"
        "  Normal setup is automatic:\n"
        "    python scripts/download_data.py\n"
        "  Optional offline override:\n"
        "    python scripts/download_data.py --contract-nli-archive /absolute/path/to/contract-nli.zip\n"
        f"  ExpGym will extract only the test split to: {target_dir}/test_segments.json\n"
    )

def _data_root() -> str:
    return os.environ.get("EXPGYM_DATA_ROOT", os.path.join(REPO_ROOT, "data"))


def _phantom_wiki_root() -> str:
    return os.environ.get(
        "PHANTOM_WIKI_ROOT", os.path.join(REPO_ROOT, "data", "phantom-wiki")
    )


def _hpobench_dir() -> str:
    return os.path.join(REPO_ROOT, "data", "hpo_tuning", "HPOBench")


def _hpobench_surrogate_dir() -> str:
    # The Docker wrapper bind-mounts the repository and sets XDG_DATA_HOME to
    # this exact location, so keep legacy HPO data repo-local even when the
    # native Search/Audit data root is overridden.
    return os.path.join(
        REPO_ROOT, "data", "hpo_tuning", "hpobench_data", "Surrogates"
    )


def _hpobench_data_dir() -> str:
    return os.path.join(REPO_ROOT, "data", "hpo_tuning", "hpobench_data")


def _nasbench101_path() -> str:
    return os.path.join(_hpobench_data_dir(), "nasbench_101", "nasbench_full.tfrecord")


def _nasbench101_compact_path() -> str:
    return os.path.join(_hpobench_data_dir(), "nasbench_101_compact.pkl")


def _nasbench101_manifest_path() -> str:
    return os.path.join(_hpobench_data_dir(), "nasbench_101_compact.manifest.json")


def _nasbench201_compact_dir() -> str:
    return os.path.join(_hpobench_data_dir(), "nasbench_201_compact")


def _phantom_wiki_snapshot_dir() -> str:
    return os.path.join(
        _phantom_wiki_root(),
        f"datasets--{PHANTOM_WIKI_HF_REPO.replace('/', '--')}",
        "snapshots",
        PHANTOM_WIKI_HF_REV,
    )


# ---------------------------------------------------------------------------
# Download steps. Each returns (ok, message).
# ---------------------------------------------------------------------------

def fetch_phantom_wiki(check_only: bool) -> Tuple[bool, str]:
    """Download Phantom Wiki via huggingface_hub.snapshot_download."""
    snap = _phantom_wiki_snapshot_dir()
    qa_dir = os.path.join(snap, "question-answer")
    corpus_dir = os.path.join(snap, "text-corpus")
    if os.path.isdir(qa_dir) and os.path.isdir(corpus_dir):
        return True, f"Phantom Wiki already present at {_phantom_wiki_root()}"

    if check_only:
        return False, (
            f"Phantom Wiki MISSING.\n"
            f"  expected: {qa_dir}\n"
            f"            {corpus_dir}\n"
            f"  fix: run `python scripts/download_data.py` (no --check)."
        )

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        return False, (
            "Phantom Wiki download needs the `huggingface_hub` package. "
            "Install it with `pip install huggingface_hub`, then re-run."
        )

    os.makedirs(_phantom_wiki_root(), exist_ok=True)
    try:
        snapshot_download(
            repo_id=PHANTOM_WIKI_HF_REPO,
            repo_type="dataset",
            revision=PHANTOM_WIKI_HF_REV,
            cache_dir=_phantom_wiki_root(),
        )
    except Exception as exc:  # huggingface_hub raises a variety of subclasses
        return False, f"Phantom Wiki download failed: {exc}"

    if not (os.path.isdir(qa_dir) and os.path.isdir(corpus_dir)):
        return False, (
            "Phantom Wiki download appeared to succeed, but expected files are "
            f"missing under {snap}. Inspect the folder and rerun."
        )
    return True, f"Phantom Wiki ready at {_phantom_wiki_root()}"


def _git_blob_sha1(path: str, size: int) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_hpobench_blob(path: str, size: int, blob_sha1: str) -> bool:
    try:
        return os.path.getsize(path) == size and _git_blob_sha1(path, size) == blob_sha1
    except OSError:
        return False


def _hpobench_source_ready(target: str, ref: str) -> bool:
    """Require the pinned checkout, not merely a directory named HPOBench."""
    if not os.path.isfile(os.path.join(target, "setup.py")):
        return False
    try:
        head = subprocess.check_output(
            ["git", "-C", target, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return False
    return head == ref


def _hash_file(path: str, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_pinned_file(
    path: str,
    size: int,
    algorithm: str,
    checksum: str,
) -> bool:
    try:
        return os.path.getsize(path) == size and _hash_file(path, algorithm) == checksum
    except OSError:
        return False


def _download_pinned_file(
    url: str,
    target: str,
    size: int,
    algorithm: str,
    checksum: str,
) -> Tuple[bool, str]:
    """Download a large immutable file without accepting partial output."""
    if _valid_pinned_file(target, size, algorithm, checksum):
        return True, f"already verified: {target}"
    os.makedirs(os.path.dirname(target), exist_ok=True)
    partial = target + ".download"
    request = urllib.request.Request(url, headers={"User-Agent": "ExpGym data downloader"})
    try:
        downloaded = 0
        next_report = 128 * 1024 * 1024
        with urllib.request.urlopen(request, timeout=180) as response:
            with open(partial, "wb") as handle:
                while True:
                    chunk = response.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    if downloaded >= next_report:
                        print(f"    downloaded {downloaded / (1024 ** 3):.1f}/{size / (1024 ** 3):.1f} GiB")
                        next_report += 128 * 1024 * 1024
        if not _valid_pinned_file(partial, size, algorithm, checksum):
            return False, f"checksum or size mismatch for {target}"
        os.replace(partial, target)
        return True, f"downloaded and verified: {target}"
    except (urllib.error.URLError, OSError) as exc:
        return False, f"download failed for {target}: {exc}"
    finally:
        try:
            os.remove(partial)
        except OSError:
            pass


def _valid_nasbench101_compact() -> bool:
    try:
        with open(_nasbench101_manifest_path(), encoding="utf-8") as handle:
            manifest = json.load(handle)
        target = _nasbench101_compact_path()
        return (
            manifest.get("schema") == NASBENCH101_COMPACT_SCHEMA
            and manifest.get("source_md5") == NASBENCH101_MD5
            and manifest.get("architectures_count") == NASBENCH101_ARCHITECTURES
            and _hash_file(target, "sha256") == manifest.get("file_sha256")
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _read_varint(payload: bytes, position: int) -> Tuple[int, int]:
    value = 0
    shift = 0
    while position < len(payload) and shift < 70:
        byte = payload[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, position
        shift += 7
    raise ValueError("invalid protobuf varint")


def _protobuf_fields(payload: bytes) -> dict:
    fields = {}
    position = 0
    while position < len(payload):
        tag, position = _read_varint(payload, position)
        field_number, wire_type = tag >> 3, tag & 7
        if wire_type == 0:
            value, position = _read_varint(payload, position)
        elif wire_type == 1:
            end = position + 8
            if end > len(payload):
                raise ValueError("truncated protobuf fixed64")
            value = payload[position:end]
            position = end
        elif wire_type == 2:
            length, position = _read_varint(payload, position)
            end = position + length
            if end > len(payload):
                raise ValueError("truncated protobuf bytes")
            value = payload[position:end]
            position = end
        elif wire_type == 5:
            end = position + 4
            if end > len(payload):
                raise ValueError("truncated protobuf fixed32")
            value = payload[position:end]
            position = end
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")
        fields.setdefault(field_number, []).append(value)
    return fields


def _protobuf_double(fields: dict, field_number: int) -> float:
    values = fields.get(field_number)
    if not values or not isinstance(values[-1], bytes) or len(values[-1]) != 8:
        raise ValueError(f"missing protobuf double field {field_number}")
    return float(struct.unpack("<d", values[-1])[0])


def _decode_nasbench101_metrics(encoded: str) -> Tuple[float, float, float]:
    metrics = _protobuf_fields(base64.b64decode(encoded))
    evaluations = metrics.get(1, [])
    if len(evaluations) < 3 or not isinstance(evaluations[2], bytes):
        raise ValueError("NASBench101 row has no final evaluation")
    final = _protobuf_fields(evaluations[2])
    return (
        _protobuf_double(final, 4),
        _protobuf_double(final, 5),
        _protobuf_double(final, 2),
    )


def _iter_tfrecord(path: str):
    with open(path, "rb") as handle:
        while True:
            header = handle.read(12)
            if not header:
                return
            if len(header) != 12:
                raise ValueError("truncated TFRecord header")
            length = struct.unpack("<Q", header[:8])[0]
            payload = handle.read(length)
            footer = handle.read(4)
            if len(payload) != length or len(footer) != 4:
                raise ValueError("truncated TFRecord payload")
            yield payload


def _convert_nasbench101(source: str) -> Tuple[bool, str]:
    """Keep only the three-run aggregate at the paper's fixed budget 108."""
    aggregates = {}
    selected_rows = 0
    try:
        for payload in _iter_tfrecord(source):
            row = json.loads(payload.decode("utf-8"))
            if not isinstance(row, list) or len(row) != 5:
                raise ValueError("unexpected NASBench101 row")
            module_hash, epochs, _adjacency, _operations, encoded_metrics = row
            if int(epochs) != 108:
                continue
            validation, test, cost = _decode_nasbench101_metrics(encoded_metrics)
            aggregate = aggregates.setdefault(str(module_hash), [0, 0.0, 0.0, 0.0])
            aggregate[0] += 1
            aggregate[1] += validation
            aggregate[2] += test
            aggregate[3] += cost
            selected_rows += 1
            if selected_rows % 250000 == 0:
                print(
                    f"    converted {selected_rows}/{NASBENCH101_ARCHITECTURES * 3} "
                    "NASBench101 epoch-108 rows"
                )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        return False, f"NASBench101 conversion failed: {exc}"

    invalid_repeats = sum(aggregate[0] != 3 for aggregate in aggregates.values())
    if len(aggregates) != NASBENCH101_ARCHITECTURES or invalid_repeats:
        return False, (
            "NASBench101 conversion was incomplete: "
            f"architectures={len(aggregates)}, invalid_repeats={invalid_repeats}"
        )
    architectures = {
        module_hash: (
            1.0 - aggregate[1] / 3.0,
            1.0 - aggregate[2] / 3.0,
            aggregate[3],
        )
        for module_hash, aggregate in aggregates.items()
    }
    actual_best = min(row[0] for row in architectures.values())
    if abs(actual_best - NASBENCH101_BEST_VALIDATION_ERROR) > 1e-12:
        return False, (
            "NASBench101 oracle mismatch: "
            f"expected {NASBENCH101_BEST_VALIDATION_ERROR}, got {actual_best}"
        )

    target = _nasbench101_compact_path()
    manifest_path = _nasbench101_manifest_path()
    os.makedirs(os.path.dirname(target), exist_ok=True)
    partial = target + ".download"
    partial_manifest = manifest_path + ".download"
    try:
        with open(partial, "wb") as handle:
            pickle.dump(
                {
                    "schema": NASBENCH101_COMPACT_SCHEMA,
                    "source_md5": NASBENCH101_MD5,
                    "architectures_count": len(architectures),
                    "architectures": architectures,
                },
                handle,
                protocol=4,
            )
        os.replace(partial, target)
        manifest = {
            "schema": NASBENCH101_COMPACT_SCHEMA,
            "source": NASBENCH101_URL,
            "source_md5": NASBENCH101_MD5,
            "architectures_count": len(architectures),
            "file_sha256": _hash_file(target, "sha256"),
        }
        with open(partial_manifest, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, sort_keys=True, indent=2)
        os.replace(partial_manifest, manifest_path)
    except OSError as exc:
        return False, f"failed to write compact NASBench101 data: {exc}"
    finally:
        for leftover in (partial, partial_manifest):
            try:
                os.remove(leftover)
            except OSError:
                pass
    return True, f"NASBench101 compact data ready at {target}"


def _prepare_nasbench101(check_only: bool) -> Tuple[bool, str]:
    if _valid_nasbench101_compact():
        return True, f"NASBench101 compact data verified at {_nasbench101_compact_path()}"
    if check_only:
        return False, (
            f"NASBench101 compact data missing or corrupt at {_nasbench101_compact_path()}"
        )

    raw_target = _nasbench101_path()
    local_file = os.environ.get(NASBENCH101_FILE_ENV)
    if local_file:
        source = os.path.abspath(local_file)
        if not _valid_pinned_file(source, NASBENCH101_SIZE, "md5", NASBENCH101_MD5):
            return False, f"offline NASBench101 file failed validation: {source}"
        remove_after_conversion = False
    else:
        source = raw_target
        ok, message = _download_pinned_file(
            NASBENCH101_URL,
            source,
            NASBENCH101_SIZE,
            "md5",
            NASBENCH101_MD5,
        )
        if not ok:
            return False, message
        remove_after_conversion = True

    ok, message = _convert_nasbench101(source)
    if ok and remove_after_conversion:
        try:
            os.remove(source)
        except OSError:
            pass
    return ok, message


def _compact_manifest_path() -> str:
    return os.path.join(_nasbench201_compact_dir(), "manifest.json")


def _valid_nasbench201_compact() -> bool:
    try:
        with open(_compact_manifest_path(), encoding="utf-8") as handle:
            manifest = json.load(handle)
        if (
            manifest.get("schema") != NASBENCH201_COMPACT_SCHEMA
            or manifest.get("source_sha256") != NATS_TSS_SHA256
            or manifest.get("missing_seed_policy") != "repeat-last-available"
            or set(manifest.get("files", {})) != set(NASBENCH201_COMPACT_FILES)
        ):
            return False
        for filename, checksum in manifest["files"].items():
            path = os.path.join(_nasbench201_compact_dir(), filename)
            if _hash_file(path, "sha256") != checksum:
                return False
        return True
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _mapping_value(mapping: dict, key: object) -> object:
    if key in mapping:
        return mapping[key]
    return mapping[str(key)]


def _nats_configuration_id(architecture: str) -> str:
    operations = [
        "none",
        "skip_connect",
        "nor_conv_1x1",
        "nor_conv_3x3",
        "avg_pool_3x3",
    ]
    selected = [component.split("|")[-1] for component in architecture.split("~")[:-1]]
    if len(selected) != 6:
        raise ValueError(f"unexpected NATS architecture: {architecture}")
    return "".join(str(operations.index(operation)) for operation in selected)


def _convert_nats_archive(archive: str) -> Tuple[bool, str]:
    """Stream the official archive into three exact max-fidelity tables."""
    datasets = {
        "cifar10-valid": ("cifar10-valid", "x-valid"),
        "cifar100": ("cifar100", "ori-test"),
        "imagenet16-120": ("ImageNet16-120", "ori-test"),
    }
    tables = {name: {} for name in datasets}
    try:
        with tarfile.open(archive, mode="r|") as tar:
            processed = 0
            for member in tar:
                if not member.isfile() or not member.name.endswith(".pickle.pbz2"):
                    continue
                filename = os.path.basename(member.name)
                if not filename[: -len(".pickle.pbz2")].isdigit():
                    continue
                extracted = tar.extractfile(member)
                if extracted is None:
                    raise ValueError(f"could not read archive member {member.name}")
                record = pickle.loads(bz2.decompress(extracted.read()))["200"]
                config_id = _nats_configuration_id(record["arch_str"])
                all_results = record["all_results"]
                for output_name, (source_name, valid_key) in datasets.items():
                    rows = []
                    for seed in (777, 888, 999):
                        result = all_results.get((source_name, seed))
                        if result is None:
                            continue
                        accuracy = float(
                            _mapping_value(result["eval_acc1es"], f"{valid_key}@199")
                        )
                        train_cost = sum(
                            float(_mapping_value(result["train_times"], epoch))
                            for epoch in range(1, 200)
                        )
                        valid_cost = sum(
                            float(
                                _mapping_value(
                                    result["eval_times"], f"{valid_key}@{epoch}"
                                )
                            )
                            for epoch in range(1, 200)
                        )
                        rows.append((accuracy, train_cost + valid_cost))
                    if not rows:
                        raise ValueError(
                            f"no {source_name} results in archive member {member.name}"
                        )
                    # HPOBench's published JSON repeats the latest available
                    # run when a suffix seed is absent (normally seed 999).
                    while len(rows) < 3:
                        rows.append(rows[-1])
                    objective = 100.0 - sum(row[0] for row in rows) / len(rows)
                    cost = sum(row[1] for row in rows)
                    tables[output_name][config_id] = (objective, cost)
                processed += 1
                if processed % 2000 == 0:
                    print(f"    converted {processed}/15625 NASBench201 architectures")
    except (KeyError, OSError, pickle.PickleError, tarfile.TarError, ValueError) as exc:
        return False, f"NASBench201 conversion failed: {exc}"

    expected = 5 ** 6
    if any(len(table) != expected for table in tables.values()):
        counts = {name: len(table) for name, table in tables.items()}
        return False, f"NASBench201 conversion was incomplete: {counts}"
    reference_best = {
        "cifar10-valid": 8.393333349609364,
        "cifar100": 26.49666666666667,
        "imagenet16-120": 53.1555555352105,
    }
    for dataset, expected_best in reference_best.items():
        actual_best = min(row[0] for row in tables[dataset].values())
        if abs(actual_best - expected_best) > 1e-9:
            return False, (
                f"NASBench201 {dataset} oracle mismatch: "
                f"expected {expected_best}, got {actual_best}"
            )

    output_dir = _nasbench201_compact_dir()
    os.makedirs(output_dir, exist_ok=True)
    checksums = {}
    try:
        for dataset, table in tables.items():
            filename = f"{dataset}.pkl"
            target = os.path.join(output_dir, filename)
            partial = target + ".download"
            payload = {
                "schema": NASBENCH201_COMPACT_SCHEMA,
                "dataset": dataset,
                "source_sha256": NATS_TSS_SHA256,
                "missing_seed_policy": "repeat-last-available",
                "architectures": table,
            }
            with open(partial, "wb") as handle:
                pickle.dump(payload, handle, protocol=4)
            os.replace(partial, target)
            checksums[filename] = _hash_file(target, "sha256")
        manifest = {
            "schema": NASBENCH201_COMPACT_SCHEMA,
            "source": NATS_TSS_URL,
            "source_sha256": NATS_TSS_SHA256,
            "missing_seed_policy": "repeat-last-available",
            "files": checksums,
        }
        manifest_path = _compact_manifest_path()
        partial_manifest = manifest_path + ".download"
        with open(partial_manifest, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, sort_keys=True, indent=2)
        os.replace(partial_manifest, manifest_path)
    except OSError as exc:
        return False, f"failed to write compact NASBench201 data: {exc}"
    return True, f"NASBench201 compact data ready at {output_dir}"


def _prepare_nasbench201(check_only: bool) -> Tuple[bool, str]:
    if _valid_nasbench201_compact():
        return True, f"NASBench201 compact data verified at {_nasbench201_compact_dir()}"
    if check_only:
        return False, f"NASBench201 compact data missing or corrupt at {_nasbench201_compact_dir()}"

    local_archive = os.environ.get(NATS_TSS_ARCHIVE_ENV)
    downloaded_archive = None
    if local_archive:
        archive = os.path.abspath(local_archive)
        if not _valid_pinned_file(
            archive, NATS_TSS_SIZE, "sha256", NATS_TSS_SHA256
        ):
            return False, f"offline NATS-Bench archive failed validation: {archive}"
    else:
        downloaded_archive = os.path.join(
            _hpobench_data_dir(), "NATS-tss-v1_0-3ffb9-simple.tar"
        )
        ok, message = _download_pinned_file(
            NATS_TSS_URL,
            downloaded_archive,
            NATS_TSS_SIZE,
            "sha256",
            NATS_TSS_SHA256,
        )
        if not ok:
            return False, message
        archive = downloaded_archive
    try:
        return _convert_nats_archive(archive)
    finally:
        if downloaded_archive:
            try:
                os.remove(downloaded_archive)
            except OSError:
                pass


def _install_hpobench_blob(
    filename: str,
    size: int,
    blob_sha1: str,
    target_dir: str,
) -> Tuple[bool, str]:
    """Install one pinned surrogate with validation and atomic replacement."""
    target = os.path.join(target_dir, filename)
    partial = target + ".download"
    local_dir = os.environ.get(HPOBENCH_SURROGATES_DIR_ENV)
    os.makedirs(target_dir, exist_ok=True)
    try:
        if local_dir:
            source = os.path.join(os.path.abspath(local_dir), filename)
            if not os.path.isfile(source):
                return False, f"offline surrogate file not found: {source}"
            shutil.copyfile(source, partial)
        else:
            url = (
                "https://raw.githubusercontent.com/"
                f"{HPOBENCH_PARAMNET_SOURCE_REPO}/"
                f"{HPOBENCH_PARAMNET_SOURCE_REF}/surrogates/{filename}"
            )
            request = urllib.request.Request(
                url, headers={"User-Agent": "ExpGym data downloader"}
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                with open(partial, "wb") as handle:
                    shutil.copyfileobj(response, handle, length=1024 * 1024)

        if not _valid_hpobench_blob(partial, size, blob_sha1):
            return False, f"checksum or size mismatch for {filename}"
        os.replace(partial, target)
        return True, filename
    except (urllib.error.URLError, OSError) as exc:
        return False, f"failed to install {filename}: {exc}"
    finally:
        try:
            os.remove(partial)
        except OSError:
            pass


def fetch_hpobench(check_only: bool) -> Tuple[bool, str]:
    """Prepare every pinned HPOBench dependency used by the paper matrix."""
    target = _hpobench_dir()
    setup_py = os.path.join(target, "setup.py")
    ref = os.environ.get("HPOBENCH_GIT_REF", HPOBENCH_GIT_REF_DEFAULT)
    source_ready = _hpobench_source_ready(target, ref)
    surrogate_dir = _hpobench_surrogate_dir()
    invalid_files = [
        filename
        for filename, (size, blob_sha1) in HPOBENCH_PARAMNET_FILES.items()
        if not _valid_hpobench_blob(
            os.path.join(surrogate_dir, filename), size, blob_sha1
        )
    ]
    nasbench101_ready, nasbench101_message = _prepare_nasbench101(check_only=True)
    nasbench201_ready, nasbench201_message = _prepare_nasbench201(check_only=True)
    if (
        source_ready
        and not invalid_files
        and nasbench101_ready
        and nasbench201_ready
    ):
        return True, f"HPOBench code and all benchmark data verified under {target}"

    if check_only:
        missing = []
        if not source_ready:
            missing.append(f"pinned source ref {ref} at {setup_py}")
        if invalid_files:
            missing.append(
                f"{len(invalid_files)} pinned ParamNet file(s) under {surrogate_dir}"
            )
        if not nasbench101_ready:
            missing.append(nasbench101_message)
        if not nasbench201_ready:
            missing.append(nasbench201_message)
        return False, (
            f"HPOBench MISSING.\n"
            f"  expected: {'; '.join(missing)}\n"
            f"  fix: run `python scripts/download_data.py` (no --check)."
        )

    if not source_ready:
        if shutil.which("git") is None:
            return False, "HPOBench download needs `git`. Install git and re-run."
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if os.path.isdir(target):
            try:
                shutil.rmtree(target)
            except OSError as exc:
                return False, f"Failed to clear stale {target}: {exc}"
        commands = [
            ["git", "init", target],
            ["git", "-C", target, "remote", "add", "origin", HPOBENCH_GIT_URL],
            ["git", "-C", target, "fetch", "--depth", "1", "origin", ref],
            ["git", "-C", target, "checkout", "--detach", "FETCH_HEAD"],
        ]
        try:
            for command in commands:
                subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            return False, f"HPOBench `git clone` failed: {exc}"
        if not os.path.isfile(setup_py):
            return False, f"HPOBench cloned but setup.py not found at {setup_py}"

    installed = []
    for filename in invalid_files:
        size, blob_sha1 = HPOBENCH_PARAMNET_FILES[filename]
        ok, message = _install_hpobench_blob(
            filename, size, blob_sha1, surrogate_dir
        )
        if not ok:
            return False, message
        installed.append(message)

    # Convert NASBench201 before downloading NASBench101 so a low-memory
    # installation fails early without wasting the larger NASBench101 fetch.
    if not nasbench201_ready:
        ok, nasbench201_message = _prepare_nasbench201(check_only=False)
        if not ok:
            return False, nasbench201_message
    if not nasbench101_ready:
        ok, nasbench101_message = _prepare_nasbench101(check_only=False)
        if not ok:
            return False, nasbench101_message
    return True, (
        f"HPOBench ready at {target} (ref={ref}); "
        f"ParamNet files installed/verified: "
        f"{len(installed) or len(HPOBENCH_PARAMNET_FILES)}; "
        f"{nasbench101_message}; {nasbench201_message}"
    )


def fetch_contract_nli(check_only: bool) -> Tuple[bool, str]:
    """Download and extract ContractNLI from the official GitHub-hosted zip."""
    target_dir = os.path.join(_data_root(), "contract-nli")
    have_all = all(
        os.path.isfile(os.path.join(target_dir, f)) for f in CONTRACT_NLI_FILES
    )
    if have_all:
        return True, f"ContractNLI already present at {target_dir}"

    archive = os.environ.get(CONTRACT_NLI_ARCHIVE_ENV)
    if archive and not check_only:
        ok, message = _extract_contract_nli_archive(archive, target_dir)
        if ok:
            return ok, message
        return False, message

    missing = [
        f for f in CONTRACT_NLI_FILES
        if not os.path.isfile(os.path.join(target_dir, f))
    ]
    if check_only:
        msg = (
            f"ContractNLI MISSING.\n"
            f"  expected: {target_dir}/test_segments.json\n"
            f"  fix: run `python scripts/download_data.py` (no --check), or use "
            f"`--contract-nli-archive /path/to/contract-nli.zip` for an offline zip.\n"
            f"  source: {CONTRACT_NLI_PAGE}\n"
            f"  Currently missing: {', '.join(missing)}"
        )
        return False, msg

    archive_path = ""
    try:
        archive_path = _download_contract_nli_archive(target_dir)
        ok, message = _extract_contract_nli_archive(archive_path, target_dir)
        if ok:
            return True, f"ContractNLI downloaded from {CONTRACT_NLI_ZIP_URL}; {message}"
        return False, message
    except RuntimeError as exc:
        return False, str(exc)
    finally:
        if archive_path:
            try:
                os.remove(archive_path)
            except OSError:
                pass


def _download_contract_nli_archive(target_dir: str) -> str:
    os.makedirs(target_dir, exist_ok=True)
    archive_path = os.path.join(target_dir, "contract-nli.zip.download")
    request = urllib.request.Request(
        CONTRACT_NLI_ZIP_URL,
        headers={"User-Agent": "ExpGym data downloader"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            with open(archive_path, "wb") as handle:
                shutil.copyfileobj(response, handle)
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(f"ContractNLI download failed: {exc}") from exc
    return archive_path


def _extract_contract_nli_archive(archive: str, target_dir: str) -> Tuple[bool, str]:
    if not os.path.isfile(archive):
        return False, f"ContractNLI archive not found: {archive}"
    try:
        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            member = next((name for name in CONTRACT_NLI_ARCHIVE_MEMBERS if name in names), None)
            if member is None:
                return False, (
                    "ContractNLI archive did not contain a supported test JSON. "
                    f"Looked for: {', '.join(CONTRACT_NLI_ARCHIVE_MEMBERS)}"
                )
            raw = zf.read(member)
    except zipfile.BadZipFile as exc:
        return False, f"ContractNLI archive is not a valid zip file: {exc}"
    except OSError as exc:
        return False, f"Failed to read ContractNLI archive: {exc}"

    try:
        data = json.loads(raw.decode("utf-8"))
        data = _normalize_contract_nli_schema(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"ContractNLI test JSON could not be parsed: {exc}"
    except (TypeError, ValueError) as exc:
        return False, f"ContractNLI test JSON has unexpected schema: {exc}"

    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, "test_segments.json")
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    return True, f"ContractNLI extracted {member} -> {target}"


def _normalize_contract_nli_schema(data: object) -> dict:
    if not isinstance(data, dict) or "documents" not in data or "labels" not in data:
        raise ValueError("expected top-level documents and labels")
    documents = data["documents"]
    if not isinstance(documents, list):
        raise ValueError("documents must be a list")
    for doc in documents:
        if not isinstance(doc, dict):
            raise ValueError("each document must be an object")
        if "segments" in doc:
            continue
        spans = doc.get("spans")
        text = doc.get("text")
        if spans is None or text is None:
            raise ValueError("document must contain segments or spans+text")
        doc["segments"] = [
            {"span_index": idx, "text": text[int(start):int(end)]}
            for idx, (start, end) in enumerate(spans)
        ]
    return data


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

STEPS: List[Tuple[str, Callable[[bool], Tuple[bool, str]]]] = [
    ("Phantom Wiki",  fetch_phantom_wiki),
    ("HPOBench",      fetch_hpobench),
    ("ContractNLI",   fetch_contract_nli),
]

STEP_ALIASES = {
    "phantom-wiki": "Phantom Wiki",
    "hpobench": "HPOBench",
    "contract-nli": "ContractNLI",
}


def _select_steps(value: str) -> List[Tuple[str, Callable[[bool], Tuple[bool, str]]]]:
    requested = [part.strip().lower() for part in value.split(",") if part.strip()]
    if not requested or requested == ["all"]:
        return STEPS
    unknown = [name for name in requested if name not in STEP_ALIASES]
    if unknown:
        choices = ", ".join([*STEP_ALIASES, "all"])
        raise ValueError(f"unknown dataset(s): {', '.join(unknown)}; choose from {choices}")
    selected_names = {STEP_ALIASES[name] for name in requested}
    return [step for step in STEPS if step[0] in selected_names]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify the layout; do not download anything.",
    )
    parser.add_argument(
        "--only",
        default="all",
        metavar="DATASETS",
        help=(
            "Comma-separated subset: phantom-wiki, hpobench, contract-nli, "
            "or all (default)."
        ),
    )
    parser.add_argument(
        "--auto-only",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--contract-nli-archive",
        default=None,
        help="Optional path to a local ContractNLI zip archive.",
    )
    parser.add_argument(
        "--print-data-links",
        dest="print_data_links",
        action="store_true",
        help="Print official data source links.",
    )
    parser.add_argument(
        "--print-manual-links",
        dest="print_data_links",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.print_data_links:
        print(contract_nli_data_links())
        return 0

    if args.contract_nli_archive:
        os.environ[CONTRACT_NLI_ARCHIVE_ENV] = args.contract_nli_archive

    print(f"EXPGYM_DATA_ROOT   = {_data_root()}")
    print(f"PHANTOM_WIKI_ROOT  = {_phantom_wiki_root()}")
    print(f"HPOBench checkout  = {_hpobench_dir()}")
    print()

    try:
        selected_steps = _select_steps(args.only)
    except ValueError as exc:
        parser.error(str(exc))
    result_label = (
        "all datasets"
        if len(selected_steps) == len(STEPS)
        else ", ".join(name for name, _ in selected_steps)
    )

    failures: List[str] = []
    for name, step in selected_steps:
        print(f"[{name}] ...")
        ok, message = step(args.check)
        prefix = "  OK  " if ok else "  ERR "
        for i, line in enumerate(message.splitlines()):
            print(f"{prefix if i == 0 else '       '}{line}")
        if not ok:
            failures.append(name)
        print()

    if failures:
        print(f"Result: {len(failures)} dataset(s) not ready: {', '.join(failures)}.")
        return 1
    print(f"Result: {result_label} ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
