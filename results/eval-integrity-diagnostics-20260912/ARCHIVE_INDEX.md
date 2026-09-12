# Portable diagnostic archive index

Diagnostic subset only; not a completed formal matrix. Original failures and unknown costs are retained.

[Original-to-public mapping](RAW_INDEX.json) · [Export index](INDEX.json) · [Archive manifest](payload/manifest.json)

## Download

- [part-000001.tar.gz](payload/part-000001.tar.gz)

Use the published `scripts/package_run.py verify --require-public-scan` with the downloaded manifest/archives. Restore only explicitly selected members when needed.

## Task groups

- `glm-5_3-graph-v4-20260912-nas101_a-poolact` — `originals/graph_smoke/runs/glm-5_3-graph-v4-20260912-nas101_a-poolact/`; status `validated_complete`
- `glm-5_3-graph-v4-20260912-audit_q0-poolact` — `originals/graph_smoke/runs/glm-5_3-graph-v4-20260912-audit_q0-poolact/`; status `validated_complete`
- `glm-5_3-graph-v4-20260912-nas101_a-matched-naive` — `originals/graph_smoke/matched_strategies/runs/glm-5_3-graph-v4-20260912-nas101_a-matched-naive/`; status `validated_complete`
- `glm-5_3-graph-v4-20260912-nas101_a-matched-cached` — `originals/graph_smoke/matched_strategies/runs/glm-5_3-graph-v4-20260912-nas101_a-matched-cached/`; status `validated_complete`
- `glm-5_3-graph-v4-20260912-audit_q0-matched-naive` — `originals/graph_smoke/matched_strategies/runs/glm-5_3-graph-v4-20260912-audit_q0-matched-naive/`; status `not_started_infra_budget`
- `glm-5_3-graph-v4-20260912-audit_q0-matched-cached` — `originals/graph_smoke/matched_strategies/runs/glm-5_3-graph-v4-20260912-audit_q0-matched-cached/`; status `not_started_infra_budget`
- `deepseek-v4-flash-0731-graph-v4-20260912-nas101_a-streamoff-poolact` — `originals/graph_smoke/streamoff/cohort_v1/runs/deepseek-v4-flash-0731-graph-v4-20260912-nas101_a-streamoff-poolact/`; status `validated_complete`
- `deepseek-v4-flash-0731-graph-v4-20260912-audit_q0-streamoff-poolact` — `originals/graph_smoke/streamoff/cohort_v1/runs/deepseek-v4-flash-0731-graph-v4-20260912-audit_q0-streamoff-poolact/`; status `validated_complete`
- `deepseek-v4-flash-0731-graph-v4-20260912-nas101_a-streamoff-matched-naive` — `originals/graph_smoke/streamoff/cohort_v1/matched_runs/deepseek-v4-flash-0731-graph-v4-20260912-nas101_a-streamoff-matched-naive/`; status `validated_complete`
- `deepseek-v4-flash-0731-graph-v4-20260912-nas101_a-streamoff-matched-cached` — `originals/graph_smoke/streamoff/cohort_v1/matched_runs/deepseek-v4-flash-0731-graph-v4-20260912-nas101_a-streamoff-matched-cached/`; status `validated_complete`
- `deepseek-v4-flash-0731-graph-v4-20260912-audit_q0-streamoff-matched-naive` — `originals/graph_smoke/streamoff/cohort_v1/matched_runs/deepseek-v4-flash-0731-graph-v4-20260912-audit_q0-streamoff-matched-naive/`; status `validated_complete`
- `deepseek-v4-flash-0731-graph-v4-20260912-audit_q0-streamoff-matched-cached` — `originals/graph_smoke/streamoff/cohort_v1/matched_runs/deepseek-v4-flash-0731-graph-v4-20260912-audit_q0-streamoff-matched-cached/`; status `validated_complete`
- `glm-5_3-graph-v4-audit-cont-20260912-audit_q0-poolact` — `originals/graph_smoke/glm_audit_continuation/runs/glm-5_3-graph-v4-audit-cont-20260912-audit_q0-poolact/`; status `validated_complete`
- `glm-5_3-graph-v4-audit-cont-20260912-audit_q0-matched-naive` — `originals/graph_smoke/glm_audit_continuation/runs/glm-5_3-graph-v4-audit-cont-20260912-audit_q0-matched-naive/`; status `validated_complete`
- `glm-5_3-graph-v4-audit-cont-20260912-audit_q0-matched-cached` — `originals/graph_smoke/glm_audit_continuation/runs/glm-5_3-graph-v4-audit-cont-20260912-audit_q0-matched-cached/`; status `validated_complete`

## Replay groups

- `baseline-tp8-c1` — `originals/baseline-tp8-c1/` (JSON body aliases preserve exact bytes).
- `original-order-v2-c1` — `originals/original-order-v2-c1/` (JSON body aliases preserve exact bytes).
- `original-order-v2-c4` — `originals/original-order-v2-c4/` (JSON body aliases preserve exact bytes).
- `multistream-off-v2-c4` — `originals/multistream-off-v2-c4/` (JSON body aliases preserve exact bytes).
- `multistream-off-v2-c4-after-smokes` — `originals/multistream-off-v2-c4-after-smokes/` (JSON body aliases preserve exact bytes).

## Other evidence

The mapping lists every selected plan, source audit, fidelity, candidate, control and release file by role and member path. Original local navigation is preserved inside the archive; it is historical provenance, not a portable hyperlink map. Five CSVs retain original source-path identities; use RAW_INDEX.json to locate their public members.

Old formal archives are referenced by the reports, not repackaged here.
