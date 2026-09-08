Static/fake validation after `evaluation_recovery_v2` was frozen.

`fake_hpo_acceptance.json` passes all nine HPO tasks: 27 ExpGym traces across all three regimes, plus 27 PoolAct strategy results / 54 agent traces under Tight with two agents. Every PoolAct graph was checked at its actual `shared_state.graph.pending_claims` field; all nine graph-bearing results report zero. All 27 PoolAct results use frozen source hash `55637cee193071b35f06c3356e706d6f652de738a5340d2c4950d5966cf1a0a3`.

`hpo_all_legacy_oracle.json` replays all nine valid oracle configurations and verifies performance, cost, determinism, fidelity, base cost, and regime budgets. `hpo_nas_native_oracle.json` repeats the six NAS tasks in the main Python environment. `runtime_equivalence.json` confirms identical NAS scores, costs, spaces, and budgets between both environments.

Commands from `kimi_k3_eval/`:

```bash
../LLM_ExpGym/.venv/bin/python data_runtime/validate_fake_hpo.py --output-root data_runtime/validation_v2/runs --report-path data_runtime/validation_v2/fake_hpo_acceptance.json --log-prefix fake_v2
../LLM_ExpGym/.venv/bin/python data_runtime/verify_hpo.py --family nas --output data_runtime/validation_v2/hpo_nas_native_oracle.json
bash data_runtime/run_hpo.sh ../kimi_k3_eval/data_runtime/verify_hpo.py --family all --output ../kimi_k3_eval/data_runtime/validation_v2/hpo_all_legacy_oracle.json
../LLM_ExpGym/.venv/bin/python data_runtime/compare_runtimes.py --native-report data_runtime/validation_v2/hpo_nas_native_oracle.json --legacy-report data_runtime/validation_v2/hpo_all_legacy_oracle.json --output data_runtime/validation_v2/runtime_equivalence.json
```

Logs are under `../logs/` with the `fake_v2_` prefix or `_v2.log` suffix. Earlier fake outputs and reports remain preserved. No LLM_ExpGym source files were changed during this validation.
