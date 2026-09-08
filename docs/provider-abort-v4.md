# Provider abort handling: v4 source cohort

This is a source-only, static/fake-validated change. It is not a formal study
result, a model-quality claim, or authorization to execute a new experiment.

## Terminal aborts

After the existing response decoder succeeds, an explicit
`finish_reason="abort"` raises `APICompletionAbortedError`, a subclass of
`APIClientError`. The partial text or tool calls are retained as evidence, not
delivered as an agent decision. The client does not resample the aborted
completion, execute its partial tool calls, repair it into a final answer, or
score that partial answer.

The original response and reported usage remain associated with the failed
attempt. Earlier retryable transport attempts remain in the same attempt
history. An abort does not erase incurred work or make an unknown usage value
zero; provider-reported usage is not independent billing verification. If the
terminal dump itself fails, the error path retains the available attempt usage.

This change does not redefine other finish reasons. Existing handling of
ordinary completion, tool calls, length limits, refusals, absent or unknown
finish reasons, and transient transport retries remains unchanged. Malformed
responses still fail the existing decoder; an `abort` label does not relax its
validation.

See the [client implementation](../expgym/llm_clients.py) and the
[synthetic abort regression tests](../tests/test_provider_abort.py).

## Preserve previous evidence and source identity

The previous v3 source release remains a distinct historical version. Preserve
old result files, traces, raw attempts, failed-run diagnostics, and their original
source and request identities. Do not rewrite an old abort as a successful
completion, silently relabel old outputs as v4, or merge source cohorts without
an explicitly reviewed study design. This source patch does not authorize
replaying failed work or replacing missing performance with a zero score.

The accepted v4 source archive contains 82 files: 80 unchanged files from v3,
the modified client, and one new test file. Its runtime fingerprint covers 77
code/test files, using the existing fingerprint algorithm:

`b280a0f640ffab8aa90bc74df4c9ecf3189b375cdd674094a005b3569bb4b608`

The accepted archive SHA-256 is
`135e9ab2f912c50e22999fb9645efadd77bd8a6481eda9a4be14ee0cf98ad630`.
The archive is not embedded in this source release. This new documentation file
is outside that runtime fingerprint and is reviewed separately.

Static validation includes the existing suite plus nine synthetic abort test
methods. The recorded full check ran 576 tests with the same five explicit
skips; focused client checks passed under the native and legacy runtimes. Fake
PoolAct smoke coverage used N2, not a formal N4 study. No live model, formal
performance matrix, deployment, or final post-analysis audit is established by
these tests or by this publication candidate.

For the existing workflows, see [portable study documentation](portable-study.md)
and [PoolAct documentation](poolact.md). Their runtime and analysis limitations
remain in force; this change adds no statistical method or completed results.
