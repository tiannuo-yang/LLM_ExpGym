# Candidate: exact canonical JSON evaluation association

Status: static/fake validation only. This candidate is staged in `data_runtime/json_lookup_fix_P9OUu1`; the frozen `LLM_ExpGym` source was not changed by this work. No model calls, GPU jobs, or resume were performed.

Patch: `patches/json_eval_exact_lookup_fix.patch` (SHA256 `b9591095ef4e54a4ad06c372c1efc14dce9f0e6e8926887baa80374beeacbc83`). `git apply --check` passes against the frozen repo. Parent must apply only after the running version has drained.

## Scope and behavior

The only production change is `_lookup_answer_metrics`: when an evaluation has `canonical_argument is not None`, a final answer must have the same complete canonical JSON to associate that record's performance and overhead. A malformed final answer containing a configuration as a substring no longer inherits that configuration's metrics. The label parser, model prompts, scoring implementation, oracle data, budgets, and fallback implementation are unchanged.

| Case | Candidate behavior |
| --- | --- |
| Complete already-evaluated JSON object/list, including different whitespace/key order | Preserves the selected configuration's score and overhead; latest equivalent record wins. |
| Complete evaluated lower or zero-scoring configuration | Preserves that selected score, even if a higher eligible evaluation exists. |
| Malformed JSON/prose containing an evaluated configuration, including multiple `Answer:` labels | Does not associate by substring; the original `best_evaluated_fallback` selects the best eligible record. |
| Complete valid but previously unseen configuration with eligible evaluations | Original best-evaluated fallback remains unchanged. |
| No eligible evaluations | No runtime fallback is invented. Existing offline final-answer scoring remains: valid final configurations can score; invalid finals score zero. |
| Over-budget evaluation, including reaching the budget boundary | Not inserted into eligible `eval_records`; withheld observations cannot become fallback candidates. A prior visible zero remains eligible. |
| Legacy non-JSON identifier such as `cfg_1` | Original substring behavior is preserved; a JSON final does not gain a new legacy-identifier match. |

Actual HPO valid configurations are dict/list JSON. Numeric two-tuples and message/performance/cost three-tuples enter eligible records only after the loop's budget check. A degenerate NAS configuration with an explicit numeric zero is eligible; invalid JSON/configuration returns with no numeric performance, or caught tool exceptions, do not create such records. Search/Audit tools return textual observations rather than numeric HPO evaluation records, so this condition does not alter their final-answer path.

Canonical comparison remains the existing JSON normalization, not a new semantic ConfigSpace equivalence. Numeric spelling differences such as `1` versus `1.0`, equivalent dict/list encodings, and added fidelity fields retain their prior behavior.

Fallback can select a higher-scoring eligible record than a configuration merely quoted inside malformed prose. This is the original fallback rule, not a new scorer. Consequently final answer text, associated `answer_overhead`, answer-source provenance, PoolAct end records, winner selection, and result dumps can differ. Do not claim byte invariance of corrected results. Cumulative tool cost, number of evaluations, and model-visible observations are not changed by this final association condition.

## Verification

Five regression methods (with subcases) cover objects/lists, key order, zero scores, duplicate canonical records, legacy non-JSON identifiers, malformed/multiple answers, valid unseen answers, eligible-vs-withheld fallback, and the no-eligible-evaluation offline scoring boundary. All existing react-loop tests remain included.

From the staged source directory:

```sh
/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/.venv/bin/python -m unittest tests.test_react_loop tests.test_json_answer_lookup -v
/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/data_runtime/.venv-hpo/bin/python -m unittest tests.test_react_loop tests.test_json_answer_lookup -v
```

Both Python 3.11 and Python 3.7 pass 51 tests. Full logs: `patches/json_eval_exact_lookup_fix.native_test.log` and `patches/json_eval_exact_lookup_fix.legacy_test.log`.

Independent read-only rule audit exercised twelve before/after loop scenarios and additional canonical/offline boundaries. The actual six-response NAS101C/moderate/naive-agent3 replay is owned by `audit_report`: `reports/nas101c_moderate_agent3_diagnostic/evidence.json` and adjacent `replay.py`. It reproduces all six original request message sequences and the same five evaluation/tool records. Old lookup reports `0.9388020833333334` for malformed final JSON that independently recomputes to zero; exact-JSON lookup invokes the existing fallback, whose valid configuration independently recomputes to `0.9388020833333334` (associated cost `3023.324951171875`). No LLM request is made in replay.

Frozen live-file SHA256 values, reconfirmed after candidate validation:

```text
9d1b9d3400f044cfe69b420a805f5738a57e8ce4cb38d1f1a741d942ee46f384  expgym/react_loop.py
3b9570531161e161b4f4f8e5dbc4182852deb1b6f2a6180580e7dede905d9890  scripts/run_paper_sweep.py
0b48a7453a8c8e4ef715307ec947a91da8f4f3712d31726744a95fb6a8f833fc  expgym/task_tuning.py
```
