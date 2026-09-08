"""Capture failed score checks before the repository refuses persistence."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2] / "LLM_ExpGym"
sys.path.insert(0, str(REPO))
from scripts import run_poolact

original_score = run_poolact._score_result


def capture_score(result, tools, evaluator):
    score = original_score(result, tools, evaluator)
    if not score.get("ok"):
        path = Path(__file__).resolve().parent / "logs" / ("failed_poolact_agent_{}.json".format(result.get("agent_id")))
        path.write_text(json.dumps({"score_check": score, "result": result}, indent=2) + "\n", encoding="utf-8")
        print("Captured failed score check at " + str(path), flush=True)
    return score


run_poolact._score_result = capture_score
if __name__ == "__main__":
    sys.exit(run_poolact.main())
