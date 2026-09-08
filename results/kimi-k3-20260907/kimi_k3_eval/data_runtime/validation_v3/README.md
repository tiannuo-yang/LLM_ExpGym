# Static/fake validation — evaluation recovery v3

All nine HPO tasks pass. This is infrastructure validation with deterministic fake model replies, not measured Kimi-K3 performance. The model label is `Kimi-K3`, but every run explicitly used `--backend fake`; no provider requests or GPU jobs were created.

- ExpGym: 27 schema-valid traces, nine tasks × Free/Moderate/Tight, one repetition, four steps and three evaluations maximum. Every trace passes repository score recomputation and terminal `score_check=ok`.
- PoolAct: 27 strategy results and 54 matching per-agent files, nine tasks × naive/cached/poolact under Tight, two agents, four steps and three evaluations maximum. Every per-agent score check passes, aggregate scores are finite, and all nine coordination graphs have `shared_state.graph.pending_claims == 0`.
- Every result matches frozen source `c4e622baff06e111b7baedcb05fdeb65b10a315582e76a2e112f6e73dfb0069e` from `provenance/evaluation_recovery_v3/manifest.json`.
- Oracle scoring was rerun, not copied: nine legacy HPO and six native NAS tasks all pass performance, cost, determinism, fidelity, explicit oracle base-cost lookup, and Free/10×/3× regime budgets. Six NAS tasks have identical fixed-configuration scores, costs, full parameter spaces and budgets in both environments.

ParamNet uses the isolated uv legacy evaluator, Python 3.7.12 / NumPy 1.18.5 / ConfigSpace 0.4.21. NAS fake runs use the main Python 3.11.15 / NumPy 2.4.6 / ConfigSpace 1.2.1 environment. Docker is not used. Cross-version random sampling sequences are not asserted equal; equivalence checks use fixed valid oracle configurations.

Primary evidence:

- `fake_hpo_acceptance.json`: exact commands, exit statuses, logs and per-task counts.
- `artifact_integrity.json`: independent schema/source/settings checks and SHA256 for all primary result/trace files; reproduced by `check_artifacts.py`.
- `hpo_all_legacy_oracle.json`, `hpo_nas_native_oracle.json`, `runtime_equivalence.json`: fresh deterministic oracle and environment-comparison evidence.
- `data_integrity.json`: independent dataset/provenance verification passes: all 46 manifest-listed files / 234,062,035 bytes match their original SHA256 and size; all 58 source-bundle files match live files and the source hash recomputes to the v3 identity.
- `evidence_v2_preserved_before.json` and `evidence_v2_preserved_after.json`: all 122 v2 files / 2,170,579 bytes remain identical over the explicitly recorded post-run audit window. These are not a retroactive before/after proof covering the earlier v3 run window.

Commands from `kimi_k3_eval/`:

```sh
../LLM_ExpGym/.venv/bin/python data_runtime/validate_fake_hpo.py --output-root data_runtime/validation_v3/runs --report-path data_runtime/validation_v3/fake_hpo_acceptance.json --log-prefix fake_v3
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ../LLM_ExpGym/.venv/bin/python data_runtime/verify_hpo.py --family nas --output data_runtime/validation_v3/hpo_nas_native_oracle.json
bash data_runtime/run_hpo.sh ../kimi_k3_eval/data_runtime/verify_hpo.py --family all --output ../kimi_k3_eval/data_runtime/validation_v3/hpo_all_legacy_oracle.json
../LLM_ExpGym/.venv/bin/python data_runtime/compare_runtimes.py --native-report data_runtime/validation_v3/hpo_nas_native_oracle.json --legacy-report data_runtime/validation_v3/hpo_all_legacy_oracle.json --output data_runtime/validation_v3/runtime_equivalence.json
../LLM_ExpGym/.venv/bin/python data_runtime/validation_v3/check_artifacts.py
```

Runner logs are under `data_runtime/logs/fake_v3_*.log`. All runner output paths were new `validation_v3/runs` paths. No previous validation directory or live repository source was edited. Real smoke and full-model studies remain separate parent-runner work.
