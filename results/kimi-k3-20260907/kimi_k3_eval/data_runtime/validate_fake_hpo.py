"""Run no-cost ExpGym and PoolAct checks for all nine real HPO evaluators."""
from __future__ import annotations

import argparse
import concurrent.futures
from functools import partial
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "LLM_ExpGym"
sys.path.insert(0, str(REPO))
from expgym.task_tuning import list_hpobench_tasks


def run_one(item, *, output_root, log_prefix):
    family, task = item
    slug = task.replace(":", "_")
    output = output_root / family / slug
    prefix = (["bash", str(HERE / "run_hpo.sh")] if ":paramnet:" in task else [str(REPO / ".venv/bin/python")])
    if family == "expgym":
        command = prefix + ["scripts/run_paper_sweep.py", "--backend", "fake", "--models", "Kimi-K3", "--scenarios", "tuning", "--tuning-tasks", task, "--cost-regimes", "cost_free,cost_moderate,cost_tight", "--tuning-reps", "1", "--max-steps", "4", "--max-evals", "3"]
    else:
        command = prefix + ["scripts/run_poolact.py", "--backend", "fake", "--model", "Kimi-K3", "--scenario", "tuning", "--tuning-task", task, "--cost-regime", "cost_tight", "--strategies", "naive,cached,poolact", "--agents", "2", "--max-steps", "4", "--max-evals", "3"]
    command += ["--output-dir", str(output), "--resume"]
    env = os.environ.copy()
    env.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    log = HERE / "logs" / ("{}_{}_{}.log".format(log_prefix, family, slug))
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as handle:
        process = subprocess.run(command, cwd=str(REPO), env=env, stdout=handle, stderr=subprocess.STDOUT)
    result = {"family": family, "task": task, "command": command, "returncode": process.returncode, "log": str(log), "output": str(output), "elapsed_seconds": time.monotonic() - started}
    try:
        assert process.returncode == 0, "Runner failed: " + str(log)
        if family == "expgym":
            files = sorted(output.rglob("traces-v2/*.json"))
            assert len(files) == 3, files
            for path in files:
                trace = json.loads(path.read_text())
                assert trace["outcome"]["validation"]["passed"] is True, path
                assert trace["outcome"]["validation"]["method"] == "repository_score_recompute", path
            result["validated_traces"] = len(files)
        else:
            files = sorted(output.rglob("result.json"))
            assert len(files) == 3, files
            assert (output / "summary.json").is_file()
            for path in files:
                content = json.loads(path.read_text())
                agents = content["agent_results"]
                assert len(agents) == 2 and all(agent["score_check"]["ok"] is True for agent in agents), path
                assert math.isfinite(content["aggregate"]["answer_perf"]), path
                assert content["implementation_sha256"], path
                if content["strategy"] == "poolact":
                    assert content["shared_state"]["graph"]["pending_claims"] == 0, path
                for agent in agents:
                    agent_path = path.parent / "agents" / ("agent_{}.json".format(agent["agent_id"]))
                    assert json.loads(agent_path.read_text()) == agent, agent_path
            result["validated_strategy_results"] = len(files)
            result["validated_agent_traces"] = 2 * len(files)
        result["passed"] = True
    except (AssertionError, KeyError, ValueError, OSError) as exc:
        result["passed"] = False
        result["error"] = str(exc)
    print(json.dumps({key: value for key, value in result.items() if key != "command"}, sort_keys=True), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=HERE / "fake_hpo_validation")
    parser.add_argument("--report-path", type=Path, default=HERE / "fake_hpo_acceptance.json")
    parser.add_argument("--log-prefix", default="fake", help="Filename prefix under data_runtime/logs.")
    args = parser.parse_args()
    if not args.log_prefix or Path(args.log_prefix).name != args.log_prefix:
        parser.error("--log-prefix must be a nonempty filename prefix without directories")
    args.output_root = args.output_root.resolve()
    args.report_path = args.report_path.resolve()
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    (HERE / "logs").mkdir(parents=True, exist_ok=True)
    tasks = [(family, task) for family in ["expgym", "poolact"] for task in list_hpobench_tasks()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(partial(run_one, output_root=args.output_root, log_prefix=args.log_prefix), tasks))
    report = {"classification": "Static/fake validation", "passed": all(item["passed"] for item in results), "output_root": str(args.output_root), "log_prefix": args.log_prefix, "jobs": results, "expected_expgym_traces": 27, "expected_poolact_strategy_results": 27, "expected_poolact_agent_traces": 54}
    args.report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
