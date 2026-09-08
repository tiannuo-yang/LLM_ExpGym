"""Require identical fake commands to skip and preserve accepted trace bytes."""
import concurrent.futures
import hashlib
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "LLM_ExpGym"
acceptance = json.loads((HERE / "fake_hpo_acceptance.json").read_text())
assert acceptance["passed"]


def check(job):
    output = Path(job["output"])
    paths = sorted(output.rglob("traces-v2/*.json")) if job["family"] == "expgym" else sorted(path for path in output.rglob("*.json") if path.name == "result.json" or path.parent.name == "agents")
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    env = os.environ.copy()
    env.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    completed = subprocess.run(job["command"], cwd=str(REPO), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    log = HERE / "logs" / ("resume_{}_{}.log".format(job["family"], job["task"].replace(":", "_")))
    log.write_text(completed.stdout, encoding="utf-8")
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    skip_count = completed.stdout.count("skip verified") if job["family"] == "expgym" else completed.stdout.count("[resume]")
    result = {"family": job["family"], "task": job["task"], "returncode": completed.returncode, "verified_skip_count": skip_count, "preserved_artifacts": len(paths), "all_artifacts_byte_identical": before == after, "log": str(log)}
    result["passed"] = completed.returncode == 0 and skip_count == 3 and "rerun" not in completed.stdout and "[run]" not in completed.stdout and before == after
    print(json.dumps(result, sort_keys=True), flush=True)
    return result


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(check, acceptance["jobs"]))
report = {"classification": "Static/fake validation", "passed": all(item["passed"] for item in results), "jobs": results, "verified_skips": sum(item["verified_skip_count"] for item in results), "preserved_artifacts": sum(item["preserved_artifacts"] for item in results)}
(HERE / "fake_resume_acceptance.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
raise SystemExit(0 if report["passed"] else 1)
