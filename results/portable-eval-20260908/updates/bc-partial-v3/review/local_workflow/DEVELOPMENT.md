# Candidate development history

The initial complete frozen-rule source scan failed only on the original stop
receipt's prose `authorization` field. The scan and invalid lock are retained
under `checks/failed_initial_v1/`; they are not reclassified as PASS. ROOT then
authorized only the fixed SHA/path control original, separate from unchanged
v2 shards, with fresh-directory complete assembly. No original bytes changed.

The first new assembly suite ran 28 tests: 26 passed, one fixture assertion
failed, one fixture construction errored. `test_output_symlink` correctly
rejected assembly but its helper then followed the preserved symlink and saw
the pre-existing target COMPLETE marker. The test now checks rejection and
exact preservation of that target. `test_cross_field_marker_not_exempted`
attempted string-plus-integer because schema_version was the first value;
its synthetic marker now concatenates the first two keys. No assembly or
frozen v2 implementation changes were needed for these two test corrections.

The first full real-data build completed pack, full restore, all ten independent
shard restores, fixed-control assembly and direct whole-original byte checks.
Its CSV step then raised KeyError: the original auditor intentionally omits
retained_semantic_zero_count in all 31 unstarted pool rows. The failed driver
source and diagnostic receipt are retained in checks/development_csv_failure_v1.
The CSV now explicitly uses not_applicable_no_execution for those rows, never
zero; missing that field in an executed row still rejects. A separate bounded
metadata completion script verifies all existing COMPLETE/data/source bindings
again and writes only new metadata; it does not rerun or change completed
payloads, archives, the original control receipt or frozen v2 tools.
