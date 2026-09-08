#!/usr/bin/env python3
"""Compare independently obtained aggregates with the final project inventory."""
import argparse
import hashlib
import json
import pathlib


def main():
    directory = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--independent", type=pathlib.Path, default=directory / "independent_project_usage.json")
    parser.add_argument("--inventory", type=pathlib.Path, default=directory.parent / "project_usage_final" / "project_usage_inventory.json")
    parser.add_argument("--output", type=pathlib.Path, default=directory / "comparison.json")
    args = parser.parse_args()
    inputs = {}
    reports = {}
    for name, path in (("independent", args.independent), ("inventory", args.inventory)):
        raw = path.read_bytes()
        inputs[name] = {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest()}
        reports[name] = json.loads(raw.decode("utf-8"))
    independent, inventory = reports["independent"], reports["inventory"]
    checks = []

    def check(name, actual, expected):
        checks.append({"name": name, "independent": actual, "inventory": expected, "passed": actual == expected})

    def check_totals(scope, left, right):
        for left_name, right_name in (
            ("unique_requests", "http_attempts"), ("unique_logical_generations", "unique_generations"),
            ("states", "states"), ("all_requests_terminal", "all_requests_terminal"),
            ("usage_object_missing_attempts", "usage_unreported_http_attempts"),
            ("reasoning_token_fields_conflict_attempts", "reasoning_tokens_conflicting_attempts"),
            ("nonempty_reasoning_content_attempts", "nonempty_reasoning_content_attempts"),
            ("reasoning_content_chars", "reasoning_content_chars_sum"),
            ("top_level_reasoning_zero_with_nonempty_text_attempts", "nonempty_reasoning_content_with_zero_reported_tokens_attempts"),
        ):
            check(scope + "." + left_name, left[left_name], right[right_name])
        for token in ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_input_tokens", "reasoning_tokens"):
            left_token = "selected_reasoning_tokens" if token == "reasoning_tokens" else token
            for left_field, right_suffix in (
                ("known_sum", "known_sum"), ("complete_total", "complete_total"),
                ("reported_attempts", "reported_attempts"), ("missing_attempts", "unreported_attempts"),
            ):
                check(scope + "." + token + "." + left_field,
                      left["tokens"][left_token][left_field], right[token + "_" + right_suffix])

    for left_key, right_key in (
        ("unique_raw_file_locations", "distinct_raw_file_locations"),
        ("unique_request_ids", "unique_requests"), ("duplicate_copy_locations", "duplicate_raw_file_locations"),
    ):
        check("project." + left_key, independent[left_key], inventory[right_key])
    check_totals("project.totals", independent["totals"], inventory["totals"])
    sources_by_path = {source["manifest_path"]: source for source in inventory["sources"]}
    check("manifest_paths", sorted(source["manifest_path"] for source in independent["sources"].values()), sorted(sources_by_path))
    for stage, source in independent["sources"].items():
        matched = sources_by_path[source["manifest_path"]]
        for left_key, right_key in (
            ("manifest_sha256", "manifest_sha256"), ("raw_file_locations", "raw_file_locations"),
            ("unique_request_ids", "unique_requests"), ("job_count", "manifest_jobs"),
        ):
            check(stage + "." + left_key, source[left_key], matched[right_key])
        check(stage + ".missing_dump_directories_count", len(source["missing_dump_directories"]), matched["missing_dump_directories"])
        check_totals(stage + ".totals", source["totals"], matched["totals"])
    result = {
        "schema_version": "kimi_k3.independent_inventory_comparison.v1",
        "inputs": inputs,
        "comparison_script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "all_passed": all(item["passed"] for item in checks),
        "checks_count": len(checks), "checks": checks,
        "note": "Comparison reads only already-generated reports; raw scanning was performed independently without project inventory or audit helpers.",
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"all_passed": result["all_passed"], "checks_count": len(checks), "output": str(args.output.resolve())}))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
