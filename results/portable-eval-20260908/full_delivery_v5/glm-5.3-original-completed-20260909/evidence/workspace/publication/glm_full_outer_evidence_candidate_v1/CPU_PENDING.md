# Outer CPU candidate — pending source bindings

Only the synthetic test candidate currently exists. It has not been run. It imports a future minimally rebound prepare_metadata.py from this same new directory and replaces all source/output globals with a private TemporaryDirectory before invoking main().

Tests cover exact scope/two hash passes, refusal to overwrite, duplicate/missing scope, pin outside scope, wrong pin, symlink rejection, second-pass byte change and stat-only change. They do not invoke pack/restore/scanner/Git/network or read real source/evidence paths. Synthetic files are created and cleaned only inside the test-owned temporary directory.

The actual preparer source and fixed path/PINS mapping are pending ROOT's final closure, adopted selection/GO, and explicit scanner/controls owner proof refs. No placeholder SHA, real metadata main, actual FILES.candidate.json or HASH_RECEIPT.json has been created. See the previously reviewed selection-directory OUTER_REUSE_NOTES.md for scope and the unchanged public-controls omission.

