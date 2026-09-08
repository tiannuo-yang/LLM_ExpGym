"""Compare fixed-configuration NAS semantics across native and legacy stacks."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def normalized_space(space):
    # Current ConfigSpace exposes weights=None for an unweighted categorical;
    # legacy ConfigSpace has no public weights field for that same space.
    return [{key: value for key, value in item.items() if not (key == "weights" and value is None)} for item in space]


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--native-report", type=Path, default=HERE / "hpo_nas_native_oracle.json")
parser.add_argument("--legacy-report", type=Path, default=HERE / "hpo_all_legacy_oracle.json")
parser.add_argument("--output", type=Path, default=HERE / "runtime_equivalence.json")
args = parser.parse_args()
native = json.loads(args.native_report.read_text())
legacy = json.loads(args.legacy_report.read_text())
legacy_by_name = {item["task"]: item for item in legacy["tasks"]}
checks = []
for item in native["tasks"]:
    other = legacy_by_name[item["task"]]
    fields = ["fidelity", "config", "perf", "cost", "c_base_seconds", "cost_regimes"]
    check = {"task": item["task"], "same_fields": {key: item[key] == other[key] for key in fields}, "same_parameter_space": normalized_space(item["config_space"]) == normalized_space(other["config_space"])}
    check["passed"] = item["passed"] and other["passed"] and all(check["same_fields"].values()) and check["same_parameter_space"]
    checks.append(check)
report = {"classification": "Static/fake validation", "passed": native["passed"] and legacy["passed"] and len(checks) == 6 and all(check["passed"] for check in checks), "native": {key: native[key] for key in ["python", "python_version", "numpy", "configspace"]}, "legacy": {key: legacy[key] for key in ["python", "python_version", "numpy", "configspace"]}, "nas_tasks": checks, "notes": ["Unweighted categorical weights=None is normalized to the absent legacy field.", "This validates fixed configuration scoring and parameter spaces; random ConfigSpace sampling sequences can differ across versions."]}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
raise SystemExit(0 if report["passed"] else 1)
