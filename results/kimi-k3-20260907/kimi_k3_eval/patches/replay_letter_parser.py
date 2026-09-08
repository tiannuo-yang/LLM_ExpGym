"""Offline diagnostic only: replay the four recorded Letter agent-3 replies."""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--source-root", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
source = Path(args.source_root).resolve()
sys.path.insert(0, str(source))


def deny_network(*args, **kwargs):
    raise AssertionError("Offline diagnostic prohibits network requests")


urllib.request.urlopen = deny_network
from expgym.react_loop import LLMOutput, run_react_loop
from expgym.task_tuning import build_tools
from scripts.run_paper_sweep import _score_result

evaluation = Path(__file__).resolve().parents[1]
raw_root = evaluation / "dumps/full/poolact__tuning__hpobench_paramnet_letter_steps__cost_free"
rows = []
for path in raw_root.glob("*.json"):
    content = json.loads(path.read_text())
    if content["context"].get("agent_id") == 3 and content["context"].get("strategy") == "naive" and content["state"] == "success":
        rows.append((path, content))
rows.sort(key=lambda item: item[1]["started_at_utc"])
assert len(rows) == 4, len(rows)


class RecordedLLM:
    def __init__(self):
        self.calls = 0
        self.observations_match = []

    def generate(self, messages):
        record = rows[self.calls][1]
        self.observations_match.append(messages[-1]["content"] == record["request_payload"]["messages"][-1]["content"])
        self.calls += 1
        response = record["response_json"]
        usage = response["usage"]
        return LLMOutput(text=response["choices"][0]["message"]["content"], prompt_tokens=usage["prompt_tokens"], completion_tokens=usage["completion_tokens"])


llm = RecordedLLM()
messages = rows[0][1]["request_payload"]["messages"]
tools = build_tools(tuning_task="hpobench:paramnet:letter:steps")
result = run_react_loop(llm=llm, tools=tools, time_budget=None, max_steps=30, max_evals=30, context=messages[1]["content"], system_prompt=messages[0]["content"], include_cost_in_observation=False, include_overhead_in_observation=False)
check = _score_result(result, tools, None)
report = {
    "classification": "Offline replay diagnostic; not an accepted model result",
    "network_disabled": True,
    "new_model_calls": 0,
    "recorded_replies_consumed": llm.calls,
    "observations_match_raw_requests": llm.observations_match,
    "source_root": str(source),
    "react_loop_sha256": hashlib.sha256((source / "expgym/react_loop.py").read_bytes()).hexdigest(),
    "raw_inputs": [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "request_id": record["request_id"]} for path, record in rows],
    "score_check": check,
    "result": result,
}
Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"output": args.output, "new_model_calls": 0, "calls": llm.calls, "observations_match_raw_requests": llm.observations_match, "score_check": check}, sort_keys=True))
