# Quota pauses for scheduler-masked failures

With the opt-in quota gate configured, Gemini and Claude HTTP 503 responses
can use an existing fresh snapshot that identifies `window_quota`,
`weekly_quota`, or `model_throttle`. Without that evidence, an explicit
`no_available_accounts` error type/code/message or a “No available accounts”
message (optionally naming an account category) requests a refresh through the
shared `refresh-request.json`.
The gate waits at most 15 seconds for a fresh observation at or after that
request. The response becomes a quota pause only when that observation confirms
one of those blocked reasons. A controller must consume the refresh request
and publish sanitized snapshots; the gate does not contact the provider.

No observation, an available observation, or an unknown observation leaves the
503 on the ordinary bounded transport-retry path. An ordinary 503 without fresh
blocked evidence does not initiate this probe. HTTP 401 and ordinary 429 retain
their existing handling; a 503 message by itself never proves quota exhaustion.

A confirmed pause preserves the pending request and records the original failed
attempt before waiting. Resumption requires a fresh available snapshot after
the pause and any known reset boundary. Quota waiting affects wall time, not
the task's simulated budget. This does not restart failed jobs or reinterpret
old failed attempts using quota evidence obtained later.

Focused offline coverage is in `tests/test_quota_gate.py`. It uses fake clocks
and controlled transport responses; it does not establish live provider
compatibility or request API/GPU resources.
