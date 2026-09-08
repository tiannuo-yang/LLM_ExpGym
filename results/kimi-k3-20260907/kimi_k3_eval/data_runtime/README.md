# Data and HPO evaluator acceptance

Current acceptance entry point: [validation_v3/README.md](validation_v3/README.md). It records the fresh nine-task fake ladder, oracle replay, native/legacy equivalence, dataset checks and source identity for `evaluation_recovery_v3` (`c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e`).

Classification: **Static/fake validation**. These artifacts validate the datasets and evaluators; they are not Kimi-K3 model results. The root-level oracle/fake reports and `validation_v2/` are historical evidence, not the current acceptance. Do not overwrite them or the dataset manifest: formal provenance and audits refer to their existing bytes.

## Data and evaluator environments

All datasets are installed under `../../LLM_ExpGym/data/`. `dataset_manifest.json` records 46 actual data/configuration file hashes (234,062,035 bytes), the pinned upstream revisions, selected question/document identities, table cardinalities, finite metrics, complete NAS201 key coverage, and official NAS oracle minima. Search resolves 35 seed-1 questions, including the 18 whois questions used by the PoolAct paper subset. Audit resolves the expected 13 document IDs and bundled hints. The ContractNLI archive is not checksum-pinned upstream by the repository; this run records the downloaded test file's observed SHA256.

Docker is installed but its daemon socket denies this user's access. The independent legacy environment uses a conda-forge Python 3.7.12 interpreter, with its packages installed and locked through uv. No system daemon or pre-existing environment was changed.

| Workload | Interpreter | Evaluator dependencies |
| --- | --- | --- |
| Search, Audit, NAS101/201 | `../../LLM_ExpGym/.venv/bin/python` | Python 3.11.15, NumPy 2.4.6, ConfigSpace 1.2.1 |
| ParamNet | `bash run_hpo.sh SCRIPT ARGS...` | Python 3.7.12, NumPy 1.18.5, SciPy 1.4.1, scikit-learn 0.23.2, ConfigSpace 0.4.21 |

`run_hpo.sh` sets the repository working directory, Python import path, HPOBench source/data/cache paths, an isolated XDG configuration directory, and one BLAS thread. It accepts any repository Python entry point, including both `scripts/run_paper_sweep.py` and `scripts/run_poolact.py`. Use the wrapper when scheduling ParamNet rather than invoking its Python without the corresponding environment.

The current nine-task replay is [validation_v3/hpo_all_legacy_oracle.json](validation_v3/hpo_all_legacy_oracle.json): fixed-fidelity performance and evaluation cost match the repository oracle, repeated evaluation is deterministic, and each task's base cost explicitly matches the existing oracle key. Cost budgets use no ceiling for Free, 10 times base cost for Moderate, and 3 times base cost for Tight. The oracle is a stored sampled best configuration, not a proof of a global optimum.

[validation_v3/runtime_equivalence.json](validation_v3/runtime_equivalence.json) verifies all six NAS tasks under both interpreters: identical fixed-configuration scores, costs, fidelities, base costs, budgets, and parameter spaces. An absent legacy categorical `weights` field and the current API's `weights=None` both denote uniform choices and are normalized for comparison. Random sampling sequences need not match across ConfigSpace versions.

## Safe inspection of the accepted evidence

Run these read-only checks from `kimi_k3_eval/`; they print to the terminal and do not replace existing reports. `--check` does not download or repair missing data. Disabling bytecode writes also avoids modifying import caches.

```bash
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 ../LLM_ExpGym/.venv/bin/python ../LLM_ExpGym/scripts/download_data.py --check
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 ../LLM_ExpGym/.venv/bin/python data_runtime/validation_v3/check_artifacts.py
```

The second command validates accepted v3 fake traces/results, settings, source identity and pending-claim state without rerunning their agents. Historical v3 command listings describe how those artifacts were created; do not copy their fixed output paths for another run.

For full-study resume byte/set auditing, see [RESUME_INTEGRITY.md](RESUME_INTEGRITY.md). Its `full_v2` names are historical examples: the coordinator must choose the current manifest and new report names after every job is quiescent. `resume_integrity.py` never executes resume itself. The full-v3 final resume remains a separate coordinator action; do not run it from these data-check instructions.

## Optional fresh offline validation

If new oracle or fake-run evidence is needed, wait until the active study finishes, then use a newly created directory. All commands below run from `kimi_k3_eval/`; each report path is explicit, and the legacy wrapper receives an absolute output path because it changes directory. These commands do not call a model provider.

