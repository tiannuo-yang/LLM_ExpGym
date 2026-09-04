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

Three datasets are needed for the full experiment sweep:
    1. Phantom Wiki    (auto-download from HuggingFace)
    2. HPOBench code   (auto-download from GitHub)
    3. ContractNLI     (auto-download from the official GitHub-hosted zip)

The script reads ``EXPGYM_DATA_ROOT`` and ``PHANTOM_WIKI_ROOT`` from the
environment if set; otherwise it places the data under ``./data/`` relative
to the repo root. It is safe to re-run: each dataset is skipped when its
expected files are already present.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
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
# Pin to a commit known to load the surrogate pickles this repo expects.
# Override with HPOBENCH_GIT_REF=<sha or tag> if you want a different cut.
HPOBENCH_GIT_REF_DEFAULT = "master"

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


def fetch_hpobench(check_only: bool) -> Tuple[bool, str]:
    """Clone HPOBench source into data/hpo_tuning/HPOBench/."""
    target = _hpobench_dir()
    setup_py = os.path.join(target, "setup.py")
    if os.path.isfile(setup_py):
        return True, f"HPOBench already cloned at {target}"

    if check_only:
        return False, (
            f"HPOBench MISSING.\n"
            f"  expected setup.py at: {setup_py}\n"
            f"  fix: run `python scripts/download_data.py` (no --check)."
        )

    if shutil.which("git") is None:
        return False, "HPOBench download needs `git`. Install git and re-run."

    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.isdir(target) and not os.path.isfile(setup_py):
        # Empty placeholder dir from earlier — clear it so git can clone in.
        try:
            shutil.rmtree(target)
        except OSError as exc:
            return False, f"Failed to clear stale {target}: {exc}"

    ref = os.environ.get("HPOBENCH_GIT_REF", HPOBENCH_GIT_REF_DEFAULT)
    cmd = ["git", "clone", "--depth", "1", "--branch", ref, HPOBENCH_GIT_URL, target]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        return False, f"HPOBench `git clone` failed: {exc}"

    if not os.path.isfile(setup_py):
        return False, f"HPOBench cloned but setup.py not found at {setup_py}"
    return True, (
        f"HPOBench cloned at {target} (ref={ref}). "
        f"Now run `pip install -e {target}` plus the deps listed in "
        f"scripts/recreate_expgym_env.sh."
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
