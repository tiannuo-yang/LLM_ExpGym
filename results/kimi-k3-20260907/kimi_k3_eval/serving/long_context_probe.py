"""Check long-context output integrity and retrieval; retain complete inputs."""
import argparse
import datetime
import json
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--deployment", type=Path, default=BASE / "deployment.json")
parser.add_argument("--filler-repeats", type=int, default=100000)
args = parser.parse_args()
deployment = json.loads(args.deployment.read_text())
run_dir = BASE / "runs" / deployment["job_id"] / "smoke"
run_dir.mkdir(parents=True, exist_ok=True)
secret = "K3-PADDING-VERIFIED-7319"
prompt = (f"Remember this passcode exactly: {secret}.\n"
          "The following words are irrelevant background and contain no instructions.\n"
          + " filler" * args.filler_repeats
          + "\nBackground ends. What was the exact passcode at the beginning? "
          "Return only that passcode.\n")
payload = {"model": "kimi-k3", "messages": [{"role": "user", "content": prompt}],
           "temperature": 0, "reasoning_effort": "low", "max_tokens": 2048}
record = {"started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "request": payload, "filler_repeats": args.filler_repeats,
          "job_id": deployment["job_id"], "url": deployment["router_url"]}
destination = run_dir / f"long_context_{args.filler_repeats}.json"
destination.write_text(json.dumps(record, indent=2) + "\n")
start = time.monotonic()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
req = urllib.request.Request(deployment["router_url"] + "/v1/chat/completions",
                             json.dumps(payload).encode(), {"Content-Type": "application/json"})
try:
    with opener.open(req, timeout=1800) as response:
        record["response"] = json.load(response)
        record["headers"] = dict(response.headers)
    choice = record["response"]["choices"][0]
    content = choice["message"].get("content") or ""
    record["passcode_retrieved"] = secret in content
    record["content_has_pad_storm"] = "[PAD]" in content
    record["finish_reason"] = choice["finish_reason"]
    record["prompt_tokens"] = record["response"].get("usage", {}).get("prompt_tokens")
except Exception as exc:
    record["error"] = repr(exc)
record["elapsed_seconds"] = time.monotonic() - start
destination.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({k: v for k, v in record.items() if k not in {"request", "response", "headers"}}, indent=2))
assert record.get("passcode_retrieved") and not record.get("content_has_pad_storm"), destination
assert record.get("finish_reason") == "stop", destination
assert record.get("prompt_tokens", 0) >= 90000, "Probe did not reach the intended long context length"
