"""Read-only checks of this fake run's schema, source identity and settings."""
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[1]
REPO = STUDY.parent / "LLM_ExpGym"
sys.path.insert(0, str(REPO))
from expgym.trace_v2 import validate_trace_v2

source = json.loads((STUDY / "provenance/evaluation_recovery_v3/manifest.json").read_text())["source_tree_sha256"]
acceptance = json.loads((HERE / "fake_hpo_acceptance.json").read_text())
assert acceptance["passed"] and len(acceptance["jobs"]) == 18
rows = []
for job in acceptance["jobs"]:
    output = Path(job["output"])
    assert output.is_relative_to(HERE / "runs")
    assert Path(job["log"]).name.startswith("fake_v3_")
    if job["family"] == "expgym":
        files = sorted(output.rglob("traces-v2/*.json"))
        assert len(files) == 3
        wrote_lines = [line for line in Path(job["log"]).read_text().splitlines() if line.strip().startswith("wrote ")]
        assert len(wrote_lines) == 3 and all("score_check=ok" in line for line in wrote_lines)
        regimes = set()
        for path in files:
            content = json.loads(path.read_text())
            validate_trace_v2(content)
            assert content["provenance"]["repository"]["source_tree_sha256"] == source
            assert content["run"]["backend"]["name"] == "fake"
            assert content["run"]["model"]["id"] == "Kimi-K3"
            assert content["run"]["resume_key"]
            assert content["task"]["item"]["id"] == job["task"]
            assert content["task"]["limits"]["max_steps"] == 4
            assert content["task"]["limits"]["max_evaluations"] == 3
            assert content["outcome"]["validation"]["passed"] is True
            regimes.add(content["task"]["budget"]["regime"])
        assert regimes == {"cost_free", "cost_moderate", "cost_tight"}
    else:
        files = sorted(output.rglob("result.json"))
        assert len(files) == 3
        assert (output / "summary.json").is_file()
        strategies = set()
        for path in files:
            content = json.loads(path.read_text())
            assert content["implementation_sha256"]["source_tree"] == source
            config = content["config"]
            assert config["backend"] == "fake" and config["model"] == "Kimi-K3"
            assert config["tuning_task"] == job["task"]
            assert config["cost_regime"] == "cost_tight" and config["agents"] == 2
            assert config["max_steps"] == 4 and config["max_evals"] == 3
            assert math.isfinite(content["aggregate"]["answer_perf"])
            assert len(content["agent_results"]) == 2
            for agent in content["agent_results"]:
                assert agent["score_check"]["ok"] is True
                agent_path = path.parent / "agents" / ("agent_{}.json".format(agent["agent_id"]))
                assert json.loads(agent_path.read_text()) == agent
            if content["strategy"] == "poolact":
                assert content["shared_state"]["graph"]["pending_claims"] == 0
            strategies.add(content["strategy"])
        assert strategies == {"naive", "cached", "poolact"}
    rows.append({"family": job["family"], "task": job["task"], "passed": True,
                 "files": [{"path": str(p.relative_to(HERE)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]})
print(json.dumps({"classification": "Static/fake validation", "passed": True,
                  "source_tree_sha256": source, "jobs": rows,
                  "expgym_traces": 27, "poolact_results": 27,
                  "poolact_agent_traces": 54, "poolact_graphs_with_zero_pending_claims": 9}, indent=2, sort_keys=True))
