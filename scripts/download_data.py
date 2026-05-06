"""Download the external datasets ExpGym needs and verify the layout.

Usage:
    python scripts/download_data.py            # download everything that is missing
    python scripts/download_data.py --check    # only verify the layout, do not fetch

Three datasets are needed for the full experiment sweep:
    1. Phantom Wiki    (auto-download from HuggingFace)
    2. HPOBench code   (auto-download from GitHub)
    3. ContractNLI     (manual — see printed instructions)

The script reads ``EXPGYM_DATA_ROOT`` and ``PHANTOM_WIKI_ROOT`` from the
environment if set; otherwise it places the data under ``./data/`` relative
to the repo root. It is safe to re-run: each dataset is skipped when its
expected files are already present.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
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

CONTRACT_NLI_PAGE = "https://stanfordnlp.github.io/contract-nli/"
CONTRACT_NLI_FILES = [
    "test_segments.json",
    "test_nda_span_dims.json",
]


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
    """ContractNLI requires manual download (Stanford's NDA-licensed release)."""
    target_dir = os.path.join(_data_root(), "contract-nli")
    have_all = all(
        os.path.isfile(os.path.join(target_dir, f)) for f in CONTRACT_NLI_FILES
    )
    if have_all:
        return True, f"ContractNLI already present at {target_dir}"

    missing = [
        f for f in CONTRACT_NLI_FILES
        if not os.path.isfile(os.path.join(target_dir, f))
    ]
    msg = (
        f"ContractNLI MISSING (manual step).\n"
        f"  Why manual: the ContractNLI release page requires accepting their "
        f"data-use terms, which can't be auto-clicked.\n"
        f"  Steps:\n"
        f"    1. Open {CONTRACT_NLI_PAGE} and download the dataset archive.\n"
        f"    2. Extract it.\n"
        f"    3. Copy at least these files into {target_dir}/:\n"
        + "".join(f"         - {f}\n" for f in CONTRACT_NLI_FILES)
        + f"  Currently missing: {', '.join(missing)}"
    )
    return False, msg


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

STEPS: List[Tuple[str, Callable[[bool], Tuple[bool, str]]]] = [
    ("Phantom Wiki",  fetch_phantom_wiki),
    ("HPOBench",      fetch_hpobench),
    ("ContractNLI",   fetch_contract_nli),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify the layout; do not download anything.",
    )
    args = parser.parse_args()

    print(f"EXPGYM_DATA_ROOT   = {_data_root()}")
    print(f"PHANTOM_WIKI_ROOT  = {_phantom_wiki_root()}")
    print(f"HPOBench checkout  = {_hpobench_dir()}")
    print()

    failures: List[str] = []
    for name, step in STEPS:
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
    print("Result: all datasets ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
