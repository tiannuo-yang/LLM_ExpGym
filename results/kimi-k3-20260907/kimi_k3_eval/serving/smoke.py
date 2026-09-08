"""Wait for all four replicas and save exact request/response smoke records."""
import argparse
import concurrent.futures
import datetime
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--deployment", type=Path, default=BASE / "deployment.json")
parser.add_argument("--wait-seconds", type=int, default=7200)
args = parser.parse_args()
deployment = json.loads(args.deployment.read_text())
run_dir = BASE / "runs" / deployment["job_id"] / "smoke"
run_dir.mkdir(parents=True, exist_ok=True)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def request(url, payload=None, timeout=1200):
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with opener.open(req, timeout=timeout) as response:
        return json.load(response), dict(response.headers)

deadline = time.monotonic() + args.wait_seconds
last_report = 0
while time.monotonic() < deadline:
    try:
        health, _ = request(deployment["router_url"] + "/health", timeout=10)
    except (OSError, ValueError):
        health = {"healthy_replicas": 0}
    if time.monotonic() - last_report > 60:
        print(json.dumps({"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          "health": health}), flush=True)
        last_report = time.monotonic()
    if health["healthy_replicas"] == 4:
        break
    time.sleep(10)
else:
    raise SystemExit("Timed out waiting for all four replicas")

def probe(name, url, overrides):
    payload = {"model": "kimi-k3", "messages": [{"role": "user", "content":
        'Compute 6 * 7. Return only the JSON object {"answer":42}.'}],
        "temperature": 0, "max_tokens": 2048, **overrides}
    start = time.monotonic()
    record = {"name": name, "url": url, "request": payload,
              "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        record["response"], record["headers"] = request(url + "/v1/chat/completions", payload)
        message = record["response"]["choices"][0]["message"]
        record["content_present"] = bool(message.get("content"))
        record["reasoning_present"] = bool(message.get("reasoning_content"))
        record["answer_42"] = "42" in (message.get("content") or "")
        record["finish_reason"] = record["response"]["choices"][0]["finish_reason"]
    except Exception as exc:
        record["error"] = repr(exc)
    record["elapsed_seconds"] = time.monotonic() - start
    (run_dir / f"{name}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k not in {"request", "response", "headers"}}), flush=True)
    return record

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    baseline = list(pool.map(lambda r: probe(f"replica{r['replica']}_native_low", r["url"],
                                             {"reasoning_effort": "low"}), deployment["replicas"]))
variants = [
    ("router_default", {}),
    ("router_enable_thinking_false", {"reasoning_effort": "low", "chat_template_kwargs": {"enable_thinking": False}}),
    ("router_thinking_false", {"reasoning_effort": "low", "chat_template_kwargs": {"thinking": False}}),
]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    modes = list(pool.map(lambda v: probe(v[0], deployment["router_url"], v[1]), variants))
summary = [{k: v for k, v in r.items() if k not in {"request", "response", "headers"}} for r in baseline + modes]
(run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
assert all(r.get("answer_42") and r.get("finish_reason") == "stop" for r in baseline), summary
print("All four native-thinking replica smoke checks passed", flush=True)
