# Qwen study CPU inputs and launchers

This is CPU preparation, **not a Qwen/model run**. No download, model request,
GPU computation, Slurm submission, dependency installation, or changes to the
old source/environment/API studies were made by this preparation.

## Data identity

`../data` contains 249 physically copied files / 240,303,980 bytes. Every copied
file was SHA256-checked once against the existing frozen inventory; no hard
links or symlinks were used. Files are 0444, directories 0555. The single
[data_inventory.json](data_inventory.json) includes all relative paths, sizes,
hashes and the source inventory's identity:
`0dcd364d3642ddd76dff4e492855fc8a60059a2cda6f243ec65fe742290b64b7`.

The source was `LLM_ExpGym_api_studies_20260910/data`, originally copied from
`LLM_ExpGym/data`. Mutable old caches, bytecode and download locks were excluded
by that source inventory. [prepare_data.py](prepare_data.py) is a study-specific,
one-time copy program; rerunning it refuses the existing destination. Do not
recopy or rehash all inputs on each worker launch.

## Execution contract

Both executable wrappers change directory to
`/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym-qwen38-20260910` and preserve
the supplied Python arguments. They do not install anything or alter the reused
environments:

| Wrapper | Interpreter | Uses |
| --- | --- | --- |
| [python_main](python_main) | `LLM_ExpGym/.venv/bin/python`, 3.11.15 | NAS, Search, Audit, queue planning |
| [python_hpo](python_hpo) | `kimi_k3_eval/data_runtime/.venv-hpo/bin/python`, 3.7.12 | ParamNet |

These interpreter paths point to reused runtimes, **not old evaluator source**.
`PYTHONPATH`, `EXPGYM_SOURCE_REPO` and cwd select the new source repository.
`EXPGYM_DATA_ROOT`, `PHANTOM_WIKI_ROOT`, `HPOBENCH_ROOT` and `XDG_DATA_HOME` select
this study's new immutable data/HPOBench source. Threaded CPU libraries are
limited to one thread; user site and bytecode writes are disabled. The local
service's no-auth placeholder overrides inherited `OPENAI_API_KEY`; no key file
is created/read by the wrappers. This study wrapper is **no-auth-only**. The
current runners prefer the environment over `--api-key-file`, so authenticated
service configuration is not supported by this wrapper; a future authenticated
study must choose a separately reviewed credential contract.

The current budget loader and evaluation identity still intentionally use the
tracked `source_repo/data/hpo_tuning/oracle3.json`. Both this file and the external
data copy must match SHA256
`f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e`.
Every wrapper launch checks these two small files and refuses missing/changed
oracle data, preventing the loader's silent fallback to a base cost of 100.
No generic source behavior was changed and no source/data symlink was needed.

For a real worker, the queue supplies absolute, study-local
`EXPGYM_API_DUMP_DIR` and its own `EXPGYM_RUN_ID`. The wrapper does not replace
the run ID or dump directory. Mutable HPO state is confined to:

```text
<job>/api_dump/                     # queue-owned model dumps
<job>/runtime/hpobench/config/.hpobenchrc
<job>/runtime/hpobench/cache/
<job>/runtime/hpobench/sockets/
```

Different queue jobs have different parent directories. An incompatible
existing `.hpobenchrc` or symlinked runtime path is rejected, not overwritten.
Re-entry keeps compatible configuration bytes and modification time unchanged.
Configuration initialization is intended for the queue's single owner per job;
do not manually launch two workers into the same invocation.

Help/version checks and the explicit `--expgym-runtime-identity` probe work with
no dump directory and do not create state, even if a dump variable is inherited.
The script-help exception only admits the three listed production runner CLIs,
with optional `-B`/`-s`; it does not admit arbitrary scripts or `-c` via other
interpreter options. Arbitrary HPO `-c`, scripts and worker
execution require a valid absolute dump. Native planning may run without a
dump; HPO mutable fallback paths then point inside the read-only data tree so
an accidental evaluator initialization cannot use another study's cache.

```bash
/lustrefs/users/chufan.shi/codex_space_tn/qwen38_eval_20260910/study/python_hpo --expgym-runtime-identity
/lustrefs/users/chufan.shi/codex_space_tn/qwen38_eval_20260910/study/python_main -B /lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym-qwen38-20260910/scripts/run_study_queue.py --help
```

Formal workers use the queue's `<wrapper> -B <new-source>/scripts/run_study_queue.py
worker ...` contract; the coordinator owns the frozen plan and endpoint.

## Checks already run

- [test_cpu_runtime.py](test_cpu_runtime.py): 9 focused tests passed, including
  both runtimes' identity/help, missing/relative/outside-study dump rejection,
  per-job cache/config/socket isolation, argument/run-ID preservation, unchanged
  configuration on re-entry, incompatible configuration rejection, symlink
  rejection, and missing/modified oracle refusal.
- [validation/cpu_main.json](validation/cpu_main.json): all 6 NAS fixed oracle
  configurations matched performance, cost, fidelity and all three budgets;
  PhantomWiki seed 2/3 selected 36/37 questions; Audit selected document IDs
  1, 2, 4, 5, 6, 8, 11, 18, 21, 22, 23, 24, 25 with 17 cc-large hypotheses.
- [validation/cpu_hpo.json](validation/cpu_hpo.json): adult/higgs/letter ParamNet
  fixed configurations matched performance, cost, fidelity and all three
  budgets in the reused legacy runtime, importing this study's HPOBench copy.

[probe_cpu_loaders.py](probe_cpu_loaders.py) blocks HTTP and socket connection
attempts. The main probe initially rejected an overly strict test assumption
that `size_5000` meant exactly 5,000 articles; the actual immutable files have
5,029/5,039 article rows. The corrected check compares loader counts to parquet
row metadata and passed. No benchmark input or evaluator was changed for this.
The legacy import prints a pandas/download-capability warning; no download is
needed for the existing ParamNet tables and the offline probe passed.

These results establish CPU input/scorer readiness, not model tool correctness,
serving performance or scientific outcome. CPU probe state is under
`study/validation/`, separate from formal queue invocations. Source/plan freezing
and model smoke validation remain the coordinator's responsibility.