```bash
HPO_RECHECK_DIR="$(mktemp -d "$PWD/data_runtime/recheck.XXXXXXXX")" || exit 1
HPO_RECHECK_LOG_PREFIX="fake_$(basename "$HPO_RECHECK_DIR")"
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 ../LLM_ExpGym/.venv/bin/python data_runtime/inventory_data.py --output "$HPO_RECHECK_DIR/dataset_manifest.json"
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ../LLM_ExpGym/.venv/bin/python data_runtime/verify_hpo.py --family nas --output "$HPO_RECHECK_DIR/hpo_nas_native_oracle.json"
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 bash data_runtime/run_hpo.sh ../kimi_k3_eval/data_runtime/verify_hpo.py --family all --output "$HPO_RECHECK_DIR/hpo_all_legacy_oracle.json"
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 ../LLM_ExpGym/.venv/bin/python data_runtime/compare_runtimes.py --native-report "$HPO_RECHECK_DIR/hpo_nas_native_oracle.json" --legacy-report "$HPO_RECHECK_DIR/hpo_all_legacy_oracle.json" --output "$HPO_RECHECK_DIR/runtime_equivalence.json"
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 ../LLM_ExpGym/.venv/bin/python data_runtime/validate_fake_hpo.py --output-root "$HPO_RECHECK_DIR/fake_runs" --report-path "$HPO_RECHECK_DIR/fake_hpo_acceptance.json" --log-prefix "$HPO_RECHECK_LOG_PREFIX"
```

The fake helper creates logs under `data_runtime/logs/` with that unique prefix and passes runner `--resume` only against the new fake-run directory; this is not a full-study resume. Retain the new directory for review. Do not run `validate_fake_hpo.py` or `compare_runtimes.py` with their defaults, which point at historical outputs. A newly generated inventory is additional evidence, not a replacement for the original manifest.

Oracle and fake execution are not strictly read-only operations: HPOBench initialization can create missing configuration/cache directories, and its upstream loader can download missing surrogate data. Use the already-verified complete dataset/environment, or run in a separate reconstruction workspace if the initial read-only check fails; do not repair the authoritative dataset during an active study.

`verify_fake_resume.py` has no argument parser, including no safe `--help`: it reads the root-level historical `fake_hpo_acceptance.json`, reruns its stored commands, and writes fixed `logs/resume_*.log` and `fake_resume_acceptance.json` paths. It is a historical reproduction helper, not a safe current-directory inspection command. Source changes can cause its stored commands to rerun and replace old results. Its historical byte check covers pre-enumerated trace/result/agent files, not added files, summaries or raw dumps. Do not execute it in this authoritative workspace.

## Environment reconstruction and limitations

The legacy rebuild entry point is `bash data_runtime/bootstrap_legacy.sh` from `kimi_k3_eval/`, but use it only in a separate reproduction workspace with the same sibling `LLM_ExpGym/` and `kimi_k3_eval/` layout, never while the authoritative environment is serving a study. It installs into fixed `data_runtime/bootstrap/` and `.venv-hpo/` paths, changes installed packages/editable HPOBench, and rewrites `requirements-hpo.freeze.txt`; it has no alternate-root CLI and is not read-only.

`requirements-hpo.lock` pins packages and distribution hashes; `requirements-hpo.freeze.txt` records installed versions, including the editable pinned HPOBench checkout. `python37-conda-explicit.lock` records the interpreter's conda package URLs. The bootstrap script requests Python 3.7.12 from conda-forge when the interpreter is absent; it does not itself replay that explicit interpreter lock. Preserve the original lock/freeze files as evidence and verify a reconstructed environment separately. Installation, data conversion, oracle replay, native HPO tests, and fake jobs retain their historical logs under `logs/`.

## Historical initial acceptance

Before the later v2/v3 recovery freezes, the initial ladder passed 27 sequential traces (nine tasks, three cost regimes, one repeat) and 27 PoolAct strategy results / 54 agent traces (nine tasks, Tight, all three strategies, two agents), with four steps and three evaluations. Root-level `fake_hpo_acceptance.json` records that initial run's commands and paths; `fake_resume_acceptance.json` records its then-compatible verified skips and byte preservation. Neither is a resume guarantee for the current source.

The initial fake validation exposed a forced-answer bug after an over-budget first observation for ParamNet adult. Its rejected diagnostic result is retained at `logs/failed_poolact_agent_1.json`; it is not an accepted trace or model score. The root agent corrected FakeLLM's forced-answer response handling before that initial acceptance ladder.

Native ConfigSpace 1.2.1 also exposed a fake-plan serialization issue for NAS101 A/B: categorical choices can be NumPy integer scalars. `build_fake_plan` converts NumPy scalars to the corresponding Python JSON primitives. Its regression tests cover integer/float/boolean/string types and valid configurations from all NAS101 variants. At the initial validation stage, both interpreters passed all 11 then-enabled HPO tests, recorded in `logs/native_hpo_tests.log` and `logs/legacy_hpo_tests.log`; these are historical test counts, not the current full-suite total.
