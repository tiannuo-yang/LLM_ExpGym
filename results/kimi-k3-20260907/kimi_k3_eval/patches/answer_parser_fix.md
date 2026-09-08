The patch changes only `_extract_answer`'s label recognition: after the existing Markdown/whitespace normalization, `Answer:` must start the line. Existing extraction of the remaining multiline answer is unchanged.

The regression reproduces the observed Letter/free/naive agent-3 protocol quotation followed by a valid final configuration. A second regression confirms that an inline protocol reference alone does not terminate the loop as a natural answer; the existing missing-action path still requests a forced answer. Existing normal, Markdown, bullet, and multiline answer tests remain in place.

Validation was performed in the isolated source copy `data_runtime/parser_fix_VLpRJo`, without modifying the running repository. All 46 `tests.test_react_loop` tests passed in both Python 3.11.15 and Python 3.7.12. See `answer_parser_fix.native_test.log` and `answer_parser_fix.legacy_test.log`. From the original repository, `git apply --check ../kimi_k3_eval/patches/answer_parser_fix.patch` passed.

`letter_parser.before_replay.json` and `letter_parser.after_replay.json` replay exactly the same four successful recorded replies with network access disabled. All four reconstructed observations match the original request messages in both replays. Before the patch, the reported score is `0.7092944375216987` but recomputation is missing because the extracted answer contains quoted prose. After the patch, reported and recomputed performance both equal `0.7092944375216987`, with `score_check.ok=true`.

These replay JSON files are diagnostic evidence, not accepted experimental results. They are separate from all `runs/` outputs and contain the four original request IDs and input SHA256 values. No new model calls were made.
